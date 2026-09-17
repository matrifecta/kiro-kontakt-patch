#!/usr/bin/env python3
"""Desktop Sides/Middle Flip + persist menu order. Keep prior three fixes. Portable Flip unchanged."""
from pathlib import Path

ROOT = Path("/home/phnx/kiro-kontakt-patch")
FILES = [
    ROOT / "public/catalogs/KONTAKT-CATALOG.html",
    ROOT / "public/catalogs/DS-CATALOG.html",
    ROOT / "public/catalogs/KONTAKT-CATALOG-portable.html",
    ROOT / "public/catalogs/DS-CATALOG-portable.html",
]


def add_indent(s, n=1):
    pad = " " * n
    return "\n".join((pad + line) if line.strip() else line for line in s.split("\n"))


def sub(text, old, new, label, optional=False):
    n = text.count(old)
    if n == 1:
        return text.replace(old, new, 1)
    if n > 1:
        raise SystemExit(f"{label}: {n} matches")
    if new in text:
        print(f"  skip {label} (already)")
        return text
    for i in range(1, 9):
        oldi, newi = add_indent(old, i), add_indent(new, i)
        ni = text.count(oldi)
        if ni == 1:
            return text.replace(oldi, newi, 1)
        if ni > 1:
            raise SystemExit(f"{label}: {ni} matches (indent {i})")
        if ni == 0 and newi in text:
            print(f"  skip {label} (already)")
            return text
    if optional:
        print(f"  skip {label}")
        return text
    raise SystemExit(f"{label}: not found")


CSS_OLD = """@media(max-width:899px){.display-btn[data-display='middle']{display:inline-flex!important}}
#portraitFlipBtn[hidden]{display:none!important}"""

