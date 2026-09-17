#!/usr/bin/env python3
"""Landscape Sides: nested KW arrow points up; full-side keeps down/collapse."""
from __future__ import annotations

import os
import tempfile
from pathlib import Path

ROOT = Path("/home/phnx/kiro-kontakt-patch")
PUB = ROOT / "public/catalogs"
JS_FILES = [
    PUB / "KONTAKT-CATALOG.html",
    PUB / "DS-CATALOG.html",
]
HELP_FILES = JS_FILES + [
    PUB / "KONTAKT-CATALOG-portable.html",
    PUB / "DS-CATALOG-portable.html",
]
MARK = "fix-SIDES-KW-NEST-ARROW"
KEEP = (
    "c00e3e",
    "fix-SIDES-KW-NEST-v1",
    "fix-SIDES-KW-NEST-v2",
    "fix-SIDES-KW-NEST-HELP-v2",
    MARK,
)

CSS_OLD = (
    "/* fix-SIDES-KW-NEST-v2: collapse arrow toggles nest; header K opens KW as its own side */\n"
    "@media(min-width:900px){\n"
)
CSS_NEW = (
    "/* fix-SIDES-KW-NEST-v2: collapse arrow toggles nest; header K opens KW as its own side */\n"
    "/* " + MARK + ": nested ▲ (up/unnest), full-side ▼ (down/nest); skip .open rotate */\n"
    "@media(min-width:900px){\n"
    "  body.desk-landscape.display-sides:not(.display-middle):not(.catalog-portable) #filterToggle .toggle-arrow{transform:none}\n"
)

SYNC_OLD = """function syncKwHideBtn(){
  var hidden=document.body.classList.contains('kw-chrome-collapsed');
  document.querySelectorAll('.kw-strip-hide').forEach(function(b){
    b.textContent=hidden?'Keywords':'Hide Keywords';
    b.setAttribute('aria-expanded',hidden?'false':'true');
    b.setAttribute('aria-label',hidden?'Keywords':'Hide Keywords');
  });
}
"""

SYNC_NEW = """function syncKwHideBtn(){
  var hidden=document.body.classList.contains('kw-chrome-collapsed');
  document.querySelectorAll('.kw-strip-hide').forEach(function(b){
    b.textContent=hidden?'Keywords':'Hide Keywords';
    b.setAttribute('aria-expanded',hidden?'false':'true');
    b.setAttribute('aria-label',hidden?'Keywords':'Hide Keywords');
  });
  var a=document.querySelector('#filterToggle .toggle-arrow');
  var ft=document.getElementById('filterToggle');
  var landSides=!!(!window.CATALOG_PORTABLE&&document.body.classList.contains('desk-landscape')&&document.body.classList.contains('display-sides')&&!document.body.classList.contains('display-middle')&&!document.body.classList.contains('catalog-portable'));
  var nested=landSides&&document.body.classList.contains('kw-nested-search')&&!hidden;
  if(a&&landSides){
    a.textContent=nested?'▲':'▼';
  }
  if(ft&&landSides){
    ft.setAttribute('aria-expanded',(!hidden&&!nested)?'true':'false');
    if(!hidden){
      ft.setAttribute('title',nested?'Return Keywords to full side':'Nest Keywords under Search');
      ft.setAttribute('aria-label',nested?'Return Keywords to full side':'Nest Keywords under Search');
    }
  }
  // #region agent log
  try{
    var tr=a?getComputedStyle(a).transform:'';
    fetch('http://127.0.0.1:7529/ingest/1cf46354-1d61-4c80-bd72-a340f1db1b51',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'c00e3e'},body:JSON.stringify({sessionId:'c00e3e',runId:'kw-arrow',hypothesisId:'ARR',location:'catalog:syncKwHideBtn',message:'kw-nest-arrow',data:{landSides:!!landSides,nested:!!nested,hidden:!!hidden,arrow:a?String(a.textContent||''):'',tr:tr,aria:ft?ft.getAttribute('aria-expanded'):null,title:ft?ft.getAttribute('title'):null,open:!!(document.getElementById('filterWrap')&&document.getElementById('filterWrap').classList.contains('open'))},timestamp:Date.now()})}).catch(function(){});
  }catch(eArrLog){}
  // #endregion
}
"""

