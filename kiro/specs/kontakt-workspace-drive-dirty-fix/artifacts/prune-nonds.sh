#!/usr/bin/env bash
#
# prune-nonds.sh
#
# Remove NON-Decent-Sampler engine content from the extracted DS Libraries, so the DS
# browser only shows things it can load. Based on probe (nonds-content-probe.txt):
#   - other-engine PATCH files by extension: nki nkc nkr nkm nkx exs adg adv als sfz sf2 logicx
#   - engine-named SUBFOLDERS (exact basename): Kontakt, SFZ, EXS, EXS24, Ableton, Logic
#   - macOS archive junk: __MACOSX folders, .DS_Store, ._* AppleDouble files
#
# HARD SAFETY RULES (verified against probe section 4 — all .dspreset refs are LOCAL/relative):
#   - NEVER delete .dspreset or .dslibrary
#   - NEVER delete audio: .wav .flac .ogg .aif .aiff .mp3
#   - NEVER delete a folder named Samples/ (any case) or anything inside it
#   - only delete the listed engine patch extensions + exact engine folder names + mac junk
#
# Moves deletions to a TRASH dir first (reversible), does not hard-rm. Source archives remain.
#
# Usage: bash prune-nonds.sh            # dry-run: list what would be pruned + reclaimed size
#        bash prune-nonds.sh apply

set -u
MODE="${1:-dryrun}"
ROOTS=( "/mnt/wd_black/DS Libraries" "/mnt/btrfs_disk/DS Libraries" )
STAMP="$(date +%Y%m%d_%H%M%S)"

# engine patch extensions to remove (lowercase; matched case-insensitively)
EXTS=(nki nkc nkr nkm nkx nkg exs adg adv als sfz sf2 logicx aupreset fxp fxb)
# exact engine folder basenames to remove wholesale
ENGINE_DIRS=(Kontakt KONTAKT SFZ sfz EXS EXS24 Ableton "Ableton Live" Logic HISE Halion NN-XT NNXT Reason)

# NEVER match these (safety)
is_protected() {  # $1 path -> return 0 if must be protected
  case "${1,,}" in
    *.dspreset|*.dslibrary) return 0;;
    *.wav|*.flac|*.ogg|*.aif|*.aiff|*.mp3) return 0;;
  esac
  # inside a Samples folder?
  case "/$1/" in
    */samples/*) return 0;;
  esac
  return 1
}

total_files=0 total_dirs=0 total_bytes=0
declare -a DEL_FILES DEL_DIRS

for r in "${ROOTS[@]}"; do
  [ -d "$r" ] || continue

  # 1) engine patch files by extension (skip anything under a Samples/ dir, skip protected)
  for e in "${EXTS[@]}"; do
    while IFS= read -r f; do
      [ -n "$f" ] || continue
      # skip if inside a Samples folder
      case "/${f,,}/" in */samples/*) continue;; esac
      is_protected "$f" && continue
      DEL_FILES+=("$f")
      sz=$(stat -c '%s' "$f" 2>/dev/null); total_bytes=$(( total_bytes + ${sz:-0} )); total_files=$((total_files+1))
    done < <(find "$r" -type f -iname "*.$e" 2>/dev/null)
  done

  # 2) engine-named subfolders (exact basename), never a Samples dir
  for d in "${ENGINE_DIRS[@]}"; do
    while IFS= read -r dir; do
      [ -n "$dir" ] || continue
      base="$(basename "$dir")"
      # never remove a Samples dir
      [ "${base,,}" = "samples" ] && continue
      DEL_DIRS+=("$dir")
      sz=$(du -sb "$dir" 2>/dev/null | cut -f1); total_bytes=$(( total_bytes + ${sz:-0} )); total_dirs=$((total_dirs+1))
    done < <(find "$r" -type d -name "$d" 2>/dev/null)
  done

  # 3) macOS junk
  while IFS= read -r j; do
    [ -n "$j" ] || continue
    DEL_DIRS+=("$j"); total_dirs=$((total_dirs+1))
  done < <(find "$r" -type d -name '__MACOSX' 2>/dev/null)
  while IFS= read -r j; do
    [ -n "$j" ] || continue
    DEL_FILES+=("$j"); total_files=$((total_files+1))
  done < <(find "$r" -type f \( -name '.DS_Store' -o -name '._*' \) 2>/dev/null)
done

echo "=== prune plan (NON-DS engine content) ==="
echo "  engine patch files: $total_files"
echo "  engine/junk folders: $total_dirs"
echo "  approx reclaim: $(( total_bytes / 1048576 )) MiB"
echo
echo "  sample of files to remove:"
printf '    %s\n' "${DEL_FILES[@]:0:15}"
echo "  folders to remove:"
printf '    %s\n' "${DEL_DIRS[@]:0:20}"

if [ "$MODE" != "apply" ]; then
  echo
  echo "DRY-RUN. Nothing removed. Re-run: bash $0 apply"
  echo "(.dspreset/.dslibrary, all audio, and every Samples/ folder are protected and untouched.)"
  exit 0
fi

echo
echo "=== moving pruned items to reversible TRASH (per drive) ==="
declare -A TRASH
for r in "${ROOTS[@]}"; do
  TRASH["$r"]="$(dirname "$r")/_kiro_nonds_trash_${STAMP}"
done

moved=0
for f in "${DEL_FILES[@]}"; do
  for r in "${ROOTS[@]}"; do
    case "$f" in "$r"/*)
      rel="${f#"$r"/}"; dest="${TRASH["$r"]}/$rel"
      mkdir -p "$(dirname "$dest")"; mv "$f" "$dest" 2>/dev/null && moved=$((moved+1)); break;;
    esac
  done
done
for d in "${DEL_DIRS[@]}"; do
  [ -d "$d" ] || continue
  for r in "${ROOTS[@]}"; do
    case "$d" in "$r"/*)
      rel="${d#"$r"/}"; dest="${TRASH["$r"]}/$rel"
      mkdir -p "$(dirname "$dest")"; mv "$d" "$dest" 2>/dev/null && moved=$((moved+1)); break;;
    esac
  done
done

echo "  moved $moved items to trash:"
for r in "${ROOTS[@]}"; do echo "    ${TRASH[$r]}"; done
echo
echo "VERIFY (should be unchanged): .dspreset counts"
for r in "${ROOTS[@]}"; do [ -d "$r" ] && echo "  $r: .dspreset=$(find "$r" -type f -iname '*.dspreset' | wc -l) .dslibrary=$(find "$r" -type f -iname '*.dslibrary' | wc -l)"; done
echo
echo "ROLLBACK: move items back from the _kiro_nonds_trash_${STAMP} dirs, or just re-extract."
echo "When satisfied, delete the trash dirs to reclaim space:  rm -rf <trash dir>"
