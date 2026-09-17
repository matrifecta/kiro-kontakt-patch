#!/usr/bin/env python3
"""Landscape Flip + Search FS must enter true FS. Index path icons actually removed."""
from pathlib import Path

ROOT = Path("/home/phnx/kiro-kontakt-patch")
FILES = [
    ROOT / "public/catalogs/KONTAKT-CATALOG.html",
    ROOT / "public/catalogs/DS-CATALOG.html",
    ROOT / "public/catalogs/KONTAKT-CATALOG-portable.html",
    ROOT / "public/catalogs/DS-CATALOG-portable.html",
]
MARK = "fix-PORTABLE-FS-FLIP-INDEX-v1"
KEEP = (
    "c00e3e",
    "fix-INDEX-ISOLATE-v3",
    "fix-INDEX-EMBED-SCROLL-v1",
    MARK,
)


def add_indent(s, n=1):
    pad = " " * n
    return "\n".join((pad + line) if line.strip() else line for line in s.split("\n"))


def sub(text, old, new, label, optional=False, replace_all=False):
    n = text.count(old)
    if n == 1 or (replace_all and n > 0):
        return text.replace(old, new)
    if n > 1:
        raise SystemExit(f"{label}: {n} matches")
    if new in text:
        print(f"  skip {label} (already)")
        return text
    for i in range(1, 9):
        oldi, newi = add_indent(old, i), add_indent(new, i)
        ni = text.count(oldi)
        if ni == 1 or (replace_all and ni > 0):
            return text.replace(oldi, newi)
        if ni > 1:
            raise SystemExit(f"{label}: {ni} matches (indent {i})")
        if ni == 0 and newi in text:
            print(f"  skip {label} (already)")
            return text
    if optional:
        print(f"  skip {label}")
        return text
    raise SystemExit(f"{label}: not found")


