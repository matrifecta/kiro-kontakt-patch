#!/usr/bin/env python3
"""Add minimized-card dock (max 3 FIFO pills) to DS/Kontakt catalogs + builders."""
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

CSS = r""" .hl-min{display:none;position:absolute;top:max(var(--card-chrome-inset),env(safe-area-inset-top));right:calc(var(--card-chrome-inset) + var(--card-chrome-btn) + var(--card-chrome-gap));z-index:5;width:var(--card-chrome-btn);height:var(--card-chrome-btn);min-width:var(--card-chrome-btn);min-height:var(--card-chrome-btn);font-size:1.375rem;align-items:center;justify-content:center;background:var(--bg-surface);color:var(--text);border:1px solid var(--border);border-radius:8px;cursor:pointer;touch-action:manipulation;line-height:1;padding:0}
 .entry.highlight .hl-min,body.chosen-preview-open .entry.selected:not(.highlight) .hl-min{display:flex;z-index:841}
 .entry.highlight .hl-min:hover,body.chosen-preview-open .entry.selected:not(.highlight) .hl-min:hover{color:var(--accent-instrument);border-color:var(--accent-instrument);background:var(--accent-instrument-bg)}
 #cardMinDock{display:none;position:fixed;z-index:10040;left:0;width:100%;bottom:0;justify-content:center;align-items:flex-end;flex-wrap:nowrap;gap:.55rem;padding:0 .75rem max(.85rem,env(safe-area-inset-bottom));box-sizing:border-box;pointer-events:none}
 #cardMinDock.is-on{display:flex}
 #cardMinDock .card-min-pill{pointer-events:auto;display:inline-flex;align-items:center;gap:.45rem;max-width:min(14.5rem,34%);min-height:2.85rem;padding:.35rem .95rem .35rem .35rem;border:1px solid var(--accent-instrument);border-radius:999px;background:var(--bg-card);color:var(--accent-instrument);font:inherit;font-size:1rem;font-weight:650;letter-spacing:.01em;line-height:1.15;cursor:pointer;touch-action:manipulation;box-shadow:0 8px 28px rgba(0,0,0,.38);transform-origin:center bottom;transition:transform .14s ease,opacity .14s ease,box-shadow .14s ease,border-color .14s ease;opacity:.92}
 #cardMinDock .card-min-pill img{width:2.15rem;height:2.15rem;border-radius:999px;object-fit:cover;flex:0 0 auto;border:1px solid var(--border);background:var(--bg-surface)}
 #cardMinDock .card-min-name{min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
 #cardMinDock .card-min-pill:hover{transform:scale(1.08);opacity:1;z-index:1}
 #cardMinDock .card-min-pill.is-front{background:var(--accent-instrument-bg);border-color:var(--accent-instrument-active);color:var(--accent-instrument-active);box-shadow:0 10px 32px rgba(0,0,0,.45);opacity:1}
 body.gallery-open #cardMinDock,body.img-focus-open #cardMinDock,body.desc-reader-open #cardMinDock,body.path-reader-open #cardMinDock,body.desc-focus-open #cardMinDock,body.path-focus-open #cardMinDock{visibility:hidden!important;pointer-events:none!important}
"""

