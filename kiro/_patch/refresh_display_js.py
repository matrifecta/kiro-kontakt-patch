#!/usr/bin/env python3
from pathlib import Path
import shutil

KIRO = Path("/home/phnx/KIRO/.kiro/specs/kontakt-workspace-drive-dirty-fix/artifacts")
WS = Path("/home/phnx/kiro-kontakt-patch/kiro/specs/kontakt-workspace-drive-dirty-fix/artifacts")
PUB = Path("/home/phnx/kiro-kontakt-patch/public/catalogs")

ds = (KIRO / "build-ds-catalog-html.sh").read_text(encoding="utf-8")
js_start = ds.find("var DISPLAY_KEY='catalog-display-mode-")
js_end = ds.find("\n</script>", js_start)
if js_start < 0 or js_end < 0:
    raise SystemExit("JS block missing in DS builder")
JS_BLOCK = ds[js_start:js_end]
if "placeMenusForDisplay" not in JS_BLOCK:
    raise SystemExit("placeMenusForDisplay missing from extracted JS")


def refresh(text, name):
    mark = "var DISPLAY_KEY='catalog-display-mode-"
    start = text.find(mark)
    if start < 0:
        raise SystemExit(f"DISPLAY_KEY missing in {name}")
    end = text.find("\n</script>", start)
    if end < 0:
        raise SystemExit(f"script end missing in {name}")
    text = text[:start] + JS_BLOCK + text[end:]
    if "</html>" not in text or "function hideSearchAc" not in text:
        raise SystemExit(f"truncated {name}")
    if "placeMenusForDisplay" not in text:
        raise SystemExit(f"placeMenusForDisplay missing in {name}")
    return text


def main():
    for name in ("build-ds-catalog-html.sh", "build-kontakt-catalog-html.sh"):
        shutil.copy2(KIRO / name, WS / name)
        print("copied", name)
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
        raw = path.read_text(encoding="utf-8")
        out = refresh(raw, path.name)
        path.write_text(out, encoding="utf-8")
        print("refreshed", path.name, len(out))


if __name__ == "__main__":
    main()
