#!/usr/bin/env python3
"""Portable: portrait→landscape must leave Middle and use Sides 2-pane."""
from __future__ import annotations

import os
import tempfile
from pathlib import Path

ROOT = Path("/home/phnx/kiro-kontakt-patch/public/catalogs")
FILES = [
    ROOT / "KONTAKT-CATALOG-portable.html",
    ROOT / "DS-CATALOG-portable.html",
]

CSS_MARK = """html body.catalog-portable.portable-sk-pair #catalogMain,
html body.catalog-portable.portable-landscape.display-sides:not(.display-middle).kw-open:not(.kw-chrome-collapsed):not(.search-chrome-collapsed):not(.ac-fs-open):not(.kw-fs-open) #catalogMain{
  display:none!important
}
"""

CSS_ADD = CSS_MARK + """
/* fix-PORTABLE-SK-ROTATE: landscape Sides 2-pane even if Middle class leftover */
html body.catalog-portable.portable-landscape.display-sides,
html body.catalog-portable.portable-landscape.display-sides.display-middle{
  display:grid!important;flex-direction:unset!important;
  grid-template-rows:auto minmax(0,1fr)!important;height:100dvh;overflow:hidden
}
html body.catalog-portable.portable-landscape.display-sides.display-middle .catalog-header,
html body.catalog-portable.portable-landscape.display-sides .catalog-header{
  grid-column:1/-1!important;grid-row:1!important;flex:0 0 auto
}
html body.catalog-portable.portable-landscape.display-sides:not(.search-chrome-collapsed):not(.kw-open),
html body.catalog-portable.portable-landscape.display-sides.display-middle:not(.search-chrome-collapsed):not(.kw-open){
  grid-template-columns:minmax(0,42%) minmax(0,1fr)!important
}
html body.catalog-portable.portable-landscape.display-sides.display-middle:not(.search-chrome-collapsed) #searchChrome,
html body.catalog-portable.portable-landscape.display-sides:not(.display-middle):not(.search-chrome-collapsed) #searchChrome{
  grid-column:1!important;grid-row:2!important;display:flex!important;
  flex:unset!important;max-height:none!important;width:auto!important;height:auto!important
}
html body.catalog-portable.portable-landscape.display-sides.display-middle:not(.search-chrome-collapsed):not(.kw-open) #catalogMain,
html body.catalog-portable.portable-landscape.display-sides:not(.display-middle):not(.search-chrome-collapsed):not(.kw-open) #catalogMain{
  grid-column:2!important;grid-row:2!important;display:block!important;
  flex:unset!important;width:auto!important
}
html body.catalog-portable.portable-landscape.display-sides.display-middle.search-chrome-collapsed.kw-open:not(.kw-chrome-collapsed),
html body.catalog-portable.portable-landscape.display-sides:not(.display-middle).search-chrome-collapsed.kw-open:not(.kw-chrome-collapsed){
  grid-template-columns:minmax(0,1fr) minmax(0,42%)!important
}
html body.catalog-portable.portable-landscape.display-sides.display-middle.search-chrome-collapsed.kw-open:not(.kw-chrome-collapsed) #filterWrap,
html body.catalog-portable.portable-landscape.display-sides:not(.display-middle).search-chrome-collapsed.kw-open:not(.kw-chrome-collapsed) #filterWrap{
  grid-column:2!important;grid-row:2!important;display:flex!important;
  position:relative!important;inset:auto!important;transform:none!important;
  width:auto!important;max-width:none!important;max-height:none!important;flex:unset!important
}
html body.catalog-portable.portable-landscape.display-sides.display-middle.search-chrome-collapsed.kw-open:not(.kw-chrome-collapsed) #catalogMain,
html body.catalog-portable.portable-landscape.display-sides:not(.display-middle).search-chrome-collapsed.kw-open:not(.kw-chrome-collapsed) #catalogMain{
  grid-column:1!important;grid-row:2!important;display:block!important;flex:unset!important
}
html body.catalog-portable.portable-landscape.display-sides.display-middle.kw-open:not(.kw-chrome-collapsed):not(.search-chrome-collapsed),
html body.catalog-portable.portable-sk-pair{
  grid-template-columns:minmax(0,1fr) minmax(0,1fr)!important
}
html body.catalog-portable.portable-landscape.display-sides.display-middle.kw-open:not(.kw-chrome-collapsed):not(.search-chrome-collapsed) #filterWrap{
  grid-column:2!important;grid-row:2!important;display:flex!important;
  position:relative!important;inset:auto!important;transform:none!important;
  width:auto!important;max-width:none!important;max-height:none!important;flex:unset!important
}
html body.catalog-portable.portable-landscape.display-sides.display-middle.kw-open:not(.kw-chrome-collapsed):not(.search-chrome-collapsed) #catalogMain{
  display:none!important
}
html body.catalog-portable.portable-landscape.display-sides.sides-portrait-flip:not(.search-chrome-collapsed):not(.kw-open) #searchChrome,
html body.catalog-portable.portable-landscape.display-sides.display-middle.sides-portrait-flip:not(.search-chrome-collapsed):not(.kw-open) #searchChrome{grid-column:2!important}
html body.catalog-portable.portable-landscape.display-sides.sides-portrait-flip:not(.search-chrome-collapsed):not(.kw-open) #catalogMain,
html body.catalog-portable.portable-landscape.display-sides.display-middle.sides-portrait-flip:not(.search-chrome-collapsed):not(.kw-open) #catalogMain{grid-column:1!important}
html body.catalog-portable.portable-landscape.display-sides.sides-portrait-flip.search-chrome-collapsed.kw-open:not(.kw-chrome-collapsed) #filterWrap,
html body.catalog-portable.portable-landscape.display-sides.display-middle.sides-portrait-flip.search-chrome-collapsed.kw-open:not(.kw-chrome-collapsed) #filterWrap{grid-column:1!important}
html body.catalog-portable.portable-landscape.display-sides.sides-portrait-flip.search-chrome-collapsed.kw-open:not(.kw-chrome-collapsed) #catalogMain,
html body.catalog-portable.portable-landscape.display-sides.display-middle.sides-portrait-flip.search-chrome-collapsed.kw-open:not(.kw-chrome-collapsed) #catalogMain{grid-column:2!important}
html body.catalog-portable.portable-sk-pair #catalogMain,
html body.catalog-portable.portable-sk-pair.index-window-open #catalogMain,
html body.catalog-portable.portable-landscape.portable-sk-pair.display-sides.index-window-open #catalogMain,
html body.catalog-portable.portable-landscape.display-sides.kw-open:not(.kw-chrome-collapsed):not(.search-chrome-collapsed):not(.ac-fs-open):not(.kw-fs-open) #catalogMain,
html body.catalog-portable.portable-landscape.display-sides.index-window-open.kw-open:not(.kw-chrome-collapsed):not(.search-chrome-collapsed) #catalogMain{
  display:none!important;visibility:hidden!important;pointer-events:none!important;
  width:0!important;min-width:0!important;max-width:0!important;height:0!important;overflow:hidden!important
}
"""

