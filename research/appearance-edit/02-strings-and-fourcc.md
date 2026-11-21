# 02 — Strings and FourCC (AppearanceEdit.exe)

Status: **in progress** (session R0-A, 2026-11-17)

## 1. Confirmed string representations

### 1.1 Pascal strings (CONFIRMED — code-level)

A Haxial Pascal string is `1 length byte (0..255) + N payload bytes`, N = length.
The length prefix is authoritative; payload may contain any bytes (including 0x00,
UTF-8 sequences, BOM).

Confirmed by decompiling the framework's string helpers (see §2): the length byte is
read/written first and only the declared count of payload bytes is copied/compared.
All helpers cap at 0xFF (a 256-byte payload limit is inherent to the type).

### 1.2 Embedded Pascal string pool in .data (CONFIRMED bytes)

| Address | Len | Payload | Note |
|---|---|---|---|
| `0x45F744` | 9 | `Untitled ` | document title prefix (trailing space) |
| `0x45F750` | 12 | `Untitled.hap` | default file path; referenced from `FUN_004030F0` @ `0x403169` |
| `0x45F760` | 21 | `Open Appearance File: ` | open dialog prompt |
| `0x45F778` | 21 | `Save Appearance File: ` | save dialog prompt |
| `0x45F790` | 90 (0x5A) | `Haxial ApeeransEdit (AppearanceEdit) 1.400\nHaxial ApeeransEdit 1.400 … .haxial.com` | version/about block; note original typo "Apeerans" |
| `0x45F7ED` | 18 | `About ApeeransEdit` | dialog title (same typo) |
| `0x45F80D` | 14 | `AppearanceEdit` | window class / app name |

Raw sample (`0x45F744`):

```
09 55 6e 74 69 74 6c 65 64 20 | 0c 55 6e 74 69 74 6c 65 64 2e 68 61 70 00
|len  9  "Untitled "        |len 12 "Untitled.hap"                (00 = next byte of pool gap)
```

### 1.3 C strings

Standard null-terminated C strings are used at the Win32 boundary (all `*A`/`*W`
APIs) and for compiler-generated literals in `.rdata` (e.g. `"!SError!"` @
`0x453F30`, dialog texts in `0x454xxx`–`0x466xxx`). MultiByteToWideChar is imported
for byte→wide conversion (file-name handling converts Pascal/byte names to wide).

### 1.4 FourCC identifiers (reclassified in S2 A2 — see `17-s2-fourcc-records.md`)

**Three representations, never conflated** (CONFIRMED, doc 17 §4):

| Representation | `TIKB` example | Where |
|---|---|---|
| Memory-ASCII (raw bytes = spelling) | `54 49 4B 42` | descriptor `class4cc`; `%REZ` type/instance; instance names |
| Code constant (BE reading of the spelling) | `0x54494B42` | `PUSH`-ed arguments (`VWIN`→`0x5657494E` @ `0x408EDD`, `MENU`→`0x4D454E55` @ `0x4124A1`) |
| Class-tag storage (constant as u32LE ⇒ **reversed spelling in memory**) | `42 4B 49 54` = "BKIT" | class object tag @+0x00 (doc 17 §6) |

`widgetInstantiate` and `builtinRecCmp` bswap the memory-ASCII side; the
`widgetClassLookup` slow path compares the code constant directly against the
tag word (no bswap) — verified from the `0x409150` subtract-chain.

**Widget class FourCCs (21 classes, doc 17 §6):** descriptor spelling —
`VUU!` (view, base), `WIND` (window), `KNTR` (container), `TXTS` (text),
`LSTS` (list, resolved A3), `CLST` (column list, resolved A3 — the earlier
D-section-colors hypothesis is disproven, see 17 §6),
`IMGS` (image), `BUTN` (button), `KLBL` (klabel), `LABL` (label), `BOX!`,
`SEPR` (separator), `BPMN` (menu button), `IKBT` (icon button), `KOLR`
(color; K-swap of COLR), `PRGS` (progress), `SLDR` (slider), `HOLD` (holder),
`MBAR` (menu bar), `IKON` (icon).

**Type FourCCs in the `%REZ` registry:** `VWIN` (window payload), `MENU`
(menu payload). **Instance FourCCs:** `doku efik emik epxm esik prvw` (the six
windows), `exam fsit scal` (the three menus), plus ~45 lowercase widget
instance names (doc 17 §11).

**FourCCs previously listed as strings — reclassified (A2):** every 4-char
alphabetic run that is a class/instance identifier has been removed from the
"string" inventories; full classification of all 358 four-char runs in doc 17
§11 (17 reversed class tags + 4 with `!`, straight descriptor spellings,
instance names, part-name tables, and false positives such as font-glyph runs
`wvgw wwva` and Win32 class regs `TXET lTrP ATAD KRLK` that are *not*
identifiers). Genuine 4-char UI strings (`Exit Save Copy Find …`) are preserved.

**% tags:** `%REZ` (registry), `%VUU` (view object), `%MNU` (menu), `%IKN`
(HAP icon section). User-confirmed (2026-11-20): `%VUU` = "view". The `%`
marker convention matches BeOS-style resource tags (PROBABLE).

