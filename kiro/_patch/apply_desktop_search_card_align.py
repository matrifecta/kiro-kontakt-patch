#!/usr/bin/env python3
"""Align desktop Search-strip buttons and card chrome across all tile variants.

Desktop catalogs only. Does not touch *-portable.html.
"""
from __future__ import annotations

import os
import tempfile
from pathlib import Path

ROOT = Path("/home/phnx/kiro-kontakt-patch")
FILES = [
    ROOT / "public/catalogs/DS-CATALOG.html",
    ROOT / "public/catalogs/KONTAKT-CATALOG.html",
]
MARK = "fix-DESKTOP-SEARCH-CARD-ALIGN-v1"

CSS_ANCHOR = """body.chosen-preview-open .entry.selected:not(.highlight) .card-actions{
  margin-top:1.05rem!important;padding-top:.7rem!important
}

/* fix-DOC-NOTE-DOCK: About/Document pinned to content-pane bottom; cards scroll above */"""

CSS_ADD = f"""body.chosen-preview-open .entry.selected:not(.highlight) .card-actions{{
  margin-top:1.05rem!important;padding-top:.7rem!important
}}

/* {MARK}: Search-strip + card chrome share a baseline (desktop only) */
body:not(.catalog-portable) #searchStrip{{
  align-items:center!important;flex-wrap:nowrap!important;min-height:2.75rem
}}
body:not(.catalog-portable) #searchStrip #searchInput{{
  box-sizing:border-box;align-self:center;min-height:2.75rem;height:2.75rem;
  padding:0 .35rem;line-height:2.75rem;display:block
}}
body:not(.catalog-portable) #searchStrip .search-strip-clear,
body:not(.catalog-portable) #searchStrip .search-strip-hide,
body:not(.catalog-portable) #searchStrip .search-strip-fs,
body:not(.catalog-portable) #searchStrip .search-strip-more,
body:not(.catalog-portable) #searchStrip .ac-history-wrap,
body:not(.catalog-portable) #searchStrip .ac-history-btn{{
  box-sizing:border-box;align-self:center;min-height:2.75rem;height:2.75rem;
  display:inline-flex;align-items:center;justify-content:center;line-height:1
}}
body:not(.catalog-portable) #searchStrip .ac-history-btn,
body:not(.catalog-portable) #searchStrip .search-strip-fs,
body:not(.catalog-portable) #searchStrip .search-strip-more{{
  width:2.75rem;min-width:2.75rem;padding:0
}}
body:not(.catalog-portable) .search-autocomplete .ac-item{{align-items:center}}
body:not(.catalog-portable) .search-autocomplete .ac-item.ac-lib{{align-items:center;height:auto}}
body:not(.catalog-portable) .search-autocomplete .ac-item .ac-count,
body:not(.catalog-portable) .search-autocomplete .ac-item.ac-lib .ac-lib-mark{{
  align-self:center;flex:0 0 auto;font-variant-numeric:tabular-nums;
  min-width:2.5em;text-align:right
}}
body:not(.catalog-portable) .entry:not(.highlight) .cover{{
  width:100%!important;max-width:100%!important;flex:0 0 auto;
  display:flex!important;align-items:center!important;justify-content:center!important;
  box-sizing:border-box
}}
body:not(.catalog-portable) .entry:not(.highlight) .cover img{{
  width:auto!important;height:auto!important;max-width:100%!important;
  object-fit:contain!important;object-position:center center!important
}}
body:not(.catalog-portable):not(.chosen-preview-open) .entry:not(.highlight):not(:has(details.patches[open])):not(:has(.path.is-expanded)) .path{{
  margin-top:auto!important
}}
body:not(.catalog-portable):not(.chosen-preview-open) .entry:not(.highlight) details.patches,
body:not(.catalog-portable):not(.chosen-preview-open) .entry:not(.highlight) .patches{{
  margin-top:0!important;margin-bottom:0!important;
  padding-top:var(--card-chrome-gap)!important;flex:0 0 auto
}}
body:not(.catalog-portable):not(.chosen-preview-open) .entry:not(.highlight) .patches>summary{{
  display:flex;align-items:center;box-sizing:border-box;
  min-height:2.25rem;padding:.35rem .25rem;margin:0
}}
body:not(.catalog-portable):not(.chosen-preview-open) .entry:not(.highlight) .card-actions{{
  margin-top:0!important;margin-bottom:0!important;
  padding-top:var(--card-chrome-gap)!important;padding-bottom:0!important;
  padding-right:calc(var(--card-chrome-btn) + var(--card-chrome-gap))!important;
  align-self:stretch;align-items:center;min-height:var(--card-chrome-btn);
  box-sizing:border-box
}}
body:not(.catalog-portable):not(.chosen-preview-open) .entry:not(.highlight) .search-popup-btn,
body:not(.catalog-portable):not(.chosen-preview-open) .entry:not(.highlight) .search-link{{
  box-sizing:border-box;min-height:var(--card-chrome-btn);height:var(--card-chrome-btn);
  margin-top:0!important;padding-top:0;padding-bottom:0;
  display:inline-flex;align-items:center;justify-content:center;line-height:1
}}
body:not(.catalog-portable):not(.chosen-preview-open) .entry:not(.highlight) .fav-btn{{
  right:.8rem;bottom:.8rem
}}

/* fix-DOC-NOTE-DOCK: About/Document pinned to content-pane bottom; cards scroll above */"""

