#!/usr/bin/env bash
#
# backup-known-good-state.sh
#
# Snapshot the CLEAN, known-good Kontakt/Wine configuration state (2026-09-07) so it
# can be recreated wholesale. Captures all DB/config/registration/mount/launcher state
# but EXCLUDES the sample library files (they live on the fast drives / Workspace and
# are far too big to snapshot).
#
# Output: a timestamped folder + a tar.gz, with a MANIFEST and RESTORE notes.
# Choose a DEST on a drive with a little room (defaults to WD Black).
#
# Run with Kontakt CLOSED so komplete.db3 is quiescent.

set -u
KP="/mnt/workspace/VST Install/Kontakt Portable"
UD="${KP}/UserData"
K8="${UD}/Kontakt 8"
WINE="${HOME}/.wine"
STAMP="$(date +%Y%m%d_%H%M%S)"
DEST="${1:-/mnt/wd_black}/kontakt-known-good-${STAMP}"

if pgrep -fi 'Kontakt 8.exe' | grep -qv grep; then
  echo "ABORT: Kontakt running. File->Exit cleanly first."; exit 1
fi

echo "=== creating ${DEST} ==="
mkdir -p "${DEST}/kontakt_userdata" "${DEST}/wine" "${DEST}/system" "${DEST}/repo"

# ---- 1. Kontakt UserData: DB + config + tile cache + hints (NO sample folders) ----
echo "=== Kontakt UserData (DBs, Settings.cfg, LibrariesCache, hints) ==="
copy() { [ -e "$1" ] && cp -av "$1" "$2" || echo "  (skip, missing: $1)"; }
copy "${K8}/komplete.db3"          "${DEST}/kontakt_userdata/"
copy "${K8}/user_config.db3"       "${DEST}/kontakt_userdata/"
copy "${K8}/LibrariesCache"        "${DEST}/kontakt_userdata/"
copy "${UD}/Settings.cfg"          "${DEST}/kontakt_userdata/"
# LibraryHints + any registration XML under UserData (small text/xml only)
find "${UD}" -maxdepth 3 -iname "LibraryHints.xml" -exec cp -av {} "${DEST}/kontakt_userdata/" \; 2>/dev/null
copy "${UD}/Service Center/pal.db" "${DEST}/kontakt_userdata/"

# integrity note for the DB we're snapshotting
echo "=== record DB integrity + counts (via python, KOMPLETE collation) ==="
python3 - "$K8/komplete.db3" > "${DEST}/kontakt_userdata/DB_STATE.txt" 2>&1 <<'PY'
import sqlite3,sys
db=sys.argv[1]
def k(a,b):
    x=(a or "").strip().casefold(); y=(b or "").strip().casefold(); return (x>y)-(x<y)
c=sqlite3.connect(f"file:{db}?mode=ro",uri=True); c.create_collation("KOMPLETE",k); cur=c.cursor()
print("content_paths:", cur.execute("SELECT COUNT(*) FROM k_content_path;").fetchone()[0])
print("sound_info:", cur.execute("SELECT COUNT(*) FROM k_sound_info;").fetchone()[0])
bad=sum(1 for r in cur.execute("PRAGMA integrity_check;") if r[0]!="ok")
print("integrity:", "ok" if bad==0 else f"{bad} issues")
print("--- content paths ---")
for r in cur.execute("SELECT id,content_type,visible,path FROM k_content_path;"):
    print("  ",r)
c.close()
PY

# ---- 2. Wine prefix: drive mappings + registry (NOT the whole prefix) ----
echo "=== Wine dosdevices + registry ==="
if [ -d "${WINE}/dosdevices" ]; then
  # copy symlinks AS symlinks (-P) so Z:->/ , D:->/mnt/workspace etc. are preserved literally
  cp -avP "${WINE}/dosdevices" "${DEST}/wine/"
  ls -la "${WINE}/dosdevices" > "${DEST}/wine/dosdevices_listing.txt"
fi
copy "${WINE}/system.reg"  "${DEST}/wine/"
copy "${WINE}/user.reg"    "${DEST}/wine/"
copy "${WINE}/userdef.reg" "${DEST}/wine/"

# ---- 3. System: fstab + systemd units + yabridge ----
echo "=== system config (fstab, units, yabridge) ==="
copy "/etc/fstab" "${DEST}/system/"
for u in ntfs-dirty-detect.service ntfs3-clean-unmount.service workspace-mount-check.service; do
  copy "/etc/systemd/system/${u}" "${DEST}/system/"
