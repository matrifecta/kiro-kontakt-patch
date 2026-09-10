#!/usr/bin/env bash
# probe-pg-png-detail.sh (READ-ONLY)
# No name appears in any text cache -> tile key isn't a stored string. DB/folder/imagedir all match a working
# lib now. Last concrete variable: the PNG itself. Deep-compare the working Tropical Trap MST_artwork.png vs
# PlugInGuru's at format level (bit depth, colortype, interlace, iCCP/gamma chunks) — Kontakt may reject a png
# with an embedded color profile or wrong bit depth. Also verify PlugInGuru's png actually opens.
set -u
NIIMG="/mnt/workspace/VST Install/Kontakt Portable/UserData/NI Resources/image"
WORK="$NIIMG/Sonic Mechanics - Tropical Trap/MST_artwork.png"
PG="$NIIMG/PlugInGuru MegaMagic Bells Winds/MST_artwork.png"
NI="$NIIMG/Electro Acoustic/MST_artwork.png"

detail() {
  local f="$1"
  echo "  file: $f"
  [ -f "$f" ] || { echo "    MISSING"; return; }
  identify -verbose "$f" 2>/dev/null | grep -iE 'Geometry|Depth|Colorspace|Type:|Interlace|png:|Gamma|Profile|Channel depth|filesize|Alpha' | sed 's/^/    /' | head -30
}
echo "=== WORKING Tropical Trap MST_artwork.png ==="; detail "$WORK"
echo "=== NI Electro Acoustic MST_artwork.png (native) ==="; detail "$NI"
echo "=== PlugInGuru MST_artwork.png ==="; detail "$PG"
echo
echo "=== raw PNG chunk types (look for iCCP/gAMA/sRGB differences) ==="
for f in "$WORK" "$PG"; do
  echo "  $f:"
  python3 - "$f" <<'PY' 2>/dev/null | sed 's/^/     /'
import sys,struct
f=open(sys.argv[1],'rb'); d=f.read(); f.close()
i=8; chunks=[]
while i<len(d):
    ln=struct.unpack('>I',d[i:i+4])[0]; typ=d[i+4:i+8].decode('latin1'); chunks.append(typ); i+=12+ln
    if typ=='IEND': break
print("chunks:", " ".join(chunks))
PY
done
echo
echo "READ-ONLY. If PlugInGuru's png carries an iCCP/gAMA chunk or different bit depth that the working ones"
echo "lack, re-encode it stripped/flat to match. Our -strip should have removed profiles; verify."
