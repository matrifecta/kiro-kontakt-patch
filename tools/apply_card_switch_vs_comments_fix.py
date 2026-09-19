#!/usr/bin/env python3
"""fix-CARD-SWITCH-VS-COMMENTS-v1

The floating "mode switch" bar (YouTube / Web / Image icons) on the Card
Search stage is `position:absolute; bottom:max(10px,4%)` -- anchored to the
STAGE's own bottom edge. That was correct back when the stage held only the
video/search result. Since the comments-pane feature landed, `yt-split` mode
stacks a tall, independently-scrolling comments list below the video inside
that same stage, so the stage's bottom edge is now the bottom of the
COMMENTS list, not the video. The switch bar still floats there, permanently
overlapping the bottom of the comments pane instead of sitting near the
video -- which is what a screenshot showed (a row of icons stamped over the
last visible comment).

Fix: in yt-split mode only, anchor the switch bar's position to the video
frame's own height (same clamp expression the frame uses) instead of the
stage's bottom, so it floats just below the video, above the comments pane,
same as it always did before the comments pane existed. yt-wide mode is
untouched -- there the frame spans the stage's full height already, so the
old bottom-of-stage anchor still lines up with the bottom of the video.
"""

FILES = [
    "public/catalogs/DS-CATALOG.html",
    "public/catalogs/DS-CATALOG-portable.html",
    "public/catalogs/KONTAKT-CATALOG.html",
    "public/catalogs/KONTAKT-CATALOG-portable.html",
]

ANCHOR = '.card-search-stage.yt-split .card-search-frame{flex:0 0 auto;height:min(46vh,56%);min-height:160px;max-height:64%}'
NEW = (
    ANCHOR +
    '\n/* fix-CARD-SWITCH-VS-COMMENTS-v1: float the mode switch over the video, not over the comments pane below it */\n'
    '.card-search-stage.yt-split .card-search-switch{bottom:auto;top:max(10px,calc(min(46vh,56%) - clamp(3.25rem,9vh,4.25rem) - 10px))}'
)


def main():
    for path in FILES:
        txt = open(path, encoding="utf-8").read()
        n = txt.count(ANCHOR)
        if n != 1:
            raise SystemExit(f"{path}: expected 1 match, got {n}")
        txt = txt.replace(ANCHOR, NEW, 1)
        open(path, "w", encoding="utf-8").write(txt)
        print(path, "ok")


if __name__ == "__main__":
    main()
