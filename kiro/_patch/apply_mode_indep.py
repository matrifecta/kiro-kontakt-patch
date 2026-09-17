#!/usr/bin/env python3
"""Mode independence + streamline: Full never becomes Sides; Upper index 1-3 cols;
layout slots do not clobber; companion stays in Full; one exit from Full → Upper.

Patch KIRO builders first, copy to workspace, then in-memory sync HTML.
"""
from pathlib import Path
import shutil

KIRO = Path("/home/phnx/KIRO/.kiro/specs/kontakt-workspace-drive-dirty-fix/artifacts")
WS = Path("/home/phnx/kiro-kontakt-patch/kiro/specs/kontakt-workspace-drive-dirty-fix/artifacts")
PUB = Path("/home/phnx/kiro-kontakt-patch/public/catalogs")
INGEST = "http://127.0.0.1:7529/ingest/1cf46354-1d61-4c80-bd72-a340f1db1b51"

REPLACEMENTS = []


def add(old, new, label, optional=False, replace_all=False):
    if isinstance(old, str):
        old = (old,)
    REPLACEMENTS.append((old, new, label, optional, replace_all))


LOG_HELPER = r"""
function logModeIndep(hid,loc,msg,extra){
  // #region agent log
  try{
    extra=extra||{};
    function pid(id){var el=document.getElementById(id);return el&&el.parentElement?(el.parentElement.id||el.parentElement.tagName):'';}
    function box(el){if(!el)return null;var b=el.getBoundingClientRect();return{x:Math.round(b.x),y:Math.round(b.y),w:Math.round(b.width),h:Math.round(b.height)};}
    extra.display=typeof currentDisplay!=='undefined'?currentDisplay:'';
    extra.lastNonFs=typeof lastNonFsDisplay!=='undefined'?lastNonFsDisplay:'';
    extra.cls={
      upper:document.body.classList.contains('display-upper'),
      sides:document.body.classList.contains('display-sides'),
      fs:document.body.classList.contains('display-fs'),
      dual:document.body.classList.contains('dual-fs-open'),
      acFs:document.body.classList.contains('ac-fs-open'),
      kwFs:document.body.classList.contains('kw-fs-open'),
      kwHid:document.body.classList.contains('kw-chrome-collapsed'),
      searchHid:document.body.classList.contains('search-chrome-collapsed')
    };
    extra.parents={fw:pid('filterWrap'),ch:pid('searchChrome'),ix:pid('catalogIndex'),sh:pid('acShell')};
    extra.lw=(getComputedStyle(document.body).getPropertyValue('--sides-lw')||'').trim();
    extra.rw=(getComputedStyle(document.body).getPropertyValue('--sides-rw')||'').trim();
    extra.indexH=(getComputedStyle(document.body).getPropertyValue('--sides-index-h')||'').trim();
    var il=document.getElementById('catalogIndexList');
    if(il){
      var cs=getComputedStyle(il);
      extra.il={cols:cs.columnCount+'/'+cs.columnWidth,ov:cs.overflowY,sh:il.scrollHeight,ch:il.clientHeight,inline:(il.getAttribute('style')||'').slice(0,180)};
    }
    extra.hdr=box(document.querySelector('.catalog-header'));
    extra.ch=box(document.getElementById('searchChrome'));
    extra.fw=box(document.getElementById('filterWrap'));
    extra.ix=box(document.getElementById('catalogIndex'));
    extra.sep=function(){var el=document.getElementById('dualFsSep');if(!el)return null;var s=getComputedStyle(el);return{disp:s.display,w:Math.round(el.getBoundingClientRect().width)};}();
    extra.slot=typeof readModeSlot==='function'?readModeSlot(extra.display||'upper'):null;
    extra.edit=document.body.classList.contains('layout-edit');
    extra.editLabel=(document.getElementById('layoutEditBtn')||{}).textContent||'';
    extra.lockLabel=(document.getElementById('modePinBtn')||{}).textContent||'';
    fetch('""" + INGEST + r"""',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'f491c2'},body:JSON.stringify({sessionId:'f491c2',runId:window.__QA_RUNID||'mode-indep',hypothesisId:hid,location:loc,message:msg,data:extra,timestamp:Date.now()})}).catch(function(){});
  }catch(err){}
  // #endregion
}
window.logModeIndep=logModeIndep;
function leaveFullscreenDisplay(){
  setDisplayMode('upper');
}
window.leaveFullscreenDisplay=leaveFullscreenDisplay;
"""

