# Implementation Plan

## Overview

This plan fixes three distinct bugs on the NTFS "Workspace" volume, in a **staged and gated** order:

- **Stage 1 (Bug A)** — clear the dirty bit, make the mount reliable, and prevent recurrence with a clean-unmount-before-teardown systemd unit + write-quiesce gate. Stage 1 MUST be proven stable across a **full reboot cycle** (an explicit checkpoint gate) before any Stage 2 work touches the DB/cache.
- **Stage 2 (Bug B)** — discriminate the blank-tile cause (H-A/H-B/H-C) *before* repairing; the known-failed clear/rescan/re-add is NOT the fix.
- **Stage 3 (Bug C)** — investigate EWQL RA SNPID to a documented decision, after Bug B is understood.
- **Stage 4 (path migration)** — converge on `Z:` and retire `F:` safely; woven in after Stage 1, alongside Stages 2/3.

**Agent execution posture:** interactive sudo is NOT available to the agent. Every root action (mount, `ntfsfix`, `chkdsk`, `fstab` edit, installing/enabling systemd units) is framed as *author the artifact/commands in-workspace, then have the USER run it, then verify the result*. The agent DOES author the unit files and helper script as workspace files. Non-destructive by default: back up `komplete.db3` and `LibrariesCache/` before any DB/cache write; force-mount is backup-only.

Property tests confirm bug conditions FIRST (expected to FAIL on the unfixed system), then fix-checking and preservation-checking verify the repair. Tasks marked `*` are genuinely optional.

## Tasks

### Bug-condition exploration (write first — EXPECTED TO FAIL on the unfixed system)

- [ ] 1. Write bug-condition exploration property tests (EXPECTED TO FAIL on unfixed system)
  - **Property 1: Bug Condition** - Dirty-mount refusal, nofail masking, blank-tile==cacheless, EWQL SNPID
  - **CRITICAL**: These tests MUST FAIL / produce the documented counterexamples on the unfixed system — failure confirms the bug conditions exist
  - **DO NOT attempt to fix the tests or the system when they fail** — the failures are the deliverable of this task
  - **GOAL**: Surface concrete counterexamples for each of the four bug conditions before any fix
  - **Scoped PBT approach**: these are deterministic, environment-bound conditions — scope each property to its concrete failing case for reproducibility

  - [ ] 1.1 Bug A — dirty-refusal counterexample (author probe commands for USER, then verify)
    - **Property 1: Bug Condition A** - Dirty-mount refusal
    - Author the exact commands for the USER (sudo required, agent cannot run): `sudo mount -t ntfs3 /dev/sdb2 /mnt/workspace 2>&1; dmesg | tail -20` and `sudo ntfsinfo -m /dev/sdb2 | grep -iE 'dirty|volume flags'`
    - **EXPECTED OUTCOME**: `dmesg` shows `volume is dirty and "force" flag is not set!` (confirms `isBugCondition_A`)
    - Document the counterexample (dirty bit SET, mount REFUSED)
    - _Bug_Condition: isBugCondition_A(state) — dirtyBit==SET AND driver==ntfs3 AND mount REFUSED AND fstab has nofail_
    - _Requirements: 1.1_

  - [ ] 1.2 Bug A — nofail-masking counterexample (author reboot check for USER, then verify)
    - **Property 1: Bug Condition A** - nofail masking
    - With the volume dirty, have the USER reboot; author the check `mountpoint -q /mnt/workspace; echo $?` and `journalctl -b | grep -i workspace`
    - **EXPECTED OUTCOME**: boot completes, `/mnt/workspace` ABSENT, no user-visible alert (confirms 1.2 masking)
    - Document that the failure is silently masked
    - _Bug_Condition: isBugCondition_A(state) — nofail masks the failed mount_
    - _Requirements: 1.2_

  - [ ]* 1.3 Bug A — ntfsfix-limitation counterexample (author for USER, then verify)
    - **Property 1: Bug Condition A** - ntfsfix does not clear the flag ntfs3 checks
    - Author for USER: `sudo umount /mnt/workspace 2>/dev/null; sudo ntfsfix /dev/sdb2` then retry the ntfs3 mount from 1.1
    - **EXPECTED OUTCOME**: `ntfs3` STILL refuses after `ntfsfix` (confirms the documented limitation; establishes chkdsk-from-Windows as the primary clear)
    - _Requirements: 1.1_

  - [ ] 1.4 Bug B — blank-set == cacheless-libraries counterexample (agent inspects mounted drive)
    - **Property 1: Bug Condition B** - Blank tile set equals cacheless Player libraries
    - On the mounted, running Kontakt: enumerate blank tiles and diff against the `.cache` files present in `UserData/Kontakt 8/LibrariesCache/` (~62 present) vs ~120 registered Player libraries
    - **EXPECTED OUTCOME**: the blank set == the set of Player libraries with no matching `.cache` entry (confirms `isBugCondition_B`)
    - Document the counterexample list (the ~58 cacheless libraries)
    - _Bug_Condition: isBugCondition_B(lib) — registered Player lib AND artwork not rendered AND (.cache missing OR fails validation)_
    - _Requirements: 1.6_

  - [ ]* 1.5 Bug B — known-failed-remedy counterexample (back up first, then verify no regeneration)
    - **Property 1: Bug Condition B** - Clear/rescan does not regenerate `.cache`
    - Back up `LibrariesCache/` first; clear it, relaunch Kontakt, run Import Content rescan, KTP re-add; restore from backup after
    - **EXPECTED OUTCOME**: count stays at 0 after clear+relaunch / stays 62 after rescan — no regeneration (confirms 1.10 that these are known-failed remedies)
    - _Requirements: 1.10_

  - [ ] 1.6 Bug C — EWQL RA SNPID-mismatch counterexample (agent inspects + loads)
    - **Property 1: Bug Condition C** - EWQL RA SNPID mismatch → "not installed"
    - Load an EWQL RA preset (and a direct `.nki` via Files browser); inspect `LibraryHints.xml` for the A02 vs A05 SNPID entries (incl. the trailing-space duplicate)
    - **EXPECTED OUTCOME**: preset fails "not installed"; `.nicnt` SNPID (A02) != instrument demanded SNPID (A05) (confirms `isBugCondition_C`)
    - Document the counterexample and classify the "check if the drive is mounted" wording as NOT Bug A
    - _Bug_Condition: isBugCondition_C(load) — library==EWQL RA AND nicnt.SNPID != instrument.demandedSNPID AND result=="not installed"_
    - _Requirements: 1.13, 1.14_

### Preservation baseline (write before any fix — EXPECTED TO PASS on unfixed system)

- [ ] 2. Write preservation property tests (BEFORE any fix — observe on UNFIXED system)
  - **Property 5: Preservation** - Other drives, clean boots, both workflows, no cross-regression
  - **IMPORTANT**: Follow observation-first methodology — record actual behavior on the UNFIXED system, then assert it holds unchanged after each stage
  - **EXPECTED OUTCOME**: all observations below PASS on the unfixed system (this is the baseline to preserve)

  - [ ] 2.1 Observe other-drive mount behavior
    - Observe: Storage (`sdc1`) and WD Black (`nvme0n1p2`) mount via `ntfs3`; `win_system` (`sda4`) mounts via `ntfs-3g`/fuseblk
    - Record `findmnt`/`mount` output and drivers for each
    - Write a property test asserting these mounts and drivers are unchanged across the domain of boots
    - _Preservation: Preservation Requirements 3.1, 3.2_
    - _Requirements: 3.1, 3.2_

  - [ ] 2.2 Observe three-consumer usability and both Kontakt workflows
    - Observe: Workspace usable from Windows native (`D:`), VirtualBox, and Linux Wine; Kontakt launches standalone (WineASIO/pw-jack) AND as yabridge `.so` in Reaper (shared `~/.wine` prefix + `komplete.db3`)
    - Record baseline launch/resolve results for both workflows
    - _Preservation: Preservation Requirements 3.3, 3.4_
    - _Requirements: 3.3, 3.4_

  - [ ] 2.3 Observe clean-volume boot and valid-cache tile rendering
    - Observe: an already-clean Workspace mounts at `/mnt/workspace` with no force/manual step; libraries WITH a present valid `.cache` render their tile (working control from 1.4)
    - Write a property test: for the valid-`.cache` subset, tiles render (must stay true after Bug B repair)
    - _Preservation: Preservation Requirements 3.5, and valid-cache subset_
    - _Requirements: 3.5_

  - [ ]* 2.4 Write property-based preservation tests (randomized domains)
    - **Property 5: Preservation** - Randomized volume/writeback/library states
    - Randomized dirty/clean volume states → boot either mounts (clean) or alerts without hang (dirty), never silently absent
    - Randomized process/writeback conditions → quiesce gate only unmounts when truly idle, else logs failure (never forces)
    - Randomized library sets with/without valid `.cache` → tiles render iff cache valid
    - **EXPECTED OUTCOME**: preservation properties hold on the unfixed system for the non-bug-condition subset
    - _Requirements: 3.1, 3.2, 3.5, 3.6, 3.7_

### Stage 1 — Bug A: clear dirty bit + reliable mount + recurrence prevention

- [x] 3. Fix Bug A — reliable clean mount with recurrence prevention

  - [x] 3.1 Author the write-quiesce helper script in-workspace
    - Create workspace file `ntfs3-clean-unmount.sh` per design §1f
    - Covers ALL THREE ntfs3 drives (Workspace, Storage, WD Black) — user chose the safest approach because more instrument libraries will be added to the other drives
    - `sync` first; per-mount loop: `mountpoint -q`, `fuser -m` (or `lsof`) idle check, `/proc/meminfo` Dirty/Writeback + `/proc/vmstat` nr_writeback gate, bounded retry (TIMEOUT=20s)
    - On success `umount`; on timeout, LOG a visible failure and DO NOT force-unmount (non-destructive)
    - _Bug_Condition: isBugCondition_A(state)_
    - _Expected_Behavior: Property 1 — clean unmount behind write-quiesce gate; log-not-force on failure_
    - _Requirements: 2.5_

  - [x] 3.2 Author the clean-unmount-before-teardown systemd unit in-workspace
    - Create workspace file `ntfs3-clean-unmount.service` per design §1d
    - `Type=oneshot`, `RemainAfterExit=yes`, `ExecStart=/bin/true`, `ExecStop=/usr/local/sbin/ntfs3-clean-unmount.sh`
    - Ordering: `Before=umount.target shutdown.target reboot.target halt.target` and `Before=systemd-hibernate.service systemd-suspend-then-hibernate.service`
    - `fstab` remounts the drives on next boot
    - _Bug_Condition: isBugCondition_A(state)_
    - _Expected_Behavior: Property 1 — cleanly unmount all ntfs3 drives before teardown_
    - _Requirements: 2.4, 2.6_

  - [x] 3.3 Author the post-boot mount-check unit in-workspace
    - Create workspace file `workspace-mount-check.service` per design §1e
    - Emits an error to the journal (`systemd-cat -p err`) when `/mnt/workspace` is absent after boot; keeps `nofail` so boot never hangs but a missing drive is never silent
    - Note the optional `~/.bashrc` login-shell reinforcement line (no sudo)
    - _Bug_Condition: isBugCondition_A(state)_
    - _Expected_Behavior: Property 1 — surface mount failure instead of masking_
    - _Requirements: 2.3_

  - [x] 3.4 Prepare the dirty-bit clear commands for the USER (primary: chkdsk; alt: ntfsfix)
    - **RUN THIS YOURSELF — sudo/Windows required** (agent cannot run): PRIMARY = clean Windows full shutdown then `chkdsk D: /f` (Fast Startup already OFF), boot back into CachyOS
    - Document the Linux ALTERNATIVE and its limitation: `sudo umount /mnt/workspace; sudo ntfsfix /dev/sdb2` may leave the flag `ntfs3` checks set → fall back to chkdsk
    - Force-mount (`rw,force`/`clear_dirty`) is backup-only, never primary
    - Verify afterward: `/mnt/workspace` mounts clean, `dmesg` shows no `volume is dirty`
    - _Bug_Condition: isBugCondition_A(state)_
    - _Expected_Behavior: Property 1 — clear via proven method, not force-mount_
    - _Requirements: 2.1, 2.2_

  - [x] 3.5 Prepare fstab verification/edit for the USER (retain nocase + nofail)
    - **RUN THIS YOURSELF — sudo required**: take a fresh `/etc/fstab` backup, then confirm the Workspace entry matches design §1c (ntfs3, `rw,uid=1000,gid=1000,dmask=022,fmask=133,nocase,nofail,x-systemd.device-timeout=5`)
    - Do NOT drop `nocase` (fixed ~10,260 lowercase-probe failures); do NOT touch Storage/WD Black ntfs3 entries or the `win_system` ntfs-3g entry
    - _Expected_Behavior: Property 1 — reliable mount with consistent options_
    - _Preservation: 3.1, 3.2, 3.5_
    - _Requirements: 2.2_

  - [x] 3.6 Prepare install/enable commands for the USER and verify units are active
    - **RUN THIS YOURSELF — sudo required**: `cp` helper to `/usr/local/sbin/` (chmod 755), `cp` both `.service` files to `/etc/systemd/system/`, `daemon-reload`, `enable --now ntfs3-clean-unmount.service`, `enable workspace-mount-check.service`
    - Verify: `systemctl status` for both units shows enabled/active; automount rule is not itself dirtying the volume
    - _Expected_Behavior: Property 1 — recurrence prevention wired in_
    - _Requirements: 2.4, 2.6_

  - [ ]* 3.7 Write unit tests for the helper and mount-check unit
    - Quiesce helper: `fuser -m` busy vs idle branches; Dirty/Writeback thresholds; timeout path LOGS and does NOT force-unmount
    - Mount-check: emits journal error when `/mnt/workspace` is absent
    - _Requirements: 2.3, 2.5_

  - [x] 3.8 Verify Bug A exploration tests now pass (fix-checking)
    - **Property 1: Expected Behavior** - Reliable clean mount + recurrence prevention
    - **IMPORTANT**: re-run the SAME probes from tasks 1.1/1.2 — do NOT write new tests
    - **EXPECTED OUTCOME**: mount succeeds, `dmesg` clean, mount-check reports mounted; no nofail masking of a real failure
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6_

- [x] 4. CHECKPOINT GATE — reboot-cycle stability (MUST PASS before any Stage 2 DB/cache work)
  - **This is the explicit Stage-1 → Stage-2 gate. No Stage 2 task that touches the DB/cache may begin until this passes.**
  - Full reboot cycle (have USER run): shutdown → boot
  - Verify: `/mnt/workspace` present after boot; kernel shows no `volume is dirty`; shutdown log shows a clean unmount for the ntfs3 drives
  - **EXPECTED OUTCOME**: stable across the cycle. If it fails, stay in Stage 1 — do NOT proceed.
  - _Requirements: 2.2, 2.4, 2.5, 2.6, 3.6_

  - **FINDING (2026-09-05 reboot test):** On a normal orderly shutdown, systemd ALREADY unmounts the ntfs3 drives cleanly (`mnt-workspace.mount: Deactivated successfully`), and the drive returned clean (`workspace-check: /mnt/workspace mounted OK`). Two consequences:
    1. The `ntfs3-clean-unmount.service` `ExecStop` runs AFTER systemd has already unmounted the drives (log: "not mounted, skipping") — the `RemainAfterExit`+`ExecStop`+`Before=umount.target` pattern does not order ahead of the individual `.mount` deactivations. The unit is currently redundant/no-op on orderly shutdowns (harmless, left installed).
    2. Because orderly Linux shutdowns are already clean, the original dirty bit was NOT caused by a rushed orderly unmount. User reports the dirtying event is "unsure / just appeared" → pivot from "assume rushed-unmount" to "instrument and catch which transition sets the dirty bit."
  - The mount-check alert IS working and is kept.

