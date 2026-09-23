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

## Catalogs on GitHub Pages

The four HTML catalogs in `public/catalogs/` are self-contained static pages with
no build step. `.github/workflows/pages.yml` publishes `public/` to GitHub Pages
so they can be opened on a real phone or tablet — which matters because several
card behaviours (YouTube embeds, and the viewport-unit sizing the expanded card
depends on) only reproduce correctly over `http(s)`, not `file://`.

One-time setup, in the repository's **Settings → Pages**: set **Source** to
**GitHub Actions**. The workflow then runs on pushes that touch `public/`, and
can also be started by hand from the **Actions** tab (*Run workflow*).

The deployed URL is `https://<owner>.github.io/<repo>/`, which forwards to
`/catalogs/` — a short list linking to all four catalogs. Note that Pages
requires the repository to be public, unless the account's plan allows private
Pages sites.

Append `?dvhdebug=1` to a portable catalog URL to show the on-page viewport
debug overlay (live `innerWidth/Height`, `visualViewport`, resolved `100dvh` in
px, orientation, and the expanded card's rect). It persists in `localStorage`;
`?dvhdebug=0` turns it back off.

To serve the same files locally instead — for example over the LAN from the
studio machine:

```bash
python3 -m http.server 8080 --directory public
```

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

## Grok index

Frozen at `data/grok-index.json` and in `kiro-backdrop.sqlite` table `grok_index`. Hub route: `/index`.

Composer next: HTML catalogs, catalog builders, `komplete.db3` / DecentSampler XML on CachyOS. Claude after that.

This Cloud Agent does **not** get a Kiro-style “approve lookup” prompt for `/home/phnx` or the web. It only sees this workspace unless you upload files. On local Cursor Desktop, the agent can read the folder you opened as the project; extra MCP servers may ask for auth. It will not silently mount CachyOS drives from here.

Cursor does **not** ship Kiro’s Python plugins. This environment has Python 3.12. `python-osc` and `python-rtmidi` were installed here for the MIDI bridge. They are not installed on CachyOS until you run the pip line above.

## Confirmed endpoints (CachyOS)

1. **Kontakt standalone** — `kiro/scripts/launch_kontakt_wineasio.sh` (WineASIO, quantum 128).
2. **Reaper** — native PipeWire/JACK @128, `jack_rtprio=88`, Kontakt via yabridge.
3. **Workspace** — `/mnt/workspace` on ntfs-3g (not ntfs3).
