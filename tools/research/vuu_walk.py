#!/usr/bin/env python3
"""Walk a built-in %VUU window payload: reconstruct the widget record tree.

Record model (code-verified, doc 17 §3):
  fixed 40 bytes:
    +0x00 class 4cc (ASCII spelling)
    +0x04 x  i16BE   +0x06 y  i16BE   +0x08 w  u16BE   +0x0A h  u16BE
    +0x0C instance 4cc (ASCII spelling; zero = none)
    +0x10 flags u32 (BE reading)
    +0x14 size  u32BE  = payload bytes after the fixed 40 (0 = none)
    +0x18 f18 u32   +0x1C f1C u32
    +0x20 mode u16BE   +0x22 b22   +0x23 b23   +0x24 pad[2]
    +0x26 childCount u16BE   +0x27 pad1
  then `size` payload bytes, then childCount records.
  (VWIN root: the 44-byte payload is the window-own block, decoded by
   vuuPayloadParse.)

Usage:
  vuu_walk.py <payload_va_hex> <size_int> [inst_table_va_hex] [inst_count]
  e.g. vuu_walk.py 0x4621A0 0x1328 0x45F57C 29
"""
import struct, sys, os

EXE = os.environ.get("HAP_EXE", "/Users/schala/Downloads/AppearanceEdit.exe")
# PE section raw offsets (verified): name -> (va, vsize, raw)
SECS = {
    ".text":  (0x401000, 0x51B30, 0x400),
    ".rdata": (0x453000, 0x8B84,  0x52000),
    ".exc":   (0x45C000, 0x2C7C,  0x5AC00),
    ".data":  (0x45F000, 0x2AE5C, 0x5DA00),
    ".rsrc":  (0x48A000, 0x1FFC,  0x88A00),
}

def va2raw(va):
    for name, (sva, vsize, raw) in SECS.items():
        if sva <= va < sva + vsize:
            return raw + (va - sva)
    raise ValueError(f"VA {va:#x} outside known sections")

