#!/usr/bin/env python3
"""Portable: no Full layout button; S+K dual; Sides menu ⛶ fills that menu."""
from pathlib import Path

ROOT = Path("/home/phnx/kiro-kontakt-patch")
FILES = [
    ROOT / "public/catalogs/DS-CATALOG-portable.html",
    ROOT / "public/catalogs/KONTAKT-CATALOG-portable.html",
]

CSS_MARK = "/* fix-PORTABLE-MENU-FS:"
CSS_ADD = r"""
/* fix-PORTABLE-MENU-FS: hide Full layout; Sides ⛶ fills one menu */
@media all{
  body.catalog-portable .display-btn[data-display="fs"]{display:none!important}
  body.catalog-portable.display-sides #searchStrip .search-strip-fs,
  body.catalog-portable.display-sides #kwStripFs,
  body.catalog-portable.display-sides .kw-fs-btn{
    display:inline-flex!important;flex:0 0 auto;order:2;position:relative;z-index:3
  }
  body.catalog-portable.display-sides.ac-fs-open:not(.kw-fs-open) .search-strip-fs,
  body.catalog-portable.display-sides.kw-fs-open:not(.ac-fs-open) .kw-fs-btn,
  body.catalog-portable.display-sides.kw-fs-open:not(.ac-fs-open) #kwStripFs{
    display:inline-flex!important
  }
  body.catalog-portable.display-sides.ac-fs-open:not(.kw-fs-open) .ac-fs-back,
  body.catalog-portable.display-sides.kw-fs-open:not(.ac-fs-open) .kw-fs-back{
    display:inline-flex!important
  }
  body.catalog-portable.display-sides.ac-fs-open:not(.kw-fs-open),
  body.catalog-portable.display-sides.ac-fs-open:not(.kw-fs-open):not(.display-middle).kw-open:not(.kw-chrome-collapsed):not(.search-chrome-collapsed),
  body.catalog-portable.display-sides.kw-fs-open:not(.ac-fs-open),
  body.catalog-portable.display-sides.kw-fs-open:not(.ac-fs-open):not(.display-middle).kw-open:not(.kw-chrome-collapsed):not(.search-chrome-collapsed),
  body.catalog-portable.display-sides.kw-fs-open:not(.ac-fs-open):not(.display-middle).search-chrome-collapsed.kw-open:not(.kw-chrome-collapsed){
    grid-template-columns:minmax(0,1fr)!important;
    grid-template-rows:auto minmax(0,1fr)!important;
    display:grid!important
  }
  body.catalog-portable.display-sides.ac-fs-open:not(.kw-fs-open) #searchChrome,
  body.catalog-portable.display-sides.ac-fs-open:not(.kw-fs-open) #acShell,
  body.catalog-portable.display-sides.ac-fs-open:not(.kw-fs-open) #acShell.ac-fs{
    grid-column:1/-1!important;grid-row:2!important;
    display:flex!important;flex-direction:column!important;
    width:100%!important;max-width:none!important;height:auto!important;max-height:none!important;
    min-height:0!important;overflow:hidden!important;
    position:relative!important;inset:auto!important;left:0!important;right:0!important
  }
  body.catalog-portable.display-sides.ac-fs-open:not(.kw-fs-open) #acList,
  body.catalog-portable.display-sides.ac-fs-open:not(.kw-fs-open) #acList.open{
    flex:1 1 0%!important;min-height:0!important;max-height:none!important;
    overflow-x:hidden!important;overflow-y:auto!important
  }
  body.catalog-portable.display-sides.ac-fs-open:not(.kw-fs-open) #filterWrap,
  body.catalog-portable.display-sides.ac-fs-open:not(.kw-fs-open).kw-open #filterWrap,
  body.catalog-portable.display-sides.ac-fs-open:not(.kw-fs-open):not(.display-middle).kw-open:not(.kw-chrome-collapsed):not(.search-chrome-collapsed) #filterWrap,
  body.catalog-portable.display-sides.ac-fs-open:not(.kw-fs-open) #catalogMain,
  body.catalog-portable.display-sides.ac-fs-open:not(.kw-fs-open) #catalogJumpStack,
  body.catalog-portable.display-sides.ac-fs-open:not(.kw-fs-open) #searchSplit,
  body.catalog-portable.display-sides.ac-fs-open:not(.kw-fs-open) #dualFsSep{
    display:none!important
  }
  body.catalog-portable.display-sides.kw-fs-open:not(.ac-fs-open) #filterWrap,
  body.catalog-portable.display-sides.kw-fs-open:not(.ac-fs-open).kw-open #filterWrap,
  body.catalog-portable.display-sides.kw-fs-open:not(.ac-fs-open):not(.display-middle).kw-open:not(.kw-chrome-collapsed):not(.search-chrome-collapsed) #filterWrap,
  body.catalog-portable.display-sides.kw-fs-open:not(.ac-fs-open):not(.display-middle).search-chrome-collapsed.kw-open:not(.kw-chrome-collapsed) #filterWrap{
    grid-column:1/-1!important;grid-row:2!important;
    display:flex!important;flex-direction:column!important;
    position:relative!important;transform:none!important;inset:auto!important;
    width:100%!important;max-width:none!important;height:auto!important;
    max-height:none!important;min-height:0!important;overflow:hidden!important;
    left:0!important;right:0!important
  }
  body.catalog-portable.display-sides.kw-fs-open:not(.ac-fs-open) #filterWrap .filter-panel,
  body.catalog-portable.display-sides.kw-fs-open:not(.ac-fs-open) #kwbar{
    flex:1 1 auto!important;min-height:0!important;max-height:none!important;
    overflow-x:hidden!important;overflow-y:auto!important
  }
  body.catalog-portable.display-sides.kw-fs-open:not(.ac-fs-open) #searchChrome,
  body.catalog-portable.display-sides.kw-fs-open:not(.ac-fs-open) #catalogMain,
  body.catalog-portable.display-sides.kw-fs-open:not(.ac-fs-open) #catalogJumpStack,
  body.catalog-portable.display-sides.kw-fs-open:not(.ac-fs-open) #searchSplit,
  body.catalog-portable.display-sides.kw-fs-open:not(.ac-fs-open) #dualFsSep{
    display:none!important
  }
  body.catalog-portable.display-sides.display-middle.ac-fs-open:not(.kw-fs-open) #searchChrome{
    flex:1 1 0%!important;max-height:none!important;min-height:0!important;height:auto!important
  }
  body.catalog-portable.display-sides.display-middle.kw-fs-open:not(.ac-fs-open) #filterWrap{
    flex:1 1 0%!important;max-height:none!important;min-height:0!important;height:auto!important
  }
}
"""

