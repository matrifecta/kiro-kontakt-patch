#!/usr/bin/env python3
"""Verify Clear on miss lives between Layouts and Search S in the top toolbar."""
import http.server
import json
import os
import socket
import subprocess
import sys
import threading
import time
import urllib.request
from pathlib import Path
from urllib.parse import urlparse

OUT = "/home/phnx/kiro-kontakt-patch/kiro/_patch/verify_clear_miss_hdr.json"
SHOT = "/home/phnx/kiro-kontakt-patch/kiro/_patch/ui-pos-shots"
PORT = 9477
HTTP_PORT = 8797
ROOT = "/home/phnx/kiro-kontakt-patch/public/catalogs"
URL = "http://127.0.0.1:8797/DS-CATALOG.html?v=clear-miss-hdr"
PROFILE = "/tmp/catalog-clear-miss-hdr2"
FILES = [
    Path("/home/phnx/kiro-kontakt-patch/public/catalogs/DS-CATALOG.html"),
    Path("/home/phnx/kiro-kontakt-patch/public/catalogs/KONTAKT-CATALOG.html"),
    Path("/home/phnx/kiro-kontakt-patch/public/catalogs/DS-CATALOG-portable.html"),
    Path("/home/phnx/kiro-kontakt-patch/public/catalogs/KONTAKT-CATALOG-portable.html"),
    Path("/home/phnx/kiro-kontakt-patch/kiro/specs/kontakt-workspace-drive-dirty-fix/artifacts/build-ds-catalog-html.sh"),
    Path("/home/phnx/kiro-kontakt-patch/kiro/specs/kontakt-workspace-drive-dirty-fix/artifacts/build-kontakt-catalog-html.sh"),
]
os.makedirs(PROFILE, exist_ok=True)
os.makedirs(SHOT, exist_ok=True)

MEASURE = r"""
(() => {
  function box(el){
    if(!el) return null;
    var r=el.getBoundingClientRect(), cs=getComputedStyle(el);
    return {
      id: el.id||'', tag: el.tagName, cls: el.className||'',
      txt: (el.textContent||'').trim().slice(0,40),
      parent: el.parentElement ? (el.parentElement.id||el.parentElement.className||el.parentElement.tagName) : '',
      prev: el.previousElementSibling ? (el.previousElementSibling.id||el.previousElementSibling.className||'') : '',
      next: el.nextElementSibling ? (el.nextElementSibling.id||el.nextElementSibling.className||'') : '',
      x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height),
      r: Math.round(r.right), disp: cs.display, vis: cs.visibility, pe: cs.pointerEvents,
      shown: cs.display!=='none' && cs.visibility!=='hidden' && r.width>2 && r.height>2
    };
  }
  function overlap(a,b){
    if(!a||!b) return false;
    return !(a.r<=b.x || b.r<=a.x || (a.y+a.h)<=b.y || (b.y+b.h)<=a.y);
  }
  var miss=document.getElementById('clearMissBtn');
  var layouts=document.getElementById('layoutPresetsBtn');
  var search=document.getElementById('hdrSearchBtn');
  var kw=document.getElementById('hdrKwBtn');
  var host=document.getElementById('hdrLayoutBtns');
  var hdr=document.querySelector('.catalog-header');
  var tools=document.getElementById('filterKwTools');
  var kids=hdr ? [...hdr.children].map(function(el){return el.id||el.className;}) : [];
  var mb=box(miss), lb=box(layouts), sb=box(search);
  return {
    display: typeof currentDisplay!=='undefined'?currentDisplay:'',
    middle: document.body.classList.contains('display-middle'),
    sides: document.body.classList.contains('display-sides'),
    vw: innerWidth, vh: innerHeight,
    kids: kids,
    missCount: document.querySelectorAll('#clearMissBtn,.clear-miss-btn').length,
    missInTools: !!(tools && miss && tools.contains(miss)),
    miss: mb,
    layouts: lb,
    search: sb,
    kw: box(kw),
    host: box(host),
    searchLabel: search ? (search.textContent||'').trim() : '',
    searchHasGlass: !!(search && /[\uD83D\uDD0D]/.test(search.textContent||'')),
    between: !!(mb && lb && sb && mb.shown && lb.shown && sb.shown && lb.r<=mb.x+1 && mb.r<=sb.x+1 && Math.abs(mb.y-lb.y)<28 && Math.abs(mb.y-sb.y)<28),
    overlapLayouts: overlap(mb, lb),
    overlapSearch: overlap(mb, sb),
    overlapLayoutSearch: overlap(lb, sb),
    parentOk: !!(miss && hdr && miss.parentElement===hdr),
    domBetween: !!(miss && miss.parentElement===hdr && miss.previousElementSibling && miss.previousElementSibling.id==='hdrLayoutBtns' && miss.nextElementSibling && (miss.nextElementSibling.id==='hdrEnd'||miss.nextElementSibling.id==='hdrMenuBtns'))
  };
})()
"""


