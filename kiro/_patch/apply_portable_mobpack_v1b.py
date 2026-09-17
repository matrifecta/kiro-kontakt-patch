#!/usr/bin/env python3
"""Finish MOBPACK: Window Index vs embed, always-hide KW back, portrait stripe, menu-rect gates."""
from __future__ import annotations

import os
import tempfile
from pathlib import Path

ROOT = Path("/home/phnx/kiro-kontakt-patch/public/catalogs")
FILES = [
    ROOT / "KONTAKT-CATALOG-portable.html",
    ROOT / "DS-CATALOG-portable.html",
]

IX_HIDE_OLD = """/* fix-MOBPACK-v1: Window Index must not overlay or shove an extended/front card */
html body.catalog-portable:is(.chosen-preview-open,.card-embed-open,.hl-open,.gallery-open,.img-focus-open,.desc-reader-open,.path-reader-open,.desc-focus-open,.path-focus-open) #catalogIndex,
html body.catalog-portable:is(.chosen-preview-open,.card-embed-open,.hl-open,.gallery-open,.img-focus-open,.desc-reader-open,.path-reader-open,.desc-focus-open,.path-focus-open) #catalogMain>#catalogIndex,
html body.catalog-portable.content-window-on:is(.chosen-preview-open,.card-embed-open,.hl-open,.gallery-open,.img-focus-open,.desc-reader-open,.path-reader-open,.desc-focus-open,.path-focus-open) #catalogIndex{
  display:none!important;visibility:hidden!important;pointer-events:none!important;
  height:0!important;max-height:0!important;min-height:0!important;flex:0 0 0px!important;
  overflow:hidden!important;margin:0!important;padding:0!important;border:0!important
}
"""

IX_HIDE_NEW = """/* fix-MOBPACK-v1: Window Index must not overlay or shove an extended/front card */
html body.catalog-portable:is(.chosen-preview-open,.card-embed-open,.hl-open,.gallery-open,.img-focus-open,.desc-reader-open,.path-reader-open,.desc-focus-open,.path-focus-open):not(.catalog-help-open):not(.catalog-help-fs) #catalogIndex:not(.is-embedded),
html body.catalog-portable.content-window-on:is(.chosen-preview-open,.card-embed-open,.hl-open,.gallery-open,.img-focus-open,.desc-reader-open,.path-reader-open,.desc-focus-open,.path-focus-open):not(.catalog-help-open):not(.catalog-help-fs) #catalogIndex:not(.is-embedded),
html body.catalog-portable:is(.chosen-preview-open,.card-embed-open,.hl-open,.gallery-open,.img-focus-open,.desc-reader-open,.path-reader-open,.desc-focus-open,.path-focus-open):not(.catalog-help-open):not(.catalog-help-fs) #catalogJumpStack{
  visibility:hidden!important;pointer-events:none!important
}
/* fix-PORTABLE-MOBPACK-v1 */
@media(orientation:portrait){
  body.catalog-portable .catalog-header h1#top{column-gap:max(6.6rem,32vw)!important}
  body.catalog-portable .catalog-header h1#top .hdr-title-lead,
  body.catalog-portable .catalog-header h1#top .hdr-title-tail{
    justify-self:center!important;text-align:center!important;
    padding-left:max(0px,env(safe-area-inset-left,0px))!important;
    padding-right:max(0px,env(safe-area-inset-right,0px))!important
  }
  body.catalog-portable.display-sides:not(.search-chrome-collapsed) #catalogMainHoverStripe.hover-scroll-fixed,
  body.catalog-portable.display-sides.kw-open:not(.kw-chrome-collapsed) #catalogMainHoverStripe.hover-scroll-fixed,
  body.catalog-portable.display-middle:not(.search-chrome-collapsed) #catalogMainHoverStripe.hover-scroll-fixed,
  body.catalog-portable.display-middle.kw-open:not(.kw-chrome-collapsed) #catalogMainHoverStripe.hover-scroll-fixed{
    display:none!important;pointer-events:none!important;visibility:hidden!important
  }
}
html body.catalog-portable #kwFsBack,
html body.catalog-portable .kw-fs-back,
html body.catalog-portable.kw-fs-open #kwFsBack,
html body.catalog-portable.kw-fs-open .kw-fs-back{
  display:none!important;visibility:hidden!important;pointer-events:none!important
}
html body.catalog-portable:not(.kw-chrome-collapsed) #kwStripHide{
  display:inline-flex!important;visibility:visible!important
}
html body.catalog-portable #catSwitch .cat-btn.active{
  background:var(--accent-instrument-bg)!important
}
html body.catalog-portable.index-fill-doc #catalogIndex:not(.is-embedded):not(.is-collapsed){
  overflow:hidden!important
}
html body.catalog-portable.index-fill-doc #catalogIndexList,
html body.catalog-portable.index-fill-doc #catalogIndex:not(.is-embedded):not(.is-collapsed) .index{
  overflow-y:auto!important;min-height:0!important;flex:1 1 auto!important
}
html body.catalog-portable:is(.chosen-preview-open,.card-embed-open) .entry.selected:not(.highlight){
  position:fixed!important;left:50%!important;top:50%!important;
  transform:translate(-50%,-50%)!important
}
"""

