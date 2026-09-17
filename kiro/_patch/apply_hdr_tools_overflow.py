#!/usr/bin/env python3
"""Desktop portrait header: collapse extra toolbar actions behind a pyramid."""
from pathlib import Path

ROOT = Path("/home/phnx/kiro-kontakt-patch")
FILES = [
    ROOT / "public/catalogs/KONTAKT-CATALOG.html",
    ROOT / "public/catalogs/DS-CATALOG.html",
]
MARK = "fix-HDR-TOOLS-OVERFLOW-v1"
KEEP = (
    "c00e3e",
    "index-embed-alignment-clash",
    "fix-INDEX-EMBED-SEP-v2",
    MARK,
)
CSS_MARK = "</style></head><body class=\"search-mode\">"

CSS_ADD = r"""
/* fix-HDR-TOOLS-OVERFLOW-v1: desktop portrait — extra toolbar actions behind a pyramid */
#hdrToolsMore{
  flex:0 0 auto;display:none;align-items:center;justify-content:center;
  box-sizing:border-box;min-width:2.25rem;min-height:2.25rem;padding:0 .4rem;margin:0;
  border:1px solid var(--border);border-radius:4px;background:transparent;color:var(--text-muted);
  cursor:pointer;touch-action:manipulation;font:inherit;line-height:1;position:relative;z-index:3
}
#hdrToolsMore:hover,#hdrToolsMore[aria-expanded="true"]{
  border-color:var(--accent-instrument);color:var(--accent-instrument);background:var(--accent-instrument-bg)
}
#hdrToolsMore .toggle-arrow{display:inline-block;font-size:.85rem;line-height:1;transition:transform .2s}
body.hdr-tools-open #hdrToolsMore .toggle-arrow{transform:rotate(180deg)}
#hdrToolsRow2{
  display:none;flex:1 0 100%;flex-wrap:nowrap;align-items:center;justify-content:flex-end;
  gap:.4rem;min-width:0;max-width:100%;order:80;box-sizing:border-box
}
#hdrToolsRow2>*{flex:0 0 auto!important}
#hdrToolsRow2 #uiScale{margin-left:0;flex:0 0 auto!important}
#hdrToolsRow2 .layout-presets,#hdrToolsRow2 #layoutPresets{
  width:auto!important;max-width:none!important;flex:0 0 auto!important;padding:0!important;flex-wrap:nowrap!important
}
#hdrToolsRow2 .layout-presets-pop,#hdrToolsRow2 #layoutPresetsPop:not(.open){display:none!important}
#hdrToolsRow2 .layout-presets-pop.open,#hdrToolsRow2 #layoutPresetsPop.open{display:flex!important}
.hdr-tools-more-pop{
  position:absolute;z-index:380;top:calc(100% + 4px);left:0;right:auto;
  display:flex;flex-direction:column;gap:.35rem;min-width:min(12rem,calc(100vw - 1.5rem));
  padding:.4rem;background:var(--bg-surface);border:1px solid var(--border);border-radius:8px;
  box-shadow:0 12px 28px rgba(0,0,0,.38);box-sizing:border-box
}
.hdr-tools-more-pop[hidden]{display:none!important}
body.catalog-portable #hdrToolsMore,
body.catalog-portable #hdrToolsRow2,
body.catalog-portable #hdrToolsMorePop{display:none!important}
@media(min-width:900px) and (orientation:portrait){
  body:not(.catalog-portable) .catalog-header{
    display:grid!important;
    grid-template-columns:max-content minmax(0,1fr)!important;
    grid-template-rows:auto!important;
    align-items:start;column-gap:.5rem;row-gap:.35rem
  }
  body:not(.catalog-portable) .catalog-header h1{
    grid-column:1!important;grid-row:1!important;justify-self:start;z-index:1;
    min-width:0;max-width:none;margin:0;overflow:visible;text-overflow:clip;white-space:nowrap
  }
  body:not(.catalog-portable) .hdr-cluster{
    grid-column:2!important;grid-row:1!important;justify-self:stretch!important;
    display:flex;flex-wrap:wrap;justify-content:flex-end;align-items:center;
    gap:.4rem;min-width:0;max-width:100%;position:relative;z-index:2
  }
  body:not(.catalog-portable) .catalog-header::after{content:none!important;display:none!important}
  body:not(.catalog-portable).hdr-tools-collapse #hdrToolsMore{display:inline-flex!important}
  body:not(.catalog-portable).hdr-tools-collapse:not(.hdr-tools-open) #layoutEditBtn,
  body:not(.catalog-portable).hdr-tools-collapse:not(.hdr-tools-open) #layoutPresets,
  body:not(.catalog-portable).hdr-tools-collapse:not(.hdr-tools-open) #hdrProfilesBtn,
  body:not(.catalog-portable).hdr-tools-collapse:not(.hdr-tools-open) #uiScale,
  body:not(.catalog-portable).hdr-tools-collapse:not(.hdr-tools-open) #hdrToolsRow2{
    display:none!important
  }
  body:not(.catalog-portable).hdr-tools-collapse:not(.hdr-tools-open) .catalog-header #clearMissBtn,
  body:not(.catalog-portable).display-sides.hdr-tools-collapse:not(.hdr-tools-open) .catalog-header #clearMissBtn,
  body:not(.catalog-portable).display-sides.display-middle.hdr-tools-collapse:not(.hdr-tools-open) .catalog-header #clearMissBtn{
    display:none!important
  }
  body:not(.catalog-portable).hdr-tools-open #hdrToolsRow2{display:flex!important}
  body:not(.catalog-portable).hdr-tools-open.hdr-tools-miss-pop .catalog-header #clearMissBtn,
  body:not(.catalog-portable).display-sides.hdr-tools-open.hdr-tools-miss-pop .catalog-header #clearMissBtn{
    display:inline-flex!important
  }
}
"""

