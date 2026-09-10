#!/usr/bin/env bash
# make-tile-hy2rogen.sh — build the missing tile for Hy2rogen - Tekno House Nights from its in-folder cover.
# Same recipe (image dir keyed by db alias; no .nicnt/db/rescan). Reversible.
set -u
MODE="${1:-dryrun}"
NIIMG="/mnt/workspace/VST Install/Kontakt Portable/UserData/NI Resources/image"
ALIAS="Hy2rogen - Tekno House Nights"
LIBDIR="/mnt/btrfs_disk/Kontakt Libraries/Custom/Hy2rogen - Tekno House Nights"
COVER="$LIBDIR/CS4068084-02A-BIG.jpg"
DEST="$NIIMG/$ALIAS"

echo "alias: $ALIAS"
echo "cover: $COVER"
echo "dest : $DEST"
[ -f "$COVER" ] || { echo "ABORT: cover missing"; exit 1; }
command -v magick >/dev/null 2>&1 || { echo "ABORT: no imagemagick"; exit 1; }
[ -e "$DEST" ] && { echo "NOTE: dest exists; rm -rf to redo"; }

if [ "$MODE" != apply ]; then echo "DRY-RUN. Re-run: bash $0 apply"; exit 0; fi
mkdir -p "$DEST"
gen() { magick "$3" -auto-orient -resize "$1^" -gravity center -extent "$1" -strip -define png:color-type=2 "$2" 2>/dev/null; }
gen "134x66"  "$DEST/MST_artwork.png" "$COVER"
gen "127x100" "$DEST/MST_plugin.png"  "$COVER"
gen "240x196" "$DEST/MST_logo.png"    "$COVER"
cat > "$DEST/$ALIAS.meta" <<EOF
<?xml version="1.0" encoding="UTF-8" standalone="no" ?>
<resource version="2.1544">
<name>$ALIAS</name>
<type>image</type>
</resource>
EOF
echo "created: $(ls "$DEST" | tr '\n' ' ')"
echo "ROLLBACK: rm -rf \"$DEST\""
