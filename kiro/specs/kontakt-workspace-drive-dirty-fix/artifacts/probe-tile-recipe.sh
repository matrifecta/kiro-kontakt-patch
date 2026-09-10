#!/usr/bin/env bash
# probe-tile-recipe.sh  (READ-ONLY)
# Before authoring tiles, learn the EXACT recipe from a known-good NKS tile:
#   - what files live in NI Resources/image/<Product>/ (MST_artwork/logo/plugin, OSO_logo, .meta)
#   - the content of the .meta (what it references)
#   - the MST_artwork.png dimensions/format (so our generated art matches)
# Also confirm how the db links: a rendering type-2 lib's alias vs the NI image dir name (must the image
# dir name == db alias, == .nicnt Product Name, or == folder?). Use two good refs on different products.

set -u
NIIMG="/mnt/workspace/VST Install/Kontakt Portable/UserData/NI Resources/image"

for prod in "Amati Viola" "Butch Vig Drums" "Electro Acoustic"; do
  echo "===== NI image dir: $prod"
  d="$NIIMG/$prod"
  if [ ! -d "$d" ]; then echo "  (missing)"; continue; fi
  ls -la "$d" | sed 's/^/  /'
  for m in "$d"/*.meta; do
    [ -f "$m" ] || continue
    echo "  --- .meta ($(basename "$m")):"
    sed 's/^/      /' "$m"
    echo
  done
  # image geometry/format of the artwork/plugin pngs (needs ImageMagick 'identify' or 'file')
  for png in "$d"/MST_artwork.png "$d"/MST_plugin.png "$d"/MST_logo.png; do
    [ -f "$png" ] || continue
    if command -v identify >/dev/null 2>&1; then
      echo "  img: $(identify -format '%f  %wx%h  %m  %[channels]\n' "$png" 2>/dev/null)"
    else
      echo "  img: $(basename "$png")  $(file -b "$png")"
    fi
  done
  echo
done

echo "===== how many NI image dirs total, and a sample of names ====="
ls -1 "$NIIMG" | wc -l | sed 's/^/  count: /'
ls -1 "$NIIMG" | head -8 | sed 's/^/  e.g. /'

echo
echo "===== do all these dir names correspond to a db alias OR a .nicnt Product Name? ====="
echo "  (checked earlier: Electro Acoustic .nicnt Name == 'Electro Acoustic' == image dir name; Amati Viola"
echo "   .nicnt Name == 'Amati Viola' == image dir. So image dir name == .nicnt Product <Name>.)"
echo
echo "READ-ONLY. Recipe = create NI Resources/image/<ProductName>/ with MST_artwork.png (+ .meta) matching"
echo "this geometry/format; and a .nicnt in the lib giving Product <Name>=<ProductName>. Then db row -> type 2."
