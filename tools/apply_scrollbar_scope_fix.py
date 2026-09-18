#!/usr/bin/env python3
"""
Fix the card-alignment regression: styling ::-webkit-scrollbar on the
universal `*` selector forces every matched element out of overlay
scrollbars into classic (space-reserving) scrollbars in
Chromium/WebKit, even for elements with only incidental sub-pixel
overflow -- which was throwing off the per-row card height/cover-size
equalization. Scope the themed scrollbar to actual scroll containers
instead of `*`.
"""

FILES = [
    "public/catalogs/DS-CATALOG.html",
    "public/catalogs/DS-CATALOG-portable.html",
    "public/catalogs/KONTAKT-CATALOG.html",
    "public/catalogs/KONTAKT-CATALOG-portable.html",
]

OLD = (
    "\n/* Theme-aware scrollbars for all scrollable content (position-indicating, native) */\n"
    "*{scrollbar-width:thin!important;scrollbar-color:var(--border) var(--bg-surface)!important}\n"
    "*::-webkit-scrollbar{width:10px!important;height:10px!important;display:block!important}\n"
    "*::-webkit-scrollbar-track{background:var(--bg-surface)!important}\n"
    "*::-webkit-scrollbar-thumb{background:var(--border)!important;border-radius:6px!important}\n"
    "*::-webkit-scrollbar-thumb:hover{background:var(--text-muted)!important}\n"
    "*::-webkit-scrollbar-corner{background:var(--bg-surface)!important}\n"
    "/* keep the search-autocomplete's own custom scroll indicator, no native scrollbar there */\n"
    ".search-autocomplete,.search-autocomplete::-webkit-scrollbar,"
    "#acList.search-autocomplete,#acList.search-autocomplete::-webkit-scrollbar"
    "{scrollbar-width:none!important;-ms-overflow-style:none!important}\n"
    ".search-autocomplete::-webkit-scrollbar,#acList.search-autocomplete::-webkit-scrollbar"
    "{display:none!important;width:0!important;height:0!important}\n"
)

SCROLL_SELECTORS = (
    "#catalogMain,.catalog-body,.summary-panel,#catalogIndexList,.index,#kwbar,"
    ".filter-wrap,.note-pop,.catalog-help-body,.ac-history-cloud,#historyPicks,"
    ".card-search-embed,.note-ta,.path,#acCtxBar,.layout-presets-list,.kw-shade-height"
)

NEW = (
    "\n/* Theme-aware scrollbars, scoped to actual scroll containers only -- styling\n"
    "   ::-webkit-scrollbar on `*` would force every element (even ones with only\n"
    "   incidental sub-pixel overflow) out of overlay scrollbars into classic\n"
    "   space-reserving ones, throwing off the per-row card equalization. */\n"
    + SCROLL_SELECTORS + "{scrollbar-width:thin;scrollbar-color:var(--border) var(--bg-surface)}\n"
    + SCROLL_SELECTORS + "::-webkit-scrollbar{width:10px;height:10px}\n"
    + SCROLL_SELECTORS + "::-webkit-scrollbar-track{background:var(--bg-surface)}\n"
    + SCROLL_SELECTORS + "::-webkit-scrollbar-thumb{background:var(--border);border-radius:6px}\n"
    + SCROLL_SELECTORS + "::-webkit-scrollbar-thumb:hover{background:var(--text-muted)}\n"
    + SCROLL_SELECTORS + "::-webkit-scrollbar-corner{background:var(--bg-surface)}\n"
    "/* keep the search-autocomplete's own custom scroll indicator, no native scrollbar there */\n"
    ".search-autocomplete,#acList.search-autocomplete{scrollbar-width:none!important;-ms-overflow-style:none!important}\n"
    ".search-autocomplete::-webkit-scrollbar,#acList.search-autocomplete::-webkit-scrollbar"
    "{display:none!important;width:0!important;height:0!important}\n"
)


def main():
    for path in FILES:
        txt = open(path, encoding="utf-8").read()
        ok = OLD in txt
        if ok:
            txt = txt.replace(OLD, NEW, 1)
        open(path, "w", encoding="utf-8").write(txt)
        print(f"{path}: fixed={ok}")


if __name__ == "__main__":
    main()
