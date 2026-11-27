#!/usr/bin/env python3
"""fnt_inspect.py — Haxial .fnt v2 corpus validator (S2 Batch F; V1-corrected).

Model (Batch V F-2 full decode — code + corpus CONFIRMED, doc 21 §1/§14.6):
  - 64-byte header: magic %FNT, u16BE ver=2, flag u8 @+6, faceCount u8 @+7,
    u32BE size @+8, 12B zero @+0xC, pstr name @+0x18
  - face slot @0xB8 (0x54B): count u8 @+0xB (# of 24B face blocks),
    table u32BE @+0xC (=0x10C), face-name pstr @+0x14 (empty in samples)
  - face blocks @ table + k*0x18 (24B each, one per size variant):
      +0 ascent, +1 descent, +2, +3, +4..+0F zero,
      +0x10 rowCount D (u32BE), +0x14 rowBase E (u32BE, blob-relative)
    block0.E = table + count*0x18 ; block k.E = block k-1.E + 0x1000
  - row tables: D x 16B rows at blob + E; row i @ E + i*16:
      +0 key u32BE (== i in direct region), +4 poolOff u32BE (0 = none),
      +8 w, +9 h, +0xA x, +0xB tag, +0xC adv, +0xD..+0xF pad
    cp < 0x100: direct index; cp >= 0x100: binary search rows [0x100, D-1]
    by bswap-u32BE key; missing -> default row = E + 0x1A0 (row 26)
  - pixel pool: per face, densely packed in ROW ORDER immediately after
    the row tables; block size = rowBytes*h, rowBytes=(w+7)>>3, MSB-first;
    next face's E = align4(previous pool end); inkBlitCore guard is the
    looser poolOff + w*h <= size

The Batch F version of this tool validated a NAIVE model (single 256-row
table at 0x10C; +0x0C dual-use). Its counts (pool_offs, inline, ext_rows,
pool_bad) are ARTIFACTS and must not be reused.

Usage:
  fnt_inspect.py <file.fnt>            single file, detailed report
  fnt_inspect.py --corpus <dir>        validate every *.fnt in dir (summary)
  fnt_inspect.py <file.fnt> --rows N   dump first N rows of the first face
  fnt_inspect.py <file.fnt> --draw CH  render glyph for codepoint CH (ASCII art)
"""
import struct
import sys
import os

MAGIC = b"%FNT"
HDR = 0x40
FACE = 0xB8
REC = 0x18  # face-block stride (24)
ROW = 0x10  # glyph-row stride (16)
DEFROW = 0x1A0  # default (missing-glyph) row offset (row 26)


def u32be(buf, off):
    return struct.unpack_from(">I", buf, off)[0]


def pstr(buf, off, width):
    n = buf[off]
    if n > width:
        return None, n
    return buf[off + 1:off + 1 + n].decode("latin1"), n


def parse_header(buf):
    errs = []
    if len(buf) < HDR + 0x54 + REC:
        return None, ["file too small (%d bytes)" % len(buf)]
    if buf[0:4] != MAGIC:
        errs.append("bad magic %r" % buf[0:4])
    ver, = struct.unpack_from(">H", buf, 4)
    flag = buf[6]
    face_count = buf[7]
    size, = struct.unpack_from(">I", buf, 8)
    if size != len(buf):
        errs.append("size field %d != file size %d" % (size, len(buf)))
    if ver != 2:
        errs.append("version %d != 2" % ver)
    if flag != 0:
        errs.append("flag @+0x06 = %d (expected 0)" % flag)
    if buf[0x0C:0x18] != b"\x00" * 12:
        errs.append("0x0C..0x17 not zeroed: %s" % buf[0x0C:0x18].hex())
    name, nl = pstr(buf, 0x18, 0x27)
    if name is None:
        errs.append("name length %d exceeds field" % nl)
    return {"ver": ver, "flag": flag, "face_count": face_count, "size": size,
            "name": name}, errs


