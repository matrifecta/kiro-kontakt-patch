#!/usr/bin/env python3
"""Verify desktop Sides Keywords nest. No fetch() in Runtime.evaluate."""
from __future__ import annotations

import json
import os
import signal
import subprocess
import time
import urllib.request
from pathlib import Path

OUT = Path("/home/phnx/kiro-kontakt-patch/kiro/_patch/verify_sides_kw_nest.json")
SHOT = Path("/home/phnx/kiro-kontakt-patch/kiro/_patch/ui-pos-shots")
PORT = 9588
HTTP = 8797
PROFILE = "/tmp/catalog-sides-kw-nest"
CHROME = next(
    (
        p
        for p in ("/usr/lib/chromium/chromium", "/usr/bin/chromium", "/usr/bin/google-chrome")
        if os.path.exists(p)
    ),
    "/usr/bin/chromium",
)
SHOT.mkdir(parents=True, exist_ok=True)
os.makedirs(PROFILE, exist_ok=True)

GEO = r"""
(() => {
  function box(el){
    if(!el) return null;
    var r=el.getBoundingClientRect(), cs=getComputedStyle(el);
    return {
      x:Math.round(r.x), y:Math.round(r.y), w:Math.round(r.width), h:Math.round(r.height),
      t:Math.round(r.top), b:Math.round(r.bottom), l:Math.round(r.left), rgt:Math.round(r.right),
      disp:cs.display, vis:cs.visibility, gc:cs.gridColumn, gr:cs.gridRow
    };
  }
  var sc=document.getElementById('searchChrome');
  var fw=document.getElementById('filterWrap');
  var cm=document.getElementById('catalogMain');
  var ix=document.getElementById('catalogIndex');
  var split=document.getElementById('searchSplit');
  var sep=document.getElementById('dualFsSep');
  var jump=document.getElementById('catalogJumpStack');
  var bcs=getComputedStyle(document.body);
  var sameCol = !!(sc && fw && Math.abs(sc.getBoundingClientRect().left - fw.getBoundingClientRect().left) < 24
    && Math.abs(sc.getBoundingClientRect().width - fw.getBoundingClientRect().width) < 48);
  var searchAbove = !!(sc && fw && sc.getBoundingClientRect().bottom <= fw.getBoundingClientRect().top + 12);
  var contentOther = false;
  if(sc && cm){
    var sr=sc.getBoundingClientRect(), mr=cm.getBoundingClientRect();
    contentOther = (mr.left >= sr.right - 8) || (sr.left >= mr.right - 8);
  }
  return {
    vw:innerWidth, vh:innerHeight,
    sides:document.body.classList.contains('display-sides'),
    middle:document.body.classList.contains('display-middle'),
    nested:document.body.classList.contains('kw-nested-search'),
    kwHid:document.body.classList.contains('kw-chrome-collapsed'),
    sOn:!document.body.classList.contains('search-chrome-collapsed'),
    kwOpen:document.body.classList.contains('kw-open'),
    flip:document.body.classList.contains('sides-portrait-flip'),
    land:document.body.classList.contains('desk-landscape'),
    edit:document.body.classList.contains('layout-edit'),
    canNest:typeof sidesKwCanNest==='function'?sidesKwCanNest():null,
    cols:bcs.gridTemplateColumns, rows:bcs.gridTemplateRows,
    nh:(getComputedStyle(document.documentElement).getPropertyValue('--sides-nested-h')||'').trim(),
    search:box(sc), kw:box(fw), main:box(cm), ix:box(ix), split:box(split), sep:box(sep), jump:box(jump),
    sameCol:sameCol, searchAbove:searchAbove, contentOther:contentOther,
    kwVisible:!!(fw && getComputedStyle(fw).display!=='none' && fw.getBoundingClientRect().height>8),
    searchVisible:!!(sc && getComputedStyle(sc).display!=='none' && sc.getBoundingClientRect().width>8)
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
    time.sleep(0.35)


def wait_ready(cdp):
    for _ in range(80):
        try:
            if cdp.eval("!!(document.getElementById('catalogMain')&&typeof applySidesCols==='function')"):
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


def three_col(cdp):
    return cdp.eval(
        """
