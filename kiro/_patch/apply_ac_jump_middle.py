#!/usr/bin/env python3
"""AC category jump + portrait Middle display layout. Sync six catalog files."""
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


def add_indent(s, n=1):
    pad = " " * n
    return "\n".join((pad + line) if line.strip() else line for line in s.split("\n"))


def sub(text, old, new, label, optional=False):
    n = text.count(old)
    if n == 1:
        return text.replace(old, new, 1)
    if n > 1:
        raise SystemExit(f"{label}: {n} matches")
    if new in text:
        print(f"  skip {label} (already)")
        return text
    for i in range(1, 9):
        oldi, newi = add_indent(old, i), add_indent(new, i)
        ni = text.count(oldi)
        if ni == 1:
            return text.replace(oldi, newi, 1)
        if ni > 1:
            raise SystemExit(f"{label}: {ni} matches (indent {i})")
        if ni == 0 and newi in text:
            print(f"  skip {label} (already)")
            return text
    if optional:
        print(f"  skip {label}")
        return text
    raise SystemExit(f"{label}: not found")


def once(text, old, new, label, path=None):
    n = text.count(old)
    if n == 1:
        return text.replace(old, new, 1)
    if n == 0 and new in text:
        print(f"  skip {label} (already)")
        return text
    for i in range(1, 9):
        oldi, newi = add_indent(old, i), add_indent(new, i)
        ni = text.count(oldi)
        if ni == 1:
            return text.replace(oldi, newi, 1)
        if ni == 0 and newi in text:
            print(f"  skip {label} (already)")
            return text
        if ni > 1:
            raise SystemExit(f"{label}: {ni} matches (indent {i})")
    prefix = f"{path.name}: " if path else ""
    raise SystemExit(f"{prefix}{label}: count={n} expected 1")


