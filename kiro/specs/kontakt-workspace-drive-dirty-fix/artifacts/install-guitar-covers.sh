#!/usr/bin/env bash
# install-guitar-covers.sh
# Copies the two web covers you saved in ~/Slike/Missing DS Images/ into covers-manual/
# with stable names, and reports what it found so we can wire cover-overrides.tsv correctly.
set -u
SRC="/home/phnx/Slike/Missing DS Images"
DEST="/home/phnx/KIRO/.kiro/specs/kontakt-workspace-drive-dirty-fix/artifacts/covers-manual"
mkdir -p "$DEST"

echo "=== files found in: $SRC ==="
ls -la "$SRC" 2>/dev/null || { echo "SRC not found"; exit 1; }

echo
echo "=== image files there ==="
find "$SRC" -maxdepth 1 -type f \( -iname '*.png' -o -iname '*.jpg' -o -iname '*.jpeg' -o -iname '*.webp' -o -iname '*.gif' \) 2>/dev/null | sed 's/^/  /'

echo
echo "(No copy performed yet — tell me which file is which instrument, or if the filenames clearly"
echo " say 'archtop' / 'diarchtop' and 'overtone', re-run with: bash $0 apply )"

if [ "${1:-}" = apply ]; then
  echo; echo "=== apply: matching by filename keywords ==="
  arch=$(find "$SRC" -maxdepth 1 -type f 2>/dev/null | grep -iE 'arch|diar' | head -1)
  over=$(find "$SRC" -maxdepth 1 -type f 2>/dev/null | grep -iE 'overtone|dynamic' | head -1)
  if [ -n "$arch" ]; then
    ext="${arch##*.}"; cp "$arch" "$DEST/thediarchtop.$ext"; echo "  TheDiArchtop      <- $arch  => thediarchtop.$ext"
  else echo "  (could not identify an archtop image by name)"; fi
  if [ -n "$over" ]; then
    ext="${over##*.}"; cp "$over" "$DEST/dynamic-overtone-guitar.$ext"; echo "  Dynamic Overtone  <- $over  => dynamic-overtone-guitar.$ext"
  else echo "  (could not identify an overtone image by name)"; fi
  echo; echo "copied into: $DEST"; ls -la "$DEST" | sed 's/^/  /'
fi
