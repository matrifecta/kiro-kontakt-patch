#!/usr/bin/env python3
"""Portable: desktop-like jump stack, pane gutters, in-pane cards, tile covers."""
from pathlib import Path

ROOT = Path("/home/phnx/kiro-kontakt-patch")
FILES = [
    ROOT / "public/catalogs/DS-CATALOG-portable.html",
    ROOT / "public/catalogs/KONTAKT-CATALOG-portable.html",
]

CSS_MARK = "/* fix-PORTABLE-JUMP-GAP-CARDS:"
CSS_ADD = r"""
/* fix-PORTABLE-JUMP-GAP-CARDS: jump at catalog pane, tiny gutters, cards/covers in-pane */
@media all{
  body.catalog-portable.display-sides,
  body.catalog-portable.display-sides.display-middle,
  body.catalog-portable.display-fs{
    column-gap:var(--sides-pane-gap,6px)!important;
    row-gap:var(--sides-pane-gap,6px)!important
  }
  body.catalog-portable.display-sides #catalogIndex:not(.is-embedded){
    margin:var(--sides-pane-gap,6px)!important;max-width:100%;min-width:0;box-sizing:border-box
  }
  body.catalog-portable #catalogJumpStack{display:none!important}
  body.catalog-portable.display-sides #catalogJumpStack{
    display:flex!important;position:fixed!important;z-index:45!important;
    flex-direction:column;align-items:flex-end;gap:.35rem;pointer-events:auto;
    max-width:min(100%,12rem)
  }
  body.catalog-portable.display-fs #catalogJumpStack,
  body.catalog-portable.display-sides.dual-fs-open #catalogJumpStack,
  body.catalog-portable.display-sides.ac-fs-open.kw-fs-open #catalogJumpStack{
    display:none!important
  }
  body.catalog-portable.display-sides #catalogJumpStack>a.top,
  body.catalog-portable.display-sides #catalogJumpStack>a.bottom{
    display:inline-flex!important;position:relative!important;
    top:auto!important;bottom:auto!important;right:auto!important;left:auto!important;
    margin:0!important;pointer-events:auto;z-index:45
  }
  body.catalog-portable.display-sides #catalogMain{
    overflow-x:hidden!important;overflow-y:auto!important;
    min-width:0!important;max-width:100%!important;
    box-sizing:border-box!important;padding:.65rem;
    position:relative
  }
  body.catalog-portable.display-sides #catalogMain .catalog-body,
  body.catalog-portable.display-sides #catalogMain .loc-group,
  body.catalog-portable.display-sides #catalogMain .entry:not(.highlight),
  body.catalog-portable.display-sides #catalogMain .catalog-index,
  body.catalog-portable.display-sides #catalogMain .catalog-doc-note{
    max-width:100%!important;min-width:0!important;box-sizing:border-box!important
  }
  body.catalog-portable.display-sides #catalogMain .entry:not(.highlight){
    overflow:hidden;outline-offset:0
  }
  body.catalog-portable.display-sides #catalogMain .entry.selected:not(.highlight){
    outline:2px solid var(--accent-instrument);outline-offset:-2px;
    box-shadow:inset 0 0 0 2px var(--accent-instrument-bg)
  }
  body.catalog-portable.display-sides #catalogMain .entry:not(.highlight) .lib-name,
  body.catalog-portable.display-sides #catalogMain .entry:not(.highlight) h3,
  body.catalog-portable.display-sides #catalogMain .entry:not(.highlight) .path,
  body.catalog-portable.display-sides #catalogMain .entry:not(.highlight) .card-actions{
    max-width:100%;min-width:0;box-sizing:border-box
  }
  body.catalog-portable.display-sides #catalogMain .entry:not(.highlight) .card-actions{
    flex-wrap:wrap
  }
  body.catalog-portable:not(.chosen-preview-open) .entry:not(.highlight) .cover,
  body.catalog-portable .entry:not(.highlight):not(.selected) .cover{
    position:relative!important;display:block!important;
    width:100%!important;max-width:100%!important;min-width:0!important;
    height:auto!important;min-height:0!important;max-height:none!important;
    aspect-ratio:3/4!important;overflow:hidden!important;
    box-sizing:border-box!important;margin:.3rem 0;flex:0 0 auto
  }
  body.catalog-portable:not(.chosen-preview-open) .entry:not(.highlight) .cover img,
  body.catalog-portable .entry:not(.highlight):not(.selected) .cover img{
    position:absolute!important;inset:0!important;
    width:100%!important;height:100%!important;
    max-width:none!important;max-height:none!important;
    min-width:0!important;min-height:0!important;
    object-fit:cover!important;object-position:center center!important;
    display:block!important
  }
}
"""

