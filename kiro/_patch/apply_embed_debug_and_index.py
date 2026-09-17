#!/usr/bin/env python3
"""Instrument embed back/refresh/YT + add nested collapsible Index pane."""
from pathlib import Path

INGEST = "http://127.0.0.1:7529/ingest/1cf46354-1d61-4c80-bd72-a340f1db1b51"
HDR = "{'Content-Type':'application/json','X-Debug-Session-Id':'f491c2'}"


def log(hid, loc, msg, data_js):
    return (
        "  // #region agent log\n"
        "  (function(){"
        + data_js
        + "fetch('"
        + INGEST
        + "',{method:'POST',headers:"
        + HDR
        + ",body:JSON.stringify({sessionId:'f491c2',runId:'pre-fix',hypothesisId:'"
        + hid
        + "',location:'"
        + loc
        + "',message:'"
        + msg
        + "',data:d,timestamp:Date.now()})}).catch(function(){});})();\n"
        "  // #endregion\n"
    )


INDEX_HTML = """    <div class="card-search-index" id="cardSearchIndex">
      <div class="card-search-index-bar">
        <button type="button" class="card-search-index-toggle" id="cardSearchIndexToggle" aria-label="Show index" aria-expanded="false" title="Show index" onclick="event.preventDefault();event.stopPropagation();cardToggleEmbedIndex()"><span class="toggle-arrow">&#9654;</span></button>
        <span class="card-search-index-name">Index</span>
      </div>
      <div class="card-search-index-body" hidden>
        <ul class="index" id="cardSearchIndexList"></ul>
      </div>
    </div>
"""

INDEX_CSS = """ .card-search-index{display:none;flex-direction:column;flex:0 0 auto;min-width:0;width:100%;max-height:42%;background:var(--bg-card);border-bottom:1px solid var(--border);z-index:4}
 body.card-embed-open .card-search-index{display:flex}
 .card-search-index-bar{display:flex;align-items:center;gap:6px;flex:0 0 auto;padding:4px 8px 4px 4px;min-height:2.75rem}
 .card-search-index-toggle{box-sizing:border-box;min-width:2.75rem;min-height:2.75rem;padding:0;border:1px solid var(--border);border-radius:8px;background:var(--bg-surface);color:var(--text);font:inherit;cursor:pointer;touch-action:manipulation;display:flex;align-items:center;justify-content:center}
 .card-search-index-toggle:hover{border-color:var(--accent-instrument);color:var(--accent-instrument);background:var(--accent-instrument-bg)}
 .card-search-index-name{font-size:.9375rem;color:var(--text-muted);font-weight:600}
 .card-search-index-body{display:none;flex:1 1 auto;min-height:0;overflow:auto;-webkit-overflow-scrolling:touch}
 .card-search-index.is-open .card-search-index-body{display:block}
 .card-search-index .index{column-width:11rem;padding:8px 12px 12px;margin:0;font-size:.85rem}
 .card-search-stage.yt-wide .card-search-index{width:auto;max-height:none;height:100%;border-bottom:0;border-right:1px solid var(--border)}
 .card-search-stage.yt-wide .card-search-index.is-open{flex:0 1 min(16rem,38%);max-width:min(16rem,42%)}
"""

INDEX_JS = """function cardSearchFillIndex(){
  var list=document.getElementById('cardSearchIndexList');
  if(!list)return;
  var src=null;
  document.querySelectorAll('ul.index').forEach(function(ul){if(ul.id!=='cardSearchIndexList'&&!src)src=ul;});
  list.innerHTML=src?src.innerHTML:'';
}
window.cardToggleEmbedIndex=function(){
  var box=document.getElementById('cardSearchIndex');
  if(!box)return;
  var on=!box.classList.contains('is-open');
  box.classList.toggle('is-open',on);
  var btn=document.getElementById('cardSearchIndexToggle');
  var arrow=btn&&btn.querySelector('.toggle-arrow');
  var body=box.querySelector('.card-search-index-body');
  if(btn){btn.setAttribute('aria-expanded',on?'true':'false');btn.setAttribute('aria-label',on?'Hide index':'Show index');btn.title=on?'Hide index':'Show index';}
  if(arrow)arrow.innerHTML=on?'\\u25bc':'\\u25b6';
  if(body)body.hidden=!on;
};
"""

