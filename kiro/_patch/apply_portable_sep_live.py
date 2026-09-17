#!/usr/bin/env python3
"""Portable Customize: one live hit-stripe path; hide dead handles; persist vars."""
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
CSS_ADD = r"""
/* fix-PORTABLE-SEP-LIVE: layout-edit hit-stripes only; vars actually move panes */
html body.catalog-portable{
  --portable-stripe:8px
}
html body.catalog-portable:not(.layout-edit) #searchSplit,
html body.catalog-portable:not(.layout-edit) #dualFsSep,
html body.catalog-portable:not(.layout-edit) #indexHeight,
html body.catalog-portable #searchHeight,
html body.catalog-portable #kwShadeHeight,
html body.catalog-portable #acWidth,
html body.catalog-portable #acHeight,
html body.catalog-portable .search-height,
html body.catalog-portable .kw-shade-height,
html body.catalog-portable .ac-width,
html body.catalog-portable .ac-height,
html body.catalog-portable.layout-edit #searchSplit:not(.port-stripe-v):not(.port-stripe-h),
html body.catalog-portable.layout-edit #dualFsSep:not(.port-stripe-v):not(.port-stripe-h){
  display:none!important;pointer-events:none!important;visibility:hidden!important;width:0!important;height:0!important
}
html body.catalog-portable.layout-edit #searchSplit.port-stripe-v,
html body.catalog-portable.layout-edit #dualFsSep.port-stripe-v,
html body.catalog-portable.display-sides.layout-edit #searchSplit.port-stripe-v,
html body.catalog-portable.display-sides.layout-edit #dualFsSep.port-stripe-v,
html body.catalog-portable.display-sides:not(.display-middle).layout-edit #searchSplit.port-stripe-v,
html body.catalog-portable.display-sides:not(.display-middle).kw-chrome-collapsed.layout-edit #searchSplit.port-stripe-v,
html body.catalog-portable.display-sides:not(.display-middle).search-chrome-collapsed.layout-edit #dualFsSep.port-stripe-v{
  display:block!important;visibility:visible!important;pointer-events:auto!important;
  position:fixed!important;z-index:160!important;
  width:8px!important;min-width:8px!important;max-width:8px!important;
  height:auto!important;min-height:0!important;max-height:none!important;
  cursor:col-resize!important;touch-action:none!important
}
html body.catalog-portable.layout-edit #searchSplit.port-stripe-h,
html body.catalog-portable.layout-edit #dualFsSep.port-stripe-h,
html body.catalog-portable.display-sides.layout-edit #searchSplit.port-stripe-h,
html body.catalog-portable.display-sides.display-middle.layout-edit #searchSplit.port-stripe-h,
html body.catalog-portable.display-sides:not(.display-middle).layout-edit #searchSplit.port-stripe-h,
html body.catalog-portable.display-sides.kw-chrome-collapsed.layout-edit #searchSplit.port-stripe-h,
html body.catalog-portable.display-sides.search-chrome-collapsed.layout-edit #dualFsSep.port-stripe-h{
  display:block!important;visibility:visible!important;pointer-events:auto!important;
  position:fixed!important;z-index:160!important;
  height:8px!important;min-height:8px!important;max-height:8px!important;
  width:var(--port-h-w,100%)!important;min-width:48px!important;max-width:none!important;
  cursor:row-resize!important;touch-action:none!important
}
html body.catalog-portable.layout-edit.ac-fs-open:not(.kw-fs-open) #searchSplit,
html body.catalog-portable.layout-edit.ac-fs-open:not(.kw-fs-open) #dualFsSep,
html body.catalog-portable.layout-edit.kw-fs-open:not(.ac-fs-open) #searchSplit,
html body.catalog-portable.layout-edit.kw-fs-open:not(.ac-fs-open) #dualFsSep,
html body.catalog-portable.display-sides.ac-fs-open:not(.kw-fs-open).layout-edit #searchSplit,
html body.catalog-portable.display-sides.kw-fs-open:not(.ac-fs-open).layout-edit #dualFsSep{
  display:none!important;pointer-events:none!important;visibility:hidden!important
}
html body.catalog-portable.layout-edit #catalogIndex:not(.is-embedded):not(.is-collapsed) #indexHeight,
html body.catalog-portable.display-sides.layout-edit #catalogIndex:not(.is-embedded):not(.is-collapsed) #indexHeight,
html body.catalog-portable.display-middle.layout-edit #catalogIndex:not(.is-embedded):not(.is-collapsed) #indexHeight{
  display:block!important;pointer-events:auto!important;cursor:row-resize;z-index:24
}
html body.catalog-portable.portable-landscape.display-sides:not(.search-chrome-collapsed):not(.kw-open):not(.ac-fs-open):not(.kw-fs-open),
html body.catalog-portable.portable-landscape.display-sides.display-middle:not(.search-chrome-collapsed):not(.kw-open):not(.ac-fs-open):not(.kw-fs-open),
html body.catalog-portable.display-sides:not(.display-middle):not(.search-chrome-collapsed):not(.kw-open):not(.ac-fs-open):not(.kw-fs-open){
  grid-template-columns:minmax(120px,var(--portable-lw,42%)) minmax(0,1fr)!important
}
html body.catalog-portable.portable-landscape.display-sides.sides-portrait-flip:not(.search-chrome-collapsed):not(.kw-open):not(.ac-fs-open):not(.kw-fs-open),
html body.catalog-portable.portable-landscape.display-sides.display-middle.sides-portrait-flip:not(.search-chrome-collapsed):not(.kw-open):not(.ac-fs-open):not(.kw-fs-open){
  grid-template-columns:minmax(0,1fr) minmax(120px,var(--portable-lw,42%))!important
}
html body.catalog-portable.portable-landscape.display-sides.search-chrome-collapsed.kw-open:not(.kw-chrome-collapsed):not(.ac-fs-open):not(.kw-fs-open),
html body.catalog-portable.portable-landscape.display-sides.display-middle.search-chrome-collapsed.kw-open:not(.kw-chrome-collapsed):not(.ac-fs-open):not(.kw-fs-open){
  grid-template-columns:minmax(0,1fr) minmax(120px,var(--portable-rw,42%))!important
}
html body.catalog-portable.portable-landscape.display-sides.sides-portrait-flip.search-chrome-collapsed.kw-open:not(.kw-chrome-collapsed):not(.ac-fs-open):not(.kw-fs-open),
html body.catalog-portable.portable-landscape.display-sides.display-middle.sides-portrait-flip.search-chrome-collapsed.kw-open:not(.kw-chrome-collapsed):not(.ac-fs-open):not(.kw-fs-open){
  grid-template-columns:minmax(120px,var(--portable-rw,42%)) minmax(0,1fr)!important
}
html body.catalog-portable.portable-sk-pair,
html body.catalog-portable.portable-landscape.portable-sk-pair,
html body.catalog-portable.portable-landscape.display-sides.kw-open:not(.kw-chrome-collapsed):not(.search-chrome-collapsed):not(.ac-fs-open):not(.kw-fs-open),
html body.catalog-portable.portable-landscape.display-sides.display-middle.kw-open:not(.kw-chrome-collapsed):not(.search-chrome-collapsed):not(.ac-fs-open):not(.kw-fs-open),
html body.catalog-portable.display-fs.dual-fs-open,
html body.catalog-portable.display-fs.ac-fs-open.kw-fs-open,
html body.catalog-portable.display-sides.dual-fs-open,
html body.catalog-portable.display-sides.ac-fs-open.kw-fs-open{
  grid-template-columns:minmax(120px,var(--portable-lw,50%)) minmax(120px,1fr)!important
}
html body.catalog-portable.display-sides.display-middle:not(.ac-fs-open):not(.kw-fs-open):not(.search-chrome-collapsed) #searchChrome,
html body.catalog-portable.display-sides.display-middle.search-chrome-collapsed.kw-open:not(.kw-chrome-collapsed):not(.kw-fs-open) #filterWrap{
  height:var(--portable-menu-h,min(44dvh,22rem))!important;
  max-height:min(62dvh,32rem)!important;flex:0 0 auto!important
}
html body.catalog-portable.mode-layout-pinned.layout-edit #searchSplit,
html body.catalog-portable.mode-layout-pinned.layout-edit #dualFsSep,
html body.catalog-portable.mode-layout-pinned.layout-edit #indexHeight,
html body.catalog-portable.sides-pinned.layout-edit #searchSplit,
html body.catalog-portable.sides-pinned.layout-edit #dualFsSep{
  cursor:default!important;pointer-events:none!important
}
"""

