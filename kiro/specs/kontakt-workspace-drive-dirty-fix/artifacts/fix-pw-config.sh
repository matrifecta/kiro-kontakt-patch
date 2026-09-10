#!/usr/bin/env bash
# fix-pw-config.sh
# FOUND: a malformed drop-in named '10-lowlatency.conf}' (23 bytes, note the trailing '}' in the FILENAME) sits
# in ~/.config/pipewire/pipewire.conf.d/ next to the real 10-lowlatency.conf. PipeWire parses EVERY file in the
# dir, so this junk fragment (a shell-quoting mishap, dated sep 2 ~ update window) corrupts the config load.
# Fix: move the junk file aside (reversible), then restart the PipeWire stack so a clean config is read.
# (The good 10-lowlatency.conf pins 128; JACK drop-ins request 64 latency — that's fine once the junk is gone.)
set -u
MODE="${1:-dryrun}"
D="$HOME/.config/pipewire/pipewire.conf.d"
JUNK="$D/10-lowlatency.conf}"
BK="$D/_kiro_bad_$(date +%Y%m%d_%H%M%S)_10-lowlatency.conf.bad"

echo "=== fix pipewire config ==="
echo "  junk file: $JUNK"
if [ -f "$JUNK" ]; then
  echo "  contents of the junk file:"; sed 's/^/     /' "$JUNK"; echo "  size: $(stat -c '%s' "$JUNK") bytes"
else
  echo "  (junk file not found — maybe already cleaned)"
fi
echo "  good file kept: $D/10-lowlatency.conf"
echo
if [ "$MODE" != apply ]; then echo "DRY-RUN. Re-run: bash $0 apply"; exit 0; fi

if [ -f "$JUNK" ]; then
  mv -v "$JUNK" "$BK"
  echo "  moved junk aside -> $BK"
fi
echo
echo "=== restart PipeWire stack ==="
systemctl --user restart pipewire pipewire-pulse wireplumber 2>&1 | sed 's/^/  /'
sleep 2
echo "=== live settings after restart ==="
pw-metadata -n settings 2>/dev/null | grep -iE "clock.(rate|quantum|force)" | grep -v allowed
echo
echo "ROLLBACK: mv \"$BK\" \"$JUNK\"  (not recommended — it's malformed)"
echo "NEXT: relaunch Kontakt via launch_kontakt_wineasio.sh, WineASIO@128, test for crackle."
