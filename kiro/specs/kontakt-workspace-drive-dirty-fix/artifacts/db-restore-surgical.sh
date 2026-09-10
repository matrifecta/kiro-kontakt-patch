#!/usr/bin/env bash
#
# db-restore-surgical.sh
#
# Restore the fully-populated 42MB komplete.db3 + LibrariesCache from the pre-cleanup
# backup (so tiles + the 162 type-3 library registrations return), THEN delete only the
# confirmed-redundant duplicate rows so the browser is clean on first launch.
#
# All kept paths resolve to /mnt/workspace (loads from Workspace originals, which are
# retained). Fast-drive (WD Black / sdd1) repointing is a SEPARATE later SQL step.
#
# FULLY REVERSIBLE: current DB + cache are backed up first; a copy of the restored DB
# is kept pre-cleanup so the DELETEs can be rolled back independently.
#
# Run with Kontakt CLOSED.

set -u

UD="/mnt/workspace/VST Install/Kontakt Portable/UserData"
K8="${UD}/Kontakt 8"
BKDIR="${UD}/_kiro_backup_20260901"
SRC_DB="${BKDIR}/komplete.db3"
SRC_CACHE="${BKDIR}/LibrariesCache_bak"
DB="${K8}/komplete.db3"
STAMP="$(date +%Y%m%d_%H%M%S)"
SAVE="${UD}/_kiro_prerestore_${STAMP}"

echo "=== Safety check: nothing Kontakt/wine running? ==="
if pgrep -fi 'Kontakt 8.exe' | grep -qv grep; then
    echo "ABORT: Kontakt appears to be running. File->Exit cleanly first."; exit 1
fi
echo "OK: nothing running."

echo "=== Verify backup sources ==="
[ -f "${SRC_DB}" ]    || { echo "ABORT: missing ${SRC_DB}"; exit 1; }
[ -d "${SRC_CACHE}" ] || { echo "ABORT: missing ${SRC_CACHE}"; exit 1; }

echo "=== Back up CURRENT (rebuilt) state to: ${SAVE} ==="
mkdir -p "${SAVE}/Kontakt 8"
cp -av "${K8}/komplete.db3"    "${SAVE}/Kontakt 8/" 2>/dev/null || echo "(no current komplete.db3)"
cp -av "${K8}/user_config.db3" "${SAVE}/Kontakt 8/" 2>/dev/null || echo "(no current user_config.db3)"
cp -av "${K8}/LibrariesCache"  "${SAVE}/Kontakt 8/" 2>/dev/null || echo "(no current LibrariesCache)"

echo "=== Restore the 42MB komplete.db3 ==="
cp -av "${SRC_DB}" "${DB}"

echo "=== Restore LibrariesCache (merge backup .cache into place) ==="
mkdir -p "${K8}/LibrariesCache"
cp -av "${SRC_CACHE}/." "${K8}/LibrariesCache/"
echo "LibrariesCache now has: $(ls -1 "${K8}/LibrariesCache" | grep -ci '.cache') .cache files"

echo "=== Keep a pre-cleanup copy of the restored DB (for DELETE rollback) ==="
cp -av "${DB}" "${SAVE}/komplete.db3.restored_precleanup"

echo "=== Row count BEFORE cleanup ==="
sqlite3 "${DB}" "SELECT COUNT(*) FROM k_content_path;"

echo "=== Surgical de-dupe: delete 20 confirmed-redundant rows ==="
# Group 1: TIXATI staging duplicates + parent
# Group 2: type-2 rows that duplicate a type-3 twin (same alias)
# Group 3: Content/Tools/Presets type-2 duplicates (keep the type-3: 130,131,132,133)
sqlite3 "${DB}" "
DELETE FROM k_content_path WHERE id IN (
  124,125,126,127,128,129,177,   -- TIXATI staging + parent
  10,12,13,15,23,33,36,          -- type-2 dupes of a type-3 twin
  1,51, 2,52, 3,53, 4,54         -- Lo-Fi Vibes / Piano Uno / Chords / Phrases type-2 dupes
);
"

echo "=== Row count AFTER cleanup (expect BEFORE - 20) ==="
sqlite3 "${DB}" "SELECT COUNT(*) FROM k_content_path;"

echo "=== Sanity: no alias still duplicated across content paths ==="
sqlite3 -separator ' | ' "${DB}" "SELECT alias, COUNT(*) c FROM k_content_path GROUP BY alias HAVING c>1 ORDER BY alias;"

echo "=== Integrity check ==="
sqlite3 "${DB}" "PRAGMA integrity_check;"

echo "=== Remove stale lock ==="
rm -fv "${K8}/lock.lck" 2>/dev/null || true

echo
echo "=== DONE. Launch Kontakt and confirm tiles + browser. ==="
echo "ROLLBACK options (Kontakt closed):"
echo "  # undo just the DELETEs (keep the restore):"
echo "  cp -av \"${SAVE}/komplete.db3.restored_precleanup\" \"${DB}\""
echo "  # undo the whole restore (back to rebuilt state):"
echo "  cp -av \"${SAVE}/Kontakt 8/komplete.db3\" \"${DB}\" 2>/dev/null"
echo "  rm -rf \"${K8}/LibrariesCache\" && cp -av \"${SAVE}/Kontakt 8/LibrariesCache\" \"${K8}/LibrariesCache\""