# --- lastNonFs + log helper ---
add(
    "var DISPLAY_KEY='catalog-display-mode-'+(window.CATALOG_NS||'catalog');\n"
    "var currentDisplay='upper';\n",
    "var DISPLAY_KEY='catalog-display-mode-'+(window.CATALOG_NS||'catalog');\n"
    "var currentDisplay='upper';\n"
    "var lastNonFsDisplay='upper';\n"
    + LOG_HELPER,
    "last-nonfs-log",
)

# --- track last non-Full when switching ---
add(
    "  var prev=typeof currentDisplay!=='undefined'?currentDisplay:'';\n"
    "  var already=prev===mode;\n",
    "  var prev=typeof currentDisplay!=='undefined'?currentDisplay:'';\n"
    "  var already=prev===mode;\n"
    "  if(prev&&prev!=='fs')lastNonFsDisplay=prev;\n",
    "track-last-nonfs",
)

# --- H1: Full menu:'both' stays display-fs dual overlay, never Sides ---
add(
    "    var menu=opts.menu||((typeof getCurrentMode==='function'?getCurrentMode():'')==='pick'?'keywords':'search');\n"
    "    if(menu==='both'&&displayIsDesktop()){setDisplayMode('sides');return;}\n"
    "    document.body.classList.remove('dual-fs-open');\n"
    "    if(menu==='search'){\n",
    "    var menu=opts.menu||((typeof getCurrentMode==='function'?getCurrentMode():'')==='pick'?'keywords':'search');\n"
    "    document.body.classList.remove('search-chrome-collapsed','search-extras-collapsed','kw-chrome-collapsed');\n"
    "    if(menu==='both'){\n"
    "      if(typeof window.setAcFullscreen==='function')window.setAcFullscreen(true);\n"
    "      if(typeof window.setKwFullscreen==='function')window.setKwFullscreen(true);\n"
    "    }else if(menu==='search'){\n"
    "      document.body.classList.remove('dual-fs-open');\n",
    "fs-both-stay-fs",
)

# --- log after setDisplayMode ---
add(
    "  syncDisplayBtns();\n"
    "  if(typeof logLayoutModes==='function')logLayoutModes('setDisplayMode');\n",
    "  syncDisplayBtns();\n"
    "  if(typeof logModeIndep==='function')logModeIndep(mode==='fs'?'H1':(mode==='upper'?'H2':'H5'),'setDisplayMode','mode-set',{mode:mode,prev:prev});\n"
    "  if(typeof logLayoutModes==='function')logLayoutModes('setDisplayMode');\n",
    "log-mode-set",
)

