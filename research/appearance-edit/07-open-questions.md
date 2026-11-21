# 07 — Open Questions and Blockers (AppearanceEdit.exe)

Sessions R0-A and R0-A.1, 2026-11-17.
R0-A.1 status: items resolved by the corpus + HAP-format work are struck through;
new questions from R0-A.1 are in §4.
**Session S1 (2026-11-18): state machine, skin install/dispatch, C-blob layout,
nine-slice runtime algorithm, painters — see §5 and docs 13–15.**

## High priority (format-critical)

1. ~~On-disk `.hap` layout is unconfirmed.~~ **RESOLVED** — 111-file corpus +
   2 built-in blobs; full spec in `04-hap-format.md`; inspector validates
   111/111 clean (`tools/research/hap_inspect.py`).
2. ~~Save-buffer builder not located.~~ **RESOLVED** — `hapSaveEntry`
   (`0x4033A0`) → `hapSerialize` (`0x402570`, v2 buffer: header + Block A +
   C/D/E/F/G) → file write; `hapLoadEntry` (`0x4036B0`) → `hapParse`
   (`0x402900`) for the load path. Field emission order documented in
   `04-hap-format.md` §4–§10.
3. **State-record field semantics** (the four u16 pairs after state+type in the
   built-in widget table) — still need the renderer consumer. (Note: R0-A.1
   showed the widget-descriptor region `0x4649xx`–`0x465xxx` is also the
   referent set of the v1 E volume map — possibly the same record type.)
4. **DDE usage** — still unresolved (search `DdeNameService`/
   `DdeCreateStringHandleW` callers).

## Medium priority

5. Byte-swapped fields in the built-in registry (`0x45F844` count, rec+0x0C,
   rec+0x10): still open. **New data point:** the on-disk HAP format uses BE
   for structural fields and LE for pixel/color data — the registry's in-memory
   byte-swaps may mirror the same convention (PROBABLE, unconfirmed).
6. Menu/window instance names → `constructApp` init mapping: still open.
7. `0x5657494E`/"VWIN" / `0x4D454E55`/"MENU" lookup context quirk: still open.
8. Bitmap/color model (DIB16/24/32, `SetDIBitsToDevice` caller): **partially
   resolved** — the file-side bitmap formats are fully specified (C/E bitmaps,
   %IKN 1/2/4/8/24bpp, %MSI 2/8/32bpp); the GDI drawing path is not.
9. 11 subsystem init functions in `constructApp`: still open.
10. Main window WndProc (candidate `FUN_004038C0`): still open.
11. ~~Formatters `FUN_00439CC0`/`FUN_00439D00`/`FUN_0043A610`: still open.~~ **RESOLVED (S1)** — 0x43A610 = `fmtByteCount` (K/M/G/T/P/E sizes); 0x439CC0 = `fmtSignedInt` (R0-A.3).
12. `FUN_00414BF0` terminal error handler / `FUN_00434420` record init: still
    open (note: `hapParse` error codes 0x10008/0x10009/0x1000A = bad
    version / bad magic / size-mismatch — now documented).
13. String class table @ `0x467D10` ("forbidden byte" rules): still open.
14. ~~Hash/map structure using `0x466984`/`0x466988` and `0x4683D4`
    (`FUN_00445530`).~~ **PARTIALLY RESOLVED** — `0x4683D4` is the embedded
    HAP v2 default blob B (`gBuiltinHapEvilChiaroscuroB`, 5 xrefs incl.
    `0x4455E3`); the "hash map" interpretation is likely wrong or refers only
    to `0x466984`/`0x466988`. Re-examine `FUN_00445530` as a blob consumer.

## Blocked / needs user input

- ~~No `.hap` samples~~ — **111 samples received** (`refs/appearances/`), all
  v1; 11 `.fnt` fonts (`refs/fonts/`); inventory in `08-corpus-inventory.md`.
- **No v2 `.hap` corpus sample** — the only v2 material is the two built-in
  blobs extracted from the exe. A v2 file saved by AppearanceEdit 1.400 would
  confirm the write path end-to-end.
- **No Haxial runtime/client executable** — the v1 E row-map question (§4.1
  below) needs it.
- Running the original exe is not part of this session (research-only).

## 4. New questions from R0-A.1

1. **v1 E row→widget map in other builds/runtime.** The 1.400 built-in map
   (rows 0/99–106) matches no corpus data (rows 1–95). Do older editors or the
   runtime use a dynamic map? (Blocks faithful v1 icon rendering.)
2. **%MSI Wmin/Hmin** (`+0x0C`/`+0x0D`) — strict-lower-bound constraint only;
   rendering role unknown (scalable glyph slot?).
3. **Option-list content** (header nibbles → doc+0x78+0x38 item list) — which
   editor setting is persisted (value 0x11 default)?
4. **v1 writer missing** — this build only writes v2 E (`[count][table]`);
   how were v1 192-row files produced (older build)?
5. **Embedded blob A** (`0x466DD4`, no xrefs) — purpose (build-time source?
   DDE payload? unused duplicate?).
