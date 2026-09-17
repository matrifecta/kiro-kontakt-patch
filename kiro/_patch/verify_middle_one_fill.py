#!/usr/bin/env python3
"""CDP 1400x900: Middle Flip S-only has no ghost pane; S+K pair; Sides 3-col."""
import base64
import http.server
import json
import os
import socket
import subprocess
import threading
import time
import urllib.request
from pathlib import Path
from urllib.parse import urlparse

OUT = Path("/home/phnx/kiro-kontakt-patch/kiro/_patch/verify_middle_one_fill.json")
SHOT = Path("/home/phnx/kiro-kontakt-patch/kiro/_patch/ui-pos-shots")
PORT = 9552
HTTP_PORT = 8797
SHOT.mkdir(parents=True, exist_ok=True)
os.makedirs("/tmp/catalog-mid-one-fill", exist_ok=True)

URL = f"http://127.0.0.1:{HTTP_PORT}/DS-CATALOG.html?midfill=1"


class Ws:
    def __init__(self, url):
        u = urlparse(url)
        host, port = u.hostname, u.port or 80
        path = u.path + (("?" + u.query) if u.query else "")
        key = base64.b64encode(os.urandom(16)).decode()
        s = socket.create_connection((host, port), timeout=60)
        s.settimeout(120)
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

    def eval(self, expr):
        r = self.call(
            "Runtime.evaluate",
            {"expression": expr, "returnByValue": True},
        )
        if r.get("exceptionDetails"):
            raise RuntimeError(r["exceptionDetails"])
        return r.get("result", {}).get("value")


def port_open(port):
    s = socket.socket()
    s.settimeout(0.3)
    try:
        s.connect(("127.0.0.1", port))
        return True
    except Exception:
        return False
    finally:
        s.close()


def ensure_http():
    try:
        urllib.request.urlopen(f"http://127.0.0.1:{HTTP_PORT}/DS-CATALOG.html", timeout=2).read(64)
        return
    except Exception:
        pass
    os.chdir("/home/phnx/kiro-kontakt-patch/public/catalogs")

    class H(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a):
            pass

    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", HTTP_PORT), H)
    httpd.allow_reuse_address = True
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    for _ in range(40):
        try:
            urllib.request.urlopen(f"http://127.0.0.1:{HTTP_PORT}/DS-CATALOG.html", timeout=1).read(64)
            return
        except Exception:
            time.sleep(0.1)
    raise SystemExit("http 8797 failed")


GEO = r"""
(() => {
  function box(el){
    if(!el)return {on:false,x:0,y:0,w:0,h:0,disp:'none'};
    var cs=getComputedStyle(el), r=el.getBoundingClientRect();
    return {
      on:cs.display!=='none'&&r.width>8&&r.height>8,
      x:Math.round(r.x),y:Math.round(r.y),w:Math.round(r.width),h:Math.round(r.height),
      disp:cs.display
    };
  }
  var sc=document.getElementById('searchChrome');
  var fw=document.getElementById('filterWrap');
  var main=document.getElementById('catalogMain');
  var hdr=document.querySelector('.catalog-header');
  var ix=document.getElementById('catalogIndex');
  var bcs=getComputedStyle(document.body);
  var gap=0;
  if(main&&hdr){
    var hr=hdr.getBoundingClientRect(), mr=main.getBoundingClientRect();
    gap=Math.round(mr.top-hr.bottom);
  }
  return {
    vw:window.innerWidth,vh:window.innerHeight,
    land:document.body.classList.contains('desk-landscape'),
    mid:document.body.classList.contains('display-middle'),
    sides:document.body.classList.contains('display-sides'),
    flip:document.body.classList.contains('sides-portrait-flip'),
    sCol:document.body.classList.contains('search-chrome-collapsed'),
    kCol:document.body.classList.contains('kw-chrome-collapsed'),
    cols:bcs.gridTemplateColumns,rows:bcs.gridTemplateRows,
    search:box(sc),kw:box(fw),main:box(main),hdr:box(hdr),ix:box(ix),
    gap:gap
  };
})()
"""


def box_ok_side(a, b):
    return a["on"] and b["on"] and abs(a["y"] - b["y"]) < 80 and a["h"] > 280 and b["h"] > 280


