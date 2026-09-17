#!/usr/bin/env python3
"""Orientation display-mode defaults: landscape Sides, portrait Middle; per-orient picks.

Syncs the six catalog HTML/builder files. Does not strip existing agent logs.
"""
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


def add_indent(s, n=1):
    pad = " " * n
    return "\n".join((pad + line) if line.strip() else line for line in s.split("\n"))


def sub(text, old, new, label, optional=False):
    n = text.count(old)
    if n == 1:
        return text.replace(old, new, 1)
    if n > 1:
        raise SystemExit(f"{label}: {n} matches")
    if new in text:
        print(f"  skip {label} (already)")
        return text
    for i in range(1, 9):
        oldi, newi = add_indent(old, i), add_indent(new, i)
        ni = text.count(oldi)
        if ni == 1:
            return text.replace(oldi, newi, 1)
        if ni > 1:
            raise SystemExit(f"{label}: {ni} matches (indent {i})")
        if ni == 0 and newi in text:
            print(f"  skip {label} (already)")
            return text
    if optional:
        print(f"  skip {label}")
        return text
    raise SystemExit(f"{label}: not found")


PICK_OLD = r"""function displayPickKey(){return 'catalog-display-pick-'+(window.CATALOG_NS||'catalog');}
function displayIsMiddle(){return !!(document.body&&document.body.classList.contains('display-middle'));}
window.displayIsMiddle=displayIsMiddle;
"""

PICK_NEW = r"""function displayPickKey(orient){
  var ns=window.CATALOG_NS||'catalog';
  if(orient)return 'catalog-display-pick-'+ns+'-'+orient;
  return 'catalog-display-pick-'+ns;
}
function displayOrientId(){
  try{
    if(window.matchMedia&&window.matchMedia('(orientation:portrait)').matches)return 'portrait';
  }catch(err){}
  return 'landscape';
}
function displayModeOrientKey(orient){
  orient=orient||displayOrientId();
  return 'catalog-display-mode-'+(window.CATALOG_NS||'catalog')+'-'+orient;
}
function defaultDisplayForOrient(orient){
  orient=orient||displayOrientId();
  return orient==='portrait'?'middle':'sides';
}
function normalizeDisplayMode(m){
  if(m==='middle'||m==='sides')return m;
  if(m==='upper'||m==='fs')return 'sides';
  return '';
}
function logDisplayOrient(hid,loc,msg,extra){
  // #region agent log
  try{
    extra=extra||{};
    extra.orient=typeof displayOrientId==='function'?displayOrientId():'';
    extra.display=typeof currentDisplay!=='undefined'?currentDisplay:'';
    extra.vw=window.innerWidth;extra.vh=window.innerHeight;
    extra.portrait=!!(window.matchMedia&&window.matchMedia('(orientation:portrait)').matches);
    extra.portable=!!window.CATALOG_PORTABLE;
    extra.desk=typeof displayIsDesktop==='function'?displayIsDesktop():null;
    extra.cls={
      sides:document.body.classList.contains('display-sides'),
      middle:document.body.classList.contains('display-middle')
    };
    extra.lastOrient=typeof lastDisplayOrient!=='undefined'?lastDisplayOrient:null;
    fetch('http://127.0.0.1:7529/ingest/1cf46354-1d61-4c80-bd72-a340f1db1b51',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'f491c2'},body:JSON.stringify({sessionId:'f491c2',runId:'display-orient',hypothesisId:hid,location:loc,message:msg,data:extra,timestamp:Date.now()})}).catch(function(){});
    fetch('http://127.0.0.1:7529/ingest/1cf46354-1d61-4c80-bd72-a340f1db1b51',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'c00e3e'},body:JSON.stringify({sessionId:'c00e3e',runId:'display-orient',hypothesisId:hid,location:loc,message:msg,data:extra,timestamp:Date.now()})}).catch(function(){});
  }catch(err){}
  // #endregion
}
function readDisplayOrientPick(orient){
  orient=orient||displayOrientId();
  try{
    var flag=localStorage.getItem(displayPickKey(orient));
    var stored=normalizeDisplayMode(localStorage.getItem(displayModeOrientKey(orient))||'');
    if(flag==='1'&&stored)return stored;
    var asMode=normalizeDisplayMode(flag);
    if(asMode)return asMode;
  }catch(err){}
  return null;
}
function writeDisplayOrientPick(mode,orient){
  orient=orient||displayOrientId();
  mode=normalizeDisplayMode(mode)||defaultDisplayForOrient(orient);
  try{
    localStorage.setItem(displayPickKey(orient),'1');
    localStorage.setItem(displayModeOrientKey(orient),mode);
    localStorage.setItem(displayPickKey(),'1');
  }catch(err){}
  logDisplayOrient('H-O2','writeDisplayOrientPick','pick',{mode:mode,orient:orient,pickKey:displayPickKey(orient),modeKey:displayModeOrientKey(orient)});
}
function resolveDisplayForOrient(orient){
  orient=orient||displayOrientId();
  var picked=readDisplayOrientPick(orient);
  if(picked)return picked;
  return defaultDisplayForOrient(orient);
}
var lastDisplayOrient=null;
function syncDisplayForOrientation(){
  var o=displayOrientId();
  if(lastDisplayOrient==null){lastDisplayOrient=o;return;}
  if(o===lastDisplayOrient)return;
  var next=resolveDisplayForOrient(o);
  lastDisplayOrient=o;
  logDisplayOrient('H-O3','syncDisplayForOrientation','orient-change',{from:typeof currentDisplay!=='undefined'?currentDisplay:'',next:next,orient:o});
  if(typeof setDisplayMode==='function')setDisplayMode(next);
}
function displayIsMiddle(){return !!(document.body&&document.body.classList.contains('display-middle'));}
window.displayIsMiddle=displayIsMiddle;
window.displayPickKey=displayPickKey;
window.displayOrientId=displayOrientId;
window.displayModeOrientKey=displayModeOrientKey;
window.defaultDisplayForOrient=defaultDisplayForOrient;
window.readDisplayOrientPick=readDisplayOrientPick;
window.writeDisplayOrientPick=writeDisplayOrientPick;
window.resolveDisplayForOrient=resolveDisplayForOrient;
window.syncDisplayForOrientation=syncDisplayForOrientation;
window.logDisplayOrient=logDisplayOrient;
"""

