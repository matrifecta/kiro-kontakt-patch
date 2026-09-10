#!/usr/bin/env bash
# read-db-robust.sh (READ-ONLY)
# Plain reads of live komplete.db3 via /mnt (ntfs-3g/FUSE) returned 0 bytes while Kontakt reads it fine.
# Likely the file is locked/mmapped by a lingering wineserver, OR FUSE stat quirk. This:
#  1) confirms wineserver is gone (so the file isn't locked),
#  2) copies the db with dd (bytes, not stat), to a LOCAL path, and reports true size,
#  3) opens the local copy with sqlite3 CLI (fallback if python collation errors) to list tables + counts,
#  4) also checks each BLANK library's ContentDir + artwork existence across ALL drives (user's theory:
#     libs added from other disks may have artwork/paths on wd_black/btrfs that don't resolve).
set -u
LIVE="/mnt/workspace/VST Install/Kontakt Portable/UserData/komplete.db3"
TMP="/tmp/komplete_live_copy.db3"

echo "===== 0) wineserver / kontakt still running? (must be closed) ====="
pgrep -a -x wineserver 2>/dev/null | sed 's/^/  /' || echo "  wineserver: not running"
pgrep -af 'Kontakt 8' 2>/dev/null | grep -v grep | sed 's/^/  /' || echo "  Kontakt: not running"
echo "  (if any listed above, run: wineserver -k , then re-run this)"
echo

echo "===== 1) true byte size via dd copy (not stat) ====="
rm -f "$TMP"
dd if="$LIVE" of="$TMP" bs=1M 2>&1 | sed 's/^/  /'
echo "  local copy size: $(stat -c '%s' "$TMP" 2>/dev/null) bytes"
echo "  ls of live (for comparison): $(ls -la "$LIVE" 2>/dev/null | awk '{print $5}') bytes (may be a FUSE artifact)"
echo

echo "===== 2) sqlite3 CLI on the local copy (may hit KOMPLETE collation on some queries) ====="
if command -v sqlite3 >/dev/null 2>&1; then
  echo "  tables:"; sqlite3 "$TMP" ".tables" 2>&1 | sed 's/^/    /'
  echo "  k_content_path count:"; sqlite3 "$TMP" "SELECT COUNT(*) FROM k_content_path;" 2>&1 | sed 's/^/    /'
  echo "  k_content_path schema:"; sqlite3 "$TMP" "PRAGMA table_info(k_content_path);" 2>&1 | sed 's/^/    /'
else
  echo "  (sqlite3 CLI not installed; we'll use python next)"
fi
echo

echo "===== 3) USER THEORY: do blank libs' ContentDir + artwork resolve on current mounts? ====="
CFG="/mnt/workspace/VST Install/Kontakt Portable/UserData/Settings.cfg"
IMG="/mnt/workspace/VST Install/Kontakt Portable/UserData/NI Resources/image"
for name in "Middle East" "Balinese Gamelan" "Straylight" "Soul Sessions" "East Asia" "India" "Piano Colors" "Mass" "Tablas"; do
  cdir=$(awk -v n="Name=sz:$name" 'BEGIN{RS="\r?\n"} $0==n{f=1} f&&/^ContentDir=sz:/{sub(/^ContentDir=sz:/,"");print;exit}' "$CFG" 2>/dev/null)
  lnx=$(printf '%s' "$cdir" | sed -E 's/^[A-Za-z]:\\//; s/\\/\//g'); lnx="/$lnx"
  echo "  $name:"
  echo "     ContentDir: ${cdir:-<none>}  -> $( [ -d "$lnx" ] && echo EXISTS || echo MISSING )"
  echo "     NI Resources art: $( [ -d "$IMG/$name" ] && echo "$(find "$IMG/$name" -type f | wc -l) files" || echo MISSING )"
done
echo
echo "READ-ONLY. Report: local-copy size (is it really 42MB+ not 0?), the tables/count, and any"
echo "ContentDir MISSING among blanks (that would confirm the other-drive path theory)."
