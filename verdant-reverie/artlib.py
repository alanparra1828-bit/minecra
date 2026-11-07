"""artlib.py - procedural art engine for the Verdant Reverie resource pack.

Everything is drawn in the unit square [0, 1], then scaled to a working
resolution and upscaled into the final build resolution, so the 512x /
1024x / 2048x builds share identical art. Pure Python + Pillow only.
"""
from __future__ import annotations

import math
import random
from PIL import Image, ImageDraw, ImageFilter

from config import ART_WORK_RES, PACK_ICON_SIZE

# --------------------------------------------------------------------------
# Palette - one cohesive "verdant reverie" set.
# --------------------------------------------------------------------------
_SKY_NIGHT   = (13, 17, 31)
_DEEP_MOSS   = (9, 47, 33)
_MOSS        = (24, 80, 49)
_SPRING_MOSS = (47, 115, 61)
_PINE_GREEN  = (19, 58, 34)
_SUN_LIT     = (88, 154, 68)
_LIGHT_GREEN = (126, 184, 78)
_GOLDEN      = (216, 164, 48)
_VERMILLION  = (204, 58, 62)
_LIME_PALE   = (156, 196, 94)
_NIGHT_PETAL = (202, 164, 232)
_AMBER       = (248, 184, 58)
_AMBER_HOLO  = (255, 218, 94)
_TINTED_GLASS= (158, 214, 236)
_FROST       = (214, 232, 241)
_MUSHROOM_CAP= (94, 57, 82)
_MUSHROOM_STEM=(208, 194, 204)
_SPARKLE     = (255, 243, 214)
_SKY_MIX     = (64, 44, 96)
_MIST        = (222, 228, 234)
_BLACK       = (12, 14, 22)


# --------------------------------------------------------------------------
# Deterministic noise (pure Python)
# --------------------------------------------------------------------------
def _rand(seed: int, i: int, j: int) -> float:
    return math.sin((int(seed) & 0xFFFFFFFF) * 12.9898 + i * 78.233
                    + j * 12.9898 * 2654435761) * 43758.5453 % 1.0


def value_noise(x: float, y: float, seed: int) -> float:
    """Smooth scalar noise in [-1, 1]."""
    i = int(math.floor(x)) & 0xFFFFFFFF
    j = int(math.floor(y)) & 0xFFFFFFFF
    h = (_rand(seed, i, j) + _rand(seed, i + 1, j) + _rand(seed, i, j + 1)
         + _rand(seed, i + 1, j + 1)) * 0.25
    return max(-1.0, min(1.0, h))


def soft_noise(width: int, height: int, seed: int, octave_bits: int = 5) -> Image.Image:
    """Smooth mottling in 0..255, built on a coarse lattice then low-passed."""
    w = max(1, width >> octave_bits)
    h = max(1, height >> octave_bits)
    small = Image.new("L", (w, h))
    sx = small.load()
    for py in range(h):
        for px in range(w):
            v = value_noise(px * 8.0 / width, py * 8.0 / height, seed) * 0.5 + 0.5
            sx[py, px] = int(v * 255)
    return small.resize((width, height), Image.LANCZOS)


# --------------------------------------------------------------------------
# Colour math
# --------------------------------------------------------------------------
def _clamp(v: float) -> float:
    return max(0.0, min(1.0, v))


def _lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * _clamp(t)


def color_lerp(a: tuple, b: tuple, t: float) -> tuple:
    return tuple(int(a[i] + (b[i] - a[i]) * _clamp(t)) for i in range(3))


def color_mult(c: tuple, m: float) -> tuple:
    return tuple(int(c[i] * m) for i in range(3))


def alpha_over(base: tuple, top: tuple, alpha: int) -> tuple:
    a = alpha / 255.0
    return tuple(int(top[i] * a + base[i] * (1.0 - a)) for i in range(3))


def fill_solid(img: Image.Image, color: tuple) -> None:
    img.paste(color, (0, 0, img.width, img.height))


