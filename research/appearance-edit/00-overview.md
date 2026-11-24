# 00 — AppearanceEdit.exe: Overview and Session Log

## Target

| Field | Value |
|---|---|
| Program | `AppearanceEdit.exe` |
| Ghidra project path | `/AppearanceEdit.exe` |
| Host file | `/Users/schala/Downloads/AppearanceEdit.exe` |
| Format | Portable Executable (PE) |
| Language | `x86:LE:32:default` (Windows x86, 32-bit) |
| Image base | `0x00400000` |
| Address range | `0x00400000` – `0x00494FFF` |
| Entry point | `0x004456C0` |
| Functions | 1384 total (9 named at session start; rest `FUN_*` auto-named) |
| Code size | ~308 KB in `.text` (`0x00401000`–`0x00452FFF`) |

## Purpose

Haxial AppearanceEdit.exe is the original Windows skin editor for the Haxial UI toolkit.
It reads and writes **Haxial Appearance** files (`.hap`). The long-term project goal is a
clean, modern Rust reimplementation of the Haxial skinnable UI toolkit with new versioned
binary formats; this repository is the reverse-engineering research base for that effort.

## Session log

### Session R0-A — 2026-11-17 — initial reconnaissance

- Verified Ghidra MCP connectivity (93 tools exposed; full read + program-local
  mutation capabilities available).
- Verified active program is AppearanceEdit.exe before any mutation.
- Confirmed program metadata, segments, entry point, import table (113 imports).
- Mapped startup path: entry → WinMain → earlyInit → constructApp →
  mainMessageLoop → shutdownApp (see 01-executable-architecture.md).
- **Established Pascal-string representation rules** and recovered the full
  16-function pstr helper cluster (see 02-strings-and-fourcc.md).
- **Established FourCC conventions**: natural byte order in data;
  big-endian integer form when passed as 32-bit code constants (e.g. "VWIN" →
  0x5657494E).
- Located and decompiled the file/stream layer: FileRec object (magic
  0x1CA6C39A), fileOpen/fileCreate/fileReadAt/fileWriteWhole (see 03-file-io.md).
- Discovered the **built-in default appearance database** in `.data` (base
  0x45F830): 9-entry registry (3 MENU + 6 VWIN instances) plus widget state
  table with BUTN/SEPR state records (see 04-hap-format.md, 05-ui-and-skin-model.md).
- Applied and verified 36 program-local symbol renames (31 functions, 5 globals);
  batch rename 100% success; spot-checked via re-read and re-decompile (see
  06-symbol-ledger.md). No GDT archive-provided definitions exist in this
  program; none touched.
- Ghidra project saved at session end.

Status: **complete for R0-A scope**. Next session: `.hap` save/load buffer
builder (see 07-open-questions.md).

### Session R0-A.1 — 2026-11-17 — HAP format reconstruction from corpus

- **Inventory + validation of the reference corpus**: 111 `.hap` (all v1) + 11
  `.fnt` (all v2). Built two read-only, bounds-checked tools:
  `tools/research/hap_inventory.py` (headers + sha256 →
  `tools/research/corpus-inventory.json`) and `tools/research/hap_inspect.py`
  (full structural inspector/validator). Full-corpus run: **111/111 clean**.
  (See `08-corpus-inventory.md`, `../fonts/00-corpus-inventory.md`.)
- **Fully specified the HAP on-disk format** — header (0x88, all multi-byte
  fields big-endian), Block A (timestamps + 4 display strings), sections C
  (512-slot table + C-bitmap pool), D (v1 = 204 words + built-in permutation;
  v2 = 54 direct), E (v1 = 192-row table + E-bitmap pool; v2 = [count][table]
  + %IKN pool), F (%IKN ink records), G (%MSI glyph records); color encoding
  0x00BBGGRR. Writer = `hapSerialize` (v2); parser = `hapParse`. (See
  `04-hap-format.md`, rewritten.)
- **Critical compatibility finding**: the v1 E row→widget map is NOT in the
  file — it is a built-in table in the editor (rows 0/99–106 in this build),
  while every corpus file stores E data in rows 1–95. AppearanceEdit 1.400
  therefore renders no v1 E icons; v1 E content is a legacy payload from
  older builds/the runtime. (See `04-hap-format.md` §8.3, `08` §1.5.)
