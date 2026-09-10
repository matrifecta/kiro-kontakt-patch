#!/usr/bin/env python3
# probe-custom-tile-link.py  (READ-ONLY on a copy)
#
# The 12 blank libs are all content_type=3 (Custom). Custom libs get their browser tile from artwork the
# vendor shipped inside the library folder. Some Custom libs in the browser DO render a tile; these 12 don't.
# GOAL: find HOW Kontakt links a Custom lib's tile so we can fix the blanks the same way.
#
# We inspect the full k_content_path row (all columns) + any related tables (k_sound_info, images/thumbnail
# tables) for a Custom lib that RENDERS vs one that's BLANK, to see which column/field carries the picture
# reference (a path, a blob, a picture id, etc.). Read-only via dd copy + KOMPLETE collation.
import sqlite3, os, subprocess, tempfile

BASE="/mnt/workspace/VST Install/Kontakt Portable/UserData/Kontakt 8"
LIVE=f"{BASE}/komplete.db3"

# fuzzy terms: some Custom libs that RENDER (from the screenshot) vs the BLANK ones
RENDER=["Electro Acoustic","Electric S","Session Keys Electric","Sonic Mechani"]  # will show what matches
BLANK =["Doru Malaia","MegaMagic","Sonic Mechanics - Tropical","Alchemist","Sinfonia","Keyscape"]

def k(a,b):
    a=(a or "").strip().casefold(); b=(b or "").strip().casefold(); return (a>b)-(a<b)

def copy(src):
    d=tempfile.mktemp(suffix=".db3"); subprocess.run(["dd",f"if={src}",f"of={d}","bs=1M"],stderr=subprocess.DEVNULL)
    for s in ("-wal","-shm"):
        if os.path.exists(src+s): subprocess.run(["dd",f"if={src+s}",f"of={d+s}","bs=1M"],stderr=subprocess.DEVNULL)
    return d

d=copy(LIVE)
con=sqlite3.connect(d); con.create_collation("KOMPLETE",k); c=con.cursor()
try: c.execute("PRAGMA wal_checkpoint(FULL)")
except Exception: pass

# list all tables + any that look image/picture/thumbnail related
tbls=[r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table'")]
print("tables:", ", ".join(tbls))
imgish=[t for t in tbls if any(w in t.lower() for w in ("image","picture","thumb","icon","art","resource","product"))]
print("image-ish tables:", imgish or "(none)")
print()

cp_cols=[r[1] for r in c.execute("PRAGMA table_info(k_content_path)")]
print("k_content_path cols:", cp_cols)
print()

def dump(term, tag):
    rows=c.execute("SELECT * FROM k_content_path WHERE alias LIKE ? OR path LIKE ?",(f"%{term}%",f"%{term}%")).fetchall()
    if not rows:
        print(f"[{tag}] {term!r}: no match"); return
    for r in rows[:2]:
        d_=dict(zip(cp_cols,r))
        print(f"[{tag}] alias={d_.get('alias')!r} type={d_.get('content_type')} id={d_.get('id')}")
        for cn,v in d_.items():
            if cn in ("alias","content_type","id","path"): continue
            if isinstance(v,(bytes,bytearray)): v=f"<blob {len(v)}B>"
            print(f"        {cn} = {v}")
        print(f"        path = {d_.get('path')}")
        # look for the id in image-ish tables
        for t in imgish:
            cols=[x[1] for x in c.execute(f"PRAGMA table_info({t})")]
            # try any column that references content path id
            for key in ("content_path_id","path_id","content_id","id"):
                if key in cols:
                    try:
                        hit=c.execute(f"SELECT * FROM {t} WHERE {key}=?",(d_.get('id'),)).fetchall()
                        if hit:
                            print(f"        -> {t}.{key} match: {len(hit)} row(s)")
                            for h in hit[:1]:
                                for hcn,hv in zip(cols,h):
                                    if isinstance(hv,(bytes,bytearray)): hv=f"<blob {len(hv)}B>"
                                    print(f"             {hcn} = {hv}")
                    except Exception as e:
                        pass
        print()

print("===== CUSTOM libs that RENDER (reference) =====")
for t in RENDER: dump(t,"RENDER")
print("===== CUSTOM libs that are BLANK =====")
for t in BLANK: dump(t,"BLANK")

con.close()
for p in (d,d+"-wal",d+"-shm"):
    try: os.remove(p)
    except OSError: pass
print("READ-ONLY. Compare the non-path columns (and any image-ish table rows) between a RENDER and a BLANK")
print("custom lib — the differing field is what links the tile picture.")
