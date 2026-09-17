#!/usr/bin/env python3
"""Pinned-card pyramid dock (max 9), History button chrome, Middle Save offset.

Syncs the six catalog HTML/builder files. Does not commit or add agent logs.
"""
from pathlib import Path

ROOT = Path("/home/phnx/kiro-kontakt-patch")
FILES = [
    ROOT / "public/catalogs/DS-CATALOG.html",
    ROOT / "public/catalogs/KONTAKT-CATALOG.html",
    ROOT / "public/catalogs/DS-CATALOG-portable.html",
    ROOT / "public/catalogs/KONTAKT-CATALOG-portable.html",
    ROOT / "kiro/specs/kontakt-workspace-drive-dirty-fix/artifacts/build-ds-catalog-html.sh",
    ROOT / "kiro/specs/kontakt-workspace-drive-dirty-fix/artifacts/build-kontakt-catalog-html.sh",
]


def sub(text, old, new, label, path, count=1):
    n = text.count(old)
    if n == count:
        return text.replace(old, new)
    if new in text or (count == 1 and text.count(new) >= 1):
        print(f"  skip {label} (already)")
        return text
    raise SystemExit(f"{path.name}: {label} count={n} expected {count}")


CSS_DOCK_OLD = (
    " #cardMinDock{display:none;position:fixed;z-index:10040;left:0;width:100%;bottom:0;justify-content:center;align-items:center;flex-wrap:nowrap;gap:.55rem;padding:0 .75rem max(.85rem,env(safe-area-inset-bottom));box-sizing:border-box;pointer-events:none}\n"
    " #cardMinDock.is-on{display:flex}\n"
    " #cardMinDock .card-min-row{display:flex;justify-content:center;align-items:center;flex-wrap:nowrap;gap:.55rem;min-width:0;max-width:100%;pointer-events:none}\n"
    " #cardMinDock .card-min-pill{pointer-events:auto;display:inline-flex;align-items:center;gap:.35rem;max-width:min(16.5rem,42%);min-height:2.85rem;padding:.28rem;"
)
CSS_DOCK_NEW = (
    " #cardMinDock{display:none;position:fixed;z-index:10040;left:0;width:100%;bottom:0;flex-direction:column;justify-content:flex-end;align-items:center;flex-wrap:nowrap;gap:.4rem;padding:0 .75rem max(.85rem,env(safe-area-inset-bottom));box-sizing:border-box;pointer-events:none;overflow:visible;max-width:100vw}\n"
    " #cardMinDock.is-on{display:flex}\n"
    " #cardMinDock .card-min-stack{display:flex;flex-direction:column-reverse;justify-content:flex-end;align-items:center;gap:.4rem;width:auto;max-width:100%;pointer-events:none}\n"
    " #cardMinDock .card-min-row{display:flex;justify-content:center;align-items:center;flex-wrap:nowrap;gap:.45rem;min-width:0;width:auto;max-width:100%;pointer-events:none}\n"
    " #cardMinDock .card-min-pill{pointer-events:auto;display:inline-flex;align-items:center;gap:.35rem;max-width:min(14.5rem,var(--card-min-pill-max,14.5rem));min-width:0;flex:0 0 auto;width:auto;min-height:2.85rem;padding:.28rem;"
)

CSS_SAVE_OLD = (
    "#cardMinDock .card-min-save{pointer-events:auto;position:absolute;right:.75rem;bottom:max(.85rem,env(safe-area-inset-bottom));display:inline-flex;align-items:center;justify-content:center;min-height:2.85rem;padding:0 .8rem;border:1px solid var(--accent-instrument);border-radius:999px;background:var(--bg-card);color:var(--accent-instrument);font:inherit;font-size:.9rem;font-weight:650;cursor:pointer;touch-action:manipulation;box-shadow:0 8px 28px rgba(0,0,0,.38)}\n"
)
CSS_SAVE_NEW = (
    "#cardMinDock .card-min-save{pointer-events:auto;position:absolute;right:.75rem;bottom:max(.85rem,env(safe-area-inset-bottom));display:inline-flex;align-items:center;justify-content:center;min-height:2.85rem;padding:0 .8rem;border:1px solid var(--accent-instrument);border-radius:999px;background:var(--bg-card);color:var(--accent-instrument);font:inherit;font-size:.9rem;font-weight:650;cursor:pointer;touch-action:manipulation;box-shadow:0 8px 28px rgba(0,0,0,.38);z-index:1}\n"
)

