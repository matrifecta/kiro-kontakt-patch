#!/usr/bin/env python3
"""
db-repoint-factory-content.py

The only non-Z rows left are Kontakt 8 Portable's OWN factory content, which Kontakt
re-registers on every launch (stable at exactly these 4, not churn):
  D:\VST Install\Kontakt Portable\Kontakt 8\Content\Presets\Lo-Fi Vibes
  D:\VST Install\Kontakt Portable\Kontakt 8\Content\Presets\Piano Uno
  D:\VST Install\Kontakt Portable\Kontakt 8\Content\Tools\Chords
  D:\VST Install\Kontakt Portable\Kontakt 8\Content\Tools\Phrases

They resolve fine (D: -> /mnt/workspace), but to keep the DB strictly Z:-only we
repoint them to the identical Z:\mnt\workspace\... path. Done via Python with the
KOMPLETE collation registered + REINDEX first, so the write can't throw
'database disk image is malformed' on the p_sound_info_* indexes.

Kontakt CLOSED. Backup first. Reversible.

Usage:
  python3 db-repoint-factory-content.py            # dry-run
  python3 db-repoint-factory-content.py apply
"""
import sqlite3, sys, os, shutil, time

K8 = "/mnt/workspace/VST Install/Kontakt Portable/UserData/Kontakt 8"
DB = os.path.join(K8, "komplete.db3")
MODE = sys.argv[1] if len(sys.argv) > 1 else "dryrun"

PAIRS = [
 (r"D:\VST Install\Kontakt Portable\Kontakt 8\Content\Presets\Lo-Fi Vibes",
  r"Z:\mnt\workspace\VST Install\Kontakt Portable\Kontakt 8\Content\Presets\Lo-Fi Vibes"),
 (r"D:\VST Install\Kontakt Portable\Kontakt 8\Content\Presets\Piano Uno",
  r"Z:\mnt\workspace\VST Install\Kontakt Portable\Kontakt 8\Content\Presets\Piano Uno"),
 (r"D:\VST Install\Kontakt Portable\Kontakt 8\Content\Tools\Chords",
  r"Z:\mnt\workspace\VST Install\Kontakt Portable\Kontakt 8\Content\Tools\Chords"),
 (r"D:\VST Install\Kontakt Portable\Kontakt 8\Content\Tools\Phrases",
  r"Z:\mnt\workspace\VST Install\Kontakt Portable\Kontakt 8\Content\Tools\Phrases"),
]

def kompare(a, b):
    x=(a or "").strip().casefold(); y=(b or "").strip().casefold(); return (x>y)-(x<y)

def con_of(path, ro=False):
    c = sqlite3.connect(f"file:{path}?mode=ro", uri=True) if ro else sqlite3.connect(path)
    c.create_collation("KOMPLETE", kompare); return c

c = con_of(DB, ro=True); cur = c.cursor()
print("current non-Z rows:")
for r in cur.execute("SELECT id,content_type,visible,path FROM k_content_path;"):
    if not str(r[3]).startswith("Z:"):
        print("  ", r)
c.close()

if MODE != "apply":
    print("\nDRY-RUN. These 4 would be repointed D: -> Z:. Re-run with:  python3", sys.argv[0], "apply")
    sys.exit(0)

if os.system("pgrep -fi 'Kontakt 8.exe' >/dev/null") == 0:
    print("ABORT: Kontakt running. File->Exit first."); sys.exit(1)

stamp = time.strftime("%Y%m%d_%H%M%S")
bak = f"{DB}.pre_factoryrepoint_{stamp}"
shutil.copy2(DB, bak); print("backup:", bak)

c = con_of(DB); cur = c.cursor()
print("REINDEX ...")
cur.execute("REINDEX;"); c.commit()
bad = sum(1 for r in cur.execute("PRAGMA integrity_check;") if r[0] != "ok")
if bad:
    print("integrity not ok after reindex; aborting"); c.close(); sys.exit(1)
print("integrity: ok")

for dpath, zpath in PAIRS:
    cur.execute("UPDATE k_content_path SET path=? WHERE path=?;", (zpath, dpath))
    print("  repointed:", dpath.split("\\")[-1])
c.commit()

left = sum(1 for r in cur.execute("SELECT path FROM k_content_path;") if not str(r[0]).startswith("Z:"))
total = cur.execute("SELECT COUNT(*) FROM k_content_path;").fetchone()[0]
print(f"non-Z rows left: {left}   total: {total}")
print("final integrity:", "ok" if sum(1 for r in cur.execute('PRAGMA integrity_check;') if r[0]!='ok')==0 else "ISSUES")
c.execute("VACUUM;"); c.commit(); c.close()

lk = os.path.join(K8, "lock.lck")
if os.path.exists(lk): os.remove(lk)
print("\nROLLBACK (Kontakt closed): cp -av", repr(bak), repr(DB))
