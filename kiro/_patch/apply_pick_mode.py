#!/usr/bin/env python3
"""Restore Pick (old Shade data-mode) without the 40vh dropdown. Fix Edit/Pin persist."""
from pathlib import Path
import shutil

KIRO = Path("/home/phnx/KIRO/.kiro/specs/kontakt-workspace-drive-dirty-fix/artifacts")
WS = Path("/home/phnx/kiro-kontakt-patch/kiro/specs/kontakt-workspace-drive-dirty-fix/artifacts")
PUB = Path("/home/phnx/kiro-kontakt-patch/public/catalogs")

INGEST = (
    "http://127.0.0.1:7529/ingest/1cf46354-1d61-4c80-bd72-a340f1db1b51"
)

HELPERS = (
    "var DATA_MODE_KEY='catalog-data-mode-'+(window.CATALOG_NS||'catalog');\n"
    "window.DATA_MODE_KEY=DATA_MODE_KEY;\n"
    "function isPickMode(m){m=m==null?currentMode:m;return m==='pick'||m==='shade';}\n"
    "function normalizeDataMode(m){if(m==='shade'||m==='pick')return'pick';if(m==='hide')return'search';return'search';}\n"
    "function logPickLock(loc,msg,hid,extra){\n"
    "// #region agent log\n"
    "try{\n"
    "extra=extra||{};\n"
    "extra.mode=typeof currentMode!=='undefined'?currentMode:'';\n"
    "extra.tapToAdd=typeof tapToAdd!=='undefined'?!!tapToAdd:null;\n"
    "extra.selN=typeof sel!=='undefined'?sel.length:null;\n"
    "extra.searchMode=document.body.classList.contains('search-mode');\n"
    "extra.pickMode=document.body.classList.contains('pick-mode');\n"
    "extra.display=typeof currentDisplay!=='undefined'?currentDisplay:'';\n"
    "extra.edit=document.body.classList.contains('layout-edit');\n"
    "extra.pinned=typeof modeLayoutPinned==='function'?!!modeLayoutPinned():null;\n"
    "fetch('" + INGEST + "',{method:'POST',headers:{'Content-Type':'application/json',"
    "'X-Debug-Session-Id':'f491c2'},body:JSON.stringify({sessionId:'f491c2',runId:'pick-lock',"
    "hypothesisId:hid,location:loc,message:msg,data:extra,timestamp:Date.now()})}).catch(function(){});\n"
    "}catch(err){}\n"
    "// #endregion\n"
    "}\n"
    "window.isPickMode=isPickMode;\n"
    "window.normalizeDataMode=normalizeDataMode;\n"
    "window.logPickLock=logPickLock;\n"
    "window.getCurrentMode=function(){return currentMode;};\n"
    "window.getSel=function(){return (sel||[]).slice();};\n"
    "window.handleSnap=handleSnap;\n"
)

HANDLE_SNAP = (
    "function handleSnap(){"
    "function one(id){var el=document.getElementById(id);if(!el)return{id:id,missing:true};"
    "var s=getComputedStyle(el),b=el.getBoundingClientRect();"
    "return{id:id,disp:s.display,pe:s.pointerEvents,z:s.zIndex,"
    "w:Math.round(b.width),h:Math.round(b.height),y:Math.round(b.y)};}"
    "return{ac:one('acHeight'),kw:one('kwShadeHeight'),sh:one('searchHeight'),"
    "split:one('searchSplit'),sep:one('dualFsSep')};}\n"
)


def apply_any(text, olds, new):
    for old in olds:
        if old in text:
            return text.replace(old, new, 1), True
    return text, False


def apply_all_any(text, olds, new):
    hit = False
    for old in olds:
        if old in text:
            text = text.replace(old, new)
            hit = True
    return text, hit


