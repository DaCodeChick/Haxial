# R0-A.2 — Ghidra Semantic Enrichment Report

Program: `AppearanceEdit.exe` (x86:LE:32, image base `0x00400000`, 1521 functions)
Project: `/Users/schala/Documents/haxial.gpr` (saved at end of session)
Session: R0-A.2 (2026-11-18)

This document records every program-local Ghidra mutation made in R0-A.2 Phase 1
(semantic enrichment of the HAP layer), with evidence, read-back verification
status, and a category-by-category coverage matrix. All changes are
program-local; no GDT/archive types were touched.

---

## 1. Method

1. Decompiled each in-scope function with the decompiler after applying
   types incrementally, so later decompiles show the effect of earlier
   mutations (regression-checked).
2. Created custom types in DTM categories `/haxial/hap/disk` (on-disk
   formats), `/haxial/hap/runtime` (runtime objects), and `/haxial/hap`
   (enums). Every type was read back via `get_data_type` and size-verified.
3. Applied parameter/return/prototype semantics via
   `set_function_prototype` (C-prototype parsing) — one mutation per
   apply→read cycle. (Rapid successive prototype sets in one batch
   silently dropped all but the first; interleaved reads make each apply
   durable. See §9 Limitations.)
4. Renamed meaningful locals/parameters, added function comments, applied
   data types to global data, and verified each via read-back
   (`get_function_prototype`, `get_function_comment`, re-decompilation).

## 2. Types created (24) — DTM, category `/haxial/hap`

### Enums (`/haxial/hap`)
| Type | Values | Evidence |
|---|---|---|
| `hapBpp` | 1, 2, 4, 8 | E-v1 raw bitmap switch in `hapEBlobParse` (0x404700) |
| `hapIknBpp` | 1, 2, 4, 8, 24 | `%IKN` subrecord bpp switch in `hapInkSubParse` (0x43F2D0) |
| `hapMsiFormat` | 0, 1, 2 | `%MSI` format switch in `hapMsiRecordParse` (0x4452C0) |
| `hapSecondaryMode` | 0, 1, 2, 3, 4 | C-blob secondary-row mode (flags&0x10 path) in `hapCBlobParse` (0x406E20) |

### Typedefs
| Type | Base | Evidence |
|---|---|---|
| `hapColor` | `uint` | All D words / C-blob palette entries are 32-bit `0x00BBGGRR` words |

### On-disk structures (`/haxial/hap/disk`, packed)
| Type | Size | Evidence |
|---|---|---|
| `hapHeaderDisk` | 136 (0x88) | `hapParse`/`hapSerialize` field access + 111/111 corpus files (04-hap-format.md §4) |
| `hapBlockAFixedDisk` | 52 (0x34) | `hapWriteBlockA` (0x402370) + corpus (04 §5) |
| `hapERowV1Disk` | 16 | E v1 192-row table (`hapESectionReadV1`) + 31/31 corpus v1-E files |
| `hapCBlobHdrDisk` | 20 (0x14) | `hapCBlobParse` min-size check `CMP [ESP+0x14],0x14` + 4101/4101 corpus blobs |
| `hapCBlobHdrExtDisk` | 32 (0x20) | `hapCBlobParse` extended header (flags bit 0x10) |
| `hapEBlobHdrDisk` | 8 | `hapEBlobParse` (decoded fully this session — §7 Finding F1) |
| `hapIknHdrDisk` | 8 | `hapInkRecordParse` |
| `hapIknSubHdrDisk` | 12 | `hapInkSubParse` |
| `hapMsiHdrDisk` | 16 (0x10) | `hapMsiRecordParse` |

