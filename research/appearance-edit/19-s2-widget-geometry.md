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

**Quad form note (CONFIRMED, D-late closure):** all widget-descriptor
quads (and the VWIN root's, identically stored) are **corner form**
{x1, y1, x2, y2}. `data/vuu-trees.txt` prints the 3rd/4th values as
"WxH" — that is x2×y2, not a width/height pair. Decisive evidence:
- prvw `sbvs` (250,110,266,236) = a 16×126 vertical strip in the 360×340
  preview window (as {x,y,w,h} it would be a 266×236 box — impossible);
  `sbhd` (10,30,350,46) = a 340×16 horizontal strip.
- doku `TXTS` "naam" (110,10,370,36): as {x,y,w,h} it would span
  x=110..480 in a 380-wide window — impossible; as corner form it is a
  260×26 field beside the "Name:" label — correct.
- doku `KNTR` "info" (0,30,380,400): as {x,y,w,h} it would end at
  y=430 in a 400-tall window; corner form fits exactly.
- code: the degenerate checks in sbarRectsCompute/sldrRender test
  quad[2]>quad[0] && quad[3]>quad[1] (corner-form emptiness).
`widgetInstantiate` copies desc+0x04..+0x0B verbatim (no x+w
conversion), so the corner form is the serialized form itself.

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
- The app consumes them at construction: `sbarBindCreate(parentWidget,
  anchor+0x0C /*&rawQuad*/, flags)` → 76-B `sbarBindObj` written back into
  the anchor slot; its classObj is the shared scrollbar CLASS object
  `g_sbarClass` (0x48E000, lazy init — a stateless method table built from
  the VUU! skeleton, NOT a stateful controller: D-late correction, §7).
- Default words in the bound object: **value=250, max=500, thumbNum=50,
  thumbDen=100** (CONFIRMED by code — thumb starts at half of track
  span; thumb length = half of track).

So the scrollbar demo's geometry flows: HOLD anchor raw quad →
sbarBindObj (raw + scaled quads, classObj = g_sbarClass) → hit-test and
pointer↔value math in `sbarRectsCompute`/`sbarValueFromPointer` → paint
via `labelMarkerDraw` with the appearance's scrollbar C-blob parts.

## 5. SLDR geometry (CONFIRMED — D-late closure, 2026-11-24)

### 5.1 Object and payload (CONFIRMED — sldrWidgetInit 0x438060, classSldr 0x467C48)

`classSldr` (magic 0x534C4452 "RDSL", size 0x44): +0x0C init, +0x1C
sldrPaint, +0x20 sldrEventPress, +0x24 sldrEventRelease, +0x28 attach,
+0x2C sldrEventMove.

`sldrWidgetInit(widget, …, payload, size≥0xC)` (called by
widgetInstantiate at 0x408A33 via class+0x0C):
- `widget+0x38 = bswap32(payload+0)` = **value** (u32BE)
- `widget+0x3C = bswap32(payload+4)` = **max** (u32BE)
- if `bswap32(payload+8) & 1`: `flagByte(+0x36) |= 0x20` (**ticked**)

prvw SLDR payloads (12 B each, raw bytes verified): all value=50,
max=100; ticked on v3/v4/h5/h6. `valueStruct` passed to paint/press =
`{flagByte(u32), value, max}` (built by sldrPaint 0x438160 and
sldrEventPress — both call sites verified).

### 5.2 Part dispatch (CONFIRMED — sldrRender 0x42B820)

- quad = scaled **corner form** {x1,y1,x2,y2}; empty (x2≤x1 || y2≤y1)
  → no-op; orientation = (x2−x1) > (y2−y1).
- `n = flagByte & 0x23` (35 cases; jump tables 0x4577C4 horiz /
  0x457738 vert):
  - horiz (track, thumb): n=1:(0x70,0x78) n=2:(0x6F,0x77) n=3:(0x6E,0x76)
    n=4:(0x70,0x74) n=5:(0x6F,0x73) else:(0x6E,0x72)
  - vert (track, thumb): n=1:(0x7C,0x84) n=2:(0x7B,0x83) n=3:(0x7A,0x82)
    n=4:(0x7C,0x80) n=5:(0x7B,0x7F) else:(0x7A,0x7E)
- partPtr = `gApp + bswap32(partOff[idx])` (table @gApp+0x40); if the
  offset is 0, retry with `g_appFallback` (doc 17 §18.5).
- Built-in part dims (blob B C-section slot values, raw bytes read this
  session): track h 110 = 5×7 ext caps(2,0,2,0) **insets(5,0,5,0)**;
  thumb h 114 = 14×16; track v 122 = 7×5 ext caps(0,2,0,2)
  insets(0,5,0,5); thumb v 126 = 16×14; the 112–116/118–120/124/128–130
  groups are the other states/ticked variants (14×16 or 16×14 thumbs).

### 5.3 Render geometry (CONFIRMED from disassembly; anomaly in §5.5)

Horizontal (w > h):
- track: `partDraw(ctx, &{x1, (y1+y2−partH)/2, x2, (y1+y2+partH)/2}, trackPart)`
  — full-width strip, partH = bswap16(part+2), vertically centered.
- `trackLen = (x2−x1) − (thumbW + trackPart[0x10] + trackPart[0x12])`;
  if `trackLen < 0` the thumb is skipped.
- thumb term: `term = FIST(trackLen × max / value)` (x87 double math +
  FIST banker's rounding; the trailing FST/FSUBP/ADD/SBB "correction"
  idiom is a **proven no-op** — dead code for all reachable fractions)
  when `value < max`; else `term = trackLen`.
- thumb: `partBlitAt(ctx, x1 + trackPart[0x10] + term, (y1+y2−thumbH)/2 − thumbPart[0x11], thumbPart)`
  (partBlitAt 0x429BE0 — generic 14-call-site blit-at-point primitive).

Vertical (h ≥ w): mirrored. Track via 0x429A20 (vertical partDraw) at
horizontal center `(x1+x2−thumbW)/2`… (track part 122: 7 wide × 5 tall,
insets 0,5,0,5). `trackLen = (y2−y1) − (thumbH + trackPart[0x10] + trackPart[0x12])`.
Thumb: `partBlitAt(ctx, centerX − thumbPart[0x10] …, y2 − thumbPart[0x13] − term − thumbH − …, thumbPart)`
with the **same** `term = FIST(trackLen × max / value)` (value<max) —
vertical branch 0x42BC6F–0x42BCD1 disassembly-matched to the horizontal.

### 5.4 Pointer → value (CONFIRMED — sldrPointerToValue 0x42C150)

Called by sldrEventPress (via sldrValueFromPointer's else path, with
half-band `outC/2`) and **directly** by sldrEventMove (with
`grabOffset = widget+0x40`, the press-time offset).

- Re-derives outA/outB/outC via sldrPartLookup (appearance part bytes;
  fallback defaults 5/5/13 or 5/5/15 when ticked).
- Horizontal: `p = *ptPtr`; bounds `[x1+outC, x2−outB−outA]`; if
  `p − grab ≤ lo` → **0**; if `p − grab ≥ hi` → **max**; else
  `round((p − grab − lo) × max / (hi − lo))` (x87 double + dtoiRound).
- Vertical: pointer y is at `ptPtr+4`; the half-band is **negated**
  (−outC/2); bounds mirror from the top (`y2−outB`, `y1+outC+outA`);
  value increases toward the top. Same value math, clamped to [0, max].

`sldrValueFromPointer` (0x42BF20) adds the snap layer: `computed =
x1 + outA + FIST(trackLen′ × max / value)` (same term as render, §5.5);
if `computed ≤ *pt < computed + outC` the pointer is "on the thumb" →
*out = old value (no change); else *out = sldrPointerToValue(…, outC/2).
Return = `*pt − computed` (or outC/2) → widget+0x40 (drag anchor).

### 5.5 The max/value anomaly (OPEN — code CONFIRMED, runtime unverified)

The render term and the snap "computed" position use **max/value**, not
value/max. For any value < max the term exceeds trackLen, so the thumb
is placed **past the right (top) track end — outside the widget** (built-in
50/100 → 2×trackLen). Verified four independent ways: Ghidra
disassembly, manual byte decode of 0x42BA4E–0x42BA77 (DF F1 = FDIVRP
on [value, max] → max/value), the vertical branch (identical), and the
proven-dead correction idiom. The press mapping (§5.4) is the normal
value/max mapping — so **render and press are asymmetric in the
original**.

Screenshot cross-check (ui-builtintheme/sliders.png, post-interaction
prvw state, pixel-level analysis this session): the h3 thumb sits at
the track's right end (the value≥max render position under either
reading); the v1 thumb sits mid-track, a position only the value/max
mapping can produce (implied value ≈ 1/3 — reachable by drag), which
the code's max/value term cannot produce for any value ≤ 100 (it would
need value ≈ 300, unreachable — the press clamps to [0, max]).