SET_OLD = r"""  if(opts.pick){try{localStorage.setItem(typeof displayPickKey==='function'?displayPickKey():('catalog-display-pick-'+(window.CATALOG_NS||'catalog')),'1');}catch(err){}}
  if(mode!=='upper'&&mode!=='sides'&&mode!=='fs'&&mode!=='middle')mode='sides';
  if(mode==='upper'||mode==='fs')mode='sides';
  var persistDisplay=mode;
  if(mode==='middle')mode='sides';
"""

SET_NEW = r"""  if(mode!=='upper'&&mode!=='sides'&&mode!=='fs'&&mode!=='middle')mode='sides';
  if(mode==='upper'||mode==='fs')mode='sides';
  var persistDisplay=mode;
  if(opts.pick){
    try{
      if(typeof writeDisplayOrientPick==='function')writeDisplayOrientPick(persistDisplay);
      else localStorage.setItem(typeof displayPickKey==='function'?displayPickKey():('catalog-display-pick-'+(window.CATALOG_NS||'catalog')),'1');
    }catch(err){}
  }
  if(mode==='middle')mode='sides';
  try{lastDisplayOrient=typeof displayOrientId==='function'?displayOrientId():lastDisplayOrient;}catch(err){}
"""

INIT_OLD = r"""  var m='sides';
  var picked=false;
  try{picked=localStorage.getItem(typeof displayPickKey==='function'?displayPickKey():('catalog-display-pick-'+(window.CATALOG_NS||'catalog')))==='1';m=localStorage.getItem(DISPLAY_KEY)||'sides';}catch(err){}
  if(m!=='upper'&&m!=='sides'&&m!=='fs'&&m!=='middle')m='sides';
  if(m==='upper'||m==='fs')m='sides';
  if(!picked){m=(window.matchMedia&&window.matchMedia('(orientation:portrait)').matches)?'middle':'sides';}
  // No mobile coercion — Sides works on all screen sizes via CSS; portrait defaults to Middle until the user picks
  setDisplayMode(m);
"""

