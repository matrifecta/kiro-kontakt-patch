#!/usr/bin/env bash
#
# db-classify-nonz.sh   (READ-ONLY — changes nothing)
#
# The 42MB restore brought back ALL the old D:\PROGRAMS Custom entries + the F:
# User Content path. Goal is Z:-only with EVERY artwork tile kept. To converge
# safely (no blind deletes) we first CLASSIFY every non-Z row in the CURRENT DB:
#
#   REPOINTABLE  : a D:/F: row whose exact Z: target path is FREE (no other row
#                  already uses it) AND whose folder exists on a fast drive
#                  -> can be UPDATE-repointed to Z:.
#   DUP-HIDE     : a D:/F: row whose Z: twin path is ALREADY TAKEN by another row
#                  (the tile-bearing type-2 row) -> hide with visible=0 (redundant).
#   JUNK-HIDE    : a D: row that is NOT a Kontakt library folder on any fast drive
#                  and has no Z: twin (the 115 non-Kontakt scans) -> hide visible=0.
#   OTHER        : anything that doesn't fit -> shown for manual review.
#
# Nothing is written. Output drives the converge script.
#
# Collation-safe: dumps unfiltered, classifies in bash.

set -u
K8="/mnt/workspace/VST Install/Kontakt Portable/UserData/Kontakt 8"
DB="${K8}/komplete.db3"

WDBLACK_LX="/mnt/wd_black/Kontakt Libraries"
SDD1_LX="/mnt/btrfs_disk/Kontakt Libraries"
WDBLACK_Z='Z:\mnt\wd_black\Kontakt Libraries'
SDD1_Z='Z:\mnt\btrfs_disk\Kontakt Libraries'

[ -f "$DB" ] || { echo "ABORT: no DB at $DB"; exit 1; }

# fast-drive folder-name -> Z path
declare -A MAP
add_map(){ local d="$1" zb="$2" sub="$3" n; [ -d "$d" ]||return
  while IFS= read -r n; do [ -z "$n" ]&&continue; [ -z "${MAP[$n]:-}" ]&&MAP["$n"]="${zb}\\${sub}\\${n}"; done < <(ls -1 "$d"); }
add_map "${WDBLACK_LX}/Player" "$WDBLACK_Z" Player
add_map "${WDBLACK_LX}/Custom" "$WDBLACK_Z" Custom
add_map "${SDD1_LX}/Player"    "$SDD1_Z"    Player
add_map "${SDD1_LX}/Custom"    "$SDD1_Z"    Custom
echo "Indexed ${#MAP[@]} fast-drive folders."

# dump: id | content_type | visible | path
sqlite3 -separator '|' "$DB" \
  "SELECT id, content_type, visible, path FROM k_content_path;" > /tmp/cz_all.txt 2>/dev/null

# set of all paths currently in the DB (to detect a taken Z: twin)
declare -A PATHSET
while IFS='|' read -r id ct vis path; do
  [ -z "$id" ] && continue
  PATHSET["$path"]=1
done < /tmp/cz_all.txt

echo
echo "row counts:"
echo -n "  total: "; grep -c '|' /tmp/cz_all.txt
echo -n "  Z: :   "; grep -c '|Z:' /tmp/cz_all.txt
echo -n "  D: :   "; grep -c '|D:' /tmp/cz_all.txt
echo -n "  F: :   "; grep -c '|F:' /tmp/cz_all.txt

echo
echo "======================= CLASSIFICATION ======================="
: > /tmp/cz_repoint.txt
: > /tmp/cz_duphide.txt
: > /tmp/cz_junkhide.txt
: > /tmp/cz_other.txt

while IFS='|' read -r id ct vis path; do
  [ -z "$id" ] && continue
  case "$path" in
    Z:*) continue ;;              # already Z:, leave alone
  esac
  folder="${path##*\\}"
  ztarget="${MAP[$folder]:-}"
  if [ -n "$ztarget" ]; then
    if [ -n "${PATHSET[$ztarget]:-}" ]; then
      # Z twin already exists -> this D:/F: row is a redundant duplicate
      echo "$id|$ct|$vis|$path   ==DUP-OF==> $ztarget" >> /tmp/cz_duphide.txt
    else
      # folder is on a fast drive and the Z path is free -> repoint
      echo "$id|$ct|$vis|$path   ==REPOINT==> $ztarget" >> /tmp/cz_repoint.txt
    fi
  else
    # not a fast-drive library folder
    if printf '%s' "$path" | grep -qiE 'User Content|UserData'; then
      echo "$id|$ct|$vis|$path" >> /tmp/cz_other.txt
    else
      echo "$id|$ct|$vis|$path" >> /tmp/cz_junkhide.txt
    fi
  fi
done < /tmp/cz_all.txt

echo
echo "--- REPOINTABLE (D:/F: -> free Z: path; will UPDATE) : $(grep -c '|' /tmp/cz_repoint.txt) ---"
cat /tmp/cz_repoint.txt
echo
echo "--- DUP-HIDE (Z: twin already exists; will visible=0) : $(grep -c '|' /tmp/cz_duphide.txt) ---"
cat /tmp/cz_duphide.txt
echo
echo "--- OTHER / needs review (User Content / UserData etc.) : $(grep -c '|' /tmp/cz_other.txt) ---"
cat /tmp/cz_other.txt
echo
echo "--- JUNK-HIDE (non-Kontakt D: scans; will visible=0) : $(grep -c '|' /tmp/cz_junkhide.txt) ---"
cat /tmp/cz_junkhide.txt

echo
echo "=== READ-ONLY. Paste this back so the converge script can be built exactly. ==="
