FILES = [
    "public/catalogs/DS-CATALOG.html",
    "public/catalogs/DS-CATALOG-portable.html",
    "public/catalogs/KONTAKT-CATALOG.html",
    "public/catalogs/KONTAKT-CATALOG-portable.html",
]

OLD_SPAN = '    <span class="card-search-title" id="cardSearchTitle">Search</span>\n'
OLD_TOGGLE_CSS = ' .card-search-switch-toggle{flex:0 0 auto;min-width:2.75rem;padding:0;display:inline-flex;align-items:center;justify-content:center}'
NEW_TOGGLE_CSS = ' .card-search-switch-toggle{flex:0 0 auto;min-width:2.75rem;padding:0;display:inline-flex;align-items:center;justify-content:center;margin-left:auto}'

for f in FILES:
    with open(f, encoding="utf-8") as fh:
        html = fh.read()

    if "NOTCH-TITLE-LABEL-v1" in html:
        print("skip (already applied)", f)
        continue

    n_span = html.count(OLD_SPAN)
    assert n_span == 1, (f, "span", n_span)
    html = html.replace(OLD_SPAN, "", 1)

    n_css = html.count(OLD_TOGGLE_CSS)
    assert n_css == 1, (f, "css", n_css)
    html = html.replace(
        OLD_TOGGLE_CSS,
        "/* fix-NOTCH-TITLE-LABEL-v1: title label removed from the embed toolbar (kept it out from under a side notch in landscape); switch-toggle now pushes the remaining right-side buttons to the end of the row */\n" + NEW_TOGGLE_CSS,
        1,
    )

    with open(f, "w", encoding="utf-8") as fh:
        fh.write(html)
    print("ok", f)