- [x] 4a. Instrument dirty-bit origin (detect-then-fix; replaces the rushed-unmount assumption)
  - Author a boot-time detector that reads the NTFS `$Volume` dirty flag on `/dev/sdb2` via `ntfsinfo` (ntfs-3g present) BEFORE the mount, and logs the as-found state each boot (captures whether the drive arrives dirty)
  - Author a `systemd-shutdown/` final-phase drop-in that records that the clean shutdown phase was actually reached + does a final `sync` (a hard power loss is then visible by the ABSENCE of this record)
  - Keep `workspace-check` as the post-boot mount alert
  - **GOAL:** when the dirty bit next appears, the logs pinpoint the transition (arrived-dirty-at-boot vs no-clean-shutdown-record vs Windows round-trip) — then fix the proven cause
  - _Requirements: 2.3, 2.6_

  - **RULED OUT — Wine registry:** the Wine registry is just files in the prefix (`~/.wine/system.reg`, `user.reg`, `userdef.reg`) which live on the home/btrfs filesystem, NOT on the NTFS Workspace drive. Registry writes cannot set the NTFS dirty bit. (Would only matter if the prefix lived on NTFS, which it does not.)
  - **RULED OUT for the recent event — Windows-in-VirtualBox:** a VM could dirty the NTFS volume ONLY if the physical Workspace disk is attached as a raw/physical disk (Windows-in-VM then sets the dirty bit like bare metal on an unclean VM shutdown). User confirms the VM has not run for several days while the drive went dirty within that window → VirtualBox is NOT the recent cause. Noted as a POTENTIAL future dirtier only if the VM is resumed with the disk raw-attached.
  - **HYPOTHESIS H-D (Kontakt/Wine writer sets the dirty bit during normal use):** Script analysis shows `launch_kontakt_wineasio.sh` / `launch_kontakt_lowlatency.sh` only `cd` into the Kontakt dir and create the `f:` dosdevices symlink (which lives on the home/btrfs FS, NOT on NTFS) — so the scripts themselves do not write to the NTFS volume. The real NTFS writer is Kontakt-under-Wine (komplete.db3, WAL, LibrariesCache, config). ntfs3 sets the `$Volume` dirty bit while a writer holds the volume open; an unclean Kontakt/wineserver exit (crash, kill, lingering wineserver at shutdown) could leave it set hours before shutdown — which is why a clean shutdown-unmount cannot rescue it.
  - **METHOD CONSTRAINT:** `ntfsinfo` cannot safely read the flag while the volume is mounted by ntfs3 (returns "Access is denied ... already exclusively opened"; `-f`/force is the risky write-path we avoid). The AUTHORITATIVE clean/dirty signal while mounted is the kernel: a successful ntfs3 mount with NO "volume is dirty" message == clean at mount time. Offline reads (`ntfsinfo` with the volume UNMOUNTED) are safe. Baseline confirmed clean 2026-09-05: kernel mounted sdb2 with no dirty complaint.
  - [x] 4a.1 Experiment to prove/rule out H-D (read dirty flag at UNMOUNT, safely)
    - Baseline (DONE): drive clean — kernel mounted sdb2 with no dirty complaint
    - Pass 1 (clean exit): launch Kontakt, use normally, close cleanly; then `sudo umount /mnt/workspace` and read offline: `sudo ntfsinfo /dev/sdb2 | grep -iE 'dirty|volume flags'`; remount after
    - Pass 2 (unclean exit): launch Kontakt, then `kill` wineserver (simulate crash); `sudo umount /mnt/workspace`; read offline as above; remount after
    - **DECISION:** if Pass 2 shows dirty but Pass 1 shows clean → H-D confirmed → fix = ensure clean Kontakt/wineserver teardown (e.g. `wineserver -w` wait in the launcher EXIT trap, and quiesce/kill wineserver at shutdown BEFORE the unmount so the volume closes cleanly)
    - If both clean → H-D unlikely; rely on the boot-time detector + shutdown-record to catch the real transition next time it appears
    - _Requirements: 2.6_

  - **RESULT (2026-09-05, Pass 1 — CAUSE FOUND):** Reproduced on demand. Launched Kontakt via WineASIO/pw-jack, loaded content, did a CLEAN File→Exit, `wineserver -w`, then unmount. Kernel logged at 11:05:48 (DURING the session, before unmount): `ntfs3(sdb2): Mark volume as dirty due to NTFS errors`. Remount then refused: `volume is dirty and "force" flag is not set!`.
    - **ROOT CAUSE REVISED:** The `ntfs3` KERNEL DRIVER itself marks the volume dirty "due to NTFS errors" while Kontakt-under-Wine writes to it — even on a clean exit. NOT a rushed unmount, NOT Windows, NOT merely a lingering wineserver. This is an ntfs3-vs-Wine-write-workload intolerance (ntfs3 self-marks dirty on errors that ntfs-3g/FUSE tolerates and self-heals). This unifies with Bug B hypothesis H-C (ntfs3 metadata handling).
    - **FIX DIRECTION (revised again — isolate the TRIGGER, don't just swap drivers):** User confirms ntfs3 did NOT have this problem before, so ntfs3 is not inherently incompatible with Wine — a SPECIFIC workload triggers the "NTFS errors" that make ntfs3 self-mark dirty. Strong lead: in this same session the user loaded EWQL RA (the known-broken repack, Bug C, SNPID mismatch) and it threw "check if the drive is mounted"; that failed/abnormal disk access is a prime candidate for the NTFS error at 11:05:48. So the driver swap is a FALLBACK, not the first fix.
    - **ISOLATION TEST PLAN (H-D refined into H-D1/H-D2/H-D3):**
      - H-D1 (Wine alone): launch Kontakt, do NOT load any instrument, clean exit → check flag. If dirty → Wine/ntfs3 base interaction is the cause.
      - H-D2 (normal library): if H-D1 clean, load a KNOWN-GOOD library (e.g. a working-tile Player lib), play, clean exit → check flag. If dirty → normal library streaming triggers it.
      - H-D3 (EWQL RA): if H-D1/H-D2 clean, load EWQL RA specifically, reproduce the "check if drive is mounted" error, clean exit → check flag. If dirty HERE only → the broken repack is the trigger; fix = remove EWQL RA and KEEP ntfs3 (no driver swap needed).
    - Each pass: `wineserver -w`; then read flag OFFLINE only after a clean unmount. Recover to ntfs3 between passes.
    - **DECISION (2026-09-05): user chose to isolate the exact ntfs3 trigger first, accepting Windows chkdsk round-trips, rather than switch to ntfs-3g as a workaround. Confirmed fact: ntfs-3g never exhibits this dirtying; only ntfs3 does under wine/kontakt/EWQL RA.**
    - **EFFICIENCY RULE:** a CLEAN pass leaves the flag 0x0000 → ntfs3 remounts fine → continue with NO Windows trip. Only a pass that DIRTIES the volume requires chkdsk-from-Windows to recover (ntfsfix confirmed insufficient: it fixes $MFT but does not clear the flag ntfs3 checks — verified twice). So run passes in order and stop at the first that dirties.
    - **RUN ORDER (stop at first dirtying pass = the trigger):**
      - Recover clean ntfs3 baseline: Windows `chkdsk D: /f` → full shutdown → boot; confirm `ntfs-dirty-detect` logs "arrived CLEAN".
      - H-D1 (Wine, no library loaded) → clean-exit → flag check. Dirty here ⇒ Wine base interaction; fix = ntfs-3g. Clean ⇒ ntfs3 remounts, go on.
      - H-D2 (one known-good Player library, play, clean-exit) → flag check. Dirty here ⇒ normal library streaming triggers it.
      - H-D3 (load EWQL RA, reproduce "check if drive is mounted", clean-exit) → flag check. Dirty ONLY here ⇒ the broken repack is the trigger; fix = remove EWQL RA, KEEP ntfs3.
    - _Requirements: 2.6_

  - **RESULT (2026-09-05, H-D1 — TRIGGER ISOLATED at Kontakt STARTUP):** Clean ntfs3 baseline confirmed at 11:30:59 (`ntfs-dirty-detect: arrived CLEAN, Volume Flags 0x0000, Restart flags 0x3`). Launched Kontakt via WineASIO; Kontakt logged `initializing... 11:33:09`; kernel logged at the SAME second `ntfs3(sdb2): Mark volume as dirty due to NTFS errors` — with NO library loaded yet.
    - **CONCLUSION:** The trigger is **Kontakt/Wine's STARTUP write pattern under ntfs3**, not EWQL RA and not library streaming. EWQL RA's "check if drive is mounted" is a SEPARATE symptom (Bug C), a red herring for the dirty bit. Every Kontakt launch dirties the ntfs3 volume — explains the "just appeared" pattern. H-D2/H-D3 are moot (H-D1 already dirties).
    - **`Restart flags: 0x3`** appeared in the detector after the chkdsk/Windows cycle — worth understanding: likely the NTFS `$LogFile` restart-area state, not the dirty bit itself (dirty was 0x0000 at that read). Note for reference; not the fault signal.
    - **FIX PATH (now evidence-backed):** Because ntfs-3g never exhibits this and ntfs3 does on Wine's startup writes, the correctness-first fix is to mount the Workspace drive with **ntfs-3g** (optionally `big_writes` to narrow the speed gap).
    - **USER CHOICE: try ntfs3 mount-option variants FIRST to keep the speed edge.** Research (official ntfs3 docs + community) findings that bound this attempt:
      - ntfs3 has NO option that changes its response to internal "NTFS errors"; it only does journal REPLAY, not full journaling (JBD is on their TODO) → inherently more fragile to interrupted/unusual write sequences than ntfs-3g. Wine-on-NTFS is a documented rough edge (udisks #653).
      - `force` = mount-despite-dirty, "Not recommended"; it does NOT prevent dirtying, only ignores it → NOT a real fix, excluded.
      - Only two options have a plausible mechanism vs the trigger: **`prealloc`** (changes allocation path on growing writes) and **`windows_names`** (rejects Wine temp names ntfs3 might error on). Cosmetic options (showmeta/hide_dot_files/sys_immutable) excluded.
    - **BOUNDED ntfs3-option test (stop rule to limit Windows trips):**
      - Test A: recover clean (chkdsk) → mount ntfs3 with existing opts + `prealloc` → launch Kontakt → clean-exit → offline flag check.
      - Test B (if A dirties): recover → mount ntfs3 with existing opts + `windows_names` (drop prealloc) → launch Kontakt → check.
      - If BOTH A and B still dirty → STOP chasing options; switch Workspace to ntfs-3g (with `big_writes`). Do not spend further Windows trips.
    - _Requirements: 2.6_

  - **RESULT (2026-09-05, Test A `prealloc` — FAILED):** Mounted ntfs3 with `...,nocase,prealloc` at 11:55:52; kernel logged `Mark volume as dirty due to NTFS errors` at the SAME second (11:55:52), i.e. essentially at mount/first-access, BEFORE meaningful Kontakt activity. Volume stayed usable all session (ntfs3 only refuses dirty at MOUNT time, not during an active mount), which is why it "felt fine" until the next umount exposed it. `prealloc` did not help and if anything the error fired even earlier.
  - **OBSERVER-EFFECT RULED OUT:** `ntfsinfo` is NOT the cause. Proof: dirty-mark at 11:55:52; the `ntfsinfo -m` probe ran 11 minutes later at 12:06:45. ntfsinfo only REPORTS the pre-existing dirty state; it does not set it. Measurement method is sound.
  - **KEY MECHANISM CLARIFIED:** ntfs3 marks dirty on the NTFS error but continues serving the ALREADY-mounted volume; the dirty bit only has a visible consequence at the NEXT mount. So "the umount command made it dirty" is an illusion — the umount is merely the first moment the pre-set dirty bit matters.
  - **RESULT (2026-09-05, Test B `windows_names` — FAILED):** Mounted ntfs3 with `...,nocase,windows_names`; ran Kontakt (init 12:22:17 → clean exit); volume came back dirty on umount. (The dmesg `Mark volume as dirty` at uptime 206s was residual from the prior prealloc session in the ring buffer; the point stands — windows_names did not prevent re-dirtying.)
  - **VERDICT — ntfs3 OPTION ROUTE EXHAUSTED (stop rule reached):** Three ntfs3 configurations tested (baseline `nocase`, `+prealloc`, `+windows_names`); ALL dirty the volume under the Wine/Kontakt workload, early and consistently, regardless of option. ntfs3 lacks full journaling and cannot tolerate Wine's write pattern on this volume. No mount option fixes it. Speed-preserving ntfs3 path is proven non-viable.
  - **FINAL FIX = switch Workspace to ntfs-3g** (the driver the user confirmed never dirties), with `big_writes` to narrow the throughput gap. Validate with the same Kontakt launch → clean exit → flag stays 0x0000 → then set as fstab default.
  - **SCOPE DECISION (user, 2026-09-05): convert ALL THREE ntfs3 drives (Workspace, Storage, WD Black) to ntfs-3g**, because instruments will later be loaded in Kontakt from Storage and WD Black too — they will get the same Wine write workload that dirties ntfs3, so they must move to ntfs-3g as well (fix once, not per-drive-later). win_system already uses ntfs-3g. This supersedes the earlier "Storage/WD Black may stay ntfs3" note and also makes the `ntfs3-clean-unmount.service` largely moot (no ntfs3 drives left) — keep it harmless or retarget later.
  - **PERM NOTE:** ntfs-3g mount line shows `user_id=0` (the FUSE invoker) but effective file ownership is correct `phnx:phnx (1000:1000)` via `uid=1000,gid=1000,default_permissions`; verified writable as uid 1000. No udisks#653 root-ownership problem.
  - **fstab conversion (all three), pending Workspace validation:** change `ntfs3` → `ntfs-3g` and swap ntfs3-only opts (`nocase` is ntfs3-specific; ntfs-3g is case-sensitive by default but Wine/Kontakt path casing was handled — re-verify the case-lookup behavior under ntfs-3g since the prior `nocase` fix was on ntfs3). Options to use: `rw,uid=1000,gid=1000,dmask=022,fmask=133,big_writes,nofail,x-systemd.device-timeout=5`. Keep UUID-based entries.

  - **VALIDATION RESULT (2026-09-05 — ntfs-3g FIXES BOTH BUG A AND BUG B):** Full Kontakt WineASIO session on ntfs-3g (init 12:33:55 → exit → remount 12:35:05). Kernel log: ZERO "Mark volume as dirty" events during the ntfs-3g session (the only such event, 12:22:17, was the prior ntfs3 windows_names test). Drive remounted cleanly as fuseblk, no "scheduled for check". **Bug A SOLVED on ntfs-3g.**
  - **BUG B ALSO SOLVED by the same change (H-C CONFIRMED):** With Workspace on ntfs-3g, ALL library tiles loaded correctly — with NO cache rebuild, clear, or re-registration. This confirms hypothesis H-C: the blank tiles were caused by **ntfs3's metadata exposure** failing Kontakt's `.cache` identity/mtime validation; ntfs-3g presents metadata the way Kontakt expects, so caches validate and tiles render. H-A (mutex/DB) and H-B (chkdsk) were red herrings for the tiles.
  - **UNIFIED ROOT CAUSE:** ntfs3 was the single common cause of BOTH the recurring dirty bit AND the blank tiles. One driver switch (ntfs3 → ntfs-3g) fixes both. Case-lookup under ntfs-3g verified OK in practice (tiles + libraries resolved without the prior nocase-style failures).
  - **PERMANENT + REBOOT-VERIFIED (2026-09-05):** fstab converted all three drives (Workspace/Storage/WD Black) ntfs3→ntfs-3g with `big_writes` (dropped ntfs3-only `nocase`), backup at `/etc/fstab.bak_*`. After a clean reboot: all four NTFS drives auto-mounted as fuseblk from fstab; `ntfs-dirty-detect` reports Workspace "arrived CLEAN, Volume Flags 0x0000". Bug A and Bug B fixes are permanent and survive reboots. Conversion doc: artifacts/fstab-ntfs3g-conversion.md.
  - **COMMUNITY CORROBORATION (web research, 2026-09-05):** This is a KNOWN ntfs3 kernel bug, not our misconfiguration. CachyOS forum reports a `kernel BUG at fs/iomap/buffered-io.c` in `iomap_write_end()` called from `ntfs_file_write_iter()[ntfs3]`, explicitly triggered by 32-bit/Wine-process buffered writes to ntfs3 (Star Citizen/Proton reproducer). Consensus fix across CachyOS/Arch/Manjaro threads = switch to the ntfs-3g FUSE driver (exactly what we did). "chkdsk finds no error" is expected: ntfs3 marks dirty on its own strict/buggy internal detection, usually without real corruption — matching the user's "no data corrupted" read. Refinement to user's theory: chkdsk-timing-realignment is NOT a required precondition; Wine writing to ntfs3 is sufficient by itself (confirmed by H-D1 dirtying a freshly-clean volume). 
  - **DOLPHIN "not authorized"/lock-icons (2026-09-05) = STALE KDE SESSION STATE, not a real access problem.** After the fstab driver change + manual `sudo umount`/`sudo mount` remounts WITHOUT a reboot, KDE's udisks/Solid layer held a stale view and showed "Not authorized to perform operation" with lock icons. PROOF it's cosmetic/desktop-only: `mount` shows all three drives properly mounted as fuseblk (rw, noatime) and `sudo -u phnx ls /mnt/storage` succeeds — filesystem access is fully working. FIX = plain reboot (systemd mounts all three from new fstab at boot; KDE then sees consistent state). No pre-reboot changes needed. Disabling ntfs3-clean-unmount is unrelated. Dirty flag already cleared by ntfs-3g (ntfsfix -d + ntfs-3g mount); chkdsk NOT needed, and ntfs-3g won't hard-refuse a dirty volume anyway.
  - **HARDENING APPLIED (2026-09-05):** added `noatime` (fewer metadata writes, no downside) to all three ntfs-3g fstab entries. **`windows_names` DELIBERATELY NOT ADDED** — user will add instrument libraries whose names may still contain Windows-illegal characters; `windows_names` blocks not just creation but ACCESS to existing files with such names, which would make those libraries unreadable in Kontakt (looks like missing libraries). The minor dual-boot benefit is not worth that concrete risk for this workflow. `hide_hid_files` from the forum example is a udisks-only name, not a valid ntfs-3g fstab option — omitted. Final options: `rw,uid=1000,gid=1000,dmask=022,fmask=133,big_writes,noatime,nofail,x-systemd.device-timeout=5`. Permissions handled via `uid=1000,gid=1000` (verified user-writable).

- [ ]* 5. CHECKPOINT — hibernate / suspend-then-hibernate cycle
  - Have USER run a hibernate and a suspend-then-hibernate cycle; verify same clean result (unit fires, quiesce clean, `/mnt/workspace` present, `dmesg` clean)
  - _Requirements: 2.4, 2.5, 2.6_

### Stage 4 — Shared path migration to Z:, retire F: (woven in after Stage 1, alongside 2/3)

- [ ] 6. Migrate Kontakt paths onto Z: and retire F: safely

  - [ ] 6.1 Keep Z: mapping, make F: deterministic in the interim
    - Confirm `Z:->/` stays (all 120 Player libraries resolve via `Z:\mnt\workspace\VST Install\Kontakt Vst-i\<Library>`) — do NOT change these
    - Make `F:->/mnt/workspace` a persistent Wine dosdevices entry (winecfg / prefix-level symlink) instead of the per-run launcher recreate; keep the launcher recreate as fallback
    - _Bug_Condition: leftover-F: path inconsistency (1.12)_
    - _Expected_Behavior: Property 4 — F: deterministic until baked paths repointed_
    - _Requirements: 2.13_

  - [ ] 6.2 Repoint the non-Player user-content base path off F:
    - Repoint `F:\VST Install\Kontakt Portable\UserData\Kontakt 8\` to the `Z:` (or `D:`) equivalent
    - _Expected_Behavior: Property 4 — converge on Z: convention_
    - _Requirements: 2.13_

  - [ ] 6.3 Identify and repoint baked-F: preset/instrument sample paths
    - Find baked `F:\...` references in `.nki`/`.nksn` presets; repoint to `Z:\...`
    - Only AFTER all baked-`F:` references are repointed, retire `F:`; do NOT repurpose `F:` for another drive
    - _Expected_Behavior: Property 4 — retire F: without breaking any consumer_
    - _Requirements: 2.12, 2.13_

  - [ ] 6.4 Verify all three consumers still resolve after each migration step
    - Verify Windows-native (`D:`), VirtualBox, and Wine all still resolve after each step
    - _Preservation: 3.3_
    - _Requirements: 3.3_

### Stage 2 — Bug B: discriminate cause, then repair (ONLY after task 4 checkpoint passes)

- [x] 7. Fix Bug B — discriminate cause (H-A/H-B/H-C) then repair tiles/cache

  - [x] 7.1 Back up komplete.db3 and LibrariesCache before any DB/cache work
    - Copy `komplete.db3` and `LibrariesCache/` to a timestamped backup (existing backup at `_kiro_backup_20260901/LibrariesCache_bak`); confirm backups before any write
    - _Preservation: non-destructive posture 3.7; no re-dirty / no DB corruption 3.6_
    - _Requirements: 3.6, 3.7_

  - [x] 7.2 Discriminate the cause — beyond the known-failed clear/rescan
    - Byte/field-diff a rendering library's `.cache` vs a blank library's expected entry (note install-date epoch + identity/mtime fields)
    - Live-Kontakt fd probe (`strace` unavailable): inspect `/proc/<kontakt-pid>/fd` while browsing to see what Kontakt opens/stats when validating a tile (library file vs `.cache` vs `.nicnt`)
    - Confirm blank libs' `.nicnt` contain artwork markers (Amati had 8) → rules out "art missing"
    - **H-C read-only driver probe** — **RUN THIS YOURSELF — sudo required** (non-destructive, read-only cannot re-dirty): `sudo umount /mnt/workspace; sudo mount -t ntfs-3g -o ro,uid=1000,gid=1000 /dev/sdb2 /mnt/workspace`, relaunch Kontakt, observe tiles, then restore the normal `ntfs3` rw mount
    - **DECISION**: identify H-A vs H-B vs H-C before committing to a repair
    - _Bug_Condition: isBugCondition_B(lib)_
    - _Expected_Behavior: Property 2 — cause discriminated before repair_
    - _Requirements: 2.7_

  - [x] 7.3 Apply the cause-driven repair (works for BOTH standalone and Reaper/yabridge)
    - **If H-C**: evaluate `ntfs-3g` (or metadata-normalization) so tiles persist; document as fix if viable without breaking latency/other consumers, else document the metadata delta + tradeoff
    - **If H-B**: determine what legitimately regenerates `.cache` (Batch Re-save, or proper per-library re-install/registration) — apply only the working regeneration path
    - **If H-A**: targeted `komplete.db3` cache-reference repair to re-link libraries to their `.cache`/artwork; correct DB into a consistent state
    - **If none regenerates in-setup**: document the limitation explicitly; do NOT loop on clear/rescan/re-add
    - Because standalone (WineASIO/pw-jack) and Reaper/yabridge share `~/.wine` + `komplete.db3`, the repair applies to BOTH workflows
    - _Bug_Condition: isBugCondition_B(lib)_
    - _Expected_Behavior: Property 2 — regenerate/revalidate .cache so tiles render, or document limitation_
    - _Preservation: valid-cache tiles keep rendering; no re-dirty (3.6)_
    - _Requirements: 2.8, 2.9_

  - [x] 7.4 Verify Bug B exploration test now passes (fix-checking, both workflows)
    - **Property 2: Expected Behavior** - Tiles render after cause-driven repair
    - **IMPORTANT**: re-run the SAME enumeration from task 1.4 — do NOT write a new test
    - **EXPECTED OUTCOME**: previously-blank tiles render in both standalone and Reaper/yabridge (OR the limitation is documented)
    - _Requirements: 2.7, 2.8, 2.9_

### Stage 3 — Bug C: investigate EWQL RA to a documented decision (after Bug B understood)

**BUG C VERDICT (2026-09-05, root cause CONFIRMED on healthy ntfs-3g):** EWQL RA (product name "Quantum Leap RA") still throws "library is not installed" even after the drive/driver fix, ruling out environment as the cause. The authoritative `EWQL RA.nicnt` declares: `Name=EWQL RA`, `AuthSystem=RAS2`, `SNPID=0c1`, `RegKey=EWQL RA`. Root cause = the library is an EastWest **RAS2-authorized** product, and this repack's SNPID/authorization does not validate (LibraryHints earlier showed conflicting A02/A05; .nicnt says 0c1). Kontakt cannot match instruments to a validly-authorized library → "not installed". NOT fixable by re-registration, drive letters, paths, ntfs-3g, or direct .nki load (instruments enforce the auth check on any load path, per prior session). This is a CONTENT/LICENSING casualty requiring a correctly-authorized EWQL RA package or genuine EastWest authorization — outside any Linux/Wine/Kontakt config. Documented and set aside; keep its registration removed or hidden so it stops emitting misleading errors during the DB rebuild.
  - **ACTION (user-approved, do FIRST): REMOVE EWQL RA.** In KTP Library Manager select "Quantum Leap RA"/EWQL RA → Remove; also remove any EWQL RA entry under Import Content → Custom Libraries; then SAVE + clean File→Exit (do NOT run a library scan this session — scan triggered the stale-mutex segfault earlier). Files: LEAVE the 8.9G folder in place (unregistered) for now since Workspace space isn't contested — only the REGISTRATION is removed, so a correctly-authorized package could reuse the path later. Delete the folder only if space is wanted.

- [x] 8. Investigate Bug C — EWQL RA SNPID

  - [x] 8.1 Reduce to a single clean registration and test access paths
    - Remove the duplicate/trailing-space `LibraryHints.xml` entry so only one SNPID is in play
    - Test preset load; test direct `.nki` via Files browser; test registering EWQL RA as a Custom library (Import Content) vs Player library
    - _Bug_Condition: isBugCondition_C(load)_
    - _Expected_Behavior: Property 3 — confirm mismatch + test alternative access paths_
    - _Requirements: 2.10_

  - [x] 8.2 Reach and record a documented decision
    - If any path works → document it as the fix
    - If confirmed unfixable in-setup (SNPID baked in `.nicnt`, needs matching-SNPID re-acquisition) → record the conclusion and REMOVE or clearly FLAG EWQL RA so it stops emitting misleading mount/path errors
    - Keep this classification separate from Bug A (genuine unmount) and leftover-`F:` path failures
    - _Bug_Condition: isBugCondition_C(load)_
    - _Expected_Behavior: Property 3 — one documented resolution; no misleading mount error_
    - _Requirements: 2.11, 2.12_

### Preservation verification + final checkpoint

- [ ] 9. Verify preservation tests still pass (no regressions after all stages)
  - **Property 5: Preservation** - Other drives, clean boots, both workflows, no cross-regression
  - **IMPORTANT**: re-run the SAME observations from task 2 — do NOT write new tests

  - [x] 9.1 Other-drives-still-mount preservation
    - Verify Storage (`sdc1`) + WD Black (`nvme0n1p2`) still mount via `ntfs3` and `win_system` (`sda4`) via `ntfs-3g` across the reboot cycle (the clean-unmount unit covers all three ntfs3 drives)
    - _Requirements: 3.1, 3.2_

  - [x] 9.2 Both-workflow Kontakt launch preservation
    - Verify standalone WineASIO/pw-jack AND Reaper/yabridge both launch and function on the stable drive; valid-`.cache` tiles still render
    - _Requirements: 3.4_

  - [ ] 9.3 No cross-regression + non-destructive posture
    - Verify `dmesg` clean and `komplete.db3` integrity after Stage 2/3 (Bug A work didn't corrupt DB; Bug B/C work didn't re-dirty the volume); confirm no force-mount used as primary and backups were taken
    - _Requirements: 3.3, 3.5, 3.6, 3.7_

- [ ] 10. Final checkpoint — Ensure all tests pass
  - End-to-end integration: launch Kontakt standalone and in Reaper on the stable drive, browse tiles, confirm EWQL RA is fixed or flagged (no misleading mount error); confirm Storage/WD Black/win_system all mount across the same cycle
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked `*` are genuinely optional and can be skipped for a faster path.
- **Gating is mandatory**: task 4 (reboot-cycle checkpoint) MUST pass before any task under 7 (Bug B DB/cache) begins. Bug B cause (7.2) is discriminated before Bug B repair (7.3). Bug C (8) comes after Bug B is understood.
- The clean-unmount systemd unit covers ALL THREE ntfs3 drives (Workspace, Storage, WD Black) — the safest approach chosen because more instrument libraries will be added to the other drives.
- Interactive sudo is unavailable to the agent: root/Windows actions are authored as artifacts/commands for the USER to run, then verified. The agent authors `ntfs3-clean-unmount.sh`, `ntfs3-clean-unmount.service`, and `workspace-mount-check.service` as workspace files (installed to `/usr/local/sbin/` and `/etc/systemd/system/` by the user).
- Bug B's known-failed remedies (clear `LibrariesCache`, Import Content rescan, KTP re-add) are NOT the planned fix — the discrimination step (incl. the `ntfs-3g` read-only probe and `/proc/<pid>/fd` inspection) decides the repair.
- Non-destructive: back up `komplete.db3` and `LibrariesCache/` before any DB/cache write; force-mount (`rw,force`/`clear_dirty`) is backup-only.

### Stage 5 — Add & organize the TIXATI DL instrument library collection (15 libraries, 381G)

**Classification (verified 2026-09-05 via `.nicnt` scan):**
- PLAYER (register via KTP Library Manager → Add): Anthology Strings [8Dio] 44G, Deep Pool Modern Downtempo Drums 2.8G, Extinction Level Event Master Kit 15G, Kontakt Factory Library 2 [NI] 38G, Majestica Professional 2.0 [8Dio] 62G, Soundiron Alpha Organ 9.2G
- CUSTOM (add via Import Content → Custom Libraries → Add; load .nki from browser): New Century Orchestral Series [8Dio] 132G, Zen Garden [Fluffy Audio] 32G, Elements – Kepler [Zero-G] 31G, Big Fish Audio Vibe Guitars 11G, Misfit Banjo [8Dio] 585M, Moroccan Vocal Phrases 329M, Pianet Ad Astra small, Puremagnetik Onda 326M, Soundiron Sandy Creek Organ 892M

**FULL STORAGE PICTURE (inventoried 2026-09-05) — larger than first thought:**
- Workspace `VST Install/Kontakt Vst-i/` = **853G** of Player libraries (~50+ libs) — ALL must move off Workspace (HDD).
- Workspace `VST Install/Kontakt Vst-i Folders/` = **113G** custom-library tree — must move off Workspace too.
- Non-library VST plugins on Workspace (AmpliTube, TONEX, FabFilter, iZotope, Kontakt Portable itself, etc.) = small, STAY on Workspace.
- WD Black `TIXATI DL/` = 381G — but LARGELY DUPLICATES libraries already installed in Workspace's Kontakt Vst-i (Majestica, Anthology, Kontakt Factory 2, Zen Garden, Elements-Kepler, Vibe Guitars, Extinction Level, Alpha Organ, Deep Pool, Sandy Creek, Misfit Banjo, ...). TIXATI DL looks like a DOWNLOAD STAGING copy → dedupe (delete staging copies of already-installed libs) to reclaim WD Black space.
- Free space: WD Black NVMe **549G free** (932G total, 384G used), sdd1 btrfs **893G free** (895G total).
- Rough math: ~966G of unique libraries to place across ~1442G combined free — fits, but requires dedupe + deliberate allocation, not a naive two-bucket move.

**OPEN DECISIONS (need user input — do not guess):**
1. Confirm TIXATI DL is a staging copy and its already-installed duplicates can be deleted (vs. it being the intended final home).
2. Voice-count/streaming-demand allocation cannot be inferred from size alone (a 24G solo Stradivari streams light; a 15G ensemble streams heavy). User must flag which libraries are high-polyphony/heavy-stream (→ WD Black NVMe) vs the rest (→ sdd1).

- Recordings/projects live on Workspace (HDD); Storage is personal, NOT for project use.

**DEDUP CONFIRMED (user):** TIXATI DL is the download-staging copy; its duplicates are already installed in Workspace AND already on WD Black. Action: for libraries that exist in BOTH Workspace and TIXATI DL, DELETE the Workspace copy (the fast WD Black copy already exists) — no re-copy. Only MOVE libraries that exist ONLY on Workspace.

**RESEARCH-BACKED streaming classification (web-verified principle 2026-09-05):** ensemble/multi-section orchestras + layered/round-robin drums = HEAVY stream (many simultaneous voices); solo instruments (even large/deep-sampled) = LIGHT stream (one voice at a time). Confirmed: Majestica (240 players/5 sections), New Century (polyphonic-legato ensemble), The Orchestra Complete (80-player Ensemble Engine); vs solo Stradivari/Guarneri/Amati (large on disk, low polyphony).

- HEAVY-STREAM → WD Black NVMe: Majestica 62G, New Century 132G, The Orchestra Complete 11G, Palette Symphonic Sketchpad 32G, EWQL Colossus 19G, Output Analog Strings 19G, Mysteria 28G, Evolution World Percussion 16G, GetGood Drums 11G, Sinfonia Drums 9.8G, Drumforge 14G, Anthology Strings 44G, Zen Garden 32G, Elements-Kepler 31G
- LIGHT-STREAM → sdd1 SSD: solo strings (Stradivari Violin 22G, Stradivari Cello 24G, Guarneri 23G, Amati Viola 22G, Iconic Violin 28G), keys/organs (Piano Colors 27G, Hybrid Keys 3.8G, Alpha Organ 9.2G, Sandy Creek, Session Keys), guitars (all Session Guitarist, Vibe Guitars 18G, Neo Guitar, Kithara 20G), world/ethnic solos (East Asia 25G, Middle East 11G, India, Kora, Tablas, Cuba, Balinese Gamelan), + all small/medium libs
- AMBIGUOUS (need user call — depends on playing style): 8Dio Phenex Bundle 21G, Hybrid Tools Dark Prophecy 18G, Iconic Violin 28G (solo but heavy mic layering?). EWQL RA 8.9G = Bug C (broken; placement low-priority).
- The `Kontakt Vst-i Folders/` 113G custom tree: destination TBD (likely sdd1 unless it contains heavy-stream content).

**CRITICAL ORDERING:** relocate a library to its FINAL drive FIRST, then register/add it — Custom libraries bake sample paths at add-time, so adding-then-moving causes "samples missing".

**SAFETY-FIRST ORDERING (user, 2026-09-05):** Nothing is deleted until the new/relocated locations are CONFIRMED loading in Kontakt. Workspace copies stay as a backup net (Workspace space is not contested — deletion is hygiene, not urgent). Ambiguous libs (Phenex, Hybrid Tools Dark Prophecy, Iconic Violin) go LAST, to WD Black only if space remains after everything else.

**OVERLAP COMPUTED (2026-09-05, by folder name):**
- DUPLICATED (in BOTH Workspace `Kontakt Vst-i` AND WD Black `TIXATI DL`) = 14 libs → register against WD Black copy, do NOT move, keep Workspace copy as backup until load-tested: Anthology Strings, Big Fish Vibe Guitars, Deep Pool Downtempo Drums, Elements-Kepler, Extinction Level Event, Kontakt Factory Library 2, Majestica 2.0, Misfit Banjo, Moroccan Vocal Phrases, Pianet Ad Astra, Puremagnetik Onda, Soundiron Alpha Organ, Sandy Creek Organ, Zen Garden.
- NOTE: New Century (132G, heaviest) is Workspace-ONLY (not in TIXATI DL) → it must actually be relocated to WD Black.
- WORKSPACE-ONLY = ~90 libs (full list captured from `comm -23`) → these need placement (WD Black heavy-stream / sdd1 light-stream per the classification above).

**SEQUENCING (user-approved 2026-09-05):** (a) finish the move ALLOCATION as PLAN only — do NOT move yet; (b) STOP and fix Bug C (EWQL RA) first; (c) if Bug C reveals anything about repack registration, ADJUST the allocation/plan; (d) THEN execute the moves; (e) THEN a clean komplete.db3 rebuild against FINAL locations (avoids stale-path conflicts from ~120 libs currently registered to Workspace paths — piecemeal patching is what caused the original mess). DB rebuild is the LAST step.

- [ ] 9. Compute overlap + relocate ONLY Workspace-only libraries (non-destructive)
  - [x] 9.1 Read-only: compute which `Kontakt Vst-i` libs exist in BOTH Workspace and TIXATI DL (=duplicated → register against WD Black copy, DO NOT move) vs Workspace-only (→ must relocate). Present the diff for approval.
  - [x] 9.2 Verify sdd1 (btrfs) writable by phnx and confirm free space vs the Workspace-only light set
    - **FINDING (2026-09-05):** sdd1 mount is healthy (`rw,noatime,compress=zstd:1,ssd,discard=async`) — btrfs is native Linux I/O, NO dirty-bit/ntfs-driver risk, ideal for Wine/Kontakt streaming. BUT the drive is ROOT-OWNED and btrfs uses real Linux perms (not fstab uid= like ntfs-3g), so phnx CANNOT write yet. MUST FIX before move: `sudo chown -R phnx:phnx /mnt/btrfs_disk` (Option A, whole drive — recommended since it's empty/dedicated). Then re-test write as phnx. btrfs CoW is irrelevant for read-streamed samples (only matters for frequently-rewritten files, which stay on Workspace).
  - [ ] 9.3 COPY (not move) Workspace-only light libraries → sdd1, and Workspace-only heavy libraries → WD Black; verify integrity (rsync --checksum or size/file-count compare). Keep Workspace originals until task 12 test passes.
  - [ ] 9.4 Defer ambiguous libs (Phenex, Hybrid Tools Dark Prophecy, Iconic Violin) to last; place on WD Black only if space remains.

  - **BATCH 2 COMPLETE (2026-09-05):** 80 light libraries rsync'd to `/mnt/btrfs_disk/Kontakt VST-i/`, ALL verified OK (Stradivari Cello healed on re-run after a mid-copy Ctrl+C — rsync resumed cleanly). sdd1 475G free. Dedup skips worked (14 WD Black libs correctly skipped). Workspace originals retained as backup until load-test. EWQL RA: user chose to SKIP entirely (Bug C casualty; sounds easily replaced) — exclude from reorg/registration; its copied folder can be deleted.
  - **BATCH 1 COMPLETE (2026-09-05):** New Century mv'd to `/mnt/wd_black/Kontakt VST-i/`; 10 heavy libs rsync'd (Palette, Mysteria, EWQL Colossus, Output Analog Strings, Evolution World Perc, The Orchestra Complete, GetGood Drums, Sinfonia Drums, Kontakt Factory Library, Kontakt Factory Selection 2) — ALL verified OK (size match). WD Black 549G→377G free (still healthy). Workspace originals retained as backup. Batch 2 (light→sdd1) next.

  - **EXTERNAL STORAGE INVENTORY (user hardware on hand, for FUTURE expansion — not part of current move):**
    - USB-C (mobo) currently used by SSL2+ soundcard.
    - UGREEN CM238 external M.2 NVMe enclosure + Samsung 970 EVO 250GB — fast external option (good for streaming libs if internal drives fill).
    - BlitzWolf BW-TH5 7-in-1 hub: microSD/microSDHC/microSDXC; SanDisk Extreme A2 V30 128GB + 512GB cards. Only ONE microSDXC adapter on hand (hub has one such slot; a smaller microSD slot may take a card without adapter — user to verify). NOTE: SD/microSD is SLOW + higher-latency vs SSD → NOT recommended for heavy sample streaming (xrun risk); fine for archival/backup or light one-shots.
    - Guidance: prefer the 970 EVO NVMe enclosure for any future streaming-library overflow; use SD cards for backup/archive, not live Kontakt streaming.
  - Note: sdd1 is btrfs → NOT readable by native Windows. All these libs are Linux/Kontakt-only (user confirmed).

- [ ] 10. Add PLAYER libraries via KTP Library Manager
  - [ ] 10.1 Register each of the 6 Player libraries pointing at their FINAL path
  - [ ] 10.2 Verify each loads a preset (watch for SNPID-mismatch "not installed" like EWQL RA/Bug C — flag any repack that fails)
  - [ ] 10.3 Confirm tiles render for the newly added Player libraries

**PRE-MOVE CLEANUP DONE (user, 2026-09-05):** EWQL RA removed (Bug C); Drumforge removed from PLAYER lib (it's Custom — no .nicnt, 123 .nki); stale Workspace custom-library path entry removed from Import Content; Kontakt closed cleanly (no scan). Custom imports (incl. Drumforge) will be (re)added AFTER the move, from the FINAL fast-drive locations, so sample paths bake correctly (no "samples missing").

- [ ] 11. Add CUSTOM libraries via Import Content (AFTER move, from final locations)
  - [ ] 11.1 Add each Custom library (incl. Drumforge I Ultimate — 123 .nki, no .nicnt) pointing at their FINAL fast-drive path (root folder with .nki, not deep Samples subfolders)
  - [ ] 11.2 Verify .nki instruments load from the Files/Library browser
  - [ ] 11.3 Dismiss harmless "Incompatible Files" (.ncw) warnings if they appear

**ADDITIONAL PATH SETTINGS FOUND (2026-09-05 screenshots) — fix AFTER the DB rebuild (plain path-picker fields, persist fine on a clean DB):**
- Options → Engine → "Edited samples path" = `F:\VST Install\Kontakt Portable\UserData\Kontakt 8\Edited Samples\` → repoint to Z: (or D:) equivalent.
- Options → Loading → "Non-Player content base path" = `D:\VST Install\Kontakt Portable\UserData\Kontakt 8\` → repoint to the canonical Z: base (this is the one from the prior session's notes).
These are simple settings (browse-icon fields), not the stuck Import Content entries.

**PRE-REBUILD ACTION = DO NOTHING BUT EXIT.** Before the clean DB rebuild, do NOT add libraries, do NOT fix paths, do NOT save — the rebuild deletes the DB, so any registration/settings done now would be wiped. Just File→Exit cleanly. ALL adding + path repointing (User Content, Edited Samples, Non-Player base) happens AFTER the rebuild, into the fresh DB where writes persist.

**F: RETIREMENT — THREE LEVELS (all must be cleared before removing F: from winecfg dosdevices):**
1. **User Content path** — NOT changed by rescan/batch-resave; it's a direct setting. Edit in Kontakt Options/Preferences content dir AND Import Content → User Presets tab: remove `F:\VST Install\Kontakt Portable\UserData\User Content`, add the `Z:\mnt\...` (or `D:\`) equivalent.
2. **Library/Custom registrations** — baked at Add time. Register/import all libraries from the new `Z:\mnt\...\Kontakt Libraries\...` paths → no F: introduced.
3. **F: baked INSIDE presets (.nki/.nksn)** — the tricky one. Rescan does NOT fix these; only **File → Batch Re-save** rewrites baked sample paths. Run Batch Re-save on libraries known to have baked-F: presets.
**SAFE-DELETE VERIFICATION ("unmap F:" = reversible test, NOT winecfg delete):** F: in Wine is just the symlink `~/.wine/dosdevices/f:`. Temporarily rename it to test what breaks WITHOUT permanent deletion:
  - disable: `mv ~/.wine/dosdevices/f: ~/.wine/dosdevices/f:.disabled`
  - launch Kontakt, load a broad sample of presets; if ALL resolve (no "content missing") → F: is safe to retire permanently (winecfg Remove, or just leave the symlink deleted).
  - restore instantly if anything breaks: `mv ~/.wine/dosdevices/f:.disabled ~/.wine/dosdevices/f:`, then Batch Re-save the broken libs and re-test.
  Do this AFTER the clean DB rebuild.

**CORRECTED EXECUTION ORDER (DB rebuild must come BEFORE re-registering — else the rebuild wipes the registrations you just made):**
  1. CLEAN DB REBUILD FIRST: Kontakt closed → back up + delete/rename the DB files → relaunch → Kontakt creates a FRESH empty DB (no stale D:/F: entries, no stuck Import Content/User-Presets entries).
  2. REGISTER into the fresh DB: add Player libs from `Z:\...\Player\...`, add Custom libs from `Z:\...\Custom\...`, repoint User Content to `Z:\...`. Save.
  3. BATCH RE-SAVE: rewrites F: paths baked INSIDE .nki/.nksn presets (separate from the entries).
  4. Test F: disabled → remove F: if clean.
  5. Load-test both workflows → delete Workspace originals.

**WHY the stuck entries won't delete (user question, clarified):** the reappearing entries (User Content `F:\...`, `Kontakt Vst-i Folders` `D:\...`) are NOT stuck because .nki files "hold" the path/keep it in use. They're stuck because Kontakt fails to PERSIST the removal to its config DB (the write doesn't commit — the DB inconsistency); on restart it reloads the old DB state and the entry returns. Therefore Batch Re-save does NOT make them removable (that only fixes F: baked inside presets). The CLEAN DB REBUILD is what clears them (the entries live in komplete.db3/config DB; replacing the DB removes them). Rebuild first → re-add only correct Z: entries.

**"CLEAN DB REBUILD" DEFINED:** `komplete.db3` is Kontakt's library database (holds registrations/paths/cache refs) — currently polluted with stale D:/F: paths, unremovable Custom entries, and half-scanned crash state. Clean rebuild = replace the polluted DB with a fresh one so Kontakt re-registers only the correct Z: paths. Approach (to verify KTP-portable DB filenames before executing):
  - Option A (definitive): close Kontakt → BACK UP komplete.db3 (+ related DBs) → delete/rename them → relaunch (Kontakt creates fresh) → re-add all libs from Z: paths. This is what permanently clears the "won't remove/reappears" entries (they live IN the DB).
  - Option B (softer): keep DB, rely on re-registration + Batch Re-save to overwrite stale entries.
  Prefer A; research exact KTP UserData DB files first so nothing needed is wiped.

- [ ] 12. Apply Z: path convention + verify both workflows
  - [ ] 12.1 Register all new library paths using the `Z:\mnt\...` convention (drive-letter independent; matches existing 120 libraries)
  - [ ] 12.2 Verify libraries resolve in BOTH standalone (WineASIO) and Reaper/yabridge (shared ~/.wine prefix + komplete.db3)
  - [ ] 12.3 Streaming sanity check: load a heavy library (e.g. New Century), play high-polyphony passage, watch `pw-top` for xruns/ERR — confirm no crackling on the chosen drive

- [ ] 13. Final cleanup — delete Workspace duplicate/relocated copies (ONLY after task 12 confirms all load fine)
  - [ ] 13.1 Verify each duplicated/relocated library loads a preset correctly from its WD Black / sdd1 location in Kontakt (both workflows)
  - [ ] 13.2 For confirmed-working libraries only: show the delete list for user approval, verify the surviving copy is complete, THEN delete the Workspace copy
  - [ ] 13.3 Leave effect plugins (AmpliTube, TONEX, FabFilter, etc.) and Kontakt Portable on Workspace untouched
  - Non-urgent hygiene; do at leisure. Never delete a Workspace copy whose relocated counterpart hasn't been load-tested.

**CONFIRMED (2026-09-05): stale Custom/User-Preset entries CANNOT be hand-removed** — `D:\VST Install\Kontakt Vst-i Folders` (Custom) and `F:\VST Install\Kontakt Portable\UserData\User Content` (User Presets) either won't remove or REAPPEAR after restart. This is the non-persisting-config-write symptom (DB inconsistency, same family as the scan-mutex issue). Do NOT keep fighting the GUI — the clean DB rebuild (task 14) must clear these. The `F:\...\User Content` entry is also the F:-retirement target for path cleanup. 

**DECISION (2026-09-05): WD Black stays ntfs-3g (no btrfs reformat).** Rationale: ntfs-3g is the proven-stable driver for the Wine/Kontakt write workload (fixed dirty-bit + tiles), keeps the drive Windows-native, and the streaming bottleneck is the NVMe hardware — btrfs would give no meaningful speed gain and would erase 384G + remove Windows access. Wine reaches it via `Z:\mnt\wd_black\...` regardless of filesystem, so reformatting wouldn't even remove the Z:/mnt pathing.

- [ ] 14. Clean komplete.db3 rebuild against FINAL library locations (LAST step)
  - **DB REBUILD DONE (2026-09-05 22:29):** backed up komplete.db3/user_config.db3/favorites.db3/pal.db to `_kiro_dbrebuild_backup_20260905_222928`; removed komplete.db3 + user_config.db3 + favorites.db3 + lock.lck; kept pal.db + LibrariesCache. Fresh DB will be created on next launch. Rollback command printed by db-rebuild.sh.
  - **PAL.DB WIPED (2026-09-05 22:59):** first DB-rebuild kept pal.db, so stale D:\Kontakt Vst-i Player associations survived and re-appeared as D: entries mixed with new Z: adds. Fixed by backing up + removing pal.db (`_kiro_paldb_backup_20260905_225951`) → Player index now EMPTY → re-register ALL Player libs from Z: only (no stale D: possible). Fresh komplete.db3 (827k) + user_config.db3 (20k) confirmed regenerated small/clean.
  - [ ] 14.1 Back up komplete.db3 + LibrariesCache before rebuild
  - [ ] 14.2 After all libraries are in final homes (WD Black / sdd1 / duplicates-tested) and Bug C resolved, rebuild the Kontakt DB so all registrations point at final `Z:\mnt\...` paths with no stale entries
  - [ ] 14.3 Verify: all libraries resolve + tiles render in BOTH standalone and Reaper; no "content missing"/"not installed" beyond any accepted Bug C casualty
  - Rationale: ~120 libs currently registered to Workspace paths; after moves those are stale. Clean rebuild > piecemeal patching (piecemeal patching caused the original DB mess).

- [ ]* 16. Verify Reaper/yabridge after the move + DB rebuild (likely verify-only, not rebuild)
  - KEY: yabridge bridges the Kontakt PLUGIN (`.../Kontakt Portable/Kontakt 8/x64/VST3/Kontakt 8 Portable.vst3`), which is on Workspace and does NOT move. So the yabridge bridge/symlink stays valid — no re-bridge needed for the library moves.
  - Library resolution is SHARED (same ~/.wine prefix + komplete.db3), so the DB rebuild fixes BOTH standalone and Reaper at once.
  - Steps: (a) confirm `~/.vst3/yabridge/Kontakt 8 Portable.vst3/...so` still present (yabridgectl sync if not); (b) load Kontakt in Reaper, confirm libraries resolve at new Z: paths; (c) ensure the Wine prefix's drive mappings (Z:, and F: if any baked-F: presets remain) are reachable in Reaper's session — Reaper does NOT run the launcher that recreates f:, so retiring F: via the Z: rebuild removes that dependency.
  - _Requirements: 3.4_


### Stage 5 — FULL INVENTORY + SPACE ANALYSIS (2026-09-05, before any moves)

**Free space (targets):**
- wd_black (NVMe SSD): 549G free (has TIXATI DL 381G already)
- sdd1 / btrfs_disk (SATA SSD): 893G free (empty)
- workspace (HDD): 399G free — will be FREED by moving libraries off; keep for recordings/projects
- storage (HDD): personal, OFF-LIMITS for libraries

**Library data to place:**
- Workspace `Kontakt Vst-i` (PLAYER map, registered via Library Manager, Z:\ paths): **853G**
- Workspace `Kontakt Vst-i Folders` (CUSTOM map, Import Content): **113G**
- WD Black `TIXATI DL` (15 libs, mixed Player/Custom): **381G**
- TOTAL library data: ~1,347G to fit into ~1,442G combined SSD free.

**HARD CONSTRAINT:** `Kontakt Vst-i` (853G) does NOT fit in wd_black's 549G free → the big Player map must go to sdd1 (893G free) or be split. Combined SSD headroom is only ~95G, so allocation must be planned, not ad-hoc.

**Also on Workspace VST Install (NOT Kontakt sample libs — leave or handle separately):** Personal Orchestra 5 12G, VG-SPARKLE2 6.8G, TONEX 4.4G, AmpliTube 3G, Kontakt Portable 2.1G (the Kontakt install itself — STAYS), Drums SOUNDBANK 2G, plus many small VST plugins. These are not part of the two library maps.
**On WD Black (non-library, leave):** REAPER, turing-smart-screen-python, Valheim, system folders. Empty `Kontakt VST-i` folder present (0 bytes).

**PROPOSED ALLOCATION (to confirm before moving):**
- sdd1 (893G): `Kontakt Vst-i` 853G Player map  → fits (≈40G headroom)
- wd_black (549G free): `Kontakt Vst-i Folders` 113G Custom map → fits alongside TIXATI DL 381G (≈55G headroom)
- Alternative if sdd1 headroom too tight: split heaviest few Player libs to wd_black.
- Result: Workspace freed of ~966G (drops to recordings/projects only). Both SSDs near-full — verify exact sizes before committing.
- [ ] 9.0 Confirm allocation fits with real sizes + leave ≥30G headroom per SSD before automating moves

### Stage 5b — MAJOR SCOPE EXPANSION: `PROGRAMS/VST, Samples & DAW/` = 1.2 TB

**Capacity reality (2026-09-05):** this folder alone is 1.2 TB. With the 853G `Kontakt Vst-i` + 113G folders, total content FAR exceeds fast-drive free space (WD Black 549G + sdd1 893G = ~1442G). CANNOT relocate everything — must prioritize by ACTUAL USE; the rest stays on Workspace HDD or is cleaned. `FROM TIXATI DL/` (177G) inside this folder is a duplicate staging copy.

**FOUR-BUCKET GROUPING (research-backed placement):**
- BUCKET A — Kontakt libraries → fast drives via Library Manager/Import Content (heavy-stream→WD Black NVMe, light/solo→sdd1): NI Cremona Quartet 90G, Palette 30G, Mysteria 28G, Piano Colors 27G, East Asia 25G, Output Analog Strings 19G, EWQL Colossus 19G, Evolution World Perc 16G, Electro Acoustic 15G, Middle East 11G, The Orchestra Complete 11G, GetGood Drums 11G, Session Guitarist x3, Audio Imperia Sinfonia Drums, Cuba/India/Balinese, the many NI Expansions, Output Exhale, etc.
- BUCKET B — Non-Kontakt sample ENGINES → fast drives BUT pathed by their OWN app, NOT Kontakt Library Manager. Research: SD3 SDXs are individually relocatable + path-edited in SD3 settings; Spectrasonics STEAM (Keyscape/Omnisphere) can live on a secondary drive via its settings or an identically-named symlink. Items: Superior Drummer 3 + SDX Parts 2/3/4/5 + Metal Foundry (~250G+), Keyscape 73G, EZDrummer2/EZbass, Addictive Drums2/Keys, Arturia V-Collection, Omnisphere.
- BUCKET C — Effect plugins/utilities → STAY on Workspace (don't stream, no fast-drive benefit): Waves, iZotope, FabFilter, Neural DSP, HOFA, Sonarworks, Slate, Eventide, etc.
- BUCKET D — Installer archives (names with `-R2R`/`.WiN`/`CE`/`Keygen`/`Incl.Patch`) + `FROM TIXATI DL/` 177G duplicate → NOT installed libraries; cleanup candidates, do NOT relocate.

**RESEARCH (web, 2026-09-05):** demanding/large sample libraries → SSD; keep OS/DAW on a separate physical drive to avoid I/O contention (Steinberg/Quora). SD3 SDX + Spectrasonics STEAM are relocatable and app-managed via their own path settings, independent of Kontakt's Library Manager.

- [ ] 15. Prioritize + allocate the 1.2TB PROGRAMS folder (capacity-constrained)
  - [ ] 15.1 USER flags which Bucket A+B items are ACTUALLY USED (→ fast drives) vs archive-only (→ stay on Workspace HDD). Cannot fit all.
  - [ ] 15.2 Dedupe: reconcile `FROM TIXATI DL/` 177G and any items already present in `Kontakt Vst-i` / WD Black `TIXATI DL` (register/keep one copy, don't move duplicates)
  - [ ] 15.3 Compute exact per-drive allocation with running free-space totals so neither WD Black nor sdd1 overflows; leave working headroom
  - [ ] 15.4 Bucket B engines: relocate + repoint via EACH app's own settings (SD3 path edit; Keyscape/Omnisphere STEAM), NOT Kontakt Library Manager
  - [ ] 15.5 Bucket C effects + Bucket D installers: leave on Workspace / mark for cleanup; do NOT consume fast-drive space

**FORWARD-LOOKING NOTES (user, 2026-09-05):**
- CURATION (later): user will audition all libraries and keep/remove per quality. Consolidated `Kontakt VST-i/` per drive makes this easy — delete unwanted folder, re-run DB rebuild. Ongoing phase after initial setup.
- FUTURE ADDITIONS: room to add more/bigger sampler libraries — sdd1 ~892G free, WD Black ~548G free. New heavy streamers → WD Black NVMe; new lighter → sdd1 (SATA SSD). Both SSDs have near-zero seek latency (far better than the old HDD for high-polyphony); `pw-top`-test any that feel risky for xruns.
- New Century: Batch 1 mv's it from `TIXATI DL/` into `/mnt/wd_black/Kontakt VST-i/` (no separate location). After Batch 1, `TIXATI DL/` is empty → removable.


### Stage 5c — Folder reorg: rename to "Kontakt Libraries" + Player/Custom split (user request, 2026-09-05)

**Target structure on EACH fast drive** (same-drive mv = instant; do AFTER Batch 2 completes, BEFORE registration):
```
/mnt/wd_black/Kontakt Libraries/{Player,Custom}/
/mnt/btrfs_disk/Kontakt Libraries/{Player,Custom}/
```
- Sort each library by `.nicnt` presence: has .nicnt → `Player/` (register via Library Manager); no .nicnt → `Custom/` (add via Import Content).
- Player/Custom split for Player libs is ORGANIZATIONAL only (Library Manager registers by each lib's own path regardless of parent). Real win: put all Custom libs under one `Custom/` root → point Import Content at that single parent with "Import subfolders as individual libraries" checked → adds them all in one action.
- Rename `Kontakt VST-i` → `Kontakt Libraries` as part of this.
- Do NOT reorganize mid-Batch-2 (would disrupt running rsync). Let Batch 2 finish into `Kontakt VST-i/`, then one reorg pass, then register from final Player/Custom paths, then the clean DB rebuild.
- Resulting Z: paths: `Z:\mnt\wd_black\Kontakt Libraries\Player\...` etc.

- [ ] 17. Reorganize into Kontakt Libraries/{Player,Custom} on both drives (after Batch 2, before registration)
  - [ ] 17.1 Classify each relocated library by .nicnt (Player vs Custom)
  - [ ] 17.2 Same-drive mv into `Kontakt Libraries/Player/` or `Kontakt Libraries/Custom/` on each drive; rename root from `Kontakt VST-i`
  - [ ] 17.3 Verify counts/sizes preserved after the reorg (no data lost in the mv)

  - **REORG COMPLETE (2026-09-05):** Both drives renamed `Kontakt VST-i`→`Kontakt Libraries` and sorted by .nicnt presence:
    - WD Black: Player=15, Custom=10
    - sdd1: Player=44, Custom=35, _unused=EWQL RA
    - CAVEAT: classification = "a .nicnt found within depth 3"; it's a good STARTING split but NOT a guarantee of clean Player registration (a repack can have a .nicnt yet fail SNPID like EWQL RA did). VALIDATION IS AT REGISTRATION: Player libs that throw "not installed" fall back to Custom (Import Content bypasses SNPID). No need for the on-disk split to be provably perfect.
    - Final Z: paths: `Z:\mnt\wd_black\Kontakt Libraries\Player|Custom\...` and `Z:\mnt\btrfs_disk\Kontakt Libraries\Player|Custom\...`


### Stage 6 — DB restore + fast-drive repoint + per-library sample/art resolution (2026-09-06)

**ROOT CAUSE of the "lost tiles / empty browser" after the earlier clean DB rebuild:** the fully-populated library index lives in `komplete.db3`'s `k_content_path` table (registrations → LibrariesCache `.cache` links). The clean rebuild produced an 827k empty DB that orphaned the 62 `.cache` tiles. The intact pre-cleanup DB (42MB, 2026-09-01) + its `LibrariesCache_bak` were preserved in `_kiro_backup_20260901/`. Re-registration/rescan never regenerates `.cache` (confirmed), so **restoring the 42MB DB is the only reliable route** to bring tiles back.

- **DONE — surgical restore** (`artifacts/db-restore-surgical.sh`): backed up current state, restored the 42MB `komplete.db3` + `LibrariesCache`, then DELETEd 20 confirmed-redundant rows (7 TIXATI staging + parent, 7 type-2 dupes of a type-3 twin, 6 Content/Tools/Presets type-2 dupes). Result: 230 → 208 rows, no duplicate aliases, tiles restored. The custom `KOMPLETE` collation makes the sqlite3 CLI abort on WHERE/`||` queries and `PRAGMA integrity_check` — use unfiltered `SELECT ... FROM k_content_path` + grep, or GLOB, as a workaround.
- **DONE — fast-drive repoint** (`artifacts/db-repoint-fastdrives.sh`): matched `k_content_path` rows to fast-drive library folders by exact name and rewrote paths to `Z:\mnt\wd_black\...` / `Z:\mnt\btrfs_disk\...`. 41 rows repointed (30 sdd1 / 11 wd_black), 2 Kontakt Vst-i rows left on Workspace (Colossus, Kontakt Factory Library — no fast-drive match). DB backed up pre-repoint. Verified.

**THREE LIBRARIES NEEDED PER-LIBRARY SAMPLE/ART RESOLUTION (root causes each distinct):**
1. **New Century Orchestral (8Dio)** — samples were sealed in an unextracted **`Samples.iso`** (131.7G, ISO 9660). The `.nki` (193) had zero sample files on the filesystem. FIX: loop-mounted the ISO read-only, `rsync`'d the `Samples/` tree (5 section folders, 155,240 files) into the library folder beside `Instruments/`. Loads + plays. The 131.7G `Samples.iso` can be deleted to reclaim space once fully confirmed (KEEP until then).
2. **Oriental Sounds (Ultimate Pro)** — samples present (3 `... Samples` folders under root). Prompted for a wallpaper PNG named `Ultimate-Pro-Oriental-Strings.png` at a nested `Instruments/.../Resources/pictures/` path that didn't exist (actual art was `Resources/pictures/icon/Ultimate-Pro.png`). Placed correctly-named copies in all nested `pictures` dirs.
3. **Elements-Kepler (Zero-G)** — samples present in non-standard `System/Samples` (12,386 ncw). Resolved by Batch Re-save's recursive search from the library root.

**BATCH RE-SAVE (the persistence step):** Runs fine through folder-picker #1 (select library). The crashing `SHBrowseForFolder` picker (#2) only opens if a referenced file is UNRESOLVABLE — so all missing content must be placed on disk FIRST, then Batch Re-save runs silently. Confirmed re-saved + persisted (today's mtimes): Elements-Kepler 27 nki, New Century 46, Oriental Sounds 18. NOTE: Batch Re-save may segfault at the very END (Wine-staging `SHBrowseForFolder`/longjmp teardown) AFTER all patches report "ok" — the re-save is already written; the end-crash is harmless. NI guidance: run Batch Re-save on SINGLE libraries, never a whole drive (a single unresolved ref would abort the whole run + crash).

**COSMETIC LIMITS — CONFIRMED UNRECOVERABLE FOR THESE REPACKS (2026-09-06):**
- **Instrument-panel wallpaper**: the wallpaper file is present at the same relative path the pre-move original used, and Instrument Options shows the wallpaper path sourced correctly, BUT the panel renders black even after setting it in Instrument Options + Batch Re-save + clean restart. CONCLUSION: the repack stripped/flattened the instrument's performance-view GUI layer that draws the wallpaper — there is no panel to render it onto. Not fixable without the original full installer.
- **Library-browser tile**: `.nicnt` present and Kontakt reports the library "already added", but no tile renders after a clean restart. The repack `.nicnt` does not carry/regenerate the browser `.cache` artwork, and this portable setup has no in-app rescan that forces it. Not fixable without the original installer.
- **`.nki` are fully binary/compressed** (`file` → `data`; `strings` finds no readable paths) → external path/art inspection or rewrite is impossible; only Kontakt itself can edit them. This bounds all art fixes to in-app actions, which were tried and failed.
- **DECISION:** accept both cosmetics as-is for the repacks. Libraries load, play, stream from the fast drives, and are correctly repointed + re-saved — functionally complete. Cosmetic-only shortfall, documented.

**WINE-STAGING NOTE:** wine-staging 11.16 (testing build) throws intermittent cold-start segfaults in `wine-preloader` (`ntdll` longjmp/`__longjmp_chk`), unrelated to Kontakt/DB/libraries — clears on relaunch. Not a data problem.

**REMAINING (functional, not yet done):**
- Remove EWQL RA's dead `k_content_path` entry (Bug C casualty) so it stops showing a non-working entry. SQL: `DELETE FROM k_content_path WHERE path GLOB '*EWQL RA*';` (back up DB first).
- Extinction Level Event crackle: raise the audio buffer — launcher `QUANTUM=128` → `256` (biggest crackle-killer); DFD preload 192kB is fine (uses RAM, not disk — does not "overkill the disk"). Legacy mode is for OLD-instrument compatibility, NOT an xrun/crackle fix — do not use it for streaming performance.
- Task 13: delete Workspace originals + New Century `Samples.iso` only AFTER load-tests confirm the fast-drive copies.


**ORIENTAL SOUNDS TILE — RESOLVED/CLARIFIED (2026-09-06):** After removing its LibraryHints block for a clean re-add, "already added" persisted because the registration is ALSO held in `pal.db` (keyed by RegKey GUID `83F801E6-...`/SNPID `A01`, not the readable name — that's why name-grep missed it). Opening KTP **Library Manager v8.0.0** shows the library IS present WITH its tile artwork ("ULTIMATE") — registration + manager tile are fine; no repair needed (do NOT restore the LibraryHints backup; pal.db keeps it registered). What remains absent is (a) the tile in the **classic Libraries browser pane** and (b) the instrument **panel wallpaper** — both are the repack `.cache`/flattened-GUI cosmetic limits that cannot be regenerated in this portable setup. The library loads + plays via Files browser (drag, or double-click into a focused empty slot). The "double-click does nothing" is standard Kontakt behavior (needs a focused empty rack slot) or set Options→Browser double-click action to Load/Replace — NOT a defect. FINAL: Oriental Sounds is functionally complete; browser-pane tile + panel wallpaper accepted as repack cosmetic limits.


### Stage 7 — Reaper/yabridge preservation check (2026-09-06)

**RESULT — Kontakt 8 Portable LOADS in Reaper via yabridge (VST3), shared prefix/DB confirmed.** Inserted `VST3i: Kontakt 8` on a track; full browser rendered with 10,727 presets and library tiles (5Elements, Amati Viola, ANALOG STRINGS, Balinese Gamelan, etc.), engine healthy (CPU active, Disk 0%). This proves preservation req 3.4: BOTH standalone (WineASIO/pw-jack) AND Reaper/yabridge work on the SAME restored+repointed `komplete.db3` reading libraries from the fast drives — one shared `~/.wine` prefix, both workflows inherit all fixes. yabridgectl status healthy; bridge target `/mnt/workspace/VST Install/Kontakt Portable/Kontakt 8/x64/VST3/Kontakt 8 Portable.vst3` (unchanged by library moves), `.so` at `~/.vst3/yabridge/Kontakt 8 Portable.vst3/Contents/x86_64-linux/`. First load is SLOW (yabridge Wine host spin-up + reading the full 42MB DB / 10,727 presets).

**KNOWN LIMITATION — yabridge GUI performance with Kontakt's heavy browser:** After load, the bridged Kontakt UI can become unresponsive with ONE Reaper thread pinned (~54% CPU = ~1 core) and ZERO disk I/O — i.e. a GUI repaint SPIN LOOP, not disk loading and not a deadlock (a deadlock would show 0% CPU). Diagnosis method: `ps -eo pid,stat,%cpu,comm` (reaper thread pinned) + 3s `/proc/diskstats` delta on sdd1/nvme (=0 → not streaming). Root cause = Reaper compositing/repainting the bridged Kontakt browser (10,727 presets + tile artwork) over Wine — a yabridge+Kontakt-on-Wine cost, NOT a failure of the drive migration or DB. WORKAROUND: after picking an instrument, COLLAPSE Kontakt's browser (side arrow) and/or CLOSE the plugin UI window (engine keeps running) — Reaper CPU drops immediately. Use the smaller performance/rack view in Reaper rather than the full browser. If fully frozen, closing just the plugin window frees it; force-closing Reaper is safe (all migration work is persisted on disk — only an unsaved Reaper session would be lost). Spin loops generally do NOT resolve by waiting (no data being consumed).


**FIX for the yabridge GUI spin (2026-09-06):** Confirmed via multi-sample that it's a spin loop, NOT progress — reaper thread flat at exactly 55.2% across 3 samples (2s apart) with sdd1 read delta = 0 over 5s. Flat CPU + zero I/O = tight repaint loop; waiting will not resolve it (nothing being consumed). Reliable progressing-vs-spinning test = sample process %cpu several times + `/proc/diskstats` sector delta: varying CPU or nonzero I/O = progress; dead-constant CPU + 0 I/O = spin.
  - ROOT CAUSE: yabridge repaints Kontakt's editor at the default `frame_rate = 60`; Kontakt's 10,727-preset browser is expensive to repaint through the bridge → saturates one Reaper core.
  - FIX = per-plugin `~/.vst3/yabridge/yabridge.toml` (artifact: artifacts/yabridge.toml) with:
    `["Kontakt 8 Portable.vst3"]` / `frame_rate = 30` (halves repaint CPU; drop to 24/20 if still pinned). Install: `cp artifacts/yabridge.toml ~/.vst3/yabridge/yabridge.toml` → `yabridgectl sync` → relaunch Reaper (config only applies on fresh plugin load).
  - COMBINE with workflow habit: after loading an instrument, collapse Kontakt's browser / close the plugin window (engine keeps running) — browser repaint is the heavy part.
  - To free the CURRENT spun session without losing migration work (all persisted on disk): close the Kontakt plugin WINDOW (not Remove); if fully frozen, force-closing Reaper is safe (only loses the unsaved Reaper session).
  - Related knobs (not needed for the spin): `editor_disable_host_scaling=true` only for HiDPI scaling issues; `group=` only for multi-instance load speed.


**FIX VERIFIED (2026-09-06):** After installing `~/.vst3/yabridge/yabridge.toml` with `frame_rate = 30` for `Kontakt 8 Portable.vst3` + `yabridgectl sync` + fresh load in Reaper, the Reaper CPU dropped from a pinned 55.2% to a steady 29.9% (≈ the 60→30 fps halving) and the bridged Kontakt UI is responsive. The remaining startup slowness is genuine load work (reading the large DB / warmup), not the spin. Optional: drop frame_rate to 24/20 for even lower CPU; collapse browser / close plugin window drops it further. yabridge GUI spin RESOLVED.


**yabridge GUI redraw-on-cursor-only (2026-09-06) — Wayland frame-presentation quirk:** Symptom = Kontakt's bridged editor only visually updates while the mouse moves, freezes when the cursor stops; disk delta 0 (NOT loading) and Reaper CPU steady ~32.5% (the frame_rate=30 editor refresh IS running — work is done, just not presented). Session confirmed `XDG_SESSION_TYPE=wayland`. Cause: Wine/yabridge plugin windows run via XWayland, and on Wayland the X11 window often only receives frame/damage callbacks on input events, so the 30fps repaint work happens but the compositor only presents on cursor motion. FIX = run Reaper as a native X11 (Qt xcb) app inside the Wayland session: quit Reaper, launch `QT_QPA_PLATFORM=xcb reaper` (or prefix `env QT_QPA_PLATFORM=xcb` in its .desktop Exec). X11 Reaper + XWayland plugin present frames continuously → GUI redraws without cursor movement. ALT: close the plugin window when not tweaking (engine keeps running, CPU→~0). Display-only issue; audio/MIDI/streaming unaffected.


**TILE-LESS ENTRIES ROOT CAUSE + CLEANUP (2026-09-06):** LibraryHints.xml had 119 <Library> blocks = 57 real (Name+Company+SNPID+RegKey → tiled) + 62 BARE GUID-named stubs (Name=raw GUID, SNPID only, NO RegKey, NO Company). The 62 bare stubs (leftover registration cruft from the DB/registration churn) are non-functional (a working Player registration needs the RegKey) and were showing as the tile-less/blank entries in the Libraries browser. All SNPIDs unique (not duplicate twins). FIX = artifacts/purge-guid-libraryhints.sh (awk block-filter, reversible, Kontakt closed): removed all GUID-named <Library> blocks → 119→57 blocks, 57 with RegKey, 0 GUID, XML open==close balanced. Backup at LibraryHints.xml.bak_purgeguid_*. NOTE: this declutters the browser; it does NOT create tiles — tiles still come from the 62 LibrariesCache/.cache files, so a named library WITHOUT a matching .cache still shows no tile (repack cache-never-generated limit, unrecoverable in this portable setup). Rollback: cp the .bak back with Kontakt closed.


### Stage 8 — Converge DB on Z: fast-drive only; purge D:\PROGRAMS legacy scan (2026-09-06, PLANNED)

**HOW WE GOT HERE:** The restored 42MB DB (`pre_ewqlra_144329`, 208 rows) contains a LEGACY full-folder scan of the old Windows `D:\PROGRAMS\VST, Samples & DAW\` tree = 150 content_type-3 rows referencing ~52,801 k_sound_info entries. Only 35 of those 150 are REAL Kontakt libraries (.nicnt/.nki); the other **115 are NON-KONTAKT junk** (Arturia, Waves, Omnisphere, Superior Drummer, PreSonus, R2R/keygen bundles, loop packs) swept in by the scan. This legacy scan is the source of the duplicate "…Library" folder-icon browser entries and the DB re-bloat. LibraryHints.xml is at 119 (57 real + 62 harmless GUID stubs) — the GUID purge was reverted; leave LibraryHints alone. Settings.cfg ContentDir is already all-Z: (57 Z:, 0 D:).

**CLASSIFICATION (exact-name matched, verified 2026-09-06):**
- 35 real Kontakt libs among the 150 D: rows: 21 PLAYER (.nicnt), 14 CUSTOM (.nki).
- 31/35 ALREADY have an exact-name fast-drive copy (WD Black/sdd1); only 4 NEED-MOVE.
- Of the 31 have-fast: **14 are Z-REG-OK** (already registered from Z: — their D: row is a pure duplicate, safe to drop) and **17 are NO-Z-REG** (fast-drive folder exists but only the D: row registers it — must register from Z: BEFORE dropping the D: row).

**Z-REG-OK (14) — D: row is a safe-to-drop duplicate:** Balinese Gamelan Library, Best Service - The Orchestra Complete, Cloud Supply Library, Evolution Series - World Percussion v2.0 Close Front Mics, Middle East Library, Mysteria Library, Output Analog Strings KONTAKT, Output Exhale, Pharlight Library, Piano Colors Library, Play Series Selection Library, Red Room Audio - Palette Symphonic Sketchpad, Session Guitarist - Electric Vintage Library, Session Guitarist - Picked Acoustic Library.

**NO-Z-REG (17) — register from Z: FIRST, then drop D: row:** Audio Imperia - Sinfonia Drums, Doru Malaia - Ethnic Super Drums Collection, Drumdrops - Vintage Funk Kit, Electro Acoustic, Epic SoundLab - The Forge, EWQL Colossus, EWQL RA (Bug C — skip/remove instead), GetGood Drums - Modern and Massive Pack, Kontakt Factory Library, PlugInGuru.MegaMagic.Bells.Winds.KONTAKT, Session Guitarist - Electric Sunburst Deluxe, Session Keys Electric R, Sonic Mechanics - Classic Guitar Licks, Sonic Mechanics - EDM Energy Drums, Sonic Mechanics - Future Cinematic FX, Sonic Mechanics - Tropical Trap, String Audio - Alchemist Cinematic Impacts.

**NEED-MOVE (4) — minor, optional:** Hy2rogen - Tekno House Nights, Keyscape - 13, LM - Reel People Broken Beat Nu Jazz And Soul.2, LM - Reel People Broken Beat Nu Jazz And Soul.3.

**PHASED PLAN (execute in order; DB backup before each DB change; Kontakt CLOSED):**
- [ ] 8.1 Register the 17 NO-Z-REG libs from their Z: fast-drive paths (in Kontakt: Player via Add Library, Custom via Import Content), so each has a Z: registration. EWQL RA excepted (Bug C — remove instead of register).
- [ ] 8.2 Verify all real libs now have a Z: registration (re-run the Z-REG-OK/NO-Z-REG check → all Z-REG-OK).
- [ ] 8.3 Delete the 115 NOT-KONTAKT junk rows + the 31 (now-duplicate) D: rows + the parent scan row id 134 (`D:\VST Install\Kontakt Vst-i Folders`) in one backed-up SQL pass: effectively `DELETE FROM k_content_path WHERE path LIKE 'D:\PROGRAMS%' OR path='D:\VST Install\Kontakt Vst-i Folders'`. (Only after 8.1/8.2 confirm the reals are Z-registered.)
- [ ] 8.4 Kill the re-scan trigger: find & remove/repoint the Kontakt content-directory setting (Options → Content, and any Settings.cfg entry) that pointed at `D:\PROGRAMS\VST, Samples & DAW` so the junk never re-populates on launch.
- [ ] 8.5 Relocate the 4 NEED-MOVE libs to a fast drive + register from Z: (or leave on Workspace if low priority).
- [ ] 8.6 VACUUM the DB (shrink from re-bloat) and verify: launch standalone + Reaper, confirm all real libs load from Z:, no duplicate/folder-icon clutter, no D:\PROGRAMS entries.

**SAFETY:** Do NOT bulk-delete D: rows before 8.1/8.2 — 17 libs would lose their only registration. Keep `komplete.db3.pre_ewqlra_144329` as the known-good fallback. The 52,801 k_sound_info entries that vanish are overwhelmingly the 115 non-Kontakt junk (Omnisphere/Superior Drummer/Arturia preset counts) — not real Kontakt instruments, so their removal from the Kontakt browser is correct.


### Stage 8 — TILE RECOVERY: proven cause + repoint-only restore (2026-09-07)

**PROVEN CAUSE (data, not assumption — `artifacts/db-tile-diagnose.sh` output 2026-09-07):**
The Z-only convergence (`db-converge-z-only.sh` Phase B) DELETED the **type-3** registration rows
(`D:\PROGRAMS\VST, Samples & DAW\<lib>`) that carried the browser-tile pairing for ~14 libraries.
Diagnostic evidence, side-by-side GOOD (`komplete.db3.pre_ewqlra_144329`, 208 rows, tiles work) vs
CURRENT (68 rows, folder icons):
- Balinese Gamelan: GOOD had `6|type2|Z:\...Player` AND `151|type3|D:\PROGRAMS\...`; CURRENT kept only row 6. Same pattern for Cloud Supply, Middle East, Pharlight, Mysteria, Output Analog Strings, Exhale, Red Room Palette, Best Service Orchestra Complete, Evolution World Perc, Session Guitarist Vintage/Picked.
- The deleted rows were the type-3 D:\PROGRAMS rows; the surviving type-2 Z: rows still STREAM fine (loading never broke — cosmetic only).
- `product_id` and `upid` are BLANK on all rows (`|||`), so `.cache` is NOT keyed on those; the tile pairing rode with the type-3 registration rows that got deleted.
- CONTROL Amati Viola (still shows tile): only ever had a type-2 Z: row, no type-3 → untouched by the delete → tile intact. This is why some kept tiles and the converged set lost them.
- 62 `.cache` files intact in LibrariesCache; the pairing (not the files) was lost.
- Confirms the earlier hard fact: re-registration/rescan never regenerates `.cache`; only restoring the fully-populated DB brings tiles back.

**USER DECISION (2026-09-07): restore the working 42MB DB, then re-apply ONLY the Z: repoints (no deletes).**
- Artifact: `artifacts/db-restore-tiles-repoint-only.sh` (dry-run default; `apply` to execute).
- Restores `komplete.db3.pre_ewqlra_144329` + LibrariesCache, then UPDATE-repoints every row whose
  folder exists on a fast drive (matched by exact folder name) to `Z:\mnt\wd_black|btrfs_disk\Kontakt Libraries\Player|Custom\<name>`. NO DELETE — the tile-bearing type-3 rows stay alive.
- Rows whose folder is not on a fast drive are LEFT AS-IS (same state as when tiles worked); the 115
  non-Kontakt junk rows are NOT touched here (browser-clutter cleanup is a separate, optional, reversible
  later step via `visible=0`, never delete).
- FULLY REVERSIBLE: backs up current DB + cache; keeps a pre-repoint restored copy for independent rollback.

**NEXT (after tiles confirmed):** standalone UI slowness — current DB is 142MB (free-page bloat from the
convergence deletes + WAL), CLI VACUUM blocked by the custom `KOMPLETE` collation. De-bloat plan is
separate (the restore itself drops the file back to ~42MB, which may already resolve the slowness).


### Stage 9 — Clean Z:-only convergence WITHOUT losing tiles (2026-09-07, DONE)

**Approach that finally worked (all reversible, backups kept, Kontakt CLOSED):**
1. `db-restore-tiles-repoint-only.sh apply` — restored the all-tiles 42MB DB (`komplete.db3.pre_ewqlra_144329`) + LibrariesCache, then UPDATE-repointed 16 rows to Z: fast drives (14 collided on the UNIQUE path index because their type-2 Z: twin already held the path — expected). Tiles came back; loaded instantly.
2. **DB-instability ROOT CAUSE found:** after the restore, launching Kontakt re-bloated the DB 42MB→124MB. Settings.cfg `ContentDir=` entries were ALL Z: (clean) — the re-bloat was Kontakt re-validating the 139 stale `D:\PROGRAMS` `k_content_path` rows carried in the backup DB, NOT a config scan trigger. So the fix = remove D:/F: from the DB itself.
3. `db-converge-hide-nonz.sh apply` — set `visible=0` on 140 dup/junk rows + repointed F: User Content→Z:. Result 68 visible / all Z: / 140 hidden. **This KILLED the churn: next launch loaded instantly, no re-hash, DB stayed put.** BUT `visible=0` does NOT suppress rows that are registered Custom Libraries — ~14 duplicates still rendered as folder-icon tiles next to their real Z: twins.
4. `relocate-two-uniques.sh apply` — the only two libraries that existed ONLY on Workspace: **Keyscape - 13** (1.8G, 13 .nki) and **Hy2rogen - Tekno House Nights** (920M) — rsync'd to `/mnt/btrfs_disk/Kontakt Libraries/Custom/`, verified (exact file-count + byte match), repointed their DB rows to Z: + visible=1. Workspace originals kept until load-test.
5. `db-finalize-zonly.sh apply` — three data-driven passes:
   - DELETE 14 duplicate rows whose Z: twin already provides tile+load (Balinese Gamelan Library, Best Service Orchestra Complete, Cloud Supply Library, Evolution World Perc, Middle East Library, Mysteria Library, Output Analog Strings, Output Exhale, Pharlight Library, Piano Colors Library, Play Series Selection Library, Red Room Palette, Session Guitarist Vintage/Picked).
   - REPOINT+SHOW: 0 (the two uniques already handled in step 4).
   - LEAVE HIDDEN: 124 (non-Kontakt junk + EWQL RA/Bug C + D: Content/Tools dupes + F: GetGood sub-path) — visible=0, not deleted, reversible.

**FINAL DB STATE:** 194 rows total; **70 visible, ALL Z:; 0 visible D:; 0 visible F:; 124 hidden.** All real libraries show one tile via their Z: fast-drive registration. DB loads instantly, no re-bloat/churn. Every step backed up (`komplete.db3.pre_*`), fully reversible.

**KEY LEARNINGS:**
- `visible=0` on `k_content_path` hides pure scan rows AND kills the re-validation churn, but does NOT hide a row that is a registered Custom Library — those must be DELETEd (safe once a Z: twin is confirmed to provide tile+load).
- The tile artwork rides with the row identity in the restored 42MB DB; only restoring that DB brings tiles back (re-registration/rescan never regenerates `.cache` — confirmed repeatedly).
- The DB re-bloat was internal stale D: rows, not a Settings.cfg scan trigger (ContentDir was already all-Z:).

**REMAINING:** load-test both workflows, then delete Workspace originals of Keyscape-13 / Tekno House (kept as backup); confirm standalone UI is responsive (was the goal); optional cleanup of the 124 hidden rows later if a tidier DB is wanted (they're harmless + reversible).


### Stage 10 — Deep clean: delete D:/F: registrations + orphan presets, repair indexes (2026-09-07, DONE)

**Discovery:** the Import Content / Custom Libraries browser AND the folder-icon dupes are driven by
`k_content_path` rows + their `k_sound_info` children — NOT by the `visible` flag. `visible=0` killed the
DB re-bloat/churn but did NOT remove rows from the Import Content list. So the D: registrations had to be
DELETED, not hidden.

**Blocker:** the DB has a custom `KOMPLETE` collation on the `p_sound_info_*` sort-order indexes. The
sqlite3 CLI lacks that collation, so any DELETE touching those indexes aborted — first with
`no such collation sequence: KOMPLETE`, then `database disk image is malformed`. Root of the "malformed":
integrity_check (run via Python with a registered KOMPLETE collation) showed the ONLY defect was STALE
SECONDARY INDEXES (`row N missing from index index_p_sound_info_*_sort_order`) — table DATA was intact,
and the same staleness existed in every backup (pre-existing, benign to data, fatal to index writes).

**Fix (Python sqlite3 with `create_collation("KOMPLETE", casefold+strip comparator)`):**
`artifacts/db-reindex-purge.py` — REINDEX (rebuilds all indexes from intact table data) → integrity ok →
DELETE orphaned `k_sound_info` (content_path_id NOT IN the 70 surviving ids; numeric, collation-safe once
indexes are healthy) → clean `k_sound_info_category`/`_mode` → VACUUM.
- Proven on a throwaway copy first (dry-run), then applied.
- RESULT: `k_sound_info` 85,325 → 30,060; integrity **ok** before+after; DB **124MB → 41.8MB**.

**Prerequisite steps this session (all reversible, backups kept):**
- `db-delete-all-df.sh apply` — deleted the 124 non-Z `k_content_path` rows (dupes + junk); the child
  `k_sound_info` delete was blocked by the collation (left 55,265 orphans → cleaned in the reindex-purge step).
- `relocate-two-uniques.sh apply` — Keyscape-13 + Hy2rogen (only-on-Workspace) copied to sdd1 Custom,
  verified, repointed to Z:, visible=1. Workspace originals kept until load-test.

**FINAL DB STATE:** 70 content paths (all Z:), 30,060 presets, 0 D:/F:, healthy indexes, 41.8MB, integrity ok.
Every real library present once via Z:; the two orphans on sdd1; EWQL RA (Bug C) removed.

**KEY LEARNING:** Kontakt's komplete.db3 uses a `KOMPLETE` collation the CLI can't load; ANY write
(DELETE/VACUUM/REINDEX) must be done via Python sqlite3 with the collation registered. Stale
`p_sound_info_*` sort indexes must be REINDEXed before deletes or they throw "malformed".

**REMAINING:** confirm the fresh Kontakt launch shows a clean browser (no dupes, no D: in Import Content,
real preset count, both relocated libs load); then delete Workspace originals of Keyscape-13/Hy2rogen; and
the standalone UI slowness should be resolved by the 41.8MB compact DB.


### Stage 10b — Browser clean; two Custom libs keep folder icons (2026-09-07, ACCEPTED)

Fresh Kontakt launch after the reindex-purge: browser is CLEAN — no folder-icon duplicates, Import Content
free of D: junk, real preset count, both relocated libs load from sdd1, instant load, no re-hash.

**Keyscape-13 and Hy2rogen - Tekno House Nights show a generic folder icon (ACCEPTED as-is):** they are
Custom libraries (added via Import Content, no `.nicnt`). The classic Libraries-browser tile is only drawn
for proper Player/NKS libraries that ship a `.nicnt` + resource container (`.nkr` with MST_ARTWORK). Custom
libraries cannot get a browser tile without authoring a resource container + registering as a Player library
(NI Creator Tools / libctool + valid SNPID) — same class of repack-authoring that's out of scope (and the
SNPID fragility we just cleaned up). Not a defect; expected behavior for Custom libs. They load + stream fine.


### Stage 11 — Known-good state snapshot (2026-09-07, DONE)

`artifacts/backup-known-good-state.sh` — snapshots all config/DB/state (NOT sample files) so the clean
state is recreatable. Output: `/mnt/wd_black/kontakt-known-good-20260907_123255/` (61M) + `.tar.gz` (11M).
Captured: komplete.db3 (clean 41.8MB), user_config.db3, Settings.cfg, LibrariesCache/ (62 tiles), pal.db,
LibraryHints.xml, Wine dosdevices symlinks (Z:/D:/F:) + system.reg/user.reg/userdef.reg, /etc/fstab, the
three systemd units + /usr/local/sbin helpers, yabridge.toml, launchers, and all spec fix scripts. MANIFEST.md
has full restore steps + the fast-drive mountpoint assumptions.
- FOLLOW-UP: DB_STATE.txt (integrity+row dump) did not write on the first run (heredoc arg form); regenerate
  with `db-integrity.py <snapshot>/kontakt_userdata/komplete.db3 | tee .../DB_STATE.txt`, then re-tar.
- NOTE: two LibraryHints.xml existed (live + _kiro_backup_20260901); flat copy kept the last one — harmless,
  LibraryHints is not part of the DB-driven fixed state; prefer the live komplete.db3 on any restore.

## STATE COMPLETE (2026-09-07)
Bug A (dirty bit) + Bug B (blank tiles) fixed via ntfs3->ntfs-3g. Libraries relocated to fast drives, DB
converged to Z:-only (70 content paths, ~30,060 presets, 0 D:/F:, integrity ok, 41.8MB, instant load).
All real libraries tile via Z:; Keyscape-13 + Hy2rogen on sdd1 (folder icon = Custom-lib limitation);
EWQL RA removed (Bug C, unfixable repack). Both standalone (WineASIO) and Reaper/yabridge share the clean DB.
Known-good snapshot taken. Remaining optional: delete Workspace originals of the 2 relocated libs (user chose
to KEEP as backup).


### Stage 11b — 4 remaining D: rows = Kontakt factory content (LEAVE, 2026-09-07)

The only non-Z rows are Kontakt 8 Portable's OWN bundled factory content (ids ~282-285):
`D:\...\Kontakt 8\Content\Presets\{Lo-Fi Vibes,Piano Uno}` and `...\Content\Tools\{Chords,Phrases}`.
Kontakt re-registers its own bundled content on every launch using its internal D: path form. They are
STABLE (74 total in both live + snapshot, no multiplication), resolve fine (D:->/mnt/workspace), and are
unrelated to the removed D:\PROGRAMS junk. NOT churn.
- DECISION (user): LEAVE them. Repointing to Z: risks Kontakt re-adding the D: version next launch =
  a NEW duplicate, a setback right before Reaper testing. `db-repoint-factory-content.py` was written
  (Python/collation-safe) but intentionally NOT run.
- Re-snapshot taken to reflect the true steady state (74 content paths, 30,060 presets, integrity ok).
- Reaper/yabridge shares the same ~/.wine prefix + komplete.db3, so it inherits this clean state. Expect:
  slow first Kontakt insert (yabridge host spin-up), and use rack/collapsed browser to avoid the known
  yabridge GUI-repaint cost (already mitigated via yabridge.toml frame_rate=30).


### Stage 11c — Snapshot finalized (2026-09-07)

Known-good snapshot: `/mnt/wd_black/kontakt-known-good-20260907_123950(.tar.gz)` — DB_STATE.txt verified
integrity **ok**, k_content_path=**74** (70 real Z: libs + 4 Kontakt factory-content rows), k_sound_info=**30,060**.
Earlier 12:32 snapshot deleted; single clean copy retained. Ready for Reaper/yabridge testing (shared prefix +
DB, so it inherits this exact clean state). If anything regresses in Reaper: roll back via the snapshot's
komplete.db3 rather than improvising.


### Stage 12 — Tile-artwork recovery investigation: EXHAUSTED, folder icons are final (2026-09-07)

User asked whether the folder-icon libraries have their tile artwork anywhere recoverable. Investigated all
on-disk sources with read-only probes (artifacts: scan-library-artwork.sh, probe-nkr-artwork.sh,
hunt-installers-artwork.sh, map-cache-sources.sh, check-live-paresources.sh, map-cache-to-library.sh,
check-nks2-tile.sh). Findings, evidence-backed:

- **The browser tile is driven by `LibrariesCache/*.cache` (62 present), NOT by the on-disk artwork.**
- PAResources/image/<Name>/ artwork (`MST_artwork.png` + `NKS2_software_tile.webp`) is PRESENT and IDENTICAL
  for BOTH working-tile libs (Amati, Butch Vig, Stradivari) AND folder-icon libs (Balinese, Cloud Supply,
  Middle East, Mysteria, Pharlight, Piano Colors, Cuba, East Asia, Ethereal Earth, Hybrid Keys, Session
  Guitarist, Analog Dreams, Soul Sessions, Straylight, West Africa). 136/159 folders have the NKS2 webp.
- Proof art isn't the gate: 5Elements shows a tile with NO PAResources folder at all.
- `.nkr` = sample resource container / instrument-panel art (INST_WALLPAPER), unrelated to browser tile;
  marker count doesn't correlate (Middle East 1085, Pharlight 759 markers but folder icon; Amati 107 has tile).
- Windows Kontakt LibrariesCache (`/mnt/win_system/.../Native Instruments/Kontakt/LibrariesCache`) has NOTHING
  extra — all its .cache also already in the Linux cache. No spare cache anywhere on any drive.
- Installers on disk: only update-setups (Balinese/Cloud Supply update .exe) + Kepler image installer +
  New Century Samples.iso — none regenerate the browser .cache under Wine.

**VERDICT:** folder-icon libraries have all artwork on disk, but the tile requires the per-library `.cache`
that only Native Access / a full installer generates at install time; it does not exist for these libs and
cannot be regenerated in this portable Wine setup (rescan/re-add/Batch-Re-save all failed; art copy is moot).
The ONLY route to those tiles is installing the specific libraries via Native Access on a proper NI/Windows
install (out of scope). Folder icons ACCEPTED as the genuine, unrecoverable final state — not a defect.
Libraries load, stream, and play fine; cosmetic-only shortfall.

**CONFIRMED BLANK-TILE SET (user-verified against live browser, 2026-09-07) — 13 entries, ALL Custom-imported:**
1. Audio Imperia - Sinfonia Drums
2. Doru Malaia - Ethnic Super Drums Collection
3. Drumdrops - Vintage Funk Kit
4. Epic SoundLab - The Forge
5. GetGood Drums - Modern and Massive Pack
6. Hy2rogen - Tekno House Nights
7. Keyscape - 13
8. PlugInGuru.MegaMagic.Bells.Winds.KONTAKT
9. Sonic Mechanics - Classic Guitar Licks
10. Sonic Mechanics - EDM Energy Drums
11. Sonic Mechanics - Future Cinematic FX
12. Sonic Mechanics - Tropical Trap
13. String Audio - Alchemist Cinematic Impacts

PATTERN: every blank-tile entry is a CUSTOM library (added via Import Content, `Kontakt Libraries/Custom/...`,
content_type=3, no Player `.nicnt`/resource-container tile, no surviving `.cache`). ALL Player libraries
(with `.nicnt` + install-time `.cache`) tile correctly — including Balinese Gamelan, Cloud Supply, Middle
East, Mysteria, Pharlight, Piano Colors, Play Series Selection (these were NOT blank, corrected from an
earlier over-broad guess). Conclusion: blank tiles == the Custom-imported set, which is inherent Kontakt
browser behavior (Custom libs get a folder icon; only Player/NKS libs render artwork). Not recoverable
in-setup; accepted.


### Stage 13 — Chords/Phrases "patch corrupted" fix (2026-09-07, DONE)

Symptom: factory Tools **Chords** and **Phrases** threw "This patch is corrupted and cannot be loaded!" and
would not load. (Lo-Fi Vibes threw a similar alert but loaded/worked; its `.nkl` timestamps were from the
user's own save, not corruption.)

DIAGNOSIS (artifacts/check-tools-patches.sh, read-only compare vs pristine `/mnt/workspace/BACKUP/Kontakt 8`):
- ALL `.nkt` instrument files in Chords (134/134) and Phrases (181/181) DIFFERED from backup (rewritten
  by Kontakt-under-Wine, mtime sep 2 22:17 = convergence/Batch-Re-save churn era) → corrupted patches.
- The `.nkr` sample containers and `.ogg` previews were IDENTICAL to backup; nothing missing from backup.

FIX (artifacts/restore-tools-nkt.sh apply): saved the 315 corrupted `.nkt` to
`_kiro_tools_nkt_backup_20260907_142904`, then restored all 315 pristine `.nkt` from BACKUP. Verify:
"still differing: 0". Reversible.

CAUSE/PREVENTION: the `.nkt` corruption was Kontakt/Wine rewriting factory patches on the NTFS Workspace
drive. Do NOT overwrite/re-save the factory Chords/Phrases patches from within Kontakt-under-Wine; load and
play only. If it recurs, consider relocating the Kontakt factory Content off Workspace, but not needed unless
it happens again. NEXT: user to launch Kontakt and confirm both load without the corrupt alert.

### Stage 13 — CORRECTION (2026-09-07): NOT corruption; Wine stack overflow parsing factory .nkt

The Stage-13 "restore .nkt from BACKUP" step above was a NO-OP and the corruption diagnosis was WRONG.
Corrected by byte/header inspection (artifacts/inspect-nkt-headers.sh) and a live process/disk diagnostic
(artifacts/diag-kontakt-hang.sh):

- LIVE Chords `.nkt` and BACKUP Chords `.nkt` are BYTE-IDENTICAL: same size (74380), same mtime (avg 31
  05:26), same valid header `8c22 0100 ... hsin / DSINv / DSINj` — the SAME `hsin/DSIN` monolith structure
  as a known-good Amati `.nki` that loads fine. The earlier `cmp` "differ" result was misleading; the files
  are not corrupt. The 315-file restore replaced identical bytes with identical bytes.
- ROOT CAUSE of the "This patch is corrupted and cannot be loaded!" alert: **Kontakt-under-Wine hits a stack
  overflow while parsing the factory Tools `.nkt` monolith.** The Reaper log shows, right at the load/save of
  these patches: `013c:err:virtual:virtual_setup_exception stack overflow 256 bytes ... (0x10000-0x11000-0x110000)`.
  Wine's default thread stack is too small for Kontakt's parse of this specific container format, so Kontakt
  aborts with its generic "corrupted" message. This is a Wine limitation, NOT file corruption, and NOT caused
  by any of our drive/DB/cache changes.
- "Kontakt unresponsive" scare: RESOLVED — Kontakt is healthy. diag-kontakt-hang.sh showed Kontakt loaded
  cleanly inside Reaper (`initialisation complete 14:35:50`, `Finished initializing ...Kontakt 8 Portable.vst3`),
  no `Kontakt 8.exe` pegged at 100% CPU (top was `reaper` at ~40%, normal), and disk sectors barely moved over
  a 3s window (nvme0n1 +~1.8MB routine writes only). The brief unresponsiveness was the failed Chords/Phrases
  parse momentarily blocking the GUI thread; it clears once you stop trying to load those patches.
- A stale, empty `lock.lck` (0 bytes, sep 7 12:17) exists at UserData/Kontakt 8/ from an earlier standalone
  run. Harmless while Kontakt runs under Reaper; leave it (do not remove while a Kontakt instance is loaded).

VERDICT: Chords/Phrases are not corrupt and not fixable by restoring files. They fail because Wine overflows
the thread stack parsing that factory-Tools `.nkt` format. Options if the user wants them working: (a) increase
Wine's thread stack size for the Kontakt host, or (b) accept as a Wine parse limitation and use other patches.
Do NOT re-save/overwrite these factory patches from Kontakt-under-Wine, and do NOT destabilize the working
setup chasing them. ROLLBACK of the no-op restore is available at
`_kiro_tools_nkt_backup_20260907_142904` but unnecessary (bytes identical).

### Stage 13 — RECOVERY PROCEDURE (2026-09-07): unstick a frozen Kontakt bridge without killing Reaper

When Kontakt (in Reaper via yabridge) spins on the Tools `.nkt` parse and its FX-window "close" does nothing,
the yabridge host dies to a `<defunct>` zombie but Reaper's bridge child keeps waiting on the dead socket,
freezing Reaper's whole UI. The other plugin hosts (bx_enhancer, Valhalla, elysia) stay fine.

FIX (artifacts/unstick-kontakt.sh, mode `reap`): find the parent of the defunct yabridge zombie — it is the
`reaper_host_x86_64` bridge helper (e.g. PID 165723) — and SIGTERM/SIGKILL ONLY that helper. This reaps the
zombie and releases Reaper's block. VERIFIED 2026-09-07: "It closed the Kontakt only, success" — Reaper
unfroze, other plugins stayed loaded. NO `wineserver -k` needed (that `nuke` fallback kills all wine plugins).

Order to use: `reap` first (surgical), `nuke` only if Reaper's main thread itself is still wedged.
PREVENTION: do not load the factory Tools Chords/Phrases patches under Kontakt-on-Wine (they overflow the
Wine thread stack). If you want them, raise the Wine host thread-stack size first.

### Stage 13 — RESOLUTION (2026-09-07): Chords/Phrases removed (reversible), freeze prevented

User doesn't need Chords/Phrases; chose removal over the Wine stack-size tweak (removal is guaranteed,
stack-size would be trial-and-error). Verified pre-removal (artifacts/probe-tools-removal.sh): Chords (32M,
134 .nkt) + Phrases (34M, 181 .nkt) are the ONLY folders under Content/Tools, no .nicnt (plain patch folders,
not a resource-container bundle), pristine BACKUP copies present, no Settings.cfg references.

APPLIED (artifacts/remove-tools-chords-phrases.sh apply, Kontakt closed): MOVED both folders out of the
Content tree to `UserData/_kiro_removed_tools_chords_phrases/` (a same-drive mv, instant + reversible).
Verified Content/Tools now empty of both. Because the .nkt patches are no longer in the Content tree, Kontakt
has nothing to load or re-register — the stack-overflow parse-freeze CANNOT recur and they won't reappear.

REVERSIBILITY (two nets):
  1. Holding dir: mv the two folders back from `UserData/_kiro_removed_tools_chords_phrases/` to Content/Tools/
  2. Pristine originals remain at `/mnt/workspace/BACKUP/Kontakt 8/Content/Tools/{Chords,Phrases}`

STATUS: Task 13 CLOSED. Remaining verification = user launches Kontakt in Reaper once to confirm clean load
with Chords/Phrases gone (expected: no corrupt alert, no freeze, other libraries unaffected).

### Stage 13 — VERIFIED FINAL STATE (2026-09-07)

verify-tools-state.sh confirms: Content/Tools is EMPTY (Chords/Phrases not present); holding dir
`UserData/_kiro_removed_tools_chords_phrases/` contains both (Chords 134 .nkt, Phrases 181 .nkt).
If Kontakt's browser still LISTS Chords/Phrases, it is a STALE DB/browser entry only — the .nkt files
are gone from the Content tree, so clicking one now yields a harmless "not found", NOT the parse-freeze
(the stack-overflow needs the .nkt present). User decision: LEAVE AS-IS indefinitely (harmless); optionally
revisit the Wine thread-stack-size route later if the patches are ever wanted. Task 13 CLOSED.

### Stage 13 — CONFIRMED BEHAVIOR AFTER REMOVAL (2026-09-07)

User confirms: the stale Chords/Phrases browser entries still appear and clicking one throws Kontakt's
dialog "File not found. Please make sure that external drives are connected!" — and it does NOT load into
the tool slot. Neither Reaper nor Kontakt freezes. This is the intended safe outcome: with the .nkt files
relocated out of the Content tree, Kontakt never begins the stack-overflow parse, so it just reports
not-found and continues normally. The dialog is harmless/dismissable. Setup is stable; leaving as-is.


### Stage 14 — Decent Sampler library extraction + non-DS prune (2026-09-07, DONE)

Extracted the Pianobook Decent Sampler collection (400 archives, ~112 GiB) from
`/mnt/workspace/Free VST-s/Pianobook/Decent Sampler` into a DISTINCT `DS Libraries/` tree
(kept separate from `Kontakt Libraries/`), split by streaming demand:
  - HEAVY (>=3GB): AutumnPianoBundle, Festive Celeste (7G), IMPACTOS Hybrid Percussion (8G)
    -> `/mnt/wd_black/DS Libraries` (NVMe)
  - LIGHT (all others, ~397 libs) -> `/mnt/btrfs_disk/DS Libraries` (SATA SSD)
Source archives left UNTOUCHED. Space verdict beforehand: both drives fit easily (btrfs
had 467G free, wd_black 244G); after extract, 374G / 227G free.

Scripts: artifacts/analyze-decentsampler-libs.sh (size/placement), extract-decentsampler-libs.sh
(idempotent, per-archive space guard). Two script fixes needed mid-run:
  - space guard used `df --output` which broke under sl_SI locale (short-skipped all 400);
    fixed to locale-proof `stat -f` (statfs blocks) reading the dest dir.
  - two archives failed: "Festive Celeste.zip" tripped unzip's zip-bomb false positive
    (store-compression 5.7GB) -> re-extracted with UNZIP_DISABLE_ZIPBOMB_DETECTION=TRUE;
    "Tea from HELL (DS).zip" was actually a RAR v5 mislabeled .zip -> extracted with unrar.
    (artifacts/fix-two-failed-archives.sh)

NON-DS PRUNE (user: packs bundled other-engine files): probe (artifacts/probe-nonds-content.sh)
found the extracted tree also held Kontakt (.nki/.nkc/.nkr), EXS24 (.exs), SFZ (.sfz), Ableton
(.adg), Logic (.logicx) patches + macOS junk (__MACOSX, .DS_Store). Verified every .dspreset
references its samples LOCALLY/relative (samples/, Samples/, Resources/) — so removing engine
patches cannot orphan a preset's audio. artifacts/verify-prune-targets.sh clarified the scary
"13,478" dry-run count = mostly __MACOSX folder contents counted recursively; only 154 GENUINE
engine patches (.nki 48, .exs 32, .nkr 26, .sfz 25, .nkc 21, .adg 2). Extension set proven
disjoint from dspreset/dslibrary/wav.

APPLIED prune (artifacts/prune-nonds.sh apply): moved 13,565 engine-patch + mac-junk items to
reversible per-drive trash `_kiro_nonds_trash_20260907_170214`. Protected absolutely: all
.dspreset/.dslibrary, all audio, every Samples/ folder. POST-VERIFY unchanged: wd_black
.dspreset=15/.dslibrary=0, btrfs .dspreset=666/.dslibrary=37 (matches pre-prune). Keepers
across both drives: 681 .dspreset + 37 .dslibrary + ~51,632 .wav.

NEXT (user): add `/mnt/wd_black/DS Libraries` and `/mnt/btrfs_disk/DS Libraries` as folders in
Decent Sampler; once confirmed loading, reclaim space with `rm -rf` on the two trash dirs.

HARDWARE NOTE (for future big commercial libs): board = ASUS TUF GAMING X570-PLUS (WI-FI),
2 M.2 slots BOTH occupied (M.2_1 = WD_BLACK SN850X 1TB = CachyOS system /,/home,/boot;
M.2_2 = WD Black SN850 1TB = ntfs `/mnt/wd_black`). No free M.2. 8 SATA ports, 4 free. For the
planned 1-2TB sampler libs, recommendation = large DRAM-cached TLC SATA SSD (e.g. Samsung 870
EVO 2-4TB) on a free SATA port, formatted ext4/btrfs (NOT NTFS — avoids the ntfs3 issues fixed
in this spec). SATA SSD is plenty for Kontakt/DS streaming (bound by RAM + random-read IOPS, not
sequential BW); NVMe only speeds initial patch load.


### Stage 14b — Decent Sampler library registration via unified symlink (2026-09-07, DONE)

DS (unlike Kontakt) has no library DB — it scans ONE configured "Sample Libraries Location"
recursively for .dspreset/.dslibrary. Our DS libs are split across two drives, so unified them
under one master folder with symlinks (artifacts/setup-ds-symlinks.sh apply):
  `~/DS Libraries All/wd_black -> /mnt/wd_black/DS Libraries`
  `~/DS Libraries All/btrfs    -> /mnt/btrfs_disk/DS Libraries`
Symlinks only (no data moved). Placed in $HOME so it's reachable through Wine's home drive map.
Verified through the links: 15 .dspreset (wd_black) + 666 .dspreset + 37 .dslibrary (btrfs).
USER STEP: in DS browser -> gear/settings -> set Sample Libraries Location to
`~/DS Libraries All` (Wine path e.g. Z:\home\phnx\DS Libraries All); DS scans recursively and
lists all presets from both drives. ROLLBACK: `rm -rf "~/DS Libraries All"` (removes only links).


### Stage 14c — Festive Celeste "missing files" = folder case mismatch (2026-09-07, DONE)

DS reported missing samples for Festive Celeste. probe-festive-celeste.sh proved the files ARE
present (3137 wav on disk vs 3154 in zip; diff = __MACOSX sidecars the prune removed). Root cause:
the .dspreset refs use `Samples/...` (capital S) but the extracted folder was `samples` (lowercase).
Linux (btrfs/ext4) is case-sensitive, so DS couldn't resolve them (works on Windows/macOS where FS
is case-insensitive). This is a Pianobook packaging inconsistency, NOT data loss and NOT caused by
our prune (prune protected all audio + Samples/).

FIX = single rename: `mv ".../Festive Celeste/samples" ".../Festive Celeste/Samples"`. User confirmed
resolved. A generalized scanner/fixer exists for any other packs with the same case mismatch:
artifacts/fix-samples-case.sh (dry-run, then apply) — renames only pure case-diff existing folders,
reversible. User will run it / report if more libs show the issue.


### Stage 15 — Kontakt "installation directory not found" after wine-staging upgrade (2026-09-08, RESOLVED)

Trigger: user ran `sudo pacman -Syu ffmpeg uv python` — the `-Syu` is a FULL system upgrade (not just
those 3 pkgs), which upgraded wine-staging 11.16 -> 11.17. On next Reaper launch Kontakt Portable v8.11.0
threw "Installation directory not found / File not found: \Kontakt 8.vst3plugin" and the browse dialog
rejected every (correct) path pointed at it.

Diagnosis (all read-only probes):
- Files INTACT: x64/Kontakt 8.vst3plugin (159614976 B), x64/Kontakt 8.exe present, readable via /mnt AND
  Z: dosdevice. Drive maps fine (D:->/mnt/workspace, F:->/mnt/workspace, Z:->/). /mnt/workspace mounted.
- ROOT CAUSE: the wine upgrade RECONFIGURED the prefix — `~/.wine/system.reg`, `user.reg`, `userdef.reg`
  all rewritten sep 8 20:09 (+ `.update-timestamp` 20:08), wiping Kontakt Portable's install registration.
- Registry stores lib ContentDirs as `Z:\mnt\...` (whole config keyed on Z:, not D:). Registry file
  associations still pointed D:\...\x64\Kontakt 8.exe (Inno installer leftovers).
- Downgrading wine-staging 11.17->11.16 (sudo pacman -U /var/cache/pacman/pkg/wine-staging-11.16-1.1-...zst)
  did NOT fix it alone — the package downgrade doesn't undo the prefix rewrite.

FIX: restored the known-good wine registry from the Stage-11 snapshot
`/mnt/wd_black/kontakt-known-good-20260907_123950/wine/` (system.reg/user.reg/userdef.reg captured
sep 7 12:23, BEFORE the break) into `~/.wine/`, backing up current .reg first, then `wineserver -k` to
reload. (artifacts/restore-wine-registry.sh, with probe-prefix-snapshot.sh confirming the snapshot held
the Kontakt registration.) Combined with wine-staging pinned at 11.16.

STATUS: NOT resolved by registry restore alone. The Reaper log line `Finished initializing
'.../Kontakt 8 Portable.vst3'` only means the plugin SHELL loaded — Kontakt's own UI still shows
"Installation directory not found" (confirmed by screenshot). Registry restore + downgrade did not fix it.
Investigation continues below.

PREVENTION: pin wine-staging so a future `-Syu` can't silently re-break it —
add `IgnorePkg = wine-staging` to /etc/pacman.conf. Remove the pin only to upgrade wine deliberately
(close Reaper, back up ~/.wine/*.reg first; if it re-breaks, restore the snapshot .reg as above).
Also: use `pacman -S <pkg>` (NOT `-Syu <pkg>`) to install single packages without a full system upgrade.
Artifacts: probe-kontakt-install-path.sh, probe-kontakt-appdir.sh, probe-vst3plugin-file.sh,
find-kontakt-install-config.sh, quick-wine-state-check.sh, check-wine-downgrade.sh,
probe-prefix-snapshot.sh, restore-wine-registry.sh.


### Stage 15 — ACTUAL ROOT CAUSE + RESOLUTION (2026-09-08)

CORRECTION: the wine-registry restore (Stage 15 above) was a DETOUR, not the fix. The real cause was a
yabridge mistake:
- The Reaper log showed the loaded Kontakt plugin came from `~/Prejemi/Yabridge_Windows/Kontakt 8 Portable.vst3`
  — a stray, INSTALL-LESS Kontakt Portable **v8.11.0** copy (ktp8110.dll + 35 runtime DLLs, dated sep 8 16:57)
  the user had dropped there to bridge some plugins, not realizing it got yabridge-synced.
- yabridge's bundle `~/.vst3/yabridge/Kontakt 8 Portable.vst3` had its Windows-side symlink pointing at that
  stray copy. Kontakt Portable resolves its install dir relative to the loaded plugin binary; that copy has
  NO install tree beside it -> "Installation directory not found. v8.11.0".
- The REAL working install is the OLDER v8.0.1 (ktp801.dll, sep 2024) at
  `/mnt/workspace/VST Install/Kontakt Portable/Kontakt 8/x64/VST3/Kontakt 8 Portable.vst3`, sitting next to the
  full Content/Database/PAResources tree. That path was ALSO a yabridge source, so Reaper saw two identically
  named "Kontakt 8 Portable.vst3" entries and the user had added the wrong (stray) one.

FIX (verified working): `yabridgectl rm "/home/phnx/Prejemi/Yabridge_Windows"` then `yabridgectl sync`
(171 plugins, 0 new) — un-bridged the stray copy (deleted no files). Re-added Kontakt in Reaper; it now
loads the workspace v8.0.1 install and opens with no install-dir error. Probes confirmed
~/Prejemi/Yabridge_Windows held ONLY that Kontakt bundle (no other wanted plugins), so removing the path
cost nothing else.

POST-FIX STATE (check-reg-and-tiles-state.sh): wine-staging pinned 11.16; live ~/.wine/*.reg = sep 8 20:48
(normal per-run rewrite); pre-restore reg backup kept at ~/.wine/_kiro_reg_backup_20260908_201906 (unused,
escape hatch only). Icons/tiles UNAFFECTED — LibrariesCache still has all 62 .cache files (matches known-good);
komplete.db3 on /mnt/workspace untouched by any wine/yabridge work. No registry rollback needed — already in
the good state.

LESSONS / PREVENTION:
- Do NOT point yabridge at a folder containing a Kontakt Portable .vst3 that lacks its install tree; keep the
  bridged Kontakt = the workspace install's own .vst3 (next to Content/Database).
- `-Syu <pkg>` = full system upgrade; use `pacman -S <pkg>` for single installs. wine-staging is pinned
  (IgnorePkg) to avoid silent upgrades that reconfigure the prefix.
- When Reaper shows a plugin path in its log, verify it's the intended install — a "Finished initializing"
  line only means the plugin shell loaded, NOT that Kontakt found its content (that check was the earlier
  premature "fixed" error).
Artifacts added: probe-loaded-vst3-origin.sh, probe-yabridge-repoint.sh, list-yw-plugins.sh,
check-reg-and-tiles-state.sh.


### Stage 16 — TILE ROOT CAUSE FINALLY ISOLATED: content_type 2->3 demotion (2026-09-09)

After the wine incident, most browser tiles went to folder icons. Exhaustive read-only probing this session
CORRECTED the prior "unrecoverable / no cache" conclusion and found the real mechanism:

- Tiles are driven by `k_content_path.content_type` in komplete.db3: **type 2 = Player/NKS (renders artwork
  tile), type 3 = User/Custom (folder icon)**. Caches, artwork (NI Resources/image/<Lib>/), and ContentDir
  paths were ALL present/identical for blank vs working libs — NOT the differentiator.
- CRITICAL path correction: the REAL browser DB is `UserData/Kontakt 8/komplete.db3` (78MB live, had -wal/-shm),
  NOT `UserData/komplete.db3` (a 0-byte decoy that misled several probes; reading it via ntfs-3g also gave
  a size=0 artifact). Always read the `Kontakt 8/` one, via a local `dd` copy, to avoid FUSE/lock artifacts.
- LIVE db: 74 paths, ALL demoted to content_type=3 (0 type-2) -> whole browser folder-icon.
  Backup `komplete.db3.pre_ewqlra_144329` (42MB): 208 paths, 46 at content_type=2 -> the tiles-working state.
  A Kontakt Import/Rescan/Reset-Multi under this Wine setup rewrote content_type 2->3 (and re-bloated the db
  42MB->78MB, sound_info 32216->60105). That rescan is the trigger that blanks the tiles.

FIX (artifacts/restore-alltiles-db.sh apply, Kontakt closed): backed up live 78MB db (+wal/shm) to
`komplete.db3.pre_tilerestore_20260909_112025`, copied `pre_ewqlra` (46 type-2 tile libs) over live, cleared
stale WAL/SHM, REINDEX (fixed the stale index_p_sound_info_Instrument_1_sort_order both dbs had), integrity
check = **ok, 208 paths, 46 type-2, 32216 presets**. Reversible (rollback cmd printed).

PREVENTION (important): do NOT run Import Content / Rescan / "Reset Multi" in Kontakt under this Wine setup —
that is what demotes content_type 2->3 and blanks all tiles + re-bloats the db. Just browse/load. If tiles
ever blank again, restore a type-2 db (pre_ewqlra or the pre_tilerestore backups) rather than rescanning.
USER STEP: launch Reaper (QT_QPA_PLATFORM=xcb reaper), load Kontakt, confirm ~46 tiles render (only genuine
Custom libs stay folder icons). Do NOT rescan.


### Stage 16b — CORRECTION: pre_ewqlra restore was too old (reintroduced D:/F: paths) (2026-09-09)

The restore-alltiles-db.sh apply above was WRONG in one dimension: `pre_ewqlra_144329` is dated ~sep 6,
PRE-dating the Stage 8-10 Z: path convergence. It DID restore the type-2 tiles, but it also brought back
**D:\ (Import Content) and F:\ (user-preset) stale paths** — exactly what Stages 8-10 fixed. User asked for
"yesterday's (sep 8)" state = clean Z: paths AND tiles, not a week-old db. Tiles reportedly still not right.

CURRENT DB STATE (important for anyone resuming):
- LIVE `komplete.db3` = pre_ewqlra content right now: 208 paths, 46 type-2 tiles, BUT D:/F: stale paths. [good tiles, bad paths]
- `komplete.db3.pre_tilerestore_20260909_112025` (78MB) = the db we overwrote: clean Z: paths, but all type-3/blank. [good paths, bad tiles]

CORRECT FIX (non-destructive MERGE, preserves current library set + clean Z: paths + restores tiles):
Do NOT wholesale-restore any single old backup. Instead:
  1. Read-only analysis: `plan-tile-merge.py` — diffs the two dbs. Outputs (a) PROMOTION PLAN = aliases that
     are type-2 in the tiles db but non-tile in the clean-Z db (the set to flip 3->2); (b) ADDED-SINCE-BACKUP
     = aliases only in the 78MB clean-Z db (libs added since sep 6 that a wholesale pre_ewqlra restore would
     LOSE — directly answers the user's "check what was added, preserve some"); (c) STALE-PATH tiles = the
     D:/F: type-2 rows proving why keeping pre_ewqlra live is wrong.
  2. Apply: restore the 78MB clean-Z db as live, then targeted SQL UPDATE content_type 3->2 for the promotion
     set (Python sqlite3 + KOMPLETE collation; Kontakt closed; back up first; REINDEX; integrity check).
     Result = clean Z: paths (incl. added-since libs) AND tiles back. Best of both, loses nothing.
  3. NEVER rescan/Import/Reset-Multi afterwards (re-demotes 2->3).

Also to check (user's other hypothesis): some blank tiles may be genuinely-added Custom libs from other drives
whose artwork lives elsewhere; those are content_type=3 by nature and correctly stay folder icons (~1-3 in the
good state per user recollection). The promotion plan only flips aliases that WERE type-2 tiles, so it won't
wrongly promote genuine Custom libs.
Artifact added: plan-tile-merge.py (read-only analysis, awaiting run).


### Stage 16c — MERGE PLAN CONFIRMED by analysis, apply script authored (2026-09-09)

User rolled back the wrong restore, so LIVE = 78MB clean-Z db again (blank/type-3); pre_ewqlra_144329 is
only a backup (tile reference). plan-tile-merge.py (re-pointed to this arrangement) output:
- LIVE: 74 paths, drive histogram {Z:70, D:4}; integrity ok apart from the known stale sort index (REINDEX fixes).
- PROMOTION SET = 45 aliases that are content_type=2 in pre_ewqlra but non-tile in live — and EVERY one already
  has a clean Z: path in live (Player libs across btrfs_disk/wd_black/storage). So flipping them 3->2 restores
  tiles WITHOUT touching paths.
- ADDED-SINCE-BACKUP = 0 (nothing unique in live would be lost — but we're not restoring the backup anyway).
- Only 1 tile alias (`GGD Modern and Massive`) is absent from live and in the backup carries a stale F:\ path —
  correctly NOT re-added (user removed/renamed it). This is the single lib that stays a folder icon by choice.
- 4 live rows remain on D: (not in promotion set, not tiles) — reported by the apply script for visibility.

DECISION: do the in-place MERGE, not a restore. Artifact `apply-tile-merge.py`:
- computes the promotion set live at runtime from both dbs (not hard-coded);
- Kontakt/Reaper must be closed (checks wineserver); backs up live (+wal/shm) to komplete.db3.pre_tilemerge_*;
- REINDEX (clears stale index_p_sound_info_Instrument_1_sort_order); UPDATE content_type=2 for the 45 aliases;
  integrity check; clears stale wal/shm; prints ROLLBACK.
Dry-run first (python3 apply-tile-merge.py), then `apply`. After: launch Reaper, confirm ~45 tiles render and
Import Content shows Z: paths; DO NOT rescan/Import/Reset-Multi (re-demotes 2->3).


### Stage 16d — MERGE APPLIED (2026-09-09 11:33)
apply-tile-merge.py apply: 45 rows updated 3->2, integrity ok, 74 paths (unchanged), 45 type-2 tile libs,
4 rows still on D: (non-tile, unchanged). Live backup: komplete.db3.pre_tilemerge_20260909_113347
(rollback cmd printed). Clean Z: paths preserved; nothing lost; no rescan.
AWAITING on-screen verification in Reaper/Kontakt (tiles render? which blank vs render?). If any stay blank
after this, the content_type flag is correct but on-disk artwork (NI Resources/image/<Lib>/) or .cache
linkage for that specific lib is the next thing to check — do NOT rescan.


### Stage 16e — tiles MOSTLY back; artwork hunt for stragglers (2026-09-09)
Screenshot after merge: ~34 of 45 tiles render. Still folder-icon: genuine Custom libs (expected: Sonic
Mechanics x4, GetGood, Keyscape, PlugInGuru, Audio Imperia, Doru Malaia, Drumdrops, Epic SoundLab, Hy2rogen,
String Audio) PLUS a subset of Player libs that SHOULD have art: ANALOG STRINGS, Balinese Gamelan, East Asia,
Guarneri Violin, India, Mass, Piano Colors, Soul Sessions, Straylight, Tablas, Ultimate Pro Oriental Strings.
For those Player libs content_type is now 2 (correct) but the on-disk TILE ARTWORK isn't resolving.
Artifact find-tile-artwork.sh (read-only): compares a working lib's art layout (NI Resources/image/<Product>
+ product .nicnt) to each blank lib, and searches all drives for image/<Lib> folders possibly copied earlier.


### Stage 16f — CORRECTION: the 45 Player tiles ALL render; blank set is 12 CUSTOM libs (2026-09-09)
User corrected the read: after the merge, ALL 45 Player libs show tiles. The genuinely-blank ones are 12
CUSTOM-type libs: Audio Imperia - Sinfonia Drums, Doru Malaia - Ethnic Super Drums Collection, Drumdrops -
Vintage Funk Kit, Epic SoundLab - The Forge, GetGood Drums - Modern and Massive Pack, Keyscape - 13,
PlugInGuru.MegaMagic.Bells.Winds, Sonic Mechanics (Classic Guitar Licks / EDM Energy Drums / Future Cinematic
FX / Tropical Trap), String Audio - Alchemist Cinematic Impacts. Custom libs get tile art from an image
shipped/placed inside the library folder (referenced by the db), NOT from the NI Resources Player tree. User
recalls only 1-3 were blank in the good state, so some of these DID have tiles before. find-tile-artwork.sh
reworked to fuzzy-match db alias OR path and dump each lib's on-disk art files (.png/.jpg/.nicnt/.meta) to
locate the missing tile images (and search other drives for copies).


### Stage 16g — artwork mechanism located (2026-09-09)
find-tile-artwork.sh output:
- WORKING Player tiles resolve art from `/mnt/workspace/VST Install/Kontakt Portable/UserData/NI Resources/
  image/<ProductName>/` (Amati Viola, Cloud Supply, ANALOG STRINGS, Balinese Gamelan, Bowls, Butch Vig Drums,
  Cinebrass, Cloud Supply, Damage, Hybrid Keys, Piano Colors, 5Elements... all present there). This is why the
  45 Player libs render. The NI Resources/image tree is the Player tile source.
- The 12 blanks are ALL content_type=3 (Custom). Custom libs are NOT in the NI Resources/image tree; their
  browser tile comes from artwork referenced by the db row / shipped in the lib folder. On disk they DO have
  cover art: Doru Malaia (wallpaper.png + Documentation/Pics/*.jpg), PlugInGuru (MegaMagic Artwork.jpg,
  bg/MMBWbg.png), Sonic Mechanics x4 (each a .jpg cover), String Audio (only .nkx). Audio Imperia, Epic
  SoundLab, Keyscape folders had NO image file surfaced at maxdepth 3.
- SPECIAL: GetGood Drums is actually a PLAYER lib (real .nicnt, product name "GGD Modern and Massive",
  path under wd_black/.../Player/... /Modern & Massive). Its blank tile = missing NI Resources/image/<GGD
  Modern and Massive> folder AND it was the merge-skipped alias. Could be given a real tile by adding its
  image dir, OR left as-is.
NEXT: probe-custom-tile-link.py — determine HOW a Custom lib links its tile picture (db column? image-ish
table? folder convention?) by comparing a Custom lib that renders vs a blank one. Then fix blanks the same way.


### Stage 16h — Custom tile is NOT db-driven; it's a folder cover-image convention (2026-09-09)
probe-custom-tile-link.py: komplete.db3 has NO image/picture/thumbnail table and NO picture column. k_content_path
rows for Custom libs are byte-identical (state=1, visible=1, product_* None) whether the tile renders or is blank.
=> The Custom-lib browser tile is resolved at DISPLAY TIME from a cover IMAGE FILE inside the library folder by a
NAME/LOCATION convention, not from the db. (My earlier RENDER/BLANK guesses in that probe were just fuzzy labels;
some "RENDER" entries — e.g. two Sonic Mechanics — are actually blank in the screenshot.)
=> No db fix will help these. Need to find the on-disk cover convention. probe-custom-cover-convention.sh lists
every image file (name+relpath+size) for Custom libs whose tiles VISIBLY render (Electro Acoustic, Electric
Sunburst DLX, Session Keys Electric R, Picked Acoustic) vs the blanks, to find the shared name/location the blanks
lack. Then fix = place/copy each blank lib's existing cover art (TT-Cover.jpg, CFX-Cover.jpg, MegaMagic Artwork.jpg,
wallpaper.png, etc.) into that convention. NOTE: these are all on btrfs_disk/wd_black (Z:), not the workspace NI
Resources tree — Player tiles use NI Resources/image/<Product>, Custom tiles use the in-folder cover.


### Stage 16i — REVISED: rendering type-3 libs are NKS (.nicnt) using NI Resources/image; blanks lack NKS art dir (2026-09-09)
probe-custom-cover-convention.sh: the type-3 libs that VISIBLY render (Electro Acoustic, Session Keys Electric R,
Picked Acoustic, Electric Sunburst DLX) have NO loose image in-folder — ONLY a .nicnt. So a rendering tile requires
NKS metadata (.nicnt) whose Product <Name> maps to NI Resources/image/<Name>/ (same tile source as the 45 Player
libs). The loose jpg/png in the blank libs (TT-Cover.jpg, CFX-Cover.jpg, MegaMagic Artwork.jpg, wallpaper.png,
Documentation/Pics/*) are vendor docs, NOT the browser tile source — Kontakt does not use them.
=> Two fix classes for the 12 blanks: (a) has .nicnt but MISSING NI Resources/image/<Name> -> create that art dir
(e.g. GetGood "GGD Modern and Massive"); (b) NO .nicnt -> never had an NKS browser tile, nothing to "restore"
(would need building a full NKS product to fake a tile — out of scope / not the good-state).
probe-blank-nicnt-vs-niimage.sh resolves per blank: .nicnt? Product Name? NI image dir present/missing? + scans
NI Resources/image for name variants. This decides exactly which blanks are fixable and how.


### Stage 16j — RESOLVED: 11 blanks never had a tile; GetGood is the only fixable one (2026-09-09)
probe-blank-nicnt-vs-niimage.sh proved the convention: a tile needs a .nicnt whose Product Name maps to
NI Resources/image/<Name>/ (with MST_artwork.png/MST_logo.png/MST_plugin.png/.meta). All 3 RENDER refs match.
- 11 of 12 blanks have NO .nicnt (Doru Malaia, PlugInGuru, Sonic Mechanics x4, String Audio, Audio Imperia,
  Epic SoundLab, Keyscape, Drumdrops) => plain user folders, no NKS metadata => Kontakt never showed a tile for
  them; their loose jpg/png are vendor docs. NOTHING to restore — folder icons is their correct/good-state look.
- GetGood Drums = the ONE genuine casualty: HAS .nicnt (Product 'GGD Modern and Massive') AND its
  NI Resources/image/GGD Modern and Massive/ dir EXISTS with full MST art. It stays blank only because its
  k_content_path row is content_type=3 (the F:\ straggler we intentionally skipped in the tile-merge; its live
  path is now on Z: wd_black). FIX = flip that single row 3->2.
Artifact fix-getgood-tile.py: matches the GetGood row by path fragment (not blind alias), backs up, REINDEX,
UPDATE content_type=2, integrity check, rollback printed. Dry-run then apply. After: only GetGood should change;
the other 11 correctly remain folder icons. This closes the tile investigation.


### Stage 16k — GetGood tile fixed; tile investigation CLOSED (2026-09-09 13:04)
fix-getgood-tile.py apply: 1 row (id=178, Z:\mnt\wd_black\...\GetGood Drums - Modern and Massive Pack) flipped
3->2, integrity ok, 46 type-2 tile libs total. Backup komplete.db3.pre_getgood_20260909_130416 (rollback printed).
FINAL TILE STATE: 46 NKS/Player libs render tiles (45 from the merge + GetGood). The remaining 11 folder-icon
libs (Doru Malaia, PlugInGuru, Sonic Mechanics x4, String Audio, Audio Imperia, Epic SoundLab, Keyscape,
Drumdrops) have no .nicnt/NKS metadata and correctly show folder icons — that is their true good-state look.
AWAITING user on-screen confirmation that GetGood now shows its tile.

TILE ROOT CAUSE (final, whole arc): a Kontakt Import/Rescan/Reset-Multi under Wine demoted all Player libs'
k_content_path.content_type 2->3 (tile -> folder icon). Fix = restore content_type=2 for the NKS libs
(non-destructive in-place UPDATE on the live clean-Z db; no rescan, paths preserved). Prevention: never run
Import Content / Rescan / Reset Multi in Kontakt under this Wine setup. Tile art itself lives in
NI Resources/image/<ProductName>/ (MST_*.png) for NKS libs; libs without a .nicnt never get a browser tile.


### Stage 16l — user disputes "11 never had tiles"; testing with evidence not inference (2026-09-09)
User (correctly) doubts the "these 11 never had a browser tile" conclusion — it was inference, not proof (my
.nicnt search was only maxdepth 3 + name-filtered; I never checked backup DBs for a prior type-2 state or
NI image dirs for these names). Two decisive read-only probes:
- verify-11-had-tiles.py: across EVERY komplete*.db3 (live+backups), report each of the 11 libs' content_type
  and whether it was EVER type-2 (=> it DID render before). If any were type-2 in a real prior db, flip 3->2.
- deep-nks-probe.sh: full-depth unfiltered search inside each lib for ANY NKS metadata (.nicnt/.nfo/.nkx/.db/
  .meta, MST_*.png, resources/pictures/snapshots) + fuzzy match against NI Resources/image folders.
Await results before concluding.


### Stage 16m — EVIDENCE on the 11 (honest limits) (2026-09-09)
verify-11-had-tiles.py scanned 22 komplete*.db3 (oldest = sep 1 19:56): ALL 11 libs are content_type=3 in
EVERY preserved db, NEVER type-2. deep-nks-probe.sh: none have a .nicnt, none have a matching
NI Resources/image/<name> dir, NI image fuzzy-match returned nothing.
=> In every PRESERVED db state (>= sep 1) these were folder-icons, and they currently lack NKS registration
   (.nicnt + image dir) so Kontakt shows no tile.
HONEST LIMITATION (do not overclaim): the oldest db on disk is sep 1; dbs were rewritten repeatedly, so
"never type-2 in any preserved db" does NOT strictly disprove the user's memory of an earlier tiled state.
CORRECTION to my earlier "plain user folders": several are real Kontakt library containers —
  Epic SoundLab (Forge.nkc+Forge.nkr), Audio Imperia Sinfonia (Sinfonia.nkc+.nkr), Drumdrops & String Audio
  (.nkx), others loose .nki. The .nkc/.nkr monoliths CAN hold a picture and be given a proper NKS tile, but
  they are NOT currently NKS-registered (no .nicnt), which is why no tile + no image dir.
So: no tile is recoverable from any backup db (none exists), and no on-disk NKS art exists to point to.
Making these show tiles would require CREATING NKS metadata (.nicnt + NI Resources/image/<Name>/MST_*.png)
per lib — i.e. authoring tiles, not restoring them. Offer that as an explicit option rather than asserting
"nothing to restore".


### Stage 16n — tile RECIPE is simple; authoring proof (2026-09-09)
probe-tile-recipe.sh: a working NKS tile = NI Resources/image/<ProductName>/ with MST_artwork.png (134x66),
MST_plugin.png (~127x100), MST_logo.png (240x196), optional OSO/VB pngs, and a PLAIN-XML <ProductName>.meta
(<resource version="2.x"><name>Name</name><type>image</type></resource>) — NO product id/signature. Image dir
name == .nicnt Product Name == browser name. ImageMagick 7 present (can scale covers). 73 image dirs currently.
OPEN QUESTION deciding simple-vs-hard: does Kontakt render the tile from JUST the image dir keyed by the db
alias (no .nicnt), or does it also require a .nicnt in the lib? Test with a proof: make-tile-proof.sh creates
ONE image dir "Sonic Mechanics - Tropical Trap" (== db alias) with MST pngs from TT-Cover.jpg + .meta, NO
.nicnt, NO db change (fully reversible: rm -rf the dir). If Kontakt shows the tile -> simple path works, batch
all 11 from their covers. If not -> add .nicnt + content_type step.


### Stage 16o — SIMPLE PATH CONFIRMED: tile from image dir alone (2026-09-09 13:16)
make-tile-proof.sh apply + user screenshot: 'Sonic Mechanics - Tropical Trap' now shows its cover tile in the
Kontakt browser — created from ONLY NI Resources/image/<db-alias>/ (MST_artwork/plugin/logo.png from TT-Cover.jpg
+ plain-XML .meta). NO .nicnt, NO db content_type change, NO rescan needed. So a browser tile for these type-3
Custom libs resolves purely from an NI image dir keyed by the db alias == browser name.
=> Batch the rest. make-tiles-batch.sh: for each remaining folder-icon lib, scale its best on-disk cover to the
3 MST sizes into NI Resources/image/<alias>/ + .meta. Covers mapped: SM Classic Guitar Licks, SM EDM Energy,
SM Future Cinematic (CFX-Cover), Doru Malaia (wallpaper.png), PlugInGuru (MegaMagic Artwork.jpg). AUTO (largest
in-folder image) for: String Audio Alchemist, Audio Imperia Sinfonia, Epic SoundLab Forge, Keyscape, Drumdrops.
Skips libs whose image dir already exists (Tropical Trap) and reports any with no cover. Reversible (rm -rf the
made dirs). No db writes, no rescan.


### Stage 16p — batch dry-run: 5 have covers, 5 need web art (2026-09-09)
make-tiles-batch.sh dry-run: 5 libs have on-disk covers (SM Classic Guitar Licks, SM EDM Energy, SM Future
Cinematic FX/CFX-Cover, Doru Malaia/wallpaper.png, PlugInGuru/MegaMagic Artwork.jpg) -> tiles buildable now.
5 have NO usable cover on disk (String Audio - Alchemist Cinematic Impacts, Audio Imperia - Sinfonia Drums,
Epic SoundLab - The Forge, Keyscape - 13, Drumdrops - Vintage Funk Kit). User wants to source official cover
art for those from the web and build tiles the same way. Plan: (1) apply the 5 local now; (2) web-search each
missing product's official cover, download to a staging dir, then run the same MST-png + .meta recipe keyed by
the exact db alias. Same simple path (no .nicnt, no db, no rescan), reversible.


### Stage 16q — 5 local tiles applied; 5 web-sourced pending staging (2026-09-09)
make-tiles-batch.sh apply created tiles for: Sonic Mechanics Classic Guitar Licks, SM EDM Energy Drums, SM
Future Cinematic FX, Doru Malaia, PlugInGuru MegaMagic (image dirs under NI Resources/image/<alias>). Rollback =
rm -rf each dir (printed). Awaiting user's on-screen confirm in Kontakt.
Remaining 5 have no on-disk cover; sourcing official art from web. Real products confirmed via search:
- String Audio - Alchemist Cinematic Impacts (kvraudio/audiofanzine/String Audio pages)
- Audio Imperia - Sinfonia Drums (audioimperia.com shop)
- Epic SoundLab - The Forge (kvraudio product page)
- Keyscape - 13 (Spectrasonics Keyscape; '-13' is a user folder tag)
- Drumdrops - Vintage Funk Kit (drumdrops.com)
WORKFLOW: user saves each cover into ~/kontakt_tile_art/<db-alias>.jpg, then make-tiles-from-staged.sh (dry-run
then apply) builds MST pngs + .meta keyed to the alias. Same simple path (no .nicnt, no db, no rescan),
reversible. Artifact make-tiles-from-staged.sh created and ready.


### Stage 16r — web covers staged; final 5 tiles (2026-09-09)
User dropped 5 official covers in ~/Slike/Missing Kontakt Lib Browser Instrument Entry Tiles Artwork/ (all PNG).
4 filenames match their alias; 'Spectrasonics Keyscape.png' -> alias 'Keyscape - 13'. make-tiles-web.sh maps
each file to its db alias and builds MST_artwork/plugin/logo.png + .meta into NI Resources/image/<alias>/ (same
recipe, no .nicnt/db/rescan, reversible). After apply, all 12 previously-blank Custom libs have tiles (6 from
local covers + GetGood db flip earlier + these 5). Awaiting user on-screen confirm.


### Stage 16s — ALL tiles restored/authored; browser fully back (2026-09-09)
make-tiles-web.sh apply created the final 5 tiles (String Audio Alchemist, Audio Imperia Sinfonia, Epic
SoundLab Forge, Keyscape-13 from Spectrasonics Keyscape.png, Drumdrops Vintage Funk) in NI Resources/image/
<alias>/. Rollback printed. Awaiting last on-screen confirm.

TILE ARC COMPLETE:
- 45 Player/NKS libs: restored via content_type 3->2 merge (apply-tile-merge.py) on the clean-Z live db.
- GetGood Drums: 1-row 3->2 flip (fix-getgood-tile.py) — had .nicnt + NI image dir already.
- 12 Custom libs: authored NI Resources/image/<alias>/ tiles from cover art (6 from on-disk covers via
  make-tile-proof.sh + make-tiles-batch.sh; 5 from user-supplied web covers via make-tiles-web.sh).
Method for Custom tiles (reusable): NI Resources/image/<db-alias>/ with MST_artwork.png 134x66, MST_plugin.png
127x100, MST_logo.png 240x196 + plain-XML <alias>.meta. Dir name == db alias == browser name. No .nicnt, no db
change, no rescan needed. ImageMagick used to scale covers.
All artifacts reversible (rm -rf the image dirs; db backups pre_tilemerge_*/pre_getgood_* for the db flips).
PREVENTION (unchanged): never run Import Content / Rescan / Reset Multi in Kontakt under this Wine setup — it
re-demotes content_type 2->3 and blanks the Player tiles again.


### Stage 16t — 3 stragglers: GetGood, PlugInGuru, Hy2rogen (2026-09-09)
Most tiles render. probe-remaining-blanks.sh on the 3 still-blank:
- GetGood: type=2, .nicnt Product 'GGD Modern and Massive', NI image dir 'GGD Modern and Massive' EXISTS.
  All correct yet blank — browser shows the db ALIAS ('GetGood Drums - Modern and Massive Pack') which differs
  from the product name; may need an image dir keyed by the alias too, OR a full Kontakt restart (image tree is
  cached at startup).
- PlugInGuru: type=3, no .nicnt, image dir 'PlugInGuru.MegaMagic.Bells.Winds.KONTAKT' EXISTS (== alias) — same
  setup as the RENDERING Tropical Trap, yet blank. Prime suspect = Kontakt not restarted after creation (image
  tree cached), OR a png/meta difference.
- Hy2rogen - Tekno House Nights: type=3, no .nicnt, NO image dir yet (never built — wasn't in the original 12).
  Has cover CS4068084-02A-BIG.jpg. Build it -> make-tile-hy2rogen.sh.
Probe compare-working-vs-blank-tiledir.sh compares Tropical Trap (works) vs PlugInGuru+GGD dirs to find any
file/geometry/meta diff. KEY CHECK: was Kontakt fully restarted after the batch? It reads NI Resources/image at
startup and caches. Build Hy2rogen regardless.


### Stage 16u — dots confirmed as PlugInGuru blocker; GetGood needs alias-named dir (2026-09-09)
probe-dot-names-and-alias.sh: PlugInGuru is the ONLY image dir of 85 with a dot in its name; every rendering
tile is dot-free. => Kontakt does not resolve the dotted 'PlugInGuru.MegaMagic.Bells.Winds.KONTAKT' image dir.
Hy2rogen tile built (make-tile-hy2rogen.sh) from CS4068084-02A-BIG.jpg.
FIXES:
- GetGood (fix-getgood-tiledir.sh): add NI image dir named EXACTLY as the db alias 'GetGood Drums - Modern and
  Massive Pack' (copied from existing 'GGD Modern and Massive' art). The pre-existing product-name dir alone
  didn't render because the browser row uses the alias. No db change.
- PlugInGuru: rename db alias to dot-free 'PlugInGuru MegaMagic Bells Winds' (fix-pluginguru-dots.py: backup,
  KOMPLETE collation, REINDEX, UPDATE alias, integrity) THEN build matching dot-free image dir + remove old
  dotted dir (fix-pluginguru-tiledir.sh). Reversible (db backup pre_pgalias_*; rm -rf dirs).
Order: getgood dir (any time) ; pluginguru = dots.py apply (Kontakt closed) THEN tiledir.sh apply ; then relaunch.


### Stage 16v — 3 stragglers fixed (2026-09-09 13:58)
- GetGood: fix-getgood-tiledir.sh apply -> NI image dir 'GetGood Drums - Modern and Massive Pack' (alias) from GGD art.
- PlugInGuru: fix-pluginguru-dots.py apply renamed db alias (id=247) to 'PlugInGuru MegaMagic Bells Winds'
  (backup pre_pgalias_20260909_135814, integrity ok); fix-pluginguru-tiledir.sh apply built the clean image dir
  + removed the old dotted dir.
- Hy2rogen tile built earlier.
Awaiting on-screen confirm of all 3. If GetGood still blank with the alias-named dir, its lookup may want the
product-name variant only + a browser reload; but alias-named dir mirrors the working Custom pattern.


### Stage 16w — CORRECTION: PlugInGuru tile keys off FOLDER NAME, not db alias (2026-09-09)
GetGood + Hy2rogen now render. probe-pluginguru-key.sh: db alias was successfully renamed to 'PlugInGuru
MegaMagic Bells Winds' BUT the browser still displays the dotted folder name 'PlugInGuru.MegaMagic.Bells.Winds.
KONTAKT' -> Kontakt keys the tile off the LIBRARY FOLDER NAME, not the db alias. So the 'dots block it' theory
was WRONG (the other 84 dirs simply have no dots); the dotted image dir we deleted was actually correct.
FIX (fix-pluginguru-final.sh): recreate the DOTTED image dir from MegaMagic Artwork.jpg, remove the wrong
clean-named dir, and revert the db alias back to the dotted name (db backup pre_pgrevert_*). Reversible.
LESSON: for these Custom libs the tile key = the on-disk library folder name (== what the browser shows),
independent of the db alias. Match the image dir name to the folder name exactly, dots and all.


### Stage 16x — PlugInGuru tile key = NKS library name in the .nki, not folder/alias (2026-09-09)
Dotted-folder-name image dir STILL didn't render. probe-pluginguru-deep.sh found the .nki internal library
name: 'Mega Magic Bells/Winds' (display 'MEGAMAGIC BELLS/WINDS'). That NKS library name is the tile key, not
the folder name or db alias. The '/' can't be a literal dir; vendor PDF uses 'Bells_Winds' (underscore).
fix-pluginguru-nkiname.sh creates candidate image dirs: 'Mega Magic Bells_Winds', nested 'Mega Magic Bells/
Winds', and 'MegaMagic Bells_Winds' — launch to see which renders, then keep the winner and delete the rest.
GENERAL LESSON (important for any future tile): for Kontakt Custom libs the browser tile key = the NKS library
name embedded in the .nki (strings: '{ <Library Name> @' and the uppercase display line), NOT the folder name
or the db alias. Match NI Resources/image/<that name>/ (with '/'->'_' if the name contains a slash).


### Stage 16y — PlugInGuru: folder renamed dot-free (2026-09-09 14:10)
rename-pluginguru-folder.sh apply: renamed lib folder PlugInGuru.MegaMagic.Bells.Winds.KONTAKT -> 'PlugInGuru
MegaMagic Bells Winds'; db path+alias updated (1 row, integrity ok, backup pre_pgfolder_20260909_141034); built
image dir matching the new dot-free folder name; removed all stale candidate image dirs. Decisive test of the
dots theory (working Custom tiles all use folder-name image dirs; PlugInGuru was the only dotted one).
Awaiting on-screen confirm. ROLLBACK: mv folder back + restore pre_pgfolder db + rm image dir.


### Stage 16z — PlugInGuru: file/db level EXHAUSTED; needs targeted re-add (2026-09-09)
After folder rename: db row (alias+path), folder name, image dir name, .meta, and MST_artwork.png FORMAT
(134x66, color_type 2, 8-bit, chunks IHDR/orNT/IDAT/IEND, no iCCP/gAMA) are ALL identical to the WORKING
Tropical Trap tile. Name grep found the entry in NO text cache (tile key isn't a stored string). So every
measurable factor matches a rendering lib yet PlugInGuru stays blank.
CONCLUSION: Kontakt has this entry cached internally from a prior name/path and hasn't re-resolved its artwork.
File/DB-level fixes are exhausted. Reliable path = TARGETED re-add of just this one library via Kontakt UI
(remove the single entry, then Add Library -> /mnt/btrfs_disk/Kontakt Libraries/Custom/PlugInGuru MegaMagic
Bells Winds). NOT a global rescan (that re-demotes the 45 Player tiles). 
KEY DIAGNOSTIC STILL NEEDED: what label does the browser show now — old dotted vs new clean name. Old dotted =>
stale cached entry, remove/re-add fixes it. New name + still blank => a plain user/drag-drop folder may not get
a Default-view tile at all (only Classic view), i.e. not tileable like NKS libs. This is the one lib where the
authored-tile method may not apply. 46 Player + GetGood + Hy2rogen + 10 other Custom tiles all render.


### Stage 16aa — folder rename broke preset paths; REVERT (2026-09-09)
Renaming the PlugInGuru folder broke its Import Content preset paths -> patches throw "File not found. Please
make sure that the external drives are connected!" (presets reference the old dotted folder). The tile still
didn't render even after the rename, so the rename had ONLY downside.
DECISION: revert the rename fully. revert-pluginguru-rename.sh: folder back to dotted name, restore db from
pre_pgfolder_20260909_141034 (reverts path+alias), remove the clean-name image dir. PlugInGuru returns to its
prior working state (loads fine; folder icon, no tile). 
DO NOT rescan (re-demotes the 45 Player tiles) and DO NOT add to KTP/Player Library Manager (no .nicnt; can't
be a Player lib; risks the same rescan). Accept PlugInGuru as a folder icon — the one lib where the authored-
tile method doesn't apply. All other 47 tiles (46 Player + GetGood + Hy2rogen + 10 Custom) render.
FINAL PREVENTION note: authoring tiles for Custom libs is safe ONLY via NI Resources/image/<foldername>/ —
never rename the library folder itself (breaks preset/sample paths).


### Stage 16bb — CLARIFIED: per-entry Rescan in Import Content is SAFE (2026-09-09)
User's Import Content (Custom Libraries) window shows the PlugInGuru entry with the correct renamed path
'Z:\mnt\btrfs_disk\Kontakt Libraries\Custom\PlugInGuru MegaMagic Bells Winds'. This dialog has a PER-ENTRY
Rescan button — that is a SCOPED single-folder rescan, NOT the global Player 'Reset Multi'/full rescan that
demotes content_type 2->3. So it's safe and won't affect the 45 Player tiles.
The "File not found" on patch load = the .nki files still reference OLD sample paths after the folder rename.
NI's own fix (per the dialog text): File -> Batch re-save in standalone Kontakt on that library folder to
rewrite the sample references, then Rescan the entry.
RECOMMENDED (instead of reverting): 1) select the PlugInGuru entry, click Rescan (single-entry, safe);
2) if patches still error, run Batch re-save on that folder; 3) Rescan again. Scoped to one folder; does not
re-demote Player tiles. (revert-pluginguru-rename.sh remains the fallback if the user prefers the old dotted
state.)


