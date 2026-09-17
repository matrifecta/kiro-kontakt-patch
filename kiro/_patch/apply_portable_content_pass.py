#!/usr/bin/env python3
"""Portable pass: content-only, dual ⛶, ⋯ bubble vs rows, cards, Middle FS."""
from pathlib import Path

ROOT = Path("/home/phnx/kiro-kontakt-patch/public/catalogs")
FILES = [ROOT / "DS-CATALOG-portable.html", ROOT / "KONTAKT-CATALOG-portable.html"]

CSS_MARK = "/* fix-PORTABLE-CONTENT-PASS:"
CSS = r"""
/* fix-PORTABLE-CONTENT-PASS: content-only, toolbar FS, ⋯ split, cards, Middle fill */
@media all{
  body.catalog-portable .display-btn[data-display="fs"],
  body.catalog-portable .display-switch{display:none!important}
  body.catalog-portable #hdrMoreBtn,
  body.catalog-portable #searchStripMore,
  body.catalog-portable #kwStripMore{display:inline-flex!important;visibility:visible!important;opacity:1!important}
  body.catalog-portable #hdrToolbarFs{
    display:inline-flex!important;align-items:center;justify-content:center;
    margin-left:auto;order:120;flex:0 0 auto;
    min-width:2.1rem;min-height:2.1rem;padding:0 .4rem;
    border:0;background:transparent;color:inherit;cursor:pointer;font-size:1.05rem
  }
  body.catalog-portable .hdr-cluster{display:flex!important;flex-wrap:wrap!important;align-items:center;gap:.25rem .4rem}
  body.catalog-portable.display-content,
  body.catalog-portable:not(.display-sides):not(.display-middle):not(.display-fs){
    display:flex!important;flex-direction:column!important
  }
  body.catalog-portable.display-content .catalog-header,
  body.catalog-portable:not(.display-sides):not(.display-middle):not(.display-fs) .catalog-header{flex:0 0 auto}
  body.catalog-portable.display-content #searchChrome,
  body.catalog-portable.display-content #filterWrap,
  body.catalog-portable.display-content #searchSplit,
  body.catalog-portable.display-content #dualFsSep,
  body.catalog-portable.display-content #searchHeight,
  body.catalog-portable:not(.display-sides):not(.display-middle):not(.display-fs) #searchChrome,
  body.catalog-portable:not(.display-sides):not(.display-middle):not(.display-fs) #filterWrap,
  body.catalog-portable:not(.display-sides):not(.display-middle):not(.display-fs) #searchSplit,
  body.catalog-portable:not(.display-sides):not(.display-middle):not(.display-fs) #dualFsSep{
    display:none!important
  }
  body.catalog-portable.display-content #catalogMain,
  body.catalog-portable:not(.display-sides):not(.display-middle):not(.display-fs) #catalogMain{
    display:block!important;flex:1 1 0%!important;min-height:0!important;width:100%!important;
    overflow-x:hidden!important;overflow-y:auto!important
  }
  body.catalog-portable.display-sides:not(.display-middle) #catalogMain .catalog-body,
  body.catalog-portable.display-sides:not(.display-middle) #catalogMain .loc-group{
    --cat-cols:1fr;grid-template-columns:1fr!important
  }
  body.catalog-portable.display-sides.display-middle #catalogMain .catalog-body,
  body.catalog-portable.display-sides.display-middle #catalogMain .loc-group,
  body.catalog-portable.display-content #catalogMain .catalog-body,
  body.catalog-portable.display-content #catalogMain .loc-group{
    grid-template-columns:repeat(2,minmax(0,1fr))!important
  }
  body.catalog-portable #searchInput{flex:1 1 8rem!important;min-width:8rem!important;max-width:100%}
  body.catalog-portable #searchStrip,
  body.catalog-portable #filterTop{
    display:flex!important;flex-wrap:wrap!important;align-items:center;overflow:visible!important
  }
  body.catalog-portable #searchStripMorePop:not([hidden]),
  body.catalog-portable #kwStripMorePop:not([hidden]){
    position:static!important;inset:auto!important;top:auto!important;right:auto!important;left:auto!important;
    float:none!important;transform:none!important;
    display:flex!important;flex-direction:row!important;flex-wrap:wrap!important;
    flex:1 1 100%!important;width:100%!important;max-width:100%!important;min-width:0!important;
    order:99!important;gap:.28rem;margin:.28rem 0 0;padding:.2rem 0;
    max-height:none!important;overflow:visible!important;
    box-shadow:none!important;background:transparent!important;z-index:1!important
  }
  body.catalog-portable #searchStripMorePop:not([hidden]) button,
  body.catalog-portable #kwStripMorePop:not([hidden]) button{
    width:auto!important;flex:0 0 auto;min-height:2rem;padding:.2rem .55rem;white-space:nowrap
  }
  body.catalog-portable #hdrMorePop:not([hidden]),
  body.catalog-portable .catalog-header>#hdrMorePop:not([hidden]){
    position:fixed!important;inset:auto!important;
    display:flex!important;flex-direction:column!important;
    flex:0 0 auto!important;width:min(22rem,calc(100vw - 1rem))!important;max-width:22rem!important;
    min-width:12rem!important;min-height:4rem!important;
    max-height:min(70dvh,28rem)!important;overflow-x:hidden!important;overflow-y:auto!important;
    z-index:420!important;order:0!important;margin:0!important;
    padding:.45rem;gap:.2rem;border-radius:10px;
    box-shadow:0 10px 32px rgba(0,0,0,.38)!important;
    background:var(--bg-surface,var(--bg,#1a1a1a))!important;
    border:1px solid var(--border,rgba(255,255,255,.12))
  }
  body.catalog-portable #hdrMorePop:not([hidden]) button{
    width:100%;min-height:2.25rem;text-align:left;white-space:nowrap
  }
  body.catalog-portable.display-sides.display-middle.kw-fs-open:not(.ac-fs-open) #catalogMain,
  body.catalog-portable.display-sides.display-middle.kw-fs-open:not(.ac-fs-open) #searchChrome,
  body.catalog-portable.display-sides.display-middle.ac-fs-open:not(.kw-fs-open) #catalogMain,
  body.catalog-portable.display-sides.display-middle.ac-fs-open:not(.kw-fs-open) #filterWrap{display:none!important}
  body.catalog-portable.display-sides.display-middle.kw-fs-open:not(.ac-fs-open) #filterWrap{
    display:flex!important;flex-direction:column!important;
    width:100%!important;max-width:none!important;min-width:0!important;
    height:auto!important;max-height:none!important;min-height:0!important;
    flex:1 1 0%!important;grid-column:1/-1!important;align-self:stretch!important
  }
  body.catalog-portable.display-sides.display-middle.ac-fs-open:not(.kw-fs-open) #searchChrome,
  body.catalog-portable.display-sides.display-middle.ac-fs-open:not(.kw-fs-open) #acShell{
    display:flex!important;flex-direction:column!important;
    width:100%!important;max-width:none!important;
    height:auto!important;max-height:none!important;min-height:0!important;
    flex:1 1 0%!important;grid-column:1/-1!important;align-self:stretch!important
  }
}
@media(orientation:portrait){
  body.catalog-portable.display-content #catalogMain .catalog-body,
  body.catalog-portable.display-content #catalogMain .loc-group,
  body.catalog-portable.display-sides.display-middle #catalogMain .catalog-body,
  body.catalog-portable.display-sides.display-middle #catalogMain .loc-group{
    grid-template-columns:1fr!important
  }
  @media(min-width:700px){
    body.catalog-portable.display-sides.display-middle #catalogMain .catalog-body,
    body.catalog-portable.display-sides.display-middle #catalogMain .loc-group,
    body.catalog-portable.display-content #catalogMain .catalog-body,
    body.catalog-portable.display-content #catalogMain .loc-group{
      grid-template-columns:repeat(2,minmax(0,1fr))!important
    }
  }
  body.catalog-portable #hdrMorePop:not([hidden]){
    left:.5rem!important;right:.5rem!important;width:auto!important;max-width:none!important
  }
}
@media(orientation:landscape){
  body.catalog-portable #hdrMorePop:not([hidden]){
    right:.5rem!important;left:auto!important;width:min(22rem,46vw)!important
  }
}
@container catmain (max-width: 22rem){
  body.catalog-portable.display-sides.display-middle #catalogMain .catalog-body,
  body.catalog-portable.display-sides.display-middle #catalogMain .loc-group,
  body.catalog-portable.display-content #catalogMain .catalog-body,
  body.catalog-portable.display-content #catalogMain .loc-group{
    grid-template-columns:1fr!important
  }
}
"""

