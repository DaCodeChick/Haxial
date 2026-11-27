# 22 — C-Blob Rendering Pipeline (S2 Batch G)

**Target:** AppearanceEdit.exe (Haxial ApeeransEdit 1.400), x86 MSVC, image base 0x400000
**Session:** S2 Batch G — C-blob rendering pipeline: header field semantics, dispatch matrix,
corpus validation, editor part pipeline.
**Companion docs:** 04 (HAP format), 11/14 (S1 9-slice), 17 (§20 C-section lifecycle), 19 (widget geometry).

Confidence labels: **CONFIRMED** = verified by executable code and/or raw corpus bytes;
**PROBABLE** = strong code evidence, limited corroboration; **HYPOTHESIS** = inferred, unverified.

---

## 1. Scope

Batch G closed the last unresolved questions about the C-section "part" blobs:

- What are the two 32-bit header words S1 left unexplained (C-blob +0x08 and +0x10)?
- What does the 12-byte ext block (flags & 0x10) contain, and how is it rendered?
- Which renderer does each part go through, and how do the tiled vs plain paths differ?
- What is the low-level blit/sampling engine that the renderers sit on?
- How does the editor side (C-section writer/parser and the part-management functions
  0x406810/0x406BD0) treat these fields?

All renderers are in `.text` 0x425000–0x42AE00; the editor pipeline in 0x406800–0x407200.

---

## 2. C-blob file layout (CONFIRMED — code + corpus)

A C-section part is a self-contained image record. Layout (all offsets from the part base):

```
+0x00  u16BE  w                    source width in pixels
+0x02  u16BE  h                    source height in pixels
+0x04  u8     flags                see §2.1
+0x05  u8     bpp                  1, 2, 4 or 8 (file corpus); runtime DIBs add 16/25/32
+0x06  u8     palCountMinus1       palette entries - 1 (0 for true-colour 32bpp-style)
+0x07  u8     transIdx             transparent palette index (tiled path only)
+0x08  u32BE  clearColour  "field0"   surface clear/fill colour  (§2.2)
+0x0C  u8     capL               nine-patch cap: left column count
+0x0D  u8     capT               top row count
+0x0E  u8     capR               right column count
+0x0F  u8     capB               bottom row count
+0x10  u32BE  margins      "field2"   {marginL, marginT, marginR, marginB} bytes (§2.3)
--- ext block, present iff flags & 0x10 (§2.4) ---
+0x14  u8     extMode
+0x15  u8x3   gradColourA
+0x18  u8x3   gradColourB
+0x1B  u8     pad (0x00 in corpus)
+0x1C  u8x4   content insets {L, T, R, B}
--- pixel data ---
+0x20  palette (palCountMinus1+1 entries, size = palEntrySize per bpp) [then pixels]
```

Palette **precedes** pixels (S1, re-confirmed here: `cBlobHeaderDecode` sets
`palettePtr = cBlob+0x14`, or `cBlob+0x20` when the ext block is present, i.e. *after*
header + ext). `palCountMinus1` means palette entries = value + 1.

Row stride (file and runtime, identical formula, table @0x4576C4 / 0x45389C):
`stride = (w + (8/bpp - 1)) & ~(8/bpp - 1)` pixels → bytes per row
(bpp1: +7 & ~7; bpp2: +3 & ~3; bpp4: +1 & ~1; bpp8: w).

### 2.1 flags (CONFIRMED — corpus + code)

| bit | value | meaning | evidence |
|---|---|---|---|
| 0 | 0x01 | **tiled/transparency mode**: renderer uses `bmpBlitAlpha` + palette-sampled center (`partBlitRepeat[V]`); byte +0x07 is the transparent index | partDraw/partDrawV/nineSliceBlitC branch on `flags & 1`; 2232/4243 corpus parts (53%) set it |
| 4 | 0x10 | **ext block present** at +0x14 (12 bytes); decode advances pixel base past it; renderers call `extContentFill` for the center | cBlobHeaderDecode `palettePtr` jump; 18 corpus parts, all from the built-in v2 blob |
| 1,2,3 | 0x02/0x04/0x08 | secondary "row-bpp" encoding bits (`0x441F70` decodes 2/4/8-row groups) | **ZERO occurrences in corpus** (all 4243 parts in 39 files + built-in use only 0x00/0x01); code path exists but is unused by any known skin → HYPOTHESIS: dead or legacy |

