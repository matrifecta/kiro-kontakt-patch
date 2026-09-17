#!/usr/bin/env python3
"""Headless Chromium CDP probe for Shade removal. Stdlib only."""
import base64
import hashlib
import json
import os
import socket
import subprocess
import time
import urllib.error
import urllib.request
from urllib.parse import urlparse

PORT = 9334
BASE = "http://127.0.0.1:8788"
CHROME = "/usr/bin/chromium"
PROFILE = "/tmp/shade-rm-chrome"


class Ws:
    def __init__(self, url):
        u = urlparse(url)
        host, port = u.hostname, u.port or 80
        path = u.path + (("?" + u.query) if u.query else "")
        key = base64.b64encode(os.urandom(16)).decode()
        s = socket.create_connection((host, port), timeout=20)
        req = (
            f"GET {path} HTTP/1.1\r\n"
            f"Host: {host}:{port}\r\n"
            "Upgrade: websocket\r\n"
            "Connection: Upgrade\r\n"
            f"Sec-WebSocket-Key: {key}\r\n"
            "Sec-WebSocket-Version: 13\r\n\r\n"
        )
        s.sendall(req.encode())
        hdr = b""
        while b"\r\n\r\n" not in hdr:
            chunk = s.recv(4096)
            if not chunk:
                raise RuntimeError("no ws handshake")
            hdr += chunk
        expect = base64.b64encode(
            hashlib.sha1((key + "258EAFA5-E914-47DA-95CA-C5AB0DC85B11").encode()).digest()
        ).decode()
        if expect not in hdr.decode("latin1"):
            raise RuntimeError("bad ws accept")
        extra = hdr.split(b"\r\n\r\n", 1)[1]
        self.s = s
        self.buf = extra
        self.n = 0

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
            b0, b1 = self.buf[0], self.buf[1]
            ln = b1 & 0x7F
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
            if (b0 & 0xF) == 0x1:
                return payload.decode()
            if (b0 & 0xF) == 0x8:
                raise RuntimeError("ws closed")

    def _fill(self):
        chunk = self.s.recv(65536)
        if not chunk:
            raise RuntimeError("ws eof")
        self.buf += chunk

    def close(self):
        try:
            self.s.close()
        except OSError:
            pass


class Cdp:
    def __init__(self, ws):
        self.ws = ws

    def call(self, method, params=None, timeout=30):
        self.n = getattr(self, "n", 0) + 1
        mid = self.n
        self.ws.send(json.dumps({"id": mid, "method": method, "params": params or {}}))
        t0 = time.time()
        while time.time() - t0 < timeout:
            msg = json.loads(self.ws.recv())
            if msg.get("id") == mid:
                if "error" in msg:
                    raise RuntimeError(f"{method}: {msg['error']}")
                return msg.get("result", {})
        raise TimeoutError(method)

    def eval(self, expr, timeout=30):
        r = self.call(
            "Runtime.evaluate",
            {
                "expression": expr,
                "returnByValue": True,
                "awaitPromise": True,
            },
            timeout=timeout,
        )
        if r.get("exceptionDetails"):
            raise RuntimeError(r["exceptionDetails"])
        return (r.get("result") or {}).get("value")


PROBE_JS = r"""
(async function(){
  function vis(el){
    if(!el) return {ok:false};
    var cs=getComputedStyle(el);
    var r=el.getBoundingClientRect();
    return {
      ok: cs.display!=='none' && cs.visibility!=='hidden' && r.width>1 && r.height>1,
      display: cs.display,
      w: Math.round(r.width),
      h: Math.round(r.height),
      x: Math.round(r.x),
      y: Math.round(r.y),
      bottom: Math.round(r.bottom),
      bottomGap: Math.round(window.innerHeight-r.bottom)
    };
  }
  function geom(){
    var fw=document.getElementById('filterWrap');
    var fp=fw&&fw.querySelector('.filter-panel');
    var sc=document.getElementById('searchChrome');
    var col=document.getElementById('searchCol');
    var sep=document.getElementById('dualFsSep');
    var split=document.getElementById('searchSplit');
    var pin=document.getElementById('dualFsSepPin');
    var shadeBtns=[].map.call(document.querySelectorAll('.mode-btn[data-mode="shade"]'), function(b){
      var c=getComputedStyle(b); var r=b.getBoundingClientRect();
      return {text:b.textContent, display:c.display, w:Math.round(r.width), h:Math.round(r.height)};
    });
    var sidesBtns=[].map.call(document.querySelectorAll('.display-btn'), function(b){
      var c=getComputedStyle(b);
      return {mode:b.getAttribute('data-display'), text:b.textContent.trim(), display:c.display, active:b.classList.contains('is-active')};
    });
    return {
      vw: window.innerWidth, vh: window.innerHeight,
      currentMode: typeof currentMode!=='undefined'?currentMode:null,
      searchMode: document.body.classList.contains('search-mode'),
      display: typeof currentDisplay!=='undefined'?currentDisplay:document.body.className,
      body: document.body.className,
      fw: vis(fw),
      fp: vis(fp),
      fpPos: fp?getComputedStyle(fp).position:'',
      fpMax: fp?getComputedStyle(fp).maxHeight:'',
      sc: vis(sc),
      col: vis(col),
      sepStyle: sep?(sep.getAttribute('style')||''):null,
      splitStyle: split?(split.getAttribute('style')||''):null,
      pin: vis(pin),
      shadeBtns: shadeBtns,
      displayBtns: sidesBtns,
      hideSearch: !!(document.querySelector('.search-strip-hide'))
    };
  }
  window.__probe = geom;
  return geom();
})()
"""


