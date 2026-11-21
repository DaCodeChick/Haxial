# 17 — S2: FourCC Records, Widget Identity, and the Class Registry

Status: **complete for Batches A1+A2-core** (2026-11-20). Evidence levels:
**CONFIRMED** = verified against executable code and/or raw static bytes;
**PROBABLE** = multiple consistent data points, no direct code proof;
**HYPOTHESIS** = single data point or inferred.

## 0. The `MENUscal` question — resolved

`MENUscal` is **not a string**. It is the concatenation of the type FourCC
(`MENU`) and the instance FourCC (`scal`) of the third record of the built-in
UI registry `%REZ` at `0x45F830` (record bytes at `0x45F860`):

```
0x45F860: 4D 45 4E 55 73 63 61 6C 00 00 00 00  28 03 00 00 A8 0A 00 00 00
          "MENU"   "scal"  flags=0   size=0x328 (BE)  offset=0x0A78 (BE)
```

Offset is relative to the registry header: `0x45F830 + 0x0A78 = 0x4602A8` —
a `%MNU` v1 menu payload (2,248 bytes) containing the **Scale** menu items
(the "Scale:" entries visible in the editor's menu bar). So the pair
`(MENU, scal)` is a **(type, instance) resource key**, and the full semantic
chain is:

1. The **doku** main window (a `%VUU` payload, `0x4605D0`) contains, among its
   child records, a **BPMN** widget whose *instance name* is `scal`
   (descriptor at `0x4609C8`, instance bytes at `0x4609D4`).
2. That BPMN (menu-button) widget's menu content is resolved through the
   registry key `(MENU, scal)` → the `%MNU` payload at `0x4602A8`.

The general rule, confirmed by the parser code: **a node is a (class FourCC,
instance FourCC) pair**. The instance FourCC identifies the concrete widget
instance (and, for menu-bearing classes, the menu content record). This
matches the developer's own convention: "the nodes are usually the class ID
('VWIN' for view window, TIKB for tick button/checkbox, etc) followed by a
four char code identifier (ie. doku)" (user, 2026-11-20).

## 1. The `%REZ` built-in UI registry (CONFIRMED, code-verified)

Located in `.data`. Code: `lookupBuiltInRec` (`0x445830`),
`lookupBuiltInRecSoft` (`0x445900`), `builtinRecCmp` (`0x4457C0`), and the
generic `searchRecords` binary search (`0x4401C0`).

### 1.1 Header — `rezHeader` (24 B, applied at `0x45F830` as `rezBuiltinHeader`)

**Code-verified against both consumers** (`lookupBuiltInRec` `0x445830`,
`lookupBuiltInRecSoft` `0x445900`): the header address is **hardcoded**
(`MOV EDI, 0x45f830`); the only field read is `countBE` @+0x14 (loaded as LE,
then byte-swapped); the record base is the **structural offset +0x18**
(`LEA ECX, [EDI+0x18]` — there is **no record pointer field**); stride 0x14
is a literal in the call.

| Offset | Size | Value | Meaning | Read by consumers? |
|---|---|---|---|---|
| +0x00 | 4 | `%REZ` (ASCII) | tag | No (address hardcoded) |
| +0x04 | 1 | `00` | unknown | No |
| +0x05 | 1 | `01` | version (probable) | No |
| +0x06 | 2 | zero | pad | No |
| +0x08 | 4 | `00 00 3C 98` = **u32BE 0x3C98** | **total registry span** = header(0x18) + records(9×0x14=0xC0) + payload pool(0x3BC0) — exact arithmetic match | No (in this binary) |
| +0x0C | 4 | zero | unknown | No |
| +0x10 | 4 | zero | unknown | No |
| +0x14 | 4 | `00 00 00 09` = **u32BE 9** | record count | **Yes** (LE load + bswap) |
| +0x18 | — | — | records begin (structural, no pointer) | base |

> **Correction to the A1 layout:** there is no "record table pointer" at
> +0x18 — the 24-byte header ends exactly where the records begin. The
> A1 "u64LE 0x3C98 @+0x09" reading is superseded: the value is a **u32BE
> total-span** at +0x08 (bytes `00 00 3C 98`), matching the actual layout to
> the byte.

### 1.2 Record — `rezRec` (20 B, applied as `rezRec[9]` at `0x45F848` as `rezBuiltinRecords`)

| Offset | Size | Meaning |
|---|---|---|
| +0x00 | 4 | **type** FourCC, ASCII in memory |
| +0x04 | 4 | **instance** FourCC, ASCII in memory |
| +0x08 | 4 | flags (0 in all 9) |
| +0x0C | 4 | payload size, **u32BE** |
| +0x10 | 4 | payload offset **from registry header**, **u32BE** |

Records are sorted by (type, instance); `builtinRecCmp` compares
`bswap(rec[+0])` vs the type key, then `bswap(rec[+4])` vs the instance key
(keys are the BE readings, §4). `searchRecords` is a standard binary search
(validates all params non-null, mid = lo + (count−1)/2, adjusts lo/hi by
sign of comparator).

### 1.3 The 9 records (all verified; payload pool contiguous, no gaps)

| # | Type | Instance | Size | Offset | Payload VA | Content |
|---|---|---|---|---|---|---|
| 1 | `MENU` | `exam` | 0x218 | 0x00D0 | `0x45F900` | Example menu |
| 2 | `MENU` | `fsit` | 0x78C | 0x02E8 | `0x45FB18` | File menu |
| 3 | `MENU` | `scal` | 0x328 | 0x0A78 | `0x4602A8` | Scale menu |
| 4 | `VWIN` | `doku` | 0x620 | 0x0DA0 | `0x4605D0` | **Main editor window** ("document") |
| 5 | `VWIN` | `efik` | 0x448 | 0x13C0 | `0x460BF0` | Edit file-icons window |
| 6 | `VWIN` | `emik` | 0x4B0 | 0x1808 | `0x461038` | Edit mouse-icons window |
| 7 | `VWIN` | `epxm` | 0x908 | 0x1CB0 | `0x4614E8` | Edit images window |
| 8 | `VWIN` | `esik` | 0x3B0 | 0x25B8 | `0x461DF0` | Edit (s) icons window |
| 9 | `VWIN` | `prvw` | 0x1328 | 0x2968 | `0x4621A0` | **Live preview window** |

> **Correction to an earlier note (A1):** the doku offset `0x0DA0` resolves to
> `0x45F830 + 0x0DA0 = 0x4605D0` (earlier miscomputed as `0x4606D0`; the
> latter address is *inside* the doku payload, in its child-record region).

Instance-code spellings follow the developer's naming eccentricities (user,
2026-11-20: "liked to switch C for K"): `doku` = document (also Japanese
"doc"), `prvw` = preview, `efik/emik/esik/epxm` = edit-{file,mouse,?,image}
icons/images. **The `scal` menu is the Scale control** — see §7.

