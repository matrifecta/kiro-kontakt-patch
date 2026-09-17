#!/usr/bin/env python3
"""Bring desktop menu progress onto phone without a 3-pane Sides layout.

Mobile only: restore FS expand/collapse, stack Middle menus, overlay FS.
Desktop CSS/JS paths stay as they are. Does not commit.
"""
from pathlib import Path

ROOT = Path("/home/phnx/kiro-kontakt-patch")
FILES = [
    ROOT / "public/catalogs/DS-CATALOG.html",
    ROOT / "public/catalogs/KONTAKT-CATALOG.html",
    ROOT / "public/catalogs/DS-CATALOG-portable.html",
    ROOT / "public/catalogs/KONTAKT-CATALOG-portable.html",
    ROOT / "kiro/specs/kontakt-workspace-drive-dirty-fix/artifacts/build-ds-catalog-html.sh",
    ROOT / "kiro/specs/kontakt-workspace-drive-dirty-fix/artifacts/build-kontakt-catalog-html.sh",
]

CSS_MARK = "/* fix-MOBILE-SIDES: single-column Sides on mobile */"
CSS_ADD = """
/* fix-MOBILE-PROGRESS: desktop chrome that fits a phone — never 3 panes */
@media(max-width:899px),(hover:none) and (pointer:coarse){
  body .search-strip-fs,body .kw-fs-btn,
  body.display-sides .search-strip-fs,body.display-sides .kw-fs-btn,
  body.display-sides:not(.search-chrome-collapsed) .search-strip-fs,
  body.catalog-portable .search-strip-fs{display:inline-flex!important}
  body.kw-fs-open .kw-fs-btn,body.ac-fs-open .search-ac-shell.ac-fs>.search-strip .search-strip-fs{display:none!important}
  body.ac-fs-open .ac-fs-back,body.kw-fs-open .kw-fs-back{display:inline-flex!important}
  body .ac-companion-btn,body .kw-companion-btn,body .fs-stripe-wrap,body .fs-mode-nav,
  body.ac-fs-open .kw-companion-btn,body.kw-fs-open .ac-companion-btn,
  body.ac-fs-open .fs-stripe-wrap,body.kw-fs-open .fs-stripe-wrap{display:none!important}
  body.display-sides #searchSplit,body.display-sides #dualFsSep,body.dual-fs-open #dualFsSep{display:none!important}
  body.display-sides.display-middle{
    display:flex!important;flex-direction:column!important;
    grid-template-columns:none!important;grid-template-rows:none!important
  }
  body.display-sides.display-middle .catalog-header{flex:0 0 auto;position:sticky;top:0;z-index:320}
  body.display-sides.display-middle #searchChrome{
    flex:0 1 auto;width:100%!important;max-height:min(32dvh,15rem)!important;
    border-right:0!important;border-bottom:1px solid var(--border)!important
  }
  body.display-sides.display-middle #filterWrap,
  body.display-sides.display-middle.kw-open #filterWrap{
    position:relative!important;inset:auto!important;right:auto!important;top:auto!important;bottom:auto!important;
    transform:none!important;width:100%!important;max-width:100%!important;
    max-height:min(32dvh,15rem)!important;flex:0 1 auto;z-index:6!important;
    box-shadow:none!important;border-left:0!important;border-top:1px solid var(--border)!important
  }
  body.display-sides.display-middle.kw-chrome-collapsed #filterWrap,
  body.display-sides.display-middle:not(.kw-open) #filterWrap{display:none!important}
  body.display-sides.display-middle.search-chrome-collapsed #searchChrome{display:none!important}
  body.display-sides.display-middle #catalogMain{flex:1 1 auto;min-height:0;width:100%!important}
  body.kw-fs-open:not(.dual-fs-open) #filterWrap,
  body.display-sides.kw-fs-open:not(.dual-fs-open) #filterWrap,
  body.display-sides.display-middle.kw-fs-open:not(.dual-fs-open) #filterWrap{
    position:fixed!important;top:var(--cat-header-h,3.5rem)!important;left:0!important;right:0!important;bottom:0!important;
    width:100%!important;max-width:none!important;max-height:none!important;height:auto!important;
    transform:none!important;z-index:340!important;box-shadow:none!important;overflow:auto!important
  }
  body.ac-fs-open:not(.dual-fs-open) #acShell.ac-fs,
  body.display-sides.ac-fs-open:not(.dual-fs-open) #acShell.ac-fs{
    position:fixed!important;top:var(--cat-header-h,3.5rem)!important;left:0!important;right:0!important;bottom:0!important;
    width:100%!important;max-width:none!important;height:auto!important;max-height:none!important;z-index:340!important
  }
}
@media(max-width:899px) and (orientation:portrait),(hover:none) and (pointer:coarse) and (orientation:portrait){
  body.dual-fs-open #acShell.ac-fs,body.display-sides.dual-fs-open #acShell.ac-fs{
    position:fixed!important;top:var(--cat-header-h,3.5rem)!important;left:0!important;right:0!important;bottom:50%!important;
    width:100%!important;height:auto!important;max-height:none!important;z-index:340!important
  }
  body.dual-fs-open #filterWrap,body.display-sides.dual-fs-open #filterWrap{
    position:fixed!important;top:50%!important;left:0!important;right:0!important;bottom:0!important;
    width:100%!important;max-width:none!important;transform:none!important;z-index:341!important;box-shadow:none!important
  }
}
@media(max-width:899px) and (orientation:landscape),(hover:none) and (pointer:coarse) and (orientation:landscape){
  body.dual-fs-open #acShell.ac-fs,body.display-sides.dual-fs-open #acShell.ac-fs{
    position:fixed!important;top:var(--cat-header-h,3.5rem)!important;left:0!important;right:50%!important;bottom:0!important;
    width:auto!important;height:auto!important;z-index:340!important
  }
  body.dual-fs-open #filterWrap,body.display-sides.dual-fs-open #filterWrap{
    position:fixed!important;top:var(--cat-header-h,3.5rem)!important;left:50%!important;right:0!important;bottom:0!important;
    width:auto!important;max-width:none!important;transform:none!important;z-index:341!important;box-shadow:none!important
  }
}
"""

