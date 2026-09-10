#!/usr/bin/env bash
# check-reg-and-tiles-state.sh (READ-ONLY)
# Kontakt loads now (fix = removed stray yabridge Kontakt copy). Clarify two things before deciding:
#  1) which wine registry is CURRENTLY live (sep-7 snapshot restore, or the sep-8 pre-restore backup),
#     and whether the reg even matters now that the real fix was yabridge.
#  2) the icon/tile state: komplete.db3 + LibrariesCache on /mnt/workspace UserData — untouched by today's
#     wine/yabridge work; report their current state so we know if icons actually need attention.
set -u
WPREF="$HOME/.wine"
UD="/mnt/workspace/VST Install/Kontakt Portable/UserData"

echo "===== 1) currently-live wine .reg (mtime tells which set is in place) ====="
for r in system.reg user.reg userdef.reg; do
  [ -f "$WPREF/$r" ] && echo "  $r : $(ls -la "$WPREF/$r" | awk '{print $5,$6,$7,$8}')"
done
echo
echo "  reg backups made during yesterday's restore (the sep-8 pre-restore state):"
ls -dla "$WPREF"/_kiro_reg_backup_* 2>/dev/null | sed 's/^/    /'
for b in "$WPREF"/_kiro_reg_backup_*; do
  [ -d "$b" ] || continue
  echo "    contents of $b:"
  ls -la "$b"/*.reg 2>/dev/null | awk '{print "      "$9" "$5" "$6" "$7" "$8}'
done
echo

echo "===== 2) icon/tile state (komplete.db3 + LibrariesCache) — untouched by wine work ====="
echo "  komplete.db3: $(ls -la "$UD/komplete.db3" 2>/dev/null | awk '{print $5,$6,$7,$8}')"
echo "  LibrariesCache: $(find "$UD/Kontakt 8/LibrariesCache" -maxdepth 1 -iname '*.cache' 2>/dev/null | wc -l) .cache files present"
echo "  (these live on /mnt/workspace, separate from ~/.wine — today's fixes did not modify them)"
echo

echo "===== 3) wine version now (confirm what we're running) ====="
pacman -Q wine-staging 2>/dev/null | sed 's/^/  /'
echo
echo "READ-ONLY. Decision after this:"
echo "  - If Kontakt+other plugins all load fine on the CURRENT reg, leave it; the reg wasn't the cause."
echo "  - The sep-8 backup lets us go back to the pre-restore ('future') reg if you prefer, but only if"
echo "    something specific regressed. Icons are a separate DB/cache matter, checked above."
