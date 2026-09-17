#!/usr/bin/env python3
"""Opaque scrolling Index (no card PATH punch-through); portable KW-FS hide, no folder, titles."""
from pathlib import Path

ROOT = Path("/home/phnx/kiro-kontakt-patch/public/catalogs")
ALL = [
    ROOT / "KONTAKT-CATALOG.html",
    ROOT / "DS-CATALOG.html",
    ROOT / "KONTAKT-CATALOG-portable.html",
    ROOT / "DS-CATALOG-portable.html",
]
PORTABLE = [
    ROOT / "KONTAKT-CATALOG-portable.html",
    ROOT / "DS-CATALOG-portable.html",
]

MARK = "fix-INDEX-OPAQUE-SCROLL-v2"
MARK_OLD = "fix-INDEX-OPAQUE-SCROLL-v1"
CSS = r"""
/* fix-INDEX-OPAQUE-SCROLL-v2: Window fills pane and scrolls; Embed stays in-flow, opaque, min-content (no overflow:hidden collapse) */
body.index-window-open #catalogMain>#catalogIndex:not(.is-embedded):not(.is-collapsed),
body.display-sides.index-window-open #catalogMain>#catalogIndex:not(.is-embedded):not(.is-collapsed),
body.display-middle.index-window-open #catalogMain>#catalogIndex:not(.is-embedded):not(.is-collapsed),
body.catalog-portable.index-window-open #catalogMain>#catalogIndex:not(.is-embedded):not(.is-collapsed){
  position:absolute!important;inset:0!important;top:0!important;left:0!important;right:0!important;bottom:0!important;
  width:auto!important;max-width:none!important;height:auto!important;max-height:none!important;min-height:0!important;
  overflow:hidden!important;isolation:isolate!important;background:var(--bg-surface)!important;
  display:flex!important;flex-direction:column!important;z-index:46!important;pointer-events:auto!important;
  margin:0!important;box-shadow:none!important
}
body.index-window-open #catalogIndex:not(.is-embedded):not(.is-collapsed) .index,
body.index-window-open #catalogIndex:not(.is-embedded):not(.is-collapsed) #catalogIndexList,
body.display-sides.index-window-open #catalogIndex:not(.is-embedded):not(.is-collapsed) .index,
body.display-sides.index-window-open #catalogIndex:not(.is-embedded):not(.is-collapsed) #catalogIndexList{
  flex:1 1 auto!important;min-height:0!important;height:auto!important;max-height:none!important;
  overflow-x:hidden!important;overflow-y:auto!important;background:var(--bg-surface)!important;
  isolation:isolate!important;-webkit-overflow-scrolling:touch
}
body.index-window-open #catalogJumpStack,
body:has(#catalogIndex.is-embedded:not(.is-collapsed)) #catalogJumpStack{
  display:none!important
}
body.display-sides #catalogMain>.catalog-body>#catalogIndex.is-embedded:not(.is-collapsed),
body.display-sides #catalogMain .catalog-body>#catalogIndex.is-embedded:not(.is-collapsed),
body.display-middle #catalogMain>.catalog-body>#catalogIndex.is-embedded:not(.is-collapsed),
body.catalog-portable #catalogMain>.catalog-body>#catalogIndex.is-embedded:not(.is-collapsed),
#catalogMain>.catalog-body>#catalogIndex.is-embedded:not(.is-collapsed),
#catalogIndex.is-embedded:not(.is-collapsed){
  height:auto!important;max-height:calc(100dvh - 11rem)!important;min-height:10rem!important;
  overflow:hidden!important;isolation:isolate!important;background:var(--bg-surface)!important;
  display:flex!important;flex-direction:column!important;position:relative!important;
  grid-column:1/-1!important;align-self:stretch!important;justify-self:stretch!important;
  z-index:45!important;flex:0 0 auto!important;pointer-events:auto!important
}
body.display-sides #catalogIndex.is-embedded:not(.is-collapsed) .index,
body.display-sides #catalogIndex.is-embedded:not(.is-collapsed) #catalogIndexList,
body.display-sides #catalogMain .catalog-body>#catalogIndex.is-embedded:not(.is-collapsed) .index,
body.display-sides #catalogMain .catalog-body>#catalogIndex.is-embedded:not(.is-collapsed) #catalogIndexList,
body.display-middle #catalogIndex.is-embedded:not(.is-collapsed) .index,
body.display-middle #catalogIndex.is-embedded:not(.is-collapsed) #catalogIndexList,
#catalogMain>.catalog-body>#catalogIndex.is-embedded:not(.is-collapsed) .index,
#catalogMain>.catalog-body>#catalogIndex.is-embedded:not(.is-collapsed) #catalogIndexList,
#catalogIndex.is-embedded:not(.is-collapsed) .index,
#catalogIndex.is-embedded:not(.is-collapsed) #catalogIndexList{
  flex:1 1 auto!important;height:auto!important;max-height:none!important;min-height:0!important;
  overflow-x:hidden!important;overflow-y:auto!important;
  background:var(--bg-surface)!important;isolation:isolate!important
}
#catalogIndex .index li,#catalogIndexList li{
  background:var(--bg-surface)!important
}
body.display-sides:has(#catalogIndex.is-embedded:not(.is-collapsed)) #catalogMain,
body.display-middle:has(#catalogIndex.is-embedded:not(.is-collapsed)) #catalogMain,
body.catalog-portable:has(#catalogIndex.is-embedded:not(.is-collapsed)) #catalogMain{
  overflow-x:hidden!important;overflow-y:auto!important;min-height:0!important
}
body.display-sides:has(#catalogIndex.is-embedded:not(.is-collapsed)) #catalogMain>.catalog-body,
body.display-middle:has(#catalogIndex.is-embedded:not(.is-collapsed)) #catalogMain>.catalog-body,
body.catalog-portable:has(#catalogIndex.is-embedded:not(.is-collapsed)) #catalogMain>.catalog-body{
  overflow-x:hidden!important;overflow-y:auto!important;min-height:0!important;flex:1 1 auto!important
}
#catalogIndex.is-embedded:not(.is-collapsed){
  margin-bottom:calc(var(--card-min-dock-h,2.75rem) + .5rem)!important
}
html body.display-sides #catalogMain>.catalog-body>#catalogIndex.is-embedded:not(.is-collapsed),
html body.display-middle #catalogMain>.catalog-body>#catalogIndex.is-embedded:not(.is-collapsed),
html body.catalog-portable #catalogMain>.catalog-body>#catalogIndex.is-embedded:not(.is-collapsed),
html body.catalog-portable.display-sides #catalogMain>.catalog-body>#catalogIndex.is-embedded:not(.is-collapsed){
  height:min(48dvh,28rem)!important;max-height:min(70dvh,40rem)!important;min-height:16rem!important;
  overflow:hidden!important;background:var(--bg-surface)!important;isolation:isolate!important;
  z-index:45!important
}
html body.display-sides #catalogIndex.is-embedded:not(.is-collapsed) #catalogIndexList,
html body.display-sides #catalogIndex.is-embedded:not(.is-collapsed) .index,
html body.catalog-portable #catalogIndex.is-embedded:not(.is-collapsed) #catalogIndexList,
html body.catalog-portable #catalogIndex.is-embedded:not(.is-collapsed) .index{
  flex:1 1 auto!important;min-height:0!important;max-height:none!important;
  overflow-x:hidden!important;overflow-y:auto!important;background:var(--bg-surface)!important
}

"""

