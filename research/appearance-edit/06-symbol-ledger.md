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

## Session S2 — 2026-11-19/20 (FourCC records, widget identity, class registry)

Evidence base: `17-s2-fourcc-records.md` (Batches A1+A2). All renames read-back
verified (symbol probes + disassembly constant checks).

### Function renames (21 new + 3 corrections = 24 ops)

| Old | New | Address | Evidence |
|---|---|---|---|
| FUN_00409150 | widgetClassLookup | 0x409150 | fast-path subtract-chain (7 class constants) + dynamic table scan vs [0x466B58]/[0x466B5C] |
| FUN_00409100 | widgetClassRegister | 0x409100 | search (0x440B70) + insert (0x440790) into same table; 11 call sites |
| FUN_00408750 | widgetInstantiate | 0x408750 | full decode: class lookup, alloc max(classSize,0x38), magic 0x5655d881, geom slots, classInit/attach, instance-table registration, child recursion |
| FUN_00408B60 | vuuPayloadParse | 0x408B60 | %VUU magic/version/VWIN-first validation; size at payload+0x1C (u32BE) |
| FUN_00408ED0 | windowCreateFromBuiltIn | 0x408ED0 | lookupBuiltInRec(VWIN,…) → vuuPayloadParse; 6 window callers |
| FUN_00412490 | menuCreateFromBuiltIn | 0x412490 | lookupBuiltInRec(MENU,…) → menuPayloadParse |
| FUN_00445900 | lookupBuiltInRecSoft | 0x445900 | %REZ lookup, NULL-tolerant |
| FUN_00429C70 | scaleQuad | 0x429C70 | dst[i] = src[i]*gScaleNum/gScaleDen (4×i16) — the `scal` menu's effect |
| FUN_00412060 | menuPayloadParse | 0x412060 | %MNU header/version/item-count/pstr decode (offsets confirmed; item-field semantics open) |
| FUN_00408670 | widgetAllocInit | 0x408670 | window-object alloc: scaleQuad + FUN_0040BFA0 + magic + WIND class binding |
| FUN_004360D0 | classRegSepr | 0x4360D0 | pushes 0x4677B0 → widgetClassRegister |
| FUN_004361F0 | classRegBpmn | 0x4361F0 | pushes 0x467874 |
| FUN_00435E40 | classRegBox | 0x435E40 | pushes 0x4676EC |
| FUN_00436AE0 | classRegIkbt | 0x436AE0 | pushes 0x467938 |
| FUN_00437850 | classRegTikb | 0x437850 | pushes 0x467AC0 |
| FUN_00437C90 | classRegPrgs | 0x437C90 | pushes 0x467B84 |
| FUN_00437EE0 | classRegSldr | 0x437EE0 | pushes 0x467C48 |
| FUN_0043CEB0 | classRegIkon | 0x43CEB0 | pushes 0x468310 |
| FUN_004229A0 | classRegImgs | 0x4229A0 | pushes 0x466ECC |
| classRegRolr | classRegKolr | 0x437220 | **correction**: pushes 0x4679FC = KOLR (tag RLOK), not "ROLR" |
| classRegRabl | classRegMbar | 0x43CD30 | **correction**: pushes 0x46824C = MBAR (tag RABM), not "RABL" |
| classRegRldr | classRegSldr | 0x437EE0 | **correction**: tag at 0x467C48 is RDLS = SLDR reversed |

### Data renames (28 new + 6 corrections/additions = 34 ops)

| Old | New | Address | Evidence |
|---|---|---|---|
| (unnamed) | rezBuiltinHeader | 0x45F830 | "%REZ" + version 1 + count 9 |
| (unnamed) | rezBuiltinRecords | 0x45F848 | 9 × 20 B records; binary-searched |
| (unnamed) | gClassTblPtr | 0x466B58 | runtime class pointer table |
| (unnamed) | gClassCount | 0x466B5C | table count |
| (unnamed) | dokuInstTable | 0x45F048 | 19 {name4cc,slot,0} entries for doku window |
| (unnamed) | prvwInstTable | 0x45F57C | 29 entries |
| (unnamed) | epxmInstTable | 0x465A9C | 18 entries |
| (unnamed) | emikInstTable | 0x465FB4 | 9 entries |
| (unnamed) | efikInstTable | 0x46440C | 8 entries |
| (unnamed) | esikInstTable | 0x4640C4 | 6 entries |
| (unnamed) | classVuu | 0x4660C4 | tag !UUV (VUU! rev), size 0x38 |
| (unnamed) | classWind | 0x466188 | tag DNIW (WIND rev), size 0x28; direct ref 0x408705 — **new in A2** |
| (unnamed) | classKntr | 0x466690 | tag RTNK, size 0x70 |
| (unnamed) | classLsts | 0x466D44 | tag STSL (stored LE of BE `LSTS`), size 0x4C; single-column list widget class — **new in A2, resolved in A3** |
| (unnamed) | classClst | 0x466E08 | tag TSLC (stored LE of BE `CLST`), size 0x54; multi-column list widget class — **new in A2, resolved in A3** (D-section association DISPROVEN) |
| (unnamed) | classImgs | 0x466ECC | tag SGMI, size 0x64 |
| (unnamed) | classButn | 0x4674A0 | tag NTUB, size 0x40 |
| (unnamed) | classKlbl | 0x467564 | tag LBLK, size 0x48 |
| (unnamed) | classLabl | 0x467628 | tag LBAL, size 0x4C |
| (unnamed) | classBox | 0x4676EC | tag !XOB (BOX! rev), size 0x44 |
| (unnamed) | classSepr | 0x4677B0 | tag RPES, size 0x38 |
| (unnamed) | classBpmn | 0x467874 | tag NMPB, size 0x40 |
| (unnamed) | classIkbt | 0x467938 | tag TBKI, size 0x50 |
| classRolr | classKolr | 0x4679FC | **correction**: tag RLOK = KOLR reversed (color chooser; K=COLR) |
| (unnamed) | classPrgs | 0x467B84 | tag SGRP, size 0x48 |
| classRldr | classSldr | 0x467C48 | **correction**: tag RDLS = SLDR reversed (slider) |
| (unnamed) | classHold | 0x468188 | tag DLOH, size 0x40 |
| classRabl | classMbar | 0x46824C | **correction**: tag RABM = MBAR reversed (menu bar) |
| (unnamed) | classIkon | 0x468310 | tag NOKI, size 0x78 |
| (unnamed) | classTikb | 0x467AC0 | tag BKIT, size 0x44 |
| dokuVwinDesc 0x4605D8, dokuKnt1Desc 0x46062C, dokuMenuDesc 0x460660, dokuSeprDesc 0x460694, dokuInfoDesc 0x4606BC, dokuKlblDesc 0x4606F0 | (created with `widgetDesc` type) | — | first six doku child records |

### Structures created (5 — all size-verified against code+data)

- `rezHeader` (24 B), `rezRec` (20 B) — applied: 0x45F830, 0x45F848[9]
- `widgetDesc` (40 B) — applied ×6 (doku records)
- `widgetBase` (56 B) — created (applied to variables pending C1 audit)
- `widgetClassObj` (144 B) — applied ×21 (all class objects)

### Key conventions established (see 17 §4)

- FourCC code constants = **BE reading of the spelling**; memory-ASCII data is
  bswapped at the comparison sites; class-object tags store the constant as
  u32LE (reversed spelling in memory).
