"""Operators for the Plane Align tool.

Provides three operators:
* ``PA_OT_PickFace``    — modal viewport face picker (source or target slot)
* ``PA_OT_AlignPlanes`` — moves/rotates the source object so its face is flush
                          with the target face (face-to-face / CAD mate)
* ``PA_OT_ClearPicks``  — resets all picks and the picking-mode state machine
"""

import bpy
from bpy.props import EnumProperty
from bpy_extras.view3d_utils import region_2d_to_origin_3d, region_2d_to_vector_3d
from mathutils import Vector


def _raycast(
    context: bpy.types.Context,
    event: bpy.types.Event,
) -> tuple[bpy.types.Object | None, int]:
    """Cast a ray from the mouse cursor into the scene.

    Parameters
    ----------
    context:
        Current Blender context (must have a VIEW_3D area active).
    event:
        The mouse event whose screen coordinates drive the ray.

    Returns
    -------
    tuple[Object | None, int]
        ``(obj, face_index)`` of the first mesh face hit, or ``(None, -1)``
        if no mesh was hit.
    """
    region = context.region
    rv3d = context.space_data.region_3d
    coord = (event.mouse_region_x, event.mouse_region_y)

    origin    = region_2d_to_origin_3d(region, rv3d, coord)
    direction = region_2d_to_vector_3d(region, rv3d, coord)

    depsgraph = context.evaluated_depsgraph_get()
    hit, _loc, _normal, face_idx, obj, _matrix = context.scene.ray_cast(
        depsgraph, origin, direction
    )

    if hit and obj and obj.type == 'MESH':
        return obj, face_idx
    return None, -1


class PA_OT_PickFace(bpy.types.Operator):
    """Modal operator that waits for the user to click a mesh face.

    The picked object name and face index are stored in ``pa_props`` under
    whichever ``slot`` ('SOURCE' or 'TARGET') was requested.  A stale-modal
    guard (checking ``picking_mode``) ensures only one picker runs at a time.
    """

    bl_idname = "pa.pick_face"
    bl_label  = "Pick Face"
    bl_description = "Click a mesh face in the viewport to set it as the pick target"
    bl_options = {'REGISTER'}  # no UNDO — modal operators must not push undo states

    slot: EnumProperty(
        items=[('SOURCE', "Source", ""), ('TARGET', "Target", "")],
        default='SOURCE',
    )

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        """Require Object Mode inside a 3-D viewport."""
        return (
            context.mode == 'OBJECT'
            and context.area is not None
            and context.area.type == 'VIEW_3D'
        )

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event) -> set[str]:
        """Begin the modal pick session."""
        props = context.scene.pa_props
        props.picking_mode = self.slot
        context.window.cursor_modal_set('CROSSHAIR')
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def modal(self, context: bpy.types.Context, event: bpy.types.Event) -> set[str]:
        """Handle each event while the picker is active."""
        props = context.scene.pa_props

        # If another pick was started, this modal is stale — exit cleanly
        if props.picking_mode != self.slot:
            context.window.cursor_modal_restore()
            return {'CANCELLED'}

        if event.type == 'LEFTMOUSE' and event.value == 'PRESS':
            obj, face_idx = _raycast(context, event)
            if obj is not None:
                if self.slot == 'SOURCE':
                    props.source_obj_name   = obj.name
                    props.source_face_index = face_idx
                else:
                    props.target_obj_name   = obj.name
                    props.target_face_index = face_idx
                props.picking_mode = 'NONE'
                context.window.cursor_modal_restore()
                for area in context.screen.areas:
                    if area.type == 'VIEW_3D':
                        area.tag_redraw()
                return {'FINISHED'}
            else:
                self.report({'WARNING'}, "No mesh face hit — click directly on a mesh surface")
                return {'RUNNING_MODAL'}

        elif event.type in {'RIGHTMOUSE', 'ESC'}:
            props.picking_mode = 'NONE'
            context.window.cursor_modal_restore()
            return {'CANCELLED'}

        # Pass everything else through so viewport navigation still works
        return {'PASS_THROUGH'}


