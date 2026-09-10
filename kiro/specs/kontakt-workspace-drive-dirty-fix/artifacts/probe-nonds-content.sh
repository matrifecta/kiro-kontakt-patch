#!/usr/bin/env bash
#
# probe-nonds-content.sh  (READ-ONLY)
#
# Before pruning non-Decent-Sampler content from the extracted DS Libraries, discover
# WHAT other-engine files/folders actually exist, so the prune rules are precise (not
# guesswork). We inventory patch-file types by extension and engine-named subfolders,
# and count .dspreset (the ONLY thing DS loads). We DO NOT list/keep audio for deletion —
# audio (.wav/.flac/.ogg) is shared and must always be preserved.
# NOTHING is deleted.

set -u
ROOTS=( "/mnt/wd_black/DS Libraries" "/mnt/btrfs_disk/DS Libraries" )
OUT="/home/phnx/KIRO/.kiro/specs/kontakt-workspace-drive-dirty-fix/artifacts/nonds-content-probe.txt"

{
echo "===== extracted roots present? ====="
for r in "${ROOTS[@]}"; do
  if [ -d "$r" ]; then echo "  $r  ($(du -sh "$r" 2>/dev/null | cut -f1), $(find "$r" -mindepth 1 -maxdepth 1 -type d | wc -l) libs)"
  else echo "  (absent) $r"; fi
done
echo

echo "===== 1) DS presets present (.dspreset / .dslibrary) — KEEP ====="
for r in "${ROOTS[@]}"; do [ -d "$r" ] || continue
  echo "  $r:  .dspreset=$(find "$r" -type f -iname '*.dspreset' | wc -l)  .dslibrary=$(find "$r" -type f -iname '*.dslibrary' | wc -l)"
done
echo

echo "===== 2) OTHER-ENGINE patch files by extension (candidates to remove) ====="
# engine patch/preset extensions (NOT audio, NOT dspreset)
EXTS=(nki nkm nkc nkx nkr exs adg adv als fxp fxb sfz sf2 h2song hise hip \
      aupreset patch vital serumpreset spf nmsv fst logicx band garageband \
      reason cmb sxt rns rex rx2 kong drumkit)
for r in "${ROOTS[@]}"; do [ -d "$r" ] || continue
  echo "--- $r ---"
  for e in "${EXTS[@]}"; do
    n=$(find "$r" -type f -iname "*.$e" 2>/dev/null | wc -l)
    [ "$n" -gt 0 ] && printf "    .%-14s %5d\n" "$e" "$n"
  done
done
echo

echo "===== 3) engine-named SUBFOLDERS (candidates to remove wholesale) ====="
# common vendor/engine folder names bundled beside a DS folder
PAT='Kontakt|EXS|EXS24|SFZ|Ableton|Live|Logic|Reason|HISE|Halion|NN-XT|NNXT|Battery|Maschine|Bitwig|SF2|SoundFont|VST|AU |Serum|Vital|Redux|Simpler|Sampler Instrument'
for r in "${ROOTS[@]}"; do [ -d "$r" ] || continue
  echo "--- $r ---"
  find "$r" -mindepth 2 -type d 2>/dev/null | grep -iE "/($PAT)( |$|/)" | sed 's/^/    /' | head -60
done
echo

echo "===== 4) sanity: do any .dspreset reference samples OUTSIDE their own lib folder? ====="
echo "    (if yes, pruning must be extra careful; usually DS refs are relative & local)"
for r in "${ROOTS[@]}"; do [ -d "$r" ] || continue
  find "$r" -type f -iname '*.dspreset' 2>/dev/null | head -3 | while IFS= read -r p; do
    echo "    sample refs in: $(basename "$p")"
    grep -oiE 'path="[^"]+"' "$p" 2>/dev/null | head -5 | sed 's/^/        /'
  done
done
echo

echo "READ-ONLY. From this we build a precise prune script:"
echo "  - delete ONLY the other-engine patch files (section 2) + engine subfolders (section 3)"
echo "  - NEVER touch .wav/.flac/.ogg/.aif or any Samples folder"
echo "  - keep every .dspreset/.dslibrary"
} > "$OUT" 2>&1

echo "Probe written to: $OUT"
echo
grep -E 'libs\)|dspreset=|^    \.|--- |absent' "$OUT" | head -60 | sed 's/^/  /'
