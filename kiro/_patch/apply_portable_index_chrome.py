#!/usr/bin/env python3
"""Portable: desktop-like Index embed/window, ⋯ chrome, portrait scroll, contain art."""
from pathlib import Path

ROOT = Path("/home/phnx/kiro-kontakt-patch")
FILES = [
    ROOT / "public/catalogs/KONTAKT-CATALOG-portable.html",
    ROOT / "public/catalogs/DS-CATALOG-portable.html",
]

CSS_MARK = "/* fix-PORTABLE-INDEX-CHROME:"
CSS_ADD = r"""
/* fix-PORTABLE-INDEX-CHROME: embed vs window like desktop; ⋯ two-row; contain art; one pills scroll */
@media all{
  body.catalog-portable #hdrLayoutBtns,
  body.catalog-portable #hdrLayoutBtns #layoutEditBtn,
  body.catalog-portable #hdrLayoutBtns #layoutPresets,
  body.catalog-portable #hdrLayoutBtns .layout-presets,
  body.catalog-portable #hdrLayoutBtns .layout-presets-btn{
    display:none!important
  }
  body.catalog-portable #hdrLayoutBtns .layout-presets-pop:not([hidden]){
    display:flex!important;position:fixed!important;z-index:430!important
  }
  body.catalog-portable #hdrMenuBtns #portraitFlipBtn,
  body.catalog-portable #hdrCluster #portraitFlipBtn,
  body.catalog-portable #portraitFlipBtn{
    display:inline-flex!important;visibility:visible!important;
    flex:0 0 auto;min-width:2.25rem;order:3
  }
  body.catalog-portable #portraitFlipBtn[hidden]{display:inline-flex!important}
  body.catalog-portable #hdrMorePop:not([hidden]),
  body.catalog-portable .catalog-header>#hdrMorePop:not([hidden]){
    display:flex!important;flex-direction:row!important;flex-wrap:wrap!important;
    align-content:flex-start!important;align-items:stretch!important;gap:.28rem!important;
    overflow-x:hidden!important;overflow-y:auto!important
  }
  body.catalog-portable #hdrMorePop:not([hidden]) button{
    width:auto!important;flex:1 1 calc(50% - .28rem)!important;min-width:calc(50% - .4rem)!important;
    max-width:100%!important;min-height:2.25rem;text-align:center;white-space:nowrap
  }
  body.catalog-portable #hdrMorePop:not([hidden]) label,
  body.catalog-portable #hdrMorePop:not([hidden]) .theme-picker,
  body.catalog-portable #hdrMorePop:not([hidden]) select{
    flex:1 1 100%!important;width:100%!important;min-width:100%!important;max-width:100%!important
  }
  body.catalog-portable.display-sides #catalogIndex:not(.is-embedded):not(.is-collapsed){
    position:relative!important;z-index:12!important;
    height:var(--sides-index-h,min(48dvh,28rem))!important;
    max-height:min(70dvh,40rem)!important;min-height:0!important;
    overflow:hidden!important;flex-shrink:0!important;
    box-shadow:0 10px 24px rgba(0,0,0,.32)!important;border-radius:0 0 10px 10px
  }
  body.catalog-portable.display-sides #catalogIndex:not(.is-embedded):not(.is-collapsed) .index,
  body.catalog-portable.display-sides #catalogIndex:not(.is-embedded):not(.is-collapsed) #catalogIndexList{
    display:grid!important;grid-template-columns:repeat(auto-fill,minmax(min(12rem,100%),1fr))!important;
    grid-auto-flow:row;align-content:start;flex:1 1 auto!important;min-height:0!important;
    overflow-x:hidden!important;overflow-y:auto!important;max-height:none!important;
    columns:none!important;height:auto!important
  }
  body.catalog-portable #catalogIndex.is-embedded,
  body.catalog-portable.display-sides #catalogIndex.is-embedded,
  body.catalog-portable.display-content #catalogIndex.is-embedded{
    position:static!important;height:auto!important;max-height:none!important;
    overflow:visible!important;box-shadow:none!important;border-radius:8px!important;
    flex-shrink:0!important
  }
  body.catalog-portable #catalogIndex.is-embedded:not(.is-collapsed) .index,
  body.catalog-portable #catalogIndex.is-embedded:not(.is-collapsed) #catalogIndexList,
  body.catalog-portable.display-sides #catalogIndex.is-embedded:not(.is-collapsed) .index,
  body.catalog-portable.display-sides #catalogIndex.is-embedded:not(.is-collapsed) #catalogIndexList{
    display:grid!important;grid-template-columns:repeat(auto-fill,minmax(min(12rem,100%),1fr))!important;
    height:auto!important;max-height:none!important;overflow:visible!important;
    flex:0 0 auto!important;min-height:0!important
  }
  body.catalog-portable #catalogIndex.is-embedded #indexHeight{display:none!important}
  body.catalog-portable #catalogIndex.is-embedded .index a,
  body.catalog-portable.display-sides #catalogIndex.is-embedded .index a{
    white-space:normal!important;overflow:visible!important;text-overflow:unset!important;
    overflow-wrap:anywhere!important;word-break:break-word!important;
    -webkit-line-clamp:unset;line-clamp:unset;max-height:none!important
  }
  body.catalog-portable:not(.chosen-preview-open) .entry:not(.highlight) .cover,
  body.catalog-portable .entry:not(.highlight):not(.selected) .cover{
    position:relative!important;display:flex!important;align-items:center!important;justify-content:center!important;
    width:100%!important;max-width:100%!important;aspect-ratio:auto!important;
    height:auto!important;min-height:min(42vw,10.5rem)!important;max-height:min(56vw,18rem)!important;
    overflow:hidden!important;background:var(--bg-surface,var(--bg))!important
  }
  body.catalog-portable:not(.chosen-preview-open) .entry:not(.highlight) .cover img,
  body.catalog-portable .entry:not(.highlight):not(.selected) .cover img{
    position:static!important;inset:auto!important;
    width:auto!important;height:auto!important;
    max-width:100%!important;max-height:min(56vw,18rem)!important;
    min-width:0!important;min-height:0!important;
    object-fit:contain!important;object-position:center center!important
  }
}
@media(orientation:portrait){
  body.catalog-portable:not(.ac-fs-open):not(.kw-fs-open) #catalogMain .catalog-body,
  body.catalog-portable:not(.ac-fs-open):not(.kw-fs-open) #catalogMain .loc-group,
  body.catalog-portable:not(.ac-fs-open):not(.kw-fs-open) #searchPills,
  body.catalog-portable:not(.ac-fs-open):not(.kw-fs-open) .search-active-pills{
    overflow:visible!important;max-height:none!important
  }
  body.catalog-portable:not(.kw-fs-open) #filterWrap .filter-panel,
  body.catalog-portable:not(.kw-fs-open) #filterWrap.open .filter-panel{
    overflow:hidden!important
  }
  body.catalog-portable:not(.kw-fs-open) #kwbar{
    overflow-x:hidden!important;overflow-y:auto!important;min-height:0!important;flex:1 1 auto!important
  }
  body.catalog-portable.display-middle:not(.ac-fs-open) #searchCol,
  body.catalog-portable.display-middle:not(.ac-fs-open) #searchChrome .search-strip-anchor,
  body.catalog-portable.display-middle:not(.ac-fs-open) #acShell{
    overflow:hidden!important
  }
  body.catalog-portable.display-middle:not(.ac-fs-open) #acList{
    overflow-y:auto!important;min-height:0!important;flex:1 1 auto!important
  }
}
"""

