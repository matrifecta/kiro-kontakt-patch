#!/usr/bin/env python3
"""Verify desktop Search-strip/card baselines + Middle KW arrow hidden."""
from __future__ import annotations

import json
import os
import signal
import subprocess
import time
import urllib.request
from pathlib import Path

OUT = Path("/home/phnx/kiro-kontakt-patch/kiro/_patch/verify_desktop_search_card_align.json")
SHOT = Path("/home/phnx/kiro-kontakt-patch/kiro/_patch/ui-pos-shots")
PORT = 9588
HTTP = 8797
PROFILE = "/tmp/catalog-desk-search-card-align"
CHROME = "/usr/bin/chromium"
SHOT.mkdir(parents=True, exist_ok=True)
os.makedirs(PROFILE, exist_ok=True)

SETUP = r"""
(() => {
  if (typeof setDisplayMode === 'function') setDisplayMode('sides', {pick: true});
  document.body.classList.remove('search-chrome-collapsed', 'kw-chrome-collapsed', 'catalog-portable');
  document.body.classList.add('search-mode', 'kw-open');
  var fw = document.getElementById('filterWrap');
  if (fw) fw.classList.add('open');
  if (typeof setMode === 'function') setMode('search');
  if (typeof showAc === 'function') showAc('', {force: true});
  if (typeof equalizeCatalogCardRows === 'function') equalizeCatalogCardRows();
  if (typeof syncKwHideBtn === 'function') syncKwHideBtn();
  return true;
})()
"""

PROBE = r"""
(() => {
  function box(el) {
    if (!el) return null;
    var r = el.getBoundingClientRect();
    var cs = getComputedStyle(el);
    return {
      t: Math.round(r.top * 10) / 10,
      b: Math.round(r.bottom * 10) / 10,
      l: Math.round(r.left * 10) / 10,
      h: Math.round(r.height * 10) / 10,
      w: Math.round(r.width * 10) / 10,
      d: cs.display, vis: cs.visibility, pe: cs.pointerEvents
    };
  }
  function vis(el) {
    if (!el) return false;
    var cs = getComputedStyle(el);
    if (cs.display === 'none' || cs.visibility === 'hidden' || Number(cs.opacity) === 0) return false;
    var r = el.getBoundingClientRect();
    return r.width > 1 && r.height > 1;
  }
  function spread(vals) {
    if (!vals.length) return 0;
    return Math.round((Math.max.apply(null, vals) - Math.min.apply(null, vals)) * 10) / 10;
  }
  var strip = document.getElementById('searchStrip');
  var inp = document.getElementById('searchInput');
  var clr = strip && strip.querySelector('.search-strip-clear');
  var hist = document.getElementById('searchHistory');
  var hide = strip && strip.querySelector('.search-strip-hide');
  var fs = document.getElementById('searchStripFs');
  var more = document.getElementById('searchStripMore');
  var stripBtns = [inp, clr, hist, hide, fs, more].filter(vis);
  var stripTops = stripBtns.map(function (el) { return box(el).t; });
  var stripHs = stripBtns.map(function (el) { return box(el).h; });
  var counts = Array.prototype.slice.call(document.querySelectorAll('#acList .ac-item .ac-count, #acList .ac-item .ac-lib-mark')).filter(vis).slice(0, 24);
  var countRights = counts.map(function (el) { return box(el).l + box(el).w; });
  var groups = [];
  document.querySelectorAll('.loc-group').forEach(function (g, gi) {
    if (gi > 5) return;
    var cards = [];
    g.querySelectorAll(':scope > .entry').forEach(function (e) {
      if (e.classList.contains('is-hidden') || e.classList.contains('highlight')) return;
      if (e.style.display === 'none') return;
      if (typeof catalogCardIsExpanded === 'function' && catalogCardIsExpanded(e)) return;
      var r = e.getBoundingClientRect();
      if (r.width < 4 || r.height < 4) return;
      cards.push(e);
    });
    var rows = [];
    cards.forEach(function (e) {
      var t = Math.round(e.getBoundingClientRect().top);
      var row = null;
      for (var i = 0; i < rows.length; i++) { if (Math.abs(rows[i].t - t) <= 12) { row = rows[i]; break; } }
      if (!row) { row = { t: t, cards: [] }; rows.push(row); }
      row.cards.push(e);
    });
    rows.forEach(function (row, ri) {
      if (row.cards.length < 2) return;
      function metric(sel) {
        return row.cards.map(function (e) {
          var el = e.querySelector(sel);
          return el && vis(el) ? box(el).t : null;
        }).filter(function (v) { return v != null; });
      }
      var searchVsFav = row.cards.map(function (e) {
        var s = e.querySelector('.search-popup-btn, .search-link');
        var f = e.querySelector('.fav-btn');
        if (!s || !f || !vis(s) || !vis(f)) return null;
        return Math.abs(box(s).t - box(f).t);
      }).filter(function (v) { return v != null; });
      groups.push({
        g: gi, r: ri, n: row.cards.length,
        name: spread(metric('.lib-name')),
        desc: spread(metric('.summary-panel')),
        path: spread(metric('.path')),
        patches: spread(metric('details.patches, .patches')),
        actions: spread(metric('.card-actions')),
        search: spread(metric('.search-popup-btn, .search-link')),
        fav: spread(metric('.fav-btn')),
        cover: spread(metric('.cover')),
        searchFavMax: searchVsFav.length ? Math.max.apply(null, searchVsFav) : null,
        ids: row.cards.slice(0, 6).map(function (e) { return e.id; })
      });
    });
  });
  var arrow = document.querySelector('#filterToggle .toggle-arrow');
  var acN = document.querySelectorAll('#acList .ac-item').length;
  return {
    vw: innerWidth, vh: innerHeight,
    portable: !!window.CATALOG_PORTABLE,
    sides: document.body.classList.contains('display-sides'),
    middle: document.body.classList.contains('display-middle'),
    land: document.body.classList.contains('desk-landscape'),
    body: document.body.className,
    strip: {
      n: stripBtns.length,
      topSpread: spread(stripTops),
      hSpread: spread(stripHs),
      heights: stripHs,
      ids: stripBtns.map(function (el) { return el.id || el.className; })
    },
    ac: { n: acN, countRightSpread: spread(countRights), counts: counts.length },
    rows: groups,
    arrow: {
      exists: !!arrow,
      text: arrow ? String(arrow.textContent || '') : '',
      vis: vis(arrow),
      d: arrow ? getComputedStyle(arrow).display : null,
      box: box(arrow)
    }
  };
})()
"""


