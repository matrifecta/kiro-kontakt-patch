#!/usr/bin/env python3
"""Desktop landscape: Search+Keywords stay side columns. Card name opens expand."""
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


CSS_OLD = """body.catalog-portable #hdrProfilesBtn{display:none!important}
@media(max-width:899px),(hover:none) and (pointer:coarse){
  #hdrProfilesBtn{display:none!important}
}"""

CSS_NEW = """body.catalog-portable #hdrProfilesBtn{display:none!important}
@media(max-width:899px),(hover:none) and (pointer:coarse){
  #hdrProfilesBtn{display:none!important}
}
/* fix-DESKTOP-SK-PAIR: landscape desktop Sides/Middle — menus are columns, never stacked bands */
@media(min-width:900px){
  body.desk-landscape.display-sides:not(.display-middle):not(.catalog-portable){
    display:grid!important;flex-direction:unset!important
  }
  body.desk-landscape.display-sides:not(.display-middle):not(.catalog-portable):not(.search-chrome-collapsed):not(.kw-chrome-collapsed){
    grid-template-columns:var(--sides-lw,22vw) minmax(0,1fr) var(--sides-rw,26vw)!important;
    grid-template-rows:auto minmax(0,1fr) var(--card-min-dock-h,0px)!important
  }
  body.desk-landscape.display-sides:not(.display-middle):not(.catalog-portable):not(.search-chrome-collapsed):not(.kw-chrome-collapsed) #searchChrome,
  body.desk-landscape.display-sides:not(.display-middle):not(.catalog-portable):not(.search-chrome-collapsed):not(.kw-chrome-collapsed) #filterWrap,
  body.desk-landscape.display-sides:not(.display-middle):not(.catalog-portable):not(.search-chrome-collapsed):not(.kw-chrome-collapsed) #catalogMain{
    grid-row:2!important;height:100%!important;max-height:none!important;min-height:0!important;
    align-self:stretch!important;position:relative!important;inset:auto!important;transform:none!important;
    width:100%!important;max-width:none!important;flex:unset!important
  }
  body.desk-landscape.display-sides:not(.display-middle):not(.catalog-portable):not(.search-chrome-collapsed):not(.kw-chrome-collapsed):not(.sides-portrait-flip) #searchChrome{grid-column:1!important}
  body.desk-landscape.display-sides:not(.display-middle):not(.catalog-portable):not(.search-chrome-collapsed):not(.kw-chrome-collapsed):not(.sides-portrait-flip) #catalogMain{grid-column:2!important}
  body.desk-landscape.display-sides:not(.display-middle):not(.catalog-portable):not(.search-chrome-collapsed):not(.kw-chrome-collapsed):not(.sides-portrait-flip) #filterWrap{grid-column:3!important}
  body.desk-landscape.display-sides:not(.display-middle):not(.catalog-portable).sides-portrait-flip:not(.search-chrome-collapsed):not(.kw-chrome-collapsed) #filterWrap{grid-column:1!important}
  body.desk-landscape.display-sides:not(.display-middle):not(.catalog-portable).sides-portrait-flip:not(.search-chrome-collapsed):not(.kw-chrome-collapsed) #catalogMain{grid-column:2!important}
  body.desk-landscape.display-sides:not(.display-middle):not(.catalog-portable).sides-portrait-flip:not(.search-chrome-collapsed):not(.kw-chrome-collapsed) #searchChrome{grid-column:3!important}
  body.desk-landscape.display-sides:not(.display-middle):not(.catalog-portable).search-chrome-collapsed:not(.kw-chrome-collapsed){
    grid-template-columns:minmax(0,1fr) var(--sides-rw,26vw)!important;
    grid-template-rows:auto minmax(0,1fr) var(--card-min-dock-h,0px)!important
  }
  body.desk-landscape.display-sides:not(.display-middle):not(.catalog-portable).search-chrome-collapsed:not(.kw-chrome-collapsed) #catalogMain{grid-column:1!important;grid-row:2!important}
  body.desk-landscape.display-sides:not(.display-middle):not(.catalog-portable).search-chrome-collapsed:not(.kw-chrome-collapsed) #filterWrap{grid-column:2!important;grid-row:2!important;height:100%!important;max-height:none!important}
  body.desk-landscape.display-sides:not(.display-middle):not(.catalog-portable).sides-portrait-flip.search-chrome-collapsed:not(.kw-chrome-collapsed){
    grid-template-columns:var(--sides-rw,26vw) minmax(0,1fr)!important
  }
  body.desk-landscape.display-sides:not(.display-middle):not(.catalog-portable).sides-portrait-flip.search-chrome-collapsed:not(.kw-chrome-collapsed) #filterWrap{grid-column:1!important}
  body.desk-landscape.display-sides:not(.display-middle):not(.catalog-portable).sides-portrait-flip.search-chrome-collapsed:not(.kw-chrome-collapsed) #catalogMain{grid-column:2!important}
  body.desk-landscape.display-sides:not(.display-middle):not(.catalog-portable).kw-chrome-collapsed:not(.search-chrome-collapsed){
    grid-template-columns:var(--sides-lw,22vw) minmax(0,1fr)!important;
    grid-template-rows:auto minmax(0,1fr) var(--card-min-dock-h,0px)!important
  }
  body.desk-landscape.display-sides:not(.display-middle):not(.catalog-portable).kw-chrome-collapsed:not(.search-chrome-collapsed) #searchChrome{grid-column:1!important;grid-row:2!important}
  body.desk-landscape.display-sides:not(.display-middle):not(.catalog-portable).kw-chrome-collapsed:not(.search-chrome-collapsed) #catalogMain{grid-column:2!important;grid-row:2!important}
  body.desk-landscape.display-sides:not(.display-middle):not(.catalog-portable).sides-portrait-flip.kw-chrome-collapsed:not(.search-chrome-collapsed){
    grid-template-columns:minmax(0,1fr) var(--sides-lw,22vw)!important
  }
  body.desk-landscape.display-sides:not(.display-middle):not(.catalog-portable).sides-portrait-flip.kw-chrome-collapsed:not(.search-chrome-collapsed) #catalogMain{grid-column:1!important}
  body.desk-landscape.display-sides:not(.display-middle):not(.catalog-portable).sides-portrait-flip.kw-chrome-collapsed:not(.search-chrome-collapsed) #searchChrome{grid-column:2!important}
  body.desk-landscape.display-sides.display-middle:not(.catalog-portable){
    display:grid!important;flex-direction:unset!important
  }
  body.desk-landscape.display-sides.display-middle:not(.catalog-portable):not(.search-chrome-collapsed):not(.kw-chrome-collapsed){
    grid-template-columns:minmax(0,var(--middle-lw,1fr)) minmax(0,var(--middle-rw,1fr))!important;
    grid-template-rows:auto var(--middle-menu-h,38dvh) minmax(0,1fr) var(--card-min-dock-h,0px)!important
  }
  body.desk-landscape.display-sides.display-middle:not(.catalog-portable):not(.search-chrome-collapsed):not(.kw-chrome-collapsed) #searchChrome,
  body.desk-landscape.display-sides.display-middle:not(.catalog-portable):not(.search-chrome-collapsed):not(.kw-chrome-collapsed) #filterWrap{
    grid-row:2!important;height:100%!important;max-height:none!important;min-height:0!important;
    width:100%!important;max-width:none!important;flex:unset!important;
    position:relative!important;inset:auto!important;transform:none!important
  }
  body.desk-landscape.display-sides.display-middle:not(.catalog-portable):not(.search-chrome-collapsed):not(.kw-chrome-collapsed) #catalogMain{
    grid-column:1/-1!important;grid-row:3!important;width:auto!important;max-width:none!important;flex:unset!important
  }
  body.desk-landscape.display-sides.display-middle:not(.catalog-portable):not(.search-chrome-collapsed):not(.kw-chrome-collapsed):not(.middle-kw-first):not(.sides-portrait-flip) #searchChrome{grid-column:1!important}
  body.desk-landscape.display-sides.display-middle:not(.catalog-portable):not(.search-chrome-collapsed):not(.kw-chrome-collapsed):not(.middle-kw-first):not(.sides-portrait-flip) #filterWrap{grid-column:2!important}
  body.desk-landscape.display-sides.display-middle:not(.catalog-portable):not(.search-chrome-collapsed):not(.kw-chrome-collapsed).middle-kw-first:not(.sides-portrait-flip) #filterWrap{grid-column:1!important}
  body.desk-landscape.display-sides.display-middle:not(.catalog-portable):not(.search-chrome-collapsed):not(.kw-chrome-collapsed).middle-kw-first:not(.sides-portrait-flip) #searchChrome{grid-column:2!important}
  body.desk-landscape.display-sides.display-middle:not(.catalog-portable):not(.search-chrome-collapsed):not(.kw-chrome-collapsed).sides-portrait-flip:not(.middle-kw-first) #searchChrome{grid-column:2!important}
  body.desk-landscape.display-sides.display-middle:not(.catalog-portable):not(.search-chrome-collapsed):not(.kw-chrome-collapsed).sides-portrait-flip:not(.middle-kw-first) #filterWrap{grid-column:1!important}
  body.desk-landscape.display-sides.display-middle:not(.catalog-portable):not(.search-chrome-collapsed):not(.kw-chrome-collapsed).sides-portrait-flip.middle-kw-first #searchChrome{grid-column:1!important}
  body.desk-landscape.display-sides.display-middle:not(.catalog-portable):not(.search-chrome-collapsed):not(.kw-chrome-collapsed).sides-portrait-flip.middle-kw-first #filterWrap{grid-column:2!important}
  body.desk-landscape.display-sides.display-middle:not(.catalog-portable).search-chrome-collapsed:not(.kw-chrome-collapsed),
  body.desk-landscape.display-sides.display-middle:not(.catalog-portable).kw-chrome-collapsed:not(.search-chrome-collapsed){
    display:grid!important;flex-direction:unset!important;
    grid-template-columns:minmax(0,1fr)!important;
    grid-template-rows:auto var(--middle-menu-h,38dvh) minmax(0,1fr)!important
  }
  body.desk-landscape.display-sides.display-middle:not(.catalog-portable).search-chrome-collapsed:not(.kw-chrome-collapsed) #filterWrap{
    display:flex!important;grid-column:1/-1!important;grid-row:2!important;width:100%!important;max-width:none!important;max-height:none!important
  }
  body.desk-landscape.display-sides.display-middle:not(.catalog-portable).kw-chrome-collapsed:not(.search-chrome-collapsed) #searchChrome{
    display:flex!important;grid-column:1/-1!important;grid-row:2!important;width:100%!important;max-width:none!important;max-height:none!important
  }
  body.desk-landscape.display-sides.display-middle:not(.catalog-portable).search-chrome-collapsed:not(.kw-chrome-collapsed) #catalogMain,
  body.desk-landscape.display-sides.display-middle:not(.catalog-portable).kw-chrome-collapsed:not(.search-chrome-collapsed) #catalogMain{
    grid-column:1/-1!important;grid-row:3!important;flex:unset!important
  }
}"""

