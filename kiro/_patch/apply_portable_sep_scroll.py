#!/usr/bin/env python3
"""Portable: themed content scrollbar only; inner-only customize separators that actually drag."""
from pathlib import Path

ROOT = Path("/home/phnx/kiro-kontakt-patch")
FILES = [
    ROOT / "public/catalogs/KONTAKT-CATALOG-portable.html",
    ROOT / "public/catalogs/DS-CATALOG-portable.html",
]

CSS_MARK = "/* fix-PORTABLE-SEP-SCROLL:"
CSS_ADD = r"""
/* fix-PORTABLE-SEP-SCROLL: themed content thumb only; inner separators that follow CSS vars */
@media all{
  body.catalog-portable #catalogMain,
  body.catalog-portable.display-sides #catalogMain,
  body.catalog-portable.display-content #catalogMain{
    scrollbar-width:none!important;-ms-overflow-style:none!important
  }
  body.catalog-portable #catalogMain::-webkit-scrollbar,
  body.catalog-portable.display-sides #catalogMain::-webkit-scrollbar{
    display:none!important;width:0!important;height:0!important
  }
  body.catalog-portable #catalogMainHoverStripe.hover-scroll-fixed:not([hidden]),
  body.catalog-portable.has-hover-overflow-content #catalogMainHoverStripe.hover-scroll-fixed:not([hidden]){
    display:block!important;pointer-events:auto!important;z-index:40!important
  }
  body.catalog-portable #catalogMain>.hover-scroll-stripe{display:none!important}
  body.catalog-portable.layout-edit .ac-width,
  body.catalog-portable.layout-edit .ac-height,
  body.catalog-portable.layout-edit #acWidth,
  body.catalog-portable.layout-edit #acHeight,
  body.catalog-portable.layout-edit .search-height,
  body.catalog-portable.layout-edit #searchHeight,
  body.catalog-portable.layout-edit .kw-shade-height,
  body.catalog-portable.layout-edit #kwShadeHeight{
    display:none!important;pointer-events:none!important
  }
  body.catalog-portable:not(.layout-edit) #indexHeight,
  body.catalog-portable #catalogIndex.is-embedded #indexHeight,
  body.catalog-portable #catalogIndex.is-collapsed #indexHeight{
    display:none!important;pointer-events:none!important
  }
  body.catalog-portable.layout-edit #catalogIndex:not(.is-embedded):not(.is-collapsed) #indexHeight{
    display:block!important;pointer-events:auto!important;cursor:row-resize;z-index:24
  }
  body.catalog-portable.layout-edit #searchSplit.port-stripe-v,
  body.catalog-portable.layout-edit #searchSplit.port-stripe-h,
  body.catalog-portable.layout-edit #dualFsSep.port-stripe-v,
  body.catalog-portable.layout-edit #dualFsSep.port-stripe-h{
    display:block!important;pointer-events:auto!important;z-index:120!important
  }
  body.catalog-portable.display-sides:not(.display-middle):not(.search-chrome-collapsed):not(.ac-fs-open) #searchChrome,
  body.catalog-portable.display-fs.dual-fs-open #searchChrome,
  body.catalog-portable.display-sides.ac-fs-open.kw-fs-open #searchChrome{
    width:auto!important
  }
  body.catalog-portable.display-sides:not(.display-middle).kw-open:not(.kw-chrome-collapsed):not(.search-chrome-collapsed):not(.ac-fs-open):not(.kw-fs-open),
  body.catalog-portable.display-sides.dual-fs-open,
  body.catalog-portable.display-sides.ac-fs-open.kw-fs-open,
  body.catalog-portable.display-fs.dual-fs-open,
  body.catalog-portable.display-fs.ac-fs-open.kw-fs-open{
    grid-template-columns:minmax(0,var(--portable-lw,42%)) minmax(0,1fr)!important
  }
  body.catalog-portable.display-sides.display-middle:not(.ac-fs-open):not(.kw-fs-open):not(.search-chrome-collapsed) #searchChrome,
  body.catalog-portable.display-sides.display-middle.search-chrome-collapsed.kw-open:not(.kw-chrome-collapsed):not(.kw-fs-open) #filterWrap{
    height:var(--portable-menu-h,min(44dvh,22rem))!important;
    max-height:min(52dvh,28rem)!important
  }
}
@media(orientation:portrait){
  body.catalog-portable.display-sides:not(.display-middle).kw-open:not(.kw-chrome-collapsed):not(.search-chrome-collapsed):not(.dual-fs-open){
    grid-template-columns:minmax(0,var(--portable-lw,42%)) minmax(0,1fr)!important;
    grid-template-rows:auto minmax(0,var(--portable-menu-h,1fr)) minmax(0,1fr)!important
  }
}
@media(orientation:landscape){
  body.catalog-portable.display-sides:not(.display-middle).kw-open:not(.kw-chrome-collapsed):not(.search-chrome-collapsed):not(.ac-fs-open):not(.kw-fs-open),
  body.catalog-portable.display-sides.dual-fs-open,
  body.catalog-portable.display-sides.ac-fs-open.kw-fs-open{
    grid-template-columns:minmax(0,var(--portable-lw,42%)) minmax(0,1fr)!important;
    grid-template-rows:auto minmax(0,1fr)!important
  }
}
"""

