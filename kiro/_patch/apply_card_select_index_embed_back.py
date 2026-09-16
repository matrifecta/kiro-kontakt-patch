#!/usr/bin/env python3
"""Four catalog UI fixes: bigger folder glyph, Index window chrome, empty-card
select, embed Back = one previous in-embed page. Safe byte replace for DS."""
from pathlib import Path

ROOT = Path("/home/phnx/kiro-kontakt-patch/public/catalogs")
FILES = [
    ROOT / "KONTAKT-CATALOG.html",
    ROOT / "DS-CATALOG.html",
    ROOT / "KONTAKT-CATALOG-portable.html",
    ROOT / "DS-CATALOG-portable.html",
]


def once(text: str, old: str, new: str, label: str, path: Path) -> str:
    n = text.count(old)
    if n != 1:
        raise SystemExit(f"{path.name}: {label} count={n} expected 1")
    return text.replace(old, new, 1)


# --- Fix 1: folder glyph only ---
FOLDER_CSS_OLD = """.path-icon-btn:hover .path-icon-glyph,.path-icon-btn:focus-visible .path-icon-glyph{
  opacity:1!important;filter:none!important
}"""

FOLDER_CSS_NEW = """.path-icon-btn:hover .path-icon-glyph,.path-icon-btn:focus-visible .path-icon-glyph{
  opacity:1!important;filter:none!important
}
/* fix-FOLDER-GLYPH-SIZE: folder only ~25% larger; never #catalogIndex */
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


# --- Fix 2: Index window + embed hide card chrome ---
INDEX_CSS_OLD = """/* fix-INDEX-ISOLATE: full-width opaque Index; card chrome stays inside .entry */
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

INDEX_CSS_NEW = """/* fix-INDEX-ISOLATE-v2: Window+Embed hide ALL card chrome; opaque overlay */
#catalogIndex,
#catalogMain>#catalogIndex,
#catalogMain>#catalogIndex:not(.is-embedded),
body.index-window-open #catalogIndex,
body.index-window-open #catalogMain>#catalogIndex:not(.is-embedded),
.catalog-body>#catalogIndex,
#catalogMain>.catalog-body>#catalogIndex,
#catalogMain>.catalog-body>#catalogIndex.is-embedded,
.loc-group>#catalogIndex{
  overflow:hidden!important;isolation:isolate!important;
  background:var(--bg-surface)!important;z-index:24!important
}
.catalog-body>#catalogIndex,
#catalogMain>.catalog-body>#catalogIndex,
#catalogMain>.catalog-body>#catalogIndex.is-embedded,
.loc-group>#catalogIndex{
  grid-column:1/-1!important;width:100%!important;max-width:100%!important;
  display:flex!important;flex-direction:column!important;
  position:relative!important
}
#catalogMain>#catalogIndex:not(.is-embedded),
body.index-window-open #catalogIndex:not(.is-embedded){
  background:var(--bg-surface)!important;
  overflow:hidden!important;isolation:isolate!important;z-index:24!important
}
#catalogIndex .index,#catalogIndex #catalogIndexList,
#catalogMain>#catalogIndex:not(.is-embedded) .index,
#catalogMain>#catalogIndex:not(.is-embedded) #catalogIndexList,
body.index-window-open #catalogIndex .index,
body.index-window-open #catalogIndex #catalogIndexList{
  background:var(--bg-surface)!important;isolation:isolate!important
}
#catalogIndex .fav-btn,
#catalogIndex .path-icon-btn,
#catalogIndex .path-action-row,
#catalogIndex a.folder,
#catalogIndex .folder,
#catalogIndex .path-fs-hit,
#catalogIndex .path-copy-hit,
#catalogIndex .path button,
#catalogIndex .path .path-icon-btn,
#catalogMain>#catalogIndex:not(.is-embedded) .fav-btn,
#catalogMain>#catalogIndex:not(.is-embedded) .path-icon-btn,
#catalogMain>#catalogIndex:not(.is-embedded) .path-action-row,
#catalogMain>#catalogIndex:not(.is-embedded) a.folder,
#catalogMain>#catalogIndex:not(.is-embedded) .folder,
#catalogMain>#catalogIndex:not(.is-embedded) .path-fs-hit,
#catalogMain>#catalogIndex:not(.is-embedded) .path-copy-hit,
body.index-window-open #catalogIndex .fav-btn,
body.index-window-open #catalogIndex .path-icon-btn,
body.index-window-open #catalogIndex .path-action-row,
body.index-window-open #catalogIndex a.folder,
body.index-window-open #catalogIndex .folder,
body.index-window-open #catalogIndex .path-fs-hit,
body.index-window-open #catalogIndex .path-copy-hit,
.catalog-body>#catalogIndex .fav-btn,
.catalog-body>#catalogIndex .path-icon-btn,
.catalog-body>#catalogIndex .path-action-row,
.catalog-body>#catalogIndex a.folder{
  display:none!important;visibility:hidden!important;pointer-events:none!important
}
.entry{position:relative}
.entry:not(.highlight){overflow:hidden}
body.display-upper #catalogIndex,body.display-fs #catalogIndex{
  overflow:hidden!important;background:var(--bg-surface)!important
}
"""

