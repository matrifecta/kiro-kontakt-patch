#!/usr/bin/env python3
"""Tighten per-mode isolation and keep Edit/Pin visible when Keywords is closed."""
from pathlib import Path
import shutil

KIRO = Path("/home/phnx/KIRO/.kiro/specs/kontakt-workspace-drive-dirty-fix/artifacts")
WS = Path("/home/phnx/kiro-kontakt-patch/kiro/specs/kontakt-workspace-drive-dirty-fix/artifacts")
PUB = Path("/home/phnx/kiro-kontakt-patch/public/catalogs")

OLD_SNAP = """function snapshotLiveToMode(mode){
  mode=mode||displayModeSlot();
  var patch={};
  try{
    if(mode==='sides'){
      var lw=parseInt(getComputedStyle(document.body).getPropertyValue('--sides-lw'),10)||0;
      var rw=parseInt(getComputedStyle(document.body).getPropertyValue('--sides-rw'),10)||0;
      if(lw)patch.lw=lw;
      if(rw)patch.rw=rw;
      patch.pinned=!!sidesPinned;
    }else{
      try{patch.chromeH=localStorage.getItem(liveLayoutKey('catalog-search-height-')+'-l')||undefined;}catch(err){}
      try{patch.splitH=localStorage.getItem(liveLayoutKey('catalog-search-split-h-'))||undefined;}catch(err){}
      try{patch.splitV=localStorage.getItem(liveLayoutKey('catalog-search-split-v-'))||undefined;}catch(err){}
      try{patch.acH=localStorage.getItem(liveLayoutKey('catalog-search-ac-height-'))||undefined;}catch(err){}
      try{patch.kwH=localStorage.getItem(liveLayoutKey('catalog-keywords-shade-height-'))||undefined;}catch(err){}
      if(mode==='fs'){
        patch.menu=document.body.classList.contains('kw-fs-open')&&!document.body.classList.contains('ac-fs-open')?'keywords':(document.body.classList.contains('ac-fs-open')&&!document.body.classList.contains('kw-fs-open')?'search':'both');
        var acVar=getComputedStyle(document.documentElement).getPropertyValue('--fs-ac-h').trim();
        var kwVar=getComputedStyle(document.documentElement).getPropertyValue('--fs-kw-h').trim();
        var avail=Math.max(160,(window.innerHeight||800)-56);
        if(acVar&&acVar.indexOf('px')>0)patch.acH=String(parseFloat(acVar)/avail);
        if(kwVar&&kwVar.indexOf('px')>0)patch.kwH=String(parseFloat(kwVar)/avail);
      }
    }
  }catch(err){}
  writeModeSlot(patch,mode);
  return patch;
}
function applyModeSlot(mode){
  mode=mode||displayModeSlot();
  var slot=readModeSlot(mode);
  try{
    if(mode==='sides'){
      if(slot.lw&&slot.rw)localStorage.setItem(SIDES_KEY,JSON.stringify({lw:slot.lw,rw:slot.rw}));
      if(typeof slot.pinned==='boolean'){
        sidesPinned=!!slot.pinned;
        localStorage.setItem(SIDES_KEY+'-pin',sidesPinned?'1':'0');
      }
    }else{
      if(slot.chromeH!=null)localStorage.setItem(liveLayoutKey('catalog-search-height-')+'-l',String(slot.chromeH));
      if(slot.splitH!=null)localStorage.setItem(liveLayoutKey('catalog-search-split-h-'),String(slot.splitH));
      if(slot.splitV!=null)localStorage.setItem(liveLayoutKey('catalog-search-split-v-'),String(slot.splitV));
      if(slot.acH!=null)localStorage.setItem(liveLayoutKey('catalog-search-ac-height-'),String(slot.acH));
      if(slot.kwH!=null)localStorage.setItem(liveLayoutKey('catalog-keywords-shade-height-'),String(slot.kwH));
    }
  }catch(err){}
"""

