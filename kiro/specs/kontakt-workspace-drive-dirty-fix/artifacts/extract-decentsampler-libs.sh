#!/usr/bin/env bash
#
# extract-decentsampler-libs.sh
#
# Extract the Pianobook Decent Sampler archives to the fast drives, into a DISTINCT
# "DS Libraries" tree (NOT "Kontakt Libraries"):
#   HEAVY (>=3GB extracted) -> /mnt/wd_black/DS Libraries/     (NVMe)
#   LIGHT (<3GB extracted)  -> /mnt/btrfs_disk/DS Libraries/   (SATA SSD)
#
# Each archive extracts into its own subfolder (named after the archive, sans extension).
# Safe by design:
#   - dry-run by default (shows plan + per-target space math, extracts nothing)
#   - re-checks free space BEFORE each extract; skips (does not fill) a drive if short
#   - skips an archive whose destination subfolder already exists & is non-empty (idempotent)
#   - never deletes the source archives
#
# Requires: unzip (zips/dsbundle/dslibrary), and unrar/7z for .rar/.7z (optional).
#
# Usage:
#   bash extract-decentsampler-libs.sh            # dry-run plan
#   bash extract-decentsampler-libs.sh apply
#   bash extract-decentsampler-libs.sh apply light   # only the light set
#   bash extract-decentsampler-libs.sh apply heavy   # only the heavy set

set -u
MODE="${1:-dryrun}"
ONLY="${2:-all}"     # all | light | heavy

SRC="/mnt/workspace/Free VST-s/Pianobook/Decent Sampler"
DST_HEAVY="/mnt/wd_black/DS Libraries"
DST_LIGHT="/mnt/btrfs_disk/DS Libraries"
HEAVY_BYTES=$(( 3 * 1073741824 ))          # 3 GiB threshold
HEADROOM_PCT=15                            # keep >=15% free on target

LOG="/home/phnx/KIRO/.kiro/specs/kontakt-workspace-drive-dirty-fix/artifacts/extract-decentsampler-run.log"

[ -d "$SRC" ] || { echo "SOURCE NOT FOUND: $SRC"; exit 1; }

# extracted-size reader (exact for zip; ratio fallback otherwise)
extracted_size() {
  local a="$1" ext=0
  case "${a,,}" in
    *.zip|*.dsbundle.zip|*.dslibrary.zip|*.dsbundle|*.dslibrary)
      ext=$(unzip -l "$a" 2>/dev/null | awk 'END{print $1+0}') ;;
    *.7z) command -v 7z >/dev/null 2>&1 && ext=$(7z l "$a" 2>/dev/null | awk '/^[0-9]/{s=$4} END{print s+0}') ;;
    *.rar) command -v unrar >/dev/null 2>&1 && ext=$(unrar l "$a" 2>/dev/null | awk '{if($1 ~ /^[0-9]+$/) s+=$1} END{print s+0}') ;;
  esac
  [ "${ext:-0}" -le 0 ] && ext=$(( $(stat -c '%s' "$a" 2>/dev/null) * 115 / 100 ))
  echo "$ext"
}

# locale-proof: use stat -f (statfs). avail = f_bavail * f_bsize ; total = f_blocks * f_bsize
avail_bytes() {
  local d="$1"; [ -d "$d" ] || d="$(dirname "$d")"
  local bs bav; bs=$(stat -f -c '%S' "$d" 2>/dev/null); bav=$(stat -f -c '%a' "$d" 2>/dev/null)
  echo $(( ${bs:-0} * ${bav:-0} ))
}
size_bytes() {
  local d="$1"; [ -d "$d" ] || d="$(dirname "$d")"
  local bs bt; bs=$(stat -f -c '%S' "$d" 2>/dev/null); bt=$(stat -f -c '%b' "$d" 2>/dev/null)
  echo $(( ${bs:-0} * ${bt:-0} ))
}

subfolder_name() {  # strip archive extensions to a clean folder name
  local b; b="$(basename "$1")"
  b="${b%.zip}"; b="${b%.rar}"; b="${b%.7z}"
  b="${b%.dsbundle}"; b="${b%.dslibrary}"
  echo "$b"
}

do_extract() { # $1 archive  $2 destdir
  local a="$1" d="$2"
  mkdir -p "$d"
  case "${a,,}" in
    *.zip|*.dsbundle.zip|*.dslibrary.zip) unzip -o -q "$a" -d "$d" ;;
    *.7z)  7z x -y -o"$d" "$a" >/dev/null ;;
    *.rar) unrar x -o+ "$a" "$d/" >/dev/null ;;
    *) echo "    (unknown type, skipped: $a)"; return 1 ;;
  esac
}

