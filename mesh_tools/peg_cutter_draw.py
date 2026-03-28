import math
import bpy
import gpu
from gpu_extras.batch import batch_for_shader
from mathutils import Vector, Euler

_handles = []


# ── Geometry helpers ──────────────────────────────────────────────────────────

def _box_tris(origin, rot_mat, hx, hy, hz):
    """Fill triangles for a box with half-extents hx/hy/hz at origin."""
    corners_local = [
        Vector((-hx, -hy, -hz)), Vector(( hx, -hy, -hz)),
        Vector(( hx,  hy, -hz)), Vector((-hx,  hy, -hz)),
        Vector((-hx, -hy,  hz)), Vector(( hx, -hy,  hz)),
        Vector(( hx,  hy,  hz)), Vector((-hx,  hy,  hz)),
    ]
    w = [origin + rot_mat @ c for c in corners_local]
    # 6 faces as quad → 2 tris
    quads = [
        (w[0], w[3], w[2], w[1]),  # bottom
        (w[4], w[5], w[6], w[7]),  # top
        (w[0], w[1], w[5], w[4]),  # front
        (w[2], w[3], w[7], w[6]),  # back
        (w[0], w[4], w[7], w[3]),  # left
        (w[1], w[2], w[6], w[5]),  # right
    ]
    tris = []
    for a, b, c, d in quads:
        tris += [a, b, c,  a, c, d]
    return tris


def _box_lines(origin, rot_mat, hx, hy, hz):
    """Wire edges for a box with half-extents hx/hy/hz."""
    corners_local = [
        Vector((-hx, -hy, -hz)), Vector(( hx, -hy, -hz)),
        Vector(( hx,  hy, -hz)), Vector((-hx,  hy, -hz)),
        Vector((-hx, -hy,  hz)), Vector(( hx, -hy,  hz)),
        Vector(( hx,  hy,  hz)), Vector((-hx,  hy,  hz)),
    ]
    w = [origin + rot_mat @ c for c in corners_local]
    pairs = [
        (w[0],w[1]),(w[1],w[2]),(w[2],w[3]),(w[3],w[0]),
        (w[4],w[5]),(w[5],w[6]),(w[6],w[7]),(w[7],w[4]),
        (w[0],w[4]),(w[1],w[5]),(w[2],w[6]),(w[3],w[7]),
    ]
    return [v for pair in pairs for v in pair]


def _cylinder_tris(origin, rot_mat, radius, hh, segments):
    """Fill triangles for a cylinder with given radius and half-height hh."""
    angles = [2 * math.pi * i / segments for i in range(segments)]
    bot = [Vector((math.cos(a) * radius, math.sin(a) * radius, -hh)) for a in angles]
    top = [Vector((math.cos(a) * radius, math.sin(a) * radius,  hh)) for a in angles]
    bot_c = Vector((0.0, 0.0, -hh))
    top_c = Vector((0.0, 0.0,  hh))

    def w(v):
        return origin + rot_mat @ v

    tris = []
    for i in range(segments):
        j = (i + 1) % segments
        tris += [w(bot_c), w(bot[j]), w(bot[i])]            # bottom cap
        tris += [w(top_c), w(top[i]), w(top[j])]            # top cap
        tris += [w(bot[i]), w(bot[j]), w(top[j]),
                 w(bot[i]), w(top[j]), w(top[i])]            # body quad
    return tris


