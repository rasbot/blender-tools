"""Scene-level properties for the Plane Align tool."""

import bpy
from bpy.props import StringProperty, IntProperty, EnumProperty, PointerProperty
from bpy.types import PropertyGroup


class PlaneAlignProps(PropertyGroup):
    """Stores the two face picks and modal-picker state for the Plane Align tool.

    Both picks are stored as (object name, face index) pairs so they survive
    object renames and undo steps.  ``picking_mode`` drives the state machine
    that prevents two modal pickers running simultaneously.
    """

    source_obj_name: StringProperty(name="Source Object", default="")
    source_face_index: IntProperty(name="Source Face", default=-1)
    target_obj_name: StringProperty(name="Target Object", default="")
    target_face_index: IntProperty(name="Target Face", default=-1)
    picking_mode: EnumProperty(
        name="Picking Mode",
        items=[
            ('NONE',   "None",   "No pick in progress"),
            ('SOURCE', "Source", "Picking source face"),
            ('TARGET', "Target", "Picking target face"),
        ],
        default='NONE',
    )


def register() -> None:
    """Register PlaneAlignProps and attach it to bpy.types.Scene."""
    bpy.utils.register_class(PlaneAlignProps)
    bpy.types.Scene.pa_props = PointerProperty(type=PlaneAlignProps)


def unregister() -> None:
    """Remove the scene attribute and unregister PlaneAlignProps."""
    if hasattr(bpy.types.Scene, 'pa_props'):
        del bpy.types.Scene.pa_props
    bpy.utils.unregister_class(PlaneAlignProps)
