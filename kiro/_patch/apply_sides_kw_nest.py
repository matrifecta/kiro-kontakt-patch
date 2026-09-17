#!/usr/bin/env python3
"""Desktop Sides: Keywords collapse nests into Search's column, then hides."""
from __future__ import annotations

import os
import tempfile
from pathlib import Path

ROOT = Path("/home/phnx/kiro-kontakt-patch")
FILES = [
    ROOT / "public/catalogs/KONTAKT-CATALOG.html",
    ROOT / "public/catalogs/DS-CATALOG.html",
]
MARK = "fix-SIDES-KW-NEST-v1"
MARK2 = "fix-SIDES-KW-NEST-v1b"
KEEP = (
    "c00e3e",
    "fix-DESKTOP-SK-PAIR",
    "fix-DESKTOP-FLIP-ARRANGE",
    MARK,
    MARK2,
)

CSS_OLD = (
    "}\n"
    "/* fix-MIDDLE-ONE-FILL-v2: landscape Middle one menu is a top band; never use --sides-lw (0px ghost) */\n"
)

CSS_NEW = (
    "}\n"
    "/* " + MARK + ": landscape Sides — Keywords nest under Search, then hide */\n"
    "@media(min-width:900px){\n"
    "  body.desk-landscape.display-sides:not(.display-middle):not(.catalog-portable).kw-nested-search:not(.search-chrome-collapsed):not(.kw-chrome-collapsed){\n"
    "    display:grid!important;flex-direction:unset!important;\n"
    "    grid-template-columns:var(--sides-lw,22vw) minmax(0,1fr)!important;\n"
    "    grid-template-rows:auto minmax(0,var(--sides-nested-h,38dvh)) minmax(0,1fr) var(--card-min-dock-h,0px)!important;\n"
    "    column-gap:var(--sides-pane-gap,6px)!important;row-gap:0!important\n"
    "  }\n"
    "  body.desk-landscape.display-sides:not(.display-middle):not(.catalog-portable).kw-nested-search:not(.search-chrome-collapsed):not(.kw-chrome-collapsed).sides-portrait-flip{\n"
    "    grid-template-columns:minmax(0,1fr) var(--sides-lw,22vw)!important\n"
    "  }\n"
    "  body.desk-landscape.display-sides:not(.display-middle):not(.catalog-portable).kw-nested-search:not(.search-chrome-collapsed):not(.kw-chrome-collapsed) #searchChrome,\n"
    "  body.desk-landscape.display-sides:not(.display-middle):not(.catalog-portable).kw-nested-search:not(.search-chrome-collapsed):not(.kw-chrome-collapsed) #filterWrap{\n"
    "    width:100%!important;max-width:none!important;min-width:0!important;min-height:0!important;\n"
    "    align-self:stretch!important;position:relative!important;inset:auto!important;transform:none!important;flex:unset!important\n"
    "  }\n"
    "  body.desk-landscape.display-sides:not(.display-middle):not(.catalog-portable).kw-nested-search:not(.search-chrome-collapsed):not(.kw-chrome-collapsed) #searchChrome{\n"
    "    grid-column:1!important;grid-row:2!important;height:100%!important;max-height:none!important;\n"
    "    overflow:hidden!important;border-bottom:1px solid var(--border)!important;margin-bottom:0!important\n"
    "  }\n"
    "  body.desk-landscape.display-sides:not(.display-middle):not(.catalog-portable).kw-nested-search:not(.search-chrome-collapsed):not(.kw-chrome-collapsed) #filterWrap{\n"
    "    display:flex!important;grid-column:1!important;grid-row:3!important;height:100%!important;max-height:none!important;overflow:hidden!important\n"
    "  }\n"
    "  body.desk-landscape.display-sides:not(.display-middle):not(.catalog-portable).kw-nested-search:not(.search-chrome-collapsed):not(.kw-chrome-collapsed) #catalogMain{\n"
    "    grid-column:2!important;grid-row:2/4!important;height:auto!important;min-height:0!important;align-self:stretch!important;flex:unset!important\n"
    "  }\n"
    "  body.desk-landscape.display-sides:not(.display-middle):not(.catalog-portable).kw-nested-search.sides-portrait-flip:not(.search-chrome-collapsed):not(.kw-chrome-collapsed) #searchChrome,\n"
    "  body.desk-landscape.display-sides:not(.display-middle):not(.catalog-portable).kw-nested-search.sides-portrait-flip:not(.search-chrome-collapsed):not(.kw-chrome-collapsed) #filterWrap{\n"
    "    grid-column:2!important\n"
    "  }\n"
    "  body.desk-landscape.display-sides:not(.display-middle):not(.catalog-portable).kw-nested-search.sides-portrait-flip:not(.search-chrome-collapsed):not(.kw-chrome-collapsed) #catalogMain{\n"
    "    grid-column:1!important\n"
    "  }\n"
    "  body.desk-landscape.display-sides:not(.display-middle):not(.catalog-portable).kw-nested-search.layout-edit:not(.search-chrome-collapsed):not(.kw-chrome-collapsed) #searchSplit{\n"
    "    display:block!important;width:auto!important;min-width:0!important;max-width:none!important;\n"
    "    height:12px!important;min-height:12px!important;max-height:12px!important;cursor:ns-resize!important;pointer-events:auto!important;z-index:80!important\n"
    "  }\n"
    "  body.desk-landscape.display-sides:not(.display-middle):not(.catalog-portable).kw-nested-search.layout-edit:not(.search-chrome-collapsed):not(.kw-chrome-collapsed) #dualFsSep{\n"
    "    display:block!important;width:12px!important;min-width:12px!important;max-width:12px!important;cursor:ew-resize!important;pointer-events:auto!important;z-index:80!important\n"
    "  }\n"
    "  body.desk-landscape.display-sides:not(.display-middle):not(.catalog-portable).kw-nested-search.layout-edit #searchSplit::before{\n"
    "    content:'';display:block;background:var(--border,rgba(128,128,128,0.5));border-radius:2px;opacity:.6;\n"
    "    position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);width:24px;height:2px\n"
    "  }\n"
    "  body.desk-landscape.display-sides:not(.display-middle):not(.catalog-portable).kw-nested-search.layout-edit #dualFsSep::before{\n"
    "    content:'';display:block;background:var(--border,rgba(128,128,128,0.5));border-radius:2px;opacity:.6;\n"
    "    position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);width:2px;height:24px\n"
    "  }\n"
    "}\n"
    "/* fix-MIDDLE-ONE-FILL-v2: landscape Middle one menu is a top band; never use --sides-lw (0px ghost) */\n"
)

