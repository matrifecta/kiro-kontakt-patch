#!/usr/bin/env python3
"""
Mobile quick-bar: make a seam dock *persistent* instead of a one-off snap.

Before: dropping the bar near a pane seam only saved the pixel offset it
landed at. When the separator moved, a pane was hidden, or the panes were
flipped, the bar stayed at the stale pixels.

After: dropping on a dock saves an orientation-independent dock descriptor
({e:'seam', pane:'searchChrome'} / {e:'vseam', panes:[..]} / edge). On every
layout change the descriptor is re-resolved against the live pane rects, so
the bar follows the separator and survives flips. If the seam does not exist
right now (menus hidden, content-only view) it falls back to bottom-centre
and returns to the seam once the menus are back. Dropping away from any dock
clears the descriptor (explicit undock).
"""
FILES = [
    "public/catalogs/DS-CATALOG.html",
    "public/catalogs/DS-CATALOG-portable.html",
    "public/catalogs/KONTAKT-CATALOG.html",
    "public/catalogs/KONTAKT-CATALOG-portable.html",
]

REPL = [
    # docks carry pane identity so a saved dock can be re-resolved later
    ("if(id!=='catalogMain'&&rr.bottom>bh/2+m+36&&rr.bottom<vh-bh/2-m-14)ds.push({x:vw/2,y:rr.bottom,e:'seam'});",
     "if(id!=='catalogMain'&&rr.bottom>bh/2+m+36&&rr.bottom<vh-bh/2-m-14)ds.push({x:vw/2,y:rr.bottom,e:'seam',pane:id});"),
    ("panes.push(rr);",
     "panes.push({id:id,r:rr});"),
    ("var ra=panes[pi],rb=panes[pj];",
     "var ra=panes[pi].r,rb=panes[pj].r;"),
    ("if(!dupe)ds.push({x:sx,y:sy,e:'vseam',v:'vseam'});",
     "if(!dupe)ds.push({x:sx,y:sy,e:'vseam',v:'vseam',panes:[panes[pi].id,panes[pj].id]});"),
    # curPos: a saved dock descriptor wins and is re-resolved live
    ("function curPos(){var c=convPos(loadPos()[orient()]);return c?clampPos(c.dx,c.dy,c.v):defPos();}",
     r"""/* fix-QB-SEAM-DOCK-v1: a persistent dock follows the seam it was dropped on */
function sameSet(a,b){if(!a||!b||a.length!==b.length)return false;var s=a.slice().sort().join('|'),t=b.slice().sort().join('|');return s===t;}
function resolveDock(dk){
  if(!dk||!window.CATALOG_PORTABLE)return null;
  var vw=window.innerWidth||800,vh=window.innerHeight||600;
  var ds=docksFor(),hit=null;
  for(var i=0;i<ds.length;i++){
    var d=ds[i];
    if(d.e!==dk.e)continue;
    if(dk.e==='seam'&&d.pane!==dk.pane)continue;
    if(dk.e==='vseam'&&!sameSet(d.panes,dk.panes))continue;
    hit=d;break;
  }
  if(!hit&&(dk.e==='seam'||dk.e==='vseam')){
    /* no seam to dock to right now (menus hidden) -> bottom centre, keep the dock saved */
    var r=bar.getBoundingClientRect(),bh=r.height||44;
    hit={x:vw/2,y:vh-bh/2-8,e:'bottom'};
  }
  if(!hit)return null;
  return clampPos(hit.x-vw/2,hit.y-vh/2,hit.v);
}
function curPos(){var st=loadPos();var d=resolveDock(st.dock);if(d)return d;var c=convPos(st[orient()]);return c?clampPos(c.dx,c.dy,c.v):defPos();}"""),
    # remember which dock we are snapping to during the drag
    ("drag.snap=t>=0?clampPos(ds[t].x-vw/2,ds[t].y-vh/2,ds[t].v):null;",
     "drag.snap=t>=0?clampPos(ds[t].x-vw/2,ds[t].y-vh/2,ds[t].v):null;drag.snapDock=t>=0?ds[t]:null;"),
    # on drop: save the dock descriptor (or clear it = explicit undock)
    ("var p=loadPos();p[orient()]=fin;savePos(p);",
     "var p=loadPos();p[orient()]=fin;"
     "if(drag.snapDock&&window.CATALOG_PORTABLE){var sd=drag.snapDock;p.dock={e:sd.e};if(sd.pane)p.dock.pane=sd.pane;if(sd.panes)p.dock.panes=sd.panes.slice();}"
     "else delete p.dock;"
     "savePos(p);"),
    # re-resolve the dock whenever the layout changes (class flips, pane resizes, separator drags)
    ("new MutationObserver(sync).observe(document.body,{attributes:true,attributeFilter:['class']});",
     r"""new MutationObserver(sync).observe(document.body,{attributes:true,attributeFilter:['class']});
/* fix-QB-SEAM-DOCK-v1: keep a docked bar glued to its seam */
(function(){
  var raf=0;
  function redock(){
    if(drag)return;
    if(!loadPos().dock)return;
    if(raf)cancelAnimationFrame(raf);
    raf=requestAnimationFrame(function(){raf=0;applyPos();});
  }
  new MutationObserver(redock).observe(document.body,{attributes:true,attributeFilter:['class','style']});
  new MutationObserver(redock).observe(document.documentElement,{attributes:true,attributeFilter:['style']});
  if(typeof ResizeObserver!=='undefined'){
    var ro=new ResizeObserver(redock);
    ['searchChrome','filterWrap','acShell','catalogMain'].forEach(function(id){var el=document.getElementById(id);if(el)try{ro.observe(el);}catch(e){}});
  }
  window.addEventListener('pointerup',function(){setTimeout(redock,0);},true);
  window.addEventListener('touchend',function(){setTimeout(redock,0);},true);
})();"""),
]


def main():
    for path in FILES:
        txt = open(path, encoding="utf-8").read()
        for old, new in REPL:
            n = txt.count(old)
            if n != 1:
                raise SystemExit(f"{path}: expected 1 match, got {n} for: {old[:70]}")
            txt = txt.replace(old, new, 1)
        open(path, "w", encoding="utf-8").write(txt)
        print(f"{path}: {len(REPL)} replacements applied")


if __name__ == "__main__":
    main()
