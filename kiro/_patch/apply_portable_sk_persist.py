#!/usr/bin/env python3
"""Landscape SK-pair: keep --portable-lw after Customize; Flip drag follows pointer."""
from __future__ import annotations

import os
import tempfile
from pathlib import Path

ROOT = Path("/home/phnx/kiro-kontakt-patch/public/catalogs")
FILES = [
    ROOT / "KONTAKT-CATALOG-portable.html",
    ROOT / "DS-CATALOG-portable.html",
]
MARK = "fix-PORTABLE-SK-PERSIST"

CSS_MARK = "</style></head>"
CSS_ADD = r"""
/* fix-PORTABLE-SK-PERSIST: SK-pair --portable-lw survives Customize; Flip lw is LEFT column */
html body.catalog-portable.portable-sk-pair,
html body.catalog-portable.layout-edit.portable-sk-pair,
html body.catalog-portable.portable-landscape.portable-sk-pair,
html body.catalog-portable.layout-edit.portable-landscape.portable-sk-pair,
html body.catalog-portable.portable-landscape.display-sides.portable-sk-pair,
html body.catalog-portable.portable-landscape.display-sides.display-middle.portable-sk-pair,
html body.catalog-portable.portable-sk-pair:not(.display-middle),
html body.catalog-portable.portable-landscape.portable-sk-pair:not(.display-middle),
html body.catalog-portable.portable-landscape.display-sides:not(.display-middle).kw-open:not(.kw-chrome-collapsed):not(.search-chrome-collapsed):not(.ac-fs-open):not(.kw-fs-open),
html body.catalog-portable.layout-edit.portable-landscape.display-sides:not(.display-middle).kw-open:not(.kw-chrome-collapsed):not(.search-chrome-collapsed):not(.ac-fs-open):not(.kw-fs-open),
html body.catalog-portable.portable-landscape.display-sides.kw-open:not(.kw-chrome-collapsed):not(.search-chrome-collapsed):not(.ac-fs-open):not(.kw-fs-open),
html body.catalog-portable.portable-landscape.display-sides.display-middle.kw-open:not(.kw-chrome-collapsed):not(.search-chrome-collapsed):not(.ac-fs-open):not(.kw-fs-open),
html body.catalog-portable.layout-edit.portable-landscape.display-sides.kw-open:not(.kw-chrome-collapsed):not(.search-chrome-collapsed):not(.ac-fs-open):not(.kw-fs-open),
html body.catalog-portable.layout-edit.portable-landscape.display-sides.display-middle.kw-open:not(.kw-chrome-collapsed):not(.search-chrome-collapsed):not(.ac-fs-open):not(.kw-fs-open),
html body.catalog-portable.portable-sk-pair.sides-portrait-flip,
html body.catalog-portable.layout-edit.portable-sk-pair.sides-portrait-flip,
html body.catalog-portable.portable-landscape.portable-sk-pair.sides-portrait-flip,
html body.catalog-portable.layout-edit.portable-landscape.portable-sk-pair.sides-portrait-flip,
html body.catalog-portable.portable-sk-pair.sides-portrait-flip:not(.display-middle),
html body.catalog-portable.portable-landscape.portable-sk-pair.sides-portrait-flip:not(.display-middle),
html body.catalog-portable.portable-landscape.display-sides.sides-portrait-flip.kw-open:not(.kw-chrome-collapsed):not(.search-chrome-collapsed):not(.ac-fs-open):not(.kw-fs-open),
html body.catalog-portable.portable-landscape.display-sides:not(.display-middle).sides-portrait-flip.kw-open:not(.kw-chrome-collapsed):not(.search-chrome-collapsed):not(.ac-fs-open):not(.kw-fs-open),
html body.catalog-portable.layout-edit.portable-landscape.display-sides.sides-portrait-flip.kw-open:not(.kw-chrome-collapsed):not(.search-chrome-collapsed):not(.ac-fs-open):not(.kw-fs-open),
html body.catalog-portable.layout-edit.portable-landscape.display-sides:not(.display-middle).sides-portrait-flip.kw-open:not(.kw-chrome-collapsed):not(.search-chrome-collapsed):not(.ac-fs-open):not(.kw-fs-open),
html body.catalog-portable.portable-landscape.display-sides.display-middle.sides-portrait-flip.kw-open:not(.kw-chrome-collapsed):not(.search-chrome-collapsed):not(.ac-fs-open):not(.kw-fs-open),
html body.catalog-portable.layout-edit.portable-landscape.display-sides.display-middle.sides-portrait-flip.kw-open:not(.kw-chrome-collapsed):not(.search-chrome-collapsed):not(.ac-fs-open):not(.kw-fs-open){
  display:grid!important;flex-direction:unset!important;
  grid-template-columns:minmax(96px,var(--portable-lw,50%)) minmax(96px,1fr)!important;
  grid-template-rows:auto minmax(0,1fr)!important
}
"""

