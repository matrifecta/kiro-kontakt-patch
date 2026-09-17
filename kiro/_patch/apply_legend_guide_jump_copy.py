#!/usr/bin/env python3
"""Tighten jump gutter leftover and splice current Legend/Guide copy into all four catalogs."""
from __future__ import annotations

import os
import tempfile
from pathlib import Path

ROOT = Path("/home/phnx/kiro-kontakt-patch/public/catalogs")
FILES = [
    ROOT / "KONTAKT-CATALOG.html",
    ROOT / "KONTAKT-CATALOG-portable.html",
    ROOT / "DS-CATALOG.html",
    ROOT / "DS-CATALOG-portable.html",
]

START = '<div class="catalog-help-panel" id="catalogHelpLegend" data-panel="legend">'
OLD_PANEL_END = """      <details>
        <summary>About stamp</summary>
        <p class="catalog-help-muted">The About / Document body (generation time, rebuild one-liner) is the live stamp for this file. Same text is reused under Legend → About / Document. No standalone changelog in this repository; this Update guide is the in-catalog record.</p>
      </details>
    </div>"""

DESK_RIGHT_OLD = "  var right=Math.max(6,Math.round((window.innerWidth||0)-r.right)+10+gutter);\n"
DESK_RIGHT_NEW = "  var right=Math.max(6,Math.round((window.innerWidth||0)-r.right)+gutter);\n"
PORT_INSET_OLD = "    var insetR=Math.max(8,Math.round(padR))+gutter;\n"
PORT_INSET_NEW = "    var insetR=gutter;\n"