TOGGLE_OLD = """window.toggleKwFullscreen=function(){
  if(typeof expandKwMenu==='function')expandKwMenu();
};
window.toggleAcFullscreen=function(){
  if(typeof expandSearchMenu==='function')expandSearchMenu();
};
"""

TOGGLE_NEW = """window.toggleKwFullscreen=function(){
  if(typeof isPhoneViewport==='function'&&isPhoneViewport()){
    if(typeof setKwFullscreen==='function')setKwFullscreen(!kwFsWanted);
    return;
  }
  if(typeof expandKwMenu==='function')expandKwMenu();
};
window.toggleAcFullscreen=function(){
  if(typeof isPhoneViewport==='function'&&isPhoneViewport()){
    if(typeof setAcFullscreen==='function')setAcFullscreen(!(typeof acFsWanted!=='undefined'&&acFsWanted));
    return;
  }
  if(typeof expandSearchMenu==='function')expandSearchMenu();
};
"""

DUAL_OLD = """  if(!isDualFs()||document.body.classList.contains('display-sides')){
    document.documentElement.style.removeProperty('--dual-fs-lw');
    if(sep&&!document.body.classList.contains('display-sides'))sep.removeAttribute('style');
    syncNarrowPanels();
    return;
  }
"""

DUAL_NEW = """  if(!isDualFs()||(document.body.classList.contains('display-sides')&&!(typeof isPhoneViewport==='function'&&isPhoneViewport()))){
    document.documentElement.style.removeProperty('--dual-fs-lw');
    if(sep&&!document.body.classList.contains('display-sides'))sep.removeAttribute('style');
    syncNarrowPanels();
    return;
  }
  if(typeof isPhoneViewport==='function'&&isPhoneViewport()){
    if(sep)sep.style.display='none';
    syncNarrowPanels();
    return;
  }
"""

PLACE_OLD = """  if(acFullscreen()){
    sh.classList.add('ac-fixed','ac-fs');
    document.body.classList.add('ac-fs-open');
    sh.style.top=Math.round(box.top)+'px';
    sh.style.left=Math.round(box.left)+'px';
    sh.style.right='auto';
    sh.style.bottom='auto';
    sh.style.width=Math.round(box.width)+'px';
    sh.style.height=Math.round(box.height)+'px';
    sh.style.maxWidth='none';
    sh.style.maxHeight=Math.round(box.height)+'px';
    syncAcWidthBtn();
    return;
  }
"""

PLACE_NEW = """  if(acFullscreen()){
    sh.classList.add('ac-fixed','ac-fs');
    document.body.classList.add('ac-fs-open');
    var top=box.top,left=box.left,width=box.width,height=box.height;
    if(typeof isPhoneViewport==='function'&&isPhoneViewport()){
      var hdr=document.querySelector('.catalog-header');
      if(hdr)top=Math.max(top,hdr.getBoundingClientRect().bottom);
      height=Math.max(80,box.bottom-top);
    }
    sh.style.top=Math.round(top)+'px';
    sh.style.left=Math.round(left)+'px';
    sh.style.right='auto';
    sh.style.bottom='auto';
    sh.style.width=Math.round(width)+'px';
    sh.style.height=Math.round(height)+'px';
    sh.style.maxWidth='none';
    sh.style.maxHeight=Math.round(height)+'px';
    syncAcWidthBtn();
    return;
  }
"""


def sub(text, old, new, label, path):
    if new in text and old not in text:
        print(f"  skip {path.name} {label}")
        return text
    n = text.count(old)
    if n != 1:
        raise SystemExit(f"{path.name}: {label} count={n} expected 1")
    return text.replace(old, new, 1)


def main():
    for path in FILES:
        t = path.read_text(encoding="utf-8")
        if CSS_ADD.strip() in t:
            print(f"  skip {path.name} css")
        else:
            if CSS_MARK not in t:
                raise SystemExit(f"{path.name}: missing {CSS_MARK}")
            # insert after the first mobile-sides media block closer following the mark
            i = t.find(CSS_MARK)
            close = t.find("}\n/* fix-PORTRAIT-SIDES", i)
            if close < 0:
                close = t.find("}\n/* fix-PORTRAIT-SIDES:", i)
            if close < 0:
                raise SystemExit(f"{path.name}: cannot find end of mobile-sides block")
            close = t.find("\n", close) + 1
            t = t[:close] + CSS_ADD + t[close:]
            print(f"  css {path.name}")
        t = sub(t, TOGGLE_OLD, TOGGLE_NEW, "toggle-fs", path)
        t = sub(t, DUAL_OLD, DUAL_NEW, "dual-layout", path)
        t = sub(t, PLACE_OLD, PLACE_NEW, "place-ac", path)
        path.write_text(t, encoding="utf-8")
        print("ok", path.name)


if __name__ == "__main__":
    main()