CSS_HIST_OLD = (
    " .ac-history-btn{box-sizing:border-box;flex:0 0 auto;min-height:2.25rem;min-width:2.25rem;padding:0 .5rem;border:1px solid var(--border);border-radius:8px;background:var(--bg-card);color:var(--text);font-family:'Palatino Linotype',Palatino,Garamond,serif;font-size:1.3rem;font-weight:700;font-style:italic;letter-spacing:-0.02em;cursor:pointer;touch-action:manipulation;white-space:nowrap;display:inline-flex;align-items:center;justify-content:center;line-height:1}\n"
    " .ac-history-btn:hover,.ac-history-btn[aria-expanded=\"true\"]{border-color:var(--accent-instrument);color:var(--accent-instrument);background:var(--accent-instrument-bg)}\n"
)
CSS_HIST_NEW = (
    " .ac-history-btn{box-sizing:border-box;flex:0 0 auto;min-height:2.25rem;min-width:2.25rem;height:2.25rem;padding:0 .5rem;border:1px solid var(--border);border-radius:6px;background:var(--bg-card);color:var(--text-muted);font:inherit;font-size:.875rem;font-weight:600;font-style:normal;letter-spacing:0;cursor:pointer;touch-action:manipulation;white-space:nowrap;display:inline-flex;align-items:center;justify-content:center;line-height:1}\n"
    " .ac-history-btn:hover,.ac-history-btn[aria-expanded=\"true\"]{border-color:var(--accent-instrument);color:var(--accent-instrument);background:var(--accent-instrument-bg);font-weight:600}\n"
)

CSS_PILL_LIVE_OLD = "max-width:min(16.5rem,var(--card-min-pill-max,18%));min-width:0;flex:0 1 auto;"
CSS_PILL_LIVE_NEW = "max-width:min(14.5rem,var(--card-min-pill-max,14.5rem));min-width:0;flex:0 0 auto;width:auto;"
CSS_SAVE_MIDDLE_OLD = (
    "body.display-middle #cardMinDock .card-min-save,body.display-sides.display-middle #cardMinDock .card-min-save{right:auto;left:calc(50% + (var(--card-min-stack-w,0px) / 2) + .45rem)}\n"
)

