#!/usr/bin/env bash
#
# diag-kontakt-hang.sh  (READ-ONLY diagnostic)
#
# Kontakt reported unresponsive. Determine: is it spinning/stuck (CPU pinned + no disk
# activity => safe to force-close) or genuinely loading/streaming (disk delta large)?
# Also list any wine/kontakt processes and stale lock files. NOTHING is killed here.

set -u

echo "===== 1) wine / kontakt / reaper processes (CPU% MEM% state) ====="
ps -eo pid,ppid,pcpu,pmem,stat,etime,comm,args \
  | grep -iE 'kontakt|wine|reaper|yabridge' \
  | grep -v grep \
  | grep -v 'diag-kontakt-hang'
echo

echo "===== 2) disk I/O delta over 3s (are the drives actually reading?) ====="
echo "--- diskstats snapshot A ---"
grep -E ' (sd[a-z]+|nvme[0-9]+n[0-9]+) ' /proc/diskstats | awk '{print $3, "rd_sectors="$6, "wr_sectors="$10}'
sleep 3
echo "--- diskstats snapshot B (after 3s) ---"
grep -E ' (sd[a-z]+|nvme[0-9]+n[0-9]+) ' /proc/diskstats | awk '{print $3, "rd_sectors="$6, "wr_sectors="$10}'
echo "(if rd_sectors/wr_sectors barely changed => no real disk work => it's a spin/stuck)"
echo

echo "===== 3) top CPU-consuming process right now ====="
ps -eo pid,pcpu,pmem,comm --sort=-pcpu | head -6
echo

echo "===== 4) stale Kontakt lock files ====="
for L in \
  "/mnt/workspace/VST Install/Kontakt Portable/UserData/Kontakt 8/lock.lck" \
  "/mnt/workspace/VST Install/Kontakt Portable/UserData/Kontakt 8" ; do
  if [ -e "$L" ]; then
    find "$L" -maxdepth 2 -iname '*.lck' -exec ls -la {} \; 2>/dev/null
  fi
done
echo "(none listed = no stale lock)"
echo

echo "READ-ONLY. Report the numbers back."
echo "If CPU pinned (~100%+) on Kontakt 8.exe AND disk sectors barely move => stuck spin,"
echo "safe to force-close with:  wineserver -k"
