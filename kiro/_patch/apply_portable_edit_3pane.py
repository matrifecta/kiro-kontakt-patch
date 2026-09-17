#!/usr/bin/env python3
"""Portable Customize: hittable live seps; 3-pane when both menus; vars actually resize."""
from __future__ import annotations

import os
import tempfile
from pathlib import Path

ROOT = Path("/home/phnx/kiro-kontakt-patch/public/catalogs")
FILES = [
    ROOT / "KONTAKT-CATALOG-portable.html",
    ROOT / "DS-CATALOG-portable.html",
]

CSS_MARK = "</style></head>"
CSS_ADD = r"""
/* fix-PORTABLE-EDIT-3PANE: Customize 3-pane + live seps above overlays; vars drive grid */
html body.catalog-portable.layout-edit #searchSplit.port-stripe-v,
html body.catalog-portable.layout-edit #dualFsSep.port-stripe-v,
html body.catalog-portable.display-sides.layout-edit #searchSplit.port-stripe-v,
html body.catalog-portable.display-sides.layout-edit #dualFsSep.port-stripe-v,
html body.catalog-portable.display-sides.display-middle.layout-edit #searchSplit.port-stripe-v,
html body.catalog-portable.display-sides.display-middle.layout-edit #dualFsSep.port-stripe-v{
  display:block!important;visibility:visible!important;pointer-events:auto!important;
  position:fixed!important;z-index:360!important;
  width:12px!important;min-width:12px!important;max-width:12px!important;
  height:auto!important;min-height:0!important;max-height:none!important;
  cursor:col-resize!important;touch-action:none!important
}
html body.catalog-portable.layout-edit #searchSplit.port-stripe-h,
html body.catalog-portable.layout-edit #dualFsSep.port-stripe-h,
html body.catalog-portable.display-sides.layout-edit #searchSplit.port-stripe-h,
html body.catalog-portable.display-sides.display-middle.layout-edit #searchSplit.port-stripe-h,
html body.catalog-portable.display-sides.layout-edit #dualFsSep.port-stripe-h,
html body.catalog-portable.display-sides.display-middle.layout-edit #dualFsSep.port-stripe-h{
  display:block!important;visibility:visible!important;pointer-events:auto!important;
  position:fixed!important;z-index:360!important;
  height:12px!important;min-height:12px!important;max-height:12px!important;
  width:var(--port-h-w,100%)!important;min-width:48px!important;max-width:none!important;
  cursor:row-resize!important;touch-action:none!important
}
html body.catalog-portable.layout-edit .filter-wrap,
html body.catalog-portable.layout-edit #filterWrap,
html body.catalog-portable.layout-edit #searchChrome,
html body.catalog-portable.layout-edit.search-mode #searchChrome{
  z-index:6!important
}
html body.catalog-portable.layout-edit.portable-landscape.display-sides:not(.search-chrome-collapsed):not(.ac-fs-open):not(.kw-fs-open):not(.portable-edit-3pane):not(.kw-open),
html body.catalog-portable.layout-edit.portable-landscape.display-sides.kw-chrome-collapsed:not(.search-chrome-collapsed):not(.ac-fs-open):not(.kw-fs-open):not(.portable-edit-3pane),
html body.catalog-portable.layout-edit.portable-landscape.display-sides.display-middle:not(.search-chrome-collapsed):not(.ac-fs-open):not(.kw-fs-open):not(.portable-edit-3pane):not(.kw-open),
html body.catalog-portable.layout-edit.portable-landscape.display-sides.display-middle.kw-chrome-collapsed:not(.search-chrome-collapsed):not(.ac-fs-open):not(.kw-fs-open):not(.portable-edit-3pane){
  grid-template-columns:minmax(96px,var(--portable-lw,42%)) minmax(0,1fr)!important;
  grid-template-rows:auto minmax(0,1fr)!important
}
html body.catalog-portable.layout-edit.portable-landscape.display-sides.sides-portrait-flip:not(.search-chrome-collapsed):not(.ac-fs-open):not(.kw-fs-open):not(.portable-edit-3pane):not(.kw-open),
html body.catalog-portable.layout-edit.portable-landscape.display-sides.sides-portrait-flip.kw-chrome-collapsed:not(.search-chrome-collapsed):not(.ac-fs-open):not(.kw-fs-open):not(.portable-edit-3pane){
  grid-template-columns:minmax(0,1fr) minmax(96px,var(--portable-lw,42%))!important
}
html body.catalog-portable.layout-edit.portable-landscape.display-sides.search-chrome-collapsed.kw-open:not(.kw-chrome-collapsed):not(.ac-fs-open):not(.kw-fs-open):not(.portable-edit-3pane),
html body.catalog-portable.layout-edit.portable-landscape.display-sides.display-middle.search-chrome-collapsed.kw-open:not(.kw-chrome-collapsed):not(.ac-fs-open):not(.kw-fs-open):not(.portable-edit-3pane){
  grid-template-columns:minmax(0,1fr) minmax(96px,var(--portable-rw,42%))!important;
  grid-template-rows:auto minmax(0,1fr)!important
}
html body.catalog-portable.layout-edit.portable-landscape.display-sides.sides-portrait-flip.search-chrome-collapsed.kw-open:not(.kw-chrome-collapsed):not(.ac-fs-open):not(.kw-fs-open):not(.portable-edit-3pane){
  grid-template-columns:minmax(96px,var(--portable-rw,42%)) minmax(0,1fr)!important
}
html body.catalog-portable.layout-edit:not(.portable-edit-3pane).portable-sk-pair,
html body.catalog-portable.layout-edit:not(.portable-edit-3pane).portable-landscape.portable-sk-pair,
html body.catalog-portable.layout-edit:not(.portable-edit-3pane).portable-landscape.display-sides.kw-open:not(.kw-chrome-collapsed):not(.search-chrome-collapsed):not(.ac-fs-open):not(.kw-fs-open),
html body.catalog-portable.layout-edit:not(.portable-edit-3pane).portable-landscape.display-sides.display-middle.kw-open:not(.kw-chrome-collapsed):not(.search-chrome-collapsed):not(.ac-fs-open):not(.kw-fs-open){
  grid-template-columns:minmax(96px,var(--portable-lw,50%)) minmax(96px,1fr)!important
}
html body.catalog-portable.layout-edit.portable-edit-3pane.portable-landscape,
html body.catalog-portable.layout-edit.portable-edit-3pane.portable-landscape.display-sides,
html body.catalog-portable.layout-edit.portable-edit-3pane.portable-landscape.display-sides.display-middle,
html body.catalog-portable.layout-edit.portable-edit-3pane.portable-landscape.portable-sk-pair,
html body.catalog-portable.layout-edit.portable-edit-3pane.portable-sk-pair{
  display:grid!important;flex-direction:unset!important;
  grid-template-columns:minmax(96px,var(--portable-lw,28%)) minmax(0,1fr) minmax(96px,var(--portable-rw,28%))!important;
  grid-template-rows:auto minmax(0,1fr)!important
}
html body.catalog-portable.layout-edit.portable-edit-3pane.portable-landscape.sides-portrait-flip,
html body.catalog-portable.layout-edit.portable-edit-3pane.portable-landscape.display-sides.sides-portrait-flip,
html body.catalog-portable.layout-edit.portable-edit-3pane.portable-landscape.portable-sk-pair.sides-portrait-flip{
  grid-template-columns:minmax(96px,var(--portable-rw,28%)) minmax(0,1fr) minmax(96px,var(--portable-lw,28%))!important
}
html body.catalog-portable.layout-edit.portable-edit-3pane.portable-landscape #searchChrome,
html body.catalog-portable.layout-edit.portable-edit-3pane.portable-landscape.display-sides #searchChrome,
html body.catalog-portable.layout-edit.portable-edit-3pane.portable-landscape.display-sides.display-middle #searchChrome,
html body.catalog-portable.layout-edit.portable-edit-3pane.portable-sk-pair #searchChrome{
  grid-column:1!important;grid-row:2!important;display:flex!important;
  width:auto!important;height:auto!important;max-height:none!important;min-height:0!important;
  flex:unset!important;position:relative!important;inset:auto!important;z-index:6!important
}
html body.catalog-portable.layout-edit.portable-edit-3pane.portable-landscape.sides-portrait-flip #searchChrome,
html body.catalog-portable.layout-edit.portable-edit-3pane.portable-sk-pair.sides-portrait-flip #searchChrome{
  grid-column:3!important
}
html body.catalog-portable.layout-edit.portable-edit-3pane.portable-landscape #filterWrap,
html body.catalog-portable.layout-edit.portable-edit-3pane.portable-landscape.display-sides #filterWrap,
html body.catalog-portable.layout-edit.portable-edit-3pane.portable-landscape.display-sides.display-middle #filterWrap,
html body.catalog-portable.layout-edit.portable-edit-3pane.portable-sk-pair #filterWrap{
  grid-column:3!important;grid-row:2!important;display:flex!important;
  position:relative!important;inset:auto!important;transform:none!important;
  width:auto!important;max-width:none!important;height:auto!important;max-height:none!important;
  min-height:0!important;flex:unset!important;z-index:6!important
}
html body.catalog-portable.layout-edit.portable-edit-3pane.portable-landscape.sides-portrait-flip #filterWrap,
html body.catalog-portable.layout-edit.portable-edit-3pane.portable-sk-pair.sides-portrait-flip #filterWrap{
  grid-column:1!important
}
html body.catalog-portable.layout-edit.portable-edit-3pane #catalogMain,
html body.catalog-portable.layout-edit.portable-edit-3pane.portable-sk-pair #catalogMain,
html body.catalog-portable.layout-edit.portable-edit-3pane.portable-sk-pair.index-window-open #catalogMain,
html body.catalog-portable.layout-edit.portable-edit-3pane.portable-landscape #catalogMain,
html body.catalog-portable.layout-edit.portable-edit-3pane.portable-landscape.display-sides.kw-open:not(.kw-chrome-collapsed):not(.search-chrome-collapsed) #catalogMain,
html body.catalog-portable.layout-edit.portable-edit-3pane.portable-landscape.display-sides.index-window-open.kw-open:not(.kw-chrome-collapsed):not(.search-chrome-collapsed) #catalogMain{
  display:block!important;visibility:visible!important;pointer-events:auto!important;
  width:auto!important;min-width:0!important;max-width:none!important;
  height:auto!important;min-height:0!important;overflow:auto!important;
  grid-column:2!important;grid-row:2!important;flex:unset!important
}
html body.catalog-portable.layout-edit.portable-edit-3pane.portable-portrait,
html body.catalog-portable.layout-edit.portable-edit-3pane.portable-portrait.display-sides,
html body.catalog-portable.layout-edit.portable-edit-3pane.portable-portrait.display-sides.display-middle,
html body.catalog-portable.layout-edit.portable-edit-3pane.portable-portrait.display-middle{
  display:grid!important;flex-direction:unset!important;
  grid-template-columns:minmax(96px,var(--portable-lw,42%)) minmax(0,1fr)!important;
  grid-template-rows:auto minmax(72px,var(--portable-menu-h,36%)) minmax(0,1fr)!important
}
html body.catalog-portable.layout-edit.portable-edit-3pane.portable-portrait.sides-portrait-flip{
  grid-template-columns:minmax(0,1fr) minmax(96px,var(--portable-lw,42%))!important
}
html body.catalog-portable.layout-edit.portable-edit-3pane.portable-portrait #searchChrome,
html body.catalog-portable.layout-edit.portable-edit-3pane.portable-portrait.display-middle #searchChrome{
  grid-column:1!important;grid-row:2!important;display:flex!important;
  width:auto!important;height:100%!important;max-height:none!important;min-height:0!important;
  flex:unset!important;z-index:6!important
}
html body.catalog-portable.layout-edit.portable-edit-3pane.portable-portrait #filterWrap,
html body.catalog-portable.layout-edit.portable-edit-3pane.portable-portrait.display-middle #filterWrap{
  grid-column:1!important;grid-row:3!important;display:flex!important;
  width:auto!important;height:100%!important;max-height:none!important;min-height:0!important;
  position:relative!important;inset:auto!important;flex:unset!important;z-index:6!important
}
html body.catalog-portable.layout-edit.portable-edit-3pane.portable-portrait #catalogMain,
html body.catalog-portable.layout-edit.portable-edit-3pane.portable-portrait.display-middle #catalogMain{
  display:block!important;visibility:visible!important;
  grid-column:2!important;grid-row:2/-1!important;min-height:0!important
}
html body.catalog-portable.layout-edit.portable-edit-3pane.portable-portrait.sides-portrait-flip #searchChrome,
html body.catalog-portable.layout-edit.portable-edit-3pane.portable-portrait.sides-portrait-flip #filterWrap{
  grid-column:2!important
}
html body.catalog-portable.layout-edit.portable-edit-3pane.portable-portrait.sides-portrait-flip #catalogMain{
  grid-column:1!important
}
html body.catalog-portable.layout-edit.display-sides.display-middle:not(.portable-edit-3pane):not(.ac-fs-open):not(.kw-fs-open):not(.search-chrome-collapsed) #searchChrome,
html body.catalog-portable.layout-edit.display-sides.display-middle:not(.portable-edit-3pane).search-chrome-collapsed.kw-open:not(.kw-chrome-collapsed):not(.kw-fs-open) #filterWrap,
html body.catalog-portable.layout-edit.portable-portrait.display-sides.display-middle:not(.portable-edit-3pane):not(.search-chrome-collapsed) #searchChrome,
html body.catalog-portable.layout-edit.portable-portrait.display-sides.display-middle:not(.portable-edit-3pane).search-chrome-collapsed.kw-open:not(.kw-chrome-collapsed) #filterWrap{
  height:var(--portable-menu-h,min(44dvh,22rem))!important;
  max-height:min(70dvh,36rem)!important;min-height:96px!important;
  flex:0 0 auto!important;z-index:6!important
}
html body.catalog-portable.layout-edit.ac-fs-open:not(.kw-fs-open) #searchSplit,
html body.catalog-portable.layout-edit.ac-fs-open:not(.kw-fs-open) #dualFsSep,
html body.catalog-portable.layout-edit.kw-fs-open:not(.ac-fs-open) #searchSplit,
html body.catalog-portable.layout-edit.kw-fs-open:not(.ac-fs-open) #dualFsSep{
  display:none!important;pointer-events:none!important;visibility:hidden!important
}
html body.catalog-portable.mode-layout-pinned.layout-edit #searchSplit,
html body.catalog-portable.mode-layout-pinned.layout-edit #dualFsSep,
html body.catalog-portable.sides-pinned.layout-edit #searchSplit,
html body.catalog-portable.sides-pinned.layout-edit #dualFsSep{
  cursor:default!important;pointer-events:none!important
}
"""