NEW_PANELS = r'''<div class="catalog-help-panel" id="catalogHelpLegend" data-panel="legend">
      <!-- catalog-help-full-copy -->
      <p class="catalog-help-muted catalog-help-scene-lead" id="catalogHelpLegendLead">Legend for the <span class="catalog-help-product">catalog</span> chrome. Cards stay in the content window; this key sits on its left border.</p>
      <p>Collapsible sections below use the same words as the chrome: Search, Keywords, Index, Window, Embed, Sides, Middle, Flip, Collapse, Customize, Layouts, Profiles, PATH, Clear, S, K, About / Document.</p>
      <details open>
        <summary>Symbols</summary>
        <ul>
          <li><b>PATH</b> — small caps label above the three path icons on a card (FS, copy, folder). There is no expandable path field on the card; the full location opens in the path reader via FS.</li>
          <li><b>Folder</b> — themed path icon that opens the library folder in the file manager on desktop (Dolphin). Omitted or inert on portable.</li>
          <li><b>Copy</b> — path icon that copies the library location. A short toast confirms.</li>
          <li><b>FS</b> — path icon that opens the <b>path reader</b> (long location). This is not the card’s own ⛶. Back closes the reader.</li>
          <li><b>♡ / ♥</b> — Favorite on the card, gallery, and image focus. Filled when the library is saved locally.</li>
          <li><b>Index Window</b> — Index docks as a scrollable window on the content pane and fills down to About / Document until you Collapse the index. Cards stay underneath; it does not overlay an expanded or front card. Skip-to-top / skip-to-bottom hide while Window is open.</li>
          <li><b>Index Embed</b> — the same list is placed with the catalog cards and scrolls away with them. The Index button reads <b>Window</b> when Embed is on (tap to return to Window) and <b>Embed</b> when Window is on.</li>
          <li><b>Index arrow</b> — opens Index. It stays closed until you use that arrow. Collapse on an open Window returns the pane to cards.</li>
          <li><b>Skip to top / bottom</b> — compact filled skip icons (bar + shaft + solid triangle; no “top” / “bottom” text). They sit just left of the content scrollbar with a small leftover so the track stays selectable. Work in Sides, Middle, and content-only. Stay put while cards scroll.</li>
          <li><b>Flip</b> — swaps Search and Keywords (Sides: skip-center around the catalog; Middle: mirror the pair). Portrait Sides swaps the menu column with content.</li>
          <li><b>⛶</b> — Open fullscreen. On an expanded card (desktop): card overlay. On Search / Keywords strips: that menu — ⛶ stays on the right; Keywords fullscreen has no back arrow. On Legend / Guide (desktop): the help card fills the viewport. Hidden on portable card chrome (phone goes straight to fullscreen popups). Distinct from path <b>FS</b>.</li>
          <li><b>⋯</b> — overflow. Header / Search More parks extra tools (Clear on miss, scale, theme, Customize, Layouts, Profiles). On portable Keywords, ⋯ shows or hides <b>category pills</b> at the top of the pills window as transparent UI buttons — not a nested popup.</li>
          <li><b>Clear</b> (sweep icon) — clears Search + Keywords filters together. <b>Clear on miss</b> — if you leave gallery on a library that is not a current hit, Search clears.</li>
          <li><b>H</b> — History (session AC, saved sessions, saved combinations).</li>
          <li><b>S</b> / <b>K</b> — show or hide Search and Keywords. Hiding both on portable is content-only (catalog pane alone).</li>
          <li><b>← Back</b> — one step back from expanded card, card fullscreen, gallery, description/path reader, Search fullscreen, embed, or this Legend/Guide. Keywords fullscreen uses ⛶ + Hide instead of a back arrow.</li>
          <li><b>Legend / Guide</b> — left-edge keys on the content border, docked like the skip icons. Selected sticks out further. They hide when the content window is not on screen and must not overlay About / Document. They also hide under card overlays unless help itself is open.</li>
        </ul>
      </details>
      <details open>
        <summary>Fields</summary>
        <ul>
          <li><b>Search</b> — field placeholder “Search libraries…”. Name / other / patch tokens. Does not auto-open a front card. Hits highlight in the content window.</li>
          <li><b>Suggestion list</b> (session AC) — lives in the Search column under the field. Groups can include libraries, keyword hits, Patch names, session pins, and saved combinations. Session only until you save. Resize edges show in Customize.</li>
          <li><b>Keyword pills</b> — Instrument / Brand / Model / Vibe / Patch groups. Combine to narrow. Active filters also appear as Search pills. Portable ⋯ reveals the category buttons at the top of this window.</li>
          <li><b>Two-line name</b> — library title uses a fixed two-line slot with ellipsis (<code>.lib-name</code>). Hover (desktop) can show the full name in a themed bubble. Portable portrait splits the document title around the notch, each word centered in its half.</li>
          <li><b>Path</b> — three icons under the cover (FS | copy | folder), not an expandable path field. FS opens the reader for the full location.</li>
          <li><b>Description</b> — blurb on the card; tap / wheel to open the description reader instead of stretching the grid.</li>
          <li><b>Patch search / Patches</b> — Patch category in Keywords, plus nested patch tree on the card (DS: grouped by subfolder). Kontakt stays library-level; Patch pills still match preset-name tokens when present. Collapse evens card heights.</li>
          <li><b>Card Search</b> — in-card Google / YouTube / image search when a card is expanded (embed vs popup depends on portable).</li>
        </ul>
      </details>
      <details open>
        <summary>Content window</summary>
        <ul>
          <li><b>Cards</b> — one library each, in the middle pane. <b>Grid</b> is the catalog. <b>Expanded card</b> is the desktop preview (centered, dimmed catalog behind). Portable/phone opens a fullscreen popup instead.</li>
          <li><b>Covers</b> — banner art. Tap for gallery / image focus. Desktop hover can enlarge the cover without leaving the grid.</li>
          <li><b>Index (alphabetical)</b> — name list. Closed until the Index arrow. Window fills down to About until Collapse and does not overlay an expanded/front card. Embed scrolls with cards. Click a name to jump.</li>
          <li><b>About / Document</b> — generation stamp and rebuild note at the foot. Window docks it under Index; Embed scrolls it with the cards. Legend / Guide keys sit above it, not on top of it.</li>
          <li><b>Pinned pyramid</b> — minimized cards dock at the bottom of the content window (Save on Middle).</li>
          <li><b>Skip icons</b> — bottom-right of this pane, just left of the scrollbar gutter.</li>
        </ul>
      </details>
      <details open>
        <summary>Menu windows</summary>
        <ul>
          <li><b>Search</b> — left (Sides landscape) or top (Middle / portrait). Field, suggestion list, pills, ⛶, Hide Search, Clear, History, scale.</li>
          <li><b>Keywords</b> — right (Sides landscape) or paired with Search on Middle. Pills, Hide Keywords, ⛶ on the right, Collapse, Customize, Layouts. Hide + the Keywords header still control size/show. Portable ⋯ toggles category pills as transparent buttons at the top of the pills window (not a popup). Fullscreen keeps ⛶; no back arrow.</li>
          <li><b>Sides</b> — Search | content | Keywords as three panes. Content is the only scrolling card window.</li>
          <li><b>Middle</b> — Search + Keywords on top, catalog below. On phone (portable always uses phone chrome), Middle is portrait-only; landscape uses Sides.</li>
          <li><b>Content-only</b> — Search and Keywords hidden (S and K off). The catalog pane fills; skip icons still work. Portable can live here even on a wide screen.</li>
          <li><b>Portrait vs landscape</b> — desktop ≥900px still uses Sides/Middle. Portrait stacks menus (Sides) or keeps Search | Keywords above cards (Middle). Portable portrait titles split around the notch.</li>
          <li><b>Portable = phone</b> — <code>*-portable.html</code> always uses phone chrome (<code>CATALOG_PORTABLE</code>), even on a wide screen: menus as sheets / fullscreen, preview as popup.</li>
          <li>Separators (Search split, dual-FS, Index height) drag only while <b>Customize</b> is on.</li>
        </ul>
      </details>
      <details>
        <summary>Mode buttons</summary>
        <ul>
          <li><b>S</b> / <b>K</b> — Search / Keywords visibility (header). Both off = content-only.</li>
          <li><b>Sides</b> / <b>Middle</b> — layout pick (persisted per catalog ns + orientation). Phone Middle is portrait-only.</li>
          <li><b>Flip</b> — swap the menu columns / stacked order.</li>
          <li><b>Collapse</b> — close open patch trees, even card row heights, and (with Index Window open) collapse the index so cards return.</li>
          <li><b>Customize</b> — reveal drag edges for Search, Keywords, Index, and menu height. Becomes <b>Done</b> while arranging.</li>
          <li><b>Layouts</b> — named menu size presets (Search + Keywords vs Search-only stores). Saved layouts, not the live session.</li>
          <li><b>Profiles</b> — saved workspace snapshots (pills, Flip, related chrome). Max <b>12</b> per catalog. Desktop header; phone parks it in ⋯. Portable hides the standing header control.</li>
          <li><b>Theme picker</b> — Desert Dusk, Night Studio, Smoked Glass, seasonal light/dark sets, HC Dark / HC Light. Saved as <code>catalog-theme</code>.</li>
          <li><b>Pick / Search</b> — data mode for Keywords vs typed Search.</li>
          <li><b>Default</b> — reset live splitter sizes without deleting named Layouts.</li>
        </ul>
      </details>
      <details>
        <summary>About / Document</summary>
        <p>About / Document is the collapsible note at the foot of the content window. Window keeps it docked under Index; Embed scrolls it with the cards. Legend / Guide edge keys and skip icons sit above this bar, not over it.</p>
        <p id="catalogHelpAboutReuse" class="catalog-help-muted">The catalog About / Document note lives at the foot of the content window (Window or Embed).</p>
      </details>
    </div>
    <div class="catalog-help-panel" id="catalogHelpUser" data-panel="user" role="tabpanel" aria-labelledby="catalogHelpTabUser" hidden>
      <p class="catalog-help-muted catalog-help-scene-lead">User guide for the <span class="catalog-help-product">catalog</span>. Each block is a task: goal, steps, what you should see.</p>
      <details open>
        <summary>Find a library by Search</summary>
        <p class="catalog-help-k">Goal</p>
        <p>Jump to one library by name (or patch token) without opening a random front card.</p>
        <p class="catalog-help-k">Steps</p>
        <ol>
          <li>Turn <b>S</b> on if Search is hidden.</li>
          <li>Click <b>Search libraries…</b> and type. Session AC lists matches under the field.</li>
          <li>Pick a suggestion or press through hits in the content window. Click the card you want. <b>Clear</b> wipes query + pills together.</li>
        </ol>
        <p class="catalog-help-k">You should see</p>
        <p>The AC list stays in the Search column. Cards in the content window filter/highlight. Nothing auto-opens as an expanded card.</p>
      </details>
      <details open>
        <summary>Filter by Keywords</summary>
        <p class="catalog-help-k">Goal</p>
        <p>Narrow the grid with Instrument / Brand / Model / Vibe / Patch pills.</p>
        <p class="catalog-help-k">Steps</p>
        <ol>
          <li>Turn <b>K</b> on. Open Keywords if the pane is hidden.</li>
          <li>On portable, tap <b>⋯</b> to show category buttons at the top of the pills window (transparent UI, not a popup). Tap ⋯ again to hide them.</li>
          <li>Choose a category, then tap pills. Combine freely. Switch Pick vs Search mode if you are hunting inside the pill set.</li>
          <li>Sweep <b>Clear</b> when you want the full set again. <b>Hide Keywords</b> (and the Keywords header) still size/show the pane; chosen pills stay until Clear.</li>
        </ol>
        <p class="catalog-help-k">You should see</p>
        <p>Pills accent when active. The content window only shows matching cards. Search pills row mirrors active filters. On Decent Sampler, expand a library to see patches grouped by subfolder.</p>
      </details>
      <details open>
        <summary>Open a card / expanded card</summary>
        <p class="catalog-help-k">Goal</p>
        <p>Read one library without losing the catalog behind it.</p>
        <p class="catalog-help-k">Steps</p>
        <ol>
          <li>Click the card (name / body) in the grid.</li>
          <li>Desktop: you get an <b>expanded card</b> (preview). Portable/phone: a fullscreen popup.</li>
          <li>Use cover for gallery, description for the reader, PATH icons for folder / copy / FS, card Search for YouTube / web / images.</li>
          <li>Desktop ⛶ on the card enters fullscreen. <b>← Back</b> from fullscreen returns to the expanded card; Back again returns to the grid.</li>
        </ol>
        <p class="catalog-help-k">You should see</p>
        <p>Desktop: catalog dimmed, card centered, Back left, ⛶ right, two-line name in its slot. Phone: full window, Back left, no extra ⛶ on that surface. Index Window does not sit on top of this card. Collapse evens card sizes after you open patch trees.</p>
      </details>
      <details>
        <summary>Path icons</summary>
        <p class="catalog-help-k">Goal</p>
        <p>Copy or open a library location, or read a long path, without mixing that up with card fullscreen.</p>
        <p class="catalog-help-k">Steps</p>
        <ol>
          <li>On the card, find the <b>PATH</b> row: three icons — FS | copy | folder. There is no expandable path field.</li>
          <li><b>Folder</b> opens Dolphin (desktop HTML only). <b>Copy</b> toasts the clipboard. <b>FS</b> opens the path reader for the full location — Back closes it.</li>
          <li>Card ⛶ (expanded-card chrome) is a different control: overlay fullscreen of the library, not the path reader.</li>
        </ol>
        <p class="catalog-help-k">You should see</p>
        <p>Icons follow the theme (not a black raster). Index Window does not show PATH icons on its own rows. Portable has no desktop folder-open.</p>
      </details>
      <details>
        <summary>Index Window vs Embed</summary>
        <p class="catalog-help-k">Goal</p>
        <p>Use the alphabetical list without covering Search, then choose dock vs in-flow.</p>
        <p class="catalog-help-k">Steps</p>
        <ol>
          <li>Click the <b>Index arrow</b> — the list stays closed until you do.</li>
          <li>Leave Embed off for <b>Window</b>. The list fills the content pane down to About / Document until you Collapse.</li>
          <li>Press <b>Embed</b> to park the list with the cards and scroll it in-flow. The button then reads <b>Window</b>.</li>
          <li>Click a name to jump to that card. Opening an expanded/front card hides Window so it does not overlay that card.</li>
        </ol>
        <p class="catalog-help-k">You should see</p>
        <p>Window fills down to the About bar. Embed sits in the card column. Search/Keywords chrome stays put. Skip icons hide while Index Window is open. The preference is remembered.</p>
      </details>
      <details>
        <summary>Sides vs Middle vs content-only</summary>
        <p class="catalog-help-k">Goal</p>
        <p>Choose whether menus hug the catalog, sit above it, or hide so only cards remain.</p>
        <p class="catalog-help-k">Steps</p>
        <ol>
          <li>Header: <b>Sides</b> — Search | content | Keywords.</li>
          <li><b>Middle</b> — Search and Keywords on top, catalog below. On phone, Middle is portrait-only (landscape stays Sides).</li>
          <li>Use <b>S</b> / <b>K</b> to hide a menu. Both off is <b>content-only</b> — catalog pane alone, skip icons still work.</li>
        </ol>
        <p class="catalog-help-k">You should see</p>
        <p>The active layout button accents. Content pane border is where Legend/Guide and skip icons live. Pick is stored for this catalog + orientation. Portable always uses phone chrome, even on a wide monitor.</p>
      </details>
      <details>
        <summary>Flip</summary>
        <p class="catalog-help-k">Goal</p>
        <p>Swap which side Search vs Keywords occupy, without changing filters.</p>
        <p class="catalog-help-k">Steps</p>
        <ol>
          <li>Press <b>Flip</b> (header / layout cluster).</li>
          <li>Landscape Sides: menus skip the center catalog. Landscape Middle: the top pair mirrors.</li>
          <li>Portrait Sides: Flip swaps the stacked Search+Keywords column with the content window. Portrait Middle: Flip only swaps the two menu columns; cards stay below.</li>
        </ol>
        <p class="catalog-help-k">You should see</p>
        <p>Search and Keywords trade places. The content window does not dump its cards. Flip can be stored in a Profile and in <code>localStorage</code> per layout scope.</p>
      </details>
      <details>
        <summary>Portrait / landscape</summary>
        <p class="catalog-help-k">Goal</p>
        <p>Keep Sides/Middle usable when the window is tall vs wide.</p>
        <p class="catalog-help-k">Steps</p>
        <ol>
          <li>Desktop is min-width 900px. Rotate or resize across that.</li>
          <li>Landscape: three columns (Sides) or menus-above (Middle).</li>
          <li>Portrait: menus stack; extra header tools go behind ⋯ if they overflow. Portable splits the title around the notch — each word centered in its half.</li>
        </ol>
        <p class="catalog-help-k">You should see</p>
        <p>Cards remain in the content window. Legend/Guide stay on that pane’s left edge, not on Search. Display mode is independent of theme.</p>
      </details>
      <details>
        <summary>Portable</summary>
        <p class="catalog-help-k">Goal</p>
        <p>Use the phone file as a phone, even on a large screen.</p>
        <p class="catalog-help-k">Steps</p>
        <ol>
          <li>Open <code class="catalog-help-file">*-portable.html</code> — always phone, even on a wide screen.</li>
          <li>Treat preview, documents, Search, and Keywords as fullscreen sheets. Back exits that sheet. Keywords fullscreen keeps ⛶ on the right and has no back arrow; Hide still works.</li>
          <li>Do not expect desktop Profiles in the header; use ⋯ where the phone menu lists Customize / Layouts / Profiles (max 12).</li>
        </ol>
        <p class="catalog-help-k">You should see</p>
        <p>No extra ⛶ on the Legend/Guide surface. Path folder-open is desktop-only. Banners in portable are embedded in the file. Skip icons and Legend / Guide hide when the content window is off-screen or another overlay is up, then return.</p>
      </details>
      <details>
        <summary>Customize separators</summary>
        <p class="catalog-help-k">Goal</p>
        <p>Resize Search, Keywords, and Index by dragging edges, then keep or reset those sizes.</p>
        <p class="catalog-help-k">Steps</p>
        <ol>
          <li>Press <b>Customize</b> (Keywords tools). Edges become live. The button reads <b>Done</b> while arranging.</li>
          <li>Drag the Search split, dual-FS separator, AC height/width, Keywords height, Index height. Pin locks a separator. Snap 50/50 when both menus are fullscreen together.</li>
          <li><b>Default</b> resets sizes. <b>Layouts</b> saves/applies a named preset (separate from the live session).</li>
        </ol>
        <p class="catalog-help-k">You should see</p>
        <p>Customize stays accented while edit is on. Without it, separators ignore pointer so you cannot nudge layout by accident. Live sizes persist in <code>localStorage</code> for this catalog namespace.</p>
      </details>
      <details>
        <summary>History</summary>
        <p class="catalog-help-k">Goal</p>
        <p>Revisit or erase Search AC history without deleting named Layouts.</p>
        <p class="catalog-help-k">Steps</p>
        <ol>
          <li>Open Search so the AC shell is visible. Press <b>H</b> (or Search ⋯ → History on compact chrome).</li>
          <li>Pick rows, or <b>All search</b> (typed history only) vs <b>All</b> (includes saved sessions and saved combinations).</li>
          <li>Confirm erase (✓) or keep (✕).</li>
        </ol>
        <p class="catalog-help-k">You should see</p>
        <p>History cloud over the Search dropdown. Session AC is not a saved Layout or Profile until you store it. Erasing search history does not reset theme or Flip unless you chose All including saved sessions/combinations.</p>
      </details>
      <details>
        <summary>Profiles</summary>
        <p class="catalog-help-k">Goal</p>
        <p>Snapshot workspace (pills, Flip, related chrome) and switch later. Cap is 12 profiles per catalog.</p>
        <p class="catalog-help-k">Steps</p>
        <ol>
          <li>Header <b>Profiles</b> (or ⋯ on phone). Save the current setup. The list refuses a 13th; replace or delete one first.</li>
          <li>Switch profiles from the list. Reload the page — the active one should return.</li>
          <li>Theme can still be changed from the theme picker; it stores as <code>catalog-theme</code>.</li>
        </ol>
        <p class="catalog-help-k">You should see</p>
        <p>A standing Profiles button on desktop; phone parks it in ⋯. Portable hides this header control. Max 12 snapshots, localStorage only.</p>
      </details>
      <details>
        <summary>Fullscreen menus</summary>
        <p class="catalog-help-k">Goal</p>
        <p>Give Search or Keywords the whole menu surface, then return.</p>
        <p class="catalog-help-k">Steps</p>
        <ol>
          <li>On the Search strip, press ⛶ — Search fullscreen. Exit with ⛶ again or Hide Search.</li>
          <li>On Keywords, press ⛶ the same way. ⛶ stays on the right. There is no back arrow on Keywords fullscreen. Hide Keywords still shows/hides the pane.</li>
          <li>Companion S / K can bring the other menu back beside it.</li>
        </ol>
        <p class="catalog-help-k">You should see</p>
        <p>The other column yields space. Dual-FS may hide some skip chrome. Flip must not block one-menu fullscreen.</p>
      </details>
      <details>
        <summary>Back from embed / preview</summary>
        <p class="catalog-help-k">Goal</p>
        <p>Leave overlay without dumping the catalog session.</p>
        <p class="catalog-help-k">Steps</p>
        <ol>
          <li>From a card Search embed: Back leaves the embed; another Back leaves the preview if you are still expanded.</li>
          <li>From desktop card fullscreen: Back → expanded card → grid.</li>
          <li>From portable preview or document popup: Back exits that popup.</li>
          <li>Gallery, description reader, path reader, Legend/Guide fullscreen: same one-step Back.</li>
        </ol>
        <p class="catalog-help-k">You should see</p>
        <p>Each Back peels one layer. Filters, Sides/Middle, and scroll position of the grid remain. Session AC is still there; Index stays however you left it.</p>
      </details>
      <details open>
        <summary>Legend / Guide widgets</summary>
        <p class="catalog-help-k">Goal</p>
        <p>Read this legend or the guides without leaving Sides / Middle / content-only.</p>
        <p class="catalog-help-k">Steps</p>
        <ol>
          <li>On the left content border, tap the key widget (Legend) or the book-with-? widget (Guide). They dock like the skip icons.</li>
          <li>Guide opens on the <b>User guide</b> tab (default). Switch to <b>Update guide</b> for rebuild / refresh.</li>
          <li>Desktop: ⛶ on the help card goes fullscreen. Back steps out. The same edge keys stay available while help is open.</li>
          <li>Scroll this card — each section is a <code>details</code> block. Close help with Back, or tap the active edge key again.</li>
        </ol>
        <p class="catalog-help-k">You should see</p>
        <p>A long scrollable card (this text). Guide tabs appear only for Guide. The keys hide when the content window is not on screen, and they sit above About / Document rather than covering it. Overlay cards hide them until you close those overlays.</p>
      </details>
    </div>
    <div class="catalog-help-panel" id="catalogHelpUpdate" data-panel="update" role="tabpanel" aria-labelledby="catalogHelpTabUpdate" hidden>
      <p class="catalog-help-muted catalog-help-scene-lead">Update guide — how this <span class="catalog-help-product">catalog</span> file is rebuilt, what persists, and what to do when chrome sticks. There is no separate changelog file in the repo; chrome notes live here.</p>
      <details open>
        <summary>Rebuild / refresh</summary>
        <p id="catalogHelpRebuild">Re-run the catalog builder for this library set, then reload the page. Desktop and portable HTML are separate files.</p>
        <ul>
          <li>Scripts live under <code>kiro/specs/kontakt-workspace-drive-dirty-fix/artifacts/</code>. Mode argument: <code>desktop</code> | <code>portable</code> | <code>both</code>.</li>
          <li><b>Decent Sampler.</b> After adding libraries, run <code>build-ds-catalog-html.sh both</code>. Output is library-level: expand a library to see patches grouped by subfolder.</li>
          <li><b>Kontakt.</b> Registered libraries come from <code>komplete.db3</code> (Kontakt Portable UserData, <code>content_type=2</code>). Rebuild with <code>build-kontakt-catalog-html.sh</code> only when that database is the real studio file — this patch tree cannot see <code>/mnt/workspace</code> from every machine.</li>
          <li>Builders write artifact HTML. Copy the new files into <code>public/catalogs/</code> (<code>KONTAKT-CATALOG.html</code>, <code>DS-CATALOG.html</code>, and the matching <code>*-portable.html</code>), then reload. Serve from <code>http://127.0.0.1:8797/</code>.</li>
          <li>A rebuild refreshes cards, covers, descriptions, and Index. It does not wipe <code>localStorage</code> theme, layouts, or profiles.</li>
        </ul>
      </details>
      <details>
        <summary>After a new catalog drop</summary>
        <ol>
          <li>Replace <span class="catalog-help-file">this HTML</span> (and the sibling portable/desktop file if you use both).</li>
          <li>Hard-reload the tab so the browser does not keep a stale multi-megabyte file.</li>
          <li>Theme, Layouts, Profiles (max 12), Favorites, and UI scale stay in localStorage — they are not inside the HTML drop.</li>
          <li>If path icons or covers look wrong, confirm you copied the matching thumbs / portable embed, not only one file.</li>
        </ol>
      </details>
      <details open>
        <summary>Portable vs desktop files</summary>
        <ul>
          <li><code>KONTAKT-CATALOG.html</code> / <code>DS-CATALOG.html</code> — desktop thumbs, [open folder] where the OS allows, Sides three-pane on wide landscape, desktop Profiles in the header.</li>
          <li><code>KONTAKT-CATALOG-portable.html</code> / <code>DS-CATALOG-portable.html</code> — self-contained, banners embedded, phone chrome always (<code>window.CATALOG_PORTABLE</code> / <code>body.catalog-portable</code>). Middle is portrait-only; landscape uses Sides. Content-only hides Search and Keywords.</li>
          <li>Do not mix: a portable file on a 1400px monitor still behaves as phone (fullscreen popups, no desktop card ⛶ on Legend/Guide). Bookmark the file you actually use.</li>
        </ul>
      </details>
      <details>
        <summary>localStorage: theme, layouts, scale</summary>
        <ul>
          <li><b>Theme</b> — <code>catalog-theme</code> (default Desert Dusk).</li>
          <li><b>UI scale</b> — <code>catalog-ui-scale-kontakt</code> / <code>catalog-ui-scale-ds</code>, plus Search-only scale keys.</li>
          <li><b>Layouts</b> — named Search / Keywords sizes from the Layouts menu. Customize drag edges write live ratios separately from those names.</li>
          <li><b>Flip</b> — <code>catalog-sides-portrait-flip-*</code> per catalog namespace and layout scope.</li>
          <li><b>Index Embed</b> — remembered Window vs Embed.</li>
          <li><b>Profiles</b> — <code>catalog-user-profiles-*</code>, max 12.</li>
          <li><b>Header bar</b> — hide/show document header.</li>
          <li>Clearing site data for this origin resets chrome. Rebuilding HTML does not.</li>
        </ul>
      </details>
      <details>
        <summary>Session vs saved</summary>
        <ul>
          <li><b>Saved (localStorage, per catalog ns)</b> — theme, Sides/Middle pick, Flip, Customize sizes, Layouts, Profiles (max 12), Favorites, notes, UI scale, Index/About Embed prefs, some Search-split ratios, Clear on miss.</li>
          <li><b>Session</b> — typed Search AC list until you save a session/combination; open expanded card; Legend/Guide open state; Index open/closed this visit (arrow still required to open).</li>
          <li>History <b>All search</b> erases typed history only. History <b>All</b> also targets saved sessions and saved combinations — not theme and not named Layouts unless those were stored as combinations.</li>
          <li>Closing the tab keeps saved keys. A private window will look like a first run.</li>
        </ul>
      </details>
      <details open>
        <summary>Troubleshooting</summary>
        <ul>
          <li><b>Hard-refresh.</b> Reload ignoring cache after a new drop (large DS file especially). Confirm the URL is <code>127.0.0.1:8797/<span class="catalog-help-file">…</span></code> so you are not on an old copy. Stale JS from a previous paste is the usual “buttons do nothing” cause.</li>
          <li><b>Search not opening.</b> Press header <b>S</b>. If Hide Search was used, show it again. If a card/gallery/Legend is fullscreen, Back first (Search is parked behind overlays). Then click the field; AC should list under it, not as a front card. In Middle + Flip, if Search is zero-width: Customize → Default.</li>
          <li><b>Layout stuck.</b> Customize off? Edges will not drag. Press <b>Default</b>, or Layouts → a known preset. Unpin a locked separator. Flip once and back if Sides/Middle look mirrored. Profiles can restore a saved chrome snapshot. Last resort: clear this origin’s <code>localStorage</code> (you will lose theme and saved layouts).</li>
          <li><b>Index empty / closed</b> — use the Index arrow. Product default is closed. Window should fill down to About; Collapse returns cards. If Window covers a front card, close the card overlay — Window is supposed to hide then.</li>
          <li><b>Missing libraries.</b> Desktop file out of date — rebuild from <code>komplete.db3</code> (Kontakt) or rescan DS library folders, then replace the file you serve.</li>
          <li><b>Folder icon does nothing.</b> You are on portable, or the path is not on this machine. Use Copy instead. PATH is icons-only; FS opens the reader.</li>
          <li><b>Legend / Guide missing.</b> The content window must be on screen (Sides, Middle, or content-only). Edge keys hide during card overlays and must not cover About; close preview / gallery first.</li>
          <li><b>Skip icons missing or covering the scrollbar.</b> They are filled skip-to-top / skip-to-bottom squares, not “↑ top” text. They hide while Index Window is open. They should leave a small gap so the scrollbar track stays clickable.</li>
        </ul>
      </details>
      <details>
        <summary>About stamp</summary>
        <p class="catalog-help-muted">The About / Document body (generation time, rebuild one-liner) is the live stamp for this file. Same text is reused under Legend → About / Document. No standalone changelog in this repository; this Update guide is the in-catalog record.</p>
      </details>
    </div>'''


