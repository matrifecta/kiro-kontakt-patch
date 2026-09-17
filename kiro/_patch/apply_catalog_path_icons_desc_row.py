#!/usr/bin/env python3
"""Path icon glyphs (data-URI), hide collapsed path text, desc row align by tallest cover."""
from __future__ import annotations

import base64
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path("/home/phnx/kiro-kontakt-patch")
ICON_DIR = ROOT / "public/catalogs/icons"
FILES = [
    ROOT / "public/catalogs/KONTAKT-CATALOG.html",
    ROOT / "public/catalogs/DS-CATALOG.html",
    ROOT / "public/catalogs/KONTAKT-CATALOG-portable.html",
    ROOT / "public/catalogs/DS-CATALOG-portable.html",
]

MARK = "fix-PATH-ICONS-DESC-ROW-v1"
MARK2 = "fix-PATH-ICONS-DESC-ROW-v2"
MARK3 = "fix-PATH-ICONS-DESC-ROW-v3"
OLD_MASK_BLOCK = """.path-icon-btn.path-fs-hit{--path-icon-mask:url('icons/path-fullscreen.png')}
.path-icon-btn.path-copy-hit{--path-icon-mask:url('icons/path-copy.png')}
a.path-icon-btn.folder{--path-icon-mask:url('icons/path-folder.png')}"""

CSS_TAIL_ANCHOR = ".entry.selected:not(.highlight) .path:not(.is-expanded),"
CSS_ADD = rf"""/* {MARK}: data-URI glyphs; hide grid path text; cover-row desc band */
.path-icon-btn::before{{display:none!important}}
.path-icon-btn .path-icon-glyph{{
  display:block!important;width:64%!important;height:64%!important;object-fit:contain!important;
  pointer-events:none!important;opacity:.82!important;
  filter:brightness(0) saturate(100%) invert(58%) sepia(8%) saturate(420%) hue-rotate(169deg) brightness(95%) contrast(88%)!important
}}
.path-icon-btn:hover .path-icon-glyph,.path-icon-btn:focus-visible .path-icon-glyph{{
  opacity:1!important;
  filter:brightness(0) saturate(100%) invert(72%) sepia(68%) saturate(1200%) hue-rotate(359deg) brightness(101%) contrast(101%)!important
}}
.entry .path:not(.is-expanded) code{{
  position:absolute!important;width:1px!important;height:1px!important;padding:0!important;margin:-1px!important;
  overflow:hidden!important;clip:rect(0,0,0,0)!important;white-space:nowrap!important;border:0!important;
  opacity:0!important;pointer-events:none!important;display:block!important
}}
.entry .path.is-expanded code{{
  position:static!important;width:auto!important;height:auto!important;margin:0!important;
  clip:auto!important;opacity:1!important;pointer-events:auto!important
}}

"""

RESET_OLD = """      if(e.classList.contains('highlight'))return;
      e.style.minHeight='';
    });"""

RESET_V1 = """      if(e.classList.contains('highlight'))return;
      e.style.minHeight='';
      var _cov=e.querySelector('.cover');
      if(_cov)_cov.style.minHeight='';
    });"""

RESET_NEW = """      if(e.classList.contains('highlight'))return;
      e.style.minHeight='';
      var _cov=e.querySelector('.cover');
      if(_cov)_cov.style.minHeight='';
      var _sp=e.querySelector('.summary-panel');
      if(_sp)_sp.style.marginTop='';
    });"""

ROW_LOG_OLD = """      if(!rowLog)rowLog={n:row.cards.length,colMh:colMh,hs:row.cards.map(function(e){return Math.round(e.getBoundingClientRect().height);}),open:row.cards.map(function(e){return !!e.querySelector('details.patches[open]');}),paths:row.cards.map(function(e){var p=e.querySelector('.path');return !!(p&&p.classList.contains('is-expanded'));})};
    });"""

