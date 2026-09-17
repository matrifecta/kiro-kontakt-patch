#!/usr/bin/env python3
"""Desktop Sides portrait A/B: menus stacked left/right, ±30% clamp, flip pref."""
from pathlib import Path

ROOT = Path("/home/phnx/kiro-kontakt-patch")
FILES = [
    ROOT / "public/catalogs/DS-CATALOG.html",
    ROOT / "public/catalogs/KONTAKT-CATALOG.html",
    ROOT / "public/catalogs/DS-CATALOG-portable.html",
    ROOT / "public/catalogs/KONTAKT-CATALOG-portable.html",
    ROOT / "kiro/specs/kontakt-workspace-drive-dirty-fix/artifacts/build-ds-catalog-html.sh",
    ROOT / "kiro/specs/kontakt-workspace-drive-dirty-fix/artifacts/build-kontakt-catalog-html.sh",
]

OLD_CSS = """/* fix-PORTRAIT-SIDES: portrait desktop — menus top, catalog bottom, 2 separators */
@media(min-width:900px) and (orientation:portrait){
  body.display-sides{
    grid-template-columns:var(--portrait-lw,1fr) 8px var(--portrait-rw,1fr)!important;
    grid-template-rows:auto var(--portrait-menu-h,42dvh) 8px 1fr!important
  }
  body.display-sides .catalog-header{grid-column:1/-1;grid-row:1}
  body.display-sides #searchChrome{grid-column:1;grid-row:2;height:100%!important;max-height:none!important;min-height:0;border-right:0!important;overflow-y:auto!important}
  body.display-sides #dualFsSep,body.display-sides:not(.layout-edit) #dualFsSep,body.display-sides.layout-edit #dualFsSep{
    grid-column:2;grid-row:2;display:block!important;
    width:8px!important;height:100%!important;min-height:0;
    cursor:col-resize!important;position:relative!important;inset:auto!important;
    background:transparent;border-left:1px solid var(--border);border-right:1px solid var(--border);
    pointer-events:auto!important;touch-action:none;z-index:20
  }
  body.display-sides #filterWrap{grid-column:3;grid-row:2;height:100%!important;max-height:none!important;min-height:0;border-left:0!important;overflow-y:auto!important}
  body.display-sides #searchSplit,body.display-sides:not(.layout-edit) #searchSplit,body.display-sides.layout-edit #searchSplit{
    grid-column:1/-1;grid-row:3;display:block!important;
    height:8px!important;width:100%!important;min-width:0!important;max-width:none!important;
    cursor:ns-resize!important;transform:none!important;margin:0;padding:0;
    position:relative!important;z-index:20;
    background:transparent;border-top:1px solid var(--border);border-bottom:1px solid var(--border);
    pointer-events:auto!important;touch-action:none
  }
  body.display-sides #catalogMain{grid-column:1/-1;grid-row:4;min-height:0;overflow-y:auto!important;overflow-x:hidden;padding:0 0 2rem}
  body.display-sides #catalogIndex{position:static!important;height:auto!important;max-height:min(22dvh,13rem)!important;overflow-y:auto!important}
  body.display-sides #filterWrap.open .filter-panel{max-height:none!important;flex:1 1 auto;min-height:0;overflow-y:auto!important}
  body.display-sides a.top{bottom:1rem;right:1.25rem!important}
  /* Drag-handle pips for visual affordance */
  body.display-sides #dualFsSep::before,body.display-sides #searchSplit::before{
    content:'';display:block;
    background:var(--border,rgba(128,128,128,0.5));border-radius:2px;
    opacity:.6;transition:opacity .15s;position:absolute;top:50%;left:50%;transform:translate(-50%,-50%)
  }
  body.display-sides #dualFsSep::before{width:2px;height:24px;margin-top:-12px}
  body.display-sides #searchSplit::before{width:24px;height:2px;margin-left:-12px}
  body.display-sides #dualFsSep:hover::before,body.display-sides #searchSplit:hover::before{opacity:1}
}
"""