Unresolved: (a) post-interaction values are unknown without a runtime
capture; (b) the screenshot may predate the analyzed build. Recorded as
the batch's open item — a runtime trace (or a second build) is the
cheapest resolution. Per the D-late constraint, the slider geometry is
**not** marked implementation-ready while this remains open.

### 5.6 Interaction state machine (CONFIRMED)

- **Press** (sldrEventPress, kind 1/2/3): OR state+0x34 ← 0x40/0x80/
  0x100 (pressed-with-button-N). Gated on `state & 0x10` AND
  `state & 0x06` (the hover bits, §5.7). Then: value via
  sldrValueFromPointer; flagByte |= 1 (armed); refresh; if changed:
  state |= 0x1000 (changed marker) + widgetSendMsg(eventId 3).
- **Move** (sldrEventMove, while flagByte & 1): sldrPointerToValue with
  grab = widget+0x40; update/refresh/message as press (no snap layer).
- **Release** (sldrEventRelease, matching kind): clear the 0x40/0x80/
  0x100 bit; if armed: flagByte &= ~1, refresh.
- Cursor calls at press/release are **RET-only stubs**
  (stubCursorSet/stubCursorRestore 0x42D170/0x42D180) — no runtime
  cursor feedback in this build.

### 5.7 State bits 0x02/0x04 — writer found (CONFIRMED)

