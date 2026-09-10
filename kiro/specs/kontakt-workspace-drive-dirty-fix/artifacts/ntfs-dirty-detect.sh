#!/usr/bin/env bash
#
# ntfs-dirty-detect.sh
#
# Boot-time detector: reads the NTFS $Volume dirty flag on the Workspace drive
# (/dev/sdb2) BEFORE it is mounted, and logs the as-found state to the journal.
# This captures whether the drive ARRIVES dirty at boot (i.e. it was dirtied in
# the previous session / by an unclean event), which is the key evidence for
# pinning down the dirty-bit origin.
#
# ntfsinfo can only read the flag safely when the volume is NOT mounted, so the
# unit that calls this must be ordered Before=mnt-workspace.mount.
#
# Install:  sudo install -o root -g root -m 0755 ntfs-dirty-detect.sh /usr/local/sbin/ntfs-dirty-detect.sh
#
set -u

DEV="/dev/sdb2"
TAG="ntfs-dirty-detect"
LOG() { echo "$*" | systemd-cat -t "$TAG" -p "${2:-info}" 2>/dev/null || echo "[$TAG] $*"; }

# Once-per-boot guard: the mount can be pulled in via multiple paths (nofail),
# which can trigger this unit more than once. Record a per-boot stamp in /run
# (tmpfs, cleared each boot) so only the first invocation does the read.
GUARD="/run/ntfs-dirty-detect.done"
if [ -e "$GUARD" ]; then
    exit 0
fi
: > "$GUARD" 2>/dev/null || true

# Bail safely if the device is already mounted (ordering failed) — do NOT force.
if findmnt -S "$DEV" >/dev/null 2>&1; then
    LOG "$DEV already mounted before detector ran (ordering issue) — cannot read flag offline; skipping" warning
    exit 0
fi

if ! command -v ntfsinfo >/dev/null 2>&1; then
    LOG "ntfsinfo not found; cannot read dirty flag" err
    exit 0
fi

# Read the volume information flags offline. The 'dirty' bit shows up in the
# Volume Information / flags line. Capture the raw relevant lines for the log.
OUT="$(ntfsinfo -m "$DEV" 2>&1 | grep -iE 'dirty|volume flags|volume information|flags' || true)"

if [ -z "$OUT" ]; then
    LOG "read $DEV offline: no flags line returned (ntfsinfo output unexpected) — raw follows"
    ntfsinfo -m "$DEV" 2>&1 | head -20 | while IFS= read -r l; do LOG "  $l"; done
elif echo "$OUT" | grep -iq 'dirty'; then
    LOG "AT BOOT $DEV arrived DIRTY -> the volume was dirtied in the previous session or by an unclean event. Flags: $OUT" err
else
    LOG "AT BOOT $DEV arrived CLEAN. Flags: $OUT"
fi

exit 0
