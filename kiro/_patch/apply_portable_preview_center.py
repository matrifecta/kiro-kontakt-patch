#!/usr/bin/env python3
"""Portable chosen-preview: centered dialog; chrome on the card top edge."""
from pathlib import Path

ROOT = Path("/home/phnx/kiro-kontakt-patch/public/catalogs")
ALL = [
    ROOT / "KONTAKT-CATALOG.html",
    ROOT / "DS-CATALOG.html",
    ROOT / "KONTAKT-CATALOG-portable.html",
    ROOT / "DS-CATALOG-portable.html",
]
PORTABLE = [
    ROOT / "KONTAKT-CATALOG-portable.html",
    ROOT / "DS-CATALOG-portable.html",
]

PIN_OLD = (
    "body.chosen-preview-open .entry.selected:not(.highlight){"
    "left:0;right:0;top:4dvh;bottom:auto;transform:none;margin:0 auto;"
    "display:flex;flex-direction:column;align-items:stretch;justify-content:flex-start;"
    "gap:10px;max-height:min(92dvh,100%);height:auto;overflow-x:hidden;overflow-y:auto;"
    "-webkit-overflow-scrolling:touch;grid-template-columns:none}"
)
PIN_NEW = (
    "body.chosen-preview-open .entry.selected:not(.highlight){"
    "left:50%;right:auto;top:50%;bottom:auto;transform:translate(-50%,-50%);margin:0;"
    "display:flex;flex-direction:column;align-items:stretch;justify-content:flex-start;"
    "gap:10px;width:min(92vw,36rem);max-width:min(92vw,36rem);"
    "max-height:min(86dvh,calc(100dvh - 2.5rem));height:auto;overflow-x:hidden;overflow-y:auto;"
    "-webkit-overflow-scrolling:touch;grid-template-columns:none}"
)

SEARCH_PIN_OLD = (
    "body.chosen-preview-open.search-modal-open .entry.selected:not(.highlight)"
    "{top:8px;bottom:auto;margin:8px auto auto;max-height:min(92dvh,100%)}"
)
SEARCH_PIN_NEW = (
    "body.chosen-preview-open.search-modal-open .entry.selected:not(.highlight)"
    "{left:50%;top:50%;right:auto;bottom:auto;transform:translate(-50%,-50%);margin:0;"
    "max-height:min(86dvh,calc(100dvh - 2.5rem))}"
)

FOCUS_OLD = (
    "body.search-modal-open[data-focus=\"search\"].chosen-preview-open "
    ".entry.selected:not(.highlight){z-index:100;-webkit-overflow-scrolling:touch;"
    "transform:none;-webkit-transform:none}"
)
FOCUS_NEW = (
    "body.search-modal-open[data-focus=\"search\"].chosen-preview-open "
    ".entry.selected:not(.highlight){z-index:100;-webkit-overflow-scrolling:touch}"
)

EMBED_TOP_OLD = """/* fix-PORTABLE-EMBED-TOP: back/fs/min on portrait title border; card below header */
@media(orientation:portrait){
  body.catalog-portable.card-embed-open.chosen-preview-open .entry.selected:not(.highlight){
    top:var(--cat-header-h,5.5rem)!important;transform:none!important;left:0!important;right:0!important;
    width:100%!important;max-width:none!important;
    height:calc(100dvh - var(--cat-header-h,5.5rem))!important;max-height:none!important;
    padding-top:.4rem!important
  }
  body.catalog-portable.card-embed-open.chosen-preview-open .entry.selected:not(.highlight) .card-chrome-start .fav-btn{
    display:none!important
  }
  body.catalog-portable.card-embed-open.chosen-preview-open .entry.selected:not(.highlight) .preview-back{
    position:fixed!important;top:max(.2rem,env(safe-area-inset-top,0px))!important;
    left:max(.2rem,env(safe-area-inset-left,0px))!important;right:auto!important;bottom:auto!important;
    z-index:10060!important;display:flex!important;
    width:2.1rem!important;height:2.1rem!important;min-width:2.1rem!important;min-height:2.1rem!important
  }
  body.catalog-portable.card-embed-open.chosen-preview-open .entry.selected:not(.highlight) .hl-min{
    position:fixed!important;top:max(.2rem,env(safe-area-inset-top,0px))!important;
    right:max(.2rem,env(safe-area-inset-right,0px))!important;left:auto!important;bottom:auto!important;
    z-index:10060!important;display:flex!important;
    width:2.1rem!important;height:2.1rem!important;min-width:2.1rem!important;min-height:2.1rem!important
  }
  body.catalog-portable.card-embed-open.chosen-preview-open .entry.selected:not(.highlight) .fs-btn{
    position:fixed!important;top:max(.2rem,env(safe-area-inset-top,0px))!important;
    right:calc(max(.2rem,env(safe-area-inset-right,0px)) + 2.1rem + .28rem)!important;
    left:auto!important;bottom:auto!important;z-index:10060!important;display:flex!important;
    width:2.1rem!important;height:2.1rem!important;min-width:2.1rem!important;min-height:2.1rem!important
  }
}"""

