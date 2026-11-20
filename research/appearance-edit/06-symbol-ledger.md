# 06 — Symbol Ledger (AppearanceEdit.exe)

All changes are **program-local** (auto-generated `FUN_*`/`DAT_*` symbols). No GDT
archive-provided definitions exist in this program; none were touched.
Verification method: batch rename reported per-item success; spot-checked by
re-reading function info and re-decompiling callers (see per-entry status).

Session R0-A, 2026-11-17.

## Function renames

| Address | Old name | New name | Confidence | Evidence | Verified |
|---|---|---|---|---|---|
| `0x438390` | `FUN_00438390` | `pstrCopy` | CONFIRMED | decompiled: copies len byte + payload, returns len; callers copy Pascal strings (e.g. `createDocument` @ `0x40310A`, `0x40317A`) | yes (read back) |
| `0x438440` | `FUN_00438440` | `pstrCopyTrunc` | CONFIRMED | same as above with `max` cap | batch OK |
| `0x438500` | `FUN_00438500` | `pstrAppend` | CONFIRMED | appends src payload after dst payload, 0xFF cap | batch OK |
| `0x4385F0` | `FUN_004385F0` | `pstrAppendTrunc` | CONFIRMED | append with src capped at `max` | batch OK |
| `0x4386E0` | `FUN_004386E0` | `pstrAppendInt` | CONFIRMED | calls `fmtInt` into payload, updates len byte | batch OK |
| `0x438720` | `FUN_00438720` | `pstrAppendNum2` | PROBABLE | calls formatter `0x439CC0` (not yet identified) | batch OK |
| `0x438760` | `FUN_00438760` | `pstrAppendNum3` | PROBABLE | calls formatter `0x43A610` (not yet identified) | batch OK |
| `0x4387B0` | `FUN_004387B0` | `pstrAppendByte` | CONFIRMED | appends single byte if len < 0xFF | batch OK |
| `0x4387E0` | `FUN_004387E0` | `pstrEqual` | CONFIRMED | len+payload compare, returns 1/0 | batch OK |
| `0x438840` | `FUN_00438840` | `pstrFindByte` | CONFIRMED | finds byte in payload, returns ptr or NULL | batch OK |
| `0x438880` | `FUN_00438880` | `pstrToRaw` | CONFIRMED | copies payload (no len byte) to raw buffer, capped | batch OK |
| `0x438930` | `FUN_00438930` | `pstrSetFromRaw` | CONFIRMED | builds pstr in place from raw buffer + len (cap 0xFF) | batch OK |
| `0x4389E0` | `FUN_004389E0` | `pstrAllocFromRaw` | CONFIRMED | heap version of above (`FUN_0041BBA0`) | batch OK |
| `0x438AB0` | `FUN_00438AB0` | `pstrDup` | CONFIRMED | heap duplicate of pstr | batch OK |
| `0x4397B0` | `FUN_004397B0` | `fmtInt` | CONFIRMED | integer → ASCII (hex/bin/dec, width, prefix, sign, commas), returns char count | batch OK |
| `0x439760` | `FUN_00439760` | `findForbiddenByte` | CONFIRMED | scans raw bytes vs class table @ `0x467D10`; used for file-name validation | batch OK |
| `0x41A640` | `FUN_0041A640` | `fileReadAt` | CONFIRMED | read at absolute offset, asserts magic `0x1CA6C39A`, returns heap buffer | yes (read back) |
| `0x41A8C0` | `FUN_0041a8c0` | `fileWriteWhole` | CONFIRMED | seek(len)+SetEndOfFile+seek(0)+WriteFile+Flush — whole-file atomic write | batch OK |
| `0x419420` | `FUN_00419420` | `fileOpen` | CONFIRMED | OPEN_EXISTING; builds FileRec (magic, name, len, mode, flags) | batch OK |
| `0x419760` | `FUN_00419760` | `fileOpenMkDir` | PROBABLE | open; on missing path calls `FUN_00419600` (dir create) then continues | batch OK |
| `0x4199E0` | `FUN_004199E0` | `fileOpenExt` | PROBABLE | open variant, custom alloc size, codes 0x30067/0x3006A | batch OK |
| `0x419DC0` | `FUN_00419DC0` | `fileCreate` | CONFIRMED | CREATE_NEW / OPEN_ALWAYS (flag 0x80) / CREATE_ALWAYS (flag 0x40) | batch OK |
| `0x434810` | `FUN_00434810` | `hErrorSimple` | CONFIRMED | stdcall noreturn; builds 0x60-byte error record (code) → `FUN_00414BF0` | batch OK |
| `0x434880` | `FUN_00434880` | `hError` | CONFIRMED | stdcall noreturn; error record (code, module, line) → `FUN_00414BF0` | yes (read back) |
| `0x4401C0` | `FUN_004401C0` | `searchRecords` | CONFIRMED | binary search over fixed-size record array with cmp fn | batch OK |
| `0x445830` | `FUN_00445830` | `lookupBuiltInRec` | CONFIRMED | searches the 9-record built-in registry @ `0x45F848`; returns DB offset | batch OK |
| `0x41BDC0` | `FUN_0041BDC0` | `mainMessageLoop` | CONFIRMED | Peek/Get/DispatchMessageW loop + post-dispatch switch on 0x12/0x312/0x48F/0x496/0x4A0 | yes (read back) |
| `0x41BF30` | `FUN_0041BF30` | `shutdownApp` | CONFIRMED | exit callback + ExitProcess(0) | batch OK |
| `0x41DB10` | `FUN_0041DB10` | `earlyInit` | CONFIRMED | hInstance store, flags, startup FILETIME, OleInitialize | batch OK |
| `0x403D30` | `FUN_00403D30` | `constructApp` | CONFIRMED | window/callback setup + 11 subsystem inits + doc creation | batch OK |
| `0x4030F0` | `FUN_004030F0` | `createDocument` | CONFIRMED | builds document object; title "Untitled ", path "Untitled.hap" @ obj+0x9C | yes (read back) |

