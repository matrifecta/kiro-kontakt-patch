#!/usr/bin/env bash
#
# db-purge-orphan-soundinfo.sh
#
# After db-delete-all-df.sh, k_content_path is clean (70 Z: rows) but the child
# DELETE on k_sound_info was blocked by the custom KOMPLETE collation (it fired on
# a text compare). Result: ~53,109 ORPHANED k_sound_info rows remain (their parent
# content_path_id no longer exists) -> they still render as browser dupes + inflate
# the preset count (13,310).
#
# FIX: delete k_sound_info rows whose content_path_id is NOT one of the 70 surviving
# content-path ids. content_path_id is an INTEGER column, so a numeric NOT IN (...)
# comparison does NOT invoke the KOMPLETE text collation -> it won't abort.
#
# Kontakt CLOSED. DB backed up first. Reversible.
#
# Usage:
#   bash db-purge-orphan-soundinfo.sh          # dry-run: counts
#   bash db-purge-orphan-soundinfo.sh apply

set -u
MODE="${1:-dryrun}"
K8="/mnt/workspace/VST Install/Kontakt Portable/UserData/Kontakt 8"
DB="${K8}/komplete.db3"
STAMP="$(date +%Y%m%d_%H%M%S)"

if pgrep -fi 'Kontakt 8.exe' | grep -qv grep; then
  echo "ABORT: Kontakt running. File->Exit cleanly first."; exit 1
fi
[ -f "$DB" ] || { echo "ABORT: no DB at $DB"; exit 1; }

# The 70 surviving content-path ids (numeric; safe to list)
KEEP_IDS="$(sqlite3 "$DB" "SELECT id FROM k_content_path;" 2>/dev/null | paste -sd, -)"
echo "surviving content-path ids (${KEEP_IDS})" | fold -s -w 100 | head
[ -z "$KEEP_IDS" ] && { echo "ABORT: could not read content-path ids"; exit 1; }

echo
echo "=== BEFORE ==="
echo -n "  k_sound_info total:            "; sqlite3 "$DB" "SELECT COUNT(*) FROM k_sound_info;"
echo -n "  k_sound_info to KEEP (in 70):  "; sqlite3 "$DB" "SELECT COUNT(*) FROM k_sound_info WHERE content_path_id IN (${KEEP_IDS});"
echo -n "  k_sound_info ORPHANS (delete): "; sqlite3 "$DB" "SELECT COUNT(*) FROM k_sound_info WHERE content_path_id NOT IN (${KEEP_IDS});"

if [ "$MODE" != "apply" ]; then
  echo; echo "DRY-RUN. Re-run with:  bash $0 apply"; exit 0
fi

echo
echo "=== backup DB ==="
cp -av "$DB" "$DB.pre_orphanpurge_$STAMP"

echo "=== delete orphaned k_sound_info (numeric NOT IN -> no KOMPLETE collation) ==="
sqlite3 "$DB" "DELETE FROM k_sound_info WHERE content_path_id NOT IN (${KEEP_IDS});"

# also clean the child/index tables that reference sound_info, numerically if present
echo "=== clean dependent rows in k_sound_info_category / k_sound_info_mode (by orphan) ==="
sqlite3 "$DB" "DELETE FROM k_sound_info_category WHERE sound_info_id NOT IN (SELECT id FROM k_sound_info);" 2>/dev/null && echo "  category cleaned" || echo "  (category: skipped/blocked)"
sqlite3 "$DB" "DELETE FROM k_sound_info_mode     WHERE sound_info_id NOT IN (SELECT id FROM k_sound_info);" 2>/dev/null && echo "  mode cleaned"     || echo "  (mode: skipped/blocked)"

echo
echo "=== AFTER ==="
echo -n "  k_sound_info total:  "; sqlite3 "$DB" "SELECT COUNT(*) FROM k_sound_info;"
echo -n "  still mentioning PROGRAMS (want 0): "; sqlite3 "$DB" "SELECT * FROM k_sound_info;" 2>/dev/null | grep -c 'PROGRAMS'
echo -n "  content paths (want 70): "; sqlite3 "$DB" "SELECT COUNT(*) FROM k_content_path;"

rm -fv "${K8}/lock.lck" 2>/dev/null || true
echo
echo "ROLLBACK (Kontakt closed): cp -av \"$DB.pre_orphanpurge_$STAMP\" \"$DB\""
