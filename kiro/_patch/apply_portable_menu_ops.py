#!/usr/bin/env python3
"""Portable: Search/KW FS exit, docked KW visible, landscape Sides 2-pane (no auto FS)."""
from __future__ import annotations

import os
import tempfile
from pathlib import Path

ROOT = Path("/home/phnx/kiro-kontakt-patch/public/catalogs")
FILES = [
    ROOT / "KONTAKT-CATALOG-portable.html",
    ROOT / "DS-CATALOG-portable.html",
]

CSS_MARK = "</style></head>"
CSS_ADD = """
/* fix-PORTABLE-MENU-OPS: docked KW stays a body pane; header S/K clickable over FS */
html body.catalog-portable.display-sides.display-middle.search-chrome-collapsed.kw-open:not(.kw-chrome-collapsed):not(.ac-fs-open):not(.kw-fs-open) #filterWrap{
  display:flex!important;visibility:visible!important;pointer-events:auto!important;
  position:relative!important;inset:auto!important;transform:none!important;
  width:100%!important;max-width:none!important;flex:1 1 0%!important;
  min-height:8rem!important;height:auto!important;max-height:none!important
}
html body.catalog-portable.display-sides.display-middle.search-chrome-collapsed.kw-open:not(.kw-chrome-collapsed):not(.ac-fs-open):not(.kw-fs-open) #searchChrome{
  display:none!important;visibility:hidden!important;pointer-events:none!important
}
html body.catalog-portable.ac-fs-open .catalog-header,
html body.catalog-portable.kw-fs-open .catalog-header,
html body.catalog-portable.ac-fs-open #hdrMenuBtns,
html body.catalog-portable.kw-fs-open #hdrMenuBtns,
html body.catalog-portable.ac-fs-open #hdrSearchBtn,
html body.catalog-portable.kw-fs-open #hdrSearchBtn,
html body.catalog-portable.ac-fs-open #hdrKwBtn,
html body.catalog-portable.kw-fs-open #hdrKwBtn{
  position:relative!important;z-index:80!important;pointer-events:auto!important
}
html body.catalog-portable.portable-sk-pair:not(.ac-fs-open):not(.kw-fs-open) #hdrMenuBtns,
html body.catalog-portable.portable-sk-pair:not(.ac-fs-open):not(.kw-fs-open) #hdrSearchBtn,
html body.catalog-portable.portable-sk-pair:not(.ac-fs-open):not(.kw-fs-open) #hdrKwBtn{
  pointer-events:auto!important;z-index:40!important
}
"""

HDR_S_OLD = """    if(typeof dbgPortableSkCover==='function')dbgPortableSkCover('hdr-s-content','A');
    // #endregion
    return;
  }
  if(window.CATALOG_PORTABLE&&document.body.classList.contains('display-fs')){
"""

HDR_S_NEW = """    if(typeof dbgPortableSkCover==='function')dbgPortableSkCover('hdr-s-content','A');
    // #endregion
    return;
  }
  if(window.CATALOG_PORTABLE){
    var fsHdrS=typeof portableMenuFsOn==='function'?portableMenuFsOn():'';
    if(fsHdrS==='search'){
      if(typeof portableExitMenuFs==='function')portableExitMenuFs();
      if(typeof portableNoteMenuWanted==='function')portableNoteMenuWanted('search',true);
      if(typeof placePortableHandles==='function')placePortableHandles();
      syncHdrMenuBtns();
      // #region agent log
      if(typeof dbgPortableSkCover==='function')dbgPortableSkCover('hdr-s-exit-fs','A');
      try{fetch('http://127.0.0.1:7529/ingest/1cf46354-1d61-4c80-bd72-a340f1db1b51',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'c00e3e'},body:JSON.stringify({sessionId:'c00e3e',runId:'menu-ops',hypothesisId:'H-SFS',location:'catalog:toggleHdrSearch',message:'hdr S exit search FS',data:{fs:typeof portableMenuFsOn==='function'?portableMenuFsOn():'',ac:document.body.classList.contains('ac-fs-open'),mid:document.body.classList.contains('display-middle')},timestamp:Date.now()})}).catch(function(){});}catch(eHdrSfs){}
      // #endregion
      return;
    }
    if(fsHdrS==='keywords'&&typeof portableExitMenuFs==='function')portableExitMenuFs();
  }
  if(window.CATALOG_PORTABLE&&document.body.classList.contains('display-fs')){
"""

