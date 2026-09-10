#!/usr/bin/env bash
#
# restore-wine-registry.sh
#
# The wine prefix was reconfigured on sep 8 20:09 (system.reg/user.reg/userdef.reg rewritten),
# wiping Kontakt Portable's install registration -> "installation directory not found".
# Restore the known-good registry files captured sep 7 12:23 (BEFORE the break) from the snapshot.
# Backs up the current .reg first (reversible), then kills wineserver so wine reloads the restored reg.
#
# Reaper/Kontakt/wine MUST be closed. Usage:
#   bash restore-wine-registry.sh          # dry-run: show what will change
#   bash restore-wine-registry.sh apply

set -u
MODE="${1:-dryrun}"
WPREF="$HOME/.wine"
SNAP="/mnt/wd_black/kontakt-known-good-20260907_123950/wine"
STAMP="$(date +%Y%m%d_%H%M%S)"
BK="$WPREF/_kiro_reg_backup_${STAMP}"

REGS=(system.reg user.reg userdef.reg)

echo "===== plan ====="
echo "  restore FROM (known-good sep 7 12:23): $SNAP"
echo "  restore TO:                            $WPREF"
for r in "${REGS[@]}"; do
  s="$SNAP/$r"; d="$WPREF/$r"
  echo "    $r:"
  echo "      snapshot: $( [ -f "$s" ] && ls -la "$s" | awk '{print $5,$6,$7,$8}' || echo MISSING )"
  echo "      current : $( [ -f "$d" ] && ls -la "$d" | awk '{print $5,$6,$7,$8}' || echo MISSING )"
done
echo

# guard: wine must be closed
if pgrep -x wineserver >/dev/null 2>&1 || pgrep -fi 'Kontakt 8' >/dev/null 2>&1 || pgrep -x reaper >/dev/null 2>&1; then
  echo "  WARNING: wineserver/Reaper/Kontakt appears to be RUNNING."
  echo "  Close Reaper first (and run 'wineserver -k') before applying."
  [ "$MODE" = apply ] && { echo "  ABORT (apply blocked while running)."; exit 1; }
fi

for r in "${REGS[@]}"; do
  [ -f "$SNAP/$r" ] || { echo "ABORT: snapshot missing $r"; exit 1; }
done

if [ "$MODE" != apply ]; then
  echo "DRY-RUN. Re-run: bash $0 apply"
  exit 0
fi

echo "===== 1) backup current .reg -> $BK ====="
mkdir -p "$BK"
for r in "${REGS[@]}"; do [ -f "$WPREF/$r" ] && cp -av "$WPREF/$r" "$BK/" | sed 's/^/  /'; done

echo "===== 2) copy known-good .reg into the prefix ====="
for r in "${REGS[@]}"; do cp -av "$SNAP/$r" "$WPREF/$r" | sed 's/^/  /'; done

echo "===== 3) stop wineserver so wine reloads the restored registry ====="
wineserver -k 2>/dev/null; sleep 1
echo "  done."

echo
echo "ROLLBACK (if needed): copy the backed-up .reg back, then wineserver -k :"
echo "  cp -av \"$BK/.\" \"$WPREF/\" && wineserver -k"
echo
echo "NEXT: launch Reaper (QT_QPA_PLATFORM=xcb reaper) and load Kontakt — it should find its"
echo "installation now. If it still asks, we set the exact install key via wine regedit."
