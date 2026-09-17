#!/usr/bin/env python3
"""Patch KIRO catalog builders: Google embed, YT 153/referrer, layout Default."""
from pathlib import Path
import re
import shutil

ART = Path("/home/phnx/KIRO/.kiro/specs/kontakt-workspace-drive-dirty-fix/artifacts")
FILES = [ART / "build-ds-catalog-html.sh", ART / "build-kontakt-catalog-html.sh"]


def must_replace(text, old, new, label, count=1):
    n = text.count(old)
    if n == 0:
        raise SystemExit(f"MISSING [{label}]")
    if count is not None and n != count:
        raise SystemExit(f"COUNT [{label}]: expected {count}, found {n}")
    return text.replace(old, new, count if count is not None else n)


def replace_once_re(text, pattern, repl, label):
    new, n = re.subn(pattern, repl, text, count=1, flags=re.S | re.M)
    if n != 1:
        raise SystemExit(f"RE [{label}]: expected 1, found {n}")
    return new


LAYOUT_JS = r'''
function persistAllLiveLayouts(){
  try{if(typeof persist==='function')persist();}catch(err){}
  try{if(typeof persistHeight==='function')persistHeight();}catch(err){}
  try{if(typeof persistAcHeight==='function')persistAcHeight();}catch(err){}
  try{if(typeof persistAcWidth==='function')persistAcWidth();}catch(err){}
  try{if(typeof persistShadeHeight==='function')persistShadeHeight();}catch(err){}
}
function clearLiveLayoutKeys(so){
  try{
    if(so){
      localStorage.removeItem(KEYCH);localStorage.removeItem(KEYCV);
      localStorage.removeItem(KEYACSO);localStorage.removeItem(KEYACWSO);
      localStorage.removeItem(SEARCH_ONLY_UI_SCALE_KEY);
      setLastLayoutNameFor(true,'');
    }else{
      localStorage.removeItem(KEYH);localStorage.removeItem(KEYV);
      localStorage.removeItem(KEYHT+'-l');localStorage.removeItem(KEYHT+'-p');
      localStorage.removeItem(KEYAC);localStorage.removeItem(KEYSH);
      setLastLayoutNameFor(false,'');
    }
  }catch(err){}
}
function resetLayoutDefaults(){
  var so=searchOnlyStore();
  clearLiveLayoutKeys(so);
  if(so){
    try{document.documentElement.style.setProperty('--search-ui-scale','1');document.documentElement.setAttribute('data-search-ui-scale','100');}catch(err){}
  }
  var el=typeof chrome==='function'?chrome():null;
  var w=typeof wrap==='function'?wrap():null;
  var sh=typeof acShell==='function'?acShell():null;
  if(el&&typeof clearHeight==='function')clearHeight(el);
  if(w&&typeof clearShadeBox==='function')clearShadeBox(w);
  if(sh){
    sh.classList.remove('ac-height-set','ac-width-set','ac-height-dragging','ac-width-dragging');
    sh.style.height='';sh.style.maxHeight='';sh.style.width='';sh.style.maxWidth='';
  }
  if(typeof applyAll==='function')applyAll();
  else if(window.syncSearchSplit)window.syncSearchSplit();
  return true;
}
window.persistAllLiveLayouts=persistAllLiveLayouts;
window.resetLayoutDefaults=resetLayoutDefaults;
'''

GOOGLE_CSS = r'''
 .card-google-cse{flex:1 1 auto;min-height:0;width:100%;overflow:auto;-webkit-overflow-scrolling:touch;padding:8px 10px;box-sizing:border-box;background:var(--bg)}
 .card-google-cse .gsc-control-cse{background:transparent!important;border:0!important;padding:0!important}
 .card-google-frame{display:block;width:100%;height:100%;border:0;background:#fff;flex:1 1 auto;min-height:0}
 .card-google-fallback{display:flex;flex-direction:column;align-items:center;justify-content:center;gap:12px;padding:24px;text-align:center;min-height:12rem}
 .card-google-fallback p{margin:0;max-width:40ch;color:var(--text-muted)}
 .card-google-fallback button{min-height:2.75rem;padding:0 16px;border:1px solid var(--accent-instrument);border-radius:8px;background:var(--accent-instrument-bg);color:var(--accent-instrument);font:inherit;cursor:pointer;touch-action:manipulation}
 .card-yt-blocked{display:flex;flex-direction:column;align-items:center;gap:12px;max-width:min(28rem,92%);padding:8px}
 .card-yt-blocked-thumb{display:block;padding:0;border:1px solid var(--border);border-radius:10px;overflow:hidden;background:var(--bg);cursor:pointer;touch-action:manipulation;max-width:100%}
 .card-yt-blocked-thumb img{display:block;width:min(22rem,86vw);max-width:100%;height:auto;aspect-ratio:16/9;object-fit:cover}
'''