## 2. `%VUU` window payloads (CONFIRMED via `vuuPayloadParse` `0x408B60`)

The `VWIN` payloads are **not** the widget tree itself at top level — they are
a framed container. Layout (offsets from payload start):

| Offset | Size | Meaning |
|---|---|---|
| +0x00 | 4 | `%VUU` (ASCII) |
| +0x04 | 2 | u16BE version = 1 |
| +0x06 | 2 | zero |
| +0x08 | 40 | **VWIN child record** (a `widgetDesc`, §3) — class `VWIN`, geometry (0,0,w,h) u16BE, `size` u32BE at +0x14 (≥ 0x2C) = the *window object size* |
| +0x30 | 4 | u32 → stored to `winObj+0x18` (packed 2×u16; meaning open) |
| +0x34 | 4 | u32 → arg of `FUN_0040CC30(win, u32)` (meaning open) |
| +0x38 | 4 | u32 (meaning open) |
| +0x3C | 8 | 4×u16BE geometry; if any non-zero: `scaleQuad` + `FUN_0040C9A0(win, 4 values)` (doku: 380, 300, 0x4E20, 0x4E20) |
| +0x44 | 4 | (align/unused in built-ins) |
| +0x5B | 1 | name length byte |
| +0x5C | … | **child widget records** — a stream of `widgetDesc` (40 B fixed + payload + children, recursively, §3) |

All six `%VUU` payloads verified consistent (record `size` values
0x2C/0x3C/0x4C/… at descriptor+0x14, all parse cleanly; disk bytes == Ghidra
memory, spot-checked at `0x460C0C`).

Window construction path (CONFIRMED):

```
docCreate (0x401000)                      [window instance table: dokuInstTable 0x45F048, 19 entries]
  └─ windowCreateFromBuiltIn (0x408ED0)   (objSize, name4cc, instTable, instCount, param4, parent)
       └─ lookupBuiltInRec (VWIN, name4cc, &size)
            └─ vuuPayloadParse (0x408B60)
                 └─ widgetInstantiate (0x408750)   [per child record, recursive]
```

