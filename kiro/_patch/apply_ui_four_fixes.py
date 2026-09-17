#!/usr/bin/env python3
"""Patch KIRO catalog builders: remove Open Google strip, harden YT 153 UX,
Keywords safe padding, Layouts Save/Update click feedback."""
from pathlib import Path
import re
import shutil

KIRO_ART = Path("/home/phnx/KIRO/.kiro/specs/kontakt-workspace-drive-dirty-fix/artifacts")
REPO_ART = Path("/home/phnx/kiro-kontakt-patch/kiro/specs/kontakt-workspace-drive-dirty-fix/artifacts")
FILES = ["build-ds-catalog-html.sh", "build-kontakt-catalog-html.sh"]


def must_replace(text, old, new, label, count=1):
    n = text.count(old)
    if n == 0:
        raise SystemExit(f"MISSING [{label}]")
    if count is not None and n != count:
        raise SystemExit(f"COUNT [{label}]: expected {count}, found {n}")
    return text.replace(old, new, count if count is not None else n)


def patch_open_google(text):
    # Fallback CTA: Open in popup (header already covers opening Google)
    old_fb = (
        "reader.innerHTML='<div class=\"card-google-fallback\"><p>'+cardSearchEsc(note)+'</p>"
        "<button type=\"button\" onclick=\"event.preventDefault();event.stopPropagation();"
        "cardSearchOpenPopup()\">Open Google</button></div>';"
    )
    new_fb = (
        "reader.innerHTML='<div class=\"card-google-fallback\"><p>'+cardSearchEsc(note)+'</p>"
        "<button type=\"button\" onclick=\"event.preventDefault();event.stopPropagation();"
        "cardSearchOpenPopup()\">Open in popup</button></div>';"
    )
    text = must_replace(text, old_fb, new_fb, "google fallback CTA")

    # Remove footer strip + Open Google button; iframe only (header Open in popup remains)
    old_mount = """function cardSearchMountGoogleIframe(mode){
  var frame=cardSearchEnsureYtFrame();
  var fallback=document.getElementById('cardSearchFallback');
  var reader=cardSearchReaderEl();
  if(!frame){cardSearchShowGoogleFallback(mode);return false;}
  if(fallback)fallback.classList.remove('open');
  var url=cardGoogleEmbedUrl(mode);
  cardSearchState.embedUrl=url;
  cardSearchState.popupUrl=cardGooglePopupUrl(mode);
  // Keep a themed strip with Open Google even if the iframe hits consent/bot walls.
  if(reader){
    showCardSearchReader(true);
    var label=mode==='img'?'Google Images':'Google Search';
    reader.innerHTML='<div class="card-google-fallback" style="min-height:0;padding:10px 12px;flex:0 0 auto"><p style="max-width:none">'+cardSearchEsc(label)+' for “'+cardSearchEsc(cardGoogleQuery())+'”. If the panel below is blocked, use Open Google.</p><button type="button" onclick="event.preventDefault();event.stopPropagation();cardSearchOpenPopup()">Open Google</button></div>';
  }else{
    showCardSearchReader(false);
  }
  frame.classList.remove('is-hidden');
  frame.classList.add('card-google-frame');
  frame.style.display='';
  frame.title=mode==='img'?'Google Images':'Google Search';
  frame.removeAttribute('allow');
  frame.setAttribute('referrerpolicy','strict-origin-when-cross-origin');
  try{frame.referrerPolicy='strict-origin-when-cross-origin';}catch(err){}
  frame.src=url;
  showCardSearchFrame(true);
  return true;
}"""
    new_mount = """function cardSearchMountGoogleIframe(mode){
  var frame=cardSearchEnsureYtFrame();
  var fallback=document.getElementById('cardSearchFallback');
  if(!frame){cardSearchShowGoogleFallback(mode);return false;}
  if(fallback)fallback.classList.remove('open');
  showCardSearchReader(false);
  var url=cardGoogleEmbedUrl(mode);
  cardSearchState.embedUrl=url;
  cardSearchState.popupUrl=cardGooglePopupUrl(mode);
  // No footer strip — header Open in popup already covers opening Google.
  frame.classList.remove('is-hidden');
  frame.classList.add('card-google-frame');
  frame.style.display='';
  frame.title=mode==='img'?'Google Images':'Google Search';
  frame.removeAttribute('allow');
  frame.setAttribute('referrerpolicy','strict-origin-when-cross-origin');
  try{frame.referrerPolicy='strict-origin-when-cross-origin';}catch(err){}
  frame.src=url;
  showCardSearchFrame(true);
  return true;
}"""
    text = must_replace(text, old_mount, new_mount, "google mount no footer")
    # Button label / user-facing copy only (comments may mention the old control).
    if re.search(r">Open Google<", text) or "use Open Google" in text:
        raise SystemExit("Open Google CTA still present after patch")
    return text


