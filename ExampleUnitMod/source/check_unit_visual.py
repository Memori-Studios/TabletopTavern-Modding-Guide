"""
Checks a unit visual folder the way Tabletop Tavern does before it uses it.

Usage:
    python check_unit_visual.py <path to unit_visuals/<UnitName>> [--shoots] [--swaps-bow-for-sword]

  --shoots               the unit is Ranged, Hybrid or a Mage, so it needs slots 0 to 14
  --swaps-bow-for-sword  the game's own unit hides its bow in melee, so every variant needs one 'bow' and one 'sword'

Prints every problem it finds and exits with 1 if there is one. A folder that passes here can still be refused in game
for a reason only the game knows (an unknown unit name, artillery, a unit with no rider shipping one), so read the
game's log too (see the README).

Pure Python 3.9+, no packages needed.
"""

import json
import os
import struct
import sys

ROLES = ("prop", "bow", "sword", "shield", "saddle")
MAX_BONES, MAX_FRAMES = 5461, 16384
MAX_ANIM, MAX_MESH, MAX_FOLDER = 256 << 20, 64 << 20, 512 << 20


class Problem(Exception):
    pass


def plain_file(folder, name):
    if not name or ".." in name or "/" in name or "\\" in name:
        raise Problem(f"'{name}' is not a plain file name in the folder")
    if not os.path.isfile(os.path.join(folder, name)):
        raise Problem(f"{name} is missing")


def check_manifest(j, folder):
    if j.get("format", 1) != 1:
        raise Problem(f"unit.json format {j.get('format')} is not 1")
    kind = j.get("kind", "unit")
    rider = kind == "rider"
    if kind not in ("unit", "rider"):
        raise Problem(f"kind '{kind}' is not unit or rider")
    if j.get("frameRate", 30) not in (24, 30, 60):
        raise Problem(f"frameRate {j.get('frameRate')} is not 24, 30 or 60")
    bones = (j.get("skeleton") or {}).get("boneCount", 0)
    if not 1 <= bones <= MAX_BONES:
        raise Problem("skeleton.boneCount is outside 1 to 5461")
    slots = j.get("slots") or []
    need = 3 if rider else 13
    if len(slots) < need:
        raise Problem(f"{len(slots)} slots, at least {need} needed")
    for i, s in enumerate(slots):
        if s.get("id", 0) != i:
            raise Problem(f"slot ids must be contiguous from 0; entry {i} has id {s.get('id')}")
        if s.get("loop") and s.get("returnToIdle"):
            raise Problem(f"slot {i} ({s.get('name')}) is both loop and returnToIdle")
        if s.get("count", 0) < 2:
            raise Problem(f"slot {i} ({s.get('name')}) has fewer than 2 frames")
    mats = j.get("materials") or []
    if not mats:
        raise Problem("materials is empty")
    variants = j.get("variants") or []
    if not 1 <= len(variants) <= 3:
        raise Problem("variants must hold 1 to 3 entries")
    lods = len(variants[0].get("lods") or [])
    if not 1 <= lods <= 3:
        raise Problem("each variant needs 1 to 3 LODs")
    if rider and lods != 1:
        raise Problem("a rider has exactly one LOD")
    sw = j.get("lodSwitch") or []
    if len(sw) != lods - 1:
        raise Problem(f"lodSwitch needs {lods - 1} entries for {lods} LODs")
    for i, h in enumerate(sw):
        if h <= 0 or h >= 1 or (i > 0 and h >= sw[i - 1]):
            raise Problem("lodSwitch values must be descending fractions in (0, 1)")
    anchors = j.get("anchors") or []
    if len(set(anchors)) != len(anchors):
        raise Problem("anchor names repeat")
    for v in variants:
        if len(v.get("lods") or []) != lods:
            raise Problem("every variant must have the same LOD count")
        for lod in v["lods"]:
            if not lod.get("meshes"):
                raise Problem("a LOD lists no mesh")
            for m in lod["meshes"]:
                plain_file(folder, m.get("file", ""))
                if not 0 <= m.get("material", 0) < len(mats):
                    raise Problem(f"{m.get('file')} uses material {m.get('material')} of {len(mats)}")
        saddles = 0
        for a in v.get("attachments") or []:
            plain_file(folder, a.get("file", ""))
            if not 0 <= a.get("material", 0) < len(mats):
                raise Problem(f"{a.get('file')} uses material {a.get('material')} of {len(mats)}")
            if a.get("anchor") not in anchors:
                raise Problem(f"attachment {a.get('file')} names unknown anchor '{a.get('anchor')}'")
            if a.get("role", "prop") not in ROLES:
                raise Problem(f"attachment {a.get('file')} has unknown role '{a.get('role')}'")
            if a.get("role") == "saddle":
                saddles += 1
        if saddles > 1:
            raise Problem("more than one attachment has role 'saddle'")
        if not rider and j.get("rider") and saddles == 0:
            raise Problem("a unit with a rider needs a saddle attachment on every variant")
    for m in mats:
        for key in ("baseColor", "normal", "emission"):
            name = m.get(key) or ""
            if key == "baseColor" and not name:
                raise Problem(f"material '{m.get('name')}' has no baseColor texture")
            if name.startswith("asset:"):
                raise Problem(f"'{name}' names a game asset, which only the game's own visuals may use")
            if name:
                plain_file(folder, name)
    if not rider and j.get("rider") and not os.path.isfile(os.path.join(folder, j["rider"], "unit.json")):
        raise Problem("rider folder has no unit.json")
    plain_file(folder, "anim.bin")
    if anchors:
        plain_file(folder, "anchors.bin")


