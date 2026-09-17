#!/usr/bin/env python3
"""Park Index for Window/Embed; stop expanded Window from covering the document."""
from pathlib import Path

FILES = [
    Path("/home/phnx/kiro-kontakt-patch/public/catalogs/KONTAKT-CATALOG-portable.html"),
    Path("/home/phnx/kiro-kontakt-patch/public/catalogs/DS-CATALOG-portable.html"),
]

CSS_OLD = """html body.catalog-portable.ac-fs-open #catalogIndex,
html body.catalog-portable.kw-fs-open #catalogIndex,
html body.catalog-portable.dual-fs-open #catalogIndex,
html body.catalog-portable.display-fs #catalogIndex{
  visibility:hidden!important;pointer-events:none!important
}
html body.index-window-open:not(.index-fill-doc) #catalogIndex:not(.is-embedded),
html body.display-sides.index-window-open:not(.index-fill-doc) #catalogIndex:not(.is-embedded),
html body.display-middle.index-window-open:not(.index-fill-doc) #catalogIndex:not(.is-embedded),
html body.catalog-portable.index-window-open:not(.index-fill-doc) #catalogIndex:not(.is-embedded),
html body.catalog-portable.display-sides.index-window-open:not(.index-fill-doc) #catalogIndex:not(.is-embedded),
html body.catalog-portable.display-middle.index-window-open:not(.index-fill-doc) #catalogIndex:not(.is-embedded),
html body.catalog-portable.display-content.index-window-open:not(.index-fill-doc) #catalogIndex:not(.is-embedded),
html body.catalog-portable #catalogMain>#catalogIndex:not(.is-embedded),
html body.catalog-portable.index-window-open #catalogIndex.is-collapsed:not(.is-embedded){
  position:relative!important;top:auto!important;left:auto!important;right:auto!important;
  margin:0 0 1.35rem!important;z-index:2!important
}"""

CSS_NEW = """html body.catalog-portable.ac-fs-open #catalogIndex,
html body.catalog-portable.kw-fs-open #catalogIndex,
html body.catalog-portable.dual-fs-open #catalogIndex,
html body.catalog-portable.display-fs #catalogIndex,
html body.catalog-portable:not(.content-window-on) #catalogIndex{
  visibility:hidden!important;pointer-events:none!important
}
html body.catalog-portable.content-window-on #catalogIndex{
  visibility:visible!important;pointer-events:auto!important
}
html body.index-window-open:not(.index-fill-doc) #catalogIndex:not(.is-embedded),
html body.display-sides.index-window-open:not(.index-fill-doc) #catalogIndex:not(.is-embedded),
html body.display-middle.index-window-open:not(.index-fill-doc) #catalogIndex:not(.is-embedded),
html body.catalog-portable.index-window-open:not(.index-fill-doc) #catalogIndex:not(.is-embedded),
html body.catalog-portable.display-sides.index-window-open:not(.index-fill-doc) #catalogIndex:not(.is-embedded),
html body.catalog-portable.display-middle.index-window-open:not(.index-fill-doc) #catalogIndex:not(.is-embedded),
html body.catalog-portable.display-content.index-window-open:not(.index-fill-doc) #catalogIndex:not(.is-embedded),
html body.catalog-portable #catalogMain>#catalogIndex:not(.is-embedded),
html body.catalog-portable.index-window-open #catalogIndex.is-collapsed:not(.is-embedded){
  position:relative!important;top:auto!important;left:auto!important;right:auto!important;bottom:auto!important;
  margin:0 0 1.35rem!important;z-index:2!important
}
html body.catalog-portable.index-window-open #catalogMain>#catalogIndex:not(.is-embedded):not(.is-collapsed),
html body.catalog-portable.display-content.index-window-open #catalogMain>#catalogIndex:not(.is-embedded):not(.is-collapsed),
html body.catalog-portable.display-sides.index-window-open #catalogMain>#catalogIndex:not(.is-embedded):not(.is-collapsed),
html body.catalog-portable.display-middle.index-window-open #catalogMain>#catalogIndex:not(.is-embedded):not(.is-collapsed){
  position:relative!important;inset:auto!important;top:auto!important;left:auto!important;right:auto!important;bottom:auto!important;
  display:flex!important;flex-direction:column!important;
  flex:0 0 var(--sides-index-h,min(48dvh,28rem))!important;
  height:var(--sides-index-h,min(48dvh,28rem))!important;
  max-height:min(70dvh,40rem)!important;min-height:0!important;
  width:auto!important;margin:0 0 1.35rem!important;z-index:2!important
}"""

