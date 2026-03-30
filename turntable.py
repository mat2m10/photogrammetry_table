import bpy
import math
import os

# ─── USER PARAMETERS ────────────────────────────────────────────────
TURNTABLE_RADIUS = 0.10
CAMERA_DISTANCE  = 0.5
CAMERA_ANGLE_DEG = 30
FRAME_START      = 1
FRAME_END        = 120
SUBJECT_BLEND    = "//subject.blend"

NUM_ARUCOS             = 8
ARUCO_SIZE             = 0.018
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
ARUCO_PATTERNS = {
    "DICT_4X4_50": [
        [[1,0,0,0],[0,1,1,1],[0,1,1,1],[0,1,1,1]],
        [[1,0,0,0],[0,1,1,1],[0,1,1,0],[0,1,0,1]],
        [[1,0,0,1],[0,1,1,0],[1,0,0,1],[0,1,1,0]],
        [[1,0,0,1],[0,1,0,1],[1,0,1,0],[0,1,0,1]],
        [[1,0,1,0],[1,0,1,0],[0,1,0,1],[1,0,1,0]],
        [[1,0,1,0],[1,0,0,1],[0,1,1,0],[1,0,0,1]],
        [[1,0,1,1],[1,0,0,0],[0,1,1,1],[1,0,0,0]],
        [[1,0,1,1],[1,0,1,0],[0,1,0,1],[1,0,1,0]],
    ],
    "DICT_5X5_100": [
        [[1,0,0,0,0],[0,1,1,1,1],[0,1,1,1,1],[0,1,1,1,1],[0,1,1,1,1]],
        [[1,0,0,0,1],[0,1,1,1,0],[1,0,0,0,1],[0,1,1,1,0],[1,0,0,0,1]],
        [[1,0,0,1,0],[1,0,0,1,0],[0,1,1,0,1],[1,0,0,1,0],[0,1,1,0,1]],
        [[1,0,0,1,1],[1,0,0,0,0],[0,1,1,1,1],[1,0,0,0,0],[0,1,1,1,1]],
        [[1,0,1,0,0],[0,1,0,1,1],[1,0,1,0,0],[0,1,0,1,1],[1,0,1,0,0]],
        [[1,0,1,0,1],[0,1,0,1,0],[1,0,1,0,1],[0,1,0,1,0],[1,0,1,0,1]],
        [[1,0,1,1,0],[0,1,0,0,1],[1,0,1,1,0],[0,1,0,0,1],[1,0,1,1,0]],
        [[1,0,1,1,1],[0,1,0,0,0],[1,0,1,1,1],[0,1,0,0,0],[1,0,1,1,1]],
    ],
    "DICT_6X6_250": [
        [[1,0,0,0,0,0],[0,1,1,1,1,1],[0,1,1,1,1,1],[0,1,1,1,1,1],[0,1,1,1,1,1],[0,1,1,1,1,1]],
        [[1,0,0,0,0,1],[0,1,1,1,1,0],[1,0,0,0,0,1],[0,1,1,1,1,0],[1,0,0,0,0,1],[0,1,1,1,1,0]],
        [[1,0,0,0,1,0],[1,0,0,0,1,0],[0,1,1,1,0,1],[1,0,0,0,1,0],[0,1,1,1,0,1],[1,0,0,0,1,0]],
        [[1,0,0,0,1,1],[1,0,0,0,0,0],[0,1,1,1,1,1],[1,0,0,0,0,0],[0,1,1,1,1,1],[1,0,0,0,0,0]],
        [[1,0,0,1,0,0],[0,1,1,0,1,1],[1,0,0,1,0,0],[0,1,1,0,1,1],[1,0,0,1,0,0],[0,1,1,0,1,1]],
        [[1,0,0,1,0,1],[0,1,1,0,1,0],[1,0,0,1,0,1],[0,1,1,0,1,0],[1,0,0,1,0,1],[0,1,1,0,1,0]],
        [[1,0,0,1,1,0],[0,1,1,0,0,1],[1,0,0,1,1,0],[0,1,1,0,0,1],[1,0,0,1,1,0],[0,1,1,0,0,1]],
        [[1,0,0,1,1,1],[0,1,1,0,0,0],[1,0,0,1,1,1],[0,1,1,0,0,0],[1,0,0,1,1,1],[0,1,1,0,0,0]],
    ],
    "DICT_7X7_1000": [
        [[1,0,0,0,0,0,0],[0,1,1,1,1,1,1],[0,1,1,1,1,1,1],[0,1,1,1,1,1,1],[0,1,1,1,1,1,1],[0,1,1,1,1,1,1],[0,1,1,1,1,1,1]],
        [[1,0,0,0,0,0,1],[0,1,1,1,1,1,0],[1,0,0,0,0,0,1],[0,1,1,1,1,1,0],[1,0,0,0,0,0,1],[0,1,1,1,1,1,0],[1,0,0,0,0,0,1]],
        [[1,0,0,0,0,1,0],[1,0,0,0,0,1,0],[0,1,1,1,1,0,1],[1,0,0,0,0,1,0],[0,1,1,1,1,0,1],[1,0,0,0,0,1,0],[0,1,1,1,1,0,1]],
        [[1,0,0,0,0,1,1],[1,0,0,0,0,0,0],[0,1,1,1,1,1,1],[1,0,0,0,0,0,0],[0,1,1,1,1,1,1],[1,0,0,0,0,0,0],[0,1,1,1,1,1,1]],
        [[1,0,0,0,1,0,0],[0,1,1,1,0,1,1],[1,0,0,0,1,0,0],[0,1,1,1,0,1,1],[1,0,0,0,1,0,0],[0,1,1,1,0,1,1],[1,0,0,0,1,0,0]],
        [[1,0,0,0,1,0,1],[0,1,1,1,0,1,0],[1,0,0,0,1,0,1],[0,1,1,1,0,1,0],[1,0,0,0,1,0,1],[0,1,1,1,0,1,0],[1,0,0,0,1,0,1]],
        [[1,0,0,0,1,1,0],[0,1,1,1,0,0,1],[1,0,0,0,1,1,0],[0,1,1,1,0,0,1],[1,0,0,0,1,1,0],[0,1,1,1,0,0,1],[1,0,0,0,1,1,0]],
        [[1,0,0,0,1,1,1],[0,1,1,1,0,0,0],[1,0,0,0,1,1,1],[0,1,1,1,0,0,0],[1,0,0,0,1,1,1],[0,1,1,1,0,0,0],[1,0,0,0,1,1,1]],
    ],
}

