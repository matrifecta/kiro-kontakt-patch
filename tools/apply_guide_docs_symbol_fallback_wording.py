#!/usr/bin/env python3
"""The 'Symbols' Legend entries added this week rely on a few uncommon Unicode
glyphs (diamond-arrows fullscreen, snap, pin, chevron). On at least one
browser/font combo those render as tofu/garbled fallback glyphs (confirmed by
screenshot: the diamond-arrows fullscreen glyph rendered as an unrelated
musical-note-looking symbol). That's a font-coverage gap, not a wrong
character -- the doc used the exact same codepoint as the real button. But it
defeats the "look it up by symbol" goal when the symbol doesn't render.

Fix: give each of those entries a plain-word shape description alongside the
glyph, so the entry stays identifiable by name/shape even where the glyph
itself fails to render legibly.
"""

FILES = [
    "public/catalogs/DS-CATALOG.html",
    "public/catalogs/DS-CATALOG-portable.html",
    "public/catalogs/KONTAKT-CATALOG.html",
    "public/catalogs/KONTAKT-CATALOG-portable.html",
]

FS_DIAMOND = "\u2922"
CHEV_R = "\u203a"
SNAP = "\u229e"
PIN = "\U0001F4CC"
MAG = "\U0001F50D"
RELOAD = "\u21bb"
RETRY = "\u21ba"
COMMENTS_TAB = "\u2039"

OLD = (
    '<li><b>' + FS_DIAMOND + ' Fullscreen (card search)</b> \u2014 a different glyph from the \u26f6 '
    'used elsewhere: it sits on the Card Search stage (the in-card Google / YouTube / image search opened from an '
    'expanded card) and expands that stage, video + comments pane included, to fill the screen. <b>' + RELOAD +
    ' Reload</b> next to it reloads the current result; a blocked YouTube embed instead shows a <b>' + RETRY +
    ' Try again</b> button.</li>'
    '<li><b>' + CHEV_R + ' Expand controls</b> \u2014 chevron on a fullscreened Search or Keywords pane that reveals '
    'a small strip with <b>' + SNAP + ' Snap 50/50</b> (even the Search/Keywords split when both are fullscreened '
    'side by side) and <b>' + PIN + ' Lock separator</b> (stop that split from being dragged).</li>'
    '<li><b>' + MAG + ' Side-by-side</b> \u2014 while Search is fullscreened, this toggle (labelled <b>K</b>) brings '
    'Keywords in beside it; while Keywords is fullscreened, the matching toggle (this ' + MAG +
    ' magnifier) brings Search in beside it. Off returns to one pane alone.</li>'
    '<li><b>' + COMMENTS_TAB + ' Comments pane tab</b> \u2014 the thin seam tab on a YouTube card-search result that '
    'hides or shows the comments pane (see <b>Card Search</b> below); it flips to the mirrored arrow when the pane '
    'is hidden.</li>'
)

NEW = (
    '<li><b>' + FS_DIAMOND + ' Fullscreen (card search)</b> \u2014 small diamond-shaped double arrow, one pointing '
    'up-right and one down-left (renders as tofu on some fonts \u2014 look for it on the Card Search stage if the '
    'glyph itself does not show). A different icon from the \u26f6 square-corners fullscreen used elsewhere: it '
    'sits on the Card Search stage (the in-card Google / YouTube / image search opened from an expanded card) and '
    'expands that stage, video + comments pane included, to fill the screen. <b>' + RELOAD +
    ' Reload</b> (circular arrow) next to it reloads the current result; a blocked YouTube embed instead shows a '
    '<b>' + RETRY + ' Try again</b> button (counter-clockwise circular arrow + text).</li>'
    '<li><b>' + CHEV_R + ' Expand controls</b> \u2014 small right-pointing chevron (">") on a fullscreened Search '
    'or Keywords pane that reveals a small strip with <b>' + SNAP + ' Snap 50/50</b> (squared-plus icon; even the '
    'Search/Keywords split when both are fullscreened side by side) and <b>' + PIN +
    ' Lock separator</b> (pushpin icon; stop that split from being dragged).</li>'
    '<li><b>' + MAG + ' Side-by-side</b> \u2014 magnifying-glass icon: while Search is fullscreened, a text '
    '<b>K</b> toggle brings Keywords in beside it; while Keywords is fullscreened, this ' + MAG +
    ' magnifier toggle brings Search in beside it. Off returns to one pane alone.</li>'
    '<li><b>' + COMMENTS_TAB + ' Comments pane tab</b> \u2014 a small left-pointing arrow on a thin seam bar '
    'attached to a YouTube card-search result, which hides or shows the comments pane (see <b>Card Search</b> '
    'below); it flips to the mirrored right-pointing arrow when the pane is hidden.</li>'
)


def main():
    for path in FILES:
        txt = open(path, encoding="utf-8").read()
        n = txt.count(OLD)
        if n != 1:
            raise SystemExit(f"{path}: expected 1 match, got {n}")
        txt = txt.replace(OLD, NEW, 1)
        open(path, "w", encoding="utf-8").write(txt)
        print(path, "ok")


if __name__ == "__main__":
    main()
