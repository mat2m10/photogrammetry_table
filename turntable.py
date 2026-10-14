"""
turntable.py: build the turntable scene (fabric, turntable, ArUco markers,
lights, camera) and import the subject from subject.blend.

GUI : Run Script in a .blend saved next to subject.blend, then save the file.
CLI : blender -b --python-exit-code 1 -P turntable.py -- \
          --subject subject.blend --num-arucos 8 --aruco-bits 4 --save turntable.blend
"""
import argparse
import bpy
import math
import os
import sys

# ─── USER PARAMETERS ────────────────────────────────────────────────
TURNTABLE_RADIUS = 0.10
CAMERA_DISTANCE  = 0.5
CAMERA_ANGLE_DEG = 30
FRAME_START      = 1
FRAME_END        = 120
SUBJECT_BLEND    = "//subject.blend"

NUM_ARUCOS             = 8
ARUCO_SIZE             = 0.018   # black-border edge length (m)
ARUCO_BITS             = 4
ARUCO_PLACEMENT_RADIUS = 0.08

FABRIC_SIZE      = 0.60
FABRIC_COLOR     = (0.02, 0.02, 0.02, 1)
FABRIC_ROUGHNESS = 0.95

WOOD_BASE_COLOR  = (0.55, 0.30, 0.12, 1)
WOOD_DARK_COLOR  = (0.25, 0.12, 0.05, 1)
WOOD_ROUGHNESS   = 0.55

# ─── LIGHT PARAMETERS ───────────────────────────────────────────────
KEY_LIGHT = {
    "pos":      (-0.3, -0.4, 0.5),
    "energy":   80,
    "size":     0.4,
    "color":    (1.0, 0.92, 0.80),
    "type":     "AREA",
}
FILL_LIGHT = {
    "pos":      (0.4, 0.2, 0.3),
    "energy":   30,
    "size":     0.6,
    "color":    (0.80, 0.88, 1.0),
    "type":     "AREA",
}
RIM_LIGHT = {
    "pos":      (0.0, 0.4, 0.35),
    "energy":   60,
    "size":     0.15,
    "color":    (1.0, 1.0, 1.0),
    "type":     "SPOT",
    "spot_size_deg":  45,
    "spot_blend":     0.3,
}
EXTRA_LIGHT = {
    "enabled":  False,
    "pos":      (0.0, 0.0, 0.6),
    "energy":   40,
    "size":     0.5,
    "color":    (1.0, 1.0, 1.0),
    "type":     "AREA",
}
# ────────────────────────────────────────────────────────────────────

