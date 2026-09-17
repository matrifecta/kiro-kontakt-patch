#!/usr/bin/env python3
"""Portable: drop KW/Search Hide pair, hide no-op Flip, keep SK side-by-side through keyboard."""
from __future__ import annotations

import os
import tempfile
from pathlib import Path

ROOT = Path("/home/phnx/kiro-kontakt-patch/public/catalogs")
FILES = [
    ROOT / "KONTAKT-CATALOG-portable.html",
    ROOT / "DS-CATALOG-portable.html",
]

HIDE_OLD = """html body.catalog-portable:not(.kw-chrome-collapsed) #kwStripHide{
  display:inline-flex!important;visibility:visible!important
}
"""

HIDE_NEW = """html body.catalog-portable #filterToggle,
html body.catalog-portable #kwStripHide,
html body.catalog-portable:not(.kw-chrome-collapsed) #kwStripHide,
html body.catalog-portable.kw-fs-open #kwStripHide,
html body.catalog-portable .kw-strip-hide,
html body.catalog-portable .search-strip-hide{
  display:none!important;visibility:hidden!important;pointer-events:none!important;
  width:0!important;min-width:0!important;max-width:0!important;height:0!important;
  padding:0!important;margin:0!important;border:0!important;overflow:hidden!important
}
"""

CSS_MARK = "</style></head>"
CSS_ADD = """
/* fix-PORTABLE-SK-TOOLBAR: no Hide/Keywords pair; Flip only when it swaps; SK pair ignores keyboard orientation */
html body.catalog-portable #portraitFlipBtn,
html body.catalog-portable #hdrMenuBtns #portraitFlipBtn,
html body.catalog-portable #hdrCluster #portraitFlipBtn,
html body.catalog-portable #portraitFlipBtn[hidden]{
  display:none!important;visibility:hidden!important;pointer-events:none!important
}
html body.catalog-portable.portable-flip-on #portraitFlipBtn,
html body.catalog-portable.portable-flip-on #hdrMenuBtns #portraitFlipBtn,
html body.catalog-portable.portable-flip-on #hdrCluster #portraitFlipBtn,
html body.catalog-portable.portable-flip-on #portraitFlipBtn[hidden]{
  display:inline-flex!important;visibility:visible!important;pointer-events:auto!important
}
html body.catalog-portable.portable-sk-pair,
html body.catalog-portable.portable-landscape.display-sides:not(.display-middle).kw-open:not(.kw-chrome-collapsed):not(.search-chrome-collapsed):not(.ac-fs-open):not(.kw-fs-open){
  grid-template-columns:minmax(0,1fr) minmax(0,1fr)!important;
  grid-template-rows:auto minmax(0,1fr)!important
}
html body.catalog-portable.portable-sk-pair #searchChrome,
html body.catalog-portable.portable-landscape.display-sides:not(.display-middle).kw-open:not(.kw-chrome-collapsed):not(.search-chrome-collapsed):not(.ac-fs-open):not(.kw-fs-open) #searchChrome{
  grid-column:1!important;grid-row:2!important;display:flex!important
}
html body.catalog-portable.portable-sk-pair.sides-portrait-flip #searchChrome,
html body.catalog-portable.portable-landscape.sides-portrait-flip.display-sides:not(.display-middle).kw-open:not(.kw-chrome-collapsed):not(.search-chrome-collapsed):not(.ac-fs-open):not(.kw-fs-open) #searchChrome{
  grid-column:2!important
}
html body.catalog-portable.portable-sk-pair #filterWrap,
html body.catalog-portable.portable-landscape.display-sides:not(.display-middle).kw-open:not(.kw-chrome-collapsed):not(.search-chrome-collapsed):not(.ac-fs-open):not(.kw-fs-open) #filterWrap{
  grid-column:2!important;grid-row:2!important;display:flex!important;
  position:relative!important;inset:auto!important;transform:none!important;
  width:auto!important;max-width:none!important;height:auto!important;max-height:none!important
}
html body.catalog-portable.portable-sk-pair.sides-portrait-flip #filterWrap,
html body.catalog-portable.portable-landscape.sides-portrait-flip.display-sides:not(.display-middle).kw-open:not(.kw-chrome-collapsed):not(.search-chrome-collapsed):not(.ac-fs-open):not(.kw-fs-open) #filterWrap{
  grid-column:1!important
}
html body.catalog-portable.portable-sk-pair #catalogMain,
html body.catalog-portable.portable-landscape.display-sides:not(.display-middle).kw-open:not(.kw-chrome-collapsed):not(.search-chrome-collapsed):not(.ac-fs-open):not(.kw-fs-open) #catalogMain{
  display:none!important
}
"""

