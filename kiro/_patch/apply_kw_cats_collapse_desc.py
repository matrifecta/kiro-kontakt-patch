#!/usr/bin/env python3
"""KW cats under ⋯ on portable; restore desc/path FS; replace auto patch-lock with Collapse."""
from pathlib import Path

ROOT = Path('/home/phnx/kiro-kontakt-patch/public/catalogs')
FILES = [
    ROOT / 'KONTAKT-CATALOG-portable.html',
    ROOT / 'DS-CATALOG-portable.html',
    ROOT / 'KONTAKT-CATALOG.html',
    ROOT / 'DS-CATALOG.html',
]

COLLAPSE_FN = r'''
function collapseAllPatchTrees(){
  window._collapsingPatches=true;
  var n=0;
  try{
    document.querySelectorAll('.entry details.patches, .entry details.grp').forEach(function(d){
      if(d.open){d.open=false;n++;}
    });
  }finally{window._collapsingPatches=false;}
  if(typeof scheduleEqualizeCardRows==='function')scheduleEqualizeCardRows();
  // #region agent log
  try{
    fetch('http://127.0.0.1:7529/ingest/1cf46354-1d61-4c80-bd72-a340f1db1b51',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'c00e3e'},body:JSON.stringify({sessionId:'c00e3e',runId:'post-fix',hypothesisId:'C',location:'catalog:collapseAllPatchTrees',message:'collapse all patch trees',data:{n:n},timestamp:Date.now()})}).catch(function(){});
  }catch(eDbgC){}
  // #endregion
}
window.collapseAllPatchTrees=collapseAllPatchTrees;
'''

KW_CSS = '''
/* fix-KW-CATS-COLLAPSE: portable KW cats under toolbar ⋯; Collapse next to Customize */
@media all{
  body.catalog-portable:not(.kw-cats-open) #catSwitch{display:none!important}
  body.catalog-portable.kw-cats-open #kwStripMorePop:not([hidden]){
    display:flex!important;flex-direction:row!important;flex-wrap:wrap!important;
    flex:1 1 100%!important;width:100%!important;max-width:100%!important;
    order:99!important;position:static!important;inset:auto!important;
    max-height:none!important;overflow:visible!important;
    background:transparent!important;box-shadow:none!important;
    padding:.2rem 0;gap:.28rem;margin:.15rem 0 0
  }
  body.catalog-portable.kw-cats-open #kwStripMorePop #catSwitch,
  body.catalog-portable.kw-cats-open #catSwitch{
    display:flex!important;flex-wrap:wrap!important;align-content:flex-start;
    width:100%!important;max-width:100%!important;margin:0!important;
    flex:1 1 100%!important
  }
}
'''

BTN_CSS = '''
.collapse-cards-btn{flex-shrink:0;box-sizing:border-box;min-height:2.25rem;background:transparent;border:1px solid var(--border);color:var(--text-muted);border-radius:4px;padding:0 .625rem;font-size:.875rem;cursor:pointer;touch-action:manipulation;white-space:nowrap}
.hdr-layout-btns .collapse-cards-btn{min-height:2.25rem}
.entry:not(.highlight) .summary-panel,.entry:not(.highlight) .path{cursor:pointer}
'''

def once(s, old, new, label):
    if old not in s:
        print('MISS', label)
        return s
    if s.count(old) != 1:
        print('MULTI', s.count(old), label)
        return s
    print('OK', label)
    return s.replace(old, new, 1)

