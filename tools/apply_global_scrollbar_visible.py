#!/usr/bin/env python3
"""
A pre-existing global rule was hiding every scrollbar in the whole
document with !important, silently overriding the themed scrollbar
styling added earlier. Remove that blanket hide (keeping the
search-autocomplete-specific hides, which have their own custom scroll
indicator UI), and make the themed scrollbar rule !important too so it
reliably wins and every scrollable panel shows a themed, position-
indicating scrollbar whenever its content actually overflows.
"""

FILES = [
    "public/catalogs/DS-CATALOG.html",
    "public/catalogs/DS-CATALOG-portable.html",
    "public/catalogs/KONTAKT-CATALOG.html",
    "public/catalogs/KONTAKT-CATALOG-portable.html",
]

OLD_HIDE = (
    "/* fix-SB: no scrollbar chrome — content still scrollable */"
    "*::-webkit-scrollbar{display:none!important}"
    "*{scrollbar-width:none!important;-ms-overflow-style:none!important}"
)
NEW_HIDE = "/* fix-SB: scrollbar chrome restored + themed, see .desc-user-note block below */"

OLD_THEME_SB = (
    "\n/* Theme-aware scrollbars for all scrollable content */\n"
    "*{scrollbar-width:thin;scrollbar-color:var(--border) var(--bg-surface)}\n"
    "*::-webkit-scrollbar{width:10px;height:10px}\n"
    "*::-webkit-scrollbar-track{background:var(--bg-surface)}\n"
    "*::-webkit-scrollbar-thumb{background:var(--border);border-radius:6px}\n"
    "*::-webkit-scrollbar-thumb:hover{background:var(--text-muted)}\n"
    "*::-webkit-scrollbar-corner{background:var(--bg-surface)}\n"
)

NEW_THEME_SB = (
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


def main():
    for path in FILES:
        txt = open(path, encoding="utf-8").read()
        hide_ok = OLD_HIDE in txt
        if hide_ok:
            txt = txt.replace(OLD_HIDE, NEW_HIDE, 1)
        theme_ok = OLD_THEME_SB in txt
        if theme_ok:
            txt = txt.replace(OLD_THEME_SB, NEW_THEME_SB, 1)
        open(path, "w", encoding="utf-8").write(txt)
        print(f"{path}: blanket_hide_removed={hide_ok} theme_rule_upgraded={theme_ok}")


if __name__ == "__main__":
    main()
