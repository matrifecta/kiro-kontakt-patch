#!/usr/bin/env python3
"""
Fix: in Sides layout (Search/Keywords beside the content column), the
embedded alphabetical Index block sits inside #catalogMain > .catalog-body
and picks up its own decorative top spacing (margin-top:.45rem, from the
"fix-IX-DOC-EMBED-FLOW" / "fix-INDEX-EMBED-BLOCK-v1" rules) meant to give it
breathing room when it floats among the cards. But when it's the very first
thing in the content column, that margin pushes its top ~7px below
#catalogMain's own top edge - while #searchChrome/#filterWrap (the Search and
Keywords panes) start flush with no such offset. The result: the content
column visibly starts lower than the menu panes instead of lining up with
them.

This patch adds a Sides-layout override that zeroes the top margin only when
the embedded index is the first child of .catalog-body (i.e. sitting right at
the top of the content column), so it lines up flush with the Search/
Keywords panes above. It keeps its bottom margin and its own border/background
box styling - no visible outline is added to the content pane itself, this
only removes the leading gap.
"""
import re
import sys

FILES = [
    "public/catalogs/DS-CATALOG.html",
    "public/catalogs/DS-CATALOG-portable.html",
    "public/catalogs/KONTAKT-CATALOG.html",
    "public/catalogs/KONTAKT-CATALOG-portable.html",
]

TAG = "SIDES-INDEX-EMBED-TOP-FLUSH-v1"

ANCHOR = (
    "#catalogMain>#catalogIndex:not(.is-embedded){flex:0 0 auto;z-index:16}"
)

INSERT = (
    "\n/* " + TAG + ": embedded Index flush with Search/Keywords tops in Sides */\n"
    "body.display-sides #catalogMain>.catalog-body>#catalogIndex.is-embedded:first-child,\n"
    "body.display-middle #catalogMain>.catalog-body>#catalogIndex.is-embedded:first-child,\n"
    "body.catalog-portable #catalogMain>.catalog-body>#catalogIndex.is-embedded:first-child{\n"
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
