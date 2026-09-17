#!/usr/bin/env python3
"""Per-display-mode layout store, handles, and restored menu buttons.

Patch KIRO builders first, copy to workspace, then in-memory sync HTML.
"""
from pathlib import Path
import shutil

KIRO = Path("/home/phnx/KIRO/.kiro/specs/kontakt-workspace-drive-dirty-fix/artifacts")
WS = Path("/home/phnx/kiro-kontakt-patch/kiro/specs/kontakt-workspace-drive-dirty-fix/artifacts")
PUB = Path("/home/phnx/kiro-kontakt-patch/public/catalogs")

INGEST = "http://127.0.0.1:7529/ingest/1cf46354-1d61-4c80-bd72-a340f1db1b51"

REPLACEMENTS = []


def add(old, new, label, optional=False):
    REPLACEMENTS.append((old, new, label, optional))


# --- CSS: Upper menus fill more of the viewport; height-set wins over 32vh ---
add(
    "  body.search-mode.kw-open:not(.kw-fs-open):not(.search-chrome-collapsed) .filter-wrap.open .filter-panel,\n"
    "  body.search-mode.kw-open:not(.kw-fs-open):not(.search-chrome-collapsed) .filter-wrap.kw-shade-height-set.open .filter-panel{position:static!important;width:auto!important;max-width:100%;max-height:min(32vh,20rem)!important;box-shadow:none;border:0;border-radius:0}\n"
    "  body.search-mode.kw-open:not(.ac-fs-open):not(.search-chrome-collapsed) .search-col{overflow:hidden;z-index:auto}\n"
    "  body.search-mode.kw-open:not(.ac-fs-open):not(.search-chrome-collapsed) .search-ac-shell.open:not(.ac-fs),\n"
    "  body.search-mode.kw-open:not(.ac-fs-open):not(.search-chrome-collapsed) .search-ac-shell:has(#acList.open):not(.ac-fs){position:relative!important;left:auto!important;top:auto!important;right:auto!important;width:auto!important;max-width:100%!important;height:auto!important;max-height:min(32vh,20rem);box-shadow:none;border:0;border-radius:0;overflow-x:hidden;overflow-y:auto;-webkit-overflow-scrolling:touch;overscroll-behavior:contain}\n"
    "  body.search-mode.kw-open:not(.ac-fs-open):not(.search-chrome-collapsed) .search-autocomplete.open{max-height:min(32vh,20rem);overflow-y:auto}\n",
    "  body.search-mode.kw-open:not(.kw-fs-open):not(.search-chrome-collapsed):not(.display-sides):not(.display-fs) .filter-wrap.open .filter-panel{position:static!important;width:auto!important;max-width:100%;max-height:var(--upper-kw-h,min(48vh,32rem))!important;box-shadow:none;border:0;border-radius:0}\n"
    "  body.search-mode.kw-open:not(.kw-fs-open):not(.search-chrome-collapsed):not(.display-sides):not(.display-fs) .filter-wrap.kw-shade-height-set.open .filter-panel,\n"
    "  body.search-mode.kw-open:not(.kw-fs-open):not(.search-chrome-collapsed).search-height-set .filter-wrap.open .filter-panel,\n"
    "  body.search-mode.kw-open:not(.kw-fs-open):not(.search-chrome-collapsed) .search-chrome.search-height-set .filter-wrap.open .filter-panel{position:static!important;width:auto!important;max-width:100%;max-height:none!important;box-shadow:none;border:0;border-radius:0}\n"
    "  body.search-mode.kw-open:not(.ac-fs-open):not(.search-chrome-collapsed) .search-col{overflow:hidden;z-index:auto}\n"
    "  body.search-mode.kw-open:not(.ac-fs-open):not(.search-chrome-collapsed):not(.display-sides):not(.display-fs) .search-ac-shell.open:not(.ac-fs),\n"
    "  body.search-mode.kw-open:not(.ac-fs-open):not(.search-chrome-collapsed):not(.display-sides):not(.display-fs) .search-ac-shell:has(#acList.open):not(.ac-fs){position:relative!important;left:auto!important;top:auto!important;right:auto!important;width:auto!important;max-width:100%!important;height:auto!important;max-height:var(--upper-ac-h,min(48vh,32rem));box-shadow:none;border:0;border-radius:0;overflow-x:hidden;overflow-y:auto;-webkit-overflow-scrolling:touch;overscroll-behavior:contain}\n"
    "  body.search-mode.kw-open:not(.ac-fs-open):not(.search-chrome-collapsed) .search-chrome.search-height-set .search-ac-shell.open:not(.ac-fs),\n"
    "  body.search-mode.kw-open:not(.ac-fs-open):not(.search-chrome-collapsed) .search-ac-shell.ac-height-set.open:not(.ac-fs){max-height:none;height:auto}\n"
    "  body.search-mode.kw-open:not(.ac-fs-open):not(.search-chrome-collapsed):not(.display-sides):not(.display-fs) .search-autocomplete.open{max-height:inherit;overflow-y:auto}\n"
    "  body.search-mode.kw-open:not(.ac-fs-open):not(.search-chrome-collapsed):not(.display-sides):not(.display-fs) .search-chrome.search-height-set .search-autocomplete.open{max-height:none}\n",
    "upper-cap",
)