CSS_NEW = """@media(max-width:899px){.display-btn[data-display='middle']{display:inline-flex!important}}
/* fix-DESKTOP-FLIP-ARRANGE: Sides skip-center Flip; Middle mirror; portrait stack first-above */
@media(min-width:900px){
  body.display-sides:not(.display-middle):not(.catalog-portable).sides-portrait-flip:not(.search-chrome-collapsed):not(.kw-chrome-collapsed) #searchChrome{grid-column:3!important}
  body.display-sides:not(.display-middle):not(.catalog-portable).sides-portrait-flip:not(.search-chrome-collapsed):not(.kw-chrome-collapsed) #filterWrap{grid-column:1!important}
  body.display-sides:not(.display-middle):not(.catalog-portable).sides-portrait-flip:not(.search-chrome-collapsed):not(.kw-chrome-collapsed) #catalogMain{grid-column:2!important}
  body.display-sides:not(.display-middle):not(.catalog-portable).sides-portrait-flip.kw-chrome-collapsed:not(.search-chrome-collapsed){
    grid-template-columns:minmax(0,1fr) var(--sides-lw,22vw)!important
  }
  body.display-sides:not(.display-middle):not(.catalog-portable).sides-portrait-flip.kw-chrome-collapsed:not(.search-chrome-collapsed) #catalogMain{grid-column:1!important}
  body.display-sides:not(.display-middle):not(.catalog-portable).sides-portrait-flip.kw-chrome-collapsed:not(.search-chrome-collapsed) #searchChrome{grid-column:2!important}
  body.display-sides:not(.display-middle):not(.catalog-portable).sides-portrait-flip.search-chrome-collapsed:not(.kw-chrome-collapsed){
    grid-template-columns:var(--sides-rw,26vw) minmax(0,1fr)!important
  }
  body.display-sides:not(.display-middle):not(.catalog-portable).sides-portrait-flip.search-chrome-collapsed:not(.kw-chrome-collapsed) #filterWrap{grid-column:1!important}
  body.display-sides:not(.display-middle):not(.catalog-portable).sides-portrait-flip.search-chrome-collapsed:not(.kw-chrome-collapsed) #catalogMain{grid-column:2!important}
  body.display-sides.display-middle:not(.catalog-portable).middle-kw-first:not(.sides-portrait-flip) #filterWrap{grid-column:1!important}
  body.display-sides.display-middle:not(.catalog-portable).middle-kw-first:not(.sides-portrait-flip) #searchChrome{grid-column:2!important}
  body.display-sides.display-middle:not(.catalog-portable).sides-portrait-flip:not(.middle-kw-first) #searchChrome{grid-column:2!important}
  body.display-sides.display-middle:not(.catalog-portable).sides-portrait-flip:not(.middle-kw-first) #filterWrap{grid-column:1!important}
  body.display-sides.display-middle:not(.catalog-portable).sides-portrait-flip.middle-kw-first #searchChrome{grid-column:1!important}
  body.display-sides.display-middle:not(.catalog-portable).sides-portrait-flip.middle-kw-first #filterWrap{grid-column:2!important}
}
@media(min-width:900px) and (orientation:portrait){
  body.display-sides.display-middle:not(.catalog-portable):not(.search-chrome-collapsed):not(.kw-chrome-collapsed){
    grid-template-columns:minmax(0,1fr)!important;
    grid-template-rows:auto minmax(0,calc(var(--middle-menu-h,38dvh) / 2)) minmax(0,calc(var(--middle-menu-h,38dvh) / 2)) minmax(0,1fr)!important
  }
  body.display-sides.display-middle:not(.catalog-portable):not(.search-chrome-collapsed):not(.kw-chrome-collapsed) #searchChrome,
  body.display-sides.display-middle:not(.catalog-portable):not(.search-chrome-collapsed):not(.kw-chrome-collapsed) #filterWrap{
    grid-column:1/-1!important;height:100%!important
  }
  body.display-sides.display-middle:not(.catalog-portable):not(.search-chrome-collapsed):not(.kw-chrome-collapsed):not(.middle-kw-first):not(.sides-portrait-flip) #searchChrome{grid-row:2!important}
  body.display-sides.display-middle:not(.catalog-portable):not(.search-chrome-collapsed):not(.kw-chrome-collapsed):not(.middle-kw-first):not(.sides-portrait-flip) #filterWrap{grid-row:3!important}
  body.display-sides.display-middle:not(.catalog-portable):not(.search-chrome-collapsed):not(.kw-chrome-collapsed):not(.middle-kw-first):not(.sides-portrait-flip) #catalogMain{grid-row:4!important;grid-column:1/-1!important}
  body.display-sides.display-middle:not(.catalog-portable):not(.search-chrome-collapsed):not(.kw-chrome-collapsed).middle-kw-first:not(.sides-portrait-flip) #filterWrap{grid-row:2!important}
  body.display-sides.display-middle:not(.catalog-portable):not(.search-chrome-collapsed):not(.kw-chrome-collapsed).middle-kw-first:not(.sides-portrait-flip) #searchChrome{grid-row:3!important}
  body.display-sides.display-middle:not(.catalog-portable):not(.search-chrome-collapsed):not(.kw-chrome-collapsed).middle-kw-first:not(.sides-portrait-flip) #catalogMain{grid-row:4!important;grid-column:1/-1!important}
  body.display-sides.display-middle:not(.catalog-portable):not(.search-chrome-collapsed):not(.kw-chrome-collapsed):not(.middle-kw-first).sides-portrait-flip #catalogMain{grid-row:2!important;grid-column:1/-1!important}
  body.display-sides.display-middle:not(.catalog-portable):not(.search-chrome-collapsed):not(.kw-chrome-collapsed):not(.middle-kw-first).sides-portrait-flip #filterWrap{grid-row:3!important}
  body.display-sides.display-middle:not(.catalog-portable):not(.search-chrome-collapsed):not(.kw-chrome-collapsed):not(.middle-kw-first).sides-portrait-flip #searchChrome{grid-row:4!important}
  body.display-sides.display-middle:not(.catalog-portable):not(.search-chrome-collapsed):not(.kw-chrome-collapsed).middle-kw-first.sides-portrait-flip #catalogMain{grid-row:2!important;grid-column:1/-1!important}
  body.display-sides.display-middle:not(.catalog-portable):not(.search-chrome-collapsed):not(.kw-chrome-collapsed).middle-kw-first.sides-portrait-flip #searchChrome{grid-row:3!important}
  body.display-sides.display-middle:not(.catalog-portable):not(.search-chrome-collapsed):not(.kw-chrome-collapsed).middle-kw-first.sides-portrait-flip #filterWrap{grid-row:4!important}
  body.display-sides.display-middle:not(.catalog-portable).sides-portrait-flip.search-chrome-collapsed:not(.kw-chrome-collapsed) #catalogMain{grid-row:2!important;grid-column:1/-1!important}
  body.display-sides.display-middle:not(.catalog-portable).sides-portrait-flip.search-chrome-collapsed:not(.kw-chrome-collapsed) #filterWrap{grid-row:3!important;grid-column:1/-1!important}
  body.display-sides.display-middle:not(.catalog-portable).sides-portrait-flip.kw-chrome-collapsed:not(.search-chrome-collapsed) #catalogMain{grid-row:2!important;grid-column:1/-1!important}
  body.display-sides.display-middle:not(.catalog-portable).sides-portrait-flip.kw-chrome-collapsed:not(.search-chrome-collapsed) #searchChrome{grid-row:3!important;grid-column:1/-1!important}
}
#portraitFlipBtn[hidden]{display:none!important}"""

