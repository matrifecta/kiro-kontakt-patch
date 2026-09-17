#!/usr/bin/env python3
"""Add Legend/Guide left-edge widgets on Kontakt/DS catalogs.

Safe writes: temp file, assert </html> + size, then replace.
Does not commit. Keeps existing c00e3e agent logs.
"""
from pathlib import Path

ROOT = Path("/home/phnx/kiro-kontakt-patch")
FILES = [
    ROOT / "public/catalogs/DS-CATALOG.html",
    ROOT / "public/catalogs/KONTAKT-CATALOG.html",
    ROOT / "public/catalogs/DS-CATALOG-portable.html",
    ROOT / "public/catalogs/KONTAKT-CATALOG-portable.html",
]

MARKER = "fix-LEGEND-GUIDE-EDGE"

CSS_JUMP = (
    "  body.display-sides #catalogJumpStack>a.top,body.display-sides #catalogJumpStack>a.bottom"
    "{position:relative!important;top:auto!important;bottom:auto!important;margin:0!important;pointer-events:auto;z-index:40}\n"
)

CSS_EDGE = r'''  body.display-sides #catalogJumpStack>a.top,body.display-sides #catalogJumpStack>a.bottom{position:relative!important;top:auto!important;bottom:auto!important;margin:0!important;pointer-events:auto;z-index:40}
/* fix-LEGEND-GUIDE-EDGE: left-border Legend/Guide widgets on the content pane */
#catalogEdgeStack{display:none;position:fixed;z-index:41;flex-direction:column;align-items:flex-start;gap:.4rem;pointer-events:none;width:0;overflow:visible}
body.display-sides #catalogEdgeStack,body.display-middle #catalogEdgeStack{display:flex}
.catalog-edge-btn{pointer-events:auto;box-sizing:border-box;flex:0 0 auto;width:2.55rem;height:2.55rem;min-width:2.55rem;min-height:2.55rem;padding:0;margin:0;display:inline-flex;align-items:center;justify-content:center;border:1px solid var(--border);border-left-width:0;border-radius:0 8px 8px 0;background:var(--bg-card);color:var(--text);cursor:pointer;touch-action:manipulation;transform:translateX(.42rem);transition:transform .16s ease,color .16s ease,border-color .16s ease,background .16s ease;box-shadow:4px 0 10px rgba(0,0,0,.18)}
.catalog-edge-btn svg{width:1.35rem;height:1.35rem;display:block;pointer-events:none;color:inherit;stroke:currentColor;fill:none}
.catalog-edge-btn:hover,.catalog-edge-btn:focus-visible{color:var(--accent-instrument);border-color:var(--accent-instrument);background:var(--accent-instrument-bg);outline:none}
.catalog-edge-btn[aria-pressed="true"]{transform:translateX(1.05rem);color:var(--accent-instrument);border-color:var(--accent-instrument);background:var(--accent-instrument-bg)}
body:is(.hl-open,.gallery-open,.img-focus-open,.desc-reader-open,.path-reader-open,.desc-focus-open,.path-focus-open,.chosen-preview-open,.card-embed-open):not(.catalog-help-open):not(.catalog-help-fs) #catalogEdgeStack{visibility:hidden!important;pointer-events:none!important}
body.catalog-help-open #catalogEdgeStack,body.catalog-help-fs #catalogEdgeStack{z-index:860;display:flex}
.catalog-help-card{display:none;position:fixed;left:50%;top:50%;transform:translate(-50%,-50%);z-index:840;box-sizing:border-box;width:min(86vw,70rem);height:auto;min-height:min(52vh,26.25rem);max-width:min(86vw,70rem);max-height:min(88vh,53.75rem);margin:0;padding:0;overflow:hidden;flex-direction:column;background:var(--bg-card);color:var(--text);border:1px solid var(--border);border-radius:8px;box-shadow:0 18px 56px rgba(0,0,0,.5);isolation:isolate}
body.catalog-help-open .catalog-help-card,body.catalog-help-fs .catalog-help-card{display:flex}
body.catalog-help-open:not(.catalog-help-fs)::before{content:"";position:fixed;inset:0;background:rgba(0,0,0,.55);z-index:830;pointer-events:none}
body.catalog-help-fs{overflow:hidden}
body.catalog-help-fs .catalog-help-card{inset:0;left:0;top:0;right:0;bottom:0;transform:none;width:100%;height:100%;max-width:none;max-height:none;min-height:100%;border-radius:0;z-index:900;padding-top:var(--safe-top);padding-bottom:var(--safe-bottom)}
.catalog-help-chrome{display:flex;align-items:center;gap:.4rem;flex:0 0 auto;min-height:calc(var(--card-chrome-btn) + 1rem);padding:.5rem .6rem .35rem;border-bottom:1px solid var(--border);background:var(--bg-surface);box-sizing:border-box}
.catalog-help-back,.catalog-help-fs-btn{box-sizing:border-box;width:var(--card-chrome-btn);height:var(--card-chrome-btn);min-width:var(--card-chrome-btn);min-height:var(--card-chrome-btn);display:inline-flex;align-items:center;justify-content:center;padding:0;border-radius:8px;cursor:pointer;touch-action:manipulation;font-size:1.375rem;line-height:1;flex:0 0 auto}
.catalog-help-back{background:var(--bg-card);color:var(--text);border:1px solid var(--border)}
.catalog-help-back:hover{color:var(--accent-instrument);border-color:var(--accent-instrument);background:var(--accent-instrument-bg)}
.catalog-help-fs-btn{margin-left:auto;background:var(--bg-surface);color:var(--accent-instrument);border:1px solid var(--accent-instrument);font-size:1.25rem}
.catalog-help-fs-btn:hover{color:var(--accent-instrument-active);border-color:var(--accent-instrument-active);background:var(--accent-instrument-bg)}
body.catalog-portable .catalog-help-fs-btn,body.catalog-help-fs .catalog-help-fs-btn{display:none!important}
@media(max-width:899px){.catalog-help-fs-btn{display:none!important}}
.catalog-help-title{flex:1 1 auto;min-width:0;margin:0;font-size:1.05rem;font-weight:650;color:var(--text);overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.catalog-help-tabs{display:none;flex:1 1 auto;min-width:0;align-items:flex-end;gap:0;height:100%;padding-top:.15rem}
body.catalog-help-kind-guide .catalog-help-tabs{display:flex}
body.catalog-help-kind-guide .catalog-help-title{display:none}
.catalog-help-tab{flex:1 1 0;min-width:0;min-height:2.35rem;margin:0;padding:.35rem .7rem 0;border:1px solid var(--border);border-bottom:0;border-radius:8px 8px 0 0;background:var(--bg);color:var(--text-muted);font:inherit;font-size:.9rem;cursor:pointer;touch-action:manipulation}
.catalog-help-tab[aria-selected="true"]{background:var(--bg-card);color:var(--accent-instrument);border-color:var(--accent-instrument);font-weight:650;z-index:1}
.catalog-help-body{flex:1 1 auto;min-height:0;overflow-x:hidden;overflow-y:auto;-webkit-overflow-scrolling:touch;padding:.7rem .9rem 1.1rem;color:var(--text);font-size:.95rem}
.catalog-help-panel[hidden]{display:none!important}
.catalog-help-body h2{margin:.2rem 0 .55rem;font-size:1.15rem;border:0;padding:0;color:var(--text)}
.catalog-help-body h3{margin:.85rem 0 .3rem;font-size:1rem;color:var(--text)}
.catalog-help-body p,.catalog-help-body li{color:var(--text);font-size:.95rem}
.catalog-help-body .catalog-help-muted{color:var(--text-muted)}
.catalog-help-body details{margin:.45rem 0;border:1px solid var(--border);border-radius:8px;background:var(--bg-surface);padding:.15rem .7rem .45rem}
.catalog-help-body summary{cursor:pointer;font-weight:650;min-height:2.15rem;display:flex;align-items:center;color:var(--text);touch-action:manipulation}
.catalog-help-body code{font-size:.85em;background:var(--bg);border:1px solid var(--border);border-radius:4px;padding:.05em .3em}
'''