PLACE_START = "function clampPortableVars(){"
PLACE_END = "window.placePortableHandles=placePortableHandles;"

PLACE_NEW = r"""function portableVarKey(n){
  return 'catalog-portable-'+n+'-'+(window.CATALOG_NS||'catalog');
}
function readPortableStored(){
  var o={};
  try{
    ['lw','rw','menu-h'].forEach(function(n){
      var v=parseInt(localStorage.getItem(portableVarKey(n)),10);
      if(v>40)o[n]=v;
    });
  }catch(e){}
  return o;
}
function persistPortableVars(){
  if(!window.CATALOG_PORTABLE)return;
  var root=document.documentElement;
  function grab(p){return parseInt(getComputedStyle(root).getPropertyValue(p),10)||0;}
  try{
    var lw=grab('--portable-lw'),rw=grab('--portable-rw'),mh=grab('--portable-menu-h');
    if(lw>40)localStorage.setItem(portableVarKey('lw'),String(lw));
    if(rw>40)localStorage.setItem(portableVarKey('rw'),String(rw));
    if(mh>40)localStorage.setItem(portableVarKey('menu-h'),String(mh));
  }catch(e){}
  try{
    if(document.body.classList.contains('display-middle')&&typeof writeMiddleLayout==='function'){
      var ml=grab('--portable-lw')||grab('--middle-lw');
      var mm=grab('--portable-menu-h')||grab('--middle-menu-h');
      if(ml>40||mm>40)writeMiddleLayout(ml,mm);
    }
  }catch(e2){}
}
function applyPortableStoredVars(){
  if(!window.CATALOG_PORTABLE||window._portableDragLock)return;
  var st=readPortableStored();
  var root=document.documentElement;
  function has(p){return parseInt(getComputedStyle(root).getPropertyValue(p),10)>40;}
  if(st.lw&&!has('--portable-lw'))root.style.setProperty('--portable-lw',st.lw+'px');
  if(st.rw&&!has('--portable-rw'))root.style.setProperty('--portable-rw',st.rw+'px');
  if(st['menu-h']&&!has('--portable-menu-h'))root.style.setProperty('--portable-menu-h',st['menu-h']+'px');
}
function clampPortableVars(){
  if(window._portableDragLock)return;
  if(document.body&&document.body.classList.contains('portable-kb-open'))return;
  var vw=window.innerWidth||400;
  var vh=window.innerHeight||800;
  var capW=Math.round(vw*0.78);
  var minW=120;
  ['--portable-lw','--portable-rw'].forEach(function(p){
    var v=parseInt(getComputedStyle(document.documentElement).getPropertyValue(p),10);
    if(v&&v>capW)document.documentElement.style.setProperty(p,capW+'px');
    else if(v&&v<minW)document.documentElement.style.setProperty(p,minW+'px');
  });
  var capH=Math.round(vh*0.62);
  var mh=parseInt(getComputedStyle(document.documentElement).getPropertyValue('--portable-menu-h'),10);
  if(mh&&mh>capH)document.documentElement.style.setProperty('--portable-menu-h',capH+'px');
  if(!mh&&document.body.classList.contains('display-middle')){
    document.documentElement.style.setProperty('--portable-menu-h',Math.round(Math.min(vh*0.36,22*16))+'px');
  }
}
function placePortableHandles(){
  if(!window.CATALOG_PORTABLE)return;
  if(!window._portableDragLock){
    applyPortableStoredVars();
    clampPortableVars();
  }
  var split=document.getElementById('searchSplit');
  var sep=document.getElementById('dualFsSep');
  var ch=document.getElementById('searchChrome');
  var fw=document.getElementById('filterWrap');
  var box=typeof portableUsableBox==='function'?portableUsableBox():null;
  var top=box&&box.top!=null?box.top:(function(){
    var hdr=document.querySelector('.catalog-header');
    return hdr?Math.round(hdr.getBoundingClientRect().bottom):56;
  })();
  var m=typeof portableMenusOn==='function'?portableMenusOn():{searchOn:true,kwOn:false,both:false};
  var oneFs=typeof portableMenuFsOn==='function'?portableMenuFsOn():'';
  var dual=document.body.classList.contains('dual-fs-open')||(document.body.classList.contains('ac-fs-open')&&document.body.classList.contains('kw-fs-open'));
  var sides=document.body.classList.contains('display-sides');
  var middle=document.body.classList.contains('display-middle');
  var portrait=!!(window.matchMedia&&window.matchMedia('(orientation:portrait)').matches);
  var flip=document.body.classList.contains('sides-portrait-flip');
  var edit=document.body.classList.contains('layout-edit');
  function vis(el){
    if(!el)return false;
    var cs=getComputedStyle(el);
    if(cs.display==='none'||cs.visibility==='hidden')return false;
    var r=el.getBoundingClientRect();
    return r.width>8&&r.height>8;
  }
  function clearRole(el){
    if(!el)return;
    el.classList.remove('port-stripe-v','port-stripe-h','port-stripe-drag');
    el.removeAttribute('data-port-prop');
    el.removeAttribute('data-port-axis');
    el.removeAttribute('data-port-grow');
    el.style.setProperty('display','none','important');
    el.style.setProperty('pointer-events','none','important');
    el.style.setProperty('visibility','hidden','important');
  }
  function bar(el,vert,edge,prop,grow){
    if(!el||!edge)return false;
    el.classList.toggle('port-stripe-v',!!vert);
    el.classList.toggle('port-stripe-h',!vert);
    el.setAttribute('data-port-prop',prop||'--portable-lw');
    el.setAttribute('data-port-axis',vert?'v':'h');
    el.setAttribute('data-port-grow',grow||(vert?'right':'down'));
    var half=4;
    el.style.cssText='';
    el.style.setProperty('position','fixed','important');
    el.style.setProperty('margin','0','important');
    el.style.setProperty('transform','none','important');
    el.style.setProperty('pointer-events','auto','important');
    el.style.setProperty('z-index','160','important');
    el.style.setProperty('background','var(--bg-surface)','important');
    el.style.setProperty('display','block','important');
    el.style.setProperty('visibility','visible','important');
    el.style.setProperty('opacity','1','important');
    if(vert){
      el.style.setProperty('top',Math.max(0,top)+'px','important');
      el.style.setProperty('bottom','0','important');
      el.style.setProperty('left',Math.round(edge.x-half)+'px','important');
      el.style.setProperty('width','8px','important');
      el.style.setProperty('min-width','8px','important');
      el.style.setProperty('max-width','8px','important');
      el.style.setProperty('height','auto','important');
      el.style.setProperty('min-height','0','important');
      el.style.setProperty('max-height','none','important');
      el.style.setProperty('cursor','col-resize','important');
    }else{
      var hw=Math.max(48,Math.round(edge.w||0));
      document.documentElement.style.setProperty('--port-h-w',hw+'px');
      el.style.setProperty('left',Math.round(edge.x)+'px','important');
      el.style.setProperty('width',hw+'px','important');
      el.style.setProperty('min-width','48px','important');
      el.style.setProperty('max-width','none','important');
      el.style.setProperty('top',Math.round(edge.y-half)+'px','important');
      el.style.setProperty('height','8px','important');
      el.style.setProperty('min-height','8px','important');
      el.style.setProperty('max-height','8px','important');
      el.style.setProperty('bottom','auto','important');
      el.style.setProperty('cursor','row-resize','important');
    }
    el.setAttribute('aria-orientation',vert?'vertical':'horizontal');
    return true;
  }
  clearRole(split);clearRole(sep);
  var ix=document.getElementById('catalogIndex');
  var ixH=document.getElementById('indexHeight');
  var showIx=edit&&ix&&vis(ix)&&!ix.classList.contains('is-collapsed')&&!ix.classList.contains('is-embedded')&&(sides||middle)&&!oneFs;
  if(ixH){
    ixH.style.setProperty('display',showIx?'block':'none','important');
    ixH.style.setProperty('pointer-events',showIx?'auto':'none','important');
    if(!showIx)ixH.style.setProperty('visibility','hidden','important');
    else ixH.style.setProperty('visibility','visible','important');
  }
  if(!edit||(oneFs&&!dual)){
    if(typeof placeCatalogJumpStack==='function')placeCatalogJumpStack();
    return;
  }
  var placed=false;
  if(dual&&vis(ch)&&vis(fw)){
    var leftDual=flip?fw:ch;
    placed=bar(split,true,{x:leftDual.getBoundingClientRect().right},'--portable-lw','right');
  }else if(middle||(portrait&&sides&&!document.body.classList.contains('portable-landscape'))){
    if(m.searchOn&&vis(ch)){
      var rs=ch.getBoundingClientRect();
      placed=bar(split,false,{x:rs.left,w:rs.width,y:rs.bottom},'--portable-menu-h','down');
    }else if(m.kwOn&&vis(fw)){
      var rk=fw.getBoundingClientRect();
      placed=bar(sep,false,{x:rk.left,w:rk.width,y:rk.bottom},'--portable-menu-h','down');
    }
  }else if(sides){
    if(m.both&&vis(ch)&&vis(fw)){
      var lp=flip?fw:ch;
      placed=bar(split,true,{x:lp.getBoundingClientRect().right},'--portable-lw','right');
    }else if(m.searchOn&&vis(ch)){
      var rc=ch.getBoundingClientRect();
      placed=bar(split,true,{x:flip?rc.left:rc.right},'--portable-lw',flip?'left':'right');
    }else if(m.kwOn&&vis(fw)){
      var rf=fw.getBoundingClientRect();
      placed=bar(sep,true,{x:flip?rf.right:rf.left},'--portable-rw',flip?'right':'left');
    }
  }
  // #region agent log
  try{
    var splitR=split&&split.getBoundingClientRect();
    var sepR=sep&&sep.getBoundingClientRect();
    var mainEl=document.getElementById('catalogMain');
    fetch('http://127.0.0.1:7529/ingest/1cf46354-1d61-4c80-bd72-a340f1db1b51',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'c00e3e'},body:JSON.stringify({sessionId:'c00e3e',runId:'sep-live',hypothesisId:'S',location:'portable:placeHandles',message:'live seps',data:{placed:!!placed,searchOn:!!m.searchOn,kwOn:!!m.kwOn,sides:sides,middle:middle,dual:!!dual,oneFs:oneFs||'',portrait:portrait,flip:flip,edit:true,splitW:splitR?Math.round(splitR.width):0,splitH:splitR?Math.round(splitR.height):0,sepW:sepR?Math.round(sepR.width):0,sepH:sepR?Math.round(sepR.height):0,splitPe:split?getComputedStyle(split).pointerEvents:'',sepPe:sep?getComputedStyle(sep).pointerEvents:'',propS:split&&split.getAttribute('data-port-prop'),propK:sep&&sep.getAttribute('data-port-prop'),menuH:getComputedStyle(document.documentElement).getPropertyValue('--portable-menu-h').trim(),lw:getComputedStyle(document.documentElement).getPropertyValue('--portable-lw').trim(),rw:getComputedStyle(document.documentElement).getPropertyValue('--portable-rw').trim(),ix:!!showIx,gutter:mainEl?((mainEl.offsetWidth||0)-(mainEl.clientWidth||0)):null,hdrTop:top},timestamp:Date.now()})}).catch(function(){});
  }catch(eDbgS){}
  // #endregion
  if(typeof placeCatalogJumpStack==='function')placeCatalogJumpStack();
  // #region agent log
  if(typeof dbgMobileUi==='function')dbgMobileUi('portable-stripe',{hyp:'H-STRIPE'});
  if(typeof dbgPortableJumpGap==='function')dbgPortableJumpGap('portable-stripe');
  // #endregion
}
window.portableVarKey=portableVarKey;
window.readPortableStored=readPortableStored;
window.persistPortableVars=persistPortableVars;
window.applyPortableStoredVars=applyPortableStoredVars;
window.clampPortableVars=clampPortableVars;
window.placePortableHandles=placePortableHandles;
"""

