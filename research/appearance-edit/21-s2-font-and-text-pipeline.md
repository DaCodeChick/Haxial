# 21 — S2 Batch F: Font and Text Pipeline

Target: `AppearanceEdit.exe` (Haxial AppearanceEdit 1.400, x86, image base 0x400000)
Status: **Batch F core complete** (F1–F6, F8 partial; F9/F10 done; F7/F8-remainder/F11 tracked below)

## 0. Executive summary

The Haxial text pipeline is a **pure bitmap-glyph system with no platform font
dependency**:

1. Fonts are serialized `.fnt` v2 blobs (64-byte header + 84-byte face slot +
   16-byte glyph records + 1bpp pixel pool). Four are embedded in the
   executable's `.data`; user fonts load from `.fnt` files and are installed as
   S2 runtime font objects (magic `0x6ABA021A`).
2. All text in the UI is **UTF-8** (code-CONFIRMED by a full 4-byte UTF-8
   decoder at `utf8ReadChar` 0x43B6F0).
3. Glyphs are 1bpp, MSB-first, row-based. Rendering targets a **1bpp
   intermediate surface** (per-line temp bitmap in `labelPaint`), then blits to
   the 32bpp DIB via the widget path. There are no GDI text calls, no TrueType,
   no ClearType: pixels only.
4. Metrics are **derived from glyph records** (ascent = reference record byte0;
   line height = byte0 + byte1), not from a separate metrics table.