mapfile -t ARCHIVES < <(find "$SRC" -type f \( -iname '*.zip' -o -iname '*.rar' -o -iname '*.7z' \) 2>/dev/null | sort)

echo "=== Decent Sampler extraction ($MODE, set=$ONLY) ==="
echo "  source:   $SRC   (${#ARCHIVES[@]} archives)"
echo "  HEAVY ->  $DST_HEAVY"
echo "  LIGHT ->  $DST_LIGHT"
echo "  threshold: >=3GiB extracted = HEAVY ; keep >=${HEADROOM_PCT}% free"
echo

if [ "$MODE" = "apply" ]; then
  echo "run started $(date)" >> "$LOG"
fi

planned_h=0 planned_l=0 done_h=0 done_l=0 skipped=0 short=0
for a in "${ARCHIVES[@]}"; do
  ext=$(extracted_size "$a")
  if [ "$ext" -ge "$HEAVY_BYTES" ]; then cls="heavy"; dstroot="$DST_HEAVY"; else cls="light"; dstroot="$DST_LIGHT"; fi
  [ "$ONLY" != "all" ] && [ "$ONLY" != "$cls" ] && continue

  name="$(subfolder_name "$a")"
  dst="$dstroot/$name"
  extM=$(( ext / 1048576 ))

  # idempotent skip
  if [ -d "$dst" ] && [ -n "$(ls -A "$dst" 2>/dev/null)" ]; then
    echo "  [skip exists] $cls  $name"
    skipped=$((skipped+1))
    continue
  fi

  if [ "$cls" = heavy ]; then planned_h=$((planned_h+ext)); else planned_l=$((planned_l+ext)); fi

  if [ "$MODE" != "apply" ]; then
    printf "  [plan %-5s] %-48.48s ~%sM -> %s\n" "$cls" "$name" "$extM" "$dstroot"
    continue
  fi

  # re-check space with headroom right before extracting
  av=$(avail_bytes "$dstroot"); tot=$(size_bytes "$dstroot")
  min_free=$(( tot * HEADROOM_PCT / 100 ))
  if [ $(( av - ext )) -lt "$min_free" ]; then
    echo "  [SHORT-SKIP] $cls  $name  (need ${extM}M; would drop below ${HEADROOM_PCT}% headroom on $dstroot)"
    echo "SHORT-SKIP $cls $name need=${extM}M avail=$((av/1048576))M" >> "$LOG"
    short=$((short+1))
    continue
  fi

  printf "  [extract %-5s] %-44.44s ~%sM\n" "$cls" "$name" "$extM"
  if do_extract "$a" "$dst"; then
    echo "OK $cls $name ${extM}M -> $dstroot" >> "$LOG"
    if [ "$cls" = heavy ]; then done_h=$((done_h+ext)); else done_l=$((done_l+ext)); fi
  else
    echo "FAIL $cls $name" >> "$LOG"
    rmdir "$dst" 2>/dev/null
  fi
done

echo
if [ "$MODE" != "apply" ]; then
  echo "DRY-RUN summary:"
  echo "  HEAVY to extract ~$(( planned_h/1073741824 )) GiB -> $DST_HEAVY (free $(( $(avail_bytes "$(dirname "$DST_HEAVY")")/1073741824 )) GiB)"
  echo "  LIGHT to extract ~$(( planned_l/1073741824 )) GiB -> $DST_LIGHT (free $(( $(avail_bytes "$(dirname "$DST_LIGHT")")/1073741824 )) GiB)"
  echo "  already-present (skipped): $skipped"
  echo
  echo "Apply:  bash $0 apply           (all)"
  echo "        bash $0 apply light     (light set only)"
  echo "        bash $0 apply heavy     (heavy set only)"
else
  echo "APPLY summary:"
  echo "  extracted HEAVY ~$(( done_h/1073741824 )) GiB, LIGHT ~$(( done_l/1073741824 )) GiB"
  echo "  skipped (already present): $skipped ; short-skipped (space): $short"
  echo "  free now: $DST_HEAVY -> $(( $(avail_bytes "$(dirname "$DST_HEAVY")")/1073741824 )) GiB ; $DST_LIGHT -> $(( $(avail_bytes "$(dirname "$DST_LIGHT")")/1073741824 )) GiB"
  echo "  log: $LOG"
  echo
  echo "  Source archives are UNTOUCHED at: $SRC"
  echo "  In Decent Sampler, add these as library folders:"
  echo "    $DST_HEAVY"
  echo "    $DST_LIGHT"
fi
