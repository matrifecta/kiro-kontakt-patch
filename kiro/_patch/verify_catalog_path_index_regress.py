#!/usr/bin/env python3
"""CDP verify: path/folder visible, desc tops aligned, Index Embed in-flow block."""
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

OUT = Path("/home/phnx/kiro-kontakt-patch/kiro/_patch/verify_catalog_path_index_regress.json")
PORT = 9544
HTTP_PORT = 8797
PROFILE = "/tmp/catalog-path-index-regress"
ROOT = "/home/phnx/kiro-kontakt-patch/public/catalogs"
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


class Ws:
    def __init__(self, url):
        u = urlparse(url)
        s = socket.create_connection((u.hostname, u.port or 80), timeout=120)
        path = u.path + (("?" + u.query) if u.query else "")
        s.settimeout(120)
        import base64

        key = base64.b64encode(os.urandom(16)).decode()
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
        import base64

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
            ln = self.buf[1] & 0x7F
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


MEASURE = r"""
(function(){
  function box(el){if(!el)return null;var r=el.getBoundingClientRect();return{t:Math.round(r.top),b:Math.round(r.bottom),h:Math.round(r.height),w:Math.round(r.width)};}
  function cs(el,k){return el?getComputedStyle(el)[k]:'';}
  var cards=[].slice.call(document.querySelectorAll('#catalogMain .loc-group > .entry:not(.highlight):not(.is-hidden)')).slice(0,6);
  var pathRows=[];
  cards.forEach(function(e){
    var p=e.querySelector('.path');if(!p)return;
    var code=p.querySelector('code');var folder=p.querySelector('.folder');
    var cr=code?code.getBoundingClientRect():null;var fr=folder?folder.getBoundingClientRect():null;
    pathRows.push({
      id:e.id,pathH:Math.round(p.getBoundingClientRect().height),pathFs:cs(p,'fontSize'),pathMinH:cs(p,'minHeight'),
      codeVis:!!(code&&cr&&cr.height>2&&cr.width>2),folderVis:!!(folder&&fr&&fr.height>2&&fr.width>2),
      overlap:code&&folder&&cr&&fr?Math.round(Math.min(cr.right,fr.right)-Math.max(cr.left,fr.left)):0,
      code:box(code),folder:box(folder)
    });
  });
  var tops=[];var rowDesc=[];
  cards.slice(0,3).forEach(function(e){
    var d=e.querySelector('.summary-panel');
    if(d){var t=Math.round(d.getBoundingClientRect().top);tops.push(t);rowDesc.push({id:e.id,descTop:t,descH:Math.round(d.getBoundingClientRect().height),descMax:cs(d,'maxHeight')});}
  });
  var ix=document.getElementById('catalogIndex');
  var main=document.getElementById('catalogMain');
  var cb=main&&(main.querySelector(':scope > .catalog-body')||main.querySelector('.catalog-body'));
  var card0=cb&&cb.querySelector('.loc-group > .entry:not(.is-hidden), .entry');
  var ixR=ix?ix.getBoundingClientRect():null;var cardR=card0?card0.getBoundingClientRect():null;
  return {
    cls:document.body.className,
    embed:!!(ix&&ix.classList.contains('is-embedded')),
    ixCollapsed:!!(ix&&ix.classList.contains('is-collapsed')),
    ixParent:ix&&ix.parentElement&&(ix.parentElement.id||String(ix.parentElement.className).split(/\s+/)[0]||ix.parentElement.tagName),
    ixPos:ix?cs(ix,'position'):'',
    ixBg:ix?cs(ix,'backgroundColor'):'',
    ixBottom:ixR?Math.round(ixR.bottom):0,
    cardTop:cardR?Math.round(cardR.top):0,
    overlap:ixR&&cardR?Math.round(ixR.bottom-cardR.top):0,
    pathRows:pathRows,
    descSpread:tops.length?Math.max.apply(null,tops)-Math.min.apply(null,tops):999,
    rowDesc:rowDesc
  };
})()
"""


