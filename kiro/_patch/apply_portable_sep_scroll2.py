#!/usr/bin/env python3
"""Portable: hittable inner seps in all combos; native content scrollbar off."""
from pathlib import Path

ROOT = Path("/home/phnx/kiro-kontakt-patch")
FILES = [
    ROOT / "public/catalogs/KONTAKT-CATALOG-portable.html",
    ROOT / "public/catalogs/DS-CATALOG-portable.html",
]

CSS_OLD = """@media(orientation:landscape){
  body.catalog-portable.display-sides:not(.display-middle).kw-open:not(.kw-chrome-collapsed):not(.search-chrome-collapsed):not(.ac-fs-open):not(.kw-fs-open),
  body.catalog-portable.display-sides.dual-fs-open,
  body.catalog-portable.display-sides.ac-fs-open.kw-fs-open{
    grid-template-columns:minmax(0,var(--portable-lw,42%)) minmax(0,1fr)!important;
    grid-template-rows:auto minmax(0,1fr)!important
  }
}
"""

CSS_NEW = CSS_OLD + r"""
/* fix-PORTABLE-SEP-SCROLL2: inner seps keep size; FS dual drag; middle height var; native gutter 0 */
@media all{
  body.catalog-portable #catalogMain,
  body.catalog-portable.display-sides #catalogMain,
  body.catalog-portable.display-middle #catalogMain,
  body.catalog-portable.display-sides.display-middle #catalogMain,
  body.catalog-portable.display-content #catalogMain{
    scrollbar-width:none!important;-ms-overflow-style:none!important;scrollbar-gutter:auto!important
  }
  body.catalog-portable #catalogMain::-webkit-scrollbar,
  body.catalog-portable #catalogMain::-webkit-scrollbar-thumb,
  body.catalog-portable #catalogMain::-webkit-scrollbar-track,
  body.catalog-portable.display-sides #catalogMain::-webkit-scrollbar,
  body.catalog-portable.display-sides.display-middle #catalogMain::-webkit-scrollbar{
    display:none!important;width:0!important;height:0!important;background:transparent!important
  }
  body.catalog-portable.layout-edit #searchSplit.port-stripe-h,
  body.catalog-portable.layout-edit #dualFsSep.port-stripe-h,
  body.catalog-portable.display-sides.layout-edit #searchSplit.port-stripe-h,
  body.catalog-portable.display-sides.display-middle.layout-edit #searchSplit.port-stripe-h,
  body.catalog-portable.display-sides.kw-chrome-collapsed.layout-edit #searchSplit.port-stripe-h,
  body.catalog-portable.display-sides.search-chrome-collapsed.layout-edit #dualFsSep.port-stripe-h{
    display:block!important;pointer-events:auto!important;position:fixed!important;
    width:var(--port-h-w,100%)!important;min-width:48px!important;max-width:none!important;
    height:8px!important;min-height:8px!important;max-height:8px!important;
    cursor:row-resize!important;z-index:130!important
  }
  body.catalog-portable.layout-edit #searchSplit.port-stripe-v,
  body.catalog-portable.layout-edit #dualFsSep.port-stripe-v,
  body.catalog-portable.display-sides.layout-edit #searchSplit.port-stripe-v,
  body.catalog-portable.display-sides.layout-edit #dualFsSep.port-stripe-v,
  body.catalog-portable.display-sides.display-middle.layout-edit #dualFsSep.port-stripe-v{
    display:block!important;pointer-events:auto!important;position:fixed!important;
    width:8px!important;min-width:8px!important;max-width:8px!important;
    height:auto!important;min-height:0!important;max-height:none!important;
    cursor:col-resize!important;z-index:130!important
  }
  body.catalog-portable.layout-edit.ac-fs-open.kw-fs-open #searchSplit.port-stripe-v,
  body.catalog-portable.layout-edit.ac-fs-open.kw-fs-open #dualFsSep.port-stripe-v,
  body.catalog-portable.layout-edit.dual-fs-open #searchSplit.port-stripe-v,
  body.catalog-portable.layout-edit.dual-fs-open #dualFsSep.port-stripe-v,
  body.catalog-portable.layout-edit.ac-fs-open.kw-fs-open #searchSplit.port-stripe-h,
  body.catalog-portable.layout-edit.dual-fs-open #searchSplit.port-stripe-h,
  body.catalog-portable.layout-edit.display-fs.dual-fs-open #dualFsSep{
    pointer-events:auto!important;display:block!important;z-index:130!important
  }
  body.catalog-portable.layout-edit.ac-fs-open:not(.kw-fs-open):not(.dual-fs-open) #searchSplit,
  body.catalog-portable.layout-edit.kw-fs-open:not(.ac-fs-open):not(.dual-fs-open) #dualFsSep,
  body.catalog-portable.layout-edit.ac-fs-open:not(.kw-fs-open):not(.dual-fs-open) #dualFsSep,
  body.catalog-portable.layout-edit.kw-fs-open:not(.ac-fs-open):not(.dual-fs-open) #searchSplit{
    display:none!important;pointer-events:none!important
  }
  body.catalog-portable.display-sides.display-middle:not(.ac-fs-open):not(.kw-fs-open):not(.search-chrome-collapsed) #searchChrome{
    height:var(--portable-menu-h,min(44dvh,22rem))!important;
    max-height:min(52dvh,28rem)!important;flex:0 0 auto!important;overflow:hidden!important
  }
  body.catalog-portable.display-sides.display-middle.search-chrome-collapsed.kw-open:not(.kw-chrome-collapsed):not(.kw-fs-open) #filterWrap{
    height:var(--portable-menu-h,min(44dvh,22rem))!important;
    max-height:min(52dvh,28rem)!important;flex:0 0 auto!important;overflow:hidden!important
  }
  body.catalog-portable.display-sides:not(.display-middle).search-chrome-collapsed.kw-open:not(.kw-chrome-collapsed):not(.kw-fs-open){
    grid-template-columns:minmax(0,var(--portable-rw,42%)) minmax(0,1fr)!important
  }
  body.catalog-portable.display-sides:not(.display-middle).sides-portrait-flip.search-chrome-collapsed.kw-open:not(.kw-chrome-collapsed):not(.kw-fs-open){
    grid-template-columns:minmax(0,1fr) minmax(0,var(--portable-rw,42%))!important
  }
  body.catalog-portable.display-fs.dual-fs-open,
  body.catalog-portable.display-fs.ac-fs-open.kw-fs-open{
    grid-template-columns:minmax(0,var(--portable-lw,42%)) minmax(0,1fr)!important
  }
}
@media(orientation:portrait){
  body.catalog-portable.display-sides.display-middle:not(.ac-fs-open):not(.kw-fs-open):not(.search-chrome-collapsed) #searchChrome,
  body.catalog-portable.display-sides.display-middle.search-chrome-collapsed.kw-open:not(.kw-chrome-collapsed):not(.kw-fs-open) #filterWrap{
    height:var(--portable-menu-h,min(44dvh,22rem))!important;
    max-height:min(52dvh,28rem)!important;flex:0 0 auto!important
  }
}
"""

