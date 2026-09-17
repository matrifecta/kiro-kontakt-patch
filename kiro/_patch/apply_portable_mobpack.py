#!/usr/bin/env python3
"""Mobile catalog pack: titles, jumps, overlay chrome, KW cats, Index fill, KW FS, Index vs extended card."""
from pathlib import Path
import os, tempfile

ROOT = Path("/home/phnx/kiro-kontakt-patch/public/catalogs")
FILES = [ROOT / "KONTAKT-CATALOG-portable.html", ROOT / "DS-CATALOG-portable.html"]

CSS_TAIL = """
/* fix-MOBPACK-v1: portrait titles centered in notch-to-edge halves */
@media(orientation:portrait){
  body.catalog-portable .catalog-header h1#top{
    display:grid!important;grid-template-columns:minmax(0,1fr) minmax(0,1fr)!important;
    align-items:center;column-gap:max(6.25rem,30vw);width:100%!important;max-width:none!important;
    overflow:visible!important;text-overflow:clip!important;white-space:nowrap
  }
  body.catalog-portable .catalog-header h1#top .hdr-title-lead{
    grid-column:1;justify-self:center;text-align:center;min-width:0;
    padding-left:max(.2rem,env(safe-area-inset-left,0px));padding-right:0
  }
  body.catalog-portable .catalog-header h1#top .hdr-title-tail{
    grid-column:2;justify-self:center;text-align:center;min-width:0;
    padding-right:max(.2rem,env(safe-area-inset-right,0px));padding-left:0
  }
}
/* fix-MOBPACK-v1: KW cats at top of pills window as transparent UI buttons */
body.catalog-portable:not(.kw-cats-open) #catSwitch{display:none!important}
body.catalog-portable.kw-cats-open #catSwitch{
  display:flex!important;flex-wrap:wrap!important;align-content:flex-start;
  width:100%!important;max-width:100%!important;margin:0 0 .35rem!important;
  flex:0 0 auto!important;order:-2;gap:.28rem;padding:.15rem 0;
  background:transparent!important;box-shadow:none!important;border:0!important
}
body.catalog-portable.kw-cats-open #kwStripMorePop{display:none!important}
body.catalog-portable #catSwitch .cat-btn{
  background:transparent!important;border:1px solid var(--border)!important;
  color:var(--text-muted)!important;box-shadow:none!important
}
body.catalog-portable #catSwitch .cat-btn.active{
  background:transparent!important;border-color:var(--accent-instrument)!important;
  color:var(--accent-instrument)!important;font-weight:600
}
body.catalog-portable #catSwitch .cat-btn[data-cat="patch"].active{
  border-color:var(--accent-patch)!important;color:var(--accent-patch)!important
}
/* fix-MOBPACK-v1: Keywords FS keeps ⛶ on the right; drop back arrow */
html body.catalog-portable.kw-fs-open #kwStripFs,
html body.catalog-portable.kw-fs-open #filterTop > #kwStripFs,
html body.catalog-portable.kw-fs-open .kw-fs-btn{
  display:inline-flex!important;visibility:visible!important;opacity:1!important;
  order:99!important;margin-left:auto!important;pointer-events:auto!important
}
html body.catalog-portable.kw-fs-open #kwFsBack,
html body.catalog-portable.kw-fs-open .kw-fs-back{
  display:none!important
}
html body.catalog-portable.kw-fs-open #kwStripHide{
  display:inline-flex!important;visibility:visible!important
}
/* fix-MOBPACK-v1: Window Index fills remaining pane to the screen bottom */
body.catalog-portable.index-fill-doc.index-window-open #catalogIndex:not(.is-embedded):not(.is-collapsed),
html body.catalog-portable.index-fill-doc.index-window-open #catalogIndex:not(.is-embedded):not(.is-collapsed){
  position:relative!important;top:auto!important;left:auto!important;right:auto!important;
  flex:1 1 0%!important;height:auto!important;max-height:none!important;min-height:0!important;
  margin-top:0!important;margin-bottom:4px!important
}
/* fix-MOBPACK-v1: Window Index must not overlay or shove an extended/front card */
html body.catalog-portable:is(.chosen-preview-open,.card-embed-open,.hl-open,.gallery-open,.img-focus-open,.desc-reader-open,.path-reader-open,.desc-focus-open,.path-focus-open) #catalogIndex,
html body.catalog-portable:is(.chosen-preview-open,.card-embed-open,.hl-open,.gallery-open,.img-focus-open,.desc-reader-open,.path-reader-open,.desc-focus-open,.path-focus-open) #catalogMain>#catalogIndex,
html body.catalog-portable.content-window-on:is(.chosen-preview-open,.card-embed-open,.hl-open,.gallery-open,.img-focus-open,.desc-reader-open,.path-reader-open,.desc-focus-open,.path-focus-open) #catalogIndex{
  display:none!important;visibility:hidden!important;pointer-events:none!important;
  height:0!important;max-height:0!important;min-height:0!important;flex:0 0 0px!important;
  overflow:hidden!important;margin:0!important;padding:0!important;border:0!important
}
</style></head>"""

