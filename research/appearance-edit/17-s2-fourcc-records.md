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

## 8. `%MNU` menu payloads (B2-remainder — COMPLETE; every offset disassembly-verified, corpus walk EXACT)

**SUPERSEDES** the preliminary §8 table (2026-11-21). The preliminary text
misidentified item `+0x00`/`+0x04` (they are `id`/`value2`, both 0 in the
corpus), located the icon length at item+0x55 (wrong: icon is a trailing
pstr inside the blob, and in the file `iconLen` is a plain byte at +0x35),
and read the `scal` titles as "u16 percentage values" (wrong: `value2`
carries opaque app command codes; the titles are fraction-glyph + scale
strings). All field offsets below were re-derived from the raw disassembly
of `menuPayloadParse` (0x412060, body blocks 0x4121F0–0x4123F1) because the
decompiler's `uint*` typing of the item pointer misdisplays byte offsets.

### 8.1 Header (fixed 0x28 B when nameLen=0; CONFIRMED)

```
+0x00  4B   magic "%MNU" (25 4D 4E 55; code checks bswap32(load) == 0x254D4E55)
+0x04  2B   u16BE version (must be 1)
+0x06  1B   nameLen          (byte count of name pstr data)
+0x07  1B   b7               (reserved; 0 in corpus)
+0x08  16B  reserved (zero in corpus)
+0x1C  4B   u32BE style      (menuObjectCtor 3rd arg: 1 = popup menu, 2 = selection list)
+0x20  4B   u32BE field5c    (menuObj+0x5C? no — passed to ctor arg slot; 0xFFFFFFFF in corpus)
+0x24  4B   u32BE itemCount  (clamped to 0x400 before array reserve)
+0x28       name pstr when nameLen > 0 (length byte + nameLen bytes)
header size = (b7 + nameLen + 0x2B) & ~3   ; all 3 corpus menus: 0x28 (nameLen = b7 = 0)
```