PORT_CSS = r"""
/* fix-PORTABLE-KW-FS-FOLDER-TITLE: no KW ⛶; no card folder; titles match desktop */
body.catalog-portable #kwStripFs,
body.catalog-portable #filterWrap .kw-fs-btn,
body.catalog-portable #filterTop > #kwStripFs,
body.catalog-portable #filterWrap .kw-fs{
  display:none!important;width:0!important;min-width:0!important;max-width:0!important;
  height:0!important;min-height:0!important;margin:0!important;padding:0!important;
  border:0!important;overflow:hidden!important;opacity:0!important;pointer-events:none!important
}
body.catalog-portable .path a.folder,
body.catalog-portable .path-icon-btn.folder,
body.catalog-portable .path-icon-btn[data-act="folder"],
body.catalog-portable .entry .path .path-icon-btn.folder{
  display:none!important
}
/* fix-PORTABLE-EMBED-OPAQUE-v1 */
html body.catalog-portable #catalogMain #catalogIndex.is-embedded:not(.is-collapsed),
html body.catalog-portable #catalogIndex.is-embedded:not(.is-collapsed){
  height:min(42dvh,24rem)!important;max-height:min(60dvh,32rem)!important;min-height:16rem!important;
  overflow:hidden!important;background:var(--bg-surface)!important;isolation:isolate!important;z-index:45!important
}
html body.catalog-portable #catalogIndex.is-embedded:not(.is-collapsed) .index,
html body.catalog-portable #catalogIndex.is-embedded:not(.is-collapsed) #catalogIndexList{
  flex:1 1 auto!important;min-height:0!important;max-height:none!important;
  overflow-x:hidden!important;overflow-y:auto!important;background:var(--bg-surface)!important
}

"""

