"""
create_subject.py
─────────────────────────────────────────────────────────────────────
Run this script ONCE in a fresh Blender file to build the benchmark
box and save it as  subject.blend  in the same folder.

Object specs (ground truth for metric accuracy check):
  Box body     : 60 × 60 × 60 mm
  Inset panels : 4 mm deep, 8 mm border on each face
  Lid panel    : slightly raised 2 mm
  Corner posts : 4 mm square, full height
  Hinge (back) : 2 cylindrical barrels, 6 mm Ø × 10 mm
  Latch (front): flat plate 20×8×2 mm + pin 2 mm Ø
  Bolt hole    : 5 mm Ø through top centre

Materials (all procedural, no image textures needed):
  Wood body    : wave + noise grain, oak colours
  Dark wood    : deeper grain for inset recesses
  Aged metal   : principled metallic + scratched bump
  Rust spots   : mixed onto metal edges via noise mask
─────────────────────────────────────────────────────────────────────
"""

import bpy
import math
import os

# ── Output path ───────────────────────────────────────────────────────
OUTPUT_BLEND = bpy.path.abspath("//subject.blend")   # same folder as current .blend
# If you want an absolute path instead, set it here:
# OUTPUT_BLEND = "/home/user/project/subject.blend"

# ── Dimensions (metres) ───────────────────────────────────────────────
B   = 0.060   # box side length (60 mm cube)
H   = B       # height
INS = 0.004   # inset panel depth
BOR = 0.008   # inset panel border width
CP  = 0.004   # corner post half-width
LID = 0.002   # lid raise
HR  = 0.003   # hinge barrel radius
HL  = 0.010   # hinge barrel length
LPW = 0.020   # latch plate width
LPH = 0.008   # latch plate height
LPD = 0.002   # latch plate depth
LPR = 0.001   # latch pin radius

# ─────────────────────────────────────────────────────────────────────

def clear_scene():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()
    for d in [bpy.data.meshes, bpy.data.materials,
              bpy.data.curves, bpy.data.collections]:
        for b in d:
            d.remove(b)


# ══════════════════════════════════════════════════════════════════════
#  MATERIALS
# ══════════════════════════════════════════════════════════════════════

def _nodes(mat):
    mat.use_nodes = True
    n = mat.node_tree.nodes
    l = mat.node_tree.links
    n.clear()
    return n, l

def _out(nodes, links, bsdf):
    out = nodes.new("ShaderNodeOutputMaterial")
    out.location = (600, 0)
    links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])

def _coord_mapping(nodes, links, scale=(1,1,1), rotation=(0,0,0), loc=(0,0,0)):
    tc = nodes.new("ShaderNodeTexCoord");  tc.location  = (-900, 0)
    mp = nodes.new("ShaderNodeMapping");   mp.location  = (-700, 0)
    mp.inputs["Scale"].default_value    = scale
    mp.inputs["Rotation"].default_value = rotation
    mp.inputs["Location"].default_value = loc
    links.new(tc.outputs["Object"], mp.inputs["Vector"])
    return mp

