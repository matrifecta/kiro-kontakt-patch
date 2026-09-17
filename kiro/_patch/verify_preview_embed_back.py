#!/usr/bin/env python3
"""CDP: preview-back never restores hl; embed-back history then preview; reload current URL."""
import json
import os
import socket
import subprocess
import sys
import time
import urllib.request
from pathlib import Path
from urllib.parse import urlparse
import base64

OUT = "/home/phnx/kiro-kontakt-patch/kiro/_patch/verify_preview_embed_back.json"
PORT = 9523
HTTP_PORT = 8797
PROFILE = "/tmp/catalog-preview-embed-back"
os.makedirs(PROFILE, exist_ok=True)

MEASURE = r"""
(() => {
  var el=document.querySelector('.entry.selected')||document.querySelector('.entry');
  var frame=document.getElementById('cardSearchFrame');
  var step=document.querySelector('#cardSearchEmbed .card-search-iframe-back');
  var reload=document.querySelector('#cardSearchEmbed .card-search-reload');
  var back=document.querySelector('#cardSearchEmbed .card-search-back');
  var cs=window.cardSearchState||{};
  function vis(n){
    if(!n)return false;
    var r=n.getBoundingClientRect(), s=getComputedStyle(n);
    return s.display!=='none'&&s.visibility!=='hidden'&&r.width>1&&r.height>1;
  }
  return {
    hl: document.body.classList.contains('hl-open'),
    preview: document.body.classList.contains('chosen-preview-open'),
    embed: document.body.classList.contains('card-embed-open'),
    selected: !!(el&&el.classList.contains('selected')),
    highlight: !!(el&&el.classList.contains('highlight')),
    id: el&&el.id,
    jumpOrigin: window.jumpOrigin||null,
    hist: (cs.history||[]).length,
    embedUrl: cs.embedUrl||'',
    frameSrc: frame?(frame.getAttribute('src')||frame.src||''):'',
    iframeBackVis: vis(step),
    reloadVis: vis(reload),
    embedBackVis: vis(back),
    hdrBar: !!document.getElementById('hdrBarToggle')
  };
})()
"""


class Ws:
    def __init__(self, url):
        u = urlparse(url)
        key = base64.b64encode(os.urandom(16)).decode()
        s = socket.create_connection((u.hostname, u.port or 80), timeout=20)
        path = u.path + (("?" + u.query) if u.query else "")
        s.sendall(
            (
                f"GET {path} HTTP/1.1\r\nHost: {u.hostname}:{u.port}\r\nUpgrade: websocket\r\n"
                f"Connection: Upgrade\r\nSec-WebSocket-Key: {key}\r\nSec-WebSocket-Version: 13\r\n\r\n"
            ).encode()
        )
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
        mask = os.urandom(4)
        hdr = bytearray([0x81])
        flen = len(data)
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
            b1 = self.buf[1]
            ln = b1 & 0x7F
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
            if b1 & 0x80:
                off += 4
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

    def eval(self, expr):
        r = self.call("Runtime.evaluate", {"expression": expr, "returnByValue": True})
        if r.get("exceptionDetails"):
            raise RuntimeError(r["exceptionDetails"])
        return r.get("result", {}).get("value")


def attach_tab():
    tabs = json.load(urllib.request.urlopen(f"http://127.0.0.1:{PORT}/json/list"))
    for t in tabs:
        if t.get("type") == "page" and t.get("webSocketDebuggerUrl"):
            return t
    raise SystemExit("no page")


def wait_ready(cdp):
    for _ in range(120):
        try:
            if cdp.eval("!!(document.querySelectorAll('.entry').length>3&&window.openChosenPreview)"):
                return
        except Exception:
            pass
        time.sleep(0.2)
    raise SystemExit("not ready")


def nav(cdp, url):
    cdp.call("Page.enable")
    cdp.call("Runtime.enable")
    cdp.call("Page.navigate", {"url": url})
    time.sleep(0.7)
    wait_ready(cdp)


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


def pick_entry(cdp):
    return cdp.eval(
        """
(() => {
  var el=document.querySelector('.entry:not(.is-hidden)')||document.querySelector('.entry');
  return el?el.id:'';
})()
"""
    )