NEW_CSS = """/* fix-PORTRAIT-SIDES: desktop portrait A/B — stacked menus left or right, content the other side */
@media(min-width:900px) and (orientation:portrait){
  body.display-sides{
    grid-template-columns:var(--portrait-lw,38%) minmax(0,1fr)!important;
    grid-template-rows:auto minmax(0,var(--portrait-menu-h,1fr)) minmax(0,1fr)!important
  }
  body.display-sides.sides-portrait-flip{
    grid-template-columns:minmax(0,1fr) var(--portrait-lw,38%)!important
  }
  body.display-sides.search-chrome-collapsed:not(.kw-chrome-collapsed),
  body.display-sides.kw-chrome-collapsed:not(.search-chrome-collapsed){
    grid-template-rows:auto minmax(0,1fr)!important
  }
  body.display-sides.search-chrome-collapsed.kw-chrome-collapsed,
  body.display-sides.sides-portrait-flip.search-chrome-collapsed.kw-chrome-collapsed{
    grid-template-columns:minmax(0,1fr)!important;
    grid-template-rows:auto minmax(0,1fr)!important
  }
  body.display-sides .catalog-header{grid-column:1/-1;grid-row:1}
  body.display-sides #searchChrome{
    grid-column:1!important;grid-row:2!important;
    height:auto!important;max-height:none!important;min-height:0;
    border-right:1px solid var(--border)!important;border-left:0!important;
    border-bottom:1px solid var(--border)!important;overflow:hidden!important
  }
  body.display-sides #filterWrap{
    grid-column:1!important;grid-row:3!important;
    height:auto!important;max-height:none!important;min-height:0;
    border-left:0!important;border-right:1px solid var(--border)!important;
    overflow:hidden!important
  }
  body.display-sides #catalogMain{
    grid-column:2!important;grid-row:2/-1!important;
    min-height:0;overflow-y:auto!important;overflow-x:hidden;padding:0 0 2rem
  }
  body.display-sides.sides-portrait-flip #searchChrome{
    grid-column:2!important;
    border-right:0!important;border-left:1px solid var(--border)!important
  }
  body.display-sides.sides-portrait-flip #filterWrap{
    grid-column:2!important;
    border-right:0!important;border-left:1px solid var(--border)!important
  }
  body.display-sides.sides-portrait-flip #catalogMain{grid-column:1!important}
  body.display-sides.search-chrome-collapsed #filterWrap{grid-row:2!important;border-bottom:0!important}
  body.display-sides.kw-chrome-collapsed #searchChrome{grid-row:2!important;border-bottom:0!important}
  body.display-sides.search-chrome-collapsed.kw-chrome-collapsed #catalogMain{grid-column:1!important;grid-row:2!important}
  body.display-sides.layout-edit #searchSplit{
    width:auto!important;min-width:0!important;max-width:none!important;
    height:12px!important;cursor:ns-resize!important
  }
  body.display-sides.layout-edit #dualFsSep{cursor:ew-resize!important}
  body.display-sides.search-chrome-collapsed.layout-edit #searchSplit,
  body.display-sides.kw-chrome-collapsed.layout-edit #searchSplit{display:none!important}
  body.display-sides.kw-chrome-collapsed.layout-edit:not(.search-chrome-collapsed) #dualFsSep,
  body.display-sides.search-chrome-collapsed.layout-edit:not(.kw-chrome-collapsed) #dualFsSep{display:block!important}
  body.display-sides.search-chrome-collapsed.kw-chrome-collapsed.layout-edit #dualFsSep{display:none!important}
  body.display-sides #filterWrap.open .filter-panel{max-height:none!important;flex:1 1 auto;min-height:0;overflow-y:auto!important}
  body.display-sides a.top{bottom:1rem;right:1.25rem!important}
  body.display-sides.sides-portrait-flip a.top{right:calc(var(--portrait-lw,38%) + 1.25rem)!important}
  body.display-sides.layout-edit #dualFsSep::before,body.display-sides.layout-edit #searchSplit::before{
    content:'';display:block;
    background:var(--border,rgba(128,128,128,0.5));border-radius:2px;
    opacity:.6;transition:opacity .15s;position:absolute;top:50%;left:50%;transform:translate(-50%,-50%)
  }
  body.display-sides.layout-edit #dualFsSep::before{width:2px;height:24px}
  body.display-sides.layout-edit #searchSplit::before{width:24px;height:2px}
  body.display-sides.layout-edit #dualFsSep:hover::before,body.display-sides.layout-edit #searchSplit:hover::before{opacity:1}
}
"""

