#!/usr/bin/env python3
"""Clip desc/path on active/preview cards; don't trap wheel; Collapse keeps scroll; debounce equalize."""
from pathlib import Path

ROOT = Path('/home/phnx/kiro-kontakt-patch/public/catalogs')
FILES = [
    ROOT / 'KONTAKT-CATALOG.html',
    ROOT / 'DS-CATALOG.html',
    ROOT / 'KONTAKT-CATALOG-portable.html',
    ROOT / 'DS-CATALOG-portable.html',
]

INGEST = "fetch('http://127.0.0.1:7529/ingest/1cf46354-1d61-4c80-bd72-a340f1db1b51',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'c00e3e'},body:JSON.stringify("
TAIL = ")}).catch(function(){});"

CLIP_CSS = r'''
/* fix-CARD-SCROLL-CLIP: grid 8.2em window even when selected; preview clips long desc; no wheel trap */
.entry.selected:not(.highlight) .summary-panel{height:8.2em;max-height:8.2em;overflow:hidden}
.entry.selected:not(.highlight) .summary-panel .desc,.entry.selected:not(.highlight) .desc{max-height:100%;overflow:hidden;overscroll-behavior:auto;touch-action:auto}
.entry.selected:not(.highlight) .path{max-height:none;overflow:hidden;overscroll-behavior:auto;touch-action:auto}
.entry.highlight .summary-panel{max-height:min(14em,32vh);overflow:hidden;overflow-y:auto}
.entry.highlight .summary-panel .desc,.entry.highlight .desc{min-height:0;max-height:none;overflow:visible}
body.chosen-preview-open .entry.selected:not(.highlight) .summary-panel{
  height:auto!important;max-height:min(14em,calc(36vh - 2.5em))!important;
  overflow:hidden!important;overflow-y:auto!important;flex:1 1 auto!important;min-height:0!important
}
body.chosen-preview-open .entry.selected:not(.highlight) .summary-panel .desc,
body.chosen-preview-open .entry.selected:not(.highlight) .desc{
  max-height:100%!important;min-height:0!important;overflow-x:hidden!important;overflow-y:auto!important
}
body.chosen-preview-open .entry.selected:not(.highlight) .path{
  overflow:hidden!important;max-height:none!important
}
'''

COLLAPSE_OLD = '''function collapseAllPatchTrees(){
  window._collapsingPatches=true;
  var n=0;
  try{
    document.querySelectorAll('.entry details.patches, .entry details.grp').forEach(function(d){
      if(d.open){d.open=false;n++;}
    });
  }finally{window._collapsingPatches=false;}
  if(typeof scheduleEqualizeCardRows==='function')scheduleEqualizeCardRows();
'''

COLLAPSE_NEW = '''function catalogScrollEl(){
  var body=document.querySelector('#catalogMain > .catalog-body');
  if(body){
    var cs=getComputedStyle(body);
    if((cs.overflowY==='auto'||cs.overflowY==='scroll')&&body.scrollHeight>body.clientHeight+4)return body;
  }
  var main=document.getElementById('catalogMain');
  if(main){
    var cs2=getComputedStyle(main);
    if(cs2.overflowY==='auto'||cs2.overflowY==='scroll')return main;
  }
  return document.scrollingElement||document.documentElement;
}
function collapseAllPatchTrees(){
  var sc=typeof catalogScrollEl==='function'?catalogScrollEl():null;
  var y0=sc?sc.scrollTop:0;
  var anchor=lastViewedEntry||document.querySelector('.entry.selected');
  var top0=anchor?anchor.getBoundingClientRect().top:null;
  window._collapsingPatches=true;
  var n=0;
  try{
    document.querySelectorAll('.entry details.patches, .entry details.grp').forEach(function(d){
      if(d.open){d.open=false;n++;}
    });
  }finally{window._collapsingPatches=false;}
  if(typeof equalizeCatalogCardRows==='function')equalizeCatalogCardRows();
  if(sc){
    if(anchor&&top0!=null){
      var top1=anchor.getBoundingClientRect().top;
      sc.scrollTop=y0+(top1-top0);
    }else sc.scrollTop=y0;
  }
  // #region agent log
  try{
    ''' + INGEST + '''{sessionId:'c00e3e',runId:'post-fix',hypothesisId:'B',location:'catalog:collapseAllPatchTrees',message:'collapse scroll restore',data:{n:n,y0:Math.round(y0),y1:sc?Math.round(sc.scrollTop):null,dTop:anchor&&top0!=null?Math.round(anchor.getBoundingClientRect().top-top0):null,scId:sc&&sc.id||(sc&&sc.className)||'root'},timestamp:Date.now()}''' + TAIL + '''
  }catch(eDbgB){}
  // #endregion
'''

