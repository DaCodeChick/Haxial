# 00 — OpenKDX Reconciliation (R0-A.2)

Repo: `~/Documents/GitHub/openkdx` (read-only). Primary source compared:
`docs/formats/hap.md` (their HAP spec, "read/write, byte-exact over all 111
files of Haxial's appearance pack") and the `openkdx-legacy` codec.

**Bottom line: the two models are byte-identical over the entire 136-byte
header and all observed section bodies.** Every apparent discrepancy
carried into R0-A.2 is resolved as a difference of *description
convention*, not of bytes. Details and verdicts below. Where they differ in
*completeness* (v2 features, flag semantics, nine-patch meaning), our model
is more complete because it is derived from the editor binary (which can
write v2), while OpenKDX is derived from the 111-file v1 corpus only.

## 1. Section directory — RESOLVED (our 6-slot framing is correct; the 13-slot framing is a v1-corpus artifact)

- **OpenKDX**: 13 × (u32 offset, u32 length) table at **0x0C** (104 bytes,
  0x0C..0x74), "sections, contiguous and in index order"; sections 0–3 and
  8–12 "never seen non-empty".
- **Us (R0-A)**: 6-slot directory at **0x2C** (A, C, D, E, F, G); 0x0C/0x0D
  = scale-option nibbles; 0x0E..0x2B and 0x5C..0x7B reserved.

**Deciding evidence (R0-A.2 corpus scan)**: all 111 v1 corpus files have
bytes 0x0C..0x2B all zero (option nibbles (0,0) in every file) — which is
why the region "looks like" four unused slots. But the **built-in v2 blob A
(R0-A.1 extraction) carries `01 01` at 0x0C/0x0D** — exactly the writer's
default scale option (`hapSerialize`: no selection → writes hi=1, lo=1). A
13-slot directory would read those as a non-zero section-0 offset, which the
editor never writes. **Verdict: 0x0C/0x0D are the option nibbles, 0x0E..0x2B
is reserved; the true section directory is the 6 slots at 0x2C..0x58.**
OpenKDX's 13-slot framing is a natural but unsupported over-generalization
from the all-zero v1 corpus (their decoder still round-trips the 111 files
byte-for-byte because the bytes are identical; the framing only matters for
files the editor actually writes, which carry the `01 01` default). Our
slot indices: A,C,D,E,F,G = slots 4,5,6,7,8,9 in their numbering.

## 2. Header fixed tail + flag region — RESOLVED (same bytes)

- **OpenKDX**: `0x74 | 20 | 00×8, 01 01 01 01, 00×8 in every file`.
- **Us**: 0x5C..0x7B reserved (zero); **0x7C..0x81 = six flag/encoding
  bytes**; 0x82..0x87 reserved (zero).

Corpus scan (all 111 files): bytes 0x7C..0x81 are **`01 01 01 01 00 00` in
every file** — matching OpenKDX's constant `01 01 01 01` followed by zeros.

**Important nuance we add (from the editor parser, `hapParse`)**: these six
bytes are *encoding selectors / enable flags*, not "present" indicators, and
**they do NOT imply non-zero size**:
- 0x7C = Block A valid (must be 1 else timestamps default to now)
- 0x7D = C encoding (1); 0x7E = D encoding (1 = v1 permutation, 2 = v2 direct)
- 0x7F = E encoding (1 = v1 192-row, 2 = v2 %IKN); 0x80 = F enable; 0x81 = G enable
- A section is actually *present* when its **length** (from the directory) is
  non-zero — **80 of 111 files have E_size=0 and 73 have C_size=0** while
  still carrying flag bytes `01 01 01 01 00 00`. So the flag is set even when
  the section is empty.
- In **v2** (written by this editor build) 0x7E=2, 0x7F=2, 0x80=1, 0x81=1 —
  a pattern OpenKDX could not observe (corpus is all v1; they round-trip only
  the 111 v1 files).

**Verdict: identical bytes over v1; our flag semantics + v2 values are the
more complete model.**

## 3. Colour word byte order — RESOLVED (our R0-A label was wrong; OpenKDX's raw-byte description is right)

- **OpenKDX**: D colours are `00 RR GG BB` (describing the on-disk byte
  sequence: byte0=0x00, byte1=R, byte2=G, byte3=B).
- **Us (R0-A)**: "u32 LE value **0x00BBGGRR** (GDI BGR; alpha 0x00)".

**Corpus evidence (raw bytes of D words)**: e.g. `BeOS.hap` word1 =
`00 cc cc cc`; `Blue Fragmentation.hap` word1 = `00 50 6f 9f` (R=0x50,
G=0x6F, B=0x9F — a blue, matching the name); `Ashen.hap` word1 =
`00 ff ff ff`. The on-disk byte order is unambiguously **`[00][R][G][B]`**.

So:
- On-disk bytes: `[00][RR][GG][BB]` = OpenKDX's `00 RR GG BB` = big-endian
  u32 value `0x00RRGGBB`.
- Native little-endian x86 load of those 4 bytes = `0xBBGGRR00` (**not**
  `0x00BBGGRR` — our R0-A label conflated this).
- The in-memory **GDI 32bpp DIB** pixel is `0x00BBGGRR` (BGR, high byte
  0x00) — standard BI_RGB. The only blit is `SetDIBitsToDevice` (BI_RGB
  32bpp), so DIB pixels must be GDI-ordered.
- Therefore a **bswap32** relates the native on-disk load (`0xBBGGRR00`) to
  the GDI DIB pixel (`0x00BBGGRR`). (The exact conversion site in the
  colour→DIB path is a UI-layer milestone, but the byte-order facts are
  confirmed.)

**Verdict: OpenKDX's `00 RR GG BB` is the correct on-disk description. Our
"0x00BBGGRR" was the *in-memory GDI* value and was mislabelled as the on-disk
LE value. Corrected in `04-hap-format.md`.** For the Rust re-implementation:
store the on-disk colour as bytes `[00, R, G, B]` (or BE u32 `0x00RRGGBB`),
and convert to GDI `0x00BBGGRR` only at DIB fill time.

## 4. Section names — RESOLVED (letter model vs numbered slots)

| Us | OpenKDX | Holds |
|---|---|---|
| Block A | section 4 "information" | created/modified (Time1900), 18 zero, 4 len bytes (name,version,creator,description), 14 zero, strings, pad 4 |
| C | section 5 "images" | 512-slot table (OpenKDX says **528-slot**; see §5) + bitmap records **with** 12-byte extra header |
| D | section 6 | 204 colours `00 RR GG BB` |
| E | section 7 "icons" | 192-row table (OpenKDX says **768-slot**; see §5) + bitmap records **without** extra header |
| F | (v2, not in their 1–7 table) | ink resources |
| G | (v2) | %MSI / mouse |

**Verdict: same sections, different labels.** OpenKDX's "images"=our C,
"icons"=our E. Their "section 4/5/6/7" = our "A/C/D/E".

## 5. Slot-table sizes — RECONCILED (same 0x840/0xC00 bytes, different slot count)

- **C / "images"**: OpenKDX "a **528-slot** table"; us "**512-slot** table"
  at +0x40 (section min 0x840 = 0x40 preamble + 512×4). 528×4 = 0x840 = the
  *whole* pre-pool region; 512×4 = 0x800 sits after a 0x40 (64-byte) zero
  preamble. **Same bytes** — OpenKDX counts the 0x40 preamble as 16 leading
  zero slots (16 + 512 = 528), we count a 0x40 preamble + 512 slots. Our
  reader/writer disassembly (`hapCSectionWrite`: table entry at
  `section + 0x40 + slot*4`, 174 (0xAE) doc entries, min 0x840) supports the
  0x40-preamble + 512 reading. **Verdict: identical bytes; slot anchor
  differs. Both round-trip.**
- **E / "icons"**: OpenKDX "a **768-slot** table"; us "192 rows × 16 bytes"
  (`[u32 offA][u32 offB][8 reserved]`). 192 rows × 4 u32 = 768 u32 slots =
  0xC00. **Same bytes** — OpenKDX sees four u32 slots per 16-byte row (two
  used offsets + two reserved), we see 192 rows of (offA, offB, reserved).
  **Verdict: identical bytes; row-vs-slot framing differs.**

## 6. Bitmap record + nine-patch extra header — RECONCILED (same 12 bytes; different field names)

Both agree the base bitmap record is:
`[u16 W][u16 H][1 flag][1 bpp][1 pal-1][1 trans-index]` then palette then
pixels (rows padded to 4, MSB-first). Differences:

- **Flag byte**: OpenKDX "flag: 1 when byte 7 names a transparent palette
  index". Us (C blob): bit 0x10 = extended header, bits 0x0F = secondary-row
  mode; the transparency flag is bit 0. For the C ("images") record the flag
  byte carries **both** the 0x10 extended bit and the 0x0F secondary mode;
  OpenKDX reads bit 0 as the transparency flag. Note: in the C blob the
  transparent-index-at-byte-7 usage is the *E/%IKN* convention; the C blob's
  byte 7 is "unused" per our parser. This is a minor per-section nuance, not a
  byte conflict.
- **12-byte extra header** (C/"images" only):
  - OpenKDX: "a colour (`00 RR GG BB`), four bytes that look like insets
    (`08 08 07 07`, `0b 0b 0a 0a`), a word (0, `04 00 00 00`, …)" — all marked
    `[I]` (inferred), and they state "nothing is rendered yet".
  - Us (decoded + corpus-verified, 18 built-in v2 samples): `[u32 colour
    (0x00FFFFFF or 0x00000000)][u8 capL][u8 capT][u8 capR][u8 capB][u8
    insetL][u8 insetT][u8 insetR][u8 insetB]`.

  **The middle four bytes (0x0C..0x0F) are the nine-patch caps**, verified by
  nine-slice arithmetic on all 18 samples (capL+capR < W, capT+capB < H; for
  slot 73 (26×8) caps (3,3,22,4) only the [L,T,R,B] assignment is valid).
  OpenKDX guessed "insets" for these and "a word" for the last four; we show
  the middle four are caps (arithmetic) and the last four are the content
  insets (the editor's Left/Right/Top/Bottom Inset fields). **Verdict: same
  12 bytes; our field assignment is better supported (rendering evidence +
  arithmetic), OpenKDX's is an uninformed guess (they haven't rendered).**
  See `11-widget-geometry-and-rendering.md` §2.

## 7. Where each model is more complete

| Topic | More complete model | Why |
|---|---|---|
| Full 13-slot header framing at 0x0C | **OpenKDX** (but see §1: a v1-corpus artifact — the `01 01` scale nibbles in the built-in v2 blob disprove it) | documents slots 0–3, 10–12 |
| Flag semantics + v2 values (0x7E/0x7F=2, 0x80/0x81=1) | **Us** | from the editor parser/writer (v1 corpus can't show v2) |
| "Present" = non-zero length, flags are encoding selectors | **Us** | corpus: 80 files E_size=0, 73 C_size=0 with flags still set |
| On-disk colour byte order (`00 RR GG BB`) | **OpenKDX** (we corrected to agree) | raw bytes |
| Nine-patch cap field identification + order | **Us** | arithmetic + editor UI; they mark it `[I]` and unrendered |
| F/G sections, v2 E (%IKN), v2 D (54 direct) | **Us** | v2-only, absent from their v1-only corpus round-trip |
| Editor could not be diffed by them | **Us** | they note Appearance Editor 1.240 "ignores a file given on the command line"; we decompiled 1.400 in Ghidra |

## 8. Recommendations for the Rust re-implementation (not adopted yet)

1. Model the header as: magic, version, option nibbles (0x0C/0x0D), reserved,
   **6 (off,len) pairs at 0x2C** (A,C,D,E,F,G), reserved, flags 0x7C..0x81,
   reserved — with our flag semantics and v2 values. (Keep OpenKDX's framing
   in mind for their interop: their "slots 4–9" = our six pairs.)
2. Keep on-disk colours as `[00,R,G,B]` bytes; convert to GDI `0x00BBGGRR`
   only when filling a 32bpp DIB.
3. For C ("images") records, parse the 12-byte extra header as
   [colour][capL,capT,capR,capB][insetL,insetT,insetR,insetB] and implement
   nine-patch stretching (fixed caps, stretched centre ≥1×1).
4. Treat section *presence* by length, not by the flag bytes.
5. OpenKDX's UI/rendering (Phase 6) is unimplemented — our
   `11-widget-geometry-and-rendering.md` (blit model, no GDI text, 9-slice,
   composite scrollbars) is the first evidence for that phase and should be
   cross-checked against a real KDX client once available.

## 9. Open questions / residual discrepancies

- C/"images" slot anchor (0x40 preamble + 512 vs 528): bytes identical, but
  a v2 file with a non-zero preamble would disambiguate; none observed.
- The 0x08..0x0B "colour" in the extra header: white vs black in samples —
  likely a backing/underneath colour (editor "Transition (underneath)");
  needs a rendering test to confirm role.
- Exact byte-swap site for colours in the editor's DIB path (UI-layer
  milestone).
- OpenKDX "flag is 0 or 1; anything else rejected" for the transparency
  flag vs our "bit 0" reading — consistent, but confirm on a record where
  byte 4's other bits (0x10, 0x0F) are set alongside bit 0.
