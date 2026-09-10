#!/usr/bin/env python3
# probe-pg-soundinfo-dupes.py (READ-ONLY on a copy)
# The ghost tile is fed by sound-info rows still carrying the OLD dotted path/name. The per-entry Rescan added
# NEW clean rows too. Confirm there are TWO sets (old dotted vs new clean) and count each, per table, so a
# targeted delete removes ONLY the stale dotted rows. Also list the table schemas + which tables are FTS/shadow
# (f_sound_info*, p_sound_info_*) so the apply script deletes safely via the right keys.
import sqlite3, os, subprocess, tempfile

LIVE="/mnt/workspace/VST Install/Kontakt Portable/UserData/Kontakt 8/komplete.db3"
OLD=r"PlugInGuru.MegaMagic.Bells.Winds.KONTAKT"
NEW="PlugInGuru MegaMagic Bells Winds"

def k(a,b):
    a=(a or "").strip().casefold(); b=(b or "").strip().casefold(); return (a>b)-(a<b)
def copy(src):
    d=tempfile.mktemp(suffix=".db3"); subprocess.run(["dd",f"if={src}",f"of={d}","bs=1M"],stderr=subprocess.DEVNULL)
    for s in ("-wal","-shm"):
        if os.path.exists(src+s): subprocess.run(["dd",f"if={src+s}",f"of={d+s}","bs=1M"],stderr=subprocess.DEVNULL)
    return d

d=copy(LIVE); con=sqlite3.connect(d); con.create_collation("KOMPLETE",k); c=con.cursor()
try: c.execute("PRAGMA wal_checkpoint(FULL)")
except Exception: pass

print("=== k_content_path rows for PlugInGuru (should be ONE clean row) ===")
for r in c.execute("SELECT id,alias,path FROM k_content_path WHERE path LIKE '%MegaMagic%' OR alias LIKE '%MegaMagic%'"):
    print("  ",r)

print("\n=== k_sound_info: old-dotted vs new-clean counts (by file_name) ===")
old=c.execute("SELECT COUNT(*) FROM k_sound_info WHERE file_name LIKE ?",(f"%{OLD}%",)).fetchone()[0]
new=c.execute("SELECT COUNT(*) FROM k_sound_info WHERE file_name LIKE ? AND file_name NOT LIKE ?",
              (f"%{NEW}%",f"%{OLD}%")).fetchone()[0]
tot=c.execute("SELECT COUNT(*) FROM k_sound_info WHERE content_path_id=247").fetchone()[0]
print(f"  old-dotted file_name: {old}")
print(f"  new-clean  file_name: {new}")
print(f"  rows with content_path_id=247 (the live row): {tot}")
# distinct file_name roots
print("  sample old file_name:", (c.execute("SELECT file_name FROM k_sound_info WHERE file_name LIKE ? LIMIT 1",(f"%{OLD}%",)).fetchone() or [None])[0])
print("  sample new file_name:", (c.execute("SELECT file_name FROM k_sound_info WHERE file_name LIKE ? AND file_name NOT LIKE ? LIMIT 1",(f"%{NEW}%",f"%{OLD}%")).fetchone() or [None])[0])

print("\n=== k_bank_chain rows referencing old dotted vs new ===")
print("  old:", c.execute("SELECT COUNT(*) FROM k_bank_chain WHERE entry1 LIKE ?",(f"%{OLD}%",)).fetchone()[0])
print("  new:", c.execute("SELECT COUNT(*) FROM k_bank_chain WHERE entry1=?",(NEW,)).fetchone()[0])
print("  bank_chain_ids (old):", [r[0] for r in c.execute("SELECT id FROM k_bank_chain WHERE entry1 LIKE ?",(f"%{OLD}%",))][:20])

print("\n=== tables that matched earlier + their type (table vs virtual/shadow) ===")
for name,typ,sql in c.execute("SELECT name,type,sql FROM sqlite_master WHERE name IN ('k_sound_info','k_bank_chain','f_sound_info','p_sound_info_Instrument_2','p_sound_info_Oneshot_2')"):
    kind="VIRTUAL/FTS" if (sql and 'USING' in sql.upper()) else "table"
    print(f"  {name}: {kind}")
    print(f"     cols: {[r[1] for r in c.execute(f'PRAGMA table_info({name})')]}")

con.close()
for x in (d,d+"-wal",d+"-shm"):
    try: os.remove(x)
    except OSError: pass
print("\nREAD-ONLY. If old>0 AND new>0 there are duplicate sound-info sets; the fix = delete ONLY the old-dotted")
print("rows (k_sound_info by file_name LIKE old; k_bank_chain by entry1 LIKE old; dependent p_/f_ shadow tables")
print("follow via their bank_chain_id / rowid). If new==0, the Rescan did NOT add clean rows -> different fix.")