- Widget node = (class FourCC, instance FourCC); instance → widget+0x2C →
  window instance table slot.
- Geometry stored as i16 in u32 slots: raw @+0x0C..+0x1B, scaled @+0x1C..+0x2B
  (scaleQuad × gScaleNum/gScaleDen).

### A3 additions — CLST/LSTS resolution (2026-11-20)

| Old | New | Address | Evidence |
|---|---|---|---|
| FUN_004215A0 | clstWidgetCtor | 0x4215A0 | full decode: alloc ≥0x54, magic, geom+scaleQuad, mode/flags, parent attach (classObj+0x88), listViewCtor→+0x38, listModelCtor→+0x3C, 6 model handlers + 2 view handlers, CLST-only column data (FUN_0044C910→+0x4C, +0x40, +0x50), class ptr → +0x04 |
| FUN_004209E0 | lstsWidgetCtor | 0x4209E0 | same shape, ≥0x4C, no column data, view flags param6 unmodified |
| FUN_00447590 | listViewCtor | 0x447590 | alloc 0xAC/0x104, magic 0xFDB6D01A, geom @+0x04, flags @+0x2C, callback @+0x54, back-ptr @+0x58, metric u16 0x10 @+0x38, const 3 @+0x50, 0xFFFFFF00 @+0x78 |
| FUN_00422EB0 | listModelCtor | 0x422EB0 | alloc 0xC8, magic 0x8521B2D1, 4-word seed @+0x04, source code @+0x18, -1 fields @+0x1C..+0x28/+0xC0, byte 1 @+0x62 |
| FUN_00422F30 | listModelDtor | 0x422F30 | magic check 0x8521B2D1; per-element teardown (count @+0x40, array @+0x3C, element callback @+0x80, arg @+0x84); frees @+0xBC, @+0x30 |
| classStsl | classLsts | 0x466D44 | **correction**: canonical spelling is BE reading of stored tag = `LSTS` (not "LSST") |
| classTslc | classClst | 0x466E08 | **correction**: canonical = `CLST`; D-section association disproven (no FourCC section tags in .hap; D colors via gStyleDColors path) |

Plate comments: classClst @0x466E08, classLsts @0x466D44 (full semantics).

**Findings:** CLST/LSTS = list widget classes (single vs multi-column). Both
use direct (non-%VUU) constructors. View object magic 0xFDB6D01A; model object
magic 0x8521B2D1 (item container with per-element destructors). Shared initFn
0x409BD0 = `RET` no-op. Consumers: doku (docCreate) builds 2×CLST
("Icon"/"Name" columns @0x466054/0x46605C; +1 more) and 2×LSTS (0x130, 0xDF8
bytes); prvw builds 2×CLST ("Column 1/2" @0x45F174/0x45F180; "Name"/"Info"
@0x45F4D4/0x45F4DC); efik/emik/esik each 1×CLST (emik: 0x1D4B, 13 entries
@0x465F1C); epxm 1×LSTS (0xDF8); 0x417CD0←0x417E90, 0x414EA0←0x416C40/0x416530
(other LSTS users). Model source codes observed: 4, 0x102, 0x103, 0x200, 0x204,
0x205, 0x214, 0x215 (meaning open). Column def record: {ptr header pstr} +
{u16 6, w, w, h?, cap?, x?} stride 0x18 (header and def interleaved).

### S2 B2 — paint dispatch closure (2026-11-21)

**Corrections (flag old entries above):** hapTextObj magic is **0xF0168873**
(code check in `textWidgetGetRect` 0x40CE90; stored by `windowCtor`) — the
`0x1688173`/`0x01688173` values recorded in R0-A.3 are wrong. The 0x120-B
window record (pv) is an **extended hapTextObj** (hwnd@+0xC, fontIdx@+0x70,
rect@+0x78, dirty@+0x88). See doc 18.

| Address | Old | New | Kind | Evidence | Confidence |
|---|---|---|---|---|---|
| 0x40A830 | FUN_0040a830 | `windowChildAttach` | function | classWind+0x88; sets windowObj+0x08 = root child; state via textWidgetStateGet(pv) | CONFIRMED |
| 0x413760 | FUN_00413760 | `kntrChildAttach` | function | classKntr+0x88; appends child to array @kntr+0x38 (count @+0x3C) via 0x440790 | CONFIRMED |
| 0x412980 | FUN_00412980 | `kntrPaint` | function | classKntr+0x1C paint slot; child array walk, recurse [childClass+0x1C]; bitmap origin save/translate/restore (0x425A10/0x425A50/0x425990) | CONFIRMED |
| 0x435350 | FUN_00435350 | `butnPaint` | function | classButn+0x1C; bmpStateIconDraw(surface, btn+0x1C, &state@+0x36) | CONFIRMED |
| 0x41F820 | FUN_0041f820 | `listWidgetPaint` | function | shared +0x1C for LSTS/CLST/IMGS → 0x448200(listView@+0x38, surface, rect) | CONFIRMED |
| 0x409BF0 | FUN_00409bf0 | `widgetEventNoop` | function | shared class +0x18 default; empty | CONFIRMED |
| 0x409C70 | FUN_00409c70 | `widgetStateFlagSet` | function | shared class +0x20 default; event+0x18 1/2/3 → mode\|=0x40/0x80/0x100 | CONFIRMED |
| 0x40AF80 / 0x40AFC0 / 0x40B000 | FUN_0040af80 / 0x40afc0 / 0x40b000 | `winSlot6Set` / `winSlot8Set` / `winSlot12Set` | function | magic-check + [pv+0x28/0x30/0x40] = fn | CONFIRMED |
| 0x401300 | FUN_00401300 | `docWindowTeardown` | function | doku slot 12: unlink gOpenDocListHead, fileDialogClose ×2, fileClose | CONFIRMED |
| 0x401350 | FUN_00401350 | `docMenuBuild` | function | doku slot 6: menu bar New/Open/Import Colors/Save/Save As/Preview/About/Exit | CONFIRMED |
| 0x401440 | FUN_00401440 | `docResizeInit` | function | doku slot 8: 0x409A00(win, 400, 800, 0x800000, 0) | CONFIRMED |
| 0x40A170 | FUN_0040a170 | `winSlot1Event567` | function | pv slot 1: events 5/6/7 → [rootChildClass +0x38/+0x3C/+0x40] | CONFIRMED |
| 0x40A2E0 | FUN_0040a2e0 | `winSlot2Event914` | function | pv slot 2: events 9-14 → [rootChildClass +0x20..+0x34]; 11=press→+0x28, 12=release→+0x30 | CONFIRMED |
| 0x40A380 | FUN_0040a380 | `winSlot3Event1014` | function | pv slot 3: events 0x10-0x14 → [rootChildClass +0x48..+0x54] | CONFIRMED |
| 0x40A450 | FUN_0040a450 | `winSlot4PopupShow` | function | pv slot 4: 0x409E50(windowObj, windowObj+0x18) | CONFIRMED |
| 0x40A4A0 | FUN_0040a4a0 | `winSlot5ContextMenu` | function | pv slot 5: menuObjectCtor(0x409F40, windowObj, 0) + drop plumbing | CONFIRMED |
| 0x40A5C0 | FUN_0040a5c0 | `winSlot10StateSync` | function | pv slot 10: 0x40C810(pv) → widgetStateSet(rootChild, 7, …) | CONFIRMED |
| 0x40A690 | FUN_0040a690 | `winSlot9StateSync` | function | pv slot 9: thunk → winSlot10StateSync | CONFIRMED |
| 0x40A6A0 | FUN_0040a6a0 | `windowObjDtor` | function | pv slot 13: release rootChild (0x409060), free +0x10 (0x40FCC0), memFree | CONFIRMED |
| 0x40BD30 | FUN_0040bd30 | `winKeyDispatch` | function | WndProc key → slot 1: *(pv+0x14)(pv+0x48, ev) | CONFIRMED |
| 0x40DD80 | FUN_0040dd80 | `winMouseDown` | function | region classify (0x42DE50): 1 client/2 title/3 border/5,8 edges/6 slot-5 callback | CONFIRMED |
| 0x40E090 | FUN_0040e090 | `winMouseUp` | function | drag cancel (modes 3/5/8/9); release via 0x40BCE0 (slot 2, code 12) | CONFIRMED |
| 0x40D7B0 | FUN_0040d7b0 | `winPointerPressRoute` | function | gPressedWinRecord 0x466288; release-old (12) + press-new (11) via 0x40BCE0 | CONFIRMED |
| 0x40BCE0 | FUN_0040bce0 | `winPointerEventDispatch` | function | pointer events → slot 2: *(pv+0x18)(pv+0x48, ev) | CONFIRMED |
| 0x466288 | DAT_00466288 | `gPressedWinRecord` | data | written by winPointerPressRoute/windowCtor path | CONFIRMED |
| 0x46628C | DAT_0046628c | `gCapturedWinRecord` | data | set on client press, released by winMouseUp | CONFIRMED |
| 0x466290 | DAT_00466290 | `gDragWinRecord` | data | drag owner | CONFIRMED |
| 0x46629C / 0x4662A0 | _DAT_0046629c / _DAT_004662a0 | `gDragStartX` / `gDragStartY` | data | drag start coords | CONFIRMED |
| 0x4662A4 | DAT_004662a4 | `gDragMode` | data | 2 title / 3 border / 5,8,9 edges | CONFIRMED |
| 0x4662A5 | DAT_004662a5 | `gSlot5CallbackActive` | data | re-entrancy guard for *(pv+0x24) callback | CONFIRMED |

