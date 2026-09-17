#!/usr/bin/env python3
"""Only the viewed card keeps patches open; collapsed cards in a row share height."""
from pathlib import Path

ROOT = Path("/home/phnx/kiro-kontakt-patch")
FILES = [
    ROOT / "public/catalogs/KONTAKT-CATALOG.html",
    ROOT / "public/catalogs/DS-CATALOG.html",
    ROOT / "public/catalogs/KONTAKT-CATALOG-portable.html",
    ROOT / "public/catalogs/DS-CATALOG-portable.html",
]

FUNCS = r"""
function activePatchEntry(){
  return document.querySelector('.entry.highlight')||document.querySelector('.entry.selected');
}
function collapseInactivePatchTrees(src){
  if(window._collapsingPatches)return;
  window._collapsingPatches=true;
  var active=activePatchEntry();
  var nClosed=0,nKeep=0;
  try{
    document.querySelectorAll('.entry details.patches, .entry details.grp').forEach(function(d){
      var e=d.closest('.entry');
      if(!e)return;
      if(active&&e===active){if(d.open)nKeep++;return;}
      if(d.open){d.open=false;nClosed++;}
    });
  }finally{
    window._collapsingPatches=false;
  }
  if(typeof scheduleEqualizeCardRows==='function')scheduleEqualizeCardRows();
  // #region agent log
  try{
    fetch('http://127.0.0.1:7529/ingest/1cf46354-1d61-4c80-bd72-a340f1db1b51',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'c00e3e'},body:JSON.stringify({sessionId:'c00e3e',runId:'post-fix',hypothesisId:'A',location:'catalog:collapseInactivePatchTrees',message:'collapse inactive patch trees',data:{src:String(src||''),nClosed:nClosed,nKeep:nKeep,hasActive:!!active,activeId:active&&active.id,hl:!!(active&&active.classList.contains('highlight'))},timestamp:Date.now()})}).catch(function(){});
  }catch(eDbgA){}
  // #endregion
}
function equalizeCatalogCardRows(){
  var groups=document.querySelectorAll('.loc-group');
  groups.forEach(function(group){
    group.querySelectorAll(':scope > .entry').forEach(function(e){
      if(e.classList.contains('highlight'))return;
      e.style.minHeight='';
    });
  });
  var rowLog=null;
  groups.forEach(function(group){
    var entries=[];
    group.querySelectorAll(':scope > .entry').forEach(function(e){
      if(e.classList.contains('is-hidden')||e.classList.contains('highlight'))return;
      if(e.style.display==='none')return;
      var r=e.getBoundingClientRect();
      if(r.width>2&&r.height>2)entries.push(e);
    });
    var rows=[];
    entries.forEach(function(e){
      var t=Math.round(e.getBoundingClientRect().top);
      var row=null;
      for(var i=0;i<rows.length;i++){if(Math.abs(rows[i].t-t)<=10){row=rows[i];break;}}
      if(!row){row={t:t,cards:[]};rows.push(row);}
      row.cards.push(e);
    });
    rows.forEach(function(row){
      if(row.cards.length<2)return;
      var maxH=0;
      row.cards.forEach(function(e){
        if(e.querySelector('details.patches[open]'))return;
        maxH=Math.max(maxH,e.getBoundingClientRect().height);
      });
      if(!(maxH>0)){
        row.cards.forEach(function(e){maxH=Math.max(maxH,e.getBoundingClientRect().height);});
      }
      var mh=Math.round(maxH);
      if(!(mh>0))return;
      row.cards.forEach(function(e){e.style.minHeight=mh+'px';});
      if(!rowLog)rowLog={n:row.cards.length,mh:mh,hs:row.cards.map(function(e){return Math.round(e.getBoundingClientRect().height);}),open:row.cards.map(function(e){return !!e.querySelector('details.patches[open]');})};
    });
  });
  // #region agent log
  try{
    fetch('http://127.0.0.1:7529/ingest/1cf46354-1d61-4c80-bd72-a340f1db1b51',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'c00e3e'},body:JSON.stringify({sessionId:'c00e3e',runId:'post-fix',hypothesisId:'C',location:'catalog:equalizeCatalogCardRows',message:'equalize card row heights',data:rowLog||{n:0},timestamp:Date.now()})}).catch(function(){});
  }catch(eDbgC){}
  // #endregion
}
function scheduleEqualizeCardRows(){
  if(window._eqCardRows)cancelAnimationFrame(window._eqCardRows);
  window._eqCardRows=requestAnimationFrame(function(){
    window._eqCardRows=0;
    equalizeCatalogCardRows();
  });
}
window.collapseInactivePatchTrees=collapseInactivePatchTrees;
window.equalizeCatalogCardRows=equalizeCatalogCardRows;
window.scheduleEqualizeCardRows=scheduleEqualizeCardRows;
"""

