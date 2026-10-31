"""
Builds the Dude Bro reskin of Levy Swordsmen as a TJBake unit visual folder. Everything is made here in code: the
skeleton, a low-poly body, the colour palettes and the animations. No model file is needed.

A reskin is usually baked in Unity with the TJBake window instead; see the README. This script shows what the files
hold, and gives you a body you can change by editing numbers.

Usage:
    python make_dude_bro.py <output unit folder> [--preview <png>] [--sheet <png>]

Needs Python 3.9+, numpy and Pillow:  pip install numpy pillow
"""

import json
import math
import os
import struct
import sys

import numpy as np
from PIL import Image

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


def palette_image(p, size=256):
    img = Image.new("RGB", (size, size))
    half = size // 2
    for block, (u, v) in BLOCK_UV.items():
        x, y = int(u * size - half / 2), int((1 - v) * size - half / 2)
        img.paste(p[block], (x, y, x + half, y + half))
    return img

# endregion

# region Skeleton

# Joint rest positions in metres: a T-pose facing +Z, feet at height 0, left side at -X. The right side mirrors the left.
CENTRE_JOINTS = [
    ("Root", None, (0, 0, 0)),
    ("Hips", "Root", (0, 0.88, 0)),
    ("Spine_01", "Hips", (0, 0.98, -0.01)),
    ("Spine_02", "Spine_01", (0, 1.15, -0.01)),
    ("Spine_03", "Spine_02", (0, 1.32, -0.02)),
    ("Neck", "Spine_03", (0, 1.46, -0.02)),
    ("Head", "Neck", (0, 1.56, 0)),
]
LEFT_JOINTS = [
    ("Clavicle", "Spine_03", (-0.07, 1.39, 0.01)),
    ("Shoulder", "Clavicle", (-0.19, 1.39, -0.03)),
    ("Elbow", "Shoulder", (-0.52, 1.37, -0.04)),
    ("Hand", "Elbow", (-0.79, 1.37, -0.03)),
    ("Thumb_01", "Hand", (-0.82, 1.36, 0.0)),
    ("Thumb_02", "Thumb_01", (-0.85, 1.35, 0.035)),
    ("Thumb_03", "Thumb_02", (-0.885, 1.345, 0.06)),
    ("Finger_01", "Hand", (-0.885, 1.37, -0.03)),
    ("Finger_02", "Finger_01", (-0.94, 1.37, -0.03)),
    ("UpperLeg", "Hips", (-0.1, 0.84, -0.02)),
    ("LowerLeg", "UpperLeg", (-0.11, 0.46, -0.01)),
    ("Ankle", "LowerLeg", (-0.11, 0.08, -0.03)),
    ("Ball", "Ankle", (-0.11, 0.02, 0.08)),
]
CENTRE = {name for name, _, _ in CENTRE_JOINTS}


def mirror_name(b):
    return b[:-2] + "_R" if b.endswith("_L") else b


def skeleton():
    bones, parent, rest = [], {}, {}
    for name, par, p in CENTRE_JOINTS:
        bones.append(name)
        parent[name] = par
        rest[name] = np.array(p, float)
    for s, flip in (("_L", 1), ("_R", -1)):
        for name, par, p in LEFT_JOINTS:
            bones.append(name + s)
            parent[name + s] = par if par in CENTRE else par + s
            rest[name + s] = np.array(p, float) * (flip, 1, 1)
    return bones, parent, rest

# endregion

# region Building the body


class Body:
    """Flat-shaded triangles. Each corner carries its own bone weights; each triangle one palette block."""

    def __init__(self):
        self.tris = []

    def tri(self, pts, weights, block, inside):
        a, b, c = (np.asarray(p, float) for p in pts)
        if np.dot(np.cross(b - a, c - a), (a + b + c) / 3 - np.asarray(inside, float)) < 0:
            b, c = c, b
            weights = (weights[0], weights[2], weights[1])
        self.tris.append(((a, b, c), weights, block))

    def quad(self, pts, weights, block, inside):
        self.tri((pts[0], pts[1], pts[2]), (weights[0], weights[1], weights[2]), block, inside)
        self.tri((pts[0], pts[2], pts[3]), (weights[0], weights[2], weights[3]), block, inside)

    def mirrored(self):
        """Adds a copy of every left-side triangle on the right: X flips and _L bones become _R."""
        for (a, b, c), ws, block in list(self.tris):
            if max(p[0] for p in (a, b, c)) >= -1e-6:
                continue
            flip = np.array([-1.0, 1.0, 1.0])
            ws = tuple({mirror_name(k): v for k, v in w.items()} for w in ws)
            self.tris.append(((c * flip, b * flip, a * flip), (ws[2], ws[1], ws[0]), block))