TOGGLE_FILTER_OLD = (
    "  if(document.body.classList.contains('display-sides')){\n"
    "    if(typeof toggleKwChrome==='function')toggleKwChrome();\n"
    "    if(typeof syncHdrMenuBtns==='function')syncHdrMenuBtns();\n"
)

TOGGLE_FILTER_NEW = (
    "  if(document.body.classList.contains('display-sides')){\n"
    "    if(typeof toggleKwChrome==='function')toggleKwChrome({fromArrow:true});\n"
    "    if(typeof syncHdrMenuBtns==='function')syncHdrMenuBtns();\n"
)

COLLAPSE_SEARCH_OLD = (
    "  document.body.classList.add('search-chrome-collapsed','search-extras-collapsed');\n"
    "  syncSearchHideBtn();\n"
)

COLLAPSE_SEARCH_NEW = (
    "  document.body.classList.add('search-chrome-collapsed','search-extras-collapsed');\n"
    "  document.body.classList.remove('kw-nested-search');\n"
    "  syncSearchHideBtn();\n"
)

KW_FNS_OLD = """function collapseKwMenu(){
  if(typeof snapshotCurrentLayoutBucket==='function'){snapshotCurrentLayoutBucket();lastLayoutBucket='pending';}
  var w=document.getElementById('filterWrap');
  if(w)w.classList.remove('open');
  document.body.classList.remove('kw-open');
  document.body.classList.add('kw-chrome-collapsed');
  if(typeof kwFsWanted!=='undefined')kwFsWanted=false;
  document.body.classList.remove('kw-fs-open');
  if(typeof syncKwHideBtn==='function')syncKwHideBtn();
  if(typeof syncSearchHideBtn==='function')syncSearchHideBtn();
  if(typeof applySidesCols==='function')applySidesCols();
  if(typeof syncHdrMenuBtns==='function')syncHdrMenuBtns();

}
function expandKwMenu(){
  if(typeof snapshotCurrentLayoutBucket==='function'){snapshotCurrentLayoutBucket();lastLayoutBucket='pending';}
  document.body.classList.remove('kw-chrome-collapsed');
  var w=document.getElementById('filterWrap');
  if(w)w.classList.add('open');
  document.body.classList.add('kw-open');
  if(typeof noteMiddleMenuOpened==='function')noteMiddleMenuOpened('keywords');
  var a=document.querySelector('#filterToggle .toggle-arrow')||document.querySelector('.toggle-arrow');
  if(a)a.textContent='▲';
  if(typeof syncKwHideBtn==='function')syncKwHideBtn();
  if(typeof syncSearchHideBtn==='function')syncSearchHideBtn();
  if(typeof applySidesCols==='function')applySidesCols();
  if(typeof window.restoreFilterUi==='function')window.restoreFilterUi();
}
function toggleKwChrome(){
  if(!document.body.classList.contains('display-sides')){
    if(typeof toggleFilter==='function')toggleFilter();
    return;
  }
  if(document.body.classList.contains('kw-chrome-collapsed')) expandKwMenu();
  else collapseKwMenu();
}
"""

