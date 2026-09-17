#!/usr/bin/env python3
"""Equal-height Sides panes + tiny non-collapsing gutter. Patch the six synced catalog files."""
from pathlib import Path

ROOT = Path("/home/phnx/kiro-kontakt-patch")
FILES = [
    ROOT / "public/catalogs/DS-CATALOG.html",
    ROOT / "public/catalogs/KONTAKT-CATALOG.html",
    ROOT / "public/catalogs/DS-CATALOG-portable.html",
    ROOT / "public/catalogs/KONTAKT-CATALOG-portable.html",
    ROOT / "kiro/specs/kontakt-workspace-drive-dirty-fix/artifacts/build-ds-catalog-html.sh",
    ROOT / "kiro/specs/kontakt-workspace-drive-dirty-fix/artifacts/build-kontakt-catalog-html.sh",
]

HTML_OLD = (
    "--safe-left:env(safe-area-inset-left,0px);font-size:calc(var(--ui-base) * var(--ui-scale))}"
)
HTML_NEW = (
    "--safe-left:env(safe-area-inset-left,0px);--sides-pane-gap:clamp(4px,.35em,8px);"
    "font-size:calc(var(--ui-base) * var(--ui-scale))}"
)

GRID_OLD = (
    "body.display-sides{max-width:none;width:100%;margin:0;padding:0;height:100dvh;overflow:hidden;"
    "display:grid;grid-template-columns:var(--sides-lw,22vw) minmax(0,1fr) var(--sides-rw,26vw);"
    "grid-template-rows:auto minmax(0,1fr)}"
)
GRID_NEW = (
    "body.display-sides{max-width:none;width:100%;margin:0;padding:0;height:100dvh;overflow:hidden;"
    "display:grid;grid-template-columns:var(--sides-lw,22vw) minmax(0,1fr) var(--sides-rw,26vw);"
    "grid-template-rows:auto minmax(0,1fr);column-gap:var(--sides-pane-gap,6px);row-gap:0;align-items:stretch}"
)

SEARCH_COL_OLD = (
    "body.display-sides.search-chrome-collapsed{grid-template-columns:0 minmax(0,1fr) var(--sides-rw,26vw)}"
)
SEARCH_COL_NEW = (
    "body.display-sides.search-chrome-collapsed{grid-template-columns:minmax(0,1fr) var(--sides-rw,26vw)}"
)

KW_COL_OLD = (
    "body.display-sides.kw-chrome-collapsed{grid-template-columns:var(--sides-lw,22vw) minmax(0,1fr) 0}"
)
KW_COL_NEW = (
    "body.display-sides.kw-chrome-collapsed{grid-template-columns:var(--sides-lw,22vw) minmax(0,1fr)}"
)

BOTH_COL_OLD = (
    "body.display-sides.search-chrome-collapsed.kw-chrome-collapsed{grid-template-columns:0 minmax(0,1fr) 0}"
)
BOTH_COL_NEW = (
    "body.display-sides.search-chrome-collapsed.kw-chrome-collapsed{grid-template-columns:minmax(0,1fr)}"
)

KW_STRIP_OLD = (
    "body.display-sides.search-chrome-collapsed:not(.kw-open):not(.kw-chrome-collapsed)"
    "{grid-template-columns:0 minmax(0,1fr) max-content}"
)
KW_STRIP_NEW = (
    "body.display-sides.search-chrome-collapsed:not(.kw-open):not(.kw-chrome-collapsed)"
    "{grid-template-columns:minmax(0,1fr) max-content}"
)

MAIN_OLD = (
    "body.display-sides #catalogMain{grid-column:2;grid-row:2;min-width:0;min-height:0;"
    "overflow-x:hidden;overflow-y:auto;-webkit-overflow-scrolling:touch;overscroll-behavior:contain;"
    "touch-action:pan-y;padding:0 0 2rem}"
)
MAIN_NEW = (
    "body.display-sides #catalogMain{grid-column:2;grid-row:2;min-width:0;min-height:0;height:100%;"
    "align-self:stretch;overflow-x:hidden;overflow-y:auto;-webkit-overflow-scrolling:touch;"
    "overscroll-behavior:contain;touch-action:pan-y;padding:0 0 2rem;background:var(--bg-surface);"
    "border:1px solid var(--border);border-top:0;box-sizing:border-box}"
)

IDX_OLD = (
    "body.display-sides #catalogIndex{position:sticky;top:0;z-index:12;box-sizing:border-box;"
    "width:100%;max-width:100%;margin:0 0 .75rem;display:flex;flex-direction:column;"
)
IDX_NEW = (
    "body.display-sides #catalogIndex{position:sticky;top:0;z-index:12;box-sizing:border-box;"
    "width:auto;max-width:100%;margin:var(--sides-pane-gap,6px);display:flex;flex-direction:column;"
)

