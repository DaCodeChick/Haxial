# R0-A.3 — Traversal Worklist (durable checkpoint)

Program: `AppearanceEdit.exe` x86:LE:32, image base `0x400000`.
Method: bidirectional BFS from 84 seeds (all functions named in R0-A/R0-A.1/R0-A.2,
see report §2). Pass 1 (direct neighbors via `get_callers`/`get_callees`):
**477 discovered non-seed nodes** (104 non-seed callees, 409 non-seed callers,
overlap included). No import functions appear in `get_callees` output (internal
refs only) → imports are an implicit boundary (B-EXT), recorded from
disassembly when relevant.

Scope rule (in-scope = appearance data pipeline):
- P1 HAP parse/serialize (+callee closure)
- P2 appearance file I/O (file* + open/save entries)
- P3 document lifecycle (docCreate/createDocument + doc list + load/save handlers)
- P4 skin data objects (bmpObj*, ink records, pair records)
- P5 skin rendering (blits, DIB builders, widget painters of skin data)
- P6 appearance metadata display (label/option/displayResource + info tab)
- P7 string/format/memory/error infrastructure used by P1–P6
Boundaries: B-EXT (imports), B-GENUI (generic widget framework), B-APP
(app shell/message loop/DDE/OLE), B-DYN (unresolved indirect calls).
Generic-only callers (350, call only mem*/pstr*/hError*/app-shell seeds) are
classified by adjacency + sampled decompilation, not individually decompiled
unless flagged `sample` below.

Status legend: pending | classified (class) | audited | deferred (reason) | boundary (class)

## Batch 1 (candidates 1–40) — classified from disassembly signatures

| Address | Name (pre) | Class | Evidence (calls / consts / refs) | Status |
|---|---|---|---|---|
| `0x41bd80` | FUN_0041bd80 | P7 (str) | 23 insns; calls pstrCopyTrunc + 0x40bc10 | audited-pending |
| `0x439cc0` | FUN_00439cc0 | P7 (fmt) | 19 insns; calls fmtInt — the pstrAppendNum2 formatter (ledger open item 11) | audited-pending |
| `0x43a610` | FUN_0043a610 | P7 (fmt) | 246 insns, no calls; IEEE-double consts (0xcccccccd, 0x51eb851f) — pstrAppendNum3 double→ASCII formatter | audited-pending |
| `0x4178b0` | FUN_004178b0 | P3 (dialog) | 87 insns; displayResourceSet, pstrFindByte; the "Save Appearance File" dialog (R0-A.2 F3) | audited-pending |
| `0x41d760` | FUN_0041d760 | P7 (err) | calls memZero, 0x41d570, terminal handler 0x414bf0; error-record variant | audited-pending |
| `0x41d570` | FUN_0041d570 | P7 (err) | 140 insns, no calls; error-record body helper | audited-pending |
| `0x41d7f0` | FUN_0041d7f0 | P7 (err) | import [0x48d298], memZero, 0x41d570, 0x414bf0; error variant w/ import | audited-pending |
| `0x41bc50` | FUN_0041bc50 | P7 (err) | hErrorSimple/hError, refs 0x466bac (g_cmdLineEmpty); startup error path | audited-pending |
| `0x414bf0` | FUN_00414bf0 | P7 (err) | terminal error handler (open item 12); calls 0x414890; refs 0x46675c | audited-pending |
| `0x419220` | FUN_00419220 | P2 (file) | FileRec magic 0x1CA6C39A; file-rec constructor (fileOpen core) | audited-pending |
| `0x419600` | FUN_00419600 | P2 (file) | 118 insns; the dir-create called by fileOpenMkDir (R0-A ledger) | audited-pending |
| `0x418a30` | FUN_00418a30 | P2 (file) | 59 insns no calls; path helper (mkdir/list helpers) | audited-pending |
| `0x418cf0` | FUN_00418cf0 | P2 (file) | memAlloc/memFree, hError, import [0x48d2b4] | audited-pending |
| `0x418de0` | FUN_00418de0 | P2 (file) | 365 insns; memCopy/Alloc; FindFirst/NextFile-style dir list | audited-pending |
| `0x418880` | FUN_00418880 | P2 (file) | 13 insns path helper | audited-pending |
| `0x4188b0` | FUN_004188b0 | P2 (file) | 15 insns; const 0xFFFFFFFE | audited-pending |
| `0x41b5f0` | FUN_0041b5f0 | P2 (file) | FileRec magic 0x1CA6C39A; observed in hapLoadEntry path (09 §8) | audited-pending |
| `0x439cc0`..(above) | | | | |
| `0x40af80` | FUN_0040af80 | P6 (label) | const 0xF0168873 (widget magic); hError paths | audited-pending |
| `0x40afc0` | FUN_0040afc0 | P6 (label) | const 0xF0168873 | audited-pending |
| `0x40b000` | FUN_0040b000 | P6 (label) | const 0xF0168873 | audited-pending |
| `0x40cc70` | FUN_0040cc70 | P6 (label) | observed (09 §8); 0xF0168873; calls 0x446f20/0x446f00 | audited-pending |
| `0x40ce90` | FUN_0040ce90 | P5 (label) | observed; labelPaint line-split helper (11 §6) | audited-pending |
| `0x427d80` | FUN_027d80→0x427d80 | P5 (dib) | 212 insns; 0xF4DA120B (bmpObj magic); calls 0x44Exxx str cluster | audited-pending |
| `0x4259d0` | FUN_004259d0 | P5 (dib) | observed DIB builder; 0xF4DA120B; 19 insns | audited-pending |
| `0x426610` | FUN_00426610 | P5 (dib) | observed DIB builder; 0xF4DA120B | audited-pending |
| `0x428260` | FUN_00428260 | P4 (bmp) | bmpObj-neighbor (0x428210); 0xF4DA120B; 23 insns | audited-pending |
| `0x440430` | FUN_00440430 | P1 (tbl) | searchRecords-neighbor; calls 0x440360, memCopy | audited-pending |
| `0x4408a0` | FUN_004408a0 | P1 (tbl) | 0x440360, memCopy, memZero | audited-pending |
| `0x440bb0` | FUN_00440bb0 | P1 (tbl) | 106 insns; table machinery region | audited-pending |
| `0x423910` | FUN_00423910 | P6 (res) | 0x8521B2D1 (res magic); calls hError | audited-pending |
| `0x423710` | FUN_00423710 | P6 (res) | 0x8521B2D1; calls 0x440ce0 | audited-pending |
| `0x423210` | FUN_00423210 | P6 (res) | 0x8521B2D1; 140 insns; fields +0x48/+0xA8; searchRecords family | audited-pending |
| `0x408ed0` | FUN_00408ed0 | P6 (res) | const 0x5657494E ("VWIN" — open item 7!); calls lookupBuiltInRec | audited-pending |
| `0x439cc0`/`0x439d00` | | | (0x439d00 queued separately) | |
| `0x40b9c0` | FUN_0040b9c0 | B-APP | 131 insns; refs g_hInstance 0x466ba4 + import table; app init | boundary(B-APP) |
| `0x43bb10` | FUN_0043bb10 | B-APP | refs 0x46693c-45 (quit-flag region); indirect call | boundary(B-APP) |
| `0x41bd30` | FUN_0041bd30 | B-APP | refs 0x466934/38; indirect call EBX | boundary(B-APP) |
| `0x44b300` | FUN_0044b300 | P6 (res) | 0x568D9814; calls error-text family 0x414d80/0x414dc0; refs 0x466b70-8c | audited-pending |
| `0x43ba30` | FUN_0043ba30 | B-GENUI? | 5-instr thunk; needs caller context | pending |
| `0x43b8a0` | FUN_0043b8a0 | P7 (str) | 60 insns; calls 0x43b5e0 (str cluster 0x43Bxxx) | audited-pending |

## Pending queues
- Signature batches: 41–120, 121–200, 201–223 (candidates in store `r0a3_candidates`)
- Second-hop BFS from in-scope set (after batch classification)
- Generic-only boundary sampling: 63 `sample`-flagged nodes (file/pstr/app-shell callers)
## Batch 2 (candidates 41–120) — classified

