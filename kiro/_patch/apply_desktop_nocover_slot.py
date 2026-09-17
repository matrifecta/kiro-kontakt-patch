#!/usr/bin/env python3
"""Reserve cover-slot height on desktop cards that have no .cover (noart)."""
from __future__ import annotations

import os
import tempfile
from pathlib import Path

ROOT = Path("/home/phnx/kiro-kontakt-patch")
FILES = [
    ROOT / "public/catalogs/DS-CATALOG.html",
    ROOT / "public/catalogs/KONTAKT-CATALOG.html",
]
MARK = "fix-DESKTOP-NOCOVER-SLOT-v1"

CSS_OLD = """body:not(.catalog-portable):not(.chosen-preview-open) .entry:not(.highlight) .fav-btn{
  right:.8rem;bottom:.8rem
}

/* fix-DOC-NOTE-DOCK: About/Document pinned to content-pane bottom; cards scroll above */"""

CSS_NEW = """body:not(.catalog-portable):not(.chosen-preview-open) .entry:not(.highlight) .fav-btn{
  right:.8rem;bottom:.8rem
}
/* """ + MARK + """: missing-cover tiles keep the cover band so titles line up */
body:not(.catalog-portable) .entry:not(.highlight):not(:has(.cover)) .hl-body{
  box-sizing:border-box;padding-top:calc(clamp(4.5rem,12vw,7.5rem) + .6rem)
}

/* fix-DOC-NOTE-DOCK: About/Document pinned to content-pane bottom; cards scroll above */"""

RESET_OLD = """      var _cov=e.querySelector('.cover');
      if(_cov)_cov.style.minHeight='';
      var _sp=e.querySelector('.summary-panel');
      if(_sp)_sp.style.marginTop='';
"""
RESET_NEW = """      var _cov=e.querySelector('.cover');
      if(_cov)_cov.style.minHeight='';
      var _sp=e.querySelector('.summary-panel');
      if(_sp)_sp.style.marginTop='';
      var _hb=e.querySelector('.hl-body');
      if(_hb)_hb.style.paddingTop='';
"""

APPLY_OLD = """        if(_c){
          if(_desk&&_maxCovH>0&&!_exp)_c.style.minHeight=_maxCovH+'px';
          else _c.style.minHeight='';
        }
        if(_sp)_sp.style.marginTop='';
"""
APPLY_NEW = """        var _hb=e.querySelector('.hl-body');
        if(_c){
          if(_desk&&_maxCovH>0&&!_exp)_c.style.minHeight=_maxCovH+'px';
          else _c.style.minHeight='';
          if(_hb)_hb.style.paddingTop='';
        }else if(_hb){
          if(_desk&&_maxCovH>0&&!_exp)_hb.style.paddingTop=_maxCovH+'px';
          else _hb.style.paddingTop='';
        }
        if(_sp)_sp.style.marginTop='';
"""


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
    print(f"  wrote {path.name} {old_size} -> {new_size}")


def patch_once(text: str, old: str, new: str, label: str) -> str:
    n = text.count(old)
    if n != 1:
        raise SystemExit(f"  {label}: matches {n}, expected 1")
    return text.replace(old, new, 1)


def main() -> None:
    for path in FILES:
        if "portable" in path.name:
            raise SystemExit(f"refusing portable {path.name}")
        text = path.read_text(encoding="utf-8")
        print(path.name)
        c00 = text.count("sessionId:'c00e3e'")
        if MARK in text:
            print("  skip")
            continue
        text = patch_once(text, CSS_OLD, CSS_NEW, "css")
        text = patch_once(text, RESET_OLD, RESET_NEW, "reset")
        text = patch_once(text, APPLY_OLD, APPLY_NEW, "apply")
        after = text.count("sessionId:'c00e3e'")
        if after < c00:
            raise SystemExit(f"{path.name}: lost logs {c00}->{after}")
        safe_write(path, text)


if __name__ == "__main__":
    main()
