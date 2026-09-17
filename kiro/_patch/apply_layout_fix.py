#!/usr/bin/env python3
"""Proven layout fixes: Full exclusivity, Upper clip/header, Sides KW well, mobile leftovers."""
from pathlib import Path
import shutil

KIRO = Path("/home/phnx/KIRO/.kiro/specs/kontakt-workspace-drive-dirty-fix/artifacts")
WS = Path("/home/phnx/kiro-kontakt-patch/kiro/specs/kontakt-workspace-drive-dirty-fix/artifacts")
PUB = Path("/home/phnx/kiro-kontakt-patch/public/catalogs")
INGEST = "http://127.0.0.1:7529/ingest/1cf46354-1d61-4c80-bd72-a340f1db1b51"

REPL = []


def add(old, new, label, optional=False):
    REPL.append((old, new, label, optional))


# --- CSS: Upper sticky header + contained chrome; Sides KW chip; no catalog bleed ---
add(
    " body.display-upper .fs-stripe-wrap,body.display-upper .fs-mode-nav,body.display-fs .fs-mode-nav{display:none!important}\n",
    " body.display-upper .catalog-header{position:sticky;top:0;z-index:320;background:var(--bg-surface)}\n"
    " body.display-upper.search-mode .search-chrome{position:sticky;top:var(--cat-header-h,3.5rem);z-index:220;overflow:hidden;align-items:stretch;background:var(--bg-surface)}\n"
    " body.display-upper.search-mode .search-col,body.display-upper.search-mode #filterWrap{min-height:0;max-height:100%;overflow:hidden}\n"
    " body.display-upper.search-mode #acShell,body.display-upper.search-mode #acShell.open,body.display-upper.search-mode #acList,body.display-upper.search-mode #acList.open{position:relative!important;inset:auto!important;max-height:100%;overflow:auto}\n"
    " body.display-upper.search-mode #filterWrap.open .filter-panel,body.display-upper.search-mode #kwbar{max-height:100%;overflow:auto}\n"
    " body.display-sides:not(.kw-open){grid-template-columns:var(--sides-lw,22vw) minmax(0,1fr) max-content}\n"
    " body.display-sides.search-chrome-collapsed:not(.kw-open){grid-template-columns:max-content minmax(0,1fr) max-content}\n"
    " body.display-sides:not(.kw-open) #filterWrap{width:auto!important;min-width:0;height:auto!important;max-height:none!important;align-self:start;overflow:visible}\n"
    " body.display-fs:not(.kw-fs-open) #filterWrap{position:relative!important;inset:auto!important;height:auto!important;max-height:none!important;width:auto!important}\n"
    " body.display-upper .fs-stripe-wrap,body.display-upper .fs-mode-nav,body.display-fs .fs-mode-nav{display:none!important}\n",
    "css-upper-sides",
)

# --- setMode: do not auto-open AC Full when already in exclusive Full ---
add(
    "&&typeof window.setAcFullscreen==='function'&&!document.body.classList.contains('ac-fs-open'))window.setAcFullscreen(true);",
    "&&!document.body.classList.contains('display-fs')&&typeof window.setAcFullscreen==='function'&&!document.body.classList.contains('ac-fs-open'))window.setAcFullscreen(true);",
    "setMode-no-dual-fs",
)

# --- Do not scroll chrome (throws header away) ---
add(
    "if(chrome&&chrome.scrollIntoView)try{chrome.scrollIntoView({block:'start'});}catch(err){}",
    "try{window.scrollTo(0,0);}catch(err){}",
    "no-scrollIntoView",
)

# --- applyDualLayout: place sep at actual AC edge ---
add(
    "function applyDualLayout(){\n"
    "  var sep=document.getElementById('dualFsSep');\n"
    "  if(!isDualFs()){\n"
    "    document.documentElement.style.removeProperty('--dual-fs-lw');\n"
    "    if(sep)sep.style.left='';\n"
    "    syncNarrowPanels();\n"
    "    return;\n"
    "  }\n"
    "  var vw=window.innerWidth;\n"
    "  var lw=Math.round(vw*dualRatio);\n"
    "  document.documentElement.style.setProperty('--dual-fs-lw',lw+'px');\n"
    "  if(sep)sep.style.left=lw+'px';\n"
    "  syncNarrowPanels();\n"
    "}\n",
    "function applyDualLayout(){\n"
    "  var sep=document.getElementById('dualFsSep');\n"
    "  if(!isDualFs()||document.body.classList.contains('display-sides')){\n"
    "    document.documentElement.style.removeProperty('--dual-fs-lw');\n"
    "    if(sep&&!document.body.classList.contains('display-sides'))sep.removeAttribute('style');\n"
    "    syncNarrowPanels();\n"
    "    return;\n"
    "  }\n"
    "  var vw=window.innerWidth||1200;\n"
    "  var lw=Math.round(vw*dualRatio);\n"
    "  var sh=document.getElementById('acShell');\n"
    "  if(sh){var r=sh.getBoundingClientRect();if(r.width>40)lw=Math.round(r.right);}\n"
    "  document.documentElement.style.setProperty('--dual-fs-lw',lw+'px');\n"
    "  if(sep){\n"
    "    var hdr=document.querySelector('.catalog-header');\n"
    "    var top=hdr?Math.round(hdr.getBoundingClientRect().bottom):0;\n"
    "    sep.style.cssText='position:fixed;top:'+top+'px;bottom:0;left:'+lw+'px;width:10px;height:auto;z-index:290;margin:0;transform:translateX(-50%);';\n"
    "  }\n"
    "  syncNarrowPanels();\n"
    "}\n",
    "applyDualLayout",
    True,
)

