# Haxial Reference Corpus — Inventory (session R0-A.1)

Target corpus: `refs/appearances/**/*.hap` (111 files) and `refs/fonts/*.fnt` (11 files).
These are untrusted external input. This inventory is a read-only catalog with
integrity hashes and header-level structure; no file in this corpus has been modified.

Companion machine-readable data: `tools/research/corpus-inventory.json` (full per-file
details incl. sha256) and `tools/research/hap_inspect.py` (the structural inspector that
validated every entry below).

**Validation status:** every one of the 111 `.hap` files was parsed end-to-end by
`hap_inspect.py` against the spec in `04-hap-format.md` with **zero errors and zero
unexplained fields** (2026-11-17). All files are HAP version 1.

---

## 1. Appearance files (`refs/appearances/`)

### 1.1 Summary

| Property | Value |
|---|---|
| File count | 111 |
| Format | HAP, version **1** in all 111 files |
| Header flags (0x7C–0x81) | `01 01 01 01 00 00` in all 111 files (A✓ C✓ D=v1 E=v1, no F, no G) |
| D section | v1 encoding (0x330 = 816 B) in all 111 files |
| C section (widget bitmaps) | present in 38 files; 13–127 non-zero table slots |
| E section (per-widget icons) | present in 31 files; 4–50 non-zero rows; 4–100 bitmap blobs |
| F / G sections | absent (flag 0x80/0x81 = 0) — v2-only sections |
| Size range | 0x3EC (1,004 B, color-only) … 0x9ACDC (634,076 B, Zurie_Constructicons_large) |
| Total bytes | 0x34B4A8 (3,442,024) |
| Header field 0x08 (→ doc+0x1B8) | 0 in all files |
| Header option nibbles (0x0C/0x0D) | 0x00/0x00 in all files (no option selection persisted) |
| Block A alignment slack | 76 files carry 1 byte of padding (B rounded up to 8) |

### 1.2 Groups

- **Color-only (71 files)** — `refs/appearances/Color-only Appearances/`. No C or E
  section; the file is header + Block A + D (816 B of colors). 34 color records ×
  6 × 4 bytes. These files exercise only the D v1 permutation path.
- **Themed (40 files)** — `refs/appearances/` top level. Carry C (widget state
  bitmaps), E (per-widget icons), or both:
  - C + E: 29 files
  - C only: 9 files
  - E only: 2 files (`MacOS9 Icons.hap`, `SprCrnr Theme 2.1.hap`)

### 1.3 Themed file table

C slots = non-zero entries in the 512-slot C offset table; E rows = non-zero rows of
the 192-row E table; blobs = A+B bitmap count in the E pool.

| File | Theme name (Block A r1) | Version (r2) | Size | C slots | E rows (blobs) |
|---|---|---|---|---|---|
| Aluminum Alloy - Toxic.hap | Aluminum Alloy - Toxic | 1.0 | 0x12304 | 114 | — |
| Ashen.hap | ashen | 1.0 | 0x15324 | 126 | 42 (69) |
| BeOS.hap | BeOS | 1.0 | 0x9284 | 104 | 20 (36) |
| Blue Fragmentation.hap | Blue Fragmentation | 1.220 | 0xC0F8 | 87 | 18 (36) |
| Blue Print.hap | Blue Print.hap | 1.000 | 0xB0B4 | 123 | 49 (98) |
| Boilerplate-Rusty.hap | Boilerplate - Rusty | 1.0 | 0x36150 | 118 | 4 (4) |
| Boilerplate-Steel.hap | Boilerplate - Steel | 1.0 | 0x36118 | 118 | 4 (4) |
| Boilerplate.hap | Boilerplate | 1.0 | 0x29E34 | 118 | 4 (4) |
| CelShaded - Blue.hap | CelShaded - Blue | 1.0 | 0xD16C | 110 | — |
| CelShaded - Mac.hap | CelShaded - Blue | 1.0 | 0xD16C | 110 | — |
| Cybernet.hap | Cybernet | 1.111 | 0x2F54 | 13 | 14 (14) |
| DSX [Green].hap | DSX [Green] | 1.0 | 0x1D1F0 | 102 | 34 (42) |
| Function (6680B2 Edition).hap | Function (6680B2 Edition) | .: VERSION 1 :. | 0x1C2CC | 115 | 43 (71) |
| Function 2.0.hap | Function | .: VERSION 2:. | 0x10780 | 116 | 4 (4) |
| Gamespot-1100.hap | Gamespot | 1.100 | 0xB788 | 104 | — |
| GrayLine 4.0 by woods.hap | GrayLine | 4.0 | 0xA324 | 88 | 16 (28) |
| International2.hap | International | 1.0 | 0x8268 | 127 | 26 (50) |
| MacOS Classic.hap | MacOS Classic | 1.0 | 0x13A80 | 109 | 42 (69) |
| MacOS9 Icons.hap | MacOS 9 | 1.000 | 0xEB2C | — | 27 (53) |
| Matrix Ice.hap | Matrix Ice | 1.0 | 0x18054 | 17 | 27 (53) |
| Milk Redux - Apple Logo.hap | Milk Redux | 1.0 | 0xE230 | 106 | — |
| Milk Redux.hap | Milk Redux | 1.0 | 0xE2A8 | 106 | — |
| Mjolnir Mac.hap | Mjolnir Mac | 1.000 | 0x65A0 | 120 | 39 (55) |
| Mjolnir Win.hap | Mjolnir Win | 1.000 | 0x659C | 120 | 39 (55) |
| Mjolnir.hap | Mjolnir | 1.000 | 0x63D8 | 116 | 39 (55) |
| Shinobi_by_PimpToxie.hap | Shinobi | 1.0 | 0x1F738 | 97 | 27 (45) |
| Siro.hap | Siro | 1.0 | 0x1E34C | 125 | 36 (56) |
| SprCrnr Theme 2.1.hap | SprCrnr Theme 2.1 | 2.1 | 0xF130 | — | 42 (69) |
| Swordfish.hap | Swordfish | 1.00 | 0x6958 | 114 | — |
| Terminal-MONO.hap | Terminal-MONO.hap | 1.000 | 0xA4D4 | 121 | 49 (98) |
| Terminal-NEO.hap | Terminal-NEO.hap | 1.000 | 0xA9F4 | 122 | 49 (98) |
| Terminal-TRON.hap | Terminal-TRON.hap | 1.000 | 0xA9B0 | 122 | 49 (98) |
| Voodoo.hap | Voodoo - Tsunami | 1.0 | 0x7518 | 117 | — |
| Win2k by Lech.hap | Win2k DarkGrey | .01 | 0x11DC4 | 107 | 47 (93) |
| WinXP.hap | WinXP | 1.100 | 0x17890 | 110 | 21 (38) |
| X 3D 000 (FINAL).hap | X 3D 000.hap | 1.3 | 0xAC10 | 124 | 50 (100) |
| X.hap | X.hap | 1.000 | 0xB70C | 122 | 50 (100) |
| Zurie_Constructicons_large.hap | Constructicons _ Large Edition | 1.5 | 0x9ACDC | 101 | 43 (71) |
| cube.hap | cube² (0xC2 0xB2) | 1.0 | 0x3A60 | 121 | — |
| iceIKle.hap | iceIKle | 1 | 0x15338 | 111 | 15 (30) |

