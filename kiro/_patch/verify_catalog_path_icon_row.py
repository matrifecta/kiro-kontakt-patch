#!/usr/bin/env python3
"""CDP verify: path icon row order, spacing, theme, copy, FS scale slider."""
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

OUT = Path("/home/phnx/kiro-kontakt-patch/kiro/_patch/verify_catalog_path_icon_row.json")
PORT = 9528
HTTP_PORT = 8797
ROOT = "/home/phnx/kiro-kontakt-patch/public/catalogs"
PROFILE = "/tmp/catalog-path-icon-row"
MARK = "fix-PATH-ICON-ROW-v1"
os.makedirs(PROFILE, exist_ok=True)


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


MEASURE = r"""
(() => {
  if(typeof bindCatalogPathHits==='function')bindCatalogPathHits();
  var cards=[].slice.call(document.querySelectorAll('#catalogMain .loc-group > .entry:not(.is-hidden):not(.highlight)'));
  cards=cards.filter(function(e){var r=e.getBoundingClientRect();return r.width>20&&r.height>20;});
  if(!cards.length)return {missing:true};
  var t0=Math.round(cards[0].getBoundingClientRect().top);
  var row=cards.filter(function(e){return Math.abs(Math.round(e.getBoundingClientRect().top)-t0)<=10;}).slice(0,6);
  var samples=row.map(function(e){
    var path=e.querySelector('.path');
    if(!path)return null;
    var act=path.querySelector('.path-action-row');
    var fs=act?act.querySelector('.path-fs-hit'):path.querySelector('.path-fs-hit');
    var cp=act?act.querySelector('.path-copy-hit'):path.querySelector('.path-copy-hit');
    var fd=act?act.querySelector('a.folder'):path.querySelector('a.folder');
    var labels=[fs&&fs.getAttribute('aria-label'),cp&&cp.getAttribute('aria-label'),fd&&fd.getAttribute('aria-label')];
    var rects=[fs,cp,fd].filter(Boolean).map(function(b){var r=b.getBoundingClientRect();return {l:Math.round(r.left),w:Math.round(r.width),h:Math.round(r.height)};});
    var gaps=[];
    for(var i=1;i<rects.length;i++)gaps.push(rects[i].l-(rects[i-1].l+rects[i-1].w));
    var rowR=act?act.getBoundingClientRect():null;
    var cardR=e.getBoundingClientRect();
    var rowCenter=rowR?Math.round(rowR.left+rowR.width/2):null;
    var cardCenter=Math.round(cardR.left+cardR.width/2);
    function themed(btn){
      if(!btn)return null;
      var cs=getComputedStyle(btn);
      var bef=btn;
      return {
        bg:cs.backgroundColor,
        color:cs.color,
        hasMask:cs.maskImage&&cs.maskImage!=='none'||!!btn.querySelector('::before'),
        cls:btn.className,
        text:(btn.textContent||'').trim()
      };
    }
    var fsCs=fs?getComputedStyle(fs,'::before'):null;
    return {
      id:e.id,
      hasRow:!!act,
      order:labels,
      orderOk:labels[0]==='Open path fullscreen'&&labels[1]==='Copy path'&&labels[2]==='Open folder',
      gaps:gaps,
      gapDelta:gaps.length?Math.max.apply(null,gaps)-Math.min.apply(null,gaps):0,
      centerDelta:rowCenter!=null?Math.abs(rowCenter-cardCenter):null,
      btnTextHidden:!((fs&&fs.textContent)||'').trim()&&!((cp&&cp.textContent)||'').trim()&&!((fd&&fd.textContent)||'').trim(),
      fsMask:fs?(getComputedStyle(fs,'::before').maskImage||getComputedStyle(fs,'::before').webkitMaskImage):null,
      pathCode:!!path.querySelector('code'),
      bHidden:path.querySelector('b')?getComputedStyle(path.querySelector('b')).display==='none':true
    };
  }).filter(Boolean);
  var pf=document.getElementById('pathFocusScale');
  var pr=document.getElementById('pathReaderScale');
  return {
    mark:document.documentElement.innerHTML.indexOf('""" + MARK + r"""')>=0,
    hasCopyFn:typeof catalogCopyPath==='function',
    samples:samples,
    allOrderOk:samples.every(function(s){return s.orderOk;}),
    allCentered:samples.every(function(s){return s.centerDelta!=null&&s.centerDelta<=12;}),
    allGapEven:samples.every(function(s){return s.gapDelta<=4;}),
    allNoText:samples.every(function(s){return s.btnTextHidden;}),
    pathFocusScale:!!pf,
    pathReaderScale:!!pr
  };
})()
"""