All six window callers confirmed: `docCreate` ("doku", obj 0x1C0),
`FUN_00401E30` ("prvw", 0xA0), `FUN_00407AD0` ("emik", 0x5C),
`FUN_00405B00` ("efik", 0x54), `FUN_00404EC0` ("esik", 0x4C),
`FUN_00406F40` ("epxm", 0x78).

`widgetAllocInit` (`0x408670`, renamed) is the **window-object** allocator:
zeroed alloc of the object size (0x28 minimum), `scaleQuad` on the 4 geometry
values, `FUN_0040BFA0(obj, geom, class4cc, param4, name4cc)` → `obj+0x04`
(class object — for windows this is the **WIND** class `0x466188`, held at
`0x466194`… direct reference from `0x408705`), `FUN_0040AE70(classObj,
&PTR_labelPaint_0046624C)` (default paint binding), magic `0x5655d881` at
`obj+0x00`, temp parent at `obj+0x08`.

## 3. The widget descriptor — `widgetDesc` (40 B, CONFIRMED via `widgetInstantiate` `0x408750`)

Applied at the six doku records (`dokuVwinDesc 0x4605D8`, `dokuKnt1Desc
0x46062C`, `dokuMenuDesc 0x460660`, `dokuSeprDesc 0x460694`, `dokuInfoDesc
0x4606BC`, `dokuKlblDesc 0x4606F0`).

| Offset | Size | Meaning |
|---|---|---|
| +0x00 | 4 | **class** FourCC, ASCII (matched via `widgetClassLookup(bswap(...))`) |
| +0x04 | 2 | x, u16BE (i16) |
| +0x06 | 2 | y, u16BE |
| +0x08 | 2 | w, u16BE |
| +0x0A | 2 | h, u16BE |
| +0x0C | 4 | **instance** FourCC, ASCII (lowercase) → `widget+0x2C`; matched against the window's instance table |
| +0x10 | 4 | flags, u32BE → `widget+0x30` |
| +0x14 | 4 | **payload size**, u32BE — bytes following the fixed 40-byte header, before the children (0 = none; VWIN = 0x2C = 44 = the window-own block; KNTR = 12 = all-zero reserved in built-ins) |
| +0x18 | 4 | f18 (0 in all built-ins; open) |
| +0x1C | 4 | f1c (0 in all built-ins; open) |
| +0x20 | 2 | mode, **u16BE** (LE-loaded then byte-swapped in code) — bit `0x04` → post-init call `FUN_00409850(widget)`; `(mode & 0x18) | 1` → `widget+0x34` (verified: `MOV word [EAX+0x34], DX` after `AND 0x18; OR 1`) |
| +0x22 | 1 | b22 → 4th arg of `classInit` (verified `MOVZX … [EAX+0x22]`) |
| +0x23 | 1 | b23 → `widget+0x37` (verified `MOVZX … [EAX+0x23]`) |
| +0x24 | 2 | pad (0) |
| +0x26 | 2 | **childCount**, **u16BE** (LE-loaded then byte-swapped; verified against the 8 KNTR children / 1 VWIN child in raw data) |
| +0x27 | 1 | pad (0) |

