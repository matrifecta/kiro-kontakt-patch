#!/usr/bin/env bash
# Create ~/Cursor Projects with two maps and install the frozen Kiro backdrop DB.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
HOME_MAP="${CURSOR_PROJECTS_ROOT:-$HOME/Cursor Projects}"
CREATED="$HOME_MAP/created-in-cursor"
IMPORTED="$HOME_MAP/imported-and-modified"
BACKDROP="$HOME_MAP/kiro-backdrop.sqlite"

mkdir -p "$CREATED" "$IMPORTED"

python3 "$ROOT/tools/build-backdrop.py"

ln -sfn "$ROOT" "$CREATED/studio-hub"
ln -sfn "$ROOT/kiro/specs/kontakt-workspace-drive-dirty-fix" \
  "$IMPORTED/kontakt-workspace-drive-dirty-fix"
ln -sfn "$ROOT/kiro/specs/kontakt-wine-optimization" \
  "$IMPORTED/kontakt-wine-optimization"
ln -sfn "$ROOT/kiro/specs/usb-audio-resume" \
  "$IMPORTED/usb-audio-resume"
ln -sfn "$ROOT/kiro/specs/turing-wake-recovery" \
  "$IMPORTED/turing-wake-recovery"
ln -sfn "$ROOT/kiro/specs/turing-installer-pid-theme-fix" \
  "$IMPORTED/turing-installer-pid-theme-fix"
mkdir -p "$IMPORTED/touchosc-midi-bridge"
ln -sfn "$ROOT/kiro/scripts/touchosc_midi_bridge.py" \
  "$IMPORTED/touchosc-midi-bridge/touchosc_midi_bridge.py"
ln -sfn "$ROOT/kiro/scripts" "$IMPORTED/_scripts"

install -m 0644 "$ROOT/data/kiro-backdrop.sqlite" "$BACKDROP"
# Frozen copy of the JSON map next to the DB (read-only backdrop).
install -m 0644 "$ROOT/data/maps.json" "$HOME_MAP/kiro-backdrop.json"

cat > "$HOME_MAP/README.txt" <<EOF
Cursor Projects
===============

Root (this folder): $HOME_MAP

created-in-cursor/
  New Cursor projects. studio-hub is this repo.

imported-and-modified/
  Kiro projects, linked to the working copies in the repo.
  Edit those files to change the living state.

kiro-backdrop.sqlite / kiro-backdrop.json
  Frozen record of what Kiro already achieved, plus filesystem
  paths cited in that work. Do not treat this DB as the working tree.

On CachyOS this should live at /home/phnx/Cursor Projects.
EOF

echo "Cursor Projects root: $HOME_MAP"
echo "  created-in-cursor -> $(ls -1 "$CREATED")"
echo "  imported-and-modified -> $(ls -1 "$IMPORTED")"
echo "  backdrop DB -> $BACKDROP"
