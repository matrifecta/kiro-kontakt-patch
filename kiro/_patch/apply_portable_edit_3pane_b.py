#!/usr/bin/env python3
"""Force Customize 3-pane grid in JS so SK-pair CSS cannot hide content or stack seps."""
from __future__ import annotations

import os
import tempfile
from pathlib import Path

ROOT = Path("/home/phnx/kiro-kontakt-patch/public/catalogs")
FILES = [
    ROOT / "KONTAKT-CATALOG-portable.html",
    ROOT / "DS-CATALOG-portable.html",
]

HELPER = r"""function applyPortableEdit3PaneGrid(on,land,flip){
  var b=document.body;
  var ch=document.getElementById('searchChrome');
  var fw=document.getElementById('filterWrap');
  var main=document.getElementById('catalogMain');
  function wipe(el){
    if(!el||!el.style||el.dataset.port3!=='1')return;
    ['display','visibility','pointer-events','grid-column','grid-row','width','min-width','max-width','height','min-height','max-height','flex','position','inset','transform','z-index','overflow'].forEach(function(p){el.style.removeProperty(p);});
    delete el.dataset.port3;
  }
  if(!on){
    if(b.dataset.port3){
      ['display','flex-direction','grid-template-columns','grid-template-rows'].forEach(function(p){b.style.removeProperty(p);});
      delete b.dataset.port3;
    }
    wipe(ch);wipe(fw);wipe(main);
    return;
  }
  var vw=window.innerWidth||400;
  var vh=window.innerHeight||800;
  var root=document.documentElement;
  var lw=parseInt(getComputedStyle(root).getPropertyValue('--portable-lw'),10)||0;
  var rw=parseInt(getComputedStyle(root).getPropertyValue('--portable-rw'),10)||0;
  var mh=parseInt(getComputedStyle(root).getPropertyValue('--portable-menu-h'),10)||0;
  b.style.setProperty('display','grid','important');
  b.style.setProperty('flex-direction','unset','important');
  function mark(el){if(el)el.dataset.port3='1';}
  if(land){
    if(lw<96)lw=Math.round(vw*0.28);
    if(rw<96)rw=Math.round(vw*0.28);
    if(lw+rw>vw-96){
      var sc=(vw-96)/(lw+rw);
      lw=Math.max(96,Math.round(lw*sc));
      rw=Math.max(96,Math.round(rw*sc));
    }
    root.style.setProperty('--portable-lw',lw+'px');
    root.style.setProperty('--portable-rw',rw+'px');
    b.style.setProperty('grid-template-columns',flip?('minmax(96px,'+rw+'px) minmax(0,1fr) minmax(96px,'+lw+'px)'):('minmax(96px,'+lw+'px) minmax(0,1fr) minmax(96px,'+rw+'px)'),'important');
    b.style.setProperty('grid-template-rows','auto minmax(0,1fr)','important');
    b.dataset.port3='land';
    function side(el,col){
      if(!el)return;
      mark(el);
      el.style.setProperty('display','flex','important');
      el.style.setProperty('visibility','visible','important');
      el.style.setProperty('grid-column',String(col),'important');
      el.style.setProperty('grid-row','2','important');
      el.style.setProperty('width','auto','important');
      el.style.setProperty('max-width','none','important');
      el.style.setProperty('height','auto','important');
      el.style.setProperty('max-height','none','important');
      el.style.setProperty('min-height','0','important');
      el.style.setProperty('position','relative','important');
      el.style.setProperty('inset','auto','important');
      el.style.setProperty('transform','none','important');
      el.style.setProperty('flex','unset','important');
      el.style.setProperty('z-index','6','important');
    }
    side(ch,flip?3:1);
    side(fw,flip?1:3);
    if(main){
      mark(main);
      main.style.setProperty('display','block','important');
      main.style.setProperty('visibility','visible','important');
      main.style.setProperty('pointer-events','auto','important');
      main.style.setProperty('grid-column','2','important');
      main.style.setProperty('grid-row','2','important');
      main.style.setProperty('width','auto','important');
      main.style.setProperty('min-width','0','important');
      main.style.setProperty('max-width','none','important');
      main.style.setProperty('height','auto','important');
      main.style.setProperty('overflow','auto','important');
    }
  }else{
    if(mh<72)mh=Math.round(Math.min(vh*0.32,280));
    if(lw<96)lw=Math.round(vw*0.42);
    root.style.setProperty('--portable-menu-h',mh+'px');
    root.style.setProperty('--middle-menu-h',mh+'px');
    root.style.setProperty('--portable-lw',lw+'px');
    b.style.setProperty('grid-template-columns',flip?('minmax(0,1fr) minmax(96px,'+lw+'px)'):('minmax(96px,'+lw+'px) minmax(0,1fr)'),'important');
    b.style.setProperty('grid-template-rows','auto minmax(72px,'+mh+'px) minmax(0,1fr)','important');
    b.dataset.port3='port';
    function stack(el,row){
      if(!el)return;
      mark(el);
      el.style.setProperty('display','flex','important');
      el.style.setProperty('visibility','visible','important');
      el.style.setProperty('grid-column',flip?'2':'1','important');
      el.style.setProperty('grid-row',String(row),'important');
      el.style.setProperty('width','auto','important');
      el.style.setProperty('height','100%','important');
      el.style.setProperty('max-height','none','important');
      el.style.setProperty('min-height','0','important');
      el.style.setProperty('position','relative','important');
      el.style.setProperty('inset','auto','important');
      el.style.setProperty('flex','unset','important');
      el.style.setProperty('z-index','6','important');
    }
    stack(ch,2);
    stack(fw,3);
    if(main){
      mark(main);
      main.style.setProperty('display','block','important');
      main.style.setProperty('visibility','visible','important');
      main.style.setProperty('grid-column',flip?'1':'2','important');
      main.style.setProperty('grid-row','2 / -1','important');
      main.style.setProperty('min-height','0','important');
    }
  }
}
window.applyPortableEdit3PaneGrid=applyPortableEdit3PaneGrid;
function placePortableHandles(){"""

