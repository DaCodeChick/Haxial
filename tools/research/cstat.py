#!/usr/bin/env python3
"""Batch G — C-blob header statistics across the HAP corpus + built-in blob.

Validates the Batch-G header model against raw data:
  +0x00 u16BE w            +0x08 u32BE field0
  +0x02 u16BE h            +0x0C u8 capL
  +0x04 u8 flags           +0x0D u8 capT
  +0x05 u8 bpp             +0x0E u8 capR
  +0x06 u8 palCount-1      +0x0F u8 capB
  +0x07 u8 transIdx        +0x10 u32BE field2
  +0x14..+0x1F ext (if flags & 0x10):
      +0x14 u8x3 gradStart, +0x17 u8 mode, +0x18 u8x3 gradEnd, +0x1B u8 ?,
      +0x1C..+0x1F u8x4 insets (L, T, R, B)
  palette (pal x 4B), then pixels (stride x h), then secondary row
  (rowBytes at bpp = flags low nibble, if mode in {2,4,8}).

Layout confidence vs semantic confidence kept separate: this script checks
LAYOUT consistency (sizes fit, no overlaps) — it does not assert semantics.
"""
import os, sys, struct
from collections import Counter

ROOT = "/Users/schala/Documents/GitHub/Haxial"
CORPUS = os.path.join(ROOT, "refs", "appearances")
EXE = "/Users/schala/Downloads/AppearanceEdit.exe"

def bswap32(v): return struct.unpack(">I", struct.pack("<I", v))[0]
def bswap16(v): return struct.unpack(">H", struct.pack("<H", v))[0]

def d_off(va):  # .data VA -> file offset
    return 0x5DA00 + (va - 0x45F000)

def load_builtin():
    with open(EXE, "rb") as f:
        exe = f.read()
    va = 0x4683D4
    size = 0x112A0
    return exe[d_off(va):d_off(va) + size], "builtin-v2"

def hap_c_section(data):
    """Return (c_off, c_size) from a .hap file, or None."""
    if data[:4] != b"%HAP":
        return None
    ver = bswap16(struct.unpack_from("<H", data, 4)[0])
    if ver not in (1, 2):
        return None
    coff = bswap32(struct.unpack_from("<I", data, 0x34)[0])
    csize = bswap32(struct.unpack_from("<I", data, 0x38)[0])
    if csize == 0 or coff + csize > len(data):
        return None
    return coff, csize

def rowbytes(w, bpp):
    if bpp == 1: return ((w + 0x1F) & ~0x1F) >> 3
    if bpp == 2: return ((w + 0xF) & ~0xF) >> 2
    if bpp == 4: return ((w + 7) & ~7) >> 1
    return (w + 3) & ~3

def analyze_c(c, tag, report):
    """c = C-section bytes. Returns per-file stats dict."""
    st = {"tag": tag, "parts": 0, "bad": 0, "flags": Counter(), "mode248": Counter(),
          "field0": Counter(), "field2": Counter(), "bpp": Counter(),
          "ext": 0, "extmode": Counter(), "size_ok": 0, "overlaps": 0, "shared": 0,
          "span": 0, "tiled": 0, "secondary": Counter()}
    if len(c) < 0x840:
        st["bad"] = 1
        report.append(f"{tag}: C section too small ({len(c)})")
        return st
    partoff = c[0x40:0x40 + 512 * 4]
    spans = []
    for i in range(512):
        off = bswap32(struct.unpack_from("<I", partoff, i * 4)[0])
        if off == 0:
            continue
        if off + 0x14 > len(c):
            st["bad"] += 1
            report.append(f"{tag}: part {i}: off {off:#x} out of bounds")
            continue
        w = bswap16(struct.unpack_from("<H", c, off)[0])
        h = bswap16(struct.unpack_from("<H", c, off + 2)[0])
        flags = c[off + 4]
        bpp = c[off + 5]
        pal = c[off + 6] + 1
        trans = c[off + 7]
        f0 = bswap32(struct.unpack_from("<I", c, off + 8)[0])
        caps = c[off + 0xC:off + 0x10]
        f2 = bswap32(struct.unpack_from("<I", c, off + 0x10)[0])
        ext = flags & 0x10
        if ext and off + 0x20 > len(c):
            st["bad"] += 1
            report.append(f"{tag}: part {i}: ext out of bounds")
            continue
        hdr = 0x20 if ext else 0x14
        rb = rowbytes(w, bpp)
        px = rb * h
        mode = flags & 0xF
        sec = 0
        if mode in (2, 4, 8):
            sec = rowbytes(w, mode)
        total = hdr + pal * 4 + px + sec
        if total > len(c) - off:
            st["bad"] += 1
            report.append(f"{tag}: part {i}: total {total:#x} exceeds section "
                          f"({len(c)-off:#x} left) w={w} h={h} bpp={bpp} pal={pal} "
                          f"flags={flags:#x}")
            continue
        st["size_ok"] += 1
        st["parts"] += 1
        st["flags"][flags] += 1
        st["bpp"][bpp] += 1
        st["field0"][f0] += 1
        st["field2"][f2] += 1
        if ext:
            st["ext"] += 1
            st["extmode"][c[off + 0x17]] += 1
        if mode in (2, 4, 8):
            st["mode248"][mode] += 1
            st["secondary"][mode] += 1
        if flags & 1:
            st["tiled"] += 1
        span = (off, off + total, i)
        spans.append(span)
    spans.sort()
    seen = {}
    for sp in spans:
        seen[(sp[0], sp[1])] = seen.get((sp[0], sp[1]), 0) + 1
    shared = sum(n - 1 for n in seen.values() if n > 1)
    for a, b in zip(spans, spans[1:]):
        if a[0] == b[0]:
            continue  # shared blob, not an overlap
        if a[1] > b[0]:
            st["overlaps"] += 1
            if st["overlaps"] <= 3:
                report.append(f"{tag}: overlap part {a[2]} end {a[1]:#x} > "
                              f"part {b[2]} start {b[0]:#x}")
    st["shared"] = shared
    if spans:
        st["span"] = spans[-1][1]
    return st

