#!/usr/bin/env python3
"""
fix-QB-FLIP-ICON-ROTATE-v1

The quick-access toolbar's Flip button (swap Search/Keywords panes) uses
a horizontal double-arrow glyph (U+21C4, looks like <->). That reads
naturally while the toolbar itself lays out horizontally, but once the
toolbar is docked to a screen edge it switches to a vertical column
(.quick-bar.qb-side{flex-direction:column}) -- with every other button
now stacked top-to-bottom, the still-horizontal Flip arrows look
sideways/mismatched against the bar's own vertical orientation.

Fix: wrap the Flip glyph in its own inline span and rotate that span 90deg
whenever the bar is in its vertical/side-docked state, so the arrows
visually match the bar's current orientation. The button's own transform
(used for its edge-hugging position offset) is untouched -- only the
glyph inside it rotates.

Applies identically to all 4 catalog files.
"""
import sys

FILES = [
    "public/catalogs/DS-CATALOG.html",
    "public/catalogs/DS-CATALOG-portable.html",
    "public/catalogs/KONTAKT-CATALOG.html",
    "public/catalogs/KONTAKT-CATALOG-portable.html",
]

OLD_CSS = (
    "#qbFlip{position:absolute;left:50%;top:-2px;transform:translate(-50%,-100%);"
    "width:2.15rem;min-width:2.15rem;height:1.25rem;min-height:1.25rem;padding:0;"
    "border-radius:8px 8px 0 0;border-bottom:0;font-size:.8rem;line-height:1;z-index:2}"
)
NEW_CSS = (
    OLD_CSS
    + "#qbFlip .qb-flip-ico{display:inline-block;transition:transform .14s ease}"
    + ".quick-bar.qb-side #qbFlip .qb-flip-ico{transform:rotate(90deg)}"
)

OLD_JS = (
    "var bF=mk('qbFlip','\\u21C4','Swap panes',function(){"
    "if(typeof togglePortraitSidesFlip==='function')togglePortraitSidesFlip();});"
)
NEW_JS = (
    "var bF=mk('qbFlip','\\u21C4','Swap panes',function(){"
    "if(typeof togglePortraitSidesFlip==='function')togglePortraitSidesFlip();});"
    "bF.innerHTML='<span class=\"qb-flip-ico\">\\u21C4</span>';"
)

REPLACEMENTS = [(OLD_CSS, NEW_CSS), (OLD_JS, NEW_JS)]


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
