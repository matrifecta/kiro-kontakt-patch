#!/usr/bin/env python3
"""Sync compact-split / collapsed-only overlay from KIRO builders into catalogs."""
from pathlib import Path
import shutil

KIRO = Path("/home/phnx/KIRO/.kiro/specs/kontakt-workspace-drive-dirty-fix/artifacts")
WS = Path("/home/phnx/kiro-kontakt-patch/kiro/specs/kontakt-workspace-drive-dirty-fix/artifacts")
PUB = Path("/home/phnx/kiro-kontakt-patch/public/catalogs")

OLD_CSS = """ @media(min-width:900px){
  /* Combined/solo split (Search left, Keywords right, catalog below): keep in-flow. */
  body.search-mode.kw-open:not(.kw-fs-open):not(.search-chrome-collapsed) .filter-wrap{overflow:hidden}
  body.search-mode.kw-open:not(.kw-fs-open):not(.search-chrome-collapsed) .filter-wrap.open .filter-panel{position:static;width:auto;max-width:100%;max-height:min(72dvh,calc(100dvh - 7rem));box-shadow:none;border:0;border-radius:0}
  body.search-mode.kw-open:not(.ac-fs-open):not(.search-chrome-collapsed) .search-col{overflow:hidden;z-index:auto}
  body.search-mode.kw-open:not(.ac-fs-open):not(.search-chrome-collapsed) .search-ac-shell.open:not(.ac-fs),
  body.search-mode.kw-open:not(.ac-fs-open):not(.search-chrome-collapsed) .search-ac-shell:has(#acList.open):not(.ac-fs){position:relative!important;left:auto!important;top:auto!important;right:auto!important;width:auto!important;max-width:100%!important;height:auto!important;max-height:min(72dvh,calc(100dvh - 7rem));box-shadow:none;border:0;border-radius:0;overflow-x:hidden;overflow-y:auto;-webkit-overflow-scrolling:touch;overscroll-behavior:contain}
  /* Side overlay dropdowns: shade-only, collapsed toolbar, or explicit overlay — not the split. */
  body:not(.search-mode):not(.kw-fs-open) .filter-wrap,
  body.search-mode.search-chrome-collapsed:not(.kw-fs-open) .filter-wrap,
  body.menu-overlay:not(.kw-fs-open) .filter-wrap{overflow:visible}
  body:not(.search-mode):not(.kw-fs-open) .filter-wrap.open .filter-panel,
  body.search-mode.search-chrome-collapsed:not(.kw-fs-open) .filter-wrap.open .filter-panel,
  body.menu-overlay:not(.kw-fs-open) .filter-wrap.open .filter-panel{position:absolute;top:calc(100% + 4px);right:0;left:auto;width:min(42vw,38rem);max-width:calc(100vw - 1.25rem);max-height:min(72dvh,calc(100dvh - 7rem));z-index:230;background:var(--bg-surface);border:1px solid var(--border);border-radius:8px;box-shadow:0 16px 40px rgba(0,0,0,.38)}
  body.search-mode.search-chrome-collapsed:not(.ac-fs-open) .search-col,
  body.menu-overlay.search-mode:not(.ac-fs-open):not(.kw-open) .search-col{overflow:visible;z-index:225}
  body.search-mode.search-chrome-collapsed:not(.ac-fs-open) .search-ac-shell.open:not(.ac-fs),
  body.search-mode.search-chrome-collapsed:not(.ac-fs-open) .search-ac-shell:has(#acList.open):not(.ac-fs),
  body.menu-overlay.search-mode:not(.ac-fs-open):not(.kw-open) .search-ac-shell.open:not(.ac-fs){position:absolute;left:0;right:auto;top:calc(100% + 4px);width:min(42vw,38rem);max-width:calc(100vw - 1.25rem);max-height:min(72dvh,calc(100dvh - 7rem));z-index:226;overflow-x:hidden;overflow-y:auto;-webkit-overflow-scrolling:touch;overscroll-behavior:contain;background:var(--bg-surface);border:1px solid var(--border);border-radius:8px;box-shadow:0 16px 40px rgba(0,0,0,.38)}
  .catalog-index,.catalog-body{overscroll-behavior:contain}
 }"""

