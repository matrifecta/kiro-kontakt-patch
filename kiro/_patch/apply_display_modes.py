#!/usr/bin/env python3
from pathlib import Path
import shutil

KIRO = Path("/home/phnx/KIRO/.kiro/specs/kontakt-workspace-drive-dirty-fix/artifacts")
WS = Path("/home/phnx/kiro-kontakt-patch/kiro/specs/kontakt-workspace-drive-dirty-fix/artifacts")
PUB = Path("/home/phnx/kiro-kontakt-patch/public/catalogs")

CSS = """ .display-switch{display:flex;align-items:center;gap:4px;flex:0 0 auto;margin-left:.5rem}
 .display-btn{box-sizing:border-box;min-height:2.25rem;padding:0 .65rem;border:1px solid var(--border);border-radius:6px;background:var(--bg-card);color:var(--text-muted);font:inherit;font-size:.8125rem;cursor:pointer;touch-action:manipulation}
 .display-btn.is-active{background:var(--accent-instrument-bg);color:var(--accent-instrument);border-color:var(--accent-instrument);font-weight:600}
 @media(max-width:899px){.display-btn.display-desktop-only{display:none!important}}
 .catalog-main{width:100%;max-width:100%;min-width:0}
 @media(min-width:900px){
  body.display-sides{max-width:none;width:100%;margin:0;padding:0;height:100dvh;overflow:hidden;display:grid;grid-template-columns:minmax(15rem,22vw) minmax(0,1fr) minmax(16rem,26vw);grid-template-rows:auto minmax(0,1fr)}
  body.display-sides .catalog-header{grid-column:1/-1;grid-row:1;padding:.4rem .75rem;margin:0;border-bottom:1px solid var(--border);background:var(--bg-surface)}
  body.display-sides .catalog-header+p,body.display-sides .catalog-header+p+p{display:none}
  body.display-sides #searchChrome{grid-column:1;grid-row:2;height:100%;min-height:0;max-width:none;width:100%;overflow:hidden;display:flex!important;flex-direction:column;position:relative!important;top:auto!important;z-index:5;background:var(--bg-surface);border-right:1px solid var(--border);padding:0;align-items:stretch}
  body.display-sides #searchCol{flex:1;min-height:0;display:flex!important;flex-direction:column;overflow:hidden;width:100%;max-width:none}
  body.display-sides #searchCol .search-strip-anchor{flex:1;min-height:0;display:flex;flex-direction:column;overflow:hidden}
  body.display-sides #filterWrap{grid-column:3;grid-row:2;height:100%;min-height:0;overflow:hidden;position:relative!important;inset:auto!important;z-index:5!important;width:100%!important;max-width:none!important;border-left:1px solid var(--border);border-bottom:0;padding:0;display:flex!important;flex-direction:column!important}
  body.display-sides #catalogMain{grid-column:2;grid-row:2;min-width:0;min-height:0;overflow-x:hidden;overflow-y:auto;-webkit-overflow-scrolling:touch;overscroll-behavior:contain;touch-action:pan-y;padding:.75rem 1rem 2rem}
  body.display-sides > p,body.display-sides > a.top,body.display-sides #searchSplit,body.display-sides #dualFsSep,body.display-sides #searchHeight,body.display-sides .search-height,body.display-sides #kwShadeHeight{display:none!important}
  body.display-sides #filterWrap.open .filter-panel,body.display-sides #filterWrap.kw-shade-height-set.open .filter-panel{position:static!important;max-height:none!important;flex:1 1 auto;min-height:0;overflow-y:auto!important;-webkit-overflow-scrolling:touch;overscroll-behavior:contain;touch-action:pan-y;width:auto!important;box-shadow:none;border:0}
  body.display-sides #acShell,body.display-sides #acShell.open,body.display-sides #acList,body.display-sides #acList.open{position:relative!important;inset:auto!important;width:auto!important;height:auto!important;max-height:none!important;flex:1 1 auto;min-height:0;overflow-y:auto!important;-webkit-overflow-scrolling:touch;overscroll-behavior:contain;touch-action:pan-y;box-shadow:none;border:0}
  body.display-sides.kw-fs-open #filterWrap,body.display-sides.ac-fs-open #acShell.ac-fs{position:relative!important;inset:auto!important;width:auto!important;height:auto!important}
 }
"""

