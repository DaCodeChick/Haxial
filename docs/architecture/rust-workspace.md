# Rust Workspace Architecture — Approved Design Decisions

Status: **owner-approved architectural decisions** (2026-11-21). These are
design choices for the planned Rust reimplementation. They are **not**
findings derived from the original executable and must not be cited as RE
evidence. No crate scaffolding, Cargo manifests, or Rust code exist yet —
this is a planning record only. Trait signatures are deliberately **not**
finalized; the `haxial-core` contents are to be informed by completed
research (stages S1/S2) rather than designed in advance.

## Crate map and dependency direction

```text
haxial-ui
├── haxial-core
├── haxial-wgpu (optional)
│   └── haxial-core
├── haxial-sdl (optional)
│   └── haxial-core
└── haxial-win32 (optional)
    └── haxial-core

haxial-compat   (standalone; no dependency on haxial-core at present)
```

All dependency relationships must remain **acyclic**.

## Decisions

### D1 — `haxial-core` (new)

Defines backend-independent contracts, traits, and any supporting types
**genuinely required by those contracts**. It must not become a miscellaneous
collection of shared utilities. Its precise contents are to be informed by
the completed research (widget model, resource model, rendering/ink abstractions
recovered in S1/S2) rather than prematurely designed.

### D2 — Backend crates implement the contracts

`haxial-wgpu`, `haxial-sdl`, `haxial-win32` (and any future third-party
backend) implement the `haxial-core` contracts. They **depend on
`haxial-core`** and **must not depend on `haxial-ui`**. Backend
implementations should not require knowledge of the concrete high-level
widgets implemented by `haxial-ui`.

Do **not** assume that rendering, window management, input handling, and
platform integration must all be represented by a single backend trait —
the contract surface is to be shaped by what the recovered architecture
actually separates (see S2 dispatch findings: paint, key/pointer events,
and message bubbling are distinct paths).

### D3 — `haxial-ui` is the public UI framework

Primary public-facing UI framework and integration crate. Depends directly
on `haxial-core`; integrates concrete backend crates through **optional
Cargo dependencies and feature gates**. The **wgpu backend is the intended
primary backend**.

### D4 — `haxial-import` renamed to `haxial-compat`

The planned compatibility crate is now **`haxial-compat`**. It is
responsible for compatibility with legacy Haxial formats (`.hap` v1/v2,
`.fnt`, built-in resource records) and associated **conversion**
requirements — not limited to one-way importing.

**Dependency constraint:** do **not** introduce a dependency from
`haxial-compat` to `haxial-core` without a demonstrated technical
requirement. At present, legacy format parsing has no inherent dependency
on rendering contracts; keep `haxial-compat` independently usable. If
future shared representations justify a dependency, evaluate it at that
time.

### D5 — Architectural constraints (standing rules)

- Dependencies must reflect actual technical requirements, not merely
  conceptual relationships.
- Legacy binary layouts must **not** dictate modern Rust runtime object
  layouts (keep on-disk serialization and runtime objects separate —
  consistent with the S1/S2 finding that on-disk and in-memory
  representations differ systematically).
- Preserve verified Haxial behavior without unnecessarily reproducing
  historical platform restrictions (e.g., GDI-specific paths are not
  binding on a wgpu backend).
- Keep compatibility functionality separate from modern rendering
  infrastructure.
- Preserve the ability to support third-party backend implementations.
- Do **not** finalize trait signatures during the research sessions;
  do **not** create Cargo manifests, crate scaffolding, or Rust
  implementations until S2 is complete (S3 scope).

### D6 — `haxial-win32` is the first backend implemented in S3

(Owner-approved design decision, 2026-11-24. Not a reverse-engineering
finding.)

- **Implementation order:** `haxial-win32` is the **first** backend
  implemented during S3, ahead of `haxial-wgpu` and `haxial-sdl`.
- **Bindings:** it uses Microsoft's Rust **`windows` crate** for the
  underlying Win32 platform bindings.
- **Purpose:** to establish a **behavioral and rendering reference**
  against the platform facilities used by the original AppearanceEdit
  executable (GDI 32bpp top-down DIB blits, SetTimer, windowless
  message dispatch, and the other platform calls recovered in S1/S2).
  Haxial implements its **own toolkit behavior and custom widget
  rendering**; the `windows` crate supplies only the platform bindings.
- **Encapsulation:** Win32-specific types and implementation details
  remain **encapsulated within `haxial-win32`**. They do not leak into
  `haxial-core` or `haxial-ui`.
- **Primary backend unchanged:** `haxial-wgpu` remains the intended
  **primary cross-platform backend** (D3). The Win32 backend's reference
  role does not change that.
- **Dependency constraints unchanged:** all previously approved crate
  dependency constraints (D1–D5, including the `haxial-compat` ↔
  `haxial-core` constraint) remain unchanged.
- **No premature freezing:** backend-independent contracts evolve through
  practical implementation and validation; platform-specific assumptions
  discovered in `haxial-win32` are **not** prematurely frozen into
  `haxial-core`.
- **Scope boundary:** this decision does **not** authorize
  implementation, scaffolding, execution of the original executable, or
  advancement into S3.

## Runtime validation checklist (future — `haxial-win32`)

Checklist items to validate during S3 Win32-backend implementation
against the original executable's behavior. Derived from documented
research findings; not research findings themselves.

- **SLDR render-vs-press arithmetic discrepancy (S2 D-late, doc 19 §5.5,
  doc 17 §22.4):** the original's slider render/snap term is
  code-CONFIRMED as proportional to **max/value** (byte-verified at
  0x42BA4E–0x42BA77 and the vertical branch; the trailing FPU
  "correction" idiom proven algebraically dead), which places the thumb
  past the track end for any value < max; the press mapping is the normal
  value/max mapping, and screenshots show mid-track thumbs the render
  term cannot produce. **Both the observed arithmetic and the expected
  value/max behavior are preserved in the research record; neither is
  selected as authoritative yet.** A Win32 runtime capture of the original
  (or a second build) is the planned resolution. Until resolved, SLDR
  geometry is not implementation-ready.

## Naming correspondence to recovered entities (reference, non-normative)

| Recovered Haxial concept (see research/appearance-edit) | Likely modern home |
|---|---|
| Widget class registry / node model (doc 17 §6, §15) | `haxial-ui` (widget tree) + `haxial-core` (node/identity contracts) |
| `%VUU` window records / instance tables | `haxial-compat` (parse) + `haxial-ui` (runtime windows) |
| `%MNU` menus (doc 17 §8) | `haxial-compat` (parse) + `haxial-ui` (menu widgets) |
| HAP v1/v2 resource records, 9-slice, ink objects (docs 04, 14) | `haxial-compat` (parse/convert) |
| 32bpp DIB compositing model (doc 11) | `haxial-core` (surface/ink contracts) + backends |
| Font pipeline / `.fnt` (docs 03, fonts/) | `haxial-compat` (parse) + `haxial-core` (text contracts) |
