#!/usr/bin/env bash
#
# restore-alltiles-db.sh
#
# ROOT CAUSE (proven): a Kontakt rescan/re-add today rewrote 73 libraries' content_type 2 -> 3 in the live
# komplete.db3 (UserData/Kontakt 8/komplete.db3, 78MB), demoting Player/NKS libs (tile) to User/Custom
# (folder icon) => whole browser went folder-icon. The 42MB backup komplete.db3.pre_ewqlra_144329 has those
# libs at content_type=2 (46 tile libs, 208 content paths) = the tiles-working state.
#
# Fix = restore pre_ewqlra over the live db. Kontakt/Reaper CLOSED. Backs up live first (reversible),
# clears stale WAL/SHM, REINDEXes (both dbs had a stale p_sound_info sort index), integrity-checks.
#
# Usage: bash restore-alltiles-db.sh            # dry-run
#        bash restore-alltiles-db.sh apply

set -u
MODE="${1:-dryrun}"
BASE="/mnt/workspace/VST Install/Kontakt Portable/UserData/Kontakt 8"
LIVE="$BASE/komplete.db3"
SRC="$BASE/komplete.db3.pre_ewqlra_144329"
STAMP="$(date +%Y%m%d_%H%M%S)"
BK="$BASE/komplete.db3.pre_tilerestore_${STAMP}"

echo "=== all-tiles DB restore ==="
echo "  source (tiles, type2):  $SRC  ($(stat -c '%s' "$SRC" 2>/dev/null) bytes)"
echo "  live  (blank, type3):   $LIVE ($(stat -c '%s' "$LIVE" 2>/dev/null) bytes)"
echo "  backup live -> $BK"
echo "  live WAL/SHM:"; ls -la "$LIVE"-wal "$LIVE"-shm 2>/dev/null | sed 's/^/    /' || echo "    (none)"
echo

if pgrep -x wineserver >/dev/null 2>&1 || pgrep -fi 'Kontakt 8' >/dev/null 2>&1 || pgrep -x reaper >/dev/null 2>&1; then
  echo "  *** Reaper/Kontakt/wineserver RUNNING — close Reaper + 'wineserver -k' first. ***"
  [ "$MODE" = apply ] && { echo "  ABORT."; exit 1; }
fi
[ -f "$SRC" ] || { echo "ABORT: source missing"; exit 1; }

if [ "$MODE" != apply ]; then echo "DRY-RUN. Re-run: bash $0 apply"; exit 0; fi

echo "=== 1) back up live db (+wal/shm) ==="
cp -av "$LIVE" "$BK" | sed 's/^/  /'
for s in -wal -shm; do [ -f "$LIVE$s" ] && cp -av "$LIVE$s" "$BK$s" | sed 's/^/  /'; done

echo "=== 2) copy pre_ewqlra over live, clear stale WAL/SHM ==="
cp -av "$SRC" "$LIVE" | sed 's/^/  /'
for s in -wal -shm; do [ -f "$LIVE$s" ] && rm -v "$LIVE$s" | sed 's/^/  removed /'; done

echo "=== 3) REINDEX (clear stale p_sound_info sort index) + integrity, via Python+KOMPLETE collation ==="
python3 - "$LIVE" <<'PY' 2>&1 | sed 's/^/  /'
import sqlite3,sys
db=sys.argv[1]
def k(a,b):
    a=(a or "").strip().casefold(); b=(b or "").strip().casefold(); return (a>b)-(a<b)
con=sqlite3.connect(db); con.create_collation("KOMPLETE",k); c=con.cursor()
try:
    c.execute("REINDEX"); con.commit(); print("REINDEX: done")
except Exception as e: print("REINDEX err:", e)
print("integrity:", c.execute("PRAGMA integrity_check").fetchone()[0])
print("content paths:", c.execute("SELECT COUNT(*) FROM k_content_path").fetchone()[0])
print("type2 (tile) libs:", c.execute("SELECT COUNT(*) FROM k_content_path WHERE content_type=2").fetchone()[0])
print("sound_info:", c.execute("SELECT COUNT(*) FROM k_sound_info").fetchone()[0])
con.close()
PY
echo
echo "ROLLBACK (Kontakt closed): cp -av \"$BK\" \"$LIVE\"; rm -f \"$LIVE\"-wal \"$LIVE\"-shm; then wineserver -k"
echo
echo "NEXT: launch Reaper, load Kontakt. DO NOT run Import/Rescan or 'Reset Multi' — a rescan is what"
echo "re-demotes content_type 2->3 and blanks the tiles again. Just use the browser as-is."