FS_BTN_OLD = '  body.catalog-portable .display-btn[data-display="fs"]{display:inline-flex!important}'
FS_BTN_NEW = '  body.catalog-portable .display-btn[data-display="fs"]{display:none!important}'

HIDE_STRIP_OLD = "  body.catalog-portable:not(.display-fs) #searchStrip .search-strip-fs{display:none!important}"
HIDE_STRIP_NEW = "  body.catalog-portable:not(.display-sides):not(.display-fs) #searchStrip .search-strip-fs{display:none!important}"

PLACE_AC_OLD = """      if(document.body.classList.contains('display-fs')&&!document.body.classList.contains('search-chrome-collapsed')){
        shP.classList.add('ac-fs');
        document.body.classList.add('ac-fs-open');
      }else if(!document.body.classList.contains('display-fs')){
        shP.classList.remove('ac-fs');
      }"""

PLACE_AC_NEW = """      if(document.body.classList.contains('ac-fs-open')&&!document.body.classList.contains('kw-fs-open')){
        shP.classList.add('ac-fs');
      }else if(document.body.classList.contains('display-fs')&&!document.body.classList.contains('search-chrome-collapsed')){
        shP.classList.add('ac-fs');
        document.body.classList.add('ac-fs-open');
      }else if(!document.body.classList.contains('display-fs')&&!document.body.classList.contains('ac-fs-open')){
        shP.classList.remove('ac-fs');
      }"""

SET_START_OLD = """function setDisplayMode(mode,opts){
  opts=opts||{};
  if(mode!=='upper'&&mode!=='sides'&&mode!=='fs'&&mode!=='middle')mode='sides';"""