JS_OLD = """window.toggleHdrBar=toggleHdrBar;
window.updateCatHeaderH=updateCatHeaderH;
(function restoreHdrBar(){"""

JS_NEW = r"""window.toggleHdrBar=toggleHdrBar;
window.updateCatHeaderH=updateCatHeaderH;
function hdrToolsPortraitOn(){
  if(window.CATALOG_PORTABLE)return false;
  var desk=typeof displayIsDesktop==='function'?displayIsDesktop():!!(window.matchMedia&&window.matchMedia('(min-width:900px)').matches);
  if(!desk)return false;
  try{return !!(window.matchMedia&&window.matchMedia('(orientation:portrait)').matches);}catch(eOr){return (window.innerHeight||0)>(window.innerWidth||0);}
}
function hdrToolsParked(el){return !!(el&&el.parentElement&&el.parentElement.id==='hdrToolsRow2');}
function hdrToolsHome(){
  var host=document.getElementById('hdrLayoutBtns');
  var cluster=document.getElementById('hdrCluster');
  var end=document.getElementById('hdrEnd')||document.getElementById('hdrMenuBtns');
  var miss=document.getElementById('clearMissBtn');
  var edit=document.getElementById('layoutEditBtn');
  var scale=document.getElementById('uiScale');
  var layouts=document.getElementById('layoutPresets');
  var profiles=document.getElementById('hdrProfilesBtn');
  if(host){
    if(edit&&edit.parentElement!==host)host.appendChild(edit);
    if(scale&&scale.parentElement!==host)host.appendChild(scale);
    if(layouts&&layouts.parentElement!==host)host.appendChild(layouts);
    if(profiles&&profiles.parentElement!==host)host.appendChild(profiles);
  }
  if(miss&&cluster){
    if(end){if(miss.parentElement!==cluster||miss.nextElementSibling!==end)cluster.insertBefore(miss,end);}
    else if(miss.parentElement!==cluster)cluster.appendChild(miss);
  }
}
function ensureHdrToolsChrome(){
  if(window.CATALOG_PORTABLE)return null;
  var cluster=document.getElementById('hdrCluster');
  if(!cluster)return null;
  var btn=document.getElementById('hdrToolsMore');
  if(!btn){
    btn=document.createElement('button');
    btn.type='button';btn.id='hdrToolsMore';btn.className='hdr-tools-more';
    btn.setAttribute('aria-expanded','false');
    btn.setAttribute('aria-label','More header actions');
    btn.title='More header actions';
    btn.innerHTML='<span class="toggle-arrow">&#9660;</span>';
    btn.addEventListener('click',function(e){e.preventDefault();e.stopPropagation();toggleHdrToolsMore();});
  }
  if(cluster.firstElementChild!==btn)cluster.insertBefore(btn,cluster.firstChild);
  var row=document.getElementById('hdrToolsRow2');
  if(!row){
    row=document.createElement('div');
    row.id='hdrToolsRow2';row.className='hdr-tools-row2';
    row.setAttribute('role','toolbar');row.setAttribute('aria-label','Header overflow actions');
  }
  if(row.parentElement!==cluster)cluster.appendChild(row);
  var pop=document.getElementById('hdrToolsMorePop');
  if(!pop){
    pop=document.createElement('div');
    pop.id='hdrToolsMorePop';pop.className='hdr-tools-more-pop';pop.hidden=true;
    pop.addEventListener('click',function(e){e.stopPropagation();});
  }
  if(pop.parentElement!==btn)btn.appendChild(pop);
  return {cluster:cluster,btn:btn,row:row,pop:pop};
}
function hdrToolsOverlap(title,cluster){
  if(!title||!cluster)return false;
  var tr=title.getBoundingClientRect();
  var cr=cluster.getBoundingClientRect();
  return cr.left<Math.round(tr.right)+6 && cr.top<Math.round(tr.bottom)-2 && tr.top<cr.bottom-2;
}
function placeHdrToolsRow2(open){
  var chrome=ensureHdrToolsChrome();
  if(!chrome)return;
  var row=chrome.row;
  var pop=chrome.pop;
  var miss=document.getElementById('clearMissBtn');
  var edit=document.getElementById('layoutEditBtn');
  var layouts=document.getElementById('layoutPresets');
  var profiles=document.getElementById('hdrProfilesBtn');
  var scale=document.getElementById('uiScale');
  document.body.classList.remove('hdr-tools-miss-pop');
  if(pop){pop.hidden=true;while(pop.firstChild)pop.removeChild(pop.firstChild);}
  if(!open){
    hdrToolsHome();
    return;
  }
  [miss,edit,layouts,profiles,scale].forEach(function(el){if(el)row.appendChild(el);});
  if(row.offsetWidth){}
  var title=document.querySelector('.catalog-header h1');
  var tr=title?title.getBoundingClientRect():null;
  var first=miss||edit;
  var fr=first?first.getBoundingClientRect():null;
  var crowded=!!(fr&&(fr.left<8||(tr&&fr.left<tr.right+6)));
  if(miss&&(crowded||hdrToolsOverlap(title,chrome.cluster))){
    document.body.classList.add('hdr-tools-miss-pop');
    if(pop){
      pop.appendChild(miss);
      pop.hidden=false;
    }
  }
}
function hdrToolsAfter(){
  if(typeof updateCatHeaderH==='function')updateCatHeaderH();
  if(typeof applyIndexScrollFit==='function')applyIndexScrollFit();
  if(typeof placeMenusForDisplay==='function'){
    var mode=(document.body.className.match(/display-(\S+)/)||[])[1];
    try{placeMenusForDisplay(mode||'sides');}catch(ePlace){}
  }
}
function syncHdrPortraitOverflow(){
  if(window._hdrToolsSyncing)return;
  window._hdrToolsSyncing=true;
  try{
    var on=hdrToolsPortraitOn();
    var chrome=window.CATALOG_PORTABLE?null:ensureHdrToolsChrome();
    var btn=chrome&&chrome.btn;
    if(!on){
      document.body.classList.remove('hdr-tools-collapse','hdr-tools-open','hdr-tools-miss-pop');
      if(btn){btn.hidden=true;btn.setAttribute('aria-expanded','false');btn.setAttribute('aria-hidden','true');}
      var popOff=document.getElementById('hdrToolsMorePop');
      if(popOff)popOff.hidden=true;
      hdrToolsHome();
      hdrToolsAfter();
      return;
    }
    document.body.classList.add('hdr-tools-collapse');
    var open=document.body.classList.contains('hdr-tools-open');
    if(btn){
      btn.hidden=false;
      btn.setAttribute('aria-hidden','false');
      btn.setAttribute('aria-expanded',open?'true':'false');
      btn.title=open?'Hide extra header actions':'More header actions';
      btn.setAttribute('aria-label',btn.title);
    }
    placeHdrToolsRow2(open);
    try{fetch('http://127.0.0.1:7529/ingest/1cf46354-1d61-4c80-bd72-a340f1db1b51',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'c00e3e'},body:JSON.stringify({sessionId:'c00e3e',runId:'hdr-tools',hypothesisId:'H-HDR',location:'catalog:syncHdrPortraitOverflow',message:'hdr-tools-overflow',data:{on:on,open:open,missPop:document.body.classList.contains('hdr-tools-miss-pop'),w:window.innerWidth,h:window.innerHeight,portable:!!window.CATALOG_PORTABLE},timestamp:Date.now()})}).catch(function(){});}catch(eLog){}
    hdrToolsAfter();
  }finally{window._hdrToolsSyncing=false;}
}
function toggleHdrToolsMore(force){
  var next=(force===true||force===false)?!!force:!document.body.classList.contains('hdr-tools-open');
  document.body.classList.toggle('hdr-tools-open',next);
  syncHdrPortraitOverflow();
}
window.hdrToolsPortraitOn=hdrToolsPortraitOn;
window.syncHdrPortraitOverflow=syncHdrPortraitOverflow;
window.toggleHdrToolsMore=toggleHdrToolsMore;
(function bindHdrToolsOverflow(){
  if(window._hdrToolsBound)return;
  window._hdrToolsBound=true;
  function go(){try{syncHdrPortraitOverflow();}catch(eGo){}}
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',go);
  else go();
  window.addEventListener('resize',go,{passive:true});
  window.addEventListener('orientationchange',function(){setTimeout(go,0);});
  try{
    var mq=window.matchMedia('(orientation: portrait)');
    if(mq.addEventListener)mq.addEventListener('change',go);
    else if(mq.addListener)mq.addListener(go);
  }catch(eMq){}
})();
(function restoreHdrBar(){
"""