YT_API_AND_SET = r'''function cardSearchYtCanEmbedHere(){
  try{
    if(location.protocol==='file:')return false;
    if(!location.origin||location.origin==='null')return false;
  }catch(err){return false;}
  return true;
}
function cardSearchEnsureYtApi(cb){
  if(window.YT&&YT.Player){if(cb)cb();return;}
  var q=window._catalogYtApiQ||(window._catalogYtApiQ=[]);
  if(cb)q.push(cb);
  var prev=window.onYouTubeIframeAPIReady;
  window.onYouTubeIframeAPIReady=function(){
    try{if(typeof prev==='function')prev();}catch(err){}
    var cbs=window._catalogYtApiQ||[];
    window._catalogYtApiQ=[];
    cbs.forEach(function(fn){try{fn();}catch(err){}});
  };
  if(document.getElementById('catalogYtIframeApi'))return;
  var s=document.createElement('script');
  s.id='catalogYtIframeApi';
  s.src='https://www.youtube.com/iframe_api';
  s.async=true;
  document.head.appendChild(s);
}
function cardSearchClearYtWatchdog(){
  if(cardSearchState&&cardSearchState._ytWatch){
    try{clearTimeout(cardSearchState._ytWatch);}catch(err){}
    cardSearchState._ytWatch=null;
  }
}
function cardSearchArmYtApiWatchdog(id){
  cardSearchClearYtWatchdog();
  cardSearchState._ytWatch=setTimeout(function(){
    if(!(cardSearchState&&cardSearchState.type==='yt'))return;
    if(cardSearchState.ytId!==id)return;
    if(cardSearchState._ytReady)return;
    // API never reached onReady — hide broken player, show thumbnail CTA.
    cardSearchYtTryNext('error 153');
  },5000);
}
function setCardYtFrame(id,host){
  var url=cardSearchYtPlayUrl(id,host);
  if(!url||cardSearchYtIsBadEmbedUrl(url))return false;
  if(!cardSearchYtCanEmbedHere()){
    cardSearchState.ytId=id;
    cardSearchState.embedUrl=url;
    cardSearchState.popupUrl=cardSearchState.popupUrl||('https://www.youtube.com/watch?v='+encodeURIComponent(id));
    showCardSearchFrame(false);
    cardSearchShowYtBlocked('file:// or null origin — YouTube needs HTTP(S) Referer');
    return true;
  }
  cardSearchClearYtWatchdog();
  if(cardSearchState._ytPlayer){
    try{cardSearchState._ytPlayer.destroy();}catch(err){}
    cardSearchState._ytPlayer=null;
  }
  var frame=cardSearchEnsureYtFrame();
  var fallback=document.getElementById('cardSearchFallback');
  if(!frame)return false;
  if(fallback)fallback.classList.remove('open');
  cardSearchState.ytId=id;
  cardSearchState._ytHost=String(host||cardSearchState._ytHost||'youtube')==='nocookie'?'nocookie':'youtube';
  cardSearchState.embedUrl=url;
  cardSearchState.history=[url];
  cardSearchState._ytReady=false;
  frame.classList.remove('is-hidden');
  frame.style.display='';
  frame.setAttribute('referrerpolicy','strict-origin-when-cross-origin');
  try{frame.referrerPolicy='strict-origin-when-cross-origin';}catch(err){}
  showCardSearchFrame(true);
  function mountPlain(){
    var f=document.getElementById('cardSearchFrame')||frame;
    if(!f)return;
    f.src=url;
  }
  function mountApi(){
    try{
      if(!(window.YT&&YT.Player)){mountPlain();return;}
      if(cardSearchState._ytPlayer){
        try{cardSearchState._ytPlayer.destroy();}catch(err){}
        cardSearchState._ytPlayer=null;
      }
      var f=cardSearchEnsureYtFrame();
      if(!f){mountPlain();return;}
      f.removeAttribute('src');
      f.setAttribute('referrerpolicy','strict-origin-when-cross-origin');
      try{f.referrerPolicy='strict-origin-when-cross-origin';}catch(err){}
      var origin=(location.origin&&location.origin!=='null')?location.origin:undefined;
      cardSearchState._ytPlayer=new YT.Player(f,{
        host:cardSearchState._ytHost==='nocookie'?'https://www.youtube-nocookie.com':'https://www.youtube.com',
        videoId:id,
        playerVars:{rel:0,modestbranding:1,playsinline:1,enablejsapi:1,origin:origin},
        events:{
          onReady:function(){cardSearchState._ytReady=true;cardSearchClearYtWatchdog();},
          onError:function(ev){
            var code=ev&&ev.data;
            if(code===153||code===150||code===101||code===100||code===2||code===5){
              if(cardSearchState&&cardSearchState.type==='yt')cardSearchYtTryNext('error '+code);
            }
          }
        }
      });
      cardSearchArmYtApiWatchdog(id);
    }catch(err){mountPlain();}
  }
  // Prefer IFrame API when already available (reliable onError for 153).
  // Otherwise plain embed + postMessage; preload API for the next play.
  if(window.YT&&YT.Player)mountApi();
  else{
    mountPlain();
    cardSearchEnsureYtApi(function(){});
  }
  return true;
}
'''