After the 40-byte fixed part comes the payload (if `size` > 0 — e.g. the VWIN
record's 44-byte window-own block; labels carry their text pstr), then the
child records. `widgetInstantiate` consumes the record: looks up the class,
allocates `max(classObj->size, 0x38)` zeroed, fills the base widget (§5),
calls `classInit(child, desc, classCode, b22)` if `classObj+0x0C` is non-null
(note: `0x409BD0` — used by VUU!/LSTS/CLST — is a single `RET` no-op),
post-init if `mode & 4`, advances by `round4(40 + size)`, recurses
`childCount` times (loop bound verified: `childCount-1` with `JC` skip at 0).

**Instance registration** (CONFIRMED): the window carries an instance table
(8-byte entries `{u32 name (LE-stored), u16 slotByteOffset, u16 0}`); after
instantiation, if `widget+0x2C` equals a table name, the widget pointer is
stored into `slotArray[slotOffset]` — this is how e.g. the editor code
reaches the `scal` menu button or the `naam` name text field at runtime.
Tables: `dokuInstTable` 0x45F048 (19), `prvwInstTable` 0x45F57C (29),
`epxmInstTable` 0x465A9C (18), `emikInstTable` 0x465FB4 (9),
`efikInstTable` 0x46440C (8), `esikInstTable` 0x4640C4 (6). doku names:
`menu info klrs jmis snks kifp kpim naam srev ktrr dsek krea idom scal klrl
lmij lnik kifb kiml`.

## 4. FourCC byte-order convention (CONFIRMED, three representations)

A FourCC appears in **three distinct representations** — never conflate them:

| Representation | `TIKB` example | Where |
|---|---|---|
| **Memory-ASCII** (raw bytes = spelling) | `54 49 4B 42` | descriptor `class4cc` @+0x00; `%REZ` type/instance; instance names |
| **Code constant** (BE reading of the spelling) | `0x54494B42` | `PUSH`-ed arguments, e.g. `VWIN` → `0x5657494E` @ `0x408EDD`; `MENU` → `0x4D454E55` @ `0x4124A1` |
| **Class-tag storage** (the code constant stored as u32LE ⇒ *byte-reversed spelling in memory*) | `42 4B 49 54` = "BKIT" | class object tag @+0x00 (§6) |

- `widgetInstantiate` passes `bswap(desc->class4cc)` → converts memory-ASCII
  to the code constant.
- `builtinRecCmp` passes `bswap(rec+0)` / `bswap(rec+4)` → same conversion.
- `widgetClassLookup` compares the code constant **directly** (no bswap)
  against the tag word (which is already the constant stored LE).

Fast-path comparison constants in `widgetClassLookup` (`0x409150`), decoded
from the subtract-chain: `BUTN`→`0x4255544E`, `HOLD`→`0x484F4C44`,
`KLBL`→`0x4B4C424C`, `KNTR`→`0x4B4E5452`, `LABL`→`0x4C41424C`,
`TXTS`→`0x54585453`, `VUU!`→`0x56555521` — all BE readings of the straight
spellings. **CONFIRMED.**

## 5. Widget object base — `widgetBase` (56 B minimum, CONFIRMED via `widgetInstantiate`)

Applied as structure `widgetBase` (56 B):

| Offset | Size | Meaning |
|---|---|---|
| +0x00 | 4 | magic `0x5655d881` |
| +0x04 | 4 | class object pointer |
| +0x08 | 4 | parent widget pointer (set after attach) |
| +0x0C | 4 | u32 slot holding **i16 x** (raw, from descriptor) |
| +0x10 | 4 | u32 slot holding **i16 y** |
| +0x14 | 4 | u32 slot holding **i16 w** |
| +0x18 | 4 | u32 slot holding **i16 h** |
| +0x1C | 4 | u32 slot holding **i16 scaled x** (`scaleQuad`) |
| +0x20 | 4 | u32 slot holding **i16 scaled y** |
| +0x24 | 4 | u32 slot holding **i16 scaled w** |
| +0x28 | 4 | u32 slot holding **i16 scaled h** |
| +0x2C | 4 | **instance** FourCC (code constant stored; ASCII when read as the constant) |
| +0x30 | 4 | flags |
| +0x34 | 2 | mode = `(descMode & 0x18) | 1` |
| +0x36 | 1 | pad |
| +0x37 | 1 | descriptor b23 |

> **S1 corrections (to be propagated):** (1) S1's "u16 state @+0x0D" was a
> misread — `+0x0C..+0x2B` are the geometry slots; (2) S1's "button rect
> @+0x2C..+0x38" — in the *base* widget `+0x2C/+0x30/+0x34` are
> instance/flags/mode; the BUTN class object size is only 0x40, so S1's
> ≥ 0xC4B button object is a different (editor-side) object. Both to be
> re-audited in Batch C1.

## 6. Class objects — 21 classes (tags + sizes CONFIRMED by data; registration by code)

Class object layout (`widgetClassObj`, 144 B applied; field meanings beyond
the listed ones **unverified**):

| Offset | Meaning |
|---|---|
| +0x00 | **tag** = code constant stored u32LE (memory shows the *reversed* spelling) |
| +0x04 | zero |
| +0x08 | instance size (u32LE; minimum widget allocation) |
| +0x0C | `initFn` (`(child, desc, classCode, b22)`); NULL = no init |
| +0x14 | child-count method |
| +0x5C | state-notify (S1-confirmed) |
| +0x88 | `attachFn` (`(parent, child)`); must exist when a parent is given (else `hError 0x10002`) |

All 21 catalogued class objects (memory tag = reversed canonical):

| VA | Memory tag | Canonical | Size | initFn | Source |
|---|---|---|---|---|---|
| `0x4660C4` | `!UUV` | `VUU!` ("view") | 0x38 | `0x409BD0` | fast path |
| `0x466188` | `DNIW` | `WIND` (window) | 0x28 | `0x0` (none) | direct ref `0x408705` |
| `0x466690` | `RTNK` | `KNTR` (container) | 0x70 | — | fast path |
| `0x466C80` | `STXT` | `TXTS` (text) | 0x5C | — | fast path |
| `0x466D44` | `STSL` | `LSTS` (list) | 0x4C | `0x409BD0` (no-op) | ref `0x420C56`; ctor `lstsWidgetCtor` |
| `0x466E08` | `TSLC` | `CLST` (column list) | 0x54 | `0x409BD0` (no-op) | ref `0x421886`; ctor `clstWidgetCtor` |
| `0x466ECC` | `SGMI` | `IMGS` (image) | 0x64 | — | registered |
| `0x4674A0` | `NTUB` | `BUTN` (button) | 0x40 | `0x4352C0` | fast path |
| `0x467564` | `LBLK` | `KLBL` (klabel) | 0x48 | — | fast path |
| `0x467628` | `LBAL` | `LABL` (label) | 0x4C | — | fast path |
| `0x4676EC` | `!XOB` | `BOX!` (box) | 0x44 | `0x435FF0` | registered |
| `0x4677B0` | `RPES` | `SEPR` (separator) | 0x38 | — | registered |
| `0x467874` | `NMPB` | `BPMN` (menu button) | 0x40 | — | registered |
| `0x467938` | `TBKI` | `IKBT` (icon button) | 0x50 | — | registered |
| `0x4679FC` | `RLOK` | `KOLR` (color; K=COLR) | 0x44 | — | registered |
| `0x467B84` | `SGRP` | `PRGS` (progress) | 0x48 | — | registered |
| `0x467C48` | `RDLS` | `SLDR` (slider) | 0x44 | — | registered |
| `0x468188` | `DLOH` | `HOLD` (holder) | 0x40 | — | fast path |
| `0x46824C` | `RABM` | `MBAR` (menu bar) | 0x40 | — | registered |
| `0x468310` | `NOKI` | `IKON` (icon) | 0x78 | — | registered |

**Corrections to A1 names (applied in Ghidra):** `classRolr @0x4679FC` →
**`classKolr`** (memory tag `RLOK` = reversed `KOLR`; descriptors spell it
`KOLR`, always adjacent to "Color:" labels — it is the color-chooser
widget); `classRabl @0x46824C` → **`classMbar`** (memory tag `RABM` =
reversed `MBAR`; descriptors spell it `MBAR`, instance `mbar`). Register
thunks renamed to match: `classRegMbar @0x43CD30`, `classRegKolr @0x437220`
(both verified to push the object pointer and call `widgetClassRegister
0x409100`). `SLDR` was **missing** from A1's 18 — it is the 11th registered
class (the slider; descriptors use it 10× in the prvw window).

Registration: `widgetClassRegister` (`0x409100`) searches
(`0x440B70`) then inserts (`0x440790`) the object pointer into the dynamic
table `[gClassTblPtr 0x466B58] / [gClassCount 0x466B5C]`; called at startup
by 11 `classReg*` thunks (callers include `constructApp 0x403D30`).
`LSTS`/`CLST` are *not* in the registered set — they are referenced directly
(`0x420C56`, `0x421886`), like `WIND`. **RESOLVED (A3, 2026-11-20):** both
are LIST widget classes — `LSTS` = single-column list, `CLST` = multi-column
list ("column list"); full consumer analysis in doc 18. **The earlier
D-section association is DISPROVEN**: `.hap` files frame sections by header
offset fields (corpus-verified — v1/v2 carry no FourCC section tags, only the
`%HAP`/`%IKN`/`%MSI` magics), and D-section colors flow through
`gStyleDColors`/`styleColorGet` (S1) with no code path to the CLST class. The
only other "TSLC" string in the binary is inside the embedded-blob assembly
table @0x466DD4 (doc 13 §3) — an unrelated mechanism.

### 6.1 Class-object method-table structure (verified by cross-class comparison)

Class objects are **method tables** (virtual-table style, but NOT C++ vtables:
no function-pointer-to-interface indirection — each slot is a concrete
function, and dispatch sites load the slot and call it directly). `VUU!`
(`0x4660C4`) is the **base class** (slots from the `0x409Bxx–0x409Dxx`
generic-method cluster); each other class overrides individual slots and keeps
the base methods elsewhere.

Verified slot roles (evidence from call sites):

| Slot | Role | Evidence |
|---|---|---|
| +0x00 | tag (constant stored LE) | `widgetClassLookup` compare |
| +0x08 | instance size | `widgetInstantiate` alloc |
| +0x0C | `initFn` | called by `widgetInstantiate` `(widget, desc, classCode, b22)`; **`0x409BD0` is a single `RET` — a no-op placeholder** used by VUU!/LSTS/CLST (those are initialized by their direct constructors / payload parsers instead) |
| +0x10 | **teardown/cleanup method** | CLST's (0x4218A0) frees widget+0x3C via `listModelDtor` (magic check 0x8521B2D1), frees the view at +0x38 (0x447670), destroys +0x4C (0x44CAF0) |
| +0x14 | always NULL in all 21 classes (reserved) | data |
| +0x18 | hit-test / cursor-column by x | 0x421130 (LSTS/CLST): view+model ops on x; reads widget+0x40 (CLST-only field; zero-tolerant for LSTS) |
| +0x5C | state-notify | S1; LSTS/CLST override 0x4210D0: view flags from state bits 0x12/0x4, model selection from 0x14 |
| +0x88 | attachFn | `widgetInstantiate` parent attach |

`LSTS` and `CLST` share **19 of 21** non-null slots (identical function
addresses) — differing only in tag, size, and +0x10 (teardown 0x421090 vs
0x4218A0). Their shared +0x18..+0x34 override block (0x421130, 0x41F820…)
is the list-specific method set; +0x38/+0x58/+0x60 remain base methods
(0x409D40/0x409DB0/0x409DF0).

Canonical-name semantics (user-supplied, PROBABLE): `VWIN` = view window,
`TIKB` = tick button, `%VUU` = "view", `KNTR` = (K)container, `KOLR` =
(C→K)color; the developer "was eccentric with his naming, liked to switch C
for K".

## 7. Geometry scaling — `scaleQuad` (`0x429C70`) and the `scal` menu (CONFIRMED)

`scaleQuad(dst, src)`: for 4 i16 values, `dst[i] = (int)(src[i] *
gScaleNum) / gScaleDen` (globals from S1). Called (a) in
`widgetInstantiate` on every widget's geometry (raw → scaled slots
`+0x1C..+0x2B`), (b) in `widgetAllocInit` on window geometry, (c) for the
`%VUU` window-own 4×u16 block when non-zero. **This is what the `scal`
menu (instance of BPMN in the doku window; content = the `%MNU` record
`(MENU, scal)`) controls** — the editor's UI-scale factor. Field-layout
confidence: CONFIRMED. The *semantic* role of `gScaleNum/gScaleDen` as
"UI zoom" is PROBABLE (consistent with the Scale: menu and scaled layout of
all built-in windows).

