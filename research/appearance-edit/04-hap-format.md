# HAP — Haxial Appearance File Format (session R0-A.1)

Target: on-disk `.hap` files read/written by `AppearanceEdit.exe` 1.400 (Windows x86,
image base 0x00400000) and consumed by the Haxial runtime.
Primary evidence: decompilation of the parse/serialize code in `AppearanceEdit.exe`
plus byte-level cross-checking against the 111-file reference corpus
(`refs/appearances/`) and the two built-in v2 blobs embedded in the executable.

Status: **v1 fully specified and validated against 111/111 corpus files (zero
errors, 2026-11-17).** v2 specified from code + the built-in sample
`assets/builtin-EvilChiaroscuro-v2-A.hap` (validated clean). No corpus v2 files
exist yet; every claim marked v2 has exactly those two evidence sources.

Companion documents: `08-corpus-inventory.md` (corpus), `06-symbol-ledger.md`
(symbol changes), `tools/research/hap_inspect.py` (validator/inspector).

---

## 1. Executive summary

A `.hap` file is a self-describing container: a fixed 0x88-byte header, a
metadata block (timestamps + 4 display strings), and up to five content sections
(C widget bitmaps, D colors, E per-widget icons, F ink resources, G glyph images).
All multi-byte header/table fields are **big-endian on disk** (the code reads/writes
them via an explicit byte-swap: `bswap32`/`swap16` of the native LE value). Pixel
data and color words are stored **little-endian** (native) inside their sections.

- Version 1 (all 111 corpus files): sections C, D(v1), E(v1); no F/G; flags
  `01 01 01 01 00 00`.
- Version 2 (writer of this build; built-in defaults): sections C, D(v2), E(v2), F,
  G; flags `01 01 02 02 01 01`.
- Key compatibility finding: the v1 E-section row→widget mapping is **not in the
  file** — it is a built-in table in the editor. The shipped 1.400 table maps only
  rows 0 and 99–106, while every corpus file stores E data in rows 1–95, so this
  build renders no v1 E icons. See §9.3.

## 2. Conventions

- Offsets are from the file start unless stated "section-relative".
- `u32 BE` / `u16 BE` = bytes stored most-significant-first. The C code performs
  `bswap32` on the LE-loaded value; on disk the bytes are BE.
- `u32 LE` = native byte order (least-significant-first).
- "Slot" = an entry of a document-side array (0x14 bytes each in memory:
  +0x00 data ptr, +0x08 blob ptr, +0x0C blob size, +0x10 u16 table index).
- Confidence: CONFIRMED = direct code + data observation; PROBABLE = strong
  inference; HYPOTHESIS = unverified.

## 3. File overview

```
+0x0000  header (0x88 bytes, fixed)
+0x0088  Block A (B bytes; B = 0x34 + r1+r2+r3+r4, 8-aligned by writer)
+0x0088+B   section C   (C_size; 0 if absent)
+…          section D   (D_size; 0x330 v1 / 0xD8 v2)
+…          section E   (E_size; 0 if absent)
+…          section F   (F_size; v2 only)
+…          section G   (G_size; v2 only)
```

Section order in the file is always C, D, E, F, G (writer computes each offset as
previous offset + previous size). A section is absent when its size is 0. The
reader validates `offset + size <= filesize` for each section before parsing and
falls back to built-in defaults where applicable (§8).

## 4. Header (0x0000–0x0087, 136 bytes)