add(
    " body.search-mode .kw-shade-height,body.search-mode .search-chrome.search-split-ud .kw-shade-height{display:none}\n",
    " body.search-mode:not(.display-upper):not(.display-fs) .kw-shade-height,body.search-mode .search-chrome.search-split-ud .kw-shade-height{display:none}\n"
    " body.search-mode.display-upper .filter-wrap.open>.kw-shade-height,body.search-mode.display-fs .filter-wrap.open>.kw-shade-height{display:block}\n",
    "kw-handle-vis",
)

add(
    " .search-ac-shell.ac-fs>.ac-height,.search-ac-shell.ac-fs>.ac-width{display:none!important}\n",
    " .search-ac-shell.ac-fs>.ac-width{display:none!important}\n"
    " body:not(.layout-edit) .search-ac-shell.ac-fs>.ac-height{display:none!important}\n"
    " body.display-fs.layout-edit .search-ac-shell.ac-fs>.ac-height{display:block!important}\n",
    "fs-ac-handle",
)

add(
    " body.display-sides #acFsBar,body.display-sides .ac-fs-bar,body.display-sides .kw-fs-back,body.display-sides .ac-fs-back,body.display-sides .ac-companion-btn,body.display-sides .kw-companion-btn,body.display-sides .kw-fs-btn,body.display-sides .search-strip-fs,body.display-sides .fs-stripe-wrap,body.display-sides .fs-mode-nav{display:none!important}\n",
    " body.display-sides #acFsBar,body.display-sides .ac-fs-bar,body.display-sides .kw-fs-back,body.display-sides .ac-fs-back,body.display-sides .ac-companion-btn,body.display-sides .kw-companion-btn,body.display-sides .fs-stripe-wrap,body.display-sides .fs-mode-nav{display:none!important}\n"
    " body.display-sides .kw-fs-btn,body.display-sides .search-strip-fs{display:inline-flex!important}\n",
    "sides-btns",
)

add(
    " body.display-upper .ac-companion-btn,body.display-upper .kw-companion-btn,body.display-upper .kw-fs-btn,body.display-upper .search-strip-fs,body.display-upper .fs-stripe-wrap,body.display-upper .fs-mode-nav{display:none!important}\n",
    " body.display-upper .fs-stripe-wrap,body.display-upper .fs-mode-nav,body.display-fs .fs-mode-nav{display:none!important}\n"
    " body.display-upper .search-strip-fs,body.display-upper .kw-fs-btn{display:inline-flex!important}\n"
    " body.display-upper .ac-companion-btn,body.display-upper .kw-companion-btn{display:inline-flex!important}\n"
    " @media(max-width:899px){body.display-upper .ac-companion-btn,body.display-upper .kw-companion-btn{display:none!important}}\n"
    " body.display-fs.kw-fs-open .filter-kw-tools{display:flex!important;flex-wrap:wrap;gap:.35rem}\n"
    " body.display-fs.kw-fs-open .filter-panel>.mode-switch{display:flex!important;flex-wrap:wrap}\n"
    " body.display-fs.ac-fs-open #acShell.ac-fs{height:var(--fs-ac-h,calc(100dvh - var(--cat-header-h,3.5rem)))!important;max-height:var(--fs-ac-h,none);bottom:auto!important}\n"
    " body.display-fs.kw-fs-open #filterWrap{height:var(--fs-kw-h,calc(100dvh - var(--cat-header-h,3.5rem)))!important;max-height:var(--fs-kw-h,none);bottom:auto!important}\n"
    " .filter-top #layoutEditBtn,.filter-top #modePinBtn{flex:0 0 auto}\n"
    " body.mode-layout-pinned.layout-edit .search-split,body.mode-layout-pinned.layout-edit .search-height,body.mode-layout-pinned.layout-edit .ac-height,body.mode-layout-pinned.layout-edit .kw-shade-height,body.mode-layout-pinned.layout-edit #searchSplit,body.mode-layout-pinned.layout-edit #dualFsSep{cursor:default!important;pointer-events:none!important}\n",
    "upper-fs-btns",
)

