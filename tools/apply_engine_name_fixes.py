#!/usr/bin/env python3
"""One-off: strip remaining sample-engine references (DS/VT/"Decent
Sampler", a mislabeled bare "Kontakt" alias) from display names, using
the same rename machinery as apply_name_cleanup_html.py/.py.

Mapping lives in tools/_generated/engine-name-fixes.json, keyed by the
CURRENT display name (not necessarily the original raw folder name --
some of these already went through the earlier cleanup pass).
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import apply_name_cleanup_html as html_apply

REPO = Path(__file__).resolve().parents[1]
GEN = REPO / 'tools' / '_generated'
FIXES = json.loads((GEN / 'engine-name-fixes.json').read_text())

# raw-folder-name key (for name-overrides.tsv) -> new clean name.
# For entries never touched before, the raw key == the current name.
# For "Antz Decent Sampler 2", the raw folder is "Antz Decent Sampler
# 1.0 2" (already in name-overrides.tsv from the earlier pass).
RAW_KEY_OVERRIDES = {
    'Antz Decent Sampler 2': 'Antz Decent Sampler 1.0 2',
}


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


def main():
    ds_map = {k: v for k, v in FIXES['ds'].items() if k != v}
    kt_map = {k: v for k, v in FIXES['kontakt'].items() if k != v}

    c1 = apply_json(REPO / 'data/ds-libs.json', ds_map)
    print(f'data/ds-libs.json: {c1} names updated')
    c2 = apply_json(REPO / 'data/kontakt-libs.json', kt_map)
    print(f'data/kontakt-libs.json: {c2} names updated')

    # HTML: reuse apply_name_cleanup_html's per-file renamer directly with
    # this mapping instead of the ds/kontakt-name-map.json files.
    for rel_path, mapping, desc_prefix, search_suffix in [
        ('public/catalogs/DS-CATALOG.html', ds_map, 'Decent Sampler library: ', 'decent+sampler'),
        ('public/catalogs/DS-CATALOG-portable.html', ds_map, 'Decent Sampler library: ', 'decent+sampler'),
        ('public/catalogs/KONTAKT-CATALOG.html', kt_map, 'Kontakt library: ', 'kontakt+library'),
        ('public/catalogs/KONTAKT-CATALOG-portable.html', kt_map, 'Kontakt library: ', 'kontakt+library'),
    ]:
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
        path.write_text(body, encoding='utf-8')
        print(f'{rel_path}: {renamed} entries renamed, index rebuilt')

    # name-overrides.tsv (repo + ~/KIRO copies)
    all_fixes = {**ds_map, **kt_map}
    raw_keyed = {RAW_KEY_OVERRIDES.get(k, k): v for k, v in all_fixes.items()}
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


if __name__ == '__main__':
    main()