def radial_glow(size: int, color: tuple, radius: float, alpha: int,
                offset: tuple = (0, 0)) -> Image.Image:
    """Soft additive radial glow (RGBA)."""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    gd = ImageDraw.Draw(img)
    cx, cy = size / 2 + offset[0], size / 2 + offset[1]
    for r in range(int(radius * 1.8), 0, -1):
        a = int(alpha * max(0.0, 1.0 - (r / radius) ** 2.0))
        if a < 3:
            continue
        gd.ellipse([cx - r, cy - r, cx + r, cy + r],
                   fill=(color[0], color[1], color[2], a))
    return img.filter(ImageFilter.GaussianBlur(radius * 0.8))


def _new_canvas(size: int) -> Image.Image:
    return Image.new("RGBA", (size, size), (0, 0, 0, 0))


def rounded_mask(size: int, frac: float) -> Image.Image:
    m = Image.new("L", (size, size), 0)
    d = ImageDraw.Draw(m)
    r = int(size * frac)
    d.rectangle([0, 0, size, size], fill=255)
    for (x, y) in [(0, 0), (size - r, 0), (0, size - r), (size - r, size - r)]:
        d.rectangle([x, y, x + r, y + r], fill=0)
    return m


def _dart(x: float, y: float, r: float, color: tuple, img: Image.Image) -> None:
    """A small filled diamond (sparkle)."""
    d = ImageDraw.Draw(img)
    d.polygon([(x, y - r), (x + r, y), (x, y + r), (x - r, y)], fill=color)


def _star(x: float, y: float, r_out: float, r_in: float, color: tuple,
          img: Image.Image, points: int = 5) -> None:
    pts = []
    for i in range(points * 2):
        a = math.pi * i / points - math.pi / 2
        rr = r_out if i % 2 == 0 else r_in
        pts.append((x + rr * math.cos(a), y + rr * math.sin(a)))
    d = ImageDraw.Draw(img)
    d.polygon(pts, fill=color)

# --------------------------------------------------------------------------
# Block textures
# --------------------------------------------------------------------------
def _blade(d: ImageDraw.ImageDraw, x: float, base_y: float, tip_x: float,
           tip_y: float, w: float, color: tuple) -> None:
    d.polygon([(x - w, base_y), (x + w, base_y), (tip_x, tip_y)], fill=color)


def _shade_grass(col: tuple, m: float) -> tuple:
    """Brighten a grass colour by mottled overlay."""
    return tuple(int(v * (0.55 + 0.95 * m)) for v in col)


def block_grass_top(size: int, seed: int) -> Image.Image:
    rng = random.Random(seed)
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    fill_solid(img, _SPRING_MOSS)
    d = ImageDraw.Draw(img)
    mott = soft_noise(size, size, seed + 101, 5)
    mx = mott.load()
    height = size
    for i in range(int(size * 0.62)):
        x = rng.uniform(0, size)
        base_y = rng.uniform(0.64, 0.93) * height
        tip_y = base_y - rng.uniform(0.16, 0.52) * height
        tip_x = x + rng.uniform(-0.35, 0.35) * height
        w = rng.uniform(1.8, 4.4)
        t = (base_y - tip_y) / height
        col = color_lerp(_PINE_GREEN, _SUN_LIT, t)
        bx = int(x) % size
        by = int(base_y) % size
        m = mx[by, bx] / 255.0
        col = _shade_grass(col, m)
        _blade(d, x, base_y, tip_x, tip_y, w, col)
    # glowing centre
    glow = radial_glow(size, _SUN_LIT, size * 0.20, 60)
    img = Image.alpha_composite(img, glow)
    # sunfleck highlights
    for i in range(12):
        x = rng.uniform(0, size)
        base_y = rng.uniform(0.66, 0.93) * height
        tip_y = base_y - rng.uniform(0.10, 0.28) * height
        tip_x = x + rng.uniform(-0.22, 0.22) * height
        w = rng.uniform(1.2, 2.8)
        d.polygon([(x - w, base_y), (x + w, base_y), (tip_x, tip_y)],
                  fill=_LIME_PALE)
    return img


