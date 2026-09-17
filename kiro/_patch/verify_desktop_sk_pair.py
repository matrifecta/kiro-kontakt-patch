#!/usr/bin/env python3
"""CDP 1400x900: Sides/Middle SK columns + card name expand."""
import base64
import json
import os
import socket
import subprocess
import time
import urllib.request
from pathlib import Path
from urllib.parse import urlparse

OUT = Path("/home/phnx/kiro-kontakt-patch/kiro/_patch/verify_desktop_sk_pair.json")
SHOT = Path("/home/phnx/kiro-kontakt-patch/kiro/_patch/ui-pos-shots")
PORT = 9548
HTTP_PORT = 8797
PROFILE = "/tmp/catalog-desk-sk-pair"
SHOT.mkdir(parents=True, exist_ok=True)
os.makedirs(PROFILE, exist_ok=True)

URLS = [
    ("ds", f"http://127.0.0.1:{HTTP_PORT}/DS-CATALOG.html?skpair=1"),
    ("kontakt", f"http://127.0.0.1:{HTTP_PORT}/KONTAKT-CATALOG.html?skpair=1"),
]


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
    for _ in range(150):
        try:
            n = cdp.eval(
                "!!(document.getElementById('catalogIndex')&&document.querySelectorAll('.entry').length>2&&typeof setDisplayMode==='function')"
            )
        except Exception:
            n = False
        if n:
            return
        time.sleep(0.2)
    raise SystemExit("catalog JS not ready")


def set_view(cdp, w, h):
    cdp.call(
        "Emulation.setDeviceMetricsOverride",
        {
            "width": w,
            "height": h,
            "deviceScaleFactor": 1,
            "mobile": False,
            "screenOrientation": {
                "type": "portraitPrimary" if h > w else "landscapePrimary",
                "angle": 0 if h > w else 90,
            },
        },
    )
    time.sleep(0.4)


def shot(cdp, name):
    data = cdp.call("Page.captureScreenshot", {"format": "png"})
    raw = data.get("data")
    path = SHOT / name
    if raw:
        path.write_bytes(base64.b64decode(raw))
    return str(path)


def nav(cdp, url):
    cdp.call("Page.enable")
    cdp.call("Runtime.enable")
    cdp.call("Page.navigate", {"url": url})
    time.sleep(0.8)
    wait_ready(cdp)


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


GEO = r"""
(() => {
  function box(el){
    if(!el)return {on:false,x:0,y:0,w:0,h:0,parent:'',disp:'',row:'',col:''};
    var cs=getComputedStyle(el), r=el.getBoundingClientRect();
    return {
      on:cs.display!=='none'&&r.width>8&&r.height>8,
      x:Math.round(r.x),y:Math.round(r.y),w:Math.round(r.width),h:Math.round(r.height),
      parent:el.parentElement?(el.parentElement.id||el.parentElement.tagName):'',
      disp:cs.display,row:cs.gridRowStart+'/'+cs.gridRowEnd,col:cs.gridColumnStart+'/'+cs.gridColumnEnd
    };
  }
  var sc=document.getElementById('searchChrome');
  var fw=document.getElementById('filterWrap');
  var main=document.getElementById('catalogMain');
  var bcs=getComputedStyle(document.body);
  return {
    vw:window.innerWidth,vh:window.innerHeight,
    land:document.body.classList.contains('desk-landscape'),
    mid:document.body.classList.contains('display-middle'),
    sides:document.body.classList.contains('display-sides'),
    flip:document.body.classList.contains('sides-portrait-flip'),
    sCol:document.body.classList.contains('search-chrome-collapsed'),
    kCol:document.body.classList.contains('kw-chrome-collapsed'),
    kwOpen:document.body.classList.contains('kw-open'),
    bodyDisp:bcs.display,bodyDir:bcs.flexDirection,bodyCols:bcs.gridTemplateColumns,
    search:box(sc),kw:box(fw),main:box(main)
  };
})()
"""


def geo(cdp):
    return cdp.eval(GEO)


def both_on(cdp):
    cdp.eval(
        "if(typeof expandSearchMenu==='function')expandSearchMenu();"
        "else if(typeof toggleHdrSearch==='function'&&document.body.classList.contains('search-chrome-collapsed'))toggleHdrSearch();"
        "if(typeof expandKwMenu==='function')expandKwMenu();"
        "else if(typeof toggleHdrKw==='function'&&document.body.classList.contains('kw-chrome-collapsed'))toggleHdrKw();"
        "document.body.classList.remove('search-chrome-collapsed','kw-chrome-collapsed');"
        "var fw=document.getElementById('filterWrap');if(fw){fw.classList.add('open');document.body.classList.add('kw-open');}"
        "if(typeof applySidesCols==='function')applySidesCols();"
        "if(typeof syncHdrMenuBtns==='function')syncHdrMenuBtns();"
    )
    time.sleep(0.3)


def sides_three(g):
    if not (g and g.get("land") and g["search"]["on"] and g["kw"]["on"] and g["main"]["on"]):
        return False
    s, k, m = g["search"], g["kw"], g["main"]
    # full-height-ish side columns; menus not stacked as full-width bands
    if s["w"] > g["vw"] * 0.72 or k["w"] > g["vw"] * 0.72:
        return False
    if abs(s["y"] - k["y"]) > 80:
        return False
    if s["h"] < 280 or k["h"] < 280:
        return False
    # content between or at least not the only full-width strip above both
    return m["w"] > 200 and m["h"] > 200


