#!/usr/bin/env python3
"""Cold-boot CDP timings for portable (and desktop) catalogs.

Measures loadEvent, navigation timing, script/style size, console errors,
debug ingest to :7529, and boot counts of layout functions.
"""
from __future__ import annotations

import json
import os
import signal
import subprocess
import threading
import time
from collections import deque
from pathlib import Path

OUT = Path("/home/phnx/kiro-kontakt-patch/kiro/_patch/verify_catalog_boot.json")
HTTP = 8797
PORT = 9641
PROFILE = "/tmp/catalog-boot-speed"
CHROME = next(
    (
        p
        for p in ("/usr/lib/chromium/chromium", "/usr/bin/chromium", "/usr/bin/google-chrome")
        if os.path.exists(p)
    ),
    "/usr/bin/chromium",
)
CATALOGS = Path("/home/phnx/kiro-kontakt-patch/public/catalogs")
FILES = [
    "KONTAKT-CATALOG-portable.html",
    "DS-CATALOG-portable.html",
    "KONTAKT-CATALOG.html",
    "DS-CATALOG.html",
]
WRAPS = [
    ("function syncPortableLayoutChrome(){", "syncPortableLayoutChrome"),
    ("function portableRelayoutChrome(reason,fromRaf){", "portableRelayoutChrome"),
    ("function placePortableHandles(){", "placePortableHandles"),
    ("function applySidesCols(){", "applySidesCols"),
    ("function setDisplayMode(mode,opts){", "setDisplayMode"),
]

INJECT_HEAD = r"""
(function(){
  window.__bc={syncPortableLayoutChrome:0,portableRelayoutChrome:0,placePortableHandles:0,applySidesCols:0,setDisplayMode:0,fetch7529:0,fetch7529_3s:0};
  window.__bcT0=Date.now();
  var _f=window.fetch;
  if(_f&&!_f.__bcWrap){
    window.fetch=function(u,o){
      try{
        var s=(typeof u==='string')?u:(u&&u.url)||'';
        if(s.indexOf('127.0.0.1:7529')>=0){
          window.__bc.fetch7529++;
          if(Date.now()-(window.__bcT0||0)<3000)window.__bc.fetch7529_3s++;
        }
      }catch(eF){}
      return _f.apply(this,arguments);
    };
    window.fetch.__bcWrap=true;
  }
})();
"""

SNAP = r"""
(function(){
  var nav=(performance.getEntriesByType&&performance.getEntriesByType('navigation')[0])||null;
  var scripts=document.scripts?document.scripts.length:0;
  var inlineJs=0, inlineCss=0;
  try{
    [].forEach.call(document.scripts||[],function(s){inlineJs+=(s.textContent||'').length;});
  }catch(e1){}
  try{
    [].forEach.call(document.querySelectorAll('style')||[],function(s){inlineCss+=(s.textContent||'').length;});
  }catch(e2){}
  var t=performance.timing||{};
  return {
    ready:document.readyState,
    portable:!!window.CATALOG_PORTABLE,
    ns:String(window.CATALOG_NS||''),
    bodyCls:(document.body&&document.body.className)||'',
    content:!!(document.body&&document.body.classList.contains('display-content')),
    sides:!!(document.body&&document.body.classList.contains('display-sides')),
    searchCol:!!(document.body&&document.body.classList.contains('search-chrome-collapsed')),
    kwCol:!!(document.body&&document.body.classList.contains('kw-chrome-collapsed')),
    hideGone:!(document.body&&/hide/i.test(document.body.innerText||'')&&false),
    vw:innerWidth, vh:innerHeight,
    scripts:scripts,
    inlineJs:inlineJs,
    inlineCss:inlineCss,
    bc:window.__bc||null,
    nav:nav?{
      startTime:nav.startTime,
      fetchStart:nav.fetchStart,
      responseEnd:nav.responseEnd,
      domInteractive:nav.domInteractive,
      domContentLoadedEventStart:nav.domContentLoadedEventStart,
      domContentLoadedEventEnd:nav.domContentLoadedEventEnd,
      loadEventStart:nav.loadEventStart,
      loadEventEnd:nav.loadEventEnd,
      duration:nav.duration,
      transferSize:nav.transferSize,
      encodedBodySize:nav.encodedBodySize,
      decodedBodySize:nav.decodedBodySize
    }:null,
    timing:{
      navigationStart:t.navigationStart||0,
      responseEnd:t.responseEnd?t.responseEnd-t.navigationStart:null,
      domContentLoaded:t.domContentLoadedEventEnd?t.domContentLoadedEventEnd-t.navigationStart:null,
      loadEventEnd:t.loadEventEnd?t.loadEventEnd-t.navigationStart:null,
      domInteractive:t.domInteractive?t.domInteractive-t.navigationStart:null
    }
  };
})()
"""


