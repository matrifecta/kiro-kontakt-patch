#!/usr/bin/env bash
# probe-dot-names-and-alias.sh (READ-ONLY)
# PlugInGuru tile dir is structurally identical to the working Tropical Trap dir; only difference = the NAME
# has dots (.MegaMagic.Bells.Winds.KONTAKT). GetGood's image dir is named by .nicnt product name, not the db
# alias the browser shows. Two checks:
#  1) Do ANY of the currently-rendering NI image dirs contain a '.' in the name? If none do, dots are the
#     likely blocker for PlugInGuru.
#  2) For GetGood: is there ALSO a working type-2 lib whose image dir == its db alias (not product name)?
#     List the db alias vs the existing image dir names to see which key the browser uses.
set -u
NIIMG="/mnt/workspace/VST Install/Kontakt Portable/UserData/NI Resources/image"

echo "=== 1) NI image dir names that contain a dot ==="
ls -1 "$NIIMG" | grep -F '.' | sed 's/^/  DOT: /' || true
echo "  (count with dot: $(ls -1 "$NIIMG" | grep -Fc '.'))"
echo "  total image dirs: $(ls -1 "$NIIMG" | wc -l)"
echo
echo "=== 2) sample of image dir names (to see the naming style that works) ==="
ls -1 "$NIIMG" | head -30 | sed 's/^/  /'
echo
echo "READ-ONLY. If NO working image dir has a dot, rename PlugInGuru's dir to a dot-free variant that matches"
echo "the db alias Kontakt shows (we may also need to change the db alias to match). For GetGood, add an image"
echo "dir named EXACTLY as the db alias 'GetGood Drums - Modern and Massive Pack'."