def file_sync():
    errors = []
    for path in FILES:
        t = path.read_text(encoding="utf-8")
        if t.count('id="clearMissBtn"') != 1:
            errors.append(path.name + ":clearMissCount")
        if 'id="filterKwTools"><button type="button" class="clear-miss-btn"' in t:
            errors.append(path.name + ":stillInTools")
        if 'id="hdrLayoutBtns" role="toolbar" aria-label="Layout controls"></div><button type="button" class="clear-miss-btn"' not in t:
            errors.append(path.name + ":notAfterLayoutsHost")
        if 'toggleHdrSearch()">S</button>' not in t:
            errors.append(path.name + ":searchNotS")
        if 'toggleHdrSearch()">&#x1F50D;</button>' in t:
            errors.append(path.name + ":searchStillGlass")
        if "sessionId:'f491c2'" not in t:
            errors.append(path.name + ":no-f491c2")
        if "// #region agent log" not in t:
            errors.append(path.name + ":no-region")
        if path.name == "DS-CATALOG.html" and "sessionId:'c00e3e'" not in t:
            errors.append("DS-CATALOG.html:no-c00e3e")
    return errors


def ensure_http():
    class H(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a):
            pass

    os.chdir(ROOT)
    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", HTTP_PORT), H)
    httpd.allow_reuse_address = True
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    for _ in range(40):
        try:
            urllib.request.urlopen(URL.split("?")[0], timeout=1).read(64)
            return httpd
        except Exception:
            time.sleep(0.1)
    raise SystemExit("http 8797 failed")


class Ws:
    def __init__(self, url):
        u = urlparse(url)
        host, port = u.hostname, u.port or 80
        path = u.path + (("?" + u.query) if u.query else "")
        key = __import__("base64").b64encode(os.urandom(16)).decode()
        s = socket.create_connection((host, port), timeout=20)
        req = (
            f"GET {path} HTTP/1.1\r\nHost: {host}:{port}\r\nUpgrade: websocket\r\n"
            f"Connection: Upgrade\r\nSec-WebSocket-Key: {key}\r\nSec-WebSocket-Version: 13\r\n\r\n"
        )
        s.sendall(req.encode())
        hdr = b""
        while b"\r\n\r\n" not in hdr:
            chunk = s.recv(4096)
            if not chunk:
                raise RuntimeError("no ws handshake")
            hdr += chunk
        self.s = s
        self.buf = hdr.split(b"\r\n\r\n", 1)[1]

    def send(self, text):
        data = text.encode()
        flen = len(data)
        hdr = bytearray([0x81])
        mask = os.urandom(4)
        if flen < 126:
            hdr.append(0x80 | flen)
        elif flen < 65536:
            hdr.append(0x80 | 126)
            hdr.extend(flen.to_bytes(2, "big"))
        else:
            hdr.append(0x80 | 127)
            hdr.extend(flen.to_bytes(8, "big"))
        hdr.extend(mask)
        self.s.sendall(bytes(hdr) + bytes(b ^ mask[i % 4] for i, b in enumerate(data)))

    def recv(self):
        while True:
            if len(self.buf) < 2:
                self._fill()
                continue
            ln = self.buf[1] & 0x7F
            off = 2
            if ln == 126:
                if len(self.buf) < 4:
                    self._fill()
                    continue
                ln = int.from_bytes(self.buf[2:4], "big")
                off = 4
            elif ln == 127:
                if len(self.buf) < 10:
                    self._fill()
                    continue
                ln = int.from_bytes(self.buf[2:10], "big")
                off = 10
            if len(self.buf) < off + ln:
                self._fill()
                continue
            payload = self.buf[off : off + ln]
            self.buf = self.buf[off + ln :]
            return payload.decode()

    def _fill(self):
        chunk = self.s.recv(65536)
        if not chunk:
            raise RuntimeError("ws eof")
        self.buf += chunk


