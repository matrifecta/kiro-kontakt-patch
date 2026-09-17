#!/usr/bin/env python3
"""Sides hide-search, Index height persist, Customize/Lock redesign.

Patch KIRO builders first, copy to workspace, then in-memory sync HTML.
"""
from pathlib import Path
import shutil

KIRO = Path("/home/phnx/KIRO/.kiro/specs/kontakt-workspace-drive-dirty-fix/artifacts")
WS = Path("/home/phnx/kiro-kontakt-patch/kiro/specs/kontakt-workspace-drive-dirty-fix/artifacts")
PUB = Path("/home/phnx/kiro-kontakt-patch/public/catalogs")

INGEST = "http://127.0.0.1:7529/ingest/1cf46354-1d61-4c80-bd72-a340f1db1b51"

REPLACEMENTS = []


def add(old, new, label, optional=False, replace_all=False):
    if isinstance(old, str):
        old = (old,)
    REPLACEMENTS.append((old, new, label, optional, replace_all))


LOG_HELPER = r"""
function logSidesEdit(hid,loc,msg,extra){
  // #region agent log
  try{
    extra=extra||{};
    var ch=document.getElementById('searchChrome');
    var hide=document.querySelector('.search-strip-hide');
    var ix=document.getElementById('catalogIndex');
    var fw=document.getElementById('filterWrap');
    var split=document.getElementById('searchSplit');
    var ih=document.getElementById('indexHeight');
    function box(el){if(!el)return null;var b=el.getBoundingClientRect();return{x:Math.round(b.x),y:Math.round(b.y),w:Math.round(b.width),h:Math.round(b.height)};}
    extra.display=typeof currentDisplay!=='undefined'?currentDisplay:'';
    extra.collapsed=document.body.classList.contains('search-chrome-collapsed');
    extra.edit=document.body.classList.contains('layout-edit');
    extra.pinned=typeof modeLayoutPinned==='function'?!!modeLayoutPinned():null;
    extra.lw=(getComputedStyle(document.body).getPropertyValue('--sides-lw')||'').trim();
    extra.rw=(getComputedStyle(document.body).getPropertyValue('--sides-rw')||'').trim();
    extra.indexCss=(getComputedStyle(document.body).getPropertyValue('--sides-index-h')||'').trim();
    extra.chip=hide?{txt:hide.textContent,disp:getComputedStyle(hide).display,box:box(hide)}:null;
    extra.ch=ch?{disp:getComputedStyle(ch).display,box:box(ch)}:null;
    extra.fw=box(fw);
    extra.ix=box(ix);
    extra.split=split?{disp:getComputedStyle(split).display,pe:getComputedStyle(split).pointerEvents,z:getComputedStyle(split).zIndex,box:box(split)}:null;
    extra.indexHandle=ih?{disp:getComputedStyle(ih).display,pe:getComputedStyle(ih).pointerEvents,box:box(ih)}:null;
    extra.editLabel=(document.getElementById('layoutEditBtn')||{}).textContent||'';
    extra.lockLabel=(document.getElementById('modePinBtn')||{}).textContent||'';
    extra.slot=typeof readModeSlot==='function'?readModeSlot(extra.display||'sides'):null;
    fetch('""" + INGEST + r"""',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'f491c2'},body:JSON.stringify({sessionId:'f491c2',runId:'sides-edit',hypothesisId:hid,location:loc,message:msg,data:extra,timestamp:Date.now()})}).catch(function(){});
  }catch(err){}
  // #endregion
}
window.logSidesEdit=logSidesEdit;
"""


# --- A. Sides hide-search: no leftover column / chip ---
add(
    "  body.display-sides.search-chrome-collapsed{grid-template-columns:max-content minmax(0,1fr) var(--sides-rw,26vw)}\n",
    "  body.display-sides.search-chrome-collapsed{grid-template-columns:0 minmax(0,1fr) var(--sides-rw,26vw)}\n",
    "sides-hide-grid",
)
add(
    "  body.display-sides.search-chrome-collapsed #searchChrome{width:auto;min-width:0;border-right:1px solid var(--border)}\n",
    "  body.display-sides.search-chrome-collapsed #searchChrome{display:none!important;width:0!important;min-width:0!important;max-width:0!important;overflow:hidden!important;border:0!important;padding:0!important}\n"
    "  body.display-sides.search-chrome-collapsed .search-strip-hide,body.display-sides.search-chrome-collapsed #searchChrome .search-strip{display:none!important}\n"
    "  body.display-sides.search-chrome-collapsed #searchSplit{display:none!important}\n",
    "sides-hide-chrome",
)
add(
    " body.display-sides.search-chrome-collapsed:not(.kw-open){grid-template-columns:max-content minmax(0,1fr) max-content}\n",
    " body.display-sides.search-chrome-collapsed:not(.kw-open){grid-template-columns:0 minmax(0,1fr) max-content}\n",
    "sides-hide-nokw",
)

