#!/usr/bin/env python3
"""Verify desktop card chrome baselines + jump gutter. Chromium 8797."""
from __future__ import annotations

import http.server
import json
import os
import signal
import subprocess
import threading
import time
import urllib.request
from pathlib import Path

OUT = Path("/home/phnx/kiro-kontakt-patch/kiro/_patch/verify_desktop_card_chrome_v2.json")
SHOT = Path("/home/phnx/kiro-kontakt-patch/kiro/_patch/ui-pos-shots")
PORT = 9591
HTTP = 8797
ROOT = Path("/home/phnx/kiro-kontakt-patch/public/catalogs")
PROFILE = "/tmp/catalog-desk-card-chrome-v2"
CHROME = "/usr/bin/chromium"
SHOT.mkdir(parents=True, exist_ok=True)
os.makedirs(PROFILE, exist_ok=True)

SETUP = r"""
(() => {
  if (typeof setDisplayMode === 'function') setDisplayMode('sides', {pick: true});
  document.body.classList.remove('search-chrome-collapsed', 'kw-chrome-collapsed', 'catalog-portable');
  document.body.classList.add('search-mode', 'kw-open', 'index-window-open');
  var fw = document.getElementById('filterWrap');
  if (fw) fw.classList.add('open');
  if (typeof setMode === 'function') setMode('search');
  var ix = document.getElementById('catalogIndex');
  if (ix && ix.classList.contains('is-embedded') && typeof toggleIndexEmbed === 'function') toggleIndexEmbed();
  if (ix && !ix.classList.contains('is-collapsed') && typeof toggleCatalogIndex === 'function') toggleCatalogIndex();
  if (typeof equalizeCatalogCardRows === 'function') equalizeCatalogCardRows();
  if (typeof placeCatalogJumpStack === 'function') placeCatalogJumpStack();
  return {
    sides: document.body.classList.contains('display-sides'),
    indexWin: document.body.classList.contains('index-window-open'),
    ixCollapsed: !!(ix && ix.classList.contains('is-collapsed')),
    portable: !!window.CATALOG_PORTABLE
  };
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
      r: Math.round(r.right * 10) / 10,
      h: Math.round(r.height * 10) / 10,
      w: Math.round(r.width * 10) / 10,
      d: cs.display, vis: cs.visibility
    };
  }
  function vis(el) {
    if (!el) return false;
    var cs = getComputedStyle(el);
    if (cs.display === 'none' || cs.visibility === 'hidden' || Number(cs.opacity) === 0) return false;
    var r = el.getBoundingClientRect();
    return r.width > 1 && r.height > 1;
  }
  function overlap(a, b) {
    if (!a || !b) return false;
    return !(a.r <= b.l + 1 || b.r <= a.l + 1 || a.b <= b.t + 1 || b.b <= a.t + 1);
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
  var groups = [];
  document.querySelectorAll('.loc-group').forEach(function (g, gi) {
    if (gi > 8) return;
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
      for (var i = 0; i < rows.length; i++) { if (Math.abs(rows[i].t - t) <= 24) { row = rows[i]; break; } }
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
      function hmetric(sel) {
        return row.cards.map(function (e) {
          var el = e.querySelector(sel);
          return el && vis(el) ? box(el).h : null;
        }).filter(function (v) { return v != null; });
      }
      var searchVsFav = row.cards.map(function (e) {
        var s = e.querySelector('.search-popup-btn, .search-link');
        var f = e.querySelector('.fav-btn');
        if (!s || !f || !vis(s) || !vis(f)) return null;
        return {
          top: Math.abs(box(s).t - box(f).t),
          bot: Math.abs(box(s).b - box(f).b),
          h: Math.abs(box(s).h - box(f).h)
        };
      }).filter(function (v) { return v != null; });
      var samples = row.cards.slice(0, 6).map(function (e) {
        return {
          id: e.id,
          name: (e.querySelector('.lib-name') || {}).textContent,
          entry: box(e),
          hl: box(e.querySelector('.hl-body')),
          cover: box(e.querySelector('.cover')),
          title: box(e.querySelector('.lib-name')),
          desc: box(e.querySelector('.summary-panel')),
          path: box(e.querySelector('.path')),
          pathLabel: box(e.querySelector('.path-label')),
          icons: box(e.querySelector('.path-action-row')),
          patches: box(e.querySelector('details.patches > summary, .patches > summary')),
          search: box(e.querySelector('.search-popup-btn, .search-link')),
          fav: box(e.querySelector('.fav-btn'))
        };
      });
      groups.push({
        g: gi, r: ri, n: row.cards.length,
        name: spread(metric('.lib-name')),
        desc: spread(metric('.summary-panel')),
        descH: spread(hmetric('.summary-panel')),
        path: spread(metric('.path')),
        pathLabel: spread(metric('.path-label')),
        icons: spread(metric('.path-action-row')),
        patches: spread(metric('details.patches > summary, .patches > summary')),
        actions: spread(metric('.card-actions')),
        search: spread(metric('.search-popup-btn, .search-link')),
        fav: spread(metric('.fav-btn')),
        cover: spread(metric('.cover')),
        searchFavTop: searchVsFav.length ? Math.max.apply(null, searchVsFav.map(function (v) { return v.top; })) : null,
        searchFavBot: searchVsFav.length ? Math.max.apply(null, searchVsFav.map(function (v) { return v.bot; })) : null,
        searchFavH: searchVsFav.length ? Math.max.apply(null, searchVsFav.map(function (v) { return v.h; })) : null,
        ids: row.cards.slice(0, 8).map(function (e) { return e.id; }),
        samples: samples
      });
    });
  });
  var jump = document.getElementById('catalogJumpStack');
  var jb = vis(jump) ? box(jump) : null;
  var jumpHits = [];
  if (jb) {
    document.querySelectorAll('#catalogMain .loc-group > .entry:not(.highlight) details.patches > summary, #catalogMain .loc-group > .entry:not(.highlight) .path-label, #catalogMain .loc-group > .entry:not(.highlight) .search-popup-btn').forEach(function (el) {
      if (!vis(el)) return;
      var b = box(el);
      if (overlap(jb, b)) jumpHits.push({cls: el.className, t: b.t, l: b.l, txt: (el.textContent || '').slice(0, 24)});
    });
  }
  var edge = document.getElementById('catalogEdgeStack');
  var eb = vis(edge) ? box(edge) : null;
  var edgeHits = [];
  if (eb) {
    document.querySelectorAll('#catalogMain .loc-group > .entry:not(.highlight) details.patches > summary').forEach(function (el) {
      if (!vis(el)) return;
      var b = box(el);
      if (overlap(eb, b)) edgeHits.push({txt: (el.textContent || '').slice(0, 24)});
    });
  }
  return {
    vw: innerWidth, vh: innerHeight,
    portable: !!window.CATALOG_PORTABLE,
    sides: document.body.classList.contains('display-sides'),
    indexWin: document.body.classList.contains('index-window-open'),
    strip: {
      n: stripBtns.length,
      topSpread: spread(stripBtns.map(function (el) { return box(el).t; })),
      hSpread: spread(stripBtns.map(function (el) { return box(el).h; })),
      heights: stripBtns.map(function (el) { return box(el).h; })
    },
    rows: groups,
    jump: { box: jb, hits: jumpHits, nHits: jumpHits.length },
    edge: { box: eb, hits: edgeHits, nHits: edgeHits.length }
  };
})()
"""


