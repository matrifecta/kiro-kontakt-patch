#!/usr/bin/env python3
"""CDP verify: row equal heights, portrait cards, path expand/collapse, Collapse, DS covers."""
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

OUT = Path("/home/phnx/kiro-kontakt-patch/kiro/_patch/verify_catalog_card_row_rect.json")
PORT = 9526
HTTP_PORT = 8797
PROFILE = "/tmp/catalog-card-row-rect"
os.makedirs(PROFILE, exist_ok=True)

MEASURE = r"""
(() => {
  function rowCards(){
    var cards=[].slice.call(document.querySelectorAll('#catalogMain .loc-group > .entry:not(.is-hidden):not(.highlight)'));
    cards=cards.filter(function(e){var r=e.getBoundingClientRect();return r.width>20&&r.height>20;});
    var rows=[];
    cards.forEach(function(e){
      var t=Math.round(e.getBoundingClientRect().top);
      var row=null;
      for(var i=0;i<rows.length;i++){if(Math.abs(rows[i].t-t)<=10){row=rows[i];break;}}
      if(!row){row={t:t,cards:[]};rows.push(row);}
      row.cards.push(e);
    });
    return rows.filter(function(r){return r.cards.length>=2;}).slice(0,3);
  }
  function cardBox(e){
    var r=e.getBoundingClientRect();
    return {id:e.id,w:Math.round(r.width),h:Math.round(r.height),ratio:+(r.height/r.width).toFixed(3),minH:e.style.minHeight||''};
  }
  var rows=rowCards().map(function(row){
    var hs=row.cards.map(function(e){return Math.round(e.getBoundingClientRect().height);});
    return {n:row.cards.length,hs:hs,delta:Math.max.apply(null,hs)-Math.min.apply(null,hs),cards:row.cards.slice(0,4).map(cardBox)};
  });
  var cubes=document.querySelectorAll('#catalogMain .entry:not(.highlight)').length;
  var cubeN=0,samples=[];
  [].slice.call(document.querySelectorAll('#catalogMain .entry:not(.highlight)')).slice(0,24).forEach(function(e){
    var r=e.getBoundingClientRect();
    if(r.width<20)return;
    var ratio=r.height/r.width;
    if(ratio>=0.92&&ratio<=1.08){cubeN++;if(samples.length<4)samples.push({id:e.id,w:Math.round(r.width),h:Math.round(r.height),ratio:+ratio.toFixed(3)});}
  });
  var path=document.querySelector('#catalogMain .entry .path');
  var piano=['item-7','item-9','item-12'].map(function(id){
    var e=document.getElementById(id);
    var img=e&&e.querySelector('.cover img');
    return {id:id,name:e&&e.getAttribute('data-name'),nat:img?img.naturalWidth:0,srcLen:img?(img.getAttribute('src')||'').length:0};
  });
  return {rows:rows,cubeN:cubeN,cubeSamples:samples,hasBind:typeof bindCatalogPathHits==='function',hasCollapsePaths:typeof collapseCatalogPaths==='function',pathFs:!!(path&&path.querySelector('.path-fs-hit')),pathExpanded:!!(path&&path.classList.contains('is-expanded')),mark:!!document.querySelector('style')&&/[.]entry:not[(][.]highlight[)]/.test(document.documentElement.innerHTML)?true:document.documentElement.innerHTML.indexOf('fix-CARD-ROW-RECT')>=0,piano:piano};
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


def run_catalog(url):
    try:
        urllib.request.urlopen(f"http://127.0.0.1:{HTTP_PORT}/", timeout=3)
    except Exception as e:
        raise SystemExit(f"http://127.0.0.1:{HTTP_PORT} not serving: {e}")

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
        ws_url = tabs[0]["webSocketDebuggerUrl"]
        ws = Ws(ws_url)
        cdp(ws, "Target.setDiscoverTargets", {"discover": True})
        cdp(ws, "Page.navigate", {"url": url})
        time.sleep(2 if "DS-CATALOG" in url else 4)
        cdp(ws, "Runtime.enable")
        rid = 10
        for _ in range(24):
            st = eval_js(ws, "({rs:document.readyState,n:document.querySelectorAll('.entry').length,m:document.documentElement.innerHTML.indexOf('fix-CARD-ROW-RECT')>=0})", rid)
            rid += 1
            if st and st.get("rs") == "complete" and (st.get("n") or 0) > 10 and st.get("m"):
                break
            time.sleep(1)
        eval_js(ws, "window.scrollTo(0,0)", rid)
        rid += 1
        time.sleep(0.5)
        base = eval_js(ws, MEASURE, rid)
        rid += 1

        entry = eval_js(
            ws,
            "(function(){var e=document.querySelector('#catalogMain .loc-group > .entry:not(.is-hidden)');if(e){e.click();return e.id;}return null;})()",
            rid,
        )
        rid += 1
        time.sleep(0.3)
        path = eval_js(
            ws,
            "(function(){var e=document.querySelector('.entry.selected')||document.querySelector('#catalogMain .entry');var p=e&&e.querySelector('.path');if(!p)return null;p.click();return {expanded:p.classList.contains('is-expanded'),h:p.clientHeight};})()",
            rid,
        )
        rid += 1
        time.sleep(0.3)
        collapse_text = eval_js(
            ws,
            "(function(){var e=document.querySelector('.entry.selected')||document.querySelector('#catalogMain .entry');var p=e&&e.querySelector('.path');var c=p&&p.querySelector('code');if(!c)return null;c.click();return {expanded:p.classList.contains('is-expanded')};})()",
            rid,
        )
        rid += 1
        time.sleep(0.3)
        expand_again = eval_js(
            ws,
            "(function(){var p=document.querySelector('.entry .path');if(!p)return null;p.click();return p.classList.contains('is-expanded');})()",
            rid,
        )
        rid += 1
        collapse_btn = eval_js(
            ws,
            "(function(){var b=document.getElementById('collapseCardsBtn')||document.querySelector('.collapse-cards-btn');if(!b)return {missing:true};b.click();var open=document.querySelectorAll('details.patches[open],details.grp[open]').length;var paths=document.querySelectorAll('.entry .path.is-expanded').length;return {open:open,paths:paths};})()",
            rid,
        )
        rid += 1
        time.sleep(0.4)
        after = eval_js(ws, MEASURE, rid)

        return {
            "url": url,
            "entry": entry,
            "pathExpand": path,
            "pathTextCollapse": collapse_text,
            "pathExpandAgain": expand_again,
            "collapseBtn": collapse_btn,
            "before": base,
            "afterCollapse": after,
        }
    finally:
        chrome.terminate()
        chrome.wait(timeout=5)


def main():
    targets = [
        f"http://127.0.0.1:{HTTP_PORT}/DS-CATALOG.html",
        f"http://127.0.0.1:{HTTP_PORT}/KONTAKT-CATALOG.html",
    ]
    results = []
    for url in targets:
        print("verify", url)
        results.append(run_catalog(url))
    OUT.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print("wrote", OUT)
    for r in results:
        b, a = r["before"], r["afterCollapse"]
        print(r["url"].split("/")[-1], "rows", b.get("rows"), "cubes", b.get("cubeN"), "path", r.get("pathExpand"), "collapse", r.get("pathTextCollapse"), "btn", r.get("collapseBtn"), "after", a.get("rows"))


if __name__ == "__main__":
    main()
