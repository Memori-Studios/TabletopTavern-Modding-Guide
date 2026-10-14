"""
Builds the Polygon Guy reskin of Levy Swordsmen as a TJBake unit visual folder, straight from the Synty FBX.

Model: "Mixamo POLYGON Guy (Naked)" by Synty Studios, shared for this example with Synty's permission.

The model is rigged but has no animations, so this script adds them. It reads the FBX itself (fbxbin.py), keeps the
mesh and skin weights, paints its own colour palettes, and writes the files the game reads. A reskin is usually baked
in Unity with the TJBake window instead; see the README.

Usage:
    python make_polygon_guy.py <Mixamo_POLYGON_Guy_Naked.fbx> <output unit folder> [--preview <png>] [--sheet <png>]

Needs Python 3.9+, numpy and Pillow:  pip install numpy pillow
"""

import json
import math
import os
import struct
import sys

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fbxbin  # noqa: E402

UNIT_NAME = "LevySwordsmen"
FPS = 30

# region Palettes

# Each variant is one palette PNG of four colour blocks. The mesh points every triangle at the middle of one block.
BLOCK_UV = {"skin": (0.25, 0.75), "eyes": (0.75, 0.75), "beard": (0.25, 0.25), "shorts": (0.75, 0.25)}
PALETTES = [
    {"file": "palette_brown_beard.png", "skin": (222, 184, 153), "eyes": (30, 24, 22), "beard": (92, 60, 38),
     "shorts": (184, 158, 115)},
    {"file": "palette_clean_shaven.png", "skin": (184, 133, 97), "eyes": (30, 24, 22), "beard": (184, 133, 97),
     "shorts": (140, 46, 36)},
    {"file": "palette_black_beard.png", "skin": (110, 74, 52), "eyes": (24, 20, 18), "beard": (28, 24, 22),
     "shorts": (78, 92, 56)},
]
# The FBX points at a Synty colour atlas; these are the three spots it uses.
SPOT_TO_BLOCK = {(0.314, 0.934): "skin", (0.03, 0.816): "eyes", (0.325, 0.89): "beard"}
# Skin triangles with every corner between these heights (metres) become shorts.
SHORTS = (0.70, 0.975)


def palette_image(p, size=256):
    img = Image.new("RGB", (size, size))
    half = size // 2
    for block, (u, v) in BLOCK_UV.items():
        x, y = int(u * size - half / 2), int((1 - v) * size - half / 2)
        img.paste(p[block], (x, y, x + half, y + half))
    return img

# endregion

# region Reading the FBX


