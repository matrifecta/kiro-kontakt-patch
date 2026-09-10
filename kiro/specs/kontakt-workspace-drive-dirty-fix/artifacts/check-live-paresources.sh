#!/usr/bin/env bash
#
# check-live-paresources.sh  (READ-ONLY)
#
# PAResources/image/<Library>/MST_artwork.png is Kontakt's browser-tile art store.
# The BACKUP copy has 158 of them (incl. our folder-icon libs). Question: does the
# LIVE Kontakt install have its own PAResources/image tree, and are the folder-icon
# libs present or missing there? If missing, copying the art folders in from BACKUP
# may restore the tiles (the art store is name-keyed, same as the working tiles use).

set -u
KP="/mnt/workspace/VST Install/Kontakt Portable"
# candidate live PAResources locations
CANDS=(
 "$KP/Kontakt 8/PAResources/image"
 "$KP/PAResources/image"
 "$KP/UserData/Kontakt 8/PAResources/image"
)
BACKUP="/mnt/workspace/BACKUP/Kontakt 8/PAResources/image"

echo "=== locate LIVE PAResources/image ==="
LIVE=""
for c in "${CANDS[@]}"; do
  if [ -d "$c" ]; then echo "  FOUND: $c  ($(ls -1 "$c" 2>/dev/null | wc -l) folders)"; LIVE="$c"; fi
done
[ -z "$LIVE" ] && echo "  none at the usual spots — searching..." && \
  LIVE=$(find "$KP" -maxdepth 4 -type d -path '*PAResources/image' 2>/dev/null | head -1) && echo "  found: $LIVE"

echo
echo "=== BACKUP PAResources/image folder count ==="
echo "  $(ls -1 "$BACKUP" 2>/dev/null | wc -l) folders at $BACKUP"

echo
echo "=== for our folder-icon libs: is the art folder in LIVE? in BACKUP? ==="
for n in "Balinese Gamelan" "Cloud Supply" "Middle East" "Mysteria" "Pharlight" \
         "Piano Colors" "Cuba" "East Asia" "Ethereal Earth" "Hybrid Keys" \
         "Session Guitarist - Electric Vintage" "Session Guitarist - Picked Acoustic" \
         "Analog Dreams" "Soul Sessions" "Straylight" "West Africa" "Amati Viola"; do
  inlive="no"; inbak="no"
  [ -n "$LIVE" ] && [ -e "$LIVE/$n/MST_artwork.png" ] && inlive="YES"
  [ -e "$BACKUP/$n/MST_artwork.png" ] && inbak="YES"
  printf '  %-45s live=%s  backup=%s\n' "$n" "$inlive" "$inbak"
done

echo
echo "=== does a WORKING-tile lib (Amati) have its art in LIVE? (control) ==="
[ -n "$LIVE" ] && ls -la "$LIVE/Amati Viola/" 2>/dev/null | head

echo
echo "READ-ONLY. If working-tile libs HAVE their art folder in LIVE and folder-icon"
echo "libs do NOT, copying the missing folders from BACKUP is the fix to test."
