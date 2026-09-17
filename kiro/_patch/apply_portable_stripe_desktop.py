#!/usr/bin/env python3
"""Portable: menu stripe + resize edges, History label, no Pick/glass dead ends."""
from pathlib import Path

ROOT = Path("/home/phnx/kiro-kontakt-patch")
FILES = [
    ROOT / "public/catalogs/DS-CATALOG-portable.html",
    ROOT / "public/catalogs/KONTAKT-CATALOG-portable.html",
]

CSS_MARK = "/* fix-PORTABLE-STRIPE-DESKTOP:"
CSS = r"""
/* fix-PORTABLE-STRIPE-DESKTOP: always-visible resize stripes, one-menu fill, no Pick/glass */
@media all{
  body.catalog-portable{
    --portable-stripe:8px
  }
  body.catalog-portable .mode-switch,
  body.catalog-portable .fs-mode-nav,
  body.catalog-portable #acFsModeNav,
  body.catalog-portable #kwFsModeNav,
  body.catalog-portable .ac-companion-btn,
  body.catalog-portable #acCompanionBtn{display:none!important}
  body.catalog-portable #searchStrip #searchHistoryWrap,
  body.catalog-portable .search-strip #searchHistoryWrap,
  body.catalog-portable.display-sides .search-strip #searchHistoryWrap,
  body.catalog-portable.display-fs .search-strip #searchHistoryWrap{
    display:inline-flex!important;align-items:center;flex:0 0 auto;position:relative;z-index:2
  }
  body.catalog-portable #searchHistory,
  body.catalog-portable .ac-history-btn{
    min-width:auto;padding:0 .55rem;white-space:nowrap
  }
  body.catalog-portable.display-sides:not(.display-middle){
    grid-template-columns:minmax(0,var(--portable-lw,42%)) minmax(0,1fr)!important
  }
  body.catalog-portable.display-sides:not(.display-middle).kw-open:not(.kw-chrome-collapsed):not(.search-chrome-collapsed){
    grid-template-columns:minmax(0,var(--portable-lw,1fr)) minmax(0,1fr)!important
  }
  body.catalog-portable.display-sides:not(.display-middle).search-chrome-collapsed.kw-open:not(.kw-chrome-collapsed){
    grid-template-columns:minmax(0,1fr) minmax(0,var(--portable-rw,42%))!important
  }
  body.catalog-portable.display-sides:not(.display-middle).sides-portrait-flip:not(.search-chrome-collapsed):not(.kw-open){
    grid-template-columns:minmax(0,1fr) minmax(0,var(--portable-lw,42%))!important
  }
  body.catalog-portable.display-sides:not(.display-middle).search-chrome-collapsed.kw-open.sides-portrait-flip{
    grid-template-columns:minmax(0,var(--portable-rw,42%)) minmax(0,1fr)!important
  }
  body.catalog-portable.display-fs.dual-fs-open,
  body.catalog-portable.display-fs.ac-fs-open.kw-fs-open{
    grid-template-columns:minmax(0,var(--portable-lw,1fr)) minmax(0,1fr)!important
  }
  body.catalog-portable.display-fs:not(.dual-fs-open),
  body.catalog-portable.display-fs.search-chrome-collapsed:not(.kw-fs-open):not(.ac-fs-open){
    grid-template-columns:minmax(0,1fr)!important
  }
  body.catalog-portable.display-fs:not(.dual-fs-open).ac-fs-open #searchChrome,
  body.catalog-portable.display-fs:not(.dual-fs-open).ac-fs-open #acShell,
  body.catalog-portable.display-fs:not(.dual-fs-open).ac-fs-open #acShell.ac-fs,
  body.catalog-portable.sides-portrait-flip.display-fs:not(.dual-fs-open).ac-fs-open #searchChrome,
  body.catalog-portable.sides-portrait-flip.display-fs:not(.dual-fs-open).ac-fs-open #acShell,
  body.catalog-portable.sides-portrait-flip.display-fs:not(.dual-fs-open).ac-fs-open #acShell.ac-fs,
  body.catalog-portable.display-fs.search-chrome-collapsed:not(.kw-fs-open).ac-fs-open #searchChrome{
    grid-column:1/-1!important
  }
  body.catalog-portable.display-fs:not(.dual-fs-open).kw-fs-open #filterWrap,
  body.catalog-portable.sides-portrait-flip.display-fs:not(.dual-fs-open).kw-fs-open #filterWrap,
  body.catalog-portable.display-fs.search-chrome-collapsed.kw-fs-open:not(.ac-fs-open) #filterWrap,
  body.catalog-portable.sides-portrait-flip.display-fs.search-chrome-collapsed.kw-fs-open #filterWrap{
    grid-column:1/-1!important
  }
  body.catalog-portable.display-fs:not(.ac-fs-open):not(.search-chrome-collapsed).kw-fs-open #filterWrap,
  body.catalog-portable.display-fs:not(.kw-fs-open).ac-fs-open #searchChrome{
    grid-column:1/-1!important
  }
  body.catalog-portable #searchSplit,
  body.catalog-portable #dualFsSep{
    box-sizing:border-box!important;
    background:var(--bg-surface,#111)!important;
    border:0!important;
    opacity:1!important;
    pointer-events:auto!important;
    z-index:90!important
  }
  body.catalog-portable.search-mode:not(.layout-edit) #searchSplit.port-stripe-v,
  body.catalog-portable.search-mode:not(.layout-edit) #searchSplit.port-stripe-h,
  body.catalog-portable.search-mode:not(.layout-edit) #dualFsSep.port-stripe-v,
  body.catalog-portable.search-mode:not(.layout-edit) #dualFsSep.port-stripe-h,
  body.catalog-portable #searchSplit.port-stripe-v,
  body.catalog-portable #searchSplit.port-stripe-h,
  body.catalog-portable #dualFsSep.port-stripe-v,
  body.catalog-portable #dualFsSep.port-stripe-h{
    display:block!important;
    pointer-events:auto!important;
    opacity:1!important
  }
  body.catalog-portable #searchSplit::before,
  body.catalog-portable #dualFsSep::before{
    content:"";
    position:absolute;
    background:var(--border);
    border-radius:1px;
    opacity:1!important;
    pointer-events:none
  }
  body.catalog-portable #searchSplit.port-stripe-v::before,
  body.catalog-portable #dualFsSep.port-stripe-v::before{
    top:16%;bottom:16%;left:3px;width:2px;height:auto;right:auto
  }
  body.catalog-portable #searchSplit.port-stripe-h::before,
  body.catalog-portable #dualFsSep.port-stripe-h::before{
    left:22%;right:22%;top:3px;height:2px;width:auto;bottom:auto
  }
  body.catalog-portable #searchSplit:hover::before,
  body.catalog-portable #dualFsSep:hover::before,
  body.catalog-portable #searchSplit.port-stripe-drag::before,
  body.catalog-portable #dualFsSep.port-stripe-drag::before{
    background:var(--accent-instrument);opacity:1!important
  }
  body.catalog-portable.display-sides #catalogIndex:not(.is-collapsed) #indexHeight{
    display:block!important;pointer-events:auto!important;cursor:row-resize;z-index:24
  }
  body.catalog-portable.display-sides #catalogIndex:not(.is-collapsed) #indexHeight::before{
    opacity:1!important;background:var(--border)
  }
}
@media(orientation:portrait){
  body.catalog-portable.display-sides:not(.display-middle).kw-open:not(.kw-chrome-collapsed):not(.search-chrome-collapsed):not(.dual-fs-open){
    grid-template-columns:minmax(0,var(--portable-lw,42%)) minmax(0,1fr)!important;
    grid-template-rows:auto minmax(0,var(--portable-menu-h,1fr)) minmax(0,1fr)!important
  }
  body.catalog-portable.display-sides:not(.display-middle).kw-open:not(.search-chrome-collapsed):not(.dual-fs-open).sides-portrait-flip{
    grid-template-columns:minmax(0,1fr) minmax(0,var(--portable-lw,42%))!important
  }
}
@media(orientation:landscape){
  body.catalog-portable.display-sides:not(.display-middle).kw-open:not(.kw-chrome-collapsed):not(.search-chrome-collapsed){
    grid-template-columns:minmax(0,var(--portable-lw,1fr)) minmax(0,1fr)!important
  }
}
"""

