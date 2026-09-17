#!/usr/bin/env python3
"""Catalog pass: bottom overlay, content stripe, history/sessions, embed back, covers, tin identity."""
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


def sub_all_once(text, pairs):
    for old, new, label, *rest in pairs:
        optional = rest[0] if rest else False
        text = sub(text, old, new, label, optional=optional)
        print(f"  ok {label}")
    return text


CSS_BOTTOM_OLD = (
    "  body.display-sides a.bottom,body.display-sides a.top{display:inline-flex!important;align-items:center;justify-content:center;position:sticky!important;z-index:26;float:none;clear:none;align-self:flex-end;flex:0 0 auto;box-sizing:border-box;margin-right:.6rem}\n"
    "  body.display-sides a.bottom{position:relative!important;top:auto!important;margin:.12rem .65rem .2rem auto;z-index:11;align-self:flex-end;flex:0 0 auto}\n"
    "  body.display-sides #catalogIndex>a.bottom{order:0}\n"
)
CSS_BOTTOM_NEW = (
    "  body.display-sides a.bottom,body.display-sides a.top{display:inline-flex!important;align-items:center;justify-content:center;position:sticky!important;z-index:26;float:none;clear:none;align-self:flex-end;flex:0 0 auto;box-sizing:border-box;margin-right:.6rem}\n"
    "  body.display-sides #catalogBottomJump{position:sticky;top:var(--index-bar-h,2.75rem);z-index:11;height:0;margin:0;padding:0;overflow:visible;pointer-events:none;align-self:stretch;flex:0 0 0;display:flex;justify-content:flex-end;width:100%;box-sizing:border-box}\n"
    "  body.display-sides #catalogBottomJump>a.bottom,body.display-sides a.bottom{position:relative!important;top:.12rem!important;margin:0 .65rem 0 0;z-index:11;align-self:flex-end;flex:0 0 auto;pointer-events:auto}\n"
    "  body.display-sides #catalogIndex>a.bottom{position:absolute!important;top:var(--index-bar-h,2.75rem);right:.65rem;left:auto;margin:0!important;z-index:11;order:0;flex:0 0 auto;pointer-events:auto}\n"
)

CSS_HEAD_OLD = "  body.display-sides #catalogIndex .catalog-index-head{flex:0 0 auto;margin:0;padding:.45rem .7rem;cursor:pointer;border-bottom:1px solid var(--border);user-select:none;min-width:0}\n"
CSS_HEAD_NEW = "  body.display-sides #catalogIndex .catalog-index-head{flex:0 0 auto;margin:0;padding:.45rem .7rem;cursor:pointer;border-bottom:1px solid var(--border);user-select:none;min-width:0;position:relative;z-index:12}\n"

CSS_STRIPE_OLD = ".hover-scroll-host.has-hover-overflow>.hover-scroll-stripe:hover .hover-scroll-thumb,.hover-scroll-host.has-hover-overflow>.hover-scroll-stripe.is-dragging .hover-scroll-thumb{width:7px;opacity:.92;transform:scaleY(1.08);cursor:grabbing}\n"
CSS_STRIPE_NEW = """.hover-scroll-host.has-hover-overflow>.hover-scroll-stripe:hover .hover-scroll-thumb,.hover-scroll-host.has-hover-overflow>.hover-scroll-stripe.is-dragging .hover-scroll-thumb{width:7px;opacity:.92;transform:scaleY(1.08);cursor:grabbing}
#catalogMain>.hover-scroll-stripe{z-index:8;top:4px}
#catalogIndex>.hover-scroll-stripe{top:var(--index-bar-h,2.75rem);z-index:10}
#cardMinDock{position:fixed}
#cardMinDock .card-min-save{pointer-events:auto;display:inline-flex;align-items:center;justify-content:center;min-height:2.85rem;padding:0 .8rem;border:1px solid var(--accent-instrument);border-radius:999px;background:var(--bg-card);color:var(--accent-instrument);font:inherit;font-size:.9rem;font-weight:650;cursor:pointer;touch-action:manipulation;box-shadow:0 8px 28px rgba(0,0,0,.38)}
#cardMinSavePop{position:absolute;bottom:calc(100% + .45rem);left:50%;transform:translateX(-50%);z-index:10041;min-width:14rem;padding:.55rem;border:1px solid var(--border);border-radius:8px;background:var(--bg-surface);box-shadow:0 10px 28px rgba(0,0,0,.4);pointer-events:auto}
#cardMinSavePop[hidden]{display:none!important}
#cardMinSaveName{width:100%;box-sizing:border-box;min-height:2.25rem;margin:0 0 .4rem;padding:.3rem .5rem;border:1px solid var(--border);border-radius:6px;background:var(--bg-card);color:var(--text);font:inherit}
#cardMinSaveGo{width:100%;min-height:2.25rem;border:1px solid var(--accent-instrument);border-radius:6px;background:var(--accent-instrument-bg);color:var(--accent-instrument);font:inherit;cursor:pointer}
.entry>.cover>img,.entry .cover>img{display:block;visibility:visible;max-width:100%}
.search-autocomplete .ac-item.ac-session .ac-count,.search-autocomplete .ac-item.ac-combo .ac-count,.search-autocomplete .ac-item.ac-cardhit .ac-count{color:var(--text-muted)}
"""

ENSURE_OLD = """  parkCatalogDocNote(w);
  var bot=document.querySelector('a.bottom');
  if(!bot){
    bot=document.createElement('a');
    bot.className='bottom';
    bot.href='#catalogBottom';
    bot.textContent='\\u2193 bottom';
  }
  var topBtn=document.querySelector('a.top');
  var ixPark=document.getElementById('catalogIndex');
  var ixHead=ixPark&&ixPark.querySelector('.catalog-index-head');
  if(ixPark&&ixHead){
    if(bot.parentNode!==ixPark||bot.previousElementSibling!==ixHead){
      if(ixHead.nextSibling)ixPark.insertBefore(bot,ixHead.nextSibling);
      else ixPark.appendChild(bot);
    }
  }else if(bot.parentNode!==w||w.firstElementChild!==bot)w.insertBefore(bot,w.firstChild);
  if(typeof syncBottomBelowIndex==='function')syncBottomBelowIndex();
  if(typeof syncIndexEmbedBtn==='function')syncIndexEmbedBtn();
  if(topBtn){if(topBtn.parentNode!==w||w.lastElementChild!==topBtn)w.appendChild(topBtn);}
}"""

ENSURE_NEW = """  parkCatalogDocNote(w);
  var bot=document.querySelector('a.bottom');
  if(!bot){
    bot=document.createElement('a');
    bot.className='bottom';
    bot.href='#catalogBottom';
    bot.textContent='\\u2193 bottom';
  }
  var topBtn=document.querySelector('a.top');
  var hold=document.getElementById('catalogBottomJump');
  if(!hold){
    hold=document.createElement('div');
    hold.id='catalogBottomJump';
    hold.className='catalog-bottom-jump';
  }
  if(bot.parentNode!==hold)hold.appendChild(bot);
  var ixPark=document.getElementById('catalogIndex');
  if(ixPark&&ixPark.parentNode===w){
    if(hold.parentNode!==w||hold.previousElementSibling!==ixPark){
      if(ixPark.nextSibling)w.insertBefore(hold,ixPark.nextSibling);
      else w.appendChild(hold);
    }
  }else if(hold.parentNode!==w||w.firstElementChild!==hold)w.insertBefore(hold,w.firstChild);
  if(typeof syncBottomBelowIndex==='function')syncBottomBelowIndex();
  if(typeof syncIndexEmbedBtn==='function')syncIndexEmbedBtn();
  if(typeof window.bindMainHoverStripe==='function')window.bindMainHoverStripe();
  else if(typeof window.syncMainHoverStripe==='function')window.syncMainHoverStripe();
  if(typeof reviveEntryCovers==='function')reviveEntryCovers();
  if(topBtn){if(topBtn.parentNode!==w||w.lastElementChild!==topBtn)w.appendChild(topBtn);}
}"""