# --- JS: shadeOn allows Keywords height in Upper/Full (Search is the only data mode) ---
add(
    "function shadeOn(){var w=wrap();return !!(w&&w.classList.contains('open')&&!document.body.classList.contains('search-mode'));}",
    "function shadeOn(){var w=wrap();if(!w||!w.classList.contains('open'))return false;if(document.body.classList.contains('display-sides'))return false;if(document.body.classList.contains('display-upper')||document.body.classList.contains('display-fs'))return true;return !document.body.classList.contains('search-mode');}",
    "shadeOn",
)

add(
    "function applySplit(){\n  if(document.body.classList.contains('display-sides'))return;\n",
    "function applySplit(){\n  if(document.body.classList.contains('display-sides')||document.body.classList.contains('display-fs'))return;\n",
    "applySplit-skip-fs",
)

add(
    "function applyHeight(){\n  var el=chrome(),b=heightBtn();\n  if(!el)return;\n  if(!heightOn()){\n    clearHeight(el);\n    if(b)b.setAttribute('aria-hidden','true');\n    return;\n  }\n",
    "function applyHeight(){\n  var el=chrome(),b=heightBtn();\n  if(!el)return;\n  if(document.body.classList.contains('display-sides')||document.body.classList.contains('display-fs')){\n    clearHeight(el);\n    if(b)b.setAttribute('aria-hidden','true');\n    return;\n  }\n  if(!heightOn()){\n    clearHeight(el);\n    if(b)b.setAttribute('aria-hidden','true');\n    return;\n  }\n",
    "applyHeight-skip",
)

add(
    "  var stored=readHeightRatio();\n  if(stored==null){\n    if(!hdrag){\n      var cur=el.getBoundingClientRect().height;\n      var bds0=heightBounds();\n      if(layoutEdit()&&cur>bds0.max)setChromeHeight(el,bds0.max);\n      else if(layoutEdit()&&cur<bds0.min)setChromeHeight(el,bds0.min);\n      else if(!layoutEdit()&&!el.classList.contains('search-height-set'))clearHeight(el);\n    }\n    return;\n  }\n",
    "  var stored=readHeightRatio();\n  if(stored==null&&document.body.classList.contains('display-upper'))stored=0.48;\n  if(stored==null){\n    if(!hdrag){\n      var cur=el.getBoundingClientRect().height;\n      var bds0=heightBounds();\n      if(layoutEdit()&&cur>bds0.max)setChromeHeight(el,bds0.max);\n      else if(layoutEdit()&&cur<bds0.min)setChromeHeight(el,bds0.min);\n      else if(!layoutEdit()&&!el.classList.contains('search-height-set'))clearHeight(el);\n    }\n    return;\n  }\n",
    "applyHeight-default",
)

add(
    "function writeHeightRatio(ratio){\n  try{localStorage.setItem(KEYHT+'-l',String(ratio));}catch(err){}\n}",
    "function writeHeightRatio(ratio){\n  try{localStorage.setItem(KEYHT+'-l',String(ratio));}catch(err){}\n  if(typeof writeModeSlot==='function')writeModeSlot({chromeH:String(ratio)});\n}",
    "writeHeightRatio",
)

add(
    "function writeRatio(axis,ratio){\n  try{localStorage.setItem(splitRatioKey(axis),String(ratio));}catch(err){}\n}",
    "function writeRatio(axis,ratio){\n  try{localStorage.setItem(splitRatioKey(axis),String(ratio));}catch(err){}\n  if(typeof writeModeSlot==='function'){var p={};p[axis==='h'?'splitH':'splitV']=String(ratio);writeModeSlot(p);}\n}",
    "writeRatio",
)

add(
    "function writeExtraRatio(key,ratio){\n  try{localStorage.setItem(key,String(ratio));}catch(err){}\n}",
    "function writeExtraRatio(key,ratio){\n  try{localStorage.setItem(key,String(ratio));}catch(err){}\n  if(typeof writeModeSlot==='function'){if(key===KEYAC||key===KEYACSO)writeModeSlot({acH:String(ratio)});if(key===KEYSH)writeModeSlot({kwH:String(ratio)});}\n}",
    "writeExtraRatio",
)

add(
    "  if(!b||!ac||!acOpen()||!layoutEdit()||acFullscreen())return;\n",
    "  if(!b||!ac||!acOpen()||!layoutEdit())return;\n  if(typeof modeLayoutPinned==='function'&&modeLayoutPinned())return;\n  if(acFullscreen()&&!document.body.classList.contains('display-fs'))return;\n",
    "onAcDown-fs",
)

add(
    "  if(!b||!el||!heightOn()||!layoutEdit())return;\n",
    "  if(!b||!el||!heightOn()||!layoutEdit())return;\n  if(typeof modeLayoutPinned==='function'&&modeLayoutPinned())return;\n",
    "onHeightDown-pin",
)

