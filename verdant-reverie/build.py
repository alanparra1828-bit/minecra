"""build.py - assemble Verdant Reverie resource packs into downloadable ZIPs.

Usage:
    python build.py 512x          # build one resolution
    python build.py 1024x
    python build.py 2048x
    python build.py all           # build every resolution
    python build.py --list        # list available resolutions
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
import zipfile
from pathlib import Path

from artlib import ART_WORK_RES, build_pack_icon, generate_all
import recipes
from recipes import BLOCKS, ITEMS, NAMESPACE
from config import RESOLUTIONS

ROOT = Path(__file__).resolve().parent
BUILD_BASE = ROOT / "builds"
ZIP_BASE = ROOT / "outputs"


def _out_dir(base: Path, resolution: int) -> Path:
    return BUILD_BASE / f"{resolution}x"


def _zip_path(resolution: int) -> Path:
    return ZIP_BASE / f"verdant-reverie-{resolution}x.zip"


def resource_to_file(resource_path: str) -> str:
    """verdantreverie:block/amber_crystal -> verdantreverie/textures/block/amber_crystal.png"""
    ns, rest = resource_path.split(":", 1)
    category, name = rest.split("/", 1)
    return f"textures/{category}/{name}.png"


def write_textures(build_root: Path, textures: dict[str, object]) -> None:
    assets = build_root / "assets" / NAMESPACE
    for resource_path, image in textures.items():
        dest = assets / resource_to_file(resource_path)
        dest.parent.mkdir(parents=True, exist_ok=True)
        image.save(dest)


def write_block_models(build_root: Path, textures: dict[str, object]) -> None:
    models_dir = build_root / "assets" / NAMESPACE / "models" / "block"
    models_dir.mkdir(parents=True, exist_ok=True)
    blockstates_dir = build_root / "assets" / NAMESPACE / "blockstates"
    blockstates_dir.mkdir(parents=True, exist_ok=True)
    for block in BLOCKS:
        bid = block["id"]
        if block.get("model") == "grass":
            side = block["tex_side"]
            top = block["tex_top"]
            model = recipes.grass_block_model(side, top)
        else:
            model = recipes.flat_block_model(block["tex"])
        (models_dir / f"{bid}.json").write_text(json.dumps(model, indent=2) + "\n", encoding="utf-8")
        model_path = f"verdantreverie:block/{bid}"
        (blockstates_dir / f"{bid}.json").write_text(
            json.dumps({"variants": {"": {"model": model_path}}}, indent=2) + "\n", encoding="utf-8"
        )


def write_item_models(build_root: Path, textures: dict[str, object]) -> None:
    models_dir = build_root / "assets" / NAMESPACE / "models" / "item"
    models_dir.mkdir(parents=True, exist_ok=True)
    for item in ITEMS:
        model = recipes.item_model(item["tex"])
        (models_dir / f"{item['id']}.json").write_text(json.dumps(model, indent=2) + "\n", encoding="utf-8")


def write_lang(build_root: Path) -> None:
    lang_dir = build_root / "assets" / NAMESPACE / "lang"
    lang_dir.mkdir(parents=True, exist_ok=True)
    (lang_dir / "en_us.json").write_text(
        json.dumps(recipes.lang_data(), indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )


def write_pack_files(build_root: Path) -> None:
    (build_root / "pack.mcmeta").write_text(
        json.dumps(recipes.PACK_MCMETA, indent=2) + "\n", encoding="utf-8"
    )
    icon = build_pack_icon()
    icon.save(build_root / "pack.png")


def build(resolution: int) -> Path:
    ZIP_BASE.mkdir(parents=True, exist_ok=True)
    build_root = _out_dir(BUILD_BASE, resolution)
    if build_root.exists():
        shutil.rmtree(build_root)
    build_root.mkdir(parents=True)

    textures = generate_all(resolution)
    write_textures(build_root, textures)
    write_block_models(build_root, textures)
    write_item_models(build_root, textures)
    write_pack_files(build_root)
    write_lang(build_root)

    zip_path = _zip_path(resolution)
    if zip_path.exists():
        zip_path.unlink()
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(build_root.rglob("*")):
            if path.is_file():
                zf.write(path, path.relative_to(build_root))

    file_count = sum(1 for _ in (build_root / 'assets').rglob('*') if _.is_file())
    print(f"built verdant-reverie-{resolution}x.zip "
          f"({file_count} files) "
          f"-> {zip_path}")
    return zip_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build Verdant Reverie resource pack ZIPs.")
    parser.add_argument("resolution", nargs="?", default="all",
                        help="512x | 1024x | 2048x | all "
                             f"(default resolution is {ART_WORK_RES})")
    args = parser.parse_args(argv)

    requested = [args.resolution] if args.resolution != "all" else list(RESOLUTIONS.keys())
    results = []
    for raw in requested:
        key = raw.lower().replace(" ", "")
        if key not in RESOLUTIONS:
            print(f"error: unknown resolution {raw!r}. choose from {list(RESOLUTIONS)}", file=sys.stderr)
            return 2
        results.append(build(RESOLUTIONS[key]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