def load(path):
    _, root = fbxbin.read(path)
    objs = {n.props[0]: n for n in root.find("Objects").children if n.props}
    name = {k: o.props[1].split("\x00")[0] for k, o in objs.items()}
    joints = [k for k, o in objs.items() if o.name == "Model" and o.props[2] == "LimbNode"]
    parent, cluster_bone = {}, {}
    for c in root.find("Connections").children:
        if c.props[0] != "OO":
            continue
        a, b = c.props[1], c.props[2]
        if a in joints and b in joints:
            parent[a] = b
        elif a in joints and objs.get(b) is not None and objs[b].name == "Deformer":
            cluster_bone[b] = a

    # Hands share finger names; give each finger the side of the hand it hangs from.
    def side(k):
        while k in parent:
            if name[k].endswith("_L") or name[k].endswith("_R"):
                return name[k][-2:]
            k = parent[k]
        return ""
    bone_name = {k: name[k] if name[k][-2:] in ("_L", "_R") or not side(k) else name[k] + side(k) for k in joints}

    # FBX is right-handed and Unity left-handed: mirror X, as Unity's importer does. Units are centimetres.
    flip = np.array([-1.0, 1.0, 1.0])
    world = {}
    for pn in [o for o in objs.values() if o.name == "Pose"][0].findall("PoseNode"):
        world[pn.find("Node").props[0]] = fbxbin.arr(pn.find("Matrix")).reshape(4, 4).T
    rest = {}
    for k in joints:
        rest[bone_name[k]] = world[k][:3, 3] * flip if k in world else None
    order = []

    def visit(k):
        if bone_name[k] in [bone_name[o] for o in order]:
            return
        if k in parent:
            visit(parent[k])
        order.append(k)
    for k in joints:
        visit(k)
    for k in order:
        if rest[bone_name[k]] is None:
            rest[bone_name[k]] = rest[bone_name[parent[k]]].copy() if k in parent else np.zeros(3)
    bones = [bone_name[k] for k in order]
    joint_parent = {bone_name[k]: (bone_name[parent[k]] if k in parent else None) for k in order}

    geo = [o for o in objs.values() if o.name == "Geometry"][0]
    pos = fbxbin.arr(geo.find("Vertices")).reshape(-1, 3) * 0.01 * flip
    weights = np.zeros((len(pos), len(bones)))
    for cl, k in cluster_bone.items():
        idx = fbxbin.arr(objs[cl].find("Indexes"), int)
        if idx is None:
            continue
        weights[idx, bones.index(bone_name[k])] = fbxbin.arr(objs[cl].find("Weights"))

    pvi = fbxbin.arr(geo.find("PolygonVertexIndex"), int)
    corner = np.where(pvi < 0, -pvi - 1, pvi).reshape(-1, 3)
    normals = fbxbin.arr(geo.find("LayerElementNormal").find("Normals")).reshape(-1, 3, 3) * flip
    uvl = geo.find("LayerElementUV")
    uv = fbxbin.arr(uvl.find("UV")).reshape(-1, 2)[fbxbin.arr(uvl.find("UVIndex"), int)].reshape(-1, 3, 2)
    blocks = []
    for t in range(len(corner)):
        block = SPOT_TO_BLOCK[tuple(np.round(uv[t, 0], 3))]
        if block == "skin" and np.all((pos[corner[t]][:, 1] >= SHORTS[0]) & (pos[corner[t]][:, 1] <= SHORTS[1])):
            block = "shorts"
        blocks.append(block)
    return {"pos": pos, "weights": weights, "bones": bones, "rest": rest, "parent": joint_parent,
            "corner": corner, "normals": normals, "blocks": blocks}


def build_mesh(m):
    """One skinned mesh. Corners sharing position, normal and colour block share a vertex."""
    keys, verts, tris = {}, [], []
    for t, block in enumerate(m["blocks"]):
        tri = []
        for k in range(3):
            vi = int(m["corner"][t, k])
            n = m["normals"][t, k]
            key = (vi, round(float(n[0]), 4), round(float(n[1]), 4), round(float(n[2]), 4), block)
            if key not in keys:
                keys[key] = len(verts)
                verts.append((vi, n, BLOCK_UV[block]))
            tri.append(keys[key])
        a, b, c = tri
        pa, pb, pc = (m["pos"][verts[i][0]] for i in tri)
        navg = sum(verts[i][1] for i in tri)
        # Keep the face whose winding agrees with the authored normal (Unity's front face).
        if np.dot(np.cross(pb - pa, pc - pa), navg) < 0:
            b, c = c, b
        tris.append((a, b, c))
    vi = np.array([v[0] for v in verts])
    w = m["weights"][vi]
    top = np.argsort(-w, axis=1)[:, :4]
    tw = np.take_along_axis(w, top, axis=1)
    tw = tw / tw.sum(axis=1, keepdims=True)
    return {"pos": m["pos"][vi], "nrm": np.array([v[1] for v in verts]), "uv": np.array([v[2] for v in verts]),
            "bi": top.astype(np.uint16), "bw": tw.astype(np.float32), "idx": np.array(tris, np.int64).ravel(), "tex": 0}

# endregion

# region Pose and animation



def rot_x(d):
    a = math.radians(d)
    c, s = math.cos(a), math.sin(a)
    return np.array([[1, 0, 0], [0, c, -s], [0, s, c]])


def rot_y(d):
    a = math.radians(d)
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])


def rot_z(d):
    a = math.radians(d)
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])


def euler(e):
    """Model-space axes. Negative X swings a hanging limb forward (+Z); positive Y turns toward the right (+X)."""
    return rot_x(e[0]) @ rot_z(e[2]) @ rot_y(e[1])