WANT_LAYOUT_OLD = """function portableWantLayout(){
  try{return (window.matchMedia&&window.matchMedia('(orientation:portrait)').matches)?'middle':'sides';}catch(e){return 'sides';}
}
"""

WANT_LAYOUT_NEW = """function portableWantLayout(){
  try{
    if(typeof portableScreenOrient==='function')return portableScreenOrient()==='portrait'?'middle':'sides';
    return (window.matchMedia&&window.matchMedia('(orientation:portrait)').matches)?'middle':'sides';
  }catch(e){return 'sides';}
}
"""

PERSIST_OLD = """  if(typeof isPhoneViewport==='function'&&isPhoneViewport()&&persistDisplay==='middle'&&window.matchMedia&&!window.matchMedia('(orientation:portrait)').matches){
    persistDisplay='sides';mode='sides';
  }
"""

PERSIST_NEW = """  var portableLandNow=window.CATALOG_PORTABLE&&typeof portableScreenOrient==='function'&&portableScreenOrient()==='landscape';
  if(persistDisplay==='middle'&&(portableLandNow||(typeof isPhoneViewport==='function'&&isPhoneViewport()&&window.matchMedia&&!window.matchMedia('(orientation:portrait)').matches))){
    persistDisplay='sides';mode='sides';
  }
"""

ADD_MODE_OLD = """  document.body.classList.add('display-'+mode);
  if(currentDisplay==='middle'){
    document.body.classList.add('display-middle');
"""

