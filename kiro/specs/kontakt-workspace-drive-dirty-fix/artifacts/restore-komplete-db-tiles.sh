#!/usr/bin/env bash
#
# restore-komplete-db-tiles.sh
#
# Tiles regressed to folder icons for Player libs whose caches/artwork/paths are IDENTICAL to the
# known-good snapshot. The differentiator = komplete.db3 (the browser DB that decides tiles):
#   live:     78,077,952 bytes, sep 8 21:22  (re-bloated/rewritten during today's Kontakt launches)
#   snapshot: 41,828,352 bytes, sep 7 12:22  (known-good, integrity ok, 74 paths/30060 presets, tiles RENDERED)
# Restore the snapshot komplete.db3 (Kontakt CLOSED), backing up the live one first. Reversible.
#
# Usage: bash restore-komplete-db-tiles.sh          # dry-run (shows sizes + safety checks)
#        bash restore-komplete-db-tiles.sh apply

set -u
MODE="${1:-dryrun}"
UD="/mnt/workspace/VST Install/Kontakt Portable/UserData"
LIVE="$UD/komplete.db3"
SNAP="/mnt/wd_black/kontakt-known-good-20260907_123950/kontakt_userdata/komplete.db3"
STAMP="$(date +%Y%m%d_%H%M%S)"
BK="$UD/_kiro_kompletedb_prewine_${STAMP}.db3"

echo "=== komplete.db3 restore plan ==="
echo "  live (current):  $(ls -la "$LIVE" 2>/dev/null | awk '{print $5" bytes, "$6" "$7" "$8}')"
echo "  snapshot (good): $(ls -la "$SNAP" 2>/dev/null | awk '{print $5" bytes, "$6" "$7" "$8}')"
echo "  backup live -> $BK"
echo

# safety: Kontakt/wineserver must be closed (DB write)
if pgrep -x wineserver >/dev/null 2>&1 || pgrep -fi 'Kontakt 8' >/dev/null 2>&1 || pgrep -x reaper >/dev/null 2>&1; then
  echo "  *** Reaper/Kontakt/wineserver RUNNING — close Reaper and run 'wineserver -k' first. ***"
  [ "$MODE" = apply ] && { echo "  ABORT."; exit 1; }
fi
[ -f "$SNAP" ] || { echo "ABORT: snapshot db missing: $SNAP"; exit 1; }

# also handle WAL/SHM sidecars so a stale WAL doesn't override the restored db
echo "  WAL/SHM sidecars present live?"
ls -la "$LIVE"-wal "$LIVE"-shm 2>/dev/null | sed 's/^/    /' || echo "    (none)"
echo

if [ "$MODE" != apply ]; then
  echo "DRY-RUN. Re-run: bash $0 apply"
  exit 0
fi

echo "=== 1) back up live komplete.db3 (+ any WAL/SHM) ==="
cp -av "$LIVE" "$BK" | sed 's/^/  /'
for sfx in -wal -shm; do [ -f "$LIVE$sfx" ] && cp -av "$LIVE$sfx" "$BK$sfx" | sed 's/^/  /'; done

echo "=== 2) restore snapshot komplete.db3 ==="
cp -av "$SNAP" "$LIVE" | sed 's/^/  /'
# remove stale WAL/SHM so the restored db is authoritative
for sfx in -wal -shm; do [ -f "$LIVE$sfx" ] && { rm -v "$LIVE$sfx" | sed 's/^/  removed stale /'; }; done

echo "=== 3) integrity check (Python + KOMPLETE collation) ==="
python3 - "$LIVE" <<'PY' 2>&1 | sed 's/^/  /'
import sqlite3,sys
db=sys.argv[1]
def kompare(a,b):
    a=(a or "").strip().casefold(); b=(b or "").strip().casefold()
    return (a>b)-(a<b)
con=sqlite3.connect(db)
con.create_collation("KOMPLETE", kompare)
cur=con.cursor()
try:
    print("integrity:", cur.execute("PRAGMA integrity_check").fetchone()[0])
    print("content paths:", cur.execute("SELECT COUNT(*) FROM k_content_path").fetchone()[0])
    print("sound_info rows:", cur.execute("SELECT COUNT(*) FROM k_sound_info").fetchone()[0])
except Exception as e:
    print("check error:", e)
con.close()
PY
echo
echo "ROLLBACK (Kontakt closed): cp -av \"$BK\" \"$LIVE\"  (and restore its -wal/-shm if any), then wineserver -k"
echo
echo "NEXT: launch Reaper (QT_QPA_PLATFORM=xcb reaper), load Kontakt, DON'T press Reset/Rescan — just look."
echo "Tiles for Middle East/Balinese/Straylight/etc. should render as they did at the snapshot."