JS_MARK = "function placePortableHandles(){"

JS = r"""
function portableMenusOn(){
  var fs=document.body.classList.contains('display-fs');
  var fw=document.getElementById('filterWrap');
  var searchOn=fs
    ?(document.body.classList.contains('ac-fs-open')&&!document.body.classList.contains('search-chrome-collapsed'))
    :!document.body.classList.contains('search-chrome-collapsed');
  var kwOn=fs
    ?(document.body.classList.contains('kw-fs-open')&&!document.body.classList.contains('kw-chrome-collapsed'))
    :(!document.body.classList.contains('kw-chrome-collapsed')&&!!(fw&&(fw.classList.contains('open')||document.body.classList.contains('kw-open'))));
  return {searchOn:!!searchOn,kwOn:!!kwOn,both:!!(searchOn&&kwOn)};
}
function placePortableHistory(){
  if(!window.CATALOG_PORTABLE)return;
  var wrap=document.getElementById('searchHistoryWrap');
  var strip=document.getElementById('searchStrip');
  var more=document.getElementById('searchStripMore');
  if(wrap&&strip&&more&&wrap.parentElement!==strip)strip.insertBefore(wrap,more);
  else if(wrap&&strip&&!more&&wrap.parentElement!==strip)strip.appendChild(wrap);
  var btn=document.getElementById('searchHistory');
  if(btn){
    btn.setAttribute('aria-label','History');
    btn.setAttribute('title','History');
    btn.textContent='History';
  }
  fitPortableHistory();
}
function fitPortableHistory(){
  var btn=document.getElementById('searchHistory');
  var strip=document.getElementById('searchStrip');
  if(!btn||!strip)return;
  btn.textContent='History';
  if(strip.scrollWidth>strip.clientWidth+4)btn.textContent='H';
}
function clampPortableVars(){
  var vw=window.innerWidth||400;
  var cap=Math.round(vw*0.72);
  ['--portable-lw','--portable-rw'].forEach(function(p){
    var v=parseInt(getComputedStyle(document.documentElement).getPropertyValue(p),10);
    if(v&&v>cap)document.documentElement.style.setProperty(p,Math.round(vw*0.42)+'px');
  });
  var vh=window.innerHeight||800;
  var mh=parseInt(getComputedStyle(document.documentElement).getPropertyValue('--portable-menu-h'),10);
  if(mh&&mh>vh*0.55)document.documentElement.style.setProperty('--portable-menu-h',Math.round(vh*0.32)+'px');
}
function placePortableHandles(){
  if(!window.CATALOG_PORTABLE)return;
  clampPortableVars();
  var split=document.getElementById('searchSplit');
  var sep=document.getElementById('dualFsSep');
  var ch=document.getElementById('searchChrome');
  var fw=document.getElementById('filterWrap');
  var hdr=document.querySelector('.catalog-header');
  var top=hdr?Math.round(hdr.getBoundingClientRect().bottom):56;
  var m=portableMenusOn();
  var sides=document.body.classList.contains('display-sides');
  var fs=document.body.classList.contains('display-fs');
  var middle=document.body.classList.contains('display-middle');
  var portrait=!!(window.matchMedia&&window.matchMedia('(orientation:portrait)').matches);
  var flip=document.body.classList.contains('sides-portrait-flip');
  function hide(el){
    if(!el)return;
    el.classList.remove('port-stripe-v','port-stripe-h','port-stripe-drag');
    el.style.setProperty('display','none','important');
  }
  function bar(el,vert,box){
    if(!el||!box)return;
    el.classList.toggle('port-stripe-v',!!vert);
    el.classList.toggle('port-stripe-h',!vert);
    if(vert){
      el.style.cssText='display:block;position:fixed;top:'+top+'px;bottom:0;left:'+Math.round(box.x-4)+'px;width:8px;min-width:8px;max-width:8px;height:auto;z-index:90;margin:0;transform:none;pointer-events:auto;cursor:col-resize;background:var(--bg-surface);';
    }else{
      el.style.cssText='display:block;position:fixed;left:'+Math.round(box.x)+'px;width:'+Math.round(box.w)+'px;top:'+Math.round(box.y-4)+'px;height:8px;min-height:8px;max-height:8px;min-width:0;max-width:none;bottom:auto;z-index:90;margin:0;transform:none;pointer-events:auto;cursor:row-resize;background:var(--bg-surface);';
    }
    el.setAttribute('aria-orientation',vert?'vertical':'horizontal');
  }
  hide(split);hide(sep);
  if(fs){
    if(m.both&&ch&&fw){
      var left=flip?fw:ch;
      var r=left.getBoundingClientRect();
      bar(sep,true,{x:r.right});
    }
  }else if(sides&&middle){
    if(m.both&&ch){
      var rm=ch.getBoundingClientRect();
      bar(sep,true,{x:rm.right});
      bar(split,false,{x:rm.left,w:rm.width,y:rm.bottom});
    }else if(m.searchOn&&ch){
      var rs=ch.getBoundingClientRect();
      bar(split,false,{x:rs.left,w:rs.width,y:rs.bottom});
    }else if(m.kwOn&&fw){
      var rk=fw.getBoundingClientRect();
      bar(sep,false,{x:rk.left,w:rk.width,y:rk.bottom});
    }
  }else if(sides){
    if(portrait&&m.both&&ch&&fw){
      var topPane=flip?fw:ch;
      var stack=flip?fw:ch;
      var rt=topPane.getBoundingClientRect();
      var rst=stack.getBoundingClientRect();
      bar(split,false,{x:rt.left,w:rt.width,y:rt.bottom});
      bar(sep,true,{x:flip?rst.left:rst.right});
    }else if(!portrait&&m.both&&ch&&fw){
      var lp=flip?fw:ch;
      bar(sep,true,{x:lp.getBoundingClientRect().right});
    }else if(m.searchOn&&!m.kwOn&&ch){
      var rc=ch.getBoundingClientRect();
      bar(split,true,{x:flip?rc.left:rc.right});
    }else if(!m.searchOn&&m.kwOn&&fw){
      var rf=fw.getBoundingClientRect();
      bar(sep,true,{x:flip?rf.right:rf.left});
    }
  }
  var ix=document.getElementById('catalogIndex');
  var ixH=document.getElementById('indexHeight');
  if(ixH&&ix&&!ix.classList.contains('is-collapsed')&&sides){
    ixH.style.setProperty('display','block','important');
    ixH.style.setProperty('pointer-events','auto','important');
  }
  // #region agent log
  if(typeof dbgMobileUi==='function')dbgMobileUi('portable-stripe',{hyp:'H-STRIPE'});
  // #endregion
}
window.portableMenusOn=portableMenusOn;
window.placePortableHistory=placePortableHistory;
window.fitPortableHistory=fitPortableHistory;
window.clampPortableVars=clampPortableVars;
window.placePortableHandles=placePortableHandles;
"""

