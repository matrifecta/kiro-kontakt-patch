#!/usr/bin/env python3
# diff-db-content.py (READ-ONLY)
# Before restoring the snapshot komplete.db3 over the live (re-bloated) one, compare what each contains:
# content paths (libraries) and preset/sound_info counts. Surface anything in LIVE that is NOT in SNAPSHOT
# (libraries/instruments added since sep 7) so we don't lose them by restoring the older DB.
import sqlite3, sys

LIVE = "/mnt/workspace/VST Install/Kontakt Portable/UserData/komplete.db3"
SNAP = "/mnt/wd_black/kontakt-known-good-20260907_123950/kontakt_userdata/komplete.db3"

def kompare(a,b):
    a=(a or "").strip().casefold(); b=(b or "").strip().casefold()
    return (a>b)-(a<b)

def openc(p):
    c=sqlite3.connect(p); c.create_collation("KOMPLETE", kompare); return c

def paths(c):
    try:
        return { r[0] for r in c.execute("SELECT k_content_path FROM k_content_path").fetchall() }
    except Exception as e:
        return set()

def count(c, t):
    try: return c.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
    except Exception: return -1

lc=openc(LIVE); sc=openc(SNAP)

print("=== row counts ===")
for t in ("k_content_path","k_sound_info"):
    print(f"  {t:16s} live={count(lc,t):8d}  snapshot={count(sc,t):8d}")

lp=paths(lc); sp=paths(sc)
print(f"\n=== content paths: live={len(lp)}  snapshot={len(sp)} ===")

only_live = sorted(lp - sp, key=lambda x:(x or "").lower())
only_snap = sorted(sp - lp, key=lambda x:(x or "").lower())

print(f"\n=== in LIVE but NOT snapshot ({len(only_live)}) — would be LOST by restore, review! ===")
for p in only_live: print("   +", p)

print(f"\n=== in SNAPSHOT but NOT live ({len(only_snap)}) — restore would re-add these ===")
for p in only_snap: print("   -", p)

# preset-level: names present in live but not snapshot (best-effort; table may vary)
def preset_names(c):
    for tbl,col in (("k_sound_info","name"),("k_sound_info","sound_info_name")):
        try:
            return { r[0] for r in c.execute(f"SELECT {col} FROM {tbl}").fetchall() }
        except Exception: continue
    return None

lpn=preset_names(lc); spn=preset_names(sc)
if lpn is not None and spn is not None:
    extra = sorted((lpn - spn))
    print(f"\n=== preset names in LIVE but NOT snapshot ({len(extra)}) — sample up to 40 ===")
    for n in extra[:40]: print("   *", n)
    if len(extra)>40: print(f"   ... (+{len(extra)-40} more)")
else:
    print("\n(preset-name column not found; relying on content-path diff above)")

lc.close(); sc.close()
print("\nREAD-ONLY. If 'in LIVE but NOT snapshot' lists real libraries you added since sep 7, we preserve")
print("them (re-point/re-add after restore) instead of losing them.")
