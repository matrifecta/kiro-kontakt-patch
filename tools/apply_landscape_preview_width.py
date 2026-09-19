#!/usr/bin/env python3
"""
LANDSCAPE-PREVIEW-WIDTH-v1

The mobile "expanded card" preview dialog (body.catalog-portable.chosen-preview-open
.entry.selected:not(.highlight)) has a fixed width:min(92vw,36rem) cap that applies
in EVERY orientation. On a narrow portrait screen this is nearly invisible (92vw is
already below 36rem), but on a wide landscape screen it clamps the card to a fixed
~576px box centered on screen with large empty margins on both sides, letterboxing
any embedded video/image inside it. This is unrelated to card pinning - it happens
on every landscape open of the preview dialog, pinned or not (confirmed headlessly:
identical rect whether freshly opened or restored from the pin dock).

Widens the cap in landscape only (body.catalog-portable.portable-landscape) to
min(92vw,70rem) - the same max-width already used by the desktop (non-portable)
preview dialog - so landscape can use most of the available screen width. The
vertical sizing/centering (max-height, top/bottom margin) is untouched, since that
rule already applies identically in both orientations already.
"""
import sys

FILES = [
    "public/catalogs/DS-CATALOG-portable.html",
    "public/catalogs/KONTAKT-CATALOG-portable.html",
]

OLD = """/* fix-PORTABLE-PREVIEW-CENTER: extended card is a centered dialog; chrome on the card top edge */
@media all{
  body.catalog-portable.chosen-preview-open .entry.selected:not(.highlight){
    position:fixed!important;
    left:50%!important;top:50%!important;right:auto!important;bottom:auto!important;
    transform:translate(-50%,-50%)!important;-webkit-transform:translate(-50%,-50%)!important;
    margin:0!important;
    width:min(92vw,36rem)!important;max-width:min(92vw,36rem)!important;
    max-height:min(86dvh,calc(100dvh - 2.5rem))!important;
    padding-top:3.5rem!important
  }"""

NEW = """/* fix-PORTABLE-PREVIEW-CENTER: extended card is a centered dialog; chrome on the card top edge */
@media all{
  body.catalog-portable.chosen-preview-open .entry.selected:not(.highlight){
    position:fixed!important;
    left:50%!important;top:50%!important;right:auto!important;bottom:auto!important;
    transform:translate(-50%,-50%)!important;-webkit-transform:translate(-50%,-50%)!important;
    margin:0!important;
    width:min(92vw,36rem)!important;max-width:min(92vw,36rem)!important;
    max-height:min(86dvh,calc(100dvh - 2.5rem))!important;
    padding-top:3.5rem!important
  }
  /* LANDSCAPE-PREVIEW-WIDTH-v1: the 36rem cap above was clamping the dialog to a
     narrow centered box with large empty side margins on wide landscape screens.
     Widen it to use most of the available width there, matching the desktop
     dialog's own 70rem cap. Vertical sizing/margins are unchanged. */
  body.catalog-portable.portable-landscape.chosen-preview-open .entry.selected:not(.highlight){
    width:min(92vw,70rem)!important;max-width:min(92vw,70rem)!important
  }"""

def patch(path):
    src = open(path, encoding="utf-8").read()
    if "LANDSCAPE-PREVIEW-WIDTH-v1" in src:
        print(f"{path}: already patched, skipping")
        return
    if src.count(OLD) != 1:
        sys.exit(f"{path}: anchor not found/unique ({src.count(OLD)})")
    src = src.replace(OLD, NEW, 1)
    open(path, "w", encoding="utf-8").write(src)
    print(f"{path}: patched")

for f in FILES:
    patch(f)
