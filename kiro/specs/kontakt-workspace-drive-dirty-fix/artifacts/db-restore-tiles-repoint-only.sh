#!/usr/bin/env bash
#
# db-restore-tiles-repoint-only.sh
#
# RECOVER BROWSER TILES without losing the fast-drive paths.
#
# Root cause (proven by db-tile-diagnose.sh, 2026-09-07): the Z-only convergence
# DELETED the type-3 registration rows (the D:\PROGRAMS\VST, Samples & DAW\ rows)
# that carried the browser-tile pairing for ~14 libraries. Loading was never
# harmed (the type-2 Z: rows survived and still stream), but the tile .cache
# pairing was dropped. Re-registration/rescan never regenerates .cache, so the
# ONLY reliable recovery is to go back to the fully-populated DB that still holds
# those pairings, then RE-APPLY ONLY the path repoints (NO row deletions).
#
# STRATEGY:
#   1. Restore the last-known-good, all-tiles DB (komplete.db3.pre_ewqlra_144329)
#      and its matching LibrariesCache from the pre-cleanup backup.
#   2. REPOINT (UPDATE only, never DELETE) every row whose library folder now
#      lives on a fast drive, matched by EXACT folder name -> Z:\mnt\wd_black\...
#      or Z:\mnt\btrfs_disk\... . This keeps the tile-bearing type-3 rows alive
#      while making them resolve at the new fast-drive location.
#   3. Rows whose folder is NOT on a fast drive are LEFT UNTOUCHED (same state
#      they were in when tiles worked). No junk deletion here -- browser clutter
#      is a separate, later, reversible step if wanted.
#
# FULLY REVERSIBLE. Kontakt CLOSED. Read the plan (dry-run) before applying.
#
# Usage:
#   bash db-restore-tiles-repoint-only.sh            # dry-run: restore-plan + repoint plan, NO writes
#   bash db-restore-tiles-repoint-only.sh apply      # do the restore + repoints

set -u
MODE="${1:-dryrun}"

UD="/mnt/workspace/VST Install/Kontakt Portable/UserData"
K8="${UD}/Kontakt 8"
DB="${K8}/komplete.db3"
GOOD="${K8}/komplete.db3.pre_ewqlra_144329"      # 208-row all-tiles DB (mtime sep 6 14:41)
BKDIR="${UD}/_kiro_backup_20260901"
SRC_CACHE="${BKDIR}/LibrariesCache_bak"
STAMP="$(date +%Y%m%d_%H%M%S)"
SAVE="${UD}/_kiro_tilerestore_${STAMP}"

WDBLACK_LX="/mnt/wd_black/Kontakt Libraries"
SDD1_LX="/mnt/btrfs_disk/Kontakt Libraries"
WDBLACK_Z='Z:\mnt\wd_black\Kontakt Libraries'
SDD1_Z='Z:\mnt\btrfs_disk\Kontakt Libraries'

# ---- safety ----
if pgrep -fi 'Kontakt 8.exe' | grep -qv grep; then
  echo "ABORT: Kontakt running. File->Exit cleanly first."; exit 1
fi
[ -f "$GOOD" ] || { echo "ABORT: known-good DB missing: $GOOD"; exit 1; }

# ---- build folder-name -> Z:\...\<sub>\<name> map from the fast drives ----
declare -A MAP
add_map () { # $1 linux dir  $2 Zbase  $3 sub
  local d="$1" zb="$2" sub="$3" name
  [ -d "$d" ] || return
  while IFS= read -r name; do
    [ -z "$name" ] && continue
    [ -z "${MAP[$name]:-}" ] && MAP["$name"]="${zb}\\${sub}\\${name}"
  done < <(ls -1 "$d")
}
add_map "${WDBLACK_LX}/Player" "${WDBLACK_Z}" "Player"
add_map "${WDBLACK_LX}/Custom" "${WDBLACK_Z}" "Custom"
add_map "${SDD1_LX}/Player"    "${SDD1_Z}"    "Player"
add_map "${SDD1_LX}/Custom"    "${SDD1_Z}"    "Custom"
echo "Indexed ${#MAP[@]} fast-drive library folders."