HDR_FS_OLD = "</optgroup></select></div></div></div>"
HDR_FS_NEW = (
    '</optgroup></select><button type="button" class="hdr-toolbar-fs" id="hdrToolbarFs" '
    'aria-pressed="false" aria-label="Fullscreen arrangement" title="Fullscreen" '
    'onclick="event.preventDefault();event.stopPropagation();togglePortableToolbarFs()">'
    "&#x26F6;</button></div></div></div>"
)

SET_MODE_OLD = """  if(window.CATALOG_PORTABLE&&mode==='fs'){portableBoth=true;mode='sides';}
  if(mode!=='upper'&&mode!=='sides'&&mode!=='fs'&&mode!=='middle')mode='sides';
  if(mode==='upper')mode=(typeof isPhoneViewport==='function'&&isPhoneViewport())?'middle':'sides';
  if(mode==='fs'&&!(typeof isPhoneViewport==='function'&&isPhoneViewport()))mode='sides';
  var persistDisplay=mode;"""

SET_MODE_NEW = """  if(window.CATALOG_PORTABLE&&mode==='fs'){portableBoth=true;mode='sides';}
  var portableContent=!!(window.CATALOG_PORTABLE&&(mode==='content'||mode==='catalog'));
  if(portableContent)mode='content';
  else if(mode!=='upper'&&mode!=='sides'&&mode!=='fs'&&mode!=='middle')mode='sides';
  if(!portableContent&&mode==='upper')mode=(typeof isPhoneViewport==='function'&&isPhoneViewport())?'middle':'sides';
  if(!portableContent&&mode==='fs'&&!(typeof isPhoneViewport==='function'&&isPhoneViewport()))mode='sides';
  var persistDisplay=mode;"""

MIDDLE_TO_SIDES_OLD = """  if(opts.pick){
    try{
      if(typeof writeDisplayOrientPick==='function')writeDisplayOrientPick(persistDisplay);
      else localStorage.setItem(typeof displayPickKey==='function'?displayPickKey():('catalog-display-pick-'+(window.CATALOG_NS||'catalog')),'1');
    }catch(err){}
  }
  if(mode==='middle')mode='sides';"""
