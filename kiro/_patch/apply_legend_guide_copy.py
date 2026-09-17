#!/usr/bin/env python3
"""Replace stub Legend/Guide panels with full catalog copy. Safe DS writes."""
from pathlib import Path

FILES = [
    Path("/home/phnx/kiro-kontakt-patch/public/catalogs/DS-CATALOG.html"),
    Path("/home/phnx/kiro-kontakt-patch/public/catalogs/KONTAKT-CATALOG.html"),
    Path("/home/phnx/kiro-kontakt-patch/public/catalogs/DS-CATALOG-portable.html"),
    Path("/home/phnx/kiro-kontakt-patch/public/catalogs/KONTAKT-CATALOG-portable.html"),
]

OLD_START = '    <div class="catalog-help-panel" id="catalogHelpLegend" data-panel="legend">'
OLD_END = '    </div>\n  </div>\n</div>\n<div id="hlBackdrop"'

CSS_OLD = ".catalog-help-body code{font-size:.85em;background:var(--bg);border:1px solid var(--border);border-radius:4px;padding:.05em .3em}\n"
CSS_NEW = CSS_OLD + (
    ".catalog-help-k{margin:.55rem 0 .12rem;color:var(--accent-instrument);font-size:.72rem;"
    "font-weight:700;letter-spacing:.06em;text-transform:uppercase}\n"
    ".catalog-help-body ol{margin:.15rem 0 .35rem 1.15rem;padding:0}\n"
    ".catalog-help-body ol li{margin:.15rem 0}\n"
    ".catalog-help-body .catalog-help-scene-lead{margin:.15rem 0 .4rem}\n"
)

FILL_OLD = """function catalogHelpFillCopy(){
  var ns=window.CATALOG_NS==='ds'?'Decent Sampler':'Kontakt';
  document.querySelectorAll('.catalog-help-product').forEach(function(el){el.textContent=ns+' catalog';});
  var about=document.getElementById('catalogDocNoteBody');
  var lead=document.getElementById('catalogHelpLegendLead');
  var reuse=document.getElementById('catalogHelpAboutReuse');
  var txt=about?String(about.textContent||'').replace(/\\s+/g,' ').trim():'';
  if(lead)lead.textContent=ns+' chrome and symbols. Cards stay in the content window; these keys sit on its left border.';
  if(reuse)reuse.textContent=txt||('About / Document is the collapsible note at the foot of the '+ns+' content window.');
  var rebuild=document.getElementById('catalogHelpRebuild');
  if(rebuild){
    rebuild.innerHTML=window.CATALOG_NS==='ds'
      ? 'Added libraries? Re-run <code>build-ds-catalog-html.sh both</code>, then reload. Desktop and portable catalogs are separate files.'
      : 'Registered libraries come from <code>komplete.db3</code>. Rebuild with <code>build-kontakt-catalog-html.sh</code>, then reload. Desktop and portable catalogs are separate files.';
  }
}
"""

FILL_NEW = """function catalogHelpFillCopy(){
  var ns=window.CATALOG_NS==='ds'?'Decent Sampler':'Kontakt';
  var portable=!!window.CATALOG_PORTABLE;
  document.querySelectorAll('.catalog-help-product').forEach(function(el){el.textContent=ns;});
  document.querySelectorAll('.catalog-help-file').forEach(function(el){
    el.textContent=window.CATALOG_NS==='ds'
      ?(portable?'DS-CATALOG-portable.html':'DS-CATALOG.html')
      :(portable?'KONTAKT-CATALOG-portable.html':'KONTAKT-CATALOG.html');
  });
  var about=document.getElementById('catalogDocNoteBody');
  var reuse=document.getElementById('catalogHelpAboutReuse');
  var txt=about?String(about.textContent||'').replace(/\\s+/g,' ').trim():'';
  if(reuse)reuse.textContent=txt||('About / Document is the collapsible note at the foot of the '+ns+' content window.');
  var rebuild=document.getElementById('catalogHelpRebuild');
  if(rebuild){
    rebuild.innerHTML=window.CATALOG_NS==='ds'
      ? 'Added libraries? From the repo, re-run <code>build-ds-catalog-html.sh both</code> (desktop + portable), copy the new HTML into <code>public/catalogs/</code>, then reload. Portable is a separate file with banners embedded.'
      : 'Registered libraries come from <code>komplete.db3</code>. Re-run <code>build-kontakt-catalog-html.sh both</code>, copy into <code>public/catalogs/</code>, then reload. Click a name in Index to jump; desktop [open folder] opens the library in Dolphin.';
  }
}
"""

