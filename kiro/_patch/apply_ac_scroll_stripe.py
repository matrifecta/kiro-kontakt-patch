#!/usr/bin/env python3
"""Bound Search AC list in Sides + theme hovering scroll stripe. Sync six catalog files."""
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

SIDES_OLD = (
    "body.display-sides #acShell,body.display-sides #acShell.open,body.display-sides #acList,body.display-sides #acList.open"
    "{position:relative!important;inset:auto!important;width:auto!important;height:auto!important;max-height:none!important;"
    "flex:1 1 auto;min-height:0;overflow-y:auto!important;-webkit-overflow-scrolling:touch;overscroll-behavior:contain;"
    "touch-action:pan-y;box-shadow:none;border:0}"
)
SIDES_NEW = (
    "body.display-sides #acShell,body.display-sides #acShell.open"
    "{position:relative!important;inset:auto!important;width:auto!important;flex:1 1 0%!important;min-height:0!important;"
    "max-height:none;overflow:hidden!important;display:flex!important;flex-direction:column!important;"
    "box-shadow:none;border:0}"
    "body.display-sides #acList.search-autocomplete,body.display-sides #acList.search-autocomplete.open"
    "{position:relative!important;inset:auto!important;width:auto!important;flex:1 1 0%!important;min-height:0!important;"
    "max-height:none!important;overflow-x:hidden!important;overflow-y:auto!important;-webkit-overflow-scrolling:touch;"
    "overscroll-behavior:contain;touch-action:pan-y;box-shadow:none;border:0;scrollbar-width:none!important;"
    "-ms-overflow-style:none!important}"
)

OPEN_OLD = ".search-autocomplete.open{display:block}"
OPEN_NEW = """.search-autocomplete.open{display:block}
.search-autocomplete{scrollbar-width:none!important;-ms-overflow-style:none!important}
.search-autocomplete::-webkit-scrollbar{display:none!important;width:0!important;height:0!important}
.ac-scroll-stripe{position:absolute;top:0;right:3px;width:12px;z-index:12;display:none;pointer-events:none;touch-action:none;-webkit-user-select:none;user-select:none;box-sizing:border-box}
.ac-scroll-stripe[hidden]{display:none!important}
.search-ac-shell.has-ac-overflow>.ac-scroll-stripe:not([hidden]){display:block;pointer-events:auto}
.ac-scroll-thumb{position:absolute;right:1px;width:3px;min-height:1.15rem;border-radius:999px;background:var(--accent-instrument);opacity:.4;box-shadow:0 0 0 1px var(--border);cursor:grab;touch-action:none;transform-origin:right center;transition:width .14s ease,opacity .14s ease,transform .14s ease}
.search-ac-shell.has-ac-overflow>.ac-scroll-stripe:hover .ac-scroll-thumb,.search-ac-shell.has-ac-overflow>.ac-scroll-stripe.is-dragging .ac-scroll-thumb{width:7px;opacity:.92;transform:scaleY(1.08);cursor:grabbing}"""

HTML_OLD = 'class="search-autocomplete" id="acList"></div>'
HTML_NEW = (
    'class="search-autocomplete" id="acList"></div>'
    '<div class="ac-scroll-stripe" id="acScrollStripe" hidden>'
    '<div class="ac-scroll-thumb" id="acScrollThumb"></div></div>'
)

MOBILE_OLD = (
    "body.display-sides #searchChrome{flex:0 0 auto;height:auto!important;max-height:min(38dvh,20rem)!important;"
    "overflow-y:auto!important;border-right:0!important;display:flex!important;flex-direction:column!important}"
)
MOBILE_NEW = (
    "body.display-sides #searchChrome{flex:0 0 auto;height:auto!important;max-height:min(38dvh,20rem)!important;"
    "overflow:hidden!important;border-right:0!important;display:flex!important;flex-direction:column!important}"
    "body.display-sides #searchCol,body.display-sides #searchCol .search-strip-anchor"
    "{flex:1 1 auto;min-height:0;display:flex;flex-direction:column;overflow:hidden;max-height:100%}"
)

SHOW_OLD = "acList.innerHTML=html;acList.classList.toggle('open',html.length>0);"
SHOW_NEW = (
    "acList.innerHTML=html;acList.classList.toggle('open',html.length>0);"
    "if(window.syncAcScrollStripe)window.syncAcScrollStripe();"
)

