#!/usr/bin/env python3
"""Portable: menu scrollports, browser fullscreen, Customize in ⋯, unobstructed search field."""
from pathlib import Path

ROOT = Path("/home/phnx/kiro-kontakt-patch")
FILES = [
    ROOT / "public/catalogs/DS-CATALOG-portable.html",
    ROOT / "public/catalogs/KONTAKT-CATALOG-portable.html",
]

CSS_MARK = "/* fix-PORTABLE-SCROLL-FS:"
CSS_END = "/* end-PORTABLE-SCROLL-FS */"
CSS = r"""
/* fix-PORTABLE-SCROLL-FS: scrollports, browser FS, search field, customize */
html.is-browser-fs,body.catalog-portable.is-browser-fs{
  position:fixed!important;inset:0!important;width:100%!important;height:100dvh!important;
  max-height:100dvh!important;overflow:hidden!important
}
@media all{
  body.catalog-portable #searchChrome,
  body.catalog-portable.search-mode #searchChrome,
  body.catalog-portable.search-mode.kw-open #searchChrome,
  body.catalog-portable.search-mode:not(.kw-open) #searchChrome{
    display:flex!important;flex-direction:column!important;
    grid-template-columns:none!important;grid-template-rows:none!important;
    width:100%!important;max-width:none!important;min-width:0!important;
    min-height:0!important;align-self:stretch!important;
    overflow:hidden!important;position:relative!important;inset:auto!important;
    padding:0!important;gap:0!important;z-index:6
  }
  body.catalog-portable.display-sides:not(.display-middle) #searchChrome,
  body.catalog-portable.display-fs #searchChrome{
    height:100%!important;max-height:none!important
  }
  body.catalog-portable #searchCol,
  body.catalog-portable.search-mode #searchCol,
  body.catalog-portable #searchChrome .search-strip-anchor{
    display:flex!important;flex-direction:column!important;
    flex:1 1 0%!important;min-height:0!important;min-width:0!important;
    width:100%!important;max-width:100%!important;
    overflow:hidden!important;height:auto!important;max-height:none!important;
    justify-self:stretch!important
  }
  body.catalog-portable #searchStrip,
  body.catalog-portable.search-mode #searchStrip,
  body.catalog-portable.display-fs #acShell.ac-fs>.search-strip{
    display:flex!important;flex-direction:row!important;flex-wrap:wrap!important;
    flex:0 0 auto!important;align-items:center;gap:.35rem;
    width:100%!important;max-width:100%!important;min-width:0!important;
    min-height:2.75rem;position:relative!important;overflow:visible!important;
    box-sizing:border-box;padding:.25rem .4rem;z-index:3
  }
  body.catalog-portable #searchInput{
    flex:1 1 auto!important;min-width:8rem!important;width:auto!important;
    max-width:none!important;position:relative!important;z-index:4!important;
    order:0
  }
  body.catalog-portable #searchStrip .search-strip-clear{
    display:inline-flex!important;flex:0 0 auto;order:1;position:relative;z-index:3
  }
  body.catalog-portable #searchStripMore{
    display:inline-flex!important;flex:0 0 auto;order:3;position:relative;z-index:3
  }
  body.catalog-portable.display-fs #searchStrip .search-strip-fs{
    display:inline-flex!important;flex:0 0 auto;order:2;position:relative;z-index:3
  }
  body.catalog-portable #searchStrip > *:not(#searchInput):not(.search-strip-clear):not(#searchStripMore):not(#searchStripMorePop):not(.search-strip-fs){
    display:none!important
  }
  body.catalog-portable:not(.display-fs) #searchStrip .search-strip-fs{display:none!important}
  body.catalog-portable #searchStrip .search-only-scale,
  body.catalog-portable #searchOnlyScale,
  body.catalog-portable #searchOnlyScalePop,
  body.catalog-portable .fs-stripe-wrap,
  body.catalog-portable .fs-mode-nav,
  body.catalog-portable #acFsBar,
  body.catalog-portable .ac-fs-bar,
  body.catalog-portable .ac-height,
  body.catalog-portable .ac-width,
  body.catalog-portable .kw-shade-height,
  body.catalog-portable .search-height,
  body.catalog-portable .ac-scroll-stripe,
  body.catalog-portable .filter-kw-tools,
  body.catalog-portable #layoutPresets,
  body.catalog-portable .layout-presets{display:none!important;pointer-events:none!important}
  body.catalog-portable #acShell,
  body.catalog-portable #acShell.open,
  body.catalog-portable #acShell.ac-fs,
  body.catalog-portable.display-fs #acShell,
  body.catalog-portable.display-fs #acShell.ac-fs{
    display:flex!important;flex-direction:column!important;
    flex:1 1 0%!important;min-height:0!important;min-width:0!important;
    width:100%!important;max-width:none!important;
    height:auto!important;max-height:none!important;
    overflow:hidden!important;position:relative!important;inset:auto!important;
    top:auto!important;left:auto!important;right:auto!important;bottom:auto!important;
    box-shadow:none!important;border:0!important
  }
  body.catalog-portable #acList,
  body.catalog-portable #acList.open,
  body.catalog-portable.display-sides #acList,
  body.catalog-portable.display-fs #acList,
  body.catalog-portable.display-sides.display-middle #acList{
    display:block!important;position:relative!important;inset:auto!important;
    flex:1 1 0%!important;min-height:0!important;min-width:0!important;
    width:100%!important;height:auto!important;max-height:none!important;
    overflow-x:hidden!important;overflow-y:auto!important;
    -webkit-overflow-scrolling:touch!important;touch-action:pan-y!important;
    overscroll-behavior:contain;box-shadow:none!important
  }
  body.catalog-portable #filterWrap,
  body.catalog-portable #filterWrap.open,
  body.catalog-portable.display-sides #filterWrap,
  body.catalog-portable.display-fs #filterWrap,
  body.catalog-portable.display-fs.kw-fs-open #filterWrap{
    display:flex!important;flex-direction:column!important;
    min-height:0!important;min-width:0!important;width:100%!important;
    max-width:none!important;overflow:hidden!important;
    position:relative!important;inset:auto!important;transform:none!important;
    box-shadow:none!important;align-self:stretch!important
  }
  body.catalog-portable.display-sides:not(.display-middle) #filterWrap,
  body.catalog-portable.display-fs #filterWrap{
    height:100%!important;max-height:none!important
  }
  body.catalog-portable #filterWrap .filter-top{flex:0 0 auto;flex-wrap:wrap;overflow:visible;min-width:0;width:100%}
  body.catalog-portable #filterWrap .filter-panel,
  body.catalog-portable #filterWrap.open .filter-panel,
  body.catalog-portable.display-fs #filterWrap .filter-panel,
  body.catalog-portable.display-sides #filterWrap.open .filter-panel{
    display:flex!important;flex-direction:column!important;
    flex:1 1 0%!important;min-height:0!important;max-height:none!important;
    height:auto!important;width:100%!important;max-width:100%!important;
    overflow-x:hidden!important;overflow-y:auto!important;
    -webkit-overflow-scrolling:touch!important;touch-action:pan-y!important;
    overscroll-behavior:contain;padding:.35rem .45rem
  }
  body.catalog-portable .cat-switch{
    display:flex!important;flex-wrap:wrap!important;
    flex:0 0 auto!important;min-width:0!important;width:100%!important;
    max-width:100%!important;overflow-x:auto!important;overflow-y:visible!important;
    -webkit-overflow-scrolling:touch;touch-action:pan-x pan-y;align-content:flex-start
  }
  body.catalog-portable #kwbar{
    flex:0 0 auto!important;min-height:min-content!important;min-width:0!important;
    width:100%!important;max-width:100%!important;height:auto!important;max-height:none!important;
    overflow:visible!important
  }
  body.catalog-portable.display-fs:not(.dual-fs-open).kw-fs-open #filterWrap,
  body.catalog-portable.display-fs:not(.ac-fs-open).kw-fs-open #filterWrap{
    grid-column:1/-1!important;width:100%!important;max-width:none!important
  }
  body.catalog-portable.display-fs:not(.dual-fs-open).ac-fs-open #searchChrome,
  body.catalog-portable.display-fs:not(.kw-fs-open).ac-fs-open #searchChrome,
  body.catalog-portable.display-fs:not(.kw-fs-open).ac-fs-open #acShell{
    grid-column:1/-1!important;width:100%!important
  }
  body.catalog-portable.display-sides.display-middle #searchChrome{
    display:flex!important;flex-direction:column!important;
    flex:0 1 auto!important;min-height:8rem!important;
    max-height:min(38dvh,18rem)!important;height:auto!important;
    overflow:hidden!important;width:100%!important;border-right:0!important
  }
  body.catalog-portable.display-sides.display-middle #filterWrap,
  body.catalog-portable.display-sides.display-middle.kw-open #filterWrap{
    display:flex!important;flex-direction:column!important;
    flex:0 1 auto!important;min-height:8rem!important;
    max-height:min(38dvh,18rem)!important;height:auto!important;
    overflow:hidden!important;width:100%!important;max-width:100%!important
  }
  body.catalog-portable #searchSplit,
  body.catalog-portable #dualFsSep,
  body.catalog-portable #searchSplit.port-stripe-v,
  body.catalog-portable #dualFsSep.port-stripe-v{
    width:8px!important;min-width:8px!important;max-width:8px!important;
    pointer-events:auto!important;touch-action:none;z-index:90
  }
  body.catalog-portable #searchSplit.port-stripe-h,
  body.catalog-portable #dualFsSep.port-stripe-h{
    height:8px!important;min-height:8px!important;max-height:8px!important;
    width:auto!important;max-width:none!important;min-width:0!important;
    pointer-events:auto!important
  }
  body.catalog-portable #searchSplit::before,
  body.catalog-portable #dualFsSep::before,
  body.catalog-portable.layout-edit #searchSplit::before,
  body.catalog-portable.layout-edit #dualFsSep::before{
    pointer-events:none!important;width:2px!important
  }
  body.catalog-portable #searchSplit.port-stripe-h::before,
  body.catalog-portable #dualFsSep.port-stripe-h::before,
  body.catalog-portable.layout-edit #searchSplit.port-stripe-h::before{
    height:2px!important;width:auto!important
  }
  body.catalog-portable .catalog-header>#hdrMorePop,
  body.catalog-portable #searchStripMorePop,
  body.catalog-portable #kwStripMorePop,
  body.catalog-portable .hdr-more-pop,
  body.catalog-portable .search-strip-more-pop,
  body.catalog-portable .kw-strip-more-pop{
    position:static!important;inset:auto!important;float:none!important;transform:none!important;
    flex:1 1 100%!important;width:100%!important;max-width:100%!important;min-width:0!important;
    max-height:min(46dvh,20rem)!important;overflow-x:hidden!important;overflow-y:auto!important;
    -webkit-overflow-scrolling:touch;word-wrap:break-word;overflow-wrap:anywhere;
    z-index:6!important;box-shadow:none!important;order:99;box-sizing:border-box
  }
  body.catalog-portable #searchStripMorePop{order:99}
  body.catalog-portable #hdrMorePop:not([hidden]) button,
  body.catalog-portable #searchStripMorePop:not([hidden]) button,
  body.catalog-portable #kwStripMorePop:not([hidden]) button{
    white-space:normal!important;text-align:left;overflow-wrap:anywhere;word-break:break-word;
    min-height:2.25rem;width:100%;box-sizing:border-box
  }
  body.catalog-portable.display-fs .kw-companion-btn,
  body.catalog-portable.display-fs .ac-companion-btn{display:none!important}
  body.catalog-portable.display-fs.ac-fs-open .ac-fs-back,
  body.catalog-portable.display-fs.kw-fs-open .kw-fs-back{display:none!important}
  body.catalog-portable.display-fs:not(.ac-fs-open) #searchChrome,
  body.catalog-portable.display-fs.search-chrome-collapsed #searchChrome{
    display:none!important
  }
  body.catalog-portable.display-fs:not(.kw-fs-open) #filterWrap,
  body.catalog-portable.display-fs.kw-chrome-collapsed #filterWrap{
    display:none!important
  }
  body.catalog-portable.display-fs.ac-fs-open.kw-fs-open,
  body.catalog-portable.display-fs.dual-fs-open{
    grid-template-columns:minmax(0,var(--portable-lw,1fr)) minmax(0,1fr)!important
  }
  body.catalog-portable.display-sides.display-middle #searchChrome,
  body.catalog-portable.display-sides.display-middle #filterWrap,
  body.catalog-portable.display-sides.display-middle.kw-open #filterWrap{
    min-height:10rem!important;max-height:min(44dvh,22rem)!important
  }
}
/* end-PORTABLE-SCROLL-FS */
"""

