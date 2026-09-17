#!/usr/bin/env python3
"""Saved pill combos (cap 12), AC library wrap+[-], history erase, Sides kw flush."""
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


def once_substr(text, old, new, label, path=None):
    n = text.count(old)
    if n != 1:
        prefix = f"{path.name}: " if path else ""
        raise SystemExit(f"{prefix}{label}: count={n} expected 1")
    return text.replace(old, new, 1)


MAX_OLD = "var PIN_SESS_MAX=12;"
MAX_NEW = "var PIN_SESS_MAX=12;\nvar KW_COMBO_MAX=12;\nvar KW_COMBO_AUTO_MAX=10;"

PERSIST_OLD = "function persistKwCombos(){lsSet(KW_COMBO_KEY,kwComboStore.slice(0,10));}"
PERSIST_NEW = """function kwComboKey(pills){return (pills||[]).map(function(x){return String(x).toLowerCase();}).sort().join('\\u001f');}
function kwSavedCombos(){return (kwComboStore||[]).filter(function(o){return o&&o.saved;});}
function kwAutoCombos(){return (kwComboStore||[]).filter(function(o){return o&&!o.saved;});}
function persistKwCombos(){
  var maxS=typeof KW_COMBO_MAX==='number'?KW_COMBO_MAX:12;
  var maxA=typeof KW_COMBO_AUTO_MAX==='number'?KW_COMBO_AUTO_MAX:10;
  var saved=kwSavedCombos().slice().sort(function(a,b){return (b.usedAt||b.savedAt||b.t||0)-(a.usedAt||a.savedAt||a.t||0);}).slice(0,maxS);
  var auto=kwAutoCombos().slice(0,maxA);
  kwComboStore=saved.concat(auto);
  lsSet(KW_COMBO_KEY,kwComboStore);
}
"""

SNAP_OLD = """function snapshotKwCombo(){
  var pills=(typeof searchKeywords!=='undefined'&&searchKeywords&&searchKeywords.length)?searchKeywords.slice():[];
  if(!pills.length)return;
  var key=pills.map(function(x){return String(x).toLowerCase();}).sort().join('\\u001f');
  kwComboStore=kwComboStore.filter(function(o){return o&&o.key!==key;});
  kwComboStore.unshift({key:key,pills:pills.slice(),t:Date.now()});
  persistKwCombos();
}
"""

SNAP_NEW = """function snapshotKwCombo(){
  var pills=(typeof searchKeywords!=='undefined'&&searchKeywords&&searchKeywords.length)?searchKeywords.slice():[];
  if(!pills.length)return;
  var key=typeof kwComboKey==='function'?kwComboKey(pills):pills.map(function(x){return String(x).toLowerCase();}).sort().join('\\u001f');
  kwComboStore=kwComboStore.filter(function(o){return o&&(o.saved||o.key!==key);});
  kwComboStore.unshift({key:key,pills:pills.slice(),t:Date.now(),saved:0});
  persistKwCombos();
}
"""

APPLY_OLD = """window.applyKwCombo=function(key){
  var hit=null;
  (kwComboStore||[]).forEach(function(o){if(o&&o.key===key)hit=o;});
  if(!hit||!hit.pills)return;
  if(typeof setMode==='function')setMode('search');
  searchKeywords=hit.pills.slice();
  if(typeof renderPills==='function')renderPills();
  if(typeof applySearch==='function')applySearch();
  if(typeof renderKwBar==='function')renderKwBar();
};
"""