FLIP_OLD = """    if(window.CATALOG_PORTABLE){
      fb.textContent='Flip';
      fb.setAttribute('aria-label','Flip');
      fb.title='Swap left and right panes';
      fb.setAttribute('aria-pressed',on?'true':'false');
      fb.classList.add('hdr-menu-btn');
      fb.classList.toggle('is-on',!!on);
      fb.hidden=false;
      fb.removeAttribute('hidden');
      fb.setAttribute('aria-hidden','false');
"""

FLIP_NEW = """    if(window.CATALOG_PORTABLE){
      fb.textContent='Flip';
      fb.setAttribute('aria-label','Flip');
      fb.title='Swap left and right panes';
      fb.setAttribute('aria-pressed',on?'true':'false');
      fb.classList.add('hdr-menu-btn');
      fb.classList.toggle('is-on',!!on);
      if(typeof syncPortableLayoutChrome==='function')syncPortableLayoutChrome();
      var show=document.body.classList.contains('portable-flip-on');
      fb.hidden=!show;
      if(show)fb.removeAttribute('hidden');
      else fb.setAttribute('hidden','');
      fb.setAttribute('aria-hidden',show?'false':'true');
"""

ORIENT_OLD = """function displayOrientId(){
  try{
    if(window.matchMedia&&window.matchMedia('(orientation:portrait)').matches)return 'portrait';
  }catch(err){}
  return 'landscape';
}
"""

ORIENT_NEW = """function portableScreenOrient(){
  try{
    var t=screen&&screen.orientation&&screen.orientation.type;
    if(t)return String(t).indexOf('portrait')===0?'portrait':'landscape';
  }catch(errSo){}
  try{
    var ang=window.orientation;
    if(ang===90||ang===-90)return 'landscape';
    if(ang===0||ang===180)return 'portrait';
  }catch(errAng){}
  try{
    if(screen&&screen.width&&screen.height)return screen.width>=screen.height?'landscape':'portrait';
  }catch(errSc){}
  try{
    if(window.matchMedia&&window.matchMedia('(orientation:portrait)').matches)return 'portrait';
  }catch(errMq){}
  return (window.innerWidth||0)>=(window.innerHeight||0)?'landscape':'portrait';
}
function portableKeyboardOpen(){
  try{
    var vv=window.visualViewport;
    if(!vv)return false;
    var layout=Math.max(window.innerHeight||0,document.documentElement.clientHeight||0);
    return (layout-vv.height)>120;
  }catch(errKb){return false;}
}
function syncPortableLayoutChrome(){
  if(!window.CATALOG_PORTABLE||!document.body)return;
  var o=typeof portableScreenOrient==='function'?portableScreenOrient():'landscape';
  var kb=typeof portableKeyboardOpen==='function'&&portableKeyboardOpen();
  var sides=document.body.classList.contains('display-sides');
  var middle=document.body.classList.contains('display-middle');
  var content=document.body.classList.contains('display-content');
  var fs=document.body.classList.contains('display-fs')||document.body.classList.contains('ac-fs-open')||document.body.classList.contains('kw-fs-open');
  var searchOn=!document.body.classList.contains('search-chrome-collapsed');
  var fw=document.getElementById('filterWrap');
  var kwOn=!document.body.classList.contains('kw-chrome-collapsed')&&!!(fw&&fw.classList.contains('open'))&&document.body.classList.contains('kw-open');
  var pair=!!(sides&&!middle&&!fs&&searchOn&&kwOn);
  var flipOn=!!(sides&&!middle&&!content&&!document.body.classList.contains('display-fs')&&(searchOn||kwOn));
  document.body.classList.toggle('portable-portrait',o==='portrait');
  document.body.classList.toggle('portable-landscape',o==='landscape');
  document.body.classList.toggle('portable-kb-open',!!kb);
  document.body.classList.toggle('portable-sk-pair',pair);
  document.body.classList.toggle('portable-flip-on',flipOn);
  // #region agent log
  try{
    if(!window._dbgSkTb||Date.now()-window._dbgSkTb>700){
      window._dbgSkTb=Date.now();
      fetch('http://127.0.0.1:7529/ingest/1cf46354-1d61-4c80-bd72-a340f1db1b51',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'c00e3e'},body:JSON.stringify({sessionId:'c00e3e',runId:'sk-toolbar',hypothesisId:'H1',location:'portable:syncPortableLayoutChrome',message:'sk toolbar chrome',data:{o:o,kb:!!kb,sides:sides,middle:middle,content:content,fs:fs,searchOn:searchOn,kwOn:kwOn,pair:pair,flipOn:flipOn,vvH:window.visualViewport?Math.round(window.visualViewport.height):null,ih:window.innerHeight||0},timestamp:Date.now()})}).catch(function(){});
    }
  }catch(eDbgSk){}
  // #endregion
}
function displayOrientId(){
  try{
    if(window.CATALOG_PORTABLE&&typeof portableScreenOrient==='function')return portableScreenOrient();
    if(window.matchMedia&&window.matchMedia('(orientation:portrait)').matches)return 'portrait';
  }catch(err){}
  return 'landscape';
}
window.portableScreenOrient=portableScreenOrient;
window.portableKeyboardOpen=portableKeyboardOpen;
window.syncPortableLayoutChrome=syncPortableLayoutChrome;
"""