JS_MARK = "function dbgPortableScroll("
JS = r"""
function portableWantBrowserFs(){
  if(!window.CATALOG_PORTABLE)return false;
  var b=document.body;
  return !!(b.classList.contains('display-fs')||(b.classList.contains('display-sides')&&!b.classList.contains('display-middle')));
}
function portableFsApiAvailable(){
  var el=document.documentElement;
  return !!(el&&(el.requestFullscreen||el.webkitRequestFullscreen||el.webkitRequestFullScreen));
}
function portableApplyFsClass(on){
  document.documentElement.classList.toggle('is-browser-fs',!!on);
  if(document.body)document.body.classList.toggle('is-browser-fs',!!on);
}
function syncPortableBrowserFs(){
  if(!window.CATALOG_PORTABLE)return;
  var want=portableWantBrowserFs();
  var fsEl=document.fullscreenElement||document.webkitFullscreenElement||null;
  var inFs=!!fsEl;
  var api=portableFsApiAvailable();
  if(want){
    if(!api){
      portableApplyFsClass(true);
      // #region agent log
      if(typeof dbgPortableScroll==='function')dbgPortableScroll('fs-fallback',{hyp:'H-FS1',want:true,api:false,inFs:false});
      // #endregion
      return;
    }
    if(inFs){portableApplyFsClass(false);return;}
    var el=document.documentElement;
    var req=null;
    try{
      if(el.requestFullscreen)req=el.requestFullscreen();
      else if(el.webkitRequestFullscreen)req=el.webkitRequestFullscreen();
      else if(el.webkitRequestFullScreen)req=el.webkitRequestFullScreen();
    }catch(errFs){portableApplyFsClass(true);req=null;}
    // #region agent log
    if(typeof dbgPortableScroll==='function')dbgPortableScroll('fs-request',{hyp:'H-FS1',want:true,api:true,called:true,inFs:!!(document.fullscreenElement||document.webkitFullscreenElement)});
    // #endregion
    if(req&&typeof req.then==='function'){
      req.then(function(){portableApplyFsClass(false);}).catch(function(){portableApplyFsClass(true);});
    }else if(!document.fullscreenElement&&!document.webkitFullscreenElement){
      portableApplyFsClass(true);
    }
  }else{
    portableApplyFsClass(false);
    if(inFs){
      try{
        if(document.exitFullscreen)document.exitFullscreen();
        else if(document.webkitExitFullscreen)document.webkitExitFullscreen();
      }catch(errEx){}
      // #region agent log
      if(typeof dbgPortableScroll==='function')dbgPortableScroll('fs-exit',{hyp:'H-FS1',want:false,inFs:true});
      // #endregion
    }
  }
}
function portableEnsureScrollMenus(){
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
    var searchOn=!document.body.classList.contains('search-chrome-collapsed');
    var kwOn=!document.body.classList.contains('kw-chrome-collapsed');
    if(typeof acFsWanted!=='undefined')acFsWanted=!!searchOn;
    if(typeof kwFsWanted!=='undefined')kwFsWanted=!!kwOn;
    document.body.classList.toggle('ac-fs-open',searchOn);
    document.body.classList.toggle('kw-fs-open',kwOn);
    document.body.classList.toggle('dual-fs-open',searchOn&&kwOn);
    document.body.classList.toggle('kw-open',kwOn);
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
}
function portableMoreEdit(pop){
  if(!pop||typeof phoneMoreAdd!=='function')return;
  var on=document.body.classList.contains('layout-edit');
  phoneMoreAdd(pop,on?'Done':'Edit',function(){if(typeof toggleLayoutEdit==='function')toggleLayoutEdit();},on?'Done arranging':'Customize layout');
}
function dbgPortableScroll(phase,extra){
  extra=extra||{};
  // #region agent log
  try{
    var ac=document.getElementById('acList');
    var fw=document.getElementById('filterWrap');
    var fp=fw&&fw.querySelector('.filter-panel');
    var inp=document.getElementById('searchInput');
    var ch=document.getElementById('searchChrome');
    var ir=inp?inp.getBoundingClientRect():null;
    var ov=false;
    if(ir&&ch){
      [].slice.call(ch.querySelectorAll('button,select,.search-strip-fs,.search-strip-more')).forEach(function(b){
        if(b===inp||(inp.contains&&inp.contains(b)))return;
        var br=b.getBoundingClientRect();
        if(br.width<2||br.height<2)return;
        if(!(ir.right<=br.left+1||br.right<=ir.left+1||ir.bottom<=br.top+1||br.bottom<=ir.top+1))ov=true;
      });
    }
    fetch('http://127.0.0.1:7529/ingest/1cf46354-1d61-4c80-bd72-a340f1db1b51',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'c00e3e'},body:JSON.stringify({sessionId:'c00e3e',runId:'post-fix',hypothesisId:extra.hyp||'H-SCR1',location:'catalog:dbgPortableScroll',message:'scroll-fs',data:{phase:String(phase||''),vw:innerWidth||0,vh:innerHeight||0,cur:typeof currentDisplay!=='undefined'?String(currentDisplay):'',cls:document.body?document.body.className:'',acH:ac?Math.round(ac.getBoundingClientRect().height):0,acClient:ac?ac.clientHeight:0,acScroll:ac?ac.scrollHeight:0,acOv:ac?getComputedStyle(ac).overflowY:'',fpH:fp?Math.round(fp.getBoundingClientRect().height):0,fpClient:fp?fp.clientHeight:0,fpScroll:fp?fp.scrollHeight:0,inpW:ir?Math.round(ir.width):0,inpL:ir?Math.round(ir.left):0,overlap:ov,fsEl:!!(document.fullscreenElement||document.webkitFullscreenElement),cssFs:!!(document.documentElement.classList.contains('is-browser-fs')),wantFs:!!portableWantBrowserFs(),api:!!portableFsApiAvailable()},timestamp:Date.now()})}).catch(function(){});
  }catch(errLog){}
  // #endregion
}
window.portableWantBrowserFs=portableWantBrowserFs;
window.syncPortableBrowserFs=syncPortableBrowserFs;
window.portableEnsureScrollMenus=portableEnsureScrollMenus;
window.dbgPortableScroll=dbgPortableScroll;
document.addEventListener('fullscreenchange',function(){
  if(!window.CATALOG_PORTABLE)return;
  var inFs=!!(document.fullscreenElement||document.webkitFullscreenElement);
  if(!inFs&&portableWantBrowserFs())portableApplyFsClass(true);
  else if(inFs)portableApplyFsClass(false);
});
document.addEventListener('webkitfullscreenchange',function(){
  if(!window.CATALOG_PORTABLE)return;
  var inFs=!!(document.fullscreenElement||document.webkitFullscreenElement);
  if(!inFs&&portableWantBrowserFs())portableApplyFsClass(true);
  else if(inFs)portableApplyFsClass(false);
});
"""

