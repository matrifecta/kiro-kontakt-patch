#!/usr/bin/env python3
"""Portable: Index in-flow when collapsed; jump kids stay in stack;
orientation scroll/interaction probe (session c00e3e)."""
from pathlib import Path

ROOT = Path("/home/phnx/kiro-kontakt-patch/public/catalogs")
FILES = [
    ROOT / "KONTAKT-CATALOG-portable.html",
    ROOT / "DS-CATALOG-portable.html",
]

JUMP_KIDS_OLD = """  body.catalog-portable.display-sides #catalogJumpStack>a.top,
  body.catalog-portable.display-sides #catalogJumpStack>a.bottom,
  body.catalog-portable.display-middle #catalogJumpStack>a.top,
  body.catalog-portable.display-middle #catalogJumpStack>a.bottom{
"""

JUMP_KIDS_NEW = """  body.catalog-portable.content-window-on #catalogJumpStack>a.top,
  body.catalog-portable.content-window-on #catalogJumpStack>a.bottom,
  body.catalog-portable.display-sides #catalogJumpStack>a.top,
  body.catalog-portable.display-sides #catalogJumpStack>a.bottom,
  body.catalog-portable.display-middle #catalogJumpStack>a.top,
  body.catalog-portable.display-middle #catalogJumpStack>a.bottom{
"""

IX_GAP_OLD = """html body.catalog-portable.index-window-open #catalogIndex.is-collapsed:not(.is-embedded){
  margin-bottom:1.35rem!important
}
"""

IX_GAP_NEW = """html body.catalog-portable.index-window-open:not(.index-fill-doc) #catalogIndex.is-collapsed:not(.is-embedded),
html body.catalog-portable.display-content.index-window-open #catalogIndex.is-collapsed:not(.is-embedded),
html body.catalog-portable.index-window-open #catalogIndex.is-collapsed:not(.is-embedded){
  position:relative!important;top:auto!important;left:auto!important;right:auto!important;
  margin-bottom:1.35rem!important;z-index:2!important
}
"""

ORIENT_FN = r"""function dbgOrientInteract(phase,extra){
  // #region agent log
  try{
    var main=document.getElementById('catalogMain');
    var cb=main&&(main.querySelector(':scope > .catalog-body')||main.querySelector('.catalog-body'));
    var sc=(typeof catalogContentScroller==='function'&&catalogContentScroller())||cb||main;
    var bcs=getComputedStyle(document.body);
    var hcs=getComputedStyle(document.documentElement);
    var mcs=main?getComputedStyle(main):null;
    var scs=sc?getComputedStyle(sc):null;
    var ix=document.getElementById('catalogIndex');
    var h2=cb&&cb.querySelector('h2');
    var ir=ix?ix.getBoundingClientRect():null;
    var hr=h2?h2.getBoundingClientRect():null;
    var data={
      phase:String(phase||''),
      portable:!!window.CATALOG_PORTABLE,
      vw:innerWidth,vh:innerHeight,
      orient:(innerWidth>=innerHeight?'land':'port'),
      overlayFs:document.documentElement.classList.contains('overlay-fs')||document.documentElement.classList.contains('is-browser-fs'),
      bodyPos:bcs.position,bodyOv:bcs.overflowY,htmlOv:hcs.overflowY,
      pe:bcs.pointerEvents,
      sides:document.body.classList.contains('display-sides'),
      middle:document.body.classList.contains('display-middle'),
      content:document.body.classList.contains('display-content'),
      acFs:document.body.classList.contains('ac-fs-open'),
      kwFs:document.body.classList.contains('kw-fs-open'),
      mainD:mcs?mcs.display:'',mainOv:mcs?mcs.overflowY:'',mainPe:mcs?mcs.pointerEvents:'',
      mainH:main?Math.round(main.getBoundingClientRect().height):0,
      scTag:sc?(sc.id||sc.className||'').toString().slice(0,32):'',
      scOv:scs?scs.overflowY:'',scPe:scs?scs.pointerEvents:'',
      scClient:sc?sc.clientHeight:0,scScroll:sc?sc.scrollHeight:0,scTop:sc?Math.round(sc.scrollTop):0,
      ixPos:ix?getComputedStyle(ix).position:'',
      gap:ir&&hr?Math.round(hr.top-ir.bottom):null,
      jumpD:(function(){var j=document.getElementById('catalogJumpStack');return j?getComputedStyle(j).display:'';})()
    };
    if(extra){for(var k in extra)data[k]=extra[k];}
    fetch('http://127.0.0.1:7529/ingest/1cf46354-1d61-4c80-bd72-a340f1db1b51',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'c00e3e'},body:JSON.stringify({sessionId:'c00e3e',runId:'orient-scroll',hypothesisId:'A-E',location:'dbgOrientInteract',message:'orient-interact',data:data,timestamp:Date.now()})}).catch(function(){});
  }catch(errOi){}
  // #endregion
}
window.dbgOrientInteract=dbgOrientInteract;
"""

