# 01 — Executable Architecture (AppearanceEdit.exe)

Status: **in progress** (session R0-A, 2026-11-17)

## 1. Basic PE facts (CONFIRMED)

| Item | Value |
|---|---|
| Format | PE, Windows x86, 32-bit |
| Image base | `0x00400000` |
| Range | `0x00400000`–`0x00494FFF` |
| Entry point | `0x004456C0` (standard MSVC `mainCRTStartup` shape) |
| Compiler | MSVC (x86, 32-bit); CRT present; SEH tables (`.exc`); MSVC-style thunks |
| Functions | 1384 (only 9 named at session start) |
| Version string | `"Haxial ApeeransEdit (AppearanceEdit) 1.400"` — Pascal string, len 90, @ `0x45F791` (note the original typo "Apeerans") |

Segments: `.text` `0x401000`–`0x452FFF`, `.rdata` `0x453000`–`0x45BFFF`, `.exc`,
`.data` `0x45F000`–`0x489FFF`, `.rsrc` `0x48A000`–`0x48BFFF` (only standard version/icon
resources), `.idata`, `.reloc` (10648 base relocations).

## 2. Startup path (CONFIRMED)

```
entry @ 0x4456C0  (MSVC CRT: SEH setup, GetCommandLineA, GetStartupInfoA)
└─ WinMain @ 0x41DB80
   ├─ FUN_0041DB10(hInstance, lpCmdLine)   — early init
   │    ├─ FUN_0041D9A0()
   │    ├─ DAT_00466BA4 = hInstance
   │    ├─ FUN_00428C70(NULL, 0)
   │    ├─ DAT_004669E4 = 1
   │    ├─ DAT_00466BA8 = (lpCmdLine[0] == 0)   — "no command line" flag
   │    ├─ GetSystemTimeAsFileTime → FILETIME_00466C00/00466C08 (startup time, stored twice)
   │    └─ OleInitialize(NULL)
   ├─ FUN_00403DE0()                          — main body
   │    ├─ FUN_00403D30(&DAT_0045F810)        — app construction (see §3)
   │    └─ FUN_0041BDC0()                     — main message loop (see §4)
   └─ FUN_0041BF30()                          — shutdown:
        if (DAT_00466C78) (*DAT_00466C78)();   — registered exit-callback
        ExitProcess(0)
```

Global state so far identified:
- `0x466BA4` — HINSTANCE (hInstance)
- `0x466BA8` — byte flag: command line empty?
- `0x4669E4` — set to 1 in early init
- `0x466C78` — function pointer, exit callback
- `0x466C00/0x466C08` — FILETIME pair (startup time)
- `0x48E0E0` — byte, set 1/0 around the message loop (re-entrancy/running flag)
- `0x466944` — byte, checked each loop iteration: message loop exits when set to 1

## 3. App construction — FUN_00403D30 (CONFIRMED structure, semantics PROBABLE)

```c
FUN_00403D30(appCtx)        // appCtx = &DAT_0045F810 (global app context, ~176B+)
{
  FUN_0040B9C0();
  FUN_0043BBE0(FUN_00403930, appCtx);            // register callback (FUN_00403930)
  FUN_0041C2B0(appCtx, ?, FUN_004038C0, appCtx, 0); // create main window? wndproc FUN_004038C0
  FUN_0043BB70(FUN_00403870, appCtx);            // register callback (FUN_00403870)
  FUN_0041BD80(&DAT_0045F800, NULL);
  FUN_0040D460(&DAT_0045F000, 1);
  FUN_004361F0(); FUN_004229A0(); FUN_00437220(); FUN_004360D0();
  FUN_00437C90(); FUN_00437EE0(); FUN_00437850(); FUN_00436AE0();
  FUN_00435E40(); FUN_0043CEB0(); FUN_0043CD30();
  // ^ 11 subsystem init calls (PROBABLE: menus/windows/toolbars built from embedded DB, §5)

  doc = FUN_00401E30();          // creates main document object
  *appCtx = doc;
  FUN_00402210(doc, 0);
  p = FUN_004030F0(appCtx);      // document/window creation, §6
  *(u8*)(p + 0x19D) = 1;
}
```

