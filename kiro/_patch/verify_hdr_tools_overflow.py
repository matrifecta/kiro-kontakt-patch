#!/usr/bin/env python3
"""CDP: desktop portrait header overflow pyramid + landscape restore."""
import base64
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

OUT = Path("/home/phnx/kiro-kontakt-patch/kiro/_patch/verify_hdr_tools_overflow.json")
SHOT = Path("/home/phnx/kiro-kontakt-patch/kiro/_patch/ui-pos-shots")
PORT = 9591
HTTP = 8797
ROOT = Path("/home/phnx/kiro-kontakt-patch/public/catalogs")
PROFILE = "/tmp/catalog-hdr-tools-ovf"
SHOT.mkdir(parents=True, exist_ok=True)
os.makedirs(PROFILE, exist_ok=True)

MARK = "fix-HDR-TOOLS-OVERFLOW-v1"
KEEP = (
    "c00e3e",
    "index-embed-alignment-clash",
    "fix-INDEX-EMBED-SEP-v2",
)
DESK = [ROOT / "KONTAKT-CATALOG.html", ROOT / "DS-CATALOG.html"]
PORTABLES = [ROOT / "KONTAKT-CATALOG-portable.html", ROOT / "DS-CATALOG-portable.html"]


def integrity():
    rows = []
    ok = True
    for p in DESK:
        t = p.read_text(encoding="utf-8")
        row = {"file": p.name, "endswith": t.strip().endswith("</html>"), "size": len(t.encode("utf-8")), MARK: MARK in t}
        for k in KEEP:
            row[k] = k in t
            if k not in t:
                ok = False
        if not row["endswith"] or row["size"] < 100000 or not row[MARK]:
            ok = False
        if t.count("function syncHdrPortraitOverflow(") != 1:
            ok = False
            row["syncFn"] = t.count("function syncHdrPortraitOverflow(")
        rows.append(row)
    for p in PORTABLES:
        t = p.read_text(encoding="utf-8")
        row = {"file": p.name, "endswith": t.strip().endswith("</html>"), MARK: MARK in t, "sep": "fix-INDEX-EMBED-SEP-v2" in t}
        if MARK in t:
            ok = False
        if not row["endswith"] or not row["sep"]:
            ok = False
        rows.append(row)
    return {"ok": ok, "files": rows}


def ensure_http():
    url = f"http://127.0.0.1:{HTTP}/DS-CATALOG.html"
    try:
        urllib.request.urlopen(url, timeout=1).read(64)
        return None
    except Exception:
        pass
    os.chdir(ROOT)

    class H(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a):
            pass

    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", HTTP), H)
    httpd.allow_reuse_address = True
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    for _ in range(40):
        try:
            urllib.request.urlopen(url, timeout=1).read(64)
            return httpd
        except Exception:
            time.sleep(0.1)
    raise SystemExit("http 8797 failed")


class Ws:
    def __init__(self, url):
        u = urlparse(url)
        host, port = u.hostname, u.port or 80
        path = u.path + (("?" + u.query) if u.query else "")
        key = base64.b64encode(os.urandom(16)).decode()
        s = socket.create_connection((host, port), timeout=30)
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


def nav(cdp, url):
    cdp.call("Page.navigate", {"url": url})
    for _ in range(80):
        try:
            n = cdp.eval(
                "!!(window.setDisplayMode&&document.getElementById('hdrCluster')&&document.querySelectorAll('.entry').length>3)"
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
            "mobile": False,
            "screenOrientation": {
                "type": "portraitPrimary" if portrait else "landscapePrimary",
                "angle": 0 if portrait else 90,
            },
        },
    )
    time.sleep(0.45)


def shot(cdp, name):
    data = cdp.call("Page.captureScreenshot", {"format": "png"}).get("data", "")
    path = SHOT / name
    path.write_bytes(base64.b64decode(data))
    return str(path)


