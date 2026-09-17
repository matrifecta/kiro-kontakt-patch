#!/usr/bin/env python3
"""Revert temporary patch peek; press still activates the card."""
from pathlib import Path

ROOT = Path("/home/phnx/kiro-kontakt-patch")
FILES = [
    ROOT / "public/catalogs/KONTAKT-CATALOG.html",
    ROOT / "public/catalogs/DS-CATALOG.html",
    ROOT / "public/catalogs/KONTAKT-CATALOG-portable.html",
    ROOT / "public/catalogs/DS-CATALOG-portable.html",
]

KEEP_OLD = """      if((active&&e===active)||(window.patchPeekEntry&&e===window.patchPeekEntry)){if(d.open)nKeep++;return;}"""
KEEP_NEW = """      if(active&&e===active){if(d.open)nKeep++;return;}"""

REMEMBER_OLD = """function isActivePatchCard(entry){
  var a=typeof activePatchEntry==='function'?activePatchEntry():null;
  return !!(entry&&a&&entry===a);
}
function endPatchPeek(src){
  var e=window.patchPeekEntry;
  if(!e)return;
  window.patchPeekEntry=null;
  window.patchPeekPress=false;
  e.classList.remove('is-patch-peek');
  e.querySelectorAll('details.patches, details.grp').forEach(function(d){d.open=false;});
  if(typeof scheduleEqualizeCardRows==='function')scheduleEqualizeCardRows();
  // #region agent log
  try{
    fetch('http://127.0.0.1:7529/ingest/1cf46354-1d61-4c80-bd72-a340f1db1b51',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'c00e3e'},body:JSON.stringify({sessionId:'c00e3e',runId:'post-fix',hypothesisId:'D',location:'catalog:endPatchPeek',message:'end patch peek',data:{src:String(src||''),id:e.id||''},timestamp:Date.now()})}).catch(function(){});
  }catch(eDbgD){}
  // #endregion
}
function beginPatchPeek(entry,press){
  if(!entry||isActivePatchCard(entry)||entry.classList.contains('highlight'))return false;
  var root=entry.querySelector('details.patches');
  if(!root)return false;
  if(window.patchPeekEntry&&window.patchPeekEntry!==entry)endPatchPeek('switch');
  window.patchPeekEntry=entry;
  window.patchPeekPress=!!press;
  entry.classList.add('is-patch-peek');
  root.open=true;
  if(typeof collapseInactivePatchTrees==='function')collapseInactivePatchTrees('peek');
  if(typeof scheduleEqualizeCardRows==='function')scheduleEqualizeCardRows();
  // #region agent log
  try{
    fetch('http://127.0.0.1:7529/ingest/1cf46354-1d61-4c80-bd72-a340f1db1b51',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'c00e3e'},body:JSON.stringify({sessionId:'c00e3e',runId:'post-fix',hypothesisId:'D',location:'catalog:beginPatchPeek',message:'begin patch peek',data:{id:entry.id||'',press:!!press,open:!!root.open,sel:entry.classList.contains('selected')},timestamp:Date.now()})}).catch(function(){});
  }catch(eDbgD2){}
  // #endregion
  return true;
}
function patchPeekPointerOut(ev){
  var e=window.patchPeekEntry;
  if(!e||!ev)return;
  var r=e.getBoundingClientRect();
  var x=ev.clientX,y=ev.clientY;
  if(x<r.left||x>r.right||y<r.top||y>r.bottom)endPatchPeek('move-out');
}
window.endPatchPeek=endPatchPeek;
window.beginPatchPeek=beginPatchPeek;
function rememberViewed(el){
  if(!el)return;
  lastViewedEntry=el;
  markSelected(el);
  if(window.patchPeekEntry&&window.patchPeekEntry!==el)endPatchPeek('viewed');
  collapseInactivePatchTrees('viewed');
}"""

REMEMBER_NEW = """function rememberViewed(el){
  if(!el)return;
  lastViewedEntry=el;
  markSelected(el);
  collapseInactivePatchTrees('viewed');
}"""