PLACE_OLD = """  var placed=false;
  if(dual&&vis(ch)&&vis(fw)){
    var leftDual=flip?fw:ch;
    placed=bar(split,true,{x:leftDual.getBoundingClientRect().right},'--portable-lw','right');
  }else if(middle||(portrait&&sides&&!document.body.classList.contains('portable-landscape'))){
    if(m.searchOn&&vis(ch)){
      var rs=ch.getBoundingClientRect();
      placed=bar(split,false,{x:rs.left,w:rs.width,y:rs.bottom},'--portable-menu-h','down');
    }else if(m.kwOn&&vis(fw)){
      var rk=fw.getBoundingClientRect();
      placed=bar(sep,false,{x:rk.left,w:rk.width,y:rk.bottom},'--portable-menu-h','down');
    }
  }else if(sides){
    if(m.both&&vis(ch)&&vis(fw)){
      var lp=flip?fw:ch;
      placed=bar(split,true,{x:lp.getBoundingClientRect().right},'--portable-lw','right');
    }else if(m.searchOn&&vis(ch)){
      var rc=ch.getBoundingClientRect();
      placed=bar(split,true,{x:flip?rc.left:rc.right},'--portable-lw',flip?'left':'right');
    }else if(m.kwOn&&vis(fw)){
      var rf=fw.getBoundingClientRect();
      placed=bar(sep,true,{x:flip?rf.right:rf.left},'--portable-rw',flip?'right':'left');
    }
  }"""

