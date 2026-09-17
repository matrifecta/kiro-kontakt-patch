#!/usr/bin/env python3
"""Fix Sides jump clicks, content hover stripe, and History menu (all 6 files)."""
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


def once(text, old, new, label, path):
    n = text.count(old)
    if n != 1:
        raise SystemExit(f"{path.name}: {label} count={n} expected 1")
    return text.replace(old, new, 1)


JUMP_CSS_OLD = (
    "  body.display-sides #catalogJumpStack{position:fixed;z-index:26;display:flex;flex-direction:column;align-items:flex-end;gap:.35rem;pointer-events:none}\n"
    "  body.display-sides #catalogJumpStack>a.top,body.display-sides #catalogJumpStack>a.bottom{position:relative!important;top:auto!important;bottom:auto!important;margin:0!important;pointer-events:auto;z-index:26}"
)
JUMP_CSS_NEW = (
    "  body.display-sides #catalogJumpStack{position:fixed;z-index:40;display:flex;flex-direction:column;align-items:flex-end;gap:.35rem;pointer-events:auto}\n"
    "  body.display-sides #catalogJumpStack>a.top,body.display-sides #catalogJumpStack>a.bottom{position:relative!important;top:auto!important;bottom:auto!important;margin:0!important;pointer-events:auto;z-index:40}"
)

STRIPE_CSS_OLD = "#catalogMain>.hover-scroll-stripe{z-index:8;top:4px}\n"
STRIPE_CSS_NEW = (
    "#catalogMain>.hover-scroll-stripe{z-index:8;top:4px}\n"
    "#catalogMainHoverStripe.hover-scroll-fixed{position:fixed!important;z-index:24;width:12px;margin:0;display:none;pointer-events:none}\n"
    "body.has-hover-overflow-content #catalogMainHoverStripe.hover-scroll-fixed:not([hidden]){display:block;pointer-events:auto}\n"
    "body.has-hover-overflow-content.is-content-hover #catalogMainHoverStripe .hover-scroll-thumb,"
    "#catalogMainHoverStripe.hover-scroll-fixed.is-dragging .hover-scroll-thumb{width:7px;opacity:.92;transform:scaleY(1.08);cursor:grabbing}\n"
)

HIST_CSS_OLD = " .ac-history-cloud{position:fixed;z-index:320;"
HIST_CSS_NEW = " .ac-history-cloud{position:fixed;z-index:420;"

ENSURE_STRIPE_OLD = """    function ensure(){
      var h=host(),sc=scroller();
      if(!h||!sc)return null;
      h.classList.add('hover-scroll-host');
      var st=h.querySelector(':scope > .hover-scroll-stripe');
      if(!st){
        st=document.createElement('div');
        st.className='hover-scroll-stripe';
        st.id=hostId+'HoverStripe';
        st.hidden=true;
        var th=document.createElement('div');
        th.className='hover-scroll-thumb';
        st.appendChild(th);
        h.appendChild(st);
      }
      return {h:h,sc:sc,st:st,th:st.querySelector('.hover-scroll-thumb')};
    }
"""
ENSURE_STRIPE_NEW = """    function ensure(){
      var h=host(),sc=scroller();
      if(!h||!sc)return null;
      h.classList.add('hover-scroll-host');
      var st=document.getElementById(hostId+'HoverStripe')||h.querySelector(':scope > .hover-scroll-stripe');
      var parkBody=mark==='content';
      if(!st){
        st=document.createElement('div');
        st.className='hover-scroll-stripe';
        st.id=hostId+'HoverStripe';
        st.hidden=true;
        var th=document.createElement('div');
        th.className='hover-scroll-thumb';
        st.appendChild(th);
      }
      if(parkBody){
        st.classList.add('hover-scroll-fixed');
        if(st.parentNode!==document.body)document.body.appendChild(st);
      }else if(st.parentNode!==h){
        h.appendChild(st);
      }
      return {h:h,sc:sc,st:st,th:st.querySelector('.hover-scroll-thumb')};
    }
"""