### Runtime structures (`/haxial/hap/runtime`)
| Type | Size | Evidence |
|---|---|---|
| `hapResEntry` | 20 (0x14) | C/E/G entry records; fields `tableIndex` (u16), `data` (ptr), `size` verified in `hapCSectionRead` decompile |
| `hapBitmapDesc` | 32 (0x20) | stack record zeroed by `memZero(&desc,0x20)` in `hapEBlobParse` |
| `hapBitmapObj` | 72 (0x48) | `bmpObjCreate` alloc size; transparency color +0x3C, flag +0x40, magic +0x44 verified in `bmpObjSetTransparency` |
| `fileRec` | 28 (0x1C) | magic `0x1CA6C39A`; `hFile` field used by `fileWriteWhole` in `hapSaveEntry` |
| `builtinRezHeader` | 24 (0x18) | global at 0x45F830 (applied, §5) |
| `builtinAppearanceRec` | 20 (0x14) | 9-entry registry at 0x45F848 (applied, §5) |
| `hapCSubObj` | 3556 (0xDE4) | doc+0x2C sub-object; entries at +0x4C (174 × 0x14) |
| `hapDSubObj` | 304 (0x130) | doc+0x30 sub-object; colors at +0x58 (54 × u32) |
| `hapESubObj` | 788 (0x314) | doc+0x34 sub-object; entries at +0x54 (34 × 0x14), slotCount at +0x310 |
| `hapGSubObj` | 468 (0x1D4) | doc+0x3C sub-object; entries at +0x54 (18 × 0x14) |
| `hapDoc` | 448 (0x1C0) | full document object (allocated by `docCreate`); sub-object pointers + UI object pointers + timestamp words + flags (see §7 F3) |

Offsets of `hapCSubObj`/`hapDSubObj`/`hapESubObj`/`hapGSubObj`/`hapDoc` were
verified by forcing alignment (explicit gap fields) until all decompiler
field accesses (e.g. `doc->dSub->colors[i]`, `entry->tableIndex`) landed on
the documented byte offsets.

## 3. Prototypes applied and read-back verified (34)

All verified via `get_function_prototype` after application (zero residual
`param_N` or `undefined` in any of the 34).

| Address | Prototype |
|---|---|
| 0x402900 | `void hapParse(hapDoc *doc, uint *fileBuf, uint fileSize)` |
| 0x402570 | `uint * hapSerialize(hapDoc *doc, uint *outSize)` |
| 0x402370 | `void hapWriteBlockA(hapDoc *doc, uint *dst, uint dstSize)` |
| 0x4022E0 | `uint hapBlockSizeA(hapDoc *doc)` |
| 0x4070F0 | `void hapCSectionRead(hapDoc *doc, uint *sectionBuf, uint sectionSize)` |
| 0x407030 | `void hapCSectionWrite(hapDoc *doc, uint *dstBuf, uint sectionSize)` |
| 0x407000 | `uint hapCSectionSize(hapDoc *doc)` |
| 0x406E20 | `uint hapCBlobParse(ushort *blob, uint remaining, uint *outConsumed)` |
| 0x404460 | `void hapDSectionReadV1(hapDoc *doc, uint *sectionBuf, uint sectionSize)` |
| 0x404410 | `void hapDSectionReadV2(hapDoc *doc, uint *sectionBuf, uint sectionSize)` |
| 0x4043D0 | `void hapDSectionWrite(hapDoc *doc, uint *dstBuf, uint sectionSize)` |
| 0x4043C0 | `uint hapDSectionSize(void)` (stdcall — benign: no params) |
| 0x404040 | `void hapDLoadBuiltInDefault(hapDSubObj *dSub)` |
| 0x405310 | `void hapESectionReadV1(hapDoc *doc, uint *poolBuf, uint poolSize)` |
| 0x405210 | `void hapESectionReadV2(hapDoc *doc, uint *sectionBuf, uint sectionSize)` |
| 0x404700 | `hapBitmapObj * hapEBlobParse(ushort *blob, uint remaining)` |
| 0x4048D0 | `uint * hapERowFetch(uint row, uint *poolBuf, uint poolSize, uchar *key, uint *outSize)` |
| 0x43F430 | `uint hapInkRecordParse(uint *record, uint remaining, uint *outConsumed)` |
| 0x43F2D0 | `uint hapInkSubParse(ushort *sub, uint remaining, uint *outSize)` |
| 0x405F50 | `void hapFSectionRead(hapDoc *doc, uint *sectionBuf, uint sectionSize)` |
| 0x408570 | `void hapGSectionRead(hapDoc *doc, uint *sectionBuf, uint sectionSize)` |
| 0x4452C0 | `uint hapMsiRecordParse(uint *record, uint remaining, uint *outConsumed)` |
| 0x4036B0 | `int hapLoadEntry(uint ownerCtx, fileRec *file)` |
| 0x4033A0 | `void hapSaveEntry(uint ownerCtx, hapDoc *doc, int forceDialog)` |
| 0x4057D0 | `void inkListAdd(uint *inkList, uint *blob, uint blobSize, int key)` |
| 0x405880 | `void inkListFinalize(uint *inkList)` |
| 0x4050B0 | `uint hapESectionSize(hapDoc *doc)` |
| 0x405D60 | `uint hapFSectionSize(hapDoc *doc)` |
| 0x408410 | `uint hapGSectionSize(hapDoc *doc)` |
| 0x43E390 | `uint * pairRecordBuild(uint *srcPtrs, uint count, uchar *key, uint flags, uint *outSize)` |
| 0x434420 | `void memZero(uint *dst, uint size)` |
| 0x4257C0 | `hapBitmapObj * bmpObjCreate(int w, int h)` |
| 0x428210 | `uint bmpObjSetTransparency(hapBitmapObj *obj, uint color, int enable)` |
| 0x401000 | `int docCreate(byte *nameLen)` |

