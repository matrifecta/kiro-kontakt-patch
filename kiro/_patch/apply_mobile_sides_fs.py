#!/usr/bin/env python3
"""Phone Sides/FS: side-by-side panes, no drawer overlay. Portable only."""
from pathlib import Path

ROOT = Path("/home/phnx/kiro-kontakt-patch")
FILES = [
    ROOT / "public/catalogs/DS-CATALOG-portable.html",
    ROOT / "public/catalogs/KONTAKT-CATALOG-portable.html",
]

CSS_MARK = "/* fix-PHONE-SIDES-FS: side-by-side panes, no drawer overlay */"
CSS_ADD = r"""
/* fix-PHONE-SIDES-FS: side-by-side panes, no drawer overlay */
@media(max-width:899px),(hover:none) and (pointer:coarse){
  body.catalog-portable .display-btn[data-display="upper"],
  body.catalog-portable .display-btn[data-display="fs"]{display:none!important}
  body.catalog-portable.display-sides:not(.display-middle){
    display:grid!important;flex-direction:unset!important;
    grid-template-columns:minmax(0,42%) minmax(0,1fr)!important;
    grid-template-rows:auto minmax(0,1fr)!important;
    height:100dvh;overflow:hidden
  }
  body.catalog-portable.display-sides:not(.display-middle) .catalog-header{
    grid-column:1/-1!important;grid-row:1!important;position:sticky!important;top:0;z-index:320
  }
  body.catalog-portable.display-sides:not(.display-middle) #searchChrome{
    grid-column:1!important;grid-row:2!important;
    position:relative!important;inset:auto!important;
    width:auto!important;max-width:none!important;max-height:none!important;height:auto!important;
    overflow:hidden!important;display:flex!important;flex-direction:column!important;
    border-right:1px solid var(--border)!important;z-index:5
  }
  body.catalog-portable.display-sides:not(.display-middle) #catalogMain{
    grid-column:2!important;grid-row:2!important;min-height:0;overflow-y:auto!important;width:auto!important
  }
  body.catalog-portable.display-sides:not(.display-middle) #filterWrap,
  body.catalog-portable.display-sides:not(.display-middle).kw-open #filterWrap{
    position:relative!important;inset:auto!important;right:auto!important;top:auto!important;bottom:auto!important;left:auto!important;
    transform:none!important;width:100%!important;max-width:100%!important;min-width:0!important;
    height:auto!important;max-height:none!important;overflow:hidden!important;box-sizing:border-box!important;
    z-index:6!important;box-shadow:none!important
  }
  body.catalog-portable.display-sides:not(.display-middle) #filterWrap .filter-panel,
  body.catalog-portable.display-sides:not(.display-middle) #kwbar{min-width:0!important;max-width:100%!important;overflow-x:hidden!important}
  body.catalog-portable.display-sides:not(.display-middle):not(.kw-open) #filterWrap,
  body.catalog-portable.display-sides:not(.display-middle).kw-chrome-collapsed #filterWrap{display:none!important}
  body.catalog-portable.display-sides:not(.display-middle).search-chrome-collapsed #searchChrome{display:none!important}
  body.catalog-portable.display-sides:not(.display-middle).search-chrome-collapsed:not(.kw-open){
    grid-template-columns:minmax(0,1fr)!important
  }
  body.catalog-portable.display-sides:not(.display-middle).search-chrome-collapsed:not(.kw-open) #catalogMain{grid-column:1/-1!important}
  body.catalog-portable.display-sides:not(.display-middle).search-chrome-collapsed.kw-open:not(.kw-chrome-collapsed){
    grid-template-columns:minmax(0,1fr) minmax(0,42%)!important
  }
  body.catalog-portable.display-sides:not(.display-middle).search-chrome-collapsed.kw-open:not(.kw-chrome-collapsed) #filterWrap{
    grid-column:2!important;grid-row:2!important;display:flex!important
  }
  body.catalog-portable.display-sides:not(.display-middle).search-chrome-collapsed.kw-open:not(.kw-chrome-collapsed) #catalogMain{grid-column:1!important}
  body.catalog-portable.display-sides:not(.display-middle).search-chrome-collapsed.kw-open.sides-portrait-flip{
    grid-template-columns:minmax(0,42%) minmax(0,1fr)!important
  }
  body.catalog-portable.display-sides:not(.display-middle).search-chrome-collapsed.kw-open.sides-portrait-flip #filterWrap{grid-column:1!important}
  body.catalog-portable.display-sides:not(.display-middle).search-chrome-collapsed.kw-open.sides-portrait-flip #catalogMain{grid-column:2!important}
  body.catalog-portable.display-sides:not(.display-middle).sides-portrait-flip:not(.search-chrome-collapsed):not(.kw-open){
    grid-template-columns:minmax(0,1fr) minmax(0,42%)!important
  }
  body.catalog-portable.display-sides:not(.display-middle).sides-portrait-flip:not(.search-chrome-collapsed):not(.kw-open) #searchChrome{grid-column:2!important}
  body.catalog-portable.display-sides:not(.display-middle).sides-portrait-flip:not(.search-chrome-collapsed):not(.kw-open) #catalogMain{grid-column:1!important}
  body.catalog-portable.ac-fs-open:not(.dual-fs-open) #acShell.ac-fs,
  body.catalog-portable.display-sides.ac-fs-open:not(.dual-fs-open) #acShell.ac-fs{
    position:relative!important;inset:auto!important;top:auto!important;left:auto!important;right:auto!important;bottom:auto!important;
    width:auto!important;height:auto!important;max-width:none!important;max-height:none!important;
    flex:1 1 auto!important;z-index:6!important
  }
  body.catalog-portable.kw-fs-open:not(.dual-fs-open) #filterWrap,
  body.catalog-portable.display-sides.kw-fs-open:not(.dual-fs-open) #filterWrap,
  body.catalog-portable.display-sides.display-middle.kw-fs-open:not(.dual-fs-open) #filterWrap{
    position:relative!important;inset:auto!important;transform:none!important;
    width:auto!important;max-width:none!important;max-height:none!important;height:auto!important;z-index:6!important
  }
  body.catalog-portable #searchSplit,body.catalog-portable #dualFsSep{display:none!important}
}
@media(max-width:899px) and (orientation:landscape),(hover:none) and (pointer:coarse) and (orientation:landscape){
  body.catalog-portable .display-btn[data-display="middle"]{display:none!important}
  body.catalog-portable.display-sides:not(.display-middle).kw-open:not(.kw-chrome-collapsed):not(.search-chrome-collapsed),
  body.catalog-portable.display-sides.dual-fs-open,
  body.catalog-portable.display-sides.ac-fs-open.kw-fs-open{
    grid-template-columns:minmax(0,1fr) minmax(0,1fr)!important;
    grid-template-rows:auto minmax(0,1fr)!important
  }
  body.catalog-portable.display-sides:not(.display-middle).kw-open:not(.kw-chrome-collapsed):not(.search-chrome-collapsed) #filterWrap,
  body.catalog-portable.display-sides.dual-fs-open #filterWrap,
  body.catalog-portable.display-sides.ac-fs-open.kw-fs-open #filterWrap{
    grid-column:2!important;grid-row:2!important;display:flex!important;
    position:relative!important;transform:none!important;inset:auto!important;
    width:auto!important;max-width:none!important;height:auto!important;max-height:none!important
  }
  body.catalog-portable.display-sides:not(.display-middle).kw-open:not(.kw-chrome-collapsed):not(.search-chrome-collapsed) #catalogMain,
  body.catalog-portable.display-sides.dual-fs-open #catalogMain,
  body.catalog-portable.display-sides.ac-fs-open.kw-fs-open #catalogMain{display:none!important}
}
@media(max-width:899px) and (orientation:portrait),(hover:none) and (pointer:coarse) and (orientation:portrait){
  body.catalog-portable.display-sides:not(.display-middle).kw-open:not(.kw-chrome-collapsed):not(.search-chrome-collapsed):not(.dual-fs-open){
    grid-template-columns:minmax(0,42%) minmax(0,1fr)!important;
    grid-template-rows:auto minmax(0,1fr) minmax(0,1fr)!important
  }
  body.catalog-portable.display-sides:not(.display-middle).kw-open:not(.search-chrome-collapsed):not(.dual-fs-open) #searchChrome{
    grid-column:1!important;grid-row:2!important
  }
  body.catalog-portable.display-sides:not(.display-middle).kw-open:not(.search-chrome-collapsed):not(.dual-fs-open) #filterWrap{
    grid-column:1!important;grid-row:3!important;display:flex!important
  }
  body.catalog-portable.display-sides:not(.display-middle).kw-open:not(.search-chrome-collapsed):not(.dual-fs-open) #catalogMain{
    grid-column:2!important;grid-row:2/-1!important;display:block!important
  }
  body.catalog-portable.display-sides:not(.display-middle).kw-open:not(.search-chrome-collapsed):not(.dual-fs-open).sides-portrait-flip{
    grid-template-columns:minmax(0,1fr) minmax(0,42%)!important
  }
  body.catalog-portable.display-sides:not(.display-middle).kw-open:not(.search-chrome-collapsed):not(.dual-fs-open).sides-portrait-flip #searchChrome,
  body.catalog-portable.display-sides:not(.display-middle).kw-open:not(.search-chrome-collapsed):not(.dual-fs-open).sides-portrait-flip #filterWrap{grid-column:2!important}
  body.catalog-portable.display-sides:not(.display-middle).kw-open:not(.search-chrome-collapsed):not(.dual-fs-open).sides-portrait-flip #catalogMain{grid-column:1!important}
  body.catalog-portable.display-sides.dual-fs-open,
  body.catalog-portable.display-sides.ac-fs-open.kw-fs-open{
    grid-template-columns:minmax(0,1fr) minmax(0,1fr)!important;
    grid-template-rows:auto minmax(0,1fr)!important
  }
  body.catalog-portable.display-sides.dual-fs-open #filterWrap,
  body.catalog-portable.display-sides.ac-fs-open.kw-fs-open #filterWrap{
    grid-column:2!important;grid-row:2!important;display:flex!important
  }
  body.catalog-portable.display-sides.dual-fs-open #catalogMain,
  body.catalog-portable.display-sides.ac-fs-open.kw-fs-open #catalogMain{display:none!important}
  body.catalog-portable.display-sides.display-middle{
    display:flex!important;flex-direction:column!important;
    grid-template-columns:none!important;grid-template-rows:none!important
  }
  body.catalog-portable.display-sides.display-middle .catalog-header{grid-column:auto!important;grid-row:auto!important;flex:0 0 auto}
  body.catalog-portable.display-sides.display-middle #searchChrome{
    grid-column:auto!important;grid-row:auto!important;
    width:100%!important;max-height:min(32dvh,15rem)!important;height:auto!important;min-height:6.5rem!important;
    flex:0 0 auto!important;overflow:auto!important;border-right:0!important
  }
  body.catalog-portable.display-sides.display-middle #filterWrap,
  body.catalog-portable.display-sides.display-middle.kw-open #filterWrap{
    grid-column:auto!important;grid-row:auto!important;
    position:relative!important;inset:auto!important;transform:none!important;
    width:100%!important;max-width:100%!important;min-height:7.5rem!important;
    max-height:min(32dvh,15rem)!important;height:auto!important;flex:0 0 auto!important;overflow:auto!important;z-index:6!important
  }
  body.catalog-portable.display-sides.display-middle:not(.kw-open) #filterWrap,
  body.catalog-portable.display-sides.display-middle.kw-chrome-collapsed #filterWrap{display:none!important}
  body.catalog-portable.display-sides.display-middle #catalogMain{
    grid-column:auto!important;grid-row:auto!important;flex:1 1 auto;width:100%!important;min-height:0
  }
}
"""