No other flag bits are tested anywhere in the renderer/pipeline.

### 2.2 field0 = clearColour (CONFIRMED — code + corpus)

The u32BE word at +0x08 is a **colour**, stored in the standard HAP on-disk form
`[00][RR][GG][BB]` (doc 04/20 — GDI DIB pixel order). Consumers:

- `bmpSetCellState` (0x42A8C0) and `widgetBaseFill` (0x42A170): read
  `*(u32*)(part+8)`, split into byte/word, and call `extContentFill`-family fills with it —
  i.e. the part's background is **cleared/filled** with this colour before the part image
  is composited.
- `mbarDrawTitleItem` (0x42AC00): after painting the overlay part, sets the surface fill
  colour to the overlay part's field0 (`bmpSetFillModeRaw` + `bmpFillChecked`) and fills
  an inner rect — the same colour then drives the text/label overlay (0x426E00).
- `partRecordBuild` (0x406BD0) and `partToSkinDib` (0x406810): copy it **verbatim** into
  the runtime record (+0 / +8) — the editor never modifies it.
- `hapCSectionWrite` (0x407030) copies part blobs verbatim to disk — field0 is whatever
  the editor's part-construction code wrote.

Corpus: **100 distinct values** across 4243 parts. 0x00000000 (black / "no clear") is
dominant (3012 parts); 0x00FFFFFF (white) appears in 169 parts. Both are colour values,
not booleans — the earlier "flag?" reading is **DISPROVEN**.

### 2.3 field2 = margins {L,T,R,B} (CONFIRMED — code + corpus)

The u32BE at +0x10 is four one-byte margins. Consumers (each reads the individual bytes
and applies them as inset distances):

- `sldrPartLookup` (0x42BD00) — scrollbar part selection insets by margins.
- `sbarRectsCompute` — scrollbar geometry (doc 19).
- `labelMarkerDraw` (0x41E8A0).
- ~12 other painters (Batch D inventory).
- Editor: `partRecordBuild` copies byte-by-byte into the runtime record
  (out+0xD..+0x10 = src+0x10..+0x13); `partToSkinDib` copies byte0 into out+0x13 and,
  **when byte1 (top margin) != 0**, remaps the ext block: out+0x14..+0x15 ←
  ext(+0x18,+0x19), out+0x16 ← src(+0x11), out+0x17 ← src(+0x13), out+0x18 ← ext(+0x1A),
  out+0x19 ← src(+0x11) — i.e. the margin values are **folded into the gradient colours**
  of the runtime DIB (PROBABLE: gradient endpoints are re-anchored to the margin box).

Corpus: **215 distinct values**; non-zero margins concentrate in the scrollbar family
(part indices 146–177, 204–223) — consistent with the margin consumers being scrollbar
geometry. Field name in Ghidra: `margins` (bytes `marginL/T/R/B`).

### 2.4 ext block (CONFIRMED — code + corpus)

Present iff `flags & 0x10`. 12 bytes at +0x14:

```
+0x14  u8   mode      0 = none, 1 = horizontal gradient, 2 = vertical gradient
+0x15  u8   gradA[0]  gradient start R
+0x16  u8   gradA[1]  G
+0x17  u8   gradA[2]  B
+0x18  u8   gradB[0]  gradient end R
+0x19  u8   gradB[1]  G
+0x1A  u8   gradB[2]  B
+0x1B  u8   pad       0x00 in all 18 corpus ext parts
+0x1C  u8   insetL    content-rect insets (x offset, right subtract)
+0x1D  u8   insetT    (y offset)
+0x1E  u8   insetR    (width subtract)
+0x1F  u8   insetB    (height subtract)
```

**Rendering** (`extContentFill` 0x426830, called by partDraw / partDrawV / nineSliceBlitC):

- The content rect = dstQuad offset by `insetL`/`insetT` and shrunk by `insetR`/`insetB`.
- **mode 1**: for each column x in the content rect, `vlineAlpha(surface, y0, y1, x, c)`
  with `c = lerp(gradA, gradB, (x - x0) / w)` per channel — a left→right gradient.