## 4. Function renames this session (9) + local variable renames (45) + comments (25)

### 4.1 Function renames (all read-back verified)
| Address | Old | New | Evidence | Confidence |
|---|---|---|---|---|
| 0x434420 | FUN_00434420 | `memZero` | zeroes `0x88` header in `hapSerialize`, `0x20` desc in `hapEBlobParse` | CONFIRMED |
| 0x4257C0 | FUN_004257c0 | `bmpObjCreate` | allocates 0x48-byte bitmap object, sets w/h, magic at +0x44 | CONFIRMED |
| 0x428210 | FUN_00428210 | `bmpObjSetTransparency` | checks object magic, writes color +0x3C, flag +0x40 | CONFIRMED |
| 0x401000 | FUN_00401000 | `docCreate` | allocates 0x1C0 doc, magic `'ukod'` (0x646F6B75), builds sub-objects | CONFIRMED |
| 0x431270 | FUN_00431270 | `strObjGetData` | `(strObj+0x3C, &len, NULL) -> data ptr`; 4× in `hapWriteBlockA` | CONFIRMED |
| 0x41bba0 | FUN_0041bba0 | `memAlloc` | allocation in `hapSerialize`, freed via `memFree` | CONFIRMED |
| 0x41bca0 | FUN_0041bca0 | `memFree` | `memFree(&ptr)` with ptr nulled after | CONFIRMED |
| 0x41c440 | FUN_0041c440 | `filetimeNow` | 64-bit FILETIME source for tsPrev/tsLast | PROBABLE |
| 0x41a450 | FUN_0041a450 | `fileNameExtract` | `(fileRec*, buf, 0xFF) -> name length` in `hapLoadEntry` | PROBABLE |

### 4.2 Local variable renames (45; all batch-verified 100% success)
| Function | Renames |
|---|---|
| `hapParse` (0x402900) | `local_11b→tsBuf`, `local_1c→descLen`, `local_18→blockAStrPtr`, `local_14→regionPtr` |
| `hapSerialize` (0x402570) | `local_24→sizeA`, `local_14→sizeD`, `local_20→sizeE`, `local_18→sizeF`, `local_1c→sizeG`, `local_28→outBuf` |
| `hapLoadEntry` (0x4036B0) | `local_12c→nodeRef`, `local_128→fileSize`, `local_124→docNode`, `local_120→nameLen`, `local_11f→nameBuf`, `local_c→nodeRefPtr` |
| `hapSaveEntry` (0x4033A0) | `local_114→outSize`, `local_110→outBuf`, `local_10b→tsBuf`, `local_10c→tsLen` |
| `hapWriteBlockA` (0x402370) | `local_28→nameData`, `local_1c→nameLen`, `local_20→str2Data`, `local_18→str2Len`, `local_24→creditsData`, `local_14→creditsLen`, `local_2c→descData`, `local_30→descLen` |
| `hapCSectionRead` (0x4070F0) | `local_18→blobSize`, `local_14→entryCount`, `phVar4→entry` |
| `hapESectionReadV1` (0x405310) | `local_18→rowSize`, `local_14→inkSize`, `phVar5→entry`, `blob→inkBlob` |
| `hapEBlobParse` (0x404700) | `local_438→desc`, `local_434→descH`, `local_42c→rowBytes`, `local_418→palBuf`, `local_41c→palBufPtr`, `local_420→pixelPtr`, `local_428→palCount`, `local_430→bpp`, `local_18→h`, `local_14→w` |

(Compiler temporaries `uVar*`/`puVar*` left as-is except where semantically
stable — per enrichment rules, cosmetic renaming of temporaries is avoided.)