def mat4(r=None, t=(0, 0, 0)):
    m = np.eye(4)
    if r is not None:
        m[:3, :3] = r
    m[:3, 3] = t
    return m


def about(p, r):
    """Rotation r about the point p."""
    return mat4(t=p) @ mat4(r) @ mat4(t=-np.asarray(p))

class Rig:
    def __init__(self, m):
        self.rest, self.parent, self.bones = m["rest"], m["parent"], m["bones"]

    def pose(self, p):
        """Model-space transform of every joint. Rotations are about the joint's rest position, in model axes."""
        g = {}
        for b in self.bones:
            local = about(self.rest[b], euler(p.get(b, (0, 0, 0))))
            if b == "Root":
                local = mat4(euler(p.get("root_r", (0, 0, 0))), p.get("root_t", (0, 0, 0))) @ local
            elif b == "Hips":
                local = mat4(t=p.get("hips_t", (0, 0, 0))) @ local
            par = self.parent[b]
            g[b] = local if par is None else g[par] @ local
        return g


def lerp_pose(a, b, t):
    out = {}
    for k in set(a) | set(b):
        va, vb = np.array(a.get(k, (0, 0, 0)), float), np.array(b.get(k, (0, 0, 0)), float)
        out[k] = tuple(va + (vb - va) * t)
    return out


def smooth(t):
    return t * t * (3 - 2 * t)


def ease_in(t):
    return t * t


def linear(t):
    return t


def keyframed(keys, frames):
    poses = []
    for f in range(frames):
        for i in range(len(keys) - 1):
            f0, f1 = keys[i][0], keys[i + 1][0]
            if f0 <= f <= f1:
                ease = keys[i][2] if len(keys[i]) > 2 else smooth
                t = 0 if f1 == f0 else (f - f0) / (f1 - f0)
                poses.append(lerp_pose(keys[i][1], keys[i + 1][1], ease(t)))
                break
        else:
            poses.append(dict(keys[-1][1]))
    return poses


def P(base, **over):
    p = dict(base)
    p.update(over)
    return p


def add(*poses):
    """Sums rotations and offsets, for layering a wobble over a key pose."""
    out = {}
    for p in poses:
        for k, v in p.items():
            out[k] = tuple(np.array(out.get(k, (0, 0, 0)), float) + np.array(v, float))
    return out




def sym(**bones):
    """Mirrors left-side rotations onto the right: X stays, Y and Z flip. Keys name the bone without its side."""
    out = {}
    for b, (x, y, z) in bones.items():
        out[b + "_L"] = (x, y, z)
        out[b + "_R"] = (x, -y, -z)
    return out


def side(s, **bones):
    """Rotations for one side only, written as for the left; s is 'L' or 'R'."""
    flip = 1 if s == "L" else -1
    return {b + "_" + s: (x, y * flip, z * flip) for b, (x, y, z) in bones.items()}


FINGERS = ["IndexFinger_01", "IndexFinger_02", "IndexFinger_03", "Finger_01", "Finger_02", "Finger_03"]


def fist(s, curl=80):
    return side(s, **{f: (0, 0, curl / 2 if f.endswith("01") else curl) for f in FINGERS}, Thumb_02=(0, 30, 20),
                Thumb_03=(0, 0, 30))


# Arms hang a little forward of the hips, elbows soft, hands loose.
REST = {**sym(Shoulder=(0, 6, 74), Elbow=(0, 12, 0)), **sym(**{f: (0, 0, 12) for f in FINGERS})}
GUARD = {**REST, **fist("L"), **fist("R"),
         **sym(Shoulder=(-25, 20, 62), Elbow=(0, 125, 0), Hand=(0, 0, 0)),
         "hips_t": (0, -0.05, 0), "Spine_01": (8, -10, 0), "Spine_03": (4, 0, 0), "Head": (-10, 10, 0),
         **side("L", UpperLeg=(-22, 0, 6), LowerLeg=(18, 0, 0), Ankle=(4, 0, 0)),
         **side("R", UpperLeg=(14, 0, 4), LowerLeg=(24, 0, 0), Ankle=(-8, 0, 0))}


