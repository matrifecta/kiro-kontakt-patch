#!/usr/bin/env bash
#
# probe-nkr-artwork.sh  (READ-ONLY)
#
# For a few Group-1 libraries (have .nicnt + .nkr but show a folder icon), confirm:
#   (a) the .nkr actually contains artwork markers (MST_ARTWORK / wallpaper / picture)
#   (b) there is NO matching LibrariesCache/*.cache for them
# => proves "artwork exists in the container, only the browser .cache is missing".
#
# Also lists the .nicnt SNPID/RegKey so we can see if it's a valid Player reg
# (a tile needs BOTH a valid reg AND a .cache).

set -u
UD="/mnt/workspace/VST Install/Kontakt Portable/UserData"
CACHE="${UD}/Kontakt 8/LibrariesCache"

# a representative Group-1 set (have nicnt+NKR, showed folder icon)
LIBS=(
 "/mnt/btrfs_disk/Kontakt Libraries/Player/Balinese Gamelan Library"
 "/mnt/btrfs_disk/Kontakt Libraries/Player/Cloud Supply Library"
 "/mnt/btrfs_disk/Kontakt Libraries/Player/Middle East Library"
 "/mnt/btrfs_disk/Kontakt Libraries/Player/Pharlight Library"
 "/mnt/btrfs_disk/Kontakt Libraries/Player/Amati Viola Library"   # CONTROL: this one HAS a tile
)

echo "=== existing .cache count in LibrariesCache: $(ls -1 "$CACHE" 2>/dev/null | grep -ci '\.cache$') ==="
echo

for p in "${LIBS[@]}"; do
  name="${p##*/}"
  echo "----- ${name} -----"
  nicnt=$(find "$p" -maxdepth 2 -iname '*.nicnt' | head -1)
  nkr=$(find "$p" -maxdepth 3 -iname '*.nkr' | head -1)
  echo "  nicnt: ${nicnt:-（none)}"
  if [ -n "$nicnt" ]; then
    echo "    .nicnt readable markers:"
    strings "$nicnt" 2>/dev/null | grep -iE 'SNPID|RegKey|Name|Company|Wallpaper|Picture|Artwork' | sed 's/^/      /' | head -12
  fi
  echo "  nkr: ${nkr:-（none)}  ($( [ -n "$nkr" ] && du -h "$nkr" | cut -f1 ))"
  if [ -n "$nkr" ]; then
    echo -n "    NKR artwork markers: "
    strings "$nkr" 2>/dev/null | grep -icE 'MST_ARTWORK|wallpaper|\.png|\.jpg|picture'
    echo "    sample markers:"
    strings "$nkr" 2>/dev/null | grep -iE 'MST_ARTWORK|wallpaper|\.png|\.jpg|picture' | sed 's/^/      /' | head -6
  fi
  echo
done

echo "=== NOTE ==="
echo "If Group-1 libs show NKR artwork markers but the tile is a folder icon, the art"
echo "EXISTS in the container; only the browser LibrariesCache/*.cache is missing."
echo "The known limit: this portable setup has no in-app path that regenerates .cache"
echo "(rescan/re-add/Batch-Re-save did not). Compare against Amati (has a working tile)."
echo "READ-ONLY."
