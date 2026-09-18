#!/usr/bin/env python3
"""
Mobile quick-bar: remember a separate position for EVERY layout combination.

A combination ("state signature") is:
    orientation | Search visible | Keywords visible | panes flipped | Middle layout
e.g. "portrait|S1K0F0M0"  (portrait, Search menu up, Keywords hidden, not flipped)

p.states[sig] = { dock: {e:'seam',pane} | {e:'vseam',panes} | null,
                  pos:  {dx,dy,v} }

- Dropping the bar saves ONLY the current combination's entry: a seam dock
  if it landed on a between-panes seam, otherwise a free position. Every
  other combination keeps whatever it already had.
- When a combination becomes active again, its saved entry is restored
  automatically: a dock is re-resolved against the live pane rects (so it
  follows the separator), a free position is applied as-is.
- Combinations that were never customised fall back to the older
  per-orientation dock / free position, then to the default spot.
"""
FILES = [
    "public/catalogs/DS-CATALOG.html",
    "public/catalogs/DS-CATALOG-portable.html",
    "public/catalogs/KONTAKT-CATALOG.html",
    "public/catalogs/KONTAKT-CATALOG-portable.html",
]

REPL = [
    # helpers: state signature + lookup
    ("function dockFor(st,o){return (st&&st.docks&&st.docks[o||orient()])||null;}",
     "function dockFor(st,o){return (st&&st.docks&&st.docks[o||orient()])||null;}\n"
     "/* fix-QB-COMBO-STATES-v1: one remembered position per layout combination */\n"
     "function paneVis(id){var el=document.getElementById(id);if(!el||el.offsetParent===null)return false;var r=el.getBoundingClientRect();return r.width>4&&r.height>4;}\n"
     "function stateSig(){var c=document.body.classList;return orient()+'|S'+(paneVis('searchChrome')?1:0)+'K'+(paneVis('filterWrap')?1:0)+'F'+(c.contains('portable-flip-on')||c.contains('sides-portrait-flip')?1:0)+'M'+(c.contains('display-middle')?1:0);}\n"
     "function stateFor(st,sig){return (st&&st.states&&st.states[sig||stateSig()])||null;}"),
    # curPos: combination entry first (dock, then pos), then legacy fallbacks
    ("function curPos(){var st=loadPos();var d=resolveDock(dockFor(st));if(d)return d;var c=convPos(st[orient()]);return c?clampPos(c.dx,c.dy,c.v):defPos();}",
     "function curPos(){\n"
     "  var st=loadPos();\n"
     "  var en=window.CATALOG_PORTABLE?stateFor(st):null;\n"
     "  if(en){\n"
     "    if(en.dock){var dd=resolveDock(en.dock);if(dd)return dd;}\n"
     "    if(en.pos){var cp=convPos(en.pos);if(cp)return clampPos(cp.dx,cp.dy,cp.v);}\n"
     "  }\n"
     "  var d=resolveDock(dockFor(st));if(d)return d;\n"
     "  var c=convPos(st[orient()]);return c?clampPos(c.dx,c.dy,c.v):defPos();\n"
     "}"),
    # endDrag: write only the current combination's entry
    ("var p=loadPos(),o=orient();p.docks=p.docks||{};var sd=drag.snapDock;if(sd&&(sd.e==='seam'||sd.e==='vseam')&&window.CATALOG_PORTABLE){var dk={e:sd.e};if(sd.pane)dk.pane=sd.pane;if(sd.panes)dk.panes=sd.panes.slice();p.docks[o]=dk;}else{p[o]=fin;if(window.CATALOG_PORTABLE&&seamAvailable())delete p.docks[o];}savePos(p);",
     "var p=loadPos(),o=orient();p[o]=fin;var sd=drag.snapDock;\n"
     "if(window.CATALOG_PORTABLE){\n"
     "  p.states=p.states||{};var sig=stateSig(),en={pos:fin,dock:null};\n"
     "  if(sd&&(sd.e==='seam'||sd.e==='vseam')){var dk={e:sd.e};if(sd.pane)dk.pane=sd.pane;if(sd.panes)dk.panes=sd.panes.slice();en.dock=dk;}\n"
     "  p.states[sig]=en;\n"
     "}\n"
     "savePos(p);"),
    # redock: re-apply on every layout change (the new combination may have its own entry)
    ("    if(!dockFor(loadPos()))return;",
     "    if(!window.CATALOG_PORTABLE)return;"),
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