add(
    "  if(!b||!w||!shadeOn()||!layoutEdit())return;\n",
    "  if(!b||!w||!shadeOn()||!layoutEdit())return;\n  if(typeof modeLayoutPinned==='function'&&modeLayoutPinned())return;\n",
    "onShadeDown-pin",
)

add(
    "    writeSnapKey(KEYAC,snap.ac);writeSnapKey(KEYSH,snap.sh);\n"
    "  }\n"
    "  applyAll();\n"
    "}\n",
    "    writeSnapKey(KEYAC,snap.ac);writeSnapKey(KEYSH,snap.sh);\n"
    "  }\n"
    "  applyAll();\n"
    "  if(typeof snapshotLiveToMode==='function')snapshotLiveToMode();\n"
    "}\n",
    "applySnapshot-slot",
)

add(
    "function persistAllLiveLayouts(){\n  try{if(typeof persist==='function')persist();}catch(err){}\n  try{if(typeof persistHeight==='function')persistHeight();}catch(err){}\n  try{if(typeof persistAcHeight==='function')persistAcHeight();}catch(err){}\n  try{if(typeof persistAcWidth==='function')persistAcWidth();}catch(err){}\n  try{if(typeof persistShadeHeight==='function')persistShadeHeight();}catch(err){}\n}",
    "function persistAllLiveLayouts(){\n  try{if(typeof persist==='function')persist();}catch(err){}\n  try{if(typeof persistHeight==='function')persistHeight();}catch(err){}\n  try{if(typeof persistAcHeight==='function')persistAcHeight();}catch(err){}\n  try{if(typeof persistAcWidth==='function')persistAcWidth();}catch(err){}\n  try{if(typeof persistShadeHeight==='function')persistShadeHeight();}catch(err){}\n  try{if(typeof snapshotLiveToMode==='function')snapshotLiveToMode();}catch(err){}\n}",
    "persistAll",
)

add(
    "function applyActiveLayoutStore(){\n  syncLayoutStoreUi();\n  var so=searchOnlyStore();\n  var last=readLastNamed(so);\n  if(last){\n    var map=readNamedMap(so);\n    if(map[last]){applySnapshot(map[last],so);return;}\n  }\n  applyAll();\n}",
    "function applyActiveLayoutStore(){\n  syncLayoutStoreUi();\n  if(typeof applyModeSlot==='function')applyModeSlot(typeof currentDisplay!=='undefined'?currentDisplay:'upper');\n  applyAll();\n  if(typeof applySidesCols==='function')applySidesCols();\n  if(typeof applyFsChromeSize==='function')applyFsChromeSize();\n  if(typeof logLayoutModes==='function')logLayoutModes('applyActiveLayoutStore');\n}",
    "applyActiveLayoutStore",
)

add(
    "function writeSidesCols(lw,rw){\n  if(sidesPinned)return;\n  try{localStorage.setItem(SIDES_KEY,JSON.stringify({lw:lw,rw:rw}));}catch(err){}\n}",
    "function writeSidesCols(lw,rw){\n  if(sidesPinned)return;\n  try{localStorage.setItem(SIDES_KEY,JSON.stringify({lw:lw,rw:rw}));}catch(err){}\n  if(typeof writeModeSlot==='function')writeModeSlot({lw:lw,rw:rw},'sides');\n}",
    "writeSidesCols",
)

add(
    "function placeMenusForDisplay(mode){\n  var ch=document.getElementById('searchChrome');\n  var fw=document.getElementById('filterWrap');\n  var main=document.getElementById('catalogMain');\n  if(!ch||!fw)return;\n  if(mode==='sides'){\n    if(fw.parentElement!==document.body){\n      document.body.insertBefore(fw, main||ch.nextSibling);\n    }\n  }else if(fw.parentElement!==ch){\n    ch.appendChild(fw);\n  }\n}",
    "function placeMenusForDisplay(mode){\n  var ch=document.getElementById('searchChrome');\n  var fw=document.getElementById('filterWrap');\n  var main=document.getElementById('catalogMain');\n  var split=document.getElementById('searchSplit');\n  if(!ch||!fw)return;\n  var searchOnlyFs=mode==='fs'&&document.body.classList.contains('ac-fs-open')&&!document.body.classList.contains('kw-fs-open');\n  if(mode==='sides'||(mode==='fs'&&!searchOnlyFs)){\n    if(fw.parentElement!==document.body){\n      document.body.insertBefore(fw, main||ch.nextSibling);\n    }\n  }else if(fw.parentElement!==ch){\n    ch.appendChild(fw);\n  }\n  if(mode==='upper'&&split&&split.parentElement!==ch){\n    var col=document.getElementById('searchCol');\n    if(col&&col.nextSibling)ch.insertBefore(split,col.nextSibling);\n    else ch.insertBefore(split,fw);\n  }\n}",
    "placeMenus",
)

