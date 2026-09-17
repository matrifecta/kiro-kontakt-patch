#!/usr/bin/env python3
"""Portable: Middle one-menu; keep FS AC list; Flip is spatial L/R only."""
from pathlib import Path

ROOT = Path("/home/phnx/kiro-kontakt-patch")
FILES = [
    ROOT / "public/catalogs/DS-CATALOG-portable.html",
    ROOT / "public/catalogs/KONTAKT-CATALOG-portable.html",
]

CSS_MARK = "/* fix-PORTABLE-MIDDLE-ONE:"
CSS_ADD = r"""
/* fix-PORTABLE-MIDDLE-ONE: Middle one menu; Flip spatial; keep FS AC */
@media all{
  body.catalog-portable.display-sides.display-middle:not(.search-chrome-collapsed) #filterWrap,
  body.catalog-portable.display-sides.display-middle:not(.search-chrome-collapsed).kw-open #filterWrap{
    display:none!important
  }
  body.catalog-portable.display-sides.display-middle.search-chrome-collapsed.kw-open:not(.kw-chrome-collapsed) #searchChrome{
    display:none!important
  }
  body.catalog-portable.display-sides.display-middle:not(.search-chrome-collapsed) #searchChrome{
    flex:0 1 auto!important;max-height:min(44dvh,22rem)!important;min-height:8rem!important
  }
  body.catalog-portable.display-sides.display-middle.search-chrome-collapsed.kw-open:not(.kw-chrome-collapsed) #filterWrap{
    display:flex!important;flex:0 1 auto!important;max-height:min(44dvh,22rem)!important;min-height:8rem!important
  }
}
"""

HDR_SYNC_OLD = """  var wrap=document.getElementById('hdrMenuBtns');
  var sb=document.getElementById('hdrSearchBtn');
  var kb=document.getElementById('hdrKwBtn');
  var flip=!!(window.CATALOG_PORTABLE&&document.body.classList.contains('sides-portrait-flip'));
  if(wrap&&sb&&kb){
    if(flip){if(wrap.firstElementChild!==kb)wrap.insertBefore(kb,sb);}
    else if(wrap.firstElementChild!==sb)wrap.insertBefore(sb,kb);
  }
  if(sb){
    sb.classList.toggle('is-on',searchOn);
    sb.setAttribute('aria-pressed',searchOn?'true':'false');
    sb.title=(searchOn?'Hide Search':'Show Search')+(flip?' (right)':' (left)');
    sb.setAttribute('aria-label','Search, '+(flip?'right':'left'));
  }
  if(kb){
    kb.classList.toggle('is-on',kwOn);
    kb.setAttribute('aria-pressed',kwOn?'true':'false');
    kb.title=(kwOn?'Hide Keywords':'Show Keywords')+(flip?' (left)':' (right)');
    kb.setAttribute('aria-label','Keywords, '+(flip?'left':'right'));
  }"""

HDR_SYNC_NEW = """  var wrap=document.getElementById('hdrMenuBtns');
  var sb=document.getElementById('hdrSearchBtn');
  var kb=document.getElementById('hdrKwBtn');
  if(wrap&&sb&&kb&&wrap.firstElementChild!==sb)wrap.insertBefore(sb,kb);
  if(sb){
    sb.classList.toggle('is-on',searchOn);
    sb.setAttribute('aria-pressed',searchOn?'true':'false');
    sb.title=searchOn?'Hide Search':'Show Search';
    sb.setAttribute('aria-label','Search');
  }
  if(kb){
    kb.classList.toggle('is-on',kwOn);
    kb.setAttribute('aria-pressed',kwOn?'true':'false');
    kb.title=kwOn?'Hide Keywords':'Show Keywords';
    kb.setAttribute('aria-label','Keywords');
  }"""

HDR_SEARCH_TAIL_OLD = """  if(typeof toggleSearchChrome==='function')toggleSearchChrome();
  else if(document.body.classList.contains('search-chrome-collapsed')){if(typeof expandSearchMenu==='function')expandSearchMenu();}
  else if(typeof collapseSearchMenu==='function')collapseSearchMenu();
  if(typeof placePortableHandles==='function')placePortableHandles();
  syncHdrMenuBtns();
}"""

HDR_SEARCH_TAIL_NEW = """  if(typeof toggleSearchChrome==='function')toggleSearchChrome();
  else if(document.body.classList.contains('search-chrome-collapsed')){if(typeof expandSearchMenu==='function')expandSearchMenu();}
  else if(typeof collapseSearchMenu==='function')collapseSearchMenu();
  if(window.CATALOG_PORTABLE&&document.body.classList.contains('display-middle')&&!document.body.classList.contains('search-chrome-collapsed')&&typeof portableCoerceMiddleMenu==='function')portableCoerceMiddleMenu('search');
  if(typeof placePortableHandles==='function')placePortableHandles();
  syncHdrMenuBtns();
}"""