HELPERS = r"""function cardMinRemPx(){
  var n=parseFloat(getComputedStyle(document.documentElement).fontSize||'16');
  return n>0?n:16;
}
function cardMinGapPx(){
  var d=document.getElementById('cardMinDock');
  var row=d&&d.querySelector('.card-min-row');
  var cs=getComputedStyle(row||d||document.body);
  var g=parseFloat(cs.columnGap||cs.gap||'0');
  return g>0?g:Math.round(.45*cardMinRemPx());
}
function cardMinInnerWidth(){
  var d=document.getElementById('cardMinDock');
  var main=document.getElementById('catalogMain');
  var w=0;
  if(d){
    var r=d.getBoundingClientRect();
    var cs=getComputedStyle(d);
    var pl=parseFloat(cs.paddingLeft)||0,pr=parseFloat(cs.paddingRight)||0;
    w=Math.max(0,r.width-pl-pr);
  }
  if(w<40&&main)w=main.getBoundingClientRect().width;
  if(w<40)w=window.innerWidth||360;
  return w;
}
function cardMinRowAvailWidth(){
  var vw=window.innerWidth||360;
  return Math.max(80,vw-24);
}
function cardMinSaveReserve(){
  var sav=document.getElementById('cardMinDockSave');
  if(!sav||sav.hidden)return 0;
  var w=72;
  var r=sav.getBoundingClientRect();
  if(r.width>8)w=r.width;
  return 2*(w+Math.round(.45*cardMinRemPx()));
}
function cardMinMaxPerRow(n){
  if(n==null||n==='')n=(typeof cardMinDockItems!=='undefined'&&cardMinDockItems)?cardMinDockItems.length:0;
  n=n|0;
  var rem=cardMinRemPx();
  var gap=cardMinGapPx();
  var saveW=0;
  var sav=document.getElementById('cardMinDockSave');
  if(sav&&!sav.hidden){
    var sr0=sav.getBoundingClientRect();
    saveW=(sr0.width>8?sr0.width:72)+Math.round(.55*rem);
  }
  var inner=Math.max(80,cardMinRowAvailWidth()-saveW);
  function fit(minW){return Math.floor((inner+gap)/Math.max(1,minW+gap));}
  var widthCap=fit(8.75*rem);
  if(widthCap>=5)widthCap=5;
  else if(widthCap>=4)widthCap=4;
  else widthCap=Math.min(3,Math.max(1,fit(4.6*rem)));
  var countCap=n>=7?5:Math.min(3,Math.max(1,n||1));
  var cap=Math.min(widthCap,countCap);
  if(n>0)cap=Math.min(cap,n);
  return Math.max(1,cap);
}
function cardMinPyramidCounts(n,maxPerRow){
  n=n|0;
  maxPerRow=Math.max(1,Math.min(5,maxPerRow|0||5));
  if(n<7&&maxPerRow>3)maxPerRow=3;
  if(n<=0)return [];
  var rows=[],left=n;
  while(left>0){
    var take=Math.min(maxPerRow,left);
    rows.push(take);
    left-=take;
  }
  if(rows.length>=3&&rows[rows.length-1]===1){
    for(var i=rows.length-2;i>=1;i--){
      if(rows[i]-1>=rows[i+1]+1){rows[i]--;rows[rows.length-1]++;break;}
    }
  }
  return rows;
}
function cardMinRectsOverlap(a,b,pad){
  if(!a||!b)return false;
  pad=pad||0;
  return !(a.right<b.left-pad||a.left>b.right+pad||a.bottom<b.top-pad||a.top>b.bottom+pad);
}
function cardMinLayoutRows(){
  var d=document.getElementById('cardMinDock');
  if(!d)return;
  var stack=d.querySelector('.card-min-stack');
  if(!stack)return;
  var pills=Array.prototype.slice.call(stack.querySelectorAll('.card-min-pill'));
  var n=pills.length;
  var rem=cardMinRemPx();
  var gap=cardMinGapPx();
  var saveRes=typeof cardMinSaveReserve==='function'?cardMinSaveReserve():0;
  var per=typeof cardMinMaxPerRow==='function'?cardMinMaxPerRow(n):Math.min(3,Math.max(1,n||1));
  function apply(perNow,pillCap){
    var counts=cardMinPyramidCounts(n,perNow);
    d.setAttribute('data-card-min-per',String(perNow));
    d.style.setProperty('--card-min-per-row',String(perNow));
    pills.forEach(function(p){stack.appendChild(p);});
    Array.prototype.slice.call(stack.querySelectorAll('.card-min-row')).forEach(function(row){
      if(row.parentNode)row.parentNode.removeChild(row);
    });
    var i=0;
    counts.forEach(function(c,ri){
      var row=document.createElement('div');
      row.className='card-min-row';
      row.setAttribute('data-card-min-row',String(ri));
      for(var k=0;k<c&&i<pills.length;k++,i++){
        var pill=pills[i];
        pill.setAttribute('data-card-min-slot',k===0?'left':(k===c-1?'right':'middle'));
        row.appendChild(pill);
      }
      stack.appendChild(row);
    });
    var rowN=Math.max(1,counts[0]||1);
    var inner=Math.max(80,cardMinRowAvailWidth()-saveRes);
    var pillMax=Math.min(pillCap,Math.floor((inner-gap*Math.max(0,rowN-1))/rowN));
    pillMax=Math.max(72,pillMax);
    d.style.setProperty('--card-min-pill-max',pillMax+'px');
    return counts;
  }
  var cap=Math.round(14.5*rem);
  apply(per,cap);
  var sav=document.getElementById('cardMinDockSave');
  var saveW=72;
  if(sav&&!sav.hidden){
    var sbb=sav.getBoundingClientRect();
    if(sbb.width>8)saveW=sbb.width;
  }
  var need=saveW+gap+8;
  function overflowRight(){
    var sr=stack.getBoundingClientRect();
    var vw=window.innerWidth||0;
    return sr.width>8&&sr.right+need>vw;
  }
  if(overflowRight()&&per>4){per=4;apply(per,cap);}
  if(overflowRight()&&per>3){per=3;apply(per,cap);}
  if(overflowRight()){
    var sr=stack.getBoundingClientRect();
    var vw=window.innerWidth||0;
    var room=Math.max(80,vw-need-(sr.left>0?sr.left:8));
    var bottom=stack.querySelector('.card-min-row');
    var rowN=bottom?Math.max(1,bottom.querySelectorAll('.card-min-pill').length):1;
    var shrink=Math.max(72,Math.floor((room-gap*Math.max(0,rowN-1))/rowN));
    apply(per,Math.min(cap,shrink));
  }
}
function cardMinPlaceSave(){
  var d=document.getElementById('cardMinDock');
  var sav=document.getElementById('cardMinDockSave');
  if(!d||!sav)return;
  sav.style.removeProperty('left');
  sav.style.removeProperty('right');
  sav.style.removeProperty('bottom');
  sav.style.removeProperty('top');
  if(sav.hidden){
    d.style.setProperty('--card-min-stack-w','0px');
    return;
  }
  var middle=document.body.classList.contains('display-middle');
  var stack=d.querySelector('.card-min-stack');
  var sr=stack?stack.getBoundingClientRect():null;
  var dr=d.getBoundingClientRect();
  var gap=Math.round(.45*cardMinRemPx());
  var saveW=sav.getBoundingClientRect().width||72;
  var saveH=sav.getBoundingClientRect().height||46;
  d.style.setProperty('--card-min-stack-w',sr&&sr.width>8?Math.round(sr.width)+'px':'0px');
  function chromeRects(){
    var out=[];
    ['catalogJumpStack','searchHistory'].forEach(function(id){
      var el=document.getElementById(id);
      if(!el)return;
      var cs=getComputedStyle(el);
      if(cs.display==='none'||cs.visibility==='hidden')return;
      var r=el.getBoundingClientRect();
      if(r.width>4&&r.height>4)out.push(r);
    });
    return out;
  }
  function hits(){
    var sb=sav.getBoundingClientRect();
    var hit=false;
    Array.prototype.forEach.call(d.querySelectorAll('.card-min-pill'),function(p){
      var r=p.getBoundingClientRect();
      if(r.width<4||r.height<4)return;
      if(cardMinRectsOverlap(sb,r,4))hit=true;
    });
    chromeRects().forEach(function(r){
      if(cardMinRectsOverlap(sb,r,4))hit=true;
    });
    return hit;
  }
  function setLeft(px){
    sav.style.right='auto';
    sav.style.left=Math.round(px)+'px';
  }
  function setRightCss(){
    sav.style.left='auto';
    sav.style.right='.75rem';
  }
  function liftAbove(){
    if(sr&&sr.width>8){
      var gapY=Math.max(gap,6);
      var wantB=sr.top-gapY;
      var cssB=dr.bottom-wantB;
      sav.style.bottom=Math.round(Math.max(0,cssB))+'px';
      var liftLeft=sr.right-saveW-dr.left;
      if(liftLeft<8)liftLeft=8;
      if(liftLeft+saveW>dr.width-8)liftLeft=Math.max(8,dr.width-saveW-8);
      setLeft(liftLeft);
    }else{
      sav.style.bottom=Math.round(saveH+gap)+'px';
    }
  }
  if(sr&&sr.width>8){
    var leftBeside=sr.right+gap-dr.left;
    var fitsRight=leftBeside+saveW<=dr.width-8;
    var leftOf=sr.left-gap-saveW-dr.left;
    var fitsLeft=leftOf>=8;
    if(middle){
      if(fitsRight)setLeft(leftBeside);
      else if(fitsLeft)setLeft(leftOf);
      else liftAbove();
    }else{
      setRightCss();
      if(hits()){
        if(fitsRight)setLeft(leftBeside);
        else if(fitsLeft)setLeft(leftOf);
        else liftAbove();
      }
    }
  }else setRightCss();
  if(hits())liftAbove();
}
window.cardMinPyramidCounts=cardMinPyramidCounts;
window.cardMinMaxPerRow=cardMinMaxPerRow;
window.cardMinLayoutRows=cardMinLayoutRows;
window.cardMinPlaceSave=cardMinPlaceSave;
"""