| Off | Size | Type | Value / meaning | Evidence |
|---|---|---|---|---|
| 0x00 | 4 | magic | `%HAP` (bytes 25 48 41 50) | parser checks bswap32 == 0x25484150; else error 0x10009 |
| 0x04 | 2 | u16 BE | version: 1 or 2 (else error 0x10008) | parser `swap16(u16) ∈ {1,2}` |
| 0x06 | 2 | — | reserved (zero in all samples) | writer never touches |
| 0x08 | 4 | u32 BE | → doc+0x1B8 (semantics unconfirmed; 0 in all 111 corpus files and both built-in blobs) | parser copies to doc+0x1B8 |
| 0x0C | 1 | u8 | option high nibble (0 = none; 1–15) | §4.1 |
| 0x0D | 1 | u8 | option low nibble (0 = none; 1–15) | §4.1 |
| 0x0E | 0x1E | — | reserved (zero) | NOT section slots 0–3: built-in v2 blob A carries `01 01` at 0x0C/0x0D (writer's default scale option), disproving a 13-slot directory at 0x0C (see cross-reference/00-openkdx.md §1); zero in all 111 v1 corpus files |
| 0x2C | 4 | u32 BE | A = Block A offset (always 0x88) — start of the 6-slot section directory (A,C,D,E,F,G at 0x2C..0x58) | writer `0x88000000` |
| 0x30 | 4 | u32 BE | B = Block A size (≥ 0x34) | writer FUN_004022E0 |
| 0x34 | 4 | u32 BE | C offset | writer |
| 0x38 | 4 | u32 BE | C size (0 if absent) | |
| 0x3C | 4 | u32 BE | D offset | |
| 0x40 | 4 | u32 BE | D size | |
| 0x44 | 4 | u32 BE | E offset | |
| 0x48 | 4 | u32 BE | E size | |
| 0x4C | 4 | u32 BE | F offset | |
| 0x50 | 4 | u32 BE | F size | |
| 0x54 | 4 | u32 BE | G offset | |
| 0x58 | 4 | u32 BE | G size | |
| 0x5C | 0x20 | — | reserved (zero) | writer memset |
| 0x7C | 1 | flag | Block A valid (must be 1 else defaults) | parser |
| 0x7D | 1 | flag | C encoding (1). Presence is C_size≠0, **not** this flag — 73/111 files have C_size=0 with flag still 1 | parser + corpus |
| 0x7E | 1 | flag | D encoding: 1 = v1 permutation, 2 = v2 direct | parser |
| 0x7F | 1 | flag | E encoding: 1 = v1 192-row, 2 = v2 %IKN. Presence is E_size≠0 (80/111 files E_size=0) | parser + corpus |
| 0x80 | 1 | flag | F enable (v1: 0, v2: 1) | parser |
| 0x81 | 1 | flag | G enable (v1: 0, v2: 1) | parser |

**Flag/presence note (CONFIRMED, R0-A.2 corpus scan):** all 111 v1 files carry
identical bytes `01 01 01 01 00 00` at 0x7C..0x81 even when C/E sections are
empty — the six bytes are encoding selectors / enables, and a section is
present iff its directory **length** is non-zero.
| 0x82 | 6 | — | reserved (zero) | |

### 4.1 Option nibbles (0x0C/0x0D) — PROBABLE

If both nibbles are in 1–15, the parser selects option-list item
`(hi << 4) | lo` (value 0x11–0xFF) in a menu-option widget (doc+0x78 sub-object
+0x38). The writer persists the currently selected value, defaulting to 0x11
(17) when nothing is selected. All corpus files store 0x00/0x00 (no selection).
The widget's item list content is editor-internal (an editor display setting,
HYPOTHESIS — e.g. palette layout/preview mode); the file only stores the index.

## 5. Block A (metadata; offset A = 0x88, size B)

Writer: `FUN_00402370`; reader: inline in `FUN_00402900`.
B = 0x34 + (r1+r2+r3+r4), rounded up to a multiple of 8 by the writer (76 of 111
corpus files carry 1 byte of slack; the reader only requires the strings fit).

| Off (A-rel) | Size | Type | Meaning |
|---|---|---|---|
| +0x00 | 4 | u32 BE | timestamp-1 low (FILETIME low) |
| +0x04 | 4 | u32 BE | timestamp-1 high |
| +0x08 | 4 | u32 BE | timestamp-2 low |
| +0x0C | 4 | u32 BE | timestamp-2 high |
| +0x10 | 0x12 | — | padding (zero) |
| +0x22 | 1 | u8 | r1 length (theme name) |
| +0x23 | 1 | u8 | r2 length (version string) |
| +0x24 | 1 | u8 | r3 length (credits) |
| +0x25 | 1 | u8 | r4 length (description) |
| +0x26 | 0x0E | — | padding |
| +0x34 | r1…r4 | bytes | r1 ‖ r2 ‖ r3 ‖ r4 (concatenated) |

