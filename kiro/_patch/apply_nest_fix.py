#!/usr/bin/env python3
"""Streamline Search/Keywords nest + Index scrollport (KIRO builders first)."""
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


NEST_HELPERS = r"""
function logNestFix(hid,loc,msg,extra){
  // #region agent log
  try{
    extra=extra||{};
    function pid(id){var el=document.getElementById(id);return el&&el.parentElement?(el.parentElement.id||el.parentElement.tagName):'';}
    function box(el){if(!el)return null;var b=el.getBoundingClientRect();return{x:Math.round(b.x),y:Math.round(b.y),w:Math.round(b.width),h:Math.round(b.height),b:Math.round(b.bottom)};}
    extra.display=typeof currentDisplay!=='undefined'?currentDisplay:'';
    extra.parents={fw:pid('filterWrap'),ch:pid('searchChrome'),sh:pid('acShell'),split:pid('searchSplit'),sep:pid('dualFsSep'),ix:pid('catalogIndex')};
    extra.chStyle=function(){var el=document.getElementById('searchChrome');return el?(el.getAttribute('style')||''):'';}();
    extra.sepX=function(){var el=document.getElementById('dualFsSep');if(!el||getComputedStyle(el).display==='none')return null;return Math.round(el.getBoundingClientRect().x);}();
    extra.hdrY=function(){var el=document.querySelector('.catalog-header');return el?Math.round(el.getBoundingClientRect().y):null;}();
    extra.dual=document.body.classList.contains('dual-fs-open');
    extra.collapsed=document.body.classList.contains('search-chrome-collapsed');
    extra.kwOpen=document.body.classList.contains('kw-open');
    var ix=document.getElementById('catalogIndex');
    var il=document.getElementById('catalogIndexList');
    if(ix)extra.ix=box(ix);
    if(il){
      var cs=getComputedStyle(il);
      extra.il={box:box(il),sh:il.scrollHeight,ch:il.clientHeight,st:Math.round(il.scrollTop),ov:cs.overflowY,cols:cs.columnWidth+'/'+cs.columnCount};
      var last=il.querySelector('li:last-child');
      extra.lastLi=last?box(last):null;
    }
    fetch('""" + INGEST + r"""',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'f491c2'},body:JSON.stringify({sessionId:'f491c2',runId:'nest-fix',hypothesisId:hid,location:loc,message:msg,data:extra,timestamp:Date.now()})}).catch(function(){});
  }catch(err){}
  // #endregion
}
function applyIndexScrollFit(){
  var ix=document.getElementById('catalogIndex');
  var il=document.getElementById('catalogIndexList')||(ix&&ix.querySelector('ul.index'));
  if(!ix||!il)return;
  if(!document.body.classList.contains('display-sides')||ix.classList.contains('is-collapsed')){
    il.style.removeProperty('height');
    il.style.removeProperty('max-height');
    return;
  }
  var head=ix.querySelector('.catalog-index-head');
  var hh=head?Math.round(head.getBoundingClientRect().height):0;
  var inner=Math.max(48,Math.round(ix.clientHeight-hh));
  il.style.setProperty('columns','unset','important');
  il.style.setProperty('column-width','unset','important');
  il.style.setProperty('column-count','unset','important');
  il.style.setProperty('column-fill','unset','important');
  il.style.height=inner+'px';
  il.style.maxHeight=inner+'px';
  if(!il.dataset.ixWheelBound){
    il.dataset.ixWheelBound='1';
    il.addEventListener('wheel',function(e){
      if(!document.body.classList.contains('display-sides'))return;
      var max=il.scrollHeight-il.clientHeight;
      if(max<=1)return;
      var atTop=il.scrollTop<=0&&e.deltaY<0;
      var atBot=il.scrollTop>=max-1&&e.deltaY>0;
      if(!atTop&&!atBot)e.stopPropagation();
    },{passive:true});
  }
  if(typeof logNestFix==='function')logNestFix('H6','applyIndexScrollFit','index-fit',{inner:inner,hh:hh,ixH:Math.round(ix.clientHeight)});
}
window.logNestFix=logNestFix;
window.applyIndexScrollFit=applyIndexScrollFit;
"""