JS = r"""
var CARD_MIN_MAX=3;
var cardMinDockItems=[];
function cardMinExpanded(){
  var hl=document.querySelector('.entry.highlight');
  if(hl)return hl;
  if(document.body.classList.contains('chosen-preview-open'))return document.querySelector('.entry.selected');
  return null;
}
function cardMinMode(el){
  if(el&&el.classList.contains('highlight'))return 'highlight';
  if(document.body.classList.contains('hl-open'))return 'highlight';
  return 'preview';
}
function cardMinShortName(el){
  var n=(el&&(el.getAttribute('data-name')||((el.querySelector('.lib-name')||{}).textContent||'')))||'Library';
  n=String(n).replace(/\s+/g,' ').trim();
  if(n.length>28)n=n.slice(0,26)+'\u2026';
  return n;
}
function cardMinCoverSrc(el){
  var img=el&&el.querySelector('.cover img');
  return img?(img.getAttribute('src')||''):'';
}
function cardMinIndex(id){
  for(var i=0;i<cardMinDockItems.length;i++)if(cardMinDockItems[i].id===id)return i;
  return -1;
}
function cardMinDismissOpen(){
  var el=cardMinExpanded();
  if(!el||!el.id)return;
  var i=cardMinIndex(el.id);
  if(i<0)return;
  cardMinDockItems.splice(i,1);
  cardMinRender();
}
function cardMinEnsureBtn(entry){
  if(!entry)return;
  var end=entry.querySelector('.card-chrome-end');
  if(!end||end.querySelector('.hl-min'))return;
  var b=document.createElement('button');
  b.type='button';
  b.className='hl-min';
  b.setAttribute('aria-label','Minimize');
  b.setAttribute('title','Minimize');
  b.innerHTML='&#x2212;';
  var close=end.querySelector('.hl-close');
  if(close)end.insertBefore(b,close);else end.appendChild(b);
}
function cardMinEnsureAllBtns(){document.querySelectorAll('.entry').forEach(cardMinEnsureBtn);}
function cardMinEnsureDock(){
  var d=document.getElementById('cardMinDock');
  if(d)return d;
  d=document.createElement('div');
  d.id='cardMinDock';
  d.setAttribute('role','toolbar');
  d.setAttribute('aria-label','Minimized library cards');
  document.body.appendChild(d);
  return d;
}
function cardMinPlace(){
  var d=document.getElementById('cardMinDock');
  if(!d)return;
  var main=document.getElementById('catalogMain');
  var r=main?main.getBoundingClientRect():null;
  if(!r||r.width<40){d.style.left='0';d.style.width='100%';d.style.bottom='0';return;}
  d.style.left=Math.round(r.left)+'px';
  d.style.width=Math.round(r.width)+'px';
  d.style.bottom=Math.max(0,Math.round((window.innerHeight||0)-r.bottom))+'px';
}
function cardMinRender(){
  var d=cardMinEnsureDock();
  var cur=cardMinExpanded();
  var curId=cur&&cur.id;
  d.classList.toggle('is-on',cardMinDockItems.length>0);
  d.innerHTML='';
  cardMinDockItems.forEach(function(item,idx){
    var el=document.getElementById(item.id);
    var pill=document.createElement('button');
    pill.type='button';
    pill.className='card-min-pill'+(item.id===curId?' is-front':'');
    pill.setAttribute('data-card-min-id',item.id);
    pill.setAttribute('data-card-min-slot',idx===0?'left':(idx===cardMinDockItems.length-1&&cardMinDockItems.length>1?'right':'middle'));
    if(cardMinDockItems.length===3)pill.setAttribute('data-card-min-slot',idx===0?'left':(idx===1?'middle':'right'));
    pill.setAttribute('aria-pressed',item.id===curId?'true':'false');
    var src=el?cardMinCoverSrc(el):'';
    if(src){
      var im=document.createElement('img');
      im.alt='';
      im.src=src;
      pill.appendChild(im);
    }
    var sp=document.createElement('span');
    sp.className='card-min-name';
    sp.textContent=el?cardMinShortName(el):(item.name||'Library');
    pill.appendChild(sp);
    d.appendChild(pill);
  });
  cardMinPlace();
}
function minimizeExpandedCard(entry){
  entry=entry||cardMinExpanded();
  if(!entry||!entry.id)return;
  var mode=cardMinMode(entry);
  var i=cardMinIndex(entry.id);
  var rec={id:entry.id,mode:mode,name:cardMinShortName(entry)};
  if(i>=0)cardMinDockItems[i].mode=mode;
  else{
    cardMinDockItems.push(rec);
    while(cardMinDockItems.length>CARD_MIN_MAX)cardMinDockItems.shift();
  }
  if(document.body.classList.contains('hl-open')||entry.classList.contains('highlight'))closeOverlay({skipScroll:true});
  else if(document.body.classList.contains('chosen-preview-open'))closeChosenPreview({skipJumpExit:true});
  cardMinRender();
}
function cardMinRestore(id){
  var i=cardMinIndex(id);
  if(i<0)return;
  var item=cardMinDockItems[i];
  var el=document.getElementById(item.id);
  if(!el){cardMinDockItems.splice(i,1);cardMinRender();return;}
  var cur=cardMinExpanded();
  if(cur&&cur!==el){
    var ci=cardMinIndex(cur.id);
    if(ci>=0)cardMinDockItems[ci].mode=cardMinMode(cur);
    if(document.body.classList.contains('hl-open')||cur.classList.contains('highlight'))closeOverlay({skipScroll:true});
    else if(document.body.classList.contains('chosen-preview-open'))closeChosenPreview({skipJumpExit:true});
  }
  if(item.mode==='highlight')openOverlay(el);
  else openChosenPreview(el);
  cardMinRender();
}
function cardMinActivate(id){
  var cur=cardMinExpanded();
  if(cur&&cur.id===id){minimizeExpandedCard(cur);return;}
  cardMinRestore(id);
}
function cardMinTabNext(){
  var n=cardMinDockItems.length;
  if(!n)return;
  var cur=cardMinExpanded();
  var idx=cur?cardMinIndex(cur.id):-1;
  var next=(idx<0)?0:((idx+1)%n);
  cardMinRestore(cardMinDockItems[next].id);
}
function cardMinField(t){
  if(!t)return false;
  if(t.isContentEditable)return true;
  var tag=(t.tagName||'').toLowerCase();
  if(tag==='textarea'||tag==='select')return true;
  if(tag==='input'){
    var ty=(t.type||'').toLowerCase();
    if(ty==='button'||ty==='submit'||ty==='checkbox'||ty==='radio'||ty==='range'||ty==='file'||ty==='hidden')return false;
    return true;
  }
  return !!(t.closest&&t.closest('textarea,select,[contenteditable="true"]'));
}
function cardMinShouldTakeTab(t){
  if(!cardMinDockItems.length)return false;
  if(cardMinField(t))return false;
  if(t&&t.closest&&t.closest('#searchInput,#acList,#acShell,.search-ac-shell,#searchChrome,.search-chrome,#filterWrap,#kwbar,.filter-wrap,.note-pop,.note-ta,textarea,select,[contenteditable="true"]'))return false;
  if(t&&t.closest&&t.closest('input')&&cardMinField(t.closest('input')))return false;
  if(cardMinExpanded())return true;
  if(t&&t.closest&&t.closest('#catalogMain,#cardMinDock,.catalog-body'))return true;
  if(!t||t===document.body||t===document.documentElement)return true;
  return false;
}
function cardMinOnOverlayOpen(el){
  if(el)cardMinEnsureBtn(el);
  cardMinRender();
}
window.minimizeExpandedCard=minimizeExpandedCard;
window.cardMinDismissOpen=cardMinDismissOpen;
window.cardMinOnOverlayOpen=cardMinOnOverlayOpen;
window.cardMinActivate=cardMinActivate;
window.cardMinTabNext=cardMinTabNext;
(function initCardMinDock(){
  if(window._cardMinDockInit)return;
  window._cardMinDockInit=true;
  function boot(){
    cardMinEnsureAllBtns();
    cardMinEnsureDock();
    cardMinRender();
    var main=document.getElementById('catalogMain');
    if(main){
      main.addEventListener('scroll',cardMinPlace,{passive:true});
      if(window.ResizeObserver)try{new ResizeObserver(cardMinPlace).observe(main);}catch(err){}
    }
    window.addEventListener('resize',cardMinPlace);
    if(window.visualViewport){
      window.visualViewport.addEventListener('resize',cardMinPlace);
      window.visualViewport.addEventListener('scroll',cardMinPlace);
    }
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot);
  else boot();
  document.addEventListener('keydown',function(e){
    if(e.key!=='Tab'||e.shiftKey||e.altKey||e.ctrlKey||e.metaKey)return;
    if(!cardMinShouldTakeTab(e.target))return;
    e.preventDefault();
    cardMinTabNext();
  },true);
  document.addEventListener('click',function(e){
    if(e.target.closest&&e.target.closest('.preview-back'))cardMinDismissOpen();
  },true);
  var _ch=clearHighlight;
  clearHighlight=function(){cardMinDismissOpen();return _ch.apply(this,arguments);};
  window.clearHighlight=clearHighlight;
  if(typeof openChosenPreview==='function'){
    var _ocp=openChosenPreview;
    openChosenPreview=function(el){var r=_ocp.apply(this,arguments);cardMinOnOverlayOpen(el);return r;};
    window.openChosenPreview=openChosenPreview;
  }
  if(typeof openOverlay==='function'){
    var _oo=openOverlay;
    openOverlay=function(el){var r=_oo.apply(this,arguments);cardMinOnOverlayOpen(el);return r;};
    window.openOverlay=openOverlay;
  }
})();
"""