Plus: 28 function comments, 15 prototypes (all read-back verified; details in
doc 18 §8). Class-slot table (all 21 classes, +0x0C/+0x10/+0x14/+0x18/+0x1C/
+0x20) documented in doc 18 §2 — incl. TXTS @0x466C80 (no +0x1C paint slot).

### S2 C3 — %VUU window trees (2026-11-20)

| Address | Old | New | Kind | Evidence | Confidence |
|---|---|---|---|---|---|
| 0x40BFA0 | FUN_0040bfa0 | `windowCtor` | function | called by widgetAllocInit (0x408670) for every window with **(windowObj, geom16, options, arg4, namePstr)** (order corrected S2 B2); result (pv record) → obj+0x0C | CONFIRMED (role) |
| 0x40AE70 | FUN_0040ae70 | `windowDefaultPaintInstall` | function | called by widgetAllocInit with (obj+0x0C, 0x46624C) right before magic/class stored; S1 deferred "default-paint" | PROBABLE (name) |
| 0x412780 | FUN_00412780 | `kntrWidgetInit` | function | KNTR classObj+0x0C; decodes: mode\|=0x20, payload 12B → widget+0x5C/+0x60/+0x64 | CONFIRMED |
| 0x412860 | FUN_00412860 | `kntrHasChildren` | function | KNTR classObj+0x14 (childCountFn gate); body = `return widget` | CONFIRMED |
| 0x436430 | FUN_00436430 | `bpmnWidgetInit` | function | BPMN classObj+0x0C; decodes 12B payload → menuCreateFromBuiltIn or menuObjectCtor; menu → widget+0x38 | CONFIRMED |
| 0x40FB90 | FUN_0040fb90 | `menuObjectCtor` | function | allocates 0xA4B menu object; +0x18 = handler fn (0x436160), +0x1C = widget, +0x50 = ref, +0x5C/+0x6C = −1 | CONFIRMED |

All read-back verified (get_function_info). 0x436160/0x4361D0 are function
addresses (prologues verified), passed as handler/callback args — NOT data.

### S2 B2-remainder — %MNU menu subsystem (2026-11-21)

Renames (all read-back verified via get_function_info / decompiler output):

