# Kontakt Workspace Drive Dirty Fix — Bugfix Design

## Overview

Kontakt 8 Portable runs under Wine on CachyOS — standalone (WineASIO via `pw-jack`) and as a yabridge `.so` in Reaper — with the executable, DB, user content, and every sample library on the NTFS "Workspace" volume (`/dev/sdb2`, UUID `B82064122063D642`, 2.7T). Three distinct bugs are tracked here and must not be conflated:

- **Bug A** — the volume carries a dirty NTFS bit; `ntfs3` hard-refuses to mount it, and `nofail` masks the failure so `/mnt/workspace` is silently absent and Kontakt cannot launch. Root cause is CONFIRMED: an unclean Linux-side dismount at shutdown/hibernate leaves the dirty bit set. `chkdsk` from Windows is a proven clear method; `nofail` then hides the next failure.
- **Bug B** — a subset of library-browser artwork tiles render blank on a mounted, running Kontakt. Cause is OPEN among H-A (mutex/DB reference breakage), H-B (`chkdsk` metadata reassignment), H-C (`ntfs3` metadata exposure). Known cache clear/rescan remedies have already failed.
- **Bug C** — EWQL RA presets fail "not installed" due to a baked SNPID mismatch (`.nicnt` A02 vs instrument A05). Strong prior: content-side casualty, unfixable in-setup. Tracked for an explicit investigation and documented decision.

The fix strategy is **staged and gated**. Bug A is fixed first and must be **proven stable across a full reboot cycle** before any Bug B work touches the DB/cache (to avoid re-dirtying the volume or corrupting the DB). Bug B's cause is discriminated before repair. Bug C is investigated last. A shared path-migration converges Kontakt onto the drive-letter-independent `Z:` convention and retires `F:` safely. All work is non-destructive by default; force-mount is backup-only; every root command is written for the USER to run (interactive sudo is unavailable to the agent).

## Glossary

- **Bug_Condition (C)**: The condition that triggers a given bug (dirty bit set / blank tile set / SNPID mismatch), formalized per bug below.
- **Property (P)**: The desired correct behavior once the fix is applied.
- **Preservation (¬C)**: Behavior on non-buggy inputs (other drives, mouse-equivalent flows, clean-volume boots, both Kontakt workflows) that MUST remain unchanged.
- **F / F'**: Original (unfixed) vs fixed system behavior.
- **dirty bit**: NTFS `$Volume` dirty flag. `ntfs3` refuses `rw` mount when set unless `force` is given.
- **ntfs3**: In-kernel NTFS driver used for Workspace (`sdb2`), Storage (`sdc1`), WD Black (`nvme0n1p2`).
- **ntfs-3g / fuseblk**: Userspace NTFS driver used by `win_system` (`sda4`); also usable read-only to probe H-C.
- **write-quiesce gate**: Pre-`umount` check that confirms `sync` completed, no process holds the mount (`fuser -m`/`lsof`), and no dirty/writeback pages remain for the backing device, with a bounded retry.
- **LibrariesCache**: Per-library browser artwork cache at `/mnt/workspace/VST Install/Kontakt Portable/UserData/Kontakt 8/LibrariesCache/` (~62 `.cache` files vs ~120 Player libraries; the missing ~58 = blank tiles). Filenames embed original install-date epochs.
- **SNPID**: Serial/product identifier binary-encoded in a library's `.nicnt`; must match the instrument's declared SNPID for Player registration to satisfy preset loads.
- **Z: convention**: Wine dosdevices `Z:->/`, so `Z:\mnt\workspace\...` maps to Linux `/mnt/workspace/...` independent of any other drive letter. All 120 Player libraries already use `ContentDir = Z:\mnt\workspace\VST Install\Kontakt Vst-i\<Library>`.
- **F: mapping**: Wine dosdevices `F:->/mnt/workspace`. Non-persistent across reboots; some baked preset/instrument sample paths still reference `F:\...`, so `F:` must remain until those are repointed.

## Bug Details

### Bug A — Dirty bit / mount refusal