PLACE_NEW = """  var placed=false;
  var land=document.body.classList.contains('portable-landscape')||(!portrait&&!document.body.classList.contains('portable-portrait'));
  var edit3=edit&&m.both&&vis(ch)&&vis(fw)&&!oneFs&&!dual;
  if(dual&&vis(ch)&&vis(fw)){
    var leftDual=flip?fw:ch;
    placed=bar(split,true,{x:leftDual.getBoundingClientRect().right},'--portable-lw','right');
  }else if(edit3&&land){
    var rc3=ch.getBoundingClientRect();
    var rf3=fw.getBoundingClientRect();
    var a=bar(split,true,{x:flip?rc3.left:rc3.right},'--portable-lw',flip?'left':'right');
    var b=bar(sep,true,{x:flip?rf3.right:rf3.left},'--portable-rw',flip?'right':'left');
    placed=a||b;
  }else if(edit3&&!land){
    var rs3=ch.getBoundingClientRect();
    var rk3=fw.getBoundingClientRect();
    var stackR=flip?rk3:rs3;
    var aH=bar(split,false,{x:rs3.left,w:rs3.width,y:rs3.bottom},'--portable-menu-h','down');
    var bV=bar(sep,true,{x:flip?stackR.left:stackR.right},'--portable-lw',flip?'left':'right');
    placed=aH||bV;
  }else if(middle||(portrait&&sides&&!land)){
    if(m.searchOn&&vis(ch)){
      var rs=ch.getBoundingClientRect();
      placed=bar(split,false,{x:rs.left,w:rs.width,y:rs.bottom},'--portable-menu-h','down');
    }else if(m.kwOn&&vis(fw)){
      var rk=fw.getBoundingClientRect();
      placed=bar(sep,false,{x:rk.left,w:rk.width,y:rk.bottom},'--portable-menu-h','down');
    }
  }else if(sides){
    if(m.searchOn&&vis(ch)){
      var rc=ch.getBoundingClientRect();
      placed=bar(split,true,{x:flip?rc.left:rc.right},'--portable-lw',flip?'left':'right');
    }else if(m.kwOn&&vis(fw)){
      var rf=fw.getBoundingClientRect();
      placed=bar(sep,true,{x:flip?rf.right:rf.left},'--portable-rw',flip?'right':'left');
    }
  }"""

