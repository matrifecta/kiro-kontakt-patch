#!/usr/bin/env python3
"""Sides restore: full Keywords hide, Sides-button restore, Index dock unstick.

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
function logSidesRestore(hid,loc,msg,extra){
  // #region agent log
  try{
    extra=extra||{};
    function box(el){if(!el)return null;var b=el.getBoundingClientRect();return{x:Math.round(b.x),y:Math.round(b.y),w:Math.round(b.width),h:Math.round(b.height)};}
    var fw=document.getElementById('filterWrap');
    var ch=document.getElementById('searchChrome');
    var ix=document.getElementById('catalogIndex');
    var il=document.getElementById('catalogIndexList')||(ix&&ix.querySelector('ul.index'));
    var chip=document.getElementById('filterToggle');
    var hide=document.getElementById('kwStripHide');
    extra.display=typeof currentDisplay!=='undefined'?currentDisplay:'';
    extra.searchCol=document.body.classList.contains('search-chrome-collapsed');
    extra.kwHid=document.body.classList.contains('kw-chrome-collapsed');
    extra.kwOpen=document.body.classList.contains('kw-open');
    extra.rw=(getComputedStyle(document.body).getPropertyValue('--sides-rw')||'').trim();
    extra.lw=(getComputedStyle(document.body).getPropertyValue('--sides-lw')||'').trim();
    extra.fw=fw?{disp:getComputedStyle(fw).display,w:Math.round(fw.getBoundingClientRect().width),box:box(fw)}:null;
    extra.ch=ch?{disp:getComputedStyle(ch).display,w:Math.round(ch.getBoundingClientRect().width)}:null;
    extra.chip=chip?{disp:getComputedStyle(chip).display,box:box(chip),txt:chip.textContent}:null;
    extra.hideBtn=hide?{disp:getComputedStyle(hide).display,txt:hide.textContent}:null;
    extra.ix=ix?{box:box(ix),col:ix.classList.contains('is-collapsed'),auto:ix.dataset.dockAuto||'',pin:ix.dataset.dockPin||''}:null;
    if(il){
      var last=il.querySelector('li:last-child');
      var cs=getComputedStyle(il);
      extra.il={sh:il.scrollHeight,ch:il.clientHeight,st:Math.round(il.scrollTop),ov:cs.overflowY,cols:cs.columnCount+'/'+cs.columnWidth,sideways:cs.columnCount!=='auto'&&cs.columnCount!=='1'&&cs.columns!=='none'};
      extra.lastLi=last?box(last):null;
    }
    fetch('""" + INGEST + r"""',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'f491c2'},body:JSON.stringify({sessionId:'f491c2',runId:'sides-restore',hypothesisId:hid,location:loc,message:msg,data:extra,timestamp:Date.now()})}).catch(function(){});
  }catch(err){}
  // #endregion
}
window.logSidesRestore=logSidesRestore;
"""

# --- CSS: Hide Keywords control (mirror Hide search) ---
add(
    " .search-strip-hide:hover{color:var(--accent-instrument);border-color:var(--accent-instrument)}\n",
    " .search-strip-hide:hover{color:var(--accent-instrument);border-color:var(--accent-instrument)}\n"
    " .kw-strip-hide{flex-shrink:0;background:transparent;border:1px solid var(--border);color:var(--text-muted);border-radius:4px;padding:6px 12px;font-size:.9375rem;cursor:pointer;min-height:2.75rem;touch-action:manipulation;white-space:nowrap}\n"
    " .kw-strip-hide:hover{color:var(--accent-instrument);border-color:var(--accent-instrument)}\n"
    " body:not(.display-sides) .kw-strip-hide{display:none!important}\n",
    "kw-hide-btn-css",
)