STEAL_OLD = """  ['uiScale','layoutPresets'].forEach(function(id){
    var el=document.getElementById(id);
    if(el&&el.parentElement!==host)host.appendChild(el);
  });"""

STEAL_NEW = """  ['uiScale','layoutPresets'].forEach(function(id){
    var el=document.getElementById(id);
    if(el&&el.parentElement!==host&&!(el.parentElement&&el.parentElement.id==='hdrToolsRow2'))host.appendChild(el);
  });"""

EDIT_OLD = """  if(edit&&edit.parentElement!==host)host.appendChild(edit);
  if(tidy&&edit){
    if(tidy.parentElement!==edit.parentElement||tidy.nextElementSibling!==edit)edit.parentElement.insertBefore(tidy,edit);
  }else if(tidy&&tidy.parentElement!==host)host.insertBefore(tidy,host.firstChild);"""

EDIT_NEW = """  if(edit&&edit.parentElement!==host&&!(edit.parentElement&&edit.parentElement.id==='hdrToolsRow2'))host.appendChild(edit);
  if(tidy&&edit&&!(edit.parentElement&&edit.parentElement.id==='hdrToolsRow2')){
    if(tidy.parentElement!==edit.parentElement||tidy.nextElementSibling!==edit)edit.parentElement.insertBefore(tidy,edit);
  }else if(tidy&&tidy.parentElement!==host&&!(tidy.parentElement&&tidy.parentElement.id==='hdrToolsRow2'))host.insertBefore(tidy,host.firstChild);"""

