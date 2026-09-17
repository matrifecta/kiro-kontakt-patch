#!/usr/bin/env python3
"""Header Search/K toggles, Sides index collapse + 1-3 cols + embed, search overflow."""
from pathlib import Path
import shutil

KIRO = Path("/home/phnx/KIRO/.kiro/specs/kontakt-workspace-drive-dirty-fix/artifacts")
WS = Path("/home/phnx/kiro-kontakt-patch/kiro/specs/kontakt-workspace-drive-dirty-fix/artifacts")
PUB = Path("/home/phnx/kiro-kontakt-patch/public/catalogs")

REPLACEMENTS = []


def add(old, new, label, optional=False, replace_all=False):
    if isinstance(old, str):
        old = (old,)
    REPLACEMENTS.append((old, new, label, optional, replace_all))


CSS_HDR = r"""
 .hdr-menu-btns{display:flex;align-items:center;gap:4px;flex:0 0 auto;margin-left:.35rem}
 .hdr-menu-btn{box-sizing:border-box;min-width:2.25rem;min-height:2.25rem;padding:0 .5rem;border:1px solid var(--border);border-radius:6px;background:var(--bg-card);color:var(--text-muted);font:inherit;font-size:.875rem;font-weight:600;cursor:pointer;touch-action:manipulation;line-height:1}
 .hdr-menu-btn.is-on{background:var(--accent-instrument-bg);color:var(--accent-instrument);border-color:var(--accent-instrument)}
 .hdr-menu-btn[aria-pressed="false"]{opacity:.72}
 .search-strip{position:relative}
 .search-strip-more{flex:0 0 auto;min-width:2.25rem;min-height:2.25rem;padding:0 .45rem;border:1px solid var(--border);border-radius:6px;background:var(--bg-card);color:var(--text);font:inherit;cursor:pointer;margin-left:auto}
 .search-strip-more-pop{position:absolute;right:.5rem;top:calc(100% + 4px);z-index:260;min-width:12rem;display:flex;flex-direction:column;gap:.35rem;padding:.5rem;background:var(--bg-surface);border:1px solid var(--border);border-radius:8px;box-shadow:0 12px 28px rgba(0,0,0,.38)}
 .search-strip-more-pop[hidden]{display:none!important}
 .search-strip-more-pop button{min-height:2.25rem;text-align:left;border:1px solid var(--border);border-radius:6px;background:var(--bg-card);color:var(--text);padding:.35rem .6rem;cursor:pointer;font:inherit}
 .catalog-index-embed{box-sizing:border-box;min-height:2.25rem;padding:0 .55rem;border:1px solid var(--border);border-radius:8px;background:var(--bg-surface);color:var(--text);font:inherit;font-size:.75rem;cursor:pointer;margin-left:auto}
 .catalog-index-embed[aria-pressed="true"]{background:var(--accent-instrument-bg);color:var(--accent-instrument);border-color:var(--accent-instrument)}
"""

