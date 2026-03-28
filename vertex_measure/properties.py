import bpy
from bpy.props import (
    StringProperty,
    FloatProperty,
    FloatVectorProperty,
    BoolProperty,
    CollectionProperty,
    IntProperty,
)
from bpy.types import PropertyGroup


class MeasurementItem(PropertyGroup):
    name: StringProperty(name="Name", default="Meas.000")
    v1_co: FloatVectorProperty(name="Vertex 1", size=3, default=(0.0, 0.0, 0.0))
    v2_co: FloatVectorProperty(name="Vertex 2", size=3, default=(0.0, 0.0, 0.0))
    distance: FloatProperty(name="Distance", default=0.0, min=0.0)
    show_components: BoolProperty(name="Show Components", default=False)
    show_x: BoolProperty(name="X", default=True)
    show_y: BoolProperty(name="Y", default=True)
    show_z: BoolProperty(name="Z", default=True)


def register():
    bpy.utils.register_class(MeasurementItem)
    bpy.types.Object.vm_measurements = CollectionProperty(type=MeasurementItem)
    bpy.types.Object.vm_active_index = IntProperty(name="Active Measurement Index", default=0)


def unregister():
    if hasattr(bpy.types.Object, "vm_measurements"):
        del bpy.types.Object.vm_measurements
    if hasattr(bpy.types.Object, "vm_active_index"):
        del bpy.types.Object.vm_active_index
    bpy.utils.unregister_class(MeasurementItem)
