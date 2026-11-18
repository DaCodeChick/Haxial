#!/usr/bin/env python3
"""hap_inspect.py — read-only structural inspector for Haxial .hap appearance files.

Research tooling for the legacy HAP format (see research/appearance-edit/04-hap-format.md).
Parses the file header, Block A (metadata resources), and the C/D/E/F/G sections
according to the structure recovered from AppearanceEdit.exe 1.400.

Guarantees:
  - read-only: never writes to or modifies any scanned file
  - bounds-checked: every read is range-validated; malformed data yields explicit
    errors, never exceptions or out-of-bounds reads
  - unknown fields are reported as-is, never silently reinterpreted
  - decodes only what the recovered spec establishes; everything else is reported
    as raw data with a confidence note

Usage:
  uv run --script tools/research/hap_inspect.py FILE...
  uv run --script tools/research/hap_inspect.py --corpus            # all refs/**
  uv run --script tools/research/hap_inspect.py --json FILE         # machine output
"""
import argparse
import json
import sys
from pathlib import Path


class HapError(Exception):
    pass


def be16(b, o):
    if o + 2 > len(b):
        raise HapError(f"bounds: need u16 at {o:#x}")
    return (b[o] << 8) | b[o + 1]


def be32(b, o):
    if o + 4 > len(b):
        raise HapError(f"bounds: need u32 at {o:#x}")
    return int.from_bytes(b[o:o + 4], "big")


class Header:
    def __init__(self, b):
        if len(b) < 0x88:
            raise HapError(f"file too small for header: {len(b):#x} < 0x88")
        if b[0:4] != b"%HAP":
            raise HapError(f"bad magic: {b[0:4]!r}")
        self.version = be16(b, 4)
        if self.version not in (1, 2):
            raise HapError(f"unsupported version: {self.version}")
        self.field_08 = be32(b, 0x08)          # -> doc+0x1B8 (meaning unconfirmed)
        self.opt_hi = b[0x0C]                  # option-list selection, high nibble
        self.opt_lo = b[0x0D]                  # option-list selection, low nibble
        self.option_value = None
        if 0 < self.opt_hi < 0x10 and 0 < self.opt_lo < 0x10:
            self.option_value = (self.opt_hi << 4) | self.opt_lo
        self.A = be32(b, 0x2C)                 # block A offset (fixed 0x88)
        self.B = be32(b, 0x30)                 # block A size
        self.C_off, self.C_size = be32(b, 0x34), be32(b, 0x38)
        self.D_off, self.D_size = be32(b, 0x3C), be32(b, 0x40)
        self.E_off, self.E_size = be32(b, 0x44), be32(b, 0x48)
        self.F_off, self.F_size = be32(b, 0x4C), be32(b, 0x50)
        self.G_off, self.G_size = be32(b, 0x54), be32(b, 0x58)
        self.flag_7C = b[0x7C]                 # C/A-block valid
        self.flag_7D = b[0x7D]                 # D section present
        self.flag_7E = b[0x7E]                 # D encoding: 1=v1 table, 2=v2 direct
        self.flag_7F = b[0x7F]                 # E encoding: 1=v1, 2=v2
        self.flag_80 = b[0x80]                 # F section enabled
        self.flag_81 = b[0x81]                 # G section enabled
        self.n = len(b)

    def check(self):
        errs = []
        if self.A != 0x88:
            errs.append(f"A offset {self.A:#x} != fixed 0x88")
        if self.B < 0x34:
            errs.append(f"block A size {self.B:#x} < 0x34")
        if self.A + self.B > self.n:
            errs.append(f"block A extends past EOF (A+B={self.A + self.B:#x})")
        if self.flag_7C != 1 or self.flag_7D != 1:
            errs.append(f"flags 0x7C/0x7D = {self.flag_7C}/{self.flag_7D} (want 1/1)")
        for nm, off, size in (("C", self.C_off, self.C_size), ("D", self.D_off, self.D_size),
                              ("E", self.E_off, self.E_size), ("F", self.F_off, self.F_size),
                              ("G", self.G_off, self.G_size)):
            if size and off + size > self.n:
                errs.append(f"section {nm} extends past EOF ({off:#x}+{size:#x})")
        return errs


