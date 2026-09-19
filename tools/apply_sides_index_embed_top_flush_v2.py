#!/usr/bin/env python3
"""
Follow-up to fix-SIDES-INDEX-EMBED-TOP-FLUSH-v1: zeroing the embedded index's
own margin-top wasn't enough. .catalog-body itself (the flex/grid container
that now holds the embedded index as its first child) carries the base
".catalog-body{margin-top:1rem}" rule - normally the gap between the
(non-embedded) collapsed index header and the cards below it. That parent
margin doesn't collapse away (catalog-body establishes its own box via
flex/grid + overflow), so it still pushed the embedded index ~1rem below
#catalogMain's top edge even after the index's own margin was zeroed -
while #searchChrome/#filterWrap keep starting flush.

This patch zeroes .catalog-body's own margin-top too, but only when its
first child is the embedded index (":has(>#catalogIndex.is-embedded:first-
child)"), matching the existing :has() pattern already used elsewhere in
this file for embedded-index-aware layout rules. When the index is NOT
embedded (normal card grid), .catalog-body keeps its usual 1rem top margin.
"""
import re
import sys

FILES = [
    "public/catalogs/DS-CATALOG.html",
    "public/catalogs/DS-CATALOG-portable.html",
    "public/catalogs/KONTAKT-CATALOG.html",
    "public/catalogs/KONTAKT-CATALOG-portable.html",
]

TAG = "SIDES-INDEX-EMBED-TOP-FLUSH-v2"

ANCHOR = (
    "/* SIDES-INDEX-EMBED-TOP-FLUSH-v1: embedded Index flush with "
    "Search/Keywords tops in Sides */\n"
    "body.display-sides #catalogMain>.catalog-body>#catalogIndex.is-embedded:first-child,\n"
    "body.display-middle #catalogMain>.catalog-body>#catalogIndex.is-embedded:first-child,\n"
    "body.catalog-portable #catalogMain>.catalog-body>#catalogIndex.is-embedded:first-child{\n"
    "  margin-top:0!important\n"
    "}"
)

INSERT = (
    "\n/* " + TAG + ": .catalog-body's own top margin doesn't collapse away, "
    "so zero it too when the embedded Index is its first child */\n"
    "body.display-sides #catalogMain>.catalog-body:has(>#catalogIndex.is-embedded:first-child),\n"
    "body.display-middle #catalogMain>.catalog-body:has(>#catalogIndex.is-embedded:first-child),\n"
    "body.catalog-portable #catalogMain>.catalog-body:has(>#catalogIndex.is-embedded:first-child){\n"
    "  margin-top:0!important\n"
    "}"
)


def main():
    changed = []
    for rel in FILES:
        with open(rel, "r", encoding="utf-8") as fh:
            html = fh.read()
        if TAG in html:
            print(f"skip (already applied): {rel}")
            continue
        count = html.count(ANCHOR)
        if count != 1:
            print(f"ERROR: expected 1 match of anchor in {rel}, found {count}", file=sys.stderr)
            sys.exit(1)
        html = html.replace(ANCHOR, ANCHOR + INSERT, 1)
        with open(rel, "w", encoding="utf-8") as fh:
            fh.write(html)
        changed.append(rel)
        print(f"patched: {rel}")
    if not changed:
        print("Nothing to do.")


if __name__ == "__main__":
    main()
