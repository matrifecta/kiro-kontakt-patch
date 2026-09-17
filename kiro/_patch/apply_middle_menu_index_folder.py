#!/usr/bin/env python3
"""Desktop portrait Middle: S or K alone. Index embed hide path chrome. Smaller folder glyph."""
from pathlib import Path

ROOT = Path("/home/phnx/kiro-kontakt-patch")
FILES = [
    ROOT / "public/catalogs/KONTAKT-CATALOG.html",
    ROOT / "public/catalogs/DS-CATALOG.html",
    ROOT / "public/catalogs/KONTAKT-CATALOG-portable.html",
    ROOT / "public/catalogs/DS-CATALOG-portable.html",
]


def add_indent(s, n=1):
    pad = " " * n
    return "\n".join((pad + line) if line.strip() else line for line in s.split("\n"))


def sub(text, old, new, label, optional=False):
    n = text.count(old)
    if n == 1:
        return text.replace(old, new, 1)
    if n > 1:
        raise SystemExit(f"{label}: {n} matches")
    if new in text:
        print(f"  skip {label} (already)")
        return text
    for i in range(1, 9):
        oldi, newi = add_indent(old, i), add_indent(new, i)
        ni = text.count(oldi)
        if ni == 1:
            return text.replace(oldi, newi, 1)
        if ni > 1:
            raise SystemExit(f"{label}: {ni} matches (indent {i})")
        if ni == 0 and newi in text:
            print(f"  skip {label} (already)")
            return text
    if optional:
        print(f"  skip {label}")
        return text
    raise SystemExit(f"{label}: not found")


PORTRAIT_MID_OLD = """@media(min-width:900px) and (orientation:portrait){
  body.display-sides.display-middle{
    grid-template-columns:minmax(0,var(--middle-lw,1fr)) minmax(0,var(--middle-rw,1fr))!important;
    grid-template-rows:auto var(--middle-menu-h,38dvh) minmax(0,1fr)!important
  }
  body.display-sides.display-middle #searchChrome{grid-column:1!important;grid-row:2!important}
  body.display-sides.display-middle #filterWrap{grid-column:2!important;grid-row:2!important}
  body.display-sides.display-middle #catalogMain{grid-column:1/-1!important;grid-row:3!important}
}"""

PORTRAIT_MID_NEW = """@media(min-width:900px) and (orientation:portrait){
  body.display-sides.display-middle{
    grid-template-columns:minmax(0,var(--middle-lw,1fr)) minmax(0,var(--middle-rw,1fr))!important;
    grid-template-rows:auto var(--middle-menu-h,38dvh) minmax(0,1fr)!important
  }
  body.display-sides.display-middle #searchChrome{grid-column:1!important;grid-row:2!important}
  body.display-sides.display-middle #filterWrap{grid-column:2!important;grid-row:2!important}
  body.display-sides.display-middle #catalogMain{grid-column:1/-1!important;grid-row:3!important}
  /* fix-MIDDLE-ONE-MENU: portrait Middle keeps a menu row when S or K is alone */
  body.display-sides.display-middle.search-chrome-collapsed:not(.kw-chrome-collapsed),
  body.display-sides.display-middle.kw-chrome-collapsed:not(.search-chrome-collapsed){
    grid-template-columns:minmax(0,1fr)!important;
    grid-template-rows:auto var(--middle-menu-h,38dvh) minmax(0,1fr)!important
  }
  body.display-sides.display-middle.search-chrome-collapsed:not(.kw-chrome-collapsed) #filterWrap{
    display:flex!important;grid-column:1/-1!important;grid-row:2!important
  }
  body.display-sides.display-middle.kw-chrome-collapsed:not(.search-chrome-collapsed) #searchChrome{
    display:flex!important;grid-column:1/-1!important;grid-row:2!important
  }
  body.display-sides.display-middle.search-chrome-collapsed:not(.kw-chrome-collapsed) #searchChrome,
  body.display-sides.display-middle.kw-chrome-collapsed:not(.search-chrome-collapsed) #filterWrap{display:none!important}
  body.display-sides.display-middle.search-chrome-collapsed:not(.kw-chrome-collapsed) #catalogMain,
  body.display-sides.display-middle.kw-chrome-collapsed:not(.search-chrome-collapsed) #catalogMain{
    grid-column:1/-1!important;grid-row:3!important
  }
  body.display-sides.display-middle.search-chrome-collapsed.kw-chrome-collapsed{
    grid-template-columns:minmax(0,1fr)!important;
    grid-template-rows:auto minmax(0,1fr)!important
  }
  body.display-sides.display-middle.search-chrome-collapsed.kw-chrome-collapsed #catalogMain{
    grid-column:1/-1!important;grid-row:2!important
  }
}"""