Notes:
- Theme names are raw Block A r1 bytes; a few contain non-ASCII (e.g. `0xAE` in
  "DSX [Green]" version field, `0xC2 0xB2` superscript-2 in "cube").
- "CelShaded - Mac.hap" reuses the "CelShaded - Blue" theme name.
- Version strings are free-form (r2): `1.0`, `1.220`, `.: VERSION 1 :.`, `.01`, `1`, …

### 1.4 Structural regularities (CONFIRMED by full-corpus parse)

1. **E pool geometry**: for every file with an E section, the minimum non-zero blob
   offset is exactly **0xC00** (end of the 192-row table) and the last blob ends
   exactly at the section end. No gaps, no trailing data.
2. **E row usage**: corpus files use rows 1–95 only (per-row counts in
   `corpus-inventory.json`); rows 96–191 are never used. See §1.5 for why this
   matters.
3. **C table sparsity**: 13–127 of the 512 slots are used; C pool = C_size − 0x840.
4. **D section**: always 0x330 bytes; the 816 B are the v1 permutation encoding
   (see `04-hap-format.md` §6).
5. **Block A**: r4 (description) is non-empty in the built-in v2 default (113 B) but
   is 0 in every corpus file; r3 (credits) is populated in most themed files.

### 1.5 Critical compatibility finding — v1 E rows vs. the 1.400 built-in map

The v1 E reader in AppearanceEdit.exe 1.400 (`FUN_00405310`) does **not** derive the
row→widget mapping from the file. It uses two built-in tables compiled into the
executable:

- `0x00464100`: 28 × u32 (LE). In the shipped build only ids 13,15,…,27 hold valid
  row indices (0x63–0x6A = rows **99–106**); ids 2,3 → row 0; all other ids hold
  pointer-sized values that fail the `row < 192` check in `FUN_004048D0`.
- `0x004642E0`: 26 × (u32, u32) volume pairs. In the shipped build every first
  field is a pointer-sized value (fails the same check); pairs 10 and 19 are
  zeroed (→ row 0, always empty).

Consequences:

- This build can load at most row 0 and rows 99–106 from a v1 E section.
- **No file in the corpus stores data in rows 96–191** (blobs live in rows 1–95).
- Therefore AppearanceEdit.exe 1.400 renders **no E-section icons** from any corpus
  file. The E data in v1 files is consumed only by older editor builds that used a
  different (presumably dynamic) row map, or by the Haxial runtime (not yet analyzed).

CONFIRMED for the reader code path (decompilation of `FUN_00405310` + disassembly
line `PUSH dword ptr [EAX*0x4 + 0x464100]` + shipped table contents + full-corpus
row-usage statistics). This is the single most important format/compatibility
constraint discovered in this session.

### 1.6 Built-in defaults embedded in the executable

AppearanceEdit.exe contains two embedded HAP v2 blobs ("Evil Chiaroscuro 2.0"):