add(
    " .display-switch{display:flex;align-items:center;gap:4px;flex:0 0 auto;margin-left:.5rem}\n",
    CSS_HDR
    + r"""
 body.display-upper .catalog-header+p,body.display-upper .catalog-header+p+p{display:none}
 body.display-upper.search-mode .search-chrome{height:auto!important;max-height:min(46dvh,32rem);margin-bottom:.35rem}
 body.display-upper .catalog-index{margin-top:.35rem}
 body.display-upper:not(.layout-edit) #searchChrome{min-height:0}
 /* fix-B: collapsed Upper: only hdrSearchBtn shows, strip-hide hidden */
 body.display-upper.search-chrome-collapsed .search-strip-hide{display:none!important}
 /* fix-C: Sides: kwStripHide is redundant with hdrKwBtn; hide it */
 body.display-sides #kwStripHide{display:none!important}
 body.display-fs.ac-fs-open .search-strip-hide,
 body.display-fs.ac-fs-open .search-strip-clear,
 body.display-fs.ac-fs-open .search-strip-fs,
 body.display-fs.ac-fs-open .search-strip-more{display:inline-flex!important}
 body.display-fs.ac-fs-open .search-only-scale{display:flex!important}
 body.display-fs.ac-fs-open .search-ac-shell.ac-fs>.search-strip{display:flex!important;flex-wrap:wrap;align-items:center}
 body.display-fs .search-ac-shell.ac-fs.toolbar-scroll-collapsed>.search-strip{display:flex!important}
 body.display-upper .search-strip-hide,body.display-upper .search-strip-clear,body.display-upper .search-strip-fs,body.display-upper .search-strip-more{display:inline-flex!important}
 body.display-sides:not(.search-chrome-collapsed) .search-strip-hide,
 body.display-sides:not(.search-chrome-collapsed) .search-strip-clear,
 body.display-sides:not(.search-chrome-collapsed) .search-strip-fs,
 body.display-sides:not(.search-chrome-collapsed) .search-strip-more{display:inline-flex!important}
 body.display-sides:not(.search-chrome-collapsed) .search-only-scale{display:flex!important}
 body.display-sides.search-chrome-collapsed .search-strip-more{display:none!important}
"""
    + " .display-switch{display:flex;align-items:center;gap:4px;flex:0 0 auto;margin-left:.5rem}\n",
    "hdr-css",
)

add(
    "  body.display-sides #catalogIndex .index,body.display-sides #catalogIndex #catalogIndexList{display:block!important;flex:1 1 auto;min-height:0;width:100%;max-width:100%;box-sizing:border-box;margin:0;padding:.4rem .7rem .75rem;overflow-x:hidden!important;overflow-y:auto!important;-webkit-overflow-scrolling:touch;overscroll-behavior:contain;touch-action:pan-y;columns:unset!important;column-width:unset!important;column-count:unset!important;column-gap:normal;column-fill:unset!important;list-style:disc;padding-left:1.25rem}\n"
    "  body.display-sides #catalogIndex .index li{display:list-item;break-inside:auto;-webkit-column-break-inside:auto;margin:.12rem 0;padding:0;max-width:100%;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}\n",
    "  body.display-sides #catalogIndex:not(.is-collapsed) .index,body.display-sides #catalogIndex:not(.is-collapsed) #catalogIndexList{display:grid!important;grid-template-columns:repeat(auto-fit,minmax(max(11rem,calc((100% - 1rem)/3)),1fr));grid-auto-flow:row;align-content:start;flex:1 1 auto;min-height:0;width:100%;max-width:100%;box-sizing:border-box;margin:0;padding:.4rem .7rem .75rem;overflow-x:hidden!important;overflow-y:auto!important;-webkit-overflow-scrolling:touch;overscroll-behavior:contain;touch-action:pan-y;columns:auto!important;column-width:auto!important;column-count:auto!important;list-style:disc;padding-left:1.25rem;gap:.05rem 1rem}\n"
    "  body.display-sides #catalogIndex.is-collapsed .index,body.display-sides #catalogIndex.is-collapsed #catalogIndexList{display:none!important;height:0!important;min-height:0!important;overflow:hidden!important;padding:0!important;border:0!important}\n"
    "  body.display-sides #catalogIndex .index li{display:list-item;break-inside:auto;margin:.12rem 0;padding:0;max-width:100%;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}\n"
    "  body.display-sides #catalogIndex.is-embedded{position:static!important;height:auto!important;max-height:none!important;box-shadow:none;border-radius:8px}\n"
    "  body.display-sides #catalogIndex.is-embedded:not(.is-collapsed) .index,body.display-sides #catalogIndex.is-embedded:not(.is-collapsed) #catalogIndexList{height:auto!important;max-height:none!important;overflow:visible!important;flex:0 0 auto}\n"
    "  body.display-sides #catalogIndex.is-embedded #indexHeight{display:none!important}\n",
    "sides-index-grid",
)

