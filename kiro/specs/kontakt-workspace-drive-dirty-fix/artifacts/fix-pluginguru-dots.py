#!/usr/bin/env python3
# fix-pluginguru-dots.py
#
# PlugInGuru is the ONLY NI image dir (of 85) with dots in its name; all rendering tiles are dot-free. The tile
# key for these Custom libs = the db alias, which is 'PlugInGuru.MegaMagic.Bells.Winds.KONTAKT' (dotted). Fix:
#   1) rename the db alias to a clean dot-free name 'PlugInGuru MegaMagic Bells Winds' (Kontakt closed; backup;
#      KOMPLETE collation; REINDEX; integrity).
#   2) the caller then creates NI Resources/image/<clean name>/ (done by the companion shell step) and removes
#      the old dotted image dir.
# This changes only the display alias (cosmetic label in the browser), not the path/content.
#
# Usage: python3 fix-pluginguru-dots.py            # dry-run
#        python3 fix-pluginguru-dots.py apply
import sqlite3, os, subprocess, tempfile, sys, time, shutil

BASE="/mnt/workspace/VST Install/Kontakt Portable/UserData/Kontakt 8"
LIVE=f"{BASE}/komplete.db3"
OLD="PlugInGuru.MegaMagic.Bells.Winds.KONTAKT"
NEW="PlugInGuru MegaMagic Bells Winds"
MODE=sys.argv[1] if len(sys.argv)>1 else "dryrun"

def k(a,b):
    a=(a or "").strip().casefold(); b=(b or "").strip().casefold(); return (a>b)-(a<b)
def copy(src):
    d=tempfile.mktemp(suffix=".db3"); subprocess.run(["dd",f"if={src}",f"of={d}","bs=1M"],stderr=subprocess.DEVNULL)
    for s in ("-wal","-shm"):
        if os.path.exists(src+s): subprocess.run(["dd",f"if={src+s}",f"of={d+s}","bs=1M"],stderr=subprocess.DEVNULL)
    return d
def running():
    for pat in (["pgrep","-x","wineserver"],["pgrep","-fi","Kontakt 8"],["pgrep","-x","reaper"]):
        if subprocess.run(pat,stdout=subprocess.DEVNULL).returncode==0: return True
    return False

d=copy(LIVE); con=sqlite3.connect(d); con.create_collation("KOMPLETE",k); c=con.cursor()
try: c.execute("PRAGMA wal_checkpoint(FULL)")
except Exception: pass
rows=c.execute("SELECT id,alias,content_type,path FROM k_content_path WHERE alias=?",(OLD,)).fetchall()
con.close()
for p in (d,d+"-wal",d+"-shm"):
    try: os.remove(p)
    except OSError: pass

print(f"rename db alias:\n  '{OLD}'\n  -> '{NEW}'")
if not rows: raise SystemExit("  no row with that alias — nothing to do.")
for rid,alias,ct,path in rows: print(f"  match id={rid} type={ct} path={path}")

if running():
    print("\n  *** close Reaper + wineserver -k first ***")
    if MODE=="apply": raise SystemExit("ABORT")

if MODE!="apply":
    print(f"\nDRY-RUN. Re-run: python3 {sys.argv[0]} apply"); raise SystemExit(0)

stamp=time.strftime("%Y%m%d_%H%M%S"); bk=f"{LIVE}.pre_pgalias_{stamp}"
shutil.copy2(LIVE,bk); print(f"backup: {bk}")
for s in ("-wal","-shm"):
    if os.path.exists(LIVE+s): shutil.copy2(LIVE+s,bk+s)
con=sqlite3.connect(LIVE); con.create_collation("KOMPLETE",k); c=con.cursor()
try: c.execute("REINDEX"); con.commit(); print("REINDEX: done")
except Exception as e: print("REINDEX err:",e)
c.execute("UPDATE k_content_path SET alias=? WHERE alias=?",(NEW,OLD)); con.commit()
print("rows updated:", c.rowcount)
print("integrity:", c.execute("PRAGMA integrity_check").fetchone()[0])
con.close()
for s in ("-wal","-shm"):
    pth=LIVE+s
    if os.path.exists(pth): os.remove(pth); print(f"removed stale {os.path.basename(pth)}")
print(f"\nROLLBACK: cp -av \"{bk}\" \"{LIVE}\"; rm -f \"{LIVE}\"-wal \"{LIVE}\"-shm")
print(f"NEXT: create NI Resources/image/'{NEW}'/ from the PlugInGuru cover, remove the old dotted image dir.")
