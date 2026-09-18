#!/usr/bin/env python3
"""
Critical fix: `A,B,C::-webkit-scrollbar{...}` only attaches the
pseudo-element to the LAST selector (C); A and B are treated as plain
element selectors, so `{width:10px;height:10px}` was being applied
directly to .path/.summary-panel/etc, collapsing them to 10px/34px.
Expand the pseudo-element onto every selector individually.
"""

FILES = [
    "public/catalogs/DS-CATALOG.html",
    "public/catalogs/DS-CATALOG-portable.html",
    "public/catalogs/KONTAKT-CATALOG.html",
    "public/catalogs/KONTAKT-CATALOG-portable.html",
]

BASE_SELECTORS = [
    "#catalogMain", ".catalog-body", ".summary-panel", "#catalogIndexList", ".index",
    "#kwbar", ".filter-wrap", ".note-pop", ".catalog-help-body", ".ac-history-cloud",
    "#historyPicks", ".card-search-embed", ".note-ta", ".path", "#acCtxBar",
    ".layout-presets-list", ".kw-shade-height",
]

BROKEN_JOINED = ",".join(BASE_SELECTORS)

PSEUDO_RULES = [
    ("::-webkit-scrollbar", "{width:10px;height:10px}"),
    ("::-webkit-scrollbar-track", "{background:var(--bg-surface)}"),
    ("::-webkit-scrollbar-thumb", "{background:var(--border);border-radius:6px}"),
    ("::-webkit-scrollbar-thumb:hover", "{background:var(--text-muted)}"),
    ("::-webkit-scrollbar-corner", "{background:var(--bg-surface)}"),
]


def expand(pseudo):
    return ",".join(s + pseudo for s in BASE_SELECTORS)


def main():
    for path in FILES:
        txt = open(path, encoding="utf-8").read()
        n_fixed = 0
        for pseudo, body in PSEUDO_RULES:
            old = BROKEN_JOINED + pseudo + body
            new = expand(pseudo) + body
            if old in txt:
                txt = txt.replace(old, new, 1)
                n_fixed += 1
            else:
                print(f"  WARN: pattern for {pseudo} not found in {path}")
        open(path, "w", encoding="utf-8").write(txt)
        print(f"{path}: {n_fixed}/5 rules fixed")


if __name__ == "__main__":
    main()
