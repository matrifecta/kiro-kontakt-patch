#!/usr/bin/env python3
"""Portable: KW label inert, Customize height edges, header ⋯ actually closes, Flip spatial only, ⛶ only on document toolbar."""
from pathlib import Path

ROOT = Path("/home/phnx/kiro-kontakt-patch")
FILES = [
    ROOT / "public/catalogs/DS-CATALOG-portable.html",
    ROOT / "public/catalogs/KONTAKT-CATALOG-portable.html",
]

CSS_MARK = "/* fix-PORTABLE-CHROME-FLIP:"
CSS = r"""
/* fix-PORTABLE-CHROME-FLIP: ⛶ only on document toolbar; ⋯ close; KW label inert; Customize edges; Flip spatial */
@media all{
  body.catalog-portable .search-strip-fs,
  body.catalog-portable .kw-fs-btn,
  body.catalog-portable #searchStripFs,
  body.catalog-portable #kwStripFs,
  body.catalog-portable.display-sides .search-strip-fs,
  body.catalog-portable.display-sides .kw-fs-btn,
  body.catalog-portable.display-sides #searchStripFs,
  body.catalog-portable.display-sides #kwStripFs,
  body.catalog-portable.display-sides.ac-fs-open .search-strip-fs,
  body.catalog-portable.display-sides.kw-fs-open .kw-fs-btn,
  body.catalog-portable.display-middle .search-strip-fs,
  body.catalog-portable.display-middle .kw-fs-btn{display:none!important}
  body.catalog-portable #hdrToolbarFs{
    display:inline-flex!important;align-items:center;justify-content:center;margin-left:auto;order:120
  }
  body.catalog-portable #hdrMorePop[hidden],
  body.catalog-portable .catalog-header>#hdrMorePop[hidden],
  body.catalog-portable .hdr-more-pop[hidden]{display:none!important}
  body.catalog-portable #filterToggle{
    pointer-events:none!important;cursor:default!important
  }
  body.catalog-portable.layout-edit #searchSplit.port-stripe-v,
  body.catalog-portable.layout-edit #searchSplit.port-stripe-h,
  body.catalog-portable.layout-edit #dualFsSep.port-stripe-v,
  body.catalog-portable.layout-edit #dualFsSep.port-stripe-h{
    display:block!important;pointer-events:auto!important
  }
}
@media(orientation:portrait){
  body.catalog-portable.sides-portrait-flip.display-sides:not(.display-middle).kw-open:not(.search-chrome-collapsed):not(.dual-fs-open) #searchChrome{
    grid-column:2!important;grid-row:2!important
  }
  body.catalog-portable.sides-portrait-flip.display-sides:not(.display-middle).kw-open:not(.search-chrome-collapsed):not(.dual-fs-open) #filterWrap{
    grid-column:2!important;grid-row:3!important
  }
}
"""

FLIP_OLD = """  body.catalog-portable.sides-portrait-flip.display-sides:not(.display-middle).kw-open:not(.search-chrome-collapsed):not(.dual-fs-open) #searchChrome{
    grid-column:2!important;grid-row:3!important
  }
  body.catalog-portable.sides-portrait-flip.display-sides:not(.display-middle).kw-open:not(.search-chrome-collapsed):not(.dual-fs-open) #filterWrap{
    grid-column:2!important;grid-row:2!important
  }"""

FLIP_NEW = """  body.catalog-portable.sides-portrait-flip.display-sides:not(.display-middle).kw-open:not(.search-chrome-collapsed):not(.dual-fs-open) #searchChrome{
    grid-column:2!important;grid-row:2!important
  }
  body.catalog-portable.sides-portrait-flip.display-sides:not(.display-middle).kw-open:not(.search-chrome-collapsed):not(.dual-fs-open) #filterWrap{
    grid-column:2!important;grid-row:3!important
  }"""


