#!/usr/bin/env python3
"""
Fix: when the mobile/desktop header toolbar is collapsed (body.hdr-bar-hidden),
the small centered arrow tab only poked ~0.7rem out of the top edge (recessed by
translateY(-.45rem)), while the page still reserved its normal, uncollapsed
body padding-top (clamp(.5rem,2vw,2rem) - up to 2rem/32px) above the content,
search and keywords panes. That left a mismatched, wasted gap: the arrow barely
stuck out of the border, but the content/search/keywords panes still started
well below it instead of being pulled up flush under the arrow.

This patch, scoped to body.hdr-bar-hidden only (does not touch the normal,
expanded-header look):
  - Makes the arrow protrude further out of the true top edge (respecting
    env(safe-area-inset-top) for notches) so it's clearly visible sticking out
    of the screen border.
  - Shrinks the page's top padding down to just clear the arrow's own height
    (instead of the much larger generic clamp() used for the expanded header),
    so the content/search/keywords panes all move up together and their tops
    line up right under the arrow - no visible outline added, purely spacing.
Since all three panes (#catalogMain, #searchChrome, #filterWrap) inherit this
same body-level top padding, they stay aligned with each other after the move.
"""
import re
import sys

FILES = [
    "public/catalogs/DS-CATALOG.html",
    "public/catalogs/DS-CATALOG-portable.html",
    "public/catalogs/KONTAKT-CATALOG.html",
    "public/catalogs/KONTAKT-CATALOG-portable.html",
]

TAG = "HDR-BAR-EDGE-STICK-v1"

OLD = (
    "body.hdr-bar-hidden .hdr-bar-toggle{\n"
    "  position:fixed!important;left:50%!important;right:auto!important;bottom:auto!important;\n"
    "  transform:translateX(-50%) translateY(-.45rem)!important;margin:0;z-index:321\n"
    "}"
)

NEW = (
    "/* " + TAG + ": arrow sticks further out of the true top edge/border when\n"
    "   collapsed, and body top padding shrinks to just clear it so content,\n"
    "   search and keywords panes move up flush under it (no visible outline). */\n"
    "body.hdr-bar-hidden{\n"
    "  padding-top:calc(env(safe-area-inset-top,0px) + .8rem)!important\n"
    "}\n"
    "body.hdr-bar-hidden .hdr-bar-toggle{\n"
    "  position:fixed!important;left:50%!important;right:auto!important;bottom:auto!important;\n"
    "  top:env(safe-area-inset-top,0px)!important;\n"
    "  transform:translateX(-50%) translateY(-.15rem)!important;margin:0;z-index:321\n"
    "}"
)


def main():
    changed = []
    for rel in FILES:
        with open(rel, "r", encoding="utf-8") as fh:
            html = fh.read()
        if TAG in html:
            print(f"skip (already applied): {rel}")
            continue
        count = html.count(OLD)
        if count != 1:
            print(f"ERROR: expected 1 match in {rel}, found {count}", file=sys.stderr)
            sys.exit(1)
        html = html.replace(OLD, NEW, 1)
        with open(rel, "w", encoding="utf-8") as fh:
            fh.write(html)
        changed.append(rel)
        print(f"patched: {rel}")
    if not changed:
        print("Nothing to do.")


if __name__ == "__main__":
    main()
