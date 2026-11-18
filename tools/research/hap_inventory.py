#!/usr/bin/env python3
"""hap_inventory.py — read-only structural inventory of the Haxial reference corpus.

Scans refs/appearances/ and refs/fonts/ (configurable), records path, size,
SHA-256, leading bytes, and ASCII FourCC occurrences, and groups files by
leading-byte signature. Read-only: never writes to or modifies scanned files.

Output:
  stdout — compact human summary
  --json PATH — machine-readable summary (default: none)

Usage:
  uv run --script tools/research/hap_inventory.py [--root PATH] [--json OUT]
"""
import argparse
import hashlib
import json
import re
from pathlib import Path


def scan(path: Path):
    data = path.read_bytes()
    h = hashlib.sha256(data).digest().hex()
    size = len(data)
    head = data[:32]
    # FourCC candidates: all-uppercase runs of 4+ letters, or mixed-case 4-letter
    # runs; record offset and text.
    fourccs = []
    for m in re.finditer(rb"[A-Za-z]{4,}", data):
        run = m.group(0)
        text = run.decode("latin1")
        if text.isupper():
            fourccs.append((m.start(), text[:12]))
        elif len(run) <= 8 and run[0:1].isalpha() and run[1:2].isupper():
            # mixed-case starts: potential Pascal/ASCII name; record short ones
            fourccs.append((m.start(), text))
    # cap list size
    fourccs = fourccs[:40]
    return {
        "path": str(path),
        "size": size,
        "sha256": h,
        "head32_hex": head.hex(),
        "head32_ascii": "".join(chr(c) if 32 <= c < 127 else "." for c in head),
        "fourccs": fourccs,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default="refs")
    ap.add_argument("--json", default=None)
    args = ap.parse_args()

    root = Path(args.root)
    entries = []
    for sub in ("appearances", "fonts"):
        base = root / sub
        if not base.exists():
            continue
        for p in sorted(base.rglob("*.hap")) + sorted(base.rglob("*.fnt")):
            if p.is_file():
                entries.append(scan(p))

    # group by head-8 signature
    groups = {}
    for e in entries:
        sig = e["head32_hex"][:16]
        groups.setdefault(sig, []).append(e["path"])

    print(f"files: {len(entries)}")
    print("groups by first 8 bytes:")
    for sig in sorted(groups, key=lambda k: -len(groups[k])):
        print(f"  {sig}  x{len(groups[sig])}")
        for p in groups[sig][:4]:
            print(f"      {p}")
        if len(groups[sig]) > 4:
            print(f"      ... +{len(groups[sig]) - 4} more")

    print("\nsize extremes:")
    for e in sorted(entries, key=lambda x: x["size"])[:3]:
        print(f"  {e['size']:>8}  {e['path']}")
    for e in sorted(entries, key=lambda x: -x["size"])[:3]:
        print(f"  {e['size']:>8}  {e['path']}")

    if args.json:
        Path(args.json).write_text(json.dumps(entries, indent=1))
        print(f"\njson written: {args.json}")


if __name__ == "__main__":
    main()