# --- B. Index height + handle ---
add(
    "  body.display-sides #catalogIndex{position:sticky;top:0;z-index:12;margin:0 0 .75rem;display:flex;flex-direction:column;max-height:min(48dvh,28rem);overflow:hidden;border:1px solid var(--border);border-top-width:1px;border-radius:0 0 10px 10px;background:var(--bg-surface);box-shadow:0 10px 24px rgba(0,0,0,.32)}\n",
    "  body.display-sides #catalogIndex{position:sticky;top:0;z-index:12;margin:0 0 .75rem;display:flex;flex-direction:column;height:var(--sides-index-h,min(48dvh,28rem));max-height:min(70dvh,40rem);overflow:hidden;border:1px solid var(--border);border-top-width:1px;border-radius:0 0 10px 10px;background:var(--bg-surface);box-shadow:0 10px 24px rgba(0,0,0,.32)}\n"
    "  body.display-sides #catalogIndex #indexHeight{display:none;box-sizing:border-box;position:absolute;z-index:22;left:0;right:0;bottom:0;width:100%;height:.75rem;margin:0;padding:0;border:0;background:transparent;cursor:ns-resize;touch-action:none;-webkit-user-select:none;user-select:none}\n"
    "  body.display-sides #catalogIndex #indexHeight::before{content:\"\";position:absolute;left:28%;right:28%;top:3px;height:4px;background:var(--border);border-radius:2px;pointer-events:none}\n"
    "  body.display-sides.layout-edit:not(.mode-layout-pinned) #catalogIndex #indexHeight{display:block!important;pointer-events:auto!important}\n",
    "index-h-css",
)
add(
    "  body.display-sides #catalogIndex.is-collapsed{max-height:none}\n",
    "  body.display-sides #catalogIndex.is-collapsed{height:auto!important;max-height:none}\n",
    "index-collapsed-h",
)

# --- C. Handles z-index + hide duplicate pins ---
add(
    "  body.display-sides.layout-edit #searchSplit,body.display-sides #dualFsSep{display:block!important;position:fixed!important;z-index:40!important;width:10px!important;transform:none!important;margin:0;padding:0;cursor:col-resize;pointer-events:auto}\n"
    "  body.display-sides:not(.layout-edit) #searchSplit{display:none!important}\n"
    "  body.display-sides.sides-pinned #searchSplit,body.display-sides.sides-pinned #dualFsSep{cursor:default!important}\n"
    "  body.display-sides #dualFsSep .dual-fs-sep-pin{display:flex}\n",
    "  body.display-sides.layout-edit #searchSplit,body.display-sides.layout-edit #dualFsSep{display:block!important;position:fixed!important;z-index:80!important;width:12px!important;transform:none!important;margin:0;padding:0;cursor:col-resize;pointer-events:auto!important}\n"
    "  body.display-sides:not(.layout-edit) #searchSplit,body.display-sides:not(.layout-edit) #dualFsSep{display:none!important}\n"
    "  body.display-sides.search-chrome-collapsed.layout-edit #searchSplit{display:none!important}\n"
    "  body.display-sides.sides-pinned #searchSplit,body.display-sides.sides-pinned #dualFsSep,body.mode-layout-pinned #searchSplit,body.mode-layout-pinned #dualFsSep,body.mode-layout-pinned #indexHeight{cursor:default!important;pointer-events:none!important}\n"
    "  body.display-sides #dualFsSep .dual-fs-sep-pin,body #fsSepPinBtn{display:none!important}\n",
    "sides-handles-z",
)
add(
    "  body.display-sides.layout-edit #searchSplit,body.display-sides.layout-edit #dualFsSep{display:block!important;position:fixed!important;z-index:80!important;width:12px!important;transform:none!important;margin:0;padding:0;cursor:col-resize;pointer-events:auto!important}\n",
    "  body.display-sides.layout-edit #searchSplit,body.display-sides.layout-edit #dualFsSep{display:block!important;position:fixed!important;z-index:80!important;width:12px!important;min-width:12px!important;max-width:12px!important;transform:none!important;margin:0;padding:0;cursor:col-resize;pointer-events:auto!important}\n",
    "sides-handle-hit",
)
add(
    " body.layout-edit:not(.mode-layout-pinned) .ac-height,body.layout-edit:not(.mode-layout-pinned) .ac-width,body.layout-edit:not(.mode-layout-pinned) .kw-shade-height,body.layout-edit:not(.mode-layout-pinned) .search-height,body.layout-edit:not(.mode-layout-pinned) .search-split{pointer-events:auto!important;z-index:46}\n",
    " body.layout-edit:not(.mode-layout-pinned) .ac-height,body.layout-edit:not(.mode-layout-pinned) .ac-width,body.layout-edit:not(.mode-layout-pinned) .kw-shade-height,body.layout-edit:not(.mode-layout-pinned) .search-height,body.layout-edit:not(.mode-layout-pinned) .search-split,body.layout-edit:not(.mode-layout-pinned) #indexHeight{pointer-events:auto!important;z-index:80}\n",
    "edit-pe",
)
add(
    " body.mode-layout-pinned.layout-edit .search-split,body.mode-layout-pinned.layout-edit .search-height,body.mode-layout-pinned.layout-edit .ac-height,body.mode-layout-pinned.layout-edit .kw-shade-height,body.mode-layout-pinned.layout-edit #searchSplit,body.mode-layout-pinned.layout-edit #dualFsSep{cursor:default!important;pointer-events:none!important}\n",
    " body.mode-layout-pinned.layout-edit .search-split,body.mode-layout-pinned.layout-edit .search-height,body.mode-layout-pinned.layout-edit .ac-height,body.mode-layout-pinned.layout-edit .kw-shade-height,body.mode-layout-pinned.layout-edit #searchSplit,body.mode-layout-pinned.layout-edit #dualFsSep,body.mode-layout-pinned.layout-edit #indexHeight{cursor:default!important;pointer-events:none!important}\n",
    "lock-pe",
)

