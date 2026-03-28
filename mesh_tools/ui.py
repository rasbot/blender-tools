import bpy
from bpy.types import Panel


class MT_PT_PlaneAlign(Panel):
    bl_label      = "Plane Align"
    bl_idname     = "MT_PT_PlaneAlign"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category   = "Mesh Tools"

    def draw(self, context):
        layout = self.layout
        props  = context.scene.pa_props

        # --- Source pick ---
        src_box = layout.box()
        src_box.label(text="Source  (mesh to move)", icon='OBJECT_DATA')

        col = src_box.column(align=True)
        if props.picking_mode == 'SOURCE':
            col.label(text="Click a face on the source mesh…", icon='MOUSE_LMB')
        else:
            op = col.operator("pa.pick_face", text="Pick Source Face", icon='RESTRICT_SELECT_OFF')
            op.slot = 'SOURCE'

        if props.source_obj_name:
            col.label(
                text=f"  {props.source_obj_name},  face {props.source_face_index}",
                icon='CHECKMARK',
            )
        else:
            col.label(text="  Not picked", icon='X')

        layout.separator(factor=0.5)

        # --- Target pick ---
        tgt_box = layout.box()
        tgt_box.label(text="Target  (reference mesh)", icon='OBJECT_DATA')

        col2 = tgt_box.column(align=True)
        if props.picking_mode == 'TARGET':
            col2.label(text="Click a face on the target mesh…", icon='MOUSE_LMB')
        else:
            op2 = col2.operator("pa.pick_face", text="Pick Target Face", icon='RESTRICT_SELECT_OFF')
            op2.slot = 'TARGET'

        if props.target_obj_name:
            col2.label(
                text=f"  {props.target_obj_name},  face {props.target_face_index}",
                icon='CHECKMARK',
            )
        else:
            col2.label(text="  Not picked", icon='X')

        layout.separator()

        # --- Action buttons ---
        both_picked = (
            props.source_obj_name != ""
            and props.target_obj_name != ""
            and props.source_face_index >= 0
            and props.target_face_index >= 0
            and props.picking_mode == 'NONE'
        )

        col3 = layout.column(align=True)
        col3.scale_y = 1.3
        col3.enabled = both_picked
        col3.operator("pa.align_planes", text="Align Planes", icon='CON_TRACKTO')

        layout.operator("pa.clear_picks", text="Clear Picks", icon='TRASH')


CLASSES = [MT_PT_PlaneAlign]


def register():
    for cls in CLASSES:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)
