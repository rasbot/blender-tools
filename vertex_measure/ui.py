"""N-panel UI for the Vertex Measure addon (Measure tab).

Two panels:
* ``VM_PT_Main``   — measurement list with add/remove controls
* ``VM_PT_Config`` — collapsible display settings (sub-panel of Main)
"""

import bpy
from bpy.types import Panel

from .preferences import get_prefs, format_distance, _draw_config


class VM_PT_Main(Panel):
    """Main Vertex Measure panel listing all measurements across all scene objects."""

    bl_label = "Vertex Measure"
    bl_idname = "VM_PT_Main"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Measure"

    def draw(self, context: bpy.types.Context) -> None:
        """Draw the Add Measurement button and per-object measurement lists."""
        layout = self.layout

        # Add Measurement button — only active in Edit Mode with 2 verts selected
        col = layout.column()
        col.scale_y = 1.3
        row = col.row()

        obj = context.active_object
        in_edit_with_two = False
        if obj and obj.type == 'MESH' and context.mode == 'EDIT_MESH':
            import bmesh
            bm = bmesh.from_edit_mesh(obj.data)
            selected_count = sum(1 for v in bm.verts if v.select)
            in_edit_with_two = (selected_count == 2)

        row.enabled = in_edit_with_two
        row.operator("vm.add_measurement", text="Add Measurement", icon='PLUS')

        if not in_edit_with_two and context.mode != 'EDIT_MESH':
            col.label(text="Enter Edit Mode and select 2 vertices", icon='INFO')
        elif not in_edit_with_two and context.mode == 'EDIT_MESH':
            col.label(text="Select exactly 2 vertices", icon='INFO')

        layout.separator()

        # List all objects that have measurements
        try:
            prefs = get_prefs(context)
        except (KeyError, AttributeError):
            prefs = None

        any_measurements = False
        for scene_obj in context.scene.objects:
            if not hasattr(scene_obj, 'vm_measurements'):
                continue
            if not scene_obj.vm_measurements:
                continue

            any_measurements = True
            box = layout.box()
            box.label(text=scene_obj.name, icon='MESH_DATA')

            for i, meas in enumerate(scene_obj.vm_measurements):
                meas_col = box.column(align=True)

                # Row 1: name and distance
                row = meas_col.row(align=True)
                row.label(text=meas.name)
                dist_text = (
                    format_distance(meas.distance, prefs)
                    if prefs else f"{meas.distance:.4f} m"
                )
                row.label(text=dist_text)

                # Row 2: component toggle + delete
                row2 = meas_col.row(align=True)
                icon = 'TRIA_DOWN' if meas.show_components else 'TRIA_RIGHT'
                row2.prop(meas, "show_components", text="Components", icon=icon, toggle=True)

                op = row2.operator("vm.remove_measurement", text="", icon='X')
                op.obj_name = scene_obj.name
                op.index = i

                # Row 3 (conditional): individual X/Y/Z toggles
                if meas.show_components:
                    sub = meas_col.row(align=True)
                    sub.prop(meas, "show_x", text="X", toggle=True)
                    sub.prop(meas, "show_y", text="Y", toggle=True)
                    sub.prop(meas, "show_z", text="Z", toggle=True)

                meas_col.separator(factor=0.3)

        if not any_measurements:
            layout.label(text="No measurements yet", icon='INFO')


class VM_PT_Config(Panel):
    """Collapsible sub-panel for Vertex Measure display settings."""

    bl_label = "Display Settings"
    bl_idname = "VM_PT_Config"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Measure"
    bl_parent_id = "VM_PT_Main"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context: bpy.types.Context) -> None:
        """Render the shared display-settings layout from preferences."""
        try:
            prefs = get_prefs(context)
        except (KeyError, AttributeError):
            self.layout.label(text="Preferences unavailable", icon='ERROR')
            return
        _draw_config(self.layout, prefs)


CLASSES = [VM_PT_Main, VM_PT_Config]


def register() -> None:
    """Register all Vertex Measure panels."""
    for cls in CLASSES:
        bpy.utils.register_class(cls)


def unregister() -> None:
    """Unregister all Vertex Measure panels."""
    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)
