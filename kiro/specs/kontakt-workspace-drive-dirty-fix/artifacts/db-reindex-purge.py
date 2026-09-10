#!/usr/bin/env python3
"""
db-reindex-purge.py

Diagnosis (2026-09-07): integrity_check (run via Python with the KOMPLETE collation
registered) shows the ONLY problem is stale secondary indexes:
    "row N missing from index index_p_sound_info_*_sort_order"
The TABLE DATA is intact (k_content_path=70, k_sound_info=85325 read fine). The same
index staleness is present in every backup too -> pre-existing, benign to data, but it
makes any write that touches those indexes throw 'database disk image is malformed'.

FIX: register the KOMPLETE collation, REINDEX (rebuilds all indexes from the intact
table rows), confirm integrity is clean, THEN delete the 55,265 orphaned k_sound_info
rows (parent content_path already gone) and VACUUM.

Kontakt CLOSED. Full backup first. Reversible.

Usage:
  python3 db-reindex-purge.py            # dry-run: reindex into a COPY, report integrity
  python3 db-reindex-purge.py apply       # reindex + purge orphans + vacuum on the live DB
"""
import sqlite3, sys, os, shutil, time

K8 = "/mnt/workspace/VST Install/Kontakt Portable/UserData/Kontakt 8"
DB = os.path.join(K8, "komplete.db3")
MODE = sys.argv[1] if len(sys.argv) > 1 else "dryrun"

def kompare(a, b):
    x = (a or "").strip().casefold(); y = (b or "").strip().casefold()
    return (x > y) - (x < y)

def open_db(path):
    c = sqlite3.connect(path)
    c.create_collation("KOMPLETE", kompare)
    return c

if not os.path.exists(DB):
    print("ABORT: no DB at", DB); sys.exit(1)

stamp = time.strftime("%Y%m%d_%H%M%S")

if MODE != "apply":
    # work on a throwaway copy so the live DB is untouched
    tmp = os.path.join(K8, f".reindex_test_{stamp}.db3")
    shutil.copy2(DB, tmp)
    print("dry-run copy:", tmp)
    con = open_db(tmp)
    cur = con.cursor()
    print("REINDEX on copy ...")
    try:
        cur.execute("REINDEX;")
        con.commit()
        print("  REINDEX ok")
    except sqlite3.Error as e:
        print("  REINDEX error:", e)
    bad = 0
    for row in cur.execute("PRAGMA integrity_check;"):
        if row[0] != "ok":
            bad += 1
            if bad <= 5: print("  still-bad:", row[0])
    print("  integrity after reindex:", "ok" if bad == 0 else f"{bad} issues")
    keep = [r[0] for r in cur.execute("SELECT id FROM k_content_path;").fetchall()]
    ph = ",".join("?" for _ in keep)
    orph = cur.execute(f"SELECT COUNT(*) FROM k_sound_info WHERE content_path_id NOT IN ({ph});", keep).fetchone()[0]
    print("  orphans that WOULD be deleted:", orph)
    con.close()
    os.remove(tmp)
    print("\nDRY-RUN done (copy removed). If integrity==ok, run:  python3", sys.argv[0], "apply")
    sys.exit(0)

# ---- APPLY on live DB ----
bak = f"{DB}.pre_reindexpurge_{stamp}"
shutil.copy2(DB, bak)
print("backup:", bak)

con = open_db(DB)
cur = con.cursor()

print("REINDEX (rebuild all indexes from table data) ...")
cur.execute("REINDEX;")
con.commit()
bad = sum(1 for row in cur.execute("PRAGMA integrity_check;") if row[0] != "ok")
print("integrity after reindex:", "ok" if bad == 0 else f"{bad} issues (stopping)")
if bad != 0:
    con.close()
    print("Aborting before delete; restore with the backup if needed.")
    sys.exit(1)

keep = [r[0] for r in cur.execute("SELECT id FROM k_content_path;").fetchall()]
ph = ",".join("?" for _ in keep)
before = cur.execute("SELECT COUNT(*) FROM k_sound_info;").fetchone()[0]
print("deleting orphaned k_sound_info ...")
cur.execute(f"DELETE FROM k_sound_info WHERE content_path_id NOT IN ({ph});", keep)
for tbl, col in (("k_sound_info_category","sound_info_id"), ("k_sound_info_mode","sound_info_id")):
    try:
        cur.execute(f"DELETE FROM {tbl} WHERE {col} NOT IN (SELECT id FROM k_sound_info);")
        print("  cleaned", tbl)
    except sqlite3.Error as e:
        print(f"  ({tbl}: {e})")
con.commit()
after = cur.execute("SELECT COUNT(*) FROM k_sound_info;").fetchone()[0]
print(f"k_sound_info: {before} -> {after}")

print("final integrity:", "ok" if sum(1 for r in cur.execute("PRAGMA integrity_check;") if r[0]!="ok")==0 else "ISSUES")
print("VACUUM ...")
con.execute("VACUUM;"); con.commit()
con.close()

lk = os.path.join(K8, "lock.lck")
if os.path.exists(lk): os.remove(lk); print("removed stale lock")
print("size now:", os.path.getsize(DB), "bytes")
print("\nROLLBACK (Kontakt closed): cp -av", repr(bak), repr(DB))
