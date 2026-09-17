#!/usr/bin/env python3
"""Portable: re-nest menu FS after chrome/orient changes; neutralize leftover half-cut CSS."""
from __future__ import annotations

import os
import tempfile
from pathlib import Path

ROOT = Path("/home/phnx/kiro-kontakt-patch/public/catalogs")
FILES = [
    ROOT / "KONTAKT-CATALOG-portable.html",
    ROOT / "DS-CATALOG-portable.html",
]

CSS_MARK = "</style></head>"
CSS_ADD = """
/* fix-PORTABLE-FS-RELAYOUT: one-menu FS fills leftover screen after chrome/orient change */
html body.catalog-portable.ac-fs-open:not(.kw-fs-open),
html body.catalog-portable.kw-fs-open:not(.ac-fs-open),
html body.catalog-portable.display-sides.ac-fs-open:not(.kw-fs-open),
html body.catalog-portable.display-sides.kw-fs-open:not(.ac-fs-open),
html body.catalog-portable.display-sides.display-middle.ac-fs-open:not(.kw-fs-open),
html body.catalog-portable.display-sides.display-middle.kw-fs-open:not(.ac-fs-open),
html body.catalog-portable.portable-landscape.ac-fs-open:not(.kw-fs-open),
html body.catalog-portable.portable-landscape.kw-fs-open:not(.ac-fs-open),
html body.catalog-portable.portable-landscape.display-sides.display-middle.ac-fs-open:not(.kw-fs-open),
html body.catalog-portable.portable-landscape.display-sides.display-middle.kw-fs-open:not(.ac-fs-open),
html body.catalog-portable.portable-landscape.display-sides.display-middle.search-chrome-collapsed.kw-open.kw-fs-open:not(.kw-chrome-collapsed):not(.ac-fs-open),
html body.catalog-portable.hdr-bar-hidden.ac-fs-open:not(.kw-fs-open),
html body.catalog-portable.hdr-bar-hidden.kw-fs-open:not(.ac-fs-open),
html body.catalog-portable.is-browser-fs.ac-fs-open:not(.kw-fs-open),
html body.catalog-portable.is-browser-fs.kw-fs-open:not(.ac-fs-open){
  display:grid!important;flex-direction:unset!important;
  grid-template-columns:minmax(0,1fr)!important;
  grid-template-rows:auto minmax(0,1fr)!important;
  height:var(--portable-vv-h,100dvh)!important;max-height:var(--portable-vv-h,100dvh)!important;
  overflow:hidden!important
}
html body.catalog-portable.ac-fs-open:not(.kw-fs-open) #searchChrome,
html body.catalog-portable.display-sides.ac-fs-open:not(.kw-fs-open) #searchChrome,
html body.catalog-portable.display-sides.display-middle.ac-fs-open:not(.kw-fs-open) #searchChrome,
html body.catalog-portable.portable-landscape.display-sides.display-middle.ac-fs-open:not(.kw-fs-open) #searchChrome,
html body.catalog-portable.hdr-bar-hidden.ac-fs-open:not(.kw-fs-open) #searchChrome,
html body.catalog-portable.ac-fs-open:not(.kw-fs-open) #acShell,
html body.catalog-portable.ac-fs-open:not(.kw-fs-open) #acShell.ac-fs{
  grid-column:1/-1!important;grid-row:2!important;
  display:flex!important;flex-direction:column!important;
  width:100%!important;max-width:none!important;
  height:var(--portable-fs-fill-h,100%)!important;max-height:none!important;
  min-height:0!important;flex:1 1 0%!important;
  position:relative!important;inset:auto!important;transform:none!important
}
html body.catalog-portable.kw-fs-open:not(.ac-fs-open) #filterWrap,
html body.catalog-portable.display-sides.kw-fs-open:not(.ac-fs-open) #filterWrap,
html body.catalog-portable.display-sides.display-middle.kw-fs-open:not(.ac-fs-open) #filterWrap,
html body.catalog-portable.display-sides.display-middle.search-chrome-collapsed.kw-open.kw-fs-open:not(.kw-chrome-collapsed) #filterWrap,
html body.catalog-portable.portable-landscape.display-sides.display-middle.search-chrome-collapsed.kw-open.kw-fs-open:not(.kw-chrome-collapsed) #filterWrap,
html body.catalog-portable.portable-landscape.display-sides.kw-fs-open:not(.ac-fs-open) #filterWrap,
html body.catalog-portable.hdr-bar-hidden.kw-fs-open:not(.ac-fs-open) #filterWrap{
  grid-column:1/-1!important;grid-row:2!important;
  display:flex!important;flex-direction:column!important;
  position:relative!important;inset:auto!important;transform:none!important;
  width:100%!important;max-width:none!important;
  height:var(--portable-fs-fill-h,100%)!important;max-height:none!important;
  min-height:0!important;flex:1 1 0%!important;overflow:hidden!important
}
html body.catalog-portable.ac-fs-open:not(.kw-fs-open) #filterWrap,
html body.catalog-portable.ac-fs-open:not(.kw-fs-open) #catalogMain,
html body.catalog-portable.kw-fs-open:not(.ac-fs-open) #searchChrome,
html body.catalog-portable.kw-fs-open:not(.ac-fs-open) #catalogMain,
html body.catalog-portable.display-sides.display-middle.ac-fs-open:not(.kw-fs-open) #filterWrap,
html body.catalog-portable.display-sides.display-middle.ac-fs-open:not(.kw-fs-open) #catalogMain,
html body.catalog-portable.display-sides.display-middle.kw-fs-open:not(.ac-fs-open) #searchChrome,
html body.catalog-portable.display-sides.display-middle.kw-fs-open:not(.ac-fs-open) #catalogMain,
html body.catalog-portable.portable-landscape.display-sides.display-middle.search-chrome-collapsed.kw-open.kw-fs-open #catalogMain,
html body.catalog-portable.portable-landscape.display-sides.display-middle.ac-fs-open:not(.kw-fs-open) #catalogMain{
  display:none!important;visibility:hidden!important;pointer-events:none!important;
  width:0!important;min-width:0!important;max-width:0!important;height:0!important;overflow:hidden!important
}
html body.catalog-portable.display-sides.display-middle.ac-fs-open:not(.kw-fs-open) #searchChrome,
html body.catalog-portable.display-sides.display-middle.kw-fs-open:not(.ac-fs-open) #filterWrap{
  max-height:none!important;flex:1 1 0%!important
}
html body.catalog-portable.kw-fs-open #kwStripHide,
html body.catalog-portable.kw-fs-open #filterToggle,
html body.catalog-portable .kw-strip-hide,
html body.catalog-portable .search-strip-hide{
  display:none!important;visibility:hidden!important;pointer-events:none!important
}
html body.catalog-portable.kw-fs-open #kwStripFs,
html body.catalog-portable.kw-fs-open .kw-fs-btn{
  display:inline-flex!important;visibility:visible!important;pointer-events:auto!important
}
html body.catalog-portable.kw-fs-open #kwFsBack,
html body.catalog-portable.kw-fs-open .kw-fs-back{
  display:none!important;visibility:hidden!important;pointer-events:none!important
}
"""