Read side: timestamp-1 (hi,lo) → doc+0x1A8/0x1AC; timestamp-2 → doc+0x1B0/0x1B4;
both are formatted (FILETIME → string, `FUN_00434EC0` with format code 0x3020)
into two label widgets (doc+0x70 "previous", doc+0x74 "last").

**Timestamp semantics — CONFIRMED via `hapSaveEntry` (`0x4033A0`):** on every
direct save the save path first overwrites doc+0x1B0/0x1B4 with the current
FILETIME (`FUN_0041C440`) and refreshes label doc+0x74; Block A then persists
(doc+0x1B0,0x1B4) → (A+8,A+12) as the **last-save time**, while (A+0,A+4) carries
doc+0x1A8/0x1AC — the previous save time as read from the last file (never
rewritten by the save path itself). The four strings are set as display
resources on four different UI sub-objects
(doc+0x60, doc+0x100, doc+0x68, doc+0x6C each +0x3C) via `FUN_004308D0`
(CONFIRMED mapping; per-object display role is PROBABLE: name, version, credits,
description — consistent with sample contents: "Boilerplate", "1.0",
"timechanic\xa0industries", built-in 113-byte description).

Strings are raw bytes of the declared length (no NUL terminator required; corpus
samples are NUL-terminated but padding inside the declared length is preserved).
Length is authoritative (per project rules: Pascal-style length-prefix semantics).

## 6. Section C — widget state bitmaps

Writer: `FUN_00407030` (size: `FUN_00407000`); reader: `FUN_004070F0`;
blob parser: `FUN_00406E20`. Minimum size 0x840 (else skipped).

Layout (section-relative):

```
+0x000  0x40  preamble (zero in all samples; PROBABLE reserved)
+0x040  0x800 512 × u32 BE pool offsets (0 = empty slot)
+0x840  C_size - 0x840  blob pool
```

Document side: 174 entries (doc+0x2C + 0x4C, 0x14 bytes each). Entry i holds a
u16 table index at +0x10 (0–511); the reader reads `table[idx]` and, if
non-zero, parses the C blob at that offset and stores (ptr, size) into the entry.
The index→entry assignment is set at document creation (editor-internal).
Corpus: 13–127 of 512 slots used per file.

**C blob** (parser `FUN_00406E20`; requires size ≥ 0x14):

```
+0x00  2  u16 BE W          (1 .. 0x4000)
+0x02  2  u16 BE H          (1 .. 0x4000)
+0x04  1  flags
       bit 0x10: extended header (0x20 instead of 0x14)
       bits 0x0F: secondary-row mode — 0/1 none; 2/4/8 = extra row array at that bpp
+0x05  1  bpp ∈ {1, 2, 4, 8}
+0x06  1  palette count - 1
+0x07  1  unused
+0x08  hdr-8  reserved/extra header bytes
+hdr   main rows:  rowbytes(W,bpp) × H
       secondary rows (if mode 2/4/8): rowbytes(W,mode) × H
       palette: (pal+1) × 4 bytes
```

`rowbytes`: 1bpp = ((W+31)&~31)>>3; 2bpp = ((W+15)&~15)>>2; 4bpp = ((W+7)&~7)>>1;
8bpp = (W+3)&~3. The parser validates `hdr + main + secondary + pal*4 <= remaining`
only — the in-file order of (main, secondary, palette) is not independently
verifiable from the parser; corpus samples place palette last (PROBABLE).

**Extended header (flags bit 0x10) — nine-patch geometry.** The 12 extra
bytes (`+0x08..+0x13`) are decoded from the 18 extended-header blobs in the
built-in v2 appearance (none occur in the 111-file v1 corpus):

```
+0x08  4  u32  field0        ; 0x00FFFFFF or 0x00000000 in all samples (semantics open)
+0x0C  1  u8  capL  (left cap width, px)
+0x0D  1  u8  capT  (top cap height, px)
+0x0E  1  u8  capR  (right cap width, px)
+0x0F  1  u8  capB  (bottom cap height, px)
+0x10  1  u8  insetL         ; content inset (PROBABLE — editor "Left Inset")
+0x11  1  u8  insetT
+0x12  1  u8  insetR
+0x13  1  u8  insetB
```