FIT_OLD = """  var head=ix.querySelector('.catalog-index-head');
  var hh=head?Math.round(head.getBoundingClientRect().height):0;
  var botEl=ix.querySelector(':scope > a.bottom');
  var bh=botEl?Math.round(botEl.getBoundingClientRect().height):0;
  var inner=Math.max(48,Math.round(ix.clientHeight-hh-bh));
"""
FIT_NEW = """  var head=ix.querySelector('.catalog-index-head');
  var hh=head?Math.round(head.getBoundingClientRect().height):0;
  var inner=Math.max(48,Math.round(ix.clientHeight-hh));
"""

BIND_OLD = """    function bind(){
      var n=ensure();
      if(!n)return;
      if(bound)return;
      bound=true;
"""
BIND_NEW = """    function bind(){
      var n=ensure();
      if(!n){
        if(document.documentElement&&!window['_hsObs_'+mark]){
          try{
            window['_hsObs_'+mark]=new MutationObserver(function(){if(!bound)bind();schedule();});
            window['_hsObs_'+mark].observe(document.documentElement,{childList:true,subtree:true});
          }catch(err){}
        }
        return;
      }
      if(bound){schedule();return;}
      bound=true;
"""

BOOT_OLD = """    function boot(){bind();schedule();}
    if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot);
    else boot();
    return schedule;
  }
  window.syncMainHoverStripe=bindStripe('catalogMain','catalogMain','content');
  window.syncIndexHoverStripe=bindStripe('catalogIndex','catalogIndexList','index');
})();
"""
BOOT_NEW = """    function boot(){bind();schedule();}
    if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot);
    else boot();
    window['bindHover_'+mark]=bind;
    return schedule;
  }
  window.syncMainHoverStripe=bindStripe('catalogMain','catalogMain','content');
  window.bindMainHoverStripe=window.bindHover_content||function(){if(window.syncMainHoverStripe)window.syncMainHoverStripe();};
  window.syncIndexHoverStripe=bindStripe('catalogIndex','catalogIndexList','index');
})();
"""

