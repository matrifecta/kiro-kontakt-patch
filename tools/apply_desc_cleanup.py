#!/usr/bin/env python3
"""Clean up <p class="desc"> text in all 4 catalog HTML files: strip
markdown/header/version boilerplate, engine-mention sentences, links,
and translate non-English text -- driven by tools/_generated/desc_auto.json
(deterministic pass) plus tools/_generated/desc_overrides.json (manual
rewrites/translations) and tools/_generated/desc_empty.json (entries with
no real content left, replaced with a neutral placeholder).
"""
import html as htmllib
import json
import re
import sys

PLACEHOLDER = "No additional description provided."

GEN = "tools/_generated"
FILES = {
    "ds": ["public/catalogs/DS-CATALOG.html", "public/catalogs/DS-CATALOG-portable.html"],
    "kt": ["public/catalogs/KONTAKT-CATALOG.html", "public/catalogs/KONTAKT-CATALOG-portable.html"],
}


def is_placeholder_raw(raw_unescaped: str) -> bool:
    if raw_unescaped.startswith("Decent Sampler library:") or raw_unescaped.startswith("Kontakt library:"):
        return True
    if re.match(r'^Native Instruments library:\s*[^.]*\.\s*(?:Tags:.*)?$', raw_unescaped.strip(), re.I):
        return True
    return False


def build_final_map():
    auto = json.load(open(f"{GEN}/desc_auto.json", encoding="utf-8"))
    empty = set(json.load(open(f"{GEN}/desc_empty.json")))
    overrides = json.load(open(f"{GEN}/desc_overrides.json", encoding="utf-8"))

    final = {}
    for key, v in auto.items():
        if key in overrides:
            final[key] = overrides[key]
        elif key in empty:
            final[key] = PLACEHOLDER
        else:
            final[key] = v["auto"]
    # overrides may reference keys not in auto (defensive)
    for key, text in overrides.items():
        final.setdefault(key, text)
    return final


def apply_to_file(path, cat, final_map, raw_data):
    txt = open(path, encoding="utf-8").read()
    changed = 0
    for itemid, name, raw in raw_data:
        key = f"{itemid}|{cat}"
        if key not in final_map:
            continue
        raw_unescaped = htmllib.unescape(raw)
        if is_placeholder_raw(raw_unescaped):
            continue
        new_text = final_map[key]
        new_escaped = htmllib.escape(new_text, quote=False)
        # scope the replacement to this entry's block
        entry_re = re.compile(
            r'(<div class="entry" id="' + re.escape(itemid) + r'"[^>]*>.*?<p class="desc">)'
            + re.escape(raw) + r'(</p>)',
            re.S,
        )
        new_txt, n = entry_re.subn(lambda m: m.group(1) + new_escaped + m.group(2), txt, count=1)
        if n == 1:
            txt = new_txt
            changed += 1
        else:
            print(f"  WARN: no match for {itemid} ({name}) in {path}", file=sys.stderr)
    open(path, "w", encoding="utf-8").write(txt)
    print(f"{path}: {changed} descriptions updated")


def main():
    final_map = build_final_map()
    raw = json.load(open(f"{GEN}/desc_raw.json"))
    for cat, entries in (("ds", raw["ds"]), ("kt", raw["kt"])):
        for path in FILES[cat]:
            apply_to_file(path, cat, final_map, entries)


if __name__ == "__main__":
    main()
