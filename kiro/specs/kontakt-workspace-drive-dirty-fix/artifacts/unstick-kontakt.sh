#!/usr/bin/env bash
#
# unstick-kontakt.sh
#
# Kontakt is spinning (stack-overflow parse of a Tools .nkt) and has frozen its
# yabridge host, which blocks Reaper's GUI thread. Free Reaper by killing ONLY the
# stuck Kontakt yabridge host + its wine host process — NOT the whole wineserver
# (that would also kill your other working plugins: bx_enhancer, Valhalla, elysia).
#
# Usage:
#   bash unstick-kontakt.sh            # show what would be killed (dry-run)
#   bash unstick-kontakt.sh kill       # kill only the Kontakt yabridge host (TERM, then KILL)
#   bash unstick-kontakt.sh nuke       # LAST RESORT: wineserver -k (kills ALL wine plugins)

set -u
MODE="${1:-dryrun}"

echo "===== Kontakt-related wine/yabridge processes ====="
# match the yabridge host that is hosting the Kontakt VST3
mapfile -t PIDS < <(pgrep -f 'yabridge-host.*Kontakt 8 Portable')
ps -eo pid,pcpu,pmem,stat,comm,args | grep -iE 'yabridge-host|Kontakt 8 Portable' | grep -v grep | grep -v unstick-kontakt

echo
if [ "${#PIDS[@]}" -eq 0 ]; then
  echo "No 'Kontakt 8 Portable' yabridge host found by name."
  echo "It may already be gone, or Reaper freed itself. Check Reaper now."
  echo "If Reaper is STILL frozen, re-run with 'nuke' as last resort."
fi

case "$MODE" in
  dryrun)
    echo "DRY-RUN. Target Kontakt-host PIDs: ${PIDS[*]:-none}"
    echo "Re-run with:  bash $0 kill      (frees Reaper, keeps other plugins)"
    echo "Last resort:  bash $0 nuke      (wineserver -k, kills ALL wine plugins)"
    ;;
  kill)
    if [ "${#PIDS[@]}" -eq 0 ]; then echo "Nothing to kill by name; try 'nuke' if Reaper still frozen."; exit 0; fi
    echo "=== sending SIGTERM to Kontakt host PIDs: ${PIDS[*]} ==="
    kill -TERM "${PIDS[@]}" 2>/dev/null
    sleep 3
    # anything still alive?
    STILL=()
    for p in "${PIDS[@]}"; do kill -0 "$p" 2>/dev/null && STILL+=("$p"); done
    if [ "${#STILL[@]}" -gt 0 ]; then
      echo "=== still alive, sending SIGKILL: ${STILL[*]} ==="
      kill -KILL "${STILL[@]}" 2>/dev/null
      sleep 1
    fi
    echo "Done. Check Reaper — it should be responsive; the Kontakt FX slot will show offline/failed."
    echo "You can then remove that Kontakt instance from the FX chain and re-add it fresh."
    ;;
  reap)
    # Kontakt host already <defunct> (zombie); Reaper still frozen waiting on the dead
    # bridge. Kill the reaper_host bridge child that parents the zombie so Reaper's
    # thread unblocks — WITHOUT touching the other plugin hosts or wineserver.
    echo "=== reaper_host bridge helpers + any defunct yabridge hosts ==="
    ps -eo pid,ppid,stat,comm,args | grep -iE 'reaper_host_x86|yabridge-host' | grep -v grep | grep -v unstick-kontakt
    echo
    mapfile -t ZPARENTS < <(ps -eo pid,ppid,stat,comm | awk '$3 ~ /Z/ && $4 ~ /yabridge/ {print $2}' | sort -u)
    echo "Parents of defunct yabridge zombies: ${ZPARENTS[*]:-none}"
    if [ "${#ZPARENTS[@]}" -gt 0 ]; then
      echo "=== SIGTERM those bridge-helper parents (reaps the zombie, frees Reaper) ==="
      kill -TERM "${ZPARENTS[@]}" 2>/dev/null
      sleep 2
      for p in "${ZPARENTS[@]}"; do kill -0 "$p" 2>/dev/null && { echo "  SIGKILL $p"; kill -KILL "$p" 2>/dev/null; }; done
    fi
    echo "Done. Check Reaper — it should unfreeze. Other plugins stay loaded."
    echo "If STILL frozen, run:  bash $0 nuke"
    ;;
  nuke)
    echo "=== LAST RESORT: wineserver -k (kills ALL wine-hosted plugins) ==="
    wineserver -k
    echo "Done. All yabridge-hosted plugins are gone. Reaper should be responsive;"
    echo "re-add plugins as needed. Kontakt-under-Reaper can be reloaded fresh."
    ;;
  *)
    echo "Unknown mode '$MODE'. Use: dryrun | kill | nuke"; exit 1;;
esac