| Address | Old | New | Kind | Evidence | Confidence |
|---|---|---|---|---|---|
| 0x411120 | FUN_00411120 | `menuInsertItem` | function | blob builder: id/value2/flags24/iconIndex/accel/b21/b23 + pstr title (leading len @+0x18); ptrArrayInsert @menu+0xC | CONFIRMED |
| 0x411290 | FUN_00411290 | `menuAddItemPstr` | function | pstr-label wrapper over menuInsertItem (append) | CONFIRMED |
| 0x411410 | FUN_00411410 | `menuInsertSeparatorAt` | function | 0x1AB blob, flags24=0x50000 hard-coded, no title; matches file items flagsHi=0x05 | CONFIRMED |
| 0x411510 | FUN_00411510 | `menuAddSeparator` | function | append wrapper (index 0xFFFFFFFF) | CONFIRMED |
| 0x40F990 | FUN_0040f990 | `menuItemDtor` | function | listModel element dtor → textObjInvalidateRect(surface, rowRect) | CONFIRMED |
| 0x40CDB0 | FUN_0040cdb0 | `textObjInvalidateRect` | function | magic 0xF0168873 (hapTextObj) check; GetClientRect ∩ rect → InvalidateRect | CONFIRMED |
| 0x40F9B0 | FUN_0040f9b0 | `menuItemCellRecord` | function | 0x28B cell: +4 title ptr (blob+0x19), +8 titleLen (blob+0x18), +0xC flags24, +0x14 iconIndex (blob+0x10), +0x26 accel — disassembly-verified | CONFIRMED |
| 0x40FA00 | FUN_0040fa00 | `menuRowCellState` | function | listModel cell-state callback (selection/hilite/first/last flags) | CONFIRMED (role) |
| 0x40FAA0 | FUN_0040faa0 | `menuRowClickDispatch` | function | event 1 → toggle(0x20000) else select; event 7 → select; 0x80000/0x40000 block all | CONFIRMED |
| 0x411880 | FUN_00411880 | `menuRowToggle` | function | blob+0xC ^= 0x20000; modelRefreshRow | CONFIRMED |
| 0x411CF0 | FUN_00411cf0 | `menuRowSelect` | function | selCursor @menu+0x5C; menuSelectHighlight/Clear; style&2 → menuSelCallbackInvoke | CONFIRMED |
| 0x423210 | FUN_00423210 | `modelRowsInsert` | function | listModel row insert (rowSize 0x10, count, NULL rows) | CONFIRMED |
| 0x424020 | FUN_00424020 | `modelRefreshRow` | function | called after flag flip (menuRowToggle) | PROBABLE (name) |
| 0x4117D0 | FUN_004117d0 | `menuSelectHighlight` | function | called after selCursor set (menuRowSelect) | PROBABLE (name) |
| 0x411920 | FUN_00411920 | `menuSelectClear` | function | called when selection cleared | PROBABLE (name) |
| 0x411E80 | FUN_00411e80 | `menuSetSelectionCallback` | function | menu+0x20 = fn, +0x24 = ctx (magic-checked) | CONFIRMED |
| 0x4110E0 | FUN_004110e0 | `menuSelCallbackInvoke` | function | calls menu+0x20 with menu+0x24 | CONFIRMED |
| 0x40FCC0 | FUN_0040fcc0 | `menuDestroy` | function | recursive; surface/model/subObj/name/array frees | CONFIRMED |
| 0x42EF60 | FUN_0042ef60 | `mbarDrawTitles` | function | MBAR horizontal title bar (itemArray @+0x40, cnt @+0x3D, sel @+0x3C) | CONFIRMED (role) |
| 0x42E9E0 | FUN_0042e9e0 | `mbarSubObjCtor` | function | 0xC0B, magic 0x455E0FD3; menu @+0x38 | CONFIRMED |
| 0x43CD50 | FUN_0043cd50 | `mbarWidgetInit` | function | MBAR classObj+0x0C init | CONFIRMED |
| 0x4097F0 | FUN_004097f0 | `widgetMsgBubble` | function | msg → owner's class+0x9C handler | CONFIRMED |
| 0x409660 | FUN_00409660 | `widgetRefresh` | function | (widget, widget+0x1C geom); used on menu open/close/selection | PROBABLE (name) |
| 0x436160 | FUN_00436160 | `bpmnMenuCmdHandler` | function | menu cmdHandler for BPMN menus: close + 0x2C msg copy + flag 0x1000 + widgetMsgBubble | CONFIRMED |
| 0x4361D0 | FUN_004361d0 | `bpmnSelectionNotify` | function | selCallback for BPMN menus: widgetRefresh(widget, geom) | CONFIRMED |
| 0x4367A0 | FUN_004367a0 | `bpmnMenuShow` | function | open popup: btn+0x36\|=1, geom, 0x4098A0 offset, popupMenuShow(menu@btn+0x38) | CONFIRMED |
| 0x436890 | FUN_00436890 | `bpmnMenuClose` | function | btn+0x36&=~1, popupMenuClose | CONFIRMED |
| 0x436670 | FUN_00436670 | `bpmnEventPress` | function | classBpmn+0x20: press/release/click → state 0x40/0x80/0x100; open/close toggle | CONFIRMED |
| 0x410C60 | FUN_00410c60 | `popupMenuShow` | function | (menu, eventInfo, rect, 0) — creates/shows popup window | CONFIRMED (role) |
| 0x410EB0 | FUN_00410eb0 | `popupMenuClose` | function | called by bpmnMenuClose | CONFIRMED (role) |
| 0x4407E0 | FUN_004407e0 | `ptrArrayReserve` | function | capacity reserve (menu+0xC, count≤0x400) | CONFIRMED |
| 0x440790 | FUN_00440790 | `ptrArrayAppend` | function | append (item array, list array) | CONFIRMED |
| 0x440820 | FUN_00440820 | `ptrArrayInsert` | function | insert at index | CONFIRMED |

Data / types (all read-back verified via list_data_variables / get_data_type):

- structs (program-local, category /): `mnuHeader` 40 B (applied ×3: exam_hdr
  0x45F900, fsit_hdr 0x45FB18, scal_hdr 0x4602A8), `mnuItemRec` 56 B (applied ×3
  at each menu's item 0), `menuItemBlob` 24 B fixed + pstr tails (title leading
  len @+0x18; icon pstr after), `menuObj` 164 B (style @+0x50, selCallback
  @+0x20, selCursor @+0x5C initialized from header field5c @+0x20), `mbarSubObj`
  192 B (magic 0x455E0FD3, menu @+0x38, 20-slot item array @+0x40);
  `widgetClassObj` extended 144 → 180 B (msgHandler @+0x9C named; WIND and KNTR
  class objects use slots through +0xB0).
- 15 function comments on the menu subsystem; 9 prototypes (menuPayloadParse,
  menuCreateFromBuiltIn, menuDestroy, menuInsertItem, menuInsertSeparatorAt,
  menuRowClickDispatch, bpmnWidgetInit, menuObjectCtor, modelRowsInsert).

Corrections to earlier notes: menuObj style is @+0x50 (not +0x14 — earlier
decompiler int-index display); selCallback/ctx are @+0x20/+0x24 (not +0x80/
+0x90); header field5c @+0x20 IS the initial selCursor; BPMN payload = {refA
record-name-or-0, refB style, w2}; %MNU payload sizes are 0x218/0x78C/0x328
(the "…B" values in session notes were misreads of the rezRec size+offset
boundary). "exam" %MNU is unreferenced by this build (sample data, PROBABLE).

### S2 C1 — widget base re-audit + list ctors (2026-11-21)

Ghidra changes (all read-back verified):

| Item | Kind | Detail |
|---|---|---|
| `widgetBase` rebuilt | struct | +0x2C instCode (was "classCode4cc" — it is the instance 4cc, source desc+0x0C), +0x30 flagsStored (source desc+0x10), +0x34 state u16 (was "mode"), +0x36 b36 (real flag byte, 0x20 when ctor flags&0x400), +0x37 flagByte, raw/scaled quad naming |
| `listWidgetObj` | struct (new) | 64 B: widgetBase + listView @+0x38 + listModel @+0x3C (CLST/LSTS shared used layout; allocations ≥0x4C/0x54) |
| 0x4093E0 widgetStateSet | prototype+comment | (uint *widget, ushort mask, ushort bits); **state word @+0x34, NOT +0x0D** (S1 correction); bit0 one-way-clear; notify = [class+0x5C](new, old, widget) |
| 0x408750 widgetInstantiate | comment | full field-source table (doc 17 §16.2); arg5/arg6 usage unverified (params left as-is) |
| 0x4215A0 clstWidgetCtor | prototype+comment | (minSize, parent, quadSrc16, flags, flagsStored, listOpts); min 0x54; view @+0x38, model @+0x3C; attach via [parentClass+0x88] |
| 0x4209E0 lstsWidgetCtor | prototype+comment | same shape; min 0x4C; state |= 0x20 |
| 0x43BDD0 buttonHoverSet | reclassification | button-internal element words +0x84/+0x98/+0xAC/+0xC0 (bit 2), NOT the widget state word — S1 "hilite writer" claim corrected |

Parameter-audit status (C1 gate):
- **changed & verified:** widgetStateSet (3 params), clstWidgetCtor (6), lstsWidgetCtor (6).
- **partially audited (arg1–arg3 verified, rest deferred):** widgetInstantiate (arg5/arg6 unverified — no prototype set), windowCtor, vuuPayloadParse (B/C3 verified behavior but prototype params not all re-checked against disassembly).
- **deferred (systematic pass pending):** remaining S1/S2 renamed functions (~150). Trigger: per-batch audit as each function is next touched; batch V final sweep. Reason for deferral: each requires its own disassembly verification; no bulk parameter naming (no evidence reuse across functions).

Corrections recorded (doc 17 §16, doc 13 §3 note): state @+0x34; +0x2C is instance code;
+0x36 is a flag byte; buttonHoverSet not a state writer.

### S2 C1/Batch D front — menuDestroy thread + MBAR mechanism (2026-11-24)

Ghidra changes (all read-back verified):

