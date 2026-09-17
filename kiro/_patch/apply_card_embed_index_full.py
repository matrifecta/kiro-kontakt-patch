#!/usr/bin/env python3
"""Unmix card/embed windows, pin card chrome to the top row, expand Embed Index to full height."""
from pathlib import Path

ROOT = Path("/home/phnx/kiro-kontakt-patch")
FILES = [
    ROOT / "public/catalogs/KONTAKT-CATALOG.html",
    ROOT / "public/catalogs/DS-CATALOG.html",
    ROOT / "public/catalogs/KONTAKT-CATALOG-portable.html",
    ROOT / "public/catalogs/DS-CATALOG-portable.html",
]
MARK = "fix-INDEX-EMBED-FULL-v1"
KEEP = (
    "c00e3e",
    "fix-PORTABLE-FS-FLIP-INDEX-v1",
    "fix-CARD-FS-EMBED-SCROLL-v1",
    "fix-INDEX-OPAQUE-SCROLL-v2",
    "fix-CARD-EMBED-SEPARATE-v1",
    "fix-CARD-CHROME-TOP-v1",
    MARK,
)

INGEST = (
    "fetch('http://127.0.0.1:7529/ingest/1cf46354-1d61-4c80-bd72-a340f1db1b51',"
    "{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'c00e3e'},"
    "body:JSON.stringify("
)
TAIL = ")}).catch(function(){});"


def add_indent(s, n=1):
    pad = " " * n
    return "\n".join((pad + line) if line.strip() else line for line in s.split("\n"))


def sub(text, old, new, label, optional=False, replace_all=False):
    n = text.count(old)
    if n == 1 or (replace_all and n > 0):
        return text.replace(old, new)
    if n > 1:
        raise SystemExit(f"{label}: {n} matches")
    if new in text:
        print(f"  skip {label} (already)")
        return text
    for i in range(1, 9):
        oldi, newi = add_indent(old, i), add_indent(new, i)
        ni = text.count(oldi)
        if ni == 1 or (replace_all and ni > 0):
            return text.replace(oldi, newi)
        if ni > 1:
            raise SystemExit(f"{label}: {ni} matches (indent {i})")
        if ni == 0 and newi in text:
            print(f"  skip {label} (already)")
            return text
    if optional:
        print(f"  skip {label}")
        return text
    raise SystemExit(f"{label}: not found")


