#!/usr/bin/env python3
"""fix-NOTE-FAV-ALIGN-v1

Desktop cards get a chrome override that nudges .fav-btn from the base
.5rem inset to .8rem (right/bottom), for non-portable, non-preview cards.
.note-view-btn's position is calculated relative to that same .5rem base
(`right:calc(.5rem + var(--card-chrome-btn) + .5rem)`), but no matching
override exists for it -- only .fav-btn got the .8rem nudge. The two
buttons that are supposed to sit side by side on a card end up offset from
each other by .3rem (about 4-5px), which is what the screenshot showed:
the note-balloon button visibly higher/further right than the heart next
to it, not a subpixel rounding artifact as first assumed.

Fix: add the same-shaped override for .note-view-btn, computed from the
same .8rem base as the nudged .fav-btn, so the two stay flush again. Only
applies to the desktop (non-portable) files; the portable files never had
the .8rem nudge rule in the first place (their fav-btn stays at the base
.5rem, where .note-view-btn already lines up correctly).
"""

FILES = [
    "public/catalogs/DS-CATALOG.html",
    "public/catalogs/KONTAKT-CATALOG.html",
]

OLD = (
    "body:not(.catalog-portable):not(.chosen-preview-open) .entry:not(.highlight) .fav-btn{\n"
    "  right:.8rem!important;bottom:.8rem!important;top:auto!important;left:auto!important;\n"
    "  width:var(--card-chrome-btn)!important;height:var(--card-chrome-btn)!important;\n"
    "  min-width:var(--card-chrome-btn)!important;min-height:var(--card-chrome-btn)!important;\n"
    "  border-radius:8px!important\n"
    "}"
)
NEW = (
    OLD +
    "\n/* fix-NOTE-FAV-ALIGN-v1: note-view-btn sits left of fav-btn and must nudge by the same .8rem base, "
    "not the .5rem it inherits from its default rule, or the two buttons go out of alignment */\n"
    "body:not(.catalog-portable):not(.chosen-preview-open) .entry:not(.highlight) .note-view-btn{\n"
    "  right:calc(.8rem + var(--card-chrome-btn) + .5rem)!important;bottom:.8rem!important;top:auto!important;left:auto!important;\n"
    "  width:var(--card-chrome-btn)!important;height:var(--card-chrome-btn)!important;\n"
    "  min-width:var(--card-chrome-btn)!important;min-height:var(--card-chrome-btn)!important;\n"
    "  border-radius:8px!important\n"
    "}"
)


def main():
    for path in FILES:
        txt = open(path, encoding="utf-8").read()
        n = txt.count(OLD)
        if n != 1:
            raise SystemExit(f"{path}: expected 1 match, got {n}")
        txt = txt.replace(OLD, NEW, 1)
        open(path, "w", encoding="utf-8").write(txt)
        print(path, "ok")


if __name__ == "__main__":
    main()
