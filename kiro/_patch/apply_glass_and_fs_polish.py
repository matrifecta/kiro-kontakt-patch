#!/usr/bin/env python3
"""Patch KIRO catalog builders: magnifying-glass Search open + FS toolbar polish."""
from pathlib import Path

ART = Path("/home/phnx/KIRO/.kiro/specs/kontakt-workspace-drive-dirty-fix/artifacts")
FILES = [
    ART / "build-ds-catalog-html.sh",
    ART / "build-kontakt-catalog-html.sh",
]

REPLACEMENTS = [
    (
        """function acFsAvailable(){
  if(window.CATALOG_PORTABLE)return true;
  try{return window.matchMedia('(max-width:899px)').matches;}catch(err){return false;}
}""",
        """function acFsAvailable(){return true;}
function acCapDropdownHeight(){
  if(window.CATALOG_PORTABLE)return true;
  try{return window.matchMedia('(max-width:899px)').matches;}catch(err){return false;}
}""",
    ),
    (
        "if(acFsAvailable())maxH=Math.min(maxH,Math.max(6*r,0.5*box.height));",
        "if(acCapDropdownHeight())maxH=Math.min(maxH,Math.max(6*r,0.5*box.height));",
    ),
    (
        "body.ac-fs-open .kw-companion-btn{display:inline-flex}\n body.kw-fs-open .ac-companion-btn{display:inline-flex}",
        "body.ac-fs-open .kw-companion-btn{display:inline-flex}\n body.search-mode .ac-companion-btn,body.kw-fs-open .ac-companion-btn{display:inline-flex}",
    ),
    (
        "body.search-extras-collapsed .search-autocomplete,body.search-extras-collapsed .search-active-pills,body.search-chrome-collapsed .search-autocomplete,body.search-chrome-collapsed .search-active-pills,body.search-extras-collapsed .search-ac-shell,body.search-chrome-collapsed .search-ac-shell{display:none!important}",
        "body.search-extras-collapsed .search-autocomplete,body.search-extras-collapsed .search-active-pills,body.search-chrome-collapsed .search-autocomplete,body.search-chrome-collapsed .search-active-pills,body.search-extras-collapsed .search-ac-shell,body.search-chrome-collapsed .search-ac-shell{display:none!important}\n body.search-chrome-collapsed .search-ac-shell.ac-fs,body.search-extras-collapsed .search-ac-shell.ac-fs{display:flex!important}\n body.search-chrome-collapsed .search-ac-shell.ac-fs .search-autocomplete,body.search-extras-collapsed .search-ac-shell.ac-fs .search-autocomplete{display:block!important}",
    ),
    (
        "body.search-mode .filter-wrap:not(.open) .filter-top{justify-content:flex-end;border:none;padding:0;min-width:0;max-width:100%;overflow:hidden}",
        "body.search-mode .filter-wrap:not(.open) .filter-top{justify-content:flex-end;border:none;padding:0;min-width:0;max-width:100%;overflow:visible}",
    ),
    (
        ".search-ac-shell.open .ac-fs-bar,.search-ac-shell:has(.search-autocomplete.open) .ac-fs-bar,.search-ac-shell.ac-fs .ac-fs-bar{display:flex;align-items:center;gap:.5rem;flex-wrap:nowrap;width:100%;max-width:100%;min-width:0;box-sizing:border-box;overflow:visible}",
        ".search-ac-shell.open .ac-fs-bar,.search-ac-shell:has(.search-autocomplete.open) .ac-fs-bar,.search-ac-shell.ac-fs .ac-fs-bar{display:flex;align-items:center;gap:.5rem;flex-wrap:wrap;width:100%;max-width:100%;min-width:0;box-sizing:border-box;overflow:visible}",
    ),
    (
        "body.ac-fs-open .search-ac-shell.ac-fs>.search-strip{display:flex;flex:0 0 auto;min-width:0;width:100%;max-width:100%;margin:0;padding:.375rem max(.75rem,env(safe-area-inset-right,0px)) .375rem max(.75rem,env(safe-area-inset-left,0px));border:0;border-bottom:1px solid var(--border);background:var(--bg-surface);flex-wrap:nowrap;align-items:center;gap:.5rem;box-sizing:border-box;overflow:visible}",
        "body.ac-fs-open .search-ac-shell.ac-fs>.search-strip{display:flex;flex:0 0 auto;min-width:0;width:100%;max-width:100%;margin:0;padding:.375rem max(.75rem,env(safe-area-inset-right,0px)) .375rem max(.75rem,env(safe-area-inset-left,0px));border:0;border-bottom:1px solid var(--border);background:var(--bg-surface);flex-wrap:wrap;align-items:center;gap:.5rem;box-sizing:border-box;overflow:visible}",
    ),
    (
        "body.kw-fs-open .filter-wrap .filter-top{flex:0 0 auto!important;display:flex!important;flex-wrap:nowrap!important;align-items:center;gap:.375rem;padding:.5rem max(.625rem,env(safe-area-inset-right,0px)) .5rem max(.625rem,env(safe-area-inset-left,0px));border-bottom:1px solid var(--border);background:var(--bg-surface);overflow:visible;position:relative;z-index:2;min-height:0}",
        "body.kw-fs-open .filter-wrap .filter-top{flex:0 0 auto!important;display:flex!important;flex-wrap:wrap!important;align-items:center;gap:.375rem;padding:.5rem max(.625rem,env(safe-area-inset-right,0px)) .5rem max(.625rem,env(safe-area-inset-left,0px));border-bottom:1px solid var(--border);background:var(--bg-surface);overflow:visible;position:relative;z-index:2;min-height:0}",
    ),
    (
        ".search-ac-shell.ac-fs .search-autocomplete,.search-ac-shell.ac-fs .search-autocomplete.open{flex:1 1 0!important;min-height:0!important;max-height:none!important;height:auto!important;overflow-x:hidden!important;overflow-y:scroll!important;-webkit-overflow-scrolling:touch;touch-action:pan-y!important;overscroll-behavior-y:auto;overscroll-behavior-x:none;border:0;width:100%;font-size:1em;pointer-events:auto}",
        ".search-ac-shell.ac-fs .search-autocomplete,.search-ac-shell.ac-fs .search-autocomplete.open{position:relative!important;inset:auto!important;flex:1 1 0!important;min-height:0!important;max-height:none!important;height:auto!important;overflow-x:hidden!important;overflow-y:scroll!important;-webkit-overflow-scrolling:touch;touch-action:pan-y!important;overscroll-behavior-y:auto;overscroll-behavior-x:none;border:0;width:100%;font-size:1em;pointer-events:auto}",
    ),
]