PLACE_HEAD_OLD = """  if(!edit||(oneFs&&!dual)){
    if(typeof placeCatalogJumpStack==='function')placeCatalogJumpStack();
    return;
  }
  var placed=false;
  var land=document.body.classList.contains('portable-landscape')||(!portrait&&!document.body.classList.contains('portable-portrait'));
  var edit3=edit&&m.both&&vis(ch)&&vis(fw)&&!oneFs&&!dual;
  if(dual&&vis(ch)&&vis(fw)){"""

PLACE_HEAD_NEW = """  var land=document.body.classList.contains('portable-landscape')||(!portrait&&!document.body.classList.contains('portable-portrait'));
  var edit3=edit&&m.both&&vis(ch)&&vis(fw)&&!oneFs&&!dual;
  if(typeof applyPortableEdit3PaneGrid==='function')applyPortableEdit3PaneGrid(!!edit3,land,flip);
  if(!edit||(oneFs&&!dual)){
    if(typeof placeCatalogJumpStack==='function')placeCatalogJumpStack();
    return;
  }
  var placed=false;
  if(dual&&vis(ch)&&vis(fw)){"""

CSS_OLD = """html body.catalog-portable.layout-edit.portable-edit-3pane.portable-landscape,
html body.catalog-portable.layout-edit.portable-edit-3pane.portable-landscape.display-sides,
html body.catalog-portable.layout-edit.portable-edit-3pane.portable-landscape.display-sides.display-middle,
html body.catalog-portable.layout-edit.portable-edit-3pane.portable-landscape.portable-sk-pair,
html body.catalog-portable.layout-edit.portable-edit-3pane.portable-sk-pair{
  display:grid!important;flex-direction:unset!important;
  grid-template-columns:minmax(96px,var(--portable-lw,28%)) minmax(0,1fr) minmax(96px,var(--portable-rw,28%))!important;
  grid-template-rows:auto minmax(0,1fr)!important
}"""

CSS_NEW = """html body.catalog-portable.layout-edit.portable-edit-3pane.portable-landscape,
html body.catalog-portable.layout-edit.portable-edit-3pane.portable-landscape.display-sides,
html body.catalog-portable.layout-edit.portable-edit-3pane.portable-landscape.display-sides.display-middle,
html body.catalog-portable.layout-edit.portable-edit-3pane.portable-landscape.portable-sk-pair,
html body.catalog-portable.layout-edit.portable-edit-3pane.portable-sk-pair,
html body.catalog-portable.layout-edit.portable-edit-3pane.portable-landscape.display-sides.kw-open:not(.kw-chrome-collapsed):not(.search-chrome-collapsed):not(.ac-fs-open):not(.kw-fs-open),
html body.catalog-portable.layout-edit.portable-edit-3pane.portable-landscape.display-sides.display-middle.kw-open:not(.kw-chrome-collapsed):not(.search-chrome-collapsed):not(.ac-fs-open):not(.kw-fs-open){
  display:grid!important;flex-direction:unset!important;
  grid-template-columns:minmax(96px,var(--portable-lw,28%)) minmax(0,1fr) minmax(96px,var(--portable-rw,28%))!important;
  grid-template-rows:auto minmax(0,1fr)!important
}"""

