# S2 worklist — FourCC records, registry, dispatch, geometry, evidence closure

Session S2. Baseline: 14507f9 (S1). Program: AppearanceEdit.exe, x86:LE:32,
base 0x400000 (verified 2026-11-19: x86/little/32, 1534 functions, S1 symbols
intact: widgetStateSet/skinInstall/nineSliceBlitC).

**New top priority (user-directed):** `MENUscal`-type apparent strings are
likely adjacent FourCC integer fields at the start of larger binary records —
reconstruct the enclosing records, not just the FourCC pairs.

## Batch plan
- A1 — `MENUscal` raw bytes, containing record, creating/consuming code
- A2 — related FourCC record families (VWIN, MENU, BUTN, SEPR, KNTR, VWINdoku,
  DisabledBUTN, DisabledSEPR, Default+BUTN, %MNU, %VUU)
- A3 — registry identity + object lifecycle model (0x45F844/0x4605D8,
  constructApp, lookup helpers, fileClose registry unlinks)
- B1 — template method tables (tableButtonMethods 0x45E140, tableLabelMethods
  0x45C560): {fn, arg} descriptor interpretation
- B2 — paint dispatch walker: WM_PAINT → per-child paint (S1 open item 1)
- C1 — S1 enrichment gate: 14 named functions (+ new registry/dispatch fns):
  prototypes, parameter names, meaningful locals, read-back
- D1 — scrollbar geometry functions
- D2 — slider geometry functions
- D3 — shared geometry (rect types, scaling, hit-testing)
- E1 — D role consumers (per-painter role-index constants; 54th slot)
- E2 — E icon mapping (155 names vs 192-row v1; runtime ink objects)
- E3 — remaining resources (gStyleStrA/B, gOncePtr, 0x40F220/0x41D390,
  blob B layout, TSLC assembly, %MSI records)
- F1 — font/text pipeline (.fnt → ink; bmpTextDraw/fontTextDraw/fontMetricsGet)
- G1 — C-blob field0/field2/field4 + secondary modes 2/4/8
- V1 — 5 remaining screenshots + corpus validation
- V2 — final audit, docs 17–21, symbol ledger, save, commit

