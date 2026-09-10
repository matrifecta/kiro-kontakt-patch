#!/usr/bin/env bash
#
# wipe-paldb.sh
#
# Removes the stale Player-library registration index (pal.db), which still
# holds old D:\...\Kontakt Vst-i associations, so the next Kontakt launch starts
# with an EMPTY Player registration. Then re-add all Player libs from Z: only.
#
# Backed up first (reversible). RUN WITH KONTAKT CLOSED.
#
set -u

UD="/mnt/workspace/VST Install/Kontakt Portable/UserData"
PAL="$UD/Service Center/pal.db"
STAMP="$(date +%Y%m%d_%H%M%S)"
BK="$UD/_kiro_paldb_backup_$STAMP"

# Safety: no real Kontakt/wineserver (exclude this script's own path)
REAL=$(pgrep -a -fi 'Kontakt 8.exe|wineserver' 2>/dev/null | grep -viE 'wipe-paldb|kontakt-workspace-drive-dirty-fix|grep')
if [ -n "$REAL" ]; then echo "ABORT: Kontakt/wineserver running:"; echo "$REAL"; exit 1; fi
echo "OK: nothing running."

if [ ! -f "$PAL" ]; then echo "pal.db not found (already gone?): $PAL"; exit 0; fi

mkdir -p "$BK"
cp -av "$PAL" "$BK/" && echo "Backed up pal.db -> $BK"
rm -v "$PAL" && echo "Removed pal.db (Player registrations now empty)."

echo
echo "NEXT: launch Kontakt -> Player index is EMPTY. Add ALL Player libs from Z: only:"
echo "  Z:\\mnt\\wd_black\\Kontakt Libraries\\Player\\..."
echo "  Z:\\mnt\\btrfs_disk\\Kontakt Libraries\\Player\\..."
echo "Then Custom via Import Content from the Z: Custom folders; set paths to Z:/D: (not F:); SAVE; clean File->Exit."
echo
echo "ROLLBACK (Kontakt closed): cp -av \"$BK/pal.db\" \"$PAL\""
