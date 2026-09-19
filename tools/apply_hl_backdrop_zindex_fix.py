#!/usr/bin/env python3
"""
fix-HL-BACKDROP-Z-INDEX-v1

Real bug found while investigating a user report that clicking a card's
cover artwork stopped opening the gallery/zoom popup from the FULLSCREEN
card view (it still works from the expanded, non-fullscreen card), and that
the fullscreen card looked visibly darker/"less bright" than the expanded
card.

Root cause: #hlBackdrop (.hl-backdrop, the click-outside-to-close dimmer
behind a highlighted card) is `position:fixed;inset:0;z-index:900`. The
fullscreen card itself (.entry.highlight) is `position:fixed;inset:0;
z-index:860` -- LOWER than the backdrop. Since the backdrop gets `.open`
added for the exact same state (hl-open) as the fullscreen card, and both
cover the full viewport, the backdrop's semi-transparent rgba(0,0,0,.35)
layer was sitting entirely ON TOP of the fullscreen card: it visibly
darkened everything by 35% black (the "not as bright" symptom) and
intercepted every click anywhere in the card (elementFromPoint on the cover
returns #hlBackdrop, not the cover -- the "artwork isn't clickable" symptom).
Confirmed both with a real mouse-coordinate click (not a synthetic
.click()), which reproduces exactly what a user's pointer would hit.

The backdrop's click-outside-to-close purpose is moot once hl-open makes
the card fill 100% of the viewport (there is no "outside" left to click),
so the safe fix is to keep it under the card's stacking order whenever
hl-open is active, rather than removing/hiding it outright (which could
affect other card states that reuse the same backdrop element without
hl-open, e.g. a future non-fullscreen highlight).

Applies identically to all 4 catalog files.
"""
import sys

FILES = [
    "public/catalogs/DS-CATALOG.html",
    "public/catalogs/DS-CATALOG-portable.html",
    "public/catalogs/KONTAKT-CATALOG.html",
    "public/catalogs/KONTAKT-CATALOG-portable.html",
]

OLD = ".hl-backdrop{display:none;position:fixed;inset:0;z-index:900;background:var(--hl-backdrop)}"
NEW = (
    OLD
    + "\n/* fix-HL-BACKDROP-Z-INDEX-v1: keep the backdrop under the fullscreen"
    + " card (z-index:860), not above it -- it was blocking every click and"
    + " darkening the card with its own dim layer once hl-open makes the card"
    + " fill the full viewport */\n"
    + "body.hl-open .hl-backdrop{z-index:850}"
)


def apply_to(path: str) -> None:
    html = open(path, encoding="utf-8").read()
    if NEW in html:
        print(f"skip (already applied): {path}")
        return
    n = html.count(OLD)
    if n != 1:
        raise SystemExit(f"{path}: expected 1 match, found {n}")
    html = html.replace(OLD, NEW, 1)
    open(path, "w", encoding="utf-8").write(html)
    print(f"ok: {path}")


def main() -> None:
    for rel in FILES:
        apply_to(rel)


if __name__ == "__main__":
    sys.exit(main())
