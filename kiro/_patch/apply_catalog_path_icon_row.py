#!/usr/bin/env python3
"""Replace path action text with centered themed icon row (FS | copy | folder)."""
from __future__ import annotations

import json
import os
import subprocess
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

MARK = "fix-PATH-ICON-ROW-v1"
MARK_TAIL = "fix-PATH-ICON-ROW-v1-tail"
CSS_ANCHOR = "/* fix-CARD-ROW-RECT:"
CSS_ADD = rf"""/* {MARK}: path icon row — FS | copy | folder; themed masks */
.entry .path b{{display:none!important}}
.entry .path .path-action-row{{
  display:flex!important;flex:0 0 auto!important;width:100%!important;
  justify-content:center!important;align-items:center!important;
  gap:clamp(.35rem,2.5vw,.65rem)!important;margin:0!important;padding:0!important;
  pointer-events:auto!important
}}
.path-icon-btn{{
  --path-icon-size:calc(var(--card-chrome-btn) * .88);
  box-sizing:border-box;flex:0 0 auto!important;position:relative!important;
  width:var(--path-icon-size)!important;height:var(--path-icon-size)!important;
  min-width:var(--path-icon-size)!important;min-height:var(--path-icon-size)!important;
  padding:0!important;margin:0!important;display:inline-flex!important;
  align-items:center!important;justify-content:center!important;
  background:var(--bg-surface)!important;color:var(--text-muted)!important;
  border:1px solid var(--border)!important;border-radius:8px!important;
  cursor:pointer!important;touch-action:manipulation!important;
  text-decoration:none!important;font-size:0!important;line-height:0!important;
  overflow:hidden!important;white-space:nowrap!important
}}
.path-icon-btn:hover,.path-icon-btn:focus-visible{{
  color:var(--accent-instrument)!important;border-color:var(--accent-instrument)!important
}}
.path-icon-btn::before{{
  content:''!important;position:absolute!important;inset:18%!important;
  background-color:currentColor!important;
  -webkit-mask:var(--path-icon-mask) center/contain no-repeat!important;
  mask:var(--path-icon-mask) center/contain no-repeat!important
}}
.path-icon-btn.path-fs-hit{{--path-icon-mask:url('icons/path-fullscreen.png')}}
.path-icon-btn.path-copy-hit{{--path-icon-mask:url('icons/path-copy.png')}}
a.path-icon-btn.folder{{--path-icon-mask:url('icons/path-folder.png')}}
.entry .path:not(.is-expanded){{
  flex-direction:column!important;align-items:stretch!important;
  gap:.28rem!important;min-height:0!important;height:auto!important;max-height:none!important;
  overflow:hidden!important
}}
.entry .path:not(.is-expanded) code{{
  flex:0 0 auto!important;width:100%!important;max-width:100%!important;
  min-width:0!important;margin:0!important
}}
.entry .path:not(.is-expanded) .path-fs-hit,
.entry .path:not(.is-expanded) .path-copy-hit,
.entry .path:not(.is-expanded) .folder{{display:inline-flex!important}}
.entry .path.is-expanded{{
  gap:.32rem!important
}}
.entry .path.is-expanded .path-action-row{{
  margin-top:.05rem!important
}}
.entry.selected:not(.highlight) .path:not(.is-expanded),
.entry.highlight .path:not(.is-expanded),
body.chosen-preview-open .entry.selected:not(.highlight) .path:not(.is-expanded){{
  min-height:0!important;height:auto!important;max-height:none!important
}}
.path-copy-toast{{
  position:fixed;z-index:10060;left:50%;bottom:max(1rem,env(safe-area-inset-bottom));
  transform:translateX(-50%);padding:.45rem .85rem;border-radius:8px;
  background:var(--bg-card);color:var(--text);border:1px solid var(--border);
  box-shadow:var(--hl-shadow);font-size:.875rem;pointer-events:none
}}
.path-focus-zoom input[type=range],.path-reader-zoom input[type=range]{{
  width:min(40vw,180px);accent-color:var(--accent-instrument)
}}

"""

