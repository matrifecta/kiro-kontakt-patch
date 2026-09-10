#!/usr/bin/env bash
#
# analyze-decentsampler-libs.sh  (READ-ONLY)
#
# Inventory the compressed Decent Sampler libraries and estimate extracted footprint +
# where each should live (fast NVMe/SSD vs light SSD) based on size (a proxy for stream
# demand: bigger multi-sample libs = heavier streaming). Compares totals vs free space
# on the fast drives. NOTHING is extracted or moved.
#
# For .zip we read the TRUE uncompressed size from the archive's central directory (unzip -l),
# which is exact. For .rar/.7z we fall back to a ratio estimate. Audio (wav) barely compresses
# in zip, so extracted size ~= sum of stored uncompressed sizes (accurate for DS libs).

set -u
SRC="/mnt/workspace/Free VST-s/Pianobook/Decent Sampler"
OUT="/home/phnx/KIRO/.kiro/specs/kontakt-workspace-drive-dirty-fix/artifacts/decentsampler-analysis.txt"

{
echo "=================================================================="
echo " Decent Sampler library extraction analysis"
echo " source: $SRC"
echo " date:   $(date)"
echo "=================================================================="
echo

if [ ! -d "$SRC" ]; then
  echo "SOURCE NOT FOUND: $SRC"
  echo "Adjust the path (list what's actually under /mnt/workspace/Free VST-s/Pianobook/):"
  find "/mnt/workspace/Free VST-s/Pianobook" -maxdepth 2 2>/dev/null | head -50
  exit 0
fi

echo "===== 1) archives found ====="
mapfile -t ARCHIVES < <(find "$SRC" -type f \( -iname '*.zip' -o -iname '*.rar' -o -iname '*.7z' -o -iname '*.dsbundle' \) 2>/dev/null | sort)
echo "  count: ${#ARCHIVES[@]}"
echo

# also any already-extracted .dslibrary / folders
echo "===== 1b) already-extracted DS content (dslibrary/folders) ====="
find "$SRC" -maxdepth 2 -type d -iname '*Samples*' 2>/dev/null | sed 's/^/    /' | head
find "$SRC" -maxdepth 2 -type f -iname '*.dspreset' 2>/dev/null | wc -l | sed 's/^/    .dspreset files present: /'
echo

echo "===== 2) per-archive: compressed size + TRUE extracted size ====="
printf "    %-52s %10s %12s\n" "ARCHIVE" "COMPRESSED" "EXTRACTED"
tot_comp=0
tot_extr=0
declare -a HEAVY LIGHT
for a in "${ARCHIVES[@]}"; do
  base="$(basename "$a")"
  csize=$(stat -c '%s' "$a" 2>/dev/null); csize=${csize:-0}
  ext=0
  case "${a,,}" in
    *.zip|*.dsbundle)
      # unzip -l last line "Total" gives uncompressed byte sum
      ext=$(unzip -l "$a" 2>/dev/null | awk 'END{print $1+0}')
      ;;
    *.7z)
      if command -v 7z >/dev/null 2>&1; then
        ext=$(7z l "$a" 2>/dev/null | awk '/^[0-9]/{s=$4} END{print s+0}')
      fi
      ;;
    *.rar)
      if command -v unrar >/dev/null 2>&1; then
        ext=$(unrar l "$a" 2>/dev/null | awk '{if($1 ~ /^[0-9]+$/) s+=$1} END{print s+0}')
      fi
      ;;
  esac
  # fallback if we couldn't read metadata: DS libs are ~lightly compressed wav -> ~1.15x
  if [ "$ext" -le 0 ]; then ext=$(( csize * 115 / 100 )); fi

  tot_comp=$(( tot_comp + csize ))
  tot_extr=$(( tot_extr + ext ))

  # classify: extracted > 3GB = heavy streamer (fast NVMe); else light (SATA SSD ok)
  gib=$(( ext / 1073741824 ))
  cls="light"; [ "$gib" -ge 3 ] && cls="HEAVY"
  printf "    %-52.52s %9sM %11sM  [%s]\n" "$base" "$((csize/1048576))" "$((ext/1048576))" "$cls"
  if [ "$cls" = "HEAVY" ]; then HEAVY+=("$base|$ext"); else LIGHT+=("$base|$ext"); fi
done
echo
printf "    %-52s %9sM %11sM\n" "TOTALS" "$((tot_comp/1048576))" "$((tot_extr/1048576))"
echo "    extracted total ~= $(( tot_extr / 1073741824 )) GiB"
echo

echo "===== 3) placement plan (HEAVY -> fast NVMe/SSD, LIGHT -> SATA SSD) ====="
h=0; for e in "${HEAVY[@]}"; do h=$(( h + ${e#*|} )); done
l=0; for e in "${LIGHT[@]}"; do l=$(( l + ${e#*|} )); done
echo "    HEAVY (>=3GB each) count=${#HEAVY[@]}  total ~= $(( h / 1073741824 )) GiB  -> WD Black NVMe (/mnt/wd_black) or new fast SSD"
echo "    LIGHT (<3GB each)  count=${#LIGHT[@]}  total ~= $(( l / 1073741824 )) GiB  -> btrfs SATA SSD (/mnt/btrfs_disk)"
echo

echo "===== 4) current FREE space on candidate targets ====="
for m in /mnt/wd_black /mnt/btrfs_disk /; do
  df -h "$m" 2>/dev/null | awk 'NR==2{printf "    %-16s size=%s used=%s FREE=%s (%s)\n", "'"$m"'", $2,$3,$4,$5}'
done
echo

echo "===== 5) VERDICT (does it fit as-is?) ====="
free_wd=$(df -B1 --output=avail /mnt/wd_black 2>/dev/null | tail -1); free_wd=${free_wd:-0}
free_bt=$(df -B1 --output=avail /mnt/btrfs_disk 2>/dev/null | tail -1); free_bt=${free_bt:-0}
echo "    HEAVY needs ~$(( h/1073741824 )) GiB; /mnt/wd_black free ~$(( free_wd/1073741824 )) GiB -> $([ "$h" -le "$free_wd" ] && echo FITS || echo 'DOES NOT FIT')"
echo "    LIGHT needs ~$(( l/1073741824 )) GiB; /mnt/btrfs_disk free ~$(( free_bt/1073741824 )) GiB -> $([ "$l" -le "$free_bt" ] && echo FITS || echo 'DOES NOT FIT')"
echo
echo "    NOTE: keep ~10-15% headroom on each drive (SSD/btrfs perform worse when near-full)."
echo "    If either DOES NOT FIT (or leaves <15% headroom), that's the case for the new SATA SSD."
} > "$OUT" 2>&1

echo "Analysis written to:"
echo "  $OUT"
echo
echo "Quick totals:"
grep -E 'extracted total|HEAVY needs|LIGHT needs|FITS|DOES NOT FIT' "$OUT" | sed 's/^/  /'
