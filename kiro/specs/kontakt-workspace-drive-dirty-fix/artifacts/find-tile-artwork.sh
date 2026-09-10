#!/usr/bin/env bash
#
# find-tile-artwork.sh   (READ-ONLY: only finds/lists, changes nothing)
#
# After the content_type 3->2 merge, most tiles render but a subset of genuine Player libs are still
# folder-icon (ANALOG STRINGS, Balinese Gamelan, East Asia, Guarneri Violin, India, Mass, Piano Colors,
# Soul Sessions, Straylight, Tablas, Ultimate Pro Oriental Strings, ...). content_type is correct now,
# so the missing piece is the on-disk TILE ARTWORK not resolving for those libs.
#
# Kontakt/NKS tile art normally lives in the WINE-side NI Resources tree:
#   <prefix>/drive_c/users/Public/Documents/Native Instruments/... or
#   .../Documents and Settings/... , and the per-product images under an "image/<ProductName>/" folder,
#   plus the library's own product art referenced by its .nicnt / .nkx (the "MST" / "picture" resources).
#
# This script:
#   1) shows how a WORKING tile lib (e.g. Amati Viola, Cloud Supply) resolves art  -> the reference shape
#   2) for each STILL-BLANK lib, locates its library folder (from komplete.db3 path), lists any product
#      art inside it (.nicnt, resources/pictures, *.png/*.meta), and searches the NI Resources image dirs
#   3) searches the other drives (storage/workspace/wd_black/btrfs) for a matching image/<Lib> folder we
#      may have copied earlier, so we can see if the art exists somewhere but isn't where Kontakt looks.
#
# Usage: bash find-tile-artwork.sh

set -u
PREFIX="${WINEPREFIX:-$HOME/.wine}"
BASE="/mnt/workspace/VST Install/Kontakt Portable/UserData/Kontakt 8"
LIVE="$BASE/komplete.db3"

echo "=== 0) NI Resources / image dirs in the wine prefix ==="
# common locations Kontakt/NKS uses for tile art
find "$PREFIX/drive_c" -type d \( -iname 'NI Resources' -o -iname 'image' -o -iname 'Pictures' \) 2>/dev/null \
  | grep -iE 'native instruments|NI Resources|image' | sort | sed 's/^/  /' | head -50
echo

# resolve ALL db rows whose alias OR path matches a fuzzy term; emit  alias\tpath\tcontent_type  lines.
# READ-ONLY via python copy. Also maps Z:\mnt\... -> /mnt/... for on-disk inspection.
resolve_rows() {  # $1 = fuzzy term
  python3 - "$LIVE" "$1" <<'PY'
import sqlite3,sys,subprocess,tempfile,os
db,term=sys.argv[1],sys.argv[2]
def k(a,b):
    a=(a or "").strip().casefold(); b=(b or "").strip().casefold(); return (a>b)-(a<b)
d=tempfile.mktemp(suffix=".db3"); subprocess.run(["dd",f"if={db}",f"of={d}","bs=1M"],stderr=subprocess.DEVNULL)
for s in ("-wal","-shm"):
    if os.path.exists(db+s): subprocess.run(["dd",f"if={db+s}",f"of={d+s}","bs=1M"],stderr=subprocess.DEVNULL)
def mapwin(p):
    if len(p)>=2 and p[1]==":":
        drive=p[0].upper(); rest=p[2:].replace("\\","/")
        m={"Z":"","D":"/mnt/workspace","F":"/mnt/workspace","G":"/mnt/btrfs_disk","L":"/mnt/wd_black","W":"/mnt/win_system"}
        return m.get(drive,"")+rest
    return p
try:
    con=sqlite3.connect(d); con.create_collation("KOMPLETE",k); c=con.cursor()
    rows=c.execute("SELECT alias,path,content_type FROM k_content_path WHERE alias LIKE ? OR path LIKE ?",
                   (f"%{term}%", f"%{term}%")).fetchall()
    con.close()
    if not rows: print("NOMATCH\t\t"); raise SystemExit
    for alias,path,ct in rows:
        print(f"{alias}\t{mapwin(path)}\t{ct}")
finally:
    for x in (d,d+"-wal",d+"-shm"):
        try: os.remove(x)
        except OSError: pass
PY
}

inspect_libdir() {  # $1 = alias  $2 = on-disk path  $3 = content_type
  local alias="$1" path="$2" ctype="$3"
  echo "----- [$alias]  content_type=$ctype"
  if [ "$path" = "" ]; then echo "    (empty path)"; return; fi
  echo "    libdir: $path"
  if [ ! -e "$path" ]; then echo "    *** libdir MISSING on disk ***"; return; fi
  if [ -d "$path" ]; then
    # any image/art assets shipped inside the library folder (Custom libs store their tile here)
    find "$path" -maxdepth 3 -type f \( -iname '*.png' -o -iname '*.jpg' -o -iname '*.nicnt' \
        -o -iname '*.meta' -o -iname 'MST*' -o -iname '*.nkx' -o -iname '*.nfo' \) 2>/dev/null \
      | head -20 | sed 's/^/      file: /'
    local nicnt; nicnt="$(find "$path" -maxdepth 2 -iname '*.nicnt' 2>/dev/null | head -1)"
    if [ -n "$nicnt" ]; then
      echo "      .nicnt: $nicnt"
      strings -n 4 "$nicnt" 2>/dev/null | grep -iE 'image|picture|\.png|[A-Z][a-z]+ [A-Z]' | head -8 | sed 's/^/         str: /'
    fi
  fi
}

inspect_lib() {  # $1 = fuzzy term
  local term="$1" line alias path ctype
  resolve_rows "$term" | while IFS=$'\t' read -r alias path ctype; do
    [ "$alias" = "NOMATCH" ] && { echo "----- [$term]  (no db row matches)"; continue; }
    inspect_libdir "$alias" "$path" "$ctype"
    # matching NI Resources image dir in the prefix
    find "$PREFIX/drive_c" -type d -ipath '*image*' -iname "*${term%% *}*" 2>/dev/null | head -6 | sed 's/^/      NIimg: /'
  done
}

echo "=== 1) WORKING reference libs (a Player tile that renders) ==="
for a in "Amati" "Cloud Supply"; do inspect_lib "$a"; done
echo

# The genuinely-blank set (all Custom-type). Fuzzy terms match db alias OR path (resolve_rows returns all).
echo "=== 2) STILL-BLANK Custom libs (find their tile artwork on disk) ==="
for a in \
  "Sinfonia" "Doru Malaia" "Drumdrops" "Epic SoundLab" "Modern and Massive" \
  "Keyscape" "MegaMagic" "Sonic Mechanics" "Alchemist" ; do
  inspect_lib "$a"
done
echo

echo "=== 3) search ALL drives for image/<Lib> folders we may have copied earlier ==="
for root in "/mnt/storage" "/mnt/workspace" "/mnt/wd_black" "/mnt/btrfs_disk"; do
  [ -d "$root" ] || continue
  echo "  under $root:"
  find "$root" -type d \( -iname 'NI Resources' -o -ipath '*NI Resources*image*' \) 2>/dev/null | head -20 | sed 's/^/    /'
done

echo
echo "READ-ONLY. Compare a WORKING lib's art layout to a BLANK one: the blank libs are missing either the"
echo "product art inside their folder OR the matching NI Resources/image/<ProductName> dir Kontakt reads."
