# Catalog UI backlog

Applies to all four catalogs in `public/catalogs/` (DS / Kontakt, desktop + portable).

## Card views and pinned-card dock (do in this order)

1. ~~**Pinned cards missing from the bottom dock**~~ — done (`21fa68f`).
2. ~~**No duplicate pins of the same card**~~ — done (`f88b6ab`).
3. ~~**Name click opens the expanded card**~~ — done (`4902555`).
3b. ~~**Playing pill layout** — while an embedded YouTube video plays in a pinned
   card, the pill loses its cover image and shows a large buffering spinner in
   the media disc that knocks the name/image out of alignment (see pill
   "Clave Frog & Fri..." with the spinner). The disc must stay 2.15rem, keep
   the cover visible or a clean thumbnail, and never reflow the pill.~~ done
   (`bd2012e`) — media is now an overlay inside a fixed `.card-min-cover` box
   instead of a pill-level flex sibling, so playback can no longer add/remove
   a flex item from the pill. Needs a manual live check with a real YouTube
   video to confirm the spinner is fully clipped in-browser.
3c. ~~**Pinned card not displaying when hidden by filter** — restore from the dock
   sometimes shows nothing when the content window does not contain the card.
   Not reproduced headless yet; needs exact steps.~~ done (`869fdc9`) —
   `cardMinRestore` now directly clears `.is-hidden`/inline `display:none` on
   the card and `.is-hidden`/`hidden` on its `.loc-group` before reopening,
   instead of depending on the `:has()` CSS override to reassert visibility.
   Needs a manual check restoring a pin while the active filter excludes it.

## Embedded content (YouTube) inside the expanded card

4. ~~**Comments pane** must show the real YouTube comments for the video, with the
   comment content scrollable.~~ done (`loadCardYtComments`/`fillYtCommentsStrip`).
5. ~~**Pane placement** — before the video starts playing the comments pane sits in
   a vertical window on the right of the video; once the video plays it moves to
   the bottom. Applies in both orientations.~~ done, `fix-YT-PANE-v1` (yt-wide/yt-split).
6. ~~**Collapsible pane** — a small yellow bar on the seam between the video window
   and the comments window marks the designated area and toggles the pane
   (hide/show) in both orientations.~~ done, `fix-YT-PANE-v1` (`.card-yt-list-toggle`).
7. ~~**Video expand** — offer the video an expand option when the pane is hidden,
   where possible.~~ done, `fix-YT-PANE-v1` (collapsed pane -> stage frame expands).
8. ~~Items 4–7 must also apply when the embedded view is fullscreened.~~ done, same
   CSS/JS applies regardless of fullscreen state — needs a manual fullscreen re-check.

## Open / logged for later

- ~~Shadow scrollbar occasionally lagging under the content window scrollbar
  (Sides/Middle layouts); tied to the custom `hover-scroll-stripe` indicator.~~
  done (`862c312`) — the thumb was positioned via `style.top`, which forces
  layout+paint every scroll frame; switched to a `--thumb-y` custom property
  consumed by `transform:translateY()` so moving it is compositor-only, like
  the browser's own scrollbar. Needs a manual check on a long content column
  with a fast wheel/trackpad scroll to confirm the lag is gone.
- Residual ~1px note-button misalignment (sub-pixel rounding) — reviewed: the
  `.note-balloon` offset chain (`--card-chrome-inset` + 2×`--card-chrome-btn`
  + 2×`--card-chrome-gap`) resolves to an exact `7rem`/112px with no
  fractional rem, so this isn't our calc() math; it's browser subpixel
  rendering at non-100% zoom/DPR, which isn't fixable from CSS. Left as-is.
