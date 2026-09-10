#!/usr/bin/env bash
#
# remove-tools-chords-phrases.sh
#
# Kontakt-on-Wine stack-overflows parsing the factory Tools "Chords"/"Phrases" .nkt
# monoliths (freezes the yabridge bridge -> Reaper). User doesn't need them. Confirmed:
#   - Chords + Phrases are the ONLY folders under Content/Tools (no siblings)
#   - no .nicnt (plain patch folders, not a resource-container bundle)
#   - pristine copies exist in BACKUP; Settings.cfg has no references
# Removal = MOVE both folders to a _kiro_removed_ holding dir on the SAME drive (instant,
# reversible). Once out of the Content tree, Kontakt has no patches to load or re-register,
# so the freeze can't recur and they won't "come back".
#
# Kontakt/Reaper MUST be CLOSED.
#
# Usage:
#   bash remove-tools-chords-phrases.sh          # dry-run (shows what will move)
#   bash remove-tools-chords-phrases.sh apply

set -u
MODE="${1:-dryrun}"
TOOLS="/mnt/workspace/VST Install/Kontakt Portable/Kontakt 8/Content/Tools"
HOLD="/mnt/workspace/VST Install/Kontakt Portable/UserData/_kiro_removed_tools_chords_phrases"

# safety: Kontakt must be closed
if pgrep -fi 'Kontakt 8.exe' >/dev/null 2>&1 || pgrep -fi 'Kontakt 8 Portable' >/dev/null 2>&1; then
  echo "ABORT: Kontakt/Reaper still running. Close it first."; exit 1
fi

echo "=== folders to relocate out of Content/Tools ==="
for lib in Chords Phrases; do
  src="$TOOLS/$lib"
  if [ -d "$src" ]; then echo "  $src  ($(du -sh "$src" 2>/dev/null | cut -f1))"
  else echo "  (already gone: $src)"; fi
done
echo "  destination holding dir: $HOLD"

if [ "$MODE" != "apply" ]; then
  echo; echo "DRY-RUN. Re-run with:  bash $0 apply"; exit 0
fi

echo
echo "=== moving (reversible) ==="
mkdir -p "$HOLD"
moved=0
for lib in Chords Phrases; do
  src="$TOOLS/$lib"
  if [ -d "$src" ]; then
    mv -v "$src" "$HOLD/" && moved=$((moved+1))
  fi
done
echo "  moved $moved folder(s)."

echo
echo "=== verify Content/Tools now empty of Chords/Phrases ==="
ls -la "$TOOLS" 2>/dev/null | sed 's/^/    /'

echo
echo "ROLLBACK (Kontakt closed) — put them back:"
echo "  mv -v \"$HOLD/Chords\"  \"$TOOLS/\""
echo "  mv -v \"$HOLD/Phrases\" \"$TOOLS/\""
echo
echo "SECOND SAFETY NET: pristine originals also remain at"
echo "  /mnt/workspace/BACKUP/Kontakt 8/Content/Tools/{Chords,Phrases}"
echo
echo "NEXT: launch Kontakt in Reaper. Chords/Phrases no longer appear as loadable factory"
echo "patches, so the parse-freeze cannot recur. Everything else is unchanged."