HIDE_RESHOW_OLD = """html body.catalog-portable.kw-fs-open #kwStripHide{
  display:inline-flex!important;visibility:visible!important
}
"""

HIDE_RESHOW_NEW = """html body.catalog-portable.kw-fs-open #kwStripHide{
  display:none!important;visibility:hidden!important;pointer-events:none!important
}
"""

KB_OLD = """function portableKeyboardOpen(){
  try{
    var vv=window.visualViewport;
    if(!vv)return false;
    var layout=Math.max(window.innerHeight||0,document.documentElement.clientHeight||0);
    return (layout-vv.height)>120;
  }catch(errKb){return false;}
}
"""

KB_NEW = """function portableKeyboardOpen(){
  try{
    var ae=document.activeElement;
    var typing=!!(ae&&(ae.id==='searchInput'||ae.tagName==='INPUT'||ae.tagName==='TEXTAREA'||ae.isContentEditable));
    if(!typing)return false;
    var vv=window.visualViewport;
    if(!vv)return false;
    var layout=Math.max(window.innerHeight||0,document.documentElement.clientHeight||0);
    return (layout-vv.height)>120;
  }catch(errKb){return false;}
}
"""

CLAMP_OLD = """function clampPortableVars(){
  if(document.body&&document.body.classList.contains('portable-kb-open'))return;
  var vw=window.innerWidth||400;
"""

