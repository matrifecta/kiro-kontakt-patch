#!/usr/bin/env python3
"""Mobile portable polish: notch titles, content-chrome hide, Index gap,
Keywords label, restore menu FS, no Search autofocus, drop FS from Search ⋯.
"""
from pathlib import Path

ROOT = Path("/home/phnx/kiro-kontakt-patch/public/catalogs")
FILES = [
    ROOT / "KONTAKT-CATALOG-portable.html",
    ROOT / "DS-CATALOG-portable.html",
]

TITLE_OLD = """  body.catalog-portable .catalog-header h1#top{
    display:grid!important;grid-template-columns:minmax(0,1fr) minmax(0,1fr)!important;
    align-items:center;column-gap:0;width:100%!important;max-width:none!important;
    overflow:visible!important;text-overflow:clip!important;white-space:nowrap
  }
  body.catalog-portable .catalog-header h1#top .hdr-title-lead{
    grid-column:1;justify-self:center;text-align:center;min-width:0
  }
  body.catalog-portable .catalog-header h1#top .hdr-title-tail{
    grid-column:2;justify-self:center;text-align:center;min-width:0
  }
"""

TITLE_NEW = """  body.catalog-portable .catalog-header h1#top{
    display:grid!important;grid-template-columns:minmax(0,1fr) minmax(0,1fr)!important;
    align-items:center;column-gap:max(2.8rem,16vw);width:100%!important;max-width:none!important;
    overflow:visible!important;text-overflow:clip!important;white-space:nowrap
  }
  body.catalog-portable .catalog-header h1#top .hdr-title-lead{
    grid-column:1;justify-self:start;text-align:left;min-width:0;
    padding-left:max(.55rem,env(safe-area-inset-left,0px))
  }
  body.catalog-portable .catalog-header h1#top .hdr-title-tail{
    grid-column:2;justify-self:end;text-align:right;min-width:0;
    padding-right:max(.55rem,env(safe-area-inset-right,0px))
  }
"""

EDGE_SHOW_OLD = """  body.catalog-portable.display-sides #catalogEdgeStack{
    display:flex!important;position:fixed!important;z-index:46!important;
    flex-direction:column;align-items:flex-start;gap:.4rem;pointer-events:none;
    width:max-content;height:auto;overflow:visible
  }
  body.catalog-portable.display-fs #catalogEdgeStack,
  body.catalog-portable.display-sides.dual-fs-open #catalogEdgeStack,
  body.catalog-portable.display-sides.ac-fs-open.kw-fs-open #catalogEdgeStack{
    display:none!important
  }
"""

EDGE_SHOW_NEW = """  body.catalog-portable.content-window-on #catalogEdgeStack,
  body.catalog-portable.display-sides #catalogEdgeStack,
  body.catalog-portable.display-middle #catalogEdgeStack{
    display:flex!important;position:fixed!important;z-index:46!important;
    flex-direction:column;align-items:flex-start;gap:.4rem;pointer-events:none;
    width:max-content;height:auto;overflow:visible
  }
  body.catalog-portable.display-fs #catalogEdgeStack,
  body.catalog-portable.ac-fs-open #catalogEdgeStack,
  body.catalog-portable.kw-fs-open #catalogEdgeStack,
  body.catalog-portable.dual-fs-open #catalogEdgeStack,
  body.catalog-portable:not(.content-window-on) #catalogEdgeStack{
    display:none!important
  }
"""

JUMP_SHOW_OLD = """  body.catalog-portable.display-sides #catalogJumpStack,
  body.catalog-portable.display-middle #catalogJumpStack{
"""

JUMP_SHOW_NEW = """  body.catalog-portable.content-window-on #catalogJumpStack,
  body.catalog-portable.display-sides #catalogJumpStack,
  body.catalog-portable.display-middle #catalogJumpStack{
"""

JUMP_HIDE_OLD = """  body.catalog-portable.display-fs #catalogJumpStack,
  body.catalog-portable.display-sides.dual-fs-open #catalogJumpStack,
  body.catalog-portable.display-sides.ac-fs-open.kw-fs-open #catalogJumpStack{
    display:none!important
  }
"""