PLACE_OLD = """function cardMinPlace(){
  if(typeof placeCatalogJumpStack==='function')placeCatalogJumpStack();
  var d=document.getElementById('cardMinDock');
  if(!d)return;
  var main=document.getElementById('catalogMain');
  var r=main?main.getBoundingClientRect():null;
  if(!r||r.width<40){d.style.left='0';d.style.width='100%';d.style.bottom='0';return;}
  d.style.left=Math.round(r.left)+'px';
  d.style.width=Math.round(r.width)+'px';
  d.style.bottom=Math.max(0,Math.round((window.innerHeight||0)-r.bottom))+'px';
}
"""

PLACE_NEW = (
    HELPERS
    + """function cardMinPlace(){
  if(typeof placeCatalogJumpStack==='function')placeCatalogJumpStack();
  var d=document.getElementById('cardMinDock');
  if(!d)return;
  d.style.left='0';
  d.style.width='100%';
  d.style.bottom='0';
  if(typeof cardMinLayoutRows==='function')cardMinLayoutRows();
  if(typeof cardMinPlaceSave==='function')cardMinPlaceSave();
}
"""
)

MAXPER_LIVE_OLD = """function cardMinMaxPerRow(){
  var w=cardMinInnerWidth();
  var gap=cardMinGapPx();
  var rem=cardMinRemPx();
  function fit(minW){return Math.floor((w+gap)/Math.max(1,minW+gap));}
  var n=Math.min(5,Math.max(1,fit(9.25*rem)));
  if(n>=5)return 5;
  if(n>=4)return 4;
  return Math.min(3,Math.max(1,fit(4.6*rem)));
}
"""
MAXPER_LIVE_NEW = """function cardMinRowAvailWidth(){
  var vw=window.innerWidth||360;
  return Math.max(80,vw-24);
}
function cardMinSaveReserve(){
  var sav=document.getElementById('cardMinDockSave');
  if(!sav||sav.hidden)return 0;
  var w=72;
  var r=sav.getBoundingClientRect();
  if(r.width>8)w=r.width;
  return 2*(w+Math.round(.45*cardMinRemPx()));
}
function cardMinMaxPerRow(){
  var w=cardMinRowAvailWidth();
  var gap=cardMinGapPx();
  var rem=cardMinRemPx();
  function fit(minW){return Math.floor((w+gap)/Math.max(1,minW+gap));}
  var n=Math.min(5,Math.max(1,fit(9.25*rem)));
  if(n>=5)return 5;
  if(n>=4)return 4;
  return Math.min(3,Math.max(1,fit(4.6*rem)));
}
"""
PILL_LIVE_OLD = """  var inner=cardMinInnerWidth();
  var gap=cardMinGapPx();
  var pillMax=Math.max(72,Math.floor((inner-gap*Math.max(0,per-1))/Math.max(1,per)));
"""
PILL_LIVE_NEW = """  var inner=Math.max(80,cardMinInnerWidth()-(typeof cardMinSaveReserve==='function'?cardMinSaveReserve():0));
  var gap=cardMinGapPx();
  var pillMax=Math.max(72,Math.floor((inner-gap*Math.max(0,per-1))/Math.max(1,per)));
"""
PLACE_GEO_OLD = """  var main=document.getElementById('catalogMain');
  var r=main?main.getBoundingClientRect():null;
  if(!r||r.width<40){d.style.left='0';d.style.width='100%';d.style.bottom='0';}
  else{
    d.style.left=Math.round(r.left)+'px';
    d.style.width=Math.round(r.width)+'px';
    d.style.bottom=Math.max(0,Math.round((window.innerHeight||0)-r.bottom))+'px';
  }
"""
PLACE_GEO_NEW = """  d.style.left='0';
  d.style.width='100%';
  d.style.bottom='0';
"""
SAVE_RESERVE_OLD = """function cardMinSaveReserve(){
  if(!document.body.classList.contains('display-middle'))return 0;
  var sav=document.getElementById('cardMinDockSave');
  var w=72;
  if(sav&&!sav.hidden){
    var r=sav.getBoundingClientRect();
    if(r.width>8)w=r.width;
  }
  return 2*(w+Math.round(.45*cardMinRemPx()));
}
"""
SAVE_RESERVE_NEW = """function cardMinSaveReserve(){
  var sav=document.getElementById('cardMinDockSave');
  if(!sav||sav.hidden)return 0;
  var w=72;
  var r=sav.getBoundingClientRect();
  if(r.width>8)w=r.width;
  return 2*(w+Math.round(.45*cardMinRemPx()));
}
"""

