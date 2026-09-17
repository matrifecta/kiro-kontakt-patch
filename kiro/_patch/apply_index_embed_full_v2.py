#!/usr/bin/env python3
"""Embed Index expanded: both overflow axes visible; inline pin after fill-doc."""
from pathlib import Path

ROOT = Path("/home/phnx/kiro-kontakt-patch")
FILES = [
    ROOT / "public/catalogs/KONTAKT-CATALOG.html",
    ROOT / "public/catalogs/DS-CATALOG.html",
    ROOT / "public/catalogs/KONTAKT-CATALOG-portable.html",
    ROOT / "public/catalogs/DS-CATALOG-portable.html",
]
MARK = "fix-INDEX-EMBED-FULL-v2"
KEEP = (
    "c00e3e",
    "fix-CARD-EMBED-SEPARATE-v1",
    "fix-CARD-CHROME-TOP-v1",
    "fix-INDEX-EMBED-FULL-v1",
    MARK,
)


def add_indent(s, n=1):
    pad = " " * n
    return "\n".join((pad + line) if line.strip() else line for line in s.split("\n"))


def sub(text, old, new, label, optional=False):
    n = text.count(old)
    if n == 1:
        return text.replace(old, new)
    if n > 1:
        raise SystemExit(f"{label}: {n} matches")
    if new in text:
        print(f"  skip {label} (already)")
        return text
    for i in range(1, 9):
        oldi, newi = add_indent(old, i), add_indent(new, i)
        ni = text.count(oldi)
        if ni == 1:
            return text.replace(oldi, newi)
        if ni > 1:
            raise SystemExit(f"{label}: {ni} matches (indent {i})")
        if newi in text:
            print(f"  skip {label} (already)")
            return text
    if optional:
        print(f"  skip {label}")
        return text
    raise SystemExit(f"{label}: not found")


CSS_ADD = r"""
/* fix-INDEX-EMBED-FULL-v2: both axes visible (hidden+visible computes to auto); no cap */
html body.display-sides #catalogMain .catalog-body #catalogIndex.is-embedded:not(.is-collapsed),
html body.display-middle #catalogMain .catalog-body #catalogIndex.is-embedded:not(.is-collapsed),
html body.catalog-portable #catalogMain .catalog-body #catalogIndex.is-embedded:not(.is-collapsed),
html body #catalogMain .catalog-body #catalogIndex.is-embedded:not(.is-collapsed){
  height:auto!important;max-height:none!important;min-height:0!important;
  overflow:visible!important;overflow-x:visible!important;overflow-y:visible!important;
  flex:0 0 auto!important;align-self:stretch!important;
  background:var(--bg-surface)!important;isolation:isolate!important
}
html body.display-sides #catalogMain .catalog-body #catalogIndex.is-embedded:not(.is-collapsed) ul#catalogIndexList.index,
html body.display-middle #catalogMain .catalog-body #catalogIndex.is-embedded:not(.is-collapsed) ul#catalogIndexList.index,
html body.catalog-portable #catalogMain .catalog-body #catalogIndex.is-embedded:not(.is-collapsed) ul#catalogIndexList.index,
html body #catalogMain .catalog-body #catalogIndex.is-embedded:not(.is-collapsed) ul#catalogIndexList.index,
html body.display-sides #catalogMain .catalog-body #catalogIndex.is-embedded:not(.is-collapsed) #catalogIndexList,
html body #catalogMain .catalog-body #catalogIndex.is-embedded:not(.is-collapsed) #catalogIndexList{
  height:auto!important;max-height:none!important;min-height:0!important;flex:0 0 auto!important;
  overflow:visible!important;overflow-x:visible!important;overflow-y:visible!important;
  background:var(--bg-surface)!important
}
"""

FN_OLD = """function applyIndexScrollFit(){
  var ix=document.getElementById('catalogIndex');
  if(typeof stripIndexCardChrome==='function')stripIndexCardChrome(ix);"""

