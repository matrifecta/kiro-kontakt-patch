#!/usr/bin/env python3
"""Add Saved sessions (unchecked) and All-search to History picker in all 6 catalogs."""
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


def must_one(text, old, new, label):
    n = text.count(old)
    if n == 1:
        return text.replace(old, new, 1)
    if n > 1:
        raise SystemExit(f"{label}: {n} matches")
    if new in text:
        print(f"  skip {label} (already)")
        return text
    raise SystemExit(f"{label}: not found")


HTML_OLD = (
    '<button type="button" class="ac-history-all" id="historyAll" title="Select all">All</button>'
)
HTML_NEW = (
    '<button type="button" class="ac-history-search" id="historySearchAll" title="Select all search history (not saved sessions)">All search</button>'
    '<button type="button" class="ac-history-all" id="historyAll" title="Select all, including saved sessions">All</button>'
)

CSS_OLD = (
    " .ac-history-all{box-sizing:border-box;min-height:2.75rem;padding:0 .7rem;border:1px solid var(--border);border-radius:999px;background:var(--bg-surface);color:var(--text);font:inherit;font-size:.8125rem;cursor:pointer;touch-action:manipulation;margin-right:auto}\n"
    " .ac-history-all:hover{border-color:var(--accent-instrument);color:var(--accent-instrument);background:var(--accent-instrument-bg)}\n"
)
CSS_NEW = (
    " .ac-history-search,.ac-history-all{box-sizing:border-box;min-height:2.75rem;padding:0 .7rem;border:1px solid var(--border);border-radius:999px;background:var(--bg-surface);color:var(--text);font:inherit;font-size:.8125rem;cursor:pointer;touch-action:manipulation}\n"
    " .ac-history-all{margin-right:auto}\n"
    " .ac-history-search:hover,.ac-history-all:hover{border-color:var(--accent-instrument);color:var(--accent-instrument);background:var(--accent-instrument-bg)}\n"
)

RENDER_OLD = """function renderHistoryPicks(){
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
"""

RENDER_NEW = """function renderHistoryPicks(){
  var el=document.getElementById('historyPicks');
  if(!el)return;
  var sessN=(pinSessionStore&&pinSessionStore.sessions||[]).length;
  var recN=(pinSessionStore&&pinSessionStore.recent||[]).length;
  var sessLab='Saved sessions'+(recN?' \\u00b7 '+recN+' recent':'');
  var rows=[
    {id:'commits',label:'Searched keywords',n:Object.keys(searchCommitCounts||{}).length,on:1},
    {id:'recent',label:'Recent keywords',n:(recentKwStore||[]).length,on:1},
    {id:'combos',label:'Keyword combos',n:(kwComboStore||[]).length,on:1},
    {id:'cards',label:'Card hits',n:Object.keys(cardHitStore||{}).length,on:1},
    {id:'sessions',label:sessLab,n:sessN,on:0}
  ];
  el.innerHTML=rows.map(function(r){return '<label><input type="checkbox" data-hist="'+r.id+'"'+(r.on?' checked':'')+'> <span>'+r.label+'</span> <span class="ac-hist-count">'+r.n+'</span></label>';}).join('');
}
"""

# In the JS string above I used '\\u00b7' which in the file would be the two-char escape
# I want actual · in the JS source as '\\u00b7' so the HTML gets · 
# In Python RENDER_NEW, `\\u00b7` in a regular string is `\u00b7` (one backslash + u00b7)? 
# In """ ... \\u00b7 ... """ that's backslash-backslash-u00b7? No:
# In Python triple-quoted: '\\u00b7' in '''...'''  wait I used """ with \\u00b7
# """ ... \\u00b7 ... """  => file contains \u00b7  (one backslash) which JS interprets as ·
# That's correct: JS source `'\u00b7'` in string concat: `'Saved sessions'+(recN?' \u00b7 '+recN+' recent':'')`
# In my RENDER_NEW I have: `'Saved sessions'+(recN?' \\u00b7 '+recN+' recent':'')`
# Python """ \\u00b7 """ => `\u00b7` in output. Good.

LOG_NOOP_OLD = "data:{buckets:[],noop:true,nCommits:Object.keys(searchCommitCounts||{}).length,nRecent:(recentKwStore||[]).length,nCombos:(kwComboStore||[]).length,nCards:Object.keys(cardHitStore||{}).length}"
LOG_NOOP_NEW = "data:{buckets:[],noop:true,sessions:false,nCommits:Object.keys(searchCommitCounts||{}).length,nRecent:(recentKwStore||[]).length,nCombos:(kwComboStore||[]).length,nCards:Object.keys(cardHitStore||{}).length,nSessions:(pinSessionStore&&pinSessionStore.sessions||[]).length}"

