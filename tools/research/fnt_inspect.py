#!/usr/bin/env python3
"""fnt_inspect.py — Haxial .fnt v2 corpus validator (S2 Batch F).

Validates the .fnt v2 model from research/appearance-edit/21-s2-font-and-text-pipeline.md:
  - 64-byte header: magic %FNT, u16BE ver=2, u16BE=1, u32BE size, 12B zero,
    pstr name @0x18 (width 0x20), pstr author @0x38 (width 0x08)
  - face slot @0xB8 (84B): count u8 @+0xB, tableOff u32BE @+0xC
  - glyph records: 16B stride @ tableOff; key u32BE @+0, charID u32BE @+4,
    bytes @+8..+B, tag/adv u32BE @+0xC (0 = none/inline, else pool offset)
  - external pixel pool: contiguous variable-length 1bpp glyph blocks

Usage:
  fnt_inspect.py <file.fnt>            single file, detailed report
  fnt_inspect.py --corpus <dir>        validate every *.fnt in dir (summary)
  fnt_inspect.py <file.fnt> --rows N   dump first N glyph records
  fnt_inspect.py <file.fnt> --draw CH  render glyph for codepoint CH as ASCII art
"""
import struct
import sys
import os

MAGIC = b"%FNT"
HDR = 0x40
FACE = 0xB8
FACE_SIZE = 0x54
REC = 0x10


def pstr(buf, off, width):
    n = buf[off]
    if n > width:
        return None, n  # length prefix exceeds field
    return buf[off + 1:off + 1 + n].decode("latin1"), n


def parse_header(buf):
    errs = []
    if len(buf) < HDR + FACE_SIZE + REC:
        return None, ["file too small (%d bytes)" % len(buf)]
    if buf[0:4] != MAGIC:
        errs.append("bad magic %r" % buf[0:4])
    ver, = struct.unpack_from(">H", buf, 4)
    flag = buf[6]
    face_count = buf[7]
    size, = struct.unpack_from(">I", buf, 8)
    if size != len(buf):
        errs.append("size field %d != file size %d (u32BE expected)"
                    % (size, len(buf)))
    if ver != 2:
        errs.append("version %d != 2" % ver)
    if flag != 0:
        errs.append("flag @+0x06 = %d (expected 0)" % flag)
    if buf[0x0C:0x18] != b"\x00" * 12:
        errs.append("0x0C..0x17 not zeroed: %s" % buf[0x0C:0x18].hex())
    name, nl = pstr(buf, 0x18, 0x27)
    if name is None:
        errs.append("name length %d exceeds field (0x19..0x3F)" % nl)
    return {
        "ver": ver, "flag": flag, "face_count": face_count, "size": size,
        "name": name,  # NOTE: no author field exists in the format (doc 21 §1.1)
    }, errs


def parse_faces(buf, face_count):
    """Face slots at 0xB8 + i*0x54: count u8 @+0xB, table u32BE @+0xC, name pstr @+0x14."""
    faces = []
    for i in range(face_count):
        s = FACE + i * FACE_SIZE
        if s + FACE_SIZE > len(buf):
            break
        cnt = buf[s + 0x0B]
        table, = struct.unpack_from(">I", buf, s + 0x0C)
        nm, _ = pstr(buf, s + 0x14, 0x20)
        faces.append({"count": cnt, "table": table, "name": nm})
    return faces


def records(buf, table, limit=None):
    """Yield (idx, rec) for the 256 ASCII rows (16B stride, no zero-break)."""
    n = 0
    i = 0
    while i < 0x100:
        off = table + i * REC
        if off + REC > len(buf):
            break
        rec = buf[off:off + REC]
        key, = struct.unpack_from(">I", rec, 0)
        chid, = struct.unpack_from(">I", rec, 4)
        tag, = struct.unpack_from(">I", rec, 0x0C)
        yield i, {"key": key, "chid": chid, "w": rec[8], "h": rec[9],
                  "x": rec[0x0A], "tag": rec[0x0B], "adv": tag,
                  "inline": rec[0:0x0C]}
        i += 1
        n += 1
        if limit and n >= limit:
            break
    return i  # total scanned


def scan_records(buf, table):
    """Scan the 256 ASCII rows: count non-empty, pool offsets, inline pixels.

    +0x0C dual use (doc 21 §7.1): u32BE ≤ 0xFFFF pointing into the data
    region = pixel-pool offset; anything else is an advance-only row
    (first memory byte = pen advance; high bytes stale/irrelevant).
    """
    total = 0
    ext = []
    inline = 0
    advance_only = 0
    for i in range(0x100):
        off = table + i * REC
        if off + REC > len(buf):
            break
        rec = buf[off:off + REC]
        if rec == b"\x00" * REC:
            continue
        total += 1
        tag, = struct.unpack_from(">I", rec, 0x0C)
        if tag:
            if tag <= 0xFFFF and table + 0x1000 < tag < len(buf):
                ext.append((i, tag, None))
            else:
                advance_only += 1  # value not a usable pool offset
        elif any(rec[0:12]):
            inline += 1
    return total, ext, inline, advance_only


def scan_extended(buf, table):
    """Scan the extended region (rows >= 0x100) trying two alignments:
    naive (table + 0x1000 + i*16) and +4 (table + 0x1004 + i*16).
    A valid row has an in-bounds u32BE @+0xC pointing past the table.
    Returns (alignment, [(i, key, poolOff), ...]) for the better candidate."""
    best = (None, [])
    for shift in (0, 4):
        base = table + 0x1000 + shift
        rows = []
        i = 0
        while True:
            r = base + i * REC
            if r + REC > len(buf):
                break
            rec = buf[r:r + REC]
            if rec == b"\x00" * REC:
                break
            off, = struct.unpack_from(">I", rec, 0x0C)
            key, = struct.unpack_from(">I", rec, 0)
            if 0x1200 < off < len(buf):
                rows.append((i, key, off))
            else:
                break
            i += 1
        if len(rows) > len(best[1]):
            best = ("+0x%x" % shift, rows)
    return best


