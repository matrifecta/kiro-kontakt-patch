#!/usr/bin/env python3
"""Jump stack parks above About; layout passes preserve scroll + selected card."""
from __future__ import annotations

import os
import tempfile
from pathlib import Path

ROOT = Path("/home/phnx/kiro-kontakt-patch")
FILES = [
    ROOT / "public/catalogs/KONTAKT-CATALOG.html",
    ROOT / "public/catalogs/DS-CATALOG.html",
    ROOT / "public/catalogs/KONTAKT-CATALOG-portable.html",
    ROOT / "public/catalogs/DS-CATALOG-portable.html",
]

MARK = "fix-CATALOG-SCROLL-JUMP-v1"

SCROLL_HELPERS = """function catalogScrollAnchor(){
  var sc=(typeof catalogContentScroller==='function'&&catalogContentScroller())||(typeof catalogScrollEl==='function'&&catalogScrollEl())||document.getElementById('catalogMain');
  if(!sc)return {sc:null,y0:0,anchor:null,top0:null};
  var y0=sc.scrollTop;
  var anchor=document.querySelector('.entry.selected:not(.highlight)')||(typeof lastViewedEntry!=='undefined'?lastViewedEntry:null);
  if(!anchor){
    var sr=sc.getBoundingClientRect();
    var vis=sc.querySelectorAll('.entry:not(.is-hidden):not(.highlight)');
    for(var i=0;i<vis.length;i++){
      var r=vis[i].getBoundingClientRect();
      if(r.height>16&&r.bottom>sr.top+4&&r.top<sr.bottom-4){anchor=vis[i];break;}
    }
  }
  var top0=anchor?anchor.getBoundingClientRect().top:null;
  return {sc:sc,y0:y0,anchor:anchor,top0:top0};
}
function catalogRestoreScroll(pin){
  if(!pin||!pin.sc)return;
  if(pin.anchor&&pin.top0!=null){
    var t=pin.anchor.getBoundingClientRect().top;
    pin.sc.scrollTop=pin.sc.scrollTop+(t-pin.top0);
  }else pin.sc.scrollTop=pin.y0;
}
function withCatalogScrollPin(fn){
  var pin=catalogScrollAnchor();
  if(pin&&pin.sc)pin.sc.style.setProperty('overflow-anchor','none');
  try{if(typeof fn==='function')fn();}finally{
    catalogRestoreScroll(pin);
    if(pin&&pin.sc){
      requestAnimationFrame(function(){
        catalogRestoreScroll(pin);
        requestAnimationFrame(function(){
          catalogRestoreScroll(pin);
          pin.sc.style.removeProperty('overflow-anchor');
          if(typeof placeCatalogJumpStack==='function')placeCatalogJumpStack();
        });
      });
    }
  }
}
window.catalogScrollAnchor=catalogScrollAnchor;
window.catalogRestoreScroll=catalogRestoreScroll;
window.withCatalogScrollPin=withCatalogScrollPin;
"""

SCROLL_ANCHOR = "window.catalogContentScroller=catalogContentScroller;"

DOC_NOTE_OLD = """function catalogDocNoteInsetBottom(){
  var note=document.getElementById('catalogDocNote');
  if(!note||note.classList.contains('is-embedded'))return 0;
  var cs=getComputedStyle(note);
  if(cs.display==='none'||cs.visibility==='hidden')return 0;
  var nr=note.getBoundingClientRect();
  if(!nr||nr.height<8)return 0;
  return Math.round(nr.height)+8;
}
function placeCatalogJumpStack(){
  var stack=document.getElementById('catalogJumpStack');
  var main=document.getElementById('catalogMain');
  if(!stack)return;
  if(!document.body.classList.contains('display-sides')||!main){
    stack.style.cssText='';
  }else{
    var r=main.getBoundingClientRect();
    var right=Math.max(6,Math.round((window.innerWidth||0)-r.right)+10);
    var bottom=Math.max(6,Math.round((window.innerHeight||0)-r.bottom)+12+(typeof catalogDocNoteInsetBottom==='function'?catalogDocNoteInsetBottom():0));
    stack.style.right=right+'px';
    stack.style.bottom=bottom+'px';
    stack.style.left='auto';
    stack.style.top='auto';
  }
}"""

