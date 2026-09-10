#!/usr/bin/env bash
#
# analyze_kontakt_log.sh
#
# Buckets failed file lookups from a Kontakt `WINEDEBUG=+file` launch log so each
# startup fix can be measured (before/after) per category.
#
# Usage:
#   ./analyze_kontakt_log.sh /path/to/kontakt_load.log
#   ./analyze_kontakt_log.sh ~/kontakt_load.log > results/baseline.txt
#
# A "failed lookup" line is one containing any of the known not-found markers.
# Each such line is classified into exactly one bucket (first match wins).

set -euo pipefail

LOG="${1:-$HOME/kontakt_load.log}"

if [[ ! -f "$LOG" ]]; then
  echo "error: log file not found: $LOG" >&2
  echo "run an instrumented launch first, e.g.:" >&2
  echo '  WINEDLLOVERRIDES="*api-ms-win-core*=b;*msvcp140*=b;*vcruntime140*=b" \' >&2
  echo '    WINEDEBUG=+file wine "Kontakt 8.exe" 2>&1 | tee ~/kontakt_load.log' >&2
  exit 1
fi

# Case-insensitive "not found" markers seen in Wine +file traces.
FAIL_RE='no such file|cannot find|not found|status_object_name_not_found|object_name_not_found|object_path_not_found'

# Pull only the failing lines once.
FAILS="$(grep -Ei "$FAIL_RE" "$LOG" || true)"

total=$(printf '%s\n' "$FAILS" | grep -c . || true)

# Classify. First matching pattern wins so buckets are mutually exclusive.
# We test the raw line (paths appear as ...\\name.ext or L"...").
count_bucket() {
  # $1 = extended-regex for this bucket
  printf '%s\n' "$FAILS" | grep -Eic "$1" || true
}

db_sidecar=$(printf '%s\n' "$FAILS" | grep -Ei '\.db-wal|\.db-journal|\.db-shm' | grep -c . || true)

# Remove already-counted sidecar lines before counting the rest so totals are exclusive.
remaining=$(printf '%s\n' "$FAILS" | grep -Eiv '\.db-wal|\.db-journal|\.db-shm' || true)

bucket_from() {
  # $1 = current remaining set (var name), $2 = regex ; echoes count and prints new remaining to fd 3
  :
}

# resource_image  (match both escaped Wine form ...\image\... and unix form)
IMG_RE='[\\/]image[\\/]'
resource_image=$(printf '%s\n' "$remaining" | grep -Ei "$IMG_RE" | grep -c . || true)
remaining=$(printf '%s\n' "$remaining" | grep -Eiv "$IMG_RE" || true)

# resource_dist_db
resource_dist_db=$(printf '%s\n' "$remaining" | grep -Ei 'dist_database' | grep -c . || true)
remaining=$(printf '%s\n' "$remaining" | grep -Eiv 'dist_database' || true)

# controller_probe (Launchpad/LCXL letters E: and J: as bare roots, pre-remap)
controller_probe=$(printf '%s\n' "$remaining" | grep -Ei '\\\?\?\\[EJ]:\\?"|\b[EJ]:\\\\?$|[EJ]:\\\\?"' | grep -c . || true)
remaining=$(printf '%s\n' "$remaining" | grep -Eiv '\\\?\?\\[EJ]:\\?"|\b[EJ]:\\\\?$|[EJ]:\\\\?"' || true)

# library_content
library_content=$(printf '%s\n' "$remaining" | grep -Ei '\.nkx|\.nkr|\.nkc|\.nicnt|\.nki|\.nkm|\.nkb|\.nksn' | grep -c . || true)
remaining=$(printf '%s\n' "$remaining" | grep -Eiv '\.nkx|\.nkr|\.nkc|\.nicnt|\.nki|\.nkm|\.nkb|\.nksn' || true)

# other = whatever is left
other=$(printf '%s\n' "$remaining" | grep -c . || true)

echo "Kontakt failed-lookup analysis"
echo "log:   $LOG"
echo "date:  $(date -Is)"
echo "-----------------------------------------"
printf '%-20s %8s\n' "bucket" "count"
printf '%-20s %8s\n' "--------------------" "--------"
printf '%-20s %8s\n' "db_sidecar"        "$db_sidecar"
printf '%-20s %8s\n' "resource_image"    "$resource_image"
printf '%-20s %8s\n' "resource_dist_db"  "$resource_dist_db"
printf '%-20s %8s\n' "controller_probe"  "$controller_probe"
printf '%-20s %8s\n' "library_content"   "$library_content"
printf '%-20s %8s\n' "other"             "$other"
printf '%-20s %8s\n' "--------------------" "--------"
printf '%-20s %8s\n' "TOTAL_failed"      "$total"
echo
echo "Top 25 most-probed missing paths:"
{
  printf '%s\n' "$FAILS" \
    | sed -E 's/.*L"//; s/".*//' \
    | sed -E 's/.*(no such file|not found)[: ]*//I' \
    | sort | uniq -c | sort -rn | head -25
} || true