5. The font module is exposed through the **module service-registry**
   (`fontServiceTable`, `{fn, serviceId}` pairs; font services
   0x0045B814–0x0045B859+), which is why font-related strings (e.g. "While
   loading font file: ") have no direct code xrefs.

Every claim below is tagged with its evidence class:
**[C]** verified by executable code · **[S]** verified by raw static data ·
**[R]** verified by corpus samples · **[I]** inferred, unverified.

---

## 1. The `.fnt` v2 on-disk format

### 1.1 Header (64 bytes) — [S][R] CONFIRMED

Verified against all 11 corpus files and all 4 embedded fonts (raw bytes
dumped for all 15). Previous session notes claiming an author pstr @+0x38
("Haxial") and a corpus-inventory note ("size @+0x08 is LE") are both
**corrected** by direct raw inspection: there is **no author field**
(+0x30..+0x3F are zero in all 15 fonts), and the size field is **
big-endian in all 15 fonts** (corpus + embedded pool, verified).

| Off | Size | Field | Notes |
|-----|------|-------|-------|
| 0x00 | 4 | magic `%FNT` (25 46 4E 54) | [S] |
| 0x04 | 2 | u16BE version = 2 | [S][R] |
| 0x06 | 1 | u8 flag (0 in all 15 fonts) | [S][R] |
| 0x07 | 1 | **u8 face count** (=1 in all 15) | [C] fntParseFace reads `byte[blob+0x07]` |
| 0x08 | 4 | u32BE total file size | [S][R] all 15 fonts |
| 0x0C | 12 | zeroed | [S][R] |
| 0x18 | 1 | u8 name_len (Pascal) | [S][R] |
| 0x19 | 47 | name bytes, zero-padded through 0x3F | [S][R] |
| 0x40 | — | font data begins (face slots @0xB8, rows @0x10C) | [S][C] |

### 1.2 Face slots (84 bytes each, starting @ blob+0xB8, stride 0x54) — [C][S][R] CONFIRMED

`fntParseFace` (0x44DEB0, fully decoded) iterates faces:
`face[i] @ 0xB8 + i*0x54`, `i` in `0..faceCount-1` (faceCount = blob+0x07).
If arg2 (a face-name pointer) is given, faces are matched by their **name
pstr at face+0x14** (via compare fn 0x4387E0); on no match face[0] is the
default. (All corpus fonts have faceCount = 1.)

| Off (in face) | Size | Field | Evidence |
|---|---|---|---|
| +0x00 | 11 | zeroed (all samples) | [S][R] |
| +0x0B | 1 | u8 record count of this face's table | [S][R][C] (read at +0xB) |
| +0x0C | 4 | u32BE glyph-table offset (= 0x10C in every sample) | [S][R][C] |
| +0x10 | 4 | zeroed | [S][R] |
| +0x14 | — | pstr face name (used for face selection) | [C] compare at +0x14; empty in all samples [S][R] |
| +0x24.. | 52 | zeroed (all samples) | [S][R] |

**Reference-record walk (fntParseFace tail, [C] CONFIRMED):** let `rec =
base + tableOff`, `n = count`. If n == 1: reference record = row 0. Else walk
`n-1` times: `if refChar <= byte[rec] break; rec += 0x18` (**stride 0x18 =
24**). On exit: `*out = byte[rec]` (first byte of the reference record) and
return `rec - base` (blob-relative record offset).

> Stride note: the reference walk uses 0x18 while the ASCII direct index
> (inkBlitCore) and the extended binary search (fontGlyphSearch) use 0x10.
> [C] Both verified in code. For face count == 1 (all 4 embedded fonts, and
> 7 of 11 corpus fonts) the walk is skipped entirely and record 0 is the
> reference record, so the mismatch has no observable effect there. For
> multi-record faces (Mjolnir n=2, Yspe Sans n=3, Von Yerk n=4, ...) the
> 0x18 stride enumerates a subsequence of the 16B rows — semantics
> unresolved. BACKLOG F-2. It does not affect rendered output for the
> built-ins (walk stops at record 0 for all embedded fonts because
> refChar ≥ record0.byte0).

### 1.3 Glyph records (16 bytes each, table @ 0x10C) — [S][R][C] layout CONFIRMED, field semantics partial

16-byte stride is CONFIRMED by three independent sources:
- `fontGlyphSearch` (0x44DF70): `mid * 16 + tableBase` [C]
- `inkBlitCore`: `base + char*16` for char < 0x100 [C]
- corpus structure: sequential u32BE tag at +0x0C matches record index in
  every file examined [S][R]

Layout (per-record):

| Off | Size | Field | Semantics | Confidence |
|-----|------|-------|-----------|------------|
| +0x00 | 4 | **record char** (byte0 = the char this row holds; 0 = empty row). For ASCII-indexed rows this is a single-byte char; for extended rows (≥ 0x100) all 4 bytes are consumed as a u32BE codepoint key by `fontGlyphSearch` (bswap) | [C] byte0 used by fntParseFace walk/metrics and refChar compare; [C] bswap(u32BE) used as binary-search key; 0-in-empty-rows [S][R] |
| +0x04 | 4 | u32BE **char ID** — `bswap` feeds the inkBlitCore budget guard (abort if `charID > budget` or `w*h + charID > budget`); equals the char value for ASCII rows in the corpus | [C] guard role; [S][R] value pattern |
| +0x08 | 1 | u8 | 0 in all samples examined; role INFERRED (width-ish) |
| +0x09 | 1 | u8 | 0 in most samples; role INFERRED (height-ish) |
| +0x0A | 1 | u8 | 0 in all samples; role INFERRED (x offset) |
| +0x0B | 1 | u8 | sequential row tag (== row index) in the ASCII region [S][R]; role PROBABLE (row/record index) |
| +0x0C | 4 | u32BE | **pixel data offset** into the blob (0 = none/inline); dual-use: first memory byte (MSB) consumed as pen-advance by inkBlitCore [C] | [S][R] CONFIRMED for "Lies 1.299": 34 offsets point at the contiguous 1bpp pool at 0x2AE4+; values > 0xFFFF are advances not offsets [S][R] |

**Table extent.** Code-verified structure: rows 0..0xFF (256) at
`tableBase + N*16` are the ASCII region (direct index by codepoint in
inkBlitCore for cp < 0x100). Rows 0x100 and beyond form the **extended
region**, searched by `fontGlyphSearch` (binary search, ascending
bswap-u32BE keys at row+0x00, range [0x100, cp-1]). The extended region's
record count is not stored in the face slot (that field is the reference-walk
record count, see F-2); its extent in the corpus files is delimited by the
pixel pool, whose first offset gives the upper bound. Row alignment in the
extended region shows a consistent 4-byte discrepancy vs the naive
`0x10C + 0x100*16` continuation in every file examined [S][R] — the extended
keys decode cleanly 4 bytes later (e.g. Lies row @0x1110+4 has plausible
small keys), suggesting the extended region starts at `tableBase + 0x1000 + 4`
or that 4 reserved bytes separate the regions. **Unresolved — BACKLOG F-2**
(needs the S2-object constructor code to settle, see F-1).

**Inline vs external pixel data.** Two storage modes observed in the corpus:
- **Inline**: leading bytes of +0x00..+0x0B hold 1bpp row bytes directly
  (≤12 bytes = 96 px/row). [S][R]
- **External**: +0x0C holds a u32BE offset into a **contiguous 1bpp pool** of
  variable-length glyph blocks (width_bytes × height rows, packed, no padding).
  Verified on Lies 1.299.fnt: offsets 0x2AE4, 0x2AF8, 0x2B0A, 0x2B1E, 0x2B26,
  ... differ by exact glyph sizes (0x14, 0x12, 0x14, 0x08, 0x03, 0x10, ...);
  decoded rows render recognizable 8×8 digit/letter shapes ('2','3','9','0'...).
  [S][R] CONFIRMED.

**Reference/metrics record.** `fntParseFace` walks records (stride 0x18 — see
§3) until record byte0 ≥ refChar and returns that record's offset. The first
record of each face carries the **metrics marker**: a control-char codepoint
whose *value* encodes the ascent. Examples [S][R]:

| Font | ref char | ascent (byte0) | descent (byte1) | line height |
|---|---|---|---|---|
| Myoklonika | 0x0F (SI) | 15 | 1 | 16 |
| Grand Mal g0 | 0x0C (FF) | 12 | 1 | 13 |
| Grand Mal g1 | 0x0F | 15 | 1 | 16 |
| Panitaka | 0x0C | 12 | 1 | 13 |
| Tonik-klonik | 0x0F | 15 | 1 | 16 |
| bit1 | 0x0D (CR) | 13 | 1 | 14 |
| End 0.9 | 0x12 | 18 | 1 | 19 |

The "ascent = char value" encoding is a [S][R] **HYPOTHESIS** (fits all 7
samples exactly; no code comment available). The byte0+byte1 = line-height
computation is [C] CONFIRMED (fontRecHeight, 0x44E5D0: `ret byte[a+b] +
byte[a+b+1]`).

---

## 2. Embedded fonts and the default font

Four complete `.fnt` v2 blobs are embedded in `.data`, **contiguous**
(pool 0x47B324–0x488AC0). Earlier session notes listed Grand Mal/Panitaka/
Tonik-klonik sizes as 0x184D/0xEC25/0x6828 — **corrected**: those were
byte-swapped artifacts. The size fields (plain u32BE) ARE the true sizes,
verified by exact pool-junction arithmetic [S] CONFIRMED:
`0x47B324 + 0x3C30 = 0x47EF54`; `0x47EF54 + 0x4D18 = 0x483C6C`;
`0x483C6C + 0x25EC = 0x486258` (all three junctions exact).

| Symbol | VA | Size (u32BE, verified) | Name |
|---|---|---|---|
| `fntMyoklonika` | 0x47B324 | 0x3C30 (15408) | Myoklonika |
| `fntGrandMal` | 0x47EF54 | 0x4D18 (19736) | Grand Mal |
| `fntPanitaka` | 0x483C6C | 0x25EC (9708) | Panitaka |
| `fntTonikKlonik` | 0x486258 | 0x2868 (10344) | Tonik-klonik |

All 4 parse cleanly with `fnt_inspect.py` at these sizes (194 pool offsets
each except Grand Mal's advance-only layout; pools within bounds).

- **`g_appFont` (0x46698C)** = default installed font blob pointer; set to
  `fntMyoklonika` at the tail of `skinInstall` (0x428C70) when NULL, together
  with **`g_appFontInit` (0x466990) = 0**. [C] CONFIRMED from disassembly.
- The font-chooser system-font list at 0x45F400 (e.g. "bel 15 - Gray") is the
  Windows face-name table used when the user picks a non-Haxial font; it is a
  separate mechanism from the embedded `.fnt` pool. [S]

---

## 3. `fontSelect` and font ID semantics — [C] CONFIRMED

`fontSelect(fontId, &glyphRecOff, refChar)` → font blob pointer (EAX).
0x44DDD0.

| fontId | Blob | refChar |
|---|---|---|
| 3 | Grand Mal | 0x0F |
| 4 | Grand Mal | 0x0C |
| 99 | Myoklonika | 0x0F |
| 100 | Myoklonika | 0x0C |
| 101 | Panitaka | 0x0F |
| 102 | Panitaka | 0x0C |
| 103 | Tonik-klonik | 0x0F |
| other | `g_appFont` | byte `g_appFontInit` |

The **reference char** selects *which* record of the face supplies metrics
(see §1.3): e.g. Grand Mal has two metric profiles (12/13 and 15/16) selected
by IDs 3 vs 4. The returned `glyphRecOff` is the record offset for the
reference char, computed by `fntParseFace` (0x44DEB0), which walks records
from the face table with **stride 0x18** comparing record byte0 against the
refChar. [C]

> Note the stride mismatch: the walk uses 0x18 while the binary search and
> direct index use 0x10. [C] Both observed in code. Interpretation: the walk
> enumerates a *subsequence* (every 1.5 records) or the reference record is
> addressed in a coarser stride than glyph rows — unresolved, BACKLOG F-2.
> It does not affect rendered output for the built-ins (walk stops at record 0
> for all 7 embedded fonts because refChar ≥ record0.byte0).

---

## 4. Character encoding: UTF-8 — [C] CONFIRMED

`utf8ReadChar(str, len, &consumed)` (0x43B6F0) is a complete, strict UTF-8
decoder:

- 1-byte: `b0 & 0x80 == 0` → codepoint = b0
- 2-byte: `0xC0–0xDF`; rejects overlongs (`0xC0`/`0xC1` lead → 0xFFFD)
- 3-byte: `0xE0–0xEF`; `0xE0` requires 2nd byte ≥ 0xA0
- 4-byte: `0xF0–0xF7`; `0xF0` requires 2nd byte ≥ 0x90, `0xF4` requires 2nd ≤ 0x8F
- invalid sequence / truncated at `len` → returns **0xFFFD**, consumes as far as valid
- `*consumed` = 1..4 on success, bytes consumed on error

Therefore **all UI strings in the text pipeline are UTF-8** (Batch F item 5
resolved by code, not corpus guesswork). The legacy encoding question is
closed for this executable; future Unicode support in the Rust reimplementation
inherits the same wire format naturally.

---

## 5. The runtime font object (S2) — [C] structure CONFIRMED, constructor BACKLOG

Font contexts passed to the metric/blit functions are either:
- a **blob pointer** (built-in / ID path), or
- an **S2 runtime font object** whose **+0x30 = 0x6ABA021A** (magic) and which
  carries two u32 values at **+0x34 / +0x38**.

`fontCtxWidth` (0x445E90) resolves both uniformly:
- ID path: `fontSelect` → (blob, recOff)
- object path: check magic at +0x30 → return `[obj+0x34]`, `*recOff = [obj+0x38]`

The two values then feed the exact same metric primitives as the built-in
path, i.e. **+0x34 = blob-equivalent base, +0x38 = reference-record
offset-equivalent** [C] by usage. The object therefore **retains references
into the serialized font data** (same pattern as the appearance object =
image pointer), rather than reconstructing an independent runtime font model.
[C] by behavior; the allocating constructor is not yet located (BACKLOG F-1).

---

## 6. Metrics — [C] CONFIRMED

| Function | Addr | Computes |
|---|---|---|
| `fontRecAscent` | 0x44E5C0 | `byte[blob + recOff]` — ascent |
| `fontRecHeight` | 0x44E5D0 | `byte[blob + recOff] + byte[blob + recOff + 1]` — line height |
| `fontAscent` | 0x446360 | `fontCtxWidth(ctx)` → `fontRecAscent(...)` |
| `fontLineHeight` | 0x446240 | `fontCtxWidth(ctx)` → `fontRecHeight(...)` |
| `fontCharWidthCore` | 0x44E4C0 | per-char advance (3-arg core) |
| `fontCharWidth` | 0x44E350 | wraps core (char, char, ctx) |
| `fontCharWidthOf` | 0x4460C0 | ctx/ID resolution + core |
| `fontCharWidthOf2` | 0x446130 | variant used by `bmpTextDraw` per-char advance |
| `fontFitWidth` | 0x4462A0 | **truncation/fit**: walks chars (utf8ReadChar + fontCharWidth), compares running width (with half-advance term, `SHR EAX,1`) against `maxW`; finds the fitting prefix |

The half-advance term in `fontFitWidth` (width += charWidth/2 during the
search, full compare at the end) is a right-bearing compensation: a string
"fits" when its advance plus half the last glyph's width ≤ maxW. [C]

No separate metrics table exists: **everything derives from glyph records**
(ascent/descent from the reference record; advances per-glyph at
+0x0C low byte). This answers Batch F item 2: the stored fields are char ID,
key, tag, and pixel offset; ascent/descent are *encoded in the reference
record's char value*, and per-glyph advance is the first memory byte (MSB) of the +0x0C field. The
"conventional typography" caution holds — these are not TTF-style metrics.

---

## 7. Text rendering pipeline — [C] CONFIRMED end-to-end

### 7.1 `inkBlitCore` (0x44DFE0) — the per-char glyph blit

`inkBlitCore(inkCtx, x, y, w, h, utf8String, len)` → chars drawn.
Let **base = row-array base** (a local set in the prologue from the surface
context; the exact base↔`0x10C`-table-offset relation is the open item in
F-2):

1. Loop while string remains:
2. `utf8ReadChar` → codepoint + consumed [C]
3. **slot lookup** [C]:
   - codepoint < 0x100 → `row = base + cp*16` (direct index)
   - codepoint ≥ 0x100 → `fontGlyphSearch(cp, &key, base)` (binary search,
     keys = bswap u32BE at row+0x00, range [0x100, cp-1]); NULL → default row
   - **default row = `base + 0x1A0` = row 13** [C]
4. **missing glyph**: `byte[row+0xC] == 0` and cp ≠ 0x0A → substitute default
   row (cp 0x0A keeps its blank row) [C]
5. **dimensions**: `w = byte[row+0x8]`, `h = byte[row+0x9]`,
   `x = byte[row+0xA]`, `y = byte[row+0xB]` [C]
6. **budget guard**: `charID = bswap(u32BE[row+0x4])`; if `charID > budget`
   (`[-0x48]`, prologue-set) or `w*h + charID > budget` → **RET** (abort
   string) [C] — degenerate/malicious font guard
7. **row blit** by height class: ≤8 → `fontGlyphRowBlit1` (0x44FE50), ≤16 →
   `fontGlyphRowBlit2` (0x450140), ≤24 → `fontGlyphRowBlit3` (0x450450); the
   row-data pointer combines `inkCtx + charID`, a y-base from surface+0x0C,
   per-row `rowBytes = (w+7)/8`, and surface stride `[arg2+0x18]` [C]
8. `x += byte[row+0xC]` (pen advance = first memory byte of the +0x0C field)
   [C]

**Advance / pool-offset dual use of the +0x0C field [C][S][R]:** the field is
a u32BE. Corpus evidence shows two usage classes:
- value ≤ 0xFFFF (hi16 = 0): a **pixel-pool offset** (e.g. Lies 0x2AE4, pool
  spans 0x2AE4–0x3233 for ASCII glyphs and 0x323D–0x40EB for the extended
  region); the advance byte (first memory byte) is then 0
- value > 0xFFFF: **not** an offset — the first byte is the pen advance
  (e.g. Mjolnir/Von Yerk rows carry `0C 00 00 00` = advance 12, `08 00 00 00`
  = advance 8, `03 00 00 00` = advance 3)

**Pixel-pool blocks [S][R] CONFIRMED (Lies 1.299):** contiguous 1bpp rows,
1 byte per row for ≤8px-wide glyphs (MSB-first), variable row count, no
per-row padding. First block @0x2AE4 (23 rows) decodes to a vertical dashed
line (dashes at rows 0, 6, 7, 10, 11, 12, 13, 15, 16, 21, 22) — a border
separator glyph. Later blocks decode to recognizable 8×8 digits ('2' @0x2BB0,
'9' @0x2BE8...). Pool glyph row-records carry w=0/h=0; the source of w/h for
pool glyphs (pool header vs row record) is unresolved — BACKLOG F-6.

**Remaining open items (exact evidence in F-2/F-6):** row-array base
([EBP-0x5C]) vs face table offset 0x10C; extended-region alignment (naive
`0x10C + 0x100*16` vs +4 — corpus keys decode 4 bytes off); w/h origin for
pool glyphs; inline-pixel rows (62–65 per font, bytes in +0x00..+0x0B) vs
pool rows. All rendering semantics above are code-CONFIRMED regardless.

### 7.2 `fontGlyphRowBlit1` (0x44FE50) — 1bpp row rasterizer

13-arg (plane, charRow, y1, x1, rowPtr, rowBytes, rows, width, rowStride,
pal1, pal2, state, mode). Confirmed behavior:
- destination is a **1bpp surface** (byte per pixel written) [C]
- palette = two colors behind a pointer (surface context field, quad+0x10)
  `{color0, color1}`; pixel mode = (arg1 & 1) ? arg1>>24 : match(color0)→0 /
  match(color1)→1 / other→2 [C]
- pixel test: `(row[x/8] >> (7 − x%8)) & 1 == mode` → **MSB-first 1bpp** [C]
- per row: `rowPtr += rowStride`, `charRow += yDelta`; rows ≤ 256 clamped [C]
- `0x444600` called twice per glyph with (0, color, rows, width) → produces
  the packed destination-color bytes (row-cache ID per (width, color) pair);
  internal semantics BACKLOG (F-4)

### 7.3 `bmpTextDraw` (0x427200) — high-level placement

6 params (surface, string, align, color?, ?, font). Confirmed:
- alignment modes: 0x20 = center (origin x = (w − stringWidth)/2), 0x08 =
  right; default left [C]
- baseline origin from surface context +0x20 (x) / +0x24 (y) [C]
- string width precomputed via `fontCtxWidth` [C]
- per-char advance via `fontCharWidthOf2`; glyphs blitted through
  `inkBlitCore` [C]
- right-edge termination: stops when pen x ≥ surface width [C]

### 7.4 Widget integration (S1-carryover, re-verified)

- `labelPaint` (0x409FC0): per-line temp 1bpp bitmap → text raster →
  `widgetBlit` to the 32bpp DIB (the "temp bitmap + text raster + widgetBlit"
  path from S1 doc 15) [C]
- `listRowFill` / `listRowPaint`, `bmpRowText`, `textWidgetGetRect`,
  `textWidgetStateGet`, `labelSetText`: text-widget plumbing, unchanged from
  S1 [C]
- `fontTextDraw` (0x424550) / `fontMetricsGet` (0x4230C0): higher-level
  font-driven text entry points (S1 inventory) [C names; per-parameter audit
  deferred — F-5]

**No GDI text APIs anywhere in the pipeline** — no `TextOut`, `DrawText`,
`ExtTextOut`, `CreateFont`. The entire text path is DIB blits. [C] by
negative IAT inspection (Batch E IAT verification covered GDI: only
`SetDIBitsToDevice` used on the skin path).

---

## 8. Service-registry exposure — **SUPERSEDED (Batch V correction)**

The Batch F identification of a `fontServiceTable` ID-dispatch registry at
0x45EA50 is **DISPROVEN** (V1, 2026-11-27). Batch F misread two unrelated data
regions as `{fnPtr, serviceId}` pairs:

1. **0x45EA48–0x45EAE0** is a `{name4cc, id}` table (19 entries, ids
   0x40..0x8C step 4) followed by a pstr pool of menu titles ("Information",
   "Colors", "Images", "Icons", "File Icons", "Mouse Icons", "New", "Open...",
   "Import Colors...", "Save", "Save As...", "Close", "Recent 1", "Recent 2",
   ...). No code xrefs, no stored pointer. PROBABLE: menu resource name/ID
   table (sample-menu icon names, bswap-stored FourCCs — "ofin"↔info,
   "lacs"↔scal). Ghidra label renamed `fontServiceTable` → `resNameIdTable`.
2. **0x45B7E0–0x45B8A0+** is a font data block: the four embedded font names
   as pstrs ("Myoklonika", "Tonik-klonik", "Grand Mal", "Panitaka"), followed
   by a mixed run of {code pointers (0x44F4xx font cluster), floats,
   self-pointers} — per-font metadata of undetermined structure (backlog
   V2-FDB; not implementation-blocking).

There is **no ID-dispatched font service registry** in this build: every font
function is directly called from the render path, and the "missing xrefs on
font strings" have a simpler explanation — the strings are data-block content
(not code-referenced) and "While loading font file: " (0x45A288) is a **dead
string with zero references** (no font-file loader in this build; see §14).

---

## 9. Batch F item-by-item status

| Item | Status |
|---|---|
| F1 .fnt on-disk format | **DONE** (header/face/rows/pool; face-count @+0x07 + face-slot structure code-corrected §1.2; extended-region alignment open in F-2; 3 row-field roles deferred in F-6) |
| F2 loader + runtime construction | **PARTIAL** — runtime object layout [C]; file loader not located (registry dispatch; BACKLOG F-1) |
| F3 glyph→ink binding | **DONE** — glyphs ARE the ink source: inkBlitCore reads record/pool directly into the 1bpp surface; no separate glyph-ink object. Shared representation confirmed (Batch F constraint satisfied: no invented abstraction). |
| F4 measurement/metrics | **DONE** (§6) — ascent/height/advance/fit/truncate all code-CONFIRMED |
| F5 encoding | **DONE** — UTF-8, strict, 0xFFFD fallback [C] |
| F6 rendering pipeline | **DONE** (§7) — 1bpp rows → 1bpp surface → 32bpp DIB |
| F7 layout/interaction | **PARTIAL** — placement (align/baseline/advance/right-edge) [C]; multi-line wrapping and text-widget edit interaction remain (S1 text-widget docs cover state; wrap logic not traced) |
| F8 scaling + appearance | **PARTIAL** — font scaling primitive: none observed (no scaleQuad usage in font path; geometry scaling ≠ font scaling constraint honored). Appearance integration: g_appFont via skinInstall [C]; per-appearance font selection not traced |
| F9 corpus validation utility | **DONE** (tools/research/fnt_inspect.py, see below) |
| F10 Ghidra enrichment | **DONE** — 24 renames, 9 prototypes, 8 comments (batch below) |
| F11 documentation | this document |

---

## 10. Ghidra mutations (this batch)

**Renames (24, all verified by read-back):**
functions: fontSelect, fntParseFace, fontGlyphSearch, utf8ReadChar,
fontCharWidth, fontCharWidthCore, fontRecAscent, fontRecHeight,
fontGlyphRowBlit1/2/3, fontCtxWidth, fontCharWidthOf, fontCharWidthOf2,
fontLineHeight, fontAscent, fontFitWidth
data: g_appFont (0x46698C, was DAT_0046698c), g_appFontInit (0x466990, was
gOnceFlag — disambiguated from gOncePtr), fntMyoklonika (0x47B324),
fntGrandMal (0x47EF54), fntPanitaka (0x483C6C), fntTonikKlonik (0x486258),
fontServiceTable (0x45EA50 anchor)

**Prototypes (9, applied):** fontSelect, utf8ReadChar, fontGlyphSearch,
fontRecAscent, fontRecHeight, fontCtxWidth, fontLineHeight, fontAscent,
fontFitWidth.

**Comments (8):** fontSelect, utf8ReadChar, fontGlyphSearch, inkBlitCore,
fontCtxWidth, fontRecAscent, fontRecHeight, fontGlyphRowBlit1.
(fontServiceTable is a data label; table documented here instead of as a
function comment.)

**Structures:** none new. Glyph records are deliberately NOT applied as a
Ghidra structure over the embedded blobs: 4 of 7 record fields have unverified
semantics (§1.3), and applying a partially-semantic structure would violate
the field-layout-vs-semantic-confidence separation. The layout is fully
documented here and in fnt_inspect.py. **Blocked (evidence), not deferred
sloppily.**

**Protected archives:** none encountered (no GDT types touched).

---

## 11. Call-graph coverage (Batch F scope)

Seeds: inkBlitCore, bmpTextDraw, labelPaint, fontMetricsGet, fontTextDraw,
g_appFont.
Visited/enriched this batch: fontSelect, fntParseFace, fontGlyphSearch,
utf8ReadChar, fontCharWidth(Core), fontRecAscent/Height, fontCtxWidth,
fontCharWidthOf(2), fontLineHeight, fontAscent, fontFitWidth,
fontGlyphRowBlit1 (2/3 listed, not fully disassembled), 0x44E470 (fit helper,
comment-only), 0x444600 (row-value, comment-only).
Already correct (S1): bmpTextDraw, labelPaint, listRowFill/Paint, bmpRowText,
textWidgetGetRect/StateGet, labelSetText, widgetBlit, fontTextDraw,
fontMetricsGet (names), widgetSendMsg.
Deferred/blocked: fontGlyphRowBlit2/3 full audit (variants of blit1, low risk);
0x44E470/0x444600 internals (BACKLOG F-4); S2 font object constructor
(BACKLOG F-1); service-table dispatcher (BACKLOG F-3); font-chooser UI
interaction (out of scope per Batch F boundary: "do not expand text layout
into a comprehensive unrelated widget investigation"); hap F-section
"font/standard" ink interaction (E3 backlog item 2).
Boundaries: GDI (verified absent from pipeline), Windows font API (chooser
only, separate mechanism), module service registry internals (cross-cutting,
own future batch).

---

## 12. Backlog (Batch F remainder)

| ID | Item | Why deferred |
|---|---|---|
| F-1 | ~~Locate the `.fnt` file loader~~ **RESOLVED (V1, §14.1)** — no .fnt loader exists in this build (dead error string, no ".fnt" extension string, built-in-only font refs) |
| F-2 | Reconcile (a) fntParseFace walk stride 0x18 vs 0x10 row stride; (b) the row-array base ([EBP-0x5C] in inkBlitCore) vs the face table offset 0x10C; (c) extended-region alignment (corpus keys decode 4 bytes off `0x10C + 0x100*16`) | OPEN — V1 next item; base origin and extended alignment only |
| F-3 | ~~Service-table full extent + ID dispatcher~~ **RESOLVED (V1, §8/§14.5, corrected)** — no ID-dispatched service registry exists in this build |
| F-4 | ~~0x444600 + 0x44E470 internals~~ **RESOLVED (V1, §14.3)** — 0x444600 = `paletteNearest` (decoded, call-verified); 0x44E470 = `fontCharWidthCore` (Batch F; the "fit helper" label was stale) |
| F-5 | fontTextDraw/fontMetricsGet per-parameter audit | S1-level names exist; full param/local gate for these two deferred to Batch V unless encountered |
| F-6 | Row fields +0x08..+0x0B exact roles (w/h/x/y — code-CONFIRMED as the dimension fields inkBlitCore reads); w/h source for pool-glyph records (w=0/h=0 in corpus); inline-pixel row semantics | Code reads them [C]; corpus values 0 in pool-glyph rows [S][R]; non-zero examples needed (font-editor write path) |
| F-7 | Multi-line text wrapping | Not traced; interaction layer beyond Batch F boundary |
| F-8 | ~~Per-appearance font selection~~ **RESOLVED (V1)** — the HAP directory has no font section (C/D/E/F/G only); font choice is application-level (fontSelect IDs + g_appFont default); nonblocking for S3 |

---

## 13. Uncertainties and explicit non-claims

- The ascent = reference-char-value encoding (§1.3) fits all samples but is
  not code-commented: **HYPOTHESIS** (computation itself CONFIRMED).
- The "author: Haxial @+0x38" claim from earlier session notes is **DISPROVEN
  by raw inspection** (all 15 fonts zero there); §1.1 corrected accordingly.
- Earlier embedded-font sizes 0x184D/0xEC25/0x6828 (from pre-Batch-F notes)
  were **byte-swap artifacts**; true sizes 0x4D18/0x25EC/0x2868 verified by
  pool-junction arithmetic (§2). The format is plain u32BE in all 15 fonts —
  no writer anomaly exists.
- ~~`fontServiceTable` anchor 0x45EA50 is mid-table; true start/end unknown.~~
  **RESOLVED (V1)** — no such table exists; §8 superseded.
- The S2 font object's fields before +0x30 (object head, vtable, size) are
  unknown — only the three consumed offsets are confirmed.
- No runtime rendering equivalence is claimed (no Haxial runtime executable
  available); all rendering claims are code-level.
- The 1bpp intermediate surface is per-line (labelPaint evidence); a
  whole-string surface for very long lines is not ruled out (F-7).
- Pixel rows are MSB-first; byte order of the *inline* 12-byte pixel area vs
  the external pool is identical (MSB-first in both, per blit1 code).
- Nothing here implies the modern implementation must keep 1bpp, UTF-8
  fallback 0xFFFD: these are legacy compatibility facts, not design mandates.

## 14. Batch V (V1) closure — font pipeline (2026-11-27)

### 14.1 F-1 — no external .fnt loader in this build [C]

Evidence (all negative-result, code + raw-data verified):

- String "While loading font file: " @0x45A288: **zero cross-references**
  (Ghidra xref query) and **zero stored pointers** (raw 32-bit LE scan of the
  whole PE). Dead string — the error path of a font-file loader that is not
  present in AppearanceEdit 1.400.
- No ".fnt" extension string exists anywhere in the binary (string search,
  case-sensitive: no matches). A font import dialog would need a filter
  string; there is none.
- The only font source pointers in .text are the four built-in blob addresses
  (0x47B324 Myoklonika, 0x47EF54 Grand Mal, 0x483C6C Panitaka, 0x486258
  Tonik-klonik), all referenced from `fontSelect` (ID table) — plus one
  Myoklonika reference at 0x4290ED inside `skinInstall`'s third block
  (the g_appFont default-font tail, Batch F).
- g_appFont (0x46698C) writers: **only** skinInstall (0x4290E7); readers:
  fontSelect (0x44DE70) and skinInstall.

**Conclusion:** fonts in this build = built-in blobs via fontSelect IDs +
g_appFont default. External .fnt loading is a capability of another Haxial
component (runtime/font module), not of the editor. For S3: `haxial-compat`
implements the .fnt *format* (from corpus + code); file-loading plumbing is a
modern design choice, not recovered behavior. Classification: **Resolved**
(negative result).

### 14.2 S2 font object — consumption-only interface [C]

The magic 0x6ABA021A appears in exactly ten sites, all in .text
0x445EBA–0x446386 = the metrics/width cluster (fontCtxWidth 0x445E90 and its
siblings fontCharWidthOf/Of2, fontLineHeight, fontFitWidth, fontAscent). The
object is **consumed** (magic check at +0x30, then +0x34/+0x38 read), never
**constructed** in this binary. The constructor lives in the external font
module (consistent with 14.1). Documented as a consumption-only interface;
object head (fields before +0x30) remains unknown (as in Batch F).

### 14.3 F-4 — paletteNearest (0x444600) decoded [C]

`paletteNearest(palette, count, targetColour, mode) -> best index` (or 0):

- Branch A (mode bit0 clear): per entry, d = |byte1(v)−byte1(t)| +
  |byte2(v)−byte2(t)| + |byte3(v)−byte3(t)| (u32 bytes 8..24; channel 0
  excluded); strict `< best` update, first hit wins ties.
- Branch B (mode bit0 set): adds |byte0(v)−byte0(t)| with a 0x1000
  zero-vs-nonzero penalty (transparency channel must match exactly).
- Convention verified at the blitRow1bpp call site (transparency index =
  nearest palette entry to 0x00000000, mode 0) — this is how DIBs obtain
  their transparent index.
- Callers: blitRow1bpp, pairRecordBuild, partToSkinDib, 0x441420, 0x4414D0.
- **Quirk (suspected latent original bug):** partToSkinDib's full-palette
  path (count ≥ 0x100, only reachable for 8bpp parts using all 256 entries)
  pushes `arr[0]` (a colour) in the `count` argument slot. Degenerate path;
  no corpus part triggers it. The Rust implementation should use the intended
  semantics (count = palette count) — see doc 23 quirk notes.

### 14.4 blitRow1bpp rename [C]

0x450450 renamed fontGlyphRowBlit3 → **blitRow1bpp**: it is both a font glyph
row rasterizer (inkBlitCore family, height ≤24) and the DIB engine's 1bpp row
blitter (jmp table 0x4575CC idx0). The font-only name was a misdescription.
fontGlyphRowBlit1/2 (font-only, height ≤8/≤16) keep their names; the family
split is documented in both docs and the ledger.

### 14.5 F-3 — correction of the Batch F service-table finding [C]

See §8 (superseded). The Batch F table of "serviceId → function" was a
misread of the 0x45B8xx font data block + 0x45EA48 menu name/ID table.
No dispatcher code exists; no pointer to either region exists; all font
functions are directly called. Ghidra label `fontServiceTable` renamed to
`resNameIdTable` (0x45EA50). The 0x45B820+ mixed block (pstrs → {code ptr,
float, ptr} runs) is backlog V2-FDB (font data block), nonblocking.