SYNC_STRIPE_OLD = """      n.h.classList.toggle('has-hover-overflow',show);
      n.st.hidden=!show;
      if(!show){n.st.classList.remove('is-dragging');return;}
      var trackH=Math.max(16,n.st.clientHeight||(sc.clientHeight-8));
"""
SYNC_STRIPE_NEW = """      n.h.classList.toggle('has-hover-overflow',show);
      if(mark==='content')document.body.classList.toggle('has-hover-overflow-content',show);
      n.st.hidden=!show;
      if(!show){n.st.classList.remove('is-dragging');return;}
      if(mark==='content'){
        var mr0=sc.getBoundingClientRect();
        n.st.style.top=Math.round(mr0.top+4)+'px';
        n.st.style.left=Math.round(Math.max(0,mr0.right-15))+'px';
        n.st.style.height=Math.round(Math.max(16,mr0.height-8))+'px';
        n.st.style.right='auto';
        n.st.style.bottom='auto';
        n.st.style.width='12px';
      }
      var trackH=Math.max(16,n.st.clientHeight||(sc.clientHeight-8));
"""

STRIPE_LOG_OLD = "runId:'pre-fix',hypothesisId:'H-SB1',location:'hoverStripe.sync',message:'content-stripe',data:{mark:mark,show:show,max:max,scrollH:sc.scrollHeight,clientH:sc.clientHeight,hidden:!!n.st.hidden,disp:cs.display,pos:cs.position,stH:Math.round(sr.height),stT:Math.round(sr.top),stR:Math.round(sr.right),mainH:Math.round(mr.height),mainR:Math.round(mr.right),ovJump:ovJump,parentIsScroller:n.st.parentNode===sc}"
STRIPE_LOG_NEW = "runId:'post-fix',hypothesisId:'H-SB1',location:'hoverStripe.sync',message:'content-stripe',data:{mark:mark,show:show,max:max,scrollH:sc.scrollHeight,clientH:sc.clientHeight,hidden:!!n.st.hidden,disp:cs.display,pos:cs.position,stH:Math.round(sr.height),stT:Math.round(sr.top),stR:Math.round(sr.right),mainH:Math.round(mr.height),mainR:Math.round(mr.right),ovJump:ovJump,parentIsScroller:n.st.parentNode===sc,parkedOnBody:n.st.parentNode===document.body}"

BIND_HOVER_OLD = """      if(bound){schedule();return;}
      bound=true;
      n.sc.addEventListener('scroll',schedule,{passive:true});
"""
BIND_HOVER_NEW = """      if(bound){schedule();return;}
      bound=true;
      if(mark==='content'&&n.h&&!n.h.dataset.hsHoverBound){
        n.h.dataset.hsHoverBound='1';
        n.h.addEventListener('pointerenter',function(){document.body.classList.add('is-content-hover');});
        n.h.addEventListener('pointerleave',function(){if(!drag)document.body.classList.remove('is-content-hover');});
      }
      n.sc.addEventListener('scroll',schedule,{passive:true});
"""

HIST_EL_OLD = """function historyCloudEl(){return document.getElementById('historyCloud');}
function historyBtnEl(){return document.getElementById('searchHistory');}
"""
HIST_EL_NEW = """function historyCloudEl(){return document.getElementById('historyCloud');}
function parkHistoryCloud(){
  var cloud=historyCloudEl();
  if(cloud&&cloud.parentNode!==document.body)document.body.appendChild(cloud);
  return cloud;
}
function historyBtnEl(){return document.getElementById('searchHistory');}
"""

SHOW_HIST_OLD = """  if(!cloud||!btn)return;
  if(typeof renderHistoryPicks==='function')renderHistoryPicks();
  cloud.hidden=false;
"""
SHOW_HIST_NEW = """  if(!cloud||!btn)return;
  cloud=parkHistoryCloud()||cloud;
  if(typeof renderHistoryPicks==='function')renderHistoryPicks();
  cloud.hidden=false;
  window.__histIgnoreUntil=Date.now()+400;
"""