ARUCO_DICT = {4:"DICT_4X4_50", 5:"DICT_5X5_100", 6:"DICT_6X6_250", 7:"DICT_7X7_1000"}
# Real OpenCV ArUco dictionaries, first 50 markers of each, baked in so the
# script needs no OpenCV inside Blender. Each marker is an int whose bits are
# the inner bits×bits cells in row-major order, most significant bit = top-left
# cell, bit 1 = WHITE (OpenCV convention). The 1-cell border is always black.
# Regenerate with (opencv-python >= 4.7):
#   d = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
#   img = cv2.aruco.generateImageMarker(d, marker_id, bits + 2)  # 1 px per cell
#   code = int("".join("1" if v > 127 else "0" for v in img[1:-1, 1:-1].flat), 2)
ARUCO_CODES = {
    "DICT_4X4_50": [
        0xb532, 0x0f9a, 0x332d, 0x9946, 0x549e, 0x79cd, 0x9e2e, 0xc4f2, 0xfeda, 0xcf56,
        0xf991, 0x11a7, 0x0eb7, 0x2a0f, 0x24b1, 0x263e, 0x4665, 0x6600, 0x6c5e, 0x76af,
        0x868b, 0xb02b, 0xccd5, 0xdd82, 0xfe47, 0x9471, 0xace4, 0xa554, 0x2123, 0x346f,
        0x4415, 0x57b2, 0x9ecf, 0xf0cb, 0x08ae, 0x0929, 0x1875, 0x04ff, 0x0df6, 0x1c5a,
        0x1718, 0x2a28, 0x328c, 0x38b2, 0x24e8, 0x2eeb, 0x2d3f, 0x4b64, 0x502e, 0x5013,
    ],
    "DICT_5X5_100": [
        0x145b2bc, 0x01c06e6, 0x1af0edd, 0x10395f7, 0x1aeb524, 0x1d4082d, 0x0d3d7ec, 0x0e2146b,
        0x10d6132, 0x1313fa5, 0x13cee03, 0x1a2dac0, 0x1e62b11, 0x05e7166, 0x1fcfca8, 0x051e37f,
        0x097a758, 0x0bea26f, 0x0f64dc4, 0x1061de8, 0x12dda75, 0x150e440, 0x16b0ca1, 0x0ba12de,
        0x19cd023, 0x1a59972, 0x1c3ce8b, 0x0224246, 0x03b9672, 0x024223b, 0x027376e, 0x0368873,
        0x040d0ce, 0x04aaac8, 0x04643ba, 0x07a6fea, 0x0998aac, 0x082d101, 0x09aad1d, 0x0863c72,
        0x0ad2825, 0x0a52f9e, 0x0d849f7, 0x0c309d9, 0x0da7e31, 0x0e9627a, 0x0e9b997, 0x0f94806,
        0x0f59125, 0x0f6b7d7,
    ],
    "DICT_6X6_250": [
        0x1e3dd82a6, 0x0efba3891, 0x15907eacd, 0xc91b3069e, 0xd607d6e15, 0xd8e8e0e68,
        0x4268b41f5, 0x88a50f29a, 0x307d524fd, 0x3c2f34b3c, 0x45dfc74e3, 0x48d85b257,
        0x710558fc6, 0x86dcfad07, 0x8d72a93f6, 0xa2b89dcde, 0x09fd1e9c4, 0x154dbd18f,
        0x300a310e2, 0x4807efafd, 0x56df11db6, 0x66883274c, 0x76e8cb781, 0x9a53d9cf3,
        0xa9cb84024, 0xc67549490, 0xc1d288941, 0xe7480852b, 0xea2fca848, 0xe963b77b1,
        0xfa36652af, 0x065bff7bd, 0x0541d72d6, 0x0cf7246a2, 0x1338a39eb, 0x15a893e74,
        0x3a417ee9e, 0x4f11e26c0, 0x530db6d20, 0x589bfae34, 0x6409e8a0b, 0x60537a891,
        0x6159069ba, 0x6bff78d7b, 0x70ad96a4f, 0x75846f71a, 0x7a95192fc, 0x8609760aa,
        0x8a2d44c3f, 0x93eb78b14,
    ],
    "DICT_7X7_1000": [
        0x1bab8d94b9415, 0x1c837e27c8156, 0x13d545758ba4f, 0x14cce0b6fd298, 0x18d78f62664ac,
        0x0b1002846b3dc, 0x1a6d77cdea890, 0x07942db1117b6, 0x1120e3ead2d3c, 0x176cb631adc7e,
        0x1ea01a305e921, 0x0044ce170a834, 0x0a9e6d72e91e1, 0x13c49108c4733, 0x17bfe64d79397,
        0x19c220b60b52f, 0x1a7e0c2e43f16, 0x003c33d9d91db, 0x04d979854e0f1, 0x070fa9aec8226,
        0x0752095d3c3d3, 0x08da908f679ba, 0x091254fbd3c57, 0x0bced87c93150, 0x0e945bdf45f11,
        0x128bbc45026b2, 0x136252ac9db47, 0x143a9285b05f0, 0x176f1cc62d9a1, 0x1976bbb97b630,
        0x1a7cbdd6f0666, 0x1e528467fa339, 0x1fbada33e77cd, 0x0748c49dd09dd, 0x0c430fc48761e,
        0x0159a86df3b86, 0x01c81a9871c04, 0x0293fb340c448, 0x03345c234cbda, 0x056a104fc3668,
        0x052d271253f46, 0x059eea9b7e8ad, 0x06bd27f3c6cf8, 0x07ee957b07be7, 0x089a053e9fe80,
        0x09081c90855ea, 0x0be3226d06804, 0x0bd64e4807abb, 0x0df36483e2b84, 0x0e555f24151c7,
    ],
}