# --- CSS: sides grid when Keywords fully hidden ---
add(
    "  body.display-sides.search-chrome-collapsed{grid-template-columns:0 minmax(0,1fr) var(--sides-rw,26vw)}\n",
    "  body.display-sides.search-chrome-collapsed{grid-template-columns:0 minmax(0,1fr) var(--sides-rw,26vw)}\n"
    "  body.display-sides.kw-chrome-collapsed{grid-template-columns:var(--sides-lw,22vw) minmax(0,1fr) 0}\n"
    "  body.display-sides.search-chrome-collapsed.kw-chrome-collapsed{grid-template-columns:0 minmax(0,1fr) 0}\n",
    "sides-kw-hide-grid",
)
add(
    "  body.display-sides.search-chrome-collapsed #searchSplit{display:none!important}\n",
    "  body.display-sides.search-chrome-collapsed #searchSplit{display:none!important}\n"
    "  body.display-sides.kw-chrome-collapsed #filterWrap{display:none!important;width:0!important;min-width:0!important;max-width:0!important;overflow:hidden!important;border:0!important;padding:0!important;height:0!important}\n"
    "  body.display-sides.kw-chrome-collapsed .kw-strip-hide,body.display-sides.kw-chrome-collapsed #filterWrap .filter-top,body.display-sides.kw-chrome-collapsed .filter-toggle{display:none!important}\n"
    "  body.display-sides.kw-chrome-collapsed #dualFsSep{display:none!important}\n",
    "sides-kw-hide-wrap",
)
add(
    "  body.display-sides.search-chrome-collapsed.layout-edit #searchSplit{display:none!important}\n",
    "  body.display-sides.search-chrome-collapsed.layout-edit #searchSplit{display:none!important}\n"
    "  body.display-sides.kw-chrome-collapsed.layout-edit #dualFsSep{display:none!important}\n",
    "sides-kw-hide-sep-edit",
)

# --- leftover Keywords chip must not win over full hide ---
add(
    " body.display-sides:not(.kw-open){grid-template-columns:var(--sides-lw,22vw) minmax(0,1fr) max-content}\n"
    " body.display-sides.search-chrome-collapsed:not(.kw-open){grid-template-columns:0 minmax(0,1fr) max-content}\n"
    " body.display-sides:not(.kw-open) #filterWrap{width:auto!important;min-width:0;height:auto!important;max-height:none!important;align-self:start;overflow:visible}\n",
    " body.display-sides:not(.kw-open):not(.kw-chrome-collapsed){grid-template-columns:var(--sides-lw,22vw) minmax(0,1fr) max-content}\n"
    " body.display-sides.search-chrome-collapsed:not(.kw-open):not(.kw-chrome-collapsed){grid-template-columns:0 minmax(0,1fr) max-content}\n"
    " body.display-sides:not(.kw-open):not(.kw-chrome-collapsed) #filterWrap{width:auto!important;min-width:0;height:auto!important;max-height:none!important;align-self:start;overflow:visible}\n"
    " body.display-sides.kw-chrome-collapsed{grid-template-columns:var(--sides-lw,22vw) minmax(0,1fr) 0}\n"
    " body.display-sides.search-chrome-collapsed.kw-chrome-collapsed{grid-template-columns:0 minmax(0,1fr) 0}\n"
    " body.display-sides.kw-chrome-collapsed #filterWrap{display:none!important;width:0!important;min-width:0!important;max-width:0!important;overflow:hidden!important;border:0!important;padding:0!important;height:0!important}\n",
    "sides-kw-chip-override",
)

# --- Hide Keywords button in filter-top ---
add(
    '<button class="filter-toggle" id="filterToggle" onclick="toggleFilter()" aria-expanded="false"><span class="toggle-arrow">&#9660;</span> Keywords</button>',
    '<button class="filter-toggle" id="filterToggle" onclick="toggleFilter()" aria-expanded="false"><span class="toggle-arrow">&#9660;</span> Keywords</button>'
    '<button type="button" class="kw-strip-hide" id="kwStripHide" onclick="event.preventDefault();event.stopPropagation();toggleKwChrome()" aria-expanded="true">Hide Keywords</button>',
    "kw-hide-btn-html",
)

