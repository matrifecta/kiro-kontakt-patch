#!/usr/bin/env bash
#
# check-m2-slots.sh  (READ-ONLY)
#
# Determine whether an M.2 NVMe slot is free for a future 2TB drive. We can't physically
# see the board, so we gather: motherboard model (to look up its M.2 slot count), the
# NVMe drives currently populated, and the PCIe/NVMe controller topology. NOTHING changes.
# Some sections may need sudo for full detail; they degrade gracefully without it.

set -u

echo "===== 1) Motherboard / system model (look up its M.2 slot count) ====="
for f in board_vendor board_name board_version product_name sys_vendor; do
  if [ -r "/sys/devices/virtual/dmi/id/$f" ]; then
    printf "    %-14s %s\n" "$f:" "$(cat /sys/devices/virtual/dmi/id/$f 2>/dev/null)"
  fi
done
echo "    (dmidecode -t baseboard needs sudo; run it for the exact board if the above is blank)"
echo

echo "===== 2) NVMe drives currently present (populated M.2/PCIe slots) ====="
lsblk -d -o NAME,SIZE,MODEL,TRAN 2>/dev/null | grep -iE 'nvme|NAME' | sed 's/^/    /'
echo
echo "    NVMe namespaces / controllers:"
ls -1 /dev/nvme* 2>/dev/null | sed 's/^/      /' || echo "      (none)"
echo

echo "===== 3) NVMe controllers on the PCIe bus ====="
if command -v lspci >/dev/null 2>&1; then
  lspci 2>/dev/null | grep -iE 'non-volatile memory|nvme' | sed 's/^/    /' || echo "    (no NVMe controllers listed by lspci)"
else
  echo "    (lspci not installed; try: sudo pacman -S pciutils)"
fi
echo

echo "===== 4) SATA devices (in case a slot is M.2-SATA or shares bandwidth) ====="
lsblk -d -o NAME,SIZE,MODEL,TRAN 2>/dev/null | grep -iE 'sata|NAME' | sed 's/^/    /'
echo

echo "===== 5) Per-NVMe physical PCIe link (helps map how many controllers exist) ====="
for c in /sys/class/nvme/nvme*; do
  [ -e "$c" ] || continue
  name=$(basename "$c")
  model=$(cat "$c/model" 2>/dev/null | xargs)
  addr=$(readlink -f "$c/device" 2>/dev/null | grep -oE '[0-9a-f]{4}:[0-9a-f]{2}:[0-9a-f]{2}\.[0-9a-f]' | tail -1)
  echo "    $name  '$model'  pci=$addr"
done
echo

echo "READ-ONLY. Report output back. I'll cross-reference the board model's spec"
echo "(total M.2 slots) against the populated NVMe count to tell you how many M.2 slots are free,"
echo "and flag any lane-sharing caveats (e.g. an M.2 that disables a SATA port when used)."