MODE_JS = r"""
var MODE_LAYOUT_KEY='catalog-layout-'+(window.CATALOG_NS||'catalog');
function liveLayoutKey(suffix){return suffix+(window.CATALOG_NS||'catalog');}
function displayModeSlot(){
  var m=typeof currentDisplay!=='undefined'?currentDisplay:'upper';
  if(m!=='upper'&&m!=='sides'&&m!=='fs')m='upper';
  return m;
}
function emptyModeLayout(){return {upper:{},sides:{},fs:{}};}
function readModeLayoutStore(){
  try{
    var o=JSON.parse(localStorage.getItem(MODE_LAYOUT_KEY)||'null');
    if(o&&typeof o==='object'&&!Array.isArray(o)){
      return {
        upper:o.upper&&typeof o.upper==='object'?o.upper:{},
        sides:o.sides&&typeof o.sides==='object'?o.sides:{},
        fs:o.fs&&typeof o.fs==='object'?o.fs:{}
      };
    }
  }catch(err){}
  var store=emptyModeLayout();
  try{
    var sc=JSON.parse(localStorage.getItem(SIDES_KEY)||'null');
    if(sc&&sc.lw&&sc.rw){store.sides.lw=sc.lw;store.sides.rw=sc.rw;}
    if(localStorage.getItem(SIDES_KEY+'-pin')==='1')store.sides.pinned=true;
  }catch(err){}
  try{
    var ac=localStorage.getItem(liveLayoutKey('catalog-search-ac-height-'));
    var sh=localStorage.getItem(liveLayoutKey('catalog-keywords-shade-height-'));
    var h=localStorage.getItem(liveLayoutKey('catalog-search-split-h-'));
    var v=localStorage.getItem(liveLayoutKey('catalog-search-split-v-'));
    var ht=localStorage.getItem(liveLayoutKey('catalog-search-height-')+'-l');
    if(ac)store.upper.acH=ac;
    if(sh)store.upper.kwH=sh;
    if(h)store.upper.splitH=h;
    if(v)store.upper.splitV=v;
    if(ht)store.upper.chromeH=ht;
  }catch(err){}
  return store;
}
function writeModeLayoutStore(store){
  try{localStorage.setItem(MODE_LAYOUT_KEY,JSON.stringify(store));}catch(err){}
}
function readModeSlot(mode){
  var s=readModeLayoutStore();
  return s[mode||displayModeSlot()]||{};
}
function writeModeSlot(patch,mode){
  mode=mode||displayModeSlot();
  var s=readModeLayoutStore();
  var cur=s[mode]||{};
  Object.keys(patch||{}).forEach(function(k){cur[k]=patch[k];});
  s[mode]=cur;
  writeModeLayoutStore(s);
  return cur;
}
function modeLayoutPinned(){
  if(document.body.classList.contains('display-sides')&&sidesPinned)return true;
  try{var s=readModeSlot();return !!(s&&s.pinned);}catch(err){return false;}
}
function snapshotLiveToMode(mode){
  mode=mode||displayModeSlot();
  var patch={};
  try{
    if(mode==='sides'){
      var lw=parseInt(getComputedStyle(document.body).getPropertyValue('--sides-lw'),10)||0;
      var rw=parseInt(getComputedStyle(document.body).getPropertyValue('--sides-rw'),10)||0;
      if(lw)patch.lw=lw;
      if(rw)patch.rw=rw;
      patch.pinned=!!sidesPinned;
    }else{
      try{patch.chromeH=localStorage.getItem(liveLayoutKey('catalog-search-height-')+'-l')||undefined;}catch(err){}
      try{patch.splitH=localStorage.getItem(liveLayoutKey('catalog-search-split-h-'))||undefined;}catch(err){}
      try{patch.splitV=localStorage.getItem(liveLayoutKey('catalog-search-split-v-'))||undefined;}catch(err){}
      try{patch.acH=localStorage.getItem(liveLayoutKey('catalog-search-ac-height-'))||undefined;}catch(err){}
      try{patch.kwH=localStorage.getItem(liveLayoutKey('catalog-keywords-shade-height-'))||undefined;}catch(err){}
      if(mode==='fs'){
        patch.menu=document.body.classList.contains('kw-fs-open')&&!document.body.classList.contains('ac-fs-open')?'keywords':(document.body.classList.contains('ac-fs-open')&&!document.body.classList.contains('kw-fs-open')?'search':'both');
        var acVar=getComputedStyle(document.documentElement).getPropertyValue('--fs-ac-h').trim();
        var kwVar=getComputedStyle(document.documentElement).getPropertyValue('--fs-kw-h').trim();
        var avail=Math.max(160,(window.innerHeight||800)-56);
        if(acVar&&acVar.indexOf('px')>0)patch.acH=String(parseFloat(acVar)/avail);
        if(kwVar&&kwVar.indexOf('px')>0)patch.kwH=String(parseFloat(kwVar)/avail);
      }
    }
  }catch(err){}
  writeModeSlot(patch,mode);
  return patch;
}
function applyModeSlot(mode){
  mode=mode||displayModeSlot();
  var slot=readModeSlot(mode);
  try{
    if(mode==='sides'){
      if(slot.lw&&slot.rw)localStorage.setItem(SIDES_KEY,JSON.stringify({lw:slot.lw,rw:slot.rw}));
      if(typeof slot.pinned==='boolean'){
        sidesPinned=!!slot.pinned;
        localStorage.setItem(SIDES_KEY+'-pin',sidesPinned?'1':'0');
      }
    }else{
      if(slot.chromeH!=null)localStorage.setItem(liveLayoutKey('catalog-search-height-')+'-l',String(slot.chromeH));
      if(slot.splitH!=null)localStorage.setItem(liveLayoutKey('catalog-search-split-h-'),String(slot.splitH));
      if(slot.splitV!=null)localStorage.setItem(liveLayoutKey('catalog-search-split-v-'),String(slot.splitV));
      if(slot.acH!=null)localStorage.setItem(liveLayoutKey('catalog-search-ac-height-'),String(slot.acH));
      if(slot.kwH!=null)localStorage.setItem(liveLayoutKey('catalog-keywords-shade-height-'),String(slot.kwH));
    }
  }catch(err){}
  document.body.classList.toggle('mode-layout-pinned',!!slot.pinned||(mode==='sides'&&!!sidesPinned));
  var pin=document.getElementById('modePinBtn');
  if(pin)pin.setAttribute('aria-pressed',(slot.pinned||(mode==='sides'&&sidesPinned))?'true':'false');
}
function applyFsChromeSize(){
  var hdr=document.querySelector('.catalog-header');
  if(hdr)document.documentElement.style.setProperty('--cat-header-h',Math.round(hdr.getBoundingClientRect().bottom)+'px');
  var root=document.documentElement;
  if(!document.body.classList.contains('display-fs')){
    root.style.removeProperty('--fs-ac-h');
    root.style.removeProperty('--fs-kw-h');
    return;
  }
  var slot=readModeSlot('fs');
  var top=hdr?hdr.getBoundingClientRect().bottom:56;
  var avail=Math.max(160,(window.innerHeight||800)-top);
  function px(frac){
    var n=parseFloat(frac);
    if(!isFinite(n))return avail;
    if(n>0&&n<=1)return Math.max(160,Math.min(avail,Math.round(n*avail)));
    return Math.max(160,Math.min(avail,Math.round(n)));
  }
  root.style.setProperty('--fs-ac-h',px(slot.acH||1)+'px');
  root.style.setProperty('--fs-kw-h',px(slot.kwH||1)+'px');
}
function ensureLayoutChromeBtns(){
  var top=document.getElementById('filterTop');
  if(!top)return;
  var edit=document.getElementById('layoutEditBtn');
  if(edit&&!top.contains(edit))top.appendChild(edit);
  if(!document.getElementById('modePinBtn')){
    var b=document.createElement('button');
    b.type='button';
    b.id='modePinBtn';
    b.className='layout-edit-btn mode-pin-btn';
    b.title='Lock this display-mode size';
    b.setAttribute('aria-label','Lock this display-mode size');
    b.textContent='📌';
    b.addEventListener('click',function(e){
      e.preventDefault();e.stopPropagation();
      var on=!modeLayoutPinned();
      writeModeSlot({pinned:on});
      if(displayModeSlot()==='sides'){
        sidesPinned=on;
        try{localStorage.setItem(SIDES_KEY+'-pin',on?'1':'0');}catch(err){}
        if(typeof syncSidesPin==='function')syncSidesPin();
      }
      document.body.classList.toggle('mode-layout-pinned',on);
      b.setAttribute('aria-pressed',on?'true':'false');
      if(typeof logLayoutModes==='function')logLayoutModes('mode-pin');
    });
    top.appendChild(b);
  }
}
function bindFsModeHandles(){
  function start(e,which){
    if(!document.body.classList.contains('display-fs'))return;
    if(!document.body.classList.contains('layout-edit'))return;
    if(modeLayoutPinned())return;
    if(e.button!=null&&e.button!==0)return;
    e.preventDefault();e.stopPropagation();
    var hdr=document.querySelector('.catalog-header');
    var top=hdr?hdr.getBoundingClientRect().bottom:56;
    var avail=Math.max(160,(window.innerHeight||800)-top);
    var cur=parseInt(getComputedStyle(document.documentElement).getPropertyValue(which==='ac'?'--fs-ac-h':'--fs-kw-h'),10)||avail;
    var drag={which:which,y:e.clientY,h:cur,avail:avail,id:e.pointerId};
    function move(ev){
      if(!drag)return;
      var h=Math.max(160,Math.min(drag.avail,drag.h+(ev.clientY-drag.y)));
      document.documentElement.style.setProperty(drag.which==='ac'?'--fs-ac-h':'--fs-kw-h',h+'px');
    }
    function up(){
      if(!drag)return;
      var h=parseInt(getComputedStyle(document.documentElement).getPropertyValue(drag.which==='ac'?'--fs-ac-h':'--fs-kw-h'),10)||0;
      var patch={};
      if(drag.which==='ac')patch.acH=String(h/drag.avail);
      else patch.kwH=String(h/drag.avail);
      writeModeSlot(patch,'fs');
      drag=null;
      document.removeEventListener('pointermove',move);
      document.removeEventListener('pointerup',up);
      if(typeof logLayoutModes==='function')logLayoutModes('fs-resize');
    }
    document.addEventListener('pointermove',move);
    document.addEventListener('pointerup',up);
    try{e.currentTarget.setPointerCapture(e.pointerId);}catch(err){}
  }
  var ac=document.getElementById('acHeight');
  var kw=document.getElementById('kwShadeHeight');
  if(ac&&!ac.dataset.fsModeBound){ac.dataset.fsModeBound='1';ac.addEventListener('pointerdown',function(e){if(document.body.classList.contains('display-fs'))start(e,'ac');});}
  if(kw&&!kw.dataset.fsModeBound){kw.dataset.fsModeBound='1';kw.addEventListener('pointerdown',function(e){if(document.body.classList.contains('display-fs'))start(e,'kw');});}
}
function logLayoutModes(tag){
  // #region agent log
  try{
    function vis(id){
      var el=document.getElementById(id);
      if(!el)return {id:id,missing:true};
      var s=getComputedStyle(el);
      var b=el.getBoundingClientRect();
      return {id:id,disp:s.display,vis:s.visibility,w:Math.round(b.width),h:Math.round(b.height),parent:el.parentElement?(el.parentElement.id||el.parentElement.tagName):''};
    }
    var keys={};
    try{
      keys.modeStore=localStorage.getItem(MODE_LAYOUT_KEY);
      keys.sides=localStorage.getItem(SIDES_KEY);
      keys.ac=localStorage.getItem(liveLayoutKey('catalog-search-ac-height-'));
      keys.sh=localStorage.getItem(liveLayoutKey('catalog-keywords-shade-height-'));
      keys.ht=localStorage.getItem(liveLayoutKey('catalog-search-height-')+'-l');
    }catch(err){}
    var d={
      tag:tag,
      currentDisplay:typeof currentDisplay!=='undefined'?currentDisplay:'',
      desk:typeof displayIsDesktop==='function'?displayIsDesktop():null,
      fw:vis('filterWrap'),ch:vis('searchChrome'),sh:vis('acShell'),
      split:vis('searchSplit'),sep:vis('dualFsSep'),
      acH:vis('acHeight'),kwH:vis('kwShadeHeight'),searchH:vis('searchHeight'),
      hide:vis('searchStrip'),fs:vis('searchStripFs'),kwfs:vis('kwStripFs'),
      companion:vis('acCompanionBtn'),kwComp:vis('kwCompanionBtn'),
      edit:vis('layoutEditBtn'),pin:vis('dualFsSepPin'),modePin:vis('modePinBtn'),
      tap:vis('tapAddBtnPanel'),ix:vis('catalogIndex'),
      keys:keys,
      pinned:typeof modeLayoutPinned==='function'?modeLayoutPinned():null
    };
    fetch('""" + INGEST + """',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'f491c2'},body:JSON.stringify({sessionId:'f491c2',runId:'layout-modes',hypothesisId:'H1',location:'logLayoutModes',message:'layout-modes',data:d,timestamp:Date.now()})}).catch(function(){});
  }catch(err){}
  // #endregion
}
window.readModeSlot=readModeSlot;
window.writeModeSlot=writeModeSlot;
window.applyModeSlot=applyModeSlot;
window.snapshotLiveToMode=snapshotLiveToMode;
window.logLayoutModes=logLayoutModes;
"""

