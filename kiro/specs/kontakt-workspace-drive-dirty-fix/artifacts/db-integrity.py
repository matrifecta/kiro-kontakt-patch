#!/usr/bin/env python3
# Check integrity of komplete.db3 with the KOMPLETE collation registered,
# so the check actually runs instead of aborting. READ-ONLY.
import sqlite3, sys, os

K8 = "/mnt/workspace/VST Install/Kontakt Portable/UserData/Kontakt 8"
target = sys.argv[1] if len(sys.argv) > 1 else os.path.join(K8, "komplete.db3")

def kompare(a, b):
    x = (a or "").strip().casefold(); y = (b or "").strip().casefold()
    return (x > y) - (x < y)

print("checking:", target)
con = sqlite3.connect(f"file:{target}?mode=ro", uri=True)
con.create_collation("KOMPLETE", kompare)
cur = con.cursor()
try:
    for row in cur.execute("PRAGMA integrity_check;"):
        print("  integrity:", row[0])
except sqlite3.Error as e:
    print("  integrity_check error:", e)
try:
    cp = cur.execute("SELECT COUNT(*) FROM k_content_path;").fetchone()[0]
    si = cur.execute("SELECT COUNT(*) FROM k_sound_info;").fetchone()[0]
    print(f"  k_content_path={cp}  k_sound_info={si}")
except sqlite3.Error as e:
    print("  count error:", e)
con.close()
