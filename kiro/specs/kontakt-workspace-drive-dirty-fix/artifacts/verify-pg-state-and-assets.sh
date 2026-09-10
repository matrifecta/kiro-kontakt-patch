#!/usr/bin/env bash
# verify-pg-state-and-assets.sh (READ-ONLY)
# Web hint: newer Kontakt 8 Default-view uses BANNER assets, and working NI tiles have extra pngs
# (OSO_logo, VB_artwork, VB_logo) beyond the 3 MST files our authored dirs have. Two checks:
# 1) current db row for PlugInGuru (did the folder-rename path/alias take? what's the browser label now?)
# 2) does a WORKING authored Custom tile (Tropical Trap) render with ONLY 3 MST files? (it does) -> then the
#    asset set is NOT the differentiator. List both dirs' files to compare precisely.
# 3) list the FULL working NI dir (Electro Acoustic) to see every asset newer Kontakt might want.
set -u
NIIMG="/mnt/workspace/VST Install/Kontakt Portable/UserData/NI Resources/image"
LIVE="/mnt/workspace/VST Install/Kontakt Portable/UserData/Kontakt 8/komplete.db3"

echo "=== 1) PlugInGuru db row now ==="
python3 - "$LIVE" <<'PY'
import sqlite3,sys,subprocess,tempfile,os
db=sys.argv[1]
def k(a,b):
    a=(a or "").strip().casefold();b=(b or "").strip().casefold();return (a>b)-(a<b)
d=tempfile.mktemp(suffix=".db3");subprocess.run(["dd",f"if={db}",f"of={d}","bs=1M"],stderr=subprocess.DEVNULL)
for s in ("-wal","-shm"):
    if os.path.exists(db+s):subprocess.run(["dd",f"if={db+s}",f"of={d+s}","bs=1M"],stderr=subprocess.DEVNULL)
con=sqlite3.connect(d);con.create_collation("KOMPLETE",k);c=con.cursor()
for a,ct,p in c.execute("SELECT alias,content_type,path FROM k_content_path WHERE alias LIKE '%MegaMagic%' OR alias LIKE '%PlugInGuru%' OR path LIKE '%MegaMagic%'"):
    print(f"  alias='{a}' type={ct}"); print(f"  path={p}")
con.close()
for x in (d,d+"-wal",d+"-shm"):
    try:os.remove(x)
    except OSError:pass
PY

echo
echo "=== 2) authored dirs file sets: Tropical Trap (works) vs PlugInGuru (fails) ==="
for n in "Sonic Mechanics - Tropical Trap" "PlugInGuru MegaMagic Bells Winds"; do
  echo "  --- $n"
  ls -la "$NIIMG/$n" 2>/dev/null | sed 's/^/     /'
done

echo
echo "=== 3) a FULL NI working dir (Electro Acoustic) — every asset present ==="
ls -la "$NIIMG/Electro Acoustic" 2>/dev/null | sed 's/^/     /'

echo
echo "READ-ONLY. If Tropical Trap renders with only 3 MST files and identical structure to PlugInGuru, the"
echo "asset set is NOT the cause. Then the difference is something in how THIS entry is indexed (e.g. the db"
echo "row's product/upid fields, or it being listed under a different browser section). Report the db row."