PLACE_OLD = """    if(typeof isPhoneViewport==='function'&&isPhoneViewport()){
      var hdr=document.querySelector('.catalog-header');
      if(hdr)top=Math.max(top,hdr.getBoundingClientRect().bottom);
      height=Math.max(80,box.bottom-top);
    }
    sh.style.top=Math.round(top)+'px';
    sh.style.left=Math.round(left)+'px';
    sh.style.right='auto';
    sh.style.bottom='auto';
    sh.style.width=Math.round(width)+'px';
    sh.style.height=Math.round(height)+'px';
    sh.style.maxWidth='none';
    sh.style.maxHeight=Math.round(height)+'px';
    syncAcWidthBtn();
    return;"""

PLACE_NEW = """    if(typeof isPhoneViewport==='function'&&isPhoneViewport()){
      ['top','left','right','bottom','width','height','max-width','max-height'].forEach(function(p){sh.style.removeProperty(p);});
      syncAcWidthBtn();
      return;
    }
    sh.style.top=Math.round(top)+'px';
    sh.style.left=Math.round(left)+'px';
    sh.style.right='auto';
    sh.style.bottom='auto';
    sh.style.width=Math.round(width)+'px';
    sh.style.height=Math.round(height)+'px';
    sh.style.maxWidth='none';
    sh.style.maxHeight=Math.round(height)+'px';
    syncAcWidthBtn();
    return;"""

