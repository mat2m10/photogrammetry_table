"""
render_turntable.py: render NUM_PICTURES stills of the turntable scene.

GUI : open the saved turntable scene, then Run Script (uses the constants below).
CLI : blender -b turntable.blend --python-exit-code 1 -P render_turntable.py -- \
          --n 36 --out data/photogrammetry_pictures --format PNG --width 1280 --height 720
"""
import argparse
import bpy
import os
import math
import sys

# ─── USER PARAMETERS ────────────────────────────────────────────────
NUM_PICTURES     = 36
OUTPUT_SUBDIR    = "data/photogrammetry_pictures"
IMAGE_FORMAT     = "PNG"       # PNG / JPEG / OPEN_EXR
JPEG_QUALITY     = 95
RESOLUTION_X     = 1280
RESOLUTION_Y     = 720
# ────────────────────────────────────────────────────────────────────


def script_argv(argv=None):
    """Arguments after `--` on the Blender command line (none in the GUI)."""
    if argv is not None:
        return argv
    return sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []


def parse_args(argv=None):
    p = argparse.ArgumentParser(
        prog="blender -b <scene.blend> -P render_turntable.py --",
        description="Render the turntable at evenly spaced angles.")
    p.add_argument("--n", type=int, default=NUM_PICTURES,
                   help=f"number of pictures (default {NUM_PICTURES})")
    p.add_argument("--out", default=None,
                   help=f"output directory (default: <blend dir>/{OUTPUT_SUBDIR})")
    p.add_argument("--format", choices=["PNG", "JPEG", "OPEN_EXR"], default=IMAGE_FORMAT)
    p.add_argument("--width", type=int, default=RESOLUTION_X)
    p.add_argument("--height", type=int, default=RESOLUTION_Y)
    args = p.parse_args(script_argv(argv))
    if args.n < 1:
        p.error("--n must be >= 1")
    return args


def setup_output_dir(blend_path, out=None):
    if out:
        output_dir = os.path.abspath(out)
    else:
        if not blend_path:
            raise RuntimeError("The .blend is not saved: save it or pass --out")
        blend_dir  = os.path.dirname(os.path.abspath(blend_path))
        output_dir = os.path.join(blend_dir, OUTPUT_SUBDIR)
    os.makedirs(output_dir, exist_ok=True)
    return output_dir


def setup_render():
    scene = bpy.context.scene
    scene.render.engine                = 'BLENDER_EEVEE_NEXT'
    scene.render.resolution_x          = RESOLUTION_X
    scene.render.resolution_y          = RESOLUTION_Y
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = IMAGE_FORMAT
    if IMAGE_FORMAT == "JPEG":
        scene.render.image_settings.quality = JPEG_QUALITY
    scene.render.film_transparent = False
    eevee = scene.eevee
    eevee.use_shadows   = True
    eevee.use_gtao      = True
    eevee.gtao_distance = 0.05
    print(f"   Engine : EEVEE Next  {RESOLUTION_X}x{RESOLUTION_Y}")


def get_pivot():
    pivot = bpy.data.objects.get("TurntablePivot")
    if pivot is None:
        raise RuntimeError("TurntablePivot not found — run turntable_loader.py first.")
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

            print(f"   [{i+1:>3}/{NUM_PICTURES}]  {angle_deg:6.1f}  ->  {filename}")

    finally:
        # Always restore even if rendering crashes halfway
        pivot.rotation_euler.z = original_angle
        restore_animation(pivot, saved_action)
        force_update()

    print(f"\n  Done -- {NUM_PICTURES} images saved to:\n   {output_dir}\n")


# ── Main ──────────────────────────────────────────────────────────────
def main(argv=None):
    global NUM_PICTURES, IMAGE_FORMAT, RESOLUTION_X, RESOLUTION_Y
    args = parse_args(argv)
    NUM_PICTURES, IMAGE_FORMAT = args.n, args.format
    RESOLUTION_X, RESOLUTION_Y = args.width, args.height
    output_dir = setup_output_dir(bpy.data.filepath, args.out)
    setup_render()
    render_turntable(output_dir)


if __name__ == "__main__":
    main()
