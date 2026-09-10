#!/usr/bin/env bash
#
# launch_kontakt_lowlatency.sh
#
# Forces the PipeWire graph to a 128-sample quantum @ 44.1kHz, launches the
# Kontakt 8 portable standalone under Wine, and restores the previous quantum
# behaviour on exit.
#
# Notes:
# - PipeWire is pinned to 128 BEFORE Kontakt starts so its WASAPI negotiation
#   sees a 128 graph. (Kontakt's own WASAPI Shared-mode node may still report a
#   larger buffer; this forces the graph side as low as possible.)
# - Restores clock.force-quantum to 0 when Kontakt closes.

set -u

KONTAKT_DIR="/mnt/workspace/VST Install/Kontakt Portable/Kontakt 8/x64"
KONTAKT_EXE="Kontakt 8.exe"
QUANTUM=128
RATE=44100

WINE_OVERRIDES="*api-ms-win-core*=b;*msvcp140*=b;*vcruntime140*=b"

# Wine uses the PulseAudio backend (winepulse) -> PipeWire's pulse emulation.
# The Kontakt/WASAPI 236-sample buffer is dictated by this path, NOT by the PipeWire
# graph quantum. PULSE_LATENCY_MSEC is the lever that can actually influence it.
# Lower = tighter latency but higher xrun risk. Try 8, then 6, then 4. Empty = leave default.
PULSE_LATENCY_MSEC_VALUE="8"

# Ensure the F: Wine drive letter exists (baked into some preset/artwork paths).
# The dosdevices symlink does not persist across reboots, so recreate it if missing.
DOSDEV="$HOME/.wine/dosdevices"
if [ ! -e "${DOSDEV}/f:" ]; then
    echo "[lowlatency] F: drive missing -> recreating f: -> /mnt/workspace"
    ln -s /mnt/workspace "${DOSDEV}/f:" 2>/dev/null
fi

echo "[lowlatency] forcing PipeWire quantum ${QUANTUM} @ ${RATE}Hz ..."
pw-metadata -n settings 0 clock.force-rate    "${RATE}"    >/dev/null 2>&1
pw-metadata -n settings 0 clock.force-quantum "${QUANTUM}" >/dev/null 2>&1

# Show what actually took effect.
echo "[lowlatency] active settings:"
pw-metadata -n settings 2>/dev/null | grep -E "clock.(force-)?(rate|quantum)" || true

# Restore auto behaviour when this script exits (Kontakt closed).
cleanup() {
    echo "[lowlatency] restoring PipeWire auto quantum/rate ..."
    pw-metadata -n settings 0 clock.force-quantum 0 >/dev/null 2>&1
    pw-metadata -n settings 0 clock.force-rate    0 >/dev/null 2>&1
}
trap cleanup EXIT

echo "[lowlatency] launching Kontakt (PULSE_LATENCY_MSEC=${PULSE_LATENCY_MSEC_VALUE:-default}) ..."
cd "${KONTAKT_DIR}" || { echo "[lowlatency] ERROR: cannot cd to ${KONTAKT_DIR}"; exit 1; }
if [ -n "${PULSE_LATENCY_MSEC_VALUE}" ]; then
    PULSE_LATENCY_MSEC="${PULSE_LATENCY_MSEC_VALUE}" WINEDLLOVERRIDES="${WINE_OVERRIDES}" wine "${KONTAKT_EXE}"
else
    WINEDLLOVERRIDES="${WINE_OVERRIDES}" wine "${KONTAKT_EXE}"
fi

# When wine returns (Kontakt closed), trap runs cleanup.
echo "[lowlatency] Kontakt exited."