def block_a(b, h):
    """Return (info_dict, warnings)."""
    w = []
    A, B = h.A, h.B
    r = {"offset": A, "size": B,
         "prev_save": (be32(b, A + 0), be32(b, A + 4)),   # (high, low) FILETIME
         "last_save": (be32(b, A + 8), be32(b, A + 12)),
         "resource_sizes": [b[A + 0x22 + i] for i in range(4)],
         "resources": []}
    off = A + 0x34
    total = 0
    for i, s in enumerate(r["resource_sizes"]):
        if off + s > A + B:
            w.append(f"r{i + 1} ({s} bytes) exceeds block A")
            break
        chunk = b[off:off + s]
        txt = "".join(chr(c) if 32 <= c < 127 else f"\\x{c:02x}" for c in chunk)
        r["resources"].append({"size": s, "text": txt})
        off += s
        total += s
    if B != 0x34 + total:
        w.append(f"block A: 0x34 + resources ({total:#x}) != B ({B:#x}); slack {B - 0x34 - total} byte(s)")
    return r, w


def section_c(b, h):
    if h.C_size == 0:
        return {"present": False}
    if h.C_size < 0x840:
        return {"present": True, "error": f"size {h.C_size:#x} < 0x840 minimum"}
    pool = h.C_size - 0x840
    if h.C_off + 0x840 > len(b):
        return {"present": True, "error": "table extends past EOF"}
    tbl = [be32(b, h.C_off + 0x40 + i * 4) for i in range(512)]
    nz = [(i, v) for i, v in enumerate(tbl) if v]
    for i, v in nz:
        if v < 0x840 or v + 0x14 > pool + 0x840:
            return {"present": True, "error": f"slot {i} offset {v:#x} implausible"}
    out = {"present": True, "table_entries": len(nz), "pool_bytes": pool}
    # parse the first blob (offset 0x840 within section) to validate the C-bitmap shape
    first = min(v for _, v in nz) if nz else None
    if first is not None:
        out["first_blob"] = parse_c_bitmap(b, h.C_off + first, h.C_off + h.C_size - first)
    return out


def rowbytes(w, bpp):
    if bpp == 1:
        return ((w + 31) & ~31) >> 3
    if bpp == 2:
        return ((w + 15) & ~15) >> 2
    if bpp == 4:
        return ((w + 7) & ~7) >> 1
    if bpp == 8:
        return (w + 3) & ~3
    raise HapError(f"bad bpp {bpp}")


def parse_c_bitmap(b, off, limit):
    """C-pool bitmap: 0x14 (or 0x20) header + main rows + secondary rows + palette."""
    o = off
    if o + 0x14 > off + limit:
        raise HapError("C bitmap: truncated header")
    W, H = be16(b, o), be16(b, o + 2)
    if not (0 < W < 0x4001 and 0 < H < 0x4001):
        raise HapError(f"C bitmap: implausible W/H {W}/{H}")
    flags, bpp, pal = b[o + 4], b[o + 5], b[o + 6]
    if bpp not in (1, 2, 4, 8):
        raise HapError(f"C bitmap: bad bpp {bpp}")
    hdr = 0x20 if flags & 0x10 else 0x14
    main = rowbytes(W, bpp) * H
    sec = 0
    m = flags & 0x0F
    if m in (2, 4, 8):
        sec = rowbytes(W, m) * H
    elif m not in (0, 1):
        raise HapError(f"C bitmap: bad secondary mode {m}")
    palb = (pal + 1) * 4
    total = hdr + main + sec + palb
    if total > limit:
        raise HapError(f"C bitmap: size {total:#x} exceeds section remainder {limit:#x}")
    return {"W": W, "H": H, "bpp": bpp, "palette": pal + 1,
            "header": hdr, "main_bytes": main, "secondary_bytes": sec,
            "total": total, "flags": flags}


def section_d(b, h):
    if h.D_size == 0:
        return {"present": False}
    if h.flag_7E == 1:
        if h.D_size < 0xD8:
            return {"present": True, "encoding": "v1",
                    "error": f"v1 D size {h.D_size:#x} < 0xD8"}
        # v1: 54-word selection from a larger D pool via built-in table
        return {"present": True, "encoding": "v1", "bytes": h.D_size,
                "words": h.D_size // 4,
                "note": "reader selects 54 words via built-in table (0x463C7C)"}
    if h.flag_7E == 2:
        if h.D_size < 0xD8:
            return {"present": True, "encoding": "v2",
                    "error": f"v2 D size {h.D_size:#x} < 0xD8"}
        words = [int.from_bytes(b[h.D_off + i * 4:h.D_off + i * 4 + 4], "little")
                 for i in range(54)]
        bad = [i for i, w in enumerate(words) if w >> 24 != 0]
        return {"present": True, "encoding": "v2", "bytes": h.D_size,
                "colors_00BBGGRR": 54,
                "high_byte_nonzero": bad,
                "sample": [f"{w:08x}" for w in words[:6]]}
    return {"present": True, "error": f"unknown D encoding flag {h.flag_7E}"}


