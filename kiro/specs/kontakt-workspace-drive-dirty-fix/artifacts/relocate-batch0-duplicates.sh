#!/usr/bin/env bash
#
# relocate-batch0-duplicates.sh
#
# BATCH 0 (instant, same-drive): consolidate the 14 duplicate libraries that
# already live on WD Black under "TIXATI DL/" into a clean "Kontakt VST-i/"
# folder. Same-filesystem `mv` = near-instant, uses no extra space.
#
# Safe: these are the confirmed duplicates (also present on Workspace, which
# stays untouched as backup). Nothing is deleted; just moved within WD Black.
#
# Run with Kontakt CLOSED. Review the echoed plan; it moves only known names.
#
set -u

SRC="/mnt/wd_black/TIXATI DL"
DST="/mnt/wd_black/Kontakt VST-i"

mkdir -p "$DST"

# The 14 duplicates (exact folder names as they exist in TIXATI DL)
DUPES=(
"Anthology Strings [8Dio]"
"Big Fish Audio - Vibe Guitars"
"Deep Pool - Modern Downtempo Drums [In Session Audio]"
"Elements - Kepler [Zero-G]"
"Extinction Level Event - Master Kit"
"Kontakt Factory Library 2 v1.4.0 [Native Instruments]"
"Majestica Professional 2.0 [8Dio]"
"Misfit Banjo [8Dio]"
"Moroccan Vocal Phrases [Sonuscore]"
"Pianet Ad Astra [Past to Future Reverbs]"
"Puremagnetik - Onda"
"Soundiron Alpha Organ"
"Soundiron - Sandy Creek Organ"
"Zen Garden, The 1.1.2 [Fluffy Audio]"
)

echo "=== BATCH 0: consolidate ${#DUPES[@]} duplicates within WD Black ==="
for name in "${DUPES[@]}"; do
    if [ -d "$SRC/$name" ]; then
        if [ -e "$DST/$name" ]; then
            echo "SKIP (already in dest): $name"
        else
            echo "MOVE: $name"
            mv -n "$SRC/$name" "$DST/$name"
        fi
    else
        echo "NOT FOUND in TIXATI DL (skip): $name"
    fi
done

echo
echo "=== Result: contents of $DST ==="
ls -1 "$DST"
echo
echo "=== Whatever remains in $SRC (non-duplicate leftovers to review later) ==="
ls -1 "$SRC" 2>/dev/null
echo
echo "=== free space after ==="
df -h /mnt/wd_black
