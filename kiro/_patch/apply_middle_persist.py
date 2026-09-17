#!/usr/bin/env python3
"""Persist + pin-safe Middle splitters (Search|Keywords, menus|content). Sync six files."""
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


MIDDLE_HELPERS_OLD = r"""function middleLayoutDefaults(){
  var hdr=document.querySelector('.catalog-header');
  var top=hdr?Math.round(hdr.getBoundingClientRect().height):56;
  var availW=Math.max(280,window.innerWidth||900);
  var availH=Math.max(220,(window.innerHeight||800)-top);
  return {menuH:Math.round(availH*0.38),lw:Math.round(availW*0.5),availW:availW,availH:availH};
}
function parseMiddleStored(key,fallback){
  try{
    var v=localStorage.getItem(key);
    if(!v)return fallback;
    var n=parseInt(v,10);
    return (isFinite(n)&&n>0)?n:fallback;
  }catch(err){return fallback;}
}
"""

MIDDLE_HELPERS_NEW = r"""function middleLayoutDefaults(){
  var hdr=document.querySelector('.catalog-header');
  var top=hdr?Math.round(hdr.getBoundingClientRect().height):56;
  var availW=Math.max(280,window.innerWidth||900);
  var availH=Math.max(220,(window.innerHeight||800)-top);
  var minL=Math.max(148,Math.min(220,Math.round(availW*0.24)));
  var minR=Math.max(148,Math.min(220,Math.round(availW*0.24)));
  var minH=Math.max(132,Math.min(200,Math.round(availH*0.20)));
  var minC=Math.max(120,Math.min(200,Math.round(availH*0.18)));
  return {menuH:Math.round(availH*0.38),lw:Math.round(availW*0.5),availW:availW,availH:availH,minL:minL,minR:minR,minH:minH,minC:minC};
}
function middleLwKey(){return (typeof liveLayoutKey==='function'?liveLayoutKey('catalog-middle-lw-'):('catalog-middle-lw-'+(window.CATALOG_NS||'catalog')));}
function middleMhKey(){return (typeof liveLayoutKey==='function'?liveLayoutKey('catalog-middle-menu-h-'):('catalog-middle-menu-h-'+(window.CATALOG_NS||'catalog')));}
function parseMiddleStored(key,fallback){
  try{
    var v=localStorage.getItem(key);
    if(!v){
      if(key===middleLwKey())v=localStorage.getItem('catalog-middle-lw');
      else if(key===middleMhKey())v=localStorage.getItem('catalog-middle-menu-h');
    }
    if(!v)return fallback;
    var n=parseInt(v,10);
    return (isFinite(n)&&n>0)?n:fallback;
  }catch(err){return fallback;}
}
function clampMiddleLw(val,d){
  d=d||middleLayoutDefaults();
  val=Number(val);if(!isFinite(val))val=d.lw;
  return Math.round(Math.max(d.minL,Math.min(d.availW-d.minR,val)));
}
function clampMiddleMh(val,d){
  d=d||middleLayoutDefaults();
  val=Number(val);if(!isFinite(val))val=d.menuH;
  return Math.round(Math.max(d.minH,Math.min(d.availH-d.minC,val)));
}
function writeMiddleLayout(lw,mh){
  if(typeof sidesPinned!=='undefined'&&sidesPinned)return;
  if(typeof modeLayoutPinned==='function'&&modeLayoutPinned())return;
  var d=middleLayoutDefaults();
  if(lw!=null)lw=clampMiddleLw(lw,d);
  if(mh!=null)mh=clampMiddleMh(mh,d);
  try{
    if(lw!=null)localStorage.setItem(middleLwKey(),lw+'px');
    if(mh!=null)localStorage.setItem(middleMhKey(),mh+'px');
  }catch(err){}
  var patch={};
  if(lw!=null)patch.middleLw=lw;
  if(mh!=null)patch.middleMh=mh;
  if(Object.keys(patch).length&&typeof writeModeSlot==='function')writeModeSlot(patch,'sides');
  if(typeof snapshotCurrentLayoutBucket==='function'&&displayIsMiddle()){
    var bid=(typeof layoutBucketId==='function')?layoutBucketId():'middle-sck';
    snapshotCurrentLayoutBucket(bid);
  }
  logMiddleLayout('H-M3','writeMiddleLayout','save',{lw:lw,mh:mh,keyLw:middleLwKey(),keyMh:middleMhKey()});
}
"""

