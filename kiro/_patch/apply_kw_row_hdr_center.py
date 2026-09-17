#!/usr/bin/env python3
"""Keywords row: Tap to add + Clear then groups. Center header button cluster.

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

CSS_NEW = (
    ".catalog-header{display:grid!important;grid-template-columns:minmax(0,1fr) auto minmax(0,1fr);align-items:center;column-gap:.5rem;row-gap:.35rem;min-width:0;position:relative}\n"
    ".catalog-header h1{grid-column:1;grid-row:1;justify-self:start;z-index:1;min-width:0;max-width:100%;margin:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}\n"
    ".hdr-cluster{grid-column:2;grid-row:1;justify-self:center;display:flex;align-items:center;gap:.5rem;flex-wrap:nowrap;min-width:0;max-width:100%;position:relative;z-index:2}\n"
    ".catalog-header::after{content:'';grid-column:3;grid-row:1}\n"
    ".hdr-layout-btns{display:flex;align-items:center;gap:4px;flex:0 1 auto;margin-left:0;min-width:0}\n"
    ".catalog-header #clearMissBtn,.hdr-cluster>#clearMissBtn{flex:0 0 auto;display:inline-flex;align-items:center;justify-content:center;min-height:2.25rem;position:relative;z-index:2}\n"
    "body.display-sides .catalog-header #clearMissBtn,body.display-sides.display-middle .catalog-header #clearMissBtn{display:inline-flex!important}\n"
    ".hdr-end{margin-left:0;display:flex;align-items:center;gap:.5rem;min-width:0;flex:0 0 auto}\n"
    ".catalog-header .hdr-menu-btns,.hdr-cluster .hdr-menu-btns{margin-left:0;flex:0 0 auto}\n"
    ".hdr-layout-btns .layout-presets{width:auto;max-width:none;padding:0;flex-wrap:nowrap;gap:4px}\n"
    ".hdr-layout-btns .layout-edit-btn,.hdr-layout-btns .layout-presets-btn,.hdr-layout-btns .ui-scale-step,.hdr-layout-btns .ui-scale-readout,.catalog-header #clearMissBtn{min-height:2.25rem}\n"
    "#hdrSearchBtn{font-weight:600;font-size:.875rem}\n"
    ".filter-panel>.mode-switch{display:none!important}\n"
    "@media(orientation:portrait){.catalog-header{grid-template-rows:auto auto}.catalog-header h1{grid-column:1/-1;grid-row:1;max-width:100%}.hdr-cluster{grid-column:2;grid-row:2;flex-wrap:wrap;justify-content:center}.catalog-header::after{grid-column:3;grid-row:2}}\n"
)

CAT_OLD = (
    ".cat-switch{display:flex;flex-wrap:wrap;align-content:flex-start;gap:clamp(4px,0.8vw,8px);margin-bottom:clamp(6px,1.2vw,10px);width:100%;max-width:100%;min-width:0;height:auto;overflow:visible;box-sizing:border-box}"
)
CAT_NEW = (
    ".cat-switch{display:flex;flex-wrap:wrap;align-items:center;align-content:flex-start;gap:clamp(4px,0.8vw,8px);margin-bottom:clamp(6px,1.2vw,10px);width:100%;max-width:100%;min-width:0;height:auto;overflow:visible;box-sizing:border-box}"
    ".cat-switch-lead{display:inline-flex;flex-wrap:nowrap;align-items:center;gap:clamp(4px,0.8vw,8px);flex:0 0 auto}"
    ".cat-switch .tap-add-btn,.cat-switch .mode-btn.clear-all{flex:0 0 auto;min-height:2.25rem;align-self:center}"
)

KW_OLD = (
    '<div class="mode-switch"><button class="mode-btn" data-mode="pick" onclick="setMode(this.dataset.mode)">Pick</button>'
    '<button class="mode-btn active" data-mode="search" onclick="setMode(this.dataset.mode)">Search</button>'
    '<button type="button" class="tap-add-btn" id="tapAddBtnPanel" aria-pressed="false" onclick="toggleTapToAdd()">Tap to add</button>'
    '<button type="button" class="mode-btn clear-all" onclick="clearAllFilters()">Clear</button></div>'
    '<div class="cat-switch" id="catSwitch">'
)
KW_NEW = (
    '<div class="mode-switch"><button class="mode-btn" data-mode="pick" onclick="setMode(this.dataset.mode)">Pick</button>'
    '<button class="mode-btn active" data-mode="search" onclick="setMode(this.dataset.mode)">Search</button></div>'
    '<div class="cat-switch" id="catSwitch">'
    '<span class="cat-switch-lead">'
    '<button type="button" class="tap-add-btn" id="tapAddBtnPanel" aria-pressed="false" onclick="toggleTapToAdd()">Tap to add</button>'
    '<button type="button" class="mode-btn clear-all" onclick="clearAllFilters()">Clear</button>'
    "</span>"
)

HDR_OPEN_OLD = '</h1><div class="hdr-layout-btns" id="hdrLayoutBtns"'
HDR_OPEN_NEW = '</h1><div class="hdr-cluster" id="hdrCluster"><div class="hdr-layout-btns" id="hdrLayoutBtns"'

HDR_CLOSE_OLD = "</optgroup></select></div>"
HDR_CLOSE_NEW = "</optgroup></select></div></div>"

JS_OLD = (
    "  var end=document.getElementById('hdrEnd');\n"
    "  if(!end&&hdr){\n"
    "    end=document.createElement('div');\n"
    "    end.id='hdrEnd';end.className='hdr-end';\n"
    "    var menu=document.getElementById('hdrMenuBtns');\n"
    "    var sw=document.getElementById('displaySwitch');\n"
    "    var th=document.getElementById('themePicker');\n"
    "    if(menu){hdr.insertBefore(end,menu);end.appendChild(menu);if(sw)end.appendChild(sw);if(th)end.appendChild(th);}\n"
    "  }\n"
    "  var miss=document.getElementById('clearMissBtn');\n"
    "  if(miss&&hdr){\n"
    "    var before=end||document.getElementById('hdrMenuBtns');\n"
    "    if(before){if(miss.parentElement!==hdr||miss.nextElementSibling!==before)hdr.insertBefore(miss,before);}\n"
    "    else if(miss.parentElement!==hdr)hdr.appendChild(miss);\n"
    "  }\n"
)

JS_NEW = (
    "  var cluster=document.getElementById('hdrCluster');\n"
    "  if(!cluster&&hdr){\n"
    "    cluster=document.createElement('div');\n"
    "    cluster.id='hdrCluster';cluster.className='hdr-cluster';\n"
    "    var after=hdr.querySelector('h1');\n"
    "    if(after&&after.nextSibling)hdr.insertBefore(cluster,after.nextSibling);\n"
    "    else hdr.appendChild(cluster);\n"
    "  }\n"
    "  if(cluster&&host&&host.parentElement!==cluster){\n"
    "    if(cluster.firstChild)cluster.insertBefore(host,cluster.firstChild);else cluster.appendChild(host);\n"
    "  }\n"
    "  var wrap=cluster||hdr;\n"
    "  var end=document.getElementById('hdrEnd');\n"
    "  if(!end&&wrap){\n"
    "    end=document.createElement('div');\n"
    "    end.id='hdrEnd';end.className='hdr-end';\n"
    "    var menu=document.getElementById('hdrMenuBtns');\n"
    "    var sw=document.getElementById('displaySwitch');\n"
    "    var th=document.getElementById('themePicker');\n"
    "    if(menu){wrap.insertBefore(end,menu);end.appendChild(menu);if(sw)end.appendChild(sw);if(th)end.appendChild(th);}\n"
    "  }\n"
    "  var miss=document.getElementById('clearMissBtn');\n"
    "  if(miss&&wrap){\n"
    "    var before=end||document.getElementById('hdrMenuBtns');\n"
    "    if(before){if(miss.parentElement!==wrap||miss.nextElementSibling!==before)wrap.insertBefore(miss,before);}\n"
    "    else if(miss.parentElement!==wrap)wrap.appendChild(miss);\n"
    "  }\n"
    "  var cs=document.getElementById('catSwitch');\n"
    "  var tap=document.getElementById('tapAddBtnPanel');\n"
    "  var clrBtn=document.querySelector('#filterPanel .mode-btn.clear-all,.cat-switch .mode-btn.clear-all,.mode-btn.clear-all');\n"
    "  if(cs&&tap&&clrBtn&&clrBtn.id!=='clearMissBtn'){\n"
    "    var lead=cs.querySelector('.cat-switch-lead');\n"
    "    if(!lead){lead=document.createElement('span');lead.className='cat-switch-lead';}\n"
    "    if(lead.parentElement!==cs||cs.firstElementChild!==lead)cs.insertBefore(lead,cs.firstChild);\n"
    "    if(tap.parentElement!==lead)lead.appendChild(tap);\n"
    "    if(clrBtn.parentElement!==lead)lead.appendChild(clrBtn);\n"
    "    if(tap.nextElementSibling!==clrBtn)lead.insertBefore(tap,clrBtn);\n"
    "  }\n"
)

SHADE_OLD = "  need+=(ms&&(ms.offsetHeight||ms.scrollHeight))||2.5*rem();\n"
SHADE_NEW = "  need+=(ms&&(ms.offsetHeight||ms.scrollHeight))||0;\n"


def patch(text, path):
    c00 = text.count("sessionId:'c00e3e'")
    f49 = text.count("sessionId:'f491c2'")
    regions = text.count("// #region agent log")

    text = sub(text, CSS_OLD, CSS_NEW, "hdr-css")
    if CAT_OLD in text:
        text = sub(text, CAT_OLD, CAT_NEW, "cat-css")
    else:
        text = sub(
            text,
            ".cat-switch .tap-add-btn,.cat-switch .mode-btn.clear-all{flex:0 0 auto}",
            ".cat-switch .tap-add-btn,.cat-switch .mode-btn.clear-all{flex:0 0 auto;min-height:2.25rem;align-self:center}",
            "cat-lead-size",
        )
    text = sub(text, KW_OLD, KW_NEW, "kw-html")
    text = sub(text, HDR_OPEN_OLD, HDR_OPEN_NEW, "hdr-open")
    text = sub(text, HDR_CLOSE_OLD, HDR_CLOSE_NEW, "hdr-close")
    text = sub(text, JS_OLD, JS_NEW, "ensure-js")
    text = sub(text, SHADE_OLD, SHADE_NEW, "shade-min")

    if 'id="hdrCluster"' not in text:
        raise SystemExit(f"{path.name}: missing hdrCluster")
    if "grid-template-columns:minmax(0,1fr) auto minmax(0,1fr)" not in text:
        raise SystemExit(f"{path.name}: missing centered header grid")
    if 'class="cat-switch-lead"' not in text:
        raise SystemExit(f"{path.name}: missing cat-switch-lead")
    if 'id="tapAddBtnPanel"' not in text:
        raise SystemExit(f"{path.name}: missing tapAddBtnPanel")
    if "mode-btn clear-all" not in text:
        raise SystemExit(f"{path.name}: missing Clear")
    if 'id="filterKwTools"><button type="button" class="clear-miss-btn"' in text:
        raise SystemExit(f"{path.name}: Clear on miss back in filterKwTools")
    if text.count('id="clearMissBtn"') != 1:
        raise SystemExit(f"{path.name}: expected 1 clearMissBtn, got {text.count('id=\"clearMissBtn\"')}")
    lead_at = text.find('class="cat-switch-lead"')
    tap_at = text.find('id="tapAddBtnPanel"', lead_at)
    clr_at = text.find("mode-btn clear-all", lead_at)
    cat_at = text.find('class="cat-btn', lead_at)
    if not (lead_at < tap_at < clr_at < cat_at):
        raise SystemExit(f"{path.name}: Keywords DOM order not Tap/Clear/groups")
    if "var cluster=document.getElementById('hdrCluster');" not in text:
        raise SystemExit(f"{path.name}: missing cluster ensure JS")
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