JUMP_JS = r"""/* ac-cat-jump */
function acScrollRoot(){
  var ac=document.getElementById('acList');
  var sh=document.getElementById('acShell');
  if(ac&&ac.classList.contains('open')&&ac.scrollHeight>ac.clientHeight+2)return ac;
  if(sh&&sh.scrollHeight>sh.clientHeight+2)return sh;
  return ac;
}
function acGroupLabelEl(cat){
  var ac=document.getElementById('acList');
  if(!ac||!cat)return null;
  cat=String(cat);
  var hit=ac.querySelector('.ac-group-label[data-cat="'+cat.replace(/"/g,'')+'"]');
  if(hit)return hit;
  var map={instrument:'instrument',brand:'brand',model:'model',vibe:'vibe',patch:'patch',fav:'favorites',lib:'libraries',other:'other',session:'saved sessions',combo:'keyword combos'};
  var want=(map[cat]||cat).toLowerCase();
  var labels=ac.querySelectorAll('.ac-group-label');
  for(var i=0;i<labels.length;i++){
    if(String(labels[i].textContent||'').replace(/^\s+|\s+$/g,'').toLowerCase()===want)return labels[i];
  }
  return null;
}
function scrollAcGroupToTop(label){
  var sc=acScrollRoot();
  if(!sc||!label)return false;
  var lr=label.getBoundingClientRect();
  var sr=sc.getBoundingClientRect();
  var next=sc.scrollTop+(lr.top-sr.top);
  var max=Math.max(0,sc.scrollHeight-sc.clientHeight);
  sc.scrollTop=Math.max(0,Math.min(max,next));
  if(window.syncAcScrollStripe)window.syncAcScrollStripe();
  return true;
}
function categoryForLibraryQuery(q){
  q=String(q||'').toLowerCase();
  if(!q||q.length<2)return '';
  var best=null,score=0;
  try{
    if(typeof entries!=='undefined')entries.forEach(function(el){
      var n=String((typeof entryName==='function'?entryName(el):'')||(el.getAttribute&&el.getAttribute('data-name'))||'').toLowerCase();
      if(!n)return;
      var s=0;
      if(n===q)s=4;
      else if(n.indexOf(q)===0)s=3;
      else if(q.length>=3&&n.indexOf(q)>=0)s=2;
      if(s>score){score=s;best=el;}
    });
  }catch(err){}
  if(!best||score<2)return '';
  var ks=typeof catTokens==='function'?catTokens(best):[];
  var order=(typeof CAT_ORDER!=='undefined'&&CAT_ORDER)?CAT_ORDER:['instrument','brand','model','vibe','patch'];
  for(var i=0;i<order.length;i++){
    var c=order[i];
    if(ks.some(function(k){return (typeof KW_CATS!=='undefined'&&KW_CATS[k]===c)||(typeof kwCat==='function'&&kwCat(k)===c);}))return c;
  }
  return 'lib';
}
function matchingAcLibGroup(q){
  var ac=document.getElementById('acList');
  if(!ac||!q)return null;
  q=String(q).toLowerCase();
  var items=ac.querySelectorAll('.ac-item.ac-lib');
  var best=null,score=0;
  for(var i=0;i<items.length;i++){
    var lab=(items[i].querySelector('.ac-label')||items[i]).textContent||'';
    lab=lab.replace(/^\s+|\s+$/g,'').toLowerCase();
    var s=0;
    if(lab===q)s=4;
    else if(lab.indexOf(q)===0)s=3;
    else if(q.length>=3&&lab.indexOf(q)>=0)s=2;
    if(s>score){score=s;best=items[i];}
  }
  if(!best||score<2)return null;
  var cat=best.getAttribute('data-cat')||'';
  if(cat){
    var byCat=acGroupLabelEl(cat);
    if(byCat)return byCat;
  }
  var el=best.previousElementSibling;
  while(el&&!el.classList.contains('ac-group-label'))el=el.previousElementSibling;
  return el;
}
function jumpAcList(q,opts){
  opts=opts||{};
  var ac=document.getElementById('acList');
  if(!ac||!ac.classList.contains('open'))return;
  var cat='';
  var label=null;
  q=String(q||'').toLowerCase();
  if(q){
    cat=categoryForLibraryQuery(q);
    if(cat)label=acGroupLabelEl(cat);
    if(!label)label=matchingAcLibGroup(q);
  }
  if(!label){
    cat=opts.jumpCat||(typeof activeCat!=='undefined'?activeCat:'');
    if(cat&&cat!=='all'&&cat!=='other')label=acGroupLabelEl(cat);
  }
  if(!label&&(opts.jumpCat==='all'||cat==='all')){
    var sc0=acScrollRoot();
    if(sc0)sc0.scrollTop=0;
    return;
  }
  if(!label)return;
  scrollAcGroupToTop(label);
  try{
    var sc=acScrollRoot();
    var lr=label.getBoundingClientRect();
    var sr=sc&&sc.getBoundingClientRect();
    var payload={q:q,cat:label.getAttribute('data-cat')||cat||'',lab:String(label.textContent||'').replace(/^\s+|\s+$/g,''),st:sc?Math.round(sc.scrollTop):0,gap:sr?Math.round(lr.top-sr.top):null,focus:document.activeElement&&document.activeElement.id,sh:sc?sc.scrollHeight:0,ch:sc?sc.clientHeight:0};
    fetch('http://127.0.0.1:7529/ingest/1cf46354-1d61-4c80-bd72-a340f1db1b51',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'f491c2'},body:JSON.stringify({sessionId:'f491c2',runId:'ac-jump',hypothesisId:'H-AC1',location:'jumpAcList',message:'ac-cat-jump',data:payload,timestamp:Date.now()})}).catch(function(){});
    fetch('http://127.0.0.1:7529/ingest/1cf46354-1d61-4c80-bd72-a340f1db1b51',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'c00e3e'},body:JSON.stringify({sessionId:'c00e3e',runId:'ac-jump',hypothesisId:'H-AC1',location:'jumpAcList',message:'ac-cat-jump',data:payload,timestamp:Date.now()})}).catch(function(){});
  }catch(err){}
}
window.jumpAcList=jumpAcList;
window.scrollAcGroupToTop=scrollAcGroupToTop;
window.acGroupLabelEl=acGroupLabelEl;
"""

