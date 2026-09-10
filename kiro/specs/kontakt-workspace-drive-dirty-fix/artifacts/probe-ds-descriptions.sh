#!/usr/bin/env bash
# probe-ds-descriptions.sh   (READ-ONLY)
# Find WHERE DecentSampler libraries store descriptive text, so the catalog can pull a real
# descriptor from disk. Checks: DSLibraryInfo.xml, readme/txt files, and description-ish
# attributes/tags inside .dspreset XML. Samples a handful of libraries. Nothing modified.
set -u
OUT="/home/phnx/KIRO/.kiro/specs/kontakt-workspace-drive-dirty-fix/artifacts/ds-desc-probe.txt"
exec > >(tee "$OUT") 2>&1

echo "===== (a) DSLibraryInfo.xml files (bundle-level metadata) — show contents ====="
find "$HOME/.config/DecentSampler/Sample Libraries" "/mnt/btrfs_disk/DS Libraries" "/mnt/wd_black/DS Libraries" \
     -maxdepth 5 -iname 'DSLibraryInfo.xml' 2>/dev/null | head -5 | while read -r f; do
  echo "--- $f ---"; sed 's/^/   /' "$f" 2>/dev/null | head -30; echo
done

echo
echo "===== (b) readme / info / txt files near libraries ====="
find "/mnt/btrfs_disk/DS Libraries" -maxdepth 4 -type f \( -iname 'readme*' -o -iname '*info*.txt' -o -iname 'about*' \) 2>/dev/null \
  | grep -viE '/__MACOSX/' | head -8 | while read -r f; do
  echo "--- $f ---"; sed 's/^/   /' "$f" 2>/dev/null | head -12; echo
done

echo
echo "===== (c) description-ish attributes/tags INSIDE .dspreset XML ====="
echo "--- which attribute/tag names appear that could hold a description? ---"
find "/mnt/btrfs_disk/DS Libraries" -maxdepth 4 -iname '*.dspreset' 2>/dev/null | grep -viE '/__MACOSX/' | head -25 | while read -r p; do
  # look for common metadata carriers
  hit=$(grep -oiE '(description|comment|author|vendor|category|tags|title|name)="[^"]{0,120}"' "$p" 2>/dev/null | head -4)
  if [ -n "$hit" ]; then echo "--- $(basename "$p") ---"; printf '%s\n' "$hit" | sed 's/^/   /'; fi
done

echo
echo "===== (d) do .dspreset files carry a <ui ...> title or top <DecentSampler ...> attrs? ====="
find "/mnt/btrfs_disk/DS Libraries" -maxdepth 4 -iname '*.dspreset' 2>/dev/null | grep -viE '/__MACOSX/' | head -6 | while read -r p; do
  echo "--- $(basename "$p") : first 15 lines ---"
  sed 's/^/   /' "$p" 2>/dev/null | head -15; echo
done
echo "(done — report at $OUT)"
