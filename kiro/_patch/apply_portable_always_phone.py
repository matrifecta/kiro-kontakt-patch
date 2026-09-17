#!/usr/bin/env python3
"""Portable catalogs: always-phone layout + Flip swaps Search/Keywords."""
from pathlib import Path

ROOT = Path("/home/phnx/kiro-kontakt-patch")
FILES = [
    ROOT / "public/catalogs/DS-CATALOG-portable.html",
    ROOT / "public/catalogs/KONTAKT-CATALOG-portable.html",
]

FLIP_MARK = "/* fix-PORTABLE-FLIP-MENUS: Search/Keywords swap when both open */"
FLIP_CSS = r"""
/* fix-PORTABLE-FLIP-MENUS: Search/Keywords swap when both open */
@media all{
  body.catalog-portable.sides-portrait-flip.display-sides:not(.display-middle).kw-open:not(.kw-chrome-collapsed):not(.search-chrome-collapsed) #searchChrome,
  body.catalog-portable.sides-portrait-flip.display-sides.dual-fs-open #searchChrome,
  body.catalog-portable.sides-portrait-flip.display-sides.ac-fs-open.kw-fs-open #searchChrome,
  body.catalog-portable.sides-portrait-flip.display-fs #searchChrome,
  body.catalog-portable.sides-portrait-flip.display-fs #acShell,
  body.catalog-portable.sides-portrait-flip.display-fs #acShell.ac-fs{
    grid-column:2!important
  }
  body.catalog-portable.sides-portrait-flip.display-sides:not(.display-middle).kw-open:not(.kw-chrome-collapsed):not(.search-chrome-collapsed) #filterWrap,
  body.catalog-portable.sides-portrait-flip.display-sides.dual-fs-open #filterWrap,
  body.catalog-portable.sides-portrait-flip.display-sides.ac-fs-open.kw-fs-open #filterWrap,
  body.catalog-portable.sides-portrait-flip.display-fs #filterWrap,
  body.catalog-portable.sides-portrait-flip.display-fs.kw-fs-open #filterWrap{
    grid-column:1!important
  }
}
@media(orientation:portrait){
  body.catalog-portable.sides-portrait-flip.display-sides:not(.display-middle).kw-open:not(.search-chrome-collapsed):not(.dual-fs-open) #searchChrome{
    grid-column:2!important;grid-row:3!important
  }
  body.catalog-portable.sides-portrait-flip.display-sides:not(.display-middle).kw-open:not(.search-chrome-collapsed):not(.dual-fs-open) #filterWrap{
    grid-column:2!important;grid-row:2!important
  }
  body.catalog-portable.sides-portrait-flip.dual-fs-open #acShell.ac-fs,
  body.catalog-portable.sides-portrait-flip.display-sides.dual-fs-open #acShell.ac-fs{
    top:50%!important;bottom:0!important;left:0!important;right:0!important
  }
  body.catalog-portable.sides-portrait-flip.dual-fs-open #filterWrap,
  body.catalog-portable.sides-portrait-flip.display-sides.dual-fs-open #filterWrap{
    top:var(--cat-header-h,3.5rem)!important;bottom:50%!important
  }
}
@media(orientation:landscape){
  body.catalog-portable.sides-portrait-flip.dual-fs-open #acShell.ac-fs,
  body.catalog-portable.sides-portrait-flip.display-sides.dual-fs-open #acShell.ac-fs{
    left:50%!important;right:0!important
  }
  body.catalog-portable.sides-portrait-flip.dual-fs-open #filterWrap,
  body.catalog-portable.sides-portrait-flip.display-sides.dual-fs-open #filterWrap{
    left:0!important;right:50%!important
  }
}
"""

PHONE_FN_OLD = """function isPhoneViewport(){
  try{
    return window.matchMedia('(max-width:899px)').matches
      || window.matchMedia('(hover:none) and (pointer:coarse)').matches;
  }catch(err){return false;}
}"""

PHONE_FN_NEW = """function isPhoneViewport(){
  if(window.CATALOG_PORTABLE)return true;
  try{
    return window.matchMedia('(max-width:899px)').matches
      || window.matchMedia('(hover:none) and (pointer:coarse)').matches;
  }catch(err){return false;}
}"""