### 4.3 Function comments (25, all read-back verified via `get_function_comment`)
`hapParse`, `hapSerialize`, `hapLoadEntry`, `hapSaveEntry`, `hapWriteBlockA`,
`hapCSectionRead`, `hapESectionReadV1`, `hapEBlobParse`, `hapDSectionReadV1`,
`hapDLoadBuiltInDefault`, `hapERowFetch`, `hapCBlobParse`,
`hapESectionReadV2`, `hapFSectionRead`, `hapGSectionRead`, `inkListAdd`,
`inkListFinalize`, `docCreate`, `memZero`, `bmpObjCreate`,
`bmpObjSetTransparency`, `hapInkRecordParse`, `hapInkSubParse`,
`hapMsiRecordParse`, `pairRecordBuild`.

## 5. Global data definitions applied (7)

| Address | Type | Label | Evidence |
|---|---|---|---|
| 0x45F820 | `uint` (4 B) | `gOpenDocListHead` (new label) | open-document linked list head in `hapLoadEntry`/`hapSaveEntry` (node +0x28=next, +0x90=win, +0x0C=doc) — PROBABLE semantics |
| 0x45F830 | `builtinRezHeader` | `gBuiltinRezHeader` | built-in resource DB header (R0-A) |
| 0x45F848 | `builtinAppearanceRec[9]` | `gBuiltinAppearanceRegistry` | 9-entry registry (R0-A) |
| 0x463C7C | `byte[54]` | `hapDPermuteTable` | D v1 54-slot permutation (re-typed; verified in `hapDSectionReadV1` decompile) |
| 0x464100 | `uint[28]` | `hapV1EWidgetRowMap` | 28 v1-E widget row entries (re-typed; verified indexed in `hapESectionReadV1`) |
| 0x4642E0 | `uint[52]` | `hapV1EVolumeMap` | 26 (row,key) pairs (re-typed; verified walked as `uint*` pairs) |
| 0x466DD4 | `byte[70304]` | `gBuiltinHapEvilChiaroscuroA` | built-in v2 HAP blob A (R0-A.1) |
| 0x4683D4 | `byte[40336]` | `gBuiltinHapEvilChiaroscuroB` | built-in v2 HAP blob B (R0-A.1) |

Note: `create_data_variable` cannot resolve custom DTM types by name
(only built-ins); `set_data_type` resolves them. Used accordingly.

## 6. Structure field renames (1)
`hapDoc.pad_64 → strObjVersion` — the second Block A string object
(doc+0x100). `hapWriteBlockA` writes it as r2, and Block A r2 is the
version string (04-hap-format.md §5; corpus string contents).

## 7. New findings from this session's decompilations

### F1 — E v1 raw bitmap header confirmed by decompilation (CONFIRMED)
`hapEBlobParse` (0x404700) decodes the 8-byte header:
```
+0 u16BE width      +2 u16BE height
+4 u8  flags (bit0 = has transparency)
+5 u8  bpp (1|2|4|8)         <- high byte of the flags word
+6 u8  paletteCount - 1
+7 u8  transparent-palette-index (valid when bit0 set)
+8  palette: paletteCount × u32 LE (0x00BBGGRR)
+8+4n pixels: rowBytes = ceil(width*bpp/8) rounded up to 4
```
(Matches 04-hap-format.md §8.4 exactly — this session's decompilation
confirms the R0-A.1 corpus-derived layout, including bpp at offset 5.)

### F2 — C section reader index math (CONFIRMED, matches 04 §6)
`sectionBuf[entry->tableIndex + 0x10]` ⇒ 512-slot u32-BE offset table at
section offset +0x40, pool at +0x840; 174 document entries; min size 0x840.

### F3 — Document list + save path (CONFIRMED structurally)
- Open documents form a linked list headed by `gOpenDocListHead` (0x45F820).
  Node layout: +0x0C doc ptr, +0x28 next, +0x90 window, +0x19D name byte.
- `hapSaveEntry`: tsLast ← `filetimeNow()` → label refresh →
  `hapSerialize` → `fileWriteWhole(file->hFile, buf, size)`. No file or
  `forceDialog` ⇒ "Save As" dialog (0x4178b0, title
  `"Save Appearance File"`, default ext filter via `PTR_DAT_0045f01c`).

