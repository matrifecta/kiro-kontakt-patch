#!/usr/bin/env python3
"""Reserve a bottom pin band and shrink side menus so session pins stay in content."""
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


def sub(text, old, new, label, path):
    n = text.count(old)
    if n == 1:
        return text.replace(old, new)
    if new in text or text.count(new) >= 1:
        print(f"  skip {path.name} {label}")
        return text
    raise SystemExit(f"{path.name}: {label} count={n}")


SIDES_ROWS_OLD = "grid-template-rows:auto minmax(0,1fr);column-gap:var(--sides-pane-gap,6px);row-gap:0;align-items:stretch}"
SIDES_ROWS_NEW = "grid-template-rows:auto minmax(0,1fr) var(--card-min-dock-h,0px);column-gap:var(--sides-pane-gap,6px);row-gap:0;align-items:stretch}"

MID_ROWS_OLD = "  grid-template-rows:auto var(--middle-menu-h,38dvh) minmax(0,1fr)!important;\n"
MID_ROWS_NEW = "  grid-template-rows:auto var(--middle-menu-h,38dvh) minmax(0,1fr) var(--card-min-dock-h,0px)!important;\n"

AVAIL_OLD = """function cardMinRowAvailWidth(){
  var vw=window.innerWidth||360;
  return Math.max(80,vw-24);
}
"""
AVAIL_NEW = """function cardMinRowAvailWidth(){
  var d=document.getElementById('cardMinDock');
  if(d){
    var dr=d.getBoundingClientRect();
    if(dr.width>40)return Math.max(80,dr.width-16);
  }
  var main=document.getElementById('catalogMain');
  if(main){
    var mr=main.getBoundingClientRect();
    if(mr.width>40)return Math.max(80,mr.width-16);
  }
  var vw=window.innerWidth||360;
  return Math.max(80,vw-24);
}
"""

FIT_FN = r"""function cardMinFitMenusForPins(){
  if(window._cardMinFitting)return;
  var n=(typeof cardMinDockItems!=='undefined'&&cardMinDockItems)?cardMinDockItems.length:0;
  var root=document.documentElement;
  var body=document.body;
  if(!n){
    root.style.setProperty('--card-min-dock-h','0px');
    body.classList.remove('has-card-min-dock');
    return;
  }
  window._cardMinFitting=1;
  body.classList.add('has-card-min-dock');
  try{
    var rem=cardMinRemPx();
    var gap=cardMinGapPx();
    var pill=Math.round(8.75*rem);
    var minPer=Math.max(1,Math.ceil(n/5));
    var countCap=n>=7?5:Math.min(3,Math.max(1,n));
    var wantPer=Math.max(minPer,Math.min(countCap,n));
    var wantW=wantPer*pill+(Math.max(0,wantPer-1)*gap)+16;
    var middle=body.classList.contains('display-middle');
    var sides=body.classList.contains('display-sides');
    var vw=window.innerWidth||1200;
    var paneGap=parseFloat(getComputedStyle(root).getPropertyValue('--sides-pane-gap'))||6;
    var lw=0,rw=0;
    if(sides&&!middle&&!(typeof isPortraitDesktopSides==='function'&&isPortraitDesktopSides())){
      var minL=240,minR=260;
      var o=typeof readSidesCols==='function'?readSidesCols():{lw:0,rw:0};
      lw=o.lw||Math.round(vw*0.22);
      rw=o.rw||Math.round(vw*0.26);
      var searchHid=body.classList.contains('search-chrome-collapsed');
      var kwHid=body.classList.contains('kw-chrome-collapsed');
      function contentW(L,R){return vw-(searchHid?0:L)-(kwHid?0:R)-2*paneGap;}
      var cw=contentW(lw,rw);
      if(cw<wantW){
        var need=wantW-cw;
        var canL=searchHid?0:Math.max(0,lw-minL);
        var canR=kwHid?0:Math.max(0,rw-minR);
        var take=Math.min(need,canL+canR);
        if(take>0){
          var dl=Math.round(take*(canL/(canL+canR||1)));
          var dr=take-dl;
          lw-=dl;rw-=dr;
          if(typeof writeSidesCols==='function')writeSidesCols(lw,rw);
          if(typeof applySidesCols==='function')applySidesCols();
        }
      }
    }
    if(middle&&typeof clampMiddleMh==='function'){
      var d=typeof middleLayoutDefaults==='function'?middleLayoutDefaults():null;
      var rowH=Math.round(2.85*rem)+gap;
      var rows=Math.min(5,Math.max(1,Math.ceil(n/Math.max(1,wantPer))));
      var band=rows*rowH+Math.round(.5*rem);
      if(d){
        var cur=parseInt(getComputedStyle(root).getPropertyValue('--middle-menu-h'),10)||d.menuH;
        var next=clampMiddleMh(cur-band,d);
        if(next<cur&&typeof writeMiddleLayout==='function'){
          writeMiddleLayout(null,next);
          if(typeof applyMiddleLayout==='function')applyMiddleLayout();
        }
      }
    }
    var per=typeof cardMinMaxPerRow==='function'?cardMinMaxPerRow(n):wantPer;
    var rows2=Math.min(5,Math.max(1,Math.ceil(n/Math.max(1,per))));
    var h=rows2*(Math.round(2.85*rem)+gap)+Math.round(.5*rem);
    root.style.setProperty('--card-min-dock-h',h+'px');
    // #region agent log
    try{var main=document.getElementById('catalogMain');var sc=document.getElementById('searchChrome');var fw=document.getElementById('filterWrap');function rb(el){if(!el)return null;var r=el.getBoundingClientRect();return {l:Math.round(r.left),r:Math.round(r.right),t:Math.round(r.top),b:Math.round(r.bottom),w:Math.round(r.width),h:Math.round(r.height)};}fetch('http://127.0.0.1:7529/ingest/1cf46354-1d61-4c80-bd72-a340f1db1b51',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'c00e3e'},body:JSON.stringify({sessionId:'c00e3e',runId:'post-fix',hypothesisId:'H1',location:'DS-CATALOG.html:cardMinFitMenusForPins',message:'pin-menu-fit',data:{n:n,wantW:wantW,lw:lw,rw:rw,per:per,rows:rows2,h:h,main:rb(main),search:rb(sc),kw:rb(fw),cls:body.className},timestamp:Date.now()})}).catch(function(){});}catch(eLog){}
    // #endregion
  }finally{
    window._cardMinFitting=0;
  }
}
"""

