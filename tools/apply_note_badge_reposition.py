#!/usr/bin/env python3
"""
1. Move the "has a note" badge (.un-badge) from an absolutely-positioned
   top-right corner overlay (which collided with the fullscreen/close
   buttons and, in the Sides "selected" preview, with the note-edit
   button) to sit inline right next to the card's title instead -- for
   every card in the grid, not just expanded ones.
2. Route clicking the card's name/title to the true fullscreen overlay
   (openOverlay) instead of the Sides "chosen preview" panel.
"""
import re

FILES = [
    "public/catalogs/DS-CATALOG.html",
    "public/catalogs/DS-CATALOG-portable.html",
    "public/catalogs/KONTAKT-CATALOG.html",
    "public/catalogs/KONTAKT-CATALOG-portable.html",
]

BADGE_SPAN = '<span class="un-badge" hidden title="User notes" aria-label="User notes">&#x1F4AC;</span>'

H3_RE = re.compile(r'(<h3 class="lib-name">[^<]*</h3>)')

OLD_BADGE_CSS = (
    " .un-badge{display:none;position:absolute;top:.5rem;right:.5rem;z-index:3;"
    "width:1.75rem;height:1.75rem;min-width:1.75rem;padding:0;align-items:center;"
    "justify-content:center;font-size:1rem;font-weight:400;letter-spacing:0;line-height:1;"
    "background:var(--accent-instrument-bg);color:var(--accent-instrument);"
    "border:1px solid var(--accent-instrument);border-radius:6px;pointer-events:none}\n"
    " .un-badge.has-note{display:inline-flex}\n"
    " .entry.selected:not(.highlight) .un-badge{right:3.5rem}\n"
    " .entry.highlight .un-badge{display:none!important}"
)

NEW_BADGE_CSS = (
    " .un-badge{display:none;margin:0 0 0 .4em;vertical-align:middle;position:relative;top:-.1em;"
    "width:1.5rem;height:1.5rem;min-width:1.5rem;padding:0;align-items:center;"
    "justify-content:center;font-size:.875rem;font-weight:400;letter-spacing:0;line-height:1;"
    "background:var(--accent-instrument-bg);color:var(--accent-instrument);"
    "border:1px solid var(--accent-instrument);border-radius:6px;pointer-events:none;flex:0 0 auto}\n"
    " .un-badge.has-note{display:inline-flex}\n"
    " .entry.highlight .un-badge{display:none!important}"
)

OLD_NAME_CLICK = "if(typeof openChosenPreview==='function')openChosenPreview(entry);"
NEW_NAME_CLICK = "if(typeof openOverlay==='function')openOverlay(entry);"


def main():
    for path in FILES:
        txt = open(path, encoding="utf-8").read()

        # 1a. Remove the old absolutely-positioned badge markup wherever it sits.
        n_removed = txt.count(BADGE_SPAN)
        txt = txt.replace(BADGE_SPAN, "")

        # 1b. Re-insert it right after every card title.
        txt, n_added = H3_RE.subn(r"\1" + BADGE_SPAN, txt)

        # 1c. Restyle it to sit inline instead of as a corner overlay.
        if OLD_BADGE_CSS in txt:
            txt = txt.replace(OLD_BADGE_CSS, NEW_BADGE_CSS, 1)
            css_ok = True
        else:
            css_ok = False

        # 2. Name-click opens the true fullscreen overlay.
        n_click = txt.count(OLD_NAME_CLICK)
        txt = txt.replace(OLD_NAME_CLICK, NEW_NAME_CLICK)

        open(path, "w", encoding="utf-8").write(txt)
        print(f"{path}: badge removed={n_removed} reinserted={n_added} css_patched={css_ok} name_click_patched={n_click}")


if __name__ == "__main__":
    main()