GOOGLE_JS = r'''
function cardGoogleQuery(){
  var name=libraryDisplayName();
  var extra=catalogSearchExtra();
  var q=(name?(name+' '+extra):String(cardSearchState.query||'')).replace(/^\s+|\s+$/g,'');
  return q||extra;
}
function cardGooglePopupUrl(mode){
  var q=cardGoogleQuery();
  if(mode==='img')return 'https://www.google.com/search?tbm=isch&q='+encodeURIComponent(q);
  return 'https://www.google.com/search?q='+encodeURIComponent(q);
}
function cardGoogleEmbedUrl(mode){
  // Undocumented but widely used: igu=1 allows Search UI in a cross-origin iframe (no XFO).
  // Official CSE needs a Programmable Search cx id; optional via window.CATALOG_GOOGLE_CSE_CX.
  var q=cardGoogleQuery();
  if(mode==='img')return 'https://www.google.com/search?igu=1&tbm=isch&q='+encodeURIComponent(q);
  return 'https://www.google.com/search?igu=1&q='+encodeURIComponent(q);
}
function cardGoogleCseCx(){
  try{
    if(window.CATALOG_GOOGLE_CSE_CX)return String(window.CATALOG_GOOGLE_CSE_CX);
    var ls=localStorage.getItem('catalog-google-cse-cx');
    if(ls)return String(ls);
  }catch(err){}
  return '';
}
function cardSearchShowGoogleFallback(mode,msg){
  var reader=cardSearchReaderEl();
  if(!reader)return;
  showCardSearchFrame(false);
  showCardSearchReader(true);
  var note=msg||('Google could not be embedded here. Open the full '+(mode==='img'?'image ':'')+'search in a popup.');
  reader.innerHTML='<div class="card-google-fallback"><p>'+cardSearchEsc(note)+'</p><button type="button" onclick="event.preventDefault();event.stopPropagation();cardSearchOpenPopup()">Open Google</button></div>';
}
function cardSearchMountGoogleIframe(mode){
  var frame=cardSearchEnsureYtFrame();
  var fallback=document.getElementById('cardSearchFallback');
  if(!frame){cardSearchShowGoogleFallback(mode);return false;}
  if(fallback)fallback.classList.remove('open');
  showCardSearchReader(false);
  var url=cardGoogleEmbedUrl(mode);
  frame.classList.remove('is-hidden');
  frame.classList.add('card-google-frame');
  frame.style.display='';
  frame.title=mode==='img'?'Google Images':'Google Search';
  frame.removeAttribute('allow');
  frame.setAttribute('referrerpolicy','strict-origin-when-cross-origin');
  try{frame.referrerPolicy='strict-origin-when-cross-origin';}catch(err){}
  frame.src=url;
  cardSearchState.embedUrl=url;
  cardSearchState.popupUrl=cardGooglePopupUrl(mode);
  showCardSearchFrame(true);
  return true;
}
function cardSearchMountGoogleCse(mode){
  var cx=cardGoogleCseCx();
  if(!cx)return false;
  var reader=cardSearchReaderEl();
  if(!reader)return false;
  showCardSearchFrame(false);
  showCardSearchReader(true);
  var q=cardGoogleQuery();
  cardSearchState.popupUrl=cardGooglePopupUrl(mode);
  reader.innerHTML='<div class="card-google-cse" id="cardGoogleCse"><div id="cardGoogleCseHost"></div></div>';
  function render(){
    try{
      if(!(window.google&&google.search&&google.search.cse&&google.search.cse.element))return false;
      var host=document.getElementById('cardGoogleCseHost');
      if(!host)return false;
      host.innerHTML='';
      var attrs={enableImageSearch:true};
      if(mode==='img'){attrs.defaultToImageSearch=true;attrs.disableWebSearch=true;}
      google.search.cse.element.render({div:host,tag:'searchresults-only',gname:'cardGoogle',attributes:attrs});
      var el=google.search.cse.element.getElement('cardGoogle');
      if(el&&el.execute)el.execute(q);
      return true;
    }catch(err){return false;}
  }
  if(window.google&&google.search&&google.search.cse){render();return true;}
  var prev=window.__gcse;
  window.__gcse={parsetags:'explicit',callback:function(){render();}};
  var s=document.createElement('script');
  s.async=true;
  s.src='https://cse.google.com/cse.js?cx='+encodeURIComponent(cx);
  s.onerror=function(){cardSearchMountGoogleIframe(mode)||cardSearchShowGoogleFallback(mode);};
  document.head.appendChild(s);
  setTimeout(function(){
    if(!(window.google&&google.search&&google.search.cse)){
      if(prev)window.__gcse=prev;
      cardSearchMountGoogleIframe(mode)||cardSearchShowGoogleFallback(mode);
    }
  },4000);
  return true;
}
function loadCardGoogleSearch(mode){
  mode=mode==='img'?'img':'web';
  cardSearchState.view=mode==='img'?'grid':'results';
  cardSearchState.history=[cardSearchState.view];
  cardSearchState.type=mode==='img'?'img':'web';
  cardSearchState.popupUrl=cardGooglePopupUrl(mode);
  var imgView=document.getElementById('cardSearchImgView');
  if(imgView)imgView.classList.remove('open');
  if(cardGoogleCseCx()&&cardSearchMountGoogleCse(mode))return;
  if(!cardSearchMountGoogleIframe(mode))cardSearchShowGoogleFallback(mode);
}
'''


