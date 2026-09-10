#!/usr/bin/env bash
# revert-pluginguru-rename.sh
# The folder rename broke Import Content preset paths ("File not found"). Undo it fully:
#   1) rename the folder back to the original dotted name
#   2) restore the db from the pre_pgfolder backup (reverts path + alias to the dotted original)
#   3) remove the authored clean-name image dir (no longer matches; harmless leftover)
# Result: PlugInGuru works exactly as before this step (loads fine; folder icon, no tile). Kontakt closed.
#
# Usage: bash revert-pluginguru-rename.sh          # dry-run
#        bash revert-pluginguru-rename.sh apply
set -u
MODE="${1:-dryrun}"
NIIMG="/mnt/workspace/VST Install/Kontakt Portable/UserData/NI Resources/image"
BASECUST="/mnt/btrfs_disk/Kontakt Libraries/Custom"
LIVE="/mnt/workspace/VST Install/Kontakt Portable/UserData/Kontakt 8/komplete.db3"
NEWDIR="$BASECUST/PlugInGuru MegaMagic Bells Winds"
OLDDIR="$BASECUST/PlugInGuru.MegaMagic.Bells.Winds.KONTAKT"
DBBAK="$LIVE.pre_pgfolder_20260909_141034"
IMGCLEAN="$NIIMG/PlugInGuru MegaMagic Bells Winds"

echo "=== revert PlugInGuru folder rename ==="
echo "  folder: '$NEWDIR' -> '$OLDDIR'"
echo "  db restore from: $DBBAK"
echo "  remove image dir: $IMGCLEAN"
[ -f "$DBBAK" ] || { echo "  WARN: db backup missing — will revert db via SQL instead"; }

if pgrep -x wineserver >/dev/null 2>&1 || pgrep -x reaper >/dev/null 2>&1; then
  echo "  *** close Reaper + wineserver -k first ***"; [ "$MODE" = apply ] && { echo ABORT; exit 1; }
fi
if [ "$MODE" != apply ]; then echo; echo "DRY-RUN. Re-run: bash $0 apply"; exit 0; fi

# 1) folder back
if [ -d "$NEWDIR" ] && [ ! -e "$OLDDIR" ]; then mv -v "$NEWDIR" "$OLDDIR"; else echo "  skip folder mv"; fi

# 2) db: prefer restoring the exact pre_pgfolder backup (also reverts the alias to dotted)
if [ -f "$DBBAK" ]; then
  cp -av "$DBBAK" "$LIVE" | sed 's/^/  /'
  rm -f "$LIVE"-wal "$LIVE"-shm
  echo "  db restored from pre_pgfolder backup"
else
  python3 - "$LIVE" <<'PY'
import sqlite3,sys,os,shutil,time
db=sys.argv[1]
def k(a,b):
    a=(a or "").strip().casefold();b=(b or "").strip().casefold();return (a>b)-(a<b)
bk=f"{db}.pre_pgrevert2_{time.strftime('%Y%m%d_%H%M%S')}"; shutil.copy2(db,bk); print("  db backup:",bk)
con=sqlite3.connect(db);con.create_collation("KOMPLETE",k);c=con.cursor()
old=r'Z:\mnt\btrfs_disk\Kontakt Libraries\Custom\PlugInGuru.MegaMagic.Bells.Winds.KONTAKT'
c.execute("UPDATE k_content_path SET path=?, alias=? WHERE path LIKE '%PlugInGuru MegaMagic Bells Winds%'",
          (old,"PlugInGuru.MegaMagic.Bells.Winds.KONTAKT"))
con.commit(); print("  rows reverted:",c.rowcount)
print("  integrity:", c.execute("PRAGMA integrity_check").fetchone()[0]); con.close()
for s in ("-wal","-shm"):
    p=db+s
    if os.path.exists(p): os.remove(p)
PY
fi

# 3) remove the clean-name image dir
[ -d "$IMGCLEAN" ] && { rm -rf "$IMGCLEAN"; echo "  removed clean image dir"; }

echo
echo "DONE. PlugInGuru back to original dotted name; presets should load again. It will be a folder icon (no"
echo "tile) as before. ROLLBACK of this revert: re-run rename-pluginguru-folder.sh apply."
echo "NEXT: launch Reaper, load a PlugInGuru patch to confirm it loads (no 'File not found')."
