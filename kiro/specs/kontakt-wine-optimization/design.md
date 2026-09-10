# Design Document

## Overview

This design turns the requirements into a concrete, ordered technical plan across four
work areas, prioritized per the user's mode strategy (standalone first):

1. **Startup diagnosis & database/resource fix** — kill the bulk of the ~10,260 failed
   file lookups (dominated by NI Resources SQLite sidecar probing and missing per-library
   resources).
2. **Wine drive-letter normalization & controller exclusion** — one canonical convention
   (`D:` → `/mnt/workspace`), stable mounts, controllers not scanned as content.
3. **Automated library scanner** — a Linux-side script that discovers and classifies all
   Kontakt content across the three roots and emits auditable lists.
4. **Clean re-registration + latency persistence + `.so` repair** — use scanner output to
   rebuild registrations, persist the 128 PipeWire quantum, then repair the REAPER path.

All mutating steps are preceded by backups and are reversible (Requirement 1.5).

## Guiding Principle: Diagnose Before Mutating

The 10,260 figure is a measurement, not yet a root cause per category. Before changing
Kontakt's databases we will produce a **categorized breakdown** of the failed lookups so
each fix is targeted and its effect is measurable (before/after lookup counts).

Diagnostic pipeline (reusable helper script `analyze_kontakt_log.sh`):

- Input: a `WINEDEBUG=+file` log from one standalone launch.
- Output: counts grouped into buckets:
  - `db_sidecar` — `*.db-wal`, `*.db-journal`, `*.db-shm`
  - `resource_image` — `...\Resources\image\...`
  - `resource_dist_db` — `...\dist_database\...`
  - `controller_probe` — paths under the `E:` / `J:` roots
  - `library_content` — `.nkx`, `.nkr`, `.nkc`, `.nicnt`, `.nki`, `.nkm`
  - `other`
- This gives a per-bucket baseline and the same buckets are re-measured after each fix.

## Area 1: Startup Database & Resource Fix

### Problem analysis

The top offenders are SQLite sidecar probes:

```
1499  D:\...\NI Resources\database\pal\categories.db-wal
1499  D:\...\NI Resources\database\pal\categories.db-journal
 148  ...shortname.db-wal / -journal
 148  ...color.db-wal / -journal
  63  ...Service Center\pal.db-wal / -journal
```

SQLite probes for `-wal`/`-journal`/`-shm` sidecars on connection. If the parent `.db`
file is **missing, zero-byte, or in rollback-journal mode with an absent journal**, and if
the containing directory is repeatedly reopened, these probes repeat. Two candidate root
causes:

- **A. The NI Resources database files are missing/empty**, so Kontakt retries building or
  opening them many times per startup.
- **B. The database directory path itself doesn't resolve** (path drift), so every open
  attempt fails and is retried.

### Approach