APPLY_OLD = r"""function applyMiddleLayout(){
  if(!displayIsMiddle())return;
  document.body.classList.remove('sides-portrait-flip');
  var d=middleLayoutDefaults();
  var mh=parseMiddleStored('catalog-middle-menu-h',d.menuH);
  var lw=parseMiddleStored('catalog-middle-lw',d.lw);
  mh=Math.max(96,Math.min(d.availH-80,mh));
  lw=Math.max(110,Math.min(d.availW-110,lw));
  document.documentElement.style.setProperty('--middle-menu-h',mh+'px');
  document.documentElement.style.setProperty('--middle-lw',lw+'px');
  document.documentElement.style.setProperty('--middle-rw',Math.max(110,d.availW-lw)+'px');
  var fw=document.getElementById('filterWrap');
  if(fw&&!document.body.classList.contains('kw-chrome-collapsed')){
    fw.classList.add('open');document.body.classList.add('kw-open');
  }
  logMiddleLayout('H-M1','applyMiddleLayout','apply',{defH:d.menuH,defW:d.lw,mh:mh,lw:lw});
}
"""

APPLY_NEW = r"""function applyMiddleLayout(){
  if(!displayIsMiddle())return;
  document.body.classList.remove('sides-portrait-flip');
  var d=middleLayoutDefaults();
  var slot=(typeof readModeSlot==='function'?readModeSlot('sides'):{})||{};
  var bid=(typeof layoutBucketId==='function')?layoutBucketId():'middle-sck';
  var buck=(typeof sidesBuckets==='function'&&sidesBuckets()[bid])||{};
  var lw=buck.mlw||slot.middleLw||parseMiddleStored(middleLwKey(),d.lw);
  var mh=buck.mmh||slot.middleMh||parseMiddleStored(middleMhKey(),d.menuH);
  lw=clampMiddleLw(lw,d);
  mh=clampMiddleMh(mh,d);
  document.documentElement.style.setProperty('--middle-menu-h',mh+'px');
  document.documentElement.style.setProperty('--middle-lw',lw+'px');
  document.documentElement.style.setProperty('--middle-rw',Math.max(d.minR,d.availW-lw)+'px');
  var fw=document.getElementById('filterWrap');
  if(fw&&!document.body.classList.contains('kw-chrome-collapsed')){
    fw.classList.add('open');document.body.classList.add('kw-open');
  }
  logMiddleLayout('H-M1','applyMiddleLayout','apply',{defH:d.menuH,defW:d.lw,mh:mh,lw:lw,bid:bid});
}
"""

PLACE_OLD = r"""function placeMiddleHandles(){
  var split=document.getElementById('searchSplit');
  var sep=document.getElementById('dualFsSep');
  var ch=document.getElementById('searchChrome');
  var fw=document.getElementById('filterWrap');
  var editing=document.body.classList.contains('layout-edit');
  var hidden=document.body.classList.contains('search-chrome-collapsed');
  var kwHid=document.body.classList.contains('kw-chrome-collapsed');
"""

PLACE_NEW = r"""function placeMiddleHandles(){
  var split=document.getElementById('searchSplit');
  var sep=document.getElementById('dualFsSep');
  var ch=document.getElementById('searchChrome');
  var fw=document.getElementById('filterWrap');
  var editing=document.body.classList.contains('layout-edit');
  var pinned=!!(typeof sidesPinned!=='undefined'&&sidesPinned)||(typeof modeLayoutPinned==='function'&&modeLayoutPinned())||document.body.classList.contains('mode-layout-pinned')||document.body.classList.contains('sides-pinned');
  var hidden=document.body.classList.contains('search-chrome-collapsed');
  var kwHid=document.body.classList.contains('kw-chrome-collapsed');
  if(pinned)editing=false;
"""

