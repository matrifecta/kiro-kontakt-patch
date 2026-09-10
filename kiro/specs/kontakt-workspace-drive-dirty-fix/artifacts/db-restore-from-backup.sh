#!/usr/bin/env bash
#
# db-restore-from-backup.sh
#
# Restores the fully-populated Kontakt library DB (komplete.db3, 42MB, 2026-09-01)
# and its matching LibrariesCache from the pre-cleanup backup, so the browser tiles
# and the 162 type-3 Player-library registrations return.
#
# WHY: the "clean rebuild" (db-rebuild.sh) produced an 827k empty DB that lost the
# link between the 162 tile-bearing content paths and their LibrariesCache/*.cache
# artwork. Re-registration/rescan never regenerates .cache (documented, known-failed).
# The intact 42MB DB already holds those links -> restoring it is the reliable fix.
#
# All paths in the backup DB resolve to /mnt/workspace (F:, D:, Z:\mnt\workspace all
# map there), so libraries load from the Workspace originals that were kept as backup.
# Fast-drive (WD Black / sdd1) repointing is a SEPARATE later step via targeted SQL.
#
# FULLY REVERSIBLE: the current (rebuilt) DB + current cache are backed up first.
# Run with Kontakt CLOSED.

set -u

UD="/mnt/workspace/VST Install/Kontakt Portable/UserData"
K8="${UD}/Kontakt 8"
BKDIR="${UD}/_kiro_backup_20260901"
SRC_DB="${BKDIR}/komplete.db3"
SRC_CACHE="${BKDIR}/LibrariesCache_bak"
STAMP="$(date +%Y%m%d_%H%M%S)"
SAVE="${UD}/_kiro_prerestore_${STAMP}"

echo "=== Safety check: nothing Kontakt/wine running? ==="
if pgrep -fi 'Kontakt 8.exe' | grep -qv grep; then
    echo "ABORT: Kontakt appears to be running. File->Exit cleanly first."
    exit 1
fi
echo "OK: nothing running."

echo "=== Verify backup sources exist ==="
[ -f "${SRC_DB}" ]    || { echo "ABORT: missing ${SRC_DB}"; exit 1; }
[ -d "${SRC_CACHE}" ] || { echo "ABORT: missing ${SRC_CACHE}"; exit 1; }
ls -la "${SRC_DB}"
echo "cache backup files: $(ls -1 "${SRC_CACHE}" | wc -l)"

echo "=== Back up CURRENT (rebuilt) state to: ${SAVE} ==="
mkdir -p "${SAVE}/Kontakt 8"
cp -av "${K8}/komplete.db3"    "${SAVE}/Kontakt 8/"    2>/dev/null || echo "(no current komplete.db3)"
cp -av "${K8}/user_config.db3" "${SAVE}/Kontakt 8/"    2>/dev/null || echo "(no current user_config.db3)"
cp -av "${K8}/LibrariesCache"  "${SAVE}/Kontakt 8/"    2>/dev/null || echo "(no current LibrariesCache)"
echo "Current state saved."

echo "=== Restore the 42MB komplete.db3 ==="
cp -av "${SRC_DB}" "${K8}/komplete.db3"

echo "=== Restore user_config.db3 from same backup (if present) ==="
if [ -f "${BKDIR}/user_config.db3" ]; then
    cp -av "${BKDIR}/user_config.db3" "${K8}/user_config.db3"
else
    echo "(no user_config.db3 in backup; leaving current)"
fi

echo "=== Restore LibrariesCache (merge backup .cache into place) ==="
mkdir -p "${K8}/LibrariesCache"
cp -av "${SRC_CACHE}/." "${K8}/LibrariesCache/"
echo "LibrariesCache now has: $(ls -1 "${K8}/LibrariesCache" | grep -ci '.cache') .cache files"

echo "=== Remove stale lock if present ==="
rm -fv "${K8}/lock.lck" 2>/dev/null || true

echo
echo "=== DONE. NEXT: launch Kontakt, confirm tiles + browser return. ==="
echo "Libraries load from the Workspace originals (F:/Z:\\mnt\\workspace). Fast-drive"
echo "repointing is a later, separate SQL step."
echo
echo "ROLLBACK (Kontakt closed):"
echo "  cp -av \"${SAVE}/Kontakt 8/komplete.db3\" \"${K8}/komplete.db3\""
echo "  cp -av \"${SAVE}/Kontakt 8/user_config.db3\" \"${K8}/user_config.db3\" 2>/dev/null"
echo "  rm -rf \"${K8}/LibrariesCache\" && cp -av \"${SAVE}/Kontakt 8/LibrariesCache\" \"${K8}/LibrariesCache\""