def main():
    report = []
    agg = {"parts": 0, "bad": 0, "flags": Counter(), "mode248": Counter(),
           "field0": Counter(), "field2": Counter(), "bpp": Counter(),
           "ext": 0, "extmode": Counter(), "size_ok": 0, "overlaps": 0,
           "tiled": 0, "shared": 0, "secondary": Counter(), "files_with_c": 0, "files": 0}
    files = sorted(
        f for f in os.listdir(CORPUS) if f.lower().endswith(".hap"))
    builtin = load_builtin()
    sources = [(os.path.join(CORPUS, f), None) for f in files]
    sources.append(("builtin", builtin))  # full v2 HAP file; parsed via hap_c_section
    per_file_modes = Counter()
    for path, blt in sources:
        if blt:
            data, name = blt
        else:
            with open(path, "rb") as fh:
                data = fh.read()
            name = os.path.basename(path)
        cs = hap_c_section(data)
        if not cs:
            agg["files"] += 1
            continue
        c_off, c_size = cs
        agg["files"] += 1
        agg["files_with_c"] += 1
        c = data[c_off:c_off + c_size]
        st = analyze_c(c, name, report)
        for k in ("parts", "bad", "ext", "size_ok", "overlaps", "tiled", "shared"):
            agg[k] += st[k]
        for k in ("flags", "mode248", "field0", "field2", "bpp", "extmode",
                  "secondary"):
            agg[k].update(st[k])
        for m, n in st["mode248"].items():
            per_file_modes[m] += n
    print(f"files: {agg['files']}, with C section: {agg['files_with_c']}")
    print(f"parts ok: {agg['size_ok']}, bad: {agg['bad']}, overlaps: {agg['overlaps']}, shared-slot duplicates: {agg['shared']}")
    print(f"flags dist: { {hex(k): v for k, v in sorted(agg['flags'].items())} }")
    print(f"flags&1 (tiled) parts: {agg['tiled']}")
    print(f"mode 2/4/8 (secondary row) parts: { {k: v for k, v in sorted(agg['mode248'].items())} }")
    print(f"bpp dist: { {k: v for k, v in sorted(agg['bpp'].items())} }")
    print(f"ext (flags&0x10) parts: {agg['ext']}, ext mode byte @+0x17: { {hex(k): v for k, v in sorted(agg['extmode'].items())} }")
    print(f"field0 top10: { [(hex(k), v) for k, v in agg['field0'].most_common(10)] }  distinct={len(agg['field0'])}")
    print(f"field2 top10: { [(hex(k), v) for k, v in agg['field2'].most_common(10)] }  distinct={len(agg['field2'])}")
    if report:
        print("\n-- issues (first 25) --")
        for r in report[:25]:
            print(" ", r)
    else:
        print("\nno layout issues")

if __name__ == "__main__":
    main()
