#!/usr/bin/env python3
"""
%MNU menu payload walker for AppearanceEdit.exe built-in menus.

Layout (code-verified against menuPayloadParse @ 0x412060 disassembly,
S2 B2-remainder, 2026-11-21):

Header (hdrSize = (b7 + nameLen + 0x2B) & ~3, name pstr at +0x28 only when nameLen>0):
  +0x00  4B   magic "%MNU" (checked byte-swapped in code)
  +0x04  2B   version u16BE == 1
  +0x06  1B   nameLen
  +0x07  1B   b7
  +0x08  16B  reserved (zero in corpus)
  +0x1C  4B   style u32BE          (menuObjectCtor arg; 1=popup/normal, 2=scal)
  +0x20  4B   field5c u32BE        (menuObj+0x5C; 0xFFFFFFFF in corpus)
  +0x24  4B   itemCount u32BE      (clamped to 0x400)
  +0x28       name pstr (length byte + bytes) when nameLen > 0

Item (size = (b36 + b37 + iconLen + tlen + 0x3B) & ~3):
  +0x00  4B   id u32BE
  +0x04  4B   value2 u32BE         (secondary/composite id)
  +0x08  1B   (pad, ignored by parser)
  +0x09  1B   flagsHi              (<<16: top byte of 24-bit flags)
  +0x0C  4B   field10 u32BE        (blob+0x10; 0 in corpus; semantics unknown)
  +0x10  8B   (not read by parser)
  +0x18  2B   accel u16BE
  +0x1A  2B   flagsLo u16BE        (low 16 bits of 24-bit flags)
  +0x1C  4B   (not read by parser; 00 20 58 00 pattern seen)
  +0x20  1B   (not read)
  +0x21  1B   b21                  (blob+0x16)
  +0x22  2B   (low byte used -> blob+0x17; high byte not read)
  +0x24  12B  (not read by parser)
  +0x34  1B   tlen                 (title byte count; authoritative)
  +0x35  1B   iconLen
  +0x36  1B   b36                  (0 in corpus; semantics unknown)
  +0x37  1B   b37                  (0 in corpus; semantics unknown)
  +0x38       title [tlen]
  +0x38+tlen  icon [iconLen]

flags24 = (flagsHi << 16) | flagsLo, observed combos:
  0x20000 ticked, 0x40000 disabled, 0x50000 separator (static+disabled),
  0x100000 icon, 0x140000 icon+disabled
"""
import struct, sys

EXE = "/Users/schala/Downloads/AppearanceEdit.exe"

# (name, va, payload_size)
MENUS = [
    ("exam", 0x45F900, 0x218),
    ("fsit", 0x45FB18, 0x78C),
    ("scal", 0x4602A8, 0x328),
]

def va_to_raw(pe, va):
    for (va_s, raw_s, sz) in pe:
        if va_s <= va < va_s + sz:
            return raw_s + (va - va_s)
    raise ValueError(hex(va))

def load_sections(path):
    with open(path, "rb") as f:
        d = f.read()
    pe_off = struct.unpack_from("<I", d, 0x3C)[0]
    machine = struct.unpack_from("<H", d, pe_off + 4)[0]
    nsec = struct.unpack_from("<H", d, pe_off + 6)[0]
    opt_size = struct.unpack_from("<H", d, pe_off + 20)[0]
    sec_off = pe_off + 24 + opt_size
    # image base from optional header (PE32: +4, PE32+: +24)
    is_pe32plus = (machine == 0x8664)
    image_base = struct.unpack_from("<Q" if is_pe32plus else "<I", d, pe_off + 24 + (24 if is_pe32plus else 28))[0]
    secs = []
    for i in range(nsec):
        o = sec_off + i * 40
        vsize = struct.unpack_from("<I", d, o + 8)[0]
        va = image_base + struct.unpack_from("<I", d, o + 12)[0]
        raw = struct.unpack_from("<I", d, o + 20)[0]
        secs.append((va, raw, vsize))
    return secs, d