def frame(axis):
    """Two unit vectors across an axis. For a vertical axis they are X and Z, so a flat side faces forward."""
    d = np.asarray(axis, float) / np.linalg.norm(axis)
    ref = np.array([0.0, 0.0, 1.0]) if abs(d[2]) < 0.9 else np.array([0.0, 1.0, 0.0])
    v = ref - d * np.dot(ref, d)
    v /= np.linalg.norm(v)
    return np.cross(v, d), v


def loft(body, rings, sides, axis, block="skin", caps=(True, True)):
    """A tube through rings of (centre, radius across, radius front-to-back, weights). block may be a function of the
    triangle's centre."""
    u, v = frame(axis)
    off = math.pi / 2 - math.pi / sides
    loops = []
    for c, ru, rv, w in rings:
        c = np.asarray(c, float)
        loops.append([c + ru * math.cos(off + 2 * math.pi * k / sides) * u +
                      rv * math.sin(off + 2 * math.pi * k / sides) * v for k in range(sides)])

    def pick(pts):
        return block(np.mean(pts, axis=0)) if callable(block) else block

    for i in range(len(rings) - 1):
        inside = (np.asarray(rings[i][0], float) + np.asarray(rings[i + 1][0], float)) / 2
        wa, wb = rings[i][3], rings[i + 1][3]
        for k in range(sides):
            k2 = (k + 1) % sides
            pts = (loops[i][k], loops[i][k2], loops[i + 1][k2], loops[i + 1][k])
            body.quad(pts, (wa, wa, wb, wb), pick(pts), inside)
    for end, nxt, on in ((0, 1, caps[0]), (-1, -2, caps[1])):
        if not on:
            continue
        c = np.asarray(rings[end][0], float)
        inside = c + (np.asarray(rings[nxt][0], float) - c) * 0.5
        for k in range(sides):
            pts = (c, loops[end][k], loops[end][(k + 1) % sides])
            body.tri(pts, (rings[end][3],) * 3, pick(pts), inside)


def segment(body, p0, p1, r0, r1, w0, w1, sides=4, block="skin"):
    """A short tapered tube from p0 to p1, for fingers and thumbs."""
    loft(body, [(p0, r0[0], r0[1], w0), (p1, r1[0], r1[1], w1)], sides, np.subtract(p1, p0), block)


def block_hex(body, corners, weights, block="skin"):
    """Eight corners: four on the bottom, then the four above them in the same order."""
    c = np.asarray(corners, float)
    inside = c.mean(axis=0)
    for f in ((0, 1, 2, 3), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)):
        body.quad([c[i] for i in f], (weights,) * 4, block, inside)


def box(body, centre, half, weights, block="skin"):
    x, y, z = centre
    hx, hy, hz = half
    block_hex(body, [(x - hx, y - hy, z - hz), (x + hx, y - hy, z - hz), (x + hx, y - hy, z + hz), (x - hx, y - hy, z + hz),
                     (x - hx, y + hy, z - hz), (x + hx, y + hy, z - hz), (x + hx, y + hy, z + hz), (x - hx, y + hy, z + hz)],
              weights, block)


def W(**w):
    """Bone weights by bone name."""
    return w


# Shorts run from the waist down to a hem just above mid-thigh.
WAIST, HEM = 0.975, 0.716


