#!/usr/bin/env bash
#
# relocate-batch2-light-sdd1.sh
#
# BATCH 2: copy the LIGHT-STREAM libraries from Workspace HDD -> sdd1 (btrfs SSD).
# Defined as: every Workspace Kontakt Vst-i library that is NOT already handled
# (not on WD Black, not in the heavy set). Computed dynamically to avoid typos.
#
# rsync copy; Workspace originals kept as backup. Re-runnable + verified.
# Run with Kontakt CLOSED. This is the big one (HDD read-bound) -- may take a while.
#
set -u

WS="/mnt/workspace/VST Install/Kontakt Vst-i"
DST="/mnt/btrfs_disk/Kontakt VST-i"
WDDST="/mnt/wd_black/Kontakt VST-i"
TIXATI="/mnt/wd_black/TIXATI DL"
mkdir -p "$DST"

# Heavy set + New Century are on WD Black; exclude them from the light copy.
EXCLUDE=(
"Red Room Audio - Palette Symphonic Sketchpad"
"Mysteria Library"
"EWQL Colossus"
"Output Analog Strings KONTAKT"
"Evolution Series - World Percussion v2.0 Close Front Mics"
"Best Service - The Orchestra Complete"
"GetGood Drums - Modern and Massive Pack"
"Audio Imperia - Sinfonia Drums"
"Kontakt Factory Library"
"Kontakt Factory Selection 2 v1.2.0 [Native Instruments]"
"New Century Orchestral Series, The - Ensemble Strings [8Dio]"
)
is_excluded() { local n="$1"; for e in "${EXCLUDE[@]}"; do [ "$e" = "$n" ] && return 0; done; return 1; }

echo "=== free space BEFORE ==="; df -h /mnt/btrfs_disk; echo

shopt -s nullglob
count=0
for dir in "$WS"/*/; do
    name="$(basename "$dir")"
    # skip if excluded (heavy/WD Black), or already present on WD Black
    if is_excluded "$name"; then continue; fi
    if [ -e "$WDDST/$name" ] || [ -e "$TIXATI/$name" ]; then
        echo "ON WD BLACK (skip): $name"; continue
    fi
    echo "----- rsync -> sdd1: $name -----"
    rsync -a --info=progress2 "$WS/$name/" "$DST/$name/"
    count=$((count+1))
done
echo "Copied/updated $count light libraries to sdd1."

echo
echo "=== VERIFY (size compare WS vs sdd1) ==="
for dir in "$DST"/*/; do
    name="$(basename "$dir")"
    s=$(du -sb "$WS/$name" 2>/dev/null | cut -f1)
    d=$(du -sb "$DST/$name" 2>/dev/null | cut -f1)
    if [ "$s" = "$d" ]; then echo "OK   $name"; else echo "DIFF $name (src=$s dst=$d) -- re-run"; fi
done

echo
echo "=== free space AFTER ==="; df -h /mnt/btrfs_disk
echo "Workspace originals kept as backup until load-test passes."