CSS_ADD = r"""
/* fix-PORTABLE-FS-FLIP-INDEX-v1: Flip must not block one-menu FS; Index path icons gone; embed list scrolls */
@media all{
  body.catalog-portable.display-sides #searchStrip .search-strip-fs,
  body.catalog-portable.display-sides #searchStripFs,
  body.catalog-portable.display-sides .search-strip-fs,
  body.catalog-portable.display-sides.ac-fs-open:not(.kw-fs-open) #searchStrip .search-strip-fs,
  body.catalog-portable.display-sides.ac-fs-open:not(.kw-fs-open) #searchStripFs,
  body.catalog-portable.display-sides #kwStripFs,
  body.catalog-portable.display-sides .kw-fs-btn,
  body.catalog-portable.display-middle #searchStrip .search-strip-fs,
  body.catalog-portable.display-middle #kwStripFs{
    display:inline-flex!important;visibility:visible!important;flex:0 0 auto
  }
  body.catalog-portable.display-sides.ac-fs-open:not(.kw-fs-open):not(.display-middle):not(.search-chrome-collapsed),
  body.catalog-portable.display-sides.ac-fs-open:not(.kw-fs-open):not(.display-middle).sides-portrait-flip:not(.search-chrome-collapsed):not(.kw-open),
  body.catalog-portable.display-sides.kw-fs-open:not(.ac-fs-open):not(.display-middle),
  body.catalog-portable.display-sides.kw-fs-open:not(.ac-fs-open):not(.display-middle).sides-portrait-flip{
    grid-template-columns:minmax(0,1fr)!important;
    grid-template-rows:auto minmax(0,1fr)!important;
    display:grid!important
  }
  body.catalog-portable.display-sides.ac-fs-open:not(.kw-fs-open):not(.display-middle):not(.search-chrome-collapsed) #searchChrome,
  body.catalog-portable.display-sides.ac-fs-open:not(.kw-fs-open):not(.display-middle).sides-portrait-flip:not(.search-chrome-collapsed):not(.kw-open) #searchChrome,
  body.catalog-portable.display-sides.ac-fs-open:not(.kw-fs-open):not(.display-middle):not(.search-chrome-collapsed) #acShell,
  body.catalog-portable.display-sides.ac-fs-open:not(.kw-fs-open):not(.display-middle).sides-portrait-flip:not(.search-chrome-collapsed):not(.kw-open) #acShell,
  body.catalog-portable.display-sides.ac-fs-open:not(.kw-fs-open):not(.display-middle) #acShell.ac-fs,
  body.catalog-portable.display-sides.ac-fs-open:not(.kw-fs-open):not(.display-middle).sides-portrait-flip:not(.search-chrome-collapsed):not(.kw-open) #acShell.ac-fs{
    grid-column:1/-1!important;grid-row:2!important;
    display:flex!important;flex-direction:column!important;
    width:100%!important;max-width:none!important;height:auto!important;max-height:none!important;
    min-height:0!important;position:relative!important;inset:auto!important;left:0!important;right:0!important
  }
  body.catalog-portable.display-sides.kw-fs-open:not(.ac-fs-open):not(.display-middle) #filterWrap,
  body.catalog-portable.display-sides.kw-fs-open:not(.ac-fs-open):not(.display-middle).sides-portrait-flip #filterWrap{
    grid-column:1/-1!important;grid-row:2!important;
    display:flex!important;flex-direction:column!important;
    width:100%!important;max-width:none!important;height:auto!important;max-height:none!important;
    min-height:0!important;position:relative!important;inset:auto!important
  }
  body.catalog-portable.display-sides.ac-fs-open:not(.kw-fs-open):not(.display-middle) #catalogMain,
  body.catalog-portable.display-sides.ac-fs-open:not(.kw-fs-open):not(.display-middle).sides-portrait-flip:not(.search-chrome-collapsed):not(.kw-open) #catalogMain,
  body.catalog-portable.display-sides.ac-fs-open:not(.kw-fs-open):not(.display-middle) #filterWrap,
  body.catalog-portable.display-sides.ac-fs-open:not(.kw-fs-open):not(.display-middle).sides-portrait-flip:not(.search-chrome-collapsed):not(.kw-open) #filterWrap,
  body.catalog-portable.display-sides.kw-fs-open:not(.ac-fs-open):not(.display-middle) #catalogMain,
  body.catalog-portable.display-sides.kw-fs-open:not(.ac-fs-open):not(.display-middle) #searchChrome,
  body.catalog-portable.display-sides.kw-fs-open:not(.ac-fs-open):not(.display-middle).sides-portrait-flip #catalogMain,
  body.catalog-portable.display-sides.kw-fs-open:not(.ac-fs-open):not(.display-middle).sides-portrait-flip #searchChrome{
    display:none!important
  }
}
@media(orientation:landscape){
  body.catalog-portable.display-sides.ac-fs-open:not(.kw-fs-open):not(.display-middle).sides-portrait-flip:not(.search-chrome-collapsed):not(.kw-open),
  body.catalog-portable.display-sides.kw-fs-open:not(.ac-fs-open):not(.display-middle).sides-portrait-flip{
    grid-template-columns:minmax(0,1fr)!important;
    grid-template-rows:auto minmax(0,1fr)!important
  }
  body.catalog-portable.display-sides.ac-fs-open:not(.kw-fs-open):not(.display-middle).sides-portrait-flip:not(.search-chrome-collapsed):not(.kw-open) #searchChrome,
  body.catalog-portable.display-sides.ac-fs-open:not(.kw-fs-open):not(.display-middle).sides-portrait-flip:not(.search-chrome-collapsed):not(.kw-open) #acShell,
  body.catalog-portable.display-sides.ac-fs-open:not(.kw-fs-open):not(.display-middle).sides-portrait-flip:not(.search-chrome-collapsed):not(.kw-open) #acShell.ac-fs{
    grid-column:1/-1!important;grid-row:2!important;width:100%!important;max-width:none!important
  }
  body.catalog-portable.display-sides.ac-fs-open:not(.kw-fs-open):not(.display-middle).sides-portrait-flip:not(.search-chrome-collapsed):not(.kw-open) #catalogMain,
  body.catalog-portable.display-sides.ac-fs-open:not(.kw-fs-open):not(.display-middle).sides-portrait-flip:not(.search-chrome-collapsed):not(.kw-open) #filterWrap{
    display:none!important
  }
}
#catalogIndex * .path-icon-btn,
#catalogIndex .path-icon-btn,
#catalogIndexList .path-icon-btn,
.index li .path-icon-btn,
.index li .path-action-row,
.index li .path-label,
#catalogIndex .path-action-row,
#catalogIndexList .path-action-row,
#catalogIndex a.folder:not([href^="#"]),
#catalogIndexList a.folder:not([href^="#"]),
.index li a.folder:not([href^="#"]),
#catalogIndex .path-fs-hit,
#catalogIndex .path-copy-hit,
#catalogIndex svg.path-icon-glyph,
#catalogIndex img.path-icon-glyph{
  display:none!important;visibility:hidden!important;pointer-events:none!important;
  width:0!important;height:0!important;min-width:0!important;min-height:0!important;
  overflow:hidden!important;opacity:0!important;position:absolute!important
}
body.display-sides #catalogIndex.is-embedded,
body.display-middle #catalogIndex.is-embedded,
body.catalog-portable #catalogIndex.is-embedded,
#catalogIndex.is-embedded,
#catalogIndex.is-embedded:not(.is-collapsed),
body.display-sides #catalogIndex.is-embedded:not(.is-collapsed),
.catalog-body>#catalogIndex.is-embedded{
  overflow:visible!important;overflow-y:visible!important;height:auto!important;max-height:none!important
}
body.display-sides #catalogIndex.is-embedded:not(.is-collapsed) .index,
body.display-sides #catalogIndex.is-embedded:not(.is-collapsed) #catalogIndexList,
body.display-middle #catalogIndex.is-embedded:not(.is-collapsed) .index,
body.display-middle #catalogIndex.is-embedded:not(.is-collapsed) #catalogIndexList,
body.catalog-portable #catalogIndex.is-embedded:not(.is-collapsed) .index,
body.catalog-portable #catalogIndex.is-embedded:not(.is-collapsed) #catalogIndexList,
#catalogIndex.is-embedded:not(.is-collapsed) .index,
#catalogIndex.is-embedded:not(.is-collapsed) #catalogIndexList{
  overflow:visible!important;overflow-x:hidden!important;overflow-y:visible!important;
  height:auto!important;max-height:none!important;flex:0 0 auto!important
}
"""