HDR_S_MID_OLD = """    if(fsS==='keywords'||visS==='keywords'){
      if(fsS==='keywords'&&typeof portableEnterMenuFs==='function')portableEnterMenuFs('search');
      if(typeof portableCoerceMiddleMenu==='function')portableCoerceMiddleMenu('search');
"""

HDR_S_MID_NEW = """    if(fsS==='keywords'||visS==='keywords'){
      if(fsS==='keywords'&&typeof portableExitMenuFs==='function')portableExitMenuFs();
      if(typeof portableCoerceMiddleMenu==='function')portableCoerceMiddleMenu('search');
"""

HDR_K_OLD = """    if(typeof dbgPortableSkCover==='function')dbgPortableSkCover('hdr-k-content','C');
    // #endregion
    return;
  }
  if(window.CATALOG_PORTABLE&&document.body.classList.contains('display-fs')){
"""

HDR_K_NEW = """    if(typeof dbgPortableSkCover==='function')dbgPortableSkCover('hdr-k-content','C');
    // #endregion
    return;
  }
  if(window.CATALOG_PORTABLE){
    var fsHdrK=typeof portableMenuFsOn==='function'?portableMenuFsOn():'';
    if(fsHdrK==='keywords'){
      if(typeof portableExitMenuFs==='function')portableExitMenuFs();
      if(typeof portableNoteMenuWanted==='function')portableNoteMenuWanted('keywords',true);
      if(typeof placePortableHandles==='function')placePortableHandles();
      syncHdrMenuBtns();
      // #region agent log
      if(typeof dbgPortableSkCover==='function')dbgPortableSkCover('hdr-k-exit-fs','C');
      try{fetch('http://127.0.0.1:7529/ingest/1cf46354-1d61-4c80-bd72-a340f1db1b51',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'c00e3e'},body:JSON.stringify({sessionId:'c00e3e',runId:'menu-ops',hypothesisId:'H-KFS',location:'catalog:toggleHdrKw',message:'hdr K exit kw FS',data:{fs:typeof portableMenuFsOn==='function'?portableMenuFsOn():'',kw:document.body.classList.contains('kw-fs-open'),mid:document.body.classList.contains('display-middle')},timestamp:Date.now()})}).catch(function(){});}catch(eHdrKfs){}
      // #endregion
      return;
    }
    if(fsHdrK==='search'&&typeof portableExitMenuFs==='function')portableExitMenuFs();
  }
  if(window.CATALOG_PORTABLE&&document.body.classList.contains('display-fs')){
"""

SYNC_FS_OLD = """  if(fsNow){
    if((which==='search'||which==='keywords')&&fsNow!==which&&typeof portableEnterMenuFs==='function')portableEnterMenuFs(which);
    if(document.body.classList.contains('display-middle')&&which&&typeof portableCoerceMiddleMenu==='function')portableCoerceMiddleMenu(which==='keywords'?'keywords':'search');
    return;
  }
"""

SYNC_FS_NEW = """  if(fsNow){
    if(fsNow===which)return;
    if(typeof portableExitMenuFs==='function')portableExitMenuFs();
    // #region agent log
    try{fetch('http://127.0.0.1:7529/ingest/1cf46354-1d61-4c80-bd72-a340f1db1b51',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'c00e3e'},body:JSON.stringify({sessionId:'c00e3e',runId:'menu-ops',hypothesisId:'H-SKFS',location:'portable:syncModeFromMenus',message:'exit fs then dock other menu',data:{which:which||'',was:fsNow||'',land:typeof portableScreenOrient==='function'?portableScreenOrient():'',mid:document.body.classList.contains('display-middle')},timestamp:Date.now()})}).catch(function(){});}catch(eSyncFs){}
    // #endregion
  }
"""

PLACE_OLD = """  if(!ch||!fw)return;
  var body=document.body;
  var col=document.getElementById('searchCol');
  if(mode==='sides'){
"""

PLACE_NEW = """  if(!ch||!fw)return;
  if(window.CATALOG_PORTABLE&&mode!=='fs')mode='sides';
  var body=document.body;
  var col=document.getElementById('searchCol');
  if(mode==='sides'){
"""

RELAYOUT_MODE_OLD = """        var mode=(which==='search'||which==='keywords')?'sides':(document.body.classList.contains('display-middle')?'middle':'sides');
        try{placeMenusForDisplay(mode);}catch(ePlaceR){}
"""