OLD_JS = """// fix-PORTRAIT-SEP: bind portrait Sides separators (ns-resize for row height, col-resize for col widths)
(function(){
  function isPortraitDesktop(){return window.matchMedia&&window.matchMedia('(min-width:900px)').matches&&window.matchMedia('(orientation:portrait)').matches;}
  // ── Horizontal separator (#searchSplit) → adjusts --portrait-menu-h ──
  (function(){
    var h=document.getElementById('searchSplit');if(!h)return;
    var dragging=false,startY=0,startH=0;
    function onMove(e){if(!dragging)return;var y=e.touches?e.touches[0].clientY:e.clientY;var dy=y-startY;var newH=Math.max(80,Math.min(startH+dy,window.innerHeight-80));document.documentElement.style.setProperty('--portrait-menu-h',newH+'px');try{localStorage.setItem('catalog-portrait-menu-h',newH+'px');}catch(ex){}}
    function onUp(){dragging=false;document.removeEventListener('mousemove',onMove);document.removeEventListener('mouseup',onUp);document.removeEventListener('touchmove',onMove);document.removeEventListener('touchend',onUp);}
    h.addEventListener('mousedown',function(e){if(!isPortraitDesktop()||!document.body.classList.contains('display-sides'))return;dragging=true;startY=e.clientY;var sc=document.getElementById('searchChrome');startH=sc?Math.round(sc.getBoundingClientRect().height):300;e.preventDefault();document.addEventListener('mousemove',onMove);document.addEventListener('mouseup',onUp);});
    h.addEventListener('touchstart',function(e){if(!isPortraitDesktop()||!document.body.classList.contains('display-sides'))return;dragging=true;startY=e.touches[0].clientY;var sc=document.getElementById('searchChrome');startH=sc?Math.round(sc.getBoundingClientRect().height):300;document.addEventListener('touchmove',onMove,{passive:false});document.addEventListener('touchend',onUp);},{passive:true});
  })();
  // ── Vertical separator (#dualFsSep) → adjusts --portrait-lw / --portrait-rw ──
  (function(){
    var s=document.getElementById('dualFsSep');if(!s)return;
    var dragging=false,startX=0,startLW=0,totalW=0;
    function onMove(e){if(!dragging)return;var x=e.touches?e.touches[0].clientX:e.clientX;var dx=x-startX;var newLW=Math.max(80,Math.min(startLW+dx,totalW-80));document.documentElement.style.setProperty('--portrait-lw',newLW+'px');document.documentElement.style.setProperty('--portrait-rw',(totalW-newLW-8)+'px');try{localStorage.setItem('catalog-portrait-lw',newLW+'px');localStorage.setItem('catalog-portrait-rw',(totalW-newLW-8)+'px');}catch(ex){}}
    function onUp(){dragging=false;document.removeEventListener('mousemove',onMove);document.removeEventListener('mouseup',onUp);document.removeEventListener('touchmove',onMove);document.removeEventListener('touchend',onUp);}
    s.addEventListener('mousedown',function(e){if(!isPortraitDesktop()||!document.body.classList.contains('display-sides'))return;dragging=true;startX=e.clientX;var sc=document.getElementById('searchChrome');startLW=sc?Math.round(sc.getBoundingClientRect().width):window.innerWidth/2;totalW=window.innerWidth;e.preventDefault();document.addEventListener('mousemove',onMove);document.addEventListener('mouseup',onUp);});
    s.addEventListener('touchstart',function(e){if(!isPortraitDesktop()||!document.body.classList.contains('display-sides'))return;dragging=true;startX=e.touches[0].clientX;var sc=document.getElementById('searchChrome');startLW=sc?Math.round(sc.getBoundingClientRect().width):window.innerWidth/2;totalW=window.innerWidth;document.addEventListener('touchmove',onMove,{passive:false});document.addEventListener('touchend',onUp);},{passive:true});
  })();
  // Restore saved portrait separator positions
  (function(){try{var pmh=localStorage.getItem('catalog-portrait-menu-h');if(pmh)document.documentElement.style.setProperty('--portrait-menu-h',pmh);var plw=localStorage.getItem('catalog-portrait-lw');if(plw)document.documentElement.style.setProperty('--portrait-lw',plw);var prw=localStorage.getItem('catalog-portrait-rw');if(prw)document.documentElement.style.setProperty('--portrait-rw',prw);}catch(ex){}})();
})();
"""