DOC_NOTE_NEW = """function catalogDocNoteBarRect(){
  var note=document.getElementById('catalogDocNote');
  if(!note)return null;
  var cs=getComputedStyle(note);
  if(cs.display==='none'||cs.visibility==='hidden')return null;
  var r=note.getBoundingClientRect();
  if(!r||r.height<8)return null;
  return r;
}
function catalogDocNoteInsetBottom(){
  var note=document.getElementById('catalogDocNote');
  if(!note||note.classList.contains('is-embedded'))return 0;
  var cs=getComputedStyle(note);
  if(cs.display==='none'||cs.visibility==='hidden')return 0;
  var nr=note.getBoundingClientRect();
  if(!nr||nr.height<8)return 0;
  return Math.round(nr.height)+8;
}
function catalogJumpStackBottomInset(){
  var main=document.getElementById('catalogMain');
  var noteR=typeof catalogDocNoteBarRect==='function'?catalogDocNoteBarRect():null;
  if(!main||!noteR)return typeof catalogDocNoteInsetBottom==='function'?catalogDocNoteInsetBottom():0;
  var mr=main.getBoundingClientRect();
  var note=document.getElementById('catalogDocNote');
  var embedded=!!(note&&note.classList.contains('is-embedded'));
  var gap=10;
  if(noteR.bottom<=mr.top+4||noteR.top>=mr.bottom-4)return 0;
  if(!embedded)return Math.max(0,Math.round(mr.bottom-noteR.top)+gap);
  if(noteR.top<mr.bottom-24)return Math.max(0,Math.round(mr.bottom-noteR.top)+gap);
  return 0;
}
function placeCatalogJumpStack(){
  var stack=document.getElementById('catalogJumpStack');
  var main=document.getElementById('catalogMain');
  if(!stack)return;
  var pane=document.body.classList.contains('display-sides')||document.body.classList.contains('display-middle');
  if(!pane||!main){
    stack.style.cssText='';
    return;
  }
  var r=main.getBoundingClientRect();
  var right=Math.max(6,Math.round((window.innerWidth||0)-r.right)+10);
  var inset=typeof catalogJumpStackBottomInset==='function'?catalogJumpStackBottomInset():0;
  var bottom=Math.max(6,Math.round((window.innerHeight||0)-r.bottom)+12+inset);
  stack.style.right=right+'px';
  stack.style.bottom=bottom+'px';
  stack.style.left='auto';
  stack.style.top='auto';
}
function bindCatalogJumpScroll(){
  var sc=(typeof catalogContentScroller==='function'&&catalogContentScroller())||document.getElementById('catalogMain');
  if(!sc||sc.dataset.jumpScrollBound)return;
  sc.dataset.jumpScrollBound='1';
  sc.addEventListener('scroll',function(){
    if(window._jumpScrollRaf)cancelAnimationFrame(window._jumpScrollRaf);
    window._jumpScrollRaf=requestAnimationFrame(function(){
      window._jumpScrollRaf=0;
      if(typeof placeCatalogJumpStack==='function')placeCatalogJumpStack();
    });
  },{passive:true});
}
window.catalogJumpStackBottomInset=catalogJumpStackBottomInset;
window.bindCatalogJumpScroll=bindCatalogJumpScroll;"""

SYNC_IX_OLD = """function syncIndexWindowDock(){
  var ix=document.getElementById('catalogIndex');
  var windowOk=window.CATALOG_PORTABLE||document.body.classList.contains('display-sides')||document.body.classList.contains('display-middle');
  var on=!!(ix&&!ix.classList.contains('is-embedded')&&windowOk);
  document.body.classList.toggle('index-window-open',on);
  var main=document.getElementById('catalogMain');
  var cb=main&&(main.querySelector(':scope > .catalog-body')||main.querySelector('.catalog-body'));
  if(main){
    main.style.setProperty('overflow-y','hidden','important');
    main.style.setProperty('overflow-x','hidden','important');
    main.scrollTop=0;
    if(cb){
      cb.style.setProperty('overflow-y','auto','important');
      cb.style.setProperty('overflow-x','hidden','important');
      cb.style.setProperty('min-height','0','important');
      cb.style.setProperty('flex','1 1 auto','important');
    }
  }
  if(typeof applyIndexFillDocStyles==='function')applyIndexFillDocStyles();
}"""

