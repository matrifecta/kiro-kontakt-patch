#!/usr/bin/env python3
from pathlib import Path
import shutil

KIRO = Path("/home/phnx/KIRO/.kiro/specs/kontakt-workspace-drive-dirty-fix/artifacts")
WS = Path("/home/phnx/kiro-kontakt-patch/kiro/specs/kontakt-workspace-drive-dirty-fix/artifacts")
PUB = Path("/home/phnx/kiro-kontakt-patch/public/catalogs")

REPLACES = [
    (
        " body.kw-fs-open .kw-fs-back{display:inline-flex}",
        " body.kw-fs-open .kw-fs-back{display:inline-flex}\n"
        " .fs-mode-nav{display:none;align-items:center;gap:4px;flex:0 1 auto;min-width:0}\n"
        " body.ac-fs-open .ac-fs-bar .fs-mode-nav,body.kw-fs-open .filter-top .fs-mode-nav{display:inline-flex}\n"
        " .fs-mode-nav .mode-btn{min-height:2.25rem;padding:0 .7rem}\n"
        " body.kw-fs-open .filter-kw-tools{display:none!important}\n"
        " body.kw-fs-open .kw-fs-btn{display:none!important}\n"
        " body.kw-fs-open .filter-panel>.mode-switch{display:none!important}\n"
        " body.kw-fs-open .filter-top{flex-wrap:nowrap}\n"
        " body.ac-fs-open .search-ac-shell.ac-fs{display:grid!important;grid-template-columns:auto minmax(0,1fr);grid-template-rows:auto minmax(0,1fr);align-items:stretch}\n"
        " body.ac-fs-open .search-ac-shell.ac-fs .ac-fs-bar{grid-column:1;grid-row:1;width:auto;max-width:100%;padding:.35rem .4rem}\n"
        " body.ac-fs-open .search-ac-shell.ac-fs>.search-strip{grid-column:2;grid-row:1;min-width:0}\n"
        " body.ac-fs-open .search-ac-shell.ac-fs>.search-strip .search-strip-fs{display:none!important}\n"
        " body.ac-fs-open .search-ac-shell.ac-fs>.search-autocomplete,body.ac-fs-open .search-ac-shell.ac-fs>#acList{grid-column:1/-1;grid-row:2;min-height:0}",
        "css-fs-nav",
    ),
    (
        '<div class="ac-fs-bar" id="acFsBar"><button type="button" class="ac-fs-back" id="acFsBack" aria-label="Exit fullscreen" title="Exit fullscreen" onclick="event.preventDefault();event.stopPropagation();setAcFullscreen(false)">&#x2190;</button><button type="button" class="kw-companion-btn"',
        '<div class="ac-fs-bar" id="acFsBar"><button type="button" class="ac-fs-back" id="acFsBack" aria-label="Exit fullscreen" title="Exit fullscreen" onclick="event.preventDefault();event.stopPropagation();setAcFullscreen(false)">&#x2190;</button><div class="fs-mode-nav" id="acFsModeNav" role="navigation" aria-label="Mode"><button type="button" class="mode-btn" data-mode="shade" onclick="event.preventDefault();event.stopPropagation();setMode(&#x27;shade&#x27;)">Shade</button><button type="button" class="mode-btn" data-mode="search" onclick="event.preventDefault();event.stopPropagation();setMode(&#x27;search&#x27;)">Search</button></div><button type="button" class="kw-companion-btn"',
        "html-ac-nav",
    ),
    (
        '<span class="toggle-arrow">&#9660;</span> Keywords</button><button type="button" class="ac-companion-btn"',
        '<span class="toggle-arrow">&#9660;</span> Keywords</button><div class="fs-mode-nav" id="kwFsModeNav" role="navigation" aria-label="Mode"><button type="button" class="mode-btn" data-mode="shade" onclick="event.preventDefault();event.stopPropagation();setMode(&#x27;shade&#x27;)">Shade</button><button type="button" class="mode-btn" data-mode="search" onclick="event.preventDefault();event.stopPropagation();setMode(&#x27;search&#x27;)">Search</button></div><button type="button" class="ac-companion-btn"',
        "html-kw-nav",
    ),
    (
        """    if(keepKw){
      if(typeof window.hideSearchAc==='function')try{window.hideSearchAc();}catch(err){}
      if(typeof window.setMode==='function'&&typeof currentMode!=='undefined'&&currentMode==='search')window.setMode('shade');
      setKwFullscreen(true);
    }""",
        """    if(keepKw){
      setKwFullscreen(true);
    }""",
        "keepKw",
    ),
    (
        """      var bar=document.getElementById('acFsBar');
      var strip2=document.getElementById('searchStrip');
      var shEl=sh||acShell();
      var shH=(shEl&&shEl.getBoundingClientRect().height)||viewBox().height||0;
      var barH=(bar&&bar.getBoundingClientRect().height)||0;
      var stripH=(strip2&&strip2.parentNode===shEl?strip2.getBoundingClientRect().height:0);
      var h=Math.max(96,Math.floor(shH-barH-stripH));""",
        """      var bar=document.getElementById('acFsBar');
      var strip2=document.getElementById('searchStrip');
      var shEl=sh||acShell();
      var shBox=shEl&&shEl.getBoundingClientRect();
      var shH=(shBox&&shBox.height)||viewBox().height||0;
      var chromeTop=shBox?shBox.top:0,chromeBot=shBox?shBox.top:0,chromeSet=false;
      [bar,strip2&&strip2.parentNode===shEl?strip2:null].forEach(function(el){
        if(!el)return;
        var er=el.getBoundingClientRect();
        if(er.height<1)return;
        if(!chromeSet){chromeTop=er.top;chromeBot=er.bottom;chromeSet=true;}
        else{chromeTop=Math.min(chromeTop,er.top);chromeBot=Math.max(chromeBot,er.bottom);}
      });
      var chromeH=chromeSet?Math.max(0,chromeBot-chromeTop):0;
      var h=Math.max(96,Math.floor(shH-chromeH));""",
        "applyH",
    ),
]


