#!/usr/bin/env python3
"""Portable first-open: hide dead scale, label ⛶ and Customize."""
from pathlib import Path

ROOT = Path("/home/phnx/kiro-kontakt-patch/public/catalogs")
FILES = [ROOT / "DS-CATALOG-portable.html", ROOT / "KONTAKT-CATALOG-portable.html"]

CSS_MARK = "/* fix-PORTABLE-FIRST-OPEN:"
CSS = """
/* fix-PORTABLE-FIRST-OPEN: hide dead Pick/scale; keep S/K on header */
@media all{
  body.catalog-portable .search-only-scale,
  body.catalog-portable #searchOnlyScale,
  body.catalog-portable #uiScale,
  body.catalog-portable .fs-stripe-scale,
  body.catalog-portable .mode-btn[data-mode="pick"]{display:none!important}
}
"""

EDIT_OLD = "layout-edit')?'Done':'Edit'"
EDIT_NEW = "layout-edit')?'Done':'Customize'"

SFS_OLD = 'id="searchStripFs" onclick="toggleAcFullscreen()" aria-pressed="false" aria-label="Fullscreen search" title="Full">'
SFS_NEW = 'id="searchStripFs" onclick="toggleAcFullscreen()" aria-pressed="false" aria-label="Fullscreen Search" title="Fullscreen Search">'

KFS_OLD = 'id="kwStripFs" aria-pressed="false" aria-label="Fullscreen Keywords" title="Full"'
KFS_NEW = 'id="kwStripFs" aria-pressed="false" aria-label="Fullscreen Keywords" title="Fullscreen Keywords"'

MID_OLD = 'title="Middle: Search and Keywords on top, catalog below"'
MID_NEW = 'title="Middle: one menu on top, catalog below"'


def patch(text):
    if CSS_MARK not in text:
        if "</style></head><body class=\"search-mode\">" not in text:
            raise SystemExit("style close not found")
        text = text.replace("</style></head><body class=\"search-mode\">", CSS + "\n</style></head><body class=\"search-mode\">", 1)
    n = text.count(EDIT_OLD)
    if n < 1:
        raise SystemExit(f"Edit label missing ({n})")
    text = text.replace(EDIT_OLD, EDIT_NEW)
    if SFS_OLD in text:
        text = text.replace(SFS_OLD, SFS_NEW, 1)
    if KFS_OLD in text:
        text = text.replace(KFS_OLD, KFS_NEW, 1)
    if MID_OLD in text:
        text = text.replace(MID_OLD, MID_NEW, 1)
    return text


def main():
    for path in FILES:
        raw = path.read_text(encoding="utf-8")
        path.write_text(patch(raw), encoding="utf-8")
        print(f"patched {path.name}")


if __name__ == "__main__":
    main()
