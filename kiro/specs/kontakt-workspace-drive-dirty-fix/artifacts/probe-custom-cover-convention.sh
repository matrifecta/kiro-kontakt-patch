#!/usr/bin/env bash
#
# probe-custom-cover-convention.sh   (READ-ONLY)
#
# FINDING so far: the db does NOT drive Custom-lib tiles (no image table, no picture column; render vs blank
# rows are byte-identical in every column). So Kontakt resolves a Custom lib's browser tile from a cover
# IMAGE FILE inside the library folder, by a NAME/LOCATION convention. This script finds that convention by
# listing EVERY image file (name + relative location + size) for:
#   - Custom libs that RENDER in the browser (reference): Electro Acoustic, Electric Sunburst Deluxe,
#     Session Keys Electric R, Picked Acoustic  (all type-3, tiles visible in the screenshot)
#   - Custom libs that are BLANK: Doru Malaia, PlugInGuru MegaMagic, all 4 Sonic Mechanics, String Audio,
#     Audio Imperia Sinfonia, Epic SoundLab, Keyscape, Drumdrops
# Compare the RENDER set's image filename/location to the BLANK set: the shared name/path in RENDER that the
# BLANK libs lack (or have under a different name) is the convention Kontakt reads.
#
# Usage: bash probe-custom-cover-convention.sh

set -u
CUSTOM_BTRFS="/mnt/btrfs_disk/Kontakt Libraries/Custom"
PLAYER_BTRFS="/mnt/btrfs_disk/Kontakt Libraries/Player"
CUSTOM_WDB="/mnt/wd_black/Kontakt Libraries/Custom"

list_imgs() {  # $1 = full lib dir path, $2 = tag
  local dir="$1" tag="$2"
  echo "----- [$tag] $dir"
  if [ ! -d "$dir" ]; then echo "    (missing)"; return; fi
  # every image-ish file, relative path + size, sorted
  find "$dir" -maxdepth 4 -type f \
      \( -iname '*.png' -o -iname '*.jpg' -o -iname '*.jpeg' -o -iname '*.bmp' -o -iname '*.gif' \) 2>/dev/null \
    | while read -r f; do
        rel="${f#$dir/}"
        sz=$(stat -c '%s' "$f" 2>/dev/null)
        printf '    %8s  %s\n' "$sz" "$rel"
      done | sort -k2
  # also note top-level non-image files that might be the picture ref (xml/txt/nki/nicnt)
  find "$dir" -maxdepth 1 -type f \( -iname '*.xml' -o -iname '*.txt' -o -iname '*.nicnt' -o -iname '*.db' -o -iname '*.meta' \) 2>/dev/null \
    | sed "s#$dir/#      meta: #"
}

echo "=================== RENDER reference (tiles VISIBLE) ==================="
list_imgs "$PLAYER_BTRFS/Electro Acoustic" "RENDER Electro Acoustic"
list_imgs "$PLAYER_BTRFS/Session Guitarist - Electric Sunburst Deluxe" "RENDER Electric Sunburst DLX"
list_imgs "$PLAYER_BTRFS/Session Keys Electric R" "RENDER Session Keys Electric R"
list_imgs "$PLAYER_BTRFS/Session Guitarist - Picked Acoustic Library" "RENDER Picked Acoustic"

echo
echo "=================== BLANK (no tile) ==================="
list_imgs "$CUSTOM_BTRFS/Doru Malaia - Ethnic Super Drums Collection" "BLANK Doru Malaia"
list_imgs "$CUSTOM_BTRFS/PlugInGuru.MegaMagic.Bells.Winds.KONTAKT" "BLANK PlugInGuru MegaMagic"
list_imgs "$CUSTOM_BTRFS/Sonic Mechanics - Classic Guitar Licks" "BLANK SM Classic Guitar Licks"
list_imgs "$CUSTOM_BTRFS/Sonic Mechanics - EDM Energy Drums" "BLANK SM EDM Energy Drums"
list_imgs "$CUSTOM_BTRFS/Sonic Mechanics - Future Cinematic FX" "BLANK SM Future Cinematic FX"
list_imgs "$CUSTOM_BTRFS/Sonic Mechanics - Tropical Trap" "BLANK SM Tropical Trap"
list_imgs "$CUSTOM_BTRFS/String Audio - Alchemist Cinematic Impacts" "BLANK String Audio Alchemist"
list_imgs "$CUSTOM_WDB/Audio Imperia - Sinfonia Drums" "BLANK Audio Imperia Sinfonia"
list_imgs "$CUSTOM_BTRFS/Epic SoundLab - The Forge" "BLANK Epic SoundLab Forge"
list_imgs "$CUSTOM_BTRFS/Keyscape - 13" "BLANK Keyscape 13"
list_imgs "$CUSTOM_BTRFS/Drumdrops - Vintage Funk Kit" "BLANK Drumdrops Vintage Funk"

echo
echo "READ-ONLY. Look for the filename/location the RENDER libs share (e.g. a top-level cover of a certain"
echo "name, or a resources/pictures/<file>) that the BLANK libs are missing or have under a different name."
echo "That shared convention is what Kontakt uses for the Custom-lib browser tile."