SYNC_IX_NEW = """function syncIndexWindowDock(){
  var run=function(){
    var ix=document.getElementById('catalogIndex');
    var windowOk=window.CATALOG_PORTABLE||document.body.classList.contains('display-sides')||document.body.classList.contains('display-middle');
    var on=!!(ix&&!ix.classList.contains('is-embedded')&&windowOk);
    document.body.classList.toggle('index-window-open',on);
    var main=document.getElementById('catalogMain');
    var cb=main&&(main.querySelector(':scope > .catalog-body')||main.querySelector('.catalog-body'));
    if(main){
      main.style.setProperty('overflow-y','hidden','important');
      main.style.setProperty('overflow-x','hidden','important');
      if(cb){
        cb.style.setProperty('overflow-y','auto','important');
        cb.style.setProperty('overflow-x','hidden','important');
        cb.style.setProperty('min-height','0','important');
        cb.style.setProperty('flex','1 1 auto','important');
      }
    }
    if(typeof applyIndexFillDocStyles==='function')applyIndexFillDocStyles();
    if(typeof placeCatalogJumpStack==='function')placeCatalogJumpStack();
  };
  if(typeof withCatalogScrollPin==='function')withCatalogScrollPin(run);
  else run();
}"""

TOGGLE_IX_TAIL_OLD = """  syncIndexEmbedBtn();
  var sc=(typeof catalogContentScroller==='function'&&catalogContentScroller())||document.getElementById('catalogMain');
  if(on&&sc)sc.scrollTop=0;
}"""

TOGGLE_IX_TAIL_NEW = """  syncIndexEmbedBtn();
}"""

TOGGLE_IX_BODY_OLD = """  if(!window.CATALOG_PORTABLE&&!sides&&!middle)return;
  var on=ix.classList.toggle('is-embedded');
  writeIndexEmbedPref(on);
  if(typeof writeModeSlot==='function')writeModeSlot({indexEmbed:on},sides?'sides':(middle?'middle':undefined));
  if(typeof parkCatalogDocNote==='function')parkCatalogDocNote();
  if(typeof applyIndexScrollFit==='function')applyIndexScrollFit();
  if(typeof syncIndexWindowDock==='function')syncIndexWindowDock();
  if(typeof applyIndexFillDocStyles==='function')applyIndexFillDocStyles();
  syncIndexEmbedBtn();
}"""

TOGGLE_IX_BODY_NEW = """  if(!window.CATALOG_PORTABLE&&!sides&&!middle)return;
  var on=ix.classList.toggle('is-embedded');
  var apply=function(){
    writeIndexEmbedPref(on);
    if(typeof writeModeSlot==='function')writeModeSlot({indexEmbed:on},sides?'sides':(middle?'middle':undefined));
    if(typeof parkCatalogDocNote==='function')parkCatalogDocNote();
    if(typeof applyIndexScrollFit==='function')applyIndexScrollFit();
    if(typeof syncIndexWindowDock==='function')syncIndexWindowDock();
    if(typeof applyIndexFillDocStyles==='function')applyIndexFillDocStyles();
    syncIndexEmbedBtn();
  };
  if(typeof withCatalogScrollPin==='function')withCatalogScrollPin(apply);
  else apply();
}"""

HDR_OLD = """function toggleHdrBar(force){
  var hide=(force===true||force===false)?!!force:!document.body.classList.contains('hdr-bar-hidden');
  document.body.classList.toggle('hdr-bar-hidden', hide);
  try{localStorage.setItem(hdrBarPrefKey(), hide?'1':'0');}catch(eHdr){}
  syncHdrBar();
  if(typeof applyFsChromeSize==='function')applyFsChromeSize();
  else updateCatHeaderH();
  if(typeof applyIndexScrollFit==='function')applyIndexScrollFit();
  if(typeof placeMenusForDisplay==='function'){
    var mode=(document.body.className.match(/display-(\\S+)/)||[])[1];
    try{placeMenusForDisplay(mode||'sides');}catch(ePlace){}
  }
}"""

HDR_NEW = """function toggleHdrBar(force){
  var hide=(force===true||force===false)?!!force:!document.body.classList.contains('hdr-bar-hidden');
  var run=function(){
    document.body.classList.toggle('hdr-bar-hidden', hide);
    try{localStorage.setItem(hdrBarPrefKey(), hide?'1':'0');}catch(eHdr){}
    syncHdrBar();
    if(typeof applyFsChromeSize==='function')applyFsChromeSize();
    else updateCatHeaderH();
    if(typeof applyIndexScrollFit==='function')applyIndexScrollFit();
    if(typeof placeMenusForDisplay==='function'){
      var mode=(document.body.className.match(/display-(\\S+)/)||[])[1];
      try{placeMenusForDisplay(mode||'sides');}catch(ePlace){}
    }
    if(typeof placeCatalogJumpStack==='function')placeCatalogJumpStack();
  };
  if(typeof withCatalogScrollPin==='function')withCatalogScrollPin(run);
  else run();
}"""

