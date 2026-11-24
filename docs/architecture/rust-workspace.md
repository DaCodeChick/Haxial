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

## Naming correspondence to recovered entities (reference, non-normative)

| Recovered Haxial concept (see research/appearance-edit) | Likely modern home |
|---|---|
| Widget class registry / node model (doc 17 §6, §15) | `haxial-ui` (widget tree) + `haxial-core` (node/identity contracts) |
| `%VUU` window records / instance tables | `haxial-compat` (parse) + `haxial-ui` (runtime windows) |
| `%MNU` menus (doc 17 §8) | `haxial-compat` (parse) + `haxial-ui` (menu widgets) |
| HAP v1/v2 resource records, 9-slice, ink objects (docs 04, 14) | `haxial-compat` (parse/convert) |
| 32bpp DIB compositing model (doc 11) | `haxial-core` (surface/ink contracts) + backends |
| Font pipeline / `.fnt` (docs 03, fonts/) | `haxial-compat` (parse) + `haxial-core` (text contracts) |
