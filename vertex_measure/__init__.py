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


def register():
    preferences.register()
    properties.register()
    operators.register()
    draw.register()
    ui.register()


def unregister():
    ui.unregister()
    draw.unregister()
    operators.unregister()
    properties.unregister()
    preferences.unregister()


if __name__ == "__main__":
    register()
