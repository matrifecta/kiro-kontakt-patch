#!/usr/bin/env python3
"""Verify compact jump icons + tighter gutter. No fetch() in Runtime.evaluate."""
from __future__ import annotations

import json
import os
import signal
import subprocess
import time
import urllib.request
from pathlib import Path

OUT = Path("/home/phnx/kiro-kontakt-patch/kiro/_patch/verify_jump_icon_gutter.json")
SHOT = Path("/home/phnx/kiro-kontakt-patch/kiro/_patch/ui-pos-shots")
PORT = 9576
HTTP = 8797
PROFILE = "/tmp/catalog-jump-icon-gutter"
CHROME = "/usr/bin/chromium"
SHOT.mkdir(parents=True, exist_ok=True)
os.makedirs(PROFILE, exist_ok=True)

PROBE = r"""
(() => {
  if (typeof placeCatalogJumpStack === 'function') placeCatalogJumpStack();
  var stack = document.getElementById('catalogJumpStack');
  var main = document.getElementById('catalogMain');
  var sc = (typeof catalogContentScroller === 'function' && catalogContentScroller()) || main;
  var top = stack && stack.querySelector('a.top');
  var bot = stack && stack.querySelector('a.bottom');
  function box(el) {
    if (!el) return null;
    var r = el.getBoundingClientRect();
    var cs = getComputedStyle(el);
    return {
      l: Math.round(r.left), r: Math.round(r.right), t: Math.round(r.top), b: Math.round(r.bottom),
      w: Math.round(r.width), h: Math.round(r.height),
      disp: cs.display, vis: cs.visibility, pe: cs.pointerEvents,
      pad: cs.padding, color: cs.color, bg: cs.backgroundColor
    };
  }
  function ico(el) {
    if (!el) return null;
    var svg = el.querySelector('svg.catalog-jump-ico');
    var poly = svg && svg.querySelector('polygon');
    var rects = svg ? svg.querySelectorAll('rect').length : 0;
    return {
      aria: el.getAttribute('aria-label') || '',
      title: el.getAttribute('title') || '',
      text: String(el.textContent || '').replace(/\s+/g, ' ').trim(),
      hasSvg: !!svg,
      fill: svg ? (svg.getAttribute('fill') || getComputedStyle(svg).fill) : '',
      poly: poly ? (poly.getAttribute('points') || '') : '',
      rects: rects,
      w: svg ? Math.round(svg.getBoundingClientRect().width) : 0,
      h: svg ? Math.round(svg.getBoundingClientRect().height) : 0
    };
  }
  var jr = stack ? stack.getBoundingClientRect() : null;
  var mr = main ? main.getBoundingClientRect() : null;
  var sr = sc ? sc.getBoundingClientRect() : null;
  var tb = box(top), bb = box(bot);
  var sbw = sc ? Math.max(0, (sc.offsetWidth || 0) - (sc.clientWidth || 0)) : 0;
  var gutter = typeof catalogJumpScrollbarGutter === 'function' ? catalogJumpScrollbarGutter(main) : null;
  var gapMain = (jr && mr) ? Math.round(mr.right - jr.right) : null;
  var gapSc = (jr && sr) ? Math.round(sr.right - jr.right) : null;
  var hits = [];
  if (sr && jr) {
    var y = Math.round(jr.top + jr.height / 2);
    [2, 4].forEach(function (d) {
      var x = Math.round(sr.right - d);
      var el = document.elementFromPoint(x, y);
      var a = el && el.closest && el.closest('a.top,a.bottom,#catalogJumpStack');
      hits.push({
        x: x, y: y, d: d,
        tag: el ? ((el.id || el.tagName || '') + '.' + String(el.className || '')).slice(0, 56) : null,
        hitJump: !!a
      });
    });
  }
  return {
    portable: !!window.CATALOG_PORTABLE,
    ns: window.CATALOG_NS,
    vw: innerWidth, vh: innerHeight,
    sides: document.body.classList.contains('display-sides'),
    middle: document.body.classList.contains('display-middle'),
    contentOn: document.body.classList.contains('content-window-on'),
    gutter: gutter, sbw: sbw,
    styleR: stack ? stack.style.right : '',
    jump: box(stack),
    main: mr ? { l: Math.round(mr.left), r: Math.round(mr.right), w: Math.round(mr.width) } : null,
    sc: sr ? { id: sc.id || '', r: Math.round(sr.right), sh: sc.scrollHeight, ch: sc.clientHeight, st: sc.scrollTop } : null,
    top: tb, bot: bb, topIco: ico(top), botIco: ico(bot),
    gapMain: gapMain, gapSc: gapSc,
    hits: hits,
    scrollbarClear: hits.every(function (h) { return !h.hitJump; })
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

    def eval(self, expr):
        r = self.call("Runtime.evaluate", {"expression": expr, "returnByValue": True})
        if r.get("exceptionDetails"):
            raise RuntimeError(r["exceptionDetails"])
        return r.get("result", {}).get("value")


def set_view(cdp, w, h, mobile=False):
    cdp.call(
        "Emulation.setDeviceMetricsOverride",
        {
            "width": w,
            "height": h,
            "deviceScaleFactor": 1,
            "mobile": mobile,
            "screenOrientation": {
                "type": "portraitPrimary" if h >= w else "landscapePrimary",
                "angle": 0 if h >= w else 90,
            },
        },
    )
    time.sleep(0.3)


def wait_ready(cdp):
    for _ in range(80):
        try:
            if cdp.eval("!!(document.getElementById('catalogMain')&&typeof placeCatalogJumpStack==='function')"):
                return
        except Exception:
            pass
        time.sleep(0.2)
    raise SystemExit("catalog not ready")


def nav(cdp, url):
    cdp.call("Page.enable")
    cdp.call("Runtime.enable")
    cdp.call("Page.navigate", {"url": url})
    time.sleep(1.2)
    wait_ready(cdp)
    time.sleep(0.35)


def shot(cdp, name):
    data = cdp.call("Page.captureScreenshot", {"format": "png", "fromSurface": True})
    raw = data.get("data")
    if not raw:
        return None
    import base64

    path = SHOT / name
    path.write_bytes(base64.b64decode(raw))
    return str(path)


def click_jump(cdp, which):
    before = cdp.eval(
        "var sc=(typeof catalogContentScroller==='function'&&catalogContentScroller())||document.getElementById('catalogMain');"
        "sc?{st:sc.scrollTop,sh:sc.scrollHeight,ch:sc.clientHeight}:null"
    )
    cdp.eval(
        f"var a=document.querySelector('#catalogJumpStack a.{which}');"
        "if(a){a.dispatchEvent(new MouseEvent('click',{bubbles:true,cancelable:true}));}"
    )
    time.sleep(0.6)
    after = cdp.eval(
        "var sc=(typeof catalogContentScroller==='function'&&catalogContentScroller())||document.getElementById('catalogMain');"
        "sc?{st:sc.scrollTop,sh:sc.scrollHeight,ch:sc.clientHeight}:null"
    )
    moved = abs((after or {}).get("st", 0) - (before or {}).get("st", 0)) > 8
    return {"before": before, "after": after, "moved": moved, "which": which}


def judge(data, clicks):
    top, bot = data.get("topIco") or {}, data.get("botIco") or {}
    tb, bb = data.get("top") or {}, data.get("bot") or {}
    issues = []
    if not top.get("hasSvg") or not bot.get("hasSvg"):
        issues.append("missing-svg")
    if "top" in (top.get("text") or "").lower() or "bottom" in (bot.get("text") or "").lower():
        issues.append("text-labels")
    if top.get("aria") != "Jump to top" or bot.get("aria") != "Jump to bottom":
        issues.append("aria")
    if (top.get("rects") or 0) < 2 or (bot.get("rects") or 0) < 2 or not top.get("poly") or not bot.get("poly"):
        issues.append("glyph-shape")
    for b in (tb, bb):
        if not b or b.get("w", 0) < 32 or b.get("h", 0) < 32:
            issues.append("tap-too-small")
        if b and (b.get("w", 0) > 52 or b.get("h", 0) > 52):
            issues.append("not-compact")
    gap = data.get("gapMain")
    if gap is None or gap >= 21:
        issues.append(f"gap-not-closer:{gap}")
    if gap is not None and gap < 2:
        issues.append("gap-too-tight")
    if not data.get("scrollbarClear"):
        issues.append("scrollbar-hit-jump")
    if data.get("gutter") is None or data.get("gutter") > 18:
        issues.append(f"gutter:{data.get('gutter')}")
    if not all(c.get("moved") for c in clicks):
        issues.append("scroll-no-move")
    data["issues"] = issues
    data["pass"] = not issues
    return data


HELP_PROBE = r"""
(() => {
  if (typeof openCatalogHelp === 'function') openCatalogHelp('legend');
  var legend = document.getElementById('catalogHelpLegend');
  var user = document.getElementById('catalogHelpUser');
  var card = document.getElementById('catalogHelpCard');
  var lg = document.getElementById('catalogLegendBtn');
  var gd = document.getElementById('catalogGuideBtn');
  var note = document.getElementById('catalogDocNote');
  function box(el){
    if(!el)return null;
    var r=el.getBoundingClientRect();
    return {l:Math.round(r.left),r:Math.round(r.right),t:Math.round(r.top),b:Math.round(r.bottom),w:Math.round(r.width),h:Math.round(r.height),hidden:!!el.hidden};
  }
  var lt = legend ? (legend.innerText || '') : '';
  var needles = [
    'Skip to top / bottom',
    'no expandable path field',
    'transparent UI',
    'portrait-only',
    'content-only',
    'max 12'
  ];
  var missing = needles.filter(function(n){ return lt.indexOf(n) < 0; });
  var stale = [];
  if (/↑ top|↓ bottom/.test(lt)) stale.push('arrow-text');
  if (/expand or collapse the folder text/.test(lt)) stale.push('old-path-field');
  var nr = box(note), lr = box(lg), gr = box(gd);
  function ov(a,b){
    if(!a||!b||a.w<2||b.w<2)return false;
    return !(a.r<b.l+2||a.l>b.r-2||a.b<b.t+2||a.t>b.b-2);
  }
  if (typeof openCatalogHelp === 'function') openCatalogHelp('guide');
  var ut = user ? (user.innerText || '') : '';
  return {
    helpOpen: document.body.classList.contains('catalog-help-open') || document.body.classList.contains('catalog-help-fs'),
    kind: window._catalogHelpKind || '',
    cardHidden: !!(card && card.hidden),
    legendHidden: !!(legend && legend.hidden),
    userHidden: !!(user && user.hidden),
    missing: missing,
    stale: stale,
    userHasPathIcons: ut.indexOf('three icons') >= 0,
    overlayAbout: ov(lr, nr) || ov(gr, nr),
    edge: {legend: lr, guide: gr, note: nr}
  };
})()
"""


def run_file(cdp, name, url, w, h, mobile, mode="sides"):
    nav(cdp, url)
    set_view(cdp, w, h, mobile=mobile)
    cdp.eval(
        f"if(typeof setDisplayMode==='function')setDisplayMode('{mode}',{{pick:true}});"
        "document.body.classList.remove('search-chrome-collapsed','kw-chrome-collapsed');"
        "if(typeof placeCatalogJumpStack==='function')placeCatalogJumpStack();"
    )
    time.sleep(0.45)
    data = cdp.eval(PROBE)
    shot_path = shot(cdp, f"D{w}-{name}-jump-icons.png")
    bot_click = click_jump(cdp, "bottom")
    top_click = click_jump(cdp, "top")
    help = cdp.eval(HELP_PROBE)
    time.sleep(0.25)
    help_shot = shot(cdp, f"D{w}-{name}-legend-guide.png")
    cdp.eval("if(typeof closeCatalogHelp==='function')closeCatalogHelp();")
    data["file"] = name
    data["mode"] = mode
    data["shot"] = shot_path
    data["helpShot"] = help_shot
    data["clicks"] = [bot_click, top_click]
    data["help"] = help
    judged = judge(data, [bot_click, top_click])
    if help:
        if help.get("missing"):
            judged["issues"].append("help-missing:" + ",".join(help["missing"]))
        if help.get("stale"):
            judged["issues"].append("help-stale:" + ",".join(help["stale"]))
        if not help.get("helpOpen"):
            judged["issues"].append("help-not-open")
        if help.get("overlayAbout"):
            judged["issues"].append("edge-over-about")
        judged["pass"] = not judged["issues"]
    return judged


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
        results.append(
            run_file(cdp, "KONTAKT-CATALOG.html", f"http://127.0.0.1:{HTTP}/KONTAKT-CATALOG.html?jumpico=1", 1400, 900, False)
        )
        results.append(
            run_file(
                cdp,
                "KONTAKT-CATALOG-portable.html",
                f"http://127.0.0.1:{HTTP}/KONTAKT-CATALOG-portable.html?jumpico=1",
                390,
                844,
                True,
            )
        )
        results.append(
            run_file(cdp, "DS-CATALOG.html", f"http://127.0.0.1:{HTTP}/DS-CATALOG.html?jumpico=1", 1400, 900, False)
        )
    finally:
        try:
            proc.send_signal(signal.SIGTERM)
            proc.wait(timeout=3)
        except Exception:
            proc.kill()
    payload = {"ok": all(r.get("pass") for r in results), "results": results}
    OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(payload, indent=2))
    if not payload["ok"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