KW_FNS_NEW = r"""function logKwNest(phase,extra){
  // #region agent log
  try{
    extra=extra||{};
    var sc=document.getElementById('searchChrome'),fw=document.getElementById('filterWrap'),cm=document.getElementById('catalogMain');
    function box(el){if(!el)return null;var r=el.getBoundingClientRect();return {x:Math.round(r.x),y:Math.round(r.y),w:Math.round(r.width),h:Math.round(r.height),t:Math.round(r.top),b:Math.round(r.bottom),l:Math.round(r.left),r:Math.round(r.right)};}
    fetch('http://127.0.0.1:7529/ingest/1cf46354-1d61-4c80-bd72-a340f1db1b51',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'c00e3e'},body:JSON.stringify({sessionId:'c00e3e',runId:'kw-nest',hypothesisId:'N',location:'catalog:logKwNest',message:'kw-nest',data:{phase:String(phase||''),nested:document.body.classList.contains('kw-nested-search'),kwHid:document.body.classList.contains('kw-chrome-collapsed'),sOn:!document.body.classList.contains('search-chrome-collapsed'),flip:document.body.classList.contains('sides-portrait-flip'),land:document.body.classList.contains('desk-landscape'),middle:document.body.classList.contains('display-middle'),fromArrow:!!extra.fromArrow,search:box(sc),kw:box(fw),main:box(cm),nh:(getComputedStyle(document.documentElement).getPropertyValue('--sides-nested-h')||'').trim()},timestamp:Date.now()})}).catch(function(){});
  }catch(eNestLog){}
  // #endregion
}
function sidesKwCanNest(){
  if(window.CATALOG_PORTABLE)return false;
  if(!document.body.classList.contains('display-sides'))return false;
  if(document.body.classList.contains('display-middle'))return false;
  if(document.body.classList.contains('search-chrome-collapsed'))return false;
  if(!(typeof displayIsDesktop==='function'?displayIsDesktop():!!(window.matchMedia&&window.matchMedia('(min-width:900px)').matches)))return false;
  if(typeof isPortraitDesktopSides==='function'&&isPortraitDesktopSides())return false;
  return true;
}
function sidesNestedHKey(){return typeof liveLayoutKey==='function'?liveLayoutKey('catalog-sides-nested-h-'):('catalog-sides-nested-h-'+(window.CATALOG_NS||'catalog'));}
function sidesNestedDefaults(){
  var hdr=document.querySelector('.catalog-header');
  var top=hdr?Math.round(hdr.getBoundingClientRect().height):56;
  var availH=Math.max(220,(window.innerHeight||800)-top);
  return {availH:availH,searchH:Math.round(availH*0.42),minH:Math.max(120,Math.round(availH*0.18)),minKw:Math.max(140,Math.round(availH*0.18))};
}
function clampSidesNestedH(val,d){
  d=d||sidesNestedDefaults();
  val=Number(val);if(!isFinite(val))val=d.searchH;
  return Math.round(Math.max(d.minH,Math.min(d.availH-d.minKw,val)));
}
function writeSidesNestedH(h){
  if(typeof sidesPinned!=='undefined'&&sidesPinned)return;
  if(typeof modeLayoutPinned==='function'&&modeLayoutPinned())return;
  h=clampSidesNestedH(h);
  try{localStorage.setItem(sidesNestedHKey(),h+'px');}catch(err){}
  document.documentElement.style.setProperty('--sides-nested-h',h+'px');
}
function applySidesNestedH(){
  if(!document.body.classList.contains('kw-nested-search'))return;
  var d=sidesNestedDefaults();
  var raw='';
  try{raw=localStorage.getItem(sidesNestedHKey())||localStorage.getItem('catalog-portrait-menu-h')||'';}catch(err){}
  var n=parseInt(raw,10);
  var h=clampSidesNestedH((isFinite(n)&&n>0)?n:d.searchH,d);
  document.documentElement.style.setProperty('--sides-nested-h',h+'px');
}
function syncKwNestedClass(){
  if(window.CATALOG_PORTABLE||!document.body.classList.contains('display-sides')||document.body.classList.contains('display-middle')||document.body.classList.contains('search-chrome-collapsed')||document.body.classList.contains('kw-chrome-collapsed')){
    document.body.classList.remove('kw-nested-search');
  }
}
function nestKwWithSearch(){
  if(typeof snapshotCurrentLayoutBucket==='function'){snapshotCurrentLayoutBucket();lastLayoutBucket='pending';}
  if(!sidesKwCanNest()){
    collapseKwMenu();
    return;
  }
  document.body.classList.remove('kw-chrome-collapsed');
  var w=document.getElementById('filterWrap');
  if(w)w.classList.add('open');
  document.body.classList.add('kw-open','kw-nested-search');
  var a=document.querySelector('#filterToggle .toggle-arrow')||document.querySelector('.toggle-arrow');
  if(a)a.textContent='▲';
  if(typeof syncKwHideBtn==='function')syncKwHideBtn();
  if(typeof syncSearchHideBtn==='function')syncSearchHideBtn();
  if(typeof applySidesCols==='function')applySidesCols();
  if(typeof syncHdrMenuBtns==='function')syncHdrMenuBtns();
  logKwNest('nest');
}
function collapseKwMenu(){
  if(typeof snapshotCurrentLayoutBucket==='function'){snapshotCurrentLayoutBucket();lastLayoutBucket='pending';}
  var w=document.getElementById('filterWrap');
  if(w)w.classList.remove('open');
  document.body.classList.remove('kw-open','kw-nested-search');
  document.body.classList.add('kw-chrome-collapsed');
  if(typeof kwFsWanted!=='undefined')kwFsWanted=false;
  document.body.classList.remove('kw-fs-open');
  if(typeof syncKwHideBtn==='function')syncKwHideBtn();
  if(typeof syncSearchHideBtn==='function')syncSearchHideBtn();
  if(typeof applySidesCols==='function')applySidesCols();
  if(typeof syncHdrMenuBtns==='function')syncHdrMenuBtns();
  logKwNest('hide');
}
function expandKwMenu(){
  if(typeof snapshotCurrentLayoutBucket==='function'){snapshotCurrentLayoutBucket();lastLayoutBucket='pending';}
  document.body.classList.remove('kw-chrome-collapsed');
  var w=document.getElementById('filterWrap');
  if(w)w.classList.add('open');
  document.body.classList.add('kw-open');
  if(typeof sidesKwCanNest==='function'&&sidesKwCanNest())document.body.classList.add('kw-nested-search');
  else document.body.classList.remove('kw-nested-search');
  if(typeof noteMiddleMenuOpened==='function')noteMiddleMenuOpened('keywords');
  var a=document.querySelector('#filterToggle .toggle-arrow')||document.querySelector('.toggle-arrow');
  if(a)a.textContent='▲';
  if(typeof syncKwHideBtn==='function')syncKwHideBtn();
  if(typeof syncSearchHideBtn==='function')syncSearchHideBtn();
  if(typeof applySidesCols==='function')applySidesCols();
  if(typeof window.restoreFilterUi==='function')window.restoreFilterUi();
  if(typeof syncHdrMenuBtns==='function')syncHdrMenuBtns();
  logKwNest('expand');
}
function toggleKwChrome(opts){
  opts=opts||{};
  if(!document.body.classList.contains('display-sides')){
    if(typeof toggleFilter==='function')toggleFilter();
    return;
  }
  if(document.body.classList.contains('kw-chrome-collapsed')){
    expandKwMenu();
    return;
  }
  if(opts.fromArrow&&typeof sidesKwCanNest==='function'&&sidesKwCanNest()&&!document.body.classList.contains('kw-nested-search')){
    nestKwWithSearch();
    return;
  }
  collapseKwMenu();
}
"""

