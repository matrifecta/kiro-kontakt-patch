#!/usr/bin/env python3
"""Desc/path FS logs + KW ⛶ left of Clear, Clear restyle, one Collapse, no Search History."""
from pathlib import Path

ROOT = Path('/home/phnx/kiro-kontakt-patch/public/catalogs')
FILES = [
    ROOT / 'KONTAKT-CATALOG-portable.html',
    ROOT / 'DS-CATALOG-portable.html',
    ROOT / 'KONTAKT-CATALOG.html',
    ROOT / 'DS-CATALOG.html',
]

INGEST = "fetch('http://127.0.0.1:7529/ingest/1cf46354-1d61-4c80-bd72-a340f1db1b51',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'c00e3e'},body:JSON.stringify("
TAIL = ")}).catch(function(){});"

KW_CSS = '''
/* fix-KW-STRIP-FS-CLEAR: show Keywords ⛶ left of Clear; Clear matches toolbar chrome */
@media all{
  body.catalog-portable #filterTop > #kwStripFs{
    display:inline-flex!important;align-items:center;justify-content:center;
    flex:0 0 auto;order:90;margin-left:auto;
    min-width:2.75rem;min-height:2.75rem;padding:0 .45rem;
    border:1px solid var(--border);border-radius:6px;
    background:var(--bg-card);color:var(--text);font:inherit;cursor:pointer
  }
  body.catalog-portable.kw-fs-open #filterTop > #kwStripFs{display:none!important}
  body.catalog-portable #filterTop > #kwStripClear,
  body.catalog-portable #kwStripClear.kw-strip-clear{
    display:inline-flex!important;align-items:center;justify-content:center;
    flex:0 0 auto;order:91;margin-left:0;
    min-height:2.75rem;padding:0 .55rem;
    border:1px solid var(--border)!important;border-radius:6px;
    background:var(--bg-card)!important;color:var(--text)!important;
    font:inherit;cursor:pointer
  }
  body.catalog-portable #kwStripClear.mode-btn.clear-all{
    border-color:var(--border)!important;color:var(--text)!important;
    background:var(--bg-card)!important
  }
  body.catalog-portable #filterTop > #kwStripMore{order:92;margin-left:0}
  body.catalog-portable #filterTop > #kwStripMorePop{order:93}
}
'''

ACTIVATE_LOG = '''function activateDesc(entry){
  // #region agent log
  try{
    var _mmH=false,_mmW=false;
    try{_mmH=window.matchMedia('(hover:none) and (pointer:coarse)').matches;_mmW=window.matchMedia('(max-width:899px)').matches;}catch(eMm){}
    ''' + INGEST + '''{sessionId:'c00e3e',runId:'pre-fix',hypothesisId:'B',location:'catalog:activateDesc',message:'activateDesc',data:{id:entry&&entry.id,phone:typeof isPhoneViewport==='function'&&isPhoneViewport(),desk:typeof displayIsDesktop==='function'&&displayIsDesktop(),mobileFocus:typeof useMobileFocus==='function'&&useMobileFocus(),hoverNoneCoarse:_mmH,maxW899:_mmW,portable:!!window.CATALOG_PORTABLE,hl:!!(entry&&entry.classList.contains('highlight')),w:window.innerWidth},timestamp:Date.now()}''' + TAIL + '''
  }catch(eDbgB){}
  // #endregion
'''

CLICK_LOG = '''    // #region agent log
    try{
      var _t=e.target;
      ''' + INGEST + '''{sessionId:'c00e3e',runId:'pre-fix',hypothesisId:'A',location:'catalog:entryClick',message:'entry click',data:{tag:_t&&_t.tagName,cls:((_t&&_t.className)||'').toString().slice(0,120),hitA:!!(_t.closest&&_t.closest('a')),hitSum:!!(_t.closest&&_t.closest('summary')),hitPat:!!(_t.closest&&_t.closest('.patches')),hitPanel:!!(_t.closest&&_t.closest('.summary-panel')),hitPath:!!(_t.closest&&_t.closest('.path')),hitEarly:!!(_t.closest&&_t.closest('a,.hl-close,.hl-min,.preview-back,.kw,input,select,textarea,summary,.patches,.search-popup-btn,.search-link,.fav-btn,.note-balloon,.note-pop,.un-badge,.note-save,.note-cancel,.fs-btn,.card-search-embed,#cardMinDock'))},timestamp:Date.now()}''' + TAIL + '''
    }catch(eDbgA){}
    // #endregion
'''

