#!/usr/bin/env python3
"""
CWDOCK-FLIP-PERSIST-v1

The quick-bar toolbar's drag-end handler only saves a re-resolvable "dock"
reference (one that gets recomputed live from current geometry on every
reposition, via resolveDock()/docksFor()) for the 'seam'/'vseam' dock types.
The 4 new content-window edge docks (cwtop/cwbottom/cwleft/cwright) fell
through to the generic branch that just snapshots a frozen pixel offset -
so when the content window later moved to the opposite side of the screen
(e.g. via the portrait/landscape pane Flip), a toolbar docked to one of the
content window's own edges stayed frozen at its old absolute screen position
instead of following the content window to its new side.

Extends the re-resolvable-dock condition to include the 4 new content-window
edge dock types, so they behave like seam/vseam: saved as a live reference,
recomputed from #catalogMain's current rect every time the existing
MutationObserver-driven redock() runs (which already fires on any body class
change, including the Flip button's sides-portrait-flip toggle).
"""
import sys

FILES = [
    "public/catalogs/DS-CATALOG-portable.html",
    "public/catalogs/KONTAKT-CATALOG-portable.html",
]

OLD = "if(sd&&(sd.e==='seam'||sd.e==='vseam')){var dk={e:sd.e};if(sd.pane)dk.pane=sd.pane;if(sd.panes)dk.panes=sd.panes.slice();en.dock=dk;}"
NEW = "if(sd&&(sd.e==='seam'||sd.e==='vseam'||sd.e==='cwtop'||sd.e==='cwbottom'||sd.e==='cwleft'||sd.e==='cwright')){var dk={e:sd.e};if(sd.pane)dk.pane=sd.pane;if(sd.panes)dk.panes=sd.panes.slice();en.dock=dk;}"

def patch(path):
    src = open(path, encoding="utf-8").read()
    if "CWDOCK-FLIP-PERSIST-v1" in src:
        print(f"{path}: already patched, skipping")
        return
    if src.count(OLD) != 1:
        sys.exit(f"{path}: anchor not found/unique ({src.count(OLD)})")
    src = src.replace(OLD, "/* CWDOCK-FLIP-PERSIST-v1 */" + NEW, 1)
    open(path, "w", encoding="utf-8").write(src)
    print(f"{path}: patched")

for f in FILES:
    patch(f)