APPLY_NEW = """window.applyKwCombo=function(key,ev){
  if(ev&&ev.stopPropagation){ev.preventDefault();ev.stopPropagation();}
  var hit=null;
  (kwComboStore||[]).forEach(function(o){if(o&&(o.key===key||o.id===key))hit=o;});
  if(!hit||!hit.pills)return;
  if(hit.saved){hit.usedAt=Date.now();if(typeof persistKwCombos==='function')persistKwCombos();}
  if(typeof hideSearchAc==='function')hideSearchAc();
  var ac=document.getElementById('acList');
  if(ac){ac.classList.remove('open');ac.innerHTML='';}
  if(typeof setMode==='function')setMode('search');
  searchKeywords=hit.pills.slice();
  if(typeof renderPills==='function')renderPills();
  if(typeof applySearch==='function')applySearch();
  if(typeof renderKwBar==='function')renderKwBar();
};
window.saveKwCombo=function(name){
  name=String(name||'').replace(/^\\s+|\\s+$/g,'');
  var pills=(typeof searchKeywords!=='undefined'&&searchKeywords)?searchKeywords.slice():[];
  if(!pills.length)return false;
  if(!name)name=pills.join(' + ');
  var key=typeof kwComboKey==='function'?kwComboKey(pills):pills.map(function(x){return String(x).toLowerCase();}).sort().join('\\u001f');
  var rec={id:'c'+Date.now().toString(36)+Math.floor(Math.random()*1e4).toString(36),key:key,pills:pills.slice(),name:name,saved:1,savedAt:Date.now(),usedAt:Date.now(),t:Date.now()};
  var exist=-1;
  kwComboStore.forEach(function(o,i){if(o&&o.saved&&(o.key===key||String(o.name||'').toLowerCase()===name.toLowerCase()))exist=i;});
  if(exist>=0){rec.id=kwComboStore[exist].id||rec.id;kwComboStore[exist]=rec;}
  else{
    var maxS=typeof KW_COMBO_MAX==='number'?KW_COMBO_MAX:12;
    var saved=kwSavedCombos();
    if(saved.length>=maxS){
      saved.sort(function(a,b){return (a.usedAt||a.savedAt||a.t||0)-(b.usedAt||b.savedAt||b.t||0);});
      var drop=saved[0];
      kwComboStore=kwComboStore.filter(function(o){return o!==drop;});
    }
    kwComboStore.unshift(rec);
  }
  kwComboStore=kwComboStore.filter(function(o){return !(o&&!o.saved&&o.key===key);});
  persistKwCombos();
  return true;
};
function defaultKwComboName(){return ((typeof searchKeywords!=='undefined'&&searchKeywords)?searchKeywords:[]).join(' + ');}
function placeKwComboSavePop(){
  var pop=document.getElementById('kwComboSavePop'),btn=document.getElementById('kwComboSave');
  if(!pop||!btn)return;
  var br=btn.getBoundingClientRect();
  pop.style.position='fixed';pop.style.zIndex='10050';
  var w=Math.max(224,pop.getBoundingClientRect().width||224);
  var left=Math.max(8,Math.min((window.innerWidth||800)-w-8,br.right-w));
  var top=br.bottom+6;
  if(top+148>(window.innerHeight||800))top=Math.max(8,br.top-148);
  pop.style.left=Math.round(left)+'px';pop.style.top=Math.round(top)+'px';
}
function parkKwComboSave(){
  var strip=document.getElementById('searchStrip');
  var pills=document.getElementById('searchPills');
  var btn=document.getElementById('kwComboSave');
  if(!btn){
    btn=document.createElement('button');
    btn.type='button';btn.id='kwComboSave';btn.className='kw-combo-save';
    btn.textContent='Save';
    btn.setAttribute('aria-label','Save keyword combination');
    btn.title='Save current pills as a named combination';
    document.body.appendChild(btn);
  }
  var pop=document.getElementById('kwComboSavePop');
  if(!pop){
    pop=document.createElement('div');
    pop.id='kwComboSavePop';pop.hidden=true;pop.className='kw-combo-save-pop';
    pop.innerHTML='<input id="kwComboSaveName" type="text" maxlength="40" placeholder="Combination name" autocomplete="off"><button type="button" id="kwComboSaveGo">Save combination</button>';
    document.body.appendChild(pop);
  }
  var n=(typeof searchKeywords!=='undefined'&&searchKeywords)?searchKeywords.length:0;
  btn.hidden=n<1;
  if(n<1){pop.hidden=true;return;}
  var pillsOn=false;
  if(pills){
    var cs=getComputedStyle(pills);
    pillsOn=cs.display!=='none'&&cs.visibility!=='hidden'&&pills.offsetParent!==null;
  }
  var host=pillsOn?pills:strip;
  if(host&&btn.parentElement!==host)host.appendChild(btn);
}
window.openKwComboSave=function(ev){
  if(ev&&ev.stopPropagation){ev.preventDefault();ev.stopPropagation();}
  if(!(typeof searchKeywords!=='undefined'&&searchKeywords&&searchKeywords.length))return;
  if(typeof parkKwComboSave==='function')parkKwComboSave();
  var pop=document.getElementById('kwComboSavePop'),inp=document.getElementById('kwComboSaveName');
  if(!pop||!inp)return;
  pop.hidden=!pop.hidden;
  if(!pop.hidden){
    inp.value=defaultKwComboName().slice(0,40);
    placeKwComboSavePop();
    try{inp.focus();inp.select();}catch(err){}
  }
};
"""