BIND_OLD = """    row.appendChild(fs);row.appendChild(cp);if(folder)row.appendChild(folder);
    ensurePathIconGlyph(fs,'fullscreen');
    ensurePathIconGlyph(cp,'copy');
    if(folder)ensurePathIconGlyph(folder,'folder');"""

BIND_NEW = """    if(window.CATALOG_PORTABLE){if(folder){try{folder.remove();}catch(ePfd){}}folder=null;}
    row.appendChild(fs);row.appendChild(cp);if(folder)row.appendChild(folder);
    ensurePathIconGlyph(fs,'fullscreen');
    ensurePathIconGlyph(cp,'copy');
    if(folder)ensurePathIconGlyph(folder,'folder');"""

STRIP_OLD = """function stripIndexCardChrome(ix){
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

STRIP_NEW = """function stripIndexCardChrome(ix){
  if(stripIndexCardChrome._busy)return;
  stripIndexCardChrome._busy=true;
  try{
    var n=0;
    function nuke(el){
      if(!el||el.nodeType!==1)return;
      n++;
      try{el.remove();}catch(err){try{el.parentNode&&el.parentNode.removeChild(el);}catch(e2){}}
    }
    var roots=[];
    var box=document.getElementById('catalogIndex');
    var list=document.getElementById('catalogIndexList')||(box&&box.querySelector('ul.index,#catalogIndexList'));
    if(ix&&ix.nodeType===1)roots.push(ix);
    if(box&&roots.indexOf(box)<0)roots.push(box);
    if(list&&roots.indexOf(list)<0)roots.push(list);
    document.querySelectorAll('#catalogIndex,.catalog-index,ul.index,#catalogIndexList').forEach(function(node){
      if(roots.indexOf(node)<0)roots.push(node);
    });
    var sel='.path-action-row,.path-icon-btn,.path-label,.path-fs-hit,.path-copy-hit,.fav-btn,a.folder,.path,svg.path-icon-glyph,img.path-icon-glyph';
    roots.forEach(function(root){
      if(!root)return;
      root.querySelectorAll('li').forEach(function(li){
        if(!(li.closest&&li.closest('#catalogIndex,.catalog-index,ul.index,#catalogIndexList')))return;
        [].slice.call(li.childNodes).forEach(function(node){
          if(node.nodeType!==1)return;
          if(node.matches&&node.matches('a[href^="#"]')){
            node.classList.remove('path-icon-btn','folder','path-fs-hit','path-copy-hit','path-label');
            node.querySelectorAll('svg,img,button,.path-icon-glyph,.path-action-row,.path-label').forEach(nuke);
            return;
          }
          nuke(node);
        });
      });
      root.querySelectorAll(sel).forEach(function(el){
        if(el.matches&&el.matches('a[href^="#"]')){
          el.classList.remove('path-icon-btn','folder','path-fs-hit','path-copy-hit');
          el.querySelectorAll('svg,img,button,.path-icon-glyph').forEach(nuke);
          return;
        }
        nuke(el);
      });
    });
    try{fetch('http://127.0.0.1:7529/ingest/1cf46354-1d61-4c80-bd72-a340f1db1b51',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'c00e3e'},body:JSON.stringify({sessionId:'c00e3e',runId:'index-nuke',hypothesisId:'IX',location:'catalog:stripIndexCardChrome',message:'index chrome strip',data:{n:n,embed:!!(box&&box.classList.contains('is-embedded')),win:document.body.classList.contains('index-window-open')},timestamp:Date.now()})}).catch(function(){});}catch(eLog){}
    if(typeof bindIndexPathIconWatch==='function')bindIndexPathIconWatch();
  }finally{stripIndexCardChrome._busy=false;}
}
function bindIndexPathIconWatch(){
  if(bindIndexPathIconWatch._on)return;
  if(typeof MutationObserver!=='function')return;
  bindIndexPathIconWatch._on=true;
  var t=0;
  function kick(){
    if(stripIndexCardChrome._busy)return;
    clearTimeout(t);
    t=setTimeout(function(){if(typeof stripIndexCardChrome==='function')stripIndexCardChrome();},24);
  }
  var mo=new MutationObserver(kick);
  var box=document.getElementById('catalogIndex');
  var list=document.getElementById('catalogIndexList');
  if(box)mo.observe(box,{childList:true,subtree:true});
  if(list&&!(box&&box.contains(list)))mo.observe(list,{childList:true,subtree:true});
}"""

TITLES = {
    "KONTAKT-CATALOG-portable.html": [
        ("<title>Kontakt Lib</title>", "<title>Kontakt Library</title>"),
        ('aria-label="Kontakt Lib"', 'aria-label="Kontakt Library"'),
        ('<span class="hdr-title-tail">Lib</span>', '<span class="hdr-title-tail">Library</span>'),
    ],
    "DS-CATALOG-portable.html": [
        ("<title>DS Lib</title>", "<title>Decent Library</title>"),
        ('aria-label="DS Lib"', 'aria-label="Decent Library"'),
        ('<span class="hdr-title-lead">DS</span>', '<span class="hdr-title-lead">Decent</span>'),
        ('<span class="hdr-title-tail">Lib</span>', '<span class="hdr-title-tail">Library</span>'),
    ],
}


JS_OV_OLD = """        el.style.setProperty('overflow','visible','important');
        el.style.setProperty('overflow-y','visible','important');
        el.style.setProperty('max-height','none','important');
        el.style.setProperty('height','auto','important');"""

JS_OV_NEW = """        el.style.removeProperty('overflow');
        el.style.removeProperty('overflow-y');
        el.style.removeProperty('max-height');
        el.style.removeProperty('height');"""

JS_H_OLD = """    if(ix.classList.contains('is-embedded')){
      ix.style.setProperty('height','auto','important');
      ix.style.setProperty('max-height','none','important');
    }else{"""

JS_H_NEW = """    if(ix.classList.contains('is-embedded')){
      ['height','max-height','overflow','overflow-y'].forEach(function(p){ix.style.removeProperty(p);});
    }else{"""


def write_ok(path: Path, text: str) -> None:
    raw = text.encode("utf-8")
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_bytes(raw)
    if not tmp.read_bytes().decode("utf-8").strip().endswith("</html>"):
        tmp.unlink()
        raise SystemExit(f"{path.name}: truncated")
    tmp.replace(path)
    print("OK", path.name, len(raw))


def patch_all(path: Path) -> str:
    t = path.read_text(encoding="utf-8")
    n = path.name
    if MARK_OLD in t:
        start = t.find("/* " + MARK_OLD)
        if start < 0:
            raise SystemExit(f"{n}: v1 marker text missing")
        end = t.find("</style>", start)
        if end < 0:
            raise SystemExit(f"{n}: v1 style end missing")
        extra = CSS
        if path in PORTABLE:
            extra += PORT_CSS
        t = t[:start] + extra + t[end:]
    elif MARK in t and "height:min(48dvh,28rem)" not in t:
        start = t.find("/* " + MARK)
        if start < 0:
            raise SystemExit(f"{n}: v2 marker text missing")
        port_at = t.find("/* fix-PORTABLE-KW-FS-FOLDER-TITLE", start)
        end = port_at if port_at > 0 else t.find("</style>", start)
        if end < 0:
            raise SystemExit(f"{n}: v2 style end missing")
        t = t[:start] + CSS + t[end:]
    elif MARK not in t:
        idx = t.rfind("</style>")
        if idx < 0:
            raise SystemExit(f"{n}: no </style>")
        extra = CSS
        if path in PORTABLE:
            extra += PORT_CSS
        t = t[:idx] + extra + t[idx:]
    port_ix = "fix-PORTABLE-EMBED-OPAQUE-v1"
    PORT_OPAQUE = """
/* fix-PORTABLE-EMBED-OPAQUE-v1 */
html body.catalog-portable #catalogMain #catalogIndex.is-embedded:not(.is-collapsed),
html body.catalog-portable #catalogIndex.is-embedded:not(.is-collapsed){
  height:min(42dvh,24rem)!important;max-height:min(60dvh,32rem)!important;min-height:16rem!important;
  overflow:hidden!important;background:var(--bg-surface)!important;isolation:isolate!important;z-index:45!important
}
html body.catalog-portable #catalogMain #catalogIndex.is-embedded:not(.is-collapsed) .index,
html body.catalog-portable #catalogMain #catalogIndex.is-embedded:not(.is-collapsed) #catalogIndexList,
html body.catalog-portable #catalogIndex.is-embedded:not(.is-collapsed) .index,
html body.catalog-portable #catalogIndex.is-embedded:not(.is-collapsed) #catalogIndexList{
  flex:1 1 auto!important;min-height:0!important;max-height:none!important;
  overflow-x:hidden!important;overflow-y:auto!important;background:var(--bg-surface)!important
}

