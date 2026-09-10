#!/usr/bin/env python3
# verify-revert-state.py (READ-ONLY) — confirm the db is back to the good state after revert-dffix:
# Lo-Fi Vibes + Piano Uno should be D: paths again; type2 tile count still 46; integrity ok.
import sqlite3, os, subprocess, tempfile
LIVE="/mnt/workspace/VST Install/Kontakt Portable/UserData/Kontakt 8/komplete.db3"
def k(a,b):
    a=(a or "").strip().casefold();b=(b or "").strip().casefold();return (a>b)-(a<b)
def copy(src):
    d=tempfile.mktemp(suffix=".db3");subprocess.run(["dd",f"if={src}",f"of={d}","bs=1M"],stderr=subprocess.DEVNULL)
    for s in ("-wal","-shm"):
        if os.path.exists(src+s):subprocess.run(["dd",f"if={src+s}",f"of={d+s}","bs=1M"],stderr=subprocess.DEVNULL)
    return d
d=copy(LIVE);con=sqlite3.connect(d);con.create_collation("KOMPLETE",k);c=con.cursor()
try: c.execute("PRAGMA wal_checkpoint(FULL)")
except Exception: pass
print("integrity:", c.execute("PRAGMA integrity_check").fetchone()[0])
print("content paths:", c.execute("SELECT COUNT(*) FROM k_content_path").fetchone()[0])
print("type2 tile libs:", c.execute("SELECT COUNT(*) FROM k_content_path WHERE content_type=2").fetchone()[0])
print("\nLo-Fi Vibes / Piano Uno / Chords / Phrases rows:")
for a,ct,p in c.execute("SELECT alias,content_type,path FROM k_content_path WHERE alias IN ('Lo-Fi Vibes','Piano Uno','Chords','Phrases')"):
    print(f"  {a:14s} type={ct}  {p}")
con.close()
for x in (d,d+"-wal",d+"-shm"):
    try:os.remove(x)
    except OSError:pass
print("\nREAD-ONLY. Lo-Fi Vibes + Piano Uno should show D:\\ paths again (that's their working state).")