def wait_dbg(timeout=25):
    import urllib.request

    t0 = time.time()
    while time.time() - t0 < timeout:
        try:
            tabs = json.load(urllib.request.urlopen(f"http://127.0.0.1:{PORT}/json", timeout=1))
        except Exception:
            time.sleep(0.2)
            continue
        pages = [t for t in tabs if t.get("type") == "page"]
        if pages and pages[0].get("webSocketDebuggerUrl"):
            return pages[0]["webSocketDebuggerUrl"]
        time.sleep(0.2)
    raise SystemExit("no debugger url")


def inject_wraps(html: str) -> str:
    out = html
    marker = "var CATALOG_PORTABLE=true;window.CATALOG_PORTABLE=true;"
    if marker in out:
        out = out.replace(marker, marker + INJECT_HEAD, 1)
    else:
        # desktop: inject at first <script>
        out = out.replace("<script>", "<script>" + INJECT_HEAD, 1)
    for sig, name in WRAPS:
        if sig in out:
            bump = (
                sig
                + f"try{{window.__bc=window.__bc||{{}};window.__bc.{name}=(window.__bc.{name}||0)+1;}}catch(_bc){{}}"
            )
            out = out.replace(sig, bump, 1)
    return out


def run_file(send, events, name: str, inject_state: dict, inject_lock: threading.Lock) -> dict:
    path = CATALOGS / name
    size = path.stat().st_size
    raw = path.read_text(encoding="utf-8")
    injected = inject_wraps(raw)
    url = f"http://127.0.0.1:{HTTP}/{name}?boot={int(time.time()*1000)}"

    console = []
    net7529 = []
    load_ms = None
    t_nav = time.time()
    send("Network.enable")
    send("Runtime.enable")
    send("Page.enable")
    send("Performance.enable")
    with inject_lock:
        inject_state["name"] = name
        inject_state["body"] = injected.encode("utf-8")
        inject_state["done"] = False
    send("Fetch.enable", {"patterns": [{"urlPattern": f"*{name}*", "requestStage": "Response"}]})

    send("Emulation.setDeviceMetricsOverride", {
        "width": 844,
        "height": 390,
        "deviceScaleFactor": 2,
        "mobile": True,
        "screenWidth": 844,
        "screenHeight": 390,
        "screenOrientation": {"type": "landscapePrimary", "angle": 90},
    })

    send("Page.navigate", {"url": url})
    t0 = time.time()
    load_ts = None
    while time.time() - t0 < 90:
        while events:
            ev = events.popleft()
            method = ev.get("method")
            params = ev.get("params") or {}
            if method == "Page.loadEventFired":
                load_ts = time.time()
                load_ms = (load_ts - t_nav) * 1000
            elif method == "Runtime.consoleAPICalled":
                if load_ts is None or (time.time() - t_nav) < 2.2:
                    typ = params.get("type")
                    if typ in ("error", "warning"):
                        args = params.get("args") or []
                        txt = " ".join(str((a.get("value") if isinstance(a, dict) else a) or "") for a in args)[:240]
                        console.append({"type": typ, "text": txt, "t": round((time.time() - t_nav) * 1000)})
            elif method == "Runtime.exceptionThrown":
                if load_ts is None or (time.time() - t_nav) < 2.2:
                    desc = ((params.get("exceptionDetails") or {}).get("text") or "")[:240]
                    console.append({"type": "exception", "text": desc, "t": round((time.time() - t_nav) * 1000)})
            elif method == "Network.requestWillBeSent":
                u = ((params.get("request") or {}).get("url") or "")
                if "127.0.0.1:7529" in u:
                    net7529.append(round((time.time() - t_nav) * 1000))
        if load_ts and (time.time() - load_ts) > 3.05:
            break
        time.sleep(0.03)

    try:
        send("Fetch.disable")
    except Exception:
        pass
    with inject_lock:
        fulfilled = bool(inject_state.get("done"))
        inject_state["name"] = None
        inject_state["body"] = None

    snap = send("Runtime.evaluate", {"expression": SNAP, "returnByValue": True, "awaitPromise": False})
    val = ((snap or {}).get("result") or {}).get("result") or {}
    val = val.get("value") if isinstance(val, dict) else None

    first3 = [ms for ms in net7529 if ms <= 3000]
    return {
        "file": name,
        "diskBytes": size,
        "endswithHtml": raw.rstrip().endswith("</html>"),
        "c00e3e": raw.count("sessionId:'c00e3e'"),
        "ingestUrls": raw.count("127.0.0.1:7529"),
        "loadEventFiredMs": round(load_ms, 1) if load_ms is not None else None,
        "nav": (val or {}).get("nav") if isinstance(val, dict) else None,
        "timing": (val or {}).get("timing") if isinstance(val, dict) else None,
        "scripts": (val or {}).get("scripts") if isinstance(val, dict) else None,
        "inlineJs": (val or {}).get("inlineJs") if isinstance(val, dict) else None,
        "inlineCss": (val or {}).get("inlineCss") if isinstance(val, dict) else None,
        "bodyCls": (val or {}).get("bodyCls") if isinstance(val, dict) else None,
        "content": (val or {}).get("content") if isinstance(val, dict) else None,
        "bc": (val or {}).get("bc") if isinstance(val, dict) else None,
        "console2s": console[:40],
        "console2sN": len(console),
        "net7529_3s": len(first3),
        "net7529_all": len(net7529),
        "fulfilled": fulfilled,
        "snapOk": isinstance(val, dict),
        "rawSnapType": type(val).__name__,
    }


