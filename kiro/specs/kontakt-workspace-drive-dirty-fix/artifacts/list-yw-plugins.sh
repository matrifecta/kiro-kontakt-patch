#!/usr/bin/env bash
# list-yw-plugins.sh (READ-ONLY)
# Identify which REAL plugin bundles live in ~/Prejemi/Yabridge_Windows (the new ones the user wants),
# vs the stray Kontakt copy + loose runtime DLLs. Also show what yabridge currently syncs from there,
# and the current yabridge source folders, so we can plan a consolidation without breaking anything.
set -u
YW="/home/phnx/Prejemi/Yabridge_Windows"

echo "===== plugin bundles (.vst3/.vst/.clap) directly in $YW ====="
find "$YW" -maxdepth 1 \( -iname '*.vst3' -o -iname '*.vst' -o -iname '*.clap' \) -printf '  %y  %f\n' 2>/dev/null
echo "  (y=f means a single-file .vst3; y=d means a bundle folder)"
echo

echo "===== anything in SUBfolders of $YW that is a plugin bundle? ====="
find "$YW" -mindepth 2 -maxdepth 3 \( -iname '*.vst3' -o -iname '*.clap' \) 2>/dev/null | sed 's/^/  /' | head -40
echo

echo "===== loose DLLs (runtime deps, NOT plugins — context only) count ====="
echo "  dll count: $(find "$YW" -maxdepth 1 -iname '*.dll' | wc -l)"
echo

echo "===== current yabridge SOURCE folders (where 'the files from before' live) ====="
yabridgectl status 2>/dev/null | grep -E '^/|^/home|^/mnt' | sed 's/^/  /'
echo

echo "READ-ONLY. This tells us if $YW has any REAL plugins to keep (move to a source folder) besides"
echo "the stray Kontakt. If Kontakt is the ONLY bundle here, we just: yabridgectl rm this path + sync."
