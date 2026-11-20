# S1 — C-Blob Layout (Correction) and Nine-Slice Runtime Algorithm

Status: session S1. **This document supersedes the C-blob layout in
04-hap-format.md §C and the "caps only in ext header" model in
11-widget-geometry-and-rendering.md §2.** All byte offsets verified against
the built-in Evil Chiaroscuro v2 A blob (assets/builtin-EvilChiaroscuro-v2-A.hap)
and the reader `hapCBlobParse` (0x406E20) / blitter `nineSliceBlitC`
(0x4293B0).

## 1. C-blob on-disk layout (CONFIRMED)

```
+0x00  u16BE  width
+0x02  u16BE  height
+0x04  byte   flags:  0x10 = extended (9-slice capable); 0x0F = secondary-mode
                      (2/4/8 → extra pixel rows, purpose: secondary layer)
+0x05  byte   bpp: 1 / 2 / 4 / 8
+0x06  byte   paletteCount - 1
+0x07  byte   transparency index (used by ext blits)
+0x08  u32BE  field0  (observed 0x00FFFFFF or 0x00000000 — semantic unconfirmed)
+0x0C  byte   capL
+0x0D  byte   capT
+0x0E  byte   capR
+0x0F  byte   capB                       ← 9-slice caps ALWAYS present, in base header
+0x10  u32BE  field2  (0 in all samples)
+0x14  [extended block, present iff flags & 0x10, 12 bytes]
        +0x14  u16BE  extColour (fill colour for the content region, pre-multiplied input)
        +0x16  (2 bytes observed 0x00)
        +0x18  u32BE  field4
        +0x1C  (1 byte)
        +0x1D  byte   contentInsetTop  (centre fill top offset from capT)
        +0x1E  (1 byte)
        +0x1F  byte   contentInsetBottom (centre fill bottom inset from capB)
+hdr    hdr = 0x14 + (ext ? 0x0C : 0)
        palette: (paletteCount+1) × 4 bytes  [00][RR][GG][BB]   ← PALETTE BEFORE PIXELS
        pixels:  rowBytes × height; rowBytes = 32-px aligned @1bpp, 16 @2bpp, 8 @4bpp, 4 @8bpp
        secondary rows (iff sec-mode 2/4/8): rowBytes(mode) × height
```

**Corrections to earlier findings:**

1. **Caps live in the base header** (+0x0C..+0x0F), not only in the extended
   block. R0-A.2's "caps after ext header" model mis-attributed the base
   header's cap bytes; `cBlobHeaderDecode` (0x429100) reads them at fixed
   offsets regardless of the ext flag.
2. **Palette precedes pixels.** R0-A.2's "palette last" ordering was wrong:
   `hapCBlobParse` computes `size = hdr + rows + secondary + (pal+1)*4` with
   the palette block immediately after the header.
3. The 12-byte ext block starts at +0x14 (i.e., the caps at +0x0C..0x0F are
   *before* it, in the base header).

### 1.1 Tiling verification (CONFIRMED)

For built-in A, C section = 512-slot table @ section+0x40 (BE u32, **C-relative**
offsets) + entries; slots used by state-icon banks:

| slot | W×H | flags | bpp | pal | caps (L,T,R,B) | span (bytes) |
|---|---|---|---|---|---|---|
| 9 | 11×11 | 0x10 ext | 4 | 2 | 2,2,2,2 | 20+hdr' … (9-slice checkbox frame) |
| 10 | 8×8 | plain | 4 | 2 | — | exact |
| 11 | 8×8 | plain | 4 | 2 | — | exact |
| 21 | 17×17 | 0x10 ext | 4 | 2 | 3,3,3,3 | (disabled checkbox frame) |
| 22/23 | 14×14 | plain | 4 | 2 | — | exact |
| 33 | ext | 0x10 ext | 4 | 2 | — | 32+44+28 = 104 B exact |
| 34 | 7×7 | plain | 4 | 2 | — | 20+24+28 = 72 B exact to next slot |
| 35 | — | — | — | — | — | exact |

Every blob's computed size exactly tiles the table spans (no gaps, no
overlaps) — the layout above is byte-exact for the corpus's built-in
appearance. `field0`/`field2`/`field4` remain unconfirmed semantics.

## 2. Runtime nine-slice expansion (CONFIRMED)

