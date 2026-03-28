"""Add-on preferences and shared display utilities for Vertex Measure.

``VM_AddonPreferences`` stores all display settings (units, precision,
colours, font size).  ``format_distance`` and ``_draw_config`` are shared
between the preferences panel and the N-panel sub-panel so the layout is
defined in one place.
"""

import bpy
from bpy.props import IntProperty, FloatVectorProperty, EnumProperty
from bpy.types import AddonPreferences

UNIT_ITEMS: list[tuple[str, str, str]] = [
    ('m',  "Meters",       "Blender default unit"),
    ('cm', "Centimeters",  ""),
    ('mm', "Millimeters",  ""),
    ('in', "Inches",       ""),
    ('ft', "Feet",         ""),
]

_UNIT_SCALE: dict[str, tuple[float, str]] = {
    'm':  (1.0,       "m"),
    'cm': (100.0,     "cm"),
    'mm': (1000.0,    "mm"),
    'in': (39.3701,   '"'),
    'ft': (3.28084,   "'"),
}


def format_distance(distance_m: float, prefs: 'VM_AddonPreferences') -> str:
    """Convert a metre value to a display string using the current unit preference.

    Parameters
    ----------
    distance_m:
        Distance in metres (as stored in ``MeasurementItem.distance``).
    prefs:
        The active ``VM_AddonPreferences`` instance.

    Returns
    -------
    str
        Formatted string such as ``"15.0000 mm"``.
    """
    scale, suffix = _UNIT_SCALE[prefs.units]
    return f"{distance_m * scale:.{prefs.precision}f} {suffix}"


def get_prefs(context: bpy.types.Context) -> 'VM_AddonPreferences':
    """Return the active ``VM_AddonPreferences`` for the current add-on package.

    Parameters
    ----------
    context:
        Current Blender context.

    Returns
    -------
    VM_AddonPreferences
        The preferences object for this package.

    Raises
    ------
    KeyError
        If the add-on is not enabled or the package key is missing.
    """
    return context.preferences.addons[__package__].preferences


class VM_AddonPreferences(AddonPreferences):
    """Global display settings for the Vertex Measure add-on."""

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

    def draw(self, context: bpy.types.Context) -> None:
        """Render the preferences layout (mirrors the N-panel config section)."""
        _draw_config(self.layout, self)


def _draw_config(layout: bpy.types.UILayout, prefs: VM_AddonPreferences) -> None:
    """Draw the shared display-settings layout for preferences and N-panel.

    Parameters
    ----------
    layout:
        The ``UILayout`` to draw into.
    prefs:
        A ``VM_AddonPreferences`` instance (or any object with the same props).
    """
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


def register() -> None:
    """Register VM_AddonPreferences."""
    bpy.utils.register_class(VM_AddonPreferences)


def unregister() -> None:
    """Unregister VM_AddonPreferences."""
    bpy.utils.unregister_class(VM_AddonPreferences)