HELPERS_OLD = """// fix-PORTRAIT-SEP: portrait A/B helpers (drag lives in bindSidesDrag; Customize + ±30% clamp)"""

HELPERS_NEW = r"""function desktopArrangeStoreKey(){return 'catalog-desktop-arrange-'+(window.CATALOG_NS||'catalog');}
function desktopArrangeSlotId(){
  var middle=typeof displayIsMiddle==='function'?displayIsMiddle():document.body.classList.contains('display-middle');
  var mode=middle?'middle':(document.body.classList.contains('display-sides')?'sides':'other');
  var orient=(typeof displayOrientId==='function')?displayOrientId():((typeof isPortraitDesktopSides==='function'&&isPortraitDesktopSides())?'portrait':'landscape');
  var scope=(typeof liveLayoutScopeId==='function')?liveLayoutScopeId():'sck';
  return mode+'-'+orient+'-'+scope;
}
function readDesktopArrangeMap(){
  try{
    var o=JSON.parse(localStorage.getItem(desktopArrangeStoreKey())||'{}');
    return (o&&typeof o==='object'&&!Array.isArray(o))?o:{};
  }catch(err){return {};}
}
function writeDesktopArrangeMap(map){try{localStorage.setItem(desktopArrangeStoreKey(),JSON.stringify(map));}catch(err){}}
function readDesktopArrange(id){
  id=id||desktopArrangeSlotId();
  var row=readDesktopArrangeMap()[id]||{};
  return {flip:!!row.flip,stackFirst:(row.stackFirst==='keywords'?'keywords':(row.stackFirst==='search'?'search':''))};
}
function writeDesktopArrange(patch,id){
  if(window.CATALOG_PORTABLE)return;
  if(id===true){id=desktopArrangeSlotId();patch=patch||{};}
  else if(typeof id!=='string')id=desktopArrangeSlotId();
  var map=readDesktopArrangeMap();
  var cur=Object.assign({flip:false,stackFirst:''},map[id]||{},patch||{});
  if(cur.stackFirst!=='keywords'&&cur.stackFirst!=='search')cur.stackFirst='';
  map[id]={flip:!!cur.flip,stackFirst:cur.stackFirst};
  writeDesktopArrangeMap(map);
  return map[id];
}
function applyDesktopArrange(){
  if(window.CATALOG_PORTABLE)return;
  if(!(typeof displayIsDesktop==='function'?displayIsDesktop():(window.matchMedia&&window.matchMedia('(min-width:900px)').matches)))return;
  var sides=document.body.classList.contains('display-sides');
  var middle=typeof displayIsMiddle==='function'?displayIsMiddle():document.body.classList.contains('display-middle');
  if(!sides&&!middle){
    document.body.classList.remove('sides-portrait-flip','middle-kw-first');
    return;
  }
  var row=readDesktopArrange();
  document.body.classList.toggle('sides-portrait-flip',!!row.flip);
  document.body.classList.toggle('middle-kw-first',middle&&row.stackFirst==='keywords');
  if(typeof syncPortraitFlipBtn==='function')syncPortraitFlipBtn();
}
function noteMiddleMenuOpened(which){
  if(window.CATALOG_PORTABLE)return;
  if(!(typeof displayIsMiddle==='function'?displayIsMiddle():document.body.classList.contains('display-middle')))return;
  if(!(typeof isPortraitDesktopSides==='function'&&isPortraitDesktopSides()))return;
  var searchOn=!document.body.classList.contains('search-chrome-collapsed');
  var kwOn=!document.body.classList.contains('kw-chrome-collapsed')&&document.body.classList.contains('kw-open');
  if(which==='search')searchOn=true;
  if(which==='keywords')kwOn=true;
  if(searchOn&&kwOn){
    var already=(which==='search')?'keywords':'search';
    writeDesktopArrange({stackFirst:already});
  }else if(which==='search'||which==='keywords'){
    var cur=readDesktopArrange();
    if(!cur.stackFirst)writeDesktopArrange({stackFirst:which});
  }
  applyDesktopArrange();
}
window.desktopArrangeSlotId=desktopArrangeSlotId;
window.readDesktopArrange=readDesktopArrange;
window.writeDesktopArrange=writeDesktopArrange;
window.applyDesktopArrange=applyDesktopArrange;
window.noteMiddleMenuOpened=noteMiddleMenuOpened;
// fix-PORTRAIT-SEP: portrait A/B helpers (drag lives in bindSidesDrag; Customize + ±30% clamp)"""

