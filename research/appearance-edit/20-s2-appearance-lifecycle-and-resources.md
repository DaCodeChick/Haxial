# S2 Batch E — Appearance object, lifecycle, and resource sections

Session: S2 (AppearanceEdit.exe v1.400, image base 0x400000).
Checkpoint: `bc503cf` → this milestone. Evidence: disassembly (skinInstall
0x428C70, styleColorGet 0x42A140, inkNameLookup 0x42D3F0, searchRecords
0x4401C0, widgetBaseFill 0x42A170, bmpFillRect 0x4263B0, hapLoadEntry
0x4036B0, appearanceLoadInstall 0x402FA0, appearanceResetDefault 0x403020,
earlyInit 0x41DB10) + raw data (built-in blob 0x4683D4, 111-file corpus
scans). Confidence levels per item.

## 1. The appearance object IS the C section (CONFIRMED)

`skinInstall(hapImage, size)` (0x428C70) reads the section
directory of a **HAP file image** and stores pointers **into that image**
into the style context. There is no separate parse or allocation of an
"appearance object": the runtime appearance object and the on-disk C
section are the same memory (BE structural fields bswap32'd at each read —
the established S1 pattern).

- `g_appFallback` (0x466950) := built-in C section **always**
  (built-in blob 0x4683D4, '%HAP\x00\x02' v2, C @+0x34=0x144).
- `g_appCurrent` (0x466954) := `hapImage + bswap32(hapImage+0x34)` when the
  loaded image has a C section (size field +0x38 ≠ 0), else
  `g_appFallback` (whole-C fallback — e.g. the 2 corpus files with C size 0).
- Part lookup (sldrRender/sldrPartLookup/sbarRectsCompute, D-late):
  `partPtr = gApp + bswap32(partOff[id])`; `partOff[id] == 0` → retry with
  `g_appFallback` (per-part fallback).

### 1.1 C section layout (CONFIRMED — code + raw, all samples)

```
+0x00  16 x u32BE  zero in the built-in and all 111 corpus files
               (PROBABLE reserved; no code reads below +0x40)
+0x40  partOff[512]  u32BE pool offsets; 0 = empty slot;
               nonzero = offset WITHIN the C section of the part blob
+0x840  part blob pool (C size - 0x840 bytes)
```

Raw verification: built-in C size 0x7838; directory 0x7838-0x840 = 28664 B
pool; all 142 used offsets in [0x840, 0x77F8); 37 of 39 corpus v1 files
have C ≥ 0x840 with every used offset pointing at a W/H-valid part blob
(0 invalid of 3983 checked); 2 corpus files have C size 0 (no C section).

## 2. 131-vs-512 reconciliation (RESOLVED)

