#!/usr/bin/env python3
"""Sides Save beside pin cluster; cover 0x0 revive; Index closed unless arrow.

Syncs the six catalog HTML/builder files. Does not commit.
Keeps existing restore-defaults / pin-fit instrumentation.
"""
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

INGEST = "http://127.0.0.1:7529/ingest/1cf46354-1d61-4c80-bd72-a340f1db1b51"


def sub(text, old, new, label, path, count=1, optional=False):
    if new in text:
        print(f"  skip {path.name} {label}")
        return text
    n = text.count(old)
    if n == count:
        return text.replace(old, new)
    if optional and n == 0:
        print(f"  skip {path.name} {label} (absent)")
        return text
    raise SystemExit(f"{path.name}: {label} count={n} expected {count}")


COVER_CSS_OLD = (
    " .cover{flex-shrink:0;width:100%;max-width:100%;max-height:clamp(7.5rem,18vw,12.5rem);margin:.3rem 0;display:flex;align-items:center;justify-content:center;overflow:hidden;border:1px solid var(--border);border-radius:4px;background:var(--bg-surface);box-sizing:border-box;cursor:pointer}\n"
    " .cover img{width:auto;height:auto;max-width:100%;max-height:clamp(7.5rem,18vw,12.5rem);object-fit:contain;object-position:center center;display:block}\n"
)
COVER_CSS_NEW = (
    " .cover{flex:0 0 auto;flex-shrink:0;width:100%;max-width:100%;min-height:clamp(4.5rem,12vw,7.5rem);max-height:clamp(7.5rem,18vw,12.5rem);margin:.3rem 0;display:flex;align-items:center;justify-content:center;overflow:hidden;border:1px solid var(--border);border-radius:4px;background:var(--bg-surface);box-sizing:border-box;cursor:pointer}\n"
    " .cover img{width:auto;height:auto;min-width:0;min-height:4.5rem;max-width:100%;max-height:clamp(7.5rem,18vw,12.5rem);object-fit:contain;object-position:center center;display:block;visibility:visible}\n"
)

COVER_VIS_OLD = ".entry>.cover>img,.entry .cover>img{display:block;visibility:visible;max-width:100%}\n"
COVER_VIS_NEW = ".entry>.cover>img,.entry .cover>img{display:block;visibility:visible;max-width:100%;min-height:4.5rem;height:auto}\n"

SAVE_CSS_OLD = (
    "#cardMinDock .card-min-save{pointer-events:auto;position:absolute;right:.75rem;bottom:max(.85rem,env(safe-area-inset-bottom));display:inline-flex;align-items:center;justify-content:center;min-height:2.85rem;padding:0 .8rem;border:1px solid var(--accent-instrument);border-radius:999px;background:var(--bg-card);color:var(--accent-instrument);font:inherit;font-size:.9rem;font-weight:650;cursor:pointer;touch-action:manipulation;box-shadow:0 8px 28px rgba(0,0,0,.38);z-index:1}\n"
)
SAVE_CSS_NEW = (
    "#cardMinDock .card-min-save{pointer-events:auto;position:absolute;right:.75rem;bottom:max(.85rem,env(safe-area-inset-bottom));display:inline-flex;align-items:center;justify-content:center;min-height:2.85rem;padding:0 .8rem;border:1px solid var(--accent-instrument);border-radius:999px;background:var(--bg-card);color:var(--accent-instrument);font:inherit;font-size:.9rem;font-weight:650;cursor:pointer;touch-action:manipulation;box-shadow:0 8px 28px rgba(0,0,0,.38);z-index:1}\n"
    "body.display-middle #cardMinDock .card-min-save,body.display-sides #cardMinDock .card-min-save{right:auto;left:calc(50% + (var(--card-min-stack-w,0px) / 2) + .45rem)}\n"
)

HEAD_CUR_OLD = "  body.display-sides #catalogIndex .catalog-index-head{flex:0 0 auto;margin:0;padding:.45rem .7rem;cursor:pointer;border-bottom:1px solid var(--border);user-select:none;min-width:0;position:relative;z-index:12}\n"
HEAD_CUR_NEW = "  body.display-sides #catalogIndex .catalog-index-head{flex:0 0 auto;margin:0;padding:.45rem .7rem;cursor:default;border-bottom:1px solid var(--border);user-select:none;min-width:0;position:relative;z-index:12}\n"