SEARCH_MORE_OLD = """    add('Clear',function(){if(typeof clearAllFilters==='function')clearAllFilters();},'Clear search');
    add('History',function(){var h=document.getElementById('searchHistory');if(h)h.click();},'History');
    pop.removeAttribute('hidden');
    btn.setAttribute('aria-expanded','true');
    // #region agent log
    if(typeof dbgMobileUi==='function')dbgMobileUi('search-more',{hyp:'H-CHROME'});
    // #endregion"""

SEARCH_MORE_NEW = """    add('Hide',function(){if(typeof toggleSearchChrome==='function')toggleSearchChrome();},'Hide Search');
    add('History',function(){var h=document.getElementById('searchHistory');if(h)h.click();},'History');
    add(document.body.classList.contains('display-fs')?'Exit':'Full',function(){if(typeof toggleAcFullscreen==='function')toggleAcFullscreen();},document.body.classList.contains('display-fs')?'Exit fullscreen':'Fullscreen search');
    add(document.body.classList.contains('layout-edit')?'Done':'Edit',function(){if(typeof toggleLayoutEdit==='function')toggleLayoutEdit();},document.body.classList.contains('layout-edit')?'Done arranging':'Customize layout');
    if(document.body.classList.contains('display-fs'))add('K',function(){if(typeof toggleHdrKw==='function')toggleHdrKw();},'Keywords');
    pop.removeAttribute('hidden');
    btn.setAttribute('aria-expanded','true');
    // #region agent log
    if(typeof dbgMobileUi==='function')dbgMobileUi('search-more',{hyp:'H-CHROME'});
    if(typeof dbgPortableScroll==='function')dbgPortableScroll('search-more',{hyp:'H-SCR1'});
    // #endregion"""

