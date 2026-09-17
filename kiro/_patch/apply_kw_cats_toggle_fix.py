#!/usr/bin/env python3
"""Fix KW cats toggle to use body.kw-cats-open instead of the always-hidden pop."""
from __future__ import annotations

import os
import tempfile
from pathlib import Path

ROOT = Path("/home/phnx/kiro-kontakt-patch/public/catalogs")
FILES = [
    ROOT / "KONTAKT-CATALOG-portable.html",
    ROOT / "DS-CATALOG-portable.html",
]

OLD = """function toggleKwStripMore(){
  var pop=document.getElementById('kwStripMorePop');var btn=document.getElementById('kwStripMore');
  var top=document.getElementById('filterTop');
  var cs=document.getElementById('catSwitch');
  var fp=document.getElementById('filterPanel');
  var kb=document.getElementById('kwbar');
  if(!pop||!btn)return;
  var open=pop.hasAttribute('hidden');
"""

NEW = """function toggleKwStripMore(){
  var pop=document.getElementById('kwStripMorePop');var btn=document.getElementById('kwStripMore');
  var top=document.getElementById('filterTop');
  var cs=document.getElementById('catSwitch');
  var fp=document.getElementById('filterPanel')||document.querySelector('#filterWrap .filter-panel');
  var kb=document.getElementById('kwbar');
  if(!btn)return;
  var open=!document.body.classList.contains('kw-cats-open');
"""


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
    text = path.read_text(encoding="utf-8")
    n = text.count(OLD)
    if n == 0:
        if "var open=!document.body.classList.contains('kw-cats-open');" in text:
            print(f"skip {path.name}")
            return
        raise SystemExit(f"{path.name}: missing toggle mark")
    if n != 1:
        raise SystemExit(f"{path.name}: count {n}")
    text = text.replace(OLD, NEW, 1)
    safe_write(path, text)


def main() -> None:
    for p in FILES:
        print("==", p.name)
        patch(p)


if __name__ == "__main__":
    main()
