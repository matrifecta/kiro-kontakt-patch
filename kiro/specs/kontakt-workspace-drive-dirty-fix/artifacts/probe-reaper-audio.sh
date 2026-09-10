#!/usr/bin/env bash
# probe-reaper-audio.sh   (READ-ONLY, changes nothing)
# Goal: see what Reaper's audio path actually runs at, and whether anything conflicts with the graph 128.
# Reaper talks PipeWire/JACK natively (no Wine/WASAPI), so it should be tight already. We check:
#   (a) is Reaper running? what device/quantum does its node report?
#   (b) graph forced quantum/rate right now
#   (c) SSL device + Reaper node QUANT/ERR under pw-top (any xruns while playing?)
#   (d) the reaper jack drop-in on disk (now 128/44100) vs what Reaper's node actually shows
#   (e) Reaper's own audio prefs from reaper.ini (jack buffer / request), if present
# RUN WHILE REAPER IS OPEN and ideally playing a Kontakt track. Paste all output.
set -u
echo "===== (a) Reaper process + its PipeWire/JACK nodes ====="
pgrep -a -f "[Rr]eaper" || echo "(Reaper not running — launch it first for full data)"
echo "--- PipeWire nodes that look like Reaper / its JACK client ---"
pw-cli ls Node 2>/dev/null | grep -iE "node.name|node.description|REAPER|reaper" | grep -iE "reaper" -A0 || echo "(none seen via pw-cli)"

echo
echo "===== (b) graph forced quantum/rate (should be 128 @ 44100) ====="
pw-metadata -n settings 2>/dev/null | grep -iE "clock\.(rate|quantum|force)" || echo "(pw-metadata unavailable)"

echo
echo "===== (c) pw-top: SSL + Reaper QUANT/ERR (are there xruns?) ====="
pw-top -b -n 4 2>/dev/null | grep -iE "SSL_2.*(in|out)put-0|REAPER|reaper|Kontakt" | tail -20
echo "(look at the QUANT column for the Reaper node and ERR — flat ERR = clean)"

echo
echo "===== (d) reaper jack drop-in on disk ====="
cat ~/.config/pipewire/jack.conf.d/99-reaper-latency.conf 2>/dev/null || echo "(missing)"

echo
echo "===== (e) Reaper's own audio config (reaper.ini) ====="
INI="$HOME/.config/REAPER/reaper.ini"
if [ -f "$INI" ]; then
  echo "--- [REAPER] audio/jack-related keys ---"
  grep -iE "^(jack_|audioconfig|dev_|reqsr|reqbs|buffer|asio|autobuf|sndoutdev|sndindev)" "$INI" | head -40
  echo "--- full [audioconfig]-ish lines ---"
  awk '/^\[/{s=$0} /jack|buf|samplerate|latency|dev/{print s"  "$0}' "$INI" | grep -iE "jack|buf|sample|latenc" | head -40
else
  echo "(reaper.ini not at $INI — tell me where Reaper stores config, or check ~/.config/REAPER/)"
fi

echo
echo "===== (f) is the SSL device itself capable of a smaller period? (theoretical headroom) ====="
echo "--- ALSA hw params for the SSL (period range the hardware allows) ---"
cat /proc/asound/card*/pcm0p/sub0/hw_params 2>/dev/null | head || echo "(not open / not playing)"
for c in /proc/asound/cards; do cat "$c" 2>/dev/null; done | grep -iE "SSL|Solid" || true
echo "(done — paste everything above)"
