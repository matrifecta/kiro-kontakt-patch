#!/usr/bin/env python3
"""Hide leftover Keywords collapse arrow in desktop Middle. Keep Sides nest arrow."""
from __future__ import annotations

import os
import tempfile
from pathlib import Path

ROOT = Path("/home/phnx/kiro-kontakt-patch")
FILES = [
    ROOT / "public/catalogs/DS-CATALOG.html",
    ROOT / "public/catalogs/KONTAKT-CATALOG.html",
]
MARK = "fix-DESKTOP-MIDDLE-KW-ARROW-v1"

CSS_OLD = (
    "  body.desk-landscape.display-sides:not(.display-middle):not(.catalog-portable) "
    "#filterToggle .toggle-arrow{transform:none}\n"
)
CSS_NEW = (
    "  body.desk-landscape.display-sides:not(.display-middle):not(.catalog-portable) "
    "#filterToggle .toggle-arrow{transform:none}\n"
    f"/* {MARK}: Middle label is not a collapse control — hide leftover ▾/▲ */\n"
    "body:not(.catalog-portable).display-middle #filterToggle .toggle-arrow,\n"
    "body:not(.catalog-portable).display-sides.display-middle #filterToggle .toggle-arrow{"
    "display:none!important}\n"
    "body:not(.catalog-portable).display-middle #filterToggle,"
    "body:not(.catalog-portable).display-sides.display-middle #filterToggle{"
    "cursor:default;pointer-events:none}\n"
)

TF_OLD = """function toggleFilter(){
  var w=document.getElementById('filterWrap'),a=document.querySelector('.toggle-arrow');
  if(!w)return;
  if(document.body.classList.contains('display-sides')){
"""
TF_NEW = """function toggleFilter(){
  var w=document.getElementById('filterWrap'),a=document.querySelector('.toggle-arrow');
  if(!w)return;
  if(!window.CATALOG_PORTABLE&&document.body.classList.contains('display-middle')){
    if(typeof logKwNest==='function')logKwNest('middle-label-noop');
    return;
  }
  if(document.body.classList.contains('display-sides')){
"""

ARROW_OLD = """  if(opts.fromArrow){
    if(typeof sidesKwCanNest==='function'&&sidesKwCanNest()){
"""
ARROW_NEW = """  if(opts.fromArrow){
    if(!window.CATALOG_PORTABLE&&document.body.classList.contains('display-middle')){
      logKwNest('middle-arrow-noop',{fromArrow:true});
      return;
    }
    if(typeof sidesKwCanNest==='function'&&sidesKwCanNest()){
"""

SYNC_OLD = """  var nested=landSides&&document.body.classList.contains('kw-nested-search')&&!hidden;
  if(a&&landSides){
    a.textContent=nested?'▲':'▼';
  }
  if(ft&&landSides){
"""
SYNC_NEW = """  var nested=landSides&&document.body.classList.contains('kw-nested-search')&&!hidden;
  var middleDesk=!!(!window.CATALOG_PORTABLE&&document.body.classList.contains('display-middle'));
  if(a&&landSides){
    a.textContent=nested?'▲':'▼';
  }
  if(ft&&middleDesk){
    ft.removeAttribute('title');
    ft.setAttribute('aria-label','Keywords');
    ft.setAttribute('aria-expanded',hidden?'false':'true');
  }
  if(ft&&landSides){
"""


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
        c00 = text.count("sessionId:'c00e3e'")
        if MARK in text:
            print("  skip (already patched)")
            continue
        text = patch_once(text, CSS_OLD, CSS_NEW, "css")
        text = patch_once(text, TF_OLD, TF_NEW, "toggleFilter")
        text = patch_once(text, ARROW_OLD, ARROW_NEW, "fromArrow")
        text = patch_once(text, SYNC_OLD, SYNC_NEW, "syncKwHideBtn")
        after = text.count("sessionId:'c00e3e'")
        if after < c00:
            raise SystemExit(f"{path.name}: lost c00e3e logs {c00}->{after}")
        if MARK not in text:
            raise SystemExit(f"{path.name}: missing {MARK}")
        safe_write(path, text)


if __name__ == "__main__":
    main()