SIDES_OLD = """  var middle=typeof displayIsMiddle==='function'?displayIsMiddle():document.body.classList.contains('display-middle');
  var portrait=typeof isPortraitDesktopSides==='function'&&isPortraitDesktopSides();
  document.body.classList.toggle('sides-orient-portrait',!!portrait&&!middle);
  if(middle){
    document.body.classList.remove('sides-portrait-flip');
    if(typeof applyMiddleLayout==='function')applyMiddleLayout();
  }else if(portrait){
    var flipOn=typeof window.portraitFlipOn==='function'?window.portraitFlipOn():document.body.classList.contains('sides-portrait-flip');
    document.body.classList.toggle('sides-portrait-flip',!!flipOn);
  }else{
    document.body.classList.remove('sides-portrait-flip');
  }"""

SIDES_NEW = """  var middle=typeof displayIsMiddle==='function'?displayIsMiddle():document.body.classList.contains('display-middle');
  var portrait=typeof isPortraitDesktopSides==='function'&&isPortraitDesktopSides();
  var phone=typeof isPhoneViewport==='function'&&isPhoneViewport();
  document.body.classList.toggle('sides-orient-portrait',!!((portrait||(phone&&window.matchMedia&&window.matchMedia('(orientation:portrait)').matches))&&!middle));
  if(middle){
    document.body.classList.remove('sides-portrait-flip');
    if(typeof applyMiddleLayout==='function')applyMiddleLayout();
  }else if(portrait||phone){
    var flipOn=typeof window.portraitFlipOn==='function'?window.portraitFlipOn():document.body.classList.contains('sides-portrait-flip');
    document.body.classList.toggle('sides-portrait-flip',!!flipOn);
  }else{
    document.body.classList.remove('sides-portrait-flip');
  }"""

