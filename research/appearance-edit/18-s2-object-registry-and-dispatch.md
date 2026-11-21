# 18. S2 — Object Registry & Dispatch (B2): the paint chain, fully closed

Session S2, Batch B2 (and the class-slot inventory that it required).
Target: `AppearanceEdit.exe` (Haxial AppearanceEdit 1.400, x86:LE:32 PE,
image base 0x00400000). All addresses VA. Confidence markers: CONFIRMED
(executable code path) / PROBABLE (strong single source) / HYPOTHESIS.

**Headline (CONFIRMED):** S1's open item 1 — "the exact WM_PAINT →
per-child paint call site" — is closed. The chain is:

```
WndProc (0x40EB50) WM_PAINT
  └─ FUN_0040E570 (window chrome: frame edges + focus border, 4 DIB blits)
  └─ accumulate content dirty rect into pv text object (rect @pv+0x78, dirty @pv+0x88)
  └─ slot 0 (pv+0x10)(windowObj)          ← default: labelPaint (0x409FC0)
        └─ textWidgetGetRect(pv, rect, 8, &state, &fontIdx)   (clears dirty)
        └─ rootChild = windowObj+0x08
        └─ VIRTUAL [rootChildClass +0x1C](rootChild, surface, rect, flag)   ← the call site
              └─ kntrPaint (0x412980): for each visible child in array
                   @kntr+0x38 (count @+0x3C): recurse [childClass +0x1C](child, surface, localClip, flag)
                     └─ leaf painters: butnPaint (0x435350), listWidgetPaint (0x41F820), …
        └─ widgetBlit(pv, surface, rect)   → screen
```

---

## 1. widgetBase layout — re-verified against `widgetInstantiate` (0x408750)

CONFIRMED by direct disassembly this session (see also doc 17 §5):

| Offset | Content | Source |
|---|---|---|
| +0x00 | magic `0x5655D881` | `MOV [child], 0x5655d881` @0x408853 |
| +0x04 | class object ptr | @0x408a12 |
| +0x08 | **parent** (leaf widgets) / **root child** (window objects, set by `windowChildAttach`) | @0x408a09 / doc 17 + §7 here |
| +0x0C..+0x17 | raw geometry x,y,w,h (i16 each, from u16BE desc+04..0A) | @0x408870..8c |
| +0x1C..+0x27 | scaled geometry (scaleQuad 0x429C70) | @0x4088c8 |
| +0x2C | instCode (u32BE desc+0C) | @0x4088f9 |
| +0x30 | flags (u32BE desc+10) | @0x40892c |
| +0x34 | mode u16 = `(u16BE desc+20 & 0x18) \| 1` | @0x408962 |
| +0x37 | desc+0x23 byte | @0x408939 |
| +0x38.. | class-specific | alloc = `max(classObj+0x08, 0x38)` |

Attach order (CONFIRMED): parent magic checked → `[parentClass+0x88]` must be
non-NULL (else `hError 0x10002`) → `attachFn(parent, child)` → **then**
`child+0x08 = parent` → `child+0x04 = classObj` → `initFn(child, payload=desc+0x28,
size=u32BE desc+0x14, b22=desc+22)` → if `mode & 0x4`: `0x409850(child)` → child
recursion gated by `[classObj+0x14]` (only KNTR has one) → advance
`0x28 + round4(size)`.

## 2. Class object layout — slot meanings (NEW, mostly CONFIRMED)

`widgetClassObj` (144 B, applied to all 21 objects in A1/A2). Slots verified
this session via cross-referencing `widgetInstantiate` (init @+0x0C,
childCount @+0x14), the slot installers, the default pv method table, the
virtual paint call in `labelPaint`, and the event dispatchers:

| Offset | Meaning | Evidence |
|---|---|---|
| +0x00 | tag (code constant u32LE = reversed spelling) | A2a |
| +0x04 | zero | data |
| +0x08 | instance size (u32LE) | `widgetInstantiate` @0x40883a |
| +0x0C | **initFn** `(child, payload, size, b22)`; NULL = no init | @0x408a1b |
| +0x10 | teardown (common default `0x409BE0`) | PROBABLE (not yet decoded) |
| +0x14 | **hasChildren** (KNTR only: `kntrHasChildren` 0x412860) | @0x408a8e |
| +0x18 | event-A slot (common default `widgetEventNoop` 0x409BF0 = empty) | data + decode |
| **+0x1C** | **PAINT slot** `(widget, surface, clipRect, flag)` | `labelPaint` virtual call `CALL [skinObj[1]+0x1c]` @0x40a0fc; KNTR/BUTN decodes |
| +0x20 | event-B slot (common default `widgetStateFlagSet` 0x409C70: event+0x18 ∈ {1,2,3} → `mode @+0x34 |= 0x40/0x80/0x100`) | decode |
| +0x24..+0x58 | class-specific event slots (window-table targets, §5) | winSlot1/2/3 decodes |
| +0x5C | state-notify | S1 |
| +0x88 | **attachFn** `(parent, child)` | @0x4089c7; decodes §7 |
| +0x8C/+0x90 | further class methods (WIND: 0x40A8C0/0x40A8E0; KNTR: 0x4137D0/0x413890 — undecoded) | data |

### Full 21-class slot table (this session, data-verified)

| Class | VA | size | initFn +0x0C | +0x10 | child +0x14 | +0x18 | **paint +0x1C** | +0x20 |
|---|---|---|---|---|---|---|---|---|
| VUU! | 0x4660C4 | 0x38 | 0x409BD0 (no-op) | 0x409BE0 | — | 0x409BF0 | 0x409C00 | 0x409C70 |
| WIND | 0x466188 | 0x28 | — | — | — | — | — | — |
| KNTR | 0x466690 | 0x70 | 0x412780 kntrWidgetInit | 0x412810 | 0x412860 kntrHasChildren | 0x412870 | **0x412980 kntrPaint** | 0x412B30 |
| TXTS | 0x466C80 | 0x5C | 0x41FDE0 | — | — | — (slots start at +0x20; no +0x1C) | — | 0x41F840 @+0x30 |
| LSTS | 0x466D44 | 0x4C | 0x409BD0 (no-op) | 0x421090 | — | 0x421130 | **0x41F820 listWidgetPaint** | 0x41F840 |
| CLST | 0x466E08 | 0x54 | 0x409BD0 (no-op) | 0x4218A0 | — | 0x421130 | **0x41F820 listWidgetPaint** | 0x41F840 |
| IMGS | 0x466ECC | 0x64 | 0x422BA0 | 0x422D30 | — | 0x41F800 | **0x41F820 listWidgetPaint** | 0x41F840 |
| BUTN | 0x4674A0 | 0x40 | 0x4352C0 | 0x435320 | — | 0x409BF0 | **0x435350 butnPaint** | 0x4353B0 |
| KLBL | 0x467564 | 0x48 | 0x4357F0 | 0x435850 | — | 0x409BF0 | 0x435870 | 0x409C70 |
| LABL | 0x467628 | 0x4C | 0x435BB0 | 0x435C30 | — | 0x409BF0 | 0x435C60 | 0x435D10 |
| BOX! | 0x4676EC | 0x44 | 0x435FF0 | 0x436040 | — | 0x409BF0 | 0x436070 | 0x409C70 |
| SEPR | 0x4677B0 | 0x38 | 0x409BD0 (no-op) | 0x4360F0 | — | 0x409BF0 | 0x436100 | 0x409C70 |
| BPMN | 0x467874 | 0x40 | 0x436430 bpmnWidgetInit | 0x436550 | — | 0x409BF0 | 0x4365E0 | 0x436670 |
| IKBT | 0x467938 | 0x50 | 0x436C00 | 0x436DC0 | — | 0x409BF0 | 0x436E60 | 0x436F10 |
| KOLR | 0x4679FC | 0x44 | 0x437240 | 0x437290 | — | 0x409BF0 | 0x4372C0 | 0x4374D0 |
| PRGS | 0x467B84 | 0x48 | 0x437DA0 | 0x437E80 | — | 0x409BF0 | 0x437E90 | 0x409C70 |
| SLDR | 0x467C48 | 0x44 | 0x438060 | 0x438100 | — | 0x409BF0 | 0x438160 | 0x4381A0 |
| TIKB | 0x467AC0 | 0x44 | 0x4378E0 | 0x437950 | — | 0x409BF0 | 0x437980 | 0x4379E0 |
| HOLD | 0x468188 | 0x40 | 0x43CC30 | 0x409BE0 | — | 0x409BF0 | 0x409C00 | 0x409C70 |
| MBAR | 0x46824C | 0x40 | 0x43CD50 | 0x43CDB0 | — | 0x43CDD0 | 0x43CDF0 | 0x43CE10 |
| IKON | 0x468310 | 0x78 | 0x43D130 | 0x43D220 | — | 0x409BF0 | 0x43D230 | 0x409C70 |

