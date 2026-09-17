#!/usr/bin/env python3
"""Portable: KW ⛶ in old ⋯ slot; collapsed Window Index sticks to content top."""
from pathlib import Path

ROOT = Path("/home/phnx/kiro-kontakt-patch/public/catalogs")
FILES = [
    ROOT / "KONTAKT-CATALOG-portable.html",
    ROOT / "DS-CATALOG-portable.html",
]

CSS_MARK = "</style></head><body class=\"search-mode\">"
CSS_ADD = r"""
/* fix-KW-FS-SLOT: ⛶ occupies old ⋯ slot (right); cats/Tap ⋯ stays immediately left */
@media all{
  body.catalog-portable #filterTop > #kwStripClear,
  body.catalog-portable #kwStripClear.kw-strip-clear{
    order:90;margin-left:auto
  }
  body.catalog-portable #filterTop > #kwStripMore{order:91;margin-left:0}
  body.catalog-portable #filterTop > #kwStripMorePop{order:92}
  body.catalog-portable #filterTop > #kwStripFs{
    display:inline-flex!important;align-items:center;justify-content:center;
    flex:0 0 auto;order:94;margin-left:0;
    min-width:2.75rem;min-height:2.75rem;padding:0 .45rem;
    border:1px solid var(--border);border-radius:6px;
    background:var(--bg-card);color:var(--text);font:inherit;cursor:pointer
  }
  body.catalog-portable.kw-fs-open #filterTop > #kwStripFs{display:none!important}
  body.catalog-portable.kw-cats-open #kwStripMorePop:not([hidden]){
    order:99!important;flex:1 1 100%!important
  }
}

/* fix-INDEX-COLLAPSE-STICK: Window Index (open or collapsed) stays at content pane top */
@media all{
  body.catalog-portable.index-window-open #catalogIndex.is-collapsed:not(.is-embedded){
    position:relative!important;top:auto!important;z-index:2!important;
    display:flex!important;flex-direction:column!important;
    flex:0 0 auto!important;height:auto!important;max-height:none!important;
    min-height:0!important;overflow:hidden!important;
    margin-top:0!important;margin-bottom:0!important;
    background:var(--bg-surface)!important;background-image:none!important;
    border:1px solid var(--border)!important;border-bottom:1px solid var(--border)!important;
    box-shadow:none!important;border-radius:0 0 10px 10px;
    pointer-events:auto!important
  }
  body.catalog-portable.index-window-open #catalogIndex.is-collapsed:not(.is-embedded) .catalog-index-head{
    flex:0 0 auto!important;border-bottom:0
  }
  body.catalog-portable.index-window-open #catalogIndex.is-collapsed:not(.is-embedded) .index,
  body.catalog-portable.index-window-open #catalogIndex.is-collapsed:not(.is-embedded) #catalogIndexList{
    display:none!important
  }
}
""" + CSS_MARK

DOCK_OLD = "  var on=!!(window.CATALOG_PORTABLE&&ix&&!ix.classList.contains('is-collapsed')&&!ix.classList.contains('is-embedded'));"
DOCK_NEW = "  var on=!!(window.CATALOG_PORTABLE&&ix&&!ix.classList.contains('is-embedded'));"

FILL_OLD = """function applyIndexFillDocStyles(){
  var fill=!!(document.body.classList.contains('index-window-open')&&indexWindowFillsToDoc());
  document.body.classList.toggle('index-fill-doc',fill);
  var ix=document.getElementById('catalogIndex');
"""
FILL_NEW = """function applyIndexFillDocStyles(){
  var ix=document.getElementById('catalogIndex');
  var fill=!!(document.body.classList.contains('index-window-open')&&indexWindowFillsToDoc()&&ix&&!ix.classList.contains('is-collapsed')&&!ix.classList.contains('is-embedded'));
  document.body.classList.toggle('index-fill-doc',fill);
"""

FS_OLD = """    var fsBtn=document.getElementById('kwStripFs');
    if(fsBtn&&topKw&&(fsBtn.parentElement!==topKw||(clrBtn&&fsBtn.nextElementSibling!==clrBtn))){
      topKw.insertBefore(fsBtn,clrBtn);
    }
    if(moreKw){
      if(clrBtn.parentElement!==topKw||clrBtn.nextElementSibling!==moreKw)topKw.insertBefore(clrBtn,moreKw);
    }else if(clrBtn.parentElement!==topKw)topKw.appendChild(clrBtn);
"""
FS_NEW = """    if(moreKw){
      if(clrBtn.parentElement!==topKw||clrBtn.nextElementSibling!==moreKw)topKw.insertBefore(clrBtn,moreKw);
    }else if(clrBtn.parentElement!==topKw)topKw.appendChild(clrBtn);
    var fsBtn=document.getElementById('kwStripFs');
    var morePop=document.getElementById('kwStripMorePop');
    if(fsBtn&&topKw){
      var after=morePop||moreKw||clrBtn;
      if(after&&(fsBtn.parentElement!==topKw||after.nextElementSibling!==fsBtn)){
        if(after.nextSibling)topKw.insertBefore(fsBtn,after.nextSibling);
        else topKw.appendChild(fsBtn);
      }
    }
"""

