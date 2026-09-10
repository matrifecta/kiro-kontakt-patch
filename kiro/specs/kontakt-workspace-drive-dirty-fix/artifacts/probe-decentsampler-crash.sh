#!/usr/bin/env bash
# probe-decentsampler-crash.sh   (READ-ONLY, changes nothing)
# The Reaper crash was NOT the rtprio change — it was DecentSampler aborting on a missing sample:
#   "File .../ZauberwindsSoloFloete_v1.dsbundle/Files/ZauberwindsSoloFloete/C3-Long1-V127.flac does not exist!"
#   then "malloc(): unaligned tcache chunk detected" -> Aborted (core dumped).
# This probe: (a) confirms jack_rtprio=88 is still set, (b) checks whether that .dsbundle / FLAC actually exists
# and how much of the sample set is missing, (c) checks for a coredump. Nothing is modified.
set -u
DSB="/home/phnx/.config/DecentSampler/.config/DecentSampler/Sample Libraries/ZauberwindsSoloFloete_v1.dsbundle"
FILES="$DSB/Files/ZauberwindsSoloFloete"

echo "===== (a) confirm the RT setting persisted ====="
grep -nE "^jack_rtprio=" "$HOME/.config/REAPER/reaper.ini" 2>/dev/null || echo "(no jack_rtprio line)"

echo
echo "===== (b) does the ZauberwindsSoloFloete .dsbundle exist, and how complete is it? ====="
if [ -d "$DSB" ]; then
  echo "  .dsbundle dir EXISTS: $DSB"
  echo "  --- top-level contents ---"
  ls -la "$DSB" 2>/dev/null | head
  echo "  --- the referenced Files/ZauberwindsSoloFloete dir ---"
  if [ -d "$FILES" ]; then
    total=$(find "$FILES" -type f 2>/dev/null | wc -l)
    flac=$(find "$FILES" -type f -iname '*.flac' 2>/dev/null | wc -l)
    echo "    exists. total files: $total, flac files: $flac"
    echo "    is the specific missing file present?"
    if [ -e "$FILES/C3-Long1-V127.flac" ]; then echo "      C3-Long1-V127.flac: PRESENT"; else echo "      C3-Long1-V127.flac: MISSING (this is what crashed DS)"; fi
    echo "    --- sample of what IS there ---"
    ls "$FILES" 2>/dev/null | head
  else
    echo "    MISSING: $FILES  (the whole sample folder is absent -> DS references samples that aren't there)"
  fi
  echo
  echo "  --- what samples does the .dspreset actually reference? (first 20 path= refs) ---"
  find "$DSB" -maxdepth 2 -iname '*.dspreset' -print 2>/dev/null | while read -r p; do
    echo "    preset: $p"
    grep -oiE 'path="[^"]+"' "$p" 2>/dev/null | head -20 | sed 's/^/       /'
  done
else
  echo "  .dsbundle dir MISSING entirely: $DSB"
  echo "  -> the project references a DecentSampler library that isn't installed at that path."
fi

echo
echo "===== (c) any coredump recorded for the crash? ====="
command -v coredumpctl >/dev/null 2>&1 && coredumpctl list 2>/dev/null | tail -5 || echo "  (coredumpctl not available or no dumps)"

echo
echo "===== (d) where are DecentSampler libraries expected? (path sanity) ====="
ls -la "/home/phnx/.config/DecentSampler/.config/DecentSampler/Sample Libraries/" 2>/dev/null | head -20 || echo "  (Sample Libraries dir not found — DS may store elsewhere)"
echo "(done — paste everything above)"
