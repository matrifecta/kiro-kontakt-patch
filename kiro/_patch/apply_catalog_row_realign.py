#!/usr/bin/env python3
"""Re-equalize row after path/patch expand/collapse; double-rAF + scroll-safe."""
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

MARK = "fix-ROW-REALIGN-v1"

SCHEDULE_OLD = """function scheduleEqualizeCardRows(){
  if(window._eqCardRows)cancelAnimationFrame(window._eqCardRows);
  window._eqCardRows=requestAnimationFrame(function(){
    window._eqCardRows=0;
    equalizeCatalogCardRows();
  });
}"""

SCHEDULE_NEW = """function scheduleEqualizeCardRows(){
  if(window._eqCardRows)cancelAnimationFrame(window._eqCardRows);
  window._eqCardRows=requestAnimationFrame(function(){
    window._eqCardRows=requestAnimationFrame(function(){
      window._eqCardRows=0;
      equalizeCatalogCardRows();
    });
  });
}"""

CLEAR_OLD = """      if(n)n.style.minHeight='';
    });
  });
  var rowLog=null;"""

CLEAR_NEW = """      if(n)n.style.minHeight='';
    });
  });
  if(typeof document!=='undefined'&&document.body)void document.body.offsetHeight;
  var rowLog=null;"""

BAND_OLD = """      var maxBand=0;
      row.cards.forEach(function(e){
        var n=e.querySelector('.lib-name');
        var sp=e.querySelector('.summary-panel');
        if(n&&sp){
          var band=Math.round(sp.getBoundingClientRect().top-n.getBoundingClientRect().top);
          if(band>0)maxBand=Math.max(maxBand,band);
        }else if(n){
          maxBand=Math.max(maxBand,n.getBoundingClientRect().height);
        }
      });"""

BAND_NEW = """      var hasExpanded=row.cards.some(function(e){
        return typeof catalogCardIsExpanded==='function'&&catalogCardIsExpanded(e);
      });
      var bandCards=row.cards;
      if(hasExpanded){
        bandCards=row.cards.filter(function(e){
          return !(typeof catalogCardIsExpanded==='function'&&catalogCardIsExpanded(e));
        });
        if(!bandCards.length)bandCards=row.cards;
      }
      var maxBand=0;
      bandCards.forEach(function(e){
        var n=e.querySelector('.lib-name');
        var sp=e.querySelector('.summary-panel');
        if(n&&sp){
          var band=Math.round(sp.getBoundingClientRect().top-n.getBoundingClientRect().top);
          if(band>0)maxBand=Math.max(maxBand,band);
        }else if(n){
          maxBand=Math.max(maxBand,n.getBoundingClientRect().height);
        }
      });"""

COLLAPSE_PATHS_OLD = """    p.setAttribute('aria-expanded','false');
    n++;
  });
  return n;
}"""

COLLAPSE_PATHS_NEW = """    p.setAttribute('aria-expanded','false');
    n++;
  });
  if(typeof scheduleEqualizeCardRows==='function')scheduleEqualizeCardRows();
  return n;
}"""

PATH_HIT_OLD = "hit.type='button';hit.className='path-fs-hit';hit.textContent='path';"
PATH_HIT_NEW = "hit.type='button';hit.className='path-fs-hit';hit.textContent='';"

SELECTED_PATH_OLD = ".entry.selected:not(.highlight) .path:not(.is-expanded){height:2.75em;max-height:2.75em;overflow:hidden;overscroll-behavior:auto;touch-action:auto}.entry.selected:not(.highlight) .path.is-expanded{max-height:none;overflow:visible}"
SELECTED_PATH_NEW = ".entry.selected:not(.highlight) .path:not(.is-expanded){min-height:2.75rem!important;height:auto!important;max-height:2.75rem!important;overflow:hidden;overscroll-behavior:auto;touch-action:auto}.entry.selected:not(.highlight) .path.is-expanded{min-height:0!important;height:auto!important;max-height:none!important;overflow:visible}"

PATH_CODE_CSS = """.entry .path:not(.is-expanded) code{color:var(--text-muted)!important;opacity:1!important}
.entry .path .folder{color:var(--accent-instrument)!important;opacity:1!important}
"""

PATH_CODE_ANCHOR = ".entry .path:not(.is-expanded) .path-fs-hit{display:none!important}"


def once(text: str, old: str, new: str, label: str, name: str, optional: bool = False) -> str:
    if old not in text:
        if new in text or optional:
            print(f"  skip {label}")
            return text
        raise SystemExit(f"{name}: missing [{label}]")
    n = text.count(old)
    if n != 1 and not (optional and n == 0):
        if optional and n == 0:
            return text
        raise SystemExit(f"{name}: [{label}] count={n}")
    print(f"  OK {label}")
    return text.replace(old, new, 1)


def replace_all(text: str, old: str, new: str, label: str, name: str) -> str:
    n = text.count(old)
    if n == 0:
        if new in text:
            print(f"  skip {label}")
            return text
        raise SystemExit(f"{name}: missing [{label}]")
    print(f"  OK {label} x{n}")
    return text.replace(old, new)


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
    print(f"  wrote {path.name} delta {Path(path).stat().st_size - old_size}")


def patch_html(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    if not text.rstrip().endswith("</html>"):
        raise SystemExit(f"{path.name}: no </html>")
    print(f"==== {path.name}")
    if MARK in text:
        print("  skip (already)")
        return

    text = once(text, SCHEDULE_OLD, SCHEDULE_NEW, "schedule-double-raf", path.name)
    text = once(text, CLEAR_OLD, CLEAR_NEW, "eq-reflow", path.name)
    text = once(text, BAND_OLD, BAND_NEW, "band-collapsed-only", path.name)
    text = replace_all(text, COLLAPSE_PATHS_OLD, COLLAPSE_PATHS_NEW, "collapse-paths-eq", path.name)
    text = replace_all(text, PATH_HIT_OLD, PATH_HIT_NEW, "path-hit-label", path.name)
    if SELECTED_PATH_OLD in text:
        text = replace_all(text, SELECTED_PATH_OLD, SELECTED_PATH_NEW, "selected-path-rem", path.name)
    if PATH_CODE_ANCHOR in text and "path .folder{color:var(--accent-instrument)" not in text:
        text = once(
            text,
            PATH_CODE_ANCHOR,
            PATH_CODE_ANCHOR + "\n" + PATH_CODE_CSS,
            "path-code-visible",
            path.name,
        )

    if MARK not in text:
        text = text.replace(
            "function scheduleEqualizeCardRows(){",
            "/* " + MARK + ": re-equalize row after expand/collapse */\nfunction scheduleEqualizeCardRows(){",
            1,
        )
    safe_write(path, text)


def main() -> None:
    for p in FILES:
        patch_html(p)
    print("OK", MARK)


if __name__ == "__main__":
    main()
