#!/usr/bin/env bash
#
# make-tile-proof.sh   (writes ONE new NI Resources/image/<name> dir; fully reversible)
#
# Recipe learned from probe-tile-recipe.sh: a browser tile = a folder
#   NI Resources/image/<ProductName>/  containing
#     MST_artwork.png  134x66     (browser tile thumbnail)
#     MST_plugin.png   ~127x100
#     MST_logo.png     240x196
#     OSO_logo.png     (optional)
#     <ProductName>.meta   plain XML: <resource version="2.x"><name>ProductName</name><type>image</type></resource>
# and the dir name == the name Kontakt shows in the browser (== db alias for these Custom libs).
#
# PROOF (simplest path first): create the image dir keyed by the DB ALIAS, generate the 3 MST pngs from the
# library's own cover art, write the .meta. DO NOT create a .nicnt and DO NOT touch the db. If Kontakt then
# shows the tile, the simple path works for all libs. If not, we add the .nicnt/db step next.
#
# Target for the proof: Sonic Mechanics - Tropical Trap (has a clean TT-Cover.jpg).
# Everything created is under a single new dir we can delete to undo.
#
# Usage: bash make-tile-proof.sh          # dry-run (shows what it would make)
#        bash make-tile-proof.sh apply

set -u
MODE="${1:-dryrun}"
NIIMG="/mnt/workspace/VST Install/Kontakt Portable/UserData/NI Resources/image"

# --- the proof lib ---
ALIAS="Sonic Mechanics - Tropical Trap"                       # == db alias == what browser shows
COVER="/mnt/btrfs_disk/Kontakt Libraries/Custom/Sonic Mechanics - Tropical Trap/TT-Cover.jpg"
DEST="$NIIMG/$ALIAS"

echo "=== make tile (proof, no .nicnt, no db change) ==="
echo "  alias/dir : $ALIAS"
echo "  cover src : $COVER"
echo "  dest dir  : $DEST"

[ -f "$COVER" ] || { echo "  ABORT: cover not found"; exit 1; }
command -v magick >/dev/null 2>&1 || { echo "  ABORT: imagemagick 'magick' not found"; exit 1; }

if [ -e "$DEST" ]; then
  echo "  NOTE: dest already exists — will not overwrite in proof. Remove it first to redo:"
  echo "        rm -rf \"$DEST\""
fi

if [ "$MODE" != apply ]; then
  echo
  echo "DRY-RUN. Would create:"
  echo "  $DEST/MST_artwork.png  (134x66, from cover)"
  echo "  $DEST/MST_plugin.png   (127x100, from cover)"
  echo "  $DEST/MST_logo.png     (240x196, from cover)"
  echo "  $DEST/${ALIAS}.meta"
  echo "Re-run: bash $0 apply"
  exit 0
fi

mkdir -p "$DEST"

# generate the three MST pngs. Fill-to-cover (crop) so aspect matches the target box like NI art does.
gen() {  # $1 = WxH  $2 = outfile  $3 = 'srgba' for alpha
  local geom="$1" out="$2"
  magick "$COVER" -auto-orient -resize "${geom}^" -gravity center -extent "$geom" \
     -strip -define png:color-type=2 "$out" 2>/dev/null
  echo "    wrote $out  ($(identify -format '%wx%h %m' "$out" 2>/dev/null))"
}
echo "  generating MST pngs from cover..."
gen "134x66"  "$DEST/MST_artwork.png"
gen "127x100" "$DEST/MST_plugin.png"
gen "240x196" "$DEST/MST_logo.png"

# .meta (plain XML like the working refs)
cat > "$DEST/$ALIAS.meta" <<EOF
<?xml version="1.0" encoding="UTF-8" standalone="no" ?>
<resource version="2.1544">
<name>$ALIAS</name>
<type>image</type>
</resource>
EOF
echo "    wrote $DEST/$ALIAS.meta"

echo
echo "created:"
ls -la "$DEST" | sed 's/^/    /'
echo
echo "ROLLBACK: rm -rf \"$DEST\""
echo
echo "NEXT: launch Reaper (QT_QPA_PLATFORM=xcb reaper), load Kontakt, look at the 'Sonic Mechanics - Tropical"
echo "Trap' entry in the browser. If it now shows the cover tile -> the simple path WORKS (no .nicnt/db needed)"
echo "and we batch all 11 from their covers. If STILL a folder icon -> report back; we'll add the .nicnt + db"
echo "content_type step. DO NOT rescan either way."