| Item | Kind | Detail |
|---|---|---|
| 0x42EE00 FUN_0042ee00 → mbarAttachBuiltInMenu | rename+proto+comment | (mbar, insertIdx(-1=append), recordName4cc, titlePstr, arg5); menuCreateFromBuiltIn(0x42F070, mbar, name); title fallback chain → mbarAddMenu; itemArray[slot]=menu; defensive no-op menuDestroy(&0 local); returns slot; 3 callers (prvw ctor 0x401E30) |
| 0x42EC50 FUN_0042ec50 → mbarAddMenu | rename+proto+comment | (mbar, insertIdx, namePstr, arg4); rec=memAlloc(len+0xD) {len@+4, self-ptr@+8, pstr@+0xC}; append to itemArray@+0x40; cnt u8 @+0x3D cap 0x20 (hError 0x1000E/0x4D42/0xA1) |
| 0x42F070 FUN_0042f070 → previewMbarCmdHandler | rename+proto+comment | (mbar, cmdEvent28); cmd struct {cbCtx@+0x24, mbar@+0x28, selIdx@+0x3C, cmd28@+0x2C}; mbarPopupShow(mbar,-1) first; cmdCbFn(mbar+0x30) dispatch |
| 0x42F0E0 FUN_0042f0e0 → mbarPopupShow | rename+comment | (mbar, index(-1=clear), outInfo); slot click: selIdx mgmt, popupMenuClose old, menuDestroy(&mbar+0x38), mbarSlotGeometry, geomCb (+0x20), popupMenuShow (0x410C60) or menuObjectCtor(0x40FB90,0x42F070,1,mbar+0x2C)+emptyMenuCb(+0x28) populate |
| 0x42EEA0 FUN_0042eea0 → mbarRefRegister | rename+proto+comment | (mbar, fn, ctx) → +0x18/+0x1C; hError 0x121/0x4D42/0x10019 on bad magic |
| 0x42EEE0 FUN_0042eee0 → mbarGeomCbRegister | rename+proto+comment | (mbar, fn, ctx) → +0x20/+0x24 |
| 0x42EF20 FUN_0042ef20 → mbarCmdCbRegister | rename+proto+comment | (mbar, fn, ctx) → +0x30/+0x34 |
| 0x42EB30 FUN_0042eb30 → mbarSlotGeometry | rename (provisional) | (mbar, index, &local) — geometry helper; full decode deferred to D3 |
| 0x411C80 FUN_00411c80 → menuBarTitleGet | rename+proto+comment | (menu, outBuf, row); selCursor<cnt && style&2 → menuRowTitleCopy else copy namePstr (+0x54) via 0x438880; hError 0x774/0x504D/0x10019 |
| 0x4115B0 FUN_004115b0 → menuRowTitleCopy | rename+proto+comment | (menu, row, outBuf, arg4); item=row<cnt → copy item title pstr (item+0x18); 1 if found; hError 0x5D5/0x504D/0x10019 |
| 0x40FCC0 menuDestroy | proto+comment | `void menuDestroy(uint *slot)` — SLOT-destructor contract (zero-skip, bad-magic zero, full teardown, slot zeroed last) |
| 0x42E9E0 mbarSubObjCtor | proto+comment | `void *mbarSubObjCtor(uint *mbarWidget)` — alloc 0xC0, magic, 16B widget snapshot +0x04..+0x14, selIdx=0xFF |
| 0x43CD50 mbarWidgetInit | comment | subObj @widget+0x38 + 3 register calls |
| mbarSubObj | struct replaced | 192 B, 19 components: snapshot {classObj,parentWidget,rawX,rawY} @+0x04, refFn/refCtx @+0x18, geomCb @+0x20, emptyMenuCb @+0x28, cmdCb @+0x30, activeMenu @+0x38, selIdx u8 @+0x3C, cnt u8 @+0x3D, itemArray[32] @+0x40 (was itemArray[20]+pad48 — B2 corrected) |
| menuObj | doc correction | namePstr @+0x54 (B2 doc said +0x58; Ghidra struct fixed in prior checkpoint) — consumers: menuDestroy free, menuBarTitleGet source, parse store |

Parameter-audit status (C1 gate, this batch):
- **changed & verified (names+types):** 10 functions above (full param sets
  from disassembly; arg2/insertIdx = uint; row = int where sign semantics
  observed).
- **partially audited:** mbarPopupShow (outInfo struct layout unverified —
  comment only, no prototype), previewMbarCmdHandler (cmdEvent28 internals
  unverified — prototype set for the two verified params).
- **deferred:** mbarSlotGeometry (D3), refFn/emptyMenuCb writers, prvw setup
  helpers.

Corrections recorded (doc 17 §17, doc 07): the "0x40FD20 mid-function call"
was a decode-arithmetic error (target = 0x40FCC0 menuDestroy entry);
"exam" %MNU IS referenced by the prvw preview (mbarAttachBuiltInMenu ×3),
superseding the B2 "unreferenced sample data" note (B2 ledger entry above
remains as a historical record of the scoped claim); mbarSubObj itemArray
cap 0x20 with 32-pointer array.

### S2 Batch D1+D2 — HOLD/SLDR object models + appearance part tables (2026-11-24)

Ghidra changes (all read-back verified; doc 17 §18):

| Item | Kind | Detail |
|---|---|---|
| 0x43CC30 FUN_0043cc30 → holdWidgetInit | rename+proto+comment | (widget, payload, size, b22); state &= ~0x08 (start hidden); size>=8 → +0x38/+0x3C = bswap32(payload[0..4]); HOLD = invisible geometry anchor (prvw sz=0 records) |
| 0x438060 FUN_00438060 → sldrWidgetInit | rename+proto+comment | size>=0xC → +0x38 = bswap32(p0) VALUE, +0x3C = bswap32(p1) MAX; p2&1 → +0x36 |= 0x20 (ticked); prvw payloads (50,100,0\|1) |
| 0x438160 FUN_00438160 → sldrPaint | rename+proto+comment | builds {flag,p1,p2} struct, calls sldrRender(ctx, widget+0x1C, struct) |
| 0x4381A0 FUN_004381a0 → sldrEventPress | rename+proto+comment | event+0x18: 1→state\|=0x40, 2→\|=0x80, 3→\|=0x100; value path needs state&0x10 and state&6; sldrValueFromPointer; +0x40 = computed cursor, +0x38 = new value, +0x36\|=1; widgetRefresh; widgetSendMsg(...,3,...) on change; state\|=0x1000 |
| 0x438110 → sldrStateNotify | rename | class+0x5C; body not decoded |
| 0x438100 → sldrHandler10 | rename | class+0x10; body not decoded |
| 0x438290 → sldrHandler24 | rename | class+0x24; body not decoded |
| 0x42BF20 → sldrValueFromPointer | rename+proto+comment | (quad{corner}, valueStruct, ptPtr, out); orientation w vs h; float value math; end-snap by thumb dim A |
| 0x42BD00 → sldrPartLookup | rename+proto+comment | (quad, valueStruct, &C, &B, &A); partDesc = gApp+bswap32(gApp+0x1F8 horiz / +0x228 vert); C=+0x10/+0x11, B=+0x12/+0x13; A = bswap16(gApp+bswap32(gApp+0x40+idx*4[+2 vert])); idx 0x72/0x76 (horiz), 0x7E/0x82 (vert), +4 ticked; fallback g_appFallback |
| 0x42B820 → sldrRender | rename+proto+comment | (ctx, quad{corner}, valueStruct); n=(flags&0x23)-1, 35-case jumptable 0x4577C4 → (track 0x6E-0x70, thumb 0x72-0x78); track via 0x429860 |
| 0x409760 → widgetSendMsg | rename+proto+comment | (widget, a2, eventId, a4, a5, a6, a7); 44B msg {sender, instCode, a2, eventId, a4, a5, a6, a7}; msgHandler = [parentClass+0x9C](parent, widget, &msg); eventId 3 = slider value-changed |
| 0x409BD0 → widgetInitNoop | rename | shared no-op init (VUU!/LSTS/CLST/SEPR) |
| 0x412780 kntrWidgetInit | proto | (widget, payload, size, b22); state \|= 0x20 (bit5); size>=0xC; arg1/arg3 verified, arg2/arg4 per convention |
| holdWidgetObj | struct (new) | 64 B: widgetBase + ext0 @+0x38 + ext1 @+0x3C |
| sldrWidgetObj | struct (new) | 68 B: widgetBase + value @+0x38 + max @+0x3C + cursor @+0x40 |
| appearanceObj | struct (new) | 608 B minimum: header (TBD E) + partOff[131] @+0x40 (bswap32 offsets → appearancePart); verified entries 110/122/0x6E-0x70/0x72-0x78 |
| appearancePart | struct (new) | 32 B minimum: dimX u16BE @+0, dimY u16BE @+2, margins u8 @+0x10..+0x13 |
| g_appFallback | data (new) | uint @0x466950 (runtime appearance fallback; 0 in .data) |
| g_appCurrent | data (new) | uint @0x466954 (runtime current appearance; 0 in .data) |