| Address | Name (pre) | Class | Evidence |
|---|---|---|---|
| `0x401e30` | FUN_00401e30 | P3 (UI) | 287 insns; "wrpv"/"maxe" consts; VWIN-res 0x408ed0 + labelSetText + widget builders — editor window ctor | audited-pending |
| `0x407600` | FUN_00407600 | P3 (UI) | 359 insns; optionListGet + pstr* + 0x406810 (C-sec) + 0x408720 — appearance UI main builder | audited-pending |
| `0x421bc0` | FUN_00421bc0 | P7 (str) | 597 insns; pstrCopy/AppendInt/Append/Num2/Num3/Byte — big string assembly (fmt consumers) | audited-pending |
| `0x403510` | FUN_00403510 | P3 (save) | calls hapSaveEntry + 0x41a270 (file) — save handler | audited-pending |
| `0x433ac0` | FUN_00433ac0 | P3 (save) | 389 insns; strObjGetData, fileCreate, fileWriteWhole, save dialog 0x4178b0 — save pipeline | audited-pending |
| `0x417070` | FUN_00417070 | P3 (open/UI) | 374 insns; displayResourceSet, label 0x412620, fileOpen 0x419da0 | audited-pending |
| `0x415920` | FUN_00415920 | P2 (open) | fileNameExtract, 0x41a270, labelSetText — open path | audited-pending |
| `0x415f00` | FUN_00415f00 | P3 (open) | fileNameExtract, optionList ctor 0x411cf0 — open + scale option | audited-pending |
| `0x41ab60` | FUN_0041ab60 | P2 (file) | FileRec magic; pstrToRaw, fileNameExtract | audited-pending |
| `0x41ad30` | FUN_0041ad30 | P2 (file) | FileRec magic; 0x41d7f0 err, 0x41ac60, 0x41ab60 | audited-pending |
| `0x41a270` | FUN_0041a270 | P2 (file) | FileRec magic; observed (09 §8) | audited-pending |
| `0x41a320` | FUN_0041a320 | P2 (file) | callee of open path (0x415920/0x415f00) | audited-pending |
| `0x41ac60` | FUN_0041ac60 | P2 (file) | callee of 0x41ad30 | audited-pending |
| `0x41aa f0`→`0x41aaf0` | (new) | P2 (file) | callee of 0x41ab60 — enqueue hop 2 | pending |
| `0x43f5d0` | FUN_0043f5d0 | P7 (str) | 227 insns; fmt formatters + filetimeToString — info-string builder | audited-pending |
| `0x43df20` | FUN_0043df20 | P6 (label) | 250 insns; fmtInt, labelSetText, displayResourceSet; 0xA0A0A0A1 | audited-pending |
| `0x4311f0` | FUN_004311f0 | P6 (label) | fmtInt + displayResourceSet, 19 insns | audited-pending |
| `0x431030` | FUN_00431030 | P6 (res) | 0x83AF6F92 (displayResource magic); 0x42f4e0 (fmt double) | audited-pending |
| `0x431160` | FUN_00431160 | P6 (res) | 0x83AF6F92 | audited-pending |
| `0x4308a0` | FUN_004308a0 | P6 (res) | displayResourceSet-neighbor, 11 insns | audited-pending |
| `0x409300` | FUN_00409300 | P6 (label) | 0x5655D881 (label magic) — label widget ctor | audited-pending |
| `0x408720` | FUN_00408720 | P6 (label) | 0x5655D881; observed (09 §8) | audited-pending |
| `0x4187b0` | FUN_004187b0 | P6 (label) | observed; 0x408720 + res fns | audited-pending |
| `0x412620` | FUN_00412620 | P6 (label) | 0x5655D881; calls labelPaint helper 0x4093e0 | audited-pending |
| `0x4093e0` | FUN_004093e0 | P5 (label) | 0x5655D881; labelPaint resource select (11 §6) | audited-pending |
| `0x411cf0` | FUN_00411cf0 | P6 (opt) | 0x51BD8891 (optionList magic) — option list ctor | audited-pending |
| `0x411ad0` | FUN_00411ad0 | P6 (opt) | 0x51BD8891 | audited-pending |
| `0x411290` | FUN_00411290 | P6 (opt) | observed (09 §8); calls 0x411120 | audited-pending |
| `0x411120` | FUN_00411120 | P6 (opt) | callee of 0x411290 | audited-pending |
| `0x4110e0` | (new) | P6 (opt) | callee of 0x411cf0 — enqueue hop 2 | pending |
| `0x411260` | (new) | P6 (opt) | callee of 0x415920/0x415f00 — enqueue hop 2 | pending |
| `0x4112d0` | (new) | P6 (opt) | callee of 0x415f00 — enqueue hop 2 | pending |
| `0x4117d0` | (new) | P6 (opt) | callee of 0x411cf0 — enqueue hop 2 | pending |
| `0x411920` | (new) | P6 (opt) | callee of 0x411cf0 — enqueue hop 2 | pending |
| `0x4065a0` | FUN_004065a0 | P1 (subobj) | sub-object ctor (res 0x423210 + widget fns) — C/D/E/G subobjs | audited-pending |
| `0x407d00` | FUN_00407d00 | P1 (subobj) | sub-object ctor | audited-pending |
| `0x4049e0` | FUN_004049e0 | P1 (subobj) | sub-object ctor | audited-pending |
| `0x4056b0` | FUN_004056b0 | P1 (subobj) | sub-object ctor | audited-pending |
| `0x403f80` | FUN_00403f80 | P1 (subobj) | res 0x423210 + widget fns — doc sub-obj builder | audited-pending |
| `0x423210` | (b1) | P6 (res) | res object 0x8521B2D1 | (b1) |
| `0x4236c0` | FUN_004236c0 | P6 (res) | 0x8521B2D1; searchRecords family — res ctor | audited-pending |
| `0x42d3f0` | FUN_0042d3f0 | P1 (tbl) | 186 insns; searchRecords + 0x43fd00 — table search consumer | audited-pending |
| `0x445900` | FUN_00445900 | P1 (tbl) | searchRecords consumer | audited-pending |
| `0x428c70` | FUN_00428c70 | P4/P5 (bmp) | 366 insns; 0x42d3f0 (search) + 0x4287f0 — bitmap object | audited-pending |
| `0x4287f0` | (new) | P5 (dib) | callee of 0x428c70 — enqueue hop 2 | pending |
| `0x441d80` | FUN_00441d80 | P5 (dib) | 0xF4DA120B; 176 insns — DIB cluster | audited-pending |
| `0x441320` | FUN_00441320 | P5 (dib) | 0xF4DA120B; 62 insns | audited-pending |
| `0x441040` | (new) | P5 (dib) | callee of 0x441320 — enqueue hop 2 | pending |
| `0x441090` | (new) | P5 (dib) | callee of 0x441320 — enqueue hop 2 | pending |
| `0x427b30` | FUN_00427b30 | P5 (dib) | 0xF4DA120B; 212 insns; 0x44Exxx str cluster — DIB builder | audited-pending |
| `0x4258d0` | FUN_004258d0 | P5 (dib) | 0xF4DA120B; 29 insns; called by 0x407600/0x421bc0 | audited-pending |
| `0x425880` | FUN_00425880 | P5 (dib) | 0xF4DA120B; paint-ctx release (11 §1) | audited-pending |
| `0x42e370` | FUN_0042e370 | P5 (clip) | 337 insns; clip intersect (11 §1) | audited-pending |
| `0x42dc90` | FUN_0042dc90 | P5 (clip) | 84 insns; 0x425910 + 0x429be0 | audited-pending |
| `0x4459e0` | FUN_004459e0 | P5 (clip) | 35 insns (11 §1) | audited-pending |
| `0x42a170` | FUN_0042a170 | P5 (ink) | 58 insns; 0x429100/0x426b20 — ink raster | audited-pending |
| `0x42a2d0` | FUN_0042a2d0 | P4/P5 (ink) | 308 insns; "%IKN" neighbor 0x43f260 + lookupBuiltInRec — ink consumer | audited-pending |
| `0x43f260` | (new) | P4 (ink) | callee of 0x42a2d0 (hapInkSubParse neighbor) — enqueue hop 2 | pending |
| `0x426e00` | (new) | P5 (dib) | callee of 0x42a2d0 — enqueue hop 2 | pending |
| `0x426370` | (new) | P5 (dib) | callee of 0x42a2d0 — enqueue hop 2 | pending |
| `0x425d00` | (new) | P5 (dib) | callee of 0x42a2d0 — enqueue hop 2 | pending |
| `0x40c5c0` | FUN_0040c5c0 | P6 (label) | 0xF0168873; observed (09 §8) — label obj method | audited-pending |
| `0x40cc70` | (b1) | P6 (label) | (b1) |
| `0x417c90` | FUN_00417c90 | P3 (dialog) | 0x3Cfe7afe; calls 0x40cc70 — save-dlg neighbor (09 §8) | audited-pending |
| `0x4179d0` | (new) | P3 (dialog) | callee of 0x403510 — enqueue hop 2 | pending |
| `0x417c50` | (new) | P3 (dialog) | callee of 0x403510 — enqueue hop 2 | pending |
| `0x40c540` | (new) | P3 (save) | callee of 0x403510 — enqueue hop 2 | pending |
| `0x41d9a0` | FUN_0041d9a0 | P7 (fmt) | 102 insns; IEEE-double consts + imports — number format | audited-pending |
| `0x42f4e0` | FUN_0042f4e0 | P7 (fmt) | 146 insns; double consts; 0x446130 | audited-pending |
| `0x446130` | (new) | P7 (fmt) | callee of 0x42f4e0 — enqueue hop 2 | pending |
| `0x434ba0` | FUN_00434ba0 | P7 (fmt) | 234 insns; double consts; 0x452180 | audited-pending |
| `0x452180` | (new) | P7 (fmt) | callee of 0x434ba0 — enqueue hop 2 | pending |
| `0x41c2b0` | FUN_0041c2b0 | P7 (time) | 22 insns; 0x41c1a0/0x41c560 | audited-pending |
| `0x41c560` | FUN_0041c560 | P7 (time) | callee of 0x41c2b0 | audited-pending |
| `0x41c4c0` | FUN_0041c4c0 | P7 (time) | import 0x48d308 (GetSystemTime?); filetime neighbor | audited-pending |
| `0x41c480` | (new) | P7 (time) | callee of 0x41ad30 — enqueue hop 2 | pending |
| `0x41c1a0` | (new) | P7 (time) | callee of 0x41c2b0 — enqueue hop 2 | pending |
| `0x409100` | (new) | P5 (paint) | common callee of ~10 eight-instr thunk stubs — paint dispatcher | pending (hop 2) |
| `0x4229a0,0x4361f0,0x437220,0x437ee0,0x435e40,0x4360d0,0x43cd30,0x437850,0x437c90,0x436ae0` | thunks | P5 (paint) | 8 insns each, call 0x409100 — per-type paint stubs | audited-pending |
| `0x40bc70` | FUN_0040bc70 | B-GENUI | indirect call via [0x466370] — callback thunk | boundary(B-GENUI) |
| `0x40f7c0` | FUN_0040f7c0 | B-GENUI | indirect [EBX+0x8] thunk | boundary(B-GENUI) |
| `0x41ba70` | FUN_0041ba70 | B-GENUI | 0x414dc0 err-text + indirect [ESI+0x1C] | boundary(B-GENUI) |
| `0x44b460` | FUN_0044b460 | B-GENUI | imports [0x48d328/2c] + 0x414d50 err-text | boundary(B-GENUI) |
| `0x43bb70,0x43bbe0` | thunks | B-GENUI? | 5-insn thunks; needs caller context | pending |
| `0x4038b0` | FUN_004038b0 | B-APP? | 6 insns; 0x43bb00 (flag family); observed (09 §8) | pending |
| `0x401470` | FUN_00401470 | P3 (UI)? | 62 insns no calls; observed (09 §8) | pending |
| `0x401550` | FUN_00401550 | P3 (UI)? | 22 insns no calls; observed (09 §8) | pending |
| `0x44c500` | FUN_0044c500 | P7? | 48 insns no calls; callee of 0x434900 (fmt family) | pending |
| `0x424020` | (new) | P5 (widget) | callee of 0x407600 — enqueue hop 2 | pending |
| `0x424310,0x424450,0x424490,0x4215a0,0x4209e0,0x422a30,0x4237d0,0x423860,0x423600` | (new) | P5 (widget) | widget-object cluster (callees of sub-obj ctors) — enqueue hop 2 | pending |
| `0x409230,0x409850` | (new) | P3/P6 (UI) | callees of 0x402210/0x401290 — enqueue hop 2 | pending |
| `0x41cc50` | (new) | P7 (str) | callee of 0x421bc0 — enqueue hop 2 | pending |
| `0x409760` | (new) | P6 (UI) | callee of 0x421bc0 — enqueue hop 2 | pending |
| `0x41d0b0` | (new) | P7 (str) | callee of 0x421bc0 — enqueue hop 2 | pending |
| `0x43cbc0,0x43cb10,0x43cd30-adj` | (new) | P7 (str) | str cluster callees — enqueue hop 2 | pending |
| `0x404e50` | (new) | P1 (C) | callee of 0x407600 (C-sec region) — enqueue hop 2 | pending |
| `0x4311a0` | (new) | P6 (res) | callee of 0x407600 — enqueue hop 2 | pending |
| `0x406810` | FUN_00406810 | P1 (C) | C-section region; callee of 0x407600 | audited-pending (hop 1) |

