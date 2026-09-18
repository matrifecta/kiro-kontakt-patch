#!/usr/bin/env python3
"""
Add English keyword aliases so libraries whose names use a non-English or
obscure instrument word still turn up when searching the English term
(e.g. "flute" should find "Zauberwinds Solo Floete").

Updates, per catalog file: the card's data-kw, the matching index <li>
data-kw, and the KW_CATS map (so new instrument terms categorise under
Instrument rather than falling through to "other"). Also syncs the kw
field in data/ds-libs.json / data/kontakt-libs.json.
"""
import json
import re

DS_FILES = ["public/catalogs/DS-CATALOG.html", "public/catalogs/DS-CATALOG-portable.html"]
KT_FILES = ["public/catalogs/KONTAKT-CATALOG.html", "public/catalogs/KONTAKT-CATALOG-portable.html"]

# name -> English terms to add (only terms the entry is missing get added)
DS_ALIASES = {
    "Zauberwinds Solo Floete": ["flute"],                       # Floete = Flöte
    "Afri Xilo": ["xylophone", "percussion"],                   # Xilo = Xilófono
    "ChingKluay": ["flute", "cymbal"],                          # Khluy = Thai flute, Ching = small cymbals
    "Cymbalum": ["cymbal", "percussion"],
    "Duduk": ["flute", "woodwind"],                             # Armenian double-reed
    "My Duduk": ["duduk", "reed", "flute", "woodwind"],
    "Flutina": ["accordion"],                                   # Flutina is an early accordion
    "Gankogui": ["bell", "percussion"],                         # West African double bell
    "Gjallar Horn": ["horn", "brass"],
    "Gusli Perepyolochka": ["zither", "strings", "harp"],       # gusli = Russian psaltery/zither
    "Hurdy Gurdy": ["strings", "bowed"],
    "Kantele The Finnish Zither": ["zither", "strings", "harp"],
    "Morpho Lute By Magisk": ["lute", "strings"],
    "Schlagwerk U78 Side Skin Udu": ["percussion", "drum"],     # Schlagwerk = percussion
    "Sonus Lucis - Cymbalon": ["dulcimer"],                     # lap harp / cimbalom family
    "Three Strings Domra": ["lute", "mandolin"],                # domra = Russian lute
    "Tunnel Bodhran": ["bodhran", "drum", "percussion"],        # Irish frame drum
    "Warty Dulcitone": ["keys", "piano"],                       # tuning-fork keyboard
    "Wiedergesichts Wurli": ["wurlitzer", "keys"],
    "Destinys Agent - Zitherone": ["zither", "strings"],
    "Glockenglass": ["glockenspiel", "bell"],
    "Maracas by Estudios Ivcame": ["maracas", "percussion", "shaker"],
}

KT_ALIASES = {
    "Balinese Gamelan": ["percussion"],
    "Tablas": ["tabla", "drum", "percussion"],
    "Cinebrass": ["brass", "orchestral"],
    "Voxos": ["choir", "vocal", "voice"],
}

# new terms that should categorise as instruments in the pill bar
NEW_KW_CATS = {
    "cymbal": "instrument",
    "dulcimer": "instrument",
    "bodhran": "instrument",
    "maracas": "instrument",
    "shaker": "instrument",
    "glockenspiel": "instrument",
    "zither": "instrument",
    "duduk": "instrument",
    "tabla": "instrument",
    "orchestral": "vibe",
}


def merge_kw(existing, additions):
    have = [t for t in existing.split() if t]
    for t in additions:
        if t not in have:
            have.append(t)
    return " ".join(have)


def patch_file(path, aliases):
    txt = open(path, encoding="utf-8").read()
    changed = 0
    for name, adds in aliases.items():
        esc = re.escape(name)
        # --- card entry ---
        pat = re.compile(r'(<div class="entry" id="item-\d+" data-kw=")([^"]*)("[^>]*data-name="' + esc + r'")')
        def repl(m):
            return m.group(1) + merge_kw(m.group(2), adds) + m.group(3)
        txt, n = pat.subn(repl, txt, count=1)
        if not n:
            print(f"  WARN: card not found for {name!r} in {path}")
        else:
            changed += 1
        # --- index list item (matched via its anchor text) ---
        ipat = re.compile(r'(<li data-kw=")([^"]*)("><a href="#item-\d+">' + esc + r'</a></li>)')
        txt, ni = ipat.subn(lambda m: m.group(1) + merge_kw(m.group(2), adds) + m.group(3), txt, count=1)
        if not ni:
            print(f"  note: index row not found for {name!r} in {path}")

    # --- KW_CATS additions ---
    mcats = re.search(r'var KW_CATS=\{', txt)
    if mcats:
        missing = {k: v for k, v in NEW_KW_CATS.items() if f'"{k}":' not in txt[mcats.start():mcats.start() + 40000]}
        if missing:
            inject = "".join(f'"{k}":"{v}",' for k, v in missing.items())
            txt = txt[:mcats.end()] + inject + txt[mcats.end():]
            print(f"  KW_CATS += {list(missing)}")
    open(path, "w", encoding="utf-8").write(txt)
    print(f"{path}: {changed}/{len(aliases)} cards updated")


def patch_json(path, aliases):
    data = json.load(open(path, encoding="utf-8"))
    hit = 0
    for entry in data:
        adds = aliases.get(entry.get("name"))
        if adds:
            entry["kw"] = merge_kw(entry.get("kw", ""), adds)
            hit += 1
    json.dump(data, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"{path}: {hit} entries updated")


def main():
    for f in DS_FILES:
        patch_file(f, DS_ALIASES)
    for f in KT_FILES:
        patch_file(f, KT_ALIASES)
    patch_json("data/ds-libs.json", DS_ALIASES)
    patch_json("data/kontakt-libs.json", KT_ALIASES)


if __name__ == "__main__":
    main()