BAR_OLD = """    var half=4;
    el.style.cssText='';
    el.style.setProperty('position','fixed','important');
    el.style.setProperty('margin','0','important');
    el.style.setProperty('transform','none','important');
    el.style.setProperty('pointer-events','auto','important');
    el.style.setProperty('z-index','160','important');"""

BAR_NEW = """    var half=6;
    el.style.cssText='';
    el.style.setProperty('position','fixed','important');
    el.style.setProperty('margin','0','important');
    el.style.setProperty('transform','none','important');
    el.style.setProperty('pointer-events','auto','important');
    el.style.setProperty('z-index','360','important');"""

PX_OLD = """      el.style.setProperty('width','8px','important');
      el.style.setProperty('min-width','8px','important');
      el.style.setProperty('max-width','8px','important');"""

PX_NEW = """      el.style.setProperty('width','12px','important');
      el.style.setProperty('min-width','12px','important');
      el.style.setProperty('max-width','12px','important');"""

H_OLD = """      el.style.setProperty('height','8px','important');
      el.style.setProperty('min-height','8px','important');
      el.style.setProperty('max-height','8px','important');"""

H_NEW = """      el.style.setProperty('height','12px','important');
      el.style.setProperty('min-height','12px','important');
      el.style.setProperty('max-height','12px','important');"""