RENDER_OLD = """  d.innerHTML='';
  var row=document.createElement('div');
  row.className='card-min-row';
"""
RENDER_NEW = """  d.innerHTML='';
  var stack=document.createElement('div');
  stack.className='card-min-stack';
"""

APPEND_OLD = "    row.appendChild(pill);\n  });\n  d.appendChild(row);\n"
APPEND_NEW = "    stack.appendChild(pill);\n  });\n  d.appendChild(stack);\n"

RESTORE_OLD = """  sess.cards.forEach(function(c){
    if(!c||!c.id)return;
    cardMinDockItems.push({id:c.id,mode:c.mode||c.kind||'preview',kind:c.kind||(c.mode==='highlight'?'highlight':'preview'),name:c.name||''});
  });
  var frontId=sess.frontId||(sess.cards[sess.cards.length-1]&&sess.cards[sess.cards.length-1].id);
"""
RESTORE_NEW = """  sess.cards.forEach(function(c){
    if(!c||!c.id)return;
    cardMinDockItems.push({id:c.id,mode:c.mode||c.kind||'preview',kind:c.kind||(c.mode==='highlight'?'highlight':'preview'),name:c.name||''});
  });
  var maxDock=typeof CARD_MIN_MAX==='number'?CARD_MIN_MAX:9;
  while(cardMinDockItems.length>maxDock)cardMinDockItems.shift();
  var frontId=sess.frontId||(sess.cards[sess.cards.length-1]&&sess.cards[sess.cards.length-1].id);
"""

