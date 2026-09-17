#!/usr/bin/env python3
"""CDP verify: grid selected card desc scrolls before catalog forward."""
from __future__ import annotations

import http.server
import json
import os
import socket
import subprocess
import threading
import time
import urllib.request
from pathlib import Path
from urllib.parse import urlparse
import base64

OUT = Path("/home/phnx/kiro-kontakt-patch/kiro/_patch/verify_catalog_desc_wheel_grid.json")
PORT = 9528
HTTP_PORT = 8797
ROOT = "/home/phnx/kiro-kontakt-patch/public/catalogs"
PROFILE = "/tmp/catalog-desc-wheel-grid"
MARK = "fix-GRID-DESC-WHEEL-v1"
os.makedirs(PROFILE, exist_ok=True)

MEASURE = r"""
(() => {
  function scroller(){
    if(typeof catalogContentScroller==='function'){
      var c=catalogContentScroller();
      if(c)return c;
    }
    return document.querySelector('#catalogMain > .catalog-body')||document.getElementById('catalogMain');
  }
  if(typeof closeChosenPreview==='function')closeChosenPreview({skipJumpExit:true});
  var entries=[].slice.call(document.querySelectorAll('#catalogMain .loc-group > .entry:not(.highlight):not(.is-hidden)'));
  var target=null,panel=null,best=0;
  for(var i=0;i<entries.length;i++){
    if(typeof selectEntry==='function')selectEntry(entries[i]);
    else entries[i].classList.add('selected');
    if(typeof scheduleEqualizeCardRows==='function')scheduleEqualizeCardRows();
    var p=entries[i].querySelector('.summary-panel');
    if(!p)continue;
    var ov=p.scrollHeight-p.clientHeight;
    if(ov>best){best=ov;target=entries[i];panel=p;}
  }
  if(target){
    if(typeof selectEntry==='function')selectEntry(target);
    else target.classList.add('selected');
    panel=target.querySelector('.summary-panel');
  }
  if(!target)return {error:'no long-desc card'};
  var sc=scroller();
  var cs=getComputedStyle(panel);
  var p0=panel.scrollTop,st0=sc?sc.scrollTop:0;
  var inner=(typeof catalogInnerWheelEl==='function')?catalogInnerWheelEl(panel.querySelector('.desc')||panel):panel;
  var applied=(typeof catalogApplyWheel==='function')?catalogApplyWheel(inner,48):false;
  var pMid=panel.scrollTop,stMid=sc?sc.scrollTop:0;
  panel.scrollTop=panel.scrollHeight;
  var pBot=panel.scrollTop;
  var appliedEnd=(typeof catalogApplyWheel==='function')?catalogApplyWheel(inner,48):false;
  var stEnd=sc?sc.scrollTop:0;
  var stFwd=0,catalogForwardDirect=0;
  if(sc){var b=sc.scrollTop;sc.scrollTop=b+48;stFwd=sc.scrollTop;catalogForwardDirect=Math.round(stFwd-b);sc.scrollTop=b;}
  return {
    previewOpen:document.body.classList.contains('chosen-preview-open'),
    mark:typeof bindLibNameTips==='function',
    wheelMark:document.documentElement.innerHTML.indexOf('""" + MARK + r"""')>=0,
    id:target.id,
    panelOv:cs.overflowY,
    canScroll:panel.scrollHeight>panel.clientHeight+1,
    panelH:Math.round(panel.clientHeight),
    panelSH:Math.round(panel.scrollHeight),
    midPanelDelta:Math.round(pMid-p0),
    midCatalogDelta:Math.round(stMid-st0),
    wheelApplyMid:applied,
    atBottom:Math.round(pBot),
    wheelApplyAtBottom:appliedEnd,
    catalogForwardAtBottom:Math.round(stEnd-stMid),
    catalogForwardDirect:catalogForwardDirect
  };
})()
"""


def ensure_http():
    try:
        urllib.request.urlopen(f"http://127.0.0.1:{HTTP_PORT}/DS-CATALOG.html", timeout=2).read(64)
        return None
    except Exception:
        pass
    os.chdir(ROOT)

    class H(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a):
            pass

    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", HTTP_PORT), H)
    httpd.allow_reuse_address = True
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    for _ in range(40):
        try:
            urllib.request.urlopen(f"http://127.0.0.1:{HTTP_PORT}/DS-CATALOG.html", timeout=1).read(64)
            return httpd
        except Exception:
            time.sleep(0.1)
    raise SystemExit("http failed")