add(
    "function applyDualLayout(){\n"
    "  var sep=document.getElementById('dualFsSep');\n"
    "  if(!isDualFs()){document.documentElement.style.removeProperty('--dual-fs-lw');if(sep)sep.style.left='';syncNarrowPanels();return;}\n"
    "  var vw=window.innerWidth;\n"
    "  var lw=Math.round(vw*dualRatio);\n"
    "  document.documentElement.style.setProperty('--dual-fs-lw',lw+'px');\n"
    "  if(sep)sep.style.left=lw+'px';\n"
    "  syncNarrowPanels();\n"
    "}\n",
    "function applyDualLayout(){\n"
    "  var sep=document.getElementById('dualFsSep');\n"
    "  if(!isDualFs()||document.body.classList.contains('display-sides')){\n"
    "    document.documentElement.style.removeProperty('--dual-fs-lw');\n"
    "    if(sep&&!document.body.classList.contains('display-sides'))sep.removeAttribute('style');\n"
    "    syncNarrowPanels();\n"
    "    return;\n"
    "  }\n"
    "  var vw=window.innerWidth||1200;\n"
    "  var lw=Math.round(vw*dualRatio);\n"
    "  var sh=document.getElementById('acShell');\n"
    "  if(sh){var r=sh.getBoundingClientRect();if(r.width>40)lw=Math.round(r.right);}\n"
    "  document.documentElement.style.setProperty('--dual-fs-lw',lw+'px');\n"
    "  if(sep){\n"
    "    var hdr=document.querySelector('.catalog-header');\n"
    "    var top=hdr?Math.round(hdr.getBoundingClientRect().bottom):0;\n"
    "    sep.style.cssText='position:fixed;top:'+top+'px;bottom:0;left:'+lw+'px;width:10px;height:auto;z-index:290;margin:0;transform:translateX(-50%);';\n"
    "  }\n"
    "  syncNarrowPanels();\n"
    "}\n",
    "applyDualLayout-compact",
    True,
)

# --- applySidesCols: clear chrome leftovers + collapse KW well ---
add(
    "    document.body.style.removeProperty('--sides-lw');\n"
    "    document.body.style.removeProperty('--sides-rw');\n"
    "    ['searchSplit','dualFsSep'].forEach(function(id){var el=document.getElementById(id);if(el)el.removeAttribute('style');});\n",
    "    document.body.style.removeProperty('--sides-lw');\n"
    "    document.body.style.removeProperty('--sides-rw');\n"
    "    ['searchSplit','dualFsSep'].forEach(function(id){var el=document.getElementById(id);if(el)el.removeAttribute('style');});\n"
    "    if(typeof clearChromeInlineLeftovers==='function')clearChromeInlineLeftovers();\n",
    "leave-sides-clear",
)

add(
    "  if(document.body.classList.contains('search-chrome-collapsed')){\n"
    "    document.body.style.removeProperty('--sides-lw');\n"
    "  }else{\n"
    "    lw=Math.max(minL,Math.min(lw,vw-minR-minC));\n"
    "    document.body.style.setProperty('--sides-lw',lw+'px');\n"
    "  }\n"
    "  rw=Math.max(minR,Math.min(rw,vw-minL-minC));\n"
    "  document.body.style.setProperty('--sides-rw',rw+'px');\n",
    "  if(document.body.classList.contains('search-chrome-collapsed')){\n"
    "    document.body.style.removeProperty('--sides-lw');\n"
    "  }else{\n"
    "    lw=Math.max(minL,Math.min(lw,vw-minR-minC));\n"
    "    document.body.style.setProperty('--sides-lw',lw+'px');\n"
    "  }\n"
    "  if(!document.body.classList.contains('kw-open')){\n"
    "    document.body.style.removeProperty('--sides-rw');\n"
    "  }else{\n"
    "    rw=Math.max(minR,Math.min(rw,vw-minL-minC));\n"
    "    document.body.style.setProperty('--sides-rw',rw+'px');\n"
    "  }\n",
    "sides-kw-well",
)

