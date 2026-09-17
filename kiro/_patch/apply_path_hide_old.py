#!/usr/bin/env python3
"""Hide leftover in-card path text; tighten desc/path/patches gaps to --card-chrome-gap."""
from __future__ import annotations

import os
import tempfile
from pathlib import Path

ROOT = Path("/home/phnx/kiro-kontakt-patch/public/catalogs")
FILES = [
    ROOT / "KONTAKT-CATALOG.html",
    ROOT / "DS-CATALOG.html",
    ROOT / "KONTAKT-CATALOG-portable.html",
    ROOT / "DS-CATALOG-portable.html",
]
MARK = "fix-PATH-HIDE-OLD-v1"

TAIL_END = """body.chosen-preview-open .entry.selected:not(.highlight) .path:not(.is-expanded){
  min-height:0!important;height:auto!important;max-height:none!important
}


.entry details.patches,"""

TAIL_NEW = f"""body.chosen-preview-open .entry.selected:not(.highlight) .path:not(.is-expanded){{
  min-height:0!important;height:auto!important;max-height:none!important
}}
/* {MARK}: leftover path <code> is retired; PATH + 3 buttons only */
.entry .path code,
.entry .path > b,
.entry .path:not(.is-expanded) code,
.entry .path.is-expanded code,
.entry .path.is-expanded > b,
.entry.selected:not(.highlight) .path:not(.is-expanded) code,
.entry.highlight .path:not(.is-expanded) code,
body.chosen-preview-open .entry.selected:not(.highlight) .path code{{
  position:absolute!important;width:1px!important;height:1px!important;padding:0!important;margin:-1px!important;
  overflow:hidden!important;clip:rect(0,0,0,0)!important;white-space:nowrap!important;border:0!important;
  opacity:0!important;pointer-events:none!important;display:block!important;flex:0 0 0!important;
  max-width:1px!important;max-height:0!important;min-height:0!important;min-width:0!important;
  line-height:0!important;font-size:0!important;color:transparent!important
}}
body:not(.chosen-preview-open) .entry:not(.highlight) .summary-panel{{
  margin:var(--card-chrome-gap) 0!important
}}
.entry .path,
.entry .path:not(.is-expanded),
.entry .path.is-expanded,
body:not(.chosen-preview-open) .entry.selected:not(.highlight) .path,
body:not(.chosen-preview-open) .entry.selected:not(.highlight) .path:not(.is-expanded){{
  margin:0 0 var(--card-chrome-gap)!important;gap:0!important;
  min-height:0!important;height:auto!important;max-height:none!important
}}
.entry .path-label{{margin:0 0 .1rem!important}}


.entry details.patches,"""

SPACE_OLD = """.entry:not(.highlight) details.patches,
.entry:not(.highlight) .patches{
  margin-top:auto;padding-top:.55rem;margin-bottom:.32rem!important
}"""

SPACE_NEW = """.entry:not(.highlight) details.patches,
.entry:not(.highlight) .patches{
  margin-top:0!important;padding-top:var(--card-chrome-gap)!important;margin-bottom:var(--card-chrome-gap)!important
}"""

ACT_OLD = """.entry .card-actions,
.entry:not(.highlight) .card-actions{
  margin-top:.62rem!important;padding-top:.38rem
}"""

ACT_NEW = """.entry .card-actions,
.entry:not(.highlight) .card-actions{
  margin-top:0!important;padding-top:0!important
}"""

SEL_OLD = "#cardMinDock,.cover,.summary-panel,.path,.path-icon-btn,.folder,.path-fs-hit,.path-copy-hit,.path-action-row'"
SEL_NEW = "#cardMinDock,.cover,.summary-panel,.path-icon-btn,.folder,.path-fs-hit,.path-copy-hit,.path-action-row'"

