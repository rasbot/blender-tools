"""Operators for the Vertex Measure addon.

Provides two operators:
* ``VM_OT_AddMeasurement``    — record the distance between the two selected
                                vertices in Edit Mode and store it on the object
* ``VM_OT_RemoveMeasurement`` — delete a measurement by object name and index
"""

import bpy
import bmesh
from mathutils import Vector


class VM_OT_AddMeasurement(bpy.types.Operator):
    """Add a distance measurement between exactly two selected vertices.

    Vertex coordinates are stored in local space; the world-space distance
    (accounting for object scale) is computed at capture time and stored in
    metres so ``format_distance`` can convert to any display unit.
    """

    bl_idname = "vm.add_measurement"
    bl_label = "Add Measurement"
    bl_description = "Add a distance measurement between two selected vertices"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        """Require an active mesh object in Edit Mode."""
        obj = context.active_object
        return (
            obj is not None
            and obj.type == 'MESH'
            and context.mode == 'EDIT_MESH'
        )

    def execute(self, context: bpy.types.Context) -> set[str]:
        """Capture the selected vertex pair and store the measurement."""
        obj = context.active_object
        bm = bmesh.from_edit_mesh(obj.data)
        bm.verts.ensure_lookup_table()

        selected = [v for v in bm.verts if v.select]
        if len(selected) != 2:
            self.report({'ERROR'}, "Select exactly 2 vertices")
            return {'CANCELLED'}

        v1_co = selected[0].co.copy()
        v2_co = selected[1].co.copy()

        v1_world = obj.matrix_world @ v1_co
        v2_world = obj.matrix_world @ v2_co
        scale = context.scene.unit_settings.scale_length
        distance = (v2_world - v1_world).length * scale  # stored in metres

        count = len(obj.vm_measurements)
        meas = obj.vm_measurements.add()
        meas.name = f"Meas.{count:03d}"
        meas.v1_co = v1_co
        meas.v2_co = v2_co
        meas.distance = distance

        # Redraw all 3-D viewports
        for area in context.screen.areas:
            if area.type == 'VIEW_3D':
                area.tag_redraw()

        self.report({'INFO'}, f"Added {meas.name}: {distance:.6f} m")
        return {'FINISHED'}


class VM_OT_RemoveMeasurement(bpy.types.Operator):
    """Remove a single measurement from an object by index."""

    bl_idname = "vm.remove_measurement"
    bl_label = "Remove Measurement"
    bl_description = "Remove this measurement"
    bl_options = {'REGISTER', 'UNDO'}

    obj_name: bpy.props.StringProperty()
    index: bpy.props.IntProperty()

    def execute(self, context: bpy.types.Context) -> set[str]:
        """Look up the object and remove the measurement at the stored index."""
        obj = bpy.data.objects.get(self.obj_name)
        if obj is None:
            self.report({'ERROR'}, f"Object '{self.obj_name}' not found")
            return {'CANCELLED'}

        measurements = obj.vm_measurements
        if self.index < 0 or self.index >= len(measurements):
            self.report({'ERROR'}, "Invalid measurement index")
            return {'CANCELLED'}

        measurements.remove(self.index)

        for area in context.screen.areas:
            if area.type == 'VIEW_3D':
                area.tag_redraw()

        return {'FINISHED'}


CLASSES = [VM_OT_AddMeasurement, VM_OT_RemoveMeasurement]


def register() -> None:
    """Register all Vertex Measure operators."""
    for cls in CLASSES:
        bpy.utils.register_class(cls)


def unregister() -> None:
    """Unregister all Vertex Measure operators."""
    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)
