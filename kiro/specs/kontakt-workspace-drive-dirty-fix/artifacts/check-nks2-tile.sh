#!/usr/bin/env bash
#
# check-nks2-tile.sh  (READ-ONLY)
#
# Amati (WORKING tile) has NKS2_software_tile.webp in its PAResources folder. Kontakt 8
# may read the browser tile from that NKS2 .webp directly (newer than the .cache path).
# Compare: do the folder-icon libs HAVE NKS2_software_tile.webp, or only the old PNGs?
# If working libs have the .webp and folder-icon libs lack it, that's the real diff.

set -u
LIVE="/mnt/workspace/VST Install/Kontakt Portable/Kontakt 8/PAResources/image"

check() {
  local n="$1" tag="$2"
  local d="$LIVE/$n"
  if [ -d "$d" ]; then
    local webp="no"; [ -e "$d/NKS2_software_tile.webp" ] && webp="YES"
    local png="no";  [ -e "$d/MST_artwork.png" ] && png="YES"
    printf '  %-40s [%s]  NKS2_tile.webp=%s  MST_artwork.png=%s\n' "$n" "$tag" "$webp" "$png"
  else
    printf '  %-40s [%s]  (no PAResources folder)\n' "$n" "$tag"
  fi
}

echo "=== WORKING-tile controls ==="
check "Amati Viola" "WORKS"
check "5Elements" "WORKS"
check "Butch Vig Drums" "WORKS"
check "Stradivari Violin" "WORKS"

echo
echo "=== FOLDER-ICON libs ==="
for n in "Balinese Gamelan" "Cloud Supply" "Middle East" "Mysteria" "Pharlight" \
         "Piano Colors" "Cuba" "East Asia" "Ethereal Earth" "Hybrid Keys" \
         "Session Guitarist - Electric Vintage" "Analog Dreams" "Soul Sessions" \
         "Straylight" "West Africa"; do
  check "$n" "folder"
done

echo
echo "=== count: how many of the 159 folders have NKS2_software_tile.webp ==="
find "$LIVE" -maxdepth 2 -iname 'NKS2_software_tile.webp' 2>/dev/null | wc -l
echo "READ-ONLY."
