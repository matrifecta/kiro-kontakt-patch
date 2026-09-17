#!/usr/bin/env python3
from pathlib import Path
import re

HELPERS = r'''function searchListShouldStay(){
  return !!(document.body&&!document.body.classList.contains('search-chrome-collapsed'));
}
function ensureSearchList(src){
  if(typeof searchListShouldStay==='function'&&!searchListShouldStay())return;
  var si=document.getElementById('searchInput')||(typeof searchInput!=='undefined'?searchInput:null);
  var q=((si&&si.value)||'').trim().toLowerCase();
  try{if(typeof showAc==='function')showAc(q,{force:true});}catch(eEns){}
  // #region agent log
  try{
    var acE=document.getElementById('acList');
    fetch('http://127.0.0.1:7529/ingest/1cf46354-1d61-4c80-bd72-a340f1db1b51',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'c00e3e'},body:JSON.stringify({sessionId:'c00e3e',runId:'post-fix',hypothesisId:'A',location:'catalog:ensureSearchList',message:'ensure search list',data:{src:String(src||''),qLen:q.length,n:acE?acE.childNodes.length:0,open:!!(acE&&acE.classList.contains('open')),htmlLen:acE?(acE.innerHTML||'').length:0},timestamp:Date.now()})}).catch(function(){});
  }catch(eDbgA){}
  // #endregion
}
window.searchListShouldStay=searchListShouldStay;
window.ensureSearchList=ensureSearchList;
'''

