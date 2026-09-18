#!/usr/bin/env python3
"""
Move the "has a note" badge from next to the card title down into the
PATH row itself: it now sits as the first item in that flex row (left
side, vertically centered / "leveled" with the row that holds the 3
path icon buttons), below the description panel.
"""
import re

FILES = [
    "public/catalogs/DS-CATALOG.html",
    "public/catalogs/DS-CATALOG-portable.html",
    "public/catalogs/KONTAKT-CATALOG.html",
    "public/catalogs/KONTAKT-CATALOG-portable.html",
]

BADGE_SPAN = '<span class="un-badge" hidden title="User notes" aria-label="User notes">&#x1F4AC;</span>'

# Undo the previous "next to title" placement.
TITLE_BADGE_RE = re.compile(r'(<h3 class="lib-name">[^<]*</h3>)' + re.escape(BADGE_SPAN))

# Re-insert as the first child of the PATH row.
PATH_OPEN_RE = re.compile(r'(<div class="path"><b>)')

OLD_CSS = (
    " .un-badge{display:none;margin:0 0 0 .4em;vertical-align:middle;position:relative;top:-.1em;"
    "width:1.5rem;height:1.5rem;min-width:1.5rem;padding:0;align-items:center;"
    "justify-content:center;font-size:.875rem;font-weight:400;letter-spacing:0;line-height:1;"
    "background:var(--accent-instrument-bg);color:var(--accent-instrument);"
    "border:1px solid var(--accent-instrument);border-radius:6px;pointer-events:none;flex:0 0 auto}\n"
    " .un-badge.has-note{display:inline-flex}\n"
    " .entry.highlight .un-badge{display:none!important}"
)

NEW_CSS = (
    " .un-badge{display:none;order:-1;flex:0 0 auto;align-self:center;"
    "width:1.5rem;height:1.5rem;min-width:1.5rem;padding:0;align-items:center;"
    "justify-content:center;font-size:.875rem;font-weight:400;letter-spacing:0;line-height:1;"
    "background:var(--accent-instrument-bg);color:var(--accent-instrument);"
    "border:1px solid var(--accent-instrument);border-radius:6px;pointer-events:none}\n"
    " .un-badge.has-note{display:inline-flex}\n"
    " .entry.highlight .un-badge{display:none!important}"
)


def main():
    for path in FILES:
        txt = open(path, encoding="utf-8").read()

        txt, n_removed = TITLE_BADGE_RE.subn(r"\1", txt)
        txt, n_added = PATH_OPEN_RE.subn(BADGE_SPAN + r"\1", txt)

        css_ok = OLD_CSS in txt
        if css_ok:
            txt = txt.replace(OLD_CSS, NEW_CSS, 1)

        open(path, "w", encoding="utf-8").write(txt)
        print(f"{path}: removed_from_title={n_removed} added_to_path={n_added} css_patched={css_ok}")


if __name__ == "__main__":
    main()