CLAMP_OLD = """function clampPortableVars(){
  var vw=window.innerWidth||400;
"""

CLAMP_NEW = """function clampPortableVars(){
  if(document.body&&document.body.classList.contains('portable-kb-open'))return;
  var vw=window.innerWidth||400;
"""

SIDES_OLD = """  document.body.classList.toggle('sides-orient-portrait',!!((portrait||(phone&&window.matchMedia&&window.matchMedia('(orientation:portrait)').matches))&&!middle));
"""

SIDES_NEW = """  var phonePort=phone&&(typeof portableScreenOrient==='function'?portableScreenOrient()==='portrait':!!(window.matchMedia&&window.matchMedia('(orientation:portrait)').matches));
  document.body.classList.toggle('sides-orient-portrait',!!((portrait||phonePort)&&!middle));
  if(typeof syncPortableLayoutChrome==='function')syncPortableLayoutChrome();
"""

HDR_OLD = """  if(kb){
    kb.classList.toggle('is-on',kwOn);
    kb.setAttribute('aria-pressed',kwOn?'true':'false');
    kb.title=kwOn?'Hide Keywords':'Show Keywords';
    kb.setAttribute('aria-label','Keywords');
  }
}
"""

HDR_NEW = """  if(kb){
    kb.classList.toggle('is-on',kwOn);
    kb.setAttribute('aria-pressed',kwOn?'true':'false');
    kb.title=kwOn?'Hide Keywords':'Show Keywords';
    kb.setAttribute('aria-label','Keywords');
  }
  if(typeof syncPortableLayoutChrome==='function')syncPortableLayoutChrome();
  if(typeof syncPortraitFlipBtn==='function')syncPortraitFlipBtn();
}
"""

VV_OLD = """  if(window.visualViewport){
    window.visualViewport.addEventListener('resize',applyAll);
    window.visualViewport.addEventListener('scroll',placeAcShell);
  }
"""

VV_NEW = """  if(window.visualViewport){
    window.visualViewport.addEventListener('resize',function(){
      if(typeof syncPortableLayoutChrome==='function')syncPortableLayoutChrome();
      if(document.body.classList.contains('portable-kb-open')){
        if(typeof placeAcShell==='function')placeAcShell();
        return;
      }
      applyAll();
    });
    window.visualViewport.addEventListener('scroll',placeAcShell);
  }
"""