def make_body():
    body = Body()

    # Torso: hips to shoulders, eight sides.
    loft(body, [
        ((0, 0.78, 0.0), 0.11, 0.08, W(Hips=1)),
        ((0, 0.86, 0.0), 0.155, 0.1, W(Hips=1)),
        ((0, 0.97, 0.0), 0.145, 0.095, W(Hips=0.4, Spine_01=0.6)),
        ((0, 1.08, 0.005), 0.145, 0.098, W(Spine_01=0.6, Spine_02=0.4)),
        ((0, 1.2, 0.01), 0.16, 0.11, W(Spine_02=0.7, Spine_03=0.3)),
        ((0, 1.32, 0.005), 0.185, 0.115, W(Spine_03=1)),
        ((0, 1.41, -0.01), 0.17, 0.095, W(Spine_03=1)),
        ((0, 1.46, -0.02), 0.1, 0.07, W(Spine_03=0.5, Neck=0.5)),
    ], 8, (0, 1, 0), block=lambda c: "shorts" if c[1] < WAIST else "skin")

    # Neck.
    loft(body, [
        ((0, 1.4, -0.02), 0.062, 0.058, W(Spine_03=1)),
        ((0, 1.48, -0.015), 0.056, 0.056, W(Neck=1)),
        ((0, 1.56, 0.0), 0.058, 0.06, W(Neck=0.5, Head=0.5)),
        ((0, 1.59, 0.0), 0.058, 0.06, W(Head=1)),
    ], 6, (0, 1, 0))

    # Head: a faceted egg. The lower front is the beard (skin-coloured on the clean-shaven variant).
    head = W(Head=1)
    loft(body, [
        ((0, 1.545, 0.0), 0.055, 0.06, head),
        ((0, 1.59, 0.015), 0.085, 0.095, head),
        ((0, 1.645, 0.01), 0.098, 0.105, head),
        ((0, 1.705, 0.0), 0.1, 0.11, head),
        ((0, 1.765, -0.01), 0.088, 0.1, head),
        ((0, 1.8, -0.01), 0.05, 0.06, head),
    ], 8, (0, 1, 0), block=lambda c: "beard" if c[1] < 1.64 and c[2] > -0.03 else "skin")

    # Face: eyes and brows use the dark block; nose and ears are skin.
    box(body, (-0.033, 1.675, 0.103), (0.012, 0.011, 0.008), head, "eyes")
    box(body, (-0.035, 1.708, 0.103), (0.022, 0.006, 0.009), head, "eyes")
    nose = [(-0.016, 1.635, 0.1), (0.016, 1.635, 0.1), (0.016, 1.635, 0.135), (-0.016, 1.635, 0.135),
            (-0.01, 1.68, 0.1), (0.01, 1.68, 0.1), (0.008, 1.672, 0.112), (-0.008, 1.672, 0.112)]
    block_hex(body, nose, head)
    box(body, (-0.1, 1.665, -0.005), (0.012, 0.028, 0.022), head)

    # Left arm: shoulder to wrist, six sides.
    loft(body, [
        ((-0.13, 1.39, -0.03), 0.06, 0.06, W(Clavicle_L=0.7, Shoulder_L=0.3)),
        ((-0.2, 1.385, -0.03), 0.072, 0.07, W(Clavicle_L=0.3, Shoulder_L=0.7)),
        ((-0.3, 1.38, -0.035), 0.062, 0.06, W(Shoulder_L=1)),
        ((-0.44, 1.375, -0.04), 0.05, 0.05, W(Shoulder_L=1)),
        ((-0.52, 1.37, -0.04), 0.045, 0.045, W(Shoulder_L=0.5, Elbow_L=0.5)),
        ((-0.6, 1.37, -0.04), 0.05, 0.052, W(Elbow_L=1)),
        ((-0.72, 1.37, -0.035), 0.04, 0.045, W(Elbow_L=1)),
        ((-0.79, 1.37, -0.03), 0.03, 0.04, W(Elbow_L=0.5, Hand_L=0.5)),
    ], 6, (-1, 0, 0))

    # Left hand: a palm, two finger blocks (they curl into a fist) and a two-part thumb.
    box(body, (-0.835, 1.37, -0.03), (0.05, 0.019, 0.042), W(Hand_L=1))
    segment(body, (-0.88, 1.37, -0.03), (-0.94, 1.37, -0.03), (0.024, 0.055), (0.022, 0.055),
            W(Finger_01_L=1), W(Finger_01_L=1))
    segment(body, (-0.94, 1.37, -0.03), (-0.985, 1.367, -0.03), (0.022, 0.055), (0.018, 0.05),
            W(Finger_02_L=1), W(Finger_02_L=1))
    segment(body, (-0.82, 1.36, 0.0), (-0.85, 1.35, 0.035), (0.026, 0.026), (0.024, 0.024),
            W(Thumb_01_L=1), W(Thumb_02_L=1))
    segment(body, (-0.85, 1.35, 0.035), (-0.89, 1.344, 0.065), (0.024, 0.024), (0.018, 0.018),
            W(Thumb_02_L=1), W(Thumb_03_L=1))

    # Left leg: hip to ankle, six sides. A step in the radius at the hem gives the shorts an edge.
    loft(body, [
        ((-0.09, 0.92, -0.02), 0.085, 0.09, W(Hips=0.5, UpperLeg_L=0.5)),
        ((-0.1, 0.8, -0.015), 0.09, 0.094, W(UpperLeg_L=1)),
        ((-0.103, 0.72, -0.01), 0.09, 0.092, W(UpperLeg_L=1)),
        ((-0.104, 0.715, -0.01), 0.072, 0.076, W(UpperLeg_L=1)),
        ((-0.107, 0.58, -0.01), 0.063, 0.068, W(UpperLeg_L=1)),
        ((-0.11, 0.46, -0.005), 0.052, 0.056, W(UpperLeg_L=0.5, LowerLeg_L=0.5)),
        ((-0.11, 0.36, -0.02), 0.056, 0.062, W(LowerLeg_L=1)),
        ((-0.11, 0.2, -0.025), 0.042, 0.045, W(LowerLeg_L=1)),
        ((-0.11, 0.09, -0.03), 0.035, 0.038, W(LowerLeg_L=0.5, Ankle_L=0.5)),
    ], 6, (0, -1, 0), block=lambda c: "shorts" if c[1] >= HEM else "skin")

    # Left foot: a wedge from heel to ball, then the toes.
    x = -0.11
    block_hex(body, [(x - 0.04, 0, -0.07), (x + 0.04, 0, -0.07), (x + 0.048, 0, 0.09), (x - 0.048, 0, 0.09),
                     (x - 0.036, 0.1, -0.06), (x + 0.036, 0.1, -0.06), (x + 0.044, 0.05, 0.09),
                     (x - 0.044, 0.05, 0.09)], W(Ankle_L=1))
    block_hex(body, [(x - 0.048, 0, 0.09), (x + 0.048, 0, 0.09), (x + 0.044, 0, 0.15), (x - 0.044, 0, 0.15),
                     (x - 0.044, 0.05, 0.09), (x + 0.044, 0.05, 0.09), (x + 0.04, 0.03, 0.15),
                     (x - 0.04, 0.03, 0.15)], W(Ball_L=1))

    body.mirrored()
    return body