HDR_MORE_OLD = """  phoneMoreAdd(pop,document.body.classList.contains('layout-edit')?'Done':'Edit',function(){if(typeof toggleLayoutEdit==='function')toggleLayoutEdit();},document.body.classList.contains('layout-edit')?'Done arranging':'Customize layout');
  phoneMoreAdd(pop,'Miss',function(){var x=document.getElementById('clearMissBtn');if(x)x.click();},'Clear on miss');
  phoneMoreAdd(pop,'Flip',function(){if(typeof togglePortraitSidesFlip==='function')togglePortraitSidesFlip();},'Flip panes');
  phoneMoreAdd(pop,'History',function(){var h=document.getElementById('searchHistory');if(h)h.click();},'History');"""

HDR_MORE_NEW = """  phoneMoreAdd(pop,document.body.classList.contains('layout-edit')?'Done':'Edit',function(){if(typeof toggleLayoutEdit==='function')toggleLayoutEdit();},document.body.classList.contains('layout-edit')?'Done arranging':'Customize layout');
  phoneMoreAdd(pop,'Miss',function(){var x=document.getElementById('clearMissBtn');if(x)x.click();},'Clear on miss');
  phoneMoreAdd(pop,'Flip',function(){if(typeof togglePortraitSidesFlip==='function')togglePortraitSidesFlip();},'Flip panes');
  phoneMoreAdd(pop,'History',function(){var h=document.getElementById('searchHistory');if(h)h.click();},'History');"""