WRITE_FLIP_OLD = """function writePortraitFlip(on){
    try{localStorage.setItem(portraitFlipKey(),on?'1':'0');}catch(err){}
  }"""

WRITE_FLIP_NEW = """function writePortraitFlip(on){
    if(!window.CATALOG_PORTABLE&&typeof writeDesktopArrange==='function'){
      writeDesktopArrange({flip:!!on});
      return;
    }
    try{localStorage.setItem(portraitFlipKey(),on?'1':'0');}catch(err){}
  }"""

FLIP_ON_OLD = """function portraitFlipOn(scope){
    try{
      var raw=localStorage.getItem(portraitFlipKey());
      if(!raw)return false;
      if(raw==='1'||raw==='0')return raw==='1';
      var o=JSON.parse(raw);
      if(o&&typeof o==='object'&&!Array.isArray(o))return !!o[scope||portraitFlipScope()];
    }catch(err){}
    return false;
  }"""

FLIP_ON_NEW = """function portraitFlipOn(scope){
    if(!window.CATALOG_PORTABLE&&typeof readDesktopArrange==='function')return !!readDesktopArrange().flip;
    try{
      var raw=localStorage.getItem(portraitFlipKey());
      if(!raw)return false;
      if(raw==='1'||raw==='0')return raw==='1';
      var o=JSON.parse(raw);
      if(o&&typeof o==='object'&&!Array.isArray(o))return !!o[scope||portraitFlipScope()];
    }catch(err){}
    return false;
  }"""

SYNC_SHOW_OLD = """var show=!!(document.body.classList.contains('display-sides')&&isPortraitDesktopSides()&&!(typeof displayIsMiddle==='function'?displayIsMiddle():document.body.classList.contains('display-middle')));
    fb.textContent=on?'Portrait: menus right':'Portrait: menus left';
    fb.setAttribute('aria-pressed',on?'true':'false');
    fb.title='Desktop portrait Sides: put Search/Keywords on the left or right of Content';
    fb.hidden=!show;"""

SYNC_SHOW_NEW = """var middleNow=typeof displayIsMiddle==='function'?displayIsMiddle():document.body.classList.contains('display-middle');
    var sidesNow=document.body.classList.contains('display-sides');
    var deskNow=typeof displayIsDesktop==='function'?displayIsDesktop():!!(window.matchMedia&&window.matchMedia('(min-width:900px)').matches);
    var show=window.CATALOG_PORTABLE?!!(sidesNow&&isPortraitDesktopSides()&&!middleNow):!!(deskNow&&(sidesNow||middleNow));
    fb.textContent=window.CATALOG_PORTABLE?'Flip':'Flip';
    fb.setAttribute('aria-pressed',on?'true':'false');
    fb.title=middleNow?'Mirror menus and content':'Swap left and right panes; content stays center when both menus are open';
    fb.classList.add('hdr-menu-btn');
    fb.classList.toggle('is-on',!!on);
    fb.hidden=!show;"""