- **mode 2**: per row, `hlineAlpha` with lerp top→bottom.
- mode 0 or others: no-op.
- Interpolation: per-channel `v = (dx * (B - A)) / w + A` (integer division).
- The gradient is drawn **before** the corner/edge blits in `nineSliceBlitC` (so cap
  pixels overdraw the gradient at the borders) and **before** the center blit in
  partDraw/partDrawV (center rows/columns of the source image overdraw it where opaque).

Corpus: 18 ext parts, all from the built-in v2 blob. Modes present: 1 (e.g. parts 110/111)
and 2 (e.g. SLDR part 122). No other mode values occur.

**Correction to S1/earlier notes:** the mode byte is at **+0x14** (first ext byte), not
+0x17 as previously recorded; colours are 3 bytes each starting +0x15/+0x18 (not a
u16BE "extColour" at +0x14 — that reading came from the 16-bit decompiler view and is
superseded).

---

## 3. cBlobHeaderDecode (0x429100) — CONFIRMED

Decodes the 20-byte header into a **32-byte runtime struct** (`cBlobDecode`, created in
Ghidra). Written fields (exact, from disassembly):

```
+0x00  w          bswap16(cBlob+0)
+0x04  h          bswap16(cBlob+2)
+0x08  bpp        cBlob+5
+0x0C  rowStride  (w + mask) & ~mask            (table @0x4576C4, idx = bpp-1;
                                                 1:7, 2:3, 4:1, 8:0, else 3)
+0x10  palCount   (cBlob+6) + 1
+0x14  rsv        0   (zero-init; non-part callers may set bit0 = 1bpp variant flag)
+0x18  pixelBase  cBlob + 0x20  (or +0x14 + 12*0 when no ext; i.e. palette end =
                                 header[20] + ext[12 if flags&0x10] + palette)
+0x1C  palettePtr cBlob + 0x14, or cBlob + 0x20 iff flags & 0x10
```

(Struct created zero-filled with `0x434420(0x20, out)`, so all other bytes are 0.)

**Not written by the decoder** (consumers read them directly from the part blob):
field0 clearColour (+0x08), margins (+0x10..+0x13), ext block (+0x14..+0x1F), flags,
transIdx. Ghidra structs `cBlobFileHeader` (20B) and `cBlobExtBlock` (12B) capture the
file side; `cBlobDecode` (32B) the runtime side.

S1's `hapDibSrc` (32B) is the **same struct** under an earlier name — `cBlobDecode`
supersedes it; `hapDibSrc` is retained in the DTM for continuity with docs 14/17.
S1's `appearancePart` (32B partial) described the first 0x14 bytes of exactly this
header; `cBlobFileHeader` supersedes it.

---

## 4. Renderer family (all CONFIRMED — disassembly)

All renderers take a skin surface, a dst quad/rect, and the C-blob pointer. They call
`cBlobHeaderDecode` first. "Tiled" = `flags & 1` path.

### 4.1 partDraw (0x429860) — horizontal 3-band

```
decode = cBlobHeaderDecode(cBlob)
if flags & 0x10: extContentFill(ctx, quad +(insetL, insetT) -(insetR, insetB),
                                mode=byte+0x14, colA3=+0x15.., colB3=+0x18..)
bands:  [x, x+capL) cap | [x+capL, x+w-capR) center | [x+w-capR, x+w) cap
tiled:   caps  = bmpBlitAlpha(mode = (transIdx << 24) | 1)
         center = partBlitRepeat(srcRow = capL, repeat = w)      // one source row, solid
plain:   caps  = bmpBlitToSurface
         center = nineSliceStretchH(srcRow = capL, repeat = w)
```

Callers: `sldrRender` (track + thumb), `bmpSetCellState`, 0x42CED0.

### 4.2 partDrawV (0x429A20) — vertical 3-band (renamed from FUN_00429a20)

Mirror image: rows capT | center | capB; tiled center = `partBlitRepeatV` (one source
**column** replicated as solid columns); plain center = `nineSliceStretchV`.
Callers: `sldrRender` (vertical track), `labelMarkerDraw`, 0x42CED0.

### 4.3 nineSliceBlitC (0x4293B0) — 9-region composite