ROW_LOG_V1 = """      var _bandCards=row.cards.filter(function(e){
        return !(typeof catalogCardIsExpanded==='function'&&catalogCardIsExpanded(e));
      });
      if(!_bandCards.length)_bandCards=row.cards;
      var _maxCovH=0;
      _bandCards.forEach(function(e){
        var _c=e.querySelector('.cover');
        if(_c)_maxCovH=Math.max(_maxCovH,Math.round(_c.getBoundingClientRect().height));
      });
      if(_maxCovH>0){
        row.cards.forEach(function(e){
          var _c=e.querySelector('.cover');
          if(!_c)return;
          if(typeof catalogCardIsExpanded==='function'&&catalogCardIsExpanded(e)){
            _c.style.minHeight='';
            return;
          }
          _c.style.minHeight=_maxCovH+'px';
        });
      }else{
        row.cards.forEach(function(e){
          var _c=e.querySelector('.cover');
          if(_c)_c.style.minHeight='';
        });
      }
      if(!rowLog)rowLog={n:row.cards.length,colMh:colMh,covH:_maxCovH,hs:row.cards.map(function(e){return Math.round(e.getBoundingClientRect().height);}),open:row.cards.map(function(e){return !!e.querySelector('details.patches[open]');}),paths:row.cards.map(function(e){var p=e.querySelector('.path');return !!(p&&p.classList.contains('is-expanded'));})};
    });"""

ROW_LOG_V2 = """      var _bandCards=row.cards.filter(function(e){
        return !(typeof catalogCardIsExpanded==='function'&&catalogCardIsExpanded(e));
      });
      if(!_bandCards.length)_bandCards=row.cards;
      var _maxCovH=0,_refCard=null;
      _bandCards.forEach(function(e){
        var _c=e.querySelector('.cover');
        if(!_c)return;
        var _h=Math.round(_c.getBoundingClientRect().height);
        var _img=_c.querySelector('img');
        if(_img&&_img.getBoundingClientRect().height>0){
          _h=Math.max(_h,Math.round(_img.getBoundingClientRect().height));
        }
        if(_h>_maxCovH){_maxCovH=_h;_refCard=e;}
      });
      row.cards.forEach(function(e){
        var _c=e.querySelector('.cover');
        var _sp=e.querySelector('.summary-panel');
        var _exp=typeof catalogCardIsExpanded==='function'&&catalogCardIsExpanded(e);
        if(_exp){
          if(_c)_c.style.minHeight='';
          if(_sp)_sp.style.marginTop='';
          return;
        }
        if(_c&&_maxCovH>0)_c.style.minHeight=_maxCovH+'px';
        else if(_c)_c.style.minHeight='';
        if(_sp)_sp.style.marginTop='';
      });
      if(_maxCovH>0&&_refCard){
        void document.body.offsetHeight;
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
      }
      if(!rowLog)rowLog={n:row.cards.length,colMh:colMh,covH:_maxCovH,hs:row.cards.map(function(e){return Math.round(e.getBoundingClientRect().height);}),open:row.cards.map(function(e){return !!e.querySelector('details.patches[open]');}),paths:row.cards.map(function(e){var p=e.querySelector('.path');return !!(p&&p.classList.contains('is-expanded'));})};
    });"""

ROW_LOG_NEW = """      var _bandCards=row.cards.filter(function(e){
        return !(typeof catalogCardIsExpanded==='function'&&catalogCardIsExpanded(e));
      });
      if(!_bandCards.length)_bandCards=row.cards;
      var _maxCovH=0,_refCard=null;
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
      }
      if(!rowLog)rowLog={n:row.cards.length,colMh:colMh,covH:_maxCovH,hs:row.cards.map(function(e){return Math.round(e.getBoundingClientRect().height);}),open:row.cards.map(function(e){return !!e.querySelector('details.patches[open]');}),paths:row.cards.map(function(e){var p=e.querySelector('.path');return !!(p&&p.classList.contains('is-expanded'));})};
    });"""

