#!/usr/bin/env bash
#
# make-tiles-web.sh  (build tiles for the 5 web-sourced libs from the user's Slike folder)
#
# Source images (user-provided) -> db alias mapping. 4 files already match their alias; Keyscape differs
# (file 'Spectrasonics Keyscape.png' -> alias 'Keyscape - 13'). Same PROVEN recipe: scale each to the 3 MST
# sizes into NI Resources/image/<alias>/ + plain-XML .meta. No .nicnt, no db change, no rescan. Reversible.
#
# Usage: bash make-tiles-web.sh          # dry-run
#        bash make-tiles-web.sh apply
set -u
MODE="${1:-dryrun}"
NIIMG="/mnt/workspace/VST Install/Kontakt Portable/UserData/NI Resources/image"
SRC="/home/phnx/Slike/Missing Kontakt Lib Browser Instrument Entry Tiles Artwork"

# "source-file-basename<TAB>db-alias"
MAP=$(cat <<'EOF'
String Audio - Alchemist Cinematic Impacts.png	String Audio - Alchemist Cinematic Impacts
Audio Imperia - Sinfonia Drums.png	Audio Imperia - Sinfonia Drums
Epic SoundLab - The Forge.png	Epic SoundLab - The Forge
Spectrasonics Keyscape.png	Keyscape - 13
Drumdrops - Vintage Funk Kit.png	Drumdrops - Vintage Funk Kit
EOF
)

command -v magick >/dev/null 2>&1 || { echo "ABORT: no imagemagick"; exit 1; }
gen() { magick "$3" -auto-orient -resize "$1^" -gravity center -extent "$1" -strip -define png:color-type=2 "$2" 2>/dev/null; }

echo "=== make web-sourced tiles (no .nicnt, no db, no rescan) ==="
made=0 miss=0 skip=0
while IFS=$'\t' read -r fname alias; do
  [ -z "$fname" ] && continue
  src="$SRC/$fname"; dest="$NIIMG/$alias"
  echo "--- $alias"
  echo "    src: $src"
  if [ ! -f "$src" ]; then echo "    MISSING source"; miss=$((miss+1)); continue; fi
  if [ -e "$dest" ]; then echo "    SKIP: image dir already exists (remove to redo)"; skip=$((skip+1)); continue; fi
  if [ "$MODE" != apply ]; then echo "    would create: $dest/{MST_artwork,MST_plugin,MST_logo}.png + .meta"; made=$((made+1)); continue; fi
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
done <<< "$MAP"

echo
echo "summary: made=$made missing=$miss skip=$skip  (mode=$MODE)"
if [ "$MODE" = apply ]; then
  echo "ROLLBACK:"
  while IFS=$'\t' read -r fname alias; do [ -z "$fname" ] && continue; echo "  rm -rf \"$NIIMG/$alias\""; done <<< "$MAP"
  echo "NEXT: launch Reaper, load Kontakt, verify these 5 tiles. DO NOT rescan."
else
  echo "DRY-RUN. Re-run: bash $0 apply"
fi
