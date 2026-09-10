#!/usr/bin/env bash
# confirm-single-pg-row.sh (READ-ONLY)
# The DB shows only ONE PlugInGuru row (the working renamed one). The blank 'PlugInGuru...nds.KONTAKT' tile in
# the browser is therefore a stale DISPLAY artifact, not a real row. Confirm: (a) exactly one row total in the
# live db; (b) whether any browser-layout/prefs file still holds the old dotted name (that would be what draws
# the ghost). If only a relaunch is needed, this says so.
set -u
LIVE="/mnt/workspace/VST Install/Kontakt Portable/UserData/Kontakt 8/komplete.db3"
UD="/mnt/workspace/VST Install/Kontakt Portable/UserData"
PREFIX="${WINEPREFIX:-$HOME/.wine}"

echo "=== count PlugInGuru/MegaMagic rows in LIVE db ==="
python3 - "$LIVE" <<'PY'
import sqlite3,sys,subprocess,tempfile,os
db=sys.argv[1]
def k(a,b):
    a=(a or "").strip().casefold();b=(b or "").strip().casefold();return (a>b)-(a<b)
d=tempfile.mktemp(suffix=".db3");subprocess.run(["dd",f"if={db}",f"of={d}","bs=1M"],stderr=subprocess.DEVNULL)
for s in ("-wal","-shm"):
    if os.path.exists(db+s):subprocess.run(["dd",f"if={db+s}",f"of={d+s}","bs=1M"],stderr=subprocess.DEVNULL)
con=sqlite3.connect(d);con.create_collation("KOMPLETE",k);c=con.cursor()
rows=c.execute("SELECT id,alias,path FROM k_content_path WHERE alias LIKE '%MegaMagic%' OR alias LIKE '%PlugInGuru%' OR path LIKE '%MegaMagic%'").fetchall()
print(f"  rows: {len(rows)}")
for i,a,p in rows: print(f"    id={i} alias='{a}'")
# any row still holding the dotted name anywhere?
dotted=c.execute("SELECT COUNT(*) FROM k_content_path WHERE path LIKE '%PlugInGuru.MegaMagic%' OR alias LIKE '%.KONTAKT%'").fetchone()[0]
print(f"  dotted/stale rows: {dotted}")
con.close()
for x in (d,d+"-wal",d+"-shm"):
    try:os.remove(x)
    except OSError:pass
PY

echo
echo "=== any file (prefs/layout/cache) under UserData or prefix still mentioning the dotted name ==="
grep -rIl --binary-files=text "PlugInGuru.MegaMagic" "$UD" 2>/dev/null | grep -viE '_kiro_backup|\.pre_' | sed 's/^/  UD: /'
grep -rIl --binary-files=text "PlugInGuru.MegaMagic" "$PREFIX/drive_c/users" 2>/dev/null | sed 's/^/  prefix: /' | head
echo
echo "READ-ONLY. If rows=1 and dotted=0 and no live prefs file mentions the dotted name, the ghost tile is"
echo "purely in Kontakt's running/session memory -> a full close (wineserver -k) + relaunch clears it."