IXH_OLD = """    ixH.style.setProperty('height',showIx?'8px':'0','important');
    ixH.style.setProperty('min-height',showIx?'8px':'0','important');"""

IXH_NEW = """    ixH.style.setProperty('height',showIx?'12px':'0','important');
    ixH.style.setProperty('min-height',showIx?'12px':'0','important');
    if(showIx)ixH.style.setProperty('z-index','24','important');"""

PAIR_OLD = """  var pair=!!(sides&&!middle&&!fs&&searchOn&&kwOn);
  var flipOn=!!(sides&&!middle&&!content&&!document.body.classList.contains('display-fs')&&(searchOn||kwOn));
  document.body.classList.toggle('portable-portrait',o==='portrait');
  document.body.classList.toggle('portable-landscape',o==='landscape');
  document.body.classList.toggle('portable-kb-open',!!kb);
  document.body.classList.toggle('portable-sk-pair',pair);
  document.body.classList.toggle('portable-flip-on',flipOn);"""

PAIR_NEW = """  var editOn=document.body.classList.contains('layout-edit');
  var pair=!!(sides&&!middle&&!fs&&searchOn&&kwOn&&!editOn);
  var edit3=!!(editOn&&searchOn&&kwOn&&!fs&&!document.body.classList.contains('ac-fs-open')&&!document.body.classList.contains('kw-fs-open')&&(sides||middle));
  var flipOn=!!(((sides&&!middle)||edit3)&&!content&&!document.body.classList.contains('display-fs')&&(searchOn||kwOn));
  document.body.classList.toggle('portable-portrait',o==='portrait');
  document.body.classList.toggle('portable-landscape',o==='landscape');
  document.body.classList.toggle('portable-kb-open',!!kb);
  document.body.classList.toggle('portable-sk-pair',pair);
  document.body.classList.toggle('portable-edit-3pane',edit3);
  document.body.classList.toggle('portable-flip-on',flipOn);"""