SEARCH_SYNC_OLD = (
    "  if(typeof syncHdrMenuBtns==='function')syncHdrMenuBtns();\n"
    "}\n"
    "function toggleFilter(){\n"
)
SEARCH_SYNC_NEW = (
    "  if(typeof syncHdrMenuBtns==='function')syncHdrMenuBtns();\n"
    "  if(typeof syncKwHideBtn==='function')syncKwHideBtn();\n"
    "}\n"
    "function toggleFilter(){\n"
)

LOG_OLD = "fromArrow:!!extra.fromArrow,search:box(sc),kw:box(fw),main:box(cm),nh:(getComputedStyle(document.documentElement).getPropertyValue('--sides-nested-h')||'').trim()}"
LOG_NEW = "fromArrow:!!extra.fromArrow,search:box(sc),kw:box(fw),main:box(cm),nh:(getComputedStyle(document.documentElement).getPropertyValue('--sides-nested-h')||'').trim(),arrow:(document.querySelector('#filterToggle .toggle-arrow')||{}).textContent||'',arrowTr:(function(){var el=document.querySelector('#filterToggle .toggle-arrow');return el?getComputedStyle(el).transform:'';})(),aria:(function(){var el=document.getElementById('filterToggle');return el?el.getAttribute('aria-expanded'):null;})()}"

COLS_OLD = (
    "  }catch(eMidLand){}\n"
    "  // #endregion\n\n"
    "}\n"
    "function placeSidesHandles(){\n"
)
COLS_NEW = (
    "  }catch(eMidLand){}\n"
    "  // #endregion\n"
    "  if(typeof syncKwHideBtn==='function')syncKwHideBtn();\n\n"
    "}\n"
    "function placeSidesHandles(){\n"
)

HELP = [
    (
        "The Keywords collapse arrow then toggles nest under Search (Search top, KW bottom, same column) ↔ back to the 3-pane side; that arrow does not hide Keywords — header <b>K</b> (or Hide) turns Keywords off.",
        "The Keywords collapse arrow then toggles nest: <b>▼</b> (down, full side) nests under Search when Search is on; nested <b>▲</b> (up) returns to the full Sides column. That arrow does not hide Keywords — header <b>K</b> (or Hide) turns Keywords off.",
        "legend-kw",
    ),
    (
        "Landscape nest (collapse arrow) stacks Search above Keywords in one column, content the other.",
        "Landscape nest (<b>▼</b> on Keywords) stacks Search above Keywords in one column, content the other; nested <b>▲</b> returns to the full column.",
        "legend-sides",
    ),
    (
        "the Keywords collapse arrow nests under Search or restores the 3-pane side (it does not hide)",
        "the Keywords down/collapse arrow (<b>▼</b>) nests under Search; the nested up arrow (<b>▲</b>) restores the 3-pane side (it does not hide)",
        "guide-filter",
    ),
    (
        "Press the Keywords panel collapse arrow (the arrow on Keywords chrome — not header K). Search sits on top, Keywords on the bottom, same column; content is the other pane.",
        "Press the Keywords panel collapse arrow (<b>▼</b> while Keywords is a full side — not header K). Search sits on top, Keywords on the bottom, same column; content is the other pane.",
        "guide-nest-down",
    ),
    (
        "Press that same arrow again to return to 3-pane Sides. Header <b>K</b> (or Hide) turns Keywords off.",
        "Press the nested up arrow (<b>▲</b>) to return to 3-pane Sides. Header <b>K</b> (or Hide) turns Keywords off.",
        "guide-nest-up",
    ),
    (
        "Nested Flip moves Search+Keywords together. Nested Customize keeps a movable divider between Search and Keywords. Portable phone chrome is unchanged.",
        "Full-side Keywords shows a down/collapse arrow meaning nest under Search. Nested Keywords shows an up arrow meaning return to the full Sides column. Nested Flip moves Search+Keywords together. Nested Customize keeps a movable divider between Search and Keywords. Portable phone chrome is unchanged. Portrait desktop still one-step hide — no up-arrow nest-toggle there.",
        "guide-see",
    ),
    (
        "Sides Keywords collapse arrow toggles nest under Search ↔ 3-pane; header K hides Keywords.",
        "Sides Keywords <b>▼</b> nests under Search; nested <b>▲</b> restores the 3-pane; header K hides Keywords.",
        "guide-land",
    ),
]