## Data renames

| Address | Old name | New name | Confidence | Evidence | Verified |
|---|---|---|---|---|---|
| `0x466BA4` | `DAT_00466ba4` | `g_hInstance` | CONFIRMED | `earlyInit`: `DAT_00466ba4 = param_1` (hInstance from WinMain) | pending re-decompile check |
| `0x466BA8` | `DAT_00466ba8` | `g_cmdLineEmpty` | CONFIRMED | `= (lpCmdLine[0] == 0)` in `earlyInit` | pending |
| `0x466C78` | `DAT_00466c78` | `g_exitCallback` | CONFIRMED | `shutdownApp`: `if (ptr) (*ptr)();` before ExitProcess | pending |
| `0x466944` | `DAT_00466944` | `g_quitFlag` | CONFIRMED | `mainMessageLoop`: loop `do…while (g_quitFlag == 0)` | pending |
| `0x48E0E0` | `DAT_0048e0e0` | `g_msgLoopActive` | CONFIRMED | set 1 entering / 0 leaving `mainMessageLoop`; guarded re-entry assert | pending |

## Protected GDT-origin definitions encountered (R0-A)

None — the program has no GDT archive-provided types in this session. (Re-check
required before any future structure/enum work: verify via `get_data_type`
provenance that target types are program-local.)

## Session R0-A.1 — HAP format layer (2026-11-17)

