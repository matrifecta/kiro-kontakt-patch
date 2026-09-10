#!/usr/bin/env bash
# probe-pg-duplicate.sh (READ-ONLY) — show BOTH PlugInGuru rows so we remove only the stale dotted one.
set -u
LIVE="/mnt/workspace/VST Install/Kontakt Portable/UserData/Kontakt 8/komplete.db3"
python3 - "$LIVE" <<'PY'
import sqlite3,sys,subprocess,tempfile,os
db=sys.argv[1]
def k(a,b):
    a=(a or "").strip().casefold();b=(b or "").strip().casefold();return (a>b)-(a<b)
d=tempfile.mktemp(suffix=".db3");subprocess.run(["dd",f"if={db}",f"of={d}","bs=1M"],stderr=subprocess.DEVNULL)
for s in ("-wal","-shm"):
    if os.path.exists(db+s):subprocess.run(["dd",f"if={db+s}",f"of={d+s}","bs=1M"],stderr=subprocess.DEVNULL)
con=sqlite3.connect(d);con.create_collation("KOMPLETE",k);c=con.cursor()
print("PlugInGuru / MegaMagic rows in k_content_path:")
for i,a,ct,p in c.execute("SELECT id,alias,content_type,path FROM k_content_path WHERE alias LIKE '%MegaMagic%' OR alias LIKE '%PlugInGuru%' OR path LIKE '%MegaMagic%'"):
    disk = "EXISTS" if os.path.isdir(p.replace('\\','/').replace('Z:','')) else "MISSING(on-disk)"
    print(f"  id={i}  type={ct}  alias='{a}'")
    print(f"       path={p}   [{disk}]")
con.close()
for x in (d,d+"-wal",d+"-shm"):
    try:os.remove(x)
    except OSError:pass
PY
echo
echo "READ-ONLY. The row whose path is the OLD dotted 'PlugInGuru.MegaMagic.Bells.Winds.KONTAKT' (folder now"
echo "MISSING) is the stale duplicate to Remove. Keep the row with 'PlugInGuru MegaMagic Bells Winds' (works)."
