#!/usr/bin/env python3
# probe-df-paths.py (READ-ONLY) — show the 4 residual D:/F: rows in k_content_path so we can decide whether to
# converge them to Z: or leave them. For each: full row + whether the equivalent Z: path exists on disk.
import sqlite3, os, subprocess, tempfile

LIVE="/mnt/workspace/VST Install/Kontakt Portable/UserData/Kontakt 8/komplete.db3"
def k(a,b):
    a=(a or "").strip().casefold();b=(b or "").strip().casefold();return (a>b)-(a<b)
def copy(src):
    d=tempfile.mktemp(suffix=".db3");subprocess.run(["dd",f"if={src}",f"of={d}","bs=1M"],stderr=subprocess.DEVNULL)
    for s in ("-wal","-shm"):
        if os.path.exists(src+s):subprocess.run(["dd",f"if={src+s}",f"of={d+s}","bs=1M"],stderr=subprocess.DEVNULL)
    return d

def winpath_to_linux(p):
    if len(p)>=2 and p[1]==":":
        drive=p[0].upper(); rest=p[2:].replace("\\","/")
        m={"Z":"","D":"/mnt/workspace","F":"/mnt/workspace","G":"/mnt/btrfs_disk","L":"/mnt/wd_black","W":"/mnt/win_system"}
        return m.get(drive,"?")+rest
    return p

d=copy(LIVE); con=sqlite3.connect(d); con.create_collation("KOMPLETE",k); c=con.cursor()
try: c.execute("PRAGMA wal_checkpoint(FULL)")
except Exception: pass
cols=[r[1] for r in c.execute("PRAGMA table_info(k_content_path)")]
rows=c.execute("SELECT * FROM k_content_path WHERE path LIKE 'D:%' OR path LIKE 'F:%'").fetchall()
print(f"{len(rows)} D:/F: rows in k_content_path:\n")
for r in rows:
    dd=dict(zip(cols,r))
    print(f"  id={dd['id']}  type={dd['content_type']}  alias={dd['alias']!r}")
    print(f"     path={dd['path']}")
    # does this D:/F: path resolve on disk? and would a Z: equivalent resolve?
    lin=winpath_to_linux(dd['path'])
    print(f"     D/F -> {lin}   [{'EXISTS' if os.path.exists(lin) else 'MISSING'}]")
    # Z: equivalent = same tail under / (both D: and F: map to /mnt/workspace here)
    ztail = dd['path'][2:].replace("\\","/")   # strip drive, keep rest
    zlin = ztail if ztail.startswith("/mnt") else "/mnt/workspace"+ztail
    print(f"     Z: equiv -> {zlin}   [{'EXISTS' if os.path.exists(zlin) else 'MISSING'}]")
    # how many sound_info rows depend on this content_path
    n=c.execute("SELECT COUNT(*) FROM k_sound_info WHERE content_path_id=?",(dd['id'],)).fetchone()[0]
    print(f"     k_sound_info rows referencing it: {n}")
    print()
con.close()
for x in (d,d+"-wal",d+"-shm"):
    try:os.remove(x)
    except OSError:pass
print("READ-ONLY. For each: if the D:/F: path is a stale duplicate of a Z: entry that already exists, it can be")
print("removed; if it's the ONLY entry for real content, converge its drive letter to Z: instead of deleting.")
