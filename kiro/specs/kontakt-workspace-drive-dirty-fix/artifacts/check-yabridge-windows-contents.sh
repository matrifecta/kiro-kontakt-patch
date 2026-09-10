#!/usr/bin/env bash
# check-yabridge-windows-contents.sh (READ-ONLY)
# Before un-bridging ~/Prejemi/Yabridge_Windows, confirm the ONLY bridgeable plugin in it is the
# stray Kontakt copy (so removing the path from yabridge costs no other plugin). List every .vst3
# /.dll and whether any OTHER real plugin bundle lives there.
set -u
YW="/home/phnx/Prejemi/Yabridge_Windows"
echo "===== every .vst3 / .clap / .dll in $YW ====="
find "$YW" -maxdepth 2 \( -iname '*.vst3' -o -iname '*.clap' -o -iname '*.vst' \) 2>/dev/null | sed 's/^/  plugin: /'
echo
echo "  (DLLs are runtime deps, not plugins. Only .vst3/.clap/.vst bundles matter for yabridge.)"
echo
echo "===== is that Kontakt .vst3 the ONLY plugin yabridge synced from here? ====="
yabridgectl status 2>/dev/null | awk '/Yabridge_Windows/{p=1} p&&/::/{print "  "$0} /^\/|^ *\/mnt|^ *\/home\/phnx\/\.(vst|clap)/{if(p&&$0 !~ /Yabridge_Windows/)p=0}' | head
echo
echo "===== what the bridged bundle in ~/.vst3/yabridge points at (dangling if we remove source?) ====="
find "$HOME/.vst3/yabridge" -maxdepth 1 -iname '*Kontakt*' 2>/dev/null | sed 's/^/  /'
echo
echo "READ-ONLY. If the only plugin here is 'Kontakt 8 Portable.vst3', removing this path from"
echo "yabridge (yabridgectl rm) + sync un-bridges just the stray Kontakt; nothing else is affected."