RESIZE_OLD = """    if(typeof applySidesCols==='function')applySidesCols();
    if(currentDisplay==='fs'&&typeof applyDualLayout==='function')applyDualLayout();
    if(typeof syncDisplayForOrientation==='function')syncDisplayForOrientation();
    if(typeof portableEnsureScrollMenus==='function')portableEnsureScrollMenus();
  },{passive:true});
  // Orientation change applies that orientation's default (or saved pick). Width-only resizes do not coerce.
  window.addEventListener('orientationchange',function(){setTimeout(function(){if(typeof syncDisplayForOrientation==='function')syncDisplayForOrientation();if(typeof portableEnsureScrollMenus==='function')portableEnsureScrollMenus();},0);});
  if(window.matchMedia){
    var mqOrient=window.matchMedia('(orientation: portrait)');
    function onOrientMq(){if(typeof syncDisplayForOrientation==='function')syncDisplayForOrientation();}
"""

RESIZE_NEW = """    if(typeof syncPortableLayoutChrome==='function')syncPortableLayoutChrome();
    if(window.CATALOG_PORTABLE&&document.body.classList.contains('portable-kb-open')){
      if(typeof placeAcShell==='function')placeAcShell();
      return;
    }
    if(typeof applySidesCols==='function')applySidesCols();
    if(currentDisplay==='fs'&&typeof applyDualLayout==='function')applyDualLayout();
    if(typeof syncDisplayForOrientation==='function')syncDisplayForOrientation();
    if(typeof portableEnsureScrollMenus==='function')portableEnsureScrollMenus();
  },{passive:true});
  // Orientation change applies that orientation's default (or saved pick). Width-only resizes do not coerce.
  window.addEventListener('orientationchange',function(){setTimeout(function(){if(typeof syncPortableLayoutChrome==='function')syncPortableLayoutChrome();if(typeof syncDisplayForOrientation==='function')syncDisplayForOrientation();if(typeof portableEnsureScrollMenus==='function')portableEnsureScrollMenus();},0);});
  if(window.matchMedia){
    var mqOrient=window.matchMedia('(orientation: portrait)');
    function onOrientMq(){if(window.CATALOG_PORTABLE&&document.body.classList.contains('portable-kb-open'))return;if(typeof syncPortableLayoutChrome==='function')syncPortableLayoutChrome();if(typeof syncDisplayForOrientation==='function')syncDisplayForOrientation();}
"""

SYNC_OLD = """function syncDisplayForOrientation(){
  var o=displayOrientId();
  if(lastDisplayOrient==null){lastDisplayOrient=o;return;}
  if(o===lastDisplayOrient)return;
"""

SYNC_NEW = """function syncDisplayForOrientation(){
  if(window.CATALOG_PORTABLE&&typeof syncPortableLayoutChrome==='function')syncPortableLayoutChrome();
  if(window.CATALOG_PORTABLE&&document.body.classList.contains('portable-kb-open'))return;
  var o=displayOrientId();
  if(lastDisplayOrient==null){lastDisplayOrient=o;return;}
  if(o===lastDisplayOrient)return;
"""


def patch(text: str) -> str:
    reps = [
        (HIDE_OLD, HIDE_NEW),
        (FLIP_OLD, FLIP_NEW),
        (ORIENT_OLD, ORIENT_NEW),
        (CLAMP_OLD, CLAMP_NEW),
        (SIDES_OLD, SIDES_NEW),
        (HDR_OLD, HDR_NEW),
        (VV_OLD, VV_NEW),
        (RESIZE_OLD, RESIZE_NEW),
        (SYNC_OLD, SYNC_NEW),
    ]
    for old, new in reps:
        n = text.count(old)
        if n != 1:
            raise SystemExit(f"expected 1 occurrence of snippet, found {n}: {old[:80]!r}")
        text = text.replace(old, new, 1)
    if CSS_MARK not in text:
        raise SystemExit("missing </style></head>")
    if "fix-PORTABLE-SK-TOOLBAR" not in text:
        text = text.replace(CSS_MARK, CSS_ADD + CSS_MARK, 1)
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