IX_HTML_OLD = (
    '<div class="catalog-index" id="catalogIndex"><div class="catalog-index-head">'
    '<button type="button" class="catalog-index-toggle" id="catalogIndexToggle" '
    'aria-label="Collapse index" aria-expanded="true" title="Collapse index" '
)
IX_HTML_NEW = (
    '<div class="catalog-index is-collapsed" id="catalogIndex"><div class="catalog-index-head">'
    '<button type="button" class="catalog-index-toggle" id="catalogIndexToggle" '
    'aria-label="Expand index" aria-expanded="false" title="Expand index" '
)

SAVE_PLACE_OLD = """    if(middle){
      if(fitsRight)setLeft(leftBeside);
      else if(fitsLeft)setLeft(leftOf);
      else liftAbove();
    }else{
      setRightCss();
      if(hits()){
        if(fitsRight)setLeft(leftBeside);
        else if(fitsLeft)setLeft(leftOf);
        else liftAbove();
      }
    }
  }else setRightCss();
  if(hits())liftAbove();
}
"""

SAVE_PLACE_NEW = """    if(fitsRight)setLeft(leftBeside);
    else if(fitsLeft)setLeft(leftOf);
    else liftAbove();
  }else setRightCss();
  if(hits())liftAbove();
  // #region agent log
  try{var sb=sav.getBoundingClientRect();var sr2=stack?stack.getBoundingClientRect():null;var kwEl=document.getElementById('filterWrap');var kwr=kwEl?kwEl.getBoundingClientRect():null;var path=(!sr||sr.width<=8)?'right-css':((sav.style.left&&sav.style.left!=='auto')?'beside':'right-css');if(!window._dbgSaveAt||Date.now()-window._dbgSaveAt>400){window._dbgSaveAt=Date.now();fetch('""" + INGEST + """',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'c00e3e'},body:JSON.stringify({sessionId:'c00e3e',runId:'post-fix',hypothesisId:'H-save',location:'catalog:cardMinPlaceSave',message:'save-place',data:{mode:document.body.classList.contains('display-middle')?'middle':(document.body.classList.contains('display-sides')?'sides':'other'),n:(typeof cardMinDockItems!=='undefined'&&cardMinDockItems)?cardMinDockItems.length:0,path:path,left:sav.style.left||'',right:sav.style.right||'',saveL:Math.round(sb.left),stackR:sr2?Math.round(sr2.right):0,gap:sr2?Math.round(sb.left-sr2.right):null,hit:hits(),kwHit:!!(kwr&&kwr.width>4&&typeof cardMinRectsOverlap==='function'&&cardMinRectsOverlap(sb,kwr,4)),vw:window.innerWidth||0},timestamp:Date.now()})}).catch(function(){});}}catch(eLog){}
  // #endregion
}
"""

CHROME_OLD = "    ['catalogJumpStack','searchHistory'].forEach(function(id){\n"
CHROME_NEW = "    ['catalogJumpStack','searchHistory','filterWrap'].forEach(function(id){\n"

REVIVE_OLD = """function reviveEntryCovers(){
  document.querySelectorAll('.entry .cover > img').forEach(function(img){
    var src=img.getAttribute('src')||'';
    var pin=img.getAttribute('data-cover-src')||'';
    if(src&&src!=='about:blank'&&!pin){img.setAttribute('data-cover-src',src);pin=src;}
    if((!src||src==='about:blank'||!(img.complete&&img.naturalWidth>0))&&pin){
      img.src=pin;
    }
  });
}
window.reviveEntryCovers=reviveEntryCovers;
"""

