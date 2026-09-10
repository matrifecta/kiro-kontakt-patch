#!/usr/bin/env bash
# probe-tile-resources.sh (READ-ONLY)
# Blank Player tiles DESPITE valid caches (same as working controls). So the cache isn't the issue —
# the tile IMAGE resources or the browser's resource path is. Investigate:
#  1) the image resource trees Kontakt renders tiles from (NI Resources / PAResources), presence + count
#  2) whether a specific blank lib (Middle East K01) has its tile image on disk
#  3) whether the wine prefix now points Kontakt at a DIFFERENT UserData/resources dir than /mnt/workspace
#  4) mtimes — did resources get touched/hidden by the recent churn
set -u
UD="/mnt/workspace/VST Install/Kontakt Portable/UserData"
WPREF="$HOME/.wine"

echo "===== 1) tile image resource trees under UserData ====="
for d in "$UD/NI Resources/image" "$UD/Kontakt 8/PAResources/image" "$UD/PAResources/image"; do
  if [ -d "$d" ]; then
    echo "  [present] $d  ($(find "$d" -maxdepth 1 -mindepth 1 -type d 2>/dev/null | wc -l) library folders, $(find "$d" -iname '*.webp' -o -iname '*.png' 2>/dev/null | wc -l) images)"
  else
    echo "  [absent]  $d"
  fi
done
echo

echo "===== 2) does a KNOWN-BLANK lib (Middle East) have tile art on disk? ====="
find "$UD" -ipath '*image*Middle East*' \( -iname '*.webp' -o -iname '*.png' \) 2>/dev/null | sed 's/^/    /' | head
echo "  vs a WORKING control (Amati Viola):"
find "$UD" -ipath '*image*Amati*' \( -iname '*.webp' -o -iname '*.png' \) 2>/dev/null | sed 's/^/    /' | head
echo

echo "===== 3) where does the prefix think Kontakt's UserData / resources live? ====="
echo "  grep user.reg + system.reg for NI/Kontakt resource or userdata paths:"
grep -aiE 'Native Instruments|Kontakt|UserData|NI Resources|Content Base|ResourcesDir' "$WPREF/user.reg" "$WPREF/system.reg" 2>/dev/null \
  | grep -aiE 'Z:|D:|F:|workspace|UserData|Resources' | head -20 | sed 's/^/    /'
echo

echo "===== 4) is there a SECOND UserData/NI Resources somewhere the reconfigured prefix may use? ====="
find "$HOME/.wine/drive_c" -maxdepth 6 -type d -iname 'NI Resources' 2>/dev/null | sed 's/^/    /'
find "$HOME" -maxdepth 4 -type d -iname 'NI Resources' 2>/dev/null | sed 's/^/    /' | head
echo

echo "===== 5) mtimes: were the resource images touched recently (churn) or old/stable? ====="
find "$UD/NI Resources/image" -iname 'NKS2_software_tile.webp' -printf '%TY-%Tm-%Td  %p\n' 2>/dev/null | sort | tail -5 | sed 's/^/    /'
echo
echo "READ-ONLY. If tile images are PRESENT+readable on /mnt/workspace but tiles still blank, the browser"
echo "needs a display refresh (or the prefix points elsewhere). If images are MISSING for the blank libs,"
echo "that's the gap. Report back."