CSS_ADD = r"""
/* fix-CARD-EMBED-SEPARATE-v1: embed is its own window; card fields stay parked/hidden */
@media all{
  body.card-embed-open .entry.highlight,
  body.card-embed-open.chosen-preview-open .entry.selected:not(.highlight),
  body.catalog-portable.card-embed-open.chosen-preview-open .entry.selected:not(.highlight){
    overflow:hidden!important;overflow-x:hidden!important;overflow-y:hidden!important;
    display:flex!important;flex-direction:column!important;align-items:stretch!important
  }
  body.card-embed-open .entry.highlight .cover,
  body.card-embed-open .entry.highlight .lib-name,
  body.card-embed-open .entry.highlight .lib-notes,
  body.card-embed-open .entry.highlight .note-text,
  body.card-embed-open .entry.highlight .noart,
  body.card-embed-open .entry.highlight .summary-panel,
  body.card-embed-open .entry.highlight .path,
  body.card-embed-open .entry.highlight details.patches,
  body.card-embed-open .entry.highlight .patches,
  body.card-embed-open .entry.highlight .card-actions,
  body.card-embed-open .entry.highlight .hl-body,
  body.card-embed-open.chosen-preview-open .entry.selected:not(.highlight) .cover,
  body.card-embed-open.chosen-preview-open .entry.selected:not(.highlight) .lib-name,
  body.card-embed-open.chosen-preview-open .entry.selected:not(.highlight) .lib-notes,
  body.card-embed-open.chosen-preview-open .entry.selected:not(.highlight) .note-text,
  body.card-embed-open.chosen-preview-open .entry.selected:not(.highlight) .noart,
  body.card-embed-open.chosen-preview-open .entry.selected:not(.highlight) .summary-panel,
  body.card-embed-open.chosen-preview-open .entry.selected:not(.highlight) .path,
  body.card-embed-open.chosen-preview-open .entry.selected:not(.highlight) details.patches,
  body.card-embed-open.chosen-preview-open .entry.selected:not(.highlight) .patches,
  body.card-embed-open.chosen-preview-open .entry.selected:not(.highlight) .card-actions,
  body.card-embed-open.chosen-preview-open .entry.selected:not(.highlight) .hl-body{
    display:none!important
  }
  body.hl-open:not(.card-embed-open) .entry.highlight,
  body.chosen-preview-open:not(.card-embed-open) .entry.selected:not(.highlight){
    overflow-x:hidden!important;overflow-y:auto!important
  }
  body.card-embed-open .entry.highlight #cardSearchEmbed,
  body.card-embed-open .entry.highlight .card-search-embed,
  body.card-embed-open.chosen-preview-open .entry.selected:not(.highlight) #cardSearchEmbed,
  body.card-embed-open.chosen-preview-open .entry.selected:not(.highlight) .card-search-embed{
    display:flex!important;flex:1 1 auto!important;flex-shrink:1!important;
    min-height:0!important;max-height:none!important;
    overflow-x:hidden!important;overflow-y:auto!important;
    position:relative!important;inset:auto!important;order:8;margin-top:8px
  }
  body.card-embed-open #cardSearchEmbed .card-search-chrome{
    position:sticky!important;top:0!important;z-index:6!important;flex:0 0 auto!important
  }
}

/* fix-CARD-CHROME-TOP-v1: one top-border row; reserved padding; no header overlay */
@media all{
  .entry.highlight,
  body.hl-open .entry.highlight,
  body.catalog-portable .entry.highlight{
    padding-top:calc(var(--card-chrome-inset) * 2 + var(--card-chrome-btn) + env(safe-area-inset-top,0px))!important
  }
  body.chosen-preview-open .entry.selected:not(.highlight),
  body.catalog-portable.chosen-preview-open .entry.selected:not(.highlight){
    padding-top:calc(var(--card-chrome-inset) * 2 + var(--card-chrome-btn))!important
  }
  .entry.highlight .card-chrome-start,
  .entry.highlight .card-chrome-end,
  body.hl-open .entry.highlight .card-chrome-start,
  body.hl-open .entry.highlight .card-chrome-end,
  body.chosen-preview-open .entry.selected:not(.highlight) .card-chrome-start,
  body.chosen-preview-open .entry.selected:not(.highlight) .card-chrome-end,
  body.catalog-portable.chosen-preview-open .entry.selected:not(.highlight) .card-chrome-start,
  body.catalog-portable.chosen-preview-open .entry.selected:not(.highlight) .card-chrome-end,
  body.card-embed-open.chosen-preview-open .entry.selected:not(.highlight) .card-chrome-start,
  body.card-embed-open.chosen-preview-open .entry.selected:not(.highlight) .card-chrome-end{
    position:absolute!important;top:var(--card-chrome-inset)!important;bottom:auto!important;
    margin:0!important;margin-top:0!important;margin-left:0!important;transform:none!important;
    display:flex!important;flex-direction:row!important;align-items:center!important;
    gap:var(--card-chrome-gap)!important;height:var(--card-chrome-btn)!important;
    width:auto!important;max-width:none!important;z-index:841!important;
    pointer-events:none!important;background:transparent!important;
    align-self:auto!important
  }
  .entry.highlight .card-chrome-start,
  body.chosen-preview-open .entry.selected:not(.highlight) .card-chrome-start{
    left:var(--card-chrome-inset)!important;right:auto!important
  }
  .entry.highlight .card-chrome-end,
  body.chosen-preview-open .entry.selected:not(.highlight) .card-chrome-end{
    right:var(--card-chrome-inset)!important;left:auto!important
  }
  .entry.highlight .card-chrome-start>*,
  .entry.highlight .card-chrome-end>*,
  body.chosen-preview-open .entry.selected:not(.highlight) .card-chrome-start>*,
  body.chosen-preview-open .entry.selected:not(.highlight) .card-chrome-end>*{
    position:static!important;top:auto!important;left:auto!important;right:auto!important;bottom:auto!important;
    margin:0!important;pointer-events:auto!important
  }
  .entry.highlight .fav-btn,
  body.chosen-preview-open .entry.selected:not(.highlight) .fav-btn,
  body.chosen-preview-open .entry.selected:not(.highlight) .preview-back,
  body.chosen-preview-open .entry.selected:not(.highlight) .fs-btn,
  body.chosen-preview-open .entry.selected:not(.highlight) .hl-min,
  .entry.highlight .hl-min,
  .entry.highlight .hl-close{
    position:static!important;top:auto!important;left:auto!important;right:auto!important;bottom:auto!important
  }
  body.catalog-portable.card-embed-open.chosen-preview-open .entry.selected:not(.highlight) .preview-back,
  body.catalog-portable.card-embed-open.chosen-preview-open .entry.selected:not(.highlight) .fs-btn,
  body.catalog-portable.card-embed-open.chosen-preview-open .entry.selected:not(.highlight) .hl-min,
  body.catalog-portable.card-embed-open.chosen-preview-open .entry.selected:not(.highlight) .fav-btn{
    position:static!important;top:auto!important;left:auto!important;right:auto!important;bottom:auto!important
  }
}

/* fix-INDEX-EMBED-FULL-v1: Embed expanded is full list height; catalog-body scrolls; Window keeps inner scroll */
html body #catalogIndex.is-embedded:not(.is-collapsed),
html body.display-sides #catalogMain>.catalog-body>#catalogIndex.is-embedded:not(.is-collapsed),
html body.display-middle #catalogMain>.catalog-body>#catalogIndex.is-embedded:not(.is-collapsed),
html body.catalog-portable #catalogMain>.catalog-body>#catalogIndex.is-embedded:not(.is-collapsed),
html body.catalog-portable.display-sides #catalogMain>.catalog-body>#catalogIndex.is-embedded:not(.is-collapsed),
html body.catalog-portable #catalogMain #catalogIndex.is-embedded:not(.is-collapsed),
html body.catalog-portable #catalogIndex.is-embedded:not(.is-collapsed),
html body #catalogMain>.catalog-body>#catalogIndex.is-embedded:not(.is-collapsed){
  height:auto!important;max-height:none!important;min-height:0!important;
  overflow:visible!important;overflow-x:hidden!important;overflow-y:visible!important;
  isolation:isolate!important;background:var(--bg-surface)!important;
  flex:0 0 auto!important;position:relative!important;z-index:45!important;
  display:flex!important;flex-direction:column!important
}
html body #catalogIndex.is-embedded:not(.is-collapsed) .index,
html body #catalogIndex.is-embedded:not(.is-collapsed) #catalogIndexList,
html body.display-sides #catalogIndex.is-embedded:not(.is-collapsed) .index,
html body.display-sides #catalogIndex.is-embedded:not(.is-collapsed) #catalogIndexList,
html body.display-middle #catalogIndex.is-embedded:not(.is-collapsed) .index,
html body.display-middle #catalogIndex.is-embedded:not(.is-collapsed) #catalogIndexList,
html body.catalog-portable #catalogIndex.is-embedded:not(.is-collapsed) .index,
html body.catalog-portable #catalogIndex.is-embedded:not(.is-collapsed) #catalogIndexList,
html body.catalog-portable #catalogMain #catalogIndex.is-embedded:not(.is-collapsed) .index,
html body.catalog-portable #catalogMain #catalogIndex.is-embedded:not(.is-collapsed) #catalogIndexList{
  height:auto!important;max-height:none!important;min-height:0!important;flex:0 0 auto!important;
  overflow:visible!important;overflow-x:hidden!important;overflow-y:visible!important;
  background:var(--bg-surface)!important;isolation:isolate!important
}
html body #catalogIndex.is-embedded:not(.is-collapsed) .index li,
html body #catalogIndex.is-embedded:not(.is-collapsed) #catalogIndexList li{
  background:var(--bg-surface)!important
}
body:has(#catalogIndex.is-embedded:not(.is-collapsed)) #catalogJumpStack{
  display:none!important
}
"""