NEW_CSS = """ @media(min-width:900px){
  /* Combined split: Search left, Keywords right, catalog visible below. Compact chrome. */
  body.search-mode.kw-open:not(.kw-fs-open):not(.search-chrome-collapsed) .filter-wrap{overflow:hidden}
  body.search-mode.kw-open:not(.kw-fs-open):not(.search-chrome-collapsed) .filter-wrap.open .filter-panel,
  body.search-mode.kw-open:not(.kw-fs-open):not(.search-chrome-collapsed) .filter-wrap.kw-shade-height-set.open .filter-panel{position:static!important;width:auto!important;max-width:100%;max-height:min(32vh,20rem)!important;box-shadow:none;border:0;border-radius:0}
  body.search-mode.kw-open:not(.ac-fs-open):not(.search-chrome-collapsed) .search-col{overflow:hidden;z-index:auto}
  body.search-mode.kw-open:not(.ac-fs-open):not(.search-chrome-collapsed) .search-ac-shell.open:not(.ac-fs),
  body.search-mode.kw-open:not(.ac-fs-open):not(.search-chrome-collapsed) .search-ac-shell:has(#acList.open):not(.ac-fs){position:relative!important;left:auto!important;top:auto!important;right:auto!important;width:auto!important;max-width:100%!important;height:auto!important;max-height:min(32vh,20rem);box-shadow:none;border:0;border-radius:0;overflow-x:hidden;overflow-y:auto;-webkit-overflow-scrolling:touch;overscroll-behavior:contain}
  body.search-mode.kw-open:not(.ac-fs-open):not(.search-chrome-collapsed) .search-autocomplete.open{max-height:min(32vh,20rem);overflow-y:auto}
  /* Side dropdowns only from the collapsed toolbar — do not overlay shade or the split. */
  body.search-mode.search-chrome-collapsed:not(.kw-fs-open) .filter-wrap{overflow:visible}
  body.search-mode.search-chrome-collapsed:not(.kw-fs-open) .filter-wrap.open .filter-panel{position:absolute;top:calc(100% + 4px);right:0;left:auto;width:min(36vw,32rem);max-width:calc(100vw - 1.25rem);max-height:min(56vh,28rem);z-index:230;background:var(--bg-surface);border:1px solid var(--border);border-radius:8px;box-shadow:0 16px 40px rgba(0,0,0,.38)}
  body.search-mode.search-chrome-collapsed:not(.ac-fs-open) .search-col{overflow:visible;z-index:225}
  body.search-mode.search-chrome-collapsed:not(.ac-fs-open) .search-ac-shell.open:not(.ac-fs),
  body.search-mode.search-chrome-collapsed:not(.ac-fs-open) .search-ac-shell:has(#acList.open):not(.ac-fs){position:absolute;left:0;right:auto;top:calc(100% + 4px);width:min(36vw,32rem);max-width:calc(100vw - 1.25rem);max-height:min(56vh,28rem);z-index:226;overflow-x:hidden;overflow-y:auto;-webkit-overflow-scrolling:touch;overscroll-behavior:contain;background:var(--bg-surface);border:1px solid var(--border);border-radius:8px;box-shadow:0 16px 40px rgba(0,0,0,.38)}
 }"""

OLD_COMBINED = """  if(combined){
    clearAcShellPos(sh);
    sh.classList.add('open');"""

NEW_COMBINED = """  if(combined){
    clearAcShellPos(sh);
    var acIn=acListEl();
    if(acIn&&typeof clearAcBox==='function')clearAcBox(acIn);
    sh.classList.add('open');"""

OLD_APPLY = """function applyAcHeight(){
  var ac=acListEl(),b=acBtn(),sh=acShell();
  if(sh)sh.classList.toggle('open',acOpen());
  placeAcShell();
  if(!ac||!acOpen()){"""

NEW_APPLY = """function applyAcHeight(){
  var ac=acListEl(),b=acBtn(),sh=acShell();
  if(sh)sh.classList.toggle('open',acOpen());
  placeAcShell();
  var combined=document.body.classList.contains('search-mode')&&document.body.classList.contains('kw-open')&&!document.body.classList.contains('search-chrome-collapsed')&&!document.body.classList.contains('kw-fs-open')&&!acFullscreen();
  if(combined){
    if(ac&&!adrag)clearAcBox(ac);
    if(b)b.setAttribute('aria-hidden','true');
    syncAcWidthBtn();
    return;
  }
  if(!ac||!acOpen()){"""