## 8. `%MNU` menu payloads (offsets CONFIRMED via `menuPayloadParse` `0x412060`; field semantics open)

| Offset | Size | Meaning |
|---|---|---|
| +0x00 | 4 | `%MNU` |
| +0x04 | 2 | u16BE version = 1 |
| +0x06 | 1 | name length |
| +0x07 | 1 | b7 |
| — | — | header size = `round4(nameLen + b7 + 0x2B)` |
| +0x1C | 4 | u32BE style → 3rd arg of the menu ctor `FUN_0040FB90` |
| +0x20 | 4 | u32BE → `menuObj+0x5C` |
| +0x24 | 4 | u32BE item count (capped 0x400) |
| +0x28 | … | pstr menu name (len = nameLen) |
| … | — | **items[]**, each ≥ 0x38 B: `+0x00 u32BE type`, `+0x04 u32BE id`, `+0x08 u16BE → +0x0C`, `+0x0C u32BE → +0x10`, `+0x18 u16BE → +0x14`, `+0x21 byte → +0x16`, `+0x22 byte → +0x17`, `+0x34 byte titleLen`, `+0x38 pstr title`, then pstr icon (len byte at item+0x55); item size = `round4(b37 + b36 + iconLen + 0x3B + titleLen)` |

Items are appended to `menuObj+0x0C` via `0x440790`; post-processing
`FUN_00423210`, `FUN_0040FCC0`. The `scal` menu contains "Scale:" items with
u16 percentage values (visible in payload at `0x4602A8+`). **The exact
meaning of item fields 0x00/0x04/0x08/0x0C is HYPOTHESIS** (type selector /
command id / state / arg) — needs a menu-item activation trace (Batch B2).

