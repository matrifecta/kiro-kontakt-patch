#!/usr/bin/env python3
"""
fix-HOVER-SCROLL-THUMB-SHADOW-v1

User reported the shadow scrollbar's "lag" (fixed in 862c312 by switching
from style.top to a --thumb-y transform) still shows a visible smeared/
ghosted trailing copy of the thumb (screenshot: a blurred second thumb
just below-right of the sharp one).

Root cause 862c312 didn't fully remove: .hover-scroll-thumb's transition
list includes `transform .14s ease`, and --thumb-y is written on every
scroll frame (rAF-throttled `sync()`, called from the scroll listener).
Since the *same* `transform` property carries both the scroll position
(translateY) and the hover/drag grow effect (scaleY(1.08)), the browser
animates the Y position over 140ms on every single scroll update -- while
scrolling continuously, the thumb is always mid-transition, chasing the
real scroll position a frame behind, and that interpolated frame renders
as a smeared duplicate ("shadow") behind the sharp thumb.

Fix: split the two effects onto the separate CSS `translate` and `scale`
properties (independent from `transform`, well supported in current
evergreen browsers) so they can be transitioned independently -- `translate`
(scroll position) updates instantly with no transition, while `scale`
(hover/drag grow) keeps its .14s ease-in feel.

Applies identically to all 4 catalog files.
"""
import sys

FILES = [
    "public/catalogs/DS-CATALOG.html",
    "public/catalogs/DS-CATALOG-portable.html",
    "public/catalogs/KONTAKT-CATALOG.html",
    "public/catalogs/KONTAKT-CATALOG-portable.html",
]

REPLACEMENTS = [
    (
        ".hover-scroll-thumb{position:absolute;top:0;right:1px;width:3px;"
        "min-height:1.15rem;border-radius:999px;background:var(--accent-instrument);"
        "opacity:.4;box-shadow:0 0 0 1px var(--border);cursor:grab;"
        "touch-action:none;transform-origin:right center;"
        "transform:translateY(var(--thumb-y,0px));will-change:transform;"
        "transition:width .14s ease,opacity .14s ease,transform .14s ease}",
        ".hover-scroll-thumb{position:absolute;top:0;right:1px;width:3px;"
        "min-height:1.15rem;border-radius:999px;background:var(--accent-instrument);"
        "opacity:.4;box-shadow:0 0 0 1px var(--border);cursor:grab;"
        "touch-action:none;transform-origin:right center;"
        "translate:0 var(--thumb-y,0px);scale:1 1;will-change:translate;"
        "transition:width .14s ease,opacity .14s ease,scale .14s ease}",
    ),
    (
        ".hover-scroll-host.has-hover-overflow>.hover-scroll-stripe:hover .hover-scroll-thumb,"
        ".hover-scroll-host.has-hover-overflow>.hover-scroll-stripe.is-dragging .hover-scroll-thumb"
        "{width:7px;opacity:.92;transform:translateY(var(--thumb-y,0px)) scaleY(1.08);cursor:grabbing}",
        ".hover-scroll-host.has-hover-overflow>.hover-scroll-stripe:hover .hover-scroll-thumb,"
        ".hover-scroll-host.has-hover-overflow>.hover-scroll-stripe.is-dragging .hover-scroll-thumb"
        "{width:7px;opacity:.92;scale:1 1.08;cursor:grabbing}",
    ),
    (
        "body.has-hover-overflow-content.is-content-hover #catalogMainHoverStripe .hover-scroll-thumb,"
        "#catalogMainHoverStripe.hover-scroll-fixed:hover .hover-scroll-thumb,"
        "#catalogMainHoverStripe.hover-scroll-fixed.is-dragging .hover-scroll-thumb"
        "{width:7px;opacity:.92;transform:translateY(var(--thumb-y,0px)) scaleY(1.08);cursor:grabbing}",
        "body.has-hover-overflow-content.is-content-hover #catalogMainHoverStripe .hover-scroll-thumb,"
        "#catalogMainHoverStripe.hover-scroll-fixed:hover .hover-scroll-thumb,"
        "#catalogMainHoverStripe.hover-scroll-fixed.is-dragging .hover-scroll-thumb"
        "{width:7px;opacity:.92;scale:1 1.08;cursor:grabbing}",
    ),
]


def apply_to(path: str) -> None:
    html = open(path, encoding="utf-8").read()
    changed = False
    for old, new in REPLACEMENTS:
        if new in html:
            continue
        n = html.count(old)
        if n != 1:
            raise SystemExit(f"{path}: expected 1 match, found {n} for:\n{old[:100]}...")
        html = html.replace(old, new, 1)
        changed = True
    if changed:
        open(path, "w", encoding="utf-8").write(html)
        print(f"ok: {path}")
    else:
        print(f"skip (already applied): {path}")


def main() -> None:
    for rel in FILES:
        apply_to(rel)


if __name__ == "__main__":
    sys.exit(main())