MIDDLE_TO_SIDES_NEW = """  if(opts.pick){
    try{
      if(typeof writeDisplayOrientPick==='function')writeDisplayOrientPick(persistDisplay);
      else localStorage.setItem(typeof displayPickKey==='function'?displayPickKey():('catalog-display-pick-'+(window.CATALOG_NS||'catalog')),'1');
    }catch(err){}
  }
  if(!portableContent&&mode==='middle')mode='sides';
  if(portableContent){
    currentDisplay='content';
    try{localStorage.setItem(DISPLAY_KEY,'content');}catch(errC){}
    document.body.classList.remove('display-upper','display-sides','display-fs','display-middle','ac-fs-open','kw-fs-open','dual-fs-open');
    document.body.classList.add('display-content');
    document.body.classList.add('search-chrome-collapsed','search-extras-collapsed','kw-chrome-collapsed');
    document.body.classList.remove('kw-open');
    var fwC=document.getElementById('filterWrap');
    if(fwC)fwC.classList.remove('open');
    var shC=document.getElementById('acShell');
    if(shC)shC.classList.remove('ac-fs','ac-fixed');
    if(typeof acFsWanted!=='undefined')acFsWanted=false;
    if(typeof kwFsWanted!=='undefined')kwFsWanted=false;
    if(typeof ensureCatalogMain==='function')ensureCatalogMain();
    if(typeof applyAll==='function')applyAll();
    if(typeof syncHdrMenuBtns==='function')syncHdrMenuBtns();
    if(typeof syncDisplayBtns==='function')syncDisplayBtns();
    if(typeof portableEnsureScrollMenus==='function')portableEnsureScrollMenus();
    if(typeof placePortableHandles==='function')placePortableHandles();
    if(typeof placeCatalogJumpStack==='function')placeCatalogJumpStack();
    if(typeof bindPortablePathHits==='function')bindPortablePathHits();
    return;
  }"""

SIDES_FORCE_OLD = """  if(mode==='sides'){
    var wasCol=document.body.classList.contains('search-chrome-collapsed');
    var wasKw=document.body.classList.contains('kw-chrome-collapsed');
    var ixPre=document.getElementById('catalogIndex');
    var ilPre=document.getElementById('catalogIndexList');
    document.body.classList.remove('search-chrome-collapsed','search-extras-collapsed','kw-chrome-collapsed');
    var fwPre=document.getElementById('filterWrap');
    if(fwPre){if(displayIsDesktop()){fwPre.classList.add('open');document.body.classList.add('kw-open');}else{fwPre.classList.remove('open');document.body.classList.remove('kw-open');}}
    var aPre=document.querySelector('#filterToggle .toggle-arrow')||document.querySelector('.toggle-arrow');
    if(aPre)aPre.textContent='▲';
    if(typeof syncSearchHideBtn==='function')syncSearchHideBtn();
    if(typeof syncKwHideBtn==='function')syncKwHideBtn();
    if(typeof resetIndexDock==='function')resetIndexDock();
    if(typeof syncHdrMenuBtns==='function')syncHdrMenuBtns();
    if(typeof syncIndexEmbedBtn==='function')syncIndexEmbedBtn();

  }else{
    document.body.classList.remove('kw-chrome-collapsed');
  }"""

SIDES_FORCE_NEW = """  if(mode==='sides'){
    var wasCol=document.body.classList.contains('search-chrome-collapsed');
    var wasKw=document.body.classList.contains('kw-chrome-collapsed');
    var ixPre=document.getElementById('catalogIndex');
    var ilPre=document.getElementById('catalogIndexList');
    if(!(window.CATALOG_PORTABLE&&opts.keepMenus)){
      document.body.classList.remove('search-chrome-collapsed','search-extras-collapsed','kw-chrome-collapsed');
      var fwPre=document.getElementById('filterWrap');
      if(fwPre){if(displayIsDesktop()){fwPre.classList.add('open');document.body.classList.add('kw-open');}else{fwPre.classList.remove('open');document.body.classList.remove('kw-open');}}
    }
    var aPre=document.querySelector('#filterToggle .toggle-arrow')||document.querySelector('.toggle-arrow');
    if(aPre)aPre.textContent='▲';
    if(typeof syncSearchHideBtn==='function')syncSearchHideBtn();
    if(typeof syncKwHideBtn==='function')syncKwHideBtn();
    if(typeof resetIndexDock==='function')resetIndexDock();
    if(typeof syncHdrMenuBtns==='function')syncHdrMenuBtns();
    if(typeof syncIndexEmbedBtn==='function')syncIndexEmbedBtn();

  }else{
    if(!(window.CATALOG_PORTABLE&&opts.keepMenus))document.body.classList.remove('kw-chrome-collapsed');
  }"""

SIDES_OPEN_OLD = """    if(typeof bindCatalogTop==='function')bindCatalogTop();
    document.body.classList.remove('search-chrome-collapsed','search-extras-collapsed');
    var ac=document.getElementById('acList'),sh=document.getElementById('acShell');"""

SIDES_OPEN_NEW = """    if(typeof bindCatalogTop==='function')bindCatalogTop();
    if(!(window.CATALOG_PORTABLE&&opts.keepMenus))document.body.classList.remove('search-chrome-collapsed','search-extras-collapsed');
    var ac=document.getElementById('acList'),sh=document.getElementById('acShell');"""

SIDES_KW_OLD = """    var fw=document.getElementById('filterWrap');
    if(fw){
      if(displayIsDesktop()){fw.classList.add('open');document.body.classList.add('kw-open');}
      else{fw.classList.remove('open');document.body.classList.remove('kw-open');}
      if(typeof clearShadeBox==='function')clearShadeBox(fw);"""

