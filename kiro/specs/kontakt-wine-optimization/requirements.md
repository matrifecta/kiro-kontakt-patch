# Requirements Document

## Introduction

This spec covers optimizing and stabilizing a portable Native Instruments Kontakt 8
setup running under Wine on CachyOS (PipeWire/JACK audio). The user runs Kontakt in
two possible modes: as a standalone Windows application under Wine, and as a bridged
VST inside REAPER via yabridge (the `.so` runtime). Windows NTFS partitions are
mounted under Linux and exposed to Wine through drive-letter symlinks in the Wine
prefix's `dosdevices`.

Three connected problems are in scope:

1. **Slow, unreliable standalone load.** A single standalone launch produces ~10,260
   failed file lookups. Diagnostics show the dominant causes are repeated SQLite
   sidecar probes (`categories.db-wal`/`-journal`, `shortname.db`, `color.db`) in the
   NI Resources database, probing of controller drives (`E:`/`J:`) that hold no
   content, missing per-library image/`dist_database` resources, and path-convention
   drift across `D:`, `F:`, and `Z:\mnt\...`.

2. **No automated way to find and register libraries.** Over 1TB of Kontakt content is
   spread across multiple NTFS partitions (`/mnt/workspace`, `/mnt/storage`,
   `/mnt/wd_black`, possibly others) with old instruments from various sources. Manual
   registration in Import Content / Library Manager is impractical. Non-Kontakt content
   (e.g. iZotope Nectar/Ozone/RX) has been registered by mistake.

3. **DAW crash isolation / mode decision.** Kontakt previously crashed inside REAPER via
   the `.so` bridge, freezing REAPER and losing unsaved work. The user prefers ease of
   use, minimal open windows/environments, and above all not losing work. A decision is
   needed on whether to rely on standalone, the REAPER `.so` path, or both — informed by
   reliability, latency/playability, and not only load speed. The user targets a sub-10ms
   round-trip latency window, at 44.1kHz (constrained by the weakest device in the chain,
   a Boss RC600), across ~16 connected devices.

## Confirmed Environment (ground truth)

- OS: CachyOS (Arch-based), audio via PipeWire/JACK.
- Wine prefix: default `~/.wine` (WINEPREFIX unset).
- Drive letters (`~/.wine/dosdevices`): `C:`→`../drive_c`, `D:`→`/mnt/workspace`,
  `F:`→`/mnt/workspace` (added to fix base-path errors), `S:`→`/mnt/workspace`
  (redundant; removed), `W:`→`/mnt/win_system`, `Z:`→`/`, `E:`→Launchpad controller,
  `J:`→LCXL controller.
- Mounts (kernel `ntfs3` driver, shown as FSTYPE `ntfs`):
  - `/mnt/workspace` → `/dev/sdb2`
  - `/mnt/storage` → `/dev/sdc1`
  - `/mnt/win_system` → `/dev/sda4`
  - `/mnt/wd_black` → `/dev/nvme1n1p2`
- Kontakt user data: `/mnt/workspace/VST Install/Kontakt Portable/UserData/Kontakt 8`
  (contains `komplete.db3`, `user_config.db3`, `presets`, `QuickLoad`, etc.).
- Standalone launch command:
  `WINEDLLOVERRIDES="*api-ms-win-core*=b;*msvcp140*=b;*vcruntime140*=b" wine "Kontakt 8.exe"`
- Measured baseline: ~10,260 failed file lookups per standalone startup; load > 3 min;
  second launch equally slow (not a cold-cache effect).

## Requirements

### Requirement 1: Reduce standalone startup failed-lookup count and load time

**User Story:** As a producer, I want Kontakt standalone to launch quickly and reliably,
so that I can start working without waiting minutes each time.

#### Acceptance Criteria

1. WHEN a standalone launch is instrumented with `WINEDEBUG=+file` THEN the count of
   failed file lookups SHALL be reduced substantially from the ~10,260 baseline.
2. WHEN Kontakt is launched normally (without debug tracing) THEN the wall-clock time to
   a usable UI SHALL be measurably lower than the >3 minute baseline.