add(
    '<div class="display-switch" id="displaySwitch" role="tablist" aria-label="Display layout"><button type="button" class="display-btn is-active" data-display="upper"',
    '<div class="hdr-menu-btns" id="hdrMenuBtns" role="toolbar" aria-label="Search and Keywords"><button type="button" class="hdr-menu-btn is-on" id="hdrSearchBtn" aria-pressed="true" title="Search" aria-label="Search" onclick="event.preventDefault();event.stopPropagation();toggleHdrSearch()">&#x1F50D;</button><button type="button" class="hdr-menu-btn is-on" id="hdrKwBtn" aria-pressed="true" title="Keywords" aria-label="Keywords" onclick="event.preventDefault();event.stopPropagation();toggleHdrKw()">K</button></div><div class="display-switch" id="displaySwitch" role="tablist" aria-label="Display layout"><button type="button" class="display-btn is-active" data-display="upper"',
    "hdr-btns",
)

add(
    'id="searchOnlyScalePop" hidden></div></div></div><div class="search-ac-shell"',
    'id="searchOnlyScalePop" hidden></div></div><button type="button" class="search-strip-more" id="searchStripMore" aria-expanded="false" aria-haspopup="true" title="More search controls" onclick="event.preventDefault();event.stopPropagation();toggleSearchStripMore()">&#x22EF;</button><div class="search-strip-more-pop" id="searchStripMorePop" hidden></div></div><div class="search-ac-shell"',
    "search-more",
)

add(
    '<h2 class="catalog-index-title">Index (alphabetical)</h2></div><ul class="index" id="catalogIndexList">',
    '<h2 class="catalog-index-title">Index (alphabetical)</h2><button type="button" class="catalog-index-embed" id="catalogIndexEmbed" aria-pressed="false" title="Embed index above the catalog cards" onclick="event.preventDefault();event.stopPropagation();toggleIndexEmbed()">Embed</button></div><ul class="index" id="catalogIndexList">',
    "index-embed-btn",
)

add(
    "function toggleFilter(){\n"
    "  var w=document.getElementById('filterWrap'),a=document.querySelector('.toggle-arrow');\n"
    "  if(!w)return;\n",
    "function toggleFilter(){\n"
    "  var w=document.getElementById('filterWrap'),a=document.querySelector('.toggle-arrow');\n"
    "  if(!w)return;\n"
    "  if(document.body.classList.contains('display-sides')){\n"
    "    if(typeof toggleKwChrome==='function')toggleKwChrome();\n"
    "    if(typeof syncHdrMenuBtns==='function')syncHdrMenuBtns();\n"
    "    return;\n"
    "  }\n",
    "togglefilter-sides",
)