def ensure_http():
    url = f"http://127.0.0.1:{HTTP}/DS-CATALOG.html"
    try:
        urllib.request.urlopen(url, timeout=1).read(64)
        return None
    except Exception:
        pass
    os.chdir(ROOT)

    class H(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a):
            pass

    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", HTTP), H)
    httpd.allow_reuse_address = True
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    for _ in range(40):
        try:
            urllib.request.urlopen(url, timeout=1).read(64)
            return httpd
        except Exception:
            time.sleep(0.1)
    raise SystemExit("http 8797 failed")


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


def issues_for(data, tag):
    issues = []
    if data.get("portable"):
        issues.append(f"{tag}:portable-flag")
    st = data.get("strip") or {}
    if st.get("topSpread", 99) > 1.2:
        issues.append(f"{tag}:strip-top:{st.get('topSpread')}")
    if st.get("hSpread", 99) > 1.2:
        issues.append(f"{tag}:strip-h:{st.get('hSpread')}")
    for row in data.get("rows") or []:
        rid = f"{tag}:g{row.get('g')}r{row.get('r')}n{row.get('n')}"
        for k in ("name", "desc", "pathLabel", "icons", "patches", "search", "fav"):
            if row.get(k) is not None and row[k] > 2.0:
                issues.append(f"{rid}:{k}:{row[k]}")
        if row.get("descH") is not None and row["descH"] > 2.0:
            issues.append(f"{rid}:descH:{row['descH']}")
        if row.get("searchFavTop") is not None and row["searchFavTop"] > 2.0:
            issues.append(f"{rid}:searchFavTop:{row['searchFavTop']}")
        if row.get("searchFavH") is not None and row["searchFavH"] > 2.0:
            issues.append(f"{rid}:searchFavH:{row['searchFavH']}")
    jump = data.get("jump") or {}
    if jump.get("nHits"):
        issues.append(f"{tag}:jump-overlap:{jump.get('nHits')}")
    edge = data.get("edge") or {}
    if edge.get("nHits"):
        issues.append(f"{tag}:edge-overlap:{edge.get('nHits')}")
    return issues