REVIVE_NEW = """function dbgCoverCensus(phase,extra){
  // #region agent log
  try{
    var now=Date.now();
    if(window._dbgCoverAt&&now-window._dbgCoverAt<250&&window._dbgCoverPh===phase)return;
    window._dbgCoverAt=now;window._dbgCoverPh=phase;
    var n=0,withImg=0,naturalOk=0,boxOk=0,zeroBox=0,emptySrc=0,noCover=0,tiny=0,samples=[];
    var clipped=0,tinySrc=0,dupMax=0,srcHash={};
    document.querySelectorAll('.entry').forEach(function(el){
      n++;
      var img=el.querySelector(':scope > .cover > img')||el.querySelector('.cover > img');
      if(!img){noCover++;return;}
      withImg++;
      var src=img.getAttribute('src')||'';
      if(!src||src==='about:blank')emptySrc++;
      var nat=img.naturalWidth||0;
      if(nat>0)naturalOk++;
      var box=(img.parentElement||img).getBoundingClientRect();
      var er=el.getBoundingClientRect();
      if(box.width>=8&&box.height>=8){
        boxOk++;
        if(box.bottom<er.top+2||box.top>er.bottom-2)clipped++;
      } else if(samples.length<6){zeroBox++;samples.push({id:el.id||'',name:(el.getAttribute('data-name')||'').slice(0,40),w:Math.round(box.width),h:Math.round(box.height),nat:nat,srcLen:(src||'').length});}
      else zeroBox++;
      if(nat>0&&box.width>=8&&box.height>0&&box.height<20)tiny++;
      if(src&&src.length<3600)tinySrc++;
      var hk=(src||'').length+':'+(src||'').slice(80,140);
      if(src){srcHash[hk]=(srcHash[hk]||0)+1;if(srcHash[hk]>dupMax)dupMax=srcHash[hk];}
    });
    var uiScale=0;try{uiScale=parseFloat(getComputedStyle(document.documentElement).getPropertyValue('--ui-scale'))||0;}catch(eSc){}
    extra=extra||{};
    fetch('""" + INGEST + """',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'c00e3e'},body:JSON.stringify({sessionId:'c00e3e',runId:'post-fix',hypothesisId:'H-cover',location:'catalog:dbgCoverCensus',message:'cover-census',data:{phase:String(phase||''),n:n,withImg:withImg,naturalOk:naturalOk,boxOk:boxOk,zeroBox:zeroBox,emptySrc:emptySrc,noCover:noCover,tiny:tiny,clipped:clipped,tinySrc:tinySrc,dupMax:dupMax,uiScale:uiScale,revived:extra.revived||0,boxFix:extra.boxFix||0,samples:samples,mode:document.body.classList.contains('display-middle')?'middle':(document.body.classList.contains('display-sides')?'sides':'other'),vw:window.innerWidth||0},timestamp:Date.now()})}).catch(function(){});
  }catch(eLog){}
  // #endregion
}
function reviveEntryCovers(phase){
  var revived=0,boxFix=0;
  document.querySelectorAll('.entry .cover').forEach(function(box){
    var img=box.querySelector(':scope > img')||box.querySelector('img');
    if(!img)return;
    var src=img.getAttribute('src')||'';
    var pin=img.getAttribute('data-cover-src')||'';
    if(src&&src!=='about:blank'&&!pin){img.setAttribute('data-cover-src',src);pin=src;}
    if((!src||src==='about:blank'||!(img.complete&&img.naturalWidth>0))&&pin){
      img.src=pin;revived++;
    }
    var br=box.getBoundingClientRect();
    if(br.height<8||box.style.height==='0px'||img.style.height==='0px'||img.style.display==='none'){
      box.style.removeProperty('height');box.style.removeProperty('min-height');box.style.removeProperty('max-height');box.style.removeProperty('display');box.style.removeProperty('flex');
      img.style.removeProperty('height');img.style.removeProperty('width');img.style.removeProperty('display');img.style.removeProperty('max-height');
      img.style.visibility='visible';
      boxFix++;
    }
  });
  if(typeof dbgCoverCensus==='function')dbgCoverCensus(phase||'revive',{revived:revived,boxFix:boxFix});
}
window.dbgCoverCensus=dbgCoverCensus;
window.reviveEntryCovers=reviveEntryCovers;
"""

