# 11 — Widget Geometry and Skin Rendering (R0-A.2)

Program: `AppearanceEdit.exe` x86:LE:32 (image base `0x00400000`).
Evidence: disassembly/decompilation (addresses below) + corpus byte
analysis + committed screenshots (`refs/screenshots/appearance-edit/`,
see `10-visual-evidence.md`). Confidence tags per project convention.

## 1. Rendering architecture — CONFIRMED

**The only GDI32 import in the entire executable is `SetDIBitsToDevice`**
(full import list audited; no BitBlt, StretchBlt, CreateDIBSection,
SetDIBits, TextOut, DrawText, CreateFont, FillRect, or any other GDI
primitive). Consequences, all confirmed:

1. **Everything on screen is a 32bpp top-down DIB blit.** The blit
   descriptors found in code are a fixed 28-byte record:
   ```
   +0x00  u32  width (px)
   +0x04  u32  height (px)
   +0x08  u32  (unread by either blit; reserved)
   +0x0C  u32  stride (bytes)   ; biWidth is set to stride>>2
   +0x10  u32  (unread; reserved)
   +0x18  u32  pixel buffer ptr ; 0x00BBGGRR words, top-down
   ```
   The `BITMAPINFO` is built on the stack each blit: `biSize=0x28`,
   `biHeight = -height` (top-down), `biBitCount=32`, `biCompression=3`
   (BI_RGB), one dummy palette entry (0x00FF0000), `biClrUsed=0`.
2. **No scaling, no resizing, no alpha.** Both blits pass
   source w/h == dest w/h to `SetDIBitsToDevice`; the 0x00 alpha byte of
   each pixel is ignored by GDI (BI_RGB 32bpp). "Transparency" therefore
   works by *compositing*: widgets blit onto the window DC in z-order and
   transparent pixels are never emitted into the DIB in the first place
   (or are pre-merged against the parent's pixels by the DIB builder).
3. **No GDI text.** Text is rasterized into temporary bitmaps by the
   toolkit's own bitmap-font path (the corpus `.fnt` files — see
   `research/fonts/`); no font GDI calls exist.

### Blit functions
| Addr | Name | Role |
|---|---|---|
| `0x40CF50` | `winBlitDib` | Widget-window blit: validates magic `0xFE9778D` at widget+8, reads widget x/y as **two separate bytes** at widget+0x8B/+0x8C (so window position is 16-bit, one byte per axis), adds optional (dx,dy) offset, optionally clips to client rect when widget flag (+0x64) bit 8 is set (`GetClientRect` + intersect helpers `0x42E370`/`0x42DC90`/`0x4459E0`), `GetDC`/`SetDIBitsToDevice`/`ReleaseDC` |
| `0x40E4D0` | `dcBlitDib` | Bare HDC blit of the same descriptor at (x,y) — used off-window (e.g. popups, preview surfaces) |
| `0x40D160` | `widgetBlit` | `winBlitDib(widget, off, *desc)` + `FUN_00425880` (paint-context release). The five widget-type painters all blit through here |

### Widget painters (callers of `widgetBlit`)
`0x409FC0` (`labelPaint` — confirmed label object magic `0x5655D881`,
same as `labelSetText`), `0x410960`, `0x43BC00`, `0x4514C0`, `0x446770`
(button/tick/scroll/list family — individual decomposition deferred to the
UI-layer milestone).

### Label painting model (CONFIRMED, `labelPaint`)
For each text line (up to 8, from `FUN_0040ce90`):
create a temp `hapBitmapObj` of the line rectangle size → rasterize text
into it (plain fill + text via `FUN_00425C30`/`FUN_00426610`, or the
flagged path `FUN_0042A170`) → `widgetBlit` the line bitmap. Skin
resource selection: `FUN_004093E0(parent, 7, mode)` with mode 0/1/2/6
per widget state.

## 2. Nine-patch (9-slice) skin model — CONFIRMED

> **S1 correction (doc 14):** the caps live in the C-blob **base header**
> (+0x0C..+0x0F, always present) — not only in the extended block. Runtime
> algorithm: corners = exact copies; **edges = per-pixel nearest-neighbour
> replication of the 1-px source edge** (not texture stretch); centre (plain)
> = solid fill of the sampled centre colour; centre (ext) = ext content fill
> (coloured rect with insets @+0x1D/0x1F). Full spec: `14-s1-c-blob-and-9slice.md`.

**This is the generalized Haxial widget-stretching model** (the BeOS
look is one *appearance* using it; the mechanism is appearance-agnostic):

1. **Editor UI** (`button-edit-uses-9patch.png`, BeOS theme): the button
   image editor exposes exactly the 9-slice parameters — *Left/Right/Top/
   Bottom Cap Width*, *Left/Right/Top/Bottom Position*, *Transparent
   Color*, *Text Color*, *Transition (underneath)* (None + Start/End
   color), *Left/Right/Top/Bottom Inset*. The preview overlays the
   cap grid on the bitmap.