EQ_START_OLD = """function equalizeCatalogCardRows(){
  var _eqT0=(typeof performance!=='undefined'&&performance.now)?performance.now():Date.now();
  window._eqN=(window._eqN||0)+1;
  var groups=document.querySelectorAll('.loc-group');"""

EQ_START_NEW = """function equalizeCatalogCardRows(){
  var _eqT0=(typeof performance!=='undefined'&&performance.now)?performance.now():Date.now();
  window._eqN=(window._eqN||0)+1;
  var _scrollPin=typeof catalogScrollAnchor==='function'?catalogScrollAnchor():null;
  if(_scrollPin&&_scrollPin.sc)_scrollPin.sc.style.setProperty('overflow-anchor','none');
  var groups=document.querySelectorAll('.loc-group');"""

EQ_END_OLD = """  }catch(eDbgF){}
  // #endregion
}
function scheduleEqualizeCardRows(){"""

EQ_END_NEW = """  }catch(eDbgF){}
  // #endregion
  if(typeof catalogRestoreScroll==='function')catalogRestoreScroll(_scrollPin);
  if(_scrollPin&&_scrollPin.sc){
    requestAnimationFrame(function(){
      catalogRestoreScroll(_scrollPin);
      requestAnimationFrame(function(){
        catalogRestoreScroll(_scrollPin);
        _scrollPin.sc.style.removeProperty('overflow-anchor');
        if(typeof placeCatalogJumpStack==='function')placeCatalogJumpStack();
      });
    });
  }
}
function scheduleEqualizeCardRows(){"""

ENSURE_JUMP_OLD = """  if(typeof placeCatalogJumpStack==='function')placeCatalogJumpStack();
  if(typeof bindCatalogTop==='function')bindCatalogTop();
}"""

ENSURE_JUMP_NEW = """  if(typeof placeCatalogJumpStack==='function')placeCatalogJumpStack();
  if(typeof bindCatalogJumpScroll==='function')bindCatalogJumpScroll();
  if(typeof bindCatalogTop==='function')bindCatalogTop();
}"""

F_LOG_BROKEN = """data:{maxTitleBand:Math.round(maxTitleBand||0),nVis:visCards.length,cards:_cards}"""
F_LOG_FIXED = """data:{cards:_cards}"""

COLLAPSE_PIN_OLD = """function collapseAllPatchTrees(){
  var sc=typeof catalogScrollEl==='function'?catalogScrollEl():null;
  var y0=sc?sc.scrollTop:0;
  var anchor=null;
  if(sc){
    var sr=sc.getBoundingClientRect();
    var vis=document.querySelectorAll('#catalogMain .entry');
    for(var i=0;i<vis.length;i++){
      var r=vis[i].getBoundingClientRect();
      if(r.height>16&&r.bottom>sr.top+4&&r.top<sr.bottom-4){anchor=vis[i];break;}
    }
  }
  if(!anchor)anchor=lastViewedEntry||document.querySelector('.entry.selected');
  var top0=anchor?anchor.getBoundingClientRect().top:null;
  var mainEl=document.getElementById('catalogMain');
  var bodyEl=document.querySelector('#catalogMain > .catalog-body');
  function _scSnap(el){if(!el)return null;var cs=getComputedStyle(el);return {id:el.id||String(el.className||'').slice(0,24),oy:cs.overflowY,st:Math.round(el.scrollTop),sh:el.scrollHeight,ch:el.clientHeight};}
  function _pin(){
    if(!sc)return;
    if(anchor&&top0!=null){
      var t=anchor.getBoundingClientRect().top;
      sc.scrollTop=sc.scrollTop+(t-top0);
    }else sc.scrollTop=y0;
  }"""