class PA_OT_AlignPlanes(bpy.types.Operator):
    """Move and rotate the source object so its picked face is flush with the target face.

    Algorithm
    ---------
    1. Compute world-space face normals via the inverse-transpose of each
       object's 3×3 model matrix (correct under non-uniform scale).
    2. Find the quaternion that rotates the source normal to be antiparallel
       to the target normal (face-to-face orientation).
    3. Apply the rotation by left-multiplying ``matrix_world`` (world-space
       rotation about the world origin).
    4. Translate so the source face centre coincides with the target face centre.
    """

    bl_idname  = "pa.align_planes"
    bl_label   = "Align Planes"
    bl_description = (
        "Move and rotate the source object so its picked face is "
        "flush (face-to-face) with the target face"
    )
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        """Require both faces to be picked and no pick in progress."""
        props = context.scene.pa_props
        return (
            props.source_obj_name != ""
            and props.target_obj_name != ""
            and props.source_face_index >= 0
            and props.target_face_index >= 0
            and props.picking_mode == 'NONE'
        )

    def execute(self, context: bpy.types.Context) -> set[str]:
        """Perform the face-to-face alignment."""
        props = context.scene.pa_props

        # --- Validate ---
        src_obj = bpy.data.objects.get(props.source_obj_name)
        tgt_obj = bpy.data.objects.get(props.target_obj_name)

        if src_obj is None or tgt_obj is None:
            self.report({'ERROR'}, "Source or target object no longer exists — re-pick faces")
            return {'CANCELLED'}

        if src_obj is tgt_obj:
            self.report({'ERROR'}, "Source and target must be different objects")
            return {'CANCELLED'}

        if src_obj.type != 'MESH' or tgt_obj.type != 'MESH':
            self.report({'ERROR'}, "Both objects must be mesh type")
            return {'CANCELLED'}

        src_fi = props.source_face_index
        tgt_fi = props.target_face_index
        src_mesh = src_obj.data
        tgt_mesh = tgt_obj.data

        if src_fi >= len(src_mesh.polygons):
            self.report({'ERROR'}, "Source face index out of range — re-pick source face")
            return {'CANCELLED'}
        if tgt_fi >= len(tgt_mesh.polygons):
            self.report({'ERROR'}, "Target face index out of range — re-pick target face")
            return {'CANCELLED'}

        src_face = src_mesh.polygons[src_fi]
        tgt_face = tgt_mesh.polygons[tgt_fi]

        src_M = src_obj.matrix_world.copy()
        tgt_M = tgt_obj.matrix_world.copy()

        # --- World-space normals via inverse-transpose (correct under non-uniform scale) ---
        try:
            src_normal_mat = src_M.to_3x3().inverted().transposed()
        except ValueError:
            self.report({'ERROR'}, "Source object has a zero scale axis — cannot compute normal")
            return {'CANCELLED'}

        try:
            tgt_normal_mat = tgt_M.to_3x3().inverted().transposed()
        except ValueError:
            self.report({'ERROR'}, "Target object has a zero scale axis — cannot compute normal")
            return {'CANCELLED'}

        n_src = (src_normal_mat @ Vector(src_face.normal)).normalized()
        n_tgt = (tgt_normal_mat @ Vector(tgt_face.normal)).normalized()

        # --- Rotation: align source normal antiparallel to target normal (face-to-face) ---
        rot_q   = n_src.rotation_difference(-n_tgt)
        rot_mat = rot_q.to_matrix().to_4x4()

        # --- Apply rotation (left-multiply = world-space rotation about world origin) ---
        src_obj.matrix_world = rot_mat @ src_M
        context.view_layer.update()  # flush matrix_world → location/rotation/scale

        # --- Translate: bring source face centre to target face centre ---
        new_p_src = src_obj.matrix_world @ Vector(src_face.center)
        p_tgt     = tgt_M @ Vector(tgt_face.center)
        delta     = p_tgt - new_p_src

        new_mw = src_obj.matrix_world.copy()
        new_mw.translation += delta
        src_obj.matrix_world = new_mw
        context.view_layer.update()

        # --- Redraw ---
        for area in context.screen.areas:
            if area.type == 'VIEW_3D':
                area.tag_redraw()

        self.report(
            {'INFO'},
            f"Aligned '{src_obj.name}' face {src_fi} → '{tgt_obj.name}' face {tgt_fi}",
        )
        return {'FINISHED'}


class PA_OT_ClearPicks(bpy.types.Operator):
    """Reset all face picks and the picking-mode state machine."""

    bl_idname  = "pa.clear_picks"
    bl_label   = "Clear Picks"
    bl_description = "Clear all picked faces and reset the tool state"
    bl_options = {'REGISTER'}

    def execute(self, context: bpy.types.Context) -> set[str]:
        """Clear all pick data and restore the cursor."""
        props = context.scene.pa_props
        props.source_obj_name   = ""
        props.source_face_index = -1
        props.target_obj_name   = ""
        props.target_face_index = -1
        props.picking_mode      = 'NONE'
        context.window.cursor_modal_restore()
        return {'FINISHED'}


CLASSES = [PA_OT_PickFace, PA_OT_AlignPlanes, PA_OT_ClearPicks]


def register() -> None:
    """Register all Plane Align operators."""
    for cls in CLASSES:
        bpy.utils.register_class(cls)


def unregister() -> None:
    """Unregister all Plane Align operators."""
    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)
