#!/usr/bin/env python3
"""Headless check: landscape→Sides, portrait→Middle, per-orient pick, reload, rotate."""
import hashlib
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

OUT = "/home/phnx/kiro-kontakt-patch/kiro/_patch/verify_display_orient_defaults.json"
PORT = 9474
HTTP_PORT = 8794
ROOT = "/home/phnx/kiro-kontakt-patch/public/catalogs"
URL_DS = "http://127.0.0.1:8794/DS-CATALOG.html?v=orient-defaults"
URL_K = "http://127.0.0.1:8794/KONTAKT-CATALOG.html?v=orient-defaults"
URL_P = "http://127.0.0.1:8794/DS-CATALOG-portable.html?v=orient-defaults"
PROFILE = "/tmp/catalog-display-orient"
FILES = [
    Path("/home/phnx/kiro-kontakt-patch/public/catalogs/DS-CATALOG.html"),
    Path("/home/phnx/kiro-kontakt-patch/public/catalogs/KONTAKT-CATALOG.html"),
    Path("/home/phnx/kiro-kontakt-patch/public/catalogs/DS-CATALOG-portable.html"),
    Path("/home/phnx/kiro-kontakt-patch/public/catalogs/KONTAKT-CATALOG-portable.html"),
    Path("/home/phnx/kiro-kontakt-patch/kiro/specs/kontakt-workspace-drive-dirty-fix/artifacts/build-ds-catalog-html.sh"),
    Path("/home/phnx/kiro-kontakt-patch/kiro/specs/kontakt-workspace-drive-dirty-fix/artifacts/build-kontakt-catalog-html.sh"),
]
os.makedirs(PROFILE, exist_ok=True)

STATE = r"""
(() => {
  const ns = window.CATALOG_NS || 'catalog';
  const cls = [...document.body.classList];
  return {
    ns, vw: innerWidth, vh: innerHeight,
    portrait: !!(window.matchMedia && window.matchMedia('(orientation:portrait)').matches),
    orient: typeof displayOrientId === 'function' ? displayOrientId() : null,
    display: typeof currentDisplay !== 'undefined' ? currentDisplay : null,
    sides: cls.includes('display-sides'),
    middle: cls.includes('display-middle'),
    portable: !!window.CATALOG_PORTABLE,
    keys: {
      mode: localStorage.getItem('catalog-display-mode-' + ns),
      pick: localStorage.getItem('catalog-display-pick-' + ns),
      pickL: localStorage.getItem('catalog-display-pick-' + ns + '-landscape'),
      modeL: localStorage.getItem('catalog-display-mode-' + ns + '-landscape'),
      pickP: localStorage.getItem('catalog-display-pick-' + ns + '-portrait'),
      modeP: localStorage.getItem('catalog-display-mode-' + ns + '-portrait')
    },
    resolved: typeof resolveDisplayForOrient === 'function' ? {
      cur: resolveDisplayForOrient(),
      l: resolveDisplayForOrient('landscape'),
      p: resolveDisplayForOrient('portrait')
    } : null
  };
})()
"""

CLEAR = r"""
(() => {
  const ns = window.CATALOG_NS || 'catalog';
  ['', '-landscape', '-portrait'].forEach(function(suf){
    localStorage.removeItem('catalog-display-pick-' + ns + suf);
    localStorage.removeItem('catalog-display-mode-' + ns + suf);
  });
  return true;
})()
"""


def file_sync():
    marker = "function displayOrientId(){"
    end = "window.logDisplayOrient=logDisplayOrient;"
    hashes = {}
    missing = []
    for path in FILES:
        text = path.read_text(encoding="utf-8")
        if marker not in text or "function resolveDisplayForOrient" not in text:
            missing.append(path.name)
            continue
        i = text.find(marker)
        j = text.find(end, i)
        chunk = text[i : j + len(end)] if j > i else ""
        hashes[path.name] = hashlib.sha256(chunk.encode()).hexdigest()[:12]
        if "sessionId:'f491c2'" not in text:
            missing.append(path.name + ":no-f491c2")
        if path.name == "DS-CATALOG.html" and "sessionId:'c00e3e'" not in text:
            missing.append("DS-CATALOG.html:no-c00e3e")
        if path.name == "DS-CATALOG.html" and "// #region agent log" not in text:
            missing.append("DS-CATALOG.html:no-region")
    uniq = set(hashes.values())
    return {"hashes": hashes, "ok": len(uniq) == 1 and not missing, "missing": missing}


def ensure_http():
    try:
        urllib.request.urlopen(URL_DS.split("?")[0], timeout=1).read(64)
        return None
    except Exception:
        pass
    os.chdir(ROOT)

    class H(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a):
            pass

    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", HTTP_PORT), H)
    httpd.allow_reuse_address = True
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    for _ in range(30):
        try:
            urllib.request.urlopen(URL_DS.split("?")[0], timeout=1).read(64)
            return httpd
        except Exception:
            time.sleep(0.1)
    raise SystemExit("http 8794 failed")


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
                "!!(window.setDisplayMode&&window.resolveDisplayForOrient&&document.querySelectorAll('.entry').length>20)",
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
    time.sleep(0.35)
    try:
        cdp.eval(
            "window.dispatchEvent(new Event('orientationchange'));"
            "if(typeof syncDisplayForOrientation==='function')syncDisplayForOrientation();"
        )
    except Exception:
        pass
    time.sleep(0.2)


def nav(cdp, url, w, h):
    set_view(cdp, w, h)
    cdp.call("Page.navigate", {"url": url})
    wait_ready(cdp)