CLAMP_NEW = """function clampPortableVars(){
  if(document.body&&(document.body.classList.contains('portable-kb-open')||document.body.classList.contains('ac-fs-open')||document.body.classList.contains('kw-fs-open')))return;
  var vw=window.innerWidth||400;
"""

HDR_OLD = """    if(typeof applyFsChromeSize==='function')applyFsChromeSize();
    else updateCatHeaderH();
    if(typeof applyIndexScrollFit==='function')applyIndexScrollFit();
    if(typeof placeMenusForDisplay==='function'){
      var mode=(document.body.className.match(/display-(\\S+)/)||[])[1];
      try{placeMenusForDisplay(mode||'sides');}catch(ePlace){}
    }
    if(typeof placeCatalogJumpStack==='function')placeCatalogJumpStack();
"""

HDR_NEW = """    if(typeof applyFsChromeSize==='function')applyFsChromeSize();
    else updateCatHeaderH();
    if(typeof applyIndexScrollFit==='function')applyIndexScrollFit();
    if(typeof placeMenusForDisplay==='function'){
      var mode=(document.body.className.match(/display-(\\S+)/)||[])[1];
      try{placeMenusForDisplay(mode||'sides');}catch(ePlace){}
    }
    if(typeof placeCatalogJumpStack==='function')placeCatalogJumpStack();
    if(typeof portableRelayoutChrome==='function')portableRelayoutChrome('hdr-bar');
"""

VV_OLD = """    window.visualViewport.addEventListener('resize',function(){
      if(typeof syncPortableLayoutChrome==='function')syncPortableLayoutChrome();
      if(document.body.classList.contains('portable-kb-open')){
        if(typeof placeAcShell==='function')placeAcShell();
        return;
      }
      applyAll();
    });
"""

VV_NEW = """    window.visualViewport.addEventListener('resize',function(){
      if(typeof syncPortableLayoutChrome==='function')syncPortableLayoutChrome();
      if(typeof portableRelayoutChrome==='function')portableRelayoutChrome('vv-resize');
      if(document.body.classList.contains('portable-kb-open')){
        if(typeof placeAcShell==='function')placeAcShell();
        return;
      }
      applyAll();
    });
"""

RESIZE_OLD = """    if(typeof syncPortableLayoutChrome==='function')syncPortableLayoutChrome();
    if(window.CATALOG_PORTABLE&&document.body.classList.contains('portable-kb-open')){
      if(typeof placeAcShell==='function')placeAcShell();
      return;
    }
    if(typeof applySidesCols==='function')applySidesCols();
"""

RESIZE_NEW = """    if(typeof syncPortableLayoutChrome==='function')syncPortableLayoutChrome();
    if(window.CATALOG_PORTABLE&&typeof portableRelayoutChrome==='function')portableRelayoutChrome('win-resize');
    if(window.CATALOG_PORTABLE&&document.body.classList.contains('portable-kb-open')){
      if(typeof placeAcShell==='function')placeAcShell();
      return;
    }
    if(typeof applySidesCols==='function')applySidesCols();
"""

ORIENT_MQ_OLD = """    function onOrientMq(){if(window.CATALOG_PORTABLE&&document.body.classList.contains('portable-kb-open'))return;if(typeof syncPortableLayoutChrome==='function')syncPortableLayoutChrome();if(typeof syncDisplayForOrientation==='function')syncDisplayForOrientation();}
"""

ORIENT_MQ_NEW = """    function onOrientMq(){if(window.CATALOG_PORTABLE&&document.body.classList.contains('portable-kb-open')){if(typeof portableRelayoutChrome==='function')portableRelayoutChrome('orient-mq-kb');return;}if(typeof syncPortableLayoutChrome==='function')syncPortableLayoutChrome();if(typeof syncDisplayForOrientation==='function')syncDisplayForOrientation();}
"""

