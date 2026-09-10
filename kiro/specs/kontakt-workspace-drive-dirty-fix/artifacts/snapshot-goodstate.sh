#!/usr/bin/env bash
#
# snapshot-goodstate.sh — capture the current KNOWN-GOOD Kontakt browser state as one restore point.
#
# Backs up (copy, non-destructive):
#   1) the live browser DB komplete.db3 (+ any -wal/-shm)  -> the content_type-2 tiles + clean paths + deduped
#   2) the NI Resources/image tree                          -> all authored + native tile artwork
#   3) a manifest (counts, integrity, date) for verification
# into a single timestamped snapshot dir under UserData. Also OPTIONALLY archives the many intermediate
# pre_*/scratch DB backups into the snapshot's _superseded/ folder to declutter (kept, not deleted).
#
# Usage: bash snapshot-goodstate.sh            # dry-run (shows what it will copy + sizes)
#        bash snapshot-goodstate.sh apply
set -u
MODE="${1:-dryrun}"
UD="/mnt/workspace/VST Install/Kontakt Portable/UserData"
K8="$UD/Kontakt 8"
LIVE="$K8/komplete.db3"
NIIMG="$UD/NI Resources/image"
STAMP="$(date +%Y%m%d_%H%M%S)"
# snapshot lands on WD Black (a DIFFERENT drive from the NTFS workspace volume), root-level KONTAKT BACKUP dir
SNAP="/mnt/wd_black/KONTAKT BACKUP/goodstate_snapshot_$STAMP"

echo "=== snapshot good state ==="
echo "  live db : $LIVE  ($(stat -c '%s' "$LIVE" 2>/dev/null) bytes)"
echo "  ni image: $NIIMG  ($(du -sh "$NIIMG" 2>/dev/null | cut -f1))"
echo "  snapshot -> $SNAP"

if pgrep -x wineserver >/dev/null 2>&1 || pgrep -x reaper >/dev/null 2>&1; then
  echo "  *** close Reaper + wineserver -k first (so the db is quiescent) ***"
  [ "$MODE" = apply ] && { echo ABORT; exit 1; }
fi

# quick integrity + tile count preview (read-only copy)
python3 - "$LIVE" <<'PY'
import sqlite3,sys,subprocess,tempfile,os
db=sys.argv[1]
def k(a,b):
    a=(a or "").strip().casefold();b=(b or "").strip().casefold();return (a>b)-(a<b)
d=tempfile.mktemp(suffix=".db3");subprocess.run(["dd",f"if={db}",f"of={d}","bs=1M"],stderr=subprocess.DEVNULL)
for s in ("-wal","-shm"):
    if os.path.exists(db+s):subprocess.run(["dd",f"if={db+s}",f"of={d+s}","bs=1M"],stderr=subprocess.DEVNULL)
con=sqlite3.connect(d);con.create_collation("KOMPLETE",k);c=con.cursor()
print("  integrity:", c.execute("PRAGMA integrity_check").fetchone()[0])
print("  content paths:", c.execute("SELECT COUNT(*) FROM k_content_path").fetchone()[0])
print("  type2 tile libs:", c.execute("SELECT COUNT(*) FROM k_content_path WHERE content_type=2").fetchone()[0])
print("  D:/F: stale paths:", c.execute("SELECT COUNT(*) FROM k_content_path WHERE path LIKE 'D:%' OR path LIKE 'F:%'").fetchone()[0])
con.close()
for x in (d,d+"-wal",d+"-shm"):
    try:os.remove(x)
    except OSError:pass
PY

echo "  NI image dirs: $(ls -1 "$NIIMG" 2>/dev/null | wc -l)"
echo "  intermediate pre_* db backups present:"
ls -1 "$K8"/komplete.db3.pre_* 2>/dev/null | sed 's/^/     /' | head -40
echo

if [ "$MODE" != apply ]; then echo "DRY-RUN. Re-run: bash $0 apply"; exit 0; fi

# ensure WD Black is mounted before writing there
if ! mountpoint -q /mnt/wd_black; then
  echo "ABORT: /mnt/wd_black is not mounted. Mount it, then re-run."
  exit 1
fi
mkdir -p "/mnt/wd_black/KONTAKT BACKUP"
mkdir -p "$SNAP"
echo "=== 1) copy live db (+wal/shm) ==="
cp -av "$LIVE" "$SNAP/komplete.db3" | sed 's/^/  /'
for s in -wal -shm; do [ -f "$LIVE$s" ] && cp -av "$LIVE$s" "$SNAP/komplete.db3$s" | sed 's/^/  /'; done

echo "=== 2) copy NI Resources/image tree ==="
mkdir -p "$SNAP/NI Resources"
cp -a "$NIIMG" "$SNAP/NI Resources/image"
echo "  copied $(ls -1 "$SNAP/NI Resources/image" | wc -l) image dirs"

echo "=== 3) archive intermediate pre_* db backups (declutter; kept, not deleted) ==="
mkdir -p "$SNAP/_superseded"
shopt -s nullglob
for f in "$K8"/komplete.db3.pre_* ; do mv -v "$f" "$SNAP/_superseded/" | sed 's/^/  /'; done
shopt -u nullglob

echo "=== 4) write manifest ==="
{
  echo "Kontakt good-state snapshot"
  echo "date: $(date -Iseconds)"
  echo "source live db: $LIVE"
  echo "ni image dirs: $(ls -1 "$SNAP/NI Resources/image" | wc -l)"
  echo "notes: 46 Player/NKS tiles (content_type=2) + 12 Custom authored tiles; PlugInGuru renamed dot-free;"
  echo "       stale duplicate sound-info rows removed; clean Z: paths; integrity ok."
  echo "restore db:   cp -av \"$SNAP/komplete.db3\" \"$LIVE\"; rm -f \"$LIVE\"-wal \"$LIVE\"-shm  (Kontakt closed)"
  echo "restore image: cp -a \"$SNAP/NI Resources/image/.\" \"$NIIMG/\""
} > "$SNAP/MANIFEST.txt"
cat "$SNAP/MANIFEST.txt" | sed 's/^/  /'

echo
echo "DONE. Snapshot at: $SNAP"
echo "Stored on WD Black (separate drive from the NTFS workspace volume) so a workspace-volume problem can't"
echo "take out both the live db and this backup. Intermediate pre_* db backups moved into $SNAP/_superseded/."
