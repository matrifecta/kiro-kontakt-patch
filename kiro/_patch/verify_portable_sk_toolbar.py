#!/usr/bin/env python3
"""Verify portable Hide/Flip/SK-pair through keyboard-like viewport shrink."""
from __future__ import annotations

import json
import os
import signal
import subprocess
import time
import urllib.request
from pathlib import Path

OUT = Path("/home/phnx/kiro-kontakt-patch/kiro/_patch/verify_portable_sk_toolbar.json")
PORT = 9591
HTTP = 8797
PROFILE = "/tmp/catalog-sk-toolbar"
CHROME = next(
    (
        p
        for p in ("/usr/lib/chromium/chromium", "/usr/bin/chromium", "/usr/bin/google-chrome")
        if os.path.exists(p)
    ),
    "/usr/bin/chromium",
)
os.makedirs(PROFILE, exist_ok=True)

JS = r"""
(() => {
  function vis(el){
    if(!el) return {ok:false};
    var r=el.getBoundingClientRect(), cs=getComputedStyle(el);
    return {
      disp:cs.display, vis:cs.visibility, w:Math.round(r.width), h:Math.round(r.height),
      x:Math.round(r.x), y:Math.round(r.y), gc:cs.gridColumn, gr:cs.gridRow,
      shown: cs.display!=='none' && cs.visibility!=='hidden' && r.width>2 && r.height>2
    };
  }
  var sc=document.getElementById('searchChrome');
  var fw=document.getElementById('filterWrap');
  var cm=document.getElementById('catalogMain');
  var flip=document.getElementById('portraitFlipBtn');
  var hideS=document.querySelector('.search-strip-hide');
  var hideK=document.getElementById('kwStripHide');
  var tog=document.getElementById('filterToggle');
  var sBtn=document.getElementById('hdrSearchBtn');
  var kBtn=document.getElementById('hdrKwBtn');
  var sr=sc&&sc.getBoundingClientRect();
  var kr=fw&&fw.getBoundingClientRect();
  var sideBySide=!!(sr&&kr&&sr.width>40&&kr.width>40&&Math.abs(sr.top-kr.top)<80&&sr.left<kr.left-20);
  return {
    vw:innerWidth, vh:innerHeight,
    o:typeof portableScreenOrient==='function'?portableScreenOrient():null,
    kb:typeof portableKeyboardOpen==='function'?portableKeyboardOpen():null,
    cls:{
      sides:document.body.classList.contains('display-sides'),
      middle:document.body.classList.contains('display-middle'),
      content:document.body.classList.contains('display-content'),
      land:document.body.classList.contains('portable-landscape'),
      port:document.body.classList.contains('portable-portrait'),
      pair:document.body.classList.contains('portable-sk-pair'),
      flipOn:document.body.classList.contains('portable-flip-on'),
      kb:document.body.classList.contains('portable-kb-open'),
      sCol:document.body.classList.contains('search-chrome-collapsed'),
      kCol:document.body.classList.contains('kw-chrome-collapsed'),
      kOpen:document.body.classList.contains('kw-open')
    },
    sOn:sBtn&&sBtn.classList.contains('is-on'),
    kOn:kBtn&&kBtn.classList.contains('is-on'),
    search:vis(sc), kw:vis(fw), main:vis(cm),
    flip:vis(flip), hideS:vis(hideS), hideK:vis(hideK), filterToggle:vis(tog),
    sideBySide:sideBySide
  };
})()
"""


def wait_dbg(timeout=20):
    t0 = time.time()
    while time.time() - t0 < timeout:
        try:
            tabs = json.load(urllib.request.urlopen(f"http://127.0.0.1:{PORT}/json", timeout=1))
        except Exception:
            time.sleep(0.25)
            continue
        pages = [t for t in tabs if t.get("type") == "page"]
        if pages and pages[0].get("webSocketDebuggerUrl"):
            return pages[0]["webSocketDebuggerUrl"]
        time.sleep(0.25)
    raise SystemExit("no debugger url")