HIDE_OLD = (
    "body:is(.hl-open,.gallery-open,.img-focus-open,.desc-reader-open,.path-reader-open,.desc-focus-open,.path-focus-open,.chosen-preview-open,.card-embed-open) .top,"
    "body:is(.hl-open,.gallery-open,.img-focus-open,.desc-reader-open,.path-reader-open,.desc-focus-open,.path-focus-open,.chosen-preview-open,.card-embed-open) .bottom"
    "{visibility:hidden!important;pointer-events:none!important}"
)
HIDE_NEW = (
    "body:is(.hl-open,.gallery-open,.img-focus-open,.desc-reader-open,.path-reader-open,.desc-focus-open,.path-focus-open,.chosen-preview-open,.card-embed-open,.catalog-help-open,.catalog-help-fs) .top,"
    "body:is(.hl-open,.gallery-open,.img-focus-open,.desc-reader-open,.path-reader-open,.desc-focus-open,.path-focus-open,.chosen-preview-open,.card-embed-open,.catalog-help-open,.catalog-help-fs) .bottom"
    "{visibility:hidden!important;pointer-events:none!important}"
)

PORT_CSS_OLD = "  body.catalog-portable #catalogJumpStack{display:none!important}\n"
PORT_CSS_NEW = (
    "  body.catalog-portable #catalogJumpStack{display:none!important}\n"
    "  body.catalog-portable #catalogEdgeStack{display:none!important}\n"
    "  body.catalog-portable.display-sides #catalogEdgeStack{\n"
    "    display:flex!important;position:fixed!important;z-index:46!important;\n"
    "    flex-direction:column;align-items:flex-start;gap:.4rem;pointer-events:none;\n"
    "    width:0;overflow:visible\n"
    "  }\n"
    "  body.catalog-portable.display-fs #catalogEdgeStack,\n"
    "  body.catalog-portable.display-sides.dual-fs-open #catalogEdgeStack,\n"
    "  body.catalog-portable.display-sides.ac-fs-open.kw-fs-open #catalogEdgeStack{\n"
    "    display:none!important\n"
    "  }\n"
    "  body.catalog-portable.catalog-help-open #catalogEdgeStack,\n"
    "  body.catalog-portable.catalog-help-fs #catalogEdgeStack{display:flex!important;z-index:860!important}\n"
)

