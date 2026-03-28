import bpy
import gpu
from gpu_extras.batch import batch_for_shader
from mathutils import Vector, Euler

_handles = []


def draw_slicer_plane():
    context = bpy.context
    if not context or not context.scene:
        return

    try:
        props = context.scene.ps_props
    except AttributeError:
        return

    if not props.show_plane:
        return

    rot_mat = Euler(tuple(props.plane_rotation), 'XYZ').to_matrix()
    origin  = Vector(props.plane_origin)
    half    = props.plane_size / 2.0

    corners = [
        origin + rot_mat @ Vector((-half, -half, 0.0)),
        origin + rot_mat @ Vector(( half, -half, 0.0)),
        origin + rot_mat @ Vector(( half,  half, 0.0)),
        origin + rot_mat @ Vector((-half,  half, 0.0)),
    ]

    fill_color = tuple(props.plane_color)
    # Edge is more opaque than fill
    edge_alpha = min(fill_color[3] * 4.0, 1.0)
    edge_color = (fill_color[0], fill_color[1], fill_color[2], edge_alpha)

    # Find the WINDOW region for POLYLINE viewport size
    region = None
    for area in context.screen.areas:
        if area.type == 'VIEW_3D':
            for r in area.regions:
                if r.type == 'WINDOW':
                    region = r
                    break

    gpu.state.blend_set('ALPHA')
    gpu.state.depth_test_set('NONE')
    gpu.state.face_culling_set('NONE')

    # --- Filled face (two triangles) ---
    shader_fill = gpu.shader.from_builtin('UNIFORM_COLOR')
    tris = [corners[0], corners[1], corners[2],
            corners[0], corners[2], corners[3]]
    batch_fill = batch_for_shader(shader_fill, 'TRIS', {"pos": tris})
    shader_fill.bind()
    shader_fill.uniform_float("color", fill_color)
    batch_fill.draw(shader_fill)

    # --- Border (line loop) ---
    shader_line = gpu.shader.from_builtin('POLYLINE_UNIFORM_COLOR')
    border_verts = corners + [corners[0]]   # close the loop
    batch_border = batch_for_shader(shader_line, 'LINE_STRIP', {"pos": border_verts})
    shader_line.bind()
    shader_line.uniform_float("color", edge_color)
    shader_line.uniform_float("lineWidth", 2.0)
    if region:
        shader_line.uniform_float("viewportSize", (region.width, region.height))
    batch_border.draw(shader_line)

    # --- Normal arrow (short line from center along local Z) ---
    normal = (rot_mat @ Vector((0.0, 0.0, 1.0))).normalized()
    arrow_tip = origin + normal * (half * 0.35)
    batch_arrow = batch_for_shader(shader_line, 'LINES', {"pos": [origin, arrow_tip]})
    shader_line.bind()
    shader_line.uniform_float("color", (1.0, 1.0, 0.3, 0.9))
    shader_line.uniform_float("lineWidth", 2.0)
    if region:
        shader_line.uniform_float("viewportSize", (region.width, region.height))
    batch_arrow.draw(shader_line)

    gpu.state.depth_test_set('LESS_EQUAL')
    gpu.state.blend_set('NONE')
    gpu.state.face_culling_set('NONE')


def register():
    _handles.append(
        bpy.types.SpaceView3D.draw_handler_add(
            draw_slicer_plane, (), 'WINDOW', 'POST_VIEW'
        )
    )


def unregister():
    for h in _handles:
        bpy.types.SpaceView3D.draw_handler_remove(h, 'WINDOW')
    _handles.clear()