FW_OLD = (
    "body.display-sides #filterWrap{grid-column:3;grid-row:2;height:100%;min-height:0;overflow:hidden;"
    "position:relative!important;inset:auto!important;z-index:5!important;width:100%!important;"
    "max-width:none!important;border-left:1px solid var(--border);border-bottom:0;padding:0;"
    "display:flex!important;flex-direction:column!important}"
)
FW_NEW = (
    "body.display-sides #filterWrap{grid-column:3;grid-row:2;height:100%;min-height:0;overflow:hidden;"
    "position:relative!important;inset:auto!important;z-index:5!important;width:100%!important;"
    "max-width:none!important;border-left:1px solid var(--border);border-bottom:1px solid var(--border);"
    "padding:0;display:flex!important;flex-direction:column!important;background:var(--bg-surface);"
    "align-self:stretch}"
)

SEARCH_OLD = (
    "body.display-sides #searchChrome{grid-column:1;grid-row:2;height:100%;min-height:0;max-width:none;"
    "width:100%;overflow:hidden;display:flex!important;flex-direction:column;position:relative!important;"
    "top:auto!important;z-index:5;background:var(--bg-surface);border-right:1px solid var(--border);"
    "padding:0;align-items:stretch}"
)
SEARCH_NEW = (
    "body.display-sides #searchChrome{grid-column:1;grid-row:2;height:100%;min-height:0;max-width:none;"
    "width:100%;overflow:hidden;display:flex!important;flex-direction:column;position:relative!important;"
    "top:auto!important;z-index:5;background:var(--bg-surface);border-right:1px solid var(--border);"
    "border-bottom:1px solid var(--border);padding:0;align-items:stretch;align-self:stretch;box-sizing:border-box}"
)

PORTRAIT_MAIN_OLD = """  body.display-sides #catalogMain{
    grid-column:2!important;grid-row:2/-1!important;
    min-height:0;overflow-y:auto!important;overflow-x:hidden;padding:0 0 2rem
  }"""
PORTRAIT_MAIN_NEW = """  body.display-sides #catalogMain{
    grid-column:2!important;grid-row:2/-1!important;
    min-height:0;height:100%;align-self:stretch;overflow-y:auto!important;overflow-x:hidden;padding:0 0 2rem
  }"""

MARKER = "#portraitFlipBtn[hidden]{display:none!important}"
BLOCK = """/* fix-SIDES-PANE: equal bottoms + tiny gutter that never collapses to 0 */
@media(min-width:900px){
  body.display-sides.search-chrome-collapsed:not(.kw-chrome-collapsed) #catalogMain{grid-column:1}
  body.display-sides.search-chrome-collapsed:not(.kw-chrome-collapsed) #filterWrap{grid-column:2}
  body.display-sides.search-chrome-collapsed.kw-chrome-collapsed #catalogMain{grid-column:1}
  body.display-sides.search-chrome-collapsed:not(.kw-open):not(.kw-chrome-collapsed) #catalogMain{grid-column:1}
  body.display-sides.search-chrome-collapsed:not(.kw-open):not(.kw-chrome-collapsed) #filterWrap{grid-column:2}
  body.display-sides #catalogMain,body.display-sides #searchChrome,body.display-sides.kw-open #filterWrap{height:100%;min-height:0;align-self:stretch}
  body.display-sides #catalogIndex:not(.is-embedded){width:auto;max-width:100%;margin:var(--sides-pane-gap,6px)}
}
@media(min-width:900px) and (orientation:portrait){
  body.display-sides{column-gap:var(--sides-pane-gap,6px)!important;row-gap:0!important}
  body.display-sides:not(.search-chrome-collapsed):not(.kw-chrome-collapsed) #searchChrome{margin-bottom:var(--sides-pane-gap,6px)!important}
  body.display-sides.kw-chrome-collapsed #searchChrome{margin-bottom:0!important}
  body.display-sides #catalogMain{height:100%!important;align-self:stretch!important}
}
"""

CLAMP_L_OLD = "lw=Math.max(minL,Math.min(lw,vw-minR-minC));"
CLAMP_L_NEW = "lw=Math.max(minL,Math.min(lw,vw-minR-minC-2*(parseFloat(getComputedStyle(document.documentElement).getPropertyValue('--sides-pane-gap'))||6)));"
CLAMP_R_OLD = "rw=Math.max(minR,Math.min(rw,vw-minL-minC));"
CLAMP_R_NEW = "rw=Math.max(minR,Math.min(rw,vw-minL-minC-2*(parseFloat(getComputedStyle(document.documentElement).getPropertyValue('--sides-pane-gap'))||6)));"
DRAG_L_OLD = "var lw=Math.max(minL,Math.min(vw-minR-minC,drag.lw+(e.clientX-drag.x)));"
DRAG_L_NEW = "var lw=Math.max(minL,Math.min(vw-minR-minC-2*(parseFloat(getComputedStyle(document.documentElement).getPropertyValue('--sides-pane-gap'))||6),drag.lw+(e.clientX-drag.x)));"
DRAG_R_OLD = "var rw=Math.max(minR,Math.min(vw-minL-minC,drag.rw-(e.clientX-drag.x)));"
DRAG_R_NEW = "var rw=Math.max(minR,Math.min(vw-minL-minC-2*(parseFloat(getComputedStyle(document.documentElement).getPropertyValue('--sides-pane-gap'))||6),drag.rw-(e.clientX-drag.x)));"