PORT_DOC_NOTE_OLD = """function catalogDocNoteInsetBottom(){
  var note=document.getElementById('catalogDocNote');
  if(!note||note.classList.contains('is-embedded'))return 0;
  var cs=getComputedStyle(note);
  if(cs.display==='none'||cs.visibility==='hidden')return 0;
  var nr=note.getBoundingClientRect();
  if(!nr||nr.height<8)return 0;
  return Math.round(nr.height)+8;
}
function placeCatalogJumpStack(){
  var stack=document.getElementById('catalogJumpStack');
  var main=document.getElementById('catalogMain');
  if(!stack)return;
  var sides=document.body.classList.contains('display-sides');
  var fs=document.body.classList.contains('display-fs');
  var mainCs=main?getComputedStyle(main):null;
  var r=main?main.getBoundingClientRect():null;
  var mainHide=!main||fs||!sides||(mainCs&&mainCs.display==='none')||!r||r.width<8||r.height<8;
  if(mainHide){
    stack.style.cssText='display:none!important';
  }else{
    stack.style.cssText='';
    var padR=parseFloat(mainCs.paddingRight)||10;
    var padB=parseFloat(mainCs.paddingBottom)||10;
    var insetR=Math.max(8,Math.round(padR));
    var insetB=Math.max(8,Math.round(padB));
    var right=Math.max(6,Math.round((window.innerWidth||0)-r.right)+insetR);
    var bottom=Math.max(6,Math.round((window.innerHeight||0)-r.bottom)+insetB+(typeof catalogDocNoteInsetBottom==='function'?catalogDocNoteInsetBottom():0));
    stack.style.right=right+'px';
    stack.style.bottom=bottom+'px';
    stack.style.left='auto';
    stack.style.top='auto';
  }
  if(typeof dbgPortableJumpGap==='function')dbgPortableJumpGap('placeJump');
}"""

PORT_DOC_NOTE_NEW = """function catalogDocNoteBarRect(){
  var note=document.getElementById('catalogDocNote');
  if(!note)return null;
  var cs=getComputedStyle(note);
  if(cs.display==='none'||cs.visibility==='hidden')return null;
  var r=note.getBoundingClientRect();
  if(!r||r.height<8)return null;
  return r;
}
function catalogDocNoteInsetBottom(){
  var note=document.getElementById('catalogDocNote');
  if(!note||note.classList.contains('is-embedded'))return 0;
  var cs=getComputedStyle(note);
  if(cs.display==='none'||cs.visibility==='hidden')return 0;
  var nr=note.getBoundingClientRect();
  if(!nr||nr.height<8)return 0;
  return Math.round(nr.height)+8;
}
function catalogJumpStackBottomInset(){
  var main=document.getElementById('catalogMain');
  var noteR=typeof catalogDocNoteBarRect==='function'?catalogDocNoteBarRect():null;
  if(!main||!noteR)return typeof catalogDocNoteInsetBottom==='function'?catalogDocNoteInsetBottom():0;
  var mr=main.getBoundingClientRect();
  var note=document.getElementById('catalogDocNote');
  var embedded=!!(note&&note.classList.contains('is-embedded'));
  var gap=10;
  if(noteR.bottom<=mr.top+4||noteR.top>=mr.bottom-4)return 0;
  if(!embedded)return Math.max(0,Math.round(mr.bottom-noteR.top)+gap);
  if(noteR.top<mr.bottom-24)return Math.max(0,Math.round(mr.bottom-noteR.top)+gap);
  return 0;
}
function placeCatalogJumpStack(){
  var stack=document.getElementById('catalogJumpStack');
  var main=document.getElementById('catalogMain');
  if(!stack)return;
  var sides=document.body.classList.contains('display-sides');
  var middle=document.body.classList.contains('display-middle');
  var fs=document.body.classList.contains('display-fs');
  var mainCs=main?getComputedStyle(main):null;
  var r=main?main.getBoundingClientRect():null;
  var mainHide=!main||fs||!(sides||middle)||(mainCs&&mainCs.display==='none')||!r||r.width<8||r.height<8;
  if(mainHide){
    stack.style.cssText='display:none!important';
  }else{
    stack.style.cssText='';
    var padR=parseFloat(mainCs.paddingRight)||10;
    var padB=parseFloat(mainCs.paddingBottom)||10;
    var insetR=Math.max(8,Math.round(padR));
    var insetB=Math.max(8,Math.round(padB));
    var right=Math.max(6,Math.round((window.innerWidth||0)-r.right)+insetR);
    var noteInset=typeof catalogJumpStackBottomInset==='function'?catalogJumpStackBottomInset():0;
    var bottom=Math.max(6,Math.round((window.innerHeight||0)-r.bottom)+insetB+noteInset);
    stack.style.right=right+'px';
    stack.style.bottom=bottom+'px';
    stack.style.left='auto';
    stack.style.top='auto';
  }
  if(typeof dbgPortableJumpGap==='function')dbgPortableJumpGap('placeJump');
}
function bindCatalogJumpScroll(){
  var sc=(typeof catalogContentScroller==='function'&&catalogContentScroller())||document.getElementById('catalogMain');
  if(!sc||sc.dataset.jumpScrollBound)return;
  sc.dataset.jumpScrollBound='1';
  sc.addEventListener('scroll',function(){
    if(window._jumpScrollRaf)cancelAnimationFrame(window._jumpScrollRaf);
    window._jumpScrollRaf=requestAnimationFrame(function(){
      window._jumpScrollRaf=0;
      if(typeof placeCatalogJumpStack==='function')placeCatalogJumpStack();
    });
  },{passive:true});
}
window.catalogJumpStackBottomInset=catalogJumpStackBottomInset;
window.bindCatalogJumpScroll=bindCatalogJumpScroll;"""

