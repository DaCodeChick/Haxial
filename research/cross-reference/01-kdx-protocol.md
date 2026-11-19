# 01 — KDX (Scott Anderson) — Scope Check (R0-A.2)

Repo: `~/Documents/GitHub/kdx` (read-only).

## What it is

"A Rust implementation of the Haxial **KDX protocol**: a client, a tracker,
and later a server, all compatible with the original KDX programs (Server
1.620, Client 1.600, Tracker 1.110)." (README)

Tools: `kdx` (CLI client: browse/download/upload/chat/news/accounts),
`kdx-probe`, `kdx-tracker`, `kdx-dissect` (pcap decoder), plus a `lab/`
sandbox that runs the original Haxial programs and captures traffic, a
`vendor/fetch` manifest for the Haxial archives, and headless Ghidra
tooling (`re/ghidra`, `re/ghidra-native`).

## Relevance to this project

- **No HAP work.** Grep-verified across `docs/`, `crates/`, `captures/`:
  no `%HAP` magic, no `.hap` parsing, no appearance handling. The "hap"
  matches in their docs are the English word "happens". **KDX is not a
  cross-implementation for the HAP format** — that role belongs to
  OpenKDX (see `00-openkdx.md`).
- **Adjacent research value:**
  1. **Methodology**: sandboxed capture lab + headless Ghidra + vendor
     manifest is a useful pattern (we already do Ghidra + corpus; a
     controlled runtime capture of a real KDX client would fill our main
     evidence gap — a non-editor Haxial client rendering appearances).
  2. **Integration surface**: KDX is how Haxial systems distribute
     content — `.hap` appearances (and `.fnt` fonts) are plausibly
     served/downloaded over the KDX protocol by real deployments. The
     future Rust toolkit's file layer should therefore be protocol-
     agnostic (it already is: HAP is a plain file format).
  3. **Corpus provenance**: their `vendor/MANIFEST.md` lists the Haxial
     archives we draw our corpus from — a provenance cross-check target
     (verify our 111 `.hap` / 11 `.fnt` against their manifest hashes when
     convenient).
- **Non-goals for us**: no KDX protocol work is in scope for the
  appearance-toolkit reimplementation (different subsystem).

## Status

Scope-check complete (2026-11-18, R0-A.2). No format reconciliation
required. If a runtime KDX client capture becomes available, revisit for
rendering cross-checks of the model in
`../appearance-edit/11-widget-geometry-and-rendering.md`.