REPLACEMENTS = [
    (
        ".card-chrome-start>.preview-back,.card-chrome-start>.fav-btn,.card-chrome-end>.fs-btn,.card-chrome-end>.hl-close{flex:0 0 auto}",
        ".card-chrome-start>.preview-back,.card-chrome-start>.fav-btn,.card-chrome-end>.fs-btn,.card-chrome-end>.hl-min,.card-chrome-end>.hl-close{flex:0 0 auto}",
    ),
    (
        " .entry.highlight .hl-close:hover{color:var(--accent-instrument);border-color:var(--accent-instrument)}\n",
        " .entry.highlight .hl-close:hover{color:var(--accent-instrument);border-color:var(--accent-instrument)}\n"
        + CSS,
    ),
    (
        "function clearHighlight(){closeOverlay();}\n",
        "function clearHighlight(){closeOverlay();}\n" + JS,
    ),
    (
        "  if(e.target.closest('.preview-back')){closeChosenPreview();e.preventDefault();e.stopPropagation();return;}\n"
        "  if(e.target.closest('.hl-close')){closeOverlay();e.preventDefault();return;}\n",
        "  if(e.target.closest('#cardMinDock')){\n"
        "    var pill=e.target.closest('.card-min-pill');\n"
        "    if(pill){cardMinActivate(pill.getAttribute('data-card-min-id'));e.preventDefault();e.stopPropagation();return;}\n"
        "    e.stopPropagation();return;\n"
        "  }\n"
        "  if(e.target.closest('.hl-min')){var minE=e.target.closest('.entry');if(minE)minimizeExpandedCard(minE);e.preventDefault();e.stopPropagation();return;}\n"
        "  if(e.target.closest('.preview-back')){closeChosenPreview();e.preventDefault();e.stopPropagation();return;}\n"
        "  if(e.target.closest('.hl-close')){closeOverlay();e.preventDefault();return;}\n",
    ),
    (
        "    if(e.target.closest('#searchModal,.search-modal,.search-modal-link')) return;\n"
        "    if(!e.target.closest('.entry.selected')){\n"
        "      if(document.body.classList.contains('card-embed-open')){closeCardSearchEmbed();e.preventDefault();return;}\n"
        "      closeChosenPreview();\n",
        "    if(e.target.closest('#searchModal,.search-modal,.search-modal-link,#cardMinDock')) return;\n"
        "    if(!e.target.closest('.entry.selected,#cardMinDock')){\n"
        "      if(document.body.classList.contains('card-embed-open')){closeCardSearchEmbed();e.preventDefault();return;}\n"
        "      cardMinDismissOpen();\n"
        "      closeChosenPreview();\n",
    ),
    (
        "  if(e.target.closest('#searchModal,.card-search-embed,.search-chrome,.search-split,.search-height,.ac-height,.ac-width,.kw-shade-height,.search-ac-shell,.filter-wrap,.search-strip,.search-autocomplete,.search-active-pills,.top,.tap-add-btn,.clear-miss-btn,.layout-edit-btn,#kwbar,.kw,.mode-switch,.cat-switch,.fav-btn,.note-pop,.note-balloon,.preview-back')) return;\n",
        "  if(e.target.closest('#searchModal,#cardMinDock,.card-min-pill,.card-search-embed,.search-chrome,.search-split,.search-height,.ac-height,.ac-width,.kw-shade-height,.search-ac-shell,.filter-wrap,.search-strip,.search-autocomplete,.search-active-pills,.top,.tap-add-btn,.clear-miss-btn,.layout-edit-btn,#kwbar,.kw,.mode-switch,.cat-switch,.fav-btn,.note-pop,.note-balloon,.preview-back,.hl-min')) return;\n",
    ),
    (
        "    if(e.target.closest('a,.hl-close,.preview-back,.kw,input,select,textarea,summary,.patches,.search-popup-btn,.search-link,.fav-btn,.note-balloon,.note-pop,.un-badge,.note-save,.note-cancel,.fs-btn,.card-search-embed')) return;\n",
        "    if(e.target.closest('a,.hl-close,.hl-min,.preview-back,.kw,input,select,textarea,summary,.patches,.search-popup-btn,.search-link,.fav-btn,.note-balloon,.note-pop,.un-badge,.note-save,.note-cancel,.fs-btn,.card-search-embed,#cardMinDock')) return;\n",
    ),
    (
        "    if(t.closest('.fs-btn,.hl-close,.preview-back,.fav-btn'))return null;\n",
        "    if(t.closest('.fs-btn,.hl-close,.hl-min,.preview-back,.fav-btn,#cardMinDock'))return null;\n",
    ),
    (
        "  if(document.querySelector('.entry.highlight')){\n"
        "    closeOverlay();\n"
        "    e.preventDefault();\n"
        "    return;\n"
        "  }\n",
        "  if(document.querySelector('.entry.highlight')){\n"
        "    cardMinDismissOpen();\n"
        "    closeOverlay();\n"
        "    e.preventDefault();\n"
        "    return;\n"
        "  }\n",
    ),
    (
        "  if(document.body.classList.contains('chosen-preview-open')){\n"
        "    closeChosenPreview();\n"
        "    e.preventDefault();\n"
        "    return;\n"
        "  }\n",
        "  if(document.body.classList.contains('chosen-preview-open')){\n"
        "    cardMinDismissOpen();\n"
        "    closeChosenPreview();\n"
        "    e.preventDefault();\n"
        "    return;\n"
        "  }\n",
    ),
]