JS = r"""
function syncHdrMenuBtns(){
  var searchOn=!document.body.classList.contains('search-chrome-collapsed');
  var fw=document.getElementById('filterWrap');
  var kwOn=!document.body.classList.contains('kw-chrome-collapsed')&&!!(fw&&fw.classList.contains('open'));
  var sb=document.getElementById('hdrSearchBtn');
  var kb=document.getElementById('hdrKwBtn');
  if(sb){sb.classList.toggle('is-on',searchOn);sb.setAttribute('aria-pressed',searchOn?'true':'false');sb.title=searchOn?'Hide Search':'Show Search';}
  if(kb){kb.classList.toggle('is-on',kwOn);kb.setAttribute('aria-pressed',kwOn?'true':'false');kb.title=kwOn?'Hide Keywords':'Show Keywords';}
}
function toggleHdrSearch(){
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
  if(typeof writeModeSlot==='function')writeModeSlot({indexEmbed:on},'sides');
  if(typeof applyIndexScrollFit==='function')applyIndexScrollFit();
  syncIndexEmbedBtn();
  var cm=document.getElementById('catalogMain');
  if(on&&cm)cm.scrollTop=0;
}
function toggleSearchStripMore(){
  var pop=document.getElementById('searchStripMorePop');
  var btn=document.getElementById('searchStripMore');
  if(!pop||!btn)return;
  var open=pop.hasAttribute('hidden');
  if(open){
    pop.innerHTML='';
    function add(label,fn){var b=document.createElement('button');b.type='button';b.textContent=label;b.addEventListener('click',function(e){e.preventDefault();e.stopPropagation();pop.setAttribute('hidden','');btn.setAttribute('aria-expanded','false');fn();});pop.appendChild(b);}
    add(document.body.classList.contains('search-chrome-collapsed')?'Show Search':'Hide search',function(){if(typeof toggleSearchChrome==='function')toggleSearchChrome();});
    add('Clear',function(){if(typeof clearAllFilters==='function')clearAllFilters();});
    add('Fullscreen search',function(){if(typeof toggleAcFullscreen==='function')toggleAcFullscreen();});
    add('Smaller Search',function(){if(typeof stepSearchOnlyUiScale==='function')stepSearchOnlyUiScale(-1);});
    add('Larger Search',function(){if(typeof stepSearchOnlyUiScale==='function')stepSearchOnlyUiScale(1);});
    pop.removeAttribute('hidden');
    btn.setAttribute('aria-expanded','true');
  }else{
    pop.setAttribute('hidden','');
    btn.setAttribute('aria-expanded','false');
  }
}
window.syncHdrMenuBtns=syncHdrMenuBtns;
window.toggleHdrSearch=toggleHdrSearch;
window.toggleHdrKw=toggleHdrKw;
window.syncIndexEmbedBtn=syncIndexEmbedBtn;
window.toggleIndexEmbed=toggleIndexEmbed;
window.toggleSearchStripMore=toggleSearchStripMore;
document.addEventListener('click',function(e){
  var pop=document.getElementById('searchStripMorePop');
  var btn=document.getElementById('searchStripMore');
  if(!pop||pop.hasAttribute('hidden'))return;
  if(btn&&(btn===e.target||btn.contains(e.target)))return;
  if(pop.contains(e.target))return;
  pop.setAttribute('hidden','');
  if(btn)btn.setAttribute('aria-expanded','false');
});
"""

add(
    "window.resetIndexDock=resetIndexDock;\n",
    "window.resetIndexDock=resetIndexDock;\n" + JS,
    "hdr-js",
)

add(
    "  if(window.syncLayoutStoreUi)window.syncLayoutStoreUi();\n"
    "  if(window.syncSearchSplit)window.syncSearchSplit();\n"
    "}\n",
    "  if(window.syncLayoutStoreUi)window.syncLayoutStoreUi();\n"
    "  if(window.syncSearchSplit)window.syncSearchSplit();\n"
    "  if(typeof syncHdrMenuBtns==='function')syncHdrMenuBtns();\n"
    "}\n",
    "sync-hdr-from-search-hide",
)

add(
    "  if(typeof syncSearchHideBtn==='function')syncSearchHideBtn();\n"
    "  if(typeof applySidesCols==='function')applySidesCols();\n"
    "  if(typeof logSidesRestore==='function')logSidesRestore('H1','collapseKwMenu','hide-kw',{});\n",
    "  if(typeof syncSearchHideBtn==='function')syncSearchHideBtn();\n"
    "  if(typeof applySidesCols==='function')applySidesCols();\n"
    "  if(typeof syncHdrMenuBtns==='function')syncHdrMenuBtns();\n"
    "  if(typeof logSidesRestore==='function')logSidesRestore('H1','collapseKwMenu','hide-kw',{});\n",
    "sync-hdr-hide-kw",
    optional=True,
)

add(
    "  if(document.body.classList.contains('display-sides')){\n"
    "    box.dataset.dockAuto='';\n"
    "    box.dataset.dockPin=collapsed?'':'1';\n"
    "  }\n",
    "  if(document.body.classList.contains('display-sides')){\n"
    "    box.dataset.dockAuto='';\n"
    "    box.dataset.dockPin=collapsed?'':'1';\n"
    "    if(typeof writeModeSlot==='function')writeModeSlot({indexCollapsed:!!collapsed},'sides');\n"
    "  }\n"
    "  if(typeof applyIndexScrollFit==='function')applyIndexScrollFit();\n",
    "index-collapse-persist",
)