COPY_TEST = r"""
(async () => {
  if(typeof bindCatalogPathHits==='function')bindCatalogPathHits();
  var e=document.querySelector('#catalogMain .entry:not(.highlight) .path');
  if(!e)return {missing:true};
  var path=e.closest('.path')||e;
  var code=path.querySelector('code');
  var expected=(code&&code.textContent||'').trim();
  var cp=path.querySelector('.path-copy-hit');
  if(!cp||!expected)return {missing:true,hasBtn:!!cp,expectedLen:expected.length};
  cp.click();
  await new Promise(function(r){setTimeout(r,300);});
  var got='';
  try{
    if(navigator.clipboard&&navigator.clipboard.readText)got=await navigator.clipboard.readText();
  }catch(eRead){}
  var toast=document.getElementById('pathCopyToast');
  return {
    expected:expected.slice(0,80),
    got:got.slice(0,80),
    match:got===expected,
    toastShown:!!(toast&&!toast.hidden),
    copyOk:got===expected||!!(toast&&!toast.hidden)
  };
})()
"""

FS_TEST = r"""
(() => {
  var fs=document.querySelector('#catalogMain .entry:not(.highlight) .path-fs-hit');
  var entry=fs&&fs.closest('.entry');
  if(!fs||!entry)return {missing:true};
  if(typeof activatePath==='function')activatePath(entry);
  var open=document.body.classList.contains('path-focus-open')||document.body.classList.contains('path-reader-open');
  var scale=document.getElementById('pathFocusScale')||document.getElementById('pathReaderScale');
  if(typeof closePathFocus==='function')closePathFocus(true);
  if(typeof closePathReader==='function')closePathReader(true);
  return {overlayOpen:open,hasScaleSlider:!!scale,scaleMin:scale&&scale.min,scaleMax:scale&&scale.max};
})()
"""


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
        wait = 8 if "DS-CATALOG" in url else 4
        time.sleep(wait)
        cdp(ws, "Runtime.enable")
        rid = 10
        for _ in range(60):
            st = eval_js(
                ws,
                "({rs:document.readyState,n:document.querySelectorAll('.entry').length,m:typeof bindCatalogPathHits==='function'})",
                rid,
            )
            rid += 1
            if st and st.get("rs") == "complete" and (st.get("n") or 0) > 10 and st.get("m"):
                break
            time.sleep(1)
        eval_js(ws, "window.scrollTo(0,0)", rid)
        rid += 1
        time.sleep(0.4)
        eval_js(ws, "if(typeof bindCatalogPathHits==='function')bindCatalogPathHits()", rid)
        rid += 1
        base = eval_js(ws, MEASURE, rid)
        rid += 1
        copy = eval_js(ws, COPY_TEST, rid)
        rid += 1
        fs = eval_js(ws, FS_TEST, rid)
        return {"url": url, "mark": MARK, "measure": base, "copy": copy, "fs": fs}
    finally:
        chrome.terminate()
        chrome.wait(timeout=5)


def main() -> None:
    ensure_http()
    targets = [
        f"http://127.0.0.1:{HTTP_PORT}/DS-CATALOG.html",
        f"http://127.0.0.1:{HTTP_PORT}/KONTAKT-CATALOG.html",
        f"http://127.0.0.1:{HTTP_PORT}/DS-CATALOG-portable.html",
        f"http://127.0.0.1:{HTTP_PORT}/KONTAKT-CATALOG-portable.html",
    ]
    results = {"mark": MARK, "catalogs": []}
    for url in targets:
        print("verify", url)
        results["catalogs"].append(run_catalog(url))
    OUT.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print("wrote", OUT)
    for r in results["catalogs"]:
        m = r.get("measure") or {}
        c = r.get("copy") or {}
        f = r.get("fs") or {}
        print(
            r["url"].split("/")[-1],
            "order",
            m.get("allOrderOk"),
            "center",
            m.get("allCentered"),
            "copy",
            c.get("copyOk"),
            "scale",
            f.get("hasScaleSlider"),
        )


if __name__ == "__main__":
    main()