### 3.1 FUN_004030F0 — document creation (CONFIRMED decompilation)

Key operations (addresses = disassembly, function `0x4030F0`–`0x4032A2`):

1. `0x403104`: pushes `0x45F744` — Pascal string `09 "Untitled "` (len 9) —
   copies via helper **FUN_00438390(dst, src)** (see 02-strings).
2. `0x40311C`: increments `[appCtx+8]` (document counter) and calls
   `FUN_004397B0(counter, 0x3F, &byte, 0)`.
3. `0x40313F`: `FUN_00438500(buf, &byte)`.
4. `0x40314D`: `doc = FUN_00401000(buf)` — allocate document object from buffer.
5. `0x403162`: `FUN_00401290(doc, 0)`.
6. `0x403169`: pushes `0x45F750` — Pascal string `0C "Untitled.hap"` —
   `FUN_00438390(doc+0x9C, 0x45F750)`: **Pascal string at doc offset 0x9C = file path**.
7. `0x403181`: `FUN_0041C440()` → (EAX, EDX) pair stored at doc+0x1B0/0x1B4 and
   copied to doc+0x1A8/0x1AC (PROBABLE: window position/size pair).
8. `0x4031C7`: `FUN_00434EC0(doc+0x1A8, doc+0x1AC, &byte, 0xFF, 0x3020)` → bool.
9. Two calls to `FUN_00409910(flag, buf, doc+0x70)` / `(flag, buf, doc+0x74)`.
10. `0x40322F`: `FUN_00411CF0(3, [doc+0x78]+0x38)`.
11. `0x40323F`: `FUN_00404040(doc+0x30)`; `0x403250`: `FUN_0040C5C0(1, doc+0xC)`.
12. Returns doc pointer.

## 4. Main message loop — FUN_0041BDC0 (CONFIRMED structure)

```
if (DAT_0048E0E0 == 0) {
  if (DAT_0048E0E0 == 0) FUN_00434880(0x1001D, 0x4D5343, 0xC4); // error/assert ("MSC"?)
  DAT_0048E0E0 = 1;
  if (DAT_00466BA9) FUN_0041BD30();
}
do {
  if (FUN_0044B300()) PeekMessageW(msg, NULL, 0, 0, PM_REMOVE) else GetMessageW(...);
  if (msg present) {
    DispatchMessageW(msg);
    // post-dispatch special handling (decompiler mangles msg.message into UVar4):
    switch (msg.message) {
      case 0x12:  FUN_0043BB10(); break;
      case 0x312: FUN_0040F7C0(msg); break;
      case 0x48F: FUN_0040BC70(); break;
      case 0x496: /* drain extra messages, dispatch, nested 0x4A0 case */ FUN_0041BA70(); break;
      case 0x4A0: FUN_0044B460(); break;
    }
  }
} while (DAT_00466944 == 0);   // loop exits when DAT_00466944 set
DAT_0048E0E0 = 0;
```

Note: `0x312`, `0x48F`, `0x496`, `0x4A0` are custom (WM_USER-range) message IDs —
PROBABLE framework messages (the decompiler's constant folding of `msg.message`
into `UVar4` is an artifact; the switch targets are real).

## 5. Embedded appearance database in .data (CONFIRMED existence, layout PROBABLE)

The `.data` region `0x45F000`–`0x489FFF` contains a large built-in database:

- **Pascal string pool** `0x45F744`–~`0x45F820`: "Untitled ", "Untitled.hap",
  "Open Appearance File: ", "Save Appearance File: ", the 90-byte version block,
  "About ApeeransEdit" (18), "AppearanceEdit" (14).
- **9-entry registry table** @ `0x45F848` (see §5.1).
- **Menu/VWIN widget structure definitions** @ `0x45F900`, `0x45FB18`, `0x4602A8`,
  `0x4605D0`, `0x460BF0`, `0x461038`, `0x4614E8`, `0x461DF0`, `0x4621A0`.