When nameLen = 0 the name pstr is absent and the first item's `id` begins at
+0x28 (the item's first byte is simply 0x00 in the corpus). Note: the pstr
length byte at +0x28 (0x00 when empty) coincidentally occupies item 0's id
high byte — no practical effect since all ids are 0.

### 8.2 Item record (disassembly-verified; size formula corpus-verified)

```
size = (b36 + b37 + iconLen + tlen + 0x3B) & ~3

+0x00  4B   u32BE id          (primary command id; 0 in entire corpus)
+0x04  4B   u32BE value2      (secondary id / command payload; 0 except scal menu)
+0x08  1B   pad (parser reads u16LE @+0x08 but uses only high byte)
+0x09  1B   flagsHi           (<<16: top byte of the 24-bit item flags)
+0x0C  4B   u32BE iconIndex   (blob+0x10 → cell+0x14 → row painter; 0 except icon items)
+0x10  8B   not read by parser (zero in corpus; 00 20 58 00 pattern in one exam item)
+0x18  2B   u16BE accel       (accelerator; exam item 1 = 0x0058 'X')
+0x1A  2B   u16BE flagsLo     (low 16 bits of the 24-bit flags)
+0x1C  16B  not read by parser (zero in corpus except one 0x20/0x58 pair)
+0x21  1B   b21               (blob+0x16; 0 in corpus)
+0x22  1B   b22               (low byte of u16LE @+0x22 → blob+0x17; 0 in corpus)
+0x24  8B   not read by parser
+0x34  1B   tlen              (title byte count — AUTHORITATIVE, pstr rule)
+0x35  1B   iconLen           (icon byte count; 0 in corpus — icons are INDEXED, not embedded)
+0x36  1B   b36               (0 in corpus; semantics unknown)
+0x37  1B   b37               (0 in corpus; semantics unknown)
+0x38       title [tlen]      (raw bytes, NUL not required; lengths authoritative)
+0x38+tlen  icon [iconLen]    (raw bytes; 0 in corpus)
```

flags24 = (flagsHi << 16) | flagsLo. Observed values and their runtime
consumers (`menuRowClickDispatch` 0x40FAA0, `menuInsertSeparatorAt` 0x411410):

| flags24 | meaning (CONFIRMED by dispatch code) |
|---|---|
| 0x00000 | normal selectable item |
| 0x00200 | (exam item 1 only; low-bit semantics UNKNOWN) |
| 0x20000 | tickable — click toggles checked state (`menuRowToggle` 0x411880) |
| 0x40000 | disabled — no dispatch, dimmed rendering |
| 0x50000 | separator (static 0x10000 + disabled 0x40000; matches runtime separator builder which hard-codes 0x50000) |
| 0x80000 | static label — never dispatches (blocks both toggle and select) |
| 0x100000 | has icon — icon drawn from iconIndex |
| 0x140000 | icon + disabled |

The 0x10000 bit ("static") only appears in the corpus combined with
0x40000 (separators); a lone 0x10000 is not observed.

### 8.3 Runtime item blob (CONFIRMED via `menuInsertItem` 0x411120 + parse disassembly)

```
blob = memAllocZeroed(0x1A + tlen + iconLen)
+0x00  4B   pad (zero)
+0x04  4B   id
+0x08  4B   value2
+0x0C  4B   flags24 & 0xFFFFFF
+0x10  4B   iconIndex
+0x14  2B   accel
+0x16  1B   b21
+0x17  1B   b23 (low byte of file word @+0x22)
+0x18  1B   titleLen  (LEADING length byte — Haxial pstr variant)
+0x19       title [tlen]
+0x19+tlen  1B iconLen (leading length byte)
+0x1A+tlen  icon [iconLen]
```

Blobs are stored in `menuObj+0x0C` (ptrArray), one 16-byte row each in the
`listModel` (rowSize byte at menuObj+0x60; 0x10 in the menu path). Separator
blobs are 0x1A B with flags24 = 0x50000 and no title (hard-coded in
`menuInsertSeparatorAt`, matching file items with flagsHi = 0x05).

### 8.4 Menu object `menuObj` (0xA4 B; CONFIRMED via destructor, parse, insert, select/toggle, callback code)

```
+0x00  4B   magic 0x51BD8891
+0x04  4B   surfaceObj (hapTextObj* of the popup surface; NULL until shown;
                       destroyed by 0x40C270; menuItemDtor invalidates its rows)
+0x08  4B   listModel (listModelCtor 0x422EB0; magic 0x8521B2D1; 16 B rows)
+0x0C  4B   itemArray (blob*; reserved to count via ptrArrayReserve 0x4407E0)
+0x10  4B   itemCnt
+0x18  4B   cmdHandler (set by menuCreateFromBuiltIn; = bpmnMenuCmdHandler 0x436160 for BPMN menus)
+0x1C  4B   cmdCtx (owner widget for BPMN menus)
+0x20  4B   selCallback (code*; set by menuSetSelectionCallback 0x411E80;
                       BPMN menus register bpmnSelectionNotify 0x4361D0 with the widget as ctx)
+0x24  4B   selCallbackCtx
+0x3C  4B   cursorLo (u32, -1; insert-adjusted; second consumer not yet traced)
+0x50  2B   style (u16, from header +0x1C; bit 1 (value 2) = selection-list mode —
                       menuRowSelect invokes selCallback only when style & 2)
+0x58  4B   namePstr (header name when nameLen > 0; memFree'd in menuDestroy)
+0x5C  4B   selCursor (u32; INITIALIZED FROM HEADER field5c — corpus 0xFFFFFFFF = none;
                       written by menuRowSelect, insert-adjusted)
+0x60  1B   rowSize (0x10)
+0x61  1B   f61 (set 1 after parse/insert; purpose unknown)
+0x68  4B   menu2 (second/linked menu — menuDestroy 0x40FCC0 recurses here;
             no file-level nesting: %MNU carries one menu per record)
+0x6C  4B   cursorHi (u32, -1; insert-adjusted; role vs selCursor unknown)
+0x80  4B   subObj (freed by 0x41C600 in menuDestroy; popup window object? PROBABLE)
```

Note on header `field5c` (+0x20): the parse stores `bswap32(header+0x20)` into
menuObj+0x5C — so the header field IS the initial selection cursor (all corpus
menus use 0xFFFFFFFF = no initial selection). The §8.1 table's "field5c"
naming is kept for the on-disk field; its runtime identity is selCursor.

### 8.5 Corpus validation (tools/research/mnu_walk.py — EXACT, leftover = 0)

| menu | VA | size | style | items | inventory |
|---|---|---|---|---|---|
| exam | 0x45F900 | 0x218 | 1 | 7 | demo: First/Second Menu Item (accel 'X'), separator, Disabled, Item With Icon (iconIndex 0x0A), Disabled With Icon, Ticked |
| fsit | 0x45FB18 | 0x78C | 1 | 28 | MIME-type paths for the file-icon editor: alias/unattached, archive/, audio/{,mpeg,wav}, data{,/truncated}, executable/program, folder/{,audio,dropbox,images,uploads}, font/, image/{,gif,jpeg}, text/, video/{,mpeg}, volume/{,cart,cd,dvd,fdd,hd,net,ram} |
| scal | 0x4602A8 | 0x328 | 2 | 12 | scale options "½ 0.25" … "½ 3.00" (fraction glyphs 0xBC/0xBD/0xBE in cp1252; 0x98 byte for the remaining labels); value2 = opaque command codes 0x11..0xB4 |

All three menus walk byte-exact: 47 items total, correct counts, correct
titles, no overreads, zero trailing bytes. Structural validation ✓.
Semantic validation: field roles above are consumer-traced (CONFIRMED for
flags/id/value2/accel/iconIndex/title); b21/b23/b36/b37/the +0x10..+0x17 and
+0x1C..+0x33 item regions, `field5c`, `f61`, `cursorLo/Hi` and `menu2` roles
remain UNKNOWN/PROBABLE as marked.

### 8.6 BPMN → %MNU association (CONFIRMED; closes the C3 open question)

BPMN payload (12 B) = `{u32BE refA, u32BE refB, u32BE w2}`:
- `refA == 0` → `menuObjectCtor(bpmnMenuCmdHandler, widget, style = refB)` —
  empty runtime menu filled by application code.
- `refA != 0` → `menuCreateFromBuiltIn(handler, widget, refA)` — refA is the
  %REZ record **name** (4cc stored as code constant); loader is
  `lookupBuiltInRec(0x4D454E55 /*"MENU"*/, name, &size)` (disassembly-verified:
  compares rec+0 and rec+4 byte-swapped; returns size u32BE @+0x0C and
  absolute payload = offset u32BE @+0x10 + 0x45F830).

All 9 BPMN nodes in the six built-in windows (PE-verified from the file
bytes; the Ghidra hexdump tool produced corrupted reads for some addresses in
this session — the PE reader is authoritative):

| window | inst | refA | menu |
|---|---|---|---|
| doku | menu | 0 | empty (style 2) — File menu built by `docMenuBuild` 0x401350 (New/Open…/Import Colors…/Save/Save As…/Preview/About/Exit Appearance) |
| doku | scal | "scal" | built-in scal (scale selector) |
| efik | typm | "fsit" | built-in fsit (MIME-type picker for the file-icon tab) |
| emik | trnk, invk | 0 | empty (style 2) |
| epxm | trns, tsty | 0 | empty (style 2) |
| prvw | pmnu, umen, mnu2 | 0 | empty (style 2) |

**"exam" is referenced by nothing in this build** — no .text constant, no
BPMN payload, no data pointer (the two .rdata hits are the English words in
"for example: joe@example.com"). It is a developer sample menu (PROBABLE).
No %MNU record is written by this build's save path (the v2 writer emits no
M section — see 04 § directory slots).

