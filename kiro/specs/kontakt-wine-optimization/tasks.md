# Implementation Plan

Tasks are ordered by the user's mode strategy: fix and harden the Wine standalone first
(Areas 1-4), then repair the REAPER `.so` path (Area 5). Every mutating step is preceded
by a backup. Progress is validated with before/after failed-lookup measurements.

- [x] 1. Establish baseline and backups
  - [x] 1.1 Create `analyze_kontakt_log.sh` that buckets `WINEDEBUG=+file` failed lookups
    into `db_sidecar`, `resource_image`, `resource_dist_db`, `controller_probe`,
    `library_content`, `other`, and prints per-bucket counts
  - [x] 1.2 Capture a fresh instrumented launch log and record the per-bucket baseline
    into `results/baseline.txt`
  - [x] 1.3 Back up `NI Resources/`, `komplete.db3`, `user_config.db3`, and
    `~/.wine/dosdevices` with timestamped copies; record restore steps
  - _Requirements: 1.1, 1.4, 1.5_

- [x] 2. Diagnose and fix the NI Resources database probing
  - [x] 2.1 Resolve the NI Resources DB paths on disk and inspect existence/size/integrity
    of `categories.db`, `shortname.db`, `color.db`, `Service Center/pal.db`
  - [x] 2.2 Apply the decision matrix (regenerate if missing/zero-byte, `.recover`/delete
    if corrupt, defer to Area 3 drive fix if path doesn't resolve)
  - [x] 2.3 Relaunch instrumented and re-measure the `db_sidecar` bucket vs baseline
  - _Requirements: 1.1, 1.3, 1.4, 1.5_

- [ ] 3. Normalize Wine drive letters and stabilize mounts
  - [ ] 3.1 Scan log/DB for `F:`-only baked content paths; if found, plan reconciliation
    to canonical `D:` instead of keeping stale `F:`->workspace
  - [ ] 3.2 Rewrite `~/.wine/dosdevices`: `D:`=workspace, `E:`=storage, `F:`=wd_black,
    controllers to `L:`/`M:`, remove redundant `S:`; keep `C:`/`W:`/`Z:`
  - [ ] 3.3 Add stable fstab entries (UUID, `ntfs3`, `nofail`, `windows_names`) for the
    three content mounts; verify they mount read-write (fast-startup disabled)
  - [ ] 3.4 Relaunch instrumented and re-measure `controller_probe` and total buckets
  - _Requirements: 2.1, 2.2, 2.3, 2.4_

- [x] 4. Build the automated library scanner
  - [x] 4.1 Write `kontakt_scan.py` (Python 3, stdlib only) with `os.scandir` traversal,
    classification rules, bottom-up dedup, and exclude patterns (iZotope/Nectar/Ozone/RX)
  - [x] 4.2 Emit `player_libraries.tsv`, `custom_libraries.tsv`, `user_presets.tsv`,
    `excluded.tsv`, `summary.txt`, each path in both Linux and Wine-letter form
    (`D:`/`E:`/`F:`)
  - [ ]* 4.3 Add a pytest with a temporary fixture tree (Player lib, loose-`.nki` folder,
    `.nksn`, iZotope folder) asserting correct categorization and dedup
  - [x] 4.4 Run against `/mnt/workspace`, `/mnt/storage`, `/mnt/wd_black`; review outputs
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8_

- [ ] 5. Clean re-registration in Kontakt
  - [ ] 5.1 Remove all Import Content entries (iZotope and unresolved paths especially)
  - [ ] 5.2 Add Custom Libraries and User Presets from scanner TSVs (Wine-letter column)
  - [ ] 5.3 Register Player libraries via Library Manager from `player_libraries.tsv`
  - [ ] 5.4 Relaunch instrumented; run `analyze_kontakt_log.sh`; confirm total failed
    lookups dropped substantially from the ~10,260 baseline; record final numbers
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 1.1, 1.2_

- [x] 6. Persist low-latency PipeWire quantum
  - [x] 6.1 Create `~/.config/pipewire/pipewire.conf.d/10-lowlatency.conf` pinning
    44.1kHz and quantum 128
  - [x] 6.2 Restart PipeWire stack; verify `pw-metadata -n settings` shows quantum 128;
    note how to raise it for heavy projects if xruns occur
  - _Requirements: 5.6, 5.7_

- [ ] 7. Repair the REAPER `.so` (yabridge) path
  - [x] 7.1 Run `yabridgectl status`; confirm the Kontakt Windows plugin path under the
    `~/.wine` prefix and identify what was removed
  - [ ] 7.2 `yabridgectl add` the Kontakt VST dir if missing, then `yabridgectl sync` to
    regenerate the `.so` bridges (the previously skipped step)
  - [ ] 7.3 Rescan plugins in REAPER, load Kontakt, verify content resolves via the shared
    canonical drive letters
  - [ ] 7.4 Document the crash-testing plan (several days, heavy composer projects) and the
    switch/fallback criteria between `.so` primary and standalone backup
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_

- [ ] 8. Finalize and document
  - [x] 8.1 Write a short `README` in the spec dir capturing final drive mapping, launch
    command, scanner usage, latency config, and restore/rollback steps
  - [ ] 8.2 Record before/after load-time and failed-lookup metrics for the record
  - _Requirements: 1.4, 2.4, 4.4_

- [x] 9. Standalone low-latency via WineASIO (escape the winepulse 236 buffer)
  - [x] 9.1 Install `wineasio` from AUR (`paru -S wineasio`); it supports `pipewire-jack`
    (no separate JACK server needed)
  - [x] 9.2 Register the driver in the prefix: `WINEPREFIX=~/.wine wineasio-register`
  - [x] 9.3 Update the launcher to run Kontakt wrapped with `pw-jack` so WineASIO binds to
    PipeWire's JACK (WineASIO expects a JACK server; pw-jack redirects it to PipeWire-JACK)
  - [x] 9.4 In Kontakt Audio panel select **WineASIO** driver; set buffer 128 (editable now)
  - [x] 9.5 Tune buffer down by ear (128 -> 96 -> 64) to lowest xrun-free value; verify with
    pw-top ERR. Optionally confirm kernel PREEMPT for lowest latency (CachyOS likely OK).
  - _Requirements: 5.6, 5.7_
  - _Note: NOT needed for the REAPER `.so` path (Reaper uses PipeWire/JACK natively)._