- **Widget state table** (skin property records) spanning ~`0x4624xx`–`0x4653xx+`:
  names such as `"DisabledBUTN"` @ `0x4631D4` (state `"Disabled"` + type `"BUTN"`),
  `"Default"`+`"BUTN"` @ `0x463210`, `"DisabledSEPR"` @ `0x4624CC`,
  `"Default Button Normal"` @ `0x4644BD`, `"Window Close Button Disabled"` @ `0x465359`,
  slider/scrollbar/tick/mutex/popup button, color chooser, focus box, column header
  states, etc. (see 05-ui-and-skin-model).

### 5.1 Registry table (CONFIRMED by code)

Lookup function **FUN_00445830** (`0x445830`–`0x4458F1`):

```
table base   EDI  = 0x45F830
count        [0x45F844] byte-swapped  → 0x00000009 (bytes 00 00 00 09 in memory)
record size  = 0x14 (20 bytes)
table start  = 0x45F830 + 0x18 = 0x45F848
```

Records (name = 8 bytes at record start; meta = 12 bytes):

| # | Address | Name (bytes) | meta (hex) | ret → 0x45F830 + byteswap([rec+0x10]) | out = byteswap([rec+0x0C]) |
|---|---|---|---|---|---|
| 0 | `0x45F848` | `MENUexam` | `00000000 0000 0218 0000 00D0` | `0x45F900` | `0x1800` |
| 1 | `0x45F85C` | `MENUfsit` | `00000000 0000 078C 0000 02E8` | `0x45FB18` | `0x8C07`? (verify) |
| 2 | `0x45F870` | `MENUscal` | `00000000 0000 0328 0000 0A78` | `0x4602A8` | — |
| 3 | `0x45F884` | `VWINdoku` | `00000000 0000 0620 0000 0DA0` | `0x4605D0` | — |
| 4 | `0x45F898` | `VWINefik` | `00000000 0000 0448 0000 13C0` | `0x460BF0` | — |
| 5 | `0x45F8AC` | `VWINemik` | `00000000 0000 04B0 0000 1808` | `0x461038` | — |
| 6 | `0x45F8C0` | `VWINepxm` | `00000000 0000 0908 0000 1CB8` | `0x4614E8` | — |
| 7 | `0x45F8D4` | `VWINesik` | `00000000 0000 03B0 0000 25C0` | `0x461DF0` | — |
| 8 | `0x45F8E8` | `VWINprvw` | `00000000 0000 1328 0000 2970` | `0x4621A0` | — |

(Meta shown as visible bytes; the code byte-swaps the dwords at record+0x0C and
record+0x10 before use.)

- Search: **FUN_004401C0** — binary search over the record array; comparison
  function at `0x4457C2` effectively returns `record_ptr - byteswap([ctx+4])`
  (contains dead code paths that dereference `ctx` and subtract `0x752D` from the
  key — compiler leftovers; key appears unused in this variant).
- On failure: `FUN_00434880(0x10011, 'M', 'R')` (error/assert routine, see below).
- On success: returns `0x45F830 + byteswap([rec+0x10])`; optional out-parameter
  receives `byteswap([rec+0x0C])`.

Callers of FUN_00445830: `FUN_0042A2D0`, `FUN_00408ED0`, `FUN_00412490`,
`FUN_0042B5D0`. Two callers pass the first argument as a **FourCC-as-big-endian
integer**: `0x5657494E` (= "VWIN") and `0x4D454E55` (= "MENU") — see
02-strings-and-fourcc.

### 5.2 Target structure headers (CONFIRMED bytes, field meanings PROBABLE)

All nine targets share the 8-byte header `25 XX XX XX 00 01 00 00` (0x25 = '%'):

```
0x45F900: 25 4D 4E 55 00 01 00 00 ...   "%MNU" class tag (menu)
0x4605D0: 25 56 55 55 00 01 00 00 56 57 49 4E 00 00 00 00 ...
          "%VUU" class tag + "VWIN" FourCC at +0x08
```

VWIN structure sample (`0x4605D0`, VWINdoku):

