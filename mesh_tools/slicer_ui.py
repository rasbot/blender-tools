import bpy
from bpy.types import Panel


class PS_PT_PlaneSlicer(Panel):
    bl_label      = "Plane Slicer"
    bl_idname     = "PS_PT_PlaneSlicer"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category   = "Mesh Tools"
    bl_options    = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        props  = context.scene.ps_props
        obj    = context.active_object

        # Target status
        if obj and obj.type == 'MESH' and context.mode == 'OBJECT':
            layout.label(text=f"Target: {obj.name}", icon='MESH_DATA')
        elif context.mode != 'OBJECT':
            layout.label(text="Switch to Object Mode to slice", icon='ERROR')
        else:
            layout.label(text="Select a mesh object to slice", icon='ERROR')

        layout.separator()

        # --- Plane origin ---
        col = layout.column(align=True)
        col.label(text="Plane Origin:")
        col.prop(props, "plane_origin", text="")
        row = col.row(align=True)
        row.operator("ps.place_at_cursor", text="Place at Cursor", icon='CURSOR')
        row.operator("ps.center_plane", text="Center on Active", icon='OBJECT_ORIGIN')

        layout.separator()

        # --- Plane rotation ---
        col2 = layout.column(align=True)
        col2.label(text="Rotation:")
        col2.prop(props, "plane_rotation", text="")

        # Axis snap presets
        row = layout.row(align=True)
        row.label(text="Snap:")
        sub = row.row(align=True)
        op = sub.operator("ps.align_to_axis", text="XY")
        op.axis = 'XY'
        op = sub.operator("ps.align_to_axis", text="XZ")
        op.axis = 'XZ'
        op = sub.operator("ps.align_to_axis", text="YZ")
        op.axis = 'YZ'

        layout.operator("ps.align_to_view", text="Align to View", icon='CAMERA_DATA')

        layout.separator()

        # --- Display settings ---
        box = layout.box()
        box.label(text="Preview", icon='HIDE_OFF')
        col3 = box.column(align=True)
        col3.prop(props, "show_plane", toggle=True,
                  icon='HIDE_OFF' if props.show_plane else 'HIDE_ON')
        col3.prop(props, "plane_size")
        col3.prop(props, "plane_color")

        layout.separator()

        # --- Slice options ---
        layout.prop(props, "fill_cut")

        layout.separator()

        # --- Slice button ---
        can_slice = (obj is not None and obj.type == 'MESH' and context.mode == 'OBJECT')
        col4 = layout.column()
        col4.scale_y = 1.4
        col4.enabled = can_slice
        col4.operator("ps.slice_mesh", text="Slice Mesh", icon='MOD_BOOLEAN')


CLASSES = [PS_PT_PlaneSlicer]


def register():
    for cls in CLASSES:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)
