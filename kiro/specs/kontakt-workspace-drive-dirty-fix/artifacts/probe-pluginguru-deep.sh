#!/usr/bin/env bash
# probe-pluginguru-deep.sh (READ-ONLY)
# The dotted image dir matching the folder name still doesn't render. Find the REAL tile key.
# 1) Diff a WORKING made-tile (Tropical Trap) vs PlugInGuru: exact meta bytes, png headers.
# 2) Look for any OTHER place a name/key is stored: the lib's Instruments/*.nki filenames (browser often keys
#    the tile by the NKS 'library name' embedded in the .nki/nicnt, NOT the folder), and strings in the .nki.
# 3) Check whether the browser entry name the user sees ('PlugInGuru.MegaMagic.Bells.Winds.KONTAKT') appears
#    verbatim anywhere in the lib (folder) or db as the authoritative key.
set -u
NIIMG="/mnt/workspace/VST Install/Kontakt Portable/UserData/NI Resources/image"
LIB="/mnt/btrfs_disk/Kontakt Libraries/Custom/PlugInGuru.MegaMagic.Bells.Winds.KONTAKT"

echo "=== 1) meta byte compare: Tropical Trap (works) vs PlugInGuru ==="
for n in "Sonic Mechanics - Tropical Trap" "PlugInGuru.MegaMagic.Bells.Winds.KONTAKT"; do
  m="$NIIMG/$n/$n.meta"
  echo "  --- $n.meta (bytes=$(stat -c '%s' "$m" 2>/dev/null)):"
  sed 's/^/      /' "$m" 2>/dev/null
done

echo
echo "=== 2) Instruments/*.nki in the lib (the browser may key the tile by the .nki NKS name) ==="
find "$LIB/Instruments" -maxdepth 2 -iname '*.nki' 2>/dev/null | sed 's/^/  /' | head -20
echo "  -- names embedded in the first .nki (look for a library/product name string):"
nki="$(find "$LIB/Instruments" -maxdepth 2 -iname '*.nki' 2>/dev/null | head -1)"
if [ -n "$nki" ]; then
  echo "     file: $nki"
  strings -n 5 "$nki" 2>/dev/null | grep -iE 'megamagic|pluginguru|bells|winds|library|productname|<name>' | head -20 | sed 's/^/       str: /'
fi

echo
echo "=== 3) how does a WORKING made-tile lib's .nki look (Tropical Trap) — same probe for contrast ==="
TT="/mnt/btrfs_disk/Kontakt Libraries/Custom/Sonic Mechanics - Tropical Trap"
find "$TT" -iname '*.nki' 2>/dev/null | head -3 | sed 's/^/  /'
ttnki="$(find "$TT" -iname '*.nki' 2>/dev/null | head -1)"
if [ -n "$ttnki" ]; then
  echo "     names in TT .nki:"
  strings -n 5 "$ttnki" 2>/dev/null | grep -iE 'tropical|sonic|library|productname|<name>' | head -12 | sed 's/^/       str: /'
fi

echo
echo "READ-ONLY. If the working TT .nki carries a 'library name' that matches its image dir, but PlugInGuru's"
echo ".nki carries a DIFFERENT internal name than its folder, THAT internal name is the image-dir key we need."