def patch_toggle_layout(text):
    old = """function toggleLayoutEdit(){
  document.body.classList.toggle('layout-edit');
  syncLayoutEditBtn();
  if(window.syncSearchSplit)window.syncSearchSplit();
}"""
    new = """function toggleLayoutEdit(){
  var was=document.body.classList.contains('layout-edit');
  document.body.classList.toggle('layout-edit');
  if(was&&typeof persistAllLiveLayouts==='function')persistAllLiveLayouts();
  syncLayoutEditBtn();
  if(window.syncSearchSplit)window.syncSearchSplit();
}"""
    return must_replace(text, old, new, "toggleLayoutEdit")


def patch_save_named(text):
    old = """function saveNamedLayout(name,overwrite){
  var so=layoutScopeSo();
  if(so&&searchOnlyStore()){
    persistAcHeight();
    persistAcWidth();
  }
  name=String(name||'').replace(/^\\s+|\\s+$/g,'').slice(0,40);"""
    new = """function saveNamedLayout(name,overwrite){
  var so=layoutScopeSo();
  if(typeof persistAllLiveLayouts==='function')persistAllLiveLayouts();
  else if(so&&searchOnlyStore()){
    persistAcHeight();
    persistAcWidth();
  }
  name=String(name||'').replace(/^\\s+|\\s+$/g,'').slice(0,40);"""
    return must_replace(text, old, new, "saveNamedLayout")


def patch_layout_helpers(text):
    # Insert after KEYSH / KEYMAP block start — right before snapshotLayout is fine
    if "function persistAllLiveLayouts(" in text:
        return text
    marker = "function snapshotLayout(so){"
    if marker not in text:
        raise SystemExit("MISSING snapshotLayout marker")
    return text.replace(marker, LAYOUT_JS + "\n" + marker, 1)