REMEMBER_OLD = """function rememberViewed(el){
  if(!el)return;
  lastViewedEntry=el;
  markSelected(el);
}"""

REMEMBER_NEW = FUNCS + """function rememberViewed(el){
  if(!el)return;
  lastViewedEntry=el;
  markSelected(el);
  collapseInactivePatchTrees('viewed');
}"""

CLEAR_OLD = """function clearSelect(){
  closeChosenPreview({skipJumpExit:true});
  document.querySelectorAll('.entry.selected').forEach(function(e){e.classList.remove('selected');});
  document.querySelectorAll('.index li.selected').forEach(function(li){li.classList.remove('selected');});
}"""

CLEAR_NEW = """function clearSelect(){
  closeChosenPreview({skipJumpExit:true});
  document.querySelectorAll('.entry.selected').forEach(function(e){e.classList.remove('selected');});
  document.querySelectorAll('.index li.selected').forEach(function(li){li.classList.remove('selected');});
  if(typeof collapseInactivePatchTrees==='function')collapseInactivePatchTrees('clear');
}"""

TOGGLE_OLD = """document.addEventListener('toggle',function(e){
  var details=e.target;
  if(!details||details.tagName!=='DETAILS'||!details.open)return;
  if(!details.classList.contains('patches')&&!details.classList.contains('grp'))return;
  var entry=details.closest('.entry');
  if(!entry||entry.classList.contains('highlight'))return;
  if(keepPatchesInPlace(entry))return;
  if(patchesOverflowGrid(entry)){
    var root=entry.querySelector('details.patches')||details;
    promotePatchesToOverlay(entry, root);
  }
},true);
document.querySelectorAll('.entry').forEach(function(el){entryPatchCount(el);});"""

TOGGLE_NEW = """document.addEventListener('toggle',function(e){
  var details=e.target;
  if(!details||details.tagName!=='DETAILS')return;
  if(!details.classList.contains('patches')&&!details.classList.contains('grp'))return;
  var entry=details.closest('.entry');
  if(!entry)return;
  if(details.open&&typeof rememberViewed==='function')rememberViewed(entry);
  else if(typeof collapseInactivePatchTrees==='function')collapseInactivePatchTrees('toggle');
  if(typeof scheduleEqualizeCardRows==='function')scheduleEqualizeCardRows();
  if(!details.open)return;
  if(entry.classList.contains('highlight'))return;
  if(keepPatchesInPlace(entry))return;
  if(patchesOverflowGrid(entry)){
    var root=entry.querySelector('details.patches')||details;
    promotePatchesToOverlay(entry, root);
  }
},true);
document.querySelectorAll('.entry').forEach(function(el){entryPatchCount(el);});
if(typeof collapseInactivePatchTrees==='function')collapseInactivePatchTrees('boot');
window.addEventListener('resize',function(){if(typeof scheduleEqualizeCardRows==='function')scheduleEqualizeCardRows();},{passive:true});
document.addEventListener('load',function(e){if(e.target&&e.target.tagName==='IMG'&&e.target.closest&&e.target.closest('.entry')&&typeof scheduleEqualizeCardRows==='function')scheduleEqualizeCardRows();},true);"""


def patch_one(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    n = 0
    for old, new in (
        (REMEMBER_OLD, REMEMBER_NEW),
        (CLEAR_OLD, CLEAR_NEW),
        (TOGGLE_OLD, TOGGLE_NEW),
    ):
        if old not in text:
            raise SystemExit(f"Missing snippet in {path.name}:\n{old[:180]!r}")
        c = text.count(old)
        if c != 1:
            raise SystemExit(f"{path.name}: expected 1 occurrence, got {c} for {old[:80]!r}")
        text = text.replace(old, new, 1)
        n += 1
    path.write_text(text, encoding="utf-8")
    print(f"{path.name}: {n} replacements")


def main() -> None:
    for p in FILES:
        patch_one(p)


if __name__ == "__main__":
    main()
