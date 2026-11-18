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