### 8.7 Runtime menu lifecycle (CONFIRMED chain)

```
BPMN press (classBpmn+0x20 = bpmnEventPress 0x436670):
  event+6: 1→state|=0x40 (press), 2→|=0x80 (release), 3→|=0x100 (click)
  if state&0x10 (menu assigned) and state&6: open or close toggle
open  → bpmnMenuShow 0x4367A0: btn+0x36|=1, geom = btn+0x1C..+0x27,
         0x4098A0 callback computes (dx,dy), popupMenuShow 0x410C60(menu, event, rect)
close → bpmnMenuClose 0x436890: btn+0x36&=~1, popupMenuClose 0x410EB0(menu)
row click → listModel cell callback menuRowClickDispatch 0x40FAA0:
  event 1:  (flags & 0x20000) ? menuRowToggle (0x411880: flags^=0x20000)
                             : menuRowSelect  (0x411CF0: selCursor=row, prev-row resync)
            — both skipped for 0x80000 (static) / 0x40000 (disabled)
  event 7:  select (if not static/disabled/tickable)
selection → (style & 2, e.g. scal) menuRowSelect → menuSelCallbackInvoke 0x4110E0
  → selCallback(selCallbackCtx) = bpmnSelectionNotify 0x4361D0 →
  widgetRefresh 0x409660(widget, widget+0x1C geom); the app then reads
  menu->selCursor → item value2 (command code) and applies it
selection (style 1 popup) → cmdHandler (menu+0x18) = bpmnMenuCmdHandler 0x436160:
  bpmnMenuClose; copies 0x2C-byte message from the model row (id/value2/flags…);
  sets flag 0x1000; widgetMsgBubble 0x4097F0 → owner's class+0x9C message handler
item removal → menuItemDtor 0x40F990 → textObjInvalidateRect 0x40CDB0(surface, rowRect)
menuDestroy 0x40FCC0: recursive (menu2 @+0x68) → surface 0x40C270 → model
dtor → subObj 0x41C600 → name pstr → item array → free
```

