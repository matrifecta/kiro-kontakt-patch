#!/usr/bin/env bash
# fix-ssl-period.sh
# ROOT CAUSE (evidence-backed): the SSL 2 ALSA node runs api.alsa.period-size=256 while the PipeWire graph +
# WineASIO run at quantum 128 -> device/graph period mismatch = crackle on the WineASIO/JACK path. Native audio
# is clean because it tolerates the mismatch; WineASIO/JACK does not. Timeline: wireplumber 0.5.15->0.5.17 on
# 2026-09-08 (day before the crackle) — the WP upgrade changed per-device period negotiation so the SSL no longer
# comes up at 128. The pipewire graph-quantum config pins the GRAPH, not the DEVICE ALSA period (WirePlumber's job).
# FIX: add a WirePlumber ALSA rule forcing the SSL 2 node to period 128 @ 44100 (api.alsa.period-size=128,
# headroom, and node.latency 128/44100). Reversible (file drop-in). Restart WP to apply.
set -u
MODE="${1:-dryrun}"
WPDIR="$HOME/.config/wireplumber/wireplumber.conf.d"
CONF="$WPDIR/99-ssl2-128period.conf"

echo "=== fix SSL2 ALSA period -> 128 (WirePlumber rule) ==="
echo "  target file: $CONF"
echo "  (matches the SSL 2 alsa card; sets period-size 128, quantum 128, rate 44100)"

read -r -d '' BODY <<'EOF'
# Force SSL 2 (Solid State Logic SSL 2+) to a 128-frame ALSA period @ 44100 so the device matches the
# PipeWire graph / WineASIO quantum (fixes crackle after the wireplumber 0.5.17 upgrade which changed
# per-device period negotiation and let the SSL come up at period-size 256).
monitor.alsa.rules = [
  {
    matches = [
      { node.name = "~alsa_output.usb-Solid_State_Logic_SSL_2.*" }
      { node.name = "~alsa_input.usb-Solid_State_Logic_SSL_2.*" }
    ]
    actions = {
      update-props = {
        audio.rate               = 44100
        api.alsa.period-size     = 128
        api.alsa.headroom        = 128
        node.latency             = "128/44100"
        session.suspend-timeout-seconds = 0
      }
    }
  }
]
EOF

if [ "$MODE" != apply ]; then
  echo; echo "--- would write ---"; echo "$BODY"
  echo; echo "DRY-RUN. Re-run: bash $0 apply"; exit 0
fi

mkdir -p "$WPDIR"
printf '%s\n' "$BODY" > "$CONF"
echo "wrote $CONF"
echo "=== restart WirePlumber (+ pipewire) ==="
systemctl --user restart wireplumber 2>&1 | sed 's/^/  /'
sleep 2
echo "=== verify SSL period now ==="
pw-dump 2>/dev/null | grep -A2 -iE '"node.name": "alsa_(out|in)put.usb-Solid_State_Logic_SSL_2' | grep -iE "node.name|period-size" | head
echo
echo "ROLLBACK: rm \"$CONF\"; systemctl --user restart wireplumber"
echo "NEXT: wineserver -k; relaunch launch_kontakt_wineasio.sh; the SSL should now be period 128 = no crackle."
