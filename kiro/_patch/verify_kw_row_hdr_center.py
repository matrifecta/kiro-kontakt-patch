#!/usr/bin/env python3
"""Verify Keywords row order (Tap to add, Clear, groups) and header cluster centering."""
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

OUT = "/home/phnx/kiro-kontakt-patch/kiro/_patch/verify_kw_row_hdr_center.json"
SHOT = "/home/phnx/kiro-kontakt-patch/kiro/_patch/ui-pos-shots"
PORT = 9478
HTTP_PORT = 8798
ROOT = "/home/phnx/kiro-kontakt-patch/public/catalogs"
URL = "http://127.0.0.1:8798/DS-CATALOG.html?v=kw-row-hdr-center"
PROFILE = "/tmp/catalog-kw-row-hdr-center"
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
      id: el.id||'', tag: el.tagName, cls: (el.className||'').toString().slice(0,80),
      txt: (el.textContent||'').trim().slice(0,40),
      parent: el.parentElement ? (el.parentElement.id||el.parentElement.className||el.parentElement.tagName) : '',
      x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height),
      r: Math.round(r.right), cy: Math.round(r.y+r.height/2),
      disp: cs.display, vis: cs.visibility,
      shown: cs.display!=='none' && cs.visibility!=='hidden' && r.width>2 && r.height>2
    };
  }
  function overlap(a,b){
    if(!a||!b) return false;
    return !(a.r<=b.x || b.r<=a.x || (a.y+a.h)<=b.y || (b.y+b.h)<=a.y);
  }
  var hdr=document.querySelector('.catalog-header');
  var cluster=document.getElementById('hdrCluster');
  var miss=document.getElementById('clearMissBtn');
  var layouts=document.getElementById('layoutPresetsBtn');
  var search=document.getElementById('hdrSearchBtn');
  var kw=document.getElementById('hdrKwBtn');
  var tap=document.getElementById('tapAddBtnPanel');
  var cs=document.getElementById('catSwitch');
  var clr=cs ? cs.querySelector('.mode-btn.clear-all') : document.querySelector('.mode-btn.clear-all');
  var cats=cs ? [...cs.querySelectorAll('.cat-btn')].map(function(b){return (b.textContent||'').trim();}) : [];
  var kwBtns=cs ? [...cs.querySelectorAll('button')].map(function(b){
    return {id:b.id||'', txt:(b.textContent||'').trim(), cls:(b.className||'').toString()};
  }) : [];
  var order=kwBtns.map(function(b){
    if(b.id==='tapAddBtnPanel' || /tap-add/.test(b.cls)) return 'tap';
    if(/clear-all/.test(b.cls)) return 'clear';
    if(/cat-btn/.test(b.cls)) return 'cat:'+b.txt;
    return b.txt;
  });
  var hb=box(hdr), cb=box(cluster);
  var midHdr=hb ? hb.x + hb.w/2 : null;
  var midCl=cb ? cb.x + cb.w/2 : null;
  var tapB=box(tap), clrB=box(clr), firstCat=cs?box(cs.querySelector('.cat-btn')):null;
  var sameRow=true;
  if(tapB&&tapB.shown&&clrB&&clrB.shown){
    sameRow=sameRow && Math.abs(tapB.cy-clrB.cy)<18 && tapB.r<=clrB.x+2;
  }
  if(clrB&&clrB.shown&&firstCat&&firstCat.shown){
    sameRow=sameRow && Math.abs(clrB.cy-firstCat.cy)<18 && clrB.r<=firstCat.x+2;
  }
  var wrapStartsAfterLead=true;
  if(tapB&&clrB&&firstCat&&firstCat.shown&&clrB.shown){
    if(firstCat.y>clrB.y+12) wrapStartsAfterLead = tapB.y===clrB.y || Math.abs(tapB.cy-clrB.cy)<12;
  }
  return {
    display: typeof currentDisplay!=='undefined'?currentDisplay:'',
    middle: document.body.classList.contains('display-middle'),
    sides: document.body.classList.contains('display-sides'),
    kwOpen: document.body.classList.contains('kw-open'),
    vw: innerWidth, vh: innerHeight,
    hdrKids: hdr ? [...hdr.children].map(function(el){return el.id||el.className;}) : [],
    clusterKids: cluster ? [...cluster.children].map(function(el){return el.id||el.className;}) : [],
    hdr: hb, cluster: cb,
    midHdr: midHdr==null?null:Math.round(midHdr),
    midCluster: midCl==null?null:Math.round(midCl),
    centerDelta: (midHdr==null||midCl==null)?null:Math.abs(midHdr-midCl),
    miss: box(miss), layouts: box(layouts), search: box(search), kw: box(kw),
    overlapLayoutsMiss: overlap(box(layouts), box(miss)),
    overlapMissS: overlap(box(miss), box(search)),
    overlapSK: overlap(box(search), box(kw)),
    overlapLayoutsS: overlap(box(layouts), box(search)),
    tap: tapB, clear: clrB, firstCat: firstCat,
    order: order, cats: cats,
    tapParent: tap && tap.parentElement ? (tap.parentElement.className||tap.parentElement.id) : '',
    clearParent: clr && clr.parentElement ? (clr.parentElement.className||clr.parentElement.id) : '',
    catParent: cs ? (cs.id||'') : '',
    tapInCat: !!(cs && tap && cs.contains(tap)),
    clearInCat: !!(cs && clr && cs.contains(clr)),
    missInTools: !!(document.getElementById('filterKwTools') && miss && document.getElementById('filterKwTools').contains(miss)),
    sameRow: sameRow,
    wrapStartsAfterLead: wrapStartsAfterLead,
    orderOk: (function(){
      var iTap=order.indexOf('tap'), iClr=order.indexOf('clear');
      var iCat=order.findIndex(function(x){return String(x).indexOf('cat:')===0;});
      return iTap>=0 && iClr>=0 && iCat>=0 && iTap<iClr && iClr<iCat;
    })()
  };
})()
"""


def file_sync():
    errors = []
    for path in FILES:
        t = path.read_text(encoding="utf-8")
        if 'id="hdrCluster"' not in t:
            errors.append(path.name + ":no-hdrCluster")
        if "grid-template-columns:minmax(0,1fr) auto minmax(0,1fr)" not in t:
            errors.append(path.name + ":no-center-grid")
        if 'class="cat-switch-lead"' not in t:
            errors.append(path.name + ":no-lead")
        if "id=\"catSwitch\"><span class=\"cat-switch-lead\"><button type=\"button\" class=\"tap-add-btn\" id=\"tapAddBtnPanel\"" not in t:
            errors.append(path.name + ":tap-not-first-in-cat")
        if "mode-btn clear-all" not in t:
            errors.append(path.name + ":no-clear")
        lead_at = t.find('class="cat-switch-lead"')
        tap_at = t.find('id="tapAddBtnPanel"', lead_at)
        clr_at = t.find("mode-btn clear-all", lead_at)
        cat_at = t.find('class="cat-btn', lead_at)
        if not (0 <= lead_at < tap_at < clr_at < cat_at):
            errors.append(path.name + ":file-order")
        if 'id="filterKwTools"><button type="button" class="clear-miss-btn"' in t:
            errors.append(path.name + ":miss-in-tools")
        if t.count('id="clearMissBtn"') != 1:
            errors.append(path.name + ":clearMissCount")
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
    raise SystemExit("http 8798 failed")


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
                "!!(window.setDisplayMode&&document.getElementById('clearMissBtn')&&document.getElementById('catSwitch')&&document.querySelectorAll('.entry').length>5)",
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


def open_kw(cdp):
    cdp.eval(
        "if(typeof setMode==='function')setMode('search');"
        "var w=document.getElementById('filterWrap');"
        "if(w)w.classList.add('open');"
        "document.body.classList.add('kw-open');"
        "if(typeof ensureLayoutChromeBtns==='function')ensureLayoutChromeBtns();"
    )
    time.sleep(0.25)


def judge(name, st, errors, portrait=False):
    if not st:
        errors.append(name + ": no state")
        return
    if st.get("missInTools"):
        errors.append(name + ": miss still in tools")
    if not st.get("orderOk"):
        errors.append(f"{name}.order={st.get('order')}")
    if not st.get("tapInCat") or not st.get("clearInCat"):
        errors.append(f"{name}.notInCat tap={st.get('tapParent')} clr={st.get('clearParent')}")
    if portrait:
        if not (st.get("sameRow") or st.get("wrapStartsAfterLead")):
            errors.append(
                f"{name}.portraitWrap tap={st.get('tap')} clr={st.get('clear')} cat={st.get('firstCat')}"
            )
    elif not st.get("sameRow"):
        errors.append(
            f"{name}.notSameRow tap={st.get('tap')} clr={st.get('clear')} cat={st.get('firstCat')}"
        )
    delta = st.get("centerDelta")
    # Portrait title is its own row; cluster should still be centered on header width.
    limit = 8 if not portrait else 12
    if delta is None or delta > limit:
        errors.append(
            f"{name}.centerDelta={delta} hdr={st.get('hdr')} cluster={st.get('cluster')} kids={st.get('hdrKids')}"
        )
    if st.get("overlapLayoutsMiss") or st.get("overlapMissS") or st.get("overlapSK") or st.get("overlapLayoutsS"):
        errors.append(name + ": overlap")
    miss = st.get("miss") or {}
    layouts = st.get("layouts") or {}
    search = st.get("search") or {}
    if not miss.get("shown"):
        errors.append(name + ": clear-miss hidden")
    if not layouts.get("shown"):
        errors.append(name + ": layouts hidden")
    if not search.get("shown"):
        errors.append(name + ": S hidden")


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
    logf = open("/tmp/catalog-kw-row-hdr-center.log", "w")
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
        open_kw(cdp)
        st = cdp.eval(MEASURE)
        result["checks"]["sides1400"] = st
        judge("sides1400", st, errors)
        shot(cdp, "D1400-kw-row-hdr-center.png")

        cdp.eval("if(typeof setDisplayMode==='function')setDisplayMode('middle',{pick:true});")
        time.sleep(0.3)
        open_kw(cdp)
        st = cdp.eval(MEASURE)
        result["checks"]["middle1400"] = st
        judge("middle1400", st, errors)
        shot(cdp, "D1400-kw-row-hdr-center-middle.png")

        set_view(cdp, 900, 1400)
        cdp.eval(
            "window.dispatchEvent(new Event('orientationchange'));"
            "if(typeof setDisplayMode==='function')setDisplayMode('middle',{pick:true});"
        )
        time.sleep(0.35)
        open_kw(cdp)
        st = cdp.eval(MEASURE)
        result["checks"]["portrait900"] = st
        judge("portrait900", st, errors, portrait=True)
        shot(cdp, "D900-kw-row-hdr-center-portrait.png")
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
    print(json.dumps(result, indent=2)[:12000])
    if errors:
        sys.exit(1)


if __name__ == "__main__":
    main()