# --- Index dock: single-column scrollport, flush to catalog column ---
add(
    "  body.display-sides #catalogMain{grid-column:2;grid-row:2;min-width:0;min-height:0;overflow-x:hidden;overflow-y:auto;-webkit-overflow-scrolling:touch;overscroll-behavior:contain;touch-action:pan-y;padding:.75rem 1rem 2rem}\n",
    "  body.display-sides #catalogMain{grid-column:2;grid-row:2;min-width:0;min-height:0;overflow-x:hidden;overflow-y:auto;-webkit-overflow-scrolling:touch;overscroll-behavior:contain;touch-action:pan-y;padding:0 0 2rem}\n"
    "  body.display-sides #catalogMain .catalog-body{padding-left:1rem;padding-right:1rem}\n",
    "sides-main-pad",
)
add(
    "  body.display-sides #catalogIndex{position:sticky;top:0;z-index:12;margin:0 0 .75rem;display:flex;flex-direction:column;height:var(--sides-index-h,min(48dvh,28rem));max-height:min(70dvh,40rem);overflow:hidden;border:1px solid var(--border);border-top-width:1px;border-radius:0 0 10px 10px;background:var(--bg-surface);box-shadow:0 10px 24px rgba(0,0,0,.32)}\n",
    "  body.display-sides #catalogIndex{position:sticky;top:0;z-index:12;box-sizing:border-box;width:100%;max-width:100%;margin:0 0 .75rem;display:flex;flex-direction:column;height:var(--sides-index-h,min(48dvh,28rem));max-height:min(70dvh,40rem);min-height:0;overflow:hidden;border:1px solid var(--border);border-radius:0 0 10px 10px;background:var(--bg-surface);box-shadow:0 10px 24px rgba(0,0,0,.32)}\n",
    "index-dock-box",
)
add(
    "  body.display-sides #catalogIndex .catalog-index-head{flex:0 0 auto;margin:0;padding:.4rem .65rem;cursor:pointer;border-bottom:1px solid var(--border);user-select:none}\n",
    "  body.display-sides #catalogIndex .catalog-index-head{flex:0 0 auto;margin:0;padding:.45rem .7rem;cursor:pointer;border-bottom:1px solid var(--border);user-select:none;min-width:0}\n"
    "  body.display-sides #catalogIndex .catalog-index-title{min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}\n",
    "index-head-align",
)
add(
    "  body.display-sides #catalogIndex .index,body.display-sides #catalogIndex #catalogIndexList{flex:1 1 auto;min-height:0;height:0;width:100%;max-width:100%;box-sizing:border-box;margin:0;padding:.4rem .7rem .75rem;overflow-x:hidden!important;overflow-y:auto!important;-webkit-overflow-scrolling:touch;overscroll-behavior:contain;touch-action:pan-y;column-width:auto!important;column-count:1!important;columns:1!important;column-gap:0;list-style:disc inside}\n"
    "  body.display-sides #catalogIndex .index li{break-inside:auto;margin:.12rem 0;padding:0;max-width:100%;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}\n"
    "  body.display-sides.layout-edit #catalogIndex .index,body.display-sides.layout-edit #catalogIndex #catalogIndexList{padding-bottom:1.05rem}\n",
    "  body.display-sides #catalogIndex .index,body.display-sides #catalogIndex #catalogIndexList{display:block!important;flex:1 1 auto;min-height:0;width:100%;max-width:100%;box-sizing:border-box;margin:0;padding:.4rem .7rem .75rem;overflow-x:hidden!important;overflow-y:auto!important;-webkit-overflow-scrolling:touch;overscroll-behavior:contain;touch-action:pan-y;columns:unset!important;column-width:unset!important;column-count:unset!important;column-gap:normal;column-fill:unset!important;list-style:disc;padding-left:1.25rem}\n"
    "  body.display-sides #catalogIndex .index li{display:list-item;break-inside:auto;-webkit-column-break-inside:auto;margin:.12rem 0;padding:0;max-width:100%;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}\n"
    "  body.display-sides.layout-edit #catalogIndex .index,body.display-sides.layout-edit #catalogIndex #catalogIndexList{padding-bottom:1.05rem}\n",
    "index-scrollport-nocol",
)

