#!/usr/bin/env bash
# probe-pluginguru-key.sh (READ-ONLY)
# Browser still LABELS the entry 'PlugInGuru.MegaMagic.Bells.Winds.KONTAKT' even after we renamed the db alias
# to 'PlugInGuru MegaMagic Bells Winds'. So Kontakt is NOT using the db alias for the label/key here — it uses
# the library's own name (folder name or an internal name). The tile image dir must match THAT key.
# Check: (1) current db alias for id 247; (2) the lib folder name; (3) any name file inside the lib
# (.nkc/.nki/name.txt/xml) that could be the display key; (4) which image dirs currently exist for it.
set -u
NIIMG="/mnt/workspace/VST Install/Kontakt Portable/UserData/NI Resources/image"
LIVE="/mnt/workspace/VST Install/Kontakt Portable/UserData/Kontakt 8/komplete.db3"
LIB="/mnt/btrfs_disk/Kontakt Libraries/Custom/PlugInGuru.MegaMagic.Bells.Winds.KONTAKT"

echo "=== db row id 247 (current alias?) ==="
python3 - "$LIVE" <<'PY'
import sqlite3,sys,subprocess,tempfile,os
db=sys.argv[1]
def k(a,b):
    a=(a or "").strip().casefold();b=(b or "").strip().casefold();return (a>b)-(a<b)
d=tempfile.mktemp(suffix=".db3");subprocess.run(["dd",f"if={db}",f"of={d}","bs=1M"],stderr=subprocess.DEVNULL)
for s in ("-wal","-shm"):
    if os.path.exists(db+s):subprocess.run(["dd",f"if={db+s}",f"of={d+s}","bs=1M"],stderr=subprocess.DEVNULL)
con=sqlite3.connect(d);con.create_collation("KOMPLETE",k);c=con.cursor()
for a,ct,p in c.execute("SELECT alias,content_type,path FROM k_content_path WHERE path LIKE '%MegaMagic%' OR alias LIKE '%MegaMagic%'"):
    print(f"  alias='{a}' type={ct} path={p}")
con.close()
for x in (d,d+"-wal",d+"-shm"):
    try:os.remove(x)
    except OSError:pass
PY

echo
echo "=== lib folder name ==="
echo "  $(basename "$LIB")"
echo
echo "=== files in lib that may carry a display name ==="
ls -la "$LIB" | sed 's/^/  /'
echo "  -- .nki names (the instrument the browser may key on):"
find "$LIB/Instruments" -maxdepth 1 -iname '*.nki' 2>/dev/null | sed 's/^/     /' | head
echo
echo "=== image dirs currently present matching pluginguru/megamagic ==="
ls -d "$NIIMG/"*MegaMagic* "$NIIMG/"*PlugInGuru* 2>/dev/null | sed 's/^/  /'
echo
echo "READ-ONLY. The image dir name must equal the key the browser shows. If the browser still shows the dotted"
echo "name, recreate the image dir with the dotted name (the delete removed it). The 'dots block it' theory may"
echo "be wrong — Amati etc. simply have no dots; PlugInGuru may just have needed its dotted dir kept + a reload."
