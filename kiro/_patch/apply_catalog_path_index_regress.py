#!/usr/bin/env python3
"""Fix path/folder visibility, desc row alignment, Index Embed in-flow block.

Root cause: fix-PATH-FOLDER-GAP-v2 set font-size:0 on .path so height:2.75em → 0px
(overflow:hidden clips code/folder). Index embed needs opaque in-flow block in .catalog-body.
"""
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

MARK = "fix-PATH-INDEX-REGRESS-v1"
PATH_V2 = "fix-PATH-FOLDER-GAP-v2"
PATH_V3 = "fix-PATH-FOLDER-GAP-v3"
INDEX_MARK = "fix-INDEX-EMBED-BLOCK-v1"

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

PATH_GAP_V3_BLOCK = """/* fix-PATH-COLLAPSE: one-line path by default; click expands in-card then overlay */
/* fix-PATH-FOLDER-GAP-v3: flex row; rem height (not em on zero-font parent); distinct hit boxes */
.entry .path{
  cursor:default;box-sizing:border-box;min-width:0;
  margin:.35rem 0 .65rem!important;position:static!important;
  font-size:.8125rem!important;line-height:1.2!important
}
.entry .path:not(.is-expanded){
  display:flex!important;flex-direction:row!important;flex-wrap:nowrap!important;
  align-items:center!important;gap:.45rem!important;
  min-height:2.75rem!important;height:auto!important;max-height:2.75rem!important;
  overflow:hidden!important
}
.entry .path b{flex:0 0 auto!important;cursor:pointer;white-space:nowrap!important}
.entry .path code{cursor:pointer;position:static!important;z-index:auto!important}
.entry .path:not(.is-expanded) code{
  flex:1 1 auto!important;min-width:2.5rem!important;max-width:100%!important;
  display:block!important;overflow:hidden!important;text-overflow:ellipsis!important;
  white-space:nowrap!important;word-break:normal!important;overflow-wrap:normal!important
}
.entry .path:not(.is-expanded) .path-fs-hit{display:none!important}
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
  display:flex!important;flex-direction:column!important;align-items:flex-start!important;
  min-height:0!important;height:auto!important;max-height:none!important;
  overflow:visible!important;gap:.32rem!important
}
.entry .path.is-expanded code{
  flex:1 1 100%!important;width:100%!important;min-width:0!important;display:block!important;
  white-space:normal!important;overflow:visible!important;
  word-break:break-word!important;overflow-wrap:anywhere!important;text-overflow:clip!important
}
.entry .path.is-expanded .folder,.entry .path.is-expanded .path-fs-hit{
  flex:0 0 auto!important;align-self:flex-start!important;margin-top:.05rem!important
}
.entry.selected:not(.highlight) .path:not(.is-expanded),
.entry.highlight .path:not(.is-expanded),
body.chosen-preview-open .entry.selected:not(.highlight) .path:not(.is-expanded){
  min-height:2.75rem!important;height:auto!important;max-height:2.75rem!important;
  overflow:hidden!important
}
.entry.selected:not(.highlight) .path.is-expanded,
.entry.highlight .path.is-expanded,
body.chosen-preview-open .entry.selected:not(.highlight) .path.is-expanded{
  min-height:0!important;height:auto!important;max-height:none!important;
  overflow:visible!important
}"""