SET_START_NEW = """function setDisplayMode(mode,opts){
  opts=opts||{};
  var portableBoth=false;
  if(window.CATALOG_PORTABLE&&mode==='fs'){portableBoth=true;mode='sides';}
  if(mode!=='upper'&&mode!=='sides'&&mode!=='fs'&&mode!=='middle')mode='sides';"""

SET_END_OLD = """  if(window.CATALOG_PORTABLE){
    if(typeof portableEnsureScrollMenus==='function')portableEnsureScrollMenus();
    if(typeof syncPortableBrowserFs==='function')syncPortableBrowserFs();
    if(typeof placePortableHandles==='function')placePortableHandles();
    if(typeof dbgPortableScroll==='function')dbgPortableScroll('setDisplayMode',{hyp:'H-FS1'});
  }
}"""

SET_END_NEW = """  if(window.CATALOG_PORTABLE){
    if(portableBoth&&mode==='sides'){
      document.body.classList.remove('search-chrome-collapsed','kw-chrome-collapsed','ac-fs-open','kw-fs-open','dual-fs-open');
      var fwBoth=document.getElementById('filterWrap');
      if(fwBoth){fwBoth.classList.add('open');document.body.classList.add('kw-open');}
      if(typeof syncHdrMenuBtns==='function')syncHdrMenuBtns();
    }
    if(typeof portableEnsureScrollMenus==='function')portableEnsureScrollMenus();
    if(typeof syncPortableBrowserFs==='function')syncPortableBrowserFs();
    if(typeof placePortableHandles==='function')placePortableHandles();
    if(typeof dbgPortableScroll==='function')dbgPortableScroll('setDisplayMode',{hyp:'H-FS1'});
    if(typeof dbgPortableJumpGap==='function')dbgPortableJumpGap('setDisplayMode');
  }
}"""

TOGGLE_OLD = """window.phoneExitFs=function(){
  var back=(typeof lastNonFsDisplay==='string'&&(lastNonFsDisplay==='middle'||lastNonFsDisplay==='sides'))?lastNonFsDisplay:'';
  if(!back)back=(window.matchMedia&&window.matchMedia('(orientation:portrait)').matches)?'middle':'sides';
  if(typeof setDisplayMode==='function')setDisplayMode(back,{pick:true});
};
window.toggleKwFullscreen=function(){
  if(typeof isPhoneViewport==='function'&&isPhoneViewport()){
    if(typeof currentDisplay!=='undefined'&&currentDisplay==='fs'){window.phoneExitFs();return;}
    if(typeof setDisplayMode==='function')setDisplayMode('fs',{menu:'keywords',pick:true});
    return;
  }
  if(typeof expandKwMenu==='function')expandKwMenu();
};
window.toggleAcFullscreen=function(){
  if(typeof isPhoneViewport==='function'&&isPhoneViewport()){
    if(typeof currentDisplay!=='undefined'&&currentDisplay==='fs'){window.phoneExitFs();return;}
    if(typeof setDisplayMode==='function')setDisplayMode('fs',{menu:'search',pick:true});
    return;
  }
  if(typeof expandSearchMenu==='function')expandSearchMenu();
};"""