def parse_face_blocks(buf, count, table, errs):
    """Return list of dicts per face block; verify E-sequence invariants."""
    blocks = []
    for k in range(count):
        b = table + k * REC
        if b + REC > len(buf):
            errs.append("face block %d out of bounds" % k)
            break
        d = u32be(buf, b + 0x10)
        e = u32be(buf, b + 0x14)
        blocks.append({
            "ascent": buf[b + 0], "descent": buf[b + 1],
            "b2": buf[b + 2], "b3": buf[b + 3],
            "D": d, "E": e,
        })
        # zero A/B/C fields (all samples)
        if u32be(buf, b + 4) or u32be(buf, b + 8) or u32be(buf, b + 0xC):
            errs.append("block %d: reserved A/B/C fields nonzero" % k)
    if blocks:
        exp0 = table + count * REC
        if blocks[0]["E"] != exp0:
            errs.append("block0 E=0x%X != expected 0x%X (table + count*0x18)"
                        % (blocks[0]["E"], exp0))
    return blocks, None  # align4(pool_end) check done by caller (needs pool stats)


def scan_face(buf, block, errs, row_end=None):
    """Validate one face's row table + pool. Returns stats dict.

    Pool invariants (V1.4): densely packed in ROW ORDER, block size
    ((w+7)>>3)*h, MSB-first; pool starts at/beyond the row-table end."""
    d, e = block["D"], block["E"]
    row_end = e + d * ROW
    stats = {"rows": 0, "with_pool": 0, "empty": 0,
             "pool_min": None, "pool_max": None, "pool_end": None, "bad": []}
    prev_pool, prev_size = None, 0
    ext = 0
    for i in range(d):
        o = e + i * ROW
        if o + ROW > len(buf):
            stats["bad"].append("row %d out of bounds" % i)
            break
        key = u32be(buf, o)
        pool = u32be(buf, o + 4)
        w, h, x, tag, adv = buf[o + 8], buf[o + 9], buf[o + 0xA], buf[o + 0xB], buf[o + 0xC]
        stats["rows"] += 1
        if i < 0x100:
            if key != i:
                stats["bad"].append("row %d: key %d != index" % (i, key))
        else:
            ext += 1
            if key < 0x100:
                stats["bad"].append("ext row %d: key 0x%X < 0x100" % (i, key))
        if pool == 0:
            stats["empty"] += 1
            if w or h:
                stats["bad"].append("row %d: poolOff=0 but w/h nonzero" % i)
            continue
        rb = (w + 7) >> 3
        size = rb * h
        if pool + size > len(buf):
            stats["bad"].append("row %d: pool 0x%X+%d exceeds file 0x%X"
                                % (i, pool, size, len(buf)))
        if pool < row_end:
            stats["bad"].append("row %d: pool 0x%X inside row table (ends 0x%X)"
                                % (i, pool, row_end))
        if prev_pool is not None and pool != prev_pool + prev_size:
            stats["bad"].append("row %d: pool 0x%X != prev 0x%X+%d (gap/overlap in packing)"
                                % (i, pool, prev_pool, prev_size))
        prev_pool, prev_size = pool, size
        stats["with_pool"] += 1
        if stats["pool_min"] is None or pool < stats["pool_min"]:
            stats["pool_min"] = pool
        if stats["pool_end"] is None or pool + size > stats["pool_end"]:
            stats["pool_end"] = pool + size
    stats["ext_rows"] = ext
    if row_end > len(buf):
        stats["bad"].append("row table end 0x%X exceeds file 0x%X"
                            % (row_end, len(buf)))
    return stats


def draw_glyph(buf, block, cp):
    e, d = block["E"], block["D"]
    if cp < 0x100:
        idx = cp
    else:
        # binary search like fontGlyphSearch
        lo, hi = 0x100, d - 1
        idx = 0
        found = False
        while lo <= hi:
            mid = (lo + hi) >> 1
            k = u32be(buf, e + mid * ROW)
            if k == cp:
                idx, found = mid, True
                break
            if cp > k:
                lo = mid + 1
            else:
                hi = mid - 1
        if not found:
            idx = 0x1A  # default row 26
    o = e + idx * ROW
    if o + ROW > len(buf):
        return "(row out of bounds)"
    key = u32be(buf, o)
    pool = u32be(buf, o + 4)
    w, h, x, tag, adv = buf[o + 8], buf[o + 9], buf[o + 0xA], buf[o + 0xB], buf[o + 0xC]
    if pool == 0 or pool + w * h > len(buf):
        return "cp=%d idx=%d key=%d poolOff=0x%X w=%d h=%d (no pixels)" % (
            cp, idx, key, pool, w, h)
    rb = (w + 7) >> 3
    lines = []
    for y in range(h):
        rowb = buf[pool + y * rb: pool + (y + 1) * rb]
        bits = ""
        for px in range(w):
            bits += "#" if (rowb[px >> 3] >> (7 - px & 7)) & 1 else "."
        lines.append(bits)
    return "cp=%d idx=%d key=%d pool=0x%X w=%d h=%d x=%d tag=%d adv=%d\n%s" % (
        cp, idx, key, pool, w, h, x, tag, adv, "\n".join(lines))


