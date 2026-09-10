#!/usr/bin/env bash
# map-snpid-cache2.sh (READ-ONLY)
# Fixed SNPID lookup: parse Settings.cfg per [section] block (SNPID may appear before or after Name),
# then check if a <SNPID>*.cache exists in LibrariesCache. Kontakt names caches by SNPID prefix.
set -u
CFG="/mnt/workspace/VST Install/Kontakt Portable/UserData/Settings.cfg"
LIVE="/mnt/workspace/VST Install/Kontakt Portable/UserData/Kontakt 8/LibrariesCache"

# Build a Name->SNPID map by scanning blocks: a block starts at '[' and we capture Name= and SNPID= within it.
map_file="$(mktemp)"
awk '
  /^\[/          { name=""; snpid="" }
  /^Name=sz:/    { n=$0; sub(/^Name=sz:/,"",n); name=n }
  /^SNPID=sz:/   { s=$0; sub(/^SNPID=sz:/,"",s); snpid=s;
                   if(name!="" && snpid!="") print name "\t" snpid }
' "$CFG" > "$map_file" 2>/dev/null

echo "===== SNPID + cache presence (fixed parser) ====="
for name in "Balinese Gamelan" "Middle East" "Straylight" "Soul Sessions" "Session Keys Electric R" \
            "India" "East Asia" "Mass" "Session Guitarist - Picked Acoustic" "Tablas" \
            "Amati Viola" "Butch Vig Drums" "Stradivari Violin" "5Elements" "Cloud Supply"; do
  snpid=$(awk -F'\t' -v n="$name" '$1==n{print $2; exit}' "$map_file")
  if [ -z "$snpid" ]; then printf "  %-34s (not in Settings.cfg)\n" "$name"; continue; fi
  hits=$(find "$LIVE" -maxdepth 1 -iname "${snpid}*.cache" 2>/dev/null | wc -l)
  files=$(find "$LIVE" -maxdepth 1 -iname "${snpid}*.cache" -printf '%f ' 2>/dev/null)
  printf "  %-34s SNPID=%-5s cache=%s  %s\n" "$name" "$snpid" "$hits" "$files"
done
rm -f "$map_file"
echo
echo "  controls that DO tile: Amati Viola, Butch Vig Drums, Stradivari Violin, 5Elements, Cloud Supply"
echo "  -> if these show cache>=1 and the blanks show cache=0, blanks simply lack a cache (expected)."
echo "  -> if a blank shows cache>=1, its cache exists but isn't validating (investigate that one)."
echo
echo "READ-ONLY."