## 9. doku window tree (verified, partial — 6 records mapped of 19+ instances)

```
VWIN doku  (380×400, obj 0x1C0, 8 children)
└─ KNTR  (380×400, classCode 0, 8 children, mode 0x18)
   ├─ BPMN  inst "menu"  (5,4 175×24)     ← menu bar (content via (MENU, exam)? — open)
   ├─ SEPR  (2,28 379×32, 4 children)     ← tab-page container (separator class hosts children)
   │  └─ KNTR  inst "info" (0,30 380×400, 3 children)
   │     ├─ KLBL  "Name:"  (10,15 100×31, payload pstr "Name:")
   │     ├─ TXTS  inst "naam" (10,65 30×36)
   │     └─ …(1 more)
   ├─ KNTR  inst "klrs" … (page 2)
   ├─ KNTR  inst "jmis" … (page 3)
   ├─ KNTR  inst "snks" … (page 4)
   ├─ KNTR  inst "kifp" … (page 5, file icons)
   ├─ KNTR  inst "kpim" … (page 6, mouse icons)
   └─ … (2 more of 8; pages continue with "srev"=preview, …)
```

The 8 KNTR children = the **8 tab pages** of the main window (Info, Colors
"klrs", "jmis", Sounds "snks", File Icons "kifp", Mouse Icons "kpim",
"Preview" "srev", …) — each a full-page container with its own controls.
The instance names in `dokuInstTable` (19) are the widgets the *editor code*
reaches by name (tabs + key controls like `naam`, `scal`, `krea`, `idom`).
Tab-page mapping by name semantics is **PROBABLE** (names follow the C→K
eccentricity: `klrs`≈"clrs", `snks`≈"snds"?); the *structure* (KNTR pages
under the SEPR) is CONFIRMED from the record bytes.