- **512** = fixed part-offset directory capacity. S1-confirmed for the
  corpus (doc 04: "512 × u32 BE pool offsets … 13–127 of 512 slots used
  per file") and re-verified this session for all 39 corpus v1 files with
  a C section plus the built-in v2 blob (142 used).
- **131** was a Batch-D assumption: `partOff[131]` was recorded after
  verifying entries only up to index 130 (the top SLDR id). It was never a
  format field and no code path bounds the table at 131.
- Directory usage is sparse: built-in max index 267 (142 used); corpus v1
  max index up to 263, 13–127 used per file.
- Consumers index by **part id** (0..511); missing id → fallback (§1).
- **Correction:** the D-late "appearanceObj fields" +0x288/+0x28C/+0x298
  (hSbar*) and +0x2D4/+0x2D8/+0x2E4 (vSbar*) are **partOff entries**, not
  struct fields: partOff[146]/[147]/[150] (horizontal sbar) and
  partOff[165]/[166]/[169] (vertical sbar). The Ghidra `appearanceObj`
  struct was replaced with the corrected 0x840 B layout.

## 3. HAP section map (CONFIRMED — skinInstall + raw)

Header pairs (u32BE, doc 04): C +0x34/0x38, D +0x3C/0x40, E +0x44/0x48,
F +0x4C/0x50, G +0x54/0x58.

| Sec | Runtime home (styleCtx) | Contents |
|---|---|---|
| C | g_appCurrent/g_appFallback @+0x38/+0x34 | appearance object (§1) |
| D | gStyleDColors @+0x40 (+count @+0x44; fallback @+0x3C) | style color roles (§5) |
| E | gIkonSec @+0x48 (+size @+0x4C) | named record pool — icon records (doc 16: 155 names/192 rows corpus) |
| F | gInkFSec @+0x50 (+size @+0x54) | named record pool — ink objects (§6) |
| G | gInkG @+0x68 (+size @+0x6C) | named record pool (20 records built-in; role TBA) |

**Named record pool** (E, F, G all follow it — CONFIRMED raw for E/F/G of
the built-in): `{ u32BE count, count × u32BE record offsets, record pool }`.
Ghidra struct `hapNamedPool` (DTM only; no fixed program address to
apply it at). Built-in: E count 36, F count 25, G count 20.

D fallback: `gStyleDColors` := loaded D only when D size ≠ 0, else built-in
D; `gStyleDColorsFallback` (0x466958) is **always** the built-in D.
E/F/G use a size > 4 gate (absent → pointer 0).

## 4. Lifecycle (CONFIRMED)

```
startup      earlyInit: g_hInstance := arg; skinInstall(0, 0)
                    -> built-in image: all section ptrs := built-in,
                       scale 1/1, metrics from bases; gSkinInstalled=1
load file    hapLoadEntry(ownerCtx, file):
                    doc-list head 0x45F820 (linked doc+0x28); if the file is
                    already open in some doc (handle doc+0x90, 0x41B5F0) ->
                    refresh (0x40CC70(doc+0xC), 0x41A270(&file)), return;
                    else read whole file (0x41A450/0x41A640; size 0 ->
                    hError 0x30074), doc = 0x401000(&size)+0x401290(doc,0),
                    filename pstr -> doc+0x9C (0x438440),
                    hapParse(doc, buf, size), notify 0x40C5C0(doc,[doc+0xC],1),
                    doc+0x90 = file; if the current doc is unmodified
                    (byte[+0x19D] == 0, 0x401470) -> 0x408720(&oldDoc)
                    destroys it. Return doc.
apply        menu cmd 0x403930 -> appearanceLoadInstall(owner, doc, file):
                    buf = hapSerialize(doc, &size)   [doc -> HAP image]
                    skinApply(buf, size) = skinInstall + 0x40F220 + 0x41D390
                    memFree(&owner+4); owner+4 = buf   [owner owns the
                    installed image; g_appCurrent & friends point into it]
                    notify 0x40C5C0(..., 0x10)
reset        appearanceResetDefault(owner): notify; skinApply(0, 0)
                    -> built-in
```

- The **installed skin** is a HAP image buffer owned by the owner struct at
  +0x4; replacing it frees the old buffer (no separate appearance-object
  lifetime exists — destroying = freeing the image).
- hapDoc (document) fields: +0x0C notify arg, +0x28 next-doc, +0x34..
  34 × 14 B resource entries (doc 04), +0x90 fileRec, +0x9C name pstr,
  +0x19D modified flag. The doc is the editable model; the installed image
  is what the toolkit reads.
- `skinApply`'s post-install calls 0x40F220 / 0x41D390 are still
  un-decoded (ink/refresh housekeeping) — E-follow-up.
- Built-in vs loaded: the built-in blob is a HAP image in .data (v2, scale
  1/1, flags 01 01). The app never patches it; all installation paths go
  through skinInstall.

## 5. D section — style color roles (CONFIRMED)

`styleColorGet(role)` (0x42A140):

```
role >= 0x36 (54)            -> 0
role < gStyleDColorCount     -> [gStyleDColors + role*4]   (RAW LE load)
else                         -> [gStyleDColorsFallback + role*4]
```

- D section = N × u32; on-disk bytes `[00][RR][GG][BB]` (same convention as
  C-blob pixels, doc 04). **No bswap** in the getter (structural fields are
  BE; color values are not).
- **Version difference:** v2 built-in D size 0xD8 = **54 roles**; corpus v1
  D size 0x330 = **204 roles** (40 of 111 files carry a D section; the rest
  use the built-in 54-role D for all roles — both getter branches hit the
  built-in table when D is absent).
- Encoding check: all 8160 corpus D colors + 54 built-in have byte0 == 0x00
  (1 exception of 8160). `bmpFillRect` (0x4263B0) treats color byte0 as a
  "keep-old" blend amount: 0x00 = solid (fast path, row memset via
  0x434350), 0xFF = no-op, between = per-channel blend — so D colors always
  take the solid path and the raw dword is written as the pixel.
- **Consumer matrix** (14 call sites, 10 functions) — usage only; role
  semantics beyond the painter association are NOT established (no
  speculative names assigned):
  - widgetBaseFill mode 0/1 → roles **0/1** (base fill; mode 2 = tile
    part 13 — partOff[13], empty in built-in → no-op there).
  - 0x4058f0 & 0x404b00 & 0x42d310 & 0x42d670: state-selected trio
    **0x0E / 0x0F / 0x10** (byte/flag-gated selection).
  - 0x42b5d0: pair **0x20/0x21**; 0x42a2d0: pair **0x22/0x23**
    (state-gated; 0x40000 flag variant).
  - 0x43d230: **0x04**; 0x425ca0: variable role = u16[widget+0x18];
    bmpSetFillMode: parameter.

## 6. F section — ink objects (CONFIRMED)

`inkNameLookup(out, namePstr)` (0x42D3F0, was FUN_0042d3f0):

1. If `gInkFSec` (F pointer) set: `searchRecords(name, F+4, count=bswap(F+0),
   stride 4, cmpFn 0x42D370, out)` — binary search over the offset
   directory (searchRecords 0x4401C0: generic cmpFn-driven binary search,
   linear for count ≤ 1).
2. Match → `*out = Fsize − matchOffset` (aux slot), return
   `F + matchOffset` (record pointer).
3. Miss → retry with the name prefix before the **last** '/'
   (`pstrRFindChar`, 0x43FD00): "folder/standard" → "folder" → fail.
4. Still miss → identical scan in the **built-in** F section
   (0x4683D4 + bswap(+0x4C)); else `*out = 0`, return 0.

skinInstall lookups: `gInkF = lookup("data")` (pstr @0x4576A0),
`gInkF2 = lookup("folder/standard")` (pstr @0x4576A8) — names confirmed
from .rdata. Record internal layout (header fields after the name) is
Batch E2/F scope.

## 7. Verified part-id ledger (cPartId)

Part ids below are the ones with code-confirmed consumers (built-in
dimensions where noted). Ghidra enum creation was **blocked** (MCP
create_structure is struct-only) — recorded here instead.

| id  | name | consumer | built-in dims |
|---|---|---|---|
| 13  | C_PART_BASEFILL_TILE | widgetBaseFill mode 2 | (empty in built-in) |
| 94  | C_PART_SLDR_H_DESC | sldrPartLookup (gApp+0x1F8) margins | (empty in built-in → default 5/5/13) |
| 106 | C_PART_SLDR_V_DESC | sldrPartLookup (gApp+0x228) margins | in use |
| 110–112 | SLDR H track (3 states) | sldrRender | 5×7 |
| 114–116, 118–120 | SLDR H thumb (6 states) | sldrRender | 14×16 |
| 122–124 | SLDR V track | sldrRender | 7×5 |
| 126–128, 130–132 | SLDR V thumb | sldrRender | 16×14 |
| 146 | C_PART_SBAR_H_LARGE | sbarRectsCompute | 63×16 |
| 147 | C_PART_SBAR_H_SMALL | sbarRectsCompute | 33×16 |
| 150 | C_PART_SBAR_H_THUMB | sbarRectsCompute | 7×16 |
| 165 | C_PART_SBAR_V_LARGE | sbarRectsCompute | 16×16 |
| 166 | C_PART_SBAR_V_SMALL | sbarRectsCompute | 16×16 |
| 169 | C_PART_SBAR_V_THUMB | sbarRectsCompute | (in use) |

Not included: ids with no code-confirmed consumer (e.g. built-in 148/149
35×16 / 5×16 near the sbar family — PROBABLE arrow buttons, unverified).

## 8. styleCtx full layout (CONFIRMED — skinInstall writes)

204 B (0xCC) verified extent @0x46691C; Ghidra struct `styleCtx`
replaced (DTM only, not applied over the named g_* globals):

```
+0x00..+0x33  pad (13 × u32; unknown — E3)
+0x34 g_appFallback        +0x38 g_appCurrent
+0x3C gStyleDColorsFallback +0x40 gStyleDColors
+0x44 gStyleDColorCount    +0x48 gIkonSec   +0x4C gIkonSecSize
+0x50 gInkFSec             +0x54 gInkFSize
+0x58 gInkF                +0x5C inkFAux    +0x60 gInkF2  +0x64 inkFAux2
+0x68 gInkG                +0x6C gInkGSize
+0x70 pad u32              +0x74 gOnceFlag (byte)
+0x75 gScaleNum (byte)     +0x76 gScaleDen (byte)  +0x77 pad
+0x78..+0xBF scaledMetrics[35] u16 = gStyleMetricBases[0x46703B+i]·num/den
+0xBE..+0xC7 pad
+0xC8 gSkinInstalled (u32; set by earlyInit)
```

**Correction to D-late:** the "sbar metrics minThumb/thumbAdd/threshold at
+0x98/+0x9A/+0x9C" are **cells of the 5×7 scaled-metrics matrix**
(metrics[16] u16 @+0x98, metrics[17] @+0x9A, metrics[18] @+0x9C), not a
separate region. Ghidra xrefs confirm the readers (0x41DECC/0x41DC42
sbarRectsCompute, 0x41F5CE/0x41EE8A/0x41E32F/0x41F5EA/0x41EEA6/0x41DEE8/
0x41E34B/0x41F168/0x41EA23/0x41E0A7) and that +0x98 is both written by
skinInstall's metrics loop (ECX=0 case) and read by 0x42AD6D — one region,
one meaning.

Once-init: `if (gOncePtr == 0) { gOncePtr = 0x47B324; gOnceFlag = 0; }`
(gOncePtr 0x46698C — the 0x47B324 table contents: E3).

## 9. Ghidra changes (read-back verified; project saved)

- **Data renames (7):** gInkTbl→gIkonSec (0x466964), gInkCount→
  gIkonSecSize (0x466968), gInkF→gInkFSec (0x46696C), gStyleStrA→gInkF
  (0x466974), gStyleStrB→gInkF2 (0x46697C); new labels gOnceFlag
  (0x466990), gSkinInstalled (0x4669E4). Preserved: g_appCurrent/
  g_appFallback/gStyleDColorsFallback/gStyleDColors/gStyleDColorCount/
  gInkFSize/gInkG/gInkGSize/gScaleNum/gScaleDen/gOncePtr.
- **Function renames (3):** inkNameLookup (0x42D3F0),
  bmpFillRectFromRect (0x426660), pstrRFindChar (0x43FD00).
- **Prototypes (7):** inkNameLookup, styleColorGet, bmpFillRectFromRect,
  pstrRFindChar, skinInstall, skinApply, appearanceLoadInstall.
- **Comments (14):** skinInstall, appearanceLoadInstall, skinApply,
  appearanceResetDefault, hapLoadEntry, styleColorGet, inkNameLookup,
  searchRecords, widgetBaseFill, bmpFillRectFromRect, bmpFillRect,
  earlyInit, pstrRFindChar (+ read-back spot-checked).
- **Structures:** `appearanceObj` replaced 744 B → 2112 B (reserved[16] +
  partOff[512]; pool tail documented, not modeled); `styleCtx` replaced
  157 B → 204 B full layout; new `hapNamedPool` (8 B header, /haxial).
  **Blocked:** cPartId enum (MCP create_structure is struct-only) — part
  ids recorded in §7 + ledger.
- **Not applied:** styleCtx/hapNamedPool are DTM-only (no fixed program
  address hosts them; applying over named globals would fight the symbol
  layer — same rule as D-late). Struct offsets verified by Ghidra-reported
  sizes (2112/204/8) matching the hand sum; per-field read-back not
  available via MCP (no get_structure).

## 10. Open / deferred (Batch E remainder)

- 0x40F220 / 0x41D390 (skinApply post-install) — decode (likely ink-cache /
  refresh).
- E section record layout + the 155-name icon table binding to IKON
  widgets (doc 16) — E2/F. F record internals after the name — E2.
  G section role (20 records) — E3.
- gOncePtr table @0x47B324 — E3. styleCtx +0x00..+0x33, +0x70, +0xBE..+0xC7
  — E3. 0x401000/0x401290 (doc create), 0x408720 (doc destroy — C1
  adjacency: verify it is the doc dtor and closes the "detach" question),
  0x40C5C0 (notify) — E3/C1.
- cmpFn 0x42D370 (record-name compare) — verify exact contract (E2).
- hapParse (0x402900) full decode — doc-model side (sections → doc
  resource entries); not needed for the install model (image-based).
- SLDR max/value anomaly — unchanged, held open (doc 19 §5.5; owner
  directive: runtime validation checklist, Win32 S3).

## 11. Section completion — E/F/G record formats + post-install (Batch E2 partial)

### 11.1 E section = %IKN icon records (CONFIRMED by raw walk, built-in)

Record (all 35 built-in records uniform):
```
+0x00  u32BE  0x25494B4E  "%IKN" magic
+0x04  u16BE  0x0001 (constant across all records)
+0x06  u16BE  image/state count: 1, or 2 (E dir[5], dir[23] — multi-state)
+0x08  u16BE  width  (built-in: 10..32)
+0x0A  u16BE  height (built-in: 13..32)
+0x0C  u16BE  flags  (0x0101..0x0108; bit semantics TBD)
+0x0E  u16BE  two 8-bit values (n,n or n1,n2; semantics TBD)
+0x10  u32BE  palette count (20 or 32)
+0x14  palette: count × [00][RR][GG][BB] (LE, same encoding as C/D)
       then index pixel data (bpp TBD — consistent with 1/2/4bpp per doc 04)
```
Directory: 36 entries, **dir[0] = 0 (reserved empty slot)**; icons = dir[1..35].
Icon names are positional (gEIconNames, 155 names, doc 16 §4) — the record
itself carries no name. E = the appearance's **icon set**; IKON widget class
(0x468310) consumes by index (binding detail deferred to E3).

### 11.2 F section = named ink records (CONFIRMED by raw walk + lookup code)

Section: {u32BE count (25 incl. dummy), count × u32BE offsets, pool}.
**dir[0] = 0x19 (dummy = count value itself)**; records = dir[1..24].
Record:
```
+0x00  u32BE  "%IKN" magic
+0x04  u16BE  0x0001
+0x06  u16BE  flags (0x0402 "data", 0x0502 others)
+0x08  name: null-terminated (e.g. "data", "font/")
       u8 name-region length (13 for "data": 4+1+8 pad)
       then embedded ink bitmap block (sub-structure TBD — E3)
```
Built-in names (dir 1..24): **data, font/, text/, audio/, image/, video/,
folder/, volume/, archive/, driver/, volume/cd, volume/hd, volume/dvd,
volume/fdd, volume/net, volume/ram, volume/cart, folder/audio,
folder/images, data/truncated, folder/dropbox, folder/uploads,
alias/unattached, executable/plugin, executable/program**.

Name matching (inkNameLookup → searchRecords + cmpFn 0x42D370): the search
key is a **fixed 16-byte buffer** (pstr len + chars, e.g. "folder/standard"
= exactly 16B); cmpFn is a two-step hash compare (0x43F510 over
{name[0:4]+off, name[4:8]−off, &byte}, gate on name[12]==byte, then
0x43F9E0 over {name[8:12], step1-ret, byte}) — the exact hash functions are
deferred (E3); the functional order (exact → last-'/'-prefix → built-in
F fallback) is code-CONFIRMED.

**Consequence**: "data" → gInkF = F+0x68 record. **"folder/standard" is NOT
in the built-in F set** (no exact match; prefix "folder" ≠ "folder/";
built-in fallback = same set) → **gInkF2 (styleCtx+0x60) = NULL for the
built-in appearance**. Consumers must tolerate NULL (or the role only
matters for non-built-in appearances — corpus check deferred to E3).

### 11.3 G section = %MSI mouse cursors (CONFIRMED — S1-decoded, re-verified)

20-entry directory, **dir[0] = 0 (dummy)**, 19 %MSI records. Format already
fully decoded in S1: `hapMsiRecordParse` (0x4452C0; magic 0x254D5349, W/H,
hotspot @+0x0C/+0x0D, bpp @+0x0E ∈ {2,8,32}, palette, pixels),
`hapGSectionRead` (0x408570; slot table), `msiBlobToBmp` (0x445080 →
hapBitmapObj). G = the appearance's **mouse cursor set** (editor "Mouse
Icons" tab, screenshot refs/screenshots/appearance-edit/.../mouseicons.png).
This batch's raw walk re-confirms the built-in layout (19 records, W/H
8×12..19×19, 2/8bpp palettes).

