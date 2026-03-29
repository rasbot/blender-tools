"""Scene-level properties for the Plane Slicer tool."""

import bpy
from bpy.props import FloatVectorProperty, FloatProperty, BoolProperty, PointerProperty
from bpy.types import PropertyGroup


def _redraw(self: bpy.types.PropertyGroup, context: bpy.types.Context) -> None:
    """Tag all VIEW_3D areas for redraw when a slicer property changes."""
    for area in context.screen.areas:
        if area.type == 'VIEW_3D':
            area.tag_redraw()


class PlaneSlicerProps(PropertyGroup):
    """Scene-level settings for the Plane Slicer tool.

    The slice plane is fully described by an origin point and a rotation
    (whose local Z axis is the plane normal).  ``show_plane`` gates the
    viewport preview draw callback so the overlay is off by default.
    """

    plane_origin: FloatVectorProperty(
        name="Origin",
        description="A point the slice plane passes through",
        size=3, subtype='TRANSLATION',
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
        default=0.002, min=0.00001, max=10.0, unit='LENGTH',
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


def register() -> None:
    """Register PlaneSlicerProps and attach it to bpy.types.Scene."""
    bpy.utils.register_class(PlaneSlicerProps)
    bpy.types.Scene.ps_props = PointerProperty(type=PlaneSlicerProps)


def unregister() -> None:
    """Remove the scene attribute and unregister PlaneSlicerProps."""
    if hasattr(bpy.types.Scene, 'ps_props'):
        del bpy.types.Scene.ps_props
    bpy.utils.unregister_class(PlaneSlicerProps)