def aruco_bits(marker_id, bits):
    """Inner bit matrix (list of rows, 1 = white) of an OpenCV ArUco marker."""
    dict_name = ARUCO_DICT[bits]
    codes = ARUCO_CODES[dict_name]
    if not 0 <= marker_id < len(codes):
        raise ValueError(f"{dict_name}: only ids 0..{len(codes)-1} are baked in "
                         f"(asked for id {marker_id}); lower NUM_ARUCOS")
    code = codes[marker_id]
    n = bits * bits
    flat = [(code >> (n - 1 - k)) & 1 for k in range(n)]
    return [flat[r*bits:(r+1)*bits] for r in range(bits)]


ARUCO_QUIET_ZONE = 1   # white cells around the black border, helps detection


def aruco_grid(marker_id, bits, quiet=ARUCO_QUIET_ZONE):
    """
    Full marker as rows of 0 (black) / 1 (white), top row first:
    `quiet` white cells, a 1-cell black border, then the data bits.
    """
    inner = aruco_bits(marker_id, bits)
    size = bits + 2 + 2 * quiet
    grid = [[1] * size for _ in range(size)]                       # quiet zone
    for r in range(bits + 2):
        for c in range(bits + 2):
            grid[quiet + r][quiet + c] = 0                         # black border
    for r in range(bits):
        for c in range(bits):
            grid[quiet + 1 + r][quiet + 1 + c] = inner[r][c]
    return grid

# ─────────────────────────────────────────────────────────────────────

def clear_scene():
    """
    Delete every object and the data-blocks a previous run created, so
    re-running does not pile up WoodMat.001, ArUco_* images, lights, ...
    Note: this wipes ALL materials/images/etc. in the open .blend.
    """
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    for collection in (bpy.data.meshes, bpy.data.materials,
                       bpy.data.lights, bpy.data.cameras, bpy.data.actions):
        for block in list(collection):
            collection.remove(block)
    for img in list(bpy.data.images):
        if img.type not in {'RENDER_RESULT', 'COMPOSITING'}:   # keep Blender's own
            bpy.data.images.remove(img)

def make_wood_material():
    mat = bpy.data.materials.new("WoodMat")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    tex_coord = nodes.new("ShaderNodeTexCoord");    tex_coord.location = (-900, 0)
    mapping   = nodes.new("ShaderNodeMapping");     mapping.location   = (-700, 0)
    mapping.inputs["Scale"].default_value    = (8.0, 1.0, 1.0)
    mapping.inputs["Rotation"].default_value = (0.0, 0.0, math.radians(12))
    links.new(tex_coord.outputs["Object"], mapping.inputs["Vector"])

    noise = nodes.new("ShaderNodeTexNoise");  noise.location = (-480, 120)
    noise.inputs["Scale"].default_value      = 18.0
    noise.inputs["Detail"].default_value     = 8.0
    noise.inputs["Roughness"].default_value  = 0.65
    noise.inputs["Distortion"].default_value = 0.4
    links.new(mapping.outputs["Vector"], noise.inputs["Vector"])

    wave = nodes.new("ShaderNodeTexWave");   wave.location = (-480, -120)
    wave.wave_type = 'RINGS';  wave.bands_direction = 'X'
    wave.inputs["Scale"].default_value           = 6.0
    wave.inputs["Distortion"].default_value      = 3.5
    wave.inputs["Detail"].default_value          = 6.0
    wave.inputs["Detail Scale"].default_value    = 1.5
    wave.inputs["Detail Roughness"].default_value= 0.6
    links.new(mapping.outputs["Vector"], wave.inputs["Vector"])

    mix_vec = nodes.new("ShaderNodeMixRGB");  mix_vec.location = (-240, 0)
    mix_vec.blend_type = 'ADD'
    mix_vec.inputs["Fac"].default_value = 0.25
    links.new(noise.outputs["Color"], mix_vec.inputs["Color1"])
    links.new(wave.outputs["Color"],  mix_vec.inputs["Color2"])

    ramp = nodes.new("ShaderNodeValToRGB");   ramp.location = (-40, 0)
    ramp.color_ramp.interpolation = 'EASE'
    ramp.color_ramp.elements[0].position = 0.0
    ramp.color_ramp.elements[0].color    = WOOD_DARK_COLOR
    ramp.color_ramp.elements[1].position = 1.0
    ramp.color_ramp.elements[1].color    = WOOD_BASE_COLOR
    mid = ramp.color_ramp.elements.new(0.45)
    mid.color = (
        (WOOD_BASE_COLOR[0] + WOOD_DARK_COLOR[0]) * 0.6,
        (WOOD_BASE_COLOR[1] + WOOD_DARK_COLOR[1]) * 0.6,
        (WOOD_BASE_COLOR[2] + WOOD_DARK_COLOR[2]) * 0.6, 1.0)
    links.new(mix_vec.outputs["Color"], ramp.inputs["Fac"])

    bump = nodes.new("ShaderNodeBump");  bump.location = (-40, -260)
    bump.inputs["Strength"].default_value = 0.3
    bump.inputs["Distance"].default_value = 0.005
    links.new(noise.outputs["Fac"], bump.inputs["Height"])

    bsdf = nodes.new("ShaderNodeBsdfPrincipled");  bsdf.location = (220, 0)
    bsdf.inputs["Roughness"].default_value          = WOOD_ROUGHNESS
    bsdf.inputs["Specular IOR Level"].default_value = 0.3
    links.new(ramp.outputs["Color"],  bsdf.inputs["Base Color"])
    links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])

    out = nodes.new("ShaderNodeOutputMaterial");  out.location = (500, 0)
    links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return mat