WIPE_OLD = """  if(buckets.cards){
    cardHitStore={};
    if(typeof persistCardHits==='function')persistCardHits();
  }
"""
WIPE_NEW = """  if(buckets.cards){
    cardHitStore={};
    if(typeof persistCardHits==='function')persistCardHits();
  }
  if(buckets.sessions){
    pinSessionStore={sessions:[],recent:[]};
    if(typeof persistPinSessions==='function')persistPinSessions();
  }
"""

LOG_WIPE_OLD = "data:{buckets:keys,nCommits:Object.keys(searchCommitCounts||{}).length,nRecent:(recentKwStore||[]).length,nCombos:(kwComboStore||[]).length,nCards:Object.keys(cardHitStore||{}).length}"
LOG_WIPE_NEW = "data:{buckets:keys,sessions:!!buckets.sessions,nCommits:Object.keys(searchCommitCounts||{}).length,nRecent:(recentKwStore||[]).length,nCombos:(kwComboStore||[]).length,nCards:Object.keys(cardHitStore||{}).length,nSessions:(pinSessionStore&&pinSessionStore.sessions||[]).length}"

BIND_OLD = """  var btn=historyBtnEl(),yes=document.getElementById('historyYes'),no=document.getElementById('historyNo'),all=document.getElementById('historyAll'),cloud=historyCloudEl();
  if(btn)btn.addEventListener('click',function(e){
    e.preventDefault();e.stopPropagation();
    if(cloud&&!cloud.hidden)hideHistoryCloud();else showHistoryCloud();
  });
  if(all)all.addEventListener('click',function(e){
    e.preventDefault();e.stopPropagation();
    var picks=document.getElementById('historyPicks');
    if(picks)picks.querySelectorAll('input[type="checkbox"][data-hist]').forEach(function(cb){cb.checked=true;});
  });
"""

BIND_NEW = """  var btn=historyBtnEl(),yes=document.getElementById('historyYes'),no=document.getElementById('historyNo'),all=document.getElementById('historyAll'),searchAll=document.getElementById('historySearchAll'),cloud=historyCloudEl();
  if(btn)btn.addEventListener('click',function(e){
    e.preventDefault();e.stopPropagation();
    if(cloud&&!cloud.hidden)hideHistoryCloud();else showHistoryCloud();
  });
  if(searchAll)searchAll.addEventListener('click',function(e){
    e.preventDefault();e.stopPropagation();
    var picks=document.getElementById('historyPicks');
    if(picks)picks.querySelectorAll('input[type="checkbox"][data-hist]').forEach(function(cb){cb.checked=cb.getAttribute('data-hist')!=='sessions';});
  });
  if(all)all.addEventListener('click',function(e){
    e.preventDefault();e.stopPropagation();
    var picks=document.getElementById('historyPicks');
    if(picks)picks.querySelectorAll('input[type="checkbox"][data-hist]').forEach(function(cb){cb.checked=true;});
  });
"""


def patch(text):
    text = must_one(text, HTML_OLD, HTML_NEW, "html-search-all")
    text = must_one(text, CSS_OLD, CSS_NEW, "css-search-all")
    text = must_one(text, RENDER_OLD, RENDER_NEW, "render-sessions")
    text = must_one(text, LOG_NOOP_OLD, LOG_NOOP_NEW, "log-noop")
    text = must_one(text, WIPE_OLD, WIPE_NEW, "wipe-sessions")
    text = must_one(text, LOG_WIPE_OLD, LOG_WIPE_NEW, "log-wipe")
    text = must_one(text, BIND_OLD, BIND_NEW, "bind-search-all")
    return text


def main():
    for path in FILES:
        text = path.read_text(encoding="utf-8")
        print(path.name)
        new = patch(text)
        path.write_text(new, encoding="utf-8")
        print("  wrote")
        for needle in (
            "historySearchAll",
            "{id:'sessions'",
            "nSessions",
            "buckets.sessions",
            "All search",
        ):
            if needle not in new:
                raise SystemExit(f"{path.name} missing {needle}")
        # Clear must still not wipe sessions
        i = new.find("clearAllFilters=function()")
        chunk = new[i : i + 2200]
        if "pinSessionStore=" in chunk:
            raise SystemExit(f"{path.name} Clear wipes pinSessionStore")
        if "catalogJumpStack" not in new:
            raise SystemExit(f"{path.name} lost catalogJumpStack")
    print("all ok")


if __name__ == "__main__":
    main()
