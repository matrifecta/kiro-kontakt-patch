#!/usr/bin/env python3
"""Portable: portrait cards 1-2 cols beside a pane, index names, collapsed path."""
from pathlib import Path

ROOT = Path("/home/phnx/kiro-kontakt-patch")
FILES = [
    ROOT / "public/catalogs/DS-CATALOG-portable.html",
    ROOT / "public/catalogs/KONTAKT-CATALOG-portable.html",
]

CSS_MARK = "/* fix-PORTABLE-CARD-PATH-INDEX:"
CSS_ADD = r"""
/* fix-PORTABLE-CARD-PATH-INDEX: portrait cards, 1-2 cols beside a pane, collapsed path, index names */
@media all{
  body.catalog-portable.display-sides #catalogIndex{
    position:relative!important;z-index:2!important;
    height:auto!important;max-height:min(36dvh,16rem)!important;
    box-shadow:none!important
  }
  body.catalog-portable.display-sides #catalogIndex.is-collapsed{
    max-height:none!important
  }
  body.catalog-portable.display-sides #catalogIndex:not(.is-collapsed) .index,
  body.catalog-portable.display-sides #catalogIndex:not(.is-collapsed) #catalogIndexList{
    display:flex!important;flex-direction:column!important;
    grid-template-columns:none!important;columns:none!important;
    gap:.1rem!important;overflow-y:auto!important;min-height:0!important
  }
  body.catalog-portable.display-sides #catalogIndex .index li{
    display:flex!important;max-width:100%!important;min-width:0!important;overflow:hidden
  }
  body.catalog-portable.display-sides #catalogIndex .index a{
    overflow:hidden!important;text-overflow:ellipsis!important;
    white-space:nowrap!important;word-break:normal!important;
    max-height:none!important;-webkit-line-clamp:unset;line-clamp:unset
  }
  body.catalog-portable #catalogMain{container-type:inline-size;container-name:catmain}
  body.catalog-portable.display-sides:not(.display-middle).kw-open .catalog-body,
  body.catalog-portable.display-sides:not(.display-middle).kw-open .loc-group,
  body.catalog-portable.display-sides:not(.display-middle):not(.search-chrome-collapsed) .catalog-body,
  body.catalog-portable.display-sides:not(.display-middle):not(.search-chrome-collapsed) .loc-group{
    --cat-min:12rem;
    --cat-cols:repeat(2,minmax(0,1fr));
    grid-template-columns:repeat(2,minmax(0,1fr))!important
  }
  body.catalog-portable .entry:not(.highlight):not(.selected) .cover{
    position:relative;display:block!important;width:100%;aspect-ratio:3/4;
    height:auto!important;min-height:0!important;max-height:none!important;
    overflow:hidden;border-radius:6px;background:var(--bg)
  }
  body.catalog-portable .entry:not(.highlight):not(.selected) .cover img{
    position:absolute;inset:0;width:100%!important;height:100%!important;max-height:none!important;min-height:0!important;
    object-fit:cover!important;object-position:center
  }
  body.catalog-portable .entry:not(.highlight) .lib-name,
  body.catalog-portable .entry:not(.highlight) h3{
    display:-webkit-box;-webkit-box-orient:vertical;-webkit-line-clamp:3;line-clamp:3;
    overflow:hidden
  }
  body.catalog-portable .entry .path{
    display:flex;flex-wrap:wrap;align-items:baseline;gap:.25rem .55rem;min-width:0
  }
  body.catalog-portable .entry .path b,
  body.catalog-portable .entry .path .path-open-hit{
    cursor:pointer;flex:0 0 auto
  }
  body.catalog-portable .entry .path .path-fs-hit{
    cursor:pointer;border:0;background:transparent;color:var(--accent-instrument);
    text-decoration:underline;font:inherit;padding:0;flex:0 0 auto
  }
  body.catalog-portable .entry .path.is-collapsed code{display:none!important}
  body.catalog-portable .entry .path:not(.is-collapsed){flex-direction:column;align-items:flex-start}
}
@container catmain (max-width: 22rem){
  body.catalog-portable.display-sides:not(.display-middle).kw-open .catalog-body,
  body.catalog-portable.display-sides:not(.display-middle).kw-open .loc-group,
  body.catalog-portable.display-sides:not(.display-middle):not(.search-chrome-collapsed) .catalog-body,
  body.catalog-portable.display-sides:not(.display-middle):not(.search-chrome-collapsed) .loc-group{
    grid-template-columns:1fr!important
  }
}
"""

PATH_OLD = "    if(e.target.closest('.path')){activatePath(entry);return;}"
PATH_NEW = """    if(e.target.closest('.path')){
      var pathBox=e.target.closest('.path');
      if(e.target.closest('.path-open-hit')||(e.target.closest('b')&&!e.target.closest('.path-fs-hit'))){
        pathBox.classList.toggle('is-collapsed');
        // #region agent log
        fetch('http://127.0.0.1:7529/ingest/1cf46354-1d61-4c80-bd72-a340f1db1b51',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'c00e3e'},body:JSON.stringify({sessionId:'c00e3e',runId:'post-fix',hypothesisId:'H-PATH1',location:'catalog:path-open',message:'path-toggle',data:{collapsed:pathBox.classList.contains('is-collapsed')},timestamp:Date.now()})}).catch(function(){});
        // #endregion
        e.preventDefault();e.stopPropagation();return;
      }
      activatePath(entry);return;
    }"""

