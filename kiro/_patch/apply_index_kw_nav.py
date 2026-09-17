#!/usr/bin/env python3
"""Index window/embed, KW pills fill, S/K nav, Clear toolbar placement."""
from pathlib import Path

ROOT = Path("/home/phnx/kiro-kontakt-patch")
ALL = [
    ROOT / "public/catalogs/KONTAKT-CATALOG.html",
    ROOT / "public/catalogs/DS-CATALOG.html",
    ROOT / "public/catalogs/KONTAKT-CATALOG-portable.html",
    ROOT / "public/catalogs/DS-CATALOG-portable.html",
]
PORTABLE = [
    ROOT / "public/catalogs/KONTAKT-CATALOG-portable.html",
    ROOT / "public/catalogs/DS-CATALOG-portable.html",
]

CLEAR_BTN = '<button type="button" class="mode-btn clear-all" onclick="clearAllFilters()">Clear</button>'
CLEAR_TOOLBAR = (
    '<button type="button" class="mode-btn clear-all kw-strip-clear" id="kwStripClear" '
    'onclick="event.preventDefault();event.stopPropagation();clearAllFilters()">Clear</button>'
)
MORE_BTN = (
    '<button type="button" class="kw-strip-more" id="kwStripMore" aria-expanded="false" '
    'aria-haspopup="true" title="More keyword controls" '
    'onclick="event.preventDefault();event.stopPropagation();toggleKwStripMore()">'
)

LEAD_OLD = """  var cs=document.getElementById('catSwitch');
  var tap=document.getElementById('tapAddBtnPanel');
  var clrBtn=document.querySelector('#filterPanel .mode-btn.clear-all,.cat-switch .mode-btn.clear-all,.mode-btn.clear-all');
  if(cs&&tap&&clrBtn&&clrBtn.id!=='clearMissBtn'){
    var lead=cs.querySelector('.cat-switch-lead');
    if(!lead){lead=document.createElement('span');lead.className='cat-switch-lead';}
    if(lead.parentElement!==cs||cs.firstElementChild!==lead)cs.insertBefore(lead,cs.firstChild);
    if(tap.parentElement!==lead)lead.appendChild(tap);
    if(clrBtn.parentElement!==lead)lead.appendChild(clrBtn);
    if(tap.nextElementSibling!==clrBtn)lead.insertBefore(tap,clrBtn);
  }"""

LEAD_NEW = """  var cs=document.getElementById('catSwitch');
  var tap=document.getElementById('tapAddBtnPanel');
  if(cs&&tap){
    var lead=cs.querySelector('.cat-switch-lead');
    if(!lead){lead=document.createElement('span');lead.className='cat-switch-lead';}
    if(lead.parentElement!==cs||cs.firstElementChild!==lead)cs.insertBefore(lead,cs.firstChild);
    if(tap.parentElement!==lead)lead.appendChild(tap);
  }
  var clrBtn=document.getElementById('kwStripClear')||document.querySelector('#filterTop .mode-btn.clear-all,.mode-btn.clear-all.kw-strip-clear');
  if(!clrBtn){
    clrBtn=document.querySelector('#filterPanel .mode-btn.clear-all,.cat-switch .mode-btn.clear-all');
  }
  var topKw=document.getElementById('filterTop');
  var moreKw=document.getElementById('kwStripMore');
  if(clrBtn&&clrBtn.id!=='clearMissBtn'&&topKw){
    clrBtn.id='kwStripClear';
    clrBtn.classList.add('kw-strip-clear');
    if(moreKw){
      if(clrBtn.parentElement!==topKw||clrBtn.nextElementSibling!==moreKw)topKw.insertBefore(clrBtn,moreKw);
    }else if(clrBtn.parentElement!==topKw)topKw.appendChild(clrBtn);
  }"""

CSS_CLEAR = """
#kwStripClear,.kw-strip-clear{display:inline-flex;align-items:center;justify-content:center;flex:0 0 auto;min-height:2.25rem;padding:0 .55rem;margin-left:auto;cursor:pointer}
.cat-switch .mode-btn.clear-all{display:none!important}
"""

