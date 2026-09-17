#!/usr/bin/env python3
from pathlib import Path

ROOT = Path("/home/phnx/kiro-kontakt-patch/public/catalogs")
FILES = [
    ROOT / "KONTAKT-CATALOG.html",
    ROOT / "DS-CATALOG.html",
    ROOT / "KONTAKT-CATALOG-portable.html",
    ROOT / "DS-CATALOG-portable.html",
]

TEARDOWN = """  if(document.body.classList.contains('chosen-preview-open')||entry.classList.contains('chosen')){
    jumpOrigin='gallery-from-expand';
    document.body.classList.remove('chosen-preview-open');
    setOverlayFocus(null);
    unpinSelectedForPreview();
  }else if(entry.classList.contains('highlight')||document.body.classList.contains('hl-open')){"""

KEEP = """  if(document.body.classList.contains('chosen-preview-open')||entry.classList.contains('chosen')){
    jumpOrigin='gallery-from-expand';
  }else if(entry.classList.contains('highlight')||document.body.classList.contains('hl-open')){"""

SHOW_OLD = """  rememberViewed(el);
  if(document.body.classList.contains('chosen-preview-open')){
    openChosenPreview(el);
    if(typeof window.syncChromeFavs==='function')window.syncChromeFavs(el);
    return true;
  }"""

SHOW_NEW = """  var overlayOn=document.body.classList.contains('gallery-open')||document.body.classList.contains('img-focus-open');
  if(!overlayOn)rememberViewed(el);
  if(overlayOn){
    var hitsO=galleryHits();
    var iO=hitsO.indexOf(el);
    if(iO>=0)galleryIndex=iO;
    if(document.body.classList.contains('gallery-open')){
      var gimgO=document.querySelector('#imgGallery .gallery-img');
      if(gimgO){gimgO.src=srcImg.src;gimgO.alt=srcImg.alt||'';}
    }
    if(document.body.classList.contains('img-focus-open')){
      var imgO=document.querySelector('#imgFocus .img-focus-img');
      if(imgO){imgO.src=srcImg.src;imgO.alt=srcImg.alt||'';}
    }
    setImgFocusScale(1);
    if(typeof window.syncChromeFavs==='function')window.syncChromeFavs(el);
    setOverlayTitle(el);
    return true;
  }
  if(document.body.classList.contains('chosen-preview-open')){
    openChosenPreview(el);
    if(typeof window.syncChromeFavs==='function')window.syncChromeFavs(el);
    return true;
  }"""

EXIT_OLD = """  if(origin==='gallery-from-expand'){
    jumpOrigin=null;
    if(last)openChosenPreview(last);
    jumpOrigin='search';
    return;
  }"""

EXIT_NEW = """  if(origin==='gallery-from-expand'){
    jumpOrigin=null;
    if(last){
      if(document.body.classList.contains('chosen-preview-open'))rememberViewed(last);
      else openChosenPreview(last);
    }
    return;
  }"""

CUR_OLD = """function currentBannerEntry(){
  return lastViewedEntry
    || document.querySelector('.entry.highlight')
    || document.querySelector('.entry.selected')
    || galleryHits()[galleryIndex]
    || null;
}"""

CUR_NEW = """function currentBannerEntry(){
  if(document.body.classList.contains('gallery-open')||document.body.classList.contains('img-focus-open')){
    var hitsC=galleryHits();
    if(galleryIndex>=0&&hitsC[galleryIndex])return hitsC[galleryIndex];
  }
  return lastViewedEntry
    || document.querySelector('.entry.highlight')
    || document.querySelector('.entry.selected')
    || galleryHits()[galleryIndex]
    || null;
}"""

CLOSE_IMG_OLD = """function closeImgFocus(keepClosed){
  var wrap=document.getElementById('imgFocus');
  if(!wrap||!wrap.classList.contains('open'))return;
  var last=lastViewedEntry||document.querySelector('.entry.selected');"""

CLOSE_IMG_NEW = """function closeImgFocus(keepClosed){
  var wrap=document.getElementById('imgFocus');
  if(!wrap||!wrap.classList.contains('open'))return;
  var last=typeof currentBannerEntry==='function'?currentBannerEntry():(lastViewedEntry||document.querySelector('.entry.selected'));"""

CLOSE_GAL_OLD = """function closeGallery(keepClosed){
  var gal=document.getElementById('imgGallery');
  if(!gal||!gal.classList.contains('open'))return;
  var last=lastViewedEntry||document.querySelector('.entry.selected');"""

CLOSE_GAL_NEW = """function closeGallery(keepClosed){
  var gal=document.getElementById('imgGallery');
  if(!gal||!gal.classList.contains('open'))return;
  var last=typeof currentBannerEntry==='function'?currentBannerEntry():(lastViewedEntry||document.querySelector('.entry.selected'));"""