HIST_COMBO_OLD = """  var combos=(kwComboStore||[]).filter(function(o){return o&&catalogHistMatch((o.pills||[]).join(' + '),q);}).slice(0,10);
  if(combos.length){
    html+='<div class="ac-group-label">Keyword combos</div>';
    combos.forEach(function(o){
      var lab=(o.pills||[]).join(' + ');
      html+='<div class="ac-item ac-combo" data-cat="combo" onclick="applyKwCombo(\\''+jsStr(o.key)+'\\')"><span class="ac-label">'+htmlStr(lab)+'</span></div>';
    });
  }
"""

HIST_COMBO_NEW = """  var savedC=(typeof kwSavedCombos==='function'?kwSavedCombos():[]).filter(function(o){return o&&(catalogHistMatch(o.name,q)||catalogHistMatch((o.pills||[]).join(' + '),q));}).sort(function(a,b){return (b.usedAt||b.savedAt||b.t||0)-(a.usedAt||a.savedAt||a.t||0);}).slice(0,typeof KW_COMBO_MAX==='number'?KW_COMBO_MAX:12);
  if(savedC.length){
    html+='<div class="ac-group-label">Saved combinations</div>';
    savedC.forEach(function(o){
      var lab=o.name||(o.pills||[]).join(' + ');
      html+='<div class="ac-item ac-combo ac-combo-saved" data-cat="combo" onclick="applyKwCombo(\\''+jsStr(o.id||o.key)+'\\',event)"><span class="ac-label">'+htmlStr(lab)+'</span><span class="ac-count">'+(o.pills&&o.pills.length||0)+'</span></div>';
    });
  }
  var combos=(typeof kwAutoCombos==='function'?kwAutoCombos():(kwComboStore||[])).filter(function(o){return o&&!o.saved&&catalogHistMatch((o.pills||[]).join(' + '),q);}).slice(0,10);
  if(combos.length){
    html+='<div class="ac-group-label">Keyword combos</div>';
    combos.forEach(function(o){
      var lab=(o.pills||[]).join(' + ');
      html+='<div class="ac-item ac-combo" data-cat="combo" onclick="applyKwCombo(\\''+jsStr(o.key)+'\\',event)"><span class="ac-label">'+htmlStr(lab)+'</span></div>';
    });
  }
"""

