#!/usr/bin/env python3
"""Close in-iframe embed Back hole: snapshot iframe navigations (incl.
cross-origin load) and pop one page without exiting embed."""
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


BIND_OLD = """function cardSearchBindFrameNav(frame){
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
"""

BIND_NEW = """function cardSearchFrameUrl(frame){
  frame=frame||document.getElementById('cardSearchFrame');
  if(!frame)return '';
  try{
    var href=frame.contentWindow&&frame.contentWindow.location&&frame.contentWindow.location.href;
    if(href&&!/^about:/i.test(href))return href;
  }catch(err){}
  var src=frame.getAttribute('src')||frame.src||'';
  return (!src||/^about:/i.test(src))?'':src;
}
function cardSearchStampLandingUrl(url){
  if(!cardSearchState||!url)return;
  if(!cardSearchState.embedUrl)cardSearchState.embedUrl=url;
  if(!cardSearchState._landingEmbedUrl)cardSearchState._landingEmbedUrl=url;
  var hist=cardSearchState.history||[];
  if(hist[0]&&(hist[0].kind==='root'||hist[0].landing)&&!hist[0].embedUrl)hist[0].embedUrl=url;
}
function cardSearchRestoreFrame(url){
  var fr=document.getElementById('cardSearchFrame');
  if(!url||!fr)return false;
  cardSearchState.embedUrl=url;
  if(typeof cardSearchMarkOwnFrameNav==='function')cardSearchMarkOwnFrameNav();
  if(typeof cardSearchBindFrameNav==='function')cardSearchBindFrameNav(fr);
  fr.src=url;
  fr.classList.remove('is-hidden');
  if(typeof showCardSearchFrame==='function')showCardSearchFrame(true);
  return true;
}
function cardSearchOnFrameNav(frame){
  if(!document.body.classList.contains('card-embed-open'))return;
  if(!cardSearchState)return;
  frame=frame||document.getElementById('cardSearchFrame');
  var src=cardSearchFrameUrl(frame);
  if(!src)return;
  cardSearchStampLandingUrl(src);
  try{
    if(frame&&frame.contentWindow&&!frame.contentWindow.__cardSearchPageShow){
      frame.contentWindow.__cardSearchPageShow=1;
      frame.contentWindow.addEventListener('pageshow',function(){cardSearchOnFrameNav(frame);});
    }
  }catch(errBind){}
  if(cardSearchState._ownFrameNav||cardSearchState._applyingHist){
    cardSearchState._ownFrameNav=false;
    cardSearchState._embedFrameLoads=Math.max(1,cardSearchState._embedFrameLoads||0);
    cardSearchState._iframeLoads=cardSearchState._embedFrameLoads;
    cardSearchState._lastFrameSrc=src;
    return;
  }
  cardSearchState._embedFrameLoads=(cardSearchState._embedFrameLoads||0)+1;
  cardSearchState._iframeLoads=cardSearchState._embedFrameLoads;
  if(cardSearchState._embedFrameLoads<=1){
    cardSearchState._lastFrameSrc=src;
    return;
  }
  cardSearchState._iframeHasStack=true;
  var last=(cardSearchState.history||[])[(cardSearchState.history||[]).length-1];
  var lastUrl=(last&&(typeof last==='string'?last:last.embedUrl))||cardSearchState._landingEmbedUrl||'';
  if(lastUrl&&String(lastUrl)===String(src)&&!cardSearchState._embedUserInteracted){
    if(typeof cardSearchEnableBack==='function')cardSearchEnableBack();
    return;
  }
  if(typeof cardSearchHistPush==='function'){
    cardSearchHistPush({kind:'frame',view:'frame',type:cardSearchState.type||'',embedUrl:src,load:cardSearchState._embedFrameLoads});
  }
  cardSearchState._lastFrameSrc=src;
  cardSearchState._embedUserInteracted=false;
  if(typeof cardSearchEnableBack==='function')cardSearchEnableBack();
}
function cardSearchBindFrameNav(frame){
  frame=frame||document.getElementById('cardSearchFrame');
  if(!frame)return frame;
  if(frame.dataset.embedNavBound!=='1'){
    frame.dataset.embedNavBound='1';
    function onNav(){cardSearchOnFrameNav(frame);}
    frame.addEventListener('load',onNav);
    frame.addEventListener('pageshow',onNav);
    frame.addEventListener('pointerdown',function(){
      if(cardSearchState)cardSearchState._embedUserInteracted=true;
    });
    frame.addEventListener('focus',function(){
      if(cardSearchState)cardSearchState._embedUserInteracted=true;
    });
  }
  try{
    if(frame.contentWindow&&!frame.contentWindow.__cardSearchPageShow){
      frame.contentWindow.__cardSearchPageShow=1;
      frame.contentWindow.addEventListener('pageshow',function(){cardSearchOnFrameNav(frame);});
    }
  }catch(err){}
  return frame;
}
function cardSearchMarkOwnFrameNav(){
  if(!window.cardSearchState)window.cardSearchState={history:[]};
  cardSearchState._ownFrameNav=true;
}
"""