EMBED_TOP_NEW = """/* fix-PORTABLE-PREVIEW-CENTER: extended card is a centered dialog; chrome on the card top edge */
@media all{
  body.catalog-portable.chosen-preview-open .entry.selected:not(.highlight){
    position:fixed!important;
    left:50%!important;top:50%!important;right:auto!important;bottom:auto!important;
    transform:translate(-50%,-50%)!important;-webkit-transform:translate(-50%,-50%)!important;
    margin:0!important;
    width:min(92vw,36rem)!important;max-width:min(92vw,36rem)!important;
    max-height:min(86dvh,calc(100dvh - 2.5rem))!important;
    padding-top:3.5rem!important
  }
  body.catalog-portable.card-embed-open.chosen-preview-open .entry.selected:not(.highlight){
    height:min(86dvh,calc(100dvh - 2.5rem))!important;
    max-height:min(86dvh,calc(100dvh - 2.5rem))!important;
    overflow:hidden!important;
    display:flex!important;flex-direction:column!important
  }
  body.catalog-portable.card-embed-open.chosen-preview-open .entry.selected:not(.highlight) .card-search-embed{
    position:relative!important;inset:auto!important;flex:1 1 auto!important;min-height:0!important;
    margin-top:0!important;order:2
  }
  body.catalog-portable.card-embed-open.chosen-preview-open .entry.selected:not(.highlight) .card-search-chrome{
    position:relative!important;top:auto!important;left:auto!important;right:auto!important;bottom:auto!important;
    display:flex!important;flex:0 0 auto!important;z-index:5!important
  }
  body.catalog-portable.chosen-preview-open .entry.selected:not(.highlight) .card-chrome-start,
  body.catalog-portable.chosen-preview-open .entry.selected:not(.highlight) .card-chrome-end{
    position:absolute!important;
    top:var(--card-chrome-inset,.5rem)!important;
    bottom:auto!important;
    z-index:841!important;
    display:flex!important;
    align-items:center
  }
  body.catalog-portable.chosen-preview-open .entry.selected:not(.highlight) .card-chrome-start{
    left:var(--card-chrome-inset,.5rem)!important;right:auto!important
  }
  body.catalog-portable.chosen-preview-open .entry.selected:not(.highlight) .card-chrome-end{
    right:var(--card-chrome-inset,.5rem)!important;left:auto!important
  }
  body.catalog-portable.chosen-preview-open .entry.selected:not(.highlight) .card-chrome-start>*,
  body.catalog-portable.chosen-preview-open .entry.selected:not(.highlight) .card-chrome-end>*{
    position:static!important;top:auto!important;left:auto!important;right:auto!important;bottom:auto!important
  }
  body.catalog-portable.chosen-preview-open .entry.selected:not(.highlight) .preview-back,
  body.catalog-portable.chosen-preview-open .entry.selected:not(.highlight) .fs-btn,
  body.catalog-portable.chosen-preview-open .entry.selected:not(.highlight) .hl-min,
  body.catalog-portable.chosen-preview-open .entry.selected:not(.highlight) .fav-btn{
    position:static!important;top:auto!important;left:auto!important;right:auto!important;bottom:auto!important;
    display:flex!important
  }
}"""


def must_replace(text: str, old: str, new: str, name: str, label: str) -> str:
    n = text.count(old)
    if n != 1:
        raise SystemExit(f"{name}: {label} count={n}")
    return text.replace(old, new, 1)


def write(path: Path, text: str) -> None:
    out = text.encode("utf-8")
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_bytes(out)
    check = tmp.read_bytes().decode("utf-8")
    if not check.strip().endswith("</html>"):
        tmp.unlink()
        raise SystemExit(f"{path.name}: truncated")
    if "127.0.0.1:7529/ingest" not in check and "agent log" in path.read_text(encoding="utf-8"):
        tmp.unlink()
        raise SystemExit(f"{path.name}: stripped debug logs")
    tmp.replace(path)
    print("OK", path.name, "bytes", len(out))


def main() -> None:
    for path in ALL:
        t = path.read_text(encoding="utf-8")
        t = must_replace(t, PIN_OLD, PIN_NEW, path.name, "4dvh pin")
        t = must_replace(t, SEARCH_PIN_OLD, SEARCH_PIN_NEW, path.name, "search pin")
        t = must_replace(t, FOCUS_OLD, FOCUS_NEW, path.name, "search-focus transform")
        write(path, t)
    for path in PORTABLE:
        t = path.read_text(encoding="utf-8")
        if "fix-PORTABLE-PREVIEW-CENTER" in t and "fix-PORTABLE-EMBED-TOP" not in t:
            print("skip embed-top", path.name)
            continue
        t = must_replace(t, EMBED_TOP_OLD, EMBED_TOP_NEW, path.name, "embed-top")
        write(path, t)


if __name__ == "__main__":
    main()