PRINTF_OLD = "    printf '  <button type=\"button\" class=\"hl-close\" aria-label=\"Close\" onclick=\"clearHighlight();event.stopPropagation()\">&#x2715;</button>\\n'\n"
PRINTF_NEW = (
    '    printf "  <button type=\\"button\\" class=\\"hl-min\\" aria-label=\\"Minimize\\" title=\\"Minimize\\" onclick=\\"event.preventDefault();event.stopPropagation();minimizeExpandedCard(this.closest(\'.entry\'))\\">&#x2212;</button>\\n"\n'
    + PRINTF_OLD
)


def apply_one(path: Path, write: bool) -> None:
    text = path.read_text(encoding="utf-8")
    if "#cardMinDock{" in text or "function cardMinExpanded(" in text:
        raise SystemExit(f"already patched: {path}")
    orig = text
    for i, (old, new) in enumerate(REPLACEMENTS):
        count = text.count(old)
        if count != 1:
            raise SystemExit(f"{path}: marker {i} expected 1, got {count}:\n{old[:220]!r}")
        text = text.replace(old, new, 1)
    if path.suffix == ".sh":
        count = text.count(PRINTF_OLD)
        if count != 1:
            raise SystemExit(f"{path}: printf hl-close count={count}\nlooking for {PRINTF_OLD!r}")
        text = text.replace(PRINTF_OLD, PRINTF_NEW, 1)
    if text == orig:
        raise SystemExit(f"no changes: {path}")
    if write:
        path.write_text(text, encoding="utf-8")
        print(f"patched {path} ({len(text) - len(orig):+d} bytes)")
    else:
        print(f"ok {path} ({len(text) - len(orig):+d} bytes)")


def main() -> None:
    for p in FILES:
        if not p.exists():
            raise SystemExit(f"missing {p}")
        apply_one(p, write=False)
    for p in FILES:
        apply_one(p, write=True)
    print("ok")


if __name__ == "__main__":
    main()