# --- Full exclusivity ---
add(
    "  }else if(mode==='fs'){\n"
    "    var menu=opts.menu||(document.body.classList.contains('search-mode')?'search':'keywords');\n"
    "    if(menu==='both'&&displayIsDesktop()){setDisplayMode('sides');return;}\n"
    "    if(menu==='search'){\n"
    "      if(typeof window.setAcFullscreen==='function')window.setAcFullscreen(true);\n"
    "    }else{\n"
    "      if(typeof window.setKwFullscreen==='function')window.setKwFullscreen(true);\n"
    "    }\n"
    "  }else{\n",
    "  }else if(mode==='fs'){\n"
    "    var menu=opts.menu||'search';\n"
    "    if(menu==='both'&&displayIsDesktop()){setDisplayMode('sides');return;}\n"
    "    document.body.classList.remove('dual-fs-open');\n"
    "    if(menu==='search'){\n"
    "      if(typeof kwFsWanted!=='undefined')kwFsWanted=false;\n"
    "      if(typeof window.setKwFullscreen==='function')window.setKwFullscreen(false);\n"
    "      document.body.classList.remove('kw-fs-open');\n"
    "      var fwEx=document.getElementById('filterWrap');\n"
    "      if(fwEx){fwEx.classList.remove('open');document.body.classList.remove('kw-open');}\n"
    "      if(typeof window.setAcFullscreen==='function')window.setAcFullscreen(true);\n"
    "    }else{\n"
    "      if(typeof acFsWanted!=='undefined')acFsWanted=false;\n"
    "      if(typeof window.setAcFullscreen==='function')window.setAcFullscreen(false);\n"
    "      document.body.classList.remove('ac-fs-open');\n"
    "      var shEx=document.getElementById('acShell');\n"
    "      if(shEx)shEx.classList.remove('ac-fs','ac-fixed');\n"
    "      if(typeof window.setKwFullscreen==='function')window.setKwFullscreen(true);\n"
    "    }\n"
    "    if(typeof placeMenusForDisplay==='function')placeMenusForDisplay('fs');\n"
    "  }else{\n",
    "fs-exclusive",
)

# --- clearChromeInline + logs + resize + toggleFilter wrap ---
add(
    "function placeMenusForDisplay(mode){\n",
    "function clearChromeInlineLeftovers(){\n"
    "  var ch=document.getElementById('searchChrome');\n"
    "  if(ch){ch.style.removeProperty('grid-template-columns');ch.style.removeProperty('height');ch.style.removeProperty('max-height');}\n"
    "  var fw=document.getElementById('filterWrap');\n"
    "  if(fw&&!document.body.classList.contains('display-fs')){fw.style.removeProperty('height');fw.style.removeProperty('max-height');}\n"
    "}\n"
    "function placeMenusForDisplay(mode){\n",
    "clearChromeFn",
)

add(
    "  if(typeof applySidesCols==='function')applySidesCols();\n"
    "  if(typeof applyAll==='function')applyAll();\n"
    "  if(typeof applyFsChromeSize==='function')applyFsChromeSize();\n"
    "  syncDisplayBtns();\n"
    "  if(typeof logLayoutModes==='function')logLayoutModes('setDisplayMode');\n",
    "  if(mode!=='sides'&&typeof clearChromeInlineLeftovers==='function')clearChromeInlineLeftovers();\n"
    "  var hdrFix=document.querySelector('.catalog-header');\n"
    "  if(hdrFix)document.documentElement.style.setProperty('--cat-header-h',Math.round(hdrFix.getBoundingClientRect().bottom)+'px');\n"
    "  if(typeof applySidesCols==='function')applySidesCols();\n"
    "  if(typeof applyAll==='function')applyAll();\n"
    "  if(typeof applyFsChromeSize==='function')applyFsChromeSize();\n"
    "  if(typeof placeMenusForDisplay==='function')placeMenusForDisplay(mode);\n"
    "  try{window.scrollTo(0,0);}catch(err){}\n"
    "  syncDisplayBtns();\n"
    "  if(typeof logLayoutModes==='function')logLayoutModes('setDisplayMode');\n"
    "// #region agent log\n"
    "fetch('" + INGEST + "',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'f491c2'},body:JSON.stringify({sessionId:'f491c2',runId:'layout-fix',hypothesisId:mode==='fs'?'H4':(mode==='upper'?'H2':'H8'),location:'setDisplayMode',message:'layout-fix',data:{mode:currentDisplay,acFs:document.body.classList.contains('ac-fs-open'),kwFs:document.body.classList.contains('kw-fs-open'),dual:document.body.classList.contains('dual-fs-open'),kwOpen:document.body.classList.contains('kw-open'),hdrY:function(){var el=document.querySelector('.catalog-header');return el?Math.round(el.getBoundingClientRect().y):null;}(),chStyle:function(){var el=document.getElementById('searchChrome');return el?(el.getAttribute('style')||''):'';}(),fwParent:function(){var el=document.getElementById('filterWrap');return el&&el.parentElement?(el.parentElement.id||el.parentElement.tagName):'';}(),sepL:function(){var el=document.getElementById('dualFsSep');if(!el)return null;return Math.round(el.getBoundingClientRect().x);}()},timestamp:Date.now()})}).catch(function(){});\n"
    "// #endregion\n",
    "setDisplay-tail",
)

