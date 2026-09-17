#!/usr/bin/env python3
"""Instrument placeCatalogJumpStack for missing ↑/↓ debug (session c00e3e)."""
from pathlib import Path

ROOT = Path("/home/phnx/kiro-kontakt-patch")
DESKTOP = [
    ROOT / "public/catalogs/DS-CATALOG.html",
    ROOT / "public/catalogs/KONTAKT-CATALOG.html",
]
PORTABLE = [
    ROOT / "public/catalogs/DS-CATALOG-portable.html",
    ROOT / "public/catalogs/KONTAKT-CATALOG-portable.html",
]

HELPER = r"""function debugJumpStackLog(reason,extra){
  // #region agent log
  try{
    var stack=document.getElementById('catalogJumpStack');
    var ix=document.getElementById('catalogIndex');
    var top=stack?stack.querySelector('a.top'):document.querySelector('a.top');
    var bot=stack?stack.querySelector('a.bottom'):document.querySelector('a.bottom');
    var jcs=stack?getComputedStyle(stack):null;
    var jr=stack?stack.getBoundingClientRect():null;
    var tcs=top?getComputedStyle(top):null;
    var bcs=bot?getComputedStyle(bot):null;
    var tr=top?top.getBoundingClientRect():null;
    var br=bot?bot.getBoundingClientRect():null;
    var data={
      reason:reason||'',
      portable:!!window.CATALOG_PORTABLE,
      ns:String(window.CATALOG_NS||''),
      vw:window.innerWidth,vh:window.innerHeight,
      sides:document.body.classList.contains('display-sides'),
      middle:document.body.classList.contains('display-middle'),
      fs:document.body.classList.contains('display-fs'),
      ixWin:document.body.classList.contains('index-window-open'),
      ixEmb:!!(ix&&ix.classList.contains('is-embedded')),
      ixCol:!!(ix&&ix.classList.contains('is-collapsed')),
      stack:!!stack,
      kids:stack?stack.children.length:0,
      disp:jcs?jcs.display:'',
      vis:jcs?jcs.visibility:'',
      z:jcs?jcs.zIndex:'',
      jr:jr?{x:Math.round(jr.x),y:Math.round(jr.y),w:Math.round(jr.width),h:Math.round(jr.height)}:null,
      tr:tr?{x:Math.round(tr.x),y:Math.round(tr.y),w:Math.round(tr.width),h:Math.round(tr.height),d:tcs&&tcs.display}:null,
      br:br?{x:Math.round(br.x),y:Math.round(br.y),w:Math.round(br.width),h:Math.round(br.height),d:bcs&&bcs.display}:null,
      styleB:stack?stack.style.bottom:'',
      styleR:stack?stack.style.right:''
    };
    if(extra){for(var k in extra)data[k]=extra[k];}
    var key=JSON.stringify({r:data.reason,s:data.sides,m:data.middle,d:data.disp,j:data.jr,e:data.ixEmb,c:data.ixCol,w:data.ixWin,k:data.kids,p:data.portable});
    var now=Date.now();
    if(debugJumpStackLog._k===key&&now-(debugJumpStackLog._t||0)<1200)return;
    debugJumpStackLog._k=key;debugJumpStackLog._t=now;
    fetch('http://127.0.0.1:7529/ingest/1cf46354-1d61-4c80-bd72-a340f1db1b51',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'c00e3e'},body:JSON.stringify({sessionId:'c00e3e',runId:'jump-miss',hypothesisId:'A-E',location:'placeCatalogJumpStack',message:'jump-place',data:data,timestamp:now})}).catch(function(){});
  }catch(errJ){}
  // #endregion
}
"""

DESK_OLD = """function placeCatalogJumpStack(){
  var stack=document.getElementById('catalogJumpStack');
  var main=document.getElementById('catalogMain');
  if(!stack){
    if(typeof placeCatalogEdgeStack==='function')placeCatalogEdgeStack();
    return;
  }
  var pane=document.body.classList.contains('display-sides')||document.body.classList.contains('display-middle');
  if(!pane||!main){
    stack.style.cssText='';
    if(typeof placeCatalogEdgeStack==='function')placeCatalogEdgeStack();
    return;
  }
"""

DESK_NEW = HELPER + """function placeCatalogJumpStack(){
  var stack=document.getElementById('catalogJumpStack');
  var main=document.getElementById('catalogMain');
  if(!stack){
    // #region agent log
    debugJumpStackLog('no-stack');
    // #endregion
    if(typeof placeCatalogEdgeStack==='function')placeCatalogEdgeStack();
    return;
  }
  var pane=document.body.classList.contains('display-sides')||document.body.classList.contains('display-middle');
  if(!pane||!main){
    stack.style.cssText='';
    // #region agent log
    debugJumpStackLog('no-pane',{pane:!!pane,main:!!main});
    // #endregion
    if(typeof placeCatalogEdgeStack==='function')placeCatalogEdgeStack();
    return;
  }
"""

