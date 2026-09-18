"""Splice a freshly-built catalog's entries/index onto whatever chrome is
currently live in public/catalogs/*.html.

Why: build-ds-catalog-html.sh / build-kontakt-catalog-html.sh each write a
full document as STATIC_HEAD + INDEX_LIST + STATIC_CONNECTOR + ENTRIES +
STATIC_TAIL. The builders' own copy of STATIC_HEAD/STATIC_TAIL has not
been kept in sync with the ~100 later UI patches applied straight to the
shipped HTML (search chrome, keywords panel, quickbar, edge tabs, the
help/guide overlay, etc.) -- so running them from scratch today would
regress the UI back to that older state.

Instead of re-syncing two copies of a giant template (which would just
drift again next time), this module makes the LIVE file's own head/tail
the permanent source of truth: every "rebuild" run pulls fresh entries +
index from a scratch build, and grafts them onto whatever chrome is
*currently shipping*. A rebuild can then never regress the UI -- it has
no independent copy of the chrome to go stale.
"""
import re

INDEX_START = '<ul class="index" id="catalogIndexList">'
INDEX_END = '</ul></div>'
FAV_LABEL = '<div class="fav-recs-label">Favorites</div>'
TAIL_MARKER = '<aside class="catalog-doc-note'


class SpliceError(Exception):
    pass


def _find_markers(html: str) -> dict:
    idx_start = html.find(INDEX_START)
    if idx_start == -1:
        raise SpliceError(f'missing marker: {INDEX_START!r}')
    idx_content_start = idx_start + len(INDEX_START)
    idx_content_end = html.find(INDEX_END, idx_content_start)
    if idx_content_end == -1:
        raise SpliceError(f'missing marker: {INDEX_END!r} (after index start)')

    fav_pos = html.find(FAV_LABEL, idx_content_end)
    if fav_pos == -1:
        raise SpliceError(f'missing marker: {FAV_LABEL!r} (after index end)')
    body_content_start = fav_pos + len(FAV_LABEL)

    tail_pos = html.find(TAIL_MARKER, body_content_start)
    if tail_pos == -1:
        raise SpliceError(f'missing marker: {TAIL_MARKER!r} (after body start)')

    return dict(
        idx_content_start=idx_content_start,
        idx_content_end=idx_content_end,
        body_content_start=body_content_start,
        tail_pos=tail_pos,
    )


def extract_fresh(html: str) -> dict:
    """Pulls the regenerated index-list content and entries body out of a
    freshly-built (scratch) catalog HTML document."""
    m = _find_markers(html)
    return dict(
        index=html[m['idx_content_start']:m['idx_content_end']],
        body=html[m['body_content_start']:m['tail_pos']],
    )


def splice_onto_live(live_html: str, fresh: dict) -> str:
    """Returns a new document: the LIVE file's head/connector/tail, with
    its index-list and entries-body content replaced by the fresh ones."""
    m = _find_markers(live_html)
    return (
        live_html[:m['idx_content_start']]
        + fresh['index']
        + live_html[m['idx_content_end']:m['body_content_start']]
        + fresh['body']
        + live_html[m['tail_pos']:]
    )


def entry_count(html: str) -> int:
    return len(re.findall(r'<div class="entry" id="item-\d+"', html))
