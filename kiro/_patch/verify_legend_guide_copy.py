#!/usr/bin/env python3
"""CDP: Legend + both Guide tabs show full collapsible copy."""
import json
import os
import socket
import subprocess
import time
import urllib.request
from pathlib import Path
from urllib.parse import urlparse
import base64

PORT = 9551
HTTP = 8797
PROFILE = "/tmp/catalog-legend-guide"
SHOT = Path("/home/phnx/kiro-kontakt-patch/kiro/_patch/ui-pos-shots")
OUT = Path("/home/phnx/kiro-kontakt-patch/kiro/_patch/verify_legend_guide_copy.json")
SHOT.mkdir(parents=True, exist_ok=True)

PROBE = r"""
(() => {
  var body=document.getElementById('catalogHelpBody');
  var legend=document.getElementById('catalogHelpLegend');
  var user=document.getElementById('catalogHelpUser');
  var upd=document.getElementById('catalogHelpUpdate');
  function titles(root){
    if(!root)return [];
    return Array.prototype.map.call(root.querySelectorAll('summary'),function(s){return (s.textContent||'').trim();});
  }
  function vis(el){
    if(!el)return {on:false,h:0,scroll:0};
    var cs=getComputedStyle(el);
    var r=el.getBoundingClientRect();
    return {on:cs.display!=='none'&&!el.hidden&&r.height>8, h:Math.round(r.height), scroll:el.scrollHeight, client:el.clientHeight, hidden:!!el.hidden};
  }
  return {
    kind:window._catalogHelpKind||null,
    tab:window._catalogHelpTab||null,
    helpOpen:document.body.classList.contains('catalog-help-open'),
    helpFs:document.body.classList.contains('catalog-help-fs'),
    userSelected:(document.getElementById('catalogHelpTabUser')||{}).getAttribute&&document.getElementById('catalogHelpTabUser').getAttribute('aria-selected'),
    updateSelected:(document.getElementById('catalogHelpTabUpdate')||{}).getAttribute&&document.getElementById('catalogHelpTabUpdate').getAttribute('aria-selected'),
    body:vis(body),
    legend:vis(legend),
    user:vis(user),
    update:vis(upd),
    legendTitles:titles(legend),
    userTitles:titles(user),
    updateTitles:titles(upd),
    openDetails: legend?legend.querySelectorAll('details[open]').length:0,
    sceneK: !!document.querySelector('#catalogHelpUser .catalog-help-k')
  };
})()
"""


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
        r = self.call("Runtime.evaluate", {"expression": expr, "returnByValue": True})
        if r.get("exceptionDetails"):
            raise RuntimeError(r["exceptionDetails"])
        return r.get("result", {}).get("value")


def port_open(p):
    s = socket.socket()
    s.settimeout(0.3)
    try:
        s.connect(("127.0.0.1", p))
        return True
    except Exception:
        return False
    finally:
        s.close()


def new_tab(url):
    try:
        return json.load(
            urllib.request.urlopen(
                urllib.request.Request(f"http://127.0.0.1:{PORT}/json/new?" + url, method="PUT")
            )
        )
    except Exception:
        return json.load(urllib.request.urlopen(f"http://127.0.0.1:{PORT}/json/new?" + url))


def shot(cdp, name):
    data = cdp.call("Page.captureScreenshot", {"format": "png"})
    raw = data.get("data")
    if raw:
        (SHOT / name).write_bytes(base64.b64decode(raw))


NEED_L = ["Symbols", "Fields", "Content window", "Menu windows", "Mode-changing buttons"]
NEED_U = [
    "Find a library by Search",
    "Filter by Keywords",
    "Open a card / expanded card",
    "Index Window vs Embed",
    "Sides vs Middle",
    "Flip",
    "History",
    "Profiles",
    "Customize separators",
    "Back from embed / preview",
]
NEED_G = ["Rebuild the catalog HTML", "After a new catalog drop", "Troubleshooting"]


