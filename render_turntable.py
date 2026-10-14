import bpy
import json
import os
import math

# ─── USER PARAMETERS ────────────────────────────────────────────────
# This is the ONLY place render settings are defined; create_subject.py
# and turntable.py build geometry and leave the render settings alone.
NUM_PICTURES     = 36
OUTPUT_SUBDIR    = "data/photogrammetry_pictures"
IMAGE_FORMAT     = "PNG"       # PNG / JPEG / OPEN_EXR
JPEG_QUALITY     = 95
RESOLUTION_X     = 1280
RESOLUTION_Y     = 720
# ────────────────────────────────────────────────────────────────────


def setup_output_dir(blend_path):
    blend_dir  = os.path.dirname(os.path.abspath(blend_path))
    output_dir = os.path.join(blend_dir, OUTPUT_SUBDIR)
    os.makedirs(output_dir, exist_ok=True)
    return output_dir


# Written for Blender 4.2 LTS. The materials need >= 4.0 (Principled BSDF v2
# input names), and the EEVEE engine id changed between releases:
#   < 4.2 : 'BLENDER_EEVEE'       (legacy EEVEE)
#   4.2+  : 'BLENDER_EEVEE_NEXT'
#   5.0+  : 'BLENDER_EEVEE' again (EEVEE Next renamed back)
MIN_BLENDER_VERSION = (4, 0, 0)
EEVEE_ENGINE_IDS    = ('BLENDER_EEVEE_NEXT', 'BLENDER_EEVEE')


def check_blender_version():
    if bpy.app.version < MIN_BLENDER_VERSION:
        raise RuntimeError(
            f"Blender {bpy.app.version_string} is too old: these scripts need "
            f"{'.'.join(map(str, MIN_BLENDER_VERSION))} or newer (target: 4.2 LTS).")


def set_eevee_engine(scene):
    """Select whichever EEVEE engine id this Blender version knows."""
    for engine_id in EEVEE_ENGINE_IDS:
        try:
            scene.render.engine = engine_id
            return engine_id
        except TypeError:   # unknown enum value in this Blender version
            continue
    raise RuntimeError(f"No EEVEE engine found (tried {EEVEE_ENGINE_IDS}) "
                       f"in Blender {bpy.app.version_string}")


def setup_render():
    scene = bpy.context.scene
    engine_id = set_eevee_engine(scene)
    scene.render.resolution_x          = RESOLUTION_X
    scene.render.resolution_y          = RESOLUTION_Y
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = IMAGE_FORMAT
    if IMAGE_FORMAT == "JPEG":
        scene.render.image_settings.quality = JPEG_QUALITY
    scene.render.film_transparent = False
    # These EEVEE options were renamed or removed across 4.x / 5.x releases;
    # set them only where they exist.
    eevee = scene.eevee
    for attr, value in (("use_shadows", True),
                        ("use_gtao", True),
                        ("gtao_distance", 0.05)):
        if hasattr(eevee, attr):
            setattr(eevee, attr, value)
        else:
            print(f"   (skipping scene.eevee.{attr}: not in this Blender version)")
    print(f"   Blender {bpy.app.version_string}  Engine : {engine_id}  "
          f"{RESOLUTION_X}x{RESOLUTION_Y}")


# ─── Camera ground truth ────────────────────────────────────────────
# The camera is static and the turntable (pivot) rotates, so in the frame of
# the subject (= the pivot's local frame, which equals world at angle 0) the
# camera orbits. For each frame we store that camera pose, OpenCV/COLMAP
# convention: x right, y down, z forward; world-to-camera X_cam = R X + t,
# metres. Pixel coordinates follow COLMAP: (0, 0) is the top-left CORNER of
# the image (subtract 0.5 from cx, cy for OpenCV's pixel-centre convention).

BLENDER_TO_CV = [[1, 0, 0], [0, -1, 0], [0, 0, -1]]   # flip camera y and z


def matmul(a, b):
    return [[sum(a[i][k] * b[k][j] for k in range(len(b)))
             for j in range(len(b[0]))] for i in range(len(a))]


def transpose(a):
    return [list(r) for r in zip(*a)]


def to_rows(m):
    """mathutils.Matrix (or nested sequence) -> list of lists."""
    return [[float(m[i][j]) for j in range(len(m[0]))] for i in range(len(m))]


def split_rigid(m, tol=1e-4):
    """4x4 rows -> (3x3 rotation, translation); refuse scaled matrices."""
    r = [row[:3] for row in m[:3]]
    t = [m[0][3], m[1][3], m[2][3]]
    rtr = matmul(transpose(r), r)
    for i in range(3):
        for j in range(3):
            if abs(rtr[i][j] - (1.0 if i == j else 0.0)) > tol:
                raise ValueError("matrix has scale/shear; apply scale on the "
                                 "camera and TurntablePivot objects")
    return r, t