def patch(text: str) -> str:
    if CSS_MARK not in text:
        idx = text.rfind("</style>")
        if idx < 0:
            raise SystemExit("no </style>")
        text = text[:idx] + CSS + text[idx:]
    text = text.replace(FLIP_OLD, FLIP_NEW, 1)
    text = text.replace(
        'id="filterToggle" onclick="toggleFilter()"',
        'id="filterToggle" onclick="if(window.CATALOG_PORTABLE){event.preventDefault();return;}toggleFilter()"',
        1,
    )
    old_close = """function closePhoneOverflowPops(except){
  [['hdrMorePop','hdrMoreBtn']].forEach(function(pair){
    if(except&&pair[0]===except)return;
    var p=document.getElementById(pair[0]);var b=document.getElementById(pair[1]);
    if(p)p.setAttribute('hidden','');
    if(b)b.setAttribute('aria-expanded','false');
  });
}"""
    new_close = """function closePhoneOverflowPops(except){
  [['hdrMorePop','hdrMoreBtn']].forEach(function(pair){
    if(except&&pair[0]===except)return;
    var p=document.getElementById(pair[0]);var b=document.getElementById(pair[1]);
    if(p){
      p.setAttribute('hidden','');
      p.style.removeProperty('display');
      p.style.setProperty('display','none','important');
    }
    if(b)b.setAttribute('aria-expanded','false');
  });
}"""
    if old_close not in text:
        raise SystemExit("closePhoneOverflowPops not found")
    text = text.replace(old_close, new_close, 1)

    old_hdr_close = """    pop.setAttribute('hidden','');btn.setAttribute('aria-expanded','false');
    // #region agent log"""
    new_hdr_close = """    pop.setAttribute('hidden','');
    pop.style.removeProperty('display');
    pop.style.setProperty('display','none','important');
    btn.setAttribute('aria-expanded','false');
    // #region agent log"""
    if old_hdr_close not in text:
        raise SystemExit("toggleHdrMore close not found")
    text = text.replace(old_hdr_close, new_hdr_close, 1)

    old_hide = """  hide(split);hide(sep);
  var oneMenuFs="""
    new_hide = """  hide(split);hide(sep);
  if(!document.body.classList.contains('layout-edit')){
    if(typeof placeCatalogJumpStack==='function')placeCatalogJumpStack();
    return;
  }
  var oneMenuFs="""
    if old_hide not in text:
        raise SystemExit("placePortableHandles hide not found")
    text = text.replace(old_hide, new_hide, 1)

    old_bar_v = "el.style.cssText='display:block;position:fixed;top:'+top+'px;bottom:0;left:'+Math.round(box.x-half)+'px;width:8px;min-width:8px;max-width:8px;height:auto;z-index:90;margin:0;transform:none;pointer-events:auto;cursor:col-resize;background:var(--bg-surface);';"
    new_bar_v = "el.style.cssText='position:fixed;top:'+top+'px;bottom:0;left:'+Math.round(box.x-half)+'px;width:8px;min-width:8px;max-width:8px;height:auto;z-index:90;margin:0;transform:none;pointer-events:auto;cursor:col-resize;background:var(--bg-surface);';el.style.setProperty('display','block','important');"
    old_bar_h = "el.style.cssText='display:block;position:fixed;left:'+Math.round(box.x)+'px;width:'+Math.round(box.w)+'px;top:'+Math.round(box.y-half)+'px;height:8px;min-height:8px;max-height:8px;min-width:0;max-width:none;bottom:auto;z-index:90;margin:0;transform:none;pointer-events:auto;cursor:row-resize;background:var(--bg-surface);';"
    new_bar_h = "el.style.cssText='position:fixed;left:'+Math.round(box.x)+'px;width:'+Math.round(box.w)+'px;top:'+Math.round(box.y-half)+'px;height:8px;min-height:8px;max-height:8px;min-width:0;max-width:none;bottom:auto;z-index:90;margin:0;transform:none;pointer-events:auto;cursor:row-resize;background:var(--bg-surface);';el.style.setProperty('display','block','important');"
    if old_bar_v not in text or old_bar_h not in text:
        raise SystemExit("placePortableHandles bar cssText not found")
    text = text.replace(old_bar_v, new_bar_v, 1)
    text = text.replace(old_bar_h, new_bar_h, 1)

    old_flip = "    var flip=(sides||fs)&&(portrait||phone)&&portraitFlipOn();"
    new_flip = "    var flip=sides&&!document.body.classList.contains('display-content')&&(portrait||phone)&&portraitFlipOn();"
    if old_flip not in text:
        raise SystemExit("applyPortraitSides flip line not found")
    text = text.replace(old_flip, new_flip, 1)
    return text


def main():
    for path in FILES:
        src = path.read_text(encoding="utf-8")
        out = patch(src)
        path.write_text(out, encoding="utf-8")
        print("patched", path.name, "delta", len(out) - len(src))


if __name__ == "__main__":
    main()
