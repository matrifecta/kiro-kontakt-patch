#!/usr/bin/env python3
"""Remove Shade as a data mode. Do not touch Sides polish (index dock, kw fill, bindCatalogTop)."""
from pathlib import Path
import shutil

KIRO = Path("/home/phnx/KIRO/.kiro/specs/kontakt-workspace-drive-dirty-fix/artifacts")
WS = Path("/home/phnx/kiro-kontakt-patch/kiro/specs/kontakt-workspace-drive-dirty-fix/artifacts")
PUB = Path("/home/phnx/kiro-kontakt-patch/public/catalogs")

INGEST = (
    "http://127.0.0.1:7529/ingest/1cf46354-1d61-4c80-bd72-a340f1db1b51"
)
HDR = (
    "{method:'POST',headers:{'Content-Type':'application/json',"
    "'X-Debug-Session-Id':'f491c2'},body:JSON.stringify("
)
SNAP = (
    "coerced:typeof mode!=='undefined'?mode:null,"
    "currentMode:typeof currentMode!=='undefined'?currentMode:'',"
    "searchMode:document.body.classList.contains('search-mode'),"
    "display:typeof currentDisplay!=='undefined'?currentDisplay:'',"
    "fwH:function(){var el=document.getElementById('filterWrap');"
    "if(!el)return null;return Math.round(el.getBoundingClientRect().height);}(),"
    "sepStyle:function(){var el=document.getElementById('dualFsSep');"
    "return el?(el.getAttribute('style')||''):null;}()"
)


def log_fetch(location, message, hid):
    payload = (
        "{sessionId:'f491c2',location:'" + location + "',message:'" + message
        + "',data:{" + SNAP + "},timestamp:Date.now(),runId:'shade-rm',"
        "hypothesisId:'" + hid + "'}"
    )
    return (
        "// #region agent log\n"
        "fetch('" + INGEST + "'," + HDR + payload + ")}).catch(function(){});\n"
        "// #endregion\n"
    )


SETMODE_LOG = log_fetch("setMode", "shade-rm-setMode", "H1")
EXIT_LOG = log_fetch("exitSearchUi", "shade-rm-exitSearchUi", "H1")
LEAVE_LOG = log_fetch("applySidesCols", "shade-rm-leaveSides", "H5")
INIT_LOG = log_fetch("display-init", "shade-rm-init-search", "H4")
DISP_LOG = log_fetch("setDisplayMode", "shade-rm-display", "H2")

SIDES_CLEAN = (
    "    ['searchSplit','dualFsSep'].forEach(function(id){"
    "var el=document.getElementById(id);if(el)el.removeAttribute('style');});\n"
)

INIT_CALL = "  if(typeof window.setMode==='function')window.setMode('search');\n"


def apply_once(text, old, new):
    if old not in text:
        return text, False
    if old == new:
        return text, False
    return text.replace(old, new), True