JUMP_HIDE_NEW = """  body.catalog-portable.display-fs #catalogJumpStack,
  body.catalog-portable.ac-fs-open #catalogJumpStack,
  body.catalog-portable.kw-fs-open #catalogJumpStack,
  body.catalog-portable.dual-fs-open #catalogJumpStack,
  body.catalog-portable:not(.content-window-on) #catalogJumpStack{
    display:none!important
  }
"""

CSS_TAIL = r"""
/* fix-PORTABLE-MOBILE-POLISH-v1: FS in all modes; Index gap; hide chrome when content off */
html body.catalog-portable .search-strip-fs,
html body.catalog-portable #searchStripFs,
html body.catalog-portable #searchStrip .search-strip-fs,
html body.catalog-portable #kwStripFs,
html body.catalog-portable #filterWrap .kw-fs-btn,
html body.catalog-portable #filterTop > #kwStripFs,
html body.catalog-portable.display-sides .search-strip-fs,
html body.catalog-portable.display-sides #kwStripFs,
html body.catalog-portable.display-middle .search-strip-fs,
html body.catalog-portable.display-middle #kwStripFs,
html body.catalog-portable.display-content .search-strip-fs,
html body.catalog-portable.display-content #kwStripFs,
html body.catalog-portable:not(.display-sides):not(.display-middle):not(.display-fs) .search-strip-fs,
html body.catalog-portable:not(.display-sides):not(.display-middle):not(.display-fs) #kwStripFs{
  display:inline-flex!important;visibility:visible!important;opacity:1!important;
  width:auto!important;min-width:2.75rem!important;max-width:none!important;
  height:auto!important;min-height:2.75rem!important;margin:0!important;
  padding:0 .45rem!important;border-width:1px!important;overflow:visible!important;
  pointer-events:auto!important
}
html body.catalog-portable.kw-fs-open #kwStripFs,
html body.catalog-portable.kw-fs-open #filterTop > #kwStripFs,
html body.catalog-portable.ac-fs-open #searchStripFs,
html body.catalog-portable.ac-fs-open .search-ac-shell.ac-fs>.search-strip .search-strip-fs{
  display:none!important
}
html body.catalog-portable.ac-fs-open #catalogIndex,
html body.catalog-portable.kw-fs-open #catalogIndex,
html body.catalog-portable.dual-fs-open #catalogIndex,
html body.catalog-portable.display-fs #catalogIndex,
html body.catalog-portable:not(.content-window-on) #catalogIndex{
  visibility:hidden!important;pointer-events:none!important
}
html body.catalog-portable.content-window-on #catalogIndex{
  visibility:visible!important;pointer-events:auto!important
}
html body.catalog-portable #catalogMain>#catalogIndex:not(.is-embedded),
html body.catalog-portable.display-sides #catalogMain>#catalogIndex:not(.is-embedded),
html body.catalog-portable.display-middle #catalogMain>#catalogIndex:not(.is-embedded),
html body.catalog-portable.index-window-open #catalogIndex.is-collapsed:not(.is-embedded){
  margin-bottom:1.35rem!important
}
html body.catalog-portable #catalogMain>.catalog-body>h2:first-of-type{
  margin-top:.45rem!important;padding-top:.2rem!important
}
"""