SPLIT_OLD = "left:'+Math.round(r.right-6)+'px;"
SPLIT_NEW = "left:'+Math.round(r.right+(parseFloat(getComputedStyle(document.documentElement).getPropertyValue('--sides-pane-gap'))||6)/2-6)+'px;"
SEP_OLD = "left:'+Math.round(r2.left-6)+'px;"
SEP_NEW = "left:'+Math.round(r2.left-(parseFloat(getComputedStyle(document.documentElement).getPropertyValue('--sides-pane-gap'))||6)/2-6)+'px;"

# Portrait vertical split sits on Search bottom; inset by half the gutter.
PORTRAIT_SPLIT_OLD = "top:Math.round(r.bottom-6)+'px'"
PORTRAIT_SPLIT_NEW = "top:Math.round(r.bottom+(parseFloat(getComputedStyle(document.documentElement).getPropertyValue('--sides-pane-gap'))||6)/2-6)+'px'"
PORTRAIT_SEP_OLD = "var x=flip?Math.round(r2.left-6):Math.round(r2.right-6);"
PORTRAIT_SEP_NEW = "var paneGap=parseFloat(getComputedStyle(document.documentElement).getPropertyValue('--sides-pane-gap'))||6;var x=flip?Math.round(r2.left-paneGap/2-6):Math.round(r2.right+paneGap/2-6);"


def sub_once(text, old, new, path, label, allow_multi=False):
    n = text.count(old)
    if n == 0:
        raise SystemExit(f"{path.name}: missing {label}")
    if not allow_multi and n != 1:
        raise SystemExit(f"{path.name}: {label} count={n}, expected 1")
    return text.replace(old, new), n


def patch(path: Path):
    text = path.read_text(encoding="utf-8")
    if "fix-SIDES-PANE: equal bottoms" in text:
        print(f"skip already patched: {path}")
        return
    counts = {}
    text, counts["html"] = sub_once(text, HTML_OLD, HTML_NEW, path, "html var")
    text, counts["grid"] = sub_once(text, GRID_OLD, GRID_NEW, path, "sides grid")
    text, counts["search_col"] = sub_once(text, SEARCH_COL_OLD, SEARCH_COL_NEW, path, "search collapsed cols")
    text, counts["kw_col"] = sub_once(text, KW_COL_OLD, KW_COL_NEW, path, "kw collapsed cols", allow_multi=True)
    text, counts["both_col"] = sub_once(text, BOTH_COL_OLD, BOTH_COL_NEW, path, "both collapsed cols", allow_multi=True)
    text, counts["kw_strip"] = sub_once(text, KW_STRIP_OLD, KW_STRIP_NEW, path, "kw-strip collapsed")
    text, counts["search"] = sub_once(text, SEARCH_OLD, SEARCH_NEW, path, "searchChrome")
    text, counts["fw"] = sub_once(text, FW_OLD, FW_NEW, path, "filterWrap")
    text, counts["main"] = sub_once(text, MAIN_OLD, MAIN_NEW, path, "catalogMain")
    text, counts["idx"] = sub_once(text, IDX_OLD, IDX_NEW, path, "catalogIndex")
    text, counts["pmain"] = sub_once(text, PORTRAIT_MAIN_OLD, PORTRAIT_MAIN_NEW, path, "portrait catalogMain")
    if MARKER not in text:
        raise SystemExit(f"{path.name}: missing portraitFlip marker")
    if text.count(MARKER) != 1:
        raise SystemExit(f"{path.name}: portraitFlip marker count={text.count(MARKER)}")
    text = text.replace(MARKER, BLOCK + MARKER, 1)
    text, counts["clamp_l"] = sub_once(text, CLAMP_L_OLD, CLAMP_L_NEW, path, "clamp L")
    text, counts["clamp_r"] = sub_once(text, CLAMP_R_OLD, CLAMP_R_NEW, path, "clamp R")
    text, counts["drag_l"] = sub_once(text, DRAG_L_OLD, DRAG_L_NEW, path, "drag L")
    text, counts["drag_r"] = sub_once(text, DRAG_R_OLD, DRAG_R_NEW, path, "drag R")
    text, counts["split"] = sub_once(text, SPLIT_OLD, SPLIT_NEW, path, "split handle")
    text, counts["sep"] = sub_once(text, SEP_OLD, SEP_NEW, path, "sep handle")
    text, counts["psplit"] = sub_once(text, PORTRAIT_SPLIT_OLD, PORTRAIT_SPLIT_NEW, path, "portrait split")
    text, counts["psep"] = sub_once(text, PORTRAIT_SEP_OLD, PORTRAIT_SEP_NEW, path, "portrait sep")
    if "cat-switch{flex-wrap:wrap!important" not in text:
        raise SystemExit(f"{path.name}: lost cat-switch wrap")
    path.write_text(text, encoding="utf-8")
    print(f"patched {path} {counts}")


def main():
    for p in FILES:
        if not p.exists():
            raise SystemExit(f"missing {p}")
        patch(p)


if __name__ == "__main__":
    main()
