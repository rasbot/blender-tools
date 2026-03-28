"""Vertex Measure — persistent vertex-pair distance measurements with viewport overlays.

Measurements are stored per-object and survive file save/load.  Each measurement
can optionally display X, Y, and Z component distances alongside the total.
All display settings (units, precision, colours, font size) are configurable
via Add-on Preferences or the N-panel Display Settings sub-panel.
"""

bl_info = {
    "name": "Vertex Measure",
    "author": "",
    "version": (1, 0, 0),
    "blender": (4, 0, 0),
    "location": "View3D > Sidebar > Measure",
    "description": (
        "Measure distances between vertex pairs with persistent, "
        "per-object overlays and optional X/Y/Z component breakdown"
    ),
    "category": "Mesh",
}

from . import preferences, properties, operators, draw, ui


def register() -> None:
    """Register all vertex-measure sub-modules in dependency order."""
    preferences.register()
    properties.register()
    operators.register()
    draw.register()
    ui.register()


def unregister() -> None:
    """Unregister all vertex-measure sub-modules in reverse dependency order."""
    ui.unregister()
    draw.unregister()
    operators.unregister()
    properties.unregister()
    preferences.unregister()


if __name__ == "__main__":
    register()
