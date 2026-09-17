#!/usr/bin/env python3
"""Park ↑/↓ in a fixed #catalogJumpStack on body (content-pane bottom-right)."""
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

CSS_OLD = (
    "  body.display-sides a.bottom,body.display-sides a.top{display:inline-flex!important;align-items:center;justify-content:center;position:sticky!important;z-index:26;float:none;clear:none;align-self:flex-end;flex:0 0 auto;box-sizing:border-box;margin-right:.6rem}\n"
    "  body.display-sides #catalogBottomJump{position:sticky;top:var(--index-bar-h,2.75rem);z-index:11;height:0;margin:0;padding:0;overflow:visible;pointer-events:none;align-self:stretch;flex:0 0 0;display:flex;justify-content:flex-end;width:100%;box-sizing:border-box}\n"
    "  body.display-sides #catalogBottomJump>a.bottom,body.display-sides a.bottom{position:relative!important;top:.12rem!important;margin:0 .65rem 0 0;z-index:11;align-self:flex-end;flex:0 0 auto;pointer-events:auto}\n"
    "  body.display-sides #catalogIndex>a.bottom{position:absolute!important;top:var(--index-bar-h,2.75rem);right:.65rem;left:auto;margin:0!important;z-index:11;order:0;flex:0 0 auto;pointer-events:auto}\n"
    "  body.display-sides a.top{bottom:1rem;top:auto;margin-bottom:1rem}"
)

CSS_NEW = (
    "  body.display-sides a.bottom,body.display-sides a.top{display:inline-flex!important;align-items:center;justify-content:center;position:sticky!important;z-index:26;float:none;clear:none;align-self:flex-end;flex:0 0 auto;box-sizing:border-box;margin-right:.6rem}\n"
    "  #catalogJumpStack{display:none}\n"
    "  body.display-sides #catalogJumpStack{position:fixed;z-index:26;display:flex;flex-direction:column;align-items:flex-end;gap:.35rem;pointer-events:none}\n"
    "  body.display-sides #catalogJumpStack>a.top,body.display-sides #catalogJumpStack>a.bottom{position:relative!important;top:auto!important;bottom:auto!important;margin:0!important;pointer-events:auto;z-index:26}"
)

HOLD_OLD = """  var topBtn=document.querySelector('a.top');
  var hold=document.getElementById('catalogBottomJump');
  if(!hold){
    hold=document.createElement('div');
    hold.id='catalogBottomJump';
    hold.className='catalog-bottom-jump';
  }
  if(bot.parentNode!==hold)hold.appendChild(bot);
  var ixPark=document.getElementById('catalogIndex');
  if(ixPark&&ixPark.parentNode===w){
    if(hold.parentNode!==w||hold.previousElementSibling!==ixPark){
      if(ixPark.nextSibling)w.insertBefore(hold,ixPark.nextSibling);
      else w.appendChild(hold);
    }
  }else if(hold.parentNode!==w||w.firstElementChild!==hold)w.insertBefore(hold,w.firstChild);
  if(typeof syncBottomBelowIndex==='function')syncBottomBelowIndex();
  if(typeof syncIndexEmbedBtn==='function')syncIndexEmbedBtn();
  if(typeof window.bindMainHoverStripe==='function')window.bindMainHoverStripe();
  else if(typeof window.syncMainHoverStripe==='function')window.syncMainHoverStripe();
  if(typeof reviveEntryCovers==='function')reviveEntryCovers();
  if(topBtn){if(topBtn.parentNode!==w||w.lastElementChild!==topBtn)w.appendChild(topBtn);}
}"""

