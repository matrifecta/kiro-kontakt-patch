#!/usr/bin/env python3
"""Document this round's changes in the Legend and User guide:
quick toolbar docking (per layout combination), the Legend/Guide and
Top/Bottom hide tabs, the Customize drag edge on the Search pane, and
English keyword aliases for non-English library names."""

FILES = [
    "public/catalogs/DS-CATALOG.html",
    "public/catalogs/DS-CATALOG-portable.html",
    "public/catalogs/KONTAKT-CATALOG.html",
    "public/catalogs/KONTAKT-CATALOG-portable.html",
]

# 1. Legend: Legend / Guide keys -> mention their hide/show tabs and phone placement
OLD_LG = ('<li><b>Legend / Guide</b> — left-edge keys on the content border, docked like the skip icons. '
          'Selected sticks out further. They hide when the content window is not on screen and must not overlay '
          'About / Document. They also hide under card overlays unless help itself is open.</li>')
NEW_LG = (OLD_LG +
          '<li><b>\u25BC / \u25B2 tabs</b> \u2014 two small tabs on the content window\u2019s bottom border hide or show '
          'the Legend / Guide pair (left) and the skip-to-top / skip-to-bottom pair (right). They stay fully inside the '
          'content window. On phone they sit a quarter of the way in from each side (not on the edges) in both '
          'orientations, so they never crowd the edge controls.</li>')

# 2. Legend: Header bar -> mention quick toolbar + docking
OLD_HDR = '<li><b>Header bar</b> — hide/show document header.</li>'
NEW_HDR = (
    '<li><b>Header bar</b> \u2014 hide/show document header. While it is hidden (or Customize is on) a small floating '
    '<b>quick toolbar</b> appears with S (Search), K (Keywords), \u21C4 Flip, layout and a collapse arrow.</li>'
    '<li><b>Quick toolbar docking (phone)</b> \u2014 long-press the toolbar (about 3 s) to drag it; dock markers appear on '
    'the screen edges and on every seam between two panes (menu | menu, or menu | content window). Drop it on a seam and '
    'it stays glued there, following the separator when you resize. Each layout combination \u2014 orientation, which of '
    'Search / Keywords is up, Flip \u2014 remembers its own position separately, so once you have placed the toolbar for a '
    'combination it comes back there automatically whenever that combination returns. Dropping it away from a seam '
    'remembers that free spot for the current combination instead.</li>'
)

# 3. Legend: Customize -> the Search pane now has the same drag edge as Keywords
OLD_CUST = '<li><b>Customize</b> — reveal drag edges for Search, Keywords, Index, and menu height. Becomes <b>Done</b> while arranging.</li>'
NEW_CUST = ('<li><b>Customize</b> \u2014 reveal drag edges for Search, Keywords, Index, and menu height. In Middle layout both the '
            'Search pane and the Keywords pane show a centred drag line on their bottom edge, so either one can set the menu '
            'height. Becomes <b>Done</b> while arranging.</li>')

# 4. Legend: Saved -> include quick toolbar positions
OLD_SAVED = ('<li><b>Saved (localStorage, per catalog ns)</b> — theme, Sides/Middle pick, Flip, Customize sizes, Layouts, '
             'Profiles (max 12), Favorites, notes, UI scale, Index/About Embed prefs, some Search-split ratios, Clear on miss.</li>')
NEW_SAVED = ('<li><b>Saved (localStorage, per catalog ns)</b> \u2014 theme, Sides/Middle pick, Flip, Customize sizes, Layouts, '
             'Profiles (max 12), Favorites, notes, UI scale, Index/About Embed prefs, some Search-split ratios, Clear on miss, '
             'quick toolbar position and docks (one per layout combination).</li>')

# 5. Legend: Keyword pills -> English aliases
OLD_KW = '<li><b>Keyword pills</b> — Instrument / Brand / Model / Vibe / Patch groups. Combine to narrow. Active filters also appear as Search pills.'
NEW_KW = ('<li><b>Keyword pills</b> \u2014 Instrument / Brand / Model / Vibe / Patch groups. Combine to narrow. Active filters also appear as '
          'Search pills. Libraries whose name uses a non-English or obscure instrument word also carry the English keyword '
          '(e.g. <i>Floete</i> \u2192 flute, <i>Xilo</i> \u2192 xylophone, <i>Gjallar Horn</i> \u2192 horn), so the English search term finds them.')

# 6. User guide: new task block before "Find a library by Search"
ANCHOR_USER = """      <details open>
        <summary>Find a library by Search</summary>"""

QB_BLOCK = """      <details>
        <summary>Place the quick toolbar (phone)</summary>
        <p class="catalog-help-k">Goal</p>
        <p>Park the floating S / K / \u21C4 toolbar where it does not get in the way, and have it remembered for every way you use the screen.</p>
        <p class="catalog-help-k">Steps</p>
        <ol>
          <li>Hide the header bar (or turn on Customize) so the toolbar shows.</li>
          <li>Press and hold the toolbar for about 3 seconds until it lifts, then drag. Dock markers appear on the edges and on the seam between the menu and the content window (or between the two menus).</li>
          <li>Drop it on a seam to dock it there, or anywhere else to leave it free. Repeat for each way you use the screen: Search up, Keywords up, both, neither, flipped, portrait, landscape.</li>
        </ol>
        <p class="catalog-help-k">You should see</p>
        <p>A docked toolbar rides along when you drag the separator. Each combination of orientation, visible menus and Flip keeps its own spot: switch menus and the toolbar jumps to where you last left it for that combination, and comes back when you switch again. Positions are saved on this device.</p>
      </details>
""" + ANCHOR_USER


def main():
    for path in FILES:
        txt = open(path, encoding="utf-8").read()
        counts = {}
        for name, old, new in [
            ("legend_guide", OLD_LG, NEW_LG),
            ("header", OLD_HDR, NEW_HDR),
            ("customize", OLD_CUST, NEW_CUST),
            ("saved", OLD_SAVED, NEW_SAVED),
            ("kw", OLD_KW, NEW_KW),
            ("qb_block", ANCHOR_USER, QB_BLOCK),
        ]:
            counts[name] = txt.count(old)
            txt = txt.replace(old, new, 1)
        open(path, "w", encoding="utf-8").write(txt)
        print(path, counts)


if __name__ == "__main__":
    main()