Notes:
- The three list-family classes (LSTS/CLST/IMGS) **share** paint slot
  `0x41F820` = `listWidgetPaint` = `0x448200(*(list+0x38) listView, surface,
  rect)` — one list-view renderer for all three (CONFIRMED).
- TXTS (text) has **no +0x1C paint slot** — text widgets are painted by the
  `labelPaint` surface dispatcher through their text object, not via their own
  class slot (consistent with the dispatcher reading `widget+0x0C`). PROBABLE
  (inferred from absence + dispatcher behavior; TXTS class slots not yet decoded).
- `0x409BF0` (event-A default) is an empty function; `0x409C70` (event-B
  default) sets mode bits 0x40/0x80/0x100 (CONFIRMED by decode).

## 3. The window record `pv` — an EXTENDED hapTextObj (CONFIRMED)

`windowCtor` (0x40BFA0) allocates a 0x120-byte record ("pv") per window.
`textWidgetGetRect` checks `obj->magic == 0xF0168873` at +0x08; `windowCtor`
stores exactly `0xF0168873` at pv+0x08, and pv+0x0C = hWin, pv+0x70 = 2
(fontIdx), pv+0x78..+0x84 = rect, pv+0x88 = dirty — the same field set the
`hapTextObj` type documents. **The window record is a hapTextObj** (surface
object) with a 0x8C..0x11F extension. This unifies windows and labels: both
are "surface objects" with dirty-rect + font + state; the window's content is
painted by delegating to the child widget tree (§5/§6).

```
pv layout (0x120 B, CONFIRMED by windowCtor disassembly 0x40C18a..0x40C258):
+0x00  next (linked list, head 0x466350; FUN_0040B490 maps hWin → pv)
+0x04  (zero)
+0x08  magic 0xF0168873
+0x0C  hWin (HWND)
+0x10..+0x47   14-slot window method table (56 B) — copied from 0x46624C by
               windowDefaultPaintInstall (memcpy(pv+0x10, 0x46624C, 0x38))
+0x48  windowObj (the WIND-class widgetBase; set last, @0x40C258)
+0x54  IDropTarget vtable ptr (0x466638); +0x58 refcount=1; +0x5C self=pv
+0x64  options word (VWIN window-own block+0; color-theme bits 0x7C00000; 0x200 = parentless)
+0x68/+0x6A  min size 50x50
+0x6C/+0x6E  max size 4000x4000
+0x70  fontIdx = 2
+0x74  set by window method 0x40CC30 (VWIN window-own block+4)
+0x78..+0x84  content rect (hapTextObj rect) — WndProc WM_PAINT writes it
+0x88  dirty flag (hapTextObj dirty)
+0x89  focus/active byte (1; then 3 or 4)
+0x8A  dragging flag (used by winMouseUp)
+0x8B..+0x8E  border L/T/R/B bytes (frame painter + coord adjustment)
+0x90/+0x91  edge-DIB selectors (frame painter)
+0x119..+0x11B  color bytes (from options via 0x42E7D0)
```

Returned by `windowCtor` → stored at `windowObj+0x0C`. So **for window
objects, `widget+0x0C` points to the pv surface object** — exactly the field
`labelPaint` reads as the text/surface object. (For leaf text widgets the
same field holds their own hapTextObj.)

## 4. The 14-slot window method table (pv+0x10..+0x47)

Default table @0x46624C (56 B, 14 dwords); per-window overrides are installed
through three small "slot setters" (each: NULL check, magic check 0xF0168873
@pv+8, then one store):