MIDDLE_CSS = r"""/* fix-MIDDLE: Search | Keywords on top, catalog full-width below */
.display-btn[data-display="middle"]{display:inline-flex!important}
body.display-sides.display-middle{
  display:grid!important;
  flex-direction:unset!important;
  grid-template-columns:minmax(0,var(--middle-lw,1fr)) minmax(0,var(--middle-rw,1fr))!important;
  grid-template-rows:auto var(--middle-menu-h,38dvh) minmax(0,1fr)!important;
  column-gap:var(--sides-pane-gap,6px)!important;
  row-gap:0!important;
  height:100dvh;overflow:hidden;align-items:stretch
}
body.display-sides.display-middle.search-chrome-collapsed:not(.kw-chrome-collapsed),
body.display-sides.display-middle.kw-chrome-collapsed:not(.search-chrome-collapsed){
  grid-template-columns:minmax(0,1fr)!important
}
body.display-sides.display-middle.search-chrome-collapsed.kw-chrome-collapsed{
  grid-template-columns:minmax(0,1fr)!important;
  grid-template-rows:auto minmax(0,1fr)!important
}
body.display-sides.display-middle .catalog-header{grid-column:1/-1!important;grid-row:1!important}
body.display-sides.display-middle #searchChrome{
  grid-column:1!important;grid-row:2!important;
  height:100%!important;max-height:none!important;min-height:0;width:100%!important;
  border-right:1px solid var(--border)!important;border-bottom:1px solid var(--border)!important;border-left:0!important;
  overflow:hidden!important;position:relative!important;inset:auto!important;transform:none!important;
  display:flex!important;flex-direction:column!important;flex:unset!important;z-index:5
}
body.display-sides.display-middle.search-chrome-collapsed #searchChrome{display:none!important}
body.display-sides.display-middle #filterWrap{
  grid-column:2!important;grid-row:2!important;
  position:relative!important;inset:auto!important;right:auto!important;top:auto!important;bottom:auto!important;
  transform:none!important;width:100%!important;max-width:none!important;
  height:100%!important;max-height:none!important;z-index:5!important;
  box-shadow:none!important;border-left:1px solid var(--border)!important;border-right:0!important;
  overflow:hidden!important;display:flex!important;flex-direction:column!important
}
body.display-sides.display-middle.kw-open #filterWrap{transform:none!important}
body.display-sides.display-middle.kw-chrome-collapsed #filterWrap{display:none!important}
body.display-sides.display-middle.search-chrome-collapsed #filterWrap{grid-column:1/-1!important}
body.display-sides.display-middle.kw-chrome-collapsed #searchChrome{grid-column:1/-1!important}
body.display-sides.display-middle #catalogMain{
  grid-column:1/-1!important;grid-row:3!important;
  min-height:0;height:auto!important;align-self:stretch;
  overflow-y:auto!important;overflow-x:hidden;padding:0 0 2rem
}
body.display-sides.display-middle.search-chrome-collapsed.kw-chrome-collapsed #catalogMain{grid-column:1/-1!important;grid-row:2!important}
body.display-sides.display-middle #filterWrap.open .filter-panel,
body.display-sides.display-middle #filterWrap .filter-panel{
  display:flex!important;flex-direction:column;flex:1 1 auto!important;min-height:0!important;max-height:none!important;
  position:static!important;width:auto!important;box-shadow:none
}
body.display-sides.display-middle #kwbar{flex:1 1 auto!important;min-height:0;overflow-y:auto!important;-webkit-overflow-scrolling:touch}
body.display-sides.display-middle.layout-edit #searchSplit,
body.display-sides.display-middle.layout-edit #dualFsSep{display:block!important;pointer-events:auto!important}
body.display-sides.display-middle.sides-portrait-flip #searchChrome{grid-column:1!important;grid-row:2!important}
body.display-sides.display-middle.sides-portrait-flip #filterWrap{grid-column:2!important;grid-row:2!important}
body.display-sides.display-middle.sides-portrait-flip #catalogMain{grid-column:1/-1!important;grid-row:3!important}
@media(max-width:899px){
  body.display-sides.display-middle{display:grid!important;flex-direction:unset!important}
  body.display-sides.display-middle #searchChrome{max-height:none!important;height:100%!important;overflow:hidden!important}
  body.display-sides.display-middle #filterWrap{
    position:relative!important;right:auto;top:auto;bottom:auto;left:auto;
    transform:none!important;width:100%!important;max-width:none!important;
    z-index:5!important;box-shadow:none!important;height:100%!important
  }
  body.display-sides.display-middle.kw-open #filterWrap{transform:none!important}
  body.display-sides.display-middle #catalogMain{flex:unset!important}
}
@media(min-width:900px) and (orientation:portrait){
  body.display-sides.display-middle{
    grid-template-columns:minmax(0,var(--middle-lw,1fr)) minmax(0,var(--middle-rw,1fr))!important;
    grid-template-rows:auto var(--middle-menu-h,38dvh) minmax(0,1fr)!important
  }
  body.display-sides.display-middle #searchChrome{grid-column:1!important;grid-row:2!important}
  body.display-sides.display-middle #filterWrap{grid-column:2!important;grid-row:2!important}
  body.display-sides.display-middle #catalogMain{grid-column:1/-1!important;grid-row:3!important}
}
@media(max-width:899px){.display-btn[data-display='middle']{display:inline-flex!important}}
"""

