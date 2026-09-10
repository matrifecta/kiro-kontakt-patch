#!/usr/bin/env bash
# fix-reaper-rtprio.sh
# CONTEXT: Reaper runs Kontakt as .so on the native PipeWire/JACK path — already glass-smooth, ERR 0, huge
# headroom (BUSY ~130us vs ~2900us budget @ 128/44100). The ONE robustness improvement available is giving
# Reaper's audio thread a real realtime priority. reaper.ini currently has jack_rtprio=-1 (NOT requesting RT).
# Under a heavy project a non-RT audio thread can be preempted -> dropouts. Setting jack_rtprio=88 hardens it
# for heavy sessions. 88 sits safely below PipeWire/WirePlumber (typically 88-95) and the kernel RT watchdog,
# so Reaper won't starve the audio server. This does NOT change idle sound quality (already optimal); it's
# insurance under load. Reaper must be CLOSED (it reads reaper.ini at startup). Reversible: backup + rollback.
set -u
MODE="${1:-dryrun}"
INI="$HOME/.config/REAPER/reaper.ini"
STAMP="$(date +%Y%m%d_%H%M%S)"
BAK="${INI}.bak_${STAMP}"
NEWPRIO=88

echo "=== Reaper audio-thread realtime priority: jack_rtprio -1 -> ${NEWPRIO} ==="
echo "  file: $INI"

if [ ! -f "$INI" ]; then echo "ERROR: $INI not found"; exit 1; fi

if pgrep -x reaper >/dev/null 2>&1 || pgrep -f "/REAPER/reaper" >/dev/null 2>&1; then
  echo "WARNING: Reaper appears to be RUNNING. Close it first (it reads reaper.ini at startup and rewrites"
  echo "         it on exit, which would overwrite this edit). Aborting to be safe."
  exit 1
fi

echo
echo "--- current line ---"
grep -nE "^jack_rtprio=" "$INI" || echo "   (no jack_rtprio= line found)"

echo
echo "===== realtime-priority limit check (does your user get to request RT ${NEWPRIO}?) ====="
echo "--- soft/hard rtprio ulimit for this shell ---"
ulimit -Hr 2>/dev/null | sed 's/^/  hard rtprio: /'
ulimit -Sr 2>/dev/null | sed 's/^/  soft rtprio: /'
echo "--- limits.d / pam rtprio grants (need >= ${NEWPRIO} for @audio or your user) ---"
grep -rIiE "rtprio" /etc/security/limits.conf /etc/security/limits.d/ 2>/dev/null | sed 's/^/  /' || echo "  (no explicit rtprio grant found in limits.conf/limits.d)"
echo "--- are you in the 'audio'/'realtime' group? ---"
id -nG 2>/dev/null | tr ' ' '\n' | grep -iE "^(audio|realtime|pipewire)$" | sed 's/^/  member of: /' || echo "  (not in audio/realtime group — RT grant may rely on a limits.d drop-in instead)"

if [ "$MODE" != apply ]; then
  echo
  echo "DRY-RUN. Would: cp \"$INI\" \"$BAK\"  then set jack_rtprio=${NEWPRIO}"
  echo "Re-run: bash $0 apply"
  echo
  echo "NOTE: if the hard rtprio limit above is < ${NEWPRIO} (or 0), Reaper will ask for RT ${NEWPRIO} but the"
  echo "system will deny it and Reaper falls back to non-RT (no harm, no benefit). In that case the real fix is"
  echo "a limits.d grant (I can prepare it) — but many audio distros (CachyOS) already grant 95 to @audio."
  exit 0
fi

cp "$INI" "$BAK"
echo "backup: $BAK"
if grep -qE "^jack_rtprio=" "$INI"; then
  sed -i "s/^jack_rtprio=.*/jack_rtprio=${NEWPRIO}/" "$INI"
else
  # insert under the [reaper] section header if the key is absent
  sed -i "0,/^\[reaper\]/s//[reaper]\njack_rtprio=${NEWPRIO}/" "$INI"
fi
echo "--- new line ---"
grep -nE "^jack_rtprio=" "$INI"
echo
echo "ROLLBACK: cp \"$BAK\" \"$INI\"    (with Reaper closed)"
echo
echo "NEXT:"
echo "  1) launch Reaper: QT_QPA_PLATFORM=xcb reaper"
echo "  2) load a Kontakt track, play; in another terminal:"
echo "     pw-top -b -n 4 | grep -iE 'REAPER|SSL_2.*input'"
echo "  3) VERIFY Reaper actually GOT realtime: check its thread priorities ->"
echo "     for p in \$(pgrep -f /REAPER/reaper); do ps -L -o pid,tid,cls,rtprio,comm -p \$p; done | grep -iE 'FF|RR|rtprio' | head"
echo "     SUCCESS = the audio thread shows cls=FF or RR with rtprio ~${NEWPRIO} (was TS/ - = timeshare/none)."
echo "  If rtprio stays blank/TS, the system denied RT -> tell me and I'll prepare a limits.d grant."
