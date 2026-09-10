#!/usr/bin/env python3
# score-db-backups.py (READ-ONLY on copies)
# I wrongly restored an OLD backup (pre_ewqlra, ~sep6) that reintroduced D:/F: paths. Find the CORRECT
# source: newest komplete.db3 backup that has BOTH (a) clean Z: paths (no D:\ or F:\ in k_content_path.path)
# AND (b) content_type=2 tile libraries. Score every candidate so we pick the right 'yesterday' db.
import sqlite3, os, subprocess, tempfile, glob, time

BASE="/mnt/workspace/VST Install/Kontakt Portable/UserData/Kontakt 8"
UD="/mnt/workspace/VST Install/Kontakt Portable/UserData"

def kompare(a,b):
    a=(a or "").strip().casefold(); b=(b or "").strip().casefold(); return (a>b)-(a<b)

def copy(src):
    d=tempfile.mktemp(suffix=".db3"); subprocess.run(["dd",f"if={src}",f"of={d}","bs=1M"],stderr=subprocess.DEVNULL)
    for s in ("-wal","-shm"):
        if os.path.exists(src+s): subprocess.run(["dd",f"if={src+s}",f"of={d+s}","bs=1M"],stderr=subprocess.DEVNULL)
    return d

# gather all komplete*.db3 candidates (live + backups), >1MB, anywhere under UserData
cands=[]
for pat in (f"{BASE}/komplete*.db3*", f"{UD}/**/komplete*.db3*"):
    cands += glob.glob(pat, recursive=True)
cands=[c for c in set(cands) if os.path.isfile(c) and not c.endswith(("-wal","-shm")) and os.path.getsize(c)>1_000_000]
# sort newest first
cands.sort(key=lambda p: os.path.getmtime(p), reverse=True)

print(f"{'MTIME':17} {'SIZE(MB)':>8} {'PATHS':>5} {'TYPE2':>5} {'D:':>4} {'F:':>4}  FILE")
for src in cands:
    mt=time.strftime('%Y-%m-%d %H:%M', time.localtime(os.path.getmtime(src)))
    mb=os.path.getsize(src)//(1024*1024)
    d=copy(src)
    paths=t2=dc=fc=-1
    try:
        con=sqlite3.connect(d); con.create_collation("KOMPLETE",kompare); c=con.cursor()
        try: c.execute("PRAGMA wal_checkpoint(FULL)")
        except Exception: pass
        paths=c.execute("SELECT COUNT(*) FROM k_content_path").fetchone()[0]
        t2=c.execute("SELECT COUNT(*) FROM k_content_path WHERE content_type=2").fetchone()[0]
        dc=c.execute("SELECT COUNT(*) FROM k_content_path WHERE path LIKE 'D:%'").fetchone()[0]
        fc=c.execute("SELECT COUNT(*) FROM k_content_path WHERE path LIKE 'F:%'").fetchone()[0]
        con.close()
    except Exception as e:
        paths=f"ERR"
    finally:
        for p in (d,d+"-wal",d+"-shm"):
            try: os.remove(p)
            except OSError: pass
    flag = " <== GOOD (Z-clean + tiles)" if (t2 and t2>0 and dc==0 and fc==0) else ""
    print(f"{mt:17} {mb:8} {str(paths):>5} {str(t2):>5} {str(dc):>4} {str(fc):>4}  {os.path.basename(src)}{flag}")

print("\nREAD-ONLY. Pick the NEWEST row with TYPE2>0 AND D:=0 AND F:=0 — that's the correct 'yesterday' db")
print("(clean Z: paths + working tiles). We restore THAT, not the old pre_ewqlra.")