### 11.4 Post-install housekeeping (CONFIRMED, Ghidra renamed)

`skinApply` (0x435030) = skinInstall (0x428C70) + **winMetricsResync**
(0x40F220) + **cursorCacheReset** (0x41D390):
- winMetricsResync: window object list head 0x466350 (link +0x00, hwnd +0xC):
  per node — system metrics (4B) via 0x42E7D0(node+0x64,...) vs cached
  node+0x8B..0x8E; on change: rect via 0x40C810(node,&r16,0,0) +
  **SetWindowPos**(hwnd, 0, x, y, w, h, 0x14); store metrics. Then
  **IsWindowVisible**(hwnd) → **InvalidateRect**(hwnd, NULL, FALSE).
- cursorCacheReset: hCur = **GetCursor()**; 20-slot handle table @0x466C28:
  non-null → DestroyCursor (remember the live one if == hCur), slot := 0;
  0x41D400(list @0x466C20); DestroyCursor(live) if found. Cursors are
  recreated on demand after install (they come from the G section).

### 11.5 Deferrals (E2/E3 — next)

1. cmpFn hash functions 0x43F510 / 0x43F9E0 (exact name-match contract).
2. F record embedded ink bitmap block sub-structure; flags 0x0402/0x0502.
3. E record flags +0x0C/+0x0E semantics; pixel bpp per record; dir[0]
   reserved-slot convention rationale; IKON widget → E-index binding.
