#!/usr/bin/env python3
"""Nudge #catalogJumpStack left of the content scrollbar in all four catalogs."""
from __future__ import annotations

import os
import tempfile
from pathlib import Path

ROOT = Path("/home/phnx/kiro-kontakt-patch/public/catalogs")
FILES = [
    ROOT / "KONTAKT-CATALOG-portable.html",
    ROOT / "DS-CATALOG-portable.html",
    ROOT / "KONTAKT-CATALOG.html",
    ROOT / "DS-CATALOG.html",
]

HELPER = r"""function catalogJumpScrollbarGutter(main){
  var sc=(typeof catalogContentScroller==='function'&&catalogContentScroller())||main||document.getElementById('catalogMain');
  var sbw=0;
  if(sc)sbw=Math.max(0,(sc.offsetWidth||0)-(sc.clientWidth||0));
  var stripe=document.getElementById('catalogMainHoverStripe');
  var stripeW=0;
  if(stripe&&!stripe.hidden){
    var stCs=getComputedStyle(stripe);
    if(stCs.display!=='none'&&stCs.visibility!=='hidden')stripeW=Math.round(stripe.getBoundingClientRect().width)||12;
  }
  return Math.max(16,Math.round(sbw||0),Math.round(stripeW||0))+8;
}
window.catalogJumpScrollbarGutter=catalogJumpScrollbarGutter;
"""

PORT_OLD = """    var padR=parseFloat(mainCs.paddingRight)||10;
    var padB=parseFloat(mainCs.paddingBottom)||10;
    var insetR=Math.max(8,Math.round(padR));
    var insetB=Math.max(8,Math.round(padB));
    var right=Math.max(6,Math.round((window.innerWidth||0)-r.right)+insetR);
"""

PORT_NEW = """    var padR=parseFloat(mainCs.paddingRight)||10;
    var padB=parseFloat(mainCs.paddingBottom)||10;
    var gutter=typeof catalogJumpScrollbarGutter==='function'?catalogJumpScrollbarGutter(main):24;
    var insetR=Math.max(8,Math.round(padR))+gutter;
    var insetB=Math.max(8,Math.round(padB));
    var right=Math.max(6,Math.round((window.innerWidth||0)-r.right)+insetR);
"""

DESK_OLD = """  var r=main.getBoundingClientRect();
  var right=Math.max(6,Math.round((window.innerWidth||0)-r.right)+10);
"""

DESK_NEW = """  var r=main.getBoundingClientRect();
  var gutter=typeof catalogJumpScrollbarGutter==='function'?catalogJumpScrollbarGutter(main):24;
  var right=Math.max(6,Math.round((window.innerWidth||0)-r.right)+10+gutter);
"""


def once(text: str, old: str, new: str, label: str, name: str) -> str:
    if old not in text:
        if new in text:
            print(f"  skip {label} {name}")
            return text
        raise SystemExit(f"{name}: missing {label}: {old[:90]!r}")
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
    if "function catalogJumpScrollbarGutter(" not in text:
        text = once(text, "function placeCatalogJumpStack(){", HELPER + "function placeCatalogJumpStack(){", "helper", name)
    else:
        print(f"  skip helper {name}")
    if "portable" in name:
        text = once(text, PORT_OLD, PORT_NEW, "port-right", name)
    else:
        text = once(text, DESK_OLD, DESK_NEW, "desk-right", name)
    if "function catalogJumpScrollbarGutter(" not in text:
        raise SystemExit(f"{name}: helper missing")
    safe_write(path, text)


def main() -> None:
    for p in FILES:
        print("==", p.name)
        patch(p)


if __name__ == "__main__":
    main()