HTML_JUMP = '<a class="bottom" href="#catalogBottom">&darr; bottom</a><a class="top" href="#top">&uarr; top</a>\n'

HTML_EDGE = r'''<a class="bottom" href="#catalogBottom">&darr; bottom</a><a class="top" href="#top">&uarr; top</a>
<div id="catalogEdgeStack" hidden>
  <button type="button" class="catalog-edge-btn" id="catalogGuideBtn" data-help="guide" aria-pressed="false" aria-label="Guide" title="Guide" onclick="event.preventDefault();event.stopPropagation();toggleCatalogHelp('guide')">
    <svg viewBox="0 0 24 24" aria-hidden="true" focusable="false" fill="none" stroke="currentColor" stroke-width="1.55" stroke-linecap="round" stroke-linejoin="round">
      <path d="M5.2 4.8h10.1c.9 0 1.7.8 1.7 1.7v11.4H6.7c-.8 0-1.5.5-1.5 1.4V6.5c0-.9.8-1.7 1.7-1.7z"/>
      <path d="M5.2 4.8v14.6"/>
      <path d="M8 8.2h6.6M8 10.7h5.1"/>
      <circle cx="17.35" cy="6.7" r="3.2" fill="var(--bg-card)"/>
      <circle cx="17.35" cy="6.7" r="3.2"/>
      <circle cx="17.35" cy="5.5" r=".45" fill="currentColor" stroke="none"/>
      <path d="M17.35 7.15v2.05" stroke-width="1.7"/>
    </svg>
  </button>
  <button type="button" class="catalog-edge-btn" id="catalogLegendBtn" data-help="legend" aria-pressed="false" aria-label="Legend" title="Legend" onclick="event.preventDefault();event.stopPropagation();toggleCatalogHelp('legend')">
    <svg viewBox="0 0 24 24" aria-hidden="true" focusable="false" fill="none" stroke="currentColor" stroke-width="1.55" stroke-linecap="round" stroke-linejoin="round">
      <g transform="rotate(-42 12 12)">
        <circle cx="12" cy="5.15" r="2.55"/>
        <circle cx="9.65" cy="8.55" r="2.55"/>
        <circle cx="14.35" cy="8.55" r="2.55"/>
        <circle cx="12" cy="5.15" r=".95"/>
        <circle cx="9.65" cy="8.55" r=".95"/>
        <circle cx="14.35" cy="8.55" r=".95"/>
        <path d="M12 11.1v8.55"/>
        <path d="M12 16.9h2.25"/>
        <path d="M12 19.65h3.05"/>
        <path d="M14.25 16.9v-1.05"/>
        <path d="M15.05 19.65v-1.1"/>
      </g>
    </svg>
  </button>
</div>
<div id="catalogHelpCard" class="catalog-help-card" hidden aria-hidden="true" role="dialog" aria-modal="true" aria-labelledby="catalogHelpTitle">
  <div class="catalog-help-chrome">
    <button type="button" class="catalog-help-back" id="catalogHelpBack" aria-label="Back" title="Back" onclick="event.preventDefault();event.stopPropagation();catalogHelpBack()">&#x2190;</button>
    <h2 class="catalog-help-title" id="catalogHelpTitle">Legend</h2>
    <div class="catalog-help-tabs" id="catalogHelpTabs" role="tablist" aria-label="Guide">
      <button type="button" class="catalog-help-tab" id="catalogHelpTabUser" role="tab" aria-selected="true" aria-controls="catalogHelpUser" data-tab="user" onclick="event.preventDefault();event.stopPropagation();setCatalogHelpTab('user')">User guide</button>
      <button type="button" class="catalog-help-tab" id="catalogHelpTabUpdate" role="tab" aria-selected="false" aria-controls="catalogHelpUpdate" data-tab="update" onclick="event.preventDefault();event.stopPropagation();setCatalogHelpTab('update')">Update guide</button>
    </div>
    <button type="button" class="catalog-help-fs-btn" id="catalogHelpFs" aria-label="Open fullscreen" title="Open fullscreen" onclick="event.preventDefault();event.stopPropagation();catalogHelpEnterFs()">&#x26F6;</button>
  </div>
  <div class="catalog-help-body" id="catalogHelpBody">
    <div class="catalog-help-panel" id="catalogHelpLegend" data-panel="legend">
      <p class="catalog-help-muted" id="catalogHelpLegendLead">Symbols and chrome for this catalog.</p>
      <details open>
        <summary>Cards and path</summary>
        <ul>
          <li><b>Cards</b> are libraries. Open one for preview; desktop fullscreen is the top-right control on that card.</li>
          <li><b>Path</b> shows the library folder. Folder / copy / open icons sit on that row and follow the current theme.</li>
          <li><b>Cover</b> opens gallery or image focus. Favorite lives on the card chrome.</li>
        </ul>
      </details>
      <details>
        <summary>Search, Keywords, Index</summary>
        <ul>
          <li><b>Search</b> filters the catalog. Session AC stays in the search column; it does not auto-open a front card.</li>
          <li><b>Keywords</b> are the right-hand (or stacked) filter chips. Combine them to narrow cards.</li>
          <li><b>Index</b> stays closed until you use the Index arrow. <b>Window</b> docks it; <b>Embed</b> places it with the cards.</li>
        </ul>
      </details>
      <details>
        <summary>Layout chrome</summary>
        <ul>
          <li><b>Sides</b> — Search | catalog | Keywords as three panes.</li>
          <li><b>Middle</b> — catalog between Search and Keywords, stacked on portrait.</li>
          <li><b>Flip</b> — swaps the side panes. Portable always behaves as phone.</li>
          <li><b>↑ top / ↓ bottom</b> sit on the content window (usually right) and stay put while you scroll cards.</li>
          <li>These Legend / Guide keys sit on the <b>left content border</b>.</li>
        </ul>
      </details>
      <details>
        <summary>About / Document</summary>
        <p id="catalogHelpAboutReuse" class="catalog-help-muted">The catalog About / Document note lives at the foot of the content window (Window or Embed).</p>
      </details>
    </div>
    <div class="catalog-help-panel" id="catalogHelpUser" data-panel="user" role="tabpanel" aria-labelledby="catalogHelpTabUser" hidden>
      <p class="catalog-help-muted">How to use the <span class="catalog-help-product">catalog</span>.</p>
      <details open>
        <summary>Find a library</summary>
        <ul>
          <li>Type in <b>Search</b>, or tap <b>Keywords</b>, or pick a name from <b>Index</b> after opening it with the Index arrow.</li>
          <li>Click a card name in Index to jump. Path icons open the folder or copy the location.</li>
        </ul>
      </details>
      <details>
        <summary>Preview and fullscreen</summary>
        <ul>
          <li>Desktop: a card opens as an expanded preview. Back (arrow left) returns to the catalog. The top-right control enters fullscreen; Back from fullscreen returns to the expanded card, then Back again returns to the catalog.</li>
          <li>Portable / phone: preview and documents open as a fullscreen popup. Back exits that step.</li>
        </ul>
      </details>
      <details>
        <summary>Arrange the workspace</summary>
        <ul>
          <li>Use <b>Sides</b>, <b>Middle</b>, and <b>Flip</b> so Search and Keywords sit where you want them. The catalog cards stay in the content window.</li>
          <li>Hide Search or Keywords when you need the cards. Index Window / Embed keep the list available without covering Search.</li>
        </ul>
      </details>
    </div>
    <div class="catalog-help-panel" id="catalogHelpUpdate" data-panel="update" role="tabpanel" aria-labelledby="catalogHelpTabUpdate" hidden>
      <p class="catalog-help-muted">What changed, and how to refresh this catalog.</p>
      <details open>
        <summary>Recent catalog chrome</summary>
        <ul>
          <li>Index <b>Window</b> / <b>Embed</b>, About / Document dock, and left-edge Legend / Guide.</li>
          <li>Jump ↑/↓ stay on the content pane while you scroll. Portable is always phone chrome.</li>
          <li>Session autocomplete does not auto-open a front card. Index stays closed until the Index arrow.</li>
        </ul>
      </details>
      <details>
        <summary>Rebuild after new libraries</summary>
        <p id="catalogHelpRebuild">Re-run the catalog builder for this library set, then reload the page. Desktop and portable HTML are separate files.</p>
      </details>
    </div>
  </div>
</div>
'''