The bug manifests when the Workspace volume was dismounted uncleanly on the Linux side (shutdown/hibernate without a guaranteed flush + dirty-bit clear). On next boot `ntfs3` sees the dirty bit and refuses the mount, emitting `volume is dirty and "force" flag is not set!`; `nofail` lets boot continue silently, so `/mnt/workspace` is absent and Kontakt cannot launch.

**Formal Specification:**
```
FUNCTION isBugCondition_A(state)
  INPUT: state of type SystemState (backing device sdb2, fstab entry, boot outcome)
  OUTPUT: boolean

  RETURN state.volume.dirtyBit == SET
         AND state.driver == ntfs3
         AND mount("/mnt/workspace") == REFUSED   // "volume is dirty" in dmesg
         AND state.fstab.workspace HAS nofail      // failure masked, no user alert
END FUNCTION
```

#### Examples (Bug A)
- Expected: after a clean shutdown, next boot mounts `/mnt/workspace`. Actual: after an unclean/rushed dismount, `sdb2` stays dirty and unmounted; `dmesg` shows `ntfs3(sdb2): volume is dirty`.
- Expected: a failed Workspace mount is visible to the user. Actual: `nofail` swallows it; the user only notices when Kontakt won't launch.
- Confirmed clear path: a clean Windows full shutdown + `chkdsk D:` returns "found no problems" and CachyOS then mounts clean.
- Edge / limitation: `ntfsfix` processed the MFT but did NOT clear the dirty flag that `ntfs3` checks — so it is not a reliable primary clear method here.

### Bug B — Blank tiles on a mounted drive

The bug manifests only when the drive is mounted and Kontakt is running (it cannot launch otherwise). A subset of Player-library tiles render with no artwork; that subset corresponds to Player libraries with no matching `.cache` entry in `LibrariesCache/` (~62 present vs ~120 registered). Cause is OPEN.

**Formal Specification:**
```
FUNCTION isBugCondition_B(lib)
  INPUT: lib of type PlayerLibrary (mounted drive, Kontakt running)
  OUTPUT: boolean

  RETURN lib.isRegisteredPlayerLibrary == true
         AND lib.tile.artworkRendered == false
         AND (NOT exists(LibrariesCache/<lib.cacheId>.cache)
              OR cacheEntryFailsValidation(lib))   // identity/mtime check fails
END FUNCTION
```

#### Examples (Bug B)
- Expected: a Player library with valid artwork shows its tile image. Actual: ~58 libraries show blank tiles; their `.cache` file is missing.
- Contrast: a library WITH a present, valid `.cache` renders its tile — a working control to compare against.
- Known-failed remedy: clearing `LibrariesCache` then relaunching left the count at 0 (no regeneration); Import Content rescan stayed at 62; KTP re-add did not regenerate.
- Data point against "art is missing": the Amati `.nicnt` contains 8 image markers — artwork IS present in the library package.

### Bug C — EWQL RA unusable

The bug manifests when any EWQL RA preset (or direct `.nki`) loads: it fails "not installed" because the `.nicnt`-declared SNPID does not match the instruments' demanded SNPID.

**Formal Specification:**
```
FUNCTION isBugCondition_C(load)
  INPUT: load of type PresetLoad (EWQL RA)
  OUTPUT: boolean

  RETURN load.library == "EWQL RA"
         AND nicnt.SNPID != instrument.demandedSNPID   // A02 vs A05 observed
         AND load.result == "not installed"
END FUNCTION
```

#### Examples (Bug C)
- `LibraryHints.xml` shows two entries: `EWQL RA` / A02 and `EWQL RA ` (trailing space) / A05.
- Content is present: Ra Samples 1–3 (~2.1GB each), Ra Resources.nkr (466MB), EWQL RA.nicnt (~515k).
- Direct `.nki` load via Files browser still failed under a clean single-entry re-registration.
- Edge: the "check if the drive is mounted" wording must NOT be read as Bug A — on a stable mount it is either a leftover-`F:` path failure or the SNPID problem.

## Expected Behavior

### Preservation Requirements