CSS_TAIL_ANCHOR = """.entry.selected:not(.highlight) .path.is-expanded,
.entry.highlight .path.is-expanded,
body.chosen-preview-open .entry.selected:not(.highlight) .path.is-expanded{
  min-height:0!important;height:auto!important;max-height:none!important;
  overflow:visible!important
}"""

CSS_TAIL_ADD = rf"""/* {MARK_TAIL}: column path + icon row wins over path-collapse row layout */
.entry .path:not(.is-expanded){{
  display:flex!important;flex-direction:column!important;flex-wrap:nowrap!important;
  align-items:stretch!important;gap:.28rem!important;
  min-height:0!important;height:auto!important;max-height:none!important;
  overflow:hidden!important
}}
.entry .path:not(.is-expanded) code{{
  flex:0 0 auto!important;width:100%!important;min-width:0!important;max-width:100%!important;
  display:block!important;margin:0!important
}}
.entry .path:not(.is-expanded) > .path-fs-hit,
.entry .path:not(.is-expanded) > .path-copy-hit,
.entry .path:not(.is-expanded) > .folder{{display:none!important}}
.entry .path:not(.is-expanded) .path-action-row .path-icon-btn{{
  display:inline-flex!important
}}
.entry .path .path-fs-hit:not(.path-icon-btn),
.entry .path .folder:not(.path-icon-btn){{
  font-size:0!important;padding:0!important;min-height:0!important;border:0!important
}}
.entry.selected:not(.highlight) .path:not(.is-expanded),
.entry.highlight .path:not(.is-expanded),
body.chosen-preview-open .entry.selected:not(.highlight) .path:not(.is-expanded){{
  min-height:0!important;height:auto!important;max-height:none!important
}}

"""

BIND_OLD = """function bindCatalogPathHits(){
  document.querySelectorAll('.entry .path').forEach(function(p){
    if(p.dataset.pathBound==='1')return;
    p.dataset.pathBound='1';
    if(!p.classList.contains('is-expanded')){p.setAttribute('aria-expanded','false');}
    if(!p.querySelector('.path-fs-hit')){
      var hit=document.createElement('button');
      hit.type='button';hit.className='path-fs-hit';hit.textContent='';
      hit.setAttribute('aria-label','Open path fullscreen');
      p.appendChild(hit);
    }
  });
}"""

BIND_NEW = """function bindCatalogPathHits(){
  document.querySelectorAll('.entry .path').forEach(function(p){
    var needsFolder=!p.querySelector('a.folder');
    if(p.dataset.pathBound==='1'&&!needsFolder)return;
    p.dataset.pathBound='1';
    if(!p.classList.contains('is-expanded')){p.setAttribute('aria-expanded','false');}
    var b=p.querySelector('b');
    if(b)b.style.display='none';
    var row=p.querySelector('.path-action-row');
    if(!row){
      row=document.createElement('div');
      row.className='path-action-row';
      p.appendChild(row);
    }
    p.querySelectorAll(':scope > .path-fs-hit,:scope > .path-copy-hit,:scope > .folder').forEach(function(el){
      if(el.parentElement!==row)row.appendChild(el);
    });
    var fs=row.querySelector('.path-fs-hit');
    if(!fs){
      fs=document.createElement('button');
      fs.type='button';fs.className='path-icon-btn path-fs-hit';
      fs.setAttribute('aria-label','Open path fullscreen');
    }else{
      fs.classList.add('path-icon-btn');fs.textContent='';
      fs.setAttribute('aria-label','Open path fullscreen');
    }
    var cp=row.querySelector('.path-copy-hit');
    if(!cp){
      cp=document.createElement('button');
      cp.type='button';cp.className='path-icon-btn path-copy-hit';
      cp.setAttribute('aria-label','Copy path');
    }else{
      cp.classList.add('path-icon-btn');cp.textContent='';
      cp.setAttribute('aria-label','Copy path');
    }
    var folder=row.querySelector('a.folder')||p.querySelector('a.folder');
    if(!folder){
      var href=typeof catalogFolderHref==='function'?catalogFolderHref(catalogPathText(p)):'';
      if(href){
        folder=document.createElement('a');
        folder.className='path-icon-btn folder';folder.href=href;
        folder.setAttribute('aria-label','Open folder');
        folder.setAttribute('target','_blank');folder.setAttribute('rel','noopener');
      }
    }
    if(folder){
      folder.classList.add('path-icon-btn');folder.textContent='';
      folder.setAttribute('aria-label','Open folder');
      if(folder.parentElement!==row)row.appendChild(folder);
    }
    row.appendChild(fs);row.appendChild(cp);if(folder)row.appendChild(folder);
  });
}"""