CLICK_OLD = """document.addEventListener('click',function(e){
  var sum=e.target.closest&&e.target.closest('summary');
  if(!sum)return;
  var details=sum.parentNode;
  if(!details||details.tagName!=='DETAILS'||!details.classList.contains('patches'))return;
  var entry=details.closest('.entry');
  if(!entry||entry.classList.contains('highlight'))return;
  if(window.patchPeekEntry===entry||entry.classList.contains('is-patch-peek')){
    e.preventDefault();
    e.stopPropagation();
    return;
  }
  if(details.open)return;
  if(keepPatchesInPlace(entry))return;
  if(entryPatchCount(entry)>=GRID_PATCH_OVERLAY_MIN){
    e.preventDefault();
    e.stopPropagation();
    promotePatchesToOverlay(entry, details);
  }
},true);"""

CLICK_NEW = """document.addEventListener('click',function(e){
  var sum=e.target.closest&&e.target.closest('summary');
  if(!sum)return;
  var details=sum.parentNode;
  if(!details||details.tagName!=='DETAILS'||!details.classList.contains('patches'))return;
  var entry=details.closest('.entry');
  if(!entry||entry.classList.contains('highlight'))return;
  if(details.open)return;
  if(keepPatchesInPlace(entry))return;
  if(entryPatchCount(entry)>=GRID_PATCH_OVERLAY_MIN){
    e.preventDefault();
    e.stopPropagation();
    promotePatchesToOverlay(entry, details);
  }
},true);"""

TOGGLE_OLD = """document.addEventListener('pointerdown',function(e){
  var sum=e.target.closest&&e.target.closest('summary');
  if(!sum)return;
  var details=sum.parentNode;
  if(!details||details.tagName!=='DETAILS'||(!details.classList.contains('patches')&&!details.classList.contains('grp')))return;
  var entry=details.closest('.entry');
  if(!entry||entry.classList.contains('highlight'))return;
  if(isActivePatchCard(entry))return;
  var press=e.pointerType!=='mouse';
  beginPatchPeek(entry,press);
  try{if(sum.setPointerCapture&&e.pointerId!=null)sum.setPointerCapture(e.pointerId);}catch(errCap){}
},true);
document.addEventListener('pointerup',function(e){
  if(!window.patchPeekEntry||!window.patchPeekPress)return;
  endPatchPeek('up');
},true);
document.addEventListener('pointercancel',function(){
  if(window.patchPeekEntry)endPatchPeek('cancel');
},true);
document.addEventListener('pointermove',function(e){
  if(!window.patchPeekEntry)return;
  patchPeekPointerOut(e);
},true);
document.addEventListener('toggle',function(e){
  var details=e.target;
  if(!details||details.tagName!=='DETAILS')return;
  if(!details.classList.contains('patches')&&!details.classList.contains('grp'))return;
  var entry=details.closest('.entry');
  if(!entry)return;
  if(details.open){
    if(isActivePatchCard(entry)||entry.classList.contains('highlight')){
      if(typeof rememberViewed==='function')rememberViewed(entry);
    }else{
      beginPatchPeek(entry,!!window.patchPeekPress);
    }
  }else if(window.patchPeekEntry===entry){
    endPatchPeek('toggle-close');
  }else if(typeof collapseInactivePatchTrees==='function'){
    collapseInactivePatchTrees('toggle');
  }
  if(typeof scheduleEqualizeCardRows==='function')scheduleEqualizeCardRows();
  if(!details.open)return;
  if(entry.classList.contains('highlight'))return;
  if(window.patchPeekEntry===entry||entry.classList.contains('is-patch-peek'))return;
  if(keepPatchesInPlace(entry))return;
  if(patchesOverflowGrid(entry)){
    var root=entry.querySelector('details.patches')||details;
    promotePatchesToOverlay(entry, root);
  }
},true);"""

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
},true);"""


def patch_one(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    n = 0
    for old, new in (
        (KEEP_OLD, KEEP_NEW),
        (REMEMBER_OLD, REMEMBER_NEW),
        (CLICK_OLD, CLICK_NEW),
        (TOGGLE_OLD, TOGGLE_NEW),
    ):
        if old not in text:
            raise SystemExit(f"Missing snippet in {path.name}:\n{old[:200]!r}")
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
