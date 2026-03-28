import bpy
from bpy.props import FloatVectorProperty, FloatProperty, BoolProperty, PointerProperty
from bpy.types import PropertyGroup


def _redraw(self, context):
    for area in context.screen.areas:
        if area.type == 'VIEW_3D':
            area.tag_redraw()


class PlaneSlicerProps(PropertyGroup):
    plane_origin: FloatVectorProperty(
        name="Origin",
        description="A point the slice plane passes through",
        size=3, subtype='XYZ',
        default=(0.0, 0.0, 0.0),
        update=_redraw,
    )
    plane_rotation: FloatVectorProperty(
        name="Rotation",
        description="Orientation of the slice plane (plane normal is its local Z axis)",
        size=3, subtype='EULER', unit='ROTATION',
        default=(0.0, 0.0, 0.0),
        update=_redraw,
    )
    plane_size: FloatProperty(
        name="Display Size",
        description="Visual size of the plane preview in the viewport",
        default=2.0, min=0.01, max=10000.0,
        update=_redraw,
    )
    fill_cut: BoolProperty(
        name="Fill Cut",
        description="Cap the open edges of each slice with a face",
        default=True,
    )
    show_plane: BoolProperty(
        name="Show Plane",
        description="Draw the slice plane preview in the viewport",
        default=False,
        update=_redraw,
    )
    plane_color: FloatVectorProperty(
        name="Plane Color",
        description="Color and opacity of the plane preview",
        subtype='COLOR_GAMMA', size=4,
        default=(0.2, 0.6, 1.0, 0.25),
        min=0.0, max=1.0,
        update=_redraw,
    )


def register():
    bpy.utils.register_class(PlaneSlicerProps)
    bpy.types.Scene.ps_props = PointerProperty(type=PlaneSlicerProps)


def unregister():
    if hasattr(bpy.types.Scene, 'ps_props'):
        del bpy.types.Scene.ps_props
    bpy.utils.unregister_class(PlaneSlicerProps)
