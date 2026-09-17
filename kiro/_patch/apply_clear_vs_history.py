#!/usr/bin/env python3
"""Split Clear (recents) vs History (selectable buckets) in all 6 catalog files."""
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

INGEST = "http://127.0.0.1:7529/ingest/1cf46354-1d61-4c80-bd72-a340f1db1b51"


def log_fetch(hid, loc, msg, data_js, run_id="post-fix"):
    return (
        "// #region agent log\n"
        f"fetch('{INGEST}',{{method:'POST',headers:{{'Content-Type':'application/json','X-Debug-Session-Id':'f491c2'}},body:JSON.stringify({{sessionId:'f491c2',runId:'{run_id}',hypothesisId:'{hid}',location:'{loc}',message:'{msg}',data:{data_js},timestamp:Date.now()}})}}).catch(function(){{}});\n"
        "// #endregion\n"
    )


def must_one(text, old, new, label):
    n = text.count(old)
    if n == 1:
        return text.replace(old, new, 1)
    if n > 1:
        raise SystemExit(f"{label}: {n} matches")
    if new in text or (isinstance(new, str) and "ac-history-picks" in new and "ac-history-picks" in text and label == "html-cloud"):
        print(f"  skip {label} (already)")
        return text
    raise SystemExit(f"{label}: not found")


def first_of(text, pairs, label):
    found = [(old, new) for old, new in pairs if text.count(old) == 1]
    if len(found) == 1:
        old, new = found[0]
        return text.replace(old, new, 1)
    if not found:
        for old, new in pairs:
            if new in text or text.count(old) == 0 and "already-ok" in label:
                print(f"  skip {label} (already)")
                return text
        raise SystemExit(f"{label}: none of {len(pairs)} variants found")
    raise SystemExit(f"{label}: {len(found)} variants matched")


HTML_OLD = (
    '<p class="ac-history-ask">Clear search history?</p>'
    '<div class="ac-history-actions">'
    '<button type="button" class="ac-history-yes" id="historyYes" aria-label="Yes, clear history" title="Clear">&#x2713;</button>'
    '<button type="button" class="ac-history-no" id="historyNo" aria-label="No, keep history" title="Keep">&#x2715;</button>'
    "</div>"
)
HTML_NEW = (
    '<p class="ac-history-ask">Erase history</p>'
    '<div class="ac-history-picks" id="historyPicks"></div>'
    '<div class="ac-history-actions">'
    '<button type="button" class="ac-history-all" id="historyAll" title="Select all">All</button>'
    '<button type="button" class="ac-history-yes" id="historyYes" aria-label="Erase selected" title="Erase">&#x2713;</button>'
    '<button type="button" class="ac-history-no" id="historyNo" aria-label="Cancel" title="Keep">&#x2715;</button>'
    "</div>"
)

CSS_MAX_OLD = "max-width:min(16rem,calc(100vw - 1.5rem - env(safe-area-inset-left,0px) - env(safe-area-inset-right,0px)));"
CSS_MAX_NEW = "max-width:min(20rem,calc(100vw - 1.5rem - env(safe-area-inset-left,0px) - env(safe-area-inset-right,0px)));"

CSS_ASK_OLD = " .ac-history-ask{margin:0;font-size:.875rem;line-height:1.35;color:var(--text);max-width:100%}\n"
CSS_ASK_NEW = (
    " .ac-history-ask{margin:0;font-size:.875rem;line-height:1.35;color:var(--text);max-width:100%}\n"
    " .ac-history-picks{display:flex;flex-direction:column;gap:.28rem;max-width:100%}\n"
    " .ac-history-picks label{display:flex;align-items:center;gap:.45rem;margin:0;font-size:.8125rem;line-height:1.3;color:var(--text);cursor:pointer;min-height:1.75rem}\n"
    " .ac-history-picks input{flex:0 0 auto;margin:0;accent-color:var(--accent-instrument)}\n"
    " .ac-history-picks .ac-hist-count{margin-left:auto;color:var(--text-muted);font-variant-numeric:tabular-nums}\n"
    " .ac-history-all{box-sizing:border-box;min-height:2.75rem;padding:0 .7rem;border:1px solid var(--border);border-radius:999px;background:var(--bg-surface);color:var(--text);font:inherit;font-size:.8125rem;cursor:pointer;touch-action:manipulation;margin-right:auto}\n"
    " .ac-history-all:hover{border-color:var(--accent-instrument);color:var(--accent-instrument);background:var(--accent-instrument-bg)}\n"
)

