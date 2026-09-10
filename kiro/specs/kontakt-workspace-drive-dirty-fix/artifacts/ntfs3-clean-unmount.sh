#!/usr/bin/env bash
#
# ntfs3-clean-unmount.sh
#
# Cleanly unmount the ntfs3 NTFS volumes (Workspace, Storage, WD Black) before
# shutdown/reboot/hibernate, behind a write-quiesce gate so the NTFS dirty bit
# is NOT left set for the ntfs3 kernel driver to refuse on the next boot.
#
# Design: called as ExecStop of ntfs3-clean-unmount.service (a RemainAfterExit
# oneshot) so it runs on the way DOWN, ordered Before umount.target /
# shutdown.target / systemd-hibernate.service. fstab remounts on next boot.
#
# NON-DESTRUCTIVE: if a volume cannot be quiesced within the timeout, it LOGS a
# visible failure to the journal and SKIPS it. It NEVER force-unmounts (forcing
# would defeat the whole purpose by risking a dirty volume).
#
# Install:  sudo cp ntfs3-clean-unmount.sh /usr/local/sbin/
#           sudo chmod 755 /usr/local/sbin/ntfs3-clean-unmount.sh
#
set -u

TAG="ntfs3-unmount"
LOG() { echo "$*" | systemd-cat -t "$TAG" -p "${2:-info}" 2>/dev/null || echo "[$TAG] $*"; }

# Mountpoints to protect. These are the three ntfs3 drives.
# win_system is intentionally EXCLUDED (it uses ntfs-3g/fuseblk, which self-heals).
MOUNTS=(
    /mnt/workspace
    /mnt/storage
    /mnt/wd_black
)

TIMEOUT=20          # max seconds to wait for a single mount to go idle
DIRTY_PAGES_MAX=8   # tolerate trivial residual dirty-page accounting (in kB from /proc/meminfo)

# Flush everything once up front.
sync

overall_rc=0

for MP in "${MOUNTS[@]}"; do
    if ! mountpoint -q "$MP"; then
        LOG "$MP not mounted, skipping"
        continue
    fi

    DEV="$(findmnt -no SOURCE "$MP" 2>/dev/null || echo '?')"
    deadline=$(( $(date +%s) + TIMEOUT ))
    clean=0

    while [ "$(date +%s)" -lt "$deadline" ]; do
        sync

        # 1) No process may hold the mount open.
        if command -v fuser >/dev/null 2>&1 && fuser -m "$MP" >/dev/null 2>&1; then
            LOG "$MP busy (a process holds it open), retrying"
            sleep 1
            continue
        fi

        # 2) No global dirty/writeback pages pending (coarse but effective gate).
        DIRTY="$(awk '/^Dirty:/{print $2}' /proc/meminfo 2>/dev/null)"
        WB="$(awk '/^Writeback:/{print $2}' /proc/meminfo 2>/dev/null)"
        # 3) Corroborate via /proc/vmstat page counters.
        NRWB="$(awk '/^nr_writeback /{print $2}' /proc/vmstat 2>/dev/null)"

        if [ "${DIRTY:-9999}" -le "$DIRTY_PAGES_MAX" ] \
           && [ "${WB:-9999}" -eq 0 ] \
           && [ "${NRWB:-9999}" -eq 0 ]; then
            clean=1
            break
        fi

        LOG "$MP writeback pending (Dirty=${DIRTY}kB Writeback=${WB}kB nr_writeback=${NRWB}), retrying"
        sleep 1
    done

    if [ "$clean" -eq 1 ] && umount "$MP" 2>/dev/null; then
        LOG "$MP unmounted cleanly (dev=$DEV)"
    else
        LOG "FAILURE: could not cleanly unmount $MP within ${TIMEOUT}s (dev=$DEV) -- NOT forcing. Volume may be left dirty; check what held it open." err
        overall_rc=1
    fi
done

# Return non-zero if any volume failed to quiesce, so the failure is visible in
# `systemctl status` / the shutdown transaction, but do not block teardown.
exit "$overall_rc"
