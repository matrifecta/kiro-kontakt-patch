# Catalog UI backlog

Applies to all four catalogs in `public/catalogs/` (DS / Kontakt, desktop + portable).

## Card views and pinned-card dock (do in this order)

1. **Pinned cards missing from the bottom dock** — minimized/pinned cards do not
   appear on the bottom bar (`#cardMinDock`) until it is clicked. Find why the
   dock is not rendered/shown on pin and fix.
2. **No duplicate pins of the same card** — one card must not be pinned twice
   (expanded card / embedded mode as one pin, fullscreen card view as another).
   A card gets a single pin regardless of which view it was minimized from.
3. **Name click opens the expanded card** — clicking the card label name must
   return to entering the expanded card view (preview, without embedded content),
   as it used to; it currently opens the fullscreen overlay.

## Embedded content (YouTube) inside the expanded card

4. **Comments pane** must show the real YouTube comments for the video, with the
   comment content scrollable.
5. **Pane placement** — before the video starts playing the comments pane sits in
   a vertical window on the right of the video; once the video plays it moves to
   the bottom. Applies in both orientations.
6. **Collapsible pane** — a small yellow bar on the seam between the video window
   and the comments window marks the designated area and toggles the pane
   (hide/show) in both orientations.
7. **Video expand** — offer the video an expand option when the pane is hidden,
   where possible.
8. Items 4–7 must also apply when the embedded view is fullscreened.

## Open / logged for later

- Shadow scrollbar occasionally lagging under the content window scrollbar
  (Sides/Middle layouts); tied to the custom `hover-scroll-stripe` indicator.
- Residual ~1px note-button misalignment (sub-pixel rounding).
