#!/usr/bin/env python3
"""
Replace the passive "has a note" badge with a real toggle button placed
in its own row directly below the 3 PATH icon buttons (centered, same
gap as used between those buttons). Clicking it switches the
description panel between showing the library's own description and
showing only the user's saved note (never both at once, so card height
never grows because of a note). Works the same in grid and fullscreen.
"""
import re

FILES = [
    "public/catalogs/DS-CATALOG.html",
    "public/catalogs/DS-CATALOG-portable.html",
    "public/catalogs/KONTAKT-CATALOG.html",
    "public/catalogs/KONTAKT-CATALOG-portable.html",
]

OLD_BADGE_IN_PATH = '<div class="path"><span class="un-badge" hidden title="User notes" aria-label="User notes">&#x1F4AC;</span><b>'
NEW_PATH_OPEN = '<div class="path"><b>'

PATH_END = '[open folder]</a></div>'
NOTE_VIEW_ROW = (
    '<div class="note-view-row">'
    '<button type="button" class="note-view-btn" hidden aria-label="Toggle my note in description" '
    'aria-pressed="false" onclick="event.preventDefault();event.stopPropagation();'
    'window.toggleNoteView(this)">&#x1F4AC;</button></div>'
)

OLD_BADGE_CSS = (
    " .un-badge{display:none;order:-1;flex:0 0 auto;align-self:center;"
    "width:1.5rem;height:1.5rem;min-width:1.5rem;padding:0;align-items:center;"
    "justify-content:center;font-size:.875rem;font-weight:400;letter-spacing:0;line-height:1;"
    "background:var(--accent-instrument-bg);color:var(--accent-instrument);"
    "border:1px solid var(--accent-instrument);border-radius:6px;pointer-events:none}\n"
    " .un-badge.has-note{display:inline-flex}\n"
    " .entry.highlight .un-badge{display:none!important}"
)

NEW_BTN_CSS = (
    " .note-view-row{display:flex;justify-content:center;align-items:center;width:100%;"
    "margin-top:clamp(.35rem,2.5vw,.65rem)}\n"
    " .note-view-btn{display:none;box-sizing:border-box;width:1.75rem;height:1.75rem;min-width:1.75rem;"
    "padding:0;align-items:center;justify-content:center;font-size:.9375rem;font-weight:400;"
    "background:var(--bg-surface);color:var(--text-muted);border:1px solid var(--border);"
    "border-radius:6px;cursor:pointer;touch-action:manipulation;line-height:1}\n"
    " .note-view-btn.has-note{display:inline-flex}\n"
    " .note-view-btn.has-note:hover{color:var(--accent-instrument);border-color:var(--accent-instrument)}\n"
    " .note-view-btn.is-active{background:var(--accent-note);color:#fff;border-color:var(--accent-note)}"
)

OLD_SYNC = """function syncEntryMeta(el){
  if(!el)return;
  var name=entryName(el);
  var fav=!!favSet[name];
  var note=String(notesMap[name]||'').replace(/^\\s+|\\s+$/g,'');
  syncNoteKw(el,note);
  el.classList.toggle('is-fav',fav);
  paintFavBtn(el.querySelector('.fav-btn'),fav);
  var badge=el.querySelector('.un-badge');
  if(badge){badge.hidden=!note;badge.classList.toggle('has-note',!!note);}
  var nt=el.querySelector('.note-text');
  if(nt){nt.hidden=true;nt.classList.remove('has-note');nt.textContent='';}
  var dsc=el.querySelector('.desc');
  if(dsc){
    if(dsc.dataset.orig===undefined)dsc.dataset.orig=dsc.textContent;
    var orig=dsc.dataset.orig;
    var isPlaceholder=(orig.replace(/^\\s+|\\s+$/g,'')===NO_DESC_TEXT);
    var escOrig=escHtml(orig);
    var escNote=note?escHtml(note).replace(/\\n/g,'<br>'):'';
    var html='';
    if(!(isPlaceholder&&note))html=escOrig;
    if(note)html+=(html?'<hr class="desc-note-sep">':'')+'<span class="desc-user-note">'+escNote+'</span>';
    dsc.innerHTML=html;
  }
}"""