RESET_OLD = """function resetIndexDock(){
  var ix=document.getElementById('catalogIndex');
  var il=document.getElementById('catalogIndexList')||(ix&&ix.querySelector('ul.index'));
  if(!ix)return;
  ix.classList.remove('is-collapsed');
  ix.dataset.dockAuto='';
  ix.dataset.dockPin='';
  ix.dataset.goingTop='';
  try{delete ix.dataset.ixFitInner;}catch(err){ix.dataset.ixFitInner='';}
  if(typeof syncIndexToggleUi==='function')syncIndexToggleUi(ix);
  if(il)il.scrollTop=0;
  var cm=document.getElementById('catalogMain');
  if(cm)cm.scrollTop=0;
  if(typeof applyIndexScrollFit==='function')applyIndexScrollFit();

}
window.syncKwHideBtn=syncKwHideBtn;
"""

RESET_NEW = """function dbgIndexGate(reason,hyp,extra){
  // #region agent log
  try{
    var ix=document.getElementById('catalogIndex');
    var collapsed=!!(ix&&ix.classList.contains('is-collapsed'));
    var payload={reason:String(reason||''),collapsed:collapsed,open:!collapsed,mode:document.body.classList.contains('display-middle')?'middle':(document.body.classList.contains('display-sides')?'sides':'other')};
    if(extra){Object.keys(extra).forEach(function(k){payload[k]=extra[k];});}
    fetch('""" + INGEST + """',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'c00e3e'},body:JSON.stringify({sessionId:'c00e3e',runId:'post-fix',hypothesisId:hyp||'H-idx',location:'catalog:dbgIndexGate',message:'index-gate',data:payload,timestamp:Date.now()})}).catch(function(){});
  }catch(eLog){}
  // #endregion
}
function forceCatalogIndexClosed(reason){
  var ix=document.getElementById('catalogIndex');
  if(!ix)return;
  ix.classList.add('is-collapsed');
  ix.dataset.dockAuto='';
  ix.dataset.dockPin='';
  if(typeof syncIndexToggleUi==='function')syncIndexToggleUi(ix);
  if(typeof dbgIndexGate==='function')dbgIndexGate(reason||'force-close','H2');
}
function resetIndexDock(){
  var ix=document.getElementById('catalogIndex');
  var il=document.getElementById('catalogIndexList')||(ix&&ix.querySelector('ul.index'));
  if(!ix)return;
  ix.classList.add('is-collapsed');
  ix.dataset.dockAuto='';
  ix.dataset.dockPin='';
  ix.dataset.goingTop='';
  try{delete ix.dataset.ixFitInner;}catch(err){ix.dataset.ixFitInner='';}
  if(typeof syncIndexToggleUi==='function')syncIndexToggleUi(ix);
  if(il)il.scrollTop=0;
  var cm=document.getElementById('catalogMain');
  if(cm)cm.scrollTop=0;
  if(typeof applyIndexScrollFit==='function')applyIndexScrollFit();
  if(typeof dbgIndexGate==='function')dbgIndexGate('reset-dock','H2');
}
window.dbgIndexGate=dbgIndexGate;
window.forceCatalogIndexClosed=forceCatalogIndexClosed;
window.syncKwHideBtn=syncKwHideBtn;
"""

TOGGLE_OLD = """window.toggleCatalogIndex=function(){
  var box=document.getElementById('catalogIndex');
  if(!box)return;
  var collapsed=box.classList.toggle('is-collapsed');
"""
TOGGLE_NEW = """window.toggleCatalogIndex=function(){
  var box=document.getElementById('catalogIndex');
  if(!box)return;
  var collapsed=box.classList.toggle('is-collapsed');
  if(typeof dbgIndexGate==='function')dbgIndexGate('arrow-toggle','H-arrow',{collapsed:collapsed,src:'toggle-btn'});
"""