SCROLL_EL_OLD = """function cardFsEmbedScrollEl(){
  return document.querySelector('.entry.highlight')
    || (document.body.classList.contains('chosen-preview-open')?document.querySelector('.entry.selected'):null);
}"""

SCROLL_EL_NEW = """function cardFsEmbedScrollEl(){
  if(document.body.classList.contains('card-embed-open')){
    var embed=document.getElementById('cardSearchEmbed');
    if(embed&&!embed.hidden)return embed;
  }
  return document.querySelector('.entry.highlight')
    || (document.body.classList.contains('chosen-preview-open')?document.querySelector('.entry.selected'):null);
}"""

LOG_OLD = """function logCardFsEmbedScroll(why){
  try{
    var card=cardFsEmbedScrollEl();
    var body=card&&card.querySelector('.hl-body');
    var embed=document.getElementById('cardSearchEmbed');
    var main=document.getElementById('catalogMain');
    function scr(n){
      if(!n)return null;
      var cs=getComputedStyle(n);
      return {id:n.id||'',cls:(n.className||'').toString().slice(0,48),ovY:cs.overflowY,sh:n.scrollHeight,ch:n.clientHeight,st:Math.round(n.scrollTop),can:n.scrollHeight>n.clientHeight+2};
    }
    fetch('http://127.0.0.1:7529/ingest/1cf46354-1d61-4c80-bd72-a340f1db1b51',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'c00e3e'},body:JSON.stringify({sessionId:'c00e3e',runId:'post-fix',hypothesisId:'P',location:'catalog:cardFsEmbedScroll',message:why||'scroll-snap',data:{portable:!!window.CATALOG_PORTABLE,vw:innerWidth,vh:innerHeight,hl:document.body.classList.contains('hl-open'),preview:document.body.classList.contains('chosen-preview-open'),embed:document.body.classList.contains('card-embed-open'),acFs:document.body.classList.contains('ac-fs-open'),card:scr(card),hlBody:scr(body),embedBox:scr(embed),main:scr(main)},timestamp:Date.now()})}).catch(function(){});
  }catch(eDbgP){}
}"""