IXFIT_OLD = """function applyIndexScrollFit(){
  var ix=document.getElementById('catalogIndex');
  var il=document.getElementById('catalogIndexList')||(ix&&ix.querySelector('ul.index'));
"""

IXFIT_NEW = """function stripIndexCardChrome(ix){
  ix=ix||document.getElementById('catalogIndex');
  if(!ix)return;
  ix.querySelectorAll('.path-action-row,.path-icon-btn,a.folder,.path-fs-hit,.path-copy-hit,.fav-btn').forEach(function(el){
    if(el.closest&&el.closest('.catalog-body .entry,.entry'))return;
    try{el.remove();}catch(err){el.style.display='none';el.setAttribute('hidden','');}
  });
}
function applyIndexScrollFit(){
  var ix=document.getElementById('catalogIndex');
  if(typeof stripIndexCardChrome==='function')stripIndexCardChrome(ix);
  var il=document.getElementById('catalogIndexList')||(ix&&ix.querySelector('ul.index'));
"""


# --- Fix 3: empty card surface selects ---
REMEMBER_OLD = """function rememberViewed(el){
"""

REMEMBER_NEW = """function cardSelectNearInteractable(entry,x,y,pad){
  if(!entry||x==null||y==null)return false;
  pad=pad==null?14:pad;
  var sel='a,button,.fav-btn,.fs-btn,.hl-close,.hl-min,.preview-back,.search-popup-btn,.search-link,.patches,summary,input,select,textarea,.note-balloon,.note-pop,.note-save,.note-cancel,.note-ta,.kw,.card-search-embed,#cardMinDock,.cover,.summary-panel,.path,.path-icon-btn,.folder,.path-fs-hit,.path-copy-hit,.path-action-row';
  var nodes=entry.querySelectorAll(sel);
  for(var i=0;i<nodes.length;i++){
    var el=nodes[i];
    if(el.closest&&el.closest('#catalogIndex'))continue;
    if(el.closest&&(el.closest('h3.lib-name')||el.classList&&el.classList.contains('lib-name')))continue;
    var r=el.getBoundingClientRect();
    if(r.width<2&&r.height<2)continue;
    if(x>=r.left-pad&&x<=r.right+pad&&y>=r.top-pad&&y<=r.bottom+pad)return true;
  }
  return false;
}
function selectCardFromEmpty(entry){
  if(!entry)return;
  if(typeof rememberViewed==='function')rememberViewed(entry);
  else if(typeof markSelected==='function')markSelected(entry);
}
function rememberViewed(el){
"""

CLICK_OLD = """    if(e.target.closest('h3,.lib-name')){openChosenPreview(entry);return;}
    if(entry.classList.contains('highlight'))return;
    if(e.target.closest('button')) return;
    if(document.body.classList.contains('chosen-preview-open')&&entry.classList.contains('selected'))return;
    selectEntry(entry);
    return;"""

CLICK_NEW = """    if(entry.classList.contains('highlight'))return;
    if(e.target.closest('button')) return;
    if(document.body.classList.contains('chosen-preview-open')&&entry.classList.contains('selected'))return;
    var nameHit=!!(e.target.closest&&e.target.closest('h3,.lib-name'));
    if(!nameHit&&typeof cardSelectNearInteractable==='function'&&cardSelectNearInteractable(entry,e.clientX,e.clientY,14))return;
    if(typeof selectCardFromEmpty==='function')selectCardFromEmpty(entry);
    else if(typeof rememberViewed==='function')rememberViewed(entry);
    e.preventDefault();
    return;"""