3. WHEN the NI Resources database sidecar probing (`-wal`/`-journal`, `shortname.db`,
   `color.db`, `categories.db`) is investigated THEN the spec SHALL identify whether the
   database can be repaired, regenerated, or relocated to reduce repeated failed probes.
4. WHEN load time is measured THEN before/after numbers SHALL be recorded so the effect
   of each change is auditable.
5. WHEN changes are applied THEN they SHALL be reversible or backed up before mutation
   (e.g. Kontakt databases and Wine config copied before edits).

### Requirement 2: Stabilize and normalize Wine drive-letter mapping

**User Story:** As a producer, I want consistent, stable drive letters, so that stored
library and preset paths always resolve and don't trigger repeated failed lookups.

#### Acceptance Criteria

1. WHEN the Wine `dosdevices` mapping is reviewed THEN redundant letters pointing to the
   same partition SHALL be eliminated or justified.
2. WHEN controller devices (Launchpad on `E:`, LCXL on `J:`) are present THEN Kontakt
   SHALL NOT probe them as content locations, OR they SHALL be excluded from Kontakt's
   registered/search paths.
3. WHEN the partitions are mounted THEN mount points SHALL be stable across reboots
   (fixed mount paths, e.g. via fstab with `nofail`) so drive-letter symlinks never
   dangle.
4. WHEN stored paths use inconsistent conventions (`D:`, `F:`, `Z:\mnt\...`) THEN the
   spec SHALL define a single canonical convention and a plan to reconcile existing
   registrations to it.

### Requirement 3: Automated Kontakt library discovery across drives

**User Story:** As a producer with 1TB+ of scattered content, I want an automated scan
that finds all real Kontakt content and categorizes it, so that I don't have to hunt and
add folders by hand.

#### Acceptance Criteria

1. WHEN the scanner runs against configured root paths (`/mnt/workspace`, `/mnt/storage`,
   `/mnt/wd_black`, plus any additional user-specified roots) THEN it SHALL traverse them
   on the Linux side (native, not through Wine) for speed.
2. WHEN a folder contains a `*.nicnt` marker THEN it SHALL be classified as a Player /
   encoded library (for Library Manager registration).
3. WHEN a folder contains loose `.nki`/`.nkm`/`.nkb` instruments with associated samples
   but no `.nicnt` THEN it SHALL be classified as Custom Library content (for Import
   Content → Custom Libraries).
4. WHEN a folder contains `.nksn` snapshots THEN it SHALL be classified as User Presets.
5. WHEN a folder contains only non-Kontakt content (e.g. iZotope Nectar/Ozone/RX, plain
   `.dll`/`.vst3` with no `.nk*` siblings) THEN it SHALL be classified as Excluded.
6. WHEN nested matches occur THEN the scanner SHALL emit the top-most library root and
   de-duplicate nested hits.
7. WHEN the scan completes THEN it SHALL produce categorized, auditable output lists
   (Player libraries, Custom Libraries, User Presets, Excluded) that the user can review
   before anything is registered in Kontakt.
8. WHEN the scan completes THEN it SHALL NOT modify Kontakt's databases directly; results
   are for user-driven registration.

### Requirement 4: Clean re-registration of content in Kontakt

**User Story:** As a producer, I want the stale and junk registrations removed and only
valid content re-added, so that startup stops probing paths that don't exist.

#### Acceptance Criteria

1. WHEN non-Kontakt entries (iZotope, etc.) are present in Import Content THEN they SHALL
   be removed.
2. WHEN registrations reference drive letters/paths that no longer resolve THEN they SHALL
   be corrected to the canonical convention or removed.
3. WHEN re-registration is performed THEN the scanner's Custom Libraries and Player
   library lists SHALL be used as the source of truth for what to add.
4. WHEN re-registration is complete THEN a follow-up instrumented launch SHALL confirm the
   failed-lookup count dropped.

### Requirement 5: Mode decision and crash isolation (standalone vs REAPER .so)

**User Story:** As a producer who has lost work to crashes, I want a clear recommendation
on whether to use standalone, the REAPER `.so` bridge, or both, so that a Kontakt crash
never destroys my session.

#### Acceptance Criteria

1. WHEN the two modes are compared THEN the comparison SHALL cover crash isolation,
   reliability, ease of use (window/environment count), and load performance.
