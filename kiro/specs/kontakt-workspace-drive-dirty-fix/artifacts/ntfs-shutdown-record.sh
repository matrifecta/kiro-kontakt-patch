#!/usr/bin/env bash
#
# ntfs-shutdown-record.sh  ->  installs to /usr/lib/systemd/system-shutdown/
#
# Runs in the FINAL shutdown phase (after everything is unmounted, just before
# the machine powers off/reboots). systemd passes the verb as $1
# (poweroff | reboot | halt | kexec).
#
# Purpose: leave a durable record that an ORDERLY shutdown reached its final
# phase, plus a final sync. If the Workspace drive is later found dirty at the
# next boot (see ntfs-dirty-detect) AND there is NO matching shutdown-record for
# the prior session, that points at a HARD POWER LOSS / crash (systemd never got
# here) rather than an orderly-shutdown problem.
#
# The record is written to /var/log (persistent) because at this phase most
# filesystems are already read-only/unmounted; /run is still writable and the
# journal may still capture systemd-cat, so we log to BOTH.
#
# Install: sudo install -o root -g root -m 0755 ntfs-shutdown-record.sh \
#            /usr/lib/systemd/system-shutdown/ntfs-shutdown-record.sh
#
set -u

VERB="${1:-unknown}"
STAMP="$(date -u +%Y-%m-%dT%H:%M:%SZ 2>/dev/null || echo unknown)"
MSG="ORDERLY shutdown final phase reached: verb=${VERB} at ${STAMP}"

# Final flush of any last writes.
sync

# Journal (may or may not still persist at this late phase).
echo "$MSG" | systemd-cat -t ntfs-shutdown-record -p info 2>/dev/null || true

# Durable marker on the root fs (still mounted read-only at this phase on most
# systems; try, but never fail the shutdown).
{
    echo "$MSG"
} >> /var/lib/ntfs-shutdown-record.log 2>/dev/null || true

exit 0