| Blob | VA | Size | Notes |
|---|---|---|---|
| A | 0x00466DD4 | 0x112A0 (70,304 B) | Complete, contiguous C/D/E/F/G. No direct xrefs found. **Extracted** to `assets/builtin-EvilChiaroscuro-v2-A.hap` — the only known real v2 sample. |
| B | 0x004683D4 | 0x9D90 (40,336 B, up to end of E) | F/G header fields overlap C/D/E (invalid → skipped on load). Referenced by 5 sites incl. the D-default loader (`0x00404045` in `FUN_00404040`). **Extracted** to `assets/builtin-EvilChiaroscuro-v2-B.hap`. |

Both were validated by `hap_inspect.py` (blob A: C 142 slots, D v2, E 35/35 %IKN,
F 25/25 %IKN, G 19/19 %MSI — all clean).

---

## 2. Font files (`refs/fonts/`)

11 files, all with the `"%FNT"` magic. Inventory only — the font format is the
subject of a future FontEdit RE session.

| File | Size | Magic | Ver (u16 BE @4) | u16 @6 | File size (u32 LE @8) | Name len (u32 LE @0x18) | Name |
|---|---|---|---|---|---|---|---|
| End 0.9.fnt | 0x1C9C | %FNT | 2 | 0x0001 | 0x1C9C ✓ | 3 | End |
| Enocht 1.11.fnt | 0x2834 | %FNT | 2 | 0x0001 | 0x2834 ✓ | 6 | Enocht |
| Harial 0.5.fnt | 0x919C | %FNT | 2 | 0x0001 | 0x919C ✓ | 6 | Harial |
| Lies 1.299.fnt | 0x40F8 | %FNT | 2 | 0x0001 | 0x40F8 ✓ | 4 | Lies |
| Mjolnir 1.21.fnt | 0x5190 | %FNT | 2 | 0x0001 | 0x5190 ✓ | 7 | Mjolnir |
| OCRAP.fnt | 0x1C30 | %FNT | 2 | 0x0001 | 0x1C30 ✓ | 5 | OCRAP |
| Von Yerk 0.9.fnt | 0x4E4C | %FNT | 2 | 0x0001 | 0x4E4C ✓ | 8 | Von Yerk |
| XeBob 1.0.fnt | 0x26B0 | %FNT | 2 | 0x0001 | 0x26B0 ✓ | 5 | XeBob |
| Yspe Sans 0.91.fnt | 0x662C | %FNT | 2 | 0x0001 | 0x662C ✓ | 9 | Yspe Sans |
| Yspe Sans Bold 0.9.fnt | 0x6814 | %FNT | 2 | 0x0001 | 0x6814 ✓ | 14 | Yspe Sans Bold |
| bit1.fnt | 0x1850 | %FNT | 2 | 0x0001 | 0x1850 ✓ | 4 | bit1 |

Header pattern (CONFIRMED by cross-file consistency; full format = future session):

```
0x00  4   magic "%FNT" (25 46 4E 54)
0x04  2   u16 version = 2  (BE byte order, same convention as HAP)
0x06  2   u16 = 1
0x08  4   u32 (LE) total file size — matches actual size in all 11 files
0x0C  12  zeroed
0x18  4   u32 (LE) font name length
0x1C  n   font name (NUL-padded to 0x40)
0x40  …   font data (structure unanalyzed)
```

Notes:
- HAP↔font linkage: the v2 `%IKN` ink records (F section / v2 E) carry path tags such
  as `font/`, `text/`, `data/` — the mechanism by which an appearance references or
  embeds font/text resources. No corpus v1 file has an F section, so no v1 sample
  exercises the linkage; the built-in v2 blob A does (25 ink records, paths
  `data`, `font/`, `text/` — 1 sub-record each, 24-bit and paletted bitmaps).
- Full sha256 hashes for all 122 files are in `tools/research/corpus-inventory.json`.

---

## 3. Method and reproducibility

- Inventory generated by `tools/research/hap_inventory.py` (headers + hashes) and
  `tools/research/hap_inspect.py` (full structural parse).
- Run: `uv run --script tools/research/hap_inspect.py --corpus`
- Machine output: `uv run --script tools/research/hap_inspect.py --corpus --json`
- All tools are strictly read-only and bounds-checked; a malformed file produces
  explicit `HapError` messages rather than silent reinterpretation.

## 4. Confidence

| Claim | Level |
|---|---|
| 111 HAP v1 files, all parse cleanly against the 04 spec | CONFIRMED (full-corpus run, 2026-11-17) |
| E pool geometry (0xC00 start, exact end) | CONFIRMED (31/31 files) |
| v1 E row usage 1–95 vs. 1.400 map rows 0/99–106 | CONFIRMED (corpus + code + shipped tables) |
| 11 FNT v2 files share the header pattern above | CONFIRMED (11/11) |
| FNT data layout beyond 0x40 | HYPOTHESIS (not analyzed — future FontEdit session) |
| "%IKN" path semantics (`font/` = font resource) | PROBABLE (consistent paths + FontEdit's existence; not yet runtime-verified) |