def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        return 1

    if args[0] == "--corpus":
        d = args[1]
        ok = 0
        for fn in sorted(os.listdir(d)):
            if not fn.endswith(".fnt"):
                continue
            buf = open(os.path.join(d, fn), "rb").read()
            hdr, errs = parse_header(buf)
            if not hdr:
                print("FAIL %s: %s" % (fn, errs))
                continue
            count = buf[FACE + 0xB]
            table = u32be(buf, FACE + 0xC)
            blocks, _ = parse_face_blocks(buf, count, table, errs)
            stats_list = [scan_face(buf, b, errs) for b in blocks]
            for k in range(1, len(blocks)):
                pe = stats_list[k - 1]["pool_end"] or 0
                if blocks[k]["E"] != (pe + 3) & ~3:
                    errs.append("block %d E=0x%X != align4(prev pool end 0x%X)=0x%X"
                                % (k, blocks[k]["E"], pe, (pe + 3) & ~3))
            total_bad = len(errs)
            name = hdr["name"] if hdr["name"] else "?"
            b0 = blocks[0] if blocks else {"ascent": 0, "descent": 0, "D": 0, "E": 0}
            last = blocks[-1] if blocks else None
            stat_line = " ".join(
                "f%d(a=%d,D=0x%X,E=0x%X,rows=%d,pool=%d)" %
                (k, b["ascent"], b["D"], b["E"], st["rows"], st["with_pool"])
                for k, (b, st) in enumerate(zip(blocks, stats_list)))
            print("%s %-28s errs=%d count=%d %s" % (
                "OK " if total_bad == 0 else "FAIL", fn,
                total_bad, count, stat_line))
            for e in errs[:4]:
                print("   " + e)
            ok += 1
        print("%d files checked" % ok)
        return 0

    path = args[0]
    buf = open(path, "rb").read()
    hdr, errs = parse_header(buf)
    print("== %s ==" % path)
    print("size=%d ver=%d flag=%d faces=%d name=%r" % (
        len(buf), hdr["ver"], hdr["flag"], hdr["face_count"], hdr["name"]))
    count = buf[FACE + 0xB]
    table = u32be(buf, FACE + 0xC)
    fface, _ = pstr(buf, FACE + 0x14, 0x30)
    print("face slot: count=%d table=0x%X faceName=%r" % (count, table, fface))
    blocks, _ = parse_face_blocks(buf, count, table, errs)
    for k, b in enumerate(blocks):
        print("  block%d: ascent=%d descent=%d b2=%d b3=%d D=0x%X(%d) E=0x%X" % (
            k, b["ascent"], b["descent"], b["b2"], b["b3"], b["D"], b["D"], b["E"]))
    for e in errs:
        print("ERR: " + e)
    blk0 = blocks[0] if blocks else None
    if blk0:
        st = scan_face(buf, blk0, [])
        print("face0 rows=%d with_pool=%d empty=%d ext=%d pool=%s..%s" % (
            st["rows"], st["with_pool"], st["empty"], st["ext_rows"],
            hex(st["pool_min"]) if st["pool_min"] is not None else "-",
            hex(st["pool_end"]) if st["pool_end"] is not None else "-"))
        for b in st["bad"][:8]:
            print("  " + b)
        if "--rows" in args:
            n = int(args[args.index("--rows") + 1])
            e0 = blk0["E"]
            for i in range(min(n, blk0["D"])):
                o = e0 + i * ROW
                print("row[%3d] @0x%04X key=%d pool=0x%X w=%d h=%d x=%d tag=%d adv=%d" % (
                    i, o, u32be(buf, o), u32be(buf, o + 4),
                    buf[o + 8], buf[o + 9], buf[o + 0xA], buf[o + 0xB], buf[o + 0xC]))
        if "--draw" in args:
            cp = int(args[args.index("--draw") + 1])
            print(draw_glyph(buf, blk0, cp))
    return 0 if not errs else 2


if __name__ == "__main__":
    sys.exit(main())