DOWN_OLD = """    if(window.CATALOG_PORTABLE){
      var chP=document.getElementById('searchChrome');
      var fwP=document.getElementById('filterWrap');
      var mP=typeof portableMenusOn==='function'?portableMenusOn():{searchOn:true,kwOn:true,both:true};
      var flipP=document.body.classList.contains('sides-portrait-flip');
      var portP=!!(window.matchMedia&&window.matchMedia('(orientation:portrait)').matches);
      var midP=typeof displayIsMiddle==='function'?displayIsMiddle():document.body.classList.contains('display-middle');
      var tP=e.currentTarget||e.target;
      var horizP=!!(tP&&tP.classList&&tP.classList.contains('port-stripe-h'));
      var paneP=horizP?(which==='sep'&&mP.kwOn&&!mP.searchOn?fwP:chP):(which==='sep'&&mP.kwOn&&!mP.searchOn?fwP:(mP.searchOn?chP:fwP));
      if(!paneP)paneP=chP||fwP;
      if(!paneP)return;
      var rP=paneP.getBoundingClientRect();
      var propP=horizP?'--portable-menu-h':((which==='sep'&&mP.kwOn&&!mP.searchOn)?'--portable-rw':'--portable-lw');
      drag={portable:true,horiz:horizP,which:which,x:e.clientX,y:e.clientY,w:rP.width,h:rP.height,flip:flipP,prop:propP,id:e.pointerId};
      try{if(tP&&tP.setPointerCapture)tP.setPointerCapture(e.pointerId);}catch(errP){}
      // #region agent log
      if(typeof dbgMobileUi==='function')dbgMobileUi('stripe-down',{hyp:'H-DRAG'});
      // #endregion
      return;
    }"""

