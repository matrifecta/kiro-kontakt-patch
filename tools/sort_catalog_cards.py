#!/usr/bin/env python3
"""Sort the .entry cards inside each location group (the "1. Via SAMPLE
STORE" / "2. Via FILE BROWSER - BTRFS drive" / etc. sections in the
content window) alphabetically by their current display name, case-
insensitive -- the same sort key already used for the Index list, so
numbered names ("12 String Acoustic") naturally sort before lettered
ones (plain ASCII: digits < letters).

The builder originally emitted cards in this order (piped through `sort
-f`), but repeated name-cleanup passes changed 200+ display names via
targeted string substitution without reordering the DOM, so the grid
drifted out of alphabetical order relative to its own group headers
while the (separately rebuilt) Index list did not.

Each location group is a `<div class="loc-group">...</div>` block; this
finds its exact span via div-depth matching (robust to whatever nested
markup the many UI patches have added inside each card), keeps its
`<h2>`/`<p class="loc-hint">` header exactly as-is, and only reorders
the whole `.entry` chunks after it.
"""
import html as html_lib
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
FILES = [
    'public/catalogs/DS-CATALOG.html',
    'public/catalogs/DS-CATALOG-portable.html',
    'public/catalogs/KONTAKT-CATALOG.html',
    'public/catalogs/KONTAKT-CATALOG-portable.html',
]
LOC_GROUP_OPEN = '<div class="loc-group">'
ENTRY_RE = re.compile(r'<div class="entry" id="item-\d+"[^>]*data-name="([^"]*)"')


def find_matching_close(html: str, open_pos: int) -> int:
    """Given the index of a `<div` open tag, returns the index right
    after its matching `</div>`, counting nested div depth."""
    tag_end = html.find('>', open_pos) + 1
    depth = 1
    pos = tag_end
    while depth > 0:
        next_open = html.find('<div', pos)
        next_close = html.find('</div>', pos)
        if next_close == -1:
            raise ValueError('unbalanced <div> in document')
        if next_open != -1 and next_open < next_close:
            depth += 1
            pos = next_open + 4
        else:
            depth -= 1
            pos = next_close + len('</div>')
    return pos


def sort_group(group_html: str) -> tuple[str, int]:
    """group_html spans exactly one `<div class="loc-group">...</div>`.
    Returns (new_group_html, entry_count)."""
    m = ENTRY_RE.search(group_html)
    if not m:
        return group_html, 0
    entries_start = m.start()
    prefix = group_html[:entries_start]
    # strip the loc-group's own closing </div> off the end -- everything
    # in between is entry chunks, back to back
    assert group_html.endswith('</div>')
    entries_region = group_html[entries_start:-len('</div>')]

    starts = [mm.start() for mm in ENTRY_RE.finditer(entries_region)]
    chunks = []
    for i, s in enumerate(starts):
        e = starts[i + 1] if i + 1 < len(starts) else len(entries_region)
        chunks.append(entries_region[s:e])

    def sort_key(chunk):
        name = ENTRY_RE.match(chunk).group(1)
        return html_lib.unescape(name).casefold()

    chunks.sort(key=sort_key)
    return prefix + ''.join(chunks) + '</div>', len(chunks)


def sort_cards_in_html(html: str) -> tuple[str, int, int]:
    """Applies sort_group() to every location group in a full document.
    Returns (new_html, group_count, entry_count)."""
    out = []
    pos = 0
    total_entries = 0
    groups = 0
    while True:
        i = html.find(LOC_GROUP_OPEN, pos)
        if i == -1:
            out.append(html[pos:])
            break
        out.append(html[pos:i])
        end = find_matching_close(html, i)
        new_group, count = sort_group(html[i:end])
        out.append(new_group)
        total_entries += count
        groups += 1
        pos = end
    return ''.join(out), groups, total_entries


def process_file(rel_path: str):
    path = REPO / rel_path
    html = path.read_text(encoding='utf-8')
    new_html, groups, total_entries = sort_cards_in_html(html)
    path.write_text(new_html, encoding='utf-8')
    print(f'{rel_path}: {groups} location groups sorted, {total_entries} cards total')


def main():
    for rel_path in FILES:
        process_file(rel_path)


if __name__ == '__main__':
    main()