SIDES_KW_NEW = """    var fw=document.getElementById('filterWrap');
    if(fw && !(window.CATALOG_PORTABLE&&opts.keepMenus)){
      if(displayIsDesktop()){fw.classList.add('open');document.body.classList.add('kw-open');}
      else{fw.classList.remove('open');document.body.classList.remove('kw-open');}
      if(typeof clearShadeBox==='function')clearShadeBox(fw);"""

ORIENT_OLD = """  if(hold)next='sides';
  else if(window.CATALOG_PORTABLE&&next==='middle'&&o!=='portrait')next='sides';"""

ORIENT_NEW = """  if(hold)next='sides';
  else if(window.CATALOG_PORTABLE){
    var searchOffO=document.body.classList.contains('search-chrome-collapsed');
    var kwOffO=document.body.classList.contains('kw-chrome-collapsed')||!document.body.classList.contains('kw-open');
    if(document.body.classList.contains('display-content')||(searchOffO&&kwOffO))next='content';
    else if(next==='middle'&&o!=='portrait')next='sides';
  }"""

WANT_FS_OLD = """function portableWantBrowserFs(){
  if(!window.CATALOG_PORTABLE)return false;
  var b=document.body;
  return !!(b.classList.contains('display-fs')||(b.classList.contains('display-sides')&&!b.classList.contains('display-middle')));
}"""

WANT_FS_NEW = """var portableToolbarFsWanted=false;
function portableWantBrowserFs(){
  if(!window.CATALOG_PORTABLE)return false;
  return !!portableToolbarFsWanted;
}
function togglePortableToolbarFs(){
  if(!window.CATALOG_PORTABLE)return;
  portableToolbarFsWanted=!portableToolbarFsWanted;
  var btn=document.getElementById('hdrToolbarFs');
  if(btn){
    btn.setAttribute('aria-pressed',portableToolbarFsWanted?'true':'false');
    btn.classList.toggle('is-on',portableToolbarFsWanted);
  }
  if(typeof syncPortableBrowserFs==='function')syncPortableBrowserFs();
  // #region agent log
  if(typeof dbgMobileUi==='function')dbgMobileUi('toolbar-fs',{hyp:'H-TFS',on:!!portableToolbarFsWanted});
  // #endregion
}
window.togglePortableToolbarFs=togglePortableToolbarFs;
window.portableToolbarFsWanted=portableToolbarFsWanted;"""

EXIT_FS_OLD = """function portableExitMenuFs(){
  var prev=portableMenuFsPrev;
  portableMenuFsPrev=null;
  portableMenuFsHold='';
  portableRestoreMenuCombo(prev);"""

EXIT_FS_NEW = """function portableExitMenuFs(){
  var which=(typeof portableMenuFsOn==='function'&&portableMenuFsOn())||portableMenuFsHold||'';
  var prev=portableMenuFsPrev;
  portableMenuFsPrev=null;
  portableMenuFsHold='';
  if(document.body.classList.contains('display-middle')&&(which==='search'||which==='keywords')){
    document.body.classList.remove('ac-fs-open','kw-fs-open','dual-fs-open');
    var shX=document.getElementById('acShell');
    if(shX)shX.classList.remove('ac-fs');
    if(typeof acFsWanted!=='undefined')acFsWanted=false;
    if(typeof kwFsWanted!=='undefined')kwFsWanted=false;
    if(typeof portableCoerceMiddleMenu==='function')portableCoerceMiddleMenu(which);
  }else{
    portableRestoreMenuCombo(prev);
  }"""

SEARCH_MORE_OLD = """function toggleSearchStripMore(){
  var pop=document.getElementById('searchStripMorePop');
  var btn=document.getElementById('searchStripMore');
  if(!pop||!btn)return;
  var open=pop.hasAttribute('hidden');
  if(typeof closePhoneOverflowPops==='function')closePhoneOverflowPops('searchStripMorePop');
  if(open){
    pop.innerHTML='';
    function add(label,fn,aria){var b=document.createElement('button');b.type='button';b.textContent=label;if(aria)b.setAttribute('aria-label',aria);b.addEventListener('click',function(e){e.preventDefault();e.stopPropagation();pop.setAttribute('hidden','');btn.setAttribute('aria-expanded','false');fn();});pop.appendChild(b);}
    add('Hide',function(){if(typeof toggleSearchChrome==='function')toggleSearchChrome();},'Hide Search');
    add('History',function(){var h=document.getElementById('searchHistory');if(h)h.click();},'History');
    add('Fullscreen',function(){if(typeof toggleAcFullscreen==='function')toggleAcFullscreen();},'Fullscreen Search');
    add(document.body.classList.contains('layout-edit')?'Done':'Customize',function(){if(typeof toggleLayoutEdit==='function')toggleLayoutEdit();},document.body.classList.contains('layout-edit')?'Done arranging':'Customize layout');
    pop.removeAttribute('hidden');
    btn.setAttribute('aria-expanded','true');
    // #region agent log
    if(typeof dbgMobileUi==='function')dbgMobileUi('search-more',{hyp:'H-CHROME'});
    if(typeof dbgPortableScroll==='function')dbgPortableScroll('search-more',{hyp:'H-SCR1'});
    // #endregion
  }else{
    pop.setAttribute('hidden','');
    btn.setAttribute('aria-expanded','false');
  }
}"""

