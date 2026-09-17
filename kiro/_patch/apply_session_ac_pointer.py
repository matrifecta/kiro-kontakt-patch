#!/usr/bin/env python3
"""Restore saved sessions on pointerdown so Search blur cannot wipe the row first."""
from pathlib import Path

ROOT = Path("/home/phnx/kiro-kontakt-patch")
FILES = [
    ROOT / "public/catalogs/DS-CATALOG.html",
    ROOT / "public/catalogs/KONTAKT-CATALOG.html",
    ROOT / "public/catalogs/DS-CATALOG-portable.html",
    ROOT / "public/catalogs/KONTAKT-CATALOG-portable.html",
    ROOT / "kiro/specs/kontakt-workspace-drive-dirty-fix/artifacts/build-ds-catalog-html.sh",
    ROOT / "kiro/specs/kontakt-workspace-drive-dirty-fix/artifacts/build-kontakt-catalog-html.sh",
]

ONCLICK_OLD = (
    "html+='<div class=\"ac-item ac-session\" data-cat=\"session\" "
    "onclick=\"restorePinSession(\\''+jsStr(s.id)+'\\',event)\">"
)
ONCLICK_NEW = (
    "html+='<div class=\"ac-item ac-session\" data-cat=\"session\" data-sid=\"'+htmlStr(s.id)+'\" "
    "onclick=\"restorePinSession(\\''+jsStr(s.id)+'\\',event)\">"
)

RESTORE_HEAD_OLD = """window.restorePinSession=function(id,ev){
  if(ev&&ev.stopPropagation){ev.preventDefault();ev.stopPropagation();}
  var sess=null;
"""
RESTORE_HEAD_NEW = """window.restorePinSession=function(id,ev){
  if(ev&&ev.stopPropagation){ev.preventDefault();ev.stopPropagation();}
  id=String(id||'');
  if(!id)return;
  if(window._pinSessLock===id)return;
  window._pinSessLock=id;
  setTimeout(function(){if(window._pinSessLock===id)window._pinSessLock='';},400);
  var sess=null;
"""

BIND = """(function(){
  if(window._pinSessAcBind)return;
  window._pinSessAcBind=1;
  document.addEventListener('pointerdown',function(e){
    var row=e.target&&e.target.closest&&e.target.closest('.ac-item');
    if(!row)return;
    window._acItemPointer=1;
    if(!row.classList.contains('ac-session'))return;
    var id=row.getAttribute('data-sid');
    if(!id){
      var m=String(row.getAttribute('onclick')||'').match(/restorePinSession\\('([^']+)'/);
      id=m&&m[1];
    }
    if(id&&typeof restorePinSession==='function')restorePinSession(id,e);
  },true);
  document.addEventListener('mousedown',function(e){
    if(e.target&&e.target.closest&&e.target.closest('#acList .ac-item,.search-autocomplete .ac-item'))e.preventDefault();
  },true);
  document.addEventListener('pointerup',function(){
    setTimeout(function(){window._acItemPointer=0;},250);
  },true);
})();
"""

SKIP = "    if(window._acItemPointer)return;\n    if(acL){acL.classList.remove('open');acL.innerHTML='';}"


def patch(path: Path):
    t = path.read_text(encoding="utf-8")
    n_on = t.count(ONCLICK_OLD)
    if n_on != 2:
        raise SystemExit(f"{path.name}: session onclick count={n_on} expected 2")
    t = t.replace(ONCLICK_OLD, ONCLICK_NEW)

    if t.count(RESTORE_HEAD_OLD) != 1:
        raise SystemExit(f"{path.name}: restore head count={t.count(RESTORE_HEAD_OLD)}")
    t = t.replace(RESTORE_HEAD_OLD, RESTORE_HEAD_NEW, 1)

    marker = "window.deletePinSession=function(id){"
    if marker not in t:
        raise SystemExit(f"{path.name}: missing deletePinSession")
    if "_pinSessAcBind" not in t:
        t = t.replace(marker, BIND + marker, 1)

    clear = "    if(acL){acL.classList.remove('open');acL.innerHTML='';}"
    if SKIP not in t:
        # Prefer the focusout copy (followed by syncSearchSplit / 100ms).
        focus_clear = (
            "    var acL=document.getElementById('acList');\n"
            "    if(acL){acL.classList.remove('open');acL.innerHTML='';}\n"
            "    if(window.syncSearchSplit)window.syncSearchSplit();\n"
            "  },100);"
        )
        focus_skip = (
            "    var acL=document.getElementById('acList');\n"
            "    if(window._acItemPointer)return;\n"
            "    if(acL){acL.classList.remove('open');acL.innerHTML='';}\n"
            "    if(window.syncSearchSplit)window.syncSearchSplit();\n"
            "  },100);"
        )
        if t.count(focus_clear) >= 1:
            t = t.replace(focus_clear, focus_skip, 1)
        elif clear in t:
            t = t.replace(clear, SKIP, 1)
        else:
            raise SystemExit(f"{path.name}: no focusout clear to skip")

    t = t.replace(
        "runId:'pre-fix',hypothesisId:'H2',location:'restorePinSession',message:'restore-session-enter'",
        "runId:'post-fix',hypothesisId:'H7',location:'restorePinSession',message:'restore-session-enter'",
        1,
    )
    t = t.replace(
        "runId:'pre-fix',hypothesisId:'H7',location:'searchInput.focusout',message:'ac-focusout-clear'",
        "runId:'post-fix',hypothesisId:'H7',location:'searchInput.focusout',message:'ac-focusout-clear'",
        1,
    )
    path.write_text(t, encoding="utf-8")
    print("patched", path.name)


def main():
    for p in FILES:
        patch(p)


if __name__ == "__main__":
    main()