DOWN_NEW = """    if(window.CATALOG_PORTABLE){
      var chP=document.getElementById('searchChrome');
      var fwP=document.getElementById('filterWrap');
      var mP=typeof portableMenusOn==='function'?portableMenusOn():{searchOn:true,kwOn:true,both:true};
      var flipP=document.body.classList.contains('sides-portrait-flip');
      var tP=e.currentTarget||e.target;
      var axisP=(tP&&tP.getAttribute&&tP.getAttribute('data-port-axis'))||(tP&&tP.classList&&tP.classList.contains('port-stripe-h')?'h':'v');
      var propP=(tP&&tP.getAttribute&&tP.getAttribute('data-port-prop'))||(axisP==='h'?'--portable-menu-h':((which==='sep'&&mP.kwOn&&!mP.searchOn)?'--portable-rw':'--portable-lw'));
      var growP=(tP&&tP.getAttribute&&tP.getAttribute('data-port-grow'))||(axisP==='h'?'down':(flipP?'left':'right'));
      var paneP=axisP==='h'?(mP.kwOn&&!mP.searchOn?fwP:chP):(propP==='--portable-rw'?fwP:(mP.both&&flipP?fwP:(mP.searchOn?chP:fwP)));
      if(!paneP)paneP=chP||fwP;
      if(!paneP)return;
      var rP=paneP.getBoundingClientRect();
      window._portableDragLock=true;
      if(tP&&tP.classList)tP.classList.add('port-stripe-drag');
      drag={portable:true,horiz:axisP==='h',axis:axisP,grow:growP,which:which,x:e.clientX,y:e.clientY,w:rP.width,h:rP.height,flip:flipP,prop:propP,id:e.pointerId};
      try{if(tP&&tP.setPointerCapture)tP.setPointerCapture(e.pointerId);}catch(errP){}
      // #region agent log
      if(typeof dbgMobileUi==='function')dbgMobileUi('stripe-down',{hyp:'H-DRAG'});
      try{fetch('http://127.0.0.1:7529/ingest/1cf46354-1d61-4c80-bd72-a340f1db1b51',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'c00e3e'},body:JSON.stringify({sessionId:'c00e3e',runId:'sep-live',hypothesisId:'H-DRAG',location:'portable:stripeDown',message:'stripe down',data:{which:which,axis:axisP,prop:propP,grow:growP,w:Math.round(rP.width),h:Math.round(rP.height)},timestamp:Date.now()})}).catch(function(){});}catch(eDn){}
      // #endregion
      return;
    }"""

