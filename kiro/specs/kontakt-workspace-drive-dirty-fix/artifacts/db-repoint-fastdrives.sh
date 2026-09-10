#!/usr/bin/env bash
#
# db-repoint-fastdrives.sh
#
# Repoint k_content_path rows for relocated libraries from their Workspace
# (F:/D:/Z:\mnt\workspace ...\Kontakt Vst-i\<Folder>) path to the fast-drive
# location (WD Black NVMe or sdd1 btrfs), matching by EXACT folder name.
#
# - Only updates a row when a folder of the SAME NAME exists on a fast drive.
# - Uses the Z:\ convention (drive-letter independent; Z: -> / in Wine).
# - DRY-RUN by default: prints the planned UPDATEs and changes nothing.
#   Pass  apply  as first arg to actually write (after backing up the DB).
#
# Run with Kontakt CLOSED.

set -u
MODE="${1:-dryrun}"

UD="/mnt/workspace/VST Install/Kontakt Portable/UserData"
K8="${UD}/Kontakt 8"
DB="${K8}/komplete.db3"
STAMP="$(date +%Y%m%d_%H%M%S)"

# Fast-drive roots (Linux paths) and their Z: equivalents
WDBLACK_LX="/mnt/wd_black/Kontakt Libraries"
SDD1_LX="/mnt/btrfs_disk/Kontakt Libraries"
WDBLACK_Z='Z:\mnt\wd_black\Kontakt Libraries'
SDD1_Z='Z:\mnt\btrfs_disk\Kontakt Libraries'

if pgrep -fi 'Kontakt 8.exe' | grep -qv grep; then
    echo "ABORT: Kontakt running. File->Exit first."; exit 1
fi
[ -f "${DB}" ] || { echo "ABORT: no DB at ${DB}"; exit 1; }

# Build a lookup: folder-name -> "Zbase|subdir"  (first match wins; Player before Custom)
declare -A MAP
add_map () { # $1 linux dir, $2 Zbase, $3 subdir label
    local d="$1" zb="$2" sub="$3"
    [ -d "$d" ] || return
    while IFS= read -r name; do
        [ -z "$name" ] && continue
        if [ -z "${MAP[$name]:-}" ]; then MAP["$name"]="${zb}\\${sub}\\${name}"; fi
    done < <(ls -1 "$d")
}
add_map "${WDBLACK_LX}/Player" "${WDBLACK_Z}" "Player"
add_map "${WDBLACK_LX}/Custom" "${WDBLACK_Z}" "Custom"
add_map "${SDD1_LX}/Player"    "${SDD1_Z}"    "Player"
add_map "${SDD1_LX}/Custom"    "${SDD1_Z}"    "Custom"

echo "Indexed ${#MAP[@]} fast-drive library folders."

# Pull candidate rows: id + path where path contains \Kontakt Vst-i\
mapfile -t ROWS < <(sqlite3 -separator $'\t' "${DB}" \
  "SELECT id, path FROM k_content_path WHERE path LIKE '%\\Kontakt Vst-i\\%';")

SQL=""
COUNT=0
echo
echo "=== Planned repoints (folder found on a fast drive) ==="
for row in "${ROWS[@]}"; do
    id="${row%%$'\t'*}"
    path="${row#*$'\t'}"
    # folder = last backslash-separated component
    folder="${path##*\\}"
    newbase="${MAP[$folder]:-}"
    if [ -n "$newbase" ]; then
        # escape single quotes for SQL
        esc="${newbase//\'/\'\'}"
        printf '  [%s] %s\n         -> %s\n' "$id" "$folder" "$newbase"
        SQL+="UPDATE k_content_path SET path='${esc}' WHERE id=${id};"$'\n'
        COUNT=$((COUNT+1))
    fi
done

echo
echo "Total rows that WILL be repointed: ${COUNT}"
echo "(Rows whose folder is NOT on a fast drive are left on Workspace.)"

if [ "${MODE}" != "apply" ]; then
    echo
    echo "DRY-RUN only. Re-run with:  bash $0 apply   to write the changes."
    exit 0
fi

echo
echo "=== APPLY: backing up DB then running UPDATEs ==="
cp -av "${DB}" "${K8}/komplete.db3.pre_repoint_${STAMP}"
printf '%s' "$SQL" | sqlite3 "${DB}"
echo "Done. ${COUNT} rows updated."

echo
echo "=== Verify: new drive-letter/base breakdown of Kontakt Vst-i rows ==="
sqlite3 -separator ' | ' "${DB}" \
  "SELECT CASE
      WHEN path LIKE 'Z:\\mnt\\wd_black%' THEN 'wd_black'
      WHEN path LIKE 'Z:\\mnt\\btrfs_disk%' THEN 'btrfs_disk'
      WHEN path LIKE '%workspace%' OR path LIKE 'F:%' OR path LIKE 'D:%' THEN 'workspace'
      ELSE 'other' END AS loc, COUNT(*)
   FROM k_content_path WHERE path LIKE '%Kontakt Vst-i%' OR path LIKE '%Kontakt Libraries%'
   GROUP BY loc;"

echo
echo "ROLLBACK (Kontakt closed):"
echo "  cp -av \"${K8}/komplete.db3.pre_repoint_${STAMP}\" \"${DB}\""
