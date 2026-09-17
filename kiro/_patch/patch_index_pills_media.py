#!/usr/bin/env python3
from pathlib import Path

FILES = [
    Path("/home/phnx/kiro-kontakt-patch/public/catalogs/DS-CATALOG.html"),
    Path("/home/phnx/kiro-kontakt-patch/public/catalogs/DS-CATALOG-portable.html"),
    Path("/home/phnx/kiro-kontakt-patch/public/catalogs/KONTAKT-CATALOG.html"),
    Path("/home/phnx/kiro-kontakt-patch/public/catalogs/KONTAKT-CATALOG-portable.html"),
    Path("/home/phnx/kiro-kontakt-patch/kiro/specs/kontakt-workspace-drive-dirty-fix/artifacts/build-ds-catalog-html.sh"),
    Path("/home/phnx/kiro-kontakt-patch/kiro/specs/kontakt-workspace-drive-dirty-fix/artifacts/build-kontakt-catalog-html.sh"),
]

CSS_PILL = (
    "#cardMinDock .card-min-pill{pointer-events:auto;display:inline-flex;align-items:center;"
    "gap:.45rem;max-width:min(14.5rem,34%);min-height:2.85rem;padding:.35rem .95rem .35rem .35rem;"
    "border:1px solid var(--accent-instrument);border-radius:999px;background:var(--bg-card);"
    "color:var(--accent-instrument);font:inherit;font-size:1rem;font-weight:650;letter-spacing:.01em;"
    "line-height:1.15;cursor:pointer;touch-action:manipulation;box-shadow:0 8px 28px rgba(0,0,0,.38);"
    "transform-origin:center bottom;transition:transform .14s ease,opacity .14s ease,box-shadow .14s ease,"
    "border-color .14s ease;opacity:.92}"
)

CSS_PILL_NEW = r"""#cardMinDock .card-min-pill{pointer-events:auto;display:inline-flex;align-items:center;gap:.35rem;max-width:min(16.5rem,42%);min-height:2.85rem;padding:.28rem;border:1px solid var(--accent-instrument);border-radius:999px;background:var(--bg-card);color:var(--accent-instrument);font:inherit;font-size:1rem;font-weight:650;letter-spacing:.01em;line-height:1.15;cursor:default;touch-action:manipulation;box-shadow:0 8px 28px rgba(0,0,0,.38);transform-origin:center bottom;transition:transform .14s ease,opacity .14s ease,box-shadow .14s ease,border-color .14s ease;opacity:.92}
#cardMinDock .card-min-open{pointer-events:auto;display:inline-flex;align-items:center;gap:.45rem;min-width:0;flex:1 1 auto;margin:0;padding:.15rem .2rem .15rem .15rem;border:0;background:transparent;color:inherit;font:inherit;font-weight:inherit;cursor:pointer;border-radius:999px}
#cardMinDock .card-min-media{display:none;flex:0 0 auto;width:2.15rem;height:2.15rem;border-radius:999px;overflow:hidden;border:1px solid var(--border);background:#000;position:relative}
#cardMinDock .card-min-pill.is-playing .card-min-media{display:block}
#cardMinDock .card-min-pill.is-playing .card-min-open>img{display:none}
#cardMinDock .card-min-media .card-search-embed,#cardMinDock .card-min-media #cardSearchEmbed{display:block!important;position:absolute;inset:-40% -70%;width:240%;height:180%;border:0;border-radius:0;background:#000;pointer-events:none}
#cardMinDock .card-min-media .card-search-chrome,#cardMinDock .card-min-media .card-yt-comments,#cardMinDock .card-min-media .card-search-hint,#cardMinDock .card-min-media .card-search-fallback,#cardMinDock .card-min-media .card-search-reader,#cardMinDock .card-min-media .card-search-img-view,#cardMinDock .card-min-media .card-img-exit{display:none!important}
#cardMinDock .card-min-media .card-search-frame,#cardMinDock .card-min-media #cardSearchFrame{display:block!important;width:100%!important;height:100%!important;border:0;pointer-events:none}
#cardMinDock .card-min-close{pointer-events:auto;flex:0 0 auto;width:1.65rem;height:1.65rem;margin:0;padding:0;border:1px solid var(--border);border-radius:999px;background:var(--bg-surface);color:var(--text);font:inherit;font-size:1.05rem;line-height:1;cursor:pointer}
#cardMinDock .card-min-close:hover{color:var(--accent-instrument);border-color:var(--accent-instrument);background:var(--accent-instrument-bg)}"""