MIDDLE_JS = r"""function displayPickKey(){return 'catalog-display-pick-'+(window.CATALOG_NS||'catalog');}
function displayIsMiddle(){return !!(document.body&&document.body.classList.contains('display-middle'));}
window.displayIsMiddle=displayIsMiddle;
function middleLayoutDefaults(){
  var hdr=document.querySelector('.catalog-header');
  var top=hdr?Math.round(hdr.getBoundingClientRect().height):56;
  var availW=Math.max(280,window.innerWidth||900);
  var availH=Math.max(220,(window.innerHeight||800)-top);
  return {menuH:Math.round(availH*0.38),lw:Math.round(availW*0.5),availW:availW,availH:availH};
}
function parseMiddleStored(key,fallback){
  try{
    var v=localStorage.getItem(key);
    if(!v)return fallback;
    var n=parseInt(v,10);
    return (isFinite(n)&&n>0)?n:fallback;
  }catch(err){return fallback;}
}
function logMiddleLayout(hid,loc,msg,extra){
  try{
    extra=extra||{};
    extra.middle=displayIsMiddle();
    extra.display=typeof currentDisplay!=='undefined'?currentDisplay:'';
    extra.vw=window.innerWidth;extra.vh=window.innerHeight;
    extra.portrait=!!(window.matchMedia&&window.matchMedia('(orientation:portrait)').matches);
    extra.mh=(getComputedStyle(document.documentElement).getPropertyValue('--middle-menu-h')||'').trim();
    extra.lw=(getComputedStyle(document.documentElement).getPropertyValue('--middle-lw')||'').trim();
    fetch('http://127.0.0.1:7529/ingest/1cf46354-1d61-4c80-bd72-a340f1db1b51',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'f491c2'},body:JSON.stringify({sessionId:'f491c2',runId:'middle-layout',hypothesisId:hid,location:loc,message:msg,data:extra,timestamp:Date.now()})}).catch(function(){});
    fetch('http://127.0.0.1:7529/ingest/1cf46354-1d61-4c80-bd72-a340f1db1b51',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'c00e3e'},body:JSON.stringify({sessionId:'c00e3e',runId:'middle-layout',hypothesisId:hid,location:loc,message:msg,data:extra,timestamp:Date.now()})}).catch(function(){});
  }catch(err){}
}
function applyMiddleLayout(){
  if(!displayIsMiddle())return;
  document.body.classList.remove('sides-portrait-flip');
  var d=middleLayoutDefaults();
  var mh=parseMiddleStored('catalog-middle-menu-h',d.menuH);
  var lw=parseMiddleStored('catalog-middle-lw',d.lw);
  mh=Math.max(96,Math.min(d.availH-80,mh));
  lw=Math.max(110,Math.min(d.availW-110,lw));
  document.documentElement.style.setProperty('--middle-menu-h',mh+'px');
  document.documentElement.style.setProperty('--middle-lw',lw+'px');
  document.documentElement.style.setProperty('--middle-rw',Math.max(110,d.availW-lw)+'px');
  var fw=document.getElementById('filterWrap');
  if(fw&&!document.body.classList.contains('kw-chrome-collapsed')){
    fw.classList.add('open');document.body.classList.add('kw-open');
  }
  logMiddleLayout('H-M1','applyMiddleLayout','apply',{defH:d.menuH,defW:d.lw,mh:mh,lw:lw});
}
function placeMiddleHandles(){
  var split=document.getElementById('searchSplit');
  var sep=document.getElementById('dualFsSep');
  var ch=document.getElementById('searchChrome');
  var fw=document.getElementById('filterWrap');
  var editing=document.body.classList.contains('layout-edit');
  var hidden=document.body.classList.contains('search-chrome-collapsed');
  var kwHid=document.body.classList.contains('kw-chrome-collapsed');
  function applyBar(el,props){
    if(!el)return;
    el.removeAttribute('style');
    Object.keys(props).forEach(function(k){el.style.setProperty(k,props[k],'important');});
  }
  if(split&&ch&&fw&&editing&&!hidden&&!kwHid){
    var r=ch.getBoundingClientRect();
    var r2=fw.getBoundingClientRect();
    var left=Math.min(r.left,r2.left);
    var right=Math.max(r.right,r2.right);
    var top=Math.max(r.bottom,r2.bottom);
    applyBar(split,{position:'fixed',display:'block',left:Math.round(left)+'px',width:Math.round(right-left)+'px',top:Math.round(top-6)+'px',height:'12px','min-width':'0','max-width':'none','min-height':'12px','max-height':'12px',bottom:'auto','z-index':'80',margin:'0',transform:'none','pointer-events':'auto',cursor:'ns-resize'});
  }else if(split){split.removeAttribute('style');}
  if(sep&&ch&&fw&&editing&&!hidden&&!kwHid){
    var a=ch.getBoundingClientRect();
    var b=fw.getBoundingClientRect();
    var x=Math.round((a.right+b.left)/2-6);
    var top2=Math.min(a.top,b.top);
    var bot=Math.max(a.bottom,b.bottom);
    applyBar(sep,{position:'fixed',display:'block',left:x+'px',top:Math.round(top2)+'px',height:Math.round(bot-top2)+'px',width:'12px','min-width':'12px','max-width':'12px',bottom:'auto','z-index':'80',margin:'0',transform:'none','pointer-events':'auto',cursor:'ew-resize'});
  }else if(sep&&!document.body.classList.contains('dual-fs-open')){sep.removeAttribute('style');}
}
window.middleLayoutDefaults=middleLayoutDefaults;
window.applyMiddleLayout=applyMiddleLayout;
window.placeMiddleHandles=placeMiddleHandles;
window.logMiddleLayout=logMiddleLayout;
"""


