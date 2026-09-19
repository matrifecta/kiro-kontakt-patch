FILES = [
    "public/catalogs/DS-CATALOG.html",
    "public/catalogs/DS-CATALOG-portable.html",
    "public/catalogs/KONTAKT-CATALOG.html",
    "public/catalogs/KONTAKT-CATALOG-portable.html",
]

OLD = ".hover-scroll-thumb{position:absolute;top:0;right:1px;width:3px;min-height:1.15rem;border-radius:999px;background:var(--accent-instrument);opacity:.4;box-shadow:0 0 0 1px var(--border);cursor:grab;touch-action:none;transform-origin:right center;translate:0 var(--thumb-y,0px);scale:1 1;will-change:translate;transition:width .14s ease,opacity .14s ease,scale .14s ease}"
NEW = ".hover-scroll-thumb{position:absolute;top:0;right:1px;width:3px;min-height:1.15rem;border-radius:999px;background:var(--accent-instrument);opacity:.4;cursor:grab;touch-action:none;transform-origin:right center;translate:0 var(--thumb-y,0px);scale:1 1;will-change:translate;transition:width .14s ease,opacity .14s ease,scale .14s ease}"

for f in FILES:
    with open(f, encoding="utf-8") as fh:
        html = fh.read()

    if "SCROLL-THUMB-NO-RING-v1" in html:
        print("skip (already applied)", f)
        continue

    n = html.count(OLD)
    assert n == 1, (f, n)
    html = html.replace(
        OLD,
        "/* fix-SCROLL-THUMB-NO-RING-v1: dropped the 1px box-shadow ring around the semi-transparent thumb -- at low opacity, "
        "the faded ring rendered as a second faint outline hugging the thumb, reading as a duplicated/\"shadow\" scrollbar. "
        "The thumb's own fill + border-radius is enough to read as a scrollbar without it. */\n" + NEW,
        1,
    )

    with open(f, "w", encoding="utf-8") as fh:
        fh.write(html)
    print("ok", f)