GLYPH_FN_OLD = "function bindCatalogPathHits(){\n  document.querySelectorAll('.entry .path').forEach(function(p){\n    var needsFolder=!p.querySelector('a.folder');"

GLYPH_HELPER = r"""
function catalogPathIconSrc(kind){
  var m=window.CATALOG_PATH_ICON_SRC||{};
  return m[kind]||'';
}
function ensurePathIconGlyph(btn,kind){
  if(!btn)return;
  var src=catalogPathIconSrc(kind);
  if(!src)return;
  var img=btn.querySelector('.path-icon-glyph');
  if(!img){
    img=document.createElement('img');
    img.className='path-icon-glyph';
    img.alt='';
    img.draggable=false;
    btn.appendChild(img);
  }
  if(img.getAttribute('src')!==src)img.setAttribute('src',src);
}
"""

GLYPH_BIND = """    ensurePathIconGlyph(fs,'fullscreen');
    ensurePathIconGlyph(cp,'copy');
    if(folder)ensurePathIconGlyph(folder,'folder');"""


def load_icon_data() -> dict[str, str]:
    out: dict[str, str] = {}
    for key, name in (
        ("fullscreen", "path-fullscreen.png"),
        ("copy", "path-copy.png"),
        ("folder", "path-folder.png"),
    ):
        p = ICON_DIR / name
        if not p.is_file():
            raise SystemExit(f"missing icon {p}")
        b64 = base64.b64encode(p.read_bytes()).decode("ascii")
        out[key] = f"data:image/png;base64,{b64}"
    return out


def icon_src_js(icons: dict[str, str]) -> str:
    parts = ", ".join(f"{k}:'{v}'" for k, v in icons.items())
    return f"/* {MARK}: embedded path icon data URIs */\nwindow.CATALOG_PATH_ICON_SRC={{{parts}}};\n"


def once(text: str, old: str, new: str, label: str, *, required: bool = True) -> str:
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
    print(f"  wrote {path.name} bytes {new_size} delta {new_size - old_size}")


def patch_bind_glyphs(text: str) -> str:
    if "ensurePathIconGlyph(" in text:
        print("  skip bind-glyphs")
        return text
    if GLYPH_FN_OLD not in text:
        raise SystemExit("MISSING bindCatalogPathHits anchor")
    text = text.replace(GLYPH_FN_OLD, GLYPH_HELPER + GLYPH_FN_OLD, 1)
    anchor = "    row.appendChild(fs);row.appendChild(cp);if(folder)row.appendChild(folder);"
    if anchor not in text:
        raise SystemExit("MISSING bind row append")
    n = text.count(anchor)
    text = text.replace(anchor, anchor + "\n" + GLYPH_BIND, n)
    print(f"  OK bind-glyphs x{n}")
    return text