CARD_HIT_OLD = """      html+='<div class="ac-item ac-cardhit" data-cat="card" onclick="openCardHit(\\''+jsStr(o.id)+'\\')"><span class="ac-label">'+htmlStr(o.name||o.id)+'</span><span class="ac-count">'+(o.n||1)+'</span></div>';"""
CARD_HIT_NEW = """      html+='<div class="ac-item ac-cardhit ac-lib" data-cat="card" data-lib="1" onclick="openCardHit(\\''+jsStr(o.id)+'\\')"><span class="ac-label">'+htmlStr(o.name||o.id)+'</span><span class="ac-lib-mark" title="Full library name">[-]</span><span class="ac-count">'+(o.n||1)+'</span></div>';"""

ACH_ITEM_OLD = """html+='<div class="ac-item'+(o.isFav||(o.label&&favSet[o.label])?' fav-rec':'')+'" data-cat="'+c+'" onclick="pickAc(\\''+jsStr(o.label||o.k)+'\\')"><span class="ac-label">'+htmlStr(o.label||o.k)+acNoteIcon(o)+'</span> <span class="ac-count">'+o.c+'</span></div>';"""
ACH_ITEM_NEW = """html+=acLibItemHtml(o,c,"pickAc('"+jsStr(o.label||o.k)+"')",{note:1,count:o.c});"""

FAV_NAME_OLD = """      html+='<div class="ac-item fav-rec" data-cat="fav" onclick="pickAc(\\''+jsStr(o.label||o.k)+'\\')"><span class="ac-label">'+htmlStr(o.label||o.k)+acNoteIcon(o)+'</span></div>';"""
FAV_NAME_NEW = """      html+=acLibItemHtml(o,'fav',"pickAc('"+jsStr(o.label||o.k)+"')",{note:1,extra:'fav-rec',forceLib:1});"""

SHOW_OLD = """var histHtml=typeof catalogAcHistoryHtml==='function'?catalogAcHistoryHtml(q):'';
var mainHtml=acHtml(list,100,!q);
var favHtml=favAcHtml(favs,ranked);
var hasMain=mainHtml.length>0;
var hasCommits=(ranked||[]).some(function(o){return o&&o.searchCommits>0;});
"""

SHOW_NEW = """var histHtml=typeof catalogAcHistoryHtml==='function'?catalogAcHistoryHtml(q):'';
var libHtml=(q&&typeof libAcHtml==='function')?libAcHtml(typeof suggestLibNames==='function'?suggestLibNames(q,24):[]):'';
var mainHtml=acHtml(list,100,!q);
var favHtml=favAcHtml(favs,ranked);
var hasMain=mainHtml.length>0;
var hasCommits=(ranked||[]).some(function(o){return o&&o.searchCommits>0;});
"""

HTML_JOIN_OLD = "var html=(histHtml||'')+((hasMain||hasCommits||!!q||opts.force)?(favHtml+mainHtml):'');"
HTML_JOIN_NEW = "var html=(histHtml||'')+(libHtml||'')+((hasMain||hasCommits||!!q||opts.force)?(favHtml+mainHtml):'');"

ACHTML_FN = "function acHtml(list,cap,hint){"