(() => {
  if(typeof setDisplayMode==='function') setDisplayMode('sides');
  document.body.classList.remove('display-middle','kw-nested-search');
  if(typeof collapseSearchMenu==='function') collapseSearchMenu();
  if(typeof expandKwMenu==='function') expandKwMenu();
  if(typeof expandSearchMenu==='function') expandSearchMenu();
  document.body.classList.remove('kw-nested-search');
  if(typeof applySidesCols==='function') applySidesCols();
  return true;
})()
"""
    )


def search_on_kw_off(cdp):
    return cdp.eval(
        """
(() => {
  if(typeof setDisplayMode==='function') setDisplayMode('sides');
  document.body.classList.remove('display-middle','kw-nested-search');
  if(typeof expandSearchMenu==='function') expandSearchMenu();
  if(typeof collapseKwMenu==='function') collapseKwMenu();
  if(typeof applySidesCols==='function') applySidesCols();
  return true;
})()
"""
    )


def click_filter(cdp):
    return cdp.eval(
        "document.getElementById('filterToggle')&&document.getElementById('filterToggle').click();true"
    )


def click_hdr_k(cdp):
    return cdp.eval(
        "document.getElementById('hdrKwBtn')&&document.getElementById('hdrKwBtn').click();true"
    )


def three_pane_ok(geo):
    return (
        geo.get("sOn")
        and geo.get("kwVisible")
        and not geo.get("kwHid")
        and not geo.get("nested")
        and not geo.get("sameCol")
        and geo.get("searchVisible")
    )


def run_file(cdp, filename, tag):
    errors = []
    out = {"file": filename, "errors": errors, "shots": []}
    nav(cdp, f"http://127.0.0.1:{HTTP}/{filename}?kwnest=1")
    set_view(cdp, 1400, 900)
    if cdp.eval("typeof applySidesCols==='function'&&applySidesCols();true"):
        pass
    search_on_kw_off(cdp)
    time.sleep(0.35)
    before_k = cdp.eval(GEO)
    out["before_hdr_k"] = before_k
    if not before_k.get("sOn") or before_k.get("kwVisible"):
        errors.append("pre-hdr-k-not-search-only")
    click_hdr_k(cdp)
    time.sleep(0.45)
    start = cdp.eval(GEO)
    out["start"] = start
    out["shots"].append(shot(cdp, f"D1400-{tag}-sides-3col.png"))
    if not start.get("sides") or start.get("middle"):
        errors.append("not-sides")
    if start.get("nested"):
        errors.append("hdr-k-opened-nested")
    if not start.get("sOn") or not start.get("kwVisible"):
        errors.append("hdr-k-menus-off")
    if start.get("sameCol"):
        errors.append("hdr-k-stacked-under-search")
    if not start.get("land"):
        errors.append("not-landscape")
    if not three_pane_ok(start):
        errors.append("hdr-k-not-3pane")

    click_filter(cdp)
    time.sleep(0.45)
    nested = cdp.eval(GEO)
    out["nested"] = nested
    out["shots"].append(shot(cdp, f"D1400-{tag}-kw-nested.png"))
    if not nested.get("nested"):
        errors.append("nest-class-missing")
    if nested.get("kwHid"):
        errors.append("nest-hid-too-soon")
    if not nested.get("sameCol"):
        errors.append("nest-not-same-column")
    if not nested.get("searchAbove"):
        errors.append("nest-search-not-above-kw")
    if not nested.get("contentOther"):
        errors.append("nest-content-not-other-column")
    if not nested.get("searchVisible") or not nested.get("kwVisible"):
        errors.append("nest-pane-missing")

    flip_before = {
        "searchL": (nested.get("search") or {}).get("l"),
        "kwL": (nested.get("kw") or {}).get("l"),
        "mainL": (nested.get("main") or {}).get("l"),
    }
    cdp.eval("if(typeof togglePortraitSidesFlip==='function')togglePortraitSidesFlip();")
    time.sleep(0.4)
    flipped = cdp.eval(GEO)
    out["flipped"] = flipped
    out["shots"].append(shot(cdp, f"D1400-{tag}-kw-nested-flip.png"))
    if not flipped.get("nested"):
        errors.append("flip-unstacked")
    if not flipped.get("sameCol") or not flipped.get("searchAbove"):
        errors.append("flip-not-stacked")
    sl0, sl1 = flip_before["searchL"], (flipped.get("search") or {}).get("l")
    ml0, ml1 = flip_before["mainL"], (flipped.get("main") or {}).get("l")
    if sl0 is not None and sl1 is not None and abs(sl1 - sl0) < 40:
        errors.append("flip-menus-did-not-move")
    if flipped.get("sameCol") and sl1 is not None and ml1 is not None:
        if not ((ml1 >= (flipped.get("search") or {}).get("rgt", 0) - 8) or (sl1 >= (flipped.get("main") or {}).get("rgt", 0) - 8)):
            errors.append("flip-content-not-opposite")
    cdp.eval("if(typeof togglePortraitSidesFlip==='function')togglePortraitSidesFlip();")
    time.sleep(0.25)

    cdp.eval("if(typeof toggleLayoutEdit==='function')toggleLayoutEdit(); if(typeof placeSidesHandles==='function')placeSidesHandles();")
    time.sleep(0.3)
    before_h = cdp.eval(GEO)
    out["edit_before"] = before_h
    drag = cdp.eval(
        """