# --- Fix 4: embed Back pops one in-embed snapshot ---
ENSURE_OLD = """function cardSearchEnsureYtFrame(){
  var old=document.getElementById('cardSearchFrame');
  var parent=old?old.parentNode:null;
  if(!parent)return null;
  var frame=document.createElement('iframe');
  frame.className='card-search-frame';
  frame.id='cardSearchFrame';
  frame.title='Library search';
  frame.setAttribute('allowfullscreen','');
  frame.setAttribute('referrerpolicy','strict-origin-when-cross-origin');
  frame.setAttribute('allow','accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; fullscreen; web-share');
  try{frame.referrerPolicy='strict-origin-when-cross-origin';}catch(err){}
  try{frame.allowFullscreen=true;}catch(err){}
  parent.replaceChild(frame,old);
  return frame;
}
"""

ENSURE_NEW = """function cardSearchBindFrameNav(frame){
  frame=frame||document.getElementById('cardSearchFrame');
  if(!frame||frame.dataset.embedNavBound==='1')return frame;
  frame.dataset.embedNavBound='1';
  frame.addEventListener('load',function(){
    if(!document.body.classList.contains('card-embed-open'))return;
    var src=frame.getAttribute('src')||frame.src||'';
    if(!src||/^about:/i.test(src))return;
    if(cardSearchState&&cardSearchState._ownFrameNav){
      cardSearchState._ownFrameNav=false;
      if(!cardSearchState._iframeLoads)cardSearchState._iframeLoads=1;
      return;
    }
    if(!cardSearchState)return;
    cardSearchState._iframeLoads=(cardSearchState._iframeLoads||0)+1;
    if(cardSearchState._iframeLoads>1)cardSearchState._iframeHasStack=true;
    try{
      var href=frame.contentWindow&&frame.contentWindow.location&&frame.contentWindow.location.href;
      if(href&&!/^about:/i.test(href)&&typeof cardSearchHistPush==='function'){
        cardSearchHistPush({kind:'frame',view:'frame',type:cardSearchState.type||'',embedUrl:href});
      }
    }catch(err){}
    if(typeof cardSearchEnableBack==='function')cardSearchEnableBack();
  });
  return frame;
}
function cardSearchMarkOwnFrameNav(){
  if(!window.cardSearchState)window.cardSearchState={history:[]};
  cardSearchState._ownFrameNav=true;
}
function cardSearchEnsureYtFrame(){
  var old=document.getElementById('cardSearchFrame');
  var parent=old?old.parentNode:null;
  if(!parent)return null;
  var frame=document.createElement('iframe');
  frame.className='card-search-frame';
  frame.id='cardSearchFrame';
  frame.title='Library search';
  frame.setAttribute('allowfullscreen','');
  frame.setAttribute('referrerpolicy','strict-origin-when-cross-origin');
  frame.setAttribute('allow','accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; fullscreen; web-share');
  try{frame.referrerPolicy='strict-origin-when-cross-origin';}catch(err){}
  try{frame.allowFullscreen=true;}catch(err){}
  parent.replaceChild(frame,old);
  if(typeof cardSearchBindFrameNav==='function')cardSearchBindFrameNav(frame);
  return frame;
}
"""

SEED_OLD = "  cardSearchState={type:type||'',popupUrl:popupUrl,embedUrl:'',history:[],query:query,name:name,view:'',results:[],images:[],_webData:null,urls:urls};"

SEED_NEW = """  cardSearchState={type:type||'',popupUrl:popupUrl,embedUrl:'',history:[],query:query,name:name,view:'',results:[],images:[],_webData:null,urls:urls,_iframeLoads:0,_iframeHasStack:false};
  var _landView=type==='yt'?'yt-list':(type==='img'?'grid':'results');
  cardSearchState.history=[{kind:'root',view:_landView,type:type||'web',landing:1}];
  if(typeof cardSearchBindFrameNav==='function')cardSearchBindFrameNav(document.getElementById('cardSearchFrame'));
  cardSearchEnableBack();"""

YT_AUTO_OLD = """    if(!cardSearchState._ytManualPlay){
      if(!setCardYtFrame(pick.id,'youtube'))cardSearchYtTryNext('bad id');
    }"""