INDEX_HIDE_OLD = """.catalog-body>#catalogIndex a.folder{
  display:none!important;visibility:hidden!important;pointer-events:none!important
}"""

INDEX_HIDE_NEW = """.catalog-body>#catalogIndex a.folder{
  display:none!important;visibility:hidden!important;pointer-events:none!important
}
/* fix-INDEX-ISOLATE-v3: Embed extended — hide path chrome; beat .entry path-icon rules */
#catalogIndex.is-embedded,
#catalogIndex.is-embedded:not(.is-collapsed),
#catalogMain>.catalog-body>#catalogIndex.is-embedded,
#catalogMain>.catalog-body>#catalogIndex.is-embedded:not(.is-collapsed),
.catalog-body>#catalogIndex.is-embedded,
.catalog-body>#catalogIndex.is-embedded:not(.is-collapsed){
  grid-column:1/-1!important;width:100%!important;max-width:100%!important;
  display:flex!important;flex-direction:column!important;
  overflow:hidden!important;isolation:isolate!important;
  background:var(--bg-surface)!important;position:relative!important;
  z-index:26!important;pointer-events:auto!important
}
#catalogIndex.is-embedded:not(.is-collapsed) .index,
#catalogIndex.is-embedded:not(.is-collapsed) #catalogIndexList,
#catalogMain>.catalog-body>#catalogIndex.is-embedded:not(.is-collapsed) .index,
#catalogMain>.catalog-body>#catalogIndex.is-embedded:not(.is-collapsed) #catalogIndexList{
  overflow:hidden!important;isolation:isolate!important;
  background:var(--bg-surface)!important;position:relative!important;z-index:1!important
}
#catalogIndex .path,
#catalogIndex .path-action-row,
#catalogIndex .path-icon-btn,
#catalogIndex .path-label,
#catalogIndex .path-fs-hit,
#catalogIndex .path-copy-hit,
#catalogIndex a.folder,
#catalogIndex .folder,
#catalogIndex .fav-btn,
#catalogIndex.is-embedded .path,
#catalogIndex.is-embedded .path-action-row,
#catalogIndex.is-embedded .path-icon-btn,
#catalogIndex.is-embedded .path-label,
#catalogIndex.is-embedded .path-fs-hit,
#catalogIndex.is-embedded .path-copy-hit,
#catalogIndex.is-embedded a.folder,
#catalogIndex.is-embedded .folder,
#catalogIndex.is-embedded .fav-btn,
#catalogIndex.is-embedded .entry .path,
#catalogIndex.is-embedded .entry .path-action-row,
#catalogIndex.is-embedded .entry .path .path-icon-btn,
#catalogIndex.is-embedded .entry .path:not(.is-expanded) .path-action-row .path-icon-btn,
#catalogMain>.catalog-body>#catalogIndex .path,
#catalogMain>.catalog-body>#catalogIndex .path-action-row,
#catalogMain>.catalog-body>#catalogIndex .path-icon-btn,
#catalogMain>.catalog-body>#catalogIndex .path-label,
#catalogMain>.catalog-body>#catalogIndex .path-fs-hit,
#catalogMain>.catalog-body>#catalogIndex .path-copy-hit,
#catalogMain>.catalog-body>#catalogIndex a.folder,
#catalogMain>.catalog-body>#catalogIndex .fav-btn,
.catalog-body>#catalogIndex .path,
.catalog-body>#catalogIndex .path-action-row,
.catalog-body>#catalogIndex .path-icon-btn,
.catalog-body>#catalogIndex .path-label,
.catalog-body>#catalogIndex .path-fs-hit,
.catalog-body>#catalogIndex .path-copy-hit,
.catalog-body>#catalogIndex a.folder,
.catalog-body>#catalogIndex .fav-btn{
  display:none!important;visibility:hidden!important;pointer-events:none!important;
  width:0!important;height:0!important;min-width:0!important;min-height:0!important;
  overflow:hidden!important;opacity:0!important
}"""