6. **F/G section consumers** — how the runtime renders ink (%IKN) records and
   %MSI glyphs (volume widget?); the editor-side objects (doc+0x38, doc+0x3C)
   are not yet mapped to widgets.
7. **C preamble** (64 zero bytes) — reserved?
8. **doc+0x1B8** (header 0x08) — always 0 in all 123 files; semantics unknown.
9. **~~Timestamp semantics~~** — RESOLVED: last-save (A+8/A+12) is rewritten on
   every save (`hapSaveEntry` overwrites doc+0x1B0/0x1B4 with the current
   FILETIME and refreshes label doc+0x74); previous-save (A+0/A+4) persists
   from the file. See `04-hap-format.md` §5.

## Suggested next sessions (in priority order) — *superseded*

Pre-R0-A.2 list; item 2 (renderer pass / SetDIBitsToDevice caller) and the
color-model half of the renderer work were resolved in R0-A.2. Replaced by
the post-R0-A.2 next-stage plan at the end of this file (§6).

## 5. R0-A.2 status (2026-11-18)

### Resolved this session
- **Color byte order** (was: "0x00BBGGRR" label): on-disk bytes are
  `[00][RR][GG][BB]` (BE u32 0x00RRGGBB); GDI DIB pixel = bswap32 of the
  native load = 0x00BBGGRR. Confirmed by raw corpus bytes + OpenKDX
  cross-check. `04-hap-format.md` §7.3 corrected.
- **Nine-patch (9-slice) model**: C-blob extended header (flags&0x10) =
  [u32 colour][capL,capT,capR,capB][insetL,insetT,insetR,insetB]; verified on
  18/18 built-in v2 blobs (cap arithmetic, [L,T,R,B] order); v2-only feature
  (0/4101 v1 corpus blobs). Editor UI fields match exactly. §6 + 11 §2.
- **Rendering architecture**: only GDI import = SetDIBitsToDevice; composited
  32bpp top-down DIB blits, no scaling/alpha/GDI text. Render functions named
  (`winBlitDib`/`dcBlitDib`/`widgetBlit`/`labelPaint`). 11 §1.
- **Flag semantics**: 0x7C..0x81 are encoding selectors, always
  `01 01 01 01 00 00` in v1 corpus; presence = non-zero section length
  (80/111 E_size=0, 73/111 C_size=0). `04` §4 corrected.
- **Section directory framing**: 6 slots @ 0x2C..0x58 confirmed; OpenKDX's
  13-slot @ 0x0C framing disproven by built-in v2 `01 01` scale nibbles.
  cross-reference/00 §1.
- **Block A r3 display role**: "Creator" (info-tab screenshot).
- `FUN_00434420` (item 12) = `memZero` (renamed this session).

### New / carried questions
- **DIB builder (skin→32bpp expansion)**: palette + transparent-index +
  9-slice expansion functions in the 0x425xxx–0x42E3xx neighborhood
  (`FUN_00425C30` fill?, `FUN_00426610` text raster?, `FUN_0042A170`
  flagged text, `FUN_0042E370`/`FUN_0042DC90`/`FUN_004459E0` clip helpers) —
  UI-layer milestone.
- **Remaining 4 widget painters** (0x410960, 0x43BC00, 0x4514C0, 0x446770) —
  button/tick/scroll/list geometry math; adaptive scrollbar rules.
- **D 54-role table**: which role index each widget consumes (color grid
  screenshot `colors.png` = visual reference).
- **C-blob ext header**: semantics of the u32 colour (white/black in
  samples — backing/"transition underneath"?), and the inset group (one
  odd sample pair (5,0,5,0)/(0,5,0,5)).
- **`labelPaint` helper IDs**: `FUN_0040CE90` (line split), `FUN_004093E0`
  (resource select: type 7, modes 0/1/2/6), `.fnt` font rasterizer location.
- Carried: DDE (item 4), subsystem inits (9), WndProc (10), formatters (11),
  string class table (13), state-record fields (3), registry byte-swaps (5).

## 5. Session S1 resolutions (2026-11-18)

- **Widget state model — RESOLVED**: `widgetStateSet` (0x4093E0): u16 state
  @+0x0D, bits 0x01/0x02/0x20 (active/hilited/disabled), constraint rules,
  virtual notification via (widget+4) vtable+0x5C. Hilite writer:
  `buttonHoverSet` (0x43BDD0). Doc 13 §3.
- **Appearance install/dispatch — RESOLVED**: `skinInstall` (0x428C70)
  populates the fixed global section-pointer block (0x466950–0x4669B1) from
  the v2 HAP directory; v2-only; entry `appearanceLoadInstall`/`appearanceResetDefault`.
  D-role lookup `styleColorGet` (54 roles + built-in fallback); ink blit core
  0x44DFE0; paint methods template-dispatched ({fn, arg} tables in .data).
  Doc 13.
- **C-blob layout + 9-slice runtime — RESOLVED** (corrections to R0-A.2):
  caps in base header, palette before pixels, ext block @+0x14; edges =
  per-pixel replication, centre = solid fill / ext content fill. Doc 14.