PORT_SYNC_IX_OLD = """function syncIndexWindowDock(){
  var ix=document.getElementById('catalogIndex');
  var windowOk=window.CATALOG_PORTABLE||document.body.classList.contains('display-sides')||document.body.classList.contains('display-middle');
  var on=!!(ix&&!ix.classList.contains('is-embedded')&&windowOk);
  var prev=document.body.classList.contains('index-window-open');
  document.body.classList.toggle('index-window-open',on);
  var main=document.getElementById('catalogMain');
  var cb=main&&(main.querySelector(':scope > .catalog-body')||main.querySelector('.catalog-body'));
  if(on&&main){
    if(!prev){
      var keep=main.scrollTop;
      if(cb&&keep)cb.scrollTop=keep;
    }
    main.scrollTop=0;
    if(!main.dataset.ixDockScrollBound){
      main.dataset.ixDockScrollBound='1';
      main.addEventListener('scroll',function(){
        if(main.scrollTop)main.scrollTop=0;
      },{passive:true});
    }
  }
  if(main){
    main.style.setProperty('display','flex','important');
    main.style.setProperty('flex-direction','column','important');
    main.style.setProperty('overflow-y','hidden','important');
    main.style.setProperty('overflow-x','hidden','important');
    main.scrollTop=0;
    if(!main.dataset.ixDockScrollBound){
      main.dataset.ixDockScrollBound='1';
      main.addEventListener('scroll',function(){if(main.scrollTop)main.scrollTop=0;},{passive:true});
    }
    if(cb){
      cb.style.setProperty('overflow-y','auto','important');
      cb.style.setProperty('overflow-x','hidden','important');
      cb.style.setProperty('min-height','0','important');
      cb.style.setProperty('flex','1 1 0%','important');
      cb.style.setProperty('height','0','important');
    }
  }
  // #region agent log"""

PORT_SYNC_IX_NEW = """function syncIndexWindowDock(){
  var run=function(){
    var ix=document.getElementById('catalogIndex');
    var windowOk=window.CATALOG_PORTABLE||document.body.classList.contains('display-sides')||document.body.classList.contains('display-middle');
    var on=!!(ix&&!ix.classList.contains('is-embedded')&&windowOk);
    document.body.classList.toggle('index-window-open',on);
    var main=document.getElementById('catalogMain');
    var cb=main&&(main.querySelector(':scope > .catalog-body')||main.querySelector('.catalog-body'));
    if(main){
      main.style.setProperty('display','flex','important');
      main.style.setProperty('flex-direction','column','important');
      main.style.setProperty('overflow-y','hidden','important');
      main.style.setProperty('overflow-x','hidden','important');
      main.scrollTop=0;
      if(!main.dataset.ixDockScrollBound){
        main.dataset.ixDockScrollBound='1';
        main.addEventListener('scroll',function(){if(main.scrollTop)main.scrollTop=0;},{passive:true});
      }
      if(cb){
        cb.style.setProperty('overflow-y','auto','important');
        cb.style.setProperty('overflow-x','hidden','important');
        cb.style.setProperty('min-height','0','important');
        cb.style.setProperty('flex','1 1 0%','important');
        cb.style.setProperty('height','0','important');
      }
    }
  // #region agent log"""

PORT_SYNC_IX_TAIL_OLD = """  if(typeof applyIndexFillDocStyles==='function')applyIndexFillDocStyles();
  if(typeof window.syncMainHoverStripe==='function')window.syncMainHoverStripe();
}
window.syncIndexWindowDock=syncIndexWindowDock;"""

