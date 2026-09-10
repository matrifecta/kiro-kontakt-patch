#!/usr/bin/env bash
#
# setup-ds-symlinks.sh
#
# Decent Sampler scans ONE "Sample Libraries Location" recursively for .dspreset/.dslibrary.
# Our DS libs are split across two drives, so create ONE master folder in $HOME with symlinks
# to both drives' "DS Libraries". Point DS at the master folder -> it sees everything.
#
# Placed under $HOME because DS runs under Wine and $HOME is reachable via the Wine drive map
# (typically Z:\home\phnx\... or the mapped home). Symlinks only — NO data moved/copied.
#
# Usage: bash setup-ds-symlinks.sh          # show plan
#        bash setup-ds-symlinks.sh apply

set -u
MODE="${1:-dryrun}"
MASTER="$HOME/DS Libraries All"
WD="/mnt/wd_black/DS Libraries"
BT="/mnt/btrfs_disk/DS Libraries"

echo "=== plan ==="
echo "  master folder: $MASTER"
echo "    wd_black -> $WD  ($( [ -d "$WD" ] && echo present || echo MISSING ))"
echo "    btrfs    -> $BT  ($( [ -d "$BT" ] && echo present || echo MISSING ))"
echo

if [ "$MODE" != "apply" ]; then
  echo "DRY-RUN. Re-run: bash $0 apply"; exit 0
fi

mkdir -p "$MASTER"
# create/refresh symlinks (ln -sfn is idempotent, replaces an existing link safely)
ln -sfn "$WD" "$MASTER/wd_black"
ln -sfn "$BT" "$MASTER/btrfs"

echo "=== created ==="
ls -la "$MASTER" | sed 's/^/  /'
echo
echo "=== sanity: presets visible THROUGH the symlinks (DS will scan these) ==="
echo "  via wd_black link: $(find -L "$MASTER/wd_black" -type f -iname '*.dspreset' ! -name '._*' 2>/dev/null | wc -l) .dspreset"
echo "  via btrfs link:    $(find -L "$MASTER/btrfs"    -type f -iname '*.dspreset' ! -name '._*' 2>/dev/null | wc -l) .dspreset"
echo "                     $(find -L "$MASTER/btrfs"    -type f -iname '*.dslibrary' ! -name '._*' 2>/dev/null | wc -l) .dslibrary"
echo
echo "NEXT — point Decent Sampler at the master folder:"
echo "  In the DS plugin, open the BROWSER, click the gear/settings (or the folder path at top),"
echo "  set 'Sample Libraries Location' to:"
echo "      $MASTER"
echo "  (Under Wine this is typically reachable as  Z:\\home\\$USER\\DS Libraries All  or via the"
echo "   mapped home drive.) DS will scan recursively and list all presets from BOTH drives."
echo
echo "ROLLBACK: rm -rf \"$MASTER\"   (removes only the symlinks + folder, NOT your libraries)"