```
decode = cBlobHeaderDecode
if flags & 0x10: extContentFill(contentRect, mode, colA, colB)
4 corners:  bmpBlitToSurface (plain) / bmpBlitAlpha (tiled, mode=(transIdx<<24)|1)
4 edges:    nineSliceStretchH/V (plain) / partBlitRepeat/V (tiled)
center:     colour = dibSamplePixel(Trans)(col=capL, row=capT, decode)
            bmpSetFillModeRaw(ctx, colour); bmpFillChecked(innerRect)   // solid fill
```

The center is **not** an image region: it samples the single pixel at (capL, capT)
(i.e. the inner corner of the 9-slice, first fully-interior pixel) and fills the whole
center rect with it. On the tiled path the same pixel goes through
`dibSamplePixelTrans` + manual palette map with transparent-index skip (→ transparent
center when that pixel is the trans index).

Callers: `mbarTitleBackground`, `mbarDrawTitleItem`, `bmpSetMetrics`,
`bmpSetCellState`, several widget painters.

### 4.4 partBlitRepeat (0x429220) / partBlitRepeatV (0x429320)

Tiled centers. `partBlitRepeat(surface, x0, y0, x1, decode, srcRow, a7, srcW, transIdx)`:
for i in 0..srcW-1: `c = palette[dibSamplePixelTrans(i, srcRow)]` (skip if `== transIdx`,
0 if index ≥ palCount); `hlineAlpha(surface, x0, y0+i, x1, c)`. `partBlitRepeatV` is the
column dual (`vlineAlpha`, rows rowStart..rowStart+rowCount-1). "Tiled" here means the
**solid rows/columns** produced by replicating one source row/column — not texture
tiling (that is `blitDecodeTiled`, §4.7).

### 4.5 nineSliceStretchH (0x429060?) / nineSliceStretchV

Plain centers: same loops but `dibSamplePixel` (raw colour, no trans handling) into
`hlineAlpha`/`vlineAlpha`. (Per-row solid fill from the source row — the S1 name
"stretch" refers to replication, not interpolation.)

### 4.6 extContentFill (0x426830)

