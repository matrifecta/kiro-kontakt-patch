#!/usr/bin/env bash
# probe-remaining-blanks.sh  (READ-ONLY)
# After the tile work, a few still show folder icons: GetGood (type2, has .nicnt+NI image dir already),
# PlugInGuru (we made an image dir), Guarneri Violin, Hy2rogen. Figure out per-lib WHY.
# For each: db row (alias, content_type, path); .nicnt Product <Name> if any; which NI Resources/image dirs
# exist that could match (by alias AND by .nicnt name); list their contents.
set -u
NIIMG="/mnt/workspace/VST Install/Kontakt Portable/UserData/NI Resources/image"
LIVE="/mnt/workspace/VST Install/Kontakt Portable/UserData/Kontakt 8/komplete.db3"

dbrow() {  # $1 fuzzy
  python3 - "$LIVE" "$1" <<'PY'
import sqlite3,sys,subprocess,tempfile,os
db,term=sys.argv[1],sys.argv[2]
def k(a,b):
    a=(a or "").strip().casefold();b=(b or "").strip().casefold();return (a>b)-(a<b)
d=tempfile.mktemp(suffix=".db3");subprocess.run(["dd",f"if={db}",f"of={d}","bs=1M"],stderr=subprocess.DEVNULL)
for s in ("-wal","-shm"):
    if os.path.exists(db+s):subprocess.run(["dd",f"if={db+s}",f"of={d+s}","bs=1M"],stderr=subprocess.DEVNULL)
try:
    con=sqlite3.connect(d);con.create_collation("KOMPLETE",k);c=con.cursor()
    for a,ct,p in c.execute("SELECT alias,content_type,path FROM k_content_path WHERE alias LIKE ? OR path LIKE ?",(f"%{term}%",f"%{term}%")):
        print(f"      db: alias='{a}'  type={ct}")
    con.close()
finally:
    for x in (d,d+"-wal",d+"-shm"):
        try:os.remove(x)
        except OSError:pass
PY
}

libnicnt() {  # $1 lib dir
  local n; n="$(find "$1" -maxdepth 3 -iname '*.nicnt' 2>/dev/null | head -1)"
  [ -z "$n" ] && { echo "      .nicnt: none"; return; }
  local nm; nm="$(strings -n3 "$n" 2>/dev/null | grep -oiE '<Name>[^<]+</Name>' | head -1 | sed -E 's#</?Name>##g')"
  echo "      .nicnt: $n"
  echo "      .nicnt Product Name: '$nm'"
}

niimg_match() {  # $1 term
  ls -d "$NIIMG/"*"$1"* 2>/dev/null | sed 's/^/      NIimg dir: /'
}

echo "===== GetGood ====="
dbrow "GetGood Drums - Modern and Massive"
libnicnt "/mnt/wd_black/Kontakt Libraries/Player/GetGood Drums - Modern and Massive Pack"
niimg_match "GGD"; niimg_match "GetGood"; niimg_match "Modern and Massive"

echo "===== PlugInGuru ====="
dbrow "MegaMagic"
libnicnt "/mnt/btrfs_disk/Kontakt Libraries/Custom/PlugInGuru.MegaMagic.Bells.Winds.KONTAKT"
niimg_match "MegaMagic"; niimg_match "PlugInGuru"

echo "===== Hy2rogen ====="
dbrow "Hy2rogen"
for base in "/mnt/btrfs_disk/Kontakt Libraries/Custom" "/mnt/wd_black/Kontakt Libraries/Custom" "/mnt/btrfs_disk/Kontakt Libraries/Player"; do
  d="$(ls -d "$base/"*Hy2rogen* 2>/dev/null | head -1)"; [ -n "$d" ] && { echo "      libdir: $d"; libnicnt "$d"; ls "$d" 2>/dev/null | head | sed 's/^/         /'; }
done
niimg_match "Hy2rogen"; niimg_match "House Nights"

echo
echo "READ-ONLY. For GetGood: if the NI image dir is 'GGD Modern and Massive' but db alias differs, the tile"
echo "key may be the .nicnt Product Name (present) — so why blank? Compare with a working type-2 lib. For"
echo "PlugInGuru: check the image dir name EXACTLY equals the db alias (incl. trailing .KONTAKT)."