def reload_page(cdp):
    cdp.call("Page.reload", {"ignoreCache": False})
    wait_ready(cdp)


def expect(result, errors, name, st, **want):
    result[name] = st
    if not st:
        errors.append(name + ": no state")
        return
    keys = st.get("keys") or {}
    for k, v in want.items():
        got = keys.get(k) if k in keys or k in ("mode", "pick", "pickL", "modeL", "pickP", "modeP") else st.get(k)
        if got != v:
            errors.append(f"{name}.{k}={got!r} want {v!r}")


def main():
    sync = file_sync()
    errors = []
    if not sync["ok"]:
        errors.append("file-sync " + json.dumps(sync))
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
    logf = open("/tmp/catalog-display-orient.log", "w")
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
    result = {"ok": False, "errors": errors, "sync": sync}
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

        nav(cdp, URL_DS, 1400, 900)
        cdp.eval(CLEAR)
        reload_page(cdp)
        st = cdp.eval(STATE)
        expect(result, errors, "land_default", st, sides=True, middle=False, display="sides", orient="landscape")

        reload_page(cdp)
        st = cdp.eval(STATE)
        expect(result, errors, "land_reload", st, sides=True, middle=False, display="sides")

        cdp.eval(CLEAR)
        set_view(cdp, 900, 1400)
        reload_page(cdp)
        st = cdp.eval(STATE)
        expect(result, errors, "port_default", st, sides=True, middle=True, display="middle", orient="portrait")

        reload_page(cdp)
        st = cdp.eval(STATE)
        expect(result, errors, "port_reload", st, sides=True, middle=True, display="middle")

        cdp.eval(
            """
(() => {
  const ns = window.CATALOG_NS || 'catalog';
  localStorage.setItem('catalog-display-pick-' + ns + '-landscape', '1');
  localStorage.setItem('catalog-display-mode-' + ns + '-landscape', 'middle');
  return true;
})()
"""
        )
        set_view(cdp, 1400, 900)
        reload_page(cdp)
        st = cdp.eval(STATE)
        expect(result, errors, "land_pick_middle", st, sides=True, middle=True, display="middle", modeL="middle")

        cdp.eval(CLEAR)
        reload_page(cdp)
        st = cdp.eval(STATE)
        expect(result, errors, "land_after_clear", st, sides=True, middle=False, display="sides")

        set_view(cdp, 900, 1400)
        time.sleep(0.4)
        st = cdp.eval(STATE)
        expect(result, errors, "rotate_to_portrait", st, sides=True, middle=True, display="middle", orient="portrait")

        set_view(cdp, 1400, 900)
        time.sleep(0.4)
        st = cdp.eval(STATE)
        expect(result, errors, "rotate_to_landscape", st, sides=True, middle=False, display="sides", orient="landscape")

        cdp.eval("if(typeof setDisplayMode==='function')setDisplayMode('middle',{pick:true});")
        st = cdp.eval(STATE)
        expect(result, errors, "explicit_middle_land", st, middle=True, display="middle", pickL="1", modeL="middle")

        set_view(cdp, 900, 1400)
        time.sleep(0.4)
        st = cdp.eval(STATE)
        expect(result, errors, "pick_middle_land_then_portrait", st, middle=True, display="middle")

        cdp.eval("if(typeof setDisplayMode==='function')setDisplayMode('sides',{pick:true});")
        st = cdp.eval(STATE)
        expect(result, errors, "explicit_sides_port", st, middle=False, display="sides", pickP="1", modeP="sides")

        set_view(cdp, 1400, 900)
        time.sleep(0.4)
        st = cdp.eval(STATE)
        expect(result, errors, "portrait_sides_pick_then_land", st, middle=True, display="middle")

        set_view(cdp, 900, 1400)
        time.sleep(0.4)
        st = cdp.eval(STATE)
        expect(result, errors, "back_to_portrait_sides_pick", st, middle=False, display="sides")

        cdp.eval(CLEAR)
        cdp.eval(
            """
(() => {
  const ns = window.CATALOG_NS || 'catalog';
  localStorage.setItem('catalog-display-pick-' + ns, '1');
  localStorage.setItem('catalog-display-mode-' + ns, 'middle');
  return true;
})()
"""
        )
        set_view(cdp, 1400, 900)
        reload_page(cdp)
        st = cdp.eval(STATE)
        expect(result, errors, "legacy_global_pick_ignored_on_land", st, middle=False, display="sides")

        nav(cdp, URL_K, 1400, 900)
        cdp.eval(CLEAR)
        reload_page(cdp)
        st = cdp.eval(STATE)
        expect(result, errors, "kontakt_land", st, sides=True, middle=False, display="sides")

        nav(cdp, URL_P, 390, 844)
        cdp.eval(CLEAR)
        reload_page(cdp)
        st = cdp.eval(STATE)
        expect(result, errors, "portable_portrait", st, middle=True, display="middle", portable=True)

        set_view(cdp, 844, 390)
        time.sleep(0.4)
        st = cdp.eval(STATE)
        expect(result, errors, "portable_landscape", st, middle=False, display="sides", portable=True)

        result["ok"] = len(errors) == 0
        result["errors"] = errors
        json.dump(result, open(OUT, "w"), indent=2)
        print(json.dumps({"ok": result["ok"], "errors": errors, "sync": sync}, indent=2))
        sys.exit(0 if result["ok"] else 1)
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=3)
        except Exception:
            proc.kill()
        if httpd:
            httpd.shutdown()


if __name__ == "__main__":
    main()
