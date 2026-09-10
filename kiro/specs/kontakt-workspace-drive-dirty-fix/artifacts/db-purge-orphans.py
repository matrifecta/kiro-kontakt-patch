#!/usr/bin/env python3
"""
db-purge-orphans.py

The sqlite3 CLI cannot DELETE from k_sound_info because the table/index uses a
custom collation named "KOMPLETE" that the CLI doesn't have -> every write that
touches the index aborts with 'no such collation sequence: KOMPLETE'. (Same wall
as VACUUM.)

Python's sqlite3 lets us REGISTER a collation named KOMPLETE at runtime. Kontakt's
KOMPLETE collation is (per NI) effectively a Unicode-aware case/space-normalizing
text sort; for a DELETE we only need SOME valid comparator so the index can be
maintained. We register a reasonable NOCASE-like collation so ordering stays sane.
That unblocks the DELETE of the 55,265 orphaned k_sound_info rows (whose parent
content_path_id was already removed), which clears the browser dupes + preset count.

Run with Kontakt CLOSED. Backs up the DB first. Reversible.

Usage:
  python3 db-purge-orphans.py            # dry-run (counts only)
  python3 db-purge-orphans.py apply       # delete orphans
"""
import sqlite3, sys, os, shutil, time

K8 = "/mnt/workspace/VST Install/Kontakt Portable/UserData/Kontakt 8"
DB = os.path.join(K8, "komplete.db3")
MODE = sys.argv[1] if len(sys.argv) > 1 else "dryrun"

def komplete_collation(a, b):
    # normalize like Kontakt's browser sort: casefold + strip, then compare.
    x = (a or "").strip().casefold()
    y = (b or "").strip().casefold()
    return (x > y) - (x < y)

if not os.path.exists(DB):
    print("ABORT: no DB at", DB); sys.exit(1)

con = sqlite3.connect(DB)
con.create_collation("KOMPLETE", komplete_collation)
cur = con.cursor()

keep = [r[0] for r in cur.execute("SELECT id FROM k_content_path;").fetchall()]
placeholders = ",".join("?" for _ in keep)
print(f"surviving content-path ids: {len(keep)}")

total = cur.execute("SELECT COUNT(*) FROM k_sound_info;").fetchone()[0]
orph  = cur.execute(
    f"SELECT COUNT(*) FROM k_sound_info WHERE content_path_id NOT IN ({placeholders});",
    keep).fetchone()[0]
print(f"k_sound_info total:   {total}")
print(f"k_sound_info orphans: {orph}")
print(f"k_sound_info keep:    {total - orph}")

if MODE != "apply":
    print("\nDRY-RUN. Re-run with:  python3", sys.argv[0], "apply")
    sys.exit(0)

stamp = time.strftime("%Y%m%d_%H%M%S")
bak = f"{DB}.pre_pyorphan_{stamp}"
con.close()
shutil.copy2(DB, bak)
print("backup:", bak)

con = sqlite3.connect(DB)
con.create_collation("KOMPLETE", komplete_collation)
cur = con.cursor()

print("deleting orphaned k_sound_info ...")
cur.execute(f"DELETE FROM k_sound_info WHERE content_path_id NOT IN ({placeholders});", keep)
# clean dependent child tables by referential orphan (ids no longer in k_sound_info)
for tbl, col in (("k_sound_info_category", "sound_info_id"),
                 ("k_sound_info_mode", "sound_info_id")):
    try:
        cur.execute(f"DELETE FROM {tbl} WHERE {col} NOT IN (SELECT id FROM k_sound_info);")
        print(f"  cleaned {tbl}")
    except sqlite3.Error as e:
        print(f"  ({tbl}: {e})")
con.commit()

total2 = cur.execute("SELECT COUNT(*) FROM k_sound_info;").fetchone()[0]
prog = 0
for (p,) in cur.execute("SELECT path FROM k_sound_info;"):
    if p and "PROGRAMS" in p:
        prog += 1
        break  # just need to know if any remain
print("AFTER k_sound_info total:", total2)
print("AFTER any PROGRAMS remaining:", "yes" if prog else "no")

# reclaim space now that the collation is available in-process
print("VACUUM ...")
try:
    con.execute("VACUUM;")
    print("  VACUUM ok")
except sqlite3.Error as e:
    print("  (VACUUM skipped:", e, ")")
con.commit()
con.close()

# clear stale lock
lk = os.path.join(K8, "lock.lck")
if os.path.exists(lk):
    os.remove(lk); print("removed stale lock")

print("\nROLLBACK (Kontakt closed): cp -av", repr(bak), repr(DB))
