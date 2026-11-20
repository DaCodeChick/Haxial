# S1 — Editor Named Resource Tables (D Roles, E Icons) and the .idata Correction

Status: session S1 (2026-11-18). Found by on-disk scan of
`/Users/schala/Downloads/AppearanceEdit.exe` (the Ghidra-loaded binary; PE
sections: .text VA 0x1000/raw 0x400, .rdata VA 0x53000/raw 0x52000,
.data VA 0x5F000/raw 0x5DA00, .rsrc VA 0x8A000/raw 0x88A00, .bss VA 0x8E000,
image base 0x400000). Both tables are in **.data**, flat sequences of
**4-byte-aligned pstrs** (length byte, ASCII/UTF-8 text, zero padding to a
4-byte boundary).

## 1. D color role names — `gColorRoleNames` @ 0x461EC8 (CONFIRMED)

6 group headers (with UTF-8 U+25C6 "◆", bytes E2 97 86) interleaved with
**53 role names**. Entry order = D-section role index (the index passed to
`styleColorGet`, 0-based; the 54-slot section therefore has one unnamed
slot — index unresolved).

| Group | Roles (in order) |
|---|---|
| ◆ Primary Group ◆ (5) | Primary Light, Primary Background, Primary Dark, Primary Label, Important Label |
| ◆ Text Group ◆ (5) | Text Box Background, Text Box Foreground, Text Hilite Background, Text Hilite Foreground, Text Insertion Point |
| ◆ List Group ◆ (21) | List Background, List Sort Column Background, List Separator, List Hilite Background, List Hilite Foreground, List Label, List Label 1 (Red) … List Label 15 (Gray) |
| ◆ Icon Tints ◆ (4) | Icon Button Tint Hilited, Icon Button Tint Disabled, Menu Icon Tint Hilited, Menu Icon Tint Disabled |
| ◆ Miscellaneous ◆ (1) | Image Scroller Background |
| ◆ Graph Colors ◆ (17) | Graph Background, Graph Alt Background, Graph Lines, Graph Bar 0 … Graph Bar 9, Graph Text, Graph Legend Background, Graph Legend Text, Graph Legend Frame |

Cross-check: the `colors.png` screenshot shows exactly these names and
group headers in the Colors tab's list widget (swatch = current role value).
The "List Label N (Color)" demo rows in `listlabelcolors.png` are roles
16–30 (List Label 1–15) — the list widget renders each row's label with the
corresponding role colour.

**Semantic implications (CONFIRMED naming, PROBABLE usage mapping):**
- Primary Light/Background/Dark = the window/page base tints (title-bar
  frame red in the built-in red theme = one of these roles per appearance).
- Important Label = the red accent label (screenshot: red swatch).
- Text Hilite Background/Foreground = selected-text colours; Text Insertion
  Point = caret colour.
- List Hilite Background/Foreground = selected-row colours (dark red + red
  in the built-in theme).
- Icon/Menu Tint roles = the tint applied to icon-button/menu icons when
  hilited/disabled (explains the greyed icons in disabled widgets).
- Image Scroller Background = background behind image-scroller views.
- Graph roles = a graph/chart widget family (not visible in the preview
  screens — toolkit capability, no editor preview).

The per-painter role-index constants (which role each element uses) are the
consumer-side mapping still to be traced (open item, doc 15 §8).

## 2. E-section icon names — `gEIconNames` @ 0x462E70 (CONFIRMED)

**155 entries** = the editor's complete widget-icon registry. Entry order =
E icon slot index. This is the concrete "editor-internal E row→widget
mapping" flagged in R0-A.1 (§8.3): the v1 E rows of corpus files index
into this fixed 155-name set (the 192-row v1 layout of corpus files
therefore covers a superset/older numbering — reconciliation open).

Groups (in slot order):

1. Primary Background Pattern
2. Button / Default Button / Icon Button — × Normal/Hilited/Disabled
3. Tick Button Blank/Ticked/Tristated — × Normal/Hilited/Disabled (9)
4. Mutex Button Blank/Ticked/Tristated — × Normal/Hilited/Disabled (9)
5. Small/Medium Plus/Minus Button Normal (4)
6. Popup Button (× Normal/Hilited/Disabled), Popup Button No Title (×3),
   Popup Button Symbol (×3)
7. Focus Box × Normal/Hilited/Disabled
8. Horiz/Vert Separator Line
9. Box, Framed Raised Box
10. Color Chooser × Normal/Hilited/Disabled
11. Progress Bar, Fill, Non-Fill, Digit 0–9, Digit 100%
12. H/V Slider Bar × Normal/Hilited/Disabled; H/V Slider Indicator ×3;
    H/V Slider Pointed Indicator ×3
13. Column Header Normal/Hilited/Disabled
14. H/V Scroll Bar: Double Arrows, Single Arrows, Disabled, Too Small,
    Indicator Normal/Hilited, Indicator Grips Normal/Hilited, First/Second
    Left(Right)/Up(Down) Arrow Hilited, Single Left(Right)/Up(Down) Arrow
    Hilited
15. Menu Bar Pattern, Menu Bar, Menu Bar Title (Pattern) × Normal/Hilited/
    Disabled, Menu Background (Pattern), Menu Item (Pattern) ×
    Normal/Hilited/Disabled, Menu First/Last Item Hilited, Menu Separator
16. Popup Window Frame Normal/Focus
17. Window Frame Normal/Focus; Window Close/Minimize/Maximize/Menu/Resize
    Button × Normal/Focus/Hilited/Disabled

**State-icon bank reconciliation (doc 14 §3):** the checkbox/mutex banks are
not separate E slots — they are the Tick/Mutex Button icon slots (10–27)
selected by state bits; `bmpStateIconDraw`'s fixed slots 9/10/11 (bank A)
and 21/22/23 (bank B) are C-table offsets used for the small tick/mutex
glyphs, while the full named 9/9-variant matrix lives in E. The two
mechanisms compose: E provides the complete per-state widget icons; C
provides the 9-slice frames + glyph marks.

**Scrollbar evidence (doc 15 §4):** the E names explain the hscrollbars.png
variants exactly — "Double Arrows"/"Single Arrows" bar styles, "Too Small"
degenerate case, "Indicator" (thumb) + "Grips" (cross-hatch texture) +
per-arrow hilite states.

## 3. Correction: 0x48Dxxx "provider vtables" are the .idata (CONFIRMED)

R0-A.3 interpreted the globals at 0x48D30C–0x48D41C (values 0x0008D6xx–
0x0008D8xx in the static dump) as runtime-filled provider vtables read by
thunks at 0x41c7xx–0x41d1xx. The PE section table shows **0x48D000–0x48DCAC
= .idata**: those values are **unbound IAT entries** (self-pointers into
.idata, replaced by the PE loader at load time with the imported function
addresses). The "thunk family" are import thunks, and `dibInfoDecode`'s
calls through them are calls to imported APIs (consistent with R0-A.2:
`SetDIBitsToDevice` is the only GDI import in the skin path). There is no
provider-vtable object at those addresses; the "unresolved 0x8Dxxxx
targets" open item is closed as a misinterpretation. (The genuinely
runtime-filled globals remain .bss at 0x48E000+.)

## 4. Open items from this document

- The 54th (unnamed) D color role slot index.
- Reconciling the 155-name E registry with the 192-row v1 E layout of corpus
  files (and the v2 E count in built-in A).
- How the name tables are reached from code (no absolute immediate refs
  found on-disk; mechanism = indirect — carried, non-blocking).
- Per-painter D role-index constants (consumer mapping).