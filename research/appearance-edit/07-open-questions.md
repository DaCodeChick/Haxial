# 07 — Open Questions and Blockers (AppearanceEdit.exe)

Session R0-A, 2026-11-17.

## High priority (format-critical)

1. **On-disk `.hap` layout is unconfirmed.** No sample files available. Need:
   real `.hap` files (default + edited), or a save operation to capture bytes.
   Static findings so far are in 04-hap-format.md and must not be treated as
   the on-disk spec.
2. **Save-buffer builder not located.** Trace callers of `fileCreate`/
   `fileOpenMkDir` (`FUN_00417070` is the prime candidate) up to the dialog
   handlers for "Open/Save Appearance File:" (`0x45F760`/`0x45F778` xrefs).
3. **State-record field semantics** (the four u16 pairs after state+type in the
   built-in widget table) — need the code that reads them (renderer or editor
   property panels, e.g. strings "Height:"/"Indexed Color Size:" handlers).
4. **DDE usage** — identify the service/app names and message payloads
   (search `DdeNameService`/`DdeCreateStringHandleW` callers) to understand
   live-apply semantics (does it push a whole `.hap` or deltas?).

## Medium priority

5. The four-byte-swapped fields in the built-in registry (count @ `0x45F844`,
   `out` @ rec+0x0C, offset @ rec+0x10): confirm whether the on-disk format
   uses the same convention or only the in-memory DB does.
6. Menu/window instance names (`MENUexam`, `VWINdoku`, …) — map each of the
   11 `constructApp` init calls to the registry entry it consumes (callers of
   `lookupBuiltInRec`: `FUN_0042A2D0`, `FUN_00408ED0` (passes "VWIN"),
   `FUN_00412490` (passes "MENU"), `FUN_0042B5D0`).
7. The `0x5657494E`/"VWIN" and `0x4D454E55`/"MENU" constants passed as the
   context argument of `lookupBuiltInRec`: the comparison function at
   `0x4457C2` dereferences `[ctx+4]` — with ctx = a FourCC integer this reads
   an address outside the image (e.g. `0x56574952`). Determine whether those
   addresses are meaningful at runtime (DLL-resident data?) or effectively
   dead (the search may be a vestigial validation step).
8. Bitmap/color model: indexed vs. DIB16/24/32; palette storage; the
   "Indexed Color Size" property; how `SetDIBitsToDevice` is fed (find its
   caller).
9. The 11 subsystem init functions in `constructApp` — identity of each
   (menus, toolbars, tray, preview, file browser?).
10. Main window WndProc (candidate `FUN_004038C0`) — command dispatch table
    (menu IDs → open/save/apply/undo, etc.).
11. Formatters `FUN_00439CC0`/`FUN_00439D00` (float pair) and `FUN_0043A610` —
    finalize names of `pstrAppendNum2`/`pstrAppendNum3`.
12. `FUN_00414BF0` — terminal error handler (what the user sees on fatal
    errors); `FUN_00434420` — 0x60-byte error record initializer.
13. String class table @ `0x467D10` (256×1 byte; bits 0x20/0x40) — full decode
    of "forbidden byte" rules for file names.
14. Hash/map structure using `0x466984`/`0x466988` and `0x4683D4`
    (`FUN_00445530`) — role (font cache? resource cache?).

## Blocked / needs user input

- **No `.hap` samples in the workspace** (`/Users/schala/Downloads/` contains
  only the exe; repo is otherwise empty). Any real Haxial installation files
  (skins, `.hap` appearances, config) would unblock items 1–3 and 8.
- **No Haxial runtime/client executable** available to cross-check the parser.
- Running the original exe is not part of this session (research-only; also
  no guarantee of a compatible modern OS for this ~1.4-era binary).

## Suggested next session (in priority order)

1. Trace "Save Appearance File" path: xrefs of `0x45F778` → dialog handler →
   buffer builder → `fileCreate`/`fileWriteWhole`. Document field emission order.
2. Decompile `FUN_00417070` and the open-side counterpart; document the
   load path symmetrically.
3. Find the renderer's state-record consumer (xrefs into the `0x4624xx`–
   `0x4653xx` table) to confirm u16 metric meanings.
4. DDE subsystem: locate service names and payloads.
5. When samples arrive: byte-level correlation between built-in DB, on-disk
   file, and the builder/reader code.
