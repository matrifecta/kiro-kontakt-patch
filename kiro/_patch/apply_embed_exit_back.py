#!/usr/bin/env python3
"""← exits embed to the extended card; ↶ is one-step back for any page after default."""
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


def once(text, old, new, label, path):
    n = text.count(old)
    if n != 1:
        raise SystemExit(f"{path.name}: {label} count={n} expected 1")
    return text.replace(old, new, 1)


def splice(text, start, end, new, label, path):
    i = text.find(start)
    if i < 0:
        raise SystemExit(f"{path.name}: {label} start not found")
    if text.find(start, i + 1) != -1:
        raise SystemExit(f"{path.name}: {label} start not unique")
    j = text.find(end, i)
    if j < 0:
        raise SystemExit(f"{path.name}: {label} end not found")
    return text[:i] + new + text[j:]


TITLE_OLD = 'title="Back one step in video"'
TITLE_NEW = 'title="Back one step in page"'

ENABLE_OLD = """function cardSearchEnableBack(){
  var back=document.querySelector('#cardSearchEmbed .card-search-back');
  if(back){back.disabled=false;back.removeAttribute('disabled');}
}
"""

ENABLE_NEW = """function cardSearchEnableBack(){
  var back=document.querySelector('#cardSearchEmbed .card-search-back');
  if(back){back.disabled=false;back.removeAttribute('disabled');}
  var step=document.querySelector('#cardSearchEmbed .card-search-iframe-back');
  if(step){
    var n=(cardSearchState&&cardSearchState.history||[]).length;
    var frame=document.getElementById('cardSearchFrame');
    var frameOn=!!(frame&&!frame.classList.contains('is-hidden')&&(frame.getAttribute('src')||''));
    var can=n>1||!!(cardSearchState&&(cardSearchState.view==='article'||cardSearchState.view==='image'||(cardSearchState.type==='yt'&&(cardSearchState.ytId||frameOn))));
    step.disabled=!can;
    if(can)step.removeAttribute('disabled');
    else step.setAttribute('disabled','');
  }
}
"""

