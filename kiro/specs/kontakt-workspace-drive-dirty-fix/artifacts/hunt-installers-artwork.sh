#!/usr/bin/env bash
#
# hunt-installers-artwork.sh  (READ-ONLY)
#
# The browser tile is NOT in .nki/.nkr/.nicnt (confirmed) — it's the LibrariesCache
# *.cache built by Native Access/the installer. This hunts every mounted disk for:
#   1. installer archives (.iso/.rar/.zip/.exe/.nicnt installers) for the folder-icon libs
#   2. any pre-existing *.cache files anywhere (a spare LibrariesCache from an install)
#   3. loose tile-like PNGs named after products or "*_info"/"artwork"/"product"
# so we can see if a tile source exists to harvest manually.

set -u
DRIVES=(/mnt/workspace /mnt/wd_black /mnt/btrfs_disk /mnt/storage /mnt/win_system)

echo "=== 1. Any *.cache files ANYWHERE (besides the live LibrariesCache)? ==="
for d in "${DRIVES[@]}"; do
  [ -d "$d" ] || continue
  find "$d" -type f -iname '*.cache' 2>/dev/null | grep -v '/Kontakt 8/LibrariesCache/' | head -40
done
echo

echo "=== 2. Installer archives on any drive (iso/rar/zip/7z/exe) mentioning the libs ==="
for d in "${DRIVES[@]}"; do
  [ -d "$d" ] || continue
  find "$d" -maxdepth 6 -type f \( -iname '*.iso' -o -iname '*.rar' -o -iname '*.r00' \
      -o -iname '*.zip' -o -iname '*.7z' -o -iname '*.exe' -o -iname '*.msi' \) 2>/dev/null \
    | grep -iE 'balinese|cloud supply|middle east|pharlight|mysteria|piano colors|palette|output|session guitarist|play series|evolution|orchestra complete|kontakt|native.?instrument|iso' \
    | head -60
done
echo

echo "=== 3. A 'Native Access'/'Komplete'/download staging area with installers? ==="
for d in "${DRIVES[@]}"; do
  [ -d "$d" ] || continue
  find "$d" -maxdepth 5 -type d \( -iname '*Native Access*' -o -iname '*Native Instruments*' \
      -o -iname '*Komplete*' -o -iname '*Downloads*' -o -iname '*Installers*' -o -iname '*ISO*' \) 2>/dev/null | head -40
done
echo

echo "=== 4. Loose product tile PNGs (product/_info/artwork/MST) on the drives ==="
for d in "${DRIVES[@]}"; do
  [ -d "$d" ] || continue
  find "$d" -maxdepth 6 -type f -iname '*.png' 2>/dev/null \
    | grep -iE '_info|product|artwork|MST_|_tile|_browser|library.?image' | head -40
done
echo
echo "READ-ONLY. Paste output; we'll see if any tile source exists to harvest."