RELAYOUT_MODE_NEW = """        var mode='sides';
        try{placeMenusForDisplay(mode);}catch(ePlaceR){}
"""

COERCE_OLD = """    try{if(typeof showAc==='function')showAc(((document.getElementById('searchInput')||{}).value||'').trim().toLowerCase(),{force:true});}catch(errM){}
  }
  if(typeof syncHdrMenuBtns==='function')syncHdrMenuBtns();
"""

COERCE_NEW = """    try{if(typeof showAc==='function')showAc(((document.getElementById('searchInput')||{}).value||'').trim().toLowerCase(),{force:true});}catch(errM){}
  }
  if(typeof placeMenusForDisplay==='function')placeMenusForDisplay('sides');
  if(typeof syncHdrMenuBtns==='function')syncHdrMenuBtns();
"""

ORIENT_HOLD_OLD = """  if(hold)next='sides';
  else if(window.CATALOG_PORTABLE){
    var searchOffO=document.body.classList.contains('search-chrome-collapsed');
    var kwOffO=document.body.classList.contains('kw-chrome-collapsed')||!document.body.classList.contains('kw-open');
    var anyMenu=!!(combo&&(combo.searchOn||combo.kwOn));
    if(!anyMenu&&(document.body.classList.contains('display-content')||(searchOffO&&kwOffO)))next='content';
    else if(o==='landscape')next='sides';
    else if(next==='middle'&&o!=='portrait')next='sides';
  }
  if(typeof setDisplayMode==='function')setDisplayMode(next,{keepMenus:true,keepMenuFs:!!hold,orientKeepFs:!!hold});
"""

ORIENT_HOLD_NEW = """  if(window.CATALOG_PORTABLE&&o==='landscape'){
    hold='';
    portableMenuFsHold='';
  }
  if(hold)next='sides';
  else if(window.CATALOG_PORTABLE){
    var searchOffO=document.body.classList.contains('search-chrome-collapsed');
    var kwOffO=document.body.classList.contains('kw-chrome-collapsed')||!document.body.classList.contains('kw-open');
    var anyMenu=!!(combo&&(combo.searchOn||combo.kwOn));
    if(!anyMenu&&(document.body.classList.contains('display-content')||(searchOffO&&kwOffO)))next='content';
    else if(o==='landscape')next='sides';
    else if(next==='middle'&&o!=='portrait')next='sides';
  }
  if(typeof setDisplayMode==='function')setDisplayMode(next,{keepMenus:true,keepMenuFs:!!hold,orientKeepFs:!!hold});
"""

RESTORE_HELD_OLD = """    if(heldFs&&!portableBoth&&typeof portableRestoreHeldFs==='function')portableRestoreHeldFs();
"""

RESTORE_HELD_NEW = """    if(heldFs&&!portableBoth&&!(typeof portableScreenOrient==='function'&&portableScreenOrient()==='landscape')&&typeof portableRestoreHeldFs==='function')portableRestoreHeldFs();
"""

TOGGLE_FS_OLD = """window.toggleKwFullscreen=function(){
  if(window.CATALOG_PORTABLE&&document.body.classList.contains('display-sides')){
    if(portableMenuFsOn()==='keywords')portableExitMenuFs();
    else portableEnterMenuFs('keywords');
    return;
  }
  if(typeof isPhoneViewport==='function'&&isPhoneViewport()){
    if(typeof setDisplayMode==='function')setDisplayMode('sides',{bothMenus:false,pick:true});
    return;
  }
  if(typeof expandKwMenu==='function')expandKwMenu();
};
window.toggleAcFullscreen=function(){
  if(window.CATALOG_PORTABLE&&document.body.classList.contains('display-sides')){
    if(portableMenuFsOn()==='search')portableExitMenuFs();
    else portableEnterMenuFs('search');
    return;
  }
  if(typeof isPhoneViewport==='function'&&isPhoneViewport()){
    if(typeof setDisplayMode==='function')setDisplayMode('sides',{pick:true});
    return;
  }
  if(typeof expandSearchMenu==='function')expandSearchMenu();
};
(function(){
  if(!window.CATALOG_PORTABLE)return;
  var _setAc=window.setAcFullscreen;
  window.setAcFullscreen=function(on){
    if(document.body.classList.contains('display-sides')){
      if(on)portableEnterMenuFs('search');
      else if(portableMenuFsOn()==='search')portableExitMenuFs();
      return;
    }
    if(_setAc)return _setAc.apply(this,arguments);
  };
})();
"""

