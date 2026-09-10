#!/usr/bin/env bash
#
# map-cache-to-library.sh  (READ-ONLY)
#
# We proved the tile ART (PAResources/image/<Name>/MST_artwork.png + NKS2_software_tile.webp)
# is present for BOTH working-tile and folder-icon libs. So the differentiator must be the
# LibrariesCache/*.cache entry. This maps each .cache -> the library name embedded inside,
# so we can list which folder-icon libs HAVE a .cache vs which LACK one.
#
# Method: each .cache is a small sqlite/binary blob; the library name/regkey appears in
# its readable strings. We extract candidate names and match against our lib list.

set -u
CACHE="/mnt/workspace/VST Install/Kontakt Portable/UserData/Kontakt 8/LibrariesCache"

echo "=== each .cache -> recovered name (strings heuristic) ==="
for f in "$CACHE"/*.cache; do
  [ -e "$f" ] || continue
  b=$(basename "$f")
  nm=$(strings "$f" 2>/dev/null \
        | grep -viE 'sqlite|CREATE|TABLE|COLLATE|NULL|NOT|text|INTEGER|index|PRIMARY|shortname|color|PAL|\.nk|_info|^K[0-9A-Za-z]{6,}$' \
        | grep -iE '^[A-Za-z0-9][A-Za-z0-9 &._-]{2,50}$' \
        | sort -u | head -4 | paste -sd' | ' -)
  printf '  %-24s %s\n' "$b" "$nm"
done

echo
echo "=== for each folder-icon lib: is there ANY .cache whose contents mention it? ==="
for n in "Balinese Gamelan" "Cloud Supply" "Middle East" "Mysteria" "Pharlight" \
         "Piano Colors" "Cuba" "East Asia" "Ethereal Earth" "Hybrid Keys" \
         "Session Guitarist" "Analog" "Soul Sessions" "Straylight" "West Africa" \
         "Amati" "Butch Vig" "5Elements"; do
  hit=$(grep -rl "$n" "$CACHE" 2>/dev/null | head -1)
  if [ -n "$hit" ]; then printf '  %-40s HAS .cache -> %s\n' "$n" "$(basename "$hit")"
  else printf '  %-40s NO .cache\n' "$n"; fi
done

echo
echo "READ-ONLY. 'HAS .cache' + folder icon = the .cache exists but Kontakt-on-Wine"
echo "isn't pairing it; 'NO .cache' = tile genuinely needs a cache we don't have."
