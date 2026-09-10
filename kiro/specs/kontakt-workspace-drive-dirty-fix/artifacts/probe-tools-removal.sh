#!/usr/bin/env bash
#
# probe-tools-removal.sh  (READ-ONLY)
#
# Plan removal of the factory Tools "Chords" and "Phrases" content (Kontakt-on-Wine
# stack-overflows parsing their .nkt; user doesn't need them). Before removing, learn:
#   1) exact folder layout + sizes of Chords/Phrases under live Content/Tools
#   2) whether a pristine copy exists in BACKUP (so removal is reversible)
#   3) whether Chords/Phrases have their OWN top-level entry, or are inside a larger
#      factory library (e.g. "Lo-Fi Vibes"/Kontakt Factory) we must NOT damage
#   4) any Settings.cfg / DB content-path references to these Tools folders
# NOTHING is deleted or moved here.

set -u
WS="/mnt/workspace/VST Install/Kontakt Portable/Kontakt 8/Content"
BK="/mnt/workspace/BACKUP/Kontakt 8/Content"
CFG="/mnt/workspace/VST Install/Kontakt Portable/UserData/Kontakt 8/Settings.cfg"

echo "===== 1) live Tools layout ====="
for d in "$WS/Tools/Chords" "$WS/Tools/Phrases"; do
  echo "--- $d ---"
  if [ -d "$d" ]; then
    du -sh "$d" 2>/dev/null
    find "$d" -maxdepth 2 -type d 2>/dev/null | sed 's/^/    /'
    echo "    .nkt count: $(find "$d" -type f -iname '*.nkt' 2>/dev/null | wc -l)"
  else
    echo "    (absent)"
  fi
done
echo

echo "===== 1b) what else lives under Tools/ (do NOT remove siblings) ====="
find "$WS/Tools" -maxdepth 1 -mindepth 1 2>/dev/null | sed 's/^/    /'
echo

echo "===== 2) pristine BACKUP copy present? (reversibility) ====="
for d in "$BK/Tools/Chords" "$BK/Tools/Phrases"; do
  if [ -d "$d" ]; then echo "    BACKUP present: $d  ($(du -sh "$d" 2>/dev/null | cut -f1))"
  else echo "    BACKUP MISSING: $d"; fi
done
echo

echo "===== 3) are Chords/Phrases standalone, or part of a bundle w/ .nicnt? ====="
find "$WS/Tools/Chords" "$WS/Tools/Phrases" -maxdepth 2 -iname '*.nicnt' 2>/dev/null | sed 's/^/    nicnt: /'
echo "    (no nicnt lines above = they are plain patch folders, safe to remove/relocate)"
echo

echo "===== 4) Settings.cfg references to these Tools paths ====="
if [ -f "$CFG" ]; then
  grep -niE 'Tools|Chords|Phrases' "$CFG" 2>/dev/null | sed 's/^/    /' || echo "    (no Tools/Chords/Phrases lines in Settings.cfg)"
else
  echo "    (Settings.cfg not found at expected path)"
fi
echo

echo "===== 5) is Kontakt currently running? (must be CLOSED before any removal) ====="
if pgrep -fi 'Kontakt 8.exe' >/dev/null 2>&1 || pgrep -fi 'Kontakt 8 Portable' >/dev/null 2>&1; then
  echo "    RUNNING — close Kontakt/Reaper before removal."
else
  echo "    not running — OK to proceed with removal step when ready."
fi

echo
echo "READ-ONLY. Report output back; then I'll write a reversible removal step"
echo "(relocate Chords/Phrases folders to a _kiro_removed_ holding dir, not hard delete)."