## 10. Lowercase 4cc part-name tables (D/E-role related — deferred to E5/D1)

Two name→u32LE map tables found in `.data` (stride 8: `{4cc name, u32 value}`):

- `0x45F0C0…` (near `dokuInstTable`): `klrl→0x7C, ljmp→0x80, lnki→0x84,
  kifl→0x88, kiml→0x8C` — then the 11 tab-name pstrs (`0x45F0E0`).
- `0x45F61C…`: `shbs→0x7C, ihbs→0x80, thbs→0x84, dvbs→0x88, svbs→0x8C,
  ivbs→0x90, tvbs→0x94, tirt→0x98, mirt→0x9C` — **scrollbar/track part
  names** (s=scrollbar, h/v, i/t/m variants; "tirt"/"mirt" = track
  tick/marker?) — these line up with the S1 finding that C-section flags
  `0x7C..0x81` are encoding selectors. **PROBABLE:** part name → style-slot
  index map. Consumer-side trace deferred to Batch E (style/ink records).

## 11. String vs FourCC re-audit (A2a — complete)

Full printable-run enumeration of `.rdata`+`.data` (6,477 runs ≥3 chars):
**358** are 4-char alphabetic runs. Classification:

- **Class spellings (straight, in descriptors):** all 19 descriptor-spelling
  classes occur (`BUTN×17, KNTR×19, KLBL×45, TXTS×16, HOLD×15, BPMN×13,
  LABL×11, SLDR×10, TIKB×10, SEPR×6, VWIN×6, IMGS×4, IKBT×2, PRGS×1, IKON×1,
  KOLR×3, MBAR×1, …`).
- **Class tags (reversed, in class objects):** exactly 17 alphabetic tags
  found (`BKIT DLOH DNIW LBAL LBLK NMPB NOKI RABM RDLS RLOK RPES RTNK SGMI
  SGRP STSL STXT TBKI TSLC`) — the remaining 4 class tags contain `!`
  (`!UUV` = VUU!, `!XOB` = BOX!) and were filtered by the alphabetic scan.
  **21 = 21: every class object accounted for, no orphans.**
- **Instance names (lowercase):** `doku efik emik epxm esik prvw exam fsit
  scal menu info klrs jmis snks kifp kpim naam srev ktrr dsek krea idom klrl
  lmij lnik kifb kiml fnam anam ikns imjs pfik pmik mbar umen trim mnut tmnu
  lscl txtk trnk trns tsty tssc tsec tpos bpos ikon imgS imgM sbht sbhi sbvd
  sbvs sbvt sbvi list pbar pbsl dele invk` — all located **inside
  descriptors** (at +0x0C) or in the §10 part tables.
- **Genuine 4-char strings** (not FourCC): `Exit Save Copy Find Mute Home
  Help Menu Stop Note News Chat Text Wait Icon Name Type None Only Open
  Undo Plus` etc. — UI labels inside pstr/C-string pools; unchanged.
