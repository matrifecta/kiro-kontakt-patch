#!/usr/bin/env python3
from pathlib import Path

FILES = [
    Path("/home/phnx/kiro-kontakt-patch/public/catalogs/DS-CATALOG.html"),
    Path("/home/phnx/kiro-kontakt-patch/public/catalogs/DS-CATALOG-portable.html"),
    Path("/home/phnx/kiro-kontakt-patch/public/catalogs/KONTAKT-CATALOG.html"),
    Path("/home/phnx/kiro-kontakt-patch/public/catalogs/KONTAKT-CATALOG-portable.html"),
    Path("/home/phnx/kiro-kontakt-patch/kiro/specs/kontakt-workspace-drive-dirty-fix/artifacts/build-ds-catalog-html.sh"),
    Path("/home/phnx/kiro-kontakt-patch/kiro/specs/kontakt-workspace-drive-dirty-fix/artifacts/build-kontakt-catalog-html.sh"),
]

A_OLD = (
    "display:-webkit-box;-webkit-box-orient:vertical;"
    "-webkit-line-clamp:var(--index-name-lines,2);line-clamp:var(--index-name-lines,2)"
)
A_NEW = (
    "display:block;-webkit-line-clamp:unset;line-clamp:unset;"
    "max-height:calc(1.35em * var(--index-name-lines,2))"
)

GRID_OLD = "grid-auto-flow:row;align-content:start;flex:1 1 auto;min-height:0;"
GRID_NEW = "grid-auto-flow:row;align-items:start;align-content:start;grid-auto-rows:min-content;flex:1 1 auto;min-height:0;"

SIDES_INDEX_COL = (
    "  body.display-sides #catalogIndex{position:sticky;"
)
SIDES_INDEX_COL_PRE = (
    "  body.display-sides .index,body.display-sides #catalogIndexList{"
    "columns:none!important;column-width:auto!important;column-count:1!important;column-fill:auto!important"
    "}\n"
    "  body.display-sides #catalogIndex{position:sticky;"
)

STRIPE_CSS_OLD = (
    ".search-ac-shell.has-ac-overflow>.ac-scroll-stripe:hover .ac-scroll-thumb,"
    ".search-ac-shell.has-ac-overflow>.ac-scroll-stripe.is-dragging .ac-scroll-thumb"
    "{width:7px;opacity:.92;transform:scaleY(1.08);cursor:grabbing}"
)
STRIPE_CSS_NEW = STRIPE_CSS_OLD + (
    "\n.hover-scroll-stripe{position:absolute;top:4px;right:3px;bottom:4px;width:12px;z-index:28;"
    "display:none;pointer-events:none;touch-action:none;-webkit-user-select:none;user-select:none;box-sizing:border-box}"
    "\n.hover-scroll-stripe[hidden]{display:none!important}"
    "\n.hover-scroll-host.has-hover-overflow>.hover-scroll-stripe:not([hidden]){display:block;pointer-events:auto}"
    "\n.hover-scroll-thumb{position:absolute;right:1px;width:3px;min-height:1.15rem;border-radius:999px;"
    "background:var(--accent-instrument);opacity:.4;box-shadow:0 0 0 1px var(--border);cursor:grab;"
    "touch-action:none;transform-origin:right center;transition:width .14s ease,opacity .14s ease,transform .14s ease}"
    "\n.hover-scroll-host.has-hover-overflow>.hover-scroll-stripe:hover .hover-scroll-thumb,"
    ".hover-scroll-host.has-hover-overflow>.hover-scroll-stripe.is-dragging .hover-scroll-thumb"
    "{width:7px;opacity:.92;transform:scaleY(1.08);cursor:grabbing}"
    "\nbody.display-sides #catalogMain,body.display-sides #catalogIndex{position:relative}"
)