MENU_OLD = """function portableMenuVisibleRect(id){
  var el=document.getElementById(id);
  if(!el)return null;
  var cs=getComputedStyle(el);
  if(cs.display==='none'||cs.visibility==='hidden')return null;
  var r=el.getBoundingClientRect();
  if(!r||r.width<24||r.height<24)return null;
  return r;
}"""

MENU_NEW = """function portableMenuVisibleRect(id){
  var el=document.getElementById(id);
  if(!el)return null;
  var b=document.body;
  if(id==='searchChrome'&&b.classList.contains('search-chrome-collapsed'))return null;
  if(id==='filterWrap'&&(!b.classList.contains('kw-open')||b.classList.contains('kw-chrome-collapsed')))return null;
  var cs=getComputedStyle(el);
  if(cs.display==='none'||cs.visibility==='hidden')return null;
  var r=el.getBoundingClientRect();
  if(!r||r.width<24||r.height<24)return null;
  return r;
}"""


def once(text: str, old: str, new: str, label: str, name: str) -> str:
    if old not in text:
        if label == "ix-hide" and "fix-PORTABLE-MOBPACK-v1" in text:
            print(f"  skip {label} {name}")
            return text
        if label == "menu-rect" and "search-chrome-collapsed" in text[text.find("function portableMenuVisibleRect") : text.find("function portableMenuVisibleRect") + 500]:
            print(f"  skip {label} {name}")
            return text
        raise SystemExit(f"{name}: missing {label}: {old[:80]!r}")
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
        check = tmp_path.read_text(encoding="utf-8")
        if not check.rstrip().endswith("</html>"):
            tmp_path.unlink(missing_ok=True)
            raise SystemExit(f"{path.name}: tmp missing </html>")
        size = tmp_path.stat().st_size
        if size < 200_000:
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


def patch(path: Path) -> None:
    name = path.name
    text = path.read_text(encoding="utf-8")
    text = once(text, IX_HIDE_OLD, IX_HIDE_NEW, "ix-hide", name)
    text = once(text, MENU_OLD, MENU_NEW, "menu-rect", name)
    if "fix-PORTABLE-MOBPACK-v1" not in text:
        raise SystemExit(f"{name}: css missing")
    if ":not(.is-embedded)" not in text[text.find("Window Index must not overlay") : text.find("Window Index must not overlay") + 900]:
        raise SystemExit(f"{name}: embed-safe hide missing")
    safe_write(path, text)


def main() -> None:
    for p in FILES:
        print("==", p.name)
        patch(p)


if __name__ == "__main__":
    main()