HDR_SEARCH_OLD = """function toggleHdrSearch(){
  if(typeof toggleSearchChrome==='function')toggleSearchChrome();
  else if(document.body.classList.contains('search-chrome-collapsed')){if(typeof expandSearchMenu==='function')expandSearchMenu();}
  else if(typeof collapseSearchMenu==='function')collapseSearchMenu();
  syncHdrMenuBtns();
}
function toggleHdrKw(){
  if(document.body.classList.contains('display-sides')){
    if(typeof toggleKwChrome==='function')toggleKwChrome();
  }else if(typeof toggleFilter==='function'){
    var w=document.getElementById('filterWrap');
    if(document.body.classList.contains('kw-chrome-collapsed')&&typeof expandKwMenu==='function')expandKwMenu();
    else toggleFilter();
  }
  syncHdrMenuBtns();
}"""

HDR_SEARCH_NEW = """function toggleHdrSearch(){
  if(window.CATALOG_PORTABLE&&document.body.classList.contains('display-fs')){
    var on=document.body.classList.contains('ac-fs-open')&&!document.body.classList.contains('search-chrome-collapsed');
    if(on){
      document.body.classList.add('search-chrome-collapsed');
      if(typeof acFsWanted!=='undefined')acFsWanted=false;
      if(typeof setAcFullscreen==='function')setAcFullscreen(false);
    }else{
      document.body.classList.remove('search-chrome-collapsed');
      if(typeof setAcFullscreen==='function')setAcFullscreen(true);
    }
    if(typeof updateDualState==='function')updateDualState();
    if(typeof placePortableHandles==='function')placePortableHandles();
    syncHdrMenuBtns();
    // #region agent log
    if(typeof dbgMobileUi==='function')dbgMobileUi('hdr-search-fs',{hyp:'H-FILL'});
    // #endregion
    return;
  }
  if(typeof toggleSearchChrome==='function')toggleSearchChrome();
  else if(document.body.classList.contains('search-chrome-collapsed')){if(typeof expandSearchMenu==='function')expandSearchMenu();}
  else if(typeof collapseSearchMenu==='function')collapseSearchMenu();
  if(typeof placePortableHandles==='function')placePortableHandles();
  syncHdrMenuBtns();
}
function toggleHdrKw(){
  if(window.CATALOG_PORTABLE&&document.body.classList.contains('display-fs')){
    var kon=document.body.classList.contains('kw-fs-open')&&!document.body.classList.contains('kw-chrome-collapsed');
    if(kon){
      if(typeof setKwFullscreen==='function')setKwFullscreen(false);
      document.body.classList.add('kw-chrome-collapsed');
      document.body.classList.remove('kw-open');
    }else{
      document.body.classList.remove('kw-chrome-collapsed');
      if(typeof setKwFullscreen==='function')setKwFullscreen(true);
    }
    if(typeof updateDualState==='function')updateDualState();
    if(typeof placePortableHandles==='function')placePortableHandles();
    syncHdrMenuBtns();
    // #region agent log
    if(typeof dbgMobileUi==='function')dbgMobileUi('hdr-kw-fs',{hyp:'H-FILL'});
    // #endregion
    return;
  }
  if(document.body.classList.contains('display-sides')){
    if(typeof toggleKwChrome==='function')toggleKwChrome();
  }else if(typeof toggleFilter==='function'){
    var w=document.getElementById('filterWrap');
    if(document.body.classList.contains('kw-chrome-collapsed')&&typeof expandKwMenu==='function')expandKwMenu();
    else toggleFilter();
  }
  if(typeof placePortableHandles==='function')placePortableHandles();
  syncHdrMenuBtns();
}"""

