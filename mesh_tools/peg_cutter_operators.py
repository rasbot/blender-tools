import math
import bpy
from mathutils import Vector, Euler, Matrix
from .peg_cutter_draw import _bbox_half_extents


# ── Mesh creation helpers ─────────────────────────────────────────────────────

def _make_box_mesh(sx, sy, sz):
    """Create and return a bpy.types.Mesh for a box of full dimensions sx × sy × sz."""
    import bmesh as _bm
    bm = _bm.new()
    hx, hy, hz = sx / 2, sy / 2, sz / 2
    verts = [
        bm.verts.new((-hx, -hy, -hz)), bm.verts.new(( hx, -hy, -hz)),
        bm.verts.new(( hx,  hy, -hz)), bm.verts.new((-hx,  hy, -hz)),
        bm.verts.new((-hx, -hy,  hz)), bm.verts.new(( hx, -hy,  hz)),
        bm.verts.new(( hx,  hy,  hz)), bm.verts.new((-hx,  hy,  hz)),
    ]
    for fi in [(0,3,2,1),(4,5,6,7),(0,1,5,4),(3,7,6,2),(0,4,7,3),(1,2,6,5)]:
        bm.faces.new([verts[i] for i in fi])
    mesh = bpy.data.meshes.new("_pc_tmp_mesh")
    bm.to_mesh(mesh)
    bm.free()
    return mesh


def _make_cylinder_mesh(radius, height, segments):
    """Create and return a bpy.types.Mesh for a closed cylinder."""
    import bmesh as _bm
    bm = _bm.new()
    hh = height / 2.0
    bot = [bm.verts.new((math.cos(2*math.pi*i/segments)*radius,
                          math.sin(2*math.pi*i/segments)*radius, -hh))
           for i in range(segments)]
    top = [bm.verts.new((math.cos(2*math.pi*i/segments)*radius,
                          math.sin(2*math.pi*i/segments)*radius,  hh))
           for i in range(segments)]
    bm.faces.new(list(reversed(bot)))   # bottom cap (normal down)
    bm.faces.new(top)                   # top cap (normal up)
    for i in range(segments):
        j = (i + 1) % segments
        bm.faces.new([bot[i], bot[j], top[j], top[i]])
    mesh = bpy.data.meshes.new("_pc_tmp_mesh")
    bm.to_mesh(mesh)
    bm.free()
    return mesh


def _world_matrix(origin, rot_mat):
    return Matrix.Translation(origin) @ rot_mat.to_4x4()


# ── Cutter and peg object builders ────────────────────────────────────────────

def _build_cutter(props, context):
    """
    Create a temporary cutter object (peg + clearance).
    Caller must link it to the scene collection and remove it after use.
    """
    shape = props.peg_shape
    c_xy  = props.clearance_xy
    c_z   = props.clearance_z if props.use_z_clearance else props.clearance_xy

    if shape == 'OBJECT':
        src = props.source_object
        if src is None:
            return None
        hx, hy, hz, local_ctr = _bbox_half_extents(src)
        origin  = src.matrix_world @ local_ctr
        rot_mat = src.matrix_world.to_3x3().normalized()
        mesh = _make_box_mesh(hx * 2 + c_xy, hy * 2 + c_xy, hz * 2 + c_z)

    elif shape == 'CYLINDER':
        origin  = Vector(props.peg_origin)
        rot_mat = Euler(tuple(props.peg_rotation), 'XYZ').to_matrix()
        radius  = props.peg_size_x / 2.0 + c_xy / 2.0
        height  = props.peg_size_z + c_z
        mesh    = _make_cylinder_mesh(radius, height, props.cyl_segments)

    else:  # CUBE
        origin  = Vector(props.peg_origin)
        rot_mat = Euler(tuple(props.peg_rotation), 'XYZ').to_matrix()
        mesh = _make_box_mesh(
            props.peg_size_x + c_xy,
            props.peg_size_y + c_xy,
            props.peg_size_z + c_z,
        )

    obj = bpy.data.objects.new("_pc_cutter_tmp", mesh)
    obj.matrix_world  = _world_matrix(origin, rot_mat)
    obj.hide_render   = True
    obj.display_type  = 'WIRE'
    return obj


def _build_peg(props, context):
    """
    Create and link the visual peg object (Cube/Cylinder only).
    Returns the new object.
    """
    shape   = props.peg_shape
    origin  = Vector(props.peg_origin)
    rot_mat = Euler(tuple(props.peg_rotation), 'XYZ').to_matrix()

    if shape == 'CYLINDER':
        radius = props.peg_size_x / 2.0
        mesh   = _make_cylinder_mesh(radius, props.peg_size_z, props.cyl_segments)
        name   = "Peg_Cylinder"
    else:
        mesh = _make_box_mesh(props.peg_size_x, props.peg_size_y, props.peg_size_z)
        name = "Peg_Cube"

    peg = bpy.data.objects.new(name, mesh)
    context.scene.collection.objects.link(peg)
    peg.matrix_world = _world_matrix(origin, rot_mat)
    return peg


