# 03 — File I/O Pathways (AppearanceEdit.exe)

Status: **in progress** (session R0-A, 2026-11-17)

## 1. File record object (CONFIRMED)

Allocated by `FUN_0041BC50(size)` (heap). Canonical size `0x1C` (28 bytes):

| Off | Size | Field | Notes |
|---|---|---|---|
| +0x00 | 4 | `HANDLE hFile` | NULL until open |
| +0x04 | 4 | `u32 magic` | **always `0x1CA6C39A`** (verified by every accessor's assert) |
| +0x08 | 4 | `LPCWSTR name` | wide file name |
| +0x0C | 4 | `u32 nameLen` | length of name |
| +0x10 | 4 | `u32 mode` | 1 = file, 2 = directory (observed values) |
| +0x14 | 4 | `u32 flags` | open flags as passed by caller |

(`FUN_004199E0` allocates `param_6` bytes instead of 0x1C — same layout head;
+0x18 onward then available for extra state.)

## 2. Open/create functions (CONFIRMED decompilations)

Common flag decoding (flag = caller's "open mode"):

- access: `GENERIC_READ` (0x80000000) by default; if `flag & 2` →
  `GENERIC_READ|GENERIC_WRITE` (0xC0000000)
- sharing: `FILE_SHARE_READ` if `!(flag & 4)`; `FILE_SHARE_WRITE` if `!(flag & 8)`
  (default sharing = 3 = read|write)
- `if ((flag & 0xF) == 0) flag |= 0x13;` (default bits 0 and 4)
- `flag & 0x10` = on sharing violation (error 5 / 0x20), retry opening
  read-only with sharing 3
- `flag & 0x40` = create-always; `flag & 0x80` = open-always (else create-new)
- file attributes `0x80` = FILE_ATTRIBUTE_NORMAL

| Function | Address | Role | Creation disposition |
|---|---|---|---|
| `FUN_00419420` | `0x419420` | open existing (byte name buffer + len); resolves via `FUN_0041BB10` (byte→wide), `GetFileAttributesW`; directory → mode 2; "virtual"/device path via `FUN_00418A30`/`FUN_00418CF0`; optional out: `*param_4 = FUN_0041A450(...)` byte and `*param_5 = rec+8` (name ptr) | `OPEN_EXISTING` (3) |
| `FUN_00419760` | `0x419760` | open with composed path (`FUN_00419220` path builder + `FUN_00418DE0` assembler); if missing → `FUN_00419600(rec, '\0')` (PROBABLE: create parent dirs) then continue | `OPEN_EXISTING` (3) |
| `FUN_004199E0` | `0x4199E0` | open (variant; error codes 0x30067/0x3006A; checks target-not-directory on failure) | `OPEN_EXISTING` (3) |
| `FUN_00419DC0` | `0x419DC0` | **create/save** path: `FUN_00418A30` result must be 0 (refuses "virtual" paths, error 0x30076) | `CREATE_NEW` (1) default, `OPEN_ALWAYS` (4) if `flag & 0x80`, `CREATE_ALWAYS` (2) if `flag & 0x40` |

Error reporting: `FUN_00434880(code, 0x46 /*'F'*/, line)` with file-layer
framework codes `0x30064` (short write), `0x30066`/`0x30067`/`0x30068` (path build
failures), `0x3006A` (no handle / is directory), `0x30076` (invalid create target);
`FUN_0041D7F0(0x46, n)` and `FUN_0041D760(winErr, 0x46, line)` for Win32 errors.

Callers:
- `FUN_00419420`: `FUN_004473E0`, `FUN_0041C300`
- `FUN_00419760`: `FUN_00417070`, `FUN_00416A00`
- `FUN_004199E0`: `FUN_00419BF0`
- `FUN_00419DC0`: `FUN_00417070`, `FUN_00433AC0`

(`FUN_00417070` uses both open-with-mkdir and create — PROBABLE the
open-or-save dispatcher; decompilation pending.)

## 3. Stream read/write (CONFIRMED decompilations)

| Function | Address | Prototype (inferred) | Behavior |
|---|---|---|---|
| `FUN_0041A640` | `0x41A640` | `HGLOBAL streamReadAt(FileRec *f, u32 offset, u32 maxLen, u32 *ioLen, u32 flags)` | Asserts f, magic, ioLen, handle. Unless `flags & 0x4000` (skip size check): `GetFileSize`; toRead = min(*ioLen, maxLen, fileSize-offset); `SetFilePointer(f, offset)`; alloc toRead via `FUN_0041BBA0`; `ReadFile`; on success `*ioLen = bytesRead`, returns buffer; else `*ioLen = 0`, NULL. |
| `FUN_0041A7D0` | `0x41A7D0` | (6 params) — SetFilePointer + WriteFile; decompilation pending | PROBABLE seek+write region variant |
| `FUN_0041A8C0` | `0x41A8C0` | `void streamWriteWhole(FileRec *f, void **bufRef, u32 len, u32 flags)` | **Whole-file atomic save**: assert magic; unless `flags & 0x4000`: `SetFilePointer(f, len)` → `SetEndOfFile(f)` (truncate/extend to len) → `SetFilePointer(f, 0)` → `WriteFile(buf, len)` → `FlushFileBuffers`. Short write → error 0x30064. Frees `*bufRef` via `FUN_0041BCA0` on all paths. |
| `FUN_0041A9E0` | `0x41A9E0` | (4 params) — SetFilePointer + WriteFile; pending | PROBABLE seek+append or second write variant |

Note: read/write operate on **absolute file offsets** (no persistent stream
position is kept in the record); the "write whole file" primitive suggests `.hap`
files are rewritten as complete buffers rather than patched in place (HYPOTHESIS,
consistent with editor semantics).

## 4. Supporting helpers

| Address | Inferred role |
|---|---|
| `0x41BC50` | heap allocate file record (GlobalAlloc family) |
| `0x41BCA0` | free (`GlobalFree` wrapper; takes pointer-to-pointer) |
| `0x41BBA0` | heap allocate byte buffer (n bytes; used for strings, reads, wide names) |
| `0x41BB10` | byte-string → wide (length-based, MultiByteToWideChar) |
| `0x419220` | wide path composer (type, parts…, buffer, cap 0x800, &len) |
| `0x418DE0` | path assembler (drive/root/name/Pascal suffix; `\0`/`\1` separator variants) |
| `0x418A30` | "is virtual/device path" test (nonzero → special handling) |
| `0x418CF0` | resolve virtual path → device id |
| `0x419600` | create missing parent directory(ies) |
| `0x41A450` | (0xFF, ptr+1, 0xFF) — byte probe (purpose unconfirmed) |
| `0x41D570`/`0x41D760`/`0x41D7F0` | Win32-error → framework error reporting |

## 5. UI dialog strings (CONFIRMED bytes, PROBABLE usage)

`"Open Appearance File: "` @ `0x45F760`, `"Save Appearance File: "` @ `0x45F778`,
plus framework open/save dialog scaffolding in `.rdata` (`"Choose a file to open:"`
@ `0x455099`, `"Save file as:"` @ `0x45511C` area, `"A file named \""` @
`0x45504D`, save-changes prompts @ `0x455130`–`0x455255`). The editor's own file
dialogs are **custom-drawn** (part of the Haxial UI framework), not Win32
GetOpenFileName — consistent with the skin-editor's self-hosting.

## 6. `.hap`-specific code (status)

The generic file/stream layer is mapped; the `.hap`-specific **serialization**
(parse/build of appearance records) has not yet been isolated. Entry points for
the next pass: callers of `FUN_00417070` (open-or-save dispatcher), the
"Open/Save Appearance File" dialog handlers (search callers of the `0x45F760`/
`0x45F778` strings), and the document-object methods around `FUN_00401000`/
`FUN_00401290` (doc create/commit). See 04-hap-format.md.
