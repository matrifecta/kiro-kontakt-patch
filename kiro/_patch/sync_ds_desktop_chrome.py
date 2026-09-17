#!/usr/bin/env python3
"""Copy Kontakt desktop chrome/CSS/JS onto DS catalog data."""
from pathlib import Path

ROOT = Path("/home/phnx/kiro-kontakt-patch/public/catalogs")
K = ROOT / "KONTAKT-CATALOG.html"
D = ROOT / "DS-CATALOG.html"
OUT = D


def main():
    k = K.read_text(encoding="utf-8")
    d = D.read_text(encoding="utf-8")

    body_mark = "</style></head><body class=\"search-mode\">\n"
    if body_mark not in k:
        raise SystemExit("kontakt body mark missing")
    k_head, k_rest = k.split(body_mark, 1)

    ix_list_mark = '<ul class="index" id="catalogIndexList">\n'
    if ix_list_mark not in k_rest:
        raise SystemExit("kontakt index list mark missing")
    k_chrome, k_after_ix_open = k_rest.split(ix_list_mark, 1)
    k_ix_close = "</ul></div>\n<div class=\"catalog-body\">"
    if k_ix_close not in k_after_ix_open:
        raise SystemExit("kontakt index close missing")
    _, k_body_and_tail = k_after_ix_open.split(k_ix_close, 1)
    # k_body_and_tail starts with catalog-body contents AFTER the opening tag we consumed
    aside_mark = '<aside class="catalog-doc-note'
    if aside_mark not in k_body_and_tail:
        raise SystemExit("kontakt aside mark missing")
    k_tail = aside_mark + k_body_and_tail.split(aside_mark, 1)[1]

    ds_ix_open = "<h2>Index (alphabetical)</h2><ul class=\"index\">\n"
    if ds_ix_open not in d:
        raise SystemExit("ds index open missing")
    ds_after_ix = d.split(ds_ix_open, 1)[1]
    ds_ix_end = "</ul>\n<div class=\"catalog-body\">"
    if ds_ix_end not in ds_after_ix:
        raise SystemExit("ds index end missing")
    ds_lis, ds_after_body_open = ds_after_ix.split(ds_ix_end, 1)
    # ds_after_body_open is catalog-body inner... until <a class="top"
    top_mark = '<a class="top" href="#top">'
    if top_mark not in ds_after_body_open:
        raise SystemExit("ds top mark missing")
    ds_body = ds_after_body_open.split(top_mark, 1)[0].rstrip() + "\n"

    gen = ""
    if "<p>generated:" in d:
        g0 = d.find("<p>generated:")
        g1 = d.find("</p>", g0)
        gen = d[g0 : g1 + 4]
    extra = ""
    if "<p><b>Added libraries?</b>" in d:
        e0 = d.find("<p><b>Added libraries?</b>")
        e1 = d.find("</p>", e0)
        extra = d[e0 : e1 + 4]

    # Adapt Kontakt head/chrome/tail for DS
    head = (
        k_head.replace("catalog-ui-scale-kontakt", "catalog-ui-scale-ds")
        .replace("catalog-search-only-ui-scale-kontakt", "catalog-search-only-ui-scale-ds")
        .replace("<title>Kontakt Library</title>", "<title>DecentSampler Library Catalog</title>")
    )
    chrome = k_chrome.replace(">Kontakt Library</h1>", ">DecentSampler Library Catalog</h1>")
    tail = k_tail.replace('var CATALOG_NS="kontakt";window.CATALOG_NS="kontakt";', 'var CATALOG_NS="ds";window.CATALOG_NS="ds";')
    if gen:
        # replace first generated paragraph inside doc note
        import re

        tail = re.sub(r"<p>generated:.*?</p>", gen, tail, count=1)
        if extra and "Added libraries?" not in tail:
            tail = tail.replace(gen, gen + extra, 1)
        if extra:
            tail = tail.replace(
                "<p>Registered Kontakt libraries (from komplete.db3). Click a name to jump; [open folder] opens the library in Dolphin.</p>",
                extra,
            )
        else:
            tail = tail.replace(
                "<p>Registered Kontakt libraries (from komplete.db3). Click a name to jump; [open folder] opens the library in Dolphin.</p>",
                "<p>Library-level; expand a library to see its patches (grouped by subfolder).</p>",
            )

    out = (
        head
        + body_mark
        + chrome
        + ix_list_mark
        + ds_lis
        + "</ul></div>\n<div class=\"catalog-body\">"
        + ds_body
        + tail
    )
    if not out.strip().endswith("</html>"):
        raise SystemExit("output missing html end")
    if 'CATALOG_NS="ds"' not in out:
        raise SystemExit("ns not ds")
    if "id=\"hdrSearchBtn\"" not in out:
        raise SystemExit("missing hdr search")
    if "function collapseAllPatchTrees" not in out:
        raise SystemExit("missing collapse fn")
    if 'id="item-1"' not in ds_body:
        raise SystemExit("missing ds cards")
    if "5Elements" in ds_lis:
        raise SystemExit("kontakt index leaked into ds")

    b = out.encode("utf-8")
    tmp = ROOT.parent.parent / "kiro/_patch/_ds_chrome_tmp.html"
    tmp.write_bytes(b)
    if tmp.stat().st_size != len(b):
        raise SystemExit("tmp size mismatch")
    OUT.write_bytes(b)
    got = OUT.read_bytes()
    if got != b:
        raise SystemExit("final size mismatch")
    tmp.unlink()
    print(
        "OK bytes",
        len(b),
        "lines",
        out.count("\n"),
        "entries",
        out.count('<div class="entry"'),
        "index li",
        ds_lis.count("<li "),
    )


if __name__ == "__main__":
    main()