PORT_CSS = """
/* fix-NAV-INDEX-KW: sticky Index window, KW pills fill leftover */
@media all{
  body.catalog-portable #catalogIndex:not(.is-embedded):not(.is-collapsed),
  body.catalog-portable.display-sides #catalogIndex:not(.is-embedded):not(.is-collapsed),
  body.catalog-portable.display-content #catalogIndex:not(.is-embedded):not(.is-collapsed),
  body.catalog-portable.display-middle #catalogIndex:not(.is-embedded):not(.is-collapsed){
    position:sticky!important;top:0!important;z-index:14!important;
    height:var(--sides-index-h,min(48dvh,28rem))!important;
    max-height:min(70dvh,40rem)!important;min-height:0!important;
    overflow:hidden!important;flex-shrink:0!important;
    box-shadow:0 10px 24px rgba(0,0,0,.32)!important;border-radius:0 0 10px 10px
  }
  body.catalog-portable #catalogIndex:not(.is-embedded):not(.is-collapsed) .index,
  body.catalog-portable #catalogIndex:not(.is-embedded):not(.is-collapsed) #catalogIndexList,
  body.catalog-portable.display-sides #catalogIndex:not(.is-embedded):not(.is-collapsed) .index,
  body.catalog-portable.display-sides #catalogIndex:not(.is-embedded):not(.is-collapsed) #catalogIndexList{
    display:grid!important;grid-template-columns:repeat(auto-fill,minmax(min(12rem,100%),1fr))!important;
    grid-auto-flow:row;align-content:start;flex:1 1 auto!important;min-height:0!important;
    overflow-x:hidden!important;overflow-y:auto!important;max-height:none!important;
    columns:none!important;height:auto!important
  }
  body.catalog-portable #filterWrap,
  body.catalog-portable #filterWrap.open,
  body.catalog-portable.display-fs.kw-fs-open #filterWrap,
  body.catalog-portable.display-middle #filterWrap.open,
  body.catalog-portable.display-sides #filterWrap.open{
    display:flex!important;flex-direction:column!important;min-height:0!important;overflow:hidden!important
  }
  body.catalog-portable #filterWrap .filter-panel,
  body.catalog-portable #filterWrap.open .filter-panel,
  body.catalog-portable.kw-fs-open #filterWrap .filter-panel{
    display:flex!important;flex-direction:column!important;flex:1 1 auto!important;
    min-height:0!important;overflow:hidden!important;max-height:none!important
  }
  body.catalog-portable #kwbar,
  body.catalog-portable.kw-fs-open #kwbar,
  body.catalog-portable.display-fs.kw-fs-open #kwbar,
  body.catalog-portable.display-middle #kwbar,
  body.catalog-portable.display-sides #kwbar{
    flex:1 1 auto!important;min-height:0!important;min-width:0!important;
    width:100%!important;max-width:100%!important;height:auto!important;max-height:none!important;
    overflow-x:hidden!important;overflow-y:auto!important;-webkit-overflow-scrolling:touch
  }
  body.catalog-portable #kwStripClear{margin-left:auto}
}
"""

IDX_TOGGLE_OLD = """function syncIndexEmbedBtn(){
  var ix=document.getElementById('catalogIndex');
  var btn=document.getElementById('catalogIndexEmbed');
  if(!btn)return;
  var on=!!(ix&&ix.classList.contains('is-embedded'));
  var sides=document.body.classList.contains('display-sides');
  btn.hidden=!sides;
  btn.setAttribute('aria-pressed',on?'true':'false');
  btn.textContent=on?'Window':'Embed';
  btn.title=on?'Show Index as a scrollable dock window':'Embed Index above the catalog cards';
}
function toggleIndexEmbed(){
  var ix=document.getElementById('catalogIndex');
  if(!ix||!document.body.classList.contains('display-sides'))return;
  var on=ix.classList.toggle('is-embedded');
  if(typeof writeModeSlot==='function')writeModeSlot({indexEmbed:on},'sides');
  if(typeof applyIndexScrollFit==='function')applyIndexScrollFit();
  if(typeof portableEnsureScrollMenus==='function')portableEnsureScrollMenus();
  syncIndexEmbedBtn();
  var cm=document.getElementById('catalogMain');
  if(on&&cm)cm.scrollTop=0;"""