MISS_OLD = """  var miss=document.getElementById('clearMissBtn');
  if(miss&&wrap){
    var before=end||document.getElementById('hdrMenuBtns');
    if(before){if(miss.parentElement!==wrap||miss.nextElementSibling!==before)wrap.insertBefore(miss,before);}
    else if(miss.parentElement!==wrap)wrap.appendChild(miss);
  }"""

MISS_NEW = """  var miss=document.getElementById('clearMissBtn');
  if(miss&&wrap&&!(miss.parentElement&&(miss.parentElement.id==='hdrToolsRow2'||miss.parentElement.id==='hdrToolsMorePop'))){
    var before=end||document.getElementById('hdrMenuBtns');
    if(before){if(miss.parentElement!==wrap||miss.nextElementSibling!==before)wrap.insertBefore(miss,before);}
    else if(miss.parentElement!==wrap)wrap.appendChild(miss);
  }"""

PROF_OLD = """  if(btn.parentElement!==host)host.appendChild(btn);
  var pop=document.getElementById('hdrProfilesPop');"""

PROF_NEW = """  if(btn.parentElement!==host&&!(btn.parentElement&&btn.parentElement.id==='hdrToolsRow2'))host.appendChild(btn);
  var pop=document.getElementById('hdrProfilesPop');"""