REPLACEMENTS = [
    (
        "index-css",
        " .card-search-stage.yt-wide .card-search-fallback{right:auto;width:55%;}\n",
        " .card-search-stage.yt-wide .card-search-fallback{right:auto;width:55%;}\n" + INDEX_CSS,
    ),
    (
        "index-html",
        '    <iframe class="card-search-frame" id="cardSearchFrame"',
        INDEX_HTML + '    <iframe class="card-search-frame" id="cardSearchFrame"',
    ),
    (
        "index-js",
        "function openCardSearchEmbed(type,popupUrl){",
        INDEX_JS + "function openCardSearchEmbed(type,popupUrl){",
    ),
    (
        "index-fill",
        "  paintCardSearchSwitch();\n  syncCardSearchLayout();\n  cardSearchShowEmbedHint();\n  return true;\n}\nwindow.cardSearchBack=function(){",
        "  paintCardSearchSwitch();\n  syncCardSearchLayout();\n  cardSearchFillIndex();\n  cardSearchShowEmbedHint();\n"
        + log(
            "E4",
            "openCardSearchEmbed",
            "embed-open",
            "var cm=document.getElementById('cardYtComments');var list=document.getElementById('cardYtList');var ix=document.getElementById('cardSearchIndexList');var d={type:type,url:String(popupUrl||'').slice(0,180),q:query||'',hasPane:!!cm,hasList:!!list,idxN:ix?ix.children.length:0};",
        )
        + "  return true;\n}\nwindow.cardSearchBack=function(){",
    ),
    (
        "back",
        "  var frame=document.getElementById('cardSearchFrame');\n  // Try iframe history for any type with a visible frame (not just yt)\n",
        "  var frame=document.getElementById('cardSearchFrame');\n"
        + log(
            "E1",
            "cardSearchBack",
            "embed-back",
            "var locOk=false,locErr='',hlen=null,src=(frame&&frame.src)||'';try{locOk=!!(frame&&frame.contentWindow&&frame.contentWindow.location&&frame.contentWindow.location.href);hlen=frame.contentWindow.history.length;}catch(e){locErr=String(e&&e.message||e);}var d={type:cardSearchState.type,view:cardSearchState.view,src:src.slice(0,180),embedUrl:String(cardSearchState.embedUrl||'').slice(0,180),locOk:locOk,locErr:locErr,hlen:hlen,stackN:(cardSearchState.history||[]).length,frameHid:!!(frame&&frame.classList.contains('is-hidden'))};",
        )
        + "  // Try iframe history for any type with a visible frame (not just yt)\n",
    ),
    (
        "reload",
        "window.cardSearchReload=function(){\n  cardSearchEnableBack();\n  var frame=document.getElementById('cardSearchFrame');\n  if(cardSearchState.type==='yt'){\n",
        "window.cardSearchReload=function(){\n  cardSearchEnableBack();\n  var frame=document.getElementById('cardSearchFrame');\n"
        + log(
            "E3",
            "cardSearchReload",
            "embed-reload",
            "var cur='',curErr='';try{cur=frame&&frame.contentWindow&&frame.contentWindow.location&&frame.contentWindow.location.href||'';}catch(e){curErr=String(e&&e.message||e);}var d={type:cardSearchState.type,view:cardSearchState.view,embedUrl:String(cardSearchState.embedUrl||'').slice(0,180),frameSrc:String((frame&&frame.src)||'').slice(0,180),cur:String(cur).slice(0,180),curErr:curErr,popupUrl:String(cardSearchState.popupUrl||'').slice(0,180)};",
        )
        + "  if(cardSearchState.type==='yt'){\n",
    ),
    (
        "iframe-back",
        "window.cardSearchIframeBack=function(){\n  var frame=document.getElementById('cardSearchFrame');\n  if(!frame||!frame.contentWindow)return;\n  try{frame.contentWindow.history.back();}catch(err){}\n};",
        "window.cardSearchIframeBack=function(){\n  var frame=document.getElementById('cardSearchFrame');\n"
        + log(
            "E2",
            "cardSearchIframeBack",
            "embed-iframe-back",
            "var locOk=false,locErr='',hlen=null;try{locOk=!!(frame&&frame.contentWindow&&frame.contentWindow.location&&frame.contentWindow.location.href);hlen=frame.contentWindow.history.length;}catch(e){locErr=String(e&&e.message||e);}var d={type:cardSearchState.type,src:String((frame&&frame.src)||'').slice(0,180),locOk:locOk,locErr:locErr,hlen:hlen,noCw:!frame||!frame.contentWindow};",
        )
        + "  if(!frame||!frame.contentWindow)return;\n  try{frame.contentWindow.history.back();}catch(err){}\n};",
    ),
    (
        "yt-layout",
        "  stage.classList.toggle('yt-split',!!(yt&&!land));\n  stage.classList.toggle('yt-wide',!!(yt&&land));\n  if(yt){fillYtCommentsStrip();cardRestoreYtListState();}\n}",
        "  stage.classList.toggle('yt-split',!!(yt&&!land));\n  stage.classList.toggle('yt-wide',!!(yt&&land));\n  if(yt){fillYtCommentsStrip();cardRestoreYtListState();}\n"
        + log(
            "E5",
            "syncCardSearchLayout",
            "yt-layout",
            "var cm=document.getElementById('cardYtComments');var list=document.getElementById('cardYtList');var cs=cm?getComputedStyle(cm):null;var d={yt:!!yt,land:!!land,stage:stage.className,cmDisp:cs&&cs.display,cmW:cm&&Math.round(cm.getBoundingClientRect().width),kids:list?list.children.length:0,n:(cardSearchState.ytItems||[]).length,listTxt:list?String(list.textContent||'').slice(0,40):'',collapsed:stage.classList.contains('yt-list-collapsed')};",
        )
        + "}",
    ),
]