def make_wood_material(name="WoodBox",
                       base=(0.52, 0.27, 0.10, 1),
                       dark=(0.22, 0.10, 0.04, 1),
                       roughness=0.58):
    mat = bpy.data.materials.new(name)
    n, l = _nodes(mat)

    mp = _coord_mapping(n, l,
                        scale=(10.0, 1.2, 1.0),
                        rotation=(0, 0, math.radians(8)))

    # Wave (ring lines)
    wave = n.new("ShaderNodeTexWave"); wave.location = (-460, 120)
    wave.wave_type = 'RINGS'; wave.bands_direction = 'X'
    wave.inputs["Scale"].default_value           = 7.0
    wave.inputs["Distortion"].default_value      = 4.0
    wave.inputs["Detail"].default_value          = 6.0
    wave.inputs["Detail Scale"].default_value    = 1.8
    wave.inputs["Detail Roughness"].default_value= 0.65
    l.new(mp.outputs["Vector"], wave.inputs["Vector"])

    # Noise (grain turbulence)
    noise = n.new("ShaderNodeTexNoise"); noise.location = (-460, -120)
    noise.inputs["Scale"].default_value      = 22.0
    noise.inputs["Detail"].default_value     = 9.0
    noise.inputs["Roughness"].default_value  = 0.68
    noise.inputs["Distortion"].default_value = 0.35
    l.new(mp.outputs["Vector"], noise.inputs["Vector"])

    # Mix wave + noise
    mx = n.new("ShaderNodeMixRGB"); mx.location = (-220, 0)
    mx.blend_type = 'ADD'; mx.inputs["Fac"].default_value = 0.22
    l.new(wave.outputs["Color"],  mx.inputs["Color1"])
    l.new(noise.outputs["Color"], mx.inputs["Color2"])

    # Color ramp → wood tones
    ramp = n.new("ShaderNodeValToRGB"); ramp.location = (-20, 0)
    ramp.color_ramp.interpolation = 'EASE'
    ramp.color_ramp.elements[0].position = 0.0
    ramp.color_ramp.elements[0].color    = dark
    ramp.color_ramp.elements[1].position = 1.0
    ramp.color_ramp.elements[1].color    = base
    mid = ramp.color_ramp.elements.new(0.42)
    mid.color = tuple((base[i]+dark[i])*0.55 for i in range(3)) + (1.0,)
    l.new(mx.outputs["Color"], ramp.inputs["Fac"])

    # Bump from noise
    bump = n.new("ShaderNodeBump"); bump.location = (-20, -260)
    bump.inputs["Strength"].default_value = 0.25
    bump.inputs["Distance"].default_value = 0.004
    l.new(noise.outputs["Fac"], bump.inputs["Height"])

    # Principled BSDF
    bsdf = n.new("ShaderNodeBsdfPrincipled"); bsdf.location = (220, 0)
    bsdf.inputs["Roughness"].default_value          = roughness
    bsdf.inputs["Specular IOR Level"].default_value = 0.25
    l.new(ramp.outputs["Color"],  bsdf.inputs["Base Color"])
    l.new(bump.outputs["Normal"], bsdf.inputs["Normal"])

    _out(n, l, bsdf)
    return mat


def make_metal_material(name="AgedMetal",
                        base=(0.62, 0.60, 0.55, 1)):
    mat = bpy.data.materials.new(name)
    n, l = _nodes(mat)

    mp = _coord_mapping(n, l, scale=(30, 30, 30))

    # Scratches via noise → bump
    noise = n.new("ShaderNodeTexNoise"); noise.location = (-460, 0)
    noise.inputs["Scale"].default_value      = 40.0
    noise.inputs["Detail"].default_value     = 12.0
    noise.inputs["Roughness"].default_value  = 0.75
    noise.inputs["Distortion"].default_value = 0.2
    l.new(mp.outputs["Vector"], noise.inputs["Vector"])

    bump = n.new("ShaderNodeBump"); bump.location = (-160, -160)
    bump.inputs["Strength"].default_value = 0.55
    bump.inputs["Distance"].default_value = 0.002
    l.new(noise.outputs["Fac"], bump.inputs["Height"])

    # Rust color mask (noise → mix between clean metal and rust)
    noise2 = n.new("ShaderNodeTexNoise"); noise2.location = (-460, -300)
    noise2.inputs["Scale"].default_value      = 8.0
    noise2.inputs["Detail"].default_value     = 5.0
    noise2.inputs["Roughness"].default_value  = 0.8
    l.new(mp.outputs["Vector"], noise2.inputs["Vector"])

    ramp_rust = n.new("ShaderNodeValToRGB"); ramp_rust.location = (-200, -300)
    ramp_rust.color_ramp.interpolation = 'EASE'
    ramp_rust.color_ramp.elements[0].position = 0.55
    ramp_rust.color_ramp.elements[0].color    = (0,0,0,1)
    ramp_rust.color_ramp.elements[1].position = 0.80
    ramp_rust.color_ramp.elements[1].color    = (1,1,1,1)
    l.new(noise2.outputs["Fac"], ramp_rust.inputs["Fac"])

    # Mix clean metal color with rust color
    mix_col = n.new("ShaderNodeMixRGB"); mix_col.location = (0, -200)
    mix_col.blend_type = 'MIX'
    mix_col.inputs["Color1"].default_value = base          # clean
    mix_col.inputs["Color2"].default_value = (0.35, 0.14, 0.04, 1)  # rust
    l.new(ramp_rust.outputs["Color"], mix_col.inputs["Fac"])

    # Mix metallic value (rust patches → non-metallic)
    mix_met = n.new("ShaderNodeMath"); mix_met.location = (0, -380)
    mix_met.operation = 'SUBTRACT'
    mix_met.inputs[0].default_value = 1.0
    l.new(ramp_rust.outputs["Color"], mix_met.inputs[1])

    # Roughness: rust is rougher
    mix_rough = n.new("ShaderNodeMixRGB"); mix_rough.location = (0, -500)
    mix_rough.blend_type = 'MIX'
    mix_rough.inputs["Color1"].default_value = (0.35,0.35,0.35,1)  # metal rough
    mix_rough.inputs["Color2"].default_value = (0.85,0.85,0.85,1)  # rust rough
    l.new(ramp_rust.outputs["Color"], mix_rough.inputs["Fac"])

    bsdf = n.new("ShaderNodeBsdfPrincipled"); bsdf.location = (240, 0)
    bsdf.inputs["Specular IOR Level"].default_value = 0.9
    l.new(mix_col.outputs["Color"],  bsdf.inputs["Base Color"])
    l.new(mix_met.outputs["Value"],  bsdf.inputs["Metallic"])
    l.new(mix_rough.outputs["Color"],bsdf.inputs["Roughness"])
    l.new(bump.outputs["Normal"],    bsdf.inputs["Normal"])

    _out(n, l, bsdf)
    return mat