def block_grass_side(size: int, seed: int) -> Image.Image:
    rng = random.Random(seed)
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    fill_solid(img, _PINE_GREEN)
    d = ImageDraw.Draw(img)
    mott = soft_noise(size, size, seed + 102, 5)
    mx = mott.load()
    height = size
    for i in range(int(size * 0.72)):
        x = rng.uniform(0, size)
        base_y = rng.uniform(0.66, 0.95) * height
        tip_y = base_y - rng.uniform(0.16, 0.48) * height
        tip_x = x + rng.uniform(-0.32, 0.32) * height
        w = rng.uniform(1.8, 4.4)
        t = (base_y - tip_y) / height
        col = color_lerp(_PINE_GREEN, _SUN_LIT, t)
        bx = int(x) % size
        by = int(base_y) % size
        m = mx[by, bx] / 255.0
        col = _shade_grass(col, m)
        _blade(d, x, base_y, tip_x, tip_y, w, col)
    glow = radial_glow(size, _SUN_LIT, size * 0.16, 45)
    img = Image.alpha_composite(img, glow)
    return img


def block_moss(size: int, seed: int) -> Image.Image:
    rng = random.Random(seed)
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    fill_solid(img, _MOSS)
    d = ImageDraw.Draw(img)
    topo = soft_noise(size, size, seed + 7, 5)
    tp = topo.load()
    for i in range(int(size * 0.20)):
        cx = rng.uniform(0, size)
        cy = rng.uniform(0, size)
        r = int(rng.uniform(8, 30) * (tp[int(cy), int(cx)] / 255.0 + 0.4))
        col = color_lerp(_DEEP_MOSS, _MOSS, tp[int(cy), int(cx)] / 255.0)
        col = color_mult(col, rng.uniform(0.8, 1.0))
        ell = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        ImageDraw.Draw(ell).ellipse([cx - r, cy - r, cx + r, cy + r], fill=col)
        img = Image.alpha_composite(img, ell)
    for i in range(26):
        cx = rng.uniform(0, size)
        cy = rng.uniform(0, size)
        _dart(cx, cy, rng.uniform(1.0, 3.2), _SPARKLE, img)
    return img


def block_fern_top(size: int, seed: int) -> Image.Image:
    rng = random.Random(seed)
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    fill_solid(img, _DEEP_MOSS)
    d = ImageDraw.Draw(img)
    height = size
    for frond in range(5):
        base_y = rng.uniform(0.25, 0.58) * height
        length = rng.uniform(0.30, 0.62) * height
        angle = rng.uniform(-0.35, 0.35)
        for leaflet in range(9):
            lx = leaflet / 8.0 - 0.5
            lx2 = lx + 0.12
            ax = frond + length * 0.16 * math.sin(angle + leaflet * 1.15)
            ay = base_y + length * (0.10 + 0.80 * lx * 0.60)
            ay2 = base_y + length * (0.10 + 0.85 * lx2)
            lsize = max(3, rng.uniform(6, 18))
            col = color_lerp(_PINE_GREEN, _SPRING_MOSS, lsize / (height * 0.08))
            _dart(ax, ay, lsize, col, img)
            _dart(ax, ay2, lsize * 0.85, _SPRING_MOSS, img)
    return img


def block_fern_side(size: int, seed: int) -> Image.Image:
    rng = random.Random(seed)
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    fill_solid(img, _PINE_GREEN)
    d = ImageDraw.Draw(img)
    height = size
    for frond in range(4):
        base_y = rng.uniform(0.52, 0.86) * height
        length = rng.uniform(0.40, 0.72) * height
        angle = rng.uniform(-0.6, 0.6)
        for leaflet in range(8):
            lx = leaflet / 7.0 - 0.5
            ax = frond + length * 0.14 * math.sin(angle + leaflet * 1.2)
            ay = base_y + length * (0.12 + 0.75 * lx)
            lsize = max(3, rng.uniform(7, 20))
            col = color_lerp(_PINE_GREEN, _SPRING_MOSS, lsize / (height * 0.09))
            _dart(ax, ay, lsize, col, img)
    return img


