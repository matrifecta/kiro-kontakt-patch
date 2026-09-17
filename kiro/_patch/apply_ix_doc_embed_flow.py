#!/usr/bin/env python3
"""Window Index/About hover on the pane; Embed lives in .catalog-body and scrolls away."""
from __future__ import annotations

from pathlib import Path

ROOT = Path("/home/phnx/kiro-kontakt-patch")
FILES = [
    ROOT / "public/catalogs/DS-CATALOG.html",
    ROOT / "public/catalogs/KONTAKT-CATALOG.html",
    ROOT / "public/catalogs/DS-CATALOG-portable.html",
    ROOT / "public/catalogs/KONTAKT-CATALOG-portable.html",
]

MARKER = "fix-IX-DOC-EMBED-FLOW"

CSS_OLD = "/* fix-DOC-NOTE-EMBED: About in-flow with cards; no second bottom dock */"
CSS_NEW = """/* fix-IX-DOC-EMBED-FLOW: Window hovers on #catalogMain; Embed is in .catalog-body and scrolls away */
#catalogMain>.catalog-body>#catalogIndex.is-embedded,
body.display-sides #catalogMain .catalog-body>#catalogIndex.is-embedded,
body.display-middle #catalogMain .catalog-body>#catalogIndex.is-embedded,
body.catalog-portable #catalogMain .catalog-body>#catalogIndex.is-embedded{
  position:static!important;top:auto!important;height:auto!important;max-height:none!important;
  flex:0 0 auto!important;margin:.45rem 0 .6rem!important;box-shadow:none!important;
  border-radius:8px;overflow:visible!important;z-index:auto
}
#catalogMain>.catalog-body>#catalogIndex.is-embedded:not(.is-collapsed),
#catalogMain>.catalog-body>#catalogIndex.is-embedded:not(.is-collapsed) .index,
#catalogMain>.catalog-body>#catalogIndex.is-embedded:not(.is-collapsed) #catalogIndexList{
  height:auto!important;max-height:none!important;overflow:visible!important;flex:0 0 auto!important
}
#catalogMain>#catalogIndex:not(.is-embedded){flex:0 0 auto;z-index:16}
""" + CSS_OLD

PARK_IX_OLD = """  if(ix&&cb){
    if(ix.classList.contains('is-embedded')){
      if(ix.parentNode!==cb){if(cb.firstChild)cb.insertBefore(ix,cb.firstChild);else cb.appendChild(ix);}
    }else if(ix.parentNode!==w){
      w.insertBefore(ix,cb);
    }
  }"""
PARK_IX_NEW = """  if(ix&&cb){
    if(ix.classList.contains('is-embedded')){
      if(ix.parentNode!==cb||cb.firstElementChild!==ix){
        if(cb.firstChild)cb.insertBefore(ix,cb.firstChild);else cb.appendChild(ix);
      }
    }else if(ix.parentNode!==w||ix.nextElementSibling!==cb){
      w.insertBefore(ix,cb);
    }
  }"""

FORCE_OLD = """    if(mode!=='sides')idx.classList.add('is-embedded');
    else{
      if(pref===true)idx.classList.add('is-embedded');
      else idx.classList.remove('is-embedded');
    }"""
FORCE_NEW = """    if(mode!=='sides'&&mode!=='middle')idx.classList.add('is-embedded');
    else{
      if(pref===true)idx.classList.add('is-embedded');
      else idx.classList.remove('is-embedded');
    }
    if(typeof parkCatalogDocNote==='function')parkCatalogDocNote();
    if(typeof syncIndexWindowDock==='function')syncIndexWindowDock();"""

APPLY_OLD = "  if(typeof applyModeSlot==='function')applyModeSlot(mode);"
APPLY_NEW = """  if(typeof applyModeSlot==='function')applyModeSlot(mode);
  if(typeof parkCatalogDocNote==='function')parkCatalogDocNote();
  if(typeof syncIndexWindowDock==='function')syncIndexWindowDock();"""

BTN_DESK_OLD = "  btn.hidden=!sides;"
BTN_DESK_NEW = (
    "  var middle=document.body.classList.contains('display-middle');\n"
    "  btn.hidden=window.CATALOG_PORTABLE?false:!(sides||middle);"
)
BTN_PORT_OLD = "  btn.hidden=window.CATALOG_PORTABLE?false:!sides;"
BTN_PORT_NEW = (
    "  var middle=document.body.classList.contains('display-middle');\n"
    "  btn.hidden=window.CATALOG_PORTABLE?false:!(sides||middle);"
)

