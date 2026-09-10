#!/usr/bin/env bash
# probe-jack-vs-device.sh   (READ-ONLY, changes nothing)
# Goal: nail down the ACTUAL period/quantum on each layer of the WineASIO->JACK->SSL path,
# so we fix the RIGHT knob. We compare:
#   (a) PipeWire graph quantum (settings)          -> what the launcher forces (256)
#   (b) SSL ALSA device period-size / quantum      -> WirePlumber's per-device negotiation
#   (c) JACK node.latency the WineASIO client asks  -> the jack.conf.d drop-ins (64/44100)
#   (d) wireplumber + pipewire + wine versions      -> confirm the 0.5.17 change vector
# Nothing is written. Paste the whole output back.
set -u
echo "===== (a) PipeWire graph settings (live) ====="
pw-metadata -n settings 2>/dev/null | grep -iE "clock\.(rate|quantum|force)" || echo "(pw-metadata unavailable)"

echo
echo "===== (b) SSL 2 ALSA device nodes: props (period-size, quantum.limit, rate, latency) ====="
pw-dump 2>/tmp/pwdump.err > /tmp/pwdump.json
python3 - <<'PY'
import json
try:
    data=json.load(open("/tmp/pwdump.json"))
except Exception as e:
    print("(pw-dump parse failed:",e,"— stderr:", open("/tmp/pwdump.err").read()[:200],")"); raise SystemExit
import json,sys
try:
    data=json.load(sys.stdin)
except Exception as e:
    print("(pw-dump parse failed:",e,")"); sys.exit(0)
keys=("api.alsa.period-size","api.alsa.headroom","node.latency","clock.quantum",
      "audio.rate","node.rate","api.alsa.period-num","clock.name","node.name")
for o in data:
    p=(o.get("info") or {}).get("props") or {}
    name=p.get("node.name","")
    if "SSL_2" in name or "Solid_State_Logic" in name:
        print("---",name)
        for k in keys:
            if k in p: print("   %-24s = %s"%(k,p[k]))
PY

echo
echo "===== (c) JACK node.latency the WineASIO client will inherit (pw-jack view) ====="
pw-jack pw-metadata 2>/dev/null | grep -iE "clock\.(rate|quantum)" | head
echo "--- jack.conf.d drop-ins on disk ---"
for f in ~/.config/pipewire/jack.conf.d/*.conf; do
  echo "### $f"; cat "$f" 2>/dev/null; echo
done

echo
echo "===== (d) version vector (regression suspects) ====="
for pkg in wireplumber pipewire pipewire-jack wine-staging wine; do
  v=$(pacman -Q "$pkg" 2>/dev/null); [ -n "$v" ] && echo "  $v"
done
echo "--- wireplumber upgrade date (confirm 0.5.17 landed 09-08) ---"
grep -iE "upgraded wireplumber" /var/log/pacman.log 2>/dev/null | tail -3

echo
echo "===== (e) any live xruns right now? (2s sample) ====="
pw-top -b -n 2 2>/dev/null | grep -iE "SSL_2.*pro-(out|in)put-0|Kontakt|ERR" | tail -8
echo "(done — paste everything above)"