EQ_START_OLD = 'function equalizeCatalogCardRows(){\n  var groups=document.querySelectorAll(\'.loc-group\');\n'
EQ_START_NEW = '''function equalizeCatalogCardRows(){
  var _eqT0=(typeof performance!=='undefined'&&performance.now)?performance.now():Date.now();
  window._eqN=(window._eqN||0)+1;
  var groups=document.querySelectorAll('.loc-group');
'''

IMG_OLD = "document.addEventListener('load',function(e){if(e.target&&e.target.tagName==='IMG'&&e.target.closest&&e.target.closest('.entry')&&typeof scheduleEqualizeCardRows==='function')scheduleEqualizeCardRows();},true);"
IMG_NEW = """document.addEventListener('load',function(e){if(e.target&&e.target.tagName==='IMG'&&e.target.closest&&e.target.closest('.entry')&&typeof scheduleEqualizeCardRows==='function'){if(window._eqImgT)clearTimeout(window._eqImgT);window._eqImgT=setTimeout(function(){window._eqImgT=0;scheduleEqualizeCardRows();},180);}},true);"""

WHEEL_LOG = '''
document.addEventListener('wheel',function(e){
  var field=e.target.closest&&e.target.closest('.summary-panel,.summary-panel .desc,.path');
  if(!field)return;
  var ent=field.closest('.entry');
  if(!ent||!ent.classList.contains('selected'))return;
  if(window._eqWheelLog&&Date.now()-window._eqWheelLog<400)return;
  window._eqWheelLog=Date.now();
  try{
    var cs=getComputedStyle(field);
    var main=document.getElementById('catalogMain');
    var body=document.querySelector('#catalogMain > .catalog-body');
    ''' + INGEST + '''{sessionId:'c00e3e',runId:'post-fix',hypothesisId:'A',location:'catalog:wheelOverDescPath',message:'wheel over active desc/path',data:{tag:field.tagName,cls:(field.className||'').toString().slice(0,40),ovY:cs.overflowY,osc:cs.overscrollBehavior||cs.overscrollBehaviorY,canScroll:field.scrollHeight>field.clientHeight+1,hl:ent.classList.contains('highlight'),preview:document.body.classList.contains('chosen-preview-open'),mainSt:main?Math.round(main.scrollTop):null,bodySt:body?Math.round(body.scrollTop):null,delta:Math.round(e.deltaY)},timestamp:Date.now()}''' + TAIL + '''
  }catch(eDbgA){}
},{passive:true});
'''

def once(s, old, new, label):
    if old not in s:
        print('MISS', label)
        return s
    n = s.count(old)
    if n != 1:
        print('MULTI', n, label)
        return s
    print('OK', label)
    return s.replace(old, new, 1)