MBAR (menu-bar widget) association: `mbarWidgetInit` 0x43CD50 builds a
0xC0 B sub-object (magic 0x455E0FD3) whose +0x38 holds a menuObj and +0x40 a
20-slot item pointer array; `mbarPaint` 0x43CDF0 → `mbarDrawTitles` 0x42EF60
renders the horizontal section-title bar (the "Information | Colors | Images…"
strip; titles come from the doc's section menu built at doc+0x78 by
docCreate/docMenuBuild). MBAR sub-callbacks 0x409660/0x4098A0 are registered
via 0x411E80 (same registration used by BPMN for 0x4361D0).

### 8.8 Ghidra enrichment (this batch — read-back verified)

- Structs (program-local): `mnuHeader` 40 B, `mnuItemRec` 56 B, `menuItemBlob`
  24 B fixed + pstr tails, `menuObj` 164 B, `mbarSubObj` 192 B; `widgetClassObj`
  extended 144 B → 180 B (msgHandler @+0x9C now named).
- Data applied: mnuHeader ×3 (exam_hdr/fsit_hdr/scal_hdr), mnuItemRec ×3 (item 0 of each).
- Renames: 33 functions (menuInsertItem, menuAddItemPstr, menuInsertSeparatorAt,
  menuAddSeparator, menuItemDtor, textObjInvalidateRect, menuItemCellRecord,
  menuRowCellState, menuRowClickDispatch, menuRowToggle, menuRowSelect,
  modelRowsInsert, modelRefreshRow, menuSelectHighlight, menuSelectClear,
  menuSetSelectionCallback, menuSelCallbackInvoke, mbarDrawTitles,
  mbarSubObjCtor, mbarWidgetInit, widgetMsgBubble, widgetRefresh,
  bpmnMenuCmdHandler, bpmnMenuShow, bpmnMenuClose, bpmnEventPress,
  bpmnSelectionNotify, popupMenuShow, popupMenuClose, ptrArrayReserve,
  ptrArrayAppend, ptrArrayInsert, menuDestroy).
- 9 prototypes, 15 function comments (menu subsystem).
- Inventories: `data/mnu-inventories.txt` + `.json` (walk EXACT).


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
- ~~**C1:** per-function parameter/local audit gate for all renamed
  functions; widgetStateSet re-audit against the corrected base layout.~~
  **PARTIALLY RESOLVED (2026-11-21, §16):** widgetStateSet re-audit done
  (state @+0x34); CLST/LSTS ctor params + list ownership + parent attach
  done; widgetBase rebuilt. Systematic sweep of the remaining ~150 renamed
  functions deferred (per-batch + V final sweep).
- **E/G:** §10 part tables → D-role indices. (LSTS/CLST consumer analysis
  RESOLVED in A3 — list widget classes, not D-section; see doc 18.)
- **F:** built-in 8×8 font block at `0x4709xx–0x478xxx` (`wvgw` glyphs etc.).
- **Remaining descriptors:** RESOLVED in C3 (§15) — all six trees walked
  exact; %MNU item decode for all 3 menus still open (B2/E).
- **rezHeader +0x0C/+0x10:** purpose open (both zero; not read in this
  binary). `+0x08 totalSpanBE` value exact (0x3C98) but writer-side semantics
  unverified (no writer in this binary — registry is static).
