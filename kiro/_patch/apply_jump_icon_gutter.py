#!/usr/bin/env python3
"""Compact filled skip-to-top/bottom jump icons and a tighter scrollbar gutter."""
from __future__ import annotations

import os
import tempfile
from pathlib import Path

ROOT = Path("/home/phnx/kiro-kontakt-patch/public/catalogs")
FILES = [
    ROOT / "KONTAKT-CATALOG.html",
    ROOT / "KONTAKT-CATALOG-portable.html",
    ROOT / "DS-CATALOG.html",
    ROOT / "DS-CATALOG-portable.html",
]

CSS_OLD = (
    ".top,.bottom{background:var(--accent-instrument);color:#1a1008;"
    "padding:.4rem .7rem;border-radius:4px;text-decoration:none;"
    "border:1px solid var(--accent-instrument)}"
)
CSS_NEW = (
    ".top,.bottom{background:var(--accent-instrument);color:#1a1008;padding:0;"
    "width:2.125rem;height:2.125rem;min-width:32px;min-height:32px;box-sizing:border-box;"
    "display:inline-flex;align-items:center;justify-content:center;border-radius:4px;"
    "text-decoration:none;border:1px solid var(--accent-instrument);line-height:0;font-size:0}"
    ".top .catalog-jump-ico,.bottom .catalog-jump-ico{display:block;width:1.2rem;height:1.2rem;"
    "flex:0 0 auto;pointer-events:none}"
)

HTML_OLD = '<a class="bottom" href="#catalogBottom">&darr; bottom</a><a class="top" href="#top">&uarr; top</a>'
HTML_NEW = (
    '<a class="bottom" href="#catalogBottom" aria-label="Jump to bottom" title="Jump to bottom">'
    '<svg class="catalog-jump-ico" viewBox="0 0 24 24" aria-hidden="true" focusable="false" fill="currentColor">'
    '<rect x="10" y="2.2" width="4" height="8.7" rx=".45"/>'
    '<polygon points="12,17.7 20.4,8.7 3.6,8.7"/>'
    '<rect x="3.5" y="18.2" width="17" height="3.6" rx=".45"/>'
    "</svg></a>"
    '<a class="top" href="#top" aria-label="Jump to top" title="Jump to top">'
    '<svg class="catalog-jump-ico" viewBox="0 0 24 24" aria-hidden="true" focusable="false" fill="currentColor">'
    '<rect x="3.5" y="2.2" width="17" height="3.6" rx=".45"/>'
    '<polygon points="12,6.3 20.4,15.3 3.6,15.3"/>'
    '<rect x="10" y="13.1" width="4" height="8.7" rx=".45"/>'
    "</svg></a>"
)

HELP_OLD = "<li><b>↑ top / ↓ bottom</b> — jump stack on the content window (usually bottom-right). Stay put while cards scroll.</li>"
HELP_NEW = "<li><b>Skip to top / bottom</b> — jump stack on the content window (usually bottom-right). Stay put while cards scroll.</li>"

GUTTER_OLD = "  return Math.max(16,Math.round(sbw||0),Math.round(stripeW||0))+8;\n"
GUTTER_NEW = "  return Math.max(12,Math.round(sbw||0))+4;\n"

GLYPH_FN = r"""function catalogJumpGlyph(kind){
  var top=kind==='top';
  var bar=top?'<rect x="3.5" y="2.2" width="17" height="3.6" rx=".45"/>':'<rect x="3.5" y="18.2" width="17" height="3.6" rx=".45"/>';
  var shaft=top?'<rect x="10" y="13.1" width="4" height="8.7" rx=".45"/>':'<rect x="10" y="2.2" width="4" height="8.7" rx=".45"/>';
  var tri=top?'<polygon points="12,6.3 20.4,15.3 3.6,15.3"/>':'<polygon points="12,17.7 20.4,8.7 3.6,8.7"/>';
  return '<svg class="catalog-jump-ico" viewBox="0 0 24 24" aria-hidden="true" focusable="false" fill="currentColor">'+bar+shaft+tri+'</svg>';
}
function ensureCatalogJumpGlyph(btn,kind){
  if(!btn)return;
  var label=kind==='top'?'Jump to top':'Jump to bottom';
  btn.setAttribute('aria-label',label);
  btn.setAttribute('title',label);
  if(!btn.querySelector('svg.catalog-jump-ico')){
    btn.textContent='';
    btn.insertAdjacentHTML('afterbegin',catalogJumpGlyph(kind));
  }
}
"""

