#!/usr/bin/env bash
# probe-prefix-snapshot.sh (READ-ONLY)
# The wine prefix was reconfigured today (system.reg mtime sep 8 20:09), losing Kontakt Portable's
# install registration -> "installation directory not found". Check what the known-good snapshot
# captured of the prefix (registry + dosdevices) so we can restore just the Kontakt registration.
set -u
SNAP="/mnt/wd_black/kontakt-known-good-20260907_123950"
WPREF="$HOME/.wine"

echo "===== known-good snapshot present? ====="
if [ -d "$SNAP" ]; then
  echo "  yes: $SNAP  ($(du -sh "$SNAP" 2>/dev/null | cut -f1))"
  echo "  top-level:"; ls -la "$SNAP" | sed 's/^/    /'
else
  echo "  MISSING: $SNAP"
  echo "  searching for any kontakt-known-good snapshot:"
  find /mnt/wd_black /mnt/btrfs_disk -maxdepth 1 -iname 'kontakt-known-good*' 2>/dev/null | sed 's/^/    /'
fi
echo

echo "===== did the snapshot capture wine registry / dosdevices? ====="
for f in system.reg user.reg userdef.reg; do
  hit=$(find "$SNAP" -maxdepth 3 -name "$f" 2>/dev/null | head -1)
  [ -n "$hit" ] && echo "  [ok] $f -> $hit  ($(ls -la "$hit" | awk '{print $5, $6, $7, $8}'))" || echo "  [missing] $f"
done
find "$SNAP" -maxdepth 3 -iname 'dosdevices' -type d 2>/dev/null | sed 's/^/  dosdevices: /'
echo

echo "===== does the snapshot's system.reg contain the Kontakt Portable install registration? ====="
SNAPREG=$(find "$SNAP" -maxdepth 3 -name 'system.reg' 2>/dev/null | head -1)
if [ -n "$SNAPREG" ]; then
  echo "  Kontakt/NI keys in snapshot system.reg:"
  grep -niE 'Kontakt 8 PORTABLE|Vst0Name|Native Instruments\\\\Kontakt|InstallDir|installation' "$SNAPREG" 2>/dev/null | head -20 | sed 's/^/    /'
fi
echo

echo "===== current prefix backups of the reg (so restore is reversible) ====="
ls -la "$WPREF"/*.reg 2>/dev/null | sed 's/^/  /'
echo
echo "READ-ONLY. If the snapshot has system.reg/user.reg with the Kontakt registration, we can"
echo "restore those into ~/.wine (backing up current first) to give Kontakt back its install record."