## 15. %VUU window trees — full reconstruction (C3 — COMPLETE)

All six built-in %VUU payloads were walked by `tools/research/vuu_walk.py`
against the on-disk EXE. **Every payload consumes its %REZ size EXACTLY and
every named instance matches its window instance table 1:1** (0 unmatched,
0 unused). Full tree: `data/vuu-trees.txt`.

| window | payload | size | records | named instances | geometry | window-own sz |
|---|---|---|---|---|---|---|
| doku | 0x4605D0 | 0x620 | 30 | 19/19 | 380×400 | 44 |
| efik | 0x460BF0 | 0x448 | 17 | 8/8 | 430×246 | 60 |
| emik | 0x461038 | 0x4B0 | 19 | 9/9 | 340×380 | 44 |
| epxm | 0x4614E8 | 0x908 | 42 | 18/18 | 690×342 | 44 |
| esik | 0x461DF0 | 0x3B0 | 15 | 6/6 | 430×246 | 56 |
| prvw | 0x4621A0 | 0x1328 | 86 | 29/29 | 360×340 | 64 |

(The %REZ pool also has a 4-byte pad between the `scal` MENU payload and the
`doku` VWIN payload: 0x4602A4..0x4602A8.)

### 15.1 `widgetInstantiate` (0x408750) — corrected full decode

Args: (parent, desc, **totalSubtreeBytes**, arg4, **windowObj**, instTable,
instCount, sizeOut). `totalSubtreeBytes` (arg3) must be ≥ 0x28; end =
desc + arg3; the payload (desc+0x14 bswapped) must fit:
desc+0x28+round4(payload) ≤ end.

Per record:
1. classObj = widgetClassLookup(bswap(desc+0)); NULL → hError(0x10017,0x56,0xA6).
2. widget = memAllocZeroed(max(classObj+0x08, 0x38)); `+0x00` = magic
   0x5655d881; `+0x04` = **classObj** (NOT desc); `+0x08` = parent.
3. Raw geometry u16BE desc+0x04..+0x0B → `+0x0C..+0x17` (i16);
   scaleQuad → `+0x1C..+0x27`.
4. `+0x2C` = bswap(desc+0x0C) **instance code**; `+0x30` = bswap(desc+0x10)
   flags; `+0x34` = (mode & 0x18) | 1 (mode = u16BE desc+0x20, swapped);
   `+0x37` = desc+0x23 (b23).
5. If parent: parent magic check (0x5655d881), then
   `parentClassObj = [parent+0x04]`; if `[parentClassObj+0x88]` →
   attachFn(parent, child) else hError(0x10002,0x56,0xBF); `child+0x08` = parent.
6. If `classObj+0x0C` (initFn) ≠ 0:
   **classInit(widget, payload = desc+0x28, payloadSize, b22 = desc+0x22)**.
7. If mode & 4: FUN_00409850(widget).
8. Children: childBase = desc+0x28+round4(payloadSize). **Gate:**
   `classObj+0x14` (childCountFn) is called with (widget); the loop runs only
   if it returns non-zero. KNTR's gate = `kntrHasChildren` (0x412860,
   2-instruction `return widget`). All other classes have NULL at +0x14 (so
   the A2/A3 claim "+0x14 always NULL" is corrected: KNTR has one). The loop
   then recurses widgetInstantiate `childCount` times (childCount = u16BE
   desc+0x26, swapped).
9. Instance registration: for each 8-byte table entry {instCode u32,
   slotOffset u32} — entry.instCode == widget+0x2C →
   **windowObj[slotOffset] = widget pointer**.
10. sizeOut = end − desc; returns the widget pointer.

### 15.2 KNTR (tab container) — payload and child model

- classObj @0x466690: size 0x70, initFn `kntrWidgetInit` 0x412780, teardown
  0x412810, childCountFn `kntrHasChildren` 0x412860; 17 non-NULL method
  slots (+0x18..+0x5C).
- `kntrWidgetInit(widget, payload, payloadSize, b22)`:
  `[widget+0x34] |= 0x20` (container bit); if payloadSize ≥ 0xC:
  widget+0x5C = bswap(payload+0 u32), +0x60 = bswap(payload+4 u32),
  +0x64 = swap16(payload+8 u16).
