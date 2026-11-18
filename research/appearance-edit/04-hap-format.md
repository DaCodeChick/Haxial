# 04 — `.hap` Format Discovery (AppearanceEdit.exe)

Status: **initial — static executable findings only. No `.hap` sample files are
available in this workspace; nothing here is sample-verified.**

## 1. What is a `.hap` file (current understanding)

HAXial Appearance (`.hap`) files store a **skin/appearance database**: for each
widget type × appearance state, the resources and metrics the renderer needs
(bitmaps, colors, geometry, fonts). The editor (AppearanceEdit) loads, edits,
and saves these databases; a default database is **built into the executable**
(§3) — so the built-in bytes are the best available ground truth for the format.

## 2. Confirmed static facts about persistence

| Fact | Evidence |
|---|---|
| Default new-document file name is `Untitled.hap` | Pascal string `0C "Untitled.hap"` @ `0x45F750`, copied into document object at offset **0x9C** by `createDocument` (`0x403169`) |
| Dialog prompts: `Open Appearance File: ` / `Save Appearance File: ` | `0x45F760`, `0x45F778` |
| Files are rewritten as complete buffers | `fileWriteWhole` (`0x41A8C0`): seek(newSize) → SetEndOfFile → seek(0) → WriteFile(entire buffer) → Flush |
| Reads are absolute-offset based | `fileReadAt` (`0x41A640`): SetFilePointer(offset) + ReadFile into fresh buffer |
| No streaming/persistent cursor kept in file records | FileRec layout (03-file-io §1) holds no position field |
| Files use wide names internally, byte names at API edges | `fileOpen` converts via `FUN_0041BB10` (MultiByteToWideChar) |
| File record magic `0x1CA6C39A` | asserted in every file-layer accessor — this is a **runtime object tag, NOT a file header** (do not confuse with on-disk magic) |

## 3. Built-in default appearance database (CONFIRMED layout fragments)

Base `0x45F830` in `.data`. Structure (from `lookupBuiltInRec` + hexdumps):

```
0x45F828: u32 0x28 (=40)                 — leading value (purpose unconfirmed;
                                           possibly size/count of surrounding block)
0x45F82C: 16 zero bytes
0x45F830: record "%REZ\0" + 12 meta bytes  — 24-byte leading record(s)? (unconfirmed)
0x45F844: u32 byte-swapped 9              — registry count
0x45F848: 9 × 20-byte registry records:
           [8-byte name][12-byte meta:
               4 zero, 2 zero, u16 V1-visible, 2 zero, u16 V2-visible]
           where code uses  byteswap([rec+0x0C])  → out value
                            0x45F830 + byteswap([rec+0x10]) → structure pointer
```

Registry entries and resolved targets (see 01-executable-architecture §5.1 for the
full table):

- `MENUexam` → `0x45F900` (menu structure, header `%MNU\0 00 01 00 00`)
- `MENUfsit` → `0x45FB18` (menu structure)
- `MENUscal` → `0x4602A8` (menu structure)
- `VWINdoku` → `0x4605D0` (VWIN structure, header `%VUU\0 00 01 00 00` + "VWIN" @ +8)
- `VWINefik` → `0x460BF0`, `VWINemik` → `0x461038`, `VWINepxm` → `0x4614E8`,
  `VWINesik` → `0x461DF0`, `VWINprvw` → `0x4621A0` (VWIN structures)

Beyond the registry: the **widget state table** at ~`0x4624CC`–`0x4653xx+` holds
per-widget-type/per-state records, e.g.:

```
0x4631D4: "Disabled" (8) "BUTN" (4) 00  | 1E 00 28 00 78 00 42 00  | … 13 00 …
0x463210: "Default"  (7) 00 "BUTN" 00  | 82 00 28 00 DC 00 42 00  | … 13 00 …
```

The four u16 pairs after each state/type pair are PROBABLE metric values
(see 05-ui-and-skin-model §2).

## 4. On-disk format — UNCONFIRMED

No on-disk header, magic, version field, record table, or encoding has been
confirmed yet from code alone. The on-disk writer is expected to sit above
`fileCreate`/`fileWriteWhole`; the builder of the save buffer has not yet been
isolated (next session). Candidate entry points:

- `FUN_00417070` — calls both `fileOpenMkDir` and `fileCreate` (open-or-save
  dispatcher)
- the "Open/Save Appearance File" dialog handlers (callers of the `0x45F760`/
  `0x45F778` strings — not yet traced)
- document commit path: `createDocument`'s collaborators `FUN_00401000` (doc
  alloc), `FUN_00401290`, and the 11 subsystem init calls in `constructApp`
  (`0x4361F0`, `0x4229A0`, `0x437220`, `0x4360D0`, `0x437C90`, `0x437EE0`,
  `0x437850`, `0x436AE0`, `0x435E40`, `0x43CEB0`, `0x43CD30`)

## 5. Byte-order observations in the built-in DB (CONFIRMED reads)

- The registry count and record offset fields are stored **byte-swapped**
  relative to the native little-endian order (the loader byte-swaps them back).
  Visible bytes `00 00 09`-style → value 9; visible `00 00 0D A0` → offset 0xDA0.
- The embedded "VWIN" FourCC and state strings are stored in natural ASCII byte
  order.
- Whether the **on-disk** format uses the same byte-swapped fields is UNKNOWN —
  the built-in DB may be a compile-time layout distinct from the file encoding.
  Do not assume they are identical.

## 6. Evidence needed to confirm the on-disk format

1. At least one real `.hap` file (ideally several: default-export, edited,
   different Haxial versions) — hexdump the first 256 bytes; look for
   `VWIN`/`BUTN` FourCCs, Pascal length prefixes, and the `0x1CA6C39A` value.
2. Observation of AppearanceEdit saving a file (screen recording or before/after
   file bytes) to correlate with `fileWriteWhole` buffer contents.
3. The save-buffer builder function (next RE target) to list the exact field
   emission order.
4. A second Haxial client executable (the game/runtime that consumes `.hap`) to
   cross-check the parser.