"""
    if path in PORTABLE:
        if "fix-PORTABLE-KW-FS-FOLDER-TITLE" not in t:
            idx = t.rfind("</style>")
            if idx < 0:
                raise SystemExit(f"{n}: no </style> for portable css")
            t = t[:idx] + PORT_CSS + t[idx:]
        start = t.find("fix-PORTABLE-EMBED-OPAQUE-v1")
        if start >= 0:
            end = t.find("</style>", start)
            t = t[:start] + PORT_OPAQUE.lstrip() + t[end:]
        else:
            idx = t.rfind("</style>")
            t = t[:idx] + PORT_OPAQUE + t[idx:]
    skip = "    if(window.CATALOG_PORTABLE){if(folder){try{folder.remove();}catch(ePfd){}}folder=null;}\n"
    if skip not in t:
        bc = t.count(BIND_OLD)
        if bc:
            if bc not in (1, 3):
                raise SystemExit(f"{n}: bind count {bc}")
            t = t.replace(BIND_OLD, BIND_NEW)
    while skip + skip in t:
        t = t.replace(skip + skip, skip)
    if STRIP_OLD not in t:
        if "function stripIndexCardChrome" in t and "runId:'index-nuke'" in t:
            pass
        else:
            raise SystemExit(f"{n}: strip block missing")
    else:
        t = t.replace(STRIP_OLD, STRIP_NEW, 1)
    if n in TITLES:
        for old, new in TITLES[n]:
            c = t.count(old)
            if c != 1:
                if t.count(new) >= 1:
                    continue
                raise SystemExit(f"{n}: title {old!r} count {c}")
            t = t.replace(old, new, 1)
    if path in PORTABLE:
        if JS_OV_OLD in t:
            t = t.replace(JS_OV_OLD, JS_OV_NEW)
        if JS_H_OLD in t:
            t = t.replace(JS_H_OLD, JS_H_NEW)
    if "c00e3e" not in t:
        raise SystemExit(f"{n}: lost c00e3e logs")
    return t


def main() -> None:
    for p in ALL:
        write_ok(p, patch_all(p))


if __name__ == "__main__":
    main()
