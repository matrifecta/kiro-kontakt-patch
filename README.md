# Studio Hub

Crtomir’s CachyOS studio map, rebuilt from the Kiro archive at `/home/phnx/KIRO`.

This is a local browser hub for:

- the **Kontakt** and **DecentSampler** portable HTML catalogs
- the **five Kiro specs** (Kontakt workspace, Wine optimization, USB audio resume, Turing wake recovery, Turing installer)
- the **runbook** for the confirmed 128 @ 44.1 kHz endpoints

It does not control Wine, PipeWire, or NTFS from this machine. Those commands belong on the Plasma box.

## Run locally

```bash
npm install
npm run dev
```

Opens at [http://127.0.0.1:43147](http://127.0.0.1:43147).

```bash
npm run build
npm start -- --port 43147
```

## What’s in the repo

| Path | Contents |
|------|----------|
| `app/` | Next.js hub (Studio, catalogs, Kiro map, runbook) |
| `public/catalogs/` | Portable HTML catalogs (10 Sep 2026 snapshot) |
| `data/` | Library names + keywords extracted from those catalogs |
| `kiro/specs/` | Original Kiro specs, tasks, and artifacts |
| `kiro/scripts/` | `launch_kontakt_wineasio.sh`, `kontakt_scan.py`, Turing installer, MIDI bridge |

## Confirmed endpoints (CachyOS)

1. **Kontakt standalone** — `kiro/scripts/launch_kontakt_wineasio.sh` (WineASIO, quantum 128).
2. **Reaper** — native PipeWire/JACK @128, `jack_rtprio=88`, Kontakt via yabridge.
3. **Workspace** — `/mnt/workspace` on ntfs-3g (not ntfs3). ntfs3 marks the volume dirty under Wine writes and blanks tiles.

Rebuild catalogs on the studio machine with `build-kontakt-catalog-html.sh both` and `build-ds-catalog-html.sh both`, then replace the files in `public/catalogs/`.