PARK_OLD = """function parkCatalogDocNote(host){
  var note=ensureCatalogDocNote();
  if(!note)return;
  var w=host||document.getElementById('catalogMain');
  if(!w){
    var cb=document.querySelector('.catalog-body');
    if(cb&&cb.parentNode){if(cb.nextSibling)cb.parentNode.insertBefore(note,cb.nextSibling);else cb.parentNode.appendChild(note);}
    return;
  }
  var cb=w.querySelector(':scope > .catalog-body')||w.querySelector('.catalog-body');
  var ix=document.getElementById('catalogIndex');
  if(ix&&cb){
    if(ix.classList.contains('is-embedded')){
      if(ix.parentNode!==cb||cb.firstElementChild!==ix){
        if(cb.firstChild)cb.insertBefore(ix,cb.firstChild);else cb.appendChild(ix);
      }
    }else if(ix.parentNode!==w||ix.nextElementSibling!==cb){
      w.insertBefore(ix,cb);
    }
  }"""

PARK_NEW = """function parkCatalogIndex(host){
  var w=host||document.getElementById('catalogMain');
  var cb=w&&(w.querySelector(':scope > .catalog-body')||w.querySelector('.catalog-body'));
  var ix=document.getElementById('catalogIndex');
  if(!w||!cb||!ix)return;
  if(ix.classList.contains('is-embedded')){
    if(ix.parentNode!==cb||cb.firstElementChild!==ix){
      if(cb.firstChild)cb.insertBefore(ix,cb.firstChild);else cb.appendChild(ix);
    }
  }else if(ix.parentNode!==w||ix.nextElementSibling!==cb){
    w.insertBefore(ix,cb);
  }
}
window.parkCatalogIndex=parkCatalogIndex;
function parkCatalogDocNote(host){
  var w=host||document.getElementById('catalogMain');
  var cb=w&&(w.querySelector(':scope > .catalog-body')||w.querySelector('.catalog-body'))||document.querySelector('.catalog-body');
  if(typeof parkCatalogIndex==='function')parkCatalogIndex(w);
  var note=ensureCatalogDocNote();
  if(!note)return;
  if(!w){
    if(cb&&cb.parentNode){if(cb.nextSibling)cb.parentNode.insertBefore(note,cb.nextSibling);else cb.parentNode.appendChild(note);}
    return;
  }
  cb=w.querySelector(':scope > .catalog-body')||w.querySelector('.catalog-body');
  var ix=document.getElementById('catalogIndex');
  if(ix&&cb){
    if(ix.classList.contains('is-embedded')){
      if(ix.parentNode!==cb||cb.firstElementChild!==ix){
        if(cb.firstChild)cb.insertBefore(ix,cb.firstChild);else cb.appendChild(ix);
      }
    }else if(ix.parentNode!==w||ix.nextElementSibling!==cb){
      w.insertBefore(ix,cb);
    }
  }"""

FORCE_OLD = """  if(typeof syncIndexToggleUi==='function')syncIndexToggleUi(ix);
  debugIndexLoad('force-closed',{asked:String(reason||'')});
}"""

FORCE_NEW = """  if(typeof syncIndexToggleUi==='function')syncIndexToggleUi(ix);
  if(typeof parkCatalogIndex==='function')parkCatalogIndex();
  else if(typeof parkCatalogDocNote==='function')parkCatalogDocNote();
  if(typeof syncIndexWindowDock==='function')syncIndexWindowDock();
  debugIndexLoad('force-closed',{asked:String(reason||'')});
}"""

IIFE_OLD = """    if(window.CATALOG_PORTABLE){
      if(pref===true)idx.classList.add('is-embedded');
      else if(pref===false)idx.classList.remove('is-embedded');
      if(typeof syncIndexEmbedBtn==='function')syncIndexEmbedBtn();
      return;
    }"""

IIFE_NEW = """    if(window.CATALOG_PORTABLE){
      if(pref===true)idx.classList.add('is-embedded');
      else if(pref===false)idx.classList.remove('is-embedded');
      if(typeof syncIndexEmbedBtn==='function')syncIndexEmbedBtn();
      if(typeof parkCatalogIndex==='function')parkCatalogIndex();
      else if(typeof parkCatalogDocNote==='function')parkCatalogDocNote();
      if(typeof syncIndexWindowDock==='function')syncIndexWindowDock();
      debugIndexLoad('display-pref-park',{pref:pref});
      return;
    }"""


def apply_one(path: Path):
    t = path.read_text(encoding="utf-8")
    n = 0
    for old, new, label in (
        (CSS_OLD, CSS_NEW, "css"),
        (PARK_OLD, PARK_NEW, "park"),
        (FORCE_OLD, FORCE_NEW, "force"),
        (IIFE_OLD, IIFE_NEW, "iife"),
    ):
        if old not in t:
            if new in t or (label == "park" and "function parkCatalogIndex(host)" in t):
                print("skip", path.name, label)
                continue
            raise SystemExit(f"{path.name} missing {label}")
        t = t.replace(old, new, 1)
        n += 1
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(t, encoding="utf-8")
    out = tmp.read_text(encoding="utf-8")
    if not out.rstrip().endswith("</html>"):
        tmp.unlink()
        raise SystemExit("trunc " + path.name)
    path.write_text(out, encoding="utf-8")
    tmp.unlink()
    print("ok", path.name, n, path.stat().st_size)


def main():
    for p in FILES:
        apply_one(p)


if __name__ == "__main__":
    main()