PLACE_OLD = """  hide(split);hide(sep);
  if(!document.body.classList.contains('layout-edit')){
    if(typeof placeCatalogJumpStack==='function')placeCatalogJumpStack();
    return;
  }
  var oneMenuFs=(document.body.classList.contains('ac-fs-open')&&!document.body.classList.contains('kw-fs-open'))||(document.body.classList.contains('kw-fs-open')&&!document.body.classList.contains('ac-fs-open'));
  if(oneMenuFs){
    /* one-menu Sides fullscreen: no resize stripe over the filled pane */
  }else if(fs){
    if(m.both&&ch&&fw){
      var left=flip?fw:ch;
      var r=left.getBoundingClientRect();
      bar(sep,true,{x:r.right});
    }
  }else if(sides&&middle){
    if(m.both&&ch){
      var rm=ch.getBoundingClientRect();
      bar(sep,true,{x:rm.right});
      bar(split,false,{x:rm.left,w:rm.width,y:rm.bottom});
    }else if(m.searchOn&&ch){
      var rs=ch.getBoundingClientRect();
      bar(split,false,{x:rs.left,w:rs.width,y:rs.bottom});
    }else if(m.kwOn&&fw){
      var rk=fw.getBoundingClientRect();
      bar(sep,false,{x:rk.left,w:rk.width,y:rk.bottom});
    }
  }else if(sides){
    if(portrait&&m.both&&ch&&fw){
      var topPane=flip?fw:ch;
      var stack=flip?fw:ch;
      var rt=topPane.getBoundingClientRect();
      var rst=stack.getBoundingClientRect();
      bar(split,false,{x:rt.left,w:rt.width,y:rt.bottom});
      bar(sep,true,{x:flip?rst.left:rst.right});
    }else if(!portrait&&m.both&&ch&&fw){
      var lp=flip?fw:ch;
      bar(sep,true,{x:lp.getBoundingClientRect().right});
    }else if(m.searchOn&&!m.kwOn&&ch){
      var rc=ch.getBoundingClientRect();
      bar(split,true,{x:flip?rc.left:rc.right});
    }else if(!m.searchOn&&m.kwOn&&fw){
      var rf=fw.getBoundingClientRect();
      bar(sep,true,{x:flip?rf.right:rf.left});
    }
  }
  var ix=document.getElementById('catalogIndex');
  var ixH=document.getElementById('indexHeight');
  if(ixH&&ix&&!ix.classList.contains('is-collapsed')&&sides){
    ixH.style.setProperty('display','block','important');
    ixH.style.setProperty('pointer-events','auto','important');
  }"""