HELPERS = """function acRowIsLib(o,cat,force){
  if(force)return true;
  if(!o)return false;
  cat=cat||o.cat||'';
  if(cat==='session'||cat==='combo'||cat==='recent'||cat==='combo-save')return false;
  if(o.isLibName||cat==='lib'||cat==='card')return true;
  var lab=String(o.label||o.k||'');
  return typeof isLibraryNameQuery==='function'&&isLibraryNameQuery(lab);
}
function acLibItemHtml(o,cat,onclick,opts){
  opts=opts||{};
  var lib=acRowIsLib(o,cat,opts.forceLib);
  var extra=opts.extra?(' '+opts.extra):'';
  var fav=(o&&(o.isFav||(o.label&&typeof favSet!=='undefined'&&favSet[o.label])))?' fav-rec':'';
  var cls='ac-item'+fav+(lib?' ac-lib':'')+extra;
  var mark=lib?'<span class="ac-lib-mark" title="Full library name">[-]</span>':'';
  var count=(opts.count==null||opts.count==='')?'':(' <span class="ac-count">'+opts.count+'</span>');
  var note=(opts.note&&typeof acNoteIcon==='function')?acNoteIcon(o):'';
  return '<div class="'+cls+'" data-cat="'+cat+'"'+(lib?' data-lib="1"':'')+' onclick="'+onclick+'"><span class="ac-label">'+htmlStr((o&&(o.label||o.k))||'')+note+'</span>'+mark+count+'</div>';
}
function suggestLibNames(q,lim){
  var ql=String(q||'').toLowerCase();
  if(!ql)return [];
  var list=[],seen={};
  function add(k,lab){
    lab=lab||k;
    var kk=String(k||'').toLowerCase();
    if(!kk||seen[kk])return;
    if(String(lab).toLowerCase().indexOf(ql)<0&&kk.indexOf(ql)<0)return;
    seen[kk]=1;
    list.push({k:kk,c:1,isLibName:1,label:lab,cat:'lib'});
  }
  try{Object.keys(nameLabel||{}).forEach(function(k){add(k,nameLabel[k]);});}catch(err){}
  try{
    if(typeof entries!=='undefined')entries.forEach(function(el){
      var n=(typeof entryName==='function'?entryName(el):(el.getAttribute&&el.getAttribute('data-name')))||'';
      if(n)add(n,n);
    });
  }catch(err2){}
  list.sort(function(a,b){return String(a.label||'').localeCompare(String(b.label||''));});
  return list.slice(0,lim||24);
}
function libAcHtml(list){
  if(!list||!list.length)return '';
  var html='<div class="ac-group-label">Libraries</div>';
  list.forEach(function(o){html+=acLibItemHtml(o,'lib',"pickAc('"+jsStr(o.label||o.k)+"')",{note:1,forceLib:1});});
  return html;
}
function acHtml(list,cap,hint){"""

PILLS_OLD = "function renderPills(){var html=searchKeywords.map(function(k){var cls='pill-tag'+(isPatchKw(k)?' patch':'');return '<span class=\"'+cls+'\"><span class=\"pill-label\">'+htmlStr(k)+'</span><button type=\"button\" class=\"pill-x\" aria-label=\"Remove '+htmlStr(k)+'\" onclick=\"event.preventDefault();event.stopPropagation();removeSearchKw(\\''+jsStr(k)+'\\')\">\\u00d7</button></span>';}).join('');document.querySelectorAll('#searchPills,.search-active-pills').forEach(function(c){c.innerHTML=html;});}"
PILLS_NEW = "function renderPills(){var keep=document.getElementById('kwComboSave');if(keep)document.body.appendChild(keep);var html=searchKeywords.map(function(k){var cls='pill-tag'+(isPatchKw(k)?' patch':'');return '<span class=\"'+cls+'\"><span class=\"pill-label\">'+htmlStr(k)+'</span><button type=\"button\" class=\"pill-x\" aria-label=\"Remove '+htmlStr(k)+'\" onclick=\"event.preventDefault();event.stopPropagation();removeSearchKw(\\''+jsStr(k)+'\\')\">\\u00d7</button></span>';}).join('');document.querySelectorAll('#searchPills,.search-active-pills').forEach(function(c){c.innerHTML=html;});if(typeof parkKwComboSave==='function')parkKwComboSave();}"

HIST_ROWS_OLD = """    {id:'combos',label:'Keyword combos',n:(kwComboStore||[]).length,on:1},
    {id:'cards',label:'Card hits',n:Object.keys(cardHitStore||{}).length,on:1},
    {id:'sessions',label:sessLab,n:sessN,on:0}
"""
HIST_ROWS_NEW = """    {id:'combos',label:'Keyword combos',n:(typeof kwAutoCombos==='function'?kwAutoCombos():(kwComboStore||[])).length,on:1},
    {id:'cards',label:'Card hits',n:Object.keys(cardHitStore||{}).length,on:1},
    {id:'savedCombos',label:'Saved combinations',n:(typeof kwSavedCombos==='function'?kwSavedCombos():[]).length,on:0},
    {id:'sessions',label:sessLab,n:sessN,on:0}
"""

