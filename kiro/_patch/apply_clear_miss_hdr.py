#!/usr/bin/env python3
"""Move Clear on miss into the top toolbar (between Layouts and Search) and
relabel the header Search control from a magnifying glass to S.

Syncs the six catalog HTML/builder files. Does not strip existing agent logs.
"""
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

CLEAR_BTN = (
    '<button type="button" class="clear-miss-btn" id="clearMissBtn" aria-pressed="false" '
    'title="When leaving the image gallery on a library outside the current Search hits, clear Search." '
    'onclick="event.preventDefault();event.stopPropagation();toggleClearOnMiss()">Clear on miss</button>'
)


def sub(text, old, new, label, optional=False):
    n = text.count(old)
    if n == 1:
        return text.replace(old, new, 1)
    if n > 1:
        raise SystemExit(f"{label}: {n} matches")
    if new in text:
        print(f"  skip {label} (already)")
        return text
    if optional:
        print(f"  skip {label}")
        return text
    raise SystemExit(f"{label}: not found")


CSS_OLD = (
    ".catalog-header{display:grid!important;grid-template-columns:minmax(0,1fr) auto minmax(0,1fr);align-items:center;gap:.5rem}\n"
    ".catalog-header h1{grid-column:1;justify-self:start;margin:0}\n"
    ".hdr-layout-btns{grid-column:2;justify-self:center;display:flex;align-items:center;gap:4px;flex:0 0 auto;margin-left:0;min-width:0}\n"
    ".hdr-end{grid-column:3;justify-self:end;display:flex;align-items:center;gap:.5rem;min-width:0}\n"
    ".hdr-layout-btns .layout-presets{width:auto;max-width:none;padding:0;flex-wrap:nowrap;gap:4px}\n"
    ".hdr-layout-btns .layout-edit-btn,.hdr-layout-btns .layout-presets-btn,.hdr-layout-btns .ui-scale-step,.hdr-layout-btns .ui-scale-readout{min-height:2.25rem}\n"
)

CSS_GRID4 = (
    ".catalog-header{display:grid!important;grid-template-columns:minmax(0,1fr) auto auto minmax(0,1fr);align-items:center;gap:.5rem}\n"
    ".catalog-header h1{grid-column:1;justify-self:start;margin:0}\n"
    ".hdr-layout-btns{grid-column:2;justify-self:end;display:flex;align-items:center;gap:4px;flex:0 0 auto;margin-left:0;min-width:0}\n"
    ".catalog-header>#clearMissBtn{grid-column:3;justify-self:start;flex:0 0 auto;display:inline-flex;align-items:center;justify-content:center;min-height:2.25rem;position:relative;z-index:2}\n"
    "body.display-sides .catalog-header>#clearMissBtn,body.display-sides.display-middle .catalog-header>#clearMissBtn{display:inline-flex!important}\n"
    ".hdr-end{grid-column:4;justify-self:end;display:flex;align-items:center;gap:.5rem;min-width:0}\n"
    ".catalog-header>.hdr-menu-btns{grid-column:4;justify-self:end}\n"
    ".hdr-layout-btns .layout-presets{width:auto;max-width:none;padding:0;flex-wrap:nowrap;gap:4px}\n"
    ".hdr-layout-btns .layout-edit-btn,.hdr-layout-btns .layout-presets-btn,.hdr-layout-btns .ui-scale-step,.hdr-layout-btns .ui-scale-readout,.catalog-header>#clearMissBtn{min-height:2.25rem}\n"
    "#hdrSearchBtn{font-weight:600;font-size:.875rem}\n"
)

CSS_NEW = (
    ".catalog-header{display:flex!important;flex-wrap:nowrap;align-items:center;gap:.5rem;min-width:0}\n"
    ".catalog-header h1{flex:0 1 auto;min-width:0;max-width:min(32vw,22rem);margin:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}\n"
    ".hdr-layout-btns{display:flex;align-items:center;gap:4px;flex:0 1 auto;margin-left:0;min-width:0}\n"
    ".catalog-header>#clearMissBtn{flex:0 0 auto;display:inline-flex;align-items:center;justify-content:center;min-height:2.25rem;position:relative;z-index:2}\n"
    "body.display-sides .catalog-header>#clearMissBtn,body.display-sides.display-middle .catalog-header>#clearMissBtn{display:inline-flex!important}\n"
    ".hdr-end{margin-left:auto;display:flex;align-items:center;gap:.5rem;min-width:0;flex:0 0 auto}\n"
    ".catalog-header>.hdr-menu-btns{margin-left:auto;flex:0 0 auto}\n"
    ".hdr-layout-btns .layout-presets{width:auto;max-width:none;padding:0;flex-wrap:nowrap;gap:4px}\n"
    ".hdr-layout-btns .layout-edit-btn,.hdr-layout-btns .layout-presets-btn,.hdr-layout-btns .ui-scale-step,.hdr-layout-btns .ui-scale-readout,.catalog-header>#clearMissBtn{min-height:2.25rem}\n"
    "#hdrSearchBtn{font-weight:600;font-size:.875rem}\n"
    "@media(orientation:portrait){.catalog-header{flex-wrap:wrap;row-gap:.35rem}.catalog-header h1{flex:1 1 100%;max-width:100%}}\n"
)