CSS_MARK = "body.chosen-preview-open.desc-focus-open .entry.selected:not(.highlight),"
CSS_OLD = """body.chosen-preview-open.desc-focus-open .entry.selected:not(.highlight),
body.chosen-preview-open.path-focus-open .entry.selected:not(.highlight){z-index:840;pointer-events:none}"""
CSS_NEW = """body.chosen-preview-open.desc-focus-open .entry.selected:not(.highlight),
body.chosen-preview-open.path-focus-open .entry.selected:not(.highlight),
body.chosen-preview-open.img-focus-open .entry.selected:not(.highlight),
body.chosen-preview-open.gallery-open .entry.selected:not(.highlight){z-index:840;pointer-events:none}
body.hl-open.img-focus-open .entry.highlight,body.hl-open.gallery-open .entry.highlight{pointer-events:none}
.img-focus-backdrop,.img-gallery{z-index:10050!important}
.img-focus-zoom,.gallery-zoom{z-index:10051!important}
.gallery-zoom input[type=range]{width:min(40vw,180px);accent-color:var(--accent-instrument)}"""

GAL_ZOOM_OLD = """  <div class="gallery-zoom" onclick="event.stopPropagation()">
    <button type="button" class="gallery-zoom-btn" aria-label="Zoom out" onclick="nudgeImgFocusScale(-0.15)">−</button>
    <button type="button" class="gallery-zoom-btn" aria-label="Zoom in" onclick="nudgeImgFocusScale(0.15)">+</button>
  </div>"""

GAL_ZOOM_NEW = """  <div class="gallery-zoom" onclick="event.stopPropagation()">
    <button type="button" class="gallery-zoom-btn" aria-label="Zoom out" onclick="nudgeImgFocusScale(-0.15)">−</button>
    <input id="imgGalleryScale" type="range" min="0.5" max="3" step="0.05" value="1" aria-label="Image scale">
    <button type="button" class="gallery-zoom-btn" aria-label="Zoom in" onclick="nudgeImgFocusScale(0.15)">+</button>
  </div>"""

SCALE_OLD = """  var sl=document.getElementById('imgFocusScale');
  if(sl)sl.value=String(imgFocusScale);"""

SCALE_NEW = """  ['imgFocusScale','imgGalleryScale'].forEach(function(id){
    var sl=document.getElementById(id);
    if(sl)sl.value=String(imgFocusScale);
  });"""

INPUT_OLD = "if(e.target&&e.target.id==='imgFocusScale')setImgFocusScale(parseFloat(e.target.value)||1);"
INPUT_NEW = "if(e.target&&(e.target.id==='imgFocusScale'||e.target.id==='imgGalleryScale'))setImgFocusScale(parseFloat(e.target.value)||1);"

POST_LOG = """  if(useMobileFocus())openGallery(entry);
  else openImgFocus(entry);
"""

POST_LOG_NEW = """  // #region agent log
  try{
    var _bk=document.body.classList;
    fetch('http://127.0.0.1:7529/ingest/1cf46354-1d61-4c80-bd72-a340f1db1b51',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'c00e3e'},body:JSON.stringify({sessionId:'c00e3e',runId:'post-fix',hypothesisId:'A',location:'catalog:openBannerGallery:kept',message:'gallery overlay kept card',data:{id:entry&&entry.id,preview:_bk.contains('chosen-preview-open'),hl:_bk.contains('hl-open'),origin:jumpOrigin},timestamp:Date.now()})}).catch(function(){});
  }catch(eKept){}
  // #endregion
  if(useMobileFocus())openGallery(entry);
  else openImgFocus(entry);
"""

def patch(path: Path):
    t = path.read_text(encoding="utf-8")
    n = 0
    reps = [
        (TEARDOWN, KEEP, "teardown"),
        (SHOW_OLD, SHOW_NEW, "showBanner"),
        (EXIT_OLD, EXIT_NEW, "exitJump"),
        (CUR_OLD, CUR_NEW, "currentBanner"),
        (CLOSE_IMG_OLD, CLOSE_IMG_NEW, "closeImg"),
        (CLOSE_GAL_OLD, CLOSE_GAL_NEW, "closeGal"),
        (CSS_OLD, CSS_NEW, "css"),
        (GAL_ZOOM_OLD, GAL_ZOOM_NEW, "galZoom"),
        (SCALE_OLD, SCALE_NEW, "scaleSync"),
        (INPUT_OLD, INPUT_NEW, "inputBind"),
    ]
    misses = []
    for old, new, name in reps:
        c = t.count(old)
        if c != 1:
            misses.append(f"{name}:{c}")
        else:
            t = t.replace(old, new, 1)
            n += 1
    if POST_LOG in t and "openBannerGallery:kept" not in t:
        if t.count(POST_LOG) >= 1:
            t = t.replace(POST_LOG, POST_LOG_NEW, 1)
            n += 1
        else:
            misses.append("postLog:0")
    path.write_text(t, encoding="utf-8")
    print(f"{path.name}: {n} replacements; misses={misses}")

def main():
    for p in FILES:
        if not p.exists():
            print("missing", p)
            continue
        patch(p)

if __name__ == "__main__":
    main()
