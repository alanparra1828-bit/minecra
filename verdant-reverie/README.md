# Verdant Reverie — Minecraft Java resource pack

A procedurally generated, high-resolution (512x / 1024x / 2048x) Minecraft Java
resource pack for **Minecraft 26.3** (resource pack format **97.1**), built
entirely from Python.

Every build shares *identical* art — the artwork is drawn once in a 512px design
space and then cleanly upscaled, so the 512x / 1024x / 2048x editions look like
the same pack, just rendered sharper.

## What you get

- `verdant-reverie-512x.zip` — each block face is 512x512 px
- `verdant-reverie-1024x.zip` — each block face is 1024x1024 px
- `verdant-reverie-2048x.zip` — each block face is 2048x2048 px

Both are valid, loadable Java 26.3 resource packs that you can install into
Minecraft.

## Prerequisites

Python 3.11+ and a Python environment. Only one third-party package is needed:

```bash
python -m pip install -r requirements.txt
```

(More information is at `requirements.txt`.)

## Quick start

```bash
python build.py all         # builds 512x, 1024x and 2048x
```

Or build a single resolution:

```bash
python build.py 2048x
```

The ZIPs are written to `outputs/`.

## Project layout

```
verdant-reverie/
├── artlib.py            # generative artwork engine (textures + icons)
├── build.py             # assembles the pack and writes the .zip files
├── config.py            # shared constants (version, palette, resolutions)
├── recipes.py           # the curated asset recipe + packaging templates
├── requirements.txt     # Python dependencies
├── validate.py          # pre-flight pack checker
├── README.md
├── builds/              # intermediate assembled pack trees (per resolution)
└── outputs/             # final .zip builds
```

## How it works

1. `artlib.py` draws every block, item and particle texture.  Each generator
   draws in the unit square and scales up to the target resolution, so 512x,
   1024x and 2048x share identical artwork.
2. `build.py` wires the recipe (`recipes.py`) to the art engine (`artlib.py`),
   writes the pack tree (`pack.mcmeta`, `pack.png`, `assets/minecraft/...`),
   and zips it.
3. `validate.py` checks the result before distribution: pack.mcmeta targets
   Java 26.3, textures are square PNGs at the advertised resolution, and every
   model references a texture that exists.

## Adding a new block

1. Add a generator to `artlib.py` that returns an RGBA image (e.g. `block_mycrystal`).
2. Register it in `artlib.TEXTURE_TABLE` with a path like
   `verdantreverie:block/mycrystal`.
3. Add a recipe to `recipes.BLOCKS` with the same texture path and a model type
   of `flat` (single surface) or `grass` (top + sides).
4. Run `python build.py all` and validate with `python validate.py outputs/*.zip`.

## Pack format

This pack targets **Minecraft Java 26.3** ("Wilderness Bound"), whose resource
pack format is **97.1**.  `pack.mcmeta` therefore declares:

```json
{ "pack": { "pack_format": 97, "min_format": [97, 1], "max_format": 97 } }
```

Resolution is the number of pixels along one edge of a single block face
(vanilla is 16x).  Every texture in a given build uses the same resolution, so
the two are one and the same choice in this project.