END_OLD = """        top.insertBefore(kb,fs);top.insertBefore(kp,fs);
      }
    }
  }
}
function bindFsModeHandles(){"""

END_NEW = """        top.insertBefore(kb,fs);top.insertBefore(kp,fs);
      }
    }
  }
  try{if(typeof window.syncHdrPortraitOverflow==='function')window.syncHdrPortraitOverflow();}catch(eHdrOv){}
}
function bindFsModeHandles(){"""

ROW_OLD = """  [miss,edit,layouts,profiles,scale].forEach(function(el){if(el)row.appendChild(el);});
  var title=document.querySelector('.catalog-header h1');
  if(miss&&hdrToolsOverlap(title,chrome.cluster)){"""

ROW_NEW = """  [miss,edit,layouts,profiles,scale].forEach(function(el){if(el)row.appendChild(el);});
  if(row.offsetWidth){}
  var title=document.querySelector('.catalog-header h1');
  var tr=title?title.getBoundingClientRect():null;
  var first=miss||edit;
  var fr=first?first.getBoundingClientRect():null;
  var crowded=!!(fr&&(fr.left<8||(tr&&fr.left<tr.right+6)));
  if(miss&&(crowded||hdrToolsOverlap(title,chrome.cluster))){"""


def replace_css(text: str, n: str) -> str:
    needle = "/* " + MARK
    start = text.find(needle)
    if start < 0:
        if CSS_MARK not in text:
            raise SystemExit(f"{n}: css mark missing")
        return text.replace(CSS_MARK, CSS_ADD + CSS_MARK, 1)
    end = text.find(CSS_MARK, start)
    if end < 0:
        raise SystemExit(f"{n}: css end missing")
    return text[:start] + CSS_ADD.lstrip("\n") + text[end:]


def sub(text, old, new, label):
    n = text.count(old)
    if n == 1:
        return text.replace(old, new, 1)
    if n > 1:
        raise SystemExit(f"{label}: {n} matches")
    if new in text:
        print(f"  skip {label} (already)")
        return text
    raise SystemExit(f"{label}: not found")


def write(path: Path, text: str, before_c00: int, before_clash: int) -> None:
    raw = text.encode("utf-8")
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_bytes(raw)
    out = tmp.read_bytes().decode("utf-8")
    if not out.strip().endswith("</html>"):
        tmp.unlink()
        raise SystemExit(f"{path.name}: truncated")
    for keep in KEEP:
        if keep not in out:
            tmp.unlink()
            raise SystemExit(f"{path.name}: lost {keep}")
    if out.count("sessionId:'c00e3e'") < before_c00:
        tmp.unlink()
        raise SystemExit(f"{path.name}: lost c00e3e logs")
    if out.count("index-embed-alignment-clash") < before_clash:
        tmp.unlink()
        raise SystemExit(f"{path.name}: lost index-embed-alignment-clash")
    tmp.replace(path)
    print("OK", path.name, len(raw))


def patch(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    n = path.name
    before_c00 = text.count("sessionId:'c00e3e'")
    before_clash = text.count("index-embed-alignment-clash")
    text = replace_css(text, n)
    if "function syncHdrPortraitOverflow(" not in text:
        text = sub(text, JS_OLD, JS_NEW, f"{n}: overflow js")
    else:
        text = sub(text, ROW_OLD, ROW_NEW, f"{n}: row2 crowded")
    text = sub(text, STEAL_OLD, STEAL_NEW, f"{n}: steal scale/layouts")
    text = sub(text, EDIT_OLD, EDIT_NEW, f"{n}: steal customize")
    text = sub(text, MISS_OLD, MISS_NEW, f"{n}: steal miss")
    text = sub(text, PROF_OLD, PROF_NEW, f"{n}: steal profiles")
    text = sub(text, END_OLD, END_NEW, f"{n}: ensure end sync")
    if "function syncHdrPortraitOverflow(" not in text:
        raise SystemExit(f"{n}: missing syncHdrPortraitOverflow")
    if 'id="hdrToolsMore"' not in CSS_ADD and "hdrToolsMore" not in text:
        raise SystemExit(f"{n}: missing hdrToolsMore")
    write(path, text, before_c00, before_clash)


def main() -> None:
    for p in FILES:
        if not p.exists():
            raise SystemExit(f"missing {p}")
        patch(p)


if __name__ == "__main__":
    main()
