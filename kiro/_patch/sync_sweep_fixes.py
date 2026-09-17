#!/usr/bin/env python3
from pathlib import Path
import shutil
import re

KIRO = Path("/home/phnx/KIRO/.kiro/specs/kontakt-workspace-drive-dirty-fix/artifacts")
WS = Path("/home/phnx/kiro-kontakt-patch/kiro/specs/kontakt-workspace-drive-dirty-fix/artifacts")
PUB = Path("/home/phnx/kiro-kontakt-patch/public/catalogs")

ds = (KIRO / "build-ds-catalog-html.sh").read_text(encoding="utf-8")

def extract(src, start, end_marker, end_from=None):
    a = src.find(start)
    if a < 0:
        raise SystemExit(f"missing start: {start[:60]}")
    b = src.find(end_marker, end_from if end_from is not None else a)
    if b < 0:
        raise SystemExit(f"missing end: {end_marker[:40]}")
    return src[a:b]

# CSS from DS builder: from body.display-sides{ through stripe-open rule
css_start = ds.find("  body.display-sides{max-width:none")
css_end = ds.find("</style></head><body>", css_start)
if css_start < 0 or css_end < 0:
    raise SystemExit("CSS block missing in DS builder")
NEW_CSS = ds[css_start:css_end]

js_start = ds.find("var DISPLAY_KEY='catalog-display-mode-")
# include SIDES_KEY that now sits before placeMenus — actually SIDES_KEY is BEFORE DISPLAY_KEY? 
# Check: SIDES_KEY is after ensureCatalogMain, DISPLAY_KEY is first.
# DISPLAY_KEY is at the start of the display-mode JS. SIDES_KEY is after ensureCatalogMain inside that block.
js_end = ds.find("\n</script>", js_start)
if js_start < 0 or js_end < 0:
    raise SystemExit("JS block missing")
NEW_JS = ds[js_start:js_end]
if "applySidesCols" not in NEW_JS or "placeMenusForDisplay" not in NEW_JS:
    raise SystemExit("display JS incomplete")

APPLY_OLD = "function applySplit(){\n  var el=chrome(),b=splitBtn();"
APPLY_NEW = "function applySplit(){\n  if(document.body.classList.contains('display-sides'))return;\n  var el=chrome(),b=splitBtn();"

COMP_KW_OLD = "window.toggleKwFsCompanion=function(){\n  // K button: toggle KW companion\n  setKwFullscreen(!kwFsWanted);\n};"
COMP_KW_OLD2 = "window.toggleKwFsCompanion=function(){setKwFullscreen(!kwFsWanted);};"
COMP_KW_NEW = (
    "window.toggleKwFsCompanion=function(){\n"
    "  if(typeof displayIsDesktop==='function'&&displayIsDesktop()&&typeof setDisplayMode==='function'){\n"
    "    setDisplayMode(document.body.classList.contains('display-sides')?'fs':'sides');\n"
    "    return;\n"
    "  }\n"
    "  setKwFullscreen(!kwFsWanted);\n"
    "};"
)

PIN_OLD = (
    "window.toggleDualFsPin=function(){\n"
    "  savePin(!dualPinned);\n"
    "  syncSepPin();\n"
    "};"
)
PIN_OLD2 = "window.toggleDualFsPin=function(){savePin(!dualPinned);syncSepPin();};"
PIN_NEW = (
    "window.toggleDualFsPin=function(){\n"
    "  if(document.body.classList.contains('display-sides')){\n"
    "    sidesPinned=!sidesPinned;\n"
    "    try{localStorage.setItem(SIDES_KEY+'-pin',sidesPinned?'1':'0');}catch(err){}\n"
    "    syncSidesPin();\n"
    "    return;\n"
    "  }\n"
    "  savePin(!dualPinned);\n"
    "  syncSepPin();\n"
    "};"
)

COMP_AC_MARK = "window.toggleAcFsCompanion=function(){\n  var wantFs="
COMP_AC_NEW_PREFIX = (
    "window.toggleAcFsCompanion=function(){\n"
    "  if(typeof displayIsDesktop==='function'&&displayIsDesktop()&&typeof setDisplayMode==='function'){\n"
    "    setDisplayMode(document.body.classList.contains('display-sides')?'fs':'sides');\n"
    "    return;\n"
    "  }\n"
    "  var wantFs="
)


def patch_html(text, name):
    # CSS: replace from first body.display-sides{ through just before </style>
    old_css_a = text.find("  body.display-sides{max-width:none")
    if old_css_a < 0:
        old_css_a = text.find(" body.display-sides{max-width:none")
    style_end = text.find("</style></head><body>")
    if old_css_a < 0 or style_end < 0:
        raise SystemExit(f"display-sides CSS missing in {name}")
    text = text[:old_css_a] + NEW_CSS + text[style_end:]

    if APPLY_OLD in text:
        text = text.replace(APPLY_OLD, APPLY_NEW, 1)
    if PIN_OLD in text:
        text = text.replace(PIN_OLD, PIN_NEW, 1)
    elif PIN_OLD2 in text:
        text = text.replace(PIN_OLD2, PIN_NEW, 1)

    if COMP_KW_OLD in text:
        text = text.replace(COMP_KW_OLD, COMP_KW_NEW, 1)
    elif COMP_KW_OLD2 in text:
        text = text.replace(COMP_KW_OLD2, COMP_KW_NEW, 1)
    elif "setDisplayMode(document.body.classList.contains('display-sides')?'fs':'sides')" not in text:
        # HTML may already have a different one-liner after previous patches
        text = text.replace(
            "window.toggleKwFsCompanion=function(){\n  setKwFullscreen(!kwFsWanted);\n};",
            COMP_KW_NEW,
            1,
        )

    if COMP_AC_MARK in text and "display-sides')?'fs':'sides'" not in text[text.find("window.toggleAcFsCompanion"):text.find("window.toggleAcFsCompanion")+400]:
        text = text.replace(COMP_AC_MARK, COMP_AC_NEW_PREFIX, 1)

    mark = "var DISPLAY_KEY='catalog-display-mode-"
    a = text.find(mark)
    b = text.find("\n</script>", a)
    if a < 0 or b < 0:
        raise SystemExit(f"DISPLAY_KEY missing in {name}")
    text = text[:a] + NEW_JS + text[b:]

    if "</html>" not in text or "function hideSearchAc" not in text:
        raise SystemExit(f"truncated {name}")
    if "applySidesCols" not in text:
        raise SystemExit(f"applySidesCols missing in {name}")
    if "var(--sides-lw" not in text:
        raise SystemExit(f"sides CSS vars missing in {name}")
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
        out = patch_html(raw, path.name)
        path.write_text(out, encoding="utf-8")
        print("synced", path.name, len(out))


if __name__ == "__main__":
    main()
