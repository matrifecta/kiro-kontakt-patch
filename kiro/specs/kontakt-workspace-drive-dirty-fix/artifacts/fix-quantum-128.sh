#!/usr/bin/env bash
# fix-quantum-128.sh
# EVIDENCE (probe-jack-vs-device.sh section e):
#   SSL input node (id 66) = QUANT 256, ERR 228 (xruns = the crackle)
#   Kontakt node   (id 102) = QUANT 128, ERR 3
#   graph force-quantum     = 256   <- set by launch_kontakt_wineasio.sh (QUANTUM=256)
# The launcher forces the GRAPH to 256, but WineASIO/Kontakt run their ASIO buffer at 128
# (your known-good "128 samples" state). The SSL INPUT is the only node dragged to 256 and
# it xruns against the 128 Kontakt clock -> crackle. Before the wireplumber 0.5.15->0.5.17
# upgrade (2026-09-08) this split negotiated cleanly; 0.5.17 no longer reconciles it.
# FIX: align the forced graph quantum to 128 so the SSL input matches Kontakt (no split).
# This restores your documented working "128 samples" endpoint. Reversible (backup + rollback).
set -u
MODE="${1:-dryrun}"
LAUNCHER="/home/phnx/KIRO/launch_kontakt_wineasio.sh"
STAMP="$(date +%Y%m%d_%H%M%S)"
BAK="${LAUNCHER}.bak_${STAMP}"

echo "=== align WineASIO graph quantum 256 -> 128 (kill SSL-input xruns) ==="
echo "  launcher: $LAUNCHER"

if ! grep -qE '^QUANTUM=256' "$LAUNCHER"; then
  echo "  NOTE: launcher does not currently have 'QUANTUM=256'. Current value:"
  grep -nE '^QUANTUM=' "$LAUNCHER" || echo "   (no QUANTUM= line found)"
fi

echo
echo "--- current QUANTUM line ---"
grep -nE '^QUANTUM=' "$LAUNCHER"

if [ "$MODE" != apply ]; then
  echo
  echo "DRY-RUN. Would: cp \"$LAUNCHER\" \"$BAK\"  then set QUANTUM=128"
  echo "Re-run: bash $0 apply"
  exit 0
fi

cp "$LAUNCHER" "$BAK"
echo "backup: $BAK"
sed -i 's/^QUANTUM=256/QUANTUM=128/' "$LAUNCHER"
echo "--- new QUANTUM line ---"
grep -nE '^QUANTUM=' "$LAUNCHER"
echo
echo "ROLLBACK: cp \"$BAK\" \"$LAUNCHER\""
echo
echo "NEXT:"
echo "  1) wineserver -k"
echo "  2) bash \"$LAUNCHER\""
echo "  3) in Kontakt keep WineASIO @128 (Fixed buffersize UNCHECKED, buffer 128 — unchanged)"
echo "  4) play; then in another terminal: pw-top -b -n 3 | grep -iE 'SSL_2.*input|Kontakt'"
echo "     SUCCESS = SSL input now QUANT 128 and ERR stops climbing (was 228)."