TOGGLE_DESK_OLD = """function toggleIndexEmbed(){
  var ix=document.getElementById('catalogIndex');
  if(!ix||!document.body.classList.contains('display-sides'))return;
  var on=ix.classList.toggle('is-embedded');
  writeIndexEmbedPref(on);
  if(typeof writeModeSlot==='function')writeModeSlot({indexEmbed:on},'sides');
  if(typeof applyIndexScrollFit==='function')applyIndexScrollFit();
  syncIndexEmbedBtn();
  var cm=document.getElementById('catalogMain');
  if(on&&cm)cm.scrollTop=0;
}"""

SYNC_DESK = r"""function syncIndexWindowDock(){
  var ix=document.getElementById('catalogIndex');
  var windowOk=window.CATALOG_PORTABLE||document.body.classList.contains('display-sides')||document.body.classList.contains('display-middle');
  var on=!!(ix&&!ix.classList.contains('is-embedded')&&windowOk);
  document.body.classList.toggle('index-window-open',on);
  var main=document.getElementById('catalogMain');
  var cb=main&&(main.querySelector(':scope > .catalog-body')||main.querySelector('.catalog-body'));
  if(on&&main){
    main.style.setProperty('overflow-y','hidden','important');
    main.style.setProperty('overflow-x','hidden','important');
    if(cb){
      cb.style.setProperty('overflow-y','auto','important');
      cb.style.setProperty('overflow-x','hidden','important');
      cb.style.setProperty('min-height','0','important');
      cb.style.setProperty('flex','1 1 auto','important');
    }
  }
  if(typeof applyIndexFillDocStyles==='function')applyIndexFillDocStyles();
}
window.syncIndexWindowDock=syncIndexWindowDock;
"""

TOGGLE_DESK_NEW = SYNC_DESK + """function toggleIndexEmbed(){
  var ix=document.getElementById('catalogIndex');
  var sides=document.body.classList.contains('display-sides');
  var middle=document.body.classList.contains('display-middle');
  if(!ix)return;
  if(!window.CATALOG_PORTABLE&&!sides&&!middle)return;
  var on=ix.classList.toggle('is-embedded');
  writeIndexEmbedPref(on);
  if(typeof writeModeSlot==='function')writeModeSlot({indexEmbed:on},sides?'sides':(middle?'middle':undefined));
  if(typeof parkCatalogDocNote==='function')parkCatalogDocNote();
  if(typeof applyIndexScrollFit==='function')applyIndexScrollFit();
  if(typeof syncIndexWindowDock==='function')syncIndexWindowDock();
  if(typeof applyIndexFillDocStyles==='function')applyIndexFillDocStyles();
  syncIndexEmbedBtn();
  var sc=(typeof catalogContentScroller==='function'&&catalogContentScroller())||document.getElementById('catalogMain');
  if(on&&sc)sc.scrollTop=0;
}"""

TOGGLE_PORT_PARK_OLD = """  writeIndexEmbedPref(on);
  if(typeof writeModeSlot==='function')writeModeSlot({indexEmbed:on});
  if(typeof applyIndexScrollFit==='function')applyIndexScrollFit();
  if(typeof portableEnsureScrollMenus==='function')portableEnsureScrollMenus();"""
TOGGLE_PORT_PARK_NEW = """  writeIndexEmbedPref(on);
  if(typeof writeModeSlot==='function')writeModeSlot({indexEmbed:on});
  if(typeof parkCatalogDocNote==='function')parkCatalogDocNote();
  if(typeof applyIndexScrollFit==='function')applyIndexScrollFit();
  if(typeof syncIndexWindowDock==='function')syncIndexWindowDock();
  if(typeof applyIndexFillDocStyles==='function')applyIndexFillDocStyles();
  if(typeof portableEnsureScrollMenus==='function')portableEnsureScrollMenus();"""

TOGGLE_PORT_GATE_OLD = "  if(!window.CATALOG_PORTABLE&&!sides)return;"
TOGGLE_PORT_GATE_NEW = (
    "  var middle=document.body.classList.contains('display-middle');\n"
    "  if(!window.CATALOG_PORTABLE&&!sides&&!middle)return;"
)

TOGGLE_PORT_SCROLL_OLD = """  var cm=document.getElementById('catalogMain');
  if(on&&cm)cm.scrollTop=0;"""
TOGGLE_PORT_SCROLL_NEW = """  var sc=(typeof catalogContentScroller==='function'&&catalogContentScroller())||document.getElementById('catalogMain');
  if(on&&sc)sc.scrollTop=0;"""

LOG_PORT_OLD = "data:{on:on,ixOv:getComputedStyle(ix).overflowY"
LOG_PORT_NEW = (
    "data:{on:on,parent:(ix.parentElement&&(ix.parentElement.id||ix.parentElement.className))||'',"
    "ixOv:getComputedStyle(ix).overflowY"
)

