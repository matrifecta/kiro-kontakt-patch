#!/usr/bin/env python3
"""Add layout-fix H5/H6/H8 logs. Skip if already present. KIRO builders first."""
from pathlib import Path
import shutil

KIRO = Path("/home/phnx/KIRO/.kiro/specs/kontakt-workspace-drive-dirty-fix/artifacts")
WS = Path("/home/phnx/kiro-kontakt-patch/kiro/specs/kontakt-workspace-drive-dirty-fix/artifacts")
PUB = Path("/home/phnx/kiro-kontakt-patch/public/catalogs")
INGEST = "http://127.0.0.1:7529/ingest/1cf46354-1d61-4c80-bd72-a340f1db1b51"
LOG = (
    "fetch('" + INGEST + "',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'f491c2'},"
    "body:JSON.stringify({sessionId:'f491c2',runId:'layout-fix',hypothesisId:'%s',location:'%s',message:'%s',data:%s,timestamp:Date.now()})}).catch(function(){});"
)

H6_OLD = (
    "  s[mode]=cur;\n"
    "  writeModeLayoutStore(s);\n"
    "  return cur;\n"
    "}\n"
    "function modeLayoutPinned(){"
)
H6_NEW = (
    "  s[mode]=cur;\n"
    "  writeModeLayoutStore(s);\n"
    "  // #region agent log\n"
    + LOG % (
        "H6",
        "writeModeSlot",
        "mode-slot-save",
        "{mode:mode,keys:Object.keys(cur||{}),hasChrome:!!(cur&&cur.chromeH),hasLw:!!(cur&&cur.lw)}",
    )
    + "\n"
    "  // #endregion\n"
    "  return cur;\n"
    "}\n"
    "function modeLayoutPinned(){"
)

H8_OLD = (
    "  if(!document.body.classList.contains('kw-open')){\n"
    "    document.body.style.removeProperty('--sides-rw');\n"
    "  }else{\n"
)
H8_NEW = (
    "  if(!document.body.classList.contains('kw-open')){\n"
    "    document.body.style.removeProperty('--sides-rw');\n"
    "    // #region agent log\n"
    + LOG % (
        "H8",
        "applySidesCols",
        "sides-kw-well",
        "{rw:getComputedStyle(document.body).getPropertyValue('--sides-rw').trim(),fwW:function(){var el=document.getElementById('filterWrap');if(!el)return null;return Math.round(el.getBoundingClientRect().width);}(),fwH:function(){var el=document.getElementById('filterWrap');if(!el)return null;return Math.round(el.getBoundingClientRect().height);}()}",
    )
    + "\n"
    "    // #endregion\n"
    "  }else{\n"
)

H5_OLD = (
    "    if(!displayIsDesktop()){\n"
    "      document.body.classList.remove('dual-fs-open');\n"
    "      if(typeof kwFsWanted!=='undefined'&&currentDisplay!=='fs')kwFsWanted=false;\n"
    "      if(typeof clearChromeInlineLeftovers==='function')clearChromeInlineLeftovers();\n"
    "      if(currentDisplay==='sides'){setDisplayMode('fs',{menu:'search'});return;}\n"
    "    }\n"
)
H5_NEW = (
    "    if(!displayIsDesktop()){\n"
    "      document.body.classList.remove('dual-fs-open');\n"
    "      if(typeof kwFsWanted!=='undefined'&&currentDisplay!=='fs')kwFsWanted=false;\n"
    "      if(typeof clearChromeInlineLeftovers==='function')clearChromeInlineLeftovers();\n"
    "      // #region agent log\n"
    + LOG % (
        "H5",
        "resize",
        "mobile-coerce",
        "{from:currentDisplay,vw:window.innerWidth,dual:document.body.classList.contains('dual-fs-open'),chGrid:function(){var el=document.getElementById('searchChrome');return el?(el.style.gridTemplateColumns||''):'';}()}",
    )
    + "\n"
    "      // #endregion\n"
    "      if(currentDisplay==='sides'){setDisplayMode('fs',{menu:'search'});return;}\n"
    "    }\n"
)


def patch_text(text, name):
    for old, new, label, marker in (
        (H6_OLD, H6_NEW, "H6", "mode-slot-save"),
        (H8_OLD, H8_NEW, "H8", "sides-kw-well"),
        (H5_OLD, H5_NEW, "H5", "mobile-coerce"),
    ):
        if marker in text and new in text:
            print(f"  skip {name}:{label}")
            continue
        n = text.count(old)
        if n == 0:
            if marker in text:
                print(f"  skip {name}:{label} (marker)")
                continue
            raise SystemExit(f"MISSING {name}:{label}")
        if n > 1:
            print(f"  warn {name}:{label} x{n} — replacing all")
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