**Cap rule CONFIRMED on all 18 samples** (valid nine-slice: `capL+capR < W` and
capT+capB < H, i.e. centre ≥ 1×1): e.g. 11×11→(5,5,5,5), 17×17→(8,8,8,8),
26×8→(3,3,22,4), 5×7→(2,0,2,0) (centre 1×7), 7×5→(0,2,0,2) (centre 7×1).
14/18 are "tight" (centre exactly 1×1); the 4 strips show the centre may be
larger — tightness is a property of those images, not a format requirement.
Slot 26×8 disambiguates the byte order: only `[L,T,R,B]` yields a valid
assignment (R=22 must be horizontal, B=4 vertical). This is the nine-patch
(9-slice) model: four corners + four edges copied fixed at draw time; the
centre region stretched to the widget size. All 18 extended blobs also carry
secondary-mode 1 (no secondary pixel buffer) — in v2 the geometry bytes
replace the v1 second row layer. The editor UI
(refs/screenshots/appearance-edit/app-beos/button-edit-uses-9patch.png)
exposes exactly these fields (Left/Right/Top/Bottom Cap Width/Height, Inset,
Transparent Color, Text Color, Transition Start/End). See
`11-widget-geometry-and-rendering.md` §2.

Corpus samples: 1/2/4/8 bpp all occur; W/H from 11×11 (built-in) to 280×1600
(Zurie_Constructicons_large); palettes 1–255.

## 7. Section D — colors

Writer: `FUN_004043D0` (v2); size: `FUN_004043C0` (returns 0xD8).
Readers: v1 `FUN_00404460`, v2 `FUN_00404410`; fallback `FUN_00404040` (built-in
default = D section of embedded blob B).

Document side: 54 color words at (doc+0x30)+0x58.

### 7.1 v1 (flag 0x7E = 1) — CONFIRMED

On disk: **204 × u32 LE color words** (D_size = 0x330 = 816; parser bound is
`word_index < D_size/4`). A built-in 54-byte table at `0x00463C7C` maps each of
the 54 UI color slots to a word index in the on-disk array; entries ≥ 204 leave
the slot at its built-in default value (loaded first via `FUN_00404040`).

So a v1 file carries a superset palette (204 words) and the *meaningful* 54
positions are selected by the editor-internal permutation table — the file cannot
express all 54 slots on its own (same class of constraint as §9.3).

### 7.2 v2 (flag 0x7E = 2) — CONFIRMED (code + built-in sample)

On disk: **54 × u32 color words, bytes `[00][RR][GG][BB]`** (D_size = 0xD8),
copied verbatim into the document (no permutation). Built-in sample
(Evil Chiaroscuro) first words, raw on-disk bytes:
`00000000 00666666 00333333 00111111 00ffffff 00ff0000 …` — a grayscale ramp
plus accent colors, consistent with the encoding below.

### 7.3 Color encoding — CONFIRMED (corrected R0-A.2 after OpenKDX audit)

**On-disk byte order: `[00][RR][GG][BB]`** — i.e. `00 RR GG BB` reading the
bytes left to right (equivalently the big-endian u32 `0x00RRGGBB`). Same in v1
(204-word) and v2 (54-word) D sections, and in C/%IKN palettes. Corpus
evidence: `BeOS.hap` D word 1 = `00 cc cc cc`; `Blue Fragmentation.hap`
D word 1 = `00 50 6f 9f` (R<G<B — blue, matches name); `Ashen.hap` D word 1
= `00 ff ff ff`; identical order in the built-in v2 blob. This matches
OpenKDX's `00 RR GG BB` (cross-reference/00-openkdx.md §3).

Derived forms (do not conflate):
- native little-endian x86 load of the 4 bytes = `0xBBGGRR00`
- in-memory **GDI 32bpp DIB pixel** = `0x00BBGGRR` (BI_RGB BGR, high byte
  0x00) — the only blit is `SetDIBitsToDevice` (BI_RGB 32bpp), so DIB pixels
  are GDI-ordered; a **bswap32** relates the on-disk load to the DIB pixel.

(The R0-A label "u32 LE value 0x00BBGGRR" was wrong: it stated the in-memory
GDI form as if it were the on-disk LE value.)

