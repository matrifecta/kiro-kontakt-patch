#!/usr/bin/env python3
"""CDP: KW ⛶ slot + collapsed/open Index stick while cards scroll."""
import json
import os
import socket
import subprocess
import sys
import time
import urllib.request
from urllib.parse import urlparse

OUT = "/home/phnx/kiro-kontakt-patch/kiro/_patch/verify_kw_fs_index_stick.json"
SHOTS = "/home/phnx/kiro-kontakt-patch/kiro/_patch/ui-pos-shots"
PORT = 9517
BASE = "http://127.0.0.1:8797"
PROFILE = "/tmp/catalog-kw-fs-index-stick"
os.makedirs(PROFILE, exist_ok=True)
os.makedirs(SHOTS, exist_ok=True)

URLS = [
    ("K", BASE + "/KONTAKT-CATALOG-portable.html?cb=kwfs-ix1"),
    ("DS", BASE + "/DS-CATALOG-portable.html?cb=kwfs-ix1"),
]


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


PROBE = r"""
(() => {
  function box(el){
    if(!el)return null;
    var cs=getComputedStyle(el);
    var r=el.getBoundingClientRect();
    return {
      id:el.id||'',
      txt:(el.getAttribute('aria-label')||el.textContent||'').replace(/\s+/g,' ').trim().slice(0,48),
      d:cs.display, v:cs.visibility, pos:cs.position, order:cs.order,
      on:!(cs.display==='none'||cs.visibility==='hidden'||el.hidden||r.width<2||r.height<2),
      l:Math.round(r.left), t:Math.round(r.top), r:Math.round(r.right), b:Math.round(r.bottom),
      w:Math.round(r.width), h:Math.round(r.height)
    };
  }
  var top=document.getElementById('filterTop');
  var kids=top?[].map.call(top.children,function(el){
    var b=box(el); b.id=el.id; return b;
  }):[];
  var visKids=kids.filter(function(k){return k.on;}).sort(function(a,b){return (a.t-b.t)||(a.l-b.l);});
  var pop=document.getElementById('kwStripMorePop');
  var popLabs=pop?[].map.call(pop.querySelectorAll('button'),function(b){return (b.textContent||'').trim();}):[];
  var cat=document.getElementById('catSwitch');
  var tap=document.getElementById('tapAddBtnPanel');
  var ix=document.getElementById('catalogIndex');
  var main=document.getElementById('catalogMain');
  var cb=main&&(main.querySelector(':scope > .catalog-body')||main.querySelector('.catalog-body'));
  var note=document.getElementById('catalogDocNote');
  var ir=ix?ix.getBoundingClientRect():null;
  var mr=main?main.getBoundingClientRect():null;
  var drift=ir&&mr?Math.round(ir.top-mr.top):null;
  return {
    vw:innerWidth, vh:innerHeight,
    portable:!!window.CATALOG_PORTABLE,
    phone:typeof isPhoneViewport==='function'?isPhoneViewport():null,
    desk:typeof displayIsDesktop==='function'?displayIsDesktop():null,
    cls:document.body.className,
    kwOrder:visKids.map(function(k){return k.id||k.txt;}),
    more:box(document.getElementById('kwStripMore')),
    fs:box(document.getElementById('kwStripFs')),
    clr:box(document.getElementById('kwStripClear')),
    popHidden:!(pop)||pop.hasAttribute('hidden'),
    popLabs:popLabs,
    popHasFs:popLabs.some(function(t){return /full/i.test(t);}),
    catsInPop:!!(pop&&cat&&pop.contains(cat)&&!pop.hasAttribute('hidden')),
    tapInCats:!!(tap&&cat&&cat.contains(tap)),
    catOn:!!(cat&&getComputedStyle(cat).display!=='none'),
    ix:box(ix),
    main:box(main),
    cb:box(cb),
    note:box(note),
    ixCollapsed:!!(ix&&ix.classList.contains('is-collapsed')),
    ixEmbed:!!(ix&&ix.classList.contains('is-embedded')),
    dock:document.body.classList.contains('index-window-open'),
    fill:document.body.classList.contains('index-fill-doc'),
    mainScroll:main?Math.round(main.scrollTop):0,
    cbScroll:cb?Math.round(cb.scrollTop):0,
    drift:drift,
    gapNote:ir&&note?Math.round(note.getBoundingClientRect().top-ir.bottom):null
  };
})()
"""