Evidence document: `04-hap-format.md` §11 (function map). All 45 items applied via
`rename_symbols_batch` (first pass 22/45 — 23 identifiers failed due to
uppercase-hex mismatch; retry with Ghidra's lowercase auto-names 23/23). Spot-check:
`get_function_info` read-back for `hapParse`, `hapESectionReadV1`,
`hapMsiRecordParse`, `hapInkRecordParse`, `hapSerialize`, `hapDLoadBuiltInDefault` —
all correct.

### Function renames

| Address | Old name | New name | Confidence | Evidence | Verified |
|---|---|---|---|---|---|
| `0x402900` | `FUN_00402900` | `hapParse` | CONFIRMED | top-level HAP parser: magic/version check, header fields, section dispatch (0x7C–0x81 flags) | yes (read back) |
| `0x402570` | `FUN_00402570` | `hapSerialize` | CONFIRMED | v2 buffer builder: header + Block A + C/D/E/F/G; asserts D size 0xD8 | yes (read back) |
| `0x4022e0` | `FUN_004022e0` | `hapBlockSizeA` | CONFIRMED | Block A size (8-aligned) | batch OK |
| `0x402370` | `FUN_00402370` | `hapWriteBlockA` | CONFIRMED | Block A writer (timestamps + 4 strings) | batch OK |
| `0x407000` | `FUN_00407000` | `hapCSectionSize` | CONFIRMED | C size = 0x840 + Σ blobs | batch OK |
| `0x407030` | `FUN_00407030` | `hapCSectionWrite` | CONFIRMED | C writer (preamble + 512 table + pool) | batch OK |
| `0x4070f0` | `FUN_004070f0` | `hapCSectionRead` | CONFIRMED | C reader: 174 entries, u16 → 512-slot table | batch OK |
| `0x406e20` | `FUN_00406e20` | `hapCBlobParse` | CONFIRMED | C bitmap: 0x14/0x20 hdr, 1/2/4/8 bpp, secondary rows, palette | batch OK |
| `0x4043c0` | `FUN_004043c0` | `hapDSectionSize` | CONFIRMED | returns constant 0xD8 | batch OK |
| `0x4043d0` | `FUN_004043d0` | `hapDSectionWrite` | CONFIRMED | v2 D writer (54 words) | batch OK |
| `0x404460` | `FUN_00404460` | `hapDSectionReadV1` | CONFIRMED | 204-word v1 D + permutation table `0x463C7C` + built-in fallback | batch OK |
| `0x404410` | `FUN_00404410` | `hapDSectionReadV2` | CONFIRMED | 54-word direct copy (min 0xD8) | batch OK |
| `0x404040` | `FUN_00404040` | `hapDLoadBuiltInDefault` | CONFIRMED | loads D default from embedded blob B (`0x4683D4`) | yes (read back) |
| `0x4050b0` | `FUN_004050b0` | `hapESectionSize` | CONFIRMED | E v2 size = 4 + count*4 + Σ blobs | batch OK |
| `0x405120` | `FUN_00405120` | `hapESectionWriteV2` | CONFIRMED | v2 writer: [count][table][%IKN pool]; asserts end == size (0x1000a) | batch OK |
| `0x405310` | `FUN_00405310` | `hapESectionReadV1` | CONFIRMED | v1 reader: built-in widget map (28) + volume map (26) | yes (read back) |
| `0x405210` | `FUN_00405210` | `hapESectionReadV2` | CONFIRMED | v2 reader: [count][table] → %IKN via `hapInkRecordParse` | batch OK |
| `0x404700` | `FUN_00404700` | `hapEBlobParse` | CONFIRMED | E bitmap: 8B hdr + palette + pixels; alpha-index option | batch OK |
| `0x4048d0` | `FUN_004048d0` | `hapERowFetch` | CONFIRMED | row<192 check; offA/offB at row*0x10; parses both via `hapEBlobParse`; composite | batch OK |
| `0x405d60` | `FUN_00405d60` | `hapFSectionSize` | CONFIRMED | F size = 4 + count*4 + Σ ink sizes | batch OK |
| `0x405e10` | `FUN_00405e10` | `hapFSectionWrite` | CONFIRMED | F writer | batch OK |
| `0x405f50` | `FUN_00405f50` | `hapFSectionRead` | CONFIRMED | F reader: [count][table] → %IKN → `inkListAdd` | batch OK |
| `0x43f430` | `FUN_0043f430` | `hapInkRecordParse` | CONFIRMED | %IKN: magic 0x25494B4E, ver 1, N/M, path, M×12B sub-headers | yes (read back) |
| `0x43f2d0` | `FUN_0043f2d0` | `hapInkSubParse` | CONFIRMED | ink sub-record: W/H/flags/bpp(1,2,4,8,24)/pal/chain offset | batch OK |
| `0x408410` | `FUN_00408410` | `hapGSectionSize` | CONFIRMED | G size = 4 + (maxSlot+1)*4 + Σ | batch OK |
| `0x408480` | `FUN_00408480` | `hapGSectionWrite` | CONFIRMED | G writer | batch OK |
| `0x408570` | `FUN_00408570` | `hapGSectionRead` | CONFIRMED | G reader: 18 slots → %MSI | batch OK |
| `0x4452c0` | `FUN_004452c0` | `hapMsiRecordParse` | CONFIRMED | %MSI: magic 0x254D5349, W/H/Wmin/Hmin, fmt 2/8/32, palette, pixels | yes (read back) |
| `0x4057d0` | `FUN_004057d0` | `inkListAdd` | CONFIRMED | appends (blob,len,key) to doc+0x38 list (F reader, v1 volume loop) | batch OK |
| `0x405880` | `FUN_00405880` | `inkListFinalize` | CONFIRMED | list finalize after F read / v1 volume loop | batch OK |
| `0x4308d0` | `FUN_004308d0` | `displayResourceSet` | CONFIRMED | sets display resource (0x83AF6F92 obj +0x2B) for Block A strings | batch OK |
| `0x434ec0` | `FUN_00434ec0` | `filetimeToString` | CONFIRMED | FILETIME (hi,lo) → formatted string, cap 0xFF, code 0x3020 | batch OK |
| `0x409910` | `FUN_00409910` | `labelSetText` | CONFIRMED | 0x5655D881 label obj; vtable +0x6C set text | batch OK |
| `0x411df0` | `FUN_00411df0` | `optionListGet` | CONFIRMED | 0x51BD8891 obj: selected item value (item+8) | batch OK |
| `0x411d80` | `FUN_00411d80` | `optionListSelect` | CONFIRMED | select item by value (find + select) | batch OK |
| `0x41bbf0` | `FUN_0041bbf0` | `memDup` | PROBABLE | alloc+copy (blob duplication in readers) | batch OK |
| `0x41bb10` | `FUN_0041bb10` | `memCopy` | PROBABLE | copy into preallocated buffer (writer) | batch OK |
| `0x43e390` | `FUN_0043e390` | `pairRecordBuild` | PROBABLE | builds 2-element composite (A,B ptrs + key + len) from `hapERowFetch` | batch OK |
| `0x4036b0` | `FUN_004036b0` | `hapLoadEntry` | CONFIRMED | re-decompiled R0-A.1: whole-file `fileReadAt` → new doc (`FUN_00401000`) → `hapParse(doc, buf, size)`; else walks doc list (head `DAT_0045F820`, link doc+0x28, file ptr doc+0x90) to activate existing | yes (read back + decompile) |
| `0x4033a0` | `FUN_004033a0` | `hapSaveEntry` | CONFIRMED | re-decompiled R0-A.1: sets doc+0x1B0/0x1B4 = current FILETIME, refreshes doc+0x74, `hapSerialize` → `fileWriteWhole(doc+0x90, …)`; dialog path uses string @ `0x45F778` | yes (read back + decompile) |

### Data renames

| Address | Old name | New name | Confidence | Evidence | Verified |
|---|---|---|---|---|---|
| `0x464100` | `DAT_00464100` | `hapV1EWidgetRowMap` | CONFIRMED | 28×u32 LE; read by `hapESectionReadV1` (`PUSH [EAX*4+0x464100]`); shipped values: ids 13,15,…,27 → rows 99–106, rest invalid | batch OK |
| `0x4642E0` | `s__004642d5+0xb` | `hapV1EVolumeMap` | CONFIRMED | 26×(u32,u32); volume loop base in `hapESectionReadV1` | batch OK |
| `0x463C7C` | `DAT_00463c7c` | `hapDPermuteTable` | CONFIRMED | 54 bytes; v1 D word selection in `hapDSectionReadV1` | batch OK |
| `0x4683D4` | `DAT_004683d4` | `gBuiltinHapEvilChiaroscuroB` | CONFIRMED | embedded v2 blob (5 xrefs incl. `hapDLoadBuiltInDefault`); extracted to assets | batch OK |
| `0x00466DD4` | (none) | `gBuiltinHapEvilChiaroscuroA` | PROBABLE | embedded v2 blob, complete C–G; no xrefs found (purpose unconfirmed); extracted to assets | batch OK (label created) |

### Protected GDT-origin definitions encountered (R0-A.1)

None — all 45 targets were auto-generated `FUN_*`/`DAT_*` symbols or new labels.
No structure/enum types were created or modified in this session.


## Session R0-A.2 — Semantic enrichment (2026-11-18)

Evidence document: `09-ghidra-semantic-enrichment.md`. All 24 types read back
via `get_data_type` (size-verified); all 34 prototypes read back via
`get_function_prototype` (zero residual `param_N`/`undefined`); all 25
comments read back via `get_function_comment`; all 54 rename-batch items
reported per-item success; data applications verified by re-decompilation of
`hapESectionReadV1`, `hapDSectionReadV1` (re-typed globals now indexed
properly).

### Function renames

| Address | Old name | New name | Confidence | Evidence | Verified |
|---|---|---|---|---|---|
| `0x434420` | `FUN_00434420` | `memZero` | CONFIRMED | zeroes 0x88 header in `hapSerialize`; 0x20 desc in `hapEBlobParse` | batch OK + re-decompile |
| `0x4257c0` | `FUN_004257c0` | `bmpObjCreate` | CONFIRMED | alloc 0x48, w/h + magic @+0x44 | batch OK + decompile |
| `0x428210` | `FUN_00428210` | `bmpObjSetTransparency` | CONFIRMED | magic check, color @+0x3C, flag @+0x40 | batch OK + decompile |
| `0x401000` | `FUN_00401000` | `docCreate` | CONFIRMED | alloc 0x1C0, magic 'ukod' (0x646F6B75), builds sub-objects | batch OK + decompile |
| `0x431270` | `FUN_00431270` | `strObjGetData` | CONFIRMED | (strObj+0x3C,&len,NULL)→ptr; 4× in `hapWriteBlockA` | batch OK + decompile |
| `0x41bba0` | `FUN_0041bba0` | `memAlloc` | CONFIRMED | alloc in `hapSerialize`, freed by `memFree` | batch OK + decompile |
| `0x41bca0` | `FUN_0041bca0` | `memFree` | CONFIRMED | `memFree(&ptr)`; ptr nulled after | batch OK + decompile |
| `0x41c440` | `FUN_0041c440` | `filetimeNow` | PROBABLE | 64-bit FILETIME source for tsPrev/tsLast (parser + save path) | batch OK + decompile |
| `0x41a450` | `FUN_0041a450` | `fileNameExtract` | PROBABLE | (fileRec*,buf,0xFF)→name len in `hapLoadEntry` | batch OK + decompile |

### Data renames / new labels

| Address | Old name | New name | Confidence | Evidence | Verified |
|---|---|---|---|---|---|
| `0x45F820` | `DAT_0045f820` | `gOpenDocListHead` | PROBABLE | open-doc list head: node +0x0C doc, +0x28 next, +0x90 win, +0x19D name | batch OK + decompile |

### Function renames (render path, R0-A.2 Phase 4)

| Address | Old name | New name | Confidence | Evidence | Verified |
|---|---|---|---|---|---|
| `0x40cf50` | `FUN_0040cf50` | `winBlitDib` | CONFIRMED | only GDI call site: magic 0xFE9778D check, GetDC/SetDIBitsToDevice/ReleaseDC, clip pass | batch OK + re-decompile |
| `0x40e4d0` | `FUN_0040e4d0` | `dcBlitDib` | CONFIRMED | bare HDC 32bpp top-down DIB blit, second SetDIBitsToDevice call site | batch OK + re-decompile |
| `0x40d160` | `FUN_0040d160` | `widgetBlit` | CONFIRMED | `winBlitDib` + paint-context release; 5 painters call it | batch OK |
| `0x409fc0` | `FUN_00409fc0` | `labelPaint` | CONFIRMED | label magic 0x5655D881; per-line temp bitmap + text raster + widgetBlit | batch OK + re-decompile |

(4 function comments added to these in the same batch, read-back verified.)

### Data type applications (see 09 §5)

| Address | Type applied | Verified |
|---|---|---|
| `0x45F830` | `builtinRezHeader` (label `gBuiltinRezHeader`) | set OK |
| `0x45F848` | `builtinAppearanceRec[9]` (label `gBuiltinAppearanceRegistry`) | set OK |
| `0x463C7C` | `byte[54]` | re-decompile of `hapDSectionReadV1` (`hapDPermuteTable[uVar1]`) |
| `0x464100` | `uint[28]` | re-decompile of `hapESectionReadV1` (`hapV1EWidgetRowMap[entry->tableIndex]`) |
| `0x4642E0` | `uint[52]` | re-decompile (walked as `uint*` pairs) |
| `0x466DD4` | `byte[70304]` | set OK |
| `0x4683D4` | `byte[40336]` | set OK |

### Types created (24; full list in 09 §2)

Enums `hapBpp`, `hapIknBpp`, `hapMsiFormat`, `hapSecondaryMode`; typedef
`hapColor`; disk structs `hapHeaderDisk`, `hapBlockAFixedDisk`,
`hapERowV1Disk`, `hapCBlobHdrDisk`, `hapCBlobHdrExtDisk`, `hapEBlobHdrDisk`,
`hapIknHdrDisk`, `hapIknSubHdrDisk`, `hapMsiHdrDisk`; runtime structs
`hapResEntry`, `hapBitmapDesc`, `hapBitmapObj`, `fileRec`,
`builtinRezHeader`, `builtinAppearanceRec`, `hapCSubObj`, `hapDSubObj`,
`hapESubObj`, `hapGSubObj`, `hapDoc`. All program-local under `/haxial/hap`.

### Signatures/prototypes (34)

Full table in 09 §3 — all read-back verified. Includes parameter typing to
`hapDoc*`/`fileRec*`/`hapDSubObj*`/`hapBitmapObj*` and return types.

### Local variable renames (45) and comments (25)

Full lists in 09 §4.2/§4.3 — all batch-verified / read-back verified.

### Structure field rename (1)

`hapDoc.pad_64 → strObjVersion` (second Block A string object; 09 §6).

### Protected GDT-origin definitions encountered (R0-A.2)

None — all created types are program-local under `/haxial/hap`.

## Naming conventions used

- `pstr*` — Pascal (length-prefixed byte) string helpers.
- `file*` — generic file/stream layer (record-based).
- `fmt*` — numeric formatters writing raw ASCII.
- `hError*` — noreturn framework error constructors (Haxial "h" convention is
  inferred, not evidenced; names describe behavior).
- `g_*` — confirmed global state.
- `searchRecords` / `lookupBuiltInRec` — record-table machinery.
---

# R0-A.3 ledger (2026-11-18)

Full per-batch audit: `r0a3-worklist.md`; report: `12-r0a3-semantic-enrichment.md`.

## Function renames (56) — all read-back verified

| Old | New | Addr | Evidence (short) |
|---|---|---|---|
| FUN_00427d80 | bmpBlitToSurface | 0x427D80 | clipped 1–32bpp blit, 0x44e5xx dispatch, magic 0xF4DA120B |
| FUN_004258d0 | bmpGetWH | 0x4258D0 | reads obj+0/+4 after magic check |
| FUN_00425880 | paintSurfaceRelease | 0x425880 | clears magic, frees pixels@+0x18 + obj |
| FUN_004259d0 | bmpSetOffset | 0x4259D0 | writes +0x20/+0x24 |
| FUN_00425c30 | bmpSetFillModeRaw | 0x425C30 | raw write +0x38 |
| FUN_00426610 | bmpBlitPair | 0x426610 | wrapper → FUN_004263b0 |
| FUN_0040ce90 | textWidgetGetRect | 0x40CE90 | magic 0x1688173@+8, rect +0x78..84, dirty +0x88 |
| FUN_0040cbb0 | textWidgetStateGet | 0x40CBB0 | IsWindowVisible/GetFocus → 1/3/4 |
| FUN_0042a170 | widgetBaseFill | 0x42A170 | style-2 pattern/solid fill |
| FUN_0042d190 | inkSlotDraw | 0x42D190 | slot → ink tbl/blobB subtable → 0x43f260 |
| FUN_00425c60 | bmpSetFillMode | 0x425C60 | modeMap → +0x38 |
| FUN_00427200 | bmpTextDraw | 0x427200 | glyph raster 0x44dfe0, font obj, flags |
| FUN_00425a90 | bmpSetClip | 0x425A90 | clamped clip @+0x28..34 |
| FUN_0042c270 | bmpStateIconDraw | 0x42C270 | 3 state bits → gStyleRec slots |
| FUN_0043bc00 | compositeWidgetPaint | 0x43BC00 | 9-slice base + gated sub-features |
| FUN_00410960 | labelWidgetPaint | 0x410960 | text rect → bmp → fill → widgetBlit (win +0x04) |
| FUN_004514c0 | iconGridPaint | 0x4514C0 | same template (win +0x04) |
| FUN_00446770 | listRowPaint | 0x446770 | same template (win +0x00) |
| FUN_004101c0 | labelWidgetFill | 0x4101C0 | font metrics + fontTextDraw + marker |
| FUN_00451260 | iconGridFill | 0x451260 | 15×12 u16 grid, inkSlotFetch + bmpInkBlit |
| FUN_004463e0 | listRowFill | 0x4463E0 | 22px rows, pstr row texts |
| FUN_004459e0 | rectIntersects | 0x4459E0 | AABB strict |
| FUN_0043b5e0 | inkSlotFetch | 0x43B5E0 | u16 slot → %IKN bytes |
| FUN_00426e00 | bmpInkBlit | 0x426E00 | %IKN blit mode 0x30 |
| FUN_0042b6c0 | bmpRowText | 0x42B6C0 | row text + selected flag |
| FUN_00426f50 | bmpTextDraw2 | 0x426F50 | pos-based text draw |
| FUN_0042a8c0 | bmpSetCellState | 0x42A8C0 | 32B cell state |
| FUN_0042a200 | bmpSetMetrics | 0x42A200 | 4-word metrics into surface |
| FUN_00424550 | fontTextDraw | 0x424550 | font + surface metrics + rect |
| FUN_004230c0 | fontMetricsGet | 0x4230C0 | 16B metrics |
| FUN_0041e8a0 | labelMarkerDraw | 0x41E8A0 | secondary marker |
| FUN_00451210 | iconGridCellState | 0x451210 | cell active test |
| FUN_00403510 | docSaveAs | 0x403510 | dialog exec → file swap → hapSaveEntry |
| FUN_004044b0 | hapDImportFromFile | 0x4044B0 | two-phase, 0xD8 D-v2 copy |
| FUN_004179d0 | openDialogExec | 0x4179D0 | IFileDialog exec → fileRec* |
| FUN_00417c50 | fileDialogClose | 0x417C50 | |
| FUN_00417c90 | fileDialogCancel | 0x417C90 | |
| FUN_004178b0 | fileDialogCreateSave | 0x4178B0 | |
| FUN_00417800 | fileDialogCreateOpen | 0x417800 | |
| FUN_0041a270 | fileClose | 0x41A270 | CloseHandle + frees rec |
| FUN_00445080 | msiBlobToBmp | 0x445080 | %MSI → hapBitmapObj |
| FUN_004282a0 | bmpObjSetTransparency32 | 0x4282A0 | 32bpp trans path |
| FUN_00439cc0 | fmtSignedInt | 0x439CC0 | abs + 0x10000 → fmtInt |
| FUN_0041bc50 | memAllocZeroed | 0x41BC50 | GlobalAlloc(0x40) |
| FUN_0041bcd0 | memResize | 0x41BCD0 | GlobalReAlloc(2) |
| FUN_004263b0 | bmpFillRect | 0x4263B0 | alpha-blend rect fill |
| FUN_004457c0 | builtinRecCmp | 0x4457C0 | registry comparator |
| FUN_0041c4c0 | tzOffsetMinutes | 0x41C4C0 | signed tz minutes |
| FUN_00434900 | filetimeBreakdown | 0x434900 | ns → 20B fields |
| FUN_00434ba0 | timeFieldsFormat | 0x434BA0 | fields → string |
| FUN_004431b0 | rectClipIntersect | 0x4431B0 | 9-param multi-rect clip |
| FUN_00441d80 | bmpBlitPalette | 0x441D80 | 1–8bpp path, 0x4415xx |
| FUN_00441320 | paletteExtract | 0x441320 | palette node-list extraction |
| FUN_0041ccc0 | dibInfoDecode | 0x41CCC0 | classic DIB → 32bpp surface |

## Global renames (7)

gStyleRec 0x466954, gStyleDef 0x466950, gInkTbl 0x466964, gInkCount 0x466968,
gIconGrid 0x488AC0, gMainWindow 0x466294, gAllocCount 0x466BAC.

## Types

- `hapDibSrc` (32 B) — w,h,bpp,rowBytes,palCount,flags,pixels,palette — applied to bmpBlitToSurface + msiBlobToBmp.
- `hapTextObj` (140 B) — magic 0x1688173@8, hwnd@0xC, fontIdx@0x70, rect@0x78, dirty@0x88 — applied to textWidgetGetRect.
- `hapBitmapObj` replaced → 18 fields/72 B: clip rect @0x28..34, fillMode @0x38 (corrections to R0-A.2 model).

## Corrections superseding earlier entries

- %MSI field map: hotspot @0x0C/0x0D, bpp @0x0E (supersedes 0x0D/0x0E/… draft in R0-A.2 notes).
- hapBitmapObj @0x28..0x34 = clip rect (not surfW/H); @0x38 = fillMode (not second trans color).
- pairRecordBuild bpp selection is palette-count based (paletteExtract), not a raw format probe.

---

## Session S1 — 2026-11-18 (resource dispatch + C-blob/9-slice + painters)

### Function renames (20)

| Old | New | addr | Evidence |
|---|---|---|---|
| FUN_004293b0 | nineSliceBlitC | 0x4293B0 | 9-slice blitter: corners + edge replication + centre fill; caller chain from state-icon/window paint |
| FUN_004444a0 | dibSamplePixel | 0x4444A0 | (palCount<<24)\|(palIndex<<16)\|0x00FF0000 test = 8bpp indexed sample with alpha-out |
| FUN_004443d0 | dibSamplePixelTrans | 0x4443D0 | trans-colour variant |
| FUN_004265d0 | bmpFillChecked | 0x4265D0 | magic 0xF4DA120B check + fill from surface+0x38 |
| FUN_004291b0 | nineSliceStretchH | 0x4291B0 | per-row per-pixel edge replication (9-slice) |
| FUN_004292b0 | nineSliceStretchV | 0x4292B0 | per-column per-pixel edge replication |
| FUN_00429100 | cBlobHeaderDecode | 0x429100 | fills hapDibSrc from C blob (base+ext) |
| FUN_00426830 | extContentFill | 0x426830 | ext centre fill (colour word@+0x14, insets @+0x1D/0x1F) |
| FUN_00427fd0 | bmpBlitAlpha | 0x427FD0 | alpha/trans-index blit (ext corners) |
| FUN_004093e0 | widgetStateSet | 0x4093E0 | state machine: magic 0x5655D881, u16 @+0x0D, constraint rules, virtual notify @vtable+0x5C |
| FUN_00428c70 | skinInstall | 0x428C70 | global skin-context installer (all g* section pointers) |
| FUN_004287f0 | hapHeaderValidateV2 | 0x4287F0 | %HAP magic, ver==2, scale nibbles, 6 dir slots |
| FUN_00435030 | skinApply | 0x435030 | skinInstall + 0x40F220 + 0x41D390 |
| FUN_00402fa0 | appearanceLoadInstall | 0x402FA0 | hapSerialize → skinApply → holder+0x04 = blob |
| FUN_00403020 | appearanceResetDefault | 0x403020 | skinApply(NULL,0) + memFree |
| FUN_0042a140 | styleColorGet | 0x42A140 | D-colour by role, 54 roles, fallback to built-in |
| FUN_0043bf60 | buttonWidgetPaint | 0x43BF60 | per-element button paint loop (no code callers — template-dispatched) |
| FUN_0043bdd0 | buttonHoverSet | 0x43BDD0 | hilite bit-2 set/clear in per-element state words |
| FUN_0044dfe0 | inkBlitCore | 0x44DFE0 | ink/glyph blit core (bmpInkBlit/bmpTextDraw callers) |
| FUN_0043a610 | fmtByteCount | 0x43A610 | human-readable K/M/G/T/P/E sizes |

### Data renames (14)

gStyleDColors 0x46695C, gStyleDColorCount 0x466960, gInkF 0x46696C,
gInkFSize 0x466970, gInkG 0x466984, gInkGSize 0x466988, gScaleNum 0x466991,
gScaleDen 0x466992, gStyleDColorsFallback 0x466958, gStyleStrA 0x466974,
gStyleStrB 0x46697C, gStyleMetricBases 0x467030, tableButtonMethods
0x45E140, tableLabelMethods 0x45C560.

### Types/fields

- `hapBitmapObj` field `fillMode` → `fillColor` (0x38; fill colour used by bmpFillChecked — supersedes R0-A.3 naming; field semantics from R0-A.3 stand).

### Comments (this session)

nineSliceBlitC, dibSamplePixel, dibSamplePixelTrans, bmpFillChecked,
nineSliceStretchH/V, cBlobHeaderDecode, extContentFill, bmpBlitAlpha,
widgetStateSet, skinInstall, hapHeaderValidateV2, skinApply,
appearanceLoadInstall, appearanceResetDefault, styleColorGet,
buttonWidgetPaint, buttonHoverSet, inkBlitCore, fmtByteCount (19).

### Corrections superseding earlier entries

- **C blob layout** (supersedes 04-hap-format.md §6 and 11 §2): caps @+0x0C..0x0F in the **base** header (always); ext block = 12 B @+0x14; **palette precedes pixels**; size = hdr + rows + sec + (pal+1)*4. Full spec: `14-s1-c-blob-and-9slice.md`.
- **9-slice runtime algorithm** (supersedes 11 §2): edges = per-pixel nearest-neighbour replication of the 1-pixel source edge (NOT texture stretch); centre (plain) = solid fill of sampled centre colour; centre (ext) = ext content fill with insets, centre fill skipped.
- `hapBitmapObj+0x38` = **fill color** (not "fillMode", not trans color).
- 11 more screenshots examined in S1 (17/22 total; doc 15); `mouseicons.png` = `app-builtintheme-blank/mouseicons.png` (a wrong `ui-builtintheme/` path lookup earlier made it appear absent).

### S1 addendum (named tables + IAT correction)

- `gColorRoleNames` @ 0x461EC8 (data, byte + plate comment): 53 D-role names + 6 UTF-8 group headers, 4-byte-aligned pstrs; order = D role index.
- `gEIconNames` @ 0x462E70 (data, plate comment): 155 E icon slot names, 4-byte-aligned pstrs.
- **Correction**: R0-A.3 "provider vtable globals 0x48D30C–0x48D41C" = .idata IAT entries (unbound; PE .idata VA 0x8D000, 0xCAC bytes). Not runtime objects; no further open item.
