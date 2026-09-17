#!/usr/bin/env python3
"""Give About/Document the same Window / Embed option as Index."""
from __future__ import annotations

from pathlib import Path

ROOT = Path("/home/phnx/kiro-kontakt-patch")
FILES = [
    ROOT / "public/catalogs/DS-CATALOG.html",
    ROOT / "public/catalogs/KONTAKT-CATALOG.html",
    ROOT / "public/catalogs/DS-CATALOG-portable.html",
    ROOT / "public/catalogs/KONTAKT-CATALOG-portable.html",
]

KEY_OLD = "function catalogDocNoteKey(){return 'catalog-doc-note-open-'+(window.CATALOG_NS||'catalog');}\n"
KEY_NEW = KEY_OLD + r"""function docNoteEmbedPrefKey(){return 'catalog-doc-note-embed-'+(window.CATALOG_NS||'catalog');}
function readDocNoteEmbedPref(){
  try{var v=localStorage.getItem(docNoteEmbedPrefKey());if(v==='1')return true;if(v==='0')return false;}catch(eDnP){}
  return null;
}
function writeDocNoteEmbedPref(on){
  try{localStorage.setItem(docNoteEmbedPrefKey(),on?'1':'0');}catch(eDnW){}
}
function ensureDocNoteChrome(note){
  if(!note)return;
  var toggle=document.getElementById('catalogDocNoteToggle')||note.querySelector('.catalog-doc-note-toggle');
  var head=note.querySelector(':scope > .catalog-doc-note-head')||note.querySelector('.catalog-doc-note-head');
  if(!head){
    head=document.createElement('div');
    head.className='catalog-doc-note-head';
    var bodyEl=document.getElementById('catalogDocNoteBody')||note.querySelector('.catalog-doc-note-body');
    if(toggle)head.appendChild(toggle);
    if(bodyEl)note.insertBefore(head,bodyEl);
    else if(note.firstChild)note.insertBefore(head,note.firstChild);
    else note.appendChild(head);
  }else if(toggle&&toggle.parentNode!==head){
    head.insertBefore(toggle,head.firstChild);
  }
  var btn=document.getElementById('catalogDocNoteEmbed')||head.querySelector('.catalog-doc-note-embed');
  if(!btn){
    btn=document.createElement('button');
    btn.type='button';
    btn.className='catalog-index-embed catalog-doc-note-embed';
    btn.id='catalogDocNoteEmbed';
    btn.setAttribute('onclick','event.preventDefault();event.stopPropagation();toggleDocNoteEmbed()');
    head.appendChild(btn);
  }else if(btn.parentNode!==head){
    head.appendChild(btn);
  }
  btn.hidden=false;
}
function syncDocNoteEmbedBtn(){
  var note=document.getElementById('catalogDocNote');
  var btn=document.getElementById('catalogDocNoteEmbed');
  if(note){
    var on=note.classList.contains('is-embedded');
    document.body.classList.toggle('doc-note-window-open',!on);
    document.body.classList.toggle('doc-note-embedded',!!on);
  }
  if(!btn)return;
  var pressed=!!(note&&note.classList.contains('is-embedded'));
  btn.hidden=false;
  btn.setAttribute('aria-pressed',pressed?'true':'false');
  btn.textContent=pressed?'Window':'Embed';
  btn.title=pressed?'Show About as a docked window at the bottom':'Embed About with the catalog cards';
}
function applyDocNoteEmbedPref(note){
  note=note||document.getElementById('catalogDocNote');
  if(!note)return;
  ensureDocNoteChrome(note);
  var pref=readDocNoteEmbedPref();
  if(pref===true)note.classList.add('is-embedded');
  else note.classList.remove('is-embedded');
  syncDocNoteEmbedBtn();
}
function toggleDocNoteEmbed(){
  var note=document.getElementById('catalogDocNote');
  if(!note)return;
  var on=note.classList.toggle('is-embedded');
  writeDocNoteEmbedPref(on);
  // #region agent log
  try{
    fetch('http://127.0.0.1:7529/ingest/1cf46354-1d61-4c80-bd72-a340f1db1b51',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'c00e3e'},body:JSON.stringify({sessionId:'c00e3e',runId:'doc-embed',hypothesisId:'D',location:'catalog:toggleDocNoteEmbed',message:'about embed toggle',data:{on:on,parent:(note.parentElement&&note.parentElement.id)||'',portable:!!window.CATALOG_PORTABLE,cls:document.body.className,pref:readDocNoteEmbedPref()},timestamp:Date.now()})}).catch(function(){});
  }catch(eDbgD){}
  // #endregion
  if(typeof parkCatalogDocNote==='function')parkCatalogDocNote();
  if(typeof applyIndexFillDocStyles==='function')applyIndexFillDocStyles();
  if(typeof syncIndexWindowDock==='function')syncIndexWindowDock();
  if(typeof placeCatalogJumpStack==='function')placeCatalogJumpStack();
  syncDocNoteEmbedBtn();
}
window.docNoteEmbedPrefKey=docNoteEmbedPrefKey;
window.readDocNoteEmbedPref=readDocNoteEmbedPref;
window.writeDocNoteEmbedPref=writeDocNoteEmbedPref;
window.syncDocNoteEmbedBtn=syncDocNoteEmbedBtn;
window.toggleDocNoteEmbed=toggleDocNoteEmbed;
window.applyDocNoteEmbedPref=applyDocNoteEmbedPref;
"""

