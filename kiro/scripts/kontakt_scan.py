#!/usr/bin/env python3
"""
kontakt_scan.py

Read-only scanner that walks Kontakt content roots on the Linux side and classifies
each library folder so junk / incomplete content can be identified before registering
or cleaning in Kontakt. Does NOT touch Kontakt's databases.

Categories:
  player      - encoded/Player library (has a *.nicnt marker)
  custom      - loose instruments (.nki/.nkm/.nkb) with samples, no .nicnt
  presets     - user snapshots (.nksn)
  incomplete  - looks like a library but is missing pieces (e.g. instruments with
                no samples, or a .nicnt with no encoded content)
  excluded    - not Kontakt content (other plugins/effects; name or extension match)
  empty       - no recognizable content at all

Usage:
  ./kontakt_scan.py ROOT [ROOT ...] [--out DIR] [--maxdepth N]

Example:
  ./kontakt_scan.py "/mnt/workspace/VST Install/Kontakt Vst-i Folders" \
                    "/mnt/workspace/VST Install/Kontakt Vst-i" \
                    --out .kiro/specs/kontakt-wine-optimization/results/scan
"""

import os
import sys
import argparse
import datetime

# --- markers -----------------------------------------------------------------
NICNT = ".nicnt"
INSTRUMENT_EXT = {".nki", ".nkm", ".nkb"}
ENCODED_EXT = {".nkx", ".nkr", ".nkc"}
PRESET_EXT = {".nksn"}
SAMPLE_EXT = {".ncw", ".wav", ".aif", ".aiff", ".flac", ".rex", ".rx2"}

# non-Kontakt signals (name-based) -> excluded
EXCLUDE_NAME_SUBSTR = (
    "izotope", "nectar", "ozone", " rx ", "xln", "addictive",
    "amplitube", "fabfilter", "waves", "soundtoys",
)
# extensions that indicate a non-Kontakt plugin folder
NONKONTAKT_EXT = {".vst3", ".dll", ".component", ".aaxplugin"}

# dirs we never descend into (junk / non-audio / OS / games)
SKIP_DIRS = {
    "$recycle.bin", "system volume information", ".trash-1000",
    "windowsapps", "xboxgames", "program files", "program files (x86)",
    "steamlibrary", "games", "vortex mods", "valheim root", "reaper",
    "config.msi", "recovery", "msdownld.tmp", "unfinished dl", "tixati dl",
    "turing-smart-screen-python", "aax", "vst3", "vst", "win",
}


def classify(root_path):
    """Walk a single top-level library folder and return (category, stats)."""
    has_nicnt = False
    n_instruments = 0
    n_encoded = 0
    n_presets = 0
    n_samples = 0
    n_nonkontakt = 0
    total_files = 0

    name_l = os.path.basename(root_path).lower()
    name_excluded = any(s in name_l for s in EXCLUDE_NAME_SUBSTR)

    for dirpath, dirnames, filenames in os.walk(root_path):
        # prune junk dirs
        dirnames[:] = [d for d in dirnames if d.lower() not in SKIP_DIRS]
        for fn in filenames:
            total_files += 1
            ext = os.path.splitext(fn)[1].lower()
            if fn.lower().endswith(NICNT):
                has_nicnt = True
            elif ext in INSTRUMENT_EXT:
                n_instruments += 1
            elif ext in ENCODED_EXT:
                n_encoded += 1
            elif ext in PRESET_EXT:
                n_presets += 1
            elif ext in SAMPLE_EXT:
                n_samples += 1
            elif ext in NONKONTAKT_EXT:
                n_nonkontakt += 1

    stats = dict(nicnt=has_nicnt, instruments=n_instruments, encoded=n_encoded,
                 presets=n_presets, samples=n_samples, nonkontakt=n_nonkontakt,
                 files=total_files)

    # --- decision ---
    kontakt_content = (has_nicnt or n_instruments or n_encoded or n_presets)

    # A folder living under a plugins tree with plugin files and no real Kontakt
    # instruments/encoded content is a plugin, not a Kontakt library.
    path_l = root_path.lower()
    under_plugins_tree = ("vst, samples" in path_l or "/programs/" in path_l
                          or path_l.endswith("/programs"))
    if under_plugins_tree and n_instruments == 0 and n_encoded == 0 and not has_nicnt:
        return "excluded", stats

    if name_excluded and not kontakt_content:
        return "excluded", stats
    if n_nonkontakt and not kontakt_content:
        return "excluded", stats
    if not kontakt_content and n_samples == 0:
        return "empty", stats

    if has_nicnt:
        # a Player library should have encoded content or instruments
        if n_encoded == 0 and n_instruments == 0:
            return "incomplete", stats
        return "player", stats

    if n_instruments:
        # loose instruments; if there are no samples anywhere it may be broken/incomplete
        if n_samples == 0 and n_encoded == 0:
            return "incomplete", stats
        return "custom", stats

    if n_presets:
        return "presets", stats

    if n_samples:
        return "custom", stats

    return "empty", stats


