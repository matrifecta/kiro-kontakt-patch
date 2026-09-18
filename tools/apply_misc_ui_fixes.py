#!/usr/bin/env python3
"""
- Remove the underline from the numbered location-group headers
  ("1. Via SAMPLE STORE...", "2. Via FILE BROWSER...", etc.) without
  touching the global h2 rule used elsewhere.
- Remove the stray period + odd spacing in the FILE BROWSER breadcrumb
  line ("DS Libraries . Root:" -> "DS Libraries Root:" reads oddly;
  use an en dash separator instead for clarity).
- Nudge the note-view-btn left/up slightly so it's better centered
  between Search and Favorite.
- Give the card title a direct onclick (in addition to the delegated
  handler) so "click name -> open expanded view" is robust everywhere.
"""
import re

FILES = [
    "public/catalogs/DS-CATALOG.html",
    "public/catalogs/DS-CATALOG-portable.html",
    "public/catalogs/KONTAKT-CATALOG.html",
    "public/catalogs/KONTAKT-CATALOG-portable.html",
]

# 1. Underline removal for loc-group headers.
OLD_H2_LAYOUT = " .catalog-body>h2,.catalog-body>p,.loc-group>h2,.loc-group>p,.loc-group>.loc-hint{grid-column:1/-1;order:-5}"
NEW_H2_LAYOUT = (
    " .catalog-body>h2,.catalog-body>p,.loc-group>h2,.loc-group>p,.loc-group>.loc-hint{grid-column:1/-1;order:-5}\n"
    " .catalog-body>h2,.loc-group>h2{border-bottom:0;padding-bottom:0}"
)

# 2. Breadcrumb text cleanup.
OLD_HINT_1 = '<p class="loc-hint">FILE BROWSER &rarr; <b>btrfs</b> &rarr; <code>DS Libraries</code>. Root: <code>/mnt/btrfs_disk/DS Libraries</code></p>'
NEW_HINT_1 = '<p class="loc-hint">FILE BROWSER &rarr; <b>btrfs</b> &rarr; <code>DS Libraries</code> &mdash; Root: <code>/mnt/btrfs_disk/DS Libraries</code></p>'
OLD_HINT_2 = '<p class="loc-hint">FILE BROWSER &rarr; <b>wd_black</b> &rarr; <code>DS Libraries</code>. Root: <code>/mnt/wd_black/DS Libraries</code></p>'
NEW_HINT_2 = '<p class="loc-hint">FILE BROWSER &rarr; <b>wd_black</b> &rarr; <code>DS Libraries</code> &mdash; Root: <code>/mnt/wd_black/DS Libraries</code></p>'

# 3. Button nudge.
OLD_BTN_POS = "right:calc(.5rem + var(--card-chrome-btn) + .5rem);bottom:.5rem;top:auto;left:auto;"
NEW_BTN_POS = "right:calc(.5rem + var(--card-chrome-btn) + .65rem);bottom:.65rem;top:auto;left:auto;"

# 4. Direct onclick on the card title.
H3_RE = re.compile(r'<h3 class="lib-name">')
H3_REPLACEMENT = (
    '<h3 class="lib-name" onclick="event.preventDefault();event.stopPropagation();'
    "if(typeof openOverlay==='function')openOverlay(this.closest('.entry'))\">"
)


def main():
    for path in FILES:
        txt = open(path, encoding="utf-8").read()

        h2_ok = OLD_H2_LAYOUT in txt
        if h2_ok:
            txt = txt.replace(OLD_H2_LAYOUT, NEW_H2_LAYOUT, 1)

        n_hint1 = txt.count(OLD_HINT_1)
        txt = txt.replace(OLD_HINT_1, NEW_HINT_1)
        n_hint2 = txt.count(OLD_HINT_2)
        txt = txt.replace(OLD_HINT_2, NEW_HINT_2)

        btn_ok = OLD_BTN_POS in txt
        if btn_ok:
            txt = txt.replace(OLD_BTN_POS, NEW_BTN_POS, 1)

        txt, n_h3 = H3_RE.subn(H3_REPLACEMENT, txt)

        open(path, "w", encoding="utf-8").write(txt)
        print(f"{path}: h2_underline_removed={h2_ok} hint1={n_hint1} hint2={n_hint2} btn_nudged={btn_ok} h3_onclick={n_h3}")


if __name__ == "__main__":
    main()