SEARCH_ALL_OLD = "if(picks)picks.querySelectorAll('input[type=\"checkbox\"][data-hist]').forEach(function(cb){cb.checked=cb.getAttribute('data-hist')!=='sessions';});"
SEARCH_ALL_NEW = "if(picks)picks.querySelectorAll('input[type=\"checkbox\"][data-hist]').forEach(function(cb){var h=cb.getAttribute('data-hist');cb.checked=h!=='sessions'&&h!=='savedCombos';});"

WIPE_OLD = """  if(buckets.combos){
    kwComboStore=[];
    if(typeof persistKwCombos==='function')persistKwCombos();
  }
"""
WIPE_NEW = """  if(buckets.combos&&buckets.savedCombos){
    kwComboStore=[];
    if(typeof persistKwCombos==='function')persistKwCombos();
  }else if(buckets.combos){
    kwComboStore=(kwComboStore||[]).filter(function(o){return o&&o.saved;});
    if(typeof persistKwCombos==='function')persistKwCombos();
  }else if(buckets.savedCombos){
    kwComboStore=(kwComboStore||[]).filter(function(o){return o&&!o.saved;});
    if(typeof persistKwCombos==='function')persistKwCombos();
  }
"""

TITLE_SEARCH_OLD = 'title="Select all search history (not saved sessions)"'
TITLE_SEARCH_NEW = 'title="Select all search history (not saved sessions or saved combinations)"'
TITLE_ALL_OLD = 'title="Select all, including saved sessions"'
TITLE_ALL_NEW = 'title="Select all, including saved sessions and saved combinations"'

CSS_ITEM_OLD = """ .search-autocomplete .ac-item{padding:10px clamp(8px,2vw,20px);cursor:pointer;font-size:1rem;color:var(--text);display:flex;justify-content:space-between;min-height:2.75rem;align-items:center;gap:8px}
 .search-autocomplete .ac-item:hover{background:var(--bg-card)}
 .search-autocomplete .ac-item .ac-label{display:flex;align-items:center;gap:8px;min-width:0;flex:1}
"""
CSS_ITEM_NEW = """ .search-autocomplete .ac-item{padding:10px clamp(8px,2vw,20px);cursor:pointer;font-size:1rem;color:var(--text);display:flex;justify-content:space-between;min-height:2.75rem;align-items:center;gap:8px}
 .search-autocomplete .ac-item:hover{background:var(--bg-card)}
 .search-autocomplete .ac-item .ac-label{display:flex;align-items:center;gap:8px;min-width:0;flex:1}
 .search-autocomplete .ac-item.ac-lib{align-items:flex-start;height:auto;white-space:normal}
 .search-autocomplete .ac-item.ac-lib .ac-label{display:block;white-space:normal;overflow-wrap:anywhere;word-break:break-word;align-self:center;line-height:1.3}
 .search-autocomplete .ac-item.ac-lib .ac-lib-mark{flex:0 0 auto;align-self:center;color:var(--text-muted);font-variant-numeric:tabular-nums;letter-spacing:.02em}
.kw-combo-save{flex:0 0 auto;box-sizing:border-box;min-height:2.25rem;padding:0 .8rem;border:1px solid var(--accent-instrument);border-radius:999px;background:var(--bg-card);color:var(--accent-instrument);font:inherit;font-size:.9rem;font-weight:650;cursor:pointer;touch-action:manipulation}
.kw-combo-save[hidden]{display:none!important}
.kw-combo-save-pop{min-width:14rem;padding:.55rem;border:1px solid var(--border);border-radius:8px;background:var(--bg-surface);box-shadow:0 10px 28px rgba(0,0,0,.4)}
.kw-combo-save-pop[hidden]{display:none!important}
#kwComboSaveName{width:100%;box-sizing:border-box;min-height:2.25rem;margin:0 0 .4rem;padding:.3rem .5rem;border:1px solid var(--border);border-radius:6px;background:var(--bg-card);color:var(--text);font:inherit}
#kwComboSaveGo{width:100%;min-height:2.25rem;border:1px solid var(--accent-instrument);border-radius:6px;background:var(--accent-instrument-bg);color:var(--accent-instrument);font:inherit;cursor:pointer}
"""