def once(text: str, old: str, new: str, label: str, name: str) -> str:
    if old not in text:
        if new in text:
            print(f"  skip {label} {name}")
            return text
        raise SystemExit(f"{name}: missing {label}: {old[:120]!r}")
    n = text.count(old)
    if n != 1:
        raise SystemExit(f"{name}: {label} count {n}")
    print(f"  1x {label} {name}")
    return text.replace(old, new, 1)


def splice(text: str, name: str) -> str:
    i = text.find(START)
    if i < 0:
        raise SystemExit(f"{name}: legend panel missing")
    k = text.find(OLD_PANEL_END, i)
    if k < 0:
        raise SystemExit(f"{name}: update-panel About stamp end missing")
    if text.find(START, i + 1) >= 0:
        raise SystemExit(f"{name}: duplicate legend start")
    print(f"  splice help {name}")
    return text[:i] + NEW_PANELS + text[k + len(OLD_PANEL_END) :]


def safe_write(path: Path, text: str) -> None:
    if not text.rstrip().endswith("</html>"):
        raise SystemExit(f"{path.name}: rewrite would drop </html>")
    raw = text.encode("utf-8")
    min_size = 4_000_000 if path.name.startswith("DS-") else 1_000_000
    if len(raw) < min_size:
        raise SystemExit(f"{path.name}: unreasonable size {len(raw)}")
    fd, tmp = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=str(path.parent))
    try:
        os.write(fd, raw)
        os.fsync(fd)
        os.close(fd)
        fd = -1
        tmp_path = Path(tmp)
        check = tmp_path.read_bytes()
        if not check.rstrip().endswith(b"</html>"):
            tmp_path.unlink(missing_ok=True)
            raise SystemExit(f"{path.name}: tmp missing </html>")
        if len(check) != len(raw):
            tmp_path.unlink(missing_ok=True)
            raise SystemExit(f"{path.name}: tmp size mismatch")
        os.replace(tmp, path)
        assert path.stat().st_size == len(raw)
        assert path.read_text(encoding="utf-8").rstrip().endswith("</html>")
        print(f"ok {path.name} bytes={len(raw)}")
    finally:
        if fd >= 0:
            try:
                os.close(fd)
            except OSError:
                pass
        if os.path.exists(tmp):
            os.unlink(tmp)