done
copy "/usr/local/sbin/ntfs3-clean-unmount.sh" "${DEST}/system/"
copy "/usr/local/sbin/ntfs-dirty-detect.sh"   "${DEST}/system/"
copy "${HOME}/.vst3/yabridge/yabridge.toml"   "${DEST}/system/"

# ---- 4. Repo artifacts: launchers + all the fix scripts (self-documenting) ----
echo "=== repo launchers + spec artifacts ==="
copy "${HOME}/.local/bin/launch_kontakt_wineasio.sh" "${DEST}/repo/"
copy "${HOME}/KIRO/launch_kontakt_wineasio.sh"       "${DEST}/repo/" 2>/dev/null || true
cp -av "${HOME}/KIRO/.kiro/specs/kontakt-workspace-drive-dirty-fix/artifacts" "${DEST}/repo/spec-artifacts" 2>/dev/null || true

# ---- 5. MANIFEST + RESTORE notes ----
cat > "${DEST}/MANIFEST.md" <<EOF
# Kontakt known-good state snapshot — ${STAMP}

Clean, converged state: komplete.db3 = 70 content paths (all Z:), ~30,060 presets,
0 D:/F:, integrity ok, 41.8MB. All real libraries tile via Z:; Keyscape-13 + Hy2rogen
on sdd1 (folder icon, Custom-lib limitation); EWQL RA removed (Bug C).

## Contents (config/state only — NO sample library files)
- kontakt_userdata/  komplete.db3, user_config.db3, Settings.cfg, LibrariesCache/,
                     pal.db, LibraryHints.xml, DB_STATE.txt (integrity+row dump)
- wine/              dosdevices/ (Z:/D:/F: symlinks), system.reg, user.reg, userdef.reg
- system/            /etc/fstab, ntfs-3g/systemd units, yabridge.toml
- repo/              launcher(s) + spec-artifacts/ (all fix scripts)

## What is NOT here (recreate from the drives, not this backup)
- The sample libraries themselves on /mnt/wd_black + /mnt/btrfs_disk (Kontakt Libraries/)
  and Workspace. The DB references them via Z:\mnt\... paths — restore the DB and the
  libraries resolve as long as the fast drives are mounted at the same mountpoints.

## RESTORE (to recreate this exact state)
1. Kontakt CLOSED.
2. Restore DB/config:
   cp -av kontakt_userdata/komplete.db3 "${K8}/komplete.db3"
   cp -av kontakt_userdata/user_config.db3 "${K8}/" 2>/dev/null
   cp -av kontakt_userdata/Settings.cfg "${UD}/"
   rm -rf "${K8}/LibrariesCache" && cp -av kontakt_userdata/LibrariesCache "${K8}/"
   cp -av kontakt_userdata/pal.db "${UD}/Service Center/" 2>/dev/null
3. Wine mappings (only if the prefix was rebuilt): restore dosdevices/ symlinks so
   Z:->/ , D:->/mnt/workspace , F:->/mnt/workspace as in dosdevices_listing.txt.
4. System (only if reinstalling OS): put fstab entries + units back (see system/).
5. Launch Kontakt — browser + tiles should match DB_STATE.txt.

## Fast-drive mountpoints this DB assumes
- /mnt/wd_black   (ntfs-3g)   -> Z:\mnt\wd_black\Kontakt Libraries\{Player,Custom}\...
- /mnt/btrfs_disk (btrfs)     -> Z:\mnt\btrfs_disk\Kontakt Libraries\{Player,Custom}\...
- /mnt/workspace  (ntfs-3g)   -> Z:\mnt\workspace\... (Kontakt Portable itself + User Content)
EOF

echo "=== tar it up ==="
tar -czf "${DEST}.tar.gz" -C "$(dirname "${DEST}")" "$(basename "${DEST}")" 2>/dev/null \
  && echo "  archive: ${DEST}.tar.gz" \
  || echo "  (tar skipped/failed; folder still at ${DEST})"

echo
echo "=== sizes ==="
du -sh "${DEST}" 2>/dev/null
[ -f "${DEST}.tar.gz" ] && ls -lah "${DEST}.tar.gz"
echo
echo "DONE. Snapshot at:"
echo "  ${DEST}"
echo "  ${DEST}.tar.gz"
