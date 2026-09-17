#!/usr/bin/env python3
"""CDP 1400x900: Embed Index scroll + zero path icons; keep SK pair/name-click."""
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

OUT = Path("/home/phnx/kiro-kontakt-patch/kiro/_patch/verify_index_embed_scroll.json")
SHOT = Path("/home/phnx/kiro-kontakt-patch/kiro/_patch/ui-pos-shots")
PORT = 9551
HTTP_PORT = 8797
PROFILE = "/tmp/catalog-ix-embed-scroll"
SHOT.mkdir(parents=True, exist_ok=True)
os.makedirs(PROFILE, exist_ok=True)

URLS = [
    ("ds", f"http://127.0.0.1:{HTTP_PORT}/DS-CATALOG.html?ixscroll=1"),
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
    if(!el)return {on:false,x:0,y:0,w:0,h:0,parent:''};
    var cs=getComputedStyle(el), r=el.getBoundingClientRect();
    return {
      on:cs.display!=='none'&&r.width>8&&r.height>8,
      x:Math.round(r.x),y:Math.round(r.y),w:Math.round(r.width),h:Math.round(r.height),
      parent:el.parentElement?(el.parentElement.id||el.parentElement.tagName):''
    };
  }
  var sc=document.getElementById('searchChrome');
  var fw=document.getElementById('filterWrap');
  var main=document.getElementById('catalogMain');
  return {
    vw:window.innerWidth,vh:window.innerHeight,
    land:document.body.classList.contains('desk-landscape'),
    mid:document.body.classList.contains('display-middle'),
    sides:document.body.classList.contains('display-sides'),
    flip:document.body.classList.contains('sides-portrait-flip'),
    search:box(sc),kw:box(fw),main:box(main)
  };
})()
"""


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
    time.sleep(0.25)


def sides_three(g):
    if not (g and g.get("land") and g["search"]["on"] and g["kw"]["on"] and g["main"]["on"]):
        return False
    s, k, m = g["search"], g["kw"], g["main"]
    if s["w"] > g["vw"] * 0.72 or k["w"] > g["vw"] * 0.72:
        return False
    if abs(s["y"] - k["y"]) > 80:
        return False
    return s["h"] > 280 and k["h"] > 280 and m["w"] > 200 and m["h"] > 200


def middle_pair(g):
    if not (g and g.get("land") and g.get("mid") and g["search"]["on"] and g["kw"]["on"]):
        return False
    s, k = g["search"], g["kw"]
    if s["w"] > g["vw"] * 0.78 or k["w"] > g["vw"] * 0.78:
        return False
    return abs(s["y"] - k["y"]) < 60 and s["w"] > 180 and k["w"] > 180


def run_catalog(cdp, key, url):
    nav(cdp, url)
    set_view(cdp, 1400, 900)
    cdp.eval(
        "try{localStorage.removeItem((typeof desktopArrangeStoreKey==='function'&&desktopArrangeStoreKey())||'');}catch(e){}"
        "document.body.classList.remove('sides-portrait-flip','middle-kw-first');"
        "if(typeof setDisplayMode==='function')setDisplayMode('sides',{pick:true});"
    )
    both_on(cdp)
    sides = cdp.eval(GEO)

    embed = cdp.eval(
        r"""
(() => {
  var ix=document.getElementById('catalogIndex');
  var il=document.getElementById('catalogIndexList');
  if(!ix||!il)return {err:'no-index'};
  if(ix.classList.contains('is-collapsed')&&typeof toggleCatalogIndex==='function')toggleCatalogIndex();
  if(!ix.classList.contains('is-embedded')&&typeof toggleIndexEmbed==='function')toggleIndexEmbed();
  if(typeof stripIndexCardChrome==='function')stripIndexCardChrome(ix);
  if(typeof applyIndexScrollFit==='function')applyIndexScrollFit();
  var main=document.getElementById('catalogMain');
  var body=document.querySelector('#catalogMain > .catalog-body');
  var icons=[].slice.call(ix.querySelectorAll('.path-icon-btn,.path-action-row,.path-label,.path-fs-hit,.path-copy-hit,a.folder,svg.path-icon-glyph'));
  var vis=icons.filter(function(el){
    var cs=getComputedStyle(el);
    var r=el.getBoundingClientRect();
    return cs.display!=='none'&&cs.visibility!=='hidden'&&cs.opacity!=='0'&&r.width>2&&r.height>2;
  }).length;
  var a=il.querySelector('a')||ix;
  var r=a.getBoundingClientRect();
  var beforeMain=main?main.scrollTop:0;
  var beforeBody=body?body.scrollTop:0;
  var beforeList=il.scrollTop;
  var ev=new WheelEvent('wheel',{bubbles:true,cancelable:true,deltaY:420,deltaMode:0,clientX:r.left+20,clientY:r.top+20,view:window});
  (a||il).dispatchEvent(ev);
  var afterMain=main?main.scrollTop:0;
  var afterBody=body?body.scrollTop:0;
  var afterList=il.scrollTop;
  var moved=Math.abs(afterMain-beforeMain)>2||Math.abs(afterBody-beforeBody)>2||Math.abs(afterList-beforeList)>2;
  var ics=getComputedStyle(ix);
  var lcs=getComputedStyle(il);
  return {
    embed:ix.classList.contains('is-embedded'),
    collapsed:ix.classList.contains('is-collapsed'),
    parent:ix.parentElement&&(ix.parentElement.className||ix.parentElement.id||''),
    pathIconNodes:icons.length,
    pathIconVisible:vis,
    folderVisible:ix.querySelectorAll('.index a.folder,.index .folder').length,
    pathLabelVisible:[].slice.call(ix.querySelectorAll('.path-label')).filter(function(el){return getComputedStyle(el).display!=='none';}).length,
    liCount:il.querySelectorAll('li').length,
    ixH:Math.round(ix.getBoundingClientRect().height),
    listH:Math.round(il.getBoundingClientRect().height),
    ixOy:ics.overflowY,listOy:lcs.overflowY,
    mainSh:main?main.scrollHeight:0,mainCh:main?main.clientHeight:0,
    beforeMain:beforeMain,afterMain:afterMain,
    beforeBody:beforeBody,afterBody:afterBody,
    beforeList:beforeList,afterList:afterList,
    moved:moved
  };
})()
"""
    )
    shot(cdp, f"D1400-{key}-ix-embed-expanded.png")

    window = cdp.eval(
        r"""
