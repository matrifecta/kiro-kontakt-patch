#!/usr/bin/env python3
"""fix-SCROLL-THUMB-COMPOSITE-v1: stop the custom scroll thumb lagging the
native scrollbar under fast/heavy scrolling.

Logged-for-later item: "Shadow scrollbar occasionally lagging under the
content window scrollbar (Sides/Middle layouts); tied to the custom
hover-scroll-stripe indicator."

The thumb's vertical position was written every scroll frame via
`el.style.top = px+'px'`. Animating `top` on an absolutely-positioned element
forces layout + paint on every update (it's a geometry property), so on a
long/heavy content column (many DecentSampler/Kontakt cards) or a fast wheel
scroll, the thumb's reflow can fall a frame or more behind the browser's own
(compositor-only) scrollbar, producing the visible lag.

Fix: drive the thumb's position with a CSS custom property consumed by
`transform: translateY()` instead of `top`, so moving the thumb is
compositor-only (no layout/paint) like the browser's native scrollbar. The
existing `scaleY(1.08)` hover/drag effect is folded into the same `transform`
declaration (combined with the translateY term) so hovering/dragging keeps
working exactly as before -- an inline `transform` from JS would otherwise
have clobbered that CSS transform.
"""
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1] / 'public' / 'catalogs'
FILES = ['DS-CATALOG.html', 'DS-CATALOG-portable.html', 'KONTAKT-CATALOG.html', 'KONTAKT-CATALOG-portable.html']

BASE_OLD = ".hover-scroll-thumb{position:absolute;right:1px;width:3px;min-height:1.15rem;border-radius:999px;background:var(--accent-instrument);opacity:.4;box-shadow:0 0 0 1px var(--border);cursor:grab;touch-action:none;transform-origin:right center;transition:width .14s ease,opacity .14s ease,transform .14s ease}"
BASE_NEW = (
    "/* fix-SCROLL-THUMB-COMPOSITE-v1: position via translateY(--thumb-y) so moving the thumb is compositor-only, not a layout+paint top animation */\n"
    ".hover-scroll-thumb{position:absolute;top:0;right:1px;width:3px;min-height:1.15rem;border-radius:999px;background:var(--accent-instrument);opacity:.4;box-shadow:0 0 0 1px var(--border);cursor:grab;touch-action:none;transform-origin:right center;transform:translateY(var(--thumb-y,0px));will-change:transform;transition:width .14s ease,opacity .14s ease,transform .14s ease}"
)

HOVER1_OLD = ".hover-scroll-host.has-hover-overflow>.hover-scroll-stripe:hover .hover-scroll-thumb,.hover-scroll-host.has-hover-overflow>.hover-scroll-stripe.is-dragging .hover-scroll-thumb{width:7px;opacity:.92;transform:scaleY(1.08);cursor:grabbing}"
HOVER1_NEW = ".hover-scroll-host.has-hover-overflow>.hover-scroll-stripe:hover .hover-scroll-thumb,.hover-scroll-host.has-hover-overflow>.hover-scroll-stripe.is-dragging .hover-scroll-thumb{width:7px;opacity:.92;transform:translateY(var(--thumb-y,0px)) scaleY(1.08);cursor:grabbing}"

HOVER2_OLD = "body.has-hover-overflow-content.is-content-hover #catalogMainHoverStripe .hover-scroll-thumb,#catalogMainHoverStripe.hover-scroll-fixed:hover .hover-scroll-thumb,#catalogMainHoverStripe.hover-scroll-fixed.is-dragging .hover-scroll-thumb{width:7px;opacity:.92;transform:scaleY(1.08);cursor:grabbing}"
HOVER2_NEW = "body.has-hover-overflow-content.is-content-hover #catalogMainHoverStripe .hover-scroll-thumb,#catalogMainHoverStripe.hover-scroll-fixed:hover .hover-scroll-thumb,#catalogMainHoverStripe.hover-scroll-fixed.is-dragging .hover-scroll-thumb{width:7px;opacity:.92;transform:translateY(var(--thumb-y,0px)) scaleY(1.08);cursor:grabbing}"

JS_OLD = "      n.th.style.top=Math.round((sc.scrollTop/Math.max(1,max))*range)+'px';"
JS_NEW = "      n.th.style.setProperty('--thumb-y',Math.round((sc.scrollTop/Math.max(1,max))*range)+'px');"

REPLACEMENTS = [
    (BASE_OLD, BASE_NEW, 'css-base'),
    (HOVER1_OLD, HOVER1_NEW, 'css-hover1'),
    (HOVER2_OLD, HOVER2_NEW, 'css-hover2'),
    (JS_OLD, JS_NEW, 'js-set-top'),
]


def patch(path: pathlib.Path) -> None:
    html = path.read_text(encoding='utf-8')
    changed = False
    for old, new, label in REPLACEMENTS:
        if new in html:
            continue
        count = html.count(old)
        if count != 1:
            raise SystemExit(f"{path.name}: expected 1 match for {label}, found {count}")
        html = html.replace(old, new, 1)
        changed = True
    if changed:
        path.write_text(html, encoding='utf-8')
        print(f"{path.name}: patched")
    else:
        print(f"{path.name}: already patched")


def main() -> None:
    for name in FILES:
        patch(ROOT / name)


if __name__ == '__main__':
    main()
