#!/usr/bin/env python3
# diff-db-content2.py (READ-ONLY-ish: only checkpoints WAL into the LIVE db, no schema/data change)
# The first diff read live=-1 (couldn't read live komplete.db3 — likely uncommitted WAL or open error).
# This version: reports any -wal/-shm, opens each DB and prints the actual error if a table read fails,
# lists tables, and checkpoints the live WAL (read-only intent) so counts are accurate. Then diffs paths.
import sqlite3, sys, os

LIVE = "/mnt/workspace/VST Install/Kontakt Portable/UserData/komplete.db3"
SNAP = "/mnt/wd_black/kontakt-known-good-20260907_123950/kontakt_userdata/komplete.db3"

def kompare(a,b):
    a=(a or "").strip().casefold(); b=(b or "").strip().casefold()
    return (a>b)-(a<b)

def info(path, label):
    print(f"\n===== {label}: {path} =====")
    for sfx in ("", "-wal", "-shm"):
        p=path+sfx
        print(f"  {os.path.basename(p):24s} exists={os.path.exists(p)} size={os.path.getsize(p) if os.path.exists(p) else '-'}")
    try:
        con=sqlite3.connect(path)
        con.create_collation("KOMPLETE", kompare)
        cur=con.cursor()
        # checkpoint WAL so we read the true current state
        try: cur.execute("PRAGMA wal_checkpoint(FULL)")
        except Exception as e: print("  wal_checkpoint:", e)
        tbls=[r[0] for r in cur.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
        print(f"  tables ({len(tbls)}):", ", ".join(sorted(tbls))[:400])
        for t in ("k_content_path","k_sound_info"):
            try: print(f"  count {t}:", cur.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0])
            except Exception as e: print(f"  count {t}: ERROR {e}")
        # grab content paths
        cps=set()
        try: cps={ r[0] for r in cur.execute("SELECT k_content_path FROM k_content_path").fetchall() }
        except Exception as e: print("  read k_content_path ERROR:", e)
        con.close()
        return cps
    except Exception as e:
        print("  OPEN ERROR:", e)
        return None

lp=info(LIVE,"LIVE")
sp=info(SNAP,"SNAPSHOT")

if lp is not None and sp is not None:
    only_live=sorted(lp-sp, key=lambda x:(x or '').lower())
    only_snap=sorted(sp-lp, key=lambda x:(x or '').lower())
    print(f"\n=== in LIVE but NOT snapshot ({len(only_live)}) — would be LOST by restore ===")
    for p in only_live: print("   +",p)
    print(f"\n=== in SNAPSHOT but NOT live ({len(only_snap)}) ===")
    for p in only_snap: print("   -",p)
else:
    print("\nCould not compare — see OPEN/READ errors above.")
print("\nNOTE: wal_checkpoint only flushes the live WAL into its own db (normal SQLite housekeeping); it")
print("does not alter Kontakt data. Still, Kontakt must be CLOSED when running this (it was: wineserver -k).")