def wait_entries(cdp):
    for _ in range(80):
        try:
            n = cdp.eval("document.querySelectorAll('.entry').length")
        except Exception:
            n = 0
        if n and n > 8:
            return n
        time.sleep(0.25)
    return 0


def metrics(cdp, w, h, mobile, landscape=False):
    cdp.call(
        "Emulation.setDeviceMetricsOverride",
        {
            "width": w,
            "height": h,
            "deviceScaleFactor": 2 if mobile else 1,
            "mobile": mobile,
            "screenOrientation": (
                {"type": "landscapePrimary", "angle": 90}
                if landscape
                else {"type": "portraitPrimary", "angle": 0}
            ),
        },
    )
    cdp.eval(
        """
        window.dispatchEvent(new Event('resize'));
        window.dispatchEvent(new Event('orientationchange'));
        if(typeof syncDisplayForOrientation==='function')syncDisplayForOrientation();
        if(typeof syncIndexWindowDock==='function')syncIndexWindowDock();
        """
    )
    time.sleep(0.35)


def shot(cdp, name):
    data = cdp.call("Page.captureScreenshot", {"format": "png", "fromSurface": True}).get("data")
    if not data:
        return
    import base64

    path = os.path.join(SHOTS, name)
    with open(path, "wb") as f:
        f.write(base64.b64decode(data))


def click_id(cdp, eid):
    cdp.eval(
        f"""
        (function(){{
          var el=document.getElementById({eid!r});
          if(!el)return;
          el.dispatchEvent(new MouseEvent('click',{{bubbles:true,cancelable:true,composed:true}}));
        }})()
        """
    )
    time.sleep(0.25)


def scroll_cards(cdp, y):
    cdp.eval(
        f"""
        (function(){{
          var main=document.getElementById('catalogMain');
          var cb=main&&(main.querySelector(':scope > .catalog-body')||main.querySelector('.catalog-body'));
          if(cb)cb.scrollTop={y};
          if(main&&!document.body.classList.contains('index-window-open'))main.scrollTop={y};
          else if(main)main.scrollTop=0;
        }})()
        """
    )
    time.sleep(0.2)


