#!/usr/bin/env python3
"""Fixed 2-line .lib-name slot, ellipsis, hover/focus bubble; drop title-band minHeight JS."""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

ROOT = Path("/home/phnx/kiro-kontakt-patch")
FILES = [
    ROOT / "public/catalogs/KONTAKT-CATALOG.html",
    ROOT / "public/catalogs/DS-CATALOG.html",
    ROOT / "public/catalogs/KONTAKT-CATALOG-portable.html",
    ROOT / "public/catalogs/DS-CATALOG-portable.html",
]

MARK = "fix-LIB-NAME-TWO-LINE-v1"
CSS_ANCHOR = "/* fix-CARD-ROW-RECT:"
CSS_ADD = rf"""/* {MARK}: fixed 2-line title slot; ellipsis; themed hover bubble */
.entry:not(.highlight) .lib-name,
.entry:not(.highlight) h3.lib-name{{
  --lib-name-lines:2;--lib-name-lh:1.25;
  --lib-name-slot-h:calc(var(--lib-name-lh) * var(--lib-name-lines) * 1em);
  line-height:var(--lib-name-lh);
  display:-webkit-box;-webkit-box-orient:vertical;
  -webkit-line-clamp:var(--lib-name-lines);line-clamp:var(--lib-name-lines);
  overflow:hidden;min-height:var(--lib-name-slot-h);max-height:var(--lib-name-slot-h);height:var(--lib-name-slot-h);
  text-overflow:ellipsis;flex:0 0 auto
}}
.lib-name-tip{{
  display:none;position:fixed;z-index:920;max-width:min(90vw,420px);
  background:var(--bg-card);color:var(--text);border:1px solid var(--border);
  border-radius:8px;padding:8px 12px;box-shadow:var(--hl-shadow);
  font-size:clamp(.9375rem,1em,1.125rem);line-height:1.35;
  pointer-events:none;white-space:normal;overflow-wrap:anywhere;word-break:break-word
}}
.lib-name-tip.open{{display:block}}

"""

PORTABLE_CLAMP_OLD = """  body.catalog-portable .entry:not(.highlight) .lib-name,
  body.catalog-portable .entry:not(.highlight) h3{
    display:-webkit-box;-webkit-box-orient:vertical;-webkit-line-clamp:3;line-clamp:3;
    overflow:hidden
  }"""

PORTABLE_CLAMP_NEW = """  body.catalog-portable .entry:not(.highlight) .lib-name,
  body.catalog-portable .entry:not(.highlight) h3{
    -webkit-line-clamp:2;line-clamp:2
  }"""

RESET_OLD = """      e.style.minHeight='';
      var n=e.querySelector('.lib-name');
      if(n)n.style.minHeight='';
    });"""

RESET_NEW = """      e.style.minHeight='';
    });"""

TITLE_BAND_OLD = """      var hasExpanded=row.cards.some(function(e){
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
      if(!rowLog)"""

TITLE_BAND_NEW = """      if(!rowLog)"""

NAME_TIP_JS = r"""
/* fix-LIB-NAME-TWO-LINE-v1: full name bubble on hover/focus/touch-hold */
(function(){
  var tip=null,anchor=null,touchTimer=0;
  function ensureTip(){
    if(!tip){
      tip=document.createElement('div');
      tip.className='lib-name-tip';
      tip.setAttribute('role','tooltip');
      tip.hidden=true;
      document.body.appendChild(tip);
    }
    return tip;
  }
  function fullName(el){
    var entry=el.closest&&el.closest('.entry');
    return ((entry&&entry.getAttribute('data-name'))||el.textContent||'').trim();
  }
  function isTruncated(el){
    return el.scrollHeight>el.clientHeight+1||el.scrollWidth>el.clientWidth+1;
  }
  function placeTip(){
    if(!tip||!anchor||tip.hidden)return;
    var r=anchor.getBoundingClientRect();
    var tr=tip.getBoundingClientRect();
    var top=r.bottom+6;
    var left=Math.max(8,Math.min(r.left,window.innerWidth-tr.width-8));
    if(top+tr.height>window.innerHeight-8)top=Math.max(8,r.top-tr.height-6);
    tip.style.top=top+'px';
    tip.style.left=left+'px';
  }
  function showTip(el,force){
    var full=fullName(el);
    if(!full)return;
    if(!force&&!isTruncated(el))return;
    var t=ensureTip();
    t.textContent=full;
    t.hidden=false;
    t.classList.add('open');
    anchor=el;
    placeTip();
  }
  function hideTip(){
    if(tip){tip.hidden=true;tip.classList.remove('open');}
    anchor=null;
  }
  function bindName(el){
    if(el.dataset.nameTipBound==='1')return;
    el.dataset.nameTipBound='1';
    var full=fullName(el);
    if(full)el.setAttribute('title',full);
    el.addEventListener('mouseenter',function(){showTip(el,false);});
    el.addEventListener('mouseleave',hideTip);
    el.addEventListener('focus',function(){showTip(el,true);});
    el.addEventListener('blur',hideTip);
    el.addEventListener('pointerdown',function(e){
      if(e.pointerType!=='touch')return;
      clearTimeout(touchTimer);
      touchTimer=setTimeout(function(){showTip(el,true);},480);
    });
    el.addEventListener('pointerup',function(e){
      if(e.pointerType!=='touch')return;
      clearTimeout(touchTimer);
    });
    el.addEventListener('pointercancel',function(){clearTimeout(touchTimer);});
  }
  function bindAll(){
    document.querySelectorAll('.entry:not(.highlight) .lib-name').forEach(bindName);
  }
  window.bindLibNameTips=bindAll;
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',bindAll);
  else bindAll();
  window.addEventListener('scroll',hideTip,true);
  window.addEventListener('resize',placeTip);
})();
"""

