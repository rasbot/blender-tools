# Blender Tools

A collection of Blender addons for mesh measurement, alignment, slicing, and 3D printing assembly. Requires Blender 4.0+.

## Addons

### Vertex Measure

Persistent vertex-pair distance measurement tool. Measurements are stored per-object and survive file save/load.

**Location:** View3D > Sidebar > Measure

#### Usage

1. Enter Edit Mode on a mesh object
2. Select exactly 2 vertices
3. Click **Add Measurement** in the Measure panel
4. A line and distance label appear in the viewport

Measurements update with object transforms and persist across sessions.

#### Features

- Measurement lines and labels drawn as viewport overlays
- Optional X/Y/Z component breakdown per measurement
- Configurable units: Meters, Centimeters, Millimeters, Inches, Feet
- Configurable display: font size, label offset, decimal precision (0-6)
- Customizable colors for lines, text, and X/Y/Z components

---

### Mesh Tools

Three mesh manipulation tools in a single addon.

**Location:** View3D > Sidebar > Mesh Tools

#### Plane Align

Face-to-face object alignment via interactive face picking.

1. Click **Pick Source Face** and click a face on the object to move
2. Click **Pick Target Face** and click a face on the reference object
3. Click **Align Planes** — the source object rotates and translates so the two faces are flush

#### Plane Slicer

Interactive slice-plane preview and mesh bisection.

1. Select a mesh object
2. Position the cutting plane using the origin/rotation fields, axis snap buttons (XY, XZ, YZ), **Align to View**, **Center on Active**, or **Place at Cursor**
3. Toggle the plane preview to visualize the cut
4. Click **Slice Mesh** — creates two objects with `_A` and `_B` suffixes

Options: fill cut edges, plane size, plane color.

#### Peg Cutter

Boolean-cut registration peg holes for 3D printing assemblies.

1. Choose a peg shape: **Cube**, **Cylinder**, or an existing **Object** mesh
2. Set dimensions and position (or inherit from source object)
3. Set **clearance** — how much larger the hole is than the peg (default 0.15 mm)
4. Pick one or two target meshes to cut into
5. Toggle the preview to visualize the peg (green) and cutter outline (orange)
6. Click **Cut Peg Holes** — applies boolean difference cuts and keeps the peg as a new object

## License

MIT License - Copyright (c) 2026 Nathan Rasmussen. See [LICENSE](LICENSE) for details.

## Installation

Install each addon folder (`vertex_measure`, `mesh_tools`) via Edit > Preferences > Add-ons > Install from Disk, or copy them into your Blender addons directory.
