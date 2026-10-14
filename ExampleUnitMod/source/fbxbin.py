"""Minimal binary FBX reader (versions 6.1 to 7.x): returns a tree of (name, props, children)."""
import struct
import zlib

import numpy as np


class Node:
    __slots__ = ("name", "props", "children")

    def __init__(self, name, props, children):
        self.name, self.props, self.children = name, props, children

    def find(self, name):
        for c in self.children:
            if c.name == name:
                return c
        return None

    def findall(self, name):
        return [c for c in self.children if c.name == name]

    def __repr__(self):
        return f"Node({self.name}, {[p if not isinstance(p, np.ndarray) else f'array{p.shape}' for p in self.props][:4]}, {len(self.children)} children)"


ARRAY = {b"f": "<f4", b"d": "<f8", b"l": "<i8", b"i": "<i4", b"b": "u1"}


def _prop(b, o):
    t = b[o:o + 1]
    o += 1
    if t == b"Y":
        return struct.unpack_from("<h", b, o)[0], o + 2
    if t == b"C":
        return b[o] != 0, o + 1
    if t == b"I":
        return struct.unpack_from("<i", b, o)[0], o + 4
    if t == b"F":
        return struct.unpack_from("<f", b, o)[0], o + 4
    if t == b"D":
        return struct.unpack_from("<d", b, o)[0], o + 8
    if t == b"L":
        return struct.unpack_from("<q", b, o)[0], o + 8
    if t in (b"S", b"R"):
        n = struct.unpack_from("<I", b, o)[0]
        raw = bytes(b[o + 4:o + 4 + n])
        return (raw.decode("utf-8", "replace") if t == b"S" else raw), o + 4 + n
    if t in ARRAY:
        count, enc, clen = struct.unpack_from("<III", b, o)
        o += 12
        raw = bytes(b[o:o + clen])
        if enc == 1:
            raw = zlib.decompress(raw)
        return np.frombuffer(raw, ARRAY[t], count).copy(), o + clen
    raise ValueError(f"unknown property type {t!r} at {o - 1}")


def _node(b, o, wide):
    if wide:
        end, nprops, plen = struct.unpack_from("<QQQ", b, o)
        o += 24
    else:
        end, nprops, plen = struct.unpack_from("<III", b, o)
        o += 12
    nlen = b[o]
    o += 1
    if end == 0:
        return None, o + nlen
    name = bytes(b[o:o + nlen]).decode("ascii")
    o += nlen
    props = []
    for _ in range(nprops):
        p, o = _prop(b, o)
        props.append(p)
    children = []
    sentinel = 25 if wide else 13
    while o < end - sentinel or (o < end and end - o != sentinel):
        child, o = _node(b, o, wide)
        if child is None:
            break
        children.append(child)
    return Node(name, props, children), end


def read(path):
    b = memoryview(open(path, "rb").read())
    if bytes(b[:20]) != b"Kaydara FBX Binary  ":
        raise ValueError("not a binary FBX")
    version = struct.unpack_from("<I", b, 23)[0]
    wide = version >= 7500
    o = 27
    top = []
    while o < len(b):
        n, o = _node(b, o, wide)
        if n is None:
            break
        top.append(n)
    return version, Node("root", [], top)


def arr(node, dtype=float):
    """A node's values as one numpy array, whether stored as a packed array (7.x) or as single values (6.1)."""
    if node is None:
        return None
    if len(node.props) == 1 and isinstance(node.props[0], np.ndarray):
        return node.props[0].astype(dtype)
    return np.array(node.props, dtype)
