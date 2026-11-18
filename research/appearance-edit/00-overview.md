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