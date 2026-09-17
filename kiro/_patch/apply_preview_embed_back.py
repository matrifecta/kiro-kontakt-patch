#!/usr/bin/env python3
"""Preview-back never restores fullscreen; embed-back owns history; reload current page."""
from pathlib import Path

ROOT = Path("/home/phnx/kiro-kontakt-patch/public/catalogs")
FILES = [
    ROOT / "KONTAKT-CATALOG.html",
    ROOT / "DS-CATALOG.html",
    ROOT / "KONTAKT-CATALOG-portable.html",
    ROOT / "DS-CATALOG-portable.html",
]

CSS_MARK = "</style></head><body class=\"search-mode\">"
CSS_ADD = (
    "/* fix-EMBED-IFRAME-BACK-HIDE: main embed back owns in-embed history */\n"
    "#cardSearchEmbed .card-search-iframe-back{display:none!important}\n"
    + CSS_MARK
)

HTML_IFRAME_BACK = (
    '    <button type="button" class="card-search-iframe-back" aria-label="Back one step" '
    'title="Back one step in page" onclick="event.preventDefault();event.stopPropagation();'
    "cardSearchIframeBack()\">&#x21BA;</button>\n"
)

ORIGIN_SET_OLD = "    jumpOrigin=fromFullscreen?'preview-from-fullscreen':null;"
ORIGIN_SET_NEW = "    if(fromFullscreen)jumpOrigin=null;"

ORIGIN_RESTORE_OLD = """  if(!opts.skipJumpExit&&origin==='preview-from-fullscreen'&&last){
    openOverlay(last);
    return;
  }
  if(jumpExit){"""

ORIGIN_RESTORE_NEW = """  if(last&&typeof rememberViewed==='function')rememberViewed(last);
  if(jumpExit){"""

BACK_OLD = """window.cardSearchBack=function(){
  var frame=document.getElementById('cardSearchFrame');
  if(typeof closeCardSearchEmbed==='function')closeCardSearchEmbed();
};"""

BACK_NEW = """window.cardSearchBack=function(){
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
};"""

RELOAD_OLD = """window.cardSearchReload=function(){
  cardSearchEnableBack();
  var frame=document.getElementById('cardSearchFrame');
  if(cardSearchState.type==='yt'){
    // Reload the currently visible YT page; fall back to root only when no embedUrl
    if(cardSearchState.embedUrl&&frame&&!frame.classList.contains('is-hidden')){
      frame.src=cardSearchState.embedUrl;
    }else{
      loadCardYtSearch(cardSearchState.query);
    }
    return;
  }
  if(cardSearchState.type==='img'){
    window.cardSearchExitImage();
    loadCardImageSearch(cardSearchState.query);
    return;
  }
  // web: reload the article iframe if visible, else reload results from scratch
  if(cardSearchState.view==='article'&&frame&&!frame.classList.contains('is-hidden')&&cardSearchState.embedUrl){
    frame.src=cardSearchState.embedUrl;
    return;
  }
  loadCardWebSearch(cardSearchState.query);
};"""

RELOAD_NEW = """window.cardSearchReload=function(){
  cardSearchEnableBack();
  var frame=document.getElementById('cardSearchFrame');
  var frameOn=!!(frame&&!frame.classList.contains('is-hidden')&&frame.style.display!=='none');
  var src='';
  if(cardSearchState&&cardSearchState.embedUrl)src=cardSearchState.embedUrl;
  if(!src&&frame)src=frame.getAttribute('src')||frame.src||'';
  if(src&&/^about:/i.test(src))src='';
  if(frameOn&&src){
    try{
      if(frame.contentWindow&&(frame.getAttribute('src')||frame.src)===src){
        frame.contentWindow.location.reload();
        return;
      }
    }catch(errReload){}
    frame.src=src;
    return;
  }
  var imgView=document.getElementById('cardSearchImgView');
  var img=document.getElementById('cardSearchImgFit');
  if(imgView&&imgView.classList.contains('open')&&img){
    var isrc=img.getAttribute('src')||'';
    if(isrc){img.removeAttribute('src');img.src=isrc;return;}
  }
  if(cardSearchState.type==='yt'){loadCardYtSearch(cardSearchState.query);return;}
  if(cardSearchState.type==='img'){loadCardImageSearch(cardSearchState.query);return;}
  loadCardWebSearch(cardSearchState.query);
};"""


def must_replace(text: str, old: str, new: str, name: str, label: str) -> str:
    n = text.count(old)
    if n != 1:
        raise SystemExit(f"{name}: {label} count={n}")
    return text.replace(old, new, 1)


def patch(path: Path) -> None:
    t = path.read_text(encoding="utf-8")
    n = path.name
    ingest = t.count("127.0.0.1:7529/ingest")
    if "fix-EMBED-IFRAME-BACK-HIDE" not in t:
        t = must_replace(t, CSS_MARK, CSS_ADD, n, "css")
    if HTML_IFRAME_BACK in t:
        t = must_replace(t, HTML_IFRAME_BACK, "", n, "iframe-back html")
    if ORIGIN_SET_OLD in t:
        t = must_replace(t, ORIGIN_SET_OLD, ORIGIN_SET_NEW, n, "origin set")
    if ORIGIN_RESTORE_OLD in t:
        t = must_replace(t, ORIGIN_RESTORE_OLD, ORIGIN_RESTORE_NEW, n, "origin restore")
    t = must_replace(t, BACK_OLD, BACK_NEW, n, "cardSearchBack")
    t = must_replace(t, RELOAD_OLD, RELOAD_NEW, n, "cardSearchReload")
    if ingest and t.count("127.0.0.1:7529/ingest") != ingest:
        raise SystemExit(f"{n}: stripped debug logs")
    if not t.strip().endswith("</html>"):
        raise SystemExit(f"{n}: truncated")
    tmp = path.with_suffix(path.suffix + ".tmp")
    out = t.encode("utf-8")
    tmp.write_bytes(out)
    if not tmp.read_bytes().decode("utf-8").strip().endswith("</html>"):
        tmp.unlink()
        raise SystemExit(f"{n}: tmp truncated")
    tmp.replace(path)
    print("OK", n, "bytes", len(out))


def main() -> None:
    for p in FILES:
        patch(p)


if __name__ == "__main__":
    main()
