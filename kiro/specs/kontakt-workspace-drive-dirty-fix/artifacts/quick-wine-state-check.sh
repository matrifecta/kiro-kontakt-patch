#!/usr/bin/env bash
# quick-wine-state-check.sh (READ-ONLY) — cheap checks before deep tracing.
set -u
WPREF="$HOME/.wine"
KP="/mnt/workspace/VST Install/Kontakt Portable"

echo "===== 1) is /mnt/workspace actually mounted right now? ====="
if mountpoint -q /mnt/workspace; then
  echo "  MOUNTED: $(findmnt -no SOURCE,FSTYPE /mnt/workspace 2>/dev/null)"
else
  echo "  *** NOT MOUNTED *** — this alone would cause 'installation directory not found'!"
fi
echo

echo "===== 2) can we actually read the plugin file through the path Kontakt uses? ====="
F="$KP/Kontakt 8/x64/Kontakt 8.vst3plugin"
[ -r "$F" ] && echo "  readable via /mnt path: yes ($(stat -c '%s' "$F") bytes)" || echo "  NOT readable via /mnt path"
# and via the Z: dosdevice (what Kontakt config uses)
ZF="$WPREF/dosdevices/z:/mnt/workspace/VST Install/Kontakt Portable/Kontakt 8/x64/Kontakt 8.vst3plugin"
[ -r "$ZF" ] && echo "  readable via Z: dosdevice: yes" || echo "  NOT readable via Z: dosdevice ($ZF)"
echo

echo "===== 3) did the wine prefix version bump (first-run reconfigure)? ====="
ls -la "$WPREF/.update-timestamp" 2>/dev/null | sed 's/^/  /'
echo "  system.reg mtime:"; ls -la "$WPREF/system.reg" 2>/dev/null | sed 's/^/    /'
echo "  (if these changed today, new wine reconfigured the prefix)"
echo

echo "===== 4) the .vst3 bundle yabridge exposes to Reaper — still present & linked? ====="
ls -la "$HOME/.vst3/yabridge/" 2>/dev/null | grep -iE 'kontakt' | sed 's/^/  /'
echo "  bundle target:"
find "$HOME/.vst3/yabridge" -iname '*Kontakt*' 2>/dev/null | sed 's/^/    /' | head
echo

echo "===== 5) is d:/f:/z: still resolving? (quick) ====="
for l in d z f; do
  t="$(readlink -f "$WPREF/dosdevices/$l:" 2>/dev/null)"
  echo "  $l: -> $t  $( [ -d "$t" ] && echo '(ok)' || echo '(BROKEN)')"
done
echo
echo "READ-ONLY."