## 8. Section E — per-widget icons

Readers: v1 `FUN_00405310` + row fetcher `FUN_004048D0` + blob parser
`FUN_00404700`; v2 `FUN_00405210` + `%IKN` parser `FUN_0043F430`.
Writer (this build, v2 only): `FUN_00405120` (size: `FUN_004050B0`).

Document side: 34 entries (doc+0x34 + 0x54, 0x14 bytes each), each with a u16
table index at +0x10.

### 8.1 v1 (flag 0x7F = 1) — CONFIRMED (corpus + code)

```
+0x0000  0xC00   192 rows × 16 bytes:
               row i = [u32 BE offA][u32 BE offB][8 reserved]
+0x0C00  E_size - 0xC00   blob pool (E bitmaps, §8.4)
```

Minimum section size 0xC00 (parser requires > 0xBFF). `offA`/`offB` are
section-relative; 0 = empty. A row can hold up to two bitmaps (A = normal state,
B = alternate state — PROBABLE; the fetcher builds a 2-element composite record
`FUN_0043E390(ptrA, ptrB, key, 0)`).

**Corpus geometry (CONFIRMED, 31/31 files):** minimum non-zero offset is exactly
0xC00; blobs are contiguous; the last blob ends exactly at the section end.
Rows used: 1–95 only (per-row counts in `corpus-inventory.json`); rows 96–191
never used.

### 8.2 v2 (flag 0x7F = 2) — CONFIRMED (code + built-in sample)

```
+0x00  4   u32 BE count
+0x04  count × u32 BE offsets (0 = empty slot)
+0x04+count*4  pool of %IKN records (§10)
```

Slot i (u16) indexes the table directly; the blob at `table[i]` is a `%IKN`
record (not a raw bitmap). Built-in sample: count = 36, 35 non-empty, all parse
clean. Writer `FUN_00405120` produces exactly this layout and asserts
`pool_end == declared E size` (error 0x1000a on mismatch).

### 8.3 v1 row→widget mapping is editor-internal — CONFIRMED (critical)

`FUN_00405310` does not derive rows from the file. It uses two built-in tables:

| Table | VA | Shape | Shipped contents (LE u32) |
|---|---|---|---|
| widget map | 0x00464100 | 28 entries | ids 2,3 → row 0; ids 13,15,17,19,21,23,25,27 → rows 99,100,101,102,103,104,105,106; all other ids hold pointer-sized values (0x4649xx / 0x8xxxxx) that fail the `row < 192` check in `FUN_004048D0` |
| volume map | 0x004642E0 | 26 × (u32,u32) pairs | every first field pointer-sized (invalid); pairs 10 and 19 zeroed (→ row 0) |

Loop: for each of 34 doc slots, if `slot.u16 < 28` fetch row
`widget_map[slot.u16]`; then the 26 volume pairs are fetched into the volume
object (doc+0x38) via `FUN_004057D0`, finalized by `FUN_00405880`; both sub-objects
get flag 0x1000 set at +0x34.

**Consequence:** this build can only load rows 0 and 99–106 from a v1 E section.
No corpus file stores data there → **AppearanceEdit 1.400 renders no E icons from
any corpus file.** The v1 E content is a legacy payload from older editor builds
(different row map) and/or the Haxial runtime (unanalyzed). A reimplementation
must decide its own row→widget convention and treat 96–191 as reserved.

### 8.4 E bitmap (v1 pool blobs; parser `FUN_00404700`)

```
+0x00  2  u16 BE W
+0x02  2  u16 BE H
+0x04  1  flags: bit 0 = transparent-index valid
+0x05  1  bpp ∈ {1,2,4,8}
+0x06  1  palette count - 1
+0x07  1  transparent palette index (if flags bit 0)
+0x08  (pal+1) × 4  palette (colors §7.3)
+…     rowbytes(W,bpp) × H  pixels
```

Size = 8 + (pal+1)*4 + rowbytes*H (validated against remaining section bytes).
Corpus: 16×16/32×32 icons typical (rows 60–95 hold 16×16 A + 32×32 B pairs —
PROBABLE normal/pressed or small/large states).

## 9. Section F — ink resources (v2 only)