BIND_MID_OLD = """    var fs=p.querySelector('.path-fs-hit');
    if(!fs){
      fs=document.createElement('button');
      fs.type='button';
      fs.className='path-icon-btn path-fs-hit';
      fs.setAttribute('aria-label','Open path fullscreen');
      row.appendChild(fs);
    }else{
      fs.classList.add('path-icon-btn');
      fs.textContent='';
      fs.setAttribute('aria-label','Open path fullscreen');
      if(fs.parentElement!==row)row.appendChild(fs);
    }
    var cp=p.querySelector('.path-copy-hit');
    if(!cp){
      cp=document.createElement('button');
      cp.type='button';
      cp.className='path-icon-btn path-copy-hit';
      cp.setAttribute('aria-label','Copy path');
      row.appendChild(cp);
    }else{
      cp.classList.add('path-icon-btn');
      cp.textContent='';
      if(cp.parentElement!==row)row.appendChild(cp);
    }
    var folder=p.querySelector('a.folder');
    if(folder){
      folder.classList.add('path-icon-btn');
      folder.textContent='';
      folder.setAttribute('aria-label','Open folder');
      if(folder.parentElement!==row)row.appendChild(folder);
    }
    row.appendChild(fs);
    row.appendChild(cp);
    if(folder)row.appendChild(folder);"""

BIND_MID_NEW = """    p.querySelectorAll(':scope > .path-fs-hit,:scope > .path-copy-hit,:scope > .folder').forEach(function(el){
      if(el.parentElement!==row)row.appendChild(el);
    });
    var fs=row.querySelector('.path-fs-hit');
    if(!fs){
      fs=document.createElement('button');
      fs.type='button';fs.className='path-icon-btn path-fs-hit';
      fs.setAttribute('aria-label','Open path fullscreen');
    }else{
      fs.classList.add('path-icon-btn');fs.textContent='';
      fs.setAttribute('aria-label','Open path fullscreen');
    }
    var cp=row.querySelector('.path-copy-hit');
    if(!cp){
      cp=document.createElement('button');
      cp.type='button';cp.className='path-icon-btn path-copy-hit';
      cp.setAttribute('aria-label','Copy path');
    }else{
      cp.classList.add('path-icon-btn');cp.textContent='';
      cp.setAttribute('aria-label','Copy path');
    }
    var folder=row.querySelector('a.folder')||p.querySelector('a.folder');
    if(!folder){
      var href=typeof catalogFolderHref==='function'?catalogFolderHref(catalogPathText(p)):'';
      if(href){
        folder=document.createElement('a');
        folder.className='path-icon-btn folder';folder.href=href;
        folder.setAttribute('aria-label','Open folder');
        folder.setAttribute('target','_blank');folder.setAttribute('rel','noopener');
      }
    }
    if(folder){
      folder.classList.add('path-icon-btn');folder.textContent='';
      folder.setAttribute('aria-label','Open folder');
      if(folder.parentElement!==row)row.appendChild(folder);
    }
    row.appendChild(fs);row.appendChild(cp);if(folder)row.appendChild(folder);"""

BIND_GUARD_OLD = """    if(p.dataset.pathBound==='1')return;
    p.dataset.pathBound='1';"""