## Status
### Completed
- **A1 (MENUscal record) — COMPLETE, code-verified (2026-11-19/20):**
  - `MENUscal` = 3rd record of the **%REZ built-in UI registry** @0x45F830. It is a
    (type FourCC, instance FourCC) record pair, NOT an eight-character string.
  - %REZ header (rezHeader 24B, applied): tag "%REZ" @+0 | byte 0 @+4 | u32LE
    version=1 @+5 | u64LE 0x3C98 @+9 (purpose unknown) | pad3 @+11 | u32LE
    count=9 @+0x14 | records @+0x18.
  - rezRec (20B, applied as rezRec[9] @0x45F848): type4cc ASCII @+0 | instance4cc
    ASCII @+4 | flags(0) @+8 | sizeBE u32 @+0xC | offsetBE u32 @+0x10 (relative to
    0x45F830). Sorted by (type,instance); binary search (searchRecords 0x4401C0:
    standard lo/hi/mid; builtinRecCmp 0x4457C0 compares bswap(rec+0) vs type key
    then bswap(rec+4) vs instance key).
  - **CORRECTION to earlier notes**: doku offset 0x0DA0 → 0x45F830+0x0DA0 =
    **0x4605D0** (earlier I miscomputed 0x4606D0; 0x830+0xDA0=0x15D0). The %VUU at
    0x4605D0 IS the doku window payload. The binary at 0x4606D0 is INSIDE the doku
    payload (offset 0x100) = its child-record region.
  - Payload pool (contiguous, verified): exam 0x218@0x45F900 (%MNU), fsit
    0x78C@0x45FB18 (%MNU), scal 0x328@0x4602A8 (%MNU), doku 0x620@0x4605D0 (%VUU),
    efik 0x448@0x460BF0 (%VUU), emik 0x4B0@0x461038 (%VUU), epxm 0x908@0x4614E8
    (%VUU), esik 0x3B0@0x461DF0 (%VUU), prvw 0x1328@0x4621A0 (%VUU).
  - **%VUU payload format (code-verified, vuuPayloadParse 0x408B60):**
    +0x00 "%VUU" | +0x04 u16BE ver=1 | +0x06 u16 0 | +0x08 VWIN record (40B,
    widgetDesc: class VWIN, x=0,y=0, w/h u16BE, classCode 0, flags 0, sizeBE @+0x14,
    f18/f1c 0, modeBE, b22, b23, pad2, childCountBE, pad1) | +0x30 window-own block
    20B: {u32 → newWin+0x18 (packed u16×2, meaning open); u32 → 0x40CC30 arg;
    u32; 4×u16BE (doku: 380,300,0x4E20,0x4E20 → if any nonzero: scaleQuad +
    0x40C9A0(win,4 v)); align byte (0→0x40CAC0(full u32), 2→default, else
    0x40CB10(byte))} | +0x5C child records (widgetDesc each, recursive).
    All 6 %VUU objects verified: sizes 0x2C/0x3C/0x4C/... at record+0x14, all
    consistent with vuuPayloadParse (my earlier "size=0" alarm was a hexdump
    misread; disk==Ghidra confirmed at 0x460C0C=00 00 00 3C).
  - **widgetDesc (40B, applied to 6 doku records):** class4cc ASCII | x,y,w,h u16BE
    (i16) | classCode4cc u32BE ASCII (→ widget+0x2C, matched vs instance table) |
    flagsBE u32 (→ widget+0x30) | sizeBE u32 (payload, round4) | f18 | f1c (both 0
    in all built-ins) | modeBE u16 (bit 0x04 → FUN_00409850 post-init;
    (mode&0x18)|1 → widget+0x34) | b22 (classInit arg) | b23 (→ widget+0x37) | pad2 |
    childCountBE u16 | pad1.
  - **widgetInstantiate (0x408750) verified semantics:**
    widgetClassLookup(bswap(desc+0)) → classObj (NULL → hError 0x10017);
    size = max(classObj->size, 0x38); memAllocZeroed; widgetBase (56B, applied):
    +0x00 magic 0x5655d881 | +0x04 classObj | +0x08 parent | +0x0C..+0x1B 4×u32
    SLOTS holding raw i16 x,y,w,h | +0x1C..+0x2B 4×u32 slots holding SCALED i16
    (scaleQuad × gScaleNum/gScaleDen) | +0x2C classCode | +0x30 flags | +0x34 mode
    | +0x37 byte. Parent: magic check (0x10019), classObj+0x88 attachFn(parent,
    child) must exist (0x10002); child+0x08 = parent; classInitFn(child, desc,
    classCode, b22) if classObj+0x0C; if mode&4 → FUN_00409850(child); advance
    round4(size); childCount from classObj+0x14 fn? NO — from desc+0x26 u16BE; recurse
    that many times passing &childOut; instance-table registration: walk table
    (8B entries {u32 name LE-stored, u16 slotByteOffset, u16 0}), if name ==
    widget+0x2C → slotArray[slotOffset] = widget.
  - **scaleQuad (0x429C70, renamed):** dst[i] = (int)(src[i] * gScaleNum)/gScaleDen
    for 4 i16 values — CONFIRMS gScaleNum/gScaleDen (S1) scale ALL widget geometry.
    This is what the "Scale:" (scal) menu controls.
  - **menuPayloadParse (0x412060, renamed):** %MNU header: +0 "​%MNU" | +4 u16BE
    ver=1 | +6 byte nameLen | +7 byte b7 | headerSize=round4(nameLen+b7+0x2B) | +0x1C
    u32BE style (arg3 of FUN_0040FB90 menu ctor) | +0x20 u32BE → menuObj+0x5C |
    +0x24 u32BE item count (≤0x400) | +0x28 pstr name (len=nameLen) | items[]:
    each ≥0x38B: +0x00 u32BE type | +0x04 u32BE id | +0x08 u16BE? +0x1A u16 packed
    → +0xC | +0x0C u32BE → +0x10 | +0x18 u16BE → +0x14 | +0x21 byte → +0x16 |
    +0x22 byte → +0x17 | +0x34 byte titleLen | +0x38 pstr title | then pstr icon
    (len byte at item+0x55) | itemSize=round4(b37+b36+iconLen+0x3B+titleLen). Items
    appended via FUN_00440790 to menuObj+0x0C array; post: FUN_00423210, FUN_0040FCC0.
    (Field meanings HYPOTHESIS; offsets CONFIRMED.)
  - **widgetAllocInit (0x408670, renamed):** (size ≥0x28, geom4, class4cc, param4,
    name4cc) → memAllocZeroed; scaleQuad(geom, local); FUN_0040BFA0(obj, geom,
    class4cc, param4, name4cc) → obj+0x04 (classObj); FUN_0040AE70(classObj,
    &PTR_labelPaint_0046624c) (default paint?); obj+0x00 = 0x5655d881; obj+0x08 =
    &DAT_00466188 (temp). Caller passes A0 = window object size: doku 0x1C0=448,
    prvw 0xA0=160, epxm 0x78=120, emik 0x5C=92, efik 0x54=84, esik 0x4C=76.
  - **windowCreateFromBuiltIn (0x408ED0, renamed):** (objSize, name4cc,
    instTable, instCount, param4, parent) → lookupBuiltInRec(VWIN, name4cc, &size)
    → vuuPayloadParse(parent, payload, size, 0, instTable, instCount, 0, parent).
    Callers: docCreate("doku", 0x1C0, dokuInstTable, 19), 0x401E30("prvw", 0xA0,
    prvwInstTable, 29), 0x407AD0("emik", 0x5C, emikInstTable, 9), 0x405B00("efik",
    0x54, efikInstTable, 8), 0x404EC0("esik", 0x4C, esikInstTable, 6), 0x406F40
    ("epxm", 0x78, epxmInstTable, 18).
  - **menuCreateFromBuiltIn (0x412490, renamed):** lookupBuiltInRec(MENU, inst)
    → menuPayloadParse.
  - **Class registry (18 classes):** widgetClassLookup (0x409150) fast path:
    BUTN→0x4674A0, HOLD→0x468188, KLBL→0x467564, KNTR→0x466690, LABL→0x467628,
    TXTS→0x466C80, "VUU!"(0x56555521)→0x4660C4; slow path = dynamic pointer array
    at [gClassTblPtr 0x466B5C] count [gClassCount 0x466B60], linear scan comparing
    arg vs classObj+0x00 (tag stored native LE). Registered at runtime by 11
    thunks classReg* (callers include constructApp 0x403D30): SEPR 0x4677B0, RABL
    0x46824C, ROLR 0x4679FC, RLDR 0x467C48, TIKB 0x467AC0, PRGS 0x467B84, IKON
    0x468310, IMGS 0x466ECC, "BOX!" 0x4676EC, BPMN 0x467874, IKBT 0x467938.
    widgetClassRegister (0x409100): search (0x440B70) then insert (0x440790) into
    that table; NULL classObj → hError 0x10002.
  - **widgetClassObj (144B, applied to all 18):** +0x00 tag (native LE of BE int) |
    +0x04 0 | +0x08 size | +0x0C initFn | +0x14 childCountFn | +0x5C stateNotifyFn
    (S1 ✓) | +0x88 attachFn | rest = unverified vtable slots (named v10..v8c).
    Sizes: VUU! 0x38, KNTR 0x70, BUTN 0x40, BPMN 0x40, SEPR 0x38, ...
  - **doku window tree (verified, partial):** VWIN 380×400 obj=0x1C0B → KNTR
    (380×400, classCode 0, 8 children, mode 0x18) → [BPMN "menu" (5,4 175×24), SEPR
    (2,28 379×32, 4 children, mode 0) → KNTR "info" (0,30 380×400, 3 children) →
    KLBL "Name:" (10,15 100×31, pstr "Name:"), TXTS "naam" (10,65 30×36, pstr?),
    ...], + 7 more KNTR children (the tab pages: info/klrs/...). SEPR apparently
    hosts the tab pages (4 children) — a separator-class container.
  - **Instance tables (typed+renamed):** dokuInstTable 0x45F048 (19),
    prvwInstTable 0x45F57C (29), epxmInstTable 0x465A9C (18), emikInstTable
    0x465FB4 (9), efikInstTable 0x46440C (8), esikInstTable 0x4640C4 (6).
    Entry = {u32 name (native LE storage; canonical spelling = BE reading = ASCII
    in descriptors), u16 slotByteOffset (4×index), u16 0}. doku names: menu, info,
    klrs, jmis, snks, kifp, kpim, naam, srev, ktrr, dsek, krea, idom, scal, klrl,
    lmij, lnik, kifb, kiml. (scal = the Scale menu ✓ matches BPMN classCode @
    0x46066C "menu"... note: BPMN menu bar's classCode = "menu"; the "scal"
    instance is a different BPMN deeper in the tree — see doc 17.)
  - **Ghidra enrichment applied + read-back verified (probes):** 21 function
    renames (widgetClassLookup, widgetClassRegister, widgetInstantiate,
    vuuPayloadParse, windowCreateFromBuiltIn, menuCreateFromBuiltIn,
    lookupBuiltInRecSoft, scaleQuad, menuPayloadParse, widgetAllocInit, 11
    classReg*); 28 data renames (rezBuiltinHeader/Records, gClassTblPtr/Count,
    18 classXxx, 6 xxxInstTable); 5 structures created (rezHeader 24B, rezRec 20B,
    widgetDesc 40B, widgetBase 56B, widgetClassObj 144B — all size-verified);
    26 data applications (rezHeader×1, rezRec[9]×1, widgetDesc×6, widgetClassObj×18
    incl. re-typing the 18 classXxx with their names).
  - **S1 corrections pending doc updates:** (1) widget "u16 state @+0x0D" was a
    misread — +0x0C..0x2B are u32 slots holding i16 geometry (raw then scaled);
    re-audit widgetStateSet in C1. (2) S1 "button rect @+0x2C..0x38" — in the base
    widget +0x2C=classCode/+0x30=flags/+0x34=mode; BUTN class size is only 0x40,
    so S1's ≥0xC4 button object is a different (editor-side) object — re-audit in
    C1. (3) 0x4625C0–0x462700 "widget class descriptor pool" = prvw window child
    records (TIKB/IKBT/IKON/BPMN/KNTR/SEPR widgets in the live preview), not class
    descriptors.
  - IKON lookups in cell painters (0x42A2D0/0x42B5D0): IKON class EXISTS in the
    registry (0x468310), so these lookups are for the IKON widget class — not a
    separate icon table. Earlier "separate runtime-registered table" theory is
    SUPERSEDED (IKON is one of the 11 registered classes).
  - `MENUscal` = 3rd record of the **%REZ built-in UI registry** @0x45F830.
  - %REZ header: +0x00 "%REZ"+NUL | +0x05 u32LE 1 | +0x09 u32BE 0x3C98 (pool total) |
    +0x0D u32 0 | +0x10 u32 0 | +0x14 u32BE count=9 | +0x18 records[9].
  - Record (20 B stride, sorted by (type,instance), binary search):
    +0x00 u32 type FourCC (ASCII bytes in memory) | +0x04 u32 instance FourCC
    | +0x08 u32 0 (all 9) | +0x0C u32BE payload size | +0x10 u32BE payload offset
    (relative to 0x45F830). All 9 payloads verified contiguous:
    exam 0x218@0x45F900, fsit 0x78C@0x45FB18, scal 0x328@0x4602A8,
    doku 0x620@0x4605D0, efik 0x448@0x460BF0, emik 0x4B0@0x461038,
    epxm 0x908@0x4614E8, esik 0x3B0@0x461DF0, prvw 0x1328@0x4621A0.
  - `lookupBuiltInRec` 0x445830: hard lookup (hError 0x10011 "RM" if missing),
    returns 0x45F830+bswap(rec+0x10); bswap(rec+0x0C) → out param.
  - `FUN_00445900` = soft variant (returns NULL if missing).
  - `searchRecords` 0x4401C0 = BINARY SEARCH (lo/hi/mid, cmp signed);
    `builtinRecCmp` 0x4457C0: type vs rec+0, instance vs rec+4 (both bswap vs
    BE-convention key constants). Table sorted: MENU exam/fsit/scal < VWIN
    doku/efik/emik/epxm/esik/prvw ✓.
  - Payloads: %MNU ×3 (exam/fsit/scal menus), %VUU ×6 (doku/efik/emik/epxm/
    esik/prvw windows). %VUU/%MNU headers: u32 class tag | u16BE version=1 |
    ...; children = [40B descriptor][payload round4(size)]; descriptor:
    +0x00 class 4cc | +0x04..0x0B 4×u16BE geom (i16) | +0x0C u32BE classCode
    | +0x10 u32BE flags | +0x14 u32BE size | +0x18.. | +0x20 u16BE mode |
    +0x22 byte | +0x23 byte | +0x2B byte (name len, window parser).
  - `FUN_00408750` = generic widget instantiator (recursive): calls
    0x409150(classCode) = **class lookup** (class registry, err 0x10017 if
    missing); allocates widget size ≥ classObj+0x8 (min 0x38); widget object:
    +0x00 magic 0x5655d881 | +0x04 classObj | +0x08 parent | +0x0C..0x1B
    i16×4 geom | +0x1C rect (via 0x429C70) | +0x2C classCode | +0x30 flags |
    +0x34 u16 mode=(descMode&0x18)|0x1 | +0x37 byte | +0x38 class-specific;
    classObj: +0x08 size, +0x0C init fn (called with (widget, desc, classCode,
    desc+0x22)), +0x5C state-notify vtable, +0x88 attach fn (parent check
    magic 0x5655d881, err 0x10019). Recursion: desc+0x18 ptr? no — child
    payloads nest after each record; child count from widget+0x14 (classObj?
    [EBP-0x20]+0x14 = u16BE childCount) — see pseudocode tasks.
  - Instance table (per-window): 19×[u32 name][u16 slot][u16 0] @0x45F048,
    count 19 (docCreate A3); names (stored LE bytes / BE-convention spelling):
    unem/menu?, ofni, srlk, simj, skns, pfik, mipk, naam, vers, rtrk, dsek,
    aerk, modi, lacs, lrkl, jilm, kinl, kifb, kiml (byte-order question open);
    slot = index×4 into parent child-slot array (0x40,0x44,...0x8C).
  - Registry node @0x45F000: u32 0x64 | u16 0x71 | u16 0x20 | pstr(17)
    "system/appearance" | u32 ptr→pstr (0x45F008) | 5×[u32][u16][u16] @0x45F020
    (0xA1/0x6E/0x20, 0xA2/0x6F/0x20, 0xA5/0x73/0x22, 0xA4/0x73/0x20,
    0x9A/0x70/0x20). docCreate: window+0x14 = 0x45F020; windowCreate call:
    (0x1C0?, "doku", &0x45F048, 19, 0, parent). Tab-name pstrs @0x45F0E0:
    Information/Colors/Images/Icons/File Icons/Mouse Icons + menu cmds
    (New/Open.../Import Colors.../Save...).
  - doku window tree contains: "Scale:" C-string + BPMN widget instance
    "scal" (menu-bar scale menu) @0x4609A0-0x4609D8; KNTR instances "info",
    "klrs"; KLBL; TXTS "naam" with pstr "Name:"; SEPR; BPMN "menu". Widget
    instance records: [class 4cc][u32][u16BE x][u16BE y][instance 4cc|pstr]...
  - docCreate @0x401000: PUSH 0x1C0, "doku", 0x45F048, 19, 0, parent →
    FUN_00408ED0 (windowCreateFromBuiltIn: lookupBuiltInRec(VWIN, inst, out)
    → 0x408B60(payload parser)). FUN_00412490 = menuCreateFromBuiltIn
    (lookupBuiltInRec(MENU, inst) → 0x412060 menu parser; sets obj+0x18/+0x1C).
  - %IKN search: 50+ hits 0x46FEBC–0x476364+ = F section (25 ink objects) +
    G section (20 cursor objects) of the embedded HAP @0x4683D4.
  - **Correction**: 0x4683D4 = complete **Evil Chiaroscuro** HAP v2 blob
    (name="Evil Chiaroscuro", C:142 slots, D:54, E:36 rows, F:25, G:20 —
    verified by hap_inspect.py on extracted file). S1 F5 "grey ramp / blank
    default" note was wrong. Extracted file naming is INVERTED vs symbols:
    assets/builtin-EvilChiaroscuro-v2-A.hap = HAP @0x4683D4 (Ghidra symbol
    gBuiltinHapEvilChiaroscuroB); -B.hap = raw fragments @0x466DD4 (TSLC).
  - IKON lookups in bmpSetCellState(0x42A2D0)/bmpRowText(0x42B5D0) cell
    painters: no IKON records exist in the 9-record static table and NO
    static writer extends it (searched immediates + pointer values). Model:
    toolkit-generic cell-icon path (used by Haxial clients with larger
    registries); editor's own list cells take the blit-pair/text paths.
    Marked PROBABLE (no disproof that editor ever hits it).