def once(text: str, old: str, new: str, label: str, name: str) -> str:
    if old not in text:
        if new in text:
            print(f"  skip {label} {name}")
            return text
        raise SystemExit(f"{name}: missing {label}: {old[:160]!r}")
    n = text.count(old)
    if n != 1:
        raise SystemExit(f"{name}: {label} count {n}")
    print(f"  1x {label} {name}")
    return text.replace(old, new, 1)


def safe_write(path: Path, text: str) -> None:
    if not text.rstrip().endswith("</html>"):
        raise SystemExit(f"{path.name}: rewrite would drop </html>")
    raw = text.encode("utf-8")
    fd, tmp = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=str(path.parent))
    try:
        os.write(fd, raw)
        os.fsync(fd)
        os.close(fd)
        fd = -1
        tmp_path = Path(tmp)
        if not tmp_path.read_text(encoding="utf-8").rstrip().endswith("</html>"):
            tmp_path.unlink(missing_ok=True)
            raise SystemExit(f"{path.name}: tmp missing </html>")
        size = tmp_path.stat().st_size
        if size < 80_000:
            tmp_path.unlink(missing_ok=True)
            raise SystemExit(f"{path.name}: tmp too small {size}")
        os.replace(tmp, path)
        assert path.stat().st_size == size
        assert path.read_text(encoding="utf-8").rstrip().endswith("</html>")
        print(f"ok {path.name} bytes={size}")
    finally:
        if fd >= 0:
            try:
                os.close(fd)
            except OSError:
                pass
        if os.path.exists(tmp):
            os.unlink(tmp)


def patch_js(path: Path) -> None:
    name = path.name
    text = path.read_text(encoding="utf-8")
    c00 = text.count("sessionId:'c00e3e'")
    if MARK in text and "kw-nest-arrow" in text:
        print("skip-js", name)
        return
    text = once(text, CSS_OLD, CSS_NEW, "css", name)
    text = once(text, SYNC_OLD, SYNC_NEW, "syncKwHideBtn", name)
    text = once(text, SEARCH_SYNC_OLD, SEARCH_SYNC_NEW, "search-sync", name)
    text = once(text, LOG_OLD, LOG_NEW, "logKwNest", name)
    text = once(text, COLS_OLD, COLS_NEW, "applySidesCols", name)
    if MARK not in text:
        raise SystemExit(f"{name}: missing {MARK}")
    after = text.count("sessionId:'c00e3e'")
    if after < c00:
        raise SystemExit(f"{name}: lost c00e3e logs {c00}->{after}")
    for keep in ("c00e3e", "fix-SIDES-KW-NEST-v1", "fix-SIDES-KW-NEST-v2", MARK):
        if keep not in text:
            raise SystemExit(f"{name}: lost {keep}")
    if "a.textContent=nested?'▲':'▼'" not in text:
        raise SystemExit(f"{name}: missing nest arrow glyph")
    safe_write(path, text)


def patch_help(path: Path) -> None:
    name = path.name
    text = path.read_text(encoding="utf-8")
    c00 = text.count("sessionId:'c00e3e'")
    if "no up-arrow nest-toggle there" in text:
        print("skip-help", name)
        return
    for old, new, label in HELP:
        text = once(text, old, new, label, name)
    stamp = '<summary>Keywords nest under Search</summary>\n        <!-- ' + MARK + ' -->'
    needle = "<summary>Keywords nest under Search</summary>"
    if "<!-- " + MARK + " -->" not in text:
        if needle not in text:
            raise SystemExit(f"{name}: missing nest section")
        n = text.count(needle)
        if n != 1:
            raise SystemExit(f"{name}: nest summary count {n}")
        text = text.replace(needle, stamp, 1)
    after = text.count("sessionId:'c00e3e'")
    if after < c00:
        raise SystemExit(f"{name}: lost c00e3e logs {c00}->{after}")
    if "no up-arrow nest-toggle there" not in text:
        raise SystemExit(f"{name}: missing portrait caveat")
    if "nested <b>▲</b>" not in text:
        raise SystemExit(f"{name}: missing nested up-arrow copy")
    safe_write(path, text)


def main() -> None:
    for p in JS_FILES:
        if not p.exists():
            raise SystemExit(f"missing {p}")
        patch_js(p)
    for p in HELP_FILES:
        if not p.exists():
            raise SystemExit(f"missing {p}")
        patch_help(p)


if __name__ == "__main__":
    main()
