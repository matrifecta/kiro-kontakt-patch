#!/usr/bin/env python3
# delete-stale-pg-soundinfo.py
#
# Remove ONLY the stale OLD-dotted PlugInGuru sound-info rows that feed the ghost browser tile, keeping the
# NEW clean set the per-entry Rescan created. Confirmed duplicates under content_path_id=247:
#   k_sound_info: 400 old-dotted (file_name LIKE old) + 405 new-clean  -> delete the 400 old
#   k_bank_chain: 9 old (entry1 LIKE old, ids 928..936) + 9 new        -> delete the 9 old
#   f_sound_info / p_sound_info_* : shadow/search rows carrying the old dotted product/entry -> delete old
#
# Strategy: gather the OLD k_sound_info ids + OLD bank_chain ids first, then delete matching rows from every
# sound-info table by those ids / by the old dotted string. Kontakt/Reaper CLOSED. Backup first. KOMPLETE
# collation. REINDEX + integrity after. Prints counts + rollback.
#
# Usage: python3 delete-stale-pg-soundinfo.py            # dry-run (counts only)
#        python3 delete-stale-pg-soundinfo.py apply
import sqlite3, os, subprocess, sys, time, shutil

LIVE="/mnt/workspace/VST Install/Kontakt Portable/UserData/Kontakt 8/komplete.db3"
OLD=r"PlugInGuru.MegaMagic.Bells.Winds.KONTAKT"
NEW="PlugInGuru MegaMagic Bells Winds"
MODE=sys.argv[1] if len(sys.argv)>1 else "dryrun"

def k(a,b):
    a=(a or "").strip().casefold(); b=(b or "").strip().casefold(); return (a>b)-(a<b)
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

# discover which tables carry the old dotted string, and in which columns
tables=[r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table'")]
plan={}   # table -> list of (col) that match old
for t in tables:
    try: cols=[r[1] for r in c.execute(f"PRAGMA table_info('{t}')")]
    except Exception: continue
    hitcols=[]
    for col in cols:
        try:
            n=c.execute(f'SELECT COUNT(*) FROM "{t}" WHERE CAST("{col}" AS TEXT) LIKE ?',(f"%{OLD}%",)).fetchone()[0]
            if n>0: hitcols.append((col,n))
        except Exception: pass
    if hitcols: plan[t]=hitcols

print("Tables/columns holding the OLD dotted string (rows to delete):")
for t,hc in plan.items():
    # rows in this table matching old in ANY column
    conds=" OR ".join(f'CAST("{col}" AS TEXT) LIKE ?' for col,_ in hc)
    n=c.execute(f'SELECT COUNT(*) FROM "{t}" WHERE {conds}',tuple(f"%{OLD}%" for _ in hc)).fetchone()[0]
    print(f"  {t}: {n} row(s)  (cols: {[col for col,_ in hc]})")

# safety: confirm the NEW clean set still exists so we don't nuke everything
new_si=c.execute("SELECT COUNT(*) FROM k_sound_info WHERE file_name LIKE ? AND file_name NOT LIKE ?",
                 (f"%{NEW}%",f"%{OLD}%")).fetchone()[0]
print(f"\nSafety check — NEW clean k_sound_info rows that will REMAIN: {new_si}")
if new_si==0:
    print("ABORT: no clean rows found; deleting old would remove the library entirely."); con.close(); raise SystemExit(1)

if MODE!="apply":
    con.close()
    print(f"\nDRY-RUN. Re-run: python3 {sys.argv[0]} apply")
    raise SystemExit(0)

con.close()
# backup
stamp=time.strftime("%Y%m%d_%H%M%S"); bk=f"{LIVE}.pre_pgdedup_{stamp}"
shutil.copy2(LIVE,bk); print(f"\nbackup: {bk}")
for s in ("-wal","-shm"):
    if os.path.exists(LIVE+s): shutil.copy2(LIVE+s,bk+s)

con=sqlite3.connect(LIVE); con.create_collation("KOMPLETE",k); c=con.cursor()
try: c.execute("REINDEX"); con.commit(); print("REINDEX(before): done")
except Exception as e: print("REINDEX err:",e)

total=0
for t,hc in plan.items():
    conds=" OR ".join(f'CAST("{col}" AS TEXT) LIKE ?' for col,_ in hc)
    try:
        c.execute(f'DELETE FROM "{t}" WHERE {conds}',tuple(f"%{OLD}%" for _ in hc))
        print(f"  deleted from {t}: {c.rowcount}")
        total+=c.rowcount
    except Exception as e:
        print(f"  {t}: DELETE err {e}")
con.commit()
print(f"total rows deleted: {total}")

try: c.execute("REINDEX"); con.commit(); print("REINDEX(after): done")
except Exception as e: print("REINDEX err:",e)
print("integrity:", c.execute("PRAGMA integrity_check").fetchone()[0])
# verify: old gone, new intact
oldleft=c.execute("SELECT COUNT(*) FROM k_sound_info WHERE file_name LIKE ?",(f"%{OLD}%",)).fetchone()[0]
newleft=c.execute("SELECT COUNT(*) FROM k_sound_info WHERE file_name LIKE ? AND file_name NOT LIKE ?",(f"%{NEW}%",f"%{OLD}%")).fetchone()[0]
print(f"k_sound_info old-dotted remaining: {oldleft}  (want 0)")
print(f"k_sound_info new-clean remaining:  {newleft}  (want ~405)")
con.close()
for s in ("-wal","-shm"):
    p=LIVE+s
    if os.path.exists(p): os.remove(p)
print(f"\nROLLBACK (Kontakt closed): cp -av \"{bk}\" \"{LIVE}\"; rm -f \"{LIVE}\"-wal \"{LIVE}\"-shm")
print("NEXT: launch Reaper, load Kontakt. The stale blank PlugInGuru tile should be gone, leaving only the")
print("working 'PlugInGuru MegaMagic Bells Winds' tile. DO NOT rescan.")
