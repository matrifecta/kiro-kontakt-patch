#!/usr/bin/env python3
"""Update Legend/Guide copy for landscape KW nest-toggle vs portrait one-step hide."""
from __future__ import annotations

import os
import tempfile
from pathlib import Path

ROOT = Path("/home/phnx/kiro-kontakt-patch/public/catalogs")
FILES = [
    ROOT / "KONTAKT-CATALOG.html",
    ROOT / "DS-CATALOG.html",
    ROOT / "KONTAKT-CATALOG-portable.html",
    ROOT / "DS-CATALOG-portable.html",
]
MARK = "fix-SIDES-KW-NEST-HELP-v2"
KEEP = ("c00e3e", MARK)

REPLACEMENTS = [
    (
        '<li><b>Keywords</b> — right (Sides landscape) or paired with Search on Middle. Pills, Hide Keywords, ⛶ on the right, Collapse, Customize, Layouts. Hide + the Keywords header still control size/show. Portable ⋯ toggles category pills as transparent buttons at the top of the pills window (not a popup). Fullscreen keeps ⛶; no back arrow.</li>',
        '<li><b>Keywords</b> — right (Sides landscape) or paired with Search on Middle. Pills, Hide Keywords, ⛶ on the right, Collapse, Customize, Layouts. Landscape Sides: header <b>K</b> opens Keywords as its own full side column (not stacked with Search). The Keywords collapse arrow then toggles nest under Search (Search top, KW bottom, same column) ↔ back to the 3-pane side; that arrow does not hide Keywords — header <b>K</b> (or Hide) turns Keywords off. Portrait Sides: menus already nest on a side, so the collapse arrow is the old one-step hide/show. Portable ⋯ toggles category pills as transparent buttons at the top of the pills window (not a popup). Fullscreen keeps ⛶; no back arrow.</li>',
        "legend-kw",
    ),
    (
        '<li><b>Sides</b> — Search | content | Keywords as three panes. Content is the only scrolling card window.</li>',
        '<li><b>Sides</b> — Search | content | Keywords as three panes on landscape (Flip equivalent swaps the menu columns around the catalog). Landscape nest (collapse arrow) stacks Search above Keywords in one column, content the other. Portrait already stacks menus on a side. Content is the only scrolling card window.</li>',
        "legend-sides",
    ),
    (
        '<li><b>Portrait vs landscape</b> — desktop ≥900px still uses Sides/Middle. Portrait stacks menus (Sides) or keeps Search | Keywords above cards (Middle). Portable portrait titles split around the notch.</li>',
        '<li><b>Portrait vs landscape</b> — desktop ≥900px still uses Sides/Middle. Landscape Sides is three columns unless the Keywords collapse arrow nests KW under Search. Portrait stacks menus (Sides) or keeps Search | Keywords above cards (Middle); portrait collapse arrow stays one-step hide/show. Portable portrait titles split around the notch.</li>',
        "legend-orient",
    ),
    (
        '<li>Separators (Search split, dual-FS, Index height) drag only while <b>Customize</b> is on.</li>',
        '<li>Separators (Search split, dual-FS, Index height, and the nested Search/Keywords divider) drag only while <b>Customize</b> is on.</li>',
        "legend-sep",
    ),
    (
        '<li><b>S</b> / <b>K</b> — Search / Keywords visibility (header). Both off = content-only.</li>',
        '<li><b>S</b> / <b>K</b> — Search / Keywords visibility (header). Landscape Sides: <b>K</b> opens Keywords as its own column, never nested under Search. Both off = content-only.</li>',
        "legend-sk",
    ),
    (
        '<li><b>Flip</b> — swap the menu columns / stacked order.</li>',
        '<li><b>Flip</b> — swap the menu columns / stacked order. Landscape nested Sides: Flip moves the Search+Keywords pair together.</li>',
        "legend-flip",
    ),
    (
        '<li>Sweep <b>Clear</b> when you want the full set again. <b>Hide Keywords</b> (and the Keywords header) still size/show the pane; chosen pills stay until Clear.</li>',
        '<li>Sweep <b>Clear</b> when you want the full set again. Chosen pills stay until Clear. Landscape Sides: header <b>K</b> / Hide turns the pane off; the Keywords collapse arrow nests under Search or restores the 3-pane side (it does not hide). Portrait Sides: that same collapse arrow is one-step hide/show.</li>',
        "guide-filter",
    ),
    (
        '<li>Header: <b>Sides</b> — Search | content | Keywords.</li>',
        '<li>Header: <b>Sides</b> — Search | content | Keywords (landscape 3-pane). Header <b>K</b> always opens Keywords as its own side, not stacked with Search.</li>',
        "guide-sides-hdr",
    ),
    (
        '<li>Use <b>S</b> / <b>K</b> to hide a menu. Both off is <b>content-only</b> — catalog pane alone, skip icons still work.</li>',
        '<li>Use <b>S</b> / <b>K</b> to show or hide a menu. Landscape Sides <b>K</b> opens Keywords solo on its side. Both off is <b>content-only</b> — catalog pane alone, skip icons still work.</li>',
        "guide-sk",
    ),
    (
        """      <details>
        <summary>Flip</summary>
        <p class="catalog-help-k">Goal</p>
        <p>Swap which side Search vs Keywords occupy, without changing filters.</p>""",
        """      <details>
        <summary>Keywords nest under Search</summary>
        <p class="catalog-help-k">Goal</p>
        <p>On landscape desktop Sides, stack Keywords under Search in one column, then restore the full 3-pane side — without hiding Keywords.</p>
        <p class="catalog-help-k">Steps</p>
        <ol>
          <li>Desktop landscape, Sides, Search on. Press header <b>K</b> — Keywords opens as its own full side column (Search | content | Keywords, or Flip equivalent).</li>
          <li>Press the Keywords panel collapse arrow (the arrow on Keywords chrome — not header K). Search sits on top, Keywords on the bottom, same column; content is the other pane.</li>
          <li>Press that same arrow again to return to 3-pane Sides. Header <b>K</b> (or Hide) turns Keywords off.</li>
          <li>Portrait desktop Sides already nests menus on a side — that collapse arrow stays one-step hide/show. Do not expect the landscape nest-toggle there. If Search is off in landscape, the nest arrow does not invent a Search column.</li>
        </ol>
        <p class="catalog-help-k">You should see</p>
        <p>Nested Flip moves Search+Keywords together. Nested Customize keeps a movable divider between Search and Keywords. Portable phone chrome is unchanged.</p>
      </details>
      <details>
        <summary>Flip</summary>
        <p class="catalog-help-k">Goal</p>
        <p>Swap which side Search vs Keywords occupy, without changing filters.</p>""",
        "guide-nest-section",
    ),
    (
        '<li>Landscape Sides: menus skip the center catalog. Landscape Middle: the top pair mirrors.</li>',
        '<li>Landscape Sides: menus skip the center catalog. If Keywords is nested under Search, Flip moves that stacked pair together. Landscape Middle: the top pair mirrors.</li>',
        "guide-flip",
    ),
    (
        '<li>Landscape: three columns (Sides) or menus-above (Middle).</li>',
        '<li>Landscape: three columns (Sides) or menus-above (Middle). Sides Keywords collapse arrow toggles nest under Search ↔ 3-pane; header K hides Keywords.</li>',
        "guide-land",
    ),
    (
        '<li>Portrait: menus stack; extra header tools go behind ⋯ if they overflow. Portable splits the title around the notch — each word centered in its half.</li>',
        '<li>Portrait: menus stack on a side (Sides) or stay above cards (Middle). The Keywords collapse arrow keeps one-step hide/show — not the landscape nest-toggle. Extra header tools go behind ⋯ if they overflow. Portable splits the title around the notch — each word centered in its half.</li>',
        "guide-port",
    ),
    (
        '<li>Drag the Search split, dual-FS separator, AC height/width, Keywords height, Index height. Pin locks a separator. Snap 50/50 when both menus are fullscreen together.</li>',
        '<li>Drag the Search split, dual-FS separator, AC height/width, Keywords height, Index height. On landscape nested Sides, the divider between Search and Keywords stays movable. Pin locks a separator. Snap 50/50 when both menus are fullscreen together.</li>',
        "guide-custom",
    ),
]


