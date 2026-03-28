import bpy
import bmesh
from mathutils import Vector


class VM_OT_AddMeasurement(bpy.types.Operator):
    bl_idname = "vm.add_measurement"
    bl_label = "Add Measurement"
    bl_description = "Add a distance measurement between two selected vertices"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return (
            obj is not None
            and obj.type == 'MESH'
            and context.mode == 'EDIT_MESH'
        )

    def execute(self, context):
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
        distance = (v2_world - v1_world).length * scale  # stored in meters

        count = len(obj.vm_measurements)
        meas = obj.vm_measurements.add()
        meas.name = f"Meas.{count:03d}"
        meas.v1_co = v1_co
        meas.v2_co = v2_co
        meas.distance = distance

        # Redraw all 3D viewports
        for area in context.screen.areas:
            if area.type == 'VIEW_3D':
                area.tag_redraw()

        self.report({'INFO'}, f"Added {meas.name}: {distance:.6f} m")
        return {'FINISHED'}


class VM_OT_RemoveMeasurement(bpy.types.Operator):
    bl_idname = "vm.remove_measurement"
    bl_label = "Remove Measurement"
    bl_description = "Remove this measurement"
    bl_options = {'REGISTER', 'UNDO'}

    obj_name: bpy.props.StringProperty()
    index: bpy.props.IntProperty()

    def execute(self, context):
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


def register():
    for cls in CLASSES:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)
