#!/usr/bin/env python3
"""Collapsed cards share equal row height; expanded cards grow solo (no sibling sync).
Separate path text from [open folder] / path-fs hit boxes (flex + gap, no overlap)."""
from __future__ import annotations

import os
import tempfile
from pathlib import Path

ROOT = Path("/home/phnx/kiro-kontakt-patch")
FILES = [
    ROOT / "public/catalogs/KONTAKT-CATALOG.html",
    ROOT / "public/catalogs/DS-CATALOG.html",
    ROOT / "public/catalogs/KONTAKT-CATALOG-portable.html",
    ROOT / "public/catalogs/DS-CATALOG-portable.html",
]

MARK = "fix-ROW-EXPAND-SOLO"
MARK_PREV = "fix-ROW-EXPAND-SPLIT"
PATH_MARK = "fix-PATH-FOLDER-GAP"
PATH_MARK_V2 = "fix-PATH-FOLDER-GAP-v2"

PATH_FS_OLD = """.entry .path .path-fs-hit{
  font:inherit;font-size:.8125rem;line-height:1.2;cursor:pointer;touch-action:manipulation;
  border:1px solid var(--border);border-radius:6px;background:var(--bg-surface);color:var(--text-muted);
  min-height:2rem;padding:.25rem .55rem
}
.entry .path.is-expanded code{cursor:pointer}
.entry .path.is-expanded code:hover{text-decoration:underline;text-decoration-style:dotted}

/* fix-PATH-COLLAPSE: one-line path by default; click expands in-card then overlay */
.entry .path{
  cursor:pointer;box-sizing:border-box;min-width:0;
  margin:.35rem 0 .65rem!important
}
.entry .path:not(.is-expanded){
  display:flex!important;flex-wrap:nowrap!important;align-items:center!important;
  gap:.95rem;height:2.75em!important;min-height:2.75em!important;max-height:2.75em!important;
  overflow:hidden!important;white-space:nowrap!important
}
.entry .path:not(.is-expanded) code{
  display:inline-block!important;flex:1 1 auto;min-width:0;max-width:100%;
  overflow:hidden!important;text-overflow:ellipsis!important;white-space:nowrap!important;
  word-break:normal!important;overflow-wrap:normal!important
}
.entry .path .folder,
.entry .path .path-fs-hit{
  flex:0 0 auto;white-space:nowrap;display:inline-block;
  margin-left:.15rem;padding:.35rem .65rem;box-sizing:border-box
}
.entry .path.is-expanded{
  display:block!important;height:auto!important;min-height:0!important;max-height:none!important;
  overflow:visible!important;white-space:normal!important;flex-wrap:wrap!important
}
.entry .path.is-expanded code{
  display:inline!important;white-space:normal!important;overflow:visible!important;
  word-break:break-word!important;overflow-wrap:anywhere!important;text-overflow:clip!important
}
.entry.selected:not(.highlight) .path:not(.is-expanded),
.entry.highlight .path:not(.is-expanded),
body.chosen-preview-open .entry.selected:not(.highlight) .path:not(.is-expanded){
  height:2.75em!important;min-height:2.75em!important;max-height:2.75em!important;
  overflow:hidden!important;white-space:nowrap!important
}
.entry.selected:not(.highlight) .path.is-expanded,
.entry.highlight .path.is-expanded,
body.chosen-preview-open .entry.selected:not(.highlight) .path.is-expanded{
  height:auto!important;min-height:0!important;max-height:none!important;
  overflow:visible!important;white-space:normal!important
}"""