(() => {
  var ix=document.getElementById('catalogIndex');
  var il=document.getElementById('catalogIndexList');
  if(!ix||!il)return {err:'no-index'};
  if(ix.classList.contains('is-embedded')&&typeof toggleIndexEmbed==='function')toggleIndexEmbed();
  if(ix.classList.contains('is-collapsed')&&typeof toggleCatalogIndex==='function')toggleCatalogIndex();
  if(typeof applyIndexScrollFit==='function')applyIndexScrollFit();
  var before=il.scrollTop;
  var ev=new WheelEvent('wheel',{bubbles:true,cancelable:true,deltaY:320,deltaMode:0,view:window});
  il.dispatchEvent(ev);
  if(il.scrollTop===before)il.scrollTop=before+80;
  var after=il.scrollTop;
  var cs=getComputedStyle(il);
  return {
    embed:ix.classList.contains('is-embedded'),
    listOy:cs.overflowY,
    before:before,after:after,
    canInner:il.scrollHeight>il.clientHeight+8,
    moved:Math.abs(after-before)>2
  };
})()
"""
    )
    shot(cdp, f"D1400-{key}-ix-window.png")

    cdp.eval(
        "if(!document.getElementById('catalogIndex').classList.contains('is-embedded')&&typeof toggleIndexEmbed==='function')toggleIndexEmbed();"
    )

    cdp.eval(
        "if(typeof togglePortraitSidesFlip==='function')togglePortraitSidesFlip();"
        "if(typeof applySidesCols==='function')applySidesCols();"
    )
    time.sleep(0.2)
    sides_flip = cdp.eval(GEO)
    cdp.eval(
        "if(document.body.classList.contains('sides-portrait-flip')&&typeof togglePortraitSidesFlip==='function')togglePortraitSidesFlip();"
        "if(typeof setDisplayMode==='function')setDisplayMode('middle',{pick:true});"
    )
    both_on(cdp)
    middle = cdp.eval(GEO)

    name = cdp.eval(
        r"""
(() => {
  if(typeof closeChosenPreview==='function')try{closeChosenPreview();}catch(e){}
  document.body.classList.remove('chosen-preview-open');
  var entry=document.querySelector('#catalogMain .entry:not(.highlight)')||document.querySelector('.entry');
  if(!entry)return {err:'no-entry'};
  var nm=entry.querySelector('h3.lib-name,.lib-name');
  if(!nm)return {err:'no-name',id:entry.id};
  nm.dispatchEvent(new MouseEvent('click',{bubbles:true,cancelable:true,view:window}));
  return {id:entry.id,preview:document.body.classList.contains('chosen-preview-open'),selected:entry.classList.contains('selected')};
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
  entry.dispatchEvent(new MouseEvent('click',{bubbles:true,cancelable:true,view:window,clientX:r.left+8,clientY:r.bottom-8}));
  return {id:entry.id,preview:document.body.classList.contains('chosen-preview-open'),selected:entry.classList.contains('selected')};
})()
"""
    )

    return {
        "sides": sides,
        "sidesFlip": sides_flip,
        "middle": middle,
        "embed": embed,
        "window": window,
        "nameClick": name,
        "emptyClick": empty,
        "pass": {
            "sides3": sides_three(sides),
            "sidesFlip": sides_three(sides_flip) and sides_flip.get("flip"),
            "middlePair": middle_pair(middle),
            "nameExpand": bool(name and name.get("preview")),
            "emptySelect": bool(empty and empty.get("selected") and not empty.get("preview")),
            "pathIconVisible0": bool(embed and embed.get("pathIconVisible") == 0),
            "pathLabelVisible0": bool(embed and embed.get("pathLabelVisible") == 0),
            "embedScroll": bool(embed and embed.get("moved")),
            "windowInner": bool(window and (window.get("moved") or window.get("canInner"))),
        },
    }


def ensure_http():
    try:
        urllib.request.urlopen(f"http://127.0.0.1:{HTTP_PORT}/DS-CATALOG.html", timeout=2).read(64)
        return None
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
            return httpd
        except Exception:
            time.sleep(0.1)
    raise SystemExit("http 8797 failed")


def main():
    ensure_http()
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