`widgetHoverState` (0x413450, renamed this session) is the writer:
(widget, newState, oldState) over the widget's child array (+0x38/+0x3C)
with current-child pointer +0x44; all writes via
`widgetStateSet(mask=0x7)` — i.e. state bits 0/1/2 are rewritten as a
group: value 0x2 (hovered/set) for non-current children, **0x6
(0x02|0x04) for the current (under-pointer) child**, (old&7) on exit.
So bit 0x04 is always set together with 0x02 on the hovered widget —
SLDR's `state & 0x06` press gate means "the pointer is over this
slider". Consumers of 0x02: the same press gates in the widget event
handlers (SLDR here; the button equivalents use the same pattern).

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

## 7. Bound scrollbar object and geometry (CONFIRMED — D-late closure, 2026-11-24)

**Object model (correction of the D-late "shared stateful controller" model):**

- `sbarBindObj` (76 B) is a **widget instance** (magic 0x5655D881) created
  by `subWidgetCtor` (0x408F10) and stored in the window slot that held
  the HOLD anchor. All per-instance state lives in the bound object.
- `g_sbarClass` (0x48E000, 0xC4-B region) is a **shared class object**
  (tag 0x4D795342 "MySB", instance size 0x4C), lazily initialized once
  (flag `g_sbarClassInit` @0x48E0C4): `memCopy` of the VUU! base class
  skeleton (0x4660C4) + 6 method overrides. **Stateless** — it is a
  method table, not a controller. (Historical process-global ownership is
  an implementation artifact, not a requirement — §19 of the Rust brief.)
