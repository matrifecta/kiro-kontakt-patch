#!/usr/bin/env bash
# probe-wine-audio-path.sh (READ-ONLY) — pinpoint the Wine-side crackle now that device+graph are ruled out.
# Native audio is clean; only Wine/Kontakt crackles even on WineASIO@128 with no xruns. Gather:
#  1) Wine audio driver in the prefix registry (winepulse vs winealsa) — a post-update change here matters.
#  2) Any Wine sound reg overrides.
#  3) Recent pacman upgrades around the crackle onset (pipewire, wireplumber, ffmpeg, wine-staging, lib32-*).
#  4) The SSL node actual rate/period + whether a resampler/adapter sits in the chain (pw-dump).
set -u
PREFIX="${WINEPREFIX:-$HOME/.wine}"

echo "=== 1) Wine audio driver in registry ==="
grep -iE '"Audio"|Drivers' "$PREFIX/user.reg" "$PREFIX/system.reg" 2>/dev/null | grep -i audio | head
echo "  (HKCU\\Software\\Wine\\Drivers 'Audio' = pulse|alsa|...) — blank = default winepulse"
echo
echo "=== 2) winMM / DirectSound / wineasio overrides ==="
grep -iE 'wineasio|winepulse|winealsa|dsound' "$PREFIX/user.reg" 2>/dev/null | head

echo
echo "=== 3) recent package upgrades (crackle onset window) ==="
grep -iE "upgraded (pipewire|wireplumber|pipewire-jack|pipewire-pulse|ffmpeg|wine-staging|lib32-pipewire|libpipewire|alsa)" /var/log/pacman.log 2>/dev/null | tail -30

echo
echo "=== 4) SSL output node actual rate/period + any resampler in chain ==="
which pw-dump >/dev/null 2>&1 && pw-dump 2>/dev/null | grep -iE '"node.name"|"clock.rate"|"audio.rate"|"resample|"api.alsa.period-size"|"api.alsa.rate"' | grep -iE "SSL|resample|rate|period" | head -30
echo
echo "=== 5) is Wine opening a winepulse stream? (pactl sink-inputs while Kontakt plays) ==="
pactl list sink-inputs 2>/dev/null | grep -iE "application.name|Kontakt|wine|sample spec|resample" | head -20

echo
echo "READ-ONLY. Key questions: (a) is Wine 'Audio' driver pulse? (b) did pipewire/wireplumber/ffmpeg upgrade"
echo "right before the crackle? (c) is the SSL running a non-44100 rate forcing a resample? (d) is Kontakt"
echo "ALSO feeding a winepulse sink-input (dual path) alongside WineASIO?"
