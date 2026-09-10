#!/usr/bin/env bash
#
# relocate-batch1-heavy-wdblack.sh
#
# BATCH 1: place the HEAVY-STREAM Workspace-only libraries onto WD Black NVMe.
# - New Century: already on WD Black (in TIXATI DL) -> same-drive mv (instant)
# - The rest: rsync COPY from Workspace HDD -> WD Black (originals kept as backup)
#
# rsync -a preserves attrs; --info=progress2 shows overall progress; re-runnable
# (skips already-copied). Verifies with a size compare at the end.
#
# Run with Kontakt CLOSED.
#
set -u

WS="/mnt/workspace/VST Install/Kontakt Vst-i"
DST="/mnt/wd_black/Kontakt VST-i"
TIXATI="/mnt/wd_black/TIXATI DL"
mkdir -p "$DST"

echo "=== free space BEFORE ==="; df -h /mnt/wd_black; echo

# 1) New Century: same-drive move from TIXATI DL (instant, no copy)
NC="New Century Orchestral Series, The - Ensemble Strings [8Dio]"
if [ -d "$TIXATI/$NC" ] && [ ! -e "$DST/$NC" ]; then
    echo "MV (instant): $NC"
    mv -n "$TIXATI/$NC" "$DST/$NC"
fi

# 2) Heavy Workspace-only libraries -> rsync copy to WD Black
HEAVY=(
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
)

for name in "${HEAVY[@]}"; do
    if [ ! -d "$WS/$name" ]; then echo "SRC MISSING (skip): $name"; continue; fi
    echo "----- rsync: $name -----"
    rsync -a --info=progress2 "$WS/$name/" "$DST/$name/"
done

echo
echo "=== VERIFY (size compare WS vs WD Black) ==="
for name in "${HEAVY[@]}"; do
    [ -d "$WS/$name" ] || continue
    s=$(du -sb "$WS/$name" 2>/dev/null | cut -f1)
    d=$(du -sb "$DST/$name" 2>/dev/null | cut -f1)
    if [ "$s" = "$d" ]; then echo "OK   $name"; else echo "DIFF $name  (src=$s dst=$d) -- re-run rsync"; fi
done

echo
echo "=== free space AFTER ==="; df -h /mnt/wd_black
echo "Workspace originals kept as backup until load-test passes."
