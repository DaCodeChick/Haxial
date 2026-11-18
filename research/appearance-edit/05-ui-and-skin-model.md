# 05 — UI and Skin Model (AppearanceEdit.exe)

Status: **initial** (session R0-A, 2026-11-17). Focus: what the editor's built-in
appearance DB tells us about the Haxial skin model. No on-disk sample evidence yet.

## 1. The editor is self-hosted on Haxial (PROBABLE, strong)

- The editor's own UI (menus + several windows) is constructed at startup from
  the **built-in appearance database** in `.data` (01-executable-architecture §5):
  `constructApp` makes 11 subsystem-init calls, and the 9-entry registry maps
  3 menu instances (`MENUexam`, `MENUfsit`, `MENUscal`) and 6 window instances
  (`VWINdoku`, `VWINefik`, `VWINemik`, `VWINepxm`, `VWINesik`, `VWINprvw`) to
  embedded structure definitions.
- Custom-drawn file dialogs ("Open/Save Appearance File:", "Choose a file to
  open:", "Save file as:", "Don't Save"/"Save All" prompts in `.rdata`) — the
  Haxial framework provides its own dialog widgets, not Win32 common dialogs.
- Only `SetDIBitsToDevice` is statically imported from GDI32; bitmap rendering
  goes through DIB blits (PROBABLE: the renderer copies indexed/DIB bitmaps
  directly to device).

## 2. Widget type vocabulary (CONFIRMED strings; semantics PROBABLE)

FourCC type tags seen in state names (byte order, spelling):

| FourCC | Probable widget | State strings observed (addresses) |
|---|---|---|
| `BUTN` | button | `DisabledBUTN` @ `0x4631D4`; `Default`+`BUTN` @ `0x463210/0x463218`; `Default Button Normal` @ `0x4644BD`; `Default Button Hilited` @ `0x4644D5`; `Icon Button Disabled` @ `0x46452D`; `Tick Button Blank/Tristated Disabled` @ `0x46457D/0x46462D`; `Mutex Button Ticked Disabled` @ `0x4646D9`; `Popup Button (No Title/Symbol) Disabled` @ `0x4647F5/0x46484D/0x4648A5` |
| `SEPR` | separator | `DisabledSEPR` @ `0x4624CC` |
| `VWIN` | (virtual) window | registry entries + embedded structures @ `0x4605D8` etc. |
| `MNU`/`MENU` | menu | registry entries + `%MNU` structures; `Menu Item (Pattern) Disabled` @ `0x46520D/0x465281` |
| `KNTR` | counter? | inside VWINdoku structure @ `0x46062C` (semantics unconfirmed) |

Other state-name families (widget inferred from name, FourCC not yet tied):
sliders (`H/V Slider Bar/Indicator/Pointed Indicator`, `…Disabled`), scroll bars
(`H/V Scroll Bar Disabled`), `Focus Box Disabled` @ `0x4648ED`,
`Color Chooser Disabled` @ `0x464975`, `Column Header Disabled` @ `0x464D09`,
`Window Close Button Disabled` @ `0x465359`, menu items with/without icon
(`Disabled Menu Item` @ `0x45F569/0x45FA28`, `Disabled With Icon` @ `0x45FABC`).

### State record sample (raw bytes, PROBABLE layout)

```
"DisabledBUTN" record @ 0x4631D8 (name at 0x4631D8):
0x4631D4: 00 00 00 08            | 0x08 = name length "Disabled" (PROBABLE)
0x4631D8: 44 69 73 61 62 6c 65 44  "Disabled"  (8 bytes)
0x4631E0: 55 54 4e 00            | "BUTN" + NUL
0x4631E4: 1E 00 28 00 78 00 42 00| four u16: 0x001E 0x0028 0x0078 0x0042
0x4631F0: 00 00 00 13 00 00 00 00| … u16 0x0013 …
0x46320C: 00 00 01 07            | 0x07 = "Default" length (next record)
0x463210: 44 65 66 61 75 6c 74 00| "Default" + NUL
0x463218: 42 55 54 4e 00         | "BUTN" + NUL
0x46321C: 82 00 28 00 DC 00 42 00| four u16: 0x0082 0x0028 0x00DC 0x0042
0x463234: … 13 00 …
```

Interpretation hypothesis (UNCONFIRMED): the four u16s are per-state metrics
(e.g. x/y/w/h or left/top/right/bottom) — note both records share `0x0028` and
`0x0042` (same y/height for two states of the same widget), while x/width
differ (0x1E/0x78 vs 0x82/0xDC). The `0x0013` (19) following may be a color
index or icon count. **Needs code-level confirmation.**

## 3. Window/menu instance semantics (HYPOTHESIS, to be confirmed)

- `MENUexam`/`MENUfsit`/`MENUscal`: three menus (exam=examination?, fsit=??,
  scal=scale?) — likely the editor's main menu, context menu, and scaling/tool
  menu. Names may be author's shorthand; do not rely on them semantically.
- `VWINprvw` = preview window (fits a skin editor: live preview of the edited
  skin). `VWINdoku` = document workspace? The other four (`efik`, `emik`,
  `epxm`, `esik`) are unmapped.
- Each VWIN structure contains repeated `0x90017C01` values, a "N N N " pattern
  (0x4E 0x20 ×4), a `KNTR` tag, and metric dwords — PROBABLE: window layout
  template (children descriptors, state colors, counters).

## 4. Drawing/input surface (from imports)

- Paint: BeginPaint/EndPaint, GetDC/ReleaseDC, InvalidateRect,
  SetDIBitsToDevice (DIB blit) — classic Win32 + DIB direct blit.
- Input: ToUnicode (keyboard), GetKeyboardState, SetCapture/ReleaseCapture,
  cursor creation (CreateCursor/GetCursor/SetCursor), GetDoubleClickTime.
- Clipboard (OpenClipboard/EmptyClipboard/SetClipboardData/GetClipboardData)
  with the "Cannot Cut"/"There is no image." strings → image cut/paste in the
  editor.
- Tray: Shell_NotifyIconW + "Minimize To Tray" string → editor minimizes to tray.
- DDE (DdeInitializeW/DdeNameService/DdeCmpStringHandles/DdeCreateStringHandleA/W/
  DdeGetData): live channel to a running Haxial application to push appearance
  changes (PROBABLE "Apply to running game" feature).
- OLE drag & drop (RegisterDragDrop, CoCreateInstance, DragQueryFileW):
  drag files (probably `.hap`) into the editor.
- Version probe: GetVersionExA (OS detection); monitor APIs loaded dynamically
  (multi-monitor support for the preview/editor layout).

## 5. Open mapping targets

- The 11 `constructApp` subsystem init functions (0x4361F0 … 0x43CD30) — which
  menu/window each builds.
- The main window WndProc (candidate `FUN_004038C0` from `constructApp`) —
  menu command IDs → actions (open/save/apply/export).
- Color model: the `0x0013`-style values and "Indexed Color Size" string @
  `0x456B05` ("Indexed Color Size: ") + "Height:" @ `0x456AB4` → the editor
  shows bitmap dimensions and palette size; Haxial bitmaps are likely indexed
  (256-color) — needs confirmation from bitmap handling code.
