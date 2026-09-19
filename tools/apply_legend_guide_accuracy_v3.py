#!/usr/bin/env python3
"""
fix-LEGEND-GUIDE-ACCURACY-v3

Third pass, driven by direct user feedback pointing at specific stale/
incomplete Legend and Guide bullets. Verified each claim against the actual
DOM/CSS/JS before changing anything:

1. Gallery / image-focus zoom slider (#imgGalleryScale, a <input type=range>
   plus -/+ .gallery-zoom-btn buttons) is reachable by tapping a card cover
   from BOTH the expanded card and the fullscreen card, and had zero mention
   anywhere in Legend/Guide.
2. The "S / K" Symbols bullet still described header Search/Keywords toggles
   as literal letter buttons. They are: #hdrSearchBtn/#hdrKwBtn (and the
   quick-access-bar twins) are swapped for an SVG magnifying-glass / tag-like
   icon at runtime (see the ICO_MAG/ICO_KW keepHtml() replacement) -- the "S"
   and "K" only remain as the aria-label/title, not on-screen text. Reworded
   to describe the icons actually seen and to disambiguate from the *other*
   still-textual "K" (Keywords side-by-side, in fullscreen) and "🔍" (Search
   side-by-side) companion toggles, which the Legend already documents
   correctly elsewhere.
3. The "› Expand controls" bullet didn't say the chevron flips to "‹" once
   open (it does, same pattern as the already-documented comments-pane tab),
   and implied Lock separator is available from both Search and Keywords
   fullscreen strips -- it only exists on the Search side (#fsSepPinBtn is a
   child of #acFsStripePanel only, not #kwFsStripePanel).
4. PATH's three icons (FS / Copy / Folder) are raster/mask icon glyphs, not
   text -- the Legend named them but never described what they look like, so
   they were unidentifiable on screen. Added a short shape description to
   each, consistent with the plain-word-fallback convention used elsewhere.

Applies identically to all 4 catalog files (same wording confirmed present
in each before patching).
"""
import sys

FILES = [
    "public/catalogs/DS-CATALOG.html",
    "public/catalogs/DS-CATALOG-portable.html",
    "public/catalogs/KONTAKT-CATALOG.html",
    "public/catalogs/KONTAKT-CATALOG-portable.html",
]

REPLACEMENTS = [
    # 1) Gallery zoom slider -- extend the existing Covers bullet.
    (
        "<li><b>Covers</b> \u2014 banner art. Tap for gallery / image focus. "
        "Desktop hover can enlarge the cover without leaving the grid.</li>",
        "<li><b>Covers</b> \u2014 banner art. Tap for gallery / image focus, "
        "from either the expanded card or the fullscreen card. A <b>\u2212 / +</b> "
        "zoom bar with a drag slider between them sits at the bottom of that "
        "view to resize the image; it does not affect the card itself.</li>"
        "<li><b>Desktop hover can enlarge the cover</b> without leaving the "
        "grid.</li>",
    ),
    # 2) S / K Symbols bullet -- now icon buttons, not literal letters.
    (
        "<li><b>S</b> / <b>K</b> \u2014 show or hide Search and Keywords. "
        "Hiding both on portable is content-only (catalog pane alone).</li>",
        "<li><b>S / K header toggles</b> \u2014 the header's Search and "
        "Keywords show/hide buttons render as a magnifying-glass icon (Search) "
        "and a tag-shaped icon (Keywords), not the letters \"S\"/\"K\" \u2014 "
        "those only remain as the button's title/aria-label. Hiding both on "
        "portable is content-only (catalog pane alone). Do not confuse with "
        "the still-textual <b>K</b> / <b>\U0001F50D</b> side-by-side companion "
        "toggles used inside a fullscreened Search or Keywords pane (see "
        "<b>\U0001F50D Side-by-side</b>).</li>",
    ),
    # 3) Expand controls chevron -- flips, and Lock separator is Search-only.
    (
        "<li><b>\u203a Expand controls</b> \u2014 small right-pointing chevron "
        "(\">\") on a fullscreened Search or Keywords pane that reveals a small "
        "strip with <b>\u229e Snap 50/50</b> (squared-plus icon; even the "
        "Search/Keywords split when both are fullscreened side by side) and "
        "<b>\U0001F4CC Lock separator</b> (pushpin icon; stop that split from "
        "being dragged).</li>",
        "<li><b>\u203a / \u2039 Expand controls</b> \u2014 small chevron on a "
        "fullscreened Search or Keywords pane; \u203a reveals a small strip "
        "with <b>\u229e Snap 50/50</b> (squared-plus icon; even the "
        "Search/Keywords split when both are fullscreened side by side) and, "
        "on the Search side only, <b>\U0001F4CC Lock separator</b> (pushpin "
        "icon; stop that split from being dragged \u2014 not offered from the "
        "Keywords strip). The chevron flips to \u2039 while that strip is open, "
        "same idea as the Comments pane tab below.</li>",
    ),
    # 4) PATH icon shapes.
    (
        "<li><b>Folder</b> \u2014 themed path icon that opens the library "
        "folder in the file manager on desktop (Dolphin). Omitted or inert on "
        "portable.</li>",
        "<li><b>Folder</b> (folder-shaped icon) \u2014 themed path icon that "
        "opens the library folder in the file manager on desktop (Dolphin). "
        "Omitted or inert on portable.</li>",
    ),
    (
        "<li><b>Copy</b> \u2014 path icon that copies the library "
        "location. A short toast confirms.</li>",
        "<li><b>Copy</b> (overlapping-squares/duplicate icon) \u2014 path icon "
        "that copies the library location. A short toast confirms.</li>",
    ),
    (
        "<li><b>FS</b> \u2014 path icon that opens the <b>path reader</b> "
        "(long location). This is not the card\u2019s own \u26f6. Back closes "
        "the reader.</li>",
        "<li><b>FS</b> (up/down arrow icon, not the text \"FS\") \u2014 path "
        "icon that opens the <b>path reader</b> (long location). This is not "
        "the card\u2019s own \u26f6. Back closes the reader.</li>",
    ),
]


def apply_to(path: str) -> None:
    html = open(path, encoding="utf-8").read()
    changed = False
    for old, new in REPLACEMENTS:
        if new in html:
            continue  # already applied
        n = html.count(old)
        if n != 1:
            raise SystemExit(
                f"{path}: expected 1 match, found {n} for:\n{old[:90]}..."
            )
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