BOT_OLD = """    bot.href='#catalogBottom';
    bot.textContent='\\u2193 bottom';
  }
  var topBtn=document.querySelector('a.top');
"""
BOT_NEW = """    bot.href='#catalogBottom';
  }
  var topBtn=document.querySelector('a.top');
  ensureCatalogJumpGlyph(topBtn,'top');
  ensureCatalogJumpGlyph(bot,'bottom');
"""

LOG_OLD = """      styleB:stack?stack.style.bottom:'',
      styleR:stack?stack.style.right:''
"""
LOG_NEW = """      styleB:stack?stack.style.bottom:'',
      styleR:stack?stack.style.right:'',
      gutter:typeof catalogJumpScrollbarGutter==='function'?catalogJumpScrollbarGutter(document.getElementById('catalogMain')):null,
      icoT:!!(top&&top.querySelector&&top.querySelector('svg.catalog-jump-ico')),
      icoB:!!(bot&&bot.querySelector&&bot.querySelector('svg.catalog-jump-ico'))
"""


def once(text: str, old: str, new: str, label: str, name: str) -> str:
    if old not in text:
        if new in text:
            print(f"  skip {label} {name}")
            return text
        raise SystemExit(f"{name}: missing {label}: {old[:120]!r}")
    n = text.count(old)
    if n != 1:
        raise SystemExit(f"{name}: {label} count {n}")
    print(f"  1x {label} {name}")
    return text.replace(old, new, 1)


def safe_write(path: Path, text: str) -> None:
    if not text.rstrip().endswith("</html>"):
        raise SystemExit(f"{path.name}: rewrite would drop </html>")
    raw = text.encode("utf-8")
    fd, tmp = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=str(path.parent))
    try:
        os.write(fd, raw)
        os.fsync(fd)
        os.close(fd)
        fd = -1
        tmp_path = Path(tmp)
        if not tmp_path.read_text(encoding="utf-8").rstrip().endswith("</html>"):
            tmp_path.unlink(missing_ok=True)
            raise SystemExit(f"{path.name}: tmp missing </html>")
        size = tmp_path.stat().st_size
        if size < 200_000:
            tmp_path.unlink(missing_ok=True)
            raise SystemExit(f"{path.name}: tmp too small {size}")
        os.replace(tmp, path)
        assert path.stat().st_size == size
        assert path.read_text(encoding="utf-8").rstrip().endswith("</html>")
        print(f"ok {path.name} bytes={size}")
    finally:
        if fd >= 0:
            try:
                os.close(fd)
            except OSError:
                pass
        if os.path.exists(tmp):
            os.unlink(tmp)


def patch(path: Path) -> None:
    name = path.name
    text = path.read_text(encoding="utf-8")
    c00 = text.count("sessionId:'c00e3e'")
    text = once(text, CSS_OLD, CSS_NEW, "css", name)
    text = once(text, HTML_OLD, HTML_NEW, "html", name)
    text = once(text, HELP_OLD, HELP_NEW, "help", name)
    text = once(text, GUTTER_OLD, GUTTER_NEW, "gutter", name)
    if "function catalogJumpGlyph(" not in text:
        text = once(text, "function ensureCatalogMain(){", GLYPH_FN + "function ensureCatalogMain(){", "glyph-fn", name)
    else:
        print(f"  skip glyph-fn {name}")
    text = once(text, BOT_OLD, BOT_NEW, "bot-create", name)
    text = once(text, LOG_OLD, LOG_NEW, "log-fields", name)
    text = text.replace(
        "catalogJumpScrollbarGutter(main):24",
        "catalogJumpScrollbarGutter(main):16",
    )
    if "catalog-jump-ico" not in text:
        raise SystemExit(f"{name}: icons missing")
    if "Math.max(12,Math.round(sbw||0))+4" not in text:
        raise SystemExit(f"{name}: tight gutter missing")
    if "bot.textContent='\\u2193 bottom'" in text:
        raise SystemExit(f"{name}: leftover bottom text")
    c00_after = text.count("sessionId:'c00e3e'")
    if c00_after < c00:
        raise SystemExit(f"{name}: lost c00e3e logs ({c00_after} < {c00})")
    safe_write(path, text)


def main() -> None:
    for p in FILES:
        print("==", p.name)
        patch(p)


if __name__ == "__main__":
    main()