NEW_JS = r"""// fix-PORTRAIT-SEP: portrait A/B helpers (drag lives in bindSidesDrag; Customize + ±30% clamp)
(function(){
  var PORTRAIT_TRAVEL=0.30;
  var PORTRAIT_STACK_FRAC=0.38;
  var PORTRAIT_SEARCH_FRAC=0.50;
  function isPortraitDesktopSides(){return !!(window.matchMedia&&window.matchMedia('(min-width:900px)').matches&&window.matchMedia('(orientation:portrait)').matches);}
  function portraitFlipKey(){return 'catalog-sides-portrait-flip-'+(window.CATALOG_NS||'catalog');}
  function portraitFlipScope(){return (typeof liveLayoutScopeId==='function')?liveLayoutScopeId():'sck';}
  function readPortraitFlipMap(){
    try{
      var raw=localStorage.getItem(portraitFlipKey());
      if(!raw)return {};
      if(raw==='1'||raw==='0'){var on=raw==='1';return {sck:on,sc:on,ck:on,c:on};}
      var o=JSON.parse(raw);
      return (o&&typeof o==='object'&&!Array.isArray(o))?o:{};
    }catch(err){return {};}
  }
  function portraitFlipOn(scope){return !!readPortraitFlipMap()[scope||portraitFlipScope()];}
  function writePortraitFlip(on,scope){
    scope=scope||portraitFlipScope();
    var m=readPortraitFlipMap();
    m[scope]=!!on;
    try{localStorage.setItem(portraitFlipKey(),JSON.stringify(m));}catch(err){}
  }
  function portraitSidesDefaults(){
    var hdr=document.querySelector('.catalog-header');
    var top=hdr?Math.round(hdr.getBoundingClientRect().height):56;
    var availW=Math.max(320,window.innerWidth||900);
    var availH=Math.max(240,(window.innerHeight||1200)-top);
    return {stackW:Math.round(availW*PORTRAIT_STACK_FRAC),searchH:Math.round(availH*PORTRAIT_SEARCH_FRAC),availW:availW,availH:availH};
  }
  function clampPortraitTravel(val,def,track){
    var lo=def-PORTRAIT_TRAVEL*track;
    var hi=def+PORTRAIT_TRAVEL*track;
    if(lo<80)lo=80;
    if(hi>track-80)hi=Math.max(lo,track-80);
    val=Number(val);
    if(!isFinite(val))val=def;
    return Math.round(Math.max(lo,Math.min(hi,val)));
  }
  function parsePortraitStored(key,fallback){
    try{
      var v=localStorage.getItem(key);
      if(!v)return fallback;
      var n=parseInt(v,10);
      return (isFinite(n)&&n>0)?n:fallback;
    }catch(err){return fallback;}
  }
  function logPortraitSides(hid,loc,msg,extra){
    try{
      extra=extra||{};
      extra.flip=document.body.classList.contains('sides-portrait-flip');
      extra.scope=portraitFlipScope();
      extra.lw=(getComputedStyle(document.documentElement).getPropertyValue('--portrait-lw')||'').trim();
      extra.mh=(getComputedStyle(document.documentElement).getPropertyValue('--portrait-menu-h')||'').trim();
      extra.orient=isPortraitDesktopSides();
      extra.edit=document.body.classList.contains('layout-edit');
      extra.w=window.innerWidth;extra.h=window.innerHeight;
      extra.searchCol=document.body.classList.contains('search-chrome-collapsed');
      extra.kwHid=document.body.classList.contains('kw-chrome-collapsed');
      fetch('http://127.0.0.1:7529/ingest/1cf46354-1d61-4c80-bd72-a340f1db1b51',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'f491c2'},body:JSON.stringify({sessionId:'f491c2',runId:'portrait-ab',hypothesisId:hid,location:loc,message:msg,data:extra,timestamp:Date.now()})}).catch(function(){});
    }catch(err){}
  }
  function syncPortraitFlipBtn(){
    var fb=document.getElementById('portraitFlipBtn');
    if(!fb)return;
    var on=portraitFlipOn();
    fb.textContent=on?'Portrait: menus right':'Portrait: menus left';
    fb.setAttribute('aria-pressed',on?'true':'false');
    fb.title='Desktop portrait Sides: put Search/Keywords on the left or right of Content';
    var desk=window.matchMedia&&window.matchMedia('(min-width:900px)').matches;
    fb.hidden=!desk;
  }
  function ensurePortraitFlipBtn(){
    var pop=document.getElementById('layoutPresetsPop');
    if(!pop)return;
    var fb=document.getElementById('portraitFlipBtn');
    if(!fb){
      fb=document.createElement('button');
      fb.type='button';fb.id='portraitFlipBtn';fb.className='layout-restore-defaults';
      fb.addEventListener('click',function(e){
        e.preventDefault();e.stopPropagation();
        togglePortraitSidesFlip();
      });
      var rb=document.getElementById('layoutRestoreDefaults');
      if(rb)rb.insertAdjacentElement('afterend',fb);
      else pop.appendChild(fb);
    }
    syncPortraitFlipBtn();
  }
  function togglePortraitSidesFlip(){
    writePortraitFlip(!portraitFlipOn());
    applyPortraitSides();
    if(typeof placeSidesHandles==='function')placeSidesHandles();
    logPortraitSides('H2','togglePortraitSidesFlip','flip',{});
  }
  function placePortraitSidesHandles(){
    var split=document.getElementById('searchSplit');
    var sep=document.getElementById('dualFsSep');
    var ch=document.getElementById('searchChrome');
    var fw=document.getElementById('filterWrap');
    var hdr=document.querySelector('.catalog-header');
    var top=hdr?Math.round(hdr.getBoundingClientRect().bottom):62;
    var hidden=document.body.classList.contains('search-chrome-collapsed');
    var kwHid=document.body.classList.contains('kw-chrome-collapsed');
    var editing=document.body.classList.contains('layout-edit');
    var flip=document.body.classList.contains('sides-portrait-flip');
    var both=!hidden&&!kwHid;
    function applyBar(el,props){
      if(!el)return;
      el.removeAttribute('style');
      Object.keys(props).forEach(function(k){el.style.setProperty(k,props[k],'important');});
    }
    if(split&&ch&&editing&&both){
      var r=ch.getBoundingClientRect();
      applyBar(split,{position:'fixed',display:'block',left:Math.round(r.left)+'px',width:Math.round(r.width)+'px',top:Math.round(r.bottom-6)+'px',height:'12px','min-width':'0','max-width':'none','min-height':'12px','max-height':'12px',bottom:'auto','z-index':'80',margin:'0',transform:'none','pointer-events':'auto',cursor:'ns-resize'});
    }else if(split){split.removeAttribute('style');}
    var stack=(!hidden&&ch)?ch:(!kwHid&&fw)?fw:null;
    if(sep&&stack&&editing&&(!hidden||!kwHid)){
      var r2=stack.getBoundingClientRect();
      var x=flip?Math.round(r2.left-6):Math.round(r2.right-6);
      applyBar(sep,{position:'fixed',display:'block',top:top+'px',bottom:'0',left:x+'px',width:'12px','min-width':'12px','max-width':'12px',height:'auto','z-index':'80',margin:'0',transform:'none','pointer-events':'auto',cursor:'ew-resize'});
    }else if(sep&&!document.body.classList.contains('dual-fs-open')){sep.removeAttribute('style');}
  }
  function applyPortraitSides(){
    var sides=document.body.classList.contains('display-sides');
    var portrait=isPortraitDesktopSides();
    var flip=sides&&portrait&&portraitFlipOn();
    document.body.classList.toggle('sides-portrait-flip',flip);
    ensurePortraitFlipBtn();
    if(!sides||!portrait){
      syncPortraitFlipBtn();
      return;
    }
    var d=portraitSidesDefaults();
    var lw=clampPortraitTravel(parsePortraitStored('catalog-portrait-lw',d.stackW),d.stackW,d.availW);
    var mh=clampPortraitTravel(parsePortraitStored('catalog-portrait-menu-h',d.searchH),d.searchH,d.availH);
    document.documentElement.style.setProperty('--portrait-lw',lw+'px');
    document.documentElement.style.setProperty('--portrait-menu-h',mh+'px');
    document.documentElement.style.setProperty('--portrait-rw',Math.max(80,d.availW-lw)+'px');
    syncPortraitFlipBtn();
    logPortraitSides('H1','applyPortraitSides','apply',{defW:d.stackW,defH:d.searchH,availW:d.availW,availH:d.availH,lw:lw,mh:mh});
  }
  window.isPortraitDesktopSides=isPortraitDesktopSides;
  window.portraitSidesDefaults=portraitSidesDefaults;
  window.clampPortraitTravel=clampPortraitTravel;
  window.applyPortraitSides=applyPortraitSides;
  window.placePortraitSidesHandles=placePortraitSidesHandles;
  window.togglePortraitSidesFlip=togglePortraitSidesFlip;
  window.syncPortraitFlipBtn=syncPortraitFlipBtn;
  window.logPortraitSides=logPortraitSides;
  try{applyPortraitSides();if(typeof placeSidesHandles==='function')placeSidesHandles();}catch(err){}
  if(window.matchMedia){
    var mqP=window.matchMedia('(orientation: portrait)');
    var mqD=window.matchMedia('(min-width:900px)');
    function onQ(){if(typeof applySidesCols==='function')applySidesCols();}
    if(mqP.addEventListener){mqP.addEventListener('change',onQ);mqD.addEventListener('change',onQ);}
    else if(mqP.addListener){mqP.addListener(onQ);mqD.addListener(onQ);}
  }
})();
"""