### Completed — A3 CLST/LSTS + B reconciliation (2026-11-20, resumed from 627febf)

- **CLST/LSTS RESOLVED (Priority A):** both are LIST widget classes.
  - `classClst` 0x466E08 (tag TSLC = stored LE of BE **CLST**), size 0x54 —
    multi-column list ("column list").
  - `classLsts` 0x466D44 (tag STSL = stored LE of BE **LSTS**), size 0x4C —
    single-column list. (Spelling correction applied: earlier "LSST" wrong.)
  - Both share 19/21 method slots (class objects = method tables; VUU! is the
    base class, 0x409Bxx–0x409Dxx generic cluster; +0x14 always NULL; +0x10 =
    teardown; shared initFn 0x409BD0 = single RET no-op). Doc 17 §6.1.
  - Direct constructors (NOT %VUU-descriptor path): `clstWidgetCtor` 0x4215A0,
    `lstsWidgetCtor` 0x4209E0. Both: memAllocZeroed(≥class size), magic
    0x5655d881, raw geom → +0x0C.., scaleQuad → +0x1C.., mode = (flags bits
    0x200/0x100 → 0x10/0x08) | 1 → +0x34, +0x36 = 0x20 if flags&0x400, +0x37 =
    (char)flags, +0x30 = classCode, parent attach (magic 0x10019, classObj+0x88
    non-null 0x10002), mode |= 0x20 post-attach.
  - Sub-objects: `listViewCtor` 0x447590 (view, 0xAC/0x104 B, magic
    **0xFDB6D01A**, geom @+0x04, flags @+0x2C (bit-normalized), u16 metric 0x10
    @+0x38, const 3 @+0x50, callback @+0x54, back-ptr @+0x58, 0xFFFFFF00
    @+0x78, extra param @+0x74) → widget+0x38; `listModelCtor` 0x422EB0 (model,
    0xC8 B, magic **0x8521B2D1**, 4-word seed @+0x04, source code @+0x18, -1s
    @+0x1C..+0x28/+0xC0, byte 1 @+0x62) → widget+0x3C; `listModelDtor` 0x422F30
    (magic check, per-element teardown: count @+0x40, array @+0x3C, element cb
    @+0x80, arg @+0x84; frees @+0xBC, @+0x30).
  - CLST-only: column data via FUN_0044C910(NULL, colData, colCount, 0x4219B0,
    widget) → +0x4C; +0x40 = FUN_0044CBE0(view); +0x50 = FUN_0044D520(view);
    FUN_00447B20(view, 0x14, 0, 0x14, 0). Column defs: interleaved {ptr to
    header pstr} + {u16: 6, w, w, 0x3C, cap(0x1F4=500), x} stride 0x18.
    Headers seen: "Column 1/2" (0x45F174/0x45F180, prvw demo), "Name/Info"
    (0x45F4D4/0x45F4DC, prvw), "Icon/Name" (0x466054/0x46605C, emik).
  - Consumers: docCreate (doku) builds CLST 0x1D4 (emik-style icon list, 13
    entries table @0x465F1C) + CLST via 0x4056B0/0x4049E0 + LSTS 0x130 (0x403F80)
    + LSTS 0xDF8 (0x4065A0); prvw (FUN_00401E30) builds 2×CLST (0x401A20: 2-col
    "Column 1/2" w/ "an item"/"123K" sample data @0x45F1C0; 0x401BB0: 3-col
    "Name/Info"); efik 0x4056B0, esik 0x4049E0 (CLST); epxm 0x4065A0 (LSTS 0xDF8);
    0x417CD0 (LSTS 0x4C) ← 0x417E90; 0x414EA0 (LSTS 0x5C) ← 0x416C40/0x416530.
  - Model source codes (ctor param7): 4, 0x102, 0x103, 0x200, 0x204, 0x205,
    0x214, 0x215 (meaning open — PROBABLE dataset family|index).
  - **D-section association DISPROVEN**: .hap files frame sections by header
    offset fields (corpus-verified: v1 header has no FourCC section tags; only
    %HAP/%IKN/%MSI magics); D colors flow via gStyleDColors/styleColorGet (S1).
    The other "TSLC" string is inside the blob-B assembly table 0x466DD4 (doc
    13 §3) — unrelated. Doc 17 §6, doc 02, 07-open-questions updated.
  - Ghidra: renames classTslc→classClst, classStsl→classLsts +
    clstWidgetCtor/lstsWidgetCtor/listViewCtor/listModelCtor/listModelDtor;
    plate comments @0x466E08, @0x466D44. Ledger A3 section written.