NEW_SYNC = """window.toggleNoteView=function(btn){
  var el=btn&&btn.closest?btn.closest('.entry'):null;
  if(!el)return;
  var name=entryName(el);
  var hasNote=!!String(notesMap[name]||'').replace(/^\\s+|\\s+$/g,'');
  if(!hasNote)return;
  el.dataset.descView=(el.dataset.descView==='note')?'orig':'note';
  syncEntryMeta(el);
};
function syncEntryMeta(el){
  if(!el)return;
  var name=entryName(el);
  var fav=!!favSet[name];
  var note=String(notesMap[name]||'').replace(/^\\s+|\\s+$/g,'');
  syncNoteKw(el,note);
  el.classList.toggle('is-fav',fav);
  paintFavBtn(el.querySelector('.fav-btn'),fav);
  if(!note)el.dataset.descView='orig';
  var viewingNote=!!note&&el.dataset.descView==='note';
  var nvBtn=el.querySelector('.note-view-btn');
  if(nvBtn){
    nvBtn.hidden=!note;
    nvBtn.classList.toggle('has-note',!!note);
    nvBtn.classList.toggle('is-active',viewingNote);
    nvBtn.setAttribute('aria-pressed',viewingNote?'true':'false');
    nvBtn.title=viewingNote?'Show library description':'Show my note';
  }
  var nt=el.querySelector('.note-text');
  if(nt){nt.hidden=true;nt.classList.remove('has-note');nt.textContent='';}
  var dsc=el.querySelector('.desc');
  if(dsc){
    if(dsc.dataset.orig===undefined)dsc.dataset.orig=dsc.textContent;
    var orig=dsc.dataset.orig;
    var html=viewingNote?('<span class="desc-user-note">'+escHtml(note).replace(/\\n/g,'<br>')+'</span>'):escHtml(orig);
    dsc.innerHTML=html;
  }
}"""

OLD_EXCLUDE_1 = "if(e.target.closest('a,.hl-close,.hl-min,.preview-back,.kw,input,select,textarea,summary,.search-popup-btn,.search-link,.fav-btn,.note-balloon,.note-pop,.un-badge,.note-save,.note-cancel,.fs-btn,.card-search-embed,#cardMinDock')) return;"
NEW_EXCLUDE_1 = "if(e.target.closest('a,.hl-close,.hl-min,.preview-back,.kw,input,select,textarea,summary,.search-popup-btn,.search-link,.fav-btn,.note-balloon,.note-pop,.note-view-btn,.note-save,.note-cancel,.fs-btn,.card-search-embed,#cardMinDock')) return;"


def main():
    for path in FILES:
        txt = open(path, encoding="utf-8").read()

        n_undo = txt.count(OLD_BADGE_IN_PATH)
        txt = txt.replace(OLD_BADGE_IN_PATH, NEW_PATH_OPEN)

        n_row = txt.count(PATH_END)
        txt = txt.replace(PATH_END, PATH_END + NOTE_VIEW_ROW)

        css_ok = OLD_BADGE_CSS in txt
        if css_ok:
            txt = txt.replace(OLD_BADGE_CSS, NEW_BTN_CSS, 1)

        sync_ok = OLD_SYNC in txt
        if sync_ok:
            txt = txt.replace(OLD_SYNC, NEW_SYNC, 1)

        excl_ok = OLD_EXCLUDE_1 in txt
        if excl_ok:
            txt = txt.replace(OLD_EXCLUDE_1, NEW_EXCLUDE_1)

        open(path, "w", encoding="utf-8").write(txt)
        print(f"{path}: undo_old_badge={n_undo} rows_added={n_row} css={css_ok} sync={sync_ok} exclude={excl_ok}")


if __name__ == "__main__":
    main()
