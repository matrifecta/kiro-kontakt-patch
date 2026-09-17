#!/usr/bin/env python3
"""Portable: header S/K buttons track Search/Keywords left-right (Flip)."""
from pathlib import Path

ROOT = Path("/home/phnx/kiro-kontakt-patch")
FILES = [
    ROOT / "public/catalogs/DS-CATALOG-portable.html",
    ROOT / "public/catalogs/KONTAKT-CATALOG-portable.html",
]

SYNC_OLD = """function syncHdrMenuBtns(){
  var searchOn=!document.body.classList.contains('search-chrome-collapsed');
  var fw=document.getElementById('filterWrap');
  var kwOn=!document.body.classList.contains('kw-chrome-collapsed')&&!!(fw&&fw.classList.contains('open'));
  var sb=document.getElementById('hdrSearchBtn');
  var kb=document.getElementById('hdrKwBtn');
  if(sb){sb.classList.toggle('is-on',searchOn);sb.setAttribute('aria-pressed',searchOn?'true':'false');sb.title=searchOn?'Hide Search':'Show Search';}
  if(kb){kb.classList.toggle('is-on',kwOn);kb.setAttribute('aria-pressed',kwOn?'true':'false');kb.title=kwOn?'Hide Keywords':'Show Keywords';}
}"""

SYNC_NEW = """function syncHdrMenuBtns(){
  var searchOn=!document.body.classList.contains('search-chrome-collapsed');
  var fw=document.getElementById('filterWrap');
  var kwOn=!document.body.classList.contains('kw-chrome-collapsed')&&!!(fw&&fw.classList.contains('open'));
  var wrap=document.getElementById('hdrMenuBtns');
  var sb=document.getElementById('hdrSearchBtn');
  var kb=document.getElementById('hdrKwBtn');
  var flip=!!(window.CATALOG_PORTABLE&&document.body.classList.contains('sides-portrait-flip'));
  if(wrap&&sb&&kb){
    if(flip){if(wrap.firstElementChild!==kb)wrap.insertBefore(kb,sb);}
    else if(wrap.firstElementChild!==sb)wrap.insertBefore(sb,kb);
  }
  if(sb){
    sb.classList.toggle('is-on',searchOn);
    sb.setAttribute('aria-pressed',searchOn?'true':'false');
    sb.title=(searchOn?'Hide Search':'Show Search')+(flip?' (right)':' (left)');
    sb.setAttribute('aria-label','Search, '+(flip?'right':'left'));
  }
  if(kb){
    kb.classList.toggle('is-on',kwOn);
    kb.setAttribute('aria-pressed',kwOn?'true':'false');
    kb.title=(kwOn?'Hide Keywords':'Show Keywords')+(flip?' (left)':' (right)');
    kb.setAttribute('aria-label','Keywords, '+(flip?'left':'right'));
  }
}"""

APPLY_TOGGLE_OLD = """    document.body.classList.toggle('sides-portrait-flip',flip);
    ensurePortraitFlipBtn();"""

APPLY_TOGGLE_NEW = """    document.body.classList.toggle('sides-portrait-flip',flip);
    if(typeof syncHdrMenuBtns==='function')syncHdrMenuBtns();
    ensurePortraitFlipBtn();"""

APPLY_MID_OLD = """      document.body.classList.remove('sides-portrait-flip');
      if(typeof syncPortraitFlipBtn==='function')syncPortraitFlipBtn();
      return;"""

APPLY_MID_NEW = """      document.body.classList.remove('sides-portrait-flip');
      if(typeof syncHdrMenuBtns==='function')syncHdrMenuBtns();
      if(typeof syncPortraitFlipBtn==='function')syncPortraitFlipBtn();
      return;"""

FLIP_END_OLD = """    applyPortraitSides();
    if(typeof placeSidesHandles==='function')placeSidesHandles();
    // #region agent log
    if(typeof dbgMobileUi==='function')dbgMobileUi('flip-panes',{hyp:'H-FLIP'});"""

FLIP_END_NEW = """    applyPortraitSides();
    if(typeof syncHdrMenuBtns==='function')syncHdrMenuBtns();
    if(typeof placeSidesHandles==='function')placeSidesHandles();
    // #region agent log
    if(typeof dbgMobileUi==='function')dbgMobileUi('flip-panes',{hyp:'H-FLIP'});"""


def patch(text: str) -> str:
    for old, new in (
        (SYNC_OLD, SYNC_NEW),
        (APPLY_TOGGLE_OLD, APPLY_TOGGLE_NEW),
        (APPLY_MID_OLD, APPLY_MID_NEW),
        (FLIP_END_OLD, FLIP_END_NEW),
    ):
        if old not in text:
            raise SystemExit("missing snippet:\n" + old[:160])
        text = text.replace(old, new, 1)
    return text


def main():
    for path in FILES:
        raw = path.read_text(encoding="utf-8")
        out = patch(raw)
        path.write_text(out, encoding="utf-8")
        print("patched", path.name, "delta", len(out) - len(raw))


if __name__ == "__main__":
    main()