def run_file(cdp, filename):
    out = {"file": filename, "issues": [], "shots": []}
    nav(cdp, f"http://127.0.0.1:{HTTP}/{filename}?chromev2b=1")
    set_view(cdp, 1400, 900)
    setup = cdp.eval(SETUP)
    out["setup"] = setup
    time.sleep(0.45)
    cdp.eval("if(typeof equalizeCatalogCardRows==='function')equalizeCatalogCardRows();if(typeof placeCatalogJumpStack==='function')placeCatalogJumpStack();true")
    time.sleep(0.3)
    sides = cdp.eval(PROBE)
    out["sides"] = sides
    out["shots"].append(shot(cdp, f"D1400-{filename}-chrome-v2-g0.png"))
    out["issues"].extend(issues_for(sides, "sides"))

    # later loc-group with more tiles
    cdp.eval(
        "var sc=(typeof catalogContentScroller==='function'&&catalogContentScroller())||document.getElementById('catalogMain');"
        "var gs=document.querySelectorAll('.loc-group');"
        "var g=gs[1]||gs[0];"
        "if(sc&&g){var r=g.getBoundingClientRect(),sr=sc.getBoundingClientRect();sc.scrollTop+=Math.max(0,r.top-sr.top-8);}"
        "if(typeof equalizeCatalogCardRows==='function')equalizeCatalogCardRows();"
        "if(typeof placeCatalogJumpStack==='function')placeCatalogJumpStack();true"
    )
    time.sleep(0.35)
    g2 = cdp.eval(PROBE)
    out["sides_g2"] = {"rows": (g2 or {}).get("rows"), "jump": (g2 or {}).get("jump")}
    out["shots"].append(shot(cdp, f"D1400-{filename}-chrome-v2-g1.png"))
    out["issues"].extend(issues_for(g2, "sides-g1"))

    # mixed A-name region if present
    cdp.eval(
        "var el=document.getElementById('item-49')||document.getElementById('item-53')||document.querySelector('.loc-group:nth-of-type(2) .entry');"
        "var sc=(typeof catalogContentScroller==='function'&&catalogContentScroller())||document.getElementById('catalogMain');"
        "if(sc&&el){var r=el.getBoundingClientRect(),sr=sc.getBoundingClientRect();sc.scrollTop+=Math.max(0,r.top-sr.top-12);}"
        "if(typeof equalizeCatalogCardRows==='function')equalizeCatalogCardRows();"
        "if(typeof placeCatalogJumpStack==='function')placeCatalogJumpStack();true"
    )
    time.sleep(0.35)
    mixed = cdp.eval(PROBE)
    out["mixed"] = mixed
    out["shots"].append(shot(cdp, f"D1400-{filename}-chrome-v2-mixed.png"))
    out["issues"].extend(issues_for(mixed, "mixed"))

    out["pass"] = not out["issues"]
    return out


def main():
    ensure_http()
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
    summary = {
        "ok": payload["ok"],
        "files": [
            {
                "file": r.get("file"),
                "pass": r.get("pass"),
                "issues": r.get("issues"),
                "rowN": [row.get("n") for row in ((r.get("mixed") or r.get("sides") or {}).get("rows") or [])[:6]],
            }
            for r in results
        ],
    }
    print(json.dumps(summary, indent=2))
    if not payload["ok"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
