#!/usr/bin/env python3
"""Document-header pyramid: hide/show the top toolbar on all four catalogs."""
from pathlib import Path

ROOT = Path("/home/phnx/kiro-kontakt-patch/public/catalogs")
FILES = [
    ROOT / "KONTAKT-CATALOG.html",
    ROOT / "DS-CATALOG.html",
    ROOT / "KONTAKT-CATALOG-portable.html",
    ROOT / "DS-CATALOG-portable.html",
]

CSS_MARK = "</style></head><body class=\"search-mode\">"
CSS_ADD = r"""
/* fix-HDR-BAR-TOGGLE: pyramid on the header bottom-center hides/shows the document toolbar */
.catalog-header{padding-bottom:1.35rem!important}
.hdr-bar-toggle{
  position:absolute;left:50%;bottom:.1rem;transform:translateX(-50%);
  z-index:40;box-sizing:border-box;
  width:2.15rem;height:1.15rem;min-width:2.15rem;min-height:1.15rem;
  padding:0;margin:0;
  display:inline-flex;align-items:center;justify-content:center;
  border:1px solid var(--border);border-bottom:0;
  border-radius:8px 8px 0 0;
  background:var(--bg-surface);color:var(--text);
  cursor:pointer;touch-action:manipulation;font:inherit;line-height:1
}
.hdr-bar-toggle:hover{border-color:var(--accent-instrument);color:var(--accent-instrument);background:var(--accent-instrument-bg)}
.hdr-bar-toggle .toggle-arrow{display:inline-block;transform:rotate(180deg);transition:transform .2s;font-size:.85rem;line-height:1}
body.hdr-bar-hidden .hdr-bar-toggle .toggle-arrow{transform:none}
body.hdr-bar-hidden .catalog-header{
  display:flex!important;justify-content:center;align-items:center;
  min-height:1.4rem;height:1.4rem;max-height:1.4rem;
  padding:0 .5rem!important;margin:0!important;row-gap:0;column-gap:0;
  overflow:visible;border-bottom:1px solid var(--border)
}
body.hdr-bar-hidden .catalog-header>:not(#hdrBarToggle){display:none!important;visibility:hidden!important;pointer-events:none!important}
body.hdr-bar-hidden .catalog-header::after{content:none!important;display:none!important}
body.hdr-bar-hidden .hdr-bar-toggle{
  position:fixed!important;left:50%!important;top:0!important;right:auto!important;bottom:auto!important;
  transform:translateX(-50%)!important;margin:0;z-index:321
}
body:is(.hl-open,.chosen-preview-open,.card-embed-open).hdr-bar-hidden .hdr-bar-toggle{z-index:40}
body.hl-open .catalog-header{visibility:hidden!important;pointer-events:none!important}
body.hl-open .hdr-bar-toggle{visibility:hidden!important;pointer-events:none!important}
body:is(.chosen-preview-open,.card-embed-open,.hl-open) #catalogIndex{
  visibility:hidden!important;pointer-events:none!important
}
/* fix-PREVIEW-BELOW-HDR: center extended card in the space under the document header */
body.chosen-preview-open .entry.selected:not(.highlight){
  top:calc(var(--cat-header-h,0px) + (100dvh - var(--cat-header-h,0px))/2)!important;
  max-height:calc(100dvh - var(--cat-header-h,0px) - 1.25rem)!important
}
body.card-embed-open.chosen-preview-open .entry.selected:not(.highlight){
  height:calc(100dvh - var(--cat-header-h,0px) - 1.25rem)!important;
  max-height:calc(100dvh - var(--cat-header-h,0px) - 1.25rem)!important
}
""" + CSS_MARK

BTN = (
    '<button type="button" class="hdr-bar-toggle" id="hdrBarToggle" aria-expanded="true" '
    'aria-label="Hide document header" title="Hide header" '
    'onclick="event.preventDefault();event.stopPropagation();toggleHdrBar()">'
    '<span class="toggle-arrow">&#9660;</span></button>'
)

HTML_DESK_OLD = "</optgroup></select></div></div></div>\n<div class=\"search-chrome\""
HTML_DESK_NEW = "</optgroup></select></div>" + BTN + "</div></div>\n<div class=\"search-chrome\""

