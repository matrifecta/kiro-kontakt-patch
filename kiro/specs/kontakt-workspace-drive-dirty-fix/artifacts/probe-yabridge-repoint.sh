#!/usr/bin/env bash
# probe-yabridge-repoint.sh (READ-ONLY)
# Loaded Kontakt = install-less copy at ~/Prejemi/Yabridge_Windows (v8.11.0 dlls, dated today),
# yabridge bundle's win vst3 -> that copy. Real install .vst3 is on /mnt/workspace next to full tree.
# Before re-pointing yabridge, inspect: the Settings.ini in that folder (may set an install dir),
# the exact yabridge bundle symlink layout, and whether the workspace copy is the SAME plugin version.
set -u
YW="/home/phnx/Prejemi/Yabridge_Windows"
KB="$HOME/.vst3/yabridge/Kontakt 8 Portable.vst3"
WS="/mnt/workspace/VST Install/Kontakt Portable/Kontakt 8/x64/VST3/Kontakt 8 Portable.vst3"

echo "===== 1) Settings.ini beside the loaded copy (may point at an install dir) ====="
for s in "$YW/Settings.ini" "$(dirname "$WS")/Settings.ini"; do
  echo "--- $s ---"; [ -f "$s" ] && sed 's/^/    /' "$s" || echo "    (none)"
done
echo

echo "===== 2) version compare: loaded copy vs workspace copy ====="
echo "  loaded  : $(ls -la "$YW/Kontakt 8 Portable.vst3" 2>/dev/null | awk '{print $5, $6,$7,$8}')  (ktp: $(ls "$YW"/ktp*.dll 2>/dev/null | xargs -n1 basename))"
echo "  workspace: $(ls -la "$WS" 2>/dev/null | awk '{print $5, $6,$7,$8}')"
echo "  workspace x64 runtime dll: $(ls "$(dirname "$(dirname "$WS")")"/ktp*.dll 2>/dev/null | xargs -n1 basename)"
echo "  (loaded is v8.11.0 = ktp8110.dll; workspace install exe was Kontakt 8.exe sep 2024 = ktp801.dll = v8.0.1?)"
echo

echo "===== 3) yabridge bundle symlink layout (what we'd re-point) ====="
find "$KB" -maxdepth 4 \( -type l -o -type f \) 2>/dev/null -printf '  %y %p -> %l\n' 2>/dev/null | sed 's/ -> $//'
echo

echo "===== 4) is the workspace VST3 a plain file (yabridge needs a path it can bridge)? ====="
ls -ld "$WS" 2>/dev/null | sed 's/^/  /'
echo

echo "===== 5) how was yabridge told about ~/Prejemi/Yabridge_Windows? (yabridge sync dirs) ====="
yabridgectl status 2>/dev/null | sed 's/^/  /' || echo "  (yabridgectl not found / not in PATH)"
echo
echo "READ-ONLY. Key question this answers: is the loaded copy a NEWER standalone Kontakt (v8.11.0) with"
echo "no install tree, while the workspace install is an OLDER version (v8.0.x)? If so, re-pointing to the"
echo "workspace .vst3 loads the version that HAS an install tree — but confirm versions match your libs first."