PORT_SYNC_IX_TAIL_NEW = """  if(typeof applyIndexFillDocStyles==='function')applyIndexFillDocStyles();
  if(typeof window.syncMainHoverStripe==='function')window.syncMainHoverStripe();
  if(typeof placeCatalogJumpStack==='function')placeCatalogJumpStack();
  };
  if(typeof withCatalogScrollPin==='function')withCatalogScrollPin(run);
  else run();
}
window.syncIndexWindowDock=syncIndexWindowDock;"""

PORT_TOGGLE_IX_OLD = """  var on=ix.classList.toggle('is-embedded');
  writeIndexEmbedPref(on);
  if(typeof writeModeSlot==='function')writeModeSlot({indexEmbed:on});
  if(typeof parkCatalogDocNote==='function')parkCatalogDocNote();
  if(typeof applyIndexScrollFit==='function')applyIndexScrollFit();
  if(typeof syncIndexWindowDock==='function')syncIndexWindowDock();
  if(typeof applyIndexFillDocStyles==='function')applyIndexFillDocStyles();
  if(typeof portableEnsureScrollMenus==='function')portableEnsureScrollMenus();
  syncIndexEmbedBtn();
  var sc=(typeof catalogContentScroller==='function'&&catalogContentScroller())||document.getElementById('catalogMain');
  if(on&&sc)sc.scrollTop=0;
  // #region agent log"""

PORT_TOGGLE_IX_NEW = """  var on=ix.classList.toggle('is-embedded');
  var apply=function(){
    writeIndexEmbedPref(on);
    if(typeof writeModeSlot==='function')writeModeSlot({indexEmbed:on});
    if(typeof parkCatalogDocNote==='function')parkCatalogDocNote();
    if(typeof applyIndexScrollFit==='function')applyIndexScrollFit();
    if(typeof syncIndexWindowDock==='function')syncIndexWindowDock();
    if(typeof applyIndexFillDocStyles==='function')applyIndexFillDocStyles();
    if(typeof portableEnsureScrollMenus==='function')portableEnsureScrollMenus();
    syncIndexEmbedBtn();
  };
  if(typeof withCatalogScrollPin==='function')withCatalogScrollPin(apply);
  else apply();
  // #region agent log"""

COLLAPSE_PIN_NEW = """function collapseAllPatchTrees(){
  var pin=typeof catalogScrollAnchor==='function'?catalogScrollAnchor():null;
  var sc=pin&&pin.sc||(typeof catalogScrollEl==='function'?catalogScrollEl():null);
  var anchor=pin&&pin.anchor||null;
  var top0=pin&&pin.top0!=null?pin.top0:(anchor?anchor.getBoundingClientRect().top:null);
  var y0=pin?pin.y0:(sc?sc.scrollTop:0);
  if(!anchor)anchor=lastViewedEntry||document.querySelector('.entry.selected');
  if(anchor&&!top0)top0=anchor.getBoundingClientRect().top;
  var mainEl=document.getElementById('catalogMain');
  var bodyEl=document.querySelector('#catalogMain > .catalog-body');
  function _scSnap(el){if(!el)return null;var cs=getComputedStyle(el);return {id:el.id||String(el.className||'').slice(0,24),oy:cs.overflowY,st:Math.round(el.scrollTop),sh:el.scrollHeight,ch:el.clientHeight};}
  function _pin(){if(typeof catalogRestoreScroll==='function')catalogRestoreScroll({sc:sc,y0:y0,anchor:anchor,top0:top0});}"""


def once(text: str, old: str, new: str, label: str, name: str, optional: bool = False) -> str:
    if old not in text:
        if new in text or optional:
            print(f"  skip {label}")
            return text
        raise SystemExit(f"{name}: missing [{label}]")
    n = text.count(old)
    if n != 1:
        raise SystemExit(f"{name}: [{label}] count={n}")
    print(f"  OK {label}")
    return text.replace(old, new, 1)


