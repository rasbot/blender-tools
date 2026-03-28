"""N-panel UI for the Peg Cutter tool (Mesh Tools tab)."""

import bpy
from bpy.types import Panel


class PC_PT_PegCutter(Panel):
    """Sidebar panel for configuring and executing the Peg Cutter."""

    bl_label       = "Peg Cutter"
    bl_idname      = "PC_PT_PegCutter"
    bl_space_type  = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category    = "Mesh Tools"
    bl_options     = {'DEFAULT_CLOSED'}

    def draw(self, context: bpy.types.Context) -> None:
        """Draw shape selector, dimensions, position, clearance, targets, and cut button."""
        layout = self.layout
        props  = context.scene.pc_props
        shape  = props.peg_shape

        # ── Peg Shape selector ────────────────────────────────────────────────
        layout.prop(props, "peg_shape", expand=True)
        layout.separator()

        # ── Shape-specific dimensions ─────────────────────────────────────────
        box = layout.box()
        if shape == 'OBJECT':
            box.label(text="Peg Source Object", icon='OBJECT_DATA')
            box.prop(props, "source_object", text="")
            if props.source_object is None:
                box.label(text="Pick a mesh object above", icon='ERROR')
            else:
                box.label(
                    text=f"Using '{props.source_object.name}' bounding box",
                    icon='CHECKMARK',
                )

        elif shape == 'CYLINDER':
            box.label(text="Cylinder Dimensions", icon='MESH_CYLINDER')
            col = box.column(align=True)
            col.prop(props, "peg_size_x", text="Diameter")
            col.prop(props, "peg_size_z", text="Height")
            col.prop(props, "cyl_segments", text="Segments")

        else:  # CUBE
            box.label(text="Box Dimensions", icon='MESH_CUBE')
            col = box.column(align=True)
            col.prop(props, "peg_size_x", text="Width  (X)")
            col.prop(props, "peg_size_y", text="Depth  (Y)")
            col.prop(props, "peg_size_z", text="Height (Z)")

        layout.separator()

        # ── Position & Rotation (greyed out for OBJECT mode) ──────────────────
        pos_box = layout.box()
        pos_box.enabled = (shape != 'OBJECT')
        pos_box.label(
            text="Position & Rotation"
            if shape != 'OBJECT'
            else "Position & Rotation  (using source object's transform)",
            icon='OBJECT_ORIGIN',
        )
        col2 = pos_box.column(align=True)
        col2.label(text="Origin:")
        col2.prop(props, "peg_origin", text="")
        row = col2.row(align=True)
        row.operator("pc.place_at_cursor", text="Place at Cursor", icon='CURSOR')
        row.operator("pc.center_peg", text="Center on Active", icon='OBJECT_ORIGIN')
        col3 = pos_box.column(align=True)
        col3.label(text="Rotation:")
        col3.prop(props, "peg_rotation", text="")

        layout.separator()

        # ── Clearance ─────────────────────────────────────────────────────────
        clr_box = layout.box()
        clr_box.label(text="Clearance (total size increase, scene units)", icon='FULLSCREEN_ENTER')
        clr_box.prop(props, "clearance_xy", text="XY")
        row = clr_box.row(align=True)
        row.prop(props, "use_z_clearance", text="Separate Z")
        sub = row.row()
        sub.enabled = props.use_z_clearance
        sub.prop(props, "clearance_z", text="Z")

        layout.separator()

        # ── Targets ───────────────────────────────────────────────────────────
        tgt_box = layout.box()
        tgt_box.label(text="Cut Into", icon='MOD_BOOLEAN')
        tgt_box.prop(props, "target_a", text="Target A")
        tgt_box.prop(props, "target_b", text="Target B  (optional)")

        layout.separator()

        # ── Preview ───────────────────────────────────────────────────────────
        prev_box = layout.box()
        prev_box.label(text="Preview", icon='HIDE_OFF')
        prev_box.prop(
            props, "show_preview", toggle=True,
            icon='HIDE_OFF' if props.show_preview else 'HIDE_ON',
        )
        if props.show_preview:
            col4 = prev_box.column(align=True)
            col4.prop(props, "peg_color",    text="Peg Fill")
            col4.prop(props, "cutter_color", text="Cutter Outline")

        layout.separator()

        # ── Cut button ────────────────────────────────────────────────────────
        can_cut = (
            props.target_a is not None
            and (shape in {'CUBE', 'CYLINDER'} or props.source_object is not None)
            and context.mode == 'OBJECT'
        )
        col5 = layout.column()
        col5.scale_y = 1.4
        col5.enabled = can_cut
        col5.operator("pc.cut_peg", text="Cut Peg Holes", icon='MOD_BOOLEAN')


CLASSES = [PC_PT_PegCutter]


def register() -> None:
    """Register the Peg Cutter panel."""
    for cls in CLASSES:
        bpy.utils.register_class(cls)


def unregister() -> None:
    """Unregister the Peg Cutter panel."""
    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)
