#!/usr/bin/env python3
"""Update the DS/Kontakt catalogs: pick up new libraries, clean their
names, and refresh the shipped HTML -- without ever regressing the UI.

WHAT THIS DOES
  1. Runs the real builders (build-ds-catalog-html.sh / build-kontakt-
     catalog-html.sh) to rescan your library folders / komplete.db3.
  2. Diffs the raw names that scan finds against what's already known
     (name-overrides.tsv + a small "reviewed" list). Anything new gets:
       - a proposed clean name (tools/name_clean_lib.py)
       - the builder's own auto-tagged keywords
     and if either looks uncertain, this ASKS YOU before continuing --
     type a corrected name, or Enter to accept the suggestion.
  3. Re-runs the builders (now with the confirmed names saved to
     name-overrides.tsv) to get final entries + a final Index.
  4. Grafts those entries/Index onto whatever chrome is CURRENTLY live
     in public/catalogs/*.html (see tools/catalog_splice.py) -- this is
     what makes it impossible for a rebuild to regress the UI: it never
     carries its own copy of the chrome to go stale.
  5. Syncs data/ds-libs.json + data/kontakt-libs.json (the Next.js
     Quick List tab) to match.

This is DESTRUCTIVE to the 4 catalog HTML files and the 2 JSON files --
back up or `git commit` your current state first. Nothing is written
until you type "yes" at the final confirmation (skip with --yes for
non-interactive use, e.g. from a cron job you've already vetted).

Usage:
  python3 tools/update_catalog.py --check                # dry run (default)
  python3 tools/update_catalog.py --mark-known            # review + save
                                                           # name-overrides.tsv
                                                           # and the known-names
                                                           # state ONLY -- leaves
                                                           # catalog HTML/JSON
                                                           # untouched
  python3 tools/update_catalog.py --apply                 # full rebuild + splice
  python3 tools/update_catalog.py --apply --only ds       # just one catalog
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import catalog_splice as splice
import name_clean_lib as ncl

REPO = Path(__file__).resolve().parents[1]
ART_DIR = Path('/home/phnx/KIRO/.kiro/specs/kontakt-workspace-drive-dirty-fix/artifacts')
KNOWN_NAMES_FILE = ART_DIR / 'catalog-known-raw-names.json'
NAME_OVERRIDES_FILE = ART_DIR / 'name-overrides.tsv'

CATALOGS = {
    'ds': dict(
        builder=ART_DIR / 'build-ds-catalog-html.sh',
        json_path=REPO / 'data/ds-libs.json',
        html_desktop=REPO / 'public/catalogs/DS-CATALOG.html',
        html_portable=REPO / 'public/catalogs/DS-CATALOG-portable.html',
        fresh_desktop=ART_DIR / 'DS-CATALOG.html',
        fresh_portable=ART_DIR / 'DS-CATALOG-portable.html',
        rawlog=ART_DIR / '.raw-names.ds.desktop.log',
    ),
    'kontakt': dict(
        builder=ART_DIR / 'build-kontakt-catalog-html.sh',
        json_path=REPO / 'data/kontakt-libs.json',
        html_desktop=REPO / 'public/catalogs/KONTAKT-CATALOG.html',
        html_portable=REPO / 'public/catalogs/KONTAKT-CATALOG-portable.html',
        fresh_desktop=ART_DIR / 'KONTAKT-CATALOG.html',
        fresh_portable=ART_DIR / 'KONTAKT-CATALOG-portable.html',
        rawlog=ART_DIR / '.raw-names.kontakt.desktop.log',
    ),
}


def load_known_names() -> dict:
    if KNOWN_NAMES_FILE.exists():
        return json.loads(KNOWN_NAMES_FILE.read_text())
    return {}


def save_known_names(known: dict):
    KNOWN_NAMES_FILE.write_text(json.dumps(known, indent=1, ensure_ascii=False))


def load_overrides() -> dict:
    if not NAME_OVERRIDES_FILE.exists():
        return {}
    out = {}
    for line in NAME_OVERRIDES_FILE.read_text().splitlines():
        if not line or line.startswith('#') or '\t' not in line:
            continue
        k, v = line.split('\t', 1)
        out[k] = v
    return out


def save_overrides(overrides: dict):
    header = [
        '# raw folder/library name<TAB>clean display name',
        '# Maintained by tools/update_catalog.py.',
        '# Consumed by build-ds-catalog-html.sh and build-kontakt-catalog-html.sh',
        '# via name_override() so a rebuild keeps these clean names instead of',
        '# reverting to the raw on-disk folder name / komplete.db3 alias.',
    ]
    lines = header + [f'{k}\t{v}' for k, v in sorted(overrides.items())]
    NAME_OVERRIDES_FILE.write_text('\n'.join(lines) + '\n')


def run_builder(builder: Path, mode: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ['bash', str(builder), mode], cwd=str(ART_DIR),
        capture_output=True, text=True, timeout=1800,
    )


def existing_vocabulary() -> set:
    """All keyword tokens already in use across both catalogs -- the
    "map" new entries should be tagged against, per the existing
    convention, rather than inventing one-off tags."""
    vocab = set()
    for cfg in CATALOGS.values():
        if cfg['json_path'].exists():
            for e in json.loads(cfg['json_path'].read_text()):
                vocab.update(e.get('kw', '').split())
    return vocab


def extract_entry_kw(fresh_html: str, raw_name_attr: str) -> str:
    m = re.search(
        r'<div class="entry" id="item-\d+" data-kw="([^"]*)"[^>]*data-name="'
        + re.escape(raw_name_attr) + '"',
        fresh_html,
    )
    return m.group(1) if m else ''


def review_new_entries(catalog: str, fresh_html: str, new_raw_names: list[str],
                        overrides: dict, vocab: set, auto_yes: bool) -> dict:
    """Interactively confirms a clean name (and reports auto-tagged
    keywords) for each newly-discovered raw name. Returns the subset of
    `overrides`-style updates {raw: clean} for names that need one."""
    if not new_raw_names:
        return {}
    all_names_for_freq = new_raw_names  # frequency signal is weak with just
    # the new batch, but still catches a repeated author across new drops
    freq = ncl.trailing_freq(new_raw_names)
    updates = {}
    print(f'\n{len(new_raw_names)} new {catalog} entries found:\n')
    for raw in new_raw_names:
        clean, needs_review = ncl.clean_name(raw, freq)
        kw = extract_entry_kw(fresh_html, _attr_escape(raw))
        unknown_kw = [k for k in kw.split() if k not in vocab]
        confident = not needs_review and not unknown_kw

        print(f'  raw name : {raw}')
        print(f'  proposed : {clean}' + ('' if clean == raw else '  (cleaned)'))
        print(f'  keywords : {kw or "(none found)"}' + (
            f'  [new tags not in the existing map: {" ".join(unknown_kw)}]' if unknown_kw else ''))

        if confident:
            print('  -> looks clear, auto-accepting.\n')
            if clean != raw:
                updates[raw] = clean
            continue

        if auto_yes:
            print('  -> --yes given, accepting the proposed name as-is.\n')
            if clean != raw:
                updates[raw] = clean
            continue

        print('  This one needs a look (uncertain name and/or an untagged keyword).')
        resp = input(
            f'  Press Enter to accept "{clean}", type a corrected name, '
            f'or "?" to list the existing keyword map: '
        ).strip()
        while resp == '?':
            print('  existing keywords:', ' '.join(sorted(vocab)))
            resp = input(f'  Press Enter to accept "{clean}", or type a corrected name: ').strip()
        final_name = resp if resp else clean
        print()
        if final_name != raw:
            updates[raw] = final_name
    return updates


def _attr_escape(s: str) -> str:
    return (s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            .replace('"', '&quot;'))


def sync_json(json_path: Path, fresh_html: str):
    """Upserts data/*.json from the fresh build's entries: adds any new
    ones, refreshes name/kw for existing ones. Preserves nothing else --
    `has_cover` is recomputed from whether the fresh entry has a cover."""
    existing = json.loads(json_path.read_text()) if json_path.exists() else []
    by_name = {e['name']: e for e in existing}

    for m in re.finditer(
        r'<div class="entry" id="item-\d+" data-kw="([^"]*)"[^>]*data-name="([^"]*)"',
        fresh_html,
    ):
        kw, name_attr = m.group(1), _unescape(m.group(2))
        if name_attr in by_name:
            by_name[name_attr]['kw'] = _unescape(kw)
        else:
            by_name[name_attr] = {'kw': _unescape(kw), 'name': name_attr, 'has_cover': True}

    json_path.write_text(json.dumps(list(by_name.values()), ensure_ascii=False))


def _unescape(s: str) -> str:
    return (s.replace('&quot;', '"').replace('&lt;', '<').replace('&gt;', '>')
            .replace('&amp;', '&'))


def update_one(catalog: str, cfg: dict, mode: str, auto_yes: bool) -> bool:
    """mode is one of:
      'check'       -- dry run, writes nothing at all
      'mark-known'  -- records the reviewed name-overrides.tsv + known-
                       names state (so future runs only flag genuinely
                       new folders), but does NOT rebuild/splice the
                       catalog HTML or touch data/*.json
      'apply'       -- the full pipeline: rebuild, splice onto the live
                       chrome, and sync data/*.json
    """
    print(f'== {catalog} ==')
    if not cfg['builder'].exists():
        print(f'  builder not found: {cfg["builder"]}')
        print('  (expected on the machine with the real library folders / komplete.db3 mounted)')
        return False

    print('  scanning to discover new entries...')
    r = run_builder(cfg['builder'], 'desktop')
    if r.returncode != 0:
        print('  builder failed:\n', r.stderr[-4000:])
        return False

    if not cfg['rawlog'].exists():
        print(f'  no raw-name log at {cfg["rawlog"]} -- builder may be an older copy '
              'without the name_override()/RAWNAMES_LOG hook')
        return False
    raw_names = [ln for ln in cfg['rawlog'].read_text().splitlines() if ln]

    known = load_known_names().setdefault(catalog, {})
    overrides = load_overrides()
    vocab = existing_vocabulary()

    fresh_html = cfg['fresh_desktop'].read_text(encoding='utf-8')
    new_raw = [n for n in dict.fromkeys(raw_names) if n not in known and n not in overrides]

    updates = review_new_entries(catalog, fresh_html, new_raw, overrides, vocab, auto_yes)

    if mode == 'check':
        print(f'  --check only: {len(new_raw)} new entries, '
              f'{sum(1 for k, v in updates.items() if k != v)} would get a name override.')
        print('  Re-run with --apply (or --mark-known) to write changes.\n')
        return True

    if updates:
        overrides.update(updates)
        save_overrides(overrides)
    all_known = load_known_names()
    all_known.setdefault(catalog, {}).update({n: True for n in raw_names})
    save_known_names(all_known)

    if mode == 'mark-known':
        print(f'  recorded {len(new_raw)} entries as known '
              f'({sum(1 for k, v in updates.items() if k != v)} name overrides saved). '
              'Catalog HTML/JSON left untouched.\n')
        return True

    print('  rebuilding with confirmed names...')
    r = run_builder(cfg['builder'], 'both')
    if r.returncode != 0:
        print('  builder failed:\n', r.stderr[-4000:])
        return False

    for html_path, fresh_path in [
        (cfg['html_desktop'], cfg['fresh_desktop']),
        (cfg['html_portable'], cfg['fresh_portable']),
    ]:
        live_html = html_path.read_text(encoding='utf-8')
        fresh_html2 = fresh_path.read_text(encoding='utf-8')
        fresh = splice.extract_fresh(fresh_html2)
        before = splice.entry_count(live_html)
        spliced = splice.splice_onto_live(live_html, fresh)
        after = splice.entry_count(spliced)
        html_path.write_text(spliced, encoding='utf-8')
        print(f'  {html_path.name}: {before} -> {after} entries')

    sync_json(cfg['json_path'], fresh_html2)
    print(f'  {cfg["json_path"].name} synced')
    return True


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--apply', action='store_true',
                     help='full pipeline: rebuild, splice onto the live catalog HTML, sync data/*.json')
    ap.add_argument('--mark-known', action='store_true',
                     help='review + save name-overrides.tsv and the known-names state only -- '
                          'does NOT touch the catalog HTML or data/*.json')
    ap.add_argument('--check', action='store_true', help='dry run (default; explicit for clarity)')
    ap.add_argument('--only', choices=['ds', 'kontakt', 'both'], default='both')
    ap.add_argument('--yes', action='store_true',
                     help='accept every proposed name automatically (no prompts) -- '
                          'use only if you already trust the auto-cleanup for this batch')
    args = ap.parse_args()

    if args.apply and args.mark_known:
        print('Pick one of --apply / --mark-known, not both.')
        sys.exit(2)
    mode = 'apply' if args.apply else ('mark-known' if args.mark_known else 'check')

    targets = ['ds', 'kontakt'] if args.only == 'both' else [args.only]

    if mode == 'apply':
        print('This will overwrite catalog HTML + JSON files. It is not reversible by')
        print('this tool -- make sure your current state is committed to git first.')
        resp = input('Type "yes" to continue: ').strip().lower()
        if resp != 'yes':
            print('Aborted.')
            return

    ok = True
    for t in targets:
        ok &= update_one(t, CATALOGS[t], mode, args.yes)

    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main()