def read(folder, name, limit):
    path = os.path.join(folder, name)
    if os.path.getsize(path) > limit:
        raise Problem(f"{name} is over {limit >> 20} MB")
    with open(path, "rb") as f:
        return f.read()


def check_anim(b):
    if len(b) < 32 or b[:4] != b"TJBA":
        raise Problem("anim.bin does not start with TJBA")
    ver, bones, frames = struct.unpack_from("<III", b, 4)
    if ver != 1:
        raise Problem(f"anim.bin version {ver} is not 1")
    if not 1 <= bones <= MAX_BONES or not 2 <= frames <= MAX_FRAMES:
        raise Problem(f"anim.bin has {bones} bones and {frames} frames, outside the limits")
    if len(b) != 32 + frames * bones * 24:
        raise Problem(f"anim.bin is {len(b)} bytes, expected {32 + frames * bones * 24}")
    return bones, frames


def check_anchors(b):
    if len(b) < 32 or b[:4] != b"TJBK":
        raise Problem("anchors.bin does not start with TJBK")
    ver, count, frames = struct.unpack_from("<III", b, 4)
    if ver != 1:
        raise Problem(f"anchors.bin version {ver} is not 1")
    if len(b) != 32 + frames * count * 48:
        raise Problem(f"anchors.bin is {len(b)} bytes, expected {32 + frames * count * 48}")
    return count, frames


def align(o):
    return (o + 15) & ~15


def check_mesh(b, name, bones, skinned_expected):
    if len(b) < 48 or b[:4] != b"TJBM":
        raise Problem(f"{name} does not start with TJBM")
    ver, vc, ic, flags = struct.unpack_from("<IIII", b, 4)
    if ver != 1:
        raise Problem(f"{name} version {ver} is not 1")
    if not 3 <= vc <= 1_000_000:
        raise Problem(f"{name} vertexCount {vc} is outside 3 to 1000000")
    if ic < 3 or ic % 3 or ic > 6_000_000:
        raise Problem(f"{name} indexCount {ic} is not a multiple of 3 in range")
    sub = struct.unpack_from("<I", b, 44)[0]
    if not 1 <= sub <= 64:
        raise Problem(f"{name} submeshCount {sub} is outside 1 to 64")
    o = 48
    for i in range(sub):
        start, count = struct.unpack_from("<II", b, o)
        if count < 3 or start + count > ic:
            raise Problem(f"{name} submesh {i} runs past the index buffer")
        o += 8

    def need(o, n, what):
        if o + n > len(b):
            raise Problem(f"{name} ends inside its {what}")

    o = align(o); need(o, vc * 12, "positions"); o += vc * 12
    if flags & 1:
        o = align(o); need(o, vc * 12, "normals"); o += vc * 12
    if flags & 2:
        o = align(o); need(o, vc * 16, "tangents"); o += vc * 16
    if flags & 4:
        o = align(o); need(o, vc * 8, "uv0"); o += vc * 8
    skinned = bool(flags & 8)
    if skinned != skinned_expected:
        raise Problem(f"{name} is {'skinned' if skinned else 'rigid'}, expected {'skinned' if skinned_expected else 'rigid'}")
    if skinned:
        o = align(o); need(o, vc * 8, "bone indices")
        top = max(struct.unpack_from(f"<{vc * 4}H", b, o))
        if top >= bones:
            raise Problem(f"{name} references bone {top} of {bones}")
        o += vc * 8
        o = align(o); need(o, vc * 16, "bone weights")
        w = struct.unpack_from(f"<{vc * 4}f", b, o)
        for v in range(vc):
            s = sum(w[v * 4:v * 4 + 4])
            if abs(s - 1) > 1 / 255:
                raise Problem(f"{name} vertex {v} weights sum to {s:.3f}, not 1")
        o += vc * 16
    o = align(o)
    wide = bool(flags & 16)
    need(o, ic * (4 if wide else 2), "indices")
    idx = struct.unpack_from(f"<{ic}{'I' if wide else 'H'}", b, o)
    if max(idx) >= vc:
        raise Problem(f"{name} has an index of {max(idx)} with {vc} vertices")


