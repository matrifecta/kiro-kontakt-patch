#!/usr/bin/env python3
"""Grid selected card: scroll desc panel first; forward catalog only at desc bounds."""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

ROOT = Path("/home/phnx/kiro-kontakt-patch")
FILES = [
    ROOT / "public/catalogs/KONTAKT-CATALOG.html",
    ROOT / "public/catalogs/DS-CATALOG.html",
    ROOT / "public/catalogs/KONTAKT-CATALOG-portable.html",
    ROOT / "public/catalogs/DS-CATALOG-portable.html",
]

MARK = "fix-GRID-DESC-WHEEL-v1"
CSS_ANCHOR = "/* fix-CARD-SCROLL-CLIP:"
CSS_ADD = rf"""/* {MARK}: outlined grid card — desc panel scrolls before catalog forward */
body:not(.chosen-preview-open) .entry.selected:not(.highlight) .summary-panel{{
  height:8.2em!important;max-height:8.2em!important;
  overflow-x:hidden!important;overflow-y:auto!important;
  overscroll-behavior:contain!important;-webkit-overflow-scrolling:touch!important;
  touch-action:auto!important;pointer-events:auto!important
}}
body:not(.chosen-preview-open) .entry.selected:not(.highlight) .summary-panel .desc,
body:not(.chosen-preview-open) .entry.selected:not(.highlight) .desc{{
  max-height:none!important;overflow:visible!important;pointer-events:auto!important
}}

"""

INNER_OLD = """function catalogInnerWheelEl(field){
  if(!field)return null;
  var path=field.classList.contains('path')?field:field.closest('.path');
  if(path&&path.classList.contains('is-expanded')){
    var oy=getComputedStyle(path).overflowY;
    if((oy==='auto'||oy==='scroll'||oy==='overlay')&&path.scrollHeight>path.clientHeight+1)return path;
  }
  var panel=field.classList.contains('summary-panel')?field:field.closest('.summary-panel');
  if(!panel)return null;
  var oy2=getComputedStyle(panel).overflowY;
  if(oy2!=='auto'&&oy2!=='scroll'&&oy2!=='overlay')return null;
  if(panel.scrollHeight<=panel.clientHeight+1)return null;
  return panel;
}"""

INNER_NEW = """function catalogInnerWheelEl(field){
  if(!field)return null;
  function pickScroll(el){
    if(!el)return null;
    var oy=getComputedStyle(el).overflowY;
    if(oy!=='auto'&&oy!=='scroll'&&oy!=='overlay')return null;
    if(el.scrollHeight<=el.clientHeight+1)return null;
    return el;
  }
  var path=field.classList.contains('path')?field:field.closest('.path');
  if(path&&path.classList.contains('is-expanded')){var p=pickScroll(path);if(p)return p;}
  var panel=field.classList.contains('summary-panel')?field:field.closest('.summary-panel');
  if(panel){
    var pan=pickScroll(panel);
    if(pan)return pan;
    var desc=panel.querySelector('.desc')||field.closest('.desc');
    var d=pickScroll(desc);
    if(d)return d;
  }
  return null;
}"""

WHEEL_OLD = """  var preview=b.contains('chosen-preview-open');
  var hl=ent.classList.contains('highlight')||b.contains('hl-open');
  if(preview||hl){
    var inner=catalogInnerWheelEl(field);
    if(inner&&catalogApplyWheel(inner,dy)){e.preventDefault();return;}
    var overlay=hl?(ent.querySelector('.hl-body')||ent):ent;
    if(catalogApplyWheel(overlay,dy)){e.preventDefault();return;}
    return;
  }
  var sc=catalogPickWheelScroller();
  if(!sc)return;
  var before=sc.scrollTop;
  sc.scrollTop=before+dy;
  if(sc.scrollTop!==before)e.preventDefault();"""

WHEEL_NEW = """  var preview=b.contains('chosen-preview-open');
  var hl=ent.classList.contains('highlight')||b.contains('hl-open');
  var inner=catalogInnerWheelEl(field);
  if(inner&&catalogApplyWheel(inner,dy)){e.preventDefault();return;}
  if(preview||hl){
    var overlay=hl?(ent.querySelector('.hl-body')||ent):ent;
    if(catalogApplyWheel(overlay,dy)){e.preventDefault();return;}
    return;
  }
  var sc=(typeof catalogContentScroller==='function'&&catalogContentScroller())||catalogPickWheelScroller();
  if(!sc)return;
  var before=sc.scrollTop;
  sc.scrollTop=before+dy;
  if(sc.scrollTop!==before)e.preventDefault();"""


def once(text: str, old: str, new: str, label: str, required: bool = True) -> str:
    if old not in text:
        if new in text or (not required and MARK in text):
            print(f"  skip {label}")
            return text
        if required:
            raise SystemExit(f"MISSING [{label}]")
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

    CSS_OLD = """/* fix-GRID-DESC-WHEEL-v1: outlined grid card — desc panel scrolls before catalog forward */
.entry.selected:not(.highlight) .summary-panel{
  height:8.2em!important;max-height:8.2em!important;
  overflow-x:hidden!important;overflow-y:auto!important;
  overscroll-behavior:contain!important;-webkit-overflow-scrolling:touch!important;
  touch-action:auto!important;pointer-events:auto!important
}
.entry.selected:not(.highlight) .summary-panel .desc,
.entry.selected:not(.highlight) .desc{
  max-height:none!important;overflow:visible!important;pointer-events:auto!important
}

"""
    if f"/* {MARK}:" not in text:
        if CSS_ANCHOR not in text:
            raise SystemExit(f"{path.name}: no CSS anchor")
        text = text.replace(CSS_ANCHOR, CSS_ADD + CSS_ANCHOR, 1)
        print(f"  OK css-{MARK}")
    elif "body:not(.chosen-preview-open) .entry.selected:not(.highlight) .summary-panel" not in text:
        text = once(text, CSS_OLD, CSS_ADD, "css-grid-scope", required=False)

    text = once(text, WHEEL_OLD, WHEEL_NEW, "wheel-desc-first")
    text = once(text, INNER_OLD, INNER_NEW, "inner-wheel-el")

    if f"/* {MARK}:" not in text or "var inner=catalogInnerWheelEl(field);" not in text.split("if(preview||hl){")[0]:
        raise SystemExit(f"VERIFY FAIL {path.name}")
    safe_write(path, text)


def main() -> None:
    for p in FILES:
        patch_html(p)
    print("MARK", MARK)
    if "--verify" in sys.argv:
        import subprocess

        v = ROOT / "kiro/_patch/verify_catalog_desc_wheel_grid.py"
        if v.is_file():
            subprocess.run([sys.executable, str(v)], cwd=str(ROOT), check=False)
    print("OK", MARK)


if __name__ == "__main__":
    main()