OLD_PLACE = """function placeSidesHandles(){
  if(!document.body.classList.contains('display-sides'))return;
  var split=document.getElementById('searchSplit');
"""

NEW_PLACE = """function placeSidesHandles(){
  if(!document.body.classList.contains('display-sides'))return;
  if(typeof isPortraitDesktopSides==='function'&&isPortraitDesktopSides()){
    if(typeof placePortraitSidesHandles==='function')placePortraitSidesHandles();
    return;
  }
  var split=document.getElementById('searchSplit');
"""

OLD_DOWN = """    e.preventDefault();e.stopPropagation();
    var vw=window.innerWidth||1200;
    var t=e.currentTarget||e.target;
    drag={which:which,x:e.clientX,lw:parseInt(getComputedStyle(document.body).getPropertyValue('--sides-lw'),10)||Math.round(vw*0.22),rw:parseInt(getComputedStyle(document.body).getPropertyValue('--sides-rw'),10)||Math.round(vw*0.26),id:e.pointerId};
"""

NEW_DOWN = """    e.preventDefault();e.stopPropagation();
    if(typeof isPortraitDesktopSides==='function'&&isPortraitDesktopSides()){
      var d=typeof portraitSidesDefaults==='function'?portraitSidesDefaults():null;
      if(!d)return;
      var root=document.documentElement;
      var plw=parseInt(getComputedStyle(root).getPropertyValue('--portrait-lw'),10)||d.stackW;
      var pmh=parseInt(getComputedStyle(root).getPropertyValue('--portrait-menu-h'),10)||d.searchH;
      var tP=e.currentTarget||e.target;
      drag={portrait:true,which:which,x:e.clientX,y:e.clientY,lw:plw,mh:pmh,flip:document.body.classList.contains('sides-portrait-flip'),def:d,id:e.pointerId};
      try{if(tP&&tP.setPointerCapture)tP.setPointerCapture(e.pointerId);}catch(err){}
      if(typeof logSidesEdit==='function')logSidesEdit('H3','sides-handle','pointerdown',{which:which,portrait:true,x:e.clientX,y:e.clientY,fired:true});
      return;
    }
    var vw=window.innerWidth||1200;
    var t=e.currentTarget||e.target;
    drag={which:which,x:e.clientX,lw:parseInt(getComputedStyle(document.body).getPropertyValue('--sides-lw'),10)||Math.round(vw*0.22),rw:parseInt(getComputedStyle(document.body).getPropertyValue('--sides-rw'),10)||Math.round(vw*0.26),id:e.pointerId};
"""