- Class methods (slot → fn): +0x10 `sbarMethCancelTimer` (timer
  cancel; triggering framework event unverified), +0x1C `sbarMethPaint`,
  +0x20 `sbarMethPress` (state machine), +0x24 `sbarMethRelease`,
  +0x28/+0x2C `sbarMethMove` (duplicate — framework calls both on move).
- Bound-object fields beyond widgetBase (CONFIRMED by displacement):
  +0x38 value u16, +0x3A max u16, +0x3C thumbNum u16, +0x3E thumbDen u16,
  +0x40 stateIdx u16 (last hit-test state 0..7), +0x42 grabOffset u16
  (press-time offset from thumb, signed-extended on use), +0x44 timerObj
  ptr, +0x48 firstTick u8, +0x49 pageMode u8 (1 = ±100 page step, else
  ±30 line step), +0x4A pad.
- `state u16 @+0x34` = 1 | (flags&0x100 ? 0x08 visible : 0) |
  (flags&0x200 ? 0 : 0x10 enabled); `flagByte @+0x36` bit1 = suppressed
  (flags&0x200, also set by sbarBindCreate), bit5 = flags&0x400.
  prvwCtor call sites: 6× 0x100 (visible+enabled), 2× 0x300
  (visible+disabled+suppressed).

**Rect computation — `sbarRectsCompute(quad, params, rectsOut)` (0x41DBD0):**

- Input quad = corner form {x1, y1, x2, y2} (i16 in u32 slots), from
  `bindObj+0x1C` (scaled quad). w = x2−x1, h = y2−y1.
- `orientFlag @rectsOut+0x70` = (w > h) ? 1 horizontal : 0 vertical.
- Part selection (appearance bswap32 offsets with `g_appFallback`
  fallback; appearanceObj fields CONFIRMED by this consumer):
  horizontal: `hSbarPartLarge` +0x288 (h ≥ threshold) / `hSbarPartSmall`
  +0x28C (h < threshold); vertical: `vSbarPartLarge` +0x2D4 / `vSbarPartSmall`
  +0x2D8; thumb part +0x298 (h) / +0x2E4 (v). Threshold/min-thumb/add are
  the `styleCtx` u16s @0x4669B8 / +0x98 (0x4669B4) / +0x9A (0x4669B6).
- Margins from the C-blob part header: horizontal part+0x10 (L) / +0x12 (R);
  vertical part+0x11 (T) / +0x13 (B) — i.e. the 4 margin bytes
  {L, T, R, B} @+0x10..+0x13 of `cBlobPartDesc` (convergence with §6).
- Minimum-size gate: horizontal w < part+0x0C+part+0x0E (capL+capR),
  vertical h < part+0x0D+part+0x0F (capT+capB) → all rects zeroed
  (scrollbar not drawn).
- **Narrow case** (short side < threshold): whole := (x1, y1, x1+mL, y2);
  part1 := (x2−mR, y1, x2, y2); part2/part3 := 0 (caps double as arrows).
- **Wide case**: whole := (x1, y1, x1+mL/2, y2); part1 := (x2−mR/2, y1,
  x2, y2); part2 := (x2−mR, y1, x2−mR/2, y2) (inner right strip);
  part3 := (x1+mL/2, y1, x1+mL, y2) (inner left strip). Cap halves are
  floor-divided signed (SAR 1).
- Track/thumb (shared tail, both orientations):
  trackStart = x1+mL; trackEnd = x2−mR; trackLen = trackEnd−trackStart.
  minThumb = max(thumbPart cap sum (h: +0x0C+0x0E, v: +0x0D+0x0F),
  styleCtx.sbarMinThumb).
  - If trackLen < minThumb + styleCtx.sbarThumbAdd:
    part4 := whole track, part5/part6 := 0 (thumb spans everything).
  - Else:
    `thumbLen = max(FISTP(trackLen * thumbNum / thumbDen), minThumb)`
    `thumbX1  = trackStart + FISTP((trackLen − thumbLen) * value / max)`
    part4 := (trackStart, y1, thumbX1, y2) (left track)
    part5 := (thumbX1+thumbLen, y1, trackEnd, y2) (right track)
    part6 := (thumbX1, y1, thumbX1+thumbLen, y2) (thumb)
  FISTP = x87 round-to-nearest-even (inline FPU; shared helper
  `dtoiRound` 0x44C870 for the value path).

