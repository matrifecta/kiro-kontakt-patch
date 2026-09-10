# fstab conversion: ntfs3 -> ntfs-3g (Workspace, Storage, WD Black)

**Why:** ntfs3 marks these NTFS volumes dirty under the Wine/Kontakt write workload
(proven: dirty-mark fires on Kontakt use, no mount option prevents it) AND its
metadata exposure breaks Kontakt's library artwork cache validation (blank tiles).
ntfs-3g (FUSE) tolerates the workload and presents metadata Kontakt accepts —
validated: full Kontakt session left the volume clean and all tiles loaded.

All three drives are converted because instrument libraries will later be loaded
in Kontakt from Storage and WD Black too (same workload). `win_system` already
uses ntfs-3g.

## Backup first

```bash
sudo cp /etc/fstab "/etc/fstab.bak_$(date +%Y%m%d_%H%M%S)"
```

## Replace these three lines

OLD (ntfs3):
```
UUID=B82064122063D642 /mnt/workspace ntfs3 rw,uid=1000,gid=1000,dmask=022,fmask=133,nocase,nofail,x-systemd.device-timeout=5 0 0
UUID=D44A1FC54A1FA2F2 /mnt/storage   ntfs3 rw,uid=1000,gid=1000,dmask=022,fmask=133,nocase,nofail,x-systemd.device-timeout=5 0 0
UUID=58EAAC8AEAAC65CA /mnt/wd_black  ntfs3 rw,uid=1000,gid=1000,dmask=022,fmask=133,nocase,nofail,x-systemd.device-timeout=5 0 0
```

NEW (ntfs-3g):
```
UUID=B82064122063D642 /mnt/workspace ntfs-3g rw,uid=1000,gid=1000,dmask=022,fmask=133,big_writes,nofail,x-systemd.device-timeout=5 0 0
UUID=D44A1FC54A1FA2F2 /mnt/storage   ntfs-3g rw,uid=1000,gid=1000,dmask=022,fmask=133,big_writes,nofail,x-systemd.device-timeout=5 0 0
UUID=58EAAC8AEAAC65CA /mnt/wd_black  ntfs-3g rw,uid=1000,gid=1000,dmask=022,fmask=133,big_writes,nofail,x-systemd.device-timeout=5 0 0
```

Notes:
- `nocase` DROPPED — it is an ntfs3-only option; ntfs-3g rejects it. Case handling
  under ntfs-3g validated OK in practice (tiles + libraries resolved). If any
  case-sensitivity lookup issue appears later, add `windows_names` is NOT the fix;
  instead investigate ntfs-3g `ignore_case` (via the `lowntfs-3g` driver) — but only
  if needed.
- `big_writes` ADDED — larger write chunks to narrow the throughput gap vs ntfs3.
- Type is `ntfs-3g` (works with the `mount.ntfs-3g` helper). `nofail` +
  `x-systemd.device-timeout` retained; UUIDs unchanged.

## Apply (edit with a real editor, do not echo)

```bash
sudo nano /etc/fstab        # or: sudo micro /etc/fstab
# replace the three lines above, save

sudo systemctl daemon-reload
# validate without rebooting:
sudo mount -a --fake --verbose
# then actually remount all three:
sudo umount /mnt/workspace /mnt/storage /mnt/wd_black 2>/dev/null
sudo mount /mnt/workspace && sudo mount /mnt/storage && sudo mount /mnt/wd_black
findmnt -t fuseblk
```

## Rollback

```bash
sudo cp /etc/fstab.bak_YYYYMMDD_HHMMSS /etc/fstab && sudo systemctl daemon-reload
```

## Post-change cleanup (optional)

- `ntfs3-clean-unmount.service` is now largely moot (no ntfs3 drives left). It is
  harmless (logs "not mounted, skipping" or unmounts cleanly). Keep or disable:
  `sudo systemctl disable ntfs3-clean-unmount.service`
- `ntfs-dirty-detect.service` still useful as an early-warning even on ntfs-3g; keep.
- `workspace-mount-check.service` still useful; keep.