def patch(text, name):
    n = 0

    for old, new in (
        ("var currentMode='shade';", "var currentMode='search';"),
        (" var currentMode='shade';", " var currentMode='search';"),
        (
            "if(mode==='hide')mode='shade';",
            "if(mode==='hide'||mode==='shade')mode='search';",
        ),
        (
            "if(currentMode==='hide')currentMode='shade';",
            "if(currentMode==='hide'||currentMode==='shade')currentMode='search';",
        ),
    ):
        text, hit = apply_once(text, old, new)
        n += int(hit)

    css_old = (
        " .mode-switch{display:flex;flex-wrap:wrap;gap:6px;margin-bottom:8px;max-width:100%}\n"
        " .mode-btn{"
    )
    css_new = (
        " .mode-switch{display:flex;flex-wrap:wrap;gap:6px;margin-bottom:8px;max-width:100%}\n"
        ' .mode-btn[data-mode="shade"]{display:none!important}\n'
        " .mode-btn{"
    )
    if 'mode-btn[data-mode="shade"]{display:none!important}' not in text:
        text, hit = apply_once(text, css_old, css_new)
        n += int(hit)

    # exitSearchUi: drop setMode('shade') then instrument
    for old in (
        "window.exitSearchUi=function(){\n"
        "closeSearchExtras();\n"
        "if(searchInput)searchInput.blur();\n"
        "if(currentMode==='search')window.setMode('shade');\n"
        "};",
        " window.exitSearchUi=function(){\n"
        "   closeSearchExtras();\n"
        "   if(searchInput)searchInput.blur();\n"
        "   if(currentMode==='search')window.setMode('shade');\n"
        " };",
    ):
        if "if(currentMode==='search')window.setMode('shade')" in old and old in text:
            if old.startswith(" "):
                new = (
                    " window.exitSearchUi=function(){\n"
                    + EXIT_LOG
                    + "   closeSearchExtras();\n"
                    "   if(searchInput)searchInput.blur();\n"
                    " };"
                )
            else:
                new = (
                    "window.exitSearchUi=function(){\n"
                    + EXIT_LOG
                    + "closeSearchExtras();\n"
                    "if(searchInput)searchInput.blur();\n"
                    "};"
                )
            text, hit = apply_once(text, old, new)
            n += int(hit)

    if "shade-rm-exitSearchUi" not in text:
        for old in (
            "window.exitSearchUi=function(){\n"
            "closeSearchExtras();\n"
            "if(searchInput)searchInput.blur();\n"
            "};",
            " window.exitSearchUi=function(){\n"
            "   closeSearchExtras();\n"
            "   if(searchInput)searchInput.blur();\n"
            " };",
        ):
            if old in text:
                if old.startswith(" "):
                    new = (
                        " window.exitSearchUi=function(){\n"
                        + EXIT_LOG
                        + "   closeSearchExtras();\n"
                        "   if(searchInput)searchInput.blur();\n"
                        " };"
                    )
                else:
                    new = (
                        "window.exitSearchUi=function(){\n"
                        + EXIT_LOG
                        + "closeSearchExtras();\n"
                        "if(searchInput)searchInput.blur();\n"
                        "};"
                    )
                text, hit = apply_once(text, old, new)
                n += int(hit)
                break

    leave_old = (
        "  if(!document.body.classList.contains('display-sides')){\n"
        "    document.body.style.removeProperty('--sides-lw');\n"
        "    document.body.style.removeProperty('--sides-rw');\n"
        "    return;\n"
        "  }"
    )
    leave_mid = (
        "  if(!document.body.classList.contains('display-sides')){\n"
        "    document.body.style.removeProperty('--sides-lw');\n"
        "    document.body.style.removeProperty('--sides-rw');\n"
        + SIDES_CLEAN
        + "    return;\n"
        "  }"
    )
    leave_new = (
        "  if(!document.body.classList.contains('display-sides')){\n"
        "    document.body.style.removeProperty('--sides-lw');\n"
        "    document.body.style.removeProperty('--sides-rw');\n"
        + SIDES_CLEAN
        + LEAVE_LOG
        + "    return;\n"
        "  }"
    )
    if "shade-rm-leaveSides" not in text:
        if leave_old in text:
            text, hit = apply_once(text, leave_old, leave_new)
            n += int(hit)
        elif leave_mid in text:
            text, hit = apply_once(text, leave_mid, leave_new)
            n += int(hit)

    if "shade-rm-setMode" not in text:
        marker = (
            "body:JSON.stringify({sessionId:'f491c2',runId:'fs-nav',hypothesisId:'N2',"
            "location:'setMode',message:'setMode-nav'"
        )
        idx = text.find(marker)
        if idx >= 0:
            end = text.find("// #endregion", idx)
            if end >= 0:
                insert_at = end + len("// #endregion\n")
                text = text[:insert_at] + SETMODE_LOG + text[insert_at:]
                n += 1

    if "shade-rm-init-search" not in text:
        old = (
            "  setDisplayMode(m);\n"
            "  window.addEventListener('resize',function(){"
        )
        new = (
            "  setDisplayMode(m);\n"
            + INIT_CALL
            + INIT_LOG
            + "  window.addEventListener('resize',function(){"
        )
        text, hit = apply_once(text, old, new)
        n += int(hit)

    if "shade-rm-display" not in text:
        marker = "message:'display-mode'"
        idx = text.find(marker)
        if idx >= 0:
            end = text.find("// #endregion", idx)
            if end >= 0:
                insert_at = end + len("// #endregion\n")
                text = text[:insert_at] + DISP_LOG + text[insert_at:]
                n += 1

    if "</style></head><body class=\"search-mode\">" not in text:
        text, hit = apply_once(
            text,
            "</style></head><body>",
            '</style></head><body class="search-mode">',
        )
        n += int(hit)

    # First-paint Search active on the visible Search pill (Shade stays hidden)
    text, hit = apply_once(
        text,
        '<button class="mode-btn active" data-mode="shade" onclick="setMode(this.dataset.mode)">Shade</button><button class="mode-btn" data-mode="search" onclick="setMode(this.dataset.mode)">Search</button>',
        '<button class="mode-btn" data-mode="shade" onclick="setMode(this.dataset.mode)">Shade</button><button class="mode-btn active" data-mode="search" onclick="setMode(this.dataset.mode)">Search</button>',
    )
    n += int(hit)

    print(f"  {name}: {n} replacements")
    return text