def anim_idle():
    n = 60
    out = []
    for f in range(n):
        ph = 2 * math.pi * f / n
        s = math.sin(ph)
        out.append(add(REST, {"hips_t": (0, 0.004 * s, 0), "Spine_02": (1.5 * s, 0, 0), "Spine_03": (1.5 * s, 0, 0),
                              "Head": (-2 * s, 0, 0), **sym(Shoulder=(0, 0, -2 * s), Clavicle=(0, 0, -1.5 * s))}))
    return out


def gait(n, swing, knee, bob, lean, arm, elbow):
    out = []
    for f in range(n):
        ph = 2 * math.pi * f / n
        s = math.sin(ph)
        out.append(add(REST, {
            "hips_t": (0, bob * abs(math.cos(ph)) - bob, 0), "Spine_01": (lean, 4 * s, 0), "Head": (-lean * 0.8, -3 * s, 0),
            "UpperLeg_L": (-swing * s, 0, 0), "UpperLeg_R": (swing * s, 0, 0),
            "LowerLeg_L": (knee * max(0.0, math.sin(ph + 1.6)), 0, 0),
            "LowerLeg_R": (knee * max(0.0, math.sin(ph + 1.6 + math.pi)), 0, 0),
            "Ankle_L": (-0.3 * swing * s, 0, 0), "Ankle_R": (0.3 * swing * s, 0, 0),
            "Shoulder_L": (arm * s, 0, -4), "Shoulder_R": (-arm * s, 0, 4),
            **sym(Elbow=(0, elbow, 0)),
        }))
    return out


def anim_stance():
    n = 40
    out = []
    for f in range(n):
        ph = 2 * math.pi * f / n
        s = math.sin(ph)
        out.append(add(GUARD, {"hips_t": (0, 0.012 * s, 0), "Spine_01": (0, 3 * s, 0),
                               **sym(Shoulder=(2 * s, 0, 0))}))
    return out


def anim_punch():
    """Left jab, then a right cross with the hips turning into it."""
    jab = P(GUARD, Shoulder_L=(-8, 84, 6), Elbow_L=(0, 8, 0), Spine_01=(10, 8, 0), Head=(-10, 0, 0))
    load = P(GUARD, Spine_01=(8, -25, 0), Shoulder_R=(-25, -20, -64))
    cross = P(GUARD, Shoulder_R=(-8, -84, -6), Elbow_R=(0, -6, 0), Spine_01=(14, 30, 0), Head=(-12, -20, 0),
              UpperLeg_R=(8, 0, 4), LowerLeg_R=(14, 0, 0), Ankle_R=(-20, 0, 0))
    keys = [(0, GUARD), (4, jab, ease_in), (7, jab), (11, GUARD), (14, load), (18, cross, ease_in), (22, cross), (32, GUARD)]
    return keyframed(keys, 33)


def anim_kick():
    """A front kick with the right leg: chamber the knee, snap the foot out, step back down."""
    chamber = P(GUARD, UpperLeg_R=(-85, 0, 0), LowerLeg_R=(100, 0, 0), Ankle_R=(20, 0, 0), Spine_01=(-6, 0, 0),
                LowerLeg_L=(10, 0, 0))
    snap = P(chamber, UpperLeg_R=(-80, 0, 0), LowerLeg_R=(5, 0, 0), Ankle_R=(-30, 0, 0), Spine_01=(-14, 0, 0))
    keys = [(0, GUARD), (8, chamber), (12, snap, ease_in), (16, snap), (21, chamber), (30, GUARD)]
    return keyframed(keys, 31)


def anim_look_around():
    left = P(REST, Head=(0, -45, 0), Neck=(0, -15, 0), Spine_02=(0, -8, 0))
    right = P(REST, Head=(0, 45, 0), Neck=(0, 15, 0), Spine_02=(0, 8, 0))
    return keyframed([(0, REST), (14, left), (28, left), (46, right), (60, right), (74, REST)], 75)


def anim_stretch():
    up = P(REST, **sym(Shoulder=(0, 10, -70), Elbow=(0, 10, 0)), Spine_02=(-8, 0, 0), Head=(-15, 0, 0), hips_t=(0, 0.01, 0))
    keys = [(0, REST), (16, up), (30, up), (36, P(up, Spine_01=(0, 0, 10))), (46, P(up, Spine_01=(0, 0, -10))), (54, up),
            (68, REST)]
    return keyframed(keys, 69)


