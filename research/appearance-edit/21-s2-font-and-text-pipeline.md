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
| 0x40 | — | font data begins (face slot @0xB8; face blocks + row table @0x10C) | [S][C] |

### 1.2 Face slot (84 bytes @ blob+0xB8) and face blocks — **[CORRECTED, Batch V]**

`fntParseFace` (0x44DEB0, fully decoded, V1 re-verification) uses:
`face @ 0xB8` (faceCount = blob+0x07 is always 1 in all 15 fonts),
`count u8 @ face+0xB` = **number of 24-byte face blocks**, `table u32BE
@ face+0xC` (= 0x10C in every sample), face-name pstr @ face+0x14
(matched via compare fn 0x4387E0 when a name is given; empty in every
sample, so face[0] is always the default).

| Off (in face slot) | Size | Field | Evidence |
|---|---|---|---|
| +0x00 | 11 | zeroed / empty pstr (all samples) | [S][R] |
| +0x0B | 1 | u8 **face-block count** (size variants: 1, 2, 3 or 4) | [C][S][R] |
| +0x0C | 4 | u32BE face-block table offset (= 0x10C always) | [C][S][R] |
| +0x10 | 4 | zeroed | [S][R] |
| +0x14 | — | pstr face name (face selection; empty in all samples) | [C][S][R] |
| +0x34.. | — | zeroed (all samples) | [S][R] |

**Face blocks (24 bytes each, @ table + k*0x18, k = 0..count-1)** — one per
size variant of the font (e.g. Von Yerk: ascents 11/12/15/17): [C][S][R]

