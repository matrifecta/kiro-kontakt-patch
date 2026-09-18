#!/usr/bin/env python3
"""
Make saved user-note text searchable via the keyword/pill system:
- Derive simple keyword tokens from note text (stopword-filtered).
- Merge them into each entry's data-kw attribute (on top of its
  original/base keywords, recomputed fresh each time so removing/
  editing a note doesn't leave stale tokens behind).
- Recompute kwCounts/allKws and re-render the keyword pill bar whenever
  a note is saved, so new keywords get their own pill (or bump the
  count of an existing matching keyword) immediately, and participate
  normally in search + saved keyword combinations (which just store
  plain keyword strings).
"""
import re

FILES = [
    "public/catalogs/DS-CATALOG.html",
    "public/catalogs/DS-CATALOG-portable.html",
    "public/catalogs/KONTAKT-CATALOG.html",
    "public/catalogs/KONTAKT-CATALOG-portable.html",
]

# 1) Add refreshKwCaches(), exposed on window, right after the initial
#    allKws computation inside the keyword-bar IIFE.
OLD_ALLKWS_TAIL = """   return list.sort(function(a,b){return b.c-a.c||(a.k<b.k?-1:a.k>b.k?1:0);});
 })();
 function renderKwBar(){"""

NEW_ALLKWS_TAIL = """   return list.sort(function(a,b){return b.c-a.c||(a.k<b.k?-1:a.k>b.k?1:0);});
 })();
 window.refreshKwCaches=function(){
   kwCounts={};entries.forEach(function(el){kws(el).forEach(function(k){kwCounts[k]=(kwCounts[k]||0)+1;});});
   allKws=(function(){
     var seen={}, list=[];
     Object.keys(kwCounts).forEach(function(k){seen[k]=1;list.push({k:k,c:kwCounts[k],untagged:0,isLibName:0,label:k,cat:kwCat(k)});});
     Object.keys(patchCounts).forEach(function(k){
       if(seen[k])return; seen[k]=1;
       list.push({k:k,c:patchCounts[k],untagged:0,isLibName:0,label:k,cat:'patch'});
     });
     return list.sort(function(a,b){return b.c-a.c||(a.k<b.k?-1:a.k>b.k?1:0);});
   })();
   if(typeof renderKwBar==='function')renderKwBar();
 };
 function renderKwBar(){"""

# 2) Add the note-keyword tokenizer + merge helper, and call it from
#    syncEntryMeta() (which already computes `note` for this entry).
OLD_SYNC = """function syncEntryMeta(el){
  if(!el)return;
  var name=entryName(el);
  var fav=!!favSet[name];
  var note=String(notesMap[name]||'').replace(/^\\s+|\\s+$/g,'');
  el.classList.toggle('is-fav',fav);"""

NEW_SYNC = """var NOTE_KW_STOP={the:1,a:1,an:1,and:1,or:1,of:1,to:1,in:1,on:1,at:1,by:1,for:1,from:1,with:1,into:1,onto:1,upon:1,is:1,it:1,its:1,this:1,that:1,these:1,those:1,be:1,was:1,were:1,are:1,not:1,no:1,nor:1,but:1,so:1,if:1,then:1,than:1,your:1,my:1,our:1,their:1,you:1,we:1,they:1,he:1,she:1,them:1,us:1,me:1,as:1,has:1,have:1,had:1,will:1,would:1,can:1,could:1,just:1,very:1,really:1,also:1,more:1,most:1,some:1,any:1,all:1,one:1,two:1,been:1,being:1,do:1,does:1,did:1,get:1,got:1,like:1,love:1,made:1,make:1,about:1,there:1,here:1,when:1,where:1,what:1,which:1,who:1,how:1,why:1,out:1,up:1,down:1,over:1,under:1,again:1,still:1,too:1,only:1,own:1,same:1,other:1,such:1,than:1};
function noteKeywordsFor(text){
  var seen={}, out=[];
  String(text||'').toLowerCase().split(/[^a-z0-9'-]+/).forEach(function(w){
    w=w.replace(/^['-]+|['-]+$/g,'');
    if(!w||w.length<3||w.length>24||NOTE_KW_STOP[w]||seen[w])return;
    if(/^[0-9'-]+$/.test(w))return;
    seen[w]=1;out.push(w);
  });
  return out.slice(0,15);
}
function syncNoteKw(el,note){
  if(!el)return false;
  if(el.dataset.baseKw===undefined)el.dataset.baseKw=el.getAttribute('data-kw')||'';
  var base=el.dataset.baseKw.split(/\\s+/).filter(Boolean);
  var noteKw=note?noteKeywordsFor(note):[];
  var merged=base.slice();
  var added=false;
  noteKw.forEach(function(k){if(merged.indexOf(k)<0){merged.push(k);added=true;}});
  var next=merged.join(' ');
  var changed=(next!==(el.getAttribute('data-kw')||''));
  if(changed)el.setAttribute('data-kw',next);
  return changed;
}
function syncEntryMeta(el){
  if(!el)return;
  var name=entryName(el);
  var fav=!!favSet[name];
  var note=String(notesMap[name]||'').replace(/^\\s+|\\s+$/g,'');
  syncNoteKw(el,note);
  el.classList.toggle('is-fav',fav);"""

# 3) Refresh the pill caches whenever a note is actually saved.
OLD_SAVE_TAIL = """  if(val)notesMap[name]=val;else delete notesMap[name];
  persistNotes();
  syncEntryMeta(el);
  window.cancelNotePop(btn);"""

NEW_SAVE_TAIL = """  if(val)notesMap[name]=val;else delete notesMap[name];
  persistNotes();
  syncEntryMeta(el);
  if(typeof window.refreshKwCaches==='function')window.refreshKwCaches();
  window.cancelNotePop(btn);"""


def main():
    for path in FILES:
        txt = open(path, encoding="utf-8").read()
        for label, old, new in (
            ("allKws tail / refreshKwCaches", OLD_ALLKWS_TAIL, NEW_ALLKWS_TAIL),
            ("syncEntryMeta / note keywords", OLD_SYNC, NEW_SYNC),
            ("saveNotePop tail", OLD_SAVE_TAIL, NEW_SAVE_TAIL),
        ):
            if old not in txt:
                print(f"  WARN: anchor '{label}' not found in {path}")
                continue
            txt = txt.replace(old, new, 1)
        open(path, "w", encoding="utf-8").write(txt)
        print(f"{path}: patched")


if __name__ == "__main__":
    main()
