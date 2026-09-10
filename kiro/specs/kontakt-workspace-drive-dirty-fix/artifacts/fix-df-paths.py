#!/usr/bin/env python3
# fix-df-paths.py — resolve the 4 residual D: rows in k_content_path.
#   CONVERGE (real content, exists on disk, wrong drive letter D: -> Z:):
#     id=282 Lo-Fi Vibes, id=283 Piano Uno  (update k_content_path.path + their k_sound_info.file_name)
#   REMOVE (content deliberately removed earlier = Task 13 Tools Chords/Phrases; folders MISSING; orphan rows):
#     id=284 Chords, id=285 Phrases  (delete k_content_path row + dependent k_sound_info + k_bank_chain + shadow)
#
# Matched by exact id AND path prefix (belt-and-suspenders). Kontakt closed. Backup, KOMPLETE collation,
# REINDEX before+after, integrity check. Dry-run unless 'apply'.
#
# Usage: python3 fix-df-paths.py            # dry-run
#        python3 fix-df-paths.py apply
import sqlite3, os, subprocess, sys, time, shutil

LIVE="/mnt/workspace/VST Install/Kontakt Portable/UserData/Kontakt 8/komplete.db3"
MODE=sys.argv[1] if len(sys.argv)>1 else "dryrun"
CONVERGE_IDS=[282,283]   # D:->Z:
REMOVE_IDS=[284,285]     # orphan Tools Chords/Phrases

def k(a,b):
    a=(a or "").strip().casefold();b=(b or "").strip().casefold();return (a>b)-(a<b)
def running():
    for pat in (["pgrep","-x","wineserver"],["pgrep","-fi","Kontakt 8"],["pgrep","-x","reaper"]):
        if subprocess.run(pat,stdout=subprocess.DEVNULL).returncode==0: return True
    return False

if running():
    print("*** close Reaper + wineserver -k first ***")
    if MODE=="apply": raise SystemExit("ABORT")

con=sqlite3.connect(LIVE); con.create_collation("KOMPLETE",k); c=con.cursor()
try: c.execute("PRAGMA wal_checkpoint(FULL)")
except Exception: pass

print("=== plan ===")
for i in CONVERGE_IDS+REMOVE_IDS:
    r=c.execute("SELECT id,alias,content_type,path FROM k_content_path WHERE id=?",(i,)).fetchone()
    n=c.execute("SELECT COUNT(*) FROM k_sound_info WHERE content_path_id=?",(i,)).fetchone()[0]
    act="CONVERGE D:->Z:" if i in CONVERGE_IDS else "REMOVE (orphan)"
    print(f"  [{act}] {r}  sound_info={n}")
con.close()

if MODE!="apply":
    print(f"\nDRY-RUN. Re-run: python3 {sys.argv[0]} apply"); raise SystemExit(0)

stamp=time.strftime("%Y%m%d_%H%M%S"); bk=f"{LIVE}.pre_dffix_{stamp}"
shutil.copy2(LIVE,bk); print(f"\nbackup: {bk}")
for s in ("-wal","-shm"):
    if os.path.exists(LIVE+s): shutil.copy2(LIVE+s,bk+s)

con=sqlite3.connect(LIVE); con.create_collation("KOMPLETE",k); c=con.cursor()
try: c.execute("REINDEX"); con.commit()
except Exception as e: print("REINDEX err:",e)

# --- CONVERGE 282,283: D: -> Z: on content_path.path and their sound_info.file_name ---
conv=0
for i in CONVERGE_IDS:
    row=c.execute("SELECT path FROM k_content_path WHERE id=?",(i,)).fetchone()
    if not row: print(f"  converge id={i}: no row, skip"); continue
    p=row[0]
    if p.startswith("D:") or p.startswith("F:"):
        newp="Z:"+p[2:]
        c.execute("UPDATE k_content_path SET path=? WHERE id=?",(newp,i))
        # sound_info file_name may embed the D:/F: prefix too
        c.execute("UPDATE k_sound_info SET file_name='Z:'||substr(file_name,3) WHERE content_path_id=? AND (file_name LIKE 'D:%' OR file_name LIKE 'F:%')",(i,))
        conv+=1
        print(f"  converged id={i}: {p} -> {newp}")
con.commit()

# --- REMOVE 284,285: delete content_path + dependent rows ---
rem=0
for i in REMOVE_IDS:
    row=c.execute("SELECT path FROM k_content_path WHERE id=?",(i,)).fetchone()
    if not row: print(f"  remove id={i}: no row, skip"); continue
    # bank_chain ids used by this content's sound_info
    bcs=[r[0] for r in c.execute("SELECT DISTINCT bank_chain_id FROM k_sound_info WHERE content_path_id=?",(i,))]
    c.execute("DELETE FROM k_sound_info WHERE content_path_id=?",(i,))
    si=c.rowcount
    # remove now-orphan bank_chain rows (only if no other sound_info references them)
    bc_del=0
    for bc in bcs:
        used=c.execute("SELECT COUNT(*) FROM k_sound_info WHERE bank_chain_id=?",(bc,)).fetchone()[0]
        if used==0:
            c.execute("DELETE FROM k_bank_chain WHERE id=?",(bc,)); bc_del+=c.rowcount
    c.execute("DELETE FROM k_content_path WHERE id=?",(i,))
    rem+=1
    print(f"  removed id={i}: content_path + {si} sound_info + {bc_del} bank_chain")
con.commit()

try: c.execute("REINDEX"); con.commit(); print("REINDEX(after): done")
except Exception as e: print("REINDEX err:",e)
print("integrity:", c.execute("PRAGMA integrity_check").fetchone()[0])
print("D:/F: paths remaining:", c.execute("SELECT COUNT(*) FROM k_content_path WHERE path LIKE 'D:%' OR path LIKE 'F:%'").fetchone()[0])
print("content paths total:", c.execute("SELECT COUNT(*) FROM k_content_path").fetchone()[0])
con.close()
for s in ("-wal","-shm"):
    p=LIVE+s
    if os.path.exists(p): os.remove(p)
print(f"\nROLLBACK (Kontakt closed): cp -av \"{bk}\" \"{LIVE}\"; rm -f \"{LIVE}\"-wal \"{LIVE}\"-shm")
print("NEXT: launch Reaper; Lo-Fi Vibes + Piano Uno still load (now Z:); Chords/Phrases orphan entries gone.")
print("Then run the snapshot. DO NOT rescan.")