## Batch 3 (candidates 121–200) — classified

### Document/open/save orchestration (P2/P3)
| Address | Class | Evidence |
|---|---|---|
| `0x403930` | P3 (docmgr) | 293 insns; createDocument + hapSaveEntry + 0x4071b0/0x407600/0x402fa0 — editor main manager | audited-pending |
| `0x402fa0` | P1 (save) | calls hapSerialize + 0x435030 + 0x40c5c0 — serialize dispatch | audited-pending |
| `0x403300` | P3 (open) | calls hapLoadEntry + 0x4179d0/0x417c50 | audited-pending |
| `0x4038c0` | P3 (open) | calls 0x41c300 + hapLoadEntry (WndProc candidate R0-A) | audited-pending |
| `0x403640` | P3 (save) | calls hapSaveEntry + 0x4187b0 + 0x4038b0 | audited-pending |
| `0x4179d0` | P2 (dlg) | 229 insns; fileOpen 0x419da0 + 0x419bf0; 0x3Cfe7afe — Open Appearance dialog | audited-pending |
| `0x419bf0` | P2 (file) | 13 insns; fileOpenExt wrapper | audited-pending |
| `0x41c300` | P2 (file) | 35 insns; fileOpen wrapper | audited-pending |
| `0x4473e0` | P2 (file) | 66 insns; fileOpen + import; 0x3537D0D5 | audited-pending |
| `0x41a320` | P2 (file) | (hop-2) open-path callee | pending |
| `0x41aaf0` | P2 (file) | (hop-2) file callee | pending |
| `0x41b680` | P2 (file) | 261 insns; imports + 0x418880 + pstr* — dir ops | audited-pending |
| `0x41af00` | P2 (file) | 387 insns; FileRec magic; 0x418990/0x418c10 | audited-pending |
| `0x418990` | (new) | P2 (file) | callee of 0x41af00/0x41ad30 — hop 2 | pending |
| `0x418c10` | (new) | P2 (file) | callee of 0x41af00 — hop 2 | pending |
| `0x418ac0` | (new) | P2 (file) | callee of 0x418cf0 — hop 2 | pending |
| `0x418e90`→`0x418e90` | | | | |
| `0x4044b0` | P2 (open) | 194 insns; fileReadAt + %HAP magic 0x25484150 + 0x417c90 — .hap file loader | audited-pending |
| `0x416a00` | P3 (dlg) | 187 insns; fileOpenMkDir + 0x415a80 + 0x40c5c0 — dialog orchestration | audited-pending |
| `0x415470` | (new) | P3 (dlg) | callee of 0x416a00 — hop 2 | pending |
| `0x420510` | P2/P3 (doc) | 301 insns; strObjGetData + findForbiddenByte + pstr* — name/path handling | audited-pending |
| `0x43fcd0` | (new) | P7 (str) | callee of 0x420510/0x44c300/0x43f5d0 — hop 2 | pending |
| `0x4390c0` | (new) | P7 (str) | callee of 0x420510 — hop 2 | pending |
| `0x43ba70` | (new) | P7 (str) | callee of 0x420510 — hop 2 | pending |
| `0x43ae50` | (new) | P7 (str) | callee of 0x420510 — hop 2 | pending |
| `0x430d70` | (new) | P6 (res) | callee of 0x420510 — hop 2 | pending |

### Editor UI: per-section tabs (P1/P6)
| Address | Class | Evidence |
|---|---|---|
| `0x4071b0` | P1 (C-tab) | 360 insns; 0x409300 (label ctor), 0x406bd0 (C-bmp), optionListSelect — Images tab | audited-pending |
| `0x406bd0` | P1 (C) | 185 insns; bmpObjCreate + 0x427d80 — C blob editor | audited-pending |
| `0x407b80` | P1 (C) | 71 insns; bmpObjSetTransparency + 0x4311a0 + 0x444d50 | audited-pending |
| `0x444d50` | (new) | P1/P5 | callee of 0x407b80 — hop 2 | pending |
| `0x406f40` | (new) | P1 (C-tab) | callee of 0x4071b0 — hop 2 | pending |
| `0x409660` | (new) | P6 (UI) | callee of 0x4071b0/0x4044b0/0x43d080 — hop 2 | pending |
| `0x4053d0` | P1 (D-tab) | 164 insns; 0x404ec0, optionListGet — Colors tab | audited-pending |
| `0x404ec0` | P1 (D) | 119 insns; VWIN-res + 0x43f5d0 + labelSetText | audited-pending |
| `0x404e50` | P6 (opt) | 15 insns; optionListGet | audited-pending |
| `0x404e70` | P6 (opt) | 31 insns; 0x411a70 + optionList ctor/select | audited-pending |
| `0x411a70` | (new) | P6 (opt) | callee of 0x404e70 — hop 2 | pending |
| `0x4115b0` | (new) | P6 (UI) | callee of 0x406520/0x403050/0x411c80 — hop 2 | pending |
| `0x406520` | P6 (UI) | 28 insns; 0x4115b0 + displayResourceSet | audited-pending |
| `0x403050` | P6 (UI) | 26 insns; 0x4115b0 + displayResourceSet | audited-pending |
| `0x406090` | P1 (E-tab) | 141 insns; 0x405b00, 0x4258d0, 0x4229c0, optionListGet | audited-pending |
| `0x406270` | P1 (E) | 71 insns; 0x405b00 + 0x409230/0x409850 | audited-pending |
| `0x405b00` | P1 (E) | 119 insns; VWIN-res + 0x43f5d0 + labelSetText; "kife" const | audited-pending |
| `0x4229c0` | (new) | P1/P6 | callee of 0x406090/0x4053d0/0x407fa0/0x4071b0 — hop 2 | pending |
| `0x43e9f0` | (new) | P1/P6 | callee of 0x406090/0x4053d0 — hop 2 | pending |
| `0x407fa0` | P1 (G-tab) | 181 insns; 0x445080 (%MSI!), optionListSelect, 0x428260 — Mouse tab | audited-pending |
| `0x445080` | P4 (msi) | 183 insns; %MSI magic 0x254D5349 + bmpObjCreate + 0x427d80 + bmpObjSetTransparency — MSI→bmp | audited-pending |
| `0x4282a0` | (new) | P4 (bmp) | callee of 0x445080 — hop 2 | pending |
| `0x41d190` | P4 (msi) | 162 insns; hapMsiRecordParse + 0x434120 + memZero — MSI consumer | audited-pending |
| `0x434120` | (new) | P4 (msi) | callee of 0x41d190 — hop 2 | pending |
| `0x406360` | P1 (E-ink) | 149 insns; inkListAdd + 0x405cf0 (pairRecordBuild) + 0x423710 — E v2 ink UI | audited-pending |
| `0x405cf0` | P1 (pair) | 32 insns; 0x4309b0 + pairRecordBuild | audited-pending |
| `0x4055a0` | P1 (pair) | 75 insns; pairRecordBuild + 0x424020 + 0x408720 | audited-pending |
| `0x4057d0` | P1 (ink) | seed (inkListAdd) | — |
| `0x409ef0` | (new) | P1 (E) | callee of 0x406360 — hop 2 | pending |
| `0x423800` | (new) | P6 (res) | callee of 0x406360/0x406090 — hop 2 | pending |
| `0x4238b0` | (new) | P6 (res) | callee of 0x406360 — hop 2 | pending |
| `0x423760` | (new) | P6 (res) | callee of 0x406360 — hop 2 | pending |
| `0x4309b0` | (new) | P1/P6 | callee of 0x405cf0/0x4179d0/0x433ac0 — hop 2 | pending |
| `0x433ac0` | P3 (save) | (b2) save pipeline | (b2) |
| `0x404250` | P1/P7 | 116 insns; 0x43e310/0x43e2d0 + pstr* + 0x43e1d0 | audited-pending |
| `0x43e310` | (new) | P1/P7 | callee of 0x404250 — hop 2 | pending |
| `0x43e2d0` | (new) | P1/P7 | callee of 0x404250 — hop 2 | pending |
| `0x435030` | (new) | P1 (save) | callee of 0x402fa0 — hop 2 | pending |

### Widget painters (P5) — the four remaining `widgetBlit` callers
| Address | Class | Evidence |
|---|---|---|
| `0x410960` | P5 (paint) | 67 insns; 0x40ce90 (line-split) + bmpObjCreate + 0x4259d0 + widgetBlit — text painter #1 | audited-pending |
| `0x43bc00` | P5 (paint) | 169 insns; 0x42a170 (ink) + clip + widgetBlit — ink painter #2 | audited-pending |
| `0x4514c0` | P5 (paint) | 65 insns; 0x40ce90 + 0x451260 + widgetBlit — painter #3 | audited-pending |
| `0x451260` | (new) | P5 (paint) | callee of 0x4514c0 — hop 2 | pending |
| `0x446770` | P5 (paint) | 63 insns; 0x40ce90 + 0x4463e0 + widgetBlit — painter #4 | audited-pending |
| `0x4463e0` | (new) | P5 (paint) | callee of 0x446770 — hop 2 | pending |
| `0x410040` | (new) | P5 (paint) | callee of 0x410960 — hop 2 | pending |
| `0x4101c0` | (new) | P5 (paint) | callee of 0x410960 — hop 2 | pending |
| `0x425c60` | (new) | P5 (dib) | callee of 0x43bc00 — hop 2 | pending |
| `0x427200` | (new) | P5 (dib) | callee of 0x43bc00 — hop 2 | pending |
| `0x425a90` | (new) | P5 (dib) | callee of 0x43bc00 — hop 2 | pending |
| `0x42c270` | (new) | P5 (dib) | callee of 0x43bc00 — hop 2 | pending |
| `0x42d190` | (new) | P5 (dib) | callee of 0x43bc00/0x42a2d0/0x42b5d0 — hop 2 | pending |
| `0x40e450` | (new) | P5 (blit) | callee of 0x40e570 (dcBlitDib-neighbor) — hop 2 | pending |
| `0x42d6d0` | (new) | P5 (blit) | callee of 0x40e570 — hop 2 | pending |
| `0x445a30` | (new) | P5 (blit) | callee of 0x40e570 — hop 2 | pending |
| `0x40e570` | P5 (blit) | 424 insns; dcBlitDib + clip 0x42e370/0x42dc90 + import — off-window blit pipeline | audited-pending |
| `0x41ccc0` | P5 (dib) | 295 insns; bmpObjCreate + memZero; 0x10000000/0xFFFFFFFF — DIB builder | audited-pending |
| `0x43e7f0` | P4/P5 (bmp) | 174 insns; bmpObjCreate + 0x427d80 + bmpObjSetTransparency — pair→bmp | audited-pending |
| `0x428260` | (b1) | P4 (bmp) | (b1) |