EXPORT_OLD = (
    "window.collapseKwMenu=collapseKwMenu;\n"
    "window.expandKwMenu=expandKwMenu;\n"
    "window.toggleKwChrome=toggleKwChrome;\n"
)

EXPORT_NEW = (
    "window.logKwNest=logKwNest;\n"
    "window.sidesKwCanNest=sidesKwCanNest;\n"
    "window.nestKwWithSearch=nestKwWithSearch;\n"
    "window.applySidesNestedH=applySidesNestedH;\n"
    "window.writeSidesNestedH=writeSidesNestedH;\n"
    "window.syncKwNestedClass=syncKwNestedClass;\n"
    "window.collapseKwMenu=collapseKwMenu;\n"
    "window.expandKwMenu=expandKwMenu;\n"
    "window.toggleKwChrome=toggleKwChrome;\n"
)

SIDES_OFF_OLD = (
    "    document.body.classList.remove('kw-chrome-collapsed');\n"
    "    ['searchSplit','dualFsSep'].forEach(function(id){var el=document.getElementById(id);if(el)el.removeAttribute('style');});\n"
)

SIDES_OFF_NEW = (
    "    document.body.classList.remove('kw-chrome-collapsed','kw-nested-search');\n"
    "    ['searchSplit','dualFsSep'].forEach(function(id){var el=document.getElementById(id);if(el)el.removeAttribute('style');});\n"
)