# --- JS: hide/restore Keywords + index reset ---
add(
    "function toggleSearchChrome(){\n"
    "  if(document.body.classList.contains('search-chrome-collapsed')) expandSearchMenu();\n"
    "  else collapseSearchMenu();\n"
    "}\n",
    "function toggleSearchChrome(){\n"
    "  if(document.body.classList.contains('search-chrome-collapsed')) expandSearchMenu();\n"
    "  else collapseSearchMenu();\n"
    "}\n"
    + LOG_HELPER
    + "function syncKwHideBtn(){\n"
    "  var hidden=document.body.classList.contains('kw-chrome-collapsed');\n"
    "  document.querySelectorAll('.kw-strip-hide').forEach(function(b){\n"
    "    b.textContent=hidden?'Keywords':'Hide Keywords';\n"
    "    b.setAttribute('aria-expanded',hidden?'false':'true');\n"
    "    b.setAttribute('aria-label',hidden?'Keywords':'Hide Keywords');\n"
    "  });\n"
    "}\n"
    "function collapseKwMenu(){\n"
    "  var w=document.getElementById('filterWrap');\n"
    "  if(w)w.classList.remove('open');\n"
    "  document.body.classList.remove('kw-open');\n"
    "  document.body.classList.add('kw-chrome-collapsed');\n"
    "  if(typeof kwFsWanted!=='undefined')kwFsWanted=false;\n"
    "  document.body.classList.remove('kw-fs-open');\n"
    "  if(typeof syncKwHideBtn==='function')syncKwHideBtn();\n"
    "  if(typeof syncSearchHideBtn==='function')syncSearchHideBtn();\n"
    "  if(typeof applySidesCols==='function')applySidesCols();\n"
    "  if(typeof logSidesRestore==='function')logSidesRestore('H1','collapseKwMenu','hide-kw',{});\n"
    "}\n"
    "function expandKwMenu(){\n"
    "  document.body.classList.remove('kw-chrome-collapsed');\n"
    "  var w=document.getElementById('filterWrap');\n"
    "  if(w)w.classList.add('open');\n"
    "  document.body.classList.add('kw-open');\n"
    "  var a=document.querySelector('#filterToggle .toggle-arrow')||document.querySelector('.toggle-arrow');\n"
    "  if(a)a.textContent='▲';\n"
    "  if(typeof syncKwHideBtn==='function')syncKwHideBtn();\n"
    "  if(typeof syncSearchHideBtn==='function')syncSearchHideBtn();\n"
    "  if(typeof applySidesCols==='function')applySidesCols();\n"
    "  if(typeof window.restoreFilterUi==='function')window.restoreFilterUi();\n"
    "}\n"
    "function toggleKwChrome(){\n"
    "  if(!document.body.classList.contains('display-sides')){\n"
    "    if(typeof toggleFilter==='function')toggleFilter();\n"
    "    return;\n"
    "  }\n"
    "  if(document.body.classList.contains('kw-chrome-collapsed')) expandKwMenu();\n"
    "  else collapseKwMenu();\n"
    "}\n"
    "function resetIndexDock(){\n"
    "  var ix=document.getElementById('catalogIndex');\n"
    "  var il=document.getElementById('catalogIndexList')||(ix&&ix.querySelector('ul.index'));\n"
    "  if(!ix)return;\n"
    "  ix.classList.remove('is-collapsed');\n"
    "  ix.dataset.dockAuto='';\n"
    "  ix.dataset.dockPin='';\n"
    "  ix.dataset.goingTop='';\n"
    "  try{delete ix.dataset.ixFitInner;}catch(err){ix.dataset.ixFitInner='';}\n"
    "  if(typeof syncIndexToggleUi==='function')syncIndexToggleUi(ix);\n"
    "  if(il)il.scrollTop=0;\n"
    "  var cm=document.getElementById('catalogMain');\n"
    "  if(cm)cm.scrollTop=0;\n"
    "  if(typeof applyIndexScrollFit==='function')applyIndexScrollFit();\n"
    "  if(typeof logSidesRestore==='function')logSidesRestore('H4','resetIndexDock','index-reset',{});\n"
    "}\n"
    "window.syncKwHideBtn=syncKwHideBtn;\n"
    "window.collapseKwMenu=collapseKwMenu;\n"
    "window.expandKwMenu=expandKwMenu;\n"
    "window.toggleKwChrome=toggleKwChrome;\n"
    "window.resetIndexDock=resetIndexDock;\n",
    "kw-hide-js",
)

# --- applySidesCols: --sides-rw 0 when Keywords fully hidden; clear class on leave ---
add(
    "    document.body.style.removeProperty('--sides-lw');\n"
    "    document.body.style.removeProperty('--sides-rw');\n"
    "    document.body.style.removeProperty('--sides-index-h');\n",
    "    document.body.style.removeProperty('--sides-lw');\n"
    "    document.body.style.removeProperty('--sides-rw');\n"
    "    document.body.style.removeProperty('--sides-index-h');\n"
    "    document.body.classList.remove('kw-chrome-collapsed');\n",
    "leave-sides-kw",
)
add(
    "  if(!document.body.classList.contains('kw-open')){\n"
    "    document.body.style.removeProperty('--sides-rw');\n",
    "  if(document.body.classList.contains('kw-chrome-collapsed')){\n"
    "    document.body.style.setProperty('--sides-rw','0px');\n"
    "  }else if(!document.body.classList.contains('kw-open')){\n"
    "    document.body.style.removeProperty('--sides-rw');\n",
    "sides-rw-zero",
)

