#!/usr/bin/env python3
"""
Replace the note-view toggle BUTTON (which sat below the PATH buttons)
with:
1. A small non-interactive indicator badge at the top-left corner of
   the card (visible whenever a note is saved; hidden in the true
   fullscreen overlay).
2. A swipe gesture on the description panel: swipe left shows the
   saved note, swipe right shows the library's own description again.
   (Desktop pointer drag works the same way for testing without touch.)
"""
import re

FILES = [
    "public/catalogs/DS-CATALOG.html",
    "public/catalogs/DS-CATALOG-portable.html",
    "public/catalogs/KONTAKT-CATALOG.html",
    "public/catalogs/KONTAKT-CATALOG-portable.html",
]

ROW_RE = re.compile(
    r'<div class="note-view-row"><button type="button" class="note-view-btn" hidden '
    r'aria-label="Toggle my note in description" aria-pressed="false" '
    r'onclick="event\.preventDefault\(\);event\.stopPropagation\(\);'
    r'window\.toggleNoteView\(this\)">&#x1F4AC;</button></div>'
)

# Re-add a non-interactive indicator right after the card-chrome-end row
# (top area of the card), so it renders at the top-left corner.
CHROME_END_RE = re.compile(r'(<div class="card-chrome card-chrome-end">.*?</div>)', re.S)
BADGE_TL = '<span class="note-badge-tl" hidden pointer-events="none" title="Has a saved note" aria-label="Has a saved note">&#x1F4AC;</span>'

OLD_BTN_CSS = (
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

NEW_BADGE_CSS = (
    " .note-badge-tl{display:none;position:absolute;top:.5rem;left:.5rem;z-index:3;"
    "width:1.75rem;height:1.75rem;min-width:1.75rem;padding:0;align-items:center;"
    "justify-content:center;font-size:1rem;font-weight:400;line-height:1;"
    "background:var(--accent-instrument-bg);color:var(--accent-instrument);"
    "border:1px solid var(--accent-instrument);border-radius:6px;pointer-events:none}\n"
    " .note-badge-tl.has-note{display:inline-flex}\n"
    " .entry.highlight .note-badge-tl{display:none!important}"
)

OLD_SYNC = """window.toggleNoteView=function(btn){
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

NEW_SYNC = """window.setDescView=function(el,view){
  if(!el)return;
  var name=entryName(el);
  var hasNote=!!String(notesMap[name]||'').replace(/^\\s+|\\s+$/g,'');
  if(view==='note'&&!hasNote)return;
  el.dataset.descView=view;
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
  var tlBadge=el.querySelector('.note-badge-tl');
  if(tlBadge){
    tlBadge.hidden=!note;
    tlBadge.classList.toggle('has-note',!!note);
    tlBadge.title=note?(viewingNote?'Showing my note \\u2013 swipe right on the description for the library description':'Has a saved note \\u2013 swipe left on the description to view it'):'Has a saved note';
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

# Bind the swipe/drag gesture once, appended right after syncAllMeta(); call.
OLD_BOOT = "syncAllMeta();"
NEW_BOOT = """syncAllMeta();
(function(){
  var startX=0,startY=0,swipeEntry=null,dragging=false;
  function begin(x,y,panel){startX=x;startY=y;swipeEntry=panel.closest('.entry');dragging=true;}
  function finish(x,y){
    if(!dragging||!swipeEntry){dragging=false;return;}
    var dx=x-startX,dy=y-startY;
    if(Math.abs(dx)>40&&Math.abs(dx)>Math.abs(dy)*1.5){
      if(typeof window.setDescView==='function')window.setDescView(swipeEntry,dx<0?'note':'orig');
    }
    dragging=false;swipeEntry=null;
  }
  document.addEventListener('touchstart',function(e){
    var panel=e.target&&e.target.closest?e.target.closest('.summary-panel'):null;
    if(!panel)return;
    var t=e.touches&&e.touches[0];if(!t)return;
    begin(t.clientX,t.clientY,panel);
  },{passive:true});
  document.addEventListener('touchend',function(e){
    if(!dragging)return;
    var t=e.changedTouches&&e.changedTouches[0];if(!t)return;
    finish(t.clientX,t.clientY);
  },{passive:true});
  document.addEventListener('pointerdown',function(e){
    if(e.pointerType==='touch')return;
    var panel=e.target&&e.target.closest?e.target.closest('.summary-panel'):null;
    if(!panel)return;
    begin(e.clientX,e.clientY,panel);
  });
  document.addEventListener('pointerup',function(e){
    if(e.pointerType==='touch'||!dragging)return;
    finish(e.clientX,e.clientY);
  });
})();"""


def main():
    for path in FILES:
        txt = open(path, encoding="utf-8").read()

        txt, n_row = ROW_RE.subn("", txt)
        txt, n_badge = CHROME_END_RE.subn(r"\1" + BADGE_TL, txt)

        css_ok = OLD_BTN_CSS in txt
        if css_ok:
            txt = txt.replace(OLD_BTN_CSS, NEW_BADGE_CSS, 1)

        sync_ok = OLD_SYNC in txt
        if sync_ok:
            txt = txt.replace(OLD_SYNC, NEW_SYNC, 1)

        boot_n = txt.count(OLD_BOOT)
        txt = txt.replace(OLD_BOOT, NEW_BOOT, 1)

        open(path, "w", encoding="utf-8").write(txt)
        print(f"{path}: rows_removed={n_row} badges_added={n_badge} css={css_ok} sync={sync_ok} boot_patched={boot_n>0}")


if __name__ == "__main__":
    main()
