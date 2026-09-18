#!/usr/bin/env python3
"""Update the Legend and User/Update guide panels to document this
session's changes: user notes, the note-view toggle button, note
keyword pills, name-click-to-expand, and the Erase History "User
text" bucket with its two-stage confirm."""

FILES = [
    "public/catalogs/DS-CATALOG.html",
    "public/catalogs/DS-CATALOG-portable.html",
    "public/catalogs/KONTAKT-CATALOG.html",
    "public/catalogs/KONTAKT-CATALOG-portable.html",
]

# 1. Legend: note button bullet, right after Favorite.
OLD_FAV = '<li><b>♡ / ♥</b> — Favorite on the card, gallery, and image focus. Filled when the library is saved locally.</li>'
NEW_FAV = (
    OLD_FAV
    + '<li><b>\U0001F4AC</b> — appears next to Favorite only on cards with a saved note. '
    'Tap it to switch the description between the library\u2019s own text and your note '
    '(never both, so card height does not change). Styled like the other card buttons.</li>'
)

# 2. Legend: name label now opens the expanded card.
OLD_NAME = '<li><b>Two-line name</b> — library title uses a fixed two-line slot with ellipsis (<code>.lib-name</code>). Hover (desktop) can show the full name in a themed bubble. Portable portrait splits the document title around the notch, each word centered in its half.</li>'
NEW_NAME = (
    '<li><b>Two-line name</b> — library title uses a fixed two-line slot with ellipsis (<code>.lib-name</code>). '
    'Hover (desktop) can show the full name in a themed bubble. Tap/click the name from anywhere '
    '(grid, Sides preview) to open the expanded card view, same as \u26F6. Portable portrait splits the '
    'document title around the notch, each word centered in its half.</li>'
)

# 3. History details block: mention the notes bucket + two-stage confirm.
OLD_HIST_STEPS = """        <ol>
          <li>Open Search so the AC shell is visible. Press <b>H</b> (or Search ⋯ → History on compact chrome).</li>
          <li>Pick rows, or <b>All search</b> (typed history only) vs <b>All</b> (includes saved sessions and saved combinations).</li>
          <li>Confirm erase (✓) or keep (✕).</li>
        </ol>
        <p class="catalog-help-k">You should see</p>
        <p>History cloud over the Search dropdown. Session AC is not a saved Layout or Profile until you store it. Erasing search history does not reset theme or Flip unless you chose All including saved sessions/combinations.</p>"""

NEW_HIST_STEPS = """        <ol>
          <li>Open Search so the AC shell is visible. Press <b>H</b> (or Search ⋯ → History on compact chrome).</li>
          <li>Pick rows, or <b>All search</b> (typed history only) vs <b>All</b> (includes saved sessions and saved combinations). Neither button ticks <b>User text (notes)</b> — that row must be checked by hand.</li>
          <li>Press <b>✓</b> once to arm it (✓ and ✕ turn red as a warning); press <b>✓</b> again to actually erase, or press <b>✕</b> to back out without erasing. Changing any checkbox while armed disarms it again.</li>
        </ol>
        <p class="catalog-help-k">You should see</p>
        <p>History cloud over the Search dropdown. The top label reads "Erase history + User text" while that box is checked. Session AC is not a saved Layout or Profile until you store it. Erasing search history does not reset theme or Flip unless you chose All including saved sessions/combinations. Erasing User text clears every saved note (and the keyword pills it generated) on this device — it cannot be undone.</p>"""

# 4. New "Notes" task block in the User guide, right after "Find a library by Search".
ANCHOR_USER = """      <details open>
        <summary>Find a library by Search</summary>"""

NOTES_BLOCK = """      <details>
        <summary>Notes on a library</summary>
        <p class="catalog-help-k">Goal</p>
        <p>Keep a personal note on a library, view it in place of the description, and have it feed search.</p>
        <p class="catalog-help-k">Steps</p>
        <ol>
          <li>Open a card (⛶ or tap its name) and tap the \U0001F4AC balloon next to the title to write a note, then Save.</li>
          <li>Back in the grid, that card shows a \U0001F4AC button next to Favorite. Tap it to swap the description between your note and the library's own text.</li>
          <li>Words from your note (3+ letters, common words filtered out) become searchable keyword pills automatically, and count toward existing pills where they match.</li>
        </ol>
        <p class="catalog-help-k">You should see</p>
        <p>The \U0001F4AC button only appears when a note is saved. Notes (and the keywords they generate) live in this browser's <code>localStorage</code> and are not part of the HTML file. Erase them from History → <b>User text (notes)</b>.</p>
      </details>
""" + ANCHOR_USER


def main():
    for path in FILES:
        txt = open(path, encoding="utf-8").read()

        n_fav = txt.count(OLD_FAV)
        txt = txt.replace(OLD_FAV, NEW_FAV, 1)

        n_name = txt.count(OLD_NAME)
        txt = txt.replace(OLD_NAME, NEW_NAME, 1)

        n_hist = txt.count(OLD_HIST_STEPS)
        txt = txt.replace(OLD_HIST_STEPS, NEW_HIST_STEPS, 1)

        n_notes = txt.count(ANCHOR_USER)
        txt = txt.replace(ANCHOR_USER, NOTES_BLOCK, 1)

        open(path, "w", encoding="utf-8").write(txt)
        print(f"{path}: fav={n_fav} name={n_name} hist={n_hist} notes_block={n_notes}")


if __name__ == "__main__":
    main()
