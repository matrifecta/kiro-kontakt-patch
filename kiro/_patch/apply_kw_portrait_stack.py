#!/usr/bin/env python3
"""Portrait Keywords: keep pills stacked inside the pane, not in a second column."""
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

PORTRAIT_OLD = (
    "@media(orientation:portrait){.filter-panel,.cat-switch,#kwbar,.mode-switch{flex-wrap:wrap;max-width:100%;overflow-x:hidden}"
    ".cat-switch{overflow-y:auto;-webkit-overflow-scrolling:touch}"
    "body:not(.layout-edit) .filter-wrap:not(.kw-shade-height-set) #kwbar{overflow:visible;max-height:none}"
    ".entry.highlight .cover,.entry.highlight .cover img{max-height:min(38dvh,100%)}}"
)
PORTRAIT_NEW = (
    "@media(orientation:portrait){"
    ".filter-panel,body.display-sides #filterWrap .filter-panel,body.display-sides.display-middle #filterWrap .filter-panel{"
    "flex-direction:column!important;flex-wrap:nowrap!important;align-items:stretch;max-width:100%;min-width:0;overflow-x:hidden}"
    ".cat-switch,#kwbar,.mode-switch{flex-wrap:wrap!important;max-width:100%;min-width:0;width:100%;box-sizing:border-box;overflow-x:hidden}"
    ".cat-switch{overflow-y:visible;-webkit-overflow-scrolling:touch;align-content:flex-start}"
    ".cat-switch-lead{display:flex!important;flex-wrap:wrap!important;max-width:100%;min-width:0;flex:0 1 auto}"
    ".filter-panel>#kwbar,body.display-sides #kwbar,body.display-sides.display-middle #kwbar{"
    "overflow-x:hidden!important;overflow-y:auto!important;align-content:flex-start;min-width:0}"
    "body:not(.layout-edit) .filter-wrap:not(.kw-shade-height-set) #kwbar{overflow-x:hidden;overflow-y:auto;max-height:none}"
    ".entry.highlight .cover,.entry.highlight .cover img{max-height:min(38dvh,100%)}}"
)

LEAK_OLD = "#kwbar{flex-wrap:wrap;max-width:100%;overflow-x:auto;overflow-y:hidden;-webkit-overflow-scrolling:touch}"
LEAK_NEW = "#kwbar{flex-wrap:wrap;max-width:100%;min-width:0;overflow-x:hidden;overflow-y:auto;-webkit-overflow-scrolling:touch;align-content:flex-start}"

DBG = r"""function dbgKwPane(phase){
  // #region agent log
  try{
    var now=Date.now();
    if(window._dbgKwAt&&now-window._dbgKwAt<200)return;
    window._dbgKwAt=now;
    var fw=document.getElementById('filterWrap'),kw=document.getElementById('kwbar'),cs=document.querySelector('.cat-switch'),panel=document.getElementById('filterPanel');
    var fr=fw?fw.getBoundingClientRect():null,kr=kw?kw.getBoundingClientRect():null,cr=cs?cs.getBoundingClientRect():null;
    var pcs=panel?getComputedStyle(panel):null;
    fetch('http://127.0.0.1:7529/ingest/1cf46354-1d61-4c80-bd72-a340f1db1b51',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'c00e3e'},body:JSON.stringify({sessionId:'c00e3e',runId:'post-fix',hypothesisId:'H-P1',location:'catalog:dbgKwPane',message:'kw-pane',data:{phase:String(phase||''),portrait:!!(window.matchMedia&&window.matchMedia('(orientation:portrait)').matches),vw:window.innerWidth||0,vh:window.innerHeight||0,mode:document.body.classList.contains('display-middle')?'middle':(document.body.classList.contains('display-sides')?'sides':'other'),paneW:fr?Math.round(fr.width):0,paneR:fr?Math.round(fr.right):0,kwL:kr?Math.round(kr.left):0,kwR:kr?Math.round(kr.right):0,csL:cr?Math.round(cr.left):0,overflow:(kr&&fr)?Math.round(kr.right-fr.right):0,beside:!!(kr&&cr&&Math.abs(kr.top-cr.top)<12&&kr.left>cr.right-8),panelDir:pcs?pcs.flexDirection:'',panelWrap:pcs?pcs.flexWrap:''},timestamp:Date.now()})}).catch(function(){});
  }catch(eLog){}
  // #endregion
}
"""

CALL_EARLY_OLD = "    if(typeof placeCatalogJumpStack==='function')placeCatalogJumpStack();\n    return;\n  }"
CALL_EARLY_NEW = "    if(typeof placeCatalogJumpStack==='function')placeCatalogJumpStack();\n    if(typeof dbgKwPane==='function')dbgKwPane('sides-off');\n    return;\n  }"

CALL_END_OLD = "  if(typeof placeCatalogJumpStack==='function')placeCatalogJumpStack();\n}\nfunction placeSidesHandles(){"
CALL_END_NEW = "  if(typeof placeCatalogJumpStack==='function')placeCatalogJumpStack();\n  if(typeof dbgKwPane==='function')dbgKwPane('sides-on');\n}\nfunction placeSidesHandles(){"

FN_OLD = "function applySidesCols(){"
FN_NEW = DBG + "function applySidesCols(){"


def sub(text, old, new, label, path, optional=False):
    if new in text and old not in text:
        print(f"  skip {path.name} {label}")
        return text
    n = text.count(old)
    if n == 1:
        return text.replace(old, new, 1)
    if optional and n == 0:
        print(f"  skip {path.name} {label} (absent)")
        return text
    raise SystemExit(f"{path.name}: {label} count={n} expected 1")


def main():
    for p in FILES:
        t = p.read_text(encoding="utf-8")
        t = sub(t, PORTRAIT_OLD, PORTRAIT_NEW, "portrait-kw", p)
        t = sub(t, LEAK_OLD, LEAK_NEW, "kw-leak", p)
        t = sub(t, FN_OLD, FN_NEW, "dbg-fn", p)
        t = sub(t, CALL_EARLY_OLD, CALL_EARLY_NEW, "dbg-early", p, optional=True)
        t = sub(t, CALL_END_OLD, CALL_END_NEW, "dbg-end", p)
        p.write_text(t, encoding="utf-8")
        print("ok", p.name)


if __name__ == "__main__":
    main()
