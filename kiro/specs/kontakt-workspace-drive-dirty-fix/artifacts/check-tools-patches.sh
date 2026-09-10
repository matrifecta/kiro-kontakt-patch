#!/usr/bin/env bash
#
# check-tools-patches.sh  (READ-ONLY)
#
# Chords/Phrases give "This patch is corrupted and cannot be loaded!" and don't load.
# Their patch files use a non-.nki extension. This shows every file in their Instruments
# tree, its type (to spot truncation), and whether it matches the pristine BACKUP.

set -u
WS="/mnt/workspace/VST Install/Kontakt Portable/Kontakt 8/Content/Tools"
BK="/mnt/workspace/BACKUP/Kontakt 8/Content/Tools"

for lib in Chords Phrases; do
  echo "===== $lib — LIVE files (all) ====="
  find "$WS/$lib" -type f 2>/dev/null -exec ls -la {} \;
  echo
  echo "===== $lib — file types ====="
  find "$WS/$lib" -type f 2>/dev/null -exec file {} \; | head -20
  echo
  echo "===== $lib — LIVE vs BACKUP (per file) ====="
  find "$WS/$lib" -type f 2>/dev/null | while read -r f; do
    rel="${f#"$WS"/}"
    if [ ! -e "$BK/$rel" ]; then echo "  NO-BACKUP  $rel"
    elif cmp -s "$f" "$BK/$rel"; then echo "  OK         $rel"
    else echo "  DIFFERS    $rel"; fi
  done
  echo
  echo "===== $lib — files in BACKUP but MISSING from LIVE ====="
  find "$BK/$lib" -type f 2>/dev/null | while read -r f; do
    rel="${f#"$BK"/}"
    [ -e "$WS/$rel" ] || echo "  MISSING-LIVE  $rel"
  done
  echo
done
echo "READ-ONLY. Paste output."
