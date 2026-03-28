import bpy
from bpy.props import IntProperty, FloatVectorProperty, EnumProperty
from bpy.types import AddonPreferences

UNIT_ITEMS = [
    ('m',  "Meters",       "Blender default unit"),
    ('cm', "Centimeters",  ""),
    ('mm', "Millimeters",  ""),
    ('in', "Inches",       ""),
    ('ft', "Feet",         ""),
]

_UNIT_SCALE = {
    'm':  (1.0,       "m"),
    'cm': (100.0,     "cm"),
    'mm': (1000.0,    "mm"),
    'in': (39.3701,   '"'),
    'ft': (3.28084,   "'"),
}


def format_distance(distance_m, prefs):
    scale, suffix = _UNIT_SCALE[prefs.units]
    return f"{distance_m * scale:.{prefs.precision}f} {suffix}"


def get_prefs(context):
    return context.preferences.addons[__package__].preferences


class VM_AddonPreferences(AddonPreferences):
    bl_idname = __package__

    precision: IntProperty(
        name="Precision",
        description="Decimal places shown for distances",
        default=4, min=0, max=6,
    )
    units: EnumProperty(
        name="Units",
        description="Unit system for displaying distances",
        items=UNIT_ITEMS,
        default='mm',
    )
    font_size: IntProperty(
        name="Font Size",
        description="Size of viewport measurement labels (points)",
        default=20, min=8, max=48,
    )
    label_offset: IntProperty(
        name="Label Offset",
        description="Distance in pixels the text label floats from the measurement midpoint",
        default=6, min=0, max=100,
        subtype='PIXEL',
    )
    line_color: FloatVectorProperty(
        name="Line Color",
        subtype='COLOR_GAMMA', size=4,
        default=(1.0, 0.8, 0.0, 1.0), min=0.0, max=1.0,
    )
    text_color: FloatVectorProperty(
        name="Text Color",
        subtype='COLOR_GAMMA', size=4,
        default=(1.0, 1.0, 1.0, 1.0), min=0.0, max=1.0,
    )
    color_x: FloatVectorProperty(
        name="X Component Color",
        subtype='COLOR_GAMMA', size=4,
        default=(1.0, 0.3, 0.3, 1.0), min=0.0, max=1.0,
    )
    color_y: FloatVectorProperty(
        name="Y Component Color",
        subtype='COLOR_GAMMA', size=4,
        default=(0.3, 1.0, 0.3, 1.0), min=0.0, max=1.0,
    )
    color_z: FloatVectorProperty(
        name="Z Component Color",
        subtype='COLOR_GAMMA', size=4,
        default=(0.4, 0.6, 1.0, 1.0), min=0.0, max=1.0,
    )

    def draw(self, context):
        # Shown in Edit > Preferences > Add-ons (mirrors the N-panel config section)
        _draw_config(self.layout, self)


def _draw_config(layout, prefs):
    """Shared layout drawing used by both AddonPreferences and the N-panel sub-panel."""
    col = layout.column(align=True)
    col.prop(prefs, "precision")
    col.prop(prefs, "units")
    col.prop(prefs, "font_size")
    col.prop(prefs, "label_offset")

    layout.separator()
    layout.label(text="Colors:")
    col2 = layout.column(align=True)
    col2.prop(prefs, "line_color")
    col2.prop(prefs, "text_color")

    layout.separator()
    layout.label(text="Component Colors:")
    col3 = layout.column(align=True)
    col3.prop(prefs, "color_x")
    col3.prop(prefs, "color_y")
    col3.prop(prefs, "color_z")


def register():
    bpy.utils.register_class(VM_AddonPreferences)


def unregister():
    bpy.utils.unregister_class(VM_AddonPreferences)
