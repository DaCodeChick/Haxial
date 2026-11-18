# Haxial Reverse-Engineering Workspace — Agent Instructions

## Project overview

This workspace is dedicated to reverse-engineering **Haxial**, a Windows x86 skinnable UI
toolkit, with the long-term goal of reimplementing it as a modern, platform-independent Rust
UI toolkit with new versioned binary formats.

Current primary target: **AppearanceEdit.exe** (Haxial's skin editor, reads/writes
`.hap` appearance files).

Rules in this file apply to ALL agents working in this repository.

## Reverse-engineering workflow

- Research is conducted through the **Ghidra MCP** connection. Verify the active program is
  the intended target before any mutation.
- This is **research only** until explicitly reassigned: no Rust implementation, no final
  format design, no executable patching.
- All findings are documented incrementally in `research/<target>/` as durable Markdown
  with exact addresses, byte offsets, raw byte examples, and evidence chains.
- Findings must be labeled by confidence: **CONFIRMED** (directly observed in code/data),
  **PROBABLE** (strong inference, triangulated evidence), **HYPOTHESIS** (unverified guess).
  Never present an inferred `.hap` field as confirmed without supporting evidence.
- Every significant finding should identify relevant function addresses, data addresses,
  callers, references, or file offsets.

## Legacy string handling — critical

Haxial uses multiple string and identifier representations:

- **Pascal strings:** a one-byte unsigned length prefix followed by exactly that many bytes.
- **C strings:** null-terminated byte sequences.
- **FourCC identifiers:** four-byte codes, commonly represented in little-endian integer
  form, such as `VWIN` and `BUTN`.

Pascal strings may contain UTF-8 byte sequences, including UTF-8 byte-order markers or other
marker bytes. Do not assume ASCII, ANSI, or UTF-8 without examining the actual bytes.

**For Pascal strings, the length prefix is authoritative.**

Never use a trailing null byte, Ghidra's inferred string boundaries, or apparently printable
neighboring bytes to override the declared length.

The only exception is when independent evidence establishes that the data is actually a
null-terminated string rather than a Pascal string.

AppearanceEdit.exe contains garbled or apparently meaningless bytes immediately following
many Pascal strings. These bytes must not be treated as part of the preceding string merely
because Ghidra's analysis incorporated them into a string representation.

For each suspicious string:

1. Inspect raw memory bytes.
2. Identify the candidate string representation.
3. Verify the Pascal length prefix or C-string terminator.
4. Determine the exact byte boundaries.
5. Decode only the verified payload.
6. Preserve undecodable bytes in hexadecimal form.
7. Record uncertainty rather than guessing.

A Pascal string's length counts **bytes, not Unicode characters**.

Do not automatically reinterpret a Pascal string as a C string simply because its payload
contains a null byte.

Do not globally repair or redefine strings until their actual representations are understood.

## FourCC handling

Investigate FourCC values as raw four-byte sequences and as 32-bit little-endian integers.

For example, the bytes `56 57 49 4E` represent the ASCII sequence `VWIN`, but a
little-endian 32-bit integer has the numeric value `0x4E495756`.

Always distinguish:

- Raw byte order
- Human-readable FourCC spelling
- Numeric representation
- Storage location
- Semantic interpretation

Do not assume every four-character sequence is a FourCC.

## Ghidra database protection

**GDT archive-provided definitions are immutable.**

Never rename, edit, delete, replace, or modify:

- GDT-provided structures and unions
- Their fields
- GDT-provided functions and signatures
- Equates
- Enumerations or typedefs supplied by archives
- Other archive-owned data types

This includes indirect changes that could modify an archive-owned definition (e.g.
applying a new prototype to an archive-provided function, or mutating a shared type
reference through a local view).

Program-local symbols and independently created program-local data types may be modified
when supported by evidence.

If provenance is unclear, investigate before changing anything; treat uncertain provenance
as protected.

Symbol changes are recorded in `research/appearance-edit/06-symbol-ledger.md` with original
address, previous name/type, new name/type, evidence, confidence, and verification status.
After each batch of changes, read back affected symbols and verify the modifications
succeeded before claiming completion.

## Evidence and confidence

Separate confirmed observations, strong inferences, and unresolved hypotheses.

Every significant finding should identify relevant function addresses, data addresses,
callers, references, or file offsets.

Never present an inferred `.hap` field as confirmed without supporting evidence.

## Operational safeguards

- Do not change executable bytes, patch instructions, or export modified binaries without
  explicit user authorization.
- Do not re-run full Ghidra analysis or change analysis settings without explaining the
  expected effect and receiving authorization.
- Prefer narrow, verifiable tool calls over large speculative batches.
- Never claim a finding, file write, rename, or type change occurred unless confirmed by
  tool results.

## Repository layout

```
AGENTS.md                      — this file
research/
  appearance-edit/
    00-overview.md             — target summary, session log, status
    01-executable-architecture.md — architecture, subsystems, call graph
    02-strings-and-fourcc.md   — string/FourCC representations and helpers
    03-file-io.md              — file open/save pathways, dialogs
    04-hap-format.md           — .hap format findings (static vs sample-verified)
    05-ui-and-skin-model.md    — editor UI, widget/skin model
    06-symbol-ledger.md        — all Ghidra symbol changes with evidence
    07-open-questions.md       — uncertainties, blockers, next targets
```