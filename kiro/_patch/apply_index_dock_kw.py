#!/usr/bin/env python3
"""Sides: index dock bar, Keywords full-height, working top button."""
from pathlib import Path
import shutil

KIRO = Path("/home/phnx/KIRO/.kiro/specs/kontakt-workspace-drive-dirty-fix/artifacts")
WS = Path("/home/phnx/kiro-kontakt-patch/kiro/specs/kontakt-workspace-drive-dirty-fix/artifacts")
PUB = Path("/home/phnx/kiro-kontakt-patch/public/catalogs")

CSS_HIDE_OLD = (
    "  body.display-sides > p,body.display-sides > a.top,body.display-sides #searchHeight,"
    "body.display-sides .search-height,body.display-sides #kwShadeHeight{display:none!important}"
)

KWBAR_OLD = "  body.display-sides #kwbar{overflow:visible!important;max-height:none!important;flex-wrap:wrap}"
KWBAR_NEW = "  body.display-sides #kwbar{flex:1 1 auto!important;min-height:0;max-height:none!important;overflow-x:hidden!important;overflow-y:auto!important;-webkit-overflow-scrolling:touch;overscroll-behavior:contain;touch-action:pan-y;align-content:flex-start;flex-wrap:wrap}"

CSS_HIDE_NEW = """  body.display-sides > p,body.display-sides #searchHeight,body.display-sides .search-height{display:none!important}
  body.display-sides:not(.layout-edit) #kwShadeHeight{display:none!important}
  body.display-sides.layout-edit #kwShadeHeight{display:block!important;position:absolute;left:0;right:0;bottom:0;z-index:6}
  body.display-sides #filterWrap{height:100%!important;max-height:none!important;align-self:stretch}
  body.display-sides #filterWrap.open .filter-panel,body.display-sides #filterWrap.kw-shade-height-set.open .filter-panel{display:flex!important;flex-direction:column;flex:1 1 auto!important;min-height:0!important;max-height:none!important}
  body.display-sides #filterWrap .filter-top,body.display-sides #filterWrap .filter-kw-tools,body.display-sides #filterWrap .mode-switch,body.display-sides #filterWrap .cat-switch,body.display-sides #filterWrap .kwstatus{flex:0 0 auto}
  body.display-sides #kwbar{flex:1 1 auto!important;min-height:0;max-height:none!important;overflow-x:hidden!important;overflow-y:auto!important;-webkit-overflow-scrolling:touch;overscroll-behavior:contain;touch-action:pan-y;align-content:flex-start;flex-wrap:wrap}
  body.display-sides #catalogMain{padding-top:0}
  body.display-sides #catalogIndex{position:sticky;top:0;z-index:12;margin:0 0 .75rem;display:flex;flex-direction:column;max-height:min(48dvh,28rem);overflow:hidden;border:1px solid var(--border);border-top-width:1px;border-radius:0 0 10px 10px;background:var(--bg-surface);box-shadow:0 10px 24px rgba(0,0,0,.32)}
  body.display-sides #catalogIndex .catalog-index-head{flex:0 0 auto;margin:0;padding:.4rem .65rem;cursor:pointer;border-bottom:1px solid var(--border);user-select:none}
  body.display-sides #catalogIndex.is-collapsed{max-height:none}
  body.display-sides #catalogIndex.is-collapsed .catalog-index-head{border-bottom:0}
  body.display-sides #catalogIndex .index,body.display-sides #catalogIndex #catalogIndexList{flex:1 1 auto;min-height:0;margin:0;padding:.45rem 1rem .65rem;overflow-x:hidden;overflow-y:auto;-webkit-overflow-scrolling:touch;overscroll-behavior:contain;touch-action:pan-y}
  body.display-sides a.top{display:block!important;position:fixed!important;z-index:25;bottom:1rem;right:calc(var(--sides-rw,26vw) + 1.25rem)}"""

SHADE_SKIP_OLD = """  if(!w)return;
  if(!shadeOn()){
    clearShadeBox(w);
    if(b)b.setAttribute('aria-hidden','true');
    return;
  }
"""