def patch(path: Path):
    s = path.read_text(encoding='utf-8')
    portable = 'portable' in path.name
    print('====', path.name)

    s = once(s,
        "  collapseInactivePatchTrees('viewed');\n}",
        "  /* auto-lock removed: use collapseAllPatchTrees */\n}",
        'rememberViewed')

    s = once(s,
        "  if(typeof collapseInactivePatchTrees==='function')collapseInactivePatchTrees('clear');\n}",
        "}",
        'clearSelect')

    s = once(s,
        "  if(details.open&&typeof rememberViewed==='function')rememberViewed(entry);\n"
        "  else if(typeof collapseInactivePatchTrees==='function')collapseInactivePatchTrees('toggle');\n",
        "  if(details.open&&typeof rememberViewed==='function')rememberViewed(entry);\n",
        'toggle-no-autolock')

    s = once(s,
        "if(typeof collapseInactivePatchTrees==='function')collapseInactivePatchTrees('boot');\n",
        "",
        'boot-collapse')

    s = once(s,
        "window.collapseInactivePatchTrees=collapseInactivePatchTrees;\n",
        "window.collapseInactivePatchTrees=collapseInactivePatchTrees;\n"+COLLAPSE_FN,
        'collapseAll-fn')

    s = once(s,
        '    if(e.target.closest(\'.summary-panel .desc\')){activateDesc(entry);return;}\n',
        '    if(e.target.closest(\'.summary-panel,.summary-panel .desc\')){activateDesc(entry);e.preventDefault();e.stopPropagation();return;}\n',
        'desc-click')

    s = once(s,
        "  if(document.body.classList.contains('gallery-open')){\n",
        "  if(document.body.classList.contains('desc-focus-open')){\n"
        "    if(e.target.closest('.desc-focus-zoom,.desc-focus-text'))return;\n"
        "    closeDescFocus();e.preventDefault();return;\n"
        "  }\n"
        "  if(document.body.classList.contains('path-focus-open')){\n"
        "    if(e.target.closest('.path-focus-zoom,.path-focus-text'))return;\n"
        "    closePathFocus();e.preventDefault();return;\n"
        "  }\n"
        "  if(document.body.classList.contains('gallery-open')){\n",
        'focus-clickaway')

    s = once(s,
        "  if(e.target.closest('#searchModal,#cardMinDock,.card-min-pill,.card-search-embed,.search-chrome,.search-split,.search-height,.ac-height,.ac-width,.kw-shade-height,.search-ac-shell,.filter-wrap,.search-strip,.search-autocomplete,.search-active-pills,.top,.tap-add-btn,.clear-miss-btn,.layout-edit-btn,#kwbar,.kw,.mode-switch,.cat-switch,.fav-btn,.note-pop,.note-balloon,.preview-back,.hl-min')) return;\n",
        "  if(e.target.closest('#searchModal,#cardMinDock,.card-min-pill,.card-search-embed,.search-chrome,.search-split,.search-height,.ac-height,.ac-width,.kw-shade-height,.search-ac-shell,.filter-wrap,.search-strip,.search-autocomplete,.search-active-pills,.top,.tap-add-btn,.clear-miss-btn,.layout-edit-btn,.collapse-cards-btn,#kwbar,.kw,.mode-switch,.cat-switch,.fav-btn,.note-pop,.note-balloon,.preview-back,.hl-min')) return;\n",
        'click-ignore-collapse')

    s = once(s,
        '<button type="button" class="layout-edit-btn" id="layoutEditBtn"',
        '<button type="button" class="collapse-cards-btn" id="collapseCardsBtn" title="Collapse open patch lists and even card sizes" onclick="event.preventDefault();event.stopPropagation();if(typeof collapseAllPatchTrees===\'function\')collapseAllPatchTrees()">Collapse</button>'
        '<button type="button" class="layout-edit-btn" id="layoutEditBtn"',
        'html-collapse-btn')

    s = once(s,
        "  var edit=document.getElementById('layoutEditBtn');\n"
        "  if(edit&&edit.parentElement!==host)host.appendChild(edit);\n",
        "  var edit=document.getElementById('layoutEditBtn');\n"
        "  var tidy=document.getElementById('collapseCardsBtn');\n"
        "  if(!tidy){\n"
        "    tidy=document.createElement('button');\n"
        "    tidy.type='button';tidy.id='collapseCardsBtn';tidy.className='collapse-cards-btn';\n"
        "    tidy.textContent='Collapse';\n"
        "    tidy.title='Collapse open patch lists and even card sizes';\n"
        "    tidy.addEventListener('click',function(e){e.preventDefault();e.stopPropagation();if(typeof collapseAllPatchTrees==='function')collapseAllPatchTrees();});\n"
        "  }\n"
        "  if(edit&&edit.parentElement!==host)host.appendChild(edit);\n"
        "  if(tidy&&edit){\n"
        "    if(tidy.parentElement!==edit.parentElement||tidy.nextElementSibling!==edit)edit.parentElement.insertBefore(tidy,edit);\n"
        "  }else if(tidy&&tidy.parentElement!==host)host.insertBefore(tidy,host.firstChild);\n",
        'ensure-collapse-btn')

    s = once(s,
        ' .layout-edit-btn{flex-shrink:0;',
        ' .collapse-cards-btn,.layout-edit-btn{flex-shrink:0;',
        'css-btn-share')

    # If the layout-edit-btn rule didn't have a leading space variant, try without
    if '.collapse-cards-btn,.layout-edit-btn{flex-shrink:0;' not in s:
        s = once(s,
            '.layout-edit-btn{flex-shrink:0;',
            '.collapse-cards-btn,.layout-edit-btn{flex-shrink:0;',
            'css-btn-share2')

    if portable:
        s = once(s,
            "function toggleKwStripMore(){\n"
            "  var pop=document.getElementById('kwStripMorePop');var btn=document.getElementById('kwStripMore');\n"
            "  var top=document.getElementById('filterTop');\n"
            "  if(!pop||!btn)return;\n"
            "  var open=pop.hasAttribute('hidden');\n"
            "  var hdr=document.getElementById('hdrMorePop');\n"
            "  if(hdr){hdr.setAttribute('hidden','');var hb=document.getElementById('hdrMoreBtn');if(hb)hb.setAttribute('aria-expanded','false');}\n"
            "  if(!open){pop.setAttribute('hidden','');btn.setAttribute('aria-expanded','false');return;}\n"
            "  if(top&&pop.parentElement!==top)top.appendChild(pop);\n"
            "  pop.innerHTML='';\n"
            "  if(typeof portableMoreRowAdd!=='function'){\n"
            "    window.portableMoreRowAdd=function(p,label,fn,aria){var b=document.createElement('button');b.type='button';b.textContent=label;if(aria)b.setAttribute('aria-label',aria);b.addEventListener('click',function(e){e.preventDefault();e.stopPropagation();fn();});p.appendChild(b);};\n"
            "  }\n"
            "  portableMoreRowAdd(pop,'Tap',function(){if(typeof toggleTapToAdd==='function')toggleTapToAdd();},'Tap to add');\n"
            "  portableMoreRowAdd(pop,'History',function(){var h=document.getElementById('searchHistory');if(h)h.click();},'History');\n"
            "  portableMoreRowAdd(pop,'Fullscreen',function(){if(typeof toggleKwFullscreen==='function')toggleKwFullscreen();},'Fullscreen Keywords');\n"
            "  pop.removeAttribute('hidden');btn.setAttribute('aria-expanded','true');\n"
            "  btn.style.setProperty('display','inline-flex','important');\n",
            "function toggleKwStripMore(){\n"
            "  var pop=document.getElementById('kwStripMorePop');var btn=document.getElementById('kwStripMore');\n"
            "  var top=document.getElementById('filterTop');\n"
            "  var cs=document.getElementById('catSwitch');\n"
            "  var fp=document.getElementById('filterPanel');\n"
            "  var kb=document.getElementById('kwbar');\n"
            "  if(!pop||!btn)return;\n"
            "  var open=pop.hasAttribute('hidden');\n"
            "  var hdr=document.getElementById('hdrMorePop');\n"
            "  if(hdr){hdr.setAttribute('hidden','');var hb=document.getElementById('hdrMoreBtn');if(hb)hb.setAttribute('aria-expanded','false');}\n"
            "  if(!open){\n"
            "    pop.setAttribute('hidden','');\n"
            "    btn.setAttribute('aria-expanded','false');\n"
            "    document.body.classList.remove('kw-cats-open');\n"
            "    if(cs&&fp){if(kb)fp.insertBefore(cs,kb);else fp.appendChild(cs);}\n"
            "    if(typeof portableEnsureScrollMenus==='function')portableEnsureScrollMenus();\n"
            "    // #region agent log\n"
            "    fetch('http://127.0.0.1:7529/ingest/1cf46354-1d61-4c80-bd72-a340f1db1b51',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'c00e3e'},body:JSON.stringify({sessionId:'c00e3e',runId:'post-fix',hypothesisId:'KW',location:'portable:toggleKwStripMore',message:'kw cats close',data:{open:false,kbH:kb?kb.clientHeight:0},timestamp:Date.now()})}).catch(function(){});\n"
            "    // #endregion\n"
            "    return;\n"
            "  }\n"
            "  if(top&&pop.parentElement!==top)top.appendChild(pop);\n"
            "  pop.innerHTML='';\n"
            "  if(cs)pop.appendChild(cs);\n"
            "  pop.removeAttribute('hidden');\n"
            "  btn.setAttribute('aria-expanded','true');\n"
            "  document.body.classList.add('kw-cats-open');\n"
            "  btn.style.setProperty('display','inline-flex','important');\n"
            "  if(typeof portableEnsureScrollMenus==='function')portableEnsureScrollMenus();\n"
            "  // #region agent log\n"
            "  fetch('http://127.0.0.1:7529/ingest/1cf46354-1d61-4c80-bd72-a340f1db1b51',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'c00e3e'},body:JSON.stringify({sessionId:'c00e3e',runId:'post-fix',hypothesisId:'KW',location:'portable:toggleKwStripMore',message:'kw cats open',data:{open:true,csInPop:!!(cs&&pop.contains(cs)),kbH:kb?kb.clientHeight:0},timestamp:Date.now()})}).catch(function(){});\n"
            "  // #endregion\n",
            'kw-strip-more')

        s = once(s,
            "  phoneMoreAdd(pop,document.body.classList.contains('layout-edit')?'Done':'Customize',function(){if(typeof toggleLayoutEdit==='function')toggleLayoutEdit();},document.body.classList.contains('layout-edit')?'Done arranging':'Customize layout');\n",
            "  phoneMoreAdd(pop,'Collapse',function(){if(typeof collapseAllPatchTrees==='function')collapseAllPatchTrees();},'Collapse open patch lists');\n"
            "  phoneMoreAdd(pop,document.body.classList.contains('layout-edit')?'Done':'Customize',function(){if(typeof toggleLayoutEdit==='function')toggleLayoutEdit();},document.body.classList.contains('layout-edit')?'Done arranging':'Customize layout');\n",
            'hdr-more-collapse')

        if '</style>' in s and 'fix-KW-CATS-COLLAPSE' not in s:
            s = s.replace('</style>', KW_CSS + '\n</style>', 1)
            print('OK kw-css')
        elif 'fix-KW-CATS-COLLAPSE' in s:
            print('SKIP kw-css already')
        else:
            print('MISS kw-css')

    if 'entry:not(.highlight) .summary-panel,.entry:not(.highlight) .path{cursor:pointer}' not in s:
        if '</style>' in s:
            s = s.replace('</style>', BTN_CSS + '\n</style>', 1)
            print('OK btn-css')
        else:
            print('MISS btn-css')
    else:
        print('SKIP btn-css already')

    path.write_text(s, encoding='utf-8')
    print('wrote', path.name, len(s))

def main():
    for p in FILES:
        patch(p)

if __name__ == '__main__':
    main()
