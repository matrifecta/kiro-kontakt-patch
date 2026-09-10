#!/usr/bin/env bash
# revert-dffix.sh — the D:->Z: convergence broke Lo-Fi Vibes / Piano Uno. Their paths were
# 'D:\VST Install\Kontakt Portable\...' where D: = /mnt/workspace; converting to Z: (= / root) gave
# 'Z:\VST Install\...' = /VST Install/... which does NOT exist -> won't load. So D: was CORRECT for these.
# Roll back the whole db to the pre_dffix backup (restores working D: paths + the Chords/Phrases rows).
set -u
LIVE="/mnt/workspace/VST Install/Kontakt Portable/UserData/Kontakt 8/komplete.db3"
BK="$LIVE.pre_dffix_20260909_145403"
echo "restore: $BK -> $LIVE"
[ -f "$BK" ] || { echo "ABORT: backup missing"; exit 1; }
if pgrep -x wineserver >/dev/null 2>&1 || pgrep -x reaper >/dev/null 2>&1; then
  echo "*** close Reaper + wineserver -k first ***"; exit 1
fi
cp -av "$BK" "$LIVE" | sed 's/^/  /'
rm -f "$LIVE"-wal "$LIVE"-shm
echo "done. Lo-Fi Vibes + Piano Uno restored to working D: paths."
echo "NOTE: this also restores the 4 D:/F: rows (incl. Chords/Phrases). Do NOT re-run fix-df-paths.py — the"
echo "D->Z convergence is WRONG for these Content\\Presets entries (D: = /mnt/workspace, Z: = / root)."
