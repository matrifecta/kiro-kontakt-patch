# Studio Hub

Crtomir’s CachyOS studio map, rebuilt from the Kiro archive at `/home/phnx/KIRO`.

## Cursor Projects (home folder)

On the studio machine (and in this Cloud session after bootstrap):

```text
~/Cursor Projects/
  created-in-cursor/          # new Cursor projects (Studio Hub is first)
  imported-and-modified/      # Kiro projects, editable working copies
  kiro-backdrop.sqlite        # frozen Kiro achievements + cited paths
  kiro-backdrop.json
```

Create or refresh it:

```bash
bash tools/bootstrap-cursor-projects.sh
```

On CachyOS that becomes `/home/phnx/Cursor Projects`. The SQLite file is the backdrop. The folders are the living maps.

## Run locally

```bash
npm install
npm run dev
```

Opens at [http://127.0.0.1:43147](http://127.0.0.1:43147).

MIDI bridge extras (optional, not needed for the hub):

```bash
pip install -r requirements-midi.txt   # python-osc, python-rtmidi
```

`kontakt_scan.py` uses the Python standard library only.

## What was cohesive enough to continue

| Project | In the archive | Can start? |
|---------|----------------|------------|
| Kontakt workspace | Specs + 180 artifacts + catalogs | Yes (live disks stay on CachyOS) |
| Wine optimization | Specs + scanner + scan TSVs | Yes |
| Turing installer | Bugfix spec + `install_turing.sh` | Yes, carefully |
| USB audio resume | Spec only, tasks unchecked | Start from spec — no hook script shipped |
| Turing wake recovery | `requirements.md` only | Not enough alone |
| TouchOSC MIDI bridge | Script only, no spec | Needs python-osc + python-rtmidi |

Live things this Cloud session cannot see: `/mnt/workspace`, `/mnt/storage`, `/mnt/wd_black`, `/mnt/btrfs_disk`, `~/.wine`, `komplete.db3`, systemd units.

## Cursor vs Kiro access

This Cloud Agent does **not** get a Kiro-style “approve lookup” prompt for `/home/phnx` or the web. It only sees this workspace unless you upload files. On local Cursor Desktop, the agent can read the folder you opened as the project; extra MCP servers may ask for auth. It will not silently mount CachyOS drives from here.

Cursor does **not** ship Kiro’s Python plugins. This environment has Python 3.12. `python-osc` and `python-rtmidi` were installed here for the MIDI bridge. They are not installed on CachyOS until you run the pip line above.

## Confirmed endpoints (CachyOS)

1. **Kontakt standalone** — `kiro/scripts/launch_kontakt_wineasio.sh` (WineASIO, quantum 128).
2. **Reaper** — native PipeWire/JACK @128, `jack_rtprio=88`, Kontakt via yabridge.
3. **Workspace** — `/mnt/workspace` on ntfs-3g (not ntfs3).