HOLD_NEW = """  var topBtn=document.querySelector('a.top');
  var stack=document.getElementById('catalogJumpStack');
  if(!stack){
    stack=document.createElement('div');
    stack.id='catalogJumpStack';
  }
  if(stack.parentNode!==document.body)document.body.appendChild(stack);
  if(topBtn&&topBtn.parentNode!==stack)stack.appendChild(topBtn);
  if(bot.parentNode!==stack)stack.appendChild(bot);
  if(topBtn&&bot.previousElementSibling!==topBtn)stack.insertBefore(topBtn,bot);
  var oldHold=document.getElementById('catalogBottomJump');
  if(oldHold&&oldHold!==stack&&!oldHold.firstElementChild)oldHold.remove();
  if(typeof syncBottomBelowIndex==='function')syncBottomBelowIndex();
  if(typeof syncIndexEmbedBtn==='function')syncIndexEmbedBtn();
  if(typeof window.bindMainHoverStripe==='function')window.bindMainHoverStripe();
  else if(typeof window.syncMainHoverStripe==='function')window.syncMainHoverStripe();
  if(typeof reviveEntryCovers==='function')reviveEntryCovers();
  if(typeof placeCatalogJumpStack==='function')placeCatalogJumpStack();
  // #region agent log
  try{var _st=document.getElementById('catalogJumpStack');var _top=_st&&_st.querySelector('a.top');var _bot=_st&&_st.querySelector('a.bottom');fetch('http://127.0.0.1:7529/ingest/1cf46354-1d61-4c80-bd72-a340f1db1b51',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'f491c2'},body:JSON.stringify({sessionId:'f491c2',runId:'post-fix',hypothesisId:'H-jump-fixed',location:'ensureCatalogMain',message:'jump-stack-park',data:{parentId:_st&&_st.parentNode&&(_st.parentNode.id||_st.parentNode.tagName||''),topParent:_top&&_top.parentNode&&_top.parentNode.id,botParent:_bot&&_bot.parentNode&&_bot.parentNode.id,order:_st&&_st.firstElementChild&&_st.firstElementChild.className,inMain:!!(w.contains(_st)),oldHold:!!document.getElementById('catalogBottomJump')},timestamp:Date.now()})}).catch(function(){});}catch(err){}
  // #endregion
}"""

PLACE_FN = """function placeCatalogJumpStack(){
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
  // #region agent log
  try{
    var topBtn=stack.querySelector('a.top');
    var botBtn=stack.querySelector('a.bottom');
    var tr=topBtn&&topBtn.getBoundingClientRect();
    var br=botBtn&&botBtn.getBoundingClientRect();
    var sr=stack.getBoundingClientRect();
    var pos=getComputedStyle(stack).position;
    var parentId=stack.parentNode?(stack.parentNode.id||stack.parentNode.tagName||''):'';
    var st=main?main.scrollTop:null;
    var botBelowTop=!!(tr&&br&&br.top>=tr.bottom-1);
    var sig=parentId+'|'+pos+'|'+botBelowTop;
    var n=window.__jumpStackLogN||0;
    var lastSt=window.__jumpStackLogSt;
    var stJump=lastSt==null||(st!=null&&Math.abs(st-lastSt)>=80);
    if(n<3||stJump||window.__jumpStackLogSig!==sig){
      window.__jumpStackLogN=n+1;
      window.__jumpStackLogSt=st;
      window.__jumpStackLogSig=sig;
      fetch('http://127.0.0.1:7529/ingest/1cf46354-1d61-4c80-bd72-a340f1db1b51',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'f491c2'},body:JSON.stringify({sessionId:'f491c2',runId:'post-fix',hypothesisId:'H-jump-fixed',location:'placeCatalogJumpStack',message:'jump-stack-place',data:{stackPos:pos,stackTop:Math.round(sr.top),topBtnTop:tr?Math.round(tr.top):null,botBtnTop:br?Math.round(br.top):null,botBelowTop:botBelowTop,parentId:parentId,mainScrollTop:st==null?null:Math.round(st),inMain:!!(main&&main.contains(stack)),displaySides:document.body.classList.contains('display-sides')},timestamp:Date.now()})}).catch(function(){});
    }
  }catch(err){}
  // #endregion
}
"""

CARD_OLD = """function cardMinPlace(){
  var d=document.getElementById('cardMinDock');
  if(!d)return;"""

CARD_NEW = """function cardMinPlace(){
  if(typeof placeCatalogJumpStack==='function')placeCatalogJumpStack();
  var d=document.getElementById('cardMinDock');
  if(!d)return;"""

LEAVE_OLD = """// #endregion
    return;
  }
  if(typeof clearChromeInlineLeftovers==='function')clearChromeInlineLeftovers();
  var portrait=typeof isPortraitDesktopSides==='function'&&isPortraitDesktopSides();"""

LEAVE_NEW = """// #endregion
    if(typeof placeCatalogJumpStack==='function')placeCatalogJumpStack();
    return;
  }
  if(typeof clearChromeInlineLeftovers==='function')clearChromeInlineLeftovers();
  var portrait=typeof isPortraitDesktopSides==='function'&&isPortraitDesktopSides();"""