def once(text: str, old: str, new: str, label: str, name: str) -> str:
    if old not in text:
        if new in text:
            print(f"  skip {label} {name}")
            return text
        raise SystemExit(f"{name}: missing {label}: {old[:140]!r}")
    n = text.count(old)
    if n != 1:
        raise SystemExit(f"{name}: {label} count {n}")
    print(f"  1x {label} {name}")
    return text.replace(old, new, 1)


def safe_write(path: Path, text: str) -> None:
    if not text.rstrip().endswith("</html>"):
        raise SystemExit(f"{path.name}: rewrite would drop </html>")
    raw = text.encode("utf-8")
    fd, tmp = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=str(path.parent))
    try:
        os.write(fd, raw)
        os.fsync(fd)
        os.close(fd)
        fd = -1
        tmp_path = Path(tmp)
        if not tmp_path.read_text(encoding="utf-8").rstrip().endswith("</html>"):
            tmp_path.unlink(missing_ok=True)
            raise SystemExit(f"{path.name}: tmp missing </html>")
        size = tmp_path.stat().st_size
        if size < 80_000:
            tmp_path.unlink(missing_ok=True)
            raise SystemExit(f"{path.name}: tmp too small {size}")
        os.replace(tmp, path)
        assert path.stat().st_size == size
        assert path.read_text(encoding="utf-8").rstrip().endswith("</html>")
        print(f"ok {path.name} bytes={size}")
    finally:
        if fd >= 0:
            try:
                os.close(fd)
            except OSError:
                pass
        if os.path.exists(tmp):
            os.unlink(tmp)


def patch(path: Path) -> None:
    name = path.name
    text = path.read_text(encoding="utf-8")
    c00 = text.count("sessionId:'c00e3e'")
    if MARK in text and "Keywords nest under Search" in text:
        print("skip", name)
        return
    for old, new, label in REPLACEMENTS:
        text = once(text, old, new, label, name)
    if MARK not in text:
        # stamp after the nest section summary so skip works
        stamp = '<summary>Keywords nest under Search</summary>\n        <!-- ' + MARK + ' -->'
        needle = "<summary>Keywords nest under Search</summary>"
        if needle not in text:
            raise SystemExit(f"{name}: missing nest section")
        text = text.replace(needle, stamp, 1)
    if MARK not in text:
        raise SystemExit(f"{name}: missing {MARK}")
    after = text.count("sessionId:'c00e3e'")
    if after < c00:
        raise SystemExit(f"{name}: lost c00e3e logs {c00}->{after}")
    for keep in KEEP:
        if keep not in text:
            raise SystemExit(f"{name}: lost {keep}")
    if "one-step hide/show" not in text:
        raise SystemExit(f"{name}: missing portrait one-step copy")
    if "that arrow does not hide Keywords" not in text:
        raise SystemExit(f"{name}: missing landscape arrow copy")
    safe_write(path, text)


def main() -> None:
    for p in FILES:
        if not p.exists():
            raise SystemExit(f"missing {p}")
        patch(p)


if __name__ == "__main__":
    main()