def wait_dbg(timeout=20):
    t0 = time.time()
    while time.time() - t0 < timeout:
        try:
            tabs = json.load(urllib.request.urlopen(f"http://127.0.0.1:{PORT}/json", timeout=1))
            pages = [t for t in tabs if t.get("type") == "page" and t.get("webSocketDebuggerUrl")]
            if pages:
                return pages[0]
        except Exception:
            time.sleep(0.2)
    raise SystemExit("no debugger tab")


class CDP:
    def __init__(self, ws_url):
        import websocket

        self.ws = websocket.create_connection(ws_url, timeout=60)
        self.id = 0

    def call(self, method, params=None, timeout=90):
        self.id += 1
        mid = self.id
        self.ws.send(json.dumps({"id": mid, "method": method, "params": params or {}}))
        t0 = time.time()
        while time.time() - t0 < timeout:
            msg = json.loads(self.ws.recv())
            if msg.get("id") == mid:
                if "error" in msg:
                    raise RuntimeError(f"{method}: {msg['error']}")
                return msg.get("result", {})
        raise TimeoutError(method)

    def eval(self, expr, await_p=False):
        r = self.call(
            "Runtime.evaluate",
            {"expression": expr, "returnByValue": True, "awaitPromise": bool(await_p)},
        )
        if r.get("exceptionDetails"):
            raise RuntimeError(r["exceptionDetails"])
        return r.get("result", {}).get("value")


def set_view(cdp, w, h):
    cdp.call(
        "Emulation.setDeviceMetricsOverride",
        {
            "width": w,
            "height": h,
            "deviceScaleFactor": 1,
            "mobile": False,
            "screenOrientation": {
                "type": "portraitPrimary" if h >= w else "landscapePrimary",
                "angle": 0 if h >= w else 90,
            },
        },
    )
    time.sleep(0.25)


def wait_ready(cdp):
    for _ in range(80):
        try:
            if cdp.eval("!!(document.getElementById('catalogMain')&&typeof setDisplayMode==='function')"):
                return
        except Exception:
            pass
        time.sleep(0.2)
    raise SystemExit("catalog not ready")


def nav(cdp, url):
    cdp.call("Page.enable")
    cdp.call("Runtime.enable")
    cdp.call("Page.navigate", {"url": url})
    time.sleep(1.4)
    wait_ready(cdp)
    time.sleep(0.4)


def shot(cdp, name):
    import base64

    data = cdp.call("Page.captureScreenshot", {"format": "png", "fromSurface": True})
    raw = data.get("data")
    if not raw:
        return None
    path = SHOT / name
    path.write_bytes(base64.b64decode(raw))
    return str(path)


def issues_for(data, expect_arrow, tag):
    issues = []
    if data.get("portable"):
        issues.append(f"{tag}:portable-flag")
    st = data.get("strip") or {}
    if st.get("topSpread", 99) > 1.2:
        issues.append(f"{tag}:strip-top:{st.get('topSpread')}")
    if st.get("hSpread", 99) > 1.2:
        issues.append(f"{tag}:strip-h:{st.get('hSpread')}")
    ac = data.get("ac") or {}
    if ac.get("counts", 0) >= 3 and ac.get("countRightSpread", 99) > 2.0:
        issues.append(f"{tag}:ac-count:{ac.get('countRightSpread')}")
    for row in data.get("rows") or []:
        rid = f"{tag}:g{row.get('g')}r{row.get('r')}"
        for k in ("name", "desc", "path", "patches", "actions", "search", "fav"):
            if row.get(k) is not None and row[k] > 2.0:
                issues.append(f"{rid}:{k}:{row[k]}")
        if row.get("searchFavMax") is not None and row["searchFavMax"] > 2.0:
            issues.append(f"{rid}:searchFav:{row['searchFavMax']}")
    arrow = data.get("arrow") or {}
    if expect_arrow and not arrow.get("vis"):
        issues.append(f"{tag}:arrow-missing")
    if not expect_arrow and arrow.get("vis"):
        issues.append(f"{tag}:arrow-still-visible:{arrow.get('text')}")
    return issues