def walk(name, va, size, secs, data, quiet=False):
    base = va_to_raw(secs, va)
    p = base
    magic = data[p:p+4]
    assert magic == b"%MNU", (name, magic)
    version = struct.unpack_from(">H", data, p+4)[0]
    nameLen = data[p+6]
    b7 = data[p+7]
    hdr = (b7 + nameLen + 0x2B) & ~3
    style = struct.unpack_from(">I", data, p+0x1C)[0]
    f5c = struct.unpack_from(">I", data, p+0x20)[0]
    count = struct.unpack_from(">I", data, p+0x24)[0]
    if not quiet:
        print(f"== {name} @0x{va:06X} size=0x{size:X} hdr=0x{hdr:X} v={version} "
              f"nameLen={nameLen} b7={b7} style={style} f5c=0x{f5c:08X} count={count}")
    rec = {"name": name, "va": va, "size": size, "hdr": hdr, "version": version,
           "nameLen": nameLen, "b7": b7, "style": style, "f5c": f5c, "count": count,
           "items": []}
    if nameLen:
        rec["name_pstr"] = data[p+0x29:p+0x29+nameLen].decode("latin-1")
        if not quiet:
            print(f"   name = {rec['name_pstr']!r}")
    q = p + hdr
    end = p + size
    ok = True
    for i in range(count):
        if q + 0x38 > end:
            if not quiet: print(f"   [FAIL] item {i}: prefix overruns payload")
            ok = False
            break
        rid = struct.unpack_from(">I", data, q)[0]
        value2 = struct.unpack_from(">I", data, q+4)[0]
        flagsHi = data[q+9]
        field10 = struct.unpack_from(">I", data, q+0x0C)[0]
        accel = struct.unpack_from(">H", data, q+0x18)[0]
        flagsLo = struct.unpack_from(">H", data, q+0x1A)[0]
        b21 = data[q+0x21]
        b23 = data[q+0x22]
        tlen = data[q+0x34]
        iconLen = data[q+0x35]
        b36 = data[q+0x36]
        b37 = data[q+0x37]
        sz = (b36 + b37 + iconLen + tlen + 0x3B) & ~3
        if q + sz > end:
            if not quiet: print(f"   [FAIL] item {i}: size 0x{sz:X} overruns payload (end 0x{end-q:X})")
            ok = False
            break
        title = data[q+0x38:q+0x38+tlen]
        icon = data[q+0x38+tlen:q+0x38+tlen+iconLen]
        flags = (flagsHi << 16) | flagsLo
        it = {"index": i, "off": q - base, "size": sz, "id": rid, "value2": value2,
              "flags": flags, "field10": field10, "accel": accel, "b21": b21, "b23": b23,
              "tlen": tlen, "iconLen": iconLen, "b36": b36, "b37": b37,
              "title": title.split(b"\0", 1)[0].decode("latin-1"),
              "icon": icon.hex() if icon else None}
        rec["items"].append(it)
        if not quiet:
            print(f"   item {i:2d} @+0x{q-base:04X} size=0x{sz:02X} id=0x{rid:08X} "
                  f"v2=0x{value2:08X} flags=0x{flags:06X} f10=0x{field10:08X} "
                  f"accel=0x{accel:04X} b21=0x{b21:02X} b23=0x{b23:02X} "
                  f"tlen={tlen} iconLen={iconLen} b36={b36} b37={b37}")
            if title:
                print(f"            title={it['title']!r}")
            if icon:
                print(f"            icon={icon.hex()}")
        q += sz
    rec["leftover"] = end - q
    rec["exact"] = (end - q) == 0 and ok
    if not quiet:
        print(f"   walk {'EXACT' if rec['exact'] else 'MISMATCH'} (leftover={end-q} bytes)")
    return rec

def main():
    import json
    mode = sys.argv[1] if len(sys.argv) > 1 else "txt"
    secs, data = load_sections(EXE)
    recs = [walk(n, va, sz, secs, data, quiet=(mode == "json")) for (n, va, sz) in MENUS]
    if mode == "json":
        print(json.dumps({"exe": EXE, "menus": recs}, indent=1))
    allok = all(r["exact"] for r in recs)
    sys.exit(0 if allok else 1)

if __name__ == "__main__":
    main()
