#!/usr/bin/env python3
"""Dock About/Document to the content-pane bottom; shorten DS desktop title; dedupe Added libraries."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path("/home/phnx/kiro-kontakt-patch")
FILES = [
    ROOT / "public/catalogs/DS-CATALOG.html",
    ROOT / "public/catalogs/KONTAKT-CATALOG.html",
    ROOT / "public/catalogs/DS-CATALOG-portable.html",
    ROOT / "public/catalogs/KONTAKT-CATALOG-portable.html",
]

CSS_MARK = "</style></head><body class=\"search-mode\">"
CSS_ADD = r"""
/* fix-DOC-NOTE-DOCK: About/Document pinned to content-pane bottom; cards scroll above */
body.display-sides #catalogMain,
body.catalog-portable #catalogMain,
body.catalog-portable.display-content #catalogMain,
body.catalog-portable.display-middle #catalogMain,
body.catalog-portable.display-sides #catalogMain{
  display:flex!important;flex-direction:column!important;align-items:stretch!important;
  overflow:hidden!important;overflow-x:hidden!important;overflow-y:hidden!important;
  padding-bottom:0!important;min-height:0
}
body.has-card-min-dock.display-sides #catalogMain,
body.has-card-min-dock.catalog-portable #catalogMain{padding-bottom:0!important}
body.display-sides #catalogMain>.catalog-body,
body.catalog-portable #catalogMain>.catalog-body,
body.catalog-portable.display-content #catalogMain>.catalog-body,
body.catalog-portable.display-middle #catalogMain>.catalog-body,
body.catalog-portable.display-sides #catalogMain>.catalog-body{
  flex:1 1 auto!important;min-height:0!important;
  overflow-x:hidden!important;overflow-y:auto!important;
  -webkit-overflow-scrolling:touch;overscroll-behavior:contain
}
body.display-sides #catalogMain>#catalogDocNote,
body.display-sides #catalogMain>.catalog-doc-note,
body.catalog-portable #catalogMain>#catalogDocNote,
body.catalog-portable #catalogMain>.catalog-doc-note{
  flex:0 0 auto!important;margin:0!important;width:auto!important;max-width:none!important;
  align-self:stretch!important;order:9;z-index:14;box-sizing:border-box;
  border-radius:8px 8px 0 0;max-height:min(42dvh,18rem);overflow:hidden;
  padding-bottom:env(safe-area-inset-bottom,0px)
}
.catalog-doc-note:not(.is-collapsed) .catalog-doc-note-body{
  max-height:min(36dvh,16rem);overflow-x:hidden;overflow-y:auto;-webkit-overflow-scrolling:touch
}
body:is(.hl-open,.gallery-open,.img-focus-open,.desc-reader-open,.path-reader-open,.desc-focus-open,.path-focus-open,.chosen-preview-open,.card-embed-open) #catalogDocNote{
  visibility:hidden!important;pointer-events:none!important
}
body.catalog-portable:is(.ac-fs-open,.kw-fs-open,.dual-fs-open) #catalogDocNote{
  visibility:hidden!important;pointer-events:none!important
}
body.catalog-portable.index-fill-doc.index-window-open #catalogIndex:not(.is-embedded):not(.is-collapsed){
  flex:1 1 0%!important;height:auto!important;max-height:none!important;min-height:0!important;
  margin-top:0!important;margin-bottom:4px!important
}
""" + CSS_MARK

ENSURE_OLD = "paras.forEach(function(p){p.removeAttribute('style');if(p.parentNode!==body)body.appendChild(p);});"
ENSURE_NEW = (
    "paras.forEach(function(p){p.removeAttribute('style');if(p.parentNode!==body){"
    "var t=(p.textContent||'').replace(/\\s+/g,' ').trim();var dup=false;"
    "for(var i=0;i<body.children.length;i++){"
    "if((body.children[i].textContent||'').replace(/\\s+/g,' ').trim()===t){dup=true;break;}}"
    "if(dup){p.remove();return;}body.appendChild(p);}});"
    "(function(){var seen={};[].slice.call(body.children).forEach(function(ch){"
    "var k=(ch.textContent||'').replace(/\\s+/g,' ').trim();if(!k)return;"
    "if(seen[k])ch.remove();else seen[k]=1;});})();"
)

TOGGLE_OLD = """  applyCatalogDocNoteOpen(open);
  try{localStorage.setItem(catalogDocNoteKey(),open?'1':'0');}catch(err){}
  
}"""
TOGGLE_NEW = """  applyCatalogDocNoteOpen(open);
  try{localStorage.setItem(catalogDocNoteKey(),open?'1':'0');}catch(err){}
  if(typeof placeCatalogJumpStack==='function')placeCatalogJumpStack();
}"""

APPLY_OPEN_OLD = (
    "  if(btn){btn.setAttribute('aria-expanded',open?'true':'false');"
    "btn.setAttribute('title',open?'Hide document text':'Show document text');}\n}"
)
APPLY_OPEN_NEW = (
    "  if(btn){btn.setAttribute('aria-expanded',open?'true':'false');"
    "btn.setAttribute('title',open?'Hide document text':'Show document text');}\n"
    "  if(typeof placeCatalogJumpStack==='function')placeCatalogJumpStack();\n}"
)

PARK_OLD = """  var top=null;
  try{top=w.querySelector(':scope > a.top');}catch(err){top=null;}
  if(!top)top=w.querySelector('a.top');
  if(note.parentNode!==w||(top&&note.nextElementSibling!==top)||(!top&&w.lastElementChild!==note)){
    if(top)w.insertBefore(note,top);else w.appendChild(note);
  }
  
}"""
PARK_NEW = """  var cb=w.querySelector(':scope > .catalog-body')||w.querySelector('.catalog-body');
  var ix=document.getElementById('catalogIndex');
  if(ix&&cb){
    if(ix.classList.contains('is-embedded')){
      if(ix.parentNode!==cb){if(cb.firstChild)cb.insertBefore(ix,cb.firstChild);else cb.appendChild(ix);}
    }else if(ix.parentNode!==w){
      w.insertBefore(ix,cb);
    }
  }
  if(note.parentNode!==w||w.lastElementChild!==note)w.appendChild(note);
  if(typeof placeCatalogJumpStack==='function')placeCatalogJumpStack();
}"""

INSET_FN = """function catalogDocNoteInsetBottom(){
  var note=document.getElementById('catalogDocNote');
  if(!note)return 0;
  var cs=getComputedStyle(note);
  if(cs.display==='none'||cs.visibility==='hidden')return 0;
  var nr=note.getBoundingClientRect();
  if(!nr||nr.height<8)return 0;
  return Math.round(nr.height)+8;
}
"""

JUMP_DESK_OLD = (
    "    var right=Math.max(6,Math.round((window.innerWidth||0)-r.right)+10);\n"
    "    var bottom=Math.max(6,Math.round((window.innerHeight||0)-r.bottom)+12);"
)
JUMP_DESK_NEW = (
    "    var right=Math.max(6,Math.round((window.innerWidth||0)-r.right)+10);\n"
    "    var bottom=Math.max(6,Math.round((window.innerHeight||0)-r.bottom)+12+(typeof catalogDocNoteInsetBottom==='function'?catalogDocNoteInsetBottom():0));"
)
JUMP_PORT_OLD = (
    "    var right=Math.max(6,Math.round((window.innerWidth||0)-r.right)+insetR);\n"
    "    var bottom=Math.max(6,Math.round((window.innerHeight||0)-r.bottom)+insetB);"
)
JUMP_PORT_NEW = (
    "    var right=Math.max(6,Math.round((window.innerWidth||0)-r.right)+insetR);\n"
    "    var bottom=Math.max(6,Math.round((window.innerHeight||0)-r.bottom)+insetB+(typeof catalogDocNoteInsetBottom==='function'?catalogDocNoteInsetBottom():0));"
)

CARDMIN_OLD = """    d.style.left=Math.round(r.left)+'px';
    d.style.width=Math.round(r.width)+'px';
    d.style.bottom='0';"""
CARDMIN_NEW = """    d.style.left=Math.round(r.left)+'px';
    d.style.width=Math.round(r.width)+'px';
    d.style.bottom=Math.max(0,typeof catalogDocNoteInsetBottom==='function'?catalogDocNoteInsetBottom():0)+'px';"""

GOTOP_OLD = (
    "    if(ix)ix.dataset.goingTop='1';\n"
    "    if(cm){try{cm.scrollTo({top:cm.scrollTop,behavior:'instant'});}catch(err){cm.scrollTop=cm.scrollTop;}"
    "try{cm.scrollTo({top:0,behavior:'smooth'});}catch(err){cm.scrollTop=0;}}"
)
GOTOP_NEW = (
    "    if(ix)ix.dataset.goingTop='1';\n"
    "    var sc=(typeof catalogContentScroller==='function'&&catalogContentScroller())||cm;\n"
    "    if(sc){try{sc.scrollTo({top:sc.scrollTop,behavior:'instant'});}catch(err){sc.scrollTop=sc.scrollTop;}"
    "try{sc.scrollTo({top:0,behavior:'smooth'});}catch(err){sc.scrollTop=0;}}"
)
GOBOT_OLD = (
    "    if(cm){try{cm.scrollTo({top:cm.scrollTop,behavior:'instant'});}catch(err){cm.scrollTop=cm.scrollTop;}"
    "try{cm.scrollTo({top:cm.scrollHeight,behavior:'smooth'});}catch(err){cm.scrollTop=cm.scrollHeight;}}"
)
GOBOT_NEW = (
    "    var sc=(typeof catalogContentScroller==='function'&&catalogContentScroller())||cm;\n"
    "    if(sc){try{sc.scrollTo({top:sc.scrollTop,behavior:'instant'});}catch(err){sc.scrollTop=sc.scrollTop;}"
    "try{sc.scrollTo({top:sc.scrollHeight,behavior:'smooth'});}catch(err){sc.scrollTop=sc.scrollHeight;}}"
)

SCROLLER_OLD = """function catalogContentScroller(){
  var cm=document.getElementById('catalogMain');
  var cb=cm&&(cm.querySelector(':scope > .catalog-body')||cm.querySelector('.catalog-body'));
  if(document.body.classList.contains('index-window-open')&&cb)return cb;
  return cm;
}"""
SCROLLER_NEW = """function catalogContentScroller(){
  var cm=document.getElementById('catalogMain');
  var cb=cm&&(cm.querySelector(':scope > .catalog-body')||cm.querySelector('.catalog-body'));
  if(cb)return cb;
  return cm;
}"""
SCROLLER_INSERT = """function catalogContentScroller(){
  var cm=document.getElementById('catalogMain');
  var cb=cm&&(cm.querySelector(':scope > .catalog-body')||cm.querySelector('.catalog-body'));
  if(cb)return cb;
  return cm;
}
window.catalogContentScroller=catalogContentScroller;
"""

STRIPE_OLD = "    function scroller(){return document.getElementById(scrollId)||host();}"
STRIPE_NEW = (
    "    function scroller(){"
    "if(mark==='content'&&typeof window.catalogContentScroller==='function'){"
    "var c=window.catalogContentScroller();if(c)return c;}"
    "return document.getElementById(scrollId)||host();}"
)

DOCK_KEY = "function catalogDocNoteKey(){"
PLACE_FN = "function placeCatalogJumpStack(){"

NOTE_BODY_RE = re.compile(
    r'(<div class="catalog-doc-note-body" id="catalogDocNoteBody">)(.*?)(</div></aside>)',
    re.S,
)


def once(text: str, old: str, new: str, label: str, name: str) -> str:
    n = text.count(old)
    if n != 1:
        raise SystemExit(f"{name}: {label} count={n} expected 1")
    return text.replace(old, new, 1)


def dedupe_note_body(text: str, name: str) -> tuple[str, int]:
    m = NOTE_BODY_RE.search(text)
    if not m:
        raise SystemExit(f"{name}: catalogDocNoteBody missing")
    inner = m.group(2)
    paras = re.findall(r"<p\b[^>]*>.*?</p>", inner, re.S)
    if not paras:
        return text, 0
    seen: set[str] = set()
    kept: list[str] = []
    removed = 0
    for p in paras:
        key = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", p)).strip().lower()
        if key in seen:
            removed += 1
            continue
        seen.add(key)
        kept.append(p)
    sep = "\n" if "\n" in inner else ""
    new_inner = sep.join(kept)
    if inner.strip().endswith("</p>") and inner.endswith("\n"):
        new_inner += "\n"
    elif inner.endswith("\n") and not new_inner.endswith("\n"):
        new_inner += "\n"
    text = text[: m.start(2)] + new_inner + text[m.end(2) :]
    return text, removed


def patch_titles(text: str, name: str) -> str:
    if name == "DS-CATALOG.html":
        text = once(
            text,
            "<title>DecentSampler Library Catalog</title>",
            "<title>Decent Library</title>",
            "ds-title",
            name,
        )
        text = once(
            text,
            '<h1 id="top">DecentSampler Library Catalog</h1>',
            '<h1 id="top">Decent Library</h1>',
            "ds-h1",
            name,
        )
    elif name == "KONTAKT-CATALOG.html":
        if "<title>Kontakt Library</title>" not in text:
            raise SystemExit(f"{name}: expected Kontakt Library title")
        if '<h1 id="top">Kontakt Library</h1>' not in text:
            raise SystemExit(f"{name}: expected Kontakt Library h1")
    elif name == "DS-CATALOG-portable.html":
        if "<title>DS Lib</title>" not in text:
            raise SystemExit(f"{name}: portable title drifted")
    elif name == "KONTAKT-CATALOG-portable.html":
        if "<title>Kontakt Lib</title>" not in text:
            raise SystemExit(f"{name}: portable title drifted")
    return text


def patch(path: Path) -> None:
    raw = path.read_bytes()
    orig_size = len(raw)
    text = raw.decode("utf-8")
    name = path.name
    if not text.strip().endswith("</html>"):
        raise SystemExit(f"{name}: missing </html> before patch")
    if CSS_MARK not in text or text.count(CSS_MARK) != 1:
        raise SystemExit(f"{name}: css mark count {text.count(CSS_MARK)}")

    if "fix-DOC-NOTE-DOCK" not in text:
        text = text.replace(CSS_MARK, CSS_ADD, 1)

    text = once(text, ENSURE_OLD, ENSURE_NEW, "ensure-dedupe", name)
    text = once(text, TOGGLE_OLD, TOGGLE_NEW, "toggle-place", name)
    text = once(text, APPLY_OPEN_OLD, APPLY_OPEN_NEW, "apply-open-place", name)
    text = once(text, PARK_OLD, PARK_NEW, "park-note", name)

    if "function catalogDocNoteInsetBottom(" not in text:
        if text.count(PLACE_FN) != 1:
            raise SystemExit(f"{name}: placeCatalogJumpStack count={text.count(PLACE_FN)}")
        text = text.replace(PLACE_FN, INSET_FN + PLACE_FN, 1)

    if JUMP_DESK_OLD in text:
        text = once(text, JUMP_DESK_OLD, JUMP_DESK_NEW, "jump-desk", name)
    elif JUMP_PORT_OLD in text:
        text = once(text, JUMP_PORT_OLD, JUMP_PORT_NEW, "jump-port", name)
    else:
        raise SystemExit(f"{name}: jump bottom mark missing")

    if CARDMIN_OLD in text:
        text = once(text, CARDMIN_OLD, CARDMIN_NEW, "cardmin", name)

    text = once(text, GOTOP_OLD, GOTOP_NEW, "gotop", name)
    text = once(text, GOBOT_OLD, GOBOT_NEW, "gobot", name)

    if SCROLLER_OLD in text:
        text = once(text, SCROLLER_OLD, SCROLLER_NEW, "scroller", name)
    elif "function catalogContentScroller(" not in text:
        if text.count(DOCK_KEY) != 1:
            raise SystemExit(f"{name}: catalogDocNoteKey count={text.count(DOCK_KEY)}")
        text = text.replace(DOCK_KEY, SCROLLER_INSERT + DOCK_KEY, 1)

    if STRIPE_OLD in text:
        text = once(text, STRIPE_OLD, STRIPE_NEW, "stripe-scroller", name)

    text, removed = dedupe_note_body(text, name)
    text = patch_titles(text, name)

    if "fix-DOC-NOTE-DOCK" not in text:
        raise SystemExit(f"{name}: css marker missing after patch")
    if "function catalogDocNoteInsetBottom(" not in text:
        raise SystemExit(f"{name}: inset fn missing")
    if not text.strip().endswith("</html>"):
        raise SystemExit(f"{name}: truncated, missing </html>")

    out = text.encode("utf-8")
    if orig_size > 4_000_000 and len(out) < orig_size * 0.9:
        raise SystemExit(f"{name}: size collapsed {orig_size} -> {len(out)}")
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_bytes(out)
    wrote = tmp.read_bytes()
    if len(wrote) != len(out):
        tmp.unlink()
        raise SystemExit(f"{name}: tmp size mismatch")
    if not wrote.decode("utf-8").strip().endswith("</html>"):
        tmp.unlink()
        raise SystemExit(f"{name}: tmp missing </html>")
    tmp.replace(path)
    print(
        "OK",
        name,
        "bytes",
        len(out),
        "delta",
        len(out) - orig_size,
        "deduped",
        removed,
        "dock",
        "fix-DOC-NOTE-DOCK" in text,
    )


def main() -> None:
    for p in FILES:
        if not p.exists():
            raise SystemExit(f"missing {p}")
        patch(p)


if __name__ == "__main__":
    main()
