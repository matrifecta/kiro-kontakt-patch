#!/usr/bin/env bash
# probe-ds-rootcause.sh   (READ-ONLY, changes nothing)
# WHY did DecentSampler suddenly not find its FLACs? We changed only audio clock/rtprio — nothing touching DS
# samples. The earlier probe showed the WHOLE "Sample Libraries" path returned nothing, so this is likely a
# LOCATION problem (moved dir / broken symlink / unmounted drive / DS config repointed), not a deleted file.
# This probe maps the real state: where DS config lives, whether the path is a symlink, where the library
# ACTUALLY is on any drive, and what DS's own config/prefs say its library path should be. Nothing is modified.
set -u

DSROOT="$HOME/.config/DecentSampler"
echo "===== (a) DecentSampler config tree — what actually exists, and is anything a symlink? ====="
if [ -d "$DSROOT" ]; then
  ls -la "$DSROOT" 2>/dev/null
  echo "--- nested .config (the odd double path from the crash string) ---"
  ls -la "$DSROOT/.config/DecentSampler" 2>/dev/null || echo "  (no nested .config/DecentSampler)"
  echo "--- find any symlinks under the DS tree (broken symlink = sudden 'file not found') ---"
  find "$DSROOT" -maxdepth 4 -type l -printf '%p -> %l\n' 2>/dev/null | sed 's/^/  LINK: /' || true
  echo "--- broken symlinks specifically ---"
  find "$DSROOT" -maxdepth 4 -xtype l -printf '%p -> %l  (BROKEN)\n' 2>/dev/null | sed 's/^/  /' || echo "  (none broken)"
else
  echo "  $DSROOT does not exist"
fi

echo
echo "===== (b) where does ZauberwindsSoloFloete / any .dsbundle ACTUALLY live on the system? ====="
echo "--- searching home + all mounted drives for the bundle name ---"
for base in "$HOME" /mnt/workspace /mnt/storage /mnt/wd_black /mnt/win_system /mnt/btrfs_disk; do
  [ -d "$base" ] || continue
  find "$base" -maxdepth 7 -iname '*ZauberwindsSoloFloete*' 2>/dev/null | sed "s|^|  [$base] |"
done
echo "--- any .dsbundle anywhere (shows where DS libraries really are) ---"
for base in "$HOME" /mnt/workspace /mnt/storage /mnt/wd_black /mnt/win_system /mnt/btrfs_disk; do
  [ -d "$base" ] || continue
  find "$base" -maxdepth 7 -iname '*.dsbundle' 2>/dev/null | head -10 | sed "s|^|  [$base] |"
done

echo
echo "===== (c) DecentSampler's own prefs — what path does IT think its libraries are in? ====="
# DS keeps settings in xml/json/properties under its config dir
find "$DSROOT" -maxdepth 4 -type f \( -iname '*.xml' -o -iname '*.json' -o -iname '*.properties' -o -iname '*.settings' -o -iname '*prefs*' \) 2>/dev/null | while read -r f; do
  echo "  --- $f ---"
  grep -oiE '(path|dir|location|folder|library)[^<>=]{0,4}[=:>][^<>]{0,160}' "$f" 2>/dev/null | head -12 | sed 's/^/     /'
done

echo
echo "===== (d) is everything still mounted? (a drive dropping = instant 'file not found') ====="
findmnt -rno TARGET,SOURCE,FSTYPE /mnt/workspace /mnt/storage /mnt/wd_black /mnt/win_system 2>/dev/null | sed 's/^/  /' || mount | grep -iE "/mnt/(workspace|storage|wd_black|win_system)" | sed 's/^/  /'

echo
echo "===== (e) recent DS-related filesystem activity (did the dir get moved/renamed recently?) ====="
echo "--- newest items in the DS config tree by mtime ---"
find "$DSROOT" -maxdepth 4 2>/dev/null -printf '%TY-%Tm-%Td %TH:%TM  %p\n' | sort -r | head -15 | sed 's/^/  /'
echo "(done — paste everything above)"