REPLACES = [
    (
        """  body.catalog-portable.display-sides:not(.display-middle).kw-open:not(.kw-chrome-collapsed):not(.search-chrome-collapsed):not(.ac-fs-open):not(.kw-fs-open),
  body.catalog-portable.display-sides.dual-fs-open,
  body.catalog-portable.display-sides.ac-fs-open.kw-fs-open{
    grid-template-columns:minmax(0,1fr) minmax(0,1fr)!important;""",
        """  body.catalog-portable.display-sides:not(.display-middle).kw-open:not(.kw-chrome-collapsed):not(.search-chrome-collapsed):not(.ac-fs-open):not(.kw-fs-open),
  body.catalog-portable.display-sides.dual-fs-open,
  body.catalog-portable.display-sides.ac-fs-open.kw-fs-open{
    grid-template-columns:minmax(96px,var(--portable-lw,50%)) minmax(96px,1fr)!important;""",
        "land-media-sk",
    ),
    (
        """  body.catalog-portable.sides-portrait-flip.display-sides:not(.display-middle).kw-open:not(.kw-chrome-collapsed):not(.search-chrome-collapsed):not(.ac-fs-open):not(.kw-fs-open){
    grid-template-columns:minmax(0,1fr) minmax(0,1fr)!important
  }""",
        """  body.catalog-portable.sides-portrait-flip.display-sides:not(.display-middle).kw-open:not(.kw-chrome-collapsed):not(.search-chrome-collapsed):not(.ac-fs-open):not(.kw-fs-open){
    grid-template-columns:minmax(96px,var(--portable-lw,50%)) minmax(96px,1fr)!important
  }""",
        "land-flip-sk",
    ),
    (
        """html body.catalog-portable.portable-sk-pair,
html body.catalog-portable.portable-landscape.display-sides:not(.display-middle).kw-open:not(.kw-chrome-collapsed):not(.search-chrome-collapsed):not(.ac-fs-open):not(.kw-fs-open){
  grid-template-columns:minmax(0,1fr) minmax(0,1fr)!important;
  grid-template-rows:auto minmax(0,1fr)!important
}""",
        """html body.catalog-portable.portable-sk-pair,
html body.catalog-portable.portable-landscape.display-sides:not(.display-middle).kw-open:not(.kw-chrome-collapsed):not(.search-chrome-collapsed):not(.ac-fs-open):not(.kw-fs-open){
  grid-template-columns:minmax(96px,var(--portable-lw,50%)) minmax(96px,1fr)!important;
  grid-template-rows:auto minmax(0,1fr)!important
}""",
        "sk-toolbar-pair",
    ),
    (
        """html body.catalog-portable.portable-landscape.display-sides.display-middle.kw-open:not(.kw-chrome-collapsed):not(.search-chrome-collapsed),
html body.catalog-portable.portable-sk-pair{
  grid-template-columns:minmax(0,1fr) minmax(0,1fr)!important
}""",
        """html body.catalog-portable.portable-landscape.display-sides.display-middle.kw-open:not(.kw-chrome-collapsed):not(.search-chrome-collapsed),
html body.catalog-portable.portable-sk-pair{
  grid-template-columns:minmax(96px,var(--portable-lw,50%)) minmax(96px,1fr)!important
}""",
        "sk-rotate-pair",
    ),
    (
        """html body.catalog-portable.portable-sk-pair.sides-portrait-flip,
html body.catalog-portable.layout-edit.portable-sk-pair.sides-portrait-flip,
html body.catalog-portable.portable-landscape.portable-sk-pair.sides-portrait-flip,
html body.catalog-portable.layout-edit.portable-landscape.display-sides.sides-portrait-flip.kw-open:not(.kw-chrome-collapsed):not(.search-chrome-collapsed):not(.ac-fs-open):not(.kw-fs-open){
  grid-template-columns:minmax(96px,1fr) minmax(96px,var(--portable-lw,50%))!important
}""",
        """html body.catalog-portable.portable-sk-pair.sides-portrait-flip,
html body.catalog-portable.layout-edit.portable-sk-pair.sides-portrait-flip,
html body.catalog-portable.portable-landscape.portable-sk-pair.sides-portrait-flip,
html body.catalog-portable.layout-edit.portable-landscape.display-sides.sides-portrait-flip.kw-open:not(.kw-chrome-collapsed):not(.search-chrome-collapsed):not(.ac-fs-open):not(.kw-fs-open){
  grid-template-columns:minmax(96px,var(--portable-lw,50%)) minmax(96px,1fr)!important
}""",
        "edit-live-flip-lw",
    ),
    (
        """        var dx=e.clientX-drag.x;
        var nl=drag.grow==='left'?drag.w-dx:drag.w+dx;""",
        """        var dx=e.clientX-drag.x;
        var pairP=document.body.classList.contains('portable-sk-pair');
        var nl=(drag.grow==='left'&&!pairP)?drag.w-dx:drag.w+dx;""",
        "drag-screen-x",
    ),
    (
        """  if(st.lw&&!has('--portable-lw'))root.style.setProperty('--portable-lw',st.lw+'px');
  if(st.rw&&!has('--portable-rw'))root.style.setProperty('--portable-rw',st.rw+'px');
  if(st['menu-h']&&!has('--portable-menu-h'))root.style.setProperty('--portable-menu-h',st['menu-h']+'px');""",
        """  function hasInline(p){return !!(root.style.getPropertyValue(p)||'').trim();}
  if(st.lw&&!hasInline('--portable-lw'))root.style.setProperty('--portable-lw',st.lw+'px');
  if(st.rw&&!hasInline('--portable-rw'))root.style.setProperty('--portable-rw',st.rw+'px');
  if(st['menu-h']&&!hasInline('--portable-menu-h'))root.style.setProperty('--portable-menu-h',st['menu-h']+'px');""",
        "apply-stored-inline",
    ),
    (
        """  }else{
    var plw=parseInt(getComputedStyle(document.documentElement).getPropertyValue('--portrait-lw'),10)||0;
    var pmh=parseInt(getComputedStyle(document.documentElement).getPropertyValue('--portrait-menu-h'),10)||0;
    if(plw>40)patch.plw=plw;
    if(pmh>40)patch.pmh=pmh;
    patch.flip=id.indexOf('-B-')>=0;
  }""",
        """  }else if(window.CATALOG_PORTABLE){
    var plw=parseInt(getComputedStyle(document.documentElement).getPropertyValue('--portable-lw'),10)||0;
    var prw=parseInt(getComputedStyle(document.documentElement).getPropertyValue('--portable-rw'),10)||0;
    var pmh=parseInt(getComputedStyle(document.documentElement).getPropertyValue('--portable-menu-h'),10)||0;
    if(plw>40)patch.plw=plw;
    if(prw>40)patch.prw=prw;
    if(pmh>40)patch.pmh=pmh;
    patch.flip=id.indexOf('-B-')>=0;
  }else{
    var plw=parseInt(getComputedStyle(document.documentElement).getPropertyValue('--portrait-lw'),10)||0;
    var pmh=parseInt(getComputedStyle(document.documentElement).getPropertyValue('--portrait-menu-h'),10)||0;
    if(plw>40)patch.plw=plw;
    if(pmh>40)patch.pmh=pmh;
    patch.flip=id.indexOf('-B-')>=0;
  }""",
        "bucket-snap-portable",
    ),
    (
        """  }else{
    var d=typeof portraitSidesDefaults==='function'?portraitSidesDefaults():null;
    var lw=b.plw,mh=b.pmh;
    if(d&&typeof clampPortraitTravel==='function'){
      lw=clampPortraitTravel(lw||d.stackW,d.stackW,d.availW);
      mh=clampPortraitTravel(mh||d.searchH,d.searchH,d.availH);
    }
    if(lw)document.documentElement.style.setProperty('--portrait-lw',parseInt(lw,10)+'px');
    if(mh)document.documentElement.style.setProperty('--portrait-menu-h',parseInt(mh,10)+'px');
    if(d&&lw)document.documentElement.style.setProperty('--portrait-rw',Math.max(80,d.availW-parseInt(lw,10))+'px');
  }""",
        """  }else if(window.CATALOG_PORTABLE){
    if(b.plw)document.documentElement.style.setProperty('--portable-lw',parseInt(b.plw,10)+'px');
    if(b.prw)document.documentElement.style.setProperty('--portable-rw',parseInt(b.prw,10)+'px');
    if(b.pmh){
      document.documentElement.style.setProperty('--portable-menu-h',parseInt(b.pmh,10)+'px');
      document.documentElement.style.setProperty('--middle-menu-h',parseInt(b.pmh,10)+'px');
    }
  }else{
    var d=typeof portraitSidesDefaults==='function'?portraitSidesDefaults():null;
    var lw=b.plw,mh=b.pmh;
    if(d&&typeof clampPortraitTravel==='function'){
      lw=clampPortraitTravel(lw||d.stackW,d.stackW,d.availW);
      mh=clampPortraitTravel(mh||d.searchH,d.searchH,d.availH);
    }
    if(lw)document.documentElement.style.setProperty('--portrait-lw',parseInt(lw,10)+'px');
    if(mh)document.documentElement.style.setProperty('--portrait-menu-h',parseInt(mh,10)+'px');
    if(d&&lw)document.documentElement.style.setProperty('--portrait-rw',Math.max(80,d.availW-parseInt(lw,10))+'px');
  }""",
        "bucket-apply-portable",
    ),
    (
        """data:{on:onE,was:was,splitDisp:splitE?getComputedStyle(splitE).display:'none',sepDisp:sepE?getComputedStyle(sepE).display:'none',splitPe:splitE?getComputedStyle(splitE).pointerEvents:'',btnPressed:(document.getElementById('layoutEditBtn')||{}).getAttribute&&document.getElementById('layoutEditBtn').getAttribute('aria-pressed')}""",
        """data:{on:onE,was:was,splitDisp:splitE?getComputedStyle(splitE).display:'none',sepDisp:sepE?getComputedStyle(sepE).display:'none',splitPe:splitE?getComputedStyle(splitE).pointerEvents:'',btnPressed:(document.getElementById('layoutEditBtn')||{}).getAttribute&&document.getElementById('layoutEditBtn').getAttribute('aria-pressed'),pair:document.body.classList.contains('portable-sk-pair'),flip:document.body.classList.contains('sides-portrait-flip'),lw:(getComputedStyle(document.documentElement).getPropertyValue('--portable-lw')||'').trim(),cols:getComputedStyle(document.body).gridTemplateColumns,searchW:(function(){var el=document.getElementById('searchChrome');return el?Math.round(el.getBoundingClientRect().width):0;})(),kwW:(function(){var el=document.getElementById('filterWrap');return el?Math.round(el.getBoundingClientRect().width):0;})()}""",
        "toggle-log",
    ),
]

