#!/usr/bin/env python3
"""Phone-only pin bottom-sheet + toolbar overflow menus.

Adds CSS only inside max-width 899px / coarse-pointer media, and JS only
behind isPhoneViewport(). Desktop pyramid, Save, Sides/Middle, header chrome
stay as-is. Does not commit.
"""
from pathlib import Path

ROOT = Path("/home/phnx/kiro-kontakt-patch")
FILES = [
    ROOT / "public/catalogs/DS-CATALOG.html",
    ROOT / "public/catalogs/KONTAKT-CATALOG.html",
    ROOT / "public/catalogs/DS-CATALOG-portable.html",
    ROOT / "public/catalogs/KONTAKT-CATALOG-portable.html",
    ROOT / "kiro/specs/kontakt-workspace-drive-dirty-fix/artifacts/build-ds-catalog-html.sh",
    ROOT / "kiro/specs/kontakt-workspace-drive-dirty-fix/artifacts/build-kontakt-catalog-html.sh",
]

CSS_MARK = "/* fix-MOBILE-PIN-SHEET: phone-only pin sheet + toolbar overflow */"
CSS_BEFORE = "/* fix-PORTRAIT-SIDES: desktop portrait A/B — stacked menus left or right, content the other side */"

CSS_ADD = r"""
.hdr-more-btn,.hdr-more-pop,.kw-strip-more,.kw-strip-more-pop{display:none}
/* fix-MOBILE-PIN-SHEET: phone-only pin sheet + toolbar overflow */
@media(max-width:899px),(hover:none) and (pointer:coarse){
  body .hdr-more-btn,body .kw-strip-more{display:inline-flex!important;flex:0 0 auto;align-items:center;justify-content:center;min-width:2.75rem;min-height:2.75rem;padding:0 .45rem;border:1px solid var(--border);border-radius:6px;background:var(--bg-card);color:var(--text);font:inherit;cursor:pointer}
  body .hdr-cluster .hdr-layout-btns,body .catalog-header .theme-picker,
  body .catalog-header #clearMissBtn,body.display-sides .catalog-header #clearMissBtn,
  body.display-sides.display-middle .catalog-header #clearMissBtn{display:none!important}
  body .hdr-more-pop .theme-picker{display:block!important;width:100%;max-width:none;min-height:2.75rem;margin:0}
  body .hdr-more-pop,body .kw-strip-more-pop,body #searchStripMorePop{
    position:absolute;z-index:360;display:flex;flex-direction:column;gap:.35rem;min-width:min(18rem,calc(100vw - 1.5rem));
    padding:.5rem;background:var(--bg-surface);border:1px solid var(--border);border-radius:8px;box-shadow:0 12px 28px rgba(0,0,0,.38)
  }
  body .hdr-more-pop{top:calc(100% + 4px);right:0;left:auto}
  body .kw-strip-more-pop{top:calc(100% + 4px);right:.35rem}
  body #searchStripMorePop{right:.35rem;top:calc(100% + 4px);left:auto}
  body .hdr-more-pop[hidden],body .kw-strip-more-pop[hidden],body #searchStripMorePop[hidden]{display:none!important}
  body .hdr-more-pop button,body .kw-strip-more-pop button,body #searchStripMorePop button{
    min-height:2.75rem;text-align:left;border:1px solid var(--border);border-radius:6px;background:var(--bg-card);color:var(--text);padding:.35rem .6rem;cursor:pointer;font:inherit
  }
  body .hdr-cluster{flex-wrap:wrap;overflow:visible;position:relative;justify-content:center}
  body #searchStripMore{display:inline-flex!important;margin-left:auto}
  body .search-strip .search-strip-clear,body .search-strip #searchHistoryWrap,body .search-strip .search-only-scale,body #searchOnlyScale{display:none!important}
  body .filter-top{position:relative;flex-wrap:nowrap;gap:.35rem}
  body .filter-kw-tools{display:none!important}
  body #cardMinDock.card-min-phone{
    flex-direction:column;justify-content:flex-end;align-items:stretch;padding:0;overflow:visible;pointer-events:none;left:0!important;width:100%!important
  }
  body #cardMinDock.card-min-phone .card-min-sheet{
    pointer-events:auto;display:flex;flex-direction:column;min-width:0;max-height:min(58dvh,28rem);
    background:var(--bg-surface);border-top:1px solid var(--border);border-radius:14px 14px 0 0;
    box-shadow:0 -10px 32px rgba(0,0,0,.4);padding:.15rem .7rem max(.55rem,env(safe-area-inset-bottom))
  }
  body #cardMinDock.card-min-phone .card-min-sheet-bar{display:flex;align-items:center;gap:.45rem;min-height:2.85rem;flex:0 0 auto}
  body #cardMinDock.card-min-phone .card-min-sheet-handle{
    flex:1 1 auto;min-width:0;min-height:2.75rem;display:inline-flex;align-items:center;justify-content:center;gap:.45rem;
    border:1px solid var(--border);border-radius:999px;background:var(--bg-card);color:var(--text);font:inherit;font-weight:650;cursor:pointer
  }
  body #cardMinDock.card-min-phone .card-min-sheet-grip{width:2.2rem;height:.28rem;border-radius:999px;background:var(--border)}
  body #cardMinDock.card-min-phone .card-min-save{position:static!important;left:auto!important;right:auto!important;bottom:auto!important;top:auto!important;flex:0 0 auto;box-shadow:none}
  body #cardMinDock.card-min-phone .card-min-stack{display:none!important}
  body #cardMinDock.card-min-phone:not(.is-sheet-open) .card-min-list{display:none}
  body #cardMinDock.card-min-phone.is-sheet-open .card-min-list{
    display:flex;flex-direction:column;gap:.4rem;overflow-y:auto;-webkit-overflow-scrolling:touch;min-height:0;padding:.15rem 0 .35rem
  }
  body #cardMinDock.card-min-phone .card-min-pill{max-width:none!important;width:100%;flex:0 0 auto}
  body #cardMinDock.card-min-phone #cardMinSavePop{left:auto;right:.7rem;transform:none;bottom:calc(100% + .4rem)}
  body.has-card-min-dock #catalogMain{padding-bottom:calc(var(--card-min-dock-h,3.25rem) + .5rem)}
}
"""