2. **On-disk**: the C-blob **extended header** (32 bytes, selected by
   header flags bit 4 = 0x10; parser `hapCBlobParse` @ `0x406E20`
   computes `hdr = 0x14 + (flags&0x10 ? 0xC : 0)`) carries 12 extra
   bytes after the standard 8-byte bitmap header. Decoded from the 18
   extended-header C blobs in the built-in v2 appearance (blob A):
   ```
   +0x08  u32  field0  ; 0x00FFFFFF or 0x00000000 in all samples
   +0x0C  u8  capL, u8 capT, u8 capR, u8 capB
   +0x10  u8  insetL, u8 insetT, u8 insetR, u8 insetB   (PROBABLE: content insets)
   ```
   **Cap arithmetic verified on every sample** (valid nine-slice: `capL+capR <
   W`, `capT+capB < H`, centre ≥ 1×1): 11×11 with caps (5,5,5,5), 17×17 with
   (8,8,8,8), 7×7 with (3,3,3,3), 5×5 with (2,2,2,2), 26×8 with
   (L3,T3,R22,B4), 5×7 with (2,0,2,0) → centre 1×7, 7×5 with (0,2,0,2) →
   centre 7×1. 14/18 samples are tight (centre exactly 1×1); the rest are
   strips. Byte order `[L,T,R,B]` is pinned by the 26×8 sample (only valid
   assignment). Edge/corner cells are copied fixed, the centre is stretched —
   the classic nine-patch.
3. **Corpus distribution**: 0/4101 C blobs in the 111-file v1 corpus use
   the extended header; **18/142** do in the built-in v2 appearance.
   → **Extended header (9-slice) is a v2 feature**; v1 widget bitmaps are
   plain (fixed-size) images. (Matches the v2-only writer.)
4. **Secondary-row linkage**: all 18 extended blobs have flags `0x11`
   (= 0x10 extended | secondary-mode 1), and mode 1 is precisely the
   "no secondary pixel buffer" mode of the v1 C-blob format. In v2 the
   stretch geometry *replaces* the v1 second pixel layer.
5. **Writer**: `hapCSectionWrite` (`0x407030`) is a pure pass-through
   (blob data is copied verbatim into the pool; 512-slot BE offset table
   at +0x40; min 0x840; exact-size assert 0x10001). The 12 geometry bytes
   are therefore emitted by the editor's image-save path (UI layer),
   consistent with the editor dialog fields above.

Rendering implication (PROBABLE, consistent with all evidence): at draw
time a widget sized (W',H') blits capL/capR/capT/capB pixels fixed from
the four edges/corners and stretches the center cell to
(W'−capL−capR, H'−capT−capB); content (text) is inset by the four inset
bytes; the "transition underneath" gradient (start/end colors) is drawn
into the DIB beneath the bitmap where applicable.

## 3. Widget geometry model — CONFIRMED structure, PROBABLE details

- Widget position in the **window** is byte-granular (x at +0x8B, y at
  +0x8C of the widget object) — the toolkit targets low-resolution
  16-bit positioning.
- Widget size is *not* stored in the DIB descriptor; each paint builds a
  descriptor sized to the computed geometry (the painter computes
  line/widget rectangles at runtime — see `labelPaint`'s per-line rects).
- **Scrollbar composition** (CONFIRMED visually, `vscrollbars.png`,
  `hscrollbars.png`): arrows (skin icons) at the ends, track (D color),
  thumb (skin) positioned by value; when the track height/width is too
  small the arrows are dropped entirely ("V Too Small" preview shows a
  bare box) — i.e. geometry is adaptive, resources are composable.
- **List box** (`misc.png`): column headers + rows + embedded
  single-size scrollbar; **progress bar**: D-color fill + numeric label;
  **slider**: track + movable thumb skin; **check state**: glyph prefix
  on label text; **focus/default state**: red outline ring drawn around
  the widget (built-in appearance) — state is an extra render layer,
  matching the C-blob state indexing (entry `tableIndex` → per-state
  512-slot pool).

## 4. D colors in rendering — PROBABLE

D section = 54 palette/role colors (04-hap-format.md §7). The red title
bars / focus rings / progress fills in the built-in appearance are
exactly D-role colors; widgets choose roles by index. The full
54-role mapping is a UI-layer milestone (needs per-widget decompilation).

## 5. Object magics observed (runtime)

| Magic (LE u32) | Object | Evidence |
|---|---|---|
| `0xFE9778D` | widget/window (blittable) | `winBlitDib` check at +8 |
| `0x5655D881` | label | `labelPaint` + `labelSetText` (R0-A.1) |
| `0x646F6B75` ("ukod") | hapDoc | `docCreate` (R0-A.2) |
| `0x83AF6F92` | string/display object | `displayResourceSet` (R0-A.1) |
| `0x51BD8891` | option list | `optionListGet` (R0-A.1) |

## 6. Open items (UI-layer milestone)

- Decompile the remaining 4 `widgetBlit` painters (0x410960, 0x43BC00,
  0x4514C0, 0x446770) → button/tick/scroll/list geometry math.
- Identify the DIB builder(s) that expand C/E/F bitmap objects
  (palette + transparency index + 9-slice) into 32bpp buffers —
  `FUN_00425C30`/`FUN_00426610`/`FUN_0042A170` neighborhood (0x425xxx–0x42E3xx).
- D 54-role table: per-widget color-role indices.
- "Transition (underneath)" gradient implementation (start/end colors).
- Field0 (u32 at C-blob ext +0x08): 0x00FFFFFF vs 0x00000000 — likely a
  default/backing color or a flag pair; needs more samples.
- The second u8 group (+0x10..+0x13): named "insets" per editor UI
  ("Left/Right/Top/Bottom Inset") — values 0 in most samples; one sample
  pair (5,0,5,0)/(0,5,0,5) on a 5×7/7×5 pair is consistent with insets
  but semantically odd (inset == full width); keep PROBABLE.