**Unchanged Behaviors:**
- Storage (`sdc1`) and WD Black (`nvme0n1p2`) continue to mount via `ntfs3` (3.1).
- `win_system` (`sda4`) continues to mount via the old `ntfs`/fuseblk/`ntfs-3g` driver (3.2).
- Workspace remains usable from Windows native (`D:`), Windows in VirtualBox, and Linux Wine after any path/driver change (3.3).
- Both Kontakt workflows — standalone WineASIO/pw-jack and yabridge `.so` in Reaper — continue to launch and function once the drive is stable; they share the same `~/.wine` prefix and `komplete.db3` (3.4).
- A clean, present Workspace volume mounts at `/mnt/workspace` with no force-mount or manual repair (3.5).
- The `nocase` fstab option is retained (it fixed ~10,260 lowercase-probe lookup failures) and all existing fstab options stay intact.

**Scope:** All inputs that do NOT satisfy a bug condition must be unaffected:
- Other NTFS drives and their drivers.
- Clean-volume boots (no dirty bit).
- Libraries whose `.cache` entries are present and valid (their tiles must keep rendering).
- All non-EWQL-RA libraries and presets.
- Cross-fix safety: Bug A driver/unmount work must not corrupt `komplete.db3`; Bug B/C cache/DB work must not re-dirty the volume (3.6).

## Hypothesized Root Cause

### Bug A (CONFIRMED)
Unclean Linux-side dismount. `ntfs3` is not guaranteed to flush and clear the dirty bit before power-down at shutdown/hibernate, and there is no clean-unmount step ordered before `umount.target`/`shutdown.target`/`systemd-hibernate.service`. `nofail` then masks the resulting boot mount failure. Windows Fast Startup is already verified OFF (satisfied precondition, not a cause).

### Bug B (OPEN — three hypotheses)
1. **H-A (Mutex / DB rebuild)**: the mutex clear / partial DB rebuild detached cache/artwork references. Weakened by prior notes ("tiles survived the mutex clear") but not eliminated.
2. **H-B (chkdsk metadata reassignment)**: `chkdsk` rewrote MFT/USN/timestamps so Kontakt's `.cache` identity/mtime validation treats valid caches as stale. Supported by prior notes, contested by recent recollection.
3. **H-C (ntfs3 metadata exposure)**: `ntfs3` exposes timestamps/metadata differently than `ntfs-3g`/Windows, failing the cache-validity check even on a clean mount.

### Bug C (STRONG PRIOR)
Baked-in SNPID mismatch in the repack (`.nicnt` A02 vs instrument A05). Likely a content-side casualty requiring a matching-SNPID package re-acquisition; not fixable by config, re-registration, drive letters, or Wine setup. Tracked for explicit confirmation and a documented decision.

## Correctness Properties

Property 1: Bug Condition A — Reliable clean mount with recurrence prevention

_For any_ system state where the Bug A condition holds (`isBugCondition_A` returns true), the fixed system SHALL clear the dirty bit via a proven-working method (Windows `chkdsk` primary; `ntfsfix`/`fsck.ntfs` documented alternative with its limitation), mount Workspace reliably at `/mnt/workspace` via `ntfs3`, and prevent recurrence by cleanly unmounting all `ntfs3` drives before shutdown/hibernate behind a write-quiesce gate, surfacing any residual mount failure to the user rather than masking it.

**Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5, 2.6**

Property 2: Bug Condition B — Tiles render after cause-driven repair

_For any_ Player library where the Bug B condition holds (`isBugCondition_B` returns true) on a drive proven stable across a reboot, the fixed system SHALL first discriminate the cause (H-A/H-B/H-C) with a step beyond the known-failed cache clear, then apply a repair that regenerates or revalidates the `.cache` entry so the tile renders in both standalone and Reaper/yabridge usage; if no in-setup regeneration path exists, the limitation SHALL be documented rather than looping on known-failed remedies.

**Validates: Requirements 2.7, 2.8, 2.9**

Property 3: Bug Condition C — EWQL RA investigated to a documented decision

_For any_ EWQL RA load where the Bug C condition holds (`isBugCondition_C` returns true), the fixed system SHALL, after Bugs A and B are addressed, confirm the SNPID mismatch and test alternative access paths (direct `.nki`, Custom-library registration), then reach one documented resolution: a working access path, or a recorded determination that it needs a matching-SNPID re-acquisition, in which case EWQL RA is removed or clearly flagged so it stops emitting misleading mount/path errors.

**Validates: Requirements 2.10, 2.11**

