# Bugfix Requirements Document

## Introduction

Kontakt 8 Portable runs under Wine on CachyOS, both standalone (WineASIO via `pw-jack`) and as a yabridge `.so` in Reaper. Everything — the Kontakt executable, PAResources, the library DB, user content, and all sample libraries — lives on the NTFS "Workspace" volume (`/dev/sdb2`, UUID `B82064122063D642`, label `Workspace`, 2.7T).

Diagnostics establish that there are TWO DISTINCT bugs that happen to share this one drive. They must not be conflated:

**Bug A — Dirty bit / mount refusal (root cause CONFIRMED).**
The Workspace volume carries a dirty NTFS bit, and the `ntfs3` kernel driver hard-refuses to mount a dirty volume.

Kernel evidence (ground truth):
- `ntfs3(sdb2): volume is dirty and "force" flag is not set!`
- `ntfs3(sdb2): It is recommended to use chkdsk.`

Because the mount fails and `fstab` uses `nofail`, boot silently continues without the drive, so `/mnt/workspace` is absent and Kontakt cannot even launch.

Confirmed evidence narrowing Bug A's recurrence:
- Windows Fast Startup is verified DISABLED — NOT the cause. Recorded only as a satisfied precondition.
- `chkdsk` from Windows is a PROVEN-WORKING clear method: last time it cleared the dirty bit and the drive returned clean into CachyOS. Windows does not re-dirty the volume.
- The recurrence source is the LINUX side: the volume is left dirty on an unclean/rushed dismount at shutdown/hibernate, where `ntfs3` is not guaranteed to flush and clear the dirty bit before power-down. `nofail` then masks the failure at boot.

**Bug B — Blank library artwork tiles while Kontakt is running on a MOUNTED drive (cause OPEN).**
This is a genuinely separate defect, not a symptom of Bug A. Reasoning: since Kontakt and everything else live on the Workspace drive, Kontakt cannot launch at all unless the drive is mounted. Therefore, any time the tiles are observed blank, the drive is necessarily already mounted and Kontakt is running. "The drive is unmounted" is logically ruled out as an explanation for blank tiles. Bug B persists on a working, mounted drive.