add(
    "var SIDES_KEY='catalog-sides-cols-'+(window.CATALOG_NS||'catalog');\n"
    "var sidesPinned=false;\n"
    "try{sidesPinned=localStorage.getItem(SIDES_KEY+'-pin')==='1';}catch(err){}\n",
    "var SIDES_KEY='catalog-sides-cols-'+(window.CATALOG_NS||'catalog');\n"
    "var sidesPinned=false;\n"
    "try{sidesPinned=localStorage.getItem(SIDES_KEY+'-pin')==='1';}catch(err){}\n"
    + MODE_JS,
    "mode-store",
)

add(
    "  currentDisplay=mode;\n  try{localStorage.setItem(DISPLAY_KEY,mode);}catch(err){}\n",
    "  var prev=typeof currentDisplay!=='undefined'?currentDisplay:'';\n"
    "  if(prev&&prev!==mode&&typeof snapshotLiveToMode==='function')snapshotLiveToMode(prev);\n"
    "  currentDisplay=mode;\n  try{localStorage.setItem(DISPLAY_KEY,mode);}catch(err){}\n",
    "setDisplay-snap",
)

add(
    "  ensureCatalogMain();\n  placeMenusForDisplay(mode);\n",
    "  ensureCatalogMain();\n  placeMenusForDisplay(mode);\n"
    "  if(typeof ensureLayoutChromeBtns==='function')ensureLayoutChromeBtns();\n"
    "  if(typeof bindFsModeHandles==='function')bindFsModeHandles();\n"
    "  if(typeof applyModeSlot==='function')applyModeSlot(mode);\n",
    "setDisplay-apply",
)

