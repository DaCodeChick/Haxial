#!/usr/bin/env python3
"""Batch G — field2/field0/ext correlation: which parts carry non-zero
field2, and what are they (part index, dims, flags, neighbors)?

Full mode: aggregate byte patterns across the corpus + built-in.
File mode (arg): per-part detail for one .hap name substring.
"""
import os, struct, sys
from collections import Counter

ROOT = "/Users/schala/Documents/GitHub/Haxial"
CORPUS = os.path.join(ROOT, "refs", "appearances")
EXE = "/Users/schala/Downloads/AppearanceEdit.exe"

def bswap32(v): return struct.unpack(">I", struct.pack("<I", v))[0]
def bswap16(v): return struct.unpack(">H", struct.pack("<H", v))[0]
def d_off(va): return 0x5DA00 + (va - 0x45F000)

def hap_c(data):
    if data[:4] != b"%HAP": return None
    coff = bswap32(struct.unpack_from("<I", data, 0x34)[0])
    csize = bswap32(struct.unpack_from("<I", data, 0x38)[0])
    if csize == 0 or coff + csize > len(data): return None
    return coff, csize

def parts_of(c):
    out = []
    partoff = c[0x40:0x40 + 512*4]
    for i in range(512):
        off = bswap32(struct.unpack_from("<I", partoff, i*4)[0])
        if off == 0: continue
        w = bswap16(struct.unpack_from("<H", c, off)[0])
        h = bswap16(struct.unpack_from("<H", c, off+2)[0])
        flags = c[off+4]
        bpp = c[off+5]
        f0 = bswap32(struct.unpack_from("<I", c, off+8)[0])
        raw = c[off+0x10:off+0x14]
        f2 = bswap32(struct.unpack("<I", raw)[0])
        out.append((i, off, w, h, flags, bpp, f0, f2, raw))
    return out

def main(which=None):
    with open(EXE, "rb") as f: exe = f.read()
    blob = exe[d_off(0x4683D4):d_off(0x4683D4) + 0x112A0]
    srcs = [("builtin", blob)]
    for fn in sorted(os.listdir(CORPUS)):
        if not fn.endswith(".hap"): continue
        if which and which not in fn: continue
        with open(os.path.join(CORPUS, fn), "rb") as f: data = f.read()
        srcs.append((fn, data))
    agg_pat = Counter()
    agg_ids = Counter()
    for name, data in srcs:
        cs = hap_c(data)
        if not cs: continue
        coff, csize = cs
        c = data[coff:coff + csize]
        if len(c) < 0x840: continue
        rows = parts_of(c)
        nz2 = [r for r in rows if r[7] != 0]
        if which:
            print(f"== {name}: {len(rows)} parts, {len(nz2)} with non-zero field2")
            for r in nz2:
                i, off, w, h, flags, bpp, f0, f2, raw = r
                print(f"  part {i:3d} off {off:#07x} {w:3d}x{h:<3d} "
                      f"flags={flags:#04x} bpp={bpp} f0={f0:#010x} "
                      f"f2={f2:#010x} raw={raw.hex()}")
            if nz2:
                print(f"  field2-nonzero part indices: "
                      f"{[r[0] for r in nz2]}")
            continue
        for r in nz2:
            agg_pat[r[8][:3]] += 1
            agg_ids[r[0]] += 1
    print(f"corpus aggregate: field2-nonzero parts across all sources")
    print(f"  top byte patterns (b0 b1 b2 of u32BE @+0x10):")
    for k, v in agg_pat.most_common(20):
        print(f"    {k.hex()}: {v}")
    print(f"  part index distribution (top 20):")
    for k, v in agg_ids.most_common(20):
        print(f"    part {k}: {v}")

if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else None)