KW_MORE_OLD = """  phoneMoreAdd(pop,document.body.classList.contains('layout-edit')?'Done':'Edit',function(){if(typeof toggleLayoutEdit==='function')toggleLayoutEdit();},document.body.classList.contains('layout-edit')?'Done arranging':'Customize layout');
  phoneMoreAdd(pop,'Hide',function(){if(typeof toggleKwChrome==='function')toggleKwChrome();else if(typeof toggleHdrKw==='function')toggleHdrKw();},'Hide Keywords');
  phoneMoreAdd(pop,'Flip',function(){if(typeof togglePortraitSidesFlip==='function')togglePortraitSidesFlip();},'Flip panes');
  phoneMoreAdd(pop,'Tap',function(){if(typeof toggleTapToAdd==='function')toggleTapToAdd();},'Tap to add');
  phoneMoreAdd(pop,'Clear',function(){if(typeof clearAllFilters==='function')clearAllFilters();},'Clear keywords');
  phoneMoreAdd(pop,'History',function(){var h=document.getElementById('searchHistory');if(h)h.click();},'History');
  phoneMoreAdd(pop,document.body.classList.contains('display-fs')?'Exit':'Full',function(){if(typeof toggleKwFullscreen==='function')toggleKwFullscreen();},document.body.classList.contains('display-fs')?'Exit fullscreen':'Fullscreen Keywords');"""