GEO_OLD = "kOn:!document.body.classList.contains('kw-chrome-collapsed'),fwP:"
GEO_NEW = "kOn:!document.body.classList.contains('kw-chrome-collapsed'),nested:document.body.classList.contains('kw-nested-search'),fwP:"

GEO2_OLD = "kOn:!document.body.classList.contains('kw-chrome-collapsed'),kwOpen:"
GEO2_NEW = "kOn:!document.body.classList.contains('kw-chrome-collapsed'),nested:document.body.classList.contains('kw-nested-search'),kwOpen:"

GEO3_OLD = "kOn:!document.body.classList.contains('kw-chrome-collapsed'),flip:"
GEO3_NEW = "kOn:!document.body.classList.contains('kw-chrome-collapsed'),nested:document.body.classList.contains('kw-nested-search'),flip:"

APPLY_NEST_H_OLD = (
    "  if(typeof applyPortraitSides==='function')applyPortraitSides();\n"
    "  placeSidesHandles();\n"
)

APPLY_NEST_H_NEW = (
    "  if(typeof syncKwNestedClass==='function')syncKwNestedClass();\n"
    "  if(typeof applySidesNestedH==='function')applySidesNestedH();\n"
    "  if(typeof applyPortraitSides==='function')applyPortraitSides();\n"
    "  placeSidesHandles();\n"
)

PLACE_OLD = (
    "  if(typeof isPortraitDesktopSides==='function'&&isPortraitDesktopSides()){\n"
    "    if(typeof placePortraitSidesHandles==='function')placePortraitSidesHandles();\n"
    "    return;\n"
    "  }\n"
    "  var split=document.getElementById('searchSplit');\n"
)

PLACE_NEW = (
    "  if(typeof isPortraitDesktopSides==='function'&&isPortraitDesktopSides()){\n"
    "    if(typeof placePortraitSidesHandles==='function')placePortraitSidesHandles();\n"
    "    return;\n"
    "  }\n"
    "  if(document.body.classList.contains('kw-nested-search')){\n"
    "    if(typeof placePortraitSidesHandles==='function')placePortraitSidesHandles();\n"
    "    return;\n"
    "  }\n"
    "  var split=document.getElementById('searchSplit');\n"
)

DOWN_OLD = (
    "      return;\n"
    "    }\n"
    "    var vw=window.innerWidth||1200;\n"
    "    var t=e.currentTarget||e.target;\n"
    "    drag={which:which,x:e.clientX,lw:parseInt(getComputedStyle(document.body).getPropertyValue('--sides-lw'),10)||Math.round(vw*0.22),rw:parseInt(getComputedStyle(document.body).getPropertyValue('--sides-rw'),10)||Math.round(vw*0.26),id:e.pointerId};\n"
)

