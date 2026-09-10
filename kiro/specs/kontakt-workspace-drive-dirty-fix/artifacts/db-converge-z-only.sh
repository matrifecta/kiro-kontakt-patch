#!/usr/bin/env bash
#
# db-converge-z-only.sh
#
# Converge komplete.db3 onto Z: fast-drive registrations and purge the legacy
# D:\PROGRAMS\VST, Samples & DAW full-folder scan.
#
# Phase A: REPOINT the 16 NO-Z-REG real libraries' D: rows to their exact Z:
#          fast-drive path (keeps the same row id -> k_sound_info links stay intact).
#          EWQL RA excluded (Bug C).
# Phase B: DELETE remaining D:\PROGRAMS rows (the 115 non-Kontakt junk + the 14
#          Z-REG-OK duplicates + EWQL RA's D: row) and the parent scan row
#          D:\VST Install\Kontakt Vst-i Folders.
#
# Kontakt MUST be closed. DB backed up first. Reversible.
#
# NOTE: paths use Windows-style backslashes exactly as stored in the DB. In this
# heredoc we write them literally; sqlite treats them as plain string chars.

set -u
DB="/mnt/workspace/VST Install/Kontakt Portable/UserData/Kontakt 8/komplete.db3"
STAMP="$(date +%Y%m%d_%H%M%S)"

if pgrep -fi 'Kontakt 8.exe' | grep -qv grep; then
  echo "ABORT: Kontakt running. File->Exit first."; exit 1
fi
[ -f "$DB" ] || { echo "ABORT: no DB at $DB"; exit 1; }

echo "=== backup DB ==="
cp -av "$DB" "$DB.pre_converge_$STAMP"

echo "=== BEFORE ==="
sqlite3 "$DB" "SELECT COUNT(*) FROM k_content_path;"

echo "=== Phase A: repoint 16 NO-Z-REG libs (D: -> exact Z: fast-drive path) ==="
sqlite3 "$DB" <<'SQL'
UPDATE k_content_path SET path='Z:\mnt\wd_black\Kontakt Libraries\Custom\Audio Imperia - Sinfonia Drums'                         WHERE path='D:\PROGRAMS\VST, Samples & DAW\Audio Imperia - Sinfonia Drums';
UPDATE k_content_path SET path='Z:\mnt\btrfs_disk\Kontakt Libraries\Custom\Doru Malaia - Ethnic Super Drums Collection'         WHERE path='D:\PROGRAMS\VST, Samples & DAW\Doru Malaia - Ethnic Super Drums Collection';
UPDATE k_content_path SET path='Z:\mnt\btrfs_disk\Kontakt Libraries\Custom\Drumdrops - Vintage Funk Kit'                        WHERE path='D:\PROGRAMS\VST, Samples & DAW\Drumdrops - Vintage Funk Kit';
UPDATE k_content_path SET path='Z:\mnt\btrfs_disk\Kontakt Libraries\Player\Electro Acoustic'                                    WHERE path='D:\PROGRAMS\VST, Samples & DAW\Electro Acoustic';
UPDATE k_content_path SET path='Z:\mnt\btrfs_disk\Kontakt Libraries\Custom\Epic SoundLab - The Forge'                          WHERE path='D:\PROGRAMS\VST, Samples & DAW\Epic SoundLab - The Forge';
UPDATE k_content_path SET path='Z:\mnt\wd_black\Kontakt Libraries\Player\EWQL Colossus'                                        WHERE path='D:\PROGRAMS\VST, Samples & DAW\EWQL Colossus';
UPDATE k_content_path SET path='Z:\mnt\wd_black\Kontakt Libraries\Player\GetGood Drums - Modern and Massive Pack'              WHERE path='D:\PROGRAMS\VST, Samples & DAW\GetGood Drums - Modern and Massive Pack';
UPDATE k_content_path SET path='Z:\mnt\wd_black\Kontakt Libraries\Player\Kontakt Factory Library'                              WHERE path='D:\PROGRAMS\VST, Samples & DAW\Kontakt Factory Library';
UPDATE k_content_path SET path='Z:\mnt\btrfs_disk\Kontakt Libraries\Custom\PlugInGuru.MegaMagic.Bells.Winds.KONTAKT'          WHERE path='D:\PROGRAMS\VST, Samples & DAW\PlugInGuru.MegaMagic.Bells.Winds.KONTAKT';
UPDATE k_content_path SET path='Z:\mnt\btrfs_disk\Kontakt Libraries\Player\Session Guitarist - Electric Sunburst Deluxe'      WHERE path='D:\PROGRAMS\VST, Samples & DAW\Session Guitarist - Electric Sunburst Deluxe';
UPDATE k_content_path SET path='Z:\mnt\btrfs_disk\Kontakt Libraries\Player\Session Keys Electric R'                            WHERE path='D:\PROGRAMS\VST, Samples & DAW\Session Keys Electric R';
UPDATE k_content_path SET path='Z:\mnt\btrfs_disk\Kontakt Libraries\Custom\Sonic Mechanics - Classic Guitar Licks'            WHERE path='D:\PROGRAMS\VST, Samples & DAW\Sonic Mechanics - Classic Guitar Licks';
UPDATE k_content_path SET path='Z:\mnt\btrfs_disk\Kontakt Libraries\Custom\Sonic Mechanics - EDM Energy Drums'                WHERE path='D:\PROGRAMS\VST, Samples & DAW\Sonic Mechanics - EDM Energy Drums';
UPDATE k_content_path SET path='Z:\mnt\btrfs_disk\Kontakt Libraries\Custom\Sonic Mechanics - Future Cinematic FX'             WHERE path='D:\PROGRAMS\VST, Samples & DAW\Sonic Mechanics - Future Cinematic FX';
UPDATE k_content_path SET path='Z:\mnt\btrfs_disk\Kontakt Libraries\Custom\Sonic Mechanics - Tropical Trap'                   WHERE path='D:\PROGRAMS\VST, Samples & DAW\Sonic Mechanics - Tropical Trap';
UPDATE k_content_path SET path='Z:\mnt\btrfs_disk\Kontakt Libraries\Custom\String Audio - Alchemist Cinematic Impacts'        WHERE path='D:\PROGRAMS\VST, Samples & DAW\String Audio - Alchemist Cinematic Impacts';
SQL

echo "=== after Phase A: remaining D:\\PROGRAMS rows (should be 150 - 16 = 134) ==="
sqlite3 "$DB" "SELECT COUNT(*) FROM k_content_path WHERE path LIKE 'D:\PROGRAMS%';"

echo "=== Phase B: delete remaining D:\\PROGRAMS junk/duplicates + parent scan row ==="
sqlite3 "$DB" "DELETE FROM k_content_path WHERE path LIKE 'D:\PROGRAMS%' OR path='D:\VST Install\Kontakt Vst-i Folders';"

echo "=== AFTER ==="
echo -n 'total rows: '; sqlite3 "$DB" "SELECT COUNT(*) FROM k_content_path;"
sqlite3 "$DB" "SELECT id, path FROM k_content_path;" > /tmp/kcp_after.txt 2>/dev/null
echo -n 'Z: rows: ';  grep -icE '\|Z:' /tmp/kcp_after.txt
echo -n 'D: rows left (expect 0): '; grep -icE '\|D:' /tmp/kcp_after.txt
echo -n 'F: rows left: '; grep -icE '\|F:' /tmp/kcp_after.txt

echo
echo "NEXT: launch Kontakt, verify all real libs load from Z:, browser is clean."
echo "ROLLBACK (Kontakt closed):  cp -av \"$DB.pre_converge_$STAMP\" \"$DB\""