BIND_MARK = "function bindPortablePathHits("
BIND_JS = r"""
function bindPortablePathHits(){
  document.querySelectorAll('.entry .path').forEach(function(p){
    if(p.dataset.pathBound==='1')return;
    p.dataset.pathBound='1';
    p.classList.add('is-collapsed');
    var b=p.querySelector('b');
    if(b){b.classList.add('path-open-hit');if(!/open/i.test((b.textContent||'').replace(/:$/,'')))b.textContent='open';}
    if(!p.querySelector('.path-fs-hit')){
      var hit=document.createElement('button');
      hit.type='button';hit.className='path-fs-hit';hit.textContent='path';
      hit.setAttribute('aria-label','Open path fullscreen');
      p.appendChild(hit);
    }
  });
}
function dbgPortableCards(phase){
  // #region agent log
  try{
    var main=document.getElementById('catalogMain'),ix=document.getElementById('catalogIndex'),ixl=document.getElementById('catalogIndexList');
    var body=main&&main.querySelector('.catalog-body,.loc-group');
    var cards=[].slice.call(document.querySelectorAll('#catalogMain .entry:not(.is-hidden)')).slice(0,6).map(function(el){
      var r=el.getBoundingClientRect();return {l:Math.round(r.left),t:Math.round(r.top),w:Math.round(r.width),h:Math.round(r.height)};
    });
    var links=[].slice.call(document.querySelectorAll('#catalogIndexList a')).slice(0,4).map(function(a){
      var r=a.getBoundingClientRect();return {t:a.textContent.slice(0,24),l:Math.round(r.left),w:Math.round(r.width),h:Math.round(r.height)};
    });
    var overlap=false;
    var as=[].slice.call(document.querySelectorAll('#catalogIndexList li')).slice(0,12);
    as.forEach(function(a,i){as.forEach(function(b,j){if(j<=i)return;var ra=a.getBoundingClientRect(),rb=b.getBoundingClientRect();if(ra.width<4||rb.width<4)return;if(!(ra.right<=rb.left+1||rb.right<=ra.left+1||ra.bottom<=rb.top+1||rb.bottom<=ra.top+1))overlap=true;});});
    var p=document.querySelector('#catalogMain .entry .path');
    var cols=0;
    if(cards.length){var tops={};cards.forEach(function(c){var k=String(Math.round(c.t/8)*8);tops[k]=(tops[k]||0)+1;});Object.keys(tops).forEach(function(k){if(tops[k]>cols)cols=tops[k];});}
    fetch('http://127.0.0.1:7529/ingest/1cf46354-1d61-4c80-bd72-a340f1db1b51',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'c00e3e'},body:JSON.stringify({sessionId:'c00e3e',runId:'post-fix',hypothesisId:'H-CARD1',location:'catalog:dbgPortableCards',message:'cards-index-path',data:{phase:String(phase||''),vw:innerWidth||0,mainW:main?Math.round(main.getBoundingClientRect().width):0,cols:cols,cards:cards,ixCollapsed:!!(ix&&ix.classList.contains('is-collapsed')),ixH:ix?Math.round(ix.getBoundingClientRect().height):0,overlap:overlap,links:links,pathCollapsed:!!(p&&p.classList.contains('is-collapsed')),pathHasFs:!!(p&&p.querySelector('.path-fs-hit')),grid:body?getComputedStyle(body).gridTemplateColumns:''},timestamp:Date.now()})}).catch(function(){});
  }catch(eC){}
  // #endregion
}
"""

BOOT_OLD = "  if(typeof dbgMobileUi==='function')dbgMobileUi('setDisplayMode',{hyp:'H-P1'});"
BOOT_NEW = """  if(typeof bindPortablePathHits==='function')bindPortablePathHits();
  if(typeof dbgPortableCards==='function')dbgPortableCards('setDisplayMode');
  if(typeof dbgMobileUi==='function')dbgMobileUi('setDisplayMode',{hyp:'H-P1'});"""


def sub(text, old, new, label, path):
    if old not in text:
        if new in text:
            print(f"  skip {path.name} {label}")
            return text
        raise SystemExit(f"{path.name}: {label} missing")
    n = text.count(old)
    if n != 1:
        raise SystemExit(f"{path.name}: {label} count={n}")
    return text.replace(old, new, 1)


def main():
    for path in FILES:
        t = path.read_text(encoding="utf-8")
        if CSS_MARK in t:
            print(f"  skip {path.name} css")
        else:
            if "</style></head>" not in t:
                raise SystemExit(f"{path.name}: no style close")
            t = t.replace("</style></head>", CSS_ADD + "\n</style></head>", 1)
            print(f"  css {path.name}")
        t = sub(t, PATH_OLD, PATH_NEW, "path-click", path)
        if BIND_MARK not in t:
            needle = "function dbgMobileUi("
            if needle not in t:
                raise SystemExit(f"{path.name}: no dbgMobileUi")
            t = t.replace(needle, BIND_JS + "\n" + needle, 1)
            print(f"  bind {path.name}")
        else:
            print(f"  skip {path.name} bind")
        t = sub(t, BOOT_OLD, BOOT_NEW, "boot", path)
        path.write_text(t, encoding="utf-8")
        print("ok", path.name)


if __name__ == "__main__":
    main()