MOVE_OLD = """    if(drag.portable){
      var vwP=window.innerWidth||1200;
      var vhP=window.innerHeight||800;
      if(drag.horiz){
        var nh=Math.max(128,Math.min(Math.round(vhP*0.48),drag.h+(e.clientY-drag.y)));
        document.documentElement.style.setProperty('--portable-menu-h',nh+'px');
      }else{
        var dx=e.clientX-drag.x;
        var nl=drag.flip?drag.w-dx:drag.w+dx;
        nl=Math.max(168,Math.min(Math.round(vwP*0.55),nl));
        document.documentElement.style.setProperty(drag.prop,nl+'px');
      }
      if(typeof placePortableHandles==='function')placePortableHandles();
      return;
    }"""

MOVE_NEW = """    if(drag.portable){
      var vwP=window.innerWidth||1200;
      var vhP=window.innerHeight||800;
      if(drag.horiz||drag.axis==='h'){
        var nh=Math.max(96,Math.min(Math.round(vhP*0.62),drag.h+(e.clientY-drag.y)));
        document.documentElement.style.setProperty('--portable-menu-h',nh+'px');
      }else{
        var dx=e.clientX-drag.x;
        var nl=drag.grow==='left'?drag.w-dx:drag.w+dx;
        nl=Math.max(120,Math.min(Math.round(vwP*0.78),nl));
        document.documentElement.style.setProperty(drag.prop||'--portable-lw',nl+'px');
      }
      if(typeof placePortableHandles==='function')placePortableHandles();
      return;
    }"""

