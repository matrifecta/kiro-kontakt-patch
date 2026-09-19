#!/usr/bin/env python3
"""
fix-NAME-CLICK-MOBILE-EXPAND-v1 + fix-QB-COMBO-LEAK-v1

Two independent mobile bugs reported together, patched in one pass since
both touch small, well-isolated functions repeated identically across all
4 catalog files.

1) Name-click on mobile opened the fullscreen popup instead of the
   expanded (in-grid) card.
   openCardFromName() had an unconditional early return for
   useMobileFocus() (phone viewport or portable build) that always called
   openOverlay() -- the true fullscreen popup -- bypassing the expanded
   card entirely. That branch was a deliberate "fullscreen on phone"
   choice from an earlier round, but the user now wants name-click to
   open the expanded card on mobile too, matching desktop. Fix: drop the
   mobile-only branch so all platforms follow the same rule -- keep
   whatever overlay is already open (fullscreen stays fullscreen) but
   otherwise always open the expanded card via openChosenPreview().

2) Quick-access toolbar "content-only" position leaked from other layout
   combinations.
   The per-combination position system (added in ad5576a) keys positions
   by `states[sig]` (sig = orientation|S?K?F?M?), but endDrag() ALSO kept
   writing the older shared per-orientation fallback field
   (`p[orient()] = fin`) on every single drag, regardless of which
   specific combination was active. curPos() falls back to that shared
   field whenever the *current* combination has no states[] entry of its
   own yet -- so a combination that was never explicitly customised (e.g.
   content-only, both Search and Keywords hidden) would silently inherit
   whatever position was last dragged in a *different* combination
   (e.g. Search-up), instead of keeping its own remembered/default spot.
   Fix: on portable builds (which have the per-combination states table),
   stop writing the shared legacy per-orientation field on drag -- it is
   now purely a backward-compatible fallback for old, pre-existing saved
   positions, not a slot every state should be able to clobber. Desktop
   (non-portable) catalogs, which have no per-combination table, keep the
   original per-orientation-only behaviour unchanged.

Applies identically to all 4 catalog files.
"""
import sys

FILES = [
    "public/catalogs/DS-CATALOG.html",
    "public/catalogs/DS-CATALOG-portable.html",
    "public/catalogs/KONTAKT-CATALOG.html",
    "public/catalogs/KONTAKT-CATALOG-portable.html",
]

REPLACEMENTS = [
    (
        "/* fix-NAME-CLICK-v2: the name opens the expanded card (desktop) or the "
        "fullscreen popup (phone); no embed */\n"
        "function openCardFromName(el){\n"
        "  if(!el)return;\n"
        "  if(typeof useMobileFocus==='function'&&useMobileFocus()){openOverlay(el);return;}\n"
        "  if(document.body.classList.contains('hl-open')||el.classList.contains('highlight')){openOverlay(el);return;}\n"
        "  if(document.body.classList.contains('chosen-preview-open')&&el.classList.contains('selected'))return;\n"
        "  if(typeof openChosenPreview==='function')openChosenPreview(el);else openOverlay(el);\n"
        "}",
        "/* fix-NAME-CLICK-MOBILE-EXPAND-v1: the name always opens the expanded card, on "
        "desktop and mobile alike; an already-open fullscreen popup stays fullscreen */\n"
        "function openCardFromName(el){\n"
        "  if(!el)return;\n"
        "  if(document.body.classList.contains('hl-open')||el.classList.contains('highlight')){openOverlay(el);return;}\n"
        "  if(document.body.classList.contains('chosen-preview-open')&&el.classList.contains('selected'))return;\n"
        "  if(typeof openChosenPreview==='function')openChosenPreview(el);else openOverlay(el);\n"
        "}",
    ),
    (
        "var p=loadPos(),o=orient();p[o]=fin;var sd=drag.snapDock;\n"
        "if(window.CATALOG_PORTABLE){\n"
        "  p.states=p.states||{};var sig=stateSig(),en={pos:fin,dock:null};\n"
        "  if(sd&&(sd.e==='seam'||sd.e==='vseam')){var dk={e:sd.e};if(sd.pane)dk.pane=sd.pane;if(sd.panes)dk.panes=sd.panes.slice();en.dock=dk;}\n"
        "  p.states[sig]=en;\n"
        "}\n"
        "savePos(p);",
        "/* fix-QB-COMBO-LEAK-v1: on portable, the shared per-orientation slot is a\n"
        "   read-only legacy fallback -- writing it on every drag let one layout\n"
        "   combination's position leak into every other not-yet-customised\n"
        "   combination via curPos()'s fallback chain. */\n"
        "var p=loadPos(),o=orient();var sd=drag.snapDock;\n"
        "if(window.CATALOG_PORTABLE){\n"
        "  p.states=p.states||{};var sig=stateSig(),en={pos:fin,dock:null};\n"
        "  if(sd&&(sd.e==='seam'||sd.e==='vseam')){var dk={e:sd.e};if(sd.pane)dk.pane=sd.pane;if(sd.panes)dk.panes=sd.panes.slice();en.dock=dk;}\n"
        "  p.states[sig]=en;\n"
        "}else{\n"
        "  p[o]=fin;\n"
        "}\n"
        "savePos(p);",
    ),
]


def apply_to(path: str) -> None:
    html = open(path, encoding="utf-8").read()
    changed = False
    for old, new in REPLACEMENTS:
        if new in html:
            continue
        n = html.count(old)
        if n != 1:
            raise SystemExit(f"{path}: expected 1 match, found {n} for:\n{old[:120]}...")
        html = html.replace(old, new, 1)
        changed = True
    if changed:
        open(path, "w", encoding="utf-8").write(html)
        print(f"ok: {path}")
    else:
        print(f"skip (already applied): {path}")


def main() -> None:
    for rel in FILES:
        apply_to(rel)


if __name__ == "__main__":
    sys.exit(main())
