import bpy
from bpy.props import (
    FloatVectorProperty, FloatProperty, BoolProperty,
    PointerProperty, EnumProperty, IntProperty,
)
from bpy.types import PropertyGroup


def _redraw(self, context):
    for area in context.screen.areas:
        if area.type == 'VIEW_3D':
            area.tag_redraw()


class PegCutterProps(PropertyGroup):

    peg_shape: EnumProperty(
        name="Peg Shape",
        items=[
            ('CUBE',     "Cube",     "Rectangular box peg",     'MESH_CUBE',     0),
            ('CYLINDER', "Cylinder", "Cylindrical peg",         'MESH_CYLINDER', 1),
            ('OBJECT',   "Object",   "Use an existing mesh object", 'OBJECT_DATA', 2),
        ],
        default='CUBE',
        update=_redraw,
    )

    # Cube / shared dimensions — stored in Blender scene units
    peg_size_x: FloatProperty(
        name="Width (X)",
        description="Peg width along X. Scene units (mm if scene is set to mm)",
        default=5.0, min=0.001, update=_redraw,
    )
    peg_size_y: FloatProperty(
        name="Depth (Y)",
        description="Peg depth along Y",
        default=5.0, min=0.001, update=_redraw,
    )
    peg_size_z: FloatProperty(
        name="Height (Z)",
        description="Peg height along Z",
        default=10.0, min=0.001, update=_redraw,
    )

    # Cylinder only — peg_size_x reused as diameter, peg_size_z as height
    cyl_segments: IntProperty(
        name="Segments",
        description="Number of sides on the cylinder",
        default=32, min=3, max=256, update=_redraw,
    )

    # Existing object peg
    source_object: PointerProperty(
        name="Peg Object",
        description="Mesh object to use as the peg shape",
        type=bpy.types.Object,
        poll=lambda self, obj: obj.type == 'MESH',
        update=_redraw,
    )

    # Position / rotation (Cube and Cylinder only)
    peg_origin: FloatVectorProperty(
        name="Origin", size=3, subtype='XYZ',
        default=(0.0, 0.0, 0.0), update=_redraw,
    )
    peg_rotation: FloatVectorProperty(
        name="Rotation", size=3, subtype='EULER', unit='ROTATION',
        default=(0.0, 0.0, 0.0), update=_redraw,
    )

    # Clearance (per side, same scene units as dimensions)
    clearance_xy: FloatProperty(
        name="XY Clearance",
        description="Total amount added to the XY size of the cutter. "
                    "0.15 means the hole is 0.15 mm wider and deeper than the peg",
        default=0.15, min=0.0, max=100.0, update=_redraw,
    )
    use_z_clearance: BoolProperty(
        name="Separate Z Clearance",
        description="Use a different clearance value for the Z axis (top and bottom)",
        default=False, update=_redraw,
    )
    clearance_z: FloatProperty(
        name="Z Clearance",
        description="Gap added to top and bottom of the cutter (per side)",
        default=0.15, min=0.0, max=100.0, update=_redraw,
    )

    # Target objects to cut
    target_a: PointerProperty(
        name="Target A",
        description="First mesh to cut a peg hole into",
        type=bpy.types.Object,
        poll=lambda self, obj: obj.type == 'MESH',
    )
    target_b: PointerProperty(
        name="Target B",
        description="Second mesh to cut a peg hole into (optional)",
        type=bpy.types.Object,
        poll=lambda self, obj: obj.type == 'MESH',
    )

    # Preview display
    show_preview: BoolProperty(
        name="Show Preview", default=False, update=_redraw,
    )
    peg_color: FloatVectorProperty(
        name="Peg Color", subtype='COLOR_GAMMA', size=4,
        default=(0.2, 0.85, 0.3, 0.25), min=0.0, max=1.0, update=_redraw,
    )
    cutter_color: FloatVectorProperty(
        name="Cutter Outline", subtype='COLOR_GAMMA', size=4,
        default=(1.0, 0.35, 0.2, 0.9), min=0.0, max=1.0, update=_redraw,
    )


def register():
    bpy.utils.register_class(PegCutterProps)
    bpy.types.Scene.pc_props = PointerProperty(type=PegCutterProps)


def unregister():
    if hasattr(bpy.types.Scene, 'pc_props'):
        del bpy.types.Scene.pc_props
    bpy.utils.unregister_class(PegCutterProps)