NEW_PANELS = r'''    <div class="catalog-help-panel" id="catalogHelpLegend" data-panel="legend">
      <p class="catalog-help-muted catalog-help-scene-lead" id="catalogHelpLegendLead">Legend for the <span class="catalog-help-product">catalog</span> chrome. Cards stay in the content window; this key sits on its left border.</p>
      <details open>
        <summary>Symbols</summary>
        <ul>
          <li><b>Path row</b> — three themed icons on each card: <b>⛶</b> (card fullscreen / overlay), <b>copy</b> (clipboard the folder path), <b>folder</b> (open the library in the file manager on desktop; omitted or inert on portable).</li>
          <li><b>♡ / ♥</b> — Favorite on the card (and gallery). Filled when the library is saved locally.</li>
          <li><b>← Back</b> — one step back from expanded card, fullscreen, gallery, description/path reader, Search/Keywords fullscreen, or this Legend/Guide.</li>
          <li><b>⛶</b> on a desktop expanded card — enter fullscreen. On Search / Keywords strips — fullscreen that menu. Hidden on portable card chrome (phone goes straight to fullscreen popups).</li>
          <li><b>⋯</b> — overflow: header More, Search More, Keywords More. Portrait parks extra tools here (Clear on miss, scale, theme).</li>
          <li><b>Index arrow</b> — opens Index. It stays closed until you use that arrow. <b>Embed</b> puts the list with the cards; without Embed it is a <b>Window</b> docked on the content pane.</li>
          <li><b>↑ top / ↓ bottom</b> — jump stack on the content window (usually bottom-right). Stay put while cards scroll.</li>
          <li><b>Legend / Guide</b> — these left-edge keys. Selected sticks out further.</li>
          <li><b>Flip</b> — swaps Search and Keywords columns (Sides: skip-center; Middle: mirror the pair). Portrait stacks first-above.</li>
          <li><b>Clear</b> (sweep icon) — clears Search + Keywords filters. <b>Clear on miss</b> — if you leave gallery on a library that is not a current hit, Search clears.</li>
          <li><b>H</b> — History (session AC, saved sessions, saved combinations). Trash in Search is the same Clear sweep.</li>
          <li><b>S</b> / <b>K</b> — show or hide the Search and Keywords menus. Companion K / magnifier in fullscreen puts the other menu side-by-side.</li>
        </ul>
      </details>
      <details>
        <summary>Fields</summary>
        <ul>
          <li><b>Search libraries…</b> — name / other / patch tokens. Does not auto-open a front card. Hits highlight in the content window.</li>
          <li><b>Suggestion list</b> (session AC) — lives in the Search column under the field. Session only until you save. Resize edges show in Customize.</li>
          <li><b>Keywords pills</b> — Instrument / Brand / Model / Vibe / Patch groups. Combine to narrow. Active filters also appear as Search pills.</li>
          <li><b>Name</b> — library title on the card (<code>.lib-name</code>).</li>
          <li><b>Path</b> — folder location under the cover, with the icon row.</li>
          <li><b>Description</b> — blurb on the card; tap to open the description reader.</li>
          <li><b>Patch search / Patches</b> — nested patch tree on the card (DS: grouped by subfolder). Collapse evens card heights.</li>
          <li><b>Card Search</b> — in-card Google / YouTube / image search when a card is expanded (Popup vs embed depends on portable).</li>
        </ul>
      </details>
      <details>
        <summary>Content window</summary>
        <ul>
          <li><b>Cards</b> — one library each, in the middle pane. Grid in the catalog; <b>expanded card</b> is the desktop preview (centered, dimmed catalog behind).</li>
          <li><b>Covers</b> — banner art. Tap for gallery / image focus. Long-press / favorite from there.</li>
          <li><b>Index (alphabetical)</b> — name list. Closed until the Index arrow. Window docks over the pane; Embed scrolls with cards.</li>
          <li><b>About / Document</b> — generation stamp and rebuild note at the foot. Window or Embed, same idea as Index.</li>
          <li><b>Pinned pyramid</b> — minimized cards dock at the bottom of the content window (Save on Middle).</li>
        </ul>
      </details>
      <details>
        <summary>Menu windows</summary>
        <ul>
          <li><b>Search</b> — left (Sides landscape) or top (Middle / portrait). Field, AC list, pills, ⛶, Hide Search, scale.</li>
          <li><b>Keywords</b> — right (Sides landscape) or paired with Search on Middle. Categories, pills, Hide Keywords, ⛶, Collapse, Customize, Layouts.</li>
          <li><b>Sides</b> — Search | content | Keywords as three panes. Content is the only scrolling card window.</li>
          <li><b>Middle</b> — Search + Keywords on top, catalog below (title: “Search and Keywords on top, catalog below”).</li>
          <li><b>Portrait vs landscape</b> — desktop ≥900px still uses Sides/Middle; portrait stacks menus. Landscape puts Search and Keywords beside the catalog. Portable is always phone chrome.</li>
          <li>Separators (Search split, dual-FS, Index height) drag only while <b>Customize</b> is on.</li>
        </ul>
      </details>
      <details>
        <summary>Mode-changing buttons</summary>
        <ul>
          <li><b>S</b> / <b>K</b> — Search / Keywords visibility (header).</li>
          <li><b>Sides</b> / <b>Middle</b> — layout pick (persisted per catalog ns + orientation).</li>
          <li><b>Flip</b> — swap the menu columns / stacked order.</li>
          <li><b>Collapse</b> — close open patch trees and even card row heights.</li>
          <li><b>Customize</b> — reveal drag edges for Search, Keywords, Index, menu height.</li>
          <li><b>Layouts</b> — named menu size presets (Search + Keywords vs Search-only stores).</li>
          <li><b>Profiles</b> — saved workspace snapshots (pills, Flip, related chrome). Cap on how many you can keep.</li>
          <li><b>Theme picker</b> — Desert Dusk, Smoked Glass, Sand Storm, and the rest. Saved as <code>catalog-theme</code>.</li>
          <li><b>Pick / Search</b> — data mode for Keywords vs typed Search.</li>
          <li><b>Portable vs desktop</b> — <code>*-portable.html</code> always phone (<code>CATALOG_PORTABLE</code>). Desktop file at min-width 900px gets expanded cards + extra ⛶. Same widgets, different presentation.</li>
        </ul>
      </details>
      <details>
        <summary>About / Document</summary>
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
          <li>Pick a suggestion or press through hits in the content window. Click the card you want.</li>
        </ol>
        <p class="catalog-help-k">You should see</p>
        <p>The AC list stays in the Search column. Cards in the content window filter/highlight. Nothing auto-opens as an expanded card.</p>
      </details>
      <details>
        <summary>Filter by Keywords</summary>
        <p class="catalog-help-k">Goal</p>
        <p>Narrow the grid with Instrument / Brand / Vibe (or Patch) pills.</p>
        <p class="catalog-help-k">Steps</p>
        <ol>
          <li>Turn <b>K</b> on. Open Keywords if the arrow is collapsed.</li>
          <li>Choose a category (All, Instrument, Brand, Model, Vibe, Patch), then tap pills. Combine freely.</li>
          <li>Sweep <b>Clear</b> when you want the full set again.</li>
        </ol>
        <p class="catalog-help-k">You should see</p>
        <p>Pills accent when active. The content window only shows matching cards. Search pills row mirrors active filters.</p>
      </details>
      <details>
        <summary>Open a card / expanded card</summary>
        <p class="catalog-help-k">Goal</p>
        <p>Read one library without losing the catalog behind it.</p>
        <p class="catalog-help-k">Steps</p>
        <ol>
          <li>Click the card (name / body) in the grid.</li>
          <li>Desktop: you get an <b>expanded card</b> (preview). Portable/phone: a fullscreen popup.</li>
          <li><b>← Back</b> (top left) returns one step.</li>
        </ol>
        <p class="catalog-help-k">You should see</p>
        <p>Desktop: catalog dimmed, card centered, Back left, ⛶ right. Phone: full window, Back left, no extra ⛶ on that surface.</p>
      </details>
      <details>
        <summary>Path, folder, copy, card FS</summary>
        <p class="catalog-help-k">Goal</p>
        <p>Get to the files, copy the path, or take the card fullscreen.</p>
        <p class="catalog-help-k">Steps</p>
        <ol>
          <li>On the card path row: <b>folder</b> opens Dolphin (desktop HTML only).</li>
          <li><b>Copy</b> puts the path on the clipboard.</li>
          <li>Path-row <b>⛶</b> or the expanded-card ⛶ enters overlay / fullscreen. Back leaves it.</li>
        </ol>
        <p class="catalog-help-k">You should see</p>
        <p>Icons follow the theme (not a black raster). Portable has no desktop folder-open. Fullscreen Back returns to the expanded card on desktop, then another Back to the grid.</p>
      </details>
      <details>
        <summary>Index Window vs Embed</summary>
        <p class="catalog-help-k">Goal</p>
        <p>Use the alphabetical list without covering Search.</p>
        <p class="catalog-help-k">Steps</p>
        <ol>
          <li>Click the <b>Index arrow</b> — the list stays closed until you do.</li>
          <li>Leave Embed off for <b>Window</b> (docked on the content pane).</li>
          <li>Press <b>Embed</b> to park the list above/with the cards and scroll it in-flow.</li>
          <li>Click a name to jump to that card.</li>
        </ol>
        <p class="catalog-help-k">You should see</p>
        <p>Window fills the content pane as its own surface. Embed sits in the card column. Search/Keywords chrome stays put. Jump ↑/↓ hide while Index Window is open.</p>
      </details>
      <details>
        <summary>Sides vs Middle</summary>
        <p class="catalog-help-k">Goal</p>
        <p>Choose whether menus hug the catalog or sit above it.</p>
        <p class="catalog-help-k">Steps</p>
        <ol>
          <li>Header: <b>Sides</b> — Search | content | Keywords.</li>
          <li><b>Middle</b> — Search and Keywords on top, catalog below.</li>
          <li>Cards always stay in the content window; these keys stay on its left border.</li>
        </ol>
        <p class="catalog-help-k">You should see</p>
        <p>The active layout button accents. Content pane border is where Legend/Guide and ↑/↓ live. Pick is stored for this catalog + orientation.</p>
      </details>
      <details>
        <summary>Flip</summary>
        <p class="catalog-help-k">Goal</p>
        <p>Swap which side Search vs Keywords occupy.</p>
        <p class="catalog-help-k">Steps</p>
        <ol>
          <li>Press <b>Flip</b> (header / layout cluster).</li>
          <li>Sides: menus skip the center catalog. Middle: the top pair mirrors. Portrait: stacked order flips first-above.</li>
        </ol>
        <p class="catalog-help-k">You should see</p>
        <p>Search and Keywords trade places. The content window does not move off-center. Flip can be stored in a Profile.</p>
      </details>
      <details>
        <summary>Portrait desktop vs landscape</summary>
        <p class="catalog-help-k">Goal</p>
        <p>Keep Sides/Middle usable when the window is tall vs wide.</p>
        <p class="catalog-help-k">Steps</p>
        <ol>
          <li>Desktop is min-width 900px. Rotate or resize across that.</li>
          <li>Landscape: three columns (Sides) or menus-above (Middle).</li>
          <li>Portrait: menus stack; extra header tools go behind ⋯ if they overflow.</li>
        </ol>
        <p class="catalog-help-k">You should see</p>
        <p>Cards remain in the content window. Legend/Guide stay on that pane’s left edge, not on Search.</p>
      </details>
      <details>
        <summary>Mobile / portable</summary>
        <p class="catalog-help-k">Goal</p>
        <p>Use the phone file or a narrow viewport without desktop card+⛶.</p>
        <p class="catalog-help-k">Steps</p>
        <ol>
          <li>Open <code class="catalog-help-file">*-portable.html</code> — always phone, even on a wide screen.</li>
          <li>Or shrink the desktop file below 900px.</li>
          <li>Open Legend/Guide, a card, or a reader — you get a fullscreen popup. Back exits.</li>
        </ol>
        <p class="catalog-help-k">You should see</p>
        <p>No extra ⛶ on the Legend/Guide surface. Path folder-open is desktop-only. Banners in portable are embedded in the file.</p>
      </details>
      <details>
        <summary>Customize separators</summary>
        <p class="catalog-help-k">Goal</p>
        <p>Resize Search, Keywords, and Index by dragging edges.</p>
        <p class="catalog-help-k">Steps</p>
        <ol>
          <li>Press <b>Customize</b> (Keywords tools). Edges become live.</li>
          <li>Drag the Search split, dual-FS separator, AC height/width, Keywords height, Index height.</li>
          <li><b>Default</b> resets sizes. <b>Layouts</b> saves/applies a named preset. Pin locks a separator.</li>
        </ol>
        <p class="catalog-help-k">You should see</p>
        <p>Customize stays accented while edit is on. Without it, separators ignore pointer so you cannot nudge layout by accident.</p>
      </details>
      <details>
        <summary>History</summary>
        <p class="catalog-help-k">Goal</p>
        <p>Revisit or erase Search AC history.</p>
        <p class="catalog-help-k">Steps</p>
        <ol>
          <li>Open Search so the AC shell is visible. Press <b>H</b>.</li>
          <li>Pick rows, or All search / All (includes saved sessions and saved combinations).</li>
          <li>Confirm erase (✓) or keep (✕).</li>
        </ol>
        <p class="catalog-help-k">You should see</p>
        <p>History cloud over the Search dropdown. Session AC is not a saved Layout or Profile until you store it.</p>
      </details>
      <details>
        <summary>Profiles</summary>
        <p class="catalog-help-k">Goal</p>
        <p>Snapshot workspace (pills, Flip, related chrome) and switch later.</p>
        <p class="catalog-help-k">Steps</p>
        <ol>
          <li>Header <b>Profiles</b> (or ⋯ on phone). Save the current setup.</li>
          <li>Switch profiles from the list. Reload the page — the active one should return.</li>
        </ol>
        <p class="catalog-help-k">You should see</p>
        <p>A standing Profiles button on desktop; phone parks it in ⋯. There is a cap on how many you can keep.</p>
      </details>
      <details>
        <summary>Fullscreen menus</summary>
        <p class="catalog-help-k">Goal</p>
        <p>Give Search or Keywords the whole menu surface.</p>
        <p class="catalog-help-k">Steps</p>
        <ol>
          <li>On the Search strip, press ⛶ — Search fullscreen. <b>←</b> on that bar exits.</li>
          <li>On Keywords, press ⛶ the same way. Companion <b>K</b> / magnifier splits both menus.</li>
          <li>Stripe › exposes scale / 50-50 snap while in that fullscreen.</li>
        </ol>
        <p class="catalog-help-k">You should see</p>
        <p>The other column yields space. Dual-FS open hides some jump chrome. Back is always the left arrow on that menu, not a second mystery button beside Refresh.</p>
      </details>
      <details>
        <summary>Back from embed / preview</summary>
        <p class="catalog-help-k">Goal</p>
        <p>Leave overlay without dumping the catalog.</p>
        <p class="catalog-help-k">Steps</p>
        <ol>
          <li>Expanded card: <b>←</b> closes preview.</li>
          <li>From card fullscreen: <b>←</b> returns to the expanded card, then <b>←</b> again to the grid.</li>
          <li>Gallery, description reader, path reader, Legend/Guide fullscreen: same one-step Back.</li>
        </ol>
        <p class="catalog-help-k">You should see</p>
        <p>Each Back peels one layer. The content window and Search/Keywords return as they were (session AC still there; Index still however you left it).</p>
      </details>
    </div>
    <div class="catalog-help-panel" id="catalogHelpUpdate" data-panel="update" role="tabpanel" aria-labelledby="catalogHelpTabUpdate" hidden>
      <p class="catalog-help-muted catalog-help-scene-lead">Update guide — how this <span class="catalog-help-product">catalog</span> file is rebuilt, what persists, and what to do when chrome sticks.</p>
      <details open>
        <summary>Rebuild the catalog HTML</summary>
        <p id="catalogHelpRebuild">Re-run the catalog builder for this library set, then reload the page. Desktop and portable HTML are separate files.</p>
        <ul>
          <li>Scripts live under <code>kiro/specs/kontakt-workspace-drive-dirty-fix/artifacts/</code>.</li>
          <li>Mode argument: <code>desktop</code> | <code>portable</code> | <code>both</code>.</li>
          <li>Kontakt sources <code>komplete.db3</code> (content_type=2). DS walks DecentSampler library folders (patches nested by subfolder).</li>
          <li>Serve from <code>public/catalogs</code> (this project uses <code>http://127.0.0.1:8797/</code>).</li>
        </ul>
      </details>
      <details>
        <summary>After a new catalog drop</summary>
        <ol>
          <li>Replace <span class="catalog-help-file">this HTML</span> (and the sibling portable/desktop file if you use both).</li>
          <li>Hard-reload the tab so the browser does not keep a stale multi-megabyte file.</li>
          <li>Theme, Layouts, Profiles, Favorites, and UI scale stay in localStorage — they are not inside the HTML drop.</li>
          <li>If path/folder icons or covers look wrong, confirm you copied the matching thumbs / portable embed, not only one file.</li>
        </ol>
      </details>
      <details>
        <summary>Portable vs desktop files</summary>
        <ul>
          <li><code>KONTAKT-CATALOG.html</code> / <code>DS-CATALOG.html</code> — desktop thumbs, [open folder] where the OS allows.</li>
          <li><code>*-portable.html</code> — self-contained, banners embedded, phone chrome always (<code>window.CATALOG_PORTABLE</code> / <code>body.catalog-portable</code>).</li>
          <li>Do not mix: a portable file on a 1400px monitor still behaves as phone (fullscreen popups, no desktop card ⛶ on Legend/Guide).</li>
        </ul>
      </details>
      <details>
        <summary>Saved locally vs session</summary>
        <ul>
          <li><b>Saved (localStorage, per catalog ns)</b> — theme, Sides/Middle pick, Flip, Customize sizes, Layouts, Profiles, Favorites, notes, UI scale, Index/About Embed prefs, some Search-split ratios, Clear on miss.</li>
          <li><b>Session</b> — typed Search AC list until you save a session/combination; open expanded card; Legend/Guide open state; Index open/closed this visit (arrow still required to open).</li>
          <li>Clearing site data drops the saved set. Rebuilding HTML does not.</li>
        </ul>
      </details>
      <details>
        <summary>Troubleshooting</summary>
        <ul>
          <li><b>Search not opening</b> — press header <b>S</b>. If a card/gallery/Legend is fullscreen, Back first (Search is parked behind overlays). Then click the field; AC should list under it, not as a front card.</li>
          <li><b>Layout stuck</b> — <b>Customize</b> off? Edges will not drag. Press <b>Default</b>, or Layouts → a known preset. Flip once and back if Sides/Middle look mirrored. Profiles can restore a saved chrome snapshot.</li>
          <li><b>Hard-refresh</b> — reload ignoring cache after a new drop (large DS file especially). Confirm the URL is <code>127.0.0.1:8797/<span class="catalog-help-file">…</span></code> so you are not on an old copy.</li>
          <li><b>Index empty / closed</b> — use the Index arrow. Product default is closed.</li>
          <li><b>Widgets missing</b> — they bind to the content pane in Sides/Middle. They hide under other overlays unless Legend/Guide is the overlay.</li>
        </ul>
      </details>
      <details>
        <summary>About stamp</summary>
        <p class="catalog-help-muted">The About / Document body (generation time, rebuild one-liner) is the live stamp for this file. Same text is reused under Legend → About / Document.</p>
      </details>
    </div>
'''