- **False positives** (4-char alphabetic inside binary data, not identifiers):
  `wwva eDDQ eDDE vUwx wvgw wwwq wwww wwwz DJUZ JwzZ KRLK lTrP TXET ATAD
  QNaN SNaN` etc. — font glyphs, palette/floating-point tables, Win32
  `WNDCLASS`-like descriptors (`TXET @0x47A85C` with " txt" class name,
  `lTrP @0x47A62C` with " trp", `ATAD @0x47B154` with " pah", `KRLK
  @0x479678` — native-control registrations, Batch E/F material).

**Result for the docs:** every 4cc that doc 02 listed (or that appeared in
earlier string inventories) as a "string" and is actually a class/instance
FourCC is reclassified in §13 below; the genuine strings are preserved as-is.
No C-string boundaries were altered.

## 12. Ghidra enrichment applied this session (all read-back verified)

- **Functions (21 unique; 24 rename ops = 21 new + 3 A1-name corrections):**
  `widgetClassLookup widgetClassRegister widgetInstantiate vuuPayloadParse
  windowCreateFromBuiltIn menuCreateFromBuiltIn lookupBuiltInRecSoft
  scaleQuad menuPayloadParse widgetAllocInit classRegSepr classRegBpmn
  classRegBox classRegIkbt classRegTikb classRegPrgs classRegSldr (was
  classRegRldr) classRegKolr (was classRegRolr) classRegMbar (was
  classRegRabl) classRegIkon classRegImgs` (all 11 register thunks verified:
  each pushes its class-object pointer and calls `widgetClassRegister`)
- **Data (31 unique; 34 ops = 28 new + 6 corrections/additions):**
  `rezBuiltinHeader rezBuiltinRecords gClassTblPtr gClassCount dokuInstTable
  prvwInstTable emikInstTable efikInstTable esikInstTable epxmInstTable
  classVuu classWind classKntr classLsts classClst classImgs classButn
  classKlbl classLabl classBox classSepr classMbar classKolr classSldr
  classPrgs classIkon classBpmn classIkbt classTikb classHold` (A2
  corrections/renames: Rolr→Kolr, Rabl→Mbar, Rldr→Sldr; added Wind/Stsl/Tslc)
- **Structures (5, all size-verified):** `rezHeader` 24 B, `rezRec` 20 B,
  `widgetDesc` 40 B, `widgetBase` 56 B, `widgetClassObj` 144 B.
- **Applications (29):** `rezHeader` @0x45F830; `rezRec[9]` @0x45F848;
  `widgetDesc` ×6 (doku records); `widgetClassObj` ×21 (all class objects,
  names preserved).

## 13. Corrections to prior documents (to propagate)

1. `02-strings-and-fourcc.md` §1.4: expand the FourCC table to the full
   class/instance inventory; add the three-representation convention (§4);
   reclassify 4cc items previously listed as strings.
2. S1 "u16 state @+0x0D" and "button rect @+0x2C..+0x38": superseded by §5
   (re-audit in C1).
3. A1 `classRolr`/`classRabl`: renamed `classKolr`/`classMbar` (§6).
4. "18 widget classes": actual count **21** (adds WIND, LSTS, CLST; SLDR
   was already catalogued as "RLDR" — corrected to SLDR here).
5. `0x4625C0–0x462700` "widget class descriptor pool" (S1): actually **prvw
   window child records** (TIKB/IKBT/IKON/KNTR/SEPR/BPMN widgets of the live
   preview), not a class pool.

## 14. Open items (carried to later S2 batches)

- **B2:** paint/dispatch side — `0x40C9A0/0x40CAC0/0x40CB10/0x40CC30` window
  methods, `FUN_0040BFA0` ctor, `FUN_0040AE70` default paint, the template
  walker that paints children (S1's WM_PAINT → per-child call site).
- **B2/E:** `%MNU` item field semantics (type/id/state/arg) via menu
  activation; `(MENU, exam)` vs the doku "menu" BPMN's actual content
  record.
- **C1:** per-function parameter/local audit gate for all renamed functions;
  widgetStateSet re-audit against the corrected base layout.
- **E/G:** §10 part tables → D-role indices. (LSTS/CLST consumer analysis
  RESOLVED in A3 — list widget classes, not D-section; see doc 18.)
- **F:** built-in 8×8 font block at `0x4709xx–0x478xxx` (`wvgw` glyphs etc.).
- **Remaining descriptors:** full doku tree (12+ more records), prvw tree
  (29 instances), epxm tree (18), %MNU item decode for all 3 menus.
- **rezHeader +0x0C/+0x10:** purpose open (both zero; not read in this
  binary). `+0x08 totalSpanBE` value exact (0x3C98) but writer-side semantics
  unverified (no writer in this binary — registry is static).