STRIP_OLD = """function stripIndexCardChrome(ix){
  ix=ix||document.getElementById('catalogIndex');
  var list=document.getElementById('catalogIndexList');
  var roots=[];
  if(ix)roots.push(ix);
  if(list&&roots.indexOf(list)<0&&!(ix&&ix.contains(list)))roots.push(list);
  var sel='.path-action-row,.path-icon-btn,.path-label,.path-fs-hit,.path-copy-hit,.fav-btn,a.folder,.path,svg.path-icon-glyph,img.path-icon-glyph';
  roots.forEach(function(root){
    root.querySelectorAll(sel).forEach(function(el){
      try{el.remove();}catch(err){
        el.style.setProperty('display','none','important');
        el.style.setProperty('visibility','hidden','important');
        el.style.setProperty('pointer-events','none','important');
        el.setAttribute('hidden','');
      }
    });
  });
}"""

STRIP_NEW = """function stripIndexCardChrome(ix){
  if(stripIndexCardChrome._busy)return;
  stripIndexCardChrome._busy=true;
  try{
    ix=ix||document.getElementById('catalogIndex');
    var list=document.getElementById('catalogIndexList')||(ix&&ix.querySelector('ul.index,#catalogIndexList'));
    var roots=[];
    if(ix)roots.push(ix);
    if(list&&roots.indexOf(list)<0&&!(ix&&ix.contains(list)))roots.push(list);
    var sel='.path-action-row,.path-icon-btn,.path-label,.path-fs-hit,.path-copy-hit,.fav-btn,a.folder,.path,svg.path-icon-glyph,img.path-icon-glyph';
    function drop(el){
      if(!el||(el.matches&&el.matches('a[href^="#"]')))return;
      try{el.remove();}catch(err){
        el.style.setProperty('display','none','important');
        el.style.setProperty('visibility','hidden','important');
        el.style.setProperty('pointer-events','none','important');
        el.setAttribute('hidden','');
      }
    }
    roots.forEach(function(root){
      root.querySelectorAll(sel).forEach(drop);
      root.querySelectorAll('li').forEach(function(li){
        if(!(li.closest&&li.closest('#catalogIndex,ul.index,#catalogIndexList')))return;
        [].slice.call(li.children).forEach(function(el){
          if(el.matches&&el.matches('a[href^="#"]'))return;
          drop(el);
        });
        li.querySelectorAll('button,svg,img,.path-icon-btn,.path-action-row,.path-label,a.folder').forEach(function(el){
          if(el.matches&&el.matches('a[href^="#"]'))return;
          drop(el);
        });
      });
    });
    if(typeof bindIndexPathIconWatch==='function')bindIndexPathIconWatch();
  }finally{stripIndexCardChrome._busy=false;}
}
function bindIndexPathIconWatch(){
  if(bindIndexPathIconWatch._on)return;
  var ix=document.getElementById('catalogIndex');
  if(!ix||typeof MutationObserver!=='function')return;
  bindIndexPathIconWatch._on=true;
  var mo=new MutationObserver(function(){
    if(stripIndexCardChrome._busy)return;
    if(typeof stripIndexCardChrome==='function')stripIndexCardChrome(ix);
  });
  mo.observe(ix,{childList:true,subtree:true});
}"""