def patch(text, path):
    if "/* ac-cat-jump */" in text and 'data-display="middle"' in text and "function applyMiddleLayout" in text:
        print(f"skip already patched: {path}")
        return text

    # --- Feature 1: group labels ---
    text = sub(text, "html+='<div class=\"ac-group-label\">Saved sessions</div>';",
               "html+='<div class=\"ac-group-label\" data-cat=\"session\">Saved sessions</div>';", "lbl-sessions")
    text = sub(text, "html+='<div class=\"ac-group-label\">Recent sessions</div>';",
               "html+='<div class=\"ac-group-label\" data-cat=\"session\">Recent sessions</div>';", "lbl-recent-sess")
    text = sub(text, "html+='<div class=\"ac-group-label\">Saved combinations</div>';",
               "html+='<div class=\"ac-group-label\" data-cat=\"combo\">Saved combinations</div>';", "lbl-saved-combo")
    text = sub(text, "html+='<div class=\"ac-group-label\">Keyword combos</div>';",
               "html+='<div class=\"ac-group-label\" data-cat=\"combo\">Keyword combos</div>';", "lbl-kw-combo")
    text = sub(text, "html+='<div class=\"ac-group-label\">Top card hits</div>';",
               "html+='<div class=\"ac-group-label\" data-cat=\"card\">Top card hits</div>';", "lbl-card")
    text = sub(text, "html+='<div class=\"ac-group-label\">Recent keywords</div>';",
               "html+='<div class=\"ac-group-label\" data-cat=\"recent\">Recent keywords</div>';", "lbl-recent-kw")
    text = sub(text, "var html='<div class=\"ac-group-label\">Libraries</div>';",
               "var html='<div class=\"ac-group-label\" data-cat=\"lib\">Libraries</div>';", "lbl-lib")
    text = sub(text, "html+='<div class=\"ac-group-label ac-fav-label\">Favorites</div>';",
               "html+='<div class=\"ac-group-label ac-fav-label\" data-cat=\"fav\">Favorites</div>';", "lbl-fav")

    text = sub(
        text,
        "window.setCat=function(cat){if(cat==='other')cat='all';activeCat=cat;document.querySelectorAll('.cat-btn').forEach(function(b){b.classList.toggle('active',b.dataset.cat===cat);});if(currentMode==='search')applySearch();else render();};",
        "window.setCat=function(cat){if(cat==='other')cat='all';activeCat=cat;document.querySelectorAll('.cat-btn').forEach(function(b){b.classList.toggle('active',b.dataset.cat===cat);});if(currentMode==='search')applySearch();else render();requestAnimationFrame(function(){requestAnimationFrame(function(){if(typeof jumpAcList==='function')jumpAcList(typeof typedQuery==='function'?typedQuery():((typeof searchInput!=='undefined'&&searchInput&&searchInput.value)||'').trim().toLowerCase(),{jumpCat:cat});});});};",
        "setCat",
    )

    if "/* ac-cat-jump */" not in text:
        text = sub(text, "function showAc(q,opts){", JUMP_JS + "function showAc(q,opts){", "jump-fn")

    text = sub(
        text,
        "acList.innerHTML=html;acList.classList.toggle('open',html.length>0);if(window.syncAcScrollStripe)window.syncAcScrollStripe();\nif(window.syncSearchSplit)window.syncSearchSplit();",
        "acList.innerHTML=html;acList.classList.toggle('open',html.length>0);if(window.syncAcScrollStripe)window.syncAcScrollStripe();\nif(window.syncSearchSplit)window.syncSearchSplit();\nrequestAnimationFrame(function(){requestAnimationFrame(function(){if(typeof jumpAcList==='function')jumpAcList(q,opts);if(window.syncAcScrollStripe)window.syncAcScrollStripe();});});",
        "showAc-jump",
    )

    # --- Feature 2: CSS + display button ---
    text = sub(
        text,
        "#portraitFlipBtn[hidden]{display:none!important}",
        MIDDLE_CSS + "#portraitFlipBtn[hidden]{display:none!important}",
        "middle-css",
    )
    text = sub(
        text,
        "@media(max-width:899px){.display-btn.display-desktop-only{display:none!important}.display-btn[data-display='sides']{display:inline-flex!important}}",
        "@media(max-width:899px){.display-btn.display-desktop-only{display:none!important}.display-btn[data-display='sides'],.display-btn[data-display='middle']{display:inline-flex!important}}",
        "mobile-btns",
    )
    text = sub(
        text,
        "setDisplayMode('sides')\">Sides</button>",
        "setDisplayMode('sides',{pick:true})\">Sides</button>"
        "<button type=\"button\" class=\"display-btn\" data-display=\"middle\" title=\"Middle: Search and Keywords on top, catalog below\" onclick=\"event.preventDefault();event.stopPropagation();setDisplayMode('middle',{pick:true})\">Middle</button>",
        "middle-btn",
    )

    # --- Feature 2: JS ---
    text = sub(
        text,
        "function displayModeSlot(){\n  var m=typeof currentDisplay!=='undefined'?currentDisplay:'upper';\n  if(m!=='upper'&&m!=='sides'&&m!=='fs')m='upper';\n  return m;\n}",
        "function displayModeSlot(){\n  var m=typeof currentDisplay!=='undefined'?currentDisplay:'upper';\n  if(m==='middle')m='sides';\n  if(m!=='upper'&&m!=='sides'&&m!=='fs')m='upper';\n  return m;\n}",
        "displayModeSlot",
    )
    text = sub(
        text,
        "function snapshotLiveToMode(mode){\n  mode=mode||displayModeSlot();",
        "function snapshotLiveToMode(mode){\n  mode=mode||displayModeSlot();\n  if(mode==='middle')mode='sides';",
        "snapshot-middle",
    )
    text = sub(
        text,
        "function applyModeSlot(mode){\n  mode=mode||displayModeSlot();",
        "function applyModeSlot(mode){\n  mode=mode||displayModeSlot();\n  if(mode==='middle')mode='sides';",
        "applySlot-middle",
    )

    if "function applyMiddleLayout" not in text:
        text = sub(text, "function applySidesCols(){", MIDDLE_JS + "function applySidesCols(){", "middle-js")

    text = sub(
        text,
        "function placeSidesHandles(){\n  if(!document.body.classList.contains('display-sides'))return;\n  if(typeof isPortraitDesktopSides==='function'&&isPortraitDesktopSides()){",
        "function placeSidesHandles(){\n  if(!document.body.classList.contains('display-sides'))return;\n  if(typeof displayIsMiddle==='function'?displayIsMiddle():document.body.classList.contains('display-middle')){\n    if(typeof placeMiddleHandles==='function')placeMiddleHandles();\n    return;\n  }\n  if(typeof isPortraitDesktopSides==='function'&&isPortraitDesktopSides()){",
        "place-handles",
    )

    text = sub(
        text,
        "    if(typeof isPortraitDesktopSides==='function'&&isPortraitDesktopSides()){\n      var d=typeof portraitSidesDefaults==='function'?portraitSidesDefaults():null;",
        "    if(typeof displayIsMiddle==='function'?displayIsMiddle():document.body.classList.contains('display-middle')){\n      var dM=typeof middleLayoutDefaults==='function'?middleLayoutDefaults():null;\n      if(!dM)return;\n      var rootM=document.documentElement;\n      var mlw=parseInt(getComputedStyle(rootM).getPropertyValue('--middle-lw'),10)||dM.lw;\n      var mmh=parseInt(getComputedStyle(rootM).getPropertyValue('--middle-menu-h'),10)||dM.menuH;\n      var tM=e.currentTarget||e.target;\n      drag={middle:true,which:which,x:e.clientX,y:e.clientY,lw:mlw,mh:mmh,def:dM,id:e.pointerId};\n      try{if(tM&&tM.setPointerCapture)tM.setPointerCapture(e.pointerId);}catch(err){}\n      return;\n    }\n    if(typeof isPortraitDesktopSides==='function'&&isPortraitDesktopSides()){\n      var d=typeof portraitSidesDefaults==='function'?portraitSidesDefaults():null;",
        "drag-down-middle",
    )
    text = sub(
        text,
        "    if(drag.portrait){\n      var clamp=window.clampPortraitTravel||function(v){return v;};",
        "    if(drag.middle){\n      var dM=drag.def;\n      if(drag.which==='split'){\n        var mhM=Math.max(96,Math.min(dM.availH-80,drag.mh+(e.clientY-drag.y)));\n        document.documentElement.style.setProperty('--middle-menu-h',mhM+'px');\n        try{localStorage.setItem('catalog-middle-menu-h',mhM+'px');}catch(ex){}\n      }else{\n        var nlwM=Math.max(110,Math.min(dM.availW-110,drag.lw+(e.clientX-drag.x)));\n        document.documentElement.style.setProperty('--middle-lw',nlwM+'px');\n        document.documentElement.style.setProperty('--middle-rw',Math.max(110,dM.availW-nlwM)+'px');\n        try{localStorage.setItem('catalog-middle-lw',nlwM+'px');}catch(ex){}\n      }\n      if(typeof placeSidesHandles==='function')placeSidesHandles();\n      return;\n    }\n    if(drag.portrait){\n      var clamp=window.clampPortraitTravel||function(v){return v;};",
        "drag-move-middle",
    )
    text = sub(
        text,
        "    if(drag.portrait){\n      var plw=parseInt(getComputedStyle(document.documentElement).getPropertyValue('--portrait-lw'),10)||0;",
        "    if(drag.middle){\n      var mlwU=parseInt(getComputedStyle(document.documentElement).getPropertyValue('--middle-lw'),10)||0;\n      var mmhU=parseInt(getComputedStyle(document.documentElement).getPropertyValue('--middle-menu-h'),10)||0;\n      try{localStorage.setItem('catalog-middle-lw',mlwU+'px');localStorage.setItem('catalog-middle-menu-h',mmhU+'px');}catch(ex){}\n      drag=null;\n      if(typeof logMiddleLayout==='function')logMiddleLayout('H-M2','sides-handle','middle-up',{lw:mlwU,mh:mmhU});\n      return;\n    }\n    if(drag.portrait){\n      var plw=parseInt(getComputedStyle(document.documentElement).getPropertyValue('--portrait-lw'),10)||0;",
        "drag-up-middle",
    )

    text = sub(
        text,
        "  var portrait=typeof isPortraitDesktopSides==='function'&&isPortraitDesktopSides();\n  document.body.classList.toggle('sides-orient-portrait',!!portrait);\n  if(portrait){\n    var flipOn=typeof window.portraitFlipOn==='function'?window.portraitFlipOn():document.body.classList.contains('sides-portrait-flip');\n    document.body.classList.toggle('sides-portrait-flip',!!flipOn);\n  }else{\n    document.body.classList.remove('sides-portrait-flip');\n  }",
        "  var middle=typeof displayIsMiddle==='function'?displayIsMiddle():document.body.classList.contains('display-middle');\n  var portrait=typeof isPortraitDesktopSides==='function'&&isPortraitDesktopSides();\n  document.body.classList.toggle('sides-orient-portrait',!!portrait&&!middle);\n  if(middle){\n    document.body.classList.remove('sides-portrait-flip');\n    if(typeof applyMiddleLayout==='function')applyMiddleLayout();\n  }else if(portrait){\n    var flipOn=typeof window.portraitFlipOn==='function'?window.portraitFlipOn():document.body.classList.contains('sides-portrait-flip');\n    document.body.classList.toggle('sides-portrait-flip',!!flipOn);\n  }else{\n    document.body.classList.remove('sides-portrait-flip');\n  }",
        "cols-middle-flag",
    )
    text = sub(
        text,
        "  if(portrait){\n    /* portrait uses --portrait-* buckets; do not overwrite widescreen --sides-lw/--sides-rw */\n  }else if(document.body.classList.contains('search-chrome-collapsed')){",
        "  if(middle){\n    /* middle uses --middle-* ; keep widescreen --sides-lw/--sides-rw intact */\n  }else if(portrait){\n    /* portrait uses --portrait-* buckets; do not overwrite widescreen --sides-lw/--sides-rw */\n  }else if(document.body.classList.contains('search-chrome-collapsed')){",
        "cols-middle-skip-lw",
    )

    text = sub(
        text,
        "    var sides=document.body.classList.contains('display-sides');\n    var portrait=isPortraitDesktopSides();\n    var flip=sides&&portrait&&portraitFlipOn();",
        "    var sides=document.body.classList.contains('display-sides');\n    if(typeof displayIsMiddle==='function'?displayIsMiddle():document.body.classList.contains('display-middle')){\n      document.body.classList.remove('sides-portrait-flip');\n      if(typeof syncPortraitFlipBtn==='function')syncPortraitFlipBtn();\n      return;\n    }\n    var portrait=isPortraitDesktopSides();\n    var flip=sides&&portrait&&portraitFlipOn();",
        "portrait-skip-middle",
    )
    text = sub(
        text,
        "    var show=!!(document.body.classList.contains('display-sides')&&isPortraitDesktopSides());",
        "    var show=!!(document.body.classList.contains('display-sides')&&isPortraitDesktopSides()&&!(typeof displayIsMiddle==='function'?displayIsMiddle():document.body.classList.contains('display-middle')));",
        "flip-btn-hide",
    )

    text = sub(
        text,
        "  if(mode!=='upper'&&mode!=='sides'&&mode!=='fs')mode='sides'; // fix-SIDES-ONLY: Sides is the only mode\n  if(mode==='upper'||mode==='fs')mode='sides'; // leftover Full/Upper always become Sides",
        "  if(opts.pick){try{localStorage.setItem(typeof displayPickKey==='function'?displayPickKey():('catalog-display-pick-'+(window.CATALOG_NS||'catalog')),'1');}catch(err){}}\n  if(mode!=='upper'&&mode!=='sides'&&mode!=='fs'&&mode!=='middle')mode='sides';\n  if(mode==='upper'||mode==='fs')mode='sides';\n  var persistDisplay=mode;\n  if(mode==='middle')mode='sides';",
        "setDisplay-coerce",
    )
    text = sub(
        text,
        "  currentDisplay=mode;\n  try{localStorage.setItem(DISPLAY_KEY,mode);}catch(err){}\n  document.body.classList.remove('display-upper','display-sides','display-fs');\n  document.body.classList.add('display-'+mode);",
        "  currentDisplay=typeof persistDisplay!=='undefined'?persistDisplay:mode;\n  try{localStorage.setItem(DISPLAY_KEY,currentDisplay);}catch(err){}\n  document.body.classList.remove('display-upper','display-sides','display-fs','display-middle');\n  document.body.classList.add('display-'+mode);\n  if(currentDisplay==='middle'){\n    document.body.classList.add('display-middle');\n    var fwMid=document.getElementById('filterWrap');\n    if(fwMid){fwMid.classList.add('open');document.body.classList.add('kw-open');}\n    document.body.classList.remove('kw-chrome-collapsed');\n  }",
        "setDisplay-class",
    )

    text = sub(
        text,
        "  var m='sides';\n  try{m=localStorage.getItem(DISPLAY_KEY)||'sides';}catch(err){}\n  if(m!=='upper'&&m!=='sides'&&m!=='fs')m='sides';\n  if(m==='upper'||m==='fs')m='sides'; // Upper/Full removed — always Sides\n  // No mobile coercion — Sides works on all screen sizes via CSS\n  setDisplayMode(m);",
        "  var m='sides';\n  var picked=false;\n  try{picked=localStorage.getItem(typeof displayPickKey==='function'?displayPickKey():('catalog-display-pick-'+(window.CATALOG_NS||'catalog')))==='1';m=localStorage.getItem(DISPLAY_KEY)||'sides';}catch(err){}\n  if(m!=='upper'&&m!=='sides'&&m!=='fs'&&m!=='middle')m='sides';\n  if(m==='upper'||m==='fs')m='sides';\n  if(!picked){m=(window.matchMedia&&window.matchMedia('(orientation:portrait)').matches)?'middle':'sides';}\n  // No mobile coercion — Sides works on all screen sizes via CSS; portrait defaults to Middle until the user picks\n  setDisplayMode(m);",
        "init-default",
    )

    text = sub(
        text,
        "if(shouldOpen&&!fw.classList.contains('open')&&typeof currentDisplay!=='undefined'&&currentDisplay!=='sides'){if(typeof toggleFilter==='function')toggleFilter();}",
        "if(shouldOpen&&!fw.classList.contains('open')&&typeof currentDisplay!=='undefined'&&currentDisplay!=='sides'&&currentDisplay!=='middle'){if(typeof toggleFilter==='function')toggleFilter();}",
        "kw-default",
        optional=True,
    )

    # Safety: existing debug sessions must remain
    if path.name == "DS-CATALOG.html":
        if "sessionId:'c00e3e'" not in text and 'sessionId:"c00e3e"' not in text:
            if "sessionId:'c00e3e'" not in text.replace(" ", ""):
                pass
        if "function dbgIndexAc" not in text:
            raise SystemExit(f"{path.name}: lost dbgIndexAc")
        if "sessionId:'c00e3e'" not in text:
            raise SystemExit(f"{path.name}: lost c00e3e logs")
        if "sessionId:'f491c2'" not in text:
            raise SystemExit(f"{path.name}: lost f491c2 logs")
        if "// #region agent log" not in text:
            raise SystemExit(f"{path.name}: lost agent log regions")
    if "sessionId:'f491c2'" not in text:
        raise SystemExit(f"{path.name}: lost f491c2 logs")
    if "/* ac-cat-jump */" not in text:
        raise SystemExit(f"{path.name}: missing ac-cat-jump")
    if "display-middle" not in text:
        raise SystemExit(f"{path.name}: missing display-middle")
    if "function applyMiddleLayout" not in text:
        raise SystemExit(f"{path.name}: missing applyMiddleLayout")
    return text


def main():
    for path in FILES:
        if not path.exists():
            raise SystemExit(f"missing {path}")
        text = path.read_text(encoding="utf-8")
        new = patch(text, path)
        if new != text:
            path.write_text(new, encoding="utf-8")
            print(f"patched {path}")
        else:
            print(f"unchanged {path}")


if __name__ == "__main__":
    main()