PERSIST_OLD = """    if(ml>40||mm>40)writeMiddleLayout(ml,mm);
    }
  }catch(e2){}
}"""

PERSIST_NEW = """    if(ml>40||mm>40)writeMiddleLayout(ml,mm);
    }
  }catch(e2){}
  try{if(typeof snapshotCurrentLayoutBucket==='function')snapshotCurrentLayoutBucket();}catch(e3){}
  // #region agent log
  try{fetch('http://127.0.0.1:7529/ingest/1cf46354-1d61-4c80-bd72-a340f1db1b51',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'c00e3e'},body:JSON.stringify({sessionId:'c00e3e',runId:'sk-persist',hypothesisId:'SK-P',location:'portable:persistPortableVars',message:'persist portable split',data:{lw:grab('--portable-lw'),rw:grab('--portable-rw'),mh:grab('--portable-menu-h'),pair:!!(document.body&&document.body.classList.contains('portable-sk-pair')),flip:!!(document.body&&document.body.classList.contains('sides-portrait-flip')),edit:!!(document.body&&document.body.classList.contains('layout-edit'))},timestamp:Date.now()})}).catch(function(){});}catch(eLogP){}
  // #endregion
}"""


def replace_once(text: str, old: str, new: str, label: str) -> str:
    n = text.count(old)
    if n != 1:
        raise SystemExit(f"{label}: expected 1 occurrence, found {n}")
    return text.replace(old, new, 1)