DOWN_NEW = (
    "      return;\n"
    "    }\n"
    "    if(document.body.classList.contains('kw-nested-search')){\n"
    "      var dN=typeof sidesNestedDefaults==='function'?sidesNestedDefaults():{availH:400,searchH:180,minH:120,minKw:140};\n"
    "      var vwN=window.innerWidth||1200;\n"
    "      var tN=e.currentTarget||e.target;\n"
    "      var nhN=parseInt(getComputedStyle(document.documentElement).getPropertyValue('--sides-nested-h'),10)||dN.searchH;\n"
    "      drag={nested:true,which:which,x:e.clientX,y:e.clientY,lw:parseInt(getComputedStyle(document.body).getPropertyValue('--sides-lw'),10)||Math.round(vwN*0.22),mh:nhN,flip:document.body.classList.contains('sides-portrait-flip'),def:dN,id:e.pointerId};\n"
    "      try{if(tN&&tN.setPointerCapture)tN.setPointerCapture(e.pointerId);}catch(err){}\n"
    "      return;\n"
    "    }\n"
    "    var vw=window.innerWidth||1200;\n"
    "    var t=e.currentTarget||e.target;\n"
    "    drag={which:which,x:e.clientX,lw:parseInt(getComputedStyle(document.body).getPropertyValue('--sides-lw'),10)||Math.round(vw*0.22),rw:parseInt(getComputedStyle(document.body).getPropertyValue('--sides-rw'),10)||Math.round(vw*0.26),id:e.pointerId};\n"
)

MOVE_OLD = (
    "      placeSidesHandles();\n"
    "      return;\n"
    "    }\n"
    "    var vw=window.innerWidth||1200;\n"
    "    var minL=240,minR=260,minC=280;\n"
    "    if(drag.which==='split'){\n"
)

MOVE_NEW = (
    "      placeSidesHandles();\n"
    "      return;\n"
    "    }\n"
    "    if(drag.nested){\n"
    "      if(drag.which==='split'){\n"
    "        var mhN=typeof clampSidesNestedH==='function'?clampSidesNestedH(drag.mh+(e.clientY-drag.y),drag.def):Math.max(120,drag.mh+(e.clientY-drag.y));\n"
    "        document.documentElement.style.setProperty('--sides-nested-h',mhN+'px');\n"
    "      }else{\n"
    "        var vwN2=window.innerWidth||1200;\n"
    "        var minLN=240,minCN=280;\n"
    "        var gapN=2*(parseFloat(getComputedStyle(document.documentElement).getPropertyValue('--sides-pane-gap'))||6);\n"
    "        var dxN=e.clientX-drag.x;\n"
    "        var nlwN=Math.max(minLN,Math.min(vwN2-minCN-gapN,drag.flip?drag.lw-dxN:drag.lw+dxN));\n"
    "        document.body.style.setProperty('--sides-lw',nlwN+'px');\n"
    "      }\n"
    "      placeSidesHandles();\n"
    "      return;\n"
    "    }\n"
    "    var vw=window.innerWidth||1200;\n"
    "    var minL=240,minR=260,minC=280;\n"
    "    if(drag.which==='split'){\n"
)

UP_OLD = (
    "      drag=null;\n"
    "\n"
    "      return;\n"
    "    }\n"
    "    var lw=parseInt(getComputedStyle(document.body).getPropertyValue('--sides-lw'),10)||0;\n"
    "    var rw=parseInt(getComputedStyle(document.body).getPropertyValue('--sides-rw'),10)||0;\n"
)

UP_NEW = (
    "      drag=null;\n"
    "\n"
    "      return;\n"
    "    }\n"
    "    if(drag.nested){\n"
    "      var lwN=parseInt(getComputedStyle(document.body).getPropertyValue('--sides-lw'),10)||0;\n"
    "      var nhU=parseInt(getComputedStyle(document.documentElement).getPropertyValue('--sides-nested-h'),10)||0;\n"
    "      if(typeof writeSidesNestedH==='function')writeSidesNestedH(nhU);\n"
    "      if(typeof writeSidesCols==='function')writeSidesCols(lwN,parseInt(getComputedStyle(document.body).getPropertyValue('--sides-rw'),10)||0);\n"
    "      drag=null;\n"
    "      return;\n"
    "    }\n"
    "    var lw=parseInt(getComputedStyle(document.body).getPropertyValue('--sides-lw'),10)||0;\n"
    "    var rw=parseInt(getComputedStyle(document.body).getPropertyValue('--sides-rw'),10)||0;\n"
)