BIND_GUARD_NEW = """    var needsFolder=!p.querySelector('a.folder');
    if(p.dataset.pathBound==='1'&&!needsFolder)return;
    p.dataset.pathBound='1';"""

FOLDER_FN = r"""
function catalogFolderHref(pathTxt){
  if(!pathTxt)return '';
  var p=pathTxt.trim();
  if(/\.dsbundle$/i.test(p))return 'file://'+encodeURI(p).replace(/#/g,'%23');
  var markers=['/DS Libraries/','/Kontakt Libraries/','/Sample Libraries/'];
  for(var i=0;i<markers.length;i++){
    var ix=p.indexOf(markers[i]);
    if(ix>=0){
      var rest=p.slice(ix+markers[i].length);
      var slash=rest.indexOf('/');
      var lib=slash>=0?rest.slice(0,slash):rest;
      var dir=p.slice(0,ix+markers[i].length+lib.length);
      return 'file://'+encodeURI(dir).replace(/#/g,'%23');
    }
  }
  var slash=Math.max(p.lastIndexOf('/'),p.lastIndexOf('\\'));
  var dir=slash>=0?p.slice(0,slash):p;
  return 'file://'+encodeURI(dir).replace(/#/g,'%23');
}
"""

COPY_JS = r"""
function catalogPathText(pathBox){
  if(!pathBox)return '';
  var code=pathBox.querySelector('code');
  return ((code&&code.textContent)||'').trim();
}
function catalogFolderHref(pathTxt){
  if(!pathTxt)return '';
  var p=pathTxt.trim();
  if(/\.dsbundle$/i.test(p))return 'file://'+encodeURI(p).replace(/#/g,'%23');
  var markers=['/DS Libraries/','/Kontakt Libraries/','/Sample Libraries/'];
  for(var i=0;i<markers.length;i++){
    var ix=p.indexOf(markers[i]);
    if(ix>=0){
      var rest=p.slice(ix+markers[i].length);
      var slash=rest.indexOf('/');
      var lib=slash>=0?rest.slice(0,slash):rest;
      var dir=p.slice(0,ix+markers[i].length+lib.length);
      return 'file://'+encodeURI(dir).replace(/#/g,'%23');
    }
  }
  var slash=Math.max(p.lastIndexOf('/'),p.lastIndexOf('\\'));
  var dir=slash>=0?p.slice(0,slash):p;
  return 'file://'+encodeURI(dir).replace(/#/g,'%23');
}
function flashPathCopy(msg){
  var el=document.getElementById('pathCopyToast');
  if(!el){
    el=document.createElement('div');
    el.id='pathCopyToast';
    el.className='path-copy-toast';
    el.setAttribute('role','status');
    el.setAttribute('aria-live','polite');
    document.body.appendChild(el);
  }
  el.textContent=msg||'Path copied';
  el.hidden=false;
  clearTimeout(flashPathCopy._t);
  flashPathCopy._t=setTimeout(function(){el.hidden=true;},1600);
}
function catalogCopyPath(pathBox){
  var txt=catalogPathText(pathBox);
  if(!txt){flashPathCopy('No path');return false;}
  function ok(){flashPathCopy('Path copied');return true;}
  function legacy(){
    try{
      var ta=document.createElement('textarea');
      ta.value=txt;ta.setAttribute('readonly','');
      ta.style.position='fixed';ta.style.left='-9999px';
      document.body.appendChild(ta);ta.select();ta.setSelectionRange(0,txt.length);
      var done=document.execCommand('copy');
      document.body.removeChild(ta);
      if(done){ok();return true;}
    }catch(eLegacy){}
    flashPathCopy('Copy failed');
    return false;
  }
  if(navigator.clipboard&&navigator.clipboard.writeText){
    return navigator.clipboard.writeText(txt).then(ok).catch(legacy);
  }
  return legacy();
}
"""

PATH_CLICK_OLD = """    if(e.target.closest('.path')){
      var pathBox=e.target.closest('.path');
      if(e.target.closest('.folder'))return;
      if(e.target.closest('.path-fs-hit')){activatePath(entry);return;}"""