Property 4: Shared path migration — converge on Z:, retire F: safely

_For any_ Kontakt path resolution (Player library, baked preset path, non-Player user-content base), the fixed system SHALL migrate off `F:` toward the `Z:\mnt\workspace\...` convention, repointing baked-`F:` preset paths and the non-Player base path, keeping `F:` deterministically mapped until those are repointed, so `F:` can be retired without breaking Windows-native (`D:`), VirtualBox, or Wine consumers.

**Validates: Requirements 2.12, 2.13**

Property 5: Preservation — other drives, clean boots, both workflows, no cross-regression

_For any_ input where NO bug condition holds (other NTFS drives, clean-volume boots, valid-cache libraries, non-EWQL-RA content), the fixed system SHALL behave exactly as the original: Storage/WD Black keep mounting via `ntfs3`, `win_system` via `ntfs-3g`, both Kontakt workflows keep working, force-mount stays backup-only, and no fix worsens another bug (no DB corruption, no re-dirtying).

**Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7**

## Fix Implementation

All root commands below are labeled **"RUN THIS YOURSELF — sudo required"**. The agent cannot run interactive sudo. Prefer the exact copy-paste blocks. `fstab` backup already exists at `/etc/fstab.bak_20260901`; take a fresh one before edits.

### Stage 1 — Bug A: clear dirty bit + reliable mount + recurrence prevention (Req 2.1–2.6)

#### 1a. Check dirty state (diagnostic, non-destructive)

**RUN THIS YOURSELF — sudo required**
```bash
# Attempt a mount and read the driver's verdict:
sudo mount -t ntfs3 /dev/sdb2 /mnt/workspace 2>&1; dmesg | tail -20
# Or inspect volume flags without mounting:
sudo ntfsinfo -m /dev/sdb2 2>&1 | grep -i -E 'dirty|volume flags'
```
If `dmesg` shows `volume is dirty and "force" flag is not set!`, the dirty bit is set.

#### 1b. Clear the dirty bit — PRIMARY: chkdsk from Windows

This is the confirmed-working path. Do a **clean Windows full shutdown** (Fast Startup already OFF), then from Windows:
```
chkdsk D: /f
```
Expected: "found no problems" (or repairs then clears). Boot back into CachyOS; the drive mounts clean. Windows does not re-dirty the volume.

**Linux-side ALTERNATIVE (documented limitation):** `ntfsfix`/`fsck.ntfs` from Linux.

**RUN THIS YOURSELF — sudo required**
```bash
sudo umount /mnt/workspace 2>/dev/null
sudo ntfsfix /dev/sdb2          # processes MFT; see limitation below
# If ntfs3 STILL refuses after ntfsfix (prior session outcome), use chkdsk from Windows.
```
> Limitation: in the prior session `ntfsfix` processed the MFT OK but did NOT clear the dirty flag that `ntfs3` inspects, so the volume still refused to mount. Treat `ntfsfix` as best-effort; `chkdsk` from Windows is required when `ntfsfix` leaves the flag set. Force-mount (`-o force`/`clear_dirty`) is backup-only and must not be the primary fix.

#### 1c. Keep fstab mount options consistent (Req 2.2)
Verify the Workspace entry uses the proven option set and driver; do NOT drop `nocase`.
```
UUID=B82064122063D642  /mnt/workspace  ntfs3  rw,uid=1000,gid=1000,dmask=022,fmask=133,nocase,nofail,x-systemd.device-timeout=5  0 0
```
`nofail` is retained deliberately (see 1e for the visible-alert tradeoff). Storage/WD Black keep their existing `ntfs3` entries; `win_system` keeps `ntfs-3g` (do not touch — 3.1/3.2).

#### 1d. Clean-unmount-before-shutdown/hibernate systemd unit (Req 2.4)

The quiesce logic lives in a helper script the unit calls; the unit only orders execution before teardown targets.

**File**: `/usr/local/sbin/ntfs3-clean-unmount.sh` (helper, see 1f)