TOGGLE_OLD = """function toggleLayoutEdit(){
  var was=document.body.classList.contains('layout-edit');
  document.body.classList.toggle('layout-edit');
  if(was&&typeof persistAllLiveLayouts==='function')persistAllLiveLayouts();
  syncLayoutEditBtn();"""

TOGGLE_NEW = """function toggleLayoutEdit(){
  var was=document.body.classList.contains('layout-edit');
  document.body.classList.toggle('layout-edit');
  if(was&&typeof persistAllLiveLayouts==='function')persistAllLiveLayouts();
  if(window.CATALOG_PORTABLE){
    var onNow=document.body.classList.contains('layout-edit');
    if(!onNow&&document.body.classList.contains('display-middle')){
      var fwE=document.getElementById('filterWrap');
      var bothE=!document.body.classList.contains('search-chrome-collapsed')&&!document.body.classList.contains('kw-chrome-collapsed')&&!!(fwE&&fwE.classList.contains('open')&&document.body.classList.contains('kw-open'));
      if(bothE&&typeof portableCoerceMiddleMenu==='function')portableCoerceMiddleMenu(typeof portableMiddleLast==='string'&&portableMiddleLast?portableMiddleLast:'search');
    }
    if(typeof syncPortableLayoutChrome==='function')syncPortableLayoutChrome();
  }
  syncLayoutEditBtn();"""

PANE_OLD = """      var paneP=axisP==='h'?(mP.kwOn&&!mP.searchOn?fwP:chP):(propP==='--portable-rw'?fwP:(mP.both&&flipP?fwP:(mP.searchOn?chP:fwP)));"""

PANE_NEW = """      var paneP=axisP==='h'?(mP.kwOn&&!mP.searchOn?fwP:chP):(propP==='--portable-rw'?fwP:(document.body.classList.contains('portable-edit-3pane')?chP:(mP.both&&flipP?fwP:(mP.searchOn?chP:fwP))));"""

MOVE_OLD = """      if(drag.horiz||drag.axis==='h'){
        var nh=Math.max(96,Math.min(Math.round(vhP*0.62),drag.h+(e.clientY-drag.y)));
        document.documentElement.style.setProperty('--portable-menu-h',nh+'px');
      }else{
        var dx=e.clientX-drag.x;
        var nl=drag.grow==='left'?drag.w-dx:drag.w+dx;
        nl=Math.max(120,Math.min(Math.round(vwP*0.78),nl));
        document.documentElement.style.setProperty(drag.prop||'--portable-lw',nl+'px');
      }"""

