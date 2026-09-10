#!/usr/bin/env bash
# show-jack-configs.sh (READ-ONLY) — dump the JACK/PipeWire low-latency drop-ins that govern the WineASIO path.
# WineASIO rides pipewire-jack, so jack.conf.d/*.conf is where its buffer/period is pinned. Also show the
# persistent pipewire quantum config + the LIVE jack settings the WineASIO client actually sees.
for f in \
  "$HOME/.config/pipewire/jack.conf.d/99-jack-44k.conf" \
  "$HOME/.config/pipewire/jack.conf.d/99-jack-latency.conf" \
  "$HOME/.config/pipewire/jack.conf.d/99-reaper-latency.conf" \
  "$HOME/.config/pipewire/pipewire.conf.d/10-lowlatency.conf" ; do
  echo "===== $f ====="
  if [ -f "$f" ]; then cat "$f"; else echo "(MISSING/empty)"; fi
  echo
done
echo "===== pipewire.conf.d listing ====="
ls -la "$HOME/.config/pipewire/pipewire.conf.d/" 2>/dev/null
echo
echo "===== jack.conf.d listing ====="
ls -la "$HOME/.config/pipewire/jack.conf.d/" 2>/dev/null
echo
echo "===== LIVE jack settings the WineASIO client sees (pw-jack) ====="
PIPEWIRE_LATENCY= pw-metadata -n settings 2>/dev/null | grep -iE "clock|jack" | head
echo
echo "===== is there a distro default 10-lowlatency in /usr that our update may have shadowed? ====="
ls -la /usr/share/pipewire/jack.conf.d/ 2>/dev/null; ls -la /usr/share/pipewire/pipewire.conf.d/ 2>/dev/null