ENSURE_OLD = """function ensurePortraitFlipBtn(){
    var pop=document.getElementById('layoutPresetsPop');
    if(!pop)return;
    var fb=document.getElementById('portraitFlipBtn');
    if(!fb){
      fb=document.createElement('button');
      fb.type='button';fb.id='portraitFlipBtn';fb.className='layout-restore-defaults';
      fb.addEventListener('click',function(e){
        e.preventDefault();e.stopPropagation();
        togglePortraitSidesFlip();
      });
      var rb=document.getElementById('layoutRestoreDefaults');
      if(rb)rb.insertAdjacentElement('afterend',fb);
      else pop.appendChild(fb);
    }
    syncPortraitFlipBtn();
  }"""

ENSURE_NEW = """function ensurePortraitFlipBtn(){
    var fb=document.getElementById('portraitFlipBtn');
    if(!fb){
      fb=document.createElement('button');
      fb.type='button';fb.id='portraitFlipBtn';
      fb.addEventListener('click',function(e){
        e.preventDefault();e.stopPropagation();
        togglePortraitSidesFlip();
      });
    }
    fb.className=window.CATALOG_PORTABLE?'hdr-menu-btn':'hdr-menu-btn';
    var host=document.getElementById('hdrLayoutBtns')||document.getElementById('hdrMenuBtns')||document.getElementById('hdrCluster');
    if(host&&fb.parentElement!==host)host.appendChild(fb);
    var pop=document.getElementById('layoutPresetsPop');
    if(pop&&window.CATALOG_PORTABLE){/* portable already parks Flip on hdr */}
    syncPortraitFlipBtn();
  }"""

# Portable has its own ensurePortraitFlipBtn — leave it. Optional replace of desktop-only function.

TOGGLE_OLD = """function togglePortraitSidesFlip(){
    if(typeof snapshotCurrentLayoutBucket==='function'){snapshotCurrentLayoutBucket();lastLayoutBucket='pending';}
    writePortraitFlip(!portraitFlipOn());
    applyPortraitSides();
    if(typeof placeSidesHandles==='function')placeSidesHandles();
    
  }"""

TOGGLE_NEW = """function togglePortraitSidesFlip(){
    if(typeof snapshotCurrentLayoutBucket==='function'){snapshotCurrentLayoutBucket();lastLayoutBucket='pending';}
    writePortraitFlip(!portraitFlipOn());
    if(!window.CATALOG_PORTABLE&&typeof applyDesktopArrange==='function')applyDesktopArrange();
    applyPortraitSides();
    if(typeof applySidesCols==='function')applySidesCols();
    if(typeof placeSidesHandles==='function')placeSidesHandles();
    if(typeof syncHdrMenuBtns==='function')syncHdrMenuBtns();
    
  }"""

APPLY_MID_STRIP_OLD = """if(typeof displayIsMiddle==='function'?displayIsMiddle():document.body.classList.contains('display-middle')){
      document.body.classList.remove('sides-portrait-flip');
      if(typeof syncPortraitFlipBtn==='function')syncPortraitFlipBtn();
      return;
    }"""

APPLY_MID_STRIP_NEW = """if(typeof displayIsMiddle==='function'?displayIsMiddle():document.body.classList.contains('display-middle')){
      if(window.CATALOG_PORTABLE)document.body.classList.remove('sides-portrait-flip');
      else if(typeof applyDesktopArrange==='function')applyDesktopArrange();
      if(typeof ensurePortraitFlipBtn==='function')ensurePortraitFlipBtn();
      if(typeof syncPortraitFlipBtn==='function')syncPortraitFlipBtn();
      return;
    }"""

APPLY_MIDDLE_OLD = """function applyMiddleLayout(){
  if(!displayIsMiddle())return;
  document.body.classList.remove('sides-portrait-flip');"""

APPLY_MIDDLE_NEW = """function applyMiddleLayout(){
  if(!displayIsMiddle())return;
  if(window.CATALOG_PORTABLE)document.body.classList.remove('sides-portrait-flip');
  else if(typeof applyDesktopArrange==='function')applyDesktopArrange();"""