1. **Inspect actual state** of the NI Resources DB directory on disk:
   - Resolve `D:\...\NI Resources\database\pal\` to its Linux path
     (`/mnt/workspace/VST Install/Kontakt Portable/UserData/NI Resources/database/pal/`).
   - Check whether `categories.db` exists, its size, and integrity
     (`sqlite3 categories.db "PRAGMA integrity_check;"` if present).
   - Same for `shortname.db`, `color.db`, and `Service Center/pal.db`.
2. **Decision matrix:**
   - If the `.db` files are **missing/zero-byte** → let Kontakt regenerate them by
     ensuring the directory is writable and launching once; OR restore from the working
     REAPER-era setup if a good copy exists.
   - If **present but corrupt** → back up, then `.recover` or delete so Kontakt rebuilds.
   - If the **directory doesn't resolve** (path drift) → fixed by Area 2 (canonical `D:`).
3. **Set SQLite journal mode expectation:** these are NI-managed DBs; we do not alter
   their schema. The fix is ensuring the file exists and the path resolves so the sidecar
   probing resolves quickly (found or definitively absent once, not retried thousands of
   times).
4. **Missing per-library resources** (`image\<lib>`, `dist_database\<lib>`): these are
   cosmetic (tile artwork / browser metadata) for libraries whose resource folders never
   got installed. Options, in order of preference:
   - Leave as-is if count is low after the DB fix (they may be a symptom, not a cause).
   - If still high, remove the corresponding stale library registrations (Area 4) so
     Kontakt stops looking for their resources.

### Backups (mandatory before any DB mutation)

```
cp -a "<UserData>/NI Resources" "<UserData>/NI Resources.bak.$(date +%s)"
cp -a "<UserData>/Kontakt 8/komplete.db3" "<UserData>/Kontakt 8/komplete.db3.bak"
cp -a "<UserData>/Kontakt 8/user_config.db3" "<UserData>/Kontakt 8/user_config.db3.bak"
cp -a ~/.wine/dosdevices ~/.wine/dosdevices.bak
```

## Area 2: Wine Drive-Letter Normalization & Controller Exclusion

### Target state for `~/.wine/dosdevices`

| Letter | Target             | Rationale                                  |
|--------|--------------------|--------------------------------------------|
| `C:`   | `../drive_c`       | Wine system (unchanged)                    |
| `D:`   | `/mnt/workspace`   | Canonical content letter (DB is keyed here)|
| `E:`   | `/mnt/storage`     | Second content drive (user preference)     |
| `F:`   | `/mnt/wd_black`    | Third content drive (user preference)      |
| `L:`   | Launchpad mount    | Controller, reassigned off `E:`            |
| `M:`   | LCXL mount         | Controller, reassigned off `J:`            |
| `W:`   | `/mnt/win_system`  | Windows system (unchanged)                 |
| `Z:`   | `/`                | Root access (unchanged; needed for Z:\mnt) |

Changes:
- **Reassign `E:`** from the Launchpad controller to `/mnt/storage` (user preference).
- **Reassign `F:`** to `/mnt/wd_black`. The old `F:`->`/mnt/workspace` alias is removed;
  before repurposing, confirm no `F:`-only baked content paths remain via a scan of the
  log/DB. If any exist, reconcile them to the canonical `D:` (Area 4) rather than keeping
  the stale `F:`->workspace mapping.
- **Remove `S:`** alias to `/mnt/workspace` (redundant).
- **Reassign controllers to out-of-the-way letters** so they stay mountable but never
  interfere with Kontakt content: Launchpad -> `L:`, LCXL -> `M:` (moved off `E:`/`J:`).
  The physical device double-colon entries (`e::`, `f::`, `g::`, `h::`, `i::`, `j::`) are
  raw device nodes and can remain; they are not DOS drive letters and are not scanned as
  content.

### Controller handling

The Launchpad and LCXL controllers are reassigned to high, non-content letters
(Launchpad -> `L:`, LCXL -> `M:`) so their auto-mounts stay usable for occasional plain
data but are clearly separated from the content drives. They will not be used as sound
storage. Final stable content mapping: `D:`=workspace, `E:`=storage, `F:`=wd_black;
controllers: `L:`=Launchpad, `M:`=LCXL.

### Mount stability (fstab)

Ensure `/mnt/workspace`, `/mnt/storage`, `/mnt/wd_black` mount at fixed paths with `nofail`
so drive-letter symlinks never dangle. Use UUIDs from `lsblk -o NAME,UUID,FSTYPE`. Example
line (ntfs3 kernel driver):

```
UUID=<uuid>  /mnt/workspace  ntfs3  rw,uid=1000,gid=1000,windows_names,nofail,x-systemd.device-timeout=5  0 0
```

Note: partitions must be cleanly unmounted from Windows (disable fast-startup/hibernation)
or ntfs3 mounts read-only.

## Area 3: Automated Library Scanner

### Language & placement

Python 3 (present on CachyOS), single script `kontakt_scan.py` in the workspace root, with
no third-party dependencies (uses `os.scandir` for speed over 1TB).

### Inputs

- Root paths (default the three content mounts; extra roots via CLI args).
- Optional exclude-name patterns (default includes iZotope, Nectar, Ozone, RX).

### Classification rules (evaluated per directory, bottom-up dedup)

| Signal in folder                                              | Category         |
|--------------------------------------------------------------|------------------|
| `*.nicnt` present                                            | Player library   |
| `.nki`/`.nkm`/`.nkb` present, no `.nicnt`, has samples nearby| Custom library   |
| `.nksn` present                                              | User presets     |
| only `.dll`/`.vst3`/effect markers, no `.nk*`                | Excluded         |
| name matches exclude patterns (iZotope/Nectar/Ozone/RX)      | Excluded         |

Encoded content markers `.nkx`/`.nkr`/`.nkc` and `Samples/` reinforce library detection.

### De-duplication

Walk depth-first; when a directory is classified as a library root, do not re-classify its
descendants. Emit the top-most root only. Prevents nested `.nki` folders inside a Player
library from being double-listed.

### Outputs (in a timestamped results dir, no Kontakt DB mutation)

- `player_libraries.tsv` — path, detected name, `.nicnt` file (for Library Manager)
- `custom_libraries.tsv` — path, instrument count (for Import Content → Custom Libraries)
- `user_presets.tsv` — path (for Import Content → User Presets)
- `excluded.tsv` — path, reason (for user audit)
- `summary.txt` — counts, total size per category, roots scanned

Each path is emitted in **both** Linux form and the mapped Wine drive-letter form (using
the Area 2 canonical map) so the user can copy the correct `D:\...`/`G:\...`/`K:\...` path
straight into Kontakt.

### Performance

- `os.scandir` + early pruning (stop descending once a library root is found).
- Skip hidden/system dirs and known non-content trees.
- Report progress per root; typical full scan of 1TB completes in minutes on ntfs3.

## Area 4: Re-registration, Latency Persistence, `.so` Repair

### Re-registration workflow (manual in Kontakt, guided by scanner output)

1. Back up `komplete.db3` / `user_config.db3` (already covered).
2. In Import Content: remove all entries (especially iZotope and unresolved paths).
3. Add Custom Libraries from `custom_libraries.tsv` (Wine-path column).
4. Register Player libraries from `player_libraries.tsv` via Library Manager.
5. Add User Presets from `user_presets.tsv`.
6. Relaunch instrumented; run `analyze_kontakt_log.sh`; confirm buckets dropped.

### Latency persistence (128 quantum)

`pw-metadata` is runtime-only. Persist via a user PipeWire config drop-in:

`~/.config/pipewire/pipewire.conf.d/10-lowlatency.conf`:
```
context.properties = {
    default.clock.rate          = 44100
    default.clock.allowed-rates = [ 44100 ]
    default.clock.quantum       = 128
    default.clock.min-quantum   = 128
    default.clock.max-quantum   = 128
}
```
Restart PipeWire (`systemctl --user restart pipewire pipewire-pulse wireplumber`) and
verify with `pw-metadata -n settings`. Keep a note to raise the quantum for very large
projects if xruns appear.

### REAPER `.so` repair (Requirement 5, after standalone is solid)

1. `yabridgectl status` — see what yabridge currently tracks and which prefix.
2. Confirm the Kontakt VST3/VST2 Windows plugin path is still present under the same prefix
   (`~/.wine`).
3. `yabridgectl add "<path to NI Kontakt VST dir>"` if missing, then `yabridgectl sync` to
   regenerate the `.so` bridges (the step that was skipped when files were deleted).
4. Rescan plugins in REAPER; load Kontakt; verify it finds content using the same canonical
   drive letters (shared prefix means the Area 2 mapping applies to both modes).
5. Crash-testing period per the mode strategy before switching primary.

## Testing Strategy

- **Metric-driven:** every startup fix is validated by re-running the instrumented launch
  and comparing per-bucket failed-lookup counts (baseline captured first).
- **Scanner validation:** run against a known subfolder with a mix of a Player library, a
  loose-`.nki` folder, a `.nksn`, and an iZotope folder; assert correct categorization and
  dedup before running on the full 1TB.
- **Reversibility check:** confirm backups exist and document restore steps before each
  mutating step.
- **Latency check:** after persistence, `pw-metadata -n settings` shows quantum 128; listen
  for xruns during real playing.
- **No automated unit-test framework applies** to the shell/config changes; the scanner
  gets a small Python test using a temporary fixture tree.

## Risks & Mitigations

- **ntfs3 read-only if Windows hibernated:** document disabling fast-startup; mount check.
- **Deleting a DB that wasn't the cause:** always back up; change one thing at a time and
  re-measure.
- **Removing `F:` breaks baked paths:** scan for `F:`-only references first; keep `F:` if
  any remain.
- **Scanner misclassifying unusual/old libraries:** `excluded.tsv` with reasons lets the
  user rescue anything wrongly excluded before registration.