# --- applySplit: clear leftover chrome grid when leaving Upper ---
add(
    "function applySplit(){\n"
    "  if(document.body.classList.contains('display-sides')||document.body.classList.contains('display-fs'))return;\n",
    "function applySplit(){\n"
    "  if(document.body.classList.contains('display-sides')||document.body.classList.contains('display-fs')){\n"
    "    var el=chrome();\n"
    "    if(el)clearSplit(el);\n"
    "    if(typeof logNestFix==='function')logNestFix('H2','applySplit','clear-split-leave-upper',{});\n"
    "    return;\n"
    "  }\n",
    "apply-split-clear",
)

# --- leave sides: also reset index list height ---
add(
    "    if(typeof applyUpperContain==='function')applyUpperContain();\n"
    "// #region agent log\n"
    "fetch('http://127.0.0.1:7529/ingest/1cf46354-1d61-4c80-bd72-a340f1db1b51',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'f491c2'},body:JSON.stringify({sessionId:'f491c2',location:'applySidesCols',message:'shade-rm-leaveSides',",
    "    if(typeof applyUpperContain==='function')applyUpperContain();\n"
    "    if(typeof applyIndexScrollFit==='function')applyIndexScrollFit();\n"
    "// #region agent log\n"
    "fetch('http://127.0.0.1:7529/ingest/1cf46354-1d61-4c80-bd72-a340f1db1b51',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'f491c2'},body:JSON.stringify({sessionId:'f491c2',location:'applySidesCols',message:'shade-rm-leaveSides',",
    "leave-sides-ixfit",
)

# --- enter sides: drop leftover chrome grid/height ---
add(
    "    return;\n"
    "  }\n"
    "  var vw=window.innerWidth||1200;\n"
    "  var minL=240,minR=260,minC=280;\n"
    "  var o=readSidesCols();\n",
    "    return;\n"
    "  }\n"
    "  if(typeof clearChromeInlineLeftovers==='function')clearChromeInlineLeftovers();\n"
    "  var vw=window.innerWidth||1200;\n"
    "  var minL=240,minR=260,minC=280;\n"
    "  var o=readSidesCols();\n",
    "sides-clear-leftovers",
)

add(
    "  placeSidesHandles();\n"
    "  syncSidesPin();\n"
    "  if(typeof applyUpperContain==='function')applyUpperContain();\n"
    "}\n",
    "  placeSidesHandles();\n"
    "  syncSidesPin();\n"
    "  if(typeof applyUpperContain==='function')applyUpperContain();\n"
    "  if(typeof applyIndexScrollFit==='function')applyIndexScrollFit();\n"
    "  if(typeof logNestFix==='function')logNestFix('H5','applySidesCols','sides-nest',{});\n"
    "}\n",
    "sides-end-fit",
)

add(
    "  if(h>40)document.body.style.setProperty('--sides-index-h',h+'px');\n"
    "}\n"
    "function ensureIndexHeightHandle(){\n",
    "  if(h>40)document.body.style.setProperty('--sides-index-h',h+'px');\n"
    "  if(typeof applyIndexScrollFit==='function')applyIndexScrollFit();\n"
    "}\n"
    "function ensureIndexHeightHandle(){\n",
    "indexh-fit",
)

add(
    "    if(nh>40&&typeof writeModeSlot==='function')writeModeSlot({indexH:nh},'sides');\n"
    "    if(typeof logSidesEdit==='function')logSidesEdit('H2','indexHeight','pointerup',{indexH:nh});\n",
    "    if(nh>40&&typeof writeModeSlot==='function')writeModeSlot({indexH:nh},'sides');\n"
    "    if(typeof applyIndexScrollFit==='function')applyIndexScrollFit();\n"
    "    if(typeof logSidesEdit==='function')logSidesEdit('H2','indexHeight','pointerup',{indexH:nh});\n"
    "    if(typeof logNestFix==='function')logNestFix('H7','indexHeight','index-resized',{indexH:nh});\n",
    "index-drag-fit",
)
add(
    "  var inner=Math.max(48,Math.round(ix.clientHeight-hh));\n"
    "  il.style.height=inner+'px';\n"
    "  il.style.maxHeight=inner+'px';\n",
    "  var inner=Math.max(48,Math.round(ix.clientHeight-hh));\n"
    "  il.style.setProperty('columns','unset','important');\n"
    "  il.style.setProperty('column-width','unset','important');\n"
    "  il.style.setProperty('column-count','unset','important');\n"
    "  il.style.setProperty('column-fill','unset','important');\n"
    "  il.style.height=inner+'px';\n"
    "  il.style.maxHeight=inner+'px';\n",
    "ixfit-unset-cols",
)