LOG_NEW = """function logCardFsEmbedScroll(why){
  try{
    var card=document.querySelector('.entry.highlight')
      || (document.body.classList.contains('chosen-preview-open')?document.querySelector('.entry.selected'):null);
    var body=card&&card.querySelector('.hl-body');
    var embed=document.getElementById('cardSearchEmbed');
    var main=document.getElementById('catalogMain');
    function scr(n){
      if(!n)return null;
      var cs=getComputedStyle(n);
      return {id:n.id||'',cls:(n.className||'').toString().slice(0,48),ovY:cs.overflowY,sh:n.scrollHeight,ch:n.clientHeight,st:Math.round(n.scrollTop),can:n.scrollHeight>n.clientHeight+2};
    }
    function vis(n){
      if(!n)return {on:false};
      var r=n.getBoundingClientRect(), cs=getComputedStyle(n);
      return {on:cs.display!=='none'&&cs.visibility!=='hidden'&&r.width>1&&r.height>1,d:cs.display,t:Math.round(r.top),b:Math.round(r.bottom),h:Math.round(r.height)};
    }
    var cover=card&&card.querySelector('.cover');
    var path=card&&card.querySelector('.path');
    var start=card&&card.querySelector('.card-chrome-start');
    var end=card&&card.querySelector('.card-chrome-end');
    var cr=card?card.getBoundingClientRect():null;
    """ + INGEST + r"""{sessionId:'c00e3e',runId:'post-fix',hypothesisId:'P',location:'catalog:cardFsEmbedScroll',message:why||'scroll-snap',data:{portable:!!window.CATALOG_PORTABLE,vw:innerWidth,vh:innerHeight,hl:document.body.classList.contains('hl-open'),preview:document.body.classList.contains('chosen-preview-open'),embed:document.body.classList.contains('card-embed-open'),cover:vis(cover),path:vis(path),name:vis(card&&card.querySelector('.lib-name')),embedHost:vis(embed),chromeStart:vis(start),chromeEnd:vis(end),cardTop:cr?Math.round(cr.top):null,card:scr(card),hlBody:scr(body),embedBox:scr(embed),main:scr(main)},timestamp:Date.now()}""" + TAIL + r"""
  }catch(eDbgP){}
}"""

PREVIEW_OLD = """  document.body.classList.add('chosen-preview-open');
  setOverlayFocus('preview');
}
function setOverlayFocus(which){"""

