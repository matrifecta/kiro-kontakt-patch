#!/usr/bin/env bash
# rename-pluginguru-folder.sh
# CONCLUSION: working Custom tiles use an image dir == the library FOLDER name. PlugInGuru is the only one
# whose folder name has DOTS, and it's the only failure. So the dots in the folder name break the tile lookup.
# FIX: rename the library folder to a dot-free name, update the db path, and create the matching image dir.
#
# old folder: /mnt/btrfs_disk/Kontakt Libraries/Custom/PlugInGuru.MegaMagic.Bells.Winds.KONTAKT
# new folder: /mnt/btrfs_disk/Kontakt Libraries/Custom/PlugInGuru MegaMagic Bells Winds
# db path Z:\mnt\btrfs_disk\Kontakt Libraries\Custom\PlugInGuru.MegaMagic.Bells.Winds.KONTAKT -> new
# db alias -> 'PlugInGuru MegaMagic Bells Winds' (matches new folder)
# image dir NI Resources/image/'PlugInGuru MegaMagic Bells Winds' (dot-free, == new folder name)
#
# All reversible. Kontakt/Reaper MUST be closed. Backs up db first.
#
# Usage: bash rename-pluginguru-folder.sh          # dry-run
#        bash rename-pluginguru-folder.sh apply
set -u
MODE="${1:-dryrun}"
NIIMG="/mnt/workspace/VST Install/Kontakt Portable/UserData/NI Resources/image"
LIVE="/mnt/workspace/VST Install/Kontakt Portable/UserData/Kontakt 8/komplete.db3"
BASECUST="/mnt/btrfs_disk/Kontakt Libraries/Custom"
OLDNAME="PlugInGuru.MegaMagic.Bells.Winds.KONTAKT"
NEWNAME="PlugInGuru MegaMagic Bells Winds"
OLDDIR="$BASECUST/$OLDNAME"
NEWDIR="$BASECUST/$NEWNAME"
OLDPATH_WIN='Z:\mnt\btrfs_disk\Kontakt Libraries\Custom\PlugInGuru.MegaMagic.Bells.Winds.KONTAKT'
NEWPATH_WIN='Z:\mnt\btrfs_disk\Kontakt Libraries\Custom\PlugInGuru MegaMagic Bells Winds'
COVER_REL="MegaMagic Artwork.jpg"

echo "=== rename PlugInGuru folder dot-free + update db + image dir ==="
echo "  old folder: $OLDDIR"
echo "  new folder: $NEWDIR"
echo "  db path: '$OLDPATH_WIN' -> '$NEWPATH_WIN'"
echo "  new image dir: $NIIMG/$NEWNAME"

[ -d "$OLDDIR" ] || { echo "  NOTE: old folder not present (already renamed?)"; }
command -v magick >/dev/null 2>&1 || { echo "ABORT: no imagemagick"; exit 1; }

if pgrep -x wineserver >/dev/null 2>&1 || pgrep -x reaper >/dev/null 2>&1; then
  echo "  *** close Reaper + wineserver -k first ***"
  [ "$MODE" = apply ] && { echo "ABORT"; exit 1; }
fi

if [ "$MODE" != apply ]; then echo; echo "DRY-RUN. Re-run: bash $0 apply"; exit 0; fi

# 1) rename the folder on disk
if [ -d "$OLDDIR" ] && [ ! -e "$NEWDIR" ]; then
  mv -v "$OLDDIR" "$NEWDIR"
else
  echo "  skip folder mv (old missing or new exists)"
fi

# 2) update db: path + alias (KOMPLETE collation, backup, REINDEX, integrity)
python3 - "$LIVE" "$OLDPATH_WIN" "$NEWPATH_WIN" "$NEWNAME" "$OLDNAME" <<'PY'
import sqlite3,sys,os,shutil,time
db,oldp,newp,newname,oldname=sys.argv[1:6]
def k(a,b):
    a=(a or "").strip().casefold();b=(b or "").strip().casefold();return (a>b)-(a<b)
bk=f"{db}.pre_pgfolder_{time.strftime('%Y%m%d_%H%M%S')}"; shutil.copy2(db,bk); print("  db backup:",bk)
for s in ("-wal","-shm"):
    if os.path.exists(db+s): shutil.copy2(db+s,bk+s)
con=sqlite3.connect(db);con.create_collation("KOMPLETE",k);c=con.cursor()
try: c.execute("REINDEX"); con.commit()
except Exception as e: print("  REINDEX err:",e)
c.execute("UPDATE k_content_path SET path=?, alias=? WHERE path=?",(newp,newname,oldp))
n=c.rowcount
if n==0:
    # fallback: match by LIKE if exact path differs
    c.execute("UPDATE k_content_path SET path=?, alias=? WHERE path LIKE '%PlugInGuru.MegaMagic%'",(newp,newname))
    n=c.rowcount
con.commit()
print("  rows updated:",n)
print("  integrity:", c.execute("PRAGMA integrity_check").fetchone()[0])
con.close()
for s in ("-wal","-shm"):
    p=db+s
    if os.path.exists(p): os.remove(p)
PY

# 3) create the image dir matching the NEW dot-free folder name
DEST="$NIIMG/$NEWNAME"
COVER="$NEWDIR/$COVER_REL"
[ -f "$COVER" ] || COVER="$OLDDIR/$COVER_REL"
mkdir -p "$DEST"
magick "$COVER" -auto-orient -resize "134x66^"  -gravity center -extent "134x66"  -strip -define png:color-type=2 "$DEST/MST_artwork.png" 2>/dev/null
magick "$COVER" -auto-orient -resize "127x100^" -gravity center -extent "127x100" -strip -define png:color-type=2 "$DEST/MST_plugin.png" 2>/dev/null
magick "$COVER" -auto-orient -resize "240x196^" -gravity center -extent "240x196" -strip -define png:color-type=2 "$DEST/MST_logo.png" 2>/dev/null
printf '<?xml version="1.0" encoding="UTF-8" standalone="no" ?>\n<resource version="2.1544">\n<name>%s</name>\n<type>image</type>\n</resource>\n' "$NEWNAME" > "$DEST/$NEWNAME.meta"
echo "  image dir: $(ls "$DEST" | tr '\n' ' ')"

# 4) clean the earlier failed candidate dirs
for d in "PlugInGuru.MegaMagic.Bells.Winds.KONTAKT" "Mega Magic Bells_Winds" "Mega Magic Bells" "MegaMagic Bells_Winds"; do
  [ -d "$NIIMG/$d" ] && { rm -rf "$NIIMG/$d"; echo "  removed stale image dir: $d"; }
done

echo
echo "ROLLBACK: mv \"$NEWDIR\" \"$OLDDIR\"; restore db from the pre_pgfolder_* backup; rm -rf \"$DEST\""
echo "NEXT: launch Reaper, load Kontakt. PlugInGuru (now 'PlugInGuru MegaMagic Bells Winds') should show a tile."
