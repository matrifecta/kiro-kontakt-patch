#!/usr/bin/env python3
"""
Final pass on the note indicator:
1. Remove the swipe-gesture binding (it fought with normal card clicks).
2. Bring back a real clickable toggle button (.note-view-btn), styled
   exactly like the other card chrome buttons (fav-btn's look/size),
   sitting in the bottom row immediately left of the Favorite button
   with a matching gap.
3. Widen card-actions' reserved gutter to fit both buttons.
"""

FILES = [
    "public/catalogs/DS-CATALOG.html",
    "public/catalogs/DS-CATALOG-portable.html",
    "public/catalogs/KONTAKT-CATALOG.html",
    "public/catalogs/KONTAKT-CATALOG-portable.html",
]

# 1. Remove the swipe IIFE appended after syncAllMeta();
SWIPE_IIFE = """
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

# 2. Markup: replace the non-interactive symbol with a real button.
OLD_BADGE_MARKUP = '<span class="note-badge-tl" hidden pointer-events="none" title="Has a saved note" aria-label="Has a saved note">&#x1F4AC;</span>'
NEW_BTN_MARKUP = (
    '<button type="button" class="note-view-btn" hidden aria-label="Toggle my note in description" '
    'aria-pressed="false" onclick="event.preventDefault();event.stopPropagation();'
    'window.toggleNoteView(this)">&#x1F4AC;</button>'
)

OLD_BADGE_CSS = (
    ' .note-badge-tl{display:none;position:absolute;'
    'right:calc(.5rem + var(--card-chrome-btn) + .4rem);'
    'bottom:calc(.5rem + (var(--card-chrome-btn) - 1.5rem)/2);'
    'top:auto;left:auto;z-index:3;'
    'width:1.5rem;height:1.5rem;min-width:1.5rem;padding:0;align-items:center;'
    'justify-content:center;font-size:.875rem;font-weight:400;line-height:1;'
    'background:var(--accent-instrument-bg);color:var(--accent-instrument);'
    'border:1px solid var(--accent-instrument);border-radius:6px;pointer-events:none}\n'
    ' .note-badge-tl.has-note{display:inline-flex}\n'
    ' .entry.highlight .note-badge-tl{display:none!important}'
)

NEW_BTN_CSS = (
    ' .note-view-btn{display:none;position:absolute;'
    'right:calc(.5rem + var(--card-chrome-btn) + .5rem);bottom:.5rem;top:auto;left:auto;z-index:3;'
    'box-sizing:border-box;width:var(--card-chrome-btn);height:var(--card-chrome-btn);'
    'min-width:var(--card-chrome-btn);min-height:var(--card-chrome-btn);'
    'align-items:center;justify-content:center;padding:0;'
    'background:var(--bg-surface);color:var(--text-muted);border:1px solid var(--border);'
    'border-radius:8px;cursor:pointer;touch-action:manipulation;font-size:1.25rem;line-height:1}\n'
    ' .note-view-btn.has-note{display:inline-flex}\n'
    ' .note-view-btn.has-note:hover{color:var(--accent-instrument);border-color:var(--accent-instrument)}\n'
    ' .note-view-btn.is-active{background:var(--accent-note);color:#fff;border-color:var(--accent-note)}\n'
    ' .entry.highlight .note-view-btn{display:none!important}'
)

OLD_PADDING = " .entry:not(.highlight) .card-actions{padding-right:calc(.5rem + var(--card-chrome-btn) + .4rem + 1.5rem + .4rem)}"
NEW_PADDING = " .entry:not(.highlight) .card-actions{padding-right:calc(.5rem + var(--card-chrome-btn)*2 + .5rem)}"

# 3. JS: syncEntryMeta targets .note-view-btn again + a click handler.
OLD_SYNC_HEAD = "window.setDescView=function(el,view){"
NEW_SYNC_FULL_OLD = """window.setDescView=function(el,view){
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

NEW_SYNC_FULL_NEW = """window.toggleNoteView=function(btn){
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


def main():
    for path in FILES:
        txt = open(path, encoding="utf-8").read()

        n_swipe = txt.count(SWIPE_IIFE)
        txt = txt.replace(SWIPE_IIFE, "", 1)

        n_markup = txt.count(OLD_BADGE_MARKUP)
        txt = txt.replace(OLD_BADGE_MARKUP, NEW_BTN_MARKUP)

        css_ok = OLD_BADGE_CSS in txt
        if css_ok:
            txt = txt.replace(OLD_BADGE_CSS, NEW_BTN_CSS, 1)

        pad_ok = OLD_PADDING in txt
        if pad_ok:
            txt = txt.replace(OLD_PADDING, NEW_PADDING, 1)

        sync_ok = NEW_SYNC_FULL_OLD in txt
        if sync_ok:
            txt = txt.replace(NEW_SYNC_FULL_OLD, NEW_SYNC_FULL_NEW, 1)

        open(path, "w", encoding="utf-8").write(txt)
        print(f"{path}: swipe_removed={n_swipe>0} markup={n_markup} css={css_ok} padding={pad_ok} sync={sync_ok}")


if __name__ == "__main__":
    main()
