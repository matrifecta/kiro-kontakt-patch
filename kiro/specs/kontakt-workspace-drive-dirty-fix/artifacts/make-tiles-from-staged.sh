#!/usr/bin/env bash
#
# make-tiles-from-staged.sh   (build tiles for the 5 web-sourced libs from a staging dir)
#
# For the libs with no on-disk cover, download the official product cover to the staging dir below, named
# EXACTLY <db-alias>.<ext> (jpg/png/jpeg/webp). This script then scales each staged image to the 3 MST sizes
# into NI Resources/image/<db-alias>/ + writes the .meta — same PROVEN recipe (no .nicnt, no db, no rescan).
#
# STAGING DIR (put downloaded covers here, named by db alias):
#   ~/kontakt_tile_art/<db-alias>.<ext>
# db aliases needed (use EXACTLY these filenames, sans extension):
#   String Audio - Alchemist Cinematic Impacts
#   Audio Imperia - Sinfonia Drums
#   Epic SoundLab - The Forge
#   Keyscape - 13
#   Drumdrops - Vintage Funk Kit
#
# Usage: bash make-tiles-from-staged.sh          # dry-run: shows which staged covers were found
#        bash make-tiles-from-staged.sh apply
#
set -u
MODE="${1:-dryrun}"
NIIMG="/mnt/workspace/VST Install/Kontakt Portable/UserData/NI Resources/image"
STAGE="$HOME/kontakt_tile_art"

ALIASES=(
 "String Audio - Alchemist Cinematic Impacts"
 "Audio Imperia - Sinfonia Drums"
 "Epic SoundLab - The Forge"
 "Keyscape - 13"
 "Drumdrops - Vintage Funk Kit"
)

command -v magick >/dev/null 2>&1 || { echo "ABORT: no imagemagick"; exit 1; }
mkdir -p "$STAGE"
echo "staging dir: $STAGE"
echo "(put each official cover here as '<db-alias>.jpg' or .png, exact alias name)"
echo

find_staged() {  # $1 = alias -> first matching staged file
  local a="$1" f
  for ext in png jpg jpeg webp PNG JPG JPEG; do
    f="$STAGE/$a.$ext"; [ -f "$f" ] && { echo "$f"; return; }
  done
}

gen() { magick "$3" -auto-orient -resize "$1^" -gravity center -extent "$1" -strip -define png:color-type=2 "$2" 2>/dev/null; }

made=0 miss=0 skip=0
for alias in "${ALIASES[@]}"; do
  dest="$NIIMG/$alias"; src="$(find_staged "$alias")"
  echo "--- $alias"
  if [ -e "$dest" ]; then echo "    SKIP: image dir already exists"; skip=$((skip+1)); continue; fi
  if [ -z "$src" ]; then echo "    no staged cover in $STAGE (add '$alias.jpg')"; miss=$((miss+1)); continue; fi
  echo "    staged cover: $src"
  if [ "$MODE" != apply ]; then echo "    would build tile dir"; made=$((made+1)); continue; fi
  mkdir -p "$dest"
  gen "134x66"  "$dest/MST_artwork.png" "$src"
  gen "127x100" "$dest/MST_plugin.png"  "$src"
  gen "240x196" "$dest/MST_logo.png"    "$src"
  cat > "$dest/$alias.meta" <<EOF
<?xml version="1.0" encoding="UTF-8" standalone="no" ?>
<resource version="2.1544">
<name>$alias</name>
<type>image</type>
</resource>
EOF
  echo "    created: $(ls "$dest" | tr '\n' ' ')"
  made=$((made+1))
done

echo
echo "summary: made=$made missing_cover=$miss skip=$skip  (mode=$MODE)"
[ "$MODE" = apply ] && {
  echo "ROLLBACK:"; for alias in "${ALIASES[@]}"; do echo "  rm -rf \"$NIIMG/$alias\""; done
  echo "NEXT: launch Reaper, load Kontakt, verify the new tiles. DO NOT rescan."
} || echo "DRY-RUN. Add covers to $STAGE then: bash $0 apply"