DESK_OLD = "function displayIsDesktop(){return !!(window.matchMedia&&window.matchMedia('(min-width:900px)').matches);}"
DESK_NEW = "function displayIsDesktop(){if(window.CATALOG_PORTABLE)return false;return !!(window.matchMedia&&window.matchMedia('(min-width:900px)').matches);}"

PORT_OLD = "  function isPortraitDesktopSides(){return !!(window.matchMedia&&window.matchMedia('(min-width:900px)').matches&&window.matchMedia('(orientation:portrait)').matches);}"
PORT_NEW = "  function isPortraitDesktopSides(){if(window.CATALOG_PORTABLE)return false;return !!(window.matchMedia&&window.matchMedia('(min-width:900px)').matches&&window.matchMedia('(orientation:portrait)').matches);}"

APPLY_P_OLD = """    var sides=document.body.classList.contains('display-sides');
    if(typeof displayIsMiddle==='function'?displayIsMiddle():document.body.classList.contains('display-middle')){
      document.body.classList.remove('sides-portrait-flip');
      if(typeof syncPortraitFlipBtn==='function')syncPortraitFlipBtn();
      return;
    }
    var portrait=isPortraitDesktopSides();
    var phone=typeof isPhoneViewport==='function'&&isPhoneViewport();
    var flip=sides&&(portrait||phone)&&portraitFlipOn();
    document.body.classList.toggle('sides-portrait-flip',flip);
    ensurePortraitFlipBtn();
    if(!sides||(!portrait&&!phone)){
      syncPortraitFlipBtn();
      return;
    }
    var d=portraitSidesDefaults();"""

APPLY_P_NEW = """    var sides=document.body.classList.contains('display-sides');
    var fs=document.body.classList.contains('display-fs');
    if(typeof displayIsMiddle==='function'?displayIsMiddle():document.body.classList.contains('display-middle')){
      document.body.classList.remove('sides-portrait-flip');
      if(typeof syncPortraitFlipBtn==='function')syncPortraitFlipBtn();
      return;
    }
    var portrait=isPortraitDesktopSides();
    var phone=typeof isPhoneViewport==='function'&&isPhoneViewport();
    var flip=(sides||fs)&&(portrait||phone)&&portraitFlipOn();
    document.body.classList.toggle('sides-portrait-flip',flip);
    ensurePortraitFlipBtn();
    if((!sides&&!fs)||(!portrait&&!phone)){
      syncPortraitFlipBtn();
      return;
    }
    if(window.CATALOG_PORTABLE){
      syncPortraitFlipBtn();
      return;
    }
    var d=portraitSidesDefaults();"""

SIDES_LW_OLD = """  if(middle){
    /* middle uses --middle-* ; keep widescreen --sides-lw/--sides-rw intact */
  }else if(portrait){
    /* portrait uses --portrait-* buckets; do not overwrite widescreen --sides-lw/--sides-rw */
  }else if(document.body.classList.contains('search-chrome-collapsed')){
    document.body.style.setProperty('--sides-lw','0px');
  }else{
    lw=Math.max(minL,Math.min(lw,vw-minR-minC-2*(parseFloat(getComputedStyle(document.documentElement).getPropertyValue('--sides-pane-gap'))||6)));
    document.body.style.setProperty('--sides-lw',lw+'px');
  }
  if(typeof applySidesIndexH==='function')applySidesIndexH();
  if(portrait){
  }else if(document.body.classList.contains('kw-chrome-collapsed')){"""

SIDES_LW_NEW = """  if(middle){
    /* middle uses --middle-* ; keep widescreen --sides-lw/--sides-rw intact */
  }else if(portrait){
    /* portrait uses --portrait-* buckets; do not overwrite widescreen --sides-lw/--sides-rw */
  }else if(phone||window.CATALOG_PORTABLE){
    document.body.style.removeProperty('--sides-lw');
    document.body.style.removeProperty('--sides-rw');
  }else if(document.body.classList.contains('search-chrome-collapsed')){
    document.body.style.setProperty('--sides-lw','0px');
  }else{
    lw=Math.max(minL,Math.min(lw,vw-minR-minC-2*(parseFloat(getComputedStyle(document.documentElement).getPropertyValue('--sides-pane-gap'))||6)));
    document.body.style.setProperty('--sides-lw',lw+'px');
  }
  if(typeof applySidesIndexH==='function')applySidesIndexH();
  if(portrait||phone||window.CATALOG_PORTABLE){
  }else if(document.body.classList.contains('kw-chrome-collapsed')){"""