HIST_ANCHOR = "if(!searchCommitCounts||typeof searchCommitCounts!=='object'||Array.isArray(searchCommitCounts))searchCommitCounts={};\nvar notesMap=lsGet(NOTES_KEY,{});"
HIST_BLOCK = r"""if(!searchCommitCounts||typeof searchCommitCounts!=='object'||Array.isArray(searchCommitCounts))searchCommitCounts={};
var PIN_SESS_KEY='catalog-pin-sessions-'+(window.CATALOG_NS||'catalog');
var KW_COMBO_KEY='catalog-kw-combos-'+(window.CATALOG_NS||'catalog');
var CARD_HIT_KEY='catalog-card-hits-'+(window.CATALOG_NS||'catalog');
var RECENT_KW_KEY='catalog-recent-kws-'+(window.CATALOG_NS||'catalog');
var PIN_SESS_MAX=12;
var pinSessionStore=lsGet(PIN_SESS_KEY,{sessions:[],recent:[]});
if(!pinSessionStore||typeof pinSessionStore!=='object')pinSessionStore={sessions:[],recent:[]};
if(!Array.isArray(pinSessionStore.sessions))pinSessionStore.sessions=[];
if(!Array.isArray(pinSessionStore.recent))pinSessionStore.recent=[];
var kwComboStore=lsGet(KW_COMBO_KEY,[]);
if(!Array.isArray(kwComboStore))kwComboStore=[];
var cardHitStore=lsGet(CARD_HIT_KEY,{});
if(!cardHitStore||typeof cardHitStore!=='object'||Array.isArray(cardHitStore))cardHitStore={};
var recentKwStore=lsGet(RECENT_KW_KEY,[]);
if(!Array.isArray(recentKwStore))recentKwStore=[];
function persistPinSessions(){lsSet(PIN_SESS_KEY,{sessions:pinSessionStore.sessions.slice(0,PIN_SESS_MAX),recent:(pinSessionStore.recent||[]).slice(0,6)});}
function persistKwCombos(){lsSet(KW_COMBO_KEY,kwComboStore.slice(0,10));}
function persistCardHits(){
  var keys=Object.keys(cardHitStore||{});
  if(keys.length>80){
    keys.sort(function(a,b){var A=cardHitStore[a]||{},B=cardHitStore[b]||{};return (B.n||0)-(A.n||0)||(B.t||0)-(A.t||0);});
    var keep={};keys.slice(0,80).forEach(function(k){keep[k]=cardHitStore[k];});
    cardHitStore=keep;
  }
  lsSet(CARD_HIT_KEY,cardHitStore);
}
function persistRecentKws(){lsSet(RECENT_KW_KEY,recentKwStore.slice(0,10));}
function isLibraryNameQuery(text){
  var t=String(text||'').replace(/^\s+|\s+$/g,'').toLowerCase();
  if(!t)return false;
  if(typeof searchMeta!=='undefined'&&searchMeta[t]&&searchMeta[t].isLibName)return true;
  try{
    if(typeof entries!=='undefined'){
      for(var i=0;i<entries.length;i++){
        var n=(typeof entryName==='function'?entryName(entries[i]):(entries[i].getAttribute&&entries[i].getAttribute('data-name')))||'';
        if(String(n).toLowerCase()===t)return true;
      }
    }
  }catch(err){}
  return false;
}
function recordRecentKeyword(text){
  var t=String(text||'').replace(/^\s+|\s+$/g,'');
  if(!t||isLibraryNameQuery(t))return;
  recentKwStore=recentKwStore.filter(function(x){return String(x).toLowerCase()!==t.toLowerCase();});
  recentKwStore.unshift(t);
  persistRecentKws();
}
function snapshotKwCombo(){
  var pills=(typeof searchKeywords!=='undefined'&&searchKeywords&&searchKeywords.length)?searchKeywords.slice():[];
  if(!pills.length)return;
  var key=pills.map(function(x){return String(x).toLowerCase();}).sort().join('\u001f');
  kwComboStore=kwComboStore.filter(function(o){return o&&o.key!==key;});
  kwComboStore.unshift({key:key,pills:pills.slice(),t:Date.now()});
  persistKwCombos();
}
function recordCardHit(el){
  if(!el)return;
  var id=el.id||'';
  var name=(typeof entryName==='function'?entryName(el):(el.getAttribute&&el.getAttribute('data-name')))||'';
  if(!id&&!name)return;
  var k=id||name;
  var cur=cardHitStore[k]||{id:id,name:name,n:0,t:0};
  cur.id=id||cur.id;cur.name=name||cur.name;cur.n=(cur.n||0)+1;cur.t=Date.now();
  cardHitStore[k]=cur;
  persistCardHits();
}
function pinTinKindOf(item){
  if(!item)return 'preview';
  if(item.kind==='highlight'||item.mode==='highlight')return 'highlight';
  return 'preview';
}
function snapshotPinSessionCards(){
  return (typeof cardMinDockItems!=='undefined'?cardMinDockItems:[]).map(function(it){
    return {id:it.id,mode:it.mode||'preview',kind:pinTinKindOf(it),name:it.name||''};
  });
}
function pinSessionId(){return 's'+Date.now().toString(36)+Math.floor(Math.random()*1e4).toString(36);}
window.savePinSession=function(name){
  name=String(name||'').replace(/^\s+|\s+$/g,'');
  if(!name)return false;
  var cards=snapshotPinSessionCards();
  if(!cards.length)return false;
  var front=typeof cardMinExpanded==='function'?cardMinExpanded():null;
  var rec={id:pinSessionId(),name:name,savedAt:Date.now(),usedAt:Date.now(),cards:cards,frontId:front&&front.id||'',frontKind:front?cardMinTinKind(front):''};
  var exist=-1;
  pinSessionStore.sessions.forEach(function(s,i){if(s&&String(s.name).toLowerCase()===name.toLowerCase())exist=i;});
  if(exist>=0){rec.id=pinSessionStore.sessions[exist].id;pinSessionStore.sessions[exist]=rec;}
  else{
    if(pinSessionStore.sessions.length>=PIN_SESS_MAX){
      pinSessionStore.sessions.sort(function(a,b){return (a.usedAt||a.savedAt||0)-(b.usedAt||b.savedAt||0);});
      pinSessionStore.sessions.shift();
    }
    pinSessionStore.sessions.push(rec);
  }
  touchPinSession(rec.id);
  persistPinSessions();
  return true;
};
function touchPinSession(id){
  pinSessionStore.recent=(pinSessionStore.recent||[]).filter(function(x){return x!==id;});
  pinSessionStore.recent.unshift(id);
  pinSessionStore.recent=pinSessionStore.recent.slice(0,6);
  pinSessionStore.sessions.forEach(function(s){if(s&&s.id===id)s.usedAt=Date.now();});
}
window.restorePinSession=function(id){
  var sess=null;
  (pinSessionStore.sessions||[]).forEach(function(s){if(s&&s.id===id)sess=s;});
  if(!sess||!sess.cards)return;
  touchPinSession(id);persistPinSessions();
  cardMinDockItems=[];
  sess.cards.forEach(function(c){
    if(!c||!c.id)return;
    cardMinDockItems.push({id:c.id,mode:c.mode||c.kind||'preview',kind:c.kind||(c.mode==='highlight'?'highlight':'preview'),name:c.name||''});
  });
  if(typeof cardMinRender==='function')cardMinRender();
  var frontId=sess.frontId||(sess.cards[0]&&sess.cards[0].id);
  var frontKind=sess.frontKind||(sess.cards[0]&&(sess.cards[0].kind||sess.cards[0].mode))||'preview';
  if(frontId&&typeof cardMinRestore==='function')cardMinRestore(frontId,frontKind);
};
window.deletePinSession=function(id){
  pinSessionStore.sessions=(pinSessionStore.sessions||[]).filter(function(s){return s&&s.id!==id;});
  pinSessionStore.recent=(pinSessionStore.recent||[]).filter(function(x){return x!==id;});
  persistPinSessions();
};
window.applyKwCombo=function(key){
  var hit=null;
  (kwComboStore||[]).forEach(function(o){if(o&&o.key===key)hit=o;});
  if(!hit||!hit.pills)return;
  if(typeof setMode==='function')setMode('search');
  searchKeywords=hit.pills.slice();
  if(typeof renderPills==='function')renderPills();
  if(typeof applySearch==='function')applySearch();
  if(typeof renderKwBar==='function')renderKwBar();
};
window.openCardHit=function(id){
  var el=id&&document.getElementById(id);
  if(!el)return;
  if(typeof openChosenPreview==='function')openChosenPreview(el);
};
function catalogHistMatch(label,q){
  if(!q)return true;
  return String(label||'').toLowerCase().indexOf(q)>=0;
}
function catalogAcHistoryHtml(q){
  var html='',q=String(q||'').toLowerCase();
  function jsStr(s){return String(s||'').replace(/\\/g,'\\\\').replace(/'/g,"\\'");}
  function htmlStr(s){return String(s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');}
  var sessions=(pinSessionStore.sessions||[]).slice().sort(function(a,b){return (b.usedAt||b.savedAt||0)-(a.usedAt||a.savedAt||0);}).filter(function(s){return s&&catalogHistMatch(s.name,q);});
  var saved=sessions.slice(0,PIN_SESS_MAX);
  if(saved.length){
    html+='<div class="ac-group-label">Saved sessions</div>';
    saved.forEach(function(s){
      html+='<div class="ac-item ac-session" data-cat="session" onclick="restorePinSession(\''+jsStr(s.id)+'\')"><span class="ac-label">'+htmlStr(s.name||'Session')+'</span><span class="ac-count">'+(s.cards&&s.cards.length||0)+'</span></div>';
    });
  }
  if((pinSessionStore.sessions||[]).length>6){
    var recentIds=pinSessionStore.recent||[];
    var savedIds={};saved.forEach(function(s){savedIds[s.id]=1;});
    var rec=[];
    recentIds.forEach(function(id){
      var s=null;(pinSessionStore.sessions||[]).forEach(function(x){if(x&&x.id===id)s=x;});
      if(s&&catalogHistMatch(s.name,q)&&rec.length<6)rec.push(s);
    });
    if(rec.length){
      html+='<div class="ac-group-label">Recent sessions</div>';
      rec.forEach(function(s){
        html+='<div class="ac-item ac-session" data-cat="session" onclick="restorePinSession(\''+jsStr(s.id)+'\')"><span class="ac-label">'+htmlStr(s.name||'Session')+'</span><span class="ac-count">'+(s.cards&&s.cards.length||0)+'</span></div>';
      });
    }
  }
  var combos=(kwComboStore||[]).filter(function(o){return o&&catalogHistMatch((o.pills||[]).join(' + '),q);}).slice(0,10);
  if(combos.length){
    html+='<div class="ac-group-label">Keyword combos</div>';
    combos.forEach(function(o){
      var lab=(o.pills||[]).join(' + ');
      html+='<div class="ac-item ac-combo" data-cat="combo" onclick="applyKwCombo(\''+jsStr(o.key)+'\')"><span class="ac-label">'+htmlStr(lab)+'</span></div>';
    });
  }
  var hits=Object.keys(cardHitStore||{}).map(function(k){return cardHitStore[k];}).filter(function(o){return o&&catalogHistMatch(o.name||o.id,q);}).sort(function(a,b){return (b.n||0)-(a.n||0)||(b.t||0)-(a.t||0);}).slice(0,10);
  if(hits.length){
    html+='<div class="ac-group-label">Top card hits</div>';
    hits.forEach(function(o){
      html+='<div class="ac-item ac-cardhit" data-cat="card" onclick="openCardHit(\''+jsStr(o.id)+'\')"><span class="ac-label">'+htmlStr(o.name||o.id)+'</span><span class="ac-count">'+(o.n||1)+'</span></div>';
    });
  }
  var recK=(recentKwStore||[]).filter(function(t){return catalogHistMatch(t,q);}).slice(0,10);
  if(recK.length){
    html+='<div class="ac-group-label">Recent keywords</div>';
    recK.forEach(function(t){
      html+='<div class="ac-item" data-cat="recent" onclick="pickAc(\''+jsStr(t)+'\')"><span class="ac-label">'+htmlStr(t)+'</span></div>';
    });
  }
  return html;
}
window.catalogAcHistoryHtml=catalogAcHistoryHtml;
var notesMap=lsGet(NOTES_KEY,{});
"""