JS_MARK = "searchInput.addEventListener('input',function(){"
JS_BLOCK = r"""/* ac-scroll-stripe */
(function(){
  var bound=false,drag=null,raf=0;
  function gid(id){return document.getElementById(id);}
  function ensure(){
    var sh=gid('acShell'),ac=gid('acList');
    if(!sh||!ac)return null;
    var st=gid('acScrollStripe');
    if(!st){
      st=document.createElement('div');
      st.id='acScrollStripe';
      st.className='ac-scroll-stripe';
      st.hidden=true;
      var th0=document.createElement('div');
      th0.id='acScrollThumb';
      th0.className='ac-scroll-thumb';
      st.appendChild(th0);
      sh.appendChild(st);
    }
    var th=gid('acScrollThumb')||st.querySelector('.ac-scroll-thumb');
    return {sh:sh,ac:ac,st:st,th:th};
  }
  function scroller(ac,sh){
    if(ac&&ac.classList.contains('open')&&ac.scrollHeight>ac.clientHeight+2)return ac;
    if(sh&&sh.scrollHeight>sh.clientHeight+2)return sh;
    return ac;
  }
  function sync(){
    var n=ensure();
    if(!n)return;
    var ac=n.ac,sh=n.sh,st=n.st,th=n.th;
    var open=ac.classList.contains('open')&&ac.childNodes.length;
    var sc=scroller(ac,sh);
    var max=sc?Math.max(0,sc.scrollHeight-sc.clientHeight):0;
    var show=!!(open&&max>2);
    sh.classList.toggle('has-ac-overflow',show);
    st.hidden=!show;
    if(!show){st.classList.remove('is-dragging');return;}
    var gap=4;
    var top=ac.offsetTop;
    var trackH=Math.max(16,ac.clientHeight-gap*2);
    st.style.top=(top+gap)+'px';
    st.style.height=trackH+'px';
    var thumbH=Math.max(22,Math.round((sc.clientHeight/Math.max(1,sc.scrollHeight))*trackH));
    if(thumbH>trackH)thumbH=trackH;
    var range=Math.max(1,trackH-thumbH);
    th.style.height=thumbH+'px';
    th.style.top=Math.round((sc.scrollTop/Math.max(1,max))*range)+'px';
  }
  function schedule(){
    if(raf)cancelAnimationFrame(raf);
    raf=requestAnimationFrame(function(){
      raf=requestAnimationFrame(function(){raf=0;sync();});
    });
  }
  function yToScroll(sc,st,clientY){
    var r=st.getBoundingClientRect();
    var th=gid('acScrollThumb');
    var thH=th?th.offsetHeight:22;
    var y=clientY-r.top-thH/2;
    var range=Math.max(1,r.height-thH);
    var ratio=Math.max(0,Math.min(1,y/range));
    sc.scrollTop=ratio*Math.max(1,sc.scrollHeight-sc.clientHeight);
  }
  function bind(){
    var n=ensure();
    if(!n||bound)return;
    bound=true;
    n.ac.addEventListener('scroll',schedule,{passive:true});
    n.sh.addEventListener('scroll',schedule,{passive:true});
    n.st.addEventListener('pointerdown',function(e){
      var n2=ensure();
      if(!n2||n2.st.hidden)return;
      var sc=scroller(n2.ac,n2.sh);
      if(!sc)return;
      e.preventDefault();
      e.stopPropagation();
      n2.st.classList.add('is-dragging');
      try{n2.st.setPointerCapture(e.pointerId);}catch(err){}
      drag={sc:sc,st:n2.st,id:e.pointerId};
      yToScroll(sc,n2.st,e.clientY);
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
      drag=null;
      schedule();
    }
    n.st.addEventListener('pointerup',end);
    n.st.addEventListener('pointercancel',end);
    if(typeof ResizeObserver!=='undefined'){
      var ro=new ResizeObserver(schedule);
      ro.observe(n.ac);ro.observe(n.sh);
    }
    var mo=new MutationObserver(schedule);
    mo.observe(n.ac,{childList:true,subtree:true,attributes:true,attributeFilter:['class']});
    if(document.body){
      var mb=new MutationObserver(schedule);
      mb.observe(document.body,{attributes:true,attributeFilter:['class','style']});
    }
    window.addEventListener('resize',schedule);
  }
  function boot(){bind();schedule();}
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot);
  else boot();
  window.syncAcScrollStripe=schedule;
})();
"""


def sub_once(text, old, new, path, label):
    n = text.count(old)
    if n != 1:
        raise SystemExit(f"{path.name}: {label} count={n}, expected 1")
    return text.replace(old, new, 1)


def patch(path: Path):
    text = path.read_text(encoding="utf-8")
    if "/* ac-scroll-stripe */" in text:
        print(f"skip already patched: {path}")
        return
    text = sub_once(text, SIDES_OLD, SIDES_NEW, path, "sides acShell/acList")
    text = sub_once(text, OPEN_OLD, OPEN_NEW, path, "ac open css")
    text = sub_once(text, HTML_OLD, HTML_NEW, path, "acList html")
    text = sub_once(text, MOBILE_OLD, MOBILE_NEW, path, "mobile searchChrome")
    text = sub_once(text, SHOW_OLD, SHOW_NEW, path, "showAc sync")
    if text.count(JS_MARK) != 1:
        raise SystemExit(f"{path.name}: js mark count={text.count(JS_MARK)}")
    text = text.replace(JS_MARK, JS_BLOCK + JS_MARK, 1)
    # Do not strip existing debug probes.
    if path.name == "DS-CATALOG.html" and "function dbgIndexAc" not in text:
        raise SystemExit(f"{path.name}: lost dbgIndexAc")
    if "cat-switch{flex-wrap:wrap!important" not in text:
        raise SystemExit(f"{path.name}: lost cat-switch wrap")
    path.write_text(text, encoding="utf-8")
    print(f"patched {path}")


def main():
    for p in FILES:
        if not p.exists():
            raise SystemExit(f"missing {p}")
        patch(p)


if __name__ == "__main__":
    main()