DESK_END_OLD = """  stack.style.left='auto';
  stack.style.top='auto';
  if(typeof placeCatalogEdgeStack==='function')placeCatalogEdgeStack();
}
function bindCatalogJumpScroll(){"""

DESK_END_NEW = """  stack.style.left='auto';
  stack.style.top='auto';
  // #region agent log
  debugJumpStackLog('placed',{inset:typeof catalogJumpStackBottomInset==='function'?catalogJumpStackBottomInset():null,bottom:stack.style.bottom,right:stack.style.right});
  // #endregion
  if(typeof placeCatalogEdgeStack==='function')placeCatalogEdgeStack();
}
function bindCatalogJumpScroll(){"""

PORT_OLD = """function placeCatalogJumpStack(){
  var stack=document.getElementById('catalogJumpStack');
  var main=document.getElementById('catalogMain');
  if(!stack){
    if(typeof placeCatalogEdgeStack==='function')placeCatalogEdgeStack();
    return;
  }
  var sides=document.body.classList.contains('display-sides');
  var middle=document.body.classList.contains('display-middle');
  var fs=document.body.classList.contains('display-fs');
  var mainCs=main?getComputedStyle(main):null;
  var r=main?main.getBoundingClientRect():null;
  var mainHide=!main||fs||!(sides||middle)||(mainCs&&mainCs.display==='none')||!r||r.width<8||r.height<8;
  if(mainHide){
    stack.style.cssText='display:none!important';
  }else{
"""

PORT_NEW = HELPER + """function placeCatalogJumpStack(){
  var stack=document.getElementById('catalogJumpStack');
  var main=document.getElementById('catalogMain');
  if(!stack){
    // #region agent log
    debugJumpStackLog('no-stack');
    // #endregion
    if(typeof placeCatalogEdgeStack==='function')placeCatalogEdgeStack();
    return;
  }
  var sides=document.body.classList.contains('display-sides');
  var middle=document.body.classList.contains('display-middle');
  var fs=document.body.classList.contains('display-fs');
  var mainCs=main?getComputedStyle(main):null;
  var r=main?main.getBoundingClientRect():null;
  var mainHide=!main||fs||!(sides||middle)||(mainCs&&mainCs.display==='none')||!r||r.width<8||r.height<8;
  if(mainHide){
    stack.style.cssText='display:none!important';
    // #region agent log
    debugJumpStackLog('main-hide',{mainHide:true,fs:fs,sides:sides,middle:middle});
    // #endregion
  }else{
"""

PORT_END_OLD = """    stack.style.left='auto';
    stack.style.top='auto';
  }
  if(typeof placeCatalogEdgeStack==='function')placeCatalogEdgeStack();
  if(typeof dbgPortableJumpGap==='function')dbgPortableJumpGap('placeJump');
}"""

PORT_END_NEW = """    stack.style.left='auto';
    stack.style.top='auto';
    // #region agent log
    debugJumpStackLog('placed',{mainHide:false,noteInset:typeof catalogJumpStackBottomInset==='function'?catalogJumpStackBottomInset():null,bottom:stack.style.bottom,right:stack.style.right});
    // #endregion
  }
  if(typeof placeCatalogEdgeStack==='function')placeCatalogEdgeStack();
  if(typeof dbgPortableJumpGap==='function')dbgPortableJumpGap('placeJump');
}"""


def safe_write(path: Path, text: str) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    out = tmp.read_text(encoding="utf-8")
    if not out.rstrip().endswith("</html>"):
        tmp.unlink(missing_ok=True)
        raise SystemExit(f"{path.name}: rewrite would drop </html>")
    path.write_text(out, encoding="utf-8")
    tmp.unlink(missing_ok=True)


def patch_one(path: Path, old_a, new_a, old_b, new_b) -> None:
    text = path.read_text(encoding="utf-8")
    if "function debugJumpStackLog(" in text:
        print(f"skip already instrumented: {path.name}")
        return
    if old_a not in text:
        raise SystemExit(f"{path.name}: start block not found")
    if old_b not in text:
        raise SystemExit(f"{path.name}: end block not found")
    if text.count(old_a) != 1:
        raise SystemExit(f"{path.name}: start count={text.count(old_a)}")
    if text.count(old_b) != 1:
        raise SystemExit(f"{path.name}: end count={text.count(old_b)}")
    text = text.replace(old_a, new_a, 1).replace(old_b, new_b, 1)
    safe_write(path, text)
    print(f"ok {path.name} bytes={path.stat().st_size}")


def main() -> None:
    for p in DESKTOP:
        patch_one(p, DESK_OLD, DESK_NEW, DESK_END_OLD, DESK_END_NEW)
    for p in PORTABLE:
        patch_one(p, PORT_OLD, PORT_NEW, PORT_END_OLD, PORT_END_NEW)


if __name__ == "__main__":
    main()