def main():
    ensure_http()
    if not port_open(PORT):
        subprocess.Popen(
            [
                "chromium",
                f"--remote-debugging-port={PORT}",
                "--user-data-dir=/tmp/catalog-mid-one-fill",
                "--headless=new",
                "--disable-gpu",
                "--no-first-run",
                "--no-default-browser-check",
                "about:blank",
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        for _ in range(40):
            if port_open(PORT):
                break
            time.sleep(0.2)
        else:
            raise SystemExit("chromium debug port failed")
        time.sleep(0.4)

    try:
        tab = json.load(
            urllib.request.urlopen(
                urllib.request.Request(f"http://127.0.0.1:{PORT}/json/new?" + URL, method="PUT")
            )
        )
    except Exception:
        tab = json.load(urllib.request.urlopen(f"http://127.0.0.1:{PORT}/json/new?" + URL))
    cdp = CDP(tab["webSocketDebuggerUrl"])
    cdp.call("Page.enable")
    cdp.call("Runtime.enable")
    cdp.call("Page.navigate", {"url": URL})
    time.sleep(0.8)
    for _ in range(150):
        try:
            if cdp.eval("!!(document.getElementById('catalogIndex')&&typeof setDisplayMode==='function')"):
                break
        except Exception:
            pass
        time.sleep(0.2)
    else:
        raise SystemExit("catalog JS not ready")

    cdp.call(
        "Emulation.setDeviceMetricsOverride",
        {
            "width": 1400,
            "height": 900,
            "deviceScaleFactor": 1,
            "mobile": False,
            "screenOrientation": {"type": "landscapePrimary", "angle": 90},
        },
    )
    time.sleep(0.4)
    cdp.eval(
        "try{localStorage.removeItem((typeof desktopArrangeStoreKey==='function'&&desktopArrangeStoreKey())||'');}catch(e){}"
        "document.body.classList.remove('sides-portrait-flip','middle-kw-first');"
        "if(typeof setDisplayMode==='function')setDisplayMode('middle',{pick:true});"
        "if(typeof expandSearchMenu==='function')expandSearchMenu();"
        "if(typeof collapseKwMenu==='function')collapseKwMenu();"
        "document.body.classList.remove('search-chrome-collapsed');"
        "document.body.classList.add('kw-chrome-collapsed');"
        "if(typeof togglePortraitSidesFlip==='function'&&!document.body.classList.contains('sides-portrait-flip'))togglePortraitSidesFlip();"
        "document.body.classList.add('sides-portrait-flip');"
        "if(typeof applySidesCols==='function')applySidesCols();"
        "if(typeof syncHdrMenuBtns==='function')syncHdrMenuBtns();"
    )
    time.sleep(0.35)
    mid_flip_s = cdp.eval(GEO)
    raw = cdp.call("Page.captureScreenshot", {"format": "png"}).get("data")
    if raw:
        (SHOT / "D1400-ds-middle-flip-s.png").write_bytes(base64.b64decode(raw))

    cdp.eval(
        "if(typeof expandKwMenu==='function')expandKwMenu();"
        "document.body.classList.remove('kw-chrome-collapsed');"
        "var fw=document.getElementById('filterWrap');if(fw){fw.classList.add('open');document.body.classList.add('kw-open');}"
        "if(typeof applySidesCols==='function')applySidesCols();"
    )
    time.sleep(0.3)
    mid_both = cdp.eval(GEO)
    raw = cdp.call("Page.captureScreenshot", {"format": "png"}).get("data")
    if raw:
        (SHOT / "D1400-ds-middle-flip-sk.png").write_bytes(base64.b64decode(raw))

    cdp.eval(
        "if(document.body.classList.contains('sides-portrait-flip')&&typeof togglePortraitSidesFlip==='function')togglePortraitSidesFlip();"
        "document.body.classList.remove('sides-portrait-flip');"
        "if(typeof setDisplayMode==='function')setDisplayMode('sides',{pick:true});"
        "if(typeof expandSearchMenu==='function')expandSearchMenu();"
        "if(typeof expandKwMenu==='function')expandKwMenu();"
        "document.body.classList.remove('search-chrome-collapsed','kw-chrome-collapsed');"
        "var fw=document.getElementById('filterWrap');if(fw){fw.classList.add('open');document.body.classList.add('kw-open');}"
        "if(typeof applySidesCols==='function')applySidesCols();"
    )
    time.sleep(0.3)
    sides = cdp.eval(GEO)
    raw = cdp.call("Page.captureScreenshot", {"format": "png"}).get("data")
    if raw:
        (SHOT / "D1400-ds-sides-3.png").write_bytes(base64.b64decode(raw))

    try:
        urllib.request.urlopen(f"http://127.0.0.1:{PORT}/json/close/{tab['id']}")
    except Exception:
        pass

    s, m = mid_flip_s["search"], mid_flip_s["main"]
    no_void = (
        mid_flip_s["flip"]
        and s["on"]
        and not mid_flip_s["kw"]["on"]
        and m["on"]
        and box_ok_side(s, m)
        and mid_flip_s["gap"] < 80
        and m["h"] > 500
        and s["x"] > m["x"]
    )
    both = mid_both
    pair = (
        both["search"]["on"]
        and both["kw"]["on"]
        and abs(both["search"]["y"] - both["kw"]["y"]) < 60
        and both["search"]["w"] < both["vw"] * 0.72
        and both["kw"]["w"] < both["vw"] * 0.72
        and both["main"]["on"]
    )
    three = (
        sides["search"]["on"]
        and sides["kw"]["on"]
        and sides["main"]["on"]
        and abs(sides["search"]["y"] - sides["kw"]["y"]) < 80
        and sides["search"]["w"] < sides["vw"] * 0.45
        and sides["kw"]["w"] < sides["vw"] * 0.45
        and sides["main"]["w"] > 200
    )
    out = {
        "midFlipS": mid_flip_s,
        "midBoth": mid_both,
        "sides": sides,
        "pass": {"midFlipSNoVoid": no_void, "middlePair": pair, "sides3": three},
    }
    OUT.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(json.dumps(out, indent=2))
    fails = [k for k, ok in out["pass"].items() if not ok]
    if fails:
        raise SystemExit("FAIL " + " | ".join(fails))
    print("PASS")


if __name__ == "__main__":
    main()