### F4 — Block A second string = version (CONFIRMED positionally)
Writer order: name, str2, credits, desc ↔ on-disk r1..r4 =
name, version, credits, description. `hapDoc` field renamed `strObjVersion`.

### F5 — E v1 reader iterates 34 widget rows (0x22) and 26 volume pairs (0x1A)
Widget rows only fetched when `entry->tableIndex < 0x1C` (28 mapped rows in
this build — consistent with R0-A.1 finding that corpus rows 1–95 map to
nothing except rows 0 and 99–106).

## 8. Semantic coverage matrix (R0-A.2 Phase 1 scope: HAP layer + directly
observed framework)

| Category | Inspected | Already correct | Changed + verified | Deferred | Blocked |
|---|---|---|---|---|---|
| Functions (renamed) | 25 | 16 (R0-A/R0-A.1 names) | 9 | 0 | 0 |
| Parameters (names+types) | 34 fns × ~2.6 avg = ~88 | 0 | 88 (via prototypes) | 0 | 0 |
| Locals (renamed) | 45 meaningful | — | 45 | compiler temporaries (intentional) | 0 |
| Signatures (ret/conv) | 34 | 0 | 34 | 0 | 0 |
| Globals | 8 | 5 (R0-A labels) | 7 re-typed/relabeled | doc node struct (needs more evidence) | 0 |
| Structures (created) | 24 | 0 | 24 created + read back | 0 | 0 |
| Structures (applied) | 13 sites | — | 11 params + 7 data globals + doc field uses | sub-obj apply to `docCreate` stack locals | 0 |
| Unions | 0 candidates | — | 0 | none seen in scope | 0 |
| Enums/equates | 4 switches | 0 | 4 created | section-flag equates (0x7D..0x81) | 0 |
| Typedefs | 1 | 0 | 1 | 0 | 0 |
| Function pointers | 3 (dlg callback `PTR_DAT_0045f01c`, `unloadCb`, `IDropTarget` vtbl) | 0 | 0 | not HAP-scoped; UI-layer milestone | 0 |
| Comments | 25 | 0 | 25 | 0 | 0 |
| References | — | — | verified via re-decompile of `hapESectionReadV1`, `hapDSectionReadV1`, `hapParse`, `hapSerialize`, `hapSaveEntry`, `hapLoadEntry`, `hapWriteBlockA`, `hapCSectionRead`, `hapEBlobParse` | — | — |

Deferred (backlog):
- `docCreate` param `nameLen` semantics (PROBABLE, needs UI-layer context)
- doc node structure (0x45F820 list nodes) — type after UI-layer pass
- UI-layer functions (0x401290, 0x40c5c0, 0x401470, 0x408720, 0x40cc70,
  0x41a270, 0x401550, 0x4038b0, 0x4187b0, 0x417c90, 0x4178b0, 0x41b5f0)
  observed in `hapLoadEntry`/`hapSaveEntry` but out of HAP scope
- `%IKN`/`%MSI` runtime objects (parsed in-place; no heap record modeled yet)

### Phase 4 addendum (render path, same session)

4 functions renamed + commented + read-back verified (`winBlitDib` 0x40CF50,
`dcBlitDib` 0x40E4D0, `widgetBlit` 0x40D160, `labelPaint` 0x409FC0) — see
`11-widget-geometry-and-rendering.md`. Remaining widget painters
(0x410960, 0x43BC00, 0x4514C0, 0x446770) and DIB-builder functions
(0x425C30, 0x426610, 0x42A170, 0x42E370, 0x42DC90, 0x4459E0) deferred to the
UI-layer milestone.

## 9. Limitations and tooling notes

- `set_function_prototype`: N rapid calls in one batch → only the first
  applies reliably (rest report success but don't persist). Interleaving a
  read after each apply fixes it.
- `rename_symbols_batch` schema: `renames: [{identifier, new_name,
  target_type}]` — functions by old auto-name (lowercase hex), data by
  address string, variables by function name + `variable_name`.
- `create_data_variable` cannot resolve custom DTM types; `set_data_type`
  can (supports `array_count`).
- `rename_structure_field` uses `old_field_name` / `new_field_name`.
- `set_local_variable_type` cannot resolve pointer types to custom
  structs (`hapDoc *` not found in its resolver); `set_function_prototype`
  handles pointers fine — preferred path for parameter typing.
- Project was saved after all mutations (`save_project` → status `saved`);
  spot read-backs (types, comments) succeeded post-save.