**File**: `/etc/systemd/system/ntfs3-clean-unmount.service`
```ini
[Unit]
Description=Cleanly unmount ntfs3 volumes before shutdown/hibernate
DefaultDependencies=no
Before=umount.target shutdown.target reboot.target halt.target
Before=systemd-hibernate.service systemd-suspend-then-hibernate.service
Requires=umount.target
Conflicts=reboot.target shutdown.target halt.target

[Service]
Type=oneshot
RemainAfterExit=yes
# ExecStop runs on the way DOWN (unit is "started" at boot, stopped at teardown)
ExecStart=/bin/true
ExecStop=/usr/local/sbin/ntfs3-clean-unmount.sh

[Install]
WantedBy=multi-user.target
```
> Design note: modeling the unmount as `ExecStop` of a `RemainAfterExit` oneshot (started at boot, stopped during teardown) gives correct ordering before `umount.target`/`shutdown.target` and before the hibernate services. It fires on shutdown, reboot, halt, and hibernate/suspend-then-hibernate. `fstab` remounts the drives on next boot (Req 2.4).

**RUN THIS YOURSELF — sudo required**
```bash
sudo cp ntfs3-clean-unmount.sh /usr/local/sbin/ && sudo chmod 755 /usr/local/sbin/ntfs3-clean-unmount.sh
sudo cp ntfs3-clean-unmount.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now ntfs3-clean-unmount.service
```

#### 1e. Surface mount failures instead of nofail masking (Req 2.3)

**Tradeoff:** dropping `nofail` makes a dirty Workspace **hang/degrade boot** (systemd waits on the device, drops to emergency after timeout) — high blast radius. Keeping `nofail` avoids the hang but hides the failure. **Recommended:** keep `nofail` AND add a lightweight post-boot alert that checks the mount and notifies the user, so boot never hangs but a missing drive is never silent.

**File**: `/etc/systemd/system/workspace-mount-check.service`
```ini
[Unit]
Description=Alert if /mnt/workspace is not mounted after boot
After=local-fs.target

[Service]
Type=oneshot
ExecStart=/bin/sh -c 'mountpoint -q /mnt/workspace || { echo "ALERT: /mnt/workspace NOT mounted (dirty bit?). Run: dmesg | grep ntfs3" | systemd-cat -t workspace-check -p err; exit 1; }'

[Install]
WantedBy=multi-user.target
```
**RUN THIS YOURSELF — sudo required**
```bash
sudo cp workspace-mount-check.service /etc/systemd/system/
sudo systemctl daemon-reload && sudo systemctl enable workspace-mount-check.service
```
Optional login-shell reinforcement (append to `~/.bashrc`, no sudo): `mountpoint -q /mnt/workspace || echo "WARNING: /mnt/workspace is not mounted — Kontakt will not launch."`

#### 1f. Write-quiesce helper script (Req 2.5)

**File**: `ntfs3-clean-unmount.sh` (installed to `/usr/local/sbin/`)
```bash
#!/usr/bin/env bash
# Cleanly unmount ntfs3 Workspace/Storage/WD Black behind a write-quiesce gate.
# Non-destructive: on failure it LOGS and skips (never force-unmounts).
set -u
LOG(){ echo "ntfs3-clean-unmount: $*" | systemd-cat -t ntfs3-unmount -p info; }
MOUNTS=(/mnt/workspace /mnt/storage /mnt/wdblack)   # adjust to actual mountpoints
TIMEOUT=20   # seconds per mount

sync   # global flush first

for MP in "${MOUNTS[@]}"; do
    mountpoint -q "$MP" || { LOG "$MP not mounted, skipping"; continue; }
    DEV=$(findmnt -no SOURCE "$MP"); BASEDEV=$(lsblk -no PKNAME "$DEV" 2>/dev/null || basename "$DEV")
    deadline=$(( $(date +%s) + TIMEOUT )); clean=0
    while [ "$(date +%s)" -lt "$deadline" ]; do
        sync
        # 1) no process holds the mount open
        if fuser -m "$MP" >/dev/null 2>&1; then LOG "$MP busy (fuser), retrying"; sleep 1; continue; fi
        # 2) no dirty/writeback pages system-wide (coarse gate)
        DIRTY=$(awk '/^Dirty:/{print $2}' /proc/meminfo)
        WB=$(awk '/^Writeback:/{print $2}' /proc/meminfo)
        # 3) per-device writeback via /proc/vmstat as corroboration
        NRWB=$(awk '/^nr_writeback /{print $2}' /proc/vmstat)
        if [ "${DIRTY:-1}" -le 8 ] && [ "${WB:-1}" -eq 0 ] && [ "${NRWB:-1}" -eq 0 ]; then
            clean=1; break
        fi
        LOG "$MP writeback pending (Dirty=${DIRTY} WB=${WB} nr_wb=${NRWB}), retrying"
        sleep 1
    done
    if [ "$clean" -eq 1 ] && umount "$MP" 2>/dev/null; then
        LOG "$MP unmounted cleanly (dev=$DEV)"
    else
        LOG "FAILURE: could not cleanly unmount $MP within ${TIMEOUT}s — NOT forcing. Volume may be left dirty."
        # deliberately do NOT force-unmount (Req 2.5 / 3.7)
    fi
done
exit 0
```
> `lsof "$MP"` may substitute for/augment `fuser -m` if installed. The Dirty threshold (≤8 pages) tolerates trivial residual kernel accounting; tighten to 0 if desired.

