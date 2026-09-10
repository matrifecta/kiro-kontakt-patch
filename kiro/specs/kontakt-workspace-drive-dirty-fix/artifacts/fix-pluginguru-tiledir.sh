#!/usr/bin/env bash
# fix-pluginguru-tiledir.sh — after fix-pluginguru-dots.py renames the db alias to the clean name, build the
# matching dot-free image dir from the PlugInGuru cover and remove the old dotted image dir. Reversible.
set -u
MODE="${1:-dryrun}"
NIIMG="/mnt/workspace/VST Install/Kontakt Portable/UserData/NI Resources/image"
NEW="PlugInGuru MegaMagic Bells Winds"
OLD_DIR="$NIIMG/PlugInGuru.MegaMagic.Bells.Winds.KONTAKT"
DEST="$NIIMG/$NEW"
COVER="/mnt/btrfs_disk/Kontakt Libraries/Custom/PlugInGuru.MegaMagic.Bells.Winds.KONTAKT/MegaMagic Artwork.jpg"
echo "cover: $COVER"
echo "new tile dir: $DEST"
echo "old dotted dir to remove: $OLD_DIR"
[ -f "$COVER" ] || { echo "ABORT: cover missing"; exit 1; }
command -v magick >/dev/null 2>&1 || { echo "ABORT: no imagemagick"; exit 1; }
if [ "$MODE" != apply ]; then echo "DRY-RUN. Re-run: bash $0 apply"; exit 0; fi
mkdir -p "$DEST"
gen() { magick "$3" -auto-orient -resize "$1^" -gravity center -extent "$1" -strip -define png:color-type=2 "$2" 2>/dev/null; }
gen "134x66"  "$DEST/MST_artwork.png" "$COVER"
gen "127x100" "$DEST/MST_plugin.png"  "$COVER"
gen "240x196" "$DEST/MST_logo.png"    "$COVER"
cat > "$DEST/$NEW.meta" <<EOF
<?xml version="1.0" encoding="UTF-8" standalone="no" ?>
<resource version="2.1544">
<name>$NEW</name>
<type>image</type>
</resource>
EOF
echo "created: $(ls "$DEST" | tr '\n' ' ')"
[ -d "$OLD_DIR" ] && { rm -rf "$OLD_DIR"; echo "removed old dotted dir"; }
echo "ROLLBACK: rm -rf \"$DEST\""