HDR_KW_TAIL_OLD = """  if(document.body.classList.contains('display-sides')){
    if(typeof toggleKwChrome==='function')toggleKwChrome();
  }else if(typeof toggleFilter==='function'){
    var w=document.getElementById('filterWrap');
    if(document.body.classList.contains('kw-chrome-collapsed')&&typeof expandKwMenu==='function')expandKwMenu();
    else toggleFilter();
  }
  if(typeof placePortableHandles==='function')placePortableHandles();
  syncHdrMenuBtns();
}"""

HDR_KW_TAIL_NEW = """  if(document.body.classList.contains('display-sides')){
    if(typeof toggleKwChrome==='function')toggleKwChrome();
  }else if(typeof toggleFilter==='function'){
    var w=document.getElementById('filterWrap');
    if(document.body.classList.contains('kw-chrome-collapsed')&&typeof expandKwMenu==='function')expandKwMenu();
    else toggleFilter();
  }
  if(window.CATALOG_PORTABLE&&document.body.classList.contains('display-middle')){
    var fwNow=document.getElementById('filterWrap');
    var kwNow=!document.body.classList.contains('kw-chrome-collapsed')&&!!(fwNow&&fwNow.classList.contains('open')&&document.body.classList.contains('kw-open'));
    if(kwNow&&typeof portableCoerceMiddleMenu==='function')portableCoerceMiddleMenu('keywords');
  }
  if(typeof placePortableHandles==='function')placePortableHandles();
  syncHdrMenuBtns();
}"""

MIDDLE_OLD = """  if(currentDisplay==='middle'){
    document.body.classList.add('display-middle');
    var fwMid=document.getElementById('filterWrap');
    if(fwMid){fwMid.classList.add('open');document.body.classList.add('kw-open');}
    document.body.classList.remove('kw-chrome-collapsed');
  }"""

MIDDLE_NEW = """  if(currentDisplay==='middle'){
    document.body.classList.add('display-middle');
    if(window.CATALOG_PORTABLE&&typeof portableCoerceMiddleMenu==='function'){
      var midBoth=!document.body.classList.contains('search-chrome-collapsed')&&!document.body.classList.contains('kw-chrome-collapsed')&&document.body.classList.contains('kw-open');
      if(midBoth)portableCoerceMiddleMenu(typeof portableMiddleLast==='string'&&portableMiddleLast?portableMiddleLast:'search');
    }
  }"""

HIDE_AC_OLD = """function hideSearchAc(){
  acFsWanted=false;
  parkSearchStrip();
  syncAcFsBtn();
  var ac=acListEl();
  if(ac){ac.classList.remove('open');ac.innerHTML='';}
  var si=document.getElementById('searchInput');
  if(si)si.blur();
  clearAcShellPos(acShell());
  if(window.syncSearchSplit)window.syncSearchSplit();
}"""

HIDE_AC_NEW = """function hideSearchAc(){
  if(typeof portableKeepAcOpen==='function'&&portableKeepAcOpen()){
    if(typeof portableEnsureScrollMenus==='function')portableEnsureScrollMenus();
    return;
  }
  acFsWanted=false;
  parkSearchStrip();
  syncAcFsBtn();
  var ac=acListEl();
  if(ac){ac.classList.remove('open');ac.innerHTML='';}
  var si=document.getElementById('searchInput');
  if(si)si.blur();
  clearAcShellPos(acShell());
  if(window.syncSearchSplit)window.syncSearchSplit();
}"""

CLICK_OUT_OLD = """    if(!acOpen())return;
    if(e.target.closest&&e.target.closest('#acShell,#searchInput,.search-strip,.search-chrome,#filterWrap,.filter-toggle'))return;
    hideSearchAc();"""

CLICK_OUT_NEW = """    if(!acOpen())return;
    if(typeof portableKeepAcOpen==='function'&&portableKeepAcOpen())return;
    if(e.target.closest&&e.target.closest('#acShell,#searchInput,.search-strip,.search-chrome,#filterWrap,.filter-toggle'))return;
    hideSearchAc();"""

FOCUS_OUT_OLD = """    if(window._acItemPointer)return;
    if(acL){acL.classList.remove('open');acL.innerHTML='';}
    if(window.syncSearchSplit)window.syncSearchSplit();"""

FOCUS_OUT_NEW = """    if(window._acItemPointer)return;
    if(typeof portableKeepAcOpen==='function'&&portableKeepAcOpen()){
      if(typeof portableEnsureScrollMenus==='function')portableEnsureScrollMenus();
      return;
    }
    if(acL){acL.classList.remove('open');acL.innerHTML='';}
    if(window.syncSearchSplit)window.syncSearchSplit();"""

