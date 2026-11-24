# S1 — Resource Dispatch, Global Skin Context, and Widget State

Status: session S1 (2026-11-18). All findings address-annotated; confidence tagged.

## 1. Global skin context (CONFIRMED)

The renderer holds a **fixed block of section pointers at 0x466950–0x466994**,
populated by the appearance install. No per-resource rich objects exist in this
layer — painters index sections directly.

| Global | Addr | Meaning (from `skinInstall`) |
|---|---|---|
| `gStyleDef` | 0x466950 | Fallback style = `embeddedBlobB + bswap(B[0x52])` (C section of built-in blob B) — set **unconditionally** at every install |
| `gStyleRec` | 0x466954 | **C section base** of the active appearance: `blob + bswap(blob[0x34])`. `gStyleRec+0x40` = 512-slot BE u32 table of C-relative blob offsets |
| `gStyleDColorsFallback` | 0x466958 | Fallback D table = `embeddedBlobB + bswap(B[0x60])` — set once, never overwritten |
| `gStyleDColors` | 0x46695C | D section base: `blob + bswap(blob[0x3C])` (or fallback ptr if blob has no D) |
| `gStyleDColorCount` | 0x466960 | `bswap(blob[0x40])>>2` = **54** (or fallback count `bswap(B[0x64])>>2`) |
| `gInkTbl` / `gInkCount` | 0x466964/68 | E section base + **byte length** (`bswap(blob[0x48])`); `<5` → 0/0 (no ink) |
| `gStyleStrA/B` | 0x466974/7C | `FUN_0042d3f0` (string build) results from 0x4576A0/A8 constants — role of these two strings unresolved |
| `gInkF` / `gInkFSize` | 0x46696C/70 | F section base + byte length (`bswap(blob[0x50])`) |
| `gInkG` / `gInkGSize` | 0x466984/88 | G section base + byte length (`bswap(blob[0x58])`) |
| `gScaleNum` / `gScaleDen` | 0x466991/92 | header bytes **0x0C/0x0D** (scale option nibbles; `01 01` = 1:1) |
| metric tables | 0x466994–0x4669B1 | **5×7 u16 matrix** = scaled `gStyleMetricBases` (5 rows × 7 cols of **bytes** @ 0x46703B–0x46705A): `u16[row][col] = byte[row][col] * gScaleNum / gScaleDen` (loop 0x429005–0x4290D8, 5 iterations, ECX += 7) |
| `gOncePtr` | 0x46698C | lazily set to `0x47B324` (runtime-region pointer) at first install; `gOnceFlag` byte @0x466990 zeroed — purpose unresolved |

Sole writers of `gStyleRec`/`gStyleDColors`/`gInkTbl`/`gInkF`/`gInkG`:
`skinInstall` (0x428C70) — ~25 read references across the paint family.

### 1.1 Install path (CONFIRMED)

```
appearanceLoadInstall (0x402FA0)          appearanceResetDefault (0x403020)
  hapSerialize(doc) → v2 buffer            notify(0, holder+0x0C)
  skinApply(buf, size)                     skinApply(NULL, 0)
  free old blob; holder+0x04 = buf         memFree(holder+0x04)
  notify(0x10, holder+0x0C)
        │
        ▼
skinApply (0x435030) = skinInstall(blob,size) + 0x40F220 + 0x41D390
        │
        ▼
skinInstall (0x428C70)
  blob == NULL → defaults (gStyleRec = gStyleDef; inks 0; scale 1/1)
  else:
    hapHeaderValidateV2 (0x4287F0):
      size >= 0x88; bswap(u32@0) == 0x25484156 ('%HAP' BE); u16BE@4 == 2
      (else hError 0x10008); scale nibbles @0x0C/0x0D non-zero;
      6 directory slots @0x2C walked (0x428720 per slot)
    then populate the table in §1 from BE directory offsets
```

