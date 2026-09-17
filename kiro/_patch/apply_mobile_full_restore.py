#!/usr/bin/env python3
"""Restore phone Full (menu+menu / one menu) beside Sides and Middle. Portable only."""
from pathlib import Path

ROOT = Path("/home/phnx/kiro-kontakt-patch")
FILES = [
    ROOT / "public/catalogs/DS-CATALOG-portable.html",
    ROOT / "public/catalogs/KONTAKT-CATALOG-portable.html",
]

CSS_MARK = "/* fix-PHONE-FULL: restore Full two-menu switch */"
CSS_ADD = r"""
/* fix-PHONE-FULL: restore Full two-menu switch */
@media(max-width:899px),(hover:none) and (pointer:coarse){
  body.catalog-portable .display-btn[data-display="fs"]{display:inline-flex!important}
  body.catalog-portable .display-btn[data-display="upper"]{display:none!important}
  body.catalog-portable.display-fs{
    display:grid!important;flex-direction:unset!important;
    grid-template-columns:minmax(0,1fr) minmax(0,1fr)!important;
    grid-template-rows:auto minmax(0,1fr)!important;
    height:100dvh;overflow:hidden
  }
  body.catalog-portable.display-fs .catalog-header{
    grid-column:1/-1!important;grid-row:1!important;position:sticky!important;top:0;z-index:320
  }
  body.catalog-portable.display-fs #searchChrome,
  body.catalog-portable.display-fs #acShell,
  body.catalog-portable.display-fs #acShell.ac-fs{
    grid-column:1!important;grid-row:2!important;
    position:relative!important;inset:auto!important;top:auto!important;left:auto!important;
    width:auto!important;height:auto!important;max-height:none!important;max-width:none!important;
    overflow:hidden!important;display:flex!important;flex-direction:column!important;z-index:6
  }
  body.catalog-portable.display-fs #filterWrap,
  body.catalog-portable.display-fs.kw-fs-open #filterWrap{
    grid-column:2!important;grid-row:2!important;
    position:relative!important;inset:auto!important;transform:none!important;
    width:auto!important;max-width:none!important;height:auto!important;max-height:none!important;
    overflow:hidden!important;display:flex!important;flex-direction:column!important;z-index:6;box-shadow:none!important
  }
  body.catalog-portable.display-fs:not(.ac-fs-open) #searchChrome{display:none!important}
  body.catalog-portable.display-fs:not(.kw-fs-open) #filterWrap{display:none!important}
  body.catalog-portable.display-fs:not(.dual-fs-open).ac-fs-open #searchChrome,
  body.catalog-portable.display-fs:not(.dual-fs-open).ac-fs-open #acShell.ac-fs{grid-column:1/-1!important}
  body.catalog-portable.display-fs:not(.dual-fs-open).kw-fs-open #filterWrap{grid-column:1/-1!important}
  body.catalog-portable.display-fs #catalogMain{display:none!important}
  body.catalog-portable.display-fs.ac-fs-open .kw-companion-btn,
  body.catalog-portable.display-fs.kw-fs-open .ac-companion-btn,
  body.catalog-portable.display-fs.ac-fs-open .ac-fs-back,
  body.catalog-portable.display-fs.kw-fs-open .kw-fs-back{display:inline-flex!important}
  body.catalog-portable.display-fs .fs-stripe-wrap,
  body.catalog-portable.display-fs .fs-mode-nav,
  body.catalog-portable.display-fs .filter-kw-tools{display:none!important}
  body.catalog-portable.display-fs #searchCol,
  body.catalog-portable.display-fs #searchChrome .search-strip-anchor,
  body.catalog-portable.display-fs #acShell,
  body.catalog-portable.display-fs #filterWrap .filter-panel{
    display:flex!important;flex-direction:column!important;flex:1 1 auto!important;min-height:0!important;overflow:hidden!important
  }
  body.catalog-portable.display-fs #acList,
  body.catalog-portable.display-fs #filterWrap .filter-panel{
    overflow-y:auto!important;-webkit-overflow-scrolling:touch!important;touch-action:pan-y!important
  }
}
"""

