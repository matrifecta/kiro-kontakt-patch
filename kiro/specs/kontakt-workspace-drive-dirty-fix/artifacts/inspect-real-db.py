#!/usr/bin/env python3
# inspect-real-db.py (READ-ONLY on copies)
# CORRECTION: the REAL browser DB is UserData/Kontakt 8/komplete.db3 (78MB, live, has -wal), NOT
# UserData/komplete.db3 (0-byte decoy). Compare the LIVE real db vs the 42MB all-tiles backup
# (pre_ewqlra) to see which libraries carry tile artwork/records and what differs.
# Reads local COPIES (dd) so FUSE/lock/WAL state can't corrupt the read; checkpoints WAL on the copy.
import sqlite3, os, subprocess, tempfile, sys

BASE="/mnt/workspace/VST Install/Kontakt Portable/UserData/Kontakt 8"
LIVE=f"{BASE}/komplete.db3"
ALLTILES=f"{BASE}/komplete.db3.pre_ewqlra_144329"   # 41.7MB, tiles-working era

def kompare(a,b):
    a=(a or "").strip().casefold(); b=(b or "").strip().casefold()
    return (a>b)-(a<b)

def localcopy(src):
    dst=tempfile.mktemp(suffix=".db3")
    # dd reads real bytes even if stat is weird; include wal if present so we can checkpoint
    subprocess.run(["dd", f"if={src}", f"of={dst}", "bs=1M"], stderr=subprocess.DEVNULL)
    for sfx in ("-wal","-shm"):
        if os.path.exists(src+sfx):
            subprocess.run(["dd", f"if={src+sfx}", f"of={dst+sfx}", "bs=1M"], stderr=subprocess.DEVNULL)
    return dst

def analyze(label, src):
    print(f"\n===== {label}: {src} =====")
    print(f"  on-disk size: {os.path.getsize(src) if os.path.exists(src) else 'MISSING'}")
    dst=localcopy(src)
    print(f"  local copy size: {os.path.getsize(dst)}")
    try:
        con=sqlite3.connect(dst); con.create_collation("KOMPLETE", kompare); cur=con.cursor()
        try: cur.execute("PRAGMA wal_checkpoint(FULL)")
        except Exception as e: print("  wal_checkpoint:", e)
        tbls=[r[0] for r in cur.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
        print(f"  tables: {len(tbls)}")
        for t in ("k_content_path","k_sound_info"):
            try: print(f"  {t}: {cur.execute(f'SELECT COUNT(*) FROM {t}').fetchone()[0]}")
            except Exception as e: print(f"  {t}: ERR {e}")
        # dump k_content_path schema + a working vs blank row
        cols=[c[1] for c in cur.execute("PRAGMA table_info(k_content_path)").fetchall()]
        print(f"  k_content_path cols: {cols}")
        # try to show rows for a few libs (match any text column)
        def find(like):
            try:
                q="SELECT * FROM k_content_path WHERE " + " OR ".join(f"CAST({c} AS TEXT) LIKE ?" for c in cols)
                return cur.execute(q, tuple(f"%{like}%" for _ in cols)).fetchall(), cols
            except Exception as e:
                return f"ERR {e}", cols
        for lib in ("Amati","Middle East"):
            rows,_=find(lib)
            print(f"  -- {lib}: ", end="")
            if isinstance(rows,str): print(rows)
            else:
                print(f"{len(rows)} row(s)")
                for r in rows[:1]:
                    for cn,v in zip(cols,r):
                        if isinstance(v,(bytes,bytearray)): v=f"<blob {len(v)}B>"
                        print(f"       {cn}={v}")
        con.close()
    except Exception as e:
        print("  OPEN ERR:", e)
    finally:
        for p in (dst,dst+"-wal",dst+"-shm"):
            try: os.remove(p)
            except OSError: pass

analyze("LIVE (78MB, current, blank subset)", LIVE)
analyze("ALL-TILES backup (42MB, pre_ewqlra)", ALLTILES)
print("\nREAD-ONLY. Compare content_path counts + the Amati(working) vs Middle East(blank) row fields")
print("between the two DBs to find what the live db lost that the 42MB tiles-working db has.")
