#!/usr/bin/env bash
# diff-tiles-vs-knowngood.sh (READ-ONLY)
# Player-library tiles that used to render (Balinese Gamelan, Middle East, Straylight, Soul Sessions,
# Session Keys Electric R, India, East Asia, Mass, Picked Acoustic, Tablas...) now show folder icons.
# Compare the LIVE LibrariesCache against the known-good snapshot to see what changed: filenames, count,
# mtimes, and whether the live caches differ byte-wise from the snapshot (indicating regeneration/invalidation).
set -u
LIVE="/mnt/workspace/VST Install/Kontakt Portable/UserData/Kontakt 8/LibrariesCache"
SNAPUD="/mnt/wd_black/kontakt-known-good-20260907_123950/kontakt_userdata"
# locate the snapshot's LibrariesCache
SNAP="$(find "$SNAPUD" -type d -iname 'LibrariesCache' 2>/dev/null | head -1)"

echo "===== live LibrariesCache ====="
echo "  path: $LIVE"
echo "  count: $(find "$LIVE" -maxdepth 1 -iname '*.cache' 2>/dev/null | wc -l) .cache"
echo "  newest 5 (mtime) — did some get rewritten recently?"
find "$LIVE" -maxdepth 1 -iname '*.cache' -printf '%TY-%Tm-%Td %TH:%TM  %f\n' 2>/dev/null | sort | tail -5 | sed 's/^/    /'
echo "  oldest 5:"
find "$LIVE" -maxdepth 1 -iname '*.cache' -printf '%TY-%Tm-%Td %TH:%TM  %f\n' 2>/dev/null | sort | head -5 | sed 's/^/    /'
echo

echo "===== known-good snapshot LibrariesCache ====="
if [ -n "$SNAP" ]; then
  echo "  path: $SNAP"
  echo "  count: $(find "$SNAP" -maxdepth 1 -iname '*.cache' 2>/dev/null | wc -l) .cache"
else
  echo "  NOT FOUND under $SNAPUD — searching whole snapshot:"
  find "/mnt/wd_black/kontakt-known-good-20260907_123950" -type d -iname 'LibrariesCache' 2>/dev/null | sed 's/^/    /'
fi
echo

echo "===== which .cache exist in snapshot but MISSING live (lost tiles)? ====="
if [ -n "$SNAP" ]; then
  comm -23 \
    <(find "$SNAP" -maxdepth 1 -iname '*.cache' -printf '%f\n' | sort) \
    <(find "$LIVE" -maxdepth 1 -iname '*.cache' -printf '%f\n' | sort) | sed 's/^/    MISSING now: /'
  echo "  --- present in BOTH but byte-DIFFERENT (possibly invalidated) ---"
  while IFS= read -r f; do
    [ -f "$LIVE/$f" ] && [ -f "$SNAP/$f" ] || continue
    cmp -s "$LIVE/$f" "$SNAP/$f" || echo "    DIFFERS: $f"
  done < <(find "$SNAP" -maxdepth 1 -iname '*.cache' -printf '%f\n')
fi
echo

echo "===== cross-check the specific regressed Player libs (name match in cache filenames) ====="
for lib in "Balinese" "Middle East" "Straylight" "Soul Session" "Session Keys" "India" "East Asia" "Mass" "Picked Acoustic" "Tablas"; do
  n=$(find "$LIVE" -maxdepth 1 -iname "*${lib}*.cache" 2>/dev/null | wc -l)
  echo "    '$lib' : $n matching live .cache"
done
echo
echo "READ-ONLY. If snapshot has caches the live is MISSING (or byte-different), restoring LibrariesCache"
echo "from the snapshot (Kontakt closed) should bring those Player tiles back. Custom-lib blanks stay blank."