# --- H1: ⛶ exits Full → Upper; from Upper/Sides enters solo Full (never Sides) ---
add(
    "window.toggleKwFullscreen=function(){\n"
    "  var desk=displayIsDesktop();\n"
    "  var both=document.body.classList.contains('search-mode')||document.body.classList.contains('ac-fs-open')||!!(document.getElementById('acList')&&document.getElementById('acList').classList.contains('open'));\n"
    "  if(document.body.classList.contains('display-sides')||document.body.classList.contains('display-fs')){setDisplayMode('upper');return;}\n"
    "  if(desk&&both){setDisplayMode('sides');return;}\n"
    "  setDisplayMode('fs',{menu:'keywords'});\n"
    "};\n"
    "window.toggleAcFullscreen=function(){\n"
    "  var desk=displayIsDesktop();\n"
    "  var both=document.body.classList.contains('kw-open')||document.body.classList.contains('kw-fs-open');\n"
    "  if(document.body.classList.contains('display-sides')||document.body.classList.contains('display-fs')){setDisplayMode('upper');return;}\n"
    "  if(desk&&both){setDisplayMode('sides');return;}\n"
    "  setDisplayMode('fs',{menu:'search'});\n"
    "};\n",
    "window.toggleKwFullscreen=function(){\n"
    "  if(document.body.classList.contains('display-fs')){\n"
    "    if(typeof leaveFullscreenDisplay==='function')leaveFullscreenDisplay();\n"
    "    else setDisplayMode('upper');\n"
    "    if(typeof logModeIndep==='function')logModeIndep('H1','toggleKwFullscreen','leave-fs',{});\n"
    "    return;\n"
    "  }\n"
    "  setDisplayMode('fs',{menu:'keywords'});\n"
    "};\n"
    "window.toggleAcFullscreen=function(){\n"
    "  if(document.body.classList.contains('display-fs')){\n"
    "    if(typeof leaveFullscreenDisplay==='function')leaveFullscreenDisplay();\n"
    "    else setDisplayMode('upper');\n"
    "    if(typeof logModeIndep==='function')logModeIndep('H1','toggleAcFullscreen','leave-fs',{});\n"
    "    return;\n"
    "  }\n"
    "  setDisplayMode('fs',{menu:'search'});\n"
    "};\n",
    "toggles-no-sides-coerce",
)

# --- H4: companion stays inside Full; never setDisplayMode('sides') ---
add(
    "window.toggleKwFsCompanion=function(){\n"
    "  if(typeof displayIsDesktop==='function'&&displayIsDesktop()&&typeof setDisplayMode==='function'){\n"
    "    setDisplayMode(document.body.classList.contains('display-sides')?'fs':'sides');\n"
    "    return;\n"
    "  }\n"
    "  setKwFullscreen(!kwFsWanted);\n"
    "};\n",
    "window.toggleKwFsCompanion=function(){\n"
    "  if(document.body.classList.contains('display-sides'))return;\n"
    "  if(!document.body.classList.contains('display-fs'))return;\n"
    "  setKwFullscreen(!kwFsWanted);\n"
    "  if(typeof logModeIndep==='function')logModeIndep('H4','toggleKwFsCompanion','companion-in-fs',{});\n"
    "};\n",
    "kw-companion-in-fs",
)
add(
    (
        "window.toggleAcFsCompanion=function(){\n"
        "  if(typeof displayIsDesktop==='function'&&displayIsDesktop()&&typeof setDisplayMode==='function'){\n"
        "    setDisplayMode(document.body.classList.contains('display-sides')?'fs':'sides');\n"
        "    return;\n"
        "  }\n",
        "window.toggleAcFsCompanion=function(){\n"
        "  if(document.body.classList.contains('display-sides'))return;\n"
        "  if(!document.body.classList.contains('display-fs'))return;\n",
    ),
    "window.toggleAcFsCompanion=function(){\n"
    "  if(document.body.classList.contains('display-sides'))return;\n"
    "  if(!document.body.classList.contains('display-fs'))return;\n"
    "  if(typeof logModeIndep==='function')logModeIndep('H4','toggleAcFsCompanion','companion-in-fs',{});\n",
    "ac-companion-in-fs",
    True,
)

# --- Keywords back arrow: one exit from Full ---
add(
    'id="kwFsBack" aria-label="Exit fullscreen Keywords" title="Exit fullscreen" onclick="event.preventDefault();event.stopPropagation();setKwFullscreen(false)"',
    'id="kwFsBack" aria-label="Exit fullscreen Keywords" title="Exit fullscreen" onclick="event.preventDefault();event.stopPropagation();toggleKwFullscreen()"',
    "kw-back-leave-fs",
)