BACK_OLD = """window.cardSearchBack=function(){
  var frame=document.getElementById('cardSearchFrame');
  // #region agent log
  (function(){var locOk=false,locErr='',hlen=null,src=(frame&&frame.src)||'';try{locOk=!!(frame&&frame.contentWindow&&frame.contentWindow.location&&frame.contentWindow.location.href);hlen=frame.contentWindow.history.length;}catch(e){locErr=String(e&&e.message||e);}var d={type:cardSearchState.type,view:cardSearchState.view,src:src.slice(0,180),embedUrl:String(cardSearchState.embedUrl||'').slice(0,180),locOk:locOk,locErr:locErr,hlen:hlen,stackN:(cardSearchState.history||[]).length,frameHid:!!(frame&&frame.classList.contains('is-hidden'))};fetch('http://127.0.0.1:7529/ingest/1cf46354-1d61-4c80-bd72-a340f1db1b51',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'f491c2'},body:JSON.stringify({sessionId:'f491c2',runId:'pre-fix',hypothesisId:'E1',location:'cardSearchBack',message:'embed-back',data:d,timestamp:Date.now()})}).catch(function(){});})();
  // #endregion
  if(!cardSearchState.history)cardSearchState.history=[];
  if(cardSearchState.history.length>1){
    cardSearchState.history.pop();
    var prev=cardSearchState.history[cardSearchState.history.length-1];
    if(typeof cardSearchApplyHist==='function')cardSearchApplyHist(prev);
    else if(typeof prev==='string'&&frame){cardSearchState.embedUrl=prev;frame.src=prev;}
    cardSearchEnableBack();
    return;
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

BACK_NEW = """window.cardSearchBack=function(){
  var frame=document.getElementById('cardSearchFrame');
  // #region agent log
  (function(){var locOk=false,locErr='',hlen=null,src=(frame&&frame.src)||'';try{locOk=!!(frame&&frame.contentWindow&&frame.contentWindow.location&&frame.contentWindow.location.href);hlen=frame.contentWindow.history.length;}catch(e){locErr=String(e&&e.message||e);}var d={type:cardSearchState.type,view:cardSearchState.view,src:src.slice(0,180),embedUrl:String(cardSearchState.embedUrl||'').slice(0,180),locOk:locOk,locErr:locErr,hlen:hlen,stackN:(cardSearchState.history||[]).length,frameHid:!!(frame&&frame.classList.contains('is-hidden')),embedOpen:document.body.classList.contains('card-embed-open'),preview:document.body.classList.contains('chosen-preview-open')};fetch('http://127.0.0.1:7529/ingest/1cf46354-1d61-4c80-bd72-a340f1db1b51',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'f491c2'},body:JSON.stringify({sessionId:'f491c2',runId:'post-fix',hypothesisId:'E1',location:'cardSearchBack',message:'embed-back',data:d,timestamp:Date.now()})}).catch(function(){});})();
  fetch('http://127.0.0.1:7529/ingest/1cf46354-1d61-4c80-bd72-a340f1db1b51',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'c00e3e'},body:JSON.stringify({sessionId:'c00e3e',runId:'post-fix',hypothesisId:'H1',location:'cardSearchBack',message:'exit-to-card',data:{type:cardSearchState.type,view:cardSearchState.view,stackN:(cardSearchState.history||[]).length,embedOpen:document.body.classList.contains('card-embed-open')},timestamp:Date.now()})}).catch(function(){});
  // #endregion
  if(typeof closeCardSearchEmbed==='function')closeCardSearchEmbed();
};
"""

IFRAME_OLD = """window.cardSearchIframeBack=function(){
  var frame=document.getElementById('cardSearchFrame');
  // #region agent log
  (function(){var locOk=false,locErr='',hlen=null;try{locOk=!!(frame&&frame.contentWindow&&frame.contentWindow.location&&frame.contentWindow.location.href);hlen=frame.contentWindow.history.length;}catch(e){locErr=String(e&&e.message||e);}var d={type:cardSearchState.type,src:String((frame&&frame.src)||'').slice(0,180),locOk:locOk,locErr:locErr,hlen:hlen,noCw:!frame||!frame.contentWindow};fetch('http://127.0.0.1:7529/ingest/1cf46354-1d61-4c80-bd72-a340f1db1b51',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'f491c2'},body:JSON.stringify({sessionId:'f491c2',runId:'pre-fix',hypothesisId:'E2',location:'cardSearchIframeBack',message:'embed-iframe-back',data:d,timestamp:Date.now()})}).catch(function(){});})();
  // #endregion
  if(!frame||!frame.contentWindow)return;
  try{frame.contentWindow.history.back();}catch(err){}
};
"""

IFRAME_NEW = """window.cardSearchIframeBack=function(){
  var frame=document.getElementById('cardSearchFrame');
  // #region agent log
  (function(){var locOk=false,locErr='',hlen=null;try{locOk=!!(frame&&frame.contentWindow&&frame.contentWindow.location&&frame.contentWindow.location.href);hlen=frame.contentWindow.history.length;}catch(e){locErr=String(e&&e.message||e);}var d={type:cardSearchState.type,view:cardSearchState.view,src:String((frame&&frame.src)||'').slice(0,180),locOk:locOk,locErr:locErr,hlen:hlen,noCw:!frame||!frame.contentWindow,stackN:(cardSearchState.history||[]).length,frameHid:!!(frame&&frame.classList.contains('is-hidden'))};fetch('http://127.0.0.1:7529/ingest/1cf46354-1d61-4c80-bd72-a340f1db1b51',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'f491c2'},body:JSON.stringify({sessionId:'f491c2',runId:'post-fix',hypothesisId:'E2',location:'cardSearchIframeBack',message:'embed-iframe-back',data:d,timestamp:Date.now()})}).catch(function(){});})();
  fetch('http://127.0.0.1:7529/ingest/1cf46354-1d61-4c80-bd72-a340f1db1b51',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'c00e3e'},body:JSON.stringify({sessionId:'c00e3e',runId:'post-fix',hypothesisId:'H2',location:'cardSearchIframeBack',message:'step-back',data:{type:cardSearchState.type,view:cardSearchState.view,stackN:(cardSearchState.history||[]).length},timestamp:Date.now()})}).catch(function(){});
  // #endregion
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


def patch(text, path):
    if TITLE_OLD in text:
        text = once(text, TITLE_OLD, TITLE_NEW, "iframe-title", path)
    if ENABLE_OLD in text:
        text = once(text, ENABLE_OLD, ENABLE_NEW, "enable-back", path)
    i = text.find("window.cardSearchBack=function(){")
    if i >= 0 and "closeCardSearchEmbed" not in text[i : i + 1200]:
        text = splice(
            text,
            "window.cardSearchBack=function(){",
            "window.cardSearchReload=function(){",
            BACK_NEW,
            "cardSearchBack",
            path,
        )
    i = text.find("window.cardSearchIframeBack=function(){")
    body = text[i : i + 2200] if i >= 0 else ""
    if i >= 0 and "cardSearchState.history.length>1" not in body:
        end = None
        rest = text[i:]
        if "function syncCardSearchLayout(){" in rest[:2500]:
            end = "function syncCardSearchLayout(){"
        elif "window.syncCardSearchLayout=syncCardSearchLayout;" in rest[:2500]:
            end = "window.syncCardSearchLayout=syncCardSearchLayout;"
        if not end:
            raise SystemExit(f"{path.name}: iframe-back end not found")
        text = splice(
            text,
            "window.cardSearchIframeBack=function(){",
            end,
            IFRAME_NEW,
            "iframe-back",
            path,
        )
    return text


def main():
    for path in FILES:
        text = path.read_text(encoding="utf-8")
        new = patch(text, path)
        path.write_text(new, encoding="utf-8")
        print(f"patched {path.name}")


if __name__ == "__main__":
    main()
