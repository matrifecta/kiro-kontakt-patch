#!/usr/bin/env bash
#
# probe-blank-nicnt-vs-niimage.sh   (READ-ONLY)
#
# NEW insight: the Custom-type libs that RENDER (Electro Acoustic, Session Keys Electric R, Picked Acoustic,
# Electric Sunburst DLX) have NO loose image in-folder — only a .nicnt. So they are NKS libs; their tile comes
# from NI Resources/image/<ProductName> (resolved by the .nicnt Product <Name>), exactly like the 45 Player libs.
# The blank libs mostly have loose jpg/png but (per prior probe) no .nicnt, so Kontakt has no NKS tile for them.
#
# This script settles it per blank lib:
#   (1) is there a .nicnt anywhere in the lib folder?  If yes, extract its Product <Name>.
#   (2) does NI Resources/image/<that Name>  (and /<alias>) exist?  list its files.
# And for a couple of RENDER refs, show their .nicnt Product Name + that the NI image dir exists.
# This tells us, for each blank, whether the fix is "add NI Resources/image/<Name>" (NKS lib missing art dir)
# or "this lib has no NKS metadata at all" (never had a browser tile; nothing to restore).
#
# Usage: bash probe-blank-nicnt-vs-niimage.sh

set -u
NIIMG="/mnt/workspace/VST Install/Kontakt Portable/UserData/NI Resources/image"
CB="/mnt/btrfs_disk/Kontakt Libraries/Custom"
PB="/mnt/btrfs_disk/Kontakt Libraries/Player"
CW="/mnt/wd_black/Kontakt Libraries/Custom"
PW="/mnt/wd_black/Kontakt Libraries/Player"

nicnt_name() {  # $1 = lib dir -> prints Product <Name> from first .nicnt, else empty
  local dir="$1" n
  n="$(find "$dir" -maxdepth 3 -iname '*.nicnt' 2>/dev/null | head -1)"
  [ -z "$n" ] && return 0
  # <Name>...</Name> from the nicnt header strings
  strings -n 3 "$n" 2>/dev/null | grep -oiE '<Name>[^<]+</Name>' | head -1 | sed -E 's#</?Name>##g'
}

report() {  # $1 = tag  $2 = lib dir
  local tag="$1" dir="$2" nm
  echo "----- [$tag]"
  echo "    dir: $dir"
  if [ ! -d "$dir" ]; then echo "    (missing dir)"; return; fi
  local nicnt; nicnt="$(find "$dir" -maxdepth 3 -iname '*.nicnt' 2>/dev/null | head -1)"
  if [ -n "$nicnt" ]; then
    nm="$(nicnt_name "$dir")"
    echo "    .nicnt: YES  Product Name = '${nm}'"
    if [ -n "$nm" ] && [ -d "$NIIMG/$nm" ]; then
      echo "    NI image dir EXISTS: $NIIMG/$nm"
      ls -la "$NIIMG/$nm" 2>/dev/null | sed 's/^/        /' | head -8
    elif [ -n "$nm" ]; then
      echo "    NI image dir MISSING: $NIIMG/$nm   <-- add art dir to get a tile"
    fi
  else
    echo "    .nicnt: NO  (no NKS metadata -> Kontakt has no browser tile for this lib; loose jpg/png are not used)"
  fi
}

echo "=========== RENDER refs (should have .nicnt + existing NI image dir) ==========="
report "Electro Acoustic"        "$PB/Electro Acoustic"
report "Session Keys Electric R" "$PB/Session Keys Electric R"
report "Picked Acoustic"         "$PB/Session Guitarist - Picked Acoustic Library"

echo
echo "=========== BLANK libs ==========="
report "Doru Malaia"        "$CB/Doru Malaia - Ethnic Super Drums Collection"
report "PlugInGuru MegaMagic" "$CB/PlugInGuru.MegaMagic.Bells.Winds.KONTAKT"
report "SM Classic Guitar Licks" "$CB/Sonic Mechanics - Classic Guitar Licks"
report "SM EDM Energy Drums" "$CB/Sonic Mechanics - EDM Energy Drums"
report "SM Future Cinematic FX" "$CB/Sonic Mechanics - Future Cinematic FX"
report "SM Tropical Trap"    "$CB/Sonic Mechanics - Tropical Trap"
report "String Audio Alchemist" "$CB/String Audio - Alchemist Cinematic Impacts"
report "Audio Imperia Sinfonia" "$CW/Audio Imperia - Sinfonia Drums"
report "Epic SoundLab Forge" "$CB/Epic SoundLab - The Forge"
report "Keyscape 13"         "$CB/Keyscape - 13"
report "Drumdrops Vintage Funk" "$CB/Drumdrops - Vintage Funk Kit"
report "GetGood Modern&Massive" "$PW/GetGood Drums - Modern and Massive Pack"

echo
echo "=========== is there an NI image dir that LOOKS like each blank (name variants)? ==========="
for q in "GGD" "Modern" "Sinfonia" "Forge" "Keyscape" "Alchemist" "MegaMagic" "Doru" "Drumdrops" "Sonic"; do
  hits="$(ls -d "$NIIMG/"*"$q"* 2>/dev/null)"
  [ -n "$hits" ] && echo "  '$q' -> $hits"
done

echo
echo "READ-ONLY. If a blank lib has .nicnt + MISSING NI image dir -> fix = create that image dir (from the"
echo "lib's own art or a copy). If a blank lib has NO .nicnt -> it never had an NKS tile; nothing to restore."