HYDRATE_OLD = "if(!Array.isArray(recentKwStore))recentKwStore=[];\nfunction persistPinSessions()"
HYDRATE_NEW = (
    "if(!Array.isArray(recentKwStore))recentKwStore=[];\n"
    + log_fetch(
        "H1",
        "hydrate:searchCommitCounts",
        "hist-hydrate",
        "{key:typeof SEARCH_COMMIT_KEY!=='undefined'?SEARCH_COMMIT_KEY:'',commits:Object.keys(searchCommitCounts||{}),recent:recentKwStore}",
        "pre-fix",
    )
    + "function persistPinSessions()"
)

SHOW_OLD = """function showHistoryCloud(){
  var cloud=historyCloudEl(),btn=historyBtnEl();
  if(!cloud||!btn)return;
  cloud.hidden=false;
  btn.setAttribute('aria-expanded','true');
  placeHistoryCloud();
}
window.clearSearchHistoryData=function(){
  searchKeywords=[];
  if(typeof searchInput!=='undefined'&&searchInput)searchInput.value='';
  searchCommitCounts={};
  if(typeof lsSet==='function'&&typeof SEARCH_COMMIT_KEY!=='undefined')lsSet(SEARCH_COMMIT_KEY,{});
  kwComboStore=[];recentKwStore=[];cardHitStore={};
  if(typeof persistKwCombos==='function')persistKwCombos();
  if(typeof persistRecentKws==='function')persistRecentKws();
  if(typeof persistCardHits==='function')persistCardHits();
  if(typeof renderPills==='function')renderPills();
  if(typeof applySearch==='function'&&currentMode==='search'){applySearch();if(typeof render==='function')render();}
  else if(typeof render==='function')render();
  hideHistoryCloud();
  try{
    if(typeof showAc==='function'){
      var q=(typeof searchInput!=='undefined'&&searchInput)?searchInput.value.trim().toLowerCase():'';
      var ac=document.getElementById('acList');
      if(ac&&(ac.classList.contains('open')||(searchInput&&document.activeElement===searchInput)))showAc(q,{force:true});
    }
  }catch(err){}
};
"""

