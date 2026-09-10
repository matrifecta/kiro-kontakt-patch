#!/usr/bin/env python3
# apply-tile-merge.py
#
# Non-destructive in-place tile fix on the LIVE komplete.db3 (78MB, clean Z: paths, tiles blank).
# It does NOT restore any old backup. It flips ONLY the promotion-set aliases' content_type 3->2
# (the 45 libs that plan-tile-merge.py proved are tiles in the pre_ewqlra reference but folder-icon
# in live). This keeps every current path (incl. the clean Z: paths) and brings the artwork tiles back.
#
# Promotion set = aliases that are content_type=2 in the pre_ewqlra backup AND present-but-non-tile in live,
# computed live at run time (not hard-coded) so it always matches the current dbs.
#
# Safety: Kontakt/Reaper MUST be closed (checks wineserver). Backs up live db (+wal/shm) first, timestamped.
# Uses Python sqlite3 with the KOMPLETE collation registered. REINDEX before writes (both dbs carry a stale
# p_sound_info sort index). Integrity check after. Prints ROLLBACK command. Dry-run unless 'apply' given.
#
# Usage: python3 apply-tile-merge.py           # dry-run: shows exactly what WOULD change
#        python3 apply-tile-merge.py apply

import sqlite3, os, subprocess, tempfile, sys, time, shutil

BASE = "/mnt/workspace/VST Install/Kontakt Portable/UserData/Kontakt 8"
LIVE = f"{BASE}/komplete.db3"
REF  = f"{BASE}/komplete.db3.pre_ewqlra_144329"   # tile reference (type-2 set), NOT restored
MODE = sys.argv[1] if len(sys.argv) > 1 else "dryrun"

def kompare(a, b):
    a = (a or "").strip().casefold(); b = (b or "").strip().casefold()
    return (a > b) - (a < b)

def copy(src):
    d = tempfile.mktemp(suffix=".db3")
    subprocess.run(["dd", f"if={src}", f"of={d}", "bs=1M"], stderr=subprocess.DEVNULL)
    for s in ("-wal", "-shm"):
        if os.path.exists(src + s):
            subprocess.run(["dd", f"if={src+s}", f"of={d+s}", "bs=1M"], stderr=subprocess.DEVNULL)
    return d

def cleanup(d):
    for p in (d, d + "-wal", d + "-shm"):
        try: os.remove(p)
        except OSError: pass

# ---- safety: Kontakt/Reaper/wineserver must be closed (we write the live db) ----
def running():
    for pat in (["pgrep", "-x", "wineserver"], ["pgrep", "-fi", "Kontakt 8"], ["pgrep", "-x", "reaper"]):
        if subprocess.run(pat, stdout=subprocess.DEVNULL).returncode == 0:
            return True
    return False

if not os.path.exists(LIVE): raise SystemExit(f"ABORT: live db missing: {LIVE}")
if not os.path.exists(REF):  raise SystemExit(f"ABORT: reference db missing: {REF}")

# ---- compute promotion set from copies (read-only) ----
def type2_aliases(src):
    d = copy(src)
    try:
        con = sqlite3.connect(d); con.create_collation("KOMPLETE", kompare); c = con.cursor()
        try: c.execute("PRAGMA wal_checkpoint(FULL)")
        except Exception: pass
        s = {r[0] for r in c.execute("SELECT alias FROM k_content_path WHERE content_type=2")}
        con.close(); return s
    finally:
        cleanup(d)

def live_alias_types(src):
    d = copy(src)
    try:
        con = sqlite3.connect(d); con.create_collation("KOMPLETE", kompare); c = con.cursor()
        try: c.execute("PRAGMA wal_checkpoint(FULL)")
        except Exception: pass
        m = {}
        for alias, ct, path in c.execute("SELECT alias, content_type, path FROM k_content_path"):
            m.setdefault(alias, []).append((ct, path))
        con.close(); return m
    finally:
        cleanup(d)

ref_t2 = type2_aliases(REF)
live_m = live_alias_types(LIVE)
promote = sorted(a for a in ref_t2 if a in live_m and all(ct != 2 for ct, _ in live_m[a]))

print("=== tile merge (in-place 3->2 on LIVE, no restore) ===")
print(f"  live db: {LIVE}")
print(f"  tile reference (not restored): {REF}")
print(f"  promotion set: {len(promote)} aliases will be set content_type -> 2")
for a in promote:
    print(f"     {a:34s} {live_m[a][0][1]}")
absent = sorted(a for a in ref_t2 if a not in live_m)
if absent:
    print(f"  (skipping {len(absent)} tile alias(es) absent from live — correctly not re-added): {', '.join(absent)}")

if running():
    print("\n  *** Reaper/Kontakt/wineserver RUNNING — close Reaper and run 'wineserver -k' first. ***")
    if MODE == "apply": raise SystemExit("  ABORT (processes running).")

if MODE != "apply":
    print(f"\nDRY-RUN. Nothing changed. Re-run to apply:\n  python3 {sys.argv[0]} apply")
    raise SystemExit(0)

# ---- backup live (+wal/shm) ----
stamp = time.strftime("%Y%m%d_%H%M%S")
bk = f"{LIVE}.pre_tilemerge_{stamp}"
print(f"\n=== 1) backup live -> {bk} ===")
shutil.copy2(LIVE, bk); print(f"  {bk}")
for s in ("-wal", "-shm"):
    if os.path.exists(LIVE + s):
        shutil.copy2(LIVE + s, bk + s); print(f"  {bk+s}")

# ---- write in-place: REINDEX, then UPDATE content_type for promotion set ----
print("\n=== 2) REINDEX + UPDATE content_type 3->2 (KOMPLETE collation) ===")
con = sqlite3.connect(LIVE); con.create_collation("KOMPLETE", kompare); c = con.cursor()
try:
    c.execute("REINDEX"); con.commit(); print("  REINDEX: done")
except Exception as e:
    print("  REINDEX err:", e)

changed = 0
for a in promote:
    c.execute("UPDATE k_content_path SET content_type=2 WHERE alias=? AND content_type<>2", (a,))
    changed += c.rowcount
con.commit()
print(f"  rows updated: {changed}")

print("  integrity:", c.execute("PRAGMA integrity_check").fetchone()[0])
print("  content paths:", c.execute("SELECT COUNT(*) FROM k_content_path").fetchone()[0])
print("  type2 (tile) libs now:", c.execute("SELECT COUNT(*) FROM k_content_path WHERE content_type=2").fetchone()[0])
print("  still on D:/F::", c.execute("SELECT COUNT(*) FROM k_content_path WHERE path LIKE 'D:%' OR path LIKE 'F:%'").fetchone()[0])
con.close()

# clear any stale wal/shm so Kontakt opens the merged db cleanly
for s in ("-wal", "-shm"):
    p = LIVE + s
    if os.path.exists(p):
        os.remove(p); print(f"  removed stale {os.path.basename(p)}")

print(f"\nROLLBACK (Kontakt closed): cp -av \"{bk}\" \"{LIVE}\"; rm -f \"{LIVE}\"-wal \"{LIVE}\"-shm")
print("\nNEXT: launch Reaper (QT_QPA_PLATFORM=xcb reaper), load Kontakt, confirm tiles render + Import")
print("Content shows Z: paths. DO NOT run Import/Rescan or 'Reset Multi' (that re-demotes 2->3).")