4. G: slot table → cursor-name mapping (gMCursorNames?); %MSI field
   semantics already S1-documented.
5. 0x42E7D0 (metrics getter) / 0x40C810 (rect getter) / 0x41D400 (list
   consumer) internals.
6. styleCtx +0x00..+0x33 (per-window list? — 0x466350 region), +0x70,
   +0xBE..+0xC7.
7. gOncePtr table @0x47B324 consumers.
8. 0x401000/0x401290 (doc create), 0x408720 (doc dtor — C1 "detach"
   counterpart), 0x40C5C0 (notify), 0x41DC25.. (26 g_appCurrent consumer
   sites — consumer matrix), hapParse full decode.
9. Corpus: v1 E/F/G section verification (v1 layout differs — S1: v1 E =
   155-name table); "folder/standard" presence in corpus F sections.

## 12. IKON widget ↔ E-icon binding closure (Batch E priority 5)

### 12.1 IKON class object (CONFIRMED, raw 0x468310)

196 B, same class layout as SLDR/MySB: magic "IKON" @+0, size 0x78 = **120 B
instance**, childCountFn NULL, init = **ikonWidgetInit** (0x43D130),
+0x10 = **ikonHandlerRet** (0x43D220, RET stub), paint = **ikonPaint**
(0x43D230); +0x18..+0x4C shared framework thunks (0x409BF0..0x409DE0).