def block_mushroom(size: int, seed: int) -> Image.Image:
    rng = random.Random(seed)
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    fill_solid(img, _MUSHROOM_STEM)
    d = ImageDraw.Draw(img)
    height = size
    cx = height / 2
    cy = height * 0.30
    cap_r = height * 0.34
    cap = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    ImageDraw.Draw(cap).ellipse([cx - cap_r, cy - cap_r, cx + cap_r, cy + cap_r],
                                fill=_MUSHROOM_CAP)
    tp = soft_noise(size, size, seed + 104, 5).load()
    for i in range(6):
        sx = cx + rng.uniform(-cap_r, cap_r) * tp[int(cy), int(cx)] / 255.0
        sy = cy + rng.uniform(-cap_r, cap_r) * 0.4
        _dart(sx, sy, rng.uniform(3, 7), _SPARKLE, cap)
    img = Image.alpha_composite(img, cap)
    stem = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    ImageDraw.Draw(stem).rectangle([cx - height * 0.05, cy + cap_r * 0.6,
                                    cx + height * 0.05, cy + cap_r * 1.5],
                                   fill=_MUSHROOM_STEM)
    img = Image.alpha_composite(img, stem)
    return img


def block_crystal(size: int, seed: int) -> Image.Image:
    rng = random.Random(seed)
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    height = size
    cx, cy = height / 2, height / 2
    n = 6
    pts = []
    for i in range(n):
        a = 2 * math.pi * i / n - math.pi / 2
        rr = height * (0.42 + 0.04 * math.sin(3 * a))
        pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    body = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    ImageDraw.Draw(body).polygon(pts, fill=alpha_over(_FROST, _AMBER_HOLO, 0))
    img = Image.alpha_composite(img, body)
    gla = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    ImageDraw.Draw(gla).polygon(pts, fill=_AMBER_HOLO)
    img = Image.alpha_composite(img, gla)
    hl = radial_glow(size, _SPARKLE, height * 0.16, 70, (height * 0.28, height * 0.32))
    img = Image.alpha_composite(img, hl)
    tp = soft_noise(size, size, seed + 105, 5).load()
    for i in range(12):
        sx = cx + rng.uniform(-height * 0.4, height * 0.4)
        sy = cy + rng.uniform(-height * 0.4, height * 0.4)
        _star(sx, sy, rng.uniform(1.4, 2.6), rng.uniform(0.7, 1.3), _SPARKLE, img)
    return img


def block_illium(size: int, seed: int) -> Image.Image:
    rng = random.Random(seed)
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    fill_solid(img, _DEEP_MOSS)
    d = ImageDraw.Draw(img)
    height = size
    cx, cy = height / 2, height / 2
    lit = radial_glow(height, _SPARKLE, height * 0.30, 45)
    img = Image.alpha_composite(img, lit)
    _star(cx, cy, height * 0.30, height * 0.13, _GOLDEN, img, 8)
    for i in range(8):
        a = math.pi * 2 * i / 8 - math.pi / 2
        r1 = height * 0.22
        r2 = height * 0.09
        _star(cx + r1 * math.cos(a), cy + r1 * math.sin(a), r2, r2 * 0.6,
               _GOLDEN, img, 4)
    for i in range(30):
        _dart(rng.uniform(0, height), rng.uniform(0, height),
               rng.uniform(1.0, 2.4), _SPARKLE, img)
    return img


def block_ice(size: int, seed: int) -> Image.Image:
    rng = random.Random(seed)
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    fill_solid(img, _FROST)
    d = ImageDraw.Draw(img)
    height = size
    mott = soft_noise(height, height, seed + 106, 5)
    tp = mott.load()
    for i in range(4):
        x = rng.uniform(0, height)
        y = rng.uniform(0, height)
        s = rng.uniform(height * 0.18, height * 0.6)
        col = color_lerp(_MIST, _FROST, tp[int(y), int(x)] / 255.0)
        d.polygon([(x, y - s), (x + s, y), (x, y + s), (x - s, y)], fill=col)
    hl = radial_glow(height, _SPARKLE, height * 0.22, 55, (height * 0.72, height * 0.62))
    img = Image.alpha_composite(img, hl)
    return img