END_OLD = """    fetch('http://127.0.0.1:7529/ingest/1cf46354-1d61-4c80-bd72-a340f1db1b51',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'f491c2'},body:JSON.stringify({sessionId:'f491c2',runId:'pre-fix',hypothesisId:'A',location:'applySidesCols',message:'sides-pane-geometry',data:{vw:innerWidth,vh:innerHeight,searchOn:searchOn,kwOn:kwOn,kwOpen:document.body.classList.contains('kw-open'),ixCollapsed:!!(ix&&ix.classList.contains('is-collapsed')),cm:cmb,sc:scb,fw:fwb,ix:ixb,top:tb,hasBottom:!!bot,overlapL:!!(searchOn&&cmb&&scb&&cmb.x<scb.r-2),overlapR:!!(kwOn&&cmb&&fwb&&cmb.r>fwb.x+2),liOver:!!(liB&&ixb&&liB.right>ixb.r+1),liWW:liCS&&liCS.whiteSpace,pathOver:!!(pB&&cmb&&pB.right>cmb.r+1),pathWW:pCS&&pCS.whiteSpace,topOutside:!!(tb&&cmb&&(tb.r>cmb.r+4||tb.x<cmb.x-4)),lw:(document.body.style.getPropertyValue('--sides-lw')||''),rw:(document.body.style.getPropertyValue('--sides-rw')||'')},timestamp:Date.now()})}).catch(function(){});
  })();
  // #endregion
}
function placeSidesHandles(){"""

END_NEW = """    fetch('http://127.0.0.1:7529/ingest/1cf46354-1d61-4c80-bd72-a340f1db1b51',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'f491c2'},body:JSON.stringify({sessionId:'f491c2',runId:'pre-fix',hypothesisId:'A',location:'applySidesCols',message:'sides-pane-geometry',data:{vw:innerWidth,vh:innerHeight,searchOn:searchOn,kwOn:kwOn,kwOpen:document.body.classList.contains('kw-open'),ixCollapsed:!!(ix&&ix.classList.contains('is-collapsed')),cm:cmb,sc:scb,fw:fwb,ix:ixb,top:tb,hasBottom:!!bot,overlapL:!!(searchOn&&cmb&&scb&&cmb.x<scb.r-2),overlapR:!!(kwOn&&cmb&&fwb&&cmb.r>fwb.x+2),liOver:!!(liB&&ixb&&liB.right>ixb.r+1),liWW:liCS&&liCS.whiteSpace,pathOver:!!(pB&&cmb&&pB.right>cmb.r+1),pathWW:pCS&&pCS.whiteSpace,topOutside:!!(tb&&cmb&&(tb.r>cmb.r+4||tb.x<cmb.x-4)),lw:(document.body.style.getPropertyValue('--sides-lw')||''),rw:(document.body.style.getPropertyValue('--sides-rw')||'')},timestamp:Date.now()})}).catch(function(){});
  })();
  // #endregion
  if(typeof placeCatalogJumpStack==='function')placeCatalogJumpStack();
}
function placeSidesHandles(){"""

ENSURE_DECL = "function ensureCatalogMain(){"


def once(text, old, new, label, path):
    n = text.count(old)
    if n != 1:
        raise SystemExit(f"{path.name}: {label} count={n} expected 1")
    return text.replace(old, new, 1)


def patch(path: Path):
    text = path.read_text(encoding="utf-8")
    if "function placeCatalogJumpStack()" in text and "id='catalogJumpStack'" in text:
        print(f"SKIP already patched {path}")
        return
    text = once(text, CSS_OLD, CSS_NEW, "CSS", path)
    text = once(text, CARD_OLD, CARD_NEW, "cardMinPlace", path)
    text = once(text, HOLD_OLD, HOLD_NEW, "ensureCatalogMain-park", path)
    text = once(text, ENSURE_DECL, PLACE_FN + ENSURE_DECL, "placeCatalogJumpStack-fn", path)
    text = once(text, LEAVE_OLD, LEAVE_NEW, "applySidesCols-leave", path)
    text = once(text, END_OLD, END_NEW, "applySidesCols-end", path)
    path.write_text(text, encoding="utf-8")
    print(f"OK {path}")


def main():
    for p in FILES:
        if not p.exists():
            raise SystemExit(f"missing {p}")
        patch(p)


if __name__ == "__main__":
    main()