COMMIT_OLD = """function commitSearchTokens(text){
  text=String(text||'').trim().toLowerCase();
  if(!text)return;
  var seen={};
  text.split(/[\\s,;/|]+/).forEach(function(t){
    t=String(t||'').replace(/^[^\\w]+|[^\\w]+$/g,'').toLowerCase();
    if(!t||seen[t]||t.length<3)return;
    if(typeof PATCH_STOP!=='undefined'&&PATCH_STOP[t])return;
    if(typeof usefulPatchToken==='function'&&!usefulPatchToken(t)&&!(typeof kwCounts!=='undefined'&&kwCounts[t]))return;
    seen[t]=1;
    searchCommitCounts[t]=(searchCommitCounts[t]||0)+1;
  });
  persistSearchCommits();
}"""
COMMIT_NEW = """function commitSearchTokens(text){
  text=String(text||'').trim();
  if(!text)return;
  if(typeof isLibraryNameQuery==='function'&&isLibraryNameQuery(text))return;
  var low=text.toLowerCase();
  var seen={};
  low.split(/[\\s,;/|]+/).forEach(function(t){
    t=String(t||'').replace(/^[^\\w]+|[^\\w]+$/g,'').toLowerCase();
    if(!t||seen[t]||t.length<3)return;
    if(typeof isLibraryNameQuery==='function'&&isLibraryNameQuery(t))return;
    if(typeof PATCH_STOP!=='undefined'&&PATCH_STOP[t])return;
    if(typeof usefulPatchToken==='function'&&!usefulPatchToken(t)&&!(typeof kwCounts!=='undefined'&&kwCounts[t]))return;
    seen[t]=1;
    searchCommitCounts[t]=(searchCommitCounts[t]||0)+1;
  });
  persistSearchCommits();
  if(typeof recordRecentKeyword==='function')recordRecentKeyword(text);
}"""

SHOW_HIST_OLD = "var mainHtml=acHtml(list,100,!q);\nvar favHtml=favAcHtml(favs,ranked);\nvar hasMain=mainHtml.length>0;\nvar hasCommits=(ranked||[]).some(function(o){return o&&o.searchCommits>0;});\n// Never open the dropdown solely to dump favorite suggestions.\nif(!q&&!hasMain&&!hasCommits&&!opts.force){\n"
SHOW_HIST_NEW = "var histHtml=typeof catalogAcHistoryHtml==='function'?catalogAcHistoryHtml(q):'';\nvar mainHtml=acHtml(list,100,!q);\nvar favHtml=favAcHtml(favs,ranked);\nvar hasMain=mainHtml.length>0;\nvar hasCommits=(ranked||[]).some(function(o){return o&&o.searchCommits>0;});\n// Never open the dropdown solely to dump favorite suggestions.\nif(!q&&!hasMain&&!hasCommits&&!histHtml&&!opts.force){\n"

SHOW_HTML_OLD = "var html=(hasMain||hasCommits||!!q||opts.force)?(favHtml+mainHtml):'';\nacList.innerHTML=html;acList.classList.toggle('open',html.length>0);if(window.syncAcScrollStripe)window.syncAcScrollStripe();\n"
SHOW_HTML_NEW = "var html=(histHtml||'')+((hasMain||hasCommits||!!q||opts.force)?(favHtml+mainHtml):'');\nacList.innerHTML=html;acList.classList.toggle('open',html.length>0);if(window.syncAcScrollStripe)window.syncAcScrollStripe();\n"

PICK_OLD = """window.pickAc=function(text){
if(!searchInput)return;
searchInput.value=text||'';
commitSearchTokens(text);
"""
PICK_NEW = """window.pickAc=function(text){
if(!searchInput)return;
searchInput.value=text||'';
if(!(typeof isLibraryNameQuery==='function'&&isLibraryNameQuery(text)))commitSearchTokens(text);
else{
  var el=null;
  try{if(typeof entries!=='undefined')entries.forEach(function(e){if(!el&&String((typeof entryName==='function'?entryName(e):'')||'').toLowerCase()===String(text||'').toLowerCase())el=e;});}catch(err){}
  if(el&&typeof recordCardHit==='function')recordCardHit(el);
}
"""

ADDKW_OLD = "searchKeywords.push(kw);renderPills();applySearch();\n"
ADDKW_NEW = "searchKeywords.push(kw);renderPills();applySearch();if(typeof recordRecentKeyword==='function')recordRecentKeyword(kw);if(typeof snapshotKwCombo==='function')snapshotKwCombo();\n"

CLEAR_OLD = """  searchCommitCounts={};
  if(typeof lsSet==='function'&&typeof SEARCH_COMMIT_KEY!=='undefined')lsSet(SEARCH_COMMIT_KEY,{});
"""
CLEAR_NEW = """  searchCommitCounts={};
  if(typeof lsSet==='function'&&typeof SEARCH_COMMIT_KEY!=='undefined')lsSet(SEARCH_COMMIT_KEY,{});
  kwComboStore=[];recentKwStore=[];cardHitStore={};
  if(typeof persistKwCombos==='function')persistKwCombos();
  if(typeof persistRecentKws==='function')persistRecentKws();
  if(typeof persistCardHits==='function')persistCardHits();
"""

COVER_SRC_OLD = """function cardMinCoverSrc(el){
  var img=el&&el.querySelector('.cover img');
  return img?(img.getAttribute('src')||''):'';
}"""
COVER_SRC_NEW = """function cardMinCoverSrc(el){
  var img=el&&(el.querySelector(':scope > .cover > img')||el.querySelector('.cover > img'));
  if(!img)return '';
  return img.getAttribute('data-cover-src')||img.getAttribute('src')||'';
}
function reviveEntryCovers(){
  document.querySelectorAll('.entry .cover > img').forEach(function(img){
    var src=img.getAttribute('src')||'';
    var pin=img.getAttribute('data-cover-src')||'';
    if(src&&src!=='about:blank'&&!pin){img.setAttribute('data-cover-src',src);pin=src;}
    if((!src||src==='about:blank'||!(img.complete&&img.naturalWidth>0))&&pin){
      img.src=pin;
    }
  });
}
window.reviveEntryCovers=reviveEntryCovers;
"""

