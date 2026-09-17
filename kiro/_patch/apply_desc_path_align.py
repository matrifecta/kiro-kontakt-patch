#!/usr/bin/env python3
"""Lock grid description panels to existing 8.2em max; equalize title bands so path starts aligned."""
from pathlib import Path

ROOT = Path("/home/phnx/kiro-kontakt-patch")
FILES = [
    ROOT / "public/catalogs/KONTAKT-CATALOG.html",
    ROOT / "public/catalogs/DS-CATALOG.html",
    ROOT / "public/catalogs/KONTAKT-CATALOG-portable.html",
    ROOT / "public/catalogs/DS-CATALOG-portable.html",
]

CSS_OLD = ".entry:not(.highlight) .card-actions{margin-top:0;margin-bottom:calc(.5rem - .8rem);padding-bottom:0;align-self:flex-start}"
CSS_NEW = """.entry:not(.highlight) .card-actions{margin-top:0;margin-bottom:calc(.5rem - .8rem);padding-bottom:0;align-self:flex-start}
.entry:not(.highlight) .lib-name{flex:0 0 auto}
.entry:not(.highlight) .lib-notes{flex:0 0 auto}
.entry:not(.highlight) .summary-panel{height:8.2em;max-height:8.2em;flex:0 0 auto}
.entry:not(.highlight) .path{flex:0 0 auto}"""

JS_RESET_OLD = """    group.querySelectorAll(':scope > .entry').forEach(function(e){
      if(e.classList.contains('highlight'))return;
      e.style.minHeight='';
    });
  });
  var rowLog=null;"""

JS_RESET_NEW = """    group.querySelectorAll(':scope > .entry').forEach(function(e){
      if(e.classList.contains('highlight'))return;
      e.style.minHeight='';
      var n=e.querySelector('.lib-name');
      if(n)n.style.minHeight='';
    });
  });
  var maxTitle=0;
  var visCards=[];
  groups.forEach(function(group){
    group.querySelectorAll(':scope > .entry').forEach(function(e){
      if(e.classList.contains('is-hidden')||e.classList.contains('highlight'))return;
      if(e.style.display==='none')return;
      var r=e.getBoundingClientRect();
      if(!(r.width>2&&r.height>2))return;
      visCards.push(e);
      var n=e.querySelector('.lib-name');
      if(n)maxTitle=Math.max(maxTitle,n.getBoundingClientRect().height);
    });
  });
  if(maxTitle>0){
    var th=Math.round(maxTitle);
    visCards.forEach(function(e){
      var n=e.querySelector('.lib-name');
      if(n)n.style.minHeight=th+'px';
    });
  }
  var rowLog=null;"""

F_LOG = """
  // #region agent log
  try{
    var _cards=[];
    document.querySelectorAll('#catalogMain .loc-group > .entry:not(.highlight)').forEach(function(e,i){
      if(i>3)return;
      if(e.classList.contains('is-hidden'))return;
      var er=e.getBoundingClientRect();
      function _rel(sel){var el=e.querySelector(sel);if(!el)return null;var r=el.getBoundingClientRect();return{t:Math.round(r.top-er.top),h:Math.round(r.height)};}
      var d=e.querySelector('.summary-panel');
      _cards.push({id:e.id,title:_rel('.lib-name'),desc:_rel('.summary-panel'),path:_rel('.path'),descMax:d?getComputedStyle(d).maxHeight:null,descH:d?getComputedStyle(d).height:null});
    });
    fetch('http://127.0.0.1:7529/ingest/1cf46354-1d61-4c80-bd72-a340f1db1b51',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'c00e3e'},body:JSON.stringify({sessionId:'c00e3e',runId:'post-fix',hypothesisId:'F',location:'catalog:equalizeCardSections',message:'title/desc/path bands',data:{maxTitle:Math.round(maxTitle||0),nVis:visCards.length,cards:_cards},timestamp:Date.now()})}).catch(function(){});
  }catch(eDbgF){}
  // #endregion"""

E_END = """  }catch(eDbgE){}
  // #endregion
}"""


def patch_one(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    if CSS_OLD not in text:
        raise SystemExit(f"{path.name}: missing card-actions CSS")
    if ".entry:not(.highlight) .summary-panel{height:8.2em" not in text:
        if text.count(CSS_OLD) != 1:
            raise SystemExit(f"{path.name}: expected 1 card-actions CSS, got {text.count(CSS_OLD)}")
        text = text.replace(CSS_OLD, CSS_NEW, 1)
    if JS_RESET_OLD not in text:
        if "n.style.minHeight=''" in text:
            print(f"{path.name}: JS title equalize already present")
        else:
            raise SystemExit(f"{path.name}: missing JS reset block")
    else:
        text = text.replace(JS_RESET_OLD, JS_RESET_NEW, 1)
    if "catalog:equalizeCardSections" not in text:
        if E_END not in text:
            raise SystemExit(f"{path.name}: missing E log end")
        text = text.replace(E_END, "  }catch(eDbgE){}\n  // #endregion" + F_LOG + "\n}", 1)
    path.write_text(text, encoding="utf-8")
    print(f"{path.name}: ok")


def main() -> None:
    for p in FILES:
        patch_one(p)


if __name__ == "__main__":
    main()
