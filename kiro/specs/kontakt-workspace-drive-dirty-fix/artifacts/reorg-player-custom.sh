#!/usr/bin/env bash
#
# reorg-player-custom.sh
#
# For each fast drive, rename "Kontakt VST-i" -> "Kontakt Libraries" and sort
# every library into Player/ (has a .nicnt) or Custom/ (no .nicnt), by reading
# each library's actual contents. Same-drive mv = instant.
#
# EWQL RA is EXCLUDED (user skipping it): moved to an "_unused/" folder so it is
# out of the registration path but not deleted (delete manually if wanted).
#
# Safe/idempotent: skips libs already sorted; re-runnable. Run with Kontakt CLOSED.
#
set -u

DRIVES=(
"/mnt/wd_black"
"/mnt/btrfs_disk"
)

has_nicnt() {
    # Returns 0 if a .nicnt exists within depth 3 of the given dir
    find "$1" -maxdepth 3 -iname '*.nicnt' 2>/dev/null | grep -q . && return 0 || return 1
}

for base in "${DRIVES[@]}"; do
    OLD="$base/Kontakt VST-i"
    NEW="$base/Kontakt Libraries"

    # Rename root if needed (only if OLD exists and NEW doesn't yet)
    if [ -d "$OLD" ] && [ ! -d "$NEW" ]; then
        echo "RENAME: $OLD -> $NEW"
        mv "$OLD" "$NEW"
    fi
    # If neither exists, skip this drive
    [ -d "$NEW" ] || { echo "SKIP (no library folder on $base)"; continue; }

    mkdir -p "$NEW/Player" "$NEW/Custom" "$NEW/_unused"
    echo "=== Sorting libraries under $NEW ==="

    shopt -s nullglob
    for dir in "$NEW"/*/; do
        name="$(basename "$dir")"
        # don't process our own target subfolders
        case "$name" in
            Player|Custom|_unused) continue ;;
        esac

        # EWQL RA -> _unused (user skipping)
        if [ "$name" = "EWQL RA" ]; then
            echo "UNUSED (EWQL RA, skipped): -> _unused/"
            mv -n "$dir" "$NEW/_unused/$name"
            continue
        fi

        if has_nicnt "$dir"; then
            echo "PLAYER: $name"
            mv -n "$dir" "$NEW/Player/$name"
        else
            echo "CUSTOM: $name"
            mv -n "$dir" "$NEW/Custom/$name"
        fi
    done

    echo
    echo "--- $NEW/Player ---"; ls -1 "$NEW/Player" 2>/dev/null | wc -l; echo "libs"
    echo "--- $NEW/Custom ---"; ls -1 "$NEW/Custom" 2>/dev/null | wc -l; echo "libs"
    echo "--- $NEW/_unused ---"; ls -1 "$NEW/_unused" 2>/dev/null
    echo
done

echo "=== DONE. Final structure: ==="
for base in "${DRIVES[@]}"; do
    echo "### $base/Kontakt Libraries"
    echo "  Player:"; ls -1 "$base/Kontakt Libraries/Player" 2>/dev/null | sed 's/^/    /'
    echo "  Custom:"; ls -1 "$base/Kontakt Libraries/Custom" 2>/dev/null | sed 's/^/    /'
done
