#!/usr/bin/env python3
"""Add 5s themed embed hint toast (use Open in popup) for YT / Web / Images."""
from pathlib import Path
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


CSS = """ .card-search-hint{position:absolute;z-index:6;left:50%;top:max(.5rem,env(safe-area-inset-top,0px));transform:translateX(-50%) translateY(-6px);max-width:min(26rem,calc(100% - 1.5rem));box-sizing:border-box;padding:.625rem .75rem .625rem .875rem;border:1px solid var(--border);border-radius:999px;background:var(--bg-surface);color:var(--text);box-shadow:0 10px 28px rgba(0,0,0,.38);display:none;align-items:center;gap:.5rem;opacity:0;pointer-events:none;transition:opacity .2s,transform .2s}
 .card-search-hint.is-on{display:flex;opacity:1;pointer-events:auto;transform:translateX(-50%) translateY(0)}
 .card-search-hint-text{margin:0;flex:1 1 auto;min-width:0;font-size:.8125rem;line-height:1.35;color:var(--text)}
 .card-search-hint-text strong{color:var(--accent-instrument);font-weight:700}
 .card-search-hint-x{flex:0 0 auto;box-sizing:border-box;width:2rem;height:2rem;min-width:2rem;min-height:2rem;padding:0;border:1px solid var(--border);border-radius:999px;background:var(--bg-card);color:var(--text-muted);font:inherit;font-size:1.05rem;line-height:1;cursor:pointer;touch-action:manipulation}
 .card-search-hint-x:hover{border-color:var(--accent-instrument);color:var(--accent-instrument);background:var(--accent-instrument-bg)}
 .card-search-stage{position:relative}
"""

JS = r'''function cardSearchClearEmbedHint(){
  if(window._cardSearchHintT){try{clearTimeout(window._cardSearchHintT);}catch(err){} window._cardSearchHintT=null;}
  var el=document.getElementById('cardSearchHint');
  if(el){el.classList.remove('is-on');el.hidden=true;}
}
function cardSearchShowEmbedHint(){
  var el=document.getElementById('cardSearchHint');
  if(!el)return;
  cardSearchClearEmbedHint();
  el.hidden=false;
  el.classList.add('is-on');
  window._cardSearchHintT=setTimeout(function(){cardSearchClearEmbedHint();},5000);
}
window.cardSearchDismissEmbedHint=function(){
  cardSearchClearEmbedHint();
};
'''


def patch(text):
    if "function cardSearchShowEmbedHint(" in text and "id=\"cardSearchHint\"" in text:
        print("  embed hint already present")
        return text

    # CSS after card-search-chrome button:disabled
    needle_css = " .card-search-chrome button:disabled{opacity:.35;pointer-events:none}"
    if " .card-search-hint{" not in text:
        text = must_replace(text, needle_css, needle_css + "\n" + CSS.rstrip("\n"), "hint CSS")

    # HTML: toast inside stage (near chrome / top of embed)
    old_html = """  <div class="card-search-stage" id="cardSearchStage">
    <iframe class="card-search-frame" id="cardSearchFrame\""""
    new_html = """  <div class="card-search-stage" id="cardSearchStage">
    <div class="card-search-hint" id="cardSearchHint" hidden role="status" aria-live="polite">
      <p class="card-search-hint-text">If this embed doesn&rsquo;t work, use <strong>Open in popup</strong>.</p>
      <button type="button" class="card-search-hint-x" aria-label="Dismiss" onclick="event.preventDefault();event.stopPropagation();cardSearchDismissEmbedHint()">×</button>
    </div>
    <iframe class="card-search-frame" id="cardSearchFrame\""""
    text = must_replace(text, old_html, new_html, "hint HTML")

    # JS helpers before openCardSearchEmbed
    if "function cardSearchShowEmbedHint(" not in text:
        marker = "function openCardSearchEmbed(type,popupUrl){"
        text = must_replace(text, marker, JS + marker, "hint JS")

    # Show on open for yt/web/img
    old_open_end = """  paintCardSearchSwitch();
  syncCardSearchLayout();
  return true;
}
window.cardSearchBack=function(){"""
    new_open_end = """  paintCardSearchSwitch();
  syncCardSearchLayout();
  cardSearchShowEmbedHint();
  return true;
}
window.cardSearchBack=function(){"""
    text = must_replace(text, old_open_end, new_open_end, "hint on open")

    # Clear on close
    old_close = """function closeCardSearchEmbed(){
  var wrap=cardSearchHost();
  var fallback=document.getElementById('cardSearchFallback');
  if(fallback)fallback.classList.remove('open');
  resetCardSearchChrome();"""
    new_close = """function closeCardSearchEmbed(){
  cardSearchClearEmbedHint();
  var wrap=cardSearchHost();
  var fallback=document.getElementById('cardSearchFallback');
  if(fallback)fallback.classList.remove('open');
  resetCardSearchChrome();"""
    text = must_replace(text, old_close, new_close, "hint on close")

    return text


def main():
    for name in FILES:
        src = KIRO_ART / name
        text = src.read_text(encoding="utf-8")
        text = patch(text)
        src.write_text(text, encoding="utf-8")
        dst = REPO_ART / name
        shutil.copy2(src, dst)
        print(f"patched+synced {name}")


if __name__ == "__main__":
    main()
