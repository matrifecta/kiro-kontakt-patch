#!/usr/bin/env bash
# probe-ds-lib-art.sh  (READ-ONLY)
# At LIBRARY level (matching the catalog's new structure), report which libraries have NO usable cover
# image on disk (any format), so we know exactly which need a manual/web override.
set -u
OUT="/home/phnx/KIRO/.kiro/specs/kontakt-workspace-drive-dirty-fix/artifacts/ds-lib-missing-art.txt"
exec > >(tee "$OUT") 2>&1
HOME_LIB="$HOME/.config/DecentSampler/Sample Libraries"
BTRFS="/mnt/btrfs_disk/DS Libraries"; WDB="/mnt/wd_black/DS Libraries"

has_cover(){ local d="$1"
  find "$d" -maxdepth 3 -type f \( -iname '*.png' -o -iname '*.jpg' -o -iname '*.jpeg' -o -iname '*.gif' -o -iname '*.bmp' -o -iname '*.webp' \) 2>/dev/null \
    | grep -viE '/__MACOSX/|/\._' | grep -viE 'knob|dial|fader|slider|button|hover|switch|led|arrow' | head -1; }

libs(){ local root="$1"
  find "$root" -maxdepth 6 -iname '*.dsbundle' -type d 2>/dev/null | grep -viE '/__MACOSX/|/_kiro_nonds_trash_'
  find "$root" -mindepth 1 -maxdepth 1 -type d 2>/dev/null | grep -viE '/__MACOSX/|/_kiro_nonds_trash_' | while read -r d; do
    case "$d" in *.dsbundle) continue;; esac
    find "$d" -maxdepth 4 -iname '*.dspreset' 2>/dev/null | grep -viE '/__MACOSX/|/\._|\.dsbundle/' | head -1 | grep -q . && echo "$d"
  done; }

miss=0; tot=0
for root in "$HOME_LIB" "$BTRFS" "$WDB"; do
  [ -d "$root" ] || continue
  while read -r d; do
    [ -z "$d" ] && continue; tot=$((tot+1))
    if [ -z "$(has_cover "$d")" ]; then miss=$((miss+1)); echo "NO-ART: $(basename "$d")   [$d]"; fi
  done < <(libs "$root" | sort -u)
done
echo; echo "libraries total: $tot   no-art: $miss"
echo "report: $OUT"
