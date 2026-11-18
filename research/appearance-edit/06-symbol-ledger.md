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


## Naming conventions used

- `pstr*` — Pascal (length-prefixed byte) string helpers.
- `file*` — generic file/stream layer (record-based).
- `fmt*` — numeric formatters writing raw ASCII.
- `hError*` — noreturn framework error constructors (Haxial "h" convention is
  inferred, not evidenced; names describe behavior).
- `g_*` — confirmed global state.
- `searchRecords` / `lookupBuiltInRec` — record-table machinery.