EXPORT_OLD = r"""window.middleLayoutDefaults=middleLayoutDefaults;
window.applyMiddleLayout=applyMiddleLayout;
window.placeMiddleHandles=placeMiddleHandles;
window.logMiddleLayout=logMiddleLayout;
"""

EXPORT_NEW = r"""window.middleLayoutDefaults=middleLayoutDefaults;
window.applyMiddleLayout=applyMiddleLayout;
window.placeMiddleHandles=placeMiddleHandles;
window.logMiddleLayout=logMiddleLayout;
window.writeMiddleLayout=writeMiddleLayout;
window.middleLwKey=middleLwKey;
window.middleMhKey=middleMhKey;
window.clampMiddleLw=clampMiddleLw;
window.clampMiddleMh=clampMiddleMh;
"""

DRAG_MOVE_OLD = r"""    if(drag.middle){
      var dM=drag.def;
      if(drag.which==='split'){
        var mhM=Math.max(96,Math.min(dM.availH-80,drag.mh+(e.clientY-drag.y)));
        document.documentElement.style.setProperty('--middle-menu-h',mhM+'px');
        try{localStorage.setItem('catalog-middle-menu-h',mhM+'px');}catch(ex){}
      }else{
        var nlwM=Math.max(110,Math.min(dM.availW-110,drag.lw+(e.clientX-drag.x)));
        document.documentElement.style.setProperty('--middle-lw',nlwM+'px');
        document.documentElement.style.setProperty('--middle-rw',Math.max(110,dM.availW-nlwM)+'px');
        try{localStorage.setItem('catalog-middle-lw',nlwM+'px');}catch(ex){}
      }
      if(typeof placeSidesHandles==='function')placeSidesHandles();
      return;
    }
"""

DRAG_MOVE_NEW = r"""    if(drag.middle){
      var dM=drag.def;
      if(drag.which==='split'){
        var mhM=clampMiddleMh(drag.mh+(e.clientY-drag.y),dM);
        document.documentElement.style.setProperty('--middle-menu-h',mhM+'px');
      }else{
        var nlwM=clampMiddleLw(drag.lw+(e.clientX-drag.x),dM);
        document.documentElement.style.setProperty('--middle-lw',nlwM+'px');
        document.documentElement.style.setProperty('--middle-rw',Math.max(dM.minR,dM.availW-nlwM)+'px');
      }
      if(typeof placeSidesHandles==='function')placeSidesHandles();
      return;
    }
"""

DRAG_UP_OLD = r"""    if(drag.middle){
      var mlwU=parseInt(getComputedStyle(document.documentElement).getPropertyValue('--middle-lw'),10)||0;
      var mmhU=parseInt(getComputedStyle(document.documentElement).getPropertyValue('--middle-menu-h'),10)||0;
      try{localStorage.setItem('catalog-middle-lw',mlwU+'px');localStorage.setItem('catalog-middle-menu-h',mmhU+'px');}catch(ex){}
      drag=null;
      if(typeof logMiddleLayout==='function')logMiddleLayout('H-M2','sides-handle','middle-up',{lw:mlwU,mh:mmhU});
      return;
    }
"""

DRAG_UP_NEW = r"""    if(drag.middle){
      var mlwU=parseInt(getComputedStyle(document.documentElement).getPropertyValue('--middle-lw'),10)||0;
      var mmhU=parseInt(getComputedStyle(document.documentElement).getPropertyValue('--middle-menu-h'),10)||0;
      if(typeof writeMiddleLayout==='function')writeMiddleLayout(mlwU,mmhU);
      drag=null;
      if(typeof logMiddleLayout==='function')logMiddleLayout('H-M2','sides-handle','middle-up',{lw:mlwU,mh:mmhU});
      return;
    }
"""

CSS_OLD = r"""body.display-sides.display-middle.layout-edit #searchSplit,
body.display-sides.display-middle.layout-edit #dualFsSep{display:block!important;pointer-events:auto!important}
"""

