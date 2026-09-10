#!/usr/bin/env bash
#
# make-tiles-batch.sh   (creates NI Resources/image/<alias> dirs; fully reversible per-lib)
#
# PROVEN by make-tile-proof.sh: a browser tile renders from JUST NI Resources/image/<alias>/ with MST pngs +
# a plain-XML .meta — NO .nicnt, NO db change, NO rescan. (Sonic Mechanics - Tropical Trap now shows its cover.)
#
# This batches the remaining folder-icon Custom libs. For each: pick the best cover image found on disk, scale
# it to the 3 MST sizes into NI Resources/image/<db-alias>/, write <alias>.meta. Skips a lib if its image dir
# already exists (so re-runs are safe) or if no cover image is found (reported).
#
# alias  MUST equal the db alias (== browser name). cover = the vendor image inside the lib folder.
#
# Usage: bash make-tiles-batch.sh          # dry-run
#        bash make-tiles-batch.sh apply

set -u
MODE="${1:-dryrun}"
NIIMG="/mnt/workspace/VST Install/Kontakt Portable/UserData/NI Resources/image"
CB="/mnt/btrfs_disk/Kontakt Libraries/Custom"
CW="/mnt/wd_black/Kontakt Libraries/Custom"

# alias <TAB> cover-file. Covers chosen from earlier deep-nks-probe output.
# For libs with no obvious top-level cover, we point at the best in-folder image or leave AUTO (search).
MAP=$(cat <<'EOF'
Sonic Mechanics - Classic Guitar Licks	/mnt/btrfs_disk/Kontakt Libraries/Custom/Sonic Mechanics - Classic Guitar Licks/Sonic Mechanics Classic Guitar Licks.jpg
Sonic Mechanics - EDM Energy Drums	/mnt/btrfs_disk/Kontakt Libraries/Custom/Sonic Mechanics - EDM Energy Drums/Sonic Mechanics - EDM Energy Drums.jpg
Sonic Mechanics - Future Cinematic FX	/mnt/btrfs_disk/Kontakt Libraries/Custom/Sonic Mechanics - Future Cinematic FX/CFX-Cover.jpg
Doru Malaia - Ethnic Super Drums Collection	/mnt/btrfs_disk/Kontakt Libraries/Custom/Doru Malaia - Ethnic Super Drums Collection/wallpaper.png
PlugInGuru.MegaMagic.Bells.Winds.KONTAKT	/mnt/btrfs_disk/Kontakt Libraries/Custom/PlugInGuru.MegaMagic.Bells.Winds.KONTAKT/MegaMagic Artwork.jpg
String Audio - Alchemist Cinematic Impacts	AUTO
Audio Imperia - Sinfonia Drums	AUTO
Epic SoundLab - The Forge	AUTO
Keyscape - 13	AUTO
Drumdrops - Vintage Funk Kit	AUTO
EOF
)

# find a usable cover for AUTO: largest image anywhere in the lib folder (jpg/png/jpeg), skip tiny icons.
find_cover() {  # $1 = alias
  local alias="$1" base
  for base in "$CB/$alias" "$CW/$alias"; do
    [ -d "$base" ] || continue
    find "$base" -type f \( -iname '*.jpg' -o -iname '*.jpeg' -o -iname '*.png' \) -printf '%s\t%p\n' 2>/dev/null \
      | sort -rn | awk -F'\t' 'NR==1{print $2}'
    return
  done
}

gen() {  # $1 geom  $2 out  $3 cover
  magick "$3" -auto-orient -resize "$1^" -gravity center -extent "$1" -strip -define png:color-type=2 "$2" 2>/dev/null
}

echo "=== batch make tiles (image dir per db alias; no .nicnt, no db) ==="
command -v magick >/dev/null 2>&1 || { echo "ABORT: no imagemagick"; exit 1; }

made=0 skip=0 nocover=0
while IFS=$'\t' read -r alias cover; do
  [ -z "$alias" ] && continue
  dest="$NIIMG/$alias"
  if [ "$cover" = "AUTO" ]; then cover="$(find_cover "$alias")"; fi
  echo "--- $alias"
  if [ -e "$dest" ]; then echo "    SKIP: image dir already exists"; skip=$((skip+1)); continue; fi
  if [ -z "$cover" ] || [ ! -f "$cover" ]; then echo "    NO COVER FOUND -> cannot make a tile"; nocover=$((nocover+1)); continue; fi
  echo "    cover: $cover"
  if [ "$MODE" != apply ]; then echo "    would create: $dest/{MST_artwork,MST_plugin,MST_logo}.png + .meta"; made=$((made+1)); continue; fi
  mkdir -p "$dest"
  gen "134x66"  "$dest/MST_artwork.png" "$cover"
  gen "127x100" "$dest/MST_plugin.png"  "$cover"
  gen "240x196" "$dest/MST_logo.png"    "$cover"
  cat > "$dest/$alias.meta" <<EOF
<?xml version="1.0" encoding="UTF-8" standalone="no" ?>
<resource version="2.1544">
<name>$alias</name>
<type>image</type>
</resource>
EOF
  echo "    created: $(ls "$dest" | tr '\n' ' ')"
  made=$((made+1))
done <<< "$MAP"

echo
echo "summary: made=$made skip=$skip nocover=$nocover  (mode=$MODE)"
if [ "$MODE" = apply ]; then
  echo
  echo "ROLLBACK (removes only the dirs made here):"
  while IFS=$'\t' read -r alias cover; do
    [ -z "$alias" ] && continue
    echo "  rm -rf \"$NIIMG/$alias\""
  done <<< "$MAP"
  echo
  echo "NEXT: launch Reaper, load Kontakt. Tiles should appear for the libs that had a cover. Any 'NO COVER'"
  echo "lib stays a folder icon (no source art). DO NOT rescan."
else
  echo "DRY-RUN. Re-run: bash $0 apply"
fi