# --- Button labels in HTML (sh echo + generated html) ---
add(
    'title="Drag menu edges to resize. Lock when finished." onclick="event.preventDefault();event.stopPropagation();toggleLayoutEdit()">Edit layout</button>',
    'title="Show drag edges to resize Search, Keywords, Index, and menu height" onclick="event.preventDefault();event.stopPropagation();toggleLayoutEdit()">Customize</button>',
    "edit-btn-html",
)

# --- Customize (was Edit layout / Lock layout) ---
add(
    "function syncLayoutEditBtn(){\n"
    "  var on=document.body.classList.contains('layout-edit');\n"
    "  document.querySelectorAll('.layout-edit-btn').forEach(function(b){\n"
    "    b.textContent=on?'Lock layout':'Edit layout';\n"
    "    b.setAttribute('aria-pressed',on?'true':'false');\n"
    "  });\n"
    "}\n",
    "function syncLayoutEditBtn(){\n"
    "  var on=document.body.classList.contains('layout-edit');\n"
    "  document.querySelectorAll('#layoutEditBtn,.layout-edit-btn:not(#modePinBtn)').forEach(function(b){\n"
    "    if(b.id==='modePinBtn')return;\n"
    "    b.textContent=on?'Done':'Customize';\n"
    "    b.setAttribute('aria-pressed',on?'true':'false');\n"
    "    b.title=on?'Finish arranging UI edges':'Show drag edges to resize Search, Keywords, Index, and menu height';\n"
    "    b.setAttribute('aria-label',on?'Done arranging':'Customize layout');\n"
    "  });\n"
    "  if(typeof syncModeLockBtn==='function')syncModeLockBtn();\n"
    "}\n",
    "sync-customize",
)

# --- collapse / expand search in Sides ---
add(
    "  document.body.classList.add('search-chrome-collapsed','search-extras-collapsed');\n"
    "  syncSearchHideBtn();\n"
    "}\n"
    "window.collapseSearchMenu=collapseSearchMenu;\n",
    "  document.body.classList.add('search-chrome-collapsed','search-extras-collapsed');\n"
    "  syncSearchHideBtn();\n"
    "  if(typeof applySidesCols==='function')applySidesCols();\n"
    "  if(typeof logSidesEdit==='function')logSidesEdit('H1','collapseSearchMenu','sides-hide-search',{sides:document.body.classList.contains('display-sides')});\n"
    "}\n"
    "window.collapseSearchMenu=collapseSearchMenu;\n",
    "collapse-sides",
)
add(
    "  document.body.classList.remove('search-chrome-collapsed','search-extras-collapsed');\n"
    "  syncSearchHideBtn();\n"
    "  if(typeof window.applyActiveLayoutStore==='function'){\n",
    "  document.body.classList.remove('search-chrome-collapsed','search-extras-collapsed');\n"
    "  syncSearchHideBtn();\n"
    "  if(typeof applySidesCols==='function')applySidesCols();\n"
    "  if(typeof window.applyActiveLayoutStore==='function'){\n",
    "expand-sides",
)

# --- snapshot indexH ---
add(
    "    if(mode==='sides'){\n"
    "      var lw=parseInt(getComputedStyle(document.body).getPropertyValue('--sides-lw'),10)||0;\n"
    "      var rw=parseInt(getComputedStyle(document.body).getPropertyValue('--sides-rw'),10)||0;\n"
    "      if(lw)patch.lw=lw;\n"
    "      if(rw)patch.rw=rw;\n"
    "      patch.pinned=!!sidesPinned;\n"
    "    }else if(mode==='fs'){\n",
    "    if(mode==='sides'){\n"
    "      var lw=parseInt(getComputedStyle(document.body).getPropertyValue('--sides-lw'),10)||0;\n"
    "      var rw=parseInt(getComputedStyle(document.body).getPropertyValue('--sides-rw'),10)||0;\n"
    "      if(lw)patch.lw=lw;\n"
    "      if(rw)patch.rw=rw;\n"
    "      var ih=parseInt(getComputedStyle(document.body).getPropertyValue('--sides-index-h'),10)||0;\n"
    "      if(!ih){var ixEl=document.getElementById('catalogIndex');if(ixEl&&!ixEl.classList.contains('is-collapsed'))ih=Math.round(ixEl.getBoundingClientRect().height);}\n"
    "      if(ih>40)patch.indexH=ih;\n"
    "      patch.pinned=!!sidesPinned;\n"
    "    }else if(mode==='fs'){\n",
    "snap-indexH",
)

# --- applyModeSlot indexH ---
add(
    "    if(mode==='sides'){\n"
    "      if(slot.lw&&slot.rw)localStorage.setItem(SIDES_KEY,JSON.stringify({lw:slot.lw,rw:slot.rw}));\n"
    "      if(typeof slot.pinned==='boolean'){\n"
    "        sidesPinned=!!slot.pinned;\n"
    "        localStorage.setItem(SIDES_KEY+'-pin',sidesPinned?'1':'0');\n"
    "      }\n"
    "    }else{\n",
    "    if(mode==='sides'){\n"
    "      if(slot.lw&&slot.rw)localStorage.setItem(SIDES_KEY,JSON.stringify({lw:slot.lw,rw:slot.rw}));\n"
    "      if(slot.indexH)document.body.style.setProperty('--sides-index-h',parseInt(slot.indexH,10)+'px');\n"
    "      if(typeof slot.pinned==='boolean'){\n"
    "        sidesPinned=!!slot.pinned;\n"
    "        localStorage.setItem(SIDES_KEY+'-pin',sidesPinned?'1':'0');\n"
    "      }\n"
    "    }else{\n",
    "apply-indexH",
)

