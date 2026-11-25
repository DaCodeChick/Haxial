# S2 Batch D — Widget Geometry, Scaling, and Appearance-Part Mapping

Status: session S2, Batch D deliverable. Consolidates the geometry-relevant
findings from doc 17 §16–§20 (detailed evidence there). This document is the
reference for the Rust reimplementation's geometry/skin-part model.

## 1. Coordinate spaces (CONFIRMED)

Four distinct representations, never conflated:

| Space | Where | Notes |
|---|---|---|
| **Serialized** (on-disk) | %VUU descriptors, .hap | BE structural words; raw geometry = 4 × i16/u16BE {x, y, w, h} at descriptor +0x04..+0x0B |
| **Widget raw** | widgetBase +0x0C..+0x1B | 4 × i32, sign-extended from the serialized u16s at instantiation |
| **Widget scaled** | widgetBase +0x1C..+0x27 | 4 × i32, = raw × scale factor via `scaleQuad 0x429C70`; all painting uses this |
| **Screen/client** | window + GDI calls | scaled quads offset into the window client area |

`scaleQuad(quad, quad)` (0x429C70) is the single scaling primitive:
- called by `widgetAllocInit` on the **window** outer geometry,
- called by `vuuPayloadParse` on the VWIN **client quad**,
- called by `widgetInstantiate` on every **widget** geometry
  (raw → +0x1C..+0x27),
- called on the VWIN client quad before `windowSetClientQuad`.

The scale factor itself (appearance-driven DPI/layout scale) is applied
inside scaleQuad; its source global is a Batch E item.

## 2. Window geometry (CONFIRMED — doc 17 §19)

`VWIN` root record = 40-B descriptor + window-own payload:

- outer geometry {x, y, w, h} @desc+0x04 (i16/u16BE; all x=y=0 in this build)
- window-own payload @R+0x28:
  - **client quad** u16BE[4] @wp+0x0C = {clientW, clientH, maxW, maxH}
    (prvw 360,340,360,340; doku 380,300,20000,20000; efik 430,246,1000,246;
    epxm 690,342,10000,10000; esik 430,246,430,246; emik 0×4 → skipped)
  - style u8 @wp+0x14 (2 = default for all six)
  - name pstr @wp+0x2C (titles: "Preview GUI Items", "Edit File Icon",
    "Edit Icon")
- `windowSetClientQuad(subObj, cW, cH, maxW, maxH)` applies the scaled
  client quad to the window sub-object.
- Window object: `windowObjBase` (40 B) + instance slot array; class =
  WIND (0x466188); magic 0x5655D881.

The client quad vs outer geometry difference (e.g. doku 380×400 outer,
380×300 client) is the **chrome reservation** (title bar, menu bar,
status area) — 100 px vertical for doku.

## 3. Widget geometry (CONFIRMED — doc 17 §16, §18)

`widgetBase` (56 B): raw quad +0x0C..+0x1B, scaled quad +0x1C..+0x27,
instCode +0x2C, flagsStored +0x30, state u16 +0x34, b36, flagByte +0x37.

- `widgetInstantiate` copies raw geometry, then scaleQuad → scaled.
- Paint dispatch (class+0x1C) receives the widget; painters read the
  **scaled** quad (e.g. `sldrPaint` passes `widget+0x1C` to `sldrRender`).
- `KNTR` children: child pointer array at widget+0x38, count +0x3C
  (array CONFIRMED).

## 4. HOLD anchors and scrollbar geometry (CONFIRMED — doc 17 §18.2, §19.5, §20.1)

- HOLD widgets start **hidden** (state bit3 cleared by `holdWidgetInit`);
  in prvw all HOLD records have empty payload → pure named geometry
  anchors (sbhd/sbhs/sbht/sbhi horizontal, sbvd/sbvs/sbvt/sbvi vertical,
  plus doku tab-page anchors).
- The app consumes them at construction: `sbarBindCreate(scrollbarWidget,
  anchor+0x0C /*&rawX*/, 0x100)` → 76-B `sbarBindObj` written back into
  the anchor slot; each bound object references the shared 196-B
  scrollbar controller (0x48E000, lazy init, 6 behavior fns).
- Default words in the bound object: 250/500/50/100 (semantics HYPOTHESIS:
  range/value pairs).

So the scrollbar demo's geometry flows: HOLD anchor scaled quad →
sbarBindObj (via &anchor->rawGeom) → scrollbar controller draws arrows/
thumb using appearance parts.

