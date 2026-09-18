#!/usr/bin/env python3
"""Apply a small, hand-curated name-fix mapping (JSON: {"ds": {...},
"kontakt": {...}}, keyed by the CURRENT display name) to data/*.json,
all 4 catalog HTML files, and name-overrides.tsv -- the same rename
machinery as apply_name_cleanup_html.py, reused for one-off manual
batches (engine-name references, Pianobook-style submission tags, etc.)
that don't need the full generate_name_mapping.py pass.

Usage: python3 tools/apply_manual_name_fixes.py tools/_generated/<file>.json \
         [--raw-key-overrides tools/_generated/<file>.raw-keys.json]

`--raw-key-overrides` is only needed when a mapping's CURRENT name isn't
the same as the raw on-disk folder name (i.e. it already went through an
earlier cleanup pass) -- it maps {current-name: original-raw-name} so
name-overrides.tsv gets keyed correctly for the builder scripts.
"""
import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import apply_name_cleanup_html as html_apply
import sort_catalog_cards as sortcards

REPO = Path(__file__).resolve().parents[1]

FILES = [
    ('public/catalogs/DS-CATALOG.html', 'ds', 'Decent Sampler library: ', 'decent+sampler'),
    ('public/catalogs/DS-CATALOG-portable.html', 'ds', 'Decent Sampler library: ', 'decent+sampler'),
    ('public/catalogs/KONTAKT-CATALOG.html', 'kontakt', 'Kontakt library: ', 'kontakt+library'),
    ('public/catalogs/KONTAKT-CATALOG-portable.html', 'kontakt', 'Kontakt library: ', 'kontakt+library'),
]
JSON_PATHS = {'ds': REPO / 'data/ds-libs.json', 'kontakt': REPO / 'data/kontakt-libs.json'}


def apply_json(json_path: Path, mapping: dict) -> int:
    data = json.loads(json_path.read_text())
    changed = 0
    for e in data:
        new = mapping.get(e['name'])
        if new and new != e['name']:
            e['name'] = new
            changed += 1
    json_path.write_text(json.dumps(data, ensure_ascii=False))
    return changed


def apply_html(rel_path: str, mapping: dict, desc_prefix: str, search_suffix: str) -> int:
    path = REPO / rel_path
    html = path.read_text(encoding='utf-8')
    head, chunks = html_apply.split_entries(html)
    renamed = 0
    new_chunks = []
    for chunk in chunks:
        m = re.search(r'<div class="entry" id="item-\d+" data-kw="[^"]*"[^>]*data-name="([^"]*)"', chunk)
        raw_attr = m.group(1) if m else None
        raw = html_apply.unesc(raw_attr) if raw_attr else None
        if raw and raw in mapping:
            chunk = html_apply.rename_in_chunk(chunk, raw, mapping[raw], desc_prefix, search_suffix)
            renamed += 1
        new_chunks.append(chunk)
    last_end = len(head) + sum(len(c) for c in chunks)
    tail = html[last_end:]
    body = head + ''.join(new_chunks) + tail
    idx_start = body.find(html_apply.INDEX_START)
    idx_content_start = idx_start + len(html_apply.INDEX_START)
    idx_end = body.find(html_apply.INDEX_END, idx_content_start)
    if idx_start != -1 and idx_end != -1:
        new_index = '\n' + html_apply.rebuild_index(new_chunks)
        body = body[:idx_content_start] + new_index + body[idx_end:]
    # keep each location group's card grid alphabetically sorted too --
    # a rename doesn't move a card, so this prevents the grid drifting
    # out of order relative to its own (now-current) display names
    body, _groups, _n = sortcards.sort_cards_in_html(body)
    path.write_text(body, encoding='utf-8')
    return renamed


def update_overrides(raw_keyed: dict):
    for art_dir in [
        REPO / 'kiro/specs/kontakt-workspace-drive-dirty-fix/artifacts',
        Path('/home/phnx/KIRO/.kiro/specs/kontakt-workspace-drive-dirty-fix/artifacts'),
    ]:
        out = art_dir / 'name-overrides.tsv'
        existing = {}
        if out.exists():
            for line in out.read_text().splitlines():
                if not line or line.startswith('#') or '\t' not in line:
                    continue
                k, v = line.split('\t', 1)
                existing[k] = v
        existing.update(raw_keyed)
        header = [
            '# raw folder/library name<TAB>clean display name',
            '# Maintained by tools/apply_name_cleanup.py / tools/update_catalog.py.',
            '# Consumed by build-ds-catalog-html.sh and build-kontakt-catalog-html.sh',
            '# via name_override() so a rebuild keeps these clean names instead of',
        ]
        lines = header + [f'{k}\t{v}' for k, v in sorted(existing.items())]
        out.write_text('\n'.join(lines) + '\n')
        print(f'{out}: {len(existing)} overrides')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('mapping_file', help='JSON: {"ds": {current: new}, "kontakt": {...}}')
    ap.add_argument('--raw-key-overrides', help='JSON: {current-name: original-raw-name}')
    args = ap.parse_args()

    fixes = json.loads(Path(args.mapping_file).read_text())
    raw_key_overrides = (
        json.loads(Path(args.raw_key_overrides).read_text()) if args.raw_key_overrides else {}
    )

    maps = {cat: {k: v for k, v in fixes.get(cat, {}).items() if k != v} for cat in JSON_PATHS}

    for cat, json_path in JSON_PATHS.items():
        c = apply_json(json_path, maps[cat])
        print(f'{json_path.relative_to(REPO)}: {c} names updated')

    for rel_path, cat, desc_prefix, search_suffix in FILES:
        renamed = apply_html(rel_path, maps[cat], desc_prefix, search_suffix)
        print(f'{rel_path}: {renamed} entries renamed, index rebuilt')

    all_fixes = {k: v for m in maps.values() for k, v in m.items()}
    raw_keyed = {raw_key_overrides.get(k, k): v for k, v in all_fixes.items()}
    update_overrides(raw_keyed)


if __name__ == '__main__':
    main()