| Slot | pv off | default (0x46624C) | role (CONFIRMED by decode) | doku override |
|---|---|---|---|---|
| 0 | +0x10 | 0x409FC0 `labelPaint` | **content paint dispatcher** (WM_PAINT) | — |
| 1 | +0x14 | 0x40A170 `winSlot1Event567` | key events: code 5/6/7 → [rootChildClass +0x38/+0x3C/+0x40] | — |
| 2 | +0x18 | 0x40A2E0 `winSlot2Event914` | pointer events: code 9-14 → [rootChildClass +0x20..+0x34] (11=press→+0x28, 12=release→+0x30) | — |
| 3 | +0x1C | 0x40A380 `winSlot3Event1014` | events 0x10-0x14 → [rootChildClass +0x48..+0x54] | — |
| 4 | +0x20 | 0x40A450 `winSlot4PopupShow` | popup show (0x409E50(windowObj, windowObj+0x18)) | — |
| 5 | +0x24 | 0x40A4A0 `winSlot5ContextMenu` | context menu (menuObjectCtor 0x409F40 …) | — |
| 6 | +0x28 | NULL | (per-window) | **`docMenuBuild` 0x401350** |
| 7 | +0x2C | NULL | — | — |
| 8 | +0x30 | NULL | (per-window) | **`docResizeInit` 0x401440** (400×800) |
| 9 | +0x34 | 0x40A690 `winSlot9StateSync` | thunk → slot 10 | — |
| 10 | +0x38 | 0x40A5C0 `winSlot10StateSync` | pv state → `widgetStateSet(rootChild, 7, …)` | — |
| 11 | +0x3C | NULL | — | — |
| 12 | +0x40 | NULL | (per-window) | **`docWindowTeardown` 0x401300** |
| 13 | +0x44 | 0x40A6A0 `windowObjDtor` | window-object destructor (release rootChild, free +0x10, memFree) | — |

Installers (renamed): `winSlot6Set` 0x40AF80 → [pv+0x28]; `winSlot8Set`
0x40AFC0 → [pv+0x30]; `winSlot12Set` 0x40B000 → [pv+0x40]. `docCreate`
(0x401000) calls them with the three doku-specific methods (CONFIRMED —
`docCreate` decompiles to exactly `winSlot12Set(pv, 0x401300); winSlot6Set(pv,
0x401350); winSlot8Set(pv, 0x401440);` after `windowCreateFromBuiltIn`).

The doku slot functions (CONFIRMED by decode):
- **`docMenuBuild` (slot 6):** builds the document window's menu bar via
  `0x411290` (add item: id, label pstr, …, accel) + `0x411510` (separator):
  0xA1 "New", 0xA2 "Open …", 0xAA "Import Colors …", 0xA4 "Save", 0xA5 "Save
  As …", 0xA9 "Preview", 0x65 "About", 100 "Exit AppearanceEdit". Called with
  the BPMN menu widget object.
- **`docResizeInit` (slot 8):** `0x409A00(windowObj, 400, 800, 0x800000, 0)`
  — initial window size 400×800.
- **`docWindowTeardown` (slot 12):** unlinks the doc from
  `gOpenDocListHead` (0x414E00), `0x4187B0(doc+0x94)`,
  `fileDialogClose(doc+0x98)`, `fileDialogClose(doc+0x1A0)`,
  `fileClose(doc+0x90)`.

## 5. WM_PAINT — the full chain (S1 open item 1: CLOSED)

From the WndProc 0x40EB50 decompile (CONFIRMED):

1. `local_90 = FUN_0040B490(hWin)` → pv (list at 0x466350).
2. `FUN_0040EA50(pv, 0)` (pre-paint), `BeginPaint`.
3. Dev instrumentation: paint-rect XOR histogram at 0x466A54 (indexed
   0x466B58). (Harmless; noted for completeness.)
4. `uVar4 = FUN_0040E570(pv, hWin, hDC, &rcPaint, &outRect)` — **window chrome
   painter**: inner rect = client − border bytes (+0x8B..+0x8E); focus ring if
   pv+0x89 == 4; four edge DIB blits (alloc 0x40E450, fill 0x42D6D0,
   `dcBlitDib`); optional full fill if options (+0x64) & 8. No child content.
5. `EndPaint`; if no content flag → done.
6. Adjust `outRect` by border bytes; **if pv+0x88 (dirty) == 0: store rect at
   pv+0x78..+0x84, dirty = 1; else union-extend** (0x445AB0). (This is the
   hapTextObj dirty-rect protocol.)
7. `if (pv[4] == NULL) return;` → **`pv[4](pv[0x12])`** =
   **`labelPaint(windowObj)`** — slot 0 with the window object.

