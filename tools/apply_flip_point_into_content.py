#!/usr/bin/env python3
"""Make the floating quick-bar's Flip button always point toward the
content window's interior instead of the screen's vertical center.

Root cause: applyPos()/the drag pointermove handler decided whether the
Flip button (#qbFlip) sits above or below the bar (.qb-flip-low) purely
from the bar's vertical offset from the *screen's* center (c.dy<0). That
assumption only holds when the content window (#catalogMain) spans the
full screen height symmetrically about that center. In layouts where the
content window is offset (e.g. Middle mode with a menu above it, or a
docked content-window-edge point below the screen's vertical midpoint),
the bar could end up on the far side of the content window's own
midpoint from what c.dy<0 assumed, so the Flip button pointed away from
(out of) the content window/screen instead of into it.

Fix: compute the low/high split from the content window's own live
vertical center when it is measurable, falling back to the previous
screen-center heuristic only when it isn't (e.g. content window fully
hidden). Applied at both call sites that set qb-flip-low (idle
position apply + live drag). Idempotent.
"""
import os

FILES = [
    "public/catalogs/DS-CATALOG-portable.html",
    "public/catalogs/KONTAKT-CATALOG-portable.html",
]

HELPER_MARK = "function flipLowFor("
HELPER = """function flipLowFor(by){
  var cwEl=document.getElementById('catalogMain');
  if(cwEl&&cwEl.offsetParent!==null){
    var cw=cwEl.getBoundingClientRect();
    if(cw.height>10)return by<(cw.top+cw.bottom)/2;
  }
  return by<(window.innerHeight||600)/2;
}
"""

APPLYPOS_OLD = "function applyPos(){var c=curPos();setSide(c.v||0);bar.style.setProperty('--qb-dx',Math.round(c.dx)+'px');bar.style.setProperty('--qb-dy',Math.round(c.dy)+'px');bar.classList.toggle('qb-flip-low',c.dy<0);bF.style.display=flipOk()?'':'none';updCollapse();updLayout();}"
APPLYPOS_NEW = "function applyPos(){var c=curPos();setSide(c.v||0);bar.style.setProperty('--qb-dx',Math.round(c.dx)+'px');bar.style.setProperty('--qb-dy',Math.round(c.dy)+'px');bar.classList.toggle('qb-flip-low',flipLowFor((window.innerHeight||600)/2+c.dy));bF.style.display=flipOk()?'':'none';updCollapse();updLayout();}"

DRAG_OLD = "  bar.classList.toggle('qb-flip-low',c.dy<0);\n  updCollapse();\n  var ds=docksFor();drag.docks=ds;"
DRAG_NEW = "  bar.classList.toggle('qb-flip-low',flipLowFor(e.clientY));\n  updCollapse();\n  var ds=docksFor();drag.docks=ds;"


def apply_file(path):
    with open(path, "r", encoding="utf-8") as f:
        html = f.read()
    changed = False

    if HELPER_MARK not in html:
        anchor = "function curPos(){"
        idx = html.index(anchor)
        html = html[:idx] + HELPER + html[idx:]
        changed = True
    else:
        print(f"  (helper already applied) {path}")

    if APPLYPOS_OLD in html:
        html = html.replace(APPLYPOS_OLD, APPLYPOS_NEW, 1)
        changed = True
    elif "flipLowFor((window.innerHeight" not in html:
        print(f"  WARNING: applyPos anchor not found in {path}")

    if DRAG_OLD in html:
        html = html.replace(DRAG_OLD, DRAG_NEW, 1)
        changed = True
    elif "flipLowFor(e.clientY)" not in html:
        print(f"  WARNING: drag anchor not found in {path}")

    if changed:
        with open(path, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"  patched {path}")
    else:
        print(f"  no changes needed {path}")


if __name__ == "__main__":
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    for rel in FILES:
        apply_file(os.path.join(root, rel))