add(
    "      if(ih>40)patch.indexH=ih;\n"
    "      patch.pinned=!!sidesPinned;\n",
    "      if(ih>40)patch.indexH=ih;\n"
    "      var ixSnap=document.getElementById('catalogIndex');\n"
    "      if(ixSnap){patch.indexEmbed=ixSnap.classList.contains('is-embedded');patch.indexCollapsed=ixSnap.classList.contains('is-collapsed');}\n"
    "      patch.pinned=!!sidesPinned;\n",
    "snapshot-index-flags",
)

add(
    "      if(slot.indexH)document.body.style.setProperty('--sides-index-h',parseInt(slot.indexH,10)+'px');\n"
    "      if(typeof slot.pinned==='boolean'){\n",
    "      if(slot.indexH)document.body.style.setProperty('--sides-index-h',parseInt(slot.indexH,10)+'px');\n"
    "      var ixSlot=document.getElementById('catalogIndex');\n"
    "      if(ixSlot){\n"
    "        if(typeof slot.indexEmbed==='boolean')ixSlot.classList.toggle('is-embedded',!!slot.indexEmbed);\n"
    "        if(typeof slot.indexCollapsed==='boolean')ixSlot.classList.toggle('is-collapsed',!!slot.indexCollapsed);\n"
    "        if(typeof syncIndexToggleUi==='function')syncIndexToggleUi(ixSlot);\n"
    "        if(typeof syncIndexEmbedBtn==='function')syncIndexEmbedBtn();\n"
    "      }\n"
    "      if(typeof slot.pinned==='boolean'){\n",
    "apply-index-flags",
)

add(
    "  if(!document.body.classList.contains('display-sides')||ix.classList.contains('is-collapsed')){\n"
    "    ['height','max-height','columns','column-width','column-count','column-fill'].forEach(function(p){il.style.removeProperty(p);});\n"
    "    try{delete ix.dataset.ixFitInner;}catch(err){ix.dataset.ixFitInner='';}\n"
    "    if(typeof logModeIndep==='function'&&!document.body.classList.contains('display-sides'))logModeIndep('H2','applyIndexScrollFit','clear-cols-leave-sides',{});\n"
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
    "  il.style.maxHeight=inner+'px';\n",
    "  if(!document.body.classList.contains('display-sides')||ix.classList.contains('is-collapsed')||ix.classList.contains('is-embedded')){\n"
    "    ['height','max-height','columns','column-width','column-count','column-fill','display','grid-template-columns'].forEach(function(p){il.style.removeProperty(p);});\n"
    "    try{delete ix.dataset.ixFitInner;}catch(err){ix.dataset.ixFitInner='';}\n"
    "    if(typeof logModeIndep==='function'&&!document.body.classList.contains('display-sides'))logModeIndep('H2','applyIndexScrollFit','clear-cols-leave-sides',{});\n"
    "    if(typeof syncIndexEmbedBtn==='function')syncIndexEmbedBtn();\n"
    "    return;\n"
    "  }\n"
    "  var head=ix.querySelector('.catalog-index-head');\n"
    "  var hh=head?Math.round(head.getBoundingClientRect().height):0;\n"
    "  var inner=Math.max(48,Math.round(ix.clientHeight-hh));\n"
    "  if((ix.dataset.ixFitInner||'')===String(inner)&&il.style.height===inner+'px')return;\n"
    "  ix.dataset.ixFitting='1';\n"
    "  il.style.removeProperty('columns');\n"
    "  il.style.removeProperty('column-width');\n"
    "  il.style.removeProperty('column-count');\n"
    "  il.style.removeProperty('column-fill');\n"
    "  il.style.height=inner+'px';\n"
    "  il.style.maxHeight=inner+'px';\n",
    "index-fit-grid",
)