OLD_MOVE = """  function onMove(e){
    if(!drag)return;
    var vw=window.innerWidth||1200;
    var minL=240,minR=260,minC=280;
"""

NEW_MOVE = """  function onMove(e){
    if(!drag)return;
    if(drag.portrait){
      var clamp=window.clampPortraitTravel||function(v){return v;};
      if(drag.which==='split'){
        var mh=clamp(drag.mh+(e.clientY-drag.y),drag.def.searchH,drag.def.availH);
        document.documentElement.style.setProperty('--portrait-menu-h',mh+'px');
      }else{
        var dx=e.clientX-drag.x;
        var nlw=clamp(drag.flip?drag.lw-dx:drag.lw+dx,drag.def.stackW,drag.def.availW);
        document.documentElement.style.setProperty('--portrait-lw',nlw+'px');
        document.documentElement.style.setProperty('--portrait-rw',Math.max(80,drag.def.availW-nlw)+'px');
      }
      placeSidesHandles();
      return;
    }
    var vw=window.innerWidth||1200;
    var minL=240,minR=260,minC=280;
"""

OLD_UP = """  function onUp(e){
    if(!drag)return;
    var lw=parseInt(getComputedStyle(document.body).getPropertyValue('--sides-lw'),10)||0;
"""

NEW_UP = """  function onUp(e){
    if(!drag)return;
    if(drag.portrait){
      var plw=parseInt(getComputedStyle(document.documentElement).getPropertyValue('--portrait-lw'),10)||0;
      var pmh=parseInt(getComputedStyle(document.documentElement).getProperty('--portrait-menu-h'),10)||0;
      var whichP=drag.which;
      try{
        localStorage.setItem('catalog-portrait-lw',plw+'px');
        localStorage.setItem('catalog-portrait-menu-h',pmh+'px');
        localStorage.setItem('catalog-portrait-rw',Math.max(0,(window.innerWidth||0)-plw)+'px');
      }catch(ex){}
      drag=null;
      if(typeof logSidesEdit==='function')logSidesEdit('H3','sides-handle','pointerup',{which:whichP,portrait:true,lw:plw,mh:pmh});
      if(typeof logPortraitSides==='function')logPortraitSides('H3','sides-handle','portrait-up',{which:whichP,lw:plw,mh:pmh});
      return;
    }
    var lw=parseInt(getComputedStyle(document.body).getPropertyValue('--sides-lw'),10)||0;
"""

