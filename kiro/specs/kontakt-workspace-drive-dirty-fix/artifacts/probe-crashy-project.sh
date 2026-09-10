#!/usr/bin/env bash
# probe-crashy-project.sh   (READ-ONLY, changes nothing)
# Goal: find the Reaper project that crashes on load (references the missing ZauberwindsSoloFloete DecentSampler
# library) and see how DecentSampler is embedded, so we can rescue the project by removing ONLY that plugin
# instance. Nothing is modified here.
set -u
echo "===== (a) most-recently-modified .rpp projects (the crashy one is likely near the top) ====="
find "$HOME" -maxdepth 6 -iname '*.rpp' -printf '%T@ %p\n' 2>/dev/null | sort -rn | head -20 | cut -d' ' -f2-

echo
echo "===== (b) Reaper's recent-project list (what it offered to reopen) ====="
grep -iE "^recent" "$HOME/.config/REAPER/reaper.ini" 2>/dev/null | head -20 | sed 's/^/  /' || echo "  (no recent entries)"

echo
echo "===== (c) which .rpp files actually REFERENCE DecentSampler or Zauberwinds? ====="
# search project files for DecentSampler / Zauberwinds references (case-insensitive)
find "$HOME" -maxdepth 6 -iname '*.rpp' 2>/dev/null | while read -r rpp; do
  if grep -qiE "decentsampler|zauberwind" "$rpp" 2>/dev/null; then
    echo "  HIT: $rpp"
    echo "    --- matching lines (plugin id + any sample path) ---"
    grep -niE "decentsampler|zauberwind|dsbundle" "$rpp" 2>/dev/null | head -12 | sed 's/^/      /'
  fi
done
echo
echo "===== (d) how is DecentSampler installed (VST3/CLAP/native)? ====="
find "$HOME" /usr/lib -maxdepth 6 -iname '*decentsampler*' 2>/dev/null | grep -iE "\.(vst3|so|clap|dll)$|DecentSampler" | head -20
echo "(done — paste everything above)"