PLACE_NEW = """  hide(split);hide(sep);
  var main=document.getElementById('catalogMain');
  var ix=document.getElementById('catalogIndex');
  var ixH=document.getElementById('indexHeight');
  var showIx=document.body.classList.contains('layout-edit')&&ix&&!ix.classList.contains('is-collapsed')&&!ix.classList.contains('is-embedded')&&(sides||middle);
  if(ixH){
    ixH.style.setProperty('display',showIx?'block':'none','important');
    ixH.style.setProperty('pointer-events',showIx?'auto':'none','important');
  }
  if(!document.body.classList.contains('layout-edit')){
    if(typeof placeCatalogJumpStack==='function')placeCatalogJumpStack();
    return;
  }
  function vis(el){
    if(!el)return false;
    var cs=getComputedStyle(el);
    if(cs.display==='none'||cs.visibility==='hidden')return false;
    var r=el.getBoundingClientRect();
    return r.width>12&&r.height>12;
  }
  function sharedEdge(a,b){
    if(!vis(a)||!vis(b))return null;
    var ra=a.getBoundingClientRect(),rb=b.getBoundingClientRect(),tol=36;
    if(Math.abs(ra.right-rb.left)<=tol)return {vert:true,x:ra.right,y:Math.max(ra.top,rb.top)};
    if(Math.abs(rb.right-ra.left)<=tol)return {vert:true,x:rb.right,y:Math.max(ra.top,rb.top)};
    if(Math.abs(ra.bottom-rb.top)<=tol)return {vert:false,x:Math.max(ra.left,rb.left),w:Math.min(ra.right,rb.right)-Math.max(ra.left,rb.left),y:ra.bottom};
    if(Math.abs(rb.bottom-ra.top)<=tol)return {vert:false,x:Math.max(ra.left,rb.left),w:Math.min(ra.right,rb.right)-Math.max(ra.left,rb.left),y:rb.bottom};
    return null;
  }
  var eSC=sharedEdge(ch,main);
  var eKC=sharedEdge(fw,main);
  var eSK=sharedEdge(ch,fw);
  if(eSC)bar(split,eSC.vert,eSC);
  else if(eSK&&!eKC)bar(split,eSK.vert,eSK);
  if(eKC)bar(sep,eKC.vert,eKC);
  else if(eSK&&eSC)bar(sep,eSK.vert,eSK);
  else if(eSK&&!eSC)bar(sep,eSK.vert,eSK);
  // #region agent log
  try{
    fetch('http://127.0.0.1:7529/ingest/1cf46354-1d61-4c80-bd72-a340f1db1b51',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'c00e3e'},body:JSON.stringify({sessionId:'c00e3e',runId:'post-fix',hypothesisId:'S',location:'portable:placeHandles',message:'inner seps',data:{eSC:!!eSC,eKC:!!eKC,eSK:!!eSK,scV:eSC&&eSC.vert,kcV:eKC&&eKC.vert,skV:eSK&&eSK.vert,searchOn:!!m.searchOn,kwOn:!!m.kwOn,sides:sides,middle:middle,fs:fs,portrait:portrait,edit:true},timestamp:Date.now()})}).catch(function(){});
  }catch(eDbgS){}
  // #endregion"""

DRAG_OLD = """      var horizP=(which==='split')&&(midP||(portP&&mP.both));
      var paneP=horizP?(which==='split'?chP:fwP):(mP.both?(flipP?fwP:chP):(mP.searchOn?chP:fwP));
      if(!paneP)return;
      var rP=paneP.getBoundingClientRect();
      var tP=e.currentTarget||e.target;
      drag={portable:true,horiz:horizP,which:which,x:e.clientX,y:e.clientY,w:rP.width,h:rP.height,flip:flipP,prop:(mP.searchOn&&!mP.kwOn)?'--portable-lw':((!mP.searchOn&&mP.kwOn)?'--portable-rw':'--portable-lw'),id:e.pointerId};"""

