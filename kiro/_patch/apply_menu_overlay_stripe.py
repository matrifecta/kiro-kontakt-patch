#!/usr/bin/env python3
"""Hide leftover content hover-scroll when a menu covers the content window."""
from pathlib import Path

ROOT = Path("/home/phnx/kiro-kontakt-patch/public/catalogs")
FILES = [ROOT / "KONTAKT-CATALOG-portable.html", ROOT / "DS-CATALOG-portable.html"]

CSS_OLD = """  body.catalog-portable #catalogMainHoverStripe.hover-scroll-fixed:not([hidden]),
  body.catalog-portable.has-hover-overflow-content #catalogMainHoverStripe.hover-scroll-fixed:not([hidden]){
    display:block!important;pointer-events:auto!important;z-index:40!important
  }
  body.catalog-portable #catalogMain>.hover-scroll-stripe{display:none!important}"""

CSS_NEW = """  body.catalog-portable #catalogMainHoverStripe.hover-scroll-fixed:not([hidden]),
  body.catalog-portable.has-hover-overflow-content #catalogMainHoverStripe.hover-scroll-fixed:not([hidden]){
    display:block!important;pointer-events:auto!important;z-index:40!important
  }
  /* fix-MENU-OVERLAY-STRIPE-v1: leftover content thumb must not sit on Search/Keywords */
  body.catalog-portable:not(.content-window-on) #catalogMainHoverStripe.hover-scroll-fixed,
  body.catalog-portable.ac-fs-open #catalogMainHoverStripe.hover-scroll-fixed,
  body.catalog-portable.kw-fs-open #catalogMainHoverStripe.hover-scroll-fixed,
  body.catalog-portable.dual-fs-open #catalogMainHoverStripe.hover-scroll-fixed,
  body.catalog-portable.display-fs #catalogMainHoverStripe.hover-scroll-fixed{
    display:none!important;pointer-events:none!important
  }
  body.catalog-portable.display-sides.ac-fs-open:not(.dual-fs-open):not(.kw-fs-open),
  body.catalog-portable.display-sides.kw-fs-open:not(.dual-fs-open):not(.ac-fs-open){
    grid-template-columns:minmax(0,1fr)!important
  }
  body.catalog-portable.display-sides.ac-fs-open:not(.dual-fs-open) #catalogMain,
  body.catalog-portable.display-sides.kw-fs-open:not(.dual-fs-open) #catalogMain{
    display:none!important
  }
  body.catalog-portable #catalogMain>.hover-scroll-stripe{display:none!important}"""

SHOW_OLD = """      var sc=n.sc,max=Math.max(0,sc.scrollHeight-sc.clientHeight);
      var show=max>8;
      n.h.classList.toggle('has-hover-overflow',show);
      if(mark==='content')document.body.classList.toggle('has-hover-overflow-content',show);
      n.st.hidden=!show;"""

SHOW_NEW = """      var sc=n.sc,max=Math.max(0,sc.scrollHeight-sc.clientHeight);
      var show=max>8;
      if(mark==='content'&&window.CATALOG_PORTABLE){
        var onScreen=typeof catalogContentWindowOnScreen==='function'?catalogContentWindowOnScreen():true;
        var mrGate=sc.getBoundingClientRect();
        if(!onScreen||mrGate.width<24||mrGate.height<48)show=false;
      }
      n.h.classList.toggle('has-hover-overflow',show);
      if(mark==='content')document.body.classList.toggle('has-hover-overflow-content',show);
      n.st.hidden=!show;"""

DOCK_OLD = """    if(main){
      main.style.setProperty('display','flex','important');
      main.style.setProperty('flex-direction','column','important');"""

DOCK_NEW = """    var menuFs=!!(window.CATALOG_PORTABLE&&(document.body.classList.contains('ac-fs-open')||document.body.classList.contains('kw-fs-open')||document.body.classList.contains('dual-fs-open')||document.body.classList.contains('display-fs')));
    if(main&&menuFs){
      main.style.setProperty('display','none','important');
    }else if(main){
      main.style.setProperty('display','flex','important');
      main.style.setProperty('flex-direction','column','important');"""

LOG_K = """data:{mark:mark,show:show,gutter:gutterHs,thW:Math.round(thHs.width),thH:Math.round(thHs.height),thRight:Math.round(thHs.right),stFixed:n.st.classList.contains('hover-scroll-fixed'),stHidden:!!n.st.hidden,parent:(n.st.parentNode&&(n.st.parentNode.id||n.st.parentNode.nodeName))||'',sbw:getComputedStyle(sc).scrollbarWidth}"""

LOG_K_NEW = """data:{mark:mark,show:show,gutter:gutterHs,thW:Math.round(thHs.width),thH:Math.round(thHs.height),thRight:Math.round(thHs.right),stFixed:n.st.classList.contains('hover-scroll-fixed'),stHidden:!!n.st.hidden,parent:(n.st.parentNode&&(n.st.parentNode.id||n.st.parentNode.nodeName))||'',sbw:getComputedStyle(sc).scrollbarWidth,orient:innerWidth>=innerHeight?'land':'port',contentOn:document.body.classList.contains('content-window-on'),acFs:document.body.classList.contains('ac-fs-open'),kwFs:document.body.classList.contains('kw-fs-open'),mainW:Math.round((document.getElementById('catalogMain')||sc).getBoundingClientRect().width),stX:Math.round(n.st.getBoundingClientRect().x),stD:getComputedStyle(n.st).display,run:'post-fix'}"""


def patch(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    orig = text
    for old, new, label in (
        (CSS_OLD, CSS_NEW, "css"),
        (SHOW_OLD, SHOW_NEW, "show"),
        (DOCK_OLD, DOCK_NEW, "dock"),
        (LOG_K, LOG_K_NEW, "log"),
    ):
        n = text.count(old)
        if n != 1:
            raise SystemExit(f"{path.name}: {label} matches {n}, expected 1")
        text = text.replace(old, new, 1)
    if not text.rstrip().endswith("</html>"):
        raise SystemExit(f"{path.name}: truncated, missing </html>")
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    out = tmp.read_text(encoding="utf-8")
    if not out.rstrip().endswith("</html>"):
        tmp.unlink()
        raise SystemExit(f"{path.name}: temp truncated")
    if len(out) < len(orig):
        tmp.unlink()
        raise SystemExit(f"{path.name}: shrank {len(orig)} -> {len(out)}")
    tmp.replace(path)
    print(f"{path.name}: {len(orig)} -> {len(out)}")


def main() -> None:
    for f in FILES:
        patch(f)


if __name__ == "__main__":
    main()
