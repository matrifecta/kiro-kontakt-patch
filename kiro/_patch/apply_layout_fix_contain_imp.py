#!/usr/bin/env python3
from pathlib import Path
import shutil

KIRO = Path("/home/phnx/KIRO/.kiro/specs/kontakt-workspace-drive-dirty-fix/artifacts")
WS = Path("/home/phnx/kiro-kontakt-patch/kiro/specs/kontakt-workspace-drive-dirty-fix/artifacts")
PUB = Path("/home/phnx/kiro-kontakt-patch/public/catalogs")

CSS_OLD = (
    " body.display-upper.search-mode .search-chrome{position:sticky;top:var(--cat-header-h,3.5rem);z-index:220;overflow:hidden;align-items:stretch;background:var(--bg-surface);grid-template-rows:minmax(0,1fr)}\n"
    " body.display-upper.search-mode .search-col{display:flex;flex-direction:column;min-height:0;max-height:100%;overflow:hidden}\n"
    " body.display-upper.search-mode #filterWrap,body.display-upper.search-mode #filterWrap.open{min-height:0;max-height:100%;overflow:hidden}\n"
    " body.display-upper.search-mode #acShell,body.display-upper.search-mode #acShell.open,body.display-upper.search-mode #acList,body.display-upper.search-mode #acList.open{position:relative!important;inset:auto!important;flex:1 1 auto;min-height:0;max-height:100%!important;height:auto!important;overflow:auto!important}\n"
    " body.display-upper.search-mode #filterWrap.open .filter-panel,body.display-upper.search-mode #kwbar{max-height:100%!important;overflow:auto!important}\n"
)
CSS_NEW = (
    " body.display-upper.search-mode .search-chrome{position:sticky;top:var(--cat-header-h,3.5rem);z-index:220;overflow:hidden!important;align-items:stretch;background:var(--bg-surface);grid-template-rows:minmax(0,1fr)}\n"
    " body.display-upper.search-mode .search-col{display:flex;flex-direction:column;min-height:0;max-height:100%;overflow:hidden}\n"
    " body.display-upper.search-mode #filterWrap,body.display-upper.search-mode #filterWrap.open{min-height:0;max-height:100%;overflow:hidden}\n"
    " body.display-upper.search-mode #acShell,body.display-upper.search-mode #acShell.open,body.display-upper.search-mode #acList,body.display-upper.search-mode #acList.open{position:relative!important;inset:auto!important;flex:1 1 auto;min-height:0;overflow:auto!important}\n"
    " body.display-upper.search-mode #filterWrap.open .filter-panel,body.display-upper.search-mode #kwbar{overflow:auto!important}\n"
)
CAP_OLD = "  function cap(el){if(!el)return;el.style.maxHeight=Math.max(72,Math.round(bottom-el.getBoundingClientRect().top))+'px';}\n"
CAP_NEW = "  function cap(el){if(!el)return;el.style.setProperty('max-height',Math.max(72,Math.round(bottom-el.getBoundingClientRect().top))+'px','important');}\n"
CLR_OLD = "  function clr(el){if(el)el.style.removeProperty('max-height');}\n"
CLR_NEW = "  function clr(el){if(el)el.style.removeProperty('max-height');}\n"


def patch_text(text, name):
    if CAP_NEW in text and "overflow:hidden!important;align-items:stretch" in text:
        print(f"  skip {name}")
        return text
    for old, new, label in (
        (CSS_OLD, CSS_NEW, "css"),
        (CAP_OLD, CAP_NEW, "cap"),
    ):
        n = text.count(old)
        if n != 1:
            raise SystemExit(f"{name}:{label} count={n}")
        text = text.replace(old, new)
        print(f"  {name}:{label}")
    if "function hideSearchAc" not in text:
        raise SystemExit(f"TRUNCATED {name}")
    if name.endswith(".html") and "</html>" not in text:
        raise SystemExit(f"TRUNCATED {name} html")
    return text


def main():
    for name in ("build-ds-catalog-html.sh", "build-kontakt-catalog-html.sh"):
        src = KIRO / name
        src.write_text(patch_text(src.read_text(encoding="utf-8"), name), encoding="utf-8")
        shutil.copy2(src, WS / name)
        print("patched KIRO", name)
    for path in [
        PUB / "DS-CATALOG.html",
        PUB / "DS-CATALOG-portable.html",
        PUB / "KONTAKT-CATALOG.html",
        PUB / "KONTAKT-CATALOG-portable.html",
        WS / "DS-CATALOG.html",
        WS / "DS-CATALOG-portable.html",
        WS / "KONTAKT-CATALOG.html",
        WS / "KONTAKT-CATALOG-portable.html",
    ]:
        if path.exists():
            path.write_text(patch_text(path.read_text(encoding="utf-8"), path.name), encoding="utf-8")
            print("patched", path.name)


if __name__ == "__main__":
    main()
