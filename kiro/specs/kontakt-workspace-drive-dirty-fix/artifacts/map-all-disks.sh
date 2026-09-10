#!/usr/bin/env bash
#
# map-all-disks.sh  (READ-ONLY)
#
# Show what each physical disk holds: partitions, filesystem, mountpoint, size, free space.
# Answers: which M.2 has CachyOS (root/boot), what each SATA disk is doing, and how much
# free space exists. NOTHING changes.

set -u

echo "===== 1) full block tree: disk -> partitions -> fs -> mountpoint -> size ====="
lsblk -o NAME,TRAN,SIZE,FSTYPE,LABEL,MOUNTPOINT 2>/dev/null | sed 's/^/    /'
echo

echo "===== 2) where is CachyOS? (root /, /boot, swap) ====="
findmnt -no SOURCE,TARGET,FSTYPE / /boot /boot/efi 2>/dev/null | sed 's/^/    /'
echo "    swap:"
swapon --show 2>/dev/null | sed 's/^/      /' || echo "      (none)"
echo

echo "===== 3) filesystem usage (mounted) ====="
df -h -x tmpfs -x devtmpfs 2>/dev/null | sed 's/^/    /'
echo

echo "===== 4) map the two NVMe (M.2) drives to their content ====="
for d in nvme0n1 nvme1n1; do
  echo "--- /dev/$d ---"
  model=$(cat /sys/block/$d/device/model 2>/dev/null | xargs)
  echo "    model: $model"
  lsblk -o NAME,SIZE,FSTYPE,LABEL,MOUNTPOINT "/dev/$d" 2>/dev/null | sed 's/^/    /'
  echo
done

echo "===== 5) SATA disks + free SATA capacity summary ====="
for d in sda sdb sdc sdd sde; do
  [ -b "/dev/$d" ] || continue
  model=$(cat /sys/block/$d/device/model 2>/dev/null | xargs)
  size=$(lsblk -dno SIZE "/dev/$d" 2>/dev/null)
  echo "    /dev/$d  $size  '$model'"
  lsblk -o NAME,SIZE,FSTYPE,LABEL,MOUNTPOINT "/dev/$d" 2>/dev/null | tail -n +2 | sed 's/^/        /'
done
echo

echo "READ-ONLY. Report back; I'll tell you which M.2 is CachyOS, what the other holds,"
echo "and whether a big SATA SSD is the right move for Kontakt heavy-stream vs another NVMe."