PLACE_OLD = """function placeCatalogJumpStack(){
  var stack=document.getElementById('catalogJumpStack');
  var main=document.getElementById('catalogMain');
  if(!stack)return;
  if(!document.body.classList.contains('display-sides')||!main){
    stack.style.cssText='';
  }else{
    var r=main.getBoundingClientRect();
    var right=Math.max(6,Math.round((window.innerWidth||0)-r.right)+10);
    var bottom=Math.max(6,Math.round((window.innerHeight||0)-r.bottom)+12);
    stack.style.right=right+'px';
    stack.style.bottom=bottom+'px';
    stack.style.left='auto';
    stack.style.top='auto';
  }
}"""

PLACE_NEW = """function dbgPortableJumpGap(phase){
  // #region agent log
  try{
    var main=document.getElementById('catalogMain'),stack=document.getElementById('catalogJumpStack');
    var sc=document.getElementById('searchChrome'),fw=document.getElementById('filterWrap');
    var bot=stack&&stack.querySelector('a.bottom'),topB=stack&&stack.querySelector('a.top');
    var entries=[].slice.call(document.querySelectorAll('#catalogMain .entry:not(.highlight):not(.is-hidden)')).slice(0,2);
    function rb(el){if(!el)return null;var cs=getComputedStyle(el);if(cs.display==='none'||cs.visibility==='hidden')return null;var r=el.getBoundingClientRect();return {l:Math.round(r.left),t:Math.round(r.top),r:Math.round(r.right),b:Math.round(r.bottom),w:Math.round(r.width),h:Math.round(r.height)};}
    var cards=entries.map(function(el){
      var cover=el.querySelector('.cover'),img=cover&&cover.querySelector('img');
      var cr=rb(cover),er=rb(el);
      return {entry:er,cover:cr,ratio:(cr&&cr.w)?+(cr.h/cr.w).toFixed(3):null,imgFit:img?getComputedStyle(img).objectFit:'',imgOverflow:!!(img&&cover&&(img.getBoundingClientRect().width>cover.getBoundingClientRect().width+1||img.getBoundingClientRect().height>cover.getBoundingClientRect().height+1))};
    });
    var mr=rb(main),sr=rb(sc),kr=rb(fw),br=rb(bot),tr=rb(topB),st=rb(stack);
    fetch('http://127.0.0.1:7529/ingest/1cf46354-1d61-4c80-bd72-a340f1db1b51',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'c00e3e'},body:JSON.stringify({sessionId:'c00e3e',runId:'post-fix',hypothesisId:'H-JUMP1',location:'catalog:dbgPortableJumpGap',message:'jump-gap-cards',data:{phase:String(phase||''),vw:innerWidth||0,vh:innerHeight||0,cur:typeof currentDisplay!=='undefined'?String(currentDisplay):'',sides:document.body.classList.contains('display-sides'),middle:document.body.classList.contains('display-middle'),fs:document.body.classList.contains('display-fs'),main:mr,search:sr,kw:kr,gapSM:sr&&mr?Math.round(mr.l-sr.r):null,gapMK:mr&&kr?Math.round(kr.l-mr.r):null,gapSK:sr&&kr?Math.round(kr.l-sr.r):null,colGap:getComputedStyle(document.body).columnGap,rowGap:getComputedStyle(document.body).rowGap,stack:st,bot:br,top:tr,inMain:!!(mr&&st&&st.l>=mr.l-2&&st.r<=mr.r+2&&st.t>=mr.t-2&&st.b<=mr.b+2),cards:cards},timestamp:Date.now()})}).catch(function(){});
  }catch(eJ){}
  // #endregion
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
    stack.style.cssText='';
  }else{
    var padR=parseFloat(mainCs.paddingRight)||10;
    var padB=parseFloat(mainCs.paddingBottom)||10;
    var insetR=Math.max(8,Math.round(padR));
    var insetB=Math.max(8,Math.round(padB));
    var right=Math.max(6,Math.round((window.innerWidth||0)-r.right)+insetR);
    var bottom=Math.max(6,Math.round((window.innerHeight||0)-r.bottom)+insetB);
    stack.style.right=right+'px';
    stack.style.bottom=bottom+'px';
    stack.style.left='auto';
    stack.style.top='auto';
  }
  if(typeof dbgPortableJumpGap==='function')dbgPortableJumpGap('placeJump');
}"""

COVER_OLD = """  body.catalog-portable .entry:not(.highlight):not(.selected) .cover{
    position:relative;display:block!important;width:100%;aspect-ratio:3/4;
    height:auto!important;min-height:0!important;max-height:none!important;
    overflow:hidden;border-radius:6px;background:var(--bg)
  }
  body.catalog-portable .entry:not(.highlight):not(.selected) .cover img{
    position:absolute;inset:0;width:100%!important;height:100%!important;max-height:none!important;min-height:0!important;
    object-fit:cover!important;object-position:center
  }"""