# --- H3: applyModeSlot must not write Full heights into Upper live keys ---
add(
    "    if(mode==='sides'){\n"
    "      if(slot.lw&&slot.rw)localStorage.setItem(SIDES_KEY,JSON.stringify({lw:slot.lw,rw:slot.rw}));\n"
    "      if(slot.indexH)document.body.style.setProperty('--sides-index-h',parseInt(slot.indexH,10)+'px');\n"
    "      if(typeof slot.pinned==='boolean'){\n"
    "        sidesPinned=!!slot.pinned;\n"
    "        localStorage.setItem(SIDES_KEY+'-pin',sidesPinned?'1':'0');\n"
    "      }\n"
    "    }else{\n"
    "      setOrClear(liveLayoutKey('catalog-search-height-')+'-l', slot.chromeH);\n",
    "    if(mode==='sides'){\n"
    "      if(slot.lw&&slot.rw)localStorage.setItem(SIDES_KEY,JSON.stringify({lw:slot.lw,rw:slot.rw}));\n"
    "      if(slot.indexH)document.body.style.setProperty('--sides-index-h',parseInt(slot.indexH,10)+'px');\n"
    "      if(typeof slot.pinned==='boolean'){\n"
    "        sidesPinned=!!slot.pinned;\n"
    "        localStorage.setItem(SIDES_KEY+'-pin',sidesPinned?'1':'0');\n"
    "      }\n"
    "    }else if(mode==='fs'){\n"
    "      if(typeof logModeIndep==='function')logModeIndep('H3','applyModeSlot','fs-slot-skip-upper-keys',{hasAc:!!(slot&&slot.acH),hasKw:!!(slot&&slot.kwH)});\n"
    "    }else{\n"
    "      setOrClear(liveLayoutKey('catalog-search-height-')+'-l', slot.chromeH);\n",
    "slot-no-fs-clobber",
)
add(
    "      if(typeof window.setAcFullscreen==='function')window.setAcFullscreen(true);\n"
    "    }else{\n"
    "      if(typeof acFsWanted!=='undefined')acFsWanted=false;\n",
    "      if(typeof window.setAcFullscreen==='function')window.setAcFullscreen(true);\n"
    "    }else{\n"
    "      document.body.classList.remove('dual-fs-open');\n"
    "      if(typeof acFsWanted!=='undefined')acFsWanted=false;\n",
    "fs-kw-solo-no-dual",
)

# --- H2: leaving Sides clears leftover columns:unset so Upper can use 1-3 cols ---
add(
    "  if(!document.body.classList.contains('display-sides')||ix.classList.contains('is-collapsed')){\n"
    "    il.style.removeProperty('height');\n"
    "    il.style.removeProperty('max-height');\n"
    "    try{delete ix.dataset.ixFitInner;}catch(err){ix.dataset.ixFitInner='';}\n"
    "    return;\n"
    "  }\n",
    "  if(!document.body.classList.contains('display-sides')||ix.classList.contains('is-collapsed')){\n"
    "    ['height','max-height','columns','column-width','column-count','column-fill'].forEach(function(p){il.style.removeProperty(p);});\n"
    "    try{delete ix.dataset.ixFitInner;}catch(err){ix.dataset.ixFitInner='';}\n"
    "    if(typeof logModeIndep==='function'&&!document.body.classList.contains('display-sides'))logModeIndep('H2','applyIndexScrollFit','clear-cols-leave-sides',{});\n"
    "    return;\n"
    "  }\n",
    "ixfit-clear-cols",
)