DRAG_NEW = """      var tP=e.currentTarget||e.target;
      var horizP=!!(tP&&tP.classList&&tP.classList.contains('port-stripe-h'));
      var paneP=horizP?(which==='sep'&&mP.kwOn&&!mP.searchOn?fwP:chP):(which==='sep'&&mP.kwOn&&!mP.searchOn?fwP:(mP.searchOn?chP:fwP));
      if(!paneP)paneP=chP||fwP;
      if(!paneP)return;
      var rP=paneP.getBoundingClientRect();
      var propP=horizP?'--portable-menu-h':((which==='sep'&&mP.kwOn&&!mP.searchOn)?'--portable-rw':'--portable-lw');
      drag={portable:true,horiz:horizP,which:which,x:e.clientX,y:e.clientY,w:rP.width,h:rP.height,flip:flipP,prop:propP,id:e.pointerId};"""

STRIPE_SKIP_OLD = """      if(window.CATALOG_PORTABLE&&mark==='content'){
        n.st.hidden=true;n.h.classList.remove('has-hover-overflow');
        document.body.classList.remove('has-hover-overflow-content');
        // #region agent log
        try{
          if(!window._dbgDot||Date.now()-window._dbgDot>1200){
            window._dbgDot=Date.now();
            fetch('http://127.0.0.1:7529/ingest/1cf46354-1d61-4c80-bd72-a340f1db1b51',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'c00e3e'},body:JSON.stringify({sessionId:'c00e3e',runId:'post-fix',hypothesisId:'G',location:'portable:hover-content',message:'content overlay suppressed',data:{showWould:show,stHidden:true,gutter:(sc.offsetWidth||0)-(sc.clientWidth||0)},timestamp:Date.now()})}).catch(function(){});
          }
        }catch(eDbgG){}
        // #endregion
        return;
      }
"""

STRIPE_SKIP_NEW = ""

BIND_OLD = """  if(window.CATALOG_PORTABLE){
    window.syncMainHoverStripe=function(){};
    window.bindMainHoverStripe=function(){};
  }else{
    window.syncMainHoverStripe=bindStripe('catalogMain','catalogMain','content');
    window.bindMainHoverStripe=window.bindHover_content||function(){if(window.syncMainHoverStripe)window.syncMainHoverStripe();};
  }"""

BIND_NEW = """  window.syncMainHoverStripe=bindStripe('catalogMain','catalogMain','content');
  window.bindMainHoverStripe=window.bindHover_content||function(){if(window.syncMainHoverStripe)window.syncMainHoverStripe();};"""

HIDE_THEMED_OLD = """  body.catalog-portable #catalogMainHoverStripe,
  body.catalog-portable #catalogMain>.hover-scroll-stripe{display:none!important}
  body.catalog-portable.has-hover-overflow-content #catalogMainHoverStripe.hover-scroll-fixed:not([hidden]){display:none!important}"""

HIDE_THEMED_NEW = """  body.catalog-portable #catalogMain>.hover-scroll-stripe{display:none!important}"""


def patch_one(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    n = 0
    if CSS_MARK not in text:
        needle = "  body.catalog-portable.display-middle:not(.ac-fs-open) #acList{\n    overflow-y:auto!important;min-height:0!important;flex:1 1 auto!important\n  }\n}\n</style>"
        if needle not in text:
            raise SystemExit(f"CSS insert missing in {path.name}")
        text = text.replace(needle, needle.replace("</style>", CSS_ADD + "</style>"), 1)
        n += 1
    pairs = [
        (PLACE_OLD, PLACE_NEW),
        (DRAG_OLD, DRAG_NEW),
        (STRIPE_SKIP_OLD, STRIPE_SKIP_NEW),
        (BIND_OLD, BIND_NEW),
        (HIDE_THEMED_OLD, HIDE_THEMED_NEW),
    ]
    for old, new in pairs:
        if old not in text:
            raise SystemExit(f"Missing snippet in {path.name}:\n{old[:160]!r}")
        c = text.count(old)
        text = text.replace(old, new)
        n += c
    path.write_text(text, encoding="utf-8")
    print(f"{path.name}: {n} replacements")


def main() -> None:
    for p in FILES:
        patch_one(p)


if __name__ == "__main__":
    main()