PATH_FS_NEW = r""".entry .path .path-fs-hit{
  font:inherit;font-size:.8125rem;line-height:1.2;cursor:pointer;touch-action:manipulation;
  border:1px solid var(--border);border-radius:6px;background:var(--bg-surface);color:var(--text-muted);
  min-height:2rem;padding:.25rem .55rem
}
.entry .path.is-expanded code{cursor:pointer}
.entry .path.is-expanded code:hover{text-decoration:underline;text-decoration-style:dotted}

/* fix-PATH-COLLAPSE: one-line path by default; click expands in-card then overlay */
/* fix-PATH-FOLDER-GAP-v2: grid row; kill whitespace flex items; column when expanded */
.entry .path{
  cursor:default;box-sizing:border-box;min-width:0;
  margin:.35rem 0 .65rem!important;position:static!important;
  font-size:0!important;line-height:0!important
}
.entry .path>b,.entry .path>code,.entry .path>.folder,.entry .path>.path-fs-hit{
  font-size:.8125rem!important;line-height:1.2!important
}
.entry .path:not(.is-expanded){
  display:grid!important;grid-template-columns:auto minmax(0,1fr) auto auto!important;
  align-items:center!important;gap:.45rem!important;
  height:2.75em!important;min-height:2.75em!important;max-height:2.75em!important;
  overflow:hidden!important
}
.entry .path:not(.is-expanded)>b{grid-column:1;cursor:pointer;white-space:nowrap!important}
.entry .path:not(.is-expanded)>code{
  grid-column:2;cursor:pointer;min-width:0!important;max-width:100%!important;
  display:block!important;overflow:hidden!important;text-overflow:ellipsis!important;
  white-space:nowrap!important;word-break:normal!important;overflow-wrap:normal!important
}
.entry .path:not(.is-expanded)>.folder{grid-column:3}
.entry .path:not(.is-expanded)>.path-fs-hit{grid-column:4}
.entry .path .folder{
  white-space:nowrap!important;display:inline-block!important;
  position:relative!important;z-index:2!important;pointer-events:auto!important;
  margin:0!important;padding:.35rem .55rem!important;box-sizing:border-box!important;
  cursor:pointer!important
}
.entry .path .path-fs-hit{
  white-space:nowrap!important;display:inline-block!important;
  position:relative!important;z-index:2!important;pointer-events:auto!important;
  margin:0!important;box-sizing:border-box!important
}
.entry .path.is-expanded{
  display:flex!important;flex-direction:column!important;align-items:flex-start!important;
  font-size:.8125rem!important;line-height:1.2!important;
  height:auto!important;min-height:0!important;max-height:none!important;
  overflow:visible!important;gap:.32rem!important
}
.entry .path.is-expanded>code{
  cursor:pointer;width:100%!important;min-width:0!important;display:block!important;
  white-space:normal!important;overflow:visible!important;
  word-break:break-word!important;overflow-wrap:anywhere!important
}
.entry .path.is-expanded>.folder,.entry .path.is-expanded>.path-fs-hit{
  align-self:flex-start!important;margin-top:.05rem!important
}
.entry.selected:not(.highlight) .path:not(.is-expanded),
.entry.highlight .path:not(.is-expanded),
body.chosen-preview-open .entry.selected:not(.highlight) .path:not(.is-expanded){
  height:2.75em!important;min-height:2.75em!important;max-height:2.75em!important;
  overflow:hidden!important
}
.entry.selected:not(.highlight) .path.is-expanded,
.entry.highlight .path.is-expanded,
body.chosen-preview-open .entry.selected:not(.highlight) .path.is-expanded{
  height:auto!important;min-height:0!important;max-height:none!important;
  overflow:visible!important
}"""

PATH_GAP_V1_BLOCK = """/* fix-PATH-COLLAPSE: one-line path by default; click expands in-card then overlay */
/* fix-PATH-FOLDER-GAP: path text vs folder/fs — flex row, distinct hit boxes */
.entry .path{
  cursor:default;box-sizing:border-box;min-width:0;
  margin:.35rem 0 .65rem!important;
  display:flex!important;flex-direction:row!important;flex-wrap:nowrap!important;
  align-items:center!important;gap:.45rem!important;position:static!important
}
.entry .path b{flex:0 0 auto!important;cursor:pointer;white-space:nowrap!important}
.entry .path code{cursor:pointer;position:static!important;z-index:auto!important}
.entry .path:not(.is-expanded){
  height:2.75em!important;min-height:2.75em!important;max-height:2.75em!important;
  overflow:hidden!important
}
.entry .path:not(.is-expanded) code{
  flex:1 1 0!important;min-width:0!important;max-width:100%!important;
  display:block!important;overflow:hidden!important;text-overflow:ellipsis!important;
  white-space:nowrap!important;word-break:normal!important;overflow-wrap:normal!important
}
.entry .path .folder{
  flex:0 0 auto!important;white-space:nowrap!important;display:inline-block!important;
  position:relative!important;z-index:2!important;pointer-events:auto!important;
  margin:0!important;padding:.35rem .55rem!important;box-sizing:border-box!important;
  cursor:pointer!important
}
.entry .path .path-fs-hit{
  flex:0 0 auto!important;white-space:nowrap!important;display:inline-block!important;
  position:relative!important;z-index:2!important;pointer-events:auto!important;
  margin:0!important;box-sizing:border-box!important
}
.entry .path.is-expanded{
  flex-wrap:wrap!important;height:auto!important;min-height:0!important;max-height:none!important;
  overflow:visible!important;align-items:flex-start!important;gap:.35rem .5rem!important
}
.entry .path.is-expanded code{
  flex:1 1 100%!important;min-width:0!important;display:block!important;
  white-space:normal!important;overflow:visible!important;
  word-break:break-word!important;overflow-wrap:anywhere!important;text-overflow:clip!important
}
.entry .path.is-expanded .folder,
.entry .path.is-expanded .path-fs-hit{flex:0 0 auto!important;margin-top:.08rem!important}
.entry.selected:not(.highlight) .path:not(.is-expanded),
.entry.highlight .path:not(.is-expanded),
body.chosen-preview-open .entry.selected:not(.highlight) .path:not(.is-expanded){
  height:2.75em!important;min-height:2.75em!important;max-height:2.75em!important;
  overflow:hidden!important
}
.entry.selected:not(.highlight) .path.is-expanded,
.entry.highlight .path.is-expanded,
body.chosen-preview-open .entry.selected:not(.highlight) .path.is-expanded{
  height:auto!important;min-height:0!important;max-height:none!important;
  overflow:visible!important
}"""