def run():
    import threading
    from collections import deque

    import websocket

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
    try:
        ws = websocket.create_connection(wait_dbg(), timeout=20)
        box = {"id": 0}
        pending = {}
        events = deque()

        def send(method, params=None):
            box["id"] += 1
            mid = box["id"]
            payload = {"id": mid, "method": method}
            if params:
                payload["params"] = params
            pending[mid] = {"ev": threading.Event(), "res": None}
            ws.send(json.dumps(payload))
            ok = pending[mid]["ev"].wait(40)
            res = pending[mid]["res"]
            pending.pop(mid, None)
            if not ok:
                raise TimeoutError(method)
            return res

        def reader():
            while True:
                try:
                    raw = ws.recv()
                except Exception:
                    break
                data = json.loads(raw)
                if "id" in data and data["id"] in pending:
                    pending[data["id"]]["res"] = data
                    pending[data["id"]]["ev"].set()
                else:
                    events.append(data)

        threading.Thread(target=reader, daemon=True).start()
        send("Page.enable")
        send("Runtime.enable")
        send("Emulation.setDeviceMetricsOverride", {
            "width": 390, "height": 844, "deviceScaleFactor": 2, "mobile": True,
            "screenOrientation": {"type": "portraitPrimary", "angle": 0},
        })
        send("Page.navigate", {"url": f"http://127.0.0.1:{HTTP}/KONTAKT-CATALOG-portable.html"})
        t0 = time.time()
        loaded = False
        while time.time() - t0 < 40:
            while events:
                ev = events.popleft()
                if ev.get("method") == "Page.loadEventFired":
                    loaded = True
            if loaded:
                break
            time.sleep(0.1)
        time.sleep(1.6)

        def ev(expr):
            res = send("Runtime.evaluate", {"expression": expr, "returnByValue": True})
            return res.get("result", {}).get("result", {}).get("value")

        def snap():
            return ev(JS)

        out = {}
        out["boot_portrait"] = snap()
        ev("toggleHdrSearch();")
        time.sleep(0.4)
        out["port_s"] = snap()
        ev("toggleHdrKw();")
        time.sleep(0.4)
        out["port_sk"] = snap()

        send("Emulation.setDeviceMetricsOverride", {
            "width": 844, "height": 390, "deviceScaleFactor": 2, "mobile": True,
            "screenOrientation": {"type": "landscapePrimary", "angle": 90},
        })
        time.sleep(0.6)
        ev("if(typeof syncPortableLayoutChrome==='function')syncPortableLayoutChrome(); if(typeof applySidesCols==='function')applySidesCols();")
        time.sleep(0.3)
        out["land_after_rotate"] = snap()
        ev("if(document.body.classList.contains('search-chrome-collapsed')&&typeof toggleHdrSearch==='function')toggleHdrSearch(); if(!document.body.classList.contains('kw-open')&&typeof toggleHdrKw==='function')toggleHdrKw(); if(typeof syncHdrMenuBtns==='function')syncHdrMenuBtns();")
        time.sleep(0.4)
        out["land_sk"] = snap()

        # Keyboard-like: CSS portrait viewport, keep screen landscape
        send("Emulation.setDeviceMetricsOverride", {
            "width": 500, "height": 620, "deviceScaleFactor": 2, "mobile": True,
            "screenOrientation": {"type": "landscapePrimary", "angle": 90},
        })
        time.sleep(0.5)
        ev("window.dispatchEvent(new Event('resize')); if(typeof syncPortableLayoutChrome==='function')syncPortableLayoutChrome();")
        time.sleep(0.4)
        out["fake_kb_portrait_css"] = snap()

        send("Emulation.setDeviceMetricsOverride", {
            "width": 844, "height": 390, "deviceScaleFactor": 2, "mobile": True,
            "screenOrientation": {"type": "landscapePrimary", "angle": 90},
        })
        time.sleep(0.4)
        ev("setDisplayMode('content');")
        time.sleep(0.3)
        out["land_content"] = snap()

        # DS portable landscape SK
        send("Emulation.setDeviceMetricsOverride", {
            "width": 844, "height": 390, "deviceScaleFactor": 2, "mobile": True,
            "screenOrientation": {"type": "landscapePrimary", "angle": 90},
        })
        send("Page.navigate", {"url": f"http://127.0.0.1:{HTTP}/DS-CATALOG-portable.html"})
        t0 = time.time()
        loaded = False
        events.clear()
        while time.time() - t0 < 40:
            while events:
                evn = events.popleft()
                if evn.get("method") == "Page.loadEventFired":
                    loaded = True
            if loaded:
                break
            time.sleep(0.1)
        time.sleep(1.8)
        ev("toggleHdrSearch(); toggleHdrKw(); if(typeof syncHdrMenuBtns==='function')syncHdrMenuBtns();")
        time.sleep(0.5)
        out["ds_land_sk"] = snap()

        def ok_hidden(node):
            return not node.get("shown")

        checks = {
            "boot_no_flip": ok_hidden(out["boot_portrait"]["flip"]),
            "boot_no_hide_k": ok_hidden(out["boot_portrait"]["hideK"]) and ok_hidden(out["boot_portrait"]["filterToggle"]),
            "port_s_no_flip": ok_hidden(out["port_s"]["flip"]),
            "port_s_no_hide": ok_hidden(out["port_s"]["hideS"]) and ok_hidden(out["port_s"]["hideK"]),
            "land_sk_pair": bool(out["land_sk"]["cls"]["pair"]) and bool(out["land_sk"]["sideBySide"]),
            "land_sk_both_on": bool(out["land_sk"]["sOn"]) and bool(out["land_sk"]["kOn"]),
            "land_sk_no_main": not out["land_sk"]["main"].get("shown"),
            "land_sk_no_hide": ok_hidden(out["land_sk"]["hideS"]) and ok_hidden(out["land_sk"]["hideK"]) and ok_hidden(out["land_sk"]["filterToggle"]),
            "land_sk_flip": bool(out["land_sk"]["flip"].get("shown")),
            "kb_keeps_pair": bool(out["fake_kb_portrait_css"]["cls"]["pair"]) and bool(out["fake_kb_portrait_css"]["sOn"]) and bool(out["fake_kb_portrait_css"]["kOn"]),
            "kb_side_by_side": bool(out["fake_kb_portrait_css"]["sideBySide"]),
            "content_no_flip": ok_hidden(out["land_content"]["flip"]),
            "ds_sk_pair": bool(out["ds_land_sk"]["cls"]["pair"]) and bool(out["ds_land_sk"]["sideBySide"]),
            "ds_no_hide": ok_hidden(out["ds_land_sk"]["hideK"]) and ok_hidden(out["ds_land_sk"]["filterToggle"]),
        }
        out["checks"] = checks
        out["pass"] = all(checks.values())
        OUT.write_text(json.dumps(out, indent=2), encoding="utf-8")
        print(json.dumps({"pass": out["pass"], "checks": checks}, indent=2))
        if not out["pass"]:
            raise SystemExit(1)
    finally:
        try:
            proc.send_signal(signal.SIGTERM)
            proc.wait(timeout=3)
        except Exception:
            proc.kill()


if __name__ == "__main__":
    run()
