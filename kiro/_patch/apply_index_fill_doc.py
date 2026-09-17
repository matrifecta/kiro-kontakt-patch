#!/usr/bin/env python3
"""Portable: Index Window fills down to About/Document; short mobile titles."""
from pathlib import Path

ROOT = Path("/home/phnx/kiro-kontakt-patch/public/catalogs")
FILES = [
    ROOT / "KONTAKT-CATALOG-portable.html",
    ROOT / "DS-CATALOG-portable.html",
]

CSS_MARK = "</style></head><body class=\"search-mode\">"
CSS_ADD = r"""
/* fix-INDEX-FILL-DOC: Window Index reaches About/Document when one menu sits beside content */
@media all{
  body.catalog-portable.index-fill-doc.index-window-open #catalogMain{
    display:flex!important;flex-direction:column!important;overflow:hidden!important
  }
  body.catalog-portable.index-fill-doc #catalogIndex:not(.is-embedded):not(.is-collapsed){
    flex:1 1 0%!important;height:auto!important;max-height:none!important;min-height:0!important;
    margin-top:0!important;margin-bottom:4px!important
  }
  body.catalog-portable.index-fill-doc #catalogMain>.catalog-body,
  body.catalog-portable.index-fill-doc #catalogMain .catalog-body{
    flex:0 0 0px!important;height:0!important;min-height:0!important;max-height:0!important;
    margin:0!important;overflow:hidden!important;overflow-y:hidden!important
  }
  body.catalog-portable.index-fill-doc #catalogDocNote,
  body.catalog-portable.index-fill-doc #catalogMain>.catalog-doc-note{
    flex:0 0 auto!important;margin:0!important
  }
}
""" + CSS_MARK

FN_OLD = """window.catalogContentScroller=catalogContentScroller;
function syncIndexWindowDock(){"""

FN_NEW = """window.catalogContentScroller=catalogContentScroller;
function indexWindowFillsToDoc(){
  if(!window.CATALOG_PORTABLE)return false;
  var b=document.body;
  if(!b.classList.contains('display-sides')||b.classList.contains('display-middle'))return false;
  if(b.classList.contains('ac-fs-open')||b.classList.contains('kw-fs-open')||b.classList.contains('dual-fs-open'))return false;
  var searchOn=!b.classList.contains('search-chrome-collapsed');
  var kwOn=b.classList.contains('kw-open')&&!b.classList.contains('kw-chrome-collapsed');
  return (searchOn&&!kwOn)||(!searchOn&&kwOn);
}
window.indexWindowFillsToDoc=indexWindowFillsToDoc;
function applyIndexFillDocStyles(){
  var fill=!!(document.body.classList.contains('index-window-open')&&indexWindowFillsToDoc());
  document.body.classList.toggle('index-fill-doc',fill);
  var ix=document.getElementById('catalogIndex');
  var main=document.getElementById('catalogMain');
  var cb=main&&(main.querySelector(':scope > .catalog-body')||main.querySelector('.catalog-body'));
  var note=document.getElementById('catalogDocNote');
  if(fill){
    if(ix){
      ix.style.setProperty('flex','1 1 0%','important');
      ix.style.setProperty('height','auto','important');
      ix.style.setProperty('max-height','none','important');
      ix.style.setProperty('margin-bottom','4px','important');
    }
    if(cb){
      cb.style.setProperty('flex','0 0 0px','important');
      cb.style.setProperty('height','0px','important');
      cb.style.setProperty('min-height','0','important');
      cb.style.setProperty('max-height','0','important');
      cb.style.setProperty('overflow','hidden','important');
      cb.style.setProperty('overflow-y','hidden','important');
      cb.style.setProperty('margin','0','important');
    }
    if(note){
      note.style.setProperty('flex','0 0 auto','important');
      note.style.setProperty('margin','0','important');
    }
  }else{
    if(ix){['flex','height','max-height','margin-bottom'].forEach(function(p){ix.style.removeProperty(p);});}
    if(note){['flex','margin'].forEach(function(p){note.style.removeProperty(p);});}
    if(cb&&document.body.classList.contains('index-window-open')){
      cb.style.setProperty('flex','1 1 0%','important');
      cb.style.setProperty('height','0','important');
      cb.style.setProperty('min-height','0','important');
      cb.style.removeProperty('max-height');
      cb.style.setProperty('overflow-y','auto','important');
      cb.style.removeProperty('margin');
    }
  }
  // #region agent log
  try{
    var ir=ix?ix.getBoundingClientRect():null;
    var nr=note?note.getBoundingClientRect():null;
    var mr=main?main.getBoundingClientRect():null;
    fetch('http://127.0.0.1:7529/ingest/1cf46354-1d61-4c80-bd72-a340f1db1b51',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'c00e3e'},body:JSON.stringify({sessionId:'c00e3e',runId:'post-fix',hypothesisId:'L',location:'catalog:applyIndexFillDocStyles',message:'index fill to doc',data:{fill:fill,on:document.body.classList.contains('index-window-open'),searchOn:!document.body.classList.contains('search-chrome-collapsed'),kwOn:document.body.classList.contains('kw-open')&&!document.body.classList.contains('kw-chrome-collapsed'),orient:window.matchMedia&&window.matchMedia('(orientation:landscape)').matches?'land':'port',vw:window.innerWidth,vh:window.innerHeight,ixH:ir?Math.round(ir.height):0,ixB:ir?Math.round(ir.bottom):0,noteT:nr?Math.round(nr.top):0,gap:ir&&nr?Math.round(nr.top-ir.bottom):null,cbH:cb?Math.round(cb.getBoundingClientRect().height):0,mainH:mr?Math.round(mr.height):0,ixFlex:ix?getComputedStyle(ix).flex:'',ixMax:ix?getComputedStyle(ix).maxHeight:'',h1:(document.querySelector('h1#top')||{}).textContent||'',title:document.title},timestamp:Date.now()})}).catch(function(){});
  }catch(eDbgL){}
  // #endregion
}
window.applyIndexFillDocStyles=applyIndexFillDocStyles;
function syncIndexWindowDock(){"""