ADD_MODE_NEW = """  document.body.classList.add('display-'+mode);
  if(window.CATALOG_PORTABLE&&mode!=='content'&&typeof portableScreenOrient==='function'&&portableScreenOrient()==='landscape'){
    document.body.classList.remove('display-middle','display-content');
    if(!document.body.classList.contains('display-fs'))document.body.classList.add('display-sides');
    currentDisplay='sides';
    try{localStorage.setItem(DISPLAY_KEY,'sides');}catch(errLandMid){}
  }
  if(currentDisplay==='middle'){
    document.body.classList.add('display-middle');
"""

SIDES_COLS_OLD = """  var middle=typeof displayIsMiddle==='function'?displayIsMiddle():document.body.classList.contains('display-middle');
  var portrait=typeof isPortraitDesktopSides==='function'&&isPortraitDesktopSides();
  var phone=typeof isPhoneViewport==='function'&&isPhoneViewport();
  var phonePort=phone&&(typeof portableScreenOrient==='function'?portableScreenOrient()==='portrait':!!(window.matchMedia&&window.matchMedia('(orientation:portrait)').matches));
"""

SIDES_COLS_NEW = """  var middle=typeof displayIsMiddle==='function'?displayIsMiddle():document.body.classList.contains('display-middle');
  var portrait=typeof isPortraitDesktopSides==='function'&&isPortraitDesktopSides();
  var phone=typeof isPhoneViewport==='function'&&isPhoneViewport();
  if(window.CATALOG_PORTABLE&&typeof portableScreenOrient==='function'&&portableScreenOrient()==='landscape'&&middle&&!document.body.classList.contains('display-content')&&!document.body.classList.contains('display-fs')){
    document.body.classList.remove('display-middle');
    try{if(typeof currentDisplay!=='undefined'&&currentDisplay==='middle')currentDisplay='sides';}catch(eMidLand){}
    middle=false;
  }
  var phonePort=phone&&(typeof portableScreenOrient==='function'?portableScreenOrient()==='portrait':!!(window.matchMedia&&window.matchMedia('(orientation:portrait)').matches));
"""

SYNC_OLD = """function syncDisplayForOrientation(){
  if(window.CATALOG_PORTABLE&&typeof syncPortableLayoutChrome==='function')syncPortableLayoutChrome();
  if(window.CATALOG_PORTABLE&&document.body.classList.contains('portable-kb-open'))return;
  var o=displayOrientId();
  if(lastDisplayOrient==null){lastDisplayOrient=o;return;}
  if(o===lastDisplayOrient)return;
  var hold='';
  if(window.CATALOG_PORTABLE){
    hold=(typeof portableMenuFsHold==='string'&&portableMenuFsHold)||(typeof portableMenuFsOn==='function'&&portableMenuFsOn())||'';
    if(hold==='search'||hold==='keywords')portableMenuFsHold=hold;
    else hold='';
  }
  var next=resolveDisplayForOrient(o);
  lastDisplayOrient=o;
  if(hold)next='sides';
  else if(window.CATALOG_PORTABLE){
    var searchOffO=document.body.classList.contains('search-chrome-collapsed');
    var kwOffO=document.body.classList.contains('kw-chrome-collapsed')||!document.body.classList.contains('kw-open');
    if(document.body.classList.contains('display-content')||(searchOffO&&kwOffO))next='content';
    else if(next==='middle'&&o!=='portrait')next='sides';
  }
  if(typeof setDisplayMode==='function')setDisplayMode(next,{keepMenuFs:!!hold,orientKeepFs:!!hold});
  if(hold&&typeof portableRestoreHeldFs==='function')portableRestoreHeldFs();
"""