INDEX_EMBED_ANCHOR = "/* fix-DOC-NOTE-EMBED: About in-flow with cards; no second bottom dock */"
INDEX_EMBED_BLOCK = """/* fix-INDEX-EMBED-BLOCK-v1: Embed Index is opaque in-flow block above cards in scroller */
#catalogMain>.catalog-body>#catalogIndex.is-embedded,
body.display-sides #catalogMain .catalog-body>#catalogIndex.is-embedded,
body.display-middle #catalogMain .catalog-body>#catalogIndex.is-embedded,
body.catalog-portable #catalogMain .catalog-body>#catalogIndex.is-embedded{
  position:relative!important;top:auto!important;left:auto!important;right:auto!important;
  background:var(--bg-surface)!important;border:1px solid var(--border)!important;
  isolation:isolate!important;z-index:2!important;pointer-events:auto!important;
  box-sizing:border-box!important;box-shadow:none!important;border-radius:8px;
  width:100%!important;max-width:100%!important;margin:.45rem 0 .75rem!important;
  height:auto!important;max-height:none!important;overflow:visible!important;
  flex:0 0 auto!important;display:flex!important;flex-direction:column!important
}
#catalogMain>.catalog-body>#catalogIndex.is-embedded:not(.is-collapsed),
#catalogMain>.catalog-body>#catalogIndex.is-embedded:not(.is-collapsed) .index,
#catalogMain>.catalog-body>#catalogIndex.is-embedded:not(.is-collapsed) #catalogIndexList{
  background:var(--bg-surface)!important
}
body.display-sides #catalogMain .catalog-body>#catalogIndex.is-embedded #indexHeight{display:none!important}
"""

TITLE_BAND_OLD = """  var maxTitle=0;
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
  }"""

TITLE_BAND_NEW = """  var maxTitleBand=0;
  var visCards=[];
  groups.forEach(function(group){
    group.querySelectorAll(':scope > .entry').forEach(function(e){
      if(e.classList.contains('is-hidden')||e.classList.contains('highlight'))return;
      if(e.style.display==='none')return;
      var r=e.getBoundingClientRect();
      if(!(r.width>2&&r.height>2))return;
      visCards.push(e);
      var n=e.querySelector('.lib-name');
      var sp=e.querySelector('.summary-panel');
      if(n&&sp){
        var band=Math.round(sp.getBoundingClientRect().top-n.getBoundingClientRect().top);
        if(band>0)maxTitleBand=Math.max(maxTitleBand,band);
      }else if(n){
        maxTitleBand=Math.max(maxTitleBand,n.getBoundingClientRect().height);
      }
    });
  });
  if(maxTitleBand>0){
    var tb=Math.round(maxTitleBand);
    visCards.forEach(function(e){
      var n=e.querySelector('.lib-name');
      if(!n)return;
      var notes=e.querySelector('.lib-notes');
      var notesH=notes?Math.round(notes.getBoundingClientRect().height):0;
      n.style.minHeight=Math.max(0,tb-notesH)+'px';
    });
  }"""

TITLE_BAND_CLEAR = """  var maxTitleBand=0;
  var visCards=[];
  groups.forEach(function(group){
    group.querySelectorAll(':scope > .entry').forEach(function(e){
      if(e.classList.contains('is-hidden')||e.classList.contains('highlight'))return;
      if(e.style.display==='none')return;
      var r=e.getBoundingClientRect();
      if(!(r.width>2&&r.height>2))return;
      visCards.push(e);
      var n=e.querySelector('.lib-name');
      var sp=e.querySelector('.summary-panel');
      if(n&&sp){
        var band=Math.round(sp.getBoundingClientRect().top-n.getBoundingClientRect().top);
        if(band>0)maxTitleBand=Math.max(maxTitleBand,band);
      }else if(n){
        maxTitleBand=Math.max(maxTitleBand,n.getBoundingClientRect().height);
      }
    });
  });
  if(maxTitleBand>0){
    var tb=Math.round(maxTitleBand);
    visCards.forEach(function(e){
      var n=e.querySelector('.lib-name');
      if(!n)return;
      var notes=e.querySelector('.lib-notes');
      var notesH=notes?Math.round(notes.getBoundingClientRect().height):0;
      n.style.minHeight=Math.max(0,tb-notesH)+'px';
    });
  }
  var rowLog=null;"""

TITLE_BAND_ROW = """      var maxBand=0;
      row.cards.forEach(function(e){
        var n=e.querySelector('.lib-name');
        var sp=e.querySelector('.summary-panel');
        if(n&&sp){
          var band=Math.round(sp.getBoundingClientRect().top-n.getBoundingClientRect().top);
          if(band>0)maxBand=Math.max(maxBand,band);
        }else if(n){
          maxBand=Math.max(maxBand,n.getBoundingClientRect().height);
        }
      });
      if(maxBand>0){
        var tb=Math.round(maxBand);
        row.cards.forEach(function(e){
          var n=e.querySelector('.lib-name');
          if(!n)return;
          var notes=e.querySelector('.lib-notes');
          var notesH=notes?Math.round(notes.getBoundingClientRect().height):0;
          n.style.minHeight=Math.max(0,tb-notesH)+'px';
        });
      }
"""