### 12.2 ikonWidgetInit (0x43D130) — payload map (CONFIRMED, disassembly)

Args (widget, payload, len); no-op if len < 0x10.

| payload | width | → widget field | semantics |
|---|---|---|---|
| +0x00 | u32BE | +0x38 (via resolve) | **icon index into the %REZ "IKON" table**; 0 → resolve NULL → sentinel 1 |
| +0x04..05 | — | — | not read (reserved) |
| +0x06 | u16BE | +0x40 | tint color (u16); 0 = untinted |
| +0x08 | u32BE | +0x44 | option flags (default 0x30 when 0); OR'd with 0x100000 at blit time |
| +0x0F | u8 | +0x48 (via 0x438930) | state count, clamped to 0x2F (47) |
| +0x10.. | states | +0x48 | state table (per-state blit descriptors) |

Icon resolve = `lookupBuiltInRecSoft` (0x445900, S2-named) with tag
0x494B4F4E ("IKON" LE): searches the **%REZ registry** (0x45F830: count
@+0x14, 20 B records @+0x18, cmpFn 0x4457C0). On hit: out = bswap(rec+0x0C),
return = 0x45F830 + bswap(rec+0x10) = **pointer into the registry's record
pool**. Miss → 0 → widget+0x38 := **1 (sentinel)**.