def run_file(cdp, filename):
    out = {"file": filename, "issues": [], "shots": []}
    nav(cdp, f"http://127.0.0.1:{HTTP}/{filename}?deskalign=1")
    set_view(cdp, 1400, 900)
    cdp.eval(SETUP)
    time.sleep(0.5)
    if cdp.eval("typeof equalizeCatalogCardRows==='function'&&equalizeCatalogCardRows();true"):
        pass
    time.sleep(0.25)
    sides = cdp.eval(PROBE)
    out["sides"] = sides
    out["shots"].append(shot(cdp, f"D1400-{filename}-sides-align.png"))
    out["issues"].extend(issues_for(sides, True, "sides"))

    # scroll later loc-group
    cdp.eval(
        "var sc=(typeof catalogContentScroller==='function'&&catalogContentScroller())||document.getElementById('catalogMain');"
        "var g=document.querySelectorAll('.loc-group')[1];"
        "if(sc&&g){var r=g.getBoundingClientRect(),sr=sc.getBoundingClientRect();sc.scrollTop+=Math.max(0,r.top-sr.top-8);}"
        "if(typeof equalizeCatalogCardRows==='function')equalizeCatalogCardRows();true"
    )
    time.sleep(0.3)
    g2 = cdp.eval(PROBE)
    out["sides_g2"] = {"rows": (g2 or {}).get("rows")}
    out["issues"].extend(issues_for(g2, True, "sides-g2"))

    # open patch tree on first visible card
    cdp.eval(
        "var e=document.querySelector('.loc-group > .entry:not(.is-hidden)');"
        "var d=e&&e.querySelector('details.patches');"
        "if(d)d.open=true;"
        "if(typeof equalizeCatalogCardRows==='function')equalizeCatalogCardRows();true"
    )
    time.sleep(0.25)
    openp = cdp.eval(PROBE)
    out["patch_open"] = {"n": len((openp or {}).get("rows") or [])}
    out["issues"].extend(issues_for(openp, True, "patch-open"))
    cdp.eval(
        "document.querySelectorAll('details.patches[open],.path.is-expanded').forEach(function(el){"
        "if(el.tagName==='DETAILS')el.open=false;else el.classList.remove('is-expanded');});"
        "if(typeof equalizeCatalogCardRows==='function')equalizeCatalogCardRows();true"
    )
    time.sleep(0.2)

    # Middle: arrow must be gone
    cdp.eval("if(typeof setDisplayMode==='function')setDisplayMode('middle',{pick:true});true")
    time.sleep(0.45)
    cdp.eval(SETUP.replace("setDisplayMode('sides', {pick: true})", "setDisplayMode('middle', {pick: true})"))
    time.sleep(0.35)
    mid = cdp.eval(PROBE)
    out["middle"] = mid
    out["shots"].append(shot(cdp, f"D1400-{filename}-middle-kw.png"))
    if not mid.get("middle"):
        out["issues"].append("middle:not-middle")
    out["issues"].extend(issues_for(mid, False, "middle"))

    # Portrait Sides: arrow should remain (hide control)
    cdp.eval("if(typeof setDisplayMode==='function')setDisplayMode('sides',{pick:true});true")
    set_view(cdp, 900, 1400)
    time.sleep(0.4)
    cdp.eval(SETUP)
    time.sleep(0.35)
    port = cdp.eval(PROBE)
    out["portrait"] = {"arrow": (port or {}).get("arrow"), "middle": (port or {}).get("middle")}
    out["shots"].append(shot(cdp, f"D900x1400-{filename}-portrait-sides.png"))
    if port.get("middle"):
        out["issues"].append("portrait:still-middle")
    out["issues"].extend(issues_for(port, True, "portrait-sides"))

    out["pass"] = not out["issues"]
    return out


def main():
    proc = subprocess.Popen(
        [
            CHROME,
            "--headless=new",
            "--disable-gpu",
            "--no-sandbox",
            f"--remote-debugging-port={PORT}",
            "--remote-allow-origins=*",
            f"--user-data-dir={PROFILE}",
            "about:blank",
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    results = []
    try:
        page = wait_dbg()
        cdp = CDP(page["webSocketDebuggerUrl"])
        results.append(run_file(cdp, "DS-CATALOG.html"))
        results.append(run_file(cdp, "KONTAKT-CATALOG.html"))
    finally:
        try:
            proc.send_signal(signal.SIGTERM)
            proc.wait(timeout=3)
        except Exception:
            proc.kill()
    payload = {"ok": all(r.get("pass") for r in results), "results": results}
    OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps({"ok": payload["ok"], "files": [{k: r.get(k) for k in ("file", "pass", "issues")} for r in results]}, indent=2))
    if not payload["ok"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