CLICK_OLD = """    var nameHit=!!(e.target.closest&&e.target.closest('h3,.lib-name'));
    if(!nameHit&&typeof cardSelectNearInteractable==='function'&&cardSelectNearInteractable(entry,e.clientX,e.clientY,14))return;
    if(typeof selectCardFromEmpty==='function')selectCardFromEmpty(entry);
    else if(typeof rememberViewed==='function')rememberViewed(entry);
    e.preventDefault();
    return;"""

CLICK_NEW = """    var nameHit=!!(e.target.closest&&e.target.closest('h3,.lib-name,.lib-name-tip'));
    if(nameHit){
      try{fetch('http://127.0.0.1:7529/ingest/1cf46354-1d61-4c80-bd72-a340f1db1b51',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'c00e3e'},body:JSON.stringify({sessionId:'c00e3e',runId:'sk-pair',hypothesisId:'NAME',location:'catalog:cardNameClick',message:'name click expand',data:{id:entry&&entry.id,preview:document.body.classList.contains('chosen-preview-open')},timestamp:Date.now()})}).catch(function(){});}catch(eLog){}
      if(typeof openChosenPreview==='function')openChosenPreview(entry);
      e.preventDefault();
      return;
    }
    if(typeof cardSelectNearInteractable==='function'&&cardSelectNearInteractable(entry,e.clientX,e.clientY,14))return;
    if(typeof selectCardFromEmpty==='function')selectCardFromEmpty(entry);
    else if(typeof rememberViewed==='function')rememberViewed(entry);
    e.preventDefault();
    return;"""