INDEX_OLD = """function cardMinIndex(id){
  for(var i=0;i<cardMinDockItems.length;i++)if(cardMinDockItems[i].id===id)return i;
  return -1;
}"""
INDEX_NEW = """function cardMinTinKind(el,mode){
  if(mode==='highlight')return 'highlight';
  if(mode==='preview'||mode==='embed')return 'preview';
  if(el&&el.classList.contains('highlight'))return 'highlight';
  if(document.body.classList.contains('hl-open')&&el&&(el.classList.contains('highlight')||el===document.querySelector('.entry.highlight')))return 'highlight';
  if(document.body.classList.contains('hl-open')&&!document.body.classList.contains('chosen-preview-open'))return 'highlight';
  return 'preview';
}
function cardMinIndex(id,kind){
  kind=kind||'preview';
  for(var i=0;i<cardMinDockItems.length;i++){
    var it=cardMinDockItems[i];
    if(it.id===id&&(it.kind||(it.mode==='highlight'?'highlight':'preview'))===kind)return i;
  }
  return -1;
}"""

DISMISS_OLD = """function cardMinDismissOpen(){
  var el=cardMinExpanded();
  if(!el||!el.id)return;
  cardMinClose(el.id,true);
}"""
DISMISS_NEW = """function cardMinDismissOpen(){
  var el=cardMinExpanded();
  if(!el||!el.id)return;
  cardMinClose(el.id,true,cardMinTinKind(el));
}"""

PARK_OLD = """  var slot=document.querySelector('#cardMinDock .card-min-pill[data-card-min-id="'+id+'"] .card-min-media');
"""
PARK_NEW = """  var slot=document.querySelector('#cardMinDock .card-min-pill[data-card-min-id="'+id+'"][data-card-min-kind="preview"] .card-min-media');
"""

CLOSE_OLD = """function cardMinClose(id,fromOpen){
  if(!id)return;
  var i=cardMinIndex(id);
  var wasOwner=window.cardMinMediaOwnerId===id;
  if(wasOwner){
    window.cardMinMediaOwnerId='';
    if(typeof closeCardSearchEmbed==='function')closeCardSearchEmbed();
  }
"""
CLOSE_NEW = """function cardMinClose(id,fromOpen,kind){
  if(!id)return;
  var i=(kind!=null&&kind!=='')?cardMinIndex(id,kind):cardMinIndex(id,cardMinTinKind(cardMinExpanded()));
  if(i<0&&(kind==null||kind==='')){
    for(var j=0;j<cardMinDockItems.length;j++)if(cardMinDockItems[j].id===id){i=j;break;}
  }
  var closedKind=(i>=0)?(cardMinDockItems[i].kind||(cardMinDockItems[i].mode==='highlight'?'highlight':'preview')):(kind||'preview');
  var wasOwner=window.cardMinMediaOwnerId===id&&closedKind==='preview';
  if(wasOwner){
    var stillPreview=false;
    for(var k=0;k<cardMinDockItems.length;k++){
      if(k===i)continue;
      var it=cardMinDockItems[k];
      if(it.id===id&&(it.kind||(it.mode==='highlight'?'highlight':'preview'))==='preview')stillPreview=true;
    }
    if(!stillPreview){
      window.cardMinMediaOwnerId='';
      if(typeof closeCardSearchEmbed==='function')closeCardSearchEmbed();
    }
  }
"""

RENDER_PILL_OLD = """    pill.setAttribute('data-card-min-id',item.id);
    pill.setAttribute('data-card-min-slot',idx===0?'left':(idx===cardMinDockItems.length-1&&cardMinDockItems.length>1?'right':'middle'));
"""
RENDER_PILL_NEW = """    pill.setAttribute('data-card-min-id',item.id);
    pill.setAttribute('data-card-min-kind',item.kind||(item.mode==='highlight'?'highlight':'preview'));
    pill.setAttribute('data-card-min-slot',idx===0?'left':(idx===cardMinDockItems.length-1&&cardMinDockItems.length>1?'right':'middle'));
"""

RENDER_MEDIA_OLD = """    var slot=d.querySelector('.card-min-pill[data-card-min-id="'+window.cardMinMediaOwnerId+'"] .card-min-media');
"""
RENDER_MEDIA_NEW = """    var slot=d.querySelector('.card-min-pill[data-card-min-id="'+window.cardMinMediaOwnerId+'"][data-card-min-kind="preview"] .card-min-media');
"""

PLAYING_OLD = """    var playing=window.cardMinMediaOwnerId===item.id;
    var pill=document.createElement('div');
    pill.className='card-min-pill'+(item.id===curId?' is-front':'')+(playing?' is-playing':'');
"""
PLAYING_NEW = """    var itemKind=item.kind||(item.mode==='highlight'?'highlight':'preview');
    var curKind=cur?cardMinTinKind(cur):'';
    var playing=window.cardMinMediaOwnerId===item.id&&itemKind==='preview';
    var pill=document.createElement('div');
    pill.className='card-min-pill'+(item.id===curId&&itemKind===curKind?' is-front':'')+(playing?' is-playing':'');
"""

ARIA_OLD = """    open.setAttribute('aria-pressed',item.id===curId?'true':'false');
    open.setAttribute('aria-label',(el?cardMinShortName(el):(item.name||'Library'))+' (restore)');
"""
ARIA_NEW = """    open.setAttribute('aria-pressed',item.id===curId&&itemKind===curKind?'true':'false');
    open.setAttribute('aria-label',(el?cardMinShortName(el):(item.name||'Library'))+(itemKind==='highlight'?' fullscreen':' embed')+' (restore)');
"""

SAVE_DOCK_OLD = """    if(host&&slot&&!slot.contains(host)&&!cardMinExpanded())slot.appendChild(host);
  }
  cardMinPlace();
"""
SAVE_DOCK_NEW = """    if(host&&slot&&!slot.contains(host)&&!cardMinExpanded())slot.appendChild(host);
  }
  var sav=document.createElement('button');
  sav.type='button';
  sav.className='card-min-save';
  sav.id='cardMinDockSave';
  sav.hidden=cardMinDockItems.length===0;
  sav.textContent='Save';
  sav.setAttribute('aria-label','Save pinned session');
  sav.title='Save pinned cards as a named session';
  d.appendChild(sav);
  var pop=document.getElementById('cardMinSavePop');
  if(!pop){
    pop=document.createElement('div');
    pop.id='cardMinSavePop';
    pop.hidden=true;
    pop.innerHTML='<input id="cardMinSaveName" type="text" maxlength="40" placeholder="Session name" autocomplete="off"><button type="button" id="cardMinSaveGo">Save session</button>';
    d.appendChild(pop);
  }else d.appendChild(pop);
  cardMinPlace();
"""

MIN_BODY_OLD = """  var mode=cardMinMode(entry);
  var i=cardMinIndex(entry.id);
  var rec={id:entry.id,mode:mode,name:cardMinShortName(entry)};
  if(i>=0)cardMinDockItems[i].mode=mode;
  else{
    cardMinDockItems.push(rec);
    while(cardMinDockItems.length>CARD_MIN_MAX){
      var drop=cardMinDockItems.shift();
      if(drop&&drop.id===window.cardMinMediaOwnerId){
        window.cardMinMediaOwnerId='';
        if(typeof closeCardSearchEmbed==='function')closeCardSearchEmbed();
      }
    }
  }
"""
MIN_BODY_NEW = """  var mode=cardMinMode(entry);
  var kind=cardMinTinKind(entry,mode);
  var i=cardMinIndex(entry.id,kind);
  var rec={id:entry.id,mode:mode,kind:kind,name:cardMinShortName(entry)};
  if(i>=0){cardMinDockItems[i].mode=mode;cardMinDockItems[i].kind=kind;cardMinDockItems[i].name=rec.name;}
  else{
    cardMinDockItems.push(rec);
    while(cardMinDockItems.length>CARD_MIN_MAX){
      var drop=cardMinDockItems.shift();
      if(drop&&drop.id===window.cardMinMediaOwnerId&&(drop.kind||(drop.mode==='highlight'?'highlight':'preview'))==='preview'){
        window.cardMinMediaOwnerId='';
        if(typeof closeCardSearchEmbed==='function')closeCardSearchEmbed();
      }
    }
  }
"""