HDR_OLD = '</button></div><div class="display-switch" id="displaySwitch"'
HDR_NEW = (
    '</button></div><button type="button" class="hdr-more-btn" id="hdrMoreBtn" aria-expanded="false" '
    'aria-haspopup="true" title="More header controls" onclick="event.preventDefault();event.stopPropagation();'
    'toggleHdrMore()">&#x22EF;</button><div class="hdr-more-pop" id="hdrMorePop" hidden></div>'
    '<div class="display-switch" id="displaySwitch"'
)

KW_OLD = (
    '<button type="button" class="kw-fs-btn" id="kwStripFs" aria-pressed="false" '
    'aria-label="Fullscreen Keywords" title="Fullscreen Keywords" '
    'onclick="event.preventDefault();event.stopPropagation();toggleKwFullscreen()">&#x26F6;</button>'
)
KW_NEW = (
    '<button type="button" class="kw-strip-more" id="kwStripMore" aria-expanded="false" aria-haspopup="true" '
    'title="More keyword controls" onclick="event.preventDefault();event.stopPropagation();toggleKwStripMore()">'
    "&#x22EF;</button><div class=\"kw-strip-more-pop\" id=\"kwStripMorePop\" hidden></div>"
    + KW_OLD
)

MORE_JS = r"""
function closePhoneOverflowPops(except){
  [['hdrMorePop','hdrMoreBtn'],['kwStripMorePop','kwStripMore'],['searchStripMorePop','searchStripMore']].forEach(function(pair){
    if(except&&pair[0]===except)return;
    var p=document.getElementById(pair[0]);var b=document.getElementById(pair[1]);
    if(p)p.setAttribute('hidden','');
    if(b)b.setAttribute('aria-expanded','false');
  });
}
function phoneMoreAdd(pop,label,fn){
  var b=document.createElement('button');b.type='button';b.textContent=label;
  b.addEventListener('click',function(e){e.preventDefault();e.stopPropagation();closePhoneOverflowPops();fn();});
  pop.appendChild(b);
}
function toggleHdrMore(){
  if(!(typeof isPhoneViewport==='function'&&isPhoneViewport()))return;
  var pop=document.getElementById('hdrMorePop');var btn=document.getElementById('hdrMoreBtn');
  if(!pop||!btn)return;
  var open=pop.hasAttribute('hidden');
  closePhoneOverflowPops('hdrMorePop');
  if(!open){pop.setAttribute('hidden','');btn.setAttribute('aria-expanded','false');return;}
  pop.innerHTML='';
  phoneMoreAdd(pop,'Clear on miss',function(){var x=document.getElementById('clearMissBtn');if(x)x.click();});
  phoneMoreAdd(pop,'Customize',function(){if(typeof toggleLayoutEdit==='function')toggleLayoutEdit();});
  phoneMoreAdd(pop,'Layouts',function(){var x=document.getElementById('layoutPresetsBtn');if(x)x.click();});
  phoneMoreAdd(pop,'Smaller UI',function(){if(typeof stepUiScale==='function')stepUiScale(-1);});
  phoneMoreAdd(pop,'Larger UI',function(){if(typeof stepUiScale==='function')stepUiScale(1);});
  var sel=document.getElementById('themePicker');
  if(sel){
    var lab=document.createElement('label');lab.textContent='Theme';lab.style.fontSize='.85rem';
    var clone=sel.cloneNode(true);clone.id='hdrMoreTheme';clone.className='theme-picker';
    clone.value=sel.value;
    clone.addEventListener('change',function(){if(typeof setTheme==='function')setTheme(clone.value);sel.value=clone.value;});
    pop.appendChild(lab);pop.appendChild(clone);
  }
  pop.removeAttribute('hidden');btn.setAttribute('aria-expanded','true');
}
function toggleKwStripMore(){
  if(!(typeof isPhoneViewport==='function'&&isPhoneViewport()))return;
  var pop=document.getElementById('kwStripMorePop');var btn=document.getElementById('kwStripMore');
  if(!pop||!btn)return;
  var open=pop.hasAttribute('hidden');
  closePhoneOverflowPops('kwStripMorePop');
  if(!open){pop.setAttribute('hidden','');btn.setAttribute('aria-expanded','false');return;}
  pop.innerHTML='';
  phoneMoreAdd(pop,'Customize',function(){if(typeof toggleLayoutEdit==='function')toggleLayoutEdit();});
  phoneMoreAdd(pop,'Layouts',function(){var x=document.getElementById('layoutPresetsBtn');if(x)x.click();});
  phoneMoreAdd(pop,'Smaller UI',function(){if(typeof stepUiScale==='function')stepUiScale(-1);});
  phoneMoreAdd(pop,'Larger UI',function(){if(typeof stepUiScale==='function')stepUiScale(1);});
  phoneMoreAdd(pop,'Tap to add',function(){if(typeof toggleTapToAdd==='function')toggleTapToAdd();});
  phoneMoreAdd(pop,'Clear keywords',function(){if(typeof clearAllFilters==='function')clearAllFilters();});
  pop.removeAttribute('hidden');btn.setAttribute('aria-expanded','true');
}
window.toggleHdrMore=toggleHdrMore;
window.toggleKwStripMore=toggleKwStripMore;
document.addEventListener('click',function(e){
  if(!(typeof isPhoneViewport==='function'&&isPhoneViewport()))return;
  var t=e.target;
  if(t&&t.closest&&t.closest('#hdrMoreBtn,#hdrMorePop,#kwStripMore,#kwStripMorePop,#searchStripMore,#searchStripMorePop'))return;
  closePhoneOverflowPops();
});
"""