OPEN_FOCUS_LOG = '''function openDescFocus(el, closeTo){
  var wrap=document.getElementById('descFocus');
  // #region agent log
  try{
    var _cs=wrap?getComputedStyle(wrap):null;
    ''' + INGEST + '''{sessionId:'c00e3e',runId:'pre-fix',hypothesisId:'D',location:'catalog:openDescFocus',message:'openDescFocus',data:{hasWrap:!!wrap,hasEl:!!el,closeTo:closeTo||null,disp:_cs&&_cs.display,z:_cs&&_cs.zIndex,openCls:!!(wrap&&wrap.classList.contains('open'))},timestamp:Date.now()}''' + TAIL + '''
  }catch(eDbgD){}
  // #endregion
'''

CLOSE_FOCUS_LOG = '''function closeDescFocus(keepClosed){
  var wrap=document.getElementById('descFocus');
  // #region agent log
  try{
    ''' + INGEST + '''{sessionId:'c00e3e',runId:'pre-fix',hypothesisId:'C',location:'catalog:closeDescFocus',message:'closeDescFocus',data:{keepClosed:!!keepClosed,wasOpen:!!(wrap&&wrap.classList.contains('open'))},timestamp:Date.now()}''' + TAIL + '''
  }catch(eDbgC){}
  // #endregion
'''

OPEN_READER_LOG = '''function openDescReader(el, closeTo){
  var reader=document.getElementById('descReader');
  // #region agent log
  try{
    var _cs=reader?getComputedStyle(reader):null;
    ''' + INGEST + '''{sessionId:'c00e3e',runId:'pre-fix',hypothesisId:'B',location:'catalog:openDescReader',message:'openDescReader',data:{hasReader:!!reader,hasEl:!!el,closeTo:closeTo||null,disp:_cs&&_cs.display,z:_cs&&_cs.zIndex},timestamp:Date.now()}''' + TAIL + '''
  }catch(eDbgR){}
  // #endregion
'''

