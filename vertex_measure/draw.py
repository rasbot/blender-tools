"""Viewport draw callbacks for Vertex Measure overlays.

Two handlers are registered:
* ``draw_lines``  (``POST_VIEW``)  — 3-D line segments between vertex pairs
* ``draw_labels`` (``POST_PIXEL``) — 2-D text labels at measurement midpoints

Both callbacks iterate over every scene object that has ``vm_measurements``
data so measurements from all objects are visible simultaneously.
"""

import bpy
import blf
import gpu
from gpu_extras.batch import batch_for_shader
from mathutils import Vector
from bpy_extras.view3d_utils import location_3d_to_region_2d

from .preferences import get_prefs, format_distance

_handles: list[object] = []


def _get_region_and_rv3d(
    context: bpy.types.Context,
) -> tuple[bpy.types.Region | None, bpy.types.RegionView3D | None]:
    """Find the first VIEW_3D WINDOW region and its ``RegionView3D``.

    Parameters
    ----------
    context:
        Current Blender context.

    Returns
    -------
    tuple[Region | None, RegionView3D | None]
        ``(region, rv3d)`` pair, or ``(None, None)`` if no VIEW_3D is found.
    """
    for area in context.screen.areas:
        if area.type == 'VIEW_3D':
            for region in area.regions:
                if region.type == 'WINDOW':
                    return region, area.spaces.active.region_3d
    return None, None


def draw_lines() -> None:
    """Draw measurement line segments for all objects in the scene (POST_VIEW).

    Reads ``vm_measurements`` from every scene object each frame.  Returns
    immediately if no measurements exist or the add-on preferences are
    unavailable.
    """
    context = bpy.context
    if not context or not context.scene:
        return

    try:
        prefs = get_prefs(context)
    except (KeyError, AttributeError):
        return

    coords: list[Vector] = []
    for obj in context.scene.objects:
        if not hasattr(obj, 'vm_measurements') or not obj.vm_measurements:
            continue
        for meas in obj.vm_measurements:
            v1 = obj.matrix_world @ Vector(meas.v1_co)
            v2 = obj.matrix_world @ Vector(meas.v2_co)
            coords.extend([v1, v2])

    if not coords:
        return

    region = None
    for area in context.screen.areas:
        if area.type == 'VIEW_3D':
            for r in area.regions:
                if r.type == 'WINDOW':
                    region = r
                    break

    shader = gpu.shader.from_builtin('POLYLINE_UNIFORM_COLOR')
    batch = batch_for_shader(shader, 'LINES', {"pos": coords})

    gpu.state.depth_test_set('NONE')
    gpu.state.blend_set('ALPHA')

    shader.bind()
    shader.uniform_float("color", prefs.line_color)
    shader.uniform_float("lineWidth", 2.0)
    if region:
        shader.uniform_float("viewportSize", (region.width, region.height))
    batch.draw(shader)

    gpu.state.depth_test_set('LESS_EQUAL')
    gpu.state.blend_set('NONE')


def draw_labels() -> None:
    """Draw measurement text labels at midpoints for all objects (POST_PIXEL).

    Projects each measurement midpoint from 3-D world space to 2-D screen
    space and renders the distance string (plus optional component breakdown)
    using ``blf``.  Returns immediately if the viewport region is unavailable.
    """
    context = bpy.context
    if not context or not context.scene:
        return

    try:
        prefs = get_prefs(context)
    except (KeyError, AttributeError):
        return

    region, rv3d = _get_region_and_rv3d(context)
    if region is None or rv3d is None:
        return

    font_id = 0
    blf.size(font_id, prefs.font_size)
    line_height = prefs.font_size + 4
    offset_px = prefs.label_offset

    for obj in context.scene.objects:
        if not hasattr(obj, 'vm_measurements') or not obj.vm_measurements:
            continue
        for meas in obj.vm_measurements:
            v1_world = obj.matrix_world @ Vector(meas.v1_co)
            v2_world = obj.matrix_world @ Vector(meas.v2_co)
            mid = (v1_world + v2_world) / 2.0

            screen_pos = location_3d_to_region_2d(region, rv3d, mid)
            if screen_pos is None:
                continue

            x = screen_pos.x + offset_px
            y = screen_pos.y + offset_px

            # Main distance label (computed live from current world coords)
            scale = context.scene.unit_settings.scale_length
            dist = (v2_world - v1_world).length * scale
            blf.color(font_id, *prefs.text_color)
            blf.position(font_id, x, y, 0)
            blf.draw(font_id, f"{meas.name}: {format_distance(dist, prefs)}")

            if not meas.show_components:
                continue

            row = 1
            if meas.show_x:
                dx = abs(v2_world.x - v1_world.x) * scale
                blf.color(font_id, *prefs.color_x)
                blf.position(font_id, x, y - line_height * row, 0)
                blf.draw(font_id, f"  X: {format_distance(dx, prefs)}")
                row += 1

            if meas.show_y:
                dy = abs(v2_world.y - v1_world.y) * scale
                blf.color(font_id, *prefs.color_y)
                blf.position(font_id, x, y - line_height * row, 0)
                blf.draw(font_id, f"  Y: {format_distance(dy, prefs)}")
                row += 1

            if meas.show_z:
                dz = abs(v2_world.z - v1_world.z) * scale
                blf.color(font_id, *prefs.color_z)
                blf.position(font_id, x, y - line_height * row, 0)
                blf.draw(font_id, f"  Z: {format_distance(dz, prefs)}")


def register() -> None:
    """Add the line and label draw handlers to SpaceView3D."""
    _handles.append(
        bpy.types.SpaceView3D.draw_handler_add(draw_lines, (), 'WINDOW', 'POST_VIEW')
    )
    _handles.append(
        bpy.types.SpaceView3D.draw_handler_add(draw_labels, (), 'WINDOW', 'POST_PIXEL')
    )


def unregister() -> None:
    """Remove all draw handlers from SpaceView3D."""
    for h in _handles:
        bpy.types.SpaceView3D.draw_handler_remove(h, 'WINDOW')
    _handles.clear()