DISPLAY_OLD = "document.body.classList.remove('search-chrome-collapsed','search-extras-collapsed','kw-chrome-collapsed');"
DISPLAY_NEW = "document.body.classList.remove('search-chrome-collapsed','search-extras-collapsed','kw-chrome-collapsed','kw-nested-search');"

PROFILE_OLD = "var keys=['--sides-lw','--sides-rw','--sides-index-h','--middle-lw','--middle-rw','--middle-menu-h','--portable-lw','--portrait-lw','--portrait-rw','--portrait-menu-h','--fs-ac-h','--fs-kw-h'];"
PROFILE_NEW = "var keys=['--sides-lw','--sides-rw','--sides-index-h','--sides-nested-h','--middle-lw','--middle-rw','--middle-menu-h','--portable-lw','--portrait-lw','--portrait-rw','--portrait-menu-h','--fs-ac-h','--fs-kw-h'];"

PERSIST_OLD = """  try{
    if(typeof displayIsMiddle==='function'&&displayIsMiddle()&&typeof writeMiddleLayout==='function'){
      var ml=parseInt(getComputedStyle(document.documentElement).getPropertyValue('--middle-lw'),10)||0;
      var mh=parseInt(getComputedStyle(document.documentElement).getPropertyValue('--middle-menu-h'),10)||0;
      writeMiddleLayout(ml,mh);
    }
  }catch(err){}
}
"""

PERSIST_NEW = """  try{
    if(typeof displayIsMiddle==='function'&&displayIsMiddle()&&typeof writeMiddleLayout==='function'){
      var ml=parseInt(getComputedStyle(document.documentElement).getPropertyValue('--middle-lw'),10)||0;
      var mh=parseInt(getComputedStyle(document.documentElement).getPropertyValue('--middle-menu-h'),10)||0;
      writeMiddleLayout(ml,mh);
    }
  }catch(err){}
  try{
    if(document.body.classList.contains('kw-nested-search')&&typeof writeSidesNestedH==='function'){
      var nH=parseInt(getComputedStyle(document.documentElement).getPropertyValue('--sides-nested-h'),10)||0;
      if(nH>40)writeSidesNestedH(nH);
    }
  }catch(err){}
}
"""

WRAP_OLD = """    window.toggleFilter=function(){
      var w=document.getElementById('filterWrap');
      if(document.body.classList.contains('display-sides')&&document.body.classList.contains('kw-chrome-collapsed')){
        if(typeof expandKwMenu==='function'){expandKwMenu();return;}
      }
      if(document.body.classList.contains('display-sides')&&w&&w.classList.contains('open')&&!document.body.classList.contains('kw-fs-open')){
        if(typeof collapseKwMenu==='function'){collapseKwMenu();return;}
      }
      _tf.apply(this,arguments);
      if(typeof applySidesCols==='function')applySidesCols();
    };
"""

WRAP_NEW = """    window.toggleFilter=function(){
      var w=document.getElementById('filterWrap');
      if(document.body.classList.contains('display-sides')&&document.body.classList.contains('kw-chrome-collapsed')){
        if(typeof expandKwMenu==='function'){expandKwMenu();return;}
      }
      if(document.body.classList.contains('display-sides')&&w&&w.classList.contains('open')&&!document.body.classList.contains('kw-fs-open')){
        if(typeof sidesKwCanNest==='function'&&sidesKwCanNest()&&!document.body.classList.contains('kw-nested-search')){
          if(typeof nestKwWithSearch==='function'){nestKwWithSearch();return;}
        }
        if(typeof collapseKwMenu==='function'){collapseKwMenu();return;}
      }
      _tf.apply(this,arguments);
      if(typeof applySidesCols==='function')applySidesCols();
    };
    /* """ + MARK2 + """ */
"""


