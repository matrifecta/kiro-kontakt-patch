#!/usr/bin/env python3
"""Landscape Middle one-menu: Search/Keywords + content, no Flip ghost pane."""
from pathlib import Path

ROOT = Path("/home/phnx/kiro-kontakt-patch")
FILES = [
    ROOT / "public/catalogs/KONTAKT-CATALOG.html",
    ROOT / "public/catalogs/DS-CATALOG.html",
    ROOT / "public/catalogs/KONTAKT-CATALOG-portable.html",
    ROOT / "public/catalogs/DS-CATALOG-portable.html",
]
MARK = "fix-MIDDLE-ONE-FILL-v1"
KEEP = (
    "fix-DESKTOP-SK-PAIR",
    "fix-MIDDLE-ONE-MENU",
    "fix-DESKTOP-FLIP-ARRANGE",
    "fix-INDEX-EMBED-SCROLL-v1",
    "name click expand",
    "c00e3e",
    MARK,
)


def add_indent(s, n=1):
    pad = " " * n
    return "\n".join((pad + line) if line.strip() else line for line in s.split("\n"))


def sub(text, old, new, label, optional=False):
    n = text.count(old)
    if n == 1:
        return text.replace(old, new, 1)
    if n > 1:
        raise SystemExit(f"{label}: {n} matches")
    if new in text:
        print(f"  skip {label} (already)")
        return text
    for i in range(1, 9):
        oldi, newi = add_indent(old, i), add_indent(new, i)
        ni = text.count(oldi)
        if ni == 1:
            return text.replace(oldi, newi, 1)
        if ni > 1:
            raise SystemExit(f"{label}: {ni} matches (indent {i})")
        if ni == 0 and newi in text:
            print(f"  skip {label} (already)")
            return text
    if optional:
        print(f"  skip {label}")
        return text
    raise SystemExit(f"{label}: not found")


CSS_OLD = """  body.desk-landscape.display-sides.display-middle:not(.catalog-portable).search-chrome-collapsed:not(.kw-chrome-collapsed) #catalogMain,
  body.desk-landscape.display-sides.display-middle:not(.catalog-portable).kw-chrome-collapsed:not(.search-chrome-collapsed) #catalogMain{
    grid-column:1/-1!important;grid-row:3!important;flex:unset!important
  }
}

.collapse-cards-btn{flex-shrink:0;box-sizing:border-box;min-height:2.25rem;background:transparent;border:1px solid var(--border);color:var(--text-muted);border-radius:4px;padding:0 .625rem;font-size:.875rem;cursor:pointer;touch-action:manipulation;white-space:nowrap}"""