JS_HELP = r'''function catalogHelpUseDesktopCard(){
  return !window.CATALOG_PORTABLE && typeof displayIsDesktop==='function' && displayIsDesktop();
}
function catalogHelpLog(msg,data){
  try{
    fetch('http://127.0.0.1:7529/ingest/1cf46354-1d61-4c80-bd72-a340f1db1b51',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'c00e3e'},body:JSON.stringify({sessionId:'c00e3e',runId:'legend-guide',hypothesisId:'H-edge',location:'catalog:help',message:msg,data:data||{},timestamp:Date.now()})}).catch(function(){});
  }catch(errLg){}
}
function ensureCatalogEdgeStack(){
  var stack=document.getElementById('catalogEdgeStack');
  if(!stack){
    stack=document.createElement('div');
    stack.id='catalogEdgeStack';
    document.body.appendChild(stack);
  }
  if(stack.parentNode!==document.body)document.body.appendChild(stack);
  var card=document.getElementById('catalogHelpCard');
  if(card&&card.parentNode!==document.body)document.body.appendChild(card);
  return stack;
}
function placeCatalogEdgeStack(){
  var stack=ensureCatalogEdgeStack();
  var main=document.getElementById('catalogMain');
  if(!stack)return;
  var sides=document.body.classList.contains('display-sides');
  var middle=document.body.classList.contains('display-middle');
  var fs=document.body.classList.contains('display-fs');
  var helpOn=document.body.classList.contains('catalog-help-open')||document.body.classList.contains('catalog-help-fs');
  var r=main?main.getBoundingClientRect():null;
  var cs=main?getComputedStyle(main):null;
  var hide=!main||(!helpOn&&(fs||!(sides||middle)))||(cs&&cs.display==='none')||!r||r.width<8||r.height<8;
  if(hide){
    stack.hidden=true;
    stack.style.cssText='';
    return;
  }
  stack.hidden=false;
  var inset=typeof catalogJumpStackBottomInset==='function'?catalogJumpStackBottomInset():0;
  var bottom=Math.max(6,Math.round((window.innerHeight||0)-r.bottom)+12+inset);
  var left=Math.max(0,Math.round(r.left));
  stack.style.position='fixed';
  stack.style.left=left+'px';
  stack.style.bottom=bottom+'px';
  stack.style.right='auto';
  stack.style.top='auto';
  stack.style.zIndex=helpOn?'860':'41';
  if(typeof catalogHelpSyncChrome==='function')catalogHelpSyncChrome();
}
function catalogHelpFillCopy(){
  var ns=window.CATALOG_NS==='ds'?'Decent Sampler':'Kontakt';
  document.querySelectorAll('.catalog-help-product').forEach(function(el){el.textContent=ns+' catalog';});
  var about=document.getElementById('catalogDocNoteBody');
  var lead=document.getElementById('catalogHelpLegendLead');
  var reuse=document.getElementById('catalogHelpAboutReuse');
  var txt=about?String(about.textContent||'').replace(/\s+/g,' ').trim():'';
  if(lead)lead.textContent=ns+' chrome and symbols. Cards stay in the content window; these keys sit on its left border.';
  if(reuse)reuse.textContent=txt||('About / Document is the collapsible note at the foot of the '+ns+' content window.');
  var rebuild=document.getElementById('catalogHelpRebuild');
  if(rebuild){
    rebuild.innerHTML=window.CATALOG_NS==='ds'
      ? 'Added libraries? Re-run <code>build-ds-catalog-html.sh both</code>, then reload. Desktop and portable catalogs are separate files.'
      : 'Registered libraries come from <code>komplete.db3</code>. Rebuild with <code>build-kontakt-catalog-html.sh</code>, then reload. Desktop and portable catalogs are separate files.';
  }
}
function catalogHelpSyncChrome(){
  var card=document.getElementById('catalogHelpCard');
  var fsBtn=document.getElementById('catalogHelpFs');
  var desk=catalogHelpUseDesktopCard();
  var fs=document.body.classList.contains('catalog-help-fs');
  if(fsBtn){
    fsBtn.hidden=!desk||fs;
    fsBtn.style.display=(!desk||fs)?'none':'inline-flex';
  }
  if(card){
    card.hidden=!document.body.classList.contains('catalog-help-open')&&!fs;
    card.setAttribute('aria-hidden',card.hidden?'true':'false');
  }
  var kind=window._catalogHelpKind||'legend';
  document.body.classList.toggle('catalog-help-kind-guide',kind==='guide');
  document.body.classList.toggle('catalog-help-kind-legend',kind==='legend');
  var title=document.getElementById('catalogHelpTitle');
  if(title)title.textContent=kind==='guide'?'Guide':'Legend';
  var legend=document.getElementById('catalogHelpLegend');
  var user=document.getElementById('catalogHelpUser');
  var upd=document.getElementById('catalogHelpUpdate');
  var tab=window._catalogHelpTab||'user';
  if(legend)legend.hidden=kind!=='legend';
  if(user)user.hidden=!(kind==='guide'&&tab==='user');
  if(upd)upd.hidden=!(kind==='guide'&&tab==='update');
  var tu=document.getElementById('catalogHelpTabUser');
  var tv=document.getElementById('catalogHelpTabUpdate');
  if(tu)tu.setAttribute('aria-selected',tab==='user'?'true':'false');
  if(tv)tv.setAttribute('aria-selected',tab==='update'?'true':'false');
  var lg=document.getElementById('catalogLegendBtn');
  var gd=document.getElementById('catalogGuideBtn');
  var open=document.body.classList.contains('catalog-help-open')||document.body.classList.contains('catalog-help-fs');
  if(lg)lg.setAttribute('aria-pressed',open&&kind==='legend'?'true':'false');
  if(gd)gd.setAttribute('aria-pressed',open&&kind==='guide'?'true':'false');
}
function setCatalogHelpTab(tab){
  window._catalogHelpTab=tab==='update'?'update':'user';
  catalogHelpSyncChrome();
}
function catalogHelpEnterFs(){
  if(!catalogHelpUseDesktopCard())return;
  if(!document.body.classList.contains('catalog-help-open'))return;
  document.body.classList.add('catalog-help-fs');
  if(typeof parkSearchBehindOverlay==='function')parkSearchBehindOverlay();
  if(typeof syncViewportLock==='function')syncViewportLock();
  catalogHelpSyncChrome();
  catalogHelpLog('help-fs',{kind:window._catalogHelpKind||''});
}
function closeCatalogHelp(){
  document.body.classList.remove('catalog-help-open','catalog-help-fs','catalog-help-kind-guide','catalog-help-kind-legend');
  window._catalogHelpKind=null;
  var card=document.getElementById('catalogHelpCard');
  if(card){card.hidden=true;card.setAttribute('aria-hidden','true');}
  catalogHelpSyncChrome();
  if(typeof placeCatalogEdgeStack==='function')placeCatalogEdgeStack();
  if(typeof syncViewportLock==='function')syncViewportLock();
}
function catalogHelpBack(){
  if(catalogHelpUseDesktopCard()&&document.body.classList.contains('catalog-help-fs')){
    document.body.classList.remove('catalog-help-fs');
    catalogHelpSyncChrome();
    if(typeof syncViewportLock==='function')syncViewportLock();
    catalogHelpLog('help-back-fs',{kind:window._catalogHelpKind||''});
    return;
  }
  closeCatalogHelp();
  catalogHelpLog('help-back-close',{});
}
function openCatalogHelp(kind){
  kind=kind==='guide'?'guide':'legend';
  if(typeof closeChosenPreview==='function')try{closeChosenPreview({skipJumpExit:true});}catch(errCp){}
  if(typeof closeOverlay==='function')try{closeOverlay({skipScroll:true});}catch(errOv){}
  if(typeof parkSearchBehindOverlay==='function')parkSearchBehindOverlay();
  window._catalogHelpKind=kind;
  if(kind==='guide')window._catalogHelpTab='user';
  catalogHelpFillCopy();
  document.body.classList.add('catalog-help-open');
  if(!catalogHelpUseDesktopCard())document.body.classList.add('catalog-help-fs');
  else document.body.classList.remove('catalog-help-fs');
  catalogHelpSyncChrome();
  if(typeof placeCatalogEdgeStack==='function')placeCatalogEdgeStack();
  if(typeof syncViewportLock==='function')syncViewportLock();
  catalogHelpLog('help-open',{kind:kind,desktop:catalogHelpUseDesktopCard(),portable:!!window.CATALOG_PORTABLE,fs:document.body.classList.contains('catalog-help-fs')});
}
function toggleCatalogHelp(kind){
  var open=document.body.classList.contains('catalog-help-open')||document.body.classList.contains('catalog-help-fs');
  if(open&&window._catalogHelpKind===kind){closeCatalogHelp();return;}
  openCatalogHelp(kind);
}
window.catalogHelpUseDesktopCard=catalogHelpUseDesktopCard;
window.ensureCatalogEdgeStack=ensureCatalogEdgeStack;
window.placeCatalogEdgeStack=placeCatalogEdgeStack;
window.setCatalogHelpTab=setCatalogHelpTab;
window.catalogHelpEnterFs=catalogHelpEnterFs;
window.catalogHelpBack=catalogHelpBack;
window.closeCatalogHelp=closeCatalogHelp;
window.openCatalogHelp=openCatalogHelp;
window.toggleCatalogHelp=toggleCatalogHelp;
function placeCatalogJumpStack(){
'''