add(
    "  window.addEventListener('resize',function(){\n"
    "    if(currentDisplay==='sides'&&!displayIsDesktop())setDisplayMode('fs');\n"
    "    else if(typeof applySidesCols==='function')applySidesCols();\n"
    "  },{passive:true});\n",
    "  window.addEventListener('resize',function(){\n"
    "    if(!displayIsDesktop()){\n"
    "      document.body.classList.remove('dual-fs-open');\n"
    "      if(typeof kwFsWanted!=='undefined'&&currentDisplay!=='fs')kwFsWanted=false;\n"
    "      if(typeof clearChromeInlineLeftovers==='function')clearChromeInlineLeftovers();\n"
    "      if(currentDisplay==='sides'){setDisplayMode('fs',{menu:'search'});return;}\n"
    "    }\n"
    "    if(typeof applySidesCols==='function')applySidesCols();\n"
    "    if(currentDisplay==='fs'&&typeof applyDualLayout==='function')applyDualLayout();\n"
    "  },{passive:true});\n",
    "resize-mobile",
)

add(
    "  var _tsc=window.toggleSearchChrome;\n"
    "  if(typeof _tsc==='function'){\n"
    "    window.toggleSearchChrome=function(){ _tsc(); if(typeof applySidesCols==='function')applySidesCols(); };\n"
    "  }\n",
    "  var _tsc=window.toggleSearchChrome;\n"
    "  if(typeof _tsc==='function'){\n"
    "    window.toggleSearchChrome=function(){ _tsc(); if(typeof applySidesCols==='function')applySidesCols(); };\n"
    "  }\n"
    "  var _tf=window.toggleFilter;\n"
    "  if(typeof _tf==='function'){\n"
    "    window.toggleFilter=function(){ _tf.apply(this,arguments); if(typeof applySidesCols==='function')applySidesCols(); };\n"
    "  }\n",
    "wrap-toggleFilter",
)


def must_replace(text, old, new, label, optional=False):
    n = text.count(old)
    if n == 0:
        if new in text or optional or (label.endswith(":css-upper-sides") and "body.display-upper .catalog-header{position:sticky" in text):
            print(f"  skip {label}")
            return text
        raise SystemExit(f"MISSING [{label}]")
    print(f"  {label} x{n}")
    return text.replace(old, new)


def patch_text(text, name):
    for old, new, label, optional in REPL:
        text = must_replace(text, old, new, f"{name}:{label}", optional)
    if "function hideSearchAc" not in text:
        raise SystemExit(f"TRUNCATED {name}: hideSearchAc")
    if name.endswith(".html") and "</html>" not in text:
        raise SystemExit(f"TRUNCATED {name}: </html>")
    if "clearChromeInlineLeftovers" not in text:
        raise SystemExit(f"MISSING clearChrome in {name}")
    if "kwFsWanted=false" not in text:
        raise SystemExit(f"MISSING fs exclusivity in {name}")
    return text


def main():
    for name in ("build-ds-catalog-html.sh", "build-kontakt-catalog-html.sh"):
        src = KIRO / name
        out = patch_text(src.read_text(encoding="utf-8"), name)
        src.write_text(out, encoding="utf-8")
        shutil.copy2(src, WS / name)
        print("patched KIRO", name, len(out))

    for path in [
        PUB / "DS-CATALOG.html",
        PUB / "DS-CATALOG-portable.html",
        PUB / "KONTAKT-CATALOG.html",
        PUB / "KONTAKT-CATALOG-portable.html",
        WS / "DS-CATALOG.html",
        WS / "DS-CATALOG-portable.html",
        WS / "KONTAKT-CATALOG.html",
        WS / "KONTAKT-CATALOG-portable.html",
    ]:
        if not path.exists():
            continue
        path.write_text(patch_text(path.read_text(encoding="utf-8"), path.name), encoding="utf-8")
        print("patched", path.name)


if __name__ == "__main__":
    main()