# --- helpers + stronger leftover clear + nest reparent ---
add(
    "function clearChromeInlineLeftovers(){\n"
    "  var ch=document.getElementById('searchChrome');\n"
    "  if(ch){ch.style.removeProperty('grid-template-columns');ch.style.removeProperty('height');ch.style.removeProperty('max-height');}\n"
    "  var fw=document.getElementById('filterWrap');\n"
    "  if(fw&&!document.body.classList.contains('display-fs')){fw.style.removeProperty('height');fw.style.removeProperty('max-height');}\n"
    "}\n",
    NEST_HELPERS
    + "function clearChromeInlineLeftovers(){\n"
    "  var ch=document.getElementById('searchChrome');\n"
    "  var had=ch?((ch.getAttribute('style')||'')+''):'';\n"
    "  if(ch){\n"
    "    ch.style.removeProperty('grid-template-columns');\n"
    "    ch.style.removeProperty('grid-template-rows');\n"
    "    ch.style.removeProperty('height');\n"
    "    ch.style.removeProperty('max-height');\n"
    "    if(!document.body.classList.contains('display-upper')){\n"
    "      ch.classList.remove('search-split-lr','search-split-ud','search-split-dragging','search-height-set');\n"
    "    }\n"
    "  }\n"
    "  var fw=document.getElementById('filterWrap');\n"
    "  if(fw&&!document.body.classList.contains('display-fs')){\n"
    "    fw.style.removeProperty('height');\n"
    "    fw.style.removeProperty('max-height');\n"
    "  }\n"
    "  ['acShell','kwbar','filterPanel'].forEach(function(id){\n"
    "    var el=document.getElementById(id);\n"
    "    if(el&&!document.body.classList.contains('display-upper'))el.style.removeProperty('max-height');\n"
    "  });\n"
    "  var split=document.getElementById('searchSplit');\n"
    "  var sep=document.getElementById('dualFsSep');\n"
    "  if(!document.body.classList.contains('display-sides')){\n"
    "    if(split)split.removeAttribute('style');\n"
    "    if(sep&&!document.body.classList.contains('dual-fs-open'))sep.removeAttribute('style');\n"
    "  }\n"
    "  if(had&&(had.indexOf('grid-template')>=0||had.indexOf('height')>=0)&&typeof logNestFix==='function')logNestFix('H2','clearChromeInlineLeftovers','cleared-inline',{had:had.slice(0,160)});\n"
    "}\n",
    "clear-leftovers",
)

add(
    "function placeMenusForDisplay(mode){\n"
    "  var ch=document.getElementById('searchChrome');\n"
    "  var fw=document.getElementById('filterWrap');\n"
    "  var main=document.getElementById('catalogMain');\n"
    "  var split=document.getElementById('searchSplit');\n"
    "  if(!ch||!fw)return;\n"
    "  var searchOnlyFs=mode==='fs'&&document.body.classList.contains('ac-fs-open')&&!document.body.classList.contains('kw-fs-open');\n"
    "  if(mode==='sides'||(mode==='fs'&&!searchOnlyFs)){\n"
    "    if(fw.parentElement!==document.body){\n"
    "      document.body.insertBefore(fw, main||ch.nextSibling);\n"
    "    }\n"
    "  }else if(fw.parentElement!==ch){\n"
    "    ch.appendChild(fw);\n"
    "  }\n"
    "  if(mode==='upper'&&split&&split.parentElement!==ch){\n"
    "    var col=document.getElementById('searchCol');\n"
    "    if(col&&col.nextSibling)ch.insertBefore(split,col.nextSibling);\n"
    "    else ch.insertBefore(split,fw);\n"
    "  }\n"
    "}\n",
    "function placeMenusForDisplay(mode){\n"
    "  var ch=document.getElementById('searchChrome');\n"
    "  var fw=document.getElementById('filterWrap');\n"
    "  var main=document.getElementById('catalogMain');\n"
    "  var split=document.getElementById('searchSplit');\n"
    "  var sep=document.getElementById('dualFsSep');\n"
    "  var ht=document.getElementById('searchHeight');\n"
    "  if(!ch||!fw)return;\n"
    "  var body=document.body;\n"
    "  var col=document.getElementById('searchCol');\n"
    "  if(mode==='sides'){\n"
    "    if(fw.parentElement!==body)body.insertBefore(fw, main||null);\n"
    "    if(split&&split.parentElement!==body)body.insertBefore(split, fw);\n"
    "    if(sep&&sep.parentElement!==body)body.insertBefore(sep, fw);\n"
    "    if(ht&&ht.parentElement!==ch)ch.appendChild(ht);\n"
    "  }else if(mode==='fs'){\n"
    "    if(fw.parentElement!==body)body.insertBefore(fw, main||null);\n"
    "    if(split){\n"
    "      if(col&&split.parentElement!==ch){if(col.nextSibling)ch.insertBefore(split,col.nextSibling);else ch.appendChild(split);}\n"
    "    }\n"
    "    if(sep&&sep.parentElement!==body)body.insertBefore(sep, main||fw);\n"
    "    if(ht&&ht.parentElement!==ch)ch.appendChild(ht);\n"
    "  }else{\n"
    "    if(fw.parentElement!==ch)ch.appendChild(fw);\n"
    "    if(split){\n"
    "      if(col&&(split.parentElement!==ch||split.previousElementSibling!==col)){\n"
    "        if(col.nextSibling)ch.insertBefore(split,col.nextSibling);\n"
    "        else ch.insertBefore(split,fw);\n"
    "      }else if(!col&&split.parentElement!==ch)ch.insertBefore(split,fw);\n"
    "    }\n"
    "    if(ht&&ht.parentElement!==ch)ch.appendChild(ht);\n"
    "    if(sep&&sep.parentElement!==body)body.insertBefore(sep, main||ch.nextSibling);\n"
    "  }\n"
    "  if(typeof logNestFix==='function')logNestFix(mode==='fs'?'H4':(mode==='sides'?'H1':'H5'),'placeMenusForDisplay','reparent',{mode:mode});\n"
    "}\n",
    "place-menus",
)