ASIDE_OLD = (
    '<aside class="catalog-doc-note is-collapsed" id="catalogDocNote">'
    '<button type="button" class="catalog-doc-note-toggle" id="catalogDocNoteToggle" aria-expanded="false" '
    'aria-controls="catalogDocNoteBody" title="Show document text" '
    'onclick="event.preventDefault();event.stopPropagation();toggleCatalogDocNote()">'
    '<span class="toggle-arrow">&#9660;</span> About / Document</button>'
    '<div class="catalog-doc-note-body" id="catalogDocNoteBody">'
)
ASIDE_NEW = (
    '<aside class="catalog-doc-note is-collapsed" id="catalogDocNote">'
    '<div class="catalog-doc-note-head">'
    '<button type="button" class="catalog-doc-note-toggle" id="catalogDocNoteToggle" aria-expanded="false" '
    'aria-controls="catalogDocNoteBody" title="Show document text" '
    'onclick="event.preventDefault();event.stopPropagation();toggleCatalogDocNote()">'
    '<span class="toggle-arrow">&#9660;</span> About / Document</button>'
    '<button type="button" class="catalog-index-embed catalog-doc-note-embed" id="catalogDocNoteEmbed" '
    'aria-pressed="false" title="Embed About with the catalog cards" '
    'onclick="event.preventDefault();event.stopPropagation();toggleDocNoteEmbed()">Embed</button></div>'
    '<div class="catalog-doc-note-body" id="catalogDocNoteBody">'
)

INNER_OLD = (
    "note.innerHTML='<button type=\"button\" class=\"catalog-doc-note-toggle\" id=\"catalogDocNoteToggle\" "
    "aria-expanded=\"false\" aria-controls=\"catalogDocNoteBody\" title=\"Show document text\" "
    "onclick=\"event.preventDefault();event.stopPropagation();toggleCatalogDocNote()\">"
    "<span class=\"toggle-arrow\">&#9660;</span> About / Document</button>"
    "<div class=\"catalog-doc-note-body\" id=\"catalogDocNoteBody\"></div>';"
)
INNER_NEW = (
    "note.innerHTML='<div class=\"catalog-doc-note-head\">"
    "<button type=\"button\" class=\"catalog-doc-note-toggle\" id=\"catalogDocNoteToggle\" "
    "aria-expanded=\"false\" aria-controls=\"catalogDocNoteBody\" title=\"Show document text\" "
    "onclick=\"event.preventDefault();event.stopPropagation();toggleCatalogDocNote()\">"
    "<span class=\"toggle-arrow\">&#9660;</span> About / Document</button>"
    "<button type=\"button\" class=\"catalog-index-embed catalog-doc-note-embed\" id=\"catalogDocNoteEmbed\" "
    "aria-pressed=\"false\" title=\"Embed About with the catalog cards\" "
    "onclick=\"event.preventDefault();event.stopPropagation();toggleDocNoteEmbed()\">Embed</button></div>"
    "<div class=\"catalog-doc-note-body\" id=\"catalogDocNoteBody\"></div>';"
)

APPLY_OLD = "  applyCatalogDocNoteOpen(saved==='1');\n  return note;\n"
APPLY_NEW = (
    "  applyCatalogDocNoteOpen(saved==='1');\n"
    "  if(typeof applyDocNoteEmbedPref==='function')applyDocNoteEmbedPref(note);\n"
    "  return note;\n"
)

PARK_OLD = (
    "  if(note.parentNode!==w||w.lastElementChild!==note)w.appendChild(note);\n"
    "  if(typeof placeCatalogJumpStack==='function')placeCatalogJumpStack();\n"
    "}"
)
PARK_NEW = (
    "  var embed=note.classList.contains('is-embedded');\n"
    "  document.body.classList.toggle('doc-note-window-open',!embed);\n"
    "  document.body.classList.toggle('doc-note-embedded',!!embed);\n"
    "  if(embed&&cb){\n"
    "    if(note.parentNode!==cb||cb.lastElementChild!==note)cb.appendChild(note);\n"
    "  }else{\n"
    "    if(note.parentNode!==w||w.lastElementChild!==note)w.appendChild(note);\n"
    "  }\n"
    "  if(typeof syncDocNoteEmbedBtn==='function')syncDocNoteEmbedBtn();\n"
    "  if(typeof placeCatalogJumpStack==='function')placeCatalogJumpStack();\n"
    "}"
)

