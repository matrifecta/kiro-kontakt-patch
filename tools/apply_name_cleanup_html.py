#!/usr/bin/env python3
"""Apply the raw->clean name mapping inside the 4 public/catalogs/*.html
catalog files.

Per entry, this updates ONLY the display-facing occurrences of the raw
name:
  - data-name="RAW" (the .entry div itself, and its Search button)
  - alt="RAW" on the cover <img>
  - <h3 class="lib-name">RAW</h3> (the visible title)
  - the generic fallback description "Decent Sampler library: RAW."
  - the external Search button's YouTube/Google URLs (re-encoded)

It deliberately never touches the "open:" <code>...</code> path or the
file:// href next to it -- those must keep reflecting the REAL on-disk
folder name, which does not change just because the display name does.

After renaming every entry in a file, the alphabetical Index list is
rebuilt from scratch from the (now-renamed) entries, exactly the way
build-ds-catalog-html.sh generates it (sorted casefold, deduped),
otherwise the index would be left in stale alphabetical order.
"""
import json
import re
import sys
import urllib.parse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import sort_catalog_cards as sortcards

REPO = Path(__file__).resolve().parents[1]
GEN = REPO / 'tools' / '_generated'

FILES = [
    # (path, name-map file, desc-fallback prefix, search_query/img suffix)
    ('public/catalogs/DS-CATALOG.html', 'ds-name-map.json',
     'Decent Sampler library: ', 'decent+sampler'),
    ('public/catalogs/DS-CATALOG-portable.html', 'ds-name-map.json',
     'Decent Sampler library: ', 'decent+sampler'),
    ('public/catalogs/KONTAKT-CATALOG.html', 'kontakt-name-map.json',
     'Kontakt library: ', 'kontakt+library'),
    ('public/catalogs/KONTAKT-CATALOG-portable.html', 'kontakt-name-map.json',
     'Kontakt library: ', 'kontakt+library'),
]

INDEX_START = '<ul class="index" id="catalogIndexList">'
INDEX_END = '</ul></div>'
ENTRY_RE = re.compile(r'<div class="entry" id="(item-\d+)"')


def esc_attr(s: str) -> str:
    return (s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            .replace('"', '&quot;'))


def esc_text(s: str) -> str:
    return s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


def unesc(s: str) -> str:
    return (s.replace('&quot;', '"').replace('&lt;', '<').replace('&gt;', '>')
            .replace('&amp;', '&'))


def quote_plus(s: str) -> str:
    return urllib.parse.quote_plus(s)


def split_entries(html: str):
    """Returns (head, [entry_chunk, ...]) where head is everything before
    the first entry, and each chunk starts at that entry's <div class=
    "entry" ...> and runs up to (but not including) the next one, or --
    for the last entry -- up to the literal '<aside class="catalog-doc-note'
    tail marker."""
    matches = list(ENTRY_RE.finditer(html))
    if not matches:
        return html, []
    head = html[:matches[0].start()]
    chunks = []
    for i, m in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else html.find(
            '<aside class="catalog-doc-note', m.start())
        chunks.append(html[m.start():end])
    return head, chunks


