# 07 — Open Questions and Blockers (AppearanceEdit.exe)

Sessions R0-A and R0-A.1, 2026-11-17.
R0-A.1 status: items resolved by the corpus + HAP-format work are struck through;
new questions from R0-A.1 are in §4.

## High priority (format-critical)

1. ~~On-disk `.hap` layout is unconfirmed.~~ **RESOLVED** — 111-file corpus +
   2 built-in blobs; full spec in `04-hap-format.md`; inspector validates
   111/111 clean (`tools/research/hap_inspect.py`).
2. ~~Save-buffer builder not located.~~ **RESOLVED** — `hapSaveEntry`
   (`0x4033A0`) → `hapSerialize` (`0x402570`, v2 buffer: header + Block A +
   C/D/E/F/G) → file write; `hapLoadEntry` (`0x4036B0`) → `hapParse`
   (`0x402900`) for the load path. Field emission order documented in
   `04-hap-format.md` §4–§10.
3. **State-record field semantics** (the four u16 pairs after state+type in the
   built-in widget table) — still need the renderer consumer. (Note: R0-A.1
   showed the widget-descriptor region `0x4649xx`–`0x465xxx` is also the
   referent set of the v1 E volume map — possibly the same record type.)
4. **DDE usage** — still unresolved (search `DdeNameService`/
   `DdeCreateStringHandleW` callers).

## Medium priority

5. Byte-swapped fields in the built-in registry (`0x45F844` count, rec+0x0C,
   rec+0x10): still open. **New data point:** the on-disk HAP format uses BE
   for structural fields and LE for pixel/color data — the registry's in-memory
   byte-swaps may mirror the same convention (PROBABLE, unconfirmed).
6. Menu/window instance names → `constructApp` init mapping: still open.
7. `0x5657494E`/"VWIN" / `0x4D454E55`/"MENU" lookup context quirk: still open.
8. Bitmap/color model (DIB16/24/32, `SetDIBitsToDevice` caller): **partially
   resolved** — the file-side bitmap formats are fully specified (C/E bitmaps,
   %IKN 1/2/4/8/24bpp, %MSI 2/8/32bpp); the GDI drawing path is not.
9. 11 subsystem init functions in `constructApp`: still open.
10. Main window WndProc (candidate `FUN_004038C0`): still open.
11. Formatters `FUN_00439CC0`/`FUN_00439D00`/`FUN_0043A610`: still open.
12. `FUN_00414BF0` terminal error handler / `FUN_00434420` record init: still
    open (note: `hapParse` error codes 0x10008/0x10009/0x1000A = bad
    version / bad magic / size-mismatch — now documented).
13. String class table @ `0x467D10` ("forbidden byte" rules): still open.
14. ~~Hash/map structure using `0x466984`/`0x466988` and `0x4683D4`
    (`FUN_00445530`).~~ **PARTIALLY RESOLVED** — `0x4683D4` is the embedded
    HAP v2 default blob B (`gBuiltinHapEvilChiaroscuroB`, 5 xrefs incl.
    `0x4455E3`); the "hash map" interpretation is likely wrong or refers only
    to `0x466984`/`0x466988`. Re-examine `FUN_00445530` as a blob consumer.

## Blocked / needs user input

- ~~No `.hap` samples~~ — **111 samples received** (`refs/appearances/`), all
  v1; 11 `.fnt` fonts (`refs/fonts/`); inventory in `08-corpus-inventory.md`.
- **No v2 `.hap` corpus sample** — the only v2 material is the two built-in
  blobs extracted from the exe. A v2 file saved by AppearanceEdit 1.400 would
  confirm the write path end-to-end.
- **No Haxial runtime/client executable** — the v1 E row-map question (§4.1
  below) needs it.
- Running the original exe is not part of this session (research-only).

## 4. New questions from R0-A.1

1. **v1 E row→widget map in other builds/runtime.** The 1.400 built-in map
   (rows 0/99–106) matches no corpus data (rows 1–95). Do older editors or the
   runtime use a dynamic map? (Blocks faithful v1 icon rendering.)
2. **%MSI Wmin/Hmin** (`+0x0C`/`+0x0D`) — strict-lower-bound constraint only;
   rendering role unknown (scalable glyph slot?).
3. **Option-list content** (header nibbles → doc+0x78+0x38 item list) — which
   editor setting is persisted (value 0x11 default)?
4. **v1 writer missing** — this build only writes v2 E (`[count][table]`);
   how were v1 192-row files produced (older build)?
5. **Embedded blob A** (`0x466DD4`, no xrefs) — purpose (build-time source?
   DDE payload? unused duplicate?).
6. **F/G section consumers** — how the runtime renders ink (%IKN) records and
   %MSI glyphs (volume widget?); the editor-side objects (doc+0x38, doc+0x3C)
   are not yet mapped to widgets.
7. **C preamble** (64 zero bytes) — reserved?
8. **doc+0x1B8** (header 0x08) — always 0 in all 123 files; semantics unknown.
9. **~~Timestamp semantics~~** — RESOLVED: last-save (A+8/A+12) is rewritten on
   every save (`hapSaveEntry` overwrites doc+0x1B0/0x1B4 with the current
   FILETIME and refreshes label doc+0x74); previous-save (A+0/A+4) persists
   from the file. See `04-hap-format.md` §5.

## Suggested next sessions (in priority order)

1. **Runtime cross-check** when available: does the Haxial runtime load v1 E
   rows 1–95, consume F/G, and read the option field? (Resolves 4.1, 4.6.)
2. **Renderer pass**: xrefs into the widget state table `0x4624xx`–`0x465xxx`
   and the `0x4649xx`–`0x465xxx` descriptor blocks — u16 metric meanings,
   `SetDIBitsToDevice` caller, DIB16/24/32 model (old items 3, 8).
3. **DDE subsystem**: service names + payloads (old item 4).
4. **Main window WndProc + menu dispatch** (old item 10) — connect the
   "Open/Save Appearance File" dialogs to `hapLoadEntry`/`hapSaveEntry`.
5. **Capture a v2 save** (run the editor on a VM or hand-assemble from the
   spec) to close the write-path validation loop.