IDX_TOGGLE_NEW = """function indexEmbedPrefKey(){return 'catalog-index-embed-'+(window.CATALOG_NS||'catalog');}
function readIndexEmbedPref(){
  try{var v=localStorage.getItem(indexEmbedPrefKey());if(v==='1')return true;if(v==='0')return false;}catch(eIxP){}
  return null;
}
function writeIndexEmbedPref(on){
  try{localStorage.setItem(indexEmbedPrefKey(),on?'1':'0');}catch(eIxW){}
}
function syncIndexEmbedBtn(){
  var ix=document.getElementById('catalogIndex');
  var btn=document.getElementById('catalogIndexEmbed');
  if(!btn)return;
  var on=!!(ix&&ix.classList.contains('is-embedded'));
  var sides=document.body.classList.contains('display-sides');
  btn.hidden=window.CATALOG_PORTABLE?false:!sides;
  btn.setAttribute('aria-pressed',on?'true':'false');
  btn.textContent=on?'Window':'Embed';
  btn.title=on?'Show Index as a scrollable dock window':'Embed Index above the catalog cards';
}
function toggleIndexEmbed(){
  var ix=document.getElementById('catalogIndex');
  var sides=document.body.classList.contains('display-sides');
  // #region agent log
  try{
    fetch('http://127.0.0.1:7529/ingest/1cf46354-1d61-4c80-bd72-a340f1db1b51',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'c00e3e'},body:JSON.stringify({sessionId:'c00e3e',runId:'post-fix',hypothesisId:'A',location:'catalog:toggleIndexEmbed',message:'index embed toggle enter',data:{hasIx:!!ix,sides:sides,portable:!!window.CATALOG_PORTABLE,embed:!!(ix&&ix.classList.contains('is-embedded')),collapsed:!!(ix&&ix.classList.contains('is-collapsed')),pos:ix?getComputedStyle(ix).position:'',btnHidden:!!(document.getElementById('catalogIndexEmbed')||{}).hidden,cls:document.body.className},timestamp:Date.now()})}).catch(function(){});
  }catch(eDbgA){}
  // #endregion
  if(!ix)return;
  if(!window.CATALOG_PORTABLE&&!sides)return;
  var on=ix.classList.toggle('is-embedded');
  writeIndexEmbedPref(on);
  if(typeof writeModeSlot==='function')writeModeSlot({indexEmbed:on});
  if(typeof applyIndexScrollFit==='function')applyIndexScrollFit();
  if(typeof portableEnsureScrollMenus==='function')portableEnsureScrollMenus();
  syncIndexEmbedBtn();
  var cm=document.getElementById('catalogMain');
  if(on&&cm)cm.scrollTop=0;"""

IDX_TOGGLE_DESK_OLD = """function syncIndexEmbedBtn(){
  var ix=document.getElementById('catalogIndex');
  var btn=document.getElementById('catalogIndexEmbed');
  if(!btn)return;
  var on=!!(ix&&ix.classList.contains('is-embedded'));
  var sides=document.body.classList.contains('display-sides');
  btn.hidden=!sides;
  btn.setAttribute('aria-pressed',on?'true':'false');
  btn.textContent=on?'Window':'Embed';
  btn.title=on?'Show Index as a scrollable dock window':'Embed Index above the catalog cards';
}
function toggleIndexEmbed(){
  var ix=document.getElementById('catalogIndex');
  if(!ix||!document.body.classList.contains('display-sides'))return;
  var on=ix.classList.toggle('is-embedded');
  if(typeof writeModeSlot==='function')writeModeSlot({indexEmbed:on},'sides');
  if(typeof applyIndexScrollFit==='function')applyIndexScrollFit();
  syncIndexEmbedBtn();
  var cm=document.getElementById('catalogMain');
  if(on&&cm)cm.scrollTop=0;
}"""

IDX_TOGGLE_DESK_NEW = """function indexEmbedPrefKey(){return 'catalog-index-embed-'+(window.CATALOG_NS||'catalog');}
function readIndexEmbedPref(){
  try{var v=localStorage.getItem(indexEmbedPrefKey());if(v==='1')return true;if(v==='0')return false;}catch(eIxP){}
  return null;
}
function writeIndexEmbedPref(on){
  try{localStorage.setItem(indexEmbedPrefKey(),on?'1':'0');}catch(eIxW){}
}
function syncIndexEmbedBtn(){
  var ix=document.getElementById('catalogIndex');
  var btn=document.getElementById('catalogIndexEmbed');
  if(!btn)return;
  var on=!!(ix&&ix.classList.contains('is-embedded'));
  var sides=document.body.classList.contains('display-sides');
  btn.hidden=!sides;
  btn.setAttribute('aria-pressed',on?'true':'false');
  btn.textContent=on?'Window':'Embed';
  btn.title=on?'Show Index as a scrollable dock window':'Embed Index above the catalog cards';
}
function toggleIndexEmbed(){
  var ix=document.getElementById('catalogIndex');
  if(!ix||!document.body.classList.contains('display-sides'))return;
  var on=ix.classList.toggle('is-embedded');
  writeIndexEmbedPref(on);
  if(typeof writeModeSlot==='function')writeModeSlot({indexEmbed:on},'sides');
  if(typeof applyIndexScrollFit==='function')applyIndexScrollFit();
  syncIndexEmbedBtn();
  var cm=document.getElementById('catalogMain');
  if(on&&cm)cm.scrollTop=0;
}"""

FORCE_IDX_OLD = """  // fix-IDX-embed: embed index in upper/fs (prevent floating window); leave sides alone
  (function(){var idx=document.getElementById('catalogIndex');if(!idx)return;if(mode!=='sides')idx.classList.add('is-embedded');else idx.classList.remove('is-embedded');})();"""

FORCE_IDX_NEW = """  // fix-IDX-embed: portable keeps Window/Embed across modes; desktop embeds off-sides
  (function(){
    var idx=document.getElementById('catalogIndex');
    if(!idx)return;
    var pref=typeof readIndexEmbedPref==='function'?readIndexEmbedPref():null;
    if(window.CATALOG_PORTABLE){
      if(pref===true)idx.classList.add('is-embedded');
      else if(pref===false)idx.classList.remove('is-embedded');
      if(typeof syncIndexEmbedBtn==='function')syncIndexEmbedBtn();
      return;
    }
    if(mode!=='sides')idx.classList.add('is-embedded');
    else{
      if(pref===true)idx.classList.add('is-embedded');
      else idx.classList.remove('is-embedded');
    }
  })();"""

