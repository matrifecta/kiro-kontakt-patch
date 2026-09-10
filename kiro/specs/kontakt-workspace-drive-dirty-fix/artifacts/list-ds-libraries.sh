#!/usr/bin/env bash
# list-ds-libraries.sh   (READ-ONLY, changes nothing)
# Inventory every DecentSampler library (.dsbundle / standalone .dspreset) across all locations, so you have a
# clear map of what you have and the exact FILE BROWSER path to reach each. Nothing is modified.
# Writes the full report to a file (no terminal truncation) AND prints it.
set -u

OUT="/home/phnx/KIRO/.kiro/specs/kontakt-workspace-drive-dirty-fix/artifacts/ds-library-inventory.txt"
# redirect everything below to both the file and the terminal
exec > >(tee "$OUT") 2>&1
echo "generated: $(date)"

echo "############################################################"
echo "# DECENTSAMPLER LIBRARY INVENTORY"
echo "############################################################"

scan() {
  local label="$1" base="$2"
  [ -d "$base" ] || { echo; echo "### $label : $base  (NOT PRESENT)"; return; }
  echo
  echo "### $label"
  echo "### root: $base"
  echo "--- .dsbundle libraries here (name = what shows in the browser) ---"
  find "$base" -maxdepth 6 -iname '*.dsbundle' 2>/dev/null | sort | while read -r b; do
    name=$(basename "$b" .dsbundle)
    printf '   %-45s\n      path: %s\n' "$name" "$b"
  done
  echo "--- standalone .dspreset files not inside a .dsbundle (also loadable) ---"
  find "$base" -maxdepth 6 -iname '*.dspreset' 2>/dev/null | grep -viE '\.dsbundle/' | sort | while read -r p; do
    printf '   %-45s\n      path: %s\n' "$(basename "$p" .dspreset)" "$p"
  done
}

scan "HOME (DS default library folder — shows in BROWSE / SAMPLE STORE installed)" \
     "$HOME/.config/DecentSampler/Sample Libraries"

scan "BTRFS DISK  (FILE BROWSER -> 'btrfs' root)" \
     "/mnt/btrfs_disk/DS Libraries"

# in case libraries live elsewhere on btrfs too
echo
echo "### any OTHER .dsbundle on /mnt/btrfs_disk outside 'DS Libraries' ---"
find /mnt/btrfs_disk -maxdepth 4 -iname '*.dsbundle' 2>/dev/null | grep -viE '/DS Libraries/' | sort | sed 's/^/   /' || true

scan "WD_BLACK  (FILE BROWSER -> 'wd_black' root)" \
     "/mnt/wd_black"

echo
echo "### also checking workspace / storage / win_system for any .dsbundle ---"
for base in /mnt/workspace /mnt/storage /mnt/win_system; do
  [ -d "$base" ] || continue
  hits=$(find "$base" -maxdepth 6 -iname '*.dsbundle' 2>/dev/null | wc -l)
  echo "   $base : $hits .dsbundle found"
  [ "$hits" -gt 0 ] && find "$base" -maxdepth 6 -iname '*.dsbundle' 2>/dev/null | sort | head -40 | sed 's/^/      /'
done

echo
echo "############################################################"
echo "# SUMMARY COUNTS"
echo "############################################################"
for base in "$HOME/.config/DecentSampler/Sample Libraries" "/mnt/btrfs_disk/DS Libraries" /mnt/wd_black /mnt/workspace /mnt/storage; do
  [ -d "$base" ] || continue
  n=$(find "$base" -maxdepth 6 -iname '*.dsbundle' 2>/dev/null | wc -l)
  printf '   %-45s %s bundles\n' "$base" "$n"
done
echo
echo "FULL REPORT SAVED TO: $OUT"
echo "(no need to paste — just tell me it finished and I'll read the file)"