Reader: `FUN_00405F50` (size: `FUN_00405D60`); record parser `FUN_0043F430`;
sub-record parser `FUN_0043F2D0`. Enabled when flag 0x80 = 1.

```
+0x00  4   u32 BE count
+0x04  count × u32 BE offsets
+…     pool of %IKN records
```

Each `%IKN` record is appended to the document's ink/volume list (doc+0x38) in
table order via `FUN_004057D0`, then finalized by `FUN_00405880`. Built-in
sample: 25 records, path tags `data`, `font/`, `text/` — PROBABLE resource
categories (font/text/data assets). No corpus v1 file has an F section.

### 9.1 %IKN record (magic bytes 25 49 4B 4E)

```
+0x00  4   magic "%IKN"
+0x04  2   u16 BE version = 1
+0x06  1   N = path string length
+0x07  1   M = number of sub-records
+0x08  N (padded to 4)  path tag bytes ("data", "font/", "text/")
+((N+3)&~3)+8  M × 12-byte sub-record headers, packed
+…       payload pool (at per-sub-record chain offsets)
```

### 9.2 %IKN sub-record (12-byte header)

```
+0x00  2  u16 BE W
+0x02  2  u16 BE H
+0x04  1  flags: bits 0x1F = secondary mode (0/1 none; 2/4/8 extra rows at that bpp);
             bit 0 also enables a palette for 24bpp
+0x05  1  bpp ∈ {1, 2, 4, 8, 24}
+0x06  1  palette count - 1 (24bpp: counted only if flags bit 0)
+0x07  1  unused
+0x08  4  u32 BE chain offset = payload position within the record
payload (at chain offset):
       main rows: rowbytes(W,bpp)×H   (24bpp: row = ((W*3)+3)&~3)
       secondary rows (if mode 2/4/8): rowbytes(W,mode)×H
       palette: (pal+1)×4 (if applicable)
```

Parser validation: `payload <= remaining` and `chain + payload <= remaining`.
Built-in sample sub-records include 24bpp and paletted variants, all parse clean.

## 10. Section G — glyph images (v2 only)

Reader: `FUN_00408570` (size: `FUN_00408410`); record parser `FUN_004452C0`.
Enabled when flag 0x81 = 1.

```
+0x00  4   u32 BE slotCount
+0x04  slotCount × u32 BE offsets (0 = empty)
+…     pool of %MSI records
```

Document side: 18 entries (doc+0x3C + 0x54, 0x14 bytes each); entry.u16 (slot
index) < slotCount → parse `%MSI` at `table[slot]`. Writer side: slotCount =
(max used slot index + 1). Built-in sample: 20 slots, 19 non-empty, all 16–19
parse clean — small 2bpp glyph bitmaps (12×16 … 16×16, 4–8 colors), consistent
with a glyph/font-image store (PROBABLE: digits/counter/arrow glyphs used by the
volume widget).

### 10.1 %MSI record (magic bytes 25 4D 53 49)

```
+0x00  4   magic "%MSI"
+0x04  2   u16 BE version = 1
+0x06  1   W  (must be > Wmin, byte +0x0C)
+0x07  1   H  (must be > Hmin, byte +0x0D)
+0x08  4   reserved (zero)
+0x0C  1   Wmin (strict lower bound for W; purpose unconfirmed — HYPOTHESIS:
             min-size for a scalable glyph slot)
+0x0D  1   Hmin
+0x0E  1   format: 2 = 2bpp, 8 = 8bpp, 32 = 32bpp
+0x0F  1   palette count - 1 (formats 2/8 require ≥ 2 colors; 32bpp: unused)
+0x10  (pal+1)×4  palette (formats 2/8)
+…     pixels: rowbytes×H   (2bpp: ((W+15)&~15)>>2; 8bpp: (W+3)&~3; 32bpp: W*4)
```

Size = 0x10 + pal*4 + rowbytes*H, validated against the remaining section.

## 11. Reader/writer function map (AppearanceEdit.exe)