# --- applySidesCols: 0 lw when hidden; apply index height ---
add(
    "    document.body.style.removeProperty('--sides-lw');\n"
    "    document.body.style.removeProperty('--sides-rw');\n",
    "    document.body.style.removeProperty('--sides-lw');\n"
    "    document.body.style.removeProperty('--sides-rw');\n"
    "    document.body.style.removeProperty('--sides-index-h');\n",
    "leave-sides-index",
)
add(
    "  if(document.body.classList.contains('search-chrome-collapsed')){\n"
    "    document.body.style.removeProperty('--sides-lw');\n"
    "  }else{\n"
    "    lw=Math.max(minL,Math.min(lw,vw-minR-minC));\n"
    "    document.body.style.setProperty('--sides-lw',lw+'px');\n"
    "  }\n",
    "  if(document.body.classList.contains('search-chrome-collapsed')){\n"
    "    document.body.style.setProperty('--sides-lw','0px');\n"
    "  }else{\n"
    "    lw=Math.max(minL,Math.min(lw,vw-minR-minC));\n"
    "    document.body.style.setProperty('--sides-lw',lw+'px');\n"
    "  }\n"
    "  if(typeof applySidesIndexH==='function')applySidesIndexH();\n",
    "sides-lw-zero",
)

# --- placeSidesHandles z-index + skip when hidden ---
add(
    "function placeSidesHandles(){\n"
    "  if(!document.body.classList.contains('display-sides'))return;\n"
    "  var split=document.getElementById('searchSplit');\n"
    "  var sep=document.getElementById('dualFsSep');\n"
    "  var ch=document.getElementById('searchChrome');\n"
    "  var fw=document.getElementById('filterWrap');\n"
    "  var hdr=document.querySelector('.catalog-header');\n"
    "  var top=hdr?Math.round(hdr.getBoundingClientRect().bottom):62;\n"
    "  if(split&&ch){\n"
    "    var r=ch.getBoundingClientRect();\n"
    "    split.style.cssText='position:fixed;top:'+top+'px;bottom:0;left:'+Math.round(r.right-5)+'px;width:10px;height:auto;z-index:40;margin:0;transform:none;';\n"
    "  }\n"
    "  if(sep&&fw){\n"
    "    var r2=fw.getBoundingClientRect();\n"
    "    sep.style.cssText='position:fixed;top:'+top+'px;bottom:0;left:'+Math.round(r2.left-5)+'px;width:10px;height:auto;z-index:40;margin:0;transform:none;';\n"
    "  }\n"
    "}\n",
    "function placeSidesHandles(){\n"
    "  if(!document.body.classList.contains('display-sides'))return;\n"
    "  var split=document.getElementById('searchSplit');\n"
    "  var sep=document.getElementById('dualFsSep');\n"
    "  var ch=document.getElementById('searchChrome');\n"
    "  var fw=document.getElementById('filterWrap');\n"
    "  var hdr=document.querySelector('.catalog-header');\n"
    "  var top=hdr?Math.round(hdr.getBoundingClientRect().bottom):62;\n"
    "  var hidden=document.body.classList.contains('search-chrome-collapsed');\n"
    "  var editing=document.body.classList.contains('layout-edit');\n"
    "  if(split&&ch&&!hidden&&editing){\n"
    "    var r=ch.getBoundingClientRect();\n"
    "    split.style.cssText='position:fixed;top:'+top+'px;bottom:0;left:'+Math.round(r.right-6)+'px;width:12px;height:auto;z-index:80;margin:0;transform:none;pointer-events:auto;';\n"
    "  }else if(split){split.removeAttribute('style');}\n"
    "  if(sep&&fw&&editing){\n"
    "    var r2=fw.getBoundingClientRect();\n"
    "    sep.style.cssText='position:fixed;top:'+top+'px;bottom:0;left:'+Math.round(r2.left-6)+'px;width:12px;height:auto;z-index:80;margin:0;transform:none;pointer-events:auto;';\n"
    "  }else if(sep&&!document.body.classList.contains('dual-fs-open')){sep.removeAttribute('style');}\n"
    "}\n",
    "place-handles",
)

