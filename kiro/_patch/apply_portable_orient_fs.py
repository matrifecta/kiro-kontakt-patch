#!/usr/bin/env python3
"""Persist one-menu FS across orientation remap in portable catalogs."""
from pathlib import Path

ROOT = Path("/home/phnx/kiro-kontakt-patch/public/catalogs")
FILES = [ROOT / "DS-CATALOG-portable.html", ROOT / "KONTAKT-CATALOG-portable.html"]

SET_START_OLD = """function setDisplayMode(mode,opts){
  opts=opts||{};
  var portableBoth=false;"""

SET_START_NEW = """function setDisplayMode(mode,opts){
  opts=opts||{};
  var heldFs='';
  if(window.CATALOG_PORTABLE){
    heldFs=(typeof portableMenuFsHold==='string'&&portableMenuFsHold)||(typeof portableMenuFsOn==='function'?portableMenuFsOn():'');
    if(heldFs!=='search'&&heldFs!=='keywords')heldFs='';
    else portableMenuFsHold=heldFs;
  }
  var portableBoth=false;"""

SIDES_WIPE_OLD = """  if(mode==='sides'){
    if(typeof acFsWanted!=='undefined')acFsWanted=false;
    if(typeof kwFsWanted!=='undefined')kwFsWanted=false;
    document.body.classList.remove('ac-fs-open','kw-fs-open','dual-fs-open');
    var _acs=document.getElementById('acShell');if(_acs)_acs.classList.remove('ac-fs');
    var _sfs=document.getElementById('searchStripFs');if(_sfs){_sfs.setAttribute('aria-pressed','false');_sfs.setAttribute('aria-label','Fullscreen search');}"""

SIDES_WIPE_NEW = """  if(mode==='sides'){
    if(!heldFs){
    if(typeof acFsWanted!=='undefined')acFsWanted=false;
    if(typeof kwFsWanted!=='undefined')kwFsWanted=false;
    document.body.classList.remove('ac-fs-open','kw-fs-open','dual-fs-open');
    var _acs=document.getElementById('acShell');if(_acs)_acs.classList.remove('ac-fs');
    var _sfs=document.getElementById('searchStripFs');if(_sfs){_sfs.setAttribute('aria-pressed','false');_sfs.setAttribute('aria-label','Fullscreen search');}
    }"""

SHELL_OLD = """    if(sh){sh.classList.add('open');sh.classList.remove('ac-fs','ac-fixed');}"""
SHELL_NEW = """    if(sh){sh.classList.add('open');if(!heldFs)sh.classList.remove('ac-fs','ac-fixed');}"""

END_WIPE_OLD = """  if(mode==='sides'&&currentDisplay!=='fs'){
    document.body.classList.remove('ac-fs-open','kw-fs-open','dual-fs-open');
    var _acsEnd=document.getElementById('acShell');if(_acsEnd)_acsEnd.classList.remove('ac-fs','ac-fixed');
    if(typeof acFsWanted!=='undefined')acFsWanted=false;
    if(typeof kwFsWanted!=='undefined')kwFsWanted=false;
  }"""

END_WIPE_NEW = """  if(mode==='sides'&&currentDisplay!=='fs'&&!heldFs){
    document.body.classList.remove('ac-fs-open','kw-fs-open','dual-fs-open');
    var _acsEnd=document.getElementById('acShell');if(_acsEnd)_acsEnd.classList.remove('ac-fs','ac-fixed');
    if(typeof acFsWanted!=='undefined')acFsWanted=false;
    if(typeof kwFsWanted!=='undefined')kwFsWanted=false;
  }"""

BOTH_OLD = """    if(portableBoth&&mode==='sides'){
      document.body.classList.remove('search-chrome-collapsed','kw-chrome-collapsed','ac-fs-open','kw-fs-open','dual-fs-open');"""

BOTH_NEW = """    if(heldFs&&!portableBoth&&typeof portableRestoreHeldFs==='function')portableRestoreHeldFs();
    else if(portableBoth&&mode==='sides'&&!heldFs){
      document.body.classList.remove('search-chrome-collapsed','kw-chrome-collapsed','ac-fs-open','kw-fs-open','dual-fs-open');"""

HOLD_DECL_OLD = "var portableMenuFsPrev=null;"
HOLD_DECL_NEW = "var portableMenuFsPrev=null;\nvar portableMenuFsHold='';"