HTML_PORT_OLD = "togglePortableToolbarFs()\">&#x26F6;</button></div></div></div>\n<div class=\"search-chrome\""
HTML_PORT_NEW = "togglePortableToolbarFs()\">&#x26F6;</button></div>" + BTN + "</div></div>\n<div class=\"search-chrome\""

JS_OLD = "window.toggleHdrMore=toggleHdrMore;\nwindow.toggleKwStripMore=toggleKwStripMore;"
JS_NEW = r"""window.toggleHdrMore=toggleHdrMore;
window.toggleKwStripMore=toggleKwStripMore;
function hdrBarPrefKey(){return 'catalog-hdr-bar-hidden-'+(window.CATALOG_NS||'catalog');}
function updateCatHeaderH(){
  var hdr=document.querySelector('.catalog-header');
  if(hdr)document.documentElement.style.setProperty('--cat-header-h',Math.round(hdr.getBoundingClientRect().bottom)+'px');
}
function syncHdrBar(){
  var hide=document.body.classList.contains('hdr-bar-hidden');
  var btn=document.getElementById('hdrBarToggle');
  if(btn){
    btn.setAttribute('aria-expanded', hide?'false':'true');
    btn.setAttribute('aria-label', hide?'Show document header':'Hide document header');
    btn.title=hide?'Show header':'Hide header';
  }
  updateCatHeaderH();
}
function toggleHdrBar(force){
  var hide=(force===true||force===false)?!!force:!document.body.classList.contains('hdr-bar-hidden');
  document.body.classList.toggle('hdr-bar-hidden', hide);
  try{localStorage.setItem(hdrBarPrefKey(), hide?'1':'0');}catch(eHdr){}
  syncHdrBar();
  if(typeof applyFsChromeSize==='function')applyFsChromeSize();
  else updateCatHeaderH();
  if(typeof applyIndexScrollFit==='function')applyIndexScrollFit();
  if(typeof placeMenusForDisplay==='function'){
    var mode=(document.body.className.match(/display-(\S+)/)||[])[1];
    try{placeMenusForDisplay(mode||'sides');}catch(ePlace){}
  }
}
window.toggleHdrBar=toggleHdrBar;
window.updateCatHeaderH=updateCatHeaderH;
(function restoreHdrBar(){
  try{
    if(localStorage.getItem(hdrBarPrefKey())==='1') document.body.classList.add('hdr-bar-hidden');
  }catch(eRest){}
  if(document.readyState==='loading') document.addEventListener('DOMContentLoaded', syncHdrBar);
  else syncHdrBar();
})();
"""


def must_replace(text: str, old: str, new: str, name: str, label: str) -> str:
    n = text.count(old)
    if n != 1:
        raise SystemExit(f"{name}: {label} count={n}")
    return text.replace(old, new, 1)


def write(path: Path, text: str) -> None:
    out = text.encode("utf-8")
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_bytes(out)
    check = tmp.read_bytes().decode("utf-8")
    if not check.strip().endswith("</html>"):
        tmp.unlink()
        raise SystemExit(f"{path.name}: truncated")
    tmp.replace(path)
    print("OK", path.name, "bytes", len(out))


def patch(path: Path) -> None:
    t = path.read_text(encoding="utf-8")
    n = path.name
    had_ingest = "127.0.0.1:7529/ingest" in t
    if "fix-HDR-BAR-TOGGLE" not in t:
        t = must_replace(t, CSS_MARK, CSS_ADD, n, "css mark")
    if 'id="hdrBarToggle"' not in t:
        if HTML_DESK_OLD in t:
            t = must_replace(t, HTML_DESK_OLD, HTML_DESK_NEW, n, "desk html")
        elif HTML_PORT_OLD in t:
            t = must_replace(t, HTML_PORT_OLD, HTML_PORT_NEW, n, "port html")
        else:
            raise SystemExit(f"{n}: header html mark missing")
    if "function toggleHdrBar(" not in t:
        t = must_replace(t, JS_OLD, JS_NEW, n, "js")
    if had_ingest and "127.0.0.1:7529/ingest" not in t:
        raise SystemExit(f"{n}: stripped debug logs")
    write(path, t)


def main() -> None:
    for p in FILES:
        patch(p)


if __name__ == "__main__":
    main()