REPLACES = [
    (
        """  body.catalog-portable #hdrLayoutBtns{
    display:inline-flex!important;align-items:center;gap:4px;flex:0 0 auto;order:2;min-width:0
  }
  body.catalog-portable #hdrLayoutBtns #layoutEditBtn,
  body.catalog-portable #hdrLayoutBtns #layoutPresets,
  body.catalog-portable #hdrLayoutBtns .layout-presets,
  body.catalog-portable #hdrLayoutBtns .layout-presets-btn{
    display:inline-flex!important;visibility:visible!important
  }""",
        """  body.catalog-portable #hdrLayoutBtns{
    display:none!important
  }
  body.catalog-portable #hdrLayoutBtns #layoutEditBtn,
  body.catalog-portable #hdrLayoutBtns #layoutPresets,
  body.catalog-portable #hdrLayoutBtns .layout-presets,
  body.catalog-portable #hdrLayoutBtns .layout-presets-btn{
    display:none!important
  }""",
    ),
    (
        """  port(fp,'auto');
  port(main,'auto');
  if(ix&&!ix.classList.contains('is-collapsed'))port(ixL||ix,'auto');""",
        """  var fsNow=!!(menuFs==='search'||menuFs==='keywords'||document.body.classList.contains('ac-fs-open')||document.body.classList.contains('kw-fs-open'));
  var kb=document.getElementById('kwbar');
  if(fsNow)port(fp,'auto');
  else{
    if(fp){fp.style.setProperty('overflow','hidden','important');fp.style.setProperty('overflow-y','hidden','important');}
    if(kb)port(kb,'auto');
  }
  port(main,'auto');
  if(ix&&!ix.classList.contains('is-collapsed')){
    if(ix.classList.contains('is-embedded')){
      var ilE=ixL||ix.querySelector('#catalogIndexList,ul.index');
      [ilE,ix].forEach(function(el){
        if(!el)return;
        el.style.setProperty('overflow','visible','important');
        el.style.setProperty('overflow-y','visible','important');
        el.style.setProperty('max-height','none','important');
        el.style.setProperty('height','auto','important');
      });
    }else port(ixL||ix,'auto');
  }
  // #region agent log
  try{
    var rM=main?main.getBoundingClientRect():null;
    fetch('http://127.0.0.1:7529/ingest/1cf46354-1d61-4c80-bd72-a340f1db1b51',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'c00e3e'},body:JSON.stringify({sessionId:'c00e3e',runId:'post-fix',hypothesisId:'I',location:'portable:ensureScroll',message:'index-pills-scroll',data:{embed:!!(ix&&ix.classList.contains('is-embedded')),ixOv:ix?getComputedStyle(ix).overflowY:'',ilOv:ixL?getComputedStyle(ixL).overflowY:'',mainOv:main?getComputedStyle(main).overflowY:'',mainH:rM?Math.round(rM.height):0,mainClient:main?main.clientHeight:0,mainScroll:main?main.scrollHeight:0,fpOv:fp?getComputedStyle(fp).overflowY:'',kbOv:kb?getComputedStyle(kb).overflowY:'',fsNow:fsNow,portrait:!!(window.matchMedia&&window.matchMedia('(orientation:portrait)').matches)},timestamp:Date.now()})}).catch(function(){});
  }catch(eDbgI){}
  // #endregion""",
    ),
    (
        """  pop.style.setProperty('display','flex','important');
  pop.style.setProperty('flex-direction','column','important');""",
        """  pop.style.setProperty('display','flex','important');
  pop.style.setProperty('flex-direction','row','important');
  pop.style.setProperty('flex-wrap','wrap','important');
  pop.style.setProperty('align-content','flex-start','important');""",
    ),
    (
        """  phoneMoreAdd(pop,document.body.classList.contains('layout-edit')?'Done':'Customize',function(){if(typeof toggleLayoutEdit==='function')toggleLayoutEdit();},document.body.classList.contains('layout-edit')?'Done arranging':'Customize layout');
  phoneMoreAdd(pop,'Miss',function(){var x=document.getElementById('clearMissBtn');if(x)x.click();},'Clear on miss');
  phoneMoreAdd(pop,'Flip',function(){if(typeof togglePortraitSidesFlip==='function')togglePortraitSidesFlip();},'Flip panes');
  phoneMoreAdd(pop,'History',function(){var h=document.getElementById('searchHistory');if(h)h.click();},'History');""",
        """  phoneMoreAdd(pop,document.body.classList.contains('layout-edit')?'Done':'Customize',function(){if(typeof toggleLayoutEdit==='function')toggleLayoutEdit();},document.body.classList.contains('layout-edit')?'Done arranging':'Customize layout');
  phoneMoreAdd(pop,'Layouts',function(){var x=document.getElementById('layoutPresetsBtn');if(x)x.click();},'Layouts');
  phoneMoreAdd(pop,'Miss',function(){var x=document.getElementById('clearMissBtn');if(x)x.click();},'Clear on miss');
  phoneMoreAdd(pop,'History',function(){var h=document.getElementById('searchHistory');if(h)h.click();},'History');""",
    ),
    (
        """  portableMoreRowAdd(pop,'History',function(){var h=document.getElementById('searchHistory');if(h)h.click();},'History');
  portableMoreRowAdd(pop,'Fullscreen',function(){if(typeof toggleAcFullscreen==='function')toggleAcFullscreen();},'Fullscreen Search');
  portableMoreRowAdd(pop,document.body.classList.contains('layout-edit')?'Done':'Customize',function(){if(typeof toggleLayoutEdit==='function')toggleLayoutEdit();},document.body.classList.contains('layout-edit')?'Done arranging':'Customize layout');""",
        """  portableMoreRowAdd(pop,'History',function(){var h=document.getElementById('searchHistory');if(h)h.click();},'History');
  portableMoreRowAdd(pop,'Fullscreen',function(){if(typeof toggleAcFullscreen==='function')toggleAcFullscreen();},'Fullscreen Search');""",
    ),
    (
        """  portableMoreRowAdd(pop,document.body.classList.contains('layout-edit')?'Done':'Customize',function(){if(typeof toggleLayoutEdit==='function')toggleLayoutEdit();},document.body.classList.contains('layout-edit')?'Done arranging':'Customize layout');
    portableMoreRowAdd(pop,'Flip',function(){if(typeof togglePortraitSidesFlip==='function')togglePortraitSidesFlip();},'Flip panes');
  portableMoreRowAdd(pop,'Tap',function(){if(typeof toggleTapToAdd==='function')toggleTapToAdd();},'Tap to add');""",
        """  portableMoreRowAdd(pop,'Tap',function(){if(typeof toggleTapToAdd==='function')toggleTapToAdd();},'Tap to add');""",
    ),
    (
        """  var on=ix.classList.toggle('is-embedded');
  if(typeof writeModeSlot==='function')writeModeSlot({indexEmbed:on},'sides');
  if(typeof applyIndexScrollFit==='function')applyIndexScrollFit();
  syncIndexEmbedBtn();
  var cm=document.getElementById('catalogMain');
  if(on&&cm)cm.scrollTop=0;
}""",
        """  var on=ix.classList.toggle('is-embedded');
  if(typeof writeModeSlot==='function')writeModeSlot({indexEmbed:on},'sides');
  if(typeof applyIndexScrollFit==='function')applyIndexScrollFit();
  if(typeof portableEnsureScrollMenus==='function')portableEnsureScrollMenus();
  syncIndexEmbedBtn();
  var cm=document.getElementById('catalogMain');
  if(on&&cm)cm.scrollTop=0;
  // #region agent log
  try{
    var ilT=document.getElementById('catalogIndexList');
    fetch('http://127.0.0.1:7529/ingest/1cf46354-1d61-4c80-bd72-a340f1db1b51',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'c00e3e'},body:JSON.stringify({sessionId:'c00e3e',runId:'post-fix',hypothesisId:'I',location:'portable:toggleIndexEmbed',message:'index embed toggle',data:{on:on,ixOv:getComputedStyle(ix).overflowY,ilOv:ilT?getComputedStyle(ilT).overflowY:'',ixH:Math.round(ix.getBoundingClientRect().height),ilH:ilT?Math.round(ilT.getBoundingClientRect().height):0,ilScroll:ilT?ilT.scrollHeight:0},timestamp:Date.now()})}).catch(function(){});
  }catch(eDbgIx){}
  // #endregion
}""",
    ),
]


def patch_one(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    orig = text
    n = 0
    if CSS_MARK not in text:
        needle = "  body.catalog-portable #portraitFlipBtn[hidden]{display:inline-flex!important}\n}\n</style>"
        if needle not in text:
            raise SystemExit(f"CSS insert point missing in {path.name}")
        text = text.replace(needle, needle.replace("</style>", CSS_ADD + "</style>"), 1)
        n += 1
    for old, new in REPLACES:
        if old not in text:
            raise SystemExit(f"Missing snippet in {path.name}:\n{old[:120]}")
        c = text.count(old)
        text = text.replace(old, new)
        n += c
    if text == orig:
        print(f"{path.name}: no change")
        return
    path.write_text(text, encoding="utf-8")
    print(f"{path.name}: {n} replacements")


def main() -> None:
    for p in FILES:
        patch_one(p)


if __name__ == "__main__":
    main()
