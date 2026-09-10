#!/usr/bin/env bash
#
# db-finalize-zonly.sh
#
# Finalize the DB to a clean Z:-only state. visible=0 already killed the DB churn
# and hid the 115 pure-junk scans, but ~14 rows are registered Custom Libraries
# that still render as folder-icon duplicates next to their real Z: tiled twins.
#
# THREE data-driven passes over every remaining D:/F: row (Kontakt CLOSED, DB backed up):
#
#   PASS 1 - DUPLICATE  : a D:/F: row whose folder name ALSO exists on a fast drive
#                         AND a Z: row already registers that exact fast-drive path
#                         -> DELETE the D:/F: row (its Z: twin already gives tile+load).
#
#   PASS 2 - UNIQUE-ON-FAST : a D: row whose folder IS on a fast drive but has NO Z:
#                         twin row yet -> REPOINT to the Z: path + set visible=1
#                         (becomes the real, single registration).  [e.g. possibly
#                         Hy2rogen, Keyscape-13 if their folder was relocated]
#
#   PASS 3 - UNIQUE-OFF-FAST : a D:/F: row whose folder is NOT on any fast drive
#                         (still only on Workspace, or non-Kontakt junk) -> LEAVE as
#                         hidden (visible=0). Not deleted, not shown. EWQL RA stays here
#                         (Bug C). Pure-junk stays hidden too. Reversible.
#
# Matching a "Z: twin" = a currently-VISIBLE Z: row whose path == the fast-drive path
# for that folder name. That is the proof the library already loads+tiles from Z:.
#
# Usage:
#   bash db-finalize-zonly.sh          # dry-run: show DELETE / REPOINT / LEAVE buckets
#   bash db-finalize-zonly.sh apply     # execute

set -u
MODE="${1:-dryrun}"

K8="/mnt/workspace/VST Install/Kontakt Portable/UserData/Kontakt 8"
DB="${K8}/komplete.db3"
STAMP="$(date +%Y%m%d_%H%M%S)"

WDBLACK_LX="/mnt/wd_black/Kontakt Libraries"
SDD1_LX="/mnt/btrfs_disk/Kontakt Libraries"
WDBLACK_Z='Z:\mnt\wd_black\Kontakt Libraries'
SDD1_Z='Z:\mnt\btrfs_disk\Kontakt Libraries'

if pgrep -fi 'Kontakt 8.exe' | grep -qv grep; then
  echo "ABORT: Kontakt running. File->Exit cleanly first."; exit 1
fi
[ -f "$DB" ] || { echo "ABORT: no DB at $DB"; exit 1; }

# folder-name -> Z path (fast drives)
declare -A MAP
add_map(){ local d="$1" zb="$2" sub="$3" n; [ -d "$d" ]||return
  while IFS= read -r n; do [ -z "$n" ]&&continue; [ -z "${MAP[$n]:-}" ]&&MAP["$n"]="${zb}\\${sub}\\${n}"; done < <(ls -1 "$d"); }
add_map "${WDBLACK_LX}/Player" "$WDBLACK_Z" Player
add_map "${WDBLACK_LX}/Custom" "$WDBLACK_Z" Custom
add_map "${SDD1_LX}/Player"    "$SDD1_Z"    Player
add_map "${SDD1_LX}/Custom"    "$SDD1_Z"    Custom

# full dump: id|type|visible|path
sqlite3 -separator '|' "$DB" "SELECT id, content_type, visible, path FROM k_content_path;" > /tmp/fz_all.txt 2>/dev/null

# set of ALL paths present (to detect a Z: twin already registered)
declare -A PATHSET
while IFS='|' read -r id ct vis path; do [ -n "$id" ] && PATHSET["$path"]=1; done < /tmp/fz_all.txt

: > /tmp/fz_delete.txt      # id \t path   (DUPLICATE -> delete)
: > /tmp/fz_repoint.txt     # id \t path \t ztarget  (UNIQUE-ON-FAST -> repoint+show)
: > /tmp/fz_leave.txt       # id \t path   (UNIQUE-OFF-FAST / junk -> leave hidden)

