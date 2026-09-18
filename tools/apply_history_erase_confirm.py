#!/usr/bin/env python3
"""
1. Add a "User text (notes)" bucket to the Erase History picks list,
   defaulting unchecked, and make the top-row label read
   "Erase history + User text" while it's checked.
2. Two-stage confirm on the checkmark button: first press arms it (both
   check + X turn red); a second press on the check actually erases,
   while pressing X while armed just disarms (no erase). Changing the
   checkbox picks while armed disarms it again (avoid stale confirms).
3. Wire the 'notes' bucket into clearSearchHistoryData() to actually
   clear notesMap + refresh cards.
"""
import re

FILES = [
    "public/catalogs/DS-CATALOG.html",
    "public/catalogs/DS-CATALOG-portable.html",
    "public/catalogs/KONTAKT-CATALOG.html",
    "public/catalogs/KONTAKT-CATALOG-portable.html",
]

OLD_RENDER = """function renderHistoryPicks(){
  var el=document.getElementById('historyPicks');
  if(!el)return;
  var sessN=(pinSessionStore&&pinSessionStore.sessions||[]).length;
  var recN=(pinSessionStore&&pinSessionStore.recent||[]).length;
  var sessLab='Saved sessions'+(recN?' \\u00b7 '+recN+' recent':'');
  var rows=[
    {id:'commits',label:'Searched keywords',n:Object.keys(searchCommitCounts||{}).length,on:1},
    {id:'recent',label:'Recent keywords',n:(recentKwStore||[]).length,on:1},
    {id:'combos',label:'Keyword combos',n:(typeof kwAutoCombos==='function'?kwAutoCombos():(kwComboStore||[])).length,on:1},
    {id:'cards',label:'Card hits',n:Object.keys(cardHitStore||{}).length,on:1},
    {id:'savedCombos',label:'Saved combinations',n:(typeof kwSavedCombos==='function'?kwSavedCombos():[]).length,on:0},
    {id:'sessions',label:sessLab,n:sessN,on:0}
  ];
  el.innerHTML=rows.map(function(r){return '<label><input type="checkbox" data-hist="'+r.id+'"'+(r.on?' checked':'')+'> <span>'+r.label+'</span> <span class="ac-hist-count">'+r.n+'</span></label>';}).join('');
}"""

NEW_RENDER = """function disarmHistoryConfirm(){
  var cloud=historyCloudEl(),yes=document.getElementById('historyYes');
  if(cloud)cloud.classList.remove('armed');
  if(yes)yes.title='Erase';
}
function updateHistoryAskLabel(){
  var ask=document.querySelector('.ac-history-ask'),picks=document.getElementById('historyPicks');
  if(!ask||!picks)return;
  var notesOn=!!picks.querySelector('input[data-hist="notes"]:checked');
  ask.textContent=notesOn?'Erase history + User text':'Erase history';
}
function renderHistoryPicks(){
  var el=document.getElementById('historyPicks');
  if(!el)return;
  var sessN=(pinSessionStore&&pinSessionStore.sessions||[]).length;
  var recN=(pinSessionStore&&pinSessionStore.recent||[]).length;
  var sessLab='Saved sessions'+(recN?' \\u00b7 '+recN+' recent':'');
  var rows=[
    {id:'commits',label:'Searched keywords',n:Object.keys(searchCommitCounts||{}).length,on:1},
    {id:'recent',label:'Recent keywords',n:(recentKwStore||[]).length,on:1},
    {id:'combos',label:'Keyword combos',n:(typeof kwAutoCombos==='function'?kwAutoCombos():(kwComboStore||[])).length,on:1},
    {id:'cards',label:'Card hits',n:Object.keys(cardHitStore||{}).length,on:1},
    {id:'savedCombos',label:'Saved combinations',n:(typeof kwSavedCombos==='function'?kwSavedCombos():[]).length,on:0},
    {id:'notes',label:'User text (notes)',n:Object.keys(notesMap||{}).length,on:0},
    {id:'sessions',label:sessLab,n:sessN,on:0}
  ];
  el.innerHTML=rows.map(function(r){return '<label><input type="checkbox" data-hist="'+r.id+'"'+(r.on?' checked':'')+'> <span>'+r.label+'</span> <span class="ac-hist-count">'+r.n+'</span></label>';}).join('');
  el.querySelectorAll('input[type="checkbox"][data-hist]').forEach(function(cb){
    cb.addEventListener('change',function(){disarmHistoryConfirm();updateHistoryAskLabel();});
  });
  updateHistoryAskLabel();
}"""

OLD_YESNO = """  if(yes)yes.addEventListener('click',function(e){e.preventDefault();e.stopPropagation();window.clearSearchHistoryData();});
  if(no)no.addEventListener('click',function(e){e.preventDefault();e.stopPropagation();hideHistoryCloud();});"""