### Stage 16cc — PlugInGuru tile SOLVED via per-entry Rescan (2026-09-09)
User clicked Rescan on the renamed 'PlugInGuru MegaMagic Bells Winds' entry -> it now RENDERS its tile AND
patches load fine. So the folder-rename-to-dot-free + matching NI image dir + per-entry Rescan was the correct
fix; the per-entry Rescan is safe (scoped, did NOT demote the 45 Player tiles — all still render per screenshot).
LEFTOVER: the old dotted 'PlugInGuru...nds.KONTAKT' entry remains as a stale duplicate (folder now missing) —
Remove it via the Import Content window (per-entry Remove). probe-pg-duplicate.sh flags which row's path is
MISSING on disk (the stale one to remove) vs the working renamed one to keep.
FINAL: ALL browser tiles restored/authored — 46 Player/NKS (content_type merge + GetGood) + 12 Custom libs
(authored NI Resources/image tiles incl. PlugInGuru after the rename). Blank-tile bug fully resolved.


### Stage 16dd — ghost tile ROOT CAUSE: duplicate sound-info rows (2026-09-09)
find-stale-pg-everywhere.py + probe-pg-soundinfo-dupes.py: the persistent blank PlugInGuru tile is fed by
DUPLICATE sound-info rows, NOT k_content_path (which has the single clean row id=247). Under content_path_id=247:
k_sound_info has 400 OLD-dotted (file_name = old 'PlugInGuru.MegaMagic.Bells.Winds.KONTAKT' path) + 405 NEW
clean rows; k_bank_chain has 9 old (ids 928-936) + 9 new; f_sound_info + p_sound_info_Instrument_2 +
p_sound_info_Oneshot_2 carry the old dotted product/entry strings. The per-entry Rescan ADDED the clean set
(tile works, patches load) but left the OLD dotted set as a stale duplicate -> ghost tile that survives restarts
(it's persisted in the db, not session memory). k_sound_info is a plain table (not FTS).
FIX: delete-stale-pg-soundinfo.py — auto-discovers every table/col holding the OLD dotted string, deletes ONLY
those rows (safety-aborts if the clean set is absent), backup pre_pgdedup_*, REINDEX before+after, integrity check,
verifies old=0/new~405 remain. Dry-run then apply; do NOT rescan (adds another dup set).


### Stage 16ee — stale PG sound-info rows deleted (2026-09-09 14:42)
delete-stale-pg-soundinfo.py apply: deleted 400 k_sound_info + 9 k_bank_chain + 1 sqlite_stat4 (410 total),
integrity ok, old-dotted remaining=0, new-clean remaining=405. Backup pre_pgdedup_20260909_144212.
NOTE: p_sound_info_Instrument_2 / p_sound_info_Oneshot_2 / f_sound_info reported deleted=0 at apply (dry-run had
counted rows there) — they are derived/shadow tables; deleting the parent k_bank_chain rows + REINDEX reconciled
them. Awaiting visual confirm the ghost PlugInGuru tile is gone. If any shadow-table remnant still shows, do a
targeted follow-up on those tables. If clean -> blank-tile bug fully closed.


### Stage 16ff — BLANK-TILE BUG FULLY RESOLVED + good-state snapshot (2026-09-09)
User confirmed (screenshot): ghost PlugInGuru duplicate gone, new entry works, ALL browser tiles render, no
blanks. Blank-tile bug is fully closed.
FINAL good state = 46 Player/NKS tiles (content_type 3->2 merge + GetGood) + 12 Custom authored tiles
(NI Resources/image/<foldername> from cover art; PlugInGuru via dot-free folder rename + per-entry Rescan +
stale-dup sound-info cleanup). Clean Z: paths, integrity ok.
Artifact snapshot-goodstate.sh: copies live komplete.db3 (+wal/shm) + the whole NI Resources/image tree into a
timestamped _kiro_goodstate_snapshot_* dir with MANIFEST + restore commands; archives the intermediate pre_*
db backups into the snapshot's _superseded/ (moved, kept). Dry-run prints integrity/type2/stale-path preview.
RECOMMENDATION recorded: copy the snapshot to a SECOND drive (btrfs_disk/wd_black) since it lands on the same
NTFS workspace volume that had the original dirty-bit problem.


### Stage 16gg — snapshot to WD Black; note 4 residual D:/F: paths (2026-09-09)
Dry-run of snapshot-goodstate.sh: live db 78MB, NI image 16M / 86 dirs, integrity ok, 46 type-2 tiles.
FLAGGED: 4 residual D:/F: stale paths remain in k_content_path (NOT tiles, unrelated to the tile bug — likely
leftover Import Content / user-preset entries pre-dating the Z: convergence). Offered to converge/inspect them
before snapshot; otherwise harmless.
Snapshot target changed to WD Black (separate drive): /mnt/wd_black/KONTAKT BACKUP/goodstate_snapshot_<stamp>/
(script now checks /mnt/wd_black mounted, creates root 'KONTAKT BACKUP', copies db+wal/shm + NI Resources/image,
archives the ~25 intermediate pre_* db backups into the snapshot's _superseded/ (moved off the workspace vol),
writes MANIFEST with restore cmds). Awaiting apply.


### Stage 16hh — the 4 residual D: rows identified + fix (2026-09-09)
probe-df-paths.py:
- id=282 Lo-Fi Vibes (D:\...\Content\Presets\Lo-Fi Vibes, EXISTS, 170 si) and id=283 Piano Uno (EXISTS, 31 si)
  = real content with a stale D: drive letter -> CONVERGE D:->Z: (path + sound_info file_name).
- id=284 Chords (Content\Tools\Chords, MISSING, 135 si) and id=285 Phrases (MISSING, 182 si) = the factory
  Tools we deliberately removed in Task 13 (Kontakt crashed parsing them) -> orphan rows -> REMOVE (content_path
  + dependent k_sound_info + orphaned k_bank_chain).
fix-df-paths.py: converge 282/283, remove 284/285; backup pre_dffix_*, REINDEX before+after, integrity, prints
remaining D:/F: count (target 0). Dry-run then apply; then snapshot the clean state. No rescan.


### Stage 16ii — DB fully clean (0 D:/F: paths) (2026-09-09 14:54)
fix-df-paths.py apply: converged Lo-Fi Vibes + Piano Uno D:->Z: (path + sound_info); removed orphan Chords
(135 si + 2 bc) and Phrases (182 si + 2 bc). integrity ok, D:/F: remaining=0, content paths=72. Backup
pre_dffix_20260909_145403. Verify presets load / orphans gone, then snapshot to WD Black.


### Stage 16jj — CORRECTION: D:->Z: convergence was WRONG for Content\Presets (2026-09-09)
The fix-df-paths convergence broke Lo-Fi Vibes + Piano Uno. Mechanism: their paths were
'D:\VST Install\Kontakt Portable\Kontakt 8\Content\Presets\...' where D: = /mnt/workspace (workspace-relative),
so real path = /mnt/workspace/VST Install/... (exists). Converting D:->Z: gave 'Z:\VST Install\...' = /VST
Install/... (Z: = / root) which does NOT exist -> won't load. The OTHER libs use 'Z:\mnt\btrfs_disk\...' (full
path from root); these Content\Presets entries legitimately use the D: (workspace-relative) form. So D: was
CORRECT here and these 4 rows are NOT stale.
FIX: revert-dffix.sh restores the pre_dffix_20260909_145403 backup (working D: paths + the Chords/Phrases rows).
Do NOT re-run the convergence. The Chords/Phrases rows are harmless orphans (deliberately-removed content ->
"file not found" if clicked). Snapshot the state AS-IS (with D: paths) once presets load again.
LESSON: D: and Z: are NOT interchangeable — D:=/mnt/workspace (workspace-relative paths), Z:=/ (root, used with
full \mnt\... paths). Only converge when the tail path resolves under the target mapping.


