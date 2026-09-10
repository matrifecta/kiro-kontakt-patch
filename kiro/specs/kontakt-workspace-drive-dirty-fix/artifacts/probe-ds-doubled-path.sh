#!/usr/bin/env bash
# probe-ds-doubled-path.sh   (READ-ONLY, changes nothing)
# ROOT CAUSE NARROWED: the library EXISTS at the SINGLE-.config path:
#   ~/.config/DecentSampler/Sample Libraries/ZauberwindsSoloFloete_v1.dsbundle/Files/ZauberwindsSoloFloete/
# but DS crashed looking for it at a DOUBLED path:
#   ~/.config/DecentSampler/.config/DecentSampler/Sample Libraries/.../C3-Long1-V127.flac
# So this is a PATH-RESOLUTION bug, not missing content. This probe finds WHERE the doubled ".config/
# DecentSampler" comes from: (1) inside the .dspreset sample path= refs, (2) DS's DecentSampler.xml library
# base path, (3) SampleLibrary.db / catalog. It also confirms the specific FLAC exists at the real path.
# Nothing is modified.
set -u
DSROOT="$HOME/.config/DecentSampler"
BUNDLE="$DSROOT/Sample Libraries/ZauberwindsSoloFloete_v1.dsbundle"

echo "===== (a) does the crashed FLAC exist at the REAL (single-.config) path? ====="
F="$BUNDLE/Files/ZauberwindsSoloFloete/C3-Long1-V127.flac"
if [ -e "$F" ]; then echo "  PRESENT: $F"; else
  echo "  not at that exact name — listing what IS in the sample dir:"
  ls "$BUNDLE/Files/ZauberwindsSoloFloete/" 2>/dev/null | head -20 | sed 's/^/    /'
fi

echo
echo "===== (b) how does the .dspreset reference its samples? (path= base) ====="
PRESET="$BUNDLE/ZauberwindsSoloFloete_v1.dspreset"
if [ -f "$PRESET" ]; then
  echo "  preset: $PRESET"
  echo "  --- sample path attributes (first 25) ---"
  grep -oiE 'path="[^"]*"' "$PRESET" 2>/dev/null | head -25 | sed 's/^/    /'
  echo "  --- does the preset itself contain a doubled .config/DecentSampler? ---"
  grep -niE '\.config/DecentSampler' "$PRESET" 2>/dev/null | head | sed 's/^/    /' || echo "    (no .config path baked in the preset — good, means paths are relative)"
  echo "  --- any absolute paths at all in the preset? ---"
  grep -oiE 'path="(/|[A-Za-z]:)[^"]*"' "$PRESET" 2>/dev/null | head | sed 's/^/    /' || echo "    (paths appear RELATIVE — resolved against a base dir DS chooses)"
else
  echo "  .dspreset not found at $PRESET"
fi

echo
echo "===== (c) DS config files — do THEY carry the doubled path / a wrong library base? ====="
for f in "$DSROOT/DecentSampler.xml" "$DSROOT/catalog" "$DSROOT/SampleLibrary.db"; do
  [ -e "$f" ] || { echo "  (missing: $f)"; continue; }
  echo "  --- $f ---"
  # SampleLibrary.db is sqlite; grep -a to scan strings safely, look for the path patterns
  echo "    doubled .config/DecentSampler occurrences:"
  grep -aoiE '(\.config/DecentSampler){2}' "$f" 2>/dev/null | head -3 | sed 's/^/      /' || true
  grep -acE '\.config/DecentSampler/\.config/DecentSampler' "$f" 2>/dev/null | sed 's/^/      count: /'
  echo "    Zauberwinds references (context):"
  grep -aoiE '[^"<> ]{0,60}Zauberwinds[^"<> ]{0,80}' "$f" 2>/dev/null | head -5 | sed 's/^/      /' || echo "      (none)"
  echo "    any 'Sample Libraries' base path strings:"
  grep -aoiE '[^"<>]{0,80}Sample Libraries' "$f" 2>/dev/null | head -5 | sed 's/^/      /' || true
done

echo
echo "===== (d) the most recent DS log (it records the exact path DS tried) ====="
LATEST=$(ls -t "$DSROOT"/DSLog_*.log 2>/dev/null | head -1)
echo "  latest log: $LATEST"
[ -n "$LATEST" ] && sed 's/^/    /' "$LATEST" 2>/dev/null | head -40
echo
echo "  --- any DS log mentioning the doubled path or 'does not exist'? ---"
grep -liE '\.config/DecentSampler/\.config|does not exist|Zauberwinds' "$DSROOT"/DSLog_*.log 2>/dev/null | tail -5 | while read -r lg; do
  echo "    $lg:"; grep -iE '\.config/DecentSampler/\.config|does not exist|Zauberwinds' "$lg" 2>/dev/null | head -6 | sed 's/^/       /'
done
echo "(done — paste everything above)"
