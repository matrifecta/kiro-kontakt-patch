#!/usr/bin/env python3
"""Stop path icons in Index; Embed list scrolls with catalog-body (no overflow clip)."""
from pathlib import Path

ROOT = Path("/home/phnx/kiro-kontakt-patch")
FILES = [
    ROOT / "public/catalogs/KONTAKT-CATALOG.html",
    ROOT / "public/catalogs/DS-CATALOG.html",
    ROOT / "public/catalogs/KONTAKT-CATALOG-portable.html",
    ROOT / "public/catalogs/DS-CATALOG-portable.html",
]
MARK = "fix-INDEX-EMBED-SCROLL-v1"
KEEP = (
    "fix-DESKTOP-SK-PAIR",
    "fix-MIDDLE-ONE-MENU",
    "fix-DESKTOP-FLIP-ARRANGE",
    "fix-USER-PROFILES",
    "fix-INDEX-ISOLATE-v3",
    "name click expand",
    "c00e3e",
    MARK,
)


def add_indent(s, n=1):
    pad = " " * n
    return "\n".join((pad + line) if line.strip() else line for line in s.split("\n"))


def sub(text, old, new, label, optional=False, replace_all=False):
    n = text.count(old)
    if n == 1 or (replace_all and n > 0):
        return text.replace(old, new)
    if n > 1:
        raise SystemExit(f"{label}: {n} matches")
    if new in text:
        print(f"  skip {label} (already)")
        return text
    for i in range(1, 9):
        oldi, newi = add_indent(old, i), add_indent(new, i)
        ni = text.count(oldi)
        if ni == 1 or (replace_all and ni > 0):
            return text.replace(oldi, newi)
        if ni > 1:
            raise SystemExit(f"{label}: {ni} matches (indent {i})")
        if ni == 0 and newi in text:
            print(f"  skip {label} (already)")
            return text
    if optional:
        print(f"  skip {label}")
        return text
    raise SystemExit(f"{label}: not found")


CSS_OLD = """.catalog-body>#catalogIndex .fav-btn{
  display:none!important;visibility:hidden!important;pointer-events:none!important;
  width:0!important;height:0!important;min-width:0!important;min-height:0!important;
  overflow:hidden!important;opacity:0!important
}
.entry{position:relative}"""