MAIN_OLD = """html body.catalog-portable.layout-edit.portable-edit-3pane #catalogMain,
html body.catalog-portable.layout-edit.portable-edit-3pane.portable-sk-pair #catalogMain,
html body.catalog-portable.layout-edit.portable-edit-3pane.portable-sk-pair.index-window-open #catalogMain,
html body.catalog-portable.layout-edit.portable-edit-3pane.portable-landscape #catalogMain,
html body.catalog-portable.layout-edit.portable-edit-3pane.portable-landscape.display-sides.kw-open:not(.kw-chrome-collapsed):not(.search-chrome-collapsed) #catalogMain,
html body.catalog-portable.layout-edit.portable-edit-3pane.portable-landscape.display-sides.index-window-open.kw-open:not(.kw-chrome-collapsed):not(.search-chrome-collapsed) #catalogMain{"""

MAIN_NEW = """html body.catalog-portable.layout-edit.portable-edit-3pane #catalogMain,
html body.catalog-portable.layout-edit.portable-edit-3pane.portable-sk-pair #catalogMain,
html body.catalog-portable.layout-edit.portable-edit-3pane.portable-sk-pair.index-window-open #catalogMain,
html body.catalog-portable.layout-edit.portable-edit-3pane.portable-landscape #catalogMain,
html body.catalog-portable.layout-edit.portable-edit-3pane.portable-landscape.display-sides.kw-open:not(.kw-chrome-collapsed):not(.search-chrome-collapsed) #catalogMain,
html body.catalog-portable.layout-edit.portable-edit-3pane.portable-landscape.display-sides.index-window-open.kw-open:not(.kw-chrome-collapsed):not(.search-chrome-collapsed) #catalogMain,
html body.catalog-portable.layout-edit.portable-edit-3pane.portable-landscape.display-sides.kw-open:not(.kw-chrome-collapsed):not(.search-chrome-collapsed):not(.ac-fs-open):not(.kw-fs-open) #catalogMain,
html body.catalog-portable.layout-edit.portable-edit-3pane.portable-landscape.portable-sk-pair.display-sides.index-window-open.kw-open:not(.kw-chrome-collapsed):not(.search-chrome-collapsed) #catalogMain{"""


def replace_once(text: str, old: str, new: str, label: str) -> str:
    n = text.count(old)
    if n != 1:
        raise SystemExit(f"{label}: expected 1 occurrence, found {n}")
    return text.replace(old, new, 1)


def patch(text: str) -> str:
    if "function applyPortableEdit3PaneGrid(" not in text:
        text = replace_once(text, "function placePortableHandles(){", HELPER, "helper")
    text = replace_once(text, PLACE_HEAD_OLD, PLACE_HEAD_NEW, "place-head")
    text = replace_once(text, CSS_OLD, CSS_NEW, "css-3col")
    text = replace_once(text, MAIN_OLD, MAIN_NEW, "css-main")
    return text


def write_safe(path: Path, data: str, before_c00: int) -> None:
    if not data.rstrip().endswith("</html>"):
        raise SystemExit(f"{path.name} rewrite missing </html>")
    if data.count("sessionId:'c00e3e'") < before_c00:
        raise SystemExit(f"{path.name}: lost c00e3e logs")
    fd, tmp = tempfile.mkstemp(prefix=path.stem + ".", suffix=".html", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise
    got = path.stat().st_size
    if got < 100000:
        raise SystemExit(f"{path.name} too small after write: {got}")
    check = path.read_text(encoding="utf-8")
    if not check.rstrip().endswith("</html>"):
        raise SystemExit(f"{path.name} after write missing </html>")
    if check.count("function applyPortableEdit3PaneGrid(") != 1:
        raise SystemExit(f"{path.name} helper count")
    if check.count("function placePortableHandles(){") != 1:
        raise SystemExit(f"{path.name} placePortableHandles count")


def main() -> None:
    for path in FILES:
        raw = path.read_text(encoding="utf-8")
        before_c00 = raw.count("sessionId:'c00e3e'")
        out = patch(raw)
        write_safe(path, out, before_c00)
        print(f"patched {path.name} {len(raw)} -> {len(out)} c00={before_c00} size={path.stat().st_size}")


if __name__ == "__main__":
    main()