#### 1g. Recurrence-prevention summary + automount check (Req 2.6)
Recurrence prevention = clean-unmount unit (1d) + quiesce gate (1f) + driver consistency (all three `ntfs3` drives on the same driver; `win_system` intentionally `ntfs-3g`). Verify the automount rule itself is not dirtying the volume by confirming the unit fires and the quiesce gate reports clean on each teardown (see Testing). Windows Fast Startup already verified OFF — precondition only.

**CHECKPOINT GATE (must pass before Stage 2):** reboot cycle proves stable — `/mnt/workspace` present after boot, `dmesg` shows no `volume is dirty`, `journalctl -t ntfs3-unmount -b -1` shows clean unmounts for the previous shutdown.

### Stage 2 — Bug B: discriminate cause, then repair (Req 2.7–2.9) — only after Stage-1 checkpoint

#### 2a. Discrimination (beyond known-failed clear/rescan)
1. **Working vs blank `.cache` compare**: byte/field-diff a rendering library's `.cache` against a blank library's expected entry; note the embedded install-date epoch and which identity/mtime fields exist.
2. **Live-Kontakt fd probing** (`strace` unavailable): inspect `/proc/<kontakt-pid>/fd` while browsing to see which files/handles Kontakt opens when validating a tile (the prior session did this successfully). Identify whether it stats the library file, the `.cache`, or the `.nicnt`.
3. **`.nicnt` art presence**: confirm blank libs' `.nicnt` actually contain artwork markers (Amati had 8) — rules out "art missing" and points at cache validation.
4. **H-C driver test**: unmount and mount Workspace **read-only via ntfs-3g**, relaunch Kontakt, and see whether tiles return. If tiles render under `ntfs-3g` but not `ntfs3`, H-C is implicated (metadata exposure).

**RUN THIS YOURSELF — sudo required (H-C read-only probe, non-destructive)**
```bash
sudo umount /mnt/workspace
sudo mount -t ntfs-3g -o ro,uid=1000,gid=1000 /dev/sdb2 /mnt/workspace
# launch Kontakt, observe tiles, then restore ntfs3 rw mount afterwards
```
> Because this is read-only, it cannot re-dirty the volume (protects Req 3.6). Restore the normal `ntfs3` rw mount after testing.

#### 2b. Repair conditioned on the finding
- **If H-C** (ntfs3 metadata exposure): evaluate whether an `ntfs-3g` mount (or a metadata-normalization pass) makes tiles persist. If `ntfs-3g` for Workspace is viable without breaking latency/other consumers, document it as the fix; otherwise document the metadata delta and the tradeoff.
- **If H-B** (chkdsk rewrote metadata): determine what legitimately regenerates `.cache` — e.g. Batch Re-save, or a proper re-install/registration path per library — since a plain clear failed. Apply only the working regeneration path.
- **If H-A** (mutex/DB reference breakage): targeted `komplete.db3` cache-reference repair to re-link libraries to their `.cache`/artwork; correct into a consistent DB state (Req 2.9).
- **If none regenerates in-setup**: document the limitation explicitly; do NOT loop on the known-failed clear/rescan/re-add (Req 2.8).