TITLE_BAND_ROW_ANCHOR = """      if(!rowLog)rowLog={n:row.cards.length,colMh:colMh,hs:row.cards.map(function(e){return Math.round(e.getBoundingClientRect().height);}),open:row.cards.map(function(e){return !!e.querySelector('details.patches[open]');}),paths:row.cards.map(function(e){var p=e.querySelector('.path');return !!(p&&p.classList.contains('is-expanded'));})};
    });"""

TOGGLE_IX_OLD = """  if(typeof applyIndexScrollFit==='function')applyIndexScrollFit();
};
function openCardSearchEmbed(type,popupUrl){"""

TOGGLE_IX_NEW = """  if(typeof applyIndexScrollFit==='function')applyIndexScrollFit();
  if(box.classList.contains('is-embedded')&&typeof parkCatalogDocNote==='function')parkCatalogDocNote();
  if(typeof syncIndexWindowDock==='function')syncIndexWindowDock();
};
function openCardSearchEmbed(type,popupUrl){"""

TOGGLE_IX_PORT_OLD = """  if(typeof applyIndexScrollFit==='function')applyIndexScrollFit();
  if(typeof portableEnsureScrollMenus==='function')portableEnsureScrollMenus();
};
function openCardSearchEmbed(type,popupUrl){"""

TOGGLE_IX_PORT_NEW = """  if(typeof applyIndexScrollFit==='function')applyIndexScrollFit();
  if(box.classList.contains('is-embedded')&&typeof parkCatalogDocNote==='function')parkCatalogDocNote();
  if(typeof syncIndexWindowDock==='function')syncIndexWindowDock();
  if(typeof portableEnsureScrollMenus==='function')portableEnsureScrollMenus();
};
function openCardSearchEmbed(type,popupUrl){"""

F_LOG_OLD = """    fetch('http://127.0.0.1:7529/ingest/1cf46354-1d61-4c80-bd72-a340f1db1b51',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'c00e3e'},body:JSON.stringify({sessionId:'c00e3e',runId:'post-fix',hypothesisId:'F',location:'catalog:equalizeCardSections',message:'title/desc/path bands',data:{maxTitle:Math.round(maxTitle||0),nVis:visCards.length,cards:_cards},timestamp:Date.now()})}).catch(function(){});"""

F_LOG_NEW = """    fetch('http://127.0.0.1:7529/ingest/1cf46354-1d61-4c80-bd72-a340f1db1b51',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'c00e3e'},body:JSON.stringify({sessionId:'c00e3e',runId:'post-fix',hypothesisId:'F',location:'catalog:equalizeCardSections',message:'title/desc/path bands',data:{cards:_cards},timestamp:Date.now()})}).catch(function(){});"""


def once(text: str, old: str, new: str, label: str, name: str, optional: bool = False) -> str:
    if old not in text:
        if new in text or optional:
            print(f"  skip {label}")
            return text
        raise SystemExit(f"{name}: missing [{label}]")
    n = text.count(old)
    if n != 1:
        raise SystemExit(f"{name}: [{label}] count={n}")
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
    print(f"  wrote {path.name} bytes {new_size} delta {new_size - old_size}")


