#!/usr/bin/env python3
"""Cap Upper AC/KW to the chrome box in px so they cannot hang past clip."""
from pathlib import Path
import shutil

KIRO = Path("/home/phnx/KIRO/.kiro/specs/kontakt-workspace-drive-dirty-fix/artifacts")
WS = Path("/home/phnx/kiro-kontakt-patch/kiro/specs/kontakt-workspace-drive-dirty-fix/artifacts")
PUB = Path("/home/phnx/kiro-kontakt-patch/public/catalogs")
INGEST = "http://127.0.0.1:7529/ingest/1cf46354-1d61-4c80-bd72-a340f1db1b51"

FN = (
    "function applyUpperContain(){\n"
    "  var sh=document.getElementById('acShell');\n"
    "  var kw=document.getElementById('kwbar');\n"
    "  var panel=document.getElementById('filterPanel')||document.querySelector('#filterWrap .filter-panel');\n"
    "  var ch=document.getElementById('searchChrome');\n"
    "  function clr(el){if(el)el.style.removeProperty('max-height');}\n"
    "  if(!document.body.classList.contains('display-upper')||!ch){clr(sh);clr(kw);clr(panel);return;}\n"
    "  var bottom=ch.getBoundingClientRect().bottom;\n"
    "  function cap(el){if(!el)return;el.style.maxHeight=Math.max(72,Math.round(bottom-el.getBoundingClientRect().top))+'px';}\n"
    "  cap(sh);cap(panel);cap(kw);\n"
    "  // #region agent log\n"
    "  fetch('" + INGEST + "',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'f491c2'},body:JSON.stringify({sessionId:'f491c2',runId:'layout-fix',hypothesisId:'H2',location:'applyUpperContain',message:'upper-contain',data:{chB:Math.round(bottom),shB:sh?Math.round(sh.getBoundingClientRect().bottom):null,kwB:kw?Math.round(kw.getBoundingClientRect().bottom):null,hdrY:function(){var el=document.querySelector('.catalog-header');return el?Math.round(el.getBoundingClientRect().y):null;}()},timestamp:Date.now()})}).catch(function(){});\n"
    "  // #endregion\n"
    "}\n"
)

REPL = [
    (
        "function clearChromeInlineLeftovers(){\n"
        "  var ch=document.getElementById('searchChrome');\n"
        "  if(ch){ch.style.removeProperty('grid-template-columns');ch.style.removeProperty('height');ch.style.removeProperty('max-height');}\n"
        "  var fw=document.getElementById('filterWrap');\n"
        "  if(fw&&!document.body.classList.contains('display-fs')){fw.style.removeProperty('height');fw.style.removeProperty('max-height');}\n"
        "}\n",
        "function clearChromeInlineLeftovers(){\n"
        "  var ch=document.getElementById('searchChrome');\n"
        "  if(ch){ch.style.removeProperty('grid-template-columns');ch.style.removeProperty('height');ch.style.removeProperty('max-height');}\n"
        "  var fw=document.getElementById('filterWrap');\n"
        "  if(fw&&!document.body.classList.contains('display-fs')){fw.style.removeProperty('height');fw.style.removeProperty('max-height');}\n"
        "}\n" + FN,
        "contain-fn",
    ),
    (
        "    if(typeof clearChromeInlineLeftovers==='function')clearChromeInlineLeftovers();\n",
        "    if(typeof clearChromeInlineLeftovers==='function')clearChromeInlineLeftovers();\n"
        "    if(typeof applyUpperContain==='function')applyUpperContain();\n",
        "leave-sides-contain",
    ),
    (
        "  placeSidesHandles();\n"
        "  syncSidesPin();\n"
        "}\n",
        "  placeSidesHandles();\n"
        "  syncSidesPin();\n"
        "  if(typeof applyUpperContain==='function')applyUpperContain();\n"
        "}\n",
        "sides-end-contain",
        True,
    ),
    (
        "  try{window.scrollTo(0,0);}catch(err){}\n"
        "  syncDisplayBtns();\n",
        "  try{window.scrollTo(0,0);}catch(err){}\n"
        "  if(typeof applyUpperContain==='function')applyUpperContain();\n"
        "  syncDisplayBtns();\n",
        "setDisplay-contain",
    ),
]


def patch_text(text, name):
    if "function applyUpperContain" in text and "upper-contain" in text:
        print(f"  skip {name}")
        return text
    for item in REPL:
        old, new, label = item[0], item[1], item[2]
        optional = item[3] if len(item) > 3 else False
        n = text.count(old)
        if n == 0:
            if optional or new in text:
                print(f"  skip {name}:{label}")
                continue
            raise SystemExit(f"MISSING {name}:{label}")
        text = text.replace(old, new)
        print(f"  {name}:{label} x{n}")
    if "function hideSearchAc" not in text:
        raise SystemExit(f"TRUNCATED {name}: hideSearchAc")
    if name.endswith(".html") and "</html>" not in text:
        raise SystemExit(f"TRUNCATED {name}: </html>")
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