def patch_youtube(text):
    # Replace setCardYtFrame with API-aware version
    old_set = """function setCardYtFrame(id,host){
  var url=cardSearchYtPlayUrl(id,host);
  if(!url||cardSearchYtIsBadEmbedUrl(url))return false;
  var frame=cardSearchEnsureYtFrame();
  var fallback=document.getElementById('cardSearchFallback');
  if(!frame)return false;
  if(fallback)fallback.classList.remove('open');
  cardSearchState.ytId=id;
  cardSearchState._ytHost=String(host||cardSearchState._ytHost||'youtube')==='nocookie'?'nocookie':'youtube';
  cardSearchState.embedUrl=url;
  cardSearchState.history=[url];
  frame.classList.remove('is-hidden');
  frame.style.display='';
  frame.src=url;
  showCardSearchFrame(true);
  return true;
}"""
    if old_set not in text:
        raise SystemExit("MISSING setCardYtFrame")
    text = text.replace(old_set, YT_API_AND_SET, 1)

    # On 153: do not leave broken player cycling — go straight to thumbnail CTA
    old_try = """function cardSearchYtTryNext(reason){
  var items=cardSearchState.ytItems||[];
  var cur=cardSearchState.ytId||'';
  var tried=cardSearchState._ytTried||{};
  var hostTried=cardSearchState._ytHostTried||{};
  // On 153/config errors, retry same ID on the other embed host before advancing.
  // Prefer youtube.com first; fall back to nocookie only as alternate host.
  if(cur&&(/153|150|101|config/i.test(String(reason||'')))){
    var curHost=cardSearchState._ytHost||'youtube';
    var alt=curHost==='youtube'?'nocookie':'youtube';
    var hk=cur+'@'+alt;
    if(!hostTried[hk]){
      hostTried[hk]=1;
      cardSearchState._ytHostTried=hostTried;
      if(setCardYtFrame(cur,alt)){
        renderCardYtList(items,cur);
        return true;
      }
    }
  }
  if(cur)tried[cur]=1;
  cardSearchState._ytTried=tried;
  cardSearchState._ytHostTried=hostTried;
  for(var i=0;i<items.length;i++){
    var it=items[i];
    if(!it||!it.id||tried[it.id])continue;
    cardSearchState._ytHost='youtube';
    if(setCardYtFrame(it.id,'youtube')){
      renderCardYtList(items,it.id);
      return true;
    }
    tried[it.id]=1;
  }
  showCardSearchFrame(false);
  cardSearchShowYtBlocked(reason);
  return false;
}"""
    new_try = """function cardSearchYtTryNext(reason){
  var items=cardSearchState.ytItems||[];
  var cur=cardSearchState.ytId||'';
  var tried=cardSearchState._ytTried||{};
  var hostTried=cardSearchState._ytHostTried||{};
  var why=String(reason||'');
  cardSearchClearYtWatchdog();
  // Error 153 is Referer/policy — cycling videos keeps a broken Napaka 153 player.
  // One host swap, then thumbnail + Open in popup (same path as header).
  if(cur&&(/\\b153\\b|file:\\/\\/|null origin|watchdog|config/i.test(why))){
    var curHost=cardSearchState._ytHost||'youtube';
    var alt=curHost==='youtube'?'nocookie':'youtube';
    var hk=cur+'@'+alt;
    if(/\\b153\\b|watchdog|config/i.test(why)&&!hostTried[hk]&&!/file:\\/\\/|null origin/i.test(why)){
      hostTried[hk]=1;
      cardSearchState._ytHostTried=hostTried;
      // Prefer IFrame API path via setCardYtFrame; if still fails, blocked UI.
      if(setCardYtFrame(cur,alt)){
        renderCardYtList(items,cur);
        return true;
      }
    }
    showCardSearchFrame(false);
    cardSearchShowYtBlocked(why||'error 153');
    return false;
  }
  if(cur&&(/150|101/i.test(why))){
    var curHost2=cardSearchState._ytHost||'youtube';
    var alt2=curHost2==='youtube'?'nocookie':'youtube';
    var hk2=cur+'@'+alt2;
    if(!hostTried[hk2]){
      hostTried[hk2]=1;
      cardSearchState._ytHostTried=hostTried;
      if(setCardYtFrame(cur,alt2)){
        renderCardYtList(items,cur);
        return true;
      }
    }
  }
  if(cur)tried[cur]=1;
  cardSearchState._ytTried=tried;
  cardSearchState._ytHostTried=hostTried;
  for(var i=0;i<items.length;i++){
    var it=items[i];
    if(!it||!it.id||tried[it.id])continue;
    cardSearchState._ytHost='youtube';
    if(setCardYtFrame(it.id,'youtube')){
      renderCardYtList(items,it.id);
      return true;
    }
    tried[it.id]=1;
  }
  showCardSearchFrame(false);
  cardSearchShowYtBlocked(reason);
  return false;
}"""
    text = must_replace(text, old_try, new_try, "ytTryNext 153")

    # Soften blocked copy: emphasize popup path, keep 153 note
    old_note = (
        "var note='YouTube blocked in-card playback'+(reason?(' ('+reason+')'):'')+"
        "' for “'+(cardSearchState.name||'this library')+'”. Error 153 means missing Referer — open the popup player instead.';"
    )
    new_note = (
        "var note='In-card YouTube blocked'+(reason?(' ('+reason+')'):'')+"
        "' for “'+(cardSearchState.name||'this library')+'”. "
        "Error 153 = missing HTTP Referer (file:// or stripped referrer). Use Open in popup.';"
    )
    if old_note in text:
        text = must_replace(text, old_note, new_note, "yt blocked note")
    return text