SEARCH_MORE_NEW = """function portableMoreRowAdd(pop,label,fn,aria){
  var b=document.createElement('button');b.type='button';b.textContent=label;
  if(aria)b.setAttribute('aria-label',aria);
  b.addEventListener('click',function(e){e.preventDefault();e.stopPropagation();fn();});
  pop.appendChild(b);
}
function toggleSearchStripMore(){
  var pop=document.getElementById('searchStripMorePop');
  var btn=document.getElementById('searchStripMore');
  var strip=document.getElementById('searchStrip');
  if(!pop||!btn)return;
  var open=pop.hasAttribute('hidden');
  var hdr=document.getElementById('hdrMorePop');
  if(hdr){hdr.setAttribute('hidden','');var hb=document.getElementById('hdrMoreBtn');if(hb)hb.setAttribute('aria-expanded','false');}
  if(!open){pop.setAttribute('hidden','');btn.setAttribute('aria-expanded','false');return;}
  if(strip&&pop.parentElement!==strip)strip.appendChild(pop);
  pop.innerHTML='';
  portableMoreRowAdd(pop,'Hide',function(){if(typeof toggleSearchChrome==='function')toggleSearchChrome();},'Hide Search');
  portableMoreRowAdd(pop,'History',function(){var h=document.getElementById('searchHistory');if(h)h.click();},'History');
  portableMoreRowAdd(pop,'Fullscreen',function(){if(typeof toggleAcFullscreen==='function')toggleAcFullscreen();},'Fullscreen Search');
  portableMoreRowAdd(pop,document.body.classList.contains('layout-edit')?'Done':'Customize',function(){if(typeof toggleLayoutEdit==='function')toggleLayoutEdit();},document.body.classList.contains('layout-edit')?'Done arranging':'Customize layout');
  pop.removeAttribute('hidden');
  btn.setAttribute('aria-expanded','true');
  btn.style.setProperty('display','inline-flex','important');
  // #region agent log
  if(typeof dbgMobileUi==='function')dbgMobileUi('search-more',{hyp:'H-CHROME'});
  if(typeof dbgPortableScroll==='function')dbgPortableScroll('search-more',{hyp:'H-SCR1'});
  // #endregion
}"""

HDR_MORE_OLD = """function closePhoneOverflowPops(except){
  [['hdrMorePop','hdrMoreBtn'],['kwStripMorePop','kwStripMore'],['searchStripMorePop','searchStripMore']].forEach(function(pair){
    if(except&&pair[0]===except)return;
    var p=document.getElementById(pair[0]);var b=document.getElementById(pair[1]);
    if(p)p.setAttribute('hidden','');
    if(b)b.setAttribute('aria-expanded','false');
  });
}
function phoneMoreAdd(pop,label,fn,aria){
  var b=document.createElement('button');b.type='button';b.textContent=label;
  if(aria)b.setAttribute('aria-label',aria);
  b.addEventListener('click',function(e){e.preventDefault();e.stopPropagation();closePhoneOverflowPops();fn();});
  pop.appendChild(b);
}
function toggleHdrMore(){
  if(!(typeof isPhoneViewport==='function'&&isPhoneViewport()))return;
  var pop=document.getElementById('hdrMorePop');var btn=document.getElementById('hdrMoreBtn');
  if(!pop||!btn)return;
  var open=pop.hasAttribute('hidden');
  closePhoneOverflowPops('hdrMorePop');
  if(!open){pop.setAttribute('hidden','');btn.setAttribute('aria-expanded','false');return;}
  var hdr=document.querySelector('.catalog-header');
  if(hdr&&pop.parentElement!==hdr)hdr.appendChild(pop);
  pop.innerHTML='';
  phoneMoreAdd(pop,document.body.classList.contains('layout-edit')?'Done':'Customize',function(){if(typeof toggleLayoutEdit==='function')toggleLayoutEdit();},document.body.classList.contains('layout-edit')?'Done arranging':'Customize layout');
  phoneMoreAdd(pop,'Miss',function(){var x=document.getElementById('clearMissBtn');if(x)x.click();},'Clear on miss');
  phoneMoreAdd(pop,'Flip',function(){if(typeof togglePortraitSidesFlip==='function')togglePortraitSidesFlip();},'Flip panes');
  phoneMoreAdd(pop,'History',function(){var h=document.getElementById('searchHistory');if(h)h.click();},'History');
  var sel=document.getElementById('themePicker');
  if(sel){
    var lab=document.createElement('label');lab.textContent='Theme';lab.style.fontSize='.85rem';
    var clone=sel.cloneNode(true);clone.id='hdrMoreTheme';clone.className='theme-picker';
    clone.value=sel.value;
    clone.addEventListener('change',function(){if(typeof setTheme==='function')setTheme(clone.value);sel.value=clone.value;});
    pop.appendChild(lab);pop.appendChild(clone);
  }
  pop.removeAttribute('hidden');btn.setAttribute('aria-expanded','true');
  if(typeof dbgMobileUi==='function')dbgMobileUi('hdr-more',{hyp:'H-M3'});
}
function toggleKwStripMore(){
  if(!(typeof isPhoneViewport==='function'&&isPhoneViewport()))return;
  var pop=document.getElementById('kwStripMorePop');var btn=document.getElementById('kwStripMore');
  if(!pop||!btn)return;
  var open=pop.hasAttribute('hidden');
  closePhoneOverflowPops('kwStripMorePop');
  if(!open){pop.setAttribute('hidden','');btn.setAttribute('aria-expanded','false');return;}
  pop.innerHTML='';
  phoneMoreAdd(pop,document.body.classList.contains('layout-edit')?'Done':'Customize',function(){if(typeof toggleLayoutEdit==='function')toggleLayoutEdit();},document.body.classList.contains('layout-edit')?'Done arranging':'Customize layout');
  phoneMoreAdd(pop,'Hide',function(){if(typeof toggleKwChrome==='function')toggleKwChrome();else if(typeof toggleHdrKw==='function')toggleHdrKw();},'Hide Keywords');
  phoneMoreAdd(pop,'Flip',function(){if(typeof togglePortraitSidesFlip==='function')togglePortraitSidesFlip();},'Flip panes');
  phoneMoreAdd(pop,'Tap',function(){if(typeof toggleTapToAdd==='function')toggleTapToAdd();},'Tap to add');
  phoneMoreAdd(pop,'Clear',function(){if(typeof clearAllFilters==='function')clearAllFilters();},'Clear keywords');
  phoneMoreAdd(pop,'History',function(){var h=document.getElementById('searchHistory');if(h)h.click();},'History');
  phoneMoreAdd(pop,'Fullscreen',function(){if(typeof toggleKwFullscreen==='function')toggleKwFullscreen();},'Fullscreen Keywords');
  pop.removeAttribute('hidden');btn.setAttribute('aria-expanded','true');
  if(typeof dbgMobileUi==='function')dbgMobileUi('kw-more',{hyp:'H-M3'});
}
window.toggleHdrMore=toggleHdrMore;
window.toggleKwStripMore=toggleKwStripMore;
document.addEventListener('click',function(e){
  if(!(typeof isPhoneViewport==='function'&&isPhoneViewport()))return;
  var t=e.target;
  if(t&&t.closest&&t.closest('#hdrMoreBtn,#hdrMorePop,#kwStripMore,#kwStripMorePop,#searchStripMore,#searchStripMorePop'))return;
  closePhoneOverflowPops();
});
document.addEventListener('click',function(e){
  var pop=document.getElementById('searchStripMorePop');
  var btn=document.getElementById('searchStripMore');
  if(!pop||pop.hasAttribute('hidden'))return;
  if(btn&&(btn===e.target||btn.contains(e.target)))return;
  if(pop.contains(e.target))return;
  pop.setAttribute('hidden','');
  if(btn)btn.setAttribute('aria-expanded','false');
});"""