SYNC_OLD = """function syncHdrMenuBtns(){
  var searchOn=!document.body.classList.contains('search-chrome-collapsed');
  var fw=document.getElementById('filterWrap');
  var kwOn=!document.body.classList.contains('kw-chrome-collapsed')&&!!(fw&&fw.classList.contains('open'));"""

SYNC_NEW = """function syncHdrMenuBtns(){
  var fs=document.body.classList.contains('display-fs');
  var searchOn=fs
    ?(document.body.classList.contains('ac-fs-open')&&!document.body.classList.contains('search-chrome-collapsed'))
    :!document.body.classList.contains('search-chrome-collapsed');
  var fw=document.getElementById('filterWrap');
  var kwOn=fs
    ?(document.body.classList.contains('kw-fs-open')&&!document.body.classList.contains('kw-chrome-collapsed'))
    :(!document.body.classList.contains('kw-chrome-collapsed')&&!!(fw&&fw.classList.contains('open')));"""

SEARCH_MORE_OLD = """    add('Clear',function(){if(typeof clearAllFilters==='function')clearAllFilters();},'Clear search');
    add('H',function(){var h=document.getElementById('searchHistory');if(h)h.click();},'History');
    add('Pick',function(){if(typeof setMode==='function')setMode('pick');});
    add('Search',function(){if(typeof setMode==='function')setMode('search');});"""

