#!/usr/bin/env python3
"""Add two chevron toggle buttons to the mobile card-search-embed chrome:

1. A centered ".card-chrome-mid" button in the card's top toolbar (row 1,
   the .card-chrome-start/.card-chrome-end row) that hides/shows the
   second-row embed toolbar (.card-search-chrome: back/reload/mode/fs
   buttons), in both portrait and landscape orientation.
2. A small ".card-chrome-fold" arrow (styled like the existing
   #hdrBarToggle document-header collapse arrow) that hides/shows the
   entire top toolbar (row 1) itself, sticking out of the card's top edge
   when collapsed.

Both buttons only appear while the card-search-embed is open
(body.card-embed-open), scoped to the expanded/preview card
(.entry.highlight or .entry.selected in chosen-preview mode). Idempotent:
safe to re-run.
"""
import re
import sys

FILES = [
    "public/catalogs/DS-CATALOG-portable.html",
    "public/catalogs/KONTAKT-CATALOG-portable.html",
]

CSS_MARK = "/* fix-CARD-EMBED-TOOLBAR-HIDE-v1"
CSS_BLOCK = """/* fix-CARD-EMBED-TOOLBAR-HIDE-v1: centered chevron in the card's top
   toolbar (row 1) hides/shows the card-search-embed second-row toolbar
   (.card-search-chrome); a small edge arrow (like #hdrBarToggle) hides/
   shows the whole top toolbar row. Both only show while the embed is
   open, in portrait and landscape alike. */
.card-chrome-mid{display:none;position:absolute;top:max(var(--card-chrome-inset),env(safe-area-inset-top));left:50%;transform:translateX(-50%);z-index:841;align-items:center}
.card-row2-toggle{box-sizing:border-box;width:var(--card-chrome-btn);height:var(--card-chrome-btn);min-width:var(--card-chrome-btn);min-height:var(--card-chrome-btn);display:inline-flex;align-items:center;justify-content:center;padding:0;background:var(--bg-surface);color:var(--text);border:1px solid var(--border);border-radius:8px;cursor:pointer;touch-action:manipulation;font-size:1.1rem;line-height:1}
.card-row2-toggle:hover{color:var(--accent-instrument);border-color:var(--accent-instrument);background:var(--accent-instrument-bg)}
.card-row2-toggle .toggle-arrow{display:inline-block;transition:transform .2s;font-size:.85rem;line-height:1}
body.card-row2-hidden .card-row2-toggle .toggle-arrow{transform:rotate(180deg)}
body.card-embed-open .entry.highlight .card-chrome-mid,
body.card-embed-open.chosen-preview-open .entry.selected:not(.highlight) .card-chrome-mid{display:flex}
body.card-row2-hidden #cardSearchEmbed .card-search-chrome{display:none!important}
.card-chrome-fold{display:none;position:absolute;left:50%;top:0;transform:translateX(-50%) translateY(-.15rem);z-index:842;box-sizing:border-box;width:2.15rem;height:1.15rem;min-width:2.15rem;min-height:1.15rem;padding:0;margin:0;align-items:center;justify-content:center;border:1px solid var(--border);border-top:0;border-radius:0 0 8px 8px;background:var(--bg-surface);color:var(--text);cursor:pointer;touch-action:manipulation;font:inherit;line-height:1}
.card-chrome-fold:hover{border-color:var(--accent-instrument);color:var(--accent-instrument);background:var(--accent-instrument-bg)}
.card-chrome-fold .toggle-arrow{display:inline-block;transform:rotate(180deg);transition:transform .2s;font-size:.85rem;line-height:1}
body.card-chrome-folded .card-chrome-fold .toggle-arrow{transform:none}
body.card-embed-open .entry.highlight .card-chrome-fold,
body.card-embed-open.chosen-preview-open .entry.selected:not(.highlight) .card-chrome-fold{display:inline-flex}
body.card-chrome-folded .entry.highlight .card-chrome-start,
body.card-chrome-folded .entry.highlight .card-chrome-mid,
body.card-chrome-folded .entry.highlight .card-chrome-end,
body.card-chrome-folded.chosen-preview-open .entry.selected:not(.highlight) .card-chrome-start,
body.card-chrome-folded.chosen-preview-open .entry.selected:not(.highlight) .card-chrome-mid,
body.card-chrome-folded.chosen-preview-open .entry.selected:not(.highlight) .card-chrome-end{display:none!important}
"""