PLACE_OLD = """  if(mode==='sides'){
    if(fw.parentElement!==body)body.insertBefore(fw, main||null);
    if(split&&split.parentElement!==body)body.insertBefore(split, fw);
    if(sep&&sep.parentElement!==body)body.insertBefore(sep, fw);
    if(ht&&ht.parentElement!==ch)ch.appendChild(ht);
  }else if(mode==='fs'){"""

PLACE_NEW = """  if(mode==='sides'){
    if(!window.CATALOG_PORTABLE){
      if(ch.parentElement!==body){if(main)body.insertBefore(ch,main);else body.appendChild(ch);}
      if(main&&fw.parentElement===main)body.insertBefore(fw,main);
    }
    if(fw.parentElement!==body)body.insertBefore(fw, main||null);
    if(split&&split.parentElement!==body)body.insertBefore(split, fw);
    if(sep&&sep.parentElement!==body)body.insertBefore(sep, fw);
    if(ht&&ht.parentElement!==ch)ch.appendChild(ht);
  }else if(mode==='fs'){"""

ORIENT_DESK_OLD = """  document.body.classList.toggle('sides-orient-portrait',!!portrait&&!middle);
  if(middle){"""

ORIENT_DESK_NEW = """  document.body.classList.toggle('sides-orient-portrait',!!portrait&&!middle);
  var deskNow=typeof displayIsDesktop==='function'?displayIsDesktop():!!(window.matchMedia&&window.matchMedia('(min-width:900px)').matches);
  document.body.classList.toggle('desk-landscape',!window.CATALOG_PORTABLE&&!!deskNow&&!portrait);
  if(!window.CATALOG_PORTABLE&&typeof placeMenusForDisplay==='function')placeMenusForDisplay('sides');
  try{var _fw=document.getElementById('filterWrap'),_ch=document.getElementById('searchChrome');fetch('http://127.0.0.1:7529/ingest/1cf46354-1d61-4c80-bd72-a340f1db1b51',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'c00e3e'},body:JSON.stringify({sessionId:'c00e3e',runId:'sk-pair',hypothesisId:'GEO',location:'catalog:applySidesCols',message:'desk sk pair',data:{desk:!!deskNow,portrait:!!portrait,middle:!!middle,flip:document.body.classList.contains('sides-portrait-flip'),land:document.body.classList.contains('desk-landscape'),sOn:!document.body.classList.contains('search-chrome-collapsed'),kOn:!document.body.classList.contains('kw-chrome-collapsed'),fwP:_fw&&_fw.parentElement&&(_fw.parentElement.id||_fw.parentElement.tagName),chP:_ch&&_ch.parentElement&&(_ch.parentElement.id||_ch.parentElement.tagName)},timestamp:Date.now()})}).catch(function(){});}catch(eLog){}
  if(middle){"""

