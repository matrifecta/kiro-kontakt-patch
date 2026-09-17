#!/usr/bin/env python3
"""Portable: in-flow toolbar expanders, no UI scale, short labels."""
from pathlib import Path

ROOT = Path("/home/phnx/kiro-kontakt-patch")
FILES = [
    ROOT / "public/catalogs/DS-CATALOG-portable.html",
    ROOT / "public/catalogs/KONTAKT-CATALOG-portable.html",
]

CSS_MARK = "/* fix-PORTABLE-EMBED-CHROME: in-flow expanders, no scale, short labels */"
CSS = r"""
/* fix-PORTABLE-EMBED-CHROME: in-flow expanders, no scale, short labels */
@media all{
  body.catalog-portable .search-only-scale,
  body.catalog-portable #searchOnlyScale,
  body.catalog-portable #searchOnlyScalePop,
  body.catalog-portable #uiScale,
  body.catalog-portable #uiScalePop,
  body.catalog-portable .fs-stripe-scale,
  body.catalog-portable .filter-kw-tools,
  body.catalog-portable #layoutEditBtn,
  body.catalog-portable #layoutPresets,
  body.catalog-portable .layout-presets,
  body.catalog-portable .layout-presets-pop{display:none!important}
  body.catalog-portable .catalog-header{
    overflow:visible!important;
    grid-template-rows:auto auto!important
  }
  body.catalog-portable .hdr-cluster{
    flex-wrap:wrap!important;min-width:0;max-width:100%;overflow:visible!important
  }
  body.catalog-portable .catalog-header>#hdrMorePop,
  body.catalog-portable #searchStripMorePop,
  body.catalog-portable #kwStripMorePop,
  body.catalog-portable .hdr-more-pop,
  body.catalog-portable .kw-strip-more-pop,
  body.catalog-portable .search-strip-more-pop{
    position:static!important;inset:auto!important;top:auto!important;right:auto!important;left:auto!important;
    float:none!important;transform:none!important;
    flex:1 1 100%;width:100%!important;max-width:100%!important;min-width:0!important;
    max-height:min(42dvh,18rem);overflow-x:hidden;overflow-y:auto;-webkit-overflow-scrolling:touch;
    z-index:6!important;box-shadow:none!important;margin:.3rem 0 0;box-sizing:border-box;order:99
  }
  body.catalog-portable .catalog-header>#hdrMorePop{
    grid-column:1/-1!important;grid-row:2!important;flex:none;width:100%!important
  }
  body.catalog-portable #searchStripMore{display:inline-flex!important}
  body.catalog-portable #hdrMorePop:not([hidden]),
  body.catalog-portable #searchStripMorePop:not([hidden]),
  body.catalog-portable #kwStripMorePop:not([hidden]),
  body.catalog-portable .hdr-more-pop:not([hidden]),
  body.catalog-portable .kw-strip-more-pop:not([hidden]),
  body.catalog-portable .search-strip-more-pop:not([hidden]){
    display:flex!important;flex-direction:column
  }
  body.catalog-portable #searchStrip,
  body.catalog-portable #filterTop{
    flex-wrap:wrap!important;overflow:visible!important;align-items:center
  }
  body.catalog-portable .search-strip-hide,
  body.catalog-portable .kw-strip-hide,
  body.catalog-portable #clearMissBtn,
  body.catalog-portable .tap-add-btn,
  body.catalog-portable #filterToggle{white-space:nowrap;overflow:hidden;text-overflow:ellipsis;min-width:0}
}
@media(orientation:portrait){
  body.catalog-portable .hdr-cluster{grid-column:1/-1!important}
  body.catalog-portable .catalog-header{grid-template-rows:auto auto auto!important}
  body.catalog-portable .catalog-header>#hdrMorePop{grid-row:3!important}
}
"""

SEARCH_MORE_OLD = """function toggleSearchStripMore(){
  var pop=document.getElementById('searchStripMorePop');
  var btn=document.getElementById('searchStripMore');
  if(!pop||!btn)return;
  var open=pop.hasAttribute('hidden');
  if(open){
    pop.innerHTML='';
    function add(label,fn){var b=document.createElement('button');b.type='button';b.textContent=label;b.addEventListener('click',function(e){e.preventDefault();e.stopPropagation();pop.setAttribute('hidden','');btn.setAttribute('aria-expanded','false');fn();});pop.appendChild(b);}
    add('Smaller Search',function(){if(typeof stepSearchOnlyUiScale==='function')stepSearchOnlyUiScale(-1);});
    add('Larger Search',function(){if(typeof stepSearchOnlyUiScale==='function')stepSearchOnlyUiScale(1);});
    if(typeof isPhoneViewport==='function'&&isPhoneViewport()){
      add('Clear search',function(){if(typeof clearAllFilters==='function')clearAllFilters();});
      add('History',function(){var h=document.getElementById('searchHistory');if(h)h.click();});
    }
    pop.removeAttribute('hidden');
    btn.setAttribute('aria-expanded','true');
  }else{
    pop.setAttribute('hidden','');
    btn.setAttribute('aria-expanded','false');
  }
}"""