def make_dark_wood_material():
    """Slightly darker wood for recessed inset panels."""
    return make_wood_material(
        name="WoodDark",
        base=(0.32, 0.16, 0.06, 1),
        dark=(0.14, 0.06, 0.02, 1),
        roughness=0.70
    )


# ══════════════════════════════════════════════════════════════════════
#  GEOMETRY HELPERS
# ══════════════════════════════════════════════════════════════════════

def new_box(name, sx, sy, sz, loc=(0,0,0), mat=None):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    obj = bpy.context.object
    obj.name = name
    obj.scale = (sx, sy, sz)
    bpy.ops.object.transform_apply(scale=True)
    if mat:
        if obj.data.materials:
            obj.data.materials[0] = mat
        else:
            obj.data.materials.append(mat)
    return obj


def new_cylinder(name, r, depth, loc=(0,0,0), rot=(0,0,0), mat=None, verts=32):
    bpy.ops.mesh.primitive_cylinder_add(
        radius=r, depth=depth, vertices=verts,
        location=loc,
        rotation=rot
    )
    obj = bpy.context.object
    obj.name = name
    if mat:
        if obj.data.materials:
            obj.data.materials[0] = mat
        else:
            obj.data.materials.append(mat)
    return obj


def boolean_diff(target, cutter, delete_cutter=True):
    """Subtract cutter from target using a Boolean modifier."""
    mod = target.modifiers.new("Bool_cut", "BOOLEAN")
    mod.operation = 'DIFFERENCE'
    mod.object    = cutter
    cutter.hide_render = True
    cutter.hide_viewport = False
    bpy.context.view_layer.objects.active = target
    bpy.ops.object.modifier_apply(modifier=mod.name)
    if delete_cutter:
        bpy.data.objects.remove(cutter, do_unlink=True)


def apply_bevel(obj, amount=0.0008, segments=2):
    """Add a small chamfer to all edges."""
    mod = obj.modifiers.new("Bevel", "BEVEL")
    mod.width    = amount
    mod.segments = segments
    mod.limit_method = 'ANGLE'
    mod.angle_limit  = math.radians(30)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.modifier_apply(modifier=mod.name)