SYNC_NEW = """function syncDisplayForOrientation(){
  if(window.CATALOG_PORTABLE&&typeof syncPortableLayoutChrome==='function')syncPortableLayoutChrome();
  var o=displayOrientId();
  var stuckMiddle=!!(window.CATALOG_PORTABLE&&o==='landscape'&&(document.body.classList.contains('display-middle')||(typeof currentDisplay!=='undefined'&&currentDisplay==='middle')));
  var kb=!!(window.CATALOG_PORTABLE&&document.body.classList.contains('portable-kb-open'));
  if(kb&&!stuckMiddle&&(lastDisplayOrient==null||o===lastDisplayOrient))return;
  if(lastDisplayOrient==null){lastDisplayOrient=o;if(!stuckMiddle)return;}
  if(o===lastDisplayOrient&&!stuckMiddle)return;
  var hold='';
  if(window.CATALOG_PORTABLE){
    hold=(typeof portableMenuFsHold==='string'&&portableMenuFsHold)||(typeof portableMenuFsOn==='function'&&portableMenuFsOn())||'';
    if(hold==='search'||hold==='keywords')portableMenuFsHold=hold;
    else hold='';
  }
  var combo=window.CATALOG_PORTABLE&&typeof portableLandscapeMenuCombo==='function'?portableLandscapeMenuCombo():null;
  var next=resolveDisplayForOrient(o);
  lastDisplayOrient=o;
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
  if(window.CATALOG_PORTABLE&&o==='landscape'&&next==='sides'){
    document.body.classList.remove('display-middle');
    try{currentDisplay='sides';}catch(eLandCur){}
    if(combo&&typeof portableRestoreMenuCombo==='function')portableRestoreMenuCombo(combo);
    if(combo&&combo.searchOn&&typeof expandSearchMenu==='function')expandSearchMenu();
    if(combo&&combo.kwOn&&typeof expandKwMenu==='function')expandKwMenu();
    if(combo&&!combo.searchOn&&typeof collapseSearchMenu==='function')collapseSearchMenu();
    if(combo&&!combo.kwOn&&typeof collapseKwMenu==='function')collapseKwMenu();
    document.body.classList.remove('display-middle');
    if(typeof applySidesCols==='function')applySidesCols();
    if(typeof placeMenusForDisplay==='function')placeMenusForDisplay('sides');
    if(typeof syncHdrMenuBtns==='function')syncHdrMenuBtns();
    if(typeof syncPortableLayoutChrome==='function')syncPortableLayoutChrome();
  }
  if(hold&&typeof portableRestoreHeldFs==='function')portableRestoreHeldFs();
  // #region agent log
  try{
    var scR=document.getElementById('searchChrome'),fwR=document.getElementById('filterWrap'),cmR=document.getElementById('catalogMain');
    function boxR(el){if(!el)return null;var r=el.getBoundingClientRect(),cs=getComputedStyle(el);return {d:cs.display,w:Math.round(r.width),h:Math.round(r.height),x:Math.round(r.x),y:Math.round(r.y)};}
    fetch('http://127.0.0.1:7529/ingest/1cf46354-1d61-4c80-bd72-a340f1db1b51',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'c00e3e'},body:JSON.stringify({sessionId:'c00e3e',runId:'sk-rotate',hypothesisId:'H-ROT',location:'portable:syncDisplayForOrientation',message:'orient-sides',data:{o:o,next:next,stuck:!!stuckMiddle,kb:!!kb,hold:String(hold||''),combo:combo,cur:typeof currentDisplay!=='undefined'?String(currentDisplay):'',middle:document.body.classList.contains('display-middle'),sides:document.body.classList.contains('display-sides'),pair:document.body.classList.contains('portable-sk-pair'),sOn:!document.body.classList.contains('search-chrome-collapsed'),kOpen:document.body.classList.contains('kw-open'),search:boxR(scR),kw:boxR(fwR),main:boxR(cmR)},timestamp:Date.now()})}).catch(function(){});
  }catch(eRot){}
  // #endregion
"""

COMBO_OLD = """function portableSaveMenuCombo(){
"""

COMBO_NEW = """var portableMenuWanted={search:false,kw:false};
function portableNoteMenuWanted(which,on){
  if(!window.CATALOG_PORTABLE)return;
  if(which==='search')portableMenuWanted.search=!!on;
  else if(which==='keywords')portableMenuWanted.kw=!!on;
}
function portableLandscapeMenuCombo(){
  var now=typeof portableMenusOpenNow==='function'?portableMenusOpenNow():{searchOn:false,kwOn:false};
  var vis=typeof portableMiddleVisible==='function'?portableMiddleVisible():'';
  var sOn=!!((portableMenuWanted&&portableMenuWanted.search)||now.searchOn||vis==='search');
  var kOn=!!((portableMenuWanted&&portableMenuWanted.kw)||now.kwOn||vis==='keywords');
  try{
    var sb=document.getElementById('hdrSearchBtn');
    var kb=document.getElementById('hdrKwBtn');
    if(sb&&sb.classList.contains('is-on'))sOn=true;
    if(kb&&kb.classList.contains('is-on'))kOn=true;
  }catch(eCombo){}
  return {searchOn:sOn,kwOn:kOn};
}
window.portableNoteMenuWanted=portableNoteMenuWanted;
window.portableLandscapeMenuCombo=portableLandscapeMenuCombo;
function portableSaveMenuCombo(){
"""

