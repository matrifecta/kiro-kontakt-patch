#!/usr/bin/env bash
# fix-pluginguru-final.sh
# CORRECTION: Kontakt keys this tile off the LIBRARY FOLDER NAME (dotted), not the db alias. The db alias
# rename was a red herring and the dotted image dir we deleted was the correct one. This script:
#   1) recreates the DOTTED image dir 'PlugInGuru.MegaMagic.Bells.Winds.KONTAKT' from the MegaMagic cover
#   2) removes the clean-named dir we wrongly made
#   3) rolls back the db alias to the original dotted name (so label + key are consistent)
# Reversible. Kontakt must be closed for the db step.
set -u
MODE="${1:-dryrun}"
NIIMG="/mnt/workspace/VST Install/Kontakt Portable/UserData/NI Resources/image"
LIVE="/mnt/workspace/VST Install/Kontakt Portable/UserData/Kontakt 8/komplete.db3"
DOTTED="PlugInGuru.MegaMagic.Bells.Winds.KONTAKT"
CLEAN="PlugInGuru MegaMagic Bells Winds"
COVER="/mnt/btrfs_disk/Kontakt Libraries/Custom/PlugInGuru.MegaMagic.Bells.Winds.KONTAKT/MegaMagic Artwork.jpg"
DEST="$NIIMG/$DOTTED"

echo "will recreate dotted image dir: $DEST"
echo "will remove clean dir:          $NIIMG/$CLEAN"
echo "will restore db alias -> '$DOTTED'"
[ -f "$COVER" ] || { echo "ABORT: cover missing"; exit 1; }
command -v magick >/dev/null 2>&1 || { echo "ABORT: no imagemagick"; exit 1; }

if [ "$MODE" != apply ]; then echo "DRY-RUN. Re-run: bash $0 apply"; exit 0; fi

# 1) recreate dotted image dir
mkdir -p "$DEST"
gen() { magick "$3" -auto-orient -resize "$1^" -gravity center -extent "$1" -strip -define png:color-type=2 "$2" 2>/dev/null; }
gen "134x66"  "$DEST/MST_artwork.png" "$COVER"
gen "127x100" "$DEST/MST_plugin.png"  "$COVER"
gen "240x196" "$DEST/MST_logo.png"    "$COVER"
cat > "$DEST/$DOTTED.meta" <<EOF
<?xml version="1.0" encoding="UTF-8" standalone="no" ?>
<resource version="2.1544">
<name>$DOTTED</name>
<type>image</type>
</resource>
EOF
echo "created dotted dir: $(ls "$DEST" | tr '\n' ' ')"

# 2) remove the wrong clean dir
[ -d "$NIIMG/$CLEAN" ] && { rm -rf "$NIIMG/$CLEAN"; echo "removed clean dir"; }

# 3) roll back db alias (Kontakt closed)
if pgrep -x wineserver >/dev/null 2>&1 || pgrep -x reaper >/dev/null 2>&1; then
  echo "  *** close Reaper + wineserver -k before db step; skipping db rollback ***"
else
python3 - "$LIVE" "$CLEAN" "$DOTTED" <<'PY'
import sqlite3,sys,os,shutil,time,subprocess,tempfile
db,clean,dotted=sys.argv[1],sys.argv[2],sys.argv[3]
def k(a,b):
    a=(a or "").strip().casefold();b=(b or "").strip().casefold();return (a>b)-(a<b)
bk=f"{db}.pre_pgrevert_{time.strftime('%Y%m%d_%H%M%S')}"; shutil.copy2(db,bk); print("  db backup:",bk)
for s in ("-wal","-shm"):
    if os.path.exists(db+s): shutil.copy2(db+s,bk+s)
con=sqlite3.connect(db);con.create_collation("KOMPLETE",k);c=con.cursor()
try: c.execute("REINDEX"); con.commit()
except Exception as e: print("  REINDEX err:",e)
c.execute("UPDATE k_content_path SET alias=? WHERE alias=?",(dotted,clean)); con.commit()
print("  alias rows reverted:", c.rowcount)
print("  integrity:", c.execute("PRAGMA integrity_check").fetchone()[0])
con.close()
for s in ("-wal","-shm"):
    p=db+s
    if os.path.exists(p): os.remove(p)
PY
fi

echo
echo "ROLLBACK: rm -rf \"$DEST\"  (and db backup printed above if made)"
echo "NEXT: launch Reaper, load Kontakt, PlugInGuru should now show its tile."