CSS_NEW = r"""body.display-sides.display-middle.layout-edit #searchSplit,
body.display-sides.display-middle.layout-edit #dualFsSep{display:block!important;pointer-events:auto!important;z-index:80!important}
body.display-sides.display-middle.layout-edit #searchSplit{
  cursor:ns-resize!important;width:auto!important;min-width:0!important;max-width:none!important;height:12px!important;min-height:12px!important;max-height:12px!important
}
body.display-sides.display-middle.layout-edit #dualFsSep{
  cursor:ew-resize!important;width:12px!important;min-width:12px!important;max-width:12px!important;height:auto!important
}
body.display-sides.display-middle.layout-edit #searchSplit::before,
body.display-sides.display-middle.layout-edit #dualFsSep::before{
  content:'';display:block;background:var(--border,rgba(128,128,128,0.5));border-radius:2px;
  opacity:.7;position:absolute;top:50%;left:50%;transform:translate(-50%,-50%)
}
body.display-sides.display-middle.layout-edit #searchSplit::before{width:28px;height:2px}
body.display-sides.display-middle.layout-edit #dualFsSep::before{width:2px;height:28px}
body.display-sides.display-middle.mode-layout-pinned.layout-edit #searchSplit,
body.display-sides.display-middle.mode-layout-pinned.layout-edit #dualFsSep,
body.display-sides.display-middle.sides-pinned.layout-edit #searchSplit,
body.display-sides.display-middle.sides-pinned.layout-edit #dualFsSep{cursor:default!important;pointer-events:none!important}
"""