def patch_css(text):
    needle = " .card-search-fallback button{min-height:2.75rem;padding:0 16px;border:1px solid var(--accent-instrument);border-radius:8px;background:var(--accent-instrument-bg);color:var(--accent-instrument);font:inherit;cursor:pointer;touch-action:manipulation}"
    if " .card-google-frame{" in text:
        return text
    if needle not in text:
        raise SystemExit("MISSING card-search-fallback button CSS")
    # Avoid duplicating yt-blocked if already present
    extra = GOOGLE_CSS
    if " .card-yt-blocked{" in text:
        extra = "\n".join(l for l in GOOGLE_CSS.splitlines() if "card-yt-blocked" not in l)
    return text.replace(needle, needle + "\n" + extra.rstrip("\n"), 1)


def patch_yt_play_url(text):
    # Normalize to youtube-first with comment about referrer/153
    old_nocookie_default = """  host=String(host||cardSearchState._ytHost||'nocookie');
  if(host!=='youtube')host='nocookie';"""
    new_yt_default = """  // Error 153 = missing HTTP Referer (Google docs), not primarily ads.
  // Prefer www.youtube.com; keep referrerpolicy + page meta strict-origin-when-cross-origin.
  host=String(host||cardSearchState._ytHost||'youtube');
  if(host!=='nocookie')host='youtube';"""
    if old_nocookie_default in text:
        text = must_replace(text, old_nocookie_default, new_yt_default, "yt host default")
    elif "host=String(host||cardSearchState._ytHost||'youtube');" in text:
        pass
    else:
        raise SystemExit("MISSING yt host default pattern")
    # Fix base URL order if still youtube-first branch inverted
    old_base = "var base=host==='youtube'?'https://www.youtube.com/embed/':'https://www.youtube-nocookie.com/embed/';"
    new_base = "var base=host==='nocookie'?'https://www.youtube-nocookie.com/embed/':'https://www.youtube.com/embed/';"
    if old_base in text:
        text = must_replace(text, old_base, new_base, "yt base url")
    return text


def patch_yt_nocookie_assigns(text):
    text = text.replace("cardSearchState._ytHost='nocookie';", "cardSearchState._ytHost='youtube';")
    text = text.replace("setCardYtFrame(it.id,'nocookie')", "setCardYtFrame(it.id,'youtube')")
    text = text.replace("setCardYtFrame(pick.id,'nocookie')", "setCardYtFrame(pick.id,'youtube')")
    text = text.replace("setCardYtFrame(known,'nocookie')", "setCardYtFrame(known,'youtube')")
    text = text.replace(
        "cardSearchState._ytHost=String(host||cardSearchState._ytHost||'nocookie')==='youtube'?'youtube':'nocookie';",
        "cardSearchState._ytHost=String(host||cardSearchState._ytHost||'youtube')==='nocookie'?'nocookie':'youtube';",
    )
    text = text.replace(
        "var curHost=cardSearchState._ytHost||'nocookie';",
        "var curHost=cardSearchState._ytHost||'youtube';",
    )
    return text


def ensure_yt_blocked(text):
    if "function cardSearchShowYtBlocked(" in text:
        return text
    # Insert before cardSearchShowStatus
    marker = "function cardSearchShowStatus(msg,showPopup){"
    block = r'''function cardSearchShowYtBlocked(reason){
  var fallback=document.getElementById('cardSearchFallback');
  var frame=document.getElementById('cardSearchFrame');
  var thumb='';
  var items=cardSearchState.ytItems||[];
  var cur=cardSearchState.ytId||'';
  for(var i=0;i<items.length;i++){
    if(items[i]&&items[i].id===cur&&items[i].thumb){thumb=items[i].thumb;break;}
  }
  if(!thumb&&items[0]&&items[0].thumb)thumb=items[0].thumb;
  if(frame){frame.classList.add('is-hidden');frame.removeAttribute('src');frame.style.display='none';}
  if(fallback){
    fallback.classList.add('open');
    var note='YouTube blocked in-card playback'+(reason?(' ('+reason+')'):'')+' for “'+(cardSearchState.name||'this library')+'”. Missing Referer causes error 153 — open the popup player instead.';
    var html='<div class="card-yt-blocked">';
    if(thumb)html+='<button type="button" class="card-yt-blocked-thumb" aria-label="Open YouTube in popup" onclick="event.preventDefault();event.stopPropagation();cardSearchOpenPopup()"><img src="'+cardSearchEsc(thumb)+'" alt=""></button>';
    html+='<p>'+cardSearchEsc(note)+'</p>';
    html+='<button type="button" onclick="event.preventDefault();event.stopPropagation();cardSearchOpenPopup()">Open in popup</button></div>';
    fallback.innerHTML=html;
  }else{
    cardSearchShowStatus('YouTube could not play an embed'+(reason?(' ('+reason+')'):'')+' for “'+(cardSearchState.name||'this library')+'”. Open in a popup instead.');
  }
}
'''
    if marker not in text:
        raise SystemExit("MISSING cardSearchShowStatus for YT blocked")
    return text.replace(marker, block + marker, 1)


