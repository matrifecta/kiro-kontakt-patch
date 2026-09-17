#!/usr/bin/env python3
"""CDP: collapsed path expand/overlay, hit-target gaps, desc/path wheel-forward."""
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

OUT = "/home/phnx/kiro-kontakt-patch/kiro/_patch/verify_path_collapse_wheel.json"
PORT = 9525
HTTP_PORT = 8797
PROFILE = "/tmp/catalog-path-collapse-wheel"
os.makedirs(PROFILE, exist_ok=True)

MEASURE = r"""
(() => {
  var el=document.querySelector('.entry.selected')||document.querySelector('.entry:not(.is-hidden)')||document.querySelector('.entry');
  if(!el) return {err:'no-entry'};
  var path=el.querySelector('.path');
  var code=path&&path.querySelector('code');
  var folder=path&&path.querySelector('a.folder,.folder');
  var patches=el.querySelector('details.patches, .patches');
  var sum=patches&&patches.querySelector('summary');
  var search=el.querySelector('.search-popup-btn, .card-actions');
  var desc=el.querySelector('.summary-panel .desc, .desc');
  var panel=el.querySelector('.summary-panel');
  var main=document.getElementById('catalogMain');
  var body=document.querySelector('#catalogMain > .catalog-body');
  var sc=(typeof catalogPickWheelScroller==='function'&&catalogPickWheelScroller())
    ||(typeof catalogContentScroller==='function'&&catalogContentScroller())
    ||(typeof catalogScrollEl==='function'&&catalogScrollEl())
    ||body||main;
  function box(n){
    if(!n)return null;
    var r=n.getBoundingClientRect();
    return {t:r.top,b:r.bottom,l:r.left,r:r.right,w:r.width,h:r.height};
  }
  function gapY(a,b){if(!a||!b)return null;return b.t-a.b;}
  function gapX(a,b){if(!a||!b)return null;return b.l-a.r;}
  var pb=box(path), cb=box(code), fb=box(folder), pat=box(sum||patches), sb=box(search);
  return {
    id: el.id,
    selected: el.classList.contains('selected'),
    preview: document.body.classList.contains('chosen-preview-open'),
    hl: document.body.classList.contains('hl-open'),
    pathFocus: document.body.classList.contains('path-focus-open')||document.body.classList.contains('path-reader-open'),
    expanded: !!(path&&path.classList.contains('is-expanded')),
    pathH: path?path.clientHeight:0,
    pathScrollH: path?path.scrollHeight:0,
    codeH: code?code.clientHeight:0,
    cardH: el.clientHeight,
    scId: sc?(sc.id||String(sc.className||'').split(/\s+/)[0]):'',
    scTop: sc?sc.scrollTop:null,
    scCan: !!(sc&&sc.scrollHeight>sc.clientHeight+4),
    gapCodeFolder: gapX(cb, fb),
    gapPathPatches: gapY(pb, pat),
    gapPatchesSearch: gapY(pat, sb),
    gapPathSearch: gapY(pb, sb),
    iframeBackVis: (function(){
      var n=document.querySelector('#cardSearchEmbed .card-search-iframe-back');
      if(!n)return false;
      var r=n.getBoundingClientRect(), s=getComputedStyle(n);
      return s.display!=='none'&&s.visibility!=='hidden'&&r.width>1&&r.height>1;
    })()
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
                ln = int.from_bytes(self.buf[8:10], "big") if False else int.from_bytes(self.buf[2:10], "big")
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
            if cdp.eval("!!(document.querySelectorAll('.entry').length>1&&window.activatePath)"):
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
  var els=[].slice.call(document.querySelectorAll('.entry:not(.is-hidden)'));
  var best=null,n=0;
  els.forEach(function(el){
    var p=el.querySelector('.path code');
    var d=el.querySelector('.summary-panel .desc, .desc');
    var score=(p?(p.textContent||'').length:0)+(d?(d.textContent||'').length:0);
    if(score>n){n=score;best=el;}
  });
  return (best||els[0]||document.querySelector('.entry')||{}).id||'';
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
  if(typeof closePathFocus==='function')closePathFocus();
  if(typeof closePathReader==='function')closePathReader();
  if(el){{
    if(typeof selectEntry==='function')selectEntry(el);
    else {{ document.querySelectorAll('.entry.selected').forEach(function(x){{x.classList.remove('selected');}}); el.classList.add('selected'); }}
    var p=el.querySelector('.path');
    if(p){{p.classList.remove('is-expanded');p.classList.add('is-collapsed');p.setAttribute('aria-expanded','false');}}
  }}
}})()
"""
    )
    time.sleep(0.25)
    st = cdp.eval(MEASURE)
    results[f"{tag}-collapsed"] = st
    if st.get("expanded"):
        errors.append(tag + ": path not collapsed by default")
    if (st.get("pathH") or 0) > 56:
        errors.append(f"{tag}: collapsed path too tall {st.get('pathH')}")
    if st.get("gapCodeFolder") is not None and st.get("gapCodeFolder") < 6:
        errors.append(f"{tag}: folder too close to path text gap={st.get('gapCodeFolder')}")
    if st.get("gapPathPatches") is not None and st.get("gapPathPatches") < 6:
        errors.append(f"{tag}: patches too close to path gap={st.get('gapPathPatches')}")
    if st.get("gapPatchesSearch") is not None and st.get("gapPatchesSearch") < 8:
        errors.append(f"{tag}: search too close to patches gap={st.get('gapPatchesSearch')}")
    elif st.get("gapPathSearch") is not None and st.get("gapPathSearch") < 10:
        errors.append(f"{tag}: search too close to path gap={st.get('gapPathSearch')}")

    h0 = st.get("pathH") or 0
    cdp.eval(
        f"""
(() => {{
  var el=document.getElementById({json.dumps(eid)});
  var path=el&&el.querySelector('.path');
  var code=path&&(path.querySelector('code')||path);
  if(code) code.click();
}})()
"""
    )
    time.sleep(0.25)
    mid = cdp.eval(MEASURE)
    results[f"{tag}-expanded"] = mid
    if not mid.get("expanded"):
        errors.append(tag + ": first click did not expand in-card")
    if mid.get("pathFocus"):
        errors.append(tag + ": first click opened fullscreen overlay")
    if (mid.get("pathH") or 0) <= h0:
        errors.append(f"{tag}: expand did not grow path {h0}->{mid.get('pathH')}")

    cdp.eval(
        f"""
(() => {{
  var el=document.getElementById({json.dumps(eid)});
  var path=el&&el.querySelector('.path');
  var code=path&&(path.querySelector('code')||path);
  if(code) code.click();
}})()
"""
    )
    time.sleep(0.3)
    ov = cdp.eval(MEASURE)
    results[f"{tag}-overlay"] = ov
    if not ov.get("pathFocus"):
        errors.append(tag + ": second click did not open path overlay")

    cdp.eval(
        """
(() => {
  if(typeof closePathFocus==='function')closePathFocus();
  if(typeof closePathReader==='function')closePathReader();
  document.body.classList.remove('path-focus-open','path-reader-open');
})()
"""
    )
    time.sleep(0.2)
    after = cdp.eval(MEASURE)
    results[f"{tag}-overlay-close"] = after
    if after.get("pathFocus"):
        errors.append(tag + ": overlay close left path-focus")
    if not after.get("expanded"):
        errors.append(tag + ": overlay close collapsed the in-card path")

    cdp.eval(
        f"""
(() => {{
  var el=document.getElementById({json.dumps(eid)});
  if(el&&typeof selectEntry==='function')selectEntry(el);
  else if(el) el.classList.add('selected');
  var desc=el&&el.querySelector('.summary-panel .desc, .desc');
  var path=el&&el.querySelector('.path');
  var sc=(typeof catalogPickWheelScroller==='function'&&catalogPickWheelScroller())
    ||(typeof catalogContentScroller==='function'&&catalogContentScroller())
    ||(typeof catalogScrollEl==='function'&&catalogScrollEl())
    ||document.querySelector('#catalogMain > .catalog-body')
    ||document.getElementById('catalogMain');
  window.__wheelSc=sc;
  window.__wheelBefore=sc?sc.scrollTop:0;
  if(desc) desc.dispatchEvent(new WheelEvent('wheel',{{deltaY:240,bubbles:true,cancelable:true}}));
  window.__wheelAfterDesc=sc?sc.scrollTop:0;
  if(sc) sc.scrollTop=window.__wheelBefore;
  if(path) path.dispatchEvent(new WheelEvent('wheel',{{deltaY:240,bubbles:true,cancelable:true}}));
  window.__wheelAfterPath=sc?sc.scrollTop:0;
}})()
"""
    )
    time.sleep(0.15)
    wh = cdp.eval(
        """
({before:window.__wheelBefore, afterDesc:window.__wheelAfterDesc, afterPath:window.__wheelAfterPath,
  scCan:!!(window.__wheelSc&&window.__wheelSc.scrollHeight>window.__wheelSc.clientHeight+4),
  scId: window.__wheelSc?(window.__wheelSc.id||String(window.__wheelSc.className||'').split(/\\s+/)[0]):''})
"""
    )
    results[f"{tag}-wheel"] = wh
    if wh and wh.get("scCan"):
        if (wh.get("afterDesc") or 0) <= (wh.get("before") or 0):
            errors.append(tag + ": desc wheel did not move catalog scroller")
        if (wh.get("afterPath") or 0) <= (wh.get("before") or 0):
            errors.append(tag + ": path wheel did not move catalog scroller")

    cdp.eval(
        """
(() => {
  if(typeof closePathFocus==='function')closePathFocus();
  if(typeof closePathReader==='function')closePathReader();
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
    logf = open("/tmp/catalog-path-collapse-wheel.log", "w")
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
                nav(cdp, f"http://127.0.0.1:{HTTP_PORT}/{page}?v=path-collapse-wheel")
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