KW_MORE_NEW = """  phoneMoreAdd(pop,document.body.classList.contains('layout-edit')?'Done':'Edit',function(){if(typeof toggleLayoutEdit==='function')toggleLayoutEdit();},document.body.classList.contains('layout-edit')?'Done arranging':'Customize layout');
  phoneMoreAdd(pop,'Hide',function(){if(typeof toggleKwChrome==='function')toggleKwChrome();else if(typeof toggleHdrKw==='function')toggleHdrKw();},'Hide Keywords');
  phoneMoreAdd(pop,'Flip',function(){if(typeof togglePortraitSidesFlip==='function')togglePortraitSidesFlip();},'Flip panes');
  phoneMoreAdd(pop,'Tap',function(){if(typeof toggleTapToAdd==='function')toggleTapToAdd();},'Tap to add');
  phoneMoreAdd(pop,'Clear',function(){if(typeof clearAllFilters==='function')clearAllFilters();},'Clear keywords');
  phoneMoreAdd(pop,'History',function(){var h=document.getElementById('searchHistory');if(h)h.click();},'History');
  phoneMoreAdd(pop,document.body.classList.contains('display-fs')?'Exit':'Full',function(){if(typeof toggleKwFullscreen==='function')toggleKwFullscreen();},document.body.classList.contains('display-fs')?'Exit fullscreen':'Fullscreen Keywords');"""