SYNC_ON_OLD = "  var on=!!(window.CATALOG_PORTABLE&&ix&&!ix.classList.contains('is-embedded'));"
SYNC_ON_NEW = (
    "  var windowOk=window.CATALOG_PORTABLE||document.body.classList.contains('display-sides')"
    "||document.body.classList.contains('display-middle');\n"
    "  var on=!!(ix&&!ix.classList.contains('is-embedded')&&windowOk);"
)

FILL_ELSE_OLD = """    if(cb&&document.body.classList.contains('index-window-open')){
      cb.style.setProperty('flex','1 1 0%','important');
      cb.style.setProperty('height','0','important');
      cb.style.setProperty('min-height','0','important');
      cb.style.removeProperty('max-height');
      cb.style.setProperty('overflow-y','auto','important');
      cb.style.removeProperty('margin');
    }"""
FILL_ELSE_NEW = """    if(cb&&document.body.classList.contains('index-window-open')){
      cb.style.setProperty('flex','1 1 0%','important');
      cb.style.setProperty('height','0','important');
      cb.style.setProperty('min-height','0','important');
      cb.style.removeProperty('max-height');
      cb.style.setProperty('overflow-y','auto','important');
      cb.style.removeProperty('margin');
    }else if(cb){
      ['flex','height','min-height','max-height','overflow','overflow-y','overflow-x','margin'].forEach(function(p){cb.style.removeProperty(p);});
    }"""


def once(text: str, old: str, new: str, label: str, name: str, optional: bool = False) -> str:
    n = text.count(old)
    if n == 1:
        return text.replace(old, new, 1)
    if n == 0 and optional:
        return text
    raise SystemExit(f"{name}: {label} count={n} expected 1")


def patch(path: Path) -> None:
    raw = path.read_bytes()
    orig_size = len(raw)
    text = raw.decode("utf-8")
    name = path.name
    if not text.strip().endswith("</html>"):
        raise SystemExit(f"{name}: missing </html> before patch")
    if MARKER in text:
        print("skip", name, "already")
        return

    text = once(text, CSS_OLD, CSS_NEW, "css", name)
    text = once(text, PARK_IX_OLD, PARK_IX_NEW, "park-ix", name)
    text = once(text, FORCE_OLD, FORCE_NEW, "force-mode", name)
    text = once(text, APPLY_OLD, APPLY_NEW, "apply-slot-park", name)
    if BTN_DESK_OLD in text:
        text = once(text, BTN_DESK_OLD, BTN_DESK_NEW, "btn-desk", name)
    elif BTN_PORT_OLD in text:
        text = once(text, BTN_PORT_OLD, BTN_PORT_NEW, "btn-port", name)
    else:
        raise SystemExit(f"{name}: syncIndexEmbedBtn hidden mark missing")

    if TOGGLE_DESK_OLD in text:
        text = once(text, TOGGLE_DESK_OLD, TOGGLE_DESK_NEW, "toggle-desk", name)
    else:
        text = once(text, TOGGLE_PORT_GATE_OLD, TOGGLE_PORT_GATE_NEW, "toggle-port-gate", name)
        text = once(text, TOGGLE_PORT_PARK_OLD, TOGGLE_PORT_PARK_NEW, "toggle-port-park", name)
        text = once(text, TOGGLE_PORT_SCROLL_OLD, TOGGLE_PORT_SCROLL_NEW, "toggle-port-scroll", name)
        text = once(text, LOG_PORT_OLD, LOG_PORT_NEW, "toggle-port-log", name)
        text = once(text, SYNC_ON_OLD, SYNC_ON_NEW, "sync-on", name)
        text = once(text, FILL_ELSE_OLD, FILL_ELSE_NEW, "fill-else", name)

    if MARKER not in text:
        raise SystemExit(f"{name}: marker missing after patch")
    if not text.strip().endswith("</html>"):
        raise SystemExit(f"{name}: truncated, missing </html>")
    out = text.encode("utf-8")
    if orig_size > 4_000_000 and len(out) < orig_size * 0.9:
        raise SystemExit(f"{name}: size collapsed {orig_size} -> {len(out)}")
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_bytes(out)
    wrote = tmp.read_bytes()
    if len(wrote) != len(out):
        tmp.unlink()
        raise SystemExit(f"{name}: tmp size mismatch")
    if not wrote.decode("utf-8").strip().endswith("</html>"):
        tmp.unlink()
        raise SystemExit(f"{name}: tmp missing </html>")
    tmp.replace(path)
    print("OK", name, "bytes", len(out), "delta", len(out) - orig_size)


def main() -> None:
    for p in FILES:
        if not p.exists():
            raise SystemExit(f"missing {p}")
        patch(p)


if __name__ == "__main__":
    main()
