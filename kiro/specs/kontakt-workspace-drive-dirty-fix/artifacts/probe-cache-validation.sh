#!/usr/bin/env bash
# probe-cache-validation.sh (READ-ONLY)
# Prior session proved (2026-09-05) that ALL tiles rendered after ntfs-3g switch, and that blank tiles =
# Kontakt failing .cache identity/mtime validation. Some tiles are blank AGAIN now. So a subset of caches
# now FAIL validation. Compare, for blank vs working libs: cache mtime, the library's ContentDir mtime,
# and whether the ContentDir path in Settings.cfg still exists/matches. Also compare live cache mtimes
# vs the known-good snapshot (which rendered all tiles) to see which caches changed.
set -u
UD="/mnt/workspace/VST Install/Kontakt Portable/UserData"
LIVE="$UD/Kontakt 8/LibrariesCache"
SNAP="/mnt/wd_black/kontakt-known-good-20260907_123950/kontakt_userdata/LibrariesCache"
CFG="$UD/Settings.cfg"

# map SNPID -> live cache file (name contains SNPID token after leading K)
cache_for() { find "$LIVE" -maxdepth 1 -iname "*$1*.cache" 2>/dev/null | head -1; }

echo "===== per-library: cache mtime (live) vs snapshot, + ContentDir existence ====="
# name|SNPID   (blank first, then working controls)
for pair in \
  "Middle East|K01|blank" "Balinese Gamelan|408|blank" "Straylight|K08|blank" "Soul Sessions|KL1|blank" \
  "East Asia|K11|blank" "India|587|blank" "Piano Colors|K25|blank" \
  "Amati Viola|K21|WORKS" "Butch Vig Drums|KE7|WORKS" "Stradivari Violin|K15|WORKS" "Cloud Supply|K18|WORKS"; do
  name="${pair%%|*}"; rest="${pair#*|}"; sn="${rest%%|*}"; tag="${rest#*|}"
  lc=$(cache_for "$sn")
  lcm=$( [ -n "$lc" ] && date -r "$lc" '+%Y-%m-%d %H:%M' || echo "-none-")
  sc="$SNAP/$(basename "$lc" 2>/dev/null)"
  scm=$( [ -f "$sc" ] && date -r "$sc" '+%Y-%m-%d %H:%M' || echo "-n/a-")
  same=$( [ -n "$lc" ] && [ -f "$sc" ] && cmp -s "$lc" "$sc" && echo "IDENTICAL" || echo "DIFFERS/na" )
  # ContentDir from Settings.cfg (strip CRLF)
  cdir=$(awk -v n="Name=sz:$name" 'BEGIN{RS="\r?\n"} $0==n{f=1} f&&/^ContentDir=sz:/{sub(/^ContentDir=sz:/,"");print;exit}' "$CFG" 2>/dev/null)
  # translate Z:\mnt\... to /mnt/... to test existence
  lnx=$(printf '%s' "$cdir" | sed -E 's/^[A-Za-z]:\\//; s/\\/\//g' ); lnx="/$lnx"
  exists=$( [ -n "$cdir" ] && [ -d "$lnx" ] && echo "DIR OK" || echo "DIR MISSING/na" )
  printf "  [%-5s] %-22s SNPID=%-4s cache=%s  live=%s snap=%s %s\n" "$tag" "$name" "$sn" "$(basename "${lc:-none}")" "$lcm" "$scm" "$same"
  printf "           ContentDir=%s -> %s\n" "${cdir:-<none>}" "$exists"
done
echo
echo "===== summary: are BLANK libs' caches byte-identical to the snapshot that rendered them? ====="
echo "  If IDENTICAL but tile still blank => validation keys on live library mtime/path, not cache content."
echo "  If ContentDir DIR MISSING for blanks => path mismatch is why cache fails validation (fixable: repoint)."
echo
echo "READ-ONLY."
