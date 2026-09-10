#!/usr/bin/env bash
# fix-pluginguru-nkiname.sh
# FOUND: PlugInGuru's .nki internal library name = 'Mega Magic Bells/Winds' (display 'MEGAMAGIC BELLS/WINDS').
# The tile key is this NKS library name, NOT the folder or db alias. The '/' can't be a literal dir name, so
# NI likely maps it. Create BOTH plausible image-dir spellings so one matches; remove the loser after we see
# which renders:
#   A) 'Mega Magic Bells_Winds'   (slash -> underscore; matches the vendor PDF 'MegaMagic Bells_Winds K5 READ ME')
#   B) 'Mega Magic Bells' / 'Winds'  (slash -> real subdir)  [nested]
# Also keep the dotted folder-name dir already present (harmless). Reversible.
set -u
MODE="${1:-dryrun}"
NIIMG="/mnt/workspace/VST Install/Kontakt Portable/UserData/NI Resources/image"
COVER="/mnt/btrfs_disk/Kontakt Libraries/Custom/PlugInGuru.MegaMagic.Bells.Winds.KONTAKT/MegaMagic Artwork.jpg"

[ -f "$COVER" ] || { echo "ABORT: cover missing"; exit 1; }
command -v magick >/dev/null 2>&1 || { echo "ABORT: no imagemagick"; exit 1; }

mk() {  # $1 = image-dir path, $2 = meta <name> value
  local dest="$1" nm="$2"
  echo "  make: $dest   (meta name='$nm')"
  [ "$MODE" != apply ] && return
  mkdir -p "$dest"
  magick "$COVER" -auto-orient -resize "134x66^"  -gravity center -extent "134x66"  -strip -define png:color-type=2 "$dest/MST_artwork.png" 2>/dev/null
  magick "$COVER" -auto-orient -resize "127x100^" -gravity center -extent "127x100" -strip -define png:color-type=2 "$dest/MST_plugin.png" 2>/dev/null
  magick "$COVER" -auto-orient -resize "240x196^" -gravity center -extent "240x196" -strip -define png:color-type=2 "$dest/MST_logo.png" 2>/dev/null
  printf '<?xml version="1.0" encoding="UTF-8" standalone="no" ?>\n<resource version="2.1544">\n<name>%s</name>\n<type>image</type>\n</resource>\n' "$nm" > "$dest/$(basename "$dest").meta"
}

echo "=== candidate image dirs for PlugInGuru (nki name 'Mega Magic Bells/Winds') ==="
# A) underscore form
mk "$NIIMG/Mega Magic Bells_Winds" "Mega Magic Bells_Winds"
# B) nested slash form: dir 'Mega Magic Bells' with subdir 'Winds' holding the assets + meta named 'Winds'
mk "$NIIMG/Mega Magic Bells/Winds" "Winds"
# C) also try the exact display-ish 'MEGAMAGIC BELLS_WINDS' and 'MegaMagic Bells_Winds'
mk "$NIIMG/MegaMagic Bells_Winds" "MegaMagic Bells_Winds"

echo
if [ "$MODE" != apply ]; then echo "DRY-RUN. Re-run: bash $0 apply"; exit 0; fi
echo "created candidates. ROLLBACK (after we see which works, delete the rest):"
echo "  rm -rf \"$NIIMG/Mega Magic Bells_Winds\" \"$NIIMG/Mega Magic Bells\" \"$NIIMG/MegaMagic Bells_Winds\""
echo
echo "NEXT: launch Reaper, load Kontakt. If PlugInGuru now shows a tile, note WHICH — then we keep only that"
echo "dir and delete the others. If none work, the nki name may need exact case/spacing; report back."