JS_STATE = r"""
(() => {
  function box(el){
    if(!el) return null;
    var r=el.getBoundingClientRect(), cs=getComputedStyle(el);
    return {
      id: el.id||'', txt: (el.textContent||'').trim().slice(0,48),
      parent: el.parentElement ? (el.parentElement.id||'') : '',
      x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height),
      r: Math.round(r.right), b: Math.round(r.bottom), cy: Math.round(r.y+r.height/2),
      disp: cs.display, vis: cs.visibility,
      shown: cs.display!=='none' && cs.visibility!=='hidden' && r.width>1 && r.height>1
    };
  }
  function overlap(a,b){
    if(!a||!b||!a.shown||!b.shown) return false;
    return !(a.r<=b.x+1 || b.r<=a.x+1 || a.b<=b.y+1 || b.b<=a.y+1);
  }
  if(typeof setDisplayMode==='function') setDisplayMode('sides',{pick:true});
  if(typeof syncHdrPortraitOverflow==='function') syncHdrPortraitOverflow();
  var hdr=document.querySelector('.catalog-header');
  var title=document.querySelector('.catalog-header h1');
  var cluster=document.getElementById('hdrCluster');
  var py=document.getElementById('hdrToolsMore');
  var row2=document.getElementById('hdrToolsRow2');
  var theme=document.getElementById('themePicker');
  var miss=document.getElementById('clearMissBtn');
  var edit=document.getElementById('layoutEditBtn');
  var layouts=document.getElementById('layoutPresetsBtn')||document.getElementById('layoutPresets');
  var profiles=document.getElementById('hdrProfilesBtn');
  var scale=document.getElementById('uiScale');
  var s=document.getElementById('hdrSearchBtn');
  var k=document.getElementById('hdrKwBtn');
  var sides=document.querySelector('.display-btn[data-display="sides"]');
  var middle=document.querySelector('.display-btn[data-display="middle"]');
  var ix=document.getElementById('catalogIndex');
  var card=document.querySelector('#catalogMain .entry:not(.is-hidden)');
  var tb=box(title), cb=box(cluster), th=box(theme), pyb=box(py);
  if(tb&&title){tb.clip=title.scrollWidth>title.clientWidth+2; tb.sw=title.scrollWidth; tb.cw=title.clientWidth;}
  var rowItems=[];
  if(row2){
    rowItems=[...row2.children].filter(function(el){return box(el)&&box(el).shown;}).map(function(el){
      var b=box(el); b.id=el.id||''; return b;
    });
  }
  return {
    w: innerWidth, h: innerHeight,
    desk: typeof displayIsDesktop==='function' && displayIsDesktop(),
    portrait: !!(window.matchMedia&&window.matchMedia('(orientation:portrait)').matches),
    portable: !!window.CATALOG_PORTABLE,
    collapse: document.body.classList.contains('hdr-tools-collapse'),
    open: document.body.classList.contains('hdr-tools-open'),
    missPop: document.body.classList.contains('hdr-tools-miss-pop'),
    title: tb, cluster: cb, pyramid: pyb, theme: th,
    miss: box(miss), customize: box(edit), layouts: box(layouts),
    profiles: box(profiles), scale: box(scale),
    s: box(s), k: box(k), sides: box(sides), middle: box(middle),
    row2: box(row2), rowItems: rowItems,
    overlapTitle: overlap(tb, cb) || overlap(tb, th) || overlap(tb, pyb) || overlap(tb, box(s)),
    titleClip: !!(tb&&tb.clip),
    themeRightmost: th && cb ? Math.abs(th.r - cb.r) <= 8 || th.r >= (cb.r - 2) : false,
    pyramidLeftOfCluster: pyb && pyb.shown && s && s.shown ? pyb.x < s.x : null,
    ixEmbed: !!(ix&&ix.classList.contains('is-embedded')),
    ixCollapsed: !!(ix&&ix.classList.contains('is-collapsed')),
    cardTop: card ? Math.round(card.getBoundingClientRect().top) : null,
    hdrBottom: hdr ? Math.round(hdr.getBoundingClientRect().bottom) : null
  };
})()
"""