TOGGLE_NEW = r"""var portableMenuFsPrev=null;
function portableMenuFsOn(){
  var ac=document.body.classList.contains('ac-fs-open')&&!document.body.classList.contains('kw-fs-open');
  var kw=document.body.classList.contains('kw-fs-open')&&!document.body.classList.contains('ac-fs-open');
  return ac?'search':(kw?'keywords':'');
}
function portableSaveMenuCombo(){
  var fw=document.getElementById('filterWrap');
  return {
    searchOn:!document.body.classList.contains('search-chrome-collapsed'),
    kwOn:!document.body.classList.contains('kw-chrome-collapsed')&&!!(fw&&fw.classList.contains('open')&&document.body.classList.contains('kw-open'))
  };
}
function portableRestoreMenuCombo(prev){
  document.body.classList.remove('ac-fs-open','kw-fs-open','dual-fs-open');
  var sh=document.getElementById('acShell');
  if(sh)sh.classList.remove('ac-fs');
  if(typeof acFsWanted!=='undefined')acFsWanted=false;
  if(typeof kwFsWanted!=='undefined')kwFsWanted=false;
  prev=prev||{searchOn:true,kwOn:false};
  if(prev.searchOn)document.body.classList.remove('search-chrome-collapsed');
  else document.body.classList.add('search-chrome-collapsed');
  var fw=document.getElementById('filterWrap');
  if(prev.kwOn){
    document.body.classList.remove('kw-chrome-collapsed');
    document.body.classList.add('kw-open');
    if(fw)fw.classList.add('open');
  }else{
    document.body.classList.add('kw-chrome-collapsed');
    document.body.classList.remove('kw-open');
    if(fw)fw.classList.remove('open');
  }
}
function portableEnterMenuFs(which){
  if(!portableMenuFsOn())portableMenuFsPrev=portableSaveMenuCombo();
  document.body.classList.remove('dual-fs-open');
  if(which==='search'){
    document.body.classList.add('ac-fs-open');
    document.body.classList.remove('kw-fs-open','search-chrome-collapsed');
    if(typeof acFsWanted!=='undefined')acFsWanted=true;
    if(typeof kwFsWanted!=='undefined')kwFsWanted=false;
    var sh=document.getElementById('acShell');
    if(sh){sh.classList.add('open','ac-fs');}
    var ac=document.getElementById('acList');
    if(ac)ac.classList.add('open');
  }else{
    document.body.classList.add('kw-fs-open','kw-open');
    document.body.classList.remove('ac-fs-open','kw-chrome-collapsed');
    if(typeof kwFsWanted!=='undefined')kwFsWanted=true;
    if(typeof acFsWanted!=='undefined')acFsWanted=false;
    var fw=document.getElementById('filterWrap');
    if(fw)fw.classList.add('open');
    var sh2=document.getElementById('acShell');
    if(sh2)sh2.classList.remove('ac-fs');
  }
  if(typeof syncAcFsBtn==='function')syncAcFsBtn();
  if(typeof syncKwFsBtn==='function')syncKwFsBtn();
  if(typeof placeCatalogJumpStack==='function')placeCatalogJumpStack();
  if(typeof placePortableHandles==='function')placePortableHandles();
  if(typeof syncHdrMenuBtns==='function')syncHdrMenuBtns();
  if(typeof syncPortableBrowserFs==='function')syncPortableBrowserFs();
  // #region agent log
  if(typeof dbgPortableJumpGap==='function')dbgPortableJumpGap('menu-fs-'+which);
  if(typeof dbgMobileUi==='function')dbgMobileUi('menu-fs-in',{hyp:'H-MFS',which:which});
  // #endregion
}
function portableExitMenuFs(){
  var prev=portableMenuFsPrev;
  portableMenuFsPrev=null;
  portableRestoreMenuCombo(prev);
  if(typeof syncAcFsBtn==='function')syncAcFsBtn();
  if(typeof syncKwFsBtn==='function')syncKwFsBtn();
  if(typeof placeCatalogJumpStack==='function')placeCatalogJumpStack();
  if(typeof placePortableHandles==='function')placePortableHandles();
  if(typeof syncHdrMenuBtns==='function')syncHdrMenuBtns();
  if(typeof syncPortableBrowserFs==='function')syncPortableBrowserFs();
  // #region agent log
  if(typeof dbgPortableJumpGap==='function')dbgPortableJumpGap('menu-fs-exit');
  if(typeof dbgMobileUi==='function')dbgMobileUi('menu-fs-out',{hyp:'H-MFS'});
  // #endregion
}
window.portableEnterMenuFs=portableEnterMenuFs;
window.portableExitMenuFs=portableExitMenuFs;
window.phoneExitFs=function(){
  if(window.CATALOG_PORTABLE&&portableMenuFsOn()){portableExitMenuFs();return;}
  var back=(typeof lastNonFsDisplay==='string'&&(lastNonFsDisplay==='middle'||lastNonFsDisplay==='sides'))?lastNonFsDisplay:'';
  if(!back||back==='fs')back=(window.matchMedia&&window.matchMedia('(orientation:portrait)').matches)?'middle':'sides';
  if(typeof setDisplayMode==='function')setDisplayMode(back,{pick:true});
};
window.toggleKwFullscreen=function(){
  if(window.CATALOG_PORTABLE&&document.body.classList.contains('display-sides')){
    if(portableMenuFsOn()==='keywords')portableExitMenuFs();
    else portableEnterMenuFs('keywords');
    return;
  }
  if(typeof isPhoneViewport==='function'&&isPhoneViewport()){
    if(typeof setDisplayMode==='function')setDisplayMode('sides',{bothMenus:false,pick:true});
    return;
  }
  if(typeof expandKwMenu==='function')expandKwMenu();
};
window.toggleAcFullscreen=function(){
  if(window.CATALOG_PORTABLE&&document.body.classList.contains('display-sides')){
    if(portableMenuFsOn()==='search')portableExitMenuFs();
    else portableEnterMenuFs('search');
    return;
  }
  if(typeof isPhoneViewport==='function'&&isPhoneViewport()){
    if(typeof setDisplayMode==='function')setDisplayMode('sides',{pick:true});
    return;
  }
  if(typeof expandSearchMenu==='function')expandSearchMenu();
};"""