HELPER = r"""function catalogContentWindowOnScreen(){
  var b=document.body;
  if(b.classList.contains('ac-fs-open')||b.classList.contains('kw-fs-open')||b.classList.contains('dual-fs-open')||b.classList.contains('display-fs'))return false;
  var main=document.getElementById('catalogMain');
  if(!main)return false;
  var cs=getComputedStyle(main);
  if(cs.display==='none'||cs.visibility==='hidden')return false;
  var r=main.getBoundingClientRect();
  return !!(r&&r.width>=24&&r.height>=48);
}
function syncCatalogContentWindowClass(){
  var on=catalogContentWindowOnScreen();
  document.body.classList.toggle('content-window-on',on);
  // #region agent log
  try{
    var ix=document.getElementById('catalogIndex');
    var lead=document.querySelector('.hdr-title-lead');
    var tail=document.querySelector('.hdr-title-tail');
    var lr=lead?lead.getBoundingClientRect():null;
    var tr=tail?tail.getBoundingClientRect():null;
    fetch('http://127.0.0.1:7529/ingest/1cf46354-1d61-4c80-bd72-a340f1db1b51',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'c00e3e'},body:JSON.stringify({sessionId:'c00e3e',runId:'mob-polish',hypothesisId:'M1-M5',location:'syncCatalogContentWindowClass',message:'content-window',data:{on:on,portable:!!window.CATALOG_PORTABLE,orient:(innerWidth>=innerHeight?'land':'port'),vw:innerWidth,vh:innerHeight,sides:document.body.classList.contains('display-sides'),middle:document.body.classList.contains('display-middle'),acFs:document.body.classList.contains('ac-fs-open'),kwFs:document.body.classList.contains('kw-fs-open'),kwLabel:((document.getElementById('filterToggle')||{}).textContent||'').replace(/\s+/g,' ').trim(),sfs:!!(document.getElementById('searchStripFs')&&getComputedStyle(document.getElementById('searchStripFs')).display!=='none'),kfs:!!(document.getElementById('kwStripFs')&&getComputedStyle(document.getElementById('kwStripFs')).display!=='none'),lead:lr?{t:lead.textContent,x:Math.round(lr.left),r:Math.round(lr.right)}:null,tail:tr?{t:tail.textContent,x:Math.round(tr.left),r:Math.round(tr.right)}:null,ixB:ix?Math.round(ix.getBoundingClientRect().bottom):null},timestamp:Date.now()})}).catch(function(){});
  }catch(errCw){}
  // #endregion
  return on;
}
window.catalogContentWindowOnScreen=catalogContentWindowOnScreen;
window.syncCatalogContentWindowClass=syncCatalogContentWindowClass;
"""

JUMP_HIDE_LINE_OLD = "  var mainHide=!main||fs||!(sides||middle)||(mainCs&&mainCs.display==='none')||!r||r.width<8||r.height<8;\n"

JUMP_HIDE_LINE_NEW = """  if(typeof syncCatalogContentWindowClass==='function')syncCatalogContentWindowClass();
  var on=typeof catalogContentWindowOnScreen==='function'?catalogContentWindowOnScreen():((sides||middle)&&!fs);
  var mainHide=!on||!main||(mainCs&&mainCs.display==='none')||!r||r.width<8||r.height<8;
"""

EDGE_HIDE_OLD = "  var hide=!main||(!helpOn&&(fs||!(sides||middle)))||(cs&&cs.display==='none')||!r||r.width<8||r.height<8;\n"

EDGE_HIDE_NEW = """  if(typeof syncCatalogContentWindowClass==='function')syncCatalogContentWindowClass();
  var paneOn=typeof catalogContentWindowOnScreen==='function'?catalogContentWindowOnScreen():((sides||middle)&&!fs);
  var hide=!main||(!helpOn&&!paneOn)||(cs&&cs.display==='none')||!r||r.width<8||r.height<8;
"""

FOCUS_EXPAND_OLD = """  var si=document.getElementById('searchInput');
  if(si&&!document.body.classList.contains('ac-fs-open'))setTimeout(function(){si.focus();if(typeof ensureSearchList==='function')ensureSearchList('expand-focus');},50);
"""

FOCUS_EXPAND_NEW = """  if(!window.CATALOG_PORTABLE){
    var si=document.getElementById('searchInput');
    if(si&&!document.body.classList.contains('ac-fs-open'))setTimeout(function(){si.focus();if(typeof ensureSearchList==='function')ensureSearchList('expand-focus');},50);
  }else if(typeof ensureSearchList==='function')ensureSearchList('expand-nofocus');
"""

FOCUS_MODE_OLD = "setTimeout(function(){var si=document.getElementById('searchInput');if(si&&!document.body.classList.contains('ac-fs-open'))si.focus();},50);"