INSET_OLD = """function catalogDocNoteInsetBottom(){
  var note=document.getElementById('catalogDocNote');
  if(!note)return 0;
  var cs=getComputedStyle(note);
  if(cs.display==='none'||cs.visibility==='hidden')return 0;
  var nr=note.getBoundingClientRect();
  if(!nr||nr.height<8)return 0;
  return Math.round(nr.height)+8;
}"""
INSET_NEW = """function catalogDocNoteInsetBottom(){
  var note=document.getElementById('catalogDocNote');
  if(!note||note.classList.contains('is-embedded'))return 0;
  var cs=getComputedStyle(note);
  if(cs.display==='none'||cs.visibility==='hidden')return 0;
  var nr=note.getBoundingClientRect();
  if(!nr||nr.height<8)return 0;
  return Math.round(nr.height)+8;
}"""

TOGGLE_CSS_OLD = (
    ".catalog-doc-note-toggle{display:flex;align-items:center;gap:.45rem;width:100%;"
    "min-height:2.25rem;padding:.35rem .7rem;border:0;border-radius:8px;background:transparent;"
    "color:var(--text-muted);font:inherit;font-size:.875rem;font-weight:600;cursor:pointer;"
    "text-align:left;touch-action:manipulation}"
)
TOGGLE_CSS_NEW = (
    ".catalog-doc-note-head{display:flex;align-items:center;gap:.4rem;min-width:0;width:100%;box-sizing:border-box}"
    ".catalog-doc-note-toggle{display:flex;align-items:center;gap:.45rem;flex:1 1 auto;min-width:0;width:auto;"
    "min-height:2.25rem;padding:.35rem .7rem;border:0;border-radius:8px;background:transparent;"
    "color:var(--text-muted);font:inherit;font-size:.875rem;font-weight:600;cursor:pointer;"
    "text-align:left;touch-action:manipulation}"
)

MAIN_FLEX_OLD = "body.display-sides #catalogMain,\nbody.catalog-portable #catalogMain,"
MAIN_FLEX_NEW = "body.display-sides #catalogMain,\nbody.display-middle #catalogMain,\nbody.catalog-portable #catalogMain,"

BODY_FLEX_OLD = "body.display-sides #catalogMain>.catalog-body,\nbody.catalog-portable #catalogMain>.catalog-body,"
BODY_FLEX_NEW = (
    "body.display-sides #catalogMain>.catalog-body,\n"
    "body.display-middle #catalogMain>.catalog-body,\n"
    "body.catalog-portable #catalogMain>.catalog-body,"
)

CARDMIN_OLD = (
    "body.has-card-min-dock.display-sides #catalogMain,\n"
    "body.has-card-min-dock.catalog-portable #catalogMain{padding-bottom:0!important}"
)
CARDMIN_NEW = (
    "body.has-card-min-dock.display-sides #catalogMain,\n"
    "body.has-card-min-dock.display-middle #catalogMain,\n"
    "body.has-card-min-dock.catalog-portable #catalogMain{padding-bottom:0!important}"
)

DOCK_SEL_OLD = """body.display-sides #catalogMain>#catalogDocNote,
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
}"""
DOCK_SEL_NEW = """body.display-sides #catalogMain>#catalogDocNote:not(.is-embedded),
body.display-sides #catalogMain>.catalog-doc-note:not(.is-embedded),
body.display-middle #catalogMain>#catalogDocNote:not(.is-embedded),
body.catalog-portable #catalogMain>#catalogDocNote:not(.is-embedded),
body.catalog-portable #catalogMain>.catalog-doc-note:not(.is-embedded){
  flex:0 0 auto!important;margin:0!important;width:auto!important;max-width:none!important;
  align-self:stretch!important;order:9;z-index:14;box-sizing:border-box;
  border-radius:8px 8px 0 0;max-height:min(42dvh,18rem);overflow:hidden;
  padding-bottom:env(safe-area-inset-bottom,0px)
}
.catalog-doc-note:not(.is-collapsed):not(.is-embedded) .catalog-doc-note-body{
  max-height:min(36dvh,16rem);overflow-x:hidden;overflow-y:auto;-webkit-overflow-scrolling:touch
}
/* fix-DOC-NOTE-EMBED: About in-flow with cards; no second bottom dock */
#catalogDocNote.is-embedded,
#catalogMain .catalog-body>#catalogDocNote,
body.display-sides #catalogMain .catalog-body>#catalogDocNote,
body.display-middle #catalogMain .catalog-body>#catalogDocNote,
body.catalog-portable #catalogMain .catalog-body>#catalogDocNote{
  flex:0 0 auto!important;order:0;margin:.75rem 0 .65rem!important;width:auto!important;max-width:none!important;
  align-self:stretch!important;position:static!important;max-height:none!important;overflow:visible;
  border-radius:8px;z-index:auto;padding-bottom:0
}
#catalogDocNote.is-embedded:not(.is-collapsed) .catalog-doc-note-body{
  max-height:none!important;overflow:visible!important
}
.catalog-doc-note-embed{flex:0 0 auto;margin-left:auto}
"""