def patch(path: Path) -> None:
    name = path.name
    text = path.read_text(encoding="utf-8")
    c00 = text.count("sessionId:'c00e3e'")
    if "portable" in name:
        text = once(text, PORT_INSET_OLD, PORT_INSET_NEW, "port-inset", name)
    else:
        text = once(text, DESK_RIGHT_OLD, DESK_RIGHT_NEW, "desk-right", name)
    text = splice(text, name)
    if "Skip to top / bottom" not in text:
        raise SystemExit(f"{name}: jump legend missing")
    i0 = text.find('id="catalogHelpLegend"')
    i1 = text.find('id="hlBackdrop"')
    help_html = text[i0:i1] if i0 >= 0 and i1 > i0 else ""
    if "<b>↑ top / ↓ bottom</b>" in help_html or "Jump ↑/↓" in help_html:
        raise SystemExit(f"{name}: leftover ↑/↓ labels in help")
    if "max 12" not in text and "Max <b>12</b>" not in text:
        raise SystemExit(f"{name}: profiles cap missing")
    if "catalogHelpAboutReuse" not in text or "catalogHelpRebuild" not in text:
        raise SystemExit(f"{name}: help ids missing")
    if text.count("sessionId:'c00e3e'") < c00:
        raise SystemExit(f"{name}: lost c00e3e logs")
    safe_write(path, text)


def main() -> None:
    for p in FILES:
        print("==", p.name)
        patch(p)


if __name__ == "__main__":
    main()