LAYOUT_OLD = """  if(typeof placeSidesHandles==='function')placeSidesHandles();
  if(typeof bindIndexHeight==='function')bindIndexHeight();

}
window.toggleLayoutEdit=toggleLayoutEdit;"""

LAYOUT_NEW = """  if(typeof placeSidesHandles==='function')placeSidesHandles();
  if(typeof bindIndexHeight==='function')bindIndexHeight();
  if(typeof placePortableHandles==='function')placePortableHandles();
  // #region agent log
  if(typeof dbgPortableScroll==='function')dbgPortableScroll('layout-edit',{hyp:'H-SCR1'});
  // #endregion

}
window.toggleLayoutEdit=toggleLayoutEdit;"""

SETDISP_OLD = """  if(typeof bindPortablePathHits==='function')bindPortablePathHits();
  if(typeof dbgPortableCards==='function')dbgPortableCards('setDisplayMode');
  if(typeof dbgMobileUi==='function')dbgMobileUi('setDisplayMode',{hyp:'H-P1'});
}
window.setDisplayMode=setDisplayMode;"""

SETDISP_NEW = """  if(typeof bindPortablePathHits==='function')bindPortablePathHits();
  if(typeof dbgPortableCards==='function')dbgPortableCards('setDisplayMode');
  if(typeof dbgMobileUi==='function')dbgMobileUi('setDisplayMode',{hyp:'H-P1'});
  if(window.CATALOG_PORTABLE){
    if(typeof portableEnsureScrollMenus==='function')portableEnsureScrollMenus();
    if(typeof syncPortableBrowserFs==='function')syncPortableBrowserFs();
    if(typeof placePortableHandles==='function')placePortableHandles();
    if(typeof dbgPortableScroll==='function')dbgPortableScroll('setDisplayMode',{hyp:'H-FS1'});
  }
}
window.setDisplayMode=setDisplayMode;"""

PARK_OLD = """function parkSearchStrip(){
  var strip=document.getElementById('searchStrip');
  var sh=acShell();
  var anchor=document.querySelector('.search-strip-anchor');
  if(!strip)return;
  if(acFsWanted){"""

PARK_NEW = """function parkSearchStrip(){
  var strip=document.getElementById('searchStrip');
  var sh=acShell();
  var anchor=document.querySelector('.search-strip-anchor');
  if(!strip)return;
  if(window.CATALOG_PORTABLE){
    if(anchor&&strip.parentNode!==anchor){
      if(sh&&sh.parentNode===anchor)anchor.insertBefore(strip,sh);
      else if(anchor.firstChild)anchor.insertBefore(strip,anchor.firstChild);
      else anchor.appendChild(strip);
    }
    return;
  }
  if(acFsWanted){"""

PLACE_OLD = """function placeAcShell(){
  var sh=acShell();
  if(!sh)return;
  syncAcFsBtn();
  parkSearchStrip();"""

PLACE_NEW = """function placeAcShell(){
  if(window.CATALOG_PORTABLE){
    var shP=typeof acShell==='function'?acShell():document.getElementById('acShell');
    var acP=document.getElementById('acList');
    if(typeof parkSearchStrip==='function')parkSearchStrip();
    if(acP){acP.classList.add('open');acP.style.removeProperty('max-height');acP.style.removeProperty('height');}
    if(shP){
      shP.classList.add('open');
      shP.classList.remove('ac-fixed');
      ['top','left','right','bottom','width','height','max-width','max-height'].forEach(function(p){shP.style.removeProperty(p);});
      if(document.body.classList.contains('display-fs')&&!document.body.classList.contains('search-chrome-collapsed')){
        shP.classList.add('ac-fs');
        document.body.classList.add('ac-fs-open');
      }else if(!document.body.classList.contains('display-fs')){
        shP.classList.remove('ac-fs');
      }
    }
    if(typeof syncAcFsBtn==='function')syncAcFsBtn();
    if(typeof syncAcWidthBtn==='function')syncAcWidthBtn();
    // #region agent log
    if(typeof dbgPortableScroll==='function')dbgPortableScroll('placeAcShell',{hyp:'H-SCR1'});
    // #endregion
    return;
  }
  var sh=acShell();
  if(!sh)return;
  syncAcFsBtn();
  parkSearchStrip();"""