HDR_OLD = (
    'id="hdrLayoutBtns" role="toolbar" aria-label="Layout controls"></div>'
    '<div class="hdr-menu-btns"'
)
HDR_NEW = (
    'id="hdrLayoutBtns" role="toolbar" aria-label="Layout controls"></div>'
    + CLEAR_BTN
    + '<div class="hdr-menu-btns"'
)

TOOLS_OLD = 'id="filterKwTools">' + CLEAR_BTN
TOOLS_NEW = 'id="filterKwTools">'

JS_OLD = (
    "    if(menu){hdr.insertBefore(end,menu);end.appendChild(menu);if(sw)end.appendChild(sw);if(th)end.appendChild(th);}\n"
    "  }\n"
    "  var edit=document.getElementById('layoutEditBtn');\n"
)
JS_NEW = (
    "    if(menu){hdr.insertBefore(end,menu);end.appendChild(menu);if(sw)end.appendChild(sw);if(th)end.appendChild(th);}\n"
    "  }\n"
    "  var miss=document.getElementById('clearMissBtn');\n"
    "  if(miss&&hdr){\n"
    "    var before=end||document.getElementById('hdrMenuBtns');\n"
    "    if(before){if(miss.parentElement!==hdr||miss.nextElementSibling!==before)hdr.insertBefore(miss,before);}\n"
    "    else if(miss.parentElement!==hdr)hdr.appendChild(miss);\n"
    "  }\n"
    "  var edit=document.getElementById('layoutEditBtn');\n"
)

SEARCH_OLD = 'toggleHdrSearch()">&#x1F50D;</button>'
SEARCH_NEW = 'toggleHdrSearch()">S</button>'


def patch(text, path):
    c00 = text.count("sessionId:'c00e3e'")
    f49 = text.count("sessionId:'f491c2'")
    regions = text.count("// #region agent log")

    if CSS_GRID4 in text:
        text = sub(text, CSS_GRID4, CSS_NEW, "hdr-css")
    else:
        text = sub(text, CSS_OLD, CSS_NEW, "hdr-css")
    text = sub(text, HDR_OLD, HDR_NEW, "hdr-html")
    text = sub(text, TOOLS_OLD, TOOLS_NEW, "kw-tools-html")
    text = sub(text, JS_OLD, JS_NEW, "ensure-js")
    text = sub(text, SEARCH_OLD, SEARCH_NEW, "search-s")

    if text.count('id="clearMissBtn"') != 1:
        raise SystemExit(f"{path.name}: expected 1 clearMissBtn, got {text.count('id=\"clearMissBtn\"')}")
    if CLEAR_BTN not in text:
        raise SystemExit(f"{path.name}: missing Clear on miss button")
    if 'id="filterKwTools">' + CLEAR_BTN in text:
        raise SystemExit(f"{path.name}: Clear on miss still in filterKwTools")
    if HDR_NEW not in text and (CLEAR_BTN + '<div class="hdr-menu-btns"') not in text:
        raise SystemExit(f"{path.name}: Clear on miss not between Layouts host and search cluster")
    if 'toggleHdrSearch()">S</button>' not in text:
        raise SystemExit(f"{path.name}: hdrSearchBtn is not S")
    if 'toggleHdrSearch()">&#x1F50D;</button>' in text:
        raise SystemExit(f"{path.name}: hdrSearchBtn still uses magnifying glass")
    if "var miss=document.getElementById('clearMissBtn');" not in text:
        raise SystemExit(f"{path.name}: missing ensureLayoutChromeBtns miss move")
    if text.count("sessionId:'f491c2'") < f49:
        raise SystemExit(f"{path.name}: lost f491c2 logs")
    if text.count("// #region agent log") < regions:
        raise SystemExit(f"{path.name}: lost agent log regions")
    if path.name == "DS-CATALOG.html":
        if "function dbgIndexAc" not in text:
            raise SystemExit(f"{path.name}: lost dbgIndexAc")
        if text.count("sessionId:'c00e3e'") < c00:
            raise SystemExit(f"{path.name}: lost c00e3e logs")
    elif c00 and text.count("sessionId:'c00e3e'") < c00:
        raise SystemExit(f"{path.name}: lost c00e3e logs")
    return text


def main():
    for path in FILES:
        if not path.exists():
            raise SystemExit(f"missing {path}")
        text = path.read_text(encoding="utf-8")
        new = patch(text, path)
        if new != text:
            path.write_text(new, encoding="utf-8")
            print(f"patched {path}")
        else:
            print(f"unchanged {path}")


if __name__ == "__main__":
    main()
