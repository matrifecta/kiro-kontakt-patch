#!/usr/bin/env python3
"""Portable portrait: split Kontakt/DS and Lib around the top-center notch."""
from pathlib import Path

ROOT = Path("/home/phnx/kiro-kontakt-patch/public/catalogs")
FILES = [
    ROOT / "KONTAKT-CATALOG-portable.html",
    ROOT / "DS-CATALOG-portable.html",
]

CSS_OLD = """@media(orientation:portrait){
  body.catalog-portable .hdr-cluster{grid-column:1/-1!important}
  body.catalog-portable .catalog-header{grid-template-rows:auto auto auto!important}
  body.catalog-portable .catalog-header>#hdrMorePop{grid-row:3!important}
}
"""

CSS_NEW = CSS_OLD + """
/* fix-PORTABLE-TITLE-NOTCH: split name around portrait Dynamic Island */
@media(orientation:portrait){
  body.catalog-portable .catalog-header h1#top{
    display:grid!important;grid-template-columns:minmax(0,1fr) minmax(0,1fr)!important;
    align-items:center;column-gap:0;width:100%!important;max-width:none!important;
    overflow:visible!important;text-overflow:clip!important;white-space:nowrap
  }
  body.catalog-portable .catalog-header h1#top .hdr-title-lead{
    grid-column:1;justify-self:center;text-align:center;min-width:0
  }
  body.catalog-portable .catalog-header h1#top .hdr-title-tail{
    grid-column:2;justify-self:center;text-align:center;min-width:0
  }
}
@media(orientation:landscape){
  body.catalog-portable .catalog-header h1#top{
    display:flex!important;align-items:center;gap:.35em;flex-wrap:nowrap
  }
}
"""

H1 = {
    "KONTAKT-CATALOG-portable.html": (
        '<h1 id="top">Kontakt Lib</h1>',
        '<h1 id="top"><span class="hdr-title-lead">Kontakt</span><span class="hdr-title-tail">Lib</span></h1>',
    ),
    "DS-CATALOG-portable.html": (
        '<h1 id="top">DS Lib</h1>',
        '<h1 id="top"><span class="hdr-title-lead">DS</span><span class="hdr-title-tail">Lib</span></h1>',
    ),
}

LOG_OLD = "h1:(document.querySelector('h1#top')||{}).textContent||'',title:document.title"
LOG_NEW = "h1:(document.querySelector('h1#top')||{}).textContent||'',title:document.title,lead:((function(){var el=document.querySelector('.hdr-title-lead');if(!el)return null;var r=el.getBoundingClientRect();return {t:el.textContent,x:Math.round(r.left),cx:Math.round(r.left+r.width/2),w:Math.round(r.width)};})()),tail:((function(){var el=document.querySelector('.hdr-title-tail');if(!el)return null;var r=el.getBoundingClientRect();return {t:el.textContent,x:Math.round(r.left),cx:Math.round(r.left+r.width/2),w:Math.round(r.width)};})()),mid:Math.round(window.innerWidth/2)"


def patch(path: Path) -> None:
    t = path.read_text(encoding="utf-8")
    n = path.name
    old_h1, new_h1 = H1[n]
    if new_h1 not in t:
        if t.count(old_h1) != 1:
            raise SystemExit(f"{n}: h1 count {t.count(old_h1)}")
        t = t.replace(old_h1, new_h1, 1)
    if "fix-PORTABLE-TITLE-NOTCH" not in t:
        if t.count(CSS_OLD) != 1:
            raise SystemExit(f"{n}: css mark count {t.count(CSS_OLD)}")
        t = t.replace(CSS_OLD, CSS_NEW, 1)
    if ".hdr-title-lead" not in t[t.find("applyIndexFillDocStyles") : t.find("applyIndexFillDocStyles") + 2500]:
        if t.count(LOG_OLD) != 1:
            raise SystemExit(f"{n}: log mark count {t.count(LOG_OLD)}")
        t = t.replace(LOG_OLD, LOG_NEW, 1)
    out = t.encode("utf-8")
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_bytes(out)
    if not tmp.read_bytes().decode("utf-8").strip().endswith("</html>"):
        tmp.unlink()
        raise SystemExit(f"{n}: truncated")
    tmp.replace(path)
    print("OK", n, "bytes", len(out), "notch", "fix-PORTABLE-TITLE-NOTCH" in t)


def main() -> None:
    for p in FILES:
        patch(p)


if __name__ == "__main__":
    main()