PREVIEW_NEW = """  document.body.classList.add('chosen-preview-open');
  setOverlayFocus('preview');
  if(typeof logCardFsEmbedScroll==='function')logCardFsEmbedScroll('preview-open');
}
function setOverlayFocus(which){"""

WHEEL_OLD = """  if(typeof catalogApplyWheel==='function'&&catalogApplyWheel(sc,dy)){e.preventDefault();e.stopPropagation();}
},{passive:false});
function collapseAllPatchTrees(){"""

WHEEL_NEW = """  if(box)box.scrollTop=0;
  var il=document.getElementById('catalogIndexList');
  if(il)il.scrollTop=0;
  if(typeof catalogApplyWheel==='function'&&catalogApplyWheel(sc,dy)){
    e.preventDefault();e.stopPropagation();
    try{
      var cb=document.querySelector('#catalogMain > .catalog-body');
      var main=document.getElementById('catalogMain');
      """ + INGEST + r"""{sessionId:'c00e3e',runId:'post-fix',hypothesisId:'IX',location:'catalog:embedIndexWheel',message:'embed-index-full-wheel',data:{portable:!!window.CATALOG_PORTABLE,ixOv:getComputedStyle(box).overflowY,ilOv:il?getComputedStyle(il).overflowY:'',ixH:box.scrollHeight,ixCh:box.clientHeight,ilSt:il?il.scrollTop:0,bodySt:cb?cb.scrollTop:0,mainSt:main?main.scrollTop:0,bodyCan:!!(cb&&cb.scrollHeight>cb.clientHeight+2),mainCan:!!(main&&main.scrollHeight>main.clientHeight+2)},timestamp:Date.now()}""" + TAIL + r"""
    }catch(eDbgIx){}
  }
},{passive:false});
function collapseAllPatchTrees(){"""

FIT_OLD = """    ['height','max-height','columns','column-width','column-count','column-fill','display','grid-template-columns'].forEach(function(p){il.style.removeProperty(p);});
    try{delete ix.dataset.ixFitInner;}catch(err){ix.dataset.ixFitInner='';}

    if(typeof syncBottomBelowIndex==='function')syncBottomBelowIndex();"""

FIT_NEW = """    ['height','max-height','columns','column-width','column-count','column-fill','display','grid-template-columns','overflow','overflow-y','overflow-x'].forEach(function(p){il.style.removeProperty(p);});
    if(ix.classList.contains('is-embedded')){
      ['height','max-height','overflow','overflow-y','overflow-x'].forEach(function(p){ix.style.removeProperty(p);});
    }
    try{delete ix.dataset.ixFitInner;}catch(err){ix.dataset.ixFitInner='';}

    if(typeof syncBottomBelowIndex==='function')syncBottomBelowIndex();"""


def patch(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    n = path.name
    if MARK in text:
        print("skip", n)
        return
    idx = text.rfind("</style>")
    if idx < 0:
        raise SystemExit(f"{n}: no </style>")
    text = text[:idx] + CSS_ADD + text[idx:]
    text = sub(text, SCROLL_EL_OLD, SCROLL_EL_NEW, f"{n}: scroll-el")
    text = sub(text, LOG_OLD, LOG_NEW, f"{n}: card-log")
    text = sub(text, PREVIEW_OLD, PREVIEW_NEW, f"{n}: preview-log")
    text = sub(text, WHEEL_OLD, WHEEL_NEW, f"{n}: ix-wheel")
    text = sub(text, FIT_OLD, FIT_NEW, f"{n}: ix-fit")
    raw = text.encode("utf-8")
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_bytes(raw)
    out = tmp.read_bytes().decode("utf-8")
    if not out.strip().endswith("</html>"):
        tmp.unlink()
        raise SystemExit(f"{n}: truncated")
    if len(raw) < 100000:
        tmp.unlink()
        raise SystemExit(f"{n}: size too small {len(raw)}")
    for keep in KEEP:
        if keep not in out:
            tmp.unlink()
            raise SystemExit(f"{n}: lost {keep}")
    if "c00e3e" not in out:
        tmp.unlink()
        raise SystemExit(f"{n}: lost c00e3e logs")
    tmp.replace(path)
    print("OK", n, len(raw))


def main() -> None:
    for p in FILES:
        if not p.exists():
            raise SystemExit(f"missing {p}")
        patch(p)


if __name__ == "__main__":
    main()
