"""Top-level package for comfy_nanobanana."""

__all__ = [
    "NODE_CLASS_MAPPINGS",
    "NODE_DISPLAY_NAME_MAPPINGS",
    "WEB_DIRECTORY",
]

__author__ = """comfy_nanobanana"""
__email__ = "hxtxmu@gmail.com"
__version__ = "0.0.1"

# Expose node mappings
from .src.comfy_nanobanana.nodes import NODE_CLASS_MAPPINGS
from .src.comfy_nanobanana.nodes import NODE_DISPLAY_NAME_MAPPINGS

# Expose web assets directory so ComfyUI loads frontend extensions (JS)
WEB_DIRECTORY = "./web"

