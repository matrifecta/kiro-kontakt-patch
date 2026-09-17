#!/usr/bin/env python3
"""CDP verify Legend/Guide left-edge widgets on Kontakt/DS catalogs."""
import base64
import json
import os
import socket
import subprocess
import time
import urllib.request
from pathlib import Path
from urllib.parse import urlparse

OUT = Path("/home/phnx/kiro-kontakt-patch/kiro/_patch/verify_legend_guide_edge.json")
SHOT = Path("/home/phnx/kiro-kontakt-patch/kiro/_patch/ui-pos-shots")
PORT = 9551
HTTP_PORT = 8797
PROFILE = "/tmp/catalog-legend-guide"
SHOT.mkdir(parents=True, exist_ok=True)
os.makedirs(PROFILE, exist_ok=True)

PROBE = r"""
(() => {
  function box(el){
    if(!el)return null;
    var cs=getComputedStyle(el);
    var r=el.getBoundingClientRect();
    return {
      hidden:!!el.hidden,
      disp:cs.display, vis:cs.visibility,
      x:Math.round(r.left), y:Math.round(r.top),
      r:Math.round(r.right), b:Math.round(r.bottom),
      w:Math.round(r.width), h:Math.round(r.height),
      color:cs.color, bg:cs.backgroundColor, pressed:el.getAttribute('aria-pressed'),
      tx:cs.transform
    };
  }
  var main=document.getElementById('catalogMain');
  var stack=document.getElementById('catalogEdgeStack');
  var lg=document.getElementById('catalogLegendBtn');
  var gd=document.getElementById('catalogGuideBtn');
  var card=document.getElementById('catalogHelpCard');
  var fsBtn=document.getElementById('catalogHelpFs');
  var user=document.getElementById('catalogHelpUser');
  var upd=document.getElementById('catalogHelpUpdate');
  var legend=document.getElementById('catalogHelpLegend');
  var jump=document.getElementById('catalogJumpStack');
  var search=document.getElementById('searchChrome');
  return {
    portable:!!window.CATALOG_PORTABLE,
    ns:window.CATALOG_NS,
    vw:innerWidth, vh:innerHeight,
    desk:typeof displayIsDesktop==='function'&&displayIsDesktop(),
    useCard:typeof catalogHelpUseDesktopCard==='function'&&catalogHelpUseDesktopCard(),
    cls:document.body.className,
    theme:document.documentElement.getAttribute('data-theme'),
    textVar:(getComputedStyle(document.documentElement).getPropertyValue('--text')||'').trim(),
    kind:window._catalogHelpKind||null,
    tab:window._catalogHelpTab||null,
    helpOpen:document.body.classList.contains('catalog-help-open'),
    helpFs:document.body.classList.contains('catalog-help-fs'),
    main:box(main),
    stack:box(stack),
    legend:box(lg),
    guide:box(gd),
    card:box(card),
    fsBtn:box(fsBtn),
    fsHidden:!!(fsBtn&&(fsBtn.hidden||getComputedStyle(fsBtn).display==='none')),
    panelLegend:!legend||legend.hidden,
    panelUser:!user||user.hidden,
    panelUpdate:!upd||upd.hidden,
    jump:box(jump),
    search:box(search),
    scroll:(main&&main.scrollTop)||0
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
    for _ in range(250):
        try:
            n = cdp.eval(
                "!!(document.getElementById('catalogMain')&&typeof toggleCatalogHelp==='function'&&typeof placeCatalogEdgeStack==='function')"
            )
        except Exception:
            n = False
        if n:
            return
        time.sleep(0.2)
    raise SystemExit("catalog JS not ready")


def set_view(cdp, w, h, mobile=False):
    cdp.call(
        "Emulation.setDeviceMetricsOverride",
        {
            "width": w,
            "height": h,
            "deviceScaleFactor": 1,
            "mobile": mobile,
            "screenOrientation": {
                "type": "portraitPrimary" if h > w else "landscapePrimary",
                "angle": 0 if h > w else 90,
            },
        },
    )
    time.sleep(0.4)
    cdp.eval(
        "if(typeof placeCatalogJumpStack==='function')placeCatalogJumpStack();"
        "if(typeof placeCatalogEdgeStack==='function')placeCatalogEdgeStack();"
    )
    time.sleep(0.15)


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
    time.sleep(1.2)
    wait_ready(cdp)
    cdp.eval(
        "if(typeof setDisplayMode==='function')setDisplayMode('sides');"
        "if(typeof placeCatalogJumpStack==='function')placeCatalogJumpStack();"
        "if(typeof placeCatalogEdgeStack==='function')placeCatalogEdgeStack();"
    )
    time.sleep(0.25)


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


def visible(b):
    return bool(b and b.get("w", 0) >= 12 and b.get("h", 0) >= 12 and b.get("disp") != "none" and b.get("vis") != "hidden" and not b.get("hidden"))


def on_left_edge(probe):
    main, lg, gd = probe.get("main"), probe.get("legend"), probe.get("guide")
    if not (main and lg and gd):
        return False, "missing boxes"
    # buttons should sit on the left content border, not over Search
    search = probe.get("search")
    if search and visible(search) and lg["x"] + 8 < search["r"] and lg["x"] < search["x"] + 4:
        # overlapping search too much
        if lg["x"] < search["r"] - 20 and search["x"] < main["x"] - 8:
            return False, f"legend over search lg.x={lg['x']} search={search['x']}-{search['r']} main.x={main['x']}"
    if abs(lg["x"] - main["x"]) > 48:
        return False, f"legend not near main left lg.x={lg['x']} main.x={main['x']}"
    if gd["b"] > lg["y"] + 6:
        return False, f"guide not above legend g.b={gd['b']} lg.y={lg['y']}"
    return True, "ok"


def run_desktop(cdp, prefix):
    set_view(cdp, 1400, 900)
    cdp.eval(
        "if(typeof setDisplayMode==='function')setDisplayMode('sides');"
        "document.body.classList.remove('index-window-open');"
        "var ix=document.getElementById('catalogIndex'); if(ix)ix.classList.add('is-collapsed');"
        "if(typeof placeCatalogEdgeStack==='function')placeCatalogEdgeStack();"
    )
    time.sleep(0.3)
    cdp.eval("if(typeof placeCatalogEdgeStack==='function')placeCatalogEdgeStack();")
    p0 = cdp.eval(PROBE)
    shot(cdp, f"{prefix}-edge-idle.png")
    cdp.eval("var m=document.getElementById('catalogMain'); if(m)m.scrollTop=Math.min(m.scrollHeight/2,800); if(typeof placeCatalogJumpStack==='function')placeCatalogJumpStack();")
    time.sleep(0.2)
    p1 = cdp.eval(PROBE)
    shot(cdp, f"{prefix}-edge-scrolled.png")
    cdp.eval("toggleCatalogHelp('legend')")
    time.sleep(0.25)
    p2 = cdp.eval(PROBE)
    shot(cdp, f"{prefix}-legend-card.png")
    cdp.eval("catalogHelpEnterFs()")
    time.sleep(0.2)
    p3 = cdp.eval(PROBE)
    shot(cdp, f"{prefix}-legend-fs.png")
    cdp.eval("catalogHelpBack()")
    time.sleep(0.2)
    p4 = cdp.eval(PROBE)
    cdp.eval("catalogHelpBack()")
    time.sleep(0.2)
    p5 = cdp.eval(PROBE)
    cdp.eval("toggleCatalogHelp('guide')")
    time.sleep(0.2)
    p6 = cdp.eval(PROBE)
    shot(cdp, f"{prefix}-guide-user.png")
    cdp.eval("setCatalogHelpTab('update')")
    time.sleep(0.15)
    p7 = cdp.eval(PROBE)
    shot(cdp, f"{prefix}-guide-update.png")
    theme0 = p0.get("textVar")
    cdp.eval("document.documentElement.setAttribute('data-theme','sandstorm');")
    time.sleep(0.2)
    p8 = cdp.eval(PROBE)
    shot(cdp, f"{prefix}-theme-sandstorm.png")
    cdp.eval("document.documentElement.setAttribute('data-theme','desert');")
    cdp.eval("closeCatalogHelp(); if(typeof setDisplayMode==='function')setDisplayMode('middle'); if(typeof placeCatalogEdgeStack==='function')placeCatalogEdgeStack();")
    time.sleep(0.35)
    p9 = cdp.eval(PROBE)
    shot(cdp, f"{prefix}-middle.png")
    return {
        "idle": p0,
        "scrolled": p1,
        "legendCard": p2,
        "legendFs": p3,
        "legendBackToCard": p4,
        "closed": p5,
        "guideUser": p6,
        "guideUpdate": p7,
        "themeSmoked": p8,
        "middle": p9,
        "theme0": theme0,
        "theme1": p8.get("textVar"),
    }


def run_phone(cdp, prefix):
    set_view(cdp, 390, 844, mobile=True)
    cdp.eval("if(typeof setDisplayMode==='function')setDisplayMode('sides'); if(typeof placeCatalogEdgeStack==='function')placeCatalogEdgeStack();")
    time.sleep(0.35)
    p0 = cdp.eval(PROBE)
    cdp.eval("toggleCatalogHelp('legend')")
    time.sleep(0.25)
    p1 = cdp.eval(PROBE)
    shot(cdp, f"{prefix}-phone-legend-fs.png")
    cdp.eval("catalogHelpBack()")
    time.sleep(0.2)
    p2 = cdp.eval(PROBE)
    return {"idle": p0, "open": p1, "closed": p2}


def judge_desktop(d, label):
    fails = []
    idle = d["idle"]
    ok, why = on_left_edge(idle)
    if not visible(idle.get("legend")) or not visible(idle.get("guide")):
        fails.append(f"{label} widgets not visible idle")
    elif not ok:
        fails.append(f"{label} left-edge {why}")
    # stay put on scroll (y should be similar; x same)
    a, b = idle.get("legend") or {}, d["scrolled"].get("legend") or {}
    if a and b and abs(a.get("x", 0) - b.get("x", 0)) > 6:
        fails.append(f"{label} scroll x drifted {a.get('x')} -> {b.get('x')}")
    if a and b and abs(a.get("y", 0) - b.get("y", 0)) > 24:
        fails.append(f"{label} scroll y drifted {a.get('y')} -> {b.get('y')}")
    lc = d["legendCard"]
    if not lc.get("helpOpen"):
        fails.append(f"{label} legend did not open card")
    if lc.get("helpFs"):
        fails.append(f"{label} legend opened as FS on desktop")
    if lc.get("fsHidden"):
        fails.append(f"{label} FS button hidden on desktop card")
    if (lc.get("legend") or {}).get("pressed") != "true":
        fails.append(f"{label} legend not aria-pressed")
    # selected sticks out more
    idle_tx = (idle.get("legend") or {}).get("tx") or ""
    open_tx = (lc.get("legend") or {}).get("tx") or ""
    def tx_x(s):
        if not s or "matrix" not in s: return 0
        try: return float(s.split("(")[1].split(",")[4])
        except Exception: return 0
    if tx_x(open_tx) < tx_x(idle_tx) + 4:
        fails.append(f"{label} selected did not stick out more idle.tx={idle_tx} open.tx={open_tx}")
    fs = d["legendFs"]
    if not fs.get("helpFs"):
        fails.append(f"{label} FS did not enter fullscreen")
    back = d["legendBackToCard"]
    if not back.get("helpOpen") or back.get("helpFs"):
        fails.append(f"{label} Back from FS did not return to card")
    if d["closed"].get("helpOpen") or d["closed"].get("helpFs"):
        fails.append(f"{label} Back from card did not close")
    gu = d["guideUser"]
    if gu.get("kind") != "guide" or gu.get("panelUser"):
        fails.append(f"{label} guide default tab not user {gu.get('tab')} hiddenUser={gu.get('panelUser')}")
    upd = d["guideUpdate"]
    if upd.get("tab") != "update" or upd.get("panelUpdate"):
        fails.append(f"{label} update tab did not swap content")
    if d.get("theme0") and d.get("theme1") and d["theme0"] == d["theme1"]:
        fails.append(f"{label} theme --text unchanged {d['theme0']}")
    mid = d["middle"]
    if not visible(mid.get("legend")):
        fails.append(f"{label} widgets missing in Middle")
    else:
        okm, whym = on_left_edge(mid)
        if not okm:
            fails.append(f"{label} middle {whym}")
    return fails


def judge_phone(p, label):
    fails = []
    if not p["open"].get("helpFs"):
        fails.append(f"{label} phone did not open fullscreen")
    if not p["open"].get("fsHidden"):
        fails.append(f"{label} phone still shows desktop FS button")
    if p["closed"].get("helpOpen") or p["closed"].get("helpFs"):
        fails.append(f"{label} phone Back did not close")
    card = p["open"].get("card") or {}
    if (card.get("w") or 0) < (p["open"].get("vw") or 390) - 24:
        fails.append(f"{label} phone card not fullscreen w={card.get('w')} vw={p['open'].get('vw')}")
    if (p["idle"].get("legend") or {}).get("disp") == "inline-block":
        fails.append(f"{label} phone widgets unstyled {p['idle'].get('legend')}")
    return fails


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
        for _ in range(50):
            if port_open(PORT):
                break
            time.sleep(0.2)
        else:
            raise SystemExit("chromium debug port failed")
        time.sleep(0.4)

    out = {}
    fails = []
    pages = [
        ("kontakt", f"http://127.0.0.1:{HTTP_PORT}/KONTAKT-CATALOG.html?lg=1"),
        ("ds", f"http://127.0.0.1:{HTTP_PORT}/DS-CATALOG.html?lg=1"),
        ("kontaktPort", f"http://127.0.0.1:{HTTP_PORT}/KONTAKT-CATALOG-portable.html?lg=1"),
    ]
    for name, url in pages:
        tab = new_tab(url)
        cdp = CDP(tab["webSocketDebuggerUrl"])
        try:
            nav(cdp, url)
            if name.endswith("Port"):
                set_view(cdp, 390, 844, mobile=True)
                out[name] = run_phone(cdp, "P390-" + name)
                fails.extend(judge_phone(out[name], name))
            else:
                out[name] = run_desktop(cdp, "D1400-" + name)
                fails.extend(judge_desktop(out[name], name))
                out[name + "Phone"] = run_phone(cdp, "P390-" + name)
                fails.extend(judge_phone(out[name + "Phone"], name + "Phone"))
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