def safe_write(path: Path, text: str) -> None:
    if not text.rstrip().endswith("</html>"):
        raise SystemExit(f"{path.name}: bad end before write")
    old_size = path.stat().st_size
    fd, tmp_name = tempfile.mkstemp(suffix=".html", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as tmp:
            tmp.write(text)
        check = Path(tmp_name).read_text(encoding="utf-8")
        if not check.rstrip().endswith("</html>"):
            raise SystemExit(f"{path.name}: temp lost </html>")
        new_size = Path(tmp_name).stat().st_size
        if new_size < old_size * 0.5:
            raise SystemExit(f"{path.name}: size drop {old_size} -> {new_size}")
        os.replace(tmp_name, path)
    except Exception:
        Path(tmp_name).unlink(missing_ok=True)
        raise
    print(f"  wrote {path.name} bytes {new_size} delta {new_size - old_size}")


def patch_html(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    if not text.rstrip().endswith("</html>"):
        raise SystemExit(f"{path.name}: no </html>")
    print(f"==== {path.name}")
    already = MARK in text
    if already and "withCatalogScrollPin(apply)" in text:
        print("  skip (already)")
        return
    if already:
        print("  partial (toggle-embed)")

    if "function catalogScrollAnchor" not in text:
        text = once(text, SCROLL_ANCHOR, SCROLL_ANCHOR + SCROLL_HELPERS, "scroll-helpers", path.name)
    is_portable = "CATALOG_PORTABLE" in text and "dbgPortableJumpGap" in text
    if not already:
        if is_portable:
            text = once(text, PORT_DOC_NOTE_OLD, PORT_DOC_NOTE_NEW, "jump-about-port", path.name)
            text = once(text, PORT_SYNC_IX_OLD, PORT_SYNC_IX_NEW, "sync-index-dock-port", path.name)
            text = once(text, PORT_SYNC_IX_TAIL_OLD, PORT_SYNC_IX_TAIL_NEW, "sync-index-dock-port-tail", path.name)
            text = once(text, PORT_TOGGLE_IX_OLD, PORT_TOGGLE_IX_NEW, "toggle-embed-port", path.name)
        else:
            text = once(text, DOC_NOTE_OLD, DOC_NOTE_NEW, "jump-about", path.name)
            text = once(text, SYNC_IX_OLD, SYNC_IX_NEW, "sync-index-dock", path.name)
    if is_portable:
        pass
    elif TOGGLE_IX_BODY_OLD in text:
        text = once(text, TOGGLE_IX_BODY_OLD, TOGGLE_IX_BODY_NEW, "toggle-embed-pin", path.name)
    elif "var on=ix.classList.toggle('is-embedded');\n  writeIndexEmbedPref(on);" in text and "withCatalogScrollPin(apply)" not in text:
        DESK_TOGGLE_OLD = """  var on=ix.classList.toggle('is-embedded');
  writeIndexEmbedPref(on);
  if(typeof writeModeSlot==='function')writeModeSlot({indexEmbed:on},sides?'sides':(middle?'middle':undefined));
  if(typeof parkCatalogDocNote==='function')parkCatalogDocNote();
  if(typeof applyIndexScrollFit==='function')applyIndexScrollFit();
  if(typeof syncIndexWindowDock==='function')syncIndexWindowDock();
  if(typeof applyIndexFillDocStyles==='function')applyIndexFillDocStyles();
  syncIndexEmbedBtn();
}"""
        text = once(text, DESK_TOGGLE_OLD, TOGGLE_IX_BODY_NEW, "toggle-embed-pin-desk", path.name)
    else:
        text = once(text, TOGGLE_IX_TAIL_OLD, TOGGLE_IX_TAIL_NEW, "toggle-embed-no-scroll0", path.name, optional=True)
    if not already:
        text = once(text, HDR_OLD, HDR_NEW, "hdr-bar-pin", path.name)
        text = once(text, EQ_START_OLD, EQ_START_NEW, "eq-scroll-pin", path.name)
        text = once(text, EQ_END_OLD, EQ_END_NEW, "eq-scroll-restore", path.name)
        text = once(text, ENSURE_JUMP_OLD, ENSURE_JUMP_NEW, "bind-jump-scroll", path.name)
        text = once(text, COLLAPSE_PIN_OLD, COLLAPSE_PIN_NEW, "collapse-use-pin", path.name)
        if F_LOG_BROKEN in text:
            text = once(text, F_LOG_BROKEN, F_LOG_FIXED, "f-log-fix", path.name)
        if MARK not in text:
            text = text.replace(
                "window.catalogScrollAnchor=catalogScrollAnchor;",
                f"/* {MARK} */\nwindow.catalogScrollAnchor=catalogScrollAnchor;",
                1,
            )
    safe_write(path, text)


def main() -> None:
    for p in FILES:
        if not p.exists():
            raise SystemExit(f"missing {p}")
        patch_html(p)
    print("OK", MARK)


if __name__ == "__main__":
    main()