**The install accepts v2 only** — v1 files are never loaded directly by this
build (consistent with R0-A.1: writer is v2-only; v1 is read by
`hapParse`/document layer for import into the document model, re-serialized to
v2 for the render layer).

`0x40F220` and `0x41D390` (post-install hooks in `skinApply`) were not fully
resolved this session (PROBABLE: derived/global cache rebuild + notification).

## 2. Resource lookup primitives (CONFIRMED)

### 2.1 D colours — `styleColorGet(roleIdx)` @ 0x42A140

```c
uint styleColorGet(uint roleIdx) {
    if (roleIdx >= 0x36) return 0;                    // 54 roles
    if (roleIdx < gStyleDColorCount)
        return gStyleDColors[roleIdx];                // active appearance
    return gStyleDColorsFallback[roleIdx];            // built-in default
}
```

Per-role fallback: any role missing from the loaded appearance (D section
shorter than 54) is served from the built-in table. Role → widget semantic
mapping (which role paints which element) is the consumer-side question
carried to §4 of doc 15.

### 2.2 C icons — direct table indexing

Painters read `gStyleRec+0x40` (the 512-slot BE u32 table) with a fixed slot
index, get a **C-relative** offset, and blit the C blob at
`gStyleRec + offset`. State icons (checkboxes/mutexes) use `bmpStateIconDraw`
(0x429F80, see doc 14).

### 2.3 E ink — `inkBlitCore` @ 0x44DFE0

Callers: `bmpInkBlit` (0x426E00), `bmpTextDraw` (0x427200), `bmpTextDraw2`
(0x426F50), 0x427430. Ink object layout (partial): `+0x08` u32 colour
(byte-swapped on use), entry table at `+0x10` (index by param_2). "Ink" is the
Haxial term for glyph/raster draw resources — text drawing is ink blitting,
so **section E is the glyph/ink section** (its runtime layout beyond the
byte length is not yet decoded; the editor's .fnt font files feed this path
— see open questions).

## 3. Widget state machine (CONFIRMED) — **state address SUPERSEDED by S2 C1**

> **CORRECTION (S2 C1 + Batch D, 2026-11-21 — doc 17 §16.1):** the state
> word is the `ushort` at **widget+0x34**, not +0x0D (S1's historical
> description is **superseded**). `buttonHoverSet` (0x43BDD0) does not
> write the widget state word — it manages four button-internal element
> words (+0x84/+0x98/+0xAC/+0xC0). Corrected bit map (bit numbers):
> 0x01 = bit 0 active (set at instantiation `(mode&0x18)|1`; stateSet can
> only clear it); 0x02 = bit 1 hilited (widget-level writer untraced);
> 0x08 = bit 3 visible (kntrPaint filter; from descriptor mode bit 3);
> 0x10 = bit 4 enabled (from descriptor mode bit 4 — the prvw disabled
> pairs clear it); 0x20 = bit 5 (OR'd by CLST/LSTS ctors after init;
> consumer pending). The S1 "0x20 = disabled" interpretation does NOT
> apply to the widget state word (disabled = absence of 0x10, pending
> painter confirmation). Notification path `class = [widget+0x04];
> notify = [class+0x5C]; notify(new, old, widget)` was correct in S1 and
> stands. The code block below is kept for the record with the wrong
> offset flagged.

`widgetStateSet` (0x4093E0):

```c
// widget: magic 0x5655D881 @+0x00; u16 state @+0x0D; obj ptr @+0x04
uint widgetStateSet(widget, mask, value) {
    if ((state & mask) != value) {
        // constraint rules (observed):
        //   if new state has bit0  -> clear bits 0 and 3
        //   if new state lacks bit1 -> clear bit0
        store state;
        if (obj && obj->vtable[0x5C/4])
            obj->vtable[0x5C/4](widget, oldState, newState);   // notification
        return (result & 0xFFFFFF00) | 1;    // low byte 1 = changed
    }
    return (result & 0xFFFFFF00);            // low byte 0 = unchanged
}
```

State bits (writer + consumer evidence):