def patch(text, name):
    n = 0

    # --- UI: Shade → Pick (visible labels + data-mode). Keep setMode('shade') alias. ---
    text, hit = apply_all_any(
        text,
        (">Shade</button>",),
        ">Pick</button>",
    )
    n += int(hit)

    # Remove hide CSS before renaming data-mode, so the selector still matches.
    hide = ' .mode-btn[data-mode="shade"]{display:none!important}\n'
    hide2 = ' .mode-btn[data-mode="pick"]{display:none!important}\n'
    if hide in text:
        text = text.replace(hide, "")
        n += 1
    if hide2 in text:
        text = text.replace(hide2, "")
        n += 1

    text, hit = apply_all_any(
        text,
        ('data-mode="shade"',),
        'data-mode="pick"',
    )
    n += int(hit)

    if "setMode(&#x27;shade&#x27;)" in text:
        text = text.replace("setMode(&#x27;shade&#x27;)", "setMode(&#x27;pick&#x27;)")
        n += 1
    # onclick leftovers only — do not rewrite comments / alias helpers
    if 'onclick="setMode(\'shade\')"' in text:
        text = text.replace('onclick="setMode(\'shade\')"', 'onclick="setMode(\'pick\')"')
        n += 1

    # --- Neutralize Shade dropdown (keep in-flow Keywords) ---
    drop_old = (
        "  /* Shade: Keywords-only dropdown on the right; catalog stays full-width behind. */\n"
        "  body:not(.search-mode):not(.kw-fs-open) .filter-wrap{overflow:visible}\n"
        "  body:not(.search-mode):not(.kw-fs-open) .filter-wrap.open .filter-panel{position:absolute;top:calc(100% + 4px);right:0;left:auto;width:min(28vw,24rem);max-width:calc(100vw - 1.25rem);max-height:min(40vh,22rem);z-index:230;background:var(--bg-surface);border:1px solid var(--border);border-radius:8px;box-shadow:0 16px 40px rgba(0,0,0,.38)}\n"
    )
    drop_new = (
        "  /* Pick: Keywords stay in-flow. Do not restore the 40vh Shade dropdown. */\n"
        "  body:not(.search-mode):not(.kw-fs-open):not(.display-sides):not(.display-fs) .filter-wrap{overflow:hidden}\n"
        "  body:not(.search-mode):not(.kw-fs-open):not(.display-sides):not(.display-fs) .filter-wrap.open .filter-panel{position:static!important;width:auto!important;max-width:100%;max-height:var(--upper-kw-h,min(48vh,32rem))!important;box-shadow:none;border:0;border-radius:0}\n"
    )
    if drop_old in text:
        text = text.replace(drop_old, drop_new, 1)
        n += 1

    pick_css = (
        " body.display-upper.pick-mode .search-chrome{position:sticky;top:var(--cat-header-h,3.5rem);z-index:220;overflow:hidden!important;background:var(--bg-surface)}\n"
        " body.display-upper.pick-mode #filterWrap,body.display-upper.pick-mode #filterWrap.open{min-height:0;max-height:100%;overflow:hidden}\n"
        " body.display-upper.pick-mode #filterWrap.open .filter-panel,body.display-upper.pick-mode #kwbar{overflow:auto!important}\n"
        " body.pick-mode:not(.display-sides) .filter-wrap{position:relative;top:auto;z-index:auto;width:100%;max-width:100%;min-width:0}\n"
        " body.layout-edit:not(.mode-layout-pinned) .ac-height,body.layout-edit:not(.mode-layout-pinned) .ac-width,body.layout-edit:not(.mode-layout-pinned) .kw-shade-height,body.layout-edit:not(.mode-layout-pinned) .search-height,body.layout-edit:not(.mode-layout-pinned) .search-split{pointer-events:auto!important;z-index:46}\n"
        " body.layout-edit:not(.mode-layout-pinned) .ac-height::before,body.layout-edit:not(.mode-layout-pinned) .ac-width::before,body.layout-edit:not(.mode-layout-pinned) .kw-shade-height::before,body.layout-edit:not(.mode-layout-pinned) .search-height::before{opacity:1}\n"
    )
    if "body.display-upper.pick-mode .search-chrome" not in text:
        marker = " body.display-upper.search-mode #filterWrap.open .filter-panel,body.display-upper.search-mode #kwbar{overflow:auto!important}\n"
        if marker in text:
            text = text.replace(marker, marker + pick_css, 1)
            n += 1
        else:
            marker2 = " body.display-upper .catalog-header{position:sticky;top:0;z-index:320;background:var(--bg-surface)}\n"
            if marker2 in text:
                text = text.replace(marker2, marker2 + pick_css, 1)
                n += 1

    if "window.DATA_MODE_KEY=DATA_MODE_KEY" not in text and "var DATA_MODE_KEY='catalog-data-mode-'" in text:
        text = text.replace(
            "var DATA_MODE_KEY='catalog-data-mode-'+(window.CATALOG_NS||'catalog');\n",
            "var DATA_MODE_KEY='catalog-data-mode-'+(window.CATALOG_NS||'catalog');\n"
            "window.DATA_MODE_KEY=DATA_MODE_KEY;\n",
            1,
        )
        n += 1
    if "window.getCurrentMode=function" not in text and "window.logPickLock=logPickLock;" in text:
        text = text.replace(
            "window.logPickLock=logPickLock;\n",
            "window.logPickLock=logPickLock;\n"
            "window.getCurrentMode=function(){return currentMode;};\n"
            "window.getSel=function(){return (sel||[]).slice();};\n"
            "window.handleSnap=handleSnap;\n",
            1,
        )
        n += 1

    # --- Helpers after currentMode ---
    if "function normalizeDataMode" not in text:
        text, hit = apply_any(
            text,
            (
                "var currentMode='search';\n",
                " var currentMode='search';\n",
                "   var currentMode='search';\n",
            ),
            "var currentMode='search';\n" + HELPERS + HANDLE_SNAP,
        )
        n += int(hit)

    # --- Undo shade→search coerce ---
    text, hit = apply_all_any(
        text,
        (
            "if(mode==='hide'||mode==='shade')mode='search';\n"
            "if(currentMode==='hide'||currentMode==='shade')currentMode='search';\n",
            "   if(mode==='hide'||mode==='shade')mode='search';\n"
            "   if(currentMode==='hide'||currentMode==='shade')currentMode='search';\n",
            " if(mode==='hide'||mode==='shade')mode='search';\n"
            " if(currentMode==='hide'||currentMode==='shade')currentMode='search';\n",
        ),
        "if(mode==='hide')mode='search';\n"
        "if(typeof normalizeDataMode==='function')mode=normalizeDataMode(mode);\n"
        "else if(mode==='shade'||mode==='pick')mode='pick';\n"
        "if(currentMode==='hide')currentMode='search';\n"
        "if(currentMode==='shade')currentMode='pick';\n"
        "if(typeof logPickLock==='function')logPickLock('setMode','setMode-in','H2',{asked:mode,prev:currentMode});\n",
    )
    n += int(hit)

    # --- setMode class + persist ---
    text, hit = apply_any(
        text,
        (
            "currentMode=mode;\n"
            "document.querySelectorAll('.mode-btn').forEach(function(b){b.classList.toggle('active',b.dataset.mode===mode);});\n"
            "document.body.classList.toggle('search-mode',mode==='search');\n",
            "currentMode=mode;\n"
            "   document.querySelectorAll('.mode-btn').forEach(function(b){b.classList.toggle('active',b.dataset.mode===mode);});\n"
            "   document.body.classList.toggle('search-mode',mode==='search');\n",
            "   currentMode=mode;\n"
            "   document.querySelectorAll('.mode-btn').forEach(function(b){b.classList.toggle('active',b.dataset.mode===mode);});\n"
            "   document.body.classList.toggle('search-mode',mode==='search');\n",
        ),
        "currentMode=mode;\n"
        "document.querySelectorAll('.mode-btn').forEach(function(b){var bm=b.dataset.mode;b.classList.toggle('active',bm===mode||((mode==='pick'||mode==='shade')&&(bm==='pick'||bm==='shade')));});\n"
        "document.body.classList.toggle('search-mode',mode==='search');\n"
        "document.body.classList.toggle('pick-mode',mode==='pick');\n"
        "try{localStorage.setItem(DATA_MODE_KEY,mode==='pick'?'pick':'search');}catch(err){}\n"
        "if(typeof logPickLock==='function')logPickLock('setMode','setMode-out','H5',{out:mode,fwH:function(){var el=document.getElementById('filterWrap');if(!el)return null;var b=el.getBoundingClientRect();var fp=el.querySelector('.filter-panel');var fpr=fp&&fp.getBoundingClientRect();var fps=fp&&getComputedStyle(fp);var kw=document.getElementById('kwbar');var kr=kw&&kw.getBoundingClientRect();return{h:Math.round(b.height),fpH:fpr?Math.round(fpr.height):null,fpPos:fps&&fps.position,fpMax:fps&&fps.maxHeight,kwH:kr?Math.round(kr.height):null};}()});\n",
    )
    n += int(hit)

    # --- Restore last data mode on init (default Search) ---
    init_old = "  if(typeof window.setMode==='function')window.setMode('search');\n"
    init_new = (
        "  var _dm='search';\n"
        "  try{_dm=typeof normalizeDataMode==='function'?normalizeDataMode(localStorage.getItem(window.DATA_MODE_KEY||('catalog-data-mode-'+(window.CATALOG_NS||'catalog')))||'search'):'search';}catch(err){_dm='search';}\n"
        "  if(_dm!=='pick')_dm='search';\n"
        "  if(typeof window.setMode==='function')window.setMode(_dm);\n"
        "  if(typeof logPickLock==='function')logPickLock('display-init','data-mode-init','H2',{dm:_dm});\n"
    )
    if init_old in text and "data-mode-init" not in text:
        text = text.replace(init_old, init_new, 1)
        n += 1
    old_init_key = "normalizeDataMode(localStorage.getItem(DATA_MODE_KEY)||'search')"
    new_init_key = "normalizeDataMode(localStorage.getItem(window.DATA_MODE_KEY||('catalog-data-mode-'+(window.CATALOG_NS||'catalog')))||'search')"
    if old_init_key in text:
        text = text.replace(old_init_key, new_init_key, 1)
        n += 1

    text, hit = apply_any(
        text,
        (
            "    var menu=opts.menu||'search';\n",
            "  var menu=opts.menu||'search';\n",
        ),
        "    var menu=opts.menu||((typeof getCurrentMode==='function'?getCurrentMode():'')==='pick'?'keywords':'search');\n",
    )
    n += int(hit)

    # --- applyModeSlot: do not wipe missing keys ---
    so_old = (
        "    function setOrClear(key,val){\n"
        "      if(val==null||val==='')localStorage.removeItem(key);\n"
        "      else localStorage.setItem(key,String(val));\n"
        "    }\n"
    )
    so_new = (
        "    function setOrClear(key,val){\n"
        "      if(val==null||val==='')return;\n"
        "      localStorage.setItem(key,String(val));\n"
        "    }\n"
    )
    if so_old in text:
        text = text.replace(so_old, so_new, 1)
        n += 1

    # --- Pin: snapshot live sizes first ---
    pin_old = (
        "      var on=!modeLayoutPinned();\n"
        "      writeModeSlot({pinned:on});\n"
    )
    pin_new = (
        "      var on=!modeLayoutPinned();\n"
        "      if(on&&typeof snapshotLiveToMode==='function')snapshotLiveToMode();\n"
        "      writeModeSlot({pinned:on});\n"
        "      if(typeof logPickLock==='function')logPickLock('modePinBtn','pin-click','H4',{on:on,slot:typeof displayModeSlot==='function'?displayModeSlot():'',store:typeof readModeSlot==='function'?readModeSlot():null});\n"
    )
    if pin_old in text and "pin-click" not in text:
        text = text.replace(pin_old, pin_new, 1)
        n += 1

    dual_old = (
        "    if(typeof writeModeSlot==='function')writeModeSlot({pinned:!!sidesPinned},'sides');\n"
    )
    dual_new = (
        "    if(sidesPinned&&typeof snapshotLiveToMode==='function')snapshotLiveToMode('sides');\n"
        "    if(typeof writeModeSlot==='function')writeModeSlot({pinned:!!sidesPinned},'sides');\n"
        "    if(typeof logPickLock==='function')logPickLock('toggleDualFsPin','sides-pin','H4',{on:!!sidesPinned,store:typeof readModeSlot==='function'?readModeSlot('sides'):null});\n"
    )
    if dual_old in text and "logPickLock('toggleDualFsPin'" not in text:
        text = text.replace(dual_old, dual_new, 1)
        n += 1

    # --- Edit layout: apply handles + log ---
    tle_old = (
        "function toggleLayoutEdit(){\n"
        "  var was=document.body.classList.contains('layout-edit');\n"
        "  document.body.classList.toggle('layout-edit');\n"
        "  if(was&&typeof persistAllLiveLayouts==='function')persistAllLiveLayouts();\n"
        "  syncLayoutEditBtn();\n"
        "  if(window.syncSearchSplit)window.syncSearchSplit();\n"
        "}\n"
    )
    tle_new = (
        "function toggleLayoutEdit(){\n"
        "  var was=document.body.classList.contains('layout-edit');\n"
        "  document.body.classList.toggle('layout-edit');\n"
        "  if(was&&typeof persistAllLiveLayouts==='function')persistAllLiveLayouts();\n"
        "  syncLayoutEditBtn();\n"
        "  if(window.syncSearchSplit)window.syncSearchSplit();\n"
        "  if(typeof applyAll==='function')applyAll();\n"
        "  if(typeof applySidesCols==='function')applySidesCols();\n"
        "  if(typeof applyFsChromeSize==='function')applyFsChromeSize();\n"
        "  if(typeof placeSidesHandles==='function')placeSidesHandles();\n"
        "  if(typeof logPickLock==='function')logPickLock('toggleLayoutEdit','edit-toggle','H3',{on:document.body.classList.contains('layout-edit'),handles:typeof handleSnap==='function'?handleSnap():null});\n"
        "}\n"
    )
    if tle_old in text:
        text = text.replace(tle_old, tle_new, 1)
        n += 1

    # --- Pill clicks: log + keep Pick sel[] / Search tap-to-add ---
    pill_on_old = (
        "b.onclick=function(){if(currentMode==='search')window.removeSearchKw(k);else{sel=sel.filter(function(x){return x!==k;});render();}};"
    )
    pill_on_new = (
        "b.onclick=function(ev){if(typeof logPickLock==='function')logPickLock('kwbar','pill-click','H1',{k:k,kind:'off',defPrev:!!(ev&&ev.defaultPrevented)});if(currentMode==='search')window.removeSearchKw(k);else{sel=sel.filter(function(x){return x!==k;});render();}};"
    )
    if pill_on_old in text:
        text = text.replace(pill_on_old, pill_on_new)
        n += 1

    pill_add_old = (
        "if(c>0)b.onclick=function(){if(currentMode==='search')return;sel.push(k);render();};"
    )
    pill_add_new = (
        "if(c>0)b.onclick=function(ev){if(typeof logPickLock==='function')logPickLock('kwbar','pill-click','H1',{k:k,kind:'on',defPrev:!!(ev&&ev.defaultPrevented)});if(currentMode==='search')return;sel.push(k);render();};"
    )
    if pill_add_old in text:
        text = text.replace(pill_add_old, pill_add_new)
        n += 1

    cap_old = (
        "if(!btn||btn.classList.contains('clear'))return;\n"
        "if(currentMode!=='search')return;\n"
        "e.preventDefault();\n"
    )
    cap_new = (
        "if(!btn||btn.classList.contains('clear'))return;\n"
        "if(typeof logPickLock==='function')logPickLock('kwbar-capture','pill-capture','H1',{defPrev:!!e.defaultPrevented,willAdd:!!(e.ctrlKey||e.metaKey||tapToAdd)});\n"
        "if(currentMode!=='search')return;\n"
        "e.preventDefault();\n"
    )
    cap_old2 = (
        "if(!btn||btn.classList.contains('clear'))return;\n"
        "   if(currentMode!=='search')return;\n"
        "   e.preventDefault();\n"
    )
    cap_old3 = (
        "     if(!btn||btn.classList.contains('clear'))return;\n"
        "     if(currentMode!=='search')return;\n"
        "     e.preventDefault();\n"
    )
    cap_new3 = (
        "     if(!btn||btn.classList.contains('clear'))return;\n"
        "     if(typeof logPickLock==='function')logPickLock('kwbar-capture','pill-capture','H1',{defPrev:!!e.defaultPrevented,willAdd:!!(e.ctrlKey||e.metaKey||tapToAdd)});\n"
        "     if(currentMode!=='search')return;\n"
        "     e.preventDefault();\n"
    )
    if cap_old in text:
        text = text.replace(cap_old, cap_new, 1)
        n += 1
    elif cap_old2 in text:
        text = text.replace(cap_old2, cap_new, 1)
        n += 1
    elif cap_old3 in text:
        text = text.replace(cap_old3, cap_new3, 1)
        n += 1

    print(f"  {name}: {n} replacements")
    return text


