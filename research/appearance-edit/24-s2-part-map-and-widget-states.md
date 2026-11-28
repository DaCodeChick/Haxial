# 24. S2 — Part-Index Map & Widget/State Binding (Batch V, V2.1 / G-4)

**Status:** COMPLETE for code-verified constants (V2.1 closed); data-driven index fields
left as explicit backlog (V2.1-rem).

**Scope (G-4):** map every part-table index (0..511) to a widget and UI state; identify
which appearance C-section slots are used, by which renderer, in which state; determine
which slots the editor reads. All static (no runtime).

**Method:** (1) `tools/research/part_map.py` — dump all used slots of the built-in C
section (at HAP offset `coff`=+0x34, per doc 20 §9) with full 20B/26B headers, cross-
referenced against disassembly; (2) single-pass disassembly extraction of every
`MOV reg, [appBase + idx*4 + 0x40]` load (partOff table) in every C-blob renderer;
(3) `get_callers` of each renderer → leaf painter → class paint slot (doc 18 §2
21-class table) → widget class; (4) corpus scan of all `refs/appearances/*.hap` C
sections for the used-slot distribution.

**Confidence key:** CONFIRMED (code-verified by disassembly or raw data) / PROBABLE /
HYPOTHESIS.

---

## 1. Part-table schema (CONFIRMED, re-verified this session)

