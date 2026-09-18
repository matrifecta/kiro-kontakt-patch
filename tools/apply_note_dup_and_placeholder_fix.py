#!/usr/bin/env python3
"""
1. Stop the standalone .note-text box from ever being shown (the note is
   now merged into .desc only) by never toggling its 'has-note' class /
   always keeping it hidden.
2. Strictly replace ALL remaining boilerplate placeholder descriptions
   ("Decent Sampler library: X. Tags: Y." / "Kontakt library: X." /
   "Native Instruments library: X. Tags: Y.") with the neutral
   placeholder text, with no exceptions.
"""
import re

FILES = [
    "public/catalogs/DS-CATALOG.html",
    "public/catalogs/DS-CATALOG-portable.html",
    "public/catalogs/KONTAKT-CATALOG.html",
    "public/catalogs/KONTAKT-CATALOG-portable.html",
]

PLACEHOLDER = "No additional description provided."

OLD_NT = (
    "  var nt=el.querySelector('.note-text');\n"
    "  if(nt){nt.textContent=note;nt.hidden=!note;nt.classList.toggle('has-note',!!note);}\n"
)
NEW_NT = (
    "  var nt=el.querySelector('.note-text');\n"
    "  if(nt){nt.hidden=true;nt.classList.remove('has-note');nt.textContent='';}\n"
)

BOILERPLATE_DESC_RE = re.compile(
    r'(<p class="desc">)(Decent Sampler library:|Kontakt library:|Native Instruments library:)([^<]*)(</p>)'
)


def main():
    for path in FILES:
        txt = open(path, encoding="utf-8").read()
        n_js = 0
        if OLD_NT in txt:
            txt = txt.replace(OLD_NT, NEW_NT, 1)
            n_js = 1
        else:
            print(f"  WARN: JS anchor not found in {path}")

        def repl(m):
            return m.group(1) + PLACEHOLDER + m.group(4)

        txt, n_desc = BOILERPLATE_DESC_RE.subn(repl, txt)
        open(path, "w", encoding="utf-8").write(txt)
        print(f"{path}: js_patched={bool(n_js)} placeholders_applied={n_desc}")


if __name__ == "__main__":
    main()
