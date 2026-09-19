FILES = [
    "public/catalogs/DS-CATALOG.html",
    "public/catalogs/DS-CATALOG-portable.html",
    "public/catalogs/KONTAKT-CATALOG.html",
    "public/catalogs/KONTAKT-CATALOG-portable.html",
]

ANCHOR = "/* keep the search-autocomplete's own custom scroll indicator, no native scrollbar there */\n.search-autocomplete,#acList.search-autocomplete{scrollbar-width:none!important;-ms-overflow-style:none!important}\n.search-autocomplete::-webkit-scrollbar,#acList.search-autocomplete::-webkit-scrollbar{display:none!important;width:0!important;height:0!important}\n"

INSERT = (
    "/* fix-CATALOGMAIN-DUPE-SCROLLBAR-v1: #catalogMain already has its own custom hover-scroll thumb "
    "(see .hover-scroll-thumb / #catalogMainHoverStripe); its still-styled native ::-webkit-scrollbar "
    "was rendering alongside it as a second, always-on 10px scrollbar (a visible \"dupe\"/shadow bar). "
    "Suppress the native one here the same way search-autocomplete's is suppressed above. */\n"
    "#catalogMain{scrollbar-width:none!important;-ms-overflow-style:none!important}\n"
    "#catalogMain::-webkit-scrollbar{display:none!important;width:0!important;height:0!important}\n"
)

for f in FILES:
    with open(f, encoding="utf-8") as fh:
        html = fh.read()

    if "CATALOGMAIN-DUPE-SCROLLBAR-v1" in html:
        print("skip (already applied)", f)
        continue

    n = html.count(ANCHOR)
    assert n == 1, (f, n)
    html = html.replace(ANCHOR, ANCHOR + INSERT, 1)

    with open(f, "w", encoding="utf-8") as fh:
        fh.write(html)
    print("ok", f)