| Role | v1 | v2 | Address(es) |
|---|---|---|---|
| load entry (open → doc → parse) | both | both | 0x004036B0 (R0-A) |
| save entry (serialize → write) | — (writer emits v2) | both | 0x004033A0 (R0-A) |
| top-level parser | — | — | 0x00402900 |
| serializer (buffer builder) | — | — | 0x00402570 |
| Block A size | — | — | 0x004022E0 |
| Block A writer | — | — | 0x00402370 |
| C size / writer / reader | both | both | 0x00407000 / 0x00407030 / 0x004070F0 |
| C blob parser | both | both | 0x00406E20 |
| D size (0xD8) / writer | — | ✓ | 0x004043C0 / 0x004043D0 |
| D reader | 0x00404460 (permutation 0x463C7C) | 0x00404410 (direct) | fallback 0x00404040 |
| E size / writer | — | ✓ (0x00405120) | 0x004050B0 |
| E reader | 0x00405310 + 0x004048D0 + 0x00404700 | 0x00405210 + 0x0043F430 | |
| F size / writer / reader | — | ✓ | 0x00405D60 / 0x00405E10 / 0x00405F50 |
| %IKN / sub parsers | — | ✓ | 0x0043F430 / 0x0043F2D0 |
| G size / writer / reader | — | ✓ | 0x00408410 / 0x00408480 / 0x00408570 |
| %MSI parser | — | ✓ | 0x004452C0 |
| ink list add / finalize | both | both | 0x004057D0 / 0x00405880 |
| mem dup / copy | both | both | 0x0041BBF0 / 0x0041BB10 |
| FILETIME → string | both | both | 0x00434EC0 |
| label set text | both | both | 0x00409910 |
| option list get/set | both | both | 0x00411DF0 / 0x00411D80 |
| display resource setter | both | both | 0x004308D0 |

Built-in data: D-default loader 0x00404040 → embedded blob B (0x004683D4);
D permutation table 0x00463C7C; v1 E widget map 0x00464100; v1 E volume map
0x004642E0; embedded blob A 0x00466DD4 (no xrefs found — purpose HYPOTHESIS:
complete default skin used at build time / older path).

## 12. Endianness summary (recap of the trap)

| Data | On-disk order |
|---|---|
| header offsets/sizes/flags, all table entries | **big-endian** (code bswap32s) |
| version field | bytes `00 01` / `00 02` (BE u16) |
| color words (D, palettes) | **bytes `[00][RR][GG][BB]`** (= BE u32 0x00RRGGBB; native LE load 0xBBGGRR00; GDI DIB pixel = bswap = 0x00BBGGRR) — see §7.3 |
| bitmap W/H in blob headers | **big-endian u16** |
| pixel rows | native, MSB-first within bytes (standard) |
| %IKN/%MSI magic | bytes are the ASCII spelling (`%IKN`, `%MSI`, `%HAP`, `%FNT`) |

## 13. Evidence and confidence

| Claim | Level | Evidence |
|---|---|---|
| Header layout & flags | CONFIRMED | FUN_00402900 + FUN_00402570 + 111/111 corpus + 2 built-ins |
| Block A layout, 4-string mapping | CONFIRMED | FUN_00402900/0x00402370/0x004308D0 + corpus strings |
| C section + C blob format | CONFIRMED | FUN_004070F0/0x00406E20 + 38/38 corpus files |
| D v1 (204 words + 0x463C7C permutation + default fallback) | CONFIRMED | FUN_00404460 + table dump + 111/111 files |
| D v2 (54 words direct) | CONFIRMED | FUN_00404410 + writer + built-in blob A |
| Color encoding: on-disk `[00][RR][GG][BB]` (GDI DIB pixel 0x00BBGGRR) | CONFIRMED | raw corpus bytes (BeOS/Blue Fragmentation/Ashen) + built-in v2 blob + OpenKDX cross-check |
| E v1 192-row layout + pool geometry | CONFIRMED | FUN_004048D0 + 31/31 corpus files |
| E v2 [count][table][%IKN] | CONFIRMED | FUN_00405210/0x00405120 + built-in blob A (35/35) |
| v1 E row map is editor-internal; 1.400 loads nothing from corpus v1 E | CONFIRMED | FUN_00405310 disassembly + shipped tables + corpus row stats |
| %IKN record/sub-record format | CONFIRMED | FUN_0043F430/0x0043F2D0 + built-in blob A (25/25) |
| %MSI record format | CONFIRMED | FUN_004452C0 + built-in blob A (19/19) |
| Wmin/Hmin semantics (§10.1) | HYPOTHESIS | only "must be greater" constraint visible |
| E row A/B semantic (normal/alt state) | PROBABLE | composite 2-element record; no other candidate |
| option nibble = editor display setting | PROBABLE/HYPOTHESIS | mechanism CONFIRMED, widget content not yet mapped |
| timestamp-2 (A+8/A+12) = last save, rewritten on save; timestamp-1 = previous save from file | CONFIRMED | `hapSaveEntry` overwrites doc+0x1B0/0x1B4 with current FILETIME and refreshes doc+0x74 before serialize |
| F path tags `font/`,`text/`,`data/` = asset categories | PROBABLE | consistent tags + FontEdit linkage; not runtime-verified |
| pixel-row order inside C/%IKN payloads (main, secondary, palette) | PROBABLE | size checks only; corpus first-blob sanity |
| purpose of embedded blob A (no xrefs) | HYPOTHESIS | see §11 |

