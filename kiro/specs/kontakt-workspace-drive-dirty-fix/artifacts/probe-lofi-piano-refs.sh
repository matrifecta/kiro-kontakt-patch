#!/usr/bin/env bash
# probe-lofi-piano-refs.sh (READ-ONLY)
# Understand WHY Lo-Fi Vibes / Piano Uno throw "File not found" before attempting Batch re-save.
# For each preset folder: list the .nki/.nkm files, and extract the SAMPLE PATH references embedded in them
# (strings) to see where they point (drive letter + path) and whether those targets exist on disk.
set -u
BASE="/mnt/workspace/VST Install/Kontakt Portable/Kontakt 8/Content/Presets"

for lib in "Lo-Fi Vibes" "Piano Uno"; do
  d="$BASE/$lib"
  echo "==================== $lib"
  echo "  dir: $d"
  if [ ! -d "$d" ]; then echo "  (MISSING)"; continue; fi
  echo "  -- tree (top 2 levels):"
  find "$d" -maxdepth 2 2>/dev/null | sed 's/^/     /' | head -40
  echo "  -- .nki/.nkm files:"
  find "$d" -type f \( -iname '*.nki' -o -iname '*.nkm' \) 2>/dev/null | sed 's/^/     /' | head
  # sample-path references embedded in the first instrument
  nki="$(find "$d" -type f \( -iname '*.nki' -o -iname '*.nkm' \) 2>/dev/null | head -1)"
  if [ -n "$nki" ]; then
    echo "  -- path-like strings inside: $(basename "$nki")"
    strings -n 6 "$nki" 2>/dev/null | grep -iE '\.wav|\.ncw|\.nkx|Samples|[A-Z]:\\\\|/mnt/|Content' | head -25 | sed 's/^/       ref: /'
  fi
  # is there a Samples/ dir with actual audio?
  echo "  -- audio files present under the folder:"
  find "$d" -type f \( -iname '*.wav' -o -iname '*.ncw' -o -iname '*.nkx' -o -iname '*.flac' \) 2>/dev/null | wc -l | sed 's/^/     count: /'
  find "$d" -type f \( -iname '*.wav' -o -iname '*.ncw' -o -iname '*.nkx' \) 2>/dev/null | head -5 | sed 's/^/     e.g. /'
  echo
done
echo "READ-ONLY. If the .nki references a drive letter/path where samples DON'T exist, that's the load failure;"
echo "Batch re-save can fix it ONLY if the actual sample files exist SOMEWHERE we can point it at. If the samples"
echo "are simply missing entirely, Batch re-save cannot conjure them — the content would need reinstalling."
