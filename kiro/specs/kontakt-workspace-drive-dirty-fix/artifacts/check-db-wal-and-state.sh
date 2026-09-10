#!/usr/bin/env bash
# check-db-wal-and-state.sh (READ-ONLY)
# On-disk komplete.db3 = 0 bytes, but Kontakt shows a populated browser (in-memory). Before restoring the
# snapshot, check: (a) is Kontakt/wineserver still holding it open? (b) is there a -wal/-shm or a temp/journal
# holding the REAL current data we should recover instead? (c) list every komplete.db3* + recent .db3 anywhere
# under UserData with real sizes, so we pick the best source.
set -u
UD="/mnt/workspace/VST Install/Kontakt Portable/UserData"

echo "===== 0) is Kontakt/wineserver STILL running (holding the db open)? ====="
pgrep -af 'wineserver|Kontakt 8|reaper' 2>/dev/null | grep -v grep | grep -v check-db-wal | sed 's/^/  /' || echo "  none running"
echo "  If Kontakt is OPEN, its real DB is in memory — do NOT kill it yet if we can make it FLUSH (File>save/Collect)."
echo

echo "===== 1) all komplete.db3 * sidecars (wal/shm/journal) with true sizes ====="
for f in "$UD/komplete.db3" "$UD/komplete.db3-wal" "$UD/komplete.db3-shm" "$UD/komplete.db3-journal"; do
  if [ -e "$f" ]; then echo "  $(ls -la "$f" | awk '{print $5" bytes  "$6" "$7" "$8"  "$9}')"; else echo "  (absent) $(basename "$f")"; fi
done
echo

echo "===== 2) any other komplete*.db3 / backups under UserData with real content ====="
find "$UD" -maxdepth 2 -iname 'komplete*.db3*' -printf '  %s bytes  %TY-%Tm-%Td %TH:%TM  %p\n' 2>/dev/null | sort
echo

echo "===== 3) our own prior DB backups (pre_* / _kiro_*) that are non-zero ====="
find "$UD" -maxdepth 2 \( -iname '*komplete*db3*' -o -iname '_kiro*db3*' \) -size +1M -printf '  %s bytes  %TY-%Tm-%Td %TH:%TM  %p\n' 2>/dev/null | sort
echo

echo "===== 4) the snapshot (known-good) for reference ====="
ls -la "/mnt/wd_black/kontakt-known-good-20260907_123950/kontakt_userdata/komplete.db3" 2>/dev/null | awk '{print "  "$5" bytes  "$6" "$7" "$8}'
echo
echo "READ-ONLY. Decision:"
echo "  - If a -wal/-shm or a non-zero komplete*.db3 backup holds today's real state, prefer recovering that."
echo "  - If ONLY the snapshot is non-zero and live is 0, restore the snapshot (nothing newer to lose)."
echo "  - If Kontakt is still OPEN with the good in-memory DB, best is to make IT save/flush before anything."