TOGGLE_FS_NEW = """window.toggleKwFullscreen=function(){
  if(window.CATALOG_PORTABLE){
    if(portableMenuFsOn()==='keywords')portableExitMenuFs();
    else portableEnterMenuFs('keywords');
    return;
  }
  if(typeof isPhoneViewport==='function'&&isPhoneViewport()){
    if(typeof setDisplayMode==='function')setDisplayMode('sides',{bothMenus:false,pick:true});
    return;
  }
  if(typeof expandKwMenu==='function')expandKwMenu();
};
window.toggleAcFullscreen=function(){
  if(window.CATALOG_PORTABLE){
    if(portableMenuFsOn()==='search')portableExitMenuFs();
    else portableEnterMenuFs('search');
    return;
  }
  if(typeof isPhoneViewport==='function'&&isPhoneViewport()){
    if(typeof setDisplayMode==='function')setDisplayMode('sides',{pick:true});
    return;
  }
  if(typeof expandSearchMenu==='function')expandSearchMenu();
};
(function(){
  if(!window.CATALOG_PORTABLE)return;
  var _setAc=window.setAcFullscreen;
  window.setAcFullscreen=function(on){
    if(document.body.classList.contains('display-sides')||document.body.classList.contains('display-middle')){
      if(on)portableEnterMenuFs('search');
      else if(portableMenuFsOn()==='search')portableExitMenuFs();
      return;
    }
    if(_setAc)return _setAc.apply(this,arguments);
  };
  var _setKw=window.setKwFullscreen;
  window.setKwFullscreen=function(on){
    if(document.body.classList.contains('display-sides')||document.body.classList.contains('display-middle')){
      if(on)portableEnterMenuFs('keywords');
      else if(portableMenuFsOn()==='keywords')portableExitMenuFs();
      return;
    }
    if(_setKw)return _setKw.apply(this,arguments);
  };
})();
"""


def patch(text: str) -> str:
    reps = [
        (HDR_S_OLD, HDR_S_NEW),
        (HDR_S_MID_OLD, HDR_S_MID_NEW),
        (HDR_K_OLD, HDR_K_NEW),
        (SYNC_FS_OLD, SYNC_FS_NEW),
        (PLACE_OLD, PLACE_NEW),
        (RELAYOUT_MODE_OLD, RELAYOUT_MODE_NEW),
        (COERCE_OLD, COERCE_NEW),
        (ORIENT_HOLD_OLD, ORIENT_HOLD_NEW),
        (RESTORE_HELD_OLD, RESTORE_HELD_NEW),
        (TOGGLE_FS_OLD, TOGGLE_FS_NEW),
    ]
    for old, new in reps:
        n = text.count(old)
        if n != 1:
            raise SystemExit(f"expected 1 occurrence of snippet, found {n}: {old[:110]!r}")
        text = text.replace(old, new, 1)
    if CSS_MARK not in text:
        raise SystemExit("missing </style></head>")
    if "fix-PORTABLE-MENU-OPS" not in text:
        text = text.replace(CSS_MARK, CSS_ADD + CSS_MARK, 1)
    return text


def write_safe(path: Path, data: str, before_c00: int) -> None:
    if not data.rstrip().endswith("</html>"):
        raise SystemExit(f"{path.name} rewrite missing </html>")
    if data.count("sessionId:'c00e3e'") < before_c00:
        raise SystemExit(f"{path.name}: lost c00e3e logs")
    fd, tmp = tempfile.mkstemp(prefix=path.stem + ".", suffix=".html", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise
    got = path.stat().st_size
    if got < 100000:
        raise SystemExit(f"{path.name} too small after write: {got}")
    check = path.read_text(encoding="utf-8")
    if not check.rstrip().endswith("</html>"):
        raise SystemExit(f"{path.name} after write missing </html>")
    if "fix-PORTABLE-MENU-OPS" not in check:
        raise SystemExit(f"{path.name} missing MENU-OPS mark")


def main() -> None:
    for path in FILES:
        raw = path.read_text(encoding="utf-8")
        before_c00 = raw.count("sessionId:'c00e3e'")
        out = patch(raw)
        write_safe(path, out, before_c00)
        print(f"patched {path.name} {len(raw)} -> {len(out)} c00={before_c00}->{out.count(chr(39)+'c00e3e'+chr(39))}")


if __name__ == "__main__":
    main()