CLAMP_OLD = """  var vh=window.innerHeight||800;
  var mh=parseInt(getComputedStyle(document.documentElement).getPropertyValue('--portable-menu-h'),10);
  if(mh&&mh>vh*0.55)document.documentElement.style.setProperty('--portable-menu-h',Math.round(vh*0.32)+'px');
}"""

CLAMP_NEW = """  var vh=window.innerHeight||800;
  var mh=parseInt(getComputedStyle(document.documentElement).getPropertyValue('--portable-menu-h'),10);
  if(mh&&mh>vh*0.55)document.documentElement.style.setProperty('--portable-menu-h',Math.round(vh*0.32)+'px');
  if(!mh&&document.body.classList.contains('display-middle')){
    document.documentElement.style.setProperty('--portable-menu-h',Math.round(Math.min(vh*0.36,22*16))+'px');
  }
}"""

BAR_OLD = """  function bar(el,vert,box){
    if(!el||!box)return;
    el.classList.toggle('port-stripe-v',!!vert);
    el.classList.toggle('port-stripe-h',!vert);
    var paneGap=parseFloat(getComputedStyle(document.documentElement).getPropertyValue('--sides-pane-gap'))||6;
    var half=Math.max(4,Math.round(paneGap/2));
    if(vert){
      el.style.cssText='position:fixed;top:'+top+'px;bottom:0;left:'+Math.round(box.x-half)+'px;width:8px;min-width:8px;max-width:8px;height:auto;z-index:90;margin:0;transform:none;pointer-events:auto;cursor:col-resize;background:var(--bg-surface);';el.style.setProperty('display','block','important');
    }else{
      el.style.cssText='position:fixed;left:'+Math.round(box.x)+'px;width:'+Math.round(box.w)+'px;top:'+Math.round(box.y-half)+'px;height:8px;min-height:8px;max-height:8px;min-width:0;max-width:none;bottom:auto;z-index:90;margin:0;transform:none;pointer-events:auto;cursor:row-resize;background:var(--bg-surface);';el.style.setProperty('display','block','important');
    }
    el.setAttribute('aria-orientation',vert?'vertical':'horizontal');
  }"""