def patch_html(path: Path, icons: dict[str, str]) -> None:
    text = path.read_text(encoding="utf-8")
    if not text.rstrip().endswith("</html>"):
        raise SystemExit(f"{path.name}: no </html>")
    print(f"==== {path.name}")

    if MARK3 in text:
        print("  skip (already v3)")
        return

    if MARK2 in text or ROW_LOG_V2.strip() in text:
        text = once(text, ROW_LOG_V2, ROW_LOG_NEW, "desc-band-margin-only-v3", required=False)
        if ROW_LOG_V2 not in text and ROW_LOG_V1 in text:
            text = once(text, ROW_LOG_V1, ROW_LOG_NEW, "desc-band-margin-only-v3", required=False)
        if RESET_V1 in text:
            text = once(text, RESET_V1, RESET_NEW, "reset-desc-margin-v3", required=False)
        elif RESET_OLD in text:
            text = once(text, RESET_OLD, RESET_NEW, "reset-desc-margin-v3", required=False)
        if MARK3 not in text:
            text = text.replace(
                f"/* {MARK2}: desc snap after tallest cover reflow */",
                f"/* {MARK3}: desc band via summary margin; covers stay centered */\n/* {MARK2}: desc snap after tallest cover reflow */",
                1,
            )
            if MARK3 not in text:
                text = text.replace(
                    f"/* {MARK}: data-URI glyphs",
                    f"/* {MARK3}: desc band via summary margin; covers stay centered */\n/* {MARK}: data-URI glyphs",
                    1,
                )
        safe_write(path, text)
        return

    if f"/* {MARK}:" in text:
        text = once(text, ROW_LOG_V1, ROW_LOG_NEW, "cover-desc-band-v2", required=False)
        if RESET_V1 in text:
            text = once(text, RESET_V1, RESET_NEW, "reset-desc-margin-v2", required=False)
        elif RESET_OLD in text:
            text = once(text, RESET_OLD, RESET_NEW, "reset-desc-margin-v2", required=False)
        if MARK3 not in text:
            text = text.replace(
                f"/* {MARK}: data-URI glyphs",
                f"/* {MARK3}: desc band via summary margin; covers stay centered */\n/* {MARK}: data-URI glyphs",
                1,
            )
        safe_write(path, text)
        return

    if OLD_MASK_BLOCK not in text:
        raise SystemExit(f"{path.name}: missing old mask block")
    text = text.replace(
        OLD_MASK_BLOCK,
        f"/* {MARK}: mask URLs replaced by embedded img glyphs */\n.path-icon-btn.path-fs-hit{{}}\n.path-icon-btn.path-copy-hit{{}}\na.path-icon-btn.folder{{}}",
        1,
    )
    print("  OK replace-mask-urls")

    if CSS_TAIL_ANCHOR not in text:
        raise SystemExit(f"{path.name}: no CSS tail anchor")
    text = text.replace(CSS_TAIL_ANCHOR, CSS_ADD + CSS_TAIL_ANCHOR, 1)
    print(f"  OK css-{MARK}")

    js_block = icon_src_js(icons)
    anchor = "window.bindCatalogPathHits=bindCatalogPathHits;"
    if anchor not in text:
        raise SystemExit(f"{path.name}: no JS anchor")
    if "window.CATALOG_PATH_ICON_SRC" not in text:
        text = text.replace(anchor, js_block + anchor, 1)
        print("  OK icon-src-js")

    text = patch_bind_glyphs(text)
    if RESET_V1 in text:
        text = once(text, RESET_V1, RESET_NEW, "reset-cover-minh")
    else:
        text = once(text, RESET_OLD, RESET_NEW, "reset-cover-minh")
    text = once(text, ROW_LOG_OLD, ROW_LOG_NEW, "cover-desc-band")
    if MARK3 not in text:
        text = text.replace(
            f"/* {MARK}: data-URI glyphs",
            f"/* {MARK3}: desc band via summary margin; covers stay centered */\n/* {MARK}: data-URI glyphs",
            1,
        )

    if f"/* {MARK}:" not in text or "CATALOG_PATH_ICON_SRC" not in text:
        raise SystemExit(f"VERIFY FAIL {path.name}")
    safe_write(path, text)


def main() -> None:
    icons = load_icon_data()
    for p in FILES:
        if not p.is_file():
            raise SystemExit(f"missing {p}")
        patch_html(p, icons)
    print("MARK", MARK3)
    if "--no-verify" not in sys.argv:
        verify = ROOT / "kiro/_patch/verify_catalog_path_icons_desc_row.py"
        if verify.is_file():
            proc = subprocess.run([sys.executable, str(verify)], cwd=str(ROOT))
            if proc.returncode != 0:
                raise SystemExit(f"verify failed exit {proc.returncode}")
    print("OK", MARK3)


if __name__ == "__main__":
    main()