FILL_NOTE_CSS_OLD = """  body.catalog-portable.index-fill-doc #catalogDocNote,
  body.catalog-portable.index-fill-doc #catalogMain>.catalog-doc-note{
    flex:0 0 auto!important;margin:0!important
  }"""
FILL_NOTE_CSS_NEW = """  body.catalog-portable.index-fill-doc #catalogMain>#catalogDocNote:not(.is-embedded),
  body.catalog-portable.index-fill-doc #catalogMain>.catalog-doc-note:not(.is-embedded){
    flex:0 0 auto!important;margin:0!important
  }
  body.catalog-portable.index-fill-doc.doc-note-embedded #catalogIndex:not(.is-embedded):not(.is-collapsed){
    margin-bottom:4px!important
  }"""

FILL_JS_OLD = """    if(note){
      note.style.setProperty('flex','0 0 auto','important');
      note.style.setProperty('margin','0','important');
    }"""
FILL_JS_NEW = """    if(note&&!note.classList.contains('is-embedded')){
      note.style.setProperty('flex','0 0 auto','important');
      note.style.setProperty('margin','0','important');
    }else if(note){
      ['flex','margin'].forEach(function(p){note.style.removeProperty(p);});
    }"""

BTN_OLD = ".catalog-index-embed,.layout-restore-defaults"
BTN_NEW = ".catalog-index-embed,.catalog-doc-note-embed,.layout-restore-defaults"

MARKER = "fix-DOC-NOTE-EMBED"


def once(text: str, old: str, new: str, label: str, name: str, optional: bool = False) -> str:
    n = text.count(old)
    if n == 1:
        return text.replace(old, new, 1)
    if n == 0 and optional:
        return text
    raise SystemExit(f"{name}: {label} count={n} expected 1")


def patch(path: Path) -> None:
    raw = path.read_bytes()
    orig_size = len(raw)
    text = raw.decode("utf-8")
    name = path.name
    if not text.strip().endswith("</html>"):
        raise SystemExit(f"{name}: missing </html> before patch")

    if MARKER not in text:
        text = once(text, TOGGLE_CSS_OLD, TOGGLE_CSS_NEW, "toggle-css", name)
        text = once(text, MAIN_FLEX_OLD, MAIN_FLEX_NEW, "main-flex", name)
        text = once(text, CARDMIN_OLD, CARDMIN_NEW, "cardmin", name)
        text = once(text, BODY_FLEX_OLD, BODY_FLEX_NEW, "body-flex", name)
        text = once(text, DOCK_SEL_OLD, DOCK_SEL_NEW, "dock-sel", name)
        text = once(text, FILL_NOTE_CSS_OLD, FILL_NOTE_CSS_NEW, "fill-note-css", name, optional=True)
        text = once(text, BTN_OLD, BTN_NEW, "btn-center", name)
        text = once(text, ASIDE_OLD, ASIDE_NEW, "aside-html", name)
        text = once(text, KEY_OLD, KEY_NEW, "pref-js", name)
        text = once(text, INNER_OLD, INNER_NEW, "innerhtml", name)
        text = once(text, APPLY_OLD, APPLY_NEW, "apply-pref", name)
        text = once(text, PARK_OLD, PARK_NEW, "park", name)
        text = once(text, INSET_OLD, INSET_NEW, "inset", name)
        text = once(text, FILL_JS_OLD, FILL_JS_NEW, "fill-js", name, optional=True)

    if MARKER not in text:
        raise SystemExit(f"{name}: embed CSS marker missing after patch")
    if "function toggleDocNoteEmbed(" not in text:
        raise SystemExit(f"{name}: toggleDocNoteEmbed missing")
    if 'id="catalogDocNoteEmbed"' not in text:
        raise SystemExit(f"{name}: catalogDocNoteEmbed missing")
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
        "embed",
        MARKER in text,
        "btn",
        text.count('id="catalogDocNoteEmbed"'),
    )


def main() -> None:
    for p in FILES:
        if not p.exists():
            raise SystemExit(f"missing {p}")
        patch(p)


if __name__ == "__main__":
    main()
