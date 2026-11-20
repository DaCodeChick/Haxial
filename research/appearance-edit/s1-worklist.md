# S1 worklist — UI rendering pipeline, widget composition, resource dispatch

Session S1. Baseline: eaff8a0 (R0-A.3). Program: AppearanceEdit.exe, x86:LE:32, base 0x400000.

## Priority order (per task)
1. Dynamic skin-resource selection and dispatch (FUN_004093E0, provider vtable 0x48D30C..41C, gStyleRec/gStyleDef/gIconGrid, magic 0x8521B2D1, vtable +0x1C)
2. Widget painters (4 widgetBlit callers re-verified: labelWidgetPaint 0x410960, compositeWidgetPaint 0x43BC00, iconGridPaint 0x4514C0, listRowPaint 0x446770; + scrollbar/slider/tick/menu via dispatch)
3. Bitmap expansion: 9-slice runtime algorithm (cap/inset consumers), transparency, fill modes (candidates 0x42E370, 0x42DC90 = clip helpers per 11 §1; 0x425C30=bmpSetFillModeRaw, 0x426610=bmpBlitPair, 0x42A170=widgetBaseFill, 0x4459E0=rectIntersects — all already reconciled)
4. Geometry/state bits 0x01/0x02/0x20 writers
5. D-section 54 color roles (dSub = doc+0x30, colors at +0x16)
6. Text/font: 0x44DFE0 glyph blit, font resource acquisition
7. Open questions (v1 E mapping, %IKN fields, %MSI hotspot, C ext-header field0)
8. Readiness assessment

## Status
### Completed
- (none yet)

### In progress
- Batch 1: dispatch core (FUN_004093E0 decompile, provider-vtable writers, gStyleRec writers, 0x8521B2D1 refs)

### Pending
- Batch 2: four painters deep-dive + vtable layout + state-bit writers
- Batch 3: 9-slice stretch algorithm (cap/inset consumers), fill modes, transparency
- Batch 4: D-color role consumers, colors.png correlation
- Batch 5: text/font pipeline (0x44DFE0, font resource, metrics)
- Batch 6: remaining screenshots (colors, mouseicons, popupmenu, hscrollbars, sliders, tickbuttons, listlabelcolors, menu)
- Batch 7: deferred decompiles (0x41A300, 0x43A610, 0x40E570, converter families) — check old task ids once (r0a3_heavy_tasks)
- Batch 8: Ghidra enrichment pass (renames/protos/locals/types/comments, read-back verified)
- Batch 9: docs 13–17 + updates (00,04,05,06,07,10,11) + commit

### Deferred / blocked
- (none yet)

## Reconciliation notes (R0-A.3 carryovers)
- 0x425C30 = bmpSetFillModeRaw, 0x426610 = bmpBlitPair, 0x42A170 = widgetBaseFill, 0x4459E0 = rectIntersects (all done)
- 0x42E370, 0x42DC90 = clip-intersect helpers (per 11 §1 winBlitDib note) — NOT yet decompiled/renamed
- dibInfoDecode sole caller 0x41d0b0 = provider-thunk (vtable 0x48D30C..41C) — resource origin = same provider object as priority 1
- gStyleRec (0x466954) population path UNKNOWN — writers must be found
- vtable +0x1C = per-widget virtual method (fill/paint?) — layout to be recovered
## Batch 1 findings (dispatch core) — 2026-11-18

### S1-F1 (CONFIRMED): global skin context = raw section pointers into the loaded HAP v2 blob
`skinInstall` (0x428c70, ex-FUN_00428c70; installer `skinApply` 0x435030; entry
`appearanceLoadInstall` 0x402fa0 / `appearanceResetDefault` 0x403020):
- gStyleRec (0x466954) = blob + BE32(blob[0x34]) = **C section base**; C+0x40 = 512-slot BE u32 table of **C-relative** blob offsets
- gStyleDef (0x466950) = embeddedBlobB + bswap(B[0x52]) (fallback; B runtime layout unresolved)
- gStyleDColors/gStyleDColorCount (0x46695C/60) = D section base + BE32(blob[0x40])>>2 = **54**
- gInkTbl/gInkCount = E section base + byte length (<5 → none); gInkF/gInkFSize = F; gInkG/gInkGSize = G
- gScaleNum/gScaleDen = header bytes 0x0C/0x0D (scale nibbles, 01/01 = 1:1)
- 7×5 u16 metric scaling tables @0x466994..0x4669B3 = base tables 0x466703b? no: 0x46703b..0x467041 (interleaved 7 rows × 5 cols) × scaleNum/scaleDen
- hapHeaderValidateV2 (0x4287f0): %HAP, ver==2, scale nibbles non-zero, 6 dir slots @0x2C — **install accepts v2 only**
- Painters index sections directly (no per-resource rich objects) — dispatch model established