HELPERS = r"""
var portableMiddleLast='search';
function portableKeepAcOpen(){
  if(!window.CATALOG_PORTABLE)return false;
  var b=document.body.classList;
  if(b.contains('search-chrome-collapsed'))return false;
  if(b.contains('ac-fs-open')&&!b.contains('kw-fs-open'))return true;
  if(b.contains('is-browser-fs')||document.documentElement.classList.contains('is-browser-fs'))return true;
  if(b.contains('display-sides')&&!b.contains('display-middle'))return true;
  return false;
}
function portableCoerceMiddleMenu(which){
  if(!window.CATALOG_PORTABLE||!document.body.classList.contains('display-middle'))return;
  if(which==='keywords'){
    portableMiddleLast='keywords';
    document.body.classList.add('search-chrome-collapsed','search-extras-collapsed');
    document.body.classList.remove('kw-chrome-collapsed');
    document.body.classList.add('kw-open');
    var fw=document.getElementById('filterWrap');
    if(fw)fw.classList.add('open');
  }else{
    portableMiddleLast='search';
    document.body.classList.remove('search-chrome-collapsed','search-extras-collapsed');
    document.body.classList.add('kw-chrome-collapsed');
    document.body.classList.remove('kw-open');
    var fw2=document.getElementById('filterWrap');
    if(fw2)fw2.classList.remove('open');
    if(typeof portableEnsureScrollMenus==='function')portableEnsureScrollMenus();
    try{if(typeof showAc==='function')showAc(((document.getElementById('searchInput')||{}).value||'').trim().toLowerCase(),{force:true});}catch(errM){}
  }
  if(typeof syncHdrMenuBtns==='function')syncHdrMenuBtns();
  if(typeof placePortableHandles==='function')placePortableHandles();
  // #region agent log
  if(typeof dbgPortableJumpGap==='function')dbgPortableJumpGap('middle-one-'+which);
  if(typeof dbgMobileUi==='function')dbgMobileUi('middle-one',{hyp:'H-MID',which:which});
  // #endregion
}
window.portableKeepAcOpen=portableKeepAcOpen;
window.portableCoerceMiddleMenu=portableCoerceMiddleMenu;
"""

FLIP_COMMENT_OLD = "/* fix-PORTABLE-FLIP-MENUS: Search/Keywords swap when both open */"
FLIP_COMMENT_NEW = "/* fix-PORTABLE-FLIP-MENUS: spatial L/R pane swap; Search/Keywords identity stays */"


def sub1(text, old, new, label, path):
    n = text.count(old)
    if n != 1:
        raise SystemExit(f"{path.name}: {label} count={n}")
    return text.replace(old, new, 1)


def main():
    for path in FILES:
        text = path.read_text(encoding="utf-8")
        if CSS_MARK not in text:
            if "</style></head>" not in text:
                raise SystemExit(f"no style end in {path}")
            text = text.replace("</style></head>", CSS_ADD + "\n</style></head>", 1)
            print("  css", path.name)
        text = sub1(text, HDR_SYNC_OLD, HDR_SYNC_NEW, "hdr-sync", path)
        text = sub1(text, HDR_SEARCH_TAIL_OLD, HDR_SEARCH_TAIL_NEW, "hdr-search", path)
        text = sub1(text, HDR_KW_TAIL_OLD, HDR_KW_TAIL_NEW, "hdr-kw", path)
        text = sub1(text, MIDDLE_OLD, MIDDLE_NEW, "middle-boot", path)
        text = sub1(text, HIDE_AC_OLD, HIDE_AC_NEW, "hide-ac", path)
        text = sub1(text, CLICK_OUT_OLD, CLICK_OUT_NEW, "click-out", path)
        text = sub1(text, FOCUS_OUT_OLD, FOCUS_OUT_NEW, "focus-out", path)
        if "function portableKeepAcOpen(" not in text:
            text = sub1(text, "var portableMenuFsPrev=null;", HELPERS + "var portableMenuFsPrev=null;", "helpers", path)
        if FLIP_COMMENT_OLD in text:
            text = text.replace(FLIP_COMMENT_OLD, FLIP_COMMENT_NEW, 1)
        end_old = """    if(typeof dbgPortableJumpGap==='function')dbgPortableJumpGap('setDisplayMode');
  }
}"""
        end_new = """    if(typeof dbgPortableJumpGap==='function')dbgPortableJumpGap('setDisplayMode');
    if(document.body.classList.contains('display-middle')&&typeof portableCoerceMiddleMenu==='function'){
      var midBothEnd=!document.body.classList.contains('search-chrome-collapsed')&&!document.body.classList.contains('kw-chrome-collapsed')&&document.body.classList.contains('kw-open');
      if(midBothEnd)portableCoerceMiddleMenu(portableMiddleLast||'search');
    }
  }
}"""
        text = sub1(text, end_old, end_new, "setDisplay-end", path)
        # keep AC after portable FS enter
        if "if(typeof portableKeepAcOpen==='function'&&portableKeepAcOpen())portableEnsureScrollMenus();" not in text:
            text = text.replace(
                "if(typeof dbgPortableJumpGap==='function')dbgPortableJumpGap('menu-fs-'+which);",
                "if(typeof portableEnsureScrollMenus==='function')portableEnsureScrollMenus();\n  if(typeof dbgPortableJumpGap==='function')dbgPortableJumpGap('menu-fs-'+which);",
                1,
            )
        path.write_text(text, encoding="utf-8")
        print("ok", path.name)


if __name__ == "__main__":
    main()