KNOWN FACTS (from the prior `kontakt-wine-optimization` session's contemporaneous notes):
- Tile artwork is a per-library BROWSER CACHE at `/mnt/workspace/VST Install/Kontakt Portable/UserData/Kontakt 8/LibrariesCache/` (observed as 62 `.cache` files, ~17MB), keyed by library ID. It is not loose PNGs; `pictures/` was empty. There are ~120 registered Player libraries vs 62 cache files, matching the set of blank tiles.
- The `.cache` filenames embed original install-date epochs, suggesting they are generated at a library's proper install/registration time, not by the rescan tools available in this portable setup.
- Already-attempted fixes that did NOT work: clearing `LibrariesCache` (did not regenerate; count stayed 0 after clear+relaunch, restored from backup), Import Content rescan (stayed at 62), and KTP Library-Manager re-add. So "just clear/rescan the cache" is a known-failed remedy and must not be the planned fix on its own.

CONFLICTING EVIDENCE ON CAUSE (unresolved — the user has chosen to investigate after the drive is mounted):
- The prior notes concluded tiles worked THROUGH the mutex clear and the KTP re-adds and went blank only AFTER the Workspace `chkdsk`, attributing it to `chkdsk` rewriting NTFS metadata (MFT/USN/timestamps) so Kontakt's cache-validity check (file identity/mtime) treated the `.cache` entries as stale.
- The user's more recent recollection is that tiles were blank even before `chkdsk`.
These conflict, so the cause is OPEN among:
- **H-A (Mutex / DB rebuild):** the mutex clear / partial rebuild detached the cache/artwork references. Weakened by the prior notes ("tiles worked through the mutex clear"), but not fully eliminated given the conflict.
- **H-B (chkdsk metadata reassignment):** `chkdsk` rewrote NTFS metadata, invalidating cache-entry identity/mtime validation. Supported by the prior notes; contested by the recent recollection.
- **H-C (ntfs3 metadata exposure):** `ntfs3` exposes timestamps/metadata differently than `ntfs-3g`/Windows, so even a clean mount presents "changed" metadata to Kontakt's cache validation.

None are testable until the drive is mounted clean. So Bug B's cause is determined by a discrimination step AFTER Bug A is fixed and the drive is proven stable, and that step must go BEYOND the already-failed cache clear/rescan (e.g. compare `.cache` install-date stamps against library file identity/mtime, and compare behaviour under `ntfs3` vs `ntfs-3g`).

**Bug C — EWQL RA library unusable (tracked in scope).**
EWQL RA presets fail with "not installed", and per the prior notes this is a baked-in SNPID mismatch in the repack (`.nicnt` declares one SNPID; the instruments demand another; A02 vs A05 seen), which persisted even on direct `.nki` load and through a clean single-entry re-registration. The prior verdict was "content-side casualty, not fixable by config/registration/drive-letters/Wine". That verdict is treated here as a STRONG PRIOR, not a closed door: Bug C is tracked in scope so it gets an explicit, staged investigation and a documented decision, rather than being silently dismissed. Its "check if the drive is mounted"/content-missing wording must still be separated from the genuine mount and leftover-`F:` path questions. Bug C is investigated only AFTER the drive is stable (Bug A) and after the tile/cache picture is understood (Bug B), because those could otherwise mask or mimic its symptoms. Any true fix would likely require re-acquiring a matching-SNPID package; if confirmed unfixable in-setup, that outcome is recorded as the resolution.

**Staging.** (1) Fix Bug A: clear the dirty bit properly and make the mount reliable, with recurrence prevention. (2) Only after the drive is proven stable across a reboot cycle, discriminate Bug B's cause among H-A/H-B/H-C (beyond the known-failed cache clear) and then repair tiles + cache. (3) Migrate Kontakt paths off `F:` to a single consistent scheme. (4) Investigate Bug C (EWQL RA SNPID) and reach a documented decision. (5) Verify the automount rule is not itself contributing to the dirty bit.

**Constraints.** Forcing the mount (`rw,force`/`clear_dirty`) is backup-only, never the primary fix. The volume must remain usable by Windows (native `D:`), Windows in VirtualBox, and Linux Wine, so path/driver changes must not break any consumer. Confirm proof before changing anything; prefer non-destructive actions.

## Bug Analysis

### Current Behavior (Defect)

#### Bug A — Dirty bit / mount refusal

1.1 WHEN the Workspace NTFS volume (`/dev/sdb2`) has its dirty bit set after an unclean dismount THEN the `ntfs3` driver refuses to mount it and emits `volume is dirty and "force" flag is not set!`, leaving `/mnt/workspace` absent

1.2 WHEN `/mnt/workspace` is absent at boot AND `fstab` uses `nofail` for the Workspace entry THEN the system continues booting silently without the drive and without surfacing the failure to the user

1.3 WHEN `/mnt/workspace` is absent THEN Kontakt cannot launch at all, because the Kontakt executable and all its content reside on that volume

1.4 WHEN the system shuts down or hibernates THEN the `ntfs3` Workspace volume is dismounted without a guaranteed write-quiesce/clean-unmount step (no assured flush, no confirmation that writes are complete and the driver has cleared the dirty bit before power-down), leaving the NTFS dirty bit set on the Linux side

1.5 WHEN the volume is dismounted uncleanly (ordinary unclean shutdown) THEN the dirty bit is set again, reproducing the condition even after a prior repair

#### Bug B — Blank tiles on a mounted drive

1.6 WHEN the Workspace drive is mounted AND Kontakt is running THEN the library browser renders a subset of tiles with no artwork images, even though Kontakt has successfully loaded from the same drive (proving the breakage is independent of mount state); the blank set corresponds to Player libraries with no matching entry in the per-library browser cache at `UserData/Kontakt 8/LibrariesCache/` (~62 `.cache` files present vs ~120 registered libraries)

1.7 WHEN the mutex was cleared/rebuilt THEN the browser cache references may have been detached (hypothesis H-A); the prior session's notes state tiles survived the mutex clear, weakening but not eliminating this

1.8 WHEN `chkdsk` repaired the volume THEN NTFS metadata (MFT/USN/timestamps) that Kontakt uses to validate `.cache` entries by file identity/mtime may have been reassigned, making valid caches look stale (hypothesis H-B; supported by prior notes, contested by recent recollection)

1.9 WHEN the volume is mounted via `ntfs3` rather than `ntfs-3g`/Windows THEN timestamps/metadata may be exposed differently, potentially failing Kontakt's `.cache` validity check even on a clean mount (hypothesis H-C)

1.10 WHEN the known cache remedies are attempted (clearing `LibrariesCache`, Import Content rescan, KTP Library-Manager re-add) THEN they do NOT regenerate the missing `.cache` entries, because those files are stamped with original install-date epochs and appear to be generated only at proper install/registration time

#### Shared / path-hygiene defects

1.11 WHEN the Kontakt library DB has been repeatedly hand-repaired against an intermittently-absent drive THEN it has accumulated inconsistent `F:`/`D:`/`Z:` paths, cleared/rebuilt mutex state, and partially rebuilt PAResources/user-content

1.12 WHEN `launch_kontakt_wineasio.sh` runs THEN it recreates the `F:` dosdevices symlink every time because the symlink does not persist across reboots, and both `D:` and `F:` point at the same `/mnt/workspace`, creating duplicate/inconsistent path references (the prior notes confirm some presets carry baked `F:` sample paths, so `F:` must stay mapped until those are repointed, and all 120 Player libraries already resolve via `Z:\mnt\workspace\...`)

#### Bug C — EWQL RA library unusable

1.13 WHEN the EWQL RA pack is loaded (via its tile OR via direct `.nki` load) THEN presets fail with "not installed" due to a baked-in SNPID mismatch in the repack (`.nicnt` SNPID vs instrument SNPID; A02 vs A05 observed), which prior investigation could not fix via config, re-registration, drive letters, or Wine setup

1.14 WHEN EWQL RA emits "check if the drive is mounted"/content-missing wording THEN it must be classified as either Bug A (genuinely unmounted), a leftover-`F:` stored-path failure, or the Bug C SNPID problem — these must NOT be conflated

### Expected Behavior (Correct)

#### Bug A — Dirty bit / mount refusal

2.1 WHEN the Workspace NTFS volume has its dirty bit set THEN the system SHALL clear the dirty bit properly using a proven-working method (`chkdsk` from Windows, which the user confirmed works, or `ntfsfix`/`fsck.ntfs` from Linux) rather than relying on force-mount as the primary fix

2.2 WHEN the dirty bit has been cleared THEN the Workspace volume SHALL mount reliably at `/mnt/workspace` with the `ntfs3` driver using consistent options, and `/mnt/workspace` SHALL be present after boot

2.3 WHEN a mount of the Workspace volume fails at boot THEN the failure SHALL be surfaced to the user (reconsider `nofail` masking) rather than silently continuing without the drive

2.4 WHEN the system shuts down or hibernates THEN a clean-unmount-before-shutdown/hibernate mechanism (a systemd unit ordered before `umount.target`/`shutdown.target` and before `systemd-hibernate.service`) SHALL cleanly unmount all `ntfs3` drives (Workspace, Storage, WD Black) prior to power-down, and those drives SHALL be remounted automatically on next boot via `fstab`

2.5 WHEN the clean-unmount mechanism is about to unmount each `ntfs3` volume THEN it SHALL first confirm the filesystem is quiesced with NO in-flight writes before calling `umount` — specifically it SHALL run `sync`, verify no process holds the mount open (`fuser -m` / `lsof` on the mountpoint), and verify no dirty/writeback pages remain for that backing device (e.g. `/proc/meminfo` `Dirty`/`Writeback` and the per-device writeback state) — and it SHALL wait up to a bounded timeout retrying the idle check; if it still cannot achieve a clean unmount within the timeout it SHALL log the failure visibly rather than force-unmounting

2.6 WHEN recurrence prevention is applied THEN it SHALL center on the clean-unmount-before-shutdown/hibernate mechanism with the write-quiesce safety gate (per 2.4 and 2.5), a consistent NTFS driver across drives, and verification that the automount rule itself is not causing the dirty bit; Windows Fast Startup is recorded as already verified disabled (a satisfied precondition, not an action item)

#### Bug B — Blank tiles on a mounted drive

2.7 WHEN the drive has been proven stable across a reboot cycle THEN Kontakt SHALL launch AND a discrimination step SHALL determine Bug B's actual cause among H-A (mutex/DB reference breakage), H-B (chkdsk metadata reassignment), and H-C (ntfs3 metadata exposure) before committing to a repair approach; the step SHALL go beyond the known-failed cache clear/rescan (e.g. compare `.cache` install-date stamps against library file identity/mtime, and compare behaviour under `ntfs3` vs `ntfs-3g`)

2.8 WHEN Bug B's cause has been identified THEN a repair that actually regenerates or revalidates the per-library `LibrariesCache` `.cache` entries SHALL be applied so the artwork tiles render correctly in the Kontakt library browser for BOTH standalone (WineASIO/pw-jack) and Reaper/yabridge usage; if no in-setup regeneration path exists, the limitation SHALL be documented rather than repeatedly retrying known-failed remedies

2.9 WHEN the Kontakt library DB is repaired THEN it SHALL be corrected into a consistent state (resolving library paths and cache references), and this SHALL happen only AFTER the drive is proven stable

#### Bug C — EWQL RA library

2.10 WHEN the drive is stable and the tile/cache picture is understood THEN Bug C SHALL be investigated with an explicit step (confirm the SNPID mismatch, test direct `.nki` load, test registering EWQL RA as a Custom library vs Player library) and SHALL reach one of two documented resolutions: a working fix if one is found, or a recorded determination that it requires a matching-SNPID package re-acquisition (unfixable in-setup)

2.11 WHEN Bug C is determined unfixable in-setup THEN the outcome SHALL be documented and EWQL RA SHALL be handled so it does not produce misleading mount/path errors (e.g. removed or clearly flagged), rather than left to masquerade as a drive/path fault

#### Shared / path-hygiene

2.12 WHEN a "check if the drive is mounted"/content-missing error appears on a mounted, stable drive THEN it SHALL be traced to a genuine mount gap, a leftover-`F:` stored-path failure, or the Bug C SNPID problem, and resolved or documented accordingly

2.13 WHEN Kontakt user-content / library paths are configured THEN they SHALL migrate off `F:` toward a single consistent scheme, preferring the `Z:\mnt\workspace\...` convention already used by all 120 Player libraries (drive-letter independent), repointing baked-`F:` preset paths and the non-Player user-content base path so `F:` can eventually be retired without breaking Windows native, Windows VirtualBox, or Linux Wine consumers

### Unchanged Behavior (Regression Prevention)

3.1 WHEN the Storage volume (`sdc1`) or WD Black volume (`nvme0n1p2`) is mounted THEN the system SHALL CONTINUE TO mount them successfully with the `ntfs3` driver

3.2 WHEN the `win_system` volume is accessed THEN the system SHALL CONTINUE TO be able to mount it (currently via the old `ntfs`/fuseblk / `ntfs-3g` driver) without regression

3.3 WHEN the Workspace drive is accessed from Windows native (`D:`), Windows in VirtualBox, or Linux Wine THEN the drive SHALL CONTINUE TO be usable by all three consumers after any path or driver changes

3.4 WHEN Kontakt runs standalone via WineASIO/pw-jack OR as a yabridge `.so` in Reaper THEN both workflows SHALL CONTINUE TO launch and function once the drive is stable

3.5 WHEN the Workspace volume is already clean and present THEN it SHALL CONTINUE TO mount at `/mnt/workspace` without requiring force-mount or manual repair

3.6 WHEN a fix for one bug is applied THEN it SHALL NOT introduce or worsen the other (e.g., the Bug A clean-unmount/driver work SHALL NOT further corrupt the Kontakt DB, and the Bug B DB/tile repair SHALL NOT re-dirty the volume)

3.7 WHEN no change is proven safe THEN the system SHALL CONTINUE TO avoid destructive operations, treating force-mount (`rw,force`/`clear_dirty`) as backup-only and confirming proof before altering anything