HELPERS = r'''
function catalogCardFrontOpen(){
  var b=document.body;
  if(!b)return false;
  return !!(b.classList.contains('chosen-preview-open')||b.classList.contains('card-embed-open')||b.classList.contains('hl-open')||b.classList.contains('gallery-open')||b.classList.contains('img-focus-open')||b.classList.contains('desc-reader-open')||b.classList.contains('path-reader-open')||b.classList.contains('desc-focus-open')||b.classList.contains('path-focus-open'));
}
function portableMenuVisibleRect(id){
  var el=document.getElementById(id);
  if(!el)return null;
  var cs=getComputedStyle(el);
  if(cs.display==='none'||cs.visibility==='hidden')return null;
  var r=el.getBoundingClientRect();
  if(!r||r.width<24||r.height<24)return null;
  return r;
}
function portableRectHitsMenu(r){
  if(!r||!window.CATALOG_PORTABLE)return false;
  var left=r.left!=null?r.left:r.x;
  var top=r.top!=null?r.top:r.y;
  var right=r.right!=null?r.right:(left+(r.width||0));
  var bottom=r.bottom!=null?r.bottom:(top+(r.height||0));
  var ids=['searchChrome','filterWrap'];
  for(var i=0;i<ids.length;i++){
    var m=portableMenuVisibleRect(ids[i]);
    if(!m)continue;
    if(!(right<=m.left+1||m.right<=left+1||bottom<=m.top+1||m.bottom<=top+1))return true;
  }
  return false;
}
window.catalogCardFrontOpen=catalogCardFrontOpen;
window.portableRectHitsMenu=portableRectHitsMenu;
function indexWindowFillsToDoc(){
'''

def sub_once(t, old, new, label):
    n = t.count(old)
    if n != 1:
        raise SystemExit(f'{label}: count={n}')
    return t.replace(old, new, 1)

def sub_all(t, old, new, label, expect=None):
    n = t.count(old)
    if expect is not None and n != expect:
        raise SystemExit(f'{label}: count={n} expected {expect}')
    if n < 1:
        raise SystemExit(f'{label}: missing')
    return t.replace(old, new)