SIDES_DRAG_HEAD = (
    "(function bindSidesDrag(){\n"
    "  var drag=null;\n"
    "  function onDown(e,which){\n"
    "    if(!document.body.classList.contains('display-sides'))return;\n"
    "    if(!document.body.classList.contains('layout-edit'))return;\n"
    "    if(sidesPinned)return;\n"
    "    if(e.button!=null&&e.button!==0)return;\n"
    "    e.preventDefault();e.stopPropagation();\n"
    "    var vw=window.innerWidth||1200;\n"
    "    drag={which:which,x:e.clientX,lw:parseInt(getComputedStyle(document.body).getPropertyValue('--sides-lw'),10)||Math.round(vw*0.22),rw:parseInt(getComputedStyle(document.body).getPropertyValue('--sides-rw'),10)||Math.round(vw*0.26),id:e.pointerId};\n"
    "    try{e.currentTarget.setPointerCapture(e.pointerId);}catch(err){}\n"
    "  }\n"
    "  function onMove(e){\n"
    "    if(!drag)return;\n"
    "    var vw=window.innerWidth||1200;\n"
    "    var minL=240,minR=260,minC=280;\n"
    "    if(drag.which==='split'){\n"
    "      var lw=Math.max(minL,Math.min(vw-minR-minC,drag.lw+(e.clientX-drag.x)));\n"
    "      document.body.style.setProperty('--sides-lw',lw+'px');\n"
    "    }else{\n"
    "      var rw=Math.max(minR,Math.min(vw-minL-minC,drag.rw-(e.clientX-drag.x)));\n"
    "      document.body.style.setProperty('--sides-rw',rw+'px');\n"
    "    }\n"
    "    placeSidesHandles();\n"
    "  }\n"
    "  function onUp(){\n"
    "    if(!drag)return;\n"
    "    var lw=parseInt(getComputedStyle(document.body).getPropertyValue('--sides-lw'),10)||0;\n"
    "    var rw=parseInt(getComputedStyle(document.body).getPropertyValue('--sides-rw'),10)||0;\n"
    "    writeSidesCols(lw,rw);\n"
    "    drag=null;\n"
)
SIDES_DRAG_TAIL = (
    "  }\n"
    "  var split=document.getElementById('searchSplit');\n"
    "  var sep=document.getElementById('dualFsSep');\n"
    "  if(split){split.addEventListener('pointerdown',function(e){onDown(e,'split');});split.addEventListener('pointermove',onMove);split.addEventListener('pointerup',onUp);}\n"
    "  if(sep){sep.addEventListener('pointerdown',function(e){if(e.target&&e.target.closest&&e.target.closest('#dualFsSepPin'))return;onDown(e,'sep');});sep.addEventListener('pointermove',onMove);sep.addEventListener('pointerup',onUp);}\n"
    "})();\n"
)
SIDES_DRAG_FETCH = (
    "    fetch('http://127.0.0.1:7529/ingest/1cf46354-1d61-4c80-bd72-a340f1db1b51',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'f491c2'},body:JSON.stringify({sessionId:'f491c2',runId:'post-fix',hypothesisId:'H1',location:'sides-drag',message:'sides-resized',data:{lw:lw,rw:rw,pinned:sidesPinned},timestamp:Date.now()})}).catch(function(){});\n"
)

# --- bindSidesDrag: document listeners + PointerEvent ---
add(
    (
        SIDES_DRAG_HEAD
        + "    // #region agent log\n"
        + SIDES_DRAG_FETCH
        + "    // #endregion\n"
        + SIDES_DRAG_TAIL,
        SIDES_DRAG_HEAD + SIDES_DRAG_FETCH + SIDES_DRAG_TAIL,
    ),
    "(function bindSidesDrag(){\n"
    "  var drag=null;\n"
    "  function onDown(e,which){\n"
    "    if(!document.body.classList.contains('display-sides'))return;\n"
    "    if(!document.body.classList.contains('layout-edit'))return;\n"
    "    if(sidesPinned||(typeof modeLayoutPinned==='function'&&modeLayoutPinned()))return;\n"
    "    if(e.pointerType==='mouse'&&e.button!=null&&e.button!==0)return;\n"
    "    e.preventDefault();e.stopPropagation();\n"
    "    var vw=window.innerWidth||1200;\n"
    "    var t=e.currentTarget||e.target;\n"
    "    drag={which:which,x:e.clientX,lw:parseInt(getComputedStyle(document.body).getPropertyValue('--sides-lw'),10)||Math.round(vw*0.22),rw:parseInt(getComputedStyle(document.body).getPropertyValue('--sides-rw'),10)||Math.round(vw*0.26),id:e.pointerId};\n"
    "    try{if(t&&t.setPointerCapture)t.setPointerCapture(e.pointerId);}catch(err){}\n"
    "    if(typeof logSidesEdit==='function')logSidesEdit('H3','sides-handle','pointerdown',{which:which,x:e.clientX,fired:true});\n"
    "  }\n"
    "  function onMove(e){\n"
    "    if(!drag)return;\n"
    "    var vw=window.innerWidth||1200;\n"
    "    var minL=240,minR=260,minC=280;\n"
    "    if(drag.which==='split'){\n"
    "      var lw=Math.max(minL,Math.min(vw-minR-minC,drag.lw+(e.clientX-drag.x)));\n"
    "      document.body.style.setProperty('--sides-lw',lw+'px');\n"
    "    }else{\n"
    "      var rw=Math.max(minR,Math.min(vw-minL-minC,drag.rw-(e.clientX-drag.x)));\n"
    "      document.body.style.setProperty('--sides-rw',rw+'px');\n"
    "    }\n"
    "    placeSidesHandles();\n"
    "  }\n"
    "  function onUp(e){\n"
    "    if(!drag)return;\n"
    "    var lw=parseInt(getComputedStyle(document.body).getPropertyValue('--sides-lw'),10)||0;\n"
    "    var rw=parseInt(getComputedStyle(document.body).getPropertyValue('--sides-rw'),10)||0;\n"
    "    var which=drag.which,dx=e&&e.clientX!=null?(e.clientX-drag.x):0;\n"
    "    writeSidesCols(lw,rw);\n"
    "    drag=null;\n"
    "    if(typeof logSidesEdit==='function')logSidesEdit('H3','sides-handle','pointerup',{which:which,dx:dx,lw:lw,rw:rw});\n"
    "  }\n"
    "  function bind(el,which){\n"
    "    if(!el||el.dataset.sidesDragBound)return;\n"
    "    el.dataset.sidesDragBound='1';\n"
    "    el.addEventListener('pointerdown',function(e){if(e.target&&e.target.closest&&e.target.closest('#dualFsSepPin'))return;onDown(e,which);});\n"
    "  }\n"
    "  bind(document.getElementById('searchSplit'),'split');\n"
    "  bind(document.getElementById('dualFsSep'),'sep');\n"
    "  document.addEventListener('pointermove',onMove);\n"
    "  document.addEventListener('pointerup',onUp);\n"
    "  document.addEventListener('pointercancel',onUp);\n"
    "})();\n",
    "bind-sides-ptr",
)