JS_MARK = "function cardChromeEnsureBtns("
JS_BLOCK = """function cardChromeEnsureBtns(entry){
  if(!entry)return;
  var start=entry.querySelector('.card-chrome-start');
  if(!start)return;
  if(!entry.querySelector('.card-chrome-fold')){
    var f=document.createElement('button');
    f.type='button';
    f.className='card-chrome-fold';
    f.setAttribute('aria-label','Hide card toolbar');
    f.setAttribute('aria-pressed','false');
    f.title='Hide toolbar';
    f.innerHTML='<span class="toggle-arrow">&#9660;</span>';
    f.onclick=function(e){e.preventDefault();e.stopPropagation();toggleCardChromeFold();};
    entry.insertBefore(f,start);
  }
  if(!entry.querySelector('.card-chrome-mid')){
    var mid=document.createElement('div');
    mid.className='card-chrome card-chrome-mid';
    var b=document.createElement('button');
    b.type='button';
    b.className='card-row2-toggle';
    b.setAttribute('aria-label','Hide embed toolbar row');
    b.setAttribute('aria-pressed','false');
    b.title='Hide toolbar row';
    b.innerHTML='<span class="toggle-arrow">&#9660;</span>';
    b.onclick=function(e){e.preventDefault();e.stopPropagation();toggleCardRow2();};
    mid.appendChild(b);
    start.parentNode.insertBefore(mid,start.nextSibling);
  }
}
function cardChromeEnsureAllBtns(){document.querySelectorAll('.entry').forEach(cardChromeEnsureBtns);}
function cardChromePrefKey(name){return 'catalog-'+name+'-'+(window.CATALOG_NS||'catalog');}
function syncCardRow2(){
  var hide=document.body.classList.contains('card-row2-hidden');
  document.querySelectorAll('.card-row2-toggle').forEach(function(b){
    b.setAttribute('aria-pressed',hide?'true':'false');
    b.title=hide?'Show toolbar row':'Hide toolbar row';
  });
}
function toggleCardRow2(force){
  var hide=(force===true||force===false)?!!force:!document.body.classList.contains('card-row2-hidden');
  document.body.classList.toggle('card-row2-hidden',hide);
  try{localStorage.setItem(cardChromePrefKey('card-row2-hidden'),hide?'1':'0');}catch(eR2){}
  syncCardRow2();
}
window.toggleCardRow2=toggleCardRow2;
function syncCardChromeFold(){
  var hide=document.body.classList.contains('card-chrome-folded');
  document.querySelectorAll('.card-chrome-fold').forEach(function(b){
    b.setAttribute('aria-pressed',hide?'true':'false');
    b.title=hide?'Show toolbar':'Hide toolbar';
  });
}
function toggleCardChromeFold(force){
  var hide=(force===true||force===false)?!!force:!document.body.classList.contains('card-chrome-folded');
  document.body.classList.toggle('card-chrome-folded',hide);
  try{localStorage.setItem(cardChromePrefKey('card-chrome-folded'),hide?'1':'0');}catch(eCF){}
  syncCardChromeFold();
}
window.toggleCardChromeFold=toggleCardChromeFold;
(function restoreCardChromeToggles(){
  try{
    if(localStorage.getItem(cardChromePrefKey('card-row2-hidden'))==='1')document.body.classList.add('card-row2-hidden');
    if(localStorage.getItem(cardChromePrefKey('card-chrome-folded'))==='1')document.body.classList.add('card-chrome-folded');
  }catch(eRest){}
})();
"""

BOOT_OLD = "    cardMinEnsureAllBtns();\n    cardMinEnsureDock();"
BOOT_NEW = "    cardMinEnsureAllBtns();\n    cardChromeEnsureAllBtns();\n    cardMinEnsureDock();"


def apply_file(path):
    with open(path, "r", encoding="utf-8") as f:
        html = f.read()

    changed = False

    if CSS_MARK not in html:
        # Insert *after* fix-CARD-CHROME-TOP-v1's @media block (which sets
        # display:flex!important on .card-chrome-start/-end at equal
        # specificity) so our display:none!important rule wins the tie by
        # coming later in source order.
        anchor = "/* fix-INDEX-EMBED-FULL-v1"
        idx = html.index(anchor)
        html = html[:idx] + CSS_BLOCK + "\n" + html[idx:]
        changed = True
    else:
        print(f"  (css already applied) {path}")

    if JS_MARK not in html:
        anchor = "function cardMinEnsureBtn(entry){"
        idx = html.index(anchor)
        html = html[:idx] + JS_BLOCK + "\n" + html[idx:]
        changed = True
    else:
        print(f"  (js already applied) {path}")

    if BOOT_OLD in html:
        html = html.replace(BOOT_OLD, BOOT_NEW, 1)
        changed = True
    elif "cardChromeEnsureAllBtns();" not in html:
        print(f"  WARNING: boot anchor not found in {path}", file=sys.stderr)

    if changed:
        with open(path, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"  patched {path}")
    else:
        print(f"  no changes needed {path}")


if __name__ == "__main__":
    import os

    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    for rel in FILES:
        apply_file(os.path.join(root, rel))
