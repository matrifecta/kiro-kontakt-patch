#!/usr/bin/env python3
"""CDP: portrait Middle S/K alone, Index embed chrome=0, folder glyph 26-28px."""
import base64
import json
import os
import socket
import subprocess
import time
import urllib.request
from pathlib import Path
from urllib.parse import urlparse

OUT = Path("/home/phnx/kiro-kontakt-patch/kiro/_patch/verify_middle_menu_index_folder.json")
SHOT = Path("/home/phnx/kiro-kontakt-patch/kiro/_patch/ui-pos-shots")
PORT = 9542
HTTP_PORT = 8797
PROFILE = "/tmp/catalog-middle-menu-ix-folder"
SHOT.mkdir(parents=True, exist_ok=True)
os.makedirs(PROFILE, exist_ok=True)

URLS = [
    ("kontakt", f"http://127.0.0.1:{HTTP_PORT}/KONTAKT-CATALOG.html?mmif=1"),
    ("ds", f"http://127.0.0.1:{HTTP_PORT}/DS-CATALOG.html?mmif=1"),
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
                "!!(document.getElementById('catalogIndex')&&document.querySelectorAll('.entry').length>2&&typeof toggleHdrSearch==='function')"
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
    time.sleep(0.35)


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


MENUS = r"""
(() => {
  var sc=document.getElementById('searchChrome');
  var fw=document.getElementById('filterWrap');
  var main=document.getElementById('catalogMain');
  function vis(el){
    if(!el)return {on:false,w:0,h:0,disp:'',row:'',col:''};
    var cs=getComputedStyle(el);
    var r=el.getBoundingClientRect();
    var on=cs.display!=='none'&&cs.visibility!=='hidden'&&r.width>8&&r.height>8;
    return {on:on,w:Math.round(r.width),h:Math.round(r.height),disp:cs.display,row:cs.gridRow,col:cs.gridColumn,top:Math.round(r.top)};
  }
  var ac=document.getElementById('acList')||document.getElementById('acShell');
  return {
    mid:document.body.classList.contains('display-middle'),
    sides:document.body.classList.contains('display-sides'),
    searchCol:document.body.classList.contains('search-chrome-collapsed'),
    kwCol:document.body.classList.contains('kw-chrome-collapsed'),
    kwOpen:document.body.classList.contains('kw-open'),
    portrait:!!(window.matchMedia&&window.matchMedia('(orientation:portrait)').matches),
    desk:!!(window.matchMedia&&window.matchMedia('(min-width:900px)').matches),
    vw:window.innerWidth,vh:window.innerHeight,
    search:vis(sc),
    kw:vis(fw),
    main:vis(main),
    acOn:!!(ac&&getComputedStyle(ac).display!=='none'&&ac.getBoundingClientRect().height>8)
  };
})()
"""

INDEX_EMBED = r"""
(() => {
  if(typeof setDisplayMode==='function')setDisplayMode('sides',{pick:true});
  var ix=document.getElementById('catalogIndex');
  if(!ix)return {err:'no-index'};
  ix.classList.add('is-embedded');
  ix.classList.remove('is-collapsed');
  if(typeof parkCatalogDocNote==='function')parkCatalogDocNote();
  if(typeof stripIndexCardChrome==='function')stripIndexCardChrome(ix);
  if(typeof applyIndexScrollFit==='function')applyIndexScrollFit();
  if(typeof syncIndexWindowDock==='function')syncIndexWindowDock();
  if(typeof syncIndexEmbedBtn==='function')syncIndexEmbedBtn();
  var sels='.path-action-row,.path-icon-btn,.path-label,.path-fs-hit,.path-copy-hit,.fav-btn,a.folder';
  var nodes=ix.querySelectorAll(sels);
  var vis=0,painted=0;
  nodes.forEach(function(el){
    var cs=getComputedStyle(el);
    var r=el.getBoundingClientRect();
    if(cs.display!=='none'||cs.visibility!=='hidden')vis++;
    if(r.width>2&&r.height>2&&cs.visibility!=='hidden'&&cs.display!=='none')painted++;
  });
  var labels=[].slice.call(ix.querySelectorAll('.path-label')).filter(function(el){
    var cs=getComputedStyle(el);var r=el.getBoundingClientRect();
    return cs.display!=='none'&&r.height>2;
  }).length;
  return {
    embed:ix.classList.contains('is-embedded'),
    collapsed:ix.classList.contains('is-collapsed'),
    parent:ix.parentElement&&(ix.parentElement.className||ix.parentElement.id),
    chromeCount:nodes.length,
    chromeVisible:vis,
    chromePainted:painted,
    pathLabelsVisible:labels,
    nameLinks:ix.querySelectorAll('#catalogIndexList a[href^="#item"]').length
  };
})()
"""

GLYPHS = r"""
(() => {
  if(typeof bindCatalogPathHits==='function')bindCatalogPathHits();
  var entry=document.querySelector('.entry:not(.is-hidden)')||document.querySelector('.entry');
  var path=entry&&entry.querySelector('.path');
  function glyph(sel){
    var btn=path&&path.querySelector(sel);
    var svg=btn&&btn.querySelector('svg.path-icon-glyph');
    if(!svg)return null;
    var r=svg.getBoundingClientRect();
    return {w:Math.round(r.width*10)/10,h:Math.round(r.height*10)/10};
  }
  return {
    folder:glyph('a.folder,.path-icon-btn.folder'),
    copy:glyph('.path-copy-hit'),
    fs:glyph('.path-fs-hit')
  };
})()
"""


def measure_menus(cdp):
    return cdp.eval(MENUS)


def run_catalog(cdp, key, url):
    nav(cdp, url)
    set_view(cdp, 900, 1400)
    cdp.eval(
        "if(typeof setDisplayMode==='function')setDisplayMode('middle',{pick:true});"
        "if(typeof collapseSearchMenu==='function')collapseSearchMenu();"
        "if(typeof collapseKwMenu==='function')collapseKwMenu();"
        "if(typeof syncHdrMenuBtns==='function')syncHdrMenuBtns();"
        "if(typeof applySidesCols==='function')applySidesCols();"
    )
    time.sleep(0.25)
    both_off = measure_menus(cdp)
    shot(cdp, f"D900-{key}-middle-both-off.png")

    cdp.eval(
        "if(typeof toggleHdrSearch==='function')toggleHdrSearch();"
        "if(typeof applySidesCols==='function')applySidesCols();"
    )
    time.sleep(0.25)
    s_alone = measure_menus(cdp)
    shot(cdp, f"D900-{key}-middle-s-alone.png")

    cdp.eval(
        "if(typeof collapseSearchMenu==='function')collapseSearchMenu();"
        "if(typeof toggleHdrKw==='function')toggleHdrKw();"
        "if(typeof applySidesCols==='function')applySidesCols();"
    )
    time.sleep(0.25)
    k_alone = measure_menus(cdp)
    shot(cdp, f"D900-{key}-middle-k-alone.png")

    cdp.eval(
        "if(typeof toggleHdrSearch==='function')toggleHdrSearch();"
        "if(typeof applySidesCols==='function')applySidesCols();"
    )
    time.sleep(0.25)
    both_on = measure_menus(cdp)
    shot(cdp, f"D900-{key}-middle-both-on.png")

    set_view(cdp, 1400, 900)
    cdp.eval(
        "if(typeof setDisplayMode==='function')setDisplayMode('middle',{pick:true});"
        "if(typeof collapseSearchMenu==='function')collapseSearchMenu();"
        "if(typeof collapseKwMenu==='function')collapseKwMenu();"
        "if(typeof toggleHdrSearch==='function')toggleHdrSearch();"
        "if(typeof applySidesCols==='function')applySidesCols();"
    )
    time.sleep(0.25)
    land_s = measure_menus(cdp)

    cdp.eval(
        "if(typeof collapseSearchMenu==='function')collapseSearchMenu();"
        "if(typeof toggleHdrKw==='function')toggleHdrKw();"
        "if(typeof applySidesCols==='function')applySidesCols();"
    )
    time.sleep(0.25)
    land_k = measure_menus(cdp)

    set_view(cdp, 900, 1400)
    ix = cdp.eval(INDEX_EMBED)
    shot(cdp, f"D900-{key}-index-embed-ext.png")

    glyphs = cdp.eval(GLYPHS)

    def ok_alone(m, which):
        if not m or not m.get("mid"):
            return False
        if which == "s":
            return bool(m["search"]["on"] and not m["kw"]["on"] and m["search"]["h"] > 80)
        return bool(m["kw"]["on"] and not m["search"]["on"] and m["kw"]["h"] > 80)

    folder_w = (glyphs or {}).get("folder") or {}
    copy_w = (glyphs or {}).get("copy") or {}
    fw = folder_w.get("w") or 0
    cw = copy_w.get("w") or 0
    folder_ok = 25.5 <= fw <= 29.5 and fw > cw + 1.5

    return {
        "url": url,
        "portrait": {
            "bothOff": both_off,
            "sAlone": s_alone,
            "kAlone": k_alone,
            "bothOn": both_on,
            "pass": {
                "contentOnly": bool(both_off and not both_off["search"]["on"] and not both_off["kw"]["on"]),
                "sAlone": ok_alone(s_alone, "s"),
                "kAlone": ok_alone(k_alone, "k"),
                "bothOn": bool(both_on and both_on["search"]["on"] and both_on["kw"]["on"]),
            },
        },
        "landscape": {
            "sAlone": land_s,
            "kAlone": land_k,
            "pass": {
                "sAlone": ok_alone(land_s, "s"),
                "kAlone": ok_alone(land_k, "k"),
            },
        },
        "indexEmbed": ix,
        "glyphs": glyphs,
        "folderOk": folder_ok,
        "indexOk": bool(ix and ix.get("chromeVisible") == 0 and ix.get("chromePainted") == 0 and ix.get("pathLabelsVisible") == 0),
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
        p = rec["portrait"]["pass"]
        l = rec["landscape"]["pass"]
        if not p["contentOnly"]:
            fails.append(f"{key}: portrait content-only")
        if not p["sAlone"]:
            fails.append(f"{key}: portrait S alone")
        if not p["kAlone"]:
            fails.append(f"{key}: portrait K alone")
        if not p["bothOn"]:
            fails.append(f"{key}: portrait both")
        if not l["sAlone"]:
            fails.append(f"{key}: landscape S alone")
        if not l["kAlone"]:
            fails.append(f"{key}: landscape K alone")
        if not rec["indexOk"]:
            fails.append(f"{key}: index chrome {rec.get('indexEmbed')}")
        if not rec["folderOk"]:
            fails.append(f"{key}: folder {rec.get('glyphs')}")
    if fails:
        raise SystemExit("FAIL " + " | ".join(fails))
    print("PASS")


if __name__ == "__main__":
    main()