SHOW_NEW = """function historyPickBuckets(){
  var picks=document.getElementById('historyPicks'),out={};
  if(!picks)return out;
  picks.querySelectorAll('input[type="checkbox"][data-hist]').forEach(function(cb){if(cb.checked)out[cb.getAttribute('data-hist')]=1;});
  return out;
}
function renderHistoryPicks(){
  var el=document.getElementById('historyPicks');
  if(!el)return;
  var rows=[
    {id:'commits',label:'Searched keywords',n:Object.keys(searchCommitCounts||{}).length},
    {id:'recent',label:'Recent keywords',n:(recentKwStore||[]).length},
    {id:'combos',label:'Keyword combos',n:(kwComboStore||[]).length},
    {id:'cards',label:'Card hits',n:Object.keys(cardHitStore||{}).length}
  ];
  el.innerHTML=rows.map(function(r){return '<label><input type="checkbox" data-hist="'+r.id+'" checked> <span>'+r.label+'</span> <span class="ac-hist-count">'+r.n+'</span></label>';}).join('');
}
function showHistoryCloud(){
  var cloud=historyCloudEl(),btn=historyBtnEl();
  if(!cloud||!btn)return;
  if(typeof renderHistoryPicks==='function')renderHistoryPicks();
  cloud.hidden=false;
  btn.setAttribute('aria-expanded','true');
  placeHistoryCloud();
}
window.clearSearchHistoryData=function(opts){
  opts=opts||{};
  var buckets=opts.buckets||(typeof historyPickBuckets==='function'?historyPickBuckets():{});
  var keys=Object.keys(buckets||{}).filter(function(k){return buckets[k];});
  if(!keys.length){
""" + log_fetch(
        "H5",
        "clearSearchHistoryData",
        "hist-erase",
        "{buckets:[],noop:true,nCommits:Object.keys(searchCommitCounts||{}).length,nRecent:(recentKwStore||[]).length,nCombos:(kwComboStore||[]).length,nCards:Object.keys(cardHitStore||{}).length}",
    ) + """    hideHistoryCloud();
    return;
  }
  if(buckets.commits){
    searchCommitCounts={};
    if(typeof persistSearchCommits==='function')persistSearchCommits();
    else if(typeof lsSet==='function'&&typeof SEARCH_COMMIT_KEY!=='undefined')lsSet(SEARCH_COMMIT_KEY,{});
  }
  if(buckets.recent){
    recentKwStore=[];
    if(typeof persistRecentKws==='function')persistRecentKws();
  }
  if(buckets.combos){
    kwComboStore=[];
    if(typeof persistKwCombos==='function')persistKwCombos();
  }
  if(buckets.cards){
    cardHitStore={};
    if(typeof persistCardHits==='function')persistCardHits();
  }
""" + log_fetch(
        "H5",
        "clearSearchHistoryData",
        "hist-erase",
        "{buckets:keys,nCommits:Object.keys(searchCommitCounts||{}).length,nRecent:(recentKwStore||[]).length,nCombos:(kwComboStore||[]).length,nCards:Object.keys(cardHitStore||{}).length}",
    ) + """  hideHistoryCloud();
  try{
    if(typeof showAc==='function'){
      var q=(typeof searchInput!=='undefined'&&searchInput)?searchInput.value.trim().toLowerCase():'';
      var ac=document.getElementById('acList');
      if(ac&&(ac.classList.contains('open')||(searchInput&&document.activeElement===searchInput)))showAc(q,{force:true});
    }
  }catch(err){}
};
"""

BIND_OLD = """(function bindHistoryCloud(){
  var btn=historyBtnEl(),yes=document.getElementById('historyYes'),no=document.getElementById('historyNo'),cloud=historyCloudEl();
  if(btn)btn.addEventListener('click',function(e){
    e.preventDefault();e.stopPropagation();
    if(cloud&&!cloud.hidden)hideHistoryCloud();else showHistoryCloud();
  });
  if(yes)yes.addEventListener('click',function(e){e.preventDefault();e.stopPropagation();window.clearSearchHistoryData();});
  if(no)no.addEventListener('click',function(e){e.preventDefault();e.stopPropagation();hideHistoryCloud();});
"""

BIND_NEW = """(function bindHistoryCloud(){
  var btn=historyBtnEl(),yes=document.getElementById('historyYes'),no=document.getElementById('historyNo'),all=document.getElementById('historyAll'),cloud=historyCloudEl();
  if(btn)btn.addEventListener('click',function(e){
    e.preventDefault();e.stopPropagation();
    if(cloud&&!cloud.hidden)hideHistoryCloud();else showHistoryCloud();
  });
  if(all)all.addEventListener('click',function(e){
    e.preventDefault();e.stopPropagation();
    var picks=document.getElementById('historyPicks');
    if(picks)picks.querySelectorAll('input[type="checkbox"][data-hist]').forEach(function(cb){cb.checked=true;});
  });
  if(yes)yes.addEventListener('click',function(e){e.preventDefault();e.stopPropagation();window.clearSearchHistoryData();});
  if(no)no.addEventListener('click',function(e){e.preventDefault();e.stopPropagation();hideHistoryCloud();});
"""