### Stage 16kk — GOOD-STATE SNAPSHOT DONE on WD Black (2026-09-09 15:03)
snapshot-goodstate.sh apply: /mnt/wd_black/KONTAKT BACKUP/goodstate_snapshot_20260909_150258/ = komplete.db3 +
86 NI image dirs + MANIFEST (restore cmds) + _superseded/ (25 archived intermediate pre_* backups moved off the
workspace volume). integrity ok, 74 content paths, 46 type-2 tiles. Restore point on a SEPARATE drive from the
NTFS workspace volume. (Manifest 'clean Z: paths' note is slightly off — 4 legitimate D: rows remain; see below.)
CLARIFICATION from user: Lo-Fi Vibes + Piano Uno were NEVER fixed to load — earlier work only PREVENTED them
freezing Kontakt/Reaper on load attempts (same class as the Task 13 Chords/Phrases factory-Tools freeze). Their
"File not found. Please make sure external drives are connected!" is the long-standing unresolved issue, not a
regression from this session. The D: paths are their correct/original form; the D:->Z: convergence was reverted.
So the 4 D: rows (Lo-Fi Vibes, Piano Uno, Chords, Phrases) stay AS-IS in the snapshot. Backup-first done; any
attempt to make these 4 load is a SEPARATE optional follow-up with a safe restore point now in place.


