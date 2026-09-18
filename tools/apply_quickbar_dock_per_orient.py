#!/usr/bin/env python3
"""
Mobile quick-bar docking, per orientation.

Storage model (localStorage catalog-quickbar-pos-<NS>):
  p.portrait / p.landscape : the "free" position for that orientation
                             (used whenever no between-panes seam exists,
                             i.e. content-only view) -- as before
  p.docks.portrait / .landscape : the seam dock for that orientation
                             ({e:'seam',pane} or {e:'vseam',panes})

Rules:
- Dropping on a between-panes dock (menu|menu or menu|content) saves the
  dock for the CURRENT orientation only. Coming back to that orientation
  restores it.
- If that seam is not present right now (only the content window is
  open), the bar uses the orientation's free position instead. Moving the
  bar in that state just updates the free position; the dock is kept and
  is restored as soon as the menus are back.
- Dropping the bar away from any seam WHILE a seam is available is an
  explicit undock: the orientation's dock is cleared and the free
  position updated. Edge docks (top/bottom/left/right) count as free
  positions since they do not depend on the panes.
- Old single global `dock` key is migrated into both orientations.
"""
FILES = [
    "public/catalogs/DS-CATALOG.html",
    "public/catalogs/DS-CATALOG-portable.html",
    "public/catalogs/KONTAKT-CATALOG.html",
    "public/catalogs/KONTAKT-CATALOG-portable.html",
]

REPL = [
    # loadPos: migrate legacy global dock into per-orientation docks
    ("function loadPos(){try{var o=JSON.parse(localStorage.getItem(POSKEY)||'null');if(o&&typeof o==='object')return o;}catch(e){}return {};}",
     "function loadPos(){try{var o=JSON.parse(localStorage.getItem(POSKEY)||'null');if(o&&typeof o==='object'){"
     "if(o.dock&&!o.docks){o.docks={portrait:o.dock,landscape:o.dock};}delete o.dock;return o;}}catch(e){}return {};}\n"
     "function dockFor(st,o){return (st&&st.docks&&st.docks[o||orient()])||null;}\n"
     "function seamAvailable(){var ds=docksFor();for(var i=0;i<ds.length;i++)if(ds[i].e==='seam'||ds[i].e==='vseam')return true;return false;}"),
    # resolveDock: when the seam is absent, fall through to the orientation's free position
    ("  if(!hit&&(dk.e==='seam'||dk.e==='vseam')){\n"
     "    /* no seam to dock to right now (menus hidden) -> bottom centre, keep the dock saved */\n"
     "    var r=bar.getBoundingClientRect(),bh=r.height||44;\n"
     "    hit={x:vw/2,y:vh-bh/2-8,e:'bottom'};\n"
     "  }\n"
     "  if(!hit)return null;",
     "  /* seam not present right now (content-only view): fall through to this orientation's\n"
     "     free position; the dock stays saved and is restored when the menus come back */\n"
     "  if(!hit)return null;"),
    # curPos: per-orientation dock first, then per-orientation free position
    ("function curPos(){var st=loadPos();var d=resolveDock(st.dock);if(d)return d;var c=convPos(st[orient()]);return c?clampPos(c.dx,c.dy,c.v):defPos();}",
     "function curPos(){var st=loadPos();var d=resolveDock(dockFor(st));if(d)return d;var c=convPos(st[orient()]);return c?clampPos(c.dx,c.dy,c.v):defPos();}"),
    # endDrag: save dock per orientation; free drop = free position (+ undock if a seam was available)
    ("var p=loadPos();p[orient()]=fin;if(drag.snapDock&&window.CATALOG_PORTABLE){var sd=drag.snapDock;p.dock={e:sd.e};if(sd.pane)p.dock.pane=sd.pane;if(sd.panes)p.dock.panes=sd.panes.slice();}else delete p.dock;savePos(p);",
     "var p=loadPos(),o=orient();p.docks=p.docks||{};var sd=drag.snapDock;"
     "if(sd&&(sd.e==='seam'||sd.e==='vseam')&&window.CATALOG_PORTABLE){"
     "var dk={e:sd.e};if(sd.pane)dk.pane=sd.pane;if(sd.panes)dk.panes=sd.panes.slice();p.docks[o]=dk;"
     "}else{"
     "p[o]=fin;"
     "if(window.CATALOG_PORTABLE&&seamAvailable())delete p.docks[o];"
     "}"
     "savePos(p);"),
    # redock guard: only when this orientation has a dock
    ("    if(!loadPos().dock)return;",
     "    if(!dockFor(loadPos()))return;"),
]


def main():
    for path in FILES:
        txt = open(path, encoding="utf-8").read()
        for old, new in REPL:
            n = txt.count(old)
            if n != 1:
                raise SystemExit(f"{path}: expected 1 match, got {n} for: {old[:70]}")
            txt = txt.replace(old, new, 1)
        open(path, "w", encoding="utf-8").write(txt)
        print(f"{path}: {len(REPL)} replacements applied")


if __name__ == "__main__":
    main()
