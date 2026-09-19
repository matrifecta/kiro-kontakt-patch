#!/usr/bin/env python3
"""
CONTENT-WINDOW-DOCK-POINTS-v1

Adds 4 new drag-and-dock points for the floating quick-bar toolbar, anchored to
the content window (#catalogMain)'s own border, centered on each of its 4 edges
(top/bottom/left/right) - in addition to the existing screen-edge and
menu-separator ("seam"/"vseam") dock points. These new points exist in every
layout/orientation combination as long as the content window is on screen, and
because they are resolved live from #catalogMain's current rect (the same
mechanism already used for the seam docks), they automatically track/flip with
the content window whenever it moves/mirrors - no separate persistence needed.
"""
import re, sys

FILES = [
    "public/catalogs/DS-CATALOG-portable.html",
    "public/catalogs/KONTAKT-CATALOG-portable.html",
]

CSS_OLD = """.qb-dock-top{clip-path:polygon(0 0,100% 0,50% 100%)}
.qb-dock-bottom{clip-path:polygon(50% 0,0 100%,100% 100%)}
.qb-dock-left{clip-path:polygon(0 0,0 100%,100% 50%)}
.qb-dock-right{clip-path:polygon(100% 0,100% 100%,0 50%)}"""

CSS_NEW = """.qb-dock-top,.qb-dock-cwtop{clip-path:polygon(0 0,100% 0,50% 100%)}
.qb-dock-bottom,.qb-dock-cwbottom{clip-path:polygon(50% 0,0 100%,100% 100%)}
.qb-dock-left,.qb-dock-cwleft{clip-path:polygon(0 0,0 100%,100% 50%)}
.qb-dock-right,.qb-dock-cwright{clip-path:polygon(100% 0,100% 100%,0 50%)}"""

JS_OLD = """      if(id!=='catalogMain'&&rr.bottom>bh/2+m+36&&rr.bottom<vh-bh/2-m-14)ds.push({x:vw/2,y:rr.bottom,e:'seam',pane:id});
    }
  });
"""

JS_NEW = """      if(id!=='catalogMain'&&rr.bottom>bh/2+m+36&&rr.bottom<vh-bh/2-m-14)ds.push({x:vw/2,y:rr.bottom,e:'seam',pane:id});
    }
  });
  /* CONTENT-WINDOW-DOCK-POINTS-v1: 4 edge-centered docks on the content window's own
     border, resolved live from its current rect so they persist and flip together
     with the content window in every layout/orientation combo. */
  var cwEl=document.getElementById('catalogMain');
  if(cwEl&&cwEl.offsetParent!==null){
    var cw=cwEl.getBoundingClientRect();
    if(cw.width>40&&cw.height>40){
      var cwPts=[
        {x:clX((cw.left+cw.right)/2),y:cw.top,e:'cwtop'},
        {x:clX((cw.left+cw.right)/2),y:cw.bottom,e:'cwbottom'},
        {x:cw.left,y:clYv((cw.top+cw.bottom)/2),e:'cwleft',v:'left'},
        {x:cw.right,y:clYv((cw.top+cw.bottom)/2),e:'cwright',v:'right'}
      ];
      cwPts.forEach(function(p){
        var dupe=false;
        for(var di=0;di<ds.length;di++){if(Math.hypot(ds[di].x-p.x,ds[di].y-p.y)<28){dupe=true;break;}}
        if(!dupe){p.pane='catalogMain';ds.push(p);}
      });
    }
  }
"""

def patch(path):
    src = open(path, encoding="utf-8").read()
    changed = False
    if "CONTENT-WINDOW-DOCK-POINTS-v1" in src:
        print(f"{path}: already patched, skipping")
        return
    if src.count(CSS_OLD) != 1:
        sys.exit(f"{path}: CSS anchor not found/unique ({src.count(CSS_OLD)})")
    src = src.replace(CSS_OLD, CSS_NEW, 1)
    changed = True
    if src.count(JS_OLD) != 1:
        sys.exit(f"{path}: JS anchor not found/unique ({src.count(JS_OLD)})")
    src = src.replace(JS_OLD, JS_NEW, 1)
    open(path, "w", encoding="utf-8").write(src)
    print(f"{path}: patched")

for f in FILES:
    patch(f)