**Hit test — `sbarHitTest` (0x41E6B0) → state:**

| state | region | action (via jump table 0x4530E8) |
|---|---|---|
| 0 | miss | (framework pre-hit-tests; entry 0x9 unreachable) |
| 1 | whole (left-cap region) | decrement: Δ = pageMode?−100:−30 |
| 2 | part1 (right cap) | increment: Δ = pageMode?+100:+30 |
| 3 | part2 (inner right strip, wide only) | decrement (original quirk: inverted) |
| 4 | part3 (inner left strip, wide only) | increment (original quirk: inverted) |
| 5 | part4 (left track) | drag start |
| 6 | part5 (right track) | drag start |
| 7 | part6 band (x from whole.x1 to thumb.x2, y in thumb band) | drag start |

**Value math (exact, both orientations — vertical is symmetric in y):**

- `sbarValueFromPointer(quad, params, ptr, grabOffset)` (0x41E5F0):
  `p = clamp(ptr − grabOffset, trackStart, trackEnd − thumbLen)`;
  `value = round((p − trackStart) / (trackLen − thumbLen) * max)`.
- Press (`sbarPressResolve`, 0x41E510): on the thumb (part6 range) →
  `value = sbarValueFromPointer(…, grabOffset = thumbLen/2)`, returns
  thumbLen/2 stored at +0x42; off the thumb → value unchanged, returns
  ptr − thumb.x1 stored at +0x42. Drag moves (`sbarMethMove`) fire only
  while stateIdx == 7 and re-solve with the stored grabOffset.
- `sbarValueOffset` (0x401700): `value = clamp(value + Δ, 0, max)`;
  refresh on change. Δ ∈ {±30 line, ±100 page} — hardcoded, not from the
  50/100 params (those are the thumb-ratio numerator/denominator).
- Inverse consistency: value→position→value round-trips (both mappings
  share trackLen − thumbLen as the span); no off-by-one found. Rounding
  is nearest-even in both directions.

**Auto-repeat timer (Win32 message timers):**

- `timerCreate(cb, ctx, intervalMs, oneShot)` (0x41C560): 24-B object
  {next@0, magic 0x1F0D2B21@4, id@8, cb@0xC, ctx@0x10, oneShot@0x14};
  `SetTimer(NULL, 0, ms, timerMsgProc)`; appended to the global list at
  0x466C10 (generic `listAppend`/`listRemove`, listObj {first,last,
  stride,count}). `timerMsgProc` (0x41C4F0, winproc RET 0x10) matches the
  id, and for oneShot timers calls `timerOneShotStop` (kill + list
  remove) before invoking the callback.
- Scrollbar use: entering states 5–7 creates a 200 ms oneShot timer
  (`sbarTimerTick`); arrow states 1–4 reset an existing one to 200 ms.
  Tick behavior: first tick (per press, `firstTick` +0x48) rearms at
  **35 ms** and steps ±30/±100; the second tick steps and then the timer
  is dead (no further rearm). Net original behavior: a held arrow produces
  exactly two steps (200 ms, then 35 ms later). CONFIRMED — documented
  as original behavior, not a defect to "fix" in the reimplementation.
- Release (`sbarMethRelease`): `timerDestroy(&obj+0x44)`, stateIdx = 0,
  refresh. Note: entering states 5–7 overwrites +0x44 without freeing a
  stale timer object (original leak quirk).

**Appearance/style-context fields confirmed by this subsystem:**