def make_fabric_material():
    mat = bpy.data.materials.new("FabricMat")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    tex_coord = nodes.new("ShaderNodeTexCoord");  tex_coord.location = (-800, 0)
    mapping   = nodes.new("ShaderNodeMapping");   mapping.location   = (-600, 0)
    mapping.inputs["Scale"].default_value = (40.0, 40.0, 40.0)
    links.new(tex_coord.outputs["Object"], mapping.inputs["Vector"])

    noise = nodes.new("ShaderNodeTexNoise");  noise.location = (-380, -100)
    noise.inputs["Scale"].default_value      = 80.0
    noise.inputs["Detail"].default_value     = 12.0
    noise.inputs["Roughness"].default_value  = 0.8
    noise.inputs["Distortion"].default_value = 0.1
    links.new(mapping.outputs["Vector"], noise.inputs["Vector"])

    bump = nodes.new("ShaderNodeBump");  bump.location = (-160, -160)
    bump.inputs["Strength"].default_value = 0.6
    bump.inputs["Distance"].default_value = 0.002
    links.new(noise.outputs["Fac"], bump.inputs["Height"])

    bsdf = nodes.new("ShaderNodeBsdfPrincipled");  bsdf.location = (80, 0)
    r, g, b, a = FABRIC_COLOR
    bsdf.inputs["Base Color"].default_value      = (r, g, b, a)
    bsdf.inputs["Roughness"].default_value       = FABRIC_ROUGHNESS
    bsdf.inputs["Sheen Weight"].default_value    = 0.8
    bsdf.inputs["Sheen Roughness"].default_value = 0.5
    bsdf.inputs["Specular IOR Level"].default_value = 0.0
    links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])

    out = nodes.new("ShaderNodeOutputMaterial");  out.location = (360, 0)
    links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return mat

def create_turntable_pivot():
    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, 0))
    pivot = bpy.context.object
    pivot.name = "TurntablePivot"
    return pivot

def create_turntable(pivot):
    bpy.ops.mesh.primitive_cylinder_add(
        radius=TURNTABLE_RADIUS,
        depth=0.005,
        location=(0, 0, -0.0025)
    )
    disc = bpy.context.object
    disc.name = "Turntable"
    disc.data.materials.append(make_wood_material())
    disc.parent = pivot
    return disc

def create_fabric_surface():
    bpy.ops.mesh.primitive_plane_add(
        size=FABRIC_SIZE * 2,
        location=(0, 0, -0.005)
    )
    plane = bpy.context.object
    plane.name = "FabricSurface"
    plane.data.materials.append(make_fabric_material())
    return plane

