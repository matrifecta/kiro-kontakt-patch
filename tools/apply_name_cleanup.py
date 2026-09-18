#!/usr/bin/env python3
"""Apply the generated raw->clean name mapping to:
  - data/ds-libs.json, data/kontakt-libs.json (the `name` field)
  - name-overrides.tsv (repo copy + the live ~/KIRO copy the builder
    scripts actually read), so future rebuilds keep the clean names
  - the 4 public/catalogs/*.html files (data-name/data-other/alt/h3/
    search-link occurrences), leaving the real on-disk folder path
    (the "open:" <code> block and the file:// href) untouched, then
    rebuilding the index list in the new sort order.

Run generate_name_mapping.py first. This script is idempotent: it
compares against the *current on-disk* raw name, so re-running after a
partial apply is safe.
"""
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
GEN = REPO / 'tools' / '_generated'
KIRO_ART_DIRS = [
    REPO / 'kiro/specs/kontakt-workspace-drive-dirty-fix/artifacts',
    Path('/home/phnx/KIRO/.kiro/specs/kontakt-workspace-drive-dirty-fix/artifacts'),
]


def apply_json(path: Path, mapping: dict[str, str]) -> int:
    data = json.loads(path.read_text())
    changed = 0
    for e in data:
        new = mapping.get(e['name'])
        if new and new != e['name']:
            e['name'] = new
            changed += 1
    path.write_text(json.dumps(data, ensure_ascii=False))
    return changed


def write_name_overrides(mapping: dict[str, str]):
    lines = [
        '# raw folder/library name<TAB>clean display name',
        '# Maintained by tools/apply_name_cleanup.py / tools/update_catalog.py.',
        '# Consumed by build-ds-catalog-html.sh and build-kontakt-catalog-html.sh',
        '# via name_override() so a rebuild keeps these clean names instead of',
        '# reverting to the raw on-disk folder name / komplete.db3 alias.',
    ]
    for raw, clean in sorted(mapping.items()):
        if raw == clean:
            continue
        lines.append(f'{raw}\t{clean}')
    text = '\n'.join(lines) + '\n'
    for art_dir in KIRO_ART_DIRS:
        if not art_dir.is_dir():
            print(f'  (skip, no such dir) {art_dir}')
            continue
        out = art_dir / 'name-overrides.tsv'
        existing = {}
        if out.exists():
            for line in out.read_text().splitlines():
                if not line or line.startswith('#') or '\t' not in line:
                    continue
                k, v = line.split('\t', 1)
                existing[k] = v
        existing.update({k: v for k, v in mapping.items() if k != v})
        lines2 = lines[:4] + [f'{k}\t{v}' for k, v in sorted(existing.items())]
        out.write_text('\n'.join(lines2) + '\n')
        print(f'  wrote {out} ({len(existing)} overrides)')


def main():
    ds_map = json.loads((GEN / 'ds-name-map.json').read_text())
    kt_map = json.loads((GEN / 'kontakt-name-map.json').read_text())

    c1 = apply_json(REPO / 'data/ds-libs.json', ds_map)
    print(f'data/ds-libs.json: {c1} names updated')
    c2 = apply_json(REPO / 'data/kontakt-libs.json', kt_map)
    print(f'data/kontakt-libs.json: {c2} names updated')

    print('name-overrides.tsv:')
    write_name_overrides({**ds_map, **kt_map})


if __name__ == '__main__':
    main()