CSS_NEW = """.catalog-body>#catalogIndex .fav-btn{
  display:none!important;visibility:hidden!important;pointer-events:none!important;
  width:0!important;height:0!important;min-width:0!important;min-height:0!important;
  overflow:hidden!important;opacity:0!important
}
/* fix-INDEX-EMBED-SCROLL-v1: Embed scrolls with catalog-body; hide path icons without clipping the name grid */
#catalogIndex.is-embedded,
#catalogIndex.is-embedded:not(.is-collapsed),
#catalogMain>.catalog-body>#catalogIndex.is-embedded,
#catalogMain>.catalog-body>#catalogIndex.is-embedded:not(.is-collapsed),
.catalog-body>#catalogIndex.is-embedded,
body.display-sides #catalogIndex.is-embedded,
body.display-sides #catalogMain .catalog-body>#catalogIndex.is-embedded,
body.display-middle #catalogMain .catalog-body>#catalogIndex.is-embedded{
  overflow:visible!important;height:auto!important;max-height:none!important;
  isolation:isolate!important;background:var(--bg-surface)!important;
  flex:0 0 auto!important;position:relative!important
}
#catalogIndex.is-embedded:not(.is-collapsed) .index,
#catalogIndex.is-embedded:not(.is-collapsed) #catalogIndexList,
#catalogMain>.catalog-body>#catalogIndex.is-embedded:not(.is-collapsed) .index,
#catalogMain>.catalog-body>#catalogIndex.is-embedded:not(.is-collapsed) #catalogIndexList,
body.display-sides #catalogIndex.is-embedded:not(.is-collapsed) .index,
body.display-sides #catalogIndex.is-embedded:not(.is-collapsed) #catalogIndexList,
body.display-middle #catalogIndex.is-embedded:not(.is-collapsed) .index,
body.display-middle #catalogIndex.is-embedded:not(.is-collapsed) #catalogIndexList{
  overflow:visible!important;overflow-x:hidden!important;overflow-y:visible!important;
  height:auto!important;max-height:none!important;flex:0 0 auto!important;
  overscroll-behavior:auto!important;touch-action:pan-y!important
}
#catalogIndex .index .path-icon-btn,
#catalogIndex .index .path-action-row,
#catalogIndex .index .path-label,
#catalogIndex .index .path-fs-hit,
#catalogIndex .index .path-copy-hit,
#catalogIndex .index a.folder,
#catalogIndex .index .folder,
#catalogIndex .index .path,
#catalogIndex .index svg.path-icon-glyph,
#catalogIndex .index img.path-icon-glyph,
#catalogIndex .index a.path-icon-btn,
#catalogIndexList .path-icon-btn,
#catalogIndexList .path-action-row,
#catalogIndexList .path-label,
#catalogIndexList .path-fs-hit,
#catalogIndexList .path-copy-hit,
#catalogIndexList a.folder,
#catalogIndexList .folder,
#catalogIndexList .path,
#catalogIndexList svg.path-icon-glyph,
#catalogIndexList img.path-icon-glyph{
  display:none!important;visibility:hidden!important;pointer-events:none!important;
  width:0!important;height:0!important;min-width:0!important;min-height:0!important;
  overflow:hidden!important;opacity:0!important
}
#catalogIndex:not(.is-embedded):not(.is-collapsed) .index,
#catalogIndex:not(.is-embedded):not(.is-collapsed) #catalogIndexList,
body.index-window-open #catalogIndex:not(.is-embedded):not(.is-collapsed) .index,
body.index-window-open #catalogIndex:not(.is-embedded):not(.is-collapsed) #catalogIndexList{
  overflow-x:hidden!important;overflow-y:auto!important
}
.entry{position:relative}"""

BIND_OLD = """document.querySelectorAll('.entry .path').forEach(function(p){
    var needsFolder=!p.querySelector('a.folder');"""

BIND_NEW = """document.querySelectorAll('.entry .path').forEach(function(p){
    if(p.closest&&p.closest('#catalogIndex,.catalog-index,#catalogIndexList,ul.index'))return;
    var needsFolder=!p.querySelector('a.folder');"""

BIND_END_OLD = """    if(folder)ensurePathIconGlyph(folder,'folder');
  });
}"""

BIND_END_NEW = """    if(folder)ensurePathIconGlyph(folder,'folder');
  });
  if(typeof stripIndexCardChrome==='function')stripIndexCardChrome();
}"""

GLYPH_OLD = """function ensurePathIconGlyph(btn,kind){
  if(!btn)return;"""

GLYPH_NEW = """function ensurePathIconGlyph(btn,kind){
  if(!btn)return;
  if(btn.closest&&btn.closest('#catalogIndex,.catalog-index,#catalogIndexList,ul.index')){try{btn.remove();}catch(err){}return;}"""

STRIP_OLD = """function stripIndexCardChrome(ix){
  ix=ix||document.getElementById('catalogIndex');
  if(!ix)return;
  ix.querySelectorAll('.path-action-row,.path-icon-btn,.path-label,.path-fs-hit,.path-copy-hit,.fav-btn,a.folder,.path').forEach(function(el){
    try{el.remove();}catch(err){
      el.style.setProperty('display','none','important');
      el.style.setProperty('visibility','hidden','important');
      el.style.setProperty('pointer-events','none','important');
      el.setAttribute('hidden','');
    }
  });
}"""

STRIP_NEW = """function stripIndexCardChrome(ix){
  ix=ix||document.getElementById('catalogIndex');
  var list=document.getElementById('catalogIndexList');
  var roots=[];
  if(ix)roots.push(ix);
  if(list&&roots.indexOf(list)<0&&!(ix&&ix.contains(list)))roots.push(list);
  var sel='.path-action-row,.path-icon-btn,.path-label,.path-fs-hit,.path-copy-hit,.fav-btn,a.folder,.path,svg.path-icon-glyph,img.path-icon-glyph';
  roots.forEach(function(root){
    root.querySelectorAll(sel).forEach(function(el){
      try{el.remove();}catch(err){
        el.style.setProperty('display','none','important');
        el.style.setProperty('visibility','hidden','important');
        el.style.setProperty('pointer-events','none','important');
        el.setAttribute('hidden','');
      }
    });
  });
}"""

