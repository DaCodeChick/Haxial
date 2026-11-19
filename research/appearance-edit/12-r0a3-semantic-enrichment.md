# R0-A.3 — Bidirectional call-graph semantic enrichment (HAP layer + render pipeline)

Session R0-A.3. Program: `AppearanceEdit.exe` (x86:LE:32, base 0x400000, 1526 functions).
Companion worklist/checkpoint: `r0a3-worklist.md` (persistent, updated per batch).

## 1. Scope and method

- **Seeds**: 84 HAP-layer/render-pipeline functions (R0-A/R0-A.1/R0-A.2 renames + task-2 carryovers).
- **Traversal**: 2-hop bidirectional BFS (84 → 561 nodes, 477 discovered non-seed), disassembly-signature classification of all 223 candidates, hop-2 filter to 258 meaningful nodes.
- **Tiers**: A = core pipeline (~150 fns, full per-function gate), B = peripheral UI builders (~200, lighter), C = boundaries (350 generic-only callers, B-APP shell, B-DYN indirects, text-raster/blit-converter families).
- **Per-function gate** (all tier-A audited fns): name evaluation, callers+callees (from traversal), every parameter inspected, every meaningful local inspected with disposition, return/CC evaluation, globals evaluated, mutations applied + read back.

## 2. Ghidra change totals (R0-A.3, all read-back verified)

| Category | Count | Notes |
|---|---|---|
| Function renames | **56** | batches 1–10 (see worklist audit log) |
| Global/data renames | **7** | gStyleRec, gStyleDef, gInkTbl, gInkCount, gIconGrid, gMainWindow, gAllocCount |
| Prototypes applied (typed) | **59** + 1 partial | partial: `searchRecords` cmp param (function-pointer typedef not supported by create_typedef; semantics documented in comment) |
| Local-variable renames | **67** | 3 labelPaint locals skipped (decompiler type confusion on its line buffer) |
| Comments (function) | **86** | including corrections |
| Types created | **2** | `hapDibSrc` (32 B), `hapTextObj` (140 B) |
| Structures modified | **1** | `hapBitmapObj` → 18 fields / 72 B (clip rect @0x28..34, fillMode @0x38) |
| Type applications | hapDibSrc ×2 (bmpBlitToSurface, msiBlobToBmp), hapBitmapObj ×~25 protos, hapTextObj ×1 | |
| Bytes patched | 0 | none (enrichment only) |

## 3. Key findings (all CONFIRMED via decompilation unless noted)

- **F6** DIB engine: `bmpBlitToSurface` (1–32bpp, 0x44e5xx converters) + `bmpBlitPalette` (1–8bpp, 0x4415xx converters) + `rectClipIntersect` (generic multi-rect clip, 9 params) + `bmpFillRect` (0xAABBGGRR, alpha blend `(px-ch)*a/255+ch`).
- **F7** Widget text rasterizes from the appearance **font glyph bitmaps** (`bmpTextDraw` → 0x44dfe0 glyph blit) — not GDI.
- **F8** Icon grid = 15×12 u16 slot table (gIconGrid 0x488AC0) → %IKN subrecords; cell states 0 / 0x40000 / 0x1000000.
- **F9** Button state icons: 3 state bits (0x01/0x02/0x20) → slots {9,10,11}/{21,22,23} in runtime-populated gStyleRec (0x466954; fallback gStyleDef 0x466950).
- **F10** Paint-surface lifecycle: bmpObjCreate → offsets/clip/fillmode → fills → widgetBlit → paintSurfaceRelease.
- **F13** D-color import from another v2 .hap: exactly 0xD8 bytes (54×u32) → dSub+0x16; dSub+0x0D bit 0x1000.
- **F15 (corrected)** %MSI: hotspotX @0x0C, hotspotY @0x0D, bpp @0x0E (2/8/32), palCount-1 @0x0F; transColor out = palette[1].
- **F20** F-section records join the same runtime ink list as v1 E volume inks (doc->inkVolumeList).
- **F21** v1 E rows hold up to two E blobs (layer A/B) → pairRecordBuild.
- **F25** pair-record storage bpp is AUTO from extracted palette size: <3→1, <5→2, <17→4, <257→8, else 24 (`paletteExtract`).
- **F26** C-section image blobs = 9-slice ext header + **classic Windows DIB** (BITMAPINFO, BI_RGB only, 24bpp or 1/2/4/8+palette, negative height = bottom-up; `dibInfoDecode` → 0x00BBGGRR).
- **F23** Built-in resource registry = FourCC-keyed binary-search table (0x45F848, 0x14B records).
- **F17/F18** Allocation = GlobalAlloc/Free counted by gAllocCount; hError = 0x90B doubled error frame → 0x414bf0 (noreturn).
- Header directory (word idx = byte/4): [0x2C]=A cap 0x88, [0x30]=A size, [0x34..0x58] = C/D/E/F/G (off,size) pairs; Block A payload @0x88; flags 0x7C/7D/7E/7F/80/81.

## 4. Per-function gate summary (tier A)