OLD_APPLY = """  placeSidesHandles();
  syncSidesPin();
"""

NEW_APPLY = """  if(typeof applyPortraitSides==='function')applyPortraitSides();
  placeSidesHandles();
  syncSidesPin();
"""

OLD_RESET = """    localStorage.removeItem('catalog-portrait-rw');
  }catch(err){}
"""

NEW_RESET = """    localStorage.removeItem('catalog-portrait-rw');
    try{localStorage.removeItem('catalog-sides-portrait-flip-'+(window.CATALOG_NS||'catalog'));}catch(eFlip){}
    document.body.classList.remove('sides-portrait-flip');
  }catch(err){}
"""

OLD_SYNC = """  var lab=document.getElementById('layoutPresetsStoreLabel');
  if(lab)lab.textContent=meta.label;
"""

NEW_SYNC = """  var lab=document.getElementById('layoutPresetsStoreLabel');
  if(lab)lab.textContent=meta.label;
  if(typeof syncPortraitFlipBtn==='function')syncPortraitFlipBtn();
"""


def brace_delta(s):
    return s.count("{") - s.count("}")


def must_replace(text, old, new, label):
    n = text.count(old)
    if n != 1:
        raise SystemExit(f"COUNT [{label}]: expected 1, found {n}")
    return text.replace(old, new, 1)