PATH_GAP_V2_BLOCK = """/* fix-PATH-COLLAPSE: one-line path by default; click expands in-card then overlay */
/* fix-PATH-FOLDER-GAP-v2: grid row; kill whitespace flex items; column when expanded */
.entry .path{
  cursor:default;box-sizing:border-box;min-width:0;
  margin:.35rem 0 .65rem!important;position:static!important;
  font-size:0!important;line-height:0!important
}
.entry .path>b,.entry .path>code,.entry .path>.folder,.entry .path>.path-fs-hit{
  font-size:.8125rem!important;line-height:1.2!important
}
.entry .path:not(.is-expanded){
  display:grid!important;grid-template-columns:auto minmax(0,1fr) auto auto!important;
  align-items:center!important;gap:.45rem!important;
  height:2.75em!important;min-height:2.75em!important;max-height:2.75em!important;
  overflow:hidden!important
}
.entry .path:not(.is-expanded)>b{grid-column:1;cursor:pointer;white-space:nowrap!important}
.entry .path:not(.is-expanded)>code{
  grid-column:2;cursor:pointer;min-width:0!important;max-width:100%!important;
  display:block!important;overflow:hidden!important;text-overflow:ellipsis!important;
  white-space:nowrap!important;word-break:normal!important;overflow-wrap:normal!important
}
.entry .path:not(.is-expanded)>.folder{grid-column:3}
.entry .path:not(.is-expanded)>.path-fs-hit{grid-column:4}
.entry .path .folder{
  white-space:nowrap!important;display:inline-block!important;
  position:relative!important;z-index:2!important;pointer-events:auto!important;
  margin:0!important;padding:.35rem .55rem!important;box-sizing:border-box!important;
  cursor:pointer!important
}
.entry .path .path-fs-hit{
  white-space:nowrap!important;display:inline-block!important;
  position:relative!important;z-index:2!important;pointer-events:auto!important;
  margin:0!important;box-sizing:border-box!important
}
.entry .path.is-expanded{
  display:flex!important;flex-direction:column!important;align-items:flex-start!important;
  font-size:.8125rem!important;line-height:1.2!important;
  height:auto!important;min-height:0!important;max-height:none!important;
  overflow:visible!important;gap:.32rem!important
}
.entry .path.is-expanded>code{
  cursor:pointer;width:100%!important;min-width:0!important;display:block!important;
  white-space:normal!important;overflow:visible!important;
  word-break:break-word!important;overflow-wrap:anywhere!important
}
.entry .path.is-expanded>.folder,.entry .path.is-expanded>.path-fs-hit{
  align-self:flex-start!important;margin-top:.05rem!important
}
.entry.selected:not(.highlight) .path:not(.is-expanded),
.entry.highlight .path:not(.is-expanded),
body.chosen-preview-open .entry.selected:not(.highlight) .path:not(.is-expanded){
  height:2.75em!important;min-height:2.75em!important;max-height:2.75em!important;
  overflow:hidden!important
}
.entry.selected:not(.highlight) .path.is-expanded,
.entry.highlight .path.is-expanded,
body.chosen-preview-open .entry.selected:not(.highlight) .path.is-expanded{
  height:auto!important;min-height:0!important;max-height:none!important;
  overflow:visible!important
}"""