NEW_YESNO = """  if(yes)yes.addEventListener('click',function(e){
    e.preventDefault();e.stopPropagation();
    var buckets=typeof historyPickBuckets==='function'?historyPickBuckets():{};
    var keys=Object.keys(buckets||{}).filter(function(k){return buckets[k];});
    if(!keys.length){hideHistoryCloud();return;}
    if(cloud&&cloud.classList.contains('armed')){
      window.clearSearchHistoryData();
      if(typeof disarmHistoryConfirm==='function')disarmHistoryConfirm();
    }else{
      if(cloud)cloud.classList.add('armed');
      yes.title='Press \\u2713 again to confirm erase';
      if(no)no.title='Cancel erase';
    }
  });
  if(no)no.addEventListener('click',function(e){
    e.preventDefault();e.stopPropagation();
    if(cloud&&cloud.classList.contains('armed')){
      if(typeof disarmHistoryConfirm==='function')disarmHistoryConfirm();
      if(no)no.title='Keep';
      return;
    }
    hideHistoryCloud();
  });"""

OLD_ALLBTNS = """  if(searchAll)searchAll.addEventListener('click',function(e){
    e.preventDefault();e.stopPropagation();
    var picks=document.getElementById('historyPicks');
    if(picks)picks.querySelectorAll('input[type="checkbox"][data-hist]').forEach(function(cb){var h=cb.getAttribute('data-hist');cb.checked=h!=='sessions'&&h!=='savedCombos';});
  });
  if(all)all.addEventListener('click',function(e){
    e.preventDefault();e.stopPropagation();
    var picks=document.getElementById('historyPicks');
    if(picks)picks.querySelectorAll('input[type="checkbox"][data-hist]').forEach(function(cb){cb.checked=true;});
  });"""

NEW_ALLBTNS = """  if(searchAll)searchAll.addEventListener('click',function(e){
    e.preventDefault();e.stopPropagation();
    var picks=document.getElementById('historyPicks');
    if(picks)picks.querySelectorAll('input[type="checkbox"][data-hist]').forEach(function(cb){var h=cb.getAttribute('data-hist');cb.checked=h!=='sessions'&&h!=='savedCombos'&&h!=='notes';});
    if(typeof disarmHistoryConfirm==='function')disarmHistoryConfirm();
    if(typeof updateHistoryAskLabel==='function')updateHistoryAskLabel();
  });
  if(all)all.addEventListener('click',function(e){
    e.preventDefault();e.stopPropagation();
    var picks=document.getElementById('historyPicks');
    if(picks)picks.querySelectorAll('input[type="checkbox"][data-hist]').forEach(function(cb){cb.checked=true;});
    if(typeof disarmHistoryConfirm==='function')disarmHistoryConfirm();
    if(typeof updateHistoryAskLabel==='function')updateHistoryAskLabel();
  });"""

OLD_HIDE = """function hideHistoryCloud(){
  var cloud=historyCloudEl(),btn=historyBtnEl();
  if(cloud){cloud.hidden=true;cloud.classList.remove('cloud-above','cloud-below');}
  if(btn)btn.setAttribute('aria-expanded','false');
}"""

NEW_HIDE = """function hideHistoryCloud(){
  var cloud=historyCloudEl(),btn=historyBtnEl();
  if(cloud){cloud.hidden=true;cloud.classList.remove('cloud-above','cloud-below','armed');}
  if(btn)btn.setAttribute('aria-expanded','false');
}"""

OLD_CLEAR_TAIL = """  if(buckets.sessions){
    pinSessionStore={sessions:[],recent:[]};
    if(typeof persistPinSessions==='function')persistPinSessions();
  }
  hideHistoryCloud();"""

NEW_CLEAR_TAIL = """  if(buckets.sessions){
    pinSessionStore={sessions:[],recent:[]};
    if(typeof persistPinSessions==='function')persistPinSessions();
  }
  if(buckets.notes){
    notesMap={};
    if(typeof persistNotes==='function')persistNotes();
    if(typeof syncAllMeta==='function')syncAllMeta();
  }
  hideHistoryCloud();"""

REPLACEMENTS = [
    ("renderHistoryPicks", OLD_RENDER, NEW_RENDER),
    ("yes/no handlers", OLD_YESNO, NEW_YESNO),
    ("all/search-all handlers", OLD_ALLBTNS, NEW_ALLBTNS),
    ("hideHistoryCloud", OLD_HIDE, NEW_HIDE),
    ("clearSearchHistoryData tail", OLD_CLEAR_TAIL, NEW_CLEAR_TAIL),
]

ARMED_CSS = (
    "\n.ac-history-cloud.armed .ac-history-yes,.ac-history-cloud.armed .ac-history-no"
    "{background:#c62828;color:#fff;border-color:#c62828}\n"
    ".ac-history-cloud.armed .ac-history-yes:hover,.ac-history-cloud.armed .ac-history-no:hover"
    "{background:#e03030;border-color:#e03030}\n"
)


def main():
    for path in FILES:
        txt = open(path, encoding="utf-8").read()
        for label, old, new in REPLACEMENTS:
            if old not in txt:
                print(f"  WARN: anchor '{label}' not found in {path}")
                continue
            txt = txt.replace(old, new, 1)
        if ".ac-history-cloud.armed" not in txt:
            txt = txt.replace("</style>", ARMED_CSS + "</style>", 1)
        open(path, "w", encoding="utf-8").write(txt)
        print(f"{path}: patched")


if __name__ == "__main__":
    main()
