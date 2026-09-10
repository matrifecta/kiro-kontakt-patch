#!/usr/bin/env python3
# find-stale-pg-everywhere.py (READ-ONLY on a copy)
# A stale blank 'PlugInGuru...KONTAKT' tile persists across full restarts, but k_content_path has only the ONE
# clean row. So the old entry lives in ANOTHER table/index. Scan EVERY table + every text/blob column in the
# live db for the old dotted name OR the old path, and report exactly where it survives.
import sqlite3, os, subprocess, tempfile

LIVE="/mnt/workspace/VST Install/Kontakt Portable/UserData/Kontakt 8/komplete.db3"
NEEDLES=["PlugInGuru.MegaMagic","PlugInGuru.MegaMagic.Bells.Winds.KONTAKT",
         r"Custom\PlugInGuru.MegaMagic","MegaMagic.Bells.Winds.KONTAKT"]

def k(a,b):
    a=(a or "").strip().casefold(); b=(b or "").strip().casefold(); return (a>b)-(a<b)
def copy(src):
    d=tempfile.mktemp(suffix=".db3"); subprocess.run(["dd",f"if={src}",f"of={d}","bs=1M"],stderr=subprocess.DEVNULL)
    for s in ("-wal","-shm"):
        if os.path.exists(src+s): subprocess.run(["dd",f"if={src+s}",f"of={d+s}","bs=1M"],stderr=subprocess.DEVNULL)
    return d

d=copy(LIVE); con=sqlite3.connect(d); con.create_collation("KOMPLETE",k); c=con.cursor()
try: c.execute("PRAGMA wal_checkpoint(FULL)")
except Exception: pass
tables=[r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table'")]
print(f"scanning {len(tables)} tables for stale PlugInGuru refs...\n")
found=False
for t in tables:
    try:
        cols=[r[1] for r in c.execute(f"PRAGMA table_info('{t}')")]
    except Exception:
        continue
    if not cols: continue
    for needle in NEEDLES:
        conds=" OR ".join(f"CAST(\"{col}\" AS TEXT) LIKE ?" for col in cols)
        try:
            q=f'SELECT rowid,* FROM "{t}" WHERE {conds}'
            rows=c.execute(q, tuple(f"%{needle}%" for _ in cols)).fetchall()
        except Exception:
            continue
        if rows:
            found=True
            print(f"== TABLE {t}: {len(rows)} row(s) match '{needle}'")
            for r in rows[:3]:
                vals=[]
                for cn,v in zip(["rowid"]+cols, r):
                    if isinstance(v,(bytes,bytearray)): v=f"<blob {len(v)}B>"
                    sv=str(v)
                    if len(sv)>60: sv=sv[:60]+"..."
                    if v not in (None,"",0): vals.append(f"{cn}={sv}")
                print("     "+", ".join(vals))
            break
con.close()
for x in (d,d+"-wal",d+"-shm"):
    try: os.remove(x)
    except OSError: pass
if not found:
    print("NO stale PlugInGuru reference anywhere in the db. Then the ghost tile is NOT db-backed — it is a")
    print("browser cache OUTSIDE this db (e.g. an NKS/NI browser index in the wine prefix or a Kontakt prefs).")
print("\nREAD-ONLY.")
