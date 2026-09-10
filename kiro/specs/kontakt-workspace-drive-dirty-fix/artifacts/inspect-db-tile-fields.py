#!/usr/bin/env python3
# inspect-db-tile-fields.py (READ-ONLY)
# The live komplete.db3 is INTACT (Kontakt renders most tiles). A subset of Player libs show folder icons
# despite identical cache/art/path. Read the LIVE db (Kontakt must be closed) and compare the per-library
# row fields between RENDERING libs and BLANK libs to find the differentiating column (e.g. a picture/tile
# blob, a 'has_image'/visibility flag, a content_type, or a NULL where working libs have a value).
#
# Opens the db copied to a temp path first (avoids any FUSE open-state weirdness / stat=0 artifact).
import sqlite3, sys, os, shutil, tempfile

LIVE = "/mnt/workspace/VST Install/Kontakt Portable/UserData/komplete.db3"

def kompare(a,b):
    a=(a or "").strip().casefold(); b=(b or "").strip().casefold()
    return (a>b)-(a<b)

# copy to local tmp so we read a stable snapshot of the live db (also sidesteps the size=0 FUSE artifact)
tmp=tempfile.mktemp(suffix=".db3")
shutil.copy2(LIVE, tmp)
print(f"copied live db -> {tmp}  ({os.path.getsize(tmp)} bytes)")

con=sqlite3.connect(tmp); con.create_collation("KOMPLETE", kompare); cur=con.cursor()

# find the table + name column that holds library rows
tbls=[r[0] for r in cur.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
print("tables:", ", ".join(sorted(tbls)))

# k_content_path likely has one row per library with a name + flags; dump its schema
for t in ("k_content_path",):
    try:
        cols=[c[1] for c in cur.execute(f"PRAGMA table_info({t})").fetchall()]
        print(f"\n{t} columns: {cols}")
    except Exception as e:
        print(f"{t}: {e}")

# Try to locate the name column
name_col=None
for c in ("name","content_path_name","alias","library_name"):
    try:
        cur.execute(f"SELECT {c} FROM k_content_path LIMIT 1"); name_col=c; break
    except Exception: pass
print("name column guess:", name_col)

def rowdump(label, like):
    print(f"\n=== {label}: rows LIKE '%{like}%' ===")
    try:
        cols=[c[1] for c in cur.execute("PRAGMA table_info(k_content_path)").fetchall()]
        q=f"SELECT * FROM k_content_path WHERE " + " OR ".join([f"CAST({c} AS TEXT) LIKE ?" for c in cols])
        rows=cur.execute(q, tuple([f"%{like}%"]*len(cols))).fetchall()
        for r in rows[:3]:
            for cn,val in zip(cols,r):
                v=val
                if isinstance(v,(bytes,bytearray)): v=f"<blob {len(v)} bytes>"
                print(f"    {cn} = {v}")
            print("    ----")
    except Exception as e:
        print("   query err:", e)

# compare a WORKING lib vs a BLANK lib
rowdump("WORKING Amati", "Amati")
rowdump("WORKING Cloud Supply", "Cloud Supply")
rowdump("BLANK Middle East", "Middle East")
rowdump("BLANK Straylight", "Straylight")

con.close(); os.remove(tmp)
print("\nREAD-ONLY (worked on a temp copy; live db untouched). Compare the column values between WORKING")
print("and BLANK rows — the field that differs (blob/flag/type) is what drives the tile.")