HISTEQ_OLD = """function cardSearchHistEq(a,b){
  if(a===b)return true;
  if(!a||!b)return false;
  if(typeof a==='string'||typeof b==='string')return String(a)===String(b);
  return (a.kind||'')===(b.kind||'')&&(a.view||'')===(b.view||'')&&(a.ytId||'')===(b.ytId||'')&&(a.embedUrl||'')===(b.embedUrl||'')&&a.i===b.i;
}
"""

HISTEQ_NEW = """function cardSearchHistEq(a,b){
  if(a===b)return true;
  if(!a||!b)return false;
  if(typeof a==='string'||typeof b==='string')return String(a)===String(b);
  return (a.kind||'')===(b.kind||'')&&(a.view||'')===(b.view||'')&&(a.ytId||'')===(b.ytId||'')&&(a.embedUrl||'')===(b.embedUrl||'')&&a.i===b.i&&(a.load||0)===(b.load||0);
}
"""

APPLY_OLD = """  var kind=snap.kind||snap.view||'';
  if(kind==='frame'&&snap.embedUrl){
    var fr=document.getElementById('cardSearchFrame');
    cardSearchState.embedUrl=snap.embedUrl;
    if(typeof cardSearchMarkOwnFrameNav==='function')cardSearchMarkOwnFrameNav();
    if(fr){fr.src=snap.embedUrl;fr.classList.remove('is-hidden');}
    if(typeof showCardSearchFrame==='function')showCardSearchFrame(true);
    return;
  }
  if(kind==='root'||kind==='yt-list'||kind==='grid'&&snap.type==='img'){
    if((cardSearchState.type==='yt'||kind==='yt-list'||kind==='root'&&cardSearchState.type==='yt')&&kind!=='grid'){
      if(typeof showCardSearchFrame==='function')showCardSearchFrame(false);
      if(typeof renderCardYtList==='function')renderCardYtList(cardSearchState.ytItems||[],'');
      cardSearchState.view='yt';
      return;
    }
  }
"""

APPLY_NEW = """  var kind=snap.kind||snap.view||'';
  if(kind==='frame'&&snap.embedUrl){
    if(typeof cardSearchRestoreFrame==='function')cardSearchRestoreFrame(snap.embedUrl);
    return;
  }
  if(kind==='root'||kind==='yt-list'||kind==='grid'&&snap.type==='img'){
    if(snap.embedUrl&&cardSearchState.type!=='yt'&&kind!=='yt-list'){
      if(typeof cardSearchRestoreFrame==='function')cardSearchRestoreFrame(snap.embedUrl);
      cardSearchState.view=snap.view||cardSearchState.view;
      return;
    }
    if((cardSearchState.type==='yt'||kind==='yt-list'||kind==='root'&&cardSearchState.type==='yt')&&kind!=='grid'){
      if(typeof showCardSearchFrame==='function')showCardSearchFrame(false);
      if(typeof renderCardYtList==='function')renderCardYtList(cardSearchState.ytItems||[],'');
      cardSearchState.view='yt';
      return;
    }
  }
"""

SEED_OLD = "  cardSearchState={type:type||'',popupUrl:popupUrl,embedUrl:'',history:[],query:query,name:name,view:'',results:[],images:[],_webData:null,urls:urls,_iframeLoads:0,_iframeHasStack:false};"

SEED_NEW = "  cardSearchState={type:type||'',popupUrl:popupUrl,embedUrl:'',history:[],query:query,name:name,view:'',results:[],images:[],_webData:null,urls:urls,_iframeLoads:0,_iframeHasStack:false,_embedFrameLoads:0,_embedUserInteracted:false,_landingEmbedUrl:''};"

MOUNT_OLD = """  if(typeof cardSearchMarkOwnFrameNav==='function')cardSearchMarkOwnFrameNav();
  if(typeof cardSearchBindFrameNav==='function')cardSearchBindFrameNav(frame);
  frame.src=url;
"""

