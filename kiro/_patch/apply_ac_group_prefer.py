#!/usr/bin/env python3
"""Prefer Search group titles over earlier library/keyword hits when jumping."""
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

FUNCS = r"""
function acGroupQuery(q){
  q=String(q||'').toLowerCase().replace(/^\s+|\s+$/g,'');
  if(!q||q.length<2)return '';
  var names=[
    {cat:'instrument',keys:['instrument']},
    {cat:'brand',keys:['brand']},
    {cat:'model',keys:['model']},
    {cat:'vibe',keys:['vibe']},
    {cat:'patch',keys:['patch']},
    {cat:'lib',keys:['libraries','library','lib']},
    {cat:'fav',keys:['favorites','favourite','favorite','fav']},
    {cat:'session',keys:['saved sessions','sessions','session']},
    {cat:'combo',keys:['saved combinations','combinations','combination','combos','combo']}
  ];
  var best='',score=0;
  names.forEach(function(n){
    n.keys.forEach(function(k){
      var s=0;
      if(k===q)s=6;
      else if(k.indexOf(q)===0)s=5;
      else if(q.length>=3&&k.indexOf(q)>=0)s=3;
      if(s>score){score=s;best=n.cat;}
    });
  });
  return score>=5?best:'';
}
function fillAcGroupQuery(q,list){
  list=list?list.slice():[];
  var gq=typeof acGroupQuery==='function'?acGroupQuery(q):'';
  if(!gq||typeof CAT_ORDER==='undefined'||CAT_ORDER.indexOf(gq)<0)return list;
  var src=(typeof allKws!=='undefined'&&allKws)?allKws:[];
  src.forEach(function(o){
    if(!o||!o.k)return;
    var c=o.cat||(typeof kwCat==='function'?kwCat(o.k):'');
    if(c!==gq)return;
    if(list.some(function(x){return x&&x.k===o.k;}))return;
    list.push({k:o.k,c:o.c||0,label:o.label||o.k,cat:c,untagged:o.untagged,isLibName:o.isLibName});
  });
  return list;
}
function matchingAcGroupLabel(q){
  var gq=typeof acGroupQuery==='function'?acGroupQuery(q):'';
  if(gq&&typeof acGroupLabelEl==='function'){
    var by=acGroupLabelEl(gq);
    if(by)return by;
  }
  var ac=document.getElementById('acList');
  if(!ac||!q)return null;
  q=String(q).toLowerCase().replace(/^\s+|\s+$/g,'');
  var labels=ac.querySelectorAll('.ac-group-label');
  var best=null,score=0;
  for(var i=0;i<labels.length;i++){
    var el=labels[i];
    var cat=String(el.getAttribute('data-cat')||'').toLowerCase();
    var lab=String(el.textContent||'').replace(/^\s+|\s+$/g,'').toLowerCase();
    var head=lab.split(/\s+[·•|]/)[0];
    var s=0;
    if(cat===q||lab===q||head===q)s=6;
    else if(cat.indexOf(q)===0||lab.indexOf(q)===0||head.indexOf(q)===0)s=5;
    if(s>score){score=s;best=el;}
  }
  return score>=5?best:null;
}
"""

JUMP_OLD = """  q=String(q||'').toLowerCase();
  if(q){
    cat=categoryForLibraryQuery(q);
    if(cat)label=acGroupLabelEl(cat);
    if(!label)label=matchingAcLibGroup(q);
  }
  if(!label){
    cat=opts.jumpCat||(typeof activeCat!=='undefined'?activeCat:'');
    if(cat&&cat!=='all'&&cat!=='other')label=acGroupLabelEl(cat);
  }
"""

JUMP_NEW = """  var path='';
  var libCat='';
  q=String(q||'').toLowerCase();
  if(q){
    libCat=typeof categoryForLibraryQuery==='function'?categoryForLibraryQuery(q):'';
    label=typeof matchingAcGroupLabel==='function'?matchingAcGroupLabel(q):null;
    if(label)path='group';
    if(!label){
      cat=libCat;
      if(cat)label=acGroupLabelEl(cat);
      if(label)path='libCat';
    }
    if(!label){label=matchingAcLibGroup(q);if(label)path='libItem';}
  }
  if(!label){
    cat=opts.jumpCat||(typeof activeCat!=='undefined'?activeCat:'');
    if(cat&&cat!=='all'&&cat!=='other'){label=acGroupLabelEl(cat);if(label)path='jumpCat';}
  }
"""

LIST_OLD = "var list=q?src.filter(function(o){return o.k.indexOf(q)>=0||(o.label&&o.label.toLowerCase().indexOf(q)>=0);}):src;"
LIST_NEW = LIST_OLD + "\nif(typeof fillAcGroupQuery==='function')list=fillAcGroupQuery(q,list);"

LIB_OLD = "suggestLibNames(q,24)"
LIB_NEW = "suggestLibNames(q,24,typeof acGroupQuery==='function'&&acGroupQuery(q)==='lib')"

SUG_OLD = """function suggestLibNames(q,lim){
  var ql=String(q||'').toLowerCase();
  if(!ql)return [];
"""
SUG_NEW = """function suggestLibNames(q,lim,all){
  var ql=String(q||'').toLowerCase();
  if(!ql&&!all)return [];
"""

HIST_OLD = "var sessions=(pinSessionStore.sessions||[]).slice().sort(function(a,b){return (b.usedAt||b.savedAt||0)-(a.usedAt||a.savedAt||0);}).filter(function(s){return s&&catalogHistMatch(s.name,q);});"
HIST_NEW = "var gqHist=typeof acGroupQuery==='function'?acGroupQuery(q):'';\n  var sessions=(pinSessionStore.sessions||[]).slice().sort(function(a,b){return (b.usedAt||b.savedAt||0)-(a.usedAt||a.savedAt||0);}).filter(function(s){return s&&(gqHist==='session'||catalogHistMatch(s.name,q));});"


def patch(path: Path):
    t = path.read_text(encoding="utf-8")
    if "function acGroupQuery(q){" not in t:
        if t.count("function jumpAcList(q,opts){") != 1:
            raise SystemExit(f"{path.name}: jumpAcList count")
        t = t.replace("function jumpAcList(q,opts){", FUNCS + "function jumpAcList(q,opts){", 1)
    if JUMP_OLD not in t:
        raise SystemExit(f"{path.name}: jump body missing")
    t = t.replace(JUMP_OLD, JUMP_NEW, 1)
    if LIST_OLD not in t:
        raise SystemExit(f"{path.name}: list filter missing")
    if "fillAcGroupQuery(q,list)" not in t:
        t = t.replace(LIST_OLD, LIST_NEW, 1)
    if SUG_OLD not in t:
        raise SystemExit(f"{path.name}: suggestLibNames missing")
    t = t.replace(SUG_OLD, SUG_NEW, 1)
    nlib = t.count(LIB_OLD)
    if nlib < 1:
        raise SystemExit(f"{path.name}: suggestLibNames(q,24) missing")
    t = t.replace(LIB_OLD, LIB_NEW)
    if HIST_OLD in t and "gqHist==='session'" not in t:
        t = t.replace(HIST_OLD, HIST_NEW, 1)
    t = t.replace(
        "var payload={q:q,cat:label.getAttribute('data-cat')||cat||'',lab:",
        "var payload={q:q,path:path||'',libCat:libCat||'',cat:label.getAttribute('data-cat')||cat||'',lab:",
        1,
    )
    path.write_text(t, encoding="utf-8")
    print("patched", path.name)


def main():
    for p in FILES:
        patch(p)


if __name__ == "__main__":
    main()