FIT_OLD = """function applyIndexScrollFit(){
  var ix=document.getElementById('catalogIndex');
  var il=document.getElementById('catalogIndexList')||(ix&&ix.querySelector('ul.index'));
  if(!ix||!il)return;
  if(ix.dataset.ixFitting==='1')return;
  if(!document.body.classList.contains('display-sides')||ix.classList.contains('is-collapsed')||ix.classList.contains('is-embedded')){"""

FIT_NEW = """function applyIndexScrollFit(){
  var ix=document.getElementById('catalogIndex');
  var il=document.getElementById('catalogIndexList')||(ix&&ix.querySelector('ul.index'));
  if(!ix||!il)return;
  if(ix.dataset.ixFitting==='1')return;
  var windowOk=window.CATALOG_PORTABLE||document.body.classList.contains('display-sides');
  if(!windowOk||ix.classList.contains('is-collapsed')||ix.classList.contains('is-embedded')){"""

FIT_WHEEL_OLD = """      if(!document.body.classList.contains('display-sides'))return;"""
FIT_WHEEL_NEW = """      if(!window.CATALOG_PORTABLE&&!document.body.classList.contains('display-sides'))return;"""

SCROLL_OLD = """  var fsNow=!!(menuFs==='search'||menuFs==='keywords'||document.body.classList.contains('ac-fs-open')||document.body.classList.contains('kw-fs-open'));
  var kb=document.getElementById('kwbar');
  if(fsNow)port(fp,'auto');
  else{
    if(fp){fp.style.setProperty('overflow','hidden','important');fp.style.setProperty('overflow-y','hidden','important');}
    if(kb)port(kb,'auto');
  }"""

SCROLL_NEW = """  var fsNow=!!(menuFs==='search'||menuFs==='keywords'||document.body.classList.contains('ac-fs-open')||document.body.classList.contains('kw-fs-open'));
  var kb=document.getElementById('kwbar');
  if(fp){fp.style.setProperty('overflow','hidden','important');fp.style.setProperty('overflow-y','hidden','important');}
  if(kb)port(kb,'auto');"""

KWBAR_FLEX_OLD = """  body.catalog-portable #kwbar{
    flex:0 0 auto!important;min-height:min-content!important;min-width:0!important;
    width:100%!important;max-width:100%!important;height:auto!important;max-height:none!important;
    overflow:visible!important
  }"""

KWBAR_FLEX_NEW = """  body.catalog-portable #kwbar{
    flex:1 1 auto!important;min-height:0!important;min-width:0!important;
    width:100%!important;max-width:100%!important;height:auto!important;max-height:none!important;
    overflow-x:hidden!important;overflow-y:auto!important
  }"""

IDX_REL_OLD = """  body.catalog-portable.display-sides #catalogIndex{
    position:relative!important;z-index:2!important;
    height:auto!important;max-height:min(36dvh,16rem)!important;
    box-shadow:none!important
  }"""

IDX_REL_NEW = """  body.catalog-portable.display-sides #catalogIndex{
    z-index:2!important;min-width:0!important;max-width:100%!important;
    box-sizing:border-box!important
  }
  body.catalog-portable.display-sides #catalogIndex.is-collapsed,
  body.catalog-portable.display-sides #catalogIndex.is-embedded{
    position:relative!important;height:auto!important;max-height:none!important;box-shadow:none!important
  }"""

IDX_WIN_OLD = """  body.catalog-portable.display-sides #catalogIndex:not(.is-embedded):not(.is-collapsed){
    position:relative!important;z-index:12!important;
    height:var(--sides-index-h,min(48dvh,28rem))!important;
    max-height:min(70dvh,40rem)!important;min-height:0!important;
    overflow:hidden!important;flex-shrink:0!important;
    box-shadow:0 10px 24px rgba(0,0,0,.32)!important;border-radius:0 0 10px 10px
  }"""

IDX_WIN_NEW = """  body.catalog-portable.display-sides #catalogIndex:not(.is-embedded):not(.is-collapsed){
    position:sticky!important;top:0!important;z-index:12!important;
    height:var(--sides-index-h,min(48dvh,28rem))!important;
    max-height:min(70dvh,40rem)!important;min-height:0!important;
    overflow:hidden!important;flex-shrink:0!important;
    box-shadow:0 10px 24px rgba(0,0,0,.32)!important;border-radius:0 0 10px 10px
  }"""

SYNC_OLD = """function portableSyncModeFromMenus(which){
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
}"""