def patch(text, name):
    text = must_replace(text, OLD_CSS, NEW_CSS, f"{name}:css")
    text = must_replace(text, OLD_JS, NEW_JS, f"{name}:js")
    text = must_replace(text, OLD_PLACE, NEW_PLACE, f"{name}:place")
    text = must_replace(text, OLD_DOWN, NEW_DOWN, f"{name}:down")
    text = must_replace(text, OLD_MOVE, NEW_MOVE, f"{name}:move")
    text = must_replace(text, OLD_UP, NEW_UP, f"{name}:up")
    text = must_replace(text, OLD_APPLY, NEW_APPLY, f"{name}:apply")
    text = must_replace(text, OLD_RESET, NEW_RESET, f"{name}:reset")
    text = must_replace(text, OLD_SYNC, NEW_SYNC, f"{name}:sync")
    return text


def main():
    js_delta = brace_delta(NEW_JS) - brace_delta(OLD_JS)
    extra = (
        brace_delta(NEW_PLACE)
        + brace_delta(NEW_DOWN)
        + brace_delta(NEW_MOVE)
        + brace_delta(NEW_UP)
        + brace_delta(NEW_APPLY)
        + brace_delta(NEW_RESET)
        + brace_delta(NEW_SYNC)
        - brace_delta(OLD_PLACE)
        - brace_delta(OLD_DOWN)
        - brace_delta(OLD_MOVE)
        - brace_delta(OLD_UP)
        - brace_delta(OLD_APPLY)
        - brace_delta(OLD_RESET)
        - brace_delta(OLD_SYNC)
    )
    print("JS IIFE brace delta", js_delta, "other JS brace delta", extra)
    if js_delta != 0 or extra != 0:
        raise SystemExit("Brace imbalance in patch snippets")

    for path in FILES:
        raw = path.read_text(encoding="utf-8")
        before = brace_delta(raw)
        new = patch(raw, path.name)
        after = brace_delta(new)
        if after != before:
            raise SystemExit(f"Brace mismatch in {path.name}: {before} -> {after}")
        path.write_text(new, encoding="utf-8")
        print("patched", path, "braces", after)


if __name__ == "__main__":
    main()
