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
- **A1 (MENUscal record) — structure recovered from evidence (code-level, 2026-11-19):**
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

### In progress
- B2 (pseudocode tasks for 0x408750/0x408B60 pending; class registry 0x4625xx
  mapping; class lookup 0x409150)

### Pending
- (all other batches)

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
- hapTextObj @ 140 B, magic 0x01688173 @+0x08 (R0-A.3).
- PE: .text VA 0x1000/raw 0x400; .rdata VA 0x53000/raw 0x52000; .data VA
  0x5F000/raw 0x5DA00; .rsrc VA 0x8A000/raw 0x88A00; .idata VA 0x8D000;
  .bss VA 0x8E000. On-disk EXE: /Users/schala/Downloads/AppearanceEdit.exe.

## Ghidra MCP notes (carried)
- Tools reached via codemode `mcp__ghidra__*` (not directly declared this session).
- get_disassembly/get_xrefs_to/get_hexdump/list_functions = sync;
  get_pseudocode may be async (task_id).
- rename_symbols_batch needs CURRENT names; function names lowercase.
- No codemode setTimeout — sequential polls only.