NEW_SNAP = """function snapshotLiveToMode(mode){
  mode=mode||displayModeSlot();
  var patch={};
  try{
    if(mode==='sides'){
      var lw=parseInt(getComputedStyle(document.body).getPropertyValue('--sides-lw'),10)||0;
      var rw=parseInt(getComputedStyle(document.body).getPropertyValue('--sides-rw'),10)||0;
      if(lw)patch.lw=lw;
      if(rw)patch.rw=rw;
      patch.pinned=!!sidesPinned;
    }else if(mode==='fs'){
      patch.menu=document.body.classList.contains('kw-fs-open')&&!document.body.classList.contains('ac-fs-open')?'keywords':(document.body.classList.contains('ac-fs-open')&&!document.body.classList.contains('kw-fs-open')?'search':'both');
      var acVar=getComputedStyle(document.documentElement).getPropertyValue('--fs-ac-h').trim();
      var kwVar=getComputedStyle(document.documentElement).getPropertyValue('--fs-kw-h').trim();
      var avail=Math.max(160,(window.innerHeight||800)-56);
      if(acVar&&acVar.indexOf('px')>0)patch.acH=String(parseFloat(acVar)/avail);
      if(kwVar&&kwVar.indexOf('px')>0)patch.kwH=String(parseFloat(kwVar)/avail);
    }else{
      try{patch.chromeH=localStorage.getItem(liveLayoutKey('catalog-search-height-')+'-l')||undefined;}catch(err){}
      try{patch.splitH=localStorage.getItem(liveLayoutKey('catalog-search-split-h-'))||undefined;}catch(err){}
      try{patch.splitV=localStorage.getItem(liveLayoutKey('catalog-search-split-v-'))||undefined;}catch(err){}
      try{patch.acH=localStorage.getItem(liveLayoutKey('catalog-search-ac-height-'))||undefined;}catch(err){}
      try{patch.kwH=localStorage.getItem(liveLayoutKey('catalog-keywords-shade-height-'))||undefined;}catch(err){}
    }
  }catch(err){}
  writeModeSlot(patch,mode);
  return patch;
}
function applyModeSlot(mode){
  mode=mode||displayModeSlot();
  var slot=readModeSlot(mode);
  try{
    function setOrClear(key,val){
      if(val==null||val==='')localStorage.removeItem(key);
      else localStorage.setItem(key,String(val));
    }
    if(mode==='sides'){
      if(slot.lw&&slot.rw)localStorage.setItem(SIDES_KEY,JSON.stringify({lw:slot.lw,rw:slot.rw}));
      if(typeof slot.pinned==='boolean'){
        sidesPinned=!!slot.pinned;
        localStorage.setItem(SIDES_KEY+'-pin',sidesPinned?'1':'0');
      }
    }else{
      setOrClear(liveLayoutKey('catalog-search-height-')+'-l', slot.chromeH);
      setOrClear(liveLayoutKey('catalog-search-split-h-'), slot.splitH);
      setOrClear(liveLayoutKey('catalog-search-split-v-'), slot.splitV);
      setOrClear(liveLayoutKey('catalog-search-ac-height-'), slot.acH);
      setOrClear(liveLayoutKey('catalog-keywords-shade-height-'), slot.kwH);
    }
  }catch(err){}
"""

OLD_CSS = " .filter-top #layoutEditBtn,.filter-top #modePinBtn{flex:0 0 auto}\n"
NEW_CSS = (
    " .filter-top #layoutEditBtn,.filter-top #modePinBtn{flex:0 0 auto;display:inline-flex!important}\n"
    " .filter-wrap:not(.open)>.filter-top #layoutEditBtn,.filter-wrap:not(.open)>.filter-top #modePinBtn{display:inline-flex!important}\n"
)


def patch(text, name):
    if OLD_SNAP not in text:
        if "function setOrClear(key,val)" in text:
            print(f"  skip snap {name}")
        else:
            raise SystemExit(f"MISSING snap in {name}")
    else:
        text = text.replace(OLD_SNAP, NEW_SNAP, 1)
    if OLD_CSS not in text:
        if "filter-wrap:not(.open)>.filter-top #layoutEditBtn" in text:
            print(f"  skip css {name}")
        else:
            raise SystemExit(f"MISSING css in {name}")
    else:
        text = text.replace(OLD_CSS, NEW_CSS, 1)
    if name.endswith(".html") or name.endswith(".sh"):
        if "function hideSearchAc" not in text:
            raise SystemExit(f"TRUNCATED {name}")
    if name.endswith(".html") and "</html>" not in text:
        raise SystemExit(f"TRUNCATED html {name}")
    return text


def main():
    for name in ("build-ds-catalog-html.sh", "build-kontakt-catalog-html.sh"):
        src = KIRO / name
        out = patch(src.read_text(encoding="utf-8"), name)
        src.write_text(out, encoding="utf-8")
        shutil.copy2(src, WS / name)
        print("patched", name)

    for path in [
        PUB / "DS-CATALOG.html",
        PUB / "DS-CATALOG-portable.html",
        PUB / "KONTAKT-CATALOG.html",
        PUB / "KONTAKT-CATALOG-portable.html",
        WS / "DS-CATALOG.html",
        WS / "DS-CATALOG-portable.html",
        WS / "KONTAKT-CATALOG.html",
        WS / "KONTAKT-CATALOG-portable.html",
    ]:
        if not path.exists():
            continue
        path.write_text(patch(path.read_text(encoding="utf-8"), path.name), encoding="utf-8")
        print("patched", path.name)


if __name__ == "__main__":
    main()