(() => {
  var split=document.getElementById('searchSplit');
  if(!split) return {ok:false, reason:'no-split'};
  var r=split.getBoundingClientRect();
  var x=Math.round(r.left+r.width/2), y=Math.round(r.top+r.height/2);
  var h0=document.getElementById('searchChrome').getBoundingClientRect().height;
  split.dispatchEvent(new PointerEvent('pointerdown',{bubbles:true,cancelable:true,pointerId:1,pointerType:'mouse',button:0,clientX:x,clientY:y}));
  document.dispatchEvent(new PointerEvent('pointermove',{bubbles:true,cancelable:true,pointerId:1,pointerType:'mouse',button:0,clientX:x,clientY:y+70}));
  document.dispatchEvent(new PointerEvent('pointerup',{bubbles:true,cancelable:true,pointerId:1,pointerType:'mouse',button:0,clientX:x,clientY:y+70}));
  var h1=document.getElementById('searchChrome').getBoundingClientRect().height;
  return {ok:true, x:x, y:y, h0:Math.round(h0), h1:Math.round(h1), splitDisp:getComputedStyle(split).display, splitH:Math.round(r.height), cursor:getComputedStyle(split).cursor};
})()
"""
    )
    time.sleep(0.25)
    after_h = cdp.eval(GEO)
    out["drag"] = drag
    out["edit_after"] = after_h
    out["shots"].append(shot(cdp, f"D1400-{tag}-kw-nested-drag.png"))
    if not drag or not drag.get("ok"):
        errors.append("drag-no-split")
    else:
        if abs((drag.get("h1") or 0) - (drag.get("h0") or 0)) < 8:
            errors.append(f"drag-height-unchanged:{drag}")
    cdp.eval("if(document.body.classList.contains('layout-edit')&&typeof toggleLayoutEdit==='function')toggleLayoutEdit();")

    click_filter(cdp)
    time.sleep(0.4)
    unnested = cdp.eval(GEO)
    out["unnested"] = unnested
    out["shots"].append(shot(cdp, f"D1400-{tag}-kw-unnested.png"))
    if unnested.get("nested"):
        errors.append("second-arrow-still-nested")
    if unnested.get("kwHid") or not unnested.get("kwVisible"):
        errors.append("second-arrow-hid-kw")
    if unnested.get("sameCol"):
        errors.append("second-arrow-still-stacked")
    if not three_pane_ok(unnested):
        errors.append("second-arrow-not-3pane")
    if not unnested.get("searchVisible") or not unnested.get("sOn"):
        errors.append("unnest-lost-search")

    click_hdr_k(cdp)
    time.sleep(0.4)
    hid = cdp.eval(GEO)
    out["hidden"] = hid
    out["shots"].append(shot(cdp, f"D1400-{tag}-kw-hidden.png"))
    if not hid.get("kwHid") and hid.get("kwVisible"):
        errors.append("hdr-k-off-did-not-hide")
    if hid.get("nested"):
        errors.append("hidden-still-nested")
    if not hid.get("searchVisible") or not hid.get("sOn"):
        errors.append("hidden-lost-search")
    if hid.get("kwVisible"):
        errors.append("hidden-kw-still-visible")

    cdp.eval("if(typeof expandKwMenu==='function')expandKwMenu();")
    time.sleep(0.35)
    restored = cdp.eval(GEO)
    out["restored"] = restored
    if restored.get("nested"):
        errors.append("hdr-restore-nested")
    if not three_pane_ok(restored):
        errors.append("hdr-restore-not-3pane")

    help_txt = cdp.eval(
        """
