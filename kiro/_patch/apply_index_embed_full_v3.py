#!/usr/bin/env python3
"""Portable: re-pin Embed Index after portableEnsureScrollMenus strips inlines."""
from pathlib import Path

ROOT = Path("/home/phnx/kiro-kontakt-patch")
FILES = [
    ROOT / "public/catalogs/KONTAKT-CATALOG.html",
    ROOT / "public/catalogs/DS-CATALOG.html",
    ROOT / "public/catalogs/KONTAKT-CATALOG-portable.html",
    ROOT / "public/catalogs/DS-CATALOG-portable.html",
]
MARK = "fix-INDEX-EMBED-FULL-v3"
KEEP = (
    "c00e3e",
    "fix-CARD-EMBED-SEPARATE-v1",
    "fix-CARD-CHROME-TOP-v1",
    "fix-INDEX-EMBED-FULL-v1",
    "fix-INDEX-EMBED-FULL-v2",
    MARK,
)


def add_indent(s, n=1):
    pad = " " * n
    return "\n".join((pad + line) if line.strip() else line for line in s.split("\n"))


def sub(text, old, new, label, optional=False):
    n = text.count(old)
    if n == 1:
        return text.replace(old, new)
    if n > 1:
        raise SystemExit(f"{label}: {n} matches")
    if new in text:
        print(f"  skip {label} (already)")
        return text
    for i in range(1, 9):
        oldi, newi = add_indent(old, i), add_indent(new, i)
        ni = text.count(oldi)
        if ni == 1:
            return text.replace(oldi, newi)
        if ni > 1:
            raise SystemExit(f"{label}: {ni} matches (indent {i})")
        if newi in text:
            print(f"  skip {label} (already)")
            return text
    if optional:
        print(f"  skip {label}")
        return text
    raise SystemExit(f"{label}: not found")


CSS_ADD = r"""
/* fix-INDEX-EMBED-FULL-v3: beat portable opaque cap; Index may sit under #catalogMain */
html body.catalog-portable #catalogMain #catalogIndex.is-embedded:not(.is-collapsed),
html body.catalog-portable #catalogIndex.is-embedded:not(.is-collapsed),
html body.catalog-portable #catalogMain>.catalog-body>#catalogIndex.is-embedded:not(.is-collapsed),
html body.catalog-portable.display-sides #catalogMain>.catalog-body>#catalogIndex.is-embedded:not(.is-collapsed){
  height:auto!important;max-height:none!important;min-height:0!important;
  overflow:visible!important;overflow-x:visible!important;overflow-y:visible!important;
  flex:0 0 auto!important;position:relative!important;
  background:var(--bg-surface)!important;isolation:isolate!important
}
html body.catalog-portable #catalogMain #catalogIndex.is-embedded:not(.is-collapsed) .index,
html body.catalog-portable #catalogMain #catalogIndex.is-embedded:not(.is-collapsed) #catalogIndexList,
html body.catalog-portable #catalogIndex.is-embedded:not(.is-collapsed) .index,
html body.catalog-portable #catalogIndex.is-embedded:not(.is-collapsed) #catalogIndexList,
html body.catalog-portable #catalogMain #catalogIndex.is-embedded:not(.is-collapsed) ul#catalogIndexList.index{
  height:auto!important;max-height:none!important;min-height:0!important;flex:0 0 auto!important;
  overflow:visible!important;overflow-x:visible!important;overflow-y:visible!important;
  background:var(--bg-surface)!important
}
html body.catalog-portable:has(#catalogIndex.is-embedded:not(.is-collapsed)) #catalogJumpStack{
  display:none!important
}
"""

STRIP_OLD = """      [ilE,ix].forEach(function(el){
        if(!el)return;
        el.style.removeProperty('overflow');
        el.style.removeProperty('overflow-y');
        el.style.removeProperty('max-height');
        el.style.removeProperty('height');
      });
    }else{"""

STRIP_NEW = """      [ilE,ix].forEach(function(el){
        if(!el)return;
        el.style.removeProperty('overflow');
        el.style.removeProperty('overflow-y');
        el.style.removeProperty('max-height');
        el.style.removeProperty('height');
      });
      if(typeof syncIndexEmbedFull==='function')syncIndexEmbedFull();
    }else{"""


def patch(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    n = path.name
    if MARK in text:
        print("skip", n)
        return
    idx = text.rfind("</style>")
    if idx < 0:
        raise SystemExit(f"{n}: no </style>")
    text = text[:idx] + CSS_ADD + text[idx:]
    text = sub(text, STRIP_OLD, STRIP_NEW, f"{n}: ensure-scroll", optional="portable" not in n)
    raw = text.encode("utf-8")
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_bytes(raw)
    out = tmp.read_bytes().decode("utf-8")
    if not out.strip().endswith("</html>"):
        tmp.unlink()
        raise SystemExit(f"{n}: truncated")
    for keep in KEEP:
        if keep not in out:
            tmp.unlink()
            raise SystemExit(f"{n}: lost {keep}")
    tmp.replace(path)
    print("OK", n, len(raw))


def main() -> None:
    for p in FILES:
        if not p.exists():
            raise SystemExit(f"missing {p}")
        patch(p)


if __name__ == "__main__":
    main()