Parameter-audit status (per-function gate, this batch):
- **fully enriched (8):** holdWidgetInit, sldrWidgetInit, sldrPartLookup,
  sldrValueFromPointer, sldrRender, widgetSendMsg, kntrWidgetInit
  (arg2/arg4 convention-noted), sldrPaint (arg1/arg3 verified; arg2 never
  read — documented).
- **partially audited (1):** sldrEventPress (args verified; event struct
  internals +0x0C/+0x10/+0x18 consumed, rest pending).
- **deferred (4 + 5 helpers):** sldrStateNotify, sldrHandler10,
  sldrHandler24 (bodies not decoded); 0x429860/0x42C150/0x42D170/0x42BAC1
  (sldrRender vertical)/0x4577C4 table contents (D-late); Batch E:
  appearanceObj header, full part table, appearancePart tail, appearance
  loading.

Corrections/notes (doc 17 §18): class objects are in .data (not .rdata);
class table in §6 had KNTR initFn as "—" — it is 0x412780 (kntrWidgetInit,
named in C3); initFn convention is (widget, payload=desc+0x28,
size=bswap32(desc+0x14), b22) — 4 args, but leaf inits read stack args with
interleaved register pushes (HOLD/SLDR/KLTR each verified individually);
widgetInitNoop = the "fast path" init for VUU!/LSTS/CLST/SEPR.

### S2 Batch D3 — built-in window creation + VWIN root layout (2026-11-24)

Ghidra changes (all read-back verified; doc 17 §19):

| Item | Kind | Detail |
|---|---|---|
| 0x40C9A0 FUN_0040c9a0 → windowSetClientQuad | rename+proto+comment | (subObj=winObj+0x08, clientW, clientH, maxW, maxH) — VWIN wp+0x0C quad via scaleQuad |
| 0x40CC30 FUN_0040cc30 → winSubParamSet | rename+proto+comment | (subObj=winObj+0x0C, bswap32(wp+0x08)); 0 for all 6 built-ins |
| 0x40CAC0 FUN_0040cac0 → winStyleSet0 | rename+proto+comment | style u8==0 dispatch; never taken (all 6 use 2) |
| 0x40CB10 FUN_0040cb10 → winStyleSet1 | rename+proto+comment | style u8==1 dispatch; never taken |
| windowCreateFromBuiltIn 0x408ED0 | proto+comment | (objSize, name4cc, instTable, instCount, instCtx, parent) → lookupBuiltInRec + vuuPayloadParse |
| vuuPayloadParse 0x408B60 | proto+comment | (objSize, payload, payloadSize, instTable, instCount, instCtx, parent, nameOut); full VWIN root + window-own payload decode; childBase = R+0x28+round4(size) |
| widgetAllocInit 0x408670 | proto+comment | (objSize, geom, packedStyle=(f2<<16)\|f, parent, namePstr); window magic + classWIND + subObj |
| lookupBuiltInRec 0x445830 | proto+comment | (classKey, name4cc, sizeOut) — %REZ search; returns payload ptr |
| prvwCtor 0x401E30 | comment | full slot-consumption map (sbhd..sbvt anchors → 0x4015B0 with hsbs/vsbs) |
| docCreate 0x401000 | comment | doku ctor: 0x1C0, dokuInstTable, winSlot12/6/8Set callbacks |
| windowObjBase | struct (new) | 40 B: magic/classObj(WIND)/parent/subObj/pad/instTableEnd/f18/f1C/f20/f24; slots beyond |

Findings (doc 17 §19): candidate part tables 0x45F0C0/0x45F61C = instance-table
tails (NON-ISSUE); %REZ = 3 %MNU + 6 %VWIN (doku/efik/emik/epxm/esik/prvw —
four edit-panel payloads located); VWIN root = 40B descriptor + window-own
payload {f u16, f2 u16, u04 u32, u08 u32, quad u16BE[4] client/max, style u8,
nameLen u8, name pstr}; titles: prvw "Preview GUI Items", efik "Edit File
Icon", esik "Edit Icon"; windows are widget-magic objects of class WIND
(0x466188); correction: "windowOwn block 0x41B42C" was a decode error — real
call at 0x401E3D (prvwCtor).

### S2 Batch D-late — scrollbar binding + partDraw + C-blob convergence (2026-11-24)

Ghidra changes (all read-back verified; doc 17 §20):

| Item | Kind | Detail |
|---|---|---|
| 0x4015B0 FUN_004015b0 → sbarBindCreate | rename+proto+comment | (scrollbarWidget, anchorGeom=anchor+0x0C, flags) → 76B sbarBindObj; lazy shared 196B sbarController @0x48E000 (tag 0x4D795342, 6 fns); default words 250/500/50/100 @+0x38..+0x3E; obj+0x04 = controller |
| 0x429860 FUN_00429860 → partDraw | rename+proto+comment | (ctx, dstQuad, partDesc): cBlobHeaderDecode → [ext? extContentFill] → [tiled? bmpBlitAlpha×2+partBlitRepeat : standard 3-band bmpBlitToSurface/nineSliceStretchH/bmpBlitToSurface using capL/capR] |
| 0x429220 FUN_00429220 → partBlitRepeat | rename+proto+comment | (ctx, dstX, dstY, dstW, surface, srcOffX, 0, surfaceField, transIdx) — tiled path; body not decoded |
| cBlobHeaderDecode 0x429100 | proto+comment (S1 name kept) | (cBlob, surfaceOut ~116B) — also called with appearance parts |
| extContentFill 0x426830 | proto+comment (S1 name kept) | (ctx, dstRect, colorByte, colorRest, field4) — 5-arg partDraw call site |
| bmpBlitToSurface 0x427D80 | proto+comment (S1 name kept) | (ctx, dstRect, surface, size, cBlob, surfaceField, 0) |
| bmpBlitAlpha 0x427FD0 | proto+comment (S1 name kept) | (ctx, dstRect, surface, size, cBlob, surfaceField, mode=(transIdx<<24)\|1) |
| nineSliceStretchH 0x4291B0 | proto+comment (S1 name kept) | (ctx, dstX, dstY, dstW, surface, srcOffX, a7=0, surfaceField) |
| sbarBindObj | struct (new) | 76 B |
| sbarController | struct (new) | 196 B |
| cBlobPartDesc | struct (new) | 32 B = C-blob 20B base header + 12B ext (doc 14 layout) |
| appearancePart | struct (replaced) | re-pointed to the cBlobPartDesc layout |
| g_sbarController | data (new) | sbarController @0x48E000 (.bss) |
| g_sbarControllerInit | data (new) | char @0x48E0C4 |