ORIENT_PORT_OLD = """  document.body.classList.toggle('sides-orient-portrait',!!((portrait||(phone&&window.matchMedia&&window.matchMedia('(orientation:portrait)').matches))&&!middle));"""

ORIENT_PORT_NEW = """  document.body.classList.toggle('sides-orient-portrait',!!((portrait||(phone&&window.matchMedia&&window.matchMedia('(orientation:portrait)').matches))&&!middle));
  document.body.classList.toggle('desk-landscape',false);"""


def patch(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    n = path.name
    if "fix-DESKTOP-SK-PAIR" in text and "desk-landscape" in text and "name click expand" in text:
        print("skip", n)
        return
    text = sub(text, CSS_OLD, CSS_NEW, f"{n}: css")
    text = sub(text, CLICK_OLD, CLICK_NEW, f"{n}: name-click")
    text = sub(text, PLACE_OLD, PLACE_NEW, f"{n}: place-menus")
    text = sub(text, ORIENT_DESK_OLD, ORIENT_DESK_NEW, f"{n}: orient-desk", optional=True)
    text = sub(text, ORIENT_PORT_OLD, ORIENT_PORT_NEW, f"{n}: orient-port", optional=True)
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
    for keep in ("fix-MIDDLE-ONE-MENU", "fix-DESKTOP-FLIP-ARRANGE", "fix-USER-PROFILES", "c00e3e", "fix-DESKTOP-SK-PAIR"):
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