FW_OLD = "  body.display-sides #filterWrap{grid-column:3;grid-row:2;height:100%;min-height:0;overflow:hidden;position:relative!important;inset:auto!important;z-index:5!important;width:100%!important;max-width:none!important;border-left:1px solid var(--border);border-bottom:1px solid var(--border);padding:0;display:flex!important;flex-direction:column!important;background:var(--bg-surface);align-self:stretch}"
FW_NEW = "  body.display-sides #filterWrap{grid-column:3;grid-row:2;height:100%;min-height:0;overflow:hidden;position:relative!important;inset:auto!important;z-index:5!important;width:100%!important;max-width:none!important;border-left:1px solid var(--border);border-bottom:0;padding:0;display:flex!important;flex-direction:column!important;background:var(--bg-surface);align-self:stretch}"

PANE_OLD = "  body.display-sides #catalogMain,body.display-sides #searchChrome,body.display-sides.kw-open #filterWrap{height:100%;min-height:0;align-self:stretch}"
PANE_NEW = """  body.display-sides #catalogMain,body.display-sides #searchChrome,body.display-sides.kw-open #filterWrap{height:100%;min-height:0;align-self:stretch}
  body.display-sides.kw-open:not(.kw-chrome-collapsed) #filterWrap{height:100%!important;max-height:none!important;align-self:stretch!important;margin-bottom:0!important;border-bottom:0!important;padding-bottom:0!important}
  body.display-sides.kw-open:not(.kw-chrome-collapsed) #filterWrap .filter-panel,body.display-sides.kw-open:not(.kw-chrome-collapsed) #filterWrap.open .filter-panel{display:flex!important;flex-direction:column!important;flex:1 1 auto!important;min-height:0!important;max-height:none!important;padding-bottom:0!important;margin-bottom:0!important}
  body.display-sides.kw-open:not(.kw-chrome-collapsed) #kwbar{flex:1 1 auto!important;min-height:0!important;margin-bottom:0!important;padding-bottom:0!important}
  body.display-sides.kw-open:not(.kw-chrome-collapsed) #kwstatus,body.display-sides.kw-open:not(.kw-chrome-collapsed) .kwstatus{margin:0!important;padding-bottom:max(.15rem,env(safe-area-inset-bottom,0px))!important}
"""

KWFLUSH2_OLD = """  body.display-sides.kw-open:not(.kw-chrome-collapsed) #kwbar{flex:1 1 auto!important;min-height:0!important;margin-bottom:0!important;padding-bottom:max(.25rem,env(safe-area-inset-bottom,0px))}
"""
KWFLUSH2_NEW = """  body.display-sides.kw-open:not(.kw-chrome-collapsed) #kwbar{flex:1 1 auto!important;min-height:0!important;margin-bottom:0!important;padding-bottom:0!important}
  body.display-sides.kw-open:not(.kw-chrome-collapsed) #kwstatus,body.display-sides.kw-open:not(.kw-chrome-collapsed) .kwstatus{margin:0!important;padding-bottom:max(.15rem,env(safe-area-inset-bottom,0px))!important}
"""

PORTRAIT_FW_OLD = """  body.display-sides #filterWrap{
    grid-column:1!important;grid-row:3!important;
    height:auto!important;max-height:none!important;min-height:0;
"""
PORTRAIT_FW_NEW = """  body.display-sides #filterWrap{
    grid-column:1!important;grid-row:3!important;
    height:100%!important;max-height:none!important;min-height:0;align-self:stretch;
"""