IS_EXPANDED_HELPER = r"""function catalogCardIsExpanded(e){
  if(!e)return false;
  if(e.querySelector('details.patches[open],details.grp[open]'))return true;
  var p=e.querySelector('.path');
  return !!(p&&p.classList.contains('is-expanded'));
}
"""

EQ_ROW_OLD = """    rows.forEach(function(row){
      if(row.cards.length<2)return;
      var maxH=0;
      row.cards.forEach(function(e){
        var r=e.getBoundingClientRect();
        var h=r.height,w=r.width;
        if(catalogCardHeightCube(h,w))return;
        maxH=Math.max(maxH,h);
      });
      if(!(maxH>0)){
        row.cards.forEach(function(e){maxH=Math.max(maxH,e.getBoundingClientRect().height);});
      }
      var mh=Math.round(maxH);
      if(!(mh>0))return;
      row.cards.forEach(function(e){
        var w=e.getBoundingClientRect().width;
        var use=mh;
        if(catalogCardHeightCube(mh,w))use=Math.round(e.getBoundingClientRect().height);
        e.style.minHeight=use>0?use+'px':'';
      });
      if(!rowLog)rowLog={n:row.cards.length,mh:mh,hs:row.cards.map(function(e){return Math.round(e.getBoundingClientRect().height);}),open:row.cards.map(function(e){return !!e.querySelector('details.patches[open]');}),paths:row.cards.map(function(e){var p=e.querySelector('.path');return !!(p&&p.classList.contains('is-expanded'));})};
    });"""

EQ_ROW_SPLIT = """    rows.forEach(function(row){
      if(row.cards.length<2)return;
      var collapsedMax=0,expandedMax=0;
      row.cards.forEach(function(e){
        var r=e.getBoundingClientRect();
        var h=r.height,w=r.width;
        if(catalogCardHeightCube(h,w))return;
        if(typeof catalogCardIsExpanded==='function'&&catalogCardIsExpanded(e)){
          expandedMax=Math.max(expandedMax,h);
        }else{
          collapsedMax=Math.max(collapsedMax,h);
        }
      });
      if(!(collapsedMax>0)&&!(expandedMax>0)){
        row.cards.forEach(function(e){collapsedMax=Math.max(collapsedMax,e.getBoundingClientRect().height);});
      }
      var colMh=collapsedMax>0?Math.round(collapsedMax):0;
      var expMh=expandedMax>0?Math.round(expandedMax):0;
      row.cards.forEach(function(e){
        var w=e.getBoundingClientRect().width;
        var exp=typeof catalogCardIsExpanded==='function'&&catalogCardIsExpanded(e);
        var use=exp?expMh:colMh;
        if(!use)return;
        if(catalogCardHeightCube(use,w))use=Math.round(e.getBoundingClientRect().height);
        e.style.minHeight=use>0?use+'px':'';
      });
      if(!rowLog)rowLog={n:row.cards.length,colMh:colMh,expMh:expMh,mh:colMh||expMh,hs:row.cards.map(function(e){return Math.round(e.getBoundingClientRect().height);}),open:row.cards.map(function(e){return !!e.querySelector('details.patches[open]');}),paths:row.cards.map(function(e){var p=e.querySelector('.path');return !!(p&&p.classList.contains('is-expanded'));})};
    });"""

EQ_ROW_SOLO = """    rows.forEach(function(row){
      if(row.cards.length<2)return;
      var collapsedMax=0;
      row.cards.forEach(function(e){
        if(typeof catalogCardIsExpanded==='function'&&catalogCardIsExpanded(e))return;
        var r=e.getBoundingClientRect();
        var h=r.height,w=r.width;
        if(catalogCardHeightCube(h,w))return;
        collapsedMax=Math.max(collapsedMax,h);
      });
      if(!(collapsedMax>0)){
        row.cards.forEach(function(e){
          if(typeof catalogCardIsExpanded==='function'&&catalogCardIsExpanded(e))return;
          collapsedMax=Math.max(collapsedMax,e.getBoundingClientRect().height);
        });
      }
      var colMh=collapsedMax>0?Math.round(collapsedMax):0;
      row.cards.forEach(function(e){
        if(typeof catalogCardIsExpanded==='function'&&catalogCardIsExpanded(e)){
          e.style.minHeight='';
          return;
        }
        if(!colMh)return;
        var w=e.getBoundingClientRect().width;
        var use=colMh;
        if(catalogCardHeightCube(colMh,w))use=Math.round(e.getBoundingClientRect().height);
        e.style.minHeight=use>0?use+'px':'';
      });
      if(!rowLog)rowLog={n:row.cards.length,colMh:colMh,hs:row.cards.map(function(e){return Math.round(e.getBoundingClientRect().height);}),open:row.cards.map(function(e){return !!e.querySelector('details.patches[open]');}),paths:row.cards.map(function(e){var p=e.querySelector('.path');return !!(p&&p.classList.contains('is-expanded'));})};
    });"""

