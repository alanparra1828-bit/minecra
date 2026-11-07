"""validate.py - validate a built Verdant Reverie pack before distribution."""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from PIL import Image, UnidentifiedImageError


def _diag(issues, severity, message):
    issues.append({'severity': severity, 'message': message})


def validate_folder(pack):
    issues = []
    if not pack.is_dir():
        return False, [{'severity': 'error', 'message': str(pack) + ' is not a directory'}]

    mcmeta = pack / 'pack.mcmeta'
    if not mcmeta.is_file():
        _diag(issues, 'error', 'pack.mcmeta is missing')
        return False, issues
    try:
        mcmeta_data = json.loads(mcmeta.read_text(encoding='utf-8'))
    except json.JSONDecodeError as exc:
        _diag(issues, 'error', 'pack.mcmeta is not valid JSON: ' + str(exc))
        return False, issues

    p = mcmeta_data.get('pack', {})
    min_f = p.get('min_format')
    max_f = p.get('max_format')
    desc = p.get('description', '')
    if not isinstance(min_f, list) or not isinstance(max_f, int):
        _diag(issues, 'error', 'pack.mcmeta needs min_format (list) and max_format (number)')
    elif min_f != [97, 1]:
        _diag(issues, 'warning', 'min_format is ' + str(min_f) + ', expected [97, 1] for Java 26.3')
    if max_f != 97:
        _diag(issues, 'warning', 'max_format is ' + str(max_f) + ', expected 97 for Java 26.3')
    if not desc:
        _diag(issues, 'warning', 'pack description is empty')
    if p.get('pack_format') != 97:
        _diag(issues, 'warning', 'pack_format is ' + str(p.get('pack_format')) + ', expected 97')

    icon = pack / 'pack.png'
    if not icon.is_file():
        _diag(issues, 'error', 'pack.png is missing')
    else:
        try:
            im = Image.open(icon)
            im.load()
            if im.mode != 'RGBA':
                _diag(issues, 'warning', 'pack.png has unexpected mode ' + str(im.mode))
            if im.size != (128, 128):
                _diag(issues, 'warning', 'pack.png is ' + str(im.size) + ', expected 128x128')
        except UnidentifiedImageError:
            _diag(issues, 'error', 'pack.png is not a readable PNG')

    assets = pack / 'assets' / 'verdantreverie'
    if not assets.is_dir():
        _diag(issues, 'error', 'assets/verdantreverie does not exist')
        return False, issues
    if not list(assets.iterdir()):
        _diag(issues, 'warning', 'assets folder is empty')

    for file in sorted(assets.rglob('*')):
        if not file.is_file():
            continue
        rel = file.relative_to(assets).as_posix()
        if not rel.startswith('textures/'):
            continue
        if file.suffix.lower() not in ('.png', '.jpg', '.jpeg'):
            _diag(issues, 'warning', rel + ': unsupported texture extension')
            continue
        try:
            im = Image.open(file)
            im.load()
            w, h = im.size
            if w != h:
                _diag(issues, 'error', rel + ': textures must be square, got ' + str(w) + 'x' + str(h))
            elif w & (w - 1) != 0:
                _diag(issues, 'error', rel + ': resolution ' + str(w) + ' is not a power of two')
        except UnidentifiedImageError:
            _diag(issues, 'error', rel + ': not a readable image')

    for file in sorted(pack.rglob('*.json')):
        if file.name == 'pack.mcmeta':
            continue
        try:
            json.loads(file.read_text(encoding='utf-8'))
        except json.JSONDecodeError as exc:
            _diag(issues, 'error', str(file.relative_to(pack)) + ': invalid JSON (' + str(exc) + ')')

    # Every model must reference a texture that actually exists.
    for model_file in sorted((assets / 'models').rglob('*.json')):
        try:
            model = json.loads(model_file.read_text(encoding='utf-8'))
        except json.JSONDecodeError:
            continue
        tex = None
        for value in model.get('textures', {}).values():
            if isinstance(value, str) and value.startswith('verdantreverie:'):
                tex = value
                break
        if tex is None:
            continue
        parts = tex.split(':', 1)[1].split('/', 1)
        if len(parts) != 2:
            continue
        texture_file = assets / 'textures' / parts[0] / (parts[1] + '.png')
        if not texture_file.is_file():
            _diag(issues, 'error', str(model_file) + ' references missing texture ' + tex)
    ok = not issues or all(i['severity'] == 'warning' for i in issues)
    return ok, issues


def main(argv=None):
    parser = argparse.ArgumentParser(description='Validate a built resource pack folder.')
    parser.add_argument('pack', type=Path, help='path to the built pack directory or ZIP')
    args = parser.parse_args(argv)

    pack = args.pack
    if pack.is_file():
        import zipfile
        tmp = pack.with_suffix('.packdir')
        if tmp.exists():
            shutil.rmtree(tmp)
        with zipfile.ZipFile(pack) as zf:
            zf.extractall(tmp)
        pack = tmp

    ok, issues = validate_folder(pack)
    print('Validating ' + str(pack))
    if issues:
        for i in issues:
            print('  [' + i['severity'].upper() + '] ' + i['message'])
        status = 'VALID' if ok else 'INVALID'
        print('=> ' + str(pack) + ' is ' + status)
        return 1 if not ok else 0
    print('=> ' + str(pack) + ' is VALID (no issues)')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