class Ws:
    def __init__(self, url):
        u = urlparse(url)
        key = base64.b64encode(os.urandom(16)).decode()
        s = socket.create_connection((u.hostname, u.port or 80), timeout=120)
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
                ln = int.from_bytes(self.buf[2:4], "big")
                off = 4
            elif ln == 127:
                ln = int.from_bytes(self.buf[2:10], "big")
                off = 10
            if len(self.buf) < off + ln:
                self._fill()
                continue
            payload = self.buf[off : off + ln]
            self.buf = self.buf[off + ln :]
            return payload.decode("utf-8", "replace")

    def _fill(self):
        chunk = self.s.recv(65536)
        if not chunk:
            raise RuntimeError("ws closed")
        self.buf += chunk


def cdp(ws, method, params=None, _id=1):
    ws.send(json.dumps({"id": _id, "method": method, "params": params or {}}))
    while True:
        msg = json.loads(ws.recv())
        if msg.get("id") == _id:
            if "error" in msg:
                raise RuntimeError(msg["error"])
            return msg.get("result", {})


def eval_js(ws, expr, _id):
    r = cdp(ws, "Runtime.evaluate", {"expression": expr, "returnByValue": True, "awaitPromise": True}, _id)
    v = r.get("result", {})
    if v.get("type") == "object" and "value" in v:
        return v["value"]
    if "exceptionDetails" in r:
        raise RuntimeError(r["exceptionDetails"])
    return v


def run_catalog(url: str) -> dict:
    chrome_bin = next(
        (p for p in ("/usr/lib/chromium/chromium", "/usr/bin/chromium", "/usr/bin/google-chrome") if os.path.isfile(p)),
        None,
    )
    if not chrome_bin:
        raise SystemExit("no chromium")
    chrome = subprocess.Popen(
        [
            chrome_bin,
            "--headless=new",
            "--disable-gpu",
            f"--remote-debugging-port={PORT}",
            f"--user-data-dir={PROFILE}",
            "--no-first-run",
            "--no-default-browser-check",
            "about:blank",
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    time.sleep(1.2)
    try:
        tabs = json.loads(urllib.request.urlopen(f"http://127.0.0.1:{PORT}/json", timeout=5).read())
        ws = Ws(tabs[0]["webSocketDebuggerUrl"])
        cdp(ws, "Page.navigate", {"url": url})
        wait = 10 if "DS-CATALOG" in url else 5
        time.sleep(wait)
        cdp(ws, "Runtime.enable")
        rid = 10
        for _ in range(60):
            st = eval_js(
                ws,
                "({rs:document.readyState,n:document.querySelectorAll('.entry').length,m:typeof catalogApplyWheel==='function'})",
                rid,
            )
            rid += 1
            if st and st.get("rs") == "complete" and (st.get("n") or 0) > 10 and st.get("m"):
                break
            time.sleep(1)
        eval_js(ws, "window.scrollTo(0,0)", rid)
        rid += 1
        time.sleep(0.5)
        data = eval_js(ws, MEASURE, rid)
        return {"url": url, "mark": MARK, "measure": data}
    finally:
        chrome.terminate()
        chrome.wait(timeout=5)


def main() -> None:
    ensure_http()
    targets = [
        f"http://127.0.0.1:{HTTP_PORT}/KONTAKT-CATALOG.html",
        f"http://127.0.0.1:{HTTP_PORT}/DS-CATALOG.html",
    ]
    results = {"mark": MARK, "catalogs": []}
    for url in targets:
        print("verify", url)
        results["catalogs"].append(run_catalog(url))
    OUT.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print("wrote", OUT)
    for r in results["catalogs"]:
        m = r.get("measure") or {}
        print(
            r["url"].split("/")[-1],
            m.get("id"),
            "panelΔ",
            m.get("midPanelDelta"),
            "catΔ",
            m.get("midCatalogDelta"),
            "fwd",
            m.get("catalogForwardAtBottom"),
        )


if __name__ == "__main__":
    main()