BIND_SKIP_OLD = """document.querySelectorAll('.entry .path').forEach(function(p){
    if(p.closest&&p.closest('#catalogIndex,.catalog-index,#catalogIndexList,ul.index'))return;"""

BIND_SKIP_NEW = """document.querySelectorAll('.entry .path').forEach(function(p){
    if(p.closest&&p.closest('#catalogIndex,.catalog-index,#catalogIndexList,ul.index,.index li'))return;"""

CLEAR_OLD = """function clearChromeInlineLeftovers(){
  var ch=document.getElementById('searchChrome');
  var had=ch?((ch.getAttribute('style')||'')+''):'';
  if(ch){
    ch.style.removeProperty('grid-template-columns');
    ch.style.removeProperty('grid-template-rows');
    ch.style.removeProperty('height');
    ch.style.removeProperty('max-height');"""

CLEAR_NEW = """function clearChromeInlineLeftovers(){
  var ch=document.getElementById('searchChrome');
  var had=ch?((ch.getAttribute('style')||'')+''):'';
  var menuFs=!!(document.body.classList.contains('ac-fs-open')||document.body.classList.contains('kw-fs-open'));
  if(ch&&!menuFs){
    ch.style.removeProperty('grid-template-columns');
    ch.style.removeProperty('grid-template-rows');
    ch.style.removeProperty('height');
    ch.style.removeProperty('max-height');"""

ENTER_OLD = """function portableEnterMenuFs(which){
  if(!portableMenuFsOn())portableMenuFsPrev=portableSaveMenuCombo();
  portableMenuFsHold=which;
  document.body.classList.remove('dual-fs-open');
  if(which==='search'){
    document.body.classList.add('ac-fs-open');
    document.body.classList.remove('kw-fs-open','search-chrome-collapsed');
    if(typeof acFsWanted!=='undefined')acFsWanted=true;
    if(typeof kwFsWanted!=='undefined')kwFsWanted=false;
    var sh=document.getElementById('acShell');
    if(sh){sh.classList.add('open','ac-fs');}
    var ac=document.getElementById('acList');
    if(ac)ac.classList.add('open');
  }else{
    document.body.classList.add('kw-fs-open','kw-open');
    document.body.classList.remove('ac-fs-open','kw-chrome-collapsed');
    if(typeof kwFsWanted!=='undefined')kwFsWanted=true;
    if(typeof acFsWanted!=='undefined')acFsWanted=false;
    var fw=document.getElementById('filterWrap');
    if(fw)fw.classList.add('open');
    var sh2=document.getElementById('acShell');
    if(sh2)sh2.classList.remove('ac-fs');
  }
  if(document.body.classList.contains('display-middle')){
    var hdrF=document.querySelector('.catalog-header');
    var topF=hdrF?Math.round(hdrF.getBoundingClientRect().bottom):56;
    var fillH=Math.max(160,(window.innerHeight||800)-topF);
    document.body.style.setProperty('grid-template-rows','auto minmax(0,1fr)','important');
    document.body.style.setProperty('grid-template-columns','minmax(0,1fr)','important');
    var fillEl=which==='keywords'?document.getElementById('filterWrap'):document.getElementById('searchChrome');
    if(fillEl){
      fillEl.style.setProperty('max-height','none','important');
      fillEl.style.setProperty('height',fillH+'px','important');
      fillEl.style.setProperty('grid-row','2','important');
      fillEl.style.setProperty('grid-column','1 / -1','important');
      fillEl.style.setProperty('align-self','stretch','important');
    }
  }"""

