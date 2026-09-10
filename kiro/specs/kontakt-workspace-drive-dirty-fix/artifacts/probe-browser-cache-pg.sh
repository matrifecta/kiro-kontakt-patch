#!/usr/bin/env bash
# probe-browser-cache-pg.sh (READ-ONLY)
# db row + image dir + folder now ALL agree on 'PlugInGuru MegaMagic Bells Winds' and match the working
# Tropical Trap pattern exactly, yet it's blank. Suspect a stale browser/layout cache still referencing the
# OLD dotted name. Find any cache/index files that mention the old OR new name.
set -u
UD="/mnt/workspace/VST Install/Kontakt Portable/UserData"
PREFIX="${WINEPREFIX:-$HOME/.wine}"

echo "=== grep UserData for the OLD dotted name and the NEW name in caches/indexes ==="
for name in "PlugInGuru.MegaMagic" "PlugInGuru MegaMagic" "MegaMagic"; do
  echo "--- '$name'"
  grep -rIl --binary-files=text "$name" "$UD" 2>/dev/null | grep -viE '/NI Resources/image/' | sed 's/^/   /' | head -20
done

echo
echo "=== Kontakt browser/db aux files (LibrariesCache, *.db, *.cache, indexes) mtimes ==="
find "$UD" -maxdepth 3 -type f \( -iname '*.db3' -o -iname '*.cache' -o -iname '*.idx' -o -iname '*.xml' \) 2>/dev/null \
  | grep -viE '/NI Resources/image/' | xargs -d '\n' ls -la 2>/dev/null | sed 's/^/  /' | head -40

echo
echo "=== wine-side NI browser caches (Komplete Kontrol / Kontakt prefs) ==="
find "$PREFIX/drive_c" -type f \( -iname '*komplete*.db3' -o -ipath '*Native Instruments*cache*' \) 2>/dev/null | sed 's/^/  /' | head -20

echo
echo "READ-ONLY. If a cache/index file still lists the OLD dotted name, that stale entry is what the browser"
echo "renders (blank, old path). Fix = safely refresh THAT cache (or the specific stale row) without a full"
echo "content rescan. Report which files match."