DOCK_END_OLD = """  if(typeof window.syncMainHoverStripe==='function')window.syncMainHoverStripe();
}
window.syncIndexWindowDock=syncIndexWindowDock;"""

DOCK_END_NEW = """  if(typeof applyIndexFillDocStyles==='function')applyIndexFillDocStyles();
  if(typeof window.syncMainHoverStripe==='function')window.syncMainHoverStripe();
}
window.syncIndexWindowDock=syncIndexWindowDock;"""

PORT_OLD = """  if(typeof syncIndexWindowDock==='function')syncIndexWindowDock();
  var dock=document.body.classList.contains('index-window-open');"""

PORT_NEW = """  if(typeof syncIndexWindowDock==='function')syncIndexWindowDock();
  if(typeof applyIndexFillDocStyles==='function')applyIndexFillDocStyles();
  var dock=document.body.classList.contains('index-window-open');"""


def patch(path: Path) -> None:
    raw = path.read_bytes()
    t = raw.decode("utf-8")
    n = path.name
    if CSS_MARK not in t:
        raise SystemExit(f"{n}: css mark missing")
    if t.count(CSS_MARK) != 1:
        raise SystemExit(f"{n}: css mark count {t.count(CSS_MARK)}")
    if "fix-INDEX-FILL-DOC" not in t:
        t = t.replace(CSS_MARK, CSS_ADD, 1)
    if "function indexWindowFillsToDoc(" not in t:
        if FN_OLD not in t:
            raise SystemExit(f"{n}: fn mark missing")
        t = t.replace(FN_OLD, FN_NEW, 1)
    if "applyIndexFillDocStyles();" not in t.split("window.syncIndexWindowDock")[0]:
        if DOCK_END_OLD not in t:
            raise SystemExit(f"{n}: dock end missing")
        t = t.replace(DOCK_END_OLD, DOCK_END_NEW, 1)
    if PORT_OLD in t and "applyIndexFillDocStyles();" not in t[t.find(PORT_OLD) : t.find(PORT_OLD) + 180]:
        t = t.replace(PORT_OLD, PORT_NEW, 1)
    if n.startswith("KONTAKT"):
        t = t.replace("<title>Kontakt Library</title>", "<title>Kontakt Lib</title>", 1)
        t = t.replace('<h1 id="top">Kontakt Library</h1>', '<h1 id="top">Kontakt Lib</h1>', 1)
    elif n.startswith("DS"):
        t = t.replace("<title>Decent Sampler Library</title>", "<title>DS Lib</title>", 1)
        t = t.replace('<h1 id="top">Decent Sampler Library</h1>', '<h1 id="top">DS Lib</h1>', 1)
    out = t.encode("utf-8")
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_bytes(out)
    if not tmp.read_bytes().decode("utf-8").strip().endswith("</html>"):
        tmp.unlink()
        raise SystemExit(f"{n}: truncated write")
    tmp.replace(path)
    print("OK", n, "bytes", len(out), "lines", t.count("\n"), "fill", "fix-INDEX-FILL-DOC" in t, "h1", "Kontakt Lib" in t or "DS Lib" in t)


def main() -> None:
    for p in FILES:
        patch(p)


if __name__ == "__main__":
    main()
