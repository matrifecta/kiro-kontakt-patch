#!/usr/bin/env python3
# verify-alltiles-db.py (READ-ONLY on a copy)
# Differentiator found: content_type 2 (Player/NKS, tiles) vs 3 (User/Custom, folder icon).
# LIVE db demoted libs to type 3 (blank). The 42MB pre_ewqlra backup had them type 2 (tiles).
# Verify the pre_ewqlra backup is the right restore source: integrity ok, count of type-2 vs type-3,
# and that the specific blank libs are type 2 there. Also compare against LIVE type distribution.
import sqlite3, os, subprocess, tempfile

BASE="/mnt/workspace/VST Install/Kontakt Portable/UserData/Kontakt 8"
CANDIDATES={
  "LIVE (blank)": f"{BASE}/komplete.db3",
  "pre_ewqlra 42MB (tiles)": f"{BASE}/komplete.db3.pre_ewqlra_144329",
}
BLANKS=["Middle East","Balinese Gamelan","Straylight","Soul Sessions","East Asia","India",
        "Piano Colors","Mass","Amati Viola","Cloud Supply","Butch Vig Drums"]

def kompare(a,b):
    a=(a or "").strip().casefold(); b=(b or "").strip().casefold(); return (a>b)-(a<b)

def copy(src):
    d=tempfile.mktemp(suffix=".db3"); subprocess.run(["dd",f"if={src}",f"of={d}","bs=1M"],stderr=subprocess.DEVNULL)
    for s in ("-wal","-shm"):
        if os.path.exists(src+s): subprocess.run(["dd",f"if={src+s}",f"of={d+s}","bs=1M"],stderr=subprocess.DEVNULL)
    return d

for label,src in CANDIDATES.items():
    print(f"\n===== {label}: {src} =====")
    if not os.path.exists(src): print("  MISSING"); continue
    d=copy(src)
    try:
        con=sqlite3.connect(d); con.create_collation("KOMPLETE",kompare); c=con.cursor()
        try: c.execute("PRAGMA wal_checkpoint(FULL)")
        except Exception: pass
        print("  integrity:", c.execute("PRAGMA integrity_check").fetchone()[0])
        print("  content paths:", c.execute("SELECT COUNT(*) FROM k_content_path").fetchone()[0])
        print("  by content_type:")
        for ct,n in c.execute("SELECT content_type, COUNT(*) FROM k_content_path GROUP BY content_type ORDER BY content_type"):
            meaning={2:"Player/NKS (tile)",3:"User/Custom (folder icon)"}.get(ct,"?")
            print(f"     type {ct} = {n}   ({meaning})")
        print("  specific libs (alias -> content_type):")
        for lib in BLANKS:
            row=c.execute("SELECT alias,content_type FROM k_content_path WHERE alias=? LIMIT 1",(lib,)).fetchone()
            print(f"     {lib:22s} -> {row[1] if row else 'NOT FOUND'}")
        con.close()
    except Exception as e:
        print("  ERR:", e)
    finally:
        for p in (d,d+"-wal",d+"-shm"):
            try: os.remove(p)
            except OSError: pass
print("\nREAD-ONLY. If pre_ewqlra shows the blank libs as type 2 + integrity ok, it's the correct restore")
print("source to bring tiles back. LIVE will show them as type 3 (why they're folder icons now).")