def replace_css(text: str) -> str:
    if CSS_MARK in text and CSS_END in text:
        start = text.index(CSS_MARK)
        end = text.index(CSS_END) + len(CSS_END)
        return text[:start] + CSS.strip() + text[end:]
    needle = "</style></head>"
    if needle not in text:
        raise SystemExit("missing </style></head>")
    return text.replace(needle, CSS + "\n</style></head>", 1)


def sub(text: str, old: str, new: str, label: str) -> str:
    if old in text:
        n = text.count(old)
        if n != 1:
            raise SystemExit(f"{label} count={n}")
        return text.replace(old, new, 1)
    if new in text:
        return text
    if label in ("placeAc", "park", "setDisplay", "layout-edit", "search-more", "hdr-more", "kw-more"):
        return text
    raise SystemExit(f"missing snippet {label}:\n{old[:160]}")


ENSURE_LIVE_OLD = """function portableEnsureScrollMenus(){
  if(!window.CATALOG_PORTABLE)return;
  var ac=document.getElementById('acList');
  var sh=document.getElementById('acShell');
  var fw=document.getElementById('filterWrap');
  if(ac)ac.classList.add('open');
  if(sh){
    sh.classList.add('open');
    sh.classList.remove('ac-fixed');
    ['top','left','right','bottom','width','height','max-width','max-height'].forEach(function(p){sh.style.removeProperty(p);});
    if(document.body.classList.contains('display-fs')&&!document.body.classList.contains('search-chrome-collapsed'))sh.classList.add('ac-fs');
    else sh.classList.remove('ac-fs');
  }
  if(document.body.classList.contains('display-middle')&&fw){
    fw.classList.add('open');
    document.body.classList.add('kw-open');
    document.body.classList.remove('kw-chrome-collapsed');
  }
}"""

ENSURE_LIVE_NEW = """function portableEnsureScrollMenus(){
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
    var searchOn=!document.body.classList.contains('search-chrome-collapsed');
    var kwOn=!document.body.classList.contains('kw-chrome-collapsed');
    if(typeof acFsWanted!=='undefined')acFsWanted=!!searchOn;
    if(typeof kwFsWanted!=='undefined')kwFsWanted=!!kwOn;
    document.body.classList.toggle('ac-fs-open',searchOn);
    document.body.classList.toggle('kw-fs-open',kwOn);
    document.body.classList.toggle('dual-fs-open',searchOn&&kwOn);
    document.body.classList.toggle('kw-open',kwOn);
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

PLACE_LIVE_OLD = """      if(document.body.classList.contains('display-fs')&&!document.body.classList.contains('search-chrome-collapsed'))shP.classList.add('ac-fs');
      else shP.classList.remove('ac-fs');"""

PLACE_LIVE_NEW = """      if(document.body.classList.contains('display-fs')&&!document.body.classList.contains('search-chrome-collapsed')){
        shP.classList.add('ac-fs');
        document.body.classList.add('ac-fs-open');
      }else if(!document.body.classList.contains('display-fs')){
        shP.classList.remove('ac-fs');
      }"""


def patch(text: str) -> str:
    text = replace_css(text)
    if JS_MARK not in text:
        anchor = "window.placePortableHandles=placePortableHandles;"
        if anchor not in text:
            raise SystemExit("missing placePortableHandles assign")
        text = text.replace(anchor, anchor + "\n" + JS, 1)
    swaps = [
        (SEARCH_MORE_OLD, SEARCH_MORE_NEW, "search-more"),
        (HDR_MORE_OLD, HDR_MORE_NEW, "hdr-more"),
        (KW_MORE_OLD, KW_MORE_NEW, "kw-more"),
        (LAYOUT_OLD, LAYOUT_NEW, "layout-edit"),
        (SETDISP_OLD, SETDISP_NEW, "setDisplay"),
        (PARK_OLD, PARK_NEW, "park"),
        (PLACE_OLD, PLACE_NEW, "placeAc"),
        (ENSURE_LIVE_OLD, ENSURE_LIVE_NEW, "ensure-live"),
        (PLACE_LIVE_OLD, PLACE_LIVE_NEW, "place-live"),
    ]
    for old, new, label in swaps:
        text = sub(text, old, new, label)
    return text


def main():
    for path in FILES:
        raw = path.read_text(encoding="utf-8")
        out = patch(raw)
        path.write_text(out, encoding="utf-8")
        print("patched", path.name, "delta", len(out) - len(raw))


if __name__ == "__main__":
    main()