def patch(t, name):
    t = sub_once(t, '</style></head>', CSS_TAIL, f'{name} css-tail')

    t = sub_all(
        t,
        '  body.catalog-portable.kw-fs-open #filterTop > #kwStripFs{display:none!important}',
        '  body.catalog-portable.kw-fs-open #filterTop > #kwStripFs{display:inline-flex!important}',
        f'{name} kwfs-css',
        expect=2,
    )

    t = sub_once(
        t,
        '''html body.catalog-portable.kw-fs-open #kwStripFs,
html body.catalog-portable.kw-fs-open #filterTop > #kwStripFs,
html body.catalog-portable.ac-fs-open #searchStripFs,
html body.catalog-portable.ac-fs-open .search-ac-shell.ac-fs>.search-strip .search-strip-fs{
  display:none!important
}''',
        '''html body.catalog-portable.ac-fs-open #searchStripFs,
html body.catalog-portable.ac-fs-open .search-ac-shell.ac-fs>.search-strip .search-strip-fs{
  display:none!important
}''',
        f'{name} html-kwfs-hide',
    )

    t = sub_once(t, 'function indexWindowFillsToDoc(){\n', HELPERS, f'{name} helpers')

    t = sub_once(
        t,
        '''function indexWindowFillsToDoc(){
  if(!window.CATALOG_PORTABLE)return false;
  var b=document.body;
  if(!b.classList.contains('display-sides')||b.classList.contains('display-middle'))return false;
  if(b.classList.contains('ac-fs-open')||b.classList.contains('kw-fs-open')||b.classList.contains('dual-fs-open'))return false;
  var searchOn=!b.classList.contains('search-chrome-collapsed');
  var kwOn=b.classList.contains('kw-open')&&!b.classList.contains('kw-chrome-collapsed');
  return (searchOn&&!kwOn)||(!searchOn&&kwOn);
}''',
        '''function indexWindowFillsToDoc(){
  if(!window.CATALOG_PORTABLE)return false;
  var b=document.body;
  if(b.classList.contains('ac-fs-open')||b.classList.contains('kw-fs-open')||b.classList.contains('dual-fs-open')||b.classList.contains('display-fs'))return false;
  if(typeof catalogCardFrontOpen==='function'&&catalogCardFrontOpen())return false;
  return true;
}''',
        f'{name} fill-doc',
    )

    t = sub_once(
        t,
        "var fill=!!(document.body.classList.contains('index-window-open')&&indexWindowFillsToDoc()&&ix&&!ix.classList.contains('is-collapsed')&&!ix.classList.contains('is-embedded')&&!(note&&note.classList.contains('is-embedded')));",
        "var fill=!!(document.body.classList.contains('index-window-open')&&indexWindowFillsToDoc()&&ix&&!ix.classList.contains('is-collapsed')&&!ix.classList.contains('is-embedded')&&!(note&&note.classList.contains('is-embedded'))&&!(typeof catalogCardFrontOpen==='function'&&catalogCardFrontOpen()));",
        f'{name} fill-cond',
    )

    t = sub_once(
        t,
        '''function syncPortableIndexContentGap(){
  if(!window.CATALOG_PORTABLE)return;
  var main=document.getElementById('catalogMain');
  var ix=document.getElementById('catalogIndex');
  var cb=main&&(main.querySelector(':scope > .catalog-body')||main.querySelector('.catalog-body'));
  if(!cb)return;
  var abs=!!(ix&&!ix.classList.contains('is-embedded')&&getComputedStyle(ix).position==='absolute'&&getComputedStyle(ix).display!=='none'&&getComputedStyle(ix).visibility!=='hidden');
  var h=abs?Math.ceil(ix.getBoundingClientRect().height):0;
  cb.style.setProperty('padding-top',(h?(h+22):0)+'px','important');
}''',
        '''function syncPortableIndexContentGap(){
  if(!window.CATALOG_PORTABLE)return;
  var main=document.getElementById('catalogMain');
  var ix=document.getElementById('catalogIndex');
  var cb=main&&(main.querySelector(':scope > .catalog-body')||main.querySelector('.catalog-body'));
  if(!cb)return;
  if(typeof catalogCardFrontOpen==='function'&&catalogCardFrontOpen()){
    cb.style.setProperty('padding-top','0px','important');
    return;
  }
  var abs=!!(ix&&!ix.classList.contains('is-embedded')&&getComputedStyle(ix).position==='absolute'&&getComputedStyle(ix).display!=='none'&&getComputedStyle(ix).visibility!=='hidden');
  var h=abs?Math.ceil(ix.getBoundingClientRect().height):0;
  cb.style.setProperty('padding-top',(h?(h+22):0)+'px','important');
}''',
        f'{name} ix-gap',
    )

    t = sub_once(
        t,
        '''  if(top&&pop.parentElement!==top)top.appendChild(pop);
  pop.innerHTML='';
  if(cs)pop.appendChild(cs);
  pop.removeAttribute('hidden');
  btn.setAttribute('aria-expanded','true');
  document.body.classList.add('kw-cats-open');
  btn.style.setProperty('display','inline-flex','important');''',
        '''  if(pop){pop.innerHTML='';pop.setAttribute('hidden','');}
  if(cs&&fp){if(kb)fp.insertBefore(cs,kb);else fp.insertBefore(cs,fp.firstChild);}
  btn.setAttribute('aria-expanded','true');
  document.body.classList.add('kw-cats-open');
  btn.style.setProperty('display','inline-flex','important');''',
        f'{name} kw-cats-open',
    )

    t = sub_once(
        t,
        '''  function goTop(e,topEl){
    if(!document.body.classList.contains('display-sides'))return;
    if(e){e.preventDefault();e.stopPropagation();}
    var cm=document.getElementById('catalogMain');
    var ix=document.getElementById('catalogIndex');
    var ixColBefore=!!(ix&&ix.classList.contains('is-collapsed'));
    var searchBefore=document.body.classList.contains('search-chrome-collapsed');
    var kwBefore=document.body.classList.contains('kw-chrome-collapsed');
    var kwOpenBefore=document.body.classList.contains('kw-open');
    if(ix)ix.dataset.goingTop='1';
    var sc=(typeof catalogContentScroller==='function'&&catalogContentScroller())||cm;
    if(sc){try{sc.scrollTo({top:sc.scrollTop,behavior:'instant'});}catch(err){sc.scrollTop=sc.scrollTop;}try{sc.scrollTo({top:0,behavior:'smooth'});}catch(err){sc.scrollTop=0;}}
  }
  function goBot(e){
    if(!document.body.classList.contains('display-sides'))return;
    if(e){e.preventDefault();e.stopPropagation();}
    var cm=document.getElementById('catalogMain');
    var ix=document.getElementById('catalogIndex');
    var ixColBefore=!!(ix&&ix.classList.contains('is-collapsed'));
    var searchBefore=document.body.classList.contains('search-chrome-collapsed');
    var kwBefore=document.body.classList.contains('kw-chrome-collapsed');
    var sc=(typeof catalogContentScroller==='function'&&catalogContentScroller())||cm;
    if(sc){try{sc.scrollTo({top:sc.scrollTop,behavior:'instant'});}catch(err){sc.scrollTop=sc.scrollTop;}try{sc.scrollTo({top:sc.scrollHeight,behavior:'smooth'});}catch(err){sc.scrollTop=sc.scrollHeight;}}
  }''',
        '''  function jumpScroller(){
    var cm=document.getElementById('catalogMain');
    var cb=(typeof catalogContentScroller==='function'&&catalogContentScroller())||cm;
    if(cb&&cb.scrollHeight>cb.clientHeight+8)return cb;
    if(cm&&cm.scrollHeight>cm.clientHeight+8)return cm;
    return cb||cm;
  }
  function jumpAllowed(){
    var b=document.body;
    return !!(window.CATALOG_PORTABLE||b.classList.contains('display-sides')||b.classList.contains('display-middle')||b.classList.contains('display-content'));
  }
  function goTop(e,topEl){
    if(!jumpAllowed())return;
    if(e){e.preventDefault();e.stopPropagation();}
    var cm=document.getElementById('catalogMain');
    var ix=document.getElementById('catalogIndex');
    var ixColBefore=!!(ix&&ix.classList.contains('is-collapsed'));
    var searchBefore=document.body.classList.contains('search-chrome-collapsed');
    var kwBefore=document.body.classList.contains('kw-chrome-collapsed');
    var kwOpenBefore=document.body.classList.contains('kw-open');
    if(ix)ix.dataset.goingTop='1';
    var sc=jumpScroller();
    // #region agent log
    fetch('http://127.0.0.1:7529/ingest/1cf46354-1d61-4c80-bd72-a340f1db1b51',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'c00e3e'},body:JSON.stringify({sessionId:'c00e3e',runId:'post-fix',hypothesisId:'H2',location:'portable:goTop',message:'jump-top',data:{allowed:true,content:document.body.classList.contains('display-content'),sides:document.body.classList.contains('display-sides'),scId:sc&&(sc.id||sc.className||'').toString().slice(0,24),sh:sc?sc.scrollHeight:0,ch:sc?sc.clientHeight:0,st:sc?sc.scrollTop:0},timestamp:Date.now()})}).catch(function(){});
    // #endregion
    if(sc){try{sc.scrollTo({top:sc.scrollTop,behavior:'instant'});}catch(err){sc.scrollTop=sc.scrollTop;}try{sc.scrollTo({top:0,behavior:'smooth'});}catch(err){sc.scrollTop=0;}}
  }
  function goBot(e){
    if(!jumpAllowed())return;
    if(e){e.preventDefault();e.stopPropagation();}
    var cm=document.getElementById('catalogMain');
    var ix=document.getElementById('catalogIndex');
    var ixColBefore=!!(ix&&ix.classList.contains('is-collapsed'));
    var searchBefore=document.body.classList.contains('search-chrome-collapsed');
    var kwBefore=document.body.classList.contains('kw-chrome-collapsed');
    var sc=jumpScroller();
    // #region agent log
    fetch('http://127.0.0.1:7529/ingest/1cf46354-1d61-4c80-bd72-a340f1db1b51',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'c00e3e'},body:JSON.stringify({sessionId:'c00e3e',runId:'post-fix',hypothesisId:'H2',location:'portable:goBot',message:'jump-bot',data:{allowed:true,content:document.body.classList.contains('display-content'),sides:document.body.classList.contains('display-sides'),scId:sc&&(sc.id||sc.className||'').toString().slice(0,24),sh:sc?sc.scrollHeight:0,ch:sc?sc.clientHeight:0,st:sc?sc.scrollTop:0},timestamp:Date.now()})}).catch(function(){});
    // #endregion
    if(sc){try{sc.scrollTo({top:sc.scrollTop,behavior:'instant'});}catch(err){sc.scrollTop=sc.scrollTop;}try{sc.scrollTo({top:sc.scrollHeight,behavior:'smooth'});}catch(err){sc.scrollTop=sc.scrollHeight;}}
  }''',
        f'{name} jumps',
    )

    t = sub_once(
        t,
        '''    stack.style.right=right+'px';
    stack.style.bottom=bottom+'px';
    stack.style.left='auto';
    stack.style.top='auto';
    // #region agent log
    debugJumpStackLog('placed',{mainHide:false,noteInset:typeof catalogJumpStackBottomInset==='function'?catalogJumpStackBottomInset():null,bottom:stack.style.bottom,right:stack.style.right});''',
        '''    stack.style.right=right+'px';
    stack.style.bottom=bottom+'px';
    stack.style.left='auto';
    stack.style.top='auto';
    if(window.CATALOG_PORTABLE&&typeof portableRectHitsMenu==='function'&&portableRectHitsMenu(stack.getBoundingClientRect())){
      stack.style.cssText='display:none!important';
    }
    // #region agent log
    debugJumpStackLog('placed',{mainHide:false,noteInset:typeof catalogJumpStackBottomInset==='function'?catalogJumpStackBottomInset():null,bottom:stack.style.bottom,right:stack.style.right,hitMenu:window.CATALOG_PORTABLE&&typeof portableRectHitsMenu==='function'&&portableRectHitsMenu(stack.getBoundingClientRect())});''',
        f'{name} jump-overlap',
    )

    t = sub_once(
        t,
        '''  if(typeof catalogHelpSyncChrome==='function')catalogHelpSyncChrome();
}''',
        '''  if(!helpOn&&window.CATALOG_PORTABLE&&typeof portableRectHitsMenu==='function'&&portableRectHitsMenu(stack.getBoundingClientRect())){
    stack.hidden=true;
    stack.style.cssText='';
  }
  if(typeof catalogHelpSyncChrome==='function')catalogHelpSyncChrome();
  if(typeof window.syncMainHoverStripe==='function')window.syncMainHoverStripe();
}''',
        f'{name} edge-overlap',
    )

    t = sub_once(
        t,
        '''        if(!onScreen||mrGate.width<24||mrGate.height<48)show=false;
      }''',
        '''        if(!onScreen||mrGate.width<24||mrGate.height<48)show=false;
        if(show&&typeof portableRectHitsMenu==='function'){
          var stHit={left:mrGate.right-16,right:mrGate.right+2,top:mrGate.top,bottom:mrGate.bottom};
          if(portableRectHitsMenu(stHit))show=false;
        }
      }''',
        f'{name} stripe-gate',
    )
    return t

for p in FILES:
    t = p.read_text(encoding='utf-8')
    t = patch(t, p.name)
    if not t.rstrip().endswith('</html>'):
        raise SystemExit(f'{p.name} truncated')
    fd, tmp = tempfile.mkstemp(suffix='.html', dir=p.parent)
    os.close(fd)
    Path(tmp).write_text(t, encoding='utf-8')
    os.replace(tmp, p)
    print('wrote', p.name, 'bytes', p.stat().st_size)
