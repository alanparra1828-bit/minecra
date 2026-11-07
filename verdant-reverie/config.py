"""Verdant Reverie — configuration and shared constants.

Every value here is a single source of truth for the build system.
"""
from __future__ import annotations

# --- Project identity -------------------------------------------------
PACK_NAME = "Verdant Reverie"
PACK_TITLE = "Verdant Reverie"
NAMESPACE = "verdantreverie"          # must be lowercase (Java rule)
IDENTIFIER = f"{NAMESPACE}:{PACK_NAME}"

# Transparent/solid colour key used when compositing foliage details:
# we keep full alpha for block faces (solid tile) and true transparency
# for item / particle sprites.

# --- Resolutions ------------------------------------------------------
# Resolution = number of pixels along one edge of a single block face.
# Vanilla is 16x.  Every texture in a given build must share the same base.
RESOLUTIONS = {
    "512x": 512,
    "1024x": 1024,
    "2048x": 2048,
}
DEFAULT_RESOLUTION = "1024x"

# --- Minecraft version target (Java 26.3, "Wilderness Bound") ---------
# Resource pack format 97.1 (held steady through the 26.3 cycle).
PACK_FORMAT = 97
MIN_FORMAT = [97, 1]
MAX_FORMAT = 97
DESCRIPTION = "Verdant Reverie: a lush forest reverie in dense, glowing detail."

# --- Icon -------------------------------------------------------------
PACK_ICON_SIZE = 128  # in-game menu icon (not resolution-scaled)

# --- Artwork source -------------------------------------------
# Procedural generation base resolution.  Textures are drawn at 512 and
# cleanly upscaled to 1024/2048 so every build keeps identical art.
ART_WORK_RES = 512