# --- Index height helpers after bindSidesDrag ---
INDEX_JS = r"""
function applySidesIndexH(){
  if(!document.body.classList.contains('display-sides')){
    document.body.style.removeProperty('--sides-index-h');
    return;
  }
  var slot=typeof readModeSlot==='function'?readModeSlot('sides'):{};
  var h=parseInt(slot&&slot.indexH,10);
  if(h>40)document.body.style.setProperty('--sides-index-h',h+'px');
}
function ensureIndexHeightHandle(){
  var ix=document.getElementById('catalogIndex');
  if(!ix)return null;
  var h=document.getElementById('indexHeight');
  if(!h){
    h=document.createElement('button');
    h.type='button';
    h.id='indexHeight';
    h.className='index-height';
    h.setAttribute('aria-label','Drag the bottom edge to resize Index height');
    h.setAttribute('aria-orientation','horizontal');
    h.tabIndex=-1;
    ix.appendChild(h);
  }
  return h;
}
function bindIndexHeight(){
  var h=ensureIndexHeightHandle();
  if(!h||h.dataset.indexHBound)return;
  h.dataset.indexHBound='1';
  var drag=null;
  h.addEventListener('pointerdown',function(e){
    if(!document.body.classList.contains('display-sides'))return;
    if(!document.body.classList.contains('layout-edit'))return;
    if(sidesPinned||(typeof modeLayoutPinned==='function'&&modeLayoutPinned()))return;
    if(e.pointerType==='mouse'&&e.button!=null&&e.button!==0)return;
    e.preventDefault();e.stopPropagation();
    var ix=document.getElementById('catalogIndex');
    if(!ix||ix.classList.contains('is-collapsed'))return;
    var cur=Math.round(ix.getBoundingClientRect().height);
    drag={y:e.clientY,h:cur,id:e.pointerId};
    try{h.setPointerCapture(e.pointerId);}catch(err){}
    if(typeof logSidesEdit==='function')logSidesEdit('H2','indexHeight','pointerdown',{h:cur});
  });
  function move(e){
    if(!drag)return;
    var max=Math.round(Math.min(window.innerHeight*0.7,640));
    var nh=Math.max(72,Math.min(max,drag.h+(e.clientY-drag.y)));
    document.body.style.setProperty('--sides-index-h',nh+'px');
  }
  function up(e){
    if(!drag)return;
    var nh=parseInt(getComputedStyle(document.body).getPropertyValue('--sides-index-h'),10)||0;
    drag=null;
    if(nh>40&&typeof writeModeSlot==='function')writeModeSlot({indexH:nh},'sides');
    if(typeof logSidesEdit==='function')logSidesEdit('H2','indexHeight','pointerup',{indexH:nh});
  }
  document.addEventListener('pointermove',move);
  document.addEventListener('pointerup',up);
  document.addEventListener('pointercancel',up);
}
window.applySidesIndexH=applySidesIndexH;
window.ensureIndexHeightHandle=ensureIndexHeightHandle;
window.bindIndexHeight=bindIndexHeight;
"""

add(
    "})();\n"
    "function logSidesGeom(tag){\n",
    "})();\n" + INDEX_JS + "function logSidesGeom(tag){\n",
    "index-js",
)

# --- Lock helper + Customize wiring ---
LOCK_JS = r"""
function syncModeLockBtn(){
  var on=typeof modeLayoutPinned==='function'&&modeLayoutPinned();
  var b=document.getElementById('modePinBtn');
  if(b){
    b.textContent=on?'Unlock':'Lock';
    b.title=on?'Unlock this display mode to resize again':'Lock current sizes for this display mode';
    b.setAttribute('aria-label',b.title);
    b.setAttribute('aria-pressed',on?'true':'false');
  }
  ['dualFsSepPin','fsSepPinBtn'].forEach(function(id){var el=document.getElementById(id);if(el){el.hidden=true;el.setAttribute('aria-hidden','true');}});
}
function toggleModeLock(){
  var on=!modeLayoutPinned();
  if(on&&typeof snapshotLiveToMode==='function')snapshotLiveToMode();
  writeModeSlot({pinned:on});
  if(displayModeSlot()==='sides'){
    sidesPinned=on;
    try{localStorage.setItem(SIDES_KEY+'-pin',on?'1':'0');}catch(err){}
    if(typeof syncSidesPin==='function')syncSidesPin();
  }
  document.body.classList.toggle('mode-layout-pinned',on);
  syncModeLockBtn();
  if(typeof placeSidesHandles==='function')placeSidesHandles();
  if(typeof logSidesEdit==='function')logSidesEdit('H3','toggleModeLock','lock-click',{on:on,slot:typeof displayModeSlot==='function'?displayModeSlot():''});
  if(typeof logPickLock==='function')logPickLock('toggleModeLock','lock-click','H3',{on:on,slot:typeof displayModeSlot==='function'?displayModeSlot():'',store:typeof readModeSlot==='function'?readModeSlot():null});
}
window.syncModeLockBtn=syncModeLockBtn;
window.toggleModeLock=toggleModeLock;
"""

add(
    "window.logLayoutModes=logLayoutModes;\n",
    "window.logLayoutModes=logLayoutModes;\n" + LOG_HELPER + LOCK_JS,
    "log-lock-helpers",
)