SLOT_OLD = """        if(typeof slot.indexEmbed==='boolean')ixSlot.classList.toggle('is-embedded',!!slot.indexEmbed);
        if(typeof slot.indexCollapsed==='boolean')ixSlot.classList.toggle('is-collapsed',!!slot.indexCollapsed);
        if(typeof syncIndexToggleUi==='function')syncIndexToggleUi(ixSlot);
"""
SLOT_NEW = """        if(typeof slot.indexEmbed==='boolean')ixSlot.classList.toggle('is-embedded',!!slot.indexEmbed);
        ixSlot.classList.add('is-collapsed');
        if(typeof syncIndexToggleUi==='function')syncIndexToggleUi(ixSlot);
        if(typeof dbgIndexGate==='function')dbgIndexGate('apply-mode-slot','H1',{hadSlot:typeof slot.indexCollapsed==='boolean',slotCollapsed:slot.indexCollapsed});
"""

SNAP_OLD = """      if(typeof snap.indexEmbed==='boolean')ix.classList.toggle('is-embedded',!!snap.indexEmbed);
      if(typeof snap.indexCollapsed==='boolean')ix.classList.toggle('is-collapsed',!!snap.indexCollapsed);
"""
SNAP_NEW = """      if(typeof snap.indexEmbed==='boolean')ix.classList.toggle('is-embedded',!!snap.indexEmbed);
      ix.classList.add('is-collapsed');
      if(typeof dbgIndexGate==='function')dbgIndexGate('named-layout','H4',{hadSnap:typeof snap.indexCollapsed==='boolean',snapCollapsed:snap.indexCollapsed});
"""

BUCKET_OLD = """    if(typeof b.indexCollapsed==='boolean'){ix.classList.toggle('is-collapsed',!!b.indexCollapsed);if(typeof syncIndexToggleUi==='function')syncIndexToggleUi(ix);}
    if(typeof b.indexEmbed==='boolean'){ix.classList.toggle('is-embedded',!!b.indexEmbed);if(typeof syncIndexEmbedBtn==='function')syncIndexEmbedBtn();}
"""
BUCKET_NEW = """    ix.classList.add('is-collapsed');if(typeof syncIndexToggleUi==='function')syncIndexToggleUi(ix);
    if(typeof b.indexEmbed==='boolean'){ix.classList.toggle('is-embedded',!!b.indexEmbed);if(typeof syncIndexEmbedBtn==='function')syncIndexEmbedBtn();}
    if(typeof dbgIndexGate==='function')dbgIndexGate('layout-bucket','H5',{hadBucket:typeof b.indexCollapsed==='boolean',bucketCollapsed:b.indexCollapsed});
"""

HEAD_CLICK_OLD = """    if(head)head.addEventListener('click',function(e){
      if(!document.body.classList.contains('display-sides'))return;
      if(e.target.closest&&e.target.closest('#catalogIndexToggle'))return;
      if(typeof toggleCatalogIndex==='function')toggleCatalogIndex();
    });
"""
HEAD_CLICK_NEW = """    /* Index opens only via #catalogIndexToggle */
"""

BOOT_OLD = """  setDisplayMode(m);
  try{lastDisplayOrient=typeof displayOrientId==='function'?displayOrientId():lastDisplayOrient;}catch(err){}
"""
BOOT_NEW = """  setDisplayMode(m);
  if(typeof forceCatalogIndexClosed==='function')forceCatalogIndexClosed('boot');
  try{lastDisplayOrient=typeof displayOrientId==='function'?displayOrientId():lastDisplayOrient;}catch(err){}
"""

PIN_COVERS_OLD = "  function pinCovers(){if(typeof reviveEntryCovers==='function')reviveEntryCovers();}\n"
PIN_COVERS_NEW = "  function pinCovers(){if(typeof reviveEntryCovers==='function')reviveEntryCovers('boot');}\n"

SCR_OLD = "    function onScr(){var now=Date.now();if(now-last<1500)return;last=now;if(typeof reviveEntryCovers==='function')reviveEntryCovers();}\n"
SCR_NEW = "    function onScr(){var now=Date.now();if(now-last<1500)return;last=now;if(typeof reviveEntryCovers==='function')reviveEntryCovers('scroll');}\n"

PREVIEW_OLD = """  if(typeof window.rehideSearchNonHits==='function')window.rehideSearchNonHits(last);
}
var previewPh=null;
"""
PREVIEW_NEW = """  if(typeof window.rehideSearchNonHits==='function')window.rehideSearchNonHits(last);
  if(typeof reviveEntryCovers==='function')reviveEntryCovers('after-preview');
}
var previewPh=null;
"""