IDX_LI = (
    "body.display-sides #catalogIndex .index li{display:flex!important;align-items:flex-start;gap:.28em;"
    "box-sizing:border-box;margin:.12rem 0;padding:0;max-width:100%;min-width:0;min-height:1.4em;"
    "line-height:1.35;overflow:visible;white-space:normal;overflow-wrap:anywhere;word-break:break-word;list-style:none}"
)
IDX_LI_NEW = IDX_LI.replace("overflow:visible", "overflow:hidden;isolation:isolate;position:relative;z-index:0")

IDX_LI_ALT = (
    "body.display-sides #catalogIndex .index li{display:flex!important;align-items:flex-start;gap:.28em;"
    "min-height:1.35em;line-height:1.35;overflow:visible;white-space:normal;overflow-wrap:anywhere;word-break:break-word}"
)
IDX_LI_ALT_NEW = IDX_LI_ALT.replace("overflow:visible", "overflow:hidden;isolation:isolate;position:relative")

DISMISS_OLD = """function cardMinDismissOpen(){
  var el=cardMinExpanded();
  if(!el||!el.id)return;
  var i=cardMinIndex(el.id);
  if(i<0)return;
  cardMinDockItems.splice(i,1);
  cardMinRender();
}"""

DISMISS_NEW = r"""function cardMinDismissOpen(){
  var el=cardMinExpanded();
  if(!el||!el.id)return;
  cardMinClose(el.id,true);
}
function cardMinYtCmd(fn){
  var f=document.getElementById('cardSearchFrame');
  if(f&&f.contentWindow){
    try{f.contentWindow.postMessage(JSON.stringify({event:'command',func:fn,args:[]}),'*');}catch(err){}
  }
  var yt=window.cardSearchState&&cardSearchState._ytPlayer;
  if(yt&&typeof yt[fn]==='function'){try{yt[fn]();}catch(err){}}
}
function cardMinMediaPlaying(){
  var f=document.getElementById('cardSearchFrame');
  if(!f)return false;
  var src=f.getAttribute('src')||'';
  if(!src||src==='about:blank')return false;
  if(f.classList.contains('is-hidden'))return false;
  return !!(document.body.classList.contains('card-embed-open')||(window.cardSearchState&&(cardSearchState.ytId||cardSearchState.embedUrl||src)));
}
function cardMinPauseMedia(){cardMinYtCmd('pauseVideo');}
function cardMinPlayMedia(){cardMinYtCmd('playVideo');}
function cardMinParkMedia(id){
  window.cardMinMediaOwnerId=id||'';
  if(!id||!cardMinMediaPlaying())return;
  cardMinRender();
  var slot=document.querySelector('#cardMinDock .card-min-pill[data-card-min-id="'+id+'"] .card-min-media');
  var host=document.getElementById('cardSearchEmbed');
  if(!slot||!host)return;
  host.hidden=false;
  slot.appendChild(host);
  cardMinPlayMedia();
  // #region agent log
  try{var fr=document.getElementById('cardSearchFrame');fetch('http://127.0.0.1:7529/ingest/1cf46354-1d61-4c80-bd72-a340f1db1b51',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'f491c2'},body:JSON.stringify({sessionId:'f491c2',runId:'post-fix',hypothesisId:'H4',location:'cardMinParkMedia',message:'park-media',data:{id:id,src:(fr&&fr.getAttribute('src')||'').slice(0,80),inPill:!!(host.parentElement&&host.parentElement.classList.contains('card-min-media'))},timestamp:Date.now()})}).catch(function(){});}catch(err){}
  // #endregion
}
function cardMinRestoreMedia(id){
  var host=document.getElementById('cardSearchEmbed');
  var card=id&&document.getElementById(id);
  if(!host)return;
  if(window.cardMinMediaOwnerId===id&&card){
    host.hidden=false;
    document.body.classList.add('card-embed-open');
    if(!card.contains(host)){
      var dest=card.querySelector('.card-actions')||card;
      dest.appendChild(host);
    }
    cardMinPlayMedia();
  }else{
    cardMinPauseMedia();
  }
}
function cardMinClose(id,fromOpen){
  if(!id)return;
  var i=cardMinIndex(id);
  var wasOwner=window.cardMinMediaOwnerId===id;
  if(wasOwner){
    window.cardMinMediaOwnerId='';
    if(typeof closeCardSearchEmbed==='function')closeCardSearchEmbed();
  }
  if(i>=0)cardMinDockItems.splice(i,1);
  var cur=cardMinExpanded();
  if(cur&&cur.id===id&&!fromOpen){
    if(document.body.classList.contains('hl-open')||cur.classList.contains('highlight'))closeOverlay({skipScroll:true});
    else if(document.body.classList.contains('chosen-preview-open'))closeChosenPreview({skipJumpExit:true,skipDismiss:true,keepMedia:true});
  }
  cardMinRender();
  // #region agent log
  try{fetch('http://127.0.0.1:7529/ingest/1cf46354-1d61-4c80-bd72-a340f1db1b51',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'f491c2'},body:JSON.stringify({sessionId:'f491c2',runId:'post-fix',hypothesisId:'H6',location:'cardMinClose',message:'close-unpin',data:{id:id,fromOpen:!!fromOpen,wasOwner:wasOwner,n:cardMinDockItems.length},timestamp:Date.now()})}).catch(function(){});}catch(err){}
  // #endregion
}"""

