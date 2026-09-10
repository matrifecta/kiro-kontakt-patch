#!/usr/bin/env python3
"""
list-blank-tiles.py   (READ-ONLY)

Determine EXACTLY which visible library-browser entries have a tile vs a folder icon.
A tile renders iff the library's registration is paired to a LibrariesCache/*.cache.
The .cache filename is the library's cache key (K + hash). We read each visible
k_content_path row's identity (upid / product_id / alias / path) and check whether
a .cache file exists whose name matches the row's cache key.

Because the .cache key derivation isn't publicly documented, we use the most reliable
available signal: match on the row's `upid`/`product_id` hash fragment against the
cache filenames, and ALSO report rows that have no such pairing = blank tile.
"""
import sqlite3, os, re

K8 = "/mnt/workspace/VST Install/Kontakt Portable/UserData/Kontakt 8"
DB = os.path.join(K8, "komplete.db3")
CACHE = os.path.join(K8, "LibrariesCache")

def kompare(a, b):
    x=(a or "").strip().casefold(); y=(b or "").strip().casefold(); return (x>y)-(x<y)

con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
con.create_collation("KOMPLETE", kompare)
cur = con.cursor()

# cache files present
caches = sorted(f for f in os.listdir(CACHE) if f.lower().endswith(".cache"))
cacheset = set(os.path.splitext(c)[0] for c in caches)  # names without .cache
print(f"LibrariesCache files: {len(caches)}")

# what columns exist
cols = [r[1] for r in cur.execute("PRAGMA table_info(k_content_path);")]
have = lambda c: c in cols
sel = "id, content_type, visible, alias, path" + \
      (", upid" if have("upid") else "") + \
      (", product_id" if have("product_id") else "")
rows = cur.execute(f"SELECT {sel} FROM k_content_path WHERE visible=1 ORDER BY alias;").fetchall()

print(f"visible content paths: {len(rows)}\n")

def cache_key_candidates(r):
    # collect any hash-like tokens from upid/product_id that could match a K... cache name
    toks = []
    for v in r[5:]:
        if v:
            for m in re.findall(r'K[0-9A-Za-z]{6,}', str(v)):
                toks.append(m)
    return toks

tiled, blank = [], []
for r in rows:
    alias = r[3]; path = r[4]
    keys = cache_key_candidates(r)
    paired = any(k in cacheset for k in keys)
    (tiled if paired else blank).append((alias, path))

print("=== HAS a paired .cache (tile likely renders) ===")
for a,p in tiled: print(f"  {a}")
print(f"  [{len(tiled)}]")

print("\n=== NO paired .cache (folder icon / blank tile) ===")
for a,p in blank: print(f"  {a}   <-  {p}")
print(f"  [{len(blank)}]")

con.close()
print("\nNOTE: pairing is inferred from upid/product_id hash tokens vs cache filenames.")
print("If ALL show as blank, the identity columns don't carry the cache key literally —")
print("in that case the authoritative source is the live browser (visual).")