def anim_wave():
    raised = P(REST, **side("R", Shoulder=(0, 15, 10), Elbow=(0, 0, -95)), Head=(0, 15, 5))
    keys = [(0, REST), (10, raised)]
    for i, f in enumerate(range(16, 46, 6)):
        keys.append((f, P(raised, **side("R", Elbow=(0, 0, -70 if i % 2 == 0 else -115)))))
    keys += [(52, raised), (62, REST)]
    return keyframed(keys, 63)


def anim_thrown():
    # Flip about the hips, not the feet, so the head clears the ground upside down.
    tuck = {**sym(UpperLeg=(-70, 0, 0), LowerLeg=(90, 0, 0), Shoulder=(-40, 20, 40))}
    rise = P(REST, hips_t=(0, 0.8, 0), Hips=(-90, 0, 0), **tuck)
    air = P(REST, hips_t=(0, 1.1, 0), Hips=(-190, 0, 0), **tuck)
    fall = P(REST, hips_t=(0, 0.6, 0), Hips=(-300, 0, 0), **tuck)
    land = P(REST, Hips=(-360, 0, 0), hips_t=(0, -0.12, 0), **sym(UpperLeg=(-45, 0, 0), LowerLeg=(70, 0, 0),
                                                                    Ankle=(-25, 0, 0), Shoulder=(-30, 20, 50)))
    keys = [(0, REST), (7, rise, linear), (13, air, linear), (19, fall, linear), (24, land),
            (30, P(land, hips_t=(0, -0.09, 0))), (46, P(REST, Hips=(-360, 0, 0)))]
    return keyframed(keys, 47)

# endregion

# region Deaths, kept on the ground

def lowest_point(rig, parts, pose):
    g = rig.pose(pose)
    skin = np.array([g[b] for b in rig.bones])
    low = np.inf
    for part in parts:
        p = skinned_positions(part, skin)
        low = min(low, p[:, 1].min())
    return low


def grounded(rig, parts, pose):
    probe = P(pose, root_t=(pose.get("root_t", (0, 0, 0))[0], 0, pose.get("root_t", (0, 0, 0))[2]))
    lift = -lowest_point(rig, parts, probe)
    t = probe["root_t"]
    return P(pose, root_t=(t[0], lift, t[2]))


def topple(rig, parts, end, n):
    end = grounded(rig, parts, end)
    bounce = P(end, root_r=tuple(a * 0.92 for a in end["root_r"]), root_t=tuple(t * 1.15 for t in end["root_t"]))
    stagger = P(REST, Spine_01=(-12 if end["root_r"][0] < 0 else 14, 0, 0), **sym(Shoulder=(-20, 10, 50)),
                LowerLeg_L=(25, 0, 0))
    keys = [(0, REST), (8, stagger), (24, end, ease_in), (28, bounce), (32, end), (n - 1, end)]
    return keyframed(keys, n)


def deaths(rig, parts):
    back = P(REST, root_r=(-90, 0, 0), **sym(Shoulder=(0, 0, 20), Elbow=(0, 30, 0)), Head=(10, 0, 0),
             UpperLeg_L=(-20, 0, 0), LowerLeg_L=(30, 0, 0))
    front = P(REST, root_r=(90, 0, 0), **sym(Shoulder=(0, -20, 60), Elbow=(0, 40, 0)), Head=(-20, 30, 0),
              UpperLeg_R=(-25, 0, 0), LowerLeg_R=(40, 0, 0))
    curl = P(REST, root_r=(0, 0, -90), **sym(UpperLeg=(-60, 0, 0), LowerLeg=(80, 0, 0), Shoulder=(-50, 20, 40),
                                              Elbow=(0, 60, 0)), Spine_01=(25, 0, 0), Head=(15, 0, 0))
    return topple(rig, parts, back, 50), topple(rig, parts, front, 50), topple(rig, parts, curl, 55)

# endregion

# region Writers


def pad16(buf):
    while len(buf) % 16:
        buf.append(0)