def once(text: str, old: str, new: str, label: str, name: str, replace_all: bool = False) -> str:
    if old not in text:
        if new in text:
            print(f"  skip {label} {name}")
            return text
        raise SystemExit(f"{name}: missing {label}: {old[:140]!r}")
    n = text.count(old)
    if replace_all:
        print(f"  {n}x {label} {name}")
        return text.replace(old, new)
    if n != 1:
        raise SystemExit(f"{name}: {label} count {n}")
    print(f"  1x {label} {name}")
    return text.replace(old, new, 1)


def safe_write(path: Path, text: str) -> None:
    if not text.rstrip().endswith("</html>"):
        raise SystemExit(f"{path.name}: rewrite would drop </html>")
    raw = text.encode("utf-8")
    fd, tmp = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=str(path.parent))
    try:
        os.write(fd, raw)
        os.fsync(fd)
        os.close(fd)
        fd = -1
        tmp_path = Path(tmp)
        if not tmp_path.read_text(encoding="utf-8").rstrip().endswith("</html>"):
            tmp_path.unlink(missing_ok=True)
            raise SystemExit(f"{path.name}: tmp missing </html>")
        size = tmp_path.stat().st_size
        if size < 200_000:
            tmp_path.unlink(missing_ok=True)
            raise SystemExit(f"{path.name}: tmp too small {size}")
        os.replace(tmp, path)
        assert path.stat().st_size == size
        assert path.read_text(encoding="utf-8").rstrip().endswith("</html>")
        print(f"ok {path.name} bytes={size}")
    finally:
        if fd >= 0:
            try:
                os.close(fd)
            except OSError:
                pass
        if os.path.exists(tmp):
            os.unlink(tmp)


def patch(path: Path) -> None:
    name = path.name
    text = path.read_text(encoding="utf-8")
    c00 = text.count("sessionId:'c00e3e'")
    if MARK2 in text and "function nestKwWithSearch(" in text:
        print("skip", name)
        return
    if MARK not in text or "function nestKwWithSearch(" not in text:
        text = once(text, CSS_OLD, CSS_NEW, "css", name)
        text = once(text, TOGGLE_FILTER_OLD, TOGGLE_FILTER_NEW, "toggle-filter", name)
        text = once(text, COLLAPSE_SEARCH_OLD, COLLAPSE_SEARCH_NEW, "collapse-search", name)
        text = once(text, KW_FNS_OLD, KW_FNS_NEW, "kw-fns", name)
        text = once(text, EXPORT_OLD, EXPORT_NEW, "export", name)
        text = once(text, SIDES_OFF_OLD, SIDES_OFF_NEW, "sides-off", name)
        text = once(text, GEO_OLD, GEO_NEW, "geo1", name)
        text = once(text, GEO2_OLD, GEO2_NEW, "geo2", name)
        text = once(text, GEO3_OLD, GEO3_NEW, "geo3", name)
        text = once(text, APPLY_NEST_H_OLD, APPLY_NEST_H_NEW, "apply-h", name)
        text = once(text, PLACE_OLD, PLACE_NEW, "place", name)
        text = once(text, DOWN_OLD, DOWN_NEW, "drag-down", name)
        text = once(text, MOVE_OLD, MOVE_NEW, "drag-move", name)
        text = once(text, UP_OLD, UP_NEW, "drag-up", name)
        text = once(text, DISPLAY_OLD, DISPLAY_NEW, "display-remove", name, replace_all=True)
        text = once(text, PROFILE_OLD, PROFILE_NEW, "profile-css", name)
        text = once(text, PERSIST_OLD, PERSIST_NEW, "persist", name)
    text = once(text, WRAP_OLD, WRAP_NEW, "toggle-wrap", name)
    if MARK not in text:
        raise SystemExit(f"{name}: missing {MARK}")
    if MARK2 not in text:
        raise SystemExit(f"{name}: missing {MARK2}")
    if "function nestKwWithSearch(" not in text:
        raise SystemExit(f"{name}: missing nestKwWithSearch")
    after = text.count("sessionId:'c00e3e'")
    if after < c00:
        raise SystemExit(f"{name}: lost c00e3e logs {c00}->{after}")
    for keep in KEEP:
        if keep not in text:
            raise SystemExit(f"{name}: lost {keep}")
    safe_write(path, text)


def main() -> None:
    for p in FILES:
        if not p.exists():
            raise SystemExit(f"missing {p}")
        patch(p)


if __name__ == "__main__":
    main()
