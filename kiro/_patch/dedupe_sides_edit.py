#!/usr/bin/env python3
from pathlib import Path
import shutil

KIRO = Path("/home/phnx/KIRO/.kiro/specs/kontakt-workspace-drive-dirty-fix/artifacts")
WS = Path("/home/phnx/kiro-kontakt-patch/kiro/specs/kontakt-workspace-drive-dirty-fix/artifacts")
PUB = Path("/home/phnx/kiro-kontakt-patch/public/catalogs")

FILES = [
    KIRO / "build-ds-catalog-html.sh",
    KIRO / "build-kontakt-catalog-html.sh",
    WS / "build-ds-catalog-html.sh",
    WS / "build-kontakt-catalog-html.sh",
    PUB / "DS-CATALOG.html",
    PUB / "DS-CATALOG-portable.html",
    PUB / "KONTAKT-CATALOG.html",
    PUB / "KONTAKT-CATALOG-portable.html",
    WS / "DS-CATALOG.html",
    WS / "DS-CATALOG-portable.html",
    WS / "KONTAKT-CATALOG.html",
    WS / "KONTAKT-CATALOG-portable.html",
]

DUP_RECLICK = (
    "    if(typeof logSidesEdit==='function')logSidesEdit('H5','setDisplayMode','sides-reclick',{already:already,wasCol:wasCol});\n"
    "  }\n"
    "  var already=prev===mode;\n"
    "  if(mode==='sides'){\n"
    "    var wasCol=document.body.classList.contains('search-chrome-collapsed');\n"
    "    document.body.classList.remove('search-chrome-collapsed','search-extras-collapsed');\n"
    "    if(typeof syncSearchHideBtn==='function')syncSearchHideBtn();\n"
    "    if(typeof logSidesEdit==='function')logSidesEdit('H5','setDisplayMode','sides-reclick',{already:already,wasCol:wasCol});\n"
    "  }\n"
)
ONE_RECLICK = (
    "    if(typeof logSidesEdit==='function')logSidesEdit('H5','setDisplayMode','sides-reclick',{already:already,wasCol:wasCol});\n"
    "  }\n"
)
DUP_RM = (
    "    document.body.style.removeProperty('--sides-index-h');\n"
    "    document.body.style.removeProperty('--sides-index-h');\n"
)
ONE_RM = "    document.body.style.removeProperty('--sides-index-h');\n"


def dedupe(t, name):
    n = 0
    start = t.find("function logSidesEdit")
    start2 = t.find("function logSidesEdit", start + 10) if start >= 0 else -1
    if start2 >= 0:
        end2 = t.find("window.toggleModeLock=toggleModeLock;\n", start2)
        if end2 < 0:
            raise SystemExit(f"{name} missing second lock export")
        end2 += len("window.toggleModeLock=toggleModeLock;\n")
        t = t[:start2] + t[end2:]
        n += 1
    if DUP_RECLICK in t:
        t = t.replace(DUP_RECLICK, ONE_RECLICK, 1)
        n += 1
    if DUP_RM in t:
        t = t.replace(DUP_RM, ONE_RM)
        n += 1
    c1 = t.count("function logSidesEdit")
    c2 = t.count("var already=prev===mode;")
    if c1 != 1 or c2 != 1 or "function hideSearchAc" not in t:
        raise SystemExit(f"BAD {name} log={c1} already={c2}")
    if name.endswith(".html") and "</html>" not in t:
        raise SystemExit(f"BAD html {name}")
    customize = ">Customize</button>" in t
    print(f"{name}: fixes={n} customize={customize} bytes={len(t)}")
    return t


def main():
    for p in FILES:
        if not p.exists():
            print("missing", p)
            continue
        p.write_text(dedupe(p.read_text(encoding="utf-8"), p.name), encoding="utf-8")
    for name in ("build-ds-catalog-html.sh", "build-kontakt-catalog-html.sh"):
        shutil.copy2(KIRO / name, WS / name)
        print("copied", name)


if __name__ == "__main__":
    main()