def write_mesh(path, pos, nrm, uv, idx, bounds, bi=None, bw=None):
    n = len(pos)
    wide = n > 65535
    skinned = bi is not None
    flags = 1 | 4 | (8 if skinned else 0) | (16 if wide else 0)
    buf = bytearray(b"TJBM" + struct.pack("<IIII", 1, n, len(idx), flags))
    buf += struct.pack("<6f", *bounds[0], *bounds[1]) + struct.pack("<III", 1, 0, len(idx))
    for arr in (pos, nrm, uv):
        pad16(buf)
        buf += np.asarray(arr, np.float32).tobytes()
    if skinned:
        pad16(buf)
        buf += np.asarray(bi, np.uint16).tobytes()
        pad16(buf)
        buf += np.asarray(bw, np.float32).tobytes()
    pad16(buf)
    buf += np.asarray(idx, np.uint32 if wide else np.uint16).tobytes()
    with open(path, "wb") as f:
        f.write(buf)


def write_anim(path, skin):
    frames, bones = skin.shape[:2]
    with open(path, "wb") as f:
        f.write(b"TJBA" + struct.pack("<III", 1, bones, frames) + bytes(16))
        f.write(skin[:, :, :3, :].astype(np.float16).tobytes())


def skinned_positions(part, skin):
    """skin: (bones, 4, 4) for one frame."""
    h = np.c_[part["pos"], np.ones(len(part["pos"]))]
    out = np.zeros((len(h), 3))
    for k in range(4):
        m = skin[part["bi"][:, k].astype(int)]
        out += part["bw"][:, k:k + 1] * np.einsum("nij,nj->ni", m[:, :3, :], h)
    return out

# endregion

# region Build


def lifted(rig, parts, poses):
    """Raises any frame that would sink below the ground, so feet never clip the battlefield."""
    out = []
    for p in poses:
        low = lowest_point(rig, parts, p)
        if low < 0:
            t = p.get("root_t", (0, 0, 0))
            p = P(p, root_t=(t[0], t[1] - low, t[2]))
        out.append(p)
    return out


def slot_table(rig, parts):
    d1, d2, d3 = deaths(rig, parts)
    clips = [
        (0, "idle", anim_idle(), True, False),
        (1, "walk", gait(32, swing=26, knee=40, bob=0.02, lean=3, arm=20, elbow=18), True, False),
        (2, "run", gait(20, swing=42, knee=80, bob=0.05, lean=14, arm=40, elbow=80), True, False),
        (3, "meleeStance", anim_stance(), True, False),
        (4, "meleeAttack", anim_punch(), False, True),
        (5, "idleVariant1", anim_look_around(), False, True),
        (6, "idleVariant2", anim_stretch(), False, True),
        (7, "idleVariant3", anim_wave(), False, True),
        (8, "death1", d1, False, False),
        (9, "death2", d2, False, False),
        (10, "death3", d3, False, False),
        (11, "thrown", anim_thrown(), False, True),
        (12, "meleeAttackAlt", anim_kick(), False, True),
    ]
    return [(sid, name, poses if 8 <= sid <= 10 else lifted(rig, parts, poses), loop, ret) for sid, name, poses, loop, ret in clips]