RESTORE_FN = r"""
function portableRestoreHeldFs(){
  if(!window.CATALOG_PORTABLE)return;
  var which=portableMenuFsHold;
  if(which!=='search'&&which!=='keywords')return;
  var prev=portableMenuFsPrev;
  if(document.body.classList.contains('display-middle')&&window.matchMedia&&!window.matchMedia('(orientation:portrait)').matches){
    document.body.classList.remove('display-middle');
    try{currentDisplay='sides';}catch(errR){}
  }
  portableEnterMenuFs(which);
  if(prev)portableMenuFsPrev=prev;
  if(typeof portableEnsureScrollMenus==='function')portableEnsureScrollMenus();
  try{
    if(which==='search'){
      var acR=document.getElementById('acList');
      if(acR)acR.classList.add('open');
      if(typeof showAc==='function')showAc(((document.getElementById('searchInput')||{}).value||'').trim().toLowerCase(),{force:true});
    }
  }catch(errR2){}
  if(typeof syncPortableBrowserFs==='function')syncPortableBrowserFs();
  if(typeof placeCatalogJumpStack==='function')placeCatalogJumpStack();
  if(typeof placePortableHandles==='function')placePortableHandles();
  if(typeof syncHdrMenuBtns==='function')syncHdrMenuBtns();
  // #region agent log
  if(typeof dbgMobileUi==='function')dbgMobileUi('orient-fs-restore',{hyp:'H-ORFS',which:String(which||'')});
  // #endregion
}
"""

FS_ON_OLD = """function portableMenuFsOn(){
  var ac=document.body.classList.contains('ac-fs-open')&&!document.body.classList.contains('kw-fs-open');
  var kw=document.body.classList.contains('kw-fs-open')&&!document.body.classList.contains('ac-fs-open');
  return ac?'search':(kw?'keywords':'');
}"""

EXIT_OLD = """function portableExitMenuFs(){
  var prev=portableMenuFsPrev;
  portableMenuFsPrev=null;
  portableRestoreMenuCombo(prev);"""

EXIT_NEW = """function portableExitMenuFs(){
  var prev=portableMenuFsPrev;
  portableMenuFsPrev=null;
  portableMenuFsHold='';
  portableRestoreMenuCombo(prev);"""

RESIZE_OLD = """    if(!displayIsDesktop()){
      document.body.classList.remove('dual-fs-open');
      if(typeof kwFsWanted!=='undefined'&&currentDisplay!=='fs')kwFsWanted=false;"""

RESIZE_NEW = """    if(!displayIsDesktop()){
      if(!(typeof portableMenuFsHold==='string'&&(portableMenuFsHold==='search'||portableMenuFsHold==='keywords'))){
      document.body.classList.remove('dual-fs-open');
      if(typeof kwFsWanted!=='undefined'&&currentDisplay!=='fs')kwFsWanted=false;
      }"""

EXPOSE_OLD = "window.portableEnterMenuFs=portableEnterMenuFs;\nwindow.portableExitMenuFs=portableExitMenuFs;"
EXPOSE_NEW = "window.portableEnterMenuFs=portableEnterMenuFs;\nwindow.portableExitMenuFs=portableExitMenuFs;\nwindow.portableRestoreHeldFs=portableRestoreHeldFs;"


def patch(text):
    reps = [
        (SET_START_OLD, SET_START_NEW),
        (SIDES_WIPE_OLD, SIDES_WIPE_NEW),
        (SHELL_OLD, SHELL_NEW),
        (END_WIPE_OLD, END_WIPE_NEW),
        (BOTH_OLD, BOTH_NEW),
        (HOLD_DECL_OLD, HOLD_DECL_NEW),
        (FS_ON_OLD, FS_ON_OLD + RESTORE_FN),
        (EXIT_OLD, EXIT_NEW),
        (RESIZE_OLD, RESIZE_NEW),
        (EXPOSE_OLD, EXPOSE_NEW),
    ]
    for old, new in reps:
        n = text.count(old)
        if n != 1:
            raise SystemExit(f"expected 1 occurrence, got {n}: {old[:80]!r}")
        text = text.replace(old, new, 1)
    return text


def main():
    for path in FILES:
        raw = path.read_text(encoding="utf-8")
        if "function portableRestoreHeldFs" in raw and "if(mode==='sides'&&currentDisplay!=='fs'&&!heldFs)" in raw:
            print(f"already patched {path.name}")
            continue
        path.write_text(patch(raw), encoding="utf-8")
        print(f"patched {path.name}")


if __name__ == "__main__":
    main()