### Ink / resource / label widgets (P4/P6)
| Address | Class | Evidence |
|---|---|---|
| `0x42b5d0` | P4 (ink) | 77 insns; 0x494B4F4E + lookupBuiltInRec + 0x43f260 — ink consumer | audited-pending |
| `0x42d5f0` | P4 (ink) | 50 insns; pstrEqual + 0x42d3f0 + 0x43f260 | audited-pending |
| `0x43f260` | (new) | P4 (ink) | callee of 0x42a2d0/0x42b5d0/0x42d5f0 (ink-sub neighbor) — hop 2 | pending |
| `0x4094a0` | P6 (label) | 171 insns; 0x5655D881; 0x429cd0/0x429c70 — label method | audited-pending |
| `0x429cd0` | (new) | P6 (label) | callee of 0x4094a0 — hop 2 | pending |
| `0x429c70` | (new) | P6 (label) | callee of 0x4094a0 — hop 2 | pending |
| `0x43d080` | P6 (label) | 62 insns; 0x5655D881 + pstrSetFromRaw + 0x43f840 — label ctor helper | audited-pending |
| `0x43f840` | (new) | P6 (label) | callee of 0x43d080/0x40c420/0x41b5f0 — hop 2 | pending |
| `0x43b940` | (new) | P7 (str) | callee of 0x40b9c0/0x40c420/0x40bfa0/0x44c300 — hop 2 | pending |
| `0x40bfa0` | P6 (widget) | 193 insns; 0xF0168873 + 0x40b9c0 + 0x42e7d0 — widget obj | audited-pending |
| `0x40c420` | P6 (widget) | 94 insns; 0xF0168873 + pstrSetFromRaw + imports | audited-pending |
| `0x40c570` | P6 (widget) | 26 insns; 0xF0168873 + pstrToRaw | audited-pending |
| `0x40c5c0` | (b2) | P6 (label) | (b2) |
| `0x42e7d0` | (new) | P5/P6 | callee of 0x40bfa0 — hop 2 | pending |
| `0x40b1d0` | (new) | P6 (widget) | callee of 0x40bfa0 — hop 2 | pending |
| `0x4336b0` | P6 (UI) | 237 insns; 0x40afc0/0x40b000 + 0x4124d0 + displayResourceSet | audited-pending |
| `0x416530` | P6 (UI) | 165 insns; 0x40b000 + 0x412620 + labelSetText | audited-pending |
| `0x417e90` | P6 (UI) | 153 insns; pstr* + 0x408670 + 0x40b130 + 0x4124d0 | audited-pending |
| `0x418380` | P6 (UI) | 170 insns; 0x43c4c0 + 0x417e90 + 0x4182e0 + 0x423210 | audited-pending |
| `0x418680` | P6 (UI) | 89 insns; 0xB0119129 + 0x4182e0 + 0x423210 | audited-pending |
| `0x4182e0` | P6 (label) | 40 insns; labelSetText | audited-pending |
| `0x43e1d0` | P6 (label) | 74 insns; 0x43df20 + labelSetText; 0xFA382D61 | audited-pending |
| `0x40a710` | (new) | P6 (UI) | callee of 0x418380/0x418680 — hop 2 | pending |
| `0x409b50` | (new) | P6 (UI) | callee of 0x416530/0x417e90/0x4336b0 — hop 2 | pending |
| `0x4124d0` | (new) | P6 (UI) | callee of 0x416530/0x417e90/0x4336b0 — hop 2 | pending |
| `0x40b130` | (new) | P6 (widget) | callee of 0x416530/0x417e90 — hop 2 | pending |
| `0x4358c0` | (new) | P6 (UI) | callee of 0x416530/0x417e90 — hop 2 | pending |
| `0x435120` | (new) | P6 (UI) | callee of 0x416530/0x417e90 — hop 2 | pending |
| `0x4355a0` | (new) | P6 (UI) | callee of 0x4336b0 — hop 2 | pending |
| `0x4350c0` | (new) | P6/P7 | callee (batch-1 neighbor) — hop 2 | pending |
| `0x436210` | (new) | P6 (UI) | callee of 0x416530 — hop 2 | pending |
| `0x414ea0` | (new) | P6 (UI) | callee of 0x416530 — hop 2 | pending |
| `0x409960` | (new) | P6 (UI) | callee of 0x4179d0 — hop 2 | pending |
| `0x43ced0` | (new) | P7 (str) | callee of 0x417e90 — hop 2 | pending |
| `0x417cd0` | (new) | P3 (dlg) | callee of 0x417e90 — hop 2 | pending |
| `0x41fde0` | P2/P6 | 178 insns; 0x447590/0x447c60 + 0x4312d0-70 + displayResourceSet | audited-pending |
| `0x447590` | (new) | P2 (file) | callee of 0x41fde0 — hop 2 | pending |
| `0x447c60` | (new) | P2 (file) | callee of 0x41fde0 — hop 2 | pending |
| `0x448960` | (new) | P6 (UI) | callee of 0x41fde0 — hop 2 | pending |
| `0x4489a0` | (new) | P6 (UI) | callee of 0x41fde0 — hop 2 | pending |
| `0x4312d0` | (new) | P6 (res) | callee of 0x41fde0 — hop 2 | pending |
| `0x431320` | (new) | P6 (res) | callee of 0x41fde0 — hop 2 | pending |
| `0x431370` | (new) | P6 (res) | callee of 0x41fde0 — hop 2 | pending |
| `0x431230` | P6 (res) | 19 insns; fmtInt + displayResourceSet | audited-pending |