WHEEL_OLD = """  var sc=(typeof catalogContentScroller==='function'&&catalogContentScroller())||catalogPickWheelScroller();
  if(!sc)return;
  var before=sc.scrollTop;
  sc.scrollTop=before+dy;
  if(sc.scrollTop!==before)e.preventDefault();
},{passive:false});
function collapseAllPatchTrees(){"""

WHEEL_NEW = """  var sc=(typeof catalogContentScroller==='function'&&catalogContentScroller())||catalogPickWheelScroller();
  if(!sc)return;
  var before=sc.scrollTop;
  sc.scrollTop=before+dy;
  if(sc.scrollTop!==before)e.preventDefault();
},{passive:false});
document.addEventListener('wheel',function(e){
  if(e.ctrlKey||e.defaultPrevented)return;
  var hit=e.target.closest&&e.target.closest('#catalogIndex,.index,#catalogIndexList');
  if(!hit)return;
  var box=document.getElementById('catalogIndex');
  if(!box||!box.classList.contains('is-embedded')||box.classList.contains('is-collapsed'))return;
  var sc=(typeof catalogPickWheelScroller==='function'&&catalogPickWheelScroller())||(typeof catalogContentScroller==='function'&&catalogContentScroller());
  if(!sc)return;
  var dy=typeof catalogWheelDeltaPx==='function'?catalogWheelDeltaPx(e):e.deltaY;
  if(typeof catalogApplyWheel==='function'&&catalogApplyWheel(sc,dy)){e.preventDefault();e.stopPropagation();}
},{passive:false});
function collapseAllPatchTrees(){"""

FIT_WHEEL_OLD = """    il.addEventListener('wheel',function(e){
      if(!document.body.classList.contains('display-sides'))return;
      var max=il.scrollHeight-il.clientHeight;"""

FIT_WHEEL_NEW = """    il.addEventListener('wheel',function(e){
      if(!document.body.classList.contains('display-sides'))return;
      if(ix&&ix.classList.contains('is-embedded'))return;
      var max=il.scrollHeight-il.clientHeight;"""


def patch(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    n = path.name
    if MARK in text:
        print("skip", n)
        return
    text = sub(text, CSS_OLD, CSS_NEW, f"{n}: css")
    text = sub(text, BIND_OLD, BIND_NEW, f"{n}: bind-skip", replace_all=True)
    text = sub(text, BIND_END_OLD, BIND_END_NEW, f"{n}: bind-strip", replace_all=True)
    text = sub(text, GLYPH_OLD, GLYPH_NEW, f"{n}: glyph")
    text = sub(text, STRIP_OLD, STRIP_NEW, f"{n}: strip")
    text = sub(text, WHEEL_OLD, WHEEL_NEW, f"{n}: embed-wheel")
    text = sub(text, FIT_WHEEL_OLD, FIT_WHEEL_NEW, f"{n}: fit-wheel", optional=True)
    raw = text.encode("utf-8")
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_bytes(raw)
    out = tmp.read_bytes().decode("utf-8")
    if not out.strip().endswith("</html>"):
        tmp.unlink()
        raise SystemExit(f"{n}: truncated")
    if len(raw) < 100000:
        tmp.unlink()
        raise SystemExit(f"{n}: size too small {len(raw)}")
    for keep in KEEP:
        if keep not in out:
            tmp.unlink()
            raise SystemExit(f"{n}: lost {keep}")
    tmp.replace(path)
    print("OK", n, len(raw))


def main() -> None:
    for p in FILES:
        if not p.exists():
            raise SystemExit(f"missing {p}")
        patch(p)


if __name__ == "__main__":
    main()