def patch(text: str) -> str:
    if MARK in text:
        raise SystemExit("already patched")
    for old, new, label in REPLACES:
        text = replace_once(text, old, new, label)
    text = replace_once(text, PERSIST_OLD, PERSIST_NEW, "persist-bucket")
    if CSS_MARK not in text:
        raise SystemExit("missing </style></head>")
    text = text.replace(CSS_MARK, CSS_ADD + CSS_MARK, 1)
    return text


def write_safe(path: Path, data: str, before_c00: int) -> None:
    if not data.rstrip().endswith("</html>"):
        raise SystemExit(f"{path.name} rewrite missing </html>")
    if data.count("sessionId:'c00e3e'") < before_c00:
        raise SystemExit(f"{path.name}: lost c00e3e logs")
    fd, tmp = tempfile.mkstemp(prefix=path.stem + ".", suffix=".html", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise
    got = path.stat().st_size
    if got < 100000:
        raise SystemExit(f"{path.name} too small after write: {got}")
    check = path.read_text(encoding="utf-8")
    if not check.rstrip().endswith("</html>"):
        raise SystemExit(f"{path.name} after write missing </html>")
    if MARK not in check:
        raise SystemExit(f"{path.name} missing {MARK}")
    if check.count("function placePortableHandles(){") != 1:
        raise SystemExit(f"{path.name} placePortableHandles count")
    if "minmax(0,1fr) minmax(0,1fr)!important" in check[
        check.find("html body.catalog-portable.portable-sk-pair,") : check.find(MARK)
        if MARK in check
        else None
    ]:
        pass
    leftover_pair = (
        "html body.catalog-portable.portable-sk-pair{\n  grid-template-columns:minmax(0,1fr) minmax(0,1fr)!important"
    )
    if leftover_pair in check:
        raise SystemExit(f"{path.name} leftover SK-pair 1fr 1fr")
    if "minmax(96px,1fr) minmax(96px,var(--portable-lw,50%))" in check:
        raise SystemExit(f"{path.name} Flip still maps lw to right column")
    if "var nl=(drag.grow==='left'&&!pairP)?drag.w-dx:drag.w+dx;" not in check:
        raise SystemExit(f"{path.name} missing screen-space SK-pair drag")
    if check.count("function wipePortableEdit3Pane(") != 1:
        raise SystemExit(f"{path.name} wipe helper count")


def main() -> None:
    for path in FILES:
        raw = path.read_text(encoding="utf-8")
        before_c00 = raw.count("sessionId:'c00e3e'")
        out = patch(raw)
        write_safe(path, out, before_c00)
        after_c00 = out.count("sessionId:'c00e3e'")
        print(
            f"patched {path.name} {len(raw)} -> {len(out)} "
            f"c00={before_c00}->{after_c00} size={path.stat().st_size}"
        )


if __name__ == "__main__":
    main()
