#!/usr/bin/env python3
"""fix-DOCK-RESTORE-VIS-v1: pinned-dock restore must not open into a hidden card.

TODO 3c: restoring a pinned card from the bottom dock sometimes showed nothing
when the current keyword/search filter had hidden that card (and/or its
`.loc-group` wrapper) before it was minimized to the dock.

The catalog's filter engine (`hideNonHitEntry`/`syncLocGroups`) hides a
non-matching entry with BOTH the `.is-hidden` class and an inline
`style.display='none'`, and hides an empty `.loc-group` with BOTH
`.is-hidden` and the native `hidden` DOM attribute. The stylesheet has
`display:grid!important` overrides for the currently-selected/highlighted
card and its group (via `:has()`), which is normally enough -- but restoring
from the dock only adds `.selected`/`.highlight` AFTER the card has already
been sitting hidden by the filter, so the visibility briefly (or, on engines
where the `:has()` override loses the cascade for any reason -- e.g. the
native `hidden` attribute) depends entirely on that one CSS rule reasserting
itself in time. That is fragile and exactly matches "not reproduced headless
yet": it depends on filter state timing, not something a fresh headless load
hits by default.

Fix: when `cardMinRestore` is about to reopen a card, explicitly clear any
hidden state on the card itself and its ancestor `.loc-group` -- the same
class/attribute the filter engine sets -- before calling
`openOverlay`/`openChosenPreview`. This makes the restore visible
unconditionally, independent of `:has()` support or cascade specificity.
`closeChosenPreview`/`closeOverlay` already re-run `rehideSearchNonHits` and
`syncLocGroups` when the preview closes, so the filter re-hides the card and
its group again once the user is done, with no listed regression.
"""
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1] / 'public' / 'catalogs'
FILES = ['DS-CATALOG.html', 'DS-CATALOG-portable.html', 'KONTAKT-CATALOG.html', 'KONTAKT-CATALOG-portable.html']

OLD = """  var el=document.getElementById(item.id);
  if(!el){cardMinDockItems.splice(i,1);cardMinRender();return;}
  var cur=cardMinExpanded();"""
NEW = """  var el=document.getElementById(item.id);
  if(!el){cardMinDockItems.splice(i,1);cardMinRender();return;}
  /* fix-DOCK-RESTORE-VIS-v1: clear any filter-driven hidden state so the
     restored card is visible unconditionally, not dependent on a CSS :has()
     override reasserting itself in time. */
  el.classList.remove('is-hidden');
  el.style.display='';
  var restoreGroup=el.closest('.loc-group');
  if(restoreGroup){restoreGroup.classList.remove('is-hidden');restoreGroup.hidden=false;}
  var cur=cardMinExpanded();"""


def patch(path: pathlib.Path) -> None:
    html = path.read_text(encoding='utf-8')
    if NEW in html:
        print(f"{path.name}: already patched")
        return
    count = html.count(OLD)
    if count != 1:
        raise SystemExit(f"{path.name}: expected 1 match, found {count}")
    html = html.replace(OLD, NEW, 1)
    path.write_text(html, encoding='utf-8')
    print(f"{path.name}: patched")


def main() -> None:
    for name in FILES:
        patch(ROOT / name)


if __name__ == '__main__':
    main()
