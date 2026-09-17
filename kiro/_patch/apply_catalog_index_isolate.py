#!/usr/bin/env python3
"""Keep Index out of the card grid so fav/path chrome cannot punch through names."""
from pathlib import Path

ROOT = Path("/home/phnx/kiro-kontakt-patch/public/catalogs")
FILES = [
    ROOT / "KONTAKT-CATALOG.html",
    ROOT / "DS-CATALOG.html",
    ROOT / "KONTAKT-CATALOG-portable.html",
    ROOT / "DS-CATALOG-portable.html",
]

ANCHOR = "body.display-sides #catalogMain .catalog-body>#catalogIndex.is-embedded #indexHeight{display:none!important}"
CSS = ANCHOR + r"""
/* fix-INDEX-ISOLATE: full-width opaque Index; card chrome stays inside .entry */
.catalog-body>#catalogIndex,
#catalogMain>.catalog-body>#catalogIndex,
#catalogMain>.catalog-body>#catalogIndex.is-embedded,
.loc-group>#catalogIndex{
  grid-column:1/-1!important;width:100%!important;max-width:100%!important;
  display:flex!important;flex-direction:column!important;
  overflow:hidden!important;isolation:isolate!important;
  background:var(--bg-surface)!important;position:relative!important;z-index:4!important
}
#catalogIndex .index,#catalogIndex #catalogIndexList{
  background:var(--bg-surface)!important;isolation:isolate!important
}
#catalogIndex .fav-btn,#catalogIndex .path-icon-btn,#catalogIndex .path-action-row{
  display:none!important
}
.entry{position:relative}
.entry:not(.highlight){overflow:hidden}
body.display-upper #catalogIndex,body.display-fs #catalogIndex{
  overflow:hidden!important;background:var(--bg-surface)!important
}
"""


def patch(path: Path) -> None:
    t = path.read_text(encoding="utf-8")
    n = path.name
    if "fix-INDEX-ISOLATE" in t:
        print("skip", n)
        return
    if t.count(ANCHOR) != 1:
        raise SystemExit(f"{n}: anchor {t.count(ANCHOR)}")
    t = t.replace(ANCHOR, CSS, 1)
    raw = t.encode("utf-8")
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_bytes(raw)
    if not tmp.read_bytes().decode("utf-8").strip().endswith("</html>"):
        tmp.unlink()
        raise SystemExit(f"{n}: truncated")
    tmp.replace(path)
    print("OK", n, len(raw))


def main() -> None:
    for p in FILES:
        patch(p)


if __name__ == "__main__":
    main()
