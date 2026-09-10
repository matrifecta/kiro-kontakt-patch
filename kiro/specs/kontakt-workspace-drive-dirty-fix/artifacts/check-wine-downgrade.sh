#!/usr/bin/env bash
# check-wine-downgrade.sh (READ-ONLY) — what wine packages are installed, and which older
# versions are cached for a rollback. Nothing is changed.
set -u
echo "===== currently installed wine packages ====="
pacman -Q 2>/dev/null | grep -iE 'wine' | sed 's/^/  /'
echo
echo "===== wine update history (when it changed) ====="
grep -iE 'wine' /var/log/pacman.log 2>/dev/null | grep -iE 'upgraded|installed' | tail -15 | sed 's/^/  /'
echo
echo "===== cached wine packages available to downgrade to ====="
ls -1 /var/cache/pacman/pkg/ 2>/dev/null | grep -iE 'wine' | sort | sed 's/^/  /'
echo
echo "READ-ONLY. If a previous wine-staging .pkg.tar.zst is cached, downgrade is:"
echo "  sudo pacman -U /var/cache/pacman/pkg/<previous-wine-staging-file>"
