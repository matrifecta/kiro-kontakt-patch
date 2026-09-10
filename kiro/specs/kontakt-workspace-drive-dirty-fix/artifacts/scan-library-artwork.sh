#!/usr/bin/env bash
#
# scan-library-artwork.sh  (READ-ONLY)
#
# For each fast-drive library folder, report what ARTWORK assets exist on disk:
#   - .nicnt            (Player registration file; may embed artwork ref)
#   - .nkr              (resource container -> holds MST_ARTWORK browser wallpaper)
#   - picture/artwork   (loose PNG/JPG in resources/pictures dirs)
# This tells us which "folder-icon" libraries actually HAVE artwork we could
# potentially use for a tile, vs which genuinely ship none.
#
# Nothing is modified.

set -u
ROOTS=("/mnt/wd_black/Kontakt Libraries" "/mnt/btrfs_disk/Kontakt Libraries")

for root in "${ROOTS[@]}"; do
  [ -d "$root" ] || continue
  for sub in Player Custom; do
    d="$root/$sub"
    [ -d "$d" ] || continue
    while IFS= read -r lib; do
      [ -z "$lib" ] && continue
      p="$d/$lib"
      nicnt=$(find "$p" -maxdepth 2 -iname '*.nicnt' 2>/dev/null | head -1)
      nkr=$(find "$p" -maxdepth 3 -iname '*.nkr' 2>/dev/null | head -1)
      # loose art in resources/pictures
      art=$(find "$p" -maxdepth 4 -type d \( -iname 'pictures' -o -iname 'resources' \) 2>/dev/null \
            -exec find {} -maxdepth 2 -type f \( -iname '*.png' -o -iname '*.jpg' -o -iname '*.jpeg' \) \; 2>/dev/null | head -1)
      flags=""
      [ -n "$nicnt" ] && flags+="nicnt "
      [ -n "$nkr" ]   && flags+="NKR "
      [ -n "$art" ]   && flags+="loosePNG "
      [ -z "$flags" ] && flags="(none)"
      printf '%-55s | %s\n' "$sub/$lib" "$flags"
    done < <(ls -1 "$d" 2>/dev/null)
  done
done
echo
echo "Legend: NKR = resource container (can carry a browser tile); nicnt = Player reg;"
echo "        loosePNG = picture file present; (none) = no artwork asset on disk."
echo "READ-ONLY."