OLD_FIT = (
    "  il.style.removeProperty('columns');\n"
    "  il.style.removeProperty('column-width');\n"
    "  il.style.removeProperty('column-count');\n"
    "  il.style.removeProperty('column-fill');"
)
NEW_FIT = (
    "  il.style.setProperty('columns','none');\n"
    "  il.style.setProperty('column-width','auto');\n"
    "  il.style.setProperty('column-count','1');\n"
    "  il.style.removeProperty('column-fill');"
)


def apply(t: str, name: str) -> str:
    print("FILE", name)
    box = [t]

    def do(src: str, dst: str, label: str) -> None:
        c = box[0].count(src)
        if not c:
            print("  MISS", label)
            return
        box[0] = box[0].replace(src, dst)
        print(" ", label, "x" + str(c))

    do(
        "columns:auto!important;column-width:auto!important;column-count:auto!important",
        "columns:none!important;column-width:auto!important;column-count:1!important;column-fill:auto!important",
        "cols-none",
    )
    t2 = box[0].replace(
        "overflow-y:auto!important;columns:auto!important;list-style:none",
        "overflow-y:auto!important;columns:none!important;column-count:1!important;list-style:none",
    )
    if t2 != box[0]:
        print("  mobile-cols")
        box[0] = t2
    if IDX_LI in box[0]:
        box[0] = box[0].replace(IDX_LI, IDX_LI_NEW)
        print("  idx-li")
    elif IDX_LI_ALT in box[0]:
        box[0] = box[0].replace(IDX_LI_ALT, IDX_LI_ALT_NEW)
        print("  idx-li-alt")
    else:
        print("  MISS idx-li")
    do(CSS_PILL, CSS_PILL_NEW, "pill-css")
    do(DISMISS_OLD, DISMISS_NEW, "dismiss")
    do(OLD_FIT, NEW_FIT, "fit-cols")
    return box[0]


def main() -> None:
    for p in FILES:
        text = p.read_text(encoding="utf-8", errors="replace")
        p.write_text(apply(text, p.name), encoding="utf-8")
        print("  wrote")


if __name__ == "__main__":
    main()
