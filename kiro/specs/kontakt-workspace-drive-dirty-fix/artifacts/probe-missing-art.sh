#!/usr/bin/env bash
# probe-missing-art.sh  (READ-ONLY)
# For every loadable DS item, report whether ANY image exists in its folder (any format),
# so we know if "no art shown" = wrong format filter, or genuinely no image.
set -u
OUT="/home/phnx/KIRO/.kiro/specs/kontakt-workspace-drive-dirty-fix/artifacts/missing-art.txt"
exec > >(tee "$OUT") 2>&1

roots=( "$HOME/.config/DecentSampler/Sample Libraries" "/mnt/btrfs_disk/DS Libraries" "/mnt/wd_black/DS Libraries" )
total=0; noart=0

for base in "${roots[@]}"; do
  [ -d "$base" ] || continue
  find "$base" -maxdepth 7 \( -iname '*.dsbundle' -o -iname '*.dspreset' \) 2>/dev/null \
    | grep -viE '/__MACOSX/|/\._|/_kiro_nonds_trash_' \
    | grep -viE '\.dsbundle/.*\.dspreset$' \
    | while read -r f; do
        total=$((total+1))
        if [[ "$f" == *.dsbundle ]]; then d="$f"; else d=$(dirname "$f"); fi
        # ANY raster image, any common format
        img=$(find "$d" -maxdepth 3 -type f \
                \( -iname '*.png' -o -iname '*.jpg' -o -iname '*.jpeg' -o -iname '*.gif' \
                   -o -iname '*.bmp' -o -iname '*.webp' -o -iname '*.tif' -o -iname '*.tiff' \) 2>/dev/null \
              | grep -viE '/__MACOSX/|/\._' | head -1)
        if [ -z "$img" ]; then
          echo "NO-IMAGE: $(basename "${f%.*}")   [$f]"
        fi
      done
done

echo
echo "===== image formats present across all DS libraries (extension histogram) ====="
for base in "${roots[@]}"; do [ -d "$base" ] && find "$base" -maxdepth 7 -type f 2>/dev/null; done \
  | grep -viE '/__MACOSX/|/\._' \
  | grep -oiE '\.(png|jpg|jpeg|gif|bmp|webp|tif|tiff)$' | tr 'A-Z' 'a-z' | sort | uniq -c | sort -rn
echo
echo "(NO-IMAGE lines above = libraries with genuinely no raster image in any format)"
echo "report saved: $OUT"
