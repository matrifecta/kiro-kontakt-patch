export type ProjectStatus = "confirmed" | "applied" | "open" | "watch"

export type KiroProject = {
  slug: string
  name: string
  folder: string
  status: ProjectStatus
  summary: string
  outcome: string
}

export const projects: KiroProject[] = [
  {
    slug: "kontakt-workspace",
    name: "Kontakt workspace",
    folder: "kontakt-workspace-drive-dirty-fix",
    status: "confirmed",
    summary:
      "Kontakt 8 Portable on CachyOS: NTFS Workspace drive, blank tiles, path hygiene, library catalogs, and the audio clock.",
    outcome:
      "Drive mounts via ntfs-3g. WineASIO @128 and Reaper @128 are the confirmed endpoints. Kontakt and DecentSampler catalogs are built.",
  },
  {
    slug: "kontakt-wine",
    name: "Wine optimization",
    folder: "kontakt-wine-optimization",
    status: "applied",
    summary:
      "Cut the ~10,260 failed startup lookups, normalize Wine drive letters, and scan 1TB+ of Kontakt content without touching the DB.",
    outcome:
      "Linux-side scanner (kontakt_scan.py), canonical Z:/D:/E:/F: mapping plan, and auditable Player vs Custom lists.",
  },
  {
    slug: "usb-audio",
    name: "USB audio resume",
    folder: "usb-audio-resume",
    status: "applied",
    summary:
      "After suspend, USB audio cards often stay dead until a physical replug. Soft unbind/rebind on wake instead.",
    outcome:
      "Systemd resume hook finds the card by vendor:product ID, rebinds it, optionally restarts PipeWire.",
  },
  {
    slug: "turing-wake",
    name: "Turing wake recovery",
    folder: "turing-wake-recovery",
    status: "applied",
    summary:
      "Turing Smart Screen Rev C loses its TTY after sleep. Old fix power-cycled the whole USB hub and killed audio.",
    outcome:
      "Targeted recovery: wait for natural re-enumeration, update COM_PORT, restart only the display container.",
  },
  {
    slug: "turing-installer",
    name: "Turing installer",
    folder: "turing-installer-pid-theme-fix",
    status: "applied",
    summary:
      "install_turing.sh assigned TURZX screens in random USB order and skipped default themes for 3.5\", 8.8\", and 10\".",
    outcome:
      "Deterministic PID order (8.8\" before 10\") and size-correct default themes plus 10\" theme filter.",
  },
]

export const endpoints = [
  {
    name: "Kontakt standalone",
    detail: "WineASIO @128 via launch_kontakt_wineasio.sh, graph 128 @ 44.1 kHz, JACK node.latency 128/44100. Crackle cleared.",
  },
  {
    name: "Reaper + yabridge",
    detail: "Native PipeWire/JACK @128, ERR 0, jack_rtprio=88. Kontakt as .so. Do not mix with a forced standalone quantum.",
  },
  {
    name: "Workspace volume",
    detail: "/mnt/workspace on /dev/sdb2 (UUID B82064122063D642). ntfs-3g, not ntfs3 — ntfs3 marks the volume dirty under Wine writes and blanks tiles.",
  },
]

export const openItems = [
  {
    title: "One old Reaper project",
    detail:
      "Zauberwinds crash is project-local: a doubled DecentSampler base path in that session chunk. Fresh DS inserts are healthy. Rescue: FX offline → delete/re-add DS → save.",
  },
  {
    title: "EWQL RA SNPID",
    detail:
      "Bug C: .nicnt A02 vs instrument A05. Content-side mismatch, not a mount or F: path problem. Needs a matching-SNPID package or a clear flag so it stops looking like a drive fault.",
  },
  {
    title: "Catalog snapshots",
    detail:
      "HTML catalogs are a 10 Sep 2026 snapshot. Rebuild on the studio machine with build-kontakt-catalog-html.sh / build-ds-catalog-html.sh, then drop the portable files back here.",
  },
]

export const runbook = [
  {
    title: "Launch Kontakt (WineASIO @128)",
    body: `QUANTUM=128
RATE=44100
~/KIRO/launch_kontakt_wineasio.sh

# In Kontakt: Audio → WineASIO, buffer 128, Fixed buffersize UNCHECKED.`,
  },
  {
    title: "If Workspace is missing after boot",
    body: `mountpoint -q /mnt/workspace || echo "Workspace not mounted"
findmnt /mnt/workspace
dmesg | grep -iE 'ntfs|dirty'
journalctl -t workspace-check -b --no-pager

# ntfs3 dirty refusal is the old failure mode.
# Current fstab target is ntfs-3g (fuseblk) for workspace, storage, wd_black.`,
  },
  {
    title: "Confirmed ntfs-3g fstab lines",
    body: `UUID=B82064122063D642 /mnt/workspace ntfs-3g rw,uid=1000,gid=1000,dmask=022,fmask=133,big_writes,nofail,x-systemd.device-timeout=5 0 0
UUID=D44A1FC54A1FA2F2 /mnt/storage   ntfs-3g rw,uid=1000,gid=1000,dmask=022,fmask=133,big_writes,nofail,x-systemd.device-timeout=5 0 0
UUID=58EAAC8AEAAC65CA /mnt/wd_black  ntfs-3g rw,uid=1000,gid=1000,dmask=022,fmask=133,big_writes,nofail,x-systemd.device-timeout=5 0 0`,
  },
  {
    title: "Wine drive letters (dosdevices)",
    body: `C:  ../drive_c
D:  /mnt/workspace     # canonical content
E:  /mnt/storage
F:  keep until leftover F:\\ baked paths are gone; then wd_black
Z:  /                  # Player libs already use Z:\\mnt\\workspace\\...
L:/M:  controllers, not content`,
  },
  {
    title: "Scan Kontakt folders (read-only)",
    body: `python3 kiro/scripts/kontakt_scan.py \\
  "/mnt/workspace/VST Install/Kontakt Vst-i" \\
  "/mnt/storage" \\
  "/mnt/wd_black" \\
  --out /tmp/kontakt-scan`,
  },
  {
    title: "Rebuild catalogs on CachyOS",
    body: `cd kiro/specs/kontakt-workspace-drive-dirty-fix/artifacts
./build-kontakt-catalog-html.sh both
./build-ds-catalog-html.sh both
# Copy *-portable.html into this app's public/catalogs/`,
  },
]

export const nav = [
  { href: "/", label: "Studio" },
  { href: "/kontakt", label: "Kontakt" },
  { href: "/decent-sampler", label: "DecentSampler" },
  { href: "/map", label: "Kiro map" },
  { href: "/runbook", label: "Runbook" },
]

export const statusLabel: Record<ProjectStatus, string> = {
  confirmed: "Confirmed working",
  applied: "Applied",
  open: "Open",
  watch: "Watch",
}