CAP_OLD = "var CARD_MIN_MAX=9;\nvar cardMinDockItems=[];"
CAP_NEW = """var CARD_MIN_MAX=9;
var CARD_MIN_PHONE_MAX=24;
function cardMinCap(){
  if(typeof isPhoneViewport==='function'&&isPhoneViewport())return CARD_MIN_PHONE_MAX;
  return typeof CARD_MIN_MAX==='number'?CARD_MIN_MAX:9;
}
var cardMinDockItems=[];"""


def sub(text, old, new, label, path, count=1):
    if old not in text:
        if new in text or (count == 1 and text.count(new) >= 1):
            print(f"  skip {path.name} {label}")
            return text
        raise SystemExit(f"{path.name}: {label} missing")
    n = text.count(old)
    if n != count:
        raise SystemExit(f"{path.name}: {label} count={n} expected {count}")
    return text.replace(old, new)


def main():
    for path in FILES:
        t = path.read_text(encoding="utf-8")
        if CSS_MARK in t:
            print(f"  skip {path.name} css")
        else:
            if CSS_BEFORE not in t:
                raise SystemExit(f"{path.name}: missing portrait-sides mark")
            t = t.replace(CSS_BEFORE, CSS_ADD + CSS_BEFORE, 1)
            print(f"  css {path.name}")

        t = sub(t, HDR_OLD, HDR_NEW, "hdr-more", path)
        t = sub(t, KW_OLD, KW_NEW, "kw-more", path)

        if "function toggleHdrMore()" not in t:
            needle = "window.toggleSearchStripMore=toggleSearchStripMore;\n"
            if needle not in t:
                raise SystemExit(f"{path.name}: missing toggleSearchStripMore export")
            t = t.replace(needle, needle + MORE_JS, 1)
            print(f"  more-js {path.name}")
        else:
            print(f"  skip {path.name} more-js")

        scale_old = (
            "    add('Smaller Search',function(){if(typeof stepSearchOnlyUiScale==='function')stepSearchOnlyUiScale(-1);});\n"
            "    add('Larger Search',function(){if(typeof stepSearchOnlyUiScale==='function')stepSearchOnlyUiScale(1);});\n"
            "    pop.removeAttribute('hidden');\n"
        )
        scale_new = (
            "    add('Smaller Search',function(){if(typeof stepSearchOnlyUiScale==='function')stepSearchOnlyUiScale(-1);});\n"
            "    add('Larger Search',function(){if(typeof stepSearchOnlyUiScale==='function')stepSearchOnlyUiScale(1);});\n"
            "    if(typeof isPhoneViewport==='function'&&isPhoneViewport()){\n"
            "      add('Clear search',function(){if(typeof clearAllFilters==='function')clearAllFilters();});\n"
            "      add('History',function(){var h=document.getElementById('searchHistory');if(h)h.click();});\n"
            "    }\n"
            "    pop.removeAttribute('hidden');\n"
        )
        t = sub(t, scale_old, scale_new, "search-more-phone", path)

        t = sub(t, CAP_OLD, CAP_NEW, "card-min-cap", path)
        t = sub(
            t,
            "  var max=typeof CARD_MIN_MAX==='number'?CARD_MIN_MAX:9;\n  var cards=[];\n",
            "  var max=typeof cardMinCap==='function'?cardMinCap():(typeof CARD_MIN_MAX==='number'?CARD_MIN_MAX:9);\n  var cards=[];\n",
            "snap-cap",
            path,
        )
        t = sub(
            t,
            "  var rec={id:front.id,mode:typeof cardMinMode==='function'?cardMinMode(front):'preview',kind:kind,name:typeof cardMinShortName==='function'?cardMinShortName(front):''};\n  var max=typeof CARD_MIN_MAX==='number'?CARD_MIN_MAX:9;\n",
            "  var rec={id:front.id,mode:typeof cardMinMode==='function'?cardMinMode(front):'preview',kind:kind,name:typeof cardMinShortName==='function'?cardMinShortName(front):''};\n  var max=typeof cardMinCap==='function'?cardMinCap():(typeof CARD_MIN_MAX==='number'?CARD_MIN_MAX:9);\n",
            "front-cap",
            path,
        )
        t = sub(
            t,
            "  var maxDock=typeof CARD_MIN_MAX==='number'?CARD_MIN_MAX:9;\n",
            "  var maxDock=typeof cardMinCap==='function'?cardMinCap():(typeof CARD_MIN_MAX==='number'?CARD_MIN_MAX:9);\n",
            "restore-cap",
            path,
        )
        t = sub(
            t,
            "    cardMinDockItems.push({id:frontId,mode:frontKind,kind:frontKind,name:''});\n    var max=typeof CARD_MIN_MAX==='number'?CARD_MIN_MAX:9;\n",
            "    cardMinDockItems.push({id:frontId,mode:frontKind,kind:frontKind,name:''});\n    var max=typeof cardMinCap==='function'?cardMinCap():(typeof CARD_MIN_MAX==='number'?CARD_MIN_MAX:9);\n",
            "restore-front-cap",
            path,
        )
        t = sub(
            t,
            "    if(cardMinDockItems.length>=CARD_MIN_MAX){\n",
            "    if(cardMinDockItems.length>=(typeof cardMinCap==='function'?cardMinCap():CARD_MIN_MAX)){\n",
            "min-cap",
            path,
        )

        fit_old = "function cardMinFitMenusForPins(){\n  if(window._cardMinFitting)return;\n"
        fit_new = """function cardMinFitMenusForPins(){
  if(typeof isPhoneViewport==='function'&&isPhoneViewport()){
    var n=(typeof cardMinDockItems!=='undefined'&&cardMinDockItems)?cardMinDockItems.length:0;
    var root=document.documentElement;var body=document.body;
    if(!n){root.style.setProperty('--card-min-dock-h','0px');body.classList.remove('has-card-min-dock');return;}
    body.classList.add('has-card-min-dock');
    var d=document.getElementById('cardMinDock');
    var h=d?Math.ceil(d.getBoundingClientRect().height):0;
    root.style.setProperty('--card-min-dock-h',(h>8?h:52)+'px');
    return;
  }
  if(window._cardMinFitting)return;
"""
        t = sub(t, fit_old, fit_new, "fit-phone", path)

        place_old = """function cardMinPlace(){
  if(typeof placeCatalogJumpStack==='function')placeCatalogJumpStack();
  var d=document.getElementById('cardMinDock');
  if(!d)return;
  if(typeof cardMinFitMenusForPins==='function')cardMinFitMenusForPins();
"""
        place_new = """function cardMinPlace(){
  if(typeof placeCatalogJumpStack==='function')placeCatalogJumpStack();
  var d=document.getElementById('cardMinDock');
  if(!d)return;
  if(typeof isPhoneViewport==='function'&&isPhoneViewport()){
    d.classList.add('card-min-phone');
    d.style.left='0';d.style.width='100%';d.style.bottom='0';
    if(typeof cardMinFitMenusForPins==='function')cardMinFitMenusForPins();
    var sheet=d.querySelector('.card-min-sheet');
    var sh=sheet?Math.ceil(sheet.getBoundingClientRect().height):Math.ceil(d.getBoundingClientRect().height);
    if(sh>8)document.documentElement.style.setProperty('--card-min-dock-h',sh+'px');
    return;
  }
  if(typeof cardMinFitMenusForPins==='function')cardMinFitMenusForPins();
"""
        t = sub(t, place_old, place_new, "place-phone", path)

        saveplace_old = """function cardMinPlaceSave(){
  var d=document.getElementById('cardMinDock');
  var sav=document.getElementById('cardMinDockSave');
  if(!d||!sav)return;
"""
        saveplace_new = """function cardMinPlaceSave(){
  var d=document.getElementById('cardMinDock');
  var sav=document.getElementById('cardMinDockSave');
  if(!d||!sav)return;
  if(typeof isPhoneViewport==='function'&&isPhoneViewport()){
    sav.style.removeProperty('left');sav.style.removeProperty('right');
    sav.style.removeProperty('bottom');sav.style.removeProperty('top');
    return;
  }
"""
        t = sub(t, saveplace_old, saveplace_new, "saveplace-phone", path)

        wrap_old = """  d.appendChild(sav);
  var pop=document.getElementById('cardMinSavePop');
  if(!pop){
    pop=document.createElement('div');
    pop.id='cardMinSavePop';
    pop.hidden=true;
    pop.innerHTML='<input id="cardMinSaveName" type="text" maxlength="40" placeholder="Session name" autocomplete="off"><button type="button" id="cardMinSaveGo">Save session</button>';
    d.appendChild(pop);
  }else d.appendChild(pop);
  cardMinPlace();
"""
        wrap_new = """  d.appendChild(sav);
  var pop=document.getElementById('cardMinSavePop');
  if(!pop){
    pop=document.createElement('div');
    pop.id='cardMinSavePop';
    pop.hidden=true;
    pop.innerHTML='<input id="cardMinSaveName" type="text" maxlength="40" placeholder="Session name" autocomplete="off"><button type="button" id="cardMinSaveGo">Save session</button>';
    d.appendChild(pop);
  }else d.appendChild(pop);
  if(typeof isPhoneViewport==='function'&&isPhoneViewport()){
    d.classList.add('card-min-phone');
    var sheetOpen=document.body.classList.contains('card-min-sheet-open');
    d.classList.toggle('is-sheet-open',sheetOpen);
    var sheet=document.createElement('div');sheet.className='card-min-sheet';
    var bar=document.createElement('div');bar.className='card-min-sheet-bar';
    var handle=document.createElement('button');handle.type='button';handle.className='card-min-sheet-handle';handle.id='cardMinSheetHandle';
    handle.setAttribute('aria-expanded',sheetOpen?'true':'false');
    var nPin=cardMinDockItems.length;
    handle.innerHTML='<span class="card-min-sheet-grip" aria-hidden="true"></span><span class="card-min-sheet-label">'+(nPin||0)+' '+(nPin===1?'pin':'pins')+'</span>';
    bar.appendChild(handle);
    if(sav.parentNode)sav.parentNode.removeChild(sav);
    bar.appendChild(sav);
    var list=document.createElement('div');list.className='card-min-list';list.id='cardMinList';
    if(stack.parentNode)stack.parentNode.removeChild(stack);
    while(stack.firstChild)list.appendChild(stack.firstChild);
    sheet.appendChild(bar);sheet.appendChild(list);
    d.insertBefore(sheet,d.firstChild);
    if(pop.parentNode)d.appendChild(pop);
  }else{
    d.classList.remove('card-min-phone','is-sheet-open');
  }
  cardMinPlace();
"""
        t = sub(t, wrap_old, wrap_new, "render-sheet", path)

        click_old = """    if(e.target.closest('#cardMinDockSave,.card-min-save')){
"""
        click_new = """    if(e.target.closest('#cardMinSheetHandle,.card-min-sheet-handle')){
      document.body.classList.toggle('card-min-sheet-open');
      var dock=document.getElementById('cardMinDock');
      if(dock)dock.classList.toggle('is-sheet-open',document.body.classList.contains('card-min-sheet-open'));
      var hh=document.getElementById('cardMinSheetHandle');
      if(hh)hh.setAttribute('aria-expanded',document.body.classList.contains('card-min-sheet-open')?'true':'false');
      if(typeof cardMinPlace==='function')cardMinPlace();
      e.preventDefault();e.stopPropagation();return;
    }
    if(e.target.closest('#cardMinDockSave,.card-min-save')){
"""
        t = sub(t, click_old, click_new, "click-handle", path)

        chrome_old = "  if(typeof syncLayoutEditBtn==='function')syncLayoutEditBtn();\n}\nfunction bindFsModeHandles(){"
        chrome_new = (
            "  if(typeof syncLayoutEditBtn==='function')syncLayoutEditBtn();\n"
            "  if(typeof isPhoneViewport==='function'&&isPhoneViewport()){\n"
            "    if(!document.getElementById('hdrMoreBtn')){\n"
            "      var cluster=document.getElementById('hdrCluster');\n"
            "      var sw=document.getElementById('displaySwitch');\n"
            "      if(cluster&&sw){\n"
            "        var hb=document.createElement('button');hb.type='button';hb.className='hdr-more-btn';hb.id='hdrMoreBtn';\n"
            "        hb.setAttribute('aria-expanded','false');hb.innerHTML='&#x22EF;';\n"
            "        hb.addEventListener('click',function(e){e.preventDefault();e.stopPropagation();toggleHdrMore();});\n"
            "        var hp=document.createElement('div');hp.className='hdr-more-pop';hp.id='hdrMorePop';hp.hidden=true;\n"
            "        cluster.insertBefore(hb,sw);cluster.insertBefore(hp,sw);\n"
            "      }\n"
            "    }\n"
            "    if(!document.getElementById('kwStripMore')){\n"
            "      var fs=document.getElementById('kwStripFs');var top=document.getElementById('filterTop');\n"
            "      if(fs&&top){\n"
            "        var kb=document.createElement('button');kb.type='button';kb.className='kw-strip-more';kb.id='kwStripMore';\n"
            "        kb.setAttribute('aria-expanded','false');kb.innerHTML='&#x22EF;';\n"
            "        kb.addEventListener('click',function(e){e.preventDefault();e.stopPropagation();toggleKwStripMore();});\n"
            "        var kp=document.createElement('div');kp.className='kw-strip-more-pop';kp.id='kwStripMorePop';kp.hidden=true;\n"
            "        top.insertBefore(kb,fs);top.insertBefore(kp,fs);\n"
            "      }\n"
            "    }\n"
            "  }\n"
            "}\nfunction bindFsModeHandles(){"
        )
        t = sub(t, chrome_old, chrome_new, "ensure-chrome", path)

        path.write_text(t, encoding="utf-8")
        print("ok", path.name)


if __name__ == "__main__":
    main()