HDR_MORE_NEW = """function closePhoneOverflowPops(except){
  [['hdrMorePop','hdrMoreBtn']].forEach(function(pair){
    if(except&&pair[0]===except)return;
    var p=document.getElementById(pair[0]);var b=document.getElementById(pair[1]);
    if(p)p.setAttribute('hidden','');
    if(b)b.setAttribute('aria-expanded','false');
  });
}
function phoneMoreAdd(pop,label,fn,aria){
  var b=document.createElement('button');b.type='button';b.textContent=label;
  if(aria)b.setAttribute('aria-label',aria);
  b.addEventListener('click',function(e){e.preventDefault();e.stopPropagation();closePhoneOverflowPops();fn();});
  pop.appendChild(b);
}
function portablePlaceHdrMorePop(){
  var pop=document.getElementById('hdrMorePop');
  var btn=document.getElementById('hdrMoreBtn');
  var hdr=document.querySelector('.catalog-header');
  if(!pop||!btn)return;
  if(hdr&&pop.parentElement!==hdr)hdr.appendChild(pop);
  var portrait=!!(window.matchMedia&&window.matchMedia('(orientation:portrait)').matches);
  var top=Math.round((hdr?hdr.getBoundingClientRect().bottom:btn.getBoundingClientRect().bottom)+4);
  pop.style.setProperty('position','fixed','important');
  pop.style.setProperty('z-index','420','important');
  pop.style.setProperty('top',top+'px','important');
  pop.style.setProperty('bottom','auto','important');
  pop.style.setProperty('display','flex','important');
  pop.style.setProperty('flex-direction','column','important');
  if(portrait){
    pop.style.setProperty('left','8px','important');
    pop.style.setProperty('right','8px','important');
    pop.style.setProperty('width','auto','important');
    pop.style.setProperty('max-width','none','important');
  }else{
    pop.style.setProperty('left','auto','important');
    pop.style.setProperty('right','8px','important');
    pop.style.setProperty('width',Math.min(352,Math.round((window.innerWidth||900)*0.46))+'px','important');
    pop.style.setProperty('max-width','22rem','important');
  }
  pop.style.setProperty('max-height','min(70dvh,28rem)','important');
  pop.style.setProperty('overflow-y','auto','important');
  pop.style.setProperty('min-height','4rem','important');
}
function toggleHdrMore(){
  var pop=document.getElementById('hdrMorePop');var btn=document.getElementById('hdrMoreBtn');
  if(!pop||!btn)return;
  var open=pop.hasAttribute('hidden');
  closePhoneOverflowPops('hdrMorePop');
  if(!open){pop.setAttribute('hidden','');btn.setAttribute('aria-expanded','false');return;}
  var hdr=document.querySelector('.catalog-header');
  if(hdr&&pop.parentElement!==hdr)hdr.appendChild(pop);
  pop.innerHTML='';
  phoneMoreAdd(pop,document.body.classList.contains('layout-edit')?'Done':'Customize',function(){if(typeof toggleLayoutEdit==='function')toggleLayoutEdit();},document.body.classList.contains('layout-edit')?'Done arranging':'Customize layout');
  phoneMoreAdd(pop,'Miss',function(){var x=document.getElementById('clearMissBtn');if(x)x.click();},'Clear on miss');
  phoneMoreAdd(pop,'Flip',function(){if(typeof togglePortraitSidesFlip==='function')togglePortraitSidesFlip();},'Flip panes');
  phoneMoreAdd(pop,'History',function(){var h=document.getElementById('searchHistory');if(h)h.click();},'History');
  var sel=document.getElementById('themePicker');
  if(sel){
    var lab=document.createElement('label');lab.textContent='Theme';lab.style.fontSize='.85rem';
    var clone=sel.cloneNode(true);clone.id='hdrMoreTheme';clone.className='theme-picker';
    clone.value=sel.value;
    clone.addEventListener('change',function(){if(typeof setTheme==='function')setTheme(clone.value);sel.value=clone.value;});
    pop.appendChild(lab);pop.appendChild(clone);
  }
  pop.removeAttribute('hidden');btn.setAttribute('aria-expanded','true');
  portablePlaceHdrMorePop();
  if(typeof dbgMobileUi==='function')dbgMobileUi('hdr-more',{hyp:'H-M3'});
}
function toggleKwStripMore(){
  var pop=document.getElementById('kwStripMorePop');var btn=document.getElementById('kwStripMore');
  var top=document.getElementById('filterTop');
  if(!pop||!btn)return;
  var open=pop.hasAttribute('hidden');
  var hdr=document.getElementById('hdrMorePop');
  if(hdr){hdr.setAttribute('hidden','');var hb=document.getElementById('hdrMoreBtn');if(hb)hb.setAttribute('aria-expanded','false');}
  if(!open){pop.setAttribute('hidden','');btn.setAttribute('aria-expanded','false');return;}
  if(top&&pop.parentElement!==top)top.appendChild(pop);
  pop.innerHTML='';
  if(typeof portableMoreRowAdd!=='function'){
    window.portableMoreRowAdd=function(p,label,fn,aria){var b=document.createElement('button');b.type='button';b.textContent=label;if(aria)b.setAttribute('aria-label',aria);b.addEventListener('click',function(e){e.preventDefault();e.stopPropagation();fn();});p.appendChild(b);};
  }
  portableMoreRowAdd(pop,document.body.classList.contains('layout-edit')?'Done':'Customize',function(){if(typeof toggleLayoutEdit==='function')toggleLayoutEdit();},document.body.classList.contains('layout-edit')?'Done arranging':'Customize layout');
  portableMoreRowAdd(pop,'Hide',function(){if(typeof toggleKwChrome==='function')toggleKwChrome();else if(typeof toggleHdrKw==='function')toggleHdrKw();},'Hide Keywords');
  portableMoreRowAdd(pop,'Flip',function(){if(typeof togglePortraitSidesFlip==='function')togglePortraitSidesFlip();},'Flip panes');
  portableMoreRowAdd(pop,'Tap',function(){if(typeof toggleTapToAdd==='function')toggleTapToAdd();},'Tap to add');
  portableMoreRowAdd(pop,'Clear',function(){if(typeof clearAllFilters==='function')clearAllFilters();},'Clear keywords');
  portableMoreRowAdd(pop,'History',function(){var h=document.getElementById('searchHistory');if(h)h.click();},'History');
  portableMoreRowAdd(pop,'Fullscreen',function(){if(typeof toggleKwFullscreen==='function')toggleKwFullscreen();},'Fullscreen Keywords');
  pop.removeAttribute('hidden');btn.setAttribute('aria-expanded','true');
  btn.style.setProperty('display','inline-flex','important');
  if(typeof dbgMobileUi==='function')dbgMobileUi('kw-more',{hyp:'H-M3'});
}
window.toggleHdrMore=toggleHdrMore;
window.toggleKwStripMore=toggleKwStripMore;
document.addEventListener('click',function(e){
  var t=e.target;
  if(t&&t.closest&&t.closest('#hdrMoreBtn,#hdrMorePop'))return;
  closePhoneOverflowPops();
});"""