# --- placeSidesHandles: skip Keywords sep when hidden ---
add(
    "  var hidden=document.body.classList.contains('search-chrome-collapsed');\n"
    "  var editing=document.body.classList.contains('layout-edit');\n"
    "  if(split&&ch&&!hidden&&editing){\n",
    "  var hidden=document.body.classList.contains('search-chrome-collapsed');\n"
    "  var kwHid=document.body.classList.contains('kw-chrome-collapsed');\n"
    "  var editing=document.body.classList.contains('layout-edit');\n"
    "  if(split&&ch&&!hidden&&editing){\n",
    "place-kwhid",
)
add(
    "  if(sep&&fw&&editing){\n",
    "  if(sep&&fw&&editing&&!kwHid){\n",
    "place-sep-kwhid",
)

# --- setDisplayMode: Sides click restores Search + Keywords + Index ---
add(
    "  if(mode==='sides'){\n"
    "    var wasCol=document.body.classList.contains('search-chrome-collapsed');\n"
    "    document.body.classList.remove('search-chrome-collapsed','search-extras-collapsed');\n"
    "    if(typeof syncSearchHideBtn==='function')syncSearchHideBtn();\n"
    "    if(typeof logSidesEdit==='function')logSidesEdit('H5','setDisplayMode','sides-reclick',{already:already,wasCol:wasCol});\n"
    "  }\n",
    "  if(mode==='sides'){\n"
    "    var wasCol=document.body.classList.contains('search-chrome-collapsed');\n"
    "    var wasKw=document.body.classList.contains('kw-chrome-collapsed');\n"
    "    var ixPre=document.getElementById('catalogIndex');\n"
    "    var ilPre=document.getElementById('catalogIndexList');\n"
    "    document.body.classList.remove('search-chrome-collapsed','search-extras-collapsed','kw-chrome-collapsed');\n"
    "    var fwPre=document.getElementById('filterWrap');\n"
    "    if(fwPre){fwPre.classList.add('open');document.body.classList.add('kw-open');}\n"
    "    var aPre=document.querySelector('#filterToggle .toggle-arrow')||document.querySelector('.toggle-arrow');\n"
    "    if(aPre)aPre.textContent='▲';\n"
    "    if(typeof syncSearchHideBtn==='function')syncSearchHideBtn();\n"
    "    if(typeof syncKwHideBtn==='function')syncKwHideBtn();\n"
    "    if(typeof resetIndexDock==='function')resetIndexDock();\n"
    "    if(typeof logSidesRestore==='function')logSidesRestore('H2','setDisplayMode','sides-already',{already:already,wasCol:wasCol,wasKw:wasKw,ixCol:!!(ixPre&&ixPre.classList.contains('is-collapsed')),ilSH:ilPre?ilPre.scrollHeight:null,ilCH:ilPre?ilPre.clientHeight:null});\n"
    "  }else{\n"
    "    document.body.classList.remove('kw-chrome-collapsed');\n"
    "  }\n",
    "sides-reclick-both",
)