COMPANION_NEW = """window.toggleAcFsCompanion=function(){
  var wantFs=!!(document.body.classList.contains('kw-fs-open')||kwFsWanted);
  if(wantFs&&isAcFs()){
    if(typeof window.setAcFullscreen==='function')window.setAcFullscreen(false);
    return;
  }
  if(typeof currentMode!=='undefined'&&currentMode!=='search'&&typeof window.setMode==='function'){
    window.setMode('search');
  }
  document.body.classList.remove('search-chrome-collapsed','search-extras-collapsed');
  if(typeof syncSearchHideBtn==='function')syncSearchHideBtn();
  var ac=document.getElementById('acList');
  var sh=document.getElementById('acShell');
  if(ac)ac.classList.add('open');
  if(sh)sh.classList.add('open');
  if(wantFs){
    if(typeof window.setAcFullscreen==='function')window.setAcFullscreen(true);
    var si=document.getElementById('searchInput');
    if(si)try{si.blur();}catch(err){}
  }else{
    if(typeof applySearch==='function')try{applySearch();}catch(err){}
    if(typeof applyAcHeight==='function')applyAcHeight();
    else if(typeof placeAcShell==='function')placeAcShell();
  }
};"""

COMPANION_OLDS = [
    """window.toggleAcFsCompanion=function(){
  // 🔍 button: toggle Search companion
  if(typeof setAcFullscreen==='function')setAcFullscreen(!isAcFs());
};""",
    "window.toggleAcFsCompanion=function(){if(typeof setAcFullscreen==='function')setAcFullscreen(!isAcFs());};",
]


def patch(path: Path) -> None:
    text = path.read_text()
    missing = []
    for old, new in REPLACEMENTS:
        if old not in text:
            missing.append(old[:80])
            continue
        text = text.replace(old, new, 1)
    found_companion = False
    for old in COMPANION_OLDS:
        if old in text:
            text = text.replace(old, COMPANION_NEW, 1)
            found_companion = True
            break
    if not found_companion:
        missing.append("toggleAcFsCompanion")
    if missing:
        raise SystemExit(f"{path.name}: missing snippets:\n- " + "\n- ".join(missing))
    path.write_text(text)
    print("patched", path)


def main() -> None:
    for f in FILES:
        if not f.exists():
            raise SystemExit(f"missing {f}")
        patch(f)
    print("ok")


if __name__ == "__main__":
    main()
