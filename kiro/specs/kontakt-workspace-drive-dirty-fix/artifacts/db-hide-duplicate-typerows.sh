#!/usr/bin/env bash
#
# db-hide-duplicate-typerows.sh
#
# After db-restore-tiles-repoint-only.sh, the browser shows DUPLICATE entries for
# ~14 libraries (confirmed from the browser screenshot 2026-09-07):
#   "Balinese Gamelan"          (type-2, short alias) -> HAS tile, points to Z:   (KEEP)
#   "Balinese Gamelan Library"  (type-3, long alias)  -> folder icon, still D:\PROGRAMS (HIDE)
# Same for Cloud Supply, Best Service Orchestra Complete, Evolution World Perc,
# Output Analog Strings, Output Exhale, Red Room Palette, Middle East, Pharlight,
# Session Guitarist Vintage/Picked, etc.
#
# ROOT CAUSE: the type-2 (KTP Player quick-registration) rows carry the working
# browser tile AND already resolve to the Z: fast-drive path. The type-3 rows are
# the legacy full-folder-scan registrations that are now REDUNDANT; the tile-repoint
# couldn't move them (UNIQUE path index collided with the type-2 twin already on Z:).
#
# FIX (non-destructive, reversible): set visible=0 on the redundant type-3 rows so
# the browser shows exactly ONE tile per library (the type-2 row, on Z:).
# We DO NOT delete — visible=0 keeps the row (and any k_sound_info links) so this is
# fully reversible with a single UPDATE.
#
# Selection is EXPLICIT by path (the exact stale D:\PROGRAMS\... type-3 rows), so
# nothing else is touched. Kontakt CLOSED. DB backed up first.
#
# Usage:
#   bash db-hide-duplicate-typerows.sh          # dry-run: list the rows it will hide
#   bash db-hide-duplicate-typerows.sh apply     # set visible=0 on them

set -u
MODE="${1:-dryrun}"

K8="/mnt/workspace/VST Install/Kontakt Portable/UserData/Kontakt 8"
DB="${K8}/komplete.db3"
STAMP="$(date +%Y%m%d_%H%M%S)"

if pgrep -fi 'Kontakt 8.exe' | grep -qv grep; then
  echo "ABORT: Kontakt running. File->Exit cleanly first."; exit 1
fi
[ -f "$DB" ] || { echo "ABORT: no DB at $DB"; exit 1; }

# The exact stale type-3 D:\PROGRAMS rows whose short-alias type-2 twin now lives on Z:
# (these are the folder-icon duplicates seen in the browser). Matched by EXACT path.
PATHS=(
'D:\PROGRAMS\VST, Samples & DAW\Balinese Gamelan Library'
'D:\PROGRAMS\VST, Samples & DAW\Best Service - The Orchestra Complete'
'D:\PROGRAMS\VST, Samples & DAW\Cloud Supply Library'
'D:\PROGRAMS\VST, Samples & DAW\Evolution Series - World Percussion v2.0 Close Front Mics'
'D:\PROGRAMS\VST, Samples & DAW\Middle East Library'
'D:\PROGRAMS\VST, Samples & DAW\Mysteria Library'
'D:\PROGRAMS\VST, Samples & DAW\Output Analog Strings KONTAKT'
'D:\PROGRAMS\VST, Samples & DAW\Output Exhale'
'D:\PROGRAMS\VST, Samples & DAW\Pharlight Library'
'D:\PROGRAMS\VST, Samples & DAW\Piano Colors Library'
'D:\PROGRAMS\VST, Samples & DAW\Play Series Selection Library'
'D:\PROGRAMS\VST, Samples & DAW\Red Room Audio - Palette Symphonic Sketchpad'
'D:\PROGRAMS\VST, Samples & DAW\Session Guitarist - Electric Vintage Library'
'D:\PROGRAMS\VST, Samples & DAW\Session Guitarist - Picked Acoustic Library'
)

# collation-safe: dump all rows, grep for our exact paths, show id|type|alias|path|visible
sqlite3 -separator '|' "$DB" \
  "SELECT id, content_type, alias, visible, path FROM k_content_path;" > /tmp/hide_dump.txt 2>/dev/null

echo "=== Rows that WILL be hidden (visible=0) — verify each is the D: type-3 twin of a Z: tile row ==="
FOUND=0
for p in "${PATHS[@]}"; do
  # grep the literal path (escape backslashes for grep -F)
  line=$(grep -F "|${p}" /tmp/hide_dump.txt)
  if [ -n "$line" ]; then
    echo "  $line"
    FOUND=$((FOUND+1))
  else
    echo "  (not found, skipping): $p"
  fi
done
echo "Matched ${FOUND} rows to hide. (Their short-alias Z: twins stay VISIBLE with tiles.)"

if [ "$MODE" != "apply" ]; then
  echo
  echo "DRY-RUN only. Nothing changed. Re-run with:  bash $0 apply"
  exit 0
fi

echo
echo "=== backup DB ==="
cp -av "$DB" "$DB.pre_hidedupes_$STAMP"

echo "=== set visible=0 on the redundant type-3 duplicates ==="
# Build one UPDATE with an IN-list of exact paths. Escape single quotes for SQL.
SQL="UPDATE k_content_path SET visible=0 WHERE path IN ("
first=1
for p in "${PATHS[@]}"; do
  esc="${p//\'/\'\'}"
  if [ $first -eq 1 ]; then SQL+="'${esc}'"; first=0; else SQL+=",'${esc}'"; fi
done
SQL+=");"
printf '%s\n' "$SQL" | sqlite3 "$DB"

echo "=== AFTER: confirm those rows are now visible=0 ==="
sqlite3 -separator '|' "$DB" \
  "SELECT id, content_type, alias, visible, path FROM k_content_path;" > /tmp/hide_after.txt 2>/dev/null
for p in "${PATHS[@]}"; do
  grep -F "|${p}" /tmp/hide_after.txt | sed 's/^/  /'
done

echo
echo "=== DONE. Launch Kontakt: each library should show ONE tile (the Z: one); no folder-icon duplicates. ==="
echo "ROLLBACK (Kontakt closed):"
echo "  cp -av \"$DB.pre_hidedupes_$STAMP\" \"$DB\""
echo "  # or un-hide in place:"
echo "  sqlite3 \"$DB\" \"UPDATE k_content_path SET visible=1 WHERE path LIKE 'D:\\PROGRAMS%';\""
