#!/usr/bin/env bash
#
# db-rebuild.sh
#
# Clean Kontakt library-DB rebuild for the KTP portable prefix.
# Backs up ALL relevant DB/state files (fresh timestamped backup), then removes
# only the ones that must be regenerated, so Kontakt builds a clean DB on next
# launch with NO stale D:/F: entries and NO stuck Import Content/User-Presets rows.
#
# RUN WITH KONTAKT FULLY CLOSED (and no wineserver). Fully reversible via the backup.
#
set -u

UD="/mnt/workspace/VST Install/Kontakt Portable/UserData"
K8="$UD/Kontakt 8"
STAMP="$(date +%Y%m%d_%H%M%S)"
BK="$UD/_kiro_dbrebuild_backup_$STAMP"

echo "=== Safety check: nothing Kontakt/wine running? ==="
# Match the actual Kontakt EXE or a real wineserver process, and EXCLUDE this
# script/its path (which contains 'kontakt') and the grep/pgrep itself.
if pgrep -fi 'Kontakt 8.exe|wineserver' 2>/dev/null | grep -qvE 'db-rebuild|kontakt-workspace-drive-dirty-fix'; then
    # re-check precisely: list real matches after excluding self
    REAL=$(pgrep -a -fi 'Kontakt 8.exe|wineserver' 2>/dev/null | grep -viE 'db-rebuild|kontakt-workspace-drive-dirty-fix|grep')
    if [ -n "$REAL" ]; then
        echo "ABORT: Kontakt/wineserver still running:"; echo "$REAL"; exit 1
    fi
fi
echo "OK: no real Kontakt/wineserver process."

mkdir -p "$BK/Kontakt 8" "$BK/Shared" "$BK/Service Center"

echo "=== Backing up DB/state files to: $BK ==="
cp -av "$K8/komplete.db3"                  "$BK/Kontakt 8/"        2>/dev/null
cp -av "$K8/user_config.db3"               "$BK/Kontakt 8/"        2>/dev/null
cp -av "$UD/Shared/favorites.db3"          "$BK/Shared/"           2>/dev/null
cp -av "$UD/Service Center/pal.db"         "$BK/Service Center/"   2>/dev/null
# also snapshot LibrariesCache list (not the files) for reference
ls -1 "$K8/LibrariesCache" 2>/dev/null > "$BK/LibrariesCache.filelist.txt"

echo
echo "=== Removing files so Kontakt rebuilds them fresh ==="
# Main library/browser index (stale D:/F: paths, half-scanned crash state)
rm -v "$K8/komplete.db3" 2>/dev/null
# User config incl. the stuck Import Content / User-Presets entries
rm -v "$K8/user_config.db3" 2>/dev/null
# Favorites (NI reset procedure removes this; backed up above)
rm -v "$UD/Shared/favorites.db3" 2>/dev/null
# Stale scan mutex (crash-on-resume culprit), if present
rm -v "$K8/boost_interprocess/01000000/Kontakt 8_scan_mtx" 2>/dev/null
# Stale lock file
rm -v "$K8/lock.lck" 2>/dev/null

echo
echo "=== KEPT (not touched): pal.db (Player-lib registration index), LibrariesCache/, presets/, QuickLoad/ ==="
echo "=== Backup is at: $BK ==="
echo
echo "NEXT: launch Kontakt -> it creates fresh komplete.db3 + user_config.db3."
echo "Then register Player + Custom libs from Z: paths, repoint User Content / Edited Samples / Non-Player base to Z:, and SAVE."
echo
echo "ROLLBACK if needed (Kontakt closed):"
echo "  cp -av \"$BK/Kontakt 8/.\" \"$K8/\" && cp -av \"$BK/Shared/favorites.db3\" \"$UD/Shared/\""