| Off | Bytes | Note |
|---|---|---|
| +0x00 | `25 56 55 55 00` | class tag "%VUU\0" |
| +0x04 | `01 00 00` | (version? = 1 at byte +4? verify) |
| +0x08 | `56 57 49 4E 00 00 00 00` | "VWIN" FourCC |
| +0x10 | `01 7C 01 90` | 32-bit `0x90017C01` (LE) |
| +0x1F | `2C` | 44 — size-ish |
| +0x27 | `01` | |
| +0x28 | `10 00 01 0F` | `0x0F010010` |
| +0x34 | `01 7C 01 2C` | `0x2C017C01` |
| +0x38 | `4E 20 4E 20 02` | "N N N" + 2 |
| +0x4C | `4B 4E 54 52` | "KNTR" FourCC (counter?) |
| +0x54 | `01 7C 01 90` | `0x90017C01` again |
| +0x58 | `00 00 00 0C` | |
| +0x64 | `00 18 00 00` | 24 (dword @+0x64 = 0x18) |

Menu structure sample (`0x45F900`, MENUexam): +0x1F=1, +0x20=0xFFFFFFFF,
+0x24=7, +0x5C=15. (MENUfsit: +0x24=0x1C, +0x5C=16; MENUscal: +0x1F=2, +0x24=12,
+0x2C=20, +0x5C=7.)

## 6. Error/assert routine FUN_00434880 (observed, not yet decompiled)

Called as `FUN_00434880(code, a, b)` with pairs like `(0x10011, 'M','R')`,
`(0x1001D, 0x4D5343, 0xC4)`, `(0x10011, 0x52, 0x4D)`. The 2/3 trailing bytes look
like a short "tag" (often ASCII-ish). Related to the `"!SError!"` strings in
`.rdata`. Likely the framework's error reporting (PROBABLE; decompile pending).

## 7. Import inventory (CONFIRMED) — subsystem mapping

- **KERNEL32**: file I/O (CreateFileW, ReadFile, WriteFile, SetFilePointer,
  GetFileSize, SetEndOfFile, FlushFileBuffers), directory ops (FindFirst/NextFileW,
  GetFileAttributesW, Create/RemoveDirectoryW, GetLogicalDriveStringsW,
  GetDiskFreeSpaceW, GetDriveTypeW, GetVolumeInformationW), memory
  (GlobalAlloc/ReAlloc/Lock/Unlock/Free/Size), sync (CreateMutexW, critical
  sections, TLS), time, version (GetVersionExA), error (GetLastError),
  ExitProcess.
- **USER32**: windowing (RegisterClassExW, CreateWindowExW, DefWindowProcW,
  Peek/Get/DispatchMessageW, ShowWindow, SetWindowPos, Get/SetWindowPlacement),
  painting (BeginPaint/EndPaint, GetDC/ReleaseDC, InvalidateRect), input
  (ToUnicode, GetKeyboardState, SetCursor, cursors, clipboard,
  GetDoubleClickTime), tray (FlashWindowEx dynamically), **DDE**
  (DdeInitializeW, DdeNameService, DdeCmpStringHandles, DdeCreateStringHandleA/W,
  DdeGetData) — PROBABLE live-communication with a running Haxial client,
  Shell_NotifyIconW (tray icon), DragQueryFileW (drag & drop), MessageBeep,
  PostThreadMessageW, timers.
- **GDI32**: only `SetDIBitsToDevice` is statically imported — other GDI calls are
  probably resolved dynamically (GetProcAddress) or via the framework; the single
  DIB blit import suggests DIB-based bitmap rendering.
- **SHELL32**: ShellExecuteW, Shell_NotifyIconW, DragQueryFileW.
- **OLE32**: OleInitialize, RegisterDragDrop/RevokeDragDrop, CoCreateInstance,
  ReleaseStgMedium (OLE for D&D).