def run_case(url: str, label: str, setup: str, is_ds: bool) -> dict:
    chrome_bin = next(
        (p for p in ("/usr/lib/chromium/chromium", "/usr/bin/chromium", "/usr/bin/google-chrome") if os.path.isfile(p)),
        None,
    )
    if not chrome_bin:
        raise SystemExit("no chromium")
    subprocess.run(["pkill", "-f", f"remote-debugging-port={PORT}"], check=False)
    time.sleep(0.5)
    prof = f"{PROFILE}-{label}"
    chrome = subprocess.Popen(
        [
            chrome_bin,
            "--headless=new",
            "--disable-gpu",
            f"--remote-debugging-port={PORT}",
            f"--user-data-dir={prof}",
            "--no-first-run",
            "--no-default-browser-check",
            "about:blank",
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    rid = 10
    try:
        time.sleep(1.5)
        tabs = json.loads(urllib.request.urlopen(f"http://127.0.0.1:{PORT}/json", timeout=10).read())
        ws = Ws(tabs[0]["webSocketDebuggerUrl"])
        cdp(ws, "Page.navigate", {"url": url})
        for _ in range(120 if is_ds else 30):
            time.sleep(2 if is_ds else 1)
            st = eval_js(
                ws,
                "({rs:document.readyState,n:document.querySelectorAll('#catalogMain .entry').length,vis:document.querySelectorAll('#catalogMain .loc-group > .entry:not(.is-hidden)').length})",
                rid,
            )
            rid += 1
            if st and st.get("rs") == "complete" and (st.get("vis") or 0) >= 2:
                break
        eval_js(
            ws,
            "if(typeof ensureCatalogMain==='function')ensureCatalogMain();if(typeof bindCatalogPathHits==='function')bindCatalogPathHits();if(typeof setDisplayMode==='function')setDisplayMode('sides',{pick:true});",
            rid,
        )
        rid += 1
        eval_js(ws, setup, rid)
        rid += 1
        time.sleep(0.6)
        data = eval_js(ws, MEASURE, rid)
        data["label"] = label
        data["url"] = url
        return data
    finally:
        chrome.terminate()
        chrome.wait(timeout=10)


def main():
    httpd = ensure_http()
    base = f"http://127.0.0.1:{HTTP_PORT}"
    cases = [
        (
            "DS-path-collapsed",
            f"{base}/DS-CATALOG.html?cb=path-regress",
            "if(typeof equalizeCatalogCardRows==='function')equalizeCatalogCardRows();true",
            True,
        ),
        (
            "DS-index-embed-open",
            f"{base}/DS-CATALOG.html?cb=path-regress-ix",
            """
(function(){
  if(typeof ensureCatalogMain==='function')ensureCatalogMain();
  var ix=document.getElementById('catalogIndex');
  if(!ix)return {err:'no index'};
  ix.classList.add('is-embedded');ix.classList.remove('is-collapsed');
  if(typeof parkCatalogDocNote==='function')parkCatalogDocNote();
  if(typeof syncIndexWindowDock==='function')syncIndexWindowDock();
  if(typeof equalizeCatalogCardRows==='function')equalizeCatalogCardRows();
  return {ok:true,parent:ix.parentElement&&(ix.parentElement.id||ix.parentElement.className)};
})()
""",
            True,
        ),
        (
            "KONTAKT-path-collapsed",
            f"{base}/KONTAKT-CATALOG.html?cb=path-regress-k",
            "if(typeof equalizeCatalogCardRows==='function')equalizeCatalogCardRows();true",
            False,
        ),
    ]
    results = [run_case(url, label, setup, is_ds) for label, url, setup, is_ds in cases]
    path_ok = all(
        r.get("pathRows")
        and all(p.get("codeVis") and p.get("folderVis") and p.get("pathH", 0) >= 8 for p in r["pathRows"][:3])
        and r.get("descSpread", 99) <= 4
        for r in results
        if "index-embed" not in r.get("label", "")
    )
    ix = next(r for r in results if "index-embed" in r.get("label", ""))
    ix_ok = (
        ix.get("embed")
        and "catalog-body" in str(ix.get("ixParent", ""))
        and ix.get("ixPos") in ("relative", "static")
        and ix.get("overlap", 99) <= 0
        and ix.get("ixBottom", 0) <= ix.get("cardTop", 0)
    )
    summary = {
        "cause": "fix-PATH-FOLDER-GAP-v2: font-size:0 on .path made height:2.75em compute to 0px; overflow:hidden clipped code/folder",
        "indexBefore": {
            "window": "#catalogMain>#catalogIndex:not(.is-embedded) position:absolute/sticky overlay on scroller",
            "embedBroken": "is-embedded but sticky/transparent — list ran through cards",
        },
        "indexAfter": {
            "embed": ".catalog-body>#catalogIndex.is-embedded position:relative, opaque bg, grid-column 1/-1",
            "window": "unchanged — index-window-open keeps hover dock",
        },
        "results": results,
        "pass": path_ok and ix_ok,
        "pathOk": path_ok,
        "indexOk": ix_ok,
    }
    OUT.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))
    if httpd:
        httpd.shutdown()
    if not summary["pass"]:
        raise SystemExit("verify failed")


if __name__ == "__main__":
    main()