- `partOff[512]` of u32BE pool offsets at **appearance+0x40** (the C section IS the
  runtime appearance object; doc 20 §12). Value 0 = empty slot; otherwise the offset
  (bswap32'd) of the part record within the C-section pool.
- **Capacity 512 is fixed; usage is variable.** The built-in uses exactly **142**
  slots (max index 0x10B). The corpus (38 files with a C section) uses exactly the
  same **142-slot canonical set** (124 of them overlap the built-in; the built-in is
  the reference implementation of the canonical set — it is NOT an outlier).
- Part record header (Batch G, doc 22): 20B base + optional 12B ext when
  `flags & 0x10`. `field2` @+0x10 = margins {L,T,R,B} (remapped to gradient
  insets by `partToSkinDib`; CONFIRMED code + PROBABLE semantics per doc 22).

## 2. Code-verified index → widget/state map (V2.1 core deliverable)

Index semantics: `partSrc = g_appCurrent + bswap32(partOff[idx])`.

### 2.1 SLDR — slider (class @0x467C48; `sldrRender` 0x42B820, `sldrPartLookup` 0x42BD00)

| idx | shape (built-in) | role (CONFIRMED code) | state logic |
|---|---|---|---|
| 0x6E | 5x7, ext mode 1 (H grad 333333→666666) | horizontal **track segment** part record | state case C (SLDR jump 0x4577C4); value struct bit 0x20 clear |
| 0x6F | 5x7, ext mode 1 (H grad 440000→bb0000) | horizontal **track segment** part record | state case B |
| 0x70 | 5x7, plain | horizontal track segment (3rd variant) | state case A |
| 0x72 | 14x16, margins {0,0,0,4} | horizontal **thumb** (unpressed) | `sldrPartLookup`: bit 0x20 clear |
| 0x73 | 14x16, margins {0,0,0,4} | horizontal thumb (state variant B) | sldrRender case B |
| 0x74 | 14x16, margins {0,0,0,4}, 4bpp | horizontal thumb (state variant A) | sldrRender case A |
| 0x76 | 14x16, margins {0,0,0,3} | horizontal thumb (**pressed**) | `sldrPartLookup`: bit 0x20 set |
| 0x77 | 14x16, margins {0,0,0,3} | horizontal thumb pressed (variant) | — |
| 0x78 | 14x16, margins {0,0,0,3}, 4bpp | horizontal thumb pressed (variant) | — |
| 0x7A | 7x5, ext mode 2 (V grad 666666→333333) | vertical track segment | press-release path |
| 0x7B | 7x5, ext mode 2 (V grad bb0000→440000) | vertical track segment (state variant) | — |
| 0x7C | 7x5, plain | vertical track segment (3rd variant) | — |
| 0x7E | 16x14, margins {0,0,0,4} | vertical **thumb** (unpressed) | `sldrPartLookup`: vertical, bit 0x20 clear |
| 0x7F | 16x14, margins {0,0,0,4} | vertical thumb (variant) | — |
| 0x80 | 16x14, margins {0,0,0,4}, 4bpp | vertical thumb (variant) | — |
| 0x82 | 16x14, margins {0,0,0,3} | vertical thumb (**pressed**) | `sldrPartLookup`: vertical, bit 0x20 set |
| 0x83 | 16x14, margins {0,0,0,3} | vertical thumb pressed (variant) | — |
| 0x84 | 16x16→16x14, margins {0,0,0,3}, 4bpp | vertical thumb pressed (variant) | — |

State bits: value-struct bit 0x20 = pressed; orientation from geometry (14x16 =
horizontal thumb, 16x14 = vertical thumb). All 18 slots present in the built-in and
in 35/38 corpus files (canonical).

**Correction to earlier note:** in `sldrRender`, 0x6E/0x6F are **part records** (their
bswapped offsets point at part blobs whose `h` = word[+2] and margins =
byte[+0x10]/byte[+0x12] are read for track sizing) — not colour table entries.

### 2.2 Scrollbar (widget class object g_sbarClass; paint `sbarMethPaint` 0x4016A0; doc 20 §12)

| idx | shape (built-in) | role (CONFIRMED, doc 20 §12) |
|---|---|---|
| 0x92 | 63x16, 8bpp, 43 pal | **hSbar track** (partOff[146]) |
| 0x93 | 33x16 | hSbar **thumb** (partOff[147]) |
| 0x94 | 35x16 | hSbar thumb variant |
| 0x95 | 5x16 | hSbar end filler |
| 0x96 | 7x16 | hSbar **arrow** (partOff[150]) |
| 0x97 | 7x16 | hSbar arrow variant |
| 0xA5 | 16x63 | **vSbar track** (partOff[165]) |
| 0xA6 | 16x33 | vSbar thumb (partOff[166]) |
| 0xA7 | 16x35 | vSbar thumb variant |
| 0xA8 | 16x5 | vSbar end filler |
| 0xA9 | 16x7 | vSbar arrow (partOff[169]) |
| 0xAA | 16x7 | vSbar arrow variant |

Orientation check: horizontal parts are wide (63x16), vertical parts are tall
(16x63) — consistent in every corpus file. 36/38 corpus files use all 12 slots
(canonical).

### 2.3 MBAR — menu bar (class @0x46824C; `mbarDrawTitles` 0x42EF60 → `mbarDrawTitleItem` 0x42AC00)

| idx | shape (built-in) | role (CONFIRMED code) | state |
|---|---|---|---|
| 0x101 | — (slot empty in built-in) | menu-bar title item **background** | state bit 0 clear |
| 0x102 | — (slot empty in built-in) | menu-bar title item background | state bit 0 set |
| 0x105 | 1x1 white | menu-bar title item **content tile** | state bit 0 clear |
| 0x106 | 3x4, ext mode 2 (b00000→660000) | menu-bar title item content tile | state bit 0 set |

**Key fact:** in the built-in, 0x101/0x102 are EMPTY — the built-in does not skin the
menu-bar title background; only the content tiles exist (and only 1 corpus file,
Blue Fragmentation, fills 0x105/0x106; menu-bar skinning is rare in the corpus).
The fallback path (empty slot → fallback appearance) applies per doc 22.

**Correction:** doc 22's earlier "mbar parts 255/256/433-435/261-263" numbers are not
reproducible from `mbarDrawTitles`/`mbarDrawTitleItem` disassembly (no such
constants there). The code-verified set is 0x101/0x102/0x105/0x106. The 0xFF/0x100/
0x1B1-0x1B3 observations are preserved as a separate open item (V2.1-rem, item 4).

### 2.4 KOLR — colour widget (class @0x4679FC; `kolrRender` 0x42D060 — renamed this session)

| idx | shape (built-in) | role (CONFIRMED code) | state |
|---|---|---|---|
| 0x109 | 5x5, 4bpp, pal 5 | colour-widget state part | state case 1 |
| 0x10A | 5x5, 4bpp, pal 5 | colour-widget state part | state case 2 |
| 0x10B | 5x5, 2bpp, pal 3 | colour-widget state part | state case 3 |

All margins {2,2,2,2}, field2 0x04040404. Present in built-in; 25-36/38 corpus files.

### 2.5 BPMN — bitmap button (class @0x467874; `bpmnRender` 0x42AD40 — renamed this session)

| idx | shape (built-in) | role (CONFIRMED code) | state group |
|---|---|---|---|
| 0x49, 0x4A, 0x4B | 26x8, margins {3,3,22,4} | BPMN part group 1 (wide) | normal (0x49/0x4A) / pressed (0x4B) |
| 0x4D, 0x4E, 0x4F | 8x8 | BPMN part group 2 (small) | normal/pressed variants |
| 0x51, 0x52, 0x53 | 9x5 | BPMN part group 3 (tiny) | normal/pressed variants |

Two state groups (normal/pressed) × 3 variants each = 9 indices. All present in the
built-in; 25-36/38 corpus files (canonical).

### 2.6 Window content paint path (caller chain: `0x40EA50` window pre-paint [doc 18] +
`0x40EB50` → `0x40E570` → `FUN_0042d6d0` 0x42D6D0)