add(
    "  if(typeof applySidesCols==='function')applySidesCols();\n  syncDisplayBtns();\n",
    "  if(typeof applySidesCols==='function')applySidesCols();\n"
    "  if(typeof applyAll==='function')applyAll();\n"
    "  if(typeof applyFsChromeSize==='function')applyFsChromeSize();\n"
    "  syncDisplayBtns();\n"
    "  if(typeof logLayoutModes==='function')logLayoutModes('setDisplayMode');\n",
    "setDisplay-log",
)

# Sides pin also writes mode slot
add(
    "    sidesPinned=!sidesPinned;\n"
    "    try{localStorage.setItem(SIDES_KEY+'-pin',sidesPinned?'1':'0');}catch(err){}\n"
    "    syncSidesPin();\n",
    "    sidesPinned=!sidesPinned;\n"
    "    try{localStorage.setItem(SIDES_KEY+'-pin',sidesPinned?'1':'0');}catch(err){}\n"
    "    if(typeof writeModeSlot==='function')writeModeSlot({pinned:!!sidesPinned},'sides');\n"
    "    syncSidesPin();\n",
    "sides-pin-slot",
    optional=True,
)


def must_replace(text, old, new, label, optional=False):
    if old not in text:
        if new in text or (optional and old not in text):
            print(f"  skip {label} (already or optional-missing)")
            return text
        raise SystemExit(f"MISSING [{label}]")
    n = text.count(old)
    if n != 1:
        # allow identical CSS in builder+comments? builders should be 1
        print(f"  warn {label} count={n}, replacing all")
    return text.replace(old, new)


