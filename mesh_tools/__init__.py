bl_info = {
    "name": "Mesh Tools",
    "author": "",
    "version": (1, 0, 0),
    "blender": (4, 0, 0),
    "location": "View3D > Sidebar > Mesh Tools",
    "description": "Collection of mesh alignment and manipulation tools",
    "category": "Mesh",
}

from . import properties, operators, ui
from . import slicer_properties, slicer_operators, slicer_draw, slicer_ui
from . import peg_cutter_properties, peg_cutter_operators, peg_cutter_draw, peg_cutter_ui


def register():
    properties.register()
    operators.register()
    ui.register()
    slicer_properties.register()
    slicer_operators.register()
    slicer_draw.register()
    slicer_ui.register()
    peg_cutter_properties.register()
    peg_cutter_operators.register()
    peg_cutter_draw.register()
    peg_cutter_ui.register()


def unregister():
    peg_cutter_ui.unregister()
    peg_cutter_draw.unregister()
    peg_cutter_operators.unregister()
    peg_cutter_properties.unregister()
    slicer_ui.unregister()
    slicer_draw.unregister()
    slicer_operators.unregister()
    slicer_properties.unregister()
    ui.unregister()
    operators.unregister()
    properties.unregister()


if __name__ == "__main__":
    register()