SHADE_SKIP_NEW = """  if(!w)return;
  if(document.body.classList.contains('display-sides')&&!(typeof layoutEdit==='function'&&layoutEdit())){
    if(typeof clearShadeBox==='function')clearShadeBox(w);
    if(b)b.setAttribute('aria-hidden','true');
    return;
  }
  if(!shadeOn()){
    clearShadeBox(w);
    if(b)b.setAttribute('aria-hidden','true');
    return;
  }
"""

TOGGLE_OLD = """window.toggleCatalogIndex=function(){
  var box=document.getElementById('catalogIndex');
  if(!box)return;
  var collapsed=box.classList.toggle('is-collapsed');
  var btn=document.getElementById('catalogIndexToggle');
  if(btn){
    btn.setAttribute('aria-expanded',collapsed?'false':'true');
    btn.setAttribute('aria-label',collapsed?'Expand index':'Collapse index');
    btn.title=collapsed?'Expand index':'Collapse index';
  }
"""

TOGGLE_NEW = """window.toggleCatalogIndex=function(){
  var box=document.getElementById('catalogIndex');
  if(!box)return;
  var collapsed=box.classList.toggle('is-collapsed');
  var btn=document.getElementById('catalogIndexToggle');
  if(btn){
    btn.setAttribute('aria-expanded',collapsed?'false':'true');
    btn.setAttribute('aria-label',collapsed?'Expand index':'Collapse index');
    btn.title=collapsed?'Expand index':'Collapse index';
  }
  if(document.body.classList.contains('display-sides')){
    box.dataset.dockAuto='';
    box.dataset.dockPin=collapsed?'':'1';
  }
"""

SIDES_OPEN_OLD = """    var fw=document.getElementById('filterWrap');
    if(fw){fw.classList.add('open');document.body.classList.add('kw-open');}
"""

SIDES_OPEN_NEW = """    var fw=document.getElementById('filterWrap');
    if(fw){
      fw.classList.add('open');document.body.classList.add('kw-open');
      if(typeof clearShadeBox==='function')clearShadeBox(fw);
      fw.style.removeProperty('height');fw.style.removeProperty('max-height');
    }
    if(typeof bindIndexDock==='function')bindIndexDock();
    if(typeof bindCatalogTop==='function')bindCatalogTop();
"""

