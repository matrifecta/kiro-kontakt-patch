#!/usr/bin/env bash
# compare-tile-images.sh (READ-ONLY)
# Today's data contradicts the old "blank=no cache" verdict: the blank Player libs HAVE both a .cache
# AND artwork. So the real differentiator must be a SPECIFIC tile-image file present for working libs but
# absent for blank ones. Compare, per library, the exact image filenames in NI Resources/image/<Name>/,
# working (tile shows) vs blank (folder icon).
set -u
IMG="/mnt/workspace/VST Install/Kontakt Portable/UserData/NI Resources/image"

show() {  # $1=label $2=libfolder
  local lib="$2"
  echo "  --- [$1] $lib ---"
  if [ -d "$IMG/$lib" ]; then
    ls -la "$IMG/$lib" 2>/dev/null | awk 'NR>1{print "      "$5"  "$9}'
  else
    echo "      (no folder $IMG/$lib)"
  fi
}

echo "===== WORKING (tile renders) ====="
for l in "Amati Viola" "Butch Vig Drums" "Stradivari Violin" "Cloud Supply"; do show WORKS "$l"; done
echo
echo "===== BLANK (folder icon) ====="
for l in "Middle East" "Balinese Gamelan" "Straylight" "Soul Sessions" "East Asia" "India" "Piano Colors"; do show BLANK "$l"; done
echo

echo "===== KEY DIFF: which tile-image basenames appear in WORKING but not BLANK? ====="
work_tmp="$(mktemp)"; blank_tmp="$(mktemp)"
for l in "Amati Viola" "Butch Vig Drums" "Stradivari Violin" "Cloud Supply"; do
  find "$IMG/$l" -maxdepth 1 -type f -printf '%f\n' 2>/dev/null
done | sort -u > "$work_tmp"
for l in "Middle East" "Balinese Gamelan" "Straylight" "Soul Sessions" "East Asia" "India" "Piano Colors"; do
  find "$IMG/$l" -maxdepth 1 -type f -printf '%f\n' 2>/dev/null
done | sort -u > "$blank_tmp"
echo "  filenames in WORKING set:"; sed 's/^/    /' "$work_tmp"
echo "  filenames in BLANK set:";   sed 's/^/    /' "$blank_tmp"
echo "  present in WORKING but MISSING from BLANK (candidate tile file):"
comm -23 "$work_tmp" "$blank_tmp" | sed 's/^/    >>> /'
rm -f "$work_tmp" "$blank_tmp"
echo
echo "READ-ONLY. If a specific file (e.g. NKS2_software_tile.webp) is present for WORKING libs and absent"
echo "for BLANK ones, THAT is the missing tile asset — and we check if it exists anywhere else to copy in."