FN_NEW = """function syncIndexEmbedFull(){
  var ix=document.getElementById('catalogIndex');
  var il=document.getElementById('catalogIndexList')||(ix&&ix.querySelector('ul.index'));
  if(!ix||!il)return;
  var on=ix.classList.contains('is-embedded')&&!ix.classList.contains('is-collapsed');
  if(!on){
    ['overflow','overflow-x','overflow-y'].forEach(function(p){ix.style.removeProperty(p);il.style.removeProperty(p);});
    ['height','max-height','min-height','flex'].forEach(function(p){il.style.removeProperty(p);});
    if(!document.body.classList.contains('index-fill-doc')){
      ['height','max-height','min-height','flex'].forEach(function(p){ix.style.removeProperty(p);});
    }
    return;
  }
  function pin(el){
    el.style.setProperty('height','auto','important');
    el.style.setProperty('max-height','none','important');
    el.style.setProperty('min-height','0','important');
    el.style.setProperty('overflow','visible','important');
    el.style.setProperty('overflow-x','visible','important');
    el.style.setProperty('overflow-y','visible','important');
    el.style.setProperty('flex','0 0 auto','important');
  }
  pin(ix);pin(il);
  try{
    fetch('http://127.0.0.1:7529/ingest/1cf46354-1d61-4c80-bd72-a340f1db1b51',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'c00e3e'},body:JSON.stringify({sessionId:'c00e3e',runId:'post-fix',hypothesisId:'IX',location:'catalog:syncIndexEmbedFull',message:'embed-index-full',data:{portable:!!window.CATALOG_PORTABLE,ixOv:getComputedStyle(ix).overflowY,ilOv:getComputedStyle(il).overflowY,ixH:ix.scrollHeight,ixCh:ix.clientHeight,ilH:il.scrollHeight,ilCh:il.clientHeight,parent:(ix.parentElement&&(ix.parentElement.id||ix.parentElement.className||'')).toString().slice(0,32)},timestamp:Date.now()})}).catch(function(){});
  }catch(eDbgIx2){}
}
window.syncIndexEmbedFull=syncIndexEmbedFull;
function applyIndexScrollFit(){
  var ix=document.getElementById('catalogIndex');
  if(typeof stripIndexCardChrome==='function')stripIndexCardChrome(ix);"""

AFTER_DESK_OLD = """    if(typeof syncBottomBelowIndex==='function')syncBottomBelowIndex();
    if(typeof syncIndexEmbedBtn==='function')syncIndexEmbedBtn();
    return;
  }
  var head=ix.querySelector('.catalog-index-head');"""

AFTER_DESK_NEW = """    if(typeof syncIndexEmbedFull==='function')syncIndexEmbedFull();
    if(typeof syncBottomBelowIndex==='function')syncBottomBelowIndex();
    if(typeof syncIndexEmbedBtn==='function')syncIndexEmbedBtn();
    return;
  }
  if(typeof syncIndexEmbedFull==='function')syncIndexEmbedFull();
  var head=ix.querySelector('.catalog-index-head');"""

AFTER_PORT_OLD = """    if(typeof syncBottomBelowIndex==='function')syncBottomBelowIndex();
    if(typeof syncIndexEmbedBtn==='function')syncIndexEmbedBtn();
    return;
  }
  ['height','max-height','overflow','overflow-y'].forEach(function(p){ix.style.removeProperty(p);});
  var dock=document.body.classList.contains('index-window-open');
  var head=ix.querySelector('.catalog-index-head');"""

AFTER_PORT_NEW = """    if(typeof syncIndexEmbedFull==='function')syncIndexEmbedFull();
    if(typeof syncBottomBelowIndex==='function')syncBottomBelowIndex();
    if(typeof syncIndexEmbedBtn==='function')syncIndexEmbedBtn();
    return;
  }
  if(typeof syncIndexEmbedFull==='function')syncIndexEmbedFull();
  ['height','max-height','overflow','overflow-y'].forEach(function(p){ix.style.removeProperty(p);});
  var dock=document.body.classList.contains('index-window-open');
  var head=ix.querySelector('.catalog-index-head');"""

TOGGLE_DESK_OLD = """  if(typeof applyIndexScrollFit==='function')applyIndexScrollFit();
  if(box.classList.contains('is-embedded')&&typeof parkCatalogDocNote==='function')parkCatalogDocNote();
  if(typeof syncIndexWindowDock==='function')syncIndexWindowDock();
};"""