def rename_in_chunk(chunk: str, raw: str, clean: str, desc_prefix: str, search_suffix: str) -> str:
    raw_attr, clean_attr = esc_attr(raw), esc_attr(clean)
    raw_text, clean_text = esc_text(raw), esc_text(clean)

    chunk = chunk.replace(f'data-name="{raw_attr}"', f'data-name="{clean_attr}"')
    chunk = chunk.replace(f'alt="{raw_attr}"', f'alt="{clean_attr}"')
    chunk = chunk.replace(
        f'<h3 class="lib-name">{raw_text}</h3>',
        f'<h3 class="lib-name">{clean_text}</h3>',
    )
    # Generic fallback description line (only present when there was no
    # README-derived blurb) -- e.g. "Decent Sampler library: RAW."
    chunk = chunk.replace(f'{desc_prefix}{raw_text}.</p>', f'{desc_prefix}{clean_text}.</p>')
    # External Search button links (YouTube/Google), re-encoded for the
    # new name -- these are just outbound convenience search URLs.
    raw_enc, clean_enc = quote_plus(raw), quote_plus(clean)
    if raw_enc != clean_enc:
        chunk = chunk.replace(
            f'search_query={raw_enc}+{search_suffix}', f'search_query={clean_enc}+{search_suffix}')
        chunk = chunk.replace(f'q={raw_enc}+vst+instrument', f'q={clean_enc}+vst+instrument')
        chunk = chunk.replace(f'q={raw_enc}+{search_suffix}', f'q={clean_enc}+{search_suffix}')
    return chunk


def rebuild_index(chunks: list[str]) -> str:
    lines = []
    seen = set()
    entries = []
    for chunk in chunks:
        m = re.search(
            r'<div class="entry" id="(item-\d+)" data-kw="([^"]*)"[^>]*data-name="([^"]*)"',
            chunk,
        )
        if not m:
            continue
        item_id, kw, name_attr = m.group(1), m.group(2), m.group(3)
        entries.append((item_id, kw, name_attr))
    # sort by casefold of the (unescaped) display name, matching the
    # builder's own sort key
    entries.sort(key=lambda t: unesc(t[2]).casefold())
    for item_id, kw, name_attr in entries:
        line = f'<li data-kw="{kw}"><a href="#{item_id}">{name_attr}</a></li>\n'
        if line in seen:
            continue
        seen.add(line)
        lines.append(line)
    return ''.join(lines)


def process_file(rel_path: str, map_name: str, desc_prefix: str, search_suffix: str):
    path = REPO / rel_path
    mapping = json.loads((GEN / map_name).read_text())
    changes = {raw: clean for raw, clean in mapping.items() if raw != clean}

    html = path.read_text(encoding='utf-8')
    head, chunks = split_entries(html)
    if not chunks:
        print(f'{rel_path}: no entries found, skipping')
        return

    renamed = 0
    new_chunks = []
    for chunk in chunks:
        m = re.search(r'<div class="entry" id="item-\d+" data-kw="[^"]*"[^>]*data-name="([^"]*)"', chunk)
        raw_attr = m.group(1) if m else None
        raw = unesc(raw_attr) if raw_attr else None
        if raw and raw in changes:
            chunk = rename_in_chunk(chunk, raw, changes[raw], desc_prefix, search_suffix)
            renamed += 1
        new_chunks.append(chunk)

    # everything after the last entry chunk, starting at the tail marker
    last_end = head_len = len(head) + sum(len(c) for c in chunks)
    tail = html[last_end:]

    body = head + ''.join(new_chunks) + tail

    # rebuild the index list from the (now-renamed) entries
    idx_start = body.find(INDEX_START)
    idx_content_start = idx_start + len(INDEX_START)
    idx_end = body.find(INDEX_END, idx_content_start)
    if idx_start == -1 or idx_end == -1:
        print(f'{rel_path}: WARNING could not find index markers, leaving index as-is')
    else:
        new_index = '\n' + rebuild_index(new_chunks)
        body = body[:idx_content_start] + new_index + body[idx_end:]

    # keep each location group's card grid alphabetically sorted too --
    # a rename doesn't move a card, so this prevents the grid drifting
    # out of order relative to its own (now-current) display names
    body, _groups, _n = sortcards.sort_cards_in_html(body)

    path.write_text(body, encoding='utf-8')
    print(f'{rel_path}: {renamed} entries renamed, {len(chunks)} total, index rebuilt')


def main():
    for rel_path, map_name, desc_prefix, search_suffix in FILES:
        process_file(rel_path, map_name, desc_prefix, search_suffix)


if __name__ == '__main__':
    main()