PARK_KEEP_OLD = "  if(keep&&typeof cardMinParkMedia==='function')cardMinParkMedia(entry.id);\n"
PARK_KEEP_NEW = "  if(keep&&kind==='preview'&&typeof cardMinParkMedia==='function')cardMinParkMedia(entry.id);\n"

RESTORE_OLD = """function cardMinRestore(id){
  var i=cardMinIndex(id);
  if(i<0)return;
  var item=cardMinDockItems[i];
  var el=document.getElementById(item.id);
  if(!el){cardMinDockItems.splice(i,1);cardMinRender();return;}
  var cur=cardMinExpanded();
  if(cur&&cur!==el){
    var ci=cardMinIndex(cur.id);
    if(ci>=0)cardMinDockItems[ci].mode=cardMinMode(cur);
    if(document.body.classList.contains('hl-open')||cur.classList.contains('highlight'))closeOverlay({skipScroll:true});
    else if(document.body.classList.contains('chosen-preview-open'))closeChosenPreview({skipJumpExit:true,skipDismiss:true,keepMedia:true});
  }
  if(item.mode==='highlight')openOverlay(el);
  else openChosenPreview(el);
  if(typeof cardMinRestoreMedia==='function')cardMinRestoreMedia(id);
  cardMinRender();
}
function cardMinActivate(id){
  var cur=cardMinExpanded();
  if(cur&&cur.id===id){minimizeExpandedCard(cur);return;}
  cardMinRestore(id);
}
function cardMinTabNext(){
  var n=cardMinDockItems.length;
  if(!n)return;
  var cur=cardMinExpanded();
  var idx=cur?cardMinIndex(cur.id):-1;
  var next=(idx<0)?0:((idx+1)%n);
  cardMinRestore(cardMinDockItems[next].id);
}"""
RESTORE_NEW = """function cardMinRestore(id,kind){
  var i=cardMinIndex(id,kind||'preview');
  if(i<0){for(var j=0;j<cardMinDockItems.length;j++)if(cardMinDockItems[j].id===id){i=j;break;}}
  if(i<0)return;
  var item=cardMinDockItems[i];
  var el=document.getElementById(item.id);
  if(!el){cardMinDockItems.splice(i,1);cardMinRender();return;}
  var cur=cardMinExpanded();
  var wantKind=item.kind||(item.mode==='highlight'?'highlight':'preview');
  if(cur){
    var ck=cardMinTinKind(cur);
    if(cur!==el||ck!==wantKind){
      var ci=cardMinIndex(cur.id,ck);
      if(ci>=0){cardMinDockItems[ci].mode=cardMinMode(cur);cardMinDockItems[ci].kind=ck;}
      if(document.body.classList.contains('hl-open')||cur.classList.contains('highlight'))closeOverlay({skipScroll:true});
      else if(document.body.classList.contains('chosen-preview-open'))closeChosenPreview({skipJumpExit:true,skipDismiss:true,keepMedia:true});
    }
  }
  if(wantKind==='highlight'||item.mode==='highlight')openOverlay(el);
  else openChosenPreview(el);
  if(wantKind!=='highlight'&&typeof cardMinRestoreMedia==='function')cardMinRestoreMedia(id);
  cardMinRender();
}
function cardMinActivate(id,kind){
  var cur=cardMinExpanded();
  var ck=cur?cardMinTinKind(cur):'';
  if(cur&&cur.id===id&&ck===(kind||ck)){minimizeExpandedCard(cur);return;}
  cardMinRestore(id,kind);
}
function cardMinTabNext(){
  var n=cardMinDockItems.length;
  if(!n)return;
  var cur=cardMinExpanded();
  var idx=cur?cardMinIndex(cur.id,cardMinTinKind(cur)):-1;
  var next=(idx<0)?0:((idx+1)%n);
  var it=cardMinDockItems[next];
  cardMinRestore(it.id,it.kind||(it.mode==='highlight'?'highlight':'preview'));
}"""

CLICK_OLD = """      if(xp)cardMinClose(xp.getAttribute('data-card-min-id'));
      e.preventDefault();e.stopPropagation();return;
    }
    var pill=e.target.closest('.card-min-pill');
    if(pill){cardMinActivate(pill.getAttribute('data-card-min-id'));e.preventDefault();e.stopPropagation();return;}
"""
CLICK_NEW = """      if(xp)cardMinClose(xp.getAttribute('data-card-min-id'),false,xp.getAttribute('data-card-min-kind')||'preview');
      e.preventDefault();e.stopPropagation();return;
    }
    if(e.target.closest('#cardMinDockSave,.card-min-save')){
      e.preventDefault();e.stopPropagation();
      var pop=document.getElementById('cardMinSavePop');
      if(pop){
        pop.hidden=!pop.hidden;
        var inp=document.getElementById('cardMinSaveName');
        if(!pop.hidden&&inp)inp.focus();
      }
      return;
    }
    if(e.target.closest('#cardMinSaveGo')){
      e.preventDefault();e.stopPropagation();
      var inp2=document.getElementById('cardMinSaveName');
      var nm=inp2?inp2.value:'';
      if(typeof savePinSession==='function'&&savePinSession(nm)){
        var p2=document.getElementById('cardMinSavePop');if(p2)p2.hidden=true;
        if(typeof showAc==='function')showAc((searchInput&&searchInput.value||'').trim().toLowerCase(),{force:true});
      }
      return;
    }
    var pill=e.target.closest('.card-min-pill');
    if(pill){cardMinActivate(pill.getAttribute('data-card-min-id'),pill.getAttribute('data-card-min-kind')||'preview');e.preventDefault();e.stopPropagation();return;}
"""

OCP_OLD = """function openChosenPreview(el){
  if(!el)return;
  parkSearchBehindOverlay();
"""
OCP_NEW = """function openChosenPreview(el){
  if(!el)return;
  if(typeof recordCardHit==='function')recordCardHit(el);
  parkSearchBehindOverlay();
"""

OO_OLD = None  # find openOverlay
# We'll patch a unique first line inside openOverlay after the function starts if needed.

SEARCH_MODAL_OLD = """window.openSearchModal = function(btn) {
  var card = btn.closest && btn.closest('.entry');
"""
SEARCH_MODAL_NEW = """window.openSearchModal = function(btn) {
  var card = btn.closest && btn.closest('.entry');
  if(card&&typeof recordCardHit==='function')recordCardHit(card);
"""

