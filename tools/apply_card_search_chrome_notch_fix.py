import re

FILES = [
    "public/catalogs/DS-CATALOG.html",
    "public/catalogs/DS-CATALOG-portable.html",
    "public/catalogs/KONTAKT-CATALOG.html",
    "public/catalogs/KONTAKT-CATALOG-portable.html",
]

OLD_BTN = '    <button type="button" class="card-search-popup" onclick="event.preventDefault();event.stopPropagation();cardSearchOpenPopup()">Open in popup</button>\n'
OLD_CSS = " .card-search-chrome{display:flex;align-items:center;gap:var(--card-chrome-gap);flex-shrink:0;padding:.5rem .625rem;background:var(--bg-surface);border-bottom:1px solid var(--border);color:var(--text)}"
NEW_CSS = " .card-search-chrome{display:flex;align-items:center;gap:var(--card-chrome-gap);flex-shrink:0;padding:.5rem max(.625rem,env(safe-area-inset-right,0px)) .5rem max(.625rem,env(safe-area-inset-left,0px));background:var(--bg-surface);border-bottom:1px solid var(--border);color:var(--text)}"

for f in FILES:
    with open(f, encoding="utf-8") as fh:
        html = fh.read()

    if "NOTCH-CHROME-v1" in html:
        print("skip (already applied)", f)
        continue

    n_btn = html.count(OLD_BTN)
    assert n_btn == 1, (f, "btn", n_btn)
    html = html.replace(OLD_BTN, "", 1)

    n_css = html.count(OLD_CSS)
    assert n_css == 1, (f, "css", n_css)
    html = html.replace(
        OLD_CSS,
        "/* fix-NOTCH-CHROME-v1: card-search-chrome respects left/right safe-area (notch) insets; \"Open in popup\" removed from the embed toolbar (redundant once the embed itself is showing) */\n" + NEW_CSS,
        1,
    )

    with open(f, "w", encoding="utf-8") as fh:
        fh.write(html)
    print("ok", f)
