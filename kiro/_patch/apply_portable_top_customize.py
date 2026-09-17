#!/usr/bin/env python3
from pathlib import Path

CSS = r"""
/* fix-PORTABLE-TOP-CUSTOMIZE: Hide gone; Customize+Layouts on header; no FS glyphs in menu FS; no overlay scrollbar dot */
@media all{
  body.catalog-portable #filterToggle .toggle-arrow{display:none!important}
  body.catalog-portable .search-strip-hide,
  body.catalog-portable.display-sides .kw-strip-hide,
  body.catalog-portable .kw-strip-hide,
  body.catalog-portable #kwStripHide{display:none!important}
  body.catalog-portable .search-strip-fs,
  body.catalog-portable .kw-fs-btn,
  body.catalog-portable #searchStripFs,
  body.catalog-portable #kwStripFs,
  body.catalog-portable.ac-fs-open .ac-fs-back,
  body.catalog-portable.kw-fs-open .kw-fs-back,
  body.catalog-portable .ac-fs-back,
  body.catalog-portable .kw-fs-back,
  body.catalog-portable .dual-fs-sep-pin,
  body.catalog-portable #dualFsSepPin,
  body.catalog-portable #fsSepPinBtn,
  body.catalog-portable #catalogMainHoverStripe,
  body.catalog-portable #catalogMain>.hover-scroll-stripe{display:none!important}
  body.catalog-portable.has-hover-overflow-content #catalogMainHoverStripe.hover-scroll-fixed:not([hidden]){display:none!important}
  body.catalog-portable #hdrLayoutBtns{
    display:inline-flex!important;align-items:center;gap:4px;flex:0 0 auto;order:2;min-width:0
  }
  body.catalog-portable #hdrLayoutBtns #layoutEditBtn,
  body.catalog-portable #hdrLayoutBtns #layoutPresets,
  body.catalog-portable #hdrLayoutBtns .layout-presets,
  body.catalog-portable #hdrLayoutBtns .layout-presets-btn{
    display:inline-flex!important;visibility:visible!important
  }
  body.catalog-portable #hdrLayoutBtns .layout-presets-pop:not([hidden]){
    display:flex!important;position:fixed!important;z-index:430!important
  }
  body.catalog-portable #hdrLayoutBtns .layout-presets-tab[hidden]{display:none!important}
}
"""

JS_ORIENT = """function layoutOrientId(){
  if(typeof displayIsMiddle==='function'?displayIsMiddle():(document.body&&document.body.classList.contains('display-middle')))return 'middle';
  if(window.CATALOG_PORTABLE){
    try{if(window.matchMedia&&window.matchMedia('(orientation:portrait)').matches)return 'phone-p';}catch(eOr){}
    return 'phone-w';
  }
  return (typeof isPortraitDesktopSides==='function'&&isPortraitDesktopSides())?'portrait':'wide';
}"""

JS_BUCKET = """function layoutBucketId(){
  var o=layoutOrientId();
  var g=(typeof liveLayoutScopeId==='function')?liveLayoutScopeId():'sck';
  if(o==='middle')return 'middle-'+g;
  var flip=document.body.classList.contains('sides-portrait-flip')?'B':'A';
  if(o==='phone-p')return 'phone-p-'+flip+'-'+g;
  if(o==='phone-w')return 'phone-w-'+flip+'-'+g;
  if(o!=='portrait')return 'wide';
  return 'portrait-'+flip+'-'+g;
}"""