def block_vines(size: int, seed: int) -> Image.Image:
    rng = random.Random(seed)
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    fill_solid(img, _MOSS)
    d = ImageDraw.Draw(img)
    height = size
    for i in range(10):
        cx = rng.uniform(0, height)
        cy = rng.uniform(0, height)
        w = rng.uniform(height * 0.03, height * 0.07)
        col = color_lerp(_PINE_GREEN, _SPRING_MOSS, rng.uniform(0.3, 0.9))
        for k in range(4):
            ax = cx + rng.uniform(-height * 0.3, height * 0.3)
            ay = cy + rng.uniform(-height * 0.3, height * 0.3)
            ar = rng.uniform(height * 0.16, height * 0.30)
            _star(ax, ay, ar, ar * 0.5, col, img, 5)
    haze = radial_glow(height, _SPRING_MOSS, height * 0.5, 18)
    img = Image.alpha_composite(img, haze)
    return img


def block_amber_gel(size: int, seed: int) -> Image.Image:
    rng = random.Random(seed)
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    fill_solid(img, _AMBER)
    d = ImageDraw.Draw(img)
    height = size
    cx, cy = height / 2, height / 2
    pool = radial_glow(height, _AMBER_HOLO, height * 0.30, 110, (0, height * 0.10))
    img = Image.alpha_composite(img, pool)
    top = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    ImageDraw.Draw(top).ellipse([cx - height * 0.28, cy - height * 0.32,
                                 cx + height * 0.28, cy + height * 0.08],
                                fill=_AMBER_HOLO)
    img = Image.alpha_composite(img, top)
    tp = soft_noise(height, height, seed + 107, 5).load()
    for i in range(32):
        sx = rng.uniform(0, height)
        sy = rng.uniform(0, height)
        _star(sx, sy, rng.uniform(1.2, 3.0), rng.uniform(0.5, 1.2),
              _SPARKLE, img)
    return img


def block_spirit_ore(size: int, seed: int) -> Image.Image:
    rng = random.Random(seed)
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    fill_solid(img, _DEEP_MOSS)
    d = ImageDraw.Draw(img)
    for i in range(6):
        _star(rng.uniform(0, size), rng.uniform(0, size),
               rng.uniform(size * 0.10, size * 0.28), rng.uniform(size * 0.10, size * 0.28) * 0.45,
               _GOLDEN, img, 6)
    glow = radial_glow(size, _SPARKLE, size * 0.28, 30)
    img = Image.alpha_composite(img, glow)
    return img


def block_driftwood(size: int, seed: int) -> Image.Image:
    rng = random.Random(seed)
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    fill_solid(img, _MOSS)
    d = ImageDraw.Draw(img)
    height = size
    # dark wood core
    core = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    ImageDraw.Draw(core).rectangle([height * 0.25, height * 0.25,
                                    height * 0.75, height * 0.75],
                                   fill=_DEEP_MOSS)
    img = Image.alpha_composite(img, core)
    for i in range(6):
        x = rng.uniform(height * 0.2, height * 0.8)
        y = rng.uniform(height * 0.22, height * 0.72)
        w = rng.uniform(height * 0.02, height * 0.06)
        d.line([x - w, y, x + w, y], fill=tuple(int(v * 0.5) for v in _PINE_GREEN), width=int(w))
    for i in range(22):
        px = rng.uniform(0, height)
        py = rng.uniform(0, height * 0.55)
        pr = rng.uniform(height * 0.05, height * 0.20)
        _star(px, py, pr, pr * 0.4, _SPRING_MOSS, img, 6)
    return img


# --------------------------------------------------------------------------
# Item textures (transparent sprites on soft dark discs)
# --------------------------------------------------------------------------
def _disc(img: Image.Image, oc: tuple, alpha: int) -> None:
    """Add a soft dark disc behind an item for a polished sprite."""
    circ = Image.new("RGBA", (img.width, img.height), (0, 0, 0, 0))
    ImageDraw.Draw(circ).ellipse([0, 0, img.width, img.height], fill=(oc[0], oc[1], oc[2], alpha))
    img = Image.alpha_composite(img, circ)
    hl = radial_glow(img.width, _SPARKLE, img.width * 0.22, 30)
    return Image.alpha_composite(img, hl)