MODE_VARIANTS = [
    (
        "  if(typeof syncHdrMenuBtns==='function')syncHdrMenuBtns(); // fix-A: sync hdr menu btn state after every mode change\n\n"
        "}\n",
        "  if(typeof syncHdrMenuBtns==='function')syncHdrMenuBtns(); // fix-A: sync hdr menu btn state after every mode change\n"
        "  if(typeof cardMinPlace==='function')try{cardMinPlace();}catch(err){}\n\n"
        "}\n",
    ),
    (
        "  if(typeof syncHdrMenuBtns==='function')syncHdrMenuBtns(); // fix-A: sync header btn state on every mode change\n\n"
        "}\n",
        "  if(typeof syncHdrMenuBtns==='function')syncHdrMenuBtns(); // fix-A: sync header btn state on every mode change\n"
        "  if(typeof cardMinPlace==='function')try{cardMinPlace();}catch(err){}\n\n"
        "}\n",
    ),
]


def replace_span(t, start, end, new, label, path):
    i = t.find(start)
    if i < 0:
        return None
    j = t.find(end, i)
    if j < 0:
        raise SystemExit(f"{path.name}: {label} end not found")
    j += len(end)
    return t[:i] + new + t[j:]


def refine(t, path):
    nfix = 0
    if CSS_PILL_LIVE_OLD in t:
        t = sub(t, CSS_PILL_LIVE_OLD, CSS_PILL_LIVE_NEW, "pill-flex", path)
        nfix += 1
    elif CSS_PILL_LIVE_NEW not in t:
        raise SystemExit(f"{path.name}: pill flex CSS not found")
    if CSS_SAVE_MIDDLE_OLD in t:
        t = t.replace(CSS_SAVE_MIDDLE_OLD, "", 1)
        nfix += 1
    if MAXPER_LIVE_OLD in t:
        t = sub(t, MAXPER_LIVE_OLD, MAXPER_LIVE_NEW, "maxper-viewport", path)
        nfix += 1
    if PILL_LIVE_OLD in t:
        t = sub(t, PILL_LIVE_OLD, PILL_LIVE_NEW, "pill-save-reserve", path)
        nfix += 1
    if PLACE_GEO_OLD in t:
        t = sub(t, PLACE_GEO_OLD, PLACE_GEO_NEW, "dock-viewport", path)
        nfix += 1
    if SAVE_RESERVE_OLD in t:
        t = sub(t, SAVE_RESERVE_OLD, SAVE_RESERVE_NEW, "save-reserve-all", path)
        nfix += 1
    helpers_new = HELPERS[HELPERS.find("function cardMinMaxPerRow(") :]
    if "function cardMinMaxPerRow(n){" in t:
        nxt = replace_span(
            t,
            "function cardMinMaxPerRow(n){",
            "window.cardMinPlaceSave=cardMinPlaceSave;\n",
            helpers_new,
            "helpers-countcap-n",
            path,
        )
        if nxt is None:
            raise SystemExit(f"{path.name}: cardMinMaxPerRow(n) block not found")
        t = nxt
        nfix += 1
    elif "n<7&&maxPerRow>3" not in t:
        nxt = replace_span(
            t,
            "function cardMinMaxPerRow(){",
            "window.cardMinLayoutRows=cardMinLayoutRows;\n",
            helpers_new,
            "helpers-countcap",
            path,
        )
        if nxt is None:
            raise SystemExit(f"{path.name}: cardMinMaxPerRow() block not found")
        t = nxt
        nfix += 1
    if "function cardMinRowAvailWidth(" not in t:
        raise SystemExit(f"{path.name}: missing cardMinRowAvailWidth after refine")
    if "n<7&&maxPerRow>3" not in t:
        raise SystemExit(f"{path.name}: missing n<7 count cap after refine")
    if CSS_SAVE_MIDDLE_OLD in t:
        raise SystemExit(f"{path.name}: middle Save CSS still present")
    return t, nfix