def assert_common(text, name):
    if "function hideSearchAc" not in text:
        raise SystemExit(f"{name} missing function hideSearchAc")
    if "bindCatalogTop" not in text:
        raise SystemExit(f"{name} lost bindCatalogTop")
    if "syncIndexDock" not in text:
        raise SystemExit(f"{name} lost syncIndexDock")
    if "height:100%!important;max-height:none!important;align-self:stretch" not in text:
        raise SystemExit(f"{name} lost Keywords fill CSS")
    if "if(mode==='hide'||mode==='shade')mode='search'" in text:
        raise SystemExit(f"{name} still coerces shade→search")
    if "normalizeDataMode" not in text:
        raise SystemExit(f"{name} missing normalizeDataMode")
    if ">Shade</button>" in text:
        raise SystemExit(f"{name} leftover Shade button label")
    if 'mode-btn[data-mode="shade"]{display:none!important}' in text:
        raise SystemExit(f"{name} still hides Shade/Pick button")
    if 'mode-btn[data-mode="pick"]{display:none!important}' in text:
        raise SystemExit(f"{name} hides Pick button")
    if "max-height:min(40vh,22rem)" in text and "body:not(.search-mode):not(.kw-fs-open) .filter-wrap.open .filter-panel{position:absolute" in text:
        raise SystemExit(f"{name} Shade dropdown CSS still active")
    if "if(val==null||val==='')localStorage.removeItem(key)" in text:
        raise SystemExit(f"{name} applyModeSlot still wipes missing keys")
    if "snapshotLiveToMode();" not in text and "snapshotLiveToMode()" not in text:
        raise SystemExit(f"{name} pin missing snapshot")
    if "runId:'pick-lock'" not in text:
        raise SystemExit(f"{name} missing pick-lock logs")
    if "if(currentMode==='search')window.setMode('shade')" in text:
        raise SystemExit(f"{name} exitSearchUi still forces shade/pick")
    if ">Pick</button>" not in text:
        raise SystemExit(f"{name} missing Pick button label")


def assert_html(text, name):
    assert_common(text, name)
    if not text.rstrip().endswith("</html>") and "</html>" not in text[-80:]:
        raise SystemExit(f"{name} missing </html>")


def main():
    builders = (
        "build-ds-catalog-html.sh",
        "build-kontakt-catalog-html.sh",
    )
    for name in builders:
        src = KIRO / name
        raw = src.read_text(encoding="utf-8")
        out = patch(raw, f"KIRO/{name}")
        assert_common(out, f"KIRO/{name}")
        src.write_text(out, encoding="utf-8")
        WS.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, WS / name)
        print("copied", name)

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
        if not path.exists():
            print("skip missing", path)
            continue
        raw = path.read_text(encoding="utf-8")
        out = patch(raw, str(path))
        assert_html(out, path.name)
        path.write_text(out, encoding="utf-8")
        tail = out.rstrip()[-20:]
        print("wrote", path.name, len(out), "tail", repr(tail))


if __name__ == "__main__":
    main()