def run_case(cdp, tag, errors, results):
    eid = pick_entry(cdp)
    if not eid:
        errors.append(tag + ": no entry")
        return
    cdp.eval(
        f"""
(() => {{
  var el=document.getElementById({json.dumps(eid)});
  if(typeof closeCardSearchEmbed==='function')closeCardSearchEmbed();
  if(typeof closeChosenPreview==='function')closeChosenPreview({{skipJumpExit:true}});
  if(typeof closeOverlay==='function')closeOverlay({{skipScroll:true}});
  if(el&&typeof openOverlay==='function')openOverlay(el);
}})()
"""
    )
    time.sleep(0.3)
    st = cdp.eval(MEASURE)
    results[f"{tag}-hl"] = st
    if not st.get("hl"):
        errors.append(tag + ": overlay did not open")

    cdp.eval(
        f"""
(() => {{
  var el=document.getElementById({json.dumps(eid)});
  if(el&&typeof openChosenPreview==='function')openChosenPreview(el);
}})()
"""
    )
    time.sleep(0.3)
    st = cdp.eval(MEASURE)
    results[f"{tag}-from-hl-preview"] = st
    if not st.get("preview"):
        errors.append(tag + ": preview did not open from fullscreen")
    if st.get("hl"):
        errors.append(tag + ": hl still open in preview")

    cdp.eval("if(typeof closeChosenPreview==='function')closeChosenPreview();")
    time.sleep(0.3)
    st = cdp.eval(MEASURE)
    results[f"{tag}-preview-back"] = st
    if st.get("hl"):
        errors.append(tag + ": preview-back restored fullscreen")
    if st.get("preview"):
        errors.append(tag + ": preview still open after back")
    if not st.get("selected"):
        errors.append(tag + ": card not selected after preview-back")

    cdp.eval(
        f"""
(() => {{
  var el=document.getElementById({json.dumps(eid)});
  if(el&&typeof openChosenPreview==='function')openChosenPreview(el);
  if(typeof openCardSearchEmbed==='function')openCardSearchEmbed('web','https://example.com/search');
}})()
"""
    )
    time.sleep(0.4)
    st = cdp.eval(MEASURE)
    results[f"{tag}-embed"] = st
    if not st.get("embed") or not st.get("preview"):
        errors.append(tag + ": embed/preview not open")
    if st.get("iframeBackVis"):
        errors.append(tag + ": iframe-back still visible")
    if not st.get("reloadVis") or not st.get("embedBackVis"):
        errors.append(tag + ": reload/embed-back missing")

    cdp.eval("if(typeof cardSearchBack==='function')cardSearchBack();")
    time.sleep(0.25)
    st = cdp.eval(MEASURE)
    results[f"{tag}-embed-back-root"] = st
    if st.get("embed"):
        errors.append(tag + ": embed-back on default did not exit embed")
    if not st.get("preview"):
        errors.append(tag + ": embed-back left preview")
    if st.get("hl"):
        errors.append(tag + ": embed-back opened fullscreen")

    cdp.eval(
        f"""
(() => {{
  var el=document.getElementById({json.dumps(eid)});
  if(el&&typeof openChosenPreview==='function')openChosenPreview(el);
  if(typeof openCardSearchEmbed==='function')openCardSearchEmbed('web','https://example.com/first');
  cardSearchState.embedUrl='https://example.com/first';
  cardSearchState.history=['https://example.com/first','https://example.com/second'];
  var frame=document.getElementById('cardSearchFrame');
  if(frame){{frame.src='https://example.com/second';frame.classList.remove('is-hidden');}}
  cardSearchState.embedUrl='https://example.com/second';
}})()
"""
    )
    time.sleep(0.35)
    before = cdp.eval(MEASURE)
    results[f"{tag}-hist-before"] = before
    cdp.eval("if(typeof cardSearchBack==='function')cardSearchBack();")
    time.sleep(0.25)
    mid = cdp.eval(MEASURE)
    results[f"{tag}-hist-back1"] = mid
    if not mid.get("embed") or not mid.get("preview"):
        errors.append(tag + ": first hist back should stay in embed+preview")
    if (mid.get("hist") or 0) >= (before.get("hist") or 0):
        errors.append(f"{tag}: hist did not shrink {before.get('hist')}->{mid.get('hist')}")
    cdp.eval("if(typeof cardSearchBack==='function')cardSearchBack();")
    time.sleep(0.25)
    after = cdp.eval(MEASURE)
    results[f"{tag}-hist-back2"] = after
    if after.get("embed"):
        errors.append(tag + ": second hist back should exit embed")
    if not after.get("preview"):
        errors.append(tag + ": second hist back left preview")

    cdp.eval(
        f"""
(() => {{
  var el=document.getElementById({json.dumps(eid)});
  if(el&&typeof openChosenPreview==='function')openChosenPreview(el);
  if(typeof openCardSearchEmbed==='function')openCardSearchEmbed('web','https://example.com/keep');
  var frame=document.getElementById('cardSearchFrame');
  var url='https://example.com/keep';
  cardSearchState.embedUrl=url;
  cardSearchState.type='web';
  cardSearchState.view='article';
  if(frame){{frame.classList.remove('is-hidden');frame.style.display='';frame.src=url;}}
}})()
"""
    )
    time.sleep(0.3)
    pre = cdp.eval(MEASURE)
    cdp.eval("if(typeof cardSearchReload==='function')cardSearchReload();")
    time.sleep(0.25)
    post = cdp.eval(MEASURE)
    results[f"{tag}-reload"] = {"pre": pre, "post": post}
    def norm(u):
        return (u or "").split("#")[0].rstrip("/")
    if "example.com/keep" not in (post.get("embedUrl") or "") and "example.com/keep" not in (post.get("frameSrc") or ""):
        errors.append(tag + ": reload navigated away url=" + str(post.get("embedUrl") or post.get("frameSrc")))
    if not post.get("embed") or not post.get("preview"):
        errors.append(tag + ": reload closed embed/preview")

    cdp.eval(
        """
(() => {
  if(typeof closeCardSearchEmbed==='function')closeCardSearchEmbed();
  if(typeof closeChosenPreview==='function')closeChosenPreview({skipJumpExit:true});
  if(typeof closeOverlay==='function')closeOverlay({skipScroll:true});
})()
"""
    )