FOCUS_MODE_NEW = "if(!window.CATALOG_PORTABLE)setTimeout(function(){var si=document.getElementById('searchInput');if(si&&!document.body.classList.contains('ac-fs-open'))si.focus();},50);"

FS_MORE_OLD = "    portableMoreRowAdd(pop,'Fullscreen',function(){if(typeof toggleAcFullscreen==='function')toggleAcFullscreen();},'Fullscreen Search');\n"

FS_MORE_NEW = "    /* keep Search ⋯ pop for later items; Fullscreen lives on the strip ⛶ */\n"


def safe_write(path: Path, text: str) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    out = tmp.read_text(encoding="utf-8")
    if not out.rstrip().endswith("</html>"):
        tmp.unlink(missing_ok=True)
        raise SystemExit(f"{path.name}: rewrite would drop </html>")
    path.write_text(out, encoding="utf-8")
    tmp.unlink(missing_ok=True)


def once(text: str, old: str, new: str, label: str, name: str) -> str:
    if old not in text:
        if new in text or (label == "fs-more" and "keep Search" in text):
            print(f"  skip {label} {name}")
            return text
        raise SystemExit(f"{name}: missing {label}: {old[:80]!r}")
    n = text.count(old)
    text = text.replace(old, new)
    print(f"  {n}x {label} {name}")
    return text


def patch(path: Path) -> None:
    name = path.name
    text = path.read_text(encoding="utf-8")
    text = once(text, TITLE_OLD, TITLE_NEW, "title", name)
    text = once(text, EDGE_SHOW_OLD, EDGE_SHOW_NEW, "edge-show", name)
    text = once(text, JUMP_SHOW_OLD, JUMP_SHOW_NEW, "jump-show", name)
    text = once(text, JUMP_HIDE_OLD, JUMP_HIDE_NEW, "jump-hide", name)
    if "fix-PORTABLE-MOBILE-POLISH-v1" not in text:
        mark = "/* fix-TAP-ADD-REMOVE-v1: Tap to add is redundant with default KW/search add */"
        if mark not in text:
            raise SystemExit(f"{name}: tail mark missing")
        text = text.replace(mark, CSS_TAIL + "\n" + mark, 1)
        print(f"  1x css-tail {name}")
    else:
        print(f"  skip css-tail {name}")
    text = once(text, '<span class="toggle-arrow">&#9660;</span> KW</button>', '<span class="toggle-arrow">&#9660;</span> Keywords</button>', "kw-html", name)
    text = once(text, "b.textContent=hidden?(window.CATALOG_PORTABLE?'KW':'Keywords'):(window.CATALOG_PORTABLE?'Hide':'Hide Keywords');", "b.textContent=hidden?'Keywords':'Hide';", "kw-hide", name)
    text = once(text, FS_MORE_OLD, FS_MORE_NEW, "fs-more", name)
    text = once(text, FOCUS_EXPAND_OLD, FOCUS_EXPAND_NEW, "focus-expand", name)
    text = once(text, FOCUS_MODE_OLD, FOCUS_MODE_NEW, "focus-mode", name)
    if "function catalogContentWindowOnScreen()" not in text:
        text = once(text, "function placeCatalogJumpStack(){", HELPER + "function placeCatalogJumpStack(){", "helper", name)
    else:
        print(f"  skip helper {name}")
    text = once(text, JUMP_HIDE_LINE_OLD, JUMP_HIDE_LINE_NEW, "jump-js", name)
    text = once(text, EDGE_HIDE_OLD, EDGE_HIDE_NEW, "edge-js", name)
    if "fix-PORTABLE-MOBILE-POLISH-v1" not in text:
        raise SystemExit(f"{name}: polish css missing")
    if "function catalogContentWindowOnScreen()" not in text:
        raise SystemExit(f"{name}: helper missing")
    safe_write(path, text)
    print(f"ok {name} bytes={path.stat().st_size}")


def main() -> None:
    for p in FILES:
        print("==", p.name)
        patch(p)


if __name__ == "__main__":
    main()