- `styleCtx` @0x46691C (struct in Ghidra): +0x34 g_appFallback (0x466950),
  +0x38 g_appCurrent (0x466954), +0x3C gStyleDColorsFallback (0x466958,
  S1), +0x54 gInkFSize (0x466970, S1), +0x68 gInkG (0x466984, S1),
  +0x6C gInkGSize (0x466988, S1), +0x75 gScaleNum (0x466991, S1),
  +0x76 gScaleDen (0x466992, S1), +0x78..+0x95 metrics[35] (5×7 scaled
  gStyleMetricBases, S1), +0x98 sbarMinThumb (0x4669B4), +0x9A
  sbarThumbAdd (0x4669B6), +0x9C sbarThreshold (0x4669B8). All runtime
  filled (zero in .data).
- **Scale factor source (bridge to Batch E, RESOLVED):** `scaleQuad`
  (0x429C70) = `dst[i] = (i32)(src[i] * gScaleNum / gScaleDen)` — signed
  multiply, signed truncate divide, 4 quad components; gScaleNum/Den are
  u8 context bytes filled from the HAP header scale bytes (S1 doc 13:
  header bytes 0x0C/0x0D, `01 01` = 1:1).
- `appearanceObj` extended to 744 B (0x2E8): partOff[131] @+0x40 ends at
  +0x24C; scrollbar part offsets at +0x288/+0x28C/+0x298 (horizontal)
  and +0x2D4/+0x2D8/+0x2E4 (vertical) — **beyond the previously applied
  608-B struct** (superseded; the 131 vs 512 reconciliation is Batch E §9).

**Degenerate cases (exact code behavior):**

- Empty quad (w ≤ 0 or h ≤ 0) → zero rects, no interaction regions.
- w < capL+capR (h < capT+capB vertical) → zero rects (not drawn).
- trackLen < minThumb + sbarThumbAdd → thumb spans whole track; part5/6
  zero; press resolves "off thumb" (value unchanged); drag math then uses
  thumbLen = 0 and a zero right-track bound (the span computation
  degenerates — value clamps toward max; original behavior).
- value == max: thumb pinned at trackEnd − thumbLen (the value→position
  formula yields exactly that; no special case).

## 8. Menu-bar slot geometry (CONFIRMED — D-late closure, 2026-11-24)

`mbarSlotGeometry(mbarSub, slotIdx, outRect{ x, y, w, h })` (0x42EB30,
renamed + prototyped this session). mbarSub = the MBAR child object
(magic 0x455E0FD3, 192 B, doc 17 §14).

- `slotIdx ≥ byte[mbarSub+0x3D]` (slot count) → outRect zeroed, return 0.
- `y = [mbarSub+0x08]`, `h = [mbarSub+0x10]` (the menu bar's own y/height
  fields — the same quad slots as the menuBarQuad).
- `x = [mbarSub+0x04] + 5` (constant 5 px left pad) + Σ byte widths of the
  sub-item pointers **before** the slot; `w =` Σ byte widths of the slot's
  own sub-items.
- Sub-item pointers live at `mbarSub+0x40`, **8 pointers per slot**, each
  pointing to a sub-object whose **byte at +0x4 is the item width**.
- Return 1 on success.

So the menu bar lays out **groups of 8 menu items per slot**: slot k
spans x = x0 + 5 + Σ_{j<k}(Σ_i w[j,i]) .. + Σ_i w[k,i]. The width bytes
are the per-item label widths measured at menu-build time (the same
values the %MNU items carry — Batch B2). This 8-per-slot grouping is
unrelated to the 512-entry C-section part pool (Batch E reconciliation
stands open).

## 9. Rust-reimplementation implications

- Geometry pipeline: serialized u16s → i32 raw → scaled (one scaleQuad)
  → paint in scaled space. Keep raw and scaled separate (resize/repaint).
- Window model: outer geometry + reserved-chrome client quad + max sizes.
- Parts: a part is a 9-slice-capable image (C-blob) with an optional
  ext colour/insets; appearance = table of part offsets + per-widget-type
  part indices (track/thumb/arrow/band slots).
- Scrollbars: geometry anchors (named, hidden widgets) + a per-bound-object
  state block; the shared class (method table) is an implementation
  detail — model the bound object as an owned widget with {value, max,
  thumbNum, thumbDen, stateIdx, grabOffset, timer} in the reimplementation.