def patch(path: Path) -> None:
    raw = path.read_bytes()
    orig = len(raw)
    if not raw.rstrip().endswith(b"</html>"):
        raise SystemExit(f"{path.name}: missing </html> before patch")
    text = raw.decode("utf-8")
    name = path.name
    a = text.find(OLD_START)
    b = text.find(OLD_END)
    if a < 0 or b < 0 or b <= a:
        raise SystemExit(f"{name}: panel bounds a={a} b={b}")
    new_text = text[:a] + NEW_PANELS + text[b:]
    if CSS_OLD not in new_text:
        raise SystemExit(f"{name}: help css missing")
    if new_text.count(CSS_OLD) < 1:
        raise SystemExit(f"{name}: css count")
    # CSS_OLD appears once at the help block
    if "catalog-help-k{" not in new_text:
        new_text = new_text.replace(CSS_OLD, CSS_NEW, 1)
    if FILL_OLD not in new_text:
        raise SystemExit(f"{name}: fillCopy block missing")
    new_text = new_text.replace(FILL_OLD, FILL_NEW, 1)
    if "Find a library by Search" not in new_text:
        raise SystemExit(f"{name}: user scenarios missing")
    if "Mode-changing buttons" not in new_text:
        raise SystemExit(f"{name}: legend modes missing")
    if "Rebuild the catalog HTML" not in new_text:
        raise SystemExit(f"{name}: update rebuild missing")
    if not new_text.strip().endswith("</html>"):
        raise SystemExit(f"{name}: truncated")
    out = new_text.encode("utf-8")
    if orig > 4_000_000 and len(out) < orig * 0.9:
        raise SystemExit(f"{name}: size collapsed {orig}->{len(out)}")
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_bytes(out)
    wrote = tmp.read_bytes()
    if len(wrote) != len(out) or not wrote.rstrip().endswith(b"</html>"):
        tmp.unlink()
        raise SystemExit(f"{name}: tmp bad")
    tmp.replace(path)
    print("OK", name, "delta", len(out) - orig)


def main():
    for p in FILES:
        if not p.exists():
            raise SystemExit(f"missing {p}")
        patch(p)


if __name__ == "__main__":
    main()