| group | idx | shape (built-in) | margins (field2) | corpus |
|---|---|---|---|---|
| 1 | 0xCF, 0xD0, 0xD1 | 14x14 | {0,4,5,0} | 36-37/38 files |
| 2 | 0xD4, 0xD5, 0xD6 | 14x14 | {0,0,4,5} | 35-36/38 |
| 3 | 0xD9, 0xDA, 0xDB | 14x14 | {0,0,4,0x17} | 36-37/38 |
| 4 | 0xDE, 0xDF, 0xE0 | 32x14 | {0x1B,0,0,4} | 37/38 |

Each group: a flag ([local_20]) selects base (idx0) / alt (idx1); idx2 is a third
variant. **The final widget class consuming this renderer is NOT YET CLOSED** — the
chain is proven to the window pre-paint, but which leaf class/record field selects
the groups is unestablished. Name withheld per S2 rules (no speculative naming).
The 4-group × 3-variant pattern (12 slots) plus their extreme corpus prevalence make
them the core window-chrome parts.

## 3. Class-level consumer map (all 21 classes + scrollbar + menu + editor)

| Widget class (doc 18) | paint slot | renderer (this session) | part index mode |
|---|---|---|---|
| SLDR @0x467C48 | 0x438160 | sldrRender/sldrPartLookup | **constants** (§2.1) |
| scrollbar (g_sbarClass) | sbarMethPaint 0x4016A0 | labelMarkerDraw + doc 20 §12 table | **constants** (§2.2) |
| MBAR @0x46824C | 0x43CDF0 → mbarDrawTitles | mbarDrawTitleItem/mbarTitleBackground | **constants** (§2.3) |
| KOLR @0x4679FC | 0x4372C0 | **kolrRender** (renamed) | **constants** (§2.4) |
| BPMN @0x467874 | 0x4365E0 | **bpmnRender** (renamed) | **constants** (§2.5) |
| PRGS @0x467B84 | 0x437E90 | **prgsRender** (renamed) | data-driven (V2.1-rem) |
| SEPR @0x4677B0 | 0x436100 | **seprRender** (renamed) — **resolves G-5** | data-driven (V2.1-rem) |
| BOX! @0x4676EC | 0x436070 | **boxRender** (renamed) | data-driven (V2.1-rem) |
| BUTN @0x4674A0 | 0x435350 butnPaint | bmpStateIconDraw | data-driven (V2.1-rem) |
| IKBT @0x467938 | 0x436E60 | bmpRowText | data-driven (V2.1-rem) |
| LSTS/CLST/IMGS | 0x41F820 listWidgetPaint → 0x448200 | labelMarkerDraw, FUN_00429d70, listRowFill→bmpRowText | data-driven (V2.1-rem) |
| KLBL/LABL/TXTS (label family) | labelPaint 0x409FC0 / labelWidgetFill | widgetBaseFill, bmpSetMetrics, labelMarkerDraw | data-driven (V2.1-rem) |
| IKON @0x468310 | 0x43D230 ikonPaint | **no C parts** (icon-resource table, E section — D-late boundary) | n/a |
| HOLD/KNTR/KNTR-family | 0x409C00 / 0x412980 | compositeWidgetPaint 0x43BC00 → bmpStateIconDraw + widgetBaseFill | data-driven (V2.1-rem) |
| window content | pre-paint 0x40EA50 | FUN_0042d6d0 (unrenamed) | **constants** (§2.6) |
| %MNU rows (menu, not widget) | menuRowCellState 0x40FA00 | bmpSetCellState | data-driven (V2.1-rem) |
| editor icon grid | iconGridFill 0x451260 | bmpSetCellState, bmpSetMetrics | data-driven (V2.1-rem) |

**Data-driven** = the renderer receives the part (or index) from a caller/widget
field; no constant found in the renderer body itself. Recovering the originating
field is backlog V2.1-rem (see §5).

## 4. Built-in slot census (142 slots; `part_map.py` output)