SYNC_NEW = """function portableSyncModeFromMenus(which){
  if(!window.CATALOG_PORTABLE)return;
  var fsNow=typeof portableMenuFsOn==='function'?portableMenuFsOn():'';
  // #region agent log
  try{
    fetch('http://127.0.0.1:7529/ingest/1cf46354-1d61-4c80-bd72-a340f1db1b51',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'c00e3e'},body:JSON.stringify({sessionId:'c00e3e',runId:'post-fix',hypothesisId:'E',location:'portable:syncModeFromMenus',message:'menu switch',data:{which:which||'',fsNow:fsNow||'',mid:document.body.classList.contains('display-middle'),searchCol:document.body.classList.contains('search-chrome-collapsed'),kwCol:document.body.classList.contains('kw-chrome-collapsed'),kwOpen:document.body.classList.contains('kw-open'),last:typeof portableMiddleLast==='string'?portableMiddleLast:'',vis:typeof portableMiddleVisible==='function'?portableMiddleVisible():''},timestamp:Date.now()})}).catch(function(){});
  }catch(eDbgE){}
  // #endregion
  if(fsNow){
    if((which==='search'||which==='keywords')&&fsNow!==which&&typeof portableEnterMenuFs==='function')portableEnterMenuFs(which);
    if(document.body.classList.contains('display-middle')&&which&&typeof portableCoerceMiddleMenu==='function')portableCoerceMiddleMenu(which==='keywords'?'keywords':'search');
    return;
  }
  var m=portableMenusOpenNow();
  if(!m.searchOn&&!m.kwOn){
    if(typeof setDisplayMode==='function')setDisplayMode('content',{keepMenus:true});
    return;
  }
  var want=portableWantLayout();
  var docked=document.body.classList.contains('display-sides')||document.body.classList.contains('display-middle');
  if(!docked){
    if(typeof setDisplayMode==='function')setDisplayMode(want,{keepMenus:true,pick:true,menu:which});
  }else if(want==='sides'&&document.body.classList.contains('display-middle')){
    if(typeof setDisplayMode==='function')setDisplayMode('sides',{keepMenus:true,pick:true,menu:which});
  }
  if(document.body.classList.contains('display-middle')&&which&&typeof portableCoerceMiddleMenu==='function'){
    portableCoerceMiddleMenu(which==='keywords'?'keywords':'search');
  }
}"""

VISIBLE_OLD = """function portableMiddleVisible(){
  if(!document.body.classList.contains('display-middle'))return '';
  if(!document.body.classList.contains('search-chrome-collapsed'))return 'search';
  var fw=document.getElementById('filterWrap');
  if(!document.body.classList.contains('kw-chrome-collapsed')&&fw&&(fw.classList.contains('open')||document.body.classList.contains('kw-open')))return 'keywords';
  return '';
}"""

VISIBLE_NEW = """function portableMiddleVisible(){
  if(!document.body.classList.contains('display-middle'))return '';
  var fs=typeof portableMenuFsOn==='function'?portableMenuFsOn():'';
  if(fs)return fs;
  var fw=document.getElementById('filterWrap');
  var kwOn=!document.body.classList.contains('kw-chrome-collapsed')&&!!(fw&&(fw.classList.contains('open')||document.body.classList.contains('kw-open')));
  var searchOn=!document.body.classList.contains('search-chrome-collapsed');
  if(kwOn&&(!searchOn||portableMiddleLast==='keywords'))return 'keywords';
  if(searchOn)return 'search';
  if(kwOn)return 'keywords';
  return '';
}"""

COERCE_MID_OLD = """    if(window.CATALOG_PORTABLE&&typeof portableCoerceMiddleMenu==='function'){
      var midBoth=!document.body.classList.contains('search-chrome-collapsed')&&!document.body.classList.contains('kw-chrome-collapsed')&&document.body.classList.contains('kw-open');
      if(midBoth)portableCoerceMiddleMenu(typeof portableMiddleLast==='string'&&portableMiddleLast?portableMiddleLast:'search');
    }"""

COERCE_MID_NEW = """    if(window.CATALOG_PORTABLE&&typeof portableCoerceMiddleMenu==='function'){
      if(opts.menu==='search'||opts.menu==='keywords')portableCoerceMiddleMenu(opts.menu);
      else{
        var midBoth=!document.body.classList.contains('search-chrome-collapsed')&&!document.body.classList.contains('kw-chrome-collapsed')&&document.body.classList.contains('kw-open');
        if(midBoth)portableCoerceMiddleMenu(typeof portableMiddleLast==='string'&&portableMiddleLast?portableMiddleLast:'search');
      }
    }"""

COERCE_END_OLD = """    if(document.body.classList.contains('display-middle')&&typeof portableCoerceMiddleMenu==='function'){
      var midBothEnd=!document.body.classList.contains('search-chrome-collapsed')&&!document.body.classList.contains('kw-chrome-collapsed')&&document.body.classList.contains('kw-open');
      if(midBothEnd)portableCoerceMiddleMenu(portableMiddleLast||'search');
    }"""

