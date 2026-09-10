#!/usr/bin/env bash
#
# db-converge-hide-nonz.sh
#
# Converge the RESTORED all-tiles DB to Z:-only WITHOUT deleting anything.
# Built from db-classify-nonz.sh output (2026-09-07):
#   - DUP-HIDE (14): D:\PROGRAMS type-3 rows whose Z: twin already shows the tile -> visible=0
#   - JUNK-HIDE (126): non-Kontakt scans + D: Content/Tools dupes + parent scan row 134
#       + stale F: GetGood sub-path -> visible=0
#   - OTHER (1): F: User Content -> REPOINT to Z: (this path is free, safe UPDATE)
#
# WHY hide (visible=0) not delete: keeps every row + its k_sound_info links intact so
# this is fully reversible with one UPDATE; the browser simply stops showing the
# hidden rows. The Z: twins keep their tiles. Net effect: all tiles, Z:-only browser,
# no D:/F: entries visible, and NOTHING for Kontakt to re-expand next launch.
#
# Selection is by EXACT id (from the classifier) so nothing else is touched.
# Kontakt CLOSED. DB backed up first. Reversible.
#
# Usage:
#   bash db-converge-hide-nonz.sh          # dry-run: show what changes
#   bash db-converge-hide-nonz.sh apply     # apply

set -u
MODE="${1:-dryrun}"

K8="/mnt/workspace/VST Install/Kontakt Portable/UserData/Kontakt 8"
DB="${K8}/komplete.db3"
STAMP="$(date +%Y%m%d_%H%M%S)"

if pgrep -fi 'Kontakt 8.exe' | grep -qv grep; then
  echo "ABORT: Kontakt running. File->Exit cleanly first."; exit 1
fi
[ -f "$DB" ] || { echo "ABORT: no DB at $DB"; exit 1; }

# ids to hide (visible=0): 14 DUP + 126 JUNK  (exact ids from db-classify-nonz.sh)
HIDE_IDS="151,153,158,172,206,210,238,239,242,243,244,255,261,262,\
18,130,131,132,133,134,138,139,140,141,142,143,144,145,147,148,149,150,152,157,159,160,165,166,169,170,171,174,175,179,181,184,185,186,192,193,195,196,197,198,199,200,201,202,203,204,207,208,209,211,212,213,214,215,216,217,218,219,220,221,224,225,226,227,228,232,233,234,236,237,240,241,245,246,248,249,250,251,252,253,254,256,257,258,259,264,265,266,267,268,269,270,271,272,277,278,279,280,282,283,284,285,286,287,288,289,290,291,292,293,294,295,296,297,298,299,300,301,302,303,304,305,306,308,309,310"

# F: User Content -> Z: repoint (id 50)
FUSER_FROM='F:\VST Install\Kontakt Portable\UserData\User Content'
FUSER_TO='Z:\mnt\workspace\VST Install\Kontakt Portable\UserData\User Content'

echo "=== PLAN ==="
echo "  visible=0 on $(echo "$HIDE_IDS" | tr ',' '\n' | grep -c '[0-9]') rows (14 dup + 126 junk)"
echo "  repoint id 50: F: User Content -> Z:"
echo

if [ "$MODE" != "apply" ]; then
  echo "DRY-RUN. Rows that WOULD be hidden (id|type|visible|path):"
  sqlite3 -separator '|' "$DB" "SELECT id, content_type, visible, path FROM k_content_path;" 2>/dev/null \
    | awk -F'|' -v ids="$HIDE_IDS" 'BEGIN{n=split(ids,a,","); for(i=1;i<=n;i++) h[a[i]+0]=1} ($1+0) in h {print "  "$0}'
  echo
  echo "  id 50 currently:"
  sqlite3 -separator '|' "$DB" "SELECT id, content_type, visible, path FROM k_content_path;" 2>/dev/null | grep '^50|'
  echo
  echo "Re-run with:  bash $0 apply"
  exit 0
fi

echo "=== backup DB ==="
cp -av "$DB" "$DB.pre_hidenonz_$STAMP"

echo "=== hide the 140 dup/junk rows (visible=0) ==="
sqlite3 "$DB" "UPDATE k_content_path SET visible=0 WHERE id IN (${HIDE_IDS});"

echo "=== repoint F: User Content -> Z: (id 50) ==="
esc_to="${FUSER_TO//\'/\'\'}"
esc_from="${FUSER_FROM//\'/\'\'}"
sqlite3 "$DB" "UPDATE k_content_path SET path='${esc_to}' WHERE path='${esc_from}';"

echo
echo "=== AFTER (collation-safe dump + grep) ==="
sqlite3 -separator '|' "$DB" "SELECT id, content_type, visible, path FROM k_content_path;" > /tmp/conv_after.txt 2>/dev/null
echo -n "total rows:        "; grep -c '|' /tmp/conv_after.txt
echo -n "VISIBLE rows:      "; awk -F'|' '$3==1' /tmp/conv_after.txt | grep -c '|'
echo -n "  of which Z:      "; awk -F'|' '$3==1' /tmp/conv_after.txt | grep -c '|Z:'
echo -n "  of which D: (VIS, expect 0): "; awk -F'|' '$3==1' /tmp/conv_after.txt | grep -c '|D:'
echo -n "  of which F: (VIS, expect 0): "; awk -F'|' '$3==1' /tmp/conv_after.txt | grep -c '|F:'
echo -n "HIDDEN rows:       "; awk -F'|' '$3==0' /tmp/conv_after.txt | grep -c '|'

echo
echo "=== any VISIBLE row still on D: or F: (should be EMPTY) ==="
awk -F'|' '$3==1' /tmp/conv_after.txt | grep -E '\|D:|\|F:' || echo "  (none — clean)"

echo "=== remove stale lock ==="
rm -fv "${K8}/lock.lck" 2>/dev/null || true

echo
echo "=== DONE. All tiles via Z: twins; D:/F: rows hidden (not deleted); F: User Content repointed. ==="
echo "ROLLBACK (Kontakt closed):"
echo "  cp -av \"$DB.pre_hidenonz_$STAMP\" \"$DB\""
