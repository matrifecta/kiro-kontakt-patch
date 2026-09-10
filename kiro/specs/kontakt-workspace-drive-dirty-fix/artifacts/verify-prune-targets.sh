#!/usr/bin/env bash
#
# verify-prune-targets.sh  (READ-ONLY)
#
# The prune dry-run reported 13,478 "engine patch files" — far more than the ~262 real
# engine patches the probe found. Suspicion: __MACOSX AppleDouble sidecars (._*) are being
# counted. Verify the breakdown BEFORE applying: how many targets are inside __MACOSX or are
# ._ sidecars, vs genuine top-level engine patches. Confirm ZERO .dspreset/.dslibrary/.wav
# would be caught. Nothing is modified.

set -u
ROOTS=( "/mnt/wd_black/DS Libraries" "/mnt/btrfs_disk/DS Libraries" )
EXTS=(nki nkc nkr nkm nkx nkg exs adg adv als sfz sf2 logicx aupreset fxp fxb)

in_macosx=0 apple_sidecar=0 real_patch=0
declare -A ext_real
for r in "${ROOTS[@]}"; do
  [ -d "$r" ] || continue
  for e in "${EXTS[@]}"; do
    while IFS= read -r f; do
      [ -n "$f" ] || continue
      b="$(basename "$f")"
      if [[ "$f" == *"/__MACOSX/"* ]]; then in_macosx=$((in_macosx+1))
      elif [[ "$b" == ._* ]]; then apple_sidecar=$((apple_sidecar+1))
      else real_patch=$((real_patch+1)); ext_real[$e]=$(( ${ext_real[$e]:-0} + 1 )); fi
    done < <(find "$r" -type f -iname "*.$e" 2>/dev/null)
  done
done

echo "===== breakdown of the 'engine patch files' matched ====="
echo "  inside __MACOSX/ (mac junk, safe):        $in_macosx"
echo "  ._ AppleDouble sidecars (mac junk, safe): $apple_sidecar"
echo "  GENUINE engine patch files:               $real_patch"
echo
echo "  genuine engine patches by extension:"
for e in "${!ext_real[@]}"; do printf "    .%-8s %5d\n" "$e" "${ext_real[$e]}"; done
echo

echo "===== SAFETY CHECK: would the EXTS list ever match a DS preset or audio? ====="
# prove the extension set is disjoint from DS/audio types
printf '    EXTS = %s\n' "${EXTS[*]}"
echo "    (none of these are dspreset/dslibrary/wav/flac/ogg/aif — so those are never matched)"
echo
echo "===== independent counts that MUST stay unchanged after prune ====="
for r in "${ROOTS[@]}"; do [ -d "$r" ] || continue
  echo "  $r:"
  echo "    .dspreset  = $(find "$r" -type f -iname '*.dspreset'  ! -name '._*' | wc -l)  (real, excluding ._ sidecars)"
  echo "    .dslibrary = $(find "$r" -type f -iname '*.dslibrary' ! -name '._*' | wc -l)"
  echo "    .wav       = $(find "$r" -type f -iname '*.wav'       ! -name '._*' | wc -l)"
done
echo
echo "READ-ONLY. If 'GENUINE engine patch files' is small (~260) and the rest are __MACOSX/._"
echo "junk, the prune is safe: it removes engine patches + mac junk, keeps all presets/audio."
