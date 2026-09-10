# Backup & Restore Notes (baseline before any mutation)

Created: 2026-09-01

## What was backed up

Kontakt UserData backups live in:
`/mnt/workspace/VST Install/Kontakt Portable/UserData/_kiro_backup_20260901/`

- `komplete.db3` (42M) — main Kontakt content/library database
- `user_config.db3` (53k) — user configuration
- `NI Resources/` — resource + database tree (categories.db, shortname.db, color.db, etc.)
- `Service Center/` — pal.db and related

Wine drive-letter symlinks backup:
`~/.wine/dosdevices.bak_20260901/` (all symlinks preserved via `cp -a`)

## Live dosdevices state at backup time

    c: -> ../drive_c
    d: -> /mnt/workspace
    f: -> /mnt/workspace        (alias added during earlier troubleshooting)
    w: -> /mnt/win_system
    z: -> /
    e: -> /run/media/phnx/LAUNCHPAD   (controller)
    j: -> /run/media/phnx/LCXL        (controller)
    e:: f:: g:: h:: i:: j::            (raw device nodes -- leave untouched)

(Note: redundant `s:` alias already removed prior to this backup.)

## Restore procedure

Kontakt MUST be closed before restoring databases.

Restore a single database:

    cp -a "/mnt/workspace/VST Install/Kontakt Portable/UserData/_kiro_backup_20260901/komplete.db3" \
          "/mnt/workspace/VST Install/Kontakt Portable/UserData/Kontakt 8/komplete.db3"

Restore NI Resources (replace the live folder):

    rm -rf "/mnt/workspace/VST Install/Kontakt Portable/UserData/NI Resources"
    cp -a "/mnt/workspace/VST Install/Kontakt Portable/UserData/_kiro_backup_20260901/NI Resources" \
          "/mnt/workspace/VST Install/Kontakt Portable/UserData/NI Resources"

Restore Wine drive letters:

    rm -rf ~/.wine/dosdevices
    cp -a ~/.wine/dosdevices.bak_20260901 ~/.wine/dosdevices

## Baseline metrics (results/baseline.txt)

    db_sidecar          3716
    resource_image      2797
    resource_dist_db     737
    controller_probe     420
    library_content       43
    other               2547
    TOTAL_failed       10260