def patch_yt_try_next_fallback(text):
    old = "showCardSearchFrame(false);\n  cardSearchShowStatus('YouTube could not play an embed'+(reason?(' ('+reason+')'):'')+' for “'+(cardSearchState.name||'this library')+'”. Open in a popup instead.');\n  return false;\n}"
    new = "showCardSearchFrame(false);\n  cardSearchShowYtBlocked(reason);\n  return false;\n}"
    if old in text:
        text = must_replace(text, old, new, "ytTryNext fallback")
    return text


def replace_web_image_loaders(text):
    # Replace loadCardWebSearch and loadCardImageSearch bodies by pointing callers and redefining functions.
    if "function loadCardGoogleSearch(" in text:
        return text
    # Insert Google helpers before loadCardWebSearch
    marker = "function loadCardWebSearch(query){"
    if marker not in text:
        raise SystemExit("MISSING loadCardWebSearch")
    text = text.replace(marker, GOOGLE_JS + "\nfunction loadCardWebSearch(query){", 1)

    # Replace loadCardWebSearch function entirely (keep cardSearchRenderImages for any leftover callers)
    text = replace_once_re(
        text,
        r"function loadCardWebSearch\(query\)\{.*?^function cardSearchRenderImages",
        "function loadCardWebSearch(query){\n  loadCardGoogleSearch('web');\n}\nfunction cardSearchRenderImages",
        "replace loadCardWebSearch",
    )
    text = replace_once_re(
        text,
        r"function loadCardImageSearch\(query\)\{.*?^function collectSearchUrls",
        "function loadCardImageSearch(query){\n  loadCardGoogleSearch('img');\n}\nfunction collectSearchUrls",
        "replace loadCardImageSearch",
    )
    return text


def patch_meta_referrer_comment(text):
    # Ensure meta referrer present (already is); add CSP-friendly note via data attr is unnecessary.
    if 'meta name="referrer" content="strict-origin-when-cross-origin"' not in text:
        text = text.replace(
            '<meta charset="utf-8">',
            '<meta charset="utf-8"><meta name="referrer" content="strict-origin-when-cross-origin">',
            1,
        )
    return text


def patch_file(path: Path):
    raw = path.read_text()
    bak = path.with_suffix(path.suffix + ".bak-google")
    if not bak.exists():
        shutil.copy2(path, bak)
    t = raw
    t = patch_meta_referrer_comment(t)
    t = patch_css(t)
    t = patch_yt_play_url(t)
    t = patch_yt_nocookie_assigns(t)
    t = patch_yt_try_next_fallback(t)
    t = ensure_yt_blocked(t)
    t = patch_toggle_layout(t)
    t = patch_layout_helpers(t)
    t = patch_save_named(t)
    t = replace_web_image_loaders(t)
    if t == raw:
        print(f"NO CHANGE {path.name}")
    else:
        path.write_text(t)
        print(f"PATCHED {path.name} ({len(raw)} -> {len(t)})")
    # sanity
    for need in [
        "loadCardGoogleSearch",
        "resetLayoutDefaults",
        "persistAllLiveLayouts",
        "cardSearchShowYtBlocked",
        "_ytHost='youtube'",
        "igu=1",
    ]:
        if need not in t:
            raise SystemExit(f"SANITY FAIL {path.name}: missing {need}")
    if "_ytHost='nocookie'" in t:
        raise SystemExit(f"SANITY FAIL {path.name}: leftover nocookie host assign")


def main():
    for f in FILES:
        patch_file(f)
    print("OK")


if __name__ == "__main__":
    main()
