#!/usr/bin/env bash
#
# launch_kontakt_wineasio.sh
#
# Launches Kontakt 8 portable under Wine through pw-jack so the registered
# WineASIO driver binds to PipeWire's JACK backend. Select "WineASIO" in
# Kontakt's Audio panel; the ASIO buffer is then directly settable (128 etc.),
# bypassing the WASAPI/winepulse 236 ceiling.
#
# Prereq: WineASIO registered in the prefix (see progress-notes.md).

set -u

KONTAKT_DIR="/mnt/workspace/VST Install/Kontakt Portable/Kontakt 8/x64"
KONTAKT_EXE="Kontakt 8.exe"
WINE_OVERRIDES="*api-ms-win-core*=b;*msvcp140*=b;*vcruntime140*=b;wineasio64=b"

# Ensure the F: Wine drive letter exists (baked into some preset/artwork paths).
# The dosdevices symlink does not persist across reboots, so recreate it if missing.
DOSDEV="$HOME/.wine/dosdevices"
if [ ! -e "${DOSDEV}/f:" ]; then
    echo "[wineasio] F: drive missing -> recreating f: -> /mnt/workspace"
    ln -s /mnt/workspace "${DOSDEV}/f:" 2>/dev/null
fi

# Optionally pin the PipeWire graph quantum for consistent low latency.
# 128 = lowest latency but can crackle/xrun on heavy multi-voice streaming libs
# (e.g. Extinction Level, big orchestras). Raise to 256 (or 512) if you hear
# crackling; lower back to 128 for light patches / lowest latency tracking.
QUANTUM=128
RATE=44100
echo "[wineasio] forcing PipeWire quantum ${QUANTUM} @ ${RATE}Hz ..."
pw-metadata -n settings 0 clock.force-rate    "${RATE}"    >/dev/null 2>&1
pw-metadata -n settings 0 clock.force-quantum "${QUANTUM}" >/dev/null 2>&1

cleanup() {
    echo "[wineasio] restoring PipeWire auto quantum/rate ..."
    pw-metadata -n settings 0 clock.force-quantum 0 >/dev/null 2>&1
    pw-metadata -n settings 0 clock.force-rate    0 >/dev/null 2>&1
}
trap cleanup EXIT

echo "[wineasio] launching Kontakt via pw-jack ..."
cd "${KONTAKT_DIR}" || { echo "[wineasio] ERROR: cannot cd to ${KONTAKT_DIR}"; exit 1; }
WINEDLLOVERRIDES="${WINE_OVERRIDES}" pw-jack wine "${KONTAKT_EXE}"

echo "[wineasio] Kontakt exited."