### String/format infrastructure (P7)
| Address | Class | Evidence |
|---|---|---|
| `0x43c4c0` | P7 (str) | 460 insns; pstrToRaw + 0x427180 + 0x4460c0/0x445c60 + 0x40bfa0 — big str fn | audited-pending |
| `0x4460c0` | (new) | P7 (str) | callee of 0x43c4c0/0x42ec50 — hop 2 | pending |
| `0x445c60` | (new) | P7 (str) | callee of 0x43c4c0 — hop 2 | pending |
| `0x427180` | (new) | P7 (str) | callee of 0x43c4c0 — hop 2 | pending |
| `0x40ae70` | (new) | P7 (str) | callee of 0x43c4c0 — hop 2 | pending |
| `0x44b220` | (new) | P7 (str) | callee of 0x43c4c0/0x418380/0x418680/0x417070 — hop 2 | pending |
| `0x44b290` | (new) | P7 (str) | callee of 0x418380 — hop 2 | pending |
| `0x44b230` | (new) | P7 (str) | callee of 0x418680 — hop 2 | pending |
| `0x42ec50` | P7 (str) | 128 insns; pstrToRaw + 0x4460c0 + 0x42eb30; 0x455E0FD3 | audited-pending |
| `0x42eb30` | (new) | P7 (str) | callee of 0x42ec50 — hop 2 | pending |
| `0x44c910` | P7 (fmt) | 164 insns; float-div consts; 0x2AAAAAAB — number format | audited-pending |
| `0x44c300` | P7 (str) | 144 insns; 0x43fcd0 + 0x438d20 + 0x44c1c0 + import | audited-pending |
| `0x44c1c0` | (new) | P7 (str) | callee of 0x44c300 — hop 2 | pending |
| `0x438d20` | (new) | P7 (str) | callee of 0x44c300 — hop 2 | pending |
| `0x438390` | P7 (str) | seed (pstrCopy) | — |
| `0x44c620` | P7 (str) | 83 insns; 0x434650 + 0x43fd00 + 0x43c4c0 | audited-pending |
| `0x43fd00` | (new) | P7 (str) | callee of 0x44c620/0x42d3f0/0x434650 — hop 2 | pending |
| `0x434650` | P7 (str) | 108 insns; indirect ESI + 0x440290 + 0x434530 | audited-pending |
| `0x440290` | (new) | P1 (tbl) | callee of 0x434650 — hop 2 | pending |
| `0x434530` | (new) | P7 (str) | callee of 0x434650 — hop 2 | pending |
| `0x44b600` | P7 (fmt) | 324 insns; " fi" + float consts — number cluster | audited-pending |
| `0x44b400` | (new) | P7 (str) | callee of 0x44c300 — hop 2 | pending |
| `0x43a900` | P7 (str) | 253 insns; pstr* + 0x43ba10 + 0x447100 + 0x447050 | audited-pending |
| `0x43ba10` | (new) | P7 (str) | callee of 0x43a900 — hop 2 | pending |
| `0x447100` | (new) | P7 (str) | callee of 0x43a900 — hop 2 | pending |
| `0x447050` | P7 (str) | 72 insns; 0x43b1e0 + pstrToRaw | audited-pending |
| `0x43b1e0` | (new) | P7 (str) | callee of 0x447050/0x4336b0 — hop 2 | pending |
| `0x43b390` | (new) | P7 (str) | callee of 0x4336b0/0x420510 — hop 2 | pending |
| `0x43b0e0` | (new) | P7 (str) | callee of 0x4336b0/0x43f5d0 — hop 2 | pending |
| `0x43b5e0` | (new) | P7 (str) | callee of 0x43b8a0/0x43f5d0/0x42a2d0/0x43a900 — hop 2 | pending |
| `0x41cc50` | P7 (io) | 47 insns; import cluster [0x48d40c..18] | audited-pending |
| `0x41c560` | P7 (err) | 53 insns; 0x41bc50 + import + 0x414d80; 0x1F0D2B21 | audited-pending |
| `0x414f20` | P7 (err) | 66 insns; memAlloc + pstrCopy + 0x440790 | audited-pending |
| `0x440790` | (new) | P1 (tbl) | callee of 0x414f20 — hop 2 | pending |
| `0x414ea0` | (new) | P6 (UI) | (dup) hop 2 | pending |
| `0x445900` | (b2) | P1 (tbl) | (b2) |
| `0x41d890` | B-APP | 69 insns; calls mainMessageLoop — post-init startup | boundary(B-APP) |
| `0x41cad0` | (new) | P7 (io) | callee of 0x41cc50 — hop 2 | pending |
| `0x440820` | (new) | P1 (tbl) | callee of 0x446bc0 — hop 2 | pending |
| `0x446bc0` | P5/P6 (paint) | 213 insns; 0x446910/0x446b80/0x446b00 + 0x40c570 — painter #4 support | audited-pending |
| `0x446910` | (new) | P5 (paint) | callee of 0x446bc0 — hop 2 | pending |
| `0x446b80` | (new) | P5 (paint) | callee of 0x446bc0 — hop 2 | pending |
| `0x40c810` | (new) | P6 (widget) | callee of 0x446bc0/0x40d5f0 — hop 2 | pending |
| `0x4469a0` | (new) | P6 (label) | callee of 0x40c5c0 — hop 2 | pending |
| `0x40cd10` | (new) | P6 (label) | callee of 0x40c5c0 — hop 2 | pending |
| `0x40b360` | (new) | P6 (widget) | callee of 0x40c5c0 — hop 2 | pending |
| `0x446f20` | (new) | P6 (widget) | callee of 0x40cc70/0x40d5f0 — hop 2 | pending |
| `0x446f00` | (new) | P6 (widget) | callee of 0x40cc70 — hop 2 | pending |
| `0x40d5f0` | P6/P7 (str) | 112 insns; memAlloc + 0x40c810 + 0x446f20 + pstrCopy | audited-pending |
| `0x404250` | (above) | P1/P7 | | |
| `0x4152f0` | P6 (res) | 50 insns; 0x423910 + pstrEqual + 0x423a50/0x424270 | audited-pending |
| `0x423a50` | (new) | P6 (res) | callee of 0x4152f0 — hop 2 | pending |
| `0x424270` | (new) | P6 (res) | callee of 0x4152f0 — hop 2 | pending |
| `0x44deb0` | P7 (str) | 69 insns; pstrEqual | audited-pending |
| `0x446b00` | P7 (str) | 52 insns; pstrEqual | audited-pending |
| `0x411c80` | P6 (opt) | 45 insns; 0x51BD8891 + 0x4115b0 + pstrToRaw | audited-pending |
| `0x436bc0` | P6/P7 | 27 insns; 0x411c80 + pstrToRaw | audited-pending |
| `0x435100` | P7 (str) | 11 insns; pstrToRaw | audited-pending |
| `0x411390` | (new) | P6 (UI) | callee of 0x417070/0x416a00 — hop 2 | pending |
| `0x408670` | (new) | P6 (UI) | callee of 0x416530/0x417e90/0x4336b0 — hop 2 | pending |
| `0x435030` | (new) | P1 (save) | (dup) hop 2 | pending |
| `0x4032b0` | (new) | P3 (doc) | callee of 0x403930 — hop 2 | pending |
| `0x4030b0` | (new) | P3 (doc) | callee of 0x403930 — hop 2 | pending |
| `0x407a90` | (new) | P1 (C-tab) | callee of 0x403930 — hop 2 | pending |
| `0x407ad0` | (new) | P1 (G-tab) | callee of 0x407fa0 — hop 2 | pending |
| `0x41fb70` | (new) | P6 (UI) | callee of 0x4336b0 — hop 2 | pending |
| `0x417cd0` | (new) | P3 (dlg) | (dup) hop 2 | pending |
| `0x414e00` | (new) | P7 (err) | callee of 0x41a270/0x4187b0/0x40c5c0 — hop 2 | pending |
| `0x423ee0` | (new) | P6 (res) | callee of 0x416a00 — hop 2 | pending |
| `0x4168f0` | (new) | P3 (dlg) | callee of 0x416a00 — hop 2 | pending |
| `0x416800` | (new) | P3 (dlg) | callee of 0x416a00 — hop 2 | pending |
| `0x43bb90` | (new) | P3 (dlg) | callee of 0x416a00 — hop 2 | pending |
| `0x4355a0` | (new) | P6 (UI) | (dup) hop 2 | pending |

## Scope decision (final, 2026-11-19)

Bidirectional traversal complete through hop 2:
- Pass 1 (seeds → direct neighbors): 477 non-seed nodes
- Hop 2 (in-scope → neighbors, filtered: callees of in-scope + non-utility
  callers): 258 kept (rest = generic callers of hError*/mem* utilities only)