def patch_keywords_padding(text):
    old_chrome = (
        "body.search-mode .search-chrome{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);"
        "grid-template-rows:none;gap:8px;align-items:start;justify-content:stretch;position:sticky;top:0;z-index:200;"
        "background:var(--bg-surface);padding-top:max(.5rem,env(safe-area-inset-top,0px));"
        "padding-left:max(.5rem,env(safe-area-inset-left,0px));"
        "padding-right:max(.5rem,env(safe-area-inset-right,0px));"
        "padding-bottom:10px;width:100%;max-width:100%;min-width:0;box-sizing:border-box;overflow-x:clip}"
    )
    new_chrome = (
        "body.search-mode .search-chrome{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);"
        "grid-template-rows:none;gap:8px;align-items:start;justify-content:stretch;position:sticky;top:0;z-index:200;"
        "background:var(--bg-surface);padding-top:max(.5rem,env(safe-area-inset-top,0px));"
        "padding-left:max(.75rem,calc(env(safe-area-inset-left,0px) + .5rem));"
        "padding-right:max(1rem,calc(env(safe-area-inset-right,0px) + .75rem));"
        "padding-bottom:10px;width:100%;max-width:100%;min-width:0;box-sizing:border-box;overflow-x:clip}"
    )
    text = must_replace(text, old_chrome, new_chrome, "search-chrome safe pad")

    old_toggle = (
        "body.search-mode .filter-wrap:not(.open) .filter-toggle{border:none;background:transparent;box-shadow:none;"
        "width:auto;max-width:100%;min-width:0;flex:0 1 auto;padding:.5rem .25rem;color:var(--text-muted);"
        "font-weight:600;justify-content:flex-end;text-align:right;overflow:hidden;text-overflow:ellipsis;"
        "white-space:nowrap;box-sizing:border-box}"
    )
    new_toggle = (
        "body.search-mode .filter-wrap:not(.open) .filter-toggle{border:none;background:transparent;box-shadow:none;"
        "width:auto;max-width:100%;min-width:0;flex:0 1 auto;"
        "padding:.5rem max(.5rem,env(safe-area-inset-right,0px)) .5rem .35rem;"
        "margin-right:0;color:var(--text-muted);"
        "font-weight:600;justify-content:flex-end;text-align:right;overflow:hidden;text-overflow:ellipsis;"
        "white-space:nowrap;box-sizing:border-box}"
    )
    text = must_replace(text, old_toggle, new_toggle, "keywords toggle pad")

    # Keep Keywords wrap inset from window edge when collapsed
    old_fw = (
        "body.search-mode .filter-wrap:not(.open){width:auto;max-width:100%;min-width:0;"
        "justify-self:end;flex:0 1 auto;overflow:hidden}"
    )
    new_fw = (
        "body.search-mode .filter-wrap:not(.open){width:auto;max-width:calc(100% - .25rem);min-width:0;"
        "justify-self:end;flex:0 1 auto;overflow:hidden;"
        "padding-right:max(.25rem,env(safe-area-inset-right,0px));box-sizing:border-box}"
    )
    text = must_replace(text, old_fw, new_fw, "filter-wrap collapsed pad")
    return text