### S1-F2 (CONFIRMED): C-blob format CORRECTION (supersedes 04-hap-format.md §C and 11 §2 layout)
```
+0x00 u16BE W, +0x02 u16BE H, +0x04 flags (0x10 ext, 0x0F sec-mode), +0x05 bpp, +0x06 pal (count-1), +0x07 transIdx?
+0x08 u32 field0 (0x00FFFFFF/0x00000000)
+0x0C capL, +0x0D capT, +0x0E capR, +0x0F capB   (caps in BASE header, always)
+0x10 u32 field2 (0 in samples)
+0x14 [12 bytes ext if flags&0x10: word@0x14 = fill colour input, byte@0x1D, byte@0x1F = content offsets]
+hdr  palette: (pal+1) × 4 bytes [00][RR][GG][BB]   (PALETTE BEFORE PIXELS — R0-A.2 "palette last" disproven)
+...  pixels: rowbytes×H (rowbytes = 32/16/8/4-px aligned)
+...  secondary rows if sec-mode 2/4/8
hdr = 0x14 + (ext?0xC:0); size = hdr + rows + sec + (pal+1)*4 (hapCBlobParse 0x406e20)
```
Verified on slots 9/10/11/21/22/23/33/34/35 of built-in A: exact tiling (e.g. slot34 7×7 plain = 20+24+28 = 72B = span to next slot; slot33 ext = 32+44+28 = 104B exact).
C section in-file layout: [preamble 0x00..0x3F][table 512×u32 @+0x40 (C-relative offsets)][entries 174×0x14 @+0x4C (runtime-written: +0x08 blobPtr, +0x0C size, +0x10 u16 slotIdx)][... 0x840][pool]. hapCSectionRead walks the entry array at [doc+0x2C]+0x4C.

### S1-F3 (CONFIRMED): 9-slice runtime algorithm (nineSliceBlitC 0x4293b0)
- corners: 4 exact copies (bmpBlitToSurface; ext: bmpBlitAlpha w/ transIdx = header byte 0x07)
- edges: 4 bands via nineSliceStretchH/V = per-pixel replication (each dest pixel filled with dibSamplePixel of the source edge pixel) — NEAREST-NEIGHBOUR replication, not texture stretch
- centre: plain → fill with sampled centre pixel colour (dibSamplePixel → bmpSetFillModeRaw → bmpFillChecked); ext → pre-fill content rect (x+capL, y+ext[0x1D], right-capB, bottom-ext[0x1F]) with ext colour (word@0x14) via extContentFill, skip centre fill
- bmpFillChecked: magic check 0xF4DA120B @+0x44, fill colour = surface+0x38 (CORRECTION: +0x38 is fillColor, not "fillMode")

### S1-F4 (CONFIRMED): state-icon banks + state bits
- bmpStateIconDraw: bit 0x20 → bank B (slots 21/22/23), else bank A (9/10/11); +1 for bit 0x01, +2 for bit 0x02
- slot value = C-relative offset; fallback: [0x46691C]+0x34+0x40+slot*4
- widgetStateSet (0x4093e0): u16 state @+0x0D, constraint rules (bit0→clear 0&3; no-bit1→clear bit0), virtual notify via (widget+4)+0x5C vtable slot 0 (widget, old, new)
- Built-in A icon sizes: bank A = 11×11(9slice)+8×8+8×8, bank B = 17×17(9slice)+14×14+14×14

### S1-F5 (CONFIRMED): built-in blob locations (R0-A.1 symbol correction)
- 0x4683D4 = contiguous %HAP v2 blob (grey-ramp D section — the "blank" default theme?)
- 0x466DD4 = TSLC fragment table (84 ptrs) — runtime-assembled Evil Chiaroscuro (assets/builtin-EvilChiaroscuro-v2-A.hap); the extracted "B" file is raw fragment storage, not a HAP
- Embedded blob D section = 54 × [00][RR][GG][BB] LE u32 (grey ramp C4C4... in 0x4683D4; black/666666/.../red in EC)

### Ghidra applied (read-back verified): 15 renames (nineSliceBlitC, dibSamplePixel, dibSamplePixelTrans, bmpFillChecked, nineSliceStretchH/V, cBlobHeaderDecode, extContentFill, bmpBlitAlpha, widgetStateSet, skinInstall, hapHeaderValidateV2, skinApply, appearanceLoadInstall, appearanceResetDefault), 8 global renames, hapBitmapObj.fillMode→fillColor, nineSliceBlitC proto, 14 comments