SEARCH_MORE_NEW = """function toggleSearchStripMore(){
  var pop=document.getElementById('searchStripMorePop');
  var btn=document.getElementById('searchStripMore');
  if(!pop||!btn)return;
  var open=pop.hasAttribute('hidden');
  if(typeof closePhoneOverflowPops==='function')closePhoneOverflowPops('searchStripMorePop');
  if(open){
    pop.innerHTML='';
    function add(label,fn,aria){var b=document.createElement('button');b.type='button';b.textContent=label;if(aria)b.setAttribute('aria-label',aria);b.addEventListener('click',function(e){e.preventDefault();e.stopPropagation();pop.setAttribute('hidden','');btn.setAttribute('aria-expanded','false');fn();});pop.appendChild(b);}
    add('Clear',function(){if(typeof clearAllFilters==='function')clearAllFilters();},'Clear search');
    add('H',function(){var h=document.getElementById('searchHistory');if(h)h.click();},'History');
    add('Pick',function(){if(typeof setMode==='function')setMode('pick');});
    add('Search',function(){if(typeof setMode==='function')setMode('search');});
    pop.removeAttribute('hidden');
    btn.setAttribute('aria-expanded','true');
    // #region agent log
    if(typeof dbgMobileUi==='function')dbgMobileUi('search-more',{hyp:'H-CHROME'});
    // #endregion
  }else{
    pop.setAttribute('hidden','');
    btn.setAttribute('aria-expanded','false');
  }
}"""

HDR_MORE_OLD = """  pop.innerHTML='';
  phoneMoreAdd(pop,'Clear on miss',function(){var x=document.getElementById('clearMissBtn');if(x)x.click();});
  phoneMoreAdd(pop,'Flip panes',function(){if(typeof togglePortraitSidesFlip==='function')togglePortraitSidesFlip();});
  phoneMoreAdd(pop,'Smaller UI',function(){if(typeof stepUiScale==='function')stepUiScale(-1);});
  phoneMoreAdd(pop,'Larger UI',function(){if(typeof stepUiScale==='function')stepUiScale(1);});
  var sel=document.getElementById('themePicker');"""

HDR_MORE_NEW = """  var hdr=document.querySelector('.catalog-header');
  if(hdr&&pop.parentElement!==hdr)hdr.appendChild(pop);
  pop.innerHTML='';
  phoneMoreAdd(pop,'Miss',function(){var x=document.getElementById('clearMissBtn');if(x)x.click();},'Clear on miss');
  phoneMoreAdd(pop,'Flip',function(){if(typeof togglePortraitSidesFlip==='function')togglePortraitSidesFlip();},'Flip panes');
  var sel=document.getElementById('themePicker');"""

KW_MORE_OLD = """  pop.innerHTML='';
  phoneMoreAdd(pop,'Flip panes',function(){if(typeof togglePortraitSidesFlip==='function')togglePortraitSidesFlip();});
  phoneMoreAdd(pop,'Smaller UI',function(){if(typeof stepUiScale==='function')stepUiScale(-1);});
  phoneMoreAdd(pop,'Larger UI',function(){if(typeof stepUiScale==='function')stepUiScale(1);});
  phoneMoreAdd(pop,'Tap to add',function(){if(typeof toggleTapToAdd==='function')toggleTapToAdd();});
  phoneMoreAdd(pop,'Clear keywords',function(){if(typeof clearAllFilters==='function')clearAllFilters();});"""

KW_MORE_NEW = """  pop.innerHTML='';
  phoneMoreAdd(pop,'Flip',function(){if(typeof togglePortraitSidesFlip==='function')togglePortraitSidesFlip();},'Flip panes');
  phoneMoreAdd(pop,'Tap',function(){if(typeof toggleTapToAdd==='function')toggleTapToAdd();},'Tap to add');
  phoneMoreAdd(pop,'Clear',function(){if(typeof clearAllFilters==='function')clearAllFilters();},'Clear keywords');
  phoneMoreAdd(pop,'Pick',function(){if(typeof setMode==='function')setMode('pick');});
  phoneMoreAdd(pop,'Search',function(){if(typeof setMode==='function')setMode('search');});"""