def middle_pair(g):
    if not (g and g.get("land") and g.get("mid") and g["search"]["on"] and g["kw"]["on"]):
        return False
    s, k = g["search"], g["kw"]
    if s["w"] > g["vw"] * 0.78 or k["w"] > g["vw"] * 0.78:
        return False
    return abs(s["y"] - k["y"]) < 60 and s["w"] > 180 and k["w"] > 180


def one_menu(g, which):
    if which == "s":
        return bool(g["search"]["on"] and not g["kw"]["on"] and g["main"]["on"])
    return bool(g["kw"]["on"] and not g["search"]["on"] and g["main"]["on"])


def run_catalog(cdp, key, url):
    nav(cdp, url)
    set_view(cdp, 1400, 900)
    cdp.eval(
        "try{localStorage.removeItem((typeof desktopArrangeStoreKey==='function'&&desktopArrangeStoreKey())||'');}catch(e){}"
        "document.body.classList.remove('sides-portrait-flip','middle-kw-first');"
        "if(typeof setDisplayMode==='function')setDisplayMode('sides',{pick:true});"
    )
    both_on(cdp)
    sides = geo(cdp)
    shot(cdp, f"D1400-{key}-skpair-sides.png")

    cdp.eval(
        "if(typeof togglePortraitSidesFlip==='function')togglePortraitSidesFlip();"
        "if(typeof applySidesCols==='function')applySidesCols();"
    )
    time.sleep(0.25)
    sides_flip = geo(cdp)
    shot(cdp, f"D1400-{key}-skpair-sides-flip.png")

    cdp.eval(
        "if(document.body.classList.contains('sides-portrait-flip')&&typeof togglePortraitSidesFlip==='function')togglePortraitSidesFlip();"
        "if(typeof setDisplayMode==='function')setDisplayMode('middle',{pick:true});"
    )
    both_on(cdp)
    middle = geo(cdp)
    shot(cdp, f"D1400-{key}-skpair-middle.png")

    cdp.eval(
        "if(typeof collapseKwMenu==='function')collapseKwMenu();"
        "if(typeof applySidesCols==='function')applySidesCols();"
    )
    time.sleep(0.2)
    mid_s = geo(cdp)
    cdp.eval(
        "if(typeof expandKwMenu==='function')expandKwMenu();"
        "if(typeof collapseSearchMenu==='function')collapseSearchMenu();"
        "if(typeof applySidesCols==='function')applySidesCols();"
    )
    time.sleep(0.2)
    mid_k = geo(cdp)

    both_on(cdp)
    name = cdp.eval(
        r"""
(() => {
  if(typeof closeChosenPreview==='function')try{closeChosenPreview();}catch(e){}
  document.body.classList.remove('chosen-preview-open');
  var entry=document.querySelector('#catalogMain .entry:not(.highlight)')||document.querySelector('.entry');
  if(!entry)return {err:'no-entry'};
  var name=entry.querySelector('h3.lib-name,.lib-name');
  if(!name)return {err:'no-name',id:entry.id};
  name.dispatchEvent(new MouseEvent('click',{bubbles:true,cancelable:true,view:window}));
  return {
    id:entry.id,
    preview:document.body.classList.contains('chosen-preview-open'),
    selected:entry.classList.contains('selected')
  };
})()
"""
    )
    empty = cdp.eval(
        r"""
(() => {
  if(typeof closeChosenPreview==='function')try{closeChosenPreview();}catch(e){}
  document.body.classList.remove('chosen-preview-open');
  var entry=document.querySelector('#catalogMain .entry:not(.highlight)')||document.querySelector('.entry');
  if(!entry)return {err:'no-entry'};
  var r=entry.getBoundingClientRect();
  var ev=new MouseEvent('click',{bubbles:true,cancelable:true,view:window,clientX:r.left+8,clientY:r.bottom-8});
  entry.dispatchEvent(ev);
  return {
    id:entry.id,
    preview:document.body.classList.contains('chosen-preview-open'),
    selected:entry.classList.contains('selected')
  };
})()
"""
    )

    return {
        "sides": sides,
        "sidesFlip": sides_flip,
        "middle": middle,
        "middleS": mid_s,
        "middleK": mid_k,
        "nameClick": name,
        "emptyClick": empty,
        "pass": {
            "sides3": sides_three(sides),
            "sidesFlip": sides_three(sides_flip) and sides_flip.get("flip"),
            "middlePair": middle_pair(middle),
            "middleS": one_menu(mid_s, "s"),
            "middleK": one_menu(mid_k, "k"),
            "nameExpand": bool(name and name.get("preview")),
            "emptySelect": bool(empty and empty.get("selected") and not empty.get("preview")),
        },
    }


def main():
    if not port_open(HTTP_PORT):
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
        for _ in range(40):
            if port_open(PORT):
                break
            time.sleep(0.2)
        else:
            raise SystemExit("chromium debug port failed")
        time.sleep(0.4)

    out = {}
    for key, url in URLS:
        print("verify", url, flush=True)
        tab = new_tab(url)
        cdp = CDP(tab["webSocketDebuggerUrl"])
        try:
            out[key] = run_catalog(cdp, key, url)
        finally:
            try:
                urllib.request.urlopen(f"http://127.0.0.1:{PORT}/json/close/{tab['id']}")
            except Exception:
                pass

    OUT.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(json.dumps(out, indent=2))
    fails = []
    for key, rec in out.items():
        for name, ok in rec["pass"].items():
            if not ok:
                fails.append(f"{key}:{name}")
    if fails:
        raise SystemExit("FAIL " + " | ".join(fails))
    print("PASS")


if __name__ == "__main__":
    main()
