# 10 — Visual Evidence (Committed Screenshots)

Source: `refs/screenshots/appearance-edit/` (commit `1e9182d`, 22 PNGs,
8-bit RGBA). Three capture groups:

| Group | Count | Contents |
|---|---|---|
| `app-beos/` | 4 | AppearanceEdit running with the **BeOS1.0.hap** corpus appearance loaded |
| `app-builtintheme-blank/` | 7 | AppearanceEdit with the **built-in** (Evil Chiaroscuro) appearance, blank/empty document |
| `ui-builtintheme/` | 11 | "Preview GUI Items" window close-ups of the toolkit's own widgets, built-in theme |

Note: the AppearanceEdit application *is itself a Haxial toolkit client*,
so every screenshot shows the real toolkit rendering real widgets with a
real appearance — direct runtime evidence (a Haxial client executable was
not otherwise available; the editor serves as one).

## Examined in detail (this session)

### `app-beos/button-edit-uses-9patch.png` (887×467)
**Title: "Button Normal"** — the C-section image editor for a button's
normal state. Fields: *Left Cap Width: 4, Right Cap Width: 4, Top Cap
Height: 4, Bottom Cap Height: 4*, *Left/Right/Top/Bottom Position*
(empty), *Transparent Color: None*, *Text Color: black*, *Transition
(underneath): None*, *Start Color / End Color*, *Left/Right/Top/Bottom
Inset: 0*. Preview pane shows the BeOS button bitmap (gray bevel) with
the 4-px cap grid overlaid (corner/edge cells vs central cell).
**Correlation: CONFIRMS the nine-patch model** — see
`11-widget-geometry-and-rendering.md` §2. The 4/4/4/4 caps here match
the on-disk extended-header cap bytes of the BeOS appearance's button
blobs.

### `app-builtintheme-blank/images-edit.png` (883×471)
Same "Button Normal" dialog under the built-in theme, caps all 0, empty
light-gray bitmap, 9-slice grid still overlaid; main editor's toolbar
visible behind ("Current position", "Current branch"). Shows the editor
is theme-independent (re-skinned by the loaded appearance).

### `ui-builtintheme/buttons.png` (476×472)
"Preview GUI Items" → *Buttons* category: raised **Button** (white
text, gray bevel), **Disabled** (desaturated), **Default** (red focus
ring), **Def Dis**, **Icon Button** (small color glyph + text),
**Disabled Icon Btn**, empty **dropdown**, grayed dropdown, black text
field + chevron, **Color Chooser** swatch. Built-in red title bar with
window controls. **Correlation: widget state set = normal / disabled /
default(focus) / icon** — matches C-section per-state blobs and the
`labelPaint` state modes (0/1/2/6).

### `ui-builtintheme/vscrollbars.png` (475×467)
"Vertical Scroll Bars": long **V Disabled** bar (arrows + track,
grayed), **V Double Arrows** (up+down arrows, thumb mid-track),
**V Single Arrows** (medium, thumb), **V Too Small** (arrows dropped,
bare track). **Correlation: scrollbars are composite** (arrow skins +
track color + thumb skin) with adaptive geometry — arrows omitted when
space is insufficient. See 11 §3.

### `ui-builtintheme/misc.png` (477×471)
"Miscellaneous": Primary Label, text box (red focus ring), 2-column
**list box** (Column 1/Column 2 headers, "an item / 123K" rows,
embedded v-scroll), h-scroll with double arrows, red **progress bar**
with value "50" in red text, two **sliders** (track + square thumb),
Button/Disabled/Default, empty dropdown, **Tick Button** (✓ checked) /
Tick Disable, icon button, red octagon **STOP** icon (a built-in E/G
skin icon rendered standalone). **Correlation: covers list, progress,
slider, checkbox, label, textfield, icon** — the general widget roster
of the toolkit.

### `app-beos/info.png` (487×547)
Information tab for **BeOS1.0.hap**: *Name: BeOS, Version: 1.0,
Creator: Jason Toffaletti, Description: "An appearance for fans of
BeOS."*, **Created: 11 Dec 2002, 03:03:37 AM**, **Modified: 10 Jan
2003, 04:54:46 PM**, *Scale:* (empty dropdown).
**Correlation (CONFIRMS 04-hap-format.md §5):**
- The four Block A strings are displayed as **Name / Version / Creator /
  Description** (r1..r4) — the label for r3 is "Creator" (a.k.a.
  credits).
- Created/Modified = Block A timestamp-1/timestamp-2 rendered by
  `filetimeToString` (format code 0x3020 → "11 Dec 2002, 03:03:37 AM").
- "Scale" = the header 4+4-bit option (header+0x07 high nibble /
  +0x0D low nibble, `optionListSelect(hi<<4|lo)` in `hapParse`); empty
  = no scale selected (both nibbles 0 in this file).
- Title bar shows the filename; the BeOS theme's red gradient chrome
  (hatched close button, square window controls) is the appearance's
  window decoration resources.

Sessions S1 examined 11 more (2026-11-18): all 8 remaining
`ui-builtintheme/` screens + `app-builtintheme-blank/{colors,mouseicons,
icons}.png`. `colors.png` = D-role grid matched against `gColorRoleNames`
(doc 16 §1); `mouseicons.png` = named %MSI/G cursor set (Standard, Standard
Add, Standard Link, Text, Crosshair, Crosshair Dot, Crosshair Circle, Wait,
No — rendered red under the built-in red theme, confirming mouse cursors
are appearance resources; its bottom H scrollbar shows the cross-hatch
"Grips" indicator, doc 16 §2); `icons.png` = general named icon list
(Stop/Note/Caution/Question/Haxial/Exit/Settings/About/Help — matches the
pstr table @0x4626D0 on disk; file-type names @0x462B70 corroborate
fileicons.png). Details: `15-s1-widget-painters.md` §3–§7,
`16-s1-named-resource-tables.md`.

## Inventoried, not yet examined (backlog — 5 remaining, 17/22 done)

| File | Group | Expected content (from name) |
|---|---|---|
| `app-beos/icons.png` | beos | named icon list under BeOS theme |
| `app-beos/fileicons.png` | beos | file-icon set (folder/… names @0x462B70), BeOS theme |
| `app-builtintheme-blank/fileicons.png` | builtin | file-icon set, empty doc |
| `app-builtintheme-blank/images.png` | builtin | images tab (C-section editor list), empty doc |
| `app-builtintheme-blank/info.png` | builtin | info tab, blank doc (timestamp zero-state) |

Remaining 5 are list views corroborating name tables already recovered from
the binary (doc 16); low architectural value.

## Cross-checks enabled by these screenshots

1. Nine-patch parameter set matches C-blob extended-header bytes
   (11 §2) — editor fields ↔ disk format.
2. Widget state set (normal/disabled/default/icon) matches per-state
   C-blob indexing and `labelPaint` modes.
3. Block A metadata display (name/version/creator/description + two
   timestamps + scale) matches parser/writer byte fields exactly.
4. Adaptive scrollbar geometry (arrows dropped when small) matches
   runtime-computed geometry + skin pieces (no per-size bitmaps).
5. The editor app is a Haxial client rendered by the toolkit — every
   screenshot is runtime evidence of the toolkit, not of a third-party
   app.
