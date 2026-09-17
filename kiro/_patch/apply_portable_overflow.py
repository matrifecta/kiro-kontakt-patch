#!/usr/bin/env python3
"""Portable: every overflow pane must scroll; keep FS classes on rotate."""
from pathlib import Path

ROOT = Path("/home/phnx/kiro-kontakt-patch/public/catalogs")
FILES = [ROOT / "DS-CATALOG-portable.html", ROOT / "KONTAKT-CATALOG-portable.html"]

CSS_MARK = "/* fix-PORTABLE-OVERFLOW:"
CSS = r"""
/* fix-PORTABLE-OVERFLOW: every pane/list can scroll its content */
@media all{
  body.catalog-portable #acList,
  body.catalog-portable #acList.open,
  body.catalog-portable.ac-fs-open #acList,
  body.catalog-portable.ac-fs-open #acList.open,
  body.catalog-portable.is-browser-fs #acList,
  body.catalog-portable.display-sides.display-middle #acList,
  body.catalog-portable.display-sides.ac-fs-open:not(.kw-fs-open) #acList{
    overflow-x:hidden!important;overflow-y:auto!important;
    min-height:0!important;flex:1 1 0%!important;
    max-height:none!important;height:auto!important;
    touch-action:pan-y!important;pointer-events:auto!important;
    overscroll-behavior:contain;-webkit-overflow-scrolling:touch!important
  }
  body.catalog-portable #acShell,
  body.catalog-portable #acShell.open,
  body.catalog-portable #acShell.ac-fs,
  body.catalog-portable.ac-fs-open #acShell{
    display:flex!important;flex-direction:column!important;
    min-height:0!important;flex:1 1 0%!important;overflow:hidden!important
  }
  body.catalog-portable #filterWrap .filter-panel,
  body.catalog-portable #filterWrap.open .filter-panel,
  body.catalog-portable.kw-fs-open #filterWrap .filter-panel,
  body.catalog-portable.display-sides.kw-fs-open:not(.ac-fs-open) #kwbar{
    overflow-x:hidden!important;overflow-y:auto!important;
    min-height:0!important;flex:1 1 auto!important;
    max-height:none!important;touch-action:pan-y!important;
    pointer-events:auto!important;-webkit-overflow-scrolling:touch!important
  }
  body.catalog-portable.kw-fs-open #kwbar{flex:1 1 0%!important}
  body.catalog-portable #catalogMain,
  body.catalog-portable.display-sides #catalogMain,
  body.catalog-portable.display-sides.display-middle #catalogMain{
    overflow-x:hidden!important;overflow-y:auto!important;
    min-height:0!important;touch-action:pan-y!important;
    pointer-events:auto!important;-webkit-overflow-scrolling:touch!important
  }
  body.catalog-portable #catalogIndex:not(.is-collapsed){
    display:flex!important;flex-direction:column!important;
    min-height:0!important;max-height:min(42dvh,20rem)!important;overflow:hidden!important
  }
  body.catalog-portable #catalogIndex:not(.is-collapsed) #catalogIndexList,
  body.catalog-portable #catalogIndex:not(.is-collapsed) .index{
    overflow-x:hidden!important;overflow-y:auto!important;
    min-height:0!important;flex:1 1 auto!important;max-height:none!important;
    touch-action:pan-y!important;-webkit-overflow-scrolling:touch!important
  }
  body.catalog-portable .path-reader-text,
  body.catalog-portable .desc-reader-text,
  body.catalog-portable .entry.highlight .hl-body{
    overflow-x:hidden!important;overflow-y:auto!important;
    min-height:0!important;flex:1 1 auto!important;
    touch-action:pan-y!important;-webkit-overflow-scrolling:touch!important
  }
  body.catalog-portable #hdrMorePop:not([hidden]),
  body.catalog-portable #searchStripMorePop:not([hidden]),
  body.catalog-portable #kwStripMorePop:not([hidden]),
  body.catalog-portable #historyCloud:not([hidden]),
  body.catalog-portable #layoutPresetsPop:not([hidden]){
    overflow-x:hidden!important;overflow-y:auto!important;
    max-height:min(50dvh,22rem)!important;-webkit-overflow-scrolling:touch!important
  }
  body.catalog-portable.display-sides.display-middle #searchChrome,
  body.catalog-portable.display-sides.display-middle #filterWrap{
    overflow:hidden!important;min-height:8rem!important
  }
  body.catalog-portable.ac-fs-open #searchSplit,
  body.catalog-portable.kw-fs-open #dualFsSep,
  body.catalog-portable.ac-fs-open #dualFsSep,
  body.catalog-portable.kw-fs-open #searchSplit{
    pointer-events:none!important
  }
}
"""