SIDES_COLS_OLD = """if(middle){
    document.body.classList.remove('sides-portrait-flip');
    if(typeof applyMiddleLayout==='function')applyMiddleLayout();
  }else if(portrait){
    var flipOn=typeof window.portraitFlipOn==='function'?window.portraitFlipOn():document.body.classList.contains('sides-portrait-flip');
    document.body.classList.toggle('sides-portrait-flip',!!flipOn);
  }else{
    document.body.classList.remove('sides-portrait-flip');
  }"""

SIDES_COLS_NEW = """if(middle){
    if(window.CATALOG_PORTABLE)document.body.classList.remove('sides-portrait-flip');
    if(typeof applyMiddleLayout==='function')applyMiddleLayout();
    if(!window.CATALOG_PORTABLE&&typeof applyDesktopArrange==='function')applyDesktopArrange();
  }else if(portrait){
    var flipOn=typeof window.portraitFlipOn==='function'?window.portraitFlipOn():document.body.classList.contains('sides-portrait-flip');
    document.body.classList.toggle('sides-portrait-flip',!!flipOn);
    if(!window.CATALOG_PORTABLE&&typeof applyDesktopArrange==='function')applyDesktopArrange();
  }else{
    if(window.CATALOG_PORTABLE)document.body.classList.remove('sides-portrait-flip');
    else if(typeof applyDesktopArrange==='function')applyDesktopArrange();
  }"""

APPLY_P_FLIP_OLD = """    var flip=sides&&portrait&&portraitFlipOn();
    document.body.classList.toggle('sides-portrait-flip',flip);"""

APPLY_P_FLIP_NEW = """    var flip=window.CATALOG_PORTABLE?(sides&&portrait&&portraitFlipOn()):(sides&&portraitFlipOn());
    document.body.classList.toggle('sides-portrait-flip',!!flip);
    if(!window.CATALOG_PORTABLE&&typeof applyDesktopArrange==='function')applyDesktopArrange();"""

SNAP_OLD = """    mmh:parseInt(getComputedStyle(document.documentElement).getPropertyValue('--middle-menu-h'),10)||undefined
  };"""

SNAP_NEW = """    mmh:parseInt(getComputedStyle(document.documentElement).getPropertyValue('--middle-menu-h'),10)||undefined,
    flip:typeof portraitFlipOn==='function'?!!portraitFlipOn():document.body.classList.contains('sides-portrait-flip'),
    stackFirst:(typeof readDesktopArrange==='function'&&readDesktopArrange().stackFirst)||(document.body.classList.contains('middle-kw-first')?'keywords':'search')
  };"""

APPLY_SNAP_OLD = """    if((snap.mlw||snap.mmh)&&typeof writeMiddleLayout==='function')writeMiddleLayout(snap.mlw,snap.mmh);"""

APPLY_SNAP_NEW = """    if((snap.mlw||snap.mmh)&&typeof writeMiddleLayout==='function')writeMiddleLayout(snap.mlw,snap.mmh);
    if(typeof writeDesktopArrange==='function'&&(typeof snap.flip==='boolean'||snap.stackFirst)){
      writeDesktopArrange({flip:typeof snap.flip==='boolean'?!!snap.flip:readDesktopArrange().flip,stackFirst:snap.stackFirst||readDesktopArrange().stackFirst});
      if(typeof applyDesktopArrange==='function')applyDesktopArrange();
    }"""

EXPAND_S_OLD = """  document.body.classList.remove('search-chrome-collapsed','search-extras-collapsed');
  syncSearchHideBtn();
  if(typeof applySidesCols==='function')applySidesCols();"""

EXPAND_S_NEW = """  document.body.classList.remove('search-chrome-collapsed','search-extras-collapsed');
  if(typeof noteMiddleMenuOpened==='function')noteMiddleMenuOpened('search');
  syncSearchHideBtn();
  if(typeof applySidesCols==='function')applySidesCols();"""

EXPAND_K_OLD = """  document.body.classList.remove('kw-chrome-collapsed');
  var w=document.getElementById('filterWrap');
  if(w)w.classList.add('open');
  document.body.classList.add('kw-open');"""

EXPAND_K_NEW = """  document.body.classList.remove('kw-chrome-collapsed');
  var w=document.getElementById('filterWrap');
  if(w)w.classList.add('open');
  document.body.classList.add('kw-open');
  if(typeof noteMiddleMenuOpened==='function')noteMiddleMenuOpened('keywords');"""