MSG = {
    "index-css": "card-search-index{",
    "index-html": 'id="cardSearchIndex"',
    "index-js": "function cardSearchFillIndex()",
    "index-fill": "message:'embed-open'",
    "back": "message:'embed-back'",
    "reload": "message:'embed-reload'",
    "iframe-back": "message:'embed-iframe-back'",
    "yt-layout": "message:'yt-layout'",
}


def apply(path: Path) -> bool:
    text = path.read_text(encoding="utf-8", errors="surrogateescape")
    applied, already, missing = [], [], []
    for label, old, new in REPLACEMENTS:
        n = text.count(old)
        if n == 0:
            if MSG[label] in text:
                already.append(label)
            else:
                missing.append(label)
            continue
        if n != 1:
            raise SystemExit(f"COUNT {path} [{label}]: {n}")
        text = text.replace(old, new, 1)
        applied.append(label)
    if missing:
        print(f"MISSING {path}: {missing} already={already} applied={applied}")
        return False
    path.write_text(text, encoding="utf-8", errors="surrogateescape")
    print(f"OK {path.name} applied={applied} already={already}")
    return True


def main():
    files = [
        Path("/home/phnx/kiro-kontakt-patch/kiro/specs/kontakt-workspace-drive-dirty-fix/artifacts/build-ds-catalog-html.sh"),
        Path("/home/phnx/kiro-kontakt-patch/kiro/specs/kontakt-workspace-drive-dirty-fix/artifacts/build-kontakt-catalog-html.sh"),
        Path("/home/phnx/kiro-kontakt-patch/kiro/specs/kontakt-workspace-drive-dirty-fix/artifacts/DS-CATALOG.html"),
        Path("/home/phnx/kiro-kontakt-patch/kiro/specs/kontakt-workspace-drive-dirty-fix/artifacts/DS-CATALOG-portable.html"),
        Path("/home/phnx/kiro-kontakt-patch/kiro/specs/kontakt-workspace-drive-dirty-fix/artifacts/KONTAKT-CATALOG.html"),
        Path("/home/phnx/kiro-kontakt-patch/kiro/specs/kontakt-workspace-drive-dirty-fix/artifacts/KONTAKT-CATALOG-portable.html"),
        Path("/home/phnx/kiro-kontakt-patch/public/catalogs/DS-CATALOG.html"),
        Path("/home/phnx/kiro-kontakt-patch/public/catalogs/DS-CATALOG-portable.html"),
        Path("/home/phnx/kiro-kontakt-patch/public/catalogs/KONTAKT-CATALOG.html"),
        Path("/home/phnx/kiro-kontakt-patch/public/catalogs/KONTAKT-CATALOG-portable.html"),
    ]
    ok = True
    for p in files:
        if not p.exists():
            print(f"SKIP missing {p}")
            continue
        if not apply(p):
            ok = False
            continue
        if p.suffix == ".html":
            data = p.read_text(encoding="utf-8", errors="surrogateescape")
            if "</html>" not in data:
                raise SystemExit(f"NO </html> {p}")
            if "function hideSearchAc" not in data:
                raise SystemExit(f"NO hideSearchAc {p}")
            print(f"  assert ok {p.name} bytes={p.stat().st_size}")
    if not ok:
        raise SystemExit("some patches missing")
    print("DONE")


if __name__ == "__main__":
    main()