ENSURE_OLD = """function portableEnsureScrollMenus(){
  if(!window.CATALOG_PORTABLE)return;
  var ac=document.getElementById('acList');
  var sh=document.getElementById('acShell');
  var fw=document.getElementById('filterWrap');
  var fs=document.body.classList.contains('display-fs');
  if(ac)ac.classList.add('open');
  if(sh){
    sh.classList.add('open');
    sh.classList.remove('ac-fixed');
    ['top','left','right','bottom','width','height','max-width','max-height'].forEach(function(p){sh.style.removeProperty(p);});
  }
  if(fs){
    var searchOn=!document.body.classList.contains('search-chrome-collapsed')&&((typeof acFsWanted!=='undefined'&&acFsWanted)||document.body.classList.contains('ac-fs-open'));
    var kwOn=!document.body.classList.contains('kw-chrome-collapsed')&&((typeof kwFsWanted!=='undefined'&&kwFsWanted)||document.body.classList.contains('kw-fs-open'));
    document.body.classList.toggle('ac-fs-open',searchOn);
    document.body.classList.toggle('kw-fs-open',kwOn);
    document.body.classList.toggle('dual-fs-open',searchOn&&kwOn);
    document.body.classList.toggle('kw-open',kwOn);
    if(typeof acFsWanted!=='undefined')acFsWanted=!!searchOn;
    if(typeof kwFsWanted!=='undefined')kwFsWanted=!!kwOn;
    if(sh)sh.classList.toggle('ac-fs',searchOn);
    if(fw){if(kwOn)fw.classList.add('open');else fw.classList.remove('open');}
  }else if(sh){
    sh.classList.remove('ac-fs');
  }
  if(document.body.classList.contains('display-middle')&&fw){
    fw.classList.add('open');
    document.body.classList.add('kw-open');
    document.body.classList.remove('kw-chrome-collapsed');
  }
}"""

ENSURE_NEW = r"""function portableBindScrollPorts(){
  if(!window.CATALOG_PORTABLE||window._portableScrollPortsBound)return;
  window._portableScrollPortsBound=true;
  document.addEventListener('pointerdown',function(e){
    var t=e.target;
    if(!t||!t.closest)return;
    if(t.closest('#acList,#filterPanel,#kwbar,#catalogMain,#catalogIndexList,.path-reader-text,.desc-reader-text,#hdrMorePop,#searchStripMorePop,#kwStripMorePop,#historyCloud')){
      e.stopPropagation();
    }
  },true);
}
function portableEnsureScrollMenus(){
  if(!window.CATALOG_PORTABLE)return;
  portableBindScrollPorts();
  var menuFs=(typeof portableMenuFsOn==='function'&&portableMenuFsOn())||(typeof portableMenuFsHold==='string'?portableMenuFsHold:'');
  var ac=document.getElementById('acList');
  var sh=document.getElementById('acShell');
  var fw=document.getElementById('filterWrap');
  var fp=document.getElementById('filterPanel')||(fw&&fw.querySelector('.filter-panel'));
  var main=document.getElementById('catalogMain');
  var ix=document.getElementById('catalogIndex');
  var ixL=document.getElementById('catalogIndexList');
  function port(el,oy){
    if(!el)return;
    el.style.setProperty('overflow-x','hidden','important');
    el.style.setProperty('overflow-y',oy||'auto','important');
    el.style.setProperty('min-height','0','important');
    el.style.setProperty('touch-action','pan-y','important');
    el.style.setProperty('pointer-events','auto','important');
  }
  if(ac){
    ac.classList.add('open');
    ac.style.removeProperty('height');
    ac.style.removeProperty('max-height');
    port(ac,'auto');
  }
  if(sh){
    sh.classList.add('open');
    sh.classList.remove('ac-fixed');
    ['top','left','right','bottom','width','height','max-width','max-height'].forEach(function(p){sh.style.removeProperty(p);});
    if(menuFs==='search'||(document.body.classList.contains('ac-fs-open')&&!document.body.classList.contains('kw-fs-open')))sh.classList.add('ac-fs');
    else if(!document.body.classList.contains('display-fs'))sh.classList.remove('ac-fs');
    sh.style.setProperty('overflow','hidden','important');
    sh.style.setProperty('min-height','0','important');
  }
  port(fp,'auto');
  port(main,'auto');
  if(ix&&!ix.classList.contains('is-collapsed'))port(ixL||ix,'auto');
  var pops=['hdrMorePop','searchStripMorePop','kwStripMorePop','historyCloud'];
  pops.forEach(function(id){
    var p=document.getElementById(id);
    if(p&&!p.hidden&&!p.hasAttribute('hidden'))port(p,'auto');
  });
  // #region agent log
  if(typeof dbgPortableScroll==='function')dbgPortableScroll('ensure-scroll',{hyp:'H-OVF',menuFs:String(menuFs||'')});
  // #endregion
}"""


def patch(text):
    if CSS_MARK not in text:
        needle = "</style></head><body class=\"search-mode\">"
        if needle not in text:
            raise SystemExit("style close missing")
        text = text.replace(needle, CSS + "\n</style></head><body class=\"search-mode\">", 1)
    n = text.count(ENSURE_OLD)
    if n != 1:
        if "function portableBindScrollPorts" in text:
            return text
        raise SystemExit(f"ensure fn count={n}")
    text = text.replace(ENSURE_OLD, ENSURE_NEW, 1)
    return text


def main():
    for path in FILES:
        raw = path.read_text(encoding="utf-8")
        path.write_text(patch(raw), encoding="utf-8")
        print(f"patched {path.name}")


if __name__ == "__main__":
    main()