HDR_S_MID_OLD = """    }else if(typeof portableCoerceMiddleMenu==='function')portableCoerceMiddleMenu('search');
    if(typeof placePortableHandles==='function')placePortableHandles();
    syncHdrMenuBtns();
    if(typeof portableSyncModeFromMenus==='function')portableSyncModeFromMenus('search');
    // #region agent log
    if(typeof dbgPortableSkCover==='function')dbgPortableSkCover('hdr-s-middle','A');
"""

HDR_S_MID_NEW = """    }else if(typeof portableCoerceMiddleMenu==='function')portableCoerceMiddleMenu('search');
    if(typeof portableNoteMenuWanted==='function')portableNoteMenuWanted('search',(typeof portableMiddleVisible==='function'?portableMiddleVisible():'')==='search');
    if(typeof placePortableHandles==='function')placePortableHandles();
    syncHdrMenuBtns();
    if(typeof portableSyncModeFromMenus==='function')portableSyncModeFromMenus('search');
    // #region agent log
    if(typeof dbgPortableSkCover==='function')dbgPortableSkCover('hdr-s-middle','A');
"""

HDR_S_CONTENT_OLD = """    if(typeof expandSearchMenu==='function')expandSearchMenu();
    if(typeof portableSyncModeFromMenus==='function')portableSyncModeFromMenus('search');
    if(typeof placePortableHandles==='function')placePortableHandles();
    syncHdrMenuBtns();
    // #region agent log
    if(typeof dbgPortableSkCover==='function')dbgPortableSkCover('hdr-s-content','A');
"""

HDR_S_CONTENT_NEW = """    if(typeof expandSearchMenu==='function')expandSearchMenu();
    if(typeof portableNoteMenuWanted==='function')portableNoteMenuWanted('search',true);
    if(typeof portableSyncModeFromMenus==='function')portableSyncModeFromMenus('search');
    if(typeof placePortableHandles==='function')placePortableHandles();
    syncHdrMenuBtns();
    // #region agent log
    if(typeof dbgPortableSkCover==='function')dbgPortableSkCover('hdr-s-content','A');
"""

HDR_S_SIDES_OLD = """  if(window.CATALOG_PORTABLE&&typeof portableSyncModeFromMenus==='function')portableSyncModeFromMenus('search');
  // #region agent log
  if(typeof dbgPortableSkCover==='function')dbgPortableSkCover('hdr-s-sides','B');
"""

HDR_S_SIDES_NEW = """  if(window.CATALOG_PORTABLE&&typeof portableNoteMenuWanted==='function')portableNoteMenuWanted('search',!document.body.classList.contains('search-chrome-collapsed'));
  if(window.CATALOG_PORTABLE&&typeof portableSyncModeFromMenus==='function')portableSyncModeFromMenus('search');
  // #region agent log
  if(typeof dbgPortableSkCover==='function')dbgPortableSkCover('hdr-s-sides','B');
"""

HDR_K_MID_OLD = """    else if(typeof portableCoerceMiddleMenu==='function')portableCoerceMiddleMenu('keywords');
    if(typeof placePortableHandles==='function')placePortableHandles();
    syncHdrMenuBtns();
    if(typeof portableSyncModeFromMenus==='function')portableSyncModeFromMenus('keywords');
    // #region agent log
    if(typeof dbgPortableSkCover==='function')dbgPortableSkCover('hdr-k-middle','C');
"""