## 14. Open questions

1. **Runtime consumer**: does the Haxial runtime (not yet analyzed) use the v1 E
   rows 1–95 (i.e., a different/dynamic row map)? Needs the runtime executable.
2. **Wmin/Hmin** in %MSI — role in rendering (scalable glyph slots?).
3. **Option list content** (doc+0x78+0x38) — which editor settings are persisted.
4. **v1 writer**: no 192-row writer exists in this build (only the v2
   `[count][table]` writer). How were v1 files produced? (Older editor build —
   unanalyzed.)
5. **Embedded blob A** — find its consumer (possibly DDE/update mechanism or a
   path Ghidra didn't associate; the 5 xref sites of blob B are all documented).
6. **C preamble** (0x40 zero bytes) — reserved or version-dependent.
7. **doc+0x1B8** (header 0x08) — always 0 in all 123 files examined.
## Appendix: R0-A.3 additions/corrections

- %MSI field map **corrected**: +0x0C hotspotX, +0x0D hotspotY, +0x0E bpp (2/8/32), +0x0F palCount-1 (transColor out = palette[1]).
- Header directory word map (word idx, bytes): 0x2C A-cap(0x88), 0x30 A-size, 0x34/0x38 C off/size, 0x3C/0x40 D, 0x44/0x48 E, 0x4C/0x50 F, 0x54/0x58 G; Block A payload @0x88.
- C section: 64B (0x10-word) header before the 512-slot offset table (min size 0x840).
- F section records join the same runtime ink list as v1 E volume inks.
- v1 E rows may hold two blobs (layer A/B) → in-memory pair record (live surface pointers; storage bpp auto from palette size <3→1, <5→2, <17→4, <257→8, else 24).
- `dibInfoDecode` (0x41ccc0) decodes a classic Windows DIB (BITMAPINFO, BI_RGB, 24bpp or ≤8bpp+palette, negative height = bottom-up); the calls through 0x41c7xx–0x41d1xx are **import thunks (.idata IAT)**, not a provider-vtable object (S1 correction, doc 16 §3).

## Appendix: S1 corrections (2026-11-18, see docs 13–16)

- **§6 C-blob layout superseded** (doc 14): caps @+0x0C..+0x0F in the **base** header (always present); extended block = 12 B @+0x14 (extColour word @+0x14, content insets @+0x1D/0x1F); **palette precedes pixels**; blob size = hdr + rows + secondary + (pal+1)*4; hdr = 0x14 + (ext?0xC:0). `field0` @+0x08 / `field2` @+0x10 semantics unconfirmed.
- D section: 54 slots; editor role names in `gColorRoleNames` @0x461EC8 (53 named + 1 unnamed, doc 16 §1). Color encoding `[00][RR][GG][BB]` stands.
- E section: editor icon registry `gEIconNames` @0x462E70 (155 named slots, doc 16 §2); runtime install tracks E by base + byte length (`gInkTbl`/`gInkCount`), v2-only for rendering (doc 13).
- Scale: header bytes 0x0C/0x0D = gScaleNum/gScaleDen; 5×7 metric matrix @0x466994 = base bytes 0x46703B..0x46705A × num/den (doc 13 §1).