- **Screenshot backlog — 11 of 22 examined in S1** (17/22 total; doc 15,
  doc 10 updated): all 8 remaining `ui-builtintheme/` screens (boxes,
  colorchooser, hscrollbars, listlabelcolors, menu, popupmenu, sliders,
  tickbuttons) + `app-builtintheme-blank/{colors,mouseicons,icons}.png`
  (D-role grid → `gColorRoleNames`; named %MSI/G cursor set; general named
  icon list matching pstr table @0x4626D0). 5 remain (icon/file-icon/info
  list views; corroborative only — name tables already recovered from the
  binary, doc 16).
- **Formatters — RESOLVED**: `fmtByteCount` (0x43A610), `fmtSignedInt`
  (R0-A.3).
- **fileClose registry — RESOLVED**: 0x41A300 unlinks two registry keys
  (0x4668D8/0x4668E8) on close when rec[6] set.

## 5.1 New S1 open items

1. **RESOLVED (S2 B2, doc 18)** — WM_PAINT → per-child paint call site:
   WndProc 0x40EB50 → chrome `FUN_0040E570` → slot 0 (pv+0x10, default
   `labelPaint` 0x409FC0) with (windowObj) → `textWidgetGetRect(pv)` fetches
   the dirty rect (pv is an extended hapTextObj) → **`[rootChildClass +0x1C]`**
   (rootChild = windowObj+0x08, set by `windowChildAttach` 0x40A830) = the
   per-child paint entry; `kntrPaint` 0x412980 recurses over the child array
   @kntr+0x38 (count @+0x3C), dispatching `[childClass +0x1C]` per visible
   child (mode@+0x34 & 0x08). Events: keys → slot 1 (0x40A170) →
   [childClass +0x38/+0x3C/+0x40]; press(11)/release(12) → slot 2 (0x40A2E0)
   → [childClass +0x28/+0x30].
2. D role → widget-element mapping (which of the 54 roles paints which
   element, per painter).
3. Runtime layout of embedded blob B (0x4683D4) beyond +0x52/+0x60/+0x64;
   blob-B assembly table (0x466DD4, 84 pointers; contains a "TSLC" string at
   +0xE8 — unrelated to the CLST list class, see 17 §6).
4. E-section runtime ink object layout (only byte length tracked globally);
   .fnt → ink pipeline.
5. C-blob `field0`/`field2`/`field4` semantics; secondary-mode (flags
   2/4/8) extra-row content + consumer.
6. `gStyleStrA/B` (0x466974/7C) and `gOncePtr` (0x46698C → 0x47B324) purposes.
7. Post-install hooks 0x40F220 / 0x41D390.

## 6. Next-stage plan (post-R0-A.2, 2026-11-18)

**Stage S1 — UI layer: widget geometry and DIB construction (Ghidra +
corpus)**
1. DIB builder: decompile the 0x425xxx–0x42E3xx neighborhood
   (`FUN_00425C30`, `FUN_00426610`, `FUN_0042A170`, clip helpers
   `FUN_0042E370`/`FUN_0042DC90`/`FUN_004459E0`) — confirm palette +
   transparent-index + nine-slice expansion into 32bpp buffers; name and
   type the pipeline (extend `hapBitmapObj` consumers).
2. Remaining 4 `widgetBlit` painters (0x410960, 0x43BC00, 0x4514C0,
   0x446770) — button/tick/scroll/list geometry math; adaptive scrollbar
   rules (arrows dropped below threshold, per `vscrollbars.png`).
3. D 54-role table: per-widget color-role indices (cross-check against
   `app-builtintheme-blank/colors.png` swatch order).
4. C-blob ext-header residues: u32 colour role (backing/transition?),
   inset-group semantics on the (5,0,5,0) samples; `labelPaint` helpers
   (`FUN_0040CE90`, `FUN_004093E0`) and the `.fnt` rasterizer.
5. Semantic-enrichment pass over S1 scope (prototypes, structs, comments —
   same discipline as `09` §1).

**Stage S2 — Remaining evidence closure**
6. ~~Examine the unexamined screenshots...~~ **11 done (S1)** — 17/22
   total; doc 15 §3–§7, doc 10. 5 list views remain (corroborative; name
   tables already recovered from the binary, doc 16).
7. State-record fields (item 3) + widget-descriptor blocks `0x4649xx`–
   `0x465xxx` (volume-map referents) — u16 metric meanings.
8. WndProc/menu dispatch (item 10) + DDE (item 4) + subsystem inits (item 9)
   — editor framework completeness.
9. Capture a real v2 save (hand-assemble from the spec if no VM is
   available) to close the write-path validation loop.

**Stage S3 — Rust re-implementation design (out of scope until S1/S2 done)**
10. Design the modern appearance format + toolkit around the confirmed
    general model: six-slot directory, on-disk `[00,R,G,B]` colors, 9-slice
    C records, composited 32bpp DIB rendering, bitmap-font text — with
    OpenKDX interop notes (cross-reference/00 §8) as input, not as the sole
    authority.
11. Runtime cross-check once a non-editor Haxial client capture is
    available (v1 E rows 1–95, F/G consumers, option nibbles).