`labelPaint` (0x409FC0; S1 name retained; comment updated) then:
- `textWidgetGetRect(pv, &lineRect, 8, &state, &fontIdx)` — fetches the dirty
  content rect from pv (clears pv+0x88 on fetch);
- `skinObj = windowObj+0x08` (root child; NULL → return);
- `widgetStateSet(skinObj, 7, mappedState)`;
- per line (single line in this build): `bmpObjCreate`, offset/fill setup,
  **`CALL [skinObj[1] + 0x1C]` = `[rootChildClass +0x1C](rootChild, surface,
  rect, flag)`** — the per-child paint entry,
- `widgetBlit(pv, surface, lineRect)`.

`kntrPaint` (classKntr+0x1C = 0x412980; CONFIRMED by decode):
- converts the rect to local coords (subtract scaled x/y @+0x1C/+0x20),
  intersects with the view,
- saves bitmap state (`0x425A10`), **sets the bitmap ORIGIN to the kntr's
  scaled position (`0x425A50`)** — the hap-bitmap-layer save/translate/restore,
- for each child in the **array @kntr+0x38 (count u32 @kntr+0x3C)**: if
  `mode @child+0x34 & 0x08` (visible), intersect `child+0x1C..+0x27` geometry,
  `bmpSetClip`, **recurse `[childClass +0x1C](child, surface, localClip,
  flag)`**,
- restores bitmap state (`0x425990`).

Leaf examples: `butnPaint` (classButn+0x1C = 0x435350) reads state byte
@btn+0x36, flags @+0x3C, pointer-to-byte @+0x38 and calls
`bmpStateIconDraw(surface, btn+0x1C (scaled x,y), &state)`. `listWidgetPaint`
(LSTS/CLST/IMGS +0x1C = 0x41F820) delegates to `0x448200(listView @list+0x38,
surface, rect)`.

**Coordinate model (CONFIRMED):** each container level translates the shared
scratch bitmap's origin to its own scaled position and clips to child
geometry; leaf painters draw at their own (parent-local) position in
`widget+0x1C`. The scratch surface is blitted into the window DC once, at the
top level.

## 6. Event dispatch map (CONFIRMED by decode)

Window-level routing (pv slots) → root-child class slots:

| Source | Path | Event codes | Targets |
|---|---|---|---|
| keys (WM_KEYDOWN/SYSKEYDOWN) | WndProc → `winKeyDispatch` 0x40BD30 → **slot 1** | event+8 == 5/6/7 | [rootChildClass +0x38/+0x3C/+0x40] |
| mouse down (client) | WndProc → `winMouseDown` 0x40DD80 (region 1) → `winPointerPressRoute` 0x40D7B0 (sets `gPressedWinRecord` 0x466288, `gCapturedWinRecord` 0x46628C) → `winPointerEventDispatch` 0x40BCE0 → **slot 2** | 11 (press) | [rootChildClass +0x28] |
| mouse up | WndProc → `winMouseUp` 0x40E090 (border-adjusted) → 0x40BCE0 → **slot 2** | 12 (release) | [rootChildClass +0x30] |
| (slot 2 also serves codes 9, 10, 13, 14 → +0x20/+0x24/+0x2C/+0x34) | | | |
| (slot 3: codes 0x10-0x14 → +0x48..+0x54; caller not yet identified — open) | | | |

`winMouseDown` region classification (`0x42DE50`): 1 = client (press +
capture), 2 = title bar (drag, `gDragWinRecord`/`gDragMode` 0x466290/0x4662A4),
3 = border (resize, mode 3), 5/8 = edges, 6 = slot-5 callback: calls
`*(pv+0x24)` (the slot-5 function pointer) with (windowObj, ev) under the
`gSlot5CallbackActive` (0x4662A5) re-entrancy guard. `winMouseUp` cancels
drag modes 3/5/8/9 (clearing pv+0x8A via 0x40BED0) and releases capture.

Renamed drag globals (data): `gPressedWinRecord` 0x466288,
`gCapturedWinRecord` 0x46628C, `gDragWinRecord` 0x466290, `gDragStartX`
0x46629C, `gDragStartY` 0x4662A0, `gDragMode` 0x4662A4,
`gSlot5CallbackActive` 0x4662A5.

## 7. Child tree model (attach semantics, CONFIRMED)