CLEAR_WIPE = (
    "recentKwStore=[];\n"
    "if(typeof persistRecentKws==='function')persistRecentKws();\n"
    "searchCommitCounts={};\n"
    "if(typeof persistSearchCommits==='function')persistSearchCommits();\n"
    "else if(typeof lsSet==='function'&&typeof SEARCH_COMMIT_KEY!=='undefined')lsSet(SEARCH_COMMIT_KEY,{});\n"
    + log_fetch(
        "H2",
        "clearAllFilters",
        "clear-recents",
        "{nCommits:Object.keys(searchCommitCounts||{}).length,nRecent:(recentKwStore||[]).length,nCombos:(kwComboStore||[]).length,nCards:Object.keys(cardHitStore||{}).length}",
    )
)

CLEAR_AC = """try{
  var acOpen=document.getElementById('acList');
  if(acOpen&&acOpen.classList.contains('open')&&typeof showAc==='function'){
    var cq=(typeof searchInput!=='undefined'&&searchInput)?searchInput.value.trim().toLowerCase():'';
    showAc(cq,{force:true});
  }
}catch(err){}
"""

CLEAR_COMPACT_OLD = """window.clearAllFilters=function(){
if(typeof hideHistoryCloud==='function')hideHistoryCloud();
sel=[];
searchKeywords=[];
activeCat='all';
document.querySelectorAll('.cat-btn').forEach(function(b){b.classList.toggle('active',b.dataset.cat==='all');});
document.querySelectorAll('.kw.on,.kw.active').forEach(function(b){if(!b.classList.contains('clear'))b.classList.remove('on','active');});
if(searchInput)searchInput.value='';
if(acList){acList.classList.remove('open');acList.innerHTML='';}
renderPills();
document.body.classList.remove('search-extras-collapsed','search-chrome-collapsed');if(window.syncSearchHideBtn)window.syncSearchHideBtn();
clearHighlight();
var grid=document.querySelector('.catalog-body');
if(grid)grid.style.display='';
if(currentMode==='search'){applySearch();render();}
else render();
};
"""

CLEAR_COMPACT_NEW = """window.clearAllFilters=function(){
if(typeof hideHistoryCloud==='function')hideHistoryCloud();
""" + CLEAR_WIPE + """sel=[];
searchKeywords=[];
activeCat='all';
document.querySelectorAll('.cat-btn').forEach(function(b){b.classList.toggle('active',b.dataset.cat==='all');});
document.querySelectorAll('.kw.on,.kw.active').forEach(function(b){if(!b.classList.contains('clear'))b.classList.remove('on','active');});
if(searchInput)searchInput.value='';
if(acList){acList.classList.remove('open');acList.innerHTML='';}
renderPills();
document.body.classList.remove('search-extras-collapsed','search-chrome-collapsed');if(window.syncSearchHideBtn)window.syncSearchHideBtn();
clearHighlight();
var grid=document.querySelector('.catalog-body');
if(grid)grid.style.display='';
if(currentMode==='search'){applySearch();render();}
else render();
""" + CLEAR_AC + """};
"""

CLEAR_INDENT_OLD = """ window.clearAllFilters=function(){
   if(typeof hideHistoryCloud==='function')hideHistoryCloud();
   sel=[];
   searchKeywords=[];
   activeCat='all';
   document.querySelectorAll('.cat-btn').forEach(function(b){b.classList.toggle('active',b.dataset.cat==='all');});
   document.querySelectorAll('.kw.on,.kw.active').forEach(function(b){if(!b.classList.contains('clear'))b.classList.remove('on','active');});
   if(searchInput)searchInput.value='';
   if(acList){acList.classList.remove('open');acList.innerHTML='';}
   renderPills();
   document.body.classList.remove('search-extras-collapsed','search-chrome-collapsed');if(window.syncSearchHideBtn)window.syncSearchHideBtn();
   clearHighlight();
   var grid=document.querySelector('.catalog-body');
   if(grid)grid.style.display='';
   if(currentMode==='search'){applySearch();render();}
   else render();
 };
"""

