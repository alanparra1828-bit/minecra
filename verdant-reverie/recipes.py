"""recipes.py - the Verdant Reverie resource-pack recipe.

This is the curated packaging manifest: package metadata, the asset lists,
and the JSON builders for models, blockstates and language files.  It does
not generate art - the art engine lives in artlib.py, and build.py wires
them together.
"""
from __future__ import annotations

# --- Package metadata -------------------------------------------------
PACK = {
    "name": "Verdant Reverie",
    "identifier": "verdantreverie:verdant-reverie",
    "description": "Verdant Reverie: a lush forest reverie in dense, glowing detail.",
    "version": "1.0.0",
    "min_format": [97, 1],
    "max_format": 97,
    "pack_format": 97,
}

# Namespace used for the pack's own assets (must be lowercase).
NAMESPACE = "verdantreverie"

# --- Assets -----------------------------------------------------------
# model: "flat" = cube_all solid tile; "grass" = grass parent using all+cross.
BLOCKS = [
    {"id": "deep_moss",       "name": "Deep Moss",               "model": "flat",
     "tex": "verdantreverie:block/deep_moss"},
    {"id": "sunlit_grass",    "name": "Sunlit Grass",            "model": "grass",
     "tex_side": "verdantreverie:block/sunlit_grass_side",
     "tex_top": "verdantreverie:block/sunlit_grass_top"},
    {"id": "amber_crystal",   "name": "Amber Crystal",           "model": "flat",
     "tex": "verdantreverie:block/amber_crystal"},
    {"id": "pale_mushroom",   "name": "Pale Mushroom",           "model": "flat",
     "tex": "verdantreverie:block/pale_mushroom"},
    {"id": "frosted_ice",     "name": "Frosted Ice",             "model": "flat",
     "tex": "verdantreverie:block/frosted_ice"},
    {"id": "nightbloom",      "name": "Nightbloom",              "model": "flat",
     "tex": "verdantreverie:block/nightbloom"},
    {"id": "vermillion_fern", "name": "Vermillion Fern",         "model": "grass",
     "tex_side": "verdantreverie:block/vermillion_fern_side",
     "tex_top": "verdantreverie:block/vermillion_fern_top"},
    {"id": "leafy_vines",     "name": "Leafy Vines",             "model": "flat",
     "tex": "verdantreverie:block/leafy_vines"},
    {"id": "fairy_illium",    "name": "Fairy Illium",            "model": "flat",
     "tex": "verdantreverie:block/fairy_illium"},
    {"id": "mist_gate",       "name": "Mist Gate",               "model": "flat",
     "tex": "verdantreverie:block/mist_gate"},
    {"id": "amber_gel_pit",   "name": "Amber Gel Pit",           "model": "flat",
     "tex": "verdantreverie:block/amber_gel_pit"},
    {"id": "spirit_ore",      "name": "Spirit Ore",              "model": "flat",
     "tex": "verdantreverie:block/spirit_ore"},
    {"id": "driftwood_slab",  "name": "Driftwood Slab",          "model": "flat",
     "tex": "verdantreverie:block/driftwood_slab"},
]

ITEMS = [
    {"id": "amber_crystal",   "name": "Amber Crystal",  "tex": "verdantreverie:item/amber_crystal"},
    {"id": "vermillion_fern_sprout", "name": "Fern Sprout", "tex": "verdantreverie:item/vermillion_fern_sprout"},
    {"id": "pale_mushroom",   "name": "Pale Mushroom",  "tex": "verdantreverie:item/pale_mushroom"},
    {"id": "wild_berry",      "name": "Wild Berry",     "tex": "verdantreverie:item/wild_berry"},
    {"id": "amber_gel",       "name": "Amber Gel",      "tex": "verdantreverie:item/amber_gel"},
    {"id": "sparkler",        "name": "Sparkler",       "tex": "verdantreverie:item/sparkler"},
    {"id": "moon_flower",     "name": "Moon Flower",   "tex": "verdantreverie:item/moon_flower"},
    {"id": "seedling",        "name": "Seedling",       "tex": "verdantreverie:item/seedling"},
]

PARTICLES = [
    {"id": "amber_sparkle", "name": "Amber Sparkle"},
    {"id": "fairy_dust",    "name": "Fairy Dust"},
]


# --- Packaging templates -----------------------------------------------
def flat_block_model(tex: str) -> dict:
    """A solid single-texture block on all six faces."""
    return {
        "parent": "minecraft:block/cube_all",
        "textures": {"all": tex},
        "elements": [{
            "from": [0, 0, 0],
            "to": [16, 16, 16],
            "faces": {
                "down":   {"texture": "#all", "cullface": "down"},
                "up":     {"texture": "#all", "cullface": "up"},
                "north":  {"texture": "#all", "cullface": "north"},
                "south":  {"texture": "#all", "cullface": "south"},
                "west":   {"texture": "#all", "cullface": "west"},
                "east":   {"texture": "#all", "cullface": "east"},
            },
        }],
    }


def grass_block_model(side_tex: str, top_tex: str) -> dict:
    """A block with a grass-like top over grassy sides."""
    return {
        "parent": "minecraft:block/grass",
        "textures": {"all": side_tex, "cross": top_tex},
    }


def item_model(tex: str) -> dict:
    """Flat generated item sprite."""
    return {
        "parent": "minecraft:item/generated",
        "textures": {"layer0": tex},
    }


def flat_blockstate() -> dict:
    return {"variants": {"": {"model": "#auto"}}}


def lang_data() -> dict:
    """Default English translation strings."""
    blocks = {b["id"]: b["name"] for b in BLOCKS}
    items = {i["id"]: i["name"] for i in ITEMS}
    data = {}
    for bid, name in blocks.items():
        data[f"block.{NAMESPACE}.{bid}"] = name
    for iid, name in items.items():
        data[f"item.{NAMESPACE}.{iid}"] = name
    for p in PARTICLES:
        data[f"particle.{NAMESPACE}.{p['id']}"] = p["name"]
    return data


# pack.mcmeta - the only two files the game reads to decide compatibility.
PACK_MCMETA = {
    "pack": {
        "description": PACK["description"],
        "pack_format": PACK["pack_format"],
        "min_format": PACK["min_format"],
        "max_format": PACK["max_format"],
    }
}
