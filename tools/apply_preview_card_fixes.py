#!/usr/bin/env python3
"""fix-PREVIEW-CARD-v1: keep the desktop expanded card (chosen preview) intact.

1. The 'no menu floats above expanded/fullscreen card' rule hid the Search /
   Keywords panes and the header cluster on desktop while the preview was open,
   blanking the catalog around the card. Those panes only float on portable, so
   the pane/header part of the rule is now scoped to body.catalog-portable.
2. equalizeCatalogCardRows() must not stamp grid min-heights onto the
   position:fixed preview card (it is .entry.selected under chosen-preview-open).
"""
import re, sys, pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1] / 'public' / 'catalogs'
FILES = ['DS-CATALOG.html', 'DS-CATALOG-portable.html', 'KONTAKT-CATALOG.html', 'KONTAKT-CATALOG-portable.html']

OVERLAYS = '.hl-open,.chosen-preview-open,.card-embed-open,.gallery-open,.img-focus-open,.desc-reader-open,.path-reader-open,.desc-focus-open,.path-focus-open,.search-modal-open,.catalog-help-open,.catalog-help-fs'
PANES = '.search-chrome,.filter-wrap,#filterWrap,.search-ac-shell,#acShell,'
HDR = ',#hdrCluster,.hdr-cluster'

RULE_RE = re.compile(r'body:is\(' + re.escape(OVERLAYS) + r'\) :is\(' + re.escape(PANES) + r'(.*?)' + re.escape(HDR) + r'(.*?)\)\{visibility:hidden!important;pointer-events:none!important\}')

RESET_OLD = "if(e.classList.contains('highlight'))return;"
RESET_NEW = RESET_OLD  # reset still clears the preview card; only row measurement skips it
ROWS_OLD = "if(e.classList.contains('is-hidden')||e.classList.contains('highlight'))return;"
ROWS_NEW = "if(e.classList.contains('is-hidden')||e.classList.contains('highlight')||_isPreviewCard(e))return;"
FN_ANCHOR = "function equalizeCatalogCardRows(){"
FN_HELPER = ("/* fix-PREVIEW-CARD-v1: the fixed-position preview card is not part of any grid row */\n"
             "function _isPreviewCard(e){return !!(e&&e.classList.contains('selected')&&document.body.classList.contains('chosen-preview-open'));}\n")

def patch(path):
    s = path.read_text(encoding='utf-8')
    m = RULE_RE.search(s)
    if not m:
        sys.exit(f'{path.name}: overlay rule not found')
    floats, tail = m.group(1), m.group(2)
    new_rule = (f'body:is({OVERLAYS}) :is({floats}{tail}){{visibility:hidden!important;pointer-events:none!important}}\n'
                f'/* fix-PREVIEW-CARD-v1: panes/header only float over the card on portable */\n'
                f'body.catalog-portable:is({OVERLAYS}) :is({PANES}#hdrCluster,.hdr-cluster){{visibility:hidden!important;pointer-events:none!important}}')
    s = s[:m.start()] + new_rule + s[m.end():]
    for old, new in ((RESET_OLD, RESET_NEW), (ROWS_OLD, ROWS_NEW)):
        if s.count(old) != 1:
            sys.exit(f'{path.name}: expected 1 of {old!r}, got {s.count(old)}')
        s = s.replace(old, new)
    if s.count(FN_ANCHOR) != 1:
        sys.exit(f'{path.name}: equalize anchor count {s.count(FN_ANCHOR)}')
    s = s.replace(FN_ANCHOR, FN_HELPER + FN_ANCHOR)
    path.write_text(s, encoding='utf-8')
    print(f'{path.name}: patched')

for f in FILES:
    patch(ROOT / f)