PATH_CLICK_NEW = """    if(e.target.closest('.path')){
      var pathBox=e.target.closest('.path');
      if(e.target.closest('.folder'))return;
      if(e.target.closest('.path-copy-hit')){
        catalogCopyPath(pathBox);
        e.preventDefault();e.stopPropagation();return;
      }
      if(e.target.closest('.path-action-row')&&!e.target.closest('.path-fs-hit,.path-copy-hit,.folder')){
        e.preventDefault();e.stopPropagation();return;
      }
      if(e.target.closest('.path-fs-hit')){activatePath(entry);return;}"""

PATH_FOCUS_ZOOM_OLD = """  <div class="path-focus-zoom" onclick="event.stopPropagation()">
    <button type="button" class="path-focus-zoom-btn" aria-label="Smaller text" onclick="nudgePathFocusSize(-2)">−</button>
    <button type="button" class="path-focus-zoom-btn" aria-label="Larger text" onclick="nudgePathFocusSize(2)">+</button>
  </div>"""

PATH_FOCUS_ZOOM_NEW = """  <div class="path-focus-zoom" onclick="event.stopPropagation()">
    <button type="button" class="path-focus-zoom-btn" aria-label="Smaller text" onclick="nudgePathFocusSize(-2)">−</button>
    <input id="pathFocusScale" type="range" min="14" max="32" step="1" value="18" aria-label="Path text size">
    <button type="button" class="path-focus-zoom-btn" aria-label="Larger text" onclick="nudgePathFocusSize(2)">+</button>
  </div>"""

PATH_READER_ZOOM_OLD = """  <div class="path-reader-zoom" onclick="event.stopPropagation()">
    <button type="button" class="path-reader-zoom-btn" aria-label="Smaller text" onclick="nudgePathFocusSize(-2)">−</button>
    <button type="button" class="path-reader-zoom-btn" aria-label="Larger text" onclick="nudgePathFocusSize(2)">+</button>
  </div>"""

PATH_READER_ZOOM_NEW = """  <div class="path-reader-zoom" onclick="event.stopPropagation()">
    <button type="button" class="path-reader-zoom-btn" aria-label="Smaller text" onclick="nudgePathFocusSize(-2)">−</button>
    <input id="pathReaderScale" type="range" min="14" max="32" step="1" value="18" aria-label="Path text size">
    <button type="button" class="path-reader-zoom-btn" aria-label="Larger text" onclick="nudgePathFocusSize(2)">+</button>
  </div>"""

SET_PATH_OLD = """function setPathFocusSize(px){
  pathFocusPx=Math.min(32,Math.max(14,px));
  var t=focusedPathText();
  if(t)t.style.fontSize=pathFocusPx+'px';
}"""

SET_PATH_NEW = """function setPathFocusSize(px){
  pathFocusPx=Math.min(32,Math.max(14,px));
  var t=focusedPathText();
  if(t)t.style.fontSize=pathFocusPx+'px';
  ['pathFocusScale','pathReaderScale'].forEach(function(id){
    var sl=document.getElementById(id);
    if(sl)sl.value=String(pathFocusPx);
  });
}"""

RANGE_OLD = """  if(e.target&&(e.target.id==='imgFocusScale'||e.target.id==='imgGalleryScale'))setImgFocusScale(parseFloat(e.target.value)||1);"""

RANGE_NEW = """  if(e.target&&(e.target.id==='imgFocusScale'||e.target.id==='imgGalleryScale'))setImgFocusScale(parseFloat(e.target.value)||1);
  if(e.target&&(e.target.id==='pathFocusScale'||e.target.id==='pathReaderScale'))setPathFocusSize(parseFloat(e.target.value)||18);"""

JS_ANCHOR = "window.bindCatalogPathHits=bindCatalogPathHits;"