def run_page(cdp, tag):
    out = {}
    metrics(cdp, 390, 844, True, False)
    wait_entries(cdp)
    time.sleep(0.4)
    # Keywords on
    cdp.eval(
        """
        (function(){
          if(typeof setDisplayMode==='function')setDisplayMode('sides',{pick:true});
          if(window.matchMedia&&window.matchMedia('(orientation:portrait)').matches){
            if(typeof setDisplayMode==='function')setDisplayMode('middle',{pick:true});
            if(typeof portableCoerceMiddleMenu==='function')portableCoerceMiddleMenu('keywords');
          }else if(typeof expandKwMenu==='function')expandKwMenu();
          if(typeof syncIndexWindowDock==='function')syncIndexWindowDock();
        })()
        """
    )
    time.sleep(0.3)
    out["portrait_kw"] = cdp.eval(PROBE)
    click_id(cdp, "kwStripMore")
    out["portrait_kw_open"] = cdp.eval(PROBE)
    shot(cdp, f"{tag}390-kw-fs-slot.png")
    click_id(cdp, "kwStripMore")  # close

    # Index collapsed stick
    cdp.eval(
        """
        (function(){
          var ix=document.getElementById('catalogIndex');
          if(ix&&ix.classList.contains('is-embedded')&&typeof toggleIndexEmbed==='function')toggleIndexEmbed();
          if(ix&&!ix.classList.contains('is-collapsed')&&typeof toggleCatalogIndex==='function')toggleCatalogIndex();
          if(typeof syncIndexWindowDock==='function')syncIndexWindowDock();
        })()
        """
    )
    time.sleep(0.25)
    scroll_cards(cdp, 0)
    out["port_ix_collapsed_top"] = cdp.eval(PROBE)
    scroll_cards(cdp, 420)
    out["port_ix_collapsed_scrolled"] = cdp.eval(PROBE)
    shot(cdp, f"{tag}390-ix-collapsed-scroll.png")

    # Index open stick
    click_id(cdp, "catalogIndexToggle")
    time.sleep(0.3)
    scroll_cards(cdp, 0)
    out["port_ix_open_top"] = cdp.eval(PROBE)
    scroll_cards(cdp, 420)
    out["port_ix_open_scrolled"] = cdp.eval(PROBE)
    shot(cdp, f"{tag}390-ix-open-scroll.png")

    # Landscape one-menu Sides fill-to-doc (Search on, KW off)
    metrics(cdp, 844, 390, True, True)
    time.sleep(0.4)
    cdp.eval(
        """
        (function(){
          if(typeof setDisplayMode==='function')setDisplayMode('sides',{pick:true});
          var k=document.getElementById('hdrKwBtn');
          if(k&&k.classList.contains('is-on')&&typeof toggleHdrKw==='function')toggleHdrKw();
          var s=document.getElementById('hdrSearchBtn');
          if(s&&!s.classList.contains('is-on')&&typeof toggleHdrSearch==='function')toggleHdrSearch();
          var ix=document.getElementById('catalogIndex');
          if(ix&&ix.classList.contains('is-embedded')&&typeof toggleIndexEmbed==='function')toggleIndexEmbed();
          if(ix&&ix.classList.contains('is-collapsed')&&typeof toggleCatalogIndex==='function')toggleCatalogIndex();
          if(typeof syncIndexWindowDock==='function')syncIndexWindowDock();
          if(typeof applyIndexFillDocStyles==='function')applyIndexFillDocStyles();
        })()
        """
    )
    time.sleep(0.4)
    out["land_fill_open"] = cdp.eval(PROBE)
    shot(cdp, f"{tag}844-ix-fill-open.png")
    click_id(cdp, "catalogIndexToggle")
    time.sleep(0.3)
    scroll_cards(cdp, 0)
    out["land_fill_collapsed_top"] = cdp.eval(PROBE)
    scroll_cards(cdp, 280)
    out["land_fill_collapsed_scrolled"] = cdp.eval(PROBE)
    shot(cdp, f"{tag}844-ix-collapsed-scroll.png")
    return out