PLACE_OLD = """function cardMinPlace(){
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
PLACE_NEW = FIT_FN + """function cardMinPlace(){
  if(typeof placeCatalogJumpStack==='function')placeCatalogJumpStack();
  var d=document.getElementById('cardMinDock');
  if(!d)return;
  if(typeof cardMinFitMenusForPins==='function')cardMinFitMenusForPins();
  var main=document.getElementById('catalogMain');
  var r=main?main.getBoundingClientRect():null;
  if(r&&r.width>40){
    d.style.left=Math.round(r.left)+'px';
    d.style.width=Math.round(r.width)+'px';
    d.style.bottom='0';
  }else{
    d.style.left='0';
    d.style.width='100%';
    d.style.bottom='0';
  }
  if(typeof cardMinLayoutRows==='function')cardMinLayoutRows();
  if(typeof cardMinPlaceSave==='function')cardMinPlaceSave();
  var stack=d.querySelector('.card-min-stack');
  if(stack){
    var sh=Math.ceil(stack.getBoundingClientRect().height+12);
    if(sh>8)document.documentElement.style.setProperty('--card-min-dock-h',sh+'px');
  }
  // #region agent log
  try{var sc=document.getElementById('searchChrome');var fw=document.getElementById('filterWrap');var st=d.querySelector('.card-min-stack');function rb(el){if(!el)return null;var r2=el.getBoundingClientRect();return {l:Math.round(r2.left),r:Math.round(r2.right),t:Math.round(r2.top),b:Math.round(r2.bottom),w:Math.round(r2.width)};}var sr=rb(st),mr=rb(main),scr=rb(sc),kwr=rb(fw);var ovL=sr&&scr?sr.l<scr.r-2&&sr.r>scr.l+2&&sr.b>scr.t+2&&sr.t<scr.b-2:false;var ovR=sr&&kwr?sr.l<kwr.r-2&&sr.r>kwr.l+2&&sr.b>kwr.t+2&&sr.t<kwr.b-2:false;var ovC=sr&&mr?sr.t<mr.b-8&&sr.b>mr.b-2&&(sr.l<mr.l-2||sr.r>mr.r+2):false;fetch('http://127.0.0.1:7529/ingest/1cf46354-1d61-4c80-bd72-a340f1db1b51',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'c00e3e'},body:JSON.stringify({sessionId:'c00e3e',runId:'post-fix',hypothesisId:'H1',location:'DS-CATALOG.html:cardMinPlace',message:'pin-place-geo',data:{n:(cardMinDockItems&&cardMinDockItems.length)||0,stack:sr,main:mr,search:scr,kw:kwr,ovL:ovL,ovR:ovR,ovC:ovC,dockH:getComputedStyle(document.documentElement).getPropertyValue('--card-min-dock-h')},timestamp:Date.now()})}).catch(function(){});}catch(eLog){}
  // #endregion
}
"""

REST_OLD = """  if(typeof cardMinRender==='function')cardMinRender();
  setTimeout(function(){
    var dock=document.getElementById('cardMinDock');
    if(dock&&cardMinDockItems.length)dock.classList.add('is-on');
  },0);
};
"""
REST_NEW = """  if(typeof cardMinRender==='function')cardMinRender();
  setTimeout(function(){
    var dock=document.getElementById('cardMinDock');
    if(dock&&cardMinDockItems.length)dock.classList.add('is-on');
    if(typeof cardMinPlace==='function')cardMinPlace();
  },0);
};
"""


def apply(path: Path) -> None:
    t = path.read_text(encoding="utf-8")
    t = sub(t, SIDES_ROWS_OLD, SIDES_ROWS_NEW, "sides-rows", path)
    t = sub(t, MID_ROWS_OLD, MID_ROWS_NEW, "middle-rows", path)
    t = sub(t, AVAIL_OLD, AVAIL_NEW, "avail", path)
    t = sub(t, PLACE_OLD, PLACE_NEW, "place", path)
    t = sub(t, REST_OLD, REST_NEW, "restore", path)
    path.write_text(t, encoding="utf-8")
    print(path.name, "ok")


def main() -> None:
    for path in FILES:
        apply(path)


if __name__ == "__main__":
    main()
