#!/usr/bin/env python3
"""Portable menus take remaining real estate and reflow on rotate/resize."""
from pathlib import Path

ROOT = Path("/home/phnx/kiro-kontakt-patch")
FILES = [
    ROOT / "public/catalogs/DS-CATALOG-portable.html",
    ROOT / "public/catalogs/KONTAKT-CATALOG-portable.html",
]

CSS_MARK = "/* fix-PORTABLE-FILL:"
CSS_ADD = r"""
/* fix-PORTABLE-FILL: menus take leftover real estate; reflow on rotate */
@media all{
  body.catalog-portable.display-sides.display-middle{
    display:flex!important;flex-direction:column!important;
    height:100dvh!important;overflow:hidden!important
  }
  body.catalog-portable.display-sides.display-middle .catalog-header{flex:0 0 auto}
  body.catalog-portable.display-sides.display-middle #searchChrome,
  body.catalog-portable.display-sides.display-middle #filterWrap,
  body.catalog-portable.display-sides.display-middle.kw-open #filterWrap{
    flex:1 1 0%!important;max-height:none!important;min-height:6.5rem!important;
    height:auto!important;width:100%!important;overflow:hidden!important
  }
  body.catalog-portable.display-sides.display-middle.search-chrome-collapsed #searchChrome{display:none!important;flex:none!important}
  body.catalog-portable.display-sides.display-middle:not(.kw-open) #filterWrap,
  body.catalog-portable.display-sides.display-middle.kw-chrome-collapsed #filterWrap{display:none!important;flex:none!important}
  body.catalog-portable.display-sides.display-middle #catalogMain{
    flex:1.2 1 0%!important;min-height:8rem!important;width:100%!important;min-width:0
  }
  body.catalog-portable.display-fs #searchChrome,
  body.catalog-portable.display-fs #filterWrap,
  body.catalog-portable.display-sides:not(.display-middle) #searchChrome,
  body.catalog-portable.display-sides:not(.display-middle) #filterWrap{
    align-self:stretch!important;min-height:0!important
  }
}
"""

CLAMP_OLD = """function clampPortableVars(){
  var vw=window.innerWidth||400;
  var cap=Math.round(vw*0.72);
  ['--portable-lw','--portable-rw'].forEach(function(p){
    var v=parseInt(getComputedStyle(document.documentElement).getPropertyValue(p),10);
    if(v&&v>cap)document.documentElement.style.setProperty(p,Math.round(vw*0.42)+'px');
  });
  var vh=window.innerHeight||800;
  var mh=parseInt(getComputedStyle(document.documentElement).getPropertyValue('--portable-menu-h'),10);
  if(mh&&mh>vh*0.55)document.documentElement.style.setProperty('--portable-menu-h',Math.round(vh*0.32)+'px');
}"""

CLAMP_NEW = """function portableOrientId(){
  try{return (window.matchMedia&&window.matchMedia('(orientation:portrait)').matches)?'p':'l';}catch(err){return 'l';}
}
var lastPortableOrient=portableOrientId();
function clampPortableVars(){
  var o=portableOrientId();
  if(lastPortableOrient&&lastPortableOrient!==o){
    ['--portable-lw','--portable-rw','--portable-menu-h'].forEach(function(p){
      document.documentElement.style.removeProperty(p);
    });
  }
  lastPortableOrient=o;
  var vw=window.innerWidth||400;
  var lo=Math.round(vw*0.28), hi=Math.round(vw*0.72);
  ['--portable-lw','--portable-rw'].forEach(function(p){
    var raw=document.documentElement.style.getPropertyValue(p);
    if(!raw||raw.indexOf('px')<0)return;
    var v=parseInt(raw,10);
    if(!v)return;
    if(v<lo)document.documentElement.style.setProperty(p,lo+'px');
    else if(v>hi)document.documentElement.style.setProperty(p,hi+'px');
  });
  var vh=window.innerHeight||800;
  var mhRaw=document.documentElement.style.getPropertyValue('--portable-menu-h');
  if(mhRaw&&mhRaw.indexOf('px')>=0){
    var mh=parseInt(mhRaw,10);
    var mlo=Math.round(vh*0.22), mhi=Math.round(vh*0.62);
    if(mh&&mh<mlo)document.documentElement.style.setProperty('--portable-menu-h',mlo+'px');
    else if(mh&&mh>mhi)document.documentElement.style.setProperty('--portable-menu-h',mhi+'px');
  }
  if(typeof dbgPortableFill==='function')dbgPortableFill('clamp');
}"""