def patch_layout_feedback(text):
    # CSS for pressed/flash
    old_css = (
        " .layout-presets-save button{flex:0 0 auto;min-height:2.25rem;padding:0 10px;"
        "border:1px solid var(--border);border-radius:6px;background:var(--bg-card);color:var(--text);"
        "font:inherit;cursor:pointer}"
    )
    new_css = (
        " .layout-presets-save button{flex:0 0 auto;min-height:2.25rem;padding:0 10px;"
        "border:1px solid var(--border);border-radius:6px;background:var(--bg-card);color:var(--text);"
        "font:inherit;cursor:pointer;touch-action:manipulation;transition:background .15s,border-color .15s,color .15s}"
        " .layout-presets-save button:active,.layout-presets-save button.is-pressed,"
        ".layout-presets-save button.is-flash{background:var(--accent-instrument-bg);color:var(--accent-instrument);"
        "border-color:var(--accent-instrument);font-weight:600}"
        " .layout-presets-flash{margin:6px 0 0;min-height:1.25em;font-size:.8125rem;font-weight:600;"
        "color:var(--accent-instrument);opacity:0;transition:opacity .15s}"
        " .layout-presets-flash.is-on{opacity:1}"
    )
    text = must_replace(text, old_css, new_css, "layout save CSS")

    # Insert flash element in popup HTML (inside layout-presets-save div, after Update button)
    old_html = (
        '<button type="button" id="layoutPresetsUpdate">Update Keywords layout</button></div></div>'
    )
    new_html = (
        '<button type="button" id="layoutPresetsUpdate">Update Keywords layout</button>'
        '<p class="layout-presets-flash" id="layoutPresetsFlash" aria-live="polite"></p></div></div>'
    )
    text = must_replace(text, old_html, new_html, "layout flash HTML", count=None)

    # JS helpers + wire into save/update clicks
    if "function flashLayoutSaveFeedback(" not in text:
        marker = "function saveNamedLayout(name,overwrite){"
        helper = r'''function flashLayoutSaveFeedback(kind){
  var save=document.getElementById('layoutPresetsSave');
  var upd=document.getElementById('layoutPresetsUpdate');
  var flash=document.getElementById('layoutPresetsFlash');
  var btn=kind==='update'?upd:save;
  var msg=kind==='update'?'Updated':'Saved';
  if(btn){
    btn.classList.add('is-pressed','is-flash');
    var prev=btn.getAttribute('data-label')||btn.textContent;
    btn.setAttribute('data-label',prev);
    btn.textContent=msg;
    clearTimeout(btn._flashT);
    btn._flashT=setTimeout(function(){
      btn.classList.remove('is-pressed','is-flash');
      var restore=btn.getAttribute('data-label');
      if(restore)btn.textContent=restore;
      if(typeof syncLayoutScopeUi==='function')syncLayoutScopeUi();
    },1100);
  }
  if(flash){
    flash.textContent=msg;
    flash.classList.add('is-on');
    clearTimeout(flash._flashT);
    flash._flashT=setTimeout(function(){flash.classList.remove('is-on');flash.textContent='';},1100);
  }
}
'''
        text = text.replace(marker, helper + marker, 1)

    old_handlers = """  if(save)save.addEventListener('click',function(e){
    e.preventDefault();e.stopPropagation();
    var inp=document.getElementById('layoutPresetsName');
    saveNamedLayout(inp&&inp.value);
  });
  if(upd)upd.addEventListener('click',function(e){
    e.preventDefault();e.stopPropagation();
    var inp=document.getElementById('layoutPresetsName');
    var n=(inp&&inp.value.replace(/^\\s+|\\s+$/g,''))||lastLayoutName();
    saveNamedLayout(n,true);
  });"""
    new_handlers = """  if(save)save.addEventListener('click',function(e){
    e.preventDefault();e.stopPropagation();
    save.classList.add('is-pressed');
    var inp=document.getElementById('layoutPresetsName');
    saveNamedLayout(inp&&inp.value);
    flashLayoutSaveFeedback('save');
  });
  if(upd)upd.addEventListener('click',function(e){
    e.preventDefault();e.stopPropagation();
    upd.classList.add('is-pressed');
    var inp=document.getElementById('layoutPresetsName');
    var n=(inp&&inp.value.replace(/^\\s+|\\s+$/g,''))||lastLayoutName();
    saveNamedLayout(n,true);
    flashLayoutSaveFeedback('update');
  });"""
    text = must_replace(text, old_handlers, new_handlers, "layout click feedback")
    return text


def patch_one(path: Path):
    text = path.read_text(encoding="utf-8")
    text = patch_open_google(text)
    text = patch_youtube(text)
    text = patch_keywords_padding(text)
    text = patch_layout_feedback(text)
    path.write_text(text, encoding="utf-8")
    print(f"patched {path}")


def main():
    for name in FILES:
        src = KIRO_ART / name
        if not src.exists():
            raise SystemExit(f"missing {src}")
        patch_one(src)
        dst = REPO_ART / name
        shutil.copy2(src, dst)
        print(f"synced -> {dst}")


if __name__ == "__main__":
    main()