PLACE_DESK_OLD = (
    "  stack.style.left='auto';\n"
    "  stack.style.top='auto';\n"
    "}\n"
    "function bindCatalogJumpScroll(){\n"
)
PLACE_DESK_NEW = (
    "  stack.style.left='auto';\n"
    "  stack.style.top='auto';\n"
    "  if(typeof placeCatalogEdgeStack==='function')placeCatalogEdgeStack();\n"
    "}\n"
    "function bindCatalogJumpScroll(){\n"
)

PLACE_PORT_OLD = (
    "  if(typeof dbgPortableJumpGap==='function')dbgPortableJumpGap('placeJump');\n"
    "}\n"
    "function bindCatalogJumpScroll(){\n"
)
PLACE_PORT_NEW = (
    "  if(typeof placeCatalogEdgeStack==='function')placeCatalogEdgeStack();\n"
    "  if(typeof dbgPortableJumpGap==='function')dbgPortableJumpGap('placeJump');\n"
    "}\n"
    "function bindCatalogJumpScroll(){\n"
)

ENSURE_OLD = (
    "  if(typeof placeCatalogJumpStack==='function')placeCatalogJumpStack();\n"
    "  if(typeof bindCatalogJumpScroll==='function')bindCatalogJumpScroll();\n"
)
ENSURE_NEW = (
    "  if(typeof ensureCatalogEdgeStack==='function')ensureCatalogEdgeStack();\n"
    "  if(typeof placeCatalogJumpStack==='function')placeCatalogJumpStack();\n"
    "  if(typeof bindCatalogJumpScroll==='function')bindCatalogJumpScroll();\n"
)