OPEN_PATH_LOG = '''function openPathFocus(el, closeTo){
  var wrap=document.getElementById('pathFocus');
  // #region agent log
  try{
    var _cs=wrap?getComputedStyle(wrap):null;
    ''' + INGEST + '''{sessionId:'c00e3e',runId:'pre-fix',hypothesisId:'E',location:'catalog:openPathFocus',message:'openPathFocus',data:{hasWrap:!!wrap,hasEl:!!el,closeTo:closeTo||null,disp:_cs&&_cs.display,z:_cs&&_cs.zIndex},timestamp:Date.now()}''' + TAIL + '''
  }catch(eDbgE){}
  // #endregion
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
    portable = 'portable' in path.name
    print('====', path.name)

    if 'catalog:activateDesc' not in s:
        s = once(s, 'function activateDesc(entry){\n  if(!entry)return;\n',
                 ACTIVATE_LOG + '  if(!entry)return;\n', 'activateDesc-log')
    if 'catalog:entryClick' not in s:
        s = once(s,
                 "  var entry=e.target.closest('.entry');\n  if(entry){\n    if(e.target.closest('a,.hl-close",
                 "  var entry=e.target.closest('.entry');\n  if(entry){\n" + CLICK_LOG + "    if(e.target.closest('a,.hl-close",
                 'entryClick-log')
    if 'catalog:openDescFocus' not in s:
        s = once(s, 'function openDescFocus(el, closeTo){\n  var wrap=document.getElementById(\'descFocus\');\n',
                 OPEN_FOCUS_LOG, 'openDescFocus-log')
    if 'catalog:closeDescFocus' not in s:
        s = once(s, 'function closeDescFocus(keepClosed){\n  var wrap=document.getElementById(\'descFocus\');\n',
                 CLOSE_FOCUS_LOG, 'closeDescFocus-log')
    if 'catalog:openDescReader' not in s:
        s = once(s, 'function openDescReader(el, closeTo){\n  var reader=document.getElementById(\'descReader\');\n',
                 OPEN_READER_LOG, 'openDescReader-log')
    if 'catalog:openPathFocus' not in s:
        s = once(s, 'function openPathFocus(el, closeTo){\n  var wrap=document.getElementById(\'pathFocus\');\n',
                 OPEN_PATH_LOG, 'openPathFocus-log')

    if portable:
        if 'fix-KW-STRIP-FS-CLEAR' not in s:
            s = once(s, '</style></head><body', KW_CSS + '</style></head><body', 'kw-fs-css')

        s = once(s,
                 "    portableMoreRowAdd(pop,'History',function(){var h=document.getElementById('searchHistory');if(h)h.click();},'History');\n  portableMoreRowAdd(pop,'Fullscreen'",
                 "    portableMoreRowAdd(pop,'Fullscreen'",
                 'search-more-no-history')

        s = once(s,
                 "  phoneMoreAdd(pop,'Collapse',function(){if(typeof collapseAllPatchTrees==='function')collapseAllPatchTrees();},'Collapse open patch lists');\n  phoneMoreAdd(pop,'Collapse',function(){if(typeof collapseAllPatchTrees==='function')collapseAllPatchTrees();},'Collapse open patch lists');\n",
                 "  phoneMoreAdd(pop,'Collapse',function(){if(typeof collapseAllPatchTrees==='function')collapseAllPatchTrees();},'Collapse open patch lists');\n",
                 'hdr-one-collapse')

        s = once(s,
                 "    clrBtn.id='kwStripClear';\n    clrBtn.classList.add('kw-strip-clear');\n    if(moreKw){\n      if(clrBtn.parentElement!==topKw||clrBtn.nextElementSibling!==moreKw)topKw.insertBefore(clrBtn,moreKw);\n    }else if(clrBtn.parentElement!==topKw)topKw.appendChild(clrBtn);\n  }",
                 "    clrBtn.id='kwStripClear';\n    clrBtn.classList.add('kw-strip-clear');\n    clrBtn.classList.remove('clear-all');\n    var fsBtn=document.getElementById('kwStripFs');\n    if(fsBtn&&topKw&&(fsBtn.parentElement!==topKw||(clrBtn&&fsBtn.nextElementSibling!==clrBtn))){\n      topKw.insertBefore(fsBtn,clrBtn);\n    }\n    if(moreKw){\n      if(clrBtn.parentElement!==topKw||clrBtn.nextElementSibling!==moreKw)topKw.insertBefore(clrBtn,moreKw);\n    }else if(clrBtn.parentElement!==topKw)topKw.appendChild(clrBtn);\n  }",
                 'kw-fs-before-clear')

    dup = '<button type="button" class="collapse-cards-btn" id="collapseCardsBtn" title="Collapse open patch lists and even card sizes" onclick="event.preventDefault();event.stopPropagation();if(typeof collapseAllPatchTrees===\'function\')collapseAllPatchTrees()">Collapse</button><button type="button" class="collapse-cards-btn" id="collapseCardsBtn"'
    one = '<button type="button" class="collapse-cards-btn" id="collapseCardsBtn"'
    if dup in s:
        s = once(s, dup, one, 'html-one-collapse')

    s = once(s,
             'class="mode-btn clear-all kw-strip-clear" id="kwStripClear"',
             'class="kw-strip-clear" id="kwStripClear"',
             'clear-not-red-html')

    path.write_text(s, encoding='utf-8')

if __name__ == '__main__':
    for p in FILES:
        patch(p)