Shape families (built-in):
- 7x7–8x8 tiny parts @0x09-0x23, 0x29-0x33: unassigned to a verified consumer
  (candidate: checkbox/tick/corner fragments — **HYPOTHESIS, no consumer identified**).
- 13x10/14x14/26x8/8x8/9x5 @0x41-0x5C, 0x49-0x53: BPMN + window-chrome families (§2.5, §2.6).
- 5x7/7x5/14x16/16x14 @0x6E-0x84: SLDR (§2.1).
- 5x5 @0x86-0x88, 0x109-0x10B: tick/KOLR families (KOLR verified §2.4; 0x86-0x88
  unassigned).
- 63x16/33x16/16x63/16x33 etc @0x92-0xAA: scrollbar (§2.2).
- 16x16 @0x9C-0xA1, 0xAF-0xB4 (8 parts, one with field2 0x0000000F, one 0x0F000000):
  unassigned (candidate: list-row icon/tick frames — **HYPOTHESIS**).
- 3x3/1x1 @0xB9-0xC2, 0xBD-0xBF: unassigned (candidate: tick marks — HYPOTHESIS).
- 13x29 @0xCC-0xCD (field2 0x06160606): unassigned.
- 14x14/32x14 @0xCF-0xE0: window content (§2.6).
- 21x21 @0xE3-0xE4: unassigned.
- 9x9 @0xE8-0xE9 (margins {4,4,4,4}): unassigned.
- 12x12 @0xF7, 0xFB (field0 0x00FFFFFF white): unassigned (candidate: list selection
  frames — HYPOTHESIS).
- 3x4/1x1 @0x100, 0x105-0x107: MBAR family (§2.3).

**Unassigned-but-used slots (no code-verified consumer): 86 of 142** (142 used − 56
verified-on-used; MBAR's 0x101/0x102 are verified but EMPTY in the built-in). These
are not speculatively named; they are listed as shape facts above with explicit
HYPOTHESIS tags.

## 5. Backlog (V2.1-rem)

1. **Data-driven index fields:** for each data-driven consumer (PRGS, SEPR, BOX!,
   BUTN, IKBT, list family, label family, HOLD/KNTR composite, %MNU rows, editor
   grid), identify the widget/record field that supplies the part index (or the
   caller that computes `partOff[idx]`). Requires per-caller argument tracing.
2. **Window content consumer class:** close the `0x40EA50 → 0x40E570 →
   FUN_0042d6d0` chain to the widget class/record that selects the 4 part groups
   (§2.6). Then rename FUN_0042d6d0 accordingly.
3. **Slot 0x1 consumer:** used in 25/38 corpus files, ABSENT from the built-in —
   some code path reads partOff[1] that the built-in never exercises (or the built-in
   relies on its fallback for it). Locate the constant `0x1` load at +0x40.
4. **mbar 0xFF/0x100/0x1B1-0x1B3:** doc 22's earlier observation; not reproducible
   from mbar painters. If real, locate the consumer (possibly a different menu path
   or the editor's menu preview).
5. **Corpus v1 C-section check:** this scan used the v2 offset (coff @+0x34); verify
   the 38-file count is not an artifact of version handling (doc 20 §9 layout is
   version-independent for the header, CONFIRMED — so expected complete).

## 6. Ghidra changes (this session)

- Renames (5, read-back verified via list_functions):
  - 0x42C610 → **prgsRender**; 0x42CED0 → **seprRender**; 0x429E80 → **boxRender**;
    0x42D060 → **kolrRender**; 0x42AD40 → **bpmnRender**
- Function comments (6): prgsRender, seprRender, boxRender, kolrRender, bpmnRender,
  FUN_0042d6d0 (part indices + caller chains recorded).
- No structure/type/data changes (all consumed via the existing appearance+0x40
  partOff model).

**Verification:** `part_map.py` 142/142 slots parsed, 0 errors; corpus scan
142 canonical slots; rename read-back (list_functions); caller mapping via
get_callers (doc 18 paint-table cross-reference).

## 7. Corrections issued

1. `sldrRender` 0x6E/0x6F are **part records**, not colour-table entries (§2.1).
2. doc 22 "mbar parts 255/256/433-435/261-263" superseded by 0x101/0x102/0x105/0x106
   (§2.3); old numbers preserved as open item V2.1-rem/4.
3. G-5 (doc 22) **resolved**: 0x42CED0 = SEPR part renderer.
4. Built-in C section is the **canonical 142-slot set** (§1) — not an idiosyncratic
   subset.