def import_subject(blend_path, pivot):
    blend_path = bpy.path.abspath(blend_path)
    if not os.path.exists(blend_path):
        raise FileNotFoundError(f"Cannot find: {blend_path}")

    with bpy.data.libraries.load(blend_path, link=False) as (data_from, data_to):
        data_to.objects = data_from.objects

    imported = []
    for obj in data_to.objects:
        if obj is not None:
            bpy.context.collection.objects.link(obj)
            imported.append(obj)

    if not imported:
        raise RuntimeError("No objects found in subject.blend")

    bpy.ops.object.select_all(action='DESELECT')
    for obj in imported:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = imported[0]
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

    all_verts = []
    for obj in imported:
        if obj.type == 'MESH':
            for v in obj.data.vertices:
                all_verts.append(obj.matrix_world @ v.co)

    if all_verts:
        min_x = min(v.x for v in all_verts); max_x = max(v.x for v in all_verts)
        min_y = min(v.y for v in all_verts); max_y = max(v.y for v in all_verts)
        min_z = min(v.z for v in all_verts)
        cx = (min_x + max_x) / 2
        cy = (min_y + max_y) / 2
        for obj in imported:
            obj.location.x -= cx
            obj.location.y -= cy
            obj.location.z -= min_z

    for obj in imported:
        obj.parent = pivot

    return imported

def aruco_pixels(grid):
    """Flat RGBA list in Blender's pixel order (bottom row first)."""
    pixels = []
    for row in reversed(grid):
        for v in row:
            pixels += [float(v), float(v), float(v), 1.0]
    return pixels

def make_aruco_texture(marker_id, bits, dict_name):
    grid = aruco_grid(marker_id, bits)
    grid_size = len(grid)
    img = bpy.data.images.new(f"ArUco_{dict_name}_id{marker_id}",
                               width=grid_size, height=grid_size, alpha=False)
    pixels = aruco_pixels(grid)
    img.pixels = pixels
    img.pack()
    return img

def make_aruco_material(marker_id, bits, dict_name):
    mat = bpy.data.materials.new(f"ArUcoMat_id{marker_id}")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()
    tex  = nodes.new("ShaderNodeTexImage")
    tex.image = make_aruco_texture(marker_id, bits, dict_name)
    tex.interpolation = 'Closest'
    emit = nodes.new("ShaderNodeEmission")
    emit.inputs["Strength"].default_value = 1.0
    out  = nodes.new("ShaderNodeOutputMaterial")
    links.new(tex.outputs["Color"],     emit.inputs["Color"])
    links.new(emit.outputs["Emission"], out.inputs["Surface"])
    return mat

def place_arucos(num, size, bits, placement_radius, pivot):
    dict_name = ARUCO_DICT.get(bits)
    if not dict_name:
        raise ValueError(f"ARUCO_BITS must be 4-7, got {bits}")
    if num > len(ARUCO_CODES[dict_name]):
        raise ValueError(f"NUM_ARUCOS={num} but only {len(ARUCO_CODES[dict_name])} "
                         f"{dict_name} markers are baked in")
    # `size` is the black-border marker size (what a detector measures);
    # the plane is larger by the white quiet zone around it.
    plane_size = size * (bits + 2 + 2 * ARUCO_QUIET_ZONE) / (bits + 2)
    for i in range(num):
        angle = 2 * math.pi * i / num
        bpy.ops.mesh.primitive_plane_add(size=plane_size, location=(0, 0, 0.001))
        m = bpy.context.object
        m.name = f"ArUco_id{i}"
        m.location.x = placement_radius * math.cos(angle)
        m.location.y = placement_radius * math.sin(angle)
        m.location.z = 0.001
        m.rotation_euler.z = angle + math.pi / 2
        m.data.materials.append(make_aruco_material(i, bits, dict_name))
        m.parent = pivot

def create_camera():
    angle_rad = math.radians(CAMERA_ANGLE_DEG)
    bpy.ops.object.camera_add(
        location=(CAMERA_DISTANCE * math.cos(angle_rad),
                  0,
                  CAMERA_DISTANCE * math.sin(angle_rad))
    )
    cam = bpy.context.object
    cam.name = "TurntableCam"
    bpy.context.scene.camera = cam
    cam.rotation_euler = (-cam.location.normalized()).to_track_quat('-Z','Y').to_euler()
    return cam

