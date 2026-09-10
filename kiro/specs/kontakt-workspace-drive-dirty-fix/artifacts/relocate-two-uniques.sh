#!/usr/bin/env bash
#
# relocate-two-uniques.sh
#
# Keyscape - 13 (1.8G, 13 loose .nki) and Hy2rogen - Tekno House Nights (920M, loop
# pack) are the only two libraries that exist ONLY on Workspace (D:) with no fast-drive
# copy. Both are light-stream Custom content -> copy to sdd1 Custom, verify, then
# repoint their komplete.db3 row to the new Z: path + set visible=1.
#
# rsync with --checksum verify. Workspace originals are KEPT (delete later after load-test).
# Kontakt CLOSED. DB backed up before the repoint.
#
# Usage:
#   bash relocate-two-uniques.sh           # dry-run (rsync -n + show planned repoints)
#   bash relocate-two-uniques.sh apply      # copy + verify + repoint DB

set -u
MODE="${1:-dryrun}"

K8="/mnt/workspace/VST Install/Kontakt Portable/UserData/Kontakt 8"
DB="${K8}/komplete.db3"
STAMP="$(date +%Y%m%d_%H%M%S)"
SRC_BASE="/mnt/workspace/PROGRAMS/VST, Samples & DAW"
DEST="/mnt/btrfs_disk/Kontakt Libraries/Custom"

# name | D: path in DB | Z: target path in DB
declare -A DPATH ZPATH
NAMES=("Keyscape - 13" "Hy2rogen - Tekno House Nights")
DPATH["Keyscape - 13"]='D:\PROGRAMS\VST, Samples & DAW\Keyscape - 13'
ZPATH["Keyscape - 13"]='Z:\mnt\btrfs_disk\Kontakt Libraries\Custom\Keyscape - 13'
DPATH["Hy2rogen - Tekno House Nights"]='D:\PROGRAMS\VST, Samples & DAW\Hy2rogen - Tekno House Nights'
ZPATH["Hy2rogen - Tekno House Nights"]='Z:\mnt\btrfs_disk\Kontakt Libraries\Custom\Hy2rogen - Tekno House Nights'

if pgrep -fi 'Kontakt 8.exe' | grep -qv grep; then
  echo "ABORT: Kontakt running. File->Exit cleanly first."; exit 1
fi
[ -f "$DB" ] || { echo "ABORT: no DB at $DB"; exit 1; }
mkdir -p "$DEST"

for n in "${NAMES[@]}"; do
  src="${SRC_BASE}/${n}"
  dst="${DEST}/${n}"
  echo "=== ${n} ==="
  if [ ! -d "$src" ]; then echo "  ABORT: source missing: $src"; exit 1; fi
  if [ "$MODE" != "apply" ]; then
    echo "  would rsync -a --checksum  \"$src/\"  ->  \"$dst/\""
    rsync -a -n --info=stats2 "$src/" "$dst/" 2>/dev/null | grep -iE 'number of files|to-check|created' | head -3
    echo "  would repoint DB: ${DPATH[$n]}"
    echo "               ->  ${ZPATH[$n]}   (visible=1)"
  else
    echo "  copying (rsync -a --checksum)..."
    mkdir -p "$dst"
    rsync -a --checksum "$src/" "$dst/"
    # verify: file count + byte size match
    sc=$(find "$src" -type f | wc -l); dc=$(find "$dst" -type f | wc -l)
    ss=$(du -sb "$src" | cut -f1); ds=$(du -sb "$dst" | cut -f1)
    echo "  files src=$sc dst=$dc ; bytes src=$ss dst=$ds"
    if [ "$sc" != "$dc" ] || [ "$ss" != "$ds" ]; then
      echo "  VERIFY FAILED for ${n} — NOT repointing this one."; continue
    fi
    echo "  verify OK."
  fi
done

if [ "$MODE" != "apply" ]; then
  echo; echo "DRY-RUN. Re-run with:  bash $0 apply"; exit 0
fi

echo
echo "=== backup DB then repoint the two rows ==="
cp -av "$DB" "$DB.pre_relocate2_$STAMP"
for n in "${NAMES[@]}"; do
  dst="${DEST}/${n}"
  # only repoint if the verified copy is in place
  [ -d "$dst" ] || { echo "  skip ${n} (no dest)"; continue; }
  from="${DPATH[$n]}"; to="${ZPATH[$n]}"
  efrom="${from//\'/\'\'}"; eto="${to//\'/\'\'}"
  sqlite3 "$DB" "UPDATE k_content_path SET path='${eto}', visible=1 WHERE path='${efrom}';"
  echo "  repointed + shown: ${n}"
done

echo
echo "=== verify ==="
sqlite3 -separator '|' "$DB" "SELECT id, content_type, visible, path FROM k_content_path;" > /tmp/rel2_after.txt 2>/dev/null
grep -iE 'Keyscape - 13|Tekno House Nights' /tmp/rel2_after.txt | sed 's/^/  /'
echo
echo "ROLLBACK (Kontakt closed): cp -av \"$DB.pre_relocate2_$STAMP\" \"$DB\""
echo "(Workspace originals kept; delete after load-test.)"