SEARCH_MORE_NEW = """    add('Clear',function(){if(typeof clearAllFilters==='function')clearAllFilters();},'Clear search');
    add('History',function(){var h=document.getElementById('searchHistory');if(h)h.click();},'History');"""

KW_MORE_OLD = """  phoneMoreAdd(pop,'Clear',function(){if(typeof clearAllFilters==='function')clearAllFilters();},'Clear keywords');
  phoneMoreAdd(pop,'Pick',function(){if(typeof setMode==='function')setMode('pick');});
  phoneMoreAdd(pop,'Search',function(){if(typeof setMode==='function')setMode('search');});"""

KW_MORE_NEW = """  phoneMoreAdd(pop,'Clear',function(){if(typeof clearAllFilters==='function')clearAllFilters();},'Clear keywords');
  phoneMoreAdd(pop,'History',function(){var h=document.getElementById('searchHistory');if(h)h.click();},'History');"""

HDR_MORE_OLD = """  phoneMoreAdd(pop,'Miss',function(){var x=document.getElementById('clearMissBtn');if(x)x.click();},'Clear on miss');
  phoneMoreAdd(pop,'Flip',function(){if(typeof togglePortraitSidesFlip==='function')togglePortraitSidesFlip();},'Flip panes');
  var sel=document.getElementById('themePicker');"""