2. WHEN the REAPER `.so` path is evaluated THEN the spec SHALL identify why it broke after
   the `.so` and other plugin entries were removed from the yabridge map without
   re-syncing (`yabridgectl sync`), and whether it can be repaired.
3. WHEN crash isolation is considered THEN options that prevent a Kontakt crash from
   freezing/crashing the DAW (e.g. out-of-process/bridged hosting) SHALL be documented.
4. WHEN a recommendation is made THEN it SHALL account for the user's stated preference for
   ease of use and minimal open environments, and for not losing work.
5. WHEN latency/playability is compared THEN the analysis SHALL note that audio round-trip
   latency is governed by the PipeWire/JACK backend (buffer size x sample rate, periods,
   interface driver), NOT by the hosting mode, so both modes can target the same sub-10ms
   round-trip window at 44.1kHz; AND that the in-process `.so`/REAPER path typically yields
   tighter, more consistent MIDI->audio timing while the Wine standalone path may show
   marginally higher jitter but provides crash isolation.
6. WHEN buffer/sample-rate settings are reviewed THEN the spec SHALL account for the
   confirmed configuration: 236-sample buffer at 44.1kHz via Wine's WASAPI backend, where
   the value is negotiated by PipeWire (Wine WASAPI requests a period; PipeWire returns a
   quantum, hence the non-power-of-two 236 ~= 5.35ms/direction). Forcing the PipeWire
   quantum to 128 yields ~2.9ms/direction (~5.8ms round-trip) before interface overhead.
7. WHEN the sub-10ms target is addressed THEN the spec SHALL document controlling the
   PipeWire quantum (`pw-metadata -n settings 0 clock.force-quantum 128`) and making it
   persistent, and SHALL note standalone adds a Wine WASAPI->PipeWire translation layer
   whereas the `.so` path allows more direct buffer control (a factor in the decision).
8. This requirement is LOWER priority than Requirements 1-4 and SHALL be addressed after
   standalone load/reliability is resolved.

## Mode Strategy (user decision)

The user has chosen a phased strategy that sets priority order:

1. **Now:** Fix and use the Wine **standalone** as the working mode (Requirements 1-4).
2. **Next:** Repair the REAPER `.so` (yabridge) path (Requirement 5).
3. **Test:** Run the `.so` path for several days, including large composer projects that
   stress system resources, watching for crashes/DAW freezes.
4. **If stable:** Switch to `.so` as primary, keep standalone as the fallback.
5. **If it misbehaves:** Fall back to standalone.

Standalone is therefore both the immediate priority and the permanent crash-isolated
safety net regardless of the final choice.

## Confirmed Audio Configuration (ground truth)

- Sample rate: 44.1kHz (`clock.rate 44100`, `clock.allowed-rates [44100]`).
- PipeWire quantum forced to **128** samples (`clock.quantum/min-quantum/max-quantum 128`,
  `clock.force-quantum 128`) -> ~2.9ms/direction, ~5.8ms round-trip before interface/RC600
  overhead, inside the sub-10ms target. Previously negotiated to 236 via Wine WASAPI.
- NOTE: `pw-metadata` quantum settings are runtime-only and reset on reboot/PipeWire
  restart; a persistence mechanism is required (design phase). Watch for xruns at 128.

## Resolved Decisions

1. Content roots for Kontakt scanning are `/mnt/workspace`, `/mnt/storage`, and
   `/mnt/wd_black`. No other locations hold Kontakt content (REAPER-only locations are out
   of scope). `/mnt/wd_black` IS used for Kontakt content and is included.
2. Canonical drive-letter convention: standardize on `D:` -> `/mnt/workspace`, since the
   current database and the vast majority of failing paths are keyed to `D:`; redundant
   `F:`/`S:` aliases are consolidated (design confirms no baked `F:`-only paths remain).

## Out of Scope

- Reinstalling Kontakt or migrating to a native Linux host other than the existing
  Wine/yabridge approaches.
- The separate Windows 10 VM used for other MIDI tooling (mentioned only as context).
- Reconfiguring PipeWire/JACK audio routing beyond the quantum/latency tuning above.