| Off | Field | Evidence |
|---|---|---|
| +0x00 | u8 **ascent** | [C] fntParseFace compare + store; [S][R] all fonts |
| +0x01 | u8 descent (= 1 in all samples) | [S][R] |
| +0x02 | u8 (= 1; role unverified) | [S][R] |
| +0x03 | u8 (= 0) | [S][R] |
| +0x04..+0x0F | three u32BE, zero in all samples | [S][R] |
| +0x10 | u32BE **rowCount D** (rows in this block's table; 256..584 in samples) | [C] passed as `hi` to fontGlyphSearch by inkBlitCore; [S][R] |
| +0x14 | u32BE **rowBase E** (blob-relative) | [C] `rowbase = ctx + bswap([ctx+recOff+0x14])` in inkBlitCore; [S][R] block0 = table + count*0x18, block k+1 = block k + 0x1000 (verified in all 7 multi-font samples) |

**Face-block walk (fntParseFace tail, [C] CONFIRMED, V1 corrected):** with
`n = count - 1`, `blk = blob + table`: if n > 0, walk `n-1` times max:
`while (reqHeight > byte[blk]) { blk += 0x18; }` — i.e. **0x18 stride
enumerates the 24B face blocks** (not glyph rows). Stops at the first block
with `ascent ≥ reqHeight`; `*out = ascent byte` and the function returns
`blk - blob` (**recOff** = face-block offset). The `reqHeight` argument
(Batch F "refChar") is the **requested face height**: fontSelect passes
12 or 15 (see §5 ID table); for count = 1 the walk is skipped and block 0
is returned (e.g. Myoklonika ascent 15). Batch F's "reference record
walk / refChar ≤ byte[rec]" wording is superseded: the compared byte is the
face block's ascent, and the stride-0x18 vs 0x10 mismatch (F-2a) is
explained — they enumerate different record classes.

### 1.3 Glyph row tables and 16-byte rows — **[CORRECTED, Batch V]**

Each face block owns one row table: **D rows of 16 bytes** at
`rowBase = blob + u32BE[faceBlock+0x14]` (D = u32BE[faceBlock+0x10]).
Row *i* is at `rowBase + i*16` and is indexed **directly by codepoint**
for i < 0x100; rows 0x100..D-1 are the extended region (binary search).
16-byte stride CONFIRMED by code (inkBlitCore `cp<<4`; fontGlyphSearch
`mid<<4`) and corpus (V1 corrected re-validation, all 15 fonts).

Layout (per row): [C][S][R]

| Off | Size | Field | Semantics | Confidence |
|-----|------|-------|-----------|------------|
| +0x00 | 4 | u32BE **key** | == row index for every sampled row; consumed by fontGlyphSearch as the binary-search key (bswap) for cp ≥ 0x100 | [C] search key; [S][R] key == i in all sampled rows |
| +0x04 | 4 | u32BE **poolOff** | 1bpp pixel-block offset into the blob; 0 = no glyph. inkBlitCore: `pixels = blob + poolOff`; guard `poolOff ≤ size && poolOff + w*h ≤ size` else abort | [C] inkBlitCore rows 0x44e1cd..0x44e205 + 0x44e28a; [S][R] |
| +0x08 | 1 | u8 **w** | glyph width (px); rowBytes = (w+7)>>3 | [C] |
| +0x09 | 1 | u8 **h** | glyph height (px) | [C] |
| +0x0A | 1 | u8 **xOff** | left bearing (added to penX) | [C] usage; [S][R] |
| +0x0B | 1 | u8 **yOff** | vertical bearing: draw y = penY + yOff (code: `[EBP-0x30] = byte[row+0xB] + penPos[4]`); values 1..5 in samples | [C][S][R] |
| +0x0C | 1 | u8 **adv** | pen advance (byte 0 of the u32BE slot; +0x0D..+0x0F zero in samples) | [C] `pen += byte[row+0xC]`; [S][R] |

**Batch F corrections (superseded claims):**
- "char ID @+0x04 … equal to the char value" — wrong: @+0x04 is the
  **pixel-pool offset**. Batch F's "budget guard = charID" is the
  poolOff size guard.
- "+0x0C dual use (≤0xFFFF = pool offset, else advance)" — wrong: @+0x0C is
  **always the advance byte**; the pool offset is @+0x04.
- "record count not stored" — wrong: stored at faceBlock+0x10 (D).
- "inline pixel data in +0x00..+0x0B" — **DISPROVEN**: inkBlitCore has no
  inline path; every drawn glyph is an external pool block (w=0/h=0 rows
  draw nothing). fnt_inspect's "inline" counts were an artifact of the
  naive row base.
- "4-byte extended-region alignment" — **artifact**: there is no separate
  extended region; rows 0x100..D-1 continue the same table. The apparent
  +4 decode came from the naive 0x10C row base (off by count*0x18 from the
  true base).
- "default row = base+0x1A0 = row 13" — row index **26** (0x1A0/16), a
  dedicated missing-glyph slot (cp 0x1A control-char position).
- "+0x0B = sequential row tag" — wrong: it is the **y bearing** (draw y =
  penY + yOff); values 1..5 in samples (not sequential).

**Row selection (inkBlitCore, [C] CONFIRMED, V1 full decode):**
```
cp < 0x100:  row = rowbase + cp*16
cp ≥ 0x100:  idx = fontGlyphSearch(cp, rowbase, D)   // binary search [0x100, D-1], key = bswap(u32BE[row+0])
             if idx == 0: row = rowbase + 0x1A0       // missing → default row 26
             else:        row = rowbase + idx*16
if byte[row+0xC] == 0 && cp != 0x0A: row = rowbase + 0x1A0   // blank/missing → default (cp 0x0A exempt)
poolOff = bswap(u32BE[row+4]); if poolOff > size || poolOff + w*h > size: abort string
blit pixels = blob + poolOff via blitRow1bpp family (height-class dispatch)
pen += byte[row+0xC]
```

**Pixel pool [S][R]:** contiguous 1bpp blocks (rowBytes × h, MSB-first,
no per-row padding) appended after the row tables (pool starts at
rowBase + D*16). Verified on Lies 1.299 (pool 0x2AE4+, offsets now read
from the chid/poolOff field @+4); the earlier "34 offsets" list is the same
pool, re-derived correctly in the V1 tool run.
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

No separate metrics table exists: **everything derives from face blocks and
glyph rows** (ascent/descent from the face block @+0/+1 via recOff;
advances per-glyph at row+0x0C). This answers Batch F item 2: the stored
fields are key, poolOff, w, h, x, tag, adv per row, plus ascent/descent/
rowCount/rowBase per face block. The "conventional typography" caution
holds — these are not TTF-style metrics.

---

## 7. Text rendering pipeline — [C] CONFIRMED end-to-end

### 7.1 `inkBlitCore` (0x44DFE0) — the per-char glyph blit **[V1 full decode]**

`inkBlitCore(blob, recOff, destSurf*, penPos*, clipRect*, string,
remainingLen, firstChar)` — **blits a whole UTF-8 string** (first char
supplied by the caller; the rest are walked internally via
utf8ReadChar 0x43B6F0, advancing `string` by the consumed bytes and
counting down `remainingLen`; loop terminates on remainingLen == 0 or
penX past the clip). **recOff** = face-block offset (from
`fontCtxWidth`/fontSelect → fntParseFace). Prologue: `size =
bswap(u32BE[blob+8])` (blob size = guard budget); `D =
bswap([blob+recOff+0x10])` (rowCount); `rowbase = blob +
bswap([blob+recOff+0x14])` [C].

1. **slot lookup** [C]:
   - cp < 0x100 → `row = rowbase + cp*16` (direct index)
   - cp ≥ 0x100 → `idx = fontGlyphSearch(cp, rowbase, D)` (binary search,
     keys = bswap u32BE at row+0x00, range [0x100, D-1]); idx == 0 →
     default row
   - **default row = `rowbase + 0x1A0` = row 26** (0x1A) [C]
2. **blank/missing**: `byte[row+0xC] == 0` (advance 0) and cp ≠ 0x0A →
   substitute default row (cp 0x0A keeps its blank row) [C]
3. **dimensions**: `w = byte[row+0x8]`, `h = byte[row+0x9]`,
   `xOff = byte[row+0xA]`, `yOff = byte[row+0xB]` (bearing; added to
   penY) [C]
4. **pool guard**: `poolOff = bswap(u32BE[row+0x4])`; if `poolOff > size`
   or `poolOff + w*h > size` → **RET** (abort string) [C] — degenerate /
   malicious font guard
5. **row blit**: pixels = `blob + poolOff`, via the blitRow1bpp family by
   height class: dispatch values {8,16,32} → `0x44FE50` (h≤8) / `0x450140`
   (h≤16) / `0x450450` (h≤24); per-row `rowBytes = (w+7)/8`, destination
   pixel buffer from `destSurf+0x18`, MSB-first [C]
6. `penX += byte[row+0xC]` (advance); draw position = penPos {x @+0, y @+4}
   + {xOff, yOff} [C]

**Superseded (Batch F):** the "+0x0C dual use (pool offset vs advance)"
model — @+0x0C is **always the advance byte**; the pool offset is @+0x04
(§1.3). The "row 13" default was row 26. The exact assignment site of the
dispatch local {8,16,32} was not isolated (value = 8·rowBytes class;
behavior verified at the three CALL sites) — cosmetic detail, nonblocking.

**Pixel-pool blocks [S][R] CONFIRMED (Lies 1.299):** contiguous 1bpp rows,
rowBytes × h per block (MSB-first), no per-row padding, appended after the
row tables. Batch F's pool addresses (0x2AE4+) are the same pool, now read
via poolOff @+4; the V1 tool run confirms in-bounds, ascending offsets for
all 15 fonts.

### 7.2 `fontGlyphRowBlit1` (0x44FE50) — 1bpp row rasterizer

13-arg (plane, charRow, y1, x1, rowPtr, rowBytes, rows, width, rowStride,
pal1, pal2, state, mode). Confirmed behavior:
- destination is a **1bpp surface** (byte per pixel written) [C]
- palette = two colors behind a pointer (surface context field, quad+0x10)
  `{color0, color1}`; pixel mode = (arg1 & 1) ? arg1>>24 : match(color0)→0 /
  match(color1)→1 / other→2 [C]
- pixel test: `(row[x/8] >> (7 − x%8)) & 1 == mode` → **MSB-first 1bpp** [C]
- per row: `rowPtr += rowStride`, `charRow += yDelta`; rows ≤ 256 clamped [C]
- `0x444600` = **paletteNearest** (Batch V F-4 decode, §14.3) called twice
  per glyph with (0, color, rows, width) → produces the packed
  destination-color bytes (row-cache per (width, color) pair) [C]

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
| F-2 | ~~(a) 0x18 vs 0x10 stride; (b) row-array base vs 0x10C; (c) extended-region alignment~~ **RESOLVED (V1, §1.2/§1.3/§14.6)** — 0x18 = face-block walk (24B blocks); rowbase = blob + u32BE[faceBlock+0x14]; rowCount D = u32BE[faceBlock+0x10]; no separate extended region (rows 0x100..D-1); default row 26; +0x0C = advance, poolOff @+4; "inline" mode disproven; fnt_inspect.py rewritten + revalidated (V1.4) |
| F-3 | ~~Service-table full extent + ID dispatcher~~ **RESOLVED (V1, §8/§14.5, corrected)** — no ID-dispatched service registry exists in this build |
| F-4 | ~~0x444600 + 0x44E470 internals~~ **RESOLVED (V1, §14.3)** — 0x444600 = `paletteNearest` (decoded, call-verified); 0x44E470 = `fontCharWidthCore` (Batch F; the "fit helper" label was stale) |
| F-5 | ~~fontTextDraw/fontMetricsGet per-parameter audit~~ **RESOLVED (V1, SS14.7)** — both fully decoded; named prototypes + fontCtxObj structure applied; labelWidgetFill named. Remaining detail: [ctx+0x34] blob-ptr-vs-count discrepancy (documented, nonblocking) |
| F-6 | ~~Row fields +0x08..+0x0B roles; w/h source; inline-pixel rows~~ **RESOLVED (V1, §14.6)** — +0x08 = w, +0x09 = h, +0x0A = xOff (bearing), +0x0B = yOff (vertical bearing; added to penY in inkBlitCore), +0x0C = adv, poolOff @+0x04; w/h come from the row itself (no pool header); "inline" mode disproven |
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

### 14.6 F-2 — record-layout reconstruction (row tables, face blocks) [C]

Full decode (2026-11-27, code + corpus): **the .fnt data region is NOT a
single 256-row table at 0x10C.** Structure:

```
blob+0x10C:  count × 24B face blocks          (one per size variant)
             block k: {ascent, descent, b2, b3, A=0, B=0, C=0, D=rowCount,
                       E=rowBase}
             block0.E = 0x10C + count*0x18
             block k.E = align4(pool end of face k-1)   (k ≥ 1)
blob+E:      D × 16B rows  (key = cp, direct index for cp < 0x100;
                           binary search for cp ≥ 0x100, range [0x100, D-1])
             row: {key u32BE, poolOff u32BE, w, h, xOff, yOff, adv, [3B pad]}
after rows:  1bpp pixel pool for THIS face: densely packed in ROW ORDER,
             block size = rowBytes*h (rowBytes = (w+7)>>3), MSB-first;
             (inkBlitCore's guard uses the looser poolOff + w*h ≤ size)
```

Code anchors: fntParseFace (block walk, stride 0x18, first ascent ≥
reqHeight, returns recOff + ascent); fontSelect (reqHeight = 12/15 per ID
table); inkBlitCore (rowbase = blob + bswap([blob+recOff+0x14]); D =
bswap([blob+recOff+0x10]); row selection + pool guard + blit dispatch +
advance); fontGlyphSearch (binary search [0x100, D-1] by bswap key, returns
row index or 0 → default row = rowbase+0x1A0 = **row 26**).

Corpus cross-check (all 15 fonts, V1.4 revalidation with the rewritten
tool): count ∈ {1,2,3,4}; D ∈ {256..1530}; block0.E invariant and the
align4(pool end) E-sequence hold in every multi-block font (Grand Mal,
Mjolnir, Von Yerk, Yspe Sans, Yspe Sans Bold); pool packing in row order
with size rowBytes*h verified per face (zero gaps/overlaps); poolOff
values in-bounds; advance bytes 1..17; w/h/x plausible per glyph
(spot-rendered 'A' in Harial 0.5 and Myoklonika: correct 7×9/8×9 shapes).

**Tooling correction:** `fnt_inspect.py` (Batch F) validated the naive
0x10C-base model; its "15/15 OK" was an artifact — its "pool offsets"
were misaligned windows overlapping true-row poolOff fields, and its
"inline" counts were non-zero key/w/h bytes, not pixels. The tool was
rewritten to the corrected model and re-run on all 15 fonts (V1.4).
**Any prior corpus statistics quoted from the old tool run (pool counts,
inline counts, extended-row alignments) are invalid** and must not be
reused.

### 14.7 F-5 — fontMetricsGet / fontTextDraw parameter gate + fontCtxObj [C]

**fontCtxObj** (magic **0x8521B2D1** @+0) — the widget-level font context
(16 dwords verified, 200B, Ghidra structure `fontCtxObj` created):

| Off | Field | Evidence |
|---|---|---|
| +0x00 | uint magic = 0x8521B2D1 | [C] fontMetricsGet 0x4230CF, fontTextDraw 0x424560 |
| +0x04..+0x0F | metrics[4] (label metrics; [1] @+8 = x origin for cell layout) | [C] fontMetricsGet copy loop; fontTextDraw baseX |
| +0x14 | charW (cell width) | [C] fontTextDraw 0x4245B4 |
| +0x18 | flags (bit 0x200 = start-col correction) | [C] fontTextDraw 0x4245E5 |
| +0x30 | S2 magic 0x6ABA021A (S2-font contexts) | [C] fontCtxWidth/fontAscent/fontLineHeight checks |
| +0x34 | blob pointer (metrics cluster) — see discrepancy | [C] fontAscent -> fontRecAscent(byte[blob+recOff]) |
| +0x38 | recOff (face-block offset) | [C] same |
| +0x3C | inkPtrs — per-column ink/color pointer array (cell-grid path) | [C] fontTextDraw 0x424693-0x424696 |
| +0x40 | inkCount (bound for inkPtrs) | [C] fontTextDraw 0x42468E |
| +0x50 | renderer — per-cell renderer **callback** (function pointer) | [C] fontTextDraw CALL [local_30] 0x4246BC |
| +0x54 | rendererCtx (passed to callback) | [C] fontTextDraw 0x4246B9 |
| +0xC4 | modeFlag byte (nonzero -> cellData \|= 0x100) | [C] fontTextDraw 0x4245C0-0x4245D0 |

**fontMetricsGet(fontCtx, outMetrics)** [C]: validates magic (hError
0x10019/0x4C/0xC6) + outMetrics non-NULL (hError 0x10002); copies
metrics[4] (16B). Single caller: labelWidgetFill (widget+8 = fontCtx).

**fontTextDraw(fontCtx, string, geom, reserved)** [C]: cell-grid text
renderer. geom = {+4: start column, +0xC: row-width bound}; reserved = 0 at
all 4 call sites (labelWidgetFill, 0x4214B0, 0x4150A0, 0x4218E0). Per
column: x = baseX + col*charW; ink = col < inkCount ? inkPtrs[col] : 0;
cellData = byte[s2Obj+col] | modeFlag; CALL renderer(geom, &metrics[0],
string, cellData, col, ink, rendererCtx); x += charW.

**Batch F "S2 object head unknown" — RESOLVED:** the 0x6ABA021A magic
@+0x30 / blob @+0x34 / recOff @+0x38 fields Batch F documented are the
**tail of fontCtxObj**, not a separate object; the head (+0..+0x2F:
wrapper magic + metrics + charW + flags) is now mapped.

**DISCREPANCY (open, nonblocking):** [ctx+0x34] is byte-indexed as a blob
pointer by the metrics cluster (fontAscent -> fontRecAscent) but used as a
small column count by fontTextDraw's cell-grid path (bounds compare at
0x424611, IMUL at 0x4245F1). For a pointer value those cell-grid usages are
dead (overflow/never-true); for a count the metrics path would be invalid.
Static resolution impossible (runtime-written field, no visible writer in
this binary); recorded as an explicit dual-interpretation. The Rust
implementation should pick one interpretation per context type (blob
pointer for the standard label font; the cell-grid path is a separate,
apparently legacy, feature).

**Ghidra (read-back verified):** fontCtxObj structure (root, 200B); named
prototypes fontMetricsGet/fontTextDraw/labelWidgetFill; comments on all
three. Parameter-name preservation: pre-mutation snapshot = auto param_N
(fontTextDraw) / Batch F names (fontMetricsGet: font, ?); no regressions on
read-back.