See §2.4. Prototype (this batch): `(surface, contentRect{x,y,w,h}, mode, colourA3,
colourB3)` — callers pre-split the ext words (the `partDesc[5] & 0xff` /
`& 0xffffff00` split in partDraw's decompilation is the mode+gradA byte/word split).

### 4.7 blitDecodeTiled (0x426B20) — whole-blob tiling (renamed from FUN_00426b20)

Intersects dst with the surface clip, then:

- **w == 1 special case**: fill the rect row-by-row with the colour of source pixel
  (col 0, row cycled 0..h-1) via `hlineAlpha` — a 1-px-wide "stripe" source becomes
  horizontal stripes.
- **else**: blit the decoded source in blocks, stepping the source origin by (srcW, srcH)
  — genuine **texture tiling** of the whole part image across the rect.

Used as a **base layer** under the 3-band/9-slice renderers: `widgetBaseFill` (part idx
1), `bmpSetMetrics` (part idx 156), `bmpSetCellState`, `mbarTitleBackground` (255),
`mbarDrawTitleItem` (433/434/435).

### 4.8 hlineAlpha (0x425D30) / vlineAlpha (0x425F20)

Alpha line primitives on the 32bpp surface (stride surface+0x0C, base +0x18).
Colour low byte = alpha: **0 = opaque** (plain dword fill), **1..254 = blend**
`dst + round((src - dst) * a / 128)` per channel, **255 = no-op**. Clamped and clipped
to the surface rect. (The 128 divisor, not 255, is the engine's blend convention —
CONFIRMED by the `SHR 7` in the blend arithmetic.)

---

## 5. DIB blit engine (CONFIRMED — disassembly + tables)

### 5.1 Surface model

Skin surfaces carry a **magic 0xF4DA120B at offset +0x44** (validated by
`bmpBlitToSurface`/`bmpBlitAlpha` prologues). Rect fields used for clipping: +0x00 (x),
+0x04 (y), +0x20..+0x34 (clip bounds), +0x2C/+0x30 (height/stride related). Pixel base
+0x18, stride +0x0C (32bpp).

### 5.2 bmpBlitToSurface (0x427D80) / bmpBlitAlpha (0x427FD0)

Both: validate surface, compute clip intersection (0x425B20), dispatch on
`bpp-1` through a 32-entry table:

| table | @ | bpp1 | bpp2 | bpp4 | bpp8 | bpp16 | bpp25 | bpp32 | other |
|---|---|---|---|---|---|---|---|---|---|
| plain | 0x457548 | 0x427F8D | 0x427F6D | 0x427F4D | 0x427F2D | 0x427F10 | 0x427EF3 | 0x427EB0 | 0x427FB0 (err) |
| alpha | 0x4575CC | 0x4281CC | 0x4281A9 | 0x428186 | 0x428160 | 0x428140 | 0x428120 | 0x428100 | 0x4281F0 (err) |

Error path: `hErrorSimple(0x10002, ...)` (bad bpp).

- The **alpha table** targets are per-bpp call thunks into shared row-blit routines:
  1bpp → **0x450450** (the 1bpp row blitter — **shared with the font pipeline**: this is
  the function Batch F named `fontGlyphRowBlit3`; it is the DIB engine's 1bpp blitter
  *and* the ink glyph blitter, a genuinely shared primitive; rename deferred to preserve
  the Batch F family), 2 → 0x4508C0, 4 → 0x450C10, 8 → 0x450DC0, 16 → 0x451060,
  25 → 0x451110, 32 → 0x4511A0.
- The **plain table** targets are in-function paths of `bmpBlitToSurface` itself.
  The bpp1 path tests `decode+0x14 & 1` (the 1bpp variant flag — always 0 for part
  paths since the decode struct is zero-init; set by non-part callers) selecting
  0x44FC30 vs 0x44FB30.
- **25bpp is a real blit mode** (blit-only: the pixel samplers §5.3 have no 25bpp entry)
  — a quirk of the engine, not seen in the C-blob file corpus (file bpp ≤ 8).
- `modeWord` (7th arg of bmpBlitAlpha) = `(transIdx << 24) | 1` on all part call sites:
  bit0 = "transparency/mode" flag, byte3 = transparent index.

### 5.3 dibSamplePixel (0x4444A0) / dibSamplePixelTrans (0x4443D0)

Sample one pixel at **(col, row)** (col first — matches the callers' (x, y) usage):

- Bounds: `col < decode.w (+0x00)` and `row < decode.h (+0x04)`, else 0.
- Address: `pixelBase (+0x18) + row * rowStride (+0x0C) + col`.
- Dispatch (table 0x45A160 / 0x45A0DC, idx = bpp-1): 1bpp = 2px/byte MSB-first bit;
  2bpp = 4px/byte; 4bpp = 8px/byte; 8bpp = 1B; 16bpp = bswap16 then 555→888 expansion
  (tables 0x479B48/0x479BC8/0x479C48); 32bpp = raw. Others → 0.
- `dibSamplePixel` resolves palette indices (< palCount @+0x10, palette @+0x1C) to
  colour; out-of-range index → 0. `dibSamplePixelTrans` returns the **raw index** so
  callers can detect the transparent index before mapping.

---

## 6. Menu-bar title painters (CONFIRMED — disassembly + callers)

Both are called only from `mbarDrawTitles` (0x42EF60):

- **mbarTitleBackground** (0x42AB30, was FUN_0042ab30): two layers —
  part 255 (`gApp+0x43C`, fallback `g_appFallback`) → `cBlobHeaderDecode` +
  `blitDecodeTiled`; part 256 (`gApp+0x440`, fallback) → `nineSliceBlitC`.
  (Part 256 in the built-in is a 3×4 ext part — consistent with a gradient title band.)
- **mbarDrawTitleItem** (0x42AC00, was FUN_0042ac00): 3-state item painter.
  `state = *stateRec` (stateRec = {stateWord, a, b, c}):
  bit1 → base part **435** + overlay **263**; bit0 → base **434** + overlay **262**;
  else base **433** + overlay **261** (partOff indices). Base via
  `cBlobHeaderDecode` + `blitDecodeTiled`; overlay via `nineSliceBlitC`; then surface
  fill colour = overlay part **field0** (u32BE @+8) via `bmpSetFillModeRaw` +
  `bmpFillChecked` on the inner rect; finally 0x426E00 (text/label overlay, 6 args,
  incl. 0x30) using stateRec+4/+8/+0xC. The field0-as-text-background role here is
  further confirmation of §2.2.

Part-index → widget meaning for 255/256/261..263/433..435: PROBABLE menu-bar title
background / selected/pressed/hovered states; the full 175-entry part table mapping is
backlog G-4.

---

## 7. Editor-side part pipeline (CONFIRMED / PROBABLE)

### 7.1 File-side C section (recap, from doc 17 §20)

`hapCBlobParse` (0x406E20) validates a part blob (header sanity + size computation;
stride table 0x45389C; a secondary "mode" table 0x453878 selects per-bpp parse
variants). `hapCSectionRead` (0x4070F0) iterates **0xAF (175)** entries through the
partOff table; `hapCSectionWrite` (0x407030) and `hapCSectionSize` (0x407000) copy
blobs **verbatim** — the writer never touches field0/field2/ext. (v1/v2: the reader
handles both via the same entry table; corpus v1 parts obey the identical header.)

### 7.2 partRecordBuild (0x406BD0) — 32B runtime part record

`partRecordBuild(partSrc, size, outRecord32)`: requires `size >= 0x14`; zeroes a 32B
record and fills (exact):

```
+0x00  clearColour  = partSrc+8          (u32, verbatim)
+0x09  capL         = partSrc+0xC
+0x0A  capT         = partSrc+0xD
+0x0B  capR         = partSrc+0xE
+0x0C  capB         = partSrc+0xF
+0x0D  marginL      = partSrc+0x10       (field2 bytes, verbatim)
+0x0E  marginT      = partSrc+0x11
+0x0F  marginR      = partSrc+0x12
+0x10  marginB      = partSrc+0x13
+0x11..+0x1F  (w/h/flags/bpp/pixel ptr filled later in the function — partial decode)
```

`w`/`h` are bswap16'd into locals ([-0x18]/[-0x1C]) for the stride/pixel stage.
Ghidra struct `partRecord32` (32B, partial) captures the verified fields.

### 7.3 partToSkinDib (0x406810) — part → runtime skin DIB (PROBABLE)

Builds a runtime DIB record from a part source with the **margin remap** described in
§2.3 (ext bytes and margin bytes mixed into out+0x14..+0x19 when marginT != 0),
copies the pixel data (0x41BB10), detects bpp via 0x442050 (1/2/4/8), and finalises the
DIB through 0x441D80. Guard: `a2 == 0 → *outSize = 0, return 0`. Full decode (exact
record layout of the output, role of a2) is backlog G-2.

---

## 8. Evidence classification (per claim type)

| claim | verified by |
|---|---|
| header field offsets / widths / BE order | executable code (cBlobHeaderDecode, partRecordBuild, hapCBlobParse) |
| caps at +0x0C..+0x0F independent of ext flag | executable code |
| field0 = clear colour (not a flag) | executable code (3 consumer families) + corpus (100 distinct values, colour-like) |
| field2 = margins {L,T,R,B} | executable code (sldrPartLookup, sbarRectsCompute, ~12 painters, 2 editor fns) + corpus (non-zero concentration in scrollbar parts) |
| ext block layout + mode 1/2 gradients | executable code (extContentFill + partDraw/nineSliceBlitC call sites) + corpus (18 parts, raw bytes match) |
| flags bit0 = tiled/transpath, 0x10 = ext | executable code (branch sites) + corpus counts (2232/4243, 18) |
| flags bits 2/4/8 = secondary row-bpp | executable code only (0x441F70 path); **zero corpus occurrences** — dead/legacy unproven |
| stride formula | executable code (both tables) + corpus (cstat.py, 4243 parts, 0 errors) |
| palette precedes pixels | executable code (cBlobHeaderDecode pixelBase/palettePtr) + corpus |
| 9-region layout, center = sampled pixel solid fill | executable code (nineSliceBlitC) |
| tiled center = one source row/col replicated solid | executable code (partBlitRepeat/V) |
| whole-blob texture tiling (blitDecodeTiled) incl. w==1 stripes | executable code |
| alpha line convention (0 opaque / 1..254 blend /255 skip, /128) | executable code (SHR 7) |
| surface magic 0xF4DA120B, bpp dispatch incl. 25bpp | executable code + jump tables (raw) |
| 555→888 expansion tables, palette @+0x1C | executable code |
| mbar parts 255/256/433-435/261-263 roles | executable code (call sites, state word); semantic state names PROBABLE |
| editor never modifies part fields | executable code (hapCSectionWrite verbatim copy; partRecordBuild verbatim copies) |
| part → widget identity for all 175 entries | **not verified** (G-4) |

---

## 9. Ghidra enrichment applied this batch (verified by read-back)

**Functions renamed (9):** 0x429A20→partDrawV, 0x429320→partBlitRepeatV,
0x426B20→blitDecodeTiled, 0x425D30→hlineAlpha, 0x425F20→vlineAlpha,
0x42AB30→mbarTitleBackground, 0x42AC00→mbarDrawTitleItem,
0x406810→partToSkinDib, 0x406BD0→partRecordBuild.

**Prototypes set + verified (9):** partDrawV (3), partBlitRepeatV (9),
blitDecodeTiled (3), hlineAlpha (5), vlineAlpha (5), mbarTitleBackground (2),
mbarDrawTitleItem (3), partToSkinDib (3), partRecordBuild (3) — all parameter names
read back intact.

**Comments set/updated (21):** partDraw, partDrawV, nineSliceBlitC, extContentFill,
cBlobHeaderDecode, partBlitRepeat, partBlitRepeatV, nineSliceStretchH, nineSliceStretchV,
dibSamplePixel, dibSamplePixelTrans, bmpBlitToSurface, bmpBlitAlpha, blitDecodeTiled,
hlineAlpha, vlineAlpha, partRecordBuild, partToSkinDib, mbarTitleBackground,
mbarDrawTitleItem, fontGlyphRowBlit3 (dual-use note; name preserved).
Two prior comments contained stale S1 claims ("116B decode", "extColour u16BE @+0x14",
"body not yet decoded") — **corrected** in this batch.

**Structures created (4), then relocated to root DTM category:** cBlobFileHeader (20B),
cBlobExtBlock (12B), cBlobDecode (32B), partRecord32 (32B partial). Sizes verified by
read-back.

**Type application:** `cBlobDecode` → partDraw local_78 (the decode output) —
`set_local_variable_type` **succeeded** after moving the struct to the root category
("Retyped 'local_78' to cBlobDecode in partDraw") and the project was saved; the change
is persisted in the Ghidra project. Infer-based application
(`infer_structure_from_variable`) attempted on local_74 and local_78 and **failed**
("Failed to create structure from variable usage") — the decompiler represents the
struct as split scalar locals, so inference has no buffer to classify. Remaining
note: struct definitions are referenced from all comments; other consumers
(partDrawV, nineSliceBlitC, …) keep scalar locals (no regression risk).

**Not renamed (deliberate):** fontGlyphRowBlit1/2/3 (Batch F family names; 0x450450
dual-use documented instead). No GDT/archive types touched.

---

## 10. Backlog (G series)

| id | item | status |
|---|---|---|
| G-1 | modeWord full semantics for 16/25/32bpp alpha thunks (bit0 only proven at part call sites) | open |
| G-2 | partToSkinDib: exact output DIB record layout, role of a2, pixel-copy details | open |
| G-3 | 25bpp pixel layout (blit-only mode; no sampler) | open |
| G-4 | 175-entry part table: index → widget/state identity (255/256/261-263/433-435 PROBABLE mbar; rest unmapped) | open |
| G-5 | 0x42CED0 (third partDraw/partDrawV caller) identity | open |
| G-6 | 0x426E00 (mbar title text overlay) internals | open |
| G-7 | partRecord32 remaining fields (+0x04..+0x08, +0x11..+0x1F) — finish decoding 0x406BD0 | open |
| G-8 | flags 0x02/0x04/0x08: dead vs legacy — needs a corpus part or second build to exercise | open |
| G-9 | partDraw local_78 → cBlobDecode: **APPLIED** ("Retyped 'local_78' to cBlobDecode in partDraw") and project saved. | resolved |

---

*Batch G complete. Next: Batch V (final audit & readiness) — doc 22 is this document
(numbered per the S2 sequence; it is the 22nd research document).*
