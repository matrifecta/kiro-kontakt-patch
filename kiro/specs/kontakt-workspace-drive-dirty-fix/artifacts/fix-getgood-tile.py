#!/usr/bin/env python3
# fix-getgood-tile.py
#
# Conclusion of the artwork investigation:
#   - A browser tile requires NKS metadata (.nicnt) whose Product Name maps to NI Resources/image/<Name>/.
#   - 11 of 12 blank libs have NO .nicnt (plain user folders) -> never had a tile, nothing to restore.
#   - GetGood Drums is the ONE genuine casualty: it HAS .nicnt (Product 'GGD Modern and Massive') AND its
#     NI Resources/image/GGD Modern and Massive/ dir EXISTS with full MST_artwork.png etc. It stays blank only
#     because its k_content_path row is content_type=3 (it was the F:\ straggler we skipped in the merge).
#     Its live path is now on Z: (wd_black). Flip that one row 3->2 to light up its tile.
#
# Safety: same pattern as apply-tile-merge.py. Kontakt/Reaper closed (checks wineserver). Backs up live db
# (+wal/shm) timestamped. KOMPLETE collation. REINDEX. Only touches rows whose path resolves to the GetGood
# lib (matched by path LIKE, not a blind alias) AND currently type<>2. Integrity check. Prints ROLLBACK.
#
# Usage: python3 fix-getgood-tile.py            # dry-run
#        python3 fix-getgood-tile.py apply

import sqlite3, os, subprocess, tempfile, sys, time, shutil

BASE = "/mnt/workspace/VST Install/Kontakt Portable/UserData/Kontakt 8"
LIVE = f"{BASE}/komplete.db3"
MODE = sys.argv[1] if len(sys.argv) > 1 else "dryrun"
# match the GetGood lib by a distinctive path fragment (works for Z: or any drive-letter form)
PATH_FRAGMENT = "GetGood Drums - Modern and Massive Pack"

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

def running():
    for pat in (["pgrep", "-x", "wineserver"], ["pgrep", "-fi", "Kontakt 8"], ["pgrep", "-x", "reaper"]):
        if subprocess.run(pat, stdout=subprocess.DEVNULL).returncode == 0:
            return True
    return False

if not os.path.exists(LIVE):
    raise SystemExit(f"ABORT: live db missing: {LIVE}")

# show current matching rows (read-only copy)
d = copy(LIVE)
con = sqlite3.connect(d); con.create_collation("KOMPLETE", kompare); c = con.cursor()
try: c.execute("PRAGMA wal_checkpoint(FULL)")
except Exception: pass
rows = c.execute("SELECT id, alias, content_type, path FROM k_content_path WHERE path LIKE ?",
                 (f"%{PATH_FRAGMENT}%",)).fetchall()
con.close(); cleanup(d)

print("=== fix GetGood tile (single-row content_type 3->2) ===")
print(f"  live db: {LIVE}")
print(f"  match path LIKE %{PATH_FRAGMENT}%")
if not rows:
    raise SystemExit("  no matching row found — nothing to do.")
for rid, alias, ct, path in rows:
    print(f"    id={rid}  type={ct}  alias={alias!r}  path={path}")
targets = [r for r in rows if r[2] != 2]
print(f"  rows to flip -> 2: {len(targets)}")

if not targets:
    print("  already type 2 — nothing to change.")
    raise SystemExit(0)

if running():
    print("\n  *** Reaper/Kontakt/wineserver RUNNING — close Reaper and run 'wineserver -k' first. ***")
    if MODE == "apply": raise SystemExit("  ABORT (processes running).")

if MODE != "apply":
    print(f"\nDRY-RUN. Nothing changed. Re-run to apply:\n  python3 {sys.argv[0]} apply")
    raise SystemExit(0)

# backup
stamp = time.strftime("%Y%m%d_%H%M%S")
bk = f"{LIVE}.pre_getgood_{stamp}"
print(f"\n=== 1) backup live -> {bk} ===")
shutil.copy2(LIVE, bk); print(f"  {bk}")
for s in ("-wal", "-shm"):
    if os.path.exists(LIVE + s):
        shutil.copy2(LIVE + s, bk + s); print(f"  {bk+s}")

print("\n=== 2) REINDEX + UPDATE the GetGood row(s) content_type -> 2 ===")
con = sqlite3.connect(LIVE); con.create_collation("KOMPLETE", kompare); c = con.cursor()
try:
    c.execute("REINDEX"); con.commit(); print("  REINDEX: done")
except Exception as e:
    print("  REINDEX err:", e)
c.execute("UPDATE k_content_path SET content_type=2 WHERE path LIKE ? AND content_type<>2",
          (f"%{PATH_FRAGMENT}%",))
con.commit()
print(f"  rows updated: {c.rowcount}")
print("  integrity:", c.execute("PRAGMA integrity_check").fetchone()[0])
print("  type2 (tile) libs now:", c.execute("SELECT COUNT(*) FROM k_content_path WHERE content_type=2").fetchone()[0])
con.close()
for s in ("-wal", "-shm"):
    p = LIVE + s
    if os.path.exists(p):
        os.remove(p); print(f"  removed stale {os.path.basename(p)}")

print(f"\nROLLBACK (Kontakt closed): cp -av \"{bk}\" \"{LIVE}\"; rm -f \"{LIVE}\"-wal \"{LIVE}\"-shm")
print("\nNEXT: launch Reaper, load Kontakt, confirm GetGood now shows its tile. DO NOT rescan.")