- **Recovered two embedded HAP v2 default blobs** ("Evil Chiaroscuro 2.0")
  from the executable: complete blob A @ 0x466DD4 (70,304 B, C/D/E/F/G, no
  xrefs) and referenced blob B @ 0x4683D4 (D-default source). Extracted to
  `assets/builtin-EvilChiaroscuro-v2-{A,B}.hap`; both validate clean under the
  inspector (the only real v2 samples). Blob A's F/G sections confirm the
  %IKN (25 records, `data`/`font/`/`text/` paths, 1/24bpp) and %MSI (19
  2bpp glyphs) record formats.
- Applied and verified **45 program-local renames** (40 HAP-layer functions,
  5 built-in data tables/blobs). First batch pass 22/45 (23 identifiers failed
  on uppercase-hex vs. Ghidra's lowercase auto-names); retry 23/23. Spot-checked
  via `get_function_info` read-back. See `06-symbol-ledger.md` (R0-A.1 section).
- No GDT archive-provided definitions touched; no structure/enum types created.
- Ghidra project saved at session end.

Status: **complete for R0-A.1 scope**. Next: runtime cross-check (v1 E row
map, F/G consumers), renderer pass (widget state table / DIB model), DDE
(see `07-open-questions.md`).
### Session R0-A.2 (Phase 1–4) — 2026-11-18 — Semantic enrichment, rendering model, visual + cross-impl audit

- **Ghidra semantic enrichment (HAP layer)** — 24 program-local types created
  and read-back verified (enums `hapBpp`/`hapIknBpp`/`hapMsiFormat`/
  `hapSecondaryMode`, typedef `hapColor`, 9 on-disk structs, 11 runtime
  structs incl. `hapDoc` 448 B); 34 prototypes applied + read-back verified
  (parameters typed to `hapDoc*`/`fileRec*`/`hapBitmapObj*`); 45 local
  variable renames; 9 + 4 function renames (`memZero`, `bmpObjCreate`,
  `bmpObjSetTransparency`, `docCreate`, `strObjGetData`, `memAlloc`,
  `memFree`, `filetimeNow`, `fileNameExtract`; render path `winBlitDib`,
  `dcBlitDib`, `widgetBlit`, `labelPaint`); 25 + 4 function comments
  read-back verified; 7 global data types applied (incl. `byte[70304]`/
  `byte[40336]` built-in blobs); `hapDoc.pad_64 → strObjVersion`. See
  `09-ghidra-semantic-enrichment.md` (coverage matrix §8) and
  `06-symbol-ledger.md` (R0-A.2 sections).
- **Skin rendering model (CONFIRMED)**: the ONLY GDI import is
  `SetDIBitsToDevice`; all rendering = composited 32bpp top-down DIB blits
  (28-byte descriptor [w][h][?][stride][?][pixels]); no scaling, no alpha,
  no GDI text (bitmap-font rasterization into temp bitmaps). **Nine-patch
  (9-slice) model CONFIRMED** via C-blob extended header (flags&0x10 → 0x20
  header: [u32 colour][capL,T,R,B][insetL,T,R,B]) — cap arithmetic verified
  on all 18 extended blobs of the built-in v2 appearance (0/4101 corpus v1
  blobs extended → v2 feature). See `11-widget-geometry-and-rendering.md`.
- **Visual evidence**: 22 committed screenshots inventoried; 6 examined in
  detail (9-patch button editor, Preview GUI Items set, BeOS info tab).
  Info tab confirms Block A = Name/Version/Creator/Description + two
  timestamps + Scale option. See `10-visual-evidence.md`.
- **Cross-implementation audit** (read-only): OpenKDX reconciled — header
  bytes identical; their 13-slot directory framing disproven by the built-in
  v2 `01 01` scale nibbles (our 6-slot @ 0x2C stands); **color encoding
  corrected** to on-disk `[00][RR][GG][BB]` (GDI DIB pixel = bswap =
  0x00BBGGRR); flag bytes are encoding selectors, presence = non-zero
  length (80/111 files E_size=0, 73 C_size=0). KDX (Scott Anderson) =
  protocol-only, no HAP work. See `../cross-reference/`.
- **Format corrections applied to `04-hap-format.md`**: §4 (directory
  framing, flag semantics), §6 (extended C-blob header + nine-patch),
  §7.2/§7.3 (color byte order + raw samples), §12/§13.
- Ghidra project saved after all mutations.

Status: **R0-A.2 Phases 1–4 complete**. Next: UI-layer milestone (remaining
`widgetBlit` painters, DIB builder expansion path, D 54-role table,
remaining screenshots) — see `07-open-questions.md` and
`11-widget-geometry-and-rendering.md` §6.

## Session R0-A.3 (2026-11-18) — COMPLETE

Bidirectional call-graph semantic enrichment over the HAP layer + render pipeline.
- Traversal: 84 seeds → 561 nodes (477 discovered), 223 classified, 258 hop-2 meaningful, 3 tiers.
- Ghidra (all read-back verified): **56 function renames, 7 global renames, 59 typed prototypes (+1 partial), 67 local renames, 86 comments, 2 new types (hapDibSrc, hapTextObj), hapBitmapObj → 18 fields/72 B**.
- Key: DIB engine (two blit paths + rectClipIntersect + alpha-blend fill), font-glyph text raster, icon-grid/state-icon machinery, %MSI field map (corrected), pair-record auto-bpp, classic-DIB decoder, file layer + error + pstr/mem/fmt layers fully gated, doc lifecycle + open/save/import pipelines.
- Docs: `12-r0a3-semantic-enrichment.md` (report + coverage audit), `r0a3-worklist.md` (durable checkpoint, per-batch audit log), `06-symbol-ledger.md` (R0-A.3 section).
- Deferred (documented): 0x41A300 + 0x43A610 decompiles (decompiler congestion; task ids saved), dibInfoDecode resource origin (S1), tier-B UI builders.

## Session S1 (2026-11-18) — COMPLETE (UI rendering pipeline, widget composition, resource dispatch)

Research + Ghidra enrichment milestone (no Rust, per task scope).
- **Global skin context**: `skinInstall` (0x428C70) populates fixed section-pointer block (gStyleRec=C base, gStyleDColors/D, gInkTbl/E, gInkF/F, gInkG/G, scale num/den, 5×7 metric matrix) from v2 HAP directory; v2-only install; entry `appearanceLoadInstall`/`appearanceResetDefault`. Doc 13.
- **Resource dispatch**: `styleColorGet` (54 D roles, per-role built-in fallback), C-table direct slot indexing, `inkBlitCore` (0x44DFE0) glyph/ink blit core; paint methods template-dispatched ({fn,arg} tables in .data; no static vtables). Docs 13 §2–4, 15 §1–2.
- **Widget state machine**: `widgetStateSet` (u16 @+0x0D, bits 0x01/0x02/0x20, constraint rules, virtual notify via (widget+4) vtable+0x5C); `buttonHoverSet` hilite writer; button widget object layout. Doc 13 §3.
- **C-blob + 9-slice CORRECTIONS** (supersede R0-A.2): caps in base header, palette before pixels, ext block @+0x14; runtime = corner copies + per-pixel edge replication + centre solid/ext-content fill. Doc 14.
- **Editor named resource tables** (on-disk scan): `gColorRoleNames` @0x461EC8 (6 groups, 53 named D roles) and `gEIconNames` @0x462E70 (155 E icon slots) — the concrete "editor-internal" E mapping; 11 more screenshots examined (17/22 total; composition per widget type). Doc 16, doc 15 §3–7.
- **Correction**: 0x48Dxxx "provider vtables" (R0-A.3) are the **.idata IAT** (unbound import entries), not runtime objects; dibInfoDecode's provider calls are import API calls. Doc 16 §3.
- Ghidra (all read-back verified): 20 function renames, 16 data renames, 19 function comments, 2 data plate comments, hapBitmapObj.fillMode→fillColor, nineSliceBlitC prototype. Docs 13–16 + 04/05/06/07/10/11 updates; `s1-worklist.md` checkpoint.

## Session S2 (2026-11-19/20/21) — IN PROGRESS (widget record reconstruction, FourCC semantics, UI evidence closure)

Priority item **CLOSED**: `MENUscal` is the (type=MENU, instance=scal) record of the
`%REZ` built-in UI registry @0x45F830 — a structured 20-byte (type4cc, instance4cc,
flags, size u32BE, offset u32BE) record, binary-searched; NOT an eight-char string.
- **`%REZ` registry** (9 records: 3 `%MNU` menus exam/fsit/scal + 6 `%VUU` windows
  doku/efik/emik/epxm/esik/prvw) — format, header, and lookup code fully
  code-verified (doc 17 §1).
- **`%VUU` payload + `widgetDesc` (40 B)** — window frame + recursive 40-byte
  widget descriptors (class/geom/instance/flags/size/mode/childCount) code-verified
  through `vuuPayloadParse`/`widgetInstantiate` (doc 17 §2–3).
- **Class registry: 21 class objects** — tag = code constant stored u32LE
  (byte-reversed spelling in memory); sizes/initFns verified; 3 new (WIND/LSTS/CLST);
  3 name corrections (KOLR/MBAR/SLDR) — doc 17 §6.
- **FourCC convention** — three representations (memory-ASCII / BE code constant /
  LE-stored tag), bswap sites identified; string-vs-FourCC re-audit of all 358
  four-char runs (doc 17 §4, §11).
- **`scaleQuad`** — all widget geometry scaled by gScaleNum/gScaleDen; this is the
  `scal` (Scale) menu's effect — doc 17 §7.
- **User-confirmed (2026-11-20)**: node = class ID + instance identifier; `%VUU` =
  "view"; developer C↔K naming eccentricity (KOLR=COLR etc.).
- Ghidra (all read-back verified): 24 function rename ops (21 new + 3 corrections),
  34 data rename ops (28 new + 6), 5 structures (rezHeader 24, rezRec 20, widgetDesc
  40, widgetBase 56, widgetClassObj 144 — all size-verified), 29 applications.
- Docs: `17-s2-fourcc-records.md` (new), `02-strings-and-fourcc.md` §1.4 rewritten,
  `06-symbol-ledger.md` (S2 section), `s2-worklist.md` checkpoint.
- **Batch A3 (2026-11-20)**: CLST/LSTS resolved as list widget classes (single/
  multi-column); view 0xFDB6D01A / model 0x8521B2D1 objects; D-section
  association disproven. **Batch B (part 1)**: rezHeader rebuilt + code-verified
  (+0x08 totalSpan u32BE, +0x14 count u32BE, no record pointer); widgetDesc
  re-verified (size = payload bytes after 40, advance 40+round4). **Batch C3**:
  all six %VUU window trees walked EXACT (209 records / 89 instances, tool
  `vuu_walk.py`, data `data/vuu-trees.txt`); widgetInstantiate fully re-decoded;
  KNTR/BPMN payloads + window-own block decoded (doc 17 §15).
- **Batch B2 (2026-11-21) — paint dispatch CLOSED**: the 0x120-B window record
  (pv) is an **extended hapTextObj** (magic 0xF0168873 @+0x08 — corrects the
  0x01688173 recorded in R0-A.3); 14-slot window method table (pv+0x10..+0x47)
  decoded with defaults @0x46624C + per-window slot setters (winSlot6/8/12Set);
  WM_PAINT chain fully traced: chrome 0x40E570 → slot 0 `labelPaint` →
  `[rootChildClass +0x1C]` → `kntrPaint` recursion over child array
  (kntr+0x38/+0x3C) → leaf painters → widgetBlit. Class slot table for all 21
  classes (init/teardown/hasChildren/event-A/**paint +0x1C**/event-B/attach).
  S1 open item 1 resolved. 26 fn + 7 global renames, 28 comments, 15
  prototypes — all read-back verified (doc 18, new).
- **Batch B2 remainder (2026-11-21) — %MNU CLOSED**: complete menu resource
  format (header/item/blob/menuObj, all offsets disassembly-verified — the
  decompiler's pointer display had misled the earlier pass), flags24 semantics
  (0x20000 tick / 0x40000 disabled / 0x50000 separator / 0x80000 static /
  0x100000 icon), BPMN payload {refA record-name-or-0, refB style, w2} with
  all 9 BPMN nodes mapped ("exam" = unreferenced sample), full open/select/
  toggle/dispatch/destroy lifecycle (bpmnEventPress → bpmnMenuShow →
  popupMenuShow → menuRowClickDispatch → toggle/select → selCallback or
  cmdHandler → widgetMsgBubble class+0x9C). Corpus walk EXACT: 47 items,
  zero leftover (tools `mnu_walk.py`, inventories in data/). 33 fn renames,
  9 prototypes, 15 comments, 5 new structs + widgetClassObj → 180 B, 6 data
  applications — all read-back verified (doc 17 §8 rewritten).
- **Architecture (2026-11-21)**: owner-approved Rust workspace decisions
  recorded in `docs/architecture/rust-workspace.md` (haxial-core, backend
  crates, haxial-ui, haxial-import → haxial-compat; design decisions, not RE
  findings).
- Remaining S2 batches: C (enrichment gate + widgetStateSet re-audit), D
  (geometry/part tables), E (resources/colors), F (font), G (C-blob), V
  (validation + docs 19–21).