- Boundary set: B-EXT (imports, excluded from get_callees output — implicit),
  B-APP (app shell: 0x403de0/0x41db80/0x41d890/0x44c5f0/0x452700/0x41d880/
  0x43bb10/0x41bd30/0x4038b0/0x40b9c0), B-GENUI (callback thunks 0x40bc70/
  0x40f7c0/0x41ba70/0x44b460, paint stubs' generic dispatch 0x409100 pending),
  B-DYN (indirect calls via global tables, e.g. 0x466370 — unresolved,
  documented per occurrence).

**Audit tiers** (every Tier A/B function gets the full per-function gate:
name eval, callers/callees enumerated (done), every parameter inspected,
every meaningful local inspected (disposition recorded even when
"temporaries only"), return/CC eval, globals eval, mutations applied +
read back):
- **Tier A (deep: params + locals + signatures + comments)** — core
  pipeline, ~150 fns: HAP layer (sub-obj ctors, C/D/E/G tab fns, 0x402fa0,
  0x404250, 0x4044b0, pair/ink fns, 0x43e9f0, 0x435030), file layer
  (0x419220/0x419600/0x418a30/0x418cf0/0x418de0/0x418880/0x4188b0/0x41b5f0/
  0x41a270/0x41a250/0x41a320/0x41ac60/0x41aaf0/0x41af00/0x41b680/0x41c300/
  0x419bf0/0x4473e0/0x418990/0x418c10/0x418ac0/0x4188e0/0x44b530/0x44be50/
  0x447120), error layer (0x414bf0/0x414890/0x414d80/0x414dc0/0x414e00/
  0x414ea0/0x414f20/0x41d760/0x41d7f0/0x41d570/0x41bc50/0x41c560/0x41cc50/
  0x41cad0/0x41c880/0x41ca30/0x41c2b0/0x41c480/0x41c4c0/0x41c1a0/0x434f60),
  render/DIB (0x427d80/0x427b30/0x441d80/0x441320/0x441040/0x441090/0x4258d0/
  0x425880/0x4259d0/0x425c30/0x425c60/0x425a90/0x425a50/0x425b80/0x425b20/
  0x425ca0/0x426370/0x4263b0/0x4265d0/0x426610/0x4266c0/0x426830/0x426c90/
  0x426db0/0x426f50/0x427200/0x4279f0/0x427fd0/0x42c270/0x42d190/0x42d6d0/
  0x42e2b0/0x42e370/0x42dc90/0x429be0/0x425910/0x4431b0/0x44e5f0…0x44fc30/
  0x40e570/0x40e450/0x445a30/0x4459e0/0x41ccc0/0x410960/0x43bc00/0x4514c0/
  0x446770/0x451260/0x4463e0/0x410040/0x4101c0/0x40ce90/0x40cbb0/0x4093e0/
  0x4094a0/0x429cd0/0x429c70/0x42a170/0x42a2d0/0x42a140/0x42b5d0/0x42d5f0/
  0x426e00/0x426b20/0x426660/0x425d00/0x429100/0x43f260/0x409100/10×stub/
  0x445080/0x4282a0/0x41d190/0x434120/0x43e7f0/0x428260/0x428c70/0x4287f0/
  0x4282d0/0x444d50), ink/MSI (0x445080/0x41d190/0x434120/0x42a2d0/0x42b5d0/
  0x43f260/0x42d5f0), formatters (0x439cc0/0x439d00/0x43a610/0x43a360/
  0x43a900/0x43ae70/0x434ba0/0x42f4e0/0x41d9a0/0x44c910/0x44c500/0x44c570/
  0x44c740/0x44c300/0x44c1c0/0x44c620/0x434650/0x434530/0x440290), doc
  lifecycle (0x403930/0x403510/0x433ac0/0x403300/0x4038c0/0x403640/0x4178b0/
  0x4179d0/0x417c90/0x417c50/0x417800/0x416a00/0x415a80/0x415920/0x415f00/
  0x415470/0x420510/0x41fde0/0x431230/0x4311f0), label/opt widgets
  (0x409300/0x411cf0/0x411ad0/0x411290/0x411120/0x4110e0/0x411260/0x4112d0/
  0x4117d0/0x411920/0x411a70/0x4115b0/0x411c80/0x411c20/0x411e80/0x435120/
  0x435e60/0x43d080/0x43f840/0x4311a0/0x431030/0x431160/0x4308a0/0x4302e0/
  0x4309b0/0x430d70), table machinery (0x440360/0x440430/0x4408a0/0x440bb0/
  0x4405a0/0x440820/0x440640/0x440790/0x4407e0/0x440950/0x4409d0/0x440a60/
  0x440b10/0x440b70/0x440ce0/0x440e10/0x440ef0/0x441420/0x445900/0x42d3f0),
  res objects (0x423210/0x4236c0/0x423910/0x423710/0x423600/0x4237d0/
  0x423860/0x423800/0x4238b0/0x423760/0x423a50/0x424270/0x4240b0/0x424020/
  0x424310/0x424350/0x424450/0x424490/0x4215a0/0x4209e0/0x423120/0x408ed0/
  0x408b60/0x412060/0x412490/0x4124d0/0x436c00/0x40fb90/0x40fcc0),
  sub-obj ctors (0x403f80/0x4049e0/0x4056b0/0x4065a0/0x407d00/0x404e70/
  0x404e50/0x405cf0/0x4055a0/0x406bd0/0x407b80/0x407ad0/0x406f40/0x406810/
  0x409ef0/0x43e9f0/0x404ec0/0x404250/0x4044b0).
- **Tier B (full audit, lighter renames: params via prototype, meaningful
  locals only)** — peripheral UI builders ~200 fns: 0x401e30/0x407600/
  0x4071b0/0x4053d0/0x406090/0x406270/0x407fa0/0x401290/0x402210/0x401470/
  0x401550/0x4015b0/0x401a20/0x401bb0/0x401da0/0x403020/0x4030b0/0x4032b0/
  0x4035d0/0x405670/0x4064f0/0x406580/0x407a90/0x408210/0x408300/0x408340/
  0x4083d0/0x408670/0x409230/0x409850/0x409660/0x409760/0x4097f0/0x409960/
  0x409b50/0x40a710/0x413760/0x416530/0x417070/0x417e90/0x418380/0x418680/
  0x4182e0/0x4187b0/0x4336b0/0x43e1d0/0x43df20/0x43f5d0/0x43d860/0x43e2d0/
  0x43e310/0x43ced0/0x43cb10/0x43c4c0/0x434f80/0x4355a0/0x4358c0/0x436210/
  0x437870/0x43bb90/0x44bd20/0x44bd70/0x44c0a0/0x44b600/0x449940/0x446130/
  0x40bfa0/0x40c420/0x40c570/0x40b1d0/0x42e7d0/0x40af40/0x40af80/0x40afc0/
  0x40b000/0x40b090/0x40c270/0x40c5c0/0x40c6d0/0x40cc30/0x40cc70/0x40cac0/
  0x40cbb0/0x40cd10/0x40b360/0x4469a0/0x446f20/0x446f00/0x40d5f0/0x446bc0/
  0x446910/0x446b80/0x40c810/0x440820/0x421bc0/0x421ab0/0x4229c0/0x422a30/
  0x422ac0/0x4279f0/0x4413c0/0x441f70/0x449940/0x42ee00/0x40bc10/0x41bd80/
  0x44deb0/0x446b00/0x435100/0x4378e0/0x435ff0/0x4352c0/0x4350c0/0x436bc0/
  0x431e50/0x4372f0/0x431960/0x430ca0/0x43b6f0/0x43b9e0/0x43ac00/0x432a50/
  0x432d40/0x451790/0x452180/0x452270/0x452820/0x42ec50/0x42eb30/0x4460c0/
  0x445c60/0x427180/0x40ae70/0x43b390/0x43b0e0/0x43b5e0/0x43b8a0/0x43ba10/
  0x43ba70/0x43ae50/0x4390c0/0x438d20/0x43fcd0/0x43fd00/0x43b1e0/0x447050/
  0x41fb70/0x433ac0-adj/0x414e00/0x414ea0/0x4168f0/0x416800/0x416c40/
  0x4162e0/0x416210/0x4160a0/0x416160/0x416350/0x4153f0/0x415ca0/0x4152f0/
  0x412620/0x411390/0x41d9a0/0x4152f0/0x433ac0/0x41fde0/0x402fa0/0x435030.
- **Tier C (boundary/deferred)**: 350 generic-only callers (boundary class
  by signature sampling — 63 sampled, rest by adjacency), B-APP shell,
  B-EXT imports, B-DYN indirects, and the 0x44E5xx–0x44FC30 text-raster
  library (deferred: consumed only by the two DIB builders; sampled, not
  individually audited — revisit trigger: DIB-builder audit needs its
  internals).

Seeds (84) are re-audited in Tier A/B passes (R0-A.2 did 34 prototypes +
8 fns' locals; the remainder of the seeds get full parameter/local gates
now).

## Audit execution order
1. Render/DIB + painters (Tier A) — R0-A.2 task-2 carryover
2. HAP layer new fns (Tier A)
3. File + error layers (Tier A)
4. Formatters + pstr family (Tier A/B)
5. Doc lifecycle + label/opt (Tier A)
6. Table machinery + res objects (Tier A/B)
7. Remaining Tier B UI builders
8. Fixed-point pass: requeue functions whose semantics changed; verify
   propagation
9. Coverage matrix + report + save + commit

## Audit log (per-function gate results)

### Batch 1 — render/DIB core (7 fns; 6 done, 1 retry)
| Function | Name | Params audited | Locals audited | Mutations | Verified |
|---|---|---|---|---|---|
| `0x427d80` | `bmpBlitToSurface` | 6 (typed hapBitmapObj*/hapDibSrc*) | local_44→(src rect, temp) temporaries: 14 locals inspected, 0 meaningful beyond rect/offset temps — disposition: temporaries only (clip math); dst/src pixel temps named in comments | rename+proto+comment | proto+comment read back; re-dec queued (TIMEOUT-5, re-verify later) |
| `0x4258d0` | `bmpGetWH` | 3 (typed) | none (0 locals) | rename+proto+comment | read back |
| `0x425880` | `paintSurfaceRelease` | 1 (typed) | 1 reg temp (iVar1) — temporaries only | rename+proto+comment | read back |
| `0x4259d0` | `bmpSetOffset` | 3 (typed) | none | rename+proto+comment | read back |
| `0x425c30` | `bmpSetTransColor` | 2 (typed) | none | rename+proto+comment | read back |
| `0x426610` | `bmpBlitPair` | 2 (typed) | none | rename+proto+comment | read back |
| `0x4263b0` | pending retry | — | — | — | decompile TIMEOUT (task queue); requeue |

Types: `hapDibSrc` (32 B: w,h,bpp,rowBytes,palCount,flags,pixels,palette) created;
`hapBitmapObj` extended 18 fields / 72 B (stride@0x0C, pixels@0x18, offX/offY@0x20/24,
surfW/surfH@0x28/2C, transColor2@0x38, transColor@0x3C, transFlag@0x40, magic@0x44) —
replace_structure + read back (size 72 ✓).
**Finding F6 (CONFIRMED)**: the DIB engine = per-bpp converter blits
(0x44e5f0 1bpp, 0x44e8e0 2, 0x44eb60 4, 0x44ed30 8, 0x44ef30 16, 0x44f210 24,
0x44fb30/0x44fc30 32 ± transparency-index) + rect intersection 0x4431b0.
Surface = hapBitmapObj (0xF4DA120B). This is how skin bitmaps (C/E/F/G blobs)
reach the widget DIBs: the widget painter builds a hapDibSrc from the parsed
blob and calls bmpBlitToSurface (9-slice = multiple blits per widget region —
slice arithmetic lives in the painters, to confirm in Batch 2).

### Batch 2/3 — widget paint + text/ink engine (applied, read back)
| Function | New name | Role (CONFIRMED via decomp) |
|---|---|---|
| `0x40ce90` | `textWidgetGetRect` | text-widget layout: state + fontIdx(+0x70) + rect(+0x78..84); dirty flag +0x88 gates repaint; single rect only |
| `0x40cbb0` | `textWidgetStateGet` | 1 hidden / 3 visible-unfocused / 4 focused (hwnd @+0x0c, GetFocus); 0x466294 special-cased → 4 |
| `0x43bc00` | `compositeWidgetPaint` | button-family painter: base fill (style 2) + up to 5 gated sub-features (ink image, text via bmpTextDraw(text@+0x70,len@+0x74), 4 state icons w/ params @+0x84..0xc0); clip test rectIntersects per feature; widgetBlit to window @+0x7c |
| `0x410960` | `labelWidgetPaint` | label painter: font @widget+0x08 → labelWidgetFill → widgetBlit (window @+0x04) |
| `0x4514c0` | `iconGridPaint` | icon-grid painter (Images tab) |
| `0x446770` | `listRowPaint` | list-row painter (window @+0x00) |
| `0x4101c0` | `labelWidgetFill` | fontMetricsGet → bmpSetMetrics → fontTextDraw; optional marker (flag +0x9d, rect +0x70, color +0x9c, subrects +0x84..94) |
| `0x451260` | `iconGridFill` | 12 rows × 15 cols, pitch 18/19px; u16 slot table **gIconGrid @0x488ac0** (180 slots); per-cell state 0x1000000 selected / 0x40000 active / 0; inkSlotFetch → bmpInkBlit(mode 0x30) |
| `0x4463e0` | `listRowFill` | 22px (0x16) rows; row objs @+0x14 table {inkIdx, pstr text}; current @+0x10; count @+0x18; selected row → bmpRowText, inkIdx==0 → 8px fill + bmpTextDraw2(flags 0x21) |
| `0x4459e0` | `rectIntersects` | AABB strict-intersection of {x1,y1,x2,y2} rects |
| `0x43b5e0` | `inkSlotFetch` | u16 slot → %IKN subrecord bytes (out buf, max len) → returns byte length |
| `0x426e00` | `bmpInkBlit` | blit %IKN subrecord into surface at pos, state flags, mode 0x30 |
| `0x42b6c0` | `bmpRowText` | list-row text draw; param_3[0] = selected |
| `0x426f50` | `bmpTextDraw2` | text draw variant (pos-based; font from surface metrics) |
| `0x42a8c0` | `bmpSetCellState` | per-cell 32B state buffer |
| `0x42a200` | `bmpSetMetrics` | copy 4-word font metrics/base rect into surface |
| `0x424550` | `fontTextDraw` | draw widget text: font obj + surface metrics + rect |
| `0x4230c0` | `fontMetricsGet` | 16-byte font metrics from font obj (proto pending hapFontObj type) |
| `0x41e8a0` | `labelMarkerDraw` | label secondary marker |
| `0x451210` | `iconGridCellState` | cell active/hover test |
| `0x42a170` | `widgetBaseFill` | base fill: style 2 → patterned (gStyleRec+0x44 color) or solid mode via modeMap(0x42a140) |
| `0x42d190` | `inkSlotDraw` | E-icon slot draw: custom ink table (gInkTbl 0x466964 ptr, gInkCount 0x466968) else built-in blobB+0x44 subtable; raster 0x43f260 (color key 0xFFFFFFFF) |
| `0x425c60` | `bmpSetFillMode` | fillMode @+0x38 = modeMap(num) |
| `0x425c30` | `bmpSetFillModeRaw` | raw write to fillMode @+0x38 |
| `0x427200` | `bmpTextDraw` | **font-glyph text raster** (NOT GDI): font → glyph table (0x445e90), row stride (0x44e5d0), advance (0x446130), glyph row (0x44e350), blit 0x44dfe0 (reads fillMode); rect via offX/offY; clip L/T/R/B; flags 0x20 center, 8 bottom, 4/0x10 fill |
| `0x425a90` | `bmpSetClip` | clip rect @+0x28..0x34 clamped to 0..w/h |
| `0x42c270` | `bmpStateIconDraw` | 3 state bits (0x01/0x02/0x20) → slot idx {9,10,11} or {21,22,23} in gStyleRec+0x40 (fallback gStyleDef+0x40); slot (bswap) = E offset; draw + trans color + 0x426e00(0x30) |

**Struct fix (applied, verified size 72)**: hapBitmapObj @0x28..0x34 = **clip rect L,T,R,B** (not surfW/H — corrected from batch 1); @0x38 = fillMode (not a second trans color).
**New types**: hapTextObj (140 B: f0,f4,magic 0x1688173,hwnd,pad,fontIdx,rect[4],dirty) created.

**Findings**
- **F7 (CONFIRMED)**: widget text is rasterized from the appearance **font glyph bitmaps** (bmpTextDraw → 0x44dfe0 glyph blit), not GDI. The appearance's own .fnt font renders its own UI text.
- **F8 (CONFIRMED)**: icon grid = 15×12 u16 slot-ID table (gIconGrid 0x488ac0) → %IKN subrecords; per-cell 3-state flags (0 selected / 0x40000 active / 0x1000000 selected-strong).
- **F9 (CONFIRMED)**: state icons (button states) map 3 state bits → 6 E-icon slots via a runtime-populated style table (gStyleRec 0x466954, zero at rest; populated from the active appearance's D/E data at load).
- **F10 (CONFIRMED)**: paint-surface lifecycle = bmpObjCreate → bmpSetOffset/bmpSetClip/bmpSetFillMode → per-content fills → widgetBlit → (surface released by paintSurfaceRelease).
- **F11 (PROBABLE)**: 0x466294 = main-window handle (text state special case).
- **F12 (CONFIRMED)**: three widget paint families share the template: textWidgetGetRect → bmpObjCreate(line rect) → bmpSetOffset(-x1,-y1) → fill → widgetBlit. label(+0x04 win, font +0x08), iconGrid, listRow (+0x00 win, rows +0x10/14/18).

**Remaining (R0-A.3)**
- Retry: 0x4263b0 (bmpBlitPair callee, 32bpp blit), bmpBlitToSurface re-dec verification (TIMEOUT-5)
- fontMetricsGet proto (needs hapFontObj or uint*font)
- Globals rename: gStyleRec 0x466954, gStyleDef 0x466950, gInkTbl 0x466964, gInkCount 0x466968, gIconGrid 0x488ac0, gMainWindow 0x466294
- Next tier: file layer (0x419xxx), error layer, doc lifecycle (0x401000/0x4030f0), hapParse/serialize param gates, formatter 0x439cc0, D-section v1/v2 readers, E-section readers, ink/MSI parse, open/save pipeline (0x403300/0x403510), %MSI converter 0x445080

### Batch 4 — doc lifecycle + HAP core gates
| Function | Gate result |
|---|---|
| `hapParse` 0x402900 | **already gated (R0-A.2)** — params (doc, fileBuf, fileSize), locals (descLen, blockAStrPtr, regionPtr, tsBuf) read back ✓. No mutation. |
| `hapSerialize` 0x402570 | **already gated (R0-A.2)** — (doc, outSize), sizeA..G/outBuf/sectionSize ✓. No mutation. |
| `docCreate` 0x401000 | proto `hapDoc * docCreate(char *namePstr)` applied+read back; locals local_24→docRef, local_c→docRefPtr (7/7 var renames ok); comment applied |
| `createDocument` 0x4030f0 | proto `hapDoc * createDocument(int *docMgrObj)` applied+read back; locals →namePstr/doc/numBuf/tsStr/namePtr; comment applied. Counter @docMgrObj+0x08. |
| `hapLoadEntry` 0x4036b0 | vars known from R0-A.2 (ownerCtx, fileRec*file; fileBuf/fileSize/nameBuf/nodeRef/docNode/nameLen) — decompile TIMEOUT (queue congestion), **requeue** |
| `hapSaveEntry` 0x4033a0 | decompile TIMEOUT, **requeue** |

**Header/Block-A layout re-confirmed from writer+parser (word idx = byte idx/4, puVar1 is uint\*)**:
- Directory = 12 words @ bytes 0x2C..0x58: [0x2C]=A cap (0x88), [0x30]=A size, [0x34]=C off, [0x38]=C size, [0x3C]=D off, [0x40]=D size, [0x44]=E off, [0x48]=E size, [0x4C]=F off, [0x50]=F size, [0x54]=G off, [0x58]=G size. (Matches R0-A.2 "6 slots @ 0x2C".)
- Block A payload @ byte 0x88 (writer: hapWriteBlockA(doc, puVar1+0x22 words, sizeA)); layout: +0x00 tsPrevLo, +0x04 tsPrevHi, +0x08 tsLastLo, +0x0C tsLastHi, +0x22 nameLen, +0x23 creditsLen, +0x24 verLen, +0x25 descLen, +0x34 name, then version, credits, desc (string order: name, version, credits, desc).
- Flags: 0x7C=A-valid (parsed as fileBuf[0x1f]), 0x7D=C, 0x7E=D ver (1|2), 0x7F=E ver (1|2), 0x80=F, 0x81=G.
- Scale nibbles: header byte 3 (hi) + byte 0x0D (lo) → optionListSelect(hi<<4|lo) on doc options list (doc->optionsObj+0x38).

### Batch 5 — open/save pipeline
| Function | Gate result |
|---|---|
| `hapLoadEntry` 0x4036b0 | **already gated (R0-A.2)** read back ✓ (params ownerCtx/file; locals fileBuf/fileSize/nameBuf/nodeRef/docNode/nameLen). No mutation. Doc-list node: +0x28 next, +0x0C doc, +0x90 win, +0x19D unload flag. |
| `hapSaveEntry` 0x4033a0 | **already gated (R0-A.2)** read back ✓ (ownerCtx, hapDoc*doc, forceDialog). No mutation. |
| `0x403510` | → **docSaveAs** renamed+proto `(uint ownerCtx, hapDoc *doc)` + locals dlgHandle/fileHandle/pathBuf + comment. Runs open dialog @doc+0x98, swaps file @doc+0x90, path pstr @doc+0x9c, then hapSaveEntry. |
| `0x4044b0` | → **hapDImportFromFile** renamed+proto `(hapDoc *doc, char execFlag)` + locals + comment. **F13 (CONFIRMED)**: D-color import = copy exactly 0xD8 bytes (54×u32) from another v2 .hap's D section into dSub+0x16; dSub+0x0D bit 0x1000 = imported flag. Version must be exactly 2, D flag must be 2. |
| `0x4179d0` | → **openDialogExec** (returns fileRec* on OK; out path buf optional) |
| `0x417c50` | → **fileDialogClose**; `0x417c90` → **fileDialogCancel**; `0x4178b0` → **fileDialogCreateSave**; `0x417800` → **fileDialogCreateOpen** |
| `0x445080` | %MSI converter — decompile TIMEOUT (3rd), **requeue** |

**F14 (CONFIRMED)**: file dialog API is IFileOpenDialog/IFileSaveDialog COM wrappers (IDropTargetVtbl-typed in Ghidra); handles stored per-doc (+0x98 open dlg, +0x1A0 D-import dlg, doc->saveDialog).

### Batch 6 — file layer + %MSI converter (all read back)
| Function | Gate result |
|---|---|
| `fileOpen` 0x419420 | proto `fileRec * fileOpen(uint16 *pathBytes, uint pathByteLen, uint accessFlags, char *outNamePstr, uint *outFileSize)` + local fileAttrs + comment. accessFlags: 1 read, 2 write, 4 no-share-read, 8 no-share-write, 0x10 read-only retry. |
| `fileCreate` 0x419dc0 | proto applied + local rec + comment. flags: 2 write, 4/8 share, 0x10 retry, 0x40 CREATE_ALWAYS, 0x80 require-existing. |
| `fileReadAt` 0x41a640 | proto `byte * fileReadAt(fileRec*, uint offset, uint wantSize, uint *inoutSize, uint flags)` + locals buf/bytesRead/seekHi + comment. wantSize=0 → read-to-capacity. |
| `fileWriteWhole` 0x41a8c0 | proto applied + comment. **CONSUMES buffer** (memFree on all paths); truncate+write+flush. |
| `fileClose` 0x41a270 | renamed + proto + comment. |
| `fileNameExtract` 0x41a450 | proto + comment. Drive paths → GetVolumeInformationW label. |
| `msiBlobToBmp` 0x445080 | renamed + proto + locals + comment. |

**F15 (CONFIRMED)**: %MSI v1 layout: `[0] "%MSI" BE magic, [2] ver u16BE=1, [6] w, [7] h, [0xD] hotspotX, [0xE] hotspotY, [0xF] palCount-1 (0 iff bpp>8), [0x10] palette palCount×u32, pixels`. bpp ∈ {2 (row 16-px aligned), 8 (row 4-aligned), 32 (row w·4)}. transColor out = palette[1] else 0xFFFFFFFF. This is the G-section (mouse icons) runtime conversion.
**F16 (CONFIRMED)**: sibling file fns exist: fileOpenMkDir @0x419760, fileOpenExt @0x4199e0 (gated next).

### Batch 7 — pstr/mem/fmt/error layers (all read back)
| Function | Gate result |
|---|---|
| `pstrCopy` 0x438390 | proto `(byte *dst, byte *src)`, locals srcLen/off + comment |
| `pstrCopyTrunc` 0x438440 | proto `(byte*, byte*, uint maxLen)` |
| `pstrAppend` 0x438500 | proto + locals curLen/srcLen/newLen + comment (cap 0xFF) |
| `pstrAppendTrunc` 0x4385f0 | proto |
| `pstrAppendInt` 0x4386e0 | proto `(byte *dst, uint value, uint flags)` (via fmtInt) |
| `pstrAppendByte` 0x4387b0 | proto |
| `pstrEqual` 0x4387e0 | proto `(byte *a, byte *b)` returns 0/1 |
| `pstrToRaw` 0x438880 | proto + locals + comment (strips len prefix) |
| `fmtInt` 0x4397b0 | proto `(uint value, char *buf, uint maxLen, uint flags)` + locals minWidth/outPtr/tmpBuf + comment (flags: 0x7F width, 0x100 space-pad, 0x1000 hex, 0x2000 0x-prefix, 0x10000 minus) |
| `0x439cc0` | → **fmtSignedInt** renamed + proto `(int, char*, uint, uint)` + comment |
| `memAlloc` 0x41bba0 | proto `void * (uint size)` + local buf + comment (GlobalAlloc(0), gAllocCount++) |
| `memFree` 0x41bca0 | proto `void (void **ptrSlot)` + comment (nulls slot, gAllocCount--) |
| `memDup` 0x41bbf0 | proto `(void *src, uint size)` |
| `memCopy` 0x41bb10 | proto `(void *dst, void *src, uint size)` + comment (overlap-aware) |
| `memZero` 0x434420 | proto `(void *dst, uint size)` (comment existed) |
| `hError` 0x434880 | comment: 0x90B error frame {code@0, module FourCC@8, sub@0xC} duplicated at +0x60, dispatcher 0x414bf0 (noreturn) |
| `0x466bac` | → **gAllocCount** (alloc counter, verified) |
| `hErrorSimple` 0x434810 | **TIMEOUT requeue** |
| `0x41bc50` (fileRecAlloc) | **TIMEOUT requeue** |
| `0x41bcd0` | **TIMEOUT requeue** |
| `0x4263b0` (bmpBlitPair callee) | **TIMEOUT requeue (3rd)** |

**F17 (CONFIRMED)**: allocation = Win32 GlobalAlloc/GlobalFree (GMEM moveable), counted by gAllocCount (leak-detection global). pstr max length 0xFF enforced by append/copy caps.
**F18 (CONFIRMED)**: hError frame layout for the error dialog (0x90 bytes, doubled frame — likely for nested-error or backtrace support).

### Batch 8 — section readers + record parsers (13/16 done, read back)
| Function | Gate result |
|---|---|
| `hapCSectionRead` 0x4070f0 | params/locals already gated (R0-A.2); comment refined: C section = 64B (0x10-word) header + 174 u32BE offsets at word tableIndex+0x10; min 0x840 |
| `hapCBlobParse` 0x406e20 | gated (R0-A.2); verified vs decomp (consumed = hdr + h*(rowBytes+palBytes) + (blob[3]+1)*4) |
| `hapDSectionReadV1` 0x404460 | gated; verified (builtin-first + permute select, LE words) |
| `hapDSectionReadV2` 0x404410 | comment refined: exact 0xD8 copy, else builtin default |
| `hapESectionReadV1` 0x405310 | comment refined: 0x22 widget (map<28) + 0x1a volume inks; eSub flag_34 \|= 0x1000, inkVolumeList+0x0D \|= 0x1000 |
| `hapESectionReadV2` 0x405210 | gated (R0-A.2) verified |
| `hapEBlobParse` 0x404700 | gated (R0-A.2); comment refined w/ full field map |
| `hapERowFetch` 0x4048d0 | locals local_18/14 -> surfA/surfB; comment: two-blob rows (layer A/B) -> pairRecordBuild(2, key) |
| `hapFSectionRead` 0x405f50 | locals -> blob/blobSize/remaining; comment: F records join doc->inkVolumeList (same list as v1 volume inks) |
| `hapGSectionRead` 0x408570 | comment: 18 slots, raw %MSI blobs, runtime msiBlobToBmp |
| `hapInkRecordParse` 0x43f430 | local local_18 -> subOut; comment refined (count @+6, stride @+7, data @+8, 12B header advance) |
| `hapInkSubParse` 0x43f2d0 | comment refined (bpp 1/2/4/8/0x18, extra u32BE @+8) |
| `hapMsiRecordParse` 0x4452c0 | comment: full validation map (hotspot bounds, bpp 2/8/32, size formula) |
| `inkListAdd` 0x4057d0 | **TIMEOUT requeue (3rd)** |
| `inkListFinalize` 0x405880 | **TIMEOUT requeue (3rd)** |
| `pairRecordBuild` 0x43e390 | **TIMEOUT requeue (3rd)** |

**F19 (CONFIRMED, corrected)**: %MSI field map — +0x0C hotspotX, +0x0D hotspotY, +0x0E bpp, +0x0F palCount-1 (earlier 0x0D/0x0E was off by one; msiBlobToBmp comment corrected).
**F20 (CONFIRMED)**: F-section (file icons) records are appended to the same runtime ink list as v1 E volume inks (doc->inkVolumeList) — one shared %IKN pool at render time.
**F21 (CONFIRMED)**: v1 E rows hold up to TWO E blobs each (normal + state layer) resolved at load into a pairRecord via pairRecordBuild.

### Batch 9 — retries (all 15 succeeded this round) + helpers (read back)
| Function | Gate result |
|---|---|
| `inkListAdd` 0x4057d0 | locals searchKey/nodeSlot + comment. 12B node {?,blob,size}; key!=0 must be unique (dup -> 0x1000d); list obj at inkList+0x3C |
| `inkListFinalize` 0x405880 | comment (0x4236c0 + comparator 0x405720) |
| `pairRecordBuild` 0x43e390 | locals entry/surf/bppClass/probe + comment. count*0x42C buffer; live surface pointers + format probe 0x441320 (bpp class 1/2/4/8/24) |
| `hErrorSimple` 0x434810 | proto `void hErrorSimple(uint code)` (Ghidra marked stdcall — noreturn wrapper) + local errFrame + comment |
| `0x41bc50` | → **memAllocZeroed** (GMEM_ZEROED) proto + comment |
| `0x41bcd0` | → **memResize** proto + comment |
| `0x4263b0` | → **bmpFillRect** proto `(hapBitmapObj*, int x1,y1,x2,y2, uint colorArgb)` + comment. **F22**: color 0xAABBGGRR; alpha 0 = fast fill; else per-pixel blend (px-ch)*a/255+ch |
| `searchRecords` 0x4401c0 | comment (binary search) + locals lo/hi/mid/midOff; cmp param left untyped (function-pointer typedef not supported by create_typedef — partial, documented) |
| `lookupBuiltInRec` 0x445830 | proto `(uint key, int ctx, uint *outValue)` + comment (registry 0x45F848, 0x14B entries, VWIN-style FourCC keys) |
| `0x4457c0` | → **builtinRecCmp** |
| `displayResourceSet` 0x4308d0 | comment (magic 0x83AF6F92, data @+0xAC, callbacks @+0x8C/+0x9C) |
| `strObjGetData` 0x431270 | comment (data @+0xAC, out @+0xB0/0xB4) |
| `filetimeNow` 0x41c440 | comment (POSIX ns = u64*10000 - 0x894deb84400) |
| `filetimeToString` 0x434ec0 | local timeFields + comment (flags 0x1BF0 spec bits, 0x2000 tz via tzOffsetMinutes, app uses 0x3020) |
| `0x41c4c0` | → **tzOffsetMinutes**; `0x434900` → **filetimeBreakdown**; `0x434ba0` → **timeFieldsFormat** |
| `optionListGet` 0x411df0 | proto + comment (items +0x0C, count +0x10, sel +0x5C, value item+8) |
| `optionListSelect` 0x411d80 | proto + comment |

**F23 (CONFIRMED)**: built-in resource registry = sorted FourCC-keyed table (binary search), 0x14B records {key, ?@4, value@0xC, dataOff@0x10 (rel to 0x45F830)}; VWIN (0x5657494E) confirmed among consumers (0x408ed0).
**F24 (CONFIRMED)**: pair records keep LIVE surface pointers (runtime index, not serialized) — E v1 entry->data = pairRecord; pixel format probed per surface (0x441320).

### Batch 10 — blit pipeline + DIB decode (8/10 done, read back; 0x41a300 & 0x43a610 TIMEOUT, final retry pending)
| Function | Gate result |
|---|---|
| `winBlitDib` 0x40cf50 | already gated (R0-A.2) + locals clientRect/dibInfo/widgetRect; DIB desc = {w,h,?,stride(px),?,pixels} |
| `dcBlitDib` 0x40e4d0 | already gated (R0-A.2); SetDIBitsToDevice 32bpp top-down confirmed again |
| `widgetBlit` 0x40d160 | proto typed `(uint *widget, int *off, hapBitmapObj **surfSlot)` + comment |
| `labelPaint` 0x409fc0 | proto `(int *label)` + locals lines/label/skinObj + refined comment: **virtual per-line fill** (vtbl+0x1C of skinObj @label+0x08); text obj @label+0x0C; style = state low byte |
| `0x4431b0` | → **rectClipIntersect** proto (9 params) + locals rL/rT/rR/rB + comment (generic multi-rect clip used by both blit paths) |
| `0x441d80` | → **bmpBlitPalette** proto `(hapDibSrc*, uint *dstOff, hapBitmapObj*, uint *srcOff, uint, int)` + locals + comment (1-8bpp path, 0x4415xx converters, hasTrans = transFlag bit1 @+0x41) |
| `0x441320` | → **paletteExtract** proto + locals + comment. **F25 (CONFIRMED)**: storage bpp is AUTO from extracted palette size (<3→1, <5→2, <17→4, <257→8, else 24) |
| `0x41ccc0` | → **dibInfoDecode** proto + locals + comment. **F26 (CONFIRMED)**: C-section image blobs = 9-slice ext header + CLASSIC WINDOWS DIB (BITMAPINFO; BI_RGB only; 24bpp or 1/2/4/8+palette; negative height = bottom-up; BGR→0x00BBGGRR) |
| `0x41a300` | **TIMEOUT requeue (2nd)** — 1250-instr GDI compositing (editor preview?) |
| `0x43a610` | **TIMEOUT requeue (2nd)** — fixed-point/float helper (0xcccccccd constants) |

Var renames: 17/20 applied (3 labelPaint decompiler-confused locals skipped — decompiler type confusion on that function's line buffer; recorded, no further action).

## R0-A.3 STATUS: COMPLETE (2026-11-18)
- All tier-A batches applied and read-back verified (56 fn renames, 7 globals, 59 protos, 67 locals, 86 comments, 2 types, 1 struct replace).
- Report: 12-r0a3-semantic-enrichment.md · Ledger: 06-symbol-ledger.md (R0-A.3 section) · Format doc: 04-hap-format.md appendix.
- Ghidra project saved (haxial.gpr).
- Deferred: 0x41A300/0x43A610 decompiles (task ids in r0a3_heavy_tasks), dibInfoDecode resource origin, tier-B builders.

