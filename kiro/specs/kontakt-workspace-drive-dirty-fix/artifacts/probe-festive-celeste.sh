#!/usr/bin/env bash
#
# probe-festive-celeste.sh  (READ-ONLY)
#
# Festive Celeste reports missing files in DS. Determine WHY:
#   (a) extraction incomplete (zip-bomb bypass may have stopped early), or
#   (b) prune removed something it referenced (shouldn't have — prune kept audio/Samples), or
#   (c) path/case mismatch (DS ref vs on-disk name).
# Compare every path referenced by its .dspreset files against what exists on disk.
# NOTHING is modified.

set -u
LIB="/mnt/wd_black/DS Libraries/Festive Celeste"
SRCZIP="/mnt/workspace/Free VST-s/Pianobook/Decent Sampler/Festive Celeste.zip"

echo "===== on-disk contents of the extracted lib ====="
if [ -d "$LIB" ]; then
  echo "  size: $(du -sh "$LIB" 2>/dev/null | cut -f1)"
  echo "  top level:"; ls -la "$LIB" | sed 's/^/    /'
  echo "  file-type counts:"
  for e in dspreset wav flac ogg png jpg; do
    echo "    .$e = $(find "$LIB" -type f -iname "*.$e" | wc -l)"
  done
else
  echo "  MISSING: $LIB"
fi
echo

echo "===== what the source ZIP actually contains (truth) ====="
if [ -f "$SRCZIP" ]; then
  echo "  entries in zip: $(UNZIP_DISABLE_ZIPBOMB_DETECTION=TRUE unzip -l "$SRCZIP" 2>/dev/null | tail -1)"
  echo "  wav entries in zip:      $(UNZIP_DISABLE_ZIPBOMB_DETECTION=TRUE unzip -l "$SRCZIP" 2>/dev/null | grep -ic '\.wav')"
  echo "  wav files on disk now:   $(find "$LIB" -type f -iname '*.wav' 2>/dev/null | wc -l)"
else
  echo "  source zip not found at $SRCZIP"
fi
echo

echo "===== per-preset: referenced paths that DO NOT exist on disk ====="
shopt -s nullglob nocaseglob
miss_total=0
while IFS= read -r preset; do
  base="$(basename "$preset")"
  # dir the preset lives in (relative paths resolve from here)
  pdir="$(dirname "$preset")"
  # extract path="..." values
  refs=$(grep -oiE 'path="[^"]+"' "$preset" 2>/dev/null | sed -E 's/^path="//I; s/"$//' | sort -u)
  [ -z "$refs" ] && continue
  missing=0
  while IFS= read -r ref; do
    [ -z "$ref" ] && continue
    # normalize backslashes to slashes
    r="${ref//\\//}"
    # try resolve relative to preset dir; also relative to lib root
    if [ -e "$pdir/$r" ] || [ -e "$LIB/$r" ]; then :; else
      missing=$((missing+1))
      [ "$missing" -le 6 ] && echo "    [$base] MISSING: $ref"
    fi
  done <<< "$refs"
  if [ "$missing" -gt 0 ]; then
    echo "    -> $base: $missing missing refs (of $(echo "$refs" | wc -l))"
    miss_total=$((miss_total+missing))
  fi
done < <(find "$LIB" -type f -iname '*.dspreset' ! -name '._*' 2>/dev/null)
echo "  TOTAL missing refs across presets: $miss_total"
echo

echo "READ-ONLY. If wav-on-disk << wav-in-zip => extraction was incomplete (re-extract)."
echo "If counts match but refs missing => path/case mismatch or samples in a subfolder DS can't find."
