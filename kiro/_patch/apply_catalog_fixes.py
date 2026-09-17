#!/usr/bin/env python3
"""Apply embed/filter/chrome/favorites fixes to KIRO catalog builders."""
from pathlib import Path
import shutil

ART = Path("/home/phnx/KIRO/.kiro/specs/kontakt-workspace-drive-dirty-fix/artifacts")
FILES = [ART / "build-kontakt-catalog-html.sh", ART / "build-ds-catalog-html.sh"]


def must_replace(text, old, new, label, count=1):
    n = text.count(old)
    if n == 0:
        raise SystemExit(f"MISSING [{label}]")
    if count is not None and n != count:
        raise SystemExit(f"COUNT [{label}]: expected {count}, found {n}")
    return text.replace(old, new, count if count is not None else n)


def patch(text, name):
    # ---- CSS: side-by-side + collapsed chrome ----
    text = must_replace(
        text,
        """ body.search-mode:not(.kw-open) .search-chrome{grid-template-columns:1fr!important;grid-template-rows:none!important}
 body.search-mode:not(.kw-open) .search-col,body.search-mode:not(.kw-open) .filter-wrap{width:100%;max-width:100%;min-width:0}""",
        """ body.search-mode .search-chrome{grid-template-columns:minmax(0,1fr) minmax(0,1fr);grid-template-rows:none;align-items:start}
 body.search-mode .search-col,body.search-mode .filter-wrap{width:auto;max-width:100%;min-width:0}
 body.search-mode.menus-collapsed .search-chrome{grid-template-columns:auto auto;justify-content:start;gap:8px}
 body.search-mode.menus-collapsed .search-col,body.search-mode.menus-collapsed .filter-wrap{width:auto;flex:0 0 auto}""",
        "css-side-by-side",
    )

    text = must_replace(
        text,
        """  body.search-mode .search-chrome{grid-template-columns:1fr!important}""",
        """  body.search-mode .search-chrome{grid-template-columns:minmax(0,1fr) minmax(0,1fr)}
  body.search-mode.menus-collapsed .search-chrome{grid-template-columns:auto auto;justify-content:start}""",
        "css-mobile-side",
    )

    text = must_replace(
        text,
        """ body.search-chrome-collapsed .search-strip input,body.search-chrome-collapsed .search-strip-clear{display:none!important}""",
        """ body.search-chrome-collapsed .search-strip input,
 body.search-chrome-collapsed .search-strip-clear,
 body.search-chrome-collapsed .search-strip-fs,
 body.search-chrome-collapsed .search-only-scale{display:none!important}
 body.search-chrome-collapsed .search-strip{flex-wrap:nowrap;gap:.5rem;border-bottom:none;padding-left:0;padding-right:0;min-width:0;width:auto}
 .filter-wrap:not(.open)>.filter-top .clear-miss-btn,
 .filter-wrap:not(.open)>.filter-top .layout-edit-btn,
 .filter-wrap:not(.open)>.layout-presets,
 .filter-wrap:not(.open)>.filter-kw-tools{display:none!important}
 .filter-wrap:not(.open)>.filter-top{padding-bottom:0}
 .filter-wrap:not(.open) .filter-toggle{flex:0 0 auto;width:auto;max-width:none}
 .filter-kw-tools{display:flex;align-items:center;flex-wrap:wrap;gap:6px;width:100%;max-width:100%;box-sizing:border-box;padding:0 0 .5rem;min-width:0;flex:0 0 auto;position:relative;z-index:5}
 .filter-wrap.open>.filter-kw-tools{display:flex}
 .filter-wrap:not(.open)>.filter-kw-tools{display:none!important}
 .filter-kw-tools .layout-presets{padding:0;width:auto;flex:1 1 auto}
 .filter-kw-tools .clear-miss-btn,.filter-kw-tools .layout-edit-btn{flex:0 0 auto}""",
        "css-collapsed-chrome",
    )

    text = must_replace(
        text,
        """ body.search-mode:not(.kw-open) #searchCol,body.search-mode:not(.kw-open) #acShell{font-size:calc(var(--ui-base) * var(--search-ui-scale,1))}
 .search-only-scale{display:none;flex:0 0 auto;position:relative;z-index:6;min-width:0}
 body.search-mode:not(.kw-open):not(.search-chrome-collapsed):not(.ac-fs-open) .search-only-scale{display:flex}
 body.ac-fs-open .search-only-scale{display:none!important}
 .search-only-scale .ui-scale-step,.search-only-scale .ui-scale-readout{min-height:2.75rem}""",
        """ body.search-mode:not(.kw-open) #searchCol,body.search-mode:not(.kw-open) #acShell{
  font-size:calc(var(--ui-base) * var(--search-ui-scale,1));
 }
 body.search-mode:not(.kw-open) #searchCol :is(.search-strip input,.search-strip-clear,.search-strip-hide,.search-strip-fs,.ui-scale-step,.ui-scale-readout,.tap-add-btn),
 body.search-mode:not(.kw-open) #acShell :is(.ac-item,.ac-item .ac-note,.ac-item .ac-count,.ac-group-label,.ac-fs-close){
  font-size:1em;
 }
 body.search-mode:not(.kw-open) #searchCol :is(.search-strip,.search-strip input,.search-strip-clear,.search-strip-hide,.search-strip-fs,.ui-scale-step,.ui-scale-readout),
 body.search-mode:not(.kw-open) #acShell :is(.ac-item,.ac-fs-close){
  min-height:2.75em;
 }
 body.search-mode:not(.kw-open) #searchCol .search-strip-fs{min-width:2.75em}
 .search-only-scale{display:none;flex:0 0 auto;position:relative;z-index:6;min-width:0}
 body.search-mode:not(.kw-open):not(.search-chrome-collapsed):not(.ac-fs-open) .search-only-scale{display:flex}
 body.ac-fs-open .search-only-scale{display:none!important}
 .search-only-scale .ui-scale-step,.search-only-scale .ui-scale-readout{min-height:2.75em}""",
        "css-search-scale-em",
    )

    text = must_replace(
        text,
        """ .search-ac-shell.ac-fs .search-autocomplete{flex:1 1 auto;min-height:0;max-height:none;height:auto;overflow-x:hidden;overflow-y:auto;-webkit-overflow-scrolling:touch;touch-action:pan-y;overscroll-behavior:contain;border:0;width:100%;font-size:1rem}""",
        """ .search-ac-shell.ac-fs{touch-action:pan-y}
 .search-ac-shell.ac-fs .search-autocomplete{flex:1 1 0;min-height:0;max-height:none;height:auto;overflow-x:hidden;overflow-y:auto;-webkit-overflow-scrolling:touch;touch-action:pan-y;overscroll-behavior:contain;border:0;width:100%;font-size:1em}""",
        "css-ac-fs-scroll",
    )

    # ---- HTML: nest Keywords tools ----
    old_ft = (
        '<div class="filter-top"><button class="filter-toggle" id="filterToggle" onclick="toggleFilter()" aria-expanded="false">'
        '<span class="toggle-arrow">&#9660;</span> Keywords</button>'
        '<button type="button" class="clear-miss-btn" id="clearMissBtn" aria-pressed="false" title="When leaving the image gallery on a library outside the current Search hits, clear Search." onclick="event.preventDefault();event.stopPropagation();toggleClearOnMiss()">Clear on miss</button>'
        '<button type="button" class="layout-edit-btn" id="layoutEditBtn" aria-pressed="false" title="Drag menu edges to resize. Lock when finished." onclick="event.preventDefault();event.stopPropagation();toggleLayoutEdit()">Edit layout</button></div>'
        '<div class="layout-presets" id="layoutPresets">'
    )
    new_ft = (
        '<div class="filter-top"><button class="filter-toggle" id="filterToggle" onclick="toggleFilter()" aria-expanded="false">'
        '<span class="toggle-arrow">&#9660;</span> Keywords</button></div>'
        '<div class="filter-panel" id="filterPanel"><div class="filter-kw-tools" id="filterKwTools">'
        '<button type="button" class="clear-miss-btn" id="clearMissBtn" aria-pressed="false" title="When leaving the image gallery on a library outside the current Search hits, clear Search." onclick="event.preventDefault();event.stopPropagation();toggleClearOnMiss()">Clear on miss</button>'
        '<button type="button" class="layout-edit-btn" id="layoutEditBtn" aria-pressed="false" title="Drag menu edges to resize. Lock when finished." onclick="event.preventDefault();event.stopPropagation();toggleLayoutEdit()">Edit layout</button>'
        '<div class="layout-presets" id="layoutPresets">'
    )
    if old_ft not in text:
        raise SystemExit(f"MISSING filter-top HTML in {name}")
    text = text.replace(old_ft, new_ft, 1)

    old_panel_open = '</div></div><div class="filter-panel" id="filterPanel"><div class="mode-switch">'
    new_panel_open = '</div></div></div><div class="mode-switch">'
    if text.count(old_panel_open) != 1:
        raise SystemExit(f"filter-panel open count={text.count(old_panel_open)} in {name}")
    text = text.replace(old_panel_open, new_panel_open, 1)

    # ---- JS chrome ----
    text = must_replace(
        text,
        """function syncSearchHideBtn(){
  var collapsed=document.body.classList.contains('search-chrome-collapsed');
  document.querySelectorAll('.search-strip-hide').forEach(function(b){
    b.textContent=collapsed?'Show search':'Hide search';
    b.setAttribute('aria-expanded',collapsed?'false':'true');
  });
  var w=document.getElementById('filterWrap');
  var t=document.getElementById('filterToggle');
  document.body.classList.toggle('kw-open',!!(w&&w.classList.contains('open')));
  if(t)t.setAttribute('aria-expanded',w&&w.classList.contains('open')?'true':'false');
  if(window.syncLayoutStoreUi)window.syncLayoutStoreUi();
  if(window.syncSearchSplit)window.syncSearchSplit();
}""",
        """function syncSearchHideBtn(){
  var collapsed=document.body.classList.contains('search-chrome-collapsed');
  document.querySelectorAll('.search-strip-hide').forEach(function(b){
    b.textContent=collapsed?'Show search':'Hide search';
    b.setAttribute('aria-expanded',collapsed?'false':'true');
  });
  var w=document.getElementById('filterWrap');
  var t=document.getElementById('filterToggle');
  var kwOpen=!!(w&&w.classList.contains('open'));
  document.body.classList.toggle('kw-open',kwOpen);
  document.body.classList.toggle('menus-collapsed',!!collapsed&&!kwOpen);
  if(t)t.setAttribute('aria-expanded',kwOpen?'true':'false');
  if(window.syncLayoutStoreUi)window.syncLayoutStoreUi();
  if(window.syncSearchSplit)window.syncSearchSplit();
}""",
        "js-menus-collapsed",
    )

    text = must_replace(
        text,
        """function splitOn(){
  return document.body.classList.contains('search-mode')&&splitExpanded();
}""",
        """function splitOn(){
  return document.body.classList.contains('search-mode');
}""",
        "js-splitOn",
    )

    text = must_replace(
        text,
        """function collapsedKwMin(){
  var w=wrap(),r=rem();
  if(!w)return 6*r;
  return Math.max(measureRowMin(w.querySelector('.filter-top')),measureRowMin(w.querySelector('.layout-presets')),6*r);
}""",
        """function collapsedKwMin(){
  var w=wrap(),r=rem();
  if(!w)return 6*r;
  if(!w.classList.contains('open'))return Math.max(measureRowMin(w.querySelector('.filter-top')),4*r);
  return Math.max(measureRowMin(w.querySelector('.filter-top')),measureRowMin(w.querySelector('.filter-kw-tools')),measureRowMin(w.querySelector('.layout-presets')),6*r);
}""",
        "js-collapsedKwMin",
    )

    text = must_replace(
        text,
        """function collapsedKwMinH(){
  var w=wrap(),r=rem();
  if(!w)return 2.75*r;
  var h=0,ft=w.querySelector('.filter-top'),lp=w.querySelector('.layout-presets');
  if(ft)h+=ft.getBoundingClientRect().height;
  if(lp)h+=lp.getBoundingClientRect().height;
  return Math.max(h,2.75*r);
}""",
        """function collapsedKwMinH(){
  var w=wrap(),r=rem();
  if(!w)return 2.75*r;
  var h=0,ft=w.querySelector('.filter-top');
  if(ft)h+=ft.getBoundingClientRect().height;
  if(w.classList.contains('open')){
    var tools=w.querySelector('.filter-kw-tools'),lp=w.querySelector('.layout-presets');
    if(tools)h+=tools.getBoundingClientRect().height;
    else if(lp)h+=lp.getBoundingClientRect().height;
  }
  return Math.max(h,2.75*r);
}""",
        "js-collapsedKwMinH",
    )

    # ---- YouTube ----
    text = must_replace(
        text,
        """function cardSearchYtPlayUrl(id){
  if(!id)return '';
  var origin=(location.origin&&location.origin!=='null')?location.origin:'';
  var q='rel=0&modestbranding=1&playsinline=1';
  if(origin)q+='&origin='+encodeURIComponent(origin);
  return 'https://www.youtube-nocookie.com/embed/'+encodeURIComponent(id)+'?'+q;
}
function cardSearchYtEmbedUrl(popupUrl,query,id){
  if(id)return cardSearchYtPlayUrl(id);
  var from=cardSearchYtIdFromUrl(popupUrl);
  if(from)return cardSearchYtPlayUrl(from);
  return '';
}""",
        """function cardSearchYtPlayUrl(id){
  if(!id)return '';
  id=String(id).replace(/^\\s+|\\s+$/g,'');
  if(!/^[A-Za-z0-9_-]{6,}$/.test(id))return '';
  if(/^(videoseries|results|search)$/i.test(id))return '';
  var origin=(location.origin&&location.origin!=='null')?location.origin:'';
  var q='rel=0&modestbranding=1&playsinline=1&enablejsapi=1';
  if(origin)q+='&origin='+encodeURIComponent(origin);
  return 'https://www.youtube-nocookie.com/embed/'+encodeURIComponent(id)+'?'+q;
}
function cardSearchYtEmbedUrl(popupUrl,query,id){
  if(id)return cardSearchYtPlayUrl(id);
  var from=cardSearchYtIdFromUrl(popupUrl);
  if(from)return cardSearchYtPlayUrl(from);
  return '';
}
function cardSearchYtIsBadEmbedUrl(url){
  var s=String(url||'');
  if(!s||s==='about:blank')return true;
  if(/listType=search|\\/results\\?|\\/watch\\?|\\/embed\\/videoseries/i.test(s))return true;
  if(!/youtube-nocookie\\.com\\/embed\\/[A-Za-z0-9_-]{6,}/.test(s))return true;
  return false;
}""",
        "js-yt-play-url",
    )

    # ---- Library-only helpers (hard filter) ----
    old_lib = """function catalogSearchExtra(){return (window.CATALOG_NS==='ds')?'decent sampler':'kontakt';}
function stripCatalogExtra(s){
  return String(s||'').replace(/\\s+decent\\s+sampler(?:\\s+library)?\\s*$/i,'').replace(/\\s+kontakt(?:\\s+library)?\\s*$/i,'').replace(/\\s+vst(?:\\s+instrument)?\\s*$/i,'').replace(/^\\s+|\\s+$/g,'');
}
function libraryQueryVariants(){
  var stop={the:1,and:1,for:1,from:1,with:1,this:1,that:1,a:1,an:1,of:1,to:1,in:1,on:1,by:1,or:1,is:1,at:1,as:1,vs:1,http:1,https:1,www:1,com:1,org:1,net:1,search:1,query:1,results:1,vst:1,instrument:1,library:1,kontakt:1,decent:1,sampler:1};
  var name=String(cardSearchState.name||'').replace(/^\\s+|\\s+$/g,'');
  var q=stripCatalogExtra(cardSearchState.query||'');
  var toks=(name+' '+q).toLowerCase().replace(/[^a-z0-9]+/g,' ').split(' ').filter(function(w){return w.length>2&&!stop[w];});
  toks.sort(function(a,b){return b.length-a.length;});
  var out=[];
  function add(s){
    s=String(s||'').replace(/^\\s+|\\s+$/g,'');
    if(!s)return;
    var key=s.toLowerCase();
    if(out.some(function(x){return x.toLowerCase()===key;}))return;
    out.push(s);
  }
  add(name);
  add(q);
  toks.forEach(add);
  return out;
}
function librarySearchTokens(){
  var name=cardSearchState.name||'';
  var q=cardSearchState.query||'';
  var card=document.querySelector('.entry.selected')||lastViewedEntry;
  var kw=card&&card.getAttribute?((card.getAttribute('data-kw')||'')+' '+(card.getAttribute('data-gear')||'')):'';
  var stop={the:1,and:1,for:1,from:1,with:1,this:1,that:1,a:1,an:1,of:1,to:1,in:1,on:1,by:1,or:1,is:1,at:1,as:1,vs:1,http:1,https:1,www:1,com:1,org:1,net:1,search:1,query:1,results:1};
  return (name+' '+q+' '+kw).toLowerCase().replace(/[^a-z0-9]+/g,' ').split(' ').filter(function(w){return w.length>1&&!stop[w];});
}
function scoreSearchHay(text,tokens){
  var hay=String(text||'').toLowerCase();
  var score=0,hits=0;
  (tokens||[]).forEach(function(t){
    if(hay.indexOf(t)>=0){hits++;score+=t.length>=4?3:1;}
  });
  return {score:score,hits:hits};
}"""

    new_lib = """function catalogSearchExtra(){return (window.CATALOG_NS==='ds')?'decent sampler':'kontakt';}
function catalogFileHint(){return (window.CATALOG_NS==='ds')?'dspreset':'nki';}
function stripCatalogExtra(s){
  return String(s||'').replace(/\\s+decent\\s+sampler(?:\\s+library)?\\s*$/i,'').replace(/\\s+kontakt(?:\\s+library)?\\s*$/i,'').replace(/\\s+vst(?:\\s+instrument)?\\s*$/i,'').replace(/^\\s+|\\s+$/g,'');
}
function libraryDisplayName(){
  return String(cardSearchState.name||stripCatalogExtra(cardSearchState.query||'')||'').replace(/^\\s+|\\s+$/g,'');
}
function libraryNameTokens(){
  var stop={the:1,and:1,for:1,from:1,with:1,this:1,that:1,a:1,an:1,of:1,to:1,in:1,on:1,by:1,or:1,is:1,at:1,as:1,vs:1,http:1,https:1,www:1,com:1,org:1,net:1,search:1,query:1,results:1,vst:1,instrument:1,library:1,kontakt:1,decent:1,sampler:1,free:1,plus:1,edition:1,vol:1,volume:1,nki:1,dspreset:1};
  var name=libraryDisplayName().toLowerCase().replace(/[^a-z0-9]+/g,' ');
  return name.split(' ').filter(function(w){return w.length>2&&!stop[w];});
}
function libraryQueryVariants(){
  var name=libraryDisplayName();
  var extra=catalogSearchExtra();
  var hint=catalogFileHint();
  var out=[];
  function add(s){
    s=String(s||'').replace(/^\\s+|\\s+$/g,'');
    if(!s)return;
    var key=s.toLowerCase();
    if(out.some(function(x){return x.toLowerCase()===key;}))return;
    out.push(s);
  }
  if(name){
    add('"'+name+'" '+extra);
    add('"'+name+'" sample library');
    add('"'+name+'" '+hint);
    add(name+' '+extra+' sample library');
    add(name+' '+extra);
  }
  return out;
}
function librarySearchTokens(){return libraryNameTokens();}
function scoreSearchHay(text,tokens){
  var hay=String(text||'').toLowerCase();
  var score=0,hits=0;
  (tokens||[]).forEach(function(t){
    if(hay.indexOf(t)>=0){hits++;score+=t.length>=4?3:1;}
  });
  return {score:score,hits:hits};
}
function libraryProductContext(hay){
  return /kontakt|decent\\s*sampler|sample\\s*library|\\bnki\\b|\\bdspreset\\b|nks|native\\s*instruments|vst|plugin|preset|gumroad|itch\\.io|patch\\s*library|instrument\\s*library|walkthrough|manual|gui|cover\\s*art/.test(String(hay||'').toLowerCase());
}
function isLibraryRelevantHit(hay,opts){
  opts=opts||{};
  hay=String(hay||'').toLowerCase();
  if(!hay)return false;
  if(/cia\\.gov|reading room|soviet activities|arctic and antarctic|histolog|microscope|patholog|anatomy atlas|tire\\b|tyre\\b/.test(hay))return false;
  var name=libraryDisplayName().toLowerCase();
  var toks=libraryNameTokens();
  if(!toks.length&&!name)return false;
  var nameHit=!!(name&&hay.indexOf(name)>=0);
  var sc=scoreSearchHay(hay,toks);
  var need=toks.length<=1?1:toks.length;
  // Require ALL distinctive name tokens in title/snippet/url — blocks CIA/arctic for "Cloud Supply"
  if(!(nameHit||sc.hits>=need))return false;
  if(opts.requireProduct===false)return true;
  if(libraryProductContext(hay))return true;
  if(nameHit&&toks.length>=2)return true;
  if(/wikipedia\\.org|wikimedia\\.org|commons\\.wikimedia|cia\\.gov/.test(hay)&&!libraryProductContext(hay))return false;
  return nameHit&&sc.hits>=need;
}"""
    if old_lib not in text:
        raise SystemExit(f"MISSING library helpers in {name}")
    text = text.replace(old_lib, new_lib, 1)

    text = must_replace(
        text,
        """function rankSearchItems(items,textFn){
  var tokens=librarySearchTokens();
  var nameToks=String(cardSearchState.name||'').toLowerCase().replace(/[^a-z0-9]+/g,' ').split(' ').filter(function(w){return w.length>1;});
  return (items||[]).map(function(it){
    var hay=textFn?textFn(it):((it.title||'')+' '+(it.snippet||'')+' '+(it.author||'')+' '+(it.url||''));
    var sc=scoreSearchHay(hay,tokens);
    var name=scoreSearchHay(hay,nameToks);
    it._score=sc.score+(name.hits?name.score*2:0);
    it._hits=sc.hits;
    it._nameHits=name.hits;
    return it;
  }).sort(function(a,b){return (b._score-a._score)||(b._nameHits-a._nameHits)||(b._hits-a._hits);});
}""",
        """function rankSearchItems(items,textFn,opts){
  opts=opts||{};
  var tokens=libraryNameTokens();
  var name=libraryDisplayName().toLowerCase();
  return (items||[]).map(function(it){
    var hay=textFn?textFn(it):((it.title||'')+' '+(it.snippet||'')+' '+(it.author||'')+' '+(it.url||''));
    var sc=scoreSearchHay(hay,tokens);
    var nameHit=name&&String(hay).toLowerCase().indexOf(name)>=0?1:0;
    var prod=libraryProductContext(hay)?1:0;
    it._hay=hay;
    it._score=sc.score+(nameHit?8:0)+(prod?10:0);
    it._hits=sc.hits;
    it._nameHits=nameHit?Math.max(1,sc.hits):sc.hits;
    it._relevant=isLibraryRelevantHit(hay,opts);
    return it;
  }).filter(function(it){return !!it._relevant;}).sort(function(a,b){return (b._score-a._score)||(b._nameHits-a._nameHits)||(b._hits-a._hits);});
}""",
        "js-rank",
    )

    text = must_replace(
        text,
        """function setCardYtFrame(id){
  var frame=document.getElementById('cardSearchFrame');
  var fallback=document.getElementById('cardSearchFallback');
  var url=cardSearchYtPlayUrl(id);
  if(!frame||!url)return false;
  if(fallback)fallback.classList.remove('open');
  cardSearchState.ytId=id;
  cardSearchState.embedUrl=url;
  cardSearchState.history=[url];
  frame.classList.remove('is-hidden');
  frame.style.display='';
  frame.setAttribute('referrerpolicy','strict-origin-when-cross-origin');
  frame.setAttribute('allow','accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; fullscreen');
  frame.setAttribute('allowfullscreen','');
  frame.src=url;
  showCardSearchFrame(true);
  return true;
}""",
        """function setCardYtFrame(id){
  var frame=document.getElementById('cardSearchFrame');
  var fallback=document.getElementById('cardSearchFallback');
  var url=cardSearchYtPlayUrl(id);
  if(!frame||!url||cardSearchYtIsBadEmbedUrl(url))return false;
  if(fallback)fallback.classList.remove('open');
  cardSearchState.ytId=id;
  cardSearchState.embedUrl=url;
  cardSearchState.history=[url];
  frame.classList.remove('is-hidden');
  frame.style.display='';
  frame.setAttribute('referrerpolicy','strict-origin-when-cross-origin');
  frame.setAttribute('allow','accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; fullscreen');
  frame.setAttribute('allowfullscreen','');
  try{frame.referrerPolicy='strict-origin-when-cross-origin';}catch(err){}
  frame.src=url;
  showCardSearchFrame(true);
  return true;
}
function cardSearchYtTryNext(reason){
  var items=cardSearchState.ytItems||[];
  if(!items.length)return false;
  var cur=cardSearchState.ytId||'';
  var tried=cardSearchState._ytTried||{};
  if(cur)tried[cur]=1;
  cardSearchState._ytTried=tried;
  for(var i=0;i<items.length;i++){
    var it=items[i];
    if(!it||!it.id||tried[it.id])continue;
    if(setCardYtFrame(it.id)){
      renderCardYtList(items,it.id);
      return true;
    }
    tried[it.id]=1;
  }
  showCardSearchFrame(false);
  cardSearchShowStatus('YouTube could not play an embed'+(reason?(' ('+reason+')'):'')+' for “'+(cardSearchState.name||'this library')+'”. Open in a popup instead.');
  return false;
}
(function(){
  if(window._ytErrBound)return;
  window._ytErrBound=1;
  window.addEventListener('message',function(e){
    try{
      var host=String((e&&e.origin)||'');
      if(host.indexOf('youtube.com')<0&&host.indexOf('youtube-nocookie.com')<0)return;
      var data=e.data;
      if(typeof data==='string'){
        try{data=JSON.parse(data);}catch(err){return;}
      }
      if(!data||typeof data!=='object')return;
      var code=null;
      if(data.event==='onError')code=data.info;
      else if(data.info&&typeof data.info==='object'&&data.info.event==='onError')code=data.info.info;
      if(code==null)return;
      code=Number(code);
      if(code===153||code===150||code===101||code===100||code===2||code===5){
        if(cardSearchState&&cardSearchState.type==='yt')cardSearchYtTryNext('error '+code);
      }
    }catch(err){}
  });
})();""",
        "js-yt-frame-153",
    )

    text = must_replace(
        text,
        """  var apis=[
    {kind:'piped',url:'https://pipedapi.ducks.party/search?q='+encodeURIComponent(q)+'&filter=videos'},
    {kind:'piped',url:'https://api.piped.private.coffee/search?q='+encodeURIComponent(q)+'&filter=videos'},
    {kind:'invidious',url:'https://inv.nadeko.net/api/v1/search?q='+encodeURIComponent(q)+'&type=video'}
  ];
  function finish(items){
    var ranked=rankSearchItems(items,function(it){return (it.title||'')+' '+(it.author||'');});
    if(!ranked.length)ranked=items||[];
    ranked=ranked.slice(0,12);
    cardSearchState.ytItems=ranked;
    if(!ranked.length){
      showCardSearchFrame(false);
      renderCardYtList([]);
      cardSearchShowStatus('No embeddable YouTube videos for “'+(cardSearchState.name||q||'this library')+'”. Open the full search in a popup.');
      return;
    }
    var pick=ranked[0];
    if(known){
      var hit=ranked.filter(function(it){return it.id===known;})[0];
      if(hit)pick=hit;
    }
    setCardYtFrame(pick.id);
    renderCardYtList(ranked,pick.id);
    syncCardSearchLayout();
  }""",
        """  var apis=[
    {kind:'piped',url:'https://pipedapi.ducks.party/search?q='+encodeURIComponent(q)+'&filter=videos'},
    {kind:'piped',url:'https://api.piped.private.coffee/search?q='+encodeURIComponent(q)+'&filter=videos'},
    {kind:'piped',url:'https://pipedapi.adminforge.de/search?q='+encodeURIComponent(q)+'&filter=videos'}
  ];
  function finish(items){
    var ranked=rankSearchItems(items,function(it){return (it.title||'')+' '+(it.author||'');},{requireProduct:false});
    ranked=(ranked.length?ranked:(items||[])).filter(function(it){
      return it&&it.id&&cardSearchYtPlayUrl(it.id)&&!cardSearchYtIsBadEmbedUrl(cardSearchYtPlayUrl(it.id));
    }).slice(0,12);
    cardSearchState.ytItems=ranked;
    cardSearchState._ytTried={};
    if(!ranked.length){
      showCardSearchFrame(false);
      renderCardYtList([]);
      cardSearchShowStatus('No embeddable YouTube videos for “'+(cardSearchState.name||q||'this library')+'”. Open the full search in a popup.');
      return;
    }
    var pick=ranked[0];
    if(known){
      var hit=ranked.filter(function(it){return it.id===known;})[0];
      if(hit)pick=hit;
    }
    if(!setCardYtFrame(pick.id))cardSearchYtTryNext('bad id');
    renderCardYtList(ranked,cardSearchState.ytId||pick.id);
    syncCardSearchLayout();
  }""",
        "js-yt-apis",
    )

    text = must_replace(
        text,
        """  rows=rankSearchItems(rows,function(r){return (r.title||'')+' '+(r.snippet||'')+' '+(r.url||'');}).filter(function(r){
    var hay=((r.title||'')+' '+(r.url||'')).toLowerCase();
    if(/duckduckgo|about duck/.test(hay)&&!(r._nameHits>0))return false;
    return true;
  }).slice(0,16);
  cardSearchState.results=rows;
  cardSearchState.view='results';
  if(!rows.length){
    cardSearchShowStatus('No embedded results for “'+(cardSearchState.query||'this search')+'”. Open the full search in a popup.');
    return;
  }""",
        """  rows=rankSearchItems(rows,function(r){return (r.title||'')+' '+(r.snippet||'')+' '+(r.url||'');}).filter(function(r){
    var hay=((r.title||'')+' '+(r.snippet||'')+' '+(r.url||'')).toLowerCase();
    if(/duckduckgo|about duck|cia\\.gov|soviet activities|arctic and antarctic/.test(hay))return false;
    return true;
  }).slice(0,16);
  cardSearchState.results=rows;
  cardSearchState.view='results';
  if(!rows.length){
    cardSearchShowStatus('No library-related web results for “'+(cardSearchState.name||cardSearchState.query||'this library')+'”. Open the full search in a popup if you want broader hits.');
    return;
  }""",
        "js-web-filter",
    )

    text = must_replace(
        text,
        """function loadCardWebSearch(query){
  var variants=libraryQueryVariants();
  var q=stripCatalogExtra(query||cardSearchState.query||'');
  if(q) variants=[q].concat(variants.filter(function(v){return v.toLowerCase()!==q.toLowerCase();}));
  cardSearchState.view='results';
  cardSearchState.history=['results'];
  showCardSearchFrame(false);
  cardSearchShowStatus('Searching…',false);
  if(!variants.length){cardSearchShowStatus('No search query for this library.');return;}""",
        """function loadCardWebSearch(query){
  var variants=libraryQueryVariants();
  cardSearchState.view='results';
  cardSearchState.history=['results'];
  showCardSearchFrame(false);
  cardSearchShowStatus('Searching…',false);
  if(!variants.length){cardSearchShowStatus('No search query for this library.');return;}""",
        "js-web-load",
    )

    text = must_replace(
        text,
        """  function finish(items){
    items=dedupe(items);
    var ranked=rankSearchItems(items,function(it){return (it.title||'')+' '+(it.url||'');}).map(function(it){
      var hay=((it.title||'')+' '+(it.url||'')).toLowerCase();
      if(/cover|artwork|screenshot|gui|plugin|kontakt|decent|library|preset/.test(hay))it._score+=6;
      return it;
    }).sort(function(a,b){return (b._score-a._score);});
    cardSearchRenderImages((ranked.length?ranked:items).slice(0,16));
  }""",
        """  function finish(items){
    items=dedupe(items);
    var ranked=rankSearchItems(items,function(it){return (it.title||'')+' '+(it.url||'');}).map(function(it){
      var hay=((it.title||'')+' '+(it.url||'')).toLowerCase();
      if(/cover|artwork|screenshot|gui|plugin|kontakt|decent|library|preset/.test(hay))it._score+=6;
      if(/histolog|microscope|tire|tyre|anatomy|cell\\b|patholog|diagram of|cia\\.gov/.test(hay))it._score-=50;
      return it;
    }).filter(function(it){
      var hay=((it.title||'')+' '+(it.url||'')).toLowerCase();
      if(/histolog|microscope|tire|tyre|anatomy|patholog|cia\\.gov/.test(hay))return false;
      return true;
    }).sort(function(a,b){return (b._score-a._score);});
    cardSearchRenderImages(ranked.slice(0,16));
  }""",
        "js-img-filter",
    )

    text = must_replace(
        text,
        """function loadCardImageSearch(query){
  var variants=libraryQueryVariants();
  var q=stripCatalogExtra(query||cardSearchState.query||'');
  if(q) variants=[q].concat(variants.filter(function(v){return v.toLowerCase()!==q.toLowerCase();}));
  cardSearchState.view='grid';
  cardSearchState.history=['grid'];
  showCardSearchFrame(false);
  cardSearchShowStatus('Loading images…',false);
  if(!variants.length){cardSearchShowStatus('No image query for this library.');return;}""",
        """function loadCardImageSearch(query){
  var variants=libraryQueryVariants();
  cardSearchState.view='grid';
  cardSearchState.history=['grid'];
  showCardSearchFrame(false);
  cardSearchShowStatus('Loading images…',false);
  if(!variants.length){cardSearchShowStatus('No image query for this library.');return;}""",
        "js-img-load",
    )

    text = must_replace(
        text,
        """  if(!items||!items.length){
    cardSearchShowStatus('No embedded images for “'+(cardSearchState.query||'this search')+'”. Open the full image search in a popup.');
    return;
  }""",
        """  if(!items||!items.length){
    cardSearchShowStatus('No library-related images for “'+(cardSearchState.name||cardSearchState.query||'this library')+'”. Open the full image search in a popup if you want broader hits.');
    return;
  }""",
        "js-img-empty",
    )

    text = must_replace(
        text,
        """  document.querySelectorAll('.ui-scale-choice').forEach(function(b){
    b.classList.toggle('is-active',parseInt(b.getAttribute('data-scale'),10)===pct);
  });
}
function reapplyLayoutAfterScale(){""",
        """  document.querySelectorAll('#uiScalePop .ui-scale-choice').forEach(function(b){
    b.classList.toggle('is-active',parseInt(b.getAttribute('data-scale'),10)===pct);
  });
}
function reapplyLayoutAfterScale(){""",
        "js-ui-scale-scope",
    )

    if 'catalog-ui-scale-kontakt' in text:
        text = must_replace(
            text,
            """<script>(function(){var k="catalog-ui-scale-kontakt";var s=[50,67,75,80,90,100,110,125,133,140,150,175,200,250,300];var n=100;try{var v=parseInt(localStorage.getItem(k)||"",10);if(s.indexOf(v)>=0)n=v;}catch(e){}var r=document.documentElement;r.style.setProperty("--ui-scale",String(n/100));r.setAttribute("data-ui-scale",String(n));})();</script>""",
            """<script>(function(){var s=[50,67,75,80,90,100,110,125,133,140,150,175,200,250,300];var r=document.documentElement;var n=100;try{var v=parseInt(localStorage.getItem("catalog-ui-scale-kontakt")||"",10);if(s.indexOf(v)>=0)n=v;}catch(e){}r.style.setProperty("--ui-scale",String(n/100));r.setAttribute("data-ui-scale",String(n));var sn=100;try{var sv=parseInt(localStorage.getItem("catalog-search-only-ui-scale-kontakt")||"",10);if(s.indexOf(sv)>=0)sn=sv;}catch(e){}r.style.setProperty("--search-ui-scale",String(sn/100));r.setAttribute("data-search-ui-scale",String(sn));})();</script>""",
            "fouc-kontakt",
        )
    if 'catalog-ui-scale-ds' in text:
        text = must_replace(
            text,
            """<script>(function(){var k="catalog-ui-scale-ds";var s=[50,67,75,80,90,100,110,125,133,140,150,175,200,250,300];var n=100;try{var v=parseInt(localStorage.getItem(k)||"",10);if(s.indexOf(v)>=0)n=v;}catch(e){}var r=document.documentElement;r.style.setProperty("--ui-scale",String(n/100));r.setAttribute("data-ui-scale",String(n));})();</script>""",
            """<script>(function(){var s=[50,67,75,80,90,100,110,125,133,140,150,175,200,250,300];var r=document.documentElement;var n=100;try{var v=parseInt(localStorage.getItem("catalog-ui-scale-ds")||"",10);if(s.indexOf(v)>=0)n=v;}catch(e){}r.style.setProperty("--ui-scale",String(n/100));r.setAttribute("data-ui-scale",String(n));var sn=100;try{var sv=parseInt(localStorage.getItem("catalog-search-only-ui-scale-ds")||"",10);if(s.indexOf(sv)>=0)sn=sv;}catch(e){}r.style.setProperty("--search-ui-scale",String(sn/100));r.setAttribute("data-search-ui-scale",String(sn));})();</script>""",
            "fouc-ds",
        )

    # ---- Favorites: nested category, do not auto-open for favs alone ----
    text = must_replace(
        text,
        """ function favAcHtml(names,kws){
   var html='';
   if(names&&names.length){
     html+='<div class="ac-group-label ac-fav-label">Favorites</div>';
     names.forEach(function(o){
       html+='<div class="ac-item fav-rec" data-cat="fav" onclick="pickAc(\\''+jsStr(o.label||o.k)+'\\')"><span class="ac-label">'+htmlStr(o.label||o.k)+acNoteIcon(o)+'</span></div>';
     });
   }
   if(kws&&kws.length){
     var anyFav=kws.some(function(o){return o.favHits>0;});
     var anyCommit=kws.some(function(o){return o.searchCommits>0;});
     var lab=anyFav&&anyCommit?'Keywords':(anyCommit?'Searched keywords':'Favorite keywords');
     html+='<div class="ac-group-label ac-fav-label">'+lab+'</div>';
     kws.forEach(function(o){
       var cls='ac-item'+(o.favHits>0?' fav-rec':'');
       html+='<div class="'+cls+'" data-cat="'+(o.cat||'other')+'" onclick="pickAc(\\''+jsStr(o.label||o.k)+'\\')"><span class="ac-label">'+htmlStr(o.label||o.k)+'</span> <span class="ac-count">'+o.c+'</span></div>';
     });
   }
   return html;
 }
 function showAc(q){
   if(document.body.classList.contains('search-extras-collapsed')){if(acList){acList.classList.remove('open');acList.innerHTML='';}return;}
   if(typeof overlayCoversSearch==='function'&&overlayCoversSearch()){if(acList){acList.classList.remove('open');acList.innerHTML='';}if(typeof window.hideSearchAc==='function')window.hideSearchAc();return;}
   var src=suggestFromHits();
   var list=q?src.filter(function(o){return o.k.indexOf(q)>=0||(o.label&&o.label.toLowerCase().indexOf(q)>=0);}):src;
   if(q&&q.length>=2){
     suggestPatchNames(q,currentHits(),16).forEach(function(o){
       if(!list.some(function(x){return x.k===o.k;}))list.push(o);
     });
   }
   var favEls=favEntries();
   var favs=suggestFavs();
   var ranked=null;
   var favHtml='';
   if(!q){
     ranked=suggestRankedKws(favEls,favs.map(function(o){return o.label||o.k;}));
     favHtml=favAcHtml(favs,ranked);
   }else{
     favs.forEach(function(o){
       var lab=(o.label||o.k||'').toLowerCase();
       if(lab.indexOf(q)<0)return;
       var hit=list.filter(function(x){return (x.label||x.k)===o.label||x.k===o.k;})[0];
       if(hit)hit.isFav=1;
     });
   }
   var html=favHtml+((!q&&(favs.length||(ranked&&ranked.length)))?'':acHtml(list,40,!q));
   acList.innerHTML=html;acList.classList.toggle('open',html.length>0);
   if(window.syncSearchSplit)window.syncSearchSplit();
 }""",
        """ function favAcHtml(names,kws){
   var html='';
   var favNames=names||[];
   var favOnly=(kws||[]).filter(function(o){return o&&o.favHits>0;});
   var commitOnly=(kws||[]).filter(function(o){return o&&o.searchCommits>0&&!(o.favHits>0);});
   if(favNames.length||favOnly.length){
     html+='<div class="ac-group-label ac-fav-label">Favorites</div>';
     favNames.forEach(function(o){
       html+='<div class="ac-item fav-rec" data-cat="fav" onclick="pickAc(\\''+jsStr(o.label||o.k)+'\\')"><span class="ac-label">'+htmlStr(o.label||o.k)+acNoteIcon(o)+'</span></div>';
     });
     favOnly.forEach(function(o){
       html+='<div class="ac-item fav-rec" data-cat="'+(o.cat||'other')+'" onclick="pickAc(\\''+jsStr(o.label||o.k)+'\\')"><span class="ac-label">'+htmlStr(o.label||o.k)+'</span> <span class="ac-count">'+o.c+'</span></div>';
     });
   }
   if(commitOnly.length){
     html+='<div class="ac-group-label">Searched keywords</div>';
     commitOnly.forEach(function(o){
       html+='<div class="ac-item" data-cat="'+(o.cat||'other')+'" onclick="pickAc(\\''+jsStr(o.label||o.k)+'\\')"><span class="ac-label">'+htmlStr(o.label||o.k)+'</span> <span class="ac-count">'+o.c+'</span></div>';
     });
   }
   return html;
 }
 function showAc(q,opts){
   opts=opts||{};
   if(document.body.classList.contains('search-extras-collapsed')){if(acList){acList.classList.remove('open');acList.innerHTML='';}return;}
   if(typeof overlayCoversSearch==='function'&&overlayCoversSearch()){if(acList){acList.classList.remove('open');acList.innerHTML='';}if(typeof window.hideSearchAc==='function')window.hideSearchAc();return;}
   var src=suggestFromHits();
   var list=q?src.filter(function(o){return o.k.indexOf(q)>=0||(o.label&&o.label.toLowerCase().indexOf(q)>=0);}):src;
   if(q&&q.length>=2){
     suggestPatchNames(q,currentHits(),16).forEach(function(o){
       if(!list.some(function(x){return x.k===o.k;}))list.push(o);
     });
   }
   var favEls=favEntries();
   var favs=suggestFavs();
   var ranked=suggestRankedKws(favEls,favs.map(function(o){return o.label||o.k;}));
   if(q){
     favs=favs.filter(function(o){return ((o.label||o.k||'').toLowerCase()).indexOf(q)>=0;});
     ranked=ranked.filter(function(o){return ((o.label||o.k||'').toLowerCase()).indexOf(q)>=0;});
     favs.forEach(function(o){
       var hit=list.filter(function(x){return (x.label||x.k)===o.label||x.k===o.k;})[0];
       if(hit)hit.isFav=1;
     });
   }
   var mainHtml=acHtml(list,40,!q);
   var favHtml=favAcHtml(favs,ranked);
   var hasMain=mainHtml.length>0;
   var hasCommits=(ranked||[]).some(function(o){return o&&o.searchCommits>0;});
   // Never open the dropdown solely to dump favorite suggestions.
   if(!q&&!hasMain&&!hasCommits&&!opts.force){
     if(acList){acList.innerHTML='';acList.classList.remove('open');}
     if(window.syncSearchSplit)window.syncSearchSplit();
     return;
   }
   var html=(hasMain||hasCommits||!!q||opts.force)?(favHtml+mainHtml):'';
   acList.innerHTML=html;acList.classList.toggle('open',html.length>0);
   if(window.syncSearchSplit)window.syncSearchSplit();
 }""",
        "js-fav-ac",
    )

    # toggleFav: refresh ac only if already open
    text = must_replace(
        text,
        """  if(typeof window.showAc==='function'&&!document.body.classList.contains('search-extras-collapsed')){
    var si=document.getElementById('searchInput');
    window.showAc(si?si.value.trim().toLowerCase():'');
  }""",
        """  if(typeof window.showAc==='function'&&!document.body.classList.contains('search-extras-collapsed')){
    var ac=document.getElementById('acList');
    if(ac&&ac.classList.contains('open')){
      var si=document.getElementById('searchInput');
      window.showAc(si?si.value.trim().toLowerCase():'',{force:true});
    }
  }""",
        "js-toggleFav-ac",
    )

    return text


def main():
    for f in FILES:
        bak = f.with_suffix(f.suffix + ".bak-resume")
        if not bak.exists():
            shutil.copy2(f, bak)
        raw = f.read_text()
        if "isLibraryRelevantHit" in raw and "menus-collapsed" in raw and "cardSearchYtTryNext" in raw:
            print("already patched?", f.name)
            # still allow re-run from bak if incomplete
        out = patch(raw, f.name)
        f.write_text(out)
        print("patched", f.name, "bytes", len(out))
        for needle in [
            "isLibraryRelevantHit",
            "cardSearchYtTryNext",
            "menus-collapsed",
            "Never open the dropdown solely",
            "No library-related web results",
            "No library-related images",
        ]:
            if needle not in out:
                raise SystemExit(f"VERIFY FAIL {f.name}: missing {needle}")
    print("OK")


if __name__ == "__main__":
    main()