INIT_NEW = r"""  var m=(typeof resolveDisplayForOrient==='function')?resolveDisplayForOrient():((window.matchMedia&&window.matchMedia('(orientation:portrait)').matches)?'middle':'sides');
  if(m!=='upper'&&m!=='sides'&&m!=='fs'&&m!=='middle')m='sides';
  if(m==='upper'||m==='fs')m='sides';
  // Landscape defaults to Sides, portrait to Middle. Explicit picks are stored per orientation.
  setDisplayMode(m);
  try{lastDisplayOrient=typeof displayOrientId==='function'?displayOrientId():lastDisplayOrient;}catch(err){}
  if(typeof logDisplayOrient==='function')logDisplayOrient('H-O1','init','display-orient-init',{mode:m,resolved:typeof resolveDisplayForOrient==='function'?resolveDisplayForOrient():m,pickL:typeof readDisplayOrientPick==='function'?readDisplayOrientPick('landscape'):null,pickP:typeof readDisplayOrientPick==='function'?readDisplayOrientPick('portrait'):null});
"""

RESIZE_OLD = r"""    if(typeof applySidesCols==='function')applySidesCols();
    if(currentDisplay==='fs'&&typeof applyDualLayout==='function')applyDualLayout();
  },{passive:true});
"""

RESIZE_NEW = r"""    if(typeof applySidesCols==='function')applySidesCols();
    if(currentDisplay==='fs'&&typeof applyDualLayout==='function')applyDualLayout();
    if(typeof syncDisplayForOrientation==='function')syncDisplayForOrientation();
  },{passive:true});
"""

LISTEN_OLD = r"""  // fix-SIDES-ONLY: no mode coercion on viewport/orientation change — CSS handles portrait/mobile Sides layouts
"""

LISTEN_NEW = r"""  // Orientation change applies that orientation's default (or saved pick). Width-only resizes do not coerce.
  window.addEventListener('orientationchange',function(){setTimeout(function(){if(typeof syncDisplayForOrientation==='function')syncDisplayForOrientation();},0);});
  if(window.matchMedia){
    var mqOrient=window.matchMedia('(orientation: portrait)');
    function onOrientMq(){if(typeof syncDisplayForOrientation==='function')syncDisplayForOrientation();}
    if(mqOrient.addEventListener)mqOrient.addEventListener('change',onOrientMq);
    else if(mqOrient.addListener)mqOrient.addListener(onOrientMq);
  }
"""


def patch(text, path):
    if "function resolveDisplayForOrient" in text and "function syncDisplayForOrientation" in text:
        print(f"skip already patched: {path}")
        return text

    c00 = text.count("sessionId:'c00e3e'")
    f49 = text.count("sessionId:'f491c2'")
    regions = text.count("// #region agent log")

    text = sub(text, PICK_OLD, PICK_NEW, "orient-helpers")
    text = sub(text, SET_OLD, SET_NEW, "setDisplay-pick")
    text = sub(text, INIT_OLD, INIT_NEW, "init-default")
    text = sub(text, RESIZE_OLD, RESIZE_NEW, "resize-sync")
    text = sub(text, LISTEN_OLD, LISTEN_NEW, "orient-listen")

    if "function resolveDisplayForOrient" not in text:
        raise SystemExit(f"{path.name}: missing resolveDisplayForOrient")
    if "function syncDisplayForOrientation" not in text:
        raise SystemExit(f"{path.name}: missing syncDisplayForOrientation")
    if "catalog-display-mode-'+(window.CATALOG_NS||'catalog')+'-'+orient" not in text:
        raise SystemExit(f"{path.name}: missing per-orient mode key")
    if "if(!picked){m=(window.matchMedia&&window.matchMedia('(orientation:portrait)').matches)?'middle':'sides';}" in text:
        raise SystemExit(f"{path.name}: still uses global pick for all orientations")
    if text.count("sessionId:'f491c2'") < f49:
        raise SystemExit(f"{path.name}: lost f491c2 logs")
    if text.count("// #region agent log") < regions:
        raise SystemExit(f"{path.name}: lost agent log regions")
    if path.name == "DS-CATALOG.html":
        if "function dbgIndexAc" not in text:
            raise SystemExit(f"{path.name}: lost dbgIndexAc")
        if text.count("sessionId:'c00e3e'") < c00:
            raise SystemExit(f"{path.name}: lost c00e3e logs")
    elif c00 and text.count("sessionId:'c00e3e'") < c00:
        raise SystemExit(f"{path.name}: lost c00e3e logs")
    return text


def main():
    for path in FILES:
        if not path.exists():
            raise SystemExit(f"missing {path}")
        text = path.read_text(encoding="utf-8")
        new = patch(text, path)
        if new != text:
            path.write_text(new, encoding="utf-8")
            print(f"patched {path}")
        else:
            print(f"unchanged {path}")


if __name__ == "__main__":
    main()
