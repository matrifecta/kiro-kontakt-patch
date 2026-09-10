#!/usr/bin/env bash
# inspect-kontakt-settings.sh (READ-ONLY)
# The app files + registry paths are correct (D:\...\x64\Kontakt 8.exe), yet the browse dialog
# rejects the folder. Inspect Settings.cfg for how it records the install/content dirs and drive
# letters, and read the recent crashlog header. This tells us if a stored path uses a drive letter
# that changed, or a format the new Wine rejects.
set -u
UD="/mnt/workspace/VST Install/Kontakt Portable/UserData"
CFG="$UD/Settings.cfg"

echo "===== Settings.cfg : full contents (it's small) ====="
if [ -f "$CFG" ]; then
  sed 's/^/  /' "$CFG"
else
  echo "  (missing $CFG)"
fi
echo
echo "===== any drive-letter paths in Settings.cfg ====="
grep -niE '[A-Za-z]:\\\\|[A-Za-z]:/' "$CFG" 2>/dev/null | sed 's/^/  /'
echo
echo "===== recent crashlog header (2.9.2026) — what module/why ====="
CL=$(find "$UD" -iname '*mini.nicrash' 2>/dev/null | sort | tail -1)
if [ -n "$CL" ]; then
  echo "  file: $CL"
  head -40 "$CL" | sed 's/^/  /'
else
  echo "  (no crashlog found)"
fi
echo
echo "READ-ONLY."