SYNC_OLD = """function syncDisplayForOrientation(){
  var o=displayOrientId();
  if(lastDisplayOrient==null){lastDisplayOrient=o;return;}
  if(o===lastDisplayOrient)return;
"""

SYNC_NEW = ORIENT_FN + """function syncDisplayForOrientation(){
  var o=displayOrientId();
  if(lastDisplayOrient==null){lastDisplayOrient=o;return;}
  if(o===lastDisplayOrient)return;
"""

AFTER_OLD = """  if(hold&&typeof portableRestoreHeldFs==='function')portableRestoreHeldFs();
  // #region agent log
  if(typeof dbgMobileUi==='function')dbgMobileUi('orient-fs',{hyp:'H-ORFS',hold:String(hold||''),o:String(o||''),next:String(next||'')});
  // #endregion
"""

AFTER_NEW = """  if(hold&&typeof portableRestoreHeldFs==='function')portableRestoreHeldFs();
  // #region agent log
  if(typeof dbgMobileUi==='function')dbgMobileUi('orient-fs',{hyp:'H-ORFS',hold:String(hold||''),o:String(o||''),next:String(next||'')});
  if(typeof dbgOrientInteract==='function')dbgOrientInteract('after-orient',{hold:String(hold||''),o:String(o||''),next:String(next||'')});
  // #endregion
"""


def safe_write(path: Path, text: str) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    out = tmp.read_text(encoding="utf-8")
    if not out.rstrip().endswith("</html>"):
        tmp.unlink(missing_ok=True)
        raise SystemExit(f"{path.name}: rewrite would drop </html>")
    path.write_text(out, encoding="utf-8")
    tmp.unlink(missing_ok=True)


def once(text, old, new, label, name):
    if old not in text:
        if new in text or (label == "orient-fn" and "function dbgOrientInteract(" in text):
            print(f"  skip {label} {name}")
            return text
        raise SystemExit(f"{name}: missing {label}: {old[:90]!r}")
    n = text.count(old)
    text = text.replace(old, new)
    print(f"  {n}x {label} {name}")
    return text


def patch(path: Path) -> None:
    name = path.name
    text = path.read_text(encoding="utf-8")
    text = once(text, JUMP_KIDS_OLD, JUMP_KIDS_NEW, "jump-kids", name)
    text = once(text, IX_GAP_OLD, IX_GAP_NEW, "ix-gap", name)
    if "function dbgOrientInteract(" not in text:
        text = once(text, SYNC_OLD, SYNC_NEW, "orient-fn", name)
    else:
        print(f"  skip orient-fn {name}")
    text = once(text, AFTER_OLD, AFTER_NEW, "after-orient", name)
    if "function dbgOrientInteract(" not in text:
        raise SystemExit(f"{name}: dbgOrientInteract missing")
    safe_write(path, text)
    print(f"ok {name} bytes={path.stat().st_size}")


def main() -> None:
    for p in FILES:
        print("==", p.name)
        patch(p)


if __name__ == "__main__":
    main()