# --- Index: no auto-collapse on catalog scroll ---
add(
    "function syncIndexDock(){\n"
    "  var ix=document.getElementById('catalogIndex');\n"
    "  var cm=document.getElementById('catalogMain');\n"
    "  if(!ix||!cm)return;\n"
    "  if(!document.body.classList.contains('display-sides')){\n"
    "    ix.dataset.dockAuto='';\n"
    "    return;\n"
    "  }\n"
    "  var y=cm.scrollTop;\n"
    "  var before=ix.classList.contains('is-collapsed')+'|'+(ix.dataset.dockAuto||'')+'|'+(ix.dataset.dockPin||'');\n"
    "  if(ix.dataset.goingTop==='1'){\n"
    "    if(y<=12)ix.dataset.goingTop='';\n"
    "    else return;\n"
    "  }\n"
    "  if(y<=12){\n"
    "    if(ix.dataset.dockAuto==='1'){\n"
    "      ix.classList.remove('is-collapsed');\n"
    "      ix.dataset.dockAuto='';\n"
    "      syncIndexToggleUi(ix);\n"
    "    }\n"
    "  }else if(y>48&&!ix.classList.contains('is-collapsed')&&ix.dataset.dockPin!=='1'){\n"
    "    ix.classList.add('is-collapsed');\n"
    "    ix.dataset.dockAuto='1';\n"
    "    syncIndexToggleUi(ix);\n"
    "  }\n"
    "  var after=ix.classList.contains('is-collapsed')+'|'+(ix.dataset.dockAuto||'')+'|'+(ix.dataset.dockPin||'');\n"
    "  // #region agent log\n"
    "  if(before!==after)fetch('http://127.0.0.1:7529/ingest/1cf46354-1d61-4c80-bd72-a340f1db1b51',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'f491c2'},body:JSON.stringify({sessionId:'f491c2',runId:'post-fix',hypothesisId:'H6',location:'syncIndexDock',message:'index-dock',data:{y:Math.round(y),collapsed:ix.classList.contains('is-collapsed'),auto:ix.dataset.dockAuto||'',pin:ix.dataset.dockPin||'',ixH:Math.round(ix.getBoundingClientRect().height)},timestamp:Date.now()})}).catch(function(){});\n"
    "  // #endregion\n"
    "}\n",
    "function syncIndexDock(){\n"
    "  var ix=document.getElementById('catalogIndex');\n"
    "  var cm=document.getElementById('catalogMain');\n"
    "  if(!ix||!cm)return;\n"
    "  if(!document.body.classList.contains('display-sides')){\n"
    "    ix.dataset.dockAuto='';\n"
    "    return;\n"
    "  }\n"
    "  if(ix.dataset.goingTop==='1'&&cm.scrollTop<=12)ix.dataset.goingTop='';\n"
    "}\n",
    "index-no-autodock",
)
add(
    "      if(typeof toggleCatalogIndex==='function')toggleCatalogIndex();\n"
    "    });\n"
    "  }\n"
    "  syncIndexDock();\n"
    "}\n",
    "      if(typeof toggleCatalogIndex==='function')toggleCatalogIndex();\n"
    "    });\n"
    "  }\n"
    "}\n",
    "bind-dock-nofit",
)

# --- applyIndexScrollFit: no re-entry / no same-height loop ---
add(
    "function applyIndexScrollFit(){\n"
    "  var ix=document.getElementById('catalogIndex');\n"
    "  var il=document.getElementById('catalogIndexList')||(ix&&ix.querySelector('ul.index'));\n"
    "  if(!ix||!il)return;\n"
    "  if(!document.body.classList.contains('display-sides')||ix.classList.contains('is-collapsed')){\n"
    "    il.style.removeProperty('height');\n"
    "    il.style.removeProperty('max-height');\n"
    "    return;\n"
    "  }\n"
    "  var head=ix.querySelector('.catalog-index-head');\n"
    "  var hh=head?Math.round(head.getBoundingClientRect().height):0;\n"
    "  var inner=Math.max(48,Math.round(ix.clientHeight-hh));\n"
    "  il.style.setProperty('columns','unset','important');\n"
    "  il.style.setProperty('column-width','unset','important');\n"
    "  il.style.setProperty('column-count','unset','important');\n"
    "  il.style.setProperty('column-fill','unset','important');\n"
    "  il.style.height=inner+'px';\n"
    "  il.style.maxHeight=inner+'px';\n",
    "function applyIndexScrollFit(){\n"
    "  var ix=document.getElementById('catalogIndex');\n"
    "  var il=document.getElementById('catalogIndexList')||(ix&&ix.querySelector('ul.index'));\n"
    "  if(!ix||!il)return;\n"
    "  if(ix.dataset.ixFitting==='1')return;\n"
    "  if(!document.body.classList.contains('display-sides')||ix.classList.contains('is-collapsed')){\n"
    "    il.style.removeProperty('height');\n"
    "    il.style.removeProperty('max-height');\n"
    "    try{delete ix.dataset.ixFitInner;}catch(err){ix.dataset.ixFitInner='';}\n"
    "    return;\n"
    "  }\n"
    "  var head=ix.querySelector('.catalog-index-head');\n"
    "  var hh=head?Math.round(head.getBoundingClientRect().height):0;\n"
    "  var inner=Math.max(48,Math.round(ix.clientHeight-hh));\n"
    "  if((ix.dataset.ixFitInner||'')===String(inner)&&il.style.height===inner+'px')return;\n"
    "  ix.dataset.ixFitting='1';\n"
    "  il.style.setProperty('columns','unset','important');\n"
    "  il.style.setProperty('column-width','unset','important');\n"
    "  il.style.setProperty('column-count','unset','important');\n"
    "  il.style.setProperty('column-fill','unset','important');\n"
    "  il.style.height=inner+'px';\n"
    "  il.style.maxHeight=inner+'px';\n"
    "  ix.dataset.ixFitInner=String(inner);\n",
    "ixfit-guard",
)
add(
    "  if(typeof logNestFix==='function')logNestFix('H6','applyIndexScrollFit','index-fit',{inner:inner,hh:hh,ixH:Math.round(ix.clientHeight)});\n"
    "}\n",
    "  ix.dataset.ixFitting='';\n"
    "  if(typeof logNestFix==='function')logNestFix('H6','applyIndexScrollFit','index-fit',{inner:inner,hh:hh,ixH:Math.round(ix.clientHeight)});\n"
    "  if(typeof logSidesRestore==='function')logSidesRestore('H3','applyIndexScrollFit','index-fit',{inner:inner,hh:hh,ixH:Math.round(ix.clientHeight)});\n"
    "}\n",
    "ixfit-log-restore",
)