def summarize(tag, d):
    checks = []
    kw = d["portrait_kw"]
    vis = [x for x in kw["kwOrder"] if x in ("kwStripClear", "kwStripMore", "kwStripFs")]
    checks.append(("kw_order_clear_more_fs", vis[-3:] == ["kwStripClear", "kwStripMore", "kwStripFs"] or vis == ["kwStripClear", "kwStripMore", "kwStripFs"], vis))
    checks.append(("fs_visible", bool(kw["fs"] and kw["fs"]["on"]), kw.get("fs")))
    checks.append(("more_left_of_fs", bool(kw["more"] and kw["fs"] and kw["more"]["on"] and kw["fs"]["on"] and kw["more"]["l"] < kw["fs"]["l"]), (kw["more"], kw["fs"])))
    pop = d["portrait_kw_open"]
    checks.append(("pop_no_fullscreen", pop["popHasFs"] is False, pop["popLabs"]))
    checks.append(("cats_or_tap_reachable", pop["catsInPop"] or pop["catOn"] or pop["tapInCats"], {"catsInPop": pop["catsInPop"], "catOn": pop["catOn"], "labs": pop["popLabs"]}))

    for key, top_key in (
        ("port_ix_collapsed_scrolled", "port_ix_collapsed_top"),
        ("port_ix_open_scrolled", "port_ix_open_top"),
        ("land_fill_collapsed_scrolled", "land_fill_collapsed_top"),
    ):
        snap = d[key]
        top = d[top_key]
        drift = snap.get("drift")
        topd = top.get("drift")
        delta = None if drift is None or topd is None else abs(drift - topd)
        checks.append(
            (
                key + "_drift0",
                isinstance(delta, int) and delta <= 2 and isinstance(drift, int) and abs(drift) <= 8,
                {
                    "drift": drift,
                    "top": topd,
                    "delta": delta,
                    "dock": snap.get("dock"),
                    "fill": snap.get("fill"),
                    "collapsed": snap.get("ixCollapsed"),
                    "cbScroll": snap.get("cbScroll"),
                    "mainScroll": snap.get("mainScroll"),
                },
            )
        )
    fill = d["land_fill_open"]
    checks.append(("land_fill_on_when_open", fill.get("fill") is True and fill.get("ixCollapsed") is False, {"fill": fill.get("fill"), "collapsed": fill.get("ixCollapsed"), "gap": fill.get("gapNote")}))
    col = d["land_fill_collapsed_scrolled"]
    checks.append(("land_fill_off_when_collapsed", col.get("fill") is False, {"fill": col.get("fill"), "dock": col.get("dock")}))
    failed = [c for c in checks if not c[1]]
    return {"tag": tag, "ok": not failed, "failed": failed, "checks": checks}


def main():
    subprocess.run(["pkill", "-f", f"remote-debugging-port={PORT}"], check=False)
    time.sleep(0.3)
    chrome = next(
        p
        for p in ("/usr/lib/chromium/chromium", "/usr/bin/chromium", "/usr/bin/google-chrome")
        if os.path.exists(p)
    )
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
            "--ozone-override-screen-size=390,844",
            "--use-angle=swiftshader-webgl",
            "about:blank",
        ],
        stdout=open("/tmp/catalog-kw-fs-index-stick.log", "w"),
        stderr=subprocess.STDOUT,
    )
    try:
        for _ in range(60):
            try:
                urllib.request.urlopen(f"http://127.0.0.1:{PORT}/json/version", timeout=1).read()
                break
            except Exception:
                time.sleep(0.25)
        else:
            raise SystemExit("cdp failed")
        report = {"pages": {}, "summaries": []}
        for tag, url in URLS:
            try:
                tab = json.load(
                    urllib.request.urlopen(
                        urllib.request.Request(f"http://127.0.0.1:{PORT}/json/new?" + url, method="PUT")
                    )
                )
            except Exception:
                tab = json.load(urllib.request.urlopen(f"http://127.0.0.1:{PORT}/json/new?" + url))
            cdp = CDP(tab["webSocketDebuggerUrl"])
            cdp.call("Page.enable")
            cdp.call("Runtime.enable")
            cdp.call("Page.navigate", {"url": url})
            time.sleep(1.2)
            wait_entries(cdp)
            data = run_page(cdp, tag)
            report["pages"][tag] = data
            report["summaries"].append(summarize(tag, data))
        report["ok"] = all(s["ok"] for s in report["summaries"])
        PathWrite = open(OUT, "w")
        json.dump(report, PathWrite, indent=2)
        PathWrite.close()
        print("OK" if report["ok"] else "FAIL", OUT)
        for s in report["summaries"]:
            print(s["tag"], "ok" if s["ok"] else "FAIL")
            for c in s["checks"]:
                if not c[1]:
                    print("  fail", c[0], c[2] if len(c) > 2 else "")
        sys.exit(0 if report["ok"] else 2)
    finally:
        proc.terminate()


if __name__ == "__main__":
    main()