- **12-byte KNTR payload** = {u32BE A, u32BE B, u16BE C}. Observed: A=B=0
  always; C = 1 (root tab containers: doku root, prvw root) or 3 (tab pages:
  all 7 doku pages, all 8 prvw tabs). C semantics = **UNKNOWN** (values only;
  no discriminating code path read yet).
- KNTR is the only class that gets children from records; HOLD pages host
  runtime-built children (CLST lists — see A3) via builder code.

### 15.3 BPMN (bitmap/pull-down menu) — payload and menu model

- classObj @0x467874: size 0x40, initFn `bpmnWidgetInit` 0x436430, teardown
  0x436550, stateNotify 0x409BF0 (+0x5C), +0x60 = 0x4365E0.
- `bpmnWidgetInit(widget, payload, payloadSize, b22)`: if payloadSize < 0xC
  use a zeroed 12-byte local.
  - If `bswap(payload+0) ≠ 0`: **menuCreateFromBuiltIn** (0x412490):
    lookupBuiltInRec(**MENU** 0x4D454E55, ref, &size) → menuPayloadParse →
    menu object; then menu+0x18 = 0x436160 (**a function pointer** —
    `push ebp/mov ebp,esp` prologue at 0x436160), menu+0x1C = widget.
  - Else: **menuObjectCtor** (0x40FB90, renamed): memAllocZeroed(0xA4);
    menu+0x18 = 0x436160 (fn), +0x1C = widget, +0x50 = ref, +0x5C = −1,
    +0x6C = −1; if ref & 8 → variant size 0x12.
  - `widget+0x38` = menu; then CALL 0x411E80(0x4361D0, menu, widget)
    (0x4361D0 = a thunk function; 0x411E80 attaches item handling).
- **12-byte BPMN payload** = {u32BE menuRefA, u32BE menuRefB, u32 reserved}.
  Observed: doku "menu" = {0,0,2}; doku "scal" = (to verify); prvw
  pmnu/umen/mnu2 = {2,0,0}-style; mnu3/tmnu have sz=0 (→ empty local →
  empty inline menu). menuRef values that are non-zero and not a %MNU
  instance (exam/fsit/scal) hit the lookup-fail path — see open items.

### 15.4 Window-own block (VWIN payload, 44–64 B) — parser reads

`vuuPayloadParse` (0x408B60) validated: payload > 7; tag "%VUU" (u32BE at
+0); u16BE version 1 at +4; first record VWIN at +8; VWIN size ≥ 0x2C and
record fits; title pstr at **payload+0x5B** (block+0x2B) fits. Then:

| block offset | read | use |
|---|---|---|
| +0x00 | u32BE "options word" | → `windowCtor` (0x40BFA0) arg3 |
| +0x04 | u32BE | bswap → `FUN_0040CC30`(window, val) |
| +0x0C..+0x12 | 4×u16BE quad | if any ≠ 0: scaleQuad → `FUN_0040C9A0`(window, q0..q3) |
| +0x14 | u8 mode | 0 → `FUN_0040CAC0`(window, u32@+0x14); 2 → none; else `FUN_0040CB10`(window, byte) |
| +0x23.. | pstr (u8 len + bytes) | window name (default; caller may override via 8th arg) |

Observed values: options word = 0 (efik/esik/prvw), 0x1000010F (doku),
0x10000001 (emik), 0x10000009 (epxm); quad = (380,296,20000,20000) (doku),
(512,0,0,0) (efik/emik/epxm/prvw), (0,0,0,9)+stray (esik — its block has a
different layout, see below). Block sizes vary 44/56/60/64; beyond the
parser-read fields the content is builder-specific: esik puts a title pstr
at +0x13.., the size pair (430,246) at +0x28 and a trailing 0x0C at +0x3C;
efik/prvw carry a 2nd size pair at +0x08 (efik 1000×246 = max size) and the
title pstr at +0x23 (parser default spot). The "KNTR" ASCII at the tail of
efik/esik/prvw blocks = the sole child's class spelling (informational).

### 15.5 Window object construction (resolves S1 "window ctor" items)