def must_replace(text, old, new, label):
    n = text.count(old)
    if n == 0:
        if new in text or (label == "css-fs-nav" and ".fs-mode-nav{display:none" in text):
            print(f"  skip {label}")
            return text
        raise SystemExit(f"MISSING [{label}]")
    return text.replace(old, new)


def patch_setmode(text, name):
    """Insert FS nav hooks into whichever setMode shape this file uses."""
    marker = "fetch('http://127.0.0.1:7529/ingest/1cf46354-1d61-4c80-bd72-a340f1db1b51',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'f491c2'},body:JSON.stringify({sessionId:'f491c2',runId:'fs-nav',hypothesisId:'N2'"
    if marker in text:
        print(f"  skip setMode-log in {name}")
    else:
        old = "if(mode==='hide')mode='shade';\nif(currentMode==='hide')currentMode='shade';\nif(mode==='search'&&currentMode==='search'){"
        new = (
            "if(mode==='hide')mode='shade';\n"
            "if(currentMode==='hide')currentMode='shade';\n"
            "// #region agent log\n"
            "fetch('http://127.0.0.1:7529/ingest/1cf46354-1d61-4c80-bd72-a340f1db1b51',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'f491c2'},body:JSON.stringify({sessionId:'f491c2',runId:'fs-nav',hypothesisId:'N2',location:'setMode',message:'setMode-nav',data:{mode:mode,prev:currentMode,kwFs:document.body.classList.contains('kw-fs-open'),acFs:document.body.classList.contains('ac-fs-open'),dual:document.body.classList.contains('dual-fs-open')},timestamp:Date.now()})}).catch(function(){});\n"
            "// #endregion\n"
            "if(mode==='search'&&currentMode==='search'){"
        )
        old2 = "   if(mode==='hide')mode='shade';\n   if(currentMode==='hide')currentMode='shade';\n   if(mode==='search'&&currentMode==='search'){"
        new2 = (
            "   if(mode==='hide')mode='shade';\n"
            "   if(currentMode==='hide')currentMode='shade';\n"
            "   // #region agent log\n"
            "   fetch('http://127.0.0.1:7529/ingest/1cf46354-1d61-4c80-bd72-a340f1db1b51',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'f491c2'},body:JSON.stringify({sessionId:'f491c2',runId:'fs-nav',hypothesisId:'N2',location:'setMode',message:'setMode-nav',data:{mode:mode,prev:currentMode,kwFs:document.body.classList.contains('kw-fs-open'),acFs:document.body.classList.contains('ac-fs-open'),dual:document.body.classList.contains('dual-fs-open')},timestamp:Date.now()})}).catch(function(){});\n"
            "   // #endregion\n"
            "   if(mode==='search'&&currentMode==='search'){"
        )
        if text.count(old) == 1:
            text = text.replace(old, new, 1)
        elif text.count(old2) == 1:
            text = text.replace(old2, new2, 1)
        else:
            raise SystemExit(f"MISSING setMode-log in {name}")

    hook = "&&!document.body.classList.contains('ac-fs-open'))window.setAcFullscreen(true);"
    if hook in text:
        print(f"  skip setMode-hooks in {name}")
        return text

    old_ret = (
        "  if(typeof window.applyActiveLayoutStore==='function')window.applyActiveLayoutStore();\n"
        "  setTimeout(function(){var si=document.getElementById('searchInput');if(si&&!document.body.classList.contains('ac-fs-open'))si.focus();},50);\n"
        "  syncTapToAddBtns();\n"
        "  return;\n"
        "}"
    )
    new_ret = (
        "  if(typeof window.applyActiveLayoutStore==='function')window.applyActiveLayoutStore();\n"
        "  setTimeout(function(){var si=document.getElementById('searchInput');if(si&&!document.body.classList.contains('ac-fs-open'))si.focus();},50);\n"
        "  if((document.body.classList.contains('kw-fs-open')||(typeof kwFsWanted!=='undefined'&&kwFsWanted))&&typeof window.setAcFullscreen==='function'&&!document.body.classList.contains('ac-fs-open'))window.setAcFullscreen(true);\n"
        "  syncTapToAddBtns();\n"
        "  return;\n"
        "}"
    )
    old_ret2 = (
        "     if(typeof window.applyActiveLayoutStore==='function')window.applyActiveLayoutStore();\n"
        "     setTimeout(function(){var si=document.getElementById('searchInput');if(si&&!document.body.classList.contains('ac-fs-open'))si.focus();},50);\n"
        "     syncTapToAddBtns();\n"
        "     return;\n"
        "   }"
    )
    new_ret2 = (
        "     if(typeof window.applyActiveLayoutStore==='function')window.applyActiveLayoutStore();\n"
        "     setTimeout(function(){var si=document.getElementById('searchInput');if(si&&!document.body.classList.contains('ac-fs-open'))si.focus();},50);\n"
        "     if((document.body.classList.contains('kw-fs-open')||(typeof kwFsWanted!=='undefined'&&kwFsWanted))&&typeof window.setAcFullscreen==='function'&&!document.body.classList.contains('ac-fs-open'))window.setAcFullscreen(true);\n"
        "     syncTapToAddBtns();\n"
        "     return;\n"
        "   }"
    )
    if text.count(old_ret) >= 1:
        text = text.replace(old_ret, new_ret, 1)
    elif text.count(old_ret2) >= 1:
        text = text.replace(old_ret2, new_ret2, 1)
    else:
        raise SystemExit(f"MISSING setMode-early in {name}")

    old_end = (
        "else{entries.forEach(function(el){el.style.display='';el.classList.remove('dim','is-hidden','fav-rec');});document.body.classList.remove('search-empty-recs');render();}\n"
        "syncTapToAddBtns();};"
    )
    new_end = (
        "else{entries.forEach(function(el){el.style.display='';el.classList.remove('dim','is-hidden','fav-rec');});document.body.classList.remove('search-empty-recs');render();\n"
        "  if(typeof acFsWanted!=='undefined')acFsWanted=false;\n"
        "  document.body.classList.remove('ac-fs-open','dual-fs-open');\n"
        "  if(typeof parkSearchStrip==='function')parkSearchStrip();\n"
        "  if(typeof placeAcShell==='function')placeAcShell();\n"
        "}\n"
        "if(mode==='search'&&(document.body.classList.contains('kw-fs-open')||(typeof kwFsWanted!=='undefined'&&kwFsWanted))&&typeof window.setAcFullscreen==='function'&&!document.body.classList.contains('ac-fs-open'))window.setAcFullscreen(true);\n"
        "syncTapToAddBtns();};"
    )
    old_end2 = (
        "   else{entries.forEach(function(el){el.style.display='';el.classList.remove('dim','is-hidden','fav-rec');});document.body.classList.remove('search-empty-recs');render();}\n"
        "   syncTapToAddBtns();};"
    )
    new_end2 = (
        "   else{entries.forEach(function(el){el.style.display='';el.classList.remove('dim','is-hidden','fav-rec');});document.body.classList.remove('search-empty-recs');render();\n"
        "     if(typeof acFsWanted!=='undefined')acFsWanted=false;\n"
        "     document.body.classList.remove('ac-fs-open','dual-fs-open');\n"
        "     if(typeof parkSearchStrip==='function')parkSearchStrip();\n"
        "     if(typeof placeAcShell==='function')placeAcShell();\n"
        "   }\n"
        "   if(mode==='search'&&(document.body.classList.contains('kw-fs-open')||(typeof kwFsWanted!=='undefined'&&kwFsWanted))&&typeof window.setAcFullscreen==='function'&&!document.body.classList.contains('ac-fs-open'))window.setAcFullscreen(true);\n"
        "   syncTapToAddBtns();};"
    )
    if text.count(old_end) == 1:
        text = text.replace(old_end, new_end, 1)
    elif text.count(old_end2) == 1:
        text = text.replace(old_end2, new_end2, 1)
    else:
        raise SystemExit(f"MISSING setMode-end in {name}")
    return text


def main():
    for name in ("build-ds-catalog-html.sh", "build-kontakt-catalog-html.sh"):
        shutil.copy2(KIRO / name, WS / name)
        print(f"copied {name}")

    htmls = [
        PUB / "DS-CATALOG.html",
        PUB / "DS-CATALOG-portable.html",
        PUB / "KONTAKT-CATALOG.html",
        PUB / "KONTAKT-CATALOG-portable.html",
        WS / "DS-CATALOG.html",
        WS / "DS-CATALOG-portable.html",
        WS / "KONTAKT-CATALOG.html",
        WS / "KONTAKT-CATALOG-portable.html",
    ]
    for path in htmls:
        text = path.read_text(encoding="utf-8")
        for old, new, label in REPLACES:
            text = must_replace(text, old, new, f"{path.name}:{label}")
        text = patch_setmode(text, path.name)
        if "</html>" not in text or "function hideSearchAc" not in text:
            raise SystemExit(f"TRUNCATED {path}")
        if "fs-mode-nav" not in text:
            raise SystemExit(f"MISSING fs-mode-nav in {path}")
        path.write_text(text, encoding="utf-8")
        print(f"patched {path.name} {len(text)}")


if __name__ == "__main__":
    main()
