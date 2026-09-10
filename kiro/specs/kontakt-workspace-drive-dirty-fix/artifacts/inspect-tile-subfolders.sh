#!/usr/bin/env bash
# inspect-tile-subfolders.sh (READ-ONLY)
# The image dirs contain a small SUBFOLDER (Amati, Middle, Cloud, Straylight...) + a <Name>.meta file.
# The actual browser-tile asset likely lives INSIDE that subfolder. Recurse fully into working vs blank
# library image dirs and list every file (esp. *.webp/*.png like NKS2_software_tile.webp / MST_artwork),
# and dump the .meta contents. This pinpoints the exact missing/differing tile asset.
set -u
IMG="/mnt/workspace/VST Install/Kontakt Portable/UserData/NI Resources/image"

deep() {  # $1 label  $2 lib
  echo "  === [$1] $2 ==="
  find "$IMG/$2" -type f -printf '    %s  %p\n' 2>/dev/null | sed "s#$IMG/$2/#      #"
  # show the .meta content (usually small text/xml pointing at the tile)
  for m in "$IMG/$2"/*.meta "$IMG/$2"/*/*.meta; do
    [ -f "$m" ] || continue
    echo "    --- meta: $(basename "$m") ---"
    head -c 400 "$m" | tr -d '\000' | sed 's/^/        /'
    echo
  done
}

echo "############ WORKING ############"
deep WORKS "Amati Viola"
deep WORKS "Cloud Supply"
echo "############ BLANK ############"
deep BLANK "Middle East"
deep BLANK "Straylight"
echo

echo "===== global: where do NKS2_software_tile.webp / *tile*.webp actually live? ====="
find "$IMG" -maxdepth 3 -iname '*tile*' 2>/dev/null | sed 's/^/  /' | head -40
echo "  count of NKS2_software_tile.webp under NI Resources/image: $(find "$IMG" -iname 'NKS2_software_tile.webp' 2>/dev/null | wc -l)"
echo
echo "READ-ONLY. We want the exact file the WORKING libs have inside their subfolder that BLANK libs lack."