# --- ensureLayoutChromeBtns: Lock not pin emoji ---
add(
    "function ensureLayoutChromeBtns(){\n"
    "  var top=document.getElementById('filterTop');\n"
    "  if(!top)return;\n"
    "  var edit=document.getElementById('layoutEditBtn');\n"
    "  if(edit&&!top.contains(edit))top.appendChild(edit);\n"
    "  if(!document.getElementById('modePinBtn')){\n"
    "    var b=document.createElement('button');\n"
    "    b.type='button';\n"
    "    b.id='modePinBtn';\n"
    "    b.className='layout-edit-btn mode-pin-btn';\n"
    "    b.title='Lock this display-mode size';\n"
    "    b.setAttribute('aria-label','Lock this display-mode size');\n"
    "    b.textContent='📌';\n"
    "    b.addEventListener('click',function(e){\n"
    "      e.preventDefault();e.stopPropagation();\n"
    "      var on=!modeLayoutPinned();\n"
    "      if(on&&typeof snapshotLiveToMode==='function')snapshotLiveToMode();\n"
    "      writeModeSlot({pinned:on});\n"
    "      if(typeof logPickLock==='function')logPickLock('modePinBtn','pin-click','H4',{on:on,slot:typeof displayModeSlot==='function'?displayModeSlot():'',store:typeof readModeSlot==='function'?readModeSlot():null});\n"
    "      if(displayModeSlot()==='sides'){\n"
    "        sidesPinned=on;\n"
    "        try{localStorage.setItem(SIDES_KEY+'-pin',on?'1':'0');}catch(err){}\n"
    "        if(typeof syncSidesPin==='function')syncSidesPin();\n"
    "      }\n"
    "      document.body.classList.toggle('mode-layout-pinned',on);\n"
    "      b.setAttribute('aria-pressed',on?'true':'false');\n"
    "      if(typeof logLayoutModes==='function')logLayoutModes('mode-pin');\n"
    "    });\n"
    "    top.appendChild(b);\n"
    "  }\n"
    "}\n",
    "function ensureLayoutChromeBtns(){\n"
    "  var top=document.getElementById('filterTop');\n"
    "  if(!top)return;\n"
    "  var edit=document.getElementById('layoutEditBtn');\n"
    "  if(edit&&!top.contains(edit))top.appendChild(edit);\n"
    "  var b=document.getElementById('modePinBtn');\n"
    "  if(!b){\n"
    "    b=document.createElement('button');\n"
    "    b.type='button';\n"
    "    b.id='modePinBtn';\n"
    "    b.className='layout-edit-btn mode-pin-btn';\n"
    "    b.addEventListener('click',function(e){\n"
    "      e.preventDefault();e.stopPropagation();\n"
    "      if(typeof toggleModeLock==='function')toggleModeLock();\n"
    "    });\n"
    "    top.appendChild(b);\n"
    "  }\n"
    "  if(typeof syncLayoutEditBtn==='function')syncLayoutEditBtn();\n"
    "  if(typeof syncModeLockBtn==='function')syncModeLockBtn();\n"
    "}\n",
    "ensure-lock-btn",
)

# --- dual pin → one Lock ---
DUAL_PIN_CORE = (
    "  if(document.body.classList.contains('display-sides')){\n"
    "    sidesPinned=!sidesPinned;\n"
    "    try{localStorage.setItem(SIDES_KEY+'-pin',sidesPinned?'1':'0');}catch(err){}\n"
    "    if(sidesPinned&&typeof snapshotLiveToMode==='function')snapshotLiveToMode('sides');\n"
    "    if(typeof writeModeSlot==='function')writeModeSlot({pinned:!!sidesPinned},'sides');\n"
    "    if(typeof logPickLock==='function')logPickLock('toggleDualFsPin','sides-pin','H4',{on:!!sidesPinned,store:typeof readModeSlot==='function'?readModeSlot('sides'):null});\n"
    "    syncSidesPin();\n"
)
add(
    (
        DUAL_PIN_CORE
        + "    // #region agent log\n"
        + "    fetch('http://127.0.0.1:7529/ingest/1cf46354-1d61-4c80-bd72-a340f1db1b51',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'f491c2'},body:JSON.stringify({sessionId:'f491c2',runId:'post-fix',hypothesisId:'H6',location:'toggleDualFsPin',message:'sides-pin',data:{pinned:sidesPinned},timestamp:Date.now()})}).catch(function(){});\n"
        + "    // #endregion\n"
        + "    return;\n"
        + "  }\n",
        DUAL_PIN_CORE + "    return;\n  }\n",
    ),
    "  if(document.body.classList.contains('display-sides')){\n"
    "    if(typeof toggleModeLock==='function')toggleModeLock();\n"
    "    return;\n"
    "  }\n",
    "dual-pin-merge",
)

# --- setDisplayMode: re-click Sides restores Search ---
add(
    "  if(mode==='sides'&&!displayIsDesktop())mode='fs';\n"
    "  var prev=typeof currentDisplay!=='undefined'?currentDisplay:'';\n",
    "  if(mode==='sides'&&!displayIsDesktop())mode='fs';\n"
    "  var prev=typeof currentDisplay!=='undefined'?currentDisplay:'';\n"
    "  var already=prev===mode;\n"
    "  if(mode==='sides'){\n"
    "    var wasCol=document.body.classList.contains('search-chrome-collapsed');\n"
    "    document.body.classList.remove('search-chrome-collapsed','search-extras-collapsed');\n"
    "    if(typeof syncSearchHideBtn==='function')syncSearchHideBtn();\n"
    "    if(typeof logSidesEdit==='function')logSidesEdit('H5','setDisplayMode','sides-reclick',{already:already,wasCol:wasCol});\n"
    "  }\n",
    "sides-reclick",
)