def patch(path: Path) -> None:
    t = path.read_text(encoding='utf-8')
    if 'function searchListShouldStay()' not in t:
        t = t.replace('function showAc(q,opts){', HELPERS + 'function showAc(q,opts){', 1)

    t = re.sub(
        r'(function showAc\(q,opts\)\{\s*opts=opts\|\|\{\};)',
        r'''\1
if(typeof searchListShouldStay==='function'&&searchListShouldStay())opts.force=true;''',
        t,
        count=1,
    )

    t = t.replace(
        "if(document.body.classList.contains('search-extras-collapsed')){if(acList){acList.classList.remove('open');acList.innerHTML='';}return;}",
        "if(document.body.classList.contains('search-extras-collapsed')&&!(typeof searchListShouldStay==='function'&&searchListShouldStay())){if(acList){acList.classList.remove('open');acList.innerHTML='';}return;}",
        1,
    )
    t = t.replace(
        "if(typeof overlayCoversSearch==='function'&&overlayCoversSearch()){if(acList){acList.classList.remove('open');acList.innerHTML='';}if(typeof window.hideSearchAc==='function')window.hideSearchAc();return;}",
        "if(typeof overlayCoversSearch==='function'&&overlayCoversSearch()&&!(typeof searchListShouldStay==='function'&&searchListShouldStay())){if(acList){acList.classList.remove('open');acList.innerHTML='';}if(typeof window.hideSearchAc==='function')window.hideSearchAc({force:true});return;}",
        1,
    )

    if 'var forceHide=' not in t:
        t = t.replace('function hideSearchAc(){', '''function hideSearchAc(opts){
  opts=opts||{};
  var forceHide=opts===true||!!opts.force;
  if(!forceHide&&typeof searchListShouldStay==='function'&&searchListShouldStay()){
    if(typeof ensureSearchList==='function')ensureSearchList('hide-stay');
    if(typeof portableEnsureScrollMenus==='function')portableEnsureScrollMenus();
    return;
  }
''', 1)

    t = t.replace(
        '''  if(typeof parkSearchStrip==='function')parkSearchStrip();
  if(typeof window.hideSearchAc==='function')window.hideSearchAc();''',
        '''  if(typeof parkSearchStrip==='function')parkSearchStrip();
  if(typeof window.hideSearchAc==='function')window.hideSearchAc({force:true});''',
        1,
    )

    exp = '''  var si=document.getElementById('searchInput');
  if(si&&!document.body.classList.contains('ac-fs-open'))setTimeout(function(){si.focus();},50);
}'''
    exp_new = '''  if(typeof ensureSearchList==='function')ensureSearchList('expand');
  var si=document.getElementById('searchInput');
  if(si&&!document.body.classList.contains('ac-fs-open'))setTimeout(function(){si.focus();if(typeof ensureSearchList==='function')ensureSearchList('expand-focus');},50);
}'''
    if exp in t:
        t = t.replace(exp, exp_new, 1)

    t = t.replace(
        "if(!document.body.classList.contains('search-extras-collapsed')&&acList&&(acList.classList.contains('open')||(searchInput&&document.activeElement===searchInput))){",
        "if((typeof searchListShouldStay==='function'&&searchListShouldStay())||(!document.body.classList.contains('search-extras-collapsed')&&acList&&(acList.classList.contains('open')||(searchInput&&document.activeElement===searchInput)))){",
        1,
    )

    fo = '''    if(window._acItemPointer)return;
    if(typeof portableKeepAcOpen==='function'&&portableKeepAcOpen()){
      if(typeof portableEnsureScrollMenus==='function')portableEnsureScrollMenus();
      return;
    }
    if(acL){acL.classList.remove('open');acL.innerHTML='';}'''
    fo_new = '''    if(window._acItemPointer)return;
    if(typeof searchListShouldStay==='function'&&searchListShouldStay()){
      if(typeof ensureSearchList==='function')ensureSearchList('focusout');
      return;
    }
    if(typeof portableKeepAcOpen==='function'&&portableKeepAcOpen()){
      if(typeof portableEnsureScrollMenus==='function')portableEnsureScrollMenus();
      return;
    }
    if(acL){acL.classList.remove('open');acL.innerHTML='';}'''
    if fo in t:
        t = t.replace(fo, fo_new, 1)
    else:
        fo2 = '''    if(window._acItemPointer)return;
    if(acL){acL.classList.remove('open');acL.innerHTML='';}'''
        fo2_new = '''    if(window._acItemPointer)return;
    if(typeof searchListShouldStay==='function'&&searchListShouldStay()){
      if(typeof ensureSearchList==='function')ensureSearchList('focusout');
      return;
    }
    if(acL){acL.classList.remove('open');acL.innerHTML='';}'''
        t = t.replace(fo2, fo2_new, 1)

    t = t.replace(
        '''  document.addEventListener('pointerdown',function(e){
    if(!acOpen())return;
    if(typeof portableKeepAcOpen==='function'&&portableKeepAcOpen())return;''',
        '''  document.addEventListener('pointerdown',function(e){
    if(!acOpen())return;
    if(typeof searchListShouldStay==='function'&&searchListShouldStay())return;
    if(typeof portableKeepAcOpen==='function'&&portableKeepAcOpen())return;''',
        1,
    )
    t = t.replace(
        '''  document.addEventListener('pointerdown',function(e){
    if(!acOpen())return;
    if(e.target.closest&&e.target.closest('#acShell,#searchInput,.search-strip,.search-chrome,#filterWrap,.filter-toggle'))return;''',
        '''  document.addEventListener('pointerdown',function(e){
    if(!acOpen())return;
    if(typeof searchListShouldStay==='function'&&searchListShouldStay())return;
    if(e.target.closest&&e.target.closest('#acShell,#searchInput,.search-strip,.search-chrome,#filterWrap,.filter-toggle'))return;''',
        1,
    )

    pick = '''if(acList){acList.classList.remove('open');acList.innerHTML='';}
if(window.CATALOG_PORTABLE||(window.matchMedia&&window.matchMedia('(max-width:899px)').matches)){
  searchInput.blur();
  if(typeof window.hideSearchAc==='function')window.hideSearchAc();
}
applySearch();'''
    pick_new = '''if(!(typeof searchListShouldStay==='function'&&searchListShouldStay())&&acList){acList.classList.remove('open');acList.innerHTML='';}
if(!(typeof searchListShouldStay==='function'&&searchListShouldStay())&&(window.CATALOG_PORTABLE||(window.matchMedia&&window.matchMedia('(max-width:899px)').matches))){
  searchInput.blur();
  if(typeof window.hideSearchAc==='function')window.hideSearchAc({force:true});
}
applySearch();
if(typeof ensureSearchList==='function')ensureSearchList('pick');'''
    if pick in t:
        t = t.replace(pick, pick_new, 1)

    t = t.replace(
        "if(searchInput)searchInput.value='';if(acList)acList.classList.remove('open');};",
        "if(searchInput)searchInput.value='';if(typeof searchListShouldStay==='function'&&searchListShouldStay()){if(typeof ensureSearchList==='function')ensureSearchList('add-kw');}else if(acList)acList.classList.remove('open');};",
        1,
    )

    t = t.replace(
        "if(acList)acList.classList.remove('open');\n     applySearch();",
        "if(!(typeof searchListShouldStay==='function'&&searchListShouldStay())&&acList)acList.classList.remove('open');\n     applySearch();",
        1,
    )
    t = t.replace(
        "if(acList)acList.classList.remove('open');\napplySearch();",
        "if(!(typeof searchListShouldStay==='function'&&searchListShouldStay())&&acList)acList.classList.remove('open');\napplySearch();",
        1,
    )

    old_keep = '''function portableKeepAcOpen(){
  if(!window.CATALOG_PORTABLE)return false;
  var b=document.body.classList;
  if(b.contains('search-chrome-collapsed'))return false;
  if(b.contains('ac-fs-open')&&!b.contains('kw-fs-open'))return true;
  if(b.contains('is-browser-fs')||document.documentElement.classList.contains('is-browser-fs'))return true;
  if(b.contains('display-sides')&&!b.contains('display-middle'))return true;
  return false;
}'''
    new_keep = '''function portableKeepAcOpen(){
  if(!window.CATALOG_PORTABLE)return false;
  return typeof searchListShouldStay==='function'?searchListShouldStay():!document.body.classList.contains('search-chrome-collapsed');
}'''
    if old_keep in t:
        t = t.replace(old_keep, new_keep, 1)

    extras = "window.showSearchExtras=function(){document.body.classList.remove('search-extras-collapsed','search-chrome-collapsed');if(window.syncSearchHideBtn)window.syncSearchHideBtn();if(window.restoreSearchUi)window.restoreSearchUi();};"
    extras_new = "window.showSearchExtras=function(){document.body.classList.remove('search-extras-collapsed','search-chrome-collapsed');if(window.syncSearchHideBtn)window.syncSearchHideBtn();if(window.restoreSearchUi)window.restoreSearchUi();if(typeof ensureSearchList==='function')ensureSearchList('show-extras');};"
    t = t.replace(extras, extras_new, 1)

    path.write_text(t, encoding='utf-8')
    print('patched', path.name)

def main():
    root = Path('/home/phnx/kiro-kontakt-patch/public/catalogs')
    for name in (
        'KONTAKT-CATALOG-portable.html',
        'DS-CATALOG-portable.html',
        'KONTAKT-CATALOG.html',
        'DS-CATALOG.html',
    ):
        patch(root / name)

if __name__ == '__main__':
    main()
