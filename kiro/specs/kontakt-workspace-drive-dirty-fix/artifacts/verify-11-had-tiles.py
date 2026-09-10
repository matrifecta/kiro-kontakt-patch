#!/usr/bin/env python3
# verify-11-had-tiles.py  (READ-ONLY)
#
# The user (rightly) doubts my "these 11 never had a tile" claim. Prove it either way with EVIDENCE, not
# inference. For each of the 11 folder-icon libs, check ACROSS EVERY komplete*.db3 (live + all backups):
#   - was this lib EVER content_type=2 (i.e. it DID render a tile in some prior good state)?
# Also list its content_type in each db and the newest db where it was type 2.
# This is the decisive test: if a lib was type-2 in a real prior db, it rendered a tile and we should restore it.
import sqlite3, os, subprocess, tempfile, glob, time

BASE="/mnt/workspace/VST Install/Kontakt Portable/UserData/Kontakt 8"
UD="/mnt/workspace/VST Install/Kontakt Portable/UserData"

# the 11 folder-icon libs, by a distinctive path/alias fragment each
LIBS = {
 "Doru Malaia":       "Doru Malaia",
 "PlugInGuru MegaMagic":"MegaMagic",
 "SM Classic Guitar": "Classic Guitar Licks",
 "SM EDM Energy":     "EDM Energy Drums",
 "SM Future Cinematic":"Future Cinematic FX",
 "SM Tropical Trap":  "Tropical Trap",
 "String Audio Alchemist":"Alchemist Cinematic Impacts",
 "Audio Imperia Sinfonia":"Sinfonia Drums",
 "Epic SoundLab Forge":"Epic SoundLab - The Forge",
 "Keyscape 13":       "Keyscape - 13",
 "Drumdrops Funk":    "Vintage Funk Kit",
}

def k(a,b):
    a=(a or "").strip().casefold(); b=(b or "").strip().casefold(); return (a>b)-(a<b)

def copy(src):
    d=tempfile.mktemp(suffix=".db3"); subprocess.run(["dd",f"if={src}",f"of={d}","bs=1M"],stderr=subprocess.DEVNULL)
    for s in ("-wal","-shm"):
        if os.path.exists(src+s): subprocess.run(["dd",f"if={src+s}",f"of={d+s}","bs=1M"],stderr=subprocess.DEVNULL)
    return d

# all candidate dbs, newest first
cands=[]
for pat in (f"{BASE}/komplete*.db3*", f"{UD}/**/komplete*.db3*"):
    cands += glob.glob(pat, recursive=True)
cands=[c for c in set(cands) if os.path.isfile(c) and not c.endswith(("-wal","-shm")) and os.path.getsize(c)>1_000_000]
cands.sort(key=lambda p: os.path.getmtime(p), reverse=True)

# ever-type-2 tracker
ever2={name:[] for name in LIBS}

print(f"Scanning {len(cands)} komplete*.db3 candidates for the 11 libs' content_type history\n")
hdr = "DB (mtime)".ljust(20) + "  " + "  ".join(n[:10].ljust(10) for n in LIBS)
for src in cands:
    mt=time.strftime('%m-%d %H:%M', time.localtime(os.path.getmtime(src)))
    d=copy(src)
    row_types={}
    try:
        con=sqlite3.connect(d); con.create_collation("KOMPLETE",k); c=con.cursor()
        try: c.execute("PRAGMA wal_checkpoint(FULL)")
        except Exception: pass
        for name,frag in LIBS.items():
            r=c.execute("SELECT content_type FROM k_content_path WHERE path LIKE ? OR alias LIKE ? LIMIT 1",
                        (f"%{frag}%",f"%{frag}%")).fetchone()
            ct = r[0] if r else None
            row_types[name]=ct
            if ct==2: ever2[name].append((mt, os.path.basename(src)))
        con.close()
    except Exception as e:
        for name in LIBS: row_types[name]="ERR"
    finally:
        for p in (d,d+"-wal",d+"-shm"):
            try: os.remove(p)
            except OSError: pass
    line = (mt+"  "+os.path.basename(src))[:20].ljust(20) + "  " + "  ".join(
        (("t"+str(row_types[n])) if row_types[n] is not None else "  -").ljust(10) for n in LIBS)
    print(line)

print("\n=== VERDICT per lib (was it EVER content_type=2 in any db?) ===")
any_ever=False
for name in LIBS:
    if ever2[name]:
        any_ever=True
        newest=ever2[name][0]
        print(f"  YES  {name:24s} was type-2 in {len(ever2[name])} db(s); newest: {newest[0]} {newest[1]}")
    else:
        print(f"  no   {name:24s} never type-2 in any db scanned")
print()
if any_ever:
    print("At least one lib WAS type-2 before => it DID render a tile; my 'never had a tile' claim was WRONG")
    print("for those. Fix = flip those libs' content_type 3->2 in the live db (same as the merge).")
else:
    print("No lib was ever type-2 in any db on disk => none rendered a tile in any preserved state.")
print("READ-ONLY: nothing changed.")