BIND_HIST_OLD = """(function bindHistoryCloud(){
  var btn=historyBtnEl(),yes=document.getElementById('historyYes'),no=document.getElementById('historyNo'),all=document.getElementById('historyAll'),searchAll=document.getElementById('historySearchAll'),cloud=historyCloudEl();
"""
BIND_HIST_NEW = """(function bindHistoryCloud(){
  if(typeof parkHistoryCloud==='function')parkHistoryCloud();
  var btn=historyBtnEl(),yes=document.getElementById('historyYes'),no=document.getElementById('historyNo'),all=document.getElementById('historyAll'),searchAll=document.getElementById('historySearchAll'),cloud=historyCloudEl();
"""

DISMISS_OLD = """    if(!cloud||cloud.hidden)return;
    if(e.target.closest&&(e.target.closest('#historyCloud')||e.target.closest('#searchHistory')))return;
"""
DISMISS_NEW = """    if(!cloud||cloud.hidden)return;
    if(window.__histIgnoreUntil&&Date.now()<window.__histIgnoreUntil)return;
    if(e.target.closest&&(e.target.closest('#historyCloud')||e.target.closest('#searchHistory')||e.target.closest('#searchHistoryWrap')))return;
"""

PARK_JUMP_OLD = """  if(typeof placeCatalogJumpStack==='function')placeCatalogJumpStack();
  // #region agent log
  try{var _st=document.getElementById('catalogJumpStack');"""
PARK_JUMP_NEW = """  if(typeof placeCatalogJumpStack==='function')placeCatalogJumpStack();
  if(typeof bindCatalogTop==='function')bindCatalogTop();
  // #region agent log
  try{var _st=document.getElementById('catalogJumpStack');"""

BIND_TOP_OLD = """function bindCatalogTop(){
  var top=document.querySelector('a.top');
  if(!top||top.dataset.sidesTopBound)return;
  top.dataset.sidesTopBound='1';
  top.addEventListener('click',function(e){
    if(!document.body.classList.contains('display-sides'))return;
    e.preventDefault();
    var cm=document.getElementById('catalogMain');
    var ix=document.getElementById('catalogIndex');
    var ixColBefore=!!(ix&&ix.classList.contains('is-collapsed'));
    var searchBefore=document.body.classList.contains('search-chrome-collapsed');
    var kwBefore=document.body.classList.contains('kw-chrome-collapsed');
    var kwOpenBefore=document.body.classList.contains('kw-open');
    if(ix)ix.dataset.goingTop='1';
    if(cm){try{cm.scrollTo({top:0,behavior:'smooth'});}catch(err){cm.scrollTop=0;}}
    // #region agent log
    fetch('http://127.0.0.1:7529/ingest/1cf46354-1d61-4c80-bd72-a340f1db1b51',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'f491c2'},body:JSON.stringify({sessionId:'f491c2',runId:'post-fix',hypothesisId:'H8',location:'bindCatalogTop',message:'sides-top-click',data:{cmTop:cm?Math.round(cm.scrollTop):null,ixH:ix?Math.round(ix.getBoundingClientRect().height):null},timestamp:Date.now()})}).catch(function(){});
    // #endregion
    // #region agent log
    fetch('http://127.0.0.1:7529/ingest/1cf46354-1d61-4c80-bd72-a340f1db1b51',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'f491c2'},body:JSON.stringify({sessionId:'f491c2',runId:'pre-fix',hypothesisId:'D',location:'bindCatalogTop',message:'sides-top-state-change',data:{ixColBefore:ixColBefore,ixColAfter:!!(ix&&ix.classList.contains('is-collapsed')),searchBefore:searchBefore,searchAfter:document.body.classList.contains('search-chrome-collapsed'),kwBefore:kwBefore,kwAfter:document.body.classList.contains('kw-chrome-collapsed'),kwOpenBefore:kwOpenBefore,kwOpenAfter:document.body.classList.contains('kw-open'),hasBottom:!!document.querySelector('a.bottom,#catalogBottom'),topText:(top&&top.textContent)||''},timestamp:Date.now()})}).catch(function(){});
    // #endregion
  });
  var bot=document.querySelector('a.bottom');
  if(bot&&!bot.dataset.sidesBotBound){
    bot.dataset.sidesBotBound='1';
    bot.addEventListener('click',function(e){
      if(!document.body.classList.contains('display-sides'))return;
      e.preventDefault();
      var cm=document.getElementById('catalogMain');
      var ix=document.getElementById('catalogIndex');
      var ixColBefore=!!(ix&&ix.classList.contains('is-collapsed'));
      var searchBefore=document.body.classList.contains('search-chrome-collapsed');
      var kwBefore=document.body.classList.contains('kw-chrome-collapsed');
      if(cm){try{cm.scrollTo({top:cm.scrollHeight,behavior:'smooth'});}catch(err){cm.scrollTop=cm.scrollHeight;}}
      // #region agent log
      fetch('http://127.0.0.1:7529/ingest/1cf46354-1d61-4c80-bd72-a340f1db1b51',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'f491c2'},body:JSON.stringify({sessionId:'f491c2',runId:'post-fix',hypothesisId:'D',location:'bindCatalogTop',message:'sides-bottom-state-change',data:{ixColBefore:ixColBefore,ixColAfter:!!(ix&&ix.classList.contains('is-collapsed')),searchBefore:searchBefore,searchAfter:document.body.classList.contains('search-chrome-collapsed'),kwBefore:kwBefore,kwAfter:document.body.classList.contains('kw-chrome-collapsed'),hasBottom:true},timestamp:Date.now()})}).catch(function(){});
      // #endregion
    });
  }
}
"""