def _cylinder_lines(origin, rot_mat, radius, hh, segments):
    """Wire circles + verticals for a cylinder."""
    angles = [2 * math.pi * i / segments for i in range(segments)]
    bot = [origin + rot_mat @ Vector((math.cos(a)*radius, math.sin(a)*radius, -hh)) for a in angles]
    top = [origin + rot_mat @ Vector((math.cos(a)*radius, math.sin(a)*radius,  hh)) for a in angles]
    lines = []
    for i in range(segments):
        j = (i + 1) % segments
        lines += [bot[i], bot[j], top[i], top[j]]
    # Vertical lines (one every ~45°)
    step = max(1, segments // 8)
    for i in range(0, segments, step):
        lines += [bot[i], top[i]]
    return lines


def _bbox_half_extents(obj):
    """Return (hx, hy, hz, local_centre) from obj.bound_box (local space)."""
    corners = [Vector(c) for c in obj.bound_box]
    xs = [c.x for c in corners]; ys = [c.y for c in corners]; zs = [c.z for c in corners]
    hx = (max(xs) - min(xs)) / 2.0
    hy = (max(ys) - min(ys)) / 2.0
    hz = (max(zs) - min(zs)) / 2.0
    lc = Vector(((max(xs)+min(xs))/2, (max(ys)+min(ys))/2, (max(zs)+min(zs))/2))
    return hx, hy, hz, lc


# ── Draw callback ─────────────────────────────────────────────────────────────

def draw_peg_preview():
    context = bpy.context
    if not context or not context.scene:
        return
    try:
        props = context.scene.pc_props
    except AttributeError:
        return
    if not props.show_preview:
        return

    shape = props.peg_shape
    c_xy = props.clearance_xy
    c_z  = props.clearance_z if props.use_z_clearance else props.clearance_xy

    # ── Resolve peg parameters ────────────────────────────────────────────────
    if shape == 'OBJECT':
        src = props.source_object
        if src is None:
            return
        hx, hy, hz, local_ctr = _bbox_half_extents(src)
        rot_mat = src.matrix_world.to_3x3().normalized()
        origin  = src.matrix_world @ local_ctr
        # Cutter is a box slightly larger than the bounding box
        peg_tris  = _box_tris( origin, rot_mat, hx,              hy,              hz)
        cut_lines = _box_lines(origin, rot_mat, hx + c_xy / 2.0, hy + c_xy / 2.0, hz + c_z / 2.0)

    elif shape == 'CYLINDER':
        origin  = Vector(props.peg_origin)
        rot_mat = Euler(tuple(props.peg_rotation), 'XYZ').to_matrix()
        radius  = props.peg_size_x / 2.0   # peg_size_x = diameter
        hh      = props.peg_size_z / 2.0
        segs    = props.cyl_segments
        peg_tris  = _cylinder_tris( origin, rot_mat, radius,              hh,              segs)
        cut_lines = _cylinder_lines(origin, rot_mat, radius + c_xy / 2.0, hh + c_z / 2.0, segs)

    else:  # CUBE
        origin  = Vector(props.peg_origin)
        rot_mat = Euler(tuple(props.peg_rotation), 'XYZ').to_matrix()
        hx = props.peg_size_x / 2.0
        hy = props.peg_size_y / 2.0
        hz = props.peg_size_z / 2.0
        peg_tris  = _box_tris( origin, rot_mat, hx,              hy,              hz)
        cut_lines = _box_lines(origin, rot_mat, hx + c_xy / 2.0, hy + c_xy / 2.0, hz + c_z / 2.0)

    # ── Find viewport window region (required for POLYLINE shader) ────────────
    region = None
    for area in context.screen.areas:
        if area.type == 'VIEW_3D':
            for r in area.regions:
                if r.type == 'WINDOW':
                    region = r
                    break

    peg_col = tuple(props.peg_color)
    cut_col = tuple(props.cutter_color)

    gpu.state.blend_set('ALPHA')
    gpu.state.depth_test_set('NONE')
    gpu.state.face_culling_set('NONE')

    # Peg — semi-transparent fill
    shader_fill = gpu.shader.from_builtin('UNIFORM_COLOR')
    batch_fill  = batch_for_shader(shader_fill, 'TRIS', {"pos": peg_tris})
    shader_fill.bind()
    shader_fill.uniform_float("color", peg_col)
    batch_fill.draw(shader_fill)

    # Cutter — wireframe outline
    shader_line = gpu.shader.from_builtin('POLYLINE_UNIFORM_COLOR')
    batch_cut   = batch_for_shader(shader_line, 'LINES', {"pos": cut_lines})
    shader_line.bind()
    shader_line.uniform_float("color", cut_col)
    shader_line.uniform_float("lineWidth", 1.5)
    if region:
        shader_line.uniform_float("viewportSize", (region.width, region.height))
    batch_cut.draw(shader_line)

    gpu.state.depth_test_set('LESS_EQUAL')
    gpu.state.blend_set('NONE')
    gpu.state.face_culling_set('NONE')


def register():
    _handles.append(
        bpy.types.SpaceView3D.draw_handler_add(
            draw_peg_preview, (), 'WINDOW', 'POST_VIEW'
        )
    )


def unregister():
    for h in _handles:
        bpy.types.SpaceView3D.draw_handler_remove(h, 'WINDOW')
    _handles.clear()