PHONE_ADD_OLD = """function phoneMoreAdd(pop,label,fn){
  var b=document.createElement('button');b.type='button';b.textContent=label;
  b.addEventListener('click',function(e){e.preventDefault();e.stopPropagation();closePhoneOverflowPops();fn();});
  pop.appendChild(b);
}"""

PHONE_ADD_NEW = """function phoneMoreAdd(pop,label,fn,aria){
  var b=document.createElement('button');b.type='button';b.textContent=label;
  if(aria)b.setAttribute('aria-label',aria);
  b.addEventListener('click',function(e){e.preventDefault();e.stopPropagation();closePhoneOverflowPops();fn();});
  pop.appendChild(b);
}"""

HIDE_S_OLD = """    b.textContent=collapsed?'Search':'Hide Search';
    b.setAttribute('aria-expanded',collapsed?'false':'true');
    b.setAttribute('aria-label',collapsed?'Search':'Hide Search');"""

HIDE_S_NEW = """    b.textContent=collapsed?'Search':(window.CATALOG_PORTABLE?'Hide':'Hide Search');
    b.setAttribute('aria-expanded',collapsed?'false':'true');
    b.setAttribute('aria-label',collapsed?'Search':'Hide Search');"""

HIDE_K_OLD = """    b.textContent=hidden?'Keywords':'Hide Keywords';
    b.setAttribute('aria-expanded',hidden?'false':'true');
    b.setAttribute('aria-label',hidden?'Keywords':'Hide Keywords');"""

HIDE_K_NEW = """    b.textContent=hidden?(window.CATALOG_PORTABLE?'KW':'Keywords'):(window.CATALOG_PORTABLE?'Hide':'Hide Keywords');
    b.setAttribute('aria-expanded',hidden?'false':'true');
    b.setAttribute('aria-label',hidden?'Keywords':'Hide Keywords');"""

ENSURE_OLD = """        var hp=document.createElement('div');hp.className='hdr-more-pop';hp.id='hdrMorePop';hp.hidden=true;
        cluster.insertBefore(hb,sw);cluster.insertBefore(hp,sw);"""

ENSURE_NEW = """        var hp=document.createElement('div');hp.className='hdr-more-pop';hp.id='hdrMorePop';hp.hidden=true;
        cluster.insertBefore(hb,sw);
        var hdrEl=document.querySelector('.catalog-header');
        if(hdrEl)hdrEl.appendChild(hp);else cluster.insertBefore(hp,sw);"""


def patch(text: str) -> str:
    if CSS_MARK not in text:
        needle = "</style></head>"
        if needle not in text:
            raise SystemExit("missing style close")
        text = text.replace(needle, CSS + needle, 1)
    swaps = [
        (SEARCH_MORE_OLD, SEARCH_MORE_NEW),
        (HDR_MORE_OLD, HDR_MORE_NEW),
        (KW_MORE_OLD, KW_MORE_NEW),
        (PHONE_ADD_OLD, PHONE_ADD_NEW),
        (HIDE_S_OLD, HIDE_S_NEW),
        (HIDE_K_OLD, HIDE_K_NEW),
        (ENSURE_OLD, ENSURE_NEW),
        (">Clear on miss</button>", ">Miss</button>"),
        ('placeholder="Search libraries..."', 'placeholder="Search…"'),
        (">Hide Search</button>", ">Hide</button>"),
        (">Hide Keywords</button>", ">Hide</button>"),
        ("> Keywords</button>", "> KW</button>"),
        (">Tap to add</button>", ">Tap</button>"),
        ('title="Fullscreen search"', 'title="Full"'),
        ('title="Fullscreen Keywords"', 'title="Full"'),
        ('aria-label="Fullscreen search"', 'aria-label="Fullscreen search"'),
        ('aria-label="Fullscreen Keywords"', 'aria-label="Fullscreen Keywords"'),
    ]
    for old, new in swaps:
        if old not in text:
            raise SystemExit("missing snippet:\n" + old[:160])
        text = text.replace(old, new)
    return text


def main():
    for path in FILES:
        raw = path.read_text(encoding="utf-8")
        out = patch(raw)
        path.write_text(out, encoding="utf-8")
        print("patched", path.name, "delta", len(out) - len(raw))


if __name__ == "__main__":
    main()
