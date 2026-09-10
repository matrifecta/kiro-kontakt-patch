#!/usr/bin/env bash
# probe-browser-index.sh (READ-ONLY)
# On-disk caches/artwork/paths are IDENTICAL for blank vs working libs (proven). So the tile decision is
# in Kontakt's BROWSER INDEX/DB built at scan, not the files. Locate that index (pal.db / browser db /
# any db that lists libraries with a 'tile'/'thumbnail'/visibility flag), compare live vs snapshot mtime,
# and see if it looks stale/half-built vs the known-good snapshot that rendered all tiles.
set -u
UD="/mnt/workspace/VST Install/Kontakt Portable/UserData"
SNAPUD="/mnt/wd_black/kontakt-known-good-20260907_123950/kontakt_userdata"

echo "===== candidate browser-index / db files under live UserData ====="
find "$UD" -maxdepth 3 -type f \( -iname '*.db' -o -iname '*.db3' -o -iname 'pal*' -o -iname '*hints*' -o -iname '*browser*' -o -iname '*.idx' \) \
  ! -path '*_kiro_*' 2>/dev/null -printf '  %TY-%Tm-%Td %TH:%TM  %10s  %p\n' | sort | sed "s#$UD/#  ...#"
echo

echo "===== same set in the known-good snapshot (rendered all tiles) ====="
find "$SNAPUD" -maxdepth 3 -type f \( -iname '*.db' -o -iname '*.db3' -o -iname 'pal*' -o -iname '*hints*' -o -iname '*browser*' -o -iname '*.idx' \) \
  2>/dev/null -printf '  %TY-%Tm-%Td %TH:%TM  %10s  %p\n' | sort | sed "s#$SNAPUD/#  ...#"
echo

echo "===== LibraryHints.xml (browser hints) live vs snapshot: mtime + size + do blank libs appear? ====="
for lh in "$UD/Service Center/LibraryHints.xml" "$SNAPUD/Service Center/LibraryHints.xml"; do
  echo "--- $lh ---"
  if [ -f "$lh" ]; then
    ls -la "$lh" | awk '{print "    size="$5" mtime="$6" "$7" "$8}'
    for L in "Middle East" "Amati Viola" "Straylight" "Cloud Supply"; do
      c=$(grep -c "$L" "$lh" 2>/dev/null); echo "    mentions '$L': $c"
    done
  else echo "    (missing)"; fi
done
echo

echo "===== komplete.db3 present? (the browser DB Kontakt actually reads for tiles) ====="
ls -la "$UD/komplete.db3" 2>/dev/null | sed 's/^/  /'
ls -la "$SNAPUD/komplete.db3" 2>/dev/null | sed 's/^/  snap: /'
echo
echo "READ-ONLY. Goal: identify the browser-index file that differs from the tiles-rendered snapshot."
echo "If a db/index is newer/half-built vs snapshot, restoring THAT from snapshot (Kontakt closed) should"
echo "bring tiles back without touching caches/artwork."