CLEAR_WIPE_INDENT = "\n".join(
    ("   " + line if line.strip() else line) for line in CLEAR_WIPE.split("\n")
)
CLEAR_AC_INDENT = "\n".join(
    ("   " + line if line.strip() else line) for line in CLEAR_AC.split("\n")
)

CLEAR_INDENT_NEW = """ window.clearAllFilters=function(){
   if(typeof hideHistoryCloud==='function')hideHistoryCloud();
""" + CLEAR_WIPE_INDENT + """   sel=[];
   searchKeywords=[];
   activeCat='all';
   document.querySelectorAll('.cat-btn').forEach(function(b){b.classList.toggle('active',b.dataset.cat==='all');});
   document.querySelectorAll('.kw.on,.kw.active').forEach(function(b){if(!b.classList.contains('clear'))b.classList.remove('on','active');});
   if(searchInput)searchInput.value='';
   if(acList){acList.classList.remove('open');acList.innerHTML='';}
   renderPills();
   document.body.classList.remove('search-extras-collapsed','search-chrome-collapsed');if(window.syncSearchHideBtn)window.syncSearchHideBtn();
   clearHighlight();
   var grid=document.querySelector('.catalog-body');
   if(grid)grid.style.display='';
   if(currentMode==='search'){applySearch();render();}
   else render();
""" + CLEAR_AC_INDENT + """ };
"""

ARIA_OLD = 'aria-label="Clear search history"'
ARIA_NEW = 'aria-label="Erase history"'


def patch(text, name):
    text = must_one(text, HTML_OLD, HTML_NEW, "html-cloud")
    text = must_one(text, ARIA_OLD, ARIA_NEW, "aria-label")
    text = must_one(text, CSS_MAX_OLD, CSS_MAX_NEW, "css-max")
    text = must_one(text, CSS_ASK_OLD, CSS_ASK_NEW, "css-picks")
    text = must_one(text, HYDRATE_OLD, HYDRATE_NEW, "hydrate-log")
    text = must_one(text, SHOW_OLD, SHOW_NEW, "history-js")
    text = must_one(text, BIND_OLD, BIND_NEW, "bind-all")
    nc, ni = text.count(CLEAR_COMPACT_OLD), text.count(CLEAR_INDENT_OLD)
    if nc == 1 and ni == 0:
        text = text.replace(CLEAR_COMPACT_OLD, CLEAR_COMPACT_NEW, 1)
        print("  ok clear-compact")
    elif ni == 1 and nc == 0:
        text = text.replace(CLEAR_INDENT_OLD, CLEAR_INDENT_NEW, 1)
        print("  ok clear-indent")
    elif "clear-recents" in text and "searchCommitCounts={}" in text:
        print("  skip clear (already)")
    else:
        raise SystemExit(f"clearAllFilters: compact={nc} indent={ni}")
    return text


def main():
    for path in FILES:
        text = path.read_text(encoding="utf-8")
        print(path.name)
        new = patch(text, path.name)
        if new == text:
            print("  unchanged")
            continue
        path.write_text(new, encoding="utf-8")
        print("  wrote")
        for needle in ("ac-history-picks", "clear-recents", "hist-hydrate", "hist-erase", "historyAll"):
            if needle not in new:
                raise SystemExit(f"{path.name} missing {needle}")
        # searchCommitCounts wipe inside clearAllFilters
        i = new.find("window.clearAllFilters=function()")
        if i < 0:
            i = new.find(" window.clearAllFilters=function()")
        chunk = new[i : i + 1800]
        if "searchCommitCounts={}" not in chunk:
            raise SystemExit(f"{path.name} clearAllFilters missing searchCommitCounts wipe")
        if "ac-history-picks" not in new:
            raise SystemExit(f"{path.name} missing ac-history-picks")
    print("all ok")


if __name__ == "__main__":
    main()