def parent_to(child, parent):
    child.parent = parent
    child.matrix_parent_inverse = parent.matrix_world.inverted()


# ══════════════════════════════════════════════════════════════════════
#  BUILD FUNCTIONS
# ══════════════════════════════════════════════════════════════════════

def build_box_body(wood_mat, dark_mat):
    """
    Main 60×60×60 mm body.
    Six inset panels (one per face), chamfered edges.
    Flat base so it sits at Z=0.
    """
    half = B / 2

    # ── Outer shell ───────────────────────────────────────────────────
    body = new_box("BoxBody", B, B, H,
                   loc=(0, 0, half), mat=wood_mat)

    # ── Corner posts (4 vertical bars, slightly proud of surface) ─────
    for sx, sy in [(1,-1),(-1,-1),(1,1),(-1,1)]:
        post = new_box(f"Post_{sx}_{sy}", CP*2, CP*2, H+0.001,
                       loc=(sx*(half-CP), sy*(half-CP), half),
                       mat=wood_mat)

    # ── Inset panels (boolean cutters) ────────────────────────────────
    # We cut a shallow rectangular recess into each of the 6 faces.
    face_configs = [
        # (normal_axis, sign, rotation_to_align)
        ("z",  1),   # top
        ("z", -1),   # bottom
        ("x",  1),   # right
        ("x", -1),   # left
        ("y",  1),   # front
        ("y", -1),   # back
    ]
    panel_size = B - 2*BOR   # inner panel size
    for axis, sign in face_configs:
        if axis == "z":
            sx, sy, sz = panel_size, panel_size, INS*2
            lx = 0; ly = 0; lz = half*sign + sign*half - sign*INS
        elif axis == "x":
            sx, sy, sz = INS*2, panel_size, panel_size
            lx = half*sign + sign*half - sign*INS; ly = 0; lz = half
        else:  # y
            sx, sy, sz = panel_size, INS*2, panel_size
            lx = 0; ly = half*sign + sign*half - sign*INS; lz = half

        cutter = new_box(f"Inset_{axis}{sign}", sx, sy, sz,
                         loc=(lx, ly, lz))
        boolean_diff(body, cutter)

    # ── Bolt hole through top centre ─────────────────────────────────
    bolt_cyl = new_cylinder("BoltHole", r=0.0025, depth=H*1.2,
                            loc=(0, 0, half))
    boolean_diff(body, bolt_cyl)

    # ── Chamfer ───────────────────────────────────────────────────────
    apply_bevel(body, amount=0.0006, segments=2)

    # Assign dark wood to inset faces via a second material slot
    body.data.materials.append(dark_mat)

    return body


def build_hinges(metal_mat, parent_obj):
    """Two cylindrical hinge barrels on the back face."""
    back_y  = -(B / 2)
    offsets = [-0.015, 0.015]   # left and right of centre
    for i, ox in enumerate(offsets):
        h = new_cylinder(f"Hinge_{i}", r=HR, depth=HL,
                         loc=(ox, back_y, B*0.72),
                         rot=(math.pi/2, 0, 0),
                         mat=metal_mat)
        apply_bevel(h, amount=0.0003, segments=1)
        parent_to(h, parent_obj)


def build_latch(metal_mat, parent_obj):
    """A simple flat latch plate + pin on the front face."""
    front_y = B / 2

    # Plate
    plate = new_box("LatchPlate", LPW, LPD, LPH,
                    loc=(0, front_y + LPD/2, B*0.52),
                    mat=metal_mat)
    apply_bevel(plate, amount=0.0003, segments=1)
    parent_to(plate, parent_obj)

    # Pin (small cylinder protruding from plate)
    pin = new_cylinder("LatchPin", r=LPR, depth=LPD*3,
                       loc=(0, front_y + LPD*2, B*0.52),
                       rot=(math.pi/2, 0, 0),
                       mat=metal_mat)
    parent_to(pin, parent_obj)

    # Two screw heads (flat discs)
    for ox in [-0.007, 0.007]:
        screw = new_cylinder(f"Screw_{ox}", r=0.0015, depth=0.0005,
                             loc=(ox, front_y + 0.0001, B*0.52),
                             rot=(math.pi/2, 0, 0),
                             mat=metal_mat, verts=16)
        parent_to(screw, parent_obj)