def item_amber_crystal(size: int, seed: int) -> Image.Image:
    rng = random.Random(seed)
    img = _new_canvas(size)
    height = size
    cx, cy = height / 2, height / 2
    n = 6
    pts = []
    for i in range(n):
        a = 2 * math.pi * i / n - math.pi / 2
        rr = height * (0.33 + 0.05 * math.sin(3 * a))
        pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    d = ImageDraw.Draw(img)
    d.polygon(pts, fill=alpha_over(_FROST, _AMBER_HOLO, 0))
    gla = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    ImageDraw.Draw(gla).polygon(pts, fill=_AMBER_HOLO)
    img = Image.alpha_composite(img, gla)
    glow = radial_glow(size, _SPARKLE, height * 0.24, 75, (height * 0.30, height * 0.28))
    img = Image.alpha_composite(img, glow)
    return _disc(img, _BLACK, 90)


def item_fern_sprout(size: int, seed: int) -> Image.Image:
    rng = random.Random(seed)
    img = _new_canvas(size)
    d = ImageDraw.Draw(img)
    height = size
    cx, cy = height / 2, height / 2
    # stem
    d.line([(cx, cy), (cx, cy + height * 0.34)], fill=_PINE_GREEN, width=int(height * 0.08))
    for i, ang in enumerate([-0.45, 0.45]):
        hx = cx + height * 0.26 * math.sin(ang)
        hy = cy + height * 0.22
        _dart(hx, hy, height * 0.11, _SPRING_MOSS, img)
        _dart(hx, hy + height * 0.06, height * 0.06, _SUN_LIT, img)
    # disc
    return _disc(img, _BLACK, 90)


def item_pale_mushroom(size: int, seed: int) -> Image.Image:
    img = _new_canvas(size)
    d = ImageDraw.Draw(img)
    height = size
    cx, cy = height / 2, height / 2
    cap_r = height * 0.30
    d.ellipse([cx - cap_r, cy - cap_r * 0.85, cx + cap_r, cy + cap_r * 0.45],
              fill=_MUSHROOM_CAP)
    d.ellipse([cx - cap_r * 0.7, cy - cap_r * 0.5, cx + cap_r * 0.7, cy + cap_r * 0.4],
              fill=_SPARKLE)
    d.rectangle([cx - height * 0.05, cy + cap_r * 0.45, cx + height * 0.05, cy + height * 0.18],
                fill=_MUSHROOM_STEM)
    return _disc(img, _BLACK, 90)


def item_wild_berry(size: int, seed: int) -> Image.Image:
    img = _new_canvas(size)
    d = ImageDraw.Draw(img)
    height = size
    cx, cy = height / 2, height / 2
    r = height * 0.32
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=_VERMILLION)
    d.ellipse([cx - r * 0.35, cy - r * 0.35, cx + r * 0.35, cy + r * 0.35], fill=_SPARKLE)
    return _disc(img, _BLACK, 90)


def item_amber_gel(size: int, seed: int) -> Image.Image:
    img = _new_canvas(size)
    d = ImageDraw.Draw(img)
    height = size
    cx, cy = height / 2, height / 2
    r = height * 0.32
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=_AMBER)
    glow = radial_glow(height, _AMBER_HOLO, height * 0.18, 70, (height * 0.65, height * 0.72))
    img = Image.alpha_composite(img, glow)
    return _disc(img, _BLACK, 90)


def item_sparkler(size: int, seed: int) -> Image.Image:
    img = _new_canvas(size)
    d = ImageDraw.Draw(img)
    height = size
    cx, cy = height / 2, height / 2
    body = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    ImageDraw.Draw(body).ellipse([cx - height * 0.14, cy - height * 0.10,
                                  cx + height * 0.14, cy + height * 0.10],
                                 fill=_BLACK)
    img = Image.alpha_composite(img, body)
    glow = radial_glow(height, _GOLDEN, height * 0.22, 180, (cx, cy - height * 0.04))
    img = Image.alpha_composite(img, glow)
    d = ImageDraw.Draw(img)
    d.ellipse([cx - height * 0.025, cy - height * 0.125, cx + height * 0.025, cy + height * 0.035],
              fill=_BLACK)
    return _disc(img, _BLACK, 90)