COERCE_END_NEW = """    if(document.body.classList.contains('display-middle')&&typeof portableCoerceMiddleMenu==='function'){
      if(opts.menu==='search'||opts.menu==='keywords')portableCoerceMiddleMenu(opts.menu);
      else{
        var midBothEnd=!document.body.classList.contains('search-chrome-collapsed')&&!document.body.classList.contains('kw-chrome-collapsed')&&document.body.classList.contains('kw-open');
        if(midBothEnd)portableCoerceMiddleMenu(portableMiddleLast||'search');
      }
    }"""

HDR_SEARCH_MID_OLD = """  if(window.CATALOG_PORTABLE&&document.body.classList.contains('display-middle')){
    var visS=typeof portableMiddleVisible==='function'?portableMiddleVisible():'';
    if(visS==='search'){if(typeof collapseSearchMenu==='function')collapseSearchMenu();}
    else if(typeof portableCoerceMiddleMenu==='function')portableCoerceMiddleMenu('search');
    if(typeof placePortableHandles==='function')placePortableHandles();
    syncHdrMenuBtns();
    if(typeof portableSyncModeFromMenus==='function')portableSyncModeFromMenus('search');
    return;
  }"""

HDR_SEARCH_MID_NEW = """  if(window.CATALOG_PORTABLE&&document.body.classList.contains('display-middle')){
    var visS=typeof portableMiddleVisible==='function'?portableMiddleVisible():'';
    var fsS=typeof portableMenuFsOn==='function'?portableMenuFsOn():'';
    if(fsS==='keywords'||visS==='keywords'){
      if(fsS==='keywords'&&typeof portableEnterMenuFs==='function')portableEnterMenuFs('search');
      if(typeof portableCoerceMiddleMenu==='function')portableCoerceMiddleMenu('search');
    }else if(visS==='search'){
      if(typeof collapseSearchMenu==='function')collapseSearchMenu();
    }else if(typeof portableCoerceMiddleMenu==='function')portableCoerceMiddleMenu('search');
    if(typeof placePortableHandles==='function')placePortableHandles();
    syncHdrMenuBtns();
    if(typeof portableSyncModeFromMenus==='function')portableSyncModeFromMenus('search');
    return;
  }"""

SETMODE_OLD = """   if(mode==='search'&&currentMode==='search'){
     // Search pill while already in Search: bring Search chrome up correctly (do not exit Search).
     document.querySelectorAll('.mode-btn').forEach(function(b){b.classList.toggle('active',b.dataset.mode==='search');});
     document.body.classList.add('search-mode');
     if(typeof expandSearchMenu==='function')expandSearchMenu();"""

SETMODE_NEW = """   if(mode==='search'&&currentMode==='search'){
     // Search pill while already in Search: bring Search chrome up correctly (do not exit Search).
     document.querySelectorAll('.mode-btn').forEach(function(b){b.classList.toggle('active',b.dataset.mode==='search');});
     document.body.classList.add('search-mode');
     if(window.CATALOG_PORTABLE){
       var fsM=typeof portableMenuFsOn==='function'?portableMenuFsOn():'';
       if(fsM==='keywords'&&typeof portableEnterMenuFs==='function')portableEnterMenuFs('search');
       if(document.body.classList.contains('display-middle')&&typeof portableCoerceMiddleMenu==='function')portableCoerceMiddleMenu('search');
       else if(typeof expandSearchMenu==='function')expandSearchMenu();
     }else if(typeof expandSearchMenu==='function')expandSearchMenu();"""

PATCH_OLD = """   if(activeCat==='patch'){
     var pcounts={};
     hits.forEach(function(el){patches(el).forEach(function(k){if(active.indexOf(k)<0&&usefulPatchToken(k))pcounts[k]=(pcounts[k]||0)+1;});});
     Object.keys(pcounts).sort(function(a,b){return (pcounts[b]-pcounts[a])||(a<b?-1:a>b?1:0);}).slice(0,PATCH_BAR_CAP).forEach(function(k){"""

PATCH_NEW = """   if(activeCat==='patch'){
     var pcounts={};
     hits.forEach(function(el){patches(el).forEach(function(k){if(active.indexOf(k)<0&&usefulPatchToken(k))pcounts[k]=(pcounts[k]||0)+1;});});
     if(!Object.keys(pcounts).length){
       Object.keys(patchCounts).forEach(function(k){if(active.indexOf(k)<0&&usefulPatchToken(k))pcounts[k]=patchCounts[k]||0;});
     }
     Object.keys(pcounts).sort(function(a,b){return (pcounts[b]-pcounts[a])||(a<b?-1:a<b?1:0);}).slice(0,PATCH_BAR_CAP).forEach(function(k){"""

