import bpy
from bpy.props import StringProperty, IntProperty, EnumProperty, PointerProperty
from bpy.types import PropertyGroup


class PlaneAlignProps(PropertyGroup):
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


def register():
    bpy.utils.register_class(PlaneAlignProps)
    bpy.types.Scene.pa_props = PointerProperty(type=PlaneAlignProps)


def unregister():
    if hasattr(bpy.types.Scene, 'pa_props'):
        del bpy.types.Scene.pa_props
    bpy.utils.unregister_class(PlaneAlignProps)
