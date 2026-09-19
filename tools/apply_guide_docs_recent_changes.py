#!/usr/bin/env python3
"""Bring the in-catalog Legend / User guide / Update guide up to date with the
last several days of chrome changes: the YouTube comments pane (toggle, wide
vs split, expand-on-collapse), the pinned-dock pill fix (no reflow while a
video plays), the pinned-card restore-from-filter fix (a card that was hidden
by the filter now reliably reappears when un-minimized), and a short dated
changelog entry in the Update guide, since this repo keeps no standalone
changelog file -- the Update guide is the record."""

FILES = [
    "public/catalogs/DS-CATALOG.html",
    "public/catalogs/DS-CATALOG-portable.html",
    "public/catalogs/KONTAKT-CATALOG.html",
    "public/catalogs/KONTAKT-CATALOG-portable.html",
]

# 1. Legend: Pinned pyramid -> describe the stable pill + restore-from-filter fix
OLD_PIN = '<li><b>Pinned pyramid</b> — minimized cards dock at the bottom of the content window (Save on Middle).</li>'
NEW_PIN = (
    '<li><b>Pinned pyramid</b> \u2014 minimized cards dock at the bottom of the content window (Save on Middle). '
    'A cover-sized frame holds the still cover and, while playing, the video in the same spot, so the pill keeps '
    'its width and the name / close button never shift. Reopening a pinned card always shows it, even if a filter '
    'or search would otherwise have hidden it.</li>'
)

# 2. Legend: Card Search -> describe the comments pane
OLD_CS = '<li><b>Card Search</b> — in-card Google / YouTube / image search when a card is expanded (embed vs popup depends on portable).</li>'
NEW_CS = (
    '<li><b>Card Search</b> \u2014 in-card Google / YouTube / image search when a card is expanded (embed vs popup '
    'depends on portable). A YouTube result adds a <b>comments pane</b> beside (wide) or under (split) the video; '
    'a thin seam tab toggles it away and back. Collapsing the pane while the layout has room lets the video stage '
    'expand into the freed space; the tab still works the same in fullscreen.</li>'
)

# 3. Update guide: insert a dated "Recent changes" block right after the Rebuild / refresh block
ANCHOR_UPDATE = '''      <details>
        <summary>After a new catalog drop</summary>'''

CHANGELOG_BLOCK = '''      <details>
        <summary>Recent changes (this week)</summary>
        <ul>
          <li><b>YouTube comments pane</b> \u2014 a card search video result now carries a collapsible comments list beside it (wide layouts) or under it (split/narrow), with a seam tab to hide/show, and the video stage expands to fill the space when the pane is collapsed. Works the same fullscreened.</li>
          <li><b>Pinned-dock pill fix</b> \u2014 the minimized-card pill no longer reflows or misaligns its name / close button when a video starts or stops playing; the cover and the video now share one fixed-size frame instead of the video pushing a new item into the pill row.</li>
          <li><b>Pinned-card restore fix</b> \u2014 reopening a card from the pinned dock while a filter/search had it hidden now always shows it, instead of occasionally opening to nothing until the filter changed again.</li>
          <li><b>Smoother custom scrollbar</b> \u2014 the hover-scroll thumb (the shadow scrollbar beside the native one) is now positioned with a compositor-only transform instead of a layout-triggering style, so it should not lag behind fast scrolling on long columns.</li>
          <li><b>Quick toolbar (phone)</b> \u2014 remembers a separate dock/position per orientation and per combination of visible menus (Search / Keywords / Flip / Middle); see <i>Place the quick toolbar</i> in the User guide.</li>
          <li><b>English keyword aliases</b>, a Middle-mode Keywords bottom border, centred mobile hide/show tabs, and note-button alignment/UX polish also landed this week.</li>
        </ul>
      </details>
''' + ANCHOR_UPDATE


def main():
    for path in FILES:
        txt = open(path, encoding="utf-8").read()
        counts = {}
        for name, old, new in [
            ("pinned_pyramid", OLD_PIN, NEW_PIN),
            ("card_search", OLD_CS, NEW_CS),
            ("changelog", ANCHOR_UPDATE, CHANGELOG_BLOCK),
        ]:
            counts[name] = txt.count(old)
            if counts[name] != 1:
                raise SystemExit(f"{path}: expected 1 match for {name}, got {counts[name]}")
            txt = txt.replace(old, new, 1)
        open(path, "w", encoding="utf-8").write(txt)
        print(path, counts)


if __name__ == "__main__":
    main()
