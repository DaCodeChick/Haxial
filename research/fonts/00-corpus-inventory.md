# Haxial Font Corpus — Inventory (session R0-A.1)

Scope: `refs/fonts/*.fnt` — 11 reference font files. **Inventory only**: the font
format itself is the subject of a future FontEdit RE session. These are untrusted
external input; no file has been modified.

Full sha256 hashes: `tools/research/corpus-inventory.json`.

## Files

| File | Size | sha256 (16) |
|---|---|---|
| End 0.9.fnt | 0x1C9C | e90d7555e05b5437 |
| Enocht 1.11.fnt | 0x2834 | c6c305e5db658cc9 |
| Harial 0.5.fnt | 0x919C | d26e3ea946f8847f |
| Lies 1.299.fnt | 0x40F8 | 13766619cd7a2bf0 |
| Mjolnir 1.21.fnt | 0x5190 | ca7a395cd8f5dc6b |
| OCRAP.fnt | 0x1C30 | 914212bd8d941a79 |
| Von Yerk 0.9.fnt | 0x4E4C | 10eef9db056987dc |
| XeBob 1.0.fnt | 0x26B0 | 4b4b1d65ece35c0b |
| Yspe Sans 0.91.fnt | 0x662C | 623a4081b7a0e05c |
| Yspe Sans Bold 0.9.fnt | 0x6814 | e142dc5f7ca8a89b |
| bit1.fnt | 0x1850 | f1e22213b9d3ded2 |

## Header pattern (CONFIRMED by 11/11 consistency)

```
0x00  4   magic "%FNT" (25 46 4E 54)
0x04  2   u16 version = 2        (BE byte order — same convention as HAP)
0x06  2   u16 = 1
0x08  4   u32 (LE) total file size  — matches actual size in all 11 files
0x0C  12  zeroed
0x18  4   u32 (LE) font name length
0x1C  …   font name (NUL-padded to 0x40)
0x40  …   font data — structure unanalyzed (future FontEdit session)
```

Observations:
- Endianness is mixed by design, exactly like HAP: structural fields BE,
  self-describing size/name fields LE. (The version field is ambiguous between
  BE-u16 and swap16-of-LE-u16 — both read as 2.)
- `Mjolnir` appears both as a `.fnt` (1.21) and as a `.hap` theme (Mjolnir /
  Mjolnir Win / Mjolnir Mac) — theme fonts are distributed alongside skins.
- No v1 HAP corpus file references fonts directly (v1 has no F section); the
  HAP↔font linkage is the v2 `%IKN` path tag `font/` (see
  `../appearance-edit/04-hap-format.md` §9).

## Confidence

| Claim | Level |
|---|---|
| 11 files, header pattern as above | CONFIRMED |
| Font data layout after 0x40 | not analyzed (out of scope this session) |