# --- Sides Keywords toggle = full hide (no leftover chip) ---
add(
    "  var _tf=window.toggleFilter;\n"
    "  if(typeof _tf==='function'){\n"
    "    window.toggleFilter=function(){ _tf.apply(this,arguments); if(typeof applySidesCols==='function')applySidesCols(); };\n"
    "  }\n",
    "  var _tf=window.toggleFilter;\n"
    "  if(typeof _tf==='function'){\n"
    "    window.toggleFilter=function(){\n"
    "      var w=document.getElementById('filterWrap');\n"
    "      if(document.body.classList.contains('display-sides')&&document.body.classList.contains('kw-chrome-collapsed')){\n"
    "        if(typeof expandKwMenu==='function'){expandKwMenu();return;}\n"
    "      }\n"
    "      if(document.body.classList.contains('display-sides')&&w&&w.classList.contains('open')&&!document.body.classList.contains('kw-fs-open')){\n"
    "        if(typeof collapseKwMenu==='function'){collapseKwMenu();return;}\n"
    "      }\n"
    "      _tf.apply(this,arguments);\n"
    "      if(typeof applySidesCols==='function')applySidesCols();\n"
    "    };\n"
    "  }\n",
    "toggle-filter-sides-hide",
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
    if optional:
        print(f"  skip {label} (optional-missing)")
        return text
    raise SystemExit(f"MISSING [{label}]")


def assert_common(text, name):
    if "function hideSearchAc" not in text:
        raise SystemExit(f"{name} missing function hideSearchAc")
    if "function collapseKwMenu" not in text:
        raise SystemExit(f"{name} missing collapseKwMenu")
    if "function resetIndexDock" not in text:
        raise SystemExit(f"{name} missing resetIndexDock")
    if "kw-chrome-collapsed" not in text:
        raise SystemExit(f"{name} missing kw-chrome-collapsed")
    if "Hide Keywords" not in text:
        raise SystemExit(f"{name} missing Hide Keywords")
    if "runId:'sides-restore'" not in text:
        raise SystemExit(f"{name} missing sides-restore logs")
    if "ix.dataset.ixFitting==='1'" not in text:
        raise SystemExit(f"{name} missing applyIndexScrollFit guard")
    if "y>48&&!ix.classList.contains('is-collapsed')" in text:
        raise SystemExit(f"{name} still auto-collapses Index on scroll")
    if ">Pick</button>" not in text:
        raise SystemExit(f"{name} lost Pick")
    if "b.textContent=on?'Done':'Customize'" not in text:
        raise SystemExit(f"{name} lost Customize")
    if "function toggleModeLock" not in text:
        raise SystemExit(f"{name} lost toggleModeLock")
    if "columns:unset!important" not in text:
        raise SystemExit(f"{name} lost index columns:unset")
    if "No Shade" in text or ">Shade<" in text:
        raise SystemExit(f"{name} Shade label returned")


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