# ---- compute the repoint plan against the GOOD db (collation-safe: unfiltered dump) ----
# We match by the LAST backslash component of the path (the folder name).
TMP_ROWS="/tmp/tilerestore_rows.txt"
sqlite3 -separator $'\t' "$GOOD" \
  "SELECT id, path FROM k_content_path;" > "$TMP_ROWS" 2>/dev/null

SQL=""
COUNT=0
echo
echo "=== REPOINT PLAN (UPDATE only; folder found on a fast drive) ==="
while IFS=$'\t' read -r id path; do
  [ -z "$id" ] && continue
  folder="${path##*\\}"
  newbase="${MAP[$folder]:-}"
  if [ -n "$newbase" ] && [ "$path" != "$newbase" ]; then
    esc="${newbase//\'/\'\'}"
    printf '  [%s] %s\n        %s\n     -> %s\n' "$id" "$folder" "$path" "$newbase"
    SQL+="UPDATE k_content_path SET path='${esc}' WHERE id=${id};"$'\n'
    COUNT=$((COUNT+1))
  fi
done < "$TMP_ROWS"
echo
echo "Rows that WILL be repointed: ${COUNT}   (all other rows LEFT AS-IS; nothing deleted)"

if [ "$MODE" != "apply" ]; then
  echo
  echo "DRY-RUN only. Nothing changed. Re-run with:  bash $0 apply"
  exit 0
fi

# ================= APPLY =================
echo
echo "=== Back up CURRENT state -> ${SAVE} ==="
mkdir -p "${SAVE}"
cp -av "${DB}" "${SAVE}/komplete.db3.current" 2>/dev/null || echo "(no current komplete.db3)"
cp -av "${K8}/LibrariesCache" "${SAVE}/LibrariesCache.current" 2>/dev/null || echo "(no current LibrariesCache)"

echo "=== Restore the all-tiles DB (${GOOD##*/}) -> komplete.db3 ==="
cp -av "${GOOD}" "${DB}"

echo "=== Restore LibrariesCache from ${SRC_CACHE} (merge .cache) ==="
if [ -d "${SRC_CACHE}" ]; then
  mkdir -p "${K8}/LibrariesCache"
  cp -av "${SRC_CACHE}/." "${K8}/LibrariesCache/"
else
  echo "(backup cache dir missing; keeping existing LibrariesCache)"
fi
echo -n "LibrariesCache .cache count: "; ls -1 "${K8}/LibrariesCache" 2>/dev/null | grep -ci '\.cache$'

echo "=== Keep a pre-repoint copy (for repoint rollback) ==="
cp -av "${DB}" "${SAVE}/komplete.db3.restored_prerepoint"

echo "=== Apply ${COUNT} UPDATE repoints (NO deletes) ==="
printf '%s' "$SQL" | sqlite3 "${DB}"

echo "=== Verify: drive breakdown of repointed rows (dump + grep, collation-safe) ==="
sqlite3 -separator '|' "${DB}" "SELECT id, path FROM k_content_path;" > /tmp/tilerestore_after.txt 2>/dev/null
echo -n "  wd_black rows:   "; grep -c 'Z:\\mnt\\wd_black'   /tmp/tilerestore_after.txt
echo -n "  btrfs_disk rows: "; grep -c 'Z:\\mnt\\btrfs_disk' /tmp/tilerestore_after.txt
echo -n "  total rows:      "; grep -c '|' /tmp/tilerestore_after.txt

echo "=== Remove stale lock ==="
rm -fv "${K8}/lock.lck" 2>/dev/null || true

echo
echo "=== DONE. Launch Kontakt (standalone) and confirm tiles are back + libs load from Z:. ==="
echo "ROLLBACK (Kontakt closed):"
echo "  # undo just the repoints, keep the restored all-tiles DB:"
echo "  cp -av \"${SAVE}/komplete.db3.restored_prerepoint\" \"${DB}\""
echo "  # undo everything, back to the current 68-row DB:"
echo "  cp -av \"${SAVE}/komplete.db3.current\" \"${DB}\""
