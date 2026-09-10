#!/usr/bin/env bash
#
# db-final-df-cleanup.sh
#
# Final convergence: remove the last D:/F: leftovers so komplete.db3 is Z:-only.
#  - Delete ids 130-133: D: Content/Presets/Tools duplicates (Z: twins 51-54 exist).
#  - Delete id 18: stale F: GetGood "Modern & Massive" sub-path (GetGood now Z:-registered).
#  - Repoint id 50: F: User Content -> Z: equivalent (retire F:, keep User Content working).
#
# Matches by exact path (not hardcoded ids) for safety. Kontakt CLOSED. DB backed up.

set -u
DB="/mnt/workspace/VST Install/Kontakt Portable/UserData/Kontakt 8/komplete.db3"
STAMP="$(date +%Y%m%d_%H%M%S)"

if pgrep -fi 'Kontakt 8.exe' | grep -qv grep; then
  echo "ABORT: Kontakt running. File->Exit first."; exit 1
fi

echo "=== backup ==="
cp -av "$DB" "$DB.pre_dfcleanup_$STAMP"

echo "=== verify the Z: twins for Content/Tools exist before deleting D: dups ==="
sqlite3 "$DB" "SELECT COUNT(*) FROM k_content_path WHERE path IN (
 'Z:\mnt\workspace\VST Install\Kontakt Portable\Kontakt 8\Content\Presets\Lo-Fi Vibes',
 'Z:\mnt\workspace\VST Install\Kontakt Portable\Kontakt 8\Content\Presets\Piano Uno',
 'Z:\mnt\workspace\VST Install\Kontakt Portable\Kontakt 8\Content\Tools\Chords',
 'Z:\mnt\workspace\VST Install\Kontakt Portable\Kontakt 8\Content\Tools\Phrases');"
echo "(expect 4 = safe to delete the D: duplicates)"

echo "=== delete D: Content/Tools duplicates + stale F: GetGood sub-path ==="
sqlite3 "$DB" "
DELETE FROM k_content_path WHERE path IN (
 'D:\VST Install\Kontakt Portable\Kontakt 8\Content\Presets\Lo-Fi Vibes',
 'D:\VST Install\Kontakt Portable\Kontakt 8\Content\Presets\Piano Uno',
 'D:\VST Install\Kontakt Portable\Kontakt 8\Content\Tools\Chords',
 'D:\VST Install\Kontakt Portable\Kontakt 8\Content\Tools\Phrases',
 'F:\VST Install\Kontakt Vst-i\GetGood Drums - Modern and Massive Pack\Modern & Massive'
);
"

echo "=== repoint F: User Content -> Z: equivalent ==="
sqlite3 "$DB" "UPDATE k_content_path SET path='Z:\mnt\workspace\VST Install\Kontakt Portable\UserData\User Content' WHERE path='F:\VST Install\Kontakt Portable\UserData\User Content';"

echo "=== AFTER ==="
sqlite3 "$DB" "SELECT id, path FROM k_content_path;" > /tmp/kcp_final.txt 2>/dev/null
echo -n 'total rows: '; wc -l < /tmp/kcp_final.txt
echo -n 'Z: rows: '; grep -icE '\|Z:' /tmp/kcp_final.txt
echo -n 'D: rows (expect 0): '; grep -icE '\|D:' /tmp/kcp_final.txt
echo -n 'F: rows (expect 0): '; grep -icE '\|F:' /tmp/kcp_final.txt

echo
echo "ROLLBACK (Kontakt closed): cp -av \"$DB.pre_dfcleanup_$STAMP\" \"$DB\""
