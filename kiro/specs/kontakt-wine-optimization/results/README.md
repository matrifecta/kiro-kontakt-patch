# Kontakt Wine Optimization — Working Reference

Quick reference for the current working setup. Full history in `progress-notes.md`.

## What was fixed (core problem SOLVED)

- **Endless load / "external drives" errors**: root cause was **case-sensitive NTFS
  mounts** (Kontakt probes `pal`, folder is `PAL`). Fixed by mounting the three content
  drives with `nocase` (persisted in `/etc/fstab`).
- **Perpetual re-scanning**: caused by a **stale KTP scan mutex**
  (`UserData/boost_interprocess/01000000/Kontakt 8_scan_mtx`). Deleting it (while Kontakt
  closed) let the index complete and commit. Index now persists across restarts.
- **Junk content**: removed non-Kontakt junk (iZotope/XLN/plugins) from Import Content.
  ~9630 clean presets (was ~51k with clutter).

## Drive mapping (Wine `~/.wine/dosdevices`)

- `C:` -> `../drive_c`, `Z:` -> `/` (KEEP — all 120 libraries resolve via `Z:\mnt\...`)
- `D:` -> `/mnt/workspace`, `F:` -> `/mnt/workspace` (KEEP F: — some presets have baked F: paths)
- `W:` -> `/mnt/win_system`
- Libraries register as `Z:\mnt\workspace\VST Install\Kontakt Vst-i\<name>` (drive-independent).

## Mounts (`/etc/fstab`, kernel ntfs3)

All three content drives use: `ntfs3 rw,uid=1000,gid=1000,dmask=022,fmask=133,nocase,nofail,x-systemd.device-timeout=5`
- workspace UUID=B82064122063D642, storage UUID=D44A1FC54A1FA2F2, wd_black UUID=58EAAC8AEAAC65CA
- Backup: `/etc/fstab.bak_20260901`

## Launch

Normal:
    cd "/mnt/workspace/VST Install/Kontakt Portable/Kontakt 8/x64"
    WINEDLLOVERRIDES="*api-ms-win-core*=b;*msvcp140*=b;*vcruntime140*=b" wine "Kontakt 8.exe"

Low-latency (recommended): shortcut "Kontakt 8 (Low Latency 128)" ->
`~/.local/bin/launch_kontakt_lowlatency.sh`. Forces PipeWire 128 quantum + sets
`PULSE_LATENCY_MSEC` (tune 8->6->4). Makes the action "super tight" even though Kontakt
still displays 236 (Wine winepulse dictates the displayed buffer).

## Audio / latency notes

- Wine routes audio via PulseAudio (winepulse) -> PipeWire pulse emulation. The real
  latency lever is `PULSE_LATENCY_MSEC`, NOT the PipeWire graph quantum.
- PipeWire pinned to 128 @ 44.1kHz: `~/.config/pipewire/pipewire.conf.d/10-lowlatency.conf`.
- WASAPI Exclusive Mode is unavailable (blocked) on this setup.

## Tooling (workspace root)

- `kontakt_scan.py` — classifies libraries (player/custom/presets/excluded). See
  `results/scan/*.tsv` and `results/cleanup-report.md`, `results/import-candidates.md`.
- `analyze_kontakt_log.sh` — buckets `WINEDEBUG=+file` failed lookups (baseline in
  `results/baseline.txt`).
- `launch_kontakt_lowlatency.sh` — the low-latency launcher.

## Backups / restore

See `RESTORE.md`. UserData backups in `_kiro_backup_20260901/` (komplete.db3,
user_config.db3, NI Resources, Service Center, boost_interprocess). Wine drives:
`~/.wine/dosdevices.bak_20260901`. fstab: `/etc/fstab.bak_20260901`.

## Known issues / open items

- **EWQL RA "not installed"**: broken repack (SNPID mismatch A02 vs A05 between presets
  and registration). NOT fixable by config/registration. Needs a matching library package.
  Revisit when adding libraries.
- **Clipping on some presets**: internal to the preset (not system; pw-top ERR 0). Decided
  to stop chasing in standalone; may not occur under Reaper `.so`.
- **NEXT: Reaper `.so`/yabridge repair (Task 7)** — long-term goal. `yabridgectl status`,
  `add` Kontakt VST dir, `yabridgectl sync` (the previously-skipped step), rescan in Reaper,
  crash-test. Keep standalone as fallback.
- Map `E:`/`F:` (storage/wd_black) letters when importing content from those drives.