add(
    "  cap(sh);cap(panel);cap(kw);\n"
    "  // #region agent log\n"
    "  fetch('http://127.0.0.1:7529/ingest/1cf46354-1d61-4c80-bd72-a340f1db1b51',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'f491c2'},body:JSON.stringify({sessionId:'f491c2',runId:'layout-fix',hypothesisId:'H2',location:'applyUpperContain',message:'upper-contain',",
    "  cap(sh);cap(panel);cap(kw);\n"
    "  if(!document.body.classList.contains('layout-edit')){ch.style.removeProperty('height');ch.style.maxHeight='min(46dvh,32rem)';}\n"
    "  // #region agent log\n"
    "  fetch('http://127.0.0.1:7529/ingest/1cf46354-1d61-4c80-bd72-a340f1db1b51',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'f491c2'},body:JSON.stringify({sessionId:'f491c2',runId:'layout-fix',hypothesisId:'H2',location:'applyUpperContain',message:'upper-contain',",
    "upper-hug",
    optional=True,
)

# Sync header buttons after setDisplayMode sides-already restore
add(
    "    if(typeof logSidesRestore==='function')logSidesRestore('H2','setDisplayMode','sides-already'",
    "    if(typeof syncHdrMenuBtns==='function')syncHdrMenuBtns();\n"
    "    if(typeof syncIndexEmbedBtn==='function')syncIndexEmbedBtn();\n"
    "    if(typeof logSidesRestore==='function')logSidesRestore('H2','setDisplayMode','sides-already'",
    "sides-already-sync",
    optional=True,
)


def must_replace(text, olds, new, label, optional=False, replace_all=False):
    marker = None
    if "hdr-menu-btns" in new and "display-switch" in new and "hdrSearchBtn" in new:
        marker = 'id="hdrSearchBtn"'
    elif "sides-index-grid" in label:
        marker = "body.display-sides #catalogIndex.is-collapsed .index"
    elif "toggleHdrSearch" in new and "window.resetIndexDock" in new:
        marker = "function toggleHdrSearch"
    elif "index-fit-grid" in label:
        marker = "ix.classList.contains('is-embedded')"
    if marker and marker in text:
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
        raise SystemExit(f"{name} missing hideSearchAc")
    if "function toggleHdrSearch" not in text:
        raise SystemExit(f"{name} missing toggleHdrSearch")
    if 'id="hdrSearchBtn"' not in text:
        raise SystemExit(f"{name} missing hdrSearchBtn")
    if 'id="hdrKwBtn"' not in text:
        raise SystemExit(f"{name} missing hdrKwBtn")
    if "function toggleIndexEmbed" not in text:
        raise SystemExit(f"{name} missing toggleIndexEmbed")
    if "catalog-index-embed" not in text:
        raise SystemExit(f"{name} missing Embed button")
    if "is-collapsed .index,body.display-sides #catalogIndex.is-collapsed #catalogIndexList{display:none!important" not in text:
        raise SystemExit(f"{name} missing collapse override")
    if "repeat(auto-fit,minmax(max(11rem" not in text:
        raise SystemExit(f"{name} missing 1-3 col grid")
    if "searchStripMore" not in text:
        raise SystemExit(f"{name} missing search more")
    if "body.display-fs.ac-fs-open .search-strip-hide" not in text:
        raise SystemExit(f"{name} missing Full search-button restore")
    if "body.display-upper.search-mode .search-chrome{height:auto!important" not in text:
        raise SystemExit(f"{name} missing Upper chrome hug")
    if ">Pick</button>" not in text:
        raise SystemExit(f"{name} lost Pick")


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
        if "function hideSearchAc" not in out or "</html>" not in out:
            raise SystemExit(f"{path.name} missing hideSearchAc or </html>")
        try:
            assert_common(out, path.name)
        except SystemExit as e:
            if "public/catalogs" in str(path):
                raise
            print("  warn stale artifact", path.name, e)
        path.write_text(out, encoding="utf-8")
        print("patched", path.name, len(out))


if __name__ == "__main__":
    main()