YT_AUTO_NEW = """    if(!cardSearchState._ytManualPlay){
      if(!setCardYtFrame(pick.id,'youtube',{noHist:1}))cardSearchYtTryNext('bad id');
    }"""

OPEN_KNOWN_OLD = "    if(known)setCardYtFrame(known,'youtube');"
OPEN_KNOWN_NEW = "    if(known)setCardYtFrame(known,'youtube',{noHist:1});"

MOUNT_SRC_OLD = """  try{frame.referrerPolicy='strict-origin-when-cross-origin';}catch(err){}
  frame.src=url;
  showCardSearchFrame(true);
  return true;
}"""

MOUNT_SRC_NEW = """  try{frame.referrerPolicy='strict-origin-when-cross-origin';}catch(err){}
  if(typeof cardSearchMarkOwnFrameNav==='function')cardSearchMarkOwnFrameNav();
  if(typeof cardSearchBindFrameNav==='function')cardSearchBindFrameNav(frame);
  frame.src=url;
  showCardSearchFrame(true);
  return true;
}"""

APPLY_KIND_OLD = """  var kind=snap.kind||snap.view||'';
  if(kind==='root'||kind==='yt-list'||kind==='grid'&&snap.type==='img'){"""

APPLY_KIND_NEW = """  var kind=snap.kind||snap.view||'';
  if(kind==='frame'&&snap.embedUrl){
    var fr=document.getElementById('cardSearchFrame');
    cardSearchState.embedUrl=snap.embedUrl;
    if(typeof cardSearchMarkOwnFrameNav==='function')cardSearchMarkOwnFrameNav();
    if(fr){fr.src=snap.embedUrl;fr.classList.remove('is-hidden');}
    if(typeof showCardSearchFrame==='function')showCardSearchFrame(true);
    return;
  }
  if(kind==='root'||kind==='yt-list'||kind==='grid'&&snap.type==='img'){"""

BACK_OLD = """window.cardSearchBack=function(){
  var frame=document.getElementById('cardSearchFrame');
  if(!window.cardSearchState)window.cardSearchState={history:[]};
  if(!cardSearchState.history)cardSearchState.history=[];
  if(cardSearchState.history.length>1){
    if(typeof window.cardSearchIframeBack==='function'){window.cardSearchIframeBack();return;}
  }
  if(frame&&!frame.classList.contains('is-hidden')&&frame.contentWindow){
    try{
      if(frame.contentWindow.history&&frame.contentWindow.history.length>1){
        frame.contentWindow.history.back();
        if(typeof cardSearchEnableBack==='function')cardSearchEnableBack();
        return;
      }
    }catch(err){}
  }
  if(typeof closeCardSearchEmbed==='function')closeCardSearchEmbed();
};
"""

BACK_NEW = """window.cardSearchPopEmbed=function(){
  if(!window.cardSearchState)window.cardSearchState={history:[]};
  if(!cardSearchState.history)cardSearchState.history=[];
  var hist=cardSearchState.history;
  var frame=document.getElementById('cardSearchFrame');
  if(hist.length>1){
    hist.pop();
    var prev=hist[hist.length-1];
    if(typeof cardSearchApplyHist==='function')cardSearchApplyHist(prev);
    else if(typeof prev==='string'&&frame){cardSearchState.embedUrl=prev;frame.src=prev;}
    if(typeof cardSearchEnableBack==='function')cardSearchEnableBack();
    return true;
  }
  var frameOn=!!(frame&&!frame.classList.contains('is-hidden')&&frame.contentWindow);
  if(frameOn&&(cardSearchState._iframeHasStack||(cardSearchState._iframeLoads||0)>1)){
    try{
      if(frame.contentWindow.history&&frame.contentWindow.history.length>1){
        frame.contentWindow.history.back();
        cardSearchState._iframeLoads=Math.max(1,(cardSearchState._iframeLoads||1)-1);
        if(cardSearchState._iframeLoads<=1)cardSearchState._iframeHasStack=false;
        if(typeof cardSearchEnableBack==='function')cardSearchEnableBack();
        return true;
      }
    }catch(err){}
  }
  return false;
};
window.cardSearchBack=function(){
  if(typeof window.cardSearchPopEmbed==='function'&&window.cardSearchPopEmbed())return;
  if(typeof closeCardSearchEmbed==='function')closeCardSearchEmbed();
};
"""