COMBO_OLD = """    if(combo&&typeof portableRestoreMenuCombo==='function')portableRestoreMenuCombo(combo);
    if(combo&&combo.searchOn&&typeof expandSearchMenu==='function')expandSearchMenu();
    if(combo&&combo.kwOn&&typeof expandKwMenu==='function')expandKwMenu();
    if(combo&&!combo.searchOn&&typeof collapseSearchMenu==='function')collapseSearchMenu();
    if(combo&&!combo.kwOn&&typeof collapseKwMenu==='function')collapseKwMenu();
"""

COMBO_NEW = """    if(!hold){
    if(combo&&typeof portableRestoreMenuCombo==='function')portableRestoreMenuCombo(combo);
    if(combo&&combo.searchOn&&typeof expandSearchMenu==='function')expandSearchMenu();
    if(combo&&combo.kwOn&&typeof expandKwMenu==='function')expandKwMenu();
    if(combo&&!combo.searchOn&&typeof collapseSearchMenu==='function')collapseSearchMenu();
    if(combo&&!combo.kwOn&&typeof collapseKwMenu==='function')collapseKwMenu();
    }
"""

HOLD_OLD = """  if(hold&&typeof portableRestoreHeldFs==='function')portableRestoreHeldFs();
"""

HOLD_NEW = """  if(hold&&typeof portableRestoreHeldFs==='function')portableRestoreHeldFs();
  if(typeof portableRelayoutChrome==='function')portableRelayoutChrome('orient');
"""

MID_OLD = """function applyMiddleLayout(){
  if(!displayIsMiddle())return;
  if(window.CATALOG_PORTABLE)document.body.classList.remove('sides-portrait-flip');
"""

MID_NEW = """function applyMiddleLayout(){
  if(!displayIsMiddle())return;
  if(window.CATALOG_PORTABLE&&(document.body.classList.contains('ac-fs-open')||document.body.classList.contains('kw-fs-open')))return;
  if(window.CATALOG_PORTABLE)document.body.classList.remove('sides-portrait-flip');
"""

FS_API_OLD = """  }
}
function portableBindScrollPorts(){
"""

FS_API_NEW = """  }
  if(typeof portableRelayoutChrome==='function')portableRelayoutChrome('browser-fs');
}
function portableBindScrollPorts(){
"""

FS_CHG_OLD = """document.addEventListener('fullscreenchange',function(){
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

FS_CHG_NEW = """document.addEventListener('fullscreenchange',function(){
  if(!window.CATALOG_PORTABLE)return;
  var inFs=!!(document.fullscreenElement||document.webkitFullscreenElement);
  if(!inFs&&portableWantBrowserFs())portableApplyFsClass(true);
  else if(inFs)portableApplyFsClass(false);
  if(typeof portableRelayoutChrome==='function')portableRelayoutChrome('fullscreenchange');
});
document.addEventListener('webkitfullscreenchange',function(){
  if(!window.CATALOG_PORTABLE)return;
  var inFs=!!(document.fullscreenElement||document.webkitFullscreenElement);
  if(!inFs&&portableWantBrowserFs())portableApplyFsClass(true);
  else if(inFs)portableApplyFsClass(false);
  if(typeof portableRelayoutChrome==='function')portableRelayoutChrome('webkitfullscreenchange');
});
"""

KW_MORE_OLD = """  if(typeof portableEnsureScrollMenus==='function')portableEnsureScrollMenus();
  // #region agent log
  fetch('http://127.0.0.1:7529/ingest/1cf46354-1d61-4c80-bd72-a340f1db1b51',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'c00e3e'},body:JSON.stringify({sessionId:'c00e3e',runId:'post-fix',hypothesisId:'KW',location:'portable:toggleKwStripMore',message:'kw cats open',data:{open:true,csInPop:!!(cs&&pop.contains(cs)),kbH:kb?kb.clientHeight:0},timestamp:Date.now()})}).catch(function(){});
"""

KW_MORE_NEW = """  if(typeof portableEnsureScrollMenus==='function')portableEnsureScrollMenus();
  if(typeof portableRelayoutChrome==='function')portableRelayoutChrome('kw-more');
  // #region agent log
  fetch('http://127.0.0.1:7529/ingest/1cf46354-1d61-4c80-bd72-a340f1db1b51',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'c00e3e'},body:JSON.stringify({sessionId:'c00e3e',runId:'post-fix',hypothesisId:'KW',location:'portable:toggleKwStripMore',message:'kw cats open',data:{open:true,csInPop:!!(cs&&pop.contains(cs)),kbH:kb?kb.clientHeight:0},timestamp:Date.now()})}).catch(function(){});
