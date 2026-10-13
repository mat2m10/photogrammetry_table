# photogrammetry_table

Blender (bpy) scripts that generate a **synthetic photogrammetry benchmark**:
a wooden box with known dimensions, sitting on a turntable with ArUco markers,
rendered from a fixed camera at evenly spaced turntable angles. Because the
geometry is known exactly, the photos can be fed to a reconstruction tool
(COLMAP, Meshroom, ...) and the result compared against the ground truth.

## Requirements

- **Blender 4.2 LTS** (target version, not pinned in code).
  - Needs Blender >= 4.0: the materials use the Principled BSDF v2 input
    names (`Specular IOR Level`, `Sheen Weight`).
  - `render_turntable.py` uses the `BLENDER_EEVEE_NEXT` engine id, which only
    exists from 4.2 on (later releases renamed it back to `BLENDER_EEVEE`).
- No extra Python packages; everything runs in Blender's bundled Python.

## Usage

Run the three scripts in order from Blender's *Scripting* workspace
(open the file in the text editor, then *Run Script*). Work from a `.blend`
file saved **in this folder**: the scripts resolve `//subject.blend` and
`data/` relative to the current `.blend`.

| Step | Script | What it does |
|------|--------|--------------|
| 1 | `create_subject.py` | Clears the scene, builds the benchmark box and saves it as `subject.blend` next to the current `.blend`. Run it once. |
| 2 | `turntable.py` | In a *different* `.blend` (e.g. `turntable.blend`, saved in this folder): clears the scene, builds the turntable, black fabric, ArUco markers, lights and camera, and imports the box from `subject.blend` onto the turntable. Save the file afterwards. |
| 3 | `render_turntable.py` | With the turntable scene open: rotates the turntable in `NUM_PICTURES` (default 36) equal steps and renders one still per step. |

Settings (number of pictures, resolution, marker count and size, lights,
camera distance and elevation) are constants at the top of each script.

**Careful:** `create_subject.py` and `turntable.py` start by deleting every
object in the open scene.

## Output

`render_turntable.py` writes to `data/photogrammetry_pictures/` (next to the
`.blend`; `data/` is git-ignored):

```
data/photogrammetry_pictures/frame_000_angle_000.00deg.png
data/photogrammetry_pictures/frame_001_angle_010.00deg.png
...
```

1280 x 720 PNG by default. The camera is static (0.5 m from the centre,
30 degrees elevation) and the turntable rotates by `360 / NUM_PICTURES`
degrees between frames, so for reconstruction the camera effectively orbits
the object.

## Ground truth

Dimensions of the subject (`create_subject.py`, body base at Z = 0):

| Feature | Size |
|---------|------|
| Box body | 60 x 60 x 60 mm |
| Inset panels | 4 mm deep, 8 mm border, one per face (44 x 44 mm) |
| Lid panel | 42 x 42 mm, raised 2 mm above the top face |
| Reference disc (top centre) | 10 mm diameter, 0.5 mm thick |
| Bolt hole (top centre) | 5 mm diameter, through |
| Hinge barrels (back) | 2 x, 6 mm diameter x 10 mm |
| Latch plate (front) | 20 x 8 x 2 mm, pin 2 mm diameter |

The turntable disc is 200 mm in diameter (`TURNTABLE_RADIUS = 0.10`), and the
8 ArUco markers (`ARUCO_SIZE` = 18 mm, 4x4 bits) sit on an 80 mm radius
circle around the subject.

Use the 10 mm reference disc and the 60 mm box edges to check the metric
scale of a reconstruction.