UP_OLD = """    if(drag.portable){
      // #region agent log
      if(typeof dbgMobileUi==='function')dbgMobileUi('stripe-up',{hyp:'H-DRAG'});
      // #endregion
      drag=null;
      if(typeof placePortableHandles==='function')placePortableHandles();
      return;
    }"""

UP_NEW = """    if(drag.portable){
      window._portableDragLock=false;
      document.querySelectorAll('.port-stripe-drag').forEach(function(el){el.classList.remove('port-stripe-drag');});
      try{if(typeof persistPortableVars==='function')persistPortableVars();}catch(ePv){}
      // #region agent log
      if(typeof dbgMobileUi==='function')dbgMobileUi('stripe-up',{hyp:'H-DRAG'});
      // #endregion
      drag=null;
      if(typeof placePortableHandles==='function')placePortableHandles();
      return;
    }"""

IDX_OLD = """    if(!document.body.classList.contains('display-sides'))return;
    if(!window.CATALOG_PORTABLE&&!document.body.classList.contains('layout-edit'))return;"""

IDX_NEW = """    if(!document.body.classList.contains('display-sides')&&!document.body.classList.contains('display-middle'))return;
    if(!document.body.classList.contains('layout-edit'))return;"""

PERSIST_OLD = """function persistAllLiveLayouts(){
  try{if(typeof persist==='function')persist();}catch(err){}"""