COVER_NEW = """  body.catalog-portable:not(.chosen-preview-open) .entry:not(.highlight) .cover,
  body.catalog-portable .entry:not(.highlight):not(.selected) .cover{
    position:relative!important;display:block!important;width:100%!important;max-width:100%!important;
    aspect-ratio:3/4!important;height:auto!important;min-height:0!important;max-height:none!important;
    overflow:hidden!important;border-radius:6px;background:var(--bg);box-sizing:border-box!important
  }
  body.catalog-portable:not(.chosen-preview-open) .entry:not(.highlight) .cover img,
  body.catalog-portable .entry:not(.highlight):not(.selected) .cover img{
    position:absolute!important;inset:0!important;width:100%!important;height:100%!important;
    max-width:none!important;max-height:none!important;min-width:0!important;min-height:0!important;
    object-fit:cover!important;object-position:center
  }"""

BAR_OLD = """    if(vert){
      el.style.cssText='display:block;position:fixed;top:'+top+'px;bottom:0;left:'+Math.round(box.x-4)+'px;width:8px;min-width:8px;max-width:8px;height:auto;z-index:90;margin:0;transform:none;pointer-events:auto;cursor:col-resize;background:var(--bg-surface);';
    }else{
      el.style.cssText='display:block;position:fixed;left:'+Math.round(box.x)+'px;width:'+Math.round(box.w)+'px;top:'+Math.round(box.y-4)+'px;height:8px;min-height:8px;max-height:8px;min-width:0;max-width:none;bottom:auto;z-index:90;margin:0;transform:none;pointer-events:auto;cursor:row-resize;background:var(--bg-surface);';
    }"""

BAR_NEW = """    var paneGap=parseFloat(getComputedStyle(document.documentElement).getPropertyValue('--sides-pane-gap'))||6;
    var half=Math.max(4,Math.round(paneGap/2));
    if(vert){
      el.style.cssText='display:block;position:fixed;top:'+top+'px;bottom:0;left:'+Math.round(box.x-half)+'px;width:8px;min-width:8px;max-width:8px;height:auto;z-index:90;margin:0;transform:none;pointer-events:auto;cursor:col-resize;background:var(--bg-surface);';
    }else{
      el.style.cssText='display:block;position:fixed;left:'+Math.round(box.x)+'px;width:'+Math.round(box.w)+'px;top:'+Math.round(box.y-half)+'px;height:8px;min-height:8px;max-height:8px;min-width:0;max-width:none;bottom:auto;z-index:90;margin:0;transform:none;pointer-events:auto;cursor:row-resize;background:var(--bg-surface);';
    }"""

STRIPE_END_OLD = """  // #region agent log
  if(typeof dbgMobileUi==='function')dbgMobileUi('portable-stripe',{hyp:'H-STRIPE'});
  // #endregion
}"""

STRIPE_END_NEW = """  if(typeof placeCatalogJumpStack==='function')placeCatalogJumpStack();
  // #region agent log
  if(typeof dbgMobileUi==='function')dbgMobileUi('portable-stripe',{hyp:'H-STRIPE'});
  if(typeof dbgPortableJumpGap==='function')dbgPortableJumpGap('portable-stripe');
  // #endregion
}"""


def once(text, old, new, label, path):
    n = text.count(old)
    if n == 1:
        return text.replace(old, new, 1)
    if n == 0 and new in text:
        print(f"  skip {path.name} {label}")
        return text
    raise SystemExit(f"{path.name}: {label} count={n}")


def patch(path: Path):
    t = path.read_text(encoding="utf-8")
    t = once(t, PLACE_OLD, PLACE_NEW, "placeJump", path)
    t = once(t, COVER_OLD, COVER_NEW, "cover", path)
    t = once(t, BAR_OLD, BAR_NEW, "stripe-bar", path)
    t = once(t, STRIPE_END_OLD, STRIPE_END_NEW, "stripe-end", path)
    if CSS_MARK not in t:
        if "</style></head>" not in t:
            raise SystemExit(f"{path.name}: no style close")
        t = t.replace("</style></head>", CSS_ADD + "\n</style></head>", 1)
        print(f"  css {path.name}")
    else:
        print(f"  skip {path.name} css")
    path.write_text(t, encoding="utf-8")
    print("ok", path.name)


def main():
    for p in FILES:
        if not p.exists():
            raise SystemExit(f"missing {p}")
        patch(p)


if __name__ == "__main__":
    main()
