#!/usr/bin/env bash
# compare-working-vs-blank-tiledir.sh (READ-ONLY)
# Tropical Trap (type3, image dir we made) RENDERS. PlugInGuru (type3, image dir we made) does NOT.
# GetGood (type2, pre-existing GGD image dir) does NOT. Compare the actual image-dir contents/geometry to
# find the difference. Also list a native working type-3 tile (Electro Acoustic is type3 & renders) for ref.
set -u
NIIMG="/mnt/workspace/VST Install/Kontakt Portable/UserData/NI Resources/image"

show() {
  echo "===== $1"
  local d="$NIIMG/$1"
  if [ ! -d "$d" ]; then echo "  (MISSING dir)"; return; fi
  ls -la "$d" | sed 's/^/  /'
  for f in "$d"/*.png; do
    [ -f "$f" ] || continue
    echo "    $(basename "$f"): $(identify -format '%wx%h %m %[channels]' "$f" 2>/dev/null)"
  done
  for m in "$d"/*.meta; do [ -f "$m" ] && { echo "  --- meta:"; sed 's/^/     /' "$m"; }; done
}

echo "### WORKING (renders):"
show "Sonic Mechanics - Tropical Trap"
show "Electro Acoustic"           # native type-3 that renders (has only .meta+MST in dir? check)
echo
echo "### NOT rendering:"
show "PlugInGuru.MegaMagic.Bells.Winds.KONTAKT"
show "GGD Modern and Massive"
echo
echo "READ-ONLY. Compare file set / png geometry / meta between the working Tropical Trap dir and the blank"
echo "PlugInGuru + GGD dirs. Any difference (missing file, different png mode, meta name) is the cause."