def assert_html(text, name):
    if not text.rstrip().endswith("</html>") and "</html>" not in text[-80:]:
        raise SystemExit(f"{name} missing </html>")
    if "function hideSearchAc" not in text:
        raise SystemExit(f"{name} missing function hideSearchAc")
    if "bindCatalogTop" not in text:
        raise SystemExit(f"{name} lost bindCatalogTop (Sides polish)")
    if "syncIndexDock" not in text:
        raise SystemExit(f"{name} lost syncIndexDock (Sides polish)")
    if "body.display-sides #filterWrap{height:100%!important" not in text and (
        "body.display-sides #filterWrap{height:100%!important" not in text.replace(" ", "")
    ):
        if "height:100%!important;max-height:none!important;align-self:stretch" not in text:
            raise SystemExit(f"{name} lost Keywords fill CSS")
    if "if(mode==='hide'||mode==='shade')mode='search'" not in text:
        raise SystemExit(f"{name} missing shade coerce")
    if "if(currentMode==='search')window.setMode('shade')" in text:
        raise SystemExit(f"{name} still restores shade in exitSearchUi")
    if "var currentMode='shade'" in text or " var currentMode='shade'" in text:
        raise SystemExit(f"{name} still defaults currentMode shade")
    if 'mode-btn[data-mode="shade"]{display:none!important}' not in text:
        raise SystemExit(f"{name} missing Shade button hide CSS")
    if "window.setMode('search')" not in text:
        raise SystemExit(f"{name} missing init setMode('search')")
    if "shade-rm-setMode" not in text or "shade-rm-exitSearchUi" not in text:
        raise SystemExit(f"{name} missing shade-rm logs")


def assert_builder(text, name):
    if "if(mode==='hide'||mode==='shade')mode='search'" not in text:
        raise SystemExit(f"{name} missing shade coerce")
    if "if(currentMode==='search')window.setMode('shade')" in text:
        raise SystemExit(f"{name} still restores shade in exitSearchUi")
    if "var currentMode='shade'" in text:
        raise SystemExit(f"{name} still defaults currentMode shade")
    if 'mode-btn[data-mode="shade"]{display:none!important}' not in text:
        raise SystemExit(f"{name} missing Shade button hide CSS")
    if "window.setMode('search')" not in text:
        raise SystemExit(f"{name} missing init setMode('search')")
    if "removeAttribute('style')" not in text:
        raise SystemExit(f"{name} missing applySidesCols style cleanup")
    if "bindCatalogTop" not in text or "syncIndexDock" not in text:
        raise SystemExit(f"{name} lost Sides polish")
    if "height:100%!important;max-height:none!important;align-self:stretch" not in text:
        raise SystemExit(f"{name} lost Keywords fill CSS")


def main():
    builders = (
        "build-ds-catalog-html.sh",
        "build-kontakt-catalog-html.sh",
    )
    for name in builders:
        src = KIRO / name
        raw = src.read_text(encoding="utf-8")
        out = patch(raw, f"KIRO/{name}")
        assert_builder(out, f"KIRO/{name}")
        src.write_text(out, encoding="utf-8")
        WS.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, WS / name)
        print("copied", name)

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
        if not path.exists():
            print("skip missing", path)
            continue
        raw = path.read_text(encoding="utf-8")
        out = patch(raw, str(path))
        assert_html(out, path.name)
        path.write_text(out, encoding="utf-8")
        tail = out.rstrip()[-20:]
        print("wrote", path.name, len(out), "tail", repr(tail))


if __name__ == "__main__":
    main()
