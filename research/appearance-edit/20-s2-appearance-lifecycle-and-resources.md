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