STRIPE_JS = r'''
/* hover-scroll-stripe: Content + Index */
(function(){
  function bindStripe(hostId, scrollId, mark){
    var drag=null,raf=0,bound=false;
    function host(){return document.getElementById(hostId);}
    function scroller(){return document.getElementById(scrollId)||host();}
    function ensure(){
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
    function sync(){
      var n=ensure();
      if(!n)return;
      var sc=n.sc,max=Math.max(0,sc.scrollHeight-sc.clientHeight);
      var show=max>8;
      n.h.classList.toggle('has-hover-overflow',show);
      n.st.hidden=!show;
      if(!show){n.st.classList.remove('is-dragging');return;}
      var trackH=Math.max(16,n.st.clientHeight||(sc.clientHeight-8));
      var thumbH=Math.max(22,Math.round((sc.clientHeight/Math.max(1,sc.scrollHeight))*trackH));
      if(thumbH>trackH)thumbH=trackH;
      var range=Math.max(1,trackH-thumbH);
      n.th.style.height=thumbH+'px';
      n.th.style.top=Math.round((sc.scrollTop/Math.max(1,max))*range)+'px';
    }
    function schedule(){
      if(raf)cancelAnimationFrame(raf);
      raf=requestAnimationFrame(function(){raf=0;sync();});
    }
    function yToScroll(sc,st,clientY){
      var r=st.getBoundingClientRect();
      var th=st.querySelector('.hover-scroll-thumb');
      var thH=th?th.offsetHeight:22;
      var y=clientY-r.top-thH/2;
      var range=Math.max(1,r.height-thH);
      sc.scrollTop=Math.max(0,Math.min(1,y/range))*Math.max(1,sc.scrollHeight-sc.clientHeight);
    }
    function bind(){
      var n=ensure();
      if(!n)return;
      if(bound)return;
      bound=true;
      n.sc.addEventListener('scroll',schedule,{passive:true});
      n.st.addEventListener('pointerdown',function(e){
        var n2=ensure();
        if(!n2||n2.st.hidden)return;
        e.preventDefault();e.stopPropagation();
        n2.st.classList.add('is-dragging');
        try{n2.st.setPointerCapture(e.pointerId);}catch(err){}
        drag={sc:n2.sc,st:n2.st,id:e.pointerId};
        yToScroll(n2.sc,n2.st,e.clientY);
        schedule();
      });
      n.st.addEventListener('pointermove',function(e){
        if(!drag||e.pointerId!==drag.id)return;
        yToScroll(drag.sc,drag.st,e.clientY);
      });
      function end(e){
        if(!drag||(e&&e.pointerId!==drag.id))return;
        drag.st.classList.remove('is-dragging');
        try{drag.st.releasePointerCapture(drag.id);}catch(err){}
        drag=null;schedule();
      }
      n.st.addEventListener('pointerup',end);
      n.st.addEventListener('pointercancel',end);
      if(typeof ResizeObserver!=='undefined'){
        var ro=new ResizeObserver(schedule);
        ro.observe(n.sc);ro.observe(n.h);
      }
      window.addEventListener('resize',schedule);
      if(document.body){
        try{new MutationObserver(function(){if(!bound)bind();schedule();}).observe(document.body,{childList:true,subtree:true});}catch(err){}
      }
      // #region agent log
      try{fetch('http://127.0.0.1:7529/ingest/1cf46354-1d61-4c80-bd72-a340f1db1b51',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'f491c2'},body:JSON.stringify({sessionId:'f491c2',runId:'post-fix',hypothesisId:'H8',location:'hoverStripe',message:'stripe-bound',data:{mark:mark,host:hostId,scroll:scrollId},timestamp:Date.now()})}).catch(function(){});}catch(err){}
      // #endregion
    }
    function boot(){bind();schedule();}
    if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot);
    else boot();
    return schedule;
  }
  window.syncMainHoverStripe=bindStripe('catalogMain','catalogMain','content');
  window.syncIndexHoverStripe=bindStripe('catalogIndex','catalogIndexList','index');
})();
'''

MARKER = "window.syncAcScrollStripe=schedule;\n})();"


def do(t, src, dst, label, name):
    c = t.count(src)
    print(" ", name, label, ("x" + str(c)) if c else "MISS")
    if c:
        t = t.replace(src, dst)
    return t


def main():
    for p in FILES:
        t = p.read_text(encoding="utf-8", errors="replace")
        print("FILE", p.name)
        t = do(t, A_OLD, A_NEW, "no-webkit-box", p.name)
        t = do(t, GRID_OLD, GRID_NEW, "grid-rows", p.name)
        if SIDES_INDEX_COL in t and "body.display-sides .index,body.display-sides #catalogIndexList{" not in t:
            t = t.replace(SIDES_INDEX_COL, SIDES_INDEX_COL_PRE, 1)
            print(" ", p.name, "sides-cols-kill")
        else:
            print(" ", p.name, "sides-cols-kill skip")
        t = do(t, STRIPE_CSS_OLD, STRIPE_CSS_NEW, "stripe-css", p.name)
        if MARKER in t and "bindStripe('catalogMain'" not in t:
            t = t.replace(MARKER, MARKER + "\n" + STRIPE_JS, 1)
            print(" ", p.name, "stripe-js")
        else:
            print(" ", p.name, "stripe-js skip/miss", MARKER in t)
        p.write_text(t, encoding="utf-8")
        print("  wrote")


if __name__ == "__main__":
    main()