MOUNT_NEW = """  cardSearchState._landingEmbedUrl=url;
  if(cardSearchState.history&&cardSearchState.history[0])cardSearchState.history[0].embedUrl=url;
  if(typeof cardSearchMarkOwnFrameNav==='function')cardSearchMarkOwnFrameNav();
  if(typeof cardSearchBindFrameNav==='function')cardSearchBindFrameNav(frame);
  frame.src=url;
"""

POP_OLD = """window.cardSearchPopEmbed=function(){
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

POP_NEW = """window.cardSearchPopEmbed=function(){
  if(!window.cardSearchState)window.cardSearchState={history:[]};
  if(!cardSearchState.history)cardSearchState.history=[];
  var hist=cardSearchState.history;
  var frame=document.getElementById('cardSearchFrame');
  var frameOn=!!(frame&&!frame.classList.contains('is-hidden')&&frame.contentWindow);
  var nested=!!(cardSearchState.view==='article'||cardSearchState.view==='image'||(cardSearchState.type==='yt'&&cardSearchState.ytId&&hist.length>1));
  if(hist.length>1){
    hist.pop();
    var prev=hist[hist.length-1];
    if(typeof cardSearchMarkOwnFrameNav==='function')cardSearchMarkOwnFrameNav();
    if(typeof cardSearchApplyHist==='function')cardSearchApplyHist(prev);
    else if(typeof prev==='string'&&frame){cardSearchState.embedUrl=prev;frame.src=prev;}
    cardSearchState._embedFrameLoads=Math.max(1,(cardSearchState._embedFrameLoads||1)-1);
    cardSearchState._iframeLoads=cardSearchState._embedFrameLoads;
    if(cardSearchState._embedFrameLoads<=1)cardSearchState._iframeHasStack=false;
    if(typeof cardSearchEnableBack==='function')cardSearchEnableBack();
    return true;
  }
  if(frameOn&&!nested&&(cardSearchState._iframeHasStack||(cardSearchState._embedFrameLoads||cardSearchState._iframeLoads||0)>1)){
    try{
      frame.contentWindow.history.back();
      cardSearchState._embedFrameLoads=Math.max(1,(cardSearchState._embedFrameLoads||1)-1);
      cardSearchState._iframeLoads=cardSearchState._embedFrameLoads;
      if(cardSearchState._embedFrameLoads<=1)cardSearchState._iframeHasStack=false;
      if(typeof cardSearchEnableBack==='function')cardSearchEnableBack();
      return true;
    }catch(errBack){}
    var land=cardSearchState._landingEmbedUrl||(hist[0]&&hist[0].embedUrl)||'';
    if(land){
      if(typeof cardSearchRestoreFrame==='function')cardSearchRestoreFrame(land);
      cardSearchState._iframeHasStack=false;
      cardSearchState._embedFrameLoads=1;
      cardSearchState._iframeLoads=1;
      if(typeof cardSearchEnableBack==='function')cardSearchEnableBack();
      return true;
    }
    return true;
  }
  return false;
};
window.cardSearchBack=function(){
  if(typeof window.cardSearchPopEmbed==='function'&&window.cardSearchPopEmbed())return;
  if(typeof closeCardSearchEmbed==='function')closeCardSearchEmbed();
};
"""

RELOAD_OLD = """if(frameOn&&src){
    try{"""

RELOAD_NEW = """if(frameOn&&src){
    if(typeof cardSearchMarkOwnFrameNav==='function')cardSearchMarkOwnFrameNav();
    try{"""


def patch(path: Path) -> None:
    raw0 = path.read_bytes()
    text = raw0.decode("utf-8")
    n = path.name
    text = once(text, BIND_OLD, BIND_NEW, "bind-nav", path)
    text = once(text, HISTEQ_OLD, HISTEQ_NEW, "histeq", path)
    text = once(text, APPLY_OLD, APPLY_NEW, "apply-hist", path)
    text = once(text, SEED_OLD, SEED_NEW, "seed", path)
    text = once(text, MOUNT_OLD, MOUNT_NEW, "mount-google", path)
    text = once(text, POP_OLD, POP_NEW, "pop-back", path)
    text = once(text, RELOAD_OLD, RELOAD_NEW, "reload-own", path)
    for mark in (
        "cardSearchOnFrameNav",
        "cardSearchRestoreFrame",
        "_embedUserInteracted",
        "_embedFrameLoads",
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
