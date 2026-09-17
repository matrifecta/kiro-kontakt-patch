#!/usr/bin/env python3
"""v2b: Search/heart same top; edge stack off first-column patch labels."""
from __future__ import annotations

import os
import tempfile
from pathlib import Path

ROOT = Path("/home/phnx/kiro-kontakt-patch")
FILES = [
    ROOT / "public/catalogs/DS-CATALOG.html",
    ROOT / "public/catalogs/KONTAKT-CATALOG.html",
]
MARK = "fix-DESKTOP-CARD-CHROME-V2b"

CSS_OLD = """body:not(.catalog-portable):not(.chosen-preview-open) .entry:not(.highlight) .card-actions{
  margin-top:0!important;margin-bottom:0!important;
  padding-top:var(--card-chrome-gap)!important;padding-bottom:0!important;
  padding-right:calc(var(--card-chrome-btn) + var(--card-chrome-gap))!important;
  align-self:stretch!important;align-items:center!important;
  min-height:var(--card-chrome-btn)!important;height:var(--card-chrome-btn)!important;
  box-sizing:border-box
}"""

CSS_NEW = """body:not(.catalog-portable):not(.chosen-preview-open) .entry:not(.highlight) .card-actions{
  margin-top:0!important;margin-bottom:0!important;
  padding-top:0!important;padding-bottom:0!important;
  padding-right:calc(var(--card-chrome-btn) + var(--card-chrome-gap))!important;
  align-self:stretch!important;align-items:center!important;
  min-height:var(--card-chrome-btn)!important;height:var(--card-chrome-btn)!important;
  box-sizing:border-box
}"""

PAD_OLD = """body:not(.catalog-portable).display-sides #catalogMain .catalog-body,
body:not(.catalog-portable).display-middle #catalogMain .catalog-body{
  padding-right:2.85rem!important
}"""

PAD_NEW = """body:not(.catalog-portable).display-sides #catalogMain .catalog-body,
body:not(.catalog-portable).display-middle #catalogMain .catalog-body{
  padding-right:2.85rem!important;padding-left:2.45rem!important
}
/* """ + MARK + """ */
body:not(.catalog-portable).display-sides #catalogEdgeStack .catalog-edge-btn,
body:not(.catalog-portable).display-middle #catalogEdgeStack .catalog-edge-btn{
  transform:none!important
}"""

JS_OLD = """            if(d>1){
              path.style.paddingTop=d+'px';
              var eh=Math.round(e.getBoundingClientRect().height);
              e.style.minHeight=Math.max(colMh,eh+d)+'px';
            }
          });
        }
      }"""

JS_NEW = """            if(d>1){
              path.style.paddingTop=d+'px';
              var eh=Math.round(e.getBoundingClientRect().height);
              e.style.minHeight=Math.max(colMh,eh+d)+'px';
            }
          });
        }
        if(typeof document!=='undefined'&&document.body)void document.body.offsetHeight;
        _bandCards.forEach(function(e){
          var s=e.querySelector('.search-popup-btn,.search-link');
          var f=e.querySelector('.fav-btn');
          if(!s||!f)return;
          var er=e.getBoundingClientRect();
          var sr=s.getBoundingClientRect();
          var bot=Math.round(er.bottom-sr.bottom);
          if(bot<0)bot=0;
          f.style.bottom=bot+'px';
        });
      }"""


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
            raise SystemExit(f"refusing portable file {path.name}")
        text = path.read_text(encoding="utf-8")
        print(path.name)
        if MARK in text:
            print("  skip (already patched)")
            continue
        text = patch_once(text, CSS_OLD, CSS_NEW, "card-actions")
        text = patch_once(text, PAD_OLD, PAD_NEW, "pad-left")
        text = patch_once(text, JS_OLD, JS_NEW, "fav-snap")
        safe_write(path, text)


if __name__ == "__main__":
    main()
