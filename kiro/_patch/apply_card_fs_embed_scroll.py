#!/usr/bin/env python3
"""Fullscreen/preview/embed cards scroll when chrome+embed don't fit the viewport."""
from pathlib import Path

ROOT = Path("/home/phnx/kiro-kontakt-patch")
FILES = [
    ROOT / "public/catalogs/KONTAKT-CATALOG.html",
    ROOT / "public/catalogs/DS-CATALOG.html",
    ROOT / "public/catalogs/KONTAKT-CATALOG-portable.html",
    ROOT / "public/catalogs/DS-CATALOG-portable.html",
]
MARK = "fix-CARD-FS-EMBED-SCROLL-v1"
KEEP = (
    "c00e3e",
    "fix-PORTABLE-FS-FLIP-INDEX-v1",
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
/* fix-CARD-FS-EMBED-SCROLL-v1: overlay/preview/embed card scrolls; catalog behind stays locked */
@media all{
  body.hl-open,body.chosen-preview-open,body.card-embed-open{
    overflow:hidden!important;overscroll-behavior:none
  }
  .entry.highlight,
  body.hl-open .entry.highlight,
  body.catalog-portable .entry.highlight,
  body.card-embed-open .entry.highlight{
    overflow-x:hidden!important;overflow-y:auto!important;
    overscroll-behavior:contain!important;-webkit-overflow-scrolling:touch!important;
    display:flex!important;flex-direction:column!important;align-items:stretch!important
  }
  .entry.highlight .cover,
  body.hl-open .entry.highlight .cover{
    flex:0 0 auto!important;flex-shrink:0!important
  }
  .entry.highlight .hl-body,
  body.hl-open .entry.highlight .hl-body,
  body.catalog-portable .entry.highlight .hl-body,
  body.card-embed-open .entry.highlight .hl-body{
    flex:0 0 auto!important;flex-shrink:0!important;
    min-height:auto!important;max-height:none!important;
    overflow:visible!important;overflow-x:visible!important;overflow-y:visible!important
  }
  .entry.highlight .card-chrome-start,
  .entry.highlight .card-chrome-end{
    position:sticky!important;top:max(var(--card-chrome-inset,.5rem),env(safe-area-inset-top))!important;
    z-index:841!important;flex:0 0 auto!important;align-self:flex-start!important;
    width:max-content!important;max-width:48%!important;background:transparent
  }
  .entry.highlight .card-chrome-end{margin-left:auto!important;margin-top:-2.85rem!important;align-self:flex-end!important}
  body.chosen-preview-open .entry.selected:not(.highlight),
  body.catalog-portable.chosen-preview-open .entry.selected:not(.highlight),
  body.card-embed-open.chosen-preview-open .entry.selected:not(.highlight),
  body.catalog-portable.card-embed-open.chosen-preview-open .entry.selected:not(.highlight){
    overflow-x:hidden!important;overflow-y:auto!important;
    overscroll-behavior:contain!important;-webkit-overflow-scrolling:touch!important
  }
  body.card-embed-open.chosen-preview-open .entry.selected:not(.highlight) .cover,
  body.card-embed-open.chosen-preview-open .entry.selected:not(.highlight) .lib-name,
  body.card-embed-open.chosen-preview-open .entry.selected:not(.highlight) .lib-notes,
  body.card-embed-open.chosen-preview-open .entry.selected:not(.highlight) .noart,
  body.card-embed-open.chosen-preview-open .entry.selected:not(.highlight) .summary-panel,
  body.card-embed-open.chosen-preview-open .entry.selected:not(.highlight) .path,
  body.card-embed-open.chosen-preview-open .entry.selected:not(.highlight) details.patches,
  body.card-embed-open.chosen-preview-open .entry.selected:not(.highlight) .patches,
  body.card-embed-open.chosen-preview-open .entry.selected:not(.highlight) .card-actions{
    display:block!important
  }
  body.card-embed-open.chosen-preview-open .entry.selected:not(.highlight) .cover{display:flex!important;flex:0 0 auto!important}
  body.card-embed-open.chosen-preview-open .entry.selected:not(.highlight) .card-actions{display:flex!important;flex:0 0 auto!important}
  body.card-embed-open.chosen-preview-open .entry.selected:not(.highlight) .note-text.has-note{display:block!important}
  body.card-embed-open.chosen-preview-open .entry.selected:not(.highlight) .hl-body{
    display:flex!important;flex-direction:column!important;align-items:stretch!important;
    flex:0 0 auto!important;overflow:visible!important;min-height:auto!important;max-height:none!important
  }
  body.chosen-preview-open .entry.selected:not(.highlight) .card-chrome-start,
  body.chosen-preview-open .entry.selected:not(.highlight) .card-chrome-end{
    position:sticky!important;top:max(var(--card-chrome-inset,.5rem),env(safe-area-inset-top))!important;
    z-index:841!important;width:max-content!important;max-width:48%!important
  }
  body.chosen-preview-open .entry.selected:not(.highlight) .card-chrome-end{
    margin-left:auto!important;margin-top:-2.85rem!important
  }
  body.hl-open .entry.highlight #cardSearchEmbed,
  body.hl-open .entry.highlight .card-search-embed,
  body.card-embed-open .entry.highlight #cardSearchEmbed,
  body.card-embed-open .entry.highlight .card-search-embed,
  body.card-embed-open.chosen-preview-open .entry.selected:not(.highlight) #cardSearchEmbed,
  body.card-embed-open.chosen-preview-open .entry.selected:not(.highlight) .card-search-embed{
    display:flex!important;flex:1 1 auto!important;flex-shrink:0!important;
    min-height:min(42vh,20rem)!important;max-height:none!important;
    overflow:hidden!important;position:relative!important;inset:auto!important;order:8
  }
}
@media(orientation:portrait){
  body.catalog-portable.card-embed-open.chosen-preview-open .entry.selected:not(.highlight){
    overflow-x:hidden!important;overflow-y:auto!important;-webkit-overflow-scrolling:touch!important
  }
  body.catalog-portable.card-embed-open.chosen-preview-open .entry.selected:not(.highlight) .preview-back,
  body.catalog-portable.card-embed-open.chosen-preview-open .entry.selected:not(.highlight) .fs-btn,
  body.catalog-portable.card-embed-open.chosen-preview-open .entry.selected:not(.highlight) .hl-min{
    position:fixed!important
  }
}
"""

JS_HELPER = r"""
function cardFsEmbedScrollEl(){
  return document.querySelector('.entry.highlight')
    || (document.body.classList.contains('chosen-preview-open')?document.querySelector('.entry.selected'):null);
}
function logCardFsEmbedScroll(why){
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
    """ + INGEST + r"""{sessionId:'c00e3e',runId:'post-fix',hypothesisId:'P',location:'catalog:cardFsEmbedScroll',message:why||'scroll-snap',data:{portable:!!window.CATALOG_PORTABLE,vw:innerWidth,vh:innerHeight,hl:document.body.classList.contains('hl-open'),preview:document.body.classList.contains('chosen-preview-open'),embed:document.body.classList.contains('card-embed-open'),acFs:document.body.classList.contains('ac-fs-open'),card:scr(card),hlBody:scr(body),embedBox:scr(embed),main:scr(main)},timestamp:Date.now()}""" + TAIL + r"""
  }catch(eDbgP){}
}
function bindCardFsEmbedScroll(){
  if(bindCardFsEmbedScroll._on)return;
  bindCardFsEmbedScroll._on=true;
  document.addEventListener('wheel',function(e){
    var card=cardFsEmbedScrollEl();
    if(!card)return;
    if(e.target&&e.target.closest&&e.target.closest('iframe,.card-search-frame'))return;
    var cs=getComputedStyle(card);
    if(cs.overflowY!=='auto'&&cs.overflowY!=='scroll')return;
    if(card.scrollHeight<=card.clientHeight+2)return;
    var inner=e.target&&e.target.closest&&e.target.closest('.summary-panel,.card-search-reader,.card-yt-comments-strip,.card-google-cse');
    if(inner){
      var ics=getComputedStyle(inner);
      if((ics.overflowY==='auto'||ics.overflowY==='scroll')&&inner.scrollHeight>inner.clientHeight+2){
        var atEnd=e.deltaY>0&&inner.scrollTop+inner.clientHeight>=inner.scrollHeight-2;
        var atStart=e.deltaY<0&&inner.scrollTop<=0;
        if(!atEnd&&!atStart)return;
      }
    }
    var main=document.getElementById('catalogMain');
    var catBody=document.querySelector('#catalogMain > .catalog-body');
    if(e.target&&e.target.closest&&((main&&main.contains(e.target)&&!card.contains(e.target))||(catBody&&catBody.contains(e.target)&&!card.contains(e.target))))return;
    card.scrollTop+=e.deltaY;
    if(e.cancelable)e.preventDefault();
  },{passive:false,capture:true});
}
"""

OPEN_OLD = """function openOverlay(el){
  if(!el)return;
  parkSearchBehindOverlay();"""

OPEN_NEW = JS_HELPER + """function openOverlay(el){
  if(!el)return;
  if(typeof bindCardFsEmbedScroll==='function')bindCardFsEmbedScroll();
  parkSearchBehindOverlay();"""

EARLY_OLD = """    document.body.classList.add('hl-open');
    syncViewportLock();
    return;
  }
  closeOverlay({skipScroll:true});"""

EARLY_NEW = """    document.body.classList.add('hl-open');
    syncViewportLock();
    if(typeof logCardFsEmbedScroll==='function')logCardFsEmbedScroll('overlay-already');
    return;
  }
  closeOverlay({skipScroll:true});"""

END_OLD = """  document.body.classList.add('hl-open');
  syncViewportLock();
}
var GRID_PATCH_OVERLAY_MIN=12;"""

END_NEW = """  document.body.classList.add('hl-open');
  syncViewportLock();
  if(typeof logCardFsEmbedScroll==='function')logCardFsEmbedScroll('overlay-open');
}
var GRID_PATCH_OVERLAY_MIN=12;"""

EMBED_OLD = "  cardSearchShowEmbedHint();"
EMBED_NEW = "  cardSearchShowEmbedHint();\n  if(typeof logCardFsEmbedScroll==='function')logCardFsEmbedScroll('embed-open');\n  if(typeof bindCardFsEmbedScroll==='function')bindCardFsEmbedScroll();"


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
    text = sub(text, OPEN_OLD, OPEN_NEW, f"{n}: open-helper")
    text = sub(text, EARLY_OLD, EARLY_NEW, f"{n}: overlay-early")
    text = sub(text, END_OLD, END_NEW, f"{n}: overlay-end")
    text = sub(text, EMBED_OLD, EMBED_NEW, f"{n}: embed-log")
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
    if "fix-PORTABLE-FS-FLIP-INDEX-v1" not in out:
        tmp.unlink()
        raise SystemExit(f"{n}: lost fs-flip-index")
    tmp.replace(path)
    print("OK", n, len(raw))


def main() -> None:
    for p in FILES:
        if not p.exists():
            raise SystemExit(f"missing {p}")
        patch(p)


if __name__ == "__main__":
    main()