HDR_MORE_NEW = """  phoneMoreAdd(pop,'Miss',function(){var x=document.getElementById('clearMissBtn');if(x)x.click();},'Clear on miss');
  phoneMoreAdd(pop,'Flip',function(){if(typeof togglePortraitSidesFlip==='function')togglePortraitSidesFlip();},'Flip panes');
  phoneMoreAdd(pop,'History',function(){var h=document.getElementById('searchHistory');if(h)h.click();},'History');
  var sel=document.getElementById('themePicker');"""

PLACE_SIDES_OLD = """function placeSidesHandles(){
  if(!document.body.classList.contains('display-sides'))return;"""

PLACE_SIDES_NEW = """function placeSidesHandles(){
  if(window.CATALOG_PORTABLE){
    if(typeof placePortableHandles==='function')placePortableHandles();
    return;
  }
  if(!document.body.classList.contains('display-sides'))return;"""

APPLY_SIDES_OLD = """  if(!document.body.classList.contains('display-sides')){
    document.body.style.removeProperty('--sides-lw');
    document.body.style.removeProperty('--sides-rw');
    document.body.style.removeProperty('--sides-index-h');
    document.body.classList.remove('kw-chrome-collapsed');
    ['searchSplit','dualFsSep'].forEach(function(id){var el=document.getElementById(id);if(el)el.removeAttribute('style');});"""

APPLY_SIDES_NEW = """  if(!document.body.classList.contains('display-sides')){
    document.body.style.removeProperty('--sides-lw');
    document.body.style.removeProperty('--sides-rw');
    document.body.style.removeProperty('--sides-index-h');
    document.body.classList.remove('kw-chrome-collapsed');
    if(window.CATALOG_PORTABLE&&document.body.classList.contains('display-fs')){
      if(typeof placePortableHandles==='function')placePortableHandles();
    }else{
      ['searchSplit','dualFsSep'].forEach(function(id){var el=document.getElementById(id);if(el)el.removeAttribute('style');});
    }"""

DUAL_PHONE_OLD = """  if(typeof isPhoneViewport==='function'&&isPhoneViewport()){
    if(sep)sep.style.display='none';
    syncNarrowPanels();
    return;
  }"""

DUAL_PHONE_NEW = """  if(typeof isPhoneViewport==='function'&&isPhoneViewport()){
    if(window.CATALOG_PORTABLE&&isDualFs()){
      var vwP=window.innerWidth||1200;
      var curP=parseInt(getComputedStyle(document.documentElement).getPropertyValue('--portable-lw'),10);
      var lwP=curP>80?curP:Math.round(vwP*(typeof dualRatio==='number'?dualRatio:0.5));
      document.documentElement.style.setProperty('--portable-lw',lwP+'px');
      if(typeof placePortableHandles==='function')placePortableHandles();
      syncNarrowPanels();
      return;
    }
    if(sep)sep.style.display='none';
    syncNarrowPanels();
    return;
  }"""

SEP_MOVE_OLD = """    dualRatio=x/vw;
    document.documentElement.style.setProperty('--dual-fs-lw',Math.round(x)+'px');
    sep.style.left=Math.round(x)+'px';
    if(typeof syncNarrowPanels==='function')syncNarrowPanels();"""

SEP_MOVE_OLD_MIN = (
    "    dualRatio=x/vw;document.documentElement.style.setProperty('--dual-fs-lw',Math.round(x)+'px');"
    "sep.style.left=Math.round(x)+'px';if(typeof syncNarrowPanels==='function')syncNarrowPanels();"
)

SEP_MOVE_NEW = """    dualRatio=x/vw;
    document.documentElement.style.setProperty('--dual-fs-lw',Math.round(x)+'px');
    if(window.CATALOG_PORTABLE)document.documentElement.style.setProperty('--portable-lw',Math.round(x)+'px');
    sep.style.left=Math.round(x)+'px';
    if(typeof placePortableHandles==='function')placePortableHandles();
    if(typeof syncNarrowPanels==='function')syncNarrowPanels();"""

SIDES_DOWN_OLD = """    if(!document.body.classList.contains('display-sides'))return;
    if(!document.body.classList.contains('layout-edit'))return;"""

SIDES_DOWN_NEW = """    if(!document.body.classList.contains('display-sides'))return;
    if(!window.CATALOG_PORTABLE&&!document.body.classList.contains('layout-edit'))return;"""