# Fix the sort typo I almost introduced: (a<b?-1:a<b?1:0) is wrong. Keep original.

PATCH_NEW = """   if(activeCat==='patch'){
     var pcounts={};
     hits.forEach(function(el){patches(el).forEach(function(k){if(active.indexOf(k)<0&&usefulPatchToken(k))pcounts[k]=(pcounts[k]||0)+1;});});
     if(!Object.keys(pcounts).length){
       Object.keys(patchCounts).forEach(function(k){if(active.indexOf(k)<0&&usefulPatchToken(k))pcounts[k]=patchCounts[k]||0;});
     }
     Object.keys(pcounts).sort(function(a,b){return (pcounts[b]-pcounts[a])||(a<b?-1:a>b?1:0);}).slice(0,PATCH_BAR_CAP).forEach(function(k){"""

RENDER_LOG = """   if(currentMode==='search'){
     if(searchKeywords.length)st.textContent=hits.length+' match(es) for: '+searchKeywords.join(' + '); else st.textContent='';
   }else if(sel.length)st.textContent=matching().length+' match(es) for: '+sel.join(' + '); else st.textContent='';
 }"""

RENDER_LOG_NEW = """   if(currentMode==='search'){
     if(searchKeywords.length)st.textContent=hits.length+' match(es) for: '+searchKeywords.join(' + '); else st.textContent='';
   }else if(sel.length)st.textContent=matching().length+' match(es) for: '+sel.join(' + '); else st.textContent='';
   // #region agent log
   try{
     var kbR=document.getElementById('kwbar');var fpR=document.getElementById('filterPanel')||document.querySelector('#filterWrap .filter-panel');var fwR=document.getElementById('filterWrap');
     fetch('http://127.0.0.1:7529/ingest/1cf46354-1d61-4c80-bd72-a340f1db1b51',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'c00e3e'},body:JSON.stringify({sessionId:'c00e3e',runId:'post-fix',hypothesisId:'C',location:'catalog:renderKwBar',message:'kw pills',data:{cat:activeCat,mode:currentMode,n:kbR?kbR.children.length:0,kbH:kbR?Math.round(kbR.getBoundingClientRect().height):0,kbFlex:kbR?getComputedStyle(kbR).flexGrow:'',fpH:fpR?Math.round(fpR.getBoundingClientRect().height):0,fwH:fwR?Math.round(fwR.getBoundingClientRect().height):0,kbOv:kbR?getComputedStyle(kbR).overflowY:'',fs:document.body.classList.contains('kw-fs-open')},timestamp:Date.now()})}).catch(function(){});
   }catch(eDbgC){}
   // #endregion
 }"""

SETCAT_OLD = """ window.setCat=function(cat){if(cat==='other')cat='all';activeCat=cat;document.querySelectorAll('.cat-btn').forEach(function(b){b.classList.toggle('active',b.dataset.cat===cat);});if(currentMode==='search')applySearch();else render();requestAnimationFrame(function(){requestAnimationFrame(function(){if(typeof jumpAcList==='function')jumpAcList(typeof typedQuery==='function'?typedQuery():((typeof searchInput!=='undefined'&&searchInput&&searchInput.value)||'').trim().toLowerCase(),{jumpCat:cat});});});};"""

SETCAT_NEW = """ window.setCat=function(cat){if(cat==='other')cat='all';activeCat=cat;document.querySelectorAll('.cat-btn').forEach(function(b){b.classList.toggle('active',b.dataset.cat===cat);});if(currentMode==='search')applySearch();else render();if(typeof renderKwBar==='function')renderKwBar();requestAnimationFrame(function(){requestAnimationFrame(function(){if(typeof jumpAcList==='function')jumpAcList(typeof typedQuery==='function'?typedQuery():((typeof searchInput!=='undefined'&&searchInput&&searchInput.value)||'').trim().toLowerCase(),{jumpCat:cat});});});};"""


def once(text, old, new, label):
    if old not in text:
        return text, f"MISSING {label}"
    if text.count(old) != 1:
        return text, f"COUNT {text.count(old)} {label}"
    return text.replace(old, new, 1), f"ok {label}"