"""

LAYOUT_OLD = """function portableApplyMenuFsLayout(which){
  if(!window.CATALOG_PORTABLE||!document.body.classList.contains('display-sides')){
    // #region agent log
    if(typeof dbgPortableSkCover==='function')dbgPortableSkCover('fs-layout-skip','D',{which:which||'',skip:'no-sides'});
    // #endregion
    return;
  }
  if(document.body.classList.contains('dual-fs-open')){
    // #region agent log
    if(typeof dbgPortableSkCover==='function')dbgPortableSkCover('fs-layout-skip','D',{which:which||'',skip:'dual'});
    // #endregion
    return;
  }
  var hdrF=document.querySelector('.catalog-header');
  var topF=hdrF?Math.round(hdrF.getBoundingClientRect().bottom):56;
  var fillH=Math.max(160,(window.innerHeight||800)-topF);
  document.body.style.setProperty('grid-template-rows','auto minmax(0,1fr)','important');
  document.body.style.setProperty('grid-template-columns','minmax(0,1fr)','important');
  var fillEl=which==='keywords'?document.getElementById('filterWrap'):document.getElementById('searchChrome');
  var hideEl=which==='keywords'?document.getElementById('searchChrome'):document.getElementById('filterWrap');
  var main=document.getElementById('catalogMain');
  if(fillEl){
    fillEl.style.setProperty('display','flex','important');
    fillEl.style.setProperty('max-height','none','important');
    fillEl.style.setProperty('height',fillH+'px','important');
    fillEl.style.setProperty('grid-row','2','important');
    fillEl.style.setProperty('grid-column','1 / -1','important');
    fillEl.style.setProperty('align-self','stretch','important');
    fillEl.style.setProperty('width','100%','important');
    fillEl.style.setProperty('max-width','none','important');
  }
  if(hideEl)hideEl.style.setProperty('display','none','important');
  if(main)main.style.setProperty('display','none','important');
  var sh=document.getElementById('acShell');
  if(which==='search'&&sh){
    sh.classList.add('open','ac-fs');
    sh.style.setProperty('grid-column','1 / -1','important');
    sh.style.setProperty('width','100%','important');
    sh.style.setProperty('max-width','none','important');
  }
  // #region agent log
  if(typeof dbgPortableSkCover==='function')dbgPortableSkCover('fs-layout-'+which,'D',{which:which||''});
  // #endregion
}
"""

LAYOUT_NEW = r"""function portableUsableBox(){
  var vv=window.visualViewport;
  var hdr=document.querySelector('.catalog-header');
  var top=0;
  if(hdr){
    var hb=hdr.getBoundingClientRect();
    top=Math.max(0,Math.round(hb.bottom));
  }
  var vvTop=vv?Math.round(vv.offsetTop||0):0;
  var vvH=vv&&vv.height?vv.height:(window.innerHeight||800);
  var vvW=vv&&vv.width?vv.width:(window.innerWidth||400);
  var y=Math.max(top,vvTop);
  var h=Math.max(120,Math.round(vvTop+vvH-y));
  return {x:vv?Math.round(vv.offsetLeft||0):0,y:y,w:Math.round(vvW),h:h,top:top,vvH:Math.round(vvH),vvW:Math.round(vvW)};
}
function portableClearMenuFsInline(){
  if(!document.body)return;
  document.body.style.removeProperty('grid-template-rows');
  document.body.style.removeProperty('grid-template-columns');
  document.body.style.removeProperty('display');
  document.body.style.removeProperty('flex-direction');
  document.body.style.removeProperty('height');
  document.body.style.removeProperty('max-height');
  ['filterWrap','searchChrome','catalogMain','acShell'].forEach(function(id){
    var el=document.getElementById(id);
    if(!el)return;
    el.style.removeProperty('height');
    el.style.removeProperty('max-height');
    el.style.removeProperty('min-height');
    el.style.removeProperty('grid-row');
    el.style.removeProperty('grid-column');
    el.style.removeProperty('align-self');
    el.style.removeProperty('display');
    el.style.removeProperty('width');
    el.style.removeProperty('max-width');
    el.style.removeProperty('flex');
  });
}
function portableRelayoutChrome(reason,fromRaf){
  if(!window.CATALOG_PORTABLE||!document.body)return;
  if(window._portableRelayoutLock)return;
  window._portableRelayoutLock=true;
  try{
    if(typeof syncPortableLayoutChrome==='function')syncPortableLayoutChrome();
    if(typeof portableScreenOrient==='function'&&portableScreenOrient()==='landscape'){
      document.body.classList.remove('display-middle');
      try{if(typeof currentDisplay!=='undefined'&&currentDisplay==='middle')currentDisplay='sides';}catch(eLand){}
      if(!document.body.classList.contains('display-content')&&!document.body.classList.contains('display-fs')){
        document.body.classList.add('display-sides');
      }
    }
    var box=typeof portableUsableBox==='function'?portableUsableBox():{h:Math.max(160,(window.innerHeight||800)-56),top:56,vvH:window.innerHeight||800};
    document.documentElement.style.setProperty('--portable-fs-fill-h',box.h+'px');
    document.documentElement.style.setProperty('--portable-vv-h',box.vvH+'px');
    document.documentElement.style.setProperty('--cat-header-h',box.top+'px');
    var which=(typeof portableMenuFsOn==='function'&&portableMenuFsOn())||'';
    if(typeof applyFsChromeSize==='function')applyFsChromeSize();
    if(!document.body.classList.contains('display-content')){
      if(typeof applySidesCols==='function')applySidesCols();
      if(typeof placeMenusForDisplay==='function'){
        var mode=(which==='search'||which==='keywords')?'sides':(document.body.classList.contains('display-middle')?'middle':'sides');
        try{placeMenusForDisplay(mode);}catch(ePlaceR){}
      }
    }
    if(which==='search'||which==='keywords'){
      if(typeof portableApplyMenuFsLayout==='function')portableApplyMenuFsLayout(which);
    }else if(typeof portableClearMenuFsInline==='function'){
      portableClearMenuFsInline();
    }
    if(typeof portableEnsureScrollMenus==='function')portableEnsureScrollMenus();
    if(typeof placePortableHandles==='function')placePortableHandles();
    if(typeof placeAcShell==='function')placeAcShell();
    if(typeof syncHdrMenuBtns==='function')syncHdrMenuBtns();
    // #region agent log
    try{
      var scL=document.getElementById('searchChrome'),fwL=document.getElementById('filterWrap'),cmL=document.getElementById('catalogMain');
      function boxL(el){if(!el)return null;var r=el.getBoundingClientRect(),cs=getComputedStyle(el);return {d:cs.display,w:Math.round(r.width),h:Math.round(r.height),x:Math.round(r.x),y:Math.round(r.y)};}
      fetch('http://127.0.0.1:7529/ingest/1cf46354-1d61-4c80-bd72-a340f1db1b51',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'c00e3e'},body:JSON.stringify({sessionId:'c00e3e',runId:'fs-relayout',hypothesisId:'H-FS-RE',location:'portable:portableRelayoutChrome',message:String(reason||'relayout'),data:{reason:String(reason||''),raf:!!fromRaf,which:which,hdrHide:document.body.classList.contains('hdr-bar-hidden'),bfs:document.body.classList.contains('is-browser-fs')||document.documentElement.classList.contains('is-browser-fs'),kb:document.body.classList.contains('portable-kb-open'),middle:document.body.classList.contains('display-middle'),sides:document.body.classList.contains('display-sides'),box:box,search:boxL(scL),kw:boxL(fwL),main:boxL(cmL),vvH:window.visualViewport?Math.round(window.visualViewport.height):null,ih:window.innerHeight||0},timestamp:Date.now()})}).catch(function(){});
    }catch(eRel){}
    // #endregion
  }finally{
    window._portableRelayoutLock=false;
  }
  if(!fromRaf){
    requestAnimationFrame(function(){portableRelayoutChrome(String(reason||'')+'-raf',true);});
  }
}
window.portableUsableBox=portableUsableBox;
window.portableClearMenuFsInline=portableClearMenuFsInline;
window.portableRelayoutChrome=portableRelayoutChrome;
function portableApplyMenuFsLayout(which){
  if(!window.CATALOG_PORTABLE){
    // #region agent log
    if(typeof dbgPortableSkCover==='function')dbgPortableSkCover('fs-layout-skip','D',{which:which||'',skip:'no-portable'});
    // #endregion
    return;
  }
  if(document.body.classList.contains('display-content')){
    // #region agent log
    if(typeof dbgPortableSkCover==='function')dbgPortableSkCover('fs-layout-skip','D',{which:which||'',skip:'content'});
    // #endregion
    return;
  }
  if(document.body.classList.contains('dual-fs-open')){
    // #region agent log
    if(typeof dbgPortableSkCover==='function')dbgPortableSkCover('fs-layout-skip','D',{which:which||'',skip:'dual'});
    // #endregion
    return;
  }
  if(typeof portableScreenOrient==='function'&&portableScreenOrient()==='landscape'){
    document.body.classList.remove('display-middle');
    document.body.classList.add('display-sides');
    try{if(typeof currentDisplay!=='undefined'&&currentDisplay==='middle')currentDisplay='sides';}catch(eFsLand){}
  }
  var box=typeof portableUsableBox==='function'?portableUsableBox():null;
  var fillH=box?box.h:Math.max(160,(window.innerHeight||800)-56);
  if(box){
    document.documentElement.style.setProperty('--portable-fs-fill-h',fillH+'px');
    document.documentElement.style.setProperty('--portable-vv-h',box.vvH+'px');
    document.documentElement.style.setProperty('--cat-header-h',box.top+'px');
  }
  document.body.style.setProperty('display','grid','important');
  document.body.style.setProperty('flex-direction','unset','important');
  document.body.style.setProperty('grid-template-rows','auto minmax(0,1fr)','important');
  document.body.style.setProperty('grid-template-columns','minmax(0,1fr)','important');
  document.body.style.setProperty('height',(box?box.vvH:(window.innerHeight||800))+'px','important');
  var fillEl=which==='keywords'?document.getElementById('filterWrap'):document.getElementById('searchChrome');
  var hideEl=which==='keywords'?document.getElementById('searchChrome'):document.getElementById('filterWrap');
  var main=document.getElementById('catalogMain');
  if(fillEl&&fillEl.parentElement!==document.body){
    document.body.insertBefore(fillEl, main||null);
  }
  if(fillEl){
    fillEl.style.setProperty('display','flex','important');
    fillEl.style.setProperty('flex-direction','column','important');
    fillEl.style.setProperty('max-height','none','important');
    fillEl.style.setProperty('min-height','0','important');
    fillEl.style.setProperty('height',fillH+'px','important');
    fillEl.style.setProperty('flex','1 1 0%','important');
    fillEl.style.setProperty('grid-row','2','important');
    fillEl.style.setProperty('grid-column','1 / -1','important');
    fillEl.style.setProperty('align-self','stretch','important');
    fillEl.style.setProperty('width','100%','important');
    fillEl.style.setProperty('max-width','none','important');
  }
  if(hideEl)hideEl.style.setProperty('display','none','important');
  if(main)main.style.setProperty('display','none','important');
  var sh=document.getElementById('acShell');
  if(which==='search'&&sh){
    sh.classList.add('open','ac-fs');
    sh.style.setProperty('display','flex','important');
    sh.style.setProperty('flex-direction','column','important');
    sh.style.setProperty('grid-column','1 / -1','important');
    sh.style.setProperty('width','100%','important');
    sh.style.setProperty('max-width','none','important');
    sh.style.setProperty('min-height','0','important');
    sh.style.setProperty('flex','1 1 0%','important');
    sh.style.removeProperty('height');
    sh.style.removeProperty('max-height');
  }
  // #region agent log
  if(typeof dbgPortableSkCover==='function')dbgPortableSkCover('fs-layout-'+which,'D',{which:which||'',h:fillH});
  try{
    fetch('http://127.0.0.1:7529/ingest/1cf46354-1d61-4c80-bd72-a340f1db1b51',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'c00e3e'},body:JSON.stringify({sessionId:'c00e3e',runId:'fs-relayout',hypothesisId:'H-FS-LAY',location:'portable:portableApplyMenuFsLayout',message:'fs-fill',data:{which:which||'',fillH:fillH,box:box,hdrHide:document.body.classList.contains('hdr-bar-hidden'),middle:document.body.classList.contains('display-middle')},timestamp:Date.now()})}).catch(function(){});
  }catch(eLay){}
  // #endregion
}
"""

ENTER_OLD = """  if(typeof dbgFsFlipSnap==='function')dbgFsFlipSnap('menu-fs-in',which);
  if(typeof portableApplyMenuFsLayout==='function')portableApplyMenuFsLayout(which);

  // #endregion
}
"""

ENTER_NEW = """  if(typeof dbgFsFlipSnap==='function')dbgFsFlipSnap('menu-fs-in',which);
  if(typeof portableApplyMenuFsLayout==='function')portableApplyMenuFsLayout(which);
  if(typeof portableRelayoutChrome==='function')portableRelayoutChrome('menu-fs-in');

  // #endregion
}
"""

EXIT_OLD = """  if(typeof dbgPortableJumpGap==='function')dbgPortableJumpGap('menu-fs-exit');
  if(typeof dbgMobileUi==='function')dbgMobileUi('menu-fs-out',{hyp:'H-MFS'});
  // #endregion
}
window.portableEnterMenuFs=portableEnterMenuFs;
"""

EXIT_NEW = """  if(typeof dbgPortableJumpGap==='function')dbgPortableJumpGap('menu-fs-exit');
  if(typeof dbgMobileUi==='function')dbgMobileUi('menu-fs-out',{hyp:'H-MFS'});
  // #endregion
  if(typeof portableRelayoutChrome==='function')portableRelayoutChrome('menu-fs-out');
}
window.portableEnterMenuFs=portableEnterMenuFs;
"""


def patch(text: str) -> str:
    reps = [
        (HIDE_RESHOW_OLD, HIDE_RESHOW_NEW),
        (KB_OLD, KB_NEW),
        (CLAMP_OLD, CLAMP_NEW),
        (HDR_OLD, HDR_NEW),
        (VV_OLD, VV_NEW),
        (RESIZE_OLD, RESIZE_NEW),
        (ORIENT_MQ_OLD, ORIENT_MQ_NEW),
        (COMBO_OLD, COMBO_NEW),
        (HOLD_OLD, HOLD_NEW),
        (MID_OLD, MID_NEW),
        (FS_API_OLD, FS_API_NEW),
        (FS_CHG_OLD, FS_CHG_NEW),
        (KW_MORE_OLD, KW_MORE_NEW),
        (LAYOUT_OLD, LAYOUT_NEW),
        (ENTER_OLD, ENTER_NEW),
        (EXIT_OLD, EXIT_NEW),
    ]
    for old, new in reps:
        n = text.count(old)
        if n != 1:
            raise SystemExit(f"expected 1 occurrence of snippet, found {n}: {old[:90]!r}")
        text = text.replace(old, new, 1)
    if CSS_MARK not in text:
        raise SystemExit("missing </style></head>")
    if "fix-PORTABLE-FS-RELAYOUT" not in text:
        text = text.replace(CSS_MARK, CSS_ADD + CSS_MARK, 1)
    return text


def write_safe(path: Path, data: str) -> None:
    if not data.rstrip().endswith("</html>"):
        raise SystemExit(f"{path.name} rewrite missing </html>")
    fd, tmp = tempfile.mkstemp(prefix=path.stem + ".", suffix=".html", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise
    got = path.stat().st_size
    if got < 100000:
        raise SystemExit(f"{path.name} too small after write: {got}")
    check = path.read_text(encoding="utf-8")
    if not check.rstrip().endswith("</html>"):
        raise SystemExit(f"{path.name} after write missing </html>")


def main() -> None:
    for path in FILES:
        raw = path.read_text(encoding="utf-8")
        out = patch(raw)
        write_safe(path, out)
        print(f"patched {path.name} {len(raw)} -> {len(out)}")


if __name__ == "__main__":
    main()