def http_json(url, timeout=5):
    with urllib.request.urlopen(url, timeout=timeout) as r:
        return json.loads(r.read().decode())


def wait_devtools():
    for _ in range(40):
        try:
            return http_json(f"http://127.0.0.1:{PORT}/json/version")
        except Exception:
            time.sleep(0.15)
    raise RuntimeError("devtools not up")


def new_page(url):
    req = urllib.request.Request(
        f"http://127.0.0.1:{PORT}/json/new?" + url,
        method="PUT",
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError:
        tabs = http_json(f"http://127.0.0.1:{PORT}/json/list")
        if not tabs:
            raise
        return tabs[0]


def attach(page):
    ws = Ws(page["webSocketDebuggerUrl"])
    cdp = Cdp(ws)
    cdp.call("Runtime.enable")
    cdp.call("Page.enable")
    return cdp


def wait_ready(cdp, timeout=25):
    t0 = time.time()
    while time.time() - t0 < timeout:
        try:
            ok = cdp.eval(
                "document.readyState==='complete' && typeof window.setMode==='function' && typeof window.setDisplayMode==='function'"
            )
            if ok:
                time.sleep(0.4)
                return
        except Exception:
            pass
        time.sleep(0.2)
    raise RuntimeError("catalog JS not ready")


def run_catalog(cdp, name, url):
    cdp.call("Page.navigate", {"url": url})
    wait_ready(cdp)
    # hard-ish refresh path: already navigated with cache-bust
    out = {"name": name, "url": url}
    out["upper"] = cdp.eval(PROBE_JS)
    # click a keyword if present
    out["kwClick"] = cdp.eval(
        """
        (function(){
          var b=document.querySelector('#kwbar .kw:not(.disabled):not(.clear)');
          if(b){b.click(); return b.textContent;}
          return null;
        })()
        """
    )
    out["afterKw"] = cdp.eval("window.__probe()")
    # hide search extras
    out["hide"] = cdp.eval(
        """
        (function(){
          var b=document.querySelector('.search-strip-hide');
          if(b){b.click(); return true;}
          if(typeof window.exitSearchUi==='function'){window.exitSearchUi(); return 'exitSearchUi';}
          return false;
        })()
        """
    )
    out["afterHide"] = cdp.eval("window.__probe()")
    # leftover Shade click
    out["shadeClick"] = cdp.eval(
        """
        (function(){
          var b=document.querySelector('.mode-btn[data-mode="shade"]');
          if(!b) return 'missing';
          b.click();
          return {searchMode: document.body.classList.contains('search-mode'), body: document.body.className};
        })()
        """
    )
    # Sides
    cdp.eval("window.setDisplayMode('sides')")
    time.sleep(0.5)
    out["sides"] = cdp.eval("window.__probe()")
    out["sidesKw"] = cdp.eval(
        """
        (function(){
          var fw=document.getElementById('filterWrap');
          var btn=document.querySelector('#kwbar .kw:not(.disabled):not(.clear)');
          if(btn) btn.click();
          var r=fw&&fw.getBoundingClientRect();
          return {
            open: !!(fw&&fw.classList.contains('open')),
            kwOpen: document.body.classList.contains('kw-open'),
            fwH: r?Math.round(r.height):null,
            bottomGap: r?Math.round(window.innerHeight-r.bottom):null,
            searchMode: document.body.classList.contains('search-mode'),
            sepStyle: (document.getElementById('dualFsSep')||{}).getAttribute?document.getElementById('dualFsSep').getAttribute('style'):null
          };
        })()
        """
    )
    # Full
    cdp.eval("window.setDisplayMode('fs')")
    time.sleep(0.4)
    out["fs"] = cdp.eval("window.__probe()")
    # back to Upper — leftover pin styles
    cdp.eval("window.setDisplayMode('upper')")
    time.sleep(0.4)
    out["backUpper"] = cdp.eval("window.__probe()")
    # mobile viewport
    cdp.call("Emulation.setDeviceMetricsOverride", {
        "width": 390,
        "height": 844,
        "deviceScaleFactor": 2,
        "mobile": True,
    })
    time.sleep(0.4)
    out["mobile"] = cdp.eval("window.__probe()")
    cdp.call("Emulation.clearDeviceMetricsOverride")
    return out


def main():
    os.makedirs(PROFILE, exist_ok=True)
    proc = subprocess.Popen(
        [
            CHROME,
            "--headless=new",
            "--disable-gpu",
            "--no-first-run",
            "--no-default-browser-check",
            f"--remote-debugging-port={PORT}",
            f"--user-data-dir={PROFILE}",
            "--window-size=1400,900",
            "about:blank",
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        wait_devtools()
        page = new_page("about:blank")
        cdp = attach(page)
        results = []
        for name, path in (
            ("DS", "/DS-CATALOG.html?v=shade-rm"),
            ("KONTAKT", "/KONTAKT-CATALOG.html?v=shade-rm"),
        ):
            results.append(run_catalog(cdp, name, BASE + path))
        out_path = "/home/phnx/kiro-kontakt-patch/kiro/_patch/verify_shade_rm.json"
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2)
        print(json.dumps(results, indent=2))
        print("WROTE", out_path)
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()


if __name__ == "__main__":
    main()