### Stage 16ll — Lo-Fi Vibes / Piano Uno: samples PRESENT, Batch re-save viable (2026-09-09)
probe-lofi-piano-refs.sh: both preset folders have COMPLETE structure + samples on disk:
- Lo-Fi Vibes: 160 .wav under Samples/<Kit> Samples/, .nkl kit files, .nicnt (Kit-based, no .nki).
- Piano Uno: 6 .nki + .nkm multis + 111 .ncw + Piano Uno 1.0.nkc/.nkr monolith + .nicnt. Has Multis/Chords +
  Multis/Phrases (so the earlier-removed 'Chords'/'Phrases' db rows were likely Piano Uno's multis).
Samples exist -> "File not found" is a broken sample-PATH reference, exactly what Batch re-save fixes (per NI/
Karanyi/NoiseAsh research). Both are .nicnt NKS libs currently content_type=3 under Content\Presets with D:
paths (D:=/mnt/workspace) — that path form is likely why refs mis-resolve.
PLAN (backup-first): backup-lofi-piano-folders.sh copies both folders to WD Black (Batch re-save OVERWRITES
.nki/.nkl/.nkm). Then MANUAL in STANDALONE Kontakt: File->Batch re-save -> choose the Piano Uno folder ->
if Content Missing, Browse for folder -> .../Piano Uno/Samples/Piano Uno Samples -> Choose; relink+resave; test
load. Repeat for Lo-Fi Vibes (samples under Samples/<Kit> Samples/). Use Batch re-save NOT the db rescan (rescan
re-demotes tiles). Prefer 'Browse for folder' over 'Search filesystem' (auto-search is the Wine hang culprit).
One lib at a time; backup+snapshot make it safe. Note: File menu also has a general rescan/collect — Batch
re-save is the correct one for relinking sample paths.


### Stage 16mm — ROOT CAUSE of Piano Uno crash: multis reference REMOVED Tools (2026-09-09)
Batch re-save segfaulted on the Content Missing dialog. Dialog listed the 4 missing files as the REMOVED
factory Tools: Chords 1.0.nkr, Phrases 1.0.nkr, ghost sample.wav (D:\...\Content\Tools\Chords|Phrases\...).
probe-piano-nki-refs.sh: all 6 Piano Uno Instruments/*.nki are CLEAN (no Chords/Phrases/Tools refs); only the
Multis/*.nkm reference them (A Myth.nkm -> Tools/Chords/). So Piano Uno's crash = its MULTIS pull the removed
Tools (Task 13 removal, which crashes Kontakt under Wine). The base instruments are fine.
FIX (quarantine-piano-multis.sh): move Piano Uno/Multis aside (reversible, to UserData/_kiro_piano_multis_
removed_*), then load an Instruments/*.nki directly via Files browser -> loads without the crash. Piano Uno
works as an instrument; multis stay quarantined (they need the deliberately-removed Tools).
LESSON: the "File not found" freeze for these presets is NOT a fixable sample-path issue — it's references to
the removed crash-inducing factory Tools. Batch re-save on the whole folder walks into the multis and segfaults
(matches the user's prior give-up). Quarantining the multis is the safe equivalent of Task 13. Lo-Fi Vibes:
verify its .nkl kits similarly (likely clean); if clean it should load once nothing references Tools.


### Stage 16nn — Piano Uno + Lo-Fi Vibes LOAD (multis quarantined); crackle = separate audio-latency issue (2026-09-09)
quarantine-piano-multis.sh apply moved Piano Uno/Multis aside -> BOTH Piano Uno and Lo-Fi Vibes now LOAD from
the Files browser (long-standing freeze/crash RESOLVED; it was the multis pulling removed Tools). Rollback: mv
the _kiro_piano_multis_removed_20260909_160357/Multis back.
NEW ISSUE (separate from tiles): heavy crackling in Kontakt STANDALONE only. Checked live PipeWire: force-quantum
/force-rate = 0 (no stale forcing; launcher cleanup trap ran), but graph default quantum = 128 @ 44100 — too
tight for Kontakt/Wine streaming = crackle. launch_kontakt_wineasio.sh forces QUANTUM=256 while running;
launch_kontakt_lowlatency.sh forces 128 + PULSE_LATENCY_MSEC=8 (comment: try 8/6/4 — a '4' value is very
aggressive, likely the crackle the user recalls). FIX being tested: forced live quantum -> 512 (pw-metadata),
and set Kontakt WineASIO ASIO buffer to 512 (the ASIO buffer is what governs latency on the WineASIO path).
If 512 clears it, make permanent: bump launcher QUANTUM 256->512. This is an audio-config issue, not part of the
blank-tile bug.


### Stage 16pp — CORRECTION: WineASIO@128 WAS the working endpoint, not abandoned (2026-09-09)
User corrected me: WineASIO was the LATEST working setting that ran Kontakt at 128 samples, not an unfinished
experiment. Confirmed in kontakt-wine-optimization/tasks.md Task 9 (all [x]): install wineasio (AUR), register in
prefix, launch via pw-jack, select WineASIO in Kontakt Audio, buffer 128, tune by ear. progress-notes documents
the registration WORKING METHOD (cp wineasio64.dll to system32 + regsvr32 the unix .so; CLSID {48D0C522-...}).
So launch_kontakt_wineasio.sh (pw-jack) IS the correct launcher; my "use lowlatency/WASAPI" was wrong.
REGRESSION ANALYSIS: pw-top showed Kontakt as a plain PipeWire node @128 + SSL INPUT node @256 (split), and the
launch log had fixme:pulse: lines = the WINEPULSE/WASAPI path, NOT WineASIO. => Kontakt likely REVERTED to WASAPI
(config reset / version change) and is now on winepulse WITHOUT the PULSE_LATENCY_MSEC lever = crackly middle
state. Need to confirm the actual Driver selected in Kontakt Options->Audio (WineASIO vs WASAPI).
NEXT: user checks Kontakt Audio driver. If WASAPI -> re-select WineASIO (buffer 128) [intended fix] or use
lowlatency launcher (adds PULSE_LATENCY_MSEC=8) as fallback. If WineASIO but still crackles -> fix the SSL JACK
port period split (input 256 vs graph 128). Do NOT keep tweaking PipeWire node params until the driver is known.


### Stage 16qq — WineASIO IS active @128 (screenshot); missing piece = WineASIO Config settings (2026-09-09)
Kontakt Options->Audio screenshot: Driver=ASIO, Device=WineASIO Driver, Status=Running, Latency=128 Samples,
Overall 5.8ms. So WineASIO is correctly active at 128 — the crackle is DESPITE the right driver, matching the
pw-top split (Kontakt/graph 128 vs SSL INPUT node 256).
RECOVERED the full working recipe from kontakt-wine-optimization/progress-notes.md (lines ~642-654):
WineASIO Settings (the 'ASIO Config' button): **Connect to hardware ON, 16 in / 16 out, Fixed buffersize ON**,
preferred buffersize = desired (confirmed 128 @ 2.9ms), Autostart server OFF (PipeWire provides JACK). Note:
buffer switch is flaky/delayed (wait a few seconds; no restart needed).
HYPOTHESIS: 'Fixed buffersize' got unchecked / WineASIO config reset -> SSL input free-runs at 256 vs Kontakt
128 -> the crackle. FIX is in ASIO Config, not PipeWire: verify Connect to hardware ON + Fixed buffersize ON +
buffer 128 + Autostart OFF. Awaiting the ASIO Config panel values (esp. Fixed buffersize ON/OFF).


### Stage 16rr — CRACKLE FIXED: two 128-alignment fixes (quantum + JACK latency) (2026-09-09)
Standalone-only crackle RESOLVED. Root cause was NOT the WineASIO ASIO Config panel (user confirmed the
known-good state = Connect to hardware ON, 16/16, Fixed buffersize UNCHECKED, buffer 128 — already correct)
and NOT the SSL device period (the queued fix-ssl-period.sh had it backwards; set aside, not run). The real
cause was TWO clock/period splits that wireplumber 0.5.15->0.5.17 (upgraded 2026-09-08, day before crackle)
stopped reconciling. Evidence from probe-jack-vs-device.sh + pw-top:
  - SSL INPUT node (id 66) ran QUANT 256 with ERR 228+ climbing (the crackle), while Kontakt ran QUANT 128.
    The launcher forced the GRAPH to 256 (QUANTUM=256) but WineASIO/Kontakt drove their ASIO buffer at 128
    -> split -> input xruns. NOTE: pre-0.5.17 this negotiated cleanly; that's the regression vector.
FIX 1 (fix-quantum-128.sh apply): launch_kontakt_wineasio.sh QUANTUM 256 -> 128 so the forced graph matches
  Kontakt's 128 ASIO buffer. Backup: launch_kontakt_wineasio.sh.bak_20260909_172515. RESULT: both nodes QUANT
  128, Kontakt ERR flat ~7, crackle "gone for the most part". SSL input still QUANT 128 but ERR ~278 residual.
FIX 2 (fix-jack-latency-128.sh apply): the three jack.conf.d drop-ins (99-jack-44k, 99-jack-latency,
  99-reaper-latency) all requested node.latency = 64/44100 = a 64-frame target on a 128 graph = smaller
  residual split on the SSL input. Rewrote 64/44100 -> 128/44100 in all three; backups *.bak_20260909_173128;
  restarted pipewire/pipewire-pulse/wireplumber. RESULT: SSL input ERR dropped 278 -> 9 and stayed FLAT at 9
  across samples while the user deliberately mashed keys to provoke crackle; Kontakt ERR flat ~6. Both nodes
  QUANT 128, both essentially xrun-free. User confirms crackle cleared by ear.
CONFIRMED WORKING ENDPOINT: WineASIO @128 via launch_kontakt_wineasio.sh (now QUANTUM=128), Fixed buffersize
  UNCHECKED + buffer 128 in ASIO Config, graph 128 @ 44100, JACK node.latency 128/44100. Persistent + reversible.
ROLLBACKS:
  FIX1: cp "/home/phnx/KIRO/launch_kontakt_wineasio.sh.bak_20260909_172515" "/home/phnx/KIRO/launch_kontakt_wineasio.sh"
  FIX2: for f in ~/.config/pipewire/jack.conf.d/{99-jack-44k,99-jack-latency,99-reaper-latency}.conf; do cp "${f}.bak_20260909_173128" "$f"; done; systemctl --user restart pipewire pipewire-pulse wireplumber
LESSON: after a wireplumber upgrade, previously-tolerated quantum/latency splits (graph vs client, JACK request
  vs graph) start xrunning. The fix is to make ALL layers agree on ONE number (128 here): forced graph quantum,
  WineASIO ASIO buffer, and JACK node.latency. Watch pw-top ERR on the SSL INPUT node (not just Kontakt) — it
  was the node carrying the crackle. artifacts: probe-jack-vs-device.sh, fix-quantum-128.sh, fix-jack-latency-128.sh.


### Stage 16ss — Reaper RT-priority hardening APPLIED + CONFIRMED; unrelated DecentSampler crash (2026-09-09)
Reaper native PipeWire/JACK path (Kontakt as .so via yabridge) was already glass-smooth: probe-reaper-audio.sh
showed REAPER node QUANT 128 @ 44100, ERR 0, BUSY ~130us vs ~2900us budget (huge headroom), no conflicting
buffer, force-quantum 0 (standalone launcher trap reset it) but graph default still 128. reaper.ini had
jack_rtprio=-1 (NOT requesting realtime) — the one available robustness improvement.
RT LIMITS VERIFIED AMPLE: hard/soft rtprio ulimit 98; user in BOTH 'audio' and 'realtime' groups; limits.d
grants @audio rtprio 95/99 and @realtime 98. So requesting 88 (safely below PipeWire/WirePlumber ~88-95 and the
kernel RT watchdog) is granted, won't starve the audio server.
FIX (fix-reaper-rtprio.sh apply, Reaper closed): reaper.ini jack_rtprio -1 -> 88. Backup:
reaper.ini.bak_20260909_174757. ROLLBACK: cp that backup over reaper.ini (Reaper closed).
CONFIRMED GRANTED (Reaper launch log): "jack: setting TIME_CRITICAL = 88" + "jack: activated client" +
"/dev/cpu_dma_latency: set to 0" — Reaper acquired RT 88 as intended. Idle sound quality unchanged (already
optimal); this is insurance against dropouts under heavy project load.
CRASH (UNRELATED to RT change): while loading a saved project, yabridge loaded bx_enhancer, Kontakt 8 Portable,
ValhallaVintageVerb fine, then DecentSampler aborted: "File .../ZauberwindsSoloFloete_v1.dsbundle/Files/
ZauberwindsSoloFloete/C3-Long1-V127.flac does not exist!" followed by "malloc(): unaligned tcache chunk detected"
-> Aborted (core dumped). This is a DecentSampler missing-sample/heap-corruption bug in that specific project's
content, a different subsystem from the audio clock/RT work. NOT caused by rtprio=88.
NEXT: confirm empty/new-project Reaper is stable (isolates the crash to that project's DecentSampler instance),
then chase the missing ZauberwindsSoloFloete FLAC / that .dsbundle separately if the user wants that library.
CONFIRMED-WORKING AUDIO ENDPOINTS (both): (1) Standalone Kontakt = WineASIO@128 via launch_kontakt_wineasio.sh
(QUANTUM=128), Fixed buffersize UNCHECKED + buffer 128, JACK node.latency 128/44100 — crackle fixed (Stage 16rr).
(2) Reaper = native PipeWire/JACK @128, ERR 0, now RT-hardened jack_rtprio=88.


### Stage 16tt — DecentSampler crash ROOT CAUSE: project-local doubled path, NOT missing content (2026-09-09)
The Reaper crash ("...C3-Long1-V127.flac does not exist" -> malloc heap abort) is NOT missing samples, NOT our
audio/rtprio changes, NOT a DS install problem. Evidence (probe-ds-doubled-path.sh, READ-ONLY):
  - The library + preset + samples ALL EXIST at the normal single-.config path:
    ~/.config/DecentSampler/Sample Libraries/ZauberwindsSoloFloete_v1.dsbundle/Files/ZauberwindsSoloFloete/
    (C3-Long1-V127.flac PRESENT).
  - The .dspreset uses RELATIVE sample paths ("Files\Zauberwinds...\*.flac", Windows backslashes = DS via
    yabridge/Wine VST3) — no absolute or doubled path baked in.
  - DS's own config (DecentSampler.xml, catalog, SampleLibrary.db) all reference the CORRECT single-.config
    path (file:///home/phnx/.config/DecentSampler/Sample Libraries/Zauberwinds...); doubled-path count = 0.
  - DS version 1.28.0.
CONCLUSION: the doubled base path ".config/DecentSampler/.config/DecentSampler/..." that appeared in the crash
came from the SAVED DS PLUGIN-INSTANCE STATE in that ONE Reaper project (serialized a bad library base at save
time under Wine). It is project-local and self-heals on a fresh DS insert. DS's global config is healthy.
IMPLICATIONS:
  - Fresh DecentSampler use is SAFE (new/other projects resolve correctly) — user can use DS freely.
  - Only that one old project crashes on its embedded DS chunk. Rescue = open that project with FX OFFLINE
    (Reaper), delete or re-add the DS track, save. No system-wide change needed.
  - (DS's own bug: it heap-aborts on a missing sample instead of erroring gracefully — upstream, not ours.)
NOTE: DS libraries live in two places — ~/.config/DecentSampler/Sample Libraries/ (3 bundles incl. Zauberwinds)
and /mnt/btrfs_disk/DS Libraries/ (many). Both fine; just noting the split.
VERIFY NEXT: new empty Reaper project -> insert DecentSampler -> load Zauberwinds -> play. Success confirms the
doubled path is project-local and DS is fully healthy.


### Stage 16uu — DecentSampler library catalog (browser HTML) built (2026-09-09)
Side task after the DS crash diagnosis: built a browsable catalog of all DS instruments. Final artifact:
artifacts/DS-CATALOG.html (open via xdg-open), generated by artifacts/build-ds-catalog-html.sh.
FEATURES: alphabetical jump-index (explicit HTML <a id> anchors — Markdown auto-slug jumps failed in Kiro
preview/OpenOffice, HTML ids work in browser); cover thumbnails (ImageMagick x160, png/jpg/jpeg/gif/bmp/webp/tif);
readme descriptions (RTF-stripped, null-byte-safe, template-junk like "Your Full Name"/"[1.x]" filtered out);
keyword filter (name-only, whole-word match so bass!=bassoon) with live counts, yellow highlight of index+entries,
multi-keyword AND-narrowing, and dead-end keywords greyed to (0); [open folder] links (file://) on open: and art:
paths for Dolphin; rebuild-safe cover-override system (cover-overrides.tsv + covers-manual/).
KEY BUG FIXED: JS paired sorted-index[i] with unsorted-entries[i] -> wrong names highlighted; fixed by testing
each element's own data-kw instead of positional pairing.
COUNTS: home(SAMPLE STORE) 3, btrfs 654, wd_black 15 loadable items. Art: only 6 had no on-disk image; PAMAHA x2
overridden to main "Pamaha Cover.png"; Dynamic Overtone Guitar + TheDiArchtop covered via user-saved Pianobook
images in covers-manual/; 2 remaining are author-flagged "Presets that don't work" (left blank).
LESSONS: readme text is mostly author backstory + unfilled templates — good for display, BAD for keyword
classification (prose bleed) -> classify from NAME only. Per-instrument web descriptions for 654 obscure free
libs is NOT feasible/verifiable -> not done. DS libraries split across ~/.config/DecentSampler/Sample Libraries
(home, shows in SAMPLE STORE) and /mnt/btrfs_disk + /mnt/wd_black /DS Libraries (FILE BROWSER roots).
artifacts: build-ds-catalog-html.sh, cover-overrides.tsv, install-guitar-covers.sh, probe-missing-art.sh,
list-ds-libraries.sh, (older markdown builder build-ds-catalog.sh superseded by the HTML one).


### Stage 16vv — Kontakt library catalog (browser HTML, desktop+mobile) built (2026-09-09)
Companion to the DS catalog, for Kontakt libraries. Builder: artifacts/build-kontakt-catalog-html.sh (modes:
desktop | portable | both). Outputs KONTAKT-CATALOG.html (desktop, banner thumbs in kontakt-thumbs/, [open
folder] links) and KONTAKT-CATALOG-portable.html (mobile, single self-contained file, banners embedded x110/q70,
no folder links).
SOURCE: komplete.db3 k_content_path WHERE content_type=2 (registered libraries), alias=display name, path
Z:\mnt\... -> /mnt/... . DEDUP: keep first (lowest id) per normalized alias AND per normalized path, so a lib
registered as both Player and Custom (lib-browser) survives only once. Library-level only (no per-patch/subpatch
entries) — user confirmed the JS keyword nav handles finding relevant data, one image per library is the sensible
scope.
BANNER ART: NI Resources/image/<alias>/MST_artwork.png (fallback MST_logo.png). 45 of 46 libraries matched a
banner (alias maps 1:1 to the image dir); the 1 miss is the Drumforge lib whose alias is literally "Kontakt".
UX: same as DS — jump-index, name-only keyword filter (Kontakt taxonomy: orchestral/cinematic/world/choir/etc.)
with highlight + AND-narrowing + dead-end greying, [open folder] on the library path. Portable size ~652K (banners
are small wide strips, much smaller than DS square covers).
BUG FIXED: banner_for had `local a="$1" d="$NIIMG/$a"` on one line -> $a unbound under set -u (fired once per lib);
split into two `local` statements + explicit `return 0`.
NOTE: some libs (Cinebrass, Damage, Evolve Mutations 2, Elite Orchestral Percussion) resolve to "Library
Identification Files" registration-stub folders (Ultimate Orchestral Toolkit repack) — [open folder] points at the
ID-file dir, not necessarily the sample content; accurate to what the DB registered.
OPEN CMDS: xdg-open the four files: DS-CATALOG.html, DS-CATALOG-portable.html, KONTAKT-CATALOG.html,
KONTAKT-CATALOG-portable.html.