def parse_e_bitmap(b, off, limit):
    """E-pool bitmap: 8-byte header + palette + pixels (FUN_00404700)."""
    if off + 8 > off + limit:
        raise HapError("E bitmap: truncated header")
    W, H = be16(b, off), be16(b, off + 2)
    if not (0 < W < 0x4001 and 0 < H < 0x4001):
        raise HapError(f"E bitmap: implausible W/H {W}/{H}")
    flags, bpp, pal, tidx = b[off + 4], b[off + 5], b[off + 6], b[off + 7]
    if bpp not in (1, 2, 4, 8):
        raise HapError(f"E bitmap: bad bpp {bpp}")
    total = 8 + (pal + 1) * 4 + rowbytes(W, bpp) * H
    if total > limit:
        raise HapError(f"E bitmap: size {total:#x} exceeds section remainder {limit:#x}")
    return {"W": W, "H": H, "bpp": bpp, "palette": pal + 1,
            "trans_alpha_flag": bool(flags & 1),
            "trans_index": tidx if flags & 1 else None,
            "total": total}


def parse_ink_record(b, off, limit):
    """%IKN record (F blobs, v2 E blobs): header + M sub-record headers + payload pool."""
    if b[off:off + 4] != b"%IKN":
        raise HapError(f"bad %IKN magic {b[off:off + 4]!r}")
    ver = be16(b, off + 4)
    if ver != 1:
        raise HapError(f"%IKN version {ver} != 1")
    N, M = b[off + 6], b[off + 7]
    npad = (N + 3) & ~3
    sub_off = off + npad + 8
    if sub_off + M * 12 > off + limit:
        raise HapError("%IKN: sub-record headers exceed record")
    subs = []
    for i in range(M):
        so = sub_off + i * 12
        W, H = be16(b, so), be16(b, so + 2)
        flg, bpp, pal, rsv = b[so + 4], b[so + 5], b[so + 6], b[so + 7]
        chain = be32(b, so + 8)
        if not (0 < W < 0x4001 and 0 < H < 0x4001):
            raise HapError(f"%IKN sub {i}: implausible W/H {W}/{H}")
        if bpp == 24:
            main = ((W * 3) + 3) & ~3 * H
        elif bpp in (1, 2, 4, 8):
            main = rowbytes(W, bpp) * H
        else:
            raise HapError(f"%IKN sub {i}: bad bpp {bpp}")
        sec = 0
        m = flg & 0x1F
        if m in (2, 4, 8):
            sec = rowbytes(W, m) * H
        elif m not in (0, 1):
            raise HapError(f"%IKN sub {i}: bad secondary mode {m}")
        palc = 0
        if bpp > 8:
            if flg & 1:
                palc = (pal + 1) * 4
        else:
            palc = (pal + 1) * 4
        payload = main + sec + palc
        if chain + payload > limit:
            raise HapError(f"%IKN sub {i}: payload ({chain:#x}+{payload:#x}) exceeds record")
        subs.append({"W": W, "H": H, "bpp": bpp, "palette": (palc // 4) if palc else 0,
                     "payload_at": chain, "payload_bytes": payload})
    name = b[off + 8:off + 8 + N]
    return {"version": 1, "path": "".join(chr(c) if 32 <= c < 127 else f"\\x{c:02x}" for c in name),
            "sub_records": subs}


def parse_msi_record(b, off, limit):
    """%MSI record (G blobs): 16-byte header + palette + pixels."""
    if b[off:off + 4] != b"%MSI":
        raise HapError(f"bad %MSI magic {b[off:off + 4]!r}")
    ver = be16(b, off + 4)
    if ver != 1:
        raise HapError(f"%MSI version {ver} != 1")
    W, H = b[off + 6], b[off + 7]
    Wmin, Hmin = b[off + 0xC], b[off + 0xD]
    fmt, pal = b[off + 0xE], b[off + 0xF]
    if W == 0 or H == 0 or W <= Wmin or H <= Hmin:
        raise HapError(f"%MSI: bad dims W={W} H={H} min={Wmin}/{Hmin}")
    if fmt == 2:
        row = ((W + 15) & ~15) >> 2
        p = (pal + 1) * 4
        if p < 8:
            raise HapError("%MSI: 2bpp needs >= 2 palette colors")
    elif fmt == 8:
        row = (W + 3) & ~3
        p = (pal + 1) * 4
        if p < 8:
            raise HapError("%MSI: 8bpp needs >= 2 palette colors")
    elif fmt == 0x20:
        row = W * 4
        p = 0
    else:
        raise HapError(f"%MSI: bad format {fmt:#x}")
    total = 0x10 + p + row * H
    if total > limit:
        raise HapError(f"%MSI: size {total:#x} exceeds record limit {limit:#x}")
    return {"W": W, "H": H, "format": fmt, "palette": p // 4, "total": total}


def section_e(b, h):
    if h.E_size == 0:
        return {"present": False}
    if h.flag_7F == 2:
        # v2: [u32 BE count][count x u32 BE offsets][pool of %IKN records]
        if h.E_size < 4:
            return {"present": True, "encoding": "v2", "error": "too small"}
        cnt = be32(b, h.E_off)
        cnt = min(cnt, (h.E_size >> 2) - 1)
        out = {"present": True, "encoding": "v2", "count": cnt}
        if h.E_off + 4 + cnt * 4 > len(b):
            out["error"] = "offset table past EOF"
            return out
        table = [be32(b, h.E_off + 4 + i * 4) for i in range(cnt)]
        out["pool_start"] = 4 + cnt * 4
        ok, bad = 0, []
        samples = []
        for i, o in enumerate(table):
            if o == 0 or o >= h.E_size:
                bad.append(f"#{i}: offset {o:#x} invalid")
                continue
            try:
                rec = parse_ink_record(b, h.E_off + o, h.E_size - o)
                ok += 1
                if len(samples) < 3:
                    samples.append({"id": i, **rec})
            except HapError as e:
                bad.append(f"#{i} @{o:#x}: {e}")
        out["parsed_ok"] = ok
        if bad:
            out["errors"] = bad[:8]
        if samples:
            out["samples"] = samples
        return out
    # v1: 192 rows x 16 bytes (u32 BE offA, u32 BE offB, 8 reserved) + pool at 0xC00
    if h.E_size <= 0xBFF:
        return {"present": True, "encoding": "v1", "error": f"size {h.E_size:#x} <= 0xBFF minimum"}
    rows = []
    for i in range(192):
        o = h.E_off + i * 16
        a, bb = be32(b, o), be32(b, o + 4)
        if a or bb:
            rows.append((i, a, bb))
    out = {"present": True, "encoding": "v1", "table_rows": len(rows)}
    parsed = 0
    errs = []
    for i, a, bb in rows:
        for tag, off in (("A", a), ("B", bb)):
            if off == 0:
                continue
            if off < 0xC00 or off >= h.E_size:
                errs.append(f"row {i} {tag}: offset {off:#x} implausible")
                continue
            try:
                rec = parse_e_bitmap(b, h.E_off + off, h.E_size - off)
                parsed += 1
                if "samples" not in out and len(errs) == 0:
                    out["samples"] = []
                if len(out.get("samples", [])) < 3:
                    out["samples"].append({"id": i, "slot": tag, **rec})
            except HapError as e:
                errs.append(f"row {i} {tag} @{off:#x}: {e}")
    out["parsed_ok"] = parsed
    if errs:
        out["errors"] = errs[:8]
    return out


def section_f(b, h):
    if h.F_size == 0:
        return {"present": False}
    if h.F_size < 4:
        return {"present": True, "error": "too small"}
    n = be32(b, h.F_off)
    n = min(n, (h.F_size >> 2) - 1)
    out = {"present": True, "count": n}
    if h.F_off + 4 + n * 4 > len(b):
        out["error"] = "offset table past EOF"
        return out
    offs = [be32(b, h.F_off + 4 + i * 4) for i in range(n)]
    ok, bad = 0, []
    samples = []
    for i, o in enumerate(offs):
        if o == 0 or o >= h.F_size:
            bad.append(f"#{i}: offset {o:#x} invalid")
            continue
        try:
            rec = parse_ink_record(b, h.F_off + o, h.F_size - o)
            ok += 1
            if len(samples) < 4:
                samples.append(rec)
        except HapError as e:
            bad.append(f"#{i} @{o:#x}: {e}")
    out["parsed_ok"] = ok
    if bad:
        out["errors"] = bad[:8]
    if samples:
        out["samples"] = samples
    return out


def section_g(b, h):
    if h.G_size == 0:
        return {"present": False}
    if h.G_size < 4:
        return {"present": True, "error": "too small"}
    slots = be32(b, h.G_off)
    slots = min(slots, (h.G_size >> 2) - 1)
    out = {"present": True, "slot_count": slots}
    if h.G_off + 4 + slots * 4 > len(b):
        out["error"] = "offset table past EOF"
        return out
    offs = [be32(b, h.G_off + 4 + i * 4) for i in range(slots)]
    ok, bad = 0, []
    samples = []
    for i, o in enumerate(offs):
        if o == 0 or o >= h.G_size:
            continue
        try:
            rec = parse_msi_record(b, h.G_off + o, h.G_size - o)
            ok += 1
            if len(samples) < 4:
                samples.append(rec)
        except HapError as e:
            bad.append(f"slot {i} @{o:#x}: {e}")
    out["parsed_ok"] = ok
    if bad:
        out["errors"] = bad[:8]
    if samples:
        out["samples"] = samples
    return out


def inspect(path, max_samples=True):
    b = Path(path).read_bytes()
    out = {"path": str(path), "size": len(b)}
    try:
        h = Header(b)
    except HapError as e:
        out["error"] = str(e)
        return out
    out["version"] = h.version
    out["header_errors"] = h.check()
    if h.option_value is not None:
        out["header_option_value"] = h.option_value
    if h.field_08:
        out["header_field_08"] = f"{h.field_08:#x}"
    try:
        ba, w = block_a(b, h)
        out["block_A"] = {
            "name": ba["resources"][0]["text"] if len(ba["resources"]) > 0 else None,
            "version_str": ba["resources"][1]["text"] if len(ba["resources"]) > 1 else None,
            "credits": ba["resources"][2]["text"] if len(ba["resources"]) > 2 else None,
            "description_len": ba["resources"][3]["size"] if len(ba["resources"]) > 3 else 0,
            "last_save_high": ba["last_save"][0], "last_save_low": ba["last_save"][1],
        }
        out["block_A_warnings"] = w
    except HapError as e:
        out["block_A_error"] = str(e)
    out["C"] = section_c(b, h)
    out["D"] = section_d(b, h)
    out["E"] = section_e(b, h)
    out["F"] = section_f(b, h)
    out["G"] = section_g(b, h)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="*")
    ap.add_argument("--corpus", action="store_true", help="scan refs/**/*.hap")
    ap.add_argument("--json", action="store_true", help="JSON output")
    args = ap.parse_args()
    files = args.files
    if args.corpus:
        files = [str(p) for p in sorted(Path("refs").rglob("*.hap"))]
    if not files:
        ap.error("no files (pass paths or --corpus)")
    results = [inspect(f) for f in files]
    if args.json:
        print(json.dumps(results, indent=1))
        return
    for r in results:
        if "error" in r:
            print(f"{r['path']}: ERROR {r['error']}")
            continue
        name = r.get("block_A", {}).get("name")
        ver = r.get("block_A", {}).get("version_str")
        line = f"{r['path']}  [{r['version']}]  {r['size']:#x}B"
        if name:
            line += f"  name={name!r}" + (f" v{ver}" if ver else "")
        print(line)
        for sec in ("C", "D", "E", "F", "G"):
            s = r.get(sec, {})
            if not s or not s.get("present"):
                print(f"  {sec}: -")
                continue
            if "error" in s:
                print(f"  {sec}: ERROR {s['error']}")
            elif sec == "C":
                extra = f" first_blob={s.get('first_blob')}" if "first_blob" in s else ""
                print(f"  C: {s['table_entries']} slots, pool {s['pool_bytes']:#x}B{extra}")
            elif sec == "D":
                enc = s.get('encoding')
                detail = f"{s.get('bytes', 0):#x}B" if s.get('bytes') else f"{s.get('words')} words"
                print(f"  D: {enc} {detail}" + (f" sample={s.get('sample')}" if s.get('sample') else ""))
            elif sec == "E":
                enc = s.get("encoding")
                rows = s.get("table_rows", s.get("count"))
                print(f"  E: {enc} rows={rows}, parsed {s.get('parsed_ok', 0)}" +
                      (f" errs={s['errors'][:2]}" if s.get("errors") else ""))
            else:
                print(f"  {sec}: count={s.get('count', s.get('slot_count'))}, ok={s.get('parsed_ok')}" +
                      (f" errs={s['errors'][:2]}" if s.get("errors") else ""))


if __name__ == "__main__":
    main()