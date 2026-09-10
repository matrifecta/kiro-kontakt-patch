#!/usr/bin/env bash
# map-snpid-cache.sh (READ-ONLY)
# Kontakt names LibrariesCache files by SNPID (e.g. K01xxxx.cache = Middle East SNPID K01), NOT by
# library name — so the earlier name-match was meaningless. For each blank Player lib the user recalls
# tiling before, look up its SNPID from Settings.cfg and check if a matching <SNPID>*.cache exists live.
# This tells us if these libs genuinely lack a cache (-> blank is expected) or have one that isn't rendering.
set -u
CFG="/mnt/workspace/VST Install/Kontakt Portable/UserData/Settings.cfg"
LIVE="/mnt/workspace/VST Install/Kontakt Portable/UserData/Kontakt 8/LibrariesCache"

echo "===== SNPID -> cache presence for the blank Player libs in question ====="
# name : as it appears in Settings.cfg [section]/Name
for name in "Balinese Gamelan" "Middle East" "Straylight" "Soul Sessions" "Session Keys Electric R" \
            "India" "East Asia" "Mass" "Session Guitarist - Picked Acoustic" "Tablas" \
            "Amati Viola" "Butch Vig Drums" "Stradivari Violin"; do
  # find SNPID: the line 'SNPID=sz:XXX' following the matching 'Name=sz:<name>'
  snpid=$(awk -v n="Name=sz:$name" '
    $0==n {found=1}
    found && /^SNPID=sz:/ {sub(/^SNPID=sz:/,""); print; exit}
  ' "$CFG" 2>/dev/null)
  if [ -z "$snpid" ]; then
    echo "  $name : (no SNPID found in Settings.cfg)"
    continue
  fi
  # cache filenames start with the SNPID token (letters+digits) — match prefix
  hits=$(find "$LIVE" -maxdepth 1 -iname "${snpid}*.cache" 2>/dev/null | wc -l)
  extra=""
  [ "$hits" -gt 0 ] && extra="  -> $(find "$LIVE" -maxdepth 1 -iname "${snpid}*.cache" -printf '%f ' 2>/dev/null)"
  printf "  %-34s SNPID=%-5s cache=%s%s\n" "$name" "$snpid" "$hits" "$extra"
done
echo
echo "  (control: Amati Viola / Butch Vig Drums / Stradivari Violin tile correctly — they SHOULD show cache=1)"
echo
echo "READ-ONLY. If a blank lib shows cache=0 => it has no cache (blank is the real state, not a regression)."
echo "If it shows cache=1 => cache exists but isn't rendering (different problem)."
