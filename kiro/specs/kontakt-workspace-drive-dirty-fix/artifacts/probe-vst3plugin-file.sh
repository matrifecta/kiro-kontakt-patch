#!/usr/bin/env bash
# probe-vst3plugin-file.sh (READ-ONLY)
# Kontakt keeps reporting missing: \Kontakt 8.vst3plugin  (note leading backslash, exact name).
# Find EVERY copy of that exact file, and every *.vst3plugin/*.exe under the portable tree,
# so we know exactly which folder to point at (the one DIRECTLY containing 'Kontakt 8.vst3plugin').
set -u
KP="/mnt/workspace/VST Install/Kontakt Portable"

echo "===== every 'Kontakt 8.vst3plugin' under the portable tree ====="
find "$KP" -iname 'Kontakt 8.vst3plugin' 2>/dev/null | sed 's/^/  /'
echo
echo "===== every *.vst3plugin (any name) ====="
find "$KP" -iname '*.vst3plugin' 2>/dev/null -exec ls -la {} \; | sed 's/^/  /'
echo
echo "===== every Kontakt*.exe ====="
find "$KP" -iname 'Kontakt*.exe' 2>/dev/null -exec ls -la {} \; | sed 's/^/  /'
echo
echo "===== the x64 dir: does it directly contain the file the alert names? ====="
X="$KP/Kontakt 8/x64"
if [ -e "$X/Kontakt 8.vst3plugin" ]; then
  echo "  YES: $X/Kontakt 8.vst3plugin exists"
  ls -la "$X/Kontakt 8.vst3plugin" | sed 's/^/    /'
else
  echo "  NO: not directly in $X"
fi
echo
echo "===== is the file readable & non-zero (not a broken symlink / partial)? ====="
F="$X/Kontakt 8.vst3plugin"
[ -r "$F" ] && echo "  readable: yes" || echo "  readable: NO"
[ -s "$F" ] && echo "  non-empty: yes ($(stat -c '%s' "$F" 2>/dev/null) bytes)" || echo "  EMPTY/missing"
echo
echo "===== full listing of x64 top level (confirm exact filename spelling) ====="
ls -la "$X" | grep -iE 'vst3plugin|\.exe|ktp' | sed 's/^/  /'
echo
echo "READ-ONLY. The folder to select is the one DIRECTLY holding 'Kontakt 8.vst3plugin'."