OPEN_PREVIEW_OLD = (
    "function openChosenPreview(el){\n"
    "  if(!el)return;\n"
    "  if(typeof recordCardHit==='function')recordCardHit(el);\n"
)
OPEN_PREVIEW_NEW = (
    "function openChosenPreview(el){\n"
    "  if(!el)return;\n"
    "  if(typeof closeCatalogHelp==='function')closeCatalogHelp();\n"
    "  if(typeof recordCardHit==='function')recordCardHit(el);\n"
)

OPEN_OV_OLD = (
    "function openOverlay(el){\n"
    "  if(!el)return;\n"
    "  if(typeof bindCardFsEmbedScroll==='function')bindCardFsEmbedScroll();\n"
)
OPEN_OV_NEW = (
    "function openOverlay(el){\n"
    "  if(!el)return;\n"
    "  if(typeof closeCatalogHelp==='function')closeCatalogHelp();\n"
    "  if(typeof bindCardFsEmbedScroll==='function')bindCardFsEmbedScroll();\n"
)

FOCUS_OLD = (
    "function overlayFocusOpen(){\n"
    "  var b=document.body.classList;\n"
    "  return b.contains('gallery-open')||b.contains('img-focus-open')||b.contains('desc-focus-open')||b.contains('desc-reader-open')||b.contains('path-focus-open')||b.contains('path-reader-open');\n"
    "}\n"
)
FOCUS_NEW = (
    "function overlayFocusOpen(){\n"
    "  var b=document.body.classList;\n"
    "  return b.contains('gallery-open')||b.contains('img-focus-open')||b.contains('desc-focus-open')||b.contains('desc-reader-open')||b.contains('path-focus-open')||b.contains('path-reader-open')||b.contains('catalog-help-open')||b.contains('catalog-help-fs');\n"
    "}\n"
)