PERSIST_NEW = """function persistAllLiveLayouts(){
  try{if(typeof persistPortableVars==='function')persistPortableVars();}catch(err){}
  try{if(typeof persist==='function')persist();}catch(err){}"""


def replace_once(text: str, old: str, new: str, label: str) -> str:
    n = text.count(old)
    if n != 1:
        raise SystemExit(f"{label}: expected 1 occurrence, found {n}")
    return text.replace(old, new, 1)


def replace_span(text: str, start: str, end: str, new: str, label: str) -> str:
    i = text.find(start)
    if i < 0:
        raise SystemExit(f"{label}: start marker missing")
    j = text.find(end, i)
    if j < 0:
        raise SystemExit(f"{label}: end marker missing")
    return text[:i] + new + text[j + len(end) :]


def patch(text: str) -> str:
    text = replace_span(text, PLACE_START, PLACE_END, PLACE_NEW, "clamp+place")
    text = replace_once(text, DOWN_OLD, DOWN_NEW, "stripe-down")
    text = replace_once(text, MOVE_OLD, MOVE_NEW, "stripe-move")
    text = replace_once(text, UP_OLD, UP_NEW, "stripe-up")
    text = replace_once(text, IDX_OLD, IDX_NEW, "index-down")
    text = replace_once(text, PERSIST_OLD, PERSIST_NEW, "persist-live")
    if CSS_MARK not in text:
        raise SystemExit("missing </style></head>")
    if "fix-PORTABLE-SEP-LIVE" not in text:
        text = text.replace(CSS_MARK, CSS_ADD + CSS_MARK, 1)
    return text