def world_to_camera_cv(pivot_world, cam_world):
    """
    pivot_world, cam_world: 4x4 matrix_world rows.
    Returns (R, t) mapping subject-frame points to OpenCV camera coordinates.
    """
    rp, tp = split_rigid(pivot_world)
    rc, tc = split_rigid(cam_world)
    # camera-to-subject: inv(P) @ C
    rpt = transpose(rp)
    r_c2s = matmul(rpt, rc)
    t_c2s = [sum(rpt[i][k] * (tc[k] - tp[k]) for k in range(3)) for i in range(3)]
    r_c2s_cv = matmul(r_c2s, BLENDER_TO_CV)
    r = transpose(r_c2s_cv)
    t = [-sum(r[i][k] * t_c2s[k] for k in range(3)) for i in range(3)]
    return r, t


def rotmat_to_quat(r):
    """3x3 rotation -> (qw, qx, qy, qz), qw >= 0 (COLMAP order)."""
    tr = r[0][0] + r[1][1] + r[2][2]
    if tr > 0:
        s = math.sqrt(tr + 1.0) * 2
        q = (0.25 * s, (r[2][1] - r[1][2]) / s, (r[0][2] - r[2][0]) / s, (r[1][0] - r[0][1]) / s)
    elif r[0][0] > r[1][1] and r[0][0] > r[2][2]:
        s = math.sqrt(1.0 + r[0][0] - r[1][1] - r[2][2]) * 2
        q = ((r[2][1] - r[1][2]) / s, 0.25 * s, (r[0][1] + r[1][0]) / s, (r[0][2] + r[2][0]) / s)
    elif r[1][1] > r[2][2]:
        s = math.sqrt(1.0 + r[1][1] - r[0][0] - r[2][2]) * 2
        q = ((r[0][2] - r[2][0]) / s, (r[0][1] + r[1][0]) / s, 0.25 * s, (r[1][2] + r[2][1]) / s)
    else:
        s = math.sqrt(1.0 + r[2][2] - r[0][0] - r[1][1]) * 2
        q = ((r[1][0] - r[0][1]) / s, (r[0][2] + r[2][0]) / s, (r[1][2] + r[2][1]) / s, 0.25 * s)
    n = math.sqrt(sum(c * c for c in q))
    q = tuple(c / n for c in q)
    return q if q[0] >= 0 else tuple(-c for c in q)


def camera_intrinsics(lens_mm, sensor_width, sensor_height, sensor_fit,
                      res_x, res_y, res_percent=100,
                      pixel_aspect_x=1.0, pixel_aspect_y=1.0,
                      shift_x=0.0, shift_y=0.0):
    """Blender perspective camera -> (width, height, fx, fy, cx, cy) in pixels."""
    scale = res_percent / 100.0
    w, h = res_x * scale, res_y * scale
    sensor = sensor_height if sensor_fit == 'VERTICAL' else sensor_width
    if sensor_fit == 'AUTO':
        sensor_fit = 'HORIZONTAL' if pixel_aspect_x * w >= pixel_aspect_y * h else 'VERTICAL'
    par = pixel_aspect_y / pixel_aspect_x
    view_fac = w if sensor_fit == 'HORIZONTAL' else par * h
    fx = lens_mm / sensor * view_fac
    fy = fx / par
    cx = w / 2 - shift_x * view_fac
    cy = h / 2 + shift_y * view_fac / par
    return int(round(w)), int(round(h)), fx, fy, cx, cy


def scene_intrinsics(scene, cam_obj):
    cam = cam_obj.data
    if cam.type != 'PERSP':
        raise ValueError(f"only perspective cameras are supported, got {cam.type}")
    r = scene.render
    return camera_intrinsics(cam.lens, cam.sensor_width, cam.sensor_height,
                             cam.sensor_fit, r.resolution_x, r.resolution_y,
                             r.resolution_percentage, r.pixel_aspect_x,
                             r.pixel_aspect_y, cam.shift_x, cam.shift_y)