ESC_OLD = (
    "  if(document.body.classList.contains('path-focus-open')){\n"
    "    closePathFocus();\n"
    "    e.preventDefault();\n"
    "    return;\n"
    "  }\n"
    "  if(document.body.classList.contains('gallery-open')){\n"
)
ESC_NEW = (
    "  if(document.body.classList.contains('path-focus-open')){\n"
    "    closePathFocus();\n"
    "    e.preventDefault();\n"
    "    return;\n"
    "  }\n"
    "  if(document.body.classList.contains('catalog-help-open')||document.body.classList.contains('catalog-help-fs')){\n"
    "    if(typeof catalogHelpBack==='function')catalogHelpBack();\n"
    "    e.preventDefault();\n"
    "    return;\n"
    "  }\n"
    "  if(document.body.classList.contains('gallery-open')){\n"
)


def once(text, old, new, label, name, optional=False):
    n = text.count(old)
    if n == 1:
        return text.replace(old, new, 1)
    if optional and n == 0:
        print(f"  skip {name}: {label}")
        return text
    if n == 0 and new in text:
        print(f"  skip {name}: {label} already")
        return text
    raise SystemExit(f"{name}: {label} count={n} expected 1")


def patch(path: Path) -> None:
    raw = path.read_bytes()
    orig_size = len(raw)
    if not raw.rstrip().endswith(b"</html>"):
        raise SystemExit(f"{path.name}: missing </html> before patch")
    text = raw.decode("utf-8")
    name = path.name
    if MARKER in text and 'id="catalogEdgeStack"' in text:
        print("SKIP already patched", name)
        return

    text = once(text, CSS_JUMP, CSS_EDGE, "css-edge", name)
    text = once(text, HIDE_OLD, HIDE_NEW, "hide-jump", name)
    text = once(text, PORT_CSS_OLD, PORT_CSS_NEW, "port-css", name, optional=True)
    text = once(text, HTML_JUMP, HTML_EDGE, "html-edge", name)
    text = once(text, "function placeCatalogJumpStack(){\n", JS_HELP, "js-help", name)
    if "dbgPortableJumpGap" in text and PLACE_PORT_OLD in text:
        text = once(text, PLACE_PORT_OLD, PLACE_PORT_NEW, "place-port", name)
    else:
        text = once(text, PLACE_DESK_OLD, PLACE_DESK_NEW, "place-desk", name)
    text = once(text, ENSURE_OLD, ENSURE_NEW, "ensure", name)
    text = once(text, OPEN_PREVIEW_OLD, OPEN_PREVIEW_NEW, "preview", name)
    text = once(text, OPEN_OV_OLD, OPEN_OV_NEW, "overlay", name)
    text = once(text, FOCUS_OLD, FOCUS_NEW, "focus-open", name)
    text = once(text, ESC_OLD, ESC_NEW, "escape", name)

    if MARKER not in text:
        raise SystemExit(f"{name}: marker missing after patch")
    if 'id="catalogEdgeStack"' not in text or "function toggleCatalogHelp(" not in text:
        raise SystemExit(f"{name}: edge widgets missing")
    if not text.strip().endswith("</html>"):
        raise SystemExit(f"{name}: truncated, missing </html>")

    out = text.encode("utf-8")
    if orig_size > 4_000_000 and len(out) < orig_size * 0.9:
        raise SystemExit(f"{name}: size collapsed {orig_size} -> {len(out)}")
    if len(out) < orig_size:
        raise SystemExit(f"{name}: unexpectedly smaller {orig_size} -> {len(out)}")

    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_bytes(out)
    wrote = tmp.read_bytes()
    if len(wrote) != len(out):
        tmp.unlink()
        raise SystemExit(f"{name}: tmp size mismatch")
    if not wrote.rstrip().endswith(b"</html>"):
        tmp.unlink()
        raise SystemExit(f"{name}: tmp missing </html>")
    tmp.replace(path)
    print("OK", name, "bytes", len(out), "delta", len(out) - orig_size)


def main():
    for p in FILES:
        if not p.exists():
            raise SystemExit(f"missing {p}")
        patch(p)


if __name__ == "__main__":
    main()