def patch_all(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    notes = []
    portable = "portable" in path.name

    if CLEAR_BTN in text and CLEAR_TOOLBAR not in text:
        text = text.replace(CLEAR_BTN, "", 1)
        notes.append("removed cat-switch Clear")
    else:
        notes.append("cat-switch Clear already gone" if CLEAR_TOOLBAR in text else "NO cat-switch Clear")

    if CLEAR_TOOLBAR not in text:
        if MORE_BTN not in text:
            notes.append("NO more btn for Clear insert")
        else:
            text = text.replace(MORE_BTN, CLEAR_TOOLBAR + MORE_BTN, 1)
            notes.append("inserted toolbar Clear")
    else:
        notes.append("toolbar Clear exists")

    if CSS_CLEAR.strip() not in text:
        needle = ".cat-switch .tap-add-btn,.cat-switch .mode-btn.clear-all{flex:0 0 auto;min-height:2.25rem;align-self:center}"
        if needle in text:
            text = text.replace(needle, needle + CSS_CLEAR, 1)
            notes.append("clear css")
        else:
            notes.append("NO clear css anchor")

    text, n = once(text, LEAD_OLD, LEAD_NEW, "lead-clear")
    notes.append(n)

    if portable:
        if "portableMoreRowAdd(pop,'Clear'" in text:
            text = text.replace(
                "  portableMoreRowAdd(pop,'Clear',function(){if(typeof clearAllFilters==='function')clearAllFilters();},'Clear keywords');\n",
                "",
                1,
            )
            notes.append("removed portable more Clear")
        else:
            notes.append("portable more Clear already gone")
    else:
        if "phoneMoreAdd(pop,'Clear keywords'" in text:
            text = text.replace(
                "  phoneMoreAdd(pop,'Clear keywords',function(){if(typeof clearAllFilters==='function')clearAllFilters();});\n",
                "",
                1,
            )
            notes.append("removed desktop more Clear")
        else:
            notes.append("desktop more Clear already gone")

    if portable:
        if "fix-NAV-INDEX-KW" not in text:
            text += "\n" if not text.endswith("\n") else ""
            # append CSS before last closing - actually inject before last </style> if present
            idx = text.rfind("</style>")
            if idx != -1:
                text = text[:idx] + PORT_CSS + text[idx:]
                notes.append("port css before last style")
            else:
                text = text.replace("<style>", "<style>\n" + PORT_CSS, 1)
                notes.append("port css after first style")
        else:
            notes.append("port css exists")

        text, n = once(text, IDX_TOGGLE_OLD, IDX_TOGGLE_NEW, "idx-toggle")
        notes.append(n)
        text, n = once(text, FORCE_IDX_OLD, FORCE_IDX_NEW, "force-idx")
        notes.append(n)
        text, n = once(text, FIT_OLD, FIT_NEW, "idx-fit")
        notes.append(n)
        if FIT_WHEEL_OLD in text:
            text = text.replace(FIT_WHEEL_OLD, FIT_WHEEL_NEW, 1)
            notes.append("idx-wheel")
        text, n = once(text, SCROLL_OLD, SCROLL_NEW, "scroll-port")
        notes.append(n)
        text, n = once(text, KWBAR_FLEX_OLD, KWBAR_FLEX_NEW, "kwbar-flex")
        notes.append(n)
        text, n = once(text, IDX_REL_OLD, IDX_REL_NEW, "idx-rel")
        notes.append(n)
        text, n = once(text, IDX_WIN_OLD, IDX_WIN_NEW, "idx-win")
        notes.append(n)
        text, n = once(text, SYNC_OLD, SYNC_NEW, "sync-menus")
        notes.append(n)
        text, n = once(text, VISIBLE_OLD, VISIBLE_NEW, "mid-vis")
        notes.append(n)
        text, n = once(text, COERCE_MID_OLD, COERCE_MID_NEW, "coerce-mid")
        notes.append(n)
        text, n = once(text, COERCE_END_OLD, COERCE_END_NEW, "coerce-end")
        notes.append(n)
        text, n = once(text, HDR_SEARCH_MID_OLD, HDR_SEARCH_MID_NEW, "hdr-search")
        notes.append(n)
        text, n = once(text, SETMODE_OLD, SETMODE_NEW, "setmode")
        notes.append(n)
        text, n = once(text, PATCH_OLD, PATCH_NEW, "patch-pills")
        notes.append(n)
        if "catalog:renderKwBar" not in text:
            text, n = once(text, RENDER_LOG, RENDER_LOG_NEW, "render-log")
            notes.append(n)
        text, n = once(text, SETCAT_OLD, SETCAT_NEW, "setcat")
        notes.append(n)
    else:
        text, n = once(text, IDX_TOGGLE_DESK_OLD, IDX_TOGGLE_DESK_NEW, "desk-idx-toggle")
        notes.append(n)
        text, n = once(text, FORCE_IDX_OLD, FORCE_IDX_NEW, "desk-force-idx")
        notes.append(n)
        if PATCH_OLD in text:
            text, n = once(text, PATCH_OLD, PATCH_NEW, "desk-patch")
            notes.append(n)
        if SETCAT_OLD in text:
            text, n = once(text, SETCAT_OLD, SETCAT_NEW, "desk-setcat")
            notes.append(n)

    path.write_text(text, encoding="utf-8")
    return notes


def main() -> None:
    for path in ALL:
        notes = patch_all(path)
        print(path.name + ":")
        for n in notes:
            print(" ", n)


if __name__ == "__main__":
    main()