APPLY_P_OLD = """    var portrait=isPortraitDesktopSides();
    var flip=sides&&portrait&&portraitFlipOn();
    document.body.classList.toggle('sides-portrait-flip',flip);
    ensurePortraitFlipBtn();
    if(!sides||!portrait){"""

APPLY_P_NEW = """    var portrait=isPortraitDesktopSides();
    var phone=typeof isPhoneViewport==='function'&&isPhoneViewport();
    var flip=sides&&(portrait||phone)&&portraitFlipOn();
    document.body.classList.toggle('sides-portrait-flip',flip);
    ensurePortraitFlipBtn();
    if(!sides||(!portrait&&!phone)){"""

MODE_OLD = """  if(mode==='upper'||mode==='fs')mode='sides';
  var persistDisplay=mode;"""

MODE_NEW = """  if(mode==='upper'||mode==='fs')mode='sides';
  var persistDisplay=mode;
  if(typeof isPhoneViewport==='function'&&isPhoneViewport()&&persistDisplay==='middle'&&window.matchMedia&&!window.matchMedia('(orientation:portrait)').matches){
    persistDisplay='sides';mode='sides';
  }"""

MORE_OLD = """  phoneMoreAdd(pop,'Clear on miss',function(){var x=document.getElementById('clearMissBtn');if(x)x.click();});
  phoneMoreAdd(pop,'Customize',function(){if(typeof toggleLayoutEdit==='function')toggleLayoutEdit();});
  phoneMoreAdd(pop,'Layouts',function(){var x=document.getElementById('layoutPresetsBtn');if(x)x.click();});
  phoneMoreAdd(pop,'Smaller UI',function(){if(typeof stepUiScale==='function')stepUiScale(-1);});"""

MORE_NEW = """  phoneMoreAdd(pop,'Clear on miss',function(){var x=document.getElementById('clearMissBtn');if(x)x.click();});
  phoneMoreAdd(pop,'Flip panes',function(){if(typeof togglePortraitSidesFlip==='function')togglePortraitSidesFlip();});
  phoneMoreAdd(pop,'Smaller UI',function(){if(typeof stepUiScale==='function')stepUiScale(-1);});"""

KWMORE_OLD = """  phoneMoreAdd(pop,'Customize',function(){if(typeof toggleLayoutEdit==='function')toggleLayoutEdit();});
  phoneMoreAdd(pop,'Layouts',function(){var x=document.getElementById('layoutPresetsBtn');if(x)x.click();});
  phoneMoreAdd(pop,'Smaller UI',function(){if(typeof stepUiScale==='function')stepUiScale(-1);});"""

KWMORE_NEW = """  phoneMoreAdd(pop,'Flip panes',function(){if(typeof togglePortraitSidesFlip==='function')togglePortraitSidesFlip();});
  phoneMoreAdd(pop,'Smaller UI',function(){if(typeof stepUiScale==='function')stepUiScale(-1);});"""

RUNID_OLD = "runId:'pre-fix'"
RUNID_NEW = "runId:'post-fix'"


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
        t = sub(t, PLACE_OLD, PLACE_NEW, "place-ac", path)
        t = sub(t, SIDES_OLD, SIDES_NEW, "sides-cols", path)
        t = sub(t, APPLY_P_OLD, APPLY_P_NEW, "apply-portrait", path)
        t = sub(t, MODE_OLD, MODE_NEW, "mode-coerce", path)
        t = sub(t, MORE_OLD, MORE_NEW, "hdr-more", path)
        t = sub(t, KWMORE_OLD, KWMORE_NEW, "kw-more", path)
        if RUNID_OLD in t:
            t = t.replace(RUNID_OLD, RUNID_NEW)
            print(f"  runId {path.name}")
        path.write_text(t, encoding="utf-8")
        print("ok", path.name)


if __name__ == "__main__":
    main()