def write_safe(path: Path, data: str, before_c00: int) -> None:
    if not data.rstrip().endswith("</html>"):
        raise SystemExit(f"{path.name} rewrite missing </html>")
    if data.count("sessionId:'c00e3e'") < before_c00:
        raise SystemExit(f"{path.name}: lost c00e3e logs")
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
    if "fix-PORTABLE-SEP-LIVE" not in check:
        raise SystemExit(f"{path.name} missing SEP-LIVE mark")
    if "function placePortableHandles(){" not in check:
        raise SystemExit(f"{path.name} missing placePortableHandles")
    if check.count("function placePortableHandles(){") != 1:
        raise SystemExit(f"{path.name} duplicate placePortableHandles")
    if "sharedEdge" in check[check.find("function placePortableHandles(){") : check.find("window.placePortableHandles=placePortableHandles;")]:
        raise SystemExit(f"{path.name} still uses sharedEdge")


def main() -> None:
    for path in FILES:
        raw = path.read_text(encoding="utf-8")
        before_c00 = raw.count("sessionId:'c00e3e'")
        out = patch(raw)
        write_safe(path, out, before_c00)
        print(
            f"patched {path.name} {len(raw)} -> {len(out)} "
            f"c00={before_c00}->{out.count(chr(39)+'c00e3e'+chr(39))} size={path.stat().st_size}"
        )


if __name__ == "__main__":
    main()
