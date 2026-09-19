#!/usr/bin/env python3
"""fix-YT-PANE-v1: YouTube comments pane inside the expanded/fullscreen card.

- Before a video plays (list state) the pane is a vertical window on the right
  (stage.yt-wide); once a video is loaded it moves below the video (stage.yt-split).
- The pane's toggle is a thin yellow seam bar on the edge shared with the video
  (left edge in yt-wide, top edge in yt-split). Clicking it collapses the pane to
  the bar only and the video expands to fill the stage.
- The old toggle was width:100% inside a row flexbox and swallowed the pane, so
  the comments strip rendered at 0px.
"""
import sys, pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1] / 'public' / 'catalogs'
FILES = ['DS-CATALOG.html', 'DS-CATALOG-portable.html', 'KONTAKT-CATALOG.html', 'KONTAKT-CATALOG-portable.html']

CSS_ANCHOR = "/* Bug2-fix: constrain blocked-state fallback to the frame area so #cardYtComments stays visible */"
CSS = """/* fix-YT-PANE-v1: comments pane = yellow seam bar + scrollable strip; right of the video before play, below it while playing */
.card-search-stage.yt-wide .card-yt-comments,.card-search-stage.yt-split .card-yt-comments{display:flex;min-height:0;min-width:0;overflow:hidden;background:var(--bg-card)}
.card-search-stage.yt-wide .card-yt-comments{flex-direction:row;flex:0 0 clamp(14rem,34%,24rem);width:auto;max-width:none;border-left:0}
.card-search-stage.yt-split .card-yt-comments{flex-direction:column;flex:1 1 auto;width:100%;border-top:0}
.card-search-stage.yt-split .card-search-frame{flex:0 0 auto;height:min(46vh,56%);min-height:160px;max-height:64%}
.card-yt-comments .card-yt-comments-strip{flex:1 1 auto;min-height:0;min-width:0;overflow:auto}
.card-yt-comments .card-yt-list-toggle{flex:0 0 12px;min-height:0;width:auto;height:auto;padding:0;border:0;border-radius:0;font-size:0;line-height:0;color:transparent;background:var(--accent-instrument,#e8c84a);opacity:.85;cursor:pointer;position:relative;writing-mode:horizontal-tb}
.card-yt-comments .card-yt-list-toggle::after{content:"";position:absolute;left:50%;top:50%;transform:translate(-50%,-50%);border-radius:2px;background:rgba(0,0,0,.45)}
.card-search-stage.yt-wide .card-yt-list-toggle{width:12px;height:auto;align-self:stretch;border-right:1px solid var(--border)}
.card-search-stage.yt-wide .card-yt-list-toggle::after{width:3px;height:36px}
.card-search-stage.yt-split .card-yt-list-toggle{width:100%;height:12px;border-bottom:1px solid var(--border)}
.card-search-stage.yt-split .card-yt-list-toggle::after{width:36px;height:3px}
.card-yt-comments .card-yt-list-toggle:hover,.card-yt-comments .card-yt-list-toggle:focus-visible{opacity:1;background:var(--accent-instrument,#e8c84a)}
.card-search-stage.yt-list-collapsed.yt-wide .card-yt-comments{flex:0 0 12px;min-width:12px;width:12px}
.card-search-stage.yt-list-collapsed.yt-split .card-yt-comments{flex:0 0 12px;min-height:12px;height:12px}
.card-search-stage.yt-list-collapsed .card-yt-comments-strip{display:none!important}
.card-search-stage.yt-list-collapsed.yt-wide .card-yt-list-toggle{height:auto;border-right:0;writing-mode:horizontal-tb}
.card-search-stage.yt-list-collapsed.yt-split .card-search-frame{flex:1 1 auto;height:auto;max-height:none}
.card-search-stage.yt-list-collapsed.yt-split .card-search-fallback{height:auto;max-height:none;bottom:12px}
.card-search-stage.yt-split .card-search-fallback{height:min(46vh,56%);max-height:64%}
.card-search-stage.yt-wide .card-search-fallback{width:auto;right:clamp(14rem,34%,24rem)}
"""

JS_OLD = """  var yt=cardSearchState.type==='yt'&&document.body.classList.contains('card-embed-open');
  stage.classList.toggle('yt-split',false);
  stage.classList.toggle('yt-wide',!!yt);
  if(yt){fillYtCommentsStrip();cardRestoreYtListState();}"""
JS_NEW = """  var yt=cardSearchState.type==='yt'&&document.body.classList.contains('card-embed-open');
  /* fix-YT-PANE-v1: list state -> pane on the right (yt-wide); a loaded video -> pane below it (yt-split) */
  var playing=!!(yt&&cardSearchState.ytId);
  stage.classList.toggle('yt-split',playing);
  stage.classList.toggle('yt-wide',!!yt&&!playing);
  if(yt){fillYtCommentsStrip();cardRestoreYtListState();}"""

TOGGLE_OLD = """    btn.setAttribute('aria-label',hidden?'Show video list':'Hide video list');
    btn.title=hidden?'Expand list':'Collapse list';
    btn.textContent=hidden?'\\u203a':'\\u2039';"""
TOGGLE_NEW = """    btn.setAttribute('aria-label',hidden?'Show comments':'Hide comments');
    btn.title=hidden?'Show comments and related videos':'Hide comments and related videos';
    btn.textContent='';"""

# re-sync layout whenever a video id is set/cleared
SET1_OLD = "  cardSearchState.ytId=id;\n  loadCardYtComments(id);\n  var hostNorm="
SET1_NEW = "  cardSearchState.ytId=id;\n  if(typeof syncCardSearchLayout==='function')syncCardSearchLayout();\n  loadCardYtComments(id);\n  var hostNorm="
SET2_OLD = "    cardSearchState.ytId=id;\n    cardSearchState.embedUrl=url;\n    cardSearchState.popupUrl=cardSearchState.popupUrl||"
SET2_NEW = "    cardSearchState.ytId=id;\n    if(typeof syncCardSearchLayout==='function')syncCardSearchLayout();\n    cardSearchState.embedUrl=url;\n    cardSearchState.popupUrl=cardSearchState.popupUrl||"
BACK_OLD = """      if(typeof renderCardYtList==='function')renderCardYtList(cardSearchState.ytItems||[],'');
      cardSearchState.view='yt';
      return;"""
BACK_NEW = """      if(typeof renderCardYtList==='function')renderCardYtList(cardSearchState.ytItems||[],'');
      cardSearchState.view='yt';
      cardSearchState.ytId='';
      if(typeof syncCardSearchLayout==='function')syncCardSearchLayout();
      return;"""

def rep(s, old, new, name, path):
    n = s.count(old)
    if n != 1:
        sys.exit(f'{path.name}: {name} expected 1 match, got {n}')
    return s.replace(old, new)

for f in FILES:
    path = ROOT / f
    s = path.read_text(encoding='utf-8')
    s = rep(s, CSS_ANCHOR, CSS + CSS_ANCHOR, 'css anchor', path)
    s = rep(s, JS_OLD, JS_NEW, 'syncCardSearchLayout', path)
    s = rep(s, TOGGLE_OLD, TOGGLE_NEW, 'toggle labels', path)
    s = rep(s, SET1_OLD, SET1_NEW, 'setCardYtFrame ytId', path)
    s = rep(s, SET2_OLD, SET2_NEW, 'setCardYtFrame blocked ytId', path)
    s = rep(s, BACK_OLD, BACK_NEW, 'back to list', path)
    path.write_text(s, encoding='utf-8')
    print(f'{f}: patched')