def build_corner_brackets(metal_mat, parent_obj):
    """
    Four small L-shaped metal brackets on the top corners.
    Each is two thin plates joined at a corner.
    """
    half = B / 2
    thick = 0.001
    size  = 0.010   # bracket arm length

    for sx, sy in [(1,-1),(-1,-1),(1,1),(-1,1)]:
        # Horizontal arm
        arm_x = new_box(f"BrktH_{sx}{sy}", size, thick, thick*3,
                        loc=(sx*(half - size/2), sy*half, H + thick*1.5),
                        mat=metal_mat)
        parent_to(arm_x, parent_obj)
        # Vertical arm
        arm_y = new_box(f"BrktV_{sx}{sy}", thick, size, thick*3,
                        loc=(sx*half, sy*(half - size/2), H + thick*1.5),
                        mat=metal_mat)
        parent_to(arm_y, parent_obj)


def build_lid_panel(wood_mat, parent_obj):
    """
    Slightly raised panel inset on the top face — a real lid.
    Gives a clean flat reference surface for planarity error measurement.
    """
    panel_size = B - 2*BOR - 0.002
    lid = new_box("LidPanel", panel_size, panel_size, LID,
                  loc=(0, 0, H + LID/2),
                  mat=wood_mat)
    apply_bevel(lid, amount=0.0003, segments=1)
    parent_to(lid, parent_obj)


def build_reference_disc(metal_mat, parent_obj):
    """
    A flat metal disc on top centre — known diameter 10 mm.
    Photogrammetry ground truth: measure reconstructed diameter vs 10 mm.
    """
    disc = new_cylinder("RefDisc", r=0.005, depth=0.0005,
                        loc=(0, 0, H + LID + 0.00025),
                        mat=metal_mat, verts=64)
    parent_to(disc, parent_obj)


# ══════════════════════════════════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════════════════════════════════

def build_all():
    clear_scene()

    # Materials
    wood  = make_wood_material()
    dark  = make_dark_wood_material()
    metal = make_metal_material()

    # Body (sits with base at Z=0)
    body = build_box_body(wood, dark)

    # Hardware (all parented to body)
    build_hinges(metal, body)
    build_latch(metal, body)
    build_corner_brackets(metal, body)
    build_lid_panel(wood, body)
    build_reference_disc(metal, body)

    # Smooth shading on all mesh objects
    for obj in bpy.data.objects:
        if obj.type == 'MESH':
            bpy.context.view_layer.objects.active = obj
            bpy.ops.object.shade_smooth()

    # World background
    bpy.context.scene.world.use_nodes = True
    bg = bpy.context.scene.world.node_tree.nodes["Background"]
    bg.inputs["Color"].default_value    = (0.05, 0.05, 0.05, 1)
    bg.inputs["Strength"].default_value = 0.5

    # Render engine
    bpy.context.scene.render.engine = 'CYCLES'
    bpy.context.scene.cycles.samples = 64

    print(f"\n✓  Subject built")
    print(f"   Box body:       {B*1000:.0f}×{B*1000:.0f}×{H*1000:.0f} mm")
    print(f"   Inset border:   {BOR*1000:.0f} mm")
    print(f"   Inset depth:    {INS*1000:.0f} mm")
    print(f"   Ref disc Ø:     {0.005*2*1000:.0f} mm  ← metric ground truth")
    print(f"   Bolt hole Ø:    5 mm")
    print(f"   Hinge Ø:        {HR*2*1000:.0f} mm")


# ── Entry points ──────────────────────────────────────────────────────
# Alias so the module-loader pattern works: subject["build"]()
build = build_all

# When run directly from Blender's Scripting workspace (not via load_module),
# build AND save subject.blend automatically.
if __name__ == "__main__":
    build_all()
    bpy.ops.wm.save_as_mainfile(filepath=OUTPUT_BLEND)
    print(f"   Saved → {OUTPUT_BLEND}")