(() => {
  var lg=document.getElementById('catalogHelpLegend');
  var ug=document.getElementById('catalogHelpUser');
  var t=((lg&&lg.textContent)||'')+' '+((ug&&ug.textContent)||'');
  return {
    nestToggle:t.indexOf('nest under Search')>=0,
    noHide:t.indexOf('that arrow does not hide Keywords')>=0,
    portraitOld:t.indexOf('one-step hide/show')>=0,
    hdrK:t.indexOf('opens Keywords as its own')>=0
  };
})()
"""
    )
    out["help"] = help_txt
    if not help_txt or not help_txt.get("nestToggle") or not help_txt.get("noHide"):
        errors.append("help-missing-landscape-nest")
    if not help_txt or not help_txt.get("portraitOld"):
        errors.append("help-missing-portrait-onestep")
    if not help_txt or not help_txt.get("hdrK"):
        errors.append("help-missing-hdr-k-own-column")

    jump = cdp.eval(
        """
(() => {
  if(typeof placeCatalogJumpStack==='function') placeCatalogJumpStack();
  var stack=document.getElementById('catalogJumpStack');
  var top=stack&&stack.querySelector('a.top');
  var bot=stack&&stack.querySelector('a.bottom');
  var ix=document.getElementById('catalogIndex');
  var vis=!!(stack && getComputedStyle(stack).display!=='none' && stack.getBoundingClientRect().width>8);
  var ixOk=!!(ix && getComputedStyle(ix).display!=='none');
  return {jump:vis, top:!!top, bot:!!bot, ix:ixOk, ixCollapsed:!!(ix&&ix.classList.contains('is-collapsed'))};
})()
"""
    )
    out["jump"] = jump
    if not jump or not jump.get("jump") or not jump.get("top") or not jump.get("bot"):
        errors.append("jump-missing")
    if not jump or not jump.get("ix"):
        errors.append("index-missing")

    set_view(cdp, 900, 1400)
    cdp.eval("if(typeof applySidesCols==='function')applySidesCols();")
    time.sleep(0.4)
    three_col(cdp)
    time.sleep(0.3)
    port = cdp.eval(GEO)
    click_filter(cdp)
    time.sleep(0.35)
    port2 = cdp.eval(GEO)
    out["portrait_before"] = port
    out["portrait_after"] = port2
    out["shots"].append(shot(cdp, f"D1400-{tag}-portrait-kw.png"))
    if port.get("land"):
        errors.append("portrait-still-landscape")
    if port.get("canNest"):
        errors.append("portrait-can-nest")
    if port2.get("nested") and not port2.get("kwHid"):
        errors.append("portrait-used-nest-toggle")
    if port.get("sOn") and port.get("kwVisible") and not port2.get("kwHid") and port2.get("kwVisible"):
        errors.append("portrait-collapse-did-not-hide")
    if port.get("kwVisible") and port2.get("nested") and port2.get("kwVisible") and not port2.get("kwHid"):
        errors.append("portrait-arrow-nested-instead-of-hide")

    set_view(cdp, 1400, 900)
    cdp.eval("if(typeof applySidesCols==='function')applySidesCols();")
    out["ok"] = not errors
    return out


def main():
    subprocess.run(["pkill", "-f", f"remote-debugging-port={PORT}"], check=False)
    time.sleep(0.2)
    proc = subprocess.Popen(
        [
            CHROME,
            "--headless=new",
            "--disable-gpu",
            "--no-sandbox",
            f"--remote-debugging-port={PORT}",
            "--remote-allow-origins=*",
            f"--user-data-dir={PROFILE}",
            "--window-size=1400,900",
            "about:blank",
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    results = {"ok": True, "files": [], "errors": []}
    try:
        page = wait_dbg()
        cdp = CDP(page["webSocketDebuggerUrl"])
        for filename, tag in (("KONTAKT-CATALOG.html", "KONTAKT"), ("DS-CATALOG.html", "DS")):
            one = run_file(cdp, filename, tag)
            results["files"].append(one)
            if not one.get("ok"):
                results["ok"] = False
                results["errors"].extend([f"{tag}:{e}" for e in one.get("errors") or []])
    finally:
        try:
            os.kill(proc.pid, signal.SIGTERM)
        except Exception:
            pass
    OUT.write_text(json.dumps(results, indent=2))
    print(json.dumps({"ok": results["ok"], "errors": results["errors"]}, indent=2))
    if not results["ok"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
