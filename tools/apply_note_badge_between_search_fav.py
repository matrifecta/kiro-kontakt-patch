#!/usr/bin/env python3
"""
Move the non-interactive "has a note" badge off the cover artwork:
position it in the bottom action row, centered in the gap between the
Search button and the Favorite button, instead of the top-left corner.
Widen card-actions' reserved right-hand gutter so the Search button
doesn't run underneath it.
"""

FILES = [
    "public/catalogs/DS-CATALOG.html",
    "public/catalogs/DS-CATALOG-portable.html",
    "public/catalogs/KONTAKT-CATALOG.html",
    "public/catalogs/KONTAKT-CATALOG-portable.html",
]

OLD_BADGE_CSS = (
    ' .note-badge-tl{display:none;position:absolute;top:.5rem;left:.5rem;z-index:3;'
    'width:1.75rem;height:1.75rem;min-width:1.75rem;padding:0;align-items:center;'
    'justify-content:center;font-size:1rem;font-weight:400;line-height:1;'
    'background:var(--accent-instrument-bg);color:var(--accent-instrument);'
    'border:1px solid var(--accent-instrument);border-radius:6px;pointer-events:none}'
)

NEW_BADGE_CSS = (
    ' .note-badge-tl{display:none;position:absolute;'
    'right:calc(.5rem + var(--card-chrome-btn) + .4rem);'
    'bottom:calc(.5rem + (var(--card-chrome-btn) - 1.5rem)/2);'
    'top:auto;left:auto;z-index:3;'
    'width:1.5rem;height:1.5rem;min-width:1.5rem;padding:0;align-items:center;'
    'justify-content:center;font-size:.875rem;font-weight:400;line-height:1;'
    'background:var(--accent-instrument-bg);color:var(--accent-instrument);'
    'border:1px solid var(--accent-instrument);border-radius:6px;pointer-events:none}'
)

OLD_PADDING = " .entry:not(.highlight) .card-actions{padding-right:3.25rem}"
NEW_PADDING = " .entry:not(.highlight) .card-actions{padding-right:calc(.5rem + var(--card-chrome-btn) + .4rem + 1.5rem + .4rem)}"


def main():
    for path in FILES:
        txt = open(path, encoding="utf-8").read()
        badge_ok = OLD_BADGE_CSS in txt
        if badge_ok:
            txt = txt.replace(OLD_BADGE_CSS, NEW_BADGE_CSS, 1)
        pad_ok = OLD_PADDING in txt
        if pad_ok:
            txt = txt.replace(OLD_PADDING, NEW_PADDING, 1)
        open(path, "w", encoding="utf-8").write(txt)
        print(f"{path}: badge_repositioned={badge_ok} padding_widened={pad_ok}")


if __name__ == "__main__":
    main()
