#!/usr/bin/env python3
"""Self-test for tools/catalog_splice.py using synthetic fixtures (no real
builder run needed). Run directly: python3 tools/test_catalog_splice.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import catalog_splice as sp

LIVE = """<!DOCTYPE html><html><head><style>/* PATCHED-CHROME-CSS-v99 */</style></head>
<body class="quickbar-docked edge-tabs-on">
<div class="header">NEWER HEADER WIDGET</div>
<ul class="index" id="catalogIndexList">
<li data-kw=""><a href="#item-1">Old Alpha</a></li>
<li data-kw=""><a href="#item-2">Old Beta</a></li>
</ul></div>
<div class="catalog-body">
<div class="fav-recs-label">Favorites</div>
<div class="entry" id="item-1" data-kw="" data-name="Old Alpha">OLD ALPHA CARD (stale data)</div>
<div class="entry" id="item-2" data-kw="" data-name="Old Beta">OLD BETA CARD (stale data)</div>
</div>
<aside class="catalog-doc-note">note widget added by a later patch</aside>
<script>/* PATCHED-CHROME-JS-v99 quickbar/edge-tabs code */</script>
</body></html>"""

FRESH = """<!DOCTYPE html><html><head><style>/* stale old builder css, pre-patches */</style></head>
<body>
<div class="header">OLD STALE HEADER (no quickbar/edge-tabs)</div>
<ul class="index" id="catalogIndexList">
<li data-kw=""><a href="#item-1">New Alpha</a></li>
<li data-kw=""><a href="#item-2">New Beta</a></li>
<li data-kw=""><a href="#item-3">New Gamma</a></li>
</ul></div>
<div class="catalog-body">
<div class="fav-recs-label">Favorites</div>
<div class="entry" id="item-1" data-kw="" data-name="New Alpha">NEW ALPHA CARD (fresh scan)</div>
<div class="entry" id="item-2" data-kw="" data-name="New Beta">NEW BETA CARD (fresh scan)</div>
<div class="entry" id="item-3" data-kw="" data-name="New Gamma">NEW GAMMA CARD (fresh scan)</div>
</div>
<aside class="catalog-doc-note">old stale note widget</aside>
<script>/* old stale builder js, no quickbar/edge-tabs */</script>
</body></html>"""


def check(label, cond):
    status = 'PASS' if cond else 'FAIL'
    print(f'[{status}] {label}')
    return cond


def main():
    fresh = sp.extract_fresh(FRESH)
    result = sp.splice_onto_live(LIVE, fresh)

    ok = True
    ok &= check('keeps patched CSS from live', 'PATCHED-CHROME-CSS-v99' in result)
    ok &= check('keeps patched JS from live', 'PATCHED-CHROME-JS-v99' in result)
    ok &= check('keeps newer header widget from live', 'NEWER HEADER WIDGET' in result)
    ok &= check('keeps the doc-note widget added by a later patch',
                'note widget added by a later patch' in result)
    ok &= check('does NOT bring in the fresh build\'s stale header',
                'OLD STALE HEADER' not in result)
    ok &= check('does NOT bring in the fresh build\'s stale JS comment',
                'old stale builder js' not in result)

    ok &= check('entries come from the FRESH scan (3, not the live 2)', sp.entry_count(result) == 3)
    ok &= check('has New Gamma (only in fresh)', 'New Gamma' in result)
    ok &= check('does NOT have Old Alpha (stale live data)', 'Old Alpha' not in result)
    ok &= check('card body content is the fresh one', 'NEW ALPHA CARD (fresh scan)' in result)

    ok &= check('index has all 3 fresh entries', result.count('<li data-kw=') == 3)
    idx_pos = result.find('<ul class="index"')
    body_pos = result.find('<div class="entry"')
    ok &= check('index still comes before the entries body', idx_pos < body_pos)

    print()
    print('ALL PASS' if ok else 'SOME FAILED')
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main()