add(
    "  if(mode!=='sides'&&typeof clearChromeInlineLeftovers==='function')clearChromeInlineLeftovers();\n",
    "  if(typeof clearChromeInlineLeftovers==='function')clearChromeInlineLeftovers();\n",
    "setdisplay-always-clear",
)

add(
    "  if(typeof applyUpperContain==='function')applyUpperContain();\n"
    "  syncDisplayBtns();\n",
    "  if(typeof applyUpperContain==='function')applyUpperContain();\n"
    "  if(typeof applyIndexScrollFit==='function')applyIndexScrollFit();\n"
    "  if(typeof logNestFix==='function')logNestFix(mode==='fs'?'H4':(mode==='upper'?'H1':'H5'),'setDisplayMode','nest-after',{});\n"
    "  syncDisplayBtns();\n",
    "setdisplay-after",
)


def must_replace(text, olds, new, label, optional=False, replace_all=False):
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
    if new in text:
        print(f"  skip {label} (already)")
        return text
    if optional:
        print(f"  skip {label} (optional-missing)")
        return text
    raise SystemExit(f"MISSING [{label}]")


def assert_common(text, name):
    if "function hideSearchAc" not in text:
        raise SystemExit(f"{name} missing function hideSearchAc")
    if "function logNestFix" not in text:
        raise SystemExit(f"{name} missing logNestFix")
    if "function applyIndexScrollFit" not in text:
        raise SystemExit(f"{name} missing applyIndexScrollFit")
    if "column-width:unset!important" not in text:
        raise SystemExit(f"{name} missing index scrollport columns-unset")
    if "runId:'nest-fix'" not in text:
        raise SystemExit(f"{name} missing nest-fix logs")
    if "if(fw.parentElement!==body)body.insertBefore(fw, main||null);" not in text:
        raise SystemExit(f"{name} missing sides/fs body reparent")
    if "if(typeof clearChromeInlineLeftovers==='function')clearChromeInlineLeftovers();" not in text:
        raise SystemExit(f"{name} missing always-clear leftovers")
    if ">Pick</button>" not in text:
        raise SystemExit(f"{name} lost Pick")
    if "function toggleModeLock" not in text:
        raise SystemExit(f"{name} lost toggleModeLock")
    if "b.textContent=on?'Done':'Customize'" not in text:
        raise SystemExit(f"{name} lost Customize")


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
        assert_html(out, path.name)
        path.write_text(out, encoding="utf-8")
        print("patched", path.name, len(out))


if __name__ == "__main__":
    main()