FILL_LOG = r"""
function dbgPortableFill(phase){
  // #region agent log
  try{
    var sc=document.getElementById('searchChrome'),fw=document.getElementById('filterWrap'),main=document.getElementById('catalogMain');
    function rb(el){if(!el||getComputedStyle(el).display==='none')return null;var r=el.getBoundingClientRect();return {l:Math.round(r.left),t:Math.round(r.top),w:Math.round(r.width),h:Math.round(r.height)};}
    var sr=rb(sc),kr=rb(fw),mr=rb(main);
    fetch('http://127.0.0.1:7529/ingest/1cf46354-1d61-4c80-bd72-a340f1db1b51',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'c00e3e'},body:JSON.stringify({sessionId:'c00e3e',runId:'post-fix',hypothesisId:'H-FILL1',location:'catalog:dbgPortableFill',message:'pane-fill',data:{phase:String(phase||''),vw:innerWidth||0,vh:innerHeight||0,orient:portableOrientId(),cur:typeof currentDisplay!=='undefined'?String(currentDisplay):'',lw:document.documentElement.style.getPropertyValue('--portable-lw')||'',search:sr,kw:kr,main:mr,grid:getComputedStyle(document.body).gridTemplateColumns,rows:getComputedStyle(document.body).gridTemplateRows,bodyDisp:getComputedStyle(document.body).display},timestamp:Date.now()})}).catch(function(){});
  }catch(eF){}
  // #endregion
}
"""

BOOT_OLD = """    if(typeof dbgPortableScroll==='function')dbgPortableScroll('setDisplayMode',{hyp:'H-FS1'});
  }
}"""

BOOT_NEW = """    if(typeof dbgPortableScroll==='function')dbgPortableScroll('setDisplayMode',{hyp:'H-FS1'});
    if(typeof dbgPortableFill==='function')dbgPortableFill('setDisplayMode');
  }
}"""

MID_OLD = "    max-height:min(38dvh,18rem)!important;height:auto!important;"
MID_NEW = "    max-height:none!important;flex:1 1 0%!important;min-height:6.5rem!important;height:auto!important;"


def sub(text, old, new, label, path):
    if old not in text:
        if new in text:
            print(f"  skip {path.name} {label}")
            return text
        raise SystemExit(f"{path.name}: {label} missing")
    n = text.count(old)
    if n != 1 and label not in ("mid-max",):
        raise SystemExit(f"{path.name}: {label} count={n}")
    return text.replace(old, new)


def main():
    for path in FILES:
        t = path.read_text(encoding="utf-8")
        t = t.replace(
            "minmax(0,var(--portable-lw,42%)) minmax(0,1fr)",
            "minmax(0,var(--portable-lw,1.2fr)) minmax(min(100%,12.5rem),1fr)",
        )
        t = t.replace(
            "minmax(0,1fr) minmax(0,var(--portable-lw,42%))",
            "minmax(min(100%,12.5rem),1fr) minmax(0,var(--portable-lw,1.2fr))",
        )
        t = t.replace(
            "minmax(0,1fr) minmax(0,var(--portable-rw,42%))",
            "minmax(min(100%,12.5rem),1fr) minmax(0,var(--portable-rw,1.2fr))",
        )
        t = t.replace(
            "minmax(0,var(--portable-rw,42%)) minmax(0,1fr)",
            "minmax(0,var(--portable-rw,1.2fr)) minmax(min(100%,12.5rem),1fr)",
        )
        if MID_OLD in t:
            t = t.replace(MID_OLD, MID_NEW)
            print(f"  mid {path.name}")
        t = sub(t, CLAMP_OLD, CLAMP_NEW, "clamp", path)
        if "function dbgPortableFill(" not in t:
            needle = "window.portableWantBrowserFs=portableWantBrowserFs;"
            if needle not in t:
                raise SystemExit(f"{path.name}: no portableWantBrowserFs")
            t = t.replace(needle, FILL_LOG + "\n" + needle, 1)
            print(f"  fill-log {path.name}")
        t = sub(t, BOOT_OLD, BOOT_NEW, "boot", path)
        if CSS_MARK not in t:
            if "</style></head>" not in t:
                raise SystemExit(f"{path.name}: no style close")
            t = t.replace("</style></head>", CSS_ADD + "\n</style></head>", 1)
            print(f"  css {path.name}")
        else:
            print(f"  skip {path.name} css")
        path.write_text(t, encoding="utf-8")
        print("ok", path.name)


if __name__ == "__main__":
    main()