YT_HIST_OLD = "  cardSearchState.embedUrl=url;\n  cardSearchState.history=[url];\n"
YT_HIST_NEW = """  cardSearchState.embedUrl=url;
  if(!(opts&&opts.noHist)&&typeof cardSearchHistPush==='function')cardSearchHistPush({kind:'yt',type:'yt',view:'yt',ytId:id,embedUrl:url,host:cardSearchState._ytHost});
  else if(!(opts&&opts.noHist))cardSearchState.history=(cardSearchState.history||[]).concat([url]);
"""

WEB_HIST_OLD = "  cardSearchState.view='article';\n  cardSearchState.history=['results','article'];\n"
WEB_HIST_NEW = "  cardSearchState.view='article';\n  if(typeof cardSearchHistPush==='function')cardSearchHistPush({kind:'article',view:'article',type:cardSearchState.type||'web',i:i});\n  else cardSearchState.history=['results','article'];\n"

GOOGLE_HIST_OLD = "  cardSearchState.history=[cardSearchState.view];\n"
GOOGLE_HIST_NEW = "  if(typeof cardSearchHistPush==='function')cardSearchHistPush({kind:'root',view:cardSearchState.view,type:cardSearchState.type});\n  else cardSearchState.history=[cardSearchState.view];\n"

IMG_GRID_OLD = "  cardSearchState.history=['grid'];\n  if(!items||!items.length){\n"
IMG_GRID_NEW = "  if(typeof cardSearchHistPush==='function')cardSearchHistPush({kind:'grid',view:'grid',type:'img'});\n  else cardSearchState.history=['grid'];\n  if(!items||!items.length){\n"

IMG_OPEN_OLD = "  cardSearchState.view='image';\n  cardSearchState.history=['grid','image'];\n"
IMG_OPEN_NEW = "  cardSearchState.view='image';\n  if(typeof cardSearchHistPush==='function')cardSearchHistPush({kind:'image',view:'image',type:'img',i:i,src:src});\n  else cardSearchState.history=['grid','image'];\n"

EXIT_IMG_OLD = "  cardSearchState.view='grid';\n  cardSearchState.history=['grid'];\n"
EXIT_IMG_NEW = """  cardSearchState.view='grid';
  if(cardSearchState.history&&cardSearchState.history.length){
    var _last=cardSearchState.history[cardSearchState.history.length-1];
    var _isImg=_last==='image'||(_last&&(_last.kind==='image'||_last.view==='image'));
    if(_isImg)cardSearchState.history.pop();
  }
"""

ENABLE_OLD = """function cardSearchEnableBack(){
  var back=document.querySelector('#cardSearchEmbed .card-search-back');
  if(back){back.disabled=false;back.removeAttribute('disabled');}
}"""
ENABLE_NEW = """function cardSearchEnableBack(){
  var back=document.querySelector('#cardSearchEmbed .card-search-back');
  if(back){back.disabled=false;back.removeAttribute('disabled');}
}
function cardSearchHistEq(a,b){
  if(a===b)return true;
  if(!a||!b)return false;
  if(typeof a==='string'||typeof b==='string')return String(a)===String(b);
  return (a.kind||'')===(b.kind||'')&&(a.view||'')===(b.view||'')&&(a.ytId||'')===(b.ytId||'')&&(a.embedUrl||'')===(b.embedUrl||'')&&a.i===b.i;
}
function cardSearchHistPush(snap){
  if(!cardSearchState.history)cardSearchState.history=[];
  var last=cardSearchState.history[cardSearchState.history.length-1];
  if(last&&cardSearchHistEq(last,snap))return;
  cardSearchState.history.push(snap);
  if(cardSearchState.history.length>40)cardSearchState.history.shift();
  cardSearchEnableBack();
}
function cardSearchApplyHist(snap){
  if(snap==null)return;
  if(typeof snap==='string'){
    if(snap==='results'){if(typeof cardSearchShowWebResults==='function')cardSearchShowWebResults();return;}
    if(snap==='grid'){if(window.cardSearchExitImage)window.cardSearchExitImage();return;}
    if(snap==='article'||snap==='image'||snap==='yt')return;
    var frame=document.getElementById('cardSearchFrame');
    cardSearchState.embedUrl=snap;
    if(frame){frame.src=snap;frame.classList.remove('is-hidden');}
    if(typeof showCardSearchFrame==='function')showCardSearchFrame(true);
    return;
  }
  var kind=snap.kind||snap.view||'';
  if(kind==='root'||kind==='yt-list'||kind==='grid'&&snap.type==='img'){
    if((cardSearchState.type==='yt'||kind==='yt-list'||kind==='root'&&cardSearchState.type==='yt')&&kind!=='grid'){
      if(typeof showCardSearchFrame==='function')showCardSearchFrame(false);
      if(typeof renderCardYtList==='function')renderCardYtList(cardSearchState.ytItems||[],'');
      cardSearchState.view='yt';
      return;
    }
  }
  if(kind==='yt'||snap.ytId){
    setCardYtFrame(snap.ytId,snap.host||'youtube',{noHist:1});
    if(typeof renderCardYtList==='function')renderCardYtList(cardSearchState.ytItems||[],snap.ytId);
    return;
  }
  if(kind==='article'||snap.view==='article'){
    var _p=cardSearchHistPush;cardSearchHistPush=function(){};
    try{if(typeof window.cardSearchOpenWebRow==='function')window.cardSearchOpenWebRow(snap.i);}finally{cardSearchHistPush=_p;}
    return;
  }
  if(kind==='results'||snap.view==='results'){
    if(typeof cardSearchShowWebResults==='function')cardSearchShowWebResults();
    return;
  }
  if(kind==='image'||snap.view==='image'){
    var _q=cardSearchHistPush;cardSearchHistPush=function(){};
    try{if(typeof window.cardSearchOpenImage==='function')window.cardSearchOpenImage(snap.i);}finally{cardSearchHistPush=_q;}
    return;
  }
  if(kind==='grid'||snap.view==='grid'){
    if(window.cardSearchExitImage)window.cardSearchExitImage();
  }
}
"""

BACK_OLD = """window.cardSearchBack=function(){
  var imgView=document.getElementById('cardSearchImgView');
  if(imgView&&imgView.classList.contains('open')){
    window.cardSearchExitImage();
    return;
  }
  if(cardSearchState.type!=='yt'&&cardSearchState.view==='article'){
    cardSearchShowWebResults();
    return;
  }
  var frame=document.getElementById('cardSearchFrame');
"""
BACK_NEW = """window.cardSearchBack=function(){
  var frame=document.getElementById('cardSearchFrame');
"""

BACK_NAV_OLD = """  // Try iframe history for any type with a visible frame (not just yt)
  if(frame&&!frame.classList.contains('is-hidden')){
    try{
      if(frame.contentWindow&&frame.contentWindow.history&&frame.contentWindow.history.length>1){
        frame.contentWindow.history.back();
        return;
      }
    }catch(err){}
  }
  // Try internal history stack
  if(cardSearchState.history.length>1){
    cardSearchState.history.pop();
    var url=cardSearchState.history[cardSearchState.history.length-1];
    cardSearchState.embedUrl=url;
    if(frame)frame.src=url;
    cardSearchEnableBack();
    return;
  }
  closeCardSearchEmbed();
};
"""
BACK_NAV_NEW = """  if(!cardSearchState.history)cardSearchState.history=[];
  if(cardSearchState.history.length>1){
    cardSearchState.history.pop();
    var prev=cardSearchState.history[cardSearchState.history.length-1];
    if(typeof cardSearchApplyHist==='function')cardSearchApplyHist(prev);
    else if(typeof prev==='string'&&frame){cardSearchState.embedUrl=prev;frame.src=prev;}
    cardSearchEnableBack();
    return;
  }
  if(cardSearchState.type==='yt'){
    if(typeof showCardSearchFrame==='function')showCardSearchFrame(false);
    if(typeof renderCardYtList==='function')renderCardYtList(cardSearchState.ytItems||[],'');
    cardSearchEnableBack();
    return;
  }
  if(cardSearchState.type==='img'){
    if(window.cardSearchExitImage)window.cardSearchExitImage();
    cardSearchEnableBack();
    return;
  }
  if(typeof cardSearchShowWebResults==='function')cardSearchShowWebResults();
  cardSearchEnableBack();
};
"""

