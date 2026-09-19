#!/usr/bin/env python3
"""fix-DOCK-PILL-MEDIA-v1: stop the pinned-dock pill reflowing when a video plays.

Root cause (TODO 3b): `.card-min-media` was appended to `.card-min-pill` as a
SIBLING of `.card-min-open`, not as an overlay on the cover image. When
`.is-playing` toggled it from `display:none` to `display:block`, it inserted a
brand-new 2.15rem flex item into the pill's flex row (while the old cover `img`
was simultaneously removed from flow via `display:none`), so the pill's total
width changed and the name/close button visibly shifted -- read by the user as
"the disc knocks the name/image out of alignment" plus a blown-up YouTube
buffering spinner rendered into that newly-inserted box.

Fix: wrap the cover `img` in a new fixed-size `.card-min-cover` box and make
`.card-min-media` an absolutely-positioned overlay INSIDE that same box
(instead of a pill-level flex sibling). The pill's flex layout is now
independent of playback state -- the disc never adds/removes a flex item, the
cover image stays put underneath as the documented fallback, and the media
box is hard-clipped to the fixed 2.15rem circle so an oversized native
YouTube spinner cannot bleed out or reflow anything.
"""
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1] / 'public' / 'catalogs'
FILES = ['DS-CATALOG.html', 'DS-CATALOG-portable.html', 'KONTAKT-CATALOG.html', 'KONTAKT-CATALOG-portable.html']

CSS_OLD = "#cardMinDock .card-min-media{display:none;flex:0 0 auto;width:2.15rem;height:2.15rem;border-radius:999px;overflow:hidden;border:1px solid var(--border);background:#000;position:relative}\n#cardMinDock .card-min-pill.is-playing .card-min-media{display:block}\n#cardMinDock .card-min-pill.is-playing .card-min-open>img{display:none}\n"
CSS_NEW = (
    "#cardMinDock .card-min-cover{position:relative;flex:0 0 auto;width:2.15rem;height:2.15rem;border-radius:999px;overflow:hidden;border:1px solid var(--border);background:var(--bg-surface)}\n"
    "/* fix-DOCK-PILL-MEDIA-v1: media overlays the cover in-place, so playback never adds/removes a flex item from the pill */\n"
    "#cardMinDock .card-min-media{display:none;position:absolute;inset:0;width:100%;height:100%;border-radius:999px;overflow:hidden;background:#000;z-index:1;pointer-events:none}\n"
    "#cardMinDock .card-min-pill.is-playing .card-min-media{display:block}\n"
)

IMG_RULE_OLD = " #cardMinDock .card-min-pill img{width:2.15rem;height:2.15rem;border-radius:999px;object-fit:cover;flex:0 0 auto;border:1px solid var(--border);background:var(--bg-surface)}\n"
IMG_RULE_NEW = " #cardMinDock .card-min-cover img{position:absolute;inset:0;width:100%;height:100%;border-radius:999px;object-fit:cover;display:block}\n"

JS_COVER_OLD = """    var src=el?cardMinCoverSrc(el):'';
    if(src){
      var im=document.createElement('img');
      im.alt='';
      im.src=src;
      open.appendChild(im);
    }
    var sp=document.createElement('span');"""
JS_COVER_NEW = """    var cover=document.createElement('span');
    cover.className='card-min-cover';
    var src=el?cardMinCoverSrc(el):'';
    if(src){
      var im=document.createElement('img');
      im.alt='';
      im.src=src;
      cover.appendChild(im);
    }
    open.appendChild(cover);
    var sp=document.createElement('span');"""

JS_MEDIA_OLD = """    var media=document.createElement('span');
    media.className='card-min-media';
    media.setAttribute('aria-hidden','true');
    pill.appendChild(media);"""
JS_MEDIA_NEW = """    var media=document.createElement('span');
    media.className='card-min-media';
    media.setAttribute('aria-hidden','true');
    cover.appendChild(media);"""


def patch(path: pathlib.Path) -> None:
    html = path.read_text(encoding='utf-8')
    for old, new, label in (
        (CSS_OLD, CSS_NEW, 'css-media-rules'),
        (IMG_RULE_OLD, IMG_RULE_NEW, 'css-img-rule'),
        (JS_COVER_OLD, JS_COVER_NEW, 'js-cover-wrap'),
        (JS_MEDIA_OLD, JS_MEDIA_NEW, 'js-media-append'),
    ):
        if new in html:
            continue
        count = html.count(old)
        if count != 1:
            raise SystemExit(f"{path.name}: expected 1 match for {label}, found {count}")
        html = html.replace(old, new, 1)
    path.write_text(html, encoding='utf-8')
    print(f"{path.name}: patched")


def main() -> None:
    for name in FILES:
        patch(ROOT / name)


if __name__ == '__main__':
    main()