def item_moon_flower(size: int, seed: int) -> Image.Image:
    img = _new_canvas(size)
    d = ImageDraw.Draw(img)
    height = size
    cx, cy = height / 2, height / 2
    r = height * 0.32
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=_NIGHT_PETAL)
    d.ellipse([cx - r * 0.6, cy - r * 0.6, cx + r * 0.6, cy + r * 0.6], fill=_DEEP_MOSS)
    for i in range(8):
        a = math.pi * 2 * i / 8 - math.pi / 2
        r1 = r * 0.45
        r2 = r * 0.14
        sx = cx + r1 * math.cos(a)
        sy = cy + r1 * math.sin(a)
        _star(sx, sy, r2, r2 * 0.6, _SPARKLE, img, 4)
    return _disc(img, _BLACK, 90)


def item_seedling(size: int, seed: int) -> Image.Image:
    img = _new_canvas(size)
    d = ImageDraw.Draw(img)
    height = size
    cx, cy = height / 2, height / 2
    d.line([(cx, cy + height * 0.16), (cx, cy + height * 0.40)], fill=_PINE_GREEN, width=int(height * 0.06))
    for i, ang in enumerate([-0.4, 0.4]):
        hx = cx + height * 0.18 * math.sin(ang)
        hy = cy + height * 0.33
        _dart(hx, hy, height * 0.10, _SPRING_MOSS, img)
        _dart(hx, hy + height * 0.05, height * 0.05, _SUN_LIT, img)
    return _disc(img, _BLACK, 90)


def block_nightbloom(size: int, seed: int) -> Image.Image:
    rng = random.Random(seed)
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    height = size
    cx, cy = height / 2, height / 2
    d = ImageDraw.Draw(img)
    # pale petals around a dark night centre
    for i in range(8):
        a = math.pi * 2 * i / 8 - math.pi / 2
        r_out = height * 0.30
        r_in = height * 0.10
        sxa = cx + r_out * math.cos(a)
        sya = cy + r_out * math.sin(a)
        sxb = cx + r_in * math.cos(a)
        syb = cy + r_in * math.sin(a)
        d.line([(sxa, sya), (sxb, syb)], fill=_NIGHT_PETAL, width=int(height * 0.06))
    # long glowing stamens
    for i in range(16):
        a = math.pi * i / 16 - math.pi / 2
        r = height * 0.34
        d.line([(cx, cy), (cx + r * math.cos(a), cy + r * math.sin(a))],
               fill=_AMBER, width=int(height * 0.02))
    glow = radial_glow(height, _NIGHT_PETAL, height * 0.40, 45)
    img = Image.alpha_composite(img, glow)
    return _disc(img, _BLACK, 90)


def block_mist_gate(size: int, seed: int) -> Image.Image:
    rng = random.Random(seed)
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    fill_solid(img, _MIST)
    height = size
    d = ImageDraw.Draw(img)
    # soft translucent veil
    veil = radial_glow(height, _TINTED_GLASS, height * 0.60, 55)
    img = Image.alpha_composite(img, veil)
    # frame lines
    for i in range(3):
        f = int(height * (0.20 + 0.25 * i))
        col = color_lerp(_TINTED_GLASS, _SPARKLE, 0.5 + 0.25 * i)
        d.line([(f, f), (height - f, height - f)], fill=col, width=int(height * 0.015))
        d.line([(height - f, f), (f, height - f)], fill=col, width=int(height * 0.015))
    return img


# --------------------------------------------------------------------------
# Item + particle texture and pack icon generators
# --------------------------------------------------------------------------
def particle_amber_sparkle(size: int, seed: int) -> Image.Image:
    img = _new_canvas(size)
    d = ImageDraw.Draw(img)
    cx, cy = size / 2, size / 2
    _star(cx, cy, size * 0.34, size * 0.14, _GOLDEN, img, 8)
    return img


