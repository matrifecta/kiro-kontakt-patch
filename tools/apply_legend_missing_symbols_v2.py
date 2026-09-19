#!/usr/bin/env python3
"""
fix-LEGEND-MISSING-SYMBOLS-v2

Second-pass audit found 4 real UI controls with zero Legend/Guide coverage:
  - the "-" Minimize button on an expanded/selected card (class .hl-min)
  - the "x" close button on a pinned-card pill (class .card-min-close)
  - the desktop header's aux-controls collapse chevron "< / >" (#hdrAuxToggle)
  - the Index height drag handle (button#indexHeight, no visible glyph)

Adds one Legend "Symbols" bullet for each, and folds the Minimize/close pair
into the existing "Pinned pyramid" bullet under Content window so the two
docs cross-reference each other.

Applies to all 4 catalog files. All four ship the same `if(DESKTOP)`-gated
code for the minimize button, pinned-dock close button, and header aux
toggle (DESKTOP is a runtime viewport check, not a build flag -- a portable
export opened on a wide screen still gets these controls), and each file
carries its own copy of the Legend/Guide help content, so each needs the
same doc update.
"""
import sys

FILES = [
    "public/catalogs/DS-CATALOG.html",
    "public/catalogs/DS-CATALOG-portable.html",
    "public/catalogs/KONTAKT-CATALOG.html",
    "public/catalogs/KONTAKT-CATALOG-portable.html",
]

OLD_SYMBOLS_TAIL = (
    "<li><b>\u2190 Back</b> \u2014 one step back from expanded card, card fullscreen, "
    "gallery, description/path reader, Search fullscreen, embed, or this Legend/Guide. "
    "Keywords fullscreen uses \u26f6 + Hide instead of a back arrow.</li>"
)

NEW_SYMBOLS_ADDITIONS = (
    "<li><b>\u2212 Minimize</b> \u2014 minus-sign icon on an expanded/selected card's "
    "top-right chrome; docks that card as a small pill in the <b>Pinned pyramid</b> "
    "at the bottom of the content window instead of closing it.</li>"
    "<li><b>\u00d7 Close pinned card</b> \u2014 small x on a pinned-dock pill; removes just "
    "that pill (does not affect Favorite or any saved note).</li>"
    "<li><b>\u25c2 / \u25b8 aux collapse</b> \u2014 desktop-only chevron in the header that "
    "hides or shows the Clear on miss, Layouts, and Profiles controls as a group, to "
    "free up header width; flips direction to show which state you're in.</li>"
    "<li><b>Index height handle</b> \u2014 thin drag bar under an open Index window "
    "(no glyph); drag its bottom edge to resize how much of the content pane the "
    "Index list takes up. Only draggable while <b>Customize</b> is on and layout is "
    "not pinned.</li>"
)

OLD_PINNED_PYRAMID = (
    "<li><b>Pinned pyramid</b> \u2014 minimized cards dock at the bottom of the content "
    "window (Save on Middle). A cover-sized frame holds the still cover and, while "
    "playing, the video in the same spot, so the pill keeps its width and the name / "
    "close button never shift. Reopening a pinned card always shows it, even if a "
    "filter or search would otherwise have hidden it.</li>"
)

NEW_PINNED_PYRAMID = (
    "<li><b>Pinned pyramid</b> \u2014 tap <b>\u2212 Minimize</b> on an expanded/selected "
    "card to dock it at the bottom of the content window (Save on Middle) instead of "
    "closing it. A cover-sized frame holds the still cover and, while playing, the "
    "video in the same spot, so the pill keeps its width and the name / <b>\u00d7 close</b> "
    "button never shift. Reopening a pinned card always shows it, even if a filter or "
    "search would otherwise have hidden it.</li>"
)


def apply_to(path: str) -> None:
    html = open(path, encoding="utf-8").read()

    if NEW_SYMBOLS_ADDITIONS.split("<li>")[1][:20] in html:
        print(f"skip (already applied): {path}")
        return

    n = html.count(OLD_SYMBOLS_TAIL)
    if n != 1:
        raise SystemExit(f"{path}: expected 1 match for symbols-tail anchor, found {n}")
    html = html.replace(OLD_SYMBOLS_TAIL, OLD_SYMBOLS_TAIL + NEW_SYMBOLS_ADDITIONS, 1)

    n2 = html.count(OLD_PINNED_PYRAMID)
    if n2 != 1:
        raise SystemExit(f"{path}: expected 1 match for pinned-pyramid bullet, found {n2}")
    html = html.replace(OLD_PINNED_PYRAMID, NEW_PINNED_PYRAMID, 1)

    open(path, "w", encoding="utf-8").write(html)
    print(f"ok: {path}")


def main() -> None:
    for rel in FILES:
        apply_to(rel)


if __name__ == "__main__":
    sys.exit(main())