HDR_K_MID_NEW = """    else if(typeof portableCoerceMiddleMenu==='function')portableCoerceMiddleMenu('keywords');
    if(typeof portableNoteMenuWanted==='function')portableNoteMenuWanted('keywords',(typeof portableMiddleVisible==='function'?portableMiddleVisible():'')==='keywords');
    if(typeof placePortableHandles==='function')placePortableHandles();
    syncHdrMenuBtns();
    if(typeof portableSyncModeFromMenus==='function')portableSyncModeFromMenus('keywords');
    // #region agent log
    if(typeof dbgPortableSkCover==='function')dbgPortableSkCover('hdr-k-middle','C');
"""

HDR_K_CONTENT_OLD = """    if(typeof expandKwMenu==='function')expandKwMenu();
    else if(typeof toggleFilter==='function')toggleFilter();
    if(typeof portableSyncModeFromMenus==='function')portableSyncModeFromMenus('keywords');
    if(typeof placePortableHandles==='function')placePortableHandles();
    syncHdrMenuBtns();
    // #region agent log
    if(typeof dbgPortableSkCover==='function')dbgPortableSkCover('hdr-k-content','C');
"""

HDR_K_CONTENT_NEW = """    if(typeof expandKwMenu==='function')expandKwMenu();
    else if(typeof toggleFilter==='function')toggleFilter();
    if(typeof portableNoteMenuWanted==='function')portableNoteMenuWanted('keywords',true);
    if(typeof portableSyncModeFromMenus==='function')portableSyncModeFromMenus('keywords');
    if(typeof placePortableHandles==='function')placePortableHandles();
    syncHdrMenuBtns();
    // #region agent log
    if(typeof dbgPortableSkCover==='function')dbgPortableSkCover('hdr-k-content','C');
"""

HDR_K_SIDES_OLD = """  if(window.CATALOG_PORTABLE&&typeof portableSyncModeFromMenus==='function')portableSyncModeFromMenus('keywords');
}
function indexEmbedPrefKey(){return 'catalog-index-embed-'+(window.CATALOG_NS||'catalog');}
"""

HDR_K_SIDES_NEW = """  if(window.CATALOG_PORTABLE&&typeof portableNoteMenuWanted==='function'){
    var fwWant=document.getElementById('filterWrap');
    portableNoteMenuWanted('keywords',!document.body.classList.contains('kw-chrome-collapsed')&&!!(fwWant&&fwWant.classList.contains('open')&&document.body.classList.contains('kw-open')));
  }
  if(window.CATALOG_PORTABLE&&typeof portableSyncModeFromMenus==='function')portableSyncModeFromMenus('keywords');
}
function indexEmbedPrefKey(){return 'catalog-index-embed-'+(window.CATALOG_NS||'catalog');}
"""


def patch(text: str) -> str:
    reps = [
        (WANT_LAYOUT_OLD, WANT_LAYOUT_NEW),
        (PERSIST_OLD, PERSIST_NEW),
        (ADD_MODE_OLD, ADD_MODE_NEW),
        (SIDES_COLS_OLD, SIDES_COLS_NEW),
        (SYNC_OLD, SYNC_NEW),
        (COMBO_OLD, COMBO_NEW),
        (HDR_S_MID_OLD, HDR_S_MID_NEW),
        (HDR_S_CONTENT_OLD, HDR_S_CONTENT_NEW),
        (HDR_S_SIDES_OLD, HDR_S_SIDES_NEW),
        (HDR_K_MID_OLD, HDR_K_MID_NEW),
        (HDR_K_CONTENT_OLD, HDR_K_CONTENT_NEW),
        (HDR_K_SIDES_OLD, HDR_K_SIDES_NEW),
    ]
    for old, new in reps:
        n = text.count(old)
        if n != 1:
            raise SystemExit(f"expected 1 occurrence of snippet, found {n}: {old[:90]!r}")
        text = text.replace(old, new, 1)
    if CSS_MARK not in text:
        raise SystemExit("missing SK-TOOLBAR catalogMain CSS mark")
    if "fix-PORTABLE-SK-ROTATE" not in text:
        text = text.replace(CSS_MARK, CSS_ADD, 1)
    return text


def write_safe(path: Path, data: str) -> None:
    if not data.rstrip().endswith("</html>"):
        raise SystemExit(f"{path.name} rewrite missing </html>")
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


def main() -> None:
    for path in FILES:
        raw = path.read_text(encoding="utf-8")
        out = patch(raw)
        write_safe(path, out)
        print(f"patched {path.name} {len(raw)} -> {len(out)}")


if __name__ == "__main__":
    main()
