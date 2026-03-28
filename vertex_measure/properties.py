"""Per-object measurement collection property for the Vertex Measure addon."""

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
    """A single vertex-pair distance measurement stored on an object.

    Vertex coordinates are stored in local object space so they transform
    correctly when the object is moved or scaled.  The ``distance`` value
    is stored in metres (Blender's internal unit) and converted for display
    by ``format_distance`` in the preferences module.
    """

    name: StringProperty(name="Name", default="Meas.000")
    v1_co: FloatVectorProperty(name="Vertex 1", size=3, default=(0.0, 0.0, 0.0))
    v2_co: FloatVectorProperty(name="Vertex 2", size=3, default=(0.0, 0.0, 0.0))
    distance: FloatProperty(name="Distance", default=0.0, min=0.0)
    show_components: BoolProperty(name="Show Components", default=False)
    show_x: BoolProperty(name="X", default=True)
    show_y: BoolProperty(name="Y", default=True)
    show_z: BoolProperty(name="Z", default=True)


def register() -> None:
    """Register MeasurementItem and attach the collection to bpy.types.Object."""
    bpy.utils.register_class(MeasurementItem)
    bpy.types.Object.vm_measurements = CollectionProperty(type=MeasurementItem)
    bpy.types.Object.vm_active_index = IntProperty(name="Active Measurement Index", default=0)


def unregister() -> None:
    """Remove object attributes and unregister MeasurementItem."""
    if hasattr(bpy.types.Object, "vm_measurements"):
        del bpy.types.Object.vm_measurements
    if hasattr(bpy.types.Object, "vm_active_index"):
        del bpy.types.Object.vm_active_index
    bpy.utils.unregister_class(MeasurementItem)