TOGGLE_DESK_NEW = """  if(typeof applyIndexScrollFit==='function')applyIndexScrollFit();
  if(typeof syncIndexEmbedFull==='function')syncIndexEmbedFull();
  if(box.classList.contains('is-embedded')&&typeof parkCatalogDocNote==='function')parkCatalogDocNote();
  if(typeof syncIndexWindowDock==='function')syncIndexWindowDock();
};"""

TOGGLE_PORT_OLD = """  if(typeof applyIndexScrollFit==='function')applyIndexScrollFit();
  if(box.classList.contains('is-embedded')&&typeof parkCatalogDocNote==='function')parkCatalogDocNote();
  if(typeof syncIndexWindowDock==='function')syncIndexWindowDock();
  if(typeof portableEnsureScrollMenus==='function')portableEnsureScrollMenus();
};"""

TOGGLE_PORT_NEW = """  if(typeof applyIndexScrollFit==='function')applyIndexScrollFit();
  if(typeof syncIndexEmbedFull==='function')syncIndexEmbedFull();
  if(box.classList.contains('is-embedded')&&typeof parkCatalogDocNote==='function')parkCatalogDocNote();
  if(typeof syncIndexWindowDock==='function')syncIndexWindowDock();
  if(typeof portableEnsureScrollMenus==='function')portableEnsureScrollMenus();
};"""

EMBED_APPLY_OLD = """    if(typeof stripIndexCardChrome==='function')stripIndexCardChrome(ix);
    if(typeof applyIndexScrollFit==='function')applyIndexScrollFit();
    if(typeof syncIndexWindowDock==='function')syncIndexWindowDock();
    if(typeof applyIndexFillDocStyles==='function')applyIndexFillDocStyles();"""

EMBED_APPLY_NEW = """    if(typeof stripIndexCardChrome==='function')stripIndexCardChrome(ix);
    if(typeof applyIndexScrollFit==='function')applyIndexScrollFit();
    if(typeof syncIndexWindowDock==='function')syncIndexWindowDock();
    if(typeof applyIndexFillDocStyles==='function')applyIndexFillDocStyles();
    if(typeof syncIndexEmbedFull==='function')syncIndexEmbedFull();"""

FILL_OLD = """  }catch(eDbgL){}
  // #endregion
}
window.applyIndexFillDocStyles=applyIndexFillDocStyles;"""

FILL_NEW = """  }catch(eDbgL){}
  // #endregion
  if(typeof syncIndexEmbedFull==='function')syncIndexEmbedFull();
}
window.applyIndexFillDocStyles=applyIndexFillDocStyles;"""


def patch(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    n = path.name
    if MARK in text:
        print("skip", n)
        return
    idx = text.rfind("</style>")
    if idx < 0:
        raise SystemExit(f"{n}: no </style>")
    text = text[:idx] + CSS_ADD + text[idx:]
    text = sub(text, FN_OLD, FN_NEW, f"{n}: sync-fn")
    if "portable" in n:
        text = sub(text, AFTER_PORT_OLD, AFTER_PORT_NEW, f"{n}: fit-port")
        text = sub(text, TOGGLE_PORT_OLD, TOGGLE_PORT_NEW, f"{n}: toggle-port")
        text = sub(text, FILL_OLD, FILL_NEW, f"{n}: fill-doc")
    else:
        text = sub(text, AFTER_DESK_OLD, AFTER_DESK_NEW, f"{n}: fit-desk")
        text = sub(text, TOGGLE_DESK_OLD, TOGGLE_DESK_NEW, f"{n}: toggle-desk")
        text = sub(text, FILL_OLD, FILL_NEW, f"{n}: fill-doc", optional=True)
    text = sub(text, EMBED_APPLY_OLD, EMBED_APPLY_NEW, f"{n}: embed-apply")
    raw = text.encode("utf-8")
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_bytes(raw)
    out = tmp.read_bytes().decode("utf-8")
    if not out.strip().endswith("</html>"):
        tmp.unlink()
        raise SystemExit(f"{n}: truncated")
    for keep in KEEP:
        if keep not in out:
            tmp.unlink()
            raise SystemExit(f"{n}: lost {keep}")
    tmp.replace(path)
    print("OK", n, len(raw))


def main() -> None:
    for p in FILES:
        if not p.exists():
            raise SystemExit(f"missing {p}")
        patch(p)


if __name__ == "__main__":
    main()
