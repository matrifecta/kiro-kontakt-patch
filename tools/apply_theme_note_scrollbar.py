#!/usr/bin/env python3
"""Add a themed --accent-note color variable (per data-theme block) and
global theme-aware scrollbar styling to all 4 catalog HTML files.
"""
import re

FILES = [
    "public/catalogs/DS-CATALOG.html",
    "public/catalogs/DS-CATALOG-portable.html",
    "public/catalogs/KONTAKT-CATALOG.html",
    "public/catalogs/KONTAKT-CATALOG-portable.html",
]

NOTE_COLORS = {
    "desert": "#7fb3e0",
    "studio": "#7fb3e0",
    "smoked": "#7fb3e0",
    "sandstorm": "#2f5fa8",
    "bleached": "#2f5fa8",
    "spring-bloom": "#2f5fa8",
    "spring-rain": "#7fb3e0",
    "summer-beach": "#0f6fae",
    "tropical-night": "#7fb3e0",
    "autumn-ember": "#7fb3e0",
    "harvest": "#2f5fa8",
    "arctic": "#1060c0",
    "deep-winter": "#6090e0",
    "hc-dark": "#4da6ff",
    "hc-light": "#0033cc",
}

SCROLLBAR_CSS = (
    "\n/* Theme-aware scrollbars for all scrollable content */\n"
    "*{scrollbar-width:thin;scrollbar-color:var(--border) var(--bg-surface)}\n"
    "*::-webkit-scrollbar{width:10px;height:10px}\n"
    "*::-webkit-scrollbar-track{background:var(--bg-surface)}\n"
    "*::-webkit-scrollbar-thumb{background:var(--border);border-radius:6px}\n"
    "*::-webkit-scrollbar-thumb:hover{background:var(--text-muted)}\n"
    "*::-webkit-scrollbar-corner{background:var(--bg-surface)}\n"
    ".desc-user-note{color:var(--accent-note);display:block}\n"
    ".desc-note-sep{border:none;border-top:1px dashed var(--border);margin:.6em 0}\n"
)


def add_note_var(txt):
    n = 0
    for theme, color in NOTE_COLORS.items():
        pat = re.compile(
            r'(\[data-theme="' + re.escape(theme) + r'"\]\{[^}]*?)\}'
        )
        def repl(m, color=color):
            return m.group(1) + ";--accent-note:" + color + "}"
        new_txt, k = pat.subn(repl, txt, count=1)
        if k:
            txt = new_txt
            n += 1
        else:
            print(f"  WARN: theme block not found: {theme}")
    return txt, n


def main():
    for path in FILES:
        txt = open(path, encoding="utf-8").read()
        txt, n = add_note_var(txt)
        if "desc-user-note{" not in txt:
            txt = txt.replace("</style>", SCROLLBAR_CSS + "</style>", 1)
        open(path, "w", encoding="utf-8").write(txt)
        print(f"{path}: {n} theme note-colors set, scrollbar css injected")


if __name__ == "__main__":
    main()
