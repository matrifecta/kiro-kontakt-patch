#!/usr/bin/env bash
# probe-nki-name-vs-working.sh (READ-ONLY)
# Get the EXACT .nki internal library name for libs that WORK (Doru Malaia, Tropical Trap, EDM Energy) vs
# PlugInGuru (fails). The working ones got a tile from an image dir == their FOLDER name. So determine:
#  - does each working lib's .nki library-name equal its folder name? (then folder name IS the key and dots are
#    the only difference for PlugInGuru)
#  - what is PlugInGuru's exact .nki library-name bytes (the '{ <name> @' string), so we can match it exactly.
set -u
CB="/mnt/btrfs_disk/Kontakt Libraries/Custom"

nki_libname() {  # $1 = lib dir -> print the '{ <Name> @' internal library name from first .nki
  local dir="$1"
  local nki; nki="$(find "$dir" -type f -iname '*.nki' 2>/dev/null | head -1)"
  [ -z "$nki" ] && { echo "    (no .nki)"; return; }
  echo "    .nki: $nki"
  # the library name usually appears as '{ NAME @' near the how_library_tab marker
  strings -n 4 "$nki" 2>/dev/null | grep -E '\{ .+ @|how_library_tab|[A-Z]{4,}' | head -8 | sed 's/^/       str: /'
}

for lib in "Sonic Mechanics - Tropical Trap" "Sonic Mechanics - EDM Energy Drums" "Doru Malaia - Ethnic Super Drums Collection" "PlugInGuru.MegaMagic.Bells.Winds.KONTAKT"; do
  echo "===== $lib"
  echo "  folder name: $lib"
  nki_libname "$CB/$lib"
done
echo
echo "READ-ONLY. If the WORKING libs' .nki '{ name @' EQUALS their folder name, the key is the folder name and"
echo "PlugInGuru fails only due to dots. If the working libs' image dir (folder-name) differs from their .nki"
echo "name yet they render, the folder name is the key. Then PlugInGuru needs its FOLDER renamed dot-free AND"
echo "the db path updated — a bigger change. Decide from the exact strings."
