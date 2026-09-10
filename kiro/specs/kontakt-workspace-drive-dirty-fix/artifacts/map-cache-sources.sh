#!/usr/bin/env bash
#
# map-cache-sources.sh   (READ-ONLY)
#
# Two potential tile sources were found:
#   A) Windows Kontakt LibrariesCache:  /mnt/win_system/.../Native Instruments/Kontakt/LibrariesCache/*.cache
#   B) PAResources image tree:          /mnt/workspace/BACKUP/Kontakt 8/PAResources/image/<Library>/MST_artwork.png
#
# Goal: figure out which .cache belongs to which library (the K-hash names are opaque),
# and which of our folder-icon libs could get a tile from source A or B.
#
# For each .cache we read its readable strings to recover the library NAME embedded
# inside, then compare Windows-cache vs our-Linux-cache by NAME.

set -u
LINUX_CACHE="/mnt/workspace/VST Install/Kontakt Portable/UserData/Kontakt 8/LibrariesCache"
WIN_CACHE="/mnt/win_system/Users/enspi/AppData/Local/Native Instruments/Kontakt/LibrariesCache"
PARES="/mnt/workspace/BACKUP/Kontakt 8/PAResources/image"

name_of() {  # extract a library-ish name from a .cache file's strings
  strings "$1" 2>/dev/null | grep -iE '^[A-Za-z0-9 ._-]{3,60}$' \
    | grep -viE '^(color|shortname|Name|PAL|text|NOT|NULL|COLLATE|CREATE|TABLE|sqlite)' \
    | head -3 | paste -sd' / ' -
}

echo "=== A) .cache present in WINDOWS cache — with recovered name ==="
if [ -d "$WIN_CACHE" ]; then
  for f in "$WIN_CACHE"/*.cache; do
    [ -e "$f" ] || continue
    b=$(basename "$f")
    here=""; [ -e "$LINUX_CACHE/$b" ] && here="(ALSO in Linux cache)" || here="*** MISSING from Linux cache ***"
    printf '  %s  %s\n       name: %s\n' "$b" "$here" "$(name_of "$f")"
  done
else
  echo "  (windows cache not found)"
fi

echo
echo "=== B) PAResources/image library folders that have MST_artwork.png ==="
if [ -d "$PARES" ]; then
  find "$PARES" -maxdepth 2 -iname 'MST_artwork.png' 2>/dev/null \
    | sed -E "s#.*/image/([^/]+)/MST_artwork.png#  \1#" | sort | head -200
  echo "  ... total: $(find "$PARES" -iname 'MST_artwork.png' 2>/dev/null | wc -l) MST_artwork.png"
else
  echo "  (PAResources image tree not found)"
fi

echo
echo "=== C) our folder-icon libs to match against the above ==="
echo "  Balinese Gamelan, Cloud Supply, Middle East, Mysteria, Pharlight, Piano Colors,"
echo "  Play Series Selection, Output Analog Strings, Output Exhale, Red Room Palette,"
echo "  Evolution World Perc, Best Service Orchestra Complete, Session Guitarist Vintage/Picked,"
echo "  East Asia, Cuba, Ethereal Earth, Hybrid Keys, GetGood, + the Custom ones."
echo
echo "READ-ONLY. Paste output; we map cache/artwork -> folder-icon libs, then copy the safe ones."