CSS_LOCK = r"""
/* fix-INDEX-MAIN-LOCK: docked Window Index never rides catalogMain scroll */
@media all{
  body.catalog-portable.index-window-open #catalogMain{
    overflow:hidden!important;overflow-x:hidden!important;overflow-y:hidden!important;
    overscroll-behavior:none!important
  }
}
""" + CSS_MARK

SCROLL_OLD = """  if(on&&!prev&&main){
    var keep=main.scrollTop;
    main.scrollTop=0;
    if(cb&&keep)cb.scrollTop=keep;
  }else if(!on&&prev&&main&&cb){
    var keep2=cb.scrollTop;
    cb.scrollTop=0;
    if(keep2)main.scrollTop=keep2;
  }
"""
SCROLL_NEW = """  if(on&&main){
    if(!prev){
      var keep=main.scrollTop;
      if(cb&&keep)cb.scrollTop=keep;
    }
    main.scrollTop=0;
    if(!main.dataset.ixDockScrollBound){
      main.dataset.ixDockScrollBound='1';
      main.addEventListener('scroll',function(){
        if(document.body.classList.contains('index-window-open')&&main.scrollTop)main.scrollTop=0;
      },{passive:true});
    }
  }else if(!on&&prev&&main&&cb){
    var keep2=cb.scrollTop;
    cb.scrollTop=0;
    if(keep2)main.scrollTop=keep2;
  }
"""


def once(s, old, new, label):
    n = s.count(old)
    if n != 1:
        raise SystemExit(f"{label}: count {n}")
    return s.replace(old, new, 1)


def patch(path: Path) -> None:
    raw = path.read_bytes()
    t = raw.decode("utf-8")
    n = path.name
    old_len = len(raw)
    if t.count(CSS_MARK) != 1:
        raise SystemExit(f"{n}: css mark {t.count(CSS_MARK)}")
    if "fix-KW-FS-SLOT" not in t:
        t = t.replace(CSS_MARK, CSS_ADD, 1)
    if DOCK_OLD in t:
        t = once(t, DOCK_OLD, DOCK_NEW, f"{n} dock-on")
    elif "var on=!!(window.CATALOG_PORTABLE&&ix&&!ix.classList.contains('is-embedded'));" not in t:
        raise SystemExit(f"{n}: dock-on missing")
    if FILL_OLD in t:
        t = once(t, FILL_OLD, FILL_NEW, f"{n} fill")
    elif "ix&&!ix.classList.contains('is-collapsed')&&!ix.classList.contains('is-embedded'));" not in t.split("function applyIndexFillDocStyles")[1][:400]:
        raise SystemExit(f"{n}: fill missing")
    if FS_OLD in t:
        t = once(t, FS_OLD, FS_NEW, f"{n} fs-slot")
    elif "var morePop=document.getElementById('kwStripMorePop');" not in t:
        raise SystemExit(f"{n}: fs-slot missing")
    if "fix-INDEX-MAIN-LOCK" not in t:
        t = t.replace(CSS_MARK, CSS_LOCK, 1)
    if SCROLL_OLD in t:
        t = once(t, SCROLL_OLD, SCROLL_NEW, f"{n} main-lock")
    elif "ixDockScrollBound" not in t:
        raise SystemExit(f"{n}: main-lock missing")
    out = t.encode("utf-8")
    if len(out) < int(old_len * 0.98):
        raise SystemExit(f"{n}: size drop {old_len} -> {len(out)}")
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_bytes(out)
    written = tmp.read_bytes()
    if not written.decode("utf-8").strip().endswith("</html>"):
        tmp.unlink()
        raise SystemExit(f"{n}: truncated, missing </html>")
    if len(written) != len(out):
        tmp.unlink()
        raise SystemExit(f"{n}: temp size mismatch")
    tmp.replace(path)
    print(
        "OK",
        n,
        "bytes",
        len(out),
        "was",
        old_len,
        "kwfs",
        "fix-KW-FS-SLOT" in t,
        "ixstick",
        "fix-INDEX-COLLAPSE-STICK" in t,
        "lock",
        "fix-INDEX-MAIN-LOCK" in t,
        "bound",
        "ixDockScrollBound" in t,
    )


def main() -> None:
    for p in FILES:
        patch(p)


if __name__ == "__main__":
    main()