**Already gated (R0-A.2) — verified by read-back, no change:** hapParse, hapSerialize, hapLoadEntry, hapSaveEntry, hapCSectionRead, hapCBlobParse, hapDSectionReadV1/V2, hapESectionReadV2, hapEBlobParse, winBlitDib, dcBlitDib, widgetBlit (comment only), memZero, hapInk*/hapMsi* comments refined.

**Fully enriched this session (rename/proto/locals/comment + read-back):**
- Render/DIB: bmpBlitToSurface, bmpGetWH, paintSurfaceRelease, bmpSetOffset, bmpSetFillModeRaw, bmpBlitPair, bmpFillRect, bmpBlitPalette, paletteExtract, rectClipIntersect, dibInfoDecode, bmpInkBlit, bmpSetCellState, bmpSetMetrics, bmpSetClip, bmpSetFillMode, bmpTextDraw, bmpStateIconDraw, msiBlobToBmp, bmpObjSetTransparency32
- Widget painters: labelWidgetPaint/Fill, iconGridPaint/Fill, listRowPaint/Fill, compositeWidgetPaint, rectIntersects, labelPaint, labelMarkerDraw, iconGridCellState, fontTextDraw, fontMetricsGet, textWidgetGetRect, textWidgetStateGet
- Ink: inkSlotFetch, inkSlotDraw, widgetBaseFill, inkListAdd, inkListFinalize, pairRecordBuild
- HAP/doc: docCreate, createDocument, docSaveAs, hapDImportFromFile, fileOpen, fileCreate, fileReadAt, fileWriteWhole, fileClose, fileNameExtract
- Dialogs: openDialogExec, fileDialogClose/Cancel, fileDialogCreateSave/Open
- mem/fmt/error: memAlloc, memFree, memDup, memCopy, memAllocZeroed, memResize, hError, hErrorSimple, fmtInt, fmtSignedInt, pstr×8 (Copy/CopyTrunc/Append/AppendTrunc/AppendInt/AppendByte/Equal/ToRaw)
- Records/registry: searchRecords, lookupBuiltInRec, builtinRecCmp
- Objects: displayResourceSet, strObjGetData, filetimeNow, filetimeToString, tzOffsetMinutes, filetimeBreakdown, timeFieldsFormat, optionListGet, optionListSelect

**Partially enriched:** searchRecords (cmp param untyped — tool limitation), labelPaint (3 confused locals skipped).

**Deferred (documented):** 0x41A300 (1250-insn GDI compositing; decompiler task still PENDING after 40+ polls — task id 6cbfbe87-1ad5-4ff3-9232-5891bf2350ee saved in `r0a3_heavy_tasks`), 0x43A610 (fixed-point helper; task 22699dcd-f364-44ca-a205-e13a41edc5a2), 0x40E570 (off-window blit variant — low priority, dcBlitDib sibling), 0x44e5xx/0x4415xx converter families (dispatch evidence complete; per-fn naming deferred), tier-B UI builders (classified, not individually gated).

## 5. Call-graph coverage

- Seeds: 84 · Discovered (1-hop + 2-hop): 477 · Meaningful after filter: 258
- Visited/analyzed: ~561 (all seeds + discovered, classified by signature or decompilation)
- Fully enriched: ~70 (incl. R0-A.2) · Already correct: ~15 · Deferred/blocked: 4 functions + converter families
- Boundaries (recorded): B-EXT (Win32 imports), B-APP (shell/menu/message-loop fns), B-DYN (3 indirect call sites — vtable +0x1C pattern now understood as per-line virtual fill), B-GENUI (350 generic callers — editor chrome), 0x44E5xx blit-converter family (understood via dispatch switches)
- Unresolved edges: vtable dispatch targets beyond +0x1C (skin resource methods) — deferred to S1 (UI layer)

## 6. Open items (hand to S1/S2)

1. Retry deferred decompiles (task ids saved); classify 0x41A300 (editor preview DIB builder candidate).
2. Skin resource object (vtbl, FUN_004093e0 category/mode selection, +0x1C methods) — S1.
3. gStyleRec population path (who writes 0x466954 at document load) — S1.
4. hapDoc full field map consolidation (fields observed: +0x0C uiCtx, +0x2C..0x3C section lists, +0x30 dSub, +0x60/68/6C/100 strObjs, +0x70/74 ts labels, +0x78 optionsObj, +0x90 file, +0x98 openDlg, +0x9C path pstr, +0x1A0 importDlg, +0x1A8/1B0 tsPrev/tsLast, saveDialog/savePrep/unloadCb) — document in 05-ui-and-skin-model.md.
5. %IKN subrecord exact field map (0x43F2D0/0x43F430 decoded but byte 0x04/0x05 roles need corpus cross-check) — S2.
## 7. Post-audit correction

- **F26 downgraded**: `dibInfoDecode`'s sole caller (0x41d0b0) is a thunk that fetches
  the blob through function-pointer provider globals (0x48D30C..0x48D41C). The DIB
  layout is CONFIRMED, but the resource origin (C image vs font vs built-in VWIN)
  was **not** established from call sites — the function comment was corrected to
  match evidence. Resource-provider vtable to be resolved in S1.