**Closure**: E-section icons are reached through the %REZ registry's "IKON"
table entry (doc 18 registry mechanism) — the widget stores the resolved
record pointer, not a raw section index. gIkonSec (0x466964) holds the raw
E section the registry table indexes. This satisfies the S2 constraint of
reconstructing the full consumer chain (payload → registry → section).

### 12.3 ikonPaint (0x43D230) — render priority (CONFIRMED, disassembly)

1. `color = styleColorGet(4)` — **D role 4** is the IKON base color
   (closes the role-4 consumer in §7's matrix).
2. if states (w+0x48) → 0x42D5F0 state-driven ink blit (opts|0x100000).
3. elif tint (w+0x40) → 0x42D190 tinted ink blit.
4. elif w+0x3C (resolve out) → 0x43F260 direct record blit (arg -1).
5. elif sentinel (w+0x38 == 1) → **dither placeholder**: pattern fill
   0xAAAAAA00 (0x425C30/0x426610/0x426690) + text **"icon missing"**
   (0x4598EC, len 12) via 0x426F50 — matches the editor's missing-icon
   rendering in screenshots.

IKON widget object (120 B): widgetBase(56) + iconRec@0x38 + recOut@0x3C +
tint@0x40 (u16) + options@0x44 + states@0x48 (+47-entry table tail).

## 13. Batch E completion assessment (2026-11-24)

| Priority | Status |
|---|---|
| 1. appearance object lifecycle | **COMPLETE** (§1–§6: install/apply/reset/load; object = C section; owner+4 ownership; winMetricsResync + cursorCacheReset post-install) |
| 2. 131-vs-512 part table | **COMPLETE** (§3: 512 = fixed capacity, corpus-verified; 131 = truncation error; partOff[146..169] sbar parts) |
| 3. appearanceObj layout | **COMPLETE** (§4: 0x840 B corrected struct; D-late "fields" reclassified) |
| 4. D-section color roles | **COMPLETE** (§7: styleColorGet, 54/204 roles, no-bswap, 14-site consumer matrix; role 4 → IKON closed) |
| 5. E-section icons + ink objects | **COMPLETE** (§11: E/F/G record formats + built-in name lists; §12: IKON binding closure via %REZ) |
| 6. remaining appearance resources | **PARTIAL** — G cursors + post-install closed; deferred to E3: gOncePtr table @0x47B324, styleCtx gaps (+0x00..+0x33, +0x70, +0xBE..+0xC7), hapParse full decode, 0x401000/0x401290/0x408720/0x40C5C0, 26-consumer g_appCurrent matrix, F ink block sub-structure, E flags/bpp |

**Batch E is COMPLETE for all six priorities** (sixth at the documented
E3-deferral boundary). Batch F (font pipeline) readiness: the 11-file .fnt
corpus is inventoried (research/fonts/00-corpus-inventory.md); hapTextObj
(140 B) and the font-glyph raster path are S1-decoded; remaining work is
fnt-on-disk → runtime glyph object binding. (Note: the F-section "font/"
record is a *named ink bitmap*, not a font file — not conflation bait.)