BAR_NEW = """  function bar(el,vert,box){
    if(!el||!box)return;
    el.classList.toggle('port-stripe-v',!!vert);
    el.classList.toggle('port-stripe-h',!vert);
    var paneGap=parseFloat(getComputedStyle(document.documentElement).getPropertyValue('--sides-pane-gap'))||6;
    var half=Math.max(4,Math.round(paneGap/2));
    el.style.cssText='';
    el.style.setProperty('position','fixed','important');
    el.style.setProperty('margin','0','important');
    el.style.setProperty('transform','none','important');
    el.style.setProperty('pointer-events','auto','important');
    el.style.setProperty('z-index','130','important');
    el.style.setProperty('background','var(--bg-surface)','important');
    el.style.setProperty('display','block','important');
    if(vert){
      el.style.setProperty('top',top+'px','important');
      el.style.setProperty('bottom','0','important');
      el.style.setProperty('left',Math.round(box.x-half)+'px','important');
      el.style.setProperty('width','8px','important');
      el.style.setProperty('min-width','8px','important');
      el.style.setProperty('max-width','8px','important');
      el.style.setProperty('height','auto','important');
      el.style.setProperty('min-height','0','important');
      el.style.setProperty('max-height','none','important');
      el.style.setProperty('cursor','col-resize','important');
    }else{
      var hw=Math.max(48,Math.round(box.w||0));
      document.documentElement.style.setProperty('--port-h-w',hw+'px');
      el.style.setProperty('left',Math.round(box.x)+'px','important');
      el.style.setProperty('width',hw+'px','important');
      el.style.setProperty('min-width','48px','important');
      el.style.setProperty('max-width','none','important');
      el.style.setProperty('top',Math.round(box.y-half)+'px','important');
      el.style.setProperty('height','8px','important');
      el.style.setProperty('min-height','8px','important');
      el.style.setProperty('max-height','8px','important');
      el.style.setProperty('bottom','auto','important');
      el.style.setProperty('cursor','row-resize','important');
    }
    el.setAttribute('aria-orientation',vert?'vertical':'horizontal');
  }"""

