#!/usr/bin/env python3
from pathlib import Path
import shutil

KIRO = Path("/home/phnx/KIRO/.kiro/specs/kontakt-workspace-drive-dirty-fix/artifacts")
WS = Path("/home/phnx/kiro-kontakt-patch/kiro/specs/kontakt-workspace-drive-dirty-fix/artifacts")
PUB = Path("/home/phnx/kiro-kontakt-patch/public/catalogs")

OLD = """  body.search-mode.kw-open:not(.ac-fs-open):not(.search-chrome-collapsed) .search-autocomplete.open{max-height:min(32vh,20rem);overflow-y:auto}
  /* Side dropdowns only from the collapsed toolbar — do not overlay shade or the split. */"""

NEW = """  body.search-mode.kw-open:not(.ac-fs-open):not(.search-chrome-collapsed) .search-autocomplete.open{max-height:min(32vh,20rem);overflow-y:auto}
  /* Shade: Keywords-only dropdown on the right; catalog stays full-width behind. */
  body:not(.search-mode):not(.kw-fs-open) .filter-wrap{overflow:visible}
  body:not(.search-mode):not(.kw-fs-open) .filter-wrap.open .filter-panel{position:absolute;top:calc(100% + 4px);right:0;left:auto;width:min(28vw,24rem);max-width:calc(100vw - 1.25rem);max-height:min(40vh,22rem);z-index:230;background:var(--bg-surface);border:1px solid var(--border);border-radius:8px;box-shadow:0 16px 40px rgba(0,0,0,.38)}
  /* Collapsed toolbar: side dropdowns. Do not overlay the combined split. */"""


def main():
    for name in ("build-ds-catalog-html.sh", "build-kontakt-catalog-html.sh"):
        shutil.copy2(KIRO / name, WS / name)
        print(f"copied {name}")

    paths = [
        PUB / "DS-CATALOG.html",
        PUB / "DS-CATALOG-portable.html",
        PUB / "KONTAKT-CATALOG.html",
        PUB / "KONTAKT-CATALOG-portable.html",
        WS / "DS-CATALOG.html",
        WS / "DS-CATALOG-portable.html",
        WS / "KONTAKT-CATALOG.html",
        WS / "KONTAKT-CATALOG-portable.html",
    ]
    for path in paths:
        text = path.read_text(encoding="utf-8")
        n = text.count(OLD)
        if n == 0:
            if NEW in text:
                print(f"skip {path.name} already")
                continue
            raise SystemExit(f"MISSING css in {path}")
        if n != 1:
            raise SystemExit(f"COUNT {path.name}: {n}")
        text = text.replace(OLD, NEW, 1)
        if "</html>" not in text or "function hideSearchAc" not in text:
            raise SystemExit(f"TRUNCATED {path}")
        path.write_text(text, encoding="utf-8")
        print(f"patched {path.name} {len(text)}")


if __name__ == "__main__":
    main()