HELPERS_OLD = "window.placePortableHandles=placePortableHandles;"
HELPERS_NEW = r"""window.placePortableHandles=placePortableHandles;
function portableMenusOpenNow(){
  var fw=document.getElementById('filterWrap');
  return {
    searchOn:!document.body.classList.contains('search-chrome-collapsed'),
    kwOn:!document.body.classList.contains('kw-chrome-collapsed')&&!!(fw&&fw.classList.contains('open')&&document.body.classList.contains('kw-open'))
  };
}
function portableWantLayout(){
  try{return (window.matchMedia&&window.matchMedia('(orientation:portrait)').matches)?'middle':'sides';}catch(e){return 'sides';}
}
function portableSyncModeFromMenus(which){
  if(!window.CATALOG_PORTABLE)return;
  if(typeof portableMenuFsOn==='function'&&portableMenuFsOn())return;
  var m=portableMenusOpenNow();
  if(!m.searchOn&&!m.kwOn){
    if(typeof setDisplayMode==='function')setDisplayMode('content',{keepMenus:true});
    return;
  }
  var want=portableWantLayout();
  var docked=document.body.classList.contains('display-sides')||document.body.classList.contains('display-middle');
  if(!docked){
    if(typeof setDisplayMode==='function')setDisplayMode(want,{keepMenus:true,pick:true});
  }else if(want==='sides'&&document.body.classList.contains('display-middle')){
    if(typeof setDisplayMode==='function')setDisplayMode('sides',{keepMenus:true,pick:true});
  }
  if(document.body.classList.contains('display-middle')&&which&&typeof portableCoerceMiddleMenu==='function'){
    portableCoerceMiddleMenu(which==='keywords'?'keywords':'search');
  }
}
window.portableSyncModeFromMenus=portableSyncModeFromMenus;"""

BOOT_OLD = """  // Landscape defaults to Sides, portrait to Middle. Explicit picks are stored per orientation.
  setDisplayMode(m);"""
BOOT_NEW = """  // Portable boots content-only; opening S/K enters Sides or Middle.
  setDisplayMode(window.CATALOG_PORTABLE?'content':m);"""

