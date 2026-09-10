#!/usr/bin/env bash
#
# capture-kontakt-load-error.sh
#
# Downgrading wine-staging did NOT fix the "Installation directory not found". So capture the
# ACTUAL runtime error: launch Reaper from terminal with Wine debug channels that show file
# opens + the exact path Kontakt probes for 'Kontakt 8.vst3plugin'. Output -> a log file we read.
#
# This is INTERACTIVE: it starts Reaper. Load the Kontakt instance so the error fires, then
# CLOSE Reaper. The log captures what path it tried and why it failed.
#
# Usage: bash capture-kontakt-load-error.sh
set -u
LOG="/home/phnx/KIRO/.kiro/specs/kontakt-workspace-drive-dirty-fix/artifacts/kontakt-load-error.log"
: > "$LOG"

echo "Launching Reaper with Wine file-trace. In Reaper: trigger the Kontakt load so the"
echo "'installation directory not found' appears, then CLOSE Reaper to end capture."
echo "Log -> $LOG"
echo

# WINEDEBUG: trace file opens + warnings; keep it focused so the log stays readable.
# Also print anything Kontakt writes about resources/install.
QT_QPA_PLATFORM=xcb \
WINEDEBUG=+file,warn+module \
reaper 2>&1 | grep -iE 'vst3plugin|Kontakt|installation|resources_ENG|lib_ENG|cannot|not found|open_file|CreateFile|\.exe|x64' \
  | tee "$LOG"

echo
echo "=== capture ended. Key lines: ==="
grep -iE 'vst3plugin|installation|not found|cannot resolve|x64' "$LOG" | tail -30
echo
echo "Log saved: $LOG"