def main():
    if not port_open(HTTP_PORT):
        raise SystemExit("http://127.0.0.1:8797 not serving")
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
    subprocess.run(["pkill", "-f", f"remote-debugging-port={PORT}"], check=False)
    time.sleep(0.2)
    logf = open("/tmp/catalog-preview-embed-back.log", "w")
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
    for _ in range(80):
        try:
            urllib.request.urlopen(f"http://127.0.0.1:{PORT}/json/version", timeout=1).read()
            break
        except Exception:
            time.sleep(0.2)
    else:
        json.dump({"err": "cdp"}, open(OUT, "w"))
        sys.exit(1)
    results = {}
    errors = []
    try:
        cdp = CDP(attach_tab()["webSocketDebuggerUrl"])
        cases = [
            ("K1400", "KONTAKT-CATALOG.html", 1400, 900, False),
            ("K390", "KONTAKT-CATALOG-portable.html", 390, 844, True),
            ("DS1400", "DS-CATALOG.html", 1400, 900, False),
            ("DS390", "DS-CATALOG-portable.html", 390, 844, True),
        ]
        last = None
        for tag, page, w, h, mobile in cases:
            if page != last:
                nav(cdp, f"http://127.0.0.1:{HTTP_PORT}/{page}?v=preview-embed-back")
                last = page
            set_view(cdp, w, h, mobile=mobile)
            run_case(cdp, tag, errors, results)
        out = {"errors": errors, "results": results, "ok": not errors}
        json.dump(out, open(OUT, "w"), indent=2)
        print("errors", len(errors))
        for e in errors:
            print(" -", e)
        if errors:
            sys.exit(1)
    finally:
        proc.terminate()


if __name__ == "__main__":
    main()