KW_BOOT_OLD = "if(shouldOpen&&!fw.classList.contains('open')&&typeof currentDisplay!=='undefined'&&currentDisplay!=='sides'&&currentDisplay!=='middle')"
KW_BOOT_NEW = "if(!window.CATALOG_PORTABLE&&shouldOpen&&!fw.classList.contains('open')&&typeof currentDisplay!=='undefined'&&currentDisplay!=='sides'&&currentDisplay!=='middle')"

HDR_S_OLD = """    if(typeof placePortableHandles==='function')placePortableHandles();
    syncHdrMenuBtns();
    return;
  }
  if(typeof toggleSearchChrome==='function')toggleSearchChrome();"""

HDR_S_NEW = """    if(typeof placePortableHandles==='function')placePortableHandles();
    syncHdrMenuBtns();
    if(typeof portableSyncModeFromMenus==='function')portableSyncModeFromMenus('search');
    return;
  }
  if(typeof toggleSearchChrome==='function')toggleSearchChrome();"""

HDR_S_END_OLD = """  if(typeof placePortableHandles==='function')placePortableHandles();
  syncHdrMenuBtns();
}
function toggleHdrKw(){"""

HDR_S_END_NEW = """  if(typeof placePortableHandles==='function')placePortableHandles();
  syncHdrMenuBtns();
  if(window.CATALOG_PORTABLE&&typeof portableSyncModeFromMenus==='function')portableSyncModeFromMenus('search');
}
function toggleHdrKw(){"""

HDR_K_OLD = """    if(visK==='keywords'){if(typeof collapseKwMenu==='function')collapseKwMenu();}
    else if(typeof portableCoerceMiddleMenu==='function')portableCoerceMiddleMenu('keywords');
    if(typeof placePortableHandles==='function')placePortableHandles();
    syncHdrMenuBtns();
    return;
  }"""

HDR_K_NEW = """    if(visK==='keywords'){if(typeof collapseKwMenu==='function')collapseKwMenu();}
    else if(typeof portableCoerceMiddleMenu==='function')portableCoerceMiddleMenu('keywords');
    if(typeof placePortableHandles==='function')placePortableHandles();
    syncHdrMenuBtns();
    if(typeof portableSyncModeFromMenus==='function')portableSyncModeFromMenus('keywords');
    return;
  }"""

HDR_K_END_OLD = """  if(typeof placePortableHandles==='function')placePortableHandles();
  syncHdrMenuBtns();
}
function syncIndexEmbedBtn(){"""

HDR_K_END_NEW = """  if(typeof placePortableHandles==='function')placePortableHandles();
  syncHdrMenuBtns();
  if(window.CATALOG_PORTABLE&&typeof portableSyncModeFromMenus==='function')portableSyncModeFromMenus('keywords');
}
function syncIndexEmbedBtn(){"""


def must_replace(text, old, new, label):
    n = text.count(old)
    if n != 1:
        raise SystemExit(f"{label}: count={n}")
    return text.replace(old, new, 1)


def patch(text):
    if CSS_MARK not in text:
        needle = "</style></head><body class=\"search-mode\">"
        if needle not in text:
            raise SystemExit("style close missing")
        text = text.replace(needle, CSS + "\n</style></head><body class=\"search-mode\">", 1)
    if 'id="hdrToolbarFs"' not in text:
        text = must_replace(text, HDR_FS_OLD, HDR_FS_NEW, "toolbar fs btn")
    text = must_replace(text, SET_MODE_OLD, SET_MODE_NEW, "setDisplayMode modes")
    text = must_replace(text, MIDDLE_TO_SIDES_OLD, MIDDLE_TO_SIDES_NEW, "content early return")
    text = must_replace(text, SIDES_FORCE_OLD, SIDES_FORCE_NEW, "sides force menus")
    text = must_replace(text, SIDES_OPEN_OLD, SIDES_OPEN_NEW, "sides keepMenus search")
    text = must_replace(text, SIDES_KW_OLD, SIDES_KW_NEW, "sides keepMenus kw")
    text = must_replace(text, ORIENT_OLD, ORIENT_NEW, "orient content")
    text = must_replace(text, WANT_FS_OLD, WANT_FS_NEW, "toolbar fs want")
    text = must_replace(text, EXIT_FS_OLD, EXIT_FS_NEW, "exit menu fs")
    text = must_replace(text, SEARCH_MORE_OLD, SEARCH_MORE_NEW, "search more rows")
    text = must_replace(text, HDR_MORE_OLD, HDR_MORE_NEW, "hdr bubble / kw rows")
    text = must_replace(text, HELPERS_OLD, HELPERS_NEW, "sync helpers")
    text = must_replace(text, BOOT_OLD, BOOT_NEW, "boot content")
    text = must_replace(text, KW_BOOT_OLD, KW_BOOT_NEW, "skip kw boot")
    text = must_replace(text, HDR_S_OLD, HDR_S_NEW, "hdr search middle sync")
    text = must_replace(text, HDR_S_END_OLD, HDR_S_END_NEW, "hdr search end sync")
    text = must_replace(text, HDR_K_OLD, HDR_K_NEW, "hdr kw middle sync")
    text = must_replace(text, HDR_K_END_OLD, HDR_K_END_NEW, "hdr kw end sync")
    return text


def main():
    for path in FILES:
        raw = path.read_text(encoding="utf-8")
        if CSS_MARK in raw and "portableSyncModeFromMenus" in raw:
            print(f"already patched {path.name}")
            continue
        path.write_text(patch(raw), encoding="utf-8")
        print(f"patched {path.name}")


if __name__ == "__main__":
    main()