def patch(path: Path):
    t = path.read_text(encoding="utf-8")
    if "function cardMinPyramidCounts(" in t and "var CARD_MIN_MAX=9;" in t:
        t, nfix = refine(t, path)
        path.write_text(t, encoding="utf-8")
        print("refined", path.name, nfix)
        return
    t = sub(t, "var CARD_MIN_MAX=3;", "var CARD_MIN_MAX=9;", "card-min-max", path)
    t = sub(
        t,
        "typeof CARD_MIN_MAX==='number'?CARD_MIN_MAX:3",
        "typeof CARD_MIN_MAX==='number'?CARD_MIN_MAX:9",
        "card-min-fallback",
        path,
        count=3,
    )
    t = sub(t, CSS_HIST_OLD, CSS_HIST_NEW, "hist-css", path)
    t = sub(t, CSS_DOCK_OLD, CSS_DOCK_NEW, "dock-css", path)
    t = sub(t, CSS_SAVE_OLD, CSS_SAVE_NEW, "save-css", path)
    t = sub(t, PLACE_OLD, PLACE_NEW, "card-min-place", path)
    t = sub(t, RENDER_OLD, RENDER_NEW, "render-stack", path)
    t = sub(t, APPEND_OLD, APPEND_NEW, "render-append", path)
    t = sub(t, RESTORE_OLD, RESTORE_NEW, "restore-cap", path)
    mode_hit = False
    for old, new in MODE_VARIANTS:
        if old in t:
            t = sub(t, old, new, "display-mode-place", path)
            mode_hit = True
            break
    if not mode_hit and "cardMinPlace();}catch(err){}" not in t:
        raise SystemExit(f"{path.name}: display-mode-place not found")
    path.write_text(t, encoding="utf-8")
    print("patched", path.name)


def main():
    for p in FILES:
        if not p.exists():
            raise SystemExit(f"missing {p}")
        patch(p)
    print("all ok")


if __name__ == "__main__":
    main()
