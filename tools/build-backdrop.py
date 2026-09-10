#!/usr/bin/env python3
"""Build the frozen Kiro backdrop DB + JSON maps from imported specs/scripts."""

from __future__ import annotations

import json
import re
import sqlite3
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KIRO = ROOT / "kiro"
DATA = ROOT / "data"
SKIP_DIRS = {".git", "node_modules", "__pycache__", "scan"}
SKIP_NAMES = {
    "ds-lib-missing-art.txt",
    "ds-library-inventory.txt",
    "ds-desc-probe.txt",
    "decentsampler-analysis.txt",
    "kontakt-libs-probe.txt",
    "nonds-content-probe.txt",
    "extract-decentsampler-run.log",
    "tools-check-output.txt",
}

PATH_RE = re.compile(
    r"(?:"
    r"/home/phnx[^\s\"'`)]+"
    r"|/mnt/[a-zA-Z0-9_./ +'-]+"
    r"|/usr/local/[a-zA-Z0-9_./-]+"
    r"|/etc/[a-zA-Z0-9_./-]+"
    r"|~/\.wine[^\s\"'`)]*"
    r"|~/\.config/[^\s\"'`)]+"
    r"|~/\.vst3[^\s\"'`)]*"
    r"|~/DS Libraries All[^\s\"'`)]*"
    r"|~/\.cache/[^\s\"'`)]+"
    r")"
)

PROJECTS = [
    {
        "slug": "studio-hub",
        "name": "Studio Hub",
        "map": "created-in-cursor",
        "origin": "cursor",
        "cohesion": "complete",
        "kiro_folder": None,
        "working_relpath": "created-in-cursor/studio-hub",
        "summary": "This Cursor project: catalogs, two maps, runbook, Kiro backdrop DB.",
        "missing": [],
        "can_start": True,
        "start_note": "Already running. Next work lands here or as a sibling under created-in-cursor/.",
    },
    {
        "slug": "kontakt-workspace",
        "name": "Kontakt workspace",
        "map": "imported-and-modified",
        "origin": "kiro",
        "cohesion": "complete",
        "kiro_folder": "kontakt-workspace-drive-dirty-fix",
        "working_relpath": "imported-and-modified/kontakt-workspace-drive-dirty-fix",
        "summary": "Specs, 180+ artifacts, catalogs, launchers. Live disks and komplete.db3 stay on CachyOS.",
        "missing": [
            "/mnt/workspace (komplete.db3, Kontakt Portable, NI Resources)",
            "/mnt/wd_black and /mnt/btrfs_disk library trees",
            "Live systemd units and /etc/fstab",
            "~/.wine prefix",
        ],
        "can_start": True,
        "start_note": "Yes — continue from artifacts + catalogs. Machine-side verify still needs the CachyOS mounts.",
    },
    {
        "slug": "kontakt-wine",
        "name": "Wine optimization",
        "map": "imported-and-modified",
        "origin": "kiro",
        "cohesion": "complete",
        "kiro_folder": "kontakt-wine-optimization",
        "working_relpath": "imported-and-modified/kontakt-wine-optimization",
        "summary": "Requirements, design, scanner, and prior scan TSVs.",
        "missing": ["Live NTFS roots to re-scan", "Wine dosdevices on this VM"],
        "can_start": True,
        "start_note": "Yes — scanner is stdlib Python. Re-run it on CachyOS against the three mounts.",
    },
    {
        "slug": "usb-audio",
        "name": "USB audio resume",
        "map": "imported-and-modified",
        "origin": "kiro",
        "cohesion": "spec-only",
        "kiro_folder": "usb-audio-resume",
        "working_relpath": "imported-and-modified/usb-audio-resume",
        "summary": "Full spec. Tasks are unchecked. No hook script shipped in the archive.",
        "missing": [
            "usb-audio-resume.sh",
            "usb-audio-resume.service",
            "/etc/usb-audio-resume.conf (USB_ID of the SSL interface)",
        ],
        "can_start": True,
        "start_note": "Start from the spec, not from existing code. Implementation is still to write.",
    },
    {
        "slug": "turing-wake",
        "name": "Turing wake recovery",
        "map": "imported-and-modified",
        "origin": "kiro",
        "cohesion": "spec-only",
        "kiro_folder": "turing-wake-recovery",
        "working_relpath": "imported-and-modified/turing-wake-recovery",
        "summary": "Requirements only — no design, tasks, or recovery service in the archive.",
        "missing": [
            "design.md / tasks.md",
            "Wake recovery service + config",
            "Container COM_PORT mappings",
        ],
        "can_start": False,
        "start_note": "Not enough to implement blindly. Need the missing spec files or a live Turing install dump.",
    },
    {
        "slug": "turing-installer",
        "name": "Turing installer",
        "map": "imported-and-modified",
        "origin": "kiro",
        "cohesion": "partial",
        "kiro_folder": "turing-installer-pid-theme-fix",
        "working_relpath": "imported-and-modified/turing-installer-pid-theme-fix",
        "summary": "Bugfix + design plus install_turing.sh in kiro/scripts.",
        "missing": ["Live Podman containers and screen config.yaml files"],
        "can_start": True,
        "start_note": "Yes — installer script is here. Confirm against the machine before re-running it.",
    },
    {
        "slug": "touchosc-bridge",
        "name": "TouchOSC MIDI bridge",
        "map": "imported-and-modified",
        "origin": "kiro",
        "cohesion": "partial",
        "kiro_folder": None,
        "working_relpath": "imported-and-modified/touchosc-midi-bridge",
        "summary": "Standalone script in the KIRO root. Not a Kiro spec folder.",
        "missing": ["python-osc", "python-rtmidi", "qpwgraph MIDI route on CachyOS"],
        "can_start": True,
        "start_note": "Needs python-osc + python-rtmidi. Script is otherwise self-contained.",
    },
]