**Convergence (doc 17 §20.3): appearance part descriptors ARE C-blobs.**
partOff[131] entries → gApp + bswap32(off) → C-blob (width/height u16BE
@+0, caps @+0xC..+0xF, field2 @+0x10 = slider margins, extColour u16BE
@+0x14, contentInsetTop/Bottom @+0x1D/+0x1F). The "appearance part tables"
discovered in D1+D2 and S1's C-blob/9-slice pipeline are the same objects.
The standard partDraw path is a horizontal 3-slice (capL/center/capR);
slider track/thumb parts are 1-D parts drawn this way.

## S2 D-late scrollbar closure (2026-11-24; doc 17 §21, doc 19 §7)

**Model correction:** the D-late "shared 196-B stateful sbarController"
entry above is SUPERSEDED — 0x48E000 is a shared **class object**
(method table), stateless; built once by `memCopy(0x48E000, 0x4660C4
VUU! skeleton, 0xC4)` + overrides (evidence: sbarBindCreate bytes).

| Item | Kind | Detail |
|---|---|---|
| 0x48E000 g_sbarController → **g_sbarClass** | data rename | sbarClassObj applied at 0x48E000 |
| 0x48E0C4 g_sbarControllerInit → **g_sbarClassInit** | data rename | class-init flag byte |
| 0x408F10 → **subWidgetCtor** | rename+proto+comment | (size, srcQuad, parentWidget, flags); raw quad := *srcQuad, scaled := scaleQuad; state/flagByte from flags; attach via [parentClass+0x88]; classObj := 0x4660C4 (overwritten by caller) |
| 0x401700 → **sbarValueOffset** | rename+proto+comment | value = clamp(value+Δ, 0, max); refresh on change |
| 0x401750 → **sbarTimerTick** | rename+proto+comment | auto-repeat cb: state1/2 → first-tick rearm 35ms + Δ±30/±100 (pageMode +0x49) |
| 0x41DBD0 → **sbarRectsCompute** | rename+proto+comment | part rects 0x74B + orientFlag; thumb formulas (doc 19 §7); appearance +0x288/+0x28C/+0x298/+0x2D4/+0x2D8/+0x2E4; styleCtx +0x98/+0x9A/+0x9C |
| 0x41E6B0 → **sbarHitTest** | rename+proto+comment | states 0..7 (whole/4 cap-strip rects/3 track-thumb rects) |
| 0x41E510 → **sbarPressResolve** | rename+proto+comment | (quad, params, ptr, outValue) → grabOffset |
| 0x41E5F0 → **sbarValueFromPointer** | rename+proto+comment | value = round(clamp(ptr−grab) span-math × max) |
| 0x401680 → **sbarMethCancelTimer** | rename+proto+comment | class slot +0x10: timerDestroy(&obj+0x44) |
| 0x4016A0 → **sbarMethPaint** | rename+proto+comment | class slot +0x1C: labelMarkerDraw(ctx, quad, &params) |
| 0x4017E0 → **sbarMethPress** | rename+proto+comment | class slot +0x20: hit-test state machine (table 0x4530E8) |
| 0x401970 → **sbarMethRelease** | rename+proto+comment | class slot +0x24: timerDestroy + stateIdx=0 |
| 0x4019A0 → **sbarMethMove** | rename+proto+comment | class slots +0x28/+0x2C: drag move (state 7) |
| 0x41C560 → **timerCreate** | rename+proto+comment | (cb, ctx, ms, oneShot) → 24B obj; SetTimer(NULL,0,ms,0x41C4F0); list 0x466C10 |
| 0x41C600 → **timerDestroy** | rename+proto+comment | (&slot): validate, KillTimer, listRemove, memFree(&slot) |
| 0x41C670 → **timerReset** | rename+proto+comment | (obj, ms, oneShot): KillTimer + SetTimer + re-list |
| 0x41C4F0 → **timerMsgProc** | rename+proto+comment | winproc (RET 0x10); oneShot → timerOneShotStop then callback |
| 0x41C710 → **timerOneShotStop** | rename+proto+comment | KillTimer + listRemove (no free) |
| 0x44C870 → **dtoiRound** | rename+proto+comment | double→int32 FISTP-based; NaN→−1 |
| 0x414D80 → **listAppend** | rename+proto | generic stride list {first,last,stride,count} |
| 0x414E00 → **listRemove** | rename+proto | same; 1/0 return |
| sbarBindObj | struct (replaced) | 76 B full field map (+0x38 value, +0x3A max, +0x3C thumbNum, +0x3E thumbDen, +0x40 stateIdx, +0x42 grabOffset, +0x44 timerObj, +0x48 firstTick, +0x49 pageMode) |
| sbarController → **sbarClassObj** | struct (replaced+renamed) | class object layout (tag/size/initFn/6 overrides/defaults/stateNotify/attach+0x88) |
| sbarGeomParams | struct (new) | 16 B {flag@0, stateIdx@4, value@8, max@0xC, thumbNum@0x10, thumbDen@0x14} |
| sbarRects | struct (new) | 0x74 B: whole + part1..part6 (16B corner rects) + orientFlag@0x70 |
| styleCtx | struct (new, DTM only) | 157 B @0x46691C layout; not applied over named g_* globals |
| appearanceObj | struct (replaced) | 608 B → **744 B (0x2E8)**: +0x288 hSbarPartLarge, +0x28C hSbarPartSmall, +0x298 hSbarThumbPart, +0x2D4 vSbarPartLarge, +0x2D8 vSbarPartSmall, +0x2E4 vSbarThumbPart (all bswap32) |

## S2 D-late — SLDR closure, state bits 0x02/0x04, menu-bar slots (2026-11-24; doc 17 §22, doc 19 §5/§8)

Evidence: disassembly (sldrRender 0x42B820, sldrValueFromPointer 0x42BF20,
sldrPointerToValue 0x42C150, sldrEventPress/Move/Release 0x4381A0/0x4382F0/
0x438290, sldrWidgetInit 0x438060, widgetHoverState 0x413450,
mbarSlotGeometry 0x42EB30, partBlitAt 0x429BE0 — 14 call sites); raw prvw
SLDR payload bytes (10 × 12B, value=50 max=100); blob B C-section part
dims (slots 110–130); screenshot pixel analysis (ui-builtintheme/
sliders.png). All read-back verified; project saved.