PATH_CLICK_OLD = """    if(e.target.closest('.path')){
      var pathBox=e.target.closest('.path');
      if(e.target.closest('.path-fs-hit')){activatePath(entry);return;}
      if(!pathBox.classList.contains('is-expanded')){"""

PATH_CLICK_NEW = """    if(e.target.closest('.path')){
      var pathBox=e.target.closest('.path');
      if(e.target.closest('.folder'))return;
      if(e.target.closest('.path-fs-hit')){activatePath(entry);return;}
      if(!pathBox.classList.contains('is-expanded')){"""


def once(text: str, old: str, new: str, label: str, required: bool = True) -> str:
    if old not in text:
        if new in text or (not required and (MARK in text or PATH_MARK in text)):
            print(f"  skip {label}")
            return text
        if required:
            raise SystemExit(f"MISSING [{label}] in patch target")
        print(f"  skip {label} (optional)")
        return text
    n = text.count(old)
    if n != 1:
        raise SystemExit(f"COUNT [{label}]: {n}")
    print(f"  OK {label}")
    return text.replace(old, new, 1)


def safe_write(path: Path, text: str) -> None:
    if not text.rstrip().endswith("</html>"):
        raise SystemExit(f"{path.name}: bad end before write")
    old_size = path.stat().st_size
    fd, tmp_name = tempfile.mkstemp(suffix=".html", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as tmp:
            tmp.write(text)
        check = Path(tmp_name).read_text(encoding="utf-8")
        if not check.rstrip().endswith("</html>"):
            raise SystemExit(f"{path.name}: temp lost </html>")
        new_size = Path(tmp_name).stat().st_size
        if new_size < old_size * 0.5:
            raise SystemExit(f"{path.name}: size drop {old_size} -> {new_size}")
        os.replace(tmp_name, path)
    except Exception:
        Path(tmp_name).unlink(missing_ok=True)
        raise
    print(f"  wrote {path.name} bytes {new_size}")


def patch_html(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    if not text.rstrip().endswith("</html>"):
        raise SystemExit(f"{path.name}: no </html>")
    print(f"==== {path.name}")

    if PATH_MARK_V2 in text:
        print("  skip path-folder-gap-v2 (already)")
    elif PATH_GAP_V1_BLOCK in text:
        text = once(text, PATH_GAP_V1_BLOCK, PATH_GAP_V2_BLOCK, "path-folder-gap-v2")
    elif PATH_MARK not in text:
        text = once(text, PATH_FS_OLD, PATH_FS_NEW, "path-folder-gap")
    else:
        print("  skip path-folder-gap (already)")

    if "function catalogCardIsExpanded" not in text:
        anchor = "function equalizeCatalogCardRows(){"
        if anchor not in text:
            raise SystemExit(f"{path.name}: no equalizeCatalogCardRows")
        text = text.replace(anchor, IS_EXPANDED_HELPER + anchor, 1)
        print("  OK catalogCardIsExpanded")
    else:
        print("  skip catalogCardIsExpanded")

    if EQ_ROW_SOLO in text:
        print("  skip eq-row-expand-solo (already)")
    elif EQ_ROW_SPLIT in text:
        text = once(text, EQ_ROW_SPLIT, EQ_ROW_SOLO, "eq-row-split-to-solo")
    elif EQ_ROW_OLD in text:
        text = once(text, EQ_ROW_OLD, EQ_ROW_SOLO, "eq-row-to-solo")
    else:
        raise SystemExit(f"{path.name}: no eq-row block to patch")

    text = once(text, PATH_CLICK_OLD, PATH_CLICK_NEW, "path-click-folder", required=False)

    if (PATH_MARK_V2 not in text and PATH_MARK not in text) or "catalogCardIsExpanded" not in text:
        raise SystemExit(f"VERIFY FAIL {path.name}")
    safe_write(path, text)


def main() -> None:
    for p in FILES:
        patch_html(p)
    print("OK", MARK, PATH_MARK)


if __name__ == "__main__":
    main()
