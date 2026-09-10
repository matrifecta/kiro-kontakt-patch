#!/usr/bin/env bash
# probe-kontakt-appdir.sh (READ-ONLY) — show the real contents of the Kontakt 8 app tree so we
# know exactly which folder to point the "browse for installation directory" dialog at.
set -u
K8="/mnt/workspace/VST Install/Kontakt Portable/Kontakt 8"
echo "===== contents of: $K8 ====="
ls -la "$K8" | sed 's/^/  /'
echo
echo "===== contents of: $K8/x64 ====="
ls -la "$K8/x64" | sed 's/^/  /'
echo
echo "===== where are Kontakt's resource/library data files? (search common names) ====="
find "$K8" -maxdepth 3 -idirname 2>/dev/null >/dev/null # noop guard
find "$K8" -maxdepth 3 -type d \( -iname 'Resources' -o -iname 'lib*' -o -iname 'Data' -o -iname 'presets' \) 2>/dev/null | sed 's/^/  /'
echo
echo "===== any .nicnt / .db3 / config that marks the portable root ====="
find "$K8" -maxdepth 2 -type f \( -iname '*.nicnt' -o -iname '*.db3' -o -iname '*.cfg' -o -iname '*.xml' \) 2>/dev/null | sed 's/^/  /' | head -20
echo
echo "===== the exe + its immediate siblings (install-root markers usually sit by the exe) ====="
ls -la "$K8/x64" | grep -iE '\.exe|\.dll|Resources|Data|lib' | sed 's/^/  /'
echo
echo "READ-ONLY."