BRACE_OLD = """      if(false&&!pathBox.classList.contains('is-expanded')){
        pathBox.classList.add('is-expanded');
        pathBox.classList.remove('is-collapsed');
        pathBox.setAttribute('aria-expanded','true');
        if(typeof scheduleEqualizeCardRows==='function')scheduleEqualizeCardRows();
        // #region agent log
        try{fetch('http://127.0.0.1:7529/ingest/1cf46354-1d61-4c80-bd72-a340f1db1b51',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'c00e3e'},body:JSON.stringify({sessionId:'c00e3e',runId:'path-card',hypothesisId:'A',location:'catalog:pathExpand',message:'path-expand-old',data:{portable:!!window.CATALOG_PORTABLE,tag:e.target&&e.target.tagName,cls:((e.target&&e.target.className)||'').toString().slice(0,80),hitCode:!!(e.target.closest&&e.target.closest('code')),hitB:!!(e.target.closest&&e.target.closest('b')),hitLab:!!(e.target.closest&&e.target.closest('.path-label'))},timestamp:Date.now()})}).catch(function(){});}catch(eExp){}
        // #endregion
        e.preventDefault();e.stopPropagation();return;
      }
      if(e.target.closest('code')||e.target.closest('b')){
        pathBox.classList.remove('is-expanded');
        pathBox.classList.add('is-collapsed');
        pathBox.setAttribute('aria-expanded','false');
        if(typeof scheduleEqualizeCardRows==='function')scheduleEqualizeCardRows();
        e.preventDefault();e.stopPropagation();return;
      }
      return;
      }
    }
    if(entry.classList.contains('highlight'))return;"""

BRACE_NEW = """      if(false){
      if(!pathBox.classList.contains('is-expanded')){
        pathBox.classList.add('is-expanded');
        pathBox.classList.remove('is-collapsed');
        pathBox.setAttribute('aria-expanded','true');
        if(typeof scheduleEqualizeCardRows==='function')scheduleEqualizeCardRows();
        // #region agent log
        try{fetch('http://127.0.0.1:7529/ingest/1cf46354-1d61-4c80-bd72-a340f1db1b51',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'c00e3e'},body:JSON.stringify({sessionId:'c00e3e',runId:'path-card',hypothesisId:'A',location:'catalog:pathExpand',message:'path-expand-old',data:{portable:!!window.CATALOG_PORTABLE,tag:e.target&&e.target.tagName,cls:((e.target&&e.target.className)||'').toString().slice(0,80),hitCode:!!(e.target.closest&&e.target.closest('code')),hitB:!!(e.target.closest&&e.target.closest('b')),hitLab:!!(e.target.closest&&e.target.closest('.path-label'))},timestamp:Date.now()})}).catch(function(){});}catch(eExp){}
        // #endregion
        e.preventDefault();e.stopPropagation();return;
      }
      if(e.target.closest('code')||e.target.closest('b')){
        pathBox.classList.remove('is-expanded');
        pathBox.classList.add('is-collapsed');
        pathBox.setAttribute('aria-expanded','false');
        if(typeof scheduleEqualizeCardRows==='function')scheduleEqualizeCardRows();
        e.preventDefault();e.stopPropagation();return;
      }
      return;
      }
    }
    if(entry.classList.contains('highlight'))return;"""


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
    print(f"  wrote {path.name} bytes {old_size} -> {new_size}")


def patch_once(text: str, old: str, new: str, label: str) -> str:
    n = text.count(old)
    if n != 1:
        raise SystemExit(f"  {label}: matches {n}, expected 1")
    return text.replace(old, new, 1)


def main() -> None:
    for path in FILES:
        text = path.read_text(encoding="utf-8")
        if MARK in text and "path-no-expand" in text:
            print(f"{path.name}: already patched")
            continue
        print(path.name)
        text = patch_once(text, TAIL_END, TAIL_NEW, "css-hide")
        text = patch_once(text, SPACE_OLD, SPACE_NEW, "space-patches")
        text = patch_once(text, ACT_OLD, ACT_NEW, "space-actions")
        text = patch_once(text, SEL_OLD, SEL_NEW, "near-sel")
        text = patch_once(text, EXPAND_OLD, EXPAND_NEW, "no-expand")
        text = patch_once(text, RETURN_OLD, RETURN_NEW, "no-return")
        safe_write(path, text)


if __name__ == "__main__":
    main()
