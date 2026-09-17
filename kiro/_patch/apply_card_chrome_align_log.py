#!/usr/bin/env python3
from pathlib import Path

ROOT = Path("/home/phnx/kiro-kontakt-patch")
FILES = [
    ROOT / "public/catalogs/KONTAKT-CATALOG.html",
    ROOT / "public/catalogs/DS-CATALOG.html",
    ROOT / "public/catalogs/KONTAKT-CATALOG-portable.html",
    ROOT / "public/catalogs/DS-CATALOG-portable.html",
]

OLD = """    fetch('http://127.0.0.1:7529/ingest/1cf46354-1d61-4c80-bd72-a340f1db1b51',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'c00e3e'},body:JSON.stringify({sessionId:'c00e3e',runId:'post-fix',hypothesisId:'C',location:'catalog:equalizeCatalogCardRows',message:'equalize card row heights',data:rowLog||{n:0},timestamp:Date.now()})}).catch(function(){});
  }catch(eDbgC){}
  // #endregion"""

NEW = """    fetch('http://127.0.0.1:7529/ingest/1cf46354-1d61-4c80-bd72-a340f1db1b51',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'c00e3e'},body:JSON.stringify({sessionId:'c00e3e',runId:'post-fix',hypothesisId:'C',location:'catalog:equalizeCatalogCardRows',message:'equalize card row heights',data:rowLog||{n:0},timestamp:Date.now()})}).catch(function(){});
  }catch(eDbgC){}
  // #endregion
  // #region agent log
  try{
    var _e=document.querySelector('#catalogMain .loc-group > .entry:not(.highlight)');
    if(_e){
      var _er=_e.getBoundingClientRect();
      function _box(el){if(!el)return null;var r=el.getBoundingClientRect();return{l:Math.round(r.left-_er.left),t:Math.round(r.top-_er.top),b:Math.round(_er.bottom-r.bottom),h:Math.round(r.height)};}
      var _fav=_e.querySelector('.fav-btn');
      var _search=_e.querySelector('.search-popup-btn');
      var _patches=_e.querySelector('details.patches');
      var _hl=_e.querySelector('.hl-body');
      var _cs=_hl?getComputedStyle(_hl):null;
      fetch('http://127.0.0.1:7529/ingest/1cf46354-1d61-4c80-bd72-a340f1db1b51',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'c00e3e'},body:JSON.stringify({sessionId:'c00e3e',runId:'post-fix',hypothesisId:'E',location:'catalog:cardChromeAlign',message:'search/fav/patches bottoms',data:{fav:_box(_fav),search:_box(_search),patches:_box(_patches),gapPatchSearch:_search&&_patches?Math.round(_search.getBoundingClientRect().top-_patches.getBoundingClientRect().bottom):null,gapSearchFav:_search&&_fav?Math.round(_search.getBoundingClientRect().bottom-_fav.getBoundingClientRect().bottom):null,hl:_cs?[_cs.display,_cs.flexGrow,_cs.marginTop].join(','):null},timestamp:Date.now()})}).catch(function(){});
    }
  }catch(eDbgE){}
  // #endregion"""


def main() -> None:
    for path in FILES:
        text = path.read_text(encoding="utf-8")
        if "catalog:cardChromeAlign" in text:
            print(f"{path.name}: already has chrome log")
            continue
        if OLD not in text:
            raise SystemExit(f"Missing equalize log block in {path.name}")
        path.write_text(text.replace(OLD, NEW, 1), encoding="utf-8")
        print(f"{path.name}: log added")


if __name__ == "__main__":
    main()
