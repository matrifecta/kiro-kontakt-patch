#!/usr/bin/env bash
#
# fix-two-failed-archives.sh
#
# Two archives failed in the main extraction:
#   1) Festive Celeste.zip  -> unzip "overlapped components (possible zip bomb)" false-positive
#      (large legit zip; bypass with UNZIP_DISABLE_ZIPBOMB_DETECTION=TRUE). HEAVY -> wd_black.
#   2) Tea from HELL (DS).zip -> "End-of-central-directory not found" = truncated OR misnamed
#      (maybe actually a rar/7z). Diagnose; extract with the right tool if possible. LIGHT -> btrfs.
#
# Usage: bash fix-two-failed-archives.sh            # diagnose only
#        bash fix-two-failed-archives.sh apply

set -u
MODE="${1:-dryrun}"
SRC="/mnt/workspace/Free VST-s/Pianobook/Decent Sampler"
DST_HEAVY="/mnt/wd_black/DS Libraries"
DST_LIGHT="/mnt/btrfs_disk/DS Libraries"

FC="$SRC/Festive Celeste.zip"
TH="$SRC/Tea from HELL (DS).zip"

echo "===== diagnose ====="
for f in "$FC" "$TH"; do
  echo "--- $f ---"
  if [ -e "$f" ]; then ls -la "$f"; echo -n "  type: "; file "$f"; else echo "  (missing)"; fi
done
echo

if [ "$MODE" != "apply" ]; then
  echo "DRY-RUN. Re-run with: bash $0 apply"
  exit 0
fi

echo "===== 1) Festive Celeste — extract with zipbomb detection disabled ====="
d="$DST_HEAVY/Festive Celeste"
mkdir -p "$d"
if UNZIP_DISABLE_ZIPBOMB_DETECTION=TRUE unzip -o -q "$FC" -d "$d"; then
  echo "  OK -> $d  ($(du -sh "$d" 2>/dev/null | cut -f1))"
else
  echo "  STILL FAILED — will report; leaving folder in place for inspection."
fi
echo

echo "===== 2) Tea from HELL — pick tool by actual file type ====="
d2="$DST_LIGHT/Tea from HELL (DS)"
mkdir -p "$d2"
ftype="$(file -b "$TH" 2>/dev/null)"
echo "  detected: $ftype"
case "$ftype" in
  *Zip*|*zip*)
    if UNZIP_DISABLE_ZIPBOMB_DETECTION=TRUE unzip -o -q "$TH" -d "$d2"; then echo "  OK (zip) -> $d2"
    else echo "  zip extract failed — likely TRUNCATED download; re-download this pack."; rmdir "$d2" 2>/dev/null; fi ;;
  *RAR*|*rar*)
    if command -v unrar >/dev/null 2>&1; then unrar x -o+ "$TH" "$d2/" >/dev/null && echo "  OK (rar) -> $d2"
    else echo "  is RAR but 'unrar' missing: sudo pacman -S unrar, then re-run."; fi ;;
  *7-zip*|*7z*)
    if command -v 7z >/dev/null 2>&1; then 7z x -y -o"$d2" "$TH" >/dev/null && echo "  OK (7z) -> $d2"
    else echo "  is 7z but '7z' missing: sudo pacman -S p7zip, then re-run."; fi ;;
  *)
    # try zip anyway, then report
    if UNZIP_DISABLE_ZIPBOMB_DETECTION=TRUE unzip -o -q "$TH" -d "$d2" 2>/dev/null; then echo "  OK (forced zip) -> $d2"
    else echo "  UNRECOVERABLE here — file appears truncated/corrupt. Re-download 'Tea from HELL' from Pianobook."; rmdir "$d2" 2>/dev/null; fi ;;
esac
echo
echo "Done. Source archives untouched."
