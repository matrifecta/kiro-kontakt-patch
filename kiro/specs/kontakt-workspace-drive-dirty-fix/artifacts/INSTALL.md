# Bug A recurrence-prevention — install instructions

These three files prevent the Workspace NTFS volume from being left dirty on an
unclean Linux-side dismount (the confirmed root cause). Run the commands below
yourself — they need `sudo`, which the agent cannot run.

Files (in this `artifacts/` folder):
- `ntfs3-clean-unmount.sh` — write-quiesce helper (unmounts the 3 ntfs3 drives cleanly on shutdown/hibernate)
- `ntfs3-clean-unmount.service` — systemd unit that runs the helper on the way down
- `workspace-mount-check.service` — post-boot alert if `/mnt/workspace` is missing

## Install

Run from this `artifacts/` directory:

```bash
# 1) Helper script -> /usr/local/sbin (root-owned, executable)
sudo install -o root -g root -m 0755 ntfs3-clean-unmount.sh /usr/local/sbin/ntfs3-clean-unmount.sh

# 2) systemd units -> /etc/systemd/system
sudo install -o root -g root -m 0644 ntfs3-clean-unmount.service /etc/systemd/system/ntfs3-clean-unmount.service
sudo install -o root -g root -m 0644 workspace-mount-check.service /etc/systemd/system/workspace-mount-check.service

# 3) Reload + enable
sudo systemctl daemon-reload
sudo systemctl enable --now ntfs3-clean-unmount.service
sudo systemctl enable workspace-mount-check.service
```

## Verify (before the reboot-cycle checkpoint)

```bash
# Units are enabled/active
systemctl status ntfs3-clean-unmount.service --no-pager
systemctl status workspace-mount-check.service --no-pager

# Dry-run the helper WITHOUT unmounting: read the quiesce logic path only.
# (Do not run the real ExecStop now; it would unmount your drives.)
bash -n /usr/local/sbin/ntfs3-clean-unmount.sh && echo "syntax OK"
```

## Optional: login-shell reinforcement (no sudo)

Append to `~/.bashrc` so an interactive shell also warns you:

```bash
mountpoint -q /mnt/workspace || echo "WARNING: /mnt/workspace is not mounted -- Kontakt will not launch."
```

## The checkpoint (Task 4 — must pass before Bug B work)

After installing, do a full **reboot cycle** (a real shutdown + boot, not just
`systemctl`), then check:

```bash
findmnt /mnt/workspace                          # present, ntfs3, rw
dmesg | grep -i ntfs3                            # NO "volume is dirty"
journalctl -t ntfs3-unmount -b -1 --no-pager     # clean-unmount log from the PREVIOUS shutdown
journalctl -t workspace-check -b --no-pager      # "mounted OK" from this boot
```

If `journalctl -t ntfs3-unmount -b -1` shows "unmounted cleanly" for all three
drives and there is no dirty message, recurrence prevention is working and you
can proceed to Stage 2 (Bug B).

## Notes
- `win_system` is intentionally NOT in the helper (it uses ntfs-3g/fuseblk, which self-heals).
- The helper NEVER force-unmounts: if a drive is busy at shutdown it logs a visible
  failure instead, so you never trade one dirty-cause for another.
- Mountpoints used: `/mnt/workspace`, `/mnt/storage`, `/mnt/wd_black` (confirmed live).

---

# Task 4a — dirty-bit origin detectors (detect-then-fix)

Two always-on detectors that pin down WHERE the dirty bit comes from the next
time it appears. Non-invasive; they never modify the NTFS volume.

- `ntfs-dirty-detect.sh` + `ntfs-dirty-detect.service` — reads the NTFS dirty
  flag on `/dev/sdb2` **before** it mounts each boot, logging whether the drive
  ARRIVED dirty (dirtied in the previous session / by an unclean event).
- `ntfs-shutdown-record.sh` — runs in the final shutdown phase; records that an
  ORDERLY shutdown completed. If the drive is later found dirty AND there is no
  shutdown-record for the prior session -> points at a hard power loss / crash.

## Install

Run from this `artifacts/` directory:

```bash
# Boot-time dirty detector
sudo install -o root -g root -m 0755 ntfs-dirty-detect.sh /usr/local/sbin/ntfs-dirty-detect.sh
sudo install -o root -g root -m 0644 ntfs-dirty-detect.service /etc/systemd/system/ntfs-dirty-detect.service

# Final-phase shutdown record (special systemd-shutdown dir)
sudo install -o root -g root -m 0755 ntfs-shutdown-record.sh /usr/lib/systemd/system-shutdown/ntfs-shutdown-record.sh

# Enable the boot detector
sudo systemctl daemon-reload
sudo systemctl enable ntfs-dirty-detect.service
```

## Verify

```bash
# After the NEXT reboot, see the as-found state:
journalctl -t ntfs-dirty-detect -b --no-pager      # "arrived CLEAN" or "arrived DIRTY"
# Shutdown records accumulate here:
sudo cat /var/lib/ntfs-shutdown-record.log 2>/dev/null
journalctl -t ntfs-shutdown-record -b -1 --no-pager
```

## How to read the evidence when the drive next goes dirty

| ntfs-dirty-detect (this boot) | shutdown-record (prior session) | Conclusion |
|---|---|---|
| arrived DIRTY | present (orderly) | dirtied DURING the session (H-D: Kontakt/Wine writer) or by the orderly unmount itself |
| arrived DIRTY | ABSENT | hard power loss / crash — systemd never reached final phase |
| arrived CLEAN | present | all good this cycle |

## H-D experiment (Kontakt/Wine writer) — safe, read-at-unmount

Do this while the drive is clean and idle:

```bash
# PASS 1 — clean exit
# launch Kontakt, use it, close it normally, then:
sudo umount /mnt/workspace && sudo ntfsinfo -m /dev/sdb2 | grep -iE 'dirty|volume flags'
sudo mount /mnt/workspace       # remount (fstab) afterwards

# PASS 2 — unclean exit
# launch Kontakt, then simulate a crash:
wineserver -k                   # or: pkill -9 wineserver
sudo umount /mnt/workspace && sudo ntfsinfo -m /dev/sdb2 | grep -iE 'dirty|volume flags'
sudo mount /mnt/workspace
```

If PASS 2 shows dirty but PASS 1 shows clean -> H-D confirmed. Fix: add
`wineserver -w` (wait for clean exit) to the launcher EXIT trap, and quiesce/kill
wineserver at shutdown BEFORE the clean-unmount runs.