# ── Boolean helper ────────────────────────────────────────────────────────────

def _boolean_difference(target, cutter, context):
    """Apply a boolean DIFFERENCE of cutter from target (destructive)."""
    mod = target.modifiers.new(name="_pc_bool_tmp", type='BOOLEAN')
    mod.operation = 'DIFFERENCE'
    mod.solver    = 'FLOAT'
    mod.object    = cutter
    with context.temp_override(object=target, active_object=target,
                               selected_objects=[target]):
        bpy.ops.object.modifier_apply(modifier=mod.name)


# ── Operators ─────────────────────────────────────────────────────────────────

class PC_OT_CutPeg(bpy.types.Operator):
    bl_idname  = "pc.cut_peg"
    bl_label   = "Cut Peg Holes"
    bl_description = (
        "Boolean-cut peg-shaped holes into the target objects. "
        "The cutter is the peg shape plus clearance. "
        "For Cube/Cylinder shapes the peg itself is kept as a new object"
    )
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        props = context.scene.pc_props
        has_target = props.target_a is not None
        has_peg = (
            props.peg_shape in {'CUBE', 'CYLINDER'}
            or (props.peg_shape == 'OBJECT' and props.source_object is not None)
        )
        return has_target and has_peg and context.mode == 'OBJECT'

    def execute(self, context):
        props   = context.scene.pc_props
        targets = [t for t in (props.target_a, props.target_b) if t is not None]

        # Validate: no shape keys, no self-cutting
        for t in targets:
            if t.data.shape_keys:
                self.report({'ERROR'}, f"'{t.name}' has shape keys — remove them before cutting")
                return {'CANCELLED'}

        if props.peg_shape == 'OBJECT' and props.source_object in targets:
            self.report({'ERROR'}, "Source peg object cannot also be a cut target")
            return {'CANCELLED'}

        # Build cutter, link to scene so boolean modifier can reference it
        cutter = _build_cutter(props, context)
        if cutter is None:
            self.report({'ERROR'}, "Could not build cutter — check source object is set")
            return {'CANCELLED'}
        context.scene.collection.objects.link(cutter)

        # Build and keep the visual peg (cube/cylinder only)
        peg_obj = None
        if props.peg_shape in {'CUBE', 'CYLINDER'}:
            peg_obj = _build_peg(props, context)

        # Apply boolean to each target
        for t in targets:
            _boolean_difference(t, cutter, context)

        # Clean up temp cutter
        cutter_mesh = cutter.data
        bpy.data.objects.remove(cutter, do_unlink=True)
        bpy.data.meshes.remove(cutter_mesh)

        target_names = " and ".join(f"'{t.name}'" for t in targets)
        peg_note = f" Peg object kept as '{peg_obj.name}'." if peg_obj else ""
        self.report({'INFO'}, f"Cut peg holes into {target_names}.{peg_note}")
        return {'FINISHED'}


class PC_OT_CenterPeg(bpy.types.Operator):
    bl_idname  = "pc.center_peg"
    bl_label   = "Center on Active"
    bl_description = (
        "Set the peg origin to the active object's bounding box center "
        "and match peg dimensions to the bounding box"
    )
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj is not None and obj.type == 'MESH'

    def execute(self, context):
        obj = context.active_object
        world_corners = [obj.matrix_world @ Vector(c) for c in obj.bound_box]
        center = sum(world_corners, Vector()) / 8.0
        xs = [c.x for c in world_corners]
        ys = [c.y for c in world_corners]
        zs = [c.z for c in world_corners]

        props = context.scene.pc_props
        props.peg_origin  = center
        props.peg_size_x  = max(xs) - min(xs)
        props.peg_size_y  = max(ys) - min(ys)
        props.peg_size_z  = max(zs) - min(zs)
        return {'FINISHED'}


class PC_OT_PlaceAtCursor(bpy.types.Operator):
    bl_idname = "pc.place_at_cursor"
    bl_label = "Place at Cursor"
    bl_description = "Move the peg origin to the 3D cursor"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        context.scene.pc_props.peg_origin = context.scene.cursor.location
        return {'FINISHED'}


CLASSES = [PC_OT_CutPeg, PC_OT_CenterPeg, PC_OT_PlaceAtCursor]


def register():
    for cls in CLASSES:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)