def build_mesh(body, bones):
    """One skinned mesh. Every triangle keeps its own three corners so the faces shade flat."""
    n = len(body.tris) * 3
    pos, nrm, uv = np.zeros((n, 3)), np.zeros((n, 3)), np.zeros((n, 2))
    weights = np.zeros((n, len(bones)))
    for t, ((a, b, c), ws, block) in enumerate(body.tris):
        f = np.cross(b - a, c - a)
        f /= np.linalg.norm(f)
        for k, (p, w) in enumerate(zip((a, b, c), ws)):
            i = t * 3 + k
            pos[i], nrm[i], uv[i] = p, f, BLOCK_UV[block]
            for bone, value in w.items():
                weights[i, bones.index(bone)] = value
    top = np.argsort(-weights, axis=1)[:, :4]
    tw = np.take_along_axis(weights, top, axis=1)
    tw = tw / tw.sum(axis=1, keepdims=True)
    return {"pos": pos, "nrm": nrm, "uv": uv, "bi": top.astype(np.uint16), "bw": tw.astype(np.float32),
            "idx": np.arange(n, dtype=np.int64), "tex": 0}

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
    def __init__(self):
        self.bones, self.parent, self.rest = skeleton()

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


FINGERS = ["Finger_01", "Finger_02"]


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


def build(out):
    rig = Rig()
    mesh = build_mesh(make_body(), rig.bones)
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
        "baker": "make_dude_bro.py (hand-written example, not TJBake)",
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
    img = render(scene_tris(rig, mesh, pose), texs, eye=(-0.9, 1.75, 2.6), target=(0, 1.25, 0), size=(1024, 1536), fov=28,
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
    if not args or args[0].startswith("--"):
        print(__doc__)
        sys.exit(1)
    out = args[0]
    rig, mesh, poses, table = build(out)
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
