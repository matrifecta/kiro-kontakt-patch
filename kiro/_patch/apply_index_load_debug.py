#!/usr/bin/env python3
"""Index load instrumentation (c00e3e) + keep mobile polish helpers."""
from pathlib import Path

FILES = [
    Path("/home/phnx/kiro-kontakt-patch/public/catalogs/KONTAKT-CATALOG-portable.html"),
    Path("/home/phnx/kiro-kontakt-patch/public/catalogs/DS-CATALOG-portable.html"),
]

HELPER = r"""function debugIndexLoad(reason,extra){
  // #region agent log
  try{
    var ix=document.getElementById('catalogIndex');
    var il=document.getElementById('catalogIndexList')||(ix&&ix.querySelector('ul.index,ul#catalogIndexList'));
    var ics=ix?getComputedStyle(ix):null;
    var lcs=il?getComputedStyle(il):null;
    var ir=ix?ix.getBoundingClientRect():null;
    var lr=il?il.getBoundingClientRect():null;
    var pref=null;
    try{if(typeof readIndexEmbedPref==='function')pref=readIndexEmbedPref();}catch(eP){}
    var data={
      reason:reason||'',
      portable:!!window.CATALOG_PORTABLE,
      ns:String(window.CATALOG_NS||''),
      vw:innerWidth,vh:innerHeight,
      orient:innerWidth>=innerHeight?'land':'port',
      sides:document.body.classList.contains('display-sides'),
      middle:document.body.classList.contains('display-middle'),
      content:document.body.classList.contains('display-content'),
      fs:document.body.classList.contains('display-fs'),
      acFs:document.body.classList.contains('ac-fs-open'),
      kwFs:document.body.classList.contains('kw-fs-open'),
      contentOn:document.body.classList.contains('content-window-on'),
      ixWin:document.body.classList.contains('index-window-open'),
      hasIx:!!ix,
      parent:ix&&ix.parentElement?(ix.parentElement.id||ix.parentElement.className||'').toString().slice(0,48):'',
      collapsed:!!(ix&&ix.classList.contains('is-collapsed')),
      embed:!!(ix&&ix.classList.contains('is-embedded')),
      pref:pref,
      listN:il?il.children.length:0,
      ixD:ics?ics.display:'',
      ixV:ics?ics.visibility:'',
      ixP:ics?ics.position:'',
      ixZ:ics?ics.zIndex:'',
      ir:ir?{x:Math.round(ir.x),y:Math.round(ir.y),w:Math.round(ir.width),h:Math.round(ir.height)}:null,
      listD:lcs?lcs.display:'',
      lr:lr?{w:Math.round(lr.width),h:Math.round(lr.height),sh:il?il.scrollHeight:0}:null
    };
    if(extra){for(var k in extra)data[k]=extra[k];}
    var key=JSON.stringify({r:data.reason,c:data.collapsed,e:data.embed,w:data.ixWin,n:data.listN,d:data.ixD,v:data.ixV,p:data.ixP,h:data.ir&&data.ir.h,on:data.contentOn,fs:data.acFs||data.kwFs||data.fs});
    var now=Date.now();
    if(debugIndexLoad._k===key&&now-(debugIndexLoad._t||0)<800)return;
    debugIndexLoad._k=key;debugIndexLoad._t=now;
    fetch('http://127.0.0.1:7529/ingest/1cf46354-1d61-4c80-bd72-a340f1db1b51',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'c00e3e'},body:JSON.stringify({sessionId:'c00e3e',runId:'ix-load',hypothesisId:'A-E',location:'debugIndexLoad',message:'index-load',data:data,timestamp:now})}).catch(function(){});
  }catch(errIxL){}
  // #endregion
}
"""

FORCE_OLD = """function forceCatalogIndexClosed(reason){
  var ix=document.getElementById('catalogIndex');
  if(!ix)return;
  ix.classList.add('is-collapsed');
  ix.dataset.dockAuto='';
  ix.dataset.dockPin='';
  if(typeof syncIndexToggleUi==='function')syncIndexToggleUi(ix);

}
"""

FORCE_NEW = HELPER + """function forceCatalogIndexClosed(reason){
  var ix=document.getElementById('catalogIndex');
  if(!ix){
    debugIndexLoad('force-closed-missing',{asked:String(reason||'')});
    return;
  }
  ix.classList.add('is-collapsed');
  ix.dataset.dockAuto='';
  ix.dataset.dockPin='';
  if(typeof syncIndexToggleUi==='function')syncIndexToggleUi(ix);
  debugIndexLoad('force-closed',{asked:String(reason||'')});
}
"""

