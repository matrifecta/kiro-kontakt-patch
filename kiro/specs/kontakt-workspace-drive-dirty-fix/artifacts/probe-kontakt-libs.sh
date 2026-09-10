#!/usr/bin/env bash
# probe-kontakt-libs.sh  (READ-ONLY)
# Map the Kontakt library catalog source: registered libraries in komplete.db3 (name, path, content_type)
# and the NI banner artwork dirs (NI Resources/image/<ProductName>/MST_artwork.png). Nothing modified.
# Writes report to artifacts/kontakt-libs-probe.txt
set -u
OUT="/home/phnx/KIRO/.kiro/specs/kontakt-workspace-drive-dirty-fix/artifacts/kontakt-libs-probe.txt"
exec > >(tee "$OUT") 2>&1

DB_SRC="/mnt/workspace/VST Install/Kontakt Portable/UserData/Kontakt 8/komplete.db3"
TMP="/tmp/komplete_probe.db3"

echo "===== (a) copy DB to /tmp (78MB read via cp) ====="
cp "$DB_SRC" "$TMP" 2>/dev/null && echo "  copied: $(du -h "$TMP" | cut -f1)" || { echo "  DB not found at $DB_SRC"; }

echo
echo "===== (b) k_content_path schema + sample rows ====="
python3 - <<'PY'
import sqlite3, sys
db="/tmp/komplete_probe.db3"
try: con=sqlite3.connect(db)
except Exception as e:
    print("  cannot open:",e); sys.exit(0)
def col(t):
    try: return [r[1] for r in con.execute(f"PRAGMA table_info({t})")]
    except: return []
print("  k_content_path columns:", col("k_content_path"))
# tables that look library-ish
tabs=[r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")]
print("  tables:", [t for t in tabs if any(k in t.lower() for k in ('content','library','product','bank','sound'))])
print()
print("  --- sample k_content_path rows (path, content_type, any name-ish col) ---")
cols=col("k_content_path")
sel=[c for c in cols if c.lower() in ('path','content_type','name','alias','id')] or cols[:4]
try:
  for r in con.execute(f"SELECT {','.join(sel)} FROM k_content_path LIMIT 25"):
    print("   ", dict(zip(sel,r)))
except Exception as e: print("   query failed:",e)
PY

echo
echo "===== (c) NI Resources/image/<name>/ banner dirs (art source) ====="
NIIMG="/mnt/workspace/VST Install/Kontakt Portable/UserData/Kontakt 8"
# NI Resources can live under UserData or the Kontakt content root — search both, shallow
for base in "$NIIMG" "/mnt/workspace/VST Install/Kontakt Portable"; do
  find "$base" -maxdepth 6 -type d -ipath '*NI Resources/image/*' 2>/dev/null | head -60
done | sort -u | while read -r d; do
  art=""; [ -f "$d/MST_artwork.png" ] && art="artwork"; [ -f "$d/MST_logo.png" ] && art="$art+logo"
  echo "   $(basename "$d")   [$art]   $d"
done
echo
echo "===== (d) counts ====="
python3 - <<'PY'
import sqlite3
con=sqlite3.connect("/tmp/komplete_probe.db3")
try:
  n=con.execute("SELECT COUNT(*) FROM k_content_path").fetchone()[0]; print("  k_content_path rows:", n)
  for ct in con.execute("SELECT content_type, COUNT(*) FROM k_content_path GROUP BY content_type"):
    print("    content_type", ct[0], "->", ct[1])
except Exception as e: print("  ",e)
PY
rm -f /tmp/komplete_probe.db3
echo "(done — report: $OUT)"