SEARCH_MORE_OLD = """    add(document.body.classList.contains('display-fs')?'Exit':'Full',function(){if(typeof toggleAcFullscreen==='function')toggleAcFullscreen();},document.body.classList.contains('display-fs')?'Exit fullscreen':'Fullscreen search');
    add(document.body.classList.contains('layout-edit')?'Done':'Edit',function(){if(typeof toggleLayoutEdit==='function')toggleLayoutEdit();},document.body.classList.contains('layout-edit')?'Done arranging':'Customize layout');
    if(document.body.classList.contains('display-fs'))add('K',function(){if(typeof toggleHdrKw==='function')toggleHdrKw();},'Keywords');"""

SEARCH_MORE_NEW = """    add('Fullscreen',function(){if(typeof toggleAcFullscreen==='function')toggleAcFullscreen();},'Fullscreen Search');
    add(document.body.classList.contains('layout-edit')?'Done':'Edit',function(){if(typeof toggleLayoutEdit==='function')toggleLayoutEdit();},document.body.classList.contains('layout-edit')?'Done arranging':'Customize layout');"""

KW_MORE_OLD = """  phoneMoreAdd(pop,document.body.classList.contains('display-fs')?'Exit':'Full',function(){if(typeof toggleKwFullscreen==='function')toggleKwFullscreen();},document.body.classList.contains('display-fs')?'Exit fullscreen':'Fullscreen Keywords');"""

KW_MORE_NEW = """  phoneMoreAdd(pop,'Fullscreen',function(){if(typeof toggleKwFullscreen==='function')toggleKwFullscreen();},'Fullscreen Keywords');"""


def once(text, old, new, label, path):
    n = text.count(old)
    if n == 1:
        return text.replace(old, new, 1)
    if n == 0 and new in text:
        print(f"  skip {path.name} {label}")
        return text
    raise SystemExit(f"{path.name}: {label} count={n}")


def patch(path: Path):
    t = path.read_text(encoding="utf-8")
    t = once(t, FS_BTN_OLD, FS_BTN_NEW, "hide-full-btn", path)
    t = once(t, HIDE_STRIP_OLD, HIDE_STRIP_NEW, "show-strip-fs", path)
    t = once(t, PLACE_AC_OLD, PLACE_AC_NEW, "placeAcShell", path)
    t = once(t, SET_START_OLD, SET_START_NEW, "setDisplay-start", path)
    t = once(t, SET_END_OLD, SET_END_NEW, "setDisplay-end", path)
    t = once(t, TOGGLE_OLD, TOGGLE_NEW, "toggle-fs", path)
    t = once(t, SEARCH_MORE_OLD, SEARCH_MORE_NEW, "search-more", path)
    t = once(t, KW_MORE_OLD, KW_MORE_NEW, "kw-more", path)
    if CSS_MARK not in t:
        if "</style></head>" not in t:
            raise SystemExit(f"{path.name}: no style close")
        t = t.replace("</style></head>", CSS_ADD + "\n</style></head>", 1)
        print(f"  css {path.name}")
    else:
        print(f"  skip {path.name} css")
    path.write_text(t, encoding="utf-8")
    print("ok", path.name)


def main():
    for p in FILES:
        if not p.exists():
            raise SystemExit(f"missing {p}")
        patch(p)


if __name__ == "__main__":
    main()
