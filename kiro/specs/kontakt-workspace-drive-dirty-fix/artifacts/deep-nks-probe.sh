#!/usr/bin/env bash
# deep-nks-probe.sh  (READ-ONLY)
# My earlier probe only searched maxdepth 3 for *.nicnt. Do an UNFILTERED, full-depth search inside each of the
# 11 folder-icon libs for ANY NKS metadata (.nicnt, .nkx with product hints, .nfo, .db, MST_*.png, a resources/
# pictures folder), AND check whether NI Resources/image has a folder for the lib's name or a close variant.
# If a lib has NKS metadata OR a matching NI image dir, it CAN render a tile — contradicting "never had one".

set -u
NIIMG="/mnt/workspace/VST Install/Kontakt Portable/UserData/NI Resources/image"
declare -A DIRS=(
 ["Doru Malaia"]="/mnt/btrfs_disk/Kontakt Libraries/Custom/Doru Malaia - Ethnic Super Drums Collection"
 ["PlugInGuru MegaMagic"]="/mnt/btrfs_disk/Kontakt Libraries/Custom/PlugInGuru.MegaMagic.Bells.Winds.KONTAKT"
 ["SM Classic Guitar"]="/mnt/btrfs_disk/Kontakt Libraries/Custom/Sonic Mechanics - Classic Guitar Licks"
 ["SM EDM Energy"]="/mnt/btrfs_disk/Kontakt Libraries/Custom/Sonic Mechanics - EDM Energy Drums"
 ["SM Future Cinematic"]="/mnt/btrfs_disk/Kontakt Libraries/Custom/Sonic Mechanics - Future Cinematic FX"
 ["SM Tropical Trap"]="/mnt/btrfs_disk/Kontakt Libraries/Custom/Sonic Mechanics - Tropical Trap"
 ["String Audio Alchemist"]="/mnt/btrfs_disk/Kontakt Libraries/Custom/String Audio - Alchemist Cinematic Impacts"
 ["Audio Imperia Sinfonia"]="/mnt/wd_black/Kontakt Libraries/Custom/Audio Imperia - Sinfonia Drums"
 ["Epic SoundLab Forge"]="/mnt/btrfs_disk/Kontakt Libraries/Custom/Epic SoundLab - The Forge"
 ["Keyscape 13"]="/mnt/btrfs_disk/Kontakt Libraries/Custom/Keyscape - 13"
 ["Drumdrops Funk"]="/mnt/btrfs_disk/Kontakt Libraries/Custom/Drumdrops - Vintage Funk Kit"
)

for name in "${!DIRS[@]}"; do
  dir="${DIRS[$name]}"
  echo "===== [$name]"
  echo "  dir: $dir"
  if [ ! -d "$dir" ]; then echo "  (missing)"; continue; fi
  echo "  -- ALL .nicnt/.nfo/.nkx/.db/.meta at ANY depth:"
  find "$dir" -type f \( -iname '*.nicnt' -o -iname '*.nfo' -o -iname '*.nkx' -o -iname '*.db' -o -iname '*.meta' \) 2>/dev/null \
    | sed 's/^/      /' | head -20
  echo "  -- any MST_*.png / resources / pictures / snapshots dir:"
  find "$dir" -type d \( -iname 'resources' -o -iname 'pictures' -o -iname 'snapshots' -o -iname 'image' \) 2>/dev/null \
    | sed 's/^/      dir: /' | head -10
  find "$dir" -type f -iname 'MST_*.png' 2>/dev/null | sed 's/^/      mst: /' | head -6
  echo "  -- top-level listing:"
  ls -la "$dir" 2>/dev/null | sed 's/^/      /' | head -20
done

echo
echo "===== NI Resources/image folders that fuzzy-match any of the 11 ====="
for q in "Doru" "Malaia" "Ethnic" "MegaMagic" "PlugInGuru" "Sonic Mechanics" "Classic Guitar" "EDM Energy" \
         "Cinematic FX" "Tropical" "Alchemist" "String Audio" "Sinfonia" "Audio Imperia" "Forge" "Epic Sound" \
         "Keyscape" "Drumdrops" "Vintage Funk"; do
  hits="$(ls -d "$NIIMG/"*"$q"* 2>/dev/null)"
  [ -n "$hits" ] && echo "  '$q' -> $hits"
done
echo
echo "READ-ONLY. Any NKS metadata OR matching NI image dir here means the lib CAN show a tile."