SWITCH = (
    '<div class="display-switch" id="displaySwitch" role="tablist" aria-label="Display layout">'
    '<button type="button" class="display-btn is-active" data-display="upper" onclick="event.preventDefault();event.stopPropagation();setDisplayMode(\'upper\')">Upper</button>'
    '<button type="button" class="display-btn display-desktop-only" data-display="sides" onclick="event.preventDefault();event.stopPropagation();setDisplayMode(\'sides\')">Sides</button>'
    '<button type="button" class="display-btn" data-display="fs" onclick="event.preventDefault();event.stopPropagation();setDisplayMode(\'fs\')">Full</button>'
    "</div>"
)

JS_MARK = "var DISPLAY_KEY='catalog-display-mode-'"
JS = Path("/tmp/display-mode.js")  # filled below from DS builder extract... we'll embed

# Pull JS from DS builder (already patched)
ds = (KIRO / "build-ds-catalog-html.sh").read_text(encoding="utf-8")
js_start = ds.find("var DISPLAY_KEY='catalog-display-mode-")
js_end = ds.find("\n</script>", js_start)
if js_start < 0 or js_end < 0:
    raise SystemExit("JS block missing in DS builder")
JS_BLOCK = ds[js_start:js_end]


def patch(text, name):
    if "body.display-sides{" not in text:
        if "</style></head><body>" not in text:
            raise SystemExit(f"no style end in {name}")
        text = text.replace("</style></head><body>", CSS + "</style></head><body>", 1)
    if 'id="displaySwitch"' not in text:
        for title in (
            "DecentSampler Library Catalog",
            "Kontakt Library Catalog",
        ):
            old = f'<h1 id="top">{title}</h1><select id="themePicker"'
            new = f'<h1 id="top">{title}</h1>{SWITCH}<select id="themePicker"'
            if old in text:
                text = text.replace(old, new, 1)
                break
        else:
            raise SystemExit(f"header missing in {name}")
    old_c1 = "  var combined=document.body.classList.contains('search-mode')&&document.body.classList.contains('kw-open')&&!document.body.classList.contains('search-chrome-collapsed')&&!document.body.classList.contains('kw-fs-open');\n  if(combined){"
    new_c1 = "  var sides=document.body.classList.contains('display-sides');\n  var combined=sides||(document.body.classList.contains('search-mode')&&document.body.classList.contains('kw-open')&&!document.body.classList.contains('search-chrome-collapsed')&&!document.body.classList.contains('kw-fs-open')&&!document.body.classList.contains('display-fs'));\n  if(combined){"
    if old_c1 in text:
        text = text.replace(old_c1, new_c1, 1)
    old_c2 = "  var combined=document.body.classList.contains('search-mode')&&document.body.classList.contains('kw-open')&&!document.body.classList.contains('search-chrome-collapsed')&&!document.body.classList.contains('kw-fs-open')&&!acFullscreen();"
    new_c2 = "  var combined=document.body.classList.contains('display-sides')||(document.body.classList.contains('search-mode')&&document.body.classList.contains('kw-open')&&!document.body.classList.contains('search-chrome-collapsed')&&!document.body.classList.contains('kw-fs-open')&&!document.body.classList.contains('display-fs')&&!acFullscreen());"
    if old_c2 in text:
        text = text.replace(old_c2, new_c2, 1)
    if JS_MARK not in text:
        if "})();\n\n</script>" in text:
            text = text.replace("})();\n\n</script>", "})();\n\n" + JS_BLOCK + "\n</script>", 1)
        elif "})();\n</script>" in text:
            text = text.replace("})();\n</script>", "})();\n\n" + JS_BLOCK + "\n</script>", 1)
        else:
            raise SystemExit(f"script end missing in {name}")
    if "</html>" not in text or "function hideSearchAc" not in text:
        raise SystemExit(f"truncated {name}")
    if "setDisplayMode" not in text or "display-sides" not in text:
        raise SystemExit(f"display mode missing in {name}")
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
        out = patch(raw, path.name)
        path.write_text(out, encoding="utf-8")
        print("patched", path.name, len(out))


if __name__ == "__main__":
    main()