# --- Upper/Full index in-flow 1-3 cols; hide companion dead-ends on Upper ---
add(
    " body.display-upper .ac-companion-btn,body.display-upper .kw-companion-btn{display:inline-flex!important}\n"
    " @media(max-width:899px){body.display-upper .ac-companion-btn,body.display-upper .kw-companion-btn{display:none!important}}\n",
    " body.display-upper .ac-companion-btn,body.display-upper .kw-companion-btn{display:none!important}\n"
    " body.display-upper #catalogIndex,body.display-fs #catalogIndex{position:static;height:auto;max-height:none;overflow:visible;border:0;box-shadow:none;display:block}\n"
    " body.display-upper #catalogIndex .index,body.display-upper #catalogIndex #catalogIndexList,body.display-fs #catalogIndex .index,body.display-fs #catalogIndex #catalogIndexList{column-width:clamp(14rem,28vw,18rem)!important;column-count:auto!important;columns:auto!important;column-fill:balance!important;height:auto!important;max-height:none!important;overflow:visible!important}\n"
    " body.display-fs:not(.dual-fs-open) #dualFsSep{display:none!important}\n",
    "upper-index-cols-css",
)
add(
    (
        "body.display-upper #catalogIndex .index,body.display-upper #catalogIndex #catalogIndexList,body.display-fs #catalogIndex .index,body.display-fs #catalogIndex #catalogIndexList{column-width:clamp(14rem,28vw,18rem)!important;column-count:auto!important;columns:auto!important;column-fill:balance!important;height:auto!important;max-height:none!important;overflow:visible!important}",
        "body.display-upper #catalogIndex .index,body.display-upper #catalogIndex #catalogIndexList,body.display-fs #catalogIndex .index,body.display-fs #catalogIndex #catalogIndexList{column-width:clamp(14rem,28vw,18rem)!important;column-count:auto!important;column-fill:balance!important;height:auto!important;max-height:none!important;overflow:visible!important}",
    ),
    "body.display-upper #catalogIndex .index,body.display-upper #catalogIndex #catalogIndexList,body.display-fs #catalogIndex .index,body.display-fs #catalogIndex #catalogIndexList{column-width:clamp(14rem,28vw,18rem)!important;column-count:3!important;column-fill:balance!important;height:auto!important;max-height:none!important;overflow:visible!important}",
    "upper-cols-max-3",
)


def must_replace(text, olds, new, label, optional=False, replace_all=False):
    if new in text:
        print(f"  skip {label} (already)")
        return text
    marker = None
    if "function leaveFullscreenDisplay" in new:
        marker = "function leaveFullscreenDisplay"
    elif "fs-slot-skip-upper-keys" in new:
        marker = "fs-slot-skip-upper-keys"
    elif "clear-cols-leave-sides" in new:
        marker = "clear-cols-leave-sides"
    elif "body.display-upper #catalogIndex,body.display-fs #catalogIndex" in new:
        marker = "body.display-upper #catalogIndex,body.display-fs #catalogIndex"
    elif "logModeIndep('H4','toggleKwFsCompanion'" in new:
        marker = "logModeIndep('H4','toggleKwFsCompanion'"
    elif "logModeIndep('H4','toggleAcFsCompanion'" in new:
        marker = "logModeIndep('H4','toggleAcFsCompanion'"
    elif "logModeIndep('H1','toggleKwFullscreen'" in new:
        marker = "logModeIndep('H1','toggleKwFullscreen'"
    elif "if(menu==='both'){" in new and "setAcFullscreen(true)" in new:
        marker = "if(menu==='both'){"
    elif "if(prev&&prev!=='fs')lastNonFsDisplay=prev;" in new:
        marker = "if(prev&&prev!=='fs')lastNonFsDisplay=prev;"
    elif "logModeIndep(mode==='fs'?'H1'" in new:
        marker = "logModeIndep(mode==='fs'?'H1'"
    elif "fs-slot-skip-upper-keys" in new:
        marker = "fs-slot-skip-upper-keys"
    elif "document.body.classList.remove('dual-fs-open');\n      if(typeof acFsWanted" in new:
        marker = "document.body.classList.remove('dual-fs-open');\n      if(typeof acFsWanted"
    elif "column-count:3!important" in new:
        marker = "column-count:3!important"
    if marker and marker in text:
        print(f"  skip {label} (already)")
        return text
    if any(o in text for o in olds):
        for old in olds:
            if old not in text:
                continue
            n = text.count(old)
            if replace_all or n != 1:
                if n != 1:
                    print(f"  warn {label} count={n}, replacing all")
                return text.replace(old, new)
            return text.replace(old, new, 1)
    if optional:
        print(f"  skip {label} (optional-missing)")
        return text
    raise SystemExit(f"MISSING [{label}]")


