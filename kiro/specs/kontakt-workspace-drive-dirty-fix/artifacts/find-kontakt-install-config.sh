#!/usr/bin/env bash
# find-kontakt-install-config.sh (READ-ONLY)
# The browse dialog won't accept the path (Wine/space quirk), but the .vst3plugin IS present in x64.
# Find where Kontakt Portable STORES its remembered install directory, so we can set it directly
# and bypass the dialog. Look in UserData config, Wine registry, and any ktp/portable ini.
set -u
KP="/mnt/workspace/VST Install/Kontakt Portable"
UD="$KP/UserData"
WPREF="$HOME/.wine"

echo "===== UserData config files (Settings.cfg, ini, xml, cfg) ====="
find "$UD" -maxdepth 3 -type f \( -iname '*.cfg' -o -iname '*.ini' -o -iname '*.xml' -o -iname '*.plist' -o -iname '*.txt' \) 2>/dev/null | sed 's/^/  /' | head -40
echo
echo "===== grep those for an install/app path (x64, vst3plugin, Kontakt Portable) ====="
grep -rilE 'vst3plugin|Kontakt Portable|InstallDir|installation|x64' "$UD" 2>/dev/null | sed 's/^/  /' | head -20
echo
echo "===== ktp / portable marker files anywhere in the tree ====="
find "$KP" -maxdepth 3 -type f \( -iname 'ktp*' -o -iname '*portable*' -o -iname '*.location' \) 2>/dev/null | sed 's/^/  /' | head
echo
echo "===== Wine registry mentions of Native Instruments / Kontakt install paths ====="
for reg in system.reg user.reg; do
  if [ -f "$WPREF/$reg" ]; then
    echo "  --- $reg: Native Instruments / Kontakt keys ---"
    grep -niE 'Native Instruments|Kontakt|ContentDir|InstallDir' "$WPREF/$reg" 2>/dev/null | head -30 | sed 's/^/    /'
  fi
done
echo
echo "===== NI global config dirs inside the prefix (common location) ====="
find "$WPREF/drive_c" -maxdepth 6 -type d -iname 'Native Instruments' 2>/dev/null | sed 's/^/  /'
find "$WPREF/drive_c" -type f -iname '*.xml' -path '*Native Instruments*' 2>/dev/null | sed 's/^/  /' | head
echo
echo "READ-ONLY. Report back; I'll identify the exact key/file that stores the install path"
echo "so we set it to the x64 folder directly and skip the broken browse dialog."