### In progress
- D-color role consumers (xrefs 0x46695C), button paint dispatch (compositeWidgetPaint callers), text/font (0x44DFE0), scrollbars, screenshots, deferred decompiles

## S1 FINAL CHECKPOINT — 2026-11-18 (session complete)

### Batches 2–7 outcomes
- **Batch 2 (painters)**: buttonWidgetPaint/buttonHoverSet/widgetStateSet/button object layout resolved (doc 13 §3, doc 15 §1–2). Scrollbar/slider composition established from screenshots + E icon names (doc 15 §4–5); per-pixel geometry functions not individually pinned (carried to S2).
- **Batch 3 (9-slice)**: FULLY RESOLVED with corrections (doc 14): base-header caps, palette-before-pixels, per-pixel edge replication, centre fill / ext content fill. Tiling byte-exact on built-in A.
- **Batch 4 (D colors)**: styleColorGet + 54 roles + fallback resolved (doc 13 §2.1); **role NAMES found** in gColorRoleNames (doc 16 §1); per-painter role-index constants still open.
- **Batch 5 (text/font)**: inkBlitCore (0x44DFE0) = ink/glyph blit core (bmpInkBlit/bmpTextDraw callers), colour bswap + entry table @+0x10 (doc 13 §2.3). E = ink/glyph section confirmed as the text path. .fnt → ink pipeline open.
- **Batch 6 (screenshots)**: 11 more examined (17/22 total; doc 15 §3–7, doc 10 updated). mouseicons.png = app-builtintheme-blank/ (path correction).
- **Batch 7 (deferred decompiles)**: 0x41A300 = fileClose (registry unlinks ×2), 0x43A610 = fmtByteCount — both resolved (doc 13 §5).
- **BONUS**: on-disk EXE scan found gColorRoleNames (53 D roles + 6 groups) and gEIconNames (155 E icons) — doc 16; and corrected the R0-A.3 "provider vtable" hypothesis → .idata IAT (doc 16 §3). PE section table recovered (.text/.rdata/.data/.rsrc/.bss offsets). Late-batch screenshots: colors (D roles → gColorRoleNames), mouseicons (named %MSI cursor set — cursors are appearance resources), icons (named icon list matching pstrs @0x4626D0).

### Ghidra session total (all read-back verified)
- Function renames: 20 (nineSliceBlitC, dibSamplePixel, dibSamplePixelTrans, bmpFillChecked, nineSliceStretchH/V, cBlobHeaderDecode, extContentFill, bmpBlitAlpha, widgetStateSet, skinInstall, hapHeaderValidateV2, skinApply, appearanceLoadInstall, appearanceResetDefault, styleColorGet, buttonWidgetPaint, buttonHoverSet, inkBlitCore, fmtByteCount)
- Data renames: 16 (gStyleDColors, gStyleDColorCount, gInkF, gInkFSize, gInkG, gInkGSize, gScaleNum, gScaleDen, gStyleDColorsFallback, gStyleStrA, gStyleStrB, gStyleMetricBases, tableButtonMethods, tableLabelMethods, gColorRoleNames, gEIconNames)
- Function comments: 19; data plate comments: 2 (gColorRoleNames, gEIconNames)
- Types: hapBitmapObj field fillMode→fillColor; nineSliceBlitC prototype set
- Project saved (haxial.gpr)

### Docs
- NEW: 13-s1-resource-dispatch.md, 14-s1-c-blob-and-9slice.md, 15-s1-widget-painters.md, 16-s1-named-resource-tables.md
- UPDATED: 00 (session log), 04 (S1 appendix), 06 (S1 section + addendum), 07 (§5 resolutions + new items), 10 (screenshot corrections), 11 (9-slice correction note)

### Carried to S2 (open)
1. WM_PAINT → per-child paint call site (template walker untraced).
2. Per-painter D role-index constants (consumer mapping).
3. Embedded blob B runtime layout beyond +0x52/+0x60/+0x64; TSLC assembly.
4. E-section runtime ink object layout + .fnt → ink pipeline.
5. C-blob field0/field2/field4; secondary-mode (2/4/8) content + consumer.
6. gStyleStrA/B, gOncePtr (0x46698C→0x47B324), 0x40F220/0x41D390.
7. 54th unnamed D role slot; 155 E names vs 192-row v1 E reconciliation.
8. Scrollbar/slider per-pixel geometry functions.
9. 0x46691C-based object: remaining unmapped fields (object is the "skin context block" @0x46691C..0x4669B3).