def eval_value(send, expr):
    msg = send("Runtime.evaluate", {"expression": expr, "returnByValue": True})
    return (((msg or {}).get("result") or {}).get("result") or {}).get("value")


def run():
    import urllib.request
    import websocket

    urllib.request.urlopen("http://127.0.0.1:8797/KONTAKT-CATALOG-portable.html", timeout=3).read(64)
    os.makedirs(PROFILE, exist_ok=True)
    proc = subprocess.Popen(
        [
            CHROME,
            "--headless=new",
            "--disable-gpu",
            "--no-sandbox",
            f"--remote-debugging-port={PORT}",
            "--remote-allow-origins=*",
            f"--user-data-dir={PROFILE}",
            "--disable-http-cache",
            "--disable-background-networking",
            "about:blank",
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        ws = websocket.create_connection(wait_dbg(), timeout=30)
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
            ok = pending[mid]["ev"].wait(90)
            res = pending[mid]["res"]
            pending.pop(mid, None)
            if not ok:
                raise TimeoutError(method)
            return res

        inject_lock = threading.Lock()
        inject_state = {"name": None, "body": None, "done": False}

        def pump():
            import base64

            while True:
                try:
                    raw = ws.recv()
                except Exception:
                    break
                msg = json.loads(raw)
                if "id" in msg and msg["id"] in pending:
                    pending[msg["id"]]["res"] = msg
                    pending[msg["id"]]["ev"].set()
                    continue
                if msg.get("method") == "Fetch.requestPaused":
                    params = msg.get("params") or {}
                    rid = params.get("requestId")
                    req_url = ((params.get("request") or {}).get("url") or "")
                    with inject_lock:
                        name = inject_state.get("name")
                        body = inject_state.get("body")
                    box["id"] += 1
                    mid = box["id"]
                    pending[mid] = {"ev": threading.Event(), "res": None}
                    if name and body is not None and name in req_url:
                        ws.send(json.dumps({
                            "id": mid,
                            "method": "Fetch.fulfillRequest",
                            "params": {
                                "requestId": rid,
                                "responseCode": 200,
                                "responseHeaders": [
                                    {"name": "Content-Type", "value": "text/html; charset=utf-8"},
                                    {"name": "Cache-Control", "value": "no-store"},
                                ],
                                "body": base64.b64encode(body).decode("ascii"),
                            },
                        }))
                        with inject_lock:
                            inject_state["done"] = True
                    else:
                        ws.send(json.dumps({
                            "id": mid,
                            "method": "Fetch.continueRequest",
                            "params": {"requestId": rid},
                        }))
                    continue
                events.append(msg)

        threading.Thread(target=pump, daemon=True).start()
        send("Page.addScriptToEvaluateOnNewDocument", {"source": INJECT_HEAD})
        rows = []
        for name in FILES:
            events.clear()
            print(f"measuring {name}...", flush=True)
            try:
                row = run_file(send, events, name, inject_state, inject_lock)
            except Exception as e:
                row = {"file": name, "error": str(e)}
            # re-eval snap with helper if needed
            if row.get("snapOk") is False or row.get("bc") is None:
                try:
                    row["bc"] = eval_value(send, "window.__bc||null")
                    row["timing"] = eval_value(
                        send,
                        "({navigationStart:performance.timing.navigationStart,responseEnd:performance.timing.responseEnd-performance.timing.navigationStart,domContentLoaded:performance.timing.domContentLoadedEventEnd-performance.timing.navigationStart,loadEventEnd:performance.timing.loadEventEnd-performance.timing.navigationStart})",
                    )
                    row["nav"] = eval_value(
                        send,
                        "(function(){var n=performance.getEntriesByType('navigation')[0];if(!n)return null;return {responseEnd:n.responseEnd,domContentLoadedEventEnd:n.domContentLoadedEventEnd,loadEventEnd:n.loadEventEnd,duration:n.duration,encodedBodySize:n.encodedBodySize};})()",
                    )
                    row["scripts"] = eval_value(send, "document.scripts.length")
                    row["inlineCss"] = eval_value(
                        send,
                        "[].reduce.call(document.querySelectorAll('style'),function(a,s){return a+(s.textContent||'').length;},0)",
                    )
                    row["bodyCls"] = eval_value(send, "document.body.className")
                    row["content"] = eval_value(
                        send, "document.body.classList.contains('display-content')"
                    )
                    row["snapOk"] = True
                except Exception as e2:
                    row["snapFixError"] = str(e2)
            rows.append(row)
            print(json.dumps({k: row.get(k) for k in ("file", "loadEventFiredMs", "timing", "bc", "net7529_3s", "scripts", "inlineCss", "content")}, default=str), flush=True)

        out = {"phase": os.environ.get("BOOT_PHASE", "baseline"), "rows": rows, "t": time.time()}
        OUT.write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
        print(json.dumps(out, indent=2, default=str)[:12000])
        ws.close()
    finally:
        proc.send_signal(signal.SIGTERM)
        try:
            proc.wait(timeout=4)
        except Exception:
            proc.kill()


if __name__ == "__main__":
    run()