COVER_BOOT_OLD = """  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot);
  else boot();
  document.addEventListener('keydown',function(e){
    if(e.key!=='Tab'||e.shiftKey||e.altKey||e.ctrlKey||e.metaKey)return;
    if(!cardMinShouldTakeTab(e.target))return;
"""
COVER_BOOT_NEW = """  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot);
  else boot();
  function pinCovers(){if(typeof reviveEntryCovers==='function')reviveEntryCovers();}
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',pinCovers);
  else pinCovers();
  document.addEventListener('keydown',function(e){
    if(e.key!=='Tab'||e.shiftKey||e.altKey||e.ctrlKey||e.metaKey)return;
    if(!cardMinShouldTakeTab(e.target))return;
"""

THEME_HIST_OLD = "    cardSearchState.history=[next];\n"
THEME_HIST_NEW = "    if(typeof cardSearchHistPush==='function')cardSearchHistPush({kind:'yt',type:'yt',view:'yt',ytId:cardSearchState.ytId,embedUrl:next,host:cardSearchState._ytHost});\n    else cardSearchState.history=[next];\n"


def patch_file(path: Path):
    text = path.read_text(encoding="utf-8")
    orig_len = len(text)
    name = path.name
    print(f"== {name} ==")
    pairs = [
        (CSS_BOTTOM_OLD, CSS_BOTTOM_NEW, "css-bottom"),
        (CSS_HEAD_OLD, CSS_HEAD_NEW, "css-index-head-z"),
        (CSS_STRIPE_OLD, CSS_STRIPE_NEW, "css-stripe-z"),
        (ENSURE_OLD, ENSURE_NEW, "ensureCatalogMain"),
        (FIT_OLD, FIT_NEW, "applyIndexScrollFit"),
        (BIND_OLD, BIND_NEW, "hover-bind-retry"),
        (BOOT_OLD, BOOT_NEW, "hover-boot"),
        (HIST_ANCHOR, HIST_BLOCK, "history-store"),
        (
            "function catalogAcHistoryHtml(q){\n  var html='',q=String(q||'').toLowerCase();\n  var sessions=(pinSessionStore.sessions||[]).slice().sort(function(a,b){return (b.usedAt||b.savedAt||0)-(a.usedAt||a.savedAt||0);}).filter(function(s){return s&&catalogHistMatch(s.name,q);});\n",
            "function catalogAcHistoryHtml(q){\n  var html='',q=String(q||'').toLowerCase();\n  function jsStr(s){return String(s||'').replace(/\\\\/g,'\\\\\\\\').replace(/'/g,\"\\\\'\");}\n  function htmlStr(s){return String(s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/\"/g,'&quot;');}\n  var sessions=(pinSessionStore.sessions||[]).slice().sort(function(a,b){return (b.usedAt||b.savedAt||0)-(a.usedAt||a.savedAt||0);}).filter(function(s){return s&&catalogHistMatch(s.name,q);});\n",
            "ac-hist-esc",
            True,
        ),
        (COMMIT_OLD, COMMIT_NEW, "commitSearchTokens"),
        (SHOW_HIST_OLD, SHOW_HIST_NEW, "showAc-hist-var"),
        (SHOW_HTML_OLD, SHOW_HTML_NEW, "showAc-html"),
        (PICK_OLD, PICK_NEW, "pickAc"),
        (ADDKW_OLD, ADDKW_NEW, "addSearchKw"),
        (CLEAR_OLD, CLEAR_NEW, "clear-history"),
        (COVER_SRC_OLD, COVER_SRC_NEW, "cover-src"),
        (INDEX_OLD, INDEX_NEW, "tin-index"),
        (DISMISS_OLD, DISMISS_NEW, "tin-dismiss"),
        (PARK_OLD, PARK_NEW, "tin-park"),
        (CLOSE_OLD, CLOSE_NEW, "tin-close"),
        (RENDER_PILL_OLD, RENDER_PILL_NEW, "tin-pill-attr"),
        (PLAYING_OLD, PLAYING_NEW, "tin-playing"),
        (ARIA_OLD, ARIA_NEW, "tin-aria"),
        (RENDER_MEDIA_OLD, RENDER_MEDIA_NEW, "tin-render-media"),
        (SAVE_DOCK_OLD, SAVE_DOCK_NEW, "tin-save-dock"),
        (MIN_BODY_OLD, MIN_BODY_NEW, "tin-minimize"),
        (PARK_KEEP_OLD, PARK_KEEP_NEW, "tin-park-keep"),
        (RESTORE_OLD, RESTORE_NEW, "tin-restore"),
        (CLICK_OLD, CLICK_NEW, "tin-click"),
        (OCP_OLD, OCP_NEW, "record-preview"),
        (SEARCH_MODAL_OLD, SEARCH_MODAL_NEW, "record-modal"),
        (ENABLE_OLD, ENABLE_NEW, "embed-hist-helpers"),
        (YT_HIST_OLD, YT_HIST_NEW, "yt-hist-push"),
        (WEB_HIST_OLD, WEB_HIST_NEW, "web-hist-push"),
        (GOOGLE_HIST_OLD, GOOGLE_HIST_NEW, "google-hist-push"),
        (IMG_GRID_OLD, IMG_GRID_NEW, "img-grid-hist"),
        (IMG_OPEN_OLD, IMG_OPEN_NEW, "img-open-hist"),
        (EXIT_IMG_OLD, EXIT_IMG_NEW, "img-exit-hist"),
        (BACK_OLD, BACK_NEW, "embed-back-start"),
        (BACK_NAV_OLD, BACK_NAV_NEW, "embed-back-nav"),
        (COVER_BOOT_OLD, COVER_BOOT_NEW, "cover-boot"),
        (THEME_HIST_OLD, THEME_HIST_NEW, "theme-hist"),
    ]
    text = sub_all_once(text, pairs)
    if "function hideSearchAc" not in text and "window.hideSearchAc" not in text:
        # not all files may use that name; don't fail
        pass
    if name.endswith(".html") and "</html>" not in text:
        raise SystemExit(f"{name} truncated: missing </html>")
    if "function ensureCatalogMain" not in text:
        raise SystemExit(f"{name} truncated: ensureCatalogMain")
    path.write_text(text, encoding="utf-8")
    print(f"  wrote {name} ({orig_len} -> {len(text)})")


def main():
    for f in FILES:
        if not f.exists():
            raise SystemExit(f"missing {f}")
        patch_file(f)
    print("done")


if __name__ == "__main__":
    main()
