#!/usr/bin/env bash
#
# probe-kontakt-install-path.sh  (READ-ONLY)
#
# Kontakt Portable v8.11.0 now says "Installation directory not found" in Reaper after a
# wine-staging update. Determine:
#   1) does the install dir still exist on disk (files intact)?
#   2) what does Kontakt consider its "installation directory" (where the .vst3 + resources are)?
#   3) did the Wine drive map (dosdevices) change — is /mnt/workspace still mapped, and to which letter?
#   4) what path should the user browse to in the "browse for it" dialog?
# NOTHING is modified.

set -u
KP="/mnt/workspace/VST Install/Kontakt Portable"
WINEPREFIX_DEFAULT="$HOME/.wine"

echo "===== 1) does the Kontakt Portable tree still exist on disk? ====="
if [ -d "$KP" ]; then
  echo "  present: $KP"
  echo "  key subdirs:"
  for d in "Kontakt 8" "Kontakt 8/x64" "Kontakt 8/x64/VST3" "UserData"; do
    [ -e "$KP/$d" ] && echo "    [ok] $d" || echo "    [MISSING] $d"
  done
  echo "  the actual VST3 plugin:"
  find "$KP/Kontakt 8/x64/VST3" -maxdepth 1 -iname '*.vst3' 2>/dev/null | sed 's/^/    /'
  echo "  the standalone/app exe(s) (what NI treats as the install root marker):"
  find "$KP/Kontakt 8" -maxdepth 2 -iname '*.exe' 2>/dev/null | sed 's/^/    /' | head
  echo "  resources dir (NI needs this next to the app):"
  for r in "$KP/Kontakt 8/Resources" "$KP/Kontakt 8/x64/Resources"; do
    [ -d "$r" ] && echo "    [ok] $r"
  done
else
  echo "  MISSING ENTIRELY: $KP  (this would be the real problem)"
fi
echo

echo "===== 2) Wine drive map (dosdevices) — which letters point where? ====="
DD="$WINEPREFIX_DEFAULT/dosdevices"
if [ -d "$DD" ]; then
  ls -la "$DD" | sed 's/^/    /'
  echo
  echo "  does any letter map to /mnt/workspace or / (root)?"
  for l in "$DD"/*:; do
    [ -e "$l" ] || continue
    tgt="$(readlink -f "$l" 2>/dev/null)"
    echo "    $(basename "$l") -> $tgt"
  done
else
  echo "  no dosdevices at $DD (is WINEPREFIX different? check env)"
fi
echo

echo "===== 3) how yabridge/Reaper referenced the plugin (last known good path) ====="
echo "  yabridge.toml section + the .vst3 path Reaper loads:"
grep -A3 -i 'Kontakt' "$HOME/.vst3/yabridge/yabridge.toml" 2>/dev/null | sed 's/^/    /' || echo "    (no Kontakt section in yabridge.toml)"
echo

echo "===== 4) suggested browse target ====="
echo "  Kontakt's 'installation directory' = the folder CONTAINING the Kontakt 8 app + Resources,"
echo "  i.e. the 'Kontakt 8' folder itself (NOT x64, NOT UserData)."
echo "  On disk that is:  $KP/Kontakt 8"
echo "  Through Wine, use whatever LETTER maps to /mnt/workspace or / from section 2 above."
echo "  If Z: -> / (root), the path is:  Z:\\mnt\\workspace\\VST Install\\Kontakt Portable\\Kontakt 8"
echo
echo "READ-ONLY. Report sections 1-3 back; I'll give the exact letter+path to browse to."