def patch_html(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    if not text.rstrip().endswith("</html>"):
        raise SystemExit(f"{path.name}: no </html>")
    print(f"==== {path.name}")

    if PATH_V3 in text:
        print("  skip path-v3 (already)")
    elif PATH_GAP_V2_BLOCK in text:
        text = once(text, PATH_GAP_V2_BLOCK, PATH_GAP_V3_BLOCK, "path-v2-to-v3", path.name)
    else:
        raise SystemExit(f"{path.name}: expected {PATH_V2} block")

    if INDEX_MARK in text:
        print("  skip index-embed-block (already)")
    elif INDEX_EMBED_ANCHOR in text:
        text = once(
            text,
            INDEX_EMBED_ANCHOR,
            INDEX_EMBED_BLOCK + INDEX_EMBED_ANCHOR,
            "index-embed-block",
            path.name,
        )
    else:
        raise SystemExit(f"{path.name}: missing index embed anchor")

    if TITLE_BAND_ROW.strip() in text:
        print("  skip title-band-row (already)")
    elif "var maxTitleBand=0;" in text:
        text = once(text, TITLE_BAND_CLEAR, "  var rowLog=null;", "title-band-clear", path.name)
        if TITLE_BAND_ROW_ANCHOR in text:
            text = once(text, TITLE_BAND_ROW_ANCHOR, TITLE_BAND_ROW + TITLE_BAND_ROW_ANCHOR, "title-band-row", path.name)
    elif TITLE_BAND_OLD in text:
        text = once(text, TITLE_BAND_OLD, "  var rowLog=null;", "title-band-old-clear", path.name)
        if TITLE_BAND_ROW_ANCHOR in text:
            text = once(text, TITLE_BAND_ROW_ANCHOR, TITLE_BAND_ROW + TITLE_BAND_ROW_ANCHOR, "title-band-row", path.name)

    if PATH_V3 in text and ".entry .path:not(.is-expanded) .path-fs-hit{display:none" not in text:
        text = once(
            text,
            ".entry .path:not(.is-expanded) code{\n  flex:1 1 0!important;min-width:0!important;",
            ".entry .path:not(.is-expanded) code{\n  flex:1 1 auto!important;min-width:2.5rem!important;",
            "path-code-min",
            path.name,
        )
        text = once(
            text,
            ".entry .path .path-fs-hit{\n  flex:0 0 auto!important;",
            ".entry .path:not(.is-expanded) .path-fs-hit{display:none!important}\n.entry .path .path-fs-hit{\n  flex:0 0 auto!important;",
            "path-fs-collapsed-hide",
            path.name,
        )
    elif ".entry .path:not(.is-expanded) .path-fs-hit{display:none" in text:
        print("  skip path-fs-hide (already)")

    if "box.classList.contains('is-embedded')&&typeof parkCatalogDocNote" in text:
        print("  skip toggle-index-park (already)")
    elif TOGGLE_IX_PORT_OLD in text:
        text = once(text, TOGGLE_IX_PORT_OLD, TOGGLE_IX_PORT_NEW, "toggle-index-park-port", path.name)
    elif TOGGLE_IX_OLD in text:
        text = once(text, TOGGLE_IX_OLD, TOGGLE_IX_NEW, "toggle-index-park", path.name)
    else:
        raise SystemExit(f"{path.name}: missing toggleCatalogIndex tail")

    if "maxTitleBand:Math.round(maxTitleBand" in text:
        print("  skip f-log (already)")
    elif F_LOG_OLD in text:
        text = once(text, F_LOG_OLD, F_LOG_NEW, "f-log", path.name)
    else:
        # repair partial patch: log already says maxTitleBand but JS still uses maxTitle
        F_LOG_BROKEN = """data:{maxTitleBand:Math.round(maxTitleBand||0),nVis:visCards.length,cards:_cards}"""
        if F_LOG_BROKEN in text and "var maxTitleBand=0;" not in text:
            text = once(text, TITLE_BAND_OLD, TITLE_BAND_NEW, "title-band-repair", path.name)
        else:
            print("  skip f-log")

    if PATH_V3 not in text or INDEX_MARK not in text:
        raise SystemExit(f"{path.name}: verify failed")
    if MARK not in text:
        text = text.replace(
            f"/* {PATH_V3}: flex row;",
            f"/* {MARK}: path visibility + index embed + desc band */\n/* {PATH_V3}: flex row;",
            1,
        )
    safe_write(path, text)


def main() -> None:
    for p in FILES:
        if not p.exists():
            raise SystemExit(f"missing {p}")
        patch_html(p)
    print("OK", MARK)


if __name__ == "__main__":
    main()