BIND_OLD = "window.catalogAcHistoryHtml=catalogAcHistoryHtml;"
BIND_NEW = """window.catalogAcHistoryHtml=catalogAcHistoryHtml;
(function bindKwComboSave(){
  if(window.__kwComboSaveBound)return;
  window.__kwComboSaveBound=1;
  document.addEventListener('click',function(e){
    var t=e.target;
    if(!t||!t.closest)return;
    if(t.closest('#kwComboSave,.kw-combo-save')){
      e.preventDefault();e.stopPropagation();
      if(typeof openKwComboSave==='function')openKwComboSave(e);
      return;
    }
    if(t.closest('#kwComboSaveGo')){
      e.preventDefault();e.stopPropagation();
      var inp=document.getElementById('kwComboSaveName');
      var nm=inp?inp.value:'';
      if(typeof saveKwCombo==='function'&&saveKwCombo(nm)){
        var p=document.getElementById('kwComboSavePop');if(p)p.hidden=true;
        if(typeof showAc==='function')showAc((typeof searchInput!=='undefined'&&searchInput&&searchInput.value||'').trim().toLowerCase(),{force:true});
      }
      return;
    }
    var pop=document.getElementById('kwComboSavePop');
    if(pop&&!pop.hidden&&!t.closest('#kwComboSavePop,#kwComboSave,.kw-combo-save'))pop.hidden=true;
  });
})();
"""


def patch(text, path):
    def one(old, new, label):
        return once_substr(text, old, new, label, path)

    text = sub(text, MAX_OLD, MAX_NEW, "max")
    text = one(PERSIST_OLD, PERSIST_NEW, "persist")
    text = sub(text, SNAP_OLD, SNAP_NEW, "snapshot")
    text = sub(text, APPLY_OLD, APPLY_NEW, "apply-save")
    text = sub(text, HIST_COMBO_OLD, HIST_COMBO_NEW, "hist-ac")
    text = one(CARD_HIT_OLD, CARD_HIT_NEW, "card-hit")
    text = one(ACHTML_FN, HELPERS, "helpers")
    text = one(ACH_ITEM_OLD, ACH_ITEM_NEW, "ac-item")
    text = one(FAV_NAME_OLD, FAV_NAME_NEW, "fav-name")
    text = sub(text, SHOW_OLD, SHOW_NEW, "show-lib")
    text = one(HTML_JOIN_OLD, HTML_JOIN_NEW, "html-join")
    text = one(PILLS_OLD, PILLS_NEW, "pills")
    text = sub(text, HIST_ROWS_OLD, HIST_ROWS_NEW, "hist-rows")
    text = one(SEARCH_ALL_OLD, SEARCH_ALL_NEW, "all-search")
    text = sub(text, WIPE_OLD, WIPE_NEW, "wipe")
    text = one(TITLE_SEARCH_OLD, TITLE_SEARCH_NEW, "title-search")
    text = one(TITLE_ALL_OLD, TITLE_ALL_NEW, "title-all")
    text = one(CSS_ITEM_OLD, CSS_ITEM_NEW, "css-ac")
    text = one(FW_OLD, FW_NEW, "fw-border")
    text = one(PANE_OLD, PANE_NEW, "kw-bottom")
    text = sub(text, KWFLUSH2_OLD, KWFLUSH2_NEW, "kw-status-flush")
    text = one(PORTRAIT_FW_OLD, PORTRAIT_FW_NEW, "portrait-fw")
    text = one(BIND_OLD, BIND_NEW, "bind-save")
    return text


def main():
    for path in FILES:
        text = path.read_text(encoding="utf-8")
        new = patch(text, path)
        path.write_text(new, encoding="utf-8")
        print(f"patched {path.name}")


if __name__ == "__main__":
    main()
