#!/usr/bin/env python3
"""CDP: Middle one-menu, Flip spatial, FS AC list persists."""
import json
import os
import socket
import subprocess
import sys
import time
import urllib.request
from urllib.parse import urlparse

OUT = "/home/phnx/kiro-kontakt-patch/kiro/_patch/verify_portable_middle_flip.json"
PORT = 9495
URL = "http://127.0.0.1:8797/DS-CATALOG-portable.html?cb=mid-flip2"
PROFILE = "/tmp/catalog-portable-middle-flip"
os.makedirs(PROFILE, exist_ok=True)


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

    def eval(self, expr, await_promise=True):
        r = self.call(
            "Runtime.evaluate",
            {"expression": expr, "awaitPromise": await_promise, "returnByValue": True},
        )
        if r.get("exceptionDetails"):
            raise RuntimeError(r["exceptionDetails"])
        return r.get("result", {}).get("value")


SNAP = r"""
(() => {
  function vis(el){
    if(!el)return {on:false};
    var cs=getComputedStyle(el);
    var r=el.getBoundingClientRect();
    var hidden=cs.display==='none'||cs.visibility==='hidden'||el.hidden||r.width<2||r.height<2;
    return {on:!hidden,l:Math.round(r.left),t:Math.round(r.top),w:Math.round(r.width),h:Math.round(r.height)};
  }
  var ac=document.getElementById('acList');
  var sb=document.getElementById('hdrSearchBtn');
  var kb=document.getElementById('hdrKwBtn');
  var wrap=document.getElementById('hdrMenuBtns');
  var order=wrap?[].map.call(wrap.querySelectorAll('.hdr-menu-btn'),function(b){return b.id;}).join(','):'';
  return {
    vw:innerWidth,vh:innerHeight,cls:document.body.className,
    cur:typeof currentDisplay!=='undefined'?currentDisplay:'',
    search:vis(document.getElementById('searchChrome')),
    kw:vis(document.getElementById('filterWrap')),
    main:vis(document.getElementById('catalogMain')),
    acOpen:!!(ac&&ac.classList.contains('open')&&ac.getBoundingClientRect().height>8),
    acH:ac?Math.round(ac.getBoundingClientRect().height):0,
    acHtml:ac?(ac.innerHTML||'').length:0,
    flip:document.body.classList.contains('sides-portrait-flip'),
    btnOrder:order,
    sOn:!!(sb&&sb.classList.contains('is-on')),
    kOn:!!(kb&&kb.classList.contains('is-on'))
  };
})()
"""


def wait_entries(cdp):
    for _ in range(80):
        try:
            n = cdp.eval("document.querySelectorAll('.entry').length", await_promise=False)
        except Exception:
            n = 0
        if n and n > 8:
            return
        time.sleep(0.25)


def shown(box):
    return bool(box and box.get("on"))