`widgetAllocInit` (0x408670): obj = memAllocZeroed(max(size,0x28));
scaleQuad(geom) into local; `windowCtor` (0x40BFA0; S1's "FUN_0040BFA0
ctor") ← (geom, options word, arg4, name, obj); `[obj+0x0C]` = its result;
`windowDefaultPaintInstall` (0x40AE70; S1's "FUN_0040AE70 default-paint") ←
(obj+0x0C, **0x46624C** — a static data constant); `obj+0x00` = magic
0x5655d881; **`obj+0x04` = classWind (0x466188) always** — the "classCode"
is NOT a class lookup; all windows are WIND-class objects. (0x46624C content
and the four window methods 0x40C9A0/0x40CAC0/0x40CB10/0x40CC30 → Batch B.)

### 15.6 prvw (live preview) tree — summary

VWIN 360×340 → KNTR (11 children): MBAR "mbar" (0,0 360×20), BPMN "pmnu"
(main menu, 5,25 195×45), SEPR, then 8 tab pages (KNTR): **misc** (15:
KLBL+TXTS, HOLD "list" 210×170, PRGS "pbar", SLDR "pbsl" + disabled SLDR,
3×BUTN, SEPR, BPMN "umen", 2×TIKB, IKBT, IKON), **tiks** (14: 12×TIKB in
2 cols × 6 rows — enabled/disabled pairs; "trit", "trim" named; 2 KLBL
headers), **boxs** (5: SEPR + 3×BOX! + LABL), **slid** (8: 4 vertical +
4 horizontal SLDR, enabled/disabled pairs), **hsbs** (8: 4 HOLD
sbhd/sbhs/sbht/sbhi + 4 KLBL), **vsbs** (8: 4 KLBL + 4 HOLD sbvd/sbvs/
sbvt/sbvi), **btns** (14: 4×BUTN, 2×IKBT, BPMN "mnu2"/"mnu3", TXTS
"mnut"+anon, BPMN "tmnu"+anon, KLBL, **KOLR** color chooser 270×260),
**lscc** (1: HOLD "lscl" 350×270 — hosts the runtime CLST list, A3).
mode 0x1A = enabled pair, 0x0A = disabled pair (bit 0x10 of the 0x18 mask
clear). This is the skin-preview window shown in the screenshots (widgets
rendered in current-appearance, enabled+disabled side by side).

## 16. C1 — widget base re-audit, state-word correction, list-ctor decode (2026-11-21)

### 16.1 `widgetStateSet` (0x4093E0) — state word is @+0x34, NOT +0x0D

Disassembly re-audit (S1/doc 13 §3 recorded "u16 state @+0x0D" — **WRONG**):

```asm
CMP [widget+0x00], 0x5655D881        ; magic
MOVZX ECX, word [widget+0x34]        ; state = u16 @ +0x34
EDX = bits & mask
ECX = (state & ~mask) | (bits & mask)
if (ECX & 1) ECX &= ~1               ; bit 0 (0x01) can only be CLEARED here
if (!(ECX & 2)) ECX &= ~2            ; (no-op branch; bit 1 unconstrained)
if (ECX == state) return 0
word [widget+0x34] = ECX
class = [widget+0x04]                ; classObj  ✓ matches corrected layout
notify = [class+0x5C]                ; stateNotifyFn ✓
if (notify) notify(new, old, widget)
return 1
```

- The `+0x0D` recorded in S1 was an artifact of the same pointer-display
  misread that affected the B2 pass; the true state word is the `ushort`
  at **+0x34** (widgetBase.state), shared with the instantiation-time
  `(descMode & 0x18) | 1` value (§15.1) and the paint-visibility filter
  (kntrPaint checks child+0x34 & 0x08 — B2).
- **Bit 0 (0x01) "active":** set at instantiation (`(mode&0x18)|1`);
  `widgetStateSet` may clear it but never set it (one-way).
- **Bit 1 (0x02) "hilited":** S1's `buttonHoverSet` (0x43BDD0) does NOT
  touch the widget state word — it sets/clears bit 2 in four button-internal
  per-element words (+0x84/+0x98/+0xAC/+0xC0 of the button object,
  confirmed by disassembly). The widget-level hilite writer remains
  untraced (open).
- **Bit 3 (0x08) "visible":** kntrPaint child filter (B2).
- **Bits 4–5 (0x18):** from descriptor mode (instantiation).
- **0x20 (bit 5):** settable; CLST/LSTS ctors OR 0x20 in after init.
- Notification = `[class+0x5C]` = widgetClassObj.stateNotifyFn ✓ (consistent
  with the corrected layout; S1's "(widget+4) vtable+0x5C" reading of the
  code was right about the path, wrong about the state address).

### 16.2 `widgetInstantiate` (0x408750) — field sources confirmed

arg mapping: (desc, parent, bufLen, …). Verified writes:

| widget offset | source | form |
|---|---|---|
| +0x00 | constant | 0x5655D881 |
| +0x04 | classTableLookup(bswap32(desc+0x00)) via 0x409150 | ptr (set by outer flow after ctor) |
| +0x08 | parent (arg2, magic-checked 0x5655D881) | ptr |
| +0x0C..+0x1B | desc+0x04..+0x0B | 4 × i16BE sign-extended to int |
| +0x1C..+0x27 | scaleQuad (0x429C70) over the raw quad | 4 × int |
| +0x2C | desc+0x0C (instance 4cc) | byte-permuted u32 (permutation consumer-side, unverified) |
| +0x30 | desc+0x10 (flags u32BE) | byte-permuted u32 |
| +0x34 | (i16(desc+0x20) & 0x18) \| 1 | u16 state |
| +0x37 | desc+0x23 | byte |

Allocation = max(classObj+0x08, 0x38). Bounds: desc+0x28+round4(desc+0x14)
≤ desc+arg3. Descriptor layout per the walker (instance @+0x0C, flags
@+0x10, size @+0x14, mode @+0x20, b22 @+0x22, b23 @+0x23) is consistent with
every source read above.

### 16.3 CLST / LSTS ctors — parameters and object layout (CONFIRMED)

`clstWidgetCtor` (0x4215A0) and `lstsWidgetCtor` (0x4209E0) are mirror
images:

- **Signature:** (minSize, parent, quadSrc16, flags, flagsStored, listOpts).
- **Allocation:** max(minSize, class min) — CLST **0x54 (84 B)**, LSTS
  **0x4C (76 B)**.
- **Base fill:** identical to widgetInstantiate (magic, raw quad ← arg3,
  scaleQuad → +0x1C, state @+0x34, +0x37 = flags&0xFF); additionally
  **+0x36 = 0x20 when flags & 0x400** (so +0x36 is a real flag byte, not
  padding); +0x30 = flagsStored (arg5, stored as-is — the permuted desc form
  only appears on the instantiate path).
- **State bits (ctor path):** CLST: 1 | (flags&0x100 ? 8 : 0) |
  (flags&0x200 ? 0 : 0x10); LSTS: same plus unconditional `state |= 0x20`.
- **Parent attach (C1 "parent attach" item CLOSED):** magic-check parent,
  require `[parentClass +0x88]` (widgetClassObj.attachFn) non-NULL (else
  hError 0x6ED/0x56/0x10002), call `attachFn(parent, child)`, then
  `[child+0x08] = parent`. Detach counterpart (likely +0x8C) not yet traced.
- **List objects (ownership item CLOSED):** `listViewCtor` (0x447590,
  args (obj, cb 0x41F970, 0xB, 0, listOpts|0x124, quadSrc)) → **listView
  @+0x38**; `listModelCtor` (0x422EB0) → **listModel @+0x3C**. Both owned
  by the list widget (dtor frees — to verify in teardown audit).
- **Event registrations:** 6 model-side (wrappers 0x4242D0/0x424410/
  0x424390/0x424310/0x424350/0x424510 with callbacks 0x41F990/0x41F9B0/
  0x41FA50/0x421540/0x420900/0x420960) + 2 view-side (0x448960/0x4489A0
  with 0x4218E0/0x421970). 0x420900/0x420960 sit in the LSTS address range
  → shared list callbacks. Wrapper names deferred to the list-subsystem
  pass (pattern is uniform: (widget, callbackFn, model|view)).

Ghidra: `widgetBase` rebuilt (instCode/flagsStored/state/b36/flagByte),
`listWidgetObj` (64 B: base + listView @+0x38 + listModel @+0x3C) created
in category /; `widgetClassObj.attachFn` @+0x88 pre-existing; comments on
0x4093E0, 0x408750, 0x4215A0, 0x4209E0 — all read-back verified.