def patch_text(text, name):
    for old, new, label, optional in REPLACEMENTS:
        text = must_replace(text, old, new, f"{name}:{label}", optional=optional)
    if "</html>" not in text and name.endswith(".html"):
        raise SystemExit(f"TRUNCATED {name}: missing </html>")
    if name.endswith(".html") and "function hideSearchAc" not in text:
        raise SystemExit(f"TRUNCATED {name}: missing hideSearchAc")
    if "function hideSearchAc" not in text and name.endswith(".sh"):
        raise SystemExit(f"TRUNCATED {name}: missing hideSearchAc")
    if "catalog-layout-" not in text:
        raise SystemExit(f"MISSING mode store in {name}")
    if "function placeMenusForDisplay" not in text:
        raise SystemExit(f"MISSING placeMenus in {name}")
    return text


def main():
    for name in ("build-ds-catalog-html.sh", "build-kontakt-catalog-html.sh"):
        src = KIRO / name
        raw = src.read_text(encoding="utf-8")
        out = patch_text(raw, name)
        src.write_text(out, encoding="utf-8")
        print(f"patched KIRO {name} bytes={len(out)}")
        shutil.copy2(src, WS / name)
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
        if not path.exists():
            print(f"skip missing {path}")
            continue
        raw = path.read_text(encoding="utf-8")
        out = patch_text(raw, path.name)
        path.write_text(out, encoding="utf-8")
        print(f"patched {path.name} bytes={len(out)}")


if __name__ == "__main__":
    main()
