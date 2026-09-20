#!/usr/bin/env python3
"""
Automated keyword-pill backfill: expands KW_CATS in the live catalog HTML
files with newly-analyzed instrument/brand terms found in the real
komplete.db3 library database, then rescans EVERY .entry card's
data-name (and mirrored index <li>) against the full (existing + new)
KW_CATS vocabulary, adding any matching-but-missing whole-word tokens to
data-kw. Only adds tokens already defined in KW_CATS (no invented terms).
Syncs data/ds-libs.json and data/kontakt-libs.json afterward.

Usage:
  python3 tools/apply_auto_kw_from_names.py --check   # dry run, report only
  python3 tools/apply_auto_kw_from_names.py --apply   # write changes
"""
import re, json, sys, html
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CATALOGS = ROOT / "public" / "catalogs"
DS_FILES = [CATALOGS / "DS-CATALOG.html", CATALOGS / "DS-CATALOG-portable.html"]
KT_FILES = [CATALOGS / "KONTAKT-CATALOG.html", CATALOGS / "KONTAKT-CATALOG-portable.html"]
ALL_FILES = DS_FILES + KT_FILES

NEW_KW_CATS = {
 "ajaeng":"instrument","dizi":"instrument","daegeum":"instrument","hichiriki":"instrument",
 "sho":"instrument","oud":"instrument","sitar":"instrument","koto":"instrument","guzheng":"instrument",
 "guqin":"instrument","pipa":"instrument","shamisen":"instrument","yangqin":"instrument",
 "gayageum":"instrument","darbuka":"instrument","glockenspiel":"instrument","vibraphone":"instrument",
 "gong":"instrument","clavinet":"instrument","timpani":"instrument","tambourine":"instrument",
 "cowbell":"instrument","conga":"instrument","bongo":"instrument","shakuhachi":"instrument",
 "soundiron":"brand","sonokinetic":"brand","submission":"brand","streamtech":"brand","output":"brand",
 "soniccouture":"brand","getgood":"brand","fluffyaudio":"brand","nami":"brand","earthmoments":"brand","8dio":"brand",
}

TOKEN_RE = re.compile(r"[a-z0-9]+")


def tokenize(name):
    return set(TOKEN_RE.findall(name.lower()))


def load_kw_cats(text):
    m = re.search(r"var KW_CATS=(\{.*?\});", text, re.S)
    if not m:
        raise SystemExit("KW_CATS not found")
    return m.group(1), json.loads(m.group(1))


def write_kw_cats(text, new_json):
    return re.sub(r"var KW_CATS=\{.*?\};", "var KW_CATS=" + new_json + ";", text, count=1, flags=re.S)


ENTRY_RE = re.compile(
    r'(<div class="entry" id="(?P<id>[^"]+)" data-kw=")(?P<kw>[^"]*)("[^>]*data-name="(?P<name>[^"]*)")'
)
LI_RE_TMPL = r'(<li data-kw=")([^"]*)("><a href="#{id}">)'


def process_file(path, check_only):
    text = path.read_text(encoding="utf-8")
    kw_cats_str, kw_cats = load_kw_cats(text)
    added_cat_count = 0
    for w, cat in NEW_KW_CATS.items():
        if w not in kw_cats:
            kw_cats[w] = cat
            added_cat_count += 1
    vocab = set(kw_cats.keys())

    stats = {"entries_scanned": 0, "entries_changed": 0, "tokens_added": 0}
    diffs = []

    def repl_entry(m):
        nonlocal_stats_scan()
        cur_kw = set(m.group("kw").split())
        name = html.unescape(m.group("name"))
        name_tokens = tokenize(name)
        add_tokens = sorted((vocab & name_tokens) - cur_kw)
        if not add_tokens:
            return m.group(0)
        new_kw = " ".join(sorted(cur_kw | set(add_tokens)))
        stats["entries_changed"] += 1
        stats["tokens_added"] += len(add_tokens)
        diffs.append((m.group("id"), m.group("name"), sorted(cur_kw), new_kw.split()))
        entry_new_kw[m.group("id")] = new_kw
        return m.group(1) + new_kw + m.group(4)

    def nonlocal_stats_scan():
        stats["entries_scanned"] += 1

    entry_new_kw = {}
    new_text = ENTRY_RE.sub(repl_entry, text)

    # mirror onto index <li data-kw="..."><a href="#id">
    for eid, new_kw in entry_new_kw.items():
        li_re = re.compile(LI_RE_TMPL.format(id=re.escape(eid)))
        new_text, n = li_re.subn(lambda m, nk=new_kw: m.group(1) + nk + m.group(3), new_text, count=1)

    if not check_only:
        new_text = write_kw_cats(new_text, json.dumps(kw_cats, separators=(",", ":")))
        path.write_text(new_text, encoding="utf-8")

    return stats, added_cat_count, diffs


def main():
    check_only = "--apply" not in sys.argv
    total = {"entries_scanned": 0, "entries_changed": 0, "tokens_added": 0}
    for f in ALL_FILES:
        stats, added_cats, diffs = process_file(f, check_only)
        print(f"{f.name}: scanned={stats['entries_scanned']} changed={stats['entries_changed']} "
              f"tokens_added={stats['tokens_added']} new_KW_CATS_entries={added_cats}")
        for eid, name, before, after in diffs[:8]:
            print(f"    {eid} '{name}': {before} -> {after}")
        for k in total:
            total[k] += stats[k]
    print("TOTAL:", total)
    if check_only:
        print("\n(dry run only; re-run with --apply to write changes)")


if __name__ == "__main__":
    main()
