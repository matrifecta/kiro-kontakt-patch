#!/usr/bin/env python3
"""Generate the raw->clean name mapping for the DS + Kontakt catalogs.

Writes JSON mappings to stdout-adjacent files for the apply scripts to
consume, so the JSON/HTML/overrides-file appliers all use one single
source of truth and can't drift from each other.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import name_clean_lib as ncl

REPO = Path(__file__).resolve().parents[1]

# Hand-corrections for the 2 cases the deterministic cleaner can't get
# right on its own (documented in the review that produced this list):
#  - "RGBwaves": the acronym-boundary heuristic has no way to know "RGB"
#    is followed by a plain lowercase word, not a second capitalized
#    word, and mis-splits it as "RG Bwaves".
#  - The two "Rain Choir ..." entries both clean to "Rain Choir",
#    colliding -- these look like an accidental duplicate download (one
#    folder has a stray "(1)" suffix); keep them distinguishable.
MANUAL_OVERRIDES = {
    'RGBwaves': 'RGB Waves',
    'Rain Choir V1.1 (1)': 'Rain Choir (1)',
}


def build_mapping(names: list[str]) -> dict[str, str]:
    freq = ncl.trailing_freq(names)
    mapping = {}
    for n in names:
        if n in MANUAL_OVERRIDES:
            mapping[n] = MANUAL_OVERRIDES[n]
            continue
        cleaned, _needs_review = ncl.clean_name(n, freq)
        mapping[n] = cleaned
    return mapping


def main():
    ds = json.loads((REPO / 'data/ds-libs.json').read_text())
    kt = json.loads((REPO / 'data/kontakt-libs.json').read_text())

    ds_names = [e['name'] for e in ds]
    kt_names = [e['name'] for e in kt]

    ds_map = build_mapping(ds_names)
    kt_map = build_mapping(kt_names)

    # sanity: no collisions within either set
    for label, m in [('ds', ds_map), ('kt', kt_map)]:
        rev = {}
        for raw, clean in m.items():
            rev.setdefault(clean, []).append(raw)
        collisions = {c: rs for c, rs in rev.items() if len(rs) > 1}
        if collisions:
            print(f'COLLISIONS in {label}:', collisions, file=sys.stderr)
            sys.exit(1)

    out_dir = REPO / 'tools' / '_generated'
    out_dir.mkdir(exist_ok=True)
    (out_dir / 'ds-name-map.json').write_text(json.dumps(ds_map, indent=1, ensure_ascii=False))
    (out_dir / 'kontakt-name-map.json').write_text(json.dumps(kt_map, indent=1, ensure_ascii=False))

    changed_ds = sum(1 for k, v in ds_map.items() if k != v)
    changed_kt = sum(1 for k, v in kt_map.items() if k != v)
    print(f'ds: {changed_ds}/{len(ds_map)} names changed')
    print(f'kt: {changed_kt}/{len(kt_map)} names changed')
    print(f'wrote {out_dir}/ds-name-map.json, {out_dir}/kontakt-name-map.json')


if __name__ == '__main__':
    main()
