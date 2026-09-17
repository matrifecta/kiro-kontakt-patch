#!/usr/bin/env python3
"""Portable mobile pack v1: titles, jumps, overlay clip, KW cats, Index fill,
KW FS chrome, Window Index vs extended cards."""
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
/* fix-PORTABLE-MOBPACK-v1 */
@media(orientation:portrait){
  body.catalog-portable .catalog-header h1#top{
    column-gap:max(6.6rem,32vw)!important
  }
  body.catalog-portable .catalog-header h1#top .hdr-title-lead,
  body.catalog-portable .catalog-header h1#top .hdr-title-tail{
    justify-self:center!important;text-align:center!important;
    padding-left:max(0px,env(safe-area-inset-left,0px))!important;
    padding-right:max(0px,env(safe-area-inset-right,0px))!important
  }
}
html body.catalog-portable:not(.kw-cats-open) #catSwitch{display:none!important}
html body.catalog-portable.kw-cats-open #catSwitch{
  display:flex!important;flex-wrap:wrap!important;order:-1!important;
  width:100%!important;max-width:100%!important;align-content:flex-start;
  margin:.2rem 0 .35rem!important;gap:.28rem;background:transparent!important;
  box-shadow:none!important
}
html body.catalog-portable #catSwitch .cat-btn{
  background:transparent!important;border:1px solid var(--border)!important;
  color:var(--text-muted)!important;border-radius:4px;min-height:2.25rem
}
html body.catalog-portable #catSwitch .cat-btn.active,
html body.catalog-portable #catSwitch .cat-btn[aria-pressed="true"]{
  background:var(--accent-instrument-bg)!important;
  color:var(--accent-instrument)!important;
  border-color:var(--accent-instrument)!important;font-weight:600
}
html body.catalog-portable.kw-cats-open #kwStripMorePop,
html body.catalog-portable.kw-cats-open #kwStripMorePop:not([hidden]){
  display:none!important;visibility:hidden!important;pointer-events:none!important
}
html body.catalog-portable .kw-fs-back,
html body.catalog-portable #kwFsBack,
html body.catalog-portable.kw-fs-open .kw-fs-back,
html body.catalog-portable.kw-fs-open #kwFsBack,
html body.catalog-portable.display-sides.kw-fs-open .kw-fs-back,
html body.catalog-portable.display-fs.kw-fs-open .kw-fs-back{
  display:none!important;visibility:hidden!important;width:0!important;
  min-width:0!important;padding:0!important;margin:0!important;
  pointer-events:none!important;overflow:hidden!important
}
html body.catalog-portable #kwStripFs,
html body.catalog-portable #filterTop > #kwStripFs,
html body.catalog-portable.kw-fs-open #kwStripFs,
html body.catalog-portable.kw-fs-open #filterTop > #kwStripFs{
  display:inline-flex!important;visibility:visible!important;opacity:1!important;
  order:99!important;margin-left:auto!important;flex:0 0 auto!important;
  pointer-events:auto!important
}
html body.catalog-portable:not(.kw-chrome-collapsed) #kwStripHide,
html body.catalog-portable:not(.kw-chrome-collapsed) .kw-strip-hide,
html body.catalog-portable.kw-fs-open #kwStripHide{
  display:inline-flex!important;visibility:visible!important;opacity:1!important;
  pointer-events:auto!important
}
html body.catalog-portable.index-fill-doc.index-window-open #catalogIndex:not(.is-embedded):not(.is-collapsed),
html body.catalog-portable.index-window-open #catalogMain>#catalogIndex:not(.is-embedded):not(.is-collapsed){
  max-height:none!important;height:auto!important;min-height:0!important;
  overflow:hidden!important
}
html body.catalog-portable.index-fill-doc.index-window-open #catalogIndex:not(.is-embedded):not(.is-collapsed){
  flex:1 1 0%!important;overflow:hidden!important
}
html body.catalog-portable.index-fill-doc #catalogIndexList,
html body.catalog-portable.index-fill-doc #catalogIndex:not(.is-embedded):not(.is-collapsed) .index{
  overflow-x:hidden!important;overflow-y:auto!important;min-height:0!important;flex:1 1 auto!important
}
html body.catalog-portable.portable-clip-jump #catalogJumpStack,
html body.catalog-portable.portable-clip-edge #catalogEdgeStack,
html body.catalog-portable.portable-clip-stripe #catalogMainHoverStripe,
html body.catalog-portable.portable-clip-stripe #catalogMainHoverStripe.hover-scroll-fixed{
  visibility:hidden!important;pointer-events:none!important;display:none!important
}
html body.catalog-portable.portable-clip-scrollbar #catalogMain,
html body.catalog-portable.portable-clip-scrollbar #catalogMain>.catalog-body,
html body.catalog-portable.portable-clip-scrollbar .catalog-body{
  scrollbar-width:none!important;-ms-overflow-style:none!important
}
html body.catalog-portable.portable-clip-scrollbar #catalogMain::-webkit-scrollbar,
html body.catalog-portable.portable-clip-scrollbar .catalog-body::-webkit-scrollbar{
  display:none!important;width:0!important
}
@media(orientation:portrait){
  body.catalog-portable.display-sides:not(.search-chrome-collapsed) #catalogMainHoverStripe.hover-scroll-fixed,
  body.catalog-portable.display-sides.kw-open:not(.kw-chrome-collapsed) #catalogMainHoverStripe.hover-scroll-fixed,
  body.catalog-portable.display-middle:not(.search-chrome-collapsed) #catalogMainHoverStripe.hover-scroll-fixed,
  body.catalog-portable.display-middle.kw-open:not(.kw-chrome-collapsed) #catalogMainHoverStripe.hover-scroll-fixed,
  body.catalog-portable.display-sides.portrait-sides-flip:not(.search-chrome-collapsed) #catalogMainHoverStripe.hover-scroll-fixed,
  body.catalog-portable.display-sides.portrait-sides-flip.kw-open:not(.kw-chrome-collapsed) #catalogMainHoverStripe.hover-scroll-fixed{
    display:none!important;pointer-events:none!important;visibility:hidden!important
  }
}
html body.catalog-portable:is(.hl-open,.gallery-open,.img-focus-open,.desc-reader-open,.path-reader-open,.desc-focus-open,.path-focus-open,.chosen-preview-open,.card-embed-open):not(.catalog-help-open):not(.catalog-help-fs) #catalogIndex:not(.is-embedded),
html body.catalog-portable:is(.hl-open,.gallery-open,.img-focus-open,.desc-reader-open,.path-reader-open,.desc-focus-open,.path-focus-open,.chosen-preview-open,.card-embed-open):not(.catalog-help-open):not(.catalog-help-fs) #catalogJumpStack{
  visibility:hidden!important;pointer-events:none!important
}
html body.catalog-portable:is(.chosen-preview-open,.card-embed-open,.hl-open,.gallery-open) #catalogMain>.catalog-body{
  padding-top:0!important
}
html body.catalog-portable:is(.chosen-preview-open,.card-embed-open) .entry.selected:not(.highlight){
  position:fixed!important;left:50%!important;top:50%!important;right:auto!important;bottom:auto!important;
  transform:translate(-50%,-50%)!important;-webkit-transform:translate(-50%,-50%)!important
}
"""

HELPERS = r"""function portableFrontCardOpen(){
  var b=document.body;
  if(!b)return false;
  return b.classList.contains('chosen-preview-open')||b.classList.contains('card-embed-open')||b.classList.contains('hl-open')||b.classList.contains('gallery-open')||b.classList.contains('img-focus-open')||b.classList.contains('desc-reader-open')||b.classList.contains('path-reader-open')||b.classList.contains('desc-focus-open')||b.classList.contains('path-focus-open');
}
window.portableFrontCardOpen=portableFrontCardOpen;
function portableMenuVisibleRect(el){
  if(!el)return null;
  var cs=getComputedStyle(el);
  if(cs.display==='none'||cs.visibility==='hidden'||parseFloat(cs.opacity||'1')<0.05)return null;
  var r=el.getBoundingClientRect();
  if(!r||r.width<12||r.height<12)return null;
  return r;
}
function portableRectsOverlap(a,b,pad){
  pad=pad||2;
  return !(a.right<b.left+pad||a.left>b.right-pad||a.bottom<b.top+pad||a.top>b.bottom-pad);
}
function portableClipContentChrome(){
  if(!window.CATALOG_PORTABLE)return;
  var b=document.body;
  var preview=typeof portableFrontCardOpen==='function'&&portableFrontCardOpen();
  var menus=[];
  var scEl=document.getElementById('searchChrome');
  var fw=document.getElementById('filterWrap');
  var sr=portableMenuVisibleRect(scEl);
  var fr=portableMenuVisibleRect(fw);
  if(sr&&!b.classList.contains('search-chrome-collapsed'))menus.push({id:'searchChrome',r:sr});
  if(fr&&b.classList.contains('kw-open')&&!b.classList.contains('kw-chrome-collapsed'))menus.push({id:'filterWrap',r:fr});
  function hit(el){
    if(!el||preview)return !!preview;
    var cs=getComputedStyle(el);
    if(cs.display==='none')return false;
    var r=el.getBoundingClientRect();
    if(!r||r.width<2||r.height<2)return false;
    for(var i=0;i<menus.length;i++){
      if(portableRectsOverlap(r,menus[i].r))return true;
    }
    return false;
  }
  var jump=document.getElementById('catalogJumpStack');
  var edge=document.getElementById('catalogEdgeStack');
  var stripe=document.getElementById('catalogMainHoverStripe');
  var hideJ=hit(jump);
  var hideE=hit(edge);
  var hideS=hit(stripe);
  b.classList.toggle('portable-clip-jump',hideJ);
  b.classList.toggle('portable-clip-edge',hideE);
  b.classList.toggle('portable-clip-stripe',hideS);
  var hideSb=hideS;
  var sc=(typeof catalogContentScroller==='function'&&catalogContentScroller())||document.getElementById('catalogMain');
  if(sc){
    var cr=sc.getBoundingClientRect();
    var rightEdge={left:cr.right-16,right:cr.right+6,top:cr.top,bottom:cr.bottom,width:22,height:cr.height};
    for(var j=0;j<menus.length;j++){
      if(portableRectsOverlap(rightEdge,menus[j].r,0)){hideSb=true;break;}
    }
  }
  b.classList.toggle('portable-clip-scrollbar',hideSb);
  if(stripe&&hideS){stripe.hidden=true;stripe.style.setProperty('display','none','important');stripe.style.setProperty('pointer-events','none','important');}
  // #region agent log
  try{
    if(!window._dbgClip||Date.now()-window._dbgClip>800){
      window._dbgClip=Date.now();
      fetch('http://127.0.0.1:7529/ingest/1cf46354-1d61-4c80-bd72-a340f1db1b51',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'c00e3e'},body:JSON.stringify({sessionId:'c00e3e',runId:'mobpack',hypothesisId:'H3',location:'portable:portableClipContentChrome',message:'clip chrome',data:{preview:preview,hideJ:hideJ,hideE:hideE,hideS:hideS,hideSb:hideSb,menus:menus.map(function(m){return m.id;}),orient:innerWidth>=innerHeight?'land':'port',vw:innerWidth,vh:innerHeight,sides:b.classList.contains('display-sides'),middle:b.classList.contains('display-middle')},timestamp:Date.now()})}).catch(function(){});
    }
  }catch(eClip){}
  // #endregion
}
window.portableClipContentChrome=portableClipContentChrome;
(function(){
  if(window._mobpackFrontObs)return;
  window._mobpackFrontObs=1;
  function tick(){
    if(typeof applyIndexFillDocStyles==='function')applyIndexFillDocStyles();
    if(typeof syncPortableIndexContentGap==='function')syncPortableIndexContentGap();
    if(typeof portableClipContentChrome==='function')portableClipContentChrome();
  }
  function boot(){
    if(!document.body||window._mobpackFrontObs===2)return;
    window._mobpackFrontObs=2;
    new MutationObserver(tick).observe(document.body,{attributes:true,attributeFilter:['class']});
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot);
  else boot();
})();
"""

INDEX_FILL_OLD = """function indexWindowFillsToDoc(){
  if(!window.CATALOG_PORTABLE)return false;
  var b=document.body;
  if(!b.classList.contains('display-sides')||b.classList.contains('display-middle'))return false;
  if(b.classList.contains('ac-fs-open')||b.classList.contains('kw-fs-open')||b.classList.contains('dual-fs-open'))return false;
  var searchOn=!b.classList.contains('search-chrome-collapsed');
  var kwOn=b.classList.contains('kw-open')&&!b.classList.contains('kw-chrome-collapsed');
  return (searchOn&&!kwOn)||(!searchOn&&kwOn);
}"""

INDEX_FILL_NEW = HELPERS + """function indexWindowFillsToDoc(){
  if(!window.CATALOG_PORTABLE)return false;
  var b=document.body;
  if(b.classList.contains('ac-fs-open')||b.classList.contains('kw-fs-open')||b.classList.contains('dual-fs-open')||b.classList.contains('display-fs'))return false;
  if(typeof portableFrontCardOpen==='function'&&portableFrontCardOpen())return false;
  var ix=document.getElementById('catalogIndex');
  if(!ix||ix.classList.contains('is-embedded')||ix.classList.contains('is-collapsed'))return false;
  if(!b.classList.contains('index-window-open'))return false;
  return true;
}"""

SCROLLER_OLD = """function catalogContentScroller(){
  var cm=document.getElementById('catalogMain');
  var cb=cm&&(cm.querySelector(':scope > .catalog-body')||cm.querySelector('.catalog-body'));
  if(cb)return cb;
  return cm;
}"""

SCROLLER_NEW = """function catalogContentScroller(){
  var cm=document.getElementById('catalogMain');
  var cb=cm&&(cm.querySelector(':scope > .catalog-body')||cm.querySelector('.catalog-body'));
  function ov(el){return el?((el.scrollHeight||0)-(el.clientHeight||0)): -1;}
  if(ov(cb)>8)return cb;
  if(ov(cm)>8)return cm;
  if(cb)return cb;
  return cm;
}"""

KW_MORE_OLD = """function toggleKwStripMore(){
  var pop=document.getElementById('kwStripMorePop');var btn=document.getElementById('kwStripMore');
  var top=document.getElementById('filterTop');
  var cs=document.getElementById('catSwitch');
  var fp=document.getElementById('filterPanel');
  var kb=document.getElementById('kwbar');
  if(!pop||!btn)return;
  var open=pop.hasAttribute('hidden');
  var hdr=document.getElementById('hdrMorePop');
  if(hdr){hdr.setAttribute('hidden','');var hb=document.getElementById('hdrMoreBtn');if(hb)hb.setAttribute('aria-expanded','false');}
  if(!open){
    pop.setAttribute('hidden','');
    btn.setAttribute('aria-expanded','false');
    document.body.classList.remove('kw-cats-open');
    if(cs&&fp){if(kb)fp.insertBefore(cs,kb);else fp.appendChild(cs);}
    if(typeof portableEnsureScrollMenus==='function')portableEnsureScrollMenus();
    // #region agent log
    fetch('http://127.0.0.1:7529/ingest/1cf46354-1d61-4c80-bd72-a340f1db1b51',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'c00e3e'},body:JSON.stringify({sessionId:'c00e3e',runId:'post-fix',hypothesisId:'KW',location:'portable:toggleKwStripMore',message:'kw cats close',data:{open:false,kbH:kb?kb.clientHeight:0},timestamp:Date.now()})}).catch(function(){});
    // #endregion
    return;
  }
  if(top&&pop.parentElement!==top)top.appendChild(pop);
  pop.innerHTML='';
  if(cs)pop.appendChild(cs);
  pop.removeAttribute('hidden');
  btn.setAttribute('aria-expanded','true');
  document.body.classList.add('kw-cats-open');
  btn.style.setProperty('display','inline-flex','important');
  if(typeof portableEnsureScrollMenus==='function')portableEnsureScrollMenus();
  // #region agent log
  fetch('http://127.0.0.1:7529/ingest/1cf46354-1d61-4c80-bd72-a340f1db1b51',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'c00e3e'},body:JSON.stringify({sessionId:'c00e3e',runId:'post-fix',hypothesisId:'KW',location:'portable:toggleKwStripMore',message:'kw cats open',data:{open:true,csInPop:!!(cs&&pop.contains(cs)),kbH:kb?kb.clientHeight:0},timestamp:Date.now()})}).catch(function(){});
  // #endregion
  if(typeof dbgMobileUi==='function')dbgMobileUi('kw-more',{hyp:'H-M3'});
}"""

KW_MORE_NEW = """function toggleKwStripMore(){
  var pop=document.getElementById('kwStripMorePop');var btn=document.getElementById('kwStripMore');
  var cs=document.getElementById('catSwitch');
  var fp=document.getElementById('filterPanel')||document.querySelector('#filterWrap .filter-panel');
  var kb=document.getElementById('kwbar');
  if(!btn)return;
  var open=!document.body.classList.contains('kw-cats-open');
  var hdr=document.getElementById('hdrMorePop');
  if(hdr){hdr.setAttribute('hidden','');var hb=document.getElementById('hdrMoreBtn');if(hb)hb.setAttribute('aria-expanded','false');}
  if(pop){pop.setAttribute('hidden','');pop.innerHTML='';}
  if(cs&&fp){
    if(kb&&kb.parentNode===fp)fp.insertBefore(cs,kb);
    else if(cs.parentNode!==fp)fp.insertBefore(cs,fp.firstChild||null);
  }
  document.body.classList.toggle('kw-cats-open',open);
  btn.setAttribute('aria-expanded',open?'true':'false');
  if(typeof portableEnsureScrollMenus==='function')portableEnsureScrollMenus();
  // #region agent log
  fetch('http://127.0.0.1:7529/ingest/1cf46354-1d61-4c80-bd72-a340f1db1b51',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'c00e3e'},body:JSON.stringify({sessionId:'c00e3e',runId:'mobpack',hypothesisId:'H4',location:'portable:toggleKwStripMore',message:'kw cats toggle',data:{open:open,parent:cs&&cs.parentElement&&(cs.parentElement.id||cs.parentElement.className)||'',inPop:!!(pop&&cs&&pop.contains(cs)),kbH:kb?kb.clientHeight:0},timestamp:Date.now()})}).catch(function(){});
  // #endregion
  if(typeof dbgMobileUi==='function')dbgMobileUi('kw-more',{hyp:'H-M3'});
}"""

GAP_OLD = """function syncPortableIndexContentGap(){
  if(!window.CATALOG_PORTABLE)return;
  var main=document.getElementById('catalogMain');
  var ix=document.getElementById('catalogIndex');
  var cb=main&&(main.querySelector(':scope > .catalog-body')||main.querySelector('.catalog-body'));
  if(!cb)return;
  var abs=!!(ix&&!ix.classList.contains('is-embedded')&&getComputedStyle(ix).position==='absolute'&&getComputedStyle(ix).display!=='none'&&getComputedStyle(ix).visibility!=='hidden');
  var h=abs?Math.ceil(ix.getBoundingClientRect().height):0;
  cb.style.setProperty('padding-top',(h?(h+22):0)+'px','important');
}"""

GAP_NEW = """function syncPortableIndexContentGap(){
  if(!window.CATALOG_PORTABLE)return;
  var main=document.getElementById('catalogMain');
  var ix=document.getElementById('catalogIndex');
  var cb=main&&(main.querySelector(':scope > .catalog-body')||main.querySelector('.catalog-body'));
  if(!cb)return;
  if(typeof portableFrontCardOpen==='function'&&portableFrontCardOpen()){
    cb.style.removeProperty('padding-top');
    return;
  }
  var abs=!!(ix&&!ix.classList.contains('is-embedded')&&getComputedStyle(ix).position==='absolute'&&getComputedStyle(ix).display!=='none'&&getComputedStyle(ix).visibility!=='hidden');
  var h=abs?Math.ceil(ix.getBoundingClientRect().height):0;
  cb.style.setProperty('padding-top',(h?(h+22):0)+'px','important');
}"""

JUMP_END_OLD = """  if(typeof placeCatalogEdgeStack==='function')placeCatalogEdgeStack();
  if(typeof dbgPortableJumpGap==='function')dbgPortableJumpGap('placeJump');
}"""

JUMP_END_NEW = """  if(typeof placeCatalogEdgeStack==='function')placeCatalogEdgeStack();
  if(typeof dbgPortableJumpGap==='function')dbgPortableJumpGap('placeJump');
  if(typeof portableClipContentChrome==='function')portableClipContentChrome();
}"""

BIND_OLD = """function bindCatalogTop(){
  function goTop(e,topEl){
    if(!document.body.classList.contains('display-sides'))return;
    if(e){e.preventDefault();e.stopPropagation();}
    var cm=document.getElementById('catalogMain');
    var ix=document.getElementById('catalogIndex');
    var ixColBefore=!!(ix&&ix.classList.contains('is-collapsed'));
    var searchBefore=document.body.classList.contains('search-chrome-collapsed');
    var kwBefore=document.body.classList.contains('kw-chrome-collapsed');
    var kwOpenBefore=document.body.classList.contains('kw-open');
    if(ix)ix.dataset.goingTop='1';
    var sc=(typeof catalogContentScroller==='function'&&catalogContentScroller())||cm;
    if(sc){try{sc.scrollTo({top:sc.scrollTop,behavior:'instant'});}catch(err){sc.scrollTop=sc.scrollTop;}try{sc.scrollTo({top:0,behavior:'smooth'});}catch(err){sc.scrollTop=0;}}
  }
  function goBot(e){
    if(!document.body.classList.contains('display-sides'))return;
    if(e){e.preventDefault();e.stopPropagation();}
    var cm=document.getElementById('catalogMain');
    var ix=document.getElementById('catalogIndex');
    var ixColBefore=!!(ix&&ix.classList.contains('is-collapsed'));
    var searchBefore=document.body.classList.contains('search-chrome-collapsed');
    var kwBefore=document.body.classList.contains('kw-chrome-collapsed');
    var sc=(typeof catalogContentScroller==='function'&&catalogContentScroller())||cm;
    if(sc){try{sc.scrollTo({top:sc.scrollTop,behavior:'instant'});}catch(err){sc.scrollTop=sc.scrollTop;}try{sc.scrollTo({top:sc.scrollHeight,behavior:'smooth'});}catch(err){sc.scrollTop=sc.scrollHeight;}}
  }"""

BIND_NEW = """function bindCatalogTop(){
  function jumpAllowed(){
    var b=document.body;
    return !!(window.CATALOG_PORTABLE||b.classList.contains('display-sides')||b.classList.contains('display-middle')||b.classList.contains('display-content'));
  }
  function jumpScroller(){
    var cm=document.getElementById('catalogMain');
    var cb=cm&&(cm.querySelector(':scope > .catalog-body')||cm.querySelector('.catalog-body'));
    var best=null,bestOv=-1,i,el,ov,cands=[cb,cm];
    for(i=0;i<cands.length;i++){
      el=cands[i];if(!el)continue;
      ov=(el.scrollHeight||0)-(el.clientHeight||0);
      if(ov>bestOv){bestOv=ov;best=el;}
    }
    return best||(typeof catalogContentScroller==='function'&&catalogContentScroller())||cm;
  }
  function goTop(e,topEl){
    if(!jumpAllowed())return;
    if(e){e.preventDefault();e.stopPropagation();}
    var cm=document.getElementById('catalogMain');
    var ix=document.getElementById('catalogIndex');
    var ixColBefore=!!(ix&&ix.classList.contains('is-collapsed'));
    var searchBefore=document.body.classList.contains('search-chrome-collapsed');
    var kwBefore=document.body.classList.contains('kw-chrome-collapsed');
    var kwOpenBefore=document.body.classList.contains('kw-open');
    if(ix)ix.dataset.goingTop='1';
    var sc=jumpScroller();
    var y0=sc?sc.scrollTop: -1;
    if(sc){try{sc.scrollTo({top:sc.scrollTop,behavior:'instant'});}catch(err){sc.scrollTop=sc.scrollTop;}try{sc.scrollTo({top:0,behavior:'smooth'});}catch(err){sc.scrollTop=0;}}
    // #region agent log
    fetch('http://127.0.0.1:7529/ingest/1cf46354-1d61-4c80-bd72-a340f1db1b51',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'c00e3e'},body:JSON.stringify({sessionId:'c00e3e',runId:'mobpack',hypothesisId:'H2',location:'portable:bindCatalogTop',message:'goTop',data:{id:sc&&(sc.id||sc.className)||'',y0:y0,y1:sc?sc.scrollTop:null,sh:sc?sc.scrollHeight:0,ch:sc?sc.clientHeight:0,portable:!!window.CATALOG_PORTABLE,sides:document.body.classList.contains('display-sides'),content:document.body.classList.contains('display-content')},timestamp:Date.now()})}).catch(function(){});
    // #endregion
  }
  function goBot(e){
    if(!jumpAllowed())return;
    if(e){e.preventDefault();e.stopPropagation();}
    var cm=document.getElementById('catalogMain');
    var ix=document.getElementById('catalogIndex');
    var ixColBefore=!!(ix&&ix.classList.contains('is-collapsed'));
    var searchBefore=document.body.classList.contains('search-chrome-collapsed');
    var kwBefore=document.body.classList.contains('kw-chrome-collapsed');
    var sc=jumpScroller();
    var y0=sc?sc.scrollTop: -1;
    var dest=sc?Math.max(0,(sc.scrollHeight||0)-(sc.clientHeight||0)):0;
    if(sc){try{sc.scrollTo({top:sc.scrollTop,behavior:'instant'});}catch(err){sc.scrollTop=sc.scrollTop;}try{sc.scrollTo({top:dest,behavior:'smooth'});}catch(err){sc.scrollTop=dest;}}
    // #region agent log
    fetch('http://127.0.0.1:7529/ingest/1cf46354-1d61-4c80-bd72-a340f1db1b51',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'c00e3e'},body:JSON.stringify({sessionId:'c00e3e',runId:'mobpack',hypothesisId:'H2',location:'portable:bindCatalogTop',message:'goBot',data:{id:sc&&(sc.id||sc.className)||'',y0:y0,dest:dest,sh:sc?sc.scrollHeight:0,ch:sc?sc.clientHeight:0,portable:!!window.CATALOG_PORTABLE,sides:document.body.classList.contains('display-sides'),content:document.body.classList.contains('display-content')},timestamp:Date.now()})}).catch(function(){});
    // #endregion
  }"""

STRIPE_OLD = """      }catch(eDbgB){}
      // #endregion
    }
    function schedule(){
      if(raf)cancelAnimationFrame(raf);
      raf=requestAnimationFrame(function(){raf=0;sync();});
    }
    function yToScroll(sc,st,clientY){"""

STRIPE_NEW = """      }catch(eDbgB){}
      // #endregion
      if(mark==='content'&&typeof portableClipContentChrome==='function')portableClipContentChrome();
    }
    function schedule(){
      if(raf)cancelAnimationFrame(raf);
      raf=requestAnimationFrame(function(){raf=0;sync();});
    }
    function yToScroll(sc,st,clientY){"""

EDGE_END_OLD = """  if(typeof catalogHelpSyncChrome==='function')catalogHelpSyncChrome();
}
function catalogHelpFillCopy(){"""

EDGE_END_NEW = """  if(typeof catalogHelpSyncChrome==='function')catalogHelpSyncChrome();
  if(typeof portableClipContentChrome==='function')portableClipContentChrome();
}
function catalogHelpFillCopy(){"""

FILL_APPLY_OLD = """  var fill=!!(document.body.classList.contains('index-window-open')&&indexWindowFillsToDoc()&&ix&&!ix.classList.contains('is-collapsed')&&!ix.classList.contains('is-embedded')&&!(note&&note.classList.contains('is-embedded')));
  document.body.classList.toggle('index-fill-doc',fill);"""

FILL_APPLY_NEW = """  var front=typeof portableFrontCardOpen==='function'&&portableFrontCardOpen();
  var fill=!front&&!!(document.body.classList.contains('index-window-open')&&indexWindowFillsToDoc()&&ix&&!ix.classList.contains('is-collapsed')&&!ix.classList.contains('is-embedded')&&!(note&&note.classList.contains('is-embedded')));
  document.body.classList.toggle('index-fill-doc',fill);"""


def once(text: str, old: str, new: str, label: str, name: str) -> str:
    if old not in text:
        if new in text or (label == "helpers" and "function portableFrontCardOpen()" in text):
            print(f"  skip {label} {name}")
            return text
        raise SystemExit(f"{name}: missing {label}: {old[:90]!r}")
    n = text.count(old)
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
        check = tmp_path.read_text(encoding="utf-8")
        if not check.rstrip().endswith("</html>"):
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
    if CSS_MARK not in text:
        raise SystemExit(f"{name}: css mark missing")
    if text.count(CSS_MARK) != 1:
        raise SystemExit(f"{name}: css mark count {text.count(CSS_MARK)}")
    if "fix-PORTABLE-MOBPACK-v1" not in text:
        text = text.replace(CSS_MARK, CSS_ADD + CSS_MARK, 1)
        print(f"  1x css-tail {name}")
    else:
        print(f"  skip css-tail {name}")
    if "function portableFrontCardOpen()" not in text:
        text = once(text, INDEX_FILL_OLD, INDEX_FILL_NEW, "index-fill", name)
    else:
        print(f"  skip index-fill {name}")
    text = once(text, SCROLLER_OLD, SCROLLER_NEW, "scroller", name)
    text = once(text, KW_MORE_OLD, KW_MORE_NEW, "kw-more", name)
    text = once(text, GAP_OLD, GAP_NEW, "ix-gap", name)
    text = once(text, JUMP_END_OLD, JUMP_END_NEW, "jump-end", name)
    text = once(text, BIND_OLD, BIND_NEW, "bind-top", name)
    text = once(text, STRIPE_OLD, STRIPE_NEW, "stripe-clip", name)
    text = once(text, EDGE_END_OLD, EDGE_END_NEW, "edge-end", name)
    text = once(text, FILL_APPLY_OLD, FILL_APPLY_NEW, "fill-apply", name)
    if "fix-PORTABLE-MOBPACK-v1" not in text:
        raise SystemExit(f"{name}: css missing after patch")
    if "function portableFrontCardOpen()" not in text:
        raise SystemExit(f"{name}: helpers missing")
    if "function jumpAllowed()" not in text:
        raise SystemExit(f"{name}: jumpAllowed missing")
    safe_write(path, text)


def main() -> None:
    for p in FILES:
        print("==", p.name)
        patch(p)


if __name__ == "__main__":
    main()