def assert_common(text, name):
    if "function hideSearchAc" not in text:
        raise SystemExit(f"{name} missing function hideSearchAc")
    if "function leaveFullscreenDisplay" not in text:
        raise SystemExit(f"{name} missing leaveFullscreenDisplay")
    if "if(menu==='both'&&displayIsDesktop()){setDisplayMode('sides');return;}" in text:
        raise SystemExit(f"{name} still coerces Full both → Sides")
    if "if(desk&&both){setDisplayMode('sides');return;}" in text:
        raise SystemExit(f"{name} still coerces ⛶ → Sides")
    if "setDisplayMode(document.body.classList.contains('display-sides')?'fs':'sides')" in text:
        raise SystemExit(f"{name} companion still teleports to Sides")
    if "fs-slot-skip-upper-keys" not in text:
        raise SystemExit(f"{name} missing applyModeSlot fs skip")
    if "clear-cols-leave-sides" not in text:
        raise SystemExit(f"{name} missing index column cleanup")
    if "body.display-upper #catalogIndex,body.display-fs #catalogIndex" not in text:
        raise SystemExit(f"{name} missing Upper index in-flow CSS")
    if ">Pick</button>" not in text:
        raise SystemExit(f"{name} lost Pick")
    if "b.textContent=on?'Done':'Customize'" not in text:
        raise SystemExit(f"{name} lost Customize")
    if "function toggleModeLock" not in text:
        raise SystemExit(f"{name} lost toggleModeLock")
    if "function collapseKwMenu" not in text:
        raise SystemExit(f"{name} lost collapseKwMenu")
    if "Hide Keywords" not in text:
        raise SystemExit(f"{name} lost Hide Keywords")
    if "No Shade" in text or ">Shade<" in text:
        raise SystemExit(f"{name} Shade label returned")
    if "columns:unset!important" not in text:
        raise SystemExit(f"{name} lost Sides index columns:unset")


def assert_html(text, name):
    assert_common(text, name)
    if "</html>" not in text:
        raise SystemExit(f"{name} missing </html>")


def patch(text, name):
    for old, new, label, optional, replace_all in REPLACEMENTS:
        text = must_replace(text, old, new, f"{name}:{label}", optional=optional, replace_all=replace_all)
    return text


def main():
    for name in ("build-ds-catalog-html.sh", "build-kontakt-catalog-html.sh"):
        src = KIRO / name
        raw = src.read_text(encoding="utf-8")
        out = patch(raw, f"KIRO/{name}")
        assert_common(out, f"KIRO/{name}")
        src.write_text(out, encoding="utf-8")
        WS.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, WS / name)
        print("patched+copied", name, len(out))

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
        out = patch(raw, path.name)
        if "function hideSearchAc" not in out or "</html>" not in out:
            raise SystemExit(f"{path.name} missing hideSearchAc or </html>")
        if "function setDisplayMode" in out:
            try:
                assert_common(out, path.name)
            except SystemExit as e:
                if "public/catalogs" in str(path):
                    raise
                print("  warn stale artifact", path.name, e)
        path.write_text(out, encoding="utf-8")
        print("patched", path.name, len(out))


if __name__ == "__main__":
    main()