NORM_OLD = """function normalizeDisplayMode(m){
  if(m==='middle'||m==='sides')return m;
  if(m==='upper'||m==='fs')return 'sides';
  return '';
}"""

NORM_NEW = """function normalizeDisplayMode(m){
  if(m==='middle'||m==='sides')return m;
  if(m==='fs'&&typeof isPhoneViewport==='function'&&isPhoneViewport())return 'fs';
  if(m==='upper'||m==='fs')return 'sides';
  return '';
}"""

MODE_OLD = """  if(mode!=='upper'&&mode!=='sides'&&mode!=='fs'&&mode!=='middle')mode='sides';
  if(mode==='upper'||mode==='fs')mode='sides';"""

MODE_NEW = """  if(mode!=='upper'&&mode!=='sides'&&mode!=='fs'&&mode!=='middle')mode='sides';
  if(mode==='upper')mode=(typeof isPhoneViewport==='function'&&isPhoneViewport())?'middle':'sides';
  if(mode==='fs'&&!(typeof isPhoneViewport==='function'&&isPhoneViewport()))mode='sides';"""

BOOT_OLD = """  if(m!=='upper'&&m!=='sides'&&m!=='fs'&&m!=='middle')m='sides';
  if(m==='upper'||m==='fs')m='sides';"""

BOOT_NEW = """  if(m!=='upper'&&m!=='sides'&&m!=='fs'&&m!=='middle')m='sides';
  if(m==='upper')m=(typeof isPhoneViewport==='function'&&isPhoneViewport())?'middle':'sides';
  if(m==='fs'&&!(typeof isPhoneViewport==='function'&&isPhoneViewport()))m='sides';"""

TOGGLE_OLD = """window.toggleKwFullscreen=function(){
  if(typeof isPhoneViewport==='function'&&isPhoneViewport()){
    if(typeof setKwFullscreen==='function')setKwFullscreen(!kwFsWanted);
    return;
  }
  if(typeof expandKwMenu==='function')expandKwMenu();
};
window.toggleAcFullscreen=function(){
  if(typeof isPhoneViewport==='function'&&isPhoneViewport()){
    if(typeof setAcFullscreen==='function')setAcFullscreen(!(typeof acFsWanted!=='undefined'&&acFsWanted));
    return;
  }
  if(typeof expandSearchMenu==='function')expandSearchMenu();
};"""

TOGGLE_NEW = """window.phoneExitFs=function(){
  var back=(typeof lastNonFsDisplay==='string'&&(lastNonFsDisplay==='middle'||lastNonFsDisplay==='sides'))?lastNonFsDisplay:'';
  if(!back)back=(window.matchMedia&&window.matchMedia('(orientation:portrait)').matches)?'middle':'sides';
  if(typeof setDisplayMode==='function')setDisplayMode(back,{pick:true});
};
window.toggleKwFullscreen=function(){
  if(typeof isPhoneViewport==='function'&&isPhoneViewport()){
    if(typeof currentDisplay!=='undefined'&&currentDisplay==='fs'){window.phoneExitFs();return;}
    if(typeof setDisplayMode==='function')setDisplayMode('fs',{menu:'keywords',pick:true});
    return;
  }
  if(typeof expandKwMenu==='function')expandKwMenu();
};
window.toggleAcFullscreen=function(){
  if(typeof isPhoneViewport==='function'&&isPhoneViewport()){
    if(typeof currentDisplay!=='undefined'&&currentDisplay==='fs'){window.phoneExitFs();return;}
    if(typeof setDisplayMode==='function')setDisplayMode('fs',{menu:'search',pick:true});
    return;
  }
  if(typeof expandSearchMenu==='function')expandSearchMenu();
};"""


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
        t = sub(t, NORM_OLD, NORM_NEW, "normalize", path)
        t = sub(t, MODE_OLD, MODE_NEW, "setDisplay", path)
        t = sub(t, BOOT_OLD, BOOT_NEW, "boot", path)
        t = sub(t, TOGGLE_OLD, TOGGLE_NEW, "toggle-fs", path)
        path.write_text(t, encoding="utf-8")
        print("ok", path.name)


if __name__ == "__main__":
    main()