TOGGLE_OLD = """  function togglePortraitSidesFlip(){
    if(typeof snapshotCurrentLayoutBucket==='function'){snapshotCurrentLayoutBucket();lastLayoutBucket='pending';}
    writePortraitFlip(!portraitFlipOn());
    applyPortraitSides();
    if(typeof placeSidesHandles==='function')placeSidesHandles();
    
  }"""

TOGGLE_NEW = """  function togglePortraitSidesFlip(){
    if(typeof snapshotCurrentLayoutBucket==='function'){snapshotCurrentLayoutBucket();lastLayoutBucket='pending';}
    writePortraitFlip(!portraitFlipOn());
    applyPortraitSides();
    if(typeof placeSidesHandles==='function')placeSidesHandles();
    // #region agent log
    if(typeof dbgMobileUi==='function')dbgMobileUi('flip-panes',{hyp:'H-FLIP'});
    // #endregion
  }"""

SET_OLD = "  if(typeof dbgMobileUi==='function')dbgMobileUi('setDisplayMode');"
SET_NEW = "  if(typeof dbgMobileUi==='function')dbgMobileUi('setDisplayMode',{hyp:'H-P1'});"

KW_OLD = """function toggleKwChrome(){
  if(!document.body.classList.contains('display-sides')){
    if(typeof toggleFilter==='function')toggleFilter();
    return;
  }
  if(document.body.classList.contains('kw-chrome-collapsed')) expandKwMenu();
  else collapseKwMenu();
}"""

KW_NEW = """function toggleKwChrome(){
  if(!document.body.classList.contains('display-sides')){
    if(typeof toggleFilter==='function')toggleFilter();
    return;
  }
  var fw=document.getElementById('filterWrap');
  var open=document.body.classList.contains('kw-open')&&fw&&fw.classList.contains('open')&&!document.body.classList.contains('kw-chrome-collapsed');
  if(open) collapseKwMenu();
  else expandKwMenu();
}"""

MQ_REPLACES = [
    (
        "@media(max-width:899px) and (orientation:landscape),(hover:none) and (pointer:coarse) and (orientation:landscape){",
        "@media(orientation:landscape){",
    ),
    (
        "@media(max-width:899px) and (orientation:portrait),(hover:none) and (pointer:coarse) and (orientation:portrait){",
        "@media(orientation:portrait){",
    ),
    (
        "@media (max-width:899px),(hover:none) and (pointer:coarse){",
        "@media all{",
    ),
    (
        "@media(max-width:899px),(hover:none) and (pointer:coarse){",
        "@media all{",
    ),
]


def patch(text: str) -> str:
    for old, new in MQ_REPLACES:
        text = text.replace(old, new)
    swaps = [
        (PHONE_FN_OLD, PHONE_FN_NEW),
        (DESK_OLD, DESK_NEW),
        (PORT_OLD, PORT_NEW),
        (APPLY_P_OLD, APPLY_P_NEW),
        (SIDES_LW_OLD, SIDES_LW_NEW),
        (TOGGLE_OLD, TOGGLE_NEW),
        (SET_OLD, SET_NEW),
        (KW_OLD, KW_NEW),
    ]
    for old, new in swaps:
        if old not in text:
            raise SystemExit("missing snippet:\n" + old[:120])
        text = text.replace(old, new, 1)
    if FLIP_MARK not in text:
        needle = "</style></head>"
        if needle not in text:
            raise SystemExit("missing </style></head>")
        text = text.replace(needle, FLIP_CSS + needle, 1)
    return text


def main():
    for path in FILES:
        raw = path.read_text(encoding="utf-8")
        out = patch(raw)
        path.write_text(out, encoding="utf-8")
        print("patched", path.name, "delta", len(out) - len(raw))


if __name__ == "__main__":
    main()