BIND_TOP_NEW = """function bindCatalogTop(){
  function goTop(e,topEl){
    if(!document.body.classList.contains('display-sides'))return;
    if(e){e.preventDefault();e.stopPropagation();}
    var cm=document.getElementById('catalogMain');
    var ix=document.getElementById('catalogIndex');
    var ixColBefore=!!(ix&&ix.classList.contains('is-collapsed'));
    var searchBefore=document.body.classList.contains('search-chrome-collapsed');
    var kwBefore=document.body.classList.contains('kw-chrome-collapsed');
    var kwOpenBefore=document.body.classList.contains('kw-open');
    if(ix)ix.dataset.goingTop='1';
    if(cm){try{cm.scrollTo({top:0,behavior:'smooth'});}catch(err){cm.scrollTop=0;}}
    // #region agent log
    fetch('http://127.0.0.1:7529/ingest/1cf46354-1d61-4c80-bd72-a340f1db1b51',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'f491c2'},body:JSON.stringify({sessionId:'f491c2',runId:'post-fix',hypothesisId:'H8',location:'bindCatalogTop',message:'sides-top-click',data:{cmTop:cm?Math.round(cm.scrollTop):null,ixH:ix?Math.round(ix.getBoundingClientRect().height):null},timestamp:Date.now()})}).catch(function(){});
    // #endregion
    // #region agent log
    fetch('http://127.0.0.1:7529/ingest/1cf46354-1d61-4c80-bd72-a340f1db1b51',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'f491c2'},body:JSON.stringify({sessionId:'f491c2',runId:'pre-fix',hypothesisId:'D',location:'bindCatalogTop',message:'sides-top-state-change',data:{ixColBefore:ixColBefore,ixColAfter:!!(ix&&ix.classList.contains('is-collapsed')),searchBefore:searchBefore,searchAfter:document.body.classList.contains('search-chrome-collapsed'),kwBefore:kwBefore,kwAfter:document.body.classList.contains('kw-chrome-collapsed'),kwOpenBefore:kwOpenBefore,kwOpenAfter:document.body.classList.contains('kw-open'),hasBottom:!!document.querySelector('a.bottom,#catalogBottom'),topText:(topEl&&topEl.textContent)||''},timestamp:Date.now()})}).catch(function(){});
    // #endregion
  }
  function goBot(e){
    if(!document.body.classList.contains('display-sides'))return;
    if(e){e.preventDefault();e.stopPropagation();}
    var cm=document.getElementById('catalogMain');
    var ix=document.getElementById('catalogIndex');
    var ixColBefore=!!(ix&&ix.classList.contains('is-collapsed'));
    var searchBefore=document.body.classList.contains('search-chrome-collapsed');
    var kwBefore=document.body.classList.contains('kw-chrome-collapsed');
    if(cm){try{cm.scrollTo({top:cm.scrollHeight,behavior:'smooth'});}catch(err){cm.scrollTop=cm.scrollHeight;}}
    // #region agent log
    fetch('http://127.0.0.1:7529/ingest/1cf46354-1d61-4c80-bd72-a340f1db1b51',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'f491c2'},body:JSON.stringify({sessionId:'f491c2',runId:'post-fix',hypothesisId:'D',location:'bindCatalogTop',message:'sides-bottom-state-change',data:{ixColBefore:ixColBefore,ixColAfter:!!(ix&&ix.classList.contains('is-collapsed')),searchBefore:searchBefore,searchAfter:document.body.classList.contains('search-chrome-collapsed'),kwBefore:kwBefore,kwAfter:document.body.classList.contains('kw-chrome-collapsed'),hasBottom:true},timestamp:Date.now()})}).catch(function(){});
    // #endregion
  }
  var stack=document.getElementById('catalogJumpStack');
  if(stack&&!stack.dataset.sidesJumpBound){
    stack.dataset.sidesJumpBound='1';
    stack.addEventListener('click',function(e){
      var t=e.target&&e.target.closest&&e.target.closest('a.top,a.bottom');
      if(!t)return;
      if(t.classList.contains('top'))goTop(e,t);
      else goBot(e);
    },true);
  }
  var top=document.querySelector('a.top');
  if(top&&!top.dataset.sidesTopBound&&!(stack&&stack.contains(top))){
    top.dataset.sidesTopBound='1';
    top.addEventListener('click',function(e){goTop(e,top);});
  }
  var bot=document.querySelector('a.bottom');
  if(bot&&!bot.dataset.sidesBotBound&&!(stack&&stack.contains(bot))){
    bot.dataset.sidesBotBound='1';
    bot.addEventListener('click',function(e){goBot(e);});
  }
}
"""


