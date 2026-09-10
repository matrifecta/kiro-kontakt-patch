#!/usr/bin/env bash
#
# verify-tools-state.sh  (READ-ONLY)
#
# User reports Chords/Phrases "still there" in Kontakt after the relocation reported success.
# Determine ground truth on disk: are the folders in Content/Tools, in the holding dir, or both?
# This tells us whether Kontakt is just showing a STALE browser entry (files already moved) vs
# the move not sticking. NOTHING is changed.

set -u
TOOLS="/mnt/workspace/VST Install/Kontakt Portable/Kontakt 8/Content/Tools"
HOLD="/mnt/workspace/VST Install/Kontakt Portable/UserData/_kiro_removed_tools_chords_phrases"

echo "===== A) live Content/Tools (should be EMPTY of Chords/Phrases) ====="
ls -la "$TOOLS" 2>/dev/null | sed 's/^/    /'
for lib in Chords Phrases; do
  if [ -d "$TOOLS/$lib" ]; then echo "    STILL IN CONTENT: $lib  ($(find "$TOOLS/$lib" -iname '*.nkt' | wc -l) .nkt)"
  else echo "    not in Content: $lib  (good — moved out)"; fi
done
echo

echo "===== B) holding dir (should CONTAIN Chords/Phrases) ====="
ls -la "$HOLD" 2>/dev/null | sed 's/^/    /'
for lib in Chords Phrases; do
  if [ -d "$HOLD/$lib" ]; then echo "    in holding: $lib  ($(find "$HOLD/$lib" -iname '*.nkt' | wc -l) .nkt)"
  else echo "    MISSING from holding: $lib"; fi
done
echo

echo "===== C) verdict ====="
inC=0; inH=0
[ -d "$TOOLS/Chords" ] || [ -d "$TOOLS/Phrases" ] && inC=1
[ -d "$HOLD/Chords" ] || [ -d "$HOLD/Phrases" ] && inH=1
if [ "$inC" -eq 0 ] && [ "$inH" -eq 1 ]; then
  echo "    Files ARE moved out of Content (in holding dir). If Kontakt still lists them,"
  echo "    it's a STALE browser/DB entry — harmless. Clicking one would give a not-found"
  echo "    error, NOT the freeze (the freeze needs the .nkt present to parse)."
elif [ "$inC" -eq 1 ]; then
  echo "    Files are STILL in Content/Tools — the move did not take effect as expected."
  echo "    They are harmless sitting there, but loading one CAN still freeze Kontakt."
else
  echo "    Unexpected state — review A/B above."
fi
echo
echo "READ-ONLY."