CSS_NEW = """  body.desk-landscape.display-sides.display-middle:not(.catalog-portable).search-chrome-collapsed:not(.kw-chrome-collapsed) #catalogMain,
  body.desk-landscape.display-sides.display-middle:not(.catalog-portable).kw-chrome-collapsed:not(.search-chrome-collapsed) #catalogMain{
    grid-column:1/-1!important;grid-row:3!important;flex:unset!important
  }
}
/* fix-MIDDLE-ONE-FILL-v1: landscape Middle one menu + content; Flip swaps; no ghost track */
@media(min-width:900px) and (orientation:landscape){
  body.display-sides.display-middle:not(.catalog-portable).kw-chrome-collapsed:not(.search-chrome-collapsed),
  body.desk-landscape.display-sides.display-middle:not(.catalog-portable).kw-chrome-collapsed:not(.search-chrome-collapsed){
    grid-template-columns:var(--sides-lw,22vw) minmax(0,1fr)!important;
    grid-template-rows:auto minmax(0,1fr) var(--card-min-dock-h,0px)!important
  }
  body.display-sides.display-middle:not(.catalog-portable).kw-chrome-collapsed:not(.search-chrome-collapsed) #searchChrome,
  body.desk-landscape.display-sides.display-middle:not(.catalog-portable).kw-chrome-collapsed:not(.search-chrome-collapsed) #searchChrome{
    display:flex!important;grid-column:1!important;grid-row:2!important;
    width:100%!important;max-width:none!important;height:100%!important;max-height:none!important;min-height:0!important
  }
  body.display-sides.display-middle:not(.catalog-portable).kw-chrome-collapsed:not(.search-chrome-collapsed) #catalogMain,
  body.desk-landscape.display-sides.display-middle:not(.catalog-portable).kw-chrome-collapsed:not(.search-chrome-collapsed) #catalogMain{
    grid-column:2!important;grid-row:2!important;width:auto!important;max-width:none!important;flex:unset!important
  }
  body.display-sides.display-middle:not(.catalog-portable).kw-chrome-collapsed:not(.search-chrome-collapsed) #filterWrap,
  body.desk-landscape.display-sides.display-middle:not(.catalog-portable).kw-chrome-collapsed:not(.search-chrome-collapsed) #filterWrap{
    display:none!important;width:0!important;min-width:0!important;max-width:0!important;height:0!important
  }
  body.display-sides.display-middle:not(.catalog-portable).sides-portrait-flip.kw-chrome-collapsed:not(.search-chrome-collapsed),
  body.desk-landscape.display-sides.display-middle:not(.catalog-portable).sides-portrait-flip.kw-chrome-collapsed:not(.search-chrome-collapsed){
    grid-template-columns:minmax(0,1fr) var(--sides-lw,22vw)!important;
    grid-template-rows:auto minmax(0,1fr) var(--card-min-dock-h,0px)!important
  }
  body.display-sides.display-middle:not(.catalog-portable).sides-portrait-flip.kw-chrome-collapsed:not(.search-chrome-collapsed) #catalogMain,
  body.desk-landscape.display-sides.display-middle:not(.catalog-portable).sides-portrait-flip.kw-chrome-collapsed:not(.search-chrome-collapsed) #catalogMain{
    grid-column:1!important;grid-row:2!important
  }
  body.display-sides.display-middle:not(.catalog-portable).sides-portrait-flip.kw-chrome-collapsed:not(.search-chrome-collapsed) #searchChrome,
  body.desk-landscape.display-sides.display-middle:not(.catalog-portable).sides-portrait-flip.kw-chrome-collapsed:not(.search-chrome-collapsed) #searchChrome{
    display:flex!important;grid-column:2!important;grid-row:2!important
  }
  body.display-sides.display-middle:not(.catalog-portable).search-chrome-collapsed:not(.kw-chrome-collapsed),
  body.desk-landscape.display-sides.display-middle:not(.catalog-portable).search-chrome-collapsed:not(.kw-chrome-collapsed){
    grid-template-columns:minmax(0,1fr) var(--sides-rw,26vw)!important;
    grid-template-rows:auto minmax(0,1fr) var(--card-min-dock-h,0px)!important
  }
  body.display-sides.display-middle:not(.catalog-portable).search-chrome-collapsed:not(.kw-chrome-collapsed) #filterWrap,
  body.desk-landscape.display-sides.display-middle:not(.catalog-portable).search-chrome-collapsed:not(.kw-chrome-collapsed) #filterWrap{
    display:flex!important;grid-column:2!important;grid-row:2!important;
    width:100%!important;max-width:none!important;height:100%!important;max-height:none!important;min-height:0!important
  }
  body.display-sides.display-middle:not(.catalog-portable).search-chrome-collapsed:not(.kw-chrome-collapsed) #catalogMain,
  body.desk-landscape.display-sides.display-middle:not(.catalog-portable).search-chrome-collapsed:not(.kw-chrome-collapsed) #catalogMain{
    grid-column:1!important;grid-row:2!important;width:auto!important;max-width:none!important;flex:unset!important
  }
  body.display-sides.display-middle:not(.catalog-portable).search-chrome-collapsed:not(.kw-chrome-collapsed) #searchChrome,
  body.desk-landscape.display-sides.display-middle:not(.catalog-portable).search-chrome-collapsed:not(.kw-chrome-collapsed) #searchChrome{
    display:none!important;width:0!important;min-width:0!important;max-width:0!important;height:0!important
  }
  body.display-sides.display-middle:not(.catalog-portable).sides-portrait-flip.search-chrome-collapsed:not(.kw-chrome-collapsed),
  body.desk-landscape.display-sides.display-middle:not(.catalog-portable).sides-portrait-flip.search-chrome-collapsed:not(.kw-chrome-collapsed){
    grid-template-columns:var(--sides-rw,26vw) minmax(0,1fr)!important;
    grid-template-rows:auto minmax(0,1fr) var(--card-min-dock-h,0px)!important
  }
  body.display-sides.display-middle:not(.catalog-portable).sides-portrait-flip.search-chrome-collapsed:not(.kw-chrome-collapsed) #filterWrap,
  body.desk-landscape.display-sides.display-middle:not(.catalog-portable).sides-portrait-flip.search-chrome-collapsed:not(.kw-chrome-collapsed) #filterWrap{
    display:flex!important;grid-column:1!important;grid-row:2!important
  }
  body.display-sides.display-middle:not(.catalog-portable).sides-portrait-flip.search-chrome-collapsed:not(.kw-chrome-collapsed) #catalogMain,
  body.desk-landscape.display-sides.display-middle:not(.catalog-portable).sides-portrait-flip.search-chrome-collapsed:not(.kw-chrome-collapsed) #catalogMain{
    grid-column:2!important;grid-row:2!important
  }
}

.collapse-cards-btn{flex-shrink:0;box-sizing:border-box;min-height:2.25rem;background:transparent;border:1px solid var(--border);color:var(--text-muted);border-radius:4px;padding:0 .625rem;font-size:.875rem;cursor:pointer;touch-action:manipulation;white-space:nowrap}"""


CSS_OLD_PORT = """  body.desk-landscape.display-sides.display-middle:not(.catalog-portable).search-chrome-collapsed:not(.kw-chrome-collapsed) #catalogMain,
  body.desk-landscape.display-sides.display-middle:not(.catalog-portable).kw-chrome-collapsed:not(.search-chrome-collapsed) #catalogMain{
    grid-column:1/-1!important;grid-row:3!important;flex:unset!important
  }
}

/* fix-PHONE-SIDES-FS: side-by-side panes, no drawer overlay */"""

CSS_NEW_PORT = CSS_NEW.replace(
    ".collapse-cards-btn{flex-shrink:0;box-sizing:border-box;min-height:2.25rem;background:transparent;border:1px solid var(--border);color:var(--text-muted);border-radius:4px;padding:0 .625rem;font-size:.875rem;cursor:pointer;touch-action:manipulation;white-space:nowrap}",
    "/* fix-PHONE-SIDES-FS: side-by-side panes, no drawer overlay */",
)


def patch(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    n = path.name
    if MARK in text:
        print("skip", n)
        return
    text = sub(text, CSS_OLD, CSS_NEW, f"{n}: css", optional=True)
    if MARK not in text:
        text = sub(text, CSS_OLD_PORT, CSS_NEW_PORT, f"{n}: css-port")
    if MARK not in text:
        raise SystemExit(f"{n}: mark missing")
    raw = text.encode("utf-8")
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_bytes(raw)
    out = tmp.read_bytes().decode("utf-8")
    if not out.strip().endswith("</html>"):
        tmp.unlink()
        raise SystemExit(f"{n}: truncated")
    if len(raw) < 100000:
        tmp.unlink()
        raise SystemExit(f"{n}: size too small {len(raw)}")
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