BOOT_OLD = """if(typeof bindCatalogPathHits==='function')bindCatalogPathHits();
if(typeof scheduleEqualizeCardRows==='function')scheduleEqualizeCardRows();"""

BOOT_NEW = """if(typeof bindCatalogPathHits==='function')bindCatalogPathHits();
if(typeof bindLibNameTips==='function')bindLibNameTips();
if(typeof scheduleEqualizeCardRows==='function')scheduleEqualizeCardRows();"""

JS_ANCHOR = "window.bindCatalogPathHits=bindCatalogPathHits;"

SLOT_OLD = """  overflow:hidden;max-height:calc(var(--lib-name-lh) * var(--lib-name-lines) * 1em);
  text-overflow:ellipsis;flex:0 0 auto;min-height:0"""

SLOT_NEW = """  --lib-name-slot-h:calc(var(--lib-name-lh) * var(--lib-name-lines) * 1em);
  overflow:hidden;min-height:var(--lib-name-slot-h);max-height:var(--lib-name-slot-h);height:var(--lib-name-slot-h);
  text-overflow:ellipsis;flex:0 0 auto"""


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

    if f"/* {MARK}:" not in text:
        if CSS_ANCHOR not in text:
            raise SystemExit(f"{path.name}: no CSS anchor")
        text = text.replace(CSS_ANCHOR, CSS_ADD + CSS_ANCHOR, 1)
        print(f"  OK css-{MARK}")

    if path.name.endswith("-portable.html"):
        text = once(text, PORTABLE_CLAMP_OLD, PORTABLE_CLAMP_NEW, "portable-clamp-2", required=False)

    text = once(text, SLOT_OLD, SLOT_NEW, "lib-name-fixed-slot", required=False)
    if "--lib-name-slot-h:" not in text:
        raise SystemExit(f"{path.name}: lib-name slot height missing")

    text = once(text, RESET_OLD, RESET_NEW, "reset-no-name-minh", required=False)
    text = once(text, TITLE_BAND_OLD, TITLE_BAND_NEW, "title-band-drop", required=False)

    if "bindLibNameTips" not in text:
        if JS_ANCHOR not in text:
            raise SystemExit(f"{path.name}: no JS anchor")
        text = text.replace(JS_ANCHOR, JS_ANCHOR + NAME_TIP_JS, 1)
        print("  OK name-tip-js")

    text = once(text, BOOT_OLD, BOOT_NEW, "boot-bind-tips", required=False)

    if f"/* {MARK}:" not in text or "bindLibNameTips" not in text:
        raise SystemExit(f"VERIFY FAIL {path.name}")
    safe_write(path, text)


def measure_via_verify() -> dict | None:
    verify = ROOT / "kiro/_patch/verify_catalog_name_two_line.py"
    if not verify.is_file():
        return None
    try:
        proc = subprocess.run(
            [sys.executable, str(verify)],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            timeout=120,
        )
        out = (proc.stdout or "") + (proc.stderr or "")
        if proc.returncode != 0:
            print(out)
            return {"error": out.strip() or f"exit {proc.returncode}"}
        out_json = ROOT / "kiro/_patch/verify_catalog_name_two_line.json"
        if out_json.is_file():
            return json.loads(out_json.read_text(encoding="utf-8"))
    except Exception as exc:
        return {"error": str(exc)}
    return None


def main() -> None:
    for p in FILES:
        patch_html(p)
    print("MARK", MARK)
    if "--no-verify" not in sys.argv:
        measured = measure_via_verify()
        if measured is not None:
            print("MEASURED", json.dumps(measured, indent=2))
    print("OK", MARK)


if __name__ == "__main__":
    main()
