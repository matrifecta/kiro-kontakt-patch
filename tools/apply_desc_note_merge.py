#!/usr/bin/env python3
"""Patch syncEntryMeta() in all 4 catalog HTML files so that a saved user
note is appended into the .desc paragraph itself (after the original
author description, separated by a rule, colored via --accent-note), and
the "no description" placeholder is suppressed when a note is present.
"""
import re

FILES = [
    "public/catalogs/DS-CATALOG.html",
    "public/catalogs/DS-CATALOG-portable.html",
    "public/catalogs/KONTAKT-CATALOG.html",
    "public/catalogs/KONTAKT-CATALOG-portable.html",
]

OLD = (
    "  var nt=el.querySelector('.note-text');\n"
    "  if(nt){nt.textContent=note;nt.hidden=!note;nt.classList.toggle('has-note',!!note);}\n"
    "}"
)

NEW = (
    "  var nt=el.querySelector('.note-text');\n"
    "  if(nt){nt.textContent=note;nt.hidden=!note;nt.classList.toggle('has-note',!!note);}\n"
    "  var dsc=el.querySelector('.desc');\n"
    "  if(dsc){\n"
    "    if(dsc.dataset.orig===undefined)dsc.dataset.orig=dsc.textContent;\n"
    "    var orig=dsc.dataset.orig;\n"
    "    var isPlaceholder=(orig.replace(/^\\s+|\\s+$/g,'')===NO_DESC_TEXT);\n"
    "    var escOrig=escHtml(orig);\n"
    "    var escNote=note?escHtml(note).replace(/\\n/g,'<br>'):'';\n"
    "    var html='';\n"
    "    if(!(isPlaceholder&&note))html=escOrig;\n"
    "    if(note)html+=(html?'<hr class=\"desc-note-sep\">':'')+'<span class=\"desc-user-note\">'+escNote+'</span>';\n"
    "    dsc.innerHTML=html;\n"
    "  }\n"
    "}"
)

ESC_FN = (
    "var NO_DESC_TEXT='No additional description provided.';\n"
    "function escHtml(s){return String(s==null?'':s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');}\n"
)


def main():
    for path in FILES:
        txt = open(path, encoding="utf-8").read()
        if OLD not in txt:
            print(f"  WARN: anchor not found in {path}")
            continue
        txt = txt.replace(OLD, NEW, 1)
        if "function escHtml(" not in txt:
            txt = txt.replace("function syncEntryMeta(el){", ESC_FN + "function syncEntryMeta(el){", 1)
        open(path, "w", encoding="utf-8").write(txt)
        print(f"{path}: patched")


if __name__ == "__main__":
    main()