ENSURE_OLD = """  if(typeof placeCatalogJumpStack==='function')placeCatalogJumpStack();
  if(typeof bindCatalogJumpScroll==='function')bindCatalogJumpScroll();
  if(typeof bindCatalogTop==='function')bindCatalogTop();
}
var SIDES_KEY='catalog-sides-cols-'+(window.CATALOG_NS||'catalog');
"""

ENSURE_NEW = """  if(typeof placeCatalogJumpStack==='function')placeCatalogJumpStack();
  if(typeof bindCatalogJumpScroll==='function')bindCatalogJumpScroll();
  if(typeof bindCatalogTop==='function')bindCatalogTop();
  debugIndexLoad('ensure-main');
}
var SIDES_KEY='catalog-sides-cols-'+(window.CATALOG_NS||'catalog');
"""

DOCK_OLD = """  if(typeof placeCatalogJumpStack==='function')placeCatalogJumpStack();
  };
  if(typeof withCatalogScrollPin==='function')withCatalogScrollPin(run);
  else run();
}
window.syncIndexWindowDock=syncIndexWindowDock;
"""

DOCK_NEW = """  if(typeof placeCatalogJumpStack==='function')placeCatalogJumpStack();
  debugIndexLoad('window-dock');
  };
  if(typeof withCatalogScrollPin==='function')withCatalogScrollPin(run);
  else run();
}
window.syncIndexWindowDock=syncIndexWindowDock;
"""

TOGGLE_OLD = """    if(typeof portableEnsureScrollMenus==='function')portableEnsureScrollMenus();
    syncIndexEmbedBtn();
  };
  if(typeof withCatalogScrollPin==='function')withCatalogScrollPin(apply);
  else apply();
"""

TOGGLE_NEW = """    if(typeof portableEnsureScrollMenus==='function')portableEnsureScrollMenus();
    syncIndexEmbedBtn();
    debugIndexLoad('embed-toggle',{on:on});
  };
  if(typeof withCatalogScrollPin==='function')withCatalogScrollPin(apply);
  else apply();
"""

SYNC_OLD = """  syncPortableIndexContentGap();
  // #region agent log
"""

SYNC_NEW = """  syncPortableIndexContentGap();
  debugIndexLoad('content-window');
  // #region agent log
"""

BOOT_OLD = "  if(typeof forceCatalogIndexClosed==='function')forceCatalogIndexClosed('boot');\n"

BOOT_NEW = """  if(typeof forceCatalogIndexClosed==='function')forceCatalogIndexClosed('boot');
  debugIndexLoad('boot-after-closed');
"""


def safe_write(path: Path, text: str) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    out = tmp.read_text(encoding="utf-8")
    if not out.rstrip().endswith("</html>"):
        tmp.unlink(missing_ok=True)
        raise SystemExit(f"{path.name}: truncated")
    path.write_text(out, encoding="utf-8")
    tmp.unlink(missing_ok=True)


def once(text, old, new, label, name):
    if old not in text:
        raise SystemExit(f"{name}: missing {label}: {old[:70]!r}")
    n = text.count(old)
    print(f"  {n}x {label} {name}")
    return text.replace(old, new)


def patch(path: Path) -> None:
    name = path.name
    text = path.read_text(encoding="utf-8")
    if "function debugIndexLoad(" in text:
        print(f"skip already {name}")
        return
    text = once(text, FORCE_OLD, FORCE_NEW, "force", name)
    text = once(text, ENSURE_OLD, ENSURE_NEW, "ensure", name)
    text = once(text, DOCK_OLD, DOCK_NEW, "dock", name)
    text = once(text, TOGGLE_OLD, TOGGLE_NEW, "toggle", name)
    text = once(text, SYNC_OLD, SYNC_NEW, "sync-cw", name)
    text = once(text, BOOT_OLD, BOOT_NEW, "boot", name)
    if "function debugIndexLoad(" not in text:
        raise SystemExit(f"{name}: helper missing")
    safe_write(path, text)
    print(f"ok {name} bytes={path.stat().st_size}")


def main():
    for p in FILES:
        print("==", p.name)
        patch(p)


if __name__ == "__main__":
    main()
