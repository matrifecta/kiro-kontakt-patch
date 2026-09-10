#!/usr/bin/env bash
# check-snpid-cache-direct.sh (READ-ONLY)
# CRLF-proof: skip awk parsing of Settings.cfg. Use SNPIDs read directly from the earlier Settings.cfg
# dump, and test whether a matching cache file exists. Kontakt cache files are named like K<SNPID><digits>.cache
# (a leading 'K' then the SNPID token). We match on the SNPID token appearing in the filename.
set -u
LIVE="/mnt/workspace/VST Install/Kontakt Portable/UserData/Kontakt 8/LibrariesCache"

echo "===== all live cache filenames (for reference) ====="
find "$LIVE" -maxdepth 1 -iname '*.cache' -printf '%f\n' 2>/dev/null | sort | sed 's/^/  /'
echo

echo "===== does a cache exist whose name contains each SNPID token? ====="
# name|SNPID  (blanks in screenshot first, then known-good controls)
for pair in \
  "Balinese Gamelan|408" "Middle East|K01" "Straylight|K08" "Soul Sessions|KL1" \
  "Session Keys Electric R|578" "India|587" "East Asia|K11" "Mass|U91" \
  "Picked Acoustic|K10" "Tablas|502" \
  "Amati Viola|K21" "Butch Vig Drums|KE7" "Stradivari Violin|K15" "5Elements|Q37" "Cloud Supply|K18"; do
  name="${pair%|*}"; sn="${pair#*|}"
  hits=$(find "$LIVE" -maxdepth 1 -iname "*${sn}*.cache" 2>/dev/null | wc -l)
  files=$(find "$LIVE" -maxdepth 1 -iname "*${sn}*.cache" -printf '%f ' 2>/dev/null)
  printf "  %-28s SNPID=%-4s cache=%s  %s\n" "$name" "$sn" "$hits" "$files"
done
echo
echo "READ-ONLY. NOTE: substring match can false-positive on short numeric SNPIDs; treat the letter-prefixed"
echo "ones (K01,K08,KL1,K11,K21,KE7,K15,Q37,K18,U91,K10) as reliable. Compare blanks vs controls."
