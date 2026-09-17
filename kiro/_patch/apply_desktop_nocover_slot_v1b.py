#!/usr/bin/env python3
"""Include cover margins in the no-cover title spacer."""
from __future__ import annotations

import os
import tempfile
from pathlib import Path

ROOT = Path("/home/phnx/kiro-kontakt-patch")
FILES = [
    ROOT / "public/catalogs/DS-CATALOG.html",
    ROOT / "public/catalogs/KONTAKT-CATALOG.html",
]
MARK = "fix-DESKTOP-NOCOVER-SLOT-v1b"

OLD = """        if(_h>_maxCovH){_maxCovH=_h;_refCard=e;}
      });
      var _desk=!(typeof window!=='undefined'&&window.CATALOG_PORTABLE);
      row.cards.forEach(function(e){
        var _c=e.querySelector('.cover');
        var _sp=e.querySelector('.summary-panel');
        var _exp=typeof catalogCardIsExpanded==='function'&&catalogCardIsExpanded(e);
        var _hb=e.querySelector('.hl-body');
        if(_c){
          if(_desk&&_maxCovH>0&&!_exp)_c.style.minHeight=_maxCovH+'px';
          else _c.style.minHeight='';
          if(_hb)_hb.style.paddingTop='';
        }else if(_hb){
          if(_desk&&_maxCovH>0&&!_exp)_hb.style.paddingTop=_maxCovH+'px';
          else _hb.style.paddingTop='';
        }
"""
NEW = """        if(_h>_maxCovH){_maxCovH=_h;_refCard=e;}
      });
      var _desk=!(typeof window!=='undefined'&&window.CATALOG_PORTABLE);
      var _slotH=_maxCovH;
      if(_refCard){
        var _rc=_refCard.querySelector('.cover');
        if(_rc){
          var _rcs=getComputedStyle(_rc);
          _slotH=_maxCovH+Math.round(parseFloat(_rcs.marginTop)||0)+Math.round(parseFloat(_rcs.marginBottom)||0);
        }
      }
      row.cards.forEach(function(e){
        var _c=e.querySelector('.cover');
        var _sp=e.querySelector('.summary-panel');
        var _exp=typeof catalogCardIsExpanded==='function'&&catalogCardIsExpanded(e);
        var _hb=e.querySelector('.hl-body');
        if(_c){
          if(_desk&&_maxCovH>0&&!_exp)_c.style.minHeight=_maxCovH+'px';
          else _c.style.minHeight='';
          if(_hb)_hb.style.paddingTop='';
        }else if(_hb){
          if(_desk&&_slotH>0&&!_exp)_hb.style.paddingTop=_slotH+'px';
          else _hb.style.paddingTop='';
        }
"""

CSS_OLD = "body:not(.catalog-portable) .entry:not(.highlight):not(:has(.cover)) .hl-body{\n  box-sizing:border-box;padding-top:calc(clamp(4.5rem,12vw,7.5rem) + .6rem)\n}"
CSS_OLD_B = "body:not(.catalog-portable) .entry:not(.highlight):not(:has(.cover)) .hl-body{\n  box-sizing:border-box;padding-top:clamp(4.5rem,12vw,7.5rem)\n}"
CSS_NEW = "body:not(.catalog-portable) .entry:not(.highlight):not(:has(.cover)) .hl-body{\n  box-sizing:border-box;padding-top:calc(clamp(4.5rem,12vw,7.5rem) + .6rem)\n}\n/* " + MARK + " */"


def safe_write(path: Path, text: str) -> None:
    if not text.rstrip().endswith("</html>"):
        raise SystemExit(f"{path.name}: bad end")
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
            raise SystemExit(f"{path.name}: size drop")
        os.replace(tmp_name, path)
    except Exception:
        Path(tmp_name).unlink(missing_ok=True)
        raise
    print(f"  wrote {path.name} {old_size} -> {new_size}")


def main() -> None:
    for path in FILES:
        text = path.read_text(encoding="utf-8")
        print(path.name)
        if MARK in text:
            print("  skip")
            continue
        if text.count(OLD) != 1:
            raise SystemExit(f"  measure matches {text.count(OLD)}")
        text = text.replace(OLD, NEW, 1)
        if CSS_OLD in text:
            text = text.replace(CSS_OLD, CSS_NEW, 1)
        elif CSS_OLD_B in text:
            text = text.replace(CSS_OLD_B, CSS_NEW, 1)
        else:
            raise SystemExit("  missing css")
        safe_write(path, text)


if __name__ == "__main__":
    main()