def main():
    payload_va = int(sys.argv[1], 16)
    size = int(sys.argv[2], 0)
    inst_table_va = int(sys.argv[3], 16) if len(sys.argv) > 3 else None
    inst_count = int(sys.argv[4], 0) if len(sys.argv) > 4 else 0

    data = open(EXE, "rb").read()
    raw = va2raw(payload_va)
    end = raw + size
    pos = raw + 8  # skip "%VUU" tag + 4 pad bytes; first record (VWIN) at +8
    out = []
    classes = {}
    instances = []
    rec_count = 0

    def c4(b):
        if b == b"\x00\x00\x00\x00":
            return "-"
        try:
            s = b.decode("ascii")
            if s.isalpha():
                return s
        except UnicodeDecodeError:
            pass
        return b.hex()

    def walk(d, depth, base_va):
        nonlocal pos, rec_count
        while True:
            if pos + 40 > end:
                out.append(f"{'  '*depth}!! TRUNCATED at rel {pos-raw:#x} (want 40 B, have {end-pos})")
                return
            cls = d[pos:pos+4]
            x, y, w, h = struct.unpack_from(">hhhh", d, pos + 4)
            inst = d[pos+0x0C:pos+0x10]
            flags, sz = struct.unpack_from(">II", d, pos + 0x10)
            f18, f1c = struct.unpack_from(">II", d, pos + 0x18)
            mode, child = struct.unpack_from(">HH", d, pos + 0x20)
            b22, b23 = d[pos+0x22], d[pos+0x23]
            rel = pos - raw
            rec_count += 1
            classes[cls] = classes.get(cls, 0) + 1
            name = c4(inst)
            if name != "-":
                instances.append((rel, c4(cls), name, mode))
            extra = []
            if f18: extra.append(f"f18={f18:#x}")
            if f1c: extra.append(f"f1c={f1c:#x}")
            if flags: extra.append(f"flags={flags:#x}")
            if b22: extra.append(f"b22={b22:#02x}")
            if b23: extra.append(f"b23={b23:#02x}")
            if mode & ~0x3F: extra.append(f"mode_hi={mode:#x}")
            ex = (" " + " ".join(extra)) if extra else ""
            out.append(f"{'  '*depth}{rel:#06x} {c4(cls):5s} "
                       f"({x:4d},{y:4d} {w:4d}x{h:<4d}) inst={name:5s} "
                       f"sz={sz:4d} mode={mode:#04x} kids={child:2d}{ex}")
            # VWIN window-own payload annotation
            if cls == b"VWIN" and sz == 0x2C:
                pv = pos + 40
                a, b, c_, d_ = struct.unpack_from(">IIII", d, pv)
                u1 = struct.unpack_from(">HHHH", d, pv + 16)
                out.append(f"{'  '*depth}   | window-own 44B: {a:#x} {b:#x} {c_:#x} {d_:#x} "
                           f"{u1[0]:#04x} {u1[1]:#04x} {u1[2]:#04x} {u1[3]:#04x}")
            pos += 40 + sz
            if child:
                walk(d, depth + 1, base_va)
            else:
                return  # leaves end the sibling run? NO -- see below

    # NOTE: childCount==0 means no CHILDREN, not end of siblings. Siblings
    # follow in the stream; the parent's childCount bounds the run. Rewrite:
    def walk_sib(d, depth, n):
        nonlocal pos, rec_count
        for i in range(n):
            if pos + 40 > end:
                out.append(f"{'  '*depth}!! TRUNCATED (child {i}) at rel {pos-raw:#x}")
                return
            cls = d[pos:pos+4]
            x, y, w, h = struct.unpack_from(">hhhh", d, pos + 4)
            inst = d[pos+0x0C:pos+0x10]
            flags, sz = struct.unpack_from(">II", d, pos + 0x10)
            f18, f1c = struct.unpack_from(">II", d, pos + 0x18)
            mode = struct.unpack_from(">H", d, pos + 0x20)[0]
            b22, b23 = d[pos+0x22], d[pos+0x23]
            child = struct.unpack_from(">H", d, pos + 0x26)[0]
            rel = pos - raw
            rec_count += 1
            classes[cls] = classes.get(cls, 0) + 1
            name = c4(inst)
            if name != "-":
                instances.append((rel, c4(cls), name, mode))
            extra = []
            if f18: extra.append(f"f18={f18:#x}")
            if f1c: extra.append(f"f1c={f1c:#x}")
            if flags: extra.append(f"flags={flags:#x}")
            if b22: extra.append(f"b22={b22:#02x}")
            if b23: extra.append(f"b23={b23:#02x}")
            ex = (" " + " ".join(extra)) if extra else ""
            out.append(f"{'  '*depth}{rel:#06x} {c4(cls):5s} "
                       f"({x:4d},{y:4d} {w:4d}x{h:<4d}) inst={name:5s} "
                       f"sz={sz:4d} mode={mode:#04x} kids={child:2d}{ex}")
            if cls == b"VWIN" and sz == 0x2C:
                pv = pos + 40
                a, b, c_, d_ = struct.unpack_from(">IIII", d, pv)
                u1 = struct.unpack_from(">HHHH", d, pv + 16)
                nm = d[pv+24:pv+40]
                nms = nm.split(b"\x00")[0][:16]
                out.append(f"{'  '*depth}   | window-own 44B: {a:#x} {b:#x} {c_:#x} {d_:#x} "
                           f"{u1[0]:#04x} {u1[1]:#04x} {u1[2]:#04x} {u1[3]:#04x} tail={nms!r}")
            # stride: 40 fixed + round4(payload) ; children start there (code: AND 0xfffffffc)
            pos += 40 + ((sz + 3) & ~3)
            if child:
                walk_sib(d, depth + 1, child)

    walk_sib(d if False else data, 0, 1)  # root = 1 record (the VWIN)
    consumed = pos - raw
    out.append("")
    out.append(f"consumed {consumed:#x} / {size:#x} ({'EXACT' if consumed == size else 'MISMATCH'}), "
               f"records={rec_count}")
    out.append("class histogram: " + "  ".join(f"{c4(k)}={v}" for k, v in sorted(classes.items(), key=lambda kv: -kv[1])))
    out.append(f"named instances ({len(instances)}):")
    for rel, cls, name, mode in instances:
        out.append(f"  {rel:#06x} {cls:5s} {name} mode={mode:#04x}")

    if inst_table_va:
        tpos = va2raw(inst_table_va)
        out.append(f"instance table @ {inst_table_va:#x} ({inst_count} entries, 8B each):")
        tbl_names = []
        for i in range(inst_count):
            nme = data[tpos + i*8 : tpos + i*8 + 4]
            ptr = struct.unpack_from("<I", data, tpos + i*8 + 4)[0]
            nm = "-" if nme == b"\x00\x00\x00\x00" else nme[::-1].decode("ascii", "replace")
            tbl_names.append(nm)
            out.append(f"  [{i:2d}] {nm:5s} -> {ptr:#08x}")
        missing = [n for _, _, n, _ in instances if n not in tbl_names]
        unused = [n for n in tbl_names if n != "-" and n not in [x[2] for x in instances]]
        out.append(f"desc-inst not in table: {missing or 'none'}")
        out.append(f"table names unused by tree: {unused or 'none'}")

    print("\n".join(out))

if __name__ == "__main__":
    main()