**Node model (user-confirmed):** "the nodes are usually the class ID ('VWIN'
for view window, TIKB for tick button/checkbox, etc) followed by a four char
code identifier (ie. doku)". Developer naming eccentricity: C↔K swaps
(`KOLR`=COLR, `KLBL`=K LABEL, `KNTR`≈KONTRAINER, `KREA`≈CREA) — user-supplied,
PROBABLE.

## 2. Pascal-string helper functions (CONFIRMED by decompilation)

All `__cdecl`. "pstr" below = length-prefixed byte string. Return values as decoded.

| Address | Proposed name | Prototype (inferred) | Behavior |
|---|---|---|---|
| `0x438390` | `pstrCopy` | `u32 pstrCopy(u8 *dst, const u8 *src)` | Copies length byte + payload (unrolled 8-byte loop). NULL src → len 0. Returns length copied. |
| `0x438440` | `pstrCopyTrunc` | `u32 pstrCopyTrunc(u8 *dst, const u8 *src, u32 max)` | Same, payload capped at `max`. |
| `0x438500` | `pstrAppend` | `u32 pstrAppend(u8 *dst, const u8 *src)` | Appends src after dst's payload; total length capped at 0xFF (excess truncated). Returns new length. |
| `0x4387B0` | `pstrAppendByte` | `u32 pstrAppendByte(u8 *dst, u8 ch)` | Appends one byte if len < 0xFF. Returns old length. |
| `0x4387E0` | `pstrEqual` | `u32 pstrEqual(const u8 *a, const u8 *b)` | 1 if length+payload identical, else 0. |
| `0x438840` | `pstrFindByte` | `u8 *pstrFindByte(const u8 *s, u8 ch)` | First occurrence of byte `ch` in payload (offsets 1..len), else NULL. |
| `0x4389E0` | `pstrFromRaw` | `u8 *pstrFromRaw(const u8 *raw, u32 len)` | Allocates len+1 (via `FUN_0041BBA0` heap), len capped 0xFF, copies raw bytes (no length prefix in source). |
| `0x438AB0` | `pstrDup` | `u8 *pstrDup(const u8 *s)` | Heap duplicate (len+1); NULL if s NULL or len 0. |
| `0x439760` | `pstrFindForbidden` | `u8 *pstrFindForbidden(const u8 *s, u32 len)` | Scans raw bytes (no prefix): flags `b < 0x21 && (tab[b] & 0x60)` or `0xC2 0x80` pair; returns pointer or 0. Table @ `0x467D10` (256-byte class table). Used for file-name validation. |
| `0x4397B0` | `fmtInt` | `u32 fmtInt(u32 value, char *dst, u32 cap, u32 flags)` | Formats integer into raw (unprefixed) ASCII buffer, returns char count. Flags: `0x1000` hex ("0x" if `0x2000`), `0x0400` binary ("0b" if `0x2000`), `0x0200` thousands commas, `0x0100` min-width (width = `flags & 0x7F`), `0x10000`/`0x4000` sign ('-'/'+'). |

Unrenamed neighbors in the same cluster (3-param, semantics pending):
`0x4385F0`, `0x4386E0`, `0x438720`, `0x438760`, `0x438880`, `0x438930`
(decompilation in progress at session end). Also `0x438110`/`0x438160`/`0x4381A0`/
`0x438290`/`0x4382F0` (2–3 param) below the cluster.

Callers of `pstrCopy` (`0x438390`) include `FUN_004030F0` (document title +
"Untitled.hap" path) — the helper is **not inlined**; the framework funnels all
pstr traffic through these functions.

## 3. Ghidra string-analysis artifacts (must not be trusted)

- Ghidra reports `"…\nxVWINdoku"` @ `0x45F882` — the `0x0A 0x78` bytes are actually
  the tail of the 12-byte meta field of registry record `VWINdoku`; the true
  boundaries are the 8-byte name at `0x45F884`.
- Ghidra reports `"fddSHELL32"` @ `0x455F45`, `"Volumes!SError!"` @ `0x455FF9`,
  `"4Save changes to these documents…"` @ `0x455168` etc. — leading bytes belong to
  adjacent C-string literals or data; do not adopt Ghidra's merged boundaries.
- For every string used as evidence: raw bytes were inspected via hexdump before use
  (this file records them).

## 4. Open questions (string layer)

- Semantics of `0x4385F0`/`0x4386E0`/`0x438720`/`0x438760`/`0x438880`/`0x438930`
  (PROBABLE: case-insensitive compare, find-substring, insert/replace, concat variants).
- Meaning of the 256-byte class table @ `0x467D10` (bits 0x20/0x40 of 0x60).
- Whether any pstr payload in this binary contains UTF-8 BOM bytes (0xEF 0xBB 0xBF)
  or 0xC2-leading 2-byte sequences — none confirmed yet in the .data pool;
  `pstrFindForbidden`'s `0xC2 0x80` check suggests the author handled such bytes.
- Where the wide (UTF-16) counterpart helpers live (file-name conversion uses
  MultiByteToWideChar directly in the file layer, §03).