- **B reconciliation (Priority B) — COMPLETE:**
  - rezHeader REBUILT + code-verified (lookupBuiltInRec 0x445830 + soft
    0x445900): header address hardcoded; ONLY +0x14 (count u32**BE**, LE-load +
    bswap) is read; records always at structural +0x18 (NO pointer field —
    A1's "records ptr" wrong); +0x08 = u32**BE** totalSpan 0x3C98 (exact:
    0x18+0xC0+0x3BC0); +0x04/+0x05 (version=1)/+0x0C/+0x10 not read in this
    binary (static registry, no writer here). Structure rezHeader replaced
    (8 components, 24 B).
  - rezRec verified: type @+0x00 / instance @+0x04 (builtinRecCmp bswaps both
    vs BE code-constant keys; difference-based predicate), size u32BE @+0x0C
    (→ sizeOut), offset u32BE @+0x10 + header (return), flags @+0x08 NOT read
    (reserved here), stride 0x14 literal. MENU/scal = record 3 (type,instance)
    — preserved, no eight-char string.
  - widgetDesc re-verified vs disassembly: mode u16BE @+0x20 (LE load +
    SHL/SAR/OR swap; (mode&0x18)|1 → widget+0x34 via `MOV word [EAX+0x34],DX`),
    b22 @+0x22, b23 @+0x23 (MOVZX byte), childCount u16BE @+0x26 (swapped;
    KNTR=8, VWIN=1 verified in raw data), size u32BE @+0x14 = PAYLOAD bytes
    after the fixed 40 (VWIN=44 = window-own block; KNTR=12 = zeroed reserved);
    record advance = 40+size (verified: 0x46062C→0x460660 = 52; 0x4605D8→
    0x46062C = 84). No field overlap; layout CONFIRMED.
  - Class inventory: 21 classes reconciled across docs (7 fast-path, 11
    registered, WIND direct, LSTS/CLST direct; SLDR corrected from "RLDR").

### Completed — C3: %VUU window trees (2026-11-20)

- Built `tools/research/vuu_walk.py` (record walker: 40B fixed +
  round4(payload) + childCount recursion; instance-table cross-check).
- **ALL SIX windows walk EXACT** against %REZ sizes; named instances match
  instance tables 1:1 (doku 30/19, efik 17/8, emik 19/9, epxm 42/18, esik
  15/6, prvw 86/29; total 209 records, 89 instances). Full trees →
  `data/vuu-trees.txt`. (esik size is 0x3B0, not 0x1B0 — earlier arithmetic
  slip; also: 4B pad between scal MENU and doku VWIN payloads in the pool.)
- **widgetInstantiate fully re-decoded** (arg3 = TOTAL subtree bytes, not
  payload size; classInit = (widget, payload=desc+40, payloadSize, b22);
  child loop gated by classObj+0x14 childCountFn — KNTR has one
  (kntrHasChildren, `return widget`); A2/A3 "always NULL" corrected).
- **KNTR payload 12B** = {u32BE A, u32BE B, u16BE C}: A=B=0 always; C=1 root
  containers, C=3 tab pages (semantics UNKNOWN, values only) →
  kntrWidgetInit (0x412780) → widget+0x5C/+0x60/+0x64; mode |= 0x20.
- **BPMN payload 12B** = {u32BE menuRefA, u32BE menuRefB, u32}: A≠0 →
  menuCreateFromBuiltIn (MENU 0x4D454E55 lookup → menuPayloadParse); else
  menuObjectCtor (0x40FB90, 0xA4B menu obj); menu → widget+0x38;
  0x436160/0x4361D0 = function pointers (handler fns), NOT data tables.
- **Window-own block model** (VWIN payload 44–64B): +0 options word →
  windowCtor; +4 u32 → FUN_0040CC30; +0C..+12 4×u16BE quad → (if any ≠0)
  scaleQuad → FUN_0040C9A0; +14 u8 mode (0→FUN_0040CAC0, 2→none, else
  FUN_0040CB10); +23.. title pstr (default name; caller can override). Block
  tail is builder-specific (esik differs: title @+13, size pair @+28, 0x0C
  @+3C). doku options 0x1000010F, emik 0x10000001, epxm 0x10000009, others 0.
- **widgetAllocInit decoded**: obj = zeroed(max(size,0x28)); windowCtor
  (0x40BFA0) ← (geom, options, arg4, name, obj); [obj+0x0C] = result;
  windowDefaultPaintInstall (0x40AE70) ← (obj+0x0C, 0x46624C); obj+0 =
  magic; **obj+0x04 = classWind (0x466188) ALWAYS** — the "classCode" is not
  a class lookup; all windows are WIND-class. Resolves S1's FUN_0040BFA0 /
  FUN_0040AE70 items (renamed windowCtor / windowDefaultPaintInstall).
- **Instance table model confirmed**: 8B entries {instCode u32, slotOffset
  u32}; registration loop stores WIDGET POINTER into windowObj[slotOffset]
  (ESI reloaded before the store — corrected my mid-analysis doubt). Static
  slot offsets are dense (0x28, 0x2C, ... per window).
- **prvw = live-preview window** (360×340, 8 tabs: misc/tiks/boxs/slid/hsbs/
  vsbs/btns/lscc — widgets rendered enabled+disabled pairs; matches the
  preview screenshots). KOLR appears in btns tab (color chooser preview);
  lscc hosts the runtime CLST list (A3).
- Ghidra: 6 renames (windowCtor, windowDefaultPaintInstall, kntrWidgetInit,
  kntrHasChildren, bpmnWidgetInit, menuObjectCtor) — all read-back verified.
  Ledger C3 section written. Doc 17 §15 written; §14 updated.

### In progress
- **Batch D (geometry) — ACTIVE** (next: D1 HOLD/scrollbar object model via
  HOLD initFn 0x43CC30 + preview sbhd/sbvs instances; D2 SLDR 0x438060;
  D3 scaleQuad 0x429C70 + mbarSlotGeometry 0x42EB30 + coordinate spaces;
  part tables 0x45F0C0–0x45F0DC / 0x45F61C–0x45F660 consumers; C1
  absorption: state-bit consumers, detach counterpart +0x8C?, list dtor).
- **Resolved 2026-11-24 (menuDestroy thread + MBAR mechanism — doc 17 §17)**:
  "0x40FD20 mid-function call" = decode-arithmetic error (target 0x40FCC0
  entry; capstone-verified); menuDestroy slot-destructor contract;
  mbarSubObj fully mapped (192 B; cb pairs; itemArray[32]); MBAR runtime
  chain decoded (mbarWidgetInit/mbarAttachBuiltInMenu/mbarAddMenu/
  mbarPopupShow/previewMbarCmdHandler/menuBarTitleGet); "exam" menu IS
  referenced (prvw preview ×3 — B2 scoped-claim corrected); 10 renames +
  10 protos + 12 comments + mbarSubObj struct replaced (read-back verified).
