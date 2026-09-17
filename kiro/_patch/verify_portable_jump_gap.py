#!/usr/bin/env python3
"""CDP: desktop jump vs portable jump, pane gutters, in-pane cards, tile covers."""
import json
import os
import socket
import subprocess
import sys
import time
import urllib.request
from urllib.parse import urlparse

OUT = "/home/phnx/kiro-kontakt-patch/kiro/_patch/verify_portable_jump_gap.json"
PORT = 9491
DESK = "http://127.0.0.1:8797/DS-CATALOG.html?cb=jump-gap-desk"
PORTABLE = "http://127.0.0.1:8797/DS-CATALOG-portable.html?cb=jump-gap-port"
PROFILE = "/tmp/catalog-portable-jump-gap"
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
  function rb(el){
    if(!el)return null;
    var cs=getComputedStyle(el);
    if(cs.display==='none')return {disp:'none',w:0,h:0};
    var r=el.getBoundingClientRect();
    return {l:Math.round(r.left),t:Math.round(r.top),r:Math.round(r.right),b:Math.round(r.bottom),w:Math.round(r.width),h:Math.round(r.height),disp:cs.display,pos:cs.position,z:cs.zIndex};
  }
  var main=document.getElementById('catalogMain');
  var stack=document.getElementById('catalogJumpStack');
  var bot=document.querySelector('#catalogJumpStack a.bottom, a.bottom');
  var topB=document.querySelector('#catalogJumpStack a.top, a.top');
  var sc=document.getElementById('searchChrome');
  var fw=document.getElementById('filterWrap');
  var entries=[].slice.call(document.querySelectorAll('#catalogMain .entry:not(.highlight):not(.is-hidden)')).filter(function(el){return el.getBoundingClientRect().height>8;}).slice(0,2);
  var cards=entries.map(function(el){
    var cover=el.querySelector('.cover'), img=cover&&cover.querySelector('img');
    var er=rb(el), cr=rb(cover), ir=rb(img);
    var cs=el?getComputedStyle(el):null;
    var padL=cs?parseFloat(cs.paddingLeft)||0:0, padR=cs?parseFloat(cs.paddingRight)||0:0;
    return {
      entry:er, cover:cr, img:ir,
      contentW:er?Math.round(er.w-padL-padR):null,
      ratio:(cr&&cr.w)?+(cr.h/cr.w).toFixed(3):null,
      imgFit:img?getComputedStyle(img).objectFit:'',
      imgOverflow:!!(ir&&cr&&(ir.l<cr.l-1||ir.r>cr.r+1||ir.t<cr.t-1||ir.b>cr.b+1)),
      inMain:!!(er&&main&&er.l>=main.getBoundingClientRect().left-1&&er.r<=main.getBoundingClientRect().right+1)
    };
  });
  var mr=rb(main), sr=rb(sc), kr=rb(fw), br=rb(bot), tr=rb(topB), st=rb(stack);
  var hit=null;
  if(bot&&br&&br.w>2){
    var el=document.elementFromPoint(br.l+br.w/2, br.t+br.h/2);
    hit=el?(el.closest('a.bottom,a.top,#catalogJumpStack')? (el.className||el.id||el.tagName): (el.id||el.className||el.tagName)):null;
  }
  return {
    vw:innerWidth, vh:innerHeight, cls:document.body.className,
    colGap:getComputedStyle(document.body).columnGap,
    rowGap:getComputedStyle(document.body).rowGap,
    main:mr, search:sr, kw:kr, stack:st, bot:br, top:tr,
    gapSM:(sr&&mr&&sr.w>8&&mr.w>8)?Math.round(mr.l-sr.r):null,
    gapMK:(mr&&kr&&mr.w>8&&kr.w>8)?Math.round(kr.l-mr.r):null,
    gapSK:(sr&&kr&&sr.w>8&&kr.w>8)?Math.round(kr.l-sr.r):null,
    jumpInMain:!!(mr&&st&&st.w>2&&st.l>=mr.l-2&&st.r<=mr.r+2&&st.b<=mr.b+2&&st.t>=mr.t-2),
    jumpClick:hit,
    cards:cards,
    childOverflow:!!(main&&[].some.call(main.querySelectorAll('.entry:not(.highlight):not(.is-hidden)'),function(el){var r=el.getBoundingClientRect(),m=main.getBoundingClientRect();return r.width>8&&(r.left<m.left-2||r.right>m.right+2);}))
  };
})()
"""


def wait_entries(cdp, n=8):
    for _ in range(80):
        try:
            c = cdp.eval("document.querySelectorAll('.entry').length", await_promise=False)
        except Exception:
            c = 0
        if c and c > n:
            return
        time.sleep(0.25)


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
    logf = open("/tmp/catalog-portable-jump-gap.log", "w")
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

        cdp.call("Page.navigate", {"url": DESK})
        wait_entries(cdp)
        cdp.eval(
            "if(typeof setDisplayMode==='function')setDisplayMode('sides',{pick:true});if(typeof placeCatalogJumpStack==='function')placeCatalogJumpStack();"
        )
        time.sleep(0.25)
        out["desktop1400"] = cdp.eval(SNAP, await_promise=False)

        cdp.call("Page.navigate", {"url": PORTABLE})
        wait_entries(cdp)
        cdp.eval(
            """
            if(typeof setDisplayMode==='function')setDisplayMode('sides',{pick:true});
            document.body.classList.add('search-chrome-collapsed');
            document.body.classList.remove('kw-chrome-collapsed');
            var fw=document.getElementById('filterWrap');
            if(fw){fw.classList.add('open');document.body.classList.add('kw-open');}
            if(typeof placePortableHandles==='function')placePortableHandles();
            if(typeof placeCatalogJumpStack==='function')placeCatalogJumpStack();
            """
        )
        time.sleep(0.3)
        out["p1400_kw"] = cdp.eval(SNAP, await_promise=False)

        cdp.eval(
            """
            document.body.classList.remove('search-chrome-collapsed','kw-open');
            document.body.classList.add('kw-chrome-collapsed');
            var fw=document.getElementById('filterWrap');
            if(fw)fw.classList.remove('open');
            if(typeof placePortableHandles==='function')placePortableHandles();
            if(typeof placeCatalogJumpStack==='function')placeCatalogJumpStack();
            """
        )
        time.sleep(0.25)
        out["p1400_scat"] = cdp.eval(SNAP, await_promise=False)

        cdp.eval(
            """
            if(typeof setDisplayMode==='function')setDisplayMode('fs');
            document.body.classList.remove('search-chrome-collapsed','kw-chrome-collapsed');
            if(typeof setAcFullscreen==='function')setAcFullscreen(true);
            if(typeof setKwFullscreen==='function')setKwFullscreen(true);
            if(typeof updateDualState==='function')updateDualState();
            if(typeof placePortableHandles==='function')placePortableHandles();
            if(typeof placeCatalogJumpStack==='function')placeCatalogJumpStack();
            """
        )
        time.sleep(0.3)
        out["p1400_full"] = cdp.eval(SNAP, await_promise=False)

        cdp.eval("if(typeof setDisplayMode==='function')setDisplayMode('sides',{pick:true});")
        cdp.call(
            "Emulation.setDeviceMetricsOverride",
            {"width": 390, "height": 844, "deviceScaleFactor": 2, "mobile": True},
        )
        cdp.eval(
            """
            window.dispatchEvent(new Event('resize'));
            if(typeof setDisplayMode==='function')setDisplayMode('sides',{pick:true});
            document.body.classList.remove('search-chrome-collapsed');
            document.body.classList.add('kw-chrome-collapsed');
            var fw=document.getElementById('filterWrap');
            if(fw){fw.classList.remove('open');document.body.classList.remove('kw-open');}
            if(typeof placePortableHandles==='function')placePortableHandles();
            if(typeof placeCatalogJumpStack==='function')placeCatalogJumpStack();
            """
        )
        time.sleep(0.35)
        out["p390_sides"] = cdp.eval(SNAP, await_promise=False)

        def chk(cond, msg):
            if cond:
                out["errors"].append(msg)

        d = out.get("desktop1400") or {}
        chk(not (d.get("bot") and d["bot"].get("w", 0) > 8), "desktop missing bottom jump")
        chk(not d.get("jumpInMain"), "desktop jump not in catalogMain")

        sc = out.get("p1400_scat") or {}
        gap = sc.get("gapSM")
        chk(gap is None or not (4 <= gap <= 12), f"1400 S+catalog gapSM={gap}")
        chk(not sc.get("jumpInMain"), "portable 1400 S jump not in catalogMain")
        chk(not (sc.get("bot") and sc["bot"].get("w", 0) > 8), "portable 1400 S missing bottom")
        chk(sc.get("jumpClick") is None, f"portable 1400 S jump not clickable hit={sc.get('jumpClick')}")

        kw = out.get("p1400_kw") or {}
        chk(kw.get("childOverflow"), "1400 KW cards overflow catalogMain")
        chk(not kw.get("jumpInMain"), "portable 1400 KW jump not in catalogMain")
        for i, c in enumerate(kw.get("cards") or []):
            chk(not c.get("inMain"), f"1400 KW card{i} not in main")
            chk(c.get("imgOverflow"), f"1400 KW card{i} img overflow")
            chk(c.get("imgFit") != "cover", f"1400 KW card{i} object-fit={c.get('imgFit')}")
            ratio = c.get("ratio") or 0
            chk(abs(ratio - 4 / 3) > 0.12, f"1400 KW card{i} ratio={ratio}")
            cw, ew = (c.get("cover") or {}).get("w"), c.get("contentW")
            chk(cw and ew and abs(cw - ew) > 8, f"1400 KW cover w={cw} contentW={ew}")

        fs = out.get("p1400_full") or {}
        fsg = fs.get("gapSK")
        chk(fsg is not None and not (4 <= fsg <= 12), f"1400 Full dual gapSK={fsg}")
        chk(bool(fs.get("bot") and fs["bot"].get("disp") not in (None, "none") and fs["bot"].get("w", 0) > 8 and not fs.get("main")), "full still showing jump")

        p3 = out.get("p390_sides") or {}
        chk(not (p3.get("bot") and p3["bot"].get("w", 0) > 8), "390 missing bottom jump")
        chk(not p3.get("jumpInMain"), "390 jump not in catalogMain")
        chk(p3.get("childOverflow"), "390 cards overflow catalogMain")
        for i, c in enumerate(p3.get("cards") or []):
            chk(not c.get("inMain"), f"390 card{i} not in main")
            chk(c.get("imgOverflow"), f"390 card{i} img overflow")
            chk(c.get("imgFit") != "cover", f"390 card{i} object-fit={c.get('imgFit')}")
            ratio = c.get("ratio") or 0
            chk(abs(ratio - 4 / 3) > 0.12, f"390 card{i} ratio={ratio}")

        out["ok"] = len(out["errors"]) == 0
        json.dump(out, open(OUT, "w"), indent=2)
        print(json.dumps(out, indent=2))
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