MOVE_NEW = """      if(drag.horiz||drag.axis==='h'){
        var nh=Math.max(96,Math.min(Math.round(vhP*0.70),drag.h+(e.clientY-drag.y)));
        document.documentElement.style.setProperty('--portable-menu-h',nh+'px');
        document.documentElement.style.setProperty('--middle-menu-h',nh+'px');
      }else{
        var dx=e.clientX-drag.x;
        var nl=drag.grow==='left'?drag.w-dx:drag.w+dx;
        var cap=Math.round(vwP*0.78);
        if(document.body.classList.contains('portable-edit-3pane')&&document.body.classList.contains('portable-landscape')){
          var otherP=drag.prop==='--portable-rw'?'--portable-lw':'--portable-rw';
          var other=parseInt(getComputedStyle(document.documentElement).getPropertyValue(otherP),10)||120;
          cap=Math.min(cap,Math.max(96,vwP-other-72));
        }else if(document.body.classList.contains('portable-edit-3pane')){
          cap=Math.min(cap,Math.round(vwP*0.58));
        }
        nl=Math.max(96,Math.min(cap,nl));
        document.documentElement.style.setProperty(drag.prop||'--portable-lw',nl+'px');
      }"""

COERCE_OLD = """  if(document.body.classList.contains('display-middle')&&which&&typeof portableCoerceMiddleMenu==='function'){
    portableCoerceMiddleMenu(which==='keywords'?'keywords':'search');
  }"""

COERCE_NEW = """  if(document.body.classList.contains('display-middle')&&which&&typeof portableCoerceMiddleMenu==='function'&&!document.body.classList.contains('layout-edit')){
    portableCoerceMiddleMenu(which==='keywords'?'keywords':'search');
  }"""

HDR_S_OLD = """  if(window.CATALOG_PORTABLE&&document.body.classList.contains('display-middle')){
    var visS=typeof portableMiddleVisible==='function'?portableMiddleVisible():'';"""

HDR_S_NEW = """  if(window.CATALOG_PORTABLE&&document.body.classList.contains('display-middle')&&!document.body.classList.contains('layout-edit')){
    var visS=typeof portableMiddleVisible==='function'?portableMiddleVisible():'';"""

HDR_K_OLD = """  if(window.CATALOG_PORTABLE&&document.body.classList.contains('display-middle')){
    var visK=typeof portableMiddleVisible==='function'?portableMiddleVisible():'';"""

HDR_K_NEW = """  if(window.CATALOG_PORTABLE&&document.body.classList.contains('display-middle')&&!document.body.classList.contains('layout-edit')){
    var visK=typeof portableMiddleVisible==='function'?portableMiddleVisible():'';"""

HDR_K2_OLD = """  if(window.CATALOG_PORTABLE&&document.body.classList.contains('display-middle')){
    var fwNow=document.getElementById('filterWrap');"""

HDR_K2_NEW = """  if(window.CATALOG_PORTABLE&&document.body.classList.contains('display-middle')&&!document.body.classList.contains('layout-edit')){
    var fwNow=document.getElementById('filterWrap');"""

HDR_S2_OLD = """  if(window.CATALOG_PORTABLE&&document.body.classList.contains('display-middle')&&!document.body.classList.contains('search-chrome-collapsed')&&typeof portableCoerceMiddleMenu==='function')portableCoerceMiddleMenu('search');"""

HDR_S2_NEW = """  if(window.CATALOG_PORTABLE&&document.body.classList.contains('display-middle')&&!document.body.classList.contains('layout-edit')&&!document.body.classList.contains('search-chrome-collapsed')&&typeof portableCoerceMiddleMenu==='function')portableCoerceMiddleMenu('search');"""

LOG_OLD = """data:{placed:!!placed,searchOn:!!m.searchOn,kwOn:!!m.kwOn,sides:sides,middle:middle,dual:!!dual,oneFs:oneFs||'',portrait:portrait,flip:flip,edit:true,"""

LOG_NEW = """data:{placed:!!placed,searchOn:!!m.searchOn,kwOn:!!m.kwOn,sides:sides,middle:middle,dual:!!dual,oneFs:oneFs||'',portrait:portrait,flip:flip,edit:true,edit3:!!document.body.classList.contains('portable-edit-3pane'),mainOn:!!(mainEl&&mainEl.getBoundingClientRect().width>8),"""