- **Window:** `windowChildAttach` (classWind+0x88 = 0x40A830), called by
  `widgetInstantiate` when the window's root child (KNTR) is attached: sets
  `windowObj+0x08 = rootChild` (idempotent), propagates pv state to
  `widgetStateSet(rootChild, 7, …)`, invalidates pv (0x40CD70).
- **KNTR:** `kntrChildAttach` (classKntr+0x88 = 0x413760): appends the child
  to the **child array @kntr+0x38 (count @+0x3C)** via `0x440790`; propagates
  tab state: `childState = (kntr mode & 0x4) ? 2 : mode`.
- Leaf widgets: `child+0x08 = parent` (set by `widgetInstantiate` after the
  attach call).
- **Visibility:** `mode @+0x34 & 0x08` (skip in `kntrPaint`). Other mode bits
  (S1): 0x02 hilited, 0x04 (extra init in instantiate), 0x01 (always set),
  0x40/0x80/0x100 (set by `widgetStateFlagSet`).
- The window object itself is a WIND-class widgetBase (0x38 B): +0x00 magic,
  +0x04 classWind, +0x08 root child, +0x0C pv; `classWind` has no init/paint
  slots (all zero except attach @+0x88 and +0x8C/+0x90) — CONFIRMED by dump.

## 8. Ghidra mutations this batch (all read-back verified)

- **26 function renames:** `windowChildAttach` 0x40A830, `kntrChildAttach`
  0x413760, `kntrPaint` 0x412980, `butnPaint` 0x435350, `widgetEventNoop`
  0x409BF0, `widgetStateFlagSet` 0x409C70, `listWidgetPaint` 0x41F820,
  `winSlot12Set` 0x40B000, `winSlot6Set` 0x40AF80, `winSlot8Set` 0x40AFC0,
  `docWindowTeardown` 0x401300, `docMenuBuild` 0x401350, `docResizeInit`
  0x401440, `winSlot1Event567` 0x40A170, `winSlot2Event914` 0x40A2E0,
  `winSlot3Event1014` 0x40A380, `winSlot4PopupShow` 0x40A450,
  `winSlot5ContextMenu` 0x40A4A0, `winSlot10StateSync` 0x40A5C0,
  `winSlot9StateSync` 0x40A690, `windowObjDtor` 0x40A6A0, `winKeyDispatch`
  0x40BD30, `winMouseDown` 0x40DD80, `winMouseUp` 0x40E090,
  `winPointerPressRoute` 0x40D7B0, `winPointerEventDispatch` 0x40BCE0.
- **7 data renames:** the drag/press globals listed in §6.
- **28 function comments** (labelPaint, windowCtor, widgetInstantiate,
  kntrPaint, windowChildAttach, kntrChildAttach, winPointerPressRoute,
  winMouseDown, winMouseUp, winPointerEventDispatch, winKeyDispatch,
  winSlot1/2/3, winSlot4/5/10, windowObjDtor, docMenuBuild, docWindowTeardown,
  docResizeInit, winSlot6/8/12Set, listWidgetPaint, butnPaint,
  widgetStateFlagSet, widgetEventNoop, textWidgetGetRect).
- **15 prototypes** (kntrPaint, butnPaint, listWidgetPaint,
  windowChildAttach, kntrChildAttach, winKeyDispatch,
  winPointerEventDispatch, winPointerPressRoute, winSlot1/2/3, winMouseDown,
  winMouseUp, windowObjDtor, docResizeInit).

## 9. Corrections

1. **hapTextObj magic = `0xF0168873`** (code check in `textWidgetGetRect`
   `obj->magic != 0xf0168873`; stored by `windowCtor`). The previously
   recorded `0x1688173`/`0x01688173` (06-symbol-ledger L237/L294,
   s2-worklist L438) is **wrong** — corrected in the `textWidgetGetRect`
   comment; ledger entries flagged here.
2. **pv window record is a hapTextObj** (extended) — the "window record" and
   "text object" are one type; S1 docs described them separately. The
   hapTextObj struct (0x8C) documents the base fields (hwnd@+0xC, fontIdx@+0x70,
   rect@+0x78, dirty@+0x88) which pv uses verbatim.
3. `labelPaint`'s S1 comment ("Editor label painter… Label obj: +0x08
   skin/resource obj, +0x0C text obj") is **reframed**: +0x08 is the **root
   child** for window objects (set by `windowChildAttach`), +0x0C is the
   surface object (pv for windows). The function is the generic **surface
   paint dispatcher**.