CANONICAL_ROOTS = [
    {"path": "/home/phnx/KIRO", "role": "Original Kiro tree on CachyOS", "on_this_machine": False},
    {"path": "~/Cursor Projects", "role": "Cursor root map (created + imported)", "on_this_machine": True},
    {"path": "/mnt/workspace", "role": "Kontakt Portable, komplete.db3, NI Resources", "on_this_machine": False},
    {"path": "/mnt/storage", "role": "Second NTFS content drive (E:)", "on_this_machine": False},
    {"path": "/mnt/wd_black", "role": "Heavy libraries, DS Libraries, known-good snapshots", "on_this_machine": False},
    {"path": "/mnt/btrfs_disk", "role": "Light Kontakt + most DecentSampler libraries", "on_this_machine": False},
    {"path": "/mnt/win_system", "role": "Windows system partition (ntfs-3g)", "on_this_machine": False},
    {"path": "~/.wine", "role": "Shared Wine prefix (standalone + yabridge)", "on_this_machine": False},
    {"path": "~/.vst3/yabridge", "role": "Kontakt 8 Portable .so bridge", "on_this_machine": False},
    {"path": "~/.config/DecentSampler/Sample Libraries", "role": "SAMPLE STORE DecentSampler bundles", "on_this_machine": False},
    {"path": "~/.config/pipewire", "role": "Quantum / JACK latency drop-ins", "on_this_machine": False},
    {"path": "/etc/fstab", "role": "ntfs-3g mounts for workspace/storage/wd_black", "on_this_machine": False},
    {"path": "/etc/usb-audio-resume.conf", "role": "Planned USB audio hook config (not written yet)", "on_this_machine": False},
    {"path": "/usr/local/sbin", "role": "ntfs unmount / dirty-detect helpers", "on_this_machine": False},
]


def iter_text_files(base: Path):
    for path in base.rglob("*"):
        if not path.is_file():
            continue
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if path.name in SKIP_NAMES:
            continue
        if path.suffix.lower() not in {
            ".sh",
            ".py",
            ".md",
            ".toml",
            ".service",
            ".conf",
        }:
            continue
        yield path


def clean_path(raw: str) -> str:
    value = raw.rstrip(".,;:)'\"`] ")
    # Drop truncated / junk matches from prose (Adobe installers, etc.)
    if "Adobe" in value or "BRUSH" in value or "PROGRAMS/VST" in value:
        return ""
    return value


def collect_refs() -> list[dict]:
    counts: dict[str, dict] = {}
    for path in iter_text_files(KIRO):
        try:
            text = path.read_text(errors="ignore")
        except OSError:
            continue
        for match in PATH_RE.finditer(text):
            value = clean_path(match.group(0))
            if not value or len(value) < 4:
                continue
            rec = counts.setdefault(
                value,
                {"path": value, "count": 0, "files": set()},
            )
            rec["count"] += 1
            rec["files"].add(str(path.relative_to(ROOT)))
    rows = []
    for rec in counts.values():
        rows.append(
            {
                "path": rec["path"],
                "count": rec["count"],
                "files": sorted(rec["files"])[:12],
                "kind": classify(rec["path"]),
            }
        )
    rows.sort(key=lambda r: (-r["count"], r["path"]))
    return rows


def is_display_path(path: str) -> bool:
    junk = ("{", "}", "\\", "---", " -maxdepth", " free", " + ", " 2", " outside")
    if any(token in path for token in junk):
        return False
    if path.count("/mnt/") > 1:
        return False
    return True


