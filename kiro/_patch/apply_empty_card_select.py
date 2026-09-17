#!/usr/bin/env python3
"""Empty card chrome (gaps/padding) selects the card; only real controls block."""
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
MARK = "fix-EMPTY-CARD-SELECT-v1"

SEL_OLD = (
    "var sel='a,button,.fav-btn,.fs-btn,.hl-close,.hl-min,.preview-back,.search-popup-btn,"
    ".search-link,.patches,summary,input,select,textarea,.note-balloon,.note-pop,.note-save,"
    ".note-cancel,.note-ta,.kw,.card-search-embed,#cardMinDock,.cover,.summary-panel,"
    ".path-icon-btn,.folder,.path-fs-hit,.path-copy-hit,.path-action-row';"
)
SEL_NEW = (
    "var sel='a,button,.fav-btn,.fs-btn,.hl-close,.hl-min,.preview-back,.search-popup-btn,"
    ".search-link,summary,input,select,textarea,.note-balloon,.note-pop,.note-save,"
    ".note-cancel,.note-ta,.kw,.card-search-embed,#cardMinDock,"
    ".path-icon-btn,.folder,.path-fs-hit,.path-copy-hit';"
)

EARLY_OLD = (
    "    if(e.target.closest('a,.hl-close,.hl-min,.preview-back,.kw,input,select,textarea,"
    "summary,.patches,.search-popup-btn,.search-link,.fav-btn,.note-balloon,.note-pop,"
    ".un-badge,.note-save,.note-cancel,.fs-btn,.card-search-embed,#cardMinDock')) return;"
)
EARLY_NEW = (
    "    if(e.target.closest('a,.hl-close,.hl-min,.preview-back,.kw,input,select,textarea,"
    "summary,.search-popup-btn,.search-link,.fav-btn,.note-balloon,.note-pop,"
    ".un-badge,.note-save,.note-cancel,.fs-btn,.card-search-embed,#cardMinDock')) return;"
)

PATH_ROW_OLD = """      if(e.target.closest('.path-action-row')&&!e.target.closest('.path-fs-hit,.path-copy-hit,.folder')){
        e.preventDefault();e.stopPropagation();return;
      }
"""
PATH_ROW_NEW = """      /* """ + MARK + """: empty PATH chrome falls through to card select */
"""

SEL_FN_OLD = """function selectCardFromEmpty(entry){
  if(!entry)return;
  if(typeof rememberViewed==='function')rememberViewed(entry);
  else if(typeof markSelected==='function')markSelected(entry);
}"""

SEL_FN_NEW = """function selectCardFromEmpty(entry){
  if(!entry)return;
  // #region agent log
  try{fetch('http://127.0.0.1:7529/ingest/1cf46354-1d61-4c80-bd72-a340f1db1b51',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'c00e3e'},body:JSON.stringify({sessionId:'c00e3e',runId:'post-fix',hypothesisId:'A',location:'catalog:selectCardFromEmpty',message:'empty-card-select',data:{id:entry&&entry.id,portable:!!window.CATALOG_PORTABLE},timestamp:Date.now()})}).catch(function(){});}catch(eEmp){}
  // #endregion
  if(typeof rememberViewed==='function')rememberViewed(entry);
  else if(typeof markSelected==='function')markSelected(entry);
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
        text = path.read_text(encoding="utf-8")
        print(path.name)
        text = patch_once(text, SEL_OLD, SEL_NEW, "near-sel")
        text = patch_once(text, EARLY_OLD, EARLY_NEW, "early")
        text = patch_once(text, PATH_ROW_OLD, PATH_ROW_NEW, "path-row")
        text = patch_once(text, SEL_FN_OLD, SEL_FN_NEW, "select-fn")
        safe_write(path, text)


if __name__ == "__main__":
    main()