def patch(path: Path) -> None:
    t = path.read_text(encoding='utf-8')
    if 'fix-PORTABLE-TOP-CUSTOMIZE' not in t:
        if '</style></head>' not in t:
            raise SystemExit(f'no style end in {path}')
        t = t.replace('</style></head>', CSS + '</style></head>', 1)

    t = t.replace(
        "portableMoreRowAdd(pop,'Hide',function(){if(typeof toggleSearchChrome==='function')toggleSearchChrome();},'Hide Search');\n",
        '',
    )
    t = t.replace(
        "portableMoreRowAdd(pop,'Hide',function(){if(typeof toggleKwChrome==='function')toggleKwChrome();else if(typeof toggleHdrKw==='function')toggleHdrKw();},'Hide Keywords');\n",
        '',
    )

    old_orient = """function layoutOrientId(){
  if(typeof displayIsMiddle==='function'?displayIsMiddle():(document.body&&document.body.classList.contains('display-middle')))return 'middle';
  return (typeof isPortraitDesktopSides==='function'&&isPortraitDesktopSides())?'portrait':'wide';
}"""
    if old_orient in t:
        t = t.replace(old_orient, JS_ORIENT, 1)
    old_bucket = """function layoutBucketId(){
  var o=layoutOrientId();
  if(o==='middle')return 'middle-'+((typeof liveLayoutScopeId==='function')?liveLayoutScopeId():'sck');
  if(o!=='portrait')return 'wide';
  var flip=document.body.classList.contains('sides-portrait-flip')?'B':'A';
  var g=(typeof liveLayoutScopeId==='function')?liveLayoutScopeId():'sck';
  return 'portrait-'+flip+'-'+g;
}"""
    if old_bucket in t:
        t = t.replace(old_bucket, JS_BUCKET, 1)

    old_map = """  if(o==='middle')return 'catalog-layouts-middle-'+coerceScope(so)+'-'+ns;
  if(o==='wide')return 'catalog-layouts-wide-'+ns;
  var flip=document.body.classList.contains('sides-portrait-flip')?'B':'A';"""
    new_map = """  if(o==='middle')return 'catalog-layouts-middle-'+coerceScope(so)+'-'+ns;
  if(o==='phone-p'||o==='phone-w'){
    var flipP=document.body.classList.contains('sides-portrait-flip')?'B':'A';
    return 'catalog-layouts-'+o+'-'+flipP+'-'+coerceScope(so)+'-'+ns;
  }
  if(o==='wide')return 'catalog-layouts-wide-'+ns;
  var flip=document.body.classList.contains('sides-portrait-flip')?'B':'A';"""
    t = t.replace(old_map, new_map)

    old_last = """  if(o==='middle')return 'catalog-layouts-middle-'+coerceScope(so)+'-last-'+ns;
  if(o==='wide')return 'catalog-layouts-wide-last-'+ns;
  var flip=document.body.classList.contains('sides-portrait-flip')?'B':'A';"""
    new_last = """  if(o==='middle')return 'catalog-layouts-middle-'+coerceScope(so)+'-last-'+ns;
  if(o==='phone-p'||o==='phone-w'){
    var flipL=document.body.classList.contains('sides-portrait-flip')?'B':'A';
    return 'catalog-layouts-'+o+'-'+flipL+'-'+coerceScope(so)+'-last-'+ns;
  }
  if(o==='wide')return 'catalog-layouts-wide-last-'+ns;
  var flip=document.body.classList.contains('sides-portrait-flip')?'B':'A';"""
    t = t.replace(old_last, new_last)

    needle = """  var lab=document.getElementById('layoutPresetsStoreLabel');
  var wide=(typeof layoutOrientId==='function'?layoutOrientId():'')==='wide';
  if(lab)lab.textContent=wide?'Widescreen':meta.label;"""
    repl = """  if(window.CATALOG_PORTABLE){
    layoutUiScope=typeof liveLayoutScopeId==='function'?liveLayoutScopeId():id;
    id=layoutUiScope;meta=layoutScopeMeta(id);
    document.querySelectorAll('.layout-presets-tab').forEach(function(t){
      var sid=normalizeLayoutScope(t.getAttribute('data-layout-scope'));
      var show=sid===id;
      t.hidden=!show;
      t.style.display=show?'':'none';
      t.classList.toggle('is-active',show);
    });
  }
  var lab=document.getElementById('layoutPresetsStoreLabel');
  var oLab=(typeof layoutOrientId==='function'?layoutOrientId():'');
  var wide=oLab==='wide';
  if(lab){
    if(window.CATALOG_PORTABLE){
      var modeN=document.body.classList.contains('display-middle')?'Middle':(document.body.classList.contains('display-sides')?'Sides':'Content');
      var orN=oLab==='phone-p'?'Portrait':(oLab==='phone-w'?'Landscape':oLab);
      lab.textContent=modeN+' · '+orN+' · '+meta.label;
    }else lab.textContent=wide?'Widescreen':meta.label;
  }"""
    if needle in t:
        t = t.replace(needle, repl, 1)

    t = t.replace(
        'nl=Math.max(140,Math.min(Math.round(vwP*0.82),nl));',
        'nl=Math.max(168,Math.min(Math.round(vwP*0.55),nl));',
    )
    t = t.replace(
        'var nh=Math.max(96,Math.min(Math.round(vhP*0.62),drag.h+(e.clientY-drag.y)));',
        'var nh=Math.max(128,Math.min(Math.round(vhP*0.48),drag.h+(e.clientY-drag.y)));',
    )

    hover = """      var sc=n.sc,max=Math.max(0,sc.scrollHeight-sc.clientHeight);
      var show=max>8;
      n.h.classList.toggle('has-hover-overflow',show);"""
    hover_new = """      var sc=n.sc,max=Math.max(0,sc.scrollHeight-sc.clientHeight);
      var show=max>8;
      if(window.CATALOG_PORTABLE&&mark==='content'){
        n.st.hidden=true;n.h.classList.remove('has-hover-overflow');
        document.body.classList.remove('has-hover-overflow-content');
        // #region agent log
        try{
          if(!window._dbgDot||Date.now()-window._dbgDot>1200){
            window._dbgDot=Date.now();
            fetch('http://127.0.0.1:7529/ingest/1cf46354-1d61-4c80-bd72-a340f1db1b51',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'c00e3e'},body:JSON.stringify({sessionId:'c00e3e',runId:'post-fix',hypothesisId:'G',location:'portable:hover-content',message:'content overlay suppressed',data:{showWould:show,stHidden:true,gutter:(sc.offsetWidth||0)-(sc.clientWidth||0)},timestamp:Date.now()})}).catch(function(){});
          }
        }catch(eDbgG){}
        // #endregion
        return;
      }
      n.h.classList.toggle('has-hover-overflow',show);"""
    if hover in t:
        t = t.replace(hover, hover_new, 1)

    tsc = """function toggleSearchChrome(){
  if(document.body.classList.contains('search-chrome-collapsed')) expandSearchMenu();
  else collapseSearchMenu();
}"""
    tsc_new = """function toggleSearchChrome(){
  // #region agent log
  try{
    fetch('http://127.0.0.1:7529/ingest/1cf46354-1d61-4c80-bd72-a340f1db1b51',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'c00e3e'},body:JSON.stringify({sessionId:'c00e3e',runId:'post-fix',hypothesisId:'H',location:'portable:toggleSearchChrome',message:'search chrome toggle',data:{collapsed:document.body.classList.contains('search-chrome-collapsed'),sides:document.body.classList.contains('display-sides'),middle:document.body.classList.contains('display-middle')},timestamp:Date.now()})}).catch(function(){});
  }catch(eDbgH){}
  // #endregion
  if(document.body.classList.contains('search-chrome-collapsed')) expandSearchMenu();
  else collapseSearchMenu();
}"""
    if tsc in t:
        t = t.replace(tsc, tsc_new, 1)

    tkc = """function toggleKwChrome(){
  if(!document.body.classList.contains('display-sides')){
    if(typeof toggleFilter==='function')toggleFilter();
    return;
  }"""
    tkc_new = """function toggleKwChrome(){
  // #region agent log
  try{
    fetch('http://127.0.0.1:7529/ingest/1cf46354-1d61-4c80-bd72-a340f1db1b51',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'c00e3e'},body:JSON.stringify({sessionId:'c00e3e',runId:'post-fix',hypothesisId:'H',location:'portable:toggleKwChrome',message:'kw chrome toggle',data:{sides:document.body.classList.contains('display-sides'),middle:document.body.classList.contains('display-middle'),kwOpen:document.body.classList.contains('kw-open'),kwCollapsed:document.body.classList.contains('kw-chrome-collapsed')},timestamp:Date.now()})}).catch(function(){});
  }catch(eDbgHk){}
  // #endregion
  if(!document.body.classList.contains('display-sides')){
    if(typeof toggleFilter==='function')toggleFilter();
    return;
  }"""
    if tkc in t:
        t = t.replace(tkc, tkc_new, 1)

    boot = 'var CATALOG_PORTABLE=true;window.CATALOG_PORTABLE=true;document.body.classList.add("catalog-portable");'
    probe = boot + r'''
function dbgPortableChromeProbe(src){
  if(!window.CATALOG_PORTABLE)return;
  try{
    if(src==='scroll'&&window._dbgProbe&&Date.now()-window._dbgProbe<1000)return;
    window._dbgProbe=Date.now();
    var cs=function(el){return el?getComputedStyle(el):null;};
    var arrow=document.querySelector('#filterToggle .toggle-arrow');
    var hideS=document.querySelector('.search-strip-hide');
    var hideK=document.getElementById('kwStripHide');
    var edit=document.getElementById('layoutEditBtn');
    var presets=document.getElementById('layoutPresets');
    var hdrHost=document.getElementById('hdrLayoutBtns');
    var stripe=document.getElementById('catalogMainHoverStripe');
    var acFs=document.querySelector('.ac-fs-back');
    var kwFs=document.querySelector('.kw-fs-back');
    var pin=document.getElementById('dualFsSepPin');
    fetch('http://127.0.0.1:7529/ingest/1cf46354-1d61-4c80-bd72-a340f1db1b51',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'c00e3e'},body:JSON.stringify({sessionId:'c00e3e',runId:'post-fix',hypothesisId:'P',location:'portable:chrome-probe',message:'portable chrome probe',data:{src:String(src||''),o:(typeof layoutOrientId==='function')?layoutOrientId():'?',b:(typeof layoutBucketId==='function')?layoutBucketId():'?',g:(typeof liveLayoutScopeId==='function')?liveLayoutScopeId():'?',arrowDisp:arrow&&cs(arrow).display,hideSDisp:hideS&&cs(hideS).display,hideKDisp:hideK&&cs(hideK).display,editDisp:edit&&cs(edit).display,editParent:edit&&edit.parentElement&&edit.parentElement.id,presetsDisp:presets&&cs(presets).display,hdrHostDisp:hdrHost&&cs(hdrHost).display,stripeHidden:stripe?!!stripe.hidden:null,stripeDisp:stripe&&cs(stripe).display,acFsDisp:acFs&&cs(acFs).display,kwFsDisp:kwFs&&cs(kwFs).display,pinDisp:pin&&cs(pin).display,acFsOpen:document.body.classList.contains('ac-fs-open'),kwFsOpen:document.body.classList.contains('kw-fs-open'),searchCollapsed:document.body.classList.contains('search-chrome-collapsed'),kwCollapsed:document.body.classList.contains('kw-chrome-collapsed'),sides:document.body.classList.contains('display-sides'),middle:document.body.classList.contains('display-middle'),portrait:!!(window.matchMedia&&window.matchMedia('(orientation:portrait)').matches)},timestamp:Date.now()})}).catch(function(){});
  }catch(eDbgP){}
}
window.dbgPortableChromeProbe=dbgPortableChromeProbe;
'''
    if 'dbgPortableChromeProbe' not in t and boot in t:
        t = t.replace(boot, probe, 1)

    ens = """  // #region agent log
  if(typeof dbgPortableScroll==='function')dbgPortableScroll('ensure-scroll',{hyp:'H-OVF',menuFs:String(menuFs||'')});
  // #endregion
}"""
    ens_new = """  // #region agent log
  if(typeof dbgPortableScroll==='function')dbgPortableScroll('ensure-scroll',{hyp:'H-OVF',menuFs:String(menuFs||'')});
  if(typeof dbgPortableChromeProbe==='function')dbgPortableChromeProbe('scroll');
  // #endregion
}"""
    if ens in t:
        t = t.replace(ens, ens_new, 1)

    pin = """  var pin=document.getElementById('modePinBtn');
  if(pin)pin.hidden=true;"""
    pin_new = """  var pin=document.getElementById('modePinBtn');
  if(pin)pin.hidden=true;
  var sepPin=document.getElementById('dualFsSepPin');
  if(sepPin&&window.CATALOG_PORTABLE)sepPin.hidden=true;"""
    if pin in t:
        t = t.replace(pin, pin_new, 1)

    hover_bind = """  window.syncMainHoverStripe=bindStripe('catalogMain','catalogMain','content');
  window.bindMainHoverStripe=window.bindHover_content||function(){if(window.syncMainHoverStripe)window.syncMainHoverStripe();};"""
    hover_bind_new = """  if(window.CATALOG_PORTABLE){
    window.syncMainHoverStripe=function(){};
    window.bindMainHoverStripe=function(){};
  }else{
    window.syncMainHoverStripe=bindStripe('catalogMain','catalogMain','content');
    window.bindMainHoverStripe=window.bindHover_content||function(){if(window.syncMainHoverStripe)window.syncMainHoverStripe();};
  }"""
    if hover_bind in t:
        t = t.replace(hover_bind, hover_bind_new, 1)

    path.write_text(t, encoding='utf-8')
    print('patched', path)

def main():
    root = Path('/home/phnx/kiro-kontakt-patch/public/catalogs')
    for name in ('KONTAKT-CATALOG-portable.html', 'DS-CATALOG-portable.html'):
        patch(root / name)

if __name__ == '__main__':
    main()