def once(text: str, old: str, new: str, label: str, *, required: bool = True, replace_all: bool = False) -> str:
    if old not in text:
        if new in text or (not required and MARK in text):
            print(f"  skip {label}")
            return text
        if required:
            raise SystemExit(f"MISSING [{label}]")
        print(f"  skip {label} (optional)")
        return text
    n = text.count(old)
    if not replace_all and n != 1:
        if replace_all or n == 0:
            pass
        else:
            raise SystemExit(f"COUNT [{label}]: {n}")
    if replace_all:
        print(f"  OK {label} x{n}")
        return text.replace(old, new)
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

    if f"/* {MARK_TAIL}:" not in text:
        if CSS_TAIL_ANCHOR not in text:
            raise SystemExit(f"{path.name}: no CSS tail anchor")
        text = text.replace(CSS_TAIL_ANCHOR, CSS_TAIL_ANCHOR + "\n" + CSS_TAIL_ADD, 1)
        print(f"  OK css-{MARK_TAIL}")

    text = once(text, BIND_OLD, BIND_NEW, "bind-path-icons", replace_all=True, required=False)
    text = once(text, BIND_MID_OLD, BIND_MID_NEW, "bind-mid", replace_all=True, required=False)
    text = once(text, BIND_GUARD_OLD, BIND_GUARD_NEW, "bind-guard", replace_all=True, required=False)
    if "path-action-row" not in text and BIND_OLD not in text:
        raise SystemExit(f"{path.name}: bindCatalogPathHits not updated")
    text = once(text, PATH_CLICK_OLD, PATH_CLICK_NEW, "path-click-copy", required=False)
    text = once(text, PATH_FOCUS_ZOOM_OLD, PATH_FOCUS_ZOOM_NEW, "path-focus-scale", required=False)
    text = once(text, PATH_READER_ZOOM_OLD, PATH_READER_ZOOM_NEW, "path-reader-scale", required=False)
    text = once(text, SET_PATH_OLD, SET_PATH_NEW, "set-path-focus-size", required=False)
    if "pathFocusScale'||e.target.id==='pathReaderScale'" not in text:
        text = once(text, RANGE_OLD, RANGE_NEW, "range-input-handler", required=False)
    else:
        print("  skip range-input-handler")

    if "function catalogCopyPath(" not in text:
        anchor = JS_ANCHOR
        if anchor not in text:
            raise SystemExit(f"{path.name}: no JS anchor")
        text = text.replace(anchor, anchor + COPY_JS, 1)
        print("  OK copy-path-js")
    elif "function catalogFolderHref(" not in text:
        text = text.replace(
            "function catalogCopyPath(pathBox){",
            FOLDER_FN + "function catalogCopyPath(pathBox){",
            1,
        )
        print("  OK folder-href-js")

    dup_range = (
        "  if(e.target&&(e.target.id==='pathFocusScale'||e.target.id==='pathReaderScale'))"
        "setPathFocusSize(parseFloat(e.target.value)||18);\n"
        "  if(e.target&&(e.target.id==='pathFocusScale'||e.target.id==='pathReaderScale'))"
        "setPathFocusSize(parseFloat(e.target.value)||18);"
    )
    one_range = (
        "  if(e.target&&(e.target.id==='pathFocusScale'||e.target.id==='pathReaderScale'))"
        "setPathFocusSize(parseFloat(e.target.value)||18);"
    )
    if dup_range in text:
        text = text.replace(dup_range, one_range, 1)
        print("  OK dedup-range-handler")

    if f"/* {MARK}:" not in text or "catalogCopyPath" not in text:
        raise SystemExit(f"VERIFY FAIL {path.name}")
    safe_write(path, text)


def measure_via_verify() -> dict | None:
    verify = ROOT / "kiro/_patch/verify_catalog_path_icon_row.py"
    if not verify.is_file():
        return None
    try:
        proc = subprocess.run(
            [sys.executable, str(verify)],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            timeout=180,
        )
        out = (proc.stdout or "") + (proc.stderr or "")
        if proc.returncode != 0:
            print(out)
            return {"error": out.strip() or f"exit {proc.returncode}"}
        out_json = ROOT / "kiro/_patch/verify_catalog_path_icon_row.json"
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