JS_OLD = """      var _maxCovH=0,_refCard=null;
      _bandCards.forEach(function(e){
        var _c=e.querySelector('.cover');
        if(!_c)return;
        var _h=Math.round(_c.getBoundingClientRect().height);
        if(_h>_maxCovH){_maxCovH=_h;_refCard=e;}
      });
      row.cards.forEach(function(e){
        var _c=e.querySelector('.cover');
        var _sp=e.querySelector('.summary-panel');
        if(_c)_c.style.minHeight='';
        if(!_sp)return;
        if(typeof catalogCardIsExpanded==='function'&&catalogCardIsExpanded(e)){
          _sp.style.marginTop='';
          return;
        }
        _sp.style.marginTop='';
      });
      if(_refCard){
        var _tSp=_refCard.querySelector('.summary-panel');
        var _targetTop=_tSp?Math.round(_tSp.getBoundingClientRect().top):0;
        if(_targetTop>0){
          row.cards.forEach(function(e){
            if(typeof catalogCardIsExpanded==='function'&&catalogCardIsExpanded(e))return;
            var _sp=e.querySelector('.summary-panel');
            if(!_sp)return;
            var _d=_targetTop-Math.round(_sp.getBoundingClientRect().top);
            _sp.style.marginTop=(_d>0?_d:0)+'px';
          });
        }
      }"""

JS_NEW = """      var _maxCovH=0,_refCard=null;
      _bandCards.forEach(function(e){
        var _c=e.querySelector('.cover');
        if(!_c)return;
        var _h=Math.round(_c.getBoundingClientRect().height);
        var _img=_c.querySelector('img');
        if(_img){
          var _ih=Math.round(_img.getBoundingClientRect().height);
          if(_ih>_h)_h=_ih;
        }
        if(_h>_maxCovH){_maxCovH=_h;_refCard=e;}
      });
      var _desk=!(typeof window!=='undefined'&&window.CATALOG_PORTABLE);
      row.cards.forEach(function(e){
        var _c=e.querySelector('.cover');
        var _sp=e.querySelector('.summary-panel');
        var _exp=typeof catalogCardIsExpanded==='function'&&catalogCardIsExpanded(e);
        if(_c){
          if(_desk&&_maxCovH>0&&!_exp)_c.style.minHeight=_maxCovH+'px';
          else _c.style.minHeight='';
        }
        if(_sp)_sp.style.marginTop='';
      });
      if(_desk&&typeof document!=='undefined'&&document.body)void document.body.offsetHeight;
      if(_refCard){
        var _tSp=_refCard.querySelector('.summary-panel');
        var _targetTop=_tSp?Math.round(_tSp.getBoundingClientRect().top):0;
        if(_targetTop>0){
          row.cards.forEach(function(e){
            if(typeof catalogCardIsExpanded==='function'&&catalogCardIsExpanded(e))return;
            var _sp=e.querySelector('.summary-panel');
            if(!_sp)return;
            var _d=_targetTop-Math.round(_sp.getBoundingClientRect().top);
            _sp.style.marginTop=(_d>0?_d:0)+'px';
          });
        }
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
        text = patch_once(text, CSS_ANCHOR, CSS_ADD, "css")
        text = patch_once(text, JS_OLD, JS_NEW, "js-cover-band")
        safe_write(path, text)


if __name__ == "__main__":
    main()