OLD_H2 = "var h2=ix&&ix.previousElementSibling;var d={h:'toggleFilter'"
NEW_H2 = "var h2=ix&&ix.previousElementSibling;var fp=fw&&fw.querySelector('.filter-panel');var fpr=fp&&fp.getBoundingClientRect();var fps=fp&&getComputedStyle(fp);var sh=document.getElementById('acShell');var shr=sh&&sh.getBoundingClientRect();var shs=sh&&getComputedStyle(sh);var d={h:'toggleFilter'"

OLD_H2END = "h2:h2&&(h2.textContent||'').slice(0,24)}"
NEW_H2END = "h2:h2&&(h2.textContent||'').slice(0,24),fp:fpr?[Math.round(fpr.x),Math.round(fpr.y),Math.round(fpr.width),Math.round(fpr.height)]:[],fpPos:fps&&fps.position,fpMh:fps&&fps.maxHeight,shCls:sh&&sh.className,shPos:shs&&shs.position,sh:shr?[Math.round(shr.x),Math.round(shr.y),Math.round(shr.width),Math.round(shr.height)]:[],vh:window.innerHeight,shadeH:!!(fw&&fw.classList.contains('kw-shade-height-set'))}"

OLD_RUN = "{sessionId:'f491c2',runId:'pre-fix',hypothesisId:hid,location:'toggleFilter'"
NEW_RUN = "{sessionId:'f491c2',runId:'layout-v3',hypothesisId:hid,location:'toggleFilter'"


def must_replace(text, old, new, label, count=None):
    n = text.count(old)
    if n == 0:
        if new in text:
            print(f"  skip {label} (already applied)")
            return text
        raise SystemExit(f"MISSING [{label}]")
    if count is not None and n != count:
        raise SystemExit(f"COUNT [{label}]: expected {count}, found {n}")
    return text.replace(old, new)


def patch_html(text, name):
    text = must_replace(text, OLD_CSS, NEW_CSS, f"{name}:css")
    text = must_replace(text, OLD_COMBINED, NEW_COMBINED, f"{name}:combined")
    text = must_replace(text, OLD_APPLY, NEW_APPLY, f"{name}:apply")
    text = must_replace(text, OLD_H2, NEW_H2, f"{name}:h2")
    text = must_replace(text, OLD_H2END, NEW_H2END, f"{name}:h2end")
    text = must_replace(text, OLD_RUN, NEW_RUN, f"{name}:run")
    if "</html>" not in text:
        raise SystemExit(f"TRUNCATED {name}: missing </html>")
    if "function hideSearchAc" not in text:
        raise SystemExit(f"TRUNCATED {name}: missing hideSearchAc")
    if "max-height:min(32vh,20rem)!important" not in text:
        raise SystemExit(f"MISSING cap in {name}")
    if "body:not(.search-mode):not(.kw-fs-open)" in text:
        raise SystemExit(f"SHADE OVERLAY STILL PRESENT in {name}")
    return text


def main():
    for name in ("build-ds-catalog-html.sh", "build-kontakt-catalog-html.sh"):
        shutil.copy2(KIRO / name, WS / name)
        print(f"copied {name}")

    htmls = [
        PUB / "DS-CATALOG.html",
        PUB / "DS-CATALOG-portable.html",
        PUB / "KONTAKT-CATALOG.html",
        PUB / "KONTAKT-CATALOG-portable.html",
        WS / "DS-CATALOG.html",
        WS / "DS-CATALOG-portable.html",
        WS / "KONTAKT-CATALOG.html",
        WS / "KONTAKT-CATALOG-portable.html",
    ]
    for path in htmls:
        raw = path.read_text(encoding="utf-8")
        out = patch_html(raw, path.name)
        path.write_text(out, encoding="utf-8")
        print(f"patched {path} bytes={len(out)}")


if __name__ == "__main__":
    main()