4. KNTR child storage: **array @+0x38 + count u32 @+0x3C** (not a linked
   list; `0x440790` is an append-to-array). Earlier B2 note "child list"
   corrected.

## 10. Per-function parameter/local audit (B2 gate)

| Function | Params audited | Locals audited | Notes |
|---|---|---|---|
| kntrPaint | 4 named (widget, surface, clipRect, flag) | — (all compiler temporaries; no meaningful stack vars) | prototype applied; call sites (labelPaint, recursion) consistent |
| butnPaint | 2 named (btn, surface) | — | prototype applied |
| listWidgetPaint | 3 named (list, surface, rect) | — | prototype applied |
| windowChildAttach | 2 named (windowObj, child) | — | prototype applied |
| kntrChildAttach | 2 named (kntr, child) | — | prototype applied |
| winKeyDispatch | 2 named (pv, event) | — | prototype applied |
| winPointerEventDispatch | 2 named (pv, event) | — | prototype applied |
| winPointerPressRoute | 2 named (pv, event) | — | prototype applied |
| winSlot1/2/3 | 2 named each (windowObj, event) | — | prototypes applied |
| winMouseDown | 2 named (pv, event) | — | prototype applied; region codes documented |
| winMouseUp | 2 named (pv, event) | — | prototype applied |
| windowObjDtor | 1 named (windowObj) | — | prototype applied |
| docResizeInit | 1 named (windowObj) | — | prototype applied |
| docMenuBuild / docWindowTeardown / winSlot6/8/12Set / winSlot4/5/9/10 / widgetEventNoop / widgetStateFlagSet | audited, left with decompiler defaults | — | single-purpose installers/short bodies; names+comments carry the semantics (deferred: no high-value retype) |
| labelPaint | 1 (windowObj — comment updated; S1 param name `label` retained to avoid churn) | — | dual role documented |
| textWidgetGetRect | 5 (S1 names kept) | — | magic corrected in comment |

## 11. Coverage matrix (B2)

| Category | Inspected | Already correct | Changed+verified | Deferred | Blocked |
|---|---|---|---|---|---|
| Functions (renamed) | 26 | 0 | 26 | 0 | 0 |
| Globals (renamed) | 7 | 0 | 7 | 0 | 0 |
| Prototypes | 15 | 0 | 15 | 9 (documented above) | 0 |
| Comments | 28 | 0 | 28 | 0 | 0 |
| Parameters (named via prototypes) | 37 | 0 | 37 | 0 | 0 |
| Meaningful locals | 0 real (all compiler temporaries in these bodies) | — | — | — | — |
| Structures created/applied | 0 new (widgetClassObj/hapTextObj exist; pv typing deferred — see backlog) | — | — | pv record type | — |
| Call-graph edges confirmed | WM_PAINT→slot0→[+0x1C] recursion; keys→slot1; press/release→slot2 | — | — | slot3 caller; +0x10 teardown role; TXTS slots; +0x8C/+0x90 class slots | — |

## 12. Open items / next targets

1. **Slot 3 caller** (events 0x10-0x14): which WndProc path (drag? double-
   click? 0x48E handler?) calls pv+0x1C — unresolved edge.
2. **pv record struct**: create a program-local `winRecord` (0x120 B) typing
   the pv layout and apply it where pv is materialized (deferred — needs
   care: pv is a runtime heap object, only referenced indirectly; low value).
3. **%MNU item decode** (B2 remainder): `menuPayloadParse` (0x412060) field
   layout via the 3 built-in menus (exam 0x45F900, fsit 0x45FB18, scal
   0x4602A8).
4. TXTS class slots (+0x20..+0x6C) — text widget event handlers.
5. Class +0x10 teardown (0x409BE0) and +0x8C/+0x90 methods.
6. Per-class leaf painters (KLBL 0x435870, LABL 0x435C60, TIKB 0x437980,
   IKBT 0x436E60, SLDR 0x438160, KOLR 0x4372C0, IKON 0x43D230, BPMN
   0x4365E0, BOX 0x436070, SEPR 0x436100, PRGS 0x437E90, MBAR 0x43CDF0) —
   one decode each for the paint-behavior ledger (Batch D/E material).