ENTER_NEW = """function portableApplyMenuFsLayout(which){
  if(!window.CATALOG_PORTABLE||!document.body.classList.contains('display-sides'))return;
  if(document.body.classList.contains('dual-fs-open'))return;
  var hdrF=document.querySelector('.catalog-header');
  var topF=hdrF?Math.round(hdrF.getBoundingClientRect().bottom):56;
  var fillH=Math.max(160,(window.innerHeight||800)-topF);
  document.body.style.setProperty('grid-template-rows','auto minmax(0,1fr)','important');
  document.body.style.setProperty('grid-template-columns','minmax(0,1fr)','important');
  var fillEl=which==='keywords'?document.getElementById('filterWrap'):document.getElementById('searchChrome');
  var hideEl=which==='keywords'?document.getElementById('searchChrome'):document.getElementById('filterWrap');
  var main=document.getElementById('catalogMain');
  if(fillEl){
    fillEl.style.setProperty('display','flex','important');
    fillEl.style.setProperty('max-height','none','important');
    fillEl.style.setProperty('height',fillH+'px','important');
    fillEl.style.setProperty('grid-row','2','important');
    fillEl.style.setProperty('grid-column','1 / -1','important');
    fillEl.style.setProperty('align-self','stretch','important');
    fillEl.style.setProperty('width','100%','important');
    fillEl.style.setProperty('max-width','none','important');
  }
  if(hideEl)hideEl.style.setProperty('display','none','important');
  if(main)main.style.setProperty('display','none','important');
  var sh=document.getElementById('acShell');
  if(which==='search'&&sh){
    sh.classList.add('open','ac-fs');
    sh.style.setProperty('grid-column','1 / -1','important');
    sh.style.setProperty('width','100%','important');
    sh.style.setProperty('max-width','none','important');
  }
}
function portableEnterMenuFs(which){
  if(!portableMenuFsOn())portableMenuFsPrev=portableSaveMenuCombo();
  portableMenuFsHold=which;
  document.body.classList.remove('dual-fs-open');
  if(which==='search'){
    document.body.classList.add('ac-fs-open');
    document.body.classList.remove('kw-fs-open','search-chrome-collapsed');
    if(typeof acFsWanted!=='undefined')acFsWanted=true;
    if(typeof kwFsWanted!=='undefined')kwFsWanted=false;
    var sh=document.getElementById('acShell');
    if(sh){sh.classList.add('open','ac-fs');}
    var ac=document.getElementById('acList');
    if(ac)ac.classList.add('open');
  }else{
    document.body.classList.add('kw-fs-open','kw-open');
    document.body.classList.remove('ac-fs-open','kw-chrome-collapsed');
    if(typeof kwFsWanted!=='undefined')kwFsWanted=true;
    if(typeof acFsWanted!=='undefined')acFsWanted=false;
    var fw=document.getElementById('filterWrap');
    if(fw)fw.classList.add('open');
    var sh2=document.getElementById('acShell');
    if(sh2)sh2.classList.remove('ac-fs');
  }
  portableApplyMenuFsLayout(which);"""

