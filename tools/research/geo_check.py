#!/usr/bin/env python3
"""Validate built-in window geometry records against the code-verified
layout (doc 17 §19, doc 19).

Checks, per %REZ VWIN record:
  1. payload magic/version
  2. VWIN descriptor at +8 (class, geometry, size, childCount)
  3. window-own payload (f, f2, u04, u08, client quad, style, name)
  4. childBase = R + 0x28 + round4(size) actually starts a record
  5. instance table: entry count matches the table-end pointer written by
     the ctor when known, and slots fit within the window object size

Usage: geo_check.py [exe_path]
Layout refs: doc 17 §19 (VWIN root), §3 (descriptor), §19.1 (slots).
"""
import struct, sys, os

EXE = sys.argv[1] if len(sys.argv) > 1 else os.environ.get(
    "HAP_EXE", "/Users/schala/Downloads/AppearanceEdit.exe")

# PE sections (verified): name -> (va, vsize, raw)
SECS = {
    ".text":  (0x401000, 0x51B30, 0x400),
    ".rdata": (0x453000, 0x8B84,  0x52000),
    ".exc":   (0x45C000, 0x2C7C,  0x5AC00),
    ".data":  (0x45F000, 0x2AE5C, 0x5DA00),
    ".rsrc":  (0x48A000, 0x1FFC,  0x88A00),
}

def va2raw(va):
    for sva, vsize, raw in SECS.values():
        if sva <= va < sva + vsize:
            return raw + (va - sva)
    raise ValueError(f"VA {va:#x} outside known sections")

def be16(d, o): return struct.unpack_from(">h", d, o)[0]
def be16u(d, o): return struct.unpack_from(">H", d, o)[0]
def be32(d, o): return struct.unpack_from(">I", d, o)[0]

# ctor-verified window object sizes + instance tables (doc 17 §19)
WIN_INFO = {
    b"prvw": {"objSize": 0xA0,  "table": 0x45F57C, "count": 29},
    b"doku": {"objSize": 0x1C0, "table": 0x45F048, "count": 19},
    b"efik": {"objSize": None,  "table": 0x46440C, "count": 8},
    b"emik": {"objSize": None,  "table": 0x465FB4, "count": 9},
    b"epxm": {"objSize": None,  "table": 0x465A9C, "count": 18},
    b"esik": {"objSize": None,  "table": 0x4640C4, "count": 6},
}

def main():
    d = open(EXE, "rb").read()
    ok = True

    def check(label, cond, detail=""):
        nonlocal ok
        mark = "ok  " if cond else "FAIL"
        if not cond: ok = False
        print(f"  [{mark}] {label}" + (f" — {detail}" if detail else ""))

    # %REZ registry
    rez = va2raw(0x45F830)
    check("%REZ magic", d[rez:rez+4] == b"%REZ")
    count = be32(d, rez + 0x14)
    print(f"records: {count}")

    for i in range(count):
        o = rez + 0x18 + i * 20
        cls = d[o:o+4]
        name = d[o+4:o+8]
        size = be32(d, o + 0x0C)
        payload = 0x45F830 + be32(d, o + 0x10)
        if cls != b"VWIN":
            print(f"[rec {i}] MENU {name.decode()} size={size:#x} (skipped)")
            continue
        print(f"[rec {i}] VWIN {name.decode()} size={size:#x} payload={payload:#x}")
        ro = va2raw(payload)
        check("payload magic %VUU", d[ro:ro+4] == b"%VUU")
        check("payload version 1", be16u(d, ro+4) == 1)
        R = ro + 8
        check("VWIN class @R+0", d[R:R+4] == b"VWIN")
        x, y, w, h = (be16(d, R+4), be16(d, R+6), be16u(d, R+8), be16u(d, R+10))
        print(f"    outer geometry: ({x},{y}) {w}x{h}")
        sz = be32(d, R + 0x14)
        # descriptor 'size' = window-own payload length (NOT the whole %REZ payload)
        check("%REZ payload >= hdr+desc+window-own",
              size >= 0x48 + sz, f"{size:#x} >= {0x48:#x}+{sz:#x}")
        kids = be16u(d, R + 0x26)
        check("childCount == 1", kids == 1)
        wp = R + 0x28
        f, f2 = struct.unpack_from("<HH", d, wp)
        u04, u08 = struct.unpack_from("<II", d, wp+4)
        quad = struct.unpack_from(">HHHH", d, wp+0xC)
        style = d[wp+0x14]
        nlen = d[wp+0x2B]
        title = d[wp+0x2C:wp+0x2C+nlen].decode("latin1")
        print(f"    window-own: f={f:#04x} f2={f2:#04x} u04={u04:#010x} u08={u08:#010x}")
        print(f"    client quad {quad}  style={style}  title={title!r}")
        if quad[0] and quad[1]:
            check("clientW <= outerW", quad[0] <= w, f"{quad[0]} <= {w}")
            check("clientH <= outerH", quad[1] <= h, f"{quad[1]} <= {h}")
        # childBase
        cb = R + 0x28 + ((sz + 3) & ~3)
        cbcls = d[cb:cb+4]
        check("childBase within payload", cb < ro + size)
        check("childBase starts a record",
              len(cbcls) == 4 and all(c.isalpha() for c in cbcls.decode("latin1", "replace")),
              f"childBase={payload + (cb - ro):#x} class={cbcls!r}")
        # instance table
        info = WIN_INFO.get(name)
        if info:
            to = va2raw(info["table"])
            slots = []
            for j in range(info["count"]):
                t, s, p = struct.unpack_from("<IHH", d, to + j*8)
                slots.append(s)
                # name must be 4cc-ish
                nm = d[to+j*8:to+j*8+4]
                if not all(32 <= c < 127 for c in nm):
                    check(f"inst[{j}] name printable", False, repr(nm))
            if info["objSize"]:
                check("slots within object", max(slots) + 4 <= info["objSize"],
                      f"max slot {max(slots):#x}+4 <= {info['objSize']:#x}")
            # table-end pointer (ctor-verified for prvw/doku)
            if name in (b"prvw",):
                check("table end == 0x45F664",
                      info["table"] + info["count"]*8 == 0x45F664)
            if name in (b"doku",):
                check("table end == 0x45F0E0",
                      info["table"] + info["count"]*8 == 0x45F0E0)
            print(f"    inst table: {info['count']} entries, slots "
                  f"{min(slots):#x}..{max(slots):#x}")

    print()
    print("RESULT:", "ALL OK" if ok else "FAILURES PRESENT")
    sys.exit(0 if ok else 1)

if __name__ == "__main__":
    main()