# --- setDisplayMode sides: bind index handle ---
add(
    "    if(typeof bindIndexDock==='function')bindIndexDock();\n"
    "    if(typeof bindCatalogTop==='function')bindCatalogTop();\n",
    "    if(typeof bindIndexDock==='function')bindIndexDock();\n"
    "    if(typeof bindIndexHeight==='function')bindIndexHeight();\n"
    "    if(typeof bindCatalogTop==='function')bindCatalogTop();\n",
    "bind-index-h",
)

# --- toggleLayoutEdit: keep existing + bind index + log ---
add(
    "  if(typeof placeSidesHandles==='function')placeSidesHandles();\n"
    "  if(typeof logPickLock==='function')logPickLock('toggleLayoutEdit','edit-toggle','H3',{on:document.body.classList.contains('layout-edit'),handles:typeof handleSnap==='function'?handleSnap():null});\n"
    "}\n",
    "  if(typeof placeSidesHandles==='function')placeSidesHandles();\n"
    "  if(typeof bindIndexHeight==='function')bindIndexHeight();\n"
    "  if(typeof logPickLock==='function')logPickLock('toggleLayoutEdit','edit-toggle','H3',{on:document.body.classList.contains('layout-edit'),handles:typeof handleSnap==='function'?handleSnap():null});\n"
    "  if(typeof logSidesEdit==='function')logSidesEdit('H3','toggleLayoutEdit','customize-toggle',{on:document.body.classList.contains('layout-edit')});\n"
    "}\n",
    "edit-toggle-log",
)
add(
    "width:12px;height:auto;z-index:80;margin:0;transform:none;pointer-events:auto;",
    "width:12px;min-width:12px;max-width:12px;height:auto;z-index:80;margin:0;transform:none;pointer-events:auto;",
    "place-handle-hit",
    replace_all=True,
)


def must_replace(text, olds, new, label, optional=False, replace_all=False):
    if new in text:
        print(f"  skip {label} (already)")
        return text
    if any(o in text for o in olds):
        for old in olds:
            if old not in text:
                continue
            n = text.count(old)
            if replace_all or n != 1:
                if n != 1:
                    print(f"  warn {label} count={n}, replacing all")
                return text.replace(old, new)
            return text.replace(old, new, 1)
    if new in text:
        print(f"  skip {label} (already)")
        return text
    if optional:
        print(f"  skip {label} (optional-missing)")
        return text
    raise SystemExit(f"MISSING [{label}]")


def assert_common(text, name):
    if "function hideSearchAc" not in text:
        raise SystemExit(f"{name} missing function hideSearchAc")
    if "function logSidesEdit" not in text:
        raise SystemExit(f"{name} missing logSidesEdit")
    if "function toggleModeLock" not in text:
        raise SystemExit(f"{name} missing toggleModeLock")
    if "function bindIndexHeight" not in text:
        raise SystemExit(f"{name} missing bindIndexHeight")
    if "grid-template-columns:0 minmax(0,1fr) var(--sides-rw,26vw)" not in text:
        raise SystemExit(f"{name} missing sides hide grid")
    if "min-width:12px!important;max-width:12px!important" not in text:
        raise SystemExit(f"{name} missing handle hit target")
    if "--sides-index-h" not in text:
        raise SystemExit(f"{name} missing index height var")
    if "b.textContent=on?'Done':'Customize'" not in text:
        raise SystemExit(f"{name} missing Customize label")
    if ">Customize</button>" not in text:
        raise SystemExit(f"{name} missing Customize button html")
    if "b.textContent=on?'Unlock':'Lock'" not in text:
        raise SystemExit(f"{name} missing Lock label")
    if "runId:'sides-edit'" not in text:
        raise SystemExit(f"{name} missing sides-edit logs")
    if ">Pick</button>" not in text:
        raise SystemExit(f"{name} lost Pick")
    if "function hideSearchAc" not in text:
        raise SystemExit(f"{name} lost hideSearchAc")


def assert_html(text, name):
    assert_common(text, name)
    if "</html>" not in text:
        raise SystemExit(f"{name} missing </html>")


def patch(text, name):
    for old, new, label, optional, replace_all in REPLACEMENTS:
        text = must_replace(text, old, new, f"{name}:{label}", optional=optional, replace_all=replace_all)
    return text


def main():
    for name in ("build-ds-catalog-html.sh", "build-kontakt-catalog-html.sh"):
        src = KIRO / name
        raw = src.read_text(encoding="utf-8")
        out = patch(raw, f"KIRO/{name}")
        assert_common(out, f"KIRO/{name}")
        src.write_text(out, encoding="utf-8")
        WS.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, WS / name)
        print("patched+copied", name, len(out))

    htmls = [
        PUB / "DS-CATALOG.html",
        PUB / "DS-CATALOG-portable.html",
        PUB / "KONTAKT-CATALOG.html",
        PUB / "KONTAKT-CATALOG-portable.html",
        WS / "DS-CATALOG.html",
        WS / "DS-CATALOG-portable.html",
        WS / "KONTAKT-CATALOG.html",
        WS / "KONTAKT-CATALOG-portable.html",
    ]
    for path in htmls:
        if not path.exists():
            print("skip missing", path)
            continue
        raw = path.read_text(encoding="utf-8")
        out = patch(raw, path.name)
        assert_html(out, path.name)
        path.write_text(out, encoding="utf-8")
        print("patched", path.name, len(out))


if __name__ == "__main__":
    main()