DOCK_JS = r"""
function syncIndexToggleUi(box){
  if(!box)box=document.getElementById('catalogIndex');
  var btn=document.getElementById('catalogIndexToggle');
  if(!box||!btn)return;
  var collapsed=box.classList.contains('is-collapsed');
  btn.setAttribute('aria-expanded',collapsed?'false':'true');
  btn.setAttribute('aria-label',collapsed?'Expand index':'Collapse index');
  btn.title=collapsed?'Expand index':'Collapse index';
}
function syncIndexDock(){
  var ix=document.getElementById('catalogIndex');
  var cm=document.getElementById('catalogMain');
  if(!ix||!cm)return;
  if(!document.body.classList.contains('display-sides')){
    ix.dataset.dockAuto='';
    return;
  }
  var y=cm.scrollTop;
  var before=ix.classList.contains('is-collapsed')+'|'+(ix.dataset.dockAuto||'')+'|'+(ix.dataset.dockPin||'');
  if(y<=12){
    if(ix.dataset.dockAuto==='1'){
      ix.classList.remove('is-collapsed');
      ix.dataset.dockAuto='';
      syncIndexToggleUi(ix);
    }
  }else if(y>48&&!ix.classList.contains('is-collapsed')&&ix.dataset.dockPin!=='1'){
    ix.classList.add('is-collapsed');
    ix.dataset.dockAuto='1';
    syncIndexToggleUi(ix);
  }
  var after=ix.classList.contains('is-collapsed')+'|'+(ix.dataset.dockAuto||'')+'|'+(ix.dataset.dockPin||'');
  // #region agent log
  if(before!==after)fetch('http://127.0.0.1:7529/ingest/1cf46354-1d61-4c80-bd72-a340f1db1b51',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'f491c2'},body:JSON.stringify({sessionId:'f491c2',runId:'post-fix',hypothesisId:'H6',location:'syncIndexDock',message:'index-dock',data:{y:Math.round(y),collapsed:ix.classList.contains('is-collapsed'),auto:ix.dataset.dockAuto||'',pin:ix.dataset.dockPin||'',ixH:Math.round(ix.getBoundingClientRect().height)},timestamp:Date.now()})}).catch(function(){});
  // #endregion
}
function bindIndexDock(){
  var cm=document.getElementById('catalogMain');
  var ix=document.getElementById('catalogIndex');
  if(!cm||!ix)return;
  if(!cm.dataset.indexDockBound){
    cm.dataset.indexDockBound='1';
    cm.addEventListener('scroll',syncIndexDock,{passive:true});
  }
  if(!ix.dataset.indexHeadBound){
    ix.dataset.indexHeadBound='1';
    var head=ix.querySelector('.catalog-index-head');
    if(head)head.addEventListener('click',function(e){
      if(!document.body.classList.contains('display-sides'))return;
      if(e.target.closest&&e.target.closest('#catalogIndexToggle'))return;
      if(typeof toggleCatalogIndex==='function')toggleCatalogIndex();
    });
  }
  syncIndexDock();
}
function bindCatalogTop(){
  var top=document.querySelector('a.top');
  if(!top||top.dataset.sidesTopBound)return;
  top.dataset.sidesTopBound='1';
  top.addEventListener('click',function(e){
    if(!document.body.classList.contains('display-sides'))return;
    e.preventDefault();
    var cm=document.getElementById('catalogMain');
    if(cm){try{cm.scrollTo({top:0,behavior:'smooth'});}catch(err){cm.scrollTop=0;}}
    var ix=document.getElementById('catalogIndex');
    if(ix){
      ix.classList.remove('is-collapsed');
      ix.dataset.dockAuto='';
      ix.dataset.dockPin='';
      syncIndexToggleUi(ix);
    }
    // #region agent log
    fetch('http://127.0.0.1:7529/ingest/1cf46354-1d61-4c80-bd72-a340f1db1b51',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'f491c2'},body:JSON.stringify({sessionId:'f491c2',runId:'post-fix',hypothesisId:'H8',location:'bindCatalogTop',message:'sides-top-click',data:{cmTop:cm?Math.round(cm.scrollTop):null,ixH:ix?Math.round(ix.getBoundingClientRect().height):null},timestamp:Date.now()})}).catch(function(){});
    // #endregion
  });
}
"""

PLACE_FN = "function placeMenusForDisplay(mode){"


def patch_builder(text, name):
    n = 0
    if CSS_HIDE_OLD not in text:
        if "body.display-sides #catalogIndex{position:sticky" in text:
            print(f"{name}: dock CSS already present")
        else:
            raise SystemExit(f"{name}: hide/top CSS marker missing")
    else:
        text = text.replace(CSS_HIDE_OLD, CSS_HIDE_NEW, 1)
        n += 1
    if KWBAR_OLD in text:
        text = text.replace(KWBAR_OLD, KWBAR_NEW, 1)
        n += 1
    if SHADE_SKIP_OLD not in text:
        if "display-sides')&&!(typeof layoutEdit" in text:
            print(f"{name}: shade skip already present")
        else:
            raise SystemExit(f"{name}: applyShadeHeight skip marker missing")
    else:
        text = text.replace(SHADE_SKIP_OLD, SHADE_SKIP_NEW, 1)
        n += 1
    if TOGGLE_OLD not in text:
        if "box.dataset.dockPin" in text:
            print(f"{name}: toggle dock pin already present")
        else:
            raise SystemExit(f"{name}: toggleCatalogIndex marker missing")
    else:
        text = text.replace(TOGGLE_OLD, TOGGLE_NEW, 1)
        n += 1
    if SIDES_OPEN_OLD not in text:
        if "bindIndexDock" in text and "clearShadeBox(fw)" in text:
            print(f"{name}: sides open bind already present")
        else:
            raise SystemExit(f"{name}: sides open marker missing")
    else:
        text = text.replace(SIDES_OPEN_OLD, SIDES_OPEN_NEW, 1)
        n += 1
    if "function bindIndexDock()" not in text:
        if PLACE_FN not in text:
            raise SystemExit(f"{name}: placeMenusForDisplay missing")
        text = text.replace(PLACE_FN, DOCK_JS + PLACE_FN, 1)
        n += 1
    print(f"{name}: replacements {n}")
    return text