def animate_turntable(pivot):
    scene = bpy.context.scene
    scene.frame_start = FRAME_START
    scene.frame_end   = FRAME_END
    scene.frame_set(FRAME_START)
    pivot.rotation_euler.z = 0.0
    pivot.keyframe_insert("rotation_euler", index=2)
    scene.frame_set(FRAME_END)
    pivot.rotation_euler.z = math.radians(360)
    pivot.keyframe_insert("rotation_euler", index=2)
    for fc in pivot.animation_data.action.fcurves:
        for kp in fc.keyframe_points:
            kp.interpolation = 'LINEAR'

def aim_at_origin(obj):
    import mathutils
    direction = mathutils.Vector((0, 0, 0)) - obj.location
    obj.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()

def add_light(cfg, name):
    ltype = cfg.get("type", "AREA")
    bpy.ops.object.light_add(type=ltype, location=cfg["pos"])
    light = bpy.context.object
    light.name = name
    light.data.energy = cfg["energy"]
    light.data.color  = cfg["color"]
    if ltype == "AREA":
        light.data.size = cfg["size"]
    elif ltype == "SPOT":
        light.data.spot_size  = math.radians(cfg.get("spot_size_deg", 45))
        light.data.spot_blend = cfg.get("spot_blend", 0.3)
        light.data.shadow_soft_size = cfg.get("size", 0.1)
    elif ltype == "SUN":
        light.data.angle = math.radians(cfg.get("angle_deg", 5))
    elif ltype == "POINT":
        light.data.shadow_soft_size = cfg.get("size", 0.1)
    aim_at_origin(light)
    return light

def add_lighting():
    add_light(KEY_LIGHT,  "KeyLight")
    add_light(FILL_LIGHT, "FillLight")
    add_light(RIM_LIGHT,  "RimLight")
    if EXTRA_LIGHT.get("enabled", True):
        add_light(EXTRA_LIGHT, "ExtraLight")

def script_argv(argv=None):
    """Arguments after `--` on the Blender command line (none in the GUI)."""
    if argv is not None:
        return argv
    return sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []


def parse_args(argv=None):
    p = argparse.ArgumentParser(
        prog="blender -b -P turntable.py --",
        description="Build the turntable scene around subject.blend.")
    p.add_argument("--subject", default=SUBJECT_BLEND,
                   help=f"subject .blend to import (default {SUBJECT_BLEND})")
    p.add_argument("--num-arucos", type=int, default=NUM_ARUCOS)
    p.add_argument("--aruco-bits", type=int, choices=sorted(ARUCO_DICT), default=ARUCO_BITS)
    p.add_argument("--save", default=None,
                   help="save the built scene to this .blend (needed when headless)")
    return p.parse_args(script_argv(argv))


# ── Entry point ───────────────────────────────────────────────────────

def build():
    clear_scene()

    pivot = create_turntable_pivot()

    create_fabric_surface()
    create_turntable(pivot)
    import_subject(SUBJECT_BLEND, pivot)
    place_arucos(NUM_ARUCOS, ARUCO_SIZE, ARUCO_BITS, ARUCO_PLACEMENT_RADIUS, pivot)

    create_camera()
    animate_turntable(pivot)
    add_lighting()

    bpy.context.scene.world.use_nodes = True
    bg = bpy.context.scene.world.node_tree.nodes["Background"]
    bg.inputs["Color"].default_value    = (0.02, 0.02, 0.02, 1)
    bg.inputs["Strength"].default_value = 0.3

    # Render settings (engine, resolution, file format) live in one place:
    # render_turntable.py sets them right before rendering.

    print("✓ Turntable built | subject rotating | camera static")

if __name__ == "__main__":
    args = parse_args()
    SUBJECT_BLEND = os.path.abspath(bpy.path.abspath(args.subject))
    NUM_ARUCOS, ARUCO_BITS = args.num_arucos, args.aruco_bits
    build()
    if args.save:
        out = os.path.abspath(bpy.path.abspath(args.save))
        bpy.ops.wm.save_as_mainfile(filepath=out)
        print(f"   Saved → {out}")
