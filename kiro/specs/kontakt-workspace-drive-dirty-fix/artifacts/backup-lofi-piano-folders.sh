#!/usr/bin/env bash
# backup-lofi-piano-folders.sh — before Batch re-save (which OVERWRITES .nki/.nkl/.nkm), back up the two
# preset folders to WD Black so we can restore the exact pre-resave instruments if anything goes wrong.
set -u
MODE="${1:-dryrun}"
SRC="/mnt/workspace/VST Install/Kontakt Portable/Kontakt 8/Content/Presets"
DEST="/mnt/wd_black/KONTAKT BACKUP/presets_pre_resave_$(date +%Y%m%d_%H%M%S)"
LIBS=("Lo-Fi Vibes" "Piano Uno")

echo "backup dest: $DEST"
for l in "${LIBS[@]}"; do
  d="$SRC/$l"
  echo "  $l -> $(du -sh "$d" 2>/dev/null | cut -f1)"
done
if ! mountpoint -q /mnt/wd_black; then echo "ABORT: /mnt/wd_black not mounted"; exit 1; fi
if [ "$MODE" != apply ]; then echo "DRY-RUN. Re-run: bash $0 apply"; exit 0; fi
mkdir -p "$DEST"
for l in "${LIBS[@]}"; do
  echo "copying $l ..."
  cp -a "$SRC/$l" "$DEST/"
done
echo "done. backup at: $DEST"
echo "ROLLBACK a lib (Kontakt closed): rm -rf \"$SRC/<lib>\"; cp -a \"$DEST/<lib>\" \"$SRC/\""