IDX_DOWN_OLD = """    if(!document.body.classList.contains('display-sides'))return;
    if(!document.body.classList.contains('layout-edit'))return;
    if(sidesPinned||(typeof modeLayoutPinned==='function'&&modeLayoutPinned()))return;
    if(e.pointerType==='mouse'&&e.button!=null&&e.button!==0)return;
    e.preventDefault();e.stopPropagation();
    var ix=document.getElementById('catalogIndex');"""

IDX_DOWN_NEW = """    if(!document.body.classList.contains('display-sides'))return;
    if(!window.CATALOG_PORTABLE&&!document.body.classList.contains('layout-edit'))return;
    if(sidesPinned||(typeof modeLayoutPinned==='function'&&modeLayoutPinned()))return;
    if(e.pointerType==='mouse'&&e.button!=null&&e.button!==0)return;
    e.preventDefault();e.stopPropagation();
    var ix=document.getElementById('catalogIndex');"""

FS_DOWN_OLD = """    if(!document.body.classList.contains('display-fs'))return;
    if(!document.body.classList.contains('layout-edit'))return;"""

FS_DOWN_NEW = """    if(!document.body.classList.contains('display-fs'))return;
    if(!window.CATALOG_PORTABLE&&!document.body.classList.contains('layout-edit'))return;"""

SIDES_ONDOWN_EXTRA_OLD = """    if(e.pointerType==='mouse'&&e.button!=null&&e.button!==0)return;
    e.preventDefault();e.stopPropagation();
    if(typeof displayIsMiddle==='function'?displayIsMiddle():document.body.classList.contains('display-middle')){"""

SIDES_ONDOWN_EXTRA_NEW = """    if(e.pointerType==='mouse'&&e.button!=null&&e.button!==0)return;
    e.preventDefault();e.stopPropagation();
    if(window.CATALOG_PORTABLE){
      var chP=document.getElementById('searchChrome');
      var fwP=document.getElementById('filterWrap');
      var mP=typeof portableMenusOn==='function'?portableMenusOn():{searchOn:true,kwOn:true,both:true};
      var flipP=document.body.classList.contains('sides-portrait-flip');
      var portP=!!(window.matchMedia&&window.matchMedia('(orientation:portrait)').matches);
      var midP=typeof displayIsMiddle==='function'?displayIsMiddle():document.body.classList.contains('display-middle');
      var horizP=(which==='split')&&(midP||(portP&&mP.both));
      var paneP=horizP?(which==='split'?chP:fwP):(mP.both?(flipP?fwP:chP):(mP.searchOn?chP:fwP));
      if(!paneP)return;
      var rP=paneP.getBoundingClientRect();
      var tP=e.currentTarget||e.target;
      drag={portable:true,horiz:horizP,which:which,x:e.clientX,y:e.clientY,w:rP.width,h:rP.height,flip:flipP,prop:(mP.searchOn&&!mP.kwOn)?'--portable-lw':((!mP.searchOn&&mP.kwOn)?'--portable-rw':'--portable-lw'),id:e.pointerId};
      try{if(tP&&tP.setPointerCapture)tP.setPointerCapture(e.pointerId);}catch(errP){}
      // #region agent log
      if(typeof dbgMobileUi==='function')dbgMobileUi('stripe-down',{hyp:'H-DRAG'});
      // #endregion
      return;
    }
    if(typeof displayIsMiddle==='function'?displayIsMiddle():document.body.classList.contains('display-middle')){"""

SIDES_MOVE_OLD = """  function onMove(e){
    if(!drag)return;
    if(drag.middle){"""

SIDES_MOVE_NEW = """  function onMove(e){
    if(!drag)return;
    if(drag.portable){
      var vwP=window.innerWidth||1200;
      var vhP=window.innerHeight||800;
      if(drag.horiz){
        var nh=Math.max(96,Math.min(Math.round(vhP*0.62),drag.h+(e.clientY-drag.y)));
        document.documentElement.style.setProperty('--portable-menu-h',nh+'px');
      }else{
        var dx=e.clientX-drag.x;
        var nl=drag.flip?drag.w-dx:drag.w+dx;
        nl=Math.max(140,Math.min(Math.round(vwP*0.82),nl));
        document.documentElement.style.setProperty(drag.prop,nl+'px');
      }
      if(typeof placePortableHandles==='function')placePortableHandles();
      return;
    }
    if(drag.middle){"""

