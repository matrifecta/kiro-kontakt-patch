#!/usr/bin/env python3
"""Verify Legend/Guide left-edge tabs clear About like ↑↓ at scroll end."""
import base64
import json
import os
import socket
import subprocess
import time
import urllib.request
from pathlib import Path
from urllib.parse import urlparse

OUT = Path("/home/phnx/kiro-kontakt-patch/kiro/_patch/verify_edge_stack_about_dock.json")
SHOT = Path("/home/phnx/kiro-kontakt-patch/kiro/_patch/ui-pos-shots")
PORT = 9552
HTTP_PORT = 8797
PROFILE = "/tmp/catalog-edge-about-dock"
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
      bottomCss:cs.bottom, leftCss:cs.left, tx:cs.transform
    };
  }
  function overlap(a,b,pad){
    pad=pad||0;
    if(!a||!b)return false;
    return !(a.r<b.x-pad||a.x>b.r+pad||a.b<b.y-pad||a.y>b.b+pad);
  }
  var main=document.getElementById('catalogMain');
  var note=document.getElementById('catalogDocNote');
  var stack=document.getElementById('catalogEdgeStack');
  var jump=document.getElementById('catalogJumpStack');
  var lg=document.getElementById('catalogLegendBtn');
  var gd=document.getElementById('catalogGuideBtn');
  var top=jump&&jump.querySelector('a.top');
  var bot=jump&&jump.querySelector('a.bottom');
  var sc=(typeof catalogContentScroller==='function'&&catalogContentScroller())||main;
  var nb=box(note), lb=box(lg), gb=box(gd), tb=box(top), bb=box(bot);
  var inset=typeof catalogJumpStackBottomInset==='function'?catalogJumpStackBottomInset():null;
  return {
    portable:!!window.CATALOG_PORTABLE,
    ns:window.CATALOG_NS,
    vw:innerWidth, vh:innerHeight,
    cls:document.body.className,
    kind:window._catalogHelpKind||null,
    helpOpen:document.body.classList.contains('catalog-help-open'),
    helpFs:document.body.classList.contains('catalog-help-fs'),
    embedded:!!(note&&note.classList.contains('is-embedded')),
    inset:inset,
    scrollTop:sc?sc.scrollTop:0,
    scrollMax:sc?Math.max(0,sc.scrollHeight-sc.clientHeight):0,
    main:box(main),
    note:nb,
    stack:box(stack),
    jump:box(jump),
    legend:lb,
    guide:gb,
    top:tb,
    bot:bb,
    edgeOverNote:overlap(lb,nb,0)||overlap(gb,nb,0),
    jumpOverNote:overlap(tb,nb,0)||overlap(bb,nb,0),
    legendClear:nb&&lb? (nb.y-lb.b):null,
    jumpClear:nb&&bb? (nb.y-bb.b):null,
    bottoms:{edge:stack&&stack.style.bottom, jump:jump&&jump.style.bottom}
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
                "!!(document.getElementById('catalogMain')&&typeof placeCatalogEdgeStack==='function'"
                "&&typeof placeCatalogJumpStack==='function'&&typeof catalogJumpStackBottomInset==='function')"
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
    time.sleep(0.35)
    cdp.eval(
        "if(typeof placeCatalogJumpStack==='function')placeCatalogJumpStack();"
        "if(typeof placeCatalogEdgeStack==='function')placeCatalogEdgeStack();"
    )
    time.sleep(0.12)


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
    return bool(
        b
        and b.get("w", 0) >= 8
        and b.get("h", 0) >= 8
        and b.get("disp") != "none"
        and b.get("vis") != "hidden"
        and not b.get("hidden")
    )


def fail_overlap(p, label, key):
    fails = []
    if p.get("edgeOverNote"):
        fails.append(
            f"{label} {key} edge overlays About legendClear={p.get('legendClear')} bottoms={p.get('bottoms')}"
        )
    if p.get("jumpOverNote"):
        fails.append(f"{label} {key} jump overlays About jumpClear={p.get('jumpClear')}")
    if p.get("legendClear") is not None and p.get("legendClear") < 4:
        fails.append(f"{label} {key} legend clearance {p.get('legendClear')}")
    return fails


def run_page(cdp, prefix, phone=False):
    if phone:
        set_view(cdp, 390, 844, mobile=True)
    else:
        set_view(cdp, 1400, 900)
    cdp.eval(
        "if(typeof setDisplayMode==='function')setDisplayMode('sides');"
        "document.body.classList.remove('index-window-open');"
        "var ix=document.getElementById('catalogIndex'); if(ix)ix.classList.add('is-collapsed');"
        "var note=document.getElementById('catalogDocNote');"
        "if(note&&note.classList.contains('is-embedded')&&typeof toggleDocNoteEmbed==='function')toggleDocNoteEmbed();"
        "if(typeof placeCatalogJumpStack==='function')placeCatalogJumpStack();"
    )
    time.sleep(0.35)
    windowed = cdp.eval(PROBE)
    shot(cdp, f"{prefix}-dock-window.png")

    cdp.eval(
        "var sc=(typeof catalogContentScroller==='function'&&catalogContentScroller())||document.getElementById('catalogMain');"
        "if(sc)sc.scrollTop=Math.max(0,Math.round((sc.scrollHeight-sc.clientHeight)/2));"
        "if(typeof placeCatalogJumpStack==='function')placeCatalogJumpStack();"
    )
    time.sleep(0.2)
    mid = cdp.eval(PROBE)
    shot(cdp, f"{prefix}-dock-mid.png")

    cdp.eval(
        "var note=document.getElementById('catalogDocNote');"
        "if(note&&!note.classList.contains('is-embedded')&&typeof toggleDocNoteEmbed==='function')toggleDocNoteEmbed();"
        "var sc=(typeof catalogContentScroller==='function'&&catalogContentScroller())||document.getElementById('catalogMain');"
        "if(sc)sc.scrollTop=0;"
        "if(typeof placeCatalogJumpStack==='function')placeCatalogJumpStack();"
    )
    time.sleep(0.3)
    embed_top = cdp.eval(PROBE)
    shot(cdp, f"{prefix}-dock-embed-top.png")

    cdp.eval(
        "var sc=(typeof catalogContentScroller==='function'&&catalogContentScroller())||document.getElementById('catalogMain');"
        "if(sc)sc.scrollTop=sc.scrollHeight;"
        "if(typeof placeCatalogJumpStack==='function')placeCatalogJumpStack();"
    )
    time.sleep(0.35)
    embed_end = cdp.eval(PROBE)
    shot(cdp, f"{prefix}-dock-embed-end.png")

    cdp.eval("if(typeof toggleCatalogHelp==='function')toggleCatalogHelp('legend');")
    time.sleep(0.25)
    legend_open = cdp.eval(PROBE)
    shot(cdp, f"{prefix}-dock-legend-open.png")
    cdp.eval("if(typeof closeCatalogHelp==='function')closeCatalogHelp();")
    time.sleep(0.15)
    cdp.eval("if(typeof toggleCatalogHelp==='function')toggleCatalogHelp('guide');")
    time.sleep(0.2)
    guide_open = cdp.eval(PROBE)
    cdp.eval("if(typeof closeCatalogHelp==='function')closeCatalogHelp();")
    time.sleep(0.15)

    return {
        "windowed": windowed,
        "mid": mid,
        "embedTop": embed_top,
        "embedEnd": embed_end,
        "legendOpen": legend_open,
        "guideOpen": guide_open,
    }


def judge(d, label, phone=False):
    fails = []
    w = d["windowed"]
    if not visible(w.get("legend")) or not visible(w.get("guide")):
        fails.append(f"{label} widgets not visible windowed")
    fails.extend(fail_overlap(w, label, "windowed"))
    fails.extend(fail_overlap(d["mid"], label, "mid"))
    # embedded top: About is at the end of scroll, may be offscreen — overlap only if note visible
    et = d["embedTop"]
    if visible(et.get("note")):
        fails.extend(fail_overlap(et, label, "embed-top"))
    ee = d["embedEnd"]
    if not visible(ee.get("note")):
        fails.append(f"{label} embed-end About not visible")
    else:
        fails.extend(fail_overlap(ee, label, "embed-end"))
    # mid-scroll: x should stay on left of main
    main, lg = w.get("main") or {}, w.get("legend") or {}
    if main and lg and abs((lg.get("x") or 0) - (main.get("x") or 0)) > 56:
        fails.append(f"{label} legend not on left edge x={lg.get('x')} main.x={main.get('x')}")
    lo = d["legendOpen"]
    if not lo.get("helpOpen") and not lo.get("helpFs"):
        fails.append(f"{label} legend did not open")
    go = d["guideOpen"]
    if go.get("kind") != "guide":
        fails.append(f"{label} guide did not open kind={go.get('kind')}")
    if phone:
        if not lo.get("helpFs"):
            fails.append(f"{label} phone legend not fullscreen")
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
        ("kontakt", f"http://127.0.0.1:{HTTP_PORT}/KONTAKT-CATALOG.html?dock=1", False),
        ("ds", f"http://127.0.0.1:{HTTP_PORT}/DS-CATALOG.html?dock=1", False),
        ("kontaktPort", f"http://127.0.0.1:{HTTP_PORT}/KONTAKT-CATALOG-portable.html?dock=1", True),
        ("dsPort", f"http://127.0.0.1:{HTTP_PORT}/DS-CATALOG-portable.html?dock=1", True),
    ]
    for name, url, phone in pages:
        tab = new_tab(url)
        cdp = CDP(tab["webSocketDebuggerUrl"])
        try:
            nav(cdp, url)
            out[name] = run_page(cdp, ("P390-" if phone else "D1400-") + name, phone=phone)
            fails.extend(judge(out[name], name, phone=phone))
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