OVERLAY_OLD = """  if(!opts.skipScroll)jumpOrigin=null;
}
function switchOverlayTo(el){
"""
OVERLAY_NEW = """  if(!opts.skipScroll)jumpOrigin=null;
  if(typeof reviveEntryCovers==='function')reviveEntryCovers('after-overlay');
}
function switchOverlayTo(el){
"""


def patch(path: Path):
    t = path.read_text(encoding="utf-8")
    t = sub(t, COVER_CSS_OLD, COVER_CSS_NEW, "cover-css", path)
    t = sub(t, COVER_VIS_OLD, COVER_VIS_NEW, "cover-vis", path)
    t = sub(t, SAVE_CSS_OLD, SAVE_CSS_NEW, "save-css", path)
    t = sub(t, HEAD_CUR_OLD, HEAD_CUR_NEW, "index-head-cursor", path)
    t = sub(t, IX_HTML_OLD, IX_HTML_NEW, "index-html-collapsed", path)
    t = sub(t, CHROME_OLD, CHROME_NEW, "save-chrome-kw", path)
    t = sub(t, SAVE_PLACE_OLD, SAVE_PLACE_NEW, "save-place-unify", path)
    t = sub(t, REVIVE_OLD, REVIVE_NEW, "revive-covers", path)
    t = sub(t, RESET_OLD, RESET_NEW, "reset-index-dock", path)
    t = sub(t, TOGGLE_OLD, TOGGLE_NEW, "toggle-index-log", path)
    t = sub(t, SLOT_OLD, SLOT_NEW, "mode-slot-index", path)
    t = sub(t, SNAP_OLD, SNAP_NEW, "snapshot-index", path)
    t = sub(t, BUCKET_OLD, BUCKET_NEW, "bucket-index", path)
    t = sub(t, HEAD_CLICK_OLD, HEAD_CLICK_NEW, "index-head-click", path)
    t = sub(t, BOOT_OLD, BOOT_NEW, "boot-index-closed", path)
    t = sub(t, PIN_COVERS_OLD, PIN_COVERS_NEW, "pin-covers-boot", path)
    t = sub(t, SCR_OLD, SCR_NEW, "scroll-covers", path, optional=True)
    t = sub(t, PREVIEW_OLD, PREVIEW_NEW, "preview-revive", path)
    t = sub(t, OVERLAY_OLD, OVERLAY_NEW, "overlay-revive", path)
    t = sub(t, "<title>DecentSampler Library Catalog</title>", "<title>Decent Sampler Library</title>", "ds-title", path, optional=True)
    t = sub(t, '<h1 id="top">DecentSampler Library Catalog</h1>', '<h1 id="top">Decent Sampler Library</h1>', "ds-h1", path, optional=True)
    t = sub(t, "<title>Kontakt Library Catalog</title>", "<title>Kontakt Library</title>", "kontakt-title", path, optional=True)
    t = sub(t, '<h1 id="top">Kontakt Library Catalog</h1>', '<h1 id="top">Kontakt Library</h1>', "kontakt-h1", path, optional=True)
    if "forceCatalogIndexClosed" not in t:
        raise SystemExit(f"{path.name}: missing forceCatalogIndexClosed")
    if "path:path" not in t and "H-save" not in t:
        raise SystemExit(f"{path.name}: missing save-place log")
    if "is-collapsed" not in t[t.find('id="catalogIndex"') - 40 : t.find('id="catalogIndex"') + 20]:
        # HTML must have is-collapsed on the catalogIndex div
        i = t.find('id="catalogIndex"')
        window = t[max(0, i - 60) : i + 20]
        if "is-collapsed" not in window:
            raise SystemExit(f"{path.name}: catalogIndex HTML not collapsed: {window!r}")
    path.write_text(t, encoding="utf-8")
    print("patched", path.name)


def main():
    for p in FILES:
        if not p.exists():
            raise SystemExit(f"missing {p}")
        patch(p)
    print("all ok")


if __name__ == "__main__":
    main()