EDGE_OLD = """  function sharedEdge(a,b){
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

EDGE_NEW = """  function ovX(a,b){return Math.min(a.right,b.right)-Math.max(a.left,b.left);}
  function ovY(a,b){return Math.min(a.bottom,b.bottom)-Math.max(a.top,b.top);}
  function sharedEdge(a,b){
    if(!vis(a)||!vis(b))return null;
    var ra=a.getBoundingClientRect(),rb=b.getBoundingClientRect(),tol=48;
    var vw=window.innerWidth||0,vh=window.innerHeight||0;
    var edge=null;
    if(Math.abs(ra.right-rb.left)<=tol&&ovY(ra,rb)>24)edge={vert:true,x:ra.right,y:Math.max(ra.top,rb.top)};
    else if(Math.abs(rb.right-ra.left)<=tol&&ovY(ra,rb)>24)edge={vert:true,x:rb.right,y:Math.max(ra.top,rb.top)};
    else if(Math.abs(ra.bottom-rb.top)<=tol&&ovX(ra,rb)>24)edge={vert:false,x:Math.max(ra.left,rb.left),w:ovX(ra,rb),y:ra.bottom};
    else if(Math.abs(rb.bottom-ra.top)<=tol&&ovX(ra,rb)>24)edge={vert:false,x:Math.max(ra.left,rb.left),w:ovX(ra,rb),y:rb.bottom};
    if(!edge)return null;
    if(edge.vert&&(edge.x<10||edge.x>vw-10))return null;
    if(!edge.vert&&(edge.y<top+4||edge.y>vh-10))return null;
    return edge;
  }
  var eSC=sharedEdge(ch,main);
  var eKC=sharedEdge(fw,main);
  var eSK=sharedEdge(ch,fw);
  function put(edge,useSplit){
    if(!edge)return;
    if(useSplit)bar(split,edge.vert,edge);
    else bar(sep,edge.vert,edge);
  }
  if(eSC&&eKC){put(eSC,true);put(eKC,false);}
  else if(eSC&&eSK){put(eSC,true);put(eSK,false);}
  else if(eKC&&eSK){put(eKC,false);put(eSK,true);}
  else if(eSC)put(eSC,true);
  else if(eKC)put(eKC,false);
  else if(eSK)put(eSK,true);
  // #region agent log
  try{
    var splitR=split&&split.getBoundingClientRect();
    var mainEl=document.getElementById('catalogMain');
    fetch('http://127.0.0.1:7529/ingest/1cf46354-1d61-4c80-bd72-a340f1db1b51',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'c00e3e'},body:JSON.stringify({sessionId:'c00e3e',runId:'post-fix',hypothesisId:'S',location:'portable:placeHandles',message:'inner seps',data:{eSC:!!eSC,eKC:!!eKC,eSK:!!eSK,scV:eSC&&eSC.vert,kcV:eKC&&eKC.vert,skV:eSK&&eSK.vert,searchOn:!!m.searchOn,kwOn:!!m.kwOn,sides:sides,middle:middle,fs:fs,portrait:portrait,edit:true,splitW:splitR?Math.round(splitR.width):0,splitH:splitR?Math.round(splitR.height):0,menuH:getComputedStyle(document.documentElement).getPropertyValue('--portable-menu-h').trim(),gutter:mainEl?((mainEl.offsetWidth||0)-(mainEl.clientWidth||0)):null,pe:split?getComputedStyle(split).pointerEvents:''},timestamp:Date.now()})}).catch(function(){});
  }catch(eDbgS){}
  // #endregion"""

DRAG_GUARD_OLD = """  function onDown(e,which){
    if(!document.body.classList.contains('display-sides'))return;
    if(!window.CATALOG_PORTABLE&&!document.body.classList.contains('layout-edit'))return;"""

DRAG_GUARD_NEW = """  function onDown(e,which){
    if(window.CATALOG_PORTABLE){
      if(!document.body.classList.contains('layout-edit'))return;
    }else{
      if(!document.body.classList.contains('display-sides'))return;
      if(!document.body.classList.contains('layout-edit'))return;
    }"""

STRIPE_OLD = """      if(mark==='content'){
        var mr0=sc.getBoundingClientRect();
        n.st.style.top=Math.round(mr0.top+4)+'px';
        n.st.style.left=Math.round(Math.max(0,mr0.right-15))+'px';
        n.st.style.height=Math.round(Math.max(16,mr0.height-8))+'px';
        n.st.style.right='auto';
        n.st.style.bottom='auto';
        n.st.style.width='12px';
      }"""

STRIPE_NEW = """      if(mark==='content'){
        if(window.CATALOG_PORTABLE){
          sc.style.setProperty('scrollbar-width','none','important');
          sc.style.setProperty('-ms-overflow-style','none','important');
        }
        var mr0=sc.getBoundingClientRect();
        n.st.style.top=Math.round(mr0.top+4)+'px';
        n.st.style.left=Math.round(Math.max(0,mr0.right-15))+'px';
        n.st.style.height=Math.round(Math.max(16,mr0.height-8))+'px';
        n.st.style.right='auto';
        n.st.style.bottom='auto';
        n.st.style.width='12px';
      }"""


def patch_one(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    n = 0
    pairs = [
        (CSS_OLD, CSS_NEW),
        (CLAMP_OLD, CLAMP_NEW),
        (BAR_OLD, BAR_NEW),
        (EDGE_OLD, EDGE_NEW),
        (DRAG_GUARD_OLD, DRAG_GUARD_NEW),
        (STRIPE_OLD, STRIPE_NEW),
    ]
    for old, new in pairs:
        if old not in text:
            raise SystemExit(f"Missing snippet in {path.name}:\n{old[:200]!r}")
        c = text.count(old)
        if c != 1:
            raise SystemExit(f"Expected 1 occurrence in {path.name}, got {c} for:\n{old[:120]!r}")
        text = text.replace(old, new, 1)
        n += 1
    path.write_text(text, encoding="utf-8")
    print(f"{path.name}: {n} replacements")


def main() -> None:
    for p in FILES:
        patch_one(p)


if __name__ == "__main__":
    main()
