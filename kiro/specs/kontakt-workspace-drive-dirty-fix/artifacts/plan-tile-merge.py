#!/usr/bin/env python3
# plan-tile-merge.py  (READ-ONLY — analyses copies, writes nothing)
#
# Situation NOW (user already rolled back the wrong restore):
#   LIVE = the 78MB clean-Z-paths db (type-3 / blank tiles)                                  [good paths, bad tiles]
#   komplete.db3.pre_ewqlra_144329 = 42MB backup (type-2 tiles, BUT stale D:\ / F:\ paths)   [good tiles, bad paths]
#
# GOAL of this probe (answers the user's questions before we touch anything):
#   1) Confirm which db has clean Z: paths and which has the type-2 tiles.
#   2) Find aliases that are type-2 (tile) in the TILES db  -> the set we must promote in the PATHS db.
#   3) Find content paths that exist ONLY in the PATHS (78MB) db and NOT in the TILES (42MB) db
#      = libraries ADDED since the old backup that a wholesale restore of pre_ewqlra would LOSE.
#      (This is the user's "check what was added to the db, maybe we need to preserve some".)
#   4) Flag any type-2/tile alias whose path points at D:\ or F:\ (stale) vs Z:\ (clean).
#
# Everything read from local dd copies (FUSE/lock-safe). Prints a MERGE PLAN, changes nothing.

import sqlite3, os, subprocess, tempfile

BASE = "/mnt/workspace/VST Install/Kontakt Portable/UserData/Kontakt 8"
PATHS_DB = f"{BASE}/komplete.db3"                                   # LIVE now = 78MB clean Z: paths, blank
TILES_DB = f"{BASE}/komplete.db3.pre_ewqlra_144329"                 # 42MB backup: type-2 tiles, D:/F: paths

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

def load(src):
    if not os.path.exists(src):
        return None, f"MISSING {src}"
    d = copy(src)
    con = sqlite3.connect(d); con.create_collation("KOMPLETE", kompare); c = con.cursor()
    try: c.execute("PRAGMA wal_checkpoint(FULL)")
    except Exception: pass
    rows = c.execute(
        "SELECT alias, path, content_type, visible FROM k_content_path"
    ).fetchall()
    integ = c.execute("PRAGMA integrity_check").fetchone()[0]
    con.close()
    for p in (d, d + "-wal", d + "-shm"):
        try: os.remove(p)
        except OSError: pass
    # key by (alias,path) but also keep alias->type map
    return {"rows": rows, "integrity": integ}, None

def drive_of(path):
    p = (path or "")
    return p[:2].upper() if len(p) >= 2 and p[1] == ":" else "??"

paths_db, e1 = load(PATHS_DB)
tiles_db, e2 = load(TILES_DB)
if e1: print(e1)
if e2: print(e2)
if not (paths_db and tiles_db):
    raise SystemExit("cannot proceed without both dbs")

print(f"PATHS db (LIVE, 78MB clean-Z, blank): {PATHS_DB}")
print(f"  integrity={paths_db['integrity']}  content_paths={len(paths_db['rows'])}")
print(f"TILES db (pre_ewqlra backup, tiles): {TILES_DB}")
print(f"  integrity={tiles_db['integrity']}  content_paths={len(tiles_db['rows'])}")

# --- drive histogram ---
def hist(rows):
    h = {}
    for alias, path, ct, vis in rows:
        h[drive_of(path)] = h.get(drive_of(path), 0) + 1
    return dict(sorted(h.items()))
print(f"\nPATHS db drive histogram: {hist(paths_db['rows'])}")
print(f"TILES db drive histogram: {hist(tiles_db['rows'])}")

# --- type-2 alias set in the TILES db (the promotion target set) ---
tiles_type2 = {alias for alias, path, ct, vis in tiles_db["rows"] if ct == 2}
print(f"\nTILES db has {len(tiles_type2)} type-2 (tile) aliases.")

# how are those same aliases represented in the PATHS db?
paths_by_alias = {}
for alias, path, ct, vis in paths_db["rows"]:
    paths_by_alias.setdefault(alias, []).append((path, ct))

promote = []      # aliases present in PATHS db that should become type 2
missing_in_paths = []  # tile aliases NOT present in PATHS db at all
for alias in sorted(tiles_type2):
    if alias in paths_by_alias:
        cur_types = {ct for _, ct in paths_by_alias[alias]}
        if 2 not in cur_types:
            promote.append(alias)
    else:
        missing_in_paths.append(alias)

print(f"\n=== PROMOTION PLAN (PATHS db aliases to flip content_type -> 2) ===")
print(f"  {len(promote)} aliases are tile-type in TILES db but non-tile in PATHS db:")
for a in promote:
    pth = paths_by_alias[a][0][0]
    print(f"     {a:26s} {drive_of(pth)}  {pth}")
if missing_in_paths:
    print(f"\n  NOTE: {len(missing_in_paths)} tile aliases from the old backup are ABSENT in the 78MB db")
    print(f"        (these were removed/renamed since; NOT restoring them keeps the current library set):")
    for a in missing_in_paths:
        print(f"     {a}")

# --- libraries ONLY in PATHS db (added since old backup — must NOT be lost) ---
tiles_aliases = {alias for alias, path, ct, vis in tiles_db["rows"]}
only_in_paths = sorted({a for a in paths_by_alias} - tiles_aliases)
print(f"\n=== ADDED-SINCE-BACKUP (aliases only in the 78MB PATHS db, absent from old 42MB backup) ===")
print(f"  {len(only_in_paths)} — a wholesale pre_ewqlra restore would LOSE these:")
for a in only_in_paths:
    pth = paths_by_alias[a][0][0]
    print(f"     {a:26s} {drive_of(pth)}  {pth}")

# --- any tile alias in TILES db pointing at stale D:/F: (confirms why wholesale restore is wrong) ---
stale = [(alias, path) for alias, path, ct, vis in tiles_db["rows"]
         if ct == 2 and drive_of(path) in ("D:", "F:")]
print(f"\n=== STALE-PATH tiles in the TILES db (why we must NOT keep pre_ewqlra live) ===")
print(f"  {len(stale)} type-2 tile rows point at D:/F::")
for a, p in stale[:40]:
    print(f"     {a:26s} {p}")

print("\n---")
print("RECOMMENDED FIX (non-destructive, preserves current library set + clean Z: paths):")
print("  Restore the 78MB clean-Z db as live, then flip the PROMOTION-PLAN aliases' content_type 3->2.")
print("  This keeps every current path (incl. added-since libs) on clean Z:, and brings the tiles back.")
print("READ-ONLY: this script changed nothing.")
