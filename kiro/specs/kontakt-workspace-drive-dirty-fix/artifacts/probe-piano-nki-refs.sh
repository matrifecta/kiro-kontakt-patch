#!/usr/bin/env bash
# probe-piano-nki-refs.sh (READ-ONLY)
# The Batch re-save segfault was triggered by Content Missing for the REMOVED Tools (Chords/Phrases .nkr),
# referenced by Piano Uno's Multis. Determine whether the base .nki INSTRUMENTS (not the multis) reference
# those Tools too, or only the piano samples. If the .nki's are clean, they can load without triggering the
# crash -> the multis are the sole problem.
set -u
PU="/mnt/workspace/VST Install/Kontakt Portable/Kontakt 8/Content/Presets/Piano Uno"

echo "=== Instruments/*.nki — do they mention Chords/Phrases/Tools? ==="
for f in "$PU/Instruments/"*.nki; do
  [ -f "$f" ] || continue
  echo "--- $(basename "$f")"
  hits="$(strings -n 5 "$f" 2>/dev/null | grep -iE 'Chords|Phrases|Tools|ghost sample' | head)"
  if [ -n "$hits" ]; then echo "$hits" | sed 's/^/    REF: /'; else echo "    (no Tools/Chords/Phrases refs — clean)"; fi
  # what samples DOES it reference?
  strings -n 6 "$f" 2>/dev/null | grep -iE 'Piano Uno|\.ncw|\.nkr|\.nkc|Samples' | head -4 | sed 's/^/    smp: /'
done

echo
echo "=== Multis/*.nkm — confirm THESE are the ones pulling Chords/Phrases ==="
for f in "$PU/Multis/Chords/"*.nkm "$PU/Multis/Phrases/"*.nkm; do
  [ -f "$f" ] || continue
  echo "--- $(basename "$f")"
  strings -n 5 "$f" 2>/dev/null | grep -iE 'Chords|Phrases|Tools|ghost sample' | head -3 | sed 's/^/    REF: /'
  break  # one example is enough
done

echo
echo "READ-ONLY. If the Instruments/*.nki have NO Chords/Phrases/Tools refs, they can be loaded directly"
echo "(Files browser -> the .nki) without the crash. Then Piano Uno works as an instrument; only its multis"
echo "(which need the removed Tools) stay broken. That's a safe, no-Batch-resave path."