def write_ground_truth(output_dir, intrinsics, frames):
    """
    frames: list of dicts {name, angle_deg, R, t}.
    Writes cameras.json and a COLMAP text model in <output_dir>/colmap/.
    """
    w, h, fx, fy, cx, cy = intrinsics
    data = {
        "convention": "OpenCV/COLMAP camera (x right, y down, z forward); "
                      "world-to-camera X_cam = R @ X + t; world = subject/turntable "
                      "frame (Z up, origin at turntable centre); metres; "
                      "pixel (0,0) = top-left corner of the image",
        "camera": {"model": "PINHOLE", "width": w, "height": h,
                   "fx": fx, "fy": fy, "cx": cx, "cy": cy},
        "frames": [{"image": f["name"], "angle_deg": f["angle_deg"],
                    "R": f["R"], "t": f["t"],
                    "qvec_wxyz": list(rotmat_to_quat(f["R"]))} for f in frames],
    }
    with open(os.path.join(output_dir, "cameras.json"), "w") as fh:
        json.dump(data, fh, indent=2)

    colmap_dir = os.path.join(output_dir, "colmap")
    os.makedirs(colmap_dir, exist_ok=True)
    with open(os.path.join(colmap_dir, "cameras.txt"), "w") as fh:
        fh.write("# CAMERA_ID, MODEL, WIDTH, HEIGHT, PARAMS[]\n")
        fh.write(f"1 PINHOLE {w} {h} {fx!r} {fy!r} {cx!r} {cy!r}\n")
    with open(os.path.join(colmap_dir, "images.txt"), "w") as fh:
        fh.write("# IMAGE_ID, QW, QX, QY, QZ, TX, TY, TZ, CAMERA_ID, NAME\n")
        fh.write("# POINTS2D[] as (X, Y, POINT3D_ID) (empty: known poses only)\n")
        for i, f in enumerate(frames, start=1):
            q = rotmat_to_quat(f["R"])
            vals = " ".join(repr(v) for v in (*q, *f["t"]))
            fh.write(f"{i} {vals} 1 {f['name']}\n\n")
    with open(os.path.join(colmap_dir, "points3D.txt"), "w") as fh:
        fh.write("# POINT3D_ID, X, Y, Z, R, G, B, ERROR, TRACK[]\n")


def get_pivot():
    pivot = bpy.data.objects.get("TurntablePivot")
    if pivot is None:
        raise RuntimeError("TurntablePivot not found — run turntable.py first (and open the saved turntable scene).")
    return pivot


def strip_animation(pivot):
    """
    Remove all keyframes from the pivot so that setting
    pivot.rotation_euler.z is not overwritten by the animation system.
    The action is saved and restored after rendering.
    """
    if pivot.animation_data and pivot.animation_data.action:
        action = pivot.animation_data.action
        pivot.animation_data.action = None   # unlink — does NOT delete
        return action
    return None


def restore_animation(pivot, action):
    """Re-link the saved action after rendering is done."""
    if action is not None:
        if pivot.animation_data is None:
            pivot.animation_data_create()
        pivot.animation_data.action = action


def force_update():
    for obj in bpy.context.scene.objects:
        obj.update_tag()
    bpy.context.view_layer.update()


def render_turntable(output_dir):
    pivot  = get_pivot()
    scene  = bpy.context.scene

    ext = "png" if IMAGE_FORMAT == "PNG" else \
          "jpg" if IMAGE_FORMAT == "JPEG" else "exr"

    print(f"\n-- Rendering {NUM_PICTURES} pictures ------------------")
    print(f"   Output : {output_dir}")
    print(f"   Format : {IMAGE_FORMAT}  {RESOLUTION_X}x{RESOLUTION_Y}\n")

    # ── Detach keyframes so they can't fight our manual rotation ──────
    saved_action   = strip_animation(pivot)
    original_angle = pivot.rotation_euler.z

    cam = scene.camera
    if cam is None:
        raise RuntimeError("Scene has no active camera — run turntable.py first.")
    intrinsics = scene_intrinsics(scene, cam)
    frames = []

    try:
        for i in range(NUM_PICTURES):
            angle_deg = 360.0 * i / NUM_PICTURES
            angle_rad = math.radians(angle_deg)

            pivot.rotation_euler.z = angle_rad
            force_update()

            filename = f"frame_{i:03d}_angle_{angle_deg:06.2f}deg.{ext}"
            filepath = os.path.join(output_dir, filename)
            scene.render.filepath = filepath

            bpy.ops.render.render(write_still=True)

            r, t = world_to_camera_cv(to_rows(pivot.matrix_world),
                                      to_rows(cam.matrix_world))
            frames.append({"name": filename, "angle_deg": angle_deg, "R": r, "t": t})

            print(f"   [{i+1:>3}/{NUM_PICTURES}]  {angle_deg:6.1f}  ->  {filename}")

    finally:
        # Always restore even if rendering crashes halfway
        pivot.rotation_euler.z = original_angle
        restore_animation(pivot, saved_action)
        force_update()

    write_ground_truth(output_dir, intrinsics, frames)
    print(f"\n  Done -- {NUM_PICTURES} images saved to:\n   {output_dir}")
    print(f"   Camera ground truth: cameras.json + colmap/{{cameras,images,points3D}}.txt\n")


# ── Main ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    check_blender_version()
    output_dir = setup_output_dir(bpy.data.filepath)
    setup_render()
    render_turntable(output_dir)
