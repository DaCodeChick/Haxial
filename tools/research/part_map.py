#!/usr/bin/env python3
"""S2 Batch V (V2.1) — part-slot map: built-in C section partOff[512] dump.

Emits, for every non-empty part slot of the built-in v2 HAP blob:
  index, pool offset, w, h, flags, bpp, palette count, transIdx,
  field0 (clear colour), caps {L,T,R,B}, field2 (margins {L,T,R,B}),
  ext block (mode, gradA, gradB, insets), total part size.

Cross-references the code-derived consumer map (V2.1) where known:
  consumer = widget render function + state context (from disassembly).
This is layout/identity data (raw static), not semantic naming — unknown
slots are listed without invented names.
"""
import struct

EXE = "/Users/schala/Downloads/AppearanceEdit.exe"

def bswap32(v): return struct.unpack(">I", struct.pack("<I", v))[0]
def bswap16(v): return struct.unpack(">H", struct.pack("<H", v))[0]
def d_off(va): return 0x5DA00 + (va - 0x45F000)

# code-derived consumer map (V2.1, disassembly-verified 2026-11-27).
# index -> (consumer fn, state context, confidence)
CODE_MAP = {
    0x6E: ("sldrRender 0x42B820", "SLDR state case C (jump 0x4577C4) — track base colour idx", "C"),
    0x6F: ("sldrRender 0x42B820", "SLDR state case B — track base colour idx", "C"),
    0x72: ("sldrRender 0x42B820; sldrPartLookup 0x42BD00", "SLDR horizontal unpressed (valueStruct bit0x20 clear)", "C"),
    0x73: ("sldrRender 0x42B820", "SLDR state case B — part idx", "C"),
    0x74: ("sldrRender 0x42B820", "SLDR state case A — part idx", "C"),
    0x76: ("sldrPartLookup 0x42BD00", "SLDR horizontal pressed (valueStruct bit0x20 set)", "C"),
    0x7A: ("sldrRender 0x42B820", "SLDR state dispatch — part idx (press-release path)", "C"),
    0x7B: ("sldrRender 0x42B820", "SLDR state dispatch — part idx", "C"),
    0x7C: ("sldrRender 0x42B820", "SLDR state dispatch — part idx", "C"),
    0x7E: ("sldrPartLookup 0x42BD00", "SLDR vertical unpressed", "C"),
    0x82: ("sldrPartLookup 0x42BD00", "SLDR vertical pressed", "C"),
    0x92: ("scrollbar path (doc 20 s12)", "hSbar partOff[146]", "C doc20"),
    0x93: ("scrollbar path (doc 20 s12)", "hSbar partOff[147]", "C doc20"),
    0x96: ("scrollbar path (doc 20 s12)", "hSbar partOff[150]", "C doc20"),
    0xA5: ("scrollbar path (doc 20 s12)", "vSbar partOff[165]", "C doc20"),
    0xA6: ("scrollbar path (doc 20 s12)", "vSbar partOff[166]", "C doc20"),
    0xA9: ("scrollbar path (doc 20 s12)", "vSbar partOff[169]", "C doc20"),
    0xCF: ("FUN_0042d6d0 0x42D6D0", "flag [local_20]==0 branch — base part", "C"),
    0xD0: ("FUN_0042d6d0 0x42D6D0", "flag [local_20]!=0 branch — alt part", "C"),
    0xD4: ("FUN_0042d6d0 0x42D6D0", "flag [local_20]==0 branch — base part (2nd group)", "C"),
    0xD5: ("FUN_0042d6d0 0x42D6D0", "flag [local_20]!=0 branch — alt part (2nd group)", "C"),
    0xD9: ("FUN_0042d6d0 0x42D6D0", "flag [local_20]==0 branch — base part (3rd group)", "C"),
    0xDA: ("FUN_0042d6d0 0x42D6D0", "flag [local_20]!=0 branch — alt part (3rd group)", "C"),
    0xDE: ("FUN_0042d6d0 0x42D6D0", "flag [local_20]==0 branch — base part (4th group)", "C"),
    0xDF: ("FUN_0042d6d0 0x42D6D0", "flag [local_20]!=0 branch — alt part (4th group)", "C"),
    0x101: ("mbarDrawTitleItem 0x42AC00", "menu-bar title item, state bit0 clear — background", "C"),
    0x102: ("mbarDrawTitleItem 0x42AC00", "menu-bar title item, state bit0 set — background", "C"),
    0x105: ("mbarDrawTitleItem 0x42AC00", "menu-bar title item, state bit0 clear — content tile", "C"),
    0x106: ("mbarDrawTitleItem 0x42AC00", "menu-bar title item, state bit0 set — content tile", "C"),
}

def main():
    exe = open(EXE, "rb").read()
    blob = exe[d_off(0x4683D4):d_off(0x4683D4) + 0x112A0]
    # built-in blob is a full v2 %HAP file; locate its C section
    # (coff u32BE @0x34, csize u32BE @0x38 — same layout as corpus .hap)
    assert blob[:4] == b"%HAP", blob[:4]
    coff = bswap32(struct.unpack_from("<I", blob, 0x34)[0])
    csize = bswap32(struct.unpack_from("<I", blob, 0x38)[0])
    c = blob[coff:coff + csize]
    print(f"built-in HAP: C section at {coff:#x}, size {csize:#x}")
    partoff = c[0x40:0x40 + 512 * 4]
    print("== built-in v2 C section partOff[512] dump ==")
    used = 0
    rows = []
    for i in range(512):
        off = bswap32(struct.unpack_from("<I", partoff, i * 4)[0])
        if off == 0:
            continue
        used += 1
        if off + 0x20 > len(c):
            rows.append(f"| {i:#x} | {off:#x} | OUT OF BOUNDS |")
            continue
        w = bswap16(struct.unpack_from("<H", c, off)[0])
        h = bswap16(struct.unpack_from("<H", c, off + 2)[0])
        flags = c[off + 4]
        bpp = c[off + 5]
        pal = c[off + 6] + 1
        trans = c[off + 7]
        f0 = bswap32(struct.unpack_from("<I", c, off + 8)[0])
        caps = list(c[off + 0xC:off + 0x10])
        f2 = bswap32(struct.unpack_from("<I", c, off + 0x10)[0])
        ext = flags & 0x10
        extstr = ""
        if ext:
            mode = c[off + 0x14]
            ga = c[off + 0x15:off + 0x18]
            gb = c[off + 0x19:off + 0x1C]
            ins = list(c[off + 0x1C:off + 0x20])
            extstr = (f"ext mode={mode} A={ga.hex()} B={gb.hex()} ins={ins}")
        cons = CODE_MAP.get(i)
        consstr = f"{cons[0]} / {cons[1]}" if cons else "—"
        rows.append(
            f"| {i:#x} | {off:#x} | {w}x{h} | {flags:#x} | {bpp} | {pal} | {trans} "
            f"| 0x{f0:08X} | {caps} | 0x{f2:08X} | {extstr} | {consstr} |")
    print(f"used slots: {used} / 512")
    print()
    print("| idx | off | WxH | flags | bpp | pal | trans | field0 | caps LTRB | field2 | ext | code consumer (V2.1) |")
    print("|---|---|---|---|---|---|---|---|---|---|---|---|")
    for r in rows:
        print(r)

if __name__ == "__main__":
    main()