def patch(text, path):
    if "function writeMiddleLayout" in text and "middleLwKey" in text:
        print(f"skip already persisted: {path}")
        return text

    text = sub(text, MIDDLE_HELPERS_OLD, MIDDLE_HELPERS_NEW, "middle-helpers")
    text = sub(text, APPLY_OLD, APPLY_NEW, "apply-middle")
    text = sub(text, PLACE_OLD, PLACE_NEW, "place-pin")
    text = sub(text, EXPORT_OLD, EXPORT_NEW, "exports")
    text = sub(text, DRAG_MOVE_OLD, DRAG_MOVE_NEW, "drag-move")
    text = sub(text, DRAG_UP_OLD, DRAG_UP_NEW, "drag-up")
    text = sub(text, CSS_OLD, CSS_NEW, "handle-css")

    text = sub(
        text,
        "function layoutOrientId(){\n  return (typeof isPortraitDesktopSides==='function'&&isPortraitDesktopSides())?'portrait':'wide';\n}\nfunction layoutBucketId(){\n  if(layoutOrientId()!=='portrait')return 'wide';",
        "function layoutOrientId(){\n  if(typeof displayIsMiddle==='function'?displayIsMiddle():(document.body&&document.body.classList.contains('display-middle')))return 'middle';\n  return (typeof isPortraitDesktopSides==='function'&&isPortraitDesktopSides())?'portrait':'wide';\n}\nfunction layoutBucketId(){\n  var o=layoutOrientId();\n  if(o==='middle')return 'middle-'+((typeof liveLayoutScopeId==='function')?liveLayoutScopeId():'sck');\n  if(o!=='portrait')return 'wide';",
        "bucket-id",
    )

    text = sub(
        text,
        "  if(id==='wide'){\n    var lw=parseInt(getComputedStyle(document.body).getPropertyValue('--sides-lw'),10)||0;\n    var rw=parseInt(getComputedStyle(document.body).getPropertyValue('--sides-rw'),10)||0;\n    if(!searchHid&&lw>40)patch.lw=lw;\n    if(!kwHid&&rw>40)patch.rw=rw;\n  }else{\n    var plw=parseInt(getComputedStyle(document.documentElement).getPropertyValue('--portrait-lw'),10)||0;",
        "  if(id==='wide'){\n    var lw=parseInt(getComputedStyle(document.body).getPropertyValue('--sides-lw'),10)||0;\n    var rw=parseInt(getComputedStyle(document.body).getPropertyValue('--sides-rw'),10)||0;\n    if(!searchHid&&lw>40)patch.lw=lw;\n    if(!kwHid&&rw>40)patch.rw=rw;\n  }else if(String(id).indexOf('middle-')===0){\n    var mlw=parseInt(getComputedStyle(document.documentElement).getPropertyValue('--middle-lw'),10)||0;\n    var mmh=parseInt(getComputedStyle(document.documentElement).getPropertyValue('--middle-menu-h'),10)||0;\n    if(mlw>40)patch.mlw=mlw;\n    if(mmh>40)patch.mmh=mmh;\n  }else{\n    var plw=parseInt(getComputedStyle(document.documentElement).getPropertyValue('--portrait-lw'),10)||0;",
        "snap-bucket-middle",
    )

    text = sub(
        text,
        "  if(id==='wide'){\n    if(patch.lw)out.lw=patch.lw;\n    if(patch.rw)out.rw=patch.rw;\n    try{if(patch.lw&&patch.rw)localStorage.setItem(SIDES_KEY,JSON.stringify({lw:patch.lw,rw:patch.rw}));}catch(eW){}\n  }",
        "  if(id==='wide'){\n    if(patch.lw)out.lw=patch.lw;\n    if(patch.rw)out.rw=patch.rw;\n    try{if(patch.lw&&patch.rw)localStorage.setItem(SIDES_KEY,JSON.stringify({lw:patch.lw,rw:patch.rw}));}catch(eW){}\n  }else if(String(id).indexOf('middle-')===0){\n    if(patch.mlw)out.middleLw=patch.mlw;\n    if(patch.mmh)out.middleMh=patch.mmh;\n  }",
        "snap-out-middle",
    )

    text = sub(
        text,
        "  if(id==='wide'){\n    if(b.lw)document.body.style.setProperty('--sides-lw',parseInt(b.lw,10)+'px');\n    if(b.rw)document.body.style.setProperty('--sides-rw',parseInt(b.rw,10)+'px');\n  }else{",
        "  if(id==='wide'){\n    if(b.lw)document.body.style.setProperty('--sides-lw',parseInt(b.lw,10)+'px');\n    if(b.rw)document.body.style.setProperty('--sides-rw',parseInt(b.rw,10)+'px');\n  }else if(String(id).indexOf('middle-')===0){\n    if(b.mlw)document.documentElement.style.setProperty('--middle-lw',parseInt(b.mlw,10)+'px');\n    if(b.mmh)document.documentElement.style.setProperty('--middle-menu-h',parseInt(b.mmh,10)+'px');\n    if(b.mlw){\n      var dMid=typeof middleLayoutDefaults==='function'?middleLayoutDefaults():{availW:window.innerWidth||900,minR:148};\n      document.documentElement.style.setProperty('--middle-rw',Math.max(dMid.minR||148,(dMid.availW||window.innerWidth)-parseInt(b.mlw,10))+'px');\n    }\n  }else{",
        "apply-bucket-middle",
    )

    text = sub(
        text,
        "      if(ixSnap){patch.indexEmbed=ixSnap.classList.contains('is-embedded');patch.indexCollapsed=ixSnap.classList.contains('is-collapsed');}\n      patch.pinned=!!sidesPinned;",
        "      if(ixSnap){patch.indexEmbed=ixSnap.classList.contains('is-embedded');patch.indexCollapsed=ixSnap.classList.contains('is-collapsed');}\n      patch.pinned=!!sidesPinned;\n      if(typeof displayIsMiddle==='function'?displayIsMiddle():document.body.classList.contains('display-middle')){\n        var mlwS=parseInt(getComputedStyle(document.documentElement).getPropertyValue('--middle-lw'),10)||0;\n        var mmhS=parseInt(getComputedStyle(document.documentElement).getPropertyValue('--middle-menu-h'),10)||0;\n        if(mlwS>40)patch.middleLw=mlwS;\n        if(mmhS>40)patch.middleMh=mmhS;\n      }",
        "live-slot-middle",
    )

    text = sub(
        text,
        "    if(mode==='sides'){\n      if(slot.lw&&slot.rw)localStorage.setItem(SIDES_KEY,JSON.stringify({lw:slot.lw,rw:slot.rw}));",
        "    if(mode==='sides'){\n      if(slot.lw&&slot.rw)localStorage.setItem(SIDES_KEY,JSON.stringify({lw:slot.lw,rw:slot.rw}));\n      try{\n        if(slot.middleLw)localStorage.setItem(typeof middleLwKey==='function'?middleLwKey():liveLayoutKey('catalog-middle-lw-'),parseInt(slot.middleLw,10)+'px');\n        if(slot.middleMh)localStorage.setItem(typeof middleMhKey==='function'?middleMhKey():liveLayoutKey('catalog-middle-menu-h-'),parseInt(slot.middleMh,10)+'px');\n      }catch(eM){}",
        "apply-slot-middle",
    )

    text = sub(
        text,
        "  var o=(typeof layoutOrientId==='function')?layoutOrientId():((typeof isPortraitDesktopSides==='function'&&isPortraitDesktopSides())?'portrait':'wide');\n  if(o==='wide')return 'catalog-layouts-wide-'+ns;\n  var flip=document.body.classList.contains('sides-portrait-flip')?'B':'A';\n  var id=coerceScope(so);\n  return 'catalog-layouts-portrait-'+flip+'-'+id+'-'+ns;\n}\nfunction layoutLastKeyFor(so){\n  var ns=window.CATALOG_NS||'catalog';\n  var o=(typeof layoutOrientId==='function')?layoutOrientId():((typeof isPortraitDesktopSides==='function'&&isPortraitDesktopSides())?'portrait':'wide');\n  if(o==='wide')return 'catalog-layouts-wide-last-'+ns;\n  var flip=document.body.classList.contains('sides-portrait-flip')?'B':'A';\n  var id=coerceScope(so);\n  return 'catalog-layouts-portrait-'+flip+'-'+id+'-last-'+ns;\n}",
        "  var o=(typeof layoutOrientId==='function')?layoutOrientId():((typeof isPortraitDesktopSides==='function'&&isPortraitDesktopSides())?'portrait':'wide');\n  if(o==='middle')return 'catalog-layouts-middle-'+coerceScope(so)+'-'+ns;\n  if(o==='wide')return 'catalog-layouts-wide-'+ns;\n  var flip=document.body.classList.contains('sides-portrait-flip')?'B':'A';\n  var id=coerceScope(so);\n  return 'catalog-layouts-portrait-'+flip+'-'+id+'-'+ns;\n}\nfunction layoutLastKeyFor(so){\n  var ns=window.CATALOG_NS||'catalog';\n  var o=(typeof layoutOrientId==='function')?layoutOrientId():((typeof isPortraitDesktopSides==='function'&&isPortraitDesktopSides())?'portrait':'wide');\n  if(o==='middle')return 'catalog-layouts-middle-'+coerceScope(so)+'-last-'+ns;\n  if(o==='wide')return 'catalog-layouts-wide-last-'+ns;\n  var flip=document.body.classList.contains('sides-portrait-flip')?'B':'A';\n  var id=coerceScope(so);\n  return 'catalog-layouts-portrait-'+flip+'-'+id+'-last-'+ns;\n}",
        "named-layout-keys",
    )

    text = sub(
        text,
        "    ac:localStorage.getItem(KEYAC),\n    sh:localStorage.getItem(KEYSH),\n    scale:typeof currentUiScale==='function'?currentUiScale():undefined\n  };\n}",
        "    ac:localStorage.getItem(KEYAC),\n    sh:localStorage.getItem(KEYSH),\n    scale:typeof currentUiScale==='function'?currentUiScale():undefined,\n    mlw:parseInt(getComputedStyle(document.documentElement).getPropertyValue('--middle-lw'),10)||undefined,\n    mmh:parseInt(getComputedStyle(document.documentElement).getPropertyValue('--middle-menu-h'),10)||undefined\n  };\n}",
        "snap-named",
    )

    text = sub(
        text,
        "    if(snap.lw)document.body.style.setProperty('--sides-lw',parseInt(snap.lw,10)+'px');\n    if(snap.rw)document.body.style.setProperty('--sides-rw',parseInt(snap.rw,10)+'px');\n    if(snap.indexH)document.body.style.setProperty('--sides-index-h',parseInt(snap.indexH,10)+'px');",
        "    if(snap.lw)document.body.style.setProperty('--sides-lw',parseInt(snap.lw,10)+'px');\n    if(snap.rw)document.body.style.setProperty('--sides-rw',parseInt(snap.rw,10)+'px');\n    if(snap.indexH)document.body.style.setProperty('--sides-index-h',parseInt(snap.indexH,10)+'px');\n    if(snap.mlw)document.documentElement.style.setProperty('--middle-lw',parseInt(snap.mlw,10)+'px');\n    if(snap.mmh)document.documentElement.style.setProperty('--middle-menu-h',parseInt(snap.mmh,10)+'px');\n    if((snap.mlw||snap.mmh)&&typeof writeMiddleLayout==='function')writeMiddleLayout(snap.mlw,snap.mmh);",
        "apply-named",
    )

    text = sub(
        text,
        "    localStorage.removeItem('catalog-portrait-menu-h');\n    localStorage.removeItem('catalog-portrait-lw');\n    localStorage.removeItem('catalog-portrait-rw');",
        "    localStorage.removeItem('catalog-portrait-menu-h');\n    localStorage.removeItem('catalog-portrait-lw');\n    localStorage.removeItem('catalog-portrait-rw');\n    try{\n      localStorage.removeItem(typeof middleLwKey==='function'?middleLwKey():('catalog-middle-lw-'+(window.CATALOG_NS||'catalog')));\n      localStorage.removeItem(typeof middleMhKey==='function'?middleMhKey():('catalog-middle-menu-h-'+(window.CATALOG_NS||'catalog')));\n      localStorage.removeItem('catalog-middle-lw');\n      localStorage.removeItem('catalog-middle-menu-h');\n    }catch(eMid){}\n    document.documentElement.style.removeProperty('--middle-lw');\n    document.documentElement.style.removeProperty('--middle-rw');\n    document.documentElement.style.removeProperty('--middle-menu-h');",
        "reset-middle",
    )

    text = sub(
        text,
        "  try{if(typeof persistShadeHeight==='function')persistShadeHeight();}catch(err){}\n  try{if(typeof snapshotLiveToMode==='function')snapshotLiveToMode();}catch(err){}\n}",
        "  try{if(typeof persistShadeHeight==='function')persistShadeHeight();}catch(err){}\n  try{if(typeof snapshotLiveToMode==='function')snapshotLiveToMode();}catch(err){}\n  try{\n    if(typeof displayIsMiddle==='function'&&displayIsMiddle()&&typeof writeMiddleLayout==='function'){\n      var ml=parseInt(getComputedStyle(document.documentElement).getPropertyValue('--middle-lw'),10)||0;\n      var mh=parseInt(getComputedStyle(document.documentElement).getPropertyValue('--middle-menu-h'),10)||0;\n      writeMiddleLayout(ml,mh);\n    }\n  }catch(err){}\n}",
        "persist-all-middle",
    )

    if "function writeMiddleLayout" not in text:
        raise SystemExit(f"{path.name}: missing writeMiddleLayout")
    if "sessionId:'f491c2'" not in text:
        raise SystemExit(f"{path.name}: lost f491c2 logs")
    if path.name == "DS-CATALOG.html":
        if "sessionId:'c00e3e'" not in text:
            raise SystemExit(f"{path.name}: lost c00e3e logs")
        if "function dbgIndexAc" not in text:
            raise SystemExit(f"{path.name}: lost dbgIndexAc")
        if "// #region agent log" not in text:
            raise SystemExit(f"{path.name}: lost agent log regions")
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
