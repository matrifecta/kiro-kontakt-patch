#!/usr/bin/env python3
"""Fix Legend/User-guide symbol references that were incomplete or wrong:

- The card-search / embed fullscreen button uses a DIFFERENT glyph ("(diamond
  arrows)") from the rest of the app's fullscreen glyph ("(screen with
  corners)"); the Legend only documented the latter and implied it was used
  everywhere, so it didn't actually match what a user sees on an expanded
  card's video/search stage. Documented as its own bullet, named + symbol.
- The dual-fullscreen "expand controls" chevron, its 50/50 snap glyph and its
  lock-separator pin glyph, and the Search<->Keywords "side-by-side in
  fullscreen" companion toggle were not documented anywhere in Legend or
  Guide.
- The reload / retry glyphs on Card Search (open result, blocked-embed retry)
  were not documented.
- The comments-pane seam-tab glyph (added with the comments pane feature)
  is now named alongside its symbol, not just described in prose.

All entries are written as "name -- symbol -- what it does" so a user can
look a button up either by what it looks like or by what the guide calls it.
"""

FILES = [
    "public/catalogs/DS-CATALOG.html",
    "public/catalogs/DS-CATALOG-portable.html",
    "public/catalogs/KONTAKT-CATALOG.html",
    "public/catalogs/KONTAKT-CATALOG-portable.html",
]

FS = "\u26F6"      # existing app-wide fullscreen glyph
FS_DIAMOND = "\u2922"  # card-search / embed fullscreen glyph (different!)
CHEV_R = "\u203a"  # fs-stripe-trigger "expand controls"
SNAP = "\u229e"    # fs-snap-btn
PIN = "\U0001F4CC" # fs-pin-btn "lock separator"
MAG = "\U0001F50D" # ac-companion-btn / kw-companion-btn "side-by-side" toggle
RELOAD = "\u21bb"  # card-search-reload
RETRY = "\u21ba"   # card-yt-blocked-retry
COMMENTS_TAB = "\u2039"  # card-yt-list-toggle collapsed-list arrow

# 1. Legend lead paragraph: add the new terms this pass introduces to the word list
OLD_LEAD_WORDS = ('<p>Collapsible sections below use the same words as the chrome: Search, Keywords, Index, '
                   'Window, Embed, Sides, Middle, Flip, Collapse, Customize, Layouts, Profiles, PATH, Clear, '
                   'S, K, About / Document.</p>')
NEW_LEAD_WORDS = ('<p>Collapsible sections below use the same words as the chrome: Search, Keywords, Index, '
                   'Window, Embed, Sides, Middle, Flip, Collapse, Customize, Layouts, Profiles, PATH, Clear, '
                   'S, K, About / Document, Expand controls, Snap 50/50, Lock separator, Side-by-side.</p>')

# 2. Legend "Symbols": the ⛶ bullet should call out that card Search / embed uses a different glyph
OLD_FS_BULLET = (
    '<li><b>\u26f6</b> \u2014 Open fullscreen. On an expanded card (desktop): card overlay. On Search / Keywords '
    'strips: that menu \u2014 \u26f6 stays on the right; Keywords fullscreen has no back arrow. On Legend / Guide '
    '(desktop): the help card fills the viewport. Hidden on portable card chrome (phone goes straight to fullscreen '
    'popups). Distinct from path <b>FS</b>.</li>'
)
NEW_FS_BULLET = (
    OLD_FS_BULLET +
    '<li><b>' + FS_DIAMOND + ' Fullscreen (card search)</b> \u2014 a different glyph from the ' + FS +
    ' used elsewhere: it sits on the Card Search stage (the in-card Google / YouTube / image search opened from an '
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


def main():
    for path in FILES:
        txt = open(path, encoding="utf-8").read()
        counts = {}
        for name, old, new in [
            ("lead_words", OLD_LEAD_WORDS, NEW_LEAD_WORDS),
            ("fs_bullet", OLD_FS_BULLET, NEW_FS_BULLET),
        ]:
            counts[name] = txt.count(old)
            if counts[name] != 1:
                raise SystemExit(f"{path}: expected 1 match for {name}, got {counts[name]}")
            txt = txt.replace(old, new, 1)
        open(path, "w", encoding="utf-8").write(txt)
        print(path, counts)


if __name__ == "__main__":
    main()