while IFS='|' read -r id ct vis path; do
  [ -z "$id" ] && continue
  case "$path" in Z:*) continue ;; esac      # only non-Z rows
  folder="${path##*\\}"
  ztarget="${MAP[$folder]:-}"
  if [ -n "$ztarget" ] && [ -n "${PATHSET[$ztarget]:-}" ]; then
    printf '%s\t%s\n' "$id" "$path" >> /tmp/fz_delete.txt          # dup: Z twin exists
  elif [ -n "$ztarget" ]; then
    printf '%s\t%s\t%s\n' "$id" "$path" "$ztarget" >> /tmp/fz_repoint.txt  # on fast, no twin yet
  else
    printf '%s\t%s\n' "$id" "$path" >> /tmp/fz_leave.txt           # not on fast drive
  fi
done < /tmp/fz_all.txt

echo "=== PASS 1: DELETE (duplicate of an existing Z: twin) : $(grep -c $'\t' /tmp/fz_delete.txt) ==="
sed 's/^/  del /' /tmp/fz_delete.txt
echo
echo "=== PASS 2: REPOINT+SHOW (unique, folder is on a fast drive) : $(grep -c $'\t' /tmp/fz_repoint.txt) ==="
awk -F'\t' '{printf "  [%s] %s\n        -> %s\n",$1,$2,$3}' /tmp/fz_repoint.txt
echo
echo "=== PASS 3: LEAVE HIDDEN (not on a fast drive / junk / EWQL RA) : $(grep -c $'\t' /tmp/fz_leave.txt) ==="
sed 's/^/  keep-hidden /' /tmp/fz_leave.txt

if [ "$MODE" != "apply" ]; then
  echo
  echo "DRY-RUN. Nothing changed. Re-run with:  bash $0 apply"
  exit 0
fi

echo
echo "=== backup DB ==="
cp -av "$DB" "$DB.pre_finalize_$STAMP"

echo "=== PASS 1: delete duplicates ==="
DEL_IDS=$(cut -f1 /tmp/fz_delete.txt | paste -sd, -)
if [ -n "$DEL_IDS" ]; then
  sqlite3 "$DB" "DELETE FROM k_content_path WHERE id IN (${DEL_IDS});"
  echo "  deleted ids: ${DEL_IDS}"
else
  echo "  (none)"
fi

echo "=== PASS 2: repoint uniques to Z: and set visible=1 ==="
while IFS=$'\t' read -r id path ztarget; do
  [ -z "$id" ] && continue
  esc="${ztarget//\'/\'\'}"
  sqlite3 "$DB" "UPDATE k_content_path SET path='${esc}', visible=1 WHERE id=${id};"
  echo "  repointed id ${id} -> ${ztarget}"
done < /tmp/fz_repoint.txt

echo
echo "=== AFTER ==="
sqlite3 -separator '|' "$DB" "SELECT id, content_type, visible, path FROM k_content_path;" > /tmp/fz_after.txt 2>/dev/null
echo -n "total rows:   "; grep -c '|' /tmp/fz_after.txt
echo -n "VISIBLE:      "; awk -F'|' '$3==1' /tmp/fz_after.txt | grep -c '|'
echo -n "  VIS Z:      "; awk -F'|' '$3==1' /tmp/fz_after.txt | grep -c '|Z:'
echo -n "  VIS D:/F: (want 0): "; awk -F'|' '$3==1' /tmp/fz_after.txt | grep -cE '\|D:|\|F:'
echo -n "HIDDEN:       "; awk -F'|' '$3==0' /tmp/fz_after.txt | grep -c '|'
echo -n "ANY D:/F: left at all (vis or hidden): "; grep -cE '\|D:|\|F:' /tmp/fz_after.txt
echo
echo "=== any VISIBLE D:/F: (should be none) ==="
awk -F'|' '$3==1' /tmp/fz_after.txt | grep -E '\|D:|\|F:' || echo "  (none — clean)"

rm -fv "${K8}/lock.lck" 2>/dev/null || true
echo
echo "ROLLBACK (Kontakt closed):  cp -av \"$DB.pre_finalize_$STAMP\" \"$DB\""