FOLDER_OLD = """/* fix-FOLDER-GLYPH-SIZE: folder only ~25% larger; never #catalogIndex */
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

FOLDER_NEW = """/* fix-FOLDER-GLYPH-SIZE: folder only ~25% larger; never #catalogIndex */
/* fix-FOLDER-GLYPH-SIZE-v2: ~27px — still above copy/fs (~23px) */
.entry .path .folder svg.path-icon-glyph,
.entry .path a.folder svg.path-icon-glyph,
.entry .path .path-icon-btn.folder svg.path-icon-glyph,
.entry .path .path-icon-btn[data-act="folder"] svg.path-icon-glyph{
  width:calc(var(--path-icon-size) * .70)!important;
  height:calc(var(--path-icon-size) * .70)!important;
  min-width:calc(var(--path-icon-size) * .70)!important;
  min-height:calc(var(--path-icon-size) * .70)!important;
  max-width:none!important;max-height:none!important;
  flex:0 0 auto!important
}"""

STRIP_OLD = """function stripIndexCardChrome(ix){
  ix=ix||document.getElementById('catalogIndex');
  if(!ix)return;
  ix.querySelectorAll('.path-action-row,.path-icon-btn,a.folder,.path-fs-hit,.path-copy-hit,.fav-btn').forEach(function(el){
    if(el.closest&&el.closest('.catalog-body .entry,.entry'))return;
    try{el.remove();}catch(err){el.style.display='none';el.setAttribute('hidden','');}
  });
}"""

STRIP_NEW = """function stripIndexCardChrome(ix){
  ix=ix||document.getElementById('catalogIndex');
  if(!ix)return;
  ix.querySelectorAll('.path-action-row,.path-icon-btn,.path-label,.path-fs-hit,.path-copy-hit,.fav-btn,a.folder,.path').forEach(function(el){
    try{el.remove();}catch(err){
      el.style.setProperty('display','none','important');
      el.style.setProperty('visibility','hidden','important');
      el.style.setProperty('pointer-events','none','important');
      el.setAttribute('hidden','');
    }
  });
}"""

EMBED_OLD = """    if(typeof parkCatalogDocNote==='function')parkCatalogDocNote();
    if(typeof applyIndexScrollFit==='function')applyIndexScrollFit();
    if(typeof syncIndexWindowDock==='function')syncIndexWindowDock();"""

EMBED_NEW = """    if(typeof parkCatalogDocNote==='function')parkCatalogDocNote();
    if(typeof stripIndexCardChrome==='function')stripIndexCardChrome(ix);
    if(typeof applyIndexScrollFit==='function')applyIndexScrollFit();
    if(typeof syncIndexWindowDock==='function')syncIndexWindowDock();"""

TOGGLE_IX_OLD = """  if(typeof applyIndexScrollFit==='function')applyIndexScrollFit();
  if(box.classList.contains('is-embedded')&&typeof parkCatalogDocNote==='function')parkCatalogDocNote();"""

TOGGLE_IX_NEW = """  if(typeof stripIndexCardChrome==='function')stripIndexCardChrome(box);
  if(typeof applyIndexScrollFit==='function')applyIndexScrollFit();
  if(box.classList.contains('is-embedded')&&typeof parkCatalogDocNote==='function')parkCatalogDocNote();"""


def patch(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    n = path.name
    if "fix-MIDDLE-ONE-MENU" in text and "fix-INDEX-ISOLATE-v3" in text and "fix-FOLDER-GLYPH-SIZE-v2" in text:
        print("skip", n)
        return
    text = sub(text, PORTRAIT_MID_OLD, PORTRAIT_MID_NEW, f"{n}: portrait-middle")
    text = sub(text, INDEX_HIDE_OLD, INDEX_HIDE_NEW, f"{n}: index-isolate-v3")
    text = sub(text, FOLDER_OLD, FOLDER_NEW, f"{n}: folder-glyph")
    text = sub(text, STRIP_OLD, STRIP_NEW, f"{n}: strip-index")
    text = sub(text, EMBED_OLD, EMBED_NEW, f"{n}: toggle-embed-strip")
    text = sub(text, TOGGLE_IX_OLD, TOGGLE_IX_NEW, f"{n}: toggle-index-strip")
    raw = text.encode("utf-8")
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_bytes(raw)
    out = tmp.read_bytes().decode("utf-8")
    if not out.strip().endswith("</html>"):
        tmp.unlink()
        raise SystemExit(f"{n}: truncated")
    if len(raw) < 100000:
        tmp.unlink()
        raise SystemExit(f"{n}: size too small {len(raw)}")
    tmp.replace(path)
    print("OK", n, len(raw))


def main() -> None:
    for p in FILES:
        if not p.exists():
            raise SystemExit(f"missing {p}")
        patch(p)


if __name__ == "__main__":
    main()