def check_pool(buf, ext):
    """Verify external offsets form a plausible packed pool (ascending, in-bounds)."""
    bad = []
    for i, off, err in ext:
        if err:
            bad.append((i, off, err))
    offs = sorted(o for _, o, e in ext if not e)
    for a, b in zip(offs, offs[1:]):
        if b < a:
            bad.append(("", (a, b), "descending offset (impossible in packed pool)"))
    return bad, offs


def draw_glyph(buf, table, cp):
    """Render the glyph for codepoint cp (ASCII range: record index = cp)."""
    off = table + cp * REC
    if off + REC > len(buf):
        return "out of range"
    rec = buf[off:off + REC]
    if rec == b"\x00" * REC:
        return "(no record)"
    tag, = struct.unpack_from(">I", rec, 0x0C)
    chid, = struct.unpack_from(">I", rec, 4)
    if tag:
        data = buf[tag:]
        # try small widths: guess width from chid? use record w if nonzero
        w = rec[8] or 1
        h = rec[9] or 1
        if w * h > len(data):
            # fall back: scan candidate (w,h) that exactly fit a prefix
            cands = [(ww, hh) for ww in range(1, 13) for hh in range(1, 33)
                     if ww * hh == len(data) or ww * hh <= len(data)]
            if not cands:
                return "(cannot infer dims; %d bytes at %s)" % (len(data), hex(tag))
            w, h = cands[0]
        data = data[:w * h]
    else:
        data = rec[0:12]
        w = min(12, max(1, sum(1 for b in data if b))) or 1
        h = 1
    lines = []
    for y in range(h):
        row = data[y * w:(y + 1) * w]
        line = ""
        for b in row:
            line += "".join("#" if (b >> (7 - x)) & 1 else "." for x in range(8))
        lines.append(line)
    return "cp=%d chid=%d tag=%s w=%d h=%d\n%s" % (
        cp, chid, hex(tag) if tag else "inline", w, h, "\n".join(lines))


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
            faces = parse_faces(buf, hdr["face_count"]) if hdr else []
            if not faces:
                print("FAIL %s: no face parsed" % fn)
                continue
            f0 = faces[0]
            total, ext, inline, adv = scan_records(buf, f0["table"])
            bad, _ = check_pool(buf, ext)
            ext_align, ext_rows = scan_extended(buf, f0["table"])
            status = "OK " if not errs and not bad else "FAIL"
            name = hdr["name"] if hdr else "?"
            print("%s %-28s hdr_errs=%d faces=%d f0count=%d table=%s rows=%d pool_offs=%d inline=%d adv_only=%d pool_bad=%d ext_rows=%d(%s)"
                  % (status, fn, len(errs), len(faces), f0["count"], hex(f0["table"]),
                     total, len(ext), inline, adv, len(bad), len(ext_rows), ext_align))
            for e in errs[:3]:
                print("   hdr: " + e)
            for b in bad[:3]:
                print("   pool: %s" % (b,))
            ok += 1
        print("%d files checked" % ok)
        return 0

    path = args[0]
    buf = open(path, "rb").read()
    hdr, errs = parse_header(buf)
    faces = parse_faces(buf, hdr["face_count"])
    print("== %s ==" % path)
    print("size=%d ver=%d flag=%d faces=%d name=%r" % (
        len(buf), hdr["ver"], hdr["flag"], hdr["face_count"], hdr["name"]))
    for i, f in enumerate(faces):
        print("face[%d]: count=%d table=%s name=%r" % (i, f["count"], hex(f["table"]), f["name"]))
    for e in errs:
        print("HDR ERR: " + e)
    f0 = faces[0]
    total, ext, inline, adv = scan_records(buf, f0["table"])
    bad, offs = check_pool(buf, ext)
    print("ascii rows=%d pool_offs=%d inline=%d advance_only=%d pool_bad=%d" % (
        total, len(ext), inline, adv, len(bad)))
    for b in bad:
        print("POOL BAD: %s" % (b,))
    if offs:
        print("ascii pool range: %s .. %s (%d offsets)" % (
            hex(offs[0]), hex(offs[-1]), len(offs)))
    ext_align, ext_rows = scan_extended(buf, f0["table"])
    if ext_rows:
        print("extended rows: %d (alignment %s) keys=%s..%s pool=%s..%s" % (
            len(ext_rows), ext_align,
            hex(ext_rows[0][1]), hex(ext_rows[-1][1]),
            hex(ext_rows[0][2]), hex(ext_rows[-1][2])))

    if "--rows" in args:
        n = int(args[args.index("--rows") + 1])
        for i, rec in records(buf, f0["table"], n):
            print("rec[%2d] key=%d chid=%d w=%d h=%d x=%d tag=%d adv=%08x inline=%s" % (
                i, rec["key"], rec["chid"], rec["w"], rec["h"], rec["x"],
                rec["tag"], rec["adv"], rec["inline"].hex()))
    if "--draw" in args:
        cp = int(args[args.index("--draw") + 1])
        print(draw_glyph(buf, f0["table"], cp))
    return 0 if not errs and not bad else 2


if __name__ == "__main__":
    sys.exit(main())