def build(fbx, out):
    m = load(fbx)
    rig = Rig(m)
    mesh = build_mesh(m)
    slots = slot_table(rig, [mesh])
    poses, table, start = [], [], 0
    for sid, name, frames, loop, ret in slots:
        poses += frames
        table.append({"id": sid, "name": name, "start": start, "count": len(frames), "loop": loop, "returnToIdle": ret,
                      "returnAt": 0.9})
        start += len(frames)
    skin = np.array([[rig.pose(p)[b] for b in rig.bones] for p in poses])

    os.makedirs(out, exist_ok=True)
    write_anim(os.path.join(out, "anim.bin"), skin)

    lo, hi = np.full(3, np.inf), np.full(3, -np.inf)
    for f in range(len(poses)):
        p = skinned_positions(mesh, skin[f])
        lo, hi = np.minimum(lo, p.min(0)), np.maximum(hi, p.max(0))
    grow = (hi - lo) * 0.05
    write_mesh(os.path.join(out, "body.mesh.bin"), mesh["pos"], mesh["nrm"], mesh["uv"], mesh["idx"],
               ((lo - grow).tolist(), (hi + grow).tolist()), mesh["bi"], mesh["bw"])

    for p in PALETTES:
        palette_image(p).save(os.path.join(out, p["file"]))

    manifest = {
        "format": 1,
        "kind": "unit",
        "unitName": UNIT_NAME,
        "baker": "make_polygon_guy.py (hand-written example, not TJBake)",
        "skeleton": {"boneCount": len(rig.bones), "names": rig.bones},
        "frameRate": FPS,
        "slots": table,
        "anchors": [],
        # One material per variant: the same body, painted from a different palette.
        "materials": [{"name": p["file"][:-4], "baseColor": p["file"], "normal": "", "emission": "", "tint": [1, 1, 1, 1],
                       "smoothness": 0.1, "transparent": False} for p in PALETTES],
        "lodSwitch": [],
        "variants": [{"lods": [{"meshes": [{"file": "body.mesh.bin", "material": v}]}], "attachments": []}
                     for v in range(len(PALETTES))],
    }
    with open(os.path.join(out, "unit.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(manifest, f, indent=2)
        f.write("\n")
    return rig, mesh, poses, table

# endregion

# region Preview renderer


def textures():
    return [np.asarray(palette_image(p), float) / 255.0 for p in PALETTES]


def scene_tris(rig, mesh, pose, tex=0, offset=(0, 0, 0)):
    g = rig.pose(pose)
    skin = np.array([g[b] for b in rig.bones])
    p = skinned_positions(mesh, skin) + np.array(offset)
    idx = mesh["idx"].reshape(-1, 3)
    return [(p[idx], mesh["uv"][idx], tex)]


def render(groups, texs, eye, target, size, fov, bg, ground=None):
    w, h = size
    eye, target = np.array(eye, float), np.array(target, float)
    fwd = target - eye
    fwd /= np.linalg.norm(fwd)
    right = np.cross([0, 1, 0], fwd)
    right /= np.linalg.norm(right)
    up = np.cross(fwd, right)
    img = np.zeros((h, w, 4))
    img[:] = bg
    zbuf = np.full((h, w), np.inf)
    focal = 0.5 * h / math.tan(math.radians(fov) / 2)
    light = np.array([0.4, 0.85, 0.5])
    light /= np.linalg.norm(light)
    if ground is not None:
        g = np.array([[[-4, 0, -4], [-4, 0, 4], [4, 0, 4]], [[-4, 0, -4], [4, 0, 4], [4, 0, -4]]], float)
        groups = [(g, None, ground)] + list(groups)
    for tris, uvs, tex in groups:
        for i, t in enumerate(tris):
            n = np.cross(t[1] - t[0], t[2] - t[0])
            ln = np.linalg.norm(n)
            if ln < 1e-12:
                continue
            n /= ln
            if np.dot(n, eye - t.mean(axis=0)) <= 0:
                continue
            rel = t - eye
            z = rel @ fwd
            if np.any(z < 0.05):
                continue
            sx = w / 2 + focal * (rel @ right) / z
            sy = h / 2 - focal * (rel @ up) / z
            x0, x1 = int(max(0, math.floor(sx.min()))), int(min(w - 1, math.ceil(sx.max())))
            y0, y1 = int(max(0, math.floor(sy.min()))), int(min(h - 1, math.ceil(sy.max())))
            if x0 > x1 or y0 > y1:
                continue
            xs, ys = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
            (ax, bx, cx), (ay, by, cy) = sx, sy
            den = (by - cy) * (ax - cx) + (cx - bx) * (ay - cy)
            if abs(den) < 1e-12:
                continue
            l1 = ((by - cy) * (xs - cx) + (cx - bx) * (ys - cy)) / den
            l2 = ((cy - ay) * (xs - cx) + (ax - cx) * (ys - cy)) / den
            l3 = 1 - l1 - l2
            inside = (l1 >= 0) & (l2 >= 0) & (l3 >= 0)
            if not inside.any():
                continue
            depth = l1 * z[0] + l2 * z[1] + l3 * z[2]
            sub = zbuf[y0:y1 + 1, x0:x1 + 1]
            draw = inside & (depth < sub)
            if not draw.any():
                continue
            shade = 0.5 + 0.55 * max(0.0, float(np.dot(n, light)))
            region = img[y0:y1 + 1, x0:x1 + 1]
            if uvs is None:
                region[draw, :3] = np.clip(np.array(tex) * shade, 0, 1)
            else:
                tx = texs[tex]
                th, tw = tx.shape[:2]
                u = l1[draw] * uvs[i, 0, 0] + l2[draw] * uvs[i, 1, 0] + l3[draw] * uvs[i, 2, 0]
                v = l1[draw] * uvs[i, 0, 1] + l2[draw] * uvs[i, 1, 1] + l3[draw] * uvs[i, 2, 1]
                px = np.clip((np.mod(u, 1.0) * tw).astype(int), 0, tw - 1)
                py = np.clip(((1 - np.mod(v, 1.0)) * th).astype(int), 0, th - 1)
                region[draw, :3] = np.clip(tx[py, px] * shade, 0, 1)
            region[draw, 3] = 1
            sub[draw] = depth[draw]
    return img


def to_image(img, scale):
    im = Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8), "RGBA")
    return im.resize((im.width // scale, im.height // scale), Image.LANCZOS) if scale != 1 else im



def render_icon(rig, mesh, texs, path):
    pose = P(GUARD, Head=(-10, -5, 0))
    img = render(scene_tris(rig, mesh, pose), texs, eye=(-0.9, 1.75, 2.6), target=(0, 1.35, 0), size=(512, 512), fov=26,
                 bg=(0, 0, 0, 0))
    to_image(img, 2).save(path)


def render_preview(rig, mesh, texs, poses_and_spots, path):
    groups = []
    for v, (pose, offset) in enumerate(poses_and_spots):
        groups += scene_tris(rig, mesh, pose, v, offset)
    img = render(groups, texs, eye=(0, 1.7, 5.2), target=(0, 0.9, 0), size=(1024, 1024), fov=34,
                 bg=(0.16, 0.11, 0.08, 1), ground=(0.40, 0.52, 0.30))
    to_image(img, 2).convert("RGB").save(path)


def contact_sheet(rig, mesh, texs, table, poses, path):
    cell = 150
    views = ((3.2, 1.5, 3.2), (4.4, 1.2, 0.0))
    sheet = Image.new("RGB", (cell * 16, cell * len(table)), (0, 0, 0))
    for r, s in enumerate(table):
        clip = poses[s["start"]:s["start"] + s["count"]]
        picks = [clip[int(i * (len(clip) - 1) / 7)] for i in range(8)]
        for vi, eye in enumerate(views):
            for i, pose in enumerate(picks):
                img = render(scene_tris(rig, mesh, pose, r % len(texs)), texs, eye=eye, target=(0, 0.85, 0),
                             size=(cell * 2, cell * 2), fov=42, bg=(0.25, 0.25, 0.3, 1), ground=(0.40, 0.52, 0.30))
                sheet.paste(to_image(img, 2).convert("RGB"), ((vi * 8 + i) * cell, r * cell))
    sheet.save(path)

# endregion


def main():
    args = sys.argv[1:]
    if len(args) < 2:
        print(__doc__)
        sys.exit(1)
    fbx, out = args[:2]
    rig, mesh, poses, table = build(fbx, out)
    texs = textures()
    render_icon(rig, mesh, texs, os.path.join(out, "icon.png"))
    first = {s["id"]: s["start"] for s in table}
    if "--preview" in args:
        render_preview(rig, mesh, texs, [(poses[first[3] + 5], (-1.2, 0, -0.2)), (poses[first[4] + 5], (0, 0, 0.4)),
                                         (poses[first[0]], (1.2, 0, -0.2))], args[args.index("--preview") + 1])
    if "--sheet" in args:
        contact_sheet(rig, mesh, texs, table, poses, args[args.index("--sheet") + 1])
    print(f"Wrote {UNIT_NAME}: {len(rig.bones)} bones, {len(poses)} frames, {len(mesh['idx']) // 3} triangles, "
          f"{len(mesh['pos'])} vertices.")


if __name__ == "__main__":
    main()