def new_tab(url):
    try:
        return json.load(
            urllib.request.urlopen(
                urllib.request.Request(f"http://127.0.0.1:{PORT}/json/new?" + url, method="PUT")
            )
        )
    except Exception:
        return json.load(urllib.request.urlopen(f"http://127.0.0.1:{PORT}/json/new?" + url))


class CDP:
    def __init__(self, url):
        self.ws = Ws(url)
        self.id = 0

    def call(self, method, params=None, timeout=180):
        self.id += 1
        mid = self.id
        self.ws.send(json.dumps({"id": mid, "method": method, "params": params or {}}))
        end = time.time() + timeout
        while time.time() < end:
            msg = json.loads(self.ws.recv())
            if msg.get("id") == mid:
                if "error" in msg:
                    raise RuntimeError(msg["error"])
                return msg.get("result", {})
        raise TimeoutError(method)

    def eval(self, expr, await_promise=False):
        r = self.call(
            "Runtime.evaluate",
            {"expression": expr, "awaitPromise": await_promise, "returnByValue": True},
        )
        if r.get("exceptionDetails"):
            raise RuntimeError(r["exceptionDetails"])
        return r.get("result", {}).get("value")


def wait_ready(cdp):
    for _ in range(80):
        try:
            n = cdp.eval(
                "!!(window.setDisplayMode&&document.getElementById('clearMissBtn')&&document.querySelectorAll('.entry').length>5)",
            )
        except Exception:
            n = False
        if n:
            return
        time.sleep(0.25)
    raise SystemExit("catalog JS not ready")


def set_view(cdp, w, h):
    portrait = h > w
    cdp.call(
        "Emulation.setDeviceMetricsOverride",
        {
            "width": w,
            "height": h,
            "deviceScaleFactor": 1,
            "mobile": w < 900,
            "screenOrientation": {
                "type": "portraitPrimary" if portrait else "landscapePrimary",
                "angle": 0 if portrait else 90,
            },
        },
    )
    time.sleep(0.3)


def shot(cdp, name):
    data = cdp.call("Page.captureScreenshot", {"format": "png"})
    raw = data.get("data")
    if not raw:
        return
    import base64

    Path(SHOT, name).write_bytes(base64.b64decode(raw))


def judge(name, st, errors):
    if not st:
        errors.append(name + ": no state")
        return
    if st.get("missCount") != 1:
        errors.append(f"{name}.dup={st.get('missCount')}")
    if st.get("missInTools"):
        errors.append(name + ": still in filterKwTools")
    if not st.get("parentOk"):
        errors.append(name + ": parent not catalog-header")
    if st.get("searchLabel") != "S":
        errors.append(f"{name}.searchLabel={st.get('searchLabel')!r}")
    if st.get("searchHasGlass"):
        errors.append(name + ": search still glass")
    miss = st.get("miss") or {}
    if not miss.get("shown"):
        errors.append(name + ": clear-miss not shown")
    if st.get("overlapLayouts") or st.get("overlapSearch") or st.get("overlapLayoutSearch"):
        errors.append(name + ": overlap")
    if not st.get("domBetween"):
        errors.append(f"{name}.domBetween kids={st.get('kids')} miss={st.get('miss')}")
    if not st.get("between"):
        errors.append(
            f"{name}.notBetween layouts={st.get('layouts')} miss={miss} search={st.get('search')} kids={st.get('kids')}"
        )