def extract_display_css(ds):
    a = ds.find("  body.display-sides{max-width:none")
    b = ds.find("</style></head><body>", a)
    if a < 0 or b < 0:
        raise SystemExit("display CSS missing in DS builder")
    return ds[a:b]


def extract_display_js(ds):
    a = ds.find("var DISPLAY_KEY='catalog-display-mode-")
    b = ds.find("\n</script>", a)
    if a < 0 or b < 0:
        raise SystemExit("display JS missing in DS builder")
    return ds[a:b]


def patch_html(text, name, new_css, new_js):
    a = text.find("  body.display-sides{max-width:none")
    if a < 0:
        a = text.find(" body.display-sides{max-width:none")
    style_end = text.find("</style></head><body>")
    if a < 0 or style_end < 0:
        raise SystemExit(f"display-sides CSS missing in {name}")
    text = text[:a] + new_css + text[style_end:]

    if KWBAR_OLD in text:
        text = text.replace(KWBAR_OLD, KWBAR_NEW, 1)
    if SHADE_SKIP_OLD in text:
        text = text.replace(SHADE_SKIP_OLD, SHADE_SKIP_NEW, 1)
    elif "display-sides')&&!(typeof layoutEdit" not in text:
        raise SystemExit(f"applyShadeHeight skip missing in {name}")

    if TOGGLE_OLD in text:
        text = text.replace(TOGGLE_OLD, TOGGLE_NEW, 1)
    elif "box.dataset.dockPin" not in text:
        raise SystemExit(f"toggleCatalogIndex missing in {name}")

    mark = "var DISPLAY_KEY='catalog-display-mode-"
    ja = text.find(mark)
    jb = text.find("\n</script>", ja)
    if ja < 0 or jb < 0:
        raise SystemExit(f"DISPLAY_KEY missing in {name}")
    text = text[:ja] + new_js + text[jb:]

    if "</html>" not in text or "function hideSearchAc" not in text:
        raise SystemExit(f"truncated {name}")
    if "function bindIndexDock" not in text:
        raise SystemExit(f"bindIndexDock missing in {name}")
    if "body.display-sides #catalogIndex{position:sticky" not in text:
        raise SystemExit(f"index dock CSS missing in {name}")
    if "body.display-sides > a.top" in text and "body.display-sides a.top{display:block" not in text:
        raise SystemExit(f"a.top still hidden in {name}")
    return text


def main():
    for name in ("build-ds-catalog-html.sh", "build-kontakt-catalog-html.sh"):
        src = KIRO / name
        text = src.read_text(encoding="utf-8")
        out = patch_builder(text, name)
        src.write_text(out, encoding="utf-8")
        shutil.copy2(src, WS / name)
        print("copied", name)

    ds = (KIRO / "build-ds-catalog-html.sh").read_text(encoding="utf-8")
    new_css = extract_display_css(ds)
    new_js = extract_display_js(ds)
    if "function bindIndexDock" not in new_js:
        raise SystemExit("display JS extract missing bindIndexDock")
    if "body.display-sides #catalogIndex{position:sticky" not in new_css:
        raise SystemExit("display CSS extract missing index dock")

    for path in [
        PUB / "DS-CATALOG.html",
        PUB / "DS-CATALOG-portable.html",
        PUB / "KONTAKT-CATALOG.html",
        PUB / "KONTAKT-CATALOG-portable.html",
        WS / "DS-CATALOG.html",
        WS / "DS-CATALOG-portable.html",
        WS / "KONTAKT-CATALOG.html",
        WS / "KONTAKT-CATALOG-portable.html",
    ]:
        raw = path.read_text(encoding="utf-8")
        out = patch_html(raw, path.name, new_css, new_js)
        path.write_text(out, encoding="utf-8")
        print("synced", path.name, len(out))


if __name__ == "__main__":
    main()
