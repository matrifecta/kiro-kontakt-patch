#!/usr/bin/env bash
# probe-loaded-vst3-origin.sh (READ-ONLY)
# Reaper log shows the LOADED Kontakt plugin is at ~/Prejemi/Yabridge_Windows/Kontakt 8 Portable.vst3,
# NOT the /mnt/workspace install tree. Kontakt Portable resolves its "installation directory" relative
# to where the actually-loaded plugin binary lives. Investigate that path + how yabridge is wired, so we
# point Kontakt at (or relink to) the correct install. NOTHING changed.
set -u
YW="/home/phnx/Prejemi/Yabridge_Windows"
YB="$HOME/.vst3/yabridge"
WSVST="/mnt/workspace/VST Install/Kontakt Portable/Kontakt 8/x64/VST3"

echo "===== 1) what is at ~/Prejemi/Yabridge_Windows ? ====="
if [ -d "$YW" ]; then
  ls -la "$YW" | sed 's/^/  /'
  echo "  Kontakt bundle contents:"
  find "$YW" -iname '*Kontakt*' 2>/dev/null | sed 's/^/    /' | head -20
else
  echo "  (absent) $YW"
fi
echo

echo "===== 2) is there a Kontakt 8.vst3plugin / install tree NEXT TO that loaded plugin? ====="
find "$YW" -maxdepth 4 -iname '*.vst3plugin' -o -iname 'Kontakt 8.exe' 2>/dev/null | sed 's/^/  /'
echo "  (if none here, this copy has NO install tree -> that's why 'installation directory not found')"
echo

echo "===== 3) how does yabridge map this? the bundle in ~/.vst3/yabridge ====="
ls -la "$YB" 2>/dev/null | grep -i kontakt | sed 's/^/  /'
KB="$YB/Kontakt 8 Portable.vst3"
if [ -d "$KB" ]; then
  echo "  inner win .vst3 target(s):"
  find "$KB" -iname '*.vst3' 2>/dev/null | sed 's/^/    /'
  echo "  what the inner win vst3 symlink points to:"
  find "$KB/Contents" -iname '*.vst3' -exec readlink -f {} \; 2>/dev/null | sed 's/^/    /'
fi
echo

echo "===== 4) the REAL install VST3 on workspace (where it SHOULD resolve from) ====="
ls -la "$WSVST" 2>/dev/null | sed 's/^/  /'
echo "  is 'Kontakt 8 Portable.vst3' here a FILE, DIR, or symlink?"
ls -ld "$WSVST/Kontakt 8 Portable.vst3" 2>/dev/null | sed 's/^/    /'
echo

echo "===== 5) does yabridge.toml or a yabridge symlink tie the loaded copy to the install? ====="
grep -niE 'Kontakt|Yabridge_Windows|workspace' "$HOME/.vst3/yabridge/yabridge.toml" 2>/dev/null | sed 's/^/  /'
echo
echo "READ-ONLY. Goal: confirm whether the loaded plugin at ~/Prejemi/Yabridge_Windows is a stray copy"
echo "with no install tree beside it (then we point yabridge back at the /mnt/workspace .vst3, which sits"
echo "next to the full Kontakt 8 install so it resolves)."