| bit | meaning | evidence |
|---|---|---|
| 0x01 | pressed/active variant | `bmpStateIconDraw` icon +1 offset; constraint "no bit1 → no bit0" |
| 0x02 | **hilited (hovered)** | `buttonHoverSet` (0x43BDD0) sets/clears bit 2 in per-element words; icon +2 offset |
| 0x20 | ~~**disabled**~~ | S1 claim — see correction note above: in the corrected state word the disabled selector is the absence of 0x10; `bmpStateIconDraw` bank-B selection bit to be re-verified in D |

`buttonHoverSet` also shows the **button widget object layout**: rect
`+0x2C..+0x38` (x, y, right, bottom), text obj `+0x7C`, per-element state
words `+0x84/+0x98/+0xAC/+0xC0` (4 elements), feature ptrs `+0xA4/+0xB8`,
position bytes `+0x8B/+0x8C`.

## 4. Paint dispatch model (CONFIRMED mechanism; one open edge)

- Five per-type paint methods: `labelPaint` (0x409FC0),
  `buttonWidgetPaint` (0x43BF60), `compositeWidgetPaint` (0x43BC00, shared
  button-family painter), `iconGridPaint` (0x4514C0), `listRowPaint` (0x446770).
- **No static vtable contains them**: a scan of all data segments found only
  `{fnPtr, argPtr}` pairs inside **template/method tables** — e.g.
  `tableButtonMethods` @ 0x45E140 (8 entries, functions 0x43BDD0–0x43CB10)
  and `tableLabelMethods` @ 0x45C560 (6 entries, 0x409EF0–0x40A450), each
  pair pointing a method at an argument blob (0x4598xx/0x453Exx regions).
  `buttonWidgetPaint` (0x43BF60) appears only as a DATA ref (0x45E150) —
  it has zero code callers.
- **Model (PROBABLE):** window templates (VWIN descriptors, cf. registry
  @0x45F848) carry per-child method/argument lists; the window initializer
  walks them (construction + state setup), and runtime paint reaches the
  per-type methods through child descriptor function pointers built from
  these tables. The exact WM_PAINT → child-paint call site is the remaining
  open edge (no static reference to resolve without runtime observation).
- State transitions use a **virtual notification**: `(widget+4)->vtable+0x5C`
  slot 0 — a second, object-owned dispatch surface for the widget's "skin
  object".

## 5. Deferred decompiles resolved (CONFIRMED)

| addr | result |
|---|---|
| 0x41A300 | `fileClose` — sentinel-checked FileRec close: magic 0x1CA6C39A, `CloseHandle(rec+0)`, registry unlinks ×2 (`DAT_004668D8/8E8`) when `rec[6]` set, frees path + rec |
| 0x43A610 | `fmtByteCount(value, scale, buf, flags)` — human-readable sizes: plain decimal (scale 0) or fixed-point `N.N` + K/M/G (value path) / T/P/E (scale path 0x100/0x40000/0x100000000) |

## 6. Open items carried from S1 batches

- Runtime layout of embedded blob B (0x4683D4 `bBuiltIn`): `+0x52`→C,
  `+0x60`→D table, `+0x64`→D count are consumed byte-swapped; the rest of
  the 40,336-byte blob's structure is unresolved. The TSLC table
  (0x466DD4, 84 pointers, "TSLC" @+0xE8) assembles the Evil Chiaroscuro
  appearance at runtime (174 entries × 0x14 match the built-in A's C entry
  count).
- `gStyleStrA/B` (0x466974/7C) purpose.
- E-section runtime ink object layout (only byte length is tracked globally).
- Scrollbar/slider specific geometry functions (composition established from
  screenshots; per-pixel geometry not yet pinned to a single function).
- 0x40F220 / 0x41D390 post-install hooks.
- `gOncePtr` (0x46698C → 0x47B324) purpose; semantic mapping of the 5×7
  metric matrix (rows/columns → which widget metrics).