# ─────────────────────────────────────────────────────────────────────

def clear_scene():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()
    for block in bpy.data.meshes:
        bpy.data.meshes.remove(block)

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

def make_aruco_texture(marker_id, bits, dict_name):
    grid_size = bits + 2
    pattern   = ARUCO_PATTERNS[dict_name][marker_id]
    grid = [[1]*grid_size for _ in range(grid_size)]
    for r in range(bits):
        for c in range(bits):
            grid[r+1][c+1] = pattern[r][c]
    img = bpy.data.images.new(f"ArUco_{dict_name}_id{marker_id}",
                               width=grid_size, height=grid_size, alpha=False)
    pixels = []
    for r in reversed(range(grid_size)):
        for c in range(grid_size):
            v = 0.0 if grid[r][c] == 1 else 1.0
            pixels += [v, v, v, 1.0]
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
    for i in range(num):
        angle = 2 * math.pi * i / num
        bpy.ops.mesh.primitive_plane_add(size=size, location=(0, 0, 0.001))
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

    scene = bpy.context.scene
    scene.render.resolution_x = 1280
    scene.render.resolution_y = 720
    scene.render.fps = 24
    scene.render.image_settings.file_format  = 'FFMPEG'
    scene.render.ffmpeg.format = 'MPEG4'
    scene.render.engine = 'CYCLES'
    scene.cycles.samples = 128

    print("✓ Turntable built | subject rotating | camera static")

if __name__ == "__main__":
    build()