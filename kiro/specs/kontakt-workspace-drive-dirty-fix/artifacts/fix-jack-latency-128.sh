#!/usr/bin/env bash
# fix-jack-latency-128.sh
# CONTEXT: after aligning the graph quantum 256->128 (fix-quantum-128.sh), Kontakt ERR went flat (~7)
# and the crackle is mostly gone. Residual pressure remains on the SSL INPUT node (id 66): QUANT 128 but
# ERR ~278 and high WAIT. Cause: the three jack.conf.d drop-ins request node.latency = 64/44100 (a 64-frame
# target) while the graph + Kontakt run 128 -> a smaller 128-vs-64 mismatch on the JACK/input path. The 64
# request buys nothing here (working buffer is 128) and reintroduces a split.
# FIX: rewrite node.latency 64/44100 -> 128/44100 in the three drop-ins so JACK matches the 128 graph.
# Reversible: each edited file is backed up; rollback restores them.
set -u
MODE="${1:-dryrun}"
STAMP="$(date +%Y%m%d_%H%M%S)"
FILES=(
  "$HOME/.config/pipewire/jack.conf.d/99-jack-44k.conf"
  "$HOME/.config/pipewire/jack.conf.d/99-jack-latency.conf"
  "$HOME/.config/pipewire/jack.conf.d/99-reaper-latency.conf"
)

echo "=== align JACK node.latency 64/44100 -> 128/44100 (SSL input still xrunning at 64 target) ==="
for f in "${FILES[@]}"; do
  echo "--- $f (current) ---"
  grep -nE "node\.latency" "$f" 2>/dev/null || echo "   (no node.latency line / file missing)"
done

if [ "$MODE" != apply ]; then
  echo
  echo "DRY-RUN. Would back up each file to <file>.bak_${STAMP} and change 64/44100 -> 128/44100."
  echo "Re-run: bash $0 apply"
  exit 0
fi

echo
for f in "${FILES[@]}"; do
  [ -f "$f" ] || { echo "skip (missing): $f"; continue; }
  cp "$f" "${f}.bak_${STAMP}"
  sed -i 's#node\.latency = 64/44100#node.latency = 128/44100#g' "$f"
  echo "edited: $f   (backup ${f}.bak_${STAMP})"
  grep -nE "node\.latency" "$f"
done

echo
echo "=== restart PipeWire stack so JACK picks up the new latency ==="
systemctl --user restart pipewire pipewire-pulse wireplumber 2>&1 | sed 's/^/  /'
sleep 2
echo "done."
echo
echo "ROLLBACK (all three): for f in ${FILES[*]}; do cp \"\${f}.bak_${STAMP}\" \"\$f\"; done; systemctl --user restart pipewire pipewire-pulse wireplumber"
echo
echo "NEXT:"
echo "  1) wineserver -k; bash \"/home/phnx/KIRO/launch_kontakt_wineasio.sh\""
echo "  2) play; then: pw-top -b -n 4 | grep -iE 'SSL_2.*input|Kontakt'"
echo "     SUCCESS = SSL input ERR stops climbing (was ~278) and the residual crackle clears by ear."