Because standalone and Reaper/yabridge share the same `~/.wine` prefix and `komplete.db3`, any DB/cache repair applies to BOTH workflows (Req 2.8, 3.4). Back up `komplete.db3` and `LibrariesCache/` before any DB/cache write (backup already at `_kiro_backup_20260901/LibrariesCache_bak`).

### Stage 3 — Bug C: investigate + documented decision (Req 2.10–2.11) — after Stage 2 understood

1. Reduce EWQL RA to a **single clean registration** (remove the duplicate/trailing-space entry so only one SNPID is in play).
2. Test **preset load**; then test **direct `.nki`** via Files browser (prior: still failed).
3. Test registering EWQL RA as a **Custom library (Import Content)** instead of a Player library, as an alternative access path.
4. **Decision:** if any path works, document it as the fix. If confirmed unfixable in-setup (SNPID baked in `.nicnt`, needs matching-SNPID re-acquisition), record that conclusion and **remove or clearly flag** EWQL RA so it stops emitting misleading mount/path errors (Req 2.11). Keep this classification separate from Bug A (genuine unmount) and leftover-`F:` path failures (Req 2.12/1.14).

### Stage 4 — Shared path migration to Z: (Req 2.12–2.13) — woven in after Stage 1, alongside 2/3

1. **Keep `Z:->/` always** — all 120 Player libraries already resolve via `Z:\mnt\workspace\VST Install\Kontakt Vst-i\<Library>` (drive-letter independent, bulletproof). Do not change these.
2. **Make `F:` deterministic in the interim** so it is not a per-run race: add `F:->/mnt/workspace` as a persistent Wine drive entry (winecfg / `dosdevices` symlink managed at prefix level) rather than relying on the launcher to recreate it each run. Keep the launcher's recreate as a fallback.
3. **Repoint non-Player user-content base path** off `F:\VST Install\Kontakt Portable\UserData\Kontakt 8\` to the `Z:` (or `D:`) equivalent so it no longer depends on `F:`.
4. **Identify + repoint baked-`F:` preset/instrument sample paths** inside `.nki`/`.nksn` to `Z:\...`.
5. **Only after** all baked-`F:` references are repointed, retire `F:`. Do NOT repurpose `F:` for another drive (would break any remaining baked-`F:` presets).
6. Verify Windows-native (`D:`), VirtualBox, and Wine all still resolve after each step (Req 3.3).

## Testing Strategy

### Validation Approach
Two-phase per bug: first surface counterexamples on the UNFIXED system to confirm/refute the root cause, then verify the fix works and preserves existing behavior. Respect staging — Bug A proven across a reboot before Bug B; Bug B understood before Bug C.

### Exploratory Bug Condition Checking

**Goal:** surface counterexamples BEFORE fixing; confirm or refute each root-cause hypothesis. If refuted, re-hypothesize.

**Bug A test plan:** on the unfixed system, attempt the mount and read `dmesg`; simulate an unclean dismount then reboot and observe the dirty bit reappear.
- **Dirty-refusal test**: `sudo mount -t ntfs3 /dev/sdb2 /mnt/workspace` → expect `volume is dirty` (confirms C_A).
- **nofail-masking test**: reboot with dirty volume → expect boot completes, `/mnt/workspace` absent, no user alert (confirms 1.2).
- **ntfsfix-limitation test**: run `ntfsfix`, retry `ntfs3` mount → expect still refused (confirms the documented limitation).
- **Unclean-dismount recurrence test**: cut power/rushed shutdown without the unit → expect dirty bit set next boot.

**Bug B test plan:** on the mounted unfixed drive, browse libraries and record which tiles are blank and whether their `.cache` exists.
- **Blank-set test**: enumerate blank tiles → expect the set == Player libraries with no `.cache` (confirms C_B).
- **Known-failed-remedy test**: clear `LibrariesCache`, relaunch → expect no regeneration (confirms 1.10; restore from backup).
- **fd-probe / ntfs-3g-vs-ntfs3 test**: probe `/proc/<pid>/fd` and compare tile rendering under `ntfs-3g` ro vs `ntfs3` → expected counterexample distinguishes H-C from H-A/H-B.

**Bug C test plan:** load an EWQL RA preset and a direct `.nki`.
- **SNPID-mismatch test**: load preset → expect "not installed"; inspect `LibraryHints.xml` A02/A05 entries (confirms C_C).

**Expected counterexamples:** dirty mount refused; masked boot; blank tiles for cache-less libraries; EWQL RA "not installed". Possible Bug B causes: mutex/DB detach (H-A), chkdsk metadata reassignment (H-B), ntfs3 metadata exposure (H-C).

### Fix Checking
**Goal:** for all inputs where a bug condition holds, the fixed system produces the expected behavior.
```
FOR ALL state WHERE isBugCondition_A(state) DO
  clearDirty(); mount(); ASSERT mounted("/mnt/workspace") AND no "volume is dirty" in dmesg
  simulateShutdown(); ASSERT unit fired AND quiesceGate reported clean AND dirtyBit == CLEAR next boot
