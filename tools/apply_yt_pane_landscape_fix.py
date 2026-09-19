#!/usr/bin/env python3
"""
fix-YT-PANE-LANDSCAPE-v1

The card's embedded YouTube comments/related-videos pane switches layout
based on playback state: list-only -> pane on the right (yt-wide), a
loaded/playing video -> pane below it (yt-split), added in the
fix-YT-PANE-v1 round. That "below" placement wastes horizontal room once
the device (or window) is in landscape, where there is plenty of width
to keep the pane on the right instead.

A cardSearchIsLandscape() helper already existed in the file (checking
matchMedia('(orientation: landscape)') with a width>height fallback), and
an orientationchange/resize/matchMedia listener already re-calls
syncCardSearchLayout() on rotation -- but the landscape check itself was
never actually wired into the yt-split/yt-wide decision, so it had no
effect. This patch is the missing connection: while a video is playing,
landscape now keeps the pane on the right (yt-wide) instead of dropping
it below (yt-split); portrait keeps the original below-the-video
placement while playing.

Applies identically to all 4 catalog files.
"""
import sys

FILES = [
    "public/catalogs/DS-CATALOG.html",
    "public/catalogs/DS-CATALOG-portable.html",
    "public/catalogs/KONTAKT-CATALOG.html",
    "public/catalogs/KONTAKT-CATALOG-portable.html",
]

OLD = (
    "  var playing=!!(yt&&cardSearchState.ytId);\n"
    "  stage.classList.toggle('yt-split',playing);\n"
    "  stage.classList.toggle('yt-wide',!!yt&&!playing);"
)
NEW = (
    "  var playing=!!(yt&&cardSearchState.ytId);\n"
    "  /* fix-YT-PANE-LANDSCAPE-v1: landscape has the width to spare, so keep the\n"
    "     comments/related pane on the right even while a video plays; portrait\n"
    "     keeps dropping it below the video. */\n"
    "  var landscape=typeof cardSearchIsLandscape==='function'&&cardSearchIsLandscape();\n"
    "  stage.classList.toggle('yt-split',playing&&!landscape);\n"
    "  stage.classList.toggle('yt-wide',!!yt&&(!playing||landscape));"
)


def apply_to(path: str) -> None:
    html = open(path, encoding="utf-8").read()
    if NEW in html:
        print(f"skip (already applied): {path}")
        return
    n = html.count(OLD)
    if n != 1:
        raise SystemExit(f"{path}: expected 1 match, found {n}")
    html = html.replace(OLD, NEW, 1)
    open(path, "w", encoding="utf-8").write(html)
    print(f"ok: {path}")


def main() -> None:
    for rel in FILES:
        apply_to(rel)


if __name__ == "__main__":
    sys.exit(main())