def classify(path: str) -> str:
    if path.startswith("/mnt/workspace"):
        return "workspace-ntfs"
    if path.startswith("/mnt/storage"):
        return "storage-ntfs"
    if path.startswith("/mnt/wd_black"):
        return "wd-black-ntfs"
    if path.startswith("/mnt/btrfs_disk"):
        return "btrfs-libraries"
    if path.startswith("/mnt/win_system"):
        return "windows-system"
    if path.startswith("/home/phnx"):
        return "cachyos-home"
    if path.startswith("~/.wine") or path.startswith("~/.vst3"):
        return "wine-prefix"
    if "DecentSampler" in path:
        return "decent-sampler"
    if path.startswith("/etc"):
        return "system-config"
    if path.startswith("/usr/local"):
        return "installed-helper"
    if path.startswith("~/.config/pipewire") or "jack.conf" in path:
        return "pipewire"
    return "other"


def write_sqlite(db_path: Path, projects: list[dict], refs: list[dict]) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        db_path.unlink()
    con = sqlite3.connect(db_path)
    cur = con.cursor()
    cur.executescript(
        """
        CREATE TABLE projects (
          slug TEXT PRIMARY KEY,
          name TEXT NOT NULL,
          map TEXT NOT NULL,
          origin TEXT NOT NULL,
          cohesion TEXT NOT NULL,
          kiro_folder TEXT,
          working_relpath TEXT NOT NULL,
          summary TEXT NOT NULL,
          can_start INTEGER NOT NULL,
          start_note TEXT NOT NULL
        );
        CREATE TABLE project_gaps (
          slug TEXT NOT NULL,
          missing TEXT NOT NULL
        );
        CREATE TABLE filesystem_refs (
          path TEXT PRIMARY KEY,
          kind TEXT NOT NULL,
          count INTEGER NOT NULL
        );
        CREATE TABLE filesystem_ref_files (
          path TEXT NOT NULL,
          file TEXT NOT NULL
        );
        """
    )
    for project in projects:
        cur.execute(
            """INSERT INTO projects VALUES (?,?,?,?,?,?,?,?,?,?)""",
            (
                project["slug"],
                project["name"],
                project["map"],
                project["origin"],
                project["cohesion"],
                project["kiro_folder"],
                project["working_relpath"],
                project["summary"],
                int(project["can_start"]),
                project["start_note"],
            ),
        )
        for gap in project["missing"]:
            cur.execute("INSERT INTO project_gaps VALUES (?,?)", (project["slug"], gap))
    for ref in refs:
        cur.execute(
            "INSERT INTO filesystem_refs VALUES (?,?,?)",
            (ref["path"], ref["kind"], ref["count"]),
        )
        for file in ref["files"]:
            cur.execute(
                "INSERT INTO filesystem_ref_files VALUES (?,?)",
                (ref["path"], file),
            )
    con.commit()
    grok_path = DATA / "grok-index.json"
    if grok_path.exists():
        grok = json.loads(grok_path.read_text())
        cur.execute(
            "CREATE TABLE grok_index (key TEXT PRIMARY KEY, value TEXT NOT NULL)"
        )
        cur.execute(
            "INSERT INTO grok_index VALUES ('frozen_at', ?)", (grok["frozen_at"],)
        )
        cur.execute(
            "INSERT INTO grok_index VALUES ('payload', ?)", (json.dumps(grok),)
        )
        con.commit()
    con.close()


def main() -> None:
    DATA.mkdir(exist_ok=True)
    refs = collect_refs()
    payload = {
        "home_root": "~/Cursor Projects",
        "maps": [
            {
                "id": "created-in-cursor",
                "title": "Created in Cursor",
                "blurb": "Projects that start here. Studio Hub is the first.",
            },
            {
                "id": "imported-and-modified",
                "title": "Imported and modified",
                "blurb": "Kiro work, editable. The SQLite file is the frozen backdrop — do not treat it as the working tree.",
            },
        ],
        "projects": PROJECTS,
        "canonical_roots": CANONICAL_ROOTS,
        "filesystem_refs": [r for r in refs if is_display_path(r["path"])],
        "ref_kinds": sorted({r["kind"] for r in refs}),
        "ref_count": len(refs),
    }
    (DATA / "maps.json").write_text(json.dumps(payload, indent=2) + "\n")
    write_sqlite(DATA / "kiro-backdrop.sqlite", PROJECTS, refs)
    print(f"projects {len(PROJECTS)} refs {len(refs)} -> data/maps.json + data/kiro-backdrop.sqlite")


if __name__ == "__main__":
    main()