def patch(path: Path):
    text = path.read_text(encoding="utf-8")
    if "function parkHistoryCloud()" in text and "hover-scroll-fixed" in text and "sidesJumpBound" in text:
        print(f"SKIP already patched {path}")
        return
    text = once(text, JUMP_CSS_OLD, JUMP_CSS_NEW, "jump-css", path)
    text = once(text, STRIPE_CSS_OLD, STRIPE_CSS_NEW, "stripe-css", path)
    text = once(text, HIST_CSS_OLD, HIST_CSS_NEW, "hist-css", path)
    text = once(text, ENSURE_STRIPE_OLD, ENSURE_STRIPE_NEW, "stripe-ensure", path)
    text = once(text, SYNC_STRIPE_OLD, SYNC_STRIPE_NEW, "stripe-sync", path)
    text = once(text, STRIPE_LOG_OLD, STRIPE_LOG_NEW, "stripe-log", path)
    text = once(text, BIND_HOVER_OLD, BIND_HOVER_NEW, "stripe-hover-bind", path)
    text = once(text, HIST_EL_OLD, HIST_EL_NEW, "hist-park-fn", path)
    text = once(text, SHOW_HIST_OLD, SHOW_HIST_NEW, "hist-show", path)
    text = once(text, BIND_HIST_OLD, BIND_HIST_NEW, "hist-bind", path)
    text = once(text, DISMISS_OLD, DISMISS_NEW, "hist-dismiss", path)
    text = once(text, PARK_JUMP_OLD, PARK_JUMP_NEW, "jump-rebind", path)
    text = once(text, BIND_TOP_OLD, BIND_TOP_NEW, "bindCatalogTop", path)
    path.write_text(text, encoding="utf-8")
    print(f"OK {path}")


def main():
    for p in FILES:
        if not p.exists():
            raise SystemExit(f"missing {p}")
        patch(p)
    for p in FILES:
        t = p.read_text(encoding="utf-8")
        for needle in (
            "parkHistoryCloud",
            "hover-scroll-fixed",
            "sidesJumpBound",
            "has-hover-overflow-content",
            "__histIgnoreUntil",
            "parkedOnBody",
        ):
            if needle not in t:
                raise SystemExit(f"{p.name} missing {needle}")
    print("all ok")


if __name__ == "__main__":
    main()