def patch(path: Path):
    s = path.read_text(encoding='utf-8')
    print('====', path.name)

    s = once(s,
        '.entry.selected:not(.highlight) .summary-panel{max-height:none;overflow:visible}\n .entry.selected:not(.highlight) .summary-panel .desc,.entry.selected:not(.highlight) .desc{max-height:7.2em;overflow-y:auto;-webkit-overflow-scrolling:touch;touch-action:pan-y;overscroll-behavior:contain}\n .entry.selected:not(.highlight) .path{max-height:6em;overflow-y:auto;-webkit-overflow-scrolling:touch;touch-action:pan-y;overscroll-behavior:contain}',
        '.entry.selected:not(.highlight) .summary-panel{height:8.2em;max-height:8.2em;overflow:hidden}\n .entry.selected:not(.highlight) .summary-panel .desc,.entry.selected:not(.highlight) .desc{max-height:100%;overflow:hidden;overscroll-behavior:auto;touch-action:auto}\n .entry.selected:not(.highlight) .path{max-height:none;overflow:hidden;overscroll-behavior:auto;touch-action:auto}',
        'selected-clip')

    s = once(s,
        '.entry.highlight .summary-panel{width:100%;max-width:100%;overflow:visible;overflow-wrap:break-word;background:var(--bg);max-height:none;flex:none}',
        '.entry.highlight .summary-panel{width:100%;max-width:100%;overflow:hidden;overflow-y:auto;overflow-wrap:break-word;background:var(--bg);max-height:min(14em,32vh);flex:none}',
        'hl-panel-clip')

    if 'fix-CARD-SCROLL-CLIP' not in s:
        s = once(s, '</style></head><body', CLIP_CSS + '</style></head><body', 'clip-css')

    if 'function catalogScrollEl()' not in s:
        s = once(s, COLLAPSE_OLD, COLLAPSE_NEW, 'collapse-scroll')

    s = once(s, EQ_START_OLD, EQ_START_NEW, 'eq-timer')

    # throttle existing equalize fetches: wrap first fetch in equalize after rowLog
    s = once(s,
        "  // #region agent log\n  try{\n    fetch('http://127.0.0.1:7529/ingest/1cf46354-1d61-4c80-bd72-a340f1db1b51',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'c00e3e'},body:JSON.stringify({sessionId:'c00e3e',runId:'post-fix',hypothesisId:'C',location:'catalog:equalizeCatalogCardRows'",
        "  // #region agent log\n  try{\n    var _eqDt=(typeof performance!=='undefined'&&performance.now)?Math.round(performance.now()-_eqT0):0;\n    if(window._eqN%8!==1){\n      /* skip hot equalize logs */\n    }else fetch('http://127.0.0.1:7529/ingest/1cf46354-1d61-4c80-bd72-a340f1db1b51',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'c00e3e'},body:JSON.stringify({sessionId:'c00e3e',runId:'post-fix',hypothesisId:'C',location:'catalog:equalizeCatalogCardRows'",
        'eq-throttle-c')

    # inject dt/n into that same payload if we can
    s = once(s,
        "message:'equalize card row heights',data:rowLog||{n:0},timestamp:Date.now()})",
        "message:'equalize card row heights',data:Object.assign({dt:_eqDt,eqN:window._eqN},rowLog||{n:0}),timestamp:Date.now()})",
        'eq-payload')

    s = once(s,
        "  // #region agent log\n  try{\n    var _e=document.querySelector('#catalogMain .loc-group > .entry:not(.highlight)');",
        "  // #region agent log\n  try{\n    if(window._eqN%8!==1)throw 0;\n    var _e=document.querySelector('#catalogMain .loc-group > .entry:not(.highlight)');",
        'eq-throttle-e')

    s = once(s,
        "  // #region agent log\n  try{\n    var _cards=[];\n    document.querySelectorAll('#catalogMain .loc-group > .entry:not(.highlight)').forEach(function(e,i){",
        "  // #region agent log\n  try{\n    if(window._eqN%8!==1)throw 0;\n    var _cards=[];\n    document.querySelectorAll('#catalogMain .loc-group > .entry:not(.highlight)').forEach(function(e,i){",
        'eq-throttle-f')

    s = once(s, IMG_OLD, IMG_NEW, 'img-debounce')

    if 'catalog:wheelOverDescPath' not in s:
        s = once(s,
            "document.addEventListener('wheel',function(e){\n  var b=document.body.classList;",
            WHEEL_LOG + "document.addEventListener('wheel',function(e){\n  var b=document.body.classList;",
            'wheel-log')

    path.write_text(s, encoding='utf-8')

if __name__ == '__main__':
    for p in FILES:
        patch(p)
