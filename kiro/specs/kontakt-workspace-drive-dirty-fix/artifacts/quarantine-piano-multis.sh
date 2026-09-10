#!/usr/bin/env bash
# quarantine-piano-multis.sh
# Piano Uno's 6 .nki instruments are CLEAN (no Tools refs). Only the Multis/*.nkm reference the removed
# Chords/Phrases Tools -> those multis are what triggers the "Content Missing" -> segfault. Move the Multis
# folder aside (reversible) so the instrument loads normally. Same relocate approach as Task 13 (Tools removal).
# Kontakt closed. Also do the same check/quarantine for Lo-Fi Vibes if its .nkl kits reference Tools (they
# likely don't, but we verify).
set -u
MODE="${1:-dryrun}"
PU="/mnt/workspace/VST Install/Kontakt Portable/Kontakt 8/Content/Presets/Piano Uno"
QUARANTINE="/mnt/workspace/VST Install/Kontakt Portable/UserData/_kiro_piano_multis_removed_$(date +%Y%m%d_%H%M%S)"

echo "=== quarantine Piano Uno Multis (they reference removed Tools) ==="
echo "  from: $PU/Multis"
echo "  to:   $QUARANTINE/Multis"
if [ ! -d "$PU/Multis" ]; then echo "  NOTE: Multis already gone"; fi

if pgrep -x wineserver >/dev/null 2>&1 || pgrep -x reaper >/dev/null 2>&1; then
  echo "  *** close Reaper + wineserver -k first ***"; [ "$MODE" = apply ] && { echo ABORT; exit 1; }
fi
if [ "$MODE" != apply ]; then echo; echo "DRY-RUN. Re-run: bash $0 apply"; exit 0; fi

mkdir -p "$QUARANTINE"
if [ -d "$PU/Multis" ]; then
  mv -v "$PU/Multis" "$QUARANTINE/Multis"
  echo "  moved Multis aside."
fi
echo
echo "ROLLBACK: mv \"$QUARANTINE/Multis\" \"$PU/Multis\""
echo "NEXT: launch standalone Kontakt, use the Files browser to load e.g."
echo "  $PU/Instruments/Piano Uno - Concert.nki"
echo "It should load WITHOUT the Content Missing crash (multis are gone). If it loads, Piano Uno works as an"
echo "instrument. (The multis needed the removed Chords/Phrases Tools; they stay quarantined.)"