def main():
    urllib.request.urlopen("http://127.0.0.1:8797/DS-CATALOG-portable.html", timeout=2).read(64)
    subprocess.run(["pkill", "-f", f"remote-debugging-port={PORT}"], check=False)
    time.sleep(0.25)
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
    logf = open("/tmp/catalog-portable-middle-flip.log", "w")
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
    out = {"ok": True, "errors": []}
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
        cdp.call(
            "Emulation.setDeviceMetricsOverride",
            {"width": 1400, "height": 900, "deviceScaleFactor": 1, "mobile": False},
        )
        cdp.call("Page.navigate", {"url": URL})
        wait_entries(cdp)

        cdp.eval(
            """
            if(typeof setDisplayMode==='function')setDisplayMode('sides',{pick:true});
            document.body.classList.remove('search-chrome-collapsed','kw-open','ac-fs-open','kw-fs-open','sides-portrait-flip');
            document.body.classList.add('kw-chrome-collapsed');
            var fw=document.getElementById('filterWrap'); if(fw)fw.classList.remove('open');
            if(typeof syncHdrMenuBtns==='function')syncHdrMenuBtns();
            """
        )
        time.sleep(0.2)
        out["s_only"] = cdp.eval(SNAP, await_promise=False)

        cdp.eval("if(typeof togglePortraitSidesFlip==='function')togglePortraitSidesFlip();")
        time.sleep(0.2)
        out["s_flip"] = cdp.eval(SNAP, await_promise=False)

        cdp.eval(
            """
            document.body.classList.remove('search-chrome-collapsed','kw-chrome-collapsed','ac-fs-open','kw-fs-open');
            var fw=document.getElementById('filterWrap');
            if(fw){fw.classList.add('open');document.body.classList.add('kw-open');}
            if(typeof syncHdrMenuBtns==='function')syncHdrMenuBtns();
            """
        )
        time.sleep(0.2)
        out["sk_flip"] = cdp.eval(SNAP, await_promise=False)

        cdp.eval("if(typeof togglePortraitSidesFlip==='function')togglePortraitSidesFlip();")
        time.sleep(0.15)
        out["sk_unflip"] = cdp.eval(SNAP, await_promise=False)

        cdp.eval(
            """
            document.body.classList.add('search-chrome-collapsed');
            document.body.classList.remove('kw-chrome-collapsed','sides-portrait-flip');
            var fw=document.getElementById('filterWrap');
            if(fw){fw.classList.add('open');document.body.classList.add('kw-open');}
            if(typeof togglePortraitSidesFlip==='function')togglePortraitSidesFlip();
            """
        )
        time.sleep(0.2)
        out["k_flip"] = cdp.eval(SNAP, await_promise=False)

        cdp.eval(
            """
            if(typeof togglePortraitSidesFlip==='function')togglePortraitSidesFlip();
            document.body.classList.remove('search-chrome-collapsed','kw-open','ac-fs-open','kw-fs-open','sides-portrait-flip');
            document.body.classList.add('kw-chrome-collapsed');
            var fw=document.getElementById('filterWrap'); if(fw)fw.classList.remove('open');
            if(typeof toggleAcFullscreen==='function')toggleAcFullscreen();
            if(typeof showAc==='function')showAc('',{force:true});
            """
        )
        time.sleep(0.25)
        out["fs_before"] = cdp.eval(SNAP, await_promise=False)
        cdp.eval(
            """
            var main=document.getElementById('catalogMain')||document.body;
            main.dispatchEvent(new PointerEvent('pointerdown',{bubbles:true,cancelable:true,composed:true}));
            document.body.dispatchEvent(new PointerEvent('pointerdown',{bubbles:true,cancelable:true,composed:true}));
            var kw=document.getElementById('filterWrap');
            if(kw)kw.dispatchEvent(new PointerEvent('pointerdown',{bubbles:true,cancelable:true,composed:true}));
            var inp=document.getElementById('searchInput');
            if(inp){inp.blur(); inp.dispatchEvent(new FocusEvent('focusout',{bubbles:true}));}
            """
        )
        time.sleep(0.25)
        out["fs_after_outside"] = cdp.eval(SNAP, await_promise=False)

        cdp.call(
            "Emulation.setDeviceMetricsOverride",
            {"width": 390, "height": 844, "deviceScaleFactor": 2, "mobile": True},
        )
        cdp.eval(
            """
            window.dispatchEvent(new Event('resize'));
            if(typeof setDisplayMode==='function')setDisplayMode('middle',{pick:true});
            """
        )
        time.sleep(0.3)
        out["mid"] = cdp.eval(SNAP, await_promise=False)
        cdp.eval("if(typeof toggleHdrKw==='function')toggleHdrKw();")
        time.sleep(0.2)
        out["mid_k"] = cdp.eval(SNAP, await_promise=False)
        cdp.eval("if(typeof toggleHdrSearch==='function')toggleHdrSearch();")
        time.sleep(0.2)
        out["mid_s"] = cdp.eval(SNAP, await_promise=False)
        cdp.eval(
            """
            document.body.classList.remove('search-chrome-collapsed','kw-chrome-collapsed');
            var fw=document.getElementById('filterWrap');
            if(fw){fw.classList.add('open');document.body.classList.add('kw-open');}
            if(typeof portableCoerceMiddleMenu==='function')portableCoerceMiddleMenu('search');
            """
        )
        time.sleep(0.2)
        out["mid_coerce"] = cdp.eval(SNAP, await_promise=False)

        cdp.eval(
            """
            if(typeof setDisplayMode==='function')setDisplayMode('sides',{pick:true});
            document.body.classList.remove('search-chrome-collapsed','kw-chrome-collapsed','ac-fs-open','kw-fs-open');
            var fw=document.getElementById('filterWrap');
            if(fw){fw.classList.add('open');document.body.classList.add('kw-open');}
            """
        )
        time.sleep(0.25)
        out["p390_sk"] = cdp.eval(SNAP, await_promise=False)

        cdp.call(
            "Emulation.setDeviceMetricsOverride",
            {"width": 1400, "height": 900, "deviceScaleFactor": 1, "mobile": False},
        )
        cdp.call("Page.navigate", {"url": "http://127.0.0.1:8797/KONTAKT-CATALOG-portable.html?cb=mid-flip2"})
        wait_entries(cdp)
        cdp.call(
            "Emulation.setDeviceMetricsOverride",
            {"width": 390, "height": 844, "deviceScaleFactor": 2, "mobile": True},
        )
        cdp.eval(
            """
            window.dispatchEvent(new Event('resize'));
            if(typeof setDisplayMode==='function')setDisplayMode('middle',{pick:true});
            if(typeof portableCoerceMiddleMenu==='function')portableCoerceMiddleMenu('keywords');
            """
        )
        time.sleep(0.25)
        out["k_mid"] = cdp.eval(SNAP, await_promise=False)

        def chk(cond, msg):
            if cond:
                out["errors"].append(msg)

        s = out.get("s_only") or {}
        fl = out.get("s_flip") or {}
        chk(not (shown(s.get("search")) and shown(s.get("main"))), "S-only missing Search|Content")
        chk(fl.get("btnOrder") != "hdrSearchBtn,hdrKwBtn", f"Flip reordered S/K buttons: {fl.get('btnOrder')}")
        if shown(s.get("search")) and shown(s.get("main")) and shown(fl.get("search")) and shown(fl.get("main")):
            chk(
                (fl["search"].get("l") or 0) <= (fl["main"].get("l") or 0),
                "Flip Search|Content did not put catalog on the left",
            )
            chk(s.get("search", {}).get("l") == fl.get("search", {}).get("l"), "Flip did not move Search pane")

        sk = out.get("sk_flip") or {}
        chk(not (shown(sk.get("search")) and shown(sk.get("kw"))), "S+K after Flip missing both menus")
        chk(shown(sk.get("main")), "S+K Flip should still hide catalog")
        if shown(sk.get("search")) and shown(sk.get("kw")):
            chk(
                (sk["search"].get("l") or 0) < (sk["kw"].get("l") or 0),
                "S+K Flip should put Keywords left of Search spatially",
            )

        kfl = out.get("k_flip") or {}
        if shown(kfl.get("kw")) and shown(kfl.get("main")):
            chk(
                (kfl["kw"].get("l") or 0) >= (kfl["main"].get("l") or 0),
                "K-only Flip did not put Keywords on the left",
            )

        fs0 = out.get("fs_before") or {}
        fs1 = out.get("fs_after_outside") or {}
        chk(not fs0.get("acOpen"), "Search FS list not open before click-away")
        chk(not fs1.get("acOpen"), "Search FS list collapsed after click-away")
        chk((fs1.get("acH") or 0) < 200, "Search FS list short after click-away")

        mid = out.get("mid") or {}
        chk(shown(mid.get("search")) and shown(mid.get("kw")), "Middle still stacking Search+Keywords")
        mk = out.get("mid_k") or {}
        chk(shown(mk.get("kw")), "Middle K did not show Keywords")
        chk(shown(mk.get("search")), "Middle K still showing Search")
        ms = out.get("mid_s") or {}
        chk(shown(ms.get("search")), "Middle S did not show Search")
        chk(shown(ms.get("kw")), "Middle S still showing Keywords")
        mc = out.get("mid_coerce") or {}
        chk(shown(mc.get("search")) and shown(mc.get("kw")), "Middle coerce still stacking")

        p3 = out.get("p390_sk") or {}
        chk(not (shown(p3.get("search")) and shown(p3.get("kw"))), "390 Sides S+K should still dual/stack")

        km = out.get("k_mid") or {}
        chk(not shown(km.get("kw")), "KONTAKT Middle K missing Keywords")
        chk(shown(km.get("search")), "KONTAKT Middle K still showing Search")

        out["ok"] = len(out["errors"]) == 0
        json.dump(out, open(OUT, "w"), indent=2)
        print(json.dumps({k: out[k] for k in ("ok", "errors") if k in out}, indent=2))
        for key in (
            "s_only",
            "s_flip",
            "sk_flip",
            "k_flip",
            "fs_before",
            "fs_after_outside",
            "mid",
            "mid_k",
            "mid_s",
            "mid_coerce",
            "p390_sk",
            "k_mid",
        ):
            v = out.get(key) or {}
            print(
                f"{key}: s={shown(v.get('search'))} { (v.get('search') or {}).get('l') }x{(v.get('search') or {}).get('w')} "
                f"kw={shown(v.get('kw'))} {(v.get('kw') or {}).get('l')} main={shown(v.get('main'))} "
                f"acOpen={v.get('acOpen')} acH={v.get('acH')} flip={v.get('flip')} order={v.get('btnOrder')} "
                f"sOn={v.get('sOn')} kOn={v.get('kOn')}"
            )
        if not out["ok"]:
            sys.exit(1)
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=3)
        except Exception:
            proc.kill()


if __name__ == "__main__":
    main()