def main():
    errors = file_sync()
    httpd = ensure_http()
    chrome = next(
        (
            p
            for p in ("/usr/lib/chromium/chromium", "/usr/bin/chromium", "/usr/bin/google-chrome")
            if os.path.exists(p)
        ),
        None,
    )
    if not chrome:
        raise SystemExit("no chromium")
    logf = open("/tmp/catalog-clear-miss-hdr.log", "w")
    proc = subprocess.Popen(
        [
            chrome,
            "--headless=new",
            "--disable-gpu",
            "--no-first-run",
            "--disable-extensions",
            f"--remote-debugging-port={PORT}",
            "--remote-allow-origins=*",
            f"--user-data-dir={PROFILE}",
            "--noerrdialogs",
            "--ozone-platform=headless",
            "--ozone-override-screen-size=1400,900",
            "--use-angle=swiftshader-webgl",
            "about:blank",
        ],
        stdout=logf,
        stderr=subprocess.STDOUT,
    )
    result = {"ok": False, "errors": errors, "checks": {}}
    try:
        for _ in range(80):
            try:
                urllib.request.urlopen(f"http://127.0.0.1:{PORT}/json/version", timeout=1).read()
                break
            except Exception:
                time.sleep(0.2)
        else:
            json.dump({"err": "cdp"}, open(OUT, "w"))
            sys.exit(1)
        tab = new_tab("about:blank")
        cdp = CDP(tab["webSocketDebuggerUrl"])
        cdp.call("Page.enable")
        cdp.call("Runtime.enable")

        set_view(cdp, 1400, 900)
        cdp.call("Page.navigate", {"url": URL})
        wait_ready(cdp)
        cdp.eval("if(typeof setDisplayMode==='function')setDisplayMode('sides',{pick:true});")
        time.sleep(0.3)
        cdp.eval("if(typeof ensureLayoutChromeBtns==='function')ensureLayoutChromeBtns();")
        st = cdp.eval(MEASURE)
        result["checks"]["sides1400"] = st
        judge("sides1400", st, errors)
        shot(cdp, "D1400-clear-miss-hdr.png")

        cdp.eval("if(typeof setDisplayMode==='function')setDisplayMode('middle',{pick:true});")
        time.sleep(0.3)
        cdp.eval("if(typeof ensureLayoutChromeBtns==='function')ensureLayoutChromeBtns();")
        st = cdp.eval(MEASURE)
        result["checks"]["middle1400"] = st
        judge("middle1400", st, errors)
        shot(cdp, "D1400-clear-miss-hdr-middle.png")

        set_view(cdp, 900, 1400)
        cdp.eval(
            "window.dispatchEvent(new Event('orientationchange'));"
            "if(typeof setDisplayMode==='function')setDisplayMode('middle',{pick:true});"
            "if(typeof ensureLayoutChromeBtns==='function')ensureLayoutChromeBtns();"
        )
        time.sleep(0.35)
        st = cdp.eval(MEASURE)
        result["checks"]["portrait900"] = st
        judge("portrait900", st, errors)
        shot(cdp, "D900-clear-miss-hdr-portrait.png")
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=3)
        except Exception:
            proc.kill()
        if httpd:
            httpd.shutdown()

    result["ok"] = not errors
    json.dump(result, open(OUT, "w"), indent=2)
    print(json.dumps(result, indent=2)[:8000])
    if errors:
        sys.exit(1)


if __name__ == "__main__":
    main()