- **C1 (enrichment gate)** — widget-base re-audit **DONE** (doc 17 §16):
  state word @+0x34 (S1's +0x0D wrong); widgetInstantiate field-source
  table; +0x2C = instance code; +0x36 = flag byte; widgetBase rebuilt;
  CLST/LSTS ctors decoded (sig, min sizes 0x54/0x4C, view @+0x38,
  model @+0x3C, attach via [parentClass+0x88]); 3 semantic prototypes
  applied (widgetStateSet, clst/lstsWidgetCtor). buttonHoverSet
  reclassified (button-internal, not state writer). REMAINING: systematic
  per-function param/local sweep of ~150 renamed fns (deferred — each
  needs its own disassembly check; done per-batch + V sweep), widget
  detach counterpart (+0x8C?), widget-level hilite (0x02) writer,
  list-widget dtor ownership check (batch G/teardown).

### Pending
- D (geometry: scrollbar/slider part tables 0x45F6xx/0x45F0xx consumers),
  E (resources: D roles, E icons, ink objects, blob-B assembly 0x466DD4,
  gOncePtr 0x46698C→0x47B324), F (font/text), G (C-blob field0/2/4 +
  secondary modes), V (validation: 5 remaining screenshots, docs 19–21,
  final audit + commit).

### Completed — B2 remainder: %MNU menu subsystem (2026-11-21)
- **Format fully reconstructed (doc 17 §8, SUPERSEDES preliminary table):**
  header 0x28B (magic/version/nameLen/b7/style@+0x1C/field5c@+0x20/count@+0x24;
  hdrSize=(b7+nameLen+0x2B)&~3); item size=(b36+b37+iconLen+tlen+0x3B)&~3 with
  id@+0, value2@+4, flags=(flagsHi@+9<<16)|u16BE@+0x1A, iconIndex@+0xC,
  accel u16BE@+0x18, b21@+0x21, b23@+0x22, tlen@+0x34, iconLen@+0x35, title
  @+0x38[tlen], icon[tail]. Every offset re-derived from raw disassembly
  (decompiler uint* display was misleading); blob = 0x1A fixed + leading-len
  pstr title @+0x18 + leading-len pstr icon.
- **flags24 semantics CONFIRMED** via menuRowClickDispatch/menuRowToggle/
  menuInsertSeparatorAt: 0x20000 tick (toggle), 0x40000 disabled, 0x50000
  separator (static 0x10000 + disabled), 0x80000 static (no dispatch),
  0x100000 icon (from iconIndex), 0x140000 icon+disabled.
- **Corpus walk EXACT** (tools/research/mnu_walk.py, txt+json inventories in
  data/): exam 7 items (demo menu: accel 'X', icon items iconIndex 0x0A,
  separator, ticked), fsit 28 (MIME-type picker for efik "typm" BPMN), scal
  12 (scale options "½ 0.25"…"½ 3.00"; value2 = opaque command codes).
  47 items, zero leftover bytes.
- **BPMN→%MNU association CLOSED:** BPMN payload {refA, refB, w2}; refA=0 →
  empty menu (style=refB) filled by app code (docMenuBuild etc.), refA≠0 →
  menuCreateFromBuiltIn(refA) — all 9 BPMN nodes mapped (PE-verified);
  **"exam" is unreferenced by this build** (developer sample, PROBABLE).
- **menuObj (0xA4B) map completed:** magic/surface+0x04/model+0x08/arr+0x0C/
  cnt+0x10/cmdHandler+0x18/cmdCtx+0x1C/selCallback+0x20/ctx+0x24/cursorLo+0x3C/
  **style u16 @+0x50** (bit 2 = selection-list mode)/namePstr+0x58/
  **selCursor+0x5C (initialized from header field5c)**/rowSize+0x60/menu2+0x68
  (recursive destroy)/cursorHi+0x6C/subObj+0x80.
- **Full lifecycle chain confirmed:** BPMN press (bpmnEventPress) →
  bpmnMenuShow → popupMenuShow → row click → menuRowClickDispatch →
  toggle/select → (style&2) menuSelCallbackInvoke → bpmnSelectionNotify →
  widgetRefresh; (style 1) cmdHandler bpmnMenuCmdHandler → widgetMsgBubble
  (class+0x9C). Destroy: menuDestroy recursive.
- **Ghidra:** 33 function renames, 9 prototypes, 15 comments, 5 structs
  (mnuHeader/mnuItemRec/menuItemBlob/menuObj/mbarSubObj) + widgetClassObj
  extended to 180B, 6 data applications — all read-back verified. Ledger
  section written. Note: Ghidra hexdump tool returned corrupted reads for
  some addresses this session; PE-file reads are authoritative.

### Completed — A2 (string re-audit + class tag discovery, 2026-11-20)

User input folded in: (2) node model = class ID + instance FourCC ("'VWIN'
for view window, TIKB for tick button/checkbox, etc) followed by a four char
code identifier (ie. doku)") — matches our code-verified model; (3) "%VUU" means
'view'; developer C↔K naming eccentricity (KOLR=COLR, KLRS≈CLRS, KREA≈CREA,
KNTR≈KONTAINER) — user-supplied = PROBABLE semantics; (4) user does not want
to enumerate literals — we list strings and diff ourselves.
- **(a) COMPLETE (2026-11-20):** full printable-run audit of .rdata+.data
  (6477 runs ≥3 chars; 358 four-char alphabetic). Results → doc 17 §11:
  - 17 reversed class tags found = all class objects minus 2 with '!' in tag
    (!UUV/VUU!, !XOB/BOX!) — **21 class objects total, no orphans**.
  - KEY FINDING: class-object tag @+0x00 stores the **code constant as u32LE**
    = byte-REVERSED spelling in memory (BKIT=TIKB, DNIW=WIND, RLOK=KOLR, RABM
    =MBAR, RDLS=SLDR, NMPB=BPMN, NOKI=IKON, SGRP=PRGS, SGMI=IMGS, RPES=SEPR,
    RTNK=KNTR, STXT=TXTS, LBLK=KLBL, LBAL=LABL, DLOH=HOLD, TBKI=IKBT, STSL=LSTS,
    TSLC=CLST). widgetClassLookup compares the BE-reading argument DIRECTLY vs the
    tag word (no bswap) — verified from the 0x409150 disassembly subtract-chain
    (BUTN 0x4255544E, HOLD 0x484F4C44, KLBL 0x4B4C424C, KNTR 0x4B4E5452, LABL
    0x4C41424C, TXTS 0x54585453, VUU! 0x56555521).
  - NEW class objects: WIND @0x466188 (size 0x28, initFn 0 — the WINDOW class,
    direct ref from 0x408705 in widgetAllocInit), LSTS @0x466D44 (0x4C, list),
    CLST @0x466E08 (0x54, column list) — both resolved in A3 (see above).
  - NAME CORRECTIONS applied in Ghidra: classRolr→**classKolr** @0x4679FC
    (KOLR = K-swap of COLR; descriptor spelling KOLR, always next to "Color:"),
    classRabl→**classMbar** @0x46824C (MBAR = menu bar; descriptor MBAR,
    instance mbar in epxm window); classRegRolr→classRegKolr, classRegRabl→
    classRegMbar (thunks verified: push the object ptr, call 0x409100).
  - BUTN tag confirmed NTUB @0x4674A0 (size 0x40, initFn 0x4352C0); BOX! tag
    !XOB @0x4676EC (0x44, initFn 0x435FF0); VUU! tag !UUV @0x4660C4 (0x38,
    initFn 0x409BD0).
  - All 21 class objects: size/initFn from disk-verified headers; widgetClassObj
    (144B) applied to all.
  - Instance names (lowercase 4cc at descriptor+0x0C): ~50 catalogued in doc 17
    §11; includes menu-bearing widget instances (menu, scal, mbar, umen, mnut,
    tmnu) and D/E part names (sbht sbhi sbvd sbvs sbvt sbvi tirt mirt pbar pbsl
    lscl txtk trnk trns tsty tssc tsec tpos bpos …).
  - Part-name→u32LE map tables: 0x45F0C0-0x45F0DC (klrl ljmp lnki kifl kiml →
    0x7C..0x8C) and 0x45F61C-0x45F660 (shbs ihbs thbs dvbs svbs ivbs tvbs tirt
    mirt → 0x7C..0x9C) — PROBABLE part→style-slot maps (relates to S1's C-blob
    flag 0x7C..0x81 finding). Deferred to Batch E.
  - False-positive 4ccs identified (font glyphs wvgw/wwva/DJUZ/JwzZ, float
    tables QNaN/SNaN/eDDQ, Win32 class regs TXET "txt"/lTrP "trp"/ATAD "pah"/
    KRLK) — documented, not identifiers.
- **(b) DONE via A3/B:** prvw child-record mapping = C3 (in progress above);
  blob-B assembly table 0x466DD4 (84 pointers, "TSLC" string @+0xE8 — NOT the
  CLST class) + gOncePtr 0x46698C→0x47B324 → Batch E.

## Carried from S1 (open items 1–9, doc 07 §5.1)
1. WM_PAINT → per-child paint call site → **B2**
2. Per-painter D role-index constants → **E1**
3. Blob B runtime layout; TSLC assembly → **E3**
4. E runtime ink object layout; .fnt → ink → **E2/F1**
5. C-blob field0/2/4; secondary modes → **G1**
6. gStyleStrA/B, gOncePtr, 0x40F220/0x41D390 → **E3**
7. 54th D role; 155 E names vs 192 rows → **E1/E2**
8. Scrollbar/slider per-pixel geometry → **D1/D2**
9. Skin context block 0x46691C remaining fields → **E3**

## Key anchors (verified)
- FourCC integer convention: arg = BE reading (VWIN → 0x5657494E, MENU →
  0x4D454E55); in-memory = ASCII bytes (doc 02 §1.4, CONFIRMED).
- Code constants: `PUSH 0x5657494E` @ 0x408EDD, `PUSH 0x4D454E55` @ 0x4124A1.
- Embedded registry: VWINdoku record @ 0x45F844 region (name @0x45F884,
  8 bytes; 12-byte meta field before it), %VUU class tag @ 0x4605D0,
  KNTR @ 0x46062C; %MNU @ 0x45F900; state names "DisabledBUTN" @ 0x4631D4,
  "Default"+"BUTN" @ 0x463218, "DisabledSEPR" @ 0x4624CC (doc 02 §1.4/§3).
- fileClose (0x41A300) unlinks two registry keys 0x4668D8/0x4668E8 when
  rec[6] set (S1).
- Template tables: tableButtonMethods @ 0x45E140 (8 × {fn, arg}),
  tableLabelMethods @ 0x45C560 (6 × {fn, arg}) — S1.
- Painters: labelWidgetPaint 0x410960, compositeWidgetPaint 0x43BC00,
  iconGridPaint 0x4514C0, listRowPaint 0x446770, buttonWidgetPaint 0x43BF60
  (zero code callers — template-dispatched).
- Skin context block: 0x46691C–0x4669B3 (gStyleRec @0x466954 = C base,
  512-slot table @C+0x40; D colors @0x46695C; E/F/G inks; scale @0x466991/92;
  metrics @0x466994; gStyleMetricBases @0x46703B).
- styleColorGet @ 0x42A140 (54 roles, per-role fallback gStyleDColorsFallback).
- inkBlitCore @ 0x44DFE0 (entry table @ ink+0x10, colour bswap).
- hapTextObj @ 140 B, magic **0xF0168873** @+0x08 (CORRECTED S2 B2; the
  0x01688173 recorded in R0-A.3 was wrong). pv window record (0x120 B) is an
  extended hapTextObj — see doc 18.
- PE: .text VA 0x1000/raw 0x400; .rdata VA 0x53000/raw 0x52000; .data VA
  0x5F000/raw 0x5DA00; .rsrc VA 0x8A000/raw 0x88A00; .idata VA 0x8D000;
  .bss VA 0x8E000. On-disk EXE: /Users/schala/Downloads/AppearanceEdit.exe.

## Ghidra MCP notes (carried)
- Tools reached via codemode `mcp__ghidra__*` (not directly declared this session).
- get_disassembly/get_xrefs_to/get_hexdump/list_functions = sync;
  get_pseudocode may be async (task_id).
- rename_symbols_batch needs CURRENT names; function names lowercase.
- No codemode setTimeout — sequential polls only.- **Batch D1+D2 core — DONE (2026-11-24, doc 17 §18)**: full 20-class
  method table (file-bytes-verified; class objects in .data); HOLD object
  model (invisible geometry anchor; init = hide + optional bswap32 payload
  ext @+0x38/+0x3C); SLDR object model (value @+0x38, max @+0x3C, cursor
  @+0x40, flag byte +0x36 bit0 valueChanged/bit5 ticked; state bits
  0x02/0x40/0x80/0x100/0x1000); sldrEventPress interaction chain;
  widgetSendMsg parent-message protocol (44B struct, [parentClass+0x9C],
  eventId 3 = value-changed); appearance part tables (g_appCurrent
  0x466954 / g_appFallback 0x466950; partOff[131] @appearance+0x40;
  slider entries 110/122/0x6E-0x70/0x72-0x78; appearancePart {dimX,dimY
  u16BE, margins @+0x10..0x13}); prvw slider payloads (50,100,ticked).
  12 renames + 9 protos + 8 comments + 4 structs + 2 data, read-back
  verified. D-late: sldrRender vertical + 0x429860 draw, value math
  vertical branch, state bit 0x04 writer, sbhd anchor consumers.
- **Batch D3 (window creation/VWIN/slots) — DONE (2026-11-24, doc 17 §19)**:
  built-in window chain decoded (windowCreateFromBuiltIn →
  lookupBuiltInRec/%REZ → vuuPayloadParse → widgetAllocInit +
  widgetInstantiate); %REZ = 3 MENU + 6 VWIN windows (efik/emik/epxm/esik
  payloads located + walked); VWIN root + window-own payload layout
  code-verified against all 6 windows; windowObjBase (class WIND, slot
  array at absolute offsets); prvwCtor slot consumption decoded (HOLD
  anchors sbhd..sbvt bound to hsbs/vsbs via 0x4015B0, slots rewritten);
  candidate part tables resolved as instance-table tails. 4 renames, 8
  protos, 10 comments, 1 struct (read-back verified). D-late: 0x4015B0/
  0x401A20/0x401BB0/0x401DA0 bodies, f/f2/u04 semantics, efik..esik ctors.
- **Batch D-late (scrollbar binding + partDraw) — DONE (2026-11-24, doc 17 §20)**:
  sbarBindCreate decoded (76B bound object + shared 196B scrollbar
  controller @0x48E000, lazy init, default words 250/500/50/100); partDraw
  decoded (cBlobHeaderDecode → ext fill / tiled / standard 3-band paths,
  capL/capR edge bands); **CONVERGENCE: appearance parts ARE C-blobs**
  (part table → C-blob part descriptors; S1 pipeline + D part tables are
  the same objects); cBlobPartDesc struct; 5 S1 blit names preserved
  (prototypes re-derived from partDraw call sites). 3 renames + 8 protos +
  8 comments + 3 structs + 2 data (read-back verified). D-late/E: 0x408F10
  (bound-obj ctor), val* word semantics, sbarController's 6 fns, tiled
  branch vs secondary-mode.
- **Batch D deliverables (2026-11-24)**: doc 19 (19-s2-widget-geometry.md)
  written — geometry consolidation (4 coordinate spaces, window outer/
  client geometry, widget raw/scaled, HOLD anchors, SLDR geometry,
  part=C-blob mapping, Rust implications, verification-status matrix).
  tools/research/geo_check.py added — validates %REZ → VWIN descriptor +
  window-own payload + childBase + instance slots for all 6 windows
  (run: ALL OK).
- **Batch D remaining (explicit deferrals, D-late/E)**: mbarSlotGeometry
  0x42EB30 internals; state bit 0x04 writer (SLDR paint gate);
  sldrRender vertical branch (0x42BAC1) + sldrValueFromPointer vertical
  branch (0x42C070) exact start/span; 0x408F10 bound-object ctor;
  sbarController's 6 fns (0x401680..0x4019A0); bound-object val* word
  semantics; scaleQuad factor source global; C1: detach counterpart
  (+0x8C?), list dtor ownership.
- **Batch D-late scrollbar closure — DONE (2026-11-24, doc 17 §21, doc 19 §7)**:
  MODEL CORRECTION — 0x48E000 is a shared CLASS object (g_sbarClass,
  "MySB"), not a stateful controller (memCopy(0x48E000, 0x4660C4 VUU!
  skeleton, 0xC4) + 6 overrides; flag 0x48E0C4 = class-init).
  subWidgetCtor (0x408F10) decoded: raw/scaled quads from anchor+0x0C,
  state/flagByte from flags, attach via class+0x88. val* words CONFIRMED:
  value=250 / max=500 / thumbNum=50 / thumbDen=100 (thumb = ½ track).
  Full geometry decoded: sbarRectsCompute (part selection from
  appearanceObj +0x288/+0x28C/+0x298 h, +0x2D4/+0x2D8/+0x2E4 v; margins
  = C-blob part+0x10..0x13; min-size gate; narrow/wide cap halves;
  thumbLen = max(FISTP(trackLen·tn/td), minThumb); thumbX1 =
  trackStart + FISTP((trackLen−thumbLen)·value/max)), sbarHitTest
  states 0..7 + jump table 0x4530E8 (states 1,3 Δ−, 2,4 Δ+, 5–7 drag;
  wide-case inner-strip inversion = original quirk),
  sbarPressResolve/sbarValueFromPointer exact pointer↔value math (FISTP,
  round-trip consistent), sbarValueOffset clamp, auto-repeat timer
  (Win32 windowless; 200ms → first tick rearm 35ms → 2 steps total;
  oneShot kill; global list 0x466C10 via listAppend/listRemove).
  styleCtx @0x46691C pinned (sbar metrics +0x98/+0x9A/+0x9C at
  0x4669B4/6/8; S1 fields at +0x34..+0x76; 5×7 metrics @+0x78).
  scaleQuad EXACT: dst = src·gScaleNum/gScaleDen (i32, signed; num/den
  = u8 @0x466991/92 from HAP header 0x0C/0x0D — D-late question
  RESOLVED). appearanceObj extended 608B → 744B (0x2E8).
  Ghidra: 22 renames, 20 protos, 21 comments, 5 structs (1 replaced:
  sbarBindObj; 1 renamed: sbarClassObj; 3 new), 1 data type applied;
  project saved.
- **Batch D-late SLDR/state/mbar closure — DONE (2026-11-24, doc 17 §22, doc 19 §5/§8)**:
  sldrWidgetInit payload (value u32BE→+0x38, max u32BE→+0x3C, bit0→ticked
  0x20); 35-case part dispatch (tables 0x4577C4/0x457738, flagByte&0x23);
  render term FIST(trackLen×max/value) (value<max) else trackLen —
  byte-verified, vertical branch matched; correction idiom proven dead.
  **OPEN anomaly**: screenshot mid-track thumb implies value/max; held
  open per D-late constraint (no implementation-ready claim).
  sldrPointerToValue exact H/V formulas + clamps; sldrValueFromPointer
  snap-band + grab offset (widget+0x40); press/move/release state bits
  (0x40/0x80/0x100, 0x1000, flagByte bit 0 armed; cursor stubs RET-only).
  **State bit 0x02/0x04 writer = widgetHoverState (0x413450)** via
  widgetStateSet(mask=0x7): non-current children 0x2, current child 0x6;
  SLDR press gate 0x06 = "pointer over this widget". mbarSlotGeometry:
  8 sub-items per slot @+0x40, width byte +0x4, 5px pad, count +0x3D.
  partBlitAt = generic 14-call-site blit primitive. Ghidra: 7 renames,
  7 protos, 12 comments (read-back verified, project saved).
- **Batch D-late remaining (reduced list)**:
  1. SLDR max/value render anomaly — runtime trace or second build
     (BLOCKER for SLDR implementation-ready status; evidence recorded in
     doc 19 §5.5 / doc 17 §22.4).
  2. State bit 0x20 consumer audit (framework-wide; SLDR audited — no
     0x20 use; only per-function register-mediated TESTs exist, no
     direct [mem+0x34] imm patterns in .text).
  3. C1: detach counterpart (+0x8C?), list dtor ownership, remaining
     widgetInstantiate arg semantics.
  4. 0x401680 (sbarMethCancelTimer) triggering framework event — minor.
  5. `flags & 1` tiled branch = secondary-mode C-blob? — Batch G.
  Then proceed to **Batch E** (appearance lifecycle) — owner-approved.
- **Batch E1 — DONE (2026-11-24, doc 20, Ghidra saved)**:
  appearance object = the C section itself (skinInstall stores image
  pointers into the styleCtx; no separate parse/alloc; owner+4 owns the
  installed image, freed on replace). 131-vs-512 RESOLVED: 512 = fixed
  directory capacity (all 39 corpus v1 + built-in verified), 131 =
  Batch-D truncation assumption; partOff[146/147/150/165/166/169] are the
  D-late "sbar fields" (appearanceObj struct corrected to 0x840 B).
  Section map C/D/E/F/G; D = 54 (v2) / 204 (v1) roles, [00][RR][GG][BB],
  no bswap, 14-site consumer matrix; E/F/G = named record pools
  {count, offsets, records}; inkNameLookup (0x42D3F0) decoded incl.
  "data"/"folder/standard" names from .rdata; full lifecycle (startup/
  load/apply/reset; doc list 0x45F820; modified flag +0x19D). D-late
  correction: sbar metrics +0x98/0x9A/0x9C = matrix cells [16]/[17]/[18].
  Ghidra: 7 data renames/labels, 3 fn renames, 7 protos, 14 comments,
  2 structs replaced + 1 new (all read-back verified).
- **Batch E remainder (E2/E3) — PENDING**:
  1. ~~0x40F220 / 0x41D390~~ **DONE**: winMetricsResync (SetWindowPos /
     IsWindowVisible / InvalidateRect per window) + cursorCacheReset
     (GetCursor/DestroyCursor, 20-slot table 0x466C28); doc 20 §11.4.
  2. E2: cmpFn hash fns 0x43F510/0x43F9E0; F ink bitmap block sub-struct;
     E record flags +0x0C/+0x0E + pixel bpp; G slot→cursor-name mapping;
     0x42E7D0/0x40C810/0x41D400 internals; corpus v1 E/F/G layout +
     "folder/standard" corpus presence.
     **IKON binding DONE (doc 20 §12):** ikonWidgetInit/ikonPaint decoded;
     icon index resolves via %REZ "IKON" tag (lookupBuiltInRecSoft);
     sentinel 1 = 'icon missing' dither; IKON = styleColorGet(4) consumer.
     **E/F/G record formats + built-in name lists CONFIRMED (doc 20 §11):**
     E = 35 %IKN icons (dir[0] reserved empty); F = 24 named %IKN inks
     (data, font/, text/, audio/, image/, video/, folder/, volume/…, data/
     truncated, alias/unattached, executable/…; dir[0] dummy = count;
     "folder/standard" ABSENT from built-in → gInkF2 = NULL); G = 19 %MSI
     cursors (S1-decoded, re-verified).
- **BATCH E — COMPLETE (2026-11-24, doc 20 §13):** all six priorities done;
  priority 6 closed at the documented E3 boundary (items 2–3 below remain
  the E3 backlog). Ghidra across the batch: 7 data renames/labels, 8 fn
  renames (inkNameLookup, bmpFillRectFromRect, pstrRFindChar,
  winMetricsResync, cursorCacheReset, ikonWidgetInit, ikonHandlerRet,
  ikonPaint), 13 prototypes, 18 comments, 2 structs replaced
  (appearanceObj 0x840, styleCtx 0xCC) + 1 new (hapNamedPool). Next:
  **Batch F (font pipeline).**
  3. E3: gOncePtr table @0x47B324; styleCtx +0x00..+0x33, +0x70,
     +0xBE..+0xC7; 0x401000/0x401290 (doc create), 0x408720 (doc dtor —
     C1 "detach" adjacency), 0x40C5C0 (notify); hapParse full decode
     (doc-model side); 26 g_appCurrent consumer-site matrix.
  E anchors: 26 g_appCurrent consumers (0x41DC25, 0x429DAE, 0x429E9D,
  0x42A185, 0x42A20B, 0x42A789, 0x42A8DE, 0x42AB3B, 0x42AC42, 0x42AD84,
  0x42B6FE, 0x42B861, 0x42BD20, 0x42C2DE, 0x42C422, 0x42C611, 0x42CA4B,
  0x42CDA8, 0x42CF07, 0x42D09E, 0x42D736, 0x42DCBE, 0x42DF5D, 0x42E434,
  0x42E83E, 0x42E925); g_appFallback consumer 0x428D1D; appearanceReset-
  Default/skinInstall (0x428C70)/appearanceLoadInstall (0x402FA0)/
  hapParse (0x402900)/hapLoadEntry (0x4036B0); styleColorGet (0x42A140,
  54 roles); inkBlitCore (0x44DFE0); gInkF/gInkF2 (0x466974/0x46697C,
  was gStyleStrA/B); 0x40F220/0x41D390 (skinApply chain); assembly table
  0x466DD4.

## BATCH F — font & text pipeline (2026-11-24, doc 21)

**CORE COMPLETE (F1–F6, F9, F10; F7/F8 partial).** Findings:
- .fnt v2 header 64B (size = u32BE — corpus-inventory LE note corrected;
  no author field exists — earlier "Haxial" note disproven; embedded font
  true sizes 0x3C30/0x4D18/0x25EC/0x2868 pool-junction-verified, earlier
  0x184D/0xEC25/0x6828 were byte-swap artifacts);
  faceCount = blob+0x07 (u8); faces @0xB8+i*0x54 {count @+0xB, table
  u32BE @+0xC = 0x10C, name pstr @+0x14}; glyph rows 16B @ tableOff:
  char/byte0, charID u32BE @+4, w/h/x/y @+8..+B, u32BE @+0xC (pool offset
  ≤0xFFFF else first-byte advance); inline vs external 1bpp pool
  (Lies: 0x2AE4–0x3233 ASCII, 0x323D–0x40EB extended; dashed-line + 8×8
  digit glyphs decoded visually).
- **UTF-8 CONFIRMED** (utf8ReadChar 0x43B6F0 = full strict decoder,
  0xFFFD fallback). No GDI text APIs in pipeline — pure DIB blits.
- Metrics derive from glyph records: ascent = ref rec byte0, line height =
  byte0+byte1 (fontRecAscent/Height), advances per-glyph, fontFitWidth
  truncation w/ half-advance term. No separate metrics table.
- inkBlitCore: row = base + cp*16 (cp<0x100); fontGlyphSearch binary
  search (cp≥0x100, keys bswap u32BE[row+0], range [0x100,cp-1]); default
  row = base + 0x1A0 (row 13); missing = byte[row+0xC]==0 && cp≠0x0A;
  budget guard (bswap u32BE[row+4], w*h+charID) aborts degenerate fonts;
  1bpp MSB-first rows → 1bpp surface → 32bpp DIB (labelPaint temp-bitmap
  path, S1-carryover).
- S2 runtime font object: magic 0x6ABA021A @+0x30; +0x34 = blob-equiv,
  +0x38 = recOff-equiv (retains refs into serialized data, not a
  reconstructed model). g_appFont (0x46698C) = Myoklonika via skinInstall
  tail + g_appFontInit (0x466990).
- fontServiceTable (anchor 0x45EA50): {fn, serviceId} pairs; font services
  0x0045B814–0x0045B859+; explains missing xrefs on font strings
  (ID dispatch, no direct calls).
- Ghidra: 24 renames, 9 prototypes, 9 comments (incl. inkBlitCore
  correction), 0 new structures (row layout documented in doc 21 §1.3 +
  tools/research/fnt_inspect.py instead — evidence-blocked, not deferred
  sloppily). All read-back verified; project saved.

**F-remainder backlog (doc 21 §12):**
- F-1 locate .fnt file loader / S2 object constructor (needs F-3 dispatcher)
- F-2 row-array base origin ([EBP-0x5C]) vs 0x10C; walk stride 0x18 vs 0x10;
  extended-region alignment (corpus keys 4B off naive)
- F-3 service-table full extent + ID dispatcher (cross-cutting)
- F-4 0x444600 (row-value) + 0x44E470 (fit helper) internals
- F-5 fontTextDraw/fontMetricsGet per-parameter gate (Batch V unless hit)
- F-6 w/h origin for pool glyphs (w=0/h=0 rows); inline-pixel row semantics
- F-7 multi-line wrapping (interaction layer, beyond F boundary)
- F-8 per-appearance font selection (corpus .hap fonts absent — E3-11)

**Batch G — DONE (2026-11-24, doc 22, Ghidra saved):**
- C-blob file layout closed: 20B header (w/h u16BE, flags, bpp, palCount-1,
  transIdx, field0 clearColour u32BE @+8, caps @+0xC..+0xF, field2 margins
  u32BE @+0x10) + 12B ext block @+0x14 iff flags & 0x10 (mode @+0x14,
  gradA 3B @+0x15, gradB 3B @+0x18, pad, insets 4B @+0x1C) + palette +
  pixels. Palette precedes pixels; stride formula both tables.
- field0 = surface clear/fill COLOUR (not a flag): 3 consumer families
  (widgetBaseFill, bmpSetCellState, mbarDrawTitleItem) + editor verbatim
  copy; 100 distinct corpus values (0x00 black 3012, 0xFFFFFF white 169).
- field2 = margins {L,T,R,B}: sldrPartLookup, sbarRectsCompute, ~12
  painters + editor remap into gradient (partToSkinDib); 215 distinct
  values, non-zero concentrated in scrollbar parts 146-177/204-223.
- flags: bit0 = tiled/transpath (2232/4243, 53%), 0x10 = ext (18, built-in
  v2 only); bits 2/4/8 (secondary row-bpp, 0x441F70) = ZERO corpus
  occurrences → dead/legacy unproven (G-8).
- Renderers: partDraw H 3-band, partDrawV V 3-band (0x429A20),
  nineSliceBlitC 9-region (center = sampled pixel solid fill, NOT a
  region), partBlitRepeat/V tiled centers (one row/col replicated solid),
  nineSliceStretchH/V plain centers, extContentFill gradients (mode 1 H,
  mode 2 V; per-channel integer lerp; /128 blend in hlineAlpha/vlineAlpha:
  0 opaque, 1..254 blend, 255 skip), blitDecodeTiled whole-blob texture
  tiling (w==1 → horizontal stripes).
- DIB engine: surface magic 0xF4DA120B @+0x44; bmpBlitToSurface/bmpBlitAlpha
  32-entry bpp tables (valid 1/2/4/8/16/25/32; 25bpp blit-only quirk);
  alpha thunks → 0x450450 (SHARED with font 1bpp blit — Batch F family
  preserved, dual-use documented) / 0x4508C0 / 0x450C10 / 0x450DC0 /
  0x451060 / 0x451110 / 0x4511A0; dibSamplePixel(Trans) (col,row) bounds
  + palette @+0x1C / 555→888 tables 0x479B48/BC8/C48; error 0x10002.
- mbar title painters: mbarTitleBackground (0x42AB30; parts 255 tiled base
  + 256 nine-slice overlay), mbarDrawTitleItem (0x42AC00; 3 states →
  base 433/434/435 + overlay 261/262/263 + field0 text bg + 0x426E00 text).
- Editor: hapCBlobParse/hapCSectionRead(0xAF=175)/Write/Size verbatim;
  partRecordBuild (0x406BD0) 32B record {field0 @+0, caps @+9..+0xC,
  margins @+0xD..+0x10}; partToSkinDib (0x406810) margin→gradient remap
  (PROBABLE, G-2).
- Ghidra: 9 renames, 9 prototypes, 21 comments (incl. 2 stale S1
  corrections: "116B decode" → 32B cBlobDecode, "extColour u16BE" → mode
  byte + 3B colours), 4 structures (cBlobFileHeader 20B, cBlobExtBlock
  12B, cBlobDecode 32B, partRecord32 32B partial) relocated to root DTM
  category. cBlobDecode→partDraw local_78 **APPLIED + saved** (G-9 resolved);
  infer_structure_from_variable failed (split scalars).
  All renames/protos read-back verified.
- Backlog G-1..G-9 in doc 22 §10 (part table mapping G-4 largest).

**Next: Batch V** (final audit & readiness) — the audit document will be
`23-s2-evidence-closure-and-readiness.md` (doc 22 was taken by Batch G).
