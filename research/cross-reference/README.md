# Cross-Reference Notes (R0-A.2)

Third-party Haxial research projects, examined **read-only** (no modifications,
no code copying, no architectural adoption without independent evaluation —
per project rules).

| Repo | Local path | Scope | Relation to this project |
|---|---|---|---|
| **OpenKDX** | `~/Documents/GitHub/openkdx` | Full KDX reimplementation (Rust): protocol + **legacy file codecs** (`openkdx-legacy`, incl. `.hap` byte-exact over the same 111-file corpus) + UI (Phase 6, not yet rendering) | **Direct cross-implementation for the HAP format** — reconciled in `00-openkdx.md` |
| **KDX** | `~/Documents/GitHub/kdx` | KDX **network protocol** only (client/tracker/server vs Server 1.620/Client 1.600/Tracker 1.110) | No HAP work (grep-verified: no `%HAP`/`.hap`/appearance references). Relevant as adjacent Haxial research + future integration point (appearances travel over KDX) — `01-kdx-protocol.md` |

Method: byte-level comparison of their documented format tables against our
corpus evidence (111 `.hap` files) and Ghidra decompilation of
AppearanceEdit 1.400. Where the two disagree, the corpus bytes + editor code
decide.