TOGGLE_PORTABLE_OLD = """function togglePortraitSidesFlip(){
    if(typeof snapshotCurrentLayoutBucket==='function'){snapshotCurrentLayoutBucket();lastLayoutBucket='pending';}
    writePortraitFlip(!portraitFlipOn());
    applyPortraitSides();
    if(typeof syncHdrMenuBtns==='function')syncHdrMenuBtns();
    if(typeof placeSidesHandles==='function')placeSidesHandles();"""

TOGGLE_PORTABLE_NEW = """function togglePortraitSidesFlip(){
    if(typeof snapshotCurrentLayoutBucket==='function'){snapshotCurrentLayoutBucket();lastLayoutBucket='pending';}
    writePortraitFlip(!portraitFlipOn());
    if(!window.CATALOG_PORTABLE&&typeof applyDesktopArrange==='function')applyDesktopArrange();
    applyPortraitSides();
    if(typeof syncHdrMenuBtns==='function')syncHdrMenuBtns();
    if(typeof placeSidesHandles==='function')placeSidesHandles();"""


def patch(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    n = path.name
    if "fix-DESKTOP-FLIP-ARRANGE" in text and "function desktopArrangeSlotId" in text:
        print("skip", n)
        return
    text = sub(text, CSS_OLD, CSS_NEW, f"{n}: css")
    text = sub(text, HELPERS_OLD, HELPERS_NEW, f"{n}: helpers")
    text = sub(text, WRITE_FLIP_OLD, WRITE_FLIP_NEW, f"{n}: write-flip")
    text = sub(text, FLIP_ON_OLD, FLIP_ON_NEW, f"{n}: flip-on")
    text = sub(text, SYNC_SHOW_OLD, SYNC_SHOW_NEW, f"{n}: sync-show")
    text = sub(text, ENSURE_OLD, ENSURE_NEW, f"{n}: ensure-btn", optional=True)
    text = sub(text, TOGGLE_OLD, TOGGLE_NEW, f"{n}: toggle-desktop", optional=True)
    text = sub(text, TOGGLE_PORTABLE_OLD, TOGGLE_PORTABLE_NEW, f"{n}: toggle-portable", optional=True)
    text = sub(text, APPLY_MID_STRIP_OLD, APPLY_MID_STRIP_NEW, f"{n}: apply-portrait-middle", optional=True)
    text = sub(text, APPLY_MIDDLE_OLD, APPLY_MIDDLE_NEW, f"{n}: apply-middle")
    text = sub(text, SIDES_COLS_OLD, SIDES_COLS_NEW, f"{n}: sides-cols", optional=True)
    text = sub(text, APPLY_P_FLIP_OLD, APPLY_P_FLIP_NEW, f"{n}: apply-portrait-flip", optional=True)
    text = sub(text, SNAP_OLD, SNAP_NEW, f"{n}: snapshot")
    text = sub(text, APPLY_SNAP_OLD, APPLY_SNAP_NEW, f"{n}: apply-snap")
    text = sub(text, EXPAND_S_OLD, EXPAND_S_NEW, f"{n}: expand-s")
    text = sub(text, EXPAND_K_OLD, EXPAND_K_NEW, f"{n}: expand-k")
    raw = text.encode("utf-8")
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_bytes(raw)
    out = tmp.read_bytes().decode("utf-8")
    if not out.strip().endswith("</html>"):
        tmp.unlink()
        raise SystemExit(f"{n}: truncated")
    if len(raw) < 100000:
        tmp.unlink()
        raise SystemExit(f"{n}: size too small {len(raw)}")
    for keep in ("fix-MIDDLE-ONE-MENU", "fix-INDEX-ISOLATE-v3", "fix-FOLDER-GLYPH-SIZE-v2", "c00e3e"):
        if keep not in out:
            tmp.unlink()
            raise SystemExit(f"{n}: lost {keep}")
    tmp.replace(path)
    print("OK", n, len(raw))


def main() -> None:
    for p in FILES:
        if not p.exists():
            raise SystemExit(f"missing {p}")
        patch(p)


if __name__ == "__main__":
    main()