JS_EXPAND = r"""
(() => {
  if(typeof toggleHdrToolsMore==='function') toggleHdrToolsMore(true);
  else if(typeof syncHdrPortraitOverflow==='function'){
    document.body.classList.add('hdr-tools-open');
    syncHdrPortraitOverflow();
  }
  return true;
})()
"""

JS_COLLAPSE = r"""
(() => {
  if(typeof toggleHdrToolsMore==='function') toggleHdrToolsMore(false);
  else {
    document.body.classList.remove('hdr-tools-open');
    if(typeof syncHdrPortraitOverflow==='function') syncHdrPortraitOverflow();
  }
  return true;
})()
"""


def judge_collapsed(st, prefix, errors):
    if not st:
        errors.append(prefix + ": no state")
        return
    if not st.get("desk"):
        errors.append(prefix + ": not desktop")
    if not st.get("portrait"):
        errors.append(prefix + ": not portrait")
    if not st.get("collapse"):
        errors.append(prefix + ": missing hdr-tools-collapse")
    if st.get("open"):
        errors.append(prefix + ": already open")
    py = st.get("pyramid") or {}
    if not py.get("shown"):
        errors.append(prefix + ": pyramid hidden")
    for key in ("customize", "layouts", "profiles", "miss"):
        b = st.get(key) or {}
        if b.get("shown"):
            errors.append(f"{prefix}: {key} standing on row1")
    th = st.get("theme") or {}
    if not th.get("shown"):
        errors.append(prefix + ": theme hidden")
    cl = st.get("cluster") or {}
    if th.get("shown") and cl.get("shown") and th.get("r", 0) < cl.get("r", 0) - 12:
        errors.append(f"{prefix}: theme not rightmost th.r={th.get('r')} cl.r={cl.get('r')}")
    if st.get("overlapTitle"):
        errors.append(prefix + ": overlaps title")
    if st.get("titleClip"):
        errors.append(prefix + ": title clipped")
    hdr_b = st.get("hdrBottom")
    card_t = st.get("cardTop")
    if hdr_b and card_t and card_t + 1 < hdr_b:
        errors.append(f"{prefix}: card under header cardTop={card_t} hdrBottom={hdr_b}")


def judge_expanded(st, prefix, errors):
    if not st:
        errors.append(prefix + ": no state")
        return
    if not st.get("open"):
        errors.append(prefix + ": not open")
    row = st.get("row2") or {}
    if not row.get("shown"):
        errors.append(prefix + ": no row2")
    scale = st.get("scale") or {}
    if not scale.get("shown"):
        errors.append(prefix + ": scale hidden on row2")
    cl = st.get("cluster") or {}
    if scale.get("shown") and cl.get("shown") and abs(scale.get("r", 0) - cl.get("r", 0)) > 14:
        errors.append(f"{prefix}: scale not flush right scale.r={scale.get('r')} cl.r={cl.get('r')}")
    cust = st.get("customize") or {}
    lay = st.get("layouts") or {}
    prof = st.get("profiles") or {}
    if not (cust.get("shown") and lay.get("shown") and prof.get("shown")):
        errors.append(prefix + ": missing Customize/Layouts/Profiles on row2")
    else:
        if cust.get("x", 0) < 8 or lay.get("x", 0) < 8:
            errors.append(f"{prefix}: row2 items off-screen cust.x={cust.get('x')} lay.x={lay.get('x')}")
        if not (cust.get("x", 0) < lay.get("x", 0) < prof.get("x", 0) < scale.get("x", 0)):
            errors.append(
                f"{prefix}: row2 order cust={cust.get('x')} lay={lay.get('x')} prof={prof.get('x')} scale={scale.get('x')}"
            )
        if abs(cust.get("cy", 0) - scale.get("cy", 0)) > 18:
            errors.append(prefix + ": Customize not on same row as scale")
    if st.get("overlapTitle"):
        errors.append(prefix + ": overlaps title")
    py = st.get("pyramid") or {}
    s = st.get("s") or {}
    if py.get("shown") and s.get("shown") and py.get("y", 0) + 12 < s.get("y", 0) - 20:
        errors.append(prefix + ": pyramid left row1")
    elif py.get("shown") and s.get("shown") and py.get("x", 0) > s.get("x", 0):
        errors.append(prefix + ": pyramid not left of S")