IFRAME_BACK_OLD = """window.cardSearchIframeBack=function(){
  var frame=document.getElementById('cardSearchFrame');
  if(!cardSearchState.history)cardSearchState.history=[];
  if(cardSearchState.history.length>1){
    cardSearchState.history.pop();
    var prev=cardSearchState.history[cardSearchState.history.length-1];
    if(typeof cardSearchApplyHist==='function')cardSearchApplyHist(prev);
    else if(typeof prev==='string'&&frame){cardSearchState.embedUrl=prev;frame.src=prev;}
    cardSearchEnableBack();
    return;
  }
  if(frame&&!frame.classList.contains('is-hidden')&&frame.contentWindow){
    try{
      if(frame.contentWindow.history&&frame.contentWindow.history.length>1){
        frame.contentWindow.history.back();
        cardSearchEnableBack();
        return;
      }
    }catch(err){}
  }
  if(cardSearchState.type==='yt'){
    if(typeof showCardSearchFrame==='function')showCardSearchFrame(false);
    if(typeof renderCardYtList==='function')renderCardYtList(cardSearchState.ytItems||[],'');
    cardSearchEnableBack();
    return;
  }
  if(cardSearchState.type==='img'){
    if(window.cardSearchExitImage)window.cardSearchExitImage();
    cardSearchEnableBack();
    return;
  }
  if(typeof cardSearchShowWebResults==='function')cardSearchShowWebResults();
  cardSearchEnableBack();
};
"""

IFRAME_BACK_NEW = """window.cardSearchIframeBack=function(){
  if(typeof window.cardSearchPopEmbed==='function'&&window.cardSearchPopEmbed())return;
  if(typeof closeCardSearchEmbed==='function')closeCardSearchEmbed();
};
"""


def patch(path: Path) -> None:
    raw0 = path.read_bytes()
    text = raw0.decode("utf-8")
    n = path.name
    text = once(text, FOLDER_CSS_OLD, FOLDER_CSS_NEW, "folder-css", path)
    text = once(text, INDEX_CSS_OLD, INDEX_CSS_NEW, "index-css", path)
    text = once(text, IXFIT_OLD, IXFIT_NEW, "ixfit", path)
    text = once(text, REMEMBER_OLD, REMEMBER_NEW, "remember", path)
    text = once(text, CLICK_OLD, CLICK_NEW, "click", path)
    text = once(text, ENSURE_OLD, ENSURE_NEW, "ensure-frame", path)
    text = once(text, SEED_OLD, SEED_NEW, "seed-landing", path)
    text = once(text, YT_AUTO_OLD, YT_AUTO_NEW, "yt-autohist", path)
    text = once(text, OPEN_KNOWN_OLD, OPEN_KNOWN_NEW, "yt-known", path)
    text = once(text, MOUNT_SRC_OLD, MOUNT_SRC_NEW, "mount-google", path)
    text = once(text, APPLY_KIND_OLD, APPLY_KIND_NEW, "apply-hist", path)
    text = once(text, BACK_OLD, BACK_NEW, "embed-back", path)
    text = once(text, IFRAME_BACK_OLD, IFRAME_BACK_NEW, "iframe-back", path)
    for mark in (
        "fix-FOLDER-GLYPH-SIZE",
        "fix-INDEX-ISOLATE-v2",
        "stripIndexCardChrome",
        "selectCardFromEmpty",
        "cardSearchPopEmbed",
        "cardSearchBindFrameNav",
    ):
        if mark not in text:
            raise SystemExit(f"{n}: missing mark {mark}")
    raw = text.encode("utf-8")
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_bytes(raw)
    check = tmp.read_bytes()
    if not (check.endswith(b"</html>") or check.endswith(b"</html>\n")):
        tmp.unlink()
        raise SystemExit(f"{n}: truncated, does not end with </html>")
    if abs(len(check) - len(raw0)) > 80_000:
        tmp.unlink()
        raise SystemExit(f"{n}: size delta {len(check)-len(raw0)} too large")
    tmp.replace(path)
    print(f"OK {n} {len(raw0)} -> {len(check)} endswith=</html>")


def main() -> None:
    for p in FILES:
        if not p.exists():
            raise SystemExit(f"missing {p}")
        patch(p)


if __name__ == "__main__":
    main()