- Message flow: value changes bubble to the parent's class+0x9C handler
  (widgetSendMsg, 44-B message, eventId 3 = slider value-changed).

## 10. Verification status

| Claim | Basis |
|---|---|
| 4-space coordinate model | code (widgetInstantiate, scaleQuad call sites) + raw descriptor bytes |
| VWIN outer/client geometry | code (vuuPayloadParse) + all 6 built-in payloads (static data) |
| HOLD hidden anchors + consumption | code (holdWidgetInit, sbarBindCreate, prvwCtor) + prvw payload |
| SLDR value/pointer math | code (sldrValueFromPointer) — start/span terms partially verified (vertical branch open) |
| part = C-blob | code (partDraw → cBlobHeaderDecode; sldrPartLookup field offsets) + doc 14 corpus verification |
| 3-slice standard part path | code (partDraw branches) + S1 nine-slice model |
| bound object = widget of shared class "MySB" | code (sbarBindCreate, subWidgetCtor, g_sbarClass init bytes) — CONFIRMED |
| bound-object words = value/max/thumbNum/thumbDen | code (sbarValueOffset clamp, sbarRectsCompute, sbarValueFromPointer) — CONFIRMED (was HYPOTHESIS) |
| scrollbar part-rect layout + thumb formulas | code (sbarRectsCompute disassembly + FPU ops) — CONFIRMED; not yet screenshot-corroborated |
| hit-test state map + actions | code (sbarHitTest + jump tables 0x4530E8/0x4530D8) — CONFIRMED; wide-case inner-strip inversion is original behavior |
| pointer↔value exact mappings + rounding (FISTP) | code (0x41E5F0/0x41E510 FPU idiom, dtoiRound) — CONFIRMED |
| auto-repeat timer behavior (2 steps) | code (timerMsgProc, sbarTimerTick, oneShot rearm) — CONFIRMED |
| scaleQuad = src * num / den, num/den u8 globals | code (0x429C70) + S1 (HAP header bytes 0x0C/0x0D) — CONFIRMED |
| styleCtx layout @0x46691C (+0x98..+0x9C sbar metrics) | code (sbarRectsCompute displacements) + S1 field list — CONFIRMED for listed fields; gaps unknown |
| appearanceObj ≥ 0x2E8 with sbar part offsets | code (sbarRectsCompute bswap32 loads at +0x288..+0x2E4) — CONFIRMED; full field map = Batch E |
| All 6 windows: %REZ → VWIN descriptor → window-own payload → childBase → instance slots | `tools/research/geo_check.py` (scripted, static data) — ALL OK, prvw payload 0x01100 exact |
| §7 scrollbar geometry formulas (degenerate cases, min gates, thumb formulas, endpoint snapping, hit-test, round-trips, scale truncation) | `tools/research/sbar_check.py` (scripted invariants of the code-decoded model) — ALL OK (165 checks); model is executable-derived, not rendering-corroborated |
| §5 SLDR payload/init, part dispatch (35 cases), render term, pointer→value, interaction states, hover-bit writer, mbar slots | code disassembly (sldrRender/sldrValueFromPointer/sldrPointerToValue/sldrEventPress/Move/Release/sldrWidgetInit/widgetHoverState/mbarSlotGeometry) + raw payload bytes — CONFIRMED; the max/value render term is runtime-unverified (§5.5) |

Open (D-late remainder / E): the SLDR render max/value term is
runtime-unverified (screenshot mid-track thumb the code cannot produce;
needs a runtime trace or second build) — held open per the D-late
constraint, SLDR geometry NOT implementation-ready. C1 items: +0x8C
class slot, list dtor ownership, detach counterpart. Batch E: appearance
object lifecycle + 131-vs-512 reconciliation + D/E-section consumers
(26 g_appCurrent consumers located at 0x41DC25–0x42E925). LSTS row
heights in scaled units: unverified (Batch C).
