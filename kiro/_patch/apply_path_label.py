#!/usr/bin/env python3
"""Add centered bold PATH label above catalog path icon buttons.

Touches only path-icon CSS/JS. Unique markers: fix-PATH-LABEL-v1.
Do not strip agent logs. Do not edit Index isolate / card select / embed Back.
"""
from __future__ import annotations

import os
import tempfile
from pathlib import Path

ROOT = Path("/home/phnx/kiro-kontakt-patch")
FILES = [
    ROOT / "public/catalogs/KONTAKT-CATALOG.html",
    ROOT / "public/catalogs/DS-CATALOG.html",
    ROOT / "public/catalogs/KONTAKT-CATALOG-portable.html",
    ROOT / "public/catalogs/DS-CATALOG-portable.html",
]

MARK = "fix-PATH-LABEL-v1"

CSS_ANCHOR = """/* fix-FOLDER-GLYPH-SIZE: folder only ~25% larger; never #catalogIndex */
.entry .path .folder svg.path-icon-glyph,
.entry .path a.folder svg.path-icon-glyph,
.entry .path .path-icon-btn.folder svg.path-icon-glyph,
.entry .path .path-icon-btn[data-act="folder"] svg.path-icon-glyph{
  width:calc(var(--path-icon-size) * .80)!important;
  height:calc(var(--path-icon-size) * .80)!important;
  min-width:calc(var(--path-icon-size) * .80)!important;
  min-height:calc(var(--path-icon-size) * .80)!important;
  max-width:none!important;max-height:none!important;
  flex:0 0 auto!important
}"""

CSS_ADD = CSS_ANCHOR + f"""
/* {MARK}: PATH caps label centered above FS|copy|folder */
.entry .path .path-action-row{{
  flex-wrap:wrap!important;justify-content:center!important;align-items:center!important
}}
.path-label{{
  flex:0 0 100%!important;width:100%!important;box-sizing:border-box!important;
  margin:0 0 .12rem!important;padding:0!important;
  text-align:center!important;font-weight:700!important;font-size:.7rem!important;
  letter-spacing:.06em!important;line-height:1.2!important;text-transform:uppercase!important;
  color:var(--text-muted)!important;pointer-events:none!important;user-select:none!important
}}
#catalogIndex .path-label,
#catalogMain>#catalogIndex .path-label,
#catalogMain>#catalogIndex:not(.is-embedded) .path-label,
body.index-window-open #catalogIndex .path-label,
.catalog-body>#catalogIndex .path-label{{
  display:none!important;visibility:hidden!important;pointer-events:none!important
}}
"""

JS_ANCHOR = """    row.appendChild(fs);row.appendChild(cp);if(folder)row.appendChild(folder);
    ensurePathIconGlyph(fs,'fullscreen');"""

JS_ADD = f"""    if(!row.querySelector('.path-label')){{
      var lab=document.createElement('div');
      lab.className='path-label';
      lab.setAttribute('aria-hidden','true');
      lab.textContent='PATH';
      row.insertBefore(lab,row.firstChild);
    }}
    /* {MARK} */
    row.appendChild(fs);row.appendChild(cp);if(folder)row.appendChild(folder);
    ensurePathIconGlyph(fs,'fullscreen');"""

INDEX_SWAPS = [
    (
        "#catalogMain>#catalogIndex:not(.is-embedded) .path-action-row,\n",
        "#catalogMain>#catalogIndex:not(.is-embedded) .path-action-row,\n#catalogMain>#catalogIndex:not(.is-embedded) .path-label,\n",
        1,
    ),
    (
        "body.index-window-open #catalogIndex .path-action-row,\n",
        "body.index-window-open #catalogIndex .path-action-row,\nbody.index-window-open #catalogIndex .path-label,\n",
        1,
    ),
    (
        ".catalog-body>#catalogIndex .path-action-row,\n",
        ".catalog-body>#catalogIndex .path-action-row,\n.catalog-body>#catalogIndex .path-label,\n",
        1,
    ),
    (
        "#catalogIndex .path-icon-btn,\n#catalogIndex .path-action-row,\n#catalogIndex a.folder,\n",
        "#catalogIndex .path-icon-btn,\n#catalogIndex .path-action-row,\n#catalogIndex .path-label,\n#catalogIndex a.folder,\n",
        1,
    ),
]


def safe_write(path: Path, text: str) -> None:
    if not text.rstrip().endswith("</html>"):
        raise SystemExit(f"{path.name}: bad end before write")
    old_size = path.stat().st_size
    fd, tmp_name = tempfile.mkstemp(suffix=".html", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as tmp:
            tmp.write(text)
        check = Path(tmp_name).read_text(encoding="utf-8")
        if not check.rstrip().endswith("</html>"):
            raise SystemExit(f"{path.name}: temp lost </html>")
        new_size = Path(tmp_name).stat().st_size
        if new_size < old_size * 0.5:
            raise SystemExit(f"{path.name}: size drop {old_size} -> {new_size}")
        os.replace(tmp_name, path)
    except Exception:
        Path(tmp_name).unlink(missing_ok=True)
        raise
    print(f"  wrote {path.name} bytes {new_size}")


def patch_once(text: str, old: str, new: str, label: str, expect: int) -> str:
    n = text.count(old)
    if n == 0:
        if new in text or MARK in text:
            print(f"  skip {label}")
            return text
        raise SystemExit(f"MISSING [{label}]")
    if n != expect:
        raise SystemExit(f"COUNT [{label}]: {n} expected {expect}")
    print(f"  OK {label} x{n}")
    return text.replace(old, new)


def patch_html(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    if not text.rstrip().endswith("</html>"):
        raise SystemExit(f"{path.name}: no </html>")
    print(f"==== {path.name}")

    if f"/* {MARK}:" in text and f"/* {MARK} */" in text:
        print("  already patched")
        return

    if f"/* {MARK}:" not in text:
        if CSS_ANCHOR not in text:
            raise SystemExit(f"{path.name}: no CSS anchor")
        text = text.replace(CSS_ANCHOR, CSS_ADD, 1)
        print("  OK css")

    if f"/* {MARK} */" not in text:
        text = patch_once(text, JS_ANCHOR, JS_ADD, "js-bind", 3)

    for old, new, expect in INDEX_SWAPS:
        if old not in text and new in text:
            print("  skip index-hide already")
            continue
        text = patch_once(text, old, new, "index-hide", expect)

    if text.count("path-label") < 8:
        raise SystemExit(f"{path.name}: path-label sparse")
    if f"/* {MARK}:" not in text or f"/* {MARK} */" not in text:
        raise SystemExit(f"{path.name}: marker missing after patch")
    safe_write(path, text)


def main() -> None:
    for p in FILES:
        try:
            patch_html(p)
        except SystemExit as exc:
            # Concurrent write race: re-read and retry once with unique markers.
            print(f"  retry after: {exc}")
            patch_html(p)
    print("OK", MARK)


if __name__ == "__main__":
    main()