ENTER_END_OLD = """  if(typeof dbgFsFlipSnap==='function')dbgFsFlipSnap('menu-fs-in',which);

  // #endregion
}"""

ENTER_END_NEW = """  if(typeof dbgFsFlipSnap==='function')dbgFsFlipSnap('menu-fs-in',which);
  if(typeof portableApplyMenuFsLayout==='function')portableApplyMenuFsLayout(which);

  // #endregion
}"""

EXIT_OLD = """  document.body.style.removeProperty('grid-template-rows');
  document.body.style.removeProperty('grid-template-columns');
  ['filterWrap','searchChrome'].forEach(function(id){
    var el=document.getElementById(id);
    if(!el)return;
    el.style.removeProperty('height');
    el.style.removeProperty('max-height');
    el.style.removeProperty('grid-row');
    el.style.removeProperty('grid-column');
    el.style.removeProperty('align-self');
  });"""

EXIT_NEW = """  document.body.style.removeProperty('grid-template-rows');
  document.body.style.removeProperty('grid-template-columns');
  ['filterWrap','searchChrome','catalogMain','acShell'].forEach(function(id){
    var el=document.getElementById(id);
    if(!el)return;
    el.style.removeProperty('height');
    el.style.removeProperty('max-height');
    el.style.removeProperty('grid-row');
    el.style.removeProperty('grid-column');
    el.style.removeProperty('align-self');
    el.style.removeProperty('display');
    el.style.removeProperty('width');
    el.style.removeProperty('max-width');
  });"""

BOOT_OLD = """  if(typeof forceCatalogIndexClosed==='function')forceCatalogIndexClosed('boot');"""
BOOT_NEW = """  if(typeof stripIndexCardChrome==='function')try{stripIndexCardChrome();}catch(eIxBoot){}
  if(typeof forceCatalogIndexClosed==='function')forceCatalogIndexClosed('boot');"""


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
    text = sub(text, STRIP_OLD, STRIP_NEW, f"{n}: strip")
    text = sub(text, BIND_SKIP_OLD, BIND_SKIP_NEW, f"{n}: bind-skip", replace_all=True)
    text = sub(text, CLEAR_OLD, CLEAR_NEW, f"{n}: clear-fs")
    text = sub(
        text,
        "  var fw=document.getElementById('filterWrap');\n  if(fw&&!document.body.classList.contains('display-fs')){",
        "  var fw=document.getElementById('filterWrap');\n  if(fw&&!document.body.classList.contains('display-fs')&&!document.body.classList.contains('kw-fs-open')&&!document.body.classList.contains('ac-fs-open')){",
        f"{n}: clear-fw-fs",
    )
    portable = "portable" in n
    text = sub(text, ENTER_OLD, ENTER_NEW, f"{n}: enter-fs", optional=not portable)
    text = sub(text, ENTER_END_OLD, ENTER_END_NEW, f"{n}: enter-fs-end", optional=not portable)
    text = sub(text, EXIT_OLD, EXIT_NEW, f"{n}: exit-fs", optional=not portable)
    text = sub(text, BOOT_OLD, BOOT_NEW, f"{n}: boot-strip", optional=True)
    raw = text.encode("utf-8")
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_bytes(raw)
    out = tmp.read_bytes().decode("utf-8")
    if not out.strip().endswith("</html>"):
        tmp.unlink()
        raise SystemExit(f"{n}: truncated")
    if len(raw) < 100000:
        tmp.unlink()
        raise SystemExit(f"{n}: size too small {len(raw)}")
    for keep in KEEP:
        if keep not in out:
            tmp.unlink()
            raise SystemExit(f"{n}: lost {keep}")
    if "c00e3e" not in out:
        tmp.unlink()
        raise SystemExit(f"{n}: lost c00e3e logs")
    tmp.replace(path)
    print("OK", n, len(raw))


def main() -> None:
    for p in FILES:
        if not p.exists():
            raise SystemExit(f"missing {p}")
        patch(p)


if __name__ == "__main__":
    main()