def particle_fairy_dust(size: int, seed: int) -> Image.Image:
    rng = random.Random(seed)
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    height = size
    n = 10
    for i in range(n):
        a = i * 2 * math.pi / n + rng.uniform(0, 0.15)
        r = height * 0.42
        x = height / 2 + r * math.cos(a)
        y = height / 2 + r * math.sin(a)
        _dart(x, y, rng.uniform(0.8, 2.0), _SPARKLE, img)
    return img


def build_pack_icon() -> Image.Image:
    """128x128 pack icon: dark ring with a glowing amber crystal and leaf."""
    size = PACK_ICON_SIZE
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    cx, cy = size / 2, size / 2
    ring = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    ImageDraw.Draw(ring).ellipse([0, 0, size, size], fill=(13, 18, 32, 255))
    img = Image.alpha_composite(img, ring)
    glow = radial_glow(size, _GOLDEN, size * 0.40, 50)
    img = Image.alpha_composite(img, glow)
    d = ImageDraw.Draw(img)
    pts = []
    for i in range(6):
        a = 2 * math.pi * i / 6 - math.pi / 2
        rr = size * 0.24
        pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    d.polygon(pts, fill=alpha_over(_FROST, _AMBER_HOLO, 0))
    d.polygon(pts, fill=_AMBER_HOLO)
    lh = size * 0.16
    leaf = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    ImageDraw.Draw(leaf).polygon([(cx - lh, cy + size * 0.04),
                                   (cx, cy + size * 0.32),
                                   (cx + lh, cy + size * 0.04)],
                                  fill=_SPRING_MOSS)
    img = Image.alpha_composite(img, leaf)
    return img


# --------------------------------------------------------------------------
# Pack seed + texture registry
# --------------------------------------------------------------------------
import zlib


_PACK_SEED = 20260915


def _seed_for(name: str) -> int:
    return _PACK_SEED + (zlib.crc32(name.encode("ascii")) & 0xFFFFFFFF)


TEXTURE_TABLE: dict[str, object] = {}


def _register(path: str, fn: object) -> None:
    TEXTURE_TABLE[path] = fn


# --- block textures ---
_register("verdantreverie:block/deep_moss", block_moss)
_register("verdantreverie:block/sunlit_grass_top", block_grass_top)
_register("verdantreverie:block/sunlit_grass_side", block_grass_side)
_register("verdantreverie:block/amber_crystal", block_crystal)
_register("verdantreverie:block/pale_mushroom", block_mushroom)
_register("verdantreverie:block/frosted_ice", block_ice)
_register("verdantreverie:block/nightbloom", block_nightbloom)
_register("verdantreverie:block/vermillion_fern_top", block_fern_top)
_register("verdantreverie:block/vermillion_fern_side", block_fern_side)
_register("verdantreverie:block/leafy_vines", block_vines)
_register("verdantreverie:block/fairy_illium", block_illium)
_register("verdantreverie:block/mist_gate", block_mist_gate)
_register("verdantreverie:block/amber_gel_pit", block_amber_gel)
_register("verdantreverie:block/spirit_ore", block_spirit_ore)
_register("verdantreverie:block/driftwood_slab", block_driftwood)

# --- item textures ---
_register("verdantreverie:item/amber_crystal", item_amber_crystal)
_register("verdantreverie:item/vermillion_fern_sprout", item_fern_sprout)
_register("verdantreverie:item/pale_mushroom", item_pale_mushroom)
_register("verdantreverie:item/wild_berry", item_wild_berry)
_register("verdantreverie:item/amber_gel", item_amber_gel)
_register("verdantreverie:item/sparkler", item_sparkler)
_register("verdantreverie:item/moon_flower", item_moon_flower)
_register("verdantreverie:item/seedling", item_seedling)

# --- particle textures ---
_register("verdantreverie:particle/amber_sparkle", particle_amber_sparkle)
_register("verdantreverie:particle/fairy_dust", particle_fairy_dust)


def generate_all(resolution: int) -> dict[str, Image.Image]:
    """Return {resource path: RGBA image}, one per texture asset."""
    return {path: fn(resolution, _seed_for(path)) for path, fn in TEXTURE_TABLE.items()}
