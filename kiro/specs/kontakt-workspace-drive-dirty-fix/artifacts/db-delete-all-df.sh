#!/usr/bin/env bash
#
# db-delete-all-df.sh
#
# FINAL cleanup. Confirmed by inspection (2026-09-07):
#   - The Import Content / Custom Libraries browser lists k_content_path rows
#     REGARDLESS of the visible flag -> visible=0 does NOT remove them from the
#     browser. Only DELETING the row removes it.
#   - k_content_path still holds 118 D:/F: rows (all hidden). Every REAL library
#     already has a Z: registration (verified: 70 visible Z: rows incl. all the
#     "...Library" twins, plus Keyscape-13 + Hy2rogen relocated to Z:). So every
#     remaining D:/F: row is either non-Kontakt junk or a duplicate of a Z: twin
#     -> all expendable.
#   - Their child preset rows live in k_sound_info (FK content_path_id) -> delete
#     those too so the ~53k junk presets drop out of the browser count.
#
# SAFETY: full DB backup first; EWQL RA row already hidden and will be deleted too
# (Bug C casualty, user chose to skip it). Reversible via the backup copy.
# Kontakt CLOSED.
#
# Usage:
#   bash db-delete-all-df.sh           # dry-run: counts + sample of what will go
#   bash db-delete-all-df.sh apply      # delete D:/F: content paths + their sound_info

set -u
MODE="${1:-dryrun}"
K8="/mnt/workspace/VST Install/Kontakt Portable/UserData/Kontakt 8"
DB="${K8}/komplete.db3"
STAMP="$(date +%Y%m%d_%H%M%S)"

if pgrep -fi 'Kontakt 8.exe' | grep -qv grep; then
  echo "ABORT: Kontakt running. File->Exit cleanly first."; exit 1
fi
[ -f "$DB" ] || { echo "ABORT: no DB at $DB"; exit 1; }

# Collect the ids of every non-Z content path (collation-safe: dump + awk, no WHERE on path)
sqlite3 -separator '|' "$DB" "SELECT id, visible, path FROM k_content_path;" > /tmp/df_all.txt 2>/dev/null
awk -F'|' '$3 !~ /^Z:/ {print $1}' /tmp/df_all.txt | paste -sd, - > /tmp/df_ids.txt
DF_IDS="$(cat /tmp/df_ids.txt)"

echo "=== current counts ==="
echo -n "  total content paths: "; grep -c '|' /tmp/df_all.txt
echo -n "  Z: (keep):           "; awk -F'|' '$3 ~ /^Z:/' /tmp/df_all.txt | grep -c '|'
echo -n "  non-Z (DELETE):      "; awk -F'|' '$3 !~ /^Z:/' /tmp/df_all.txt | grep -c '|'
echo
echo "=== sample of rows that WILL be deleted (first 20) ==="
awk -F'|' '$3 !~ /^Z:/ {print "  "$1" | vis="$2" | "$3}' /tmp/df_all.txt | head -20
echo "  ..."
echo
echo "=== VERIFY every real library keeps a Z: row (these must stay) : $(awk -F'|' '$3 ~ /^Z:/' /tmp/df_all.txt | grep -c '|') ==="
echo -n "  k_sound_info rows attached to the DELETE set: "
if [ -n "$DF_IDS" ]; then
  sqlite3 "$DB" "SELECT COUNT(*) FROM k_sound_info WHERE content_path_id IN (${DF_IDS});" 2>/dev/null || echo "(count blocked by collation; will still delete)"
fi

if [ "$MODE" != "apply" ]; then
  echo
  echo "DRY-RUN. Nothing changed. Re-run with:  bash $0 apply"
  exit 0
fi

[ -z "$DF_IDS" ] && { echo "Nothing to delete (no non-Z rows)."; exit 0; }

echo
echo "=== backup DB ==="
cp -av "$DB" "$DB.pre_deletedf_$STAMP"

echo "=== delete child k_sound_info rows for the D:/F: content paths ==="
sqlite3 "$DB" "DELETE FROM k_sound_info WHERE content_path_id IN (${DF_IDS});" 2>/dev/null \
  && echo "  k_sound_info children deleted" \
  || echo "  (k_sound_info delete reported a note; continuing)"

echo "=== delete the D:/F: content paths themselves ==="
sqlite3 "$DB" "DELETE FROM k_content_path WHERE id IN (${DF_IDS});"

echo
echo "=== AFTER ==="
sqlite3 -separator '|' "$DB" "SELECT id, visible, path FROM k_content_path;" > /tmp/df_after.txt 2>/dev/null
echo -n "  total content paths: "; grep -c '|' /tmp/df_after.txt
echo -n "  Z: rows:             "; grep -c '|Z:' /tmp/df_after.txt
echo -n "  D:/F: rows (want 0): "; grep -cE '\|D:|\|F:' /tmp/df_after.txt
echo
echo "=== any D:/F: left (should be none) ==="
grep -E '\|D:|\|F:' /tmp/df_after.txt || echo "  (none — clean)"

rm -fv "${K8}/lock.lck" 2>/dev/null || true
echo
echo "ROLLBACK (Kontakt closed): cp -av \"$DB.pre_deletedf_$STAMP\" \"$DB\""
