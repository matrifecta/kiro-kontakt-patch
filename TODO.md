# Catalog UI backlog

Applies to all four catalogs in `public/catalogs/` (DS / Kontakt, desktop + portable).

## Card views and pinned-card dock (do in this order)

1. ~~**Pinned cards missing from the bottom dock**~~ — done (`21fa68f`).
2. ~~**No duplicate pins of the same card**~~ — done (`f88b6ab`).
3. ~~**Name click opens the expanded card**~~ — done (`4902555`).
3b. **Playing pill layout** — while an embedded YouTube video plays in a pinned
   card, the pill loses its cover image and shows a large buffering spinner in
   the media disc that knocks the name/image out of alignment (see pill
   "Clave Frog & Fri..." with the spinner). The disc must stay 2.15rem, keep
   the cover visible or a clean thumbnail, and never reflow the pill.
3c. **Pinned card not displaying when hidden by filter** — restore from the dock
   sometimes shows nothing when the content window does not contain the card.
   Not reproduced headless yet; needs exact steps.

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
