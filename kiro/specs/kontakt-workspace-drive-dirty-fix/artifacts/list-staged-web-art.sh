#!/usr/bin/env bash
# list-staged-web-art.sh (READ-ONLY) — show the images the user dropped for the 5 missing tiles, with
# dimensions/format so we can match each file to the correct db alias before generating tiles.
set -u
SRC="/home/phnx/Slike/Missing Kontakt Lib Browser Instrument Entry Tiles Artwork"
echo "listing: $SRC"
if [ ! -d "$SRC" ]; then echo "  (dir missing)"; exit 1; fi
find "$SRC" -maxdepth 2 -type f \( -iname '*.jpg' -o -iname '*.jpeg' -o -iname '*.png' -o -iname '*.webp' -o -iname '*.bmp' -o -iname '*.gif' \) 2>/dev/null \
  | while read -r f; do
      if command -v identify >/dev/null 2>&1; then
        printf '  %s  |  %s\n' "$(identify -format '%wx%h %m' "$f" 2>/dev/null)" "$f"
      else
        printf '  %s  |  %s\n' "$(file -b "$f")" "$f"
      fi
    done
echo
echo "READ-ONLY. Match each file to one of the 5 aliases:"
echo "  String Audio - Alchemist Cinematic Impacts"
echo "  Audio Imperia - Sinfonia Drums"
echo "  Epic SoundLab - The Forge"
echo "  Keyscape - 13"
echo "  Drumdrops - Vintage Funk Kit"