`nineSliceBlitC(surface, dstRect, cBlobPtr)` @ 0x4293B0:

```
decode cBlobHeaderDecode → hapDibSrc {w, h, palCount, palette, pixels, ...}
if (flags & 0x10) extContentFill(surface, extColour, contentRect):
      contentRect = (x+capL, y+capT+insetTop, x+w-capR, y+h-capB-insetBottom)
      fill with extColour (word@+0x14) — via bmpFillChecked (fill colour
      taken from hapBitmapObj+0x38 = fillColor)

CORNERS (always, plain and ext):
  TL (x, y, capL, capT)                from (0, 0)
  TR (x+w-capR, y, capR, capT)         from (w-capR, 0)
  BL (x, y+h-capB, capL, capB)         from (0, h-capB)
  BR (x+w-capR, y+h-capB, capR, capB)  from (w-capR, h-capB)
  plain: bmpBlitToSurface (opaque copy)
  ext:   bmpBlitAlpha (transparent index = header byte +0x07)

EDGES (nearest-neighbour per-pixel replication — NOT texture stretch):
  top:    (x+capL, y, w-capL-capR, capT)      nineSliceStretchH from (capL, 0)
  bottom: (x+capL, y+h-capB, w-capL-capR, capB)  from (capL, h-capB)
  left:   (x, y+capT, capL, h-capT-capB)      nineSliceStretchV from (0, capT)
  right:  (x+w-capR, y+capT, capR, h-capT-capB) from (w-capR, capT)
  each destination pixel is filled with the colour sampled from the
  corresponding source edge pixel (dibSamplePixel); bands are drawn per-row
  (H) or per-column (V).

CENTRE:
  plain: fill with the single sampled centre-pixel colour
         (dibSamplePixel(w/2, h/2) → bmpSetFillModeRaw → bmpFillChecked)
  ext:   skipped (already filled by extContentFill, which respects the
         content insets)
```

**Corrections to R0-A.2:**

- "Edge = stretch texture" → **per-pixel replication of the one-pixel edge**
  (the edge band is replicated, so an 8px-tall source edge yields a flat
  band; there is no interpolation or texture repeat).
- "Centre = stretch" → **solid fill of the sampled centre colour** (plain)
  or the ext content fill (ext).
- `hapBitmapObj+0x38` is the **fill colour** (was named "fillMode" in R0-A.2;
  renamed `fillColor` in Ghidra).

### 2.1 Which widgets use which mode

- 9-slice (ext) blobs: checkbox/mutex frames (slots 9, 21), window/panel
  frames, slider thumbs, scrollbar arrows, button bevels — anything that
  must scale to arbitrary widget sizes while keeping pixel-exact corners.
- Plain blobs with non-zero caps: still run through `nineSliceBlitC` when
  the painter requests 9-slice mode; with caps 0 they degenerate to a single
  opaque blit (corners cover the whole rect).
- Plain blobs, centre fill: used where a flat interior is acceptable
  (small glyphs, tick marks).

## 3. State-icon banks (CONFIRMED)

`bmpStateIconDraw` (0x429F80) — checkbox/mutex glyph selection:

```
bank  = (state & 0x20) ? B : A          // disabled → bank B
slot  = bank base + (state & 0x02) * 1 + (state & 0x01) * 2
bank A base = C-table slot 9   (frame 11×11 9-slice) + variants 10, 11 (8×8)
bank B base = C-table slot 21  (frame 17×17 9-slice) + variants 22, 23 (14×14)
slot value = C-relative offset; if 0 → fallback:
    [gStyleDef] + 0x40 + slot*4        (built-in blob B's C table)
```

Combined with §2: the **frame** is a 9-slice ext blob (scaleable, transparent
index), the **tick/dash marks** are the plain variant blobs overpainted
centred. This matches the tick-buttons screenshot (doc 15 §5): checked =
frame + check mark; tristated = frame + dash; disabled = larger grey frame +
grey mark.

## 4. Remaining unknowns (this document's scope)

- Semantics of `field0` (+0x08), `field2` (+0x10), `field4` (ext +0x18).
- Secondary-mode (flags 2/4/8) extra-row content: PROBABLE alpha/specular
  overlay; no consumer examined yet.
- Whether `extColour` @+0x14 is used raw or combined with the D palette
  (it is a BE u16 — one channel or an index? unresolved).