END FOR
FOR ALL lib WHERE isBugCondition_B(lib) DO
  applyCauseDrivenRepair(); ASSERT tile.artworkRendered(lib) == true (both workflows)  // OR limitation documented
END FOR
FOR ALL load WHERE isBugCondition_C(load) DO
  ASSERT workingAccessPath(load) OR decisionDocumented(load) AND NOT misleadingMountError(load)
END FOR
```

### Preservation Checking
**Goal:** for all inputs where NO bug condition holds, the fixed system equals the original.
```
FOR ALL input WHERE NOT isBugCondition_*(input) DO
  ASSERT behavior_original(input) == behavior_fixed(input)
END FOR
```
Property-based testing is recommended for preservation: it generates many inputs across the domain, catches edge cases, and gives strong "unchanged behavior" guarantees. Observe behavior on the UNFIXED system first (other drives mounting, clean-volume boots, valid-cache tiles, both Kontakt workflows), then assert it holds after each stage.

**Preservation test cases:**
1. **Other ntfs3 drives**: Storage (`sdc1`) and WD Black (`nvme0n1p2`) still mount via `ntfs3` after the unit and any driver work (3.1).
2. **win_system driver**: `sda4` still mounts via `ntfs-3g`/fuseblk (3.2).
3. **Three consumers**: Workspace usable from Windows `D:`, VirtualBox, and Wine after path/driver changes (3.3).
4. **Both Kontakt workflows**: standalone WineASIO/pw-jack and Reaper/yabridge both launch and function (3.4).
5. **Clean-volume boot**: an already-clean Workspace mounts with no force/manual step (3.5).
6. **Valid-cache tiles**: libraries with present valid `.cache` keep rendering after Bug B repair.
7. **No cross-regression**: Bug A work does not corrupt `komplete.db3`; Bug B/C work does not re-dirty the volume (3.6) — verify `dmesg` clean and DB integrity after Stage 2/3.
8. **Non-destructive posture**: no force-mount used as primary; backups taken before DB/cache writes (3.7).

### Unit Tests
- Quiesce helper: `fuser -m` busy vs idle branches; Dirty/Writeback thresholds; timeout-failure path logs and does NOT force-unmount.
- Mount-check unit emits an error to the journal when `/mnt/workspace` is absent.
- Path resolution: `Z:\mnt\workspace\...` and repointed non-Player base resolve; baked-`F:` presets resolve while `F:` still mapped.

### Property-Based Tests
- Randomized dirty/clean volume states → fixed boot either mounts (clean) or alerts without hang (dirty), never silently absent.
- Randomized process/writeback conditions → quiesce gate only unmounts when truly idle, else logs failure (never forces).
- Randomized library sets with/without valid `.cache` → tiles render iff cache valid; preservation for the valid-cache subset.

### Integration Tests
- Full reboot cycle: shutdown → unit fires → quiesce clean → boot → `/mnt/workspace` present, `dmesg` clean, `journalctl -t ntfs3-unmount` clean. **This is the Stage-1→Stage-2 checkpoint.**
- Hibernate/suspend-then-hibernate cycle → same clean result.
- End-to-end Kontakt: launch standalone and in Reaper on the stable drive; browse libraries (tiles), verify visual feedback; attempt EWQL RA and confirm it is either fixed or flagged (no misleading mount error).
- Context switch: verify Storage/WD Black/win_system all still mount across the same cycle.
