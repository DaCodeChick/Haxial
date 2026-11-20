# S1 — Widget Painters, State-Driven Composition, and Screenshot Evidence

Status: session S1. Painters decompiled in R0-A.3; state/hover writers and
D-colour lookup resolved this session (doc 13). Screenshot evidence: all 11
`refs/screenshots/appearance-edit/ui-builtintheme/` screens examined (plus
2 `app-beos/` from R0-A.2 and 3 `app-builtintheme-blank/` this session:
colors, mouseicons, icons).

## 1. Known paint methods (CONFIRMED)

| Function | addr | Widget | Role |
|---|---|---|---|
| `labelPaint` | 0x409FC0 | label/text | `widgetBaseFill` → per-line `labelWidgetFill` (text obj @+0x7C; per-line rect @+0x78, dirty @+0x88) |
| `buttonWidgetPaint` | 0x43BF60 | button family | per-element loop → `compositeWidgetPaint`; elements = 4 state words @+0x84/98/AC/C0 |
| `compositeWidgetPaint` | 0x43BC00 | button family | frame (9-slice C blob) + D-colour fills + icon (state banks) + text; the shared button/dropdown/menu/popup painter |
| `iconGridPaint` | 0x4514C0 | icon grid | grid of C-table icons (gIconGrid @0x488AC0, 180×u16 indices) |
| `listRowPaint` | 0x446770 | list row | per-row icon + text + striping; per-row virtual fill (doc 10 §list) |

Dispatch: no static vtable; `{methodFn, argPtr}` template tables in .data
(`tableButtonMethods` @0x45E140, `tableLabelMethods` @0x45C560, doc 13 §4).
`buttonWidgetPaint` has zero code callers — reached via child-descriptor
function pointers built from template tables. **Open edge:** the exact
WM_PAINT → per-child paint call site.

## 2. State-driven rendering (CONFIRMED)

Every interactive widget's paint is a function of:

1. **u16 state word** (label magic widgets @+0x0D; button per-element words
   @+0x84..): bits 0x01 (pressed/active), 0x02 (hilited/hover — set by
   `buttonHoverSet` on mouse enter/leave), 0x20 (disabled → bank B icons).
2. **Appearance resources**: D colour roles via `styleColorGet` (54 roles,
   per-role fallback to built-in), C icons via `gStyleRec+0x40` table, ink
   glyphs via `inkBlitCore`.
3. **Geometry**: widget rect @+0x2C..+0x38; 9-slice caps from the C blob
   (doc 14).

Painters never hardcode colours or sizes: every fill colour is a D role
index, every bitmap a C table slot, every glyph an ink entry. This is the
**general-purpose composition rule** — an appearance is (C images, D colour
roles, E ink, scale), and a widget is (geometry, state, resource references).

## 3. Window chrome (from screenshots, PROBABLE composition)

All screens share the built-in (red) appearance:

- **Title bar**: solid red band (D role), white centred title text (ink),
  window-drag icon at left (C icon — diagonal-hatch block, cf. C-table slot 0
  region), maximize (▣) + close (×) buttons at right (C icons on D-colour
  squares, 9-slice frames).
- **Frame**: 1–2 px red border around the whole window (9-slice frame blob,
  cf. BeOS screenshot's blue variant — same widget, different D role values).
- **Menu bar**: inline items ("MenuBar Example Tools"); selected item =
  red-filled band + white text; popup panel = 9-slice frame, dark fill,
  red border (menu.png, popupmenu.png).
- **Status/preview bar** at window bottom in some screens (small icons +
  text).

## 4. Scrollbars (hscrollbars.png, vscrollbars.png)

Composition per bar:

```
[arrow btn][track .........][thumb ............][track][arrow btn]
```

- **Double-arrow** variant: each end is a 2-arrow button (◄► / ►◄).
- **Single-arrow** variant: one ◄ / ► button per end.
- **Track**: dark flat band (D role fill; 9-slice or solid).
- **Thumb**: cross-hatch textured band (small C blob, 9-slice/replicated —
  the texture is the source bitmap's centre fill / edge replication per
  doc 14 §2).
- **Too small**: degenerate case renders a stub box (track + arrows only).
- **Disabled**: arrows greyed (bank B icons), no thumb.
- Exact per-pixel geometry function not yet pinned (open item, doc 13 §6);
  the composition above is what the screenshots require.

## 5. Sliders, tick buttons, lists (sliders.png, tickbuttons.png, listlabelcolors.png)

- **Sliders**: 1–2 px track line (D role); thumb shape variants: square,
  triangle, diamond (C blobs, 9-slice); disabled = greyed thumb. Vertical
  mirrors horizontal.
- **Tick buttons** (checkboxes): frame = 9-slice ext C blob (doc 14 §3:
  slot 9 / 21 banks) + centred mark glyph (slot 10/11 / 22/23): unchecked
  (frame only), ticked (check mark), tristated (dash); disabled = bank B
  (larger grey frames, per screenshot). **Mutex** variant: circular frame +
  same marks.
- **List**: header row (label text on lighter D fill), rows = [16×16 C
  icon][label text][right-aligned value]; **zebra striping** (row parity →
  two D roles); **per-row label colour** (the "List Label N - Color" demo
  renders each row's text in a different colour — text colour is a per-row
  attribute, not a fixed D role). Right-side vertical scrollbar.
- **Menu items**: [icon?][text][accelerator "^X" right-aligned]; states:
  normal (white), disabled (grey text + lighter band), ticked (check glyph
  prefix), selected (red D-role band + white text). Long text truncated
  with "…". Two-line items supported ("Purple Icicles / And Pink Kumquats").

## 6. Boxes, color chooser, misc (boxes.png, colorchooser.png, misc.png)

- **Boxes**: plain etched frame, titled frame (label overlapping the top
  frame line at left), raised bevel frame (light top-left / dark bottom-right
  1-px lines). These are **line-drawn** (D roles), not bitmap frames.
- **Color chooser dialog**: labels, R/G/B sliders with swatch + percent text,
  hex + decimal text inputs (black field, white text), New/Old colour
  swatches (solid fill of the actual RGB), Cancel/OK buttons (OK has
  focus-highlight border). Demonstrates that input fields, swatches and
  dialogs are all the same toolkit composition.
- **misc.png** (R0-A.2): progress bar, separators, group labels.

## 7. Cross-appearance invariance (CONFIRMED by app-beos + app-builtintheme-blank)

- BeOS appearance: same widget set; frame/title colours blue instead of red;
  button bevels flatter; 9-slice button edit visible (button-edit-uses-9patch.png).
- Blank built-in: all-C blobs blank/empty, D roles neutral grey — widgets
  still lay out and render (frames visible as grey 9-slice), proving the
  renderer does not depend on any specific appearance's content, only on
  the (C, D, E, scale) tuple.

## 8. Open items

- Scrollbar/slider geometry function addresses (composition is established;
  per-pixel code not yet attributed).
- D role → widget-element mapping table (which of the 54 roles paints
  track vs thumb vs title bar, etc.) — requires tracing `styleColorGet`
  argument constants in each painter; carried to S2.
- Secondary-mode C blobs (flags 2/4/8): no screenshot shows a two-layer
  artifact; consumer unexamined.
- Focus-highlight border colour source (D role vs fixed).