## 5. SLDR geometry (CONFIRMED — doc 17 §18.3, §18.5)

- value @+0x38, max @+0x3C (from payload, u32BE), computed cursor @+0x40.
- `sldrRender` takes the **corner-form** scaled quad {x1, y1, x2, y2};
  orientation from (x2−x1) vs (y2−y1): width > height → horizontal.
- `sldrPartLookup` picks parts by orientation + ticked flag from the
  appearance part table (horizontal: entries 0x72/0x76 (+4 ticked);
  vertical: 0x7E/0x82), dimension `A` = u16BE width/height of the part
  C-blob; margins from the part's field2 bytes.
- `sldrValueFromPointer`: pointer → value via float math
  (round((pt − start − margins)/trackLen × span) + min), clamped, with
  end-snap when the pointer is within `A` (thumb dimension) of an end.
  (Exact start/span terms incl. the vertical branch 0x42C070: D-late.)

## 6. Appearance part → C-blob mapping (CONFIRMED — doc 17 §20)

**An appearance part IS a C-blob** (doc 14 §1 layout):

```
part (via g_appCurrent + bswap32(partOff[i])):
  +0x00  u16BE width      (= slider dimension A)
  +0x02  u16BE height
  +0x04  flags  (0x10 = extended; low bits = secondary/tile mode)
  +0x05  bpp        +0x06  palCount-1     +0x07  transIdx
  +0x08  u32BE field0
  +0x0C  capL  +0x0D capT  +0x0E capR  +0x0F capB
  +0x10  u32BE field2  (= slider margins: u8 @+0x10 H, +0x11 V, +0x12 H2, +0x13 V2)
  +0x14  [ext iff flags&0x10] extColour u16BE, …, contentInsetTop @+0x1D,
          contentInsetBottom @+0x1F
  then palette (before pixels), then pixels — doc 14 §1
```

`partDraw(ctx, dstQuad, part)` (0x429860) renders one part:
1. `cBlobHeaderDecode` → surface,
2. extended → `extContentFill` (content rect inset by +0x1C..+0x1F),
3. flags & 1 → tiled/alpha path (`bmpBlitAlpha` + `partBlitRepeat`),
4. else → **horizontal 3-slice**: left band (width capL) `bmpBlitToSurface`,
   middle `nineSliceStretchH`, right band (width capR) `bmpBlitToSurface`.

Slider parts are 1-D elements (track, thumb) drawn by the 3-slice path;
2-D parts (button bevels, checkbox frames) use the full 3×3
`nineSliceBlitC` (doc 14 §2).

## 7. Rust-reimplementation implications

- Geometry pipeline: serialized u16s → i32 raw → scaled (one scaleQuad)
  → paint in scaled space. Keep raw and scaled separate (resize/repaint).
- Window model: outer geometry + reserved-chrome client quad + max sizes.
- Parts: a part is a 9-slice-capable image (C-blob) with an optional
  ext colour/insets; appearance = table of part offsets + per-widget-type
  part indices (track/thumb/arrow/band slots).
- Scrollbars: geometry anchors (named, hidden widgets) + a shared
  controller per process; bound object carries default range/value words.
- Message flow: value changes bubble to the parent's class+0x9C handler
  (widgetSendMsg, 44-B message, eventId 3 = slider value-changed).

## 8. Verification status

| Claim | Basis |
|---|---|
| 4-space coordinate model | code (widgetInstantiate, scaleQuad call sites) + raw descriptor bytes |
| VWIN outer/client geometry | code (vuuPayloadParse) + all 6 built-in payloads (static data) |
| HOLD hidden anchors + consumption | code (holdWidgetInit, sbarBindCreate, prvwCtor) + prvw payload |
| SLDR value/pointer math | code (sldrValueFromPointer) — start/span terms partially verified |
| part = C-blob | code (partDraw → cBlobHeaderDecode; sldrPartLookup field offsets) + doc 14 corpus verification |
| 3-slice standard part path | code (partDraw branches) + S1 nine-slice model |
| bound-object default words 250/500/50/100 | code (sbarBindCreate) — semantics HYPOTHESIS |

Open (D-late/E): scaleQuad factor source, sldrValueFromPointer vertical
branch, 0x408F10 bound-object ctor, sbarController's 6 fns, state bit
0x04 writer, mbarSlotGeometry 0x42EB30 internals.