CHROME_LOG_OLD = """data:{o:o,kb:!!kb,sides:sides,middle:middle,content:content,fs:fs,searchOn:searchOn,kwOn:kwOn,pair:pair,flipOn:flipOn,"""

CHROME_LOG_NEW = """data:{o:o,kb:!!kb,sides:sides,middle:middle,content:content,fs:fs,searchOn:searchOn,kwOn:kwOn,pair:pair,edit3:!!edit3,flipOn:flipOn,"""


def replace_once(text: str, old: str, new: str, label: str) -> str:
    n = text.count(old)
    if n != 1:
        raise SystemExit(f"{label}: expected 1 occurrence, found {n}")
    return text.replace(old, new, 1)


def patch(text: str) -> str:
    text = replace_once(text, BAR_OLD, BAR_NEW, "bar-z")
    text = replace_once(text, PX_OLD, PX_NEW, "bar-w")
    text = replace_once(text, H_OLD, H_NEW, "bar-h")
    text = replace_once(text, IXH_OLD, IXH_NEW, "ixh")
    text = replace_once(text, PLACE_OLD, PLACE_NEW, "place-branch")
    text = replace_once(text, PAIR_OLD, PAIR_NEW, "pair-class")
    text = replace_once(text, TOGGLE_OLD, TOGGLE_NEW, "toggle-edit")
    text = replace_once(text, PANE_OLD, PANE_NEW, "pane-sel")
    text = replace_once(text, MOVE_OLD, MOVE_NEW, "drag-move")
    text = replace_once(text, COERCE_OLD, COERCE_NEW, "coerce-skip")
    text = replace_once(text, HDR_S_OLD, HDR_S_NEW, "hdr-s-mid")
    text = replace_once(text, HDR_K_OLD, HDR_K_NEW, "hdr-k-mid")
    text = replace_once(text, HDR_K2_OLD, HDR_K2_NEW, "hdr-k2")
    text = replace_once(text, HDR_S2_OLD, HDR_S2_NEW, "hdr-s2")
    text = replace_once(text, LOG_OLD, LOG_NEW, "place-log")
    text = replace_once(text, CHROME_LOG_OLD, CHROME_LOG_NEW, "chrome-log")
    if CSS_MARK not in text:
        raise SystemExit("missing </style></head>")
    if "fix-PORTABLE-EDIT-3PANE" not in text:
        text = text.replace(CSS_MARK, CSS_ADD + CSS_MARK, 1)
    return text


def write_safe(path: Path, data: str, before_c00: int) -> None:
    if not data.rstrip().endswith("</html>"):
        raise SystemExit(f"{path.name} rewrite missing </html>")
    if data.count("sessionId:'c00e3e'") < before_c00:
        raise SystemExit(f"{path.name}: lost c00e3e logs")
    fd, tmp = tempfile.mkstemp(prefix=path.stem + ".", suffix=".html", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise
    got = path.stat().st_size
    if got < 100000:
        raise SystemExit(f"{path.name} too small after write: {got}")
    check = path.read_text(encoding="utf-8")
    if not check.rstrip().endswith("</html>"):
        raise SystemExit(f"{path.name} after write missing </html>")
    if "fix-PORTABLE-EDIT-3PANE" not in check:
        raise SystemExit(f"{path.name} missing EDIT-3PANE mark")
    if check.count("function placePortableHandles(){") != 1:
        raise SystemExit(f"{path.name} placePortableHandles count")
    if "portable-edit-3pane" not in check:
        raise SystemExit(f"{path.name} missing 3pane class")
    if "z-index','360'" not in check:
        raise SystemExit(f"{path.name} stripe z-index not 360")


def main() -> None:
    for path in FILES:
        raw = path.read_text(encoding="utf-8")
        before_c00 = raw.count("sessionId:'c00e3e'")
        out = patch(raw)
        write_safe(path, out, before_c00)
        print(
            f"patched {path.name} {len(raw)} -> {len(out)} "
            f"c00={before_c00}->{out.count(chr(39)+'c00e3e'+chr(39))} size={path.stat().st_size}"
        )


if __name__ == "__main__":
    main()
