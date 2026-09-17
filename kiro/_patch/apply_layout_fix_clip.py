#!/usr/bin/env python3
"""Win Upper AC/KW clip over max-height:none !important leftovers."""
from pathlib import Path
import shutil

KIRO = Path("/home/phnx/KIRO/.kiro/specs/kontakt-workspace-drive-dirty-fix/artifacts")
WS = Path("/home/phnx/kiro-kontakt-patch/kiro/specs/kontakt-workspace-drive-dirty-fix/artifacts")
PUB = Path("/home/phnx/kiro-kontakt-patch/public/catalogs")

OLD = (
    " body.display-upper .catalog-header{position:sticky;top:0;z-index:320;background:var(--bg-surface)}\n"
    " body.display-upper.search-mode .search-chrome{position:sticky;top:var(--cat-header-h,3.5rem);z-index:220;overflow:hidden;align-items:stretch;background:var(--bg-surface)}\n"
    " body.display-upper.search-mode .search-col,body.display-upper.search-mode #filterWrap{min-height:0;max-height:100%;overflow:hidden}\n"
    " body.display-upper.search-mode #acShell,body.display-upper.search-mode #acShell.open,body.display-upper.search-mode #acList,body.display-upper.search-mode #acList.open{position:relative!important;inset:auto!important;max-height:100%;overflow:auto}\n"
    " body.display-upper.search-mode #filterWrap.open .filter-panel,body.display-upper.search-mode #kwbar{max-height:100%;overflow:auto}\n"
)
NEW = (
    " body.display-upper .catalog-header{position:sticky;top:0;z-index:320;background:var(--bg-surface)}\n"
    " body.display-upper.search-mode .search-chrome{position:sticky;top:var(--cat-header-h,3.5rem);z-index:220;overflow:hidden;align-items:stretch;background:var(--bg-surface);grid-template-rows:minmax(0,1fr)}\n"
    " body.display-upper.search-mode .search-col{display:flex;flex-direction:column;min-height:0;max-height:100%;overflow:hidden}\n"
    " body.display-upper.search-mode #filterWrap,body.display-upper.search-mode #filterWrap.open{min-height:0;max-height:100%;overflow:hidden}\n"
    " body.display-upper.search-mode #acShell,body.display-upper.search-mode #acShell.open,body.display-upper.search-mode #acList,body.display-upper.search-mode #acList.open{position:relative!important;inset:auto!important;flex:1 1 auto;min-height:0;max-height:100%!important;height:auto!important;overflow:auto!important}\n"
    " body.display-upper.search-mode #filterWrap.open .filter-panel,body.display-upper.search-mode #kwbar{max-height:100%!important;overflow:auto!important}\n"
)


def patch_text(text, name):
    if NEW in text:
        print(f"  skip {name}")
        return text
    n = text.count(OLD)
    if n != 1:
        raise SystemExit(f"{name}: expected 1 clip CSS, got {n}")
    text = text.replace(OLD, NEW)
    if "function hideSearchAc" not in text:
        raise SystemExit(f"TRUNCATED {name}: hideSearchAc")
    if name.endswith(".html") and "</html>" not in text:
        raise SystemExit(f"TRUNCATED {name}: </html>")
    print(f"  {name} clip")
    return text


def main():
    for name in ("build-ds-catalog-html.sh", "build-kontakt-catalog-html.sh"):
        src = KIRO / name
        out = patch_text(src.read_text(encoding="utf-8"), name)
        src.write_text(out, encoding="utf-8")
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
        if not path.exists():
            continue
        path.write_text(patch_text(path.read_text(encoding="utf-8"), path.name), encoding="utf-8")
        print("patched", path.name)


if __name__ == "__main__":
    main()
