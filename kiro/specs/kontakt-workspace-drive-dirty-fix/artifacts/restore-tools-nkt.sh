#!/usr/bin/env bash
#
# restore-tools-nkt.sh
#
# Chords/Phrases "This patch is corrupted and cannot be loaded!" — confirmed cause:
# their .nkt instrument files were rewritten/corrupted by Kontakt-under-Wine (mtime
# sep 2 22:17), and ALL .nkt DIFFER from the pristine BACKUP. The .nkr sample
# containers and .ogg previews are IDENTICAL to backup and stay. Nothing is missing
# from backup. Fix = restore ONLY the .nkt files from BACKUP.
#
# Kontakt CLOSED. Current (corrupted) .nkt files are saved first, so this is reversible.
#
# Usage:
#   bash restore-tools-nkt.sh            # dry-run: counts of .nkt to restore
#   bash restore-tools-nkt.sh apply

set -u
MODE="${1:-dryrun}"
WS="/mnt/workspace/VST Install/Kontakt Portable/Kontakt 8/Content/Tools"
BK="/mnt/workspace/BACKUP/Kontakt 8/Content/Tools"
STAMP="$(date +%Y%m%d_%H%M%S)"
SAVE="/mnt/workspace/VST Install/Kontakt Portable/UserData/_kiro_tools_nkt_backup_${STAMP}"

if pgrep -fi 'Kontakt 8.exe' | grep -qv grep; then
  echo "ABORT: Kontakt running. File->Exit cleanly first."; exit 1
fi
for lib in Chords Phrases; do
  [ -d "$BK/$lib/Instruments" ] || { echo "ABORT: backup missing: $BK/$lib/Instruments"; exit 1; }
done

echo "=== .nkt files that DIFFER from backup (will be restored) ==="
total=0
for lib in Chords Phrases; do
  n=0
  while IFS= read -r f; do
    rel="${f#"$BK"/}"
    if [ -e "$WS/$rel" ] && ! cmp -s "$f" "$WS/$rel"; then n=$((n+1)); fi
  done < <(find "$BK/$lib/Instruments" -maxdepth 1 -type f -iname '*.nkt')
  echo "  $lib: $n .nkt differ (of $(find "$BK/$lib/Instruments" -maxdepth 1 -type f -iname '*.nkt' | wc -l) total)"
  total=$((total+n))
done
echo "  TOTAL to restore: $total"

if [ "$MODE" != "apply" ]; then
  echo; echo "DRY-RUN. Re-run with:  bash $0 apply"; exit 0
fi

echo
echo "=== save current (corrupted) .nkt -> $SAVE ==="
for lib in Chords Phrases; do
  mkdir -p "$SAVE/$lib"
  find "$WS/$lib/Instruments" -maxdepth 1 -type f -iname '*.nkt' -exec cp -av {} "$SAVE/$lib/" \; >/dev/null 2>&1
done
echo "  saved."

echo "=== restore pristine .nkt from BACKUP ==="
for lib in Chords Phrases; do
  c=0
  while IFS= read -r f; do
    rel="${f#"$BK"/}"
    cp -a "$f" "$WS/$rel" && c=$((c+1))
  done < <(find "$BK/$lib/Instruments" -maxdepth 1 -type f -iname '*.nkt')
  echo "  $lib: restored $c .nkt"
done

echo
echo "=== verify: any .nkt still differ? (should be 0) ==="
still=0
for lib in Chords Phrases; do
  while IFS= read -r f; do
    rel="${f#"$BK"/}"
    cmp -s "$f" "$WS/$rel" || still=$((still+1))
  done < <(find "$BK/$lib/Instruments" -maxdepth 1 -type f -iname '*.nkt')
done
echo "  .nkt still differing: $still"

echo
echo "ROLLBACK (Kontakt closed): copy the saved files back, e.g.:"
echo "  cp -av \"$SAVE/Chords/.\"  \"$WS/Chords/Instruments/\""
echo "  cp -av \"$SAVE/Phrases/.\" \"$WS/Phrases/Instruments/\""
echo
echo "NEXT: launch Kontakt, load a Chords + a Phrases patch — should load without the corrupt alert."