def wine_letter(path):
    """Map a linux path to the Wine drive-letter form used by Kontakt."""
    mapping = [
        ("/mnt/workspace", "D:"),
        ("/mnt/storage", "E:"),
        ("/mnt/wd_black", "F:"),
    ]
    for lin, letter in mapping:
        if path.startswith(lin):
            rest = path[len(lin):].replace("/", "\\")
            return letter + rest
    # fall back to Z: root mapping
    return "Z:" + path.replace("/", "\\")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("roots", nargs="+")
    ap.add_argument("--out", default="scan_results")
    ap.add_argument("--maxdepth", type=int, default=3,
                    help="how many container levels to descend (default 3)")
    args = ap.parse_args()

    os.makedirs(args.out, exist_ok=True)
    buckets = {k: [] for k in
               ("player", "custom", "presets", "incomplete", "excluded", "empty")}

    # Folders that are containers, not libraries themselves: descend one level.
    def is_container(name):
        n = name.lower()
        return n in ("programs", "vst install", "vst, samples", "kontakt vst-i",
                     "kontakt vst-i folders", "kontakt vst-i library", "content",
                     "presets", "libraries", "documents") or "sample" in n

    # Subfolder names that indicate THIS folder is a library root (its parts live below).
    LIB_CHILD_MARKERS = {"instruments", "instrument", "samples", "multis",
                         "snapshots", "presets", "nki", "wallpaper", "documentation"}

    def looks_like_library_root(path):
        """
        A folder is a library root if it OR its immediate children contain library
        markers. We check the folder's own files AND one level of children names.
        Returns True if this whole folder should be evaluated as a single library.
        """
        try:
            with os.scandir(path) as it:
                child_dirs = []
                for e in it:
                    if e.is_file():
                        n = e.name.lower()
                        ext = os.path.splitext(n)[1]
                        if n.endswith(NICNT) or ext in INSTRUMENT_EXT \
                           or ext in ENCODED_EXT or ext in PRESET_EXT:
                            return True
                    elif e.is_dir():
                        child_dirs.append(e.name.lower())
        except (PermissionError, OSError):
            return False
        # If it has the classic library subfolders, treat it as a root.
        return any(c in LIB_CHILD_MARKERS for c in child_dirs)

    def scan_dir(base, depth):
        try:
            with os.scandir(base) as it:
                entries = sorted((e for e in it if e.is_dir()),
                                 key=lambda e: e.name.lower())
        except (PermissionError, OSError):
            return
        for e in entries:
            if e.name.lower() in SKIP_DIRS:
                continue
            # If this folder is (or contains) a complete library, classify the WHOLE
            # folder as one unit -- do not descend into its Instruments/Samples parts.
            if looks_like_library_root(e.path):
                cat, st = classify(e.path)
                buckets[cat].append((e.path, st))
                print(f"  [{cat:10}] {e.path}", file=sys.stderr)
                continue

            # Not a library root: it's a container. Descend if budget left.
            if depth > 0:
                scan_dir(e.path, depth - 1)
            else:
                cat, st = classify(e.path)
                if cat != "empty":
                    buckets[cat].append((e.path, st))
                    print(f"  [{cat:10}] {e.path}", file=sys.stderr)

    for root in args.roots:
        if not os.path.isdir(root):
            print(f"skip (not a dir): {root}", file=sys.stderr)
            continue
        print(f"scanning: {root}", file=sys.stderr)
        scan_dir(root, args.maxdepth)

    # write per-category TSVs
    stamp = datetime.datetime.now().isoformat(timespec="seconds")
    for cat, rows in buckets.items():
        fn = os.path.join(args.out, f"{cat}.tsv")
        with open(fn, "w") as f:
            f.write("linux_path\twine_path\tinstruments\tencoded\tpresets\tsamples\tnonkontakt\tfiles\n")
            for path, st in rows:
                f.write("\t".join([
                    path, wine_letter(path),
                    str(st["instruments"]), str(st["encoded"]), str(st["presets"]),
                    str(st["samples"]), str(st["nonkontakt"]), str(st["files"]),
                ]) + "\n")

    # summary
    with open(os.path.join(args.out, "summary.txt"), "w") as f:
        f.write(f"Kontakt content scan  {stamp}\n")
        f.write(f"roots: {args.roots}\n\n")
        for cat in ("player", "custom", "presets", "incomplete", "excluded", "empty"):
            f.write(f"{cat:12} {len(buckets[cat])}\n")

    print("\n=== SUMMARY ===")
    for cat in ("player", "custom", "presets", "incomplete", "excluded", "empty"):
        print(f"{cat:12} {len(buckets[cat])}")
    print(f"\nresults written to: {args.out}/")


if __name__ == "__main__":
    main()
