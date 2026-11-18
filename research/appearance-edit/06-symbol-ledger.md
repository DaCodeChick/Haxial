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

## Protected GDT-origin definitions encountered

None — the program has no GDT archive-provided types in this session. (Re-check
required before any future structure/enum work: verify via `get_data_type`
provenance that target types are program-local.)

## Naming conventions used

- `pstr*` — Pascal (length-prefixed byte) string helpers.
- `file*` — generic file/stream layer (record-based).
- `fmt*` — numeric formatters writing raw ASCII.
- `hError*` — noreturn framework error constructors (Haxial "h" convention is
  inferred, not evidenced; names describe behavior).
- `g_*` — confirmed global state.
- `searchRecords` / `lookupBuiltInRec` — record-table machinery.