- **Dynamic loading via GetProcAddress** (CONFIRMED strings): USER32
  (GetSystemMetrics, MonitorFromWindow/Rect/Point, EnumDisplayMonitors,
  EnumDisplayDevicesW, GetMonitorInfoA/W, FlashWindowEx), SHELL32
  (EmptyRecycleBinW), PSAPI (CreateToolhelp32Snapshot, Process32FirstW/NextW,
  Thread32First/Next, GetProcessTimes, GetProcessMemoryInfo), ADVAPI32
  (OpenProcessToken, LookupPrivilegeValueA, AdjustTokenPrivileges,
  SeShutdownPrivilege), "System" (WWW_OpenURL).
- **No statically imported Haxial DLLs** — the whole framework is statically
  linked into the exe.

## 8. Known globals (partial; see symbol ledger for renames)

| Address | Observed role | Confidence |
|---|---|---|
| `0x466BA4` | hInstance | CONFIRMED |
| `0x466BA8` | flag: command line empty | CONFIRMED |
| `0x466BA9` | flag checked at loop start (set where?) | PROBABLE |
| `0x4669E4` | init flag (set 1) | CONFIRMED write |
| `0x466C78` | exit callback pointer | CONFIRMED |
| `0x466C00`/`0x466C08` | startup FILETIME | CONFIRMED |
| `0x466944` | "quit" flag — nonzero ends message loop | CONFIRMED use |
| `0x48E0E0` | message-loop running flag | CONFIRMED use |
| `0x45F000` | base of big embedded DB block A (used by FUN_0040D460(&DAT_0045F000, 1)) | PROBABLE |
| `0x45F810` | app context object (176+ bytes; +8 = doc counter; +0x9C area etc.) | PROBABLE |
| `0x45F800` | global object (FUN_0041BD80(&DAT_0045F800, NULL)) | PROBABLE |
| `0x45F830` | embedded appearance DB base (offset origin for registry records) | CONFIRMED |
| `0x45F844` | registry count (byte-swapped 9) | CONFIRMED |
| `0x45F848` | registry table start (9 × 20-byte records) | CONFIRMED |
| `0x466984`/`0x466988` | used by FUN_00445530 (hash table? 4-slot structure) | PROBABLE |
| `0x4683D4` | used by FUN_00445530 second path (+0x54 field) | PROBABLE |

## 9. Call hierarchy (important subsystems)

```
WinMain
├─ early init (0x41DB10)
├─ FUN_00403DE0
│  ├─ FUN_00403D30  app construction
│  │   ├─ FUN_0040B9C0 / FUN_0043BBE0 / FUN_0041C2B0 / FUN_0043BB70  (window + callbacks)
│  │   ├─ 11 subsystem inits (0x4361F0, 0x4229A0, 0x437220, 0x4360D0, 0x437C90,
│  │   │   0x437EE0, 0x437850, 0x436AE0, 0x435E40, 0x43CEB0, 0x43CD30)
│  │   ├─ FUN_00401E30  doc create → FUN_00402210
│  │   └─ FUN_004030F0  document/window object (title "Untitled", path "Untitled.hap")
│  └─ FUN_0041BDC0  message loop
└─ FUN_0041BF30  shutdown (exit callback + ExitProcess)

Framework helpers:
├─ FUN_004401C0  binary search over fixed-size record table
├─ FUN_00445830  embedded-appearance-DB record lookup (9-entry registry)
├─ FUN_00438390  Pascal string copy (dst, src)
├─ FUN_004397B0  (counter, 0x3F, &byte, 0) — name/id generator?
├─ FUN_00438500  (buf, &byte)
├─ FUN_00434880  error/assert (code, tag...)
├─ FUN_00434EC0  (a, b, &byte, 0xFF, 0x3020) — validate/config?
└─ FUN_00445530  hash/map accessor using 0x466984/0x466988 and 0x4683D4
```

## 10. File I/O cluster (initial, CONFIRMED locations)

CreateFileW callers: `FUN_00419420`, `FUN_00419760`, `FUN_004199E0`, `FUN_00419DC0`
(all in `0x4194xx`–`0x419Fxx`; decompilation in progress). These are the likely
open/read/write core of the `.hap` storage layer. See 03-file-io.md.