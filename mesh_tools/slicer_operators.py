import bpy
import math
from bpy.props import EnumProperty
from mathutils import Vector, Euler, Matrix


def _plane_from_props(props):
    """Return (origin: Vector, normal: Vector) in world space from scene ps_props."""
    rot = Euler(tuple(props.plane_rotation), 'XYZ')
    normal = (rot.to_matrix() @ Vector((0.0, 0.0, 1.0))).normalized()
    return Vector(props.plane_origin), normal


def _bisect_object(obj, plane_co, plane_no, fill_cut, clear_inner, clear_outer):
    """Enter edit mode on obj, bisect it, and return to object mode."""
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.bisect(
        plane_co=tuple(plane_co),
        plane_no=tuple(plane_no),
        use_fill=fill_cut,
        clear_inner=clear_inner,
        clear_outer=clear_outer,
    )
    bpy.ops.object.mode_set(mode='OBJECT')


class PS_OT_SliceMesh(bpy.types.Operator):
    bl_idname = "ps.slice_mesh"
    bl_label = "Slice Mesh"
    bl_description = (
        "Slice the active mesh into two separate objects along the defined plane. "
        "The original is kept as '<name>_A' (outer side) and a new '<name>_B' (inner side) is created"
    )
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return (
            context.active_object is not None
            and context.active_object.type == 'MESH'
            and context.mode == 'OBJECT'
        )

    def execute(self, context):
        obj = context.active_object
        props = context.scene.ps_props
        plane_co, plane_no = _plane_from_props(props)
        original_name = obj.name

        # Duplicate original to get the second half
        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)
        context.view_layer.objects.active = obj
        bpy.ops.object.duplicate(linked=False)
        obj_b = context.active_object   # the duplicate

        # Slice the original — keep outer (positive normal side), remove inner
        _bisect_object(
            obj, plane_co, plane_no, props.fill_cut,
            clear_inner=True, clear_outer=False,
        )
        obj.name = original_name + "_A"

        # Slice the duplicate — keep inner (negative normal side), remove outer
        _bisect_object(
            obj_b, plane_co, plane_no, props.fill_cut,
            clear_inner=False, clear_outer=True,
        )
        obj_b.name = original_name + "_B"

        self.report(
            {'INFO'},
            f"Sliced '{original_name}' → '{obj.name}' and '{obj_b.name}'",
        )
        return {'FINISHED'}


class PS_OT_CenterPlane(bpy.types.Operator):
    bl_idname = "ps.center_plane"
    bl_label = "Center on Active"
    bl_description = (
        "Move the slice plane origin to the active object's bounding box center "
        "and resize the display to match the object"
    )
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return (
            context.active_object is not None
            and context.active_object.type == 'MESH'
        )

    def execute(self, context):
        obj = context.active_object
        world_corners = [obj.matrix_world @ Vector(c) for c in obj.bound_box]

        center = sum(world_corners, Vector()) / 8.0

        # Size plane to fit the object's bounding box diagonal
        xs = [c.x for c in world_corners]
        ys = [c.y for c in world_corners]
        zs = [c.z for c in world_corners]
        bbox_min = Vector((min(xs), min(ys), min(zs)))
        bbox_max = Vector((max(xs), max(ys), max(zs)))
        diagonal = (bbox_max - bbox_min).length

        props = context.scene.ps_props
        props.plane_origin = center
        props.plane_size = max(diagonal, 0.01)
        return {'FINISHED'}


class PS_OT_AlignToAxis(bpy.types.Operator):
    bl_idname = "ps.align_to_axis"
    bl_label = "Align to Axis"
    bl_description = "Snap the slice plane to a world axis-aligned orientation"
    bl_options = {'REGISTER', 'UNDO'}

    axis: EnumProperty(
        name="Axis",
        items=[
            ('XY', "XY Plane", "Normal along world +Z"),
            ('XZ', "XZ Plane", "Normal along world +Y"),
            ('YZ', "YZ Plane", "Normal along world +X"),
        ],
        default='XY',
    )

    def execute(self, context):
        props = context.scene.ps_props
        if self.axis == 'XY':
            props.plane_rotation = (0.0, 0.0, 0.0)
        elif self.axis == 'XZ':
            props.plane_rotation = (math.radians(90.0), 0.0, 0.0)
        elif self.axis == 'YZ':
            props.plane_rotation = (0.0, math.radians(90.0), 0.0)
        return {'FINISHED'}


class PS_OT_AlignToView(bpy.types.Operator):
    bl_idname = "ps.align_to_view"
    bl_label = "Align to View"
    bl_description = "Orient the slice plane to face the current viewport camera"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return (
            context.area is not None
            and context.area.type == 'VIEW_3D'
            and context.space_data is not None
        )

    def execute(self, context):
        rv3d = context.space_data.region_3d

        # view_rotation rotates from view space to world space.
        # Applying it to (0,0,1) gives the world-space direction of view +Z,
        # which points from the scene toward the viewer.
        view_normal = (rv3d.view_rotation @ Vector((0.0, 0.0, 1.0))).normalized()

        # Build a rotation matrix whose local Z axis is view_normal
        z_axis = view_normal
        ref = Vector((1.0, 0.0, 0.0)) if abs(z_axis.dot(Vector((1.0, 0.0, 0.0)))) < 0.9 else Vector((0.0, 1.0, 0.0))
        x_axis = ref.cross(z_axis).normalized()
        y_axis = z_axis.cross(x_axis).normalized()

        rot_mat = Matrix([
            [x_axis.x, y_axis.x, z_axis.x],
            [x_axis.y, y_axis.y, z_axis.y],
            [x_axis.z, y_axis.z, z_axis.z],
        ])
        context.scene.ps_props.plane_rotation = rot_mat.to_euler('XYZ')
        return {'FINISHED'}


class PS_OT_PlaceAtCursor(bpy.types.Operator):
    bl_idname = "ps.place_at_cursor"
    bl_label = "Place at Cursor"
    bl_description = "Move the slice plane origin to the 3D cursor"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        context.scene.ps_props.plane_origin = context.scene.cursor.location
        return {'FINISHED'}


CLASSES = [PS_OT_SliceMesh, PS_OT_CenterPlane, PS_OT_AlignToAxis, PS_OT_AlignToView, PS_OT_PlaceAtCursor]


def register():
    for cls in CLASSES:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)