def run(cdp, prefix, mobile=False):
    cdp.call(
        "Emulation.setDeviceMetricsOverride",
        {
            "width": 390 if mobile else 1400,
            "height": 844 if mobile else 900,
            "deviceScaleFactor": 1,
            "mobile": mobile,
        },
    )
    time.sleep(0.4)
    cdp.eval(
        "if(typeof setDisplayMode==='function')setDisplayMode('sides');"
        "if(typeof placeCatalogEdgeStack==='function')placeCatalogEdgeStack();"
    )
    time.sleep(0.25)
    cdp.eval("toggleCatalogHelp('legend')")
    time.sleep(0.3)
    p1 = cdp.eval(PROBE)
    cdp.eval(
        "var d=document.querySelector('#catalogHelpLegend details:not([open])'); if(d)d.open=true;"
        "var b=document.getElementById('catalogHelpBody'); if(b)b.scrollTop=b.scrollHeight;"
    )
    time.sleep(0.2)
    p1b = cdp.eval(PROBE)
    shot(cdp, f"{prefix}-legend-full.png")
    cdp.eval("toggleCatalogHelp('guide')")
    time.sleep(0.25)
    p2 = cdp.eval(PROBE)
    shot(cdp, f"{prefix}-guide-user.png")
    cdp.eval("setCatalogHelpTab('update')")
    time.sleep(0.2)
    p3 = cdp.eval(PROBE)
    shot(cdp, f"{prefix}-guide-update.png")
    cdp.eval("closeCatalogHelp()")
    return {"legend": p1, "legendScrolled": p1b, "guideUser": p2, "guideUpdate": p3}


def judge(label, d):
    fails = []
    lg = d["legend"]
    for t in NEED_L:
        if t not in (lg.get("legendTitles") or []):
            fails.append(f"{label} legend missing {t}")
    if (lg.get("legend") or {}).get("scroll", 0) < 400:
        fails.append(f"{label} legend not tall/scrollable {lg.get('legend')}")
    gu = d["guideUser"]
    if gu.get("tab") != "user" or gu.get("userSelected") != "true":
        fails.append(f"{label} default tab not User {gu.get('tab')} sel={gu.get('userSelected')}")
    for t in NEED_U:
        if t not in (gu.get("userTitles") or []):
            fails.append(f"{label} user missing {t}")
    if not gu.get("sceneK"):
        fails.append(f"{label} user missing Goal/Steps labels")
    if (gu.get("user") or {}).get("scroll", 0) < 600:
        fails.append(f"{label} user guide not scrollable {gu.get('user')}")
    up = d["guideUpdate"]
    if up.get("tab") != "update" or up.get("user") and up["user"].get("on"):
        if up.get("tab") != "update":
            fails.append(f"{label} update tab not selected")
    if (up.get("user") or {}).get("on"):
        fails.append(f"{label} user panel still visible on update tab")
    if not (up.get("update") or {}).get("on"):
        fails.append(f"{label} update panel hidden")
    for t in NEED_G:
        if t not in (up.get("updateTitles") or []):
            fails.append(f"{label} update missing {t}")
    return fails


def main():
    if not port_open(HTTP):
        raise SystemExit("http 8797 down")
    if not port_open(PORT):
        subprocess.Popen(
            [
                "chromium",
                f"--remote-debugging-port={PORT}",
                f"--user-data-dir={PROFILE}",
                "--headless=new",
                "--disable-gpu",
                "--no-first-run",
                "--no-default-browser-check",
                "about:blank",
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        for _ in range(50):
            if port_open(PORT):
                break
            time.sleep(0.2)
        else:
            raise SystemExit("chromium debug port failed")
        time.sleep(0.3)

    out = {}
    fails = []
    pages = [
        ("kontakt", f"http://127.0.0.1:{HTTP}/KONTAKT-CATALOG.html?copy=1", False),
        ("ds", f"http://127.0.0.1:{HTTP}/DS-CATALOG.html?copy=1", False),
        ("port", f"http://127.0.0.1:{HTTP}/KONTAKT-CATALOG-portable.html?copy=1", True),
    ]
    for name, url, mobile in pages:
        tab = new_tab("about:blank")
        cdp = CDP(tab["webSocketDebuggerUrl"])
        try:
            cdp.call("Page.enable")
            cdp.call("Runtime.enable")
            cdp.call("Page.navigate", {"url": url})
            for _ in range(250):
                try:
                    if cdp.eval("typeof toggleCatalogHelp==='function'"):
                        break
                except Exception:
                    pass
                time.sleep(0.2)
            else:
                fails.append(f"{name} JS not ready")
                continue
            time.sleep(0.4)
            out[name] = run(cdp, "copy-" + name, mobile=mobile)
            fails.extend(judge(name, out[name]))
        finally:
            try:
                urllib.request.urlopen(f"http://127.0.0.1:{PORT}/json/close/{tab['id']}")
            except Exception:
                pass
    OUT.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print("wrote", OUT)
    if fails:
        raise SystemExit("FAIL " + " | ".join(fails))
    print("PASS")


if __name__ == "__main__":
    main()