def check_png(folder, name, exact=None):
    with open(os.path.join(folder, name), "rb") as f:
        head = f.read(24)
    if head[:8] != b"\x89PNG\r\n\x1a\n":
        raise Problem(f"{name} is not a PNG")
    w, h = struct.unpack(">II", head[16:24])
    if w > 4096 or h > 4096:
        raise Problem(f"{name} is larger than 4096 on a side")
    if exact and (w, h) != exact:
        raise Problem(f"{name} is {w}x{h}, it must be {exact[0]}x{exact[1]}")


def check_folder(folder, shoots, swaps, is_rider=False):
    total = sum(os.path.getsize(os.path.join(r, f)) for r, _, fs in os.walk(folder) for f in fs)
    if total > MAX_FOLDER:
        raise Problem(f"folder is {total >> 20} MB, the limit is 512 MB")
    path = os.path.join(folder, "unit.json")
    if not os.path.isfile(path):
        raise Problem("unit.json is missing")
    with open(path, encoding="utf-8") as f:
        j = json.load(f)
    check_manifest(j, folder)
    if is_rider != (j.get("kind", "unit") == "rider"):
        raise Problem(f"kind is '{j.get('kind')}', expected '{'rider' if is_rider else 'unit'}'")
    if not is_rider:
        name = os.path.basename(os.path.normpath(folder))
        if j.get("unitName") and j["unitName"] != name:
            raise Problem(f"unitName '{j['unitName']}' does not match the folder name '{name}'")
        if shoots and len(j["slots"]) < 15:
            raise Problem(f"a unit that shoots or casts needs slots 0 to 14, this has {len(j['slots'])}")
    bones, frames = check_anim(read(folder, "anim.bin", MAX_ANIM))
    if bones != j["skeleton"]["boneCount"]:
        raise Problem(f"anim.bin has {bones} bones, unit.json says {j['skeleton']['boneCount']}")
    for s in j["slots"]:
        if s.get("start", 0) < 0 or s["start"] + s["count"] > frames:
            raise Problem(f"slot {s['id']} ({s.get('name')}) frames {s['start']}+{s['count']} fall outside anim.bin's {frames}")
    if j.get("anchors"):
        count, af = check_anchors(read(folder, "anchors.bin", MAX_ANIM))
        if count != len(j["anchors"]):
            raise Problem(f"anchors.bin has {count} anchors, unit.json lists {len(j['anchors'])}")
        if af != frames:
            raise Problem(f"anchors.bin has {af} frames, anim.bin {frames}")
    for m in j["materials"]:
        for key in ("baseColor", "normal", "emission"):
            if m.get(key):
                check_png(folder, m[key])
    for v in j["variants"]:
        for lod in v["lods"]:
            for m in lod["meshes"]:
                check_mesh(read(folder, m["file"], MAX_MESH), m["file"], bones, True)
        roles = [a.get("role", "prop") for a in v.get("attachments") or []]
        for a in v.get("attachments") or []:
            check_mesh(read(folder, a["file"], MAX_MESH), a["file"], bones, False)
        if not is_rider and swaps != ("bow" in roles and "sword" in roles):
            raise Problem("the game's unit swaps bow for sword, so every variant needs a 'bow' and a 'sword'" if swaps
                          else "the game's unit has no bow and sword pair, so no variant may have both")
    if not is_rider and os.path.isfile(os.path.join(folder, "icon.png")):
        check_png(folder, "icon.png", (256, 256))
    if not is_rider and j.get("rider"):
        check_folder(os.path.join(folder, j["rider"]), False, False, is_rider=True)
    return j, frames


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not args:
        print(__doc__)
        sys.exit(2)
    folder = args[0]
    try:
        j, frames = check_folder(folder, "--shoots" in sys.argv, "--swaps-bow-for-sword" in sys.argv)
    except Problem as p:
        print(f"REFUSED {folder}: {p}")
        sys.exit(1)
    except (OSError, ValueError, KeyError, struct.error) as e:
        print(f"REFUSED {folder}: could not read it ({e})")
        sys.exit(1)
    print(f"OK {j.get('unitName') or folder}: {j['skeleton']['boneCount']} bones, {frames} frames, "
          f"{len(j['slots'])} slots, {len(j['variants'])} variant(s), {len(j['materials'])} material(s).")


if __name__ == "__main__":
    main()