SIDES_UP_OLD = """  function onUp(e){
    if(!drag)return;
    if(drag.middle){"""

SIDES_UP_NEW = """  function onUp(e){
    if(!drag)return;
    if(drag.portable){
      // #region agent log
      if(typeof dbgMobileUi==='function')dbgMobileUi('stripe-up',{hyp:'H-DRAG'});
      // #endregion
      drag=null;
      if(typeof placePortableHandles==='function')placePortableHandles();
      return;
    }
    if(drag.middle){"""

HIST_BTN_OLD = 'id="searchHistory" aria-haspopup="dialog" aria-expanded="false" aria-controls="historyCloud" title="History">H</button>'
HIST_BTN_NEW = 'id="searchHistory" aria-haspopup="dialog" aria-expanded="false" aria-controls="historyCloud" title="History" aria-label="History">History</button>'

BOOT_OLD = """var CATALOG_PORTABLE=true;window.CATALOG_PORTABLE=true;document.body.classList.add("catalog-portable");"""
BOOT_NEW = """var CATALOG_PORTABLE=true;window.CATALOG_PORTABLE=true;document.body.classList.add("catalog-portable");
(function bootPortableStripe(){
  function go(){
    if(typeof placePortableHistory==='function')placePortableHistory();
    if(typeof placePortableHandles==='function')placePortableHandles();
    if(typeof setMode==='function')setMode('search');
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',function(){setTimeout(go,0);});
  else setTimeout(go,0);
  window.addEventListener('resize',function(){
    if(typeof fitPortableHistory==='function')fitPortableHistory();
    if(typeof placePortableHandles==='function')placePortableHandles();
  },{passive:true});
})();"""


def patch(text: str) -> str:
    if CSS_MARK not in text:
        needle = "</style></head>"
        if needle not in text:
            raise SystemExit("missing </style></head>")
        text = text.replace(needle, CSS + needle, 1)
    if JS_MARK not in text:
        anchor = "window.toggleSearchStripMore=toggleSearchStripMore;"
        if anchor not in text:
            raise SystemExit("missing toggleSearchStripMore assign")
        text = text.replace(anchor, anchor + JS, 1)
    swaps = [
        (HDR_SEARCH_OLD, HDR_SEARCH_NEW),
        (SYNC_OLD, SYNC_NEW),
        (SEARCH_MORE_OLD, SEARCH_MORE_NEW),
        (KW_MORE_OLD, KW_MORE_NEW),
        (HDR_MORE_OLD, HDR_MORE_NEW),
        (PLACE_SIDES_OLD, PLACE_SIDES_NEW),
        (APPLY_SIDES_OLD, APPLY_SIDES_NEW),
        (DUAL_PHONE_OLD, DUAL_PHONE_NEW),
        (SEP_MOVE_OLD, SEP_MOVE_NEW),
        (SEP_MOVE_OLD_MIN, SEP_MOVE_NEW),
        (SIDES_DOWN_OLD, SIDES_DOWN_NEW),
        (IDX_DOWN_OLD, IDX_DOWN_NEW),
        (FS_DOWN_OLD, FS_DOWN_NEW),
        (SIDES_ONDOWN_EXTRA_OLD, SIDES_ONDOWN_EXTRA_NEW),
        (SIDES_MOVE_OLD, SIDES_MOVE_NEW),
        (SIDES_UP_OLD, SIDES_UP_NEW),
        (HIST_BTN_OLD, HIST_BTN_NEW),
        (BOOT_OLD, BOOT_NEW),
    ]
    for old, new in swaps:
        if old is BOOT_OLD and "bootPortableStripe" in text:
            continue
        if old in text:
            text = text.replace(old, new, 1)
            continue
        if new in text:
            continue
        if old in (SEP_MOVE_OLD, SEP_MOVE_OLD_MIN) and (
            SEP_MOVE_NEW in text or SEP_MOVE_OLD_MIN in text or SEP_MOVE_OLD in text
        ):
            continue
        raise SystemExit("missing snippet:\n" + old[:180])
    return text


def main():
    for path in FILES:
        raw = path.read_text(encoding="utf-8")
        out = patch(raw)
        path.write_text(out, encoding="utf-8")
        print("patched", path.name, "delta", len(out) - len(raw))


if __name__ == "__main__":
    main()