| Item | Kind | Detail |
|---|---|---|
| 0x42C150 FUN_0042c150 → **sldrPointerToValue** | rename+proto+comment | (quad, valueStruct, ptPtr, grabOffset) → new value; clamp [0,max]; H: [x1+outC, x2−outB−outA], V mirrored from top w/ negated half-band; round((p−grab−lo)×max/(hi−lo)) |
| 0x4382F0 FUN_004382f0 → **sldrEventMove** | rename+proto+comment | classSldr+0x2C; armed-only; drag value math w/ grab=+0x40; state\|=0x1000 + msg 3 on change |
| 0x438290 sldrHandler24 → **sldrEventRelease** | rename+proto+comment | classSldr+0x24; clears 0x40/0x80/0x100 by kind; disarms flagByte bit 0 |
| 0x429BE0 FUN_00429be0 → **partBlitAt** | rename+proto+comment | generic blit-part-at-point (14 call sites); cBlobHeaderDecode + bmpBlitAlpha (part flag bit 0) / bmpBlitToSurface |
| 0x413450 FUN_00413450 → **widgetHoverState** | rename+proto+comment | (widget, newState, oldState); child array +0x38/+0x3C, current child +0x44; writes 0x2 / 0x6 via widgetStateSet(mask=0x7) — the 0x02/0x04 writer |
| 0x42D170 FUN_0042d170 → **stubCursorSet** | rename+comment | RET-only stub (cursor feedback placeholder) |
| 0x42D180 FUN_0042d180 → **stubCursorRestore** | rename+comment | RET-only stub |
| sldrValueFromPointer | proto+comment | 4 params (quad, valueStruct, ptPtr, out); snap-band logic; returns grab offset; max/value "computed" term (anomaly) |
| sldrEventPress / sldrRender / sldrWidgetInit | comment | state-bit flow + gate (0x10 & 0x06); 35-case dispatch tables 0x4577C4/0x457738; payload layout |
| mbarSlotGeometry | proto+comment | (mbarSub, slotIdx, outRect); 8 sub-items per slot @+0x40, width byte +0x4; 5px pad; count +0x3D |
| no new structs | — | sldrWidgetObj (68B) and mbarSubObj (192B) already exist; valueStruct = ad-hoc {flagByte, value, max} documented in comments |

Open: the render/snap term `FIST(trackLen × max / value)` is code-CONFIRMED
(byte-verified 0x42BA4E–0x42BA77 + vertical branch; correction idiom
proven dead) but runtime-unverified — screenshot mid-track thumb implies
value/max. Held open (no implementation-ready claim for SLDR geometry).

## S2 Batch E — appearance object, lifecycle, resource sections (2026-11-24; doc 20)

Evidence: skinInstall 0x428C70 disassembly (all styleCtx writes),
styleColorGet 0x42A140, inkNameLookup 0x42D3F0 + searchRecords 0x4401C0 +
pstrRFindChar 0x43FD00, widgetBaseFill 0x42A170 + bmpFillRect 0x4263B0,
hapLoadEntry 0x4036B0, appearanceLoadInstall 0x402FA0,
appearanceResetDefault 0x403020, earlyInit 0x41DB10; raw: built-in blob
header/sections, 111-file corpus D/C scans (all 8160 D colors byte0=0x00
except 1; 39/39 C directories valid). All read-back verified; project
saved.

| Item | Kind | Detail |
|---|---|---|
| 0x466964 gInkTbl → **gIkonSec** | data rename | E section (icon records) pointer |
| 0x466968 gInkCount → **gIkonSecSize** | data rename | E section size |
| 0x46696C gInkF → **gInkFSec** | data rename | F section (ink records) pointer |
| 0x466974 gStyleStrA → **gInkF** | data rename (S1 mis-naming corrected) | inkNameLookup("data") record ptr @styleCtx+0x58 |
| 0x46697C gStyleStrB → **gInkF2** | data rename (S1 mis-naming corrected) | inkNameLookup("folder/standard") record ptr @+0x60 |
| 0x466990 → **gOnceFlag** | new data label | byte; 0 when gOncePtr first set |
| 0x4669E4 → **gSkinInstalled** | new data label | u32; set by earlyInit after skinInstall(0,0) |
| 0x42D3F0 → **inkNameLookup** | rename+proto+comment | (out, namePstr); F-section binary search, '/'-prefix fallback, built-in F fallback |
| 0x426660 → **bmpFillRectFromRect** | rename+proto+comment | 3-arg thunk over bmpFillRect(surf, r.x, r.y, r.w, r.h, color) |
| 0x43FD00 → **pstrRFindChar** | rename+proto+comment | last-occurrence char find (right-to-left) |
| styleColorGet / skinInstall / skinApply / appearanceLoadInstall / appearanceResetDefault / hapLoadEntry / earlyInit / widgetBaseFill / bmpFillRect / searchRecords | proto+comment | lifecycle + role matrix + blend-byte semantics |
| appearanceObj | struct replaced | 744 B → **2112 B (0x840)**: reserved[16] + partOff[512]; hSbar*/vSbar* "fields" were partOff[146]/[147]/[150]/[165]/[166]/[169] (correction); pool tail documented |
| styleCtx | struct replaced | 157 B → **204 B (0xCC)** full layout (D/E/F/G pointers, ink ptrs, once, scale, metrics[35], gSkinInstalled@+0xC8); DTM only |
| hapNamedPool | struct (new, /haxial) | 8 B {count, offsets[1]} — E/F/G section pattern |
| cPartId enum | **blocked** | MCP create_structure is struct-only; part ids recorded in doc 20 §7 + this ledger (13, 94, 106, 110–132 SLDR, 146/147/150/165/166/169 sbar) |

Key findings (doc 20): appearance object = C section (no separate parse);
131-vs-512 RESOLVED (512 = fixed capacity; 131 = Batch-D truncation
assumption); section map C/D/E/F/G; D = 54 (v2) / 204 (v1) color roles,
[00][RR][GG][BB], no bswap, consumer matrix; F/G/E = named record pools
{count, offsets, records}; lifecycle install/apply/reset/load (owner+4
owns the installed image); D-late correction: sbar "metrics" +0x98/+0x9A/
+0x9C = scaled-metrics matrix cells [16]/[17]/[18].

## S2 Batch E2-partial — post-install + section records (2026-11-24; doc 20 §11)

| Item | Kind | Detail |
|---|---|---|
| 0x40F220 | rename+comment | **winMetricsResync** — per-window SetWindowPos(0x14)/InvalidateRect after install (IAT: SetWindowPos/IsWindowVisible/InvalidateRect; metrics via 0x42E7D0, rect via 0x40C810) |
| 0x41D390 | rename+comment | **cursorCacheReset** — GetCursor/DestroyCursor over 20-slot table @0x466C28 + list @0x466C20 |

Findings (no further Ghidra mutation this sub-batch; all raw/data-level):
E section = %IKN icon records (35 icons, dir[0] reserved empty; header map
doc 20 §11.1). F section = named %IKN ink records (24 built-in names:
data, font/, text/, audio/, image/, video/, folder/, volume/{cd,hd,dvd,fdd,
net,ram,cart}, volume/, archive/, driver/, folder/{audio,images,dropbox,
uploads}, data/truncated, alias/unattached, executable/{plugin,program};
dir[0] dummy = count; 16-byte hash name match; "folder/standard" absent
from built-in → gInkF2 = NULL). G section = 19 %MSI cursors (S1-decoded;
re-verified).