def judge_land(st, prefix, errors):
    if not st:
        errors.append(prefix + ": no state")
        return
    if st.get("portrait"):
        errors.append(prefix + ": still portrait")
    py = st.get("pyramid") or {}
    if py.get("shown"):
        errors.append(prefix + ": pyramid still shown")
    if st.get("collapse"):
        errors.append(prefix + ": collapse class remains")
    for key in ("customize", "layouts", "profiles", "miss"):
        b = st.get(key) or {}
        if not b.get("shown"):
            errors.append(f"{prefix}: {key} not standing")


def main():
    integ = integrity()
    ensure_http()
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
    logf = open("/tmp/catalog-hdr-tools-ovf.log", "w")
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
            "--ozone-override-screen-size=900,1400",
            "--use-angle=swiftshader-webgl",
            "about:blank",
        ],
        stdout=logf,
        stderr=subprocess.STDOUT,
    )
    out = {"ok": True, "integrity": integ, "errors": [], "shots": []}
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

        set_view(cdp, 900, 1400)
        nav(cdp, f"http://127.0.0.1:{HTTP}/DS-CATALOG.html?v=hdr-tools")
        collapsed = cdp.eval(JS_STATE)
        out["collapsed"] = collapsed
        judge_collapsed(collapsed, "DS-900-collapsed", out["errors"])
        out["shots"].append(shot(cdp, "D1400-ds-hdr-tools-collapsed.png"))

        cdp.eval(JS_EXPAND)
        time.sleep(0.35)
        expanded = cdp.eval(JS_STATE)
        out["expanded"] = expanded
        judge_expanded(expanded, "DS-900-expanded", out["errors"])
        out["shots"].append(shot(cdp, "D1400-ds-hdr-tools-expanded.png"))

        cdp.eval(JS_COLLAPSE)
        set_view(cdp, 1400, 900)
        time.sleep(0.35)
        if typeof_sync := cdp.eval("typeof syncHdrPortraitOverflow==='function'"):
            cdp.eval("syncHdrPortraitOverflow()")
        land = cdp.eval(JS_STATE)
        out["landscape"] = land
        judge_land(land, "DS-1400-land", out["errors"])
        out["shots"].append(shot(cdp, "D1400-ds-hdr-tools-landscape.png"))

        if not integ.get("ok"):
            out["errors"].append("integrity")
        out["ok"] = len(out["errors"]) == 0
    except Exception as e:
        out["ok"] = False
        out["errors"].append(str(e))
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=3)
        except Exception:
            proc.kill()
    OUT.write_text(json.dumps(out, indent=2))
    slim = {
        "ok": out.get("ok"),
        "errors": out.get("errors"),
        "integrity": integ,
        "shots": out.get("shots"),
        "collapsed": {
            k: (out.get("collapsed") or {}).get(k)
            for k in ("w", "h", "desk", "portrait", "collapse", "open", "overlapTitle", "pyramid", "theme", "customize", "miss", "hdrBottom", "cardTop")
        },
        "expanded": {
            k: (out.get("expanded") or {}).get(k)
            for k in ("open", "overlapTitle", "row2", "scale", "customize", "layouts", "profiles", "miss")
        },
        "landscape": {
            k: (out.get("landscape") or {}).get(k)
            for k in ("w", "h", "portrait", "collapse", "pyramid", "customize", "miss")
        },
    }
    print(json.dumps(slim, indent=2)[:14000])
    sys.exit(0 if out.get("ok") else 1